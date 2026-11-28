#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""T8 nested Hyprland session test for OverviewHost + ScreenEdges (via check-focus-safety.py)."""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]


def send_sock(sock_path: Path, command: str) -> str:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.settimeout(4.0)
        s.connect(str(sock_path))
        s.sendall((command + "\n").encode("utf-8"))
        chunks = []
        while True:
            data = s.recv(4096)
            if not data:
                break
            chunks.append(data)
        return b"".join(chunks).decode("utf-8", errors="replace").strip()


def main() -> int:
    assert os.environ.get("BWM_FOCUS_NESTED") == "1", "Must run inside check-focus-safety.py"
    host_bin = ROOT / "build/bwm-plasma-host-tests/bwm-plasma-host"
    if not host_bin.exists():
        host_bin = ROOT / "build/bwm-plasma-host/bwm-plasma-host"
    assert host_bin.exists(), f"Missing host binary: {host_bin}"

    with tempfile.TemporaryDirectory(prefix="bwm-t8-session-", ignore_cleanup_errors=True) as tmp:
        base = Path(tmp)
        env = dict(os.environ)
        for k, sub in (("XDG_CONFIG_HOME", "cfg"), ("XDG_DATA_HOME", "data"),
                       ("XDG_CACHE_HOME", "cache"), ("XDG_STATE_HOME", "state"),
                       ("XDG_RUNTIME_DIR", "run")):
            d = base / sub
            d.mkdir(mode=0o700, exist_ok=True)
            env[k] = str(d)
        env["BWM_HOST_STATE_DIR"] = str(base / "state/bwm-plasma-host")
        sock_path = Path(env["XDG_RUNTIME_DIR"]) / "bwm-plasma-host.sock"

        # Start host inside a private session D-Bus so ownsShellApi=true and daily session is untouched.
        host = subprocess.Popen(
            ["dbus-run-session", "--", str(host_bin), "--session"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        try:
            deadline = time.monotonic() + 20.0
            while not sock_path.exists() and host.poll() is None and time.monotonic() < deadline:
                time.sleep(0.1)
            assert sock_path.exists(), f"Host socket did not appear (rc={host.poll()})"

            edges_status = json.loads(send_sock(sock_path, "screenedges-status"))
            assert edges_status["running"] is True, edges_status
            assert edges_status["actions"].get("TopLeft") == "Overview", edges_status
            assert edges_status["sensors"] >= 1, edges_status

            modes_checked = {}
            for mode in ("overview", "grid", "windowview", "windowview-all"):
                reply = send_sock(sock_path, f"overview-open {mode}")
                if reply != "ok":
                    st_err = send_sock(sock_path, "overview-status")
                    raise AssertionError(f"overview-open {mode} failed: {reply}; status={st_err}")
                time.sleep(0.35)
                st = json.loads(send_sock(sock_path, "overview-status"))
                assert st["active"] is True, st
                assert st["mode"] == mode, st
                assert st["views"] >= 1, st
                assert st["error"] == "", st
                modes_checked[mode] = st
                assert send_sock(sock_path, "overview-close") == "ok"
                time.sleep(0.15)
                closed_st = json.loads(send_sock(sock_path, "overview-status"))
                assert closed_st["active"] is False, closed_st

            # Verify toggle opens and closes cleanly
            assert send_sock(sock_path, "overview-toggle overview") == "ok"
            assert json.loads(send_sock(sock_path, "overview-status"))["active"] is True
            assert send_sock(sock_path, "overview-toggle overview") == "ok"
            assert json.loads(send_sock(sock_path, "overview-status"))["active"] is False

            print(json.dumps({"screenedges": edges_status, "modes": list(modes_checked.keys()), "passed": True}))
            return 0
        finally:
            if host.poll() is None:
                os.killpg(host.pid, signal.SIGTERM)
                try:
                    host.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(host.pid, signal.SIGKILL)


if __name__ == "__main__":
    raise SystemExit(main())
