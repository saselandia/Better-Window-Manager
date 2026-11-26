#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""T4: native layouts, theme logout and original KSplash, in a private session.

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
    parser.add_argument("--layan",type=Path,required=True)
    args = parser.parse_args()

    if not os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        parser.error("A Hyprland parent session is required")
    if any(c.get("class") == "aquamarine" for c in json.loads(hypr("-j", "clients"))):
        parser.error("Another nested compositor is already open")

    output = f"BWM-T4-{os.getpid()}"
    rule = f"bwm-t4-{os.getpid()}"
    created = rule_added = False
    nested = None
    dbus_proc = None
    host_proc = None
    report: dict = {"passed": False}

    with tempfile.TemporaryDirectory(prefix="bwm-t4-session-") as temporary:
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
            scripts=Path(__file__).resolve().parents[2] / "config/hypr/skins/plasma/scripts"
            helper=scripts / "session-ui.py"
            packages=Path(host_env["XDG_DATA_HOME"])/"plasma/look-and-feel"
            packages.mkdir(parents=True)
            (packages/"Sweet").symlink_to(Path.home()/".local/share/plasma/look-and-feel/Sweet",target_is_directory=True)
            layan=args.layan.resolve()/"plasma/look-and-feel/com.github.vinceliuice.Layan"
            (packages/"com.github.vinceliuice.Layan").symlink_to(layan,target_is_directory=True)
            report["layanRevision"]=subprocess.check_output(["git","-C",str(args.layan),"rev-parse","HEAD"],text=True).strip()
            for name,code in [("org.bwm.t4.broken",'var panel=new Panel(); throw Error("deliberate rollback");'),("org.bwm.t4.loop",'while(true){}')]:
                package=packages/name
                (package/"contents/layouts").mkdir(parents=True)
                (package/"metadata.json").write_text(json.dumps({"KPackageStructure":"Plasma/LookAndFeel","KPlugin":{"Id":name,"Name":name,"License":"GPL-2.0-or-later"}}))
                (package/"contents/layouts/org.kde.plasma.desktop-layout.js").write_text(code)
            custom=packages/"org.bwm.t4.customlogout"
            (custom/"contents/logout").mkdir(parents=True)
            (custom/"metadata.json").write_text(json.dumps({"KPackageStructure":"Plasma/LookAndFeel","KPlugin":{"Id":"org.bwm.t4.customlogout","Name":"Test logout","License":"GPL-2.0-or-later"}}))
            (custom/"contents/logout/Logout.qml").write_text("import QtQuick\nRectangle {color: \"#782345\"; signal logoutRequested(); signal haltRequested(); signal rebootRequested(); signal suspendRequested(int type); signal lockScreenRequested(); signal cancelRequested(); function finish(){Qt.quit();}}\n")
            cfg=Path(host_env["XDG_CONFIG_HOME"])/"illogical-impulse";cfg.mkdir()
            (cfg/"config.json").write_text('{"appearance":{"bwmTheme":"plasma"}}')
            with (root/"fixture.log").open("w") as log:
                test=subprocess.run([str(args.test.resolve())],env=host_env,stdout=log,stderr=subprocess.STDOUT,timeout=90)
            report["fixture"]=(root/"fixture.log").read_text(errors="replace")[-10000:]
            if test.returncode:raise RuntimeError("Native T4 fixture failed")
            (Path(host_env["XDG_CONFIG_HOME"])/"kdeglobals").write_text("[KDE]\nLookAndFeelPackage=org.kde.breeze.desktop\n")
            # Fallback without the native host: one auxiliary dialog, original
            # theme, cancellation via IPC. Dry-run is an additional hard boundary.
            aux_env=dict(host_env,BWM_POWER_DRY_RUN="1")
            aux_log=(root/"auxiliary.log").open("w")
            aux=subprocess.Popen([str(args.binary.resolve()),"--logout-dialog","all"],env=aux_env,stdout=aux_log,stderr=subprocess.STDOUT,start_new_session=True)
            try:
                aux_socket=nested_runtime/"bwm-plasma-logout.sock"
                wait(lambda:aux_socket.exists(),"Fallback dialog did not create its socket")
                time.sleep(.25)
                duplicate=subprocess.run([str(args.binary.resolve()),"--logout-dialog","all"],env=aux_env,capture_output=True,timeout=8)
                if duplicate.returncode or aux.poll() is not None:raise RuntimeError("Fallback dialog was duplicated or closed prematurely")
                subprocess.run(["python3",str(helper),"cancel"],env=aux_env,check=True,timeout=4)
                if aux.wait(timeout=5):raise RuntimeError("Fallback cancellation failed")
                report["fallbackDialogSingleAndCancelled"]=True
            finally:
                if aux.poll() is None:aux.terminate();aux.wait(timeout=5)
                aux_log.close()
            if "[dry-run]" in (root/"auxiliary.log").read_text(errors="replace"):raise RuntimeError("Cancelling a dialog attempted a power action")
            report["splashes"]=[]
            for theme in ("org.kde.breeze.desktop","Sweet","com.github.vinceliuice.Layan"):
                with (root/"splash.log").open("w") as log:
                    splash=subprocess.Popen(["ksplashqml","--nofork",theme],env=host_env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                try:
                    def owner():
                        r=subprocess.run(["busctl","--user","--auto-start=no","call","org.freedesktop.DBus","/org/freedesktop/DBus","org.freedesktop.DBus","GetConnectionUnixProcessID","s","org.kde.KSplash"],env=host_env,capture_output=True,text=True,timeout=3)
                        return r.stdout.strip()==f"u {splash.pid}"
                    wait(owner,"Original KSplash did not register",timeout=5)
                    time.sleep(.3)
                    subprocess.run(["python3",str(helper),"splash-finish",str(splash.pid)],env=host_env,check=True,timeout=10)
                    code=splash.wait(timeout=5)
                    report["splashes"].append({"theme":theme,"exitCode":code,"log":(root/"splash.log").read_text(errors="replace")[-2000:]})
                    if code:raise RuntimeError("Original KSplash failed")
                finally:
                    if splash.poll() is None:splash.terminate();splash.wait(timeout=5)
            # Exercise the actual supervisor with real disposable --session hosts.
            # Their virtual outputs have no EDID, so native PanelRuntime refuses a
            # persistent output binding: this must trigger a safe rollback.
            import importlib.util
            spec=importlib.util.spec_from_file_location("t4_supervisor",helper)
            prior_env=dict(os.environ);os.environ.clear();os.environ.update(host_env)
            processes=[]
            try:
                supervisor=importlib.util.module_from_spec(spec);spec.loader.exec_module(supervisor)
                staged=json.loads((Path(host_env["XDG_CONFIG_HOME"])/"bwm-plasma-host/last-layout.json").read_text())
                def launch_host():
                    proc=subprocess.Popen([str(args.binary.resolve()),"--session"],env=host_env,
                        stdout=(root/"host.log").open("a"),stderr=subprocess.STDOUT,start_new_session=True)
                    processes.append(proc)
                    try:wait(lambda:supervisor.host.ready_pid()==proc.pid,"Disposable replacement host not ready",timeout=20)
                    except TimeoutError:return 1
                    return 0
                supervisor.host.start_host=launch_host
                code=supervisor.replace_layout(9999999999,staged["candidate"],staged["previous"])
                result=json.loads((supervisor.LEGACY/"last-layout.json").read_text())
                if code!=1 or result.get("phase")!="rolled-back" or not result.get("restored"):
                    raise RuntimeError("Supervisor did not roll back an unrenderable replacement")
                report["actualSupervisorRollback"]=result
            finally:
                for proc in processes:
                    if proc.poll() is None:proc.terminate();proc.wait(timeout=8)
                os.environ.clear();os.environ.update(prior_env)
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
