#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 BWM
# SPDX-License-Identifier: GPL-2.0-or-later
"""Render the candidate shadow plugin in a disposable nested Hyprland only.

The new compositor window goes to a disposable headless host output. Only that compositor
loads the candidate, during its startup before creating clients. Screenshots contain
only the fixture's terminal/background, are measured, and are deleted on exit.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]


def hypr(*args, instance=None, timeout=5):
    result = subprocess.run(["hyprctl", *(["-i", instance] if instance else []), *args],
        capture_output=True, text=True, timeout=timeout, check=True)
    return result.stdout


def wait(predicate, message, timeout=15):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        value = predicate()
        if value:
            return value
        time.sleep(.1)
    raise TimeoutError(message)


def snapshot():
    focus = json.loads(hypr("-j", "activewindow"))
    return {"focus": {key: focus.get(key) for key in ("address", "pid")},
        "cursor": json.loads(hypr("-j", "cursorpos")),
        "plugins": json.loads(hypr("-j", "plugin", "list")),
        "monitors": [{k: m.get(k) for k in ("description", "width", "height", "x", "y", "scale", "transform", "reserved", "activeWorkspace")}
            for m in json.loads(hypr("-j", "monitors"))]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--helper", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    module, helper = args.module.resolve(), args.helper.resolve()
    if not module.is_file() or not helper.is_file():
        parser.error("Candidate module and helper must already be built")
    from PIL import Image, ImageChops
    before = snapshot()
    parent_clients = json.loads(hypr("-j", "clients"))
    if any(c.get("class") == "aquamarine" for c in parent_clients):
        parser.error("Another nested compositor is open; cannot isolate its parent window")
    dialogs_before = {c["pid"] for c in parent_clients if c.get("class") == "hyprland-dialog"}
    instances = {i["instance"] for i in json.loads(hypr("instances", "-j"))}
    rule = f"bwm-r6-nested-{os.getpid()}"
    processes = []
    rule_added = False
    host_output = f"BWM-R6-HOST-{os.getpid()}"
    host_created = False
    report = {"version": 1, "passed": False, "scope": "nested-Hyprland Wayland OpenGL/output capture, not Plasma visual parity", "xwaylandTested": False}
    with tempfile.TemporaryDirectory(prefix="bwm-r6-nested-") as temporary:
        root = Path(temporary)
        try:
            for folder in ("config", "data", "cache"):
                (root / folder).mkdir(mode=0o700)
            (root / "config/kdeglobals").write_text(Path("/usr/share/color-schemes/BreezeDark.colors").read_text())
            (root / "config/kwinrc").write_text("[org.kde.kdecoration2]\nlibrary=org.kde.breeze\n")
            config = root / "hyprland.lua"
            config.write_text('''hl.monitor({output="",mode="1280x800",position="0x0",scale=1})
hl.config({misc={disable_hyprland_logo=true,disable_splash_rendering=true},animations={enabled=false},xwayland={enabled=false},
 decoration={shadow={enabled=false},blur={enabled=false}},input={follow_mouse=0}})
hl.window_rule({name="fixture",match={class="^bwm-r6-window$"},float=true,size="500 300",move="220 180",no_shadow=false})
''')
            runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
            env = dict(os.environ, XDG_CONFIG_HOME=str(root / "config"), XDG_DATA_HOME=str(root / "data"),
                XDG_CACHE_HOME=str(root / "cache"), DBUS_SESSION_BUS_ADDRESS="unix:path="+str(root / "no-bus"),
                BWM_DECORATOR_SOCKET=str(root / "deco.sock"))
            for key in ("HYPRLAND_INSTANCE_SIGNATURE", "WAYLAND_SOCKET", "QT_QPA_PLATFORMTHEME", "DISPLAY"):
                env.pop(key, None)
            with (root / "helper.log").open("w") as log:
                processes.append(subprocess.Popen([str(helper), "--socket", str(root / "deco.sock")],
                    env=dict(env, QT_QPA_PLATFORM="offscreen"), stdout=log, stderr=subprocess.STDOUT, start_new_session=True))
            wait(lambda: (root / "deco.sock").exists(), "Disposable decorator socket missing")
            # A hidden parent workspace suppresses frame callbacks. Use a temporary
            # headless host output, as in the R5 fractional-scale checks; physical
            # outputs retain their modes/positions. Capture only the child display.
            hypr("output", "create", "headless", host_output)
            host_created = True
            hypr("eval", 'hl.monitor({output='+json.dumps(host_output)+',mode="1280x800@60",position="20000x20000",scale=1})')
            host_monitor = wait(lambda: next((m for m in json.loads(hypr("-j", "monitors")) if m["name"] == host_output),None), "Host output missing")
            workspace = host_monitor["activeWorkspace"]["id"]
            hypr("eval", f'hl.window_rule({{name="{rule}",match={{class="^aquamarine$"}},workspace="{workspace} silent",no_initial_focus=true}})')
            rule_added = True
            with (root / "hypr.log").open("w") as log:
                nested = subprocess.Popen(["Hyprland", "--config", str(config)], env=env,
                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                processes.append(nested)
            instance = wait(lambda: next((i for i in json.loads(hypr("instances", "-j"))
                if i["instance"] not in instances and i["pid"] == nested.pid), None), "Nested compositor did not start")
            signature = instance["instance"]
            wait(lambda: json.loads(hypr("-j", "monitors", instance=signature)), "Nested output missing")
            # Initial module setup in the new disposable compositor, before any client.
            if hypr("plugin", "load", str(module), instance=signature, timeout=45).strip() != "ok":
                raise RuntimeError("Candidate module could not load in the new compositor")
            hypr("eval", "hl.config({plugin={breezebars={enabled=true}}})", instance=signature)
            native_env = dict(env, WAYLAND_DISPLAY=str(runtime / instance["wl_socket"]), HYPRLAND_INSTANCE_SIGNATURE=signature)
            with (root / "client.log").open("w") as log:
                processes.append(subprocess.Popen(["kitty", "--config", "NONE", "--class", "bwm-r6-window",
                    "--title", "BWM R6 fixture", "-e", "/usr/bin/sleep", "120"], env=native_env,
                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True))
            def decorated():
                state = json.loads(hypr("-j", "breezebars-csd", instance=signature))
                report["lastDecorationState"] = state
                return next((w for w in state["windows"] if w["class"] == "bwm-r6-window" and w["kind"] == "kde"), None)
            view = wait(decorated, "Native decoration never arrived")
            output = json.loads(hypr("-j", "monitors", instance=signature))[0]["name"]

            def capture(name):
                path = root / f"{name}.png"
                time.sleep(.25)
                subprocess.run(["grim", "-o", output, str(path)], env=native_env, check=True, capture_output=True, timeout=10)
                with Image.open(path) as image:
                    return image.convert("RGB")

            client_before = next(w for w in json.loads(hypr("-j", "clients", instance=signature)) if w["class"] == "bwm-r6-window")
            shadow = capture("shadow")
            hypr("eval", 'hl.window_rule({name="fixture-shadow-off",match={class="^bwm-r6-window$"},no_shadow=true})', instance=signature)
            plain = capture("plain")
            client = next(w for w in json.loads(hypr("-j", "clients", instance=signature)) if w["class"] == "bwm-r6-window")
            if any(client[key] != client_before[key] for key in ("pid", "at", "size")):
                raise AssertionError("Fixture identity/geometry changed during shadow comparison")
            x,y = client["at"]; width,height = client["size"]; b = view["borders"]
            frame = (int(x-b["left"]),int(y-b["top"]),int(x+width+b["right"]),int(y+height+b["bottom"]))
            difference = ImageChops.difference(shadow, plain)
            difference.paste((0,0,0), frame)
            affected = sum(any(p) for p in difference.getdata())
            if affected < 100:
                raise AssertionError(f"No measurable external shadow in GPU output ({affected} changed pixels)")
            report.update(passed=True, nativeDecoration=True, externalShadowChangedPixels=affected,
                externalDifferenceBounds=difference.getbbox(), nestedConfigErrors=hypr("configerrors", instance=signature).strip())
            if report["nestedConfigErrors"]:
                raise AssertionError(report["nestedConfigErrors"])
        except Exception as error:
            report.update(passed=False,error=str(error))
            report["nestedLogTail"] = (root / "hypr.log").read_text(errors="replace")[-2500:] if (root / "hypr.log").exists() else ""
            for name in ("client", "helper"):
                report[name+"LogTail"] = (root / f"{name}.log").read_text(errors="replace")[-1200:] if (root / f"{name}.log").exists() else ""
        finally:
            for process in reversed(processes):
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL); process.wait(5)
            if host_created:
                hypr("output", "remove", host_output)
            # Retire the temporary rule as prescribed in AGENTS.md.
            if rule_added:
                hypr("reload")
                time.sleep(.5)
            # A blocked nested client can cause its parent to launch an unresponsive
            # application dialog outside the fixture process group. Retire only new
            # dialogs that explicitly name this test's aquamarine backend.
            for client in json.loads(hypr("-j", "clients")):
                if client.get("class") != "hyprland-dialog" or client["pid"] in dialogs_before:
                    continue
                try:
                    argv = Path(f'/proc/{client["pid"]}/cmdline').read_bytes().split(b'\0')
                    if any(b'An application aquamarine - WAYLAND-1 - aquamarine is not responding.' in arg for arg in argv):
                        os.kill(client["pid"], signal.SIGTERM)
                except (ProcessLookupError, FileNotFoundError):
                    pass
            time.sleep(.1)
            cursor = before["cursor"]
            if json.loads(hypr("-j", "cursorpos")) != cursor:
                hypr("dispatch", f'hl.dsp.cursor.move({{x={cursor["x"]},y={cursor["y"]}}})')
    after = snapshot()
    report["sessionUnchanged"] = after == before
    report["sessionDifferences"] = [key for key in before if before[key] != after[key]]
    report["cleanupVerified"] = {i["instance"] for i in json.loads(hypr("instances", "-j"))} <= instances
    report["sessionConfigErrors"] = hypr("configerrors").strip()
    report["passed"] = report["passed"] and report["sessionUnchanged"] and report["cleanupVerified"] and not report["sessionConfigErrors"]
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(report,ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
