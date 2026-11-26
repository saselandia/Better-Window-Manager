#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""End-to-end verification of native Plasma notifications in bwm-plasma-host.

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


def layers_by_namespace(instance: str, namespace: str) -> list[dict]:
    data = json.loads(hypr("-j", "layers", instance=instance))
    found: list[dict] = []
    for monitor_data in data.values():
        for level_layers in monitor_data.get("levels", {}).values():
            for layer in level_layers:
                if layer.get("namespace") == namespace:
                    found.append(layer)
    return found


def bus_owner_pid(env: dict[str, str], name: str) -> int | None:
    res = subprocess.run(
        ["busctl", "--user", "--auto-start=no", "call",
         "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
         "GetConnectionUnixProcessID", "s", name],
        env=env, capture_output=True, text=True, timeout=3, check=False,
    )
    if res.returncode != 0:
        return None
    parts = res.stdout.strip().split()
    return int(parts[1]) if len(parts) == 2 and parts[0] == "u" else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    if not os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        parser.error("A Hyprland parent session is required")
    if any(c.get("class") == "aquamarine" for c in json.loads(hypr("-j", "clients"))):
        parser.error("Another nested compositor is already open")

    output = f"BWM-NOTIF-{os.getpid()}"
    rule = f"bwm-notif-{os.getpid()}"
    created = rule_added = False
    nested = None
    dbus_proc = None
    host_proc = None
    report: dict = {"passed": False}

    with tempfile.TemporaryDirectory(prefix="bwm-notif-session-") as temporary:
        root = Path(temporary)
        try:
            hypr("output", "create", "headless", output)
            created = True
            hypr("eval", f'hl.monitor({{output="{output}",mode="1280x800@60",position="20000x20000",scale=1}})')
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
            for variable, name in [("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"), ("XDG_CACHE_HOME", "cache")]:
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
            report["nestedMonitors"] = nested_monitors
            parent_runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))

            host_env = dict(base_env)
            host_env.update(
                DBUS_SESSION_BUS_ADDRESS=bus_addr,
                DBUS_SYSTEM_BUS_ADDRESS=f"unix:path={root / 'no-system-bus'}",
                WAYLAND_DISPLAY=str(parent_runtime / instance["wl_socket"]),
                HYPRLAND_INSTANCE_SIGNATURE=signature,
                XDG_RUNTIME_DIR=str(nested_runtime),
                QT_QPA_PLATFORM="wayland",
                QT_QUICK_BACKEND="software",
                BWM_R5_HYPR_RUNTIME=str(parent_runtime),
            )
            with (root / "host.log").open("w") as hlog:
                host_proc = subprocess.Popen(
                    [str(args.binary.resolve())],
                    env=host_env, stdout=hlog, stderr=subprocess.STDOUT, start_new_session=True,
                )

            ready_file = nested_runtime / "bwm-plasma-host.ready"
            sock_path = nested_runtime / "bwm-plasma-host.sock"
            dnd_file = nested_runtime / "bwm-plasma-dnd"
            wait(lambda: ready_file.exists() and sock_path.exists(), "Host did not become ready", timeout=20.0)

            def poll_valid():
                try:
                    st = json.loads(host_ctl(sock_path, "notifications-status"))
                    return st if st.get("valid") else None
                except (OSError, ValueError):
                    return None

            notif_status = wait(poll_valid, "NotificationManager::Server did not become valid", timeout=10.0)
            report["initialStatus"] = notif_status

            wait(
                lambda: bus_owner_pid(host_env, "org.kde.JobViewServer") == host_proc.pid,
                "org.kde.JobViewServer did not register in time",
                timeout=10.0,
            )
            report["owners"] = {
                "org.freedesktop.Notifications": bus_owner_pid(host_env, "org.freedesktop.Notifications"),
                "org.kde.JobViewServer": bus_owner_pid(host_env, "org.kde.JobViewServer"),
                "org.kde.kuiserver": bus_owner_pid(host_env, "org.kde.kuiserver"),
                "hostPid": host_proc.pid,
            }
            report["initialLayers"] = json.loads(hypr("-j", "layers", instance=signature))
            if report["owners"]["org.freedesktop.Notifications"] != host_proc.pid:
                raise RuntimeError(f"Wrong owner for org.freedesktop.Notifications: {report['owners']}")
            if report["owners"]["org.kde.JobViewServer"] != host_proc.pid:
                raise RuntimeError(f"Wrong owner for org.kde.JobViewServer: {report['owners']}")

            # Send a real notification via notify-send and verify LayerShellQt popup (no xdg_toplevel client)
            subprocess.run(
                ["notify-send", "-a", "NestedTest", "-t", "10000", "Popup Test", "Desde Hyprland anidado"],
                env=host_env, check=True, timeout=5,
            )
            popup_layers = wait(
                lambda: [l for l in layers_by_namespace(signature, "bwm-plasma-notification") if l.get("y", 0) > 400],
                "Native Plasma notification popup layer did not appear at bottom edge",
                timeout=8.0,
            )
            clients_during_popup = json.loads(hypr("-j", "clients", instance=signature))
            report["defaultPopupLayers"] = popup_layers
            report["clientsDuringPopup"] = len(clients_during_popup)
            if len(clients_during_popup) != 0:
                raise RuntimeError(f"Notification popup leaked as xdg_toplevel client: {clients_during_popup}")
            first = popup_layers[0]
            if first.get("w", 0) <= 0 or first.get("h", 0) <= 0 or first.get("x", 0) <= 0:
                raise RuntimeError(f"Invalid popup geometry: {first}")

            # Change PopupPosition to TopLeft in plasmanotifyrc (as kcm_notifications does) and notify via KConfig D-Bus signal
            notifyrc = Path(host_env["XDG_CONFIG_HOME"]) / "plasmanotifyrc"
            notifyrc.write_text("[Notifications]\nPopupPosition=TopLeft\nPopupTimeout=10000\n")
            subprocess.run(
                ["busctl", "--user", "emit", "/plasmanotifyrc",
                 "org.kde.kconfig.notify", "ConfigChanged", "a{saay}", "1", "Notifications", "0"],
                env=host_env, check=True, timeout=3,
            )
            time.sleep(0.4)
            subprocess.run(
                ["notify-send", "-a", "TopLeftTest", "-t", "10000", "TopLeft Popup", "Movido por plasmanotifyrc"],
                env=host_env, check=True, timeout=5,
            )
            topleft_layers = wait(
                lambda: [l for l in layers_by_namespace(signature, "bwm-plasma-notification")
                         if 0 < l.get("x", 0) < 200 and 0 < l.get("y", 0) < 200],
                "PopupPosition=TopLeft did not move notification popup to top-left",
                timeout=8.0,
            )
            report["topLeftPopupLayers"] = topleft_layers

            # DND control via socket + dnd state file
            dnd_on = host_ctl(sock_path, "dnd-set true")
            if dnd_on != "true" or dnd_file.read_text().strip() != "true":
                raise RuntimeError(f"DND enable failed: reply={dnd_on!r} file={dnd_file.read_text()!r}")
            dnd_toggle = host_ctl(sock_path, "dnd-toggle")
            if dnd_toggle != "false" or dnd_file.read_text().strip() != "false":
                raise RuntimeError(f"DND toggle off failed: reply={dnd_toggle!r} file={dnd_file.read_text()!r}")
            report["dndVerified"] = True

            # Clean shutdown releases D-Bus name and removes dnd state file
            host_proc.terminate()
            host_proc.wait(timeout=8)
            host_proc = None
            report["ownerAfterStop"] = bus_owner_pid(host_env, "org.freedesktop.Notifications")
            report["dndFileAfterStop"] = dnd_file.exists()
            if report["ownerAfterStop"] is not None or report["dndFileAfterStop"]:
                raise RuntimeError("Host did not cleanly release notification service / dnd file on stop")

            report["passed"] = True
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
