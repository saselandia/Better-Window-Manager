#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""T3: real native wallpaper configuration, production host and Python routes.

Runs bwm-plasma-host --session inside a disposable nested Hyprland on a temporary
headless output with a private D-Bus session and isolated XDG dirs. Never touches
the user's daily host, bus, config or physical monitors.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import tempfile
import time


def hypr(*args: str, instance: str | None = None) -> str:
    return subprocess.run(
        ["hyprctl", *(["-i", instance] if instance else []), *args],
        check=True, capture_output=True, text=True, timeout=5,
    ).stdout


def wait(predicate, message: str, timeout: float = 15.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        value = predicate()
        if value:
            return value
        time.sleep(0.1)
    raise TimeoutError(message)


def host_ctl(sock_path: Path, cmd: str) -> str:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.settimeout(2.0)
        s.connect(str(sock_path))
        s.sendall((cmd + "\n").encode("utf-8"))
        chunks = []
        while True:
            data = s.recv(4096)
            if not data:
                break
            chunks.append(data)
            if b"\n" in data:
                break
        return b"".join(chunks).decode("utf-8", "ignore").strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    args = parser.parse_args()

    if not os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        parser.error("A Hyprland parent session is required")
    if any(c.get("class") == "aquamarine" for c in json.loads(hypr("-j", "clients"))):
        parser.error("Another nested compositor is already open")

    output = f"BWM-WALLPAPER-{os.getpid()}"
    rule = f"bwm-wallpaper-{os.getpid()}"
    created = rule_added = False
    nested = None
    dbus_proc = None
    host_proc = None
    report: dict = {"passed": False}

    with tempfile.TemporaryDirectory(prefix="bwm-wallpaper-session-") as temporary:
        root = Path(temporary)
        try:
            hypr("output", "create", "headless", output)
            created = True
            hypr("eval", f'hl.monitor({{output="{output}",mode="2800x1000@60",position="20000x20000",scale=1}})')
            monitor = wait(
                lambda: next((m for m in json.loads(hypr("-j", "monitors")) if m["name"] == output), None),
                "Temporary output did not appear",
            )
            workspace = monitor["activeWorkspace"]["id"]
            hypr(
                "eval",
                f'hl.window_rule({{name="{rule}",match={{class="^aquamarine$"}},workspace="{workspace} silent",no_initial_focus=true}})',
            )
            rule_added = True

            config = root / "hyprland.lua"
            config.write_text(
                'hl.monitor({output="",mode="1280x800",position="0x0",scale=1})\n'
                'hl.config({misc={disable_hyprland_logo=true,disable_splash_rendering=true},animations={enabled=false},'
                'xwayland={enabled=false},input={follow_mouse=2},decoration={blur={enabled=false}}})\n'
            )

            base_env = {
                k: v for k, v in os.environ.items()
                if not k.startswith(("QT_", "BWM_R4_", "BWM_R5_", "DBUS_"))
                and k not in ("HYPRLAND_INSTANCE_SIGNATURE", "WAYLAND_SOCKET", "DISPLAY", "XDG_ACTIVATION_TOKEN")
            }
            for variable, name in [("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"), ("XDG_CACHE_HOME", "cache"), ("XDG_STATE_HOME", "state")]:
                (root / name).mkdir(mode=0o700)
                base_env[variable] = str(root / name)
            nested_runtime = root / "runtime"
            nested_runtime.mkdir(mode=0o700)

            # Start private session D-Bus
            dbus_addr_path = root / "dbus.addr"
            dbus_proc = subprocess.Popen(
                ["dbus-daemon", "--session", "--nofork", f"--address=unix:path={root / 'bus'}", "--print-address=1"],
                env=base_env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                start_new_session=True,
            )
            assert dbus_proc.stdout is not None
            bus_addr = dbus_proc.stdout.readline().strip()
            dbus_addr_path.write_text(bus_addr)
            if not bus_addr:
                raise RuntimeError("Private dbus-daemon did not report an address")

            hypr_env = dict(base_env)
            hypr_env["DBUS_SESSION_BUS_ADDRESS"] = bus_addr
            hypr_env["DBUS_SYSTEM_BUS_ADDRESS"] = f"unix:path={root / 'no-system-bus'}"
            with (root / "hypr.log").open("w") as log:
                nested = subprocess.Popen(
                    ["Hyprland", "--config", str(config)],
                    env=hypr_env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                )

            instance = wait(
                lambda: next((i for i in json.loads(hypr("instances", "-j")) if i["pid"] == nested.pid), None),
                "Nested compositor did not start",
            )
            signature = instance["instance"]
            nested_monitors = wait(lambda: json.loads(hypr("-j", "monitors", instance=signature)), "Nested output missing")
            hypr("output", "create", "wayland", instance=signature)
            nested_monitors = wait(lambda: (m if len(m:=json.loads(hypr("-j","monitors",instance=signature)))==2 else None), "Second nested output missing")
            second_output = next(m["name"] for m in nested_monitors if m["name"] != nested_monitors[0]["name"])
            hypr("eval", f'hl.monitor({{output="{second_output}",mode="1280x800@60",position="1280x0",scale=1.25}})', instance=signature)
            nested_monitors = wait(lambda: (m if len(m:=json.loads(hypr("-j","monitors",instance=signature)))==2 and all(x["width"]>0 and x["height"]>0 for x in m) and any(x["name"]==second_output and x["scale"]==1.25 for x in m) else None), "Second nested mode missing")
            parent_windows = wait(lambda: (w if len(w:=[c for c in json.loads(hypr("-j","clients")) if c.get("pid")==nested.pid and c.get("class")=="aquamarine"])==2 else None), "Second nested surface missing")
            for index, window in enumerate(parent_windows):
                hypr("eval", f'local w=hl.get_window("address:{window["address"]}"); if w and w.pid=={nested.pid} then '
                     'hl.dispatch(hl.dsp.window.float({action="enable",window=w})); '
                     'hl.dispatch(hl.dsp.window.resize({x=1280,y=800,relative=false,window=w})); '
                     f'hl.dispatch(hl.dsp.window.move({{x={20020+index*1400},y=20020,relative=false,window=w}})); end')
            report["nestedMonitors"] = nested_monitors
            parent_runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))

            fake_bin = root / "fake-bin"
            fake_bin.mkdir()
            command_log = root / "engines.log"
            for name in ("swww", "awww", "pgrep"):
                script = fake_bin / name
                script.write_text("#!/bin/sh\n" + ("exit 1\n" if name == "pgrep" else
                    f"printf '%s\\n' \"{name} $*\" >> '{command_log}'\nexit 0\n"))
                script.chmod(0o755)
            host_env = dict(base_env)
            host_env["PATH"] = str(fake_bin) + ":" + os.environ["PATH"]
            host_env.update(
                DBUS_SESSION_BUS_ADDRESS=bus_addr,
                DBUS_SYSTEM_BUS_ADDRESS=f"unix:path={root / 'no-system-bus'}",
                WAYLAND_DISPLAY=str(parent_runtime / instance["wl_socket"]),
                HYPRLAND_INSTANCE_SIGNATURE=signature,
                XDG_RUNTIME_DIR=str(nested_runtime),
                QT_QPA_PLATFORM="wayland",
                QSG_RHI_BACKEND="opengl",
                BWM_R5_HYPR_RUNTIME=str(parent_runtime),
            )
            scripts = Path(__file__).resolve().parents[2] / "config/hypr/skins/plasma/scripts"
            helper = scripts / "wallpaper-sync.py"
            config_dir = Path(host_env["XDG_CONFIG_HOME"]) / "illogical-impulse"
            config_dir.mkdir()
            from PIL import Image
            first = root / "primero ñ.png"
            second = root / "segundo.png"
            Image.new("RGB", (256, 128), "#ca3149").save(first)
            Image.new("RGB", (256, 128), "#3149ca").save(second)
            for name in ("config.json", "config-plasma.json"):
                (config_dir / name).write_text(json.dumps({"appearance":{"bwmTheme":"plasma"},
                    "background":{"wallpaperPath":str(first),"thumbnailPath":str(first)}}))
            kdeglobals = Path(host_env["XDG_CONFIG_HOME"]) / "kdeglobals"
            kdeglobals.write_text("[General]\nColorScheme=BreezeDark\n")
            palette = kdeglobals.read_bytes()
            subprocess.run(["python3", str(helper), "install"], env=host_env, check=True, timeout=5)
            with (root / "fixture.log").open("w") as log:
                test = subprocess.run([str(args.test.resolve())], env=host_env, stdout=log, stderr=subprocess.STDOUT, timeout=65)
            report["nativeFixture"] = (root / "fixture.log").read_text(errors="replace")[-7000:]
            if test.returncode:
                raise RuntimeError("Native wallpaper fixture failed")
            ready_file = nested_runtime / "bwm-plasma-host.ready"
            sock_path = nested_runtime / "bwm-plasma-host.sock"
            def start():
                proc = subprocess.Popen([str(args.binary.resolve()), "--session"], env=host_env,
                    stdout=(root / "host.log").open("a"), stderr=subprocess.STDOUT, start_new_session=True)
                wait(lambda: ready_file.exists() and ready_file.read_text().strip()==str(proc.pid) and sock_path.exists(), "Host not ready", timeout=20)
                return proc
            def state():
                return json.loads(host_ctl(sock_path, "wallpaper-status"))
            def path_is(path):
                rows=state().get("screens",[])
                return rows and all(row.get("source")==str(path) for row in rows)
            host_proc=start()
            wait(lambda: path_is(first), "Initial BWM wallpaper did not seed Plasma", timeout=20)
            subprocess.run(["python3", str(helper), "route", str(second)], env=host_env, check=True, timeout=20)
            wait(lambda: path_is(second), "BWM did not reach native wallpaper")
            state_path=Path(host_env["XDG_STATE_HOME"]) / "bwm/plasma-wallpaper.json"
            wait(lambda: state_path.exists() and str(second) in state_path.read_text(), "Native wallpaper did not export")
            report["productionRoute"]=state()
            assert json.loads((config_dir / "config-plasma.json").read_text())["background"]["wallpaperPath"]==str(second)
            assert kdeglobals.read_bytes()==palette, "Wallpaper unexpectedly recolored Plasma"
            assert (Path(host_env["XDG_STATE_HOME"]) / "bwm/boot/.stamp").exists(), "Boot renderer did not run"
            # Fragmented requests cannot block another client or truncate Unicode/long paths.
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as fragmented:
                fragmented.settimeout(2)
                fragmented.connect(str(sock_path))
                fragmented.sendall(b"wallpaper-sta")
                assert state()["version"]==1
                fragmented.sendall(b"tus\n")
                assert b'"screens"' in fragmented.recv(65536)
            long_dir=root
            for _ in range(6): long_dir=long_dir / ("a"*95)
            long_dir.mkdir(parents=True)
            long_image=long_dir / "ñ largo.png"
            Image.new("RGB",(64,64),"#55aa33").save(long_image)
            subprocess.run(["python3",str(helper),"route",str(long_image)],env=host_env,check=True,timeout=20)
            wait(lambda:path_is(long_image),"Long socket request failed")
            report["fragmentedAndLongRequests"]=True
            host_proc.terminate();host_proc.wait(timeout=10);host_proc=None
            # Offline choice is queued; a skin entry does not flatten native choices.
            offline=subprocess.run(["python3",str(helper),"route",str(first)],env=host_env,timeout=10)
            assert offline.returncode==1
            subprocess.run(["python3",str(helper),"fallback"],env=host_env,check=True,timeout=10)
            assert "img" in command_log.read_text()
            host_proc=start()
            subprocess.run(["python3",str(helper),"resume"],env=host_env,check=True,timeout=10)
            wait(lambda:path_is(first),"Offline selection was not replayed")
            report["offlineResume"]=True
            # Crash leaves the ready file behind: fallback must still restore the last image.
            wait(lambda:state_path.exists() and str(first) in state_path.read_text(),"Last selection not exported")
            host_proc.kill();host_proc.wait(timeout=5);host_proc=None
            subprocess.run(["python3",str(helper),"fallback"],env=host_env,check=True,timeout=10)
            report["fallbackAfterCrash"]=True
            report["paletteUnchanged"]=kdeglobals.read_bytes()==palette
            report["engineCommands"]=command_log.read_text().splitlines()[-12:]
            report["passed"]=True
        except Exception as exc:
            report["passed"] = False
            report["error"] = str(exc)
            if (root / "host.log").exists():
                report["hostLogTail"] = (root / "host.log").read_text(errors="replace")[-3000:]
            if (root / "hypr.log").exists():
                report["hyprLogTail"] = (root / "hypr.log").read_text(errors="replace")[-1500:]
        finally:
            for proc in (host_proc, nested, dbus_proc):
                if proc and proc.poll() is None:
                    try:
                        os.killpg(proc.pid, signal.SIGTERM)
                        proc.wait(timeout=5)
                    except Exception:
                        try:
                            os.killpg(proc.pid, signal.SIGKILL)
                            proc.wait(timeout=3)
                        except Exception:
                            pass
            if rule_added:
                hypr("eval", f'hl.window_rule({{name="{rule}",match={{class="^bwm-notif-never$"}}}})')
            if created:
                hypr("output", "remove", output)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2))
    print(json.dumps({"passed": report["passed"], "error": report.get("error")}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
