pragma Singleton

import qs.modules.common
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland

/**
 * Plasma 6 floating panel behaviour: the panel stops floating (docks to the
 * screen edge) while a window is maximized or fullscreen on its monitor, and
 * floats again when there is none.
 *
 * "Maximized" covers Hyprland fullscreen modes and the KDE-style maximize used
 * by the Plasma theme (quick-tile.py / titlebar button), which is a floating
 * window filling the monitor's usable area.
 */
Singleton {
    id: root

    readonly property bool active: Appearance.sizes.plasmaFloating
    // Monitor name -> true while it has a maximized window on its active workspace
    property var docked: ({})

    function isDocked(screenName) {
        return root.active && root.docked[screenName] === true;
    }
    // Gap the panel and its popups keep from the screen edges on that screen
    function gapFor(screenName) {
        return root.active && !root.isDocked(screenName) ? Appearance.sizes.plasmaFloatingGap : 0;
    }

    // Distance from the screen edge to the outer side of the panel, where popups attach:
    // floating = gap + panel thickness + gap above it; docked = just the panel thickness.
    // The panel keeps its thickness in both states (only its side/bottom margins change).
    function panelEdgeOffset(screenName) {
        return Appearance.sizes.plasmaPanelHeight + 2 * root.gapFor(screenName);
    }

    function refresh() {
        if (root.active && !stateProc.running) stateProc.running = true;
    }

    Process {
        id: stateProc
        command: ["sh", "-c", "printf '['; hyprctl -j monitors; printf ','; hyprctl -j clients; printf ']'"]
        stdout: StdioCollector {
            onStreamFinished: {
                let monitors, clients;
                try {
                    [monitors, clients] = JSON.parse(text);
                } catch (e) {
                    return;
                }
                const result = {};
                const tolerance = 24;
                for (const m of monitors) {
                    // reserved = [left, top, right, bottom]
                    const [rl, rt, rr, rb] = m.reserved ?? [0, 0, 0, 0];
                    const usableW = m.width / m.scale - rl - rr;
                    const usableH = m.height / m.scale - rt - rb;
                    const workspaces = [m.activeWorkspace?.id, m.specialWorkspace?.id].filter(id => id !== undefined && id !== 0);
                    result[m.name] = clients.some(c =>
                        c.monitor === m.id && c.mapped !== false && !c.hidden
                        && workspaces.includes(c.workspace?.id)
                        && (c.fullscreen > 0
                            || (c.size[0] >= usableW - tolerance && c.size[1] >= usableH - tolerance)));
                }
                if (JSON.stringify(result) !== JSON.stringify(root.docked))
                    root.docked = result;
            }
        }
    }

    // Window/workspace/fullscreen events refresh immediately (debounced)
    Connections {
        target: Hyprland
        enabled: root.active
        function onRawEvent(event) {
            debounce.restart();
        }
    }
    Timer {
        id: debounce
        interval: 60
        onTriggered: root.refresh()
    }
    // Resizes (maximize from quick-tile) emit no Hyprland event: poll lightly as a fallback
    Timer {
        interval: 700
        repeat: true
        running: root.active
        triggeredOnStart: true
        onTriggered: root.refresh()
    }
    onActiveChanged: if (!active) root.docked = ({})
}
