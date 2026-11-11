// SPDX-License-Identifier: GPL-2.0-or-later
// BWM: Show Desktop lifecycle on the shared minimize state; no panel geometry heuristics.
pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
Singleton {
    id: root
    property bool showingDesktop: false
    property double enteredAt: 0
    onShowingDesktopChanged: enteredAt = Date.now()
    function toggle() {
        Quickshell.execDetached(["/home/sasel/.config/hypr/skins/plasma/scripts/kwin-window.py", "show-desktop"]);
    }
    function leave() {
        showingDesktop = false;
        Quickshell.execDetached(["/home/sasel/.config/hypr/skins/plasma/scripts/kwin-window.py", "show-desktop", "leave"]);
    }
    FileView {
        path: (Quickshell.env("XDG_RUNTIME_DIR") || "/tmp") + "/bwm-show-desktop.json"
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: {
            try { root.showingDesktop = (JSON.parse(text()).windows ?? []).length > 0; }
            catch (e) { root.showingDesktop = false; }
        }
        onLoadFailed: root.showingDesktop = false
    }
    // PanelState already refreshes the common window model for panel geometry.
    Connections {
        target: HyprlandData
        function onWindowListChanged() {
            if (!root.showingDesktop || Date.now() - root.enteredAt < 800) return;
            const visibleIds = [];
            for (const m of HyprlandData.monitors) {
                if (m.activeWorkspace?.id > 0) visibleIds.push(m.activeWorkspace.id);
                if (m.specialWorkspace?.id > 0) visibleIds.push(m.specialWorkspace.id);
            }
            if (HyprlandData.windowList.some(c => c.mapped !== false && !c.hidden && visibleIds.includes(c.workspace?.id))) root.leave();
        }
    }
}
