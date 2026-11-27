#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Integration test of bwm-kglobalaccel. Run inside a private bus (dbus-run-session):
CTest does it. Uses a fake hyprctl and temporary XDG roots; never touches the session."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time

FAKE_HYPRCTL = r'''#!/usr/bin/env python3
import json, os, re, sys
root = os.environ["BWM_TEST_ROOT"]
args = sys.argv[1:]
if args == ["-j", "binds"]:
    sys.stdout.write(open(os.path.join(root, "binds.json")).read())
elif args and args[0] == "eval":
    path = re.search(r'dofile\("(.*)"\)', args[1]).group(1)
    with open(os.path.join(root, "evals.log"), "a") as log:
        log.write("=== " + open(path).read() + "\n")
    print("ok")
else:
    sys.exit(1)
'''


def wait(predicate, timeout=10.0, what="condition"):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.05)
    raise AssertionError(f"timeout waiting for {what}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", required=True)
    parser.add_argument("--client")
    args = parser.parse_args()
    binary = Path(args.binary).resolve()
    client_bin = Path(args.client) if args.client else binary.with_name("test-client")
    if "DBUS_SESSION_BUS_ADDRESS" not in os.environ or os.environ.get("BWM_TEST_PRIVATE_BUS") != "1":
        # CTest runs us through dbus-run-session; refuse the user's bus.
        if not os.environ.get("DBUS_SESSION_BUS_ADDRESS", "").startswith("unix:path=/tmp/"):
            print("refusing to run outside a private dbus-run-session bus", file=sys.stderr)
            return 2

    root = Path(tempfile.mkdtemp(prefix="bwmkga-"))
    runtime = root / "run"
    runtime.mkdir(mode=0o700)
    (root / "fake-hyprctl").write_text(FAKE_HYPRCTL)
    (root / "fake-hyprctl").chmod(0o755)
    binds = [{"modmask": 8, "key": "F1", "description": "Lanzadores: Kickoff", "mouse": False, "submap": ""},
             {"modmask": 64, "key": "RETURN", "description": "Lanzadores: Terminal", "mouse": False, "submap": ""}]
    (root / "binds.json").write_text(json.dumps(binds))
    state = root / "state" / "kde-shortcuts.lua"
    env = {**os.environ, "BWM_TEST_ROOT": str(root), "XDG_RUNTIME_DIR": str(runtime),
           "XDG_CONFIG_HOME": str(root / "config"), "XDG_STATE_HOME": str(root / "state-home"),
           "XDG_DATA_HOME": str(root / "data"), "BWM_KGLOBALACCEL_HYPRCTL": str(root / "fake-hyprctl"),
           "BWM_KGLOBALACCEL_STATE": str(state), "QT_QPA_PLATFORM": "offscreen", "BWM_KGLOBALACCEL_NO_NOTIFY": "1"}
    env.pop("HYPRLAND_INSTANCE_SIGNATURE", None)

    def status():
        r = subprocess.run([str(binary), "--status"], env=env, capture_output=True, text=True, timeout=5)
        return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None

    daemon = subprocess.Popen([str(binary)], env=env, stderr=subprocess.PIPE, text=True)
    client = None
    try:
        wait(status, what="daemon socket")
        client = subprocess.Popen([str(client_bin)], env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  text=True, bufsize=1)
        line = client.stdout.readline().strip()
        assert line.startswith("assigned free=Meta+Shift+K taken="), line
        if line != "assigned free=Meta+Shift+K taken=":
            # kglobalacceld 6.7 accepts a shared key; the daemon then takes it back for BWM.
            changed = client.stdout.readline().strip()
            assert changed == "changed taken=", f"KDE must not keep BWM's Alt+F1: {changed}"

        st = wait(lambda: (s := status()) and any(b["key"] == "SUPER + SHIFT + k" for b in s["bound"]) and s,
                  what="free shortcut bound")
        assert not any(b["key"] == "ALT + F1" for b in st["bound"]), st
        assert any(c["action"] == "taken-action" and c["key"] == "ALT + F1" for c in st["conflicts"]), st["conflicts"]
        text = state.read_text()
        match = re.search(r'add\("SUPER \+ SHIFT \+ k", (\d+), "KDE: ', text)
        assert match, text
        assert "ALT + F1" not in text and "SUPER + Return" not in text, text
        code = match.group(1)

        for phase in ("press", "release"):
            r = subprocess.run([str(binary), "--trigger", phase, code], env=env, timeout=5)
            assert r.returncode == 0, phase
        assert client.stdout.readline().strip() == "triggered free"
        r = subprocess.run([str(binary), "--trigger", "press", "12345"], env=env, timeout=5)
        assert r.returncode == 1, "unknown keys must be ignored"

        # Editing a BWM shortcut from Preferences is undone: BWM's keys come from keybinds.json.
        client.stdin.write("edit-bwm\n")
        assert client.stdout.readline().strip() == "edited"
        time.sleep(0.6)
        client.stdin.write("query\n")
        assert client.stdout.readline().strip() == "keys free=Meta+Shift+K taken="
        assert client.stdout.readline().strip() == "bwm=Alt+F1"
        notices = status()["notices"]
        assert "Atajo de BWM sin cambios" in notices and "Atajo de KDE en conflicto con BWM" in notices, notices

        # BWM starts using the KDE key (keybinds-manager reload): BWM keeps it, KDE loses it.
        binds.append({"modmask": 65, "key": "K", "description": "Nuevo atajo de BWM", "mouse": False, "submap": ""})
        (root / "binds.json").write_text(json.dumps(binds))
        subprocess.run([str(binary), "--sync"], env=env, capture_output=True, timeout=5)
        changed = client.stdout.readline().strip()
        assert changed == "changed free=", changed
        try:
            wait(lambda: (s := status()) and not any(b["key"] == "SUPER + SHIFT + k" for b in s["bound"]), what="KDE bind withdrawn")
        except AssertionError:
            print(status(), file=sys.stderr)
            raise
        assert "SUPER + SHIFT + k" not in state.read_text()
        last_eval = (root / "evals.log").read_text().split("=== ")[-1]
        assert '["SUPER + SHIFT + k"]=true' in last_eval, "a key now BWM's is only disabled, never removed"

        daemon.send_signal(signal.SIGTERM)
        assert daemon.wait(timeout=10) == 0
        assert not state.exists(), "state file must go when the daemon stops"
        last_eval = (root / "evals.log").read_text().split("=== ")[-1]
        assert "dofile" not in last_eval, last_eval
        assert (root / "config" / "kglobalshortcutsrc").is_file()
        print("check-daemon: OK")
        return 0
    finally:
        if client:
            client.kill()
        if daemon.poll() is None:
            daemon.kill()
        err = daemon.stderr.read() if daemon.stderr else ""
        if err.strip():
            print(err[-3000:], file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
