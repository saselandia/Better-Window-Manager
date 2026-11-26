// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import qs
import qs.modules.common
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland

Scope {
    id: root
    readonly property string helper: Quickshell.env("HOME") + "/.config/hypr/skins/plasma/scripts/session-ui.py"
    function open() { Quickshell.execDetached(["python3", helper, "prompt", "all"]); }
    function close() { Quickshell.execDetached(["python3", helper, "cancel"]); }
    function toggle() { Quickshell.execDetached(["python3", helper, "toggle"]); }
    Connections {
        target: GlobalStates
        function onSessionOpenChanged() {
            if (!GlobalStates.sessionOpen) return;
            GlobalStates.sessionOpen = false;
            root.open();
        }
    }
    IpcHandler {
        target: "session"
        function open(): void { root.open(); }
        function close(): void { root.close(); }
        function toggle(): void { root.toggle(); }
    }
    GlobalShortcut { name: "sessionOpen"; description: "Opens session screen on press"; onPressed: root.open() }
    GlobalShortcut { name: "sessionClose"; description: "Closes session screen on press"; onPressed: root.close() }
    GlobalShortcut { name: "sessionToggle"; description: "Toggles session screen on press"; onPressed: root.toggle() }
}
