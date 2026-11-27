#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""T6 client for check-focus-safety.py: real zoom, Emoji Selector and KDE FileChooser.

Only runs in the disposable compositor supplied by that harness. Its helper state,
portal service/configuration and D-Bus are private; no input goes to the daily session.
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]

def wait(predicate, message, timeout=10):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        value = predicate()
        if value: return value
        time.sleep(.1)
    raise RuntimeError(message)

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec); spec.loader.exec_module(loaded)
    return loaded

def hypr(*args):
    return subprocess.check_output(["hyprctl", *args], text=True, timeout=3)

def main():
    if os.environ.get("BWM_FOCUS_NESTED") != "1": raise RuntimeError("Disposable compositor required")
    pid = int(os.environ["BWM_FOCUS_COMPOSITOR_PID"])
    assert any(i["pid"] == pid and i["instance"] == os.environ["HYPRLAND_INSTANCE_SIGNATURE"] for i in json.loads(hypr("instances", "-j")))
    if sys.argv[1:] != ["--private"]:
        path = Path(os.environ["XDG_CONFIG_HOME"]).parent / "t6-private.log"
        with path.open("w+") as log:
            result = subprocess.run(["dbus-run-session", "--", sys.executable, __file__, "--private"], stdout=log, stderr=subprocess.STDOUT, check=False, timeout=45)
            log.seek(0); content = log.read()
            for line in content.splitlines():
                if "PASS:" in line: print(line[line.index("PASS:"):])
            if result.returncode: print(content[-3500:],file=sys.stderr)
        return result.returncode
    from gi.repository import Gio, GLib
    root = Path(os.environ["XDG_CONFIG_HOME"]).parent
    assert root.name.startswith("bwm-focus-safety-")
    processes = []
    logs = []
    try:
        cfg = Path(os.environ["XDG_CONFIG_HOME"]) / "illogical-impulse"
        cfg.mkdir(); (cfg / "config.json").write_text('{"appearance":{"bwmTheme":"plasma"}}')
        actions = module("t6_actions_real", ROOT / "config/hypr/skins/plasma/scripts/desktop-actions.py")
        actions.RUNTIME = root / "actions-runtime"; actions.RUNTIME.mkdir()
        actions.STATE = actions.RUNTIME / "bwm-plasma-zoom.json"
        def factor(): return json.loads(hypr("getoption", "cursor:zoom_factor", "-j"))["float"]
        assert factor() == 1
        for action, expected in [("in",1.2),("in",1.44),("out",1.2),("reset",1)]:
            assert actions.main(["zoom",action]) == 0
            assert abs(factor()-expected) < .0001, (factor(),expected)
        actions.zoom("leave"); assert not actions.STATE.exists()
        print("PASS: real Hyprland zoom in/out/reset and cleanup", flush=True)

        def launch(name, argv, env=None):
            log = (root / (name+".log")).open("w+"); logs.append(log)
            proc = subprocess.Popen(argv, env=env, stdout=log, stderr=subprocess.STDOUT)
            processes.append(proc); return proc
        # Render the same scoped configuration as the session manager, but its
        # drop-in and processes are confined to the harness directories/private bus.
        sys.path.insert(0,str(ROOT / "config/hypr/scripts"))
        portals = module("t6_portals_real", ROOT / "config/hypr/scripts/bwm_portals.py")
        portals.RUNTIME = root / "portal-runtime"; portals.PROFILE = portals.RUNTIME / "bwm-portals"
        portals.DROPIN = portals.RUNTIME / "systemd/user/xdg-desktop-portal.service.d/50-bwm.conf"
        config = portals.CONFIG / "xdg-desktop-portal/portals.conf"; config.parent.mkdir()
        config.write_text("[preferred]\ndefault=hyprland;gtk;\norg.freedesktop.impl.portal.FileChooser=gtk;\n")
        portals.apply("plasma",restart=False)
        env = dict(os.environ, XDG_CONFIG_HOME=str(portals.PROFILE), XDG_CURRENT_DESKTOP="Hyprland")
        # Qt can activate the host portal while starting its platform theme.
        # Give private-bus activation the profile too, so that race cannot pick GTK.
        subprocess.run(["dbus-update-activation-environment", "XDG_CONFIG_HOME="+str(portals.PROFILE), "XDG_CURRENT_DESKTOP=Hyprland"],check=True,timeout=3)
        kde = launch("kde",["/usr/libexec/xdg-desktop-portal-kde"], dict(env,QT_QPA_PLATFORMTHEME="",QT_STYLE_OVERRIDE="Breeze"))
        desktop = launch("portal",["/usr/libexec/xdg-desktop-portal","--verbose"], env)
        bus = Gio.bus_get_sync(Gio.BusType.SESSION,None)
        def has_filechooser():
            try:
                return bus.call_sync("org.freedesktop.portal.Desktop","/org/freedesktop/portal/desktop","org.freedesktop.DBus.Properties","Get",GLib.Variant("(ss)",("org.freedesktop.portal.FileChooser","version")),None,Gio.DBusCallFlags.NONE,700,None)
            except GLib.Error: return None
        wait(has_filechooser,"Portal FileChooser did not register")
        kde_pid = bus.call_sync("org.freedesktop.DBus","/org/freedesktop/DBus","org.freedesktop.DBus","GetConnectionUnixProcessID",GLib.Variant("(s)",("org.freedesktop.impl.portal.desktop.kde",)),None,Gio.DBusCallFlags.NONE,1000,None).unpack()[0]
        options = {"handle_token":GLib.Variant("s","bwm_t6"),"current_folder":GLib.Variant("ay",list(str(root).encode()+b"\0"))}
        response = bus.call_sync("org.freedesktop.portal.Desktop","/org/freedesktop/portal/desktop","org.freedesktop.portal.FileChooser","OpenFile",GLib.Variant("(ssa{sv})",("","BWM T6 disposable chooser",options)),None,Gio.DBusCallFlags.NONE,5000,None)
        handle = response.unpack()[0]
        wait(lambda:any(c["pid"]==kde_pid for c in json.loads(hypr("-j","clients"))),"KDE FileChooser did not map a window")
        bus.call_sync("org.freedesktop.portal.Desktop",handle,"org.freedesktop.portal.Request","Close",None,None,Gio.DBusCallFlags.NONE,2000,None)
        wait(lambda:not any(c["pid"]==kde_pid for c in json.loads(hypr("-j","clients"))),"KDE FileChooser did not close")
        print("PASS: portal OpenFile maps original KDE dialog and Close cancels",flush=True)
        assert has_filechooser()
        os.environ["GTK_USE_PORTAL"] = "1"
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk
        Gtk.init([])
        chooser = Gtk.FileChooserNative.new("BWM T6 GTK chooser",None,Gtk.FileChooserAction.OPEN,"Open","Cancel")
        chooser.set_current_folder(str(root)); chooser.show()
        def gtk_dialog_visible(expected):
            context = GLib.MainContext.default()
            while context.pending():context.iteration(False)
            return any(c["pid"]==kde_pid for c in json.loads(hypr("-j","clients"))) == expected
        wait(lambda:gtk_dialog_visible(True),"GTK native chooser did not use KDE portal")
        chooser.destroy()
        wait(lambda:gtk_dialog_visible(False),"GTK native chooser did not cancel")
        print("PASS: GTK3 FileChooserNative uses KDE portal and cancels",flush=True)
        emoji = launch("emoji", ["plasma-emojier"])
        wait(lambda:any(c["pid"]==emoji.pid for c in json.loads(hypr("-j","clients"))), "Emoji Selector did not map a window")
        emoji.terminate(); emoji.wait(timeout=4)
        print("PASS: original Plasma Emoji Selector maps and closes", flush=True)
        stats = launch("stats", ["ksystemstats", "--remain"])
        sensors = root / "sensors.qml"
        sensors.write_text('''import QtQuick
import QtQuick.Window
import org.kde.ksysguard.sensors 1.0
Window {
    visible: false
    property int cpuSamples: 0
    property int memorySamples: 0
    function check() {
        if (cpuSamples >= 2 && memorySamples >= 2) {
            console.log("PASS: native Sensor receives live CPU and memory values")
            Qt.quit()
        }
    }
    Sensor {
        sensorId: "cpu/all/usage"
        onValueChanged: if (status === Sensor.Ready && Number.isFinite(Number(value)) && value >= 0 && value <= 100) { cpuSamples++; check(); }
    }
    Sensor {
        sensorId: "memory/physical/used"
        onValueChanged: if (status === Sensor.Ready && Number(value) > 0) { memorySamples++; check(); }
    }
    Timer { interval: 12000; running: true; onTriggered: Qt.exit(1) }
}
''')
        sampled = subprocess.run(["/usr/lib64/qt6/bin/qml", "-platform", "offscreen", str(sensors)],capture_output=True,text=True,timeout=15)
        print(sampled.stdout + sampled.stderr,flush=True)
        assert sampled.returncode == 0 and "PASS: native Sensor" in sampled.stdout + sampled.stderr, "CPU/memory data did not arrive: " + sampled.stdout + sampled.stderr
        host = ROOT / "build/bwm-plasma-host-tests/bwm-plasma-host"
        preview_runtime = root / "preview-runtime"; preview_runtime.mkdir(mode=0o700)
        preview_state = root / "preview-state"; preview_state.mkdir(mode=0o700)
        preview_env = dict(os.environ,XDG_RUNTIME_DIR=str(preview_runtime),XDG_STATE_HOME=str(preview_state))
        for plugin in ["org.kde.plasma.systemmonitor.cpu", "org.kde.plasma.systemmonitor.memory", "org.kde.plasma.calculator"]:
            preview = launch(plugin, [str(host), "--preview", plugin],preview_env)
            def mapped():
                if preview.poll() is not None:
                    log=logs[-1];log.flush();log.seek(0)
                    raise RuntimeError("Original widget preview exited: "+plugin+"\n"+log.read()[-2000:])
                return any(c["pid"]==preview.pid for c in json.loads(hypr("-j","clients")))
            wait(mapped,"Original widget preview did not map: "+plugin)
            time.sleep(1.2)
            assert preview.poll() is None
            if plugin == "org.kde.plasma.systemmonitor.cpu":
                subprocess.run(["grim", "-o", json.loads(hypr("-j","monitors"))[0]["name"], str(root / "cpu-preview.png")],check=True,timeout=3)
            preview.terminate(); preview.wait(timeout=4)
            log = logs[-1]; log.flush(); log.seek(0); content = log.read()
            assert "Error loading QML file" not in content and "is not installed" not in content, content[-1500:]
            print("PASS: original widget mapped without missing QML: "+plugin,flush=True)
        return 0
    finally:
        for proc in reversed(processes):
            if proc.poll() is None:
                proc.terminate()
                try: proc.wait(timeout=3)
                except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=3)
        for log in logs:
            log.seek(0); content=log.read()
            if "failed" in content.lower() or "error" in content.lower():print(content[-2200:],file=sys.stderr)
            log.close()

if __name__ == "__main__":
    raise SystemExit(main())
