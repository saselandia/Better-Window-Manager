// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import Quickshell
import Quickshell.Io

/**
 * BWM F11: reads the effective KWin/KDE values exactly as the F2 bridge applies them
 * (kde-config-bridge.py kwin-settings) and writes KDE's own files with kwriteconfig6 --notify, so
 * the bridge's watcher translates them to Hyprland (and KDE apps see the KConfig change signal).
 * Never writes BWM's configuration directly.
 */
QtObject {
    id: store
    property var values: ({})
    property bool ready: false
    readonly property string bridge: Quickshell.env("HOME") + "/.config/hypr/skins/plasma/scripts/kde-config-bridge.py"

    function reload() { reader.running = true; }
    // file: kwinrc | kdeglobals; value: string
    function write(file, group, key, value, valueKey) {
        writer.command = ["kwriteconfig6", "--notify", "--file", file, "--group", group, "--key", key, String(value)];
        if (valueKey) store.values = Object.assign({}, store.values, { [valueKey]: value });
        writer.running = true;
    }

    property Process reader: Process {
        command: ["python3", store.bridge, "kwin-settings"]
        stdout: StdioCollector {
            onStreamFinished: {
                try { store.values = JSON.parse(text); store.ready = true; }
                catch (e) { console.warn("BWM settings: kwin-settings", e); }
            }
        }
    }
    property Process writer: Process {
        onExited: (code) => { if (code !== 0) console.warn("BWM settings: kwriteconfig6 failed", code); }
    }
    Component.onCompleted: reload()
}
