/*
    SPDX-FileCopyrightText: 2026 BWM
    SPDX-License-Identifier: GPL-2.0-or-later
*/
pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import org.kde.ksvg as KSvg
import org.kde.kirigami as Kirigami
import qs
import qs.modules.plasma.panel

/**
 * BWM: anfitrión del Kickoff portado (fase 4 de docs/BREEZE_PLAN.md). En Plasma lo muestra un
 * PlasmaQuick::Dialog junto al botón del panel; aquí una capa de layer-shell a pantalla completa
 * con el mismo fondo del estilo de Plasma activo («dialogs/background», sin el borde que toca al
 * panel cuando está pegado) y el mismo comportamiento: se cierra al pulsar fuera salvo que esté
 * fijado («Mantener abierto»), con Escape o al lanzar algo.
 *
 * Se abre con el botón del panel (PanelContent.qml), Super/Alt+F1 (keybinds-manager) y la IPC
 * `qs -c ii ipc call plasmaKickoff toggle|open|close`, que siguen igual que antes.
 */
Scope {
    id: root

    readonly property bool opened: GlobalStates.plasmaKickoffOpen

    function open(screenName) {
        GlobalStates.plasmaKickoffScreen = screenName || Hyprland.focusedMonitor?.name || "";
        GlobalStates.plasmaKickoffOpen = true;
    }
    function close() {
        GlobalStates.plasmaKickoffOpen = false;
        GlobalStates.plasmaKickoffAnchorX = -1;
    }
    function toggle() {
        if (root.opened)
            root.close();
        else
            root.open("");
    }

    IpcHandler {
        target: "plasmaKickoff"
        function toggle(): void { root.toggle(); }
        function open(): void { root.open(""); }
        function close(): void { root.close(); }
    }

    PanelWindow {
        id: win

        readonly property string screenName: screen?.name ?? ""
        readonly property string edge: PanelState.edgeFor(screenName)
        readonly property real distance: PanelState.distanceFor(screenName)
        readonly property real gap: PanelState.gapFor(screenName)
        readonly property bool floatingPanel: gap > 0
        // Tamaño de la superficie: el de la pantalla (las cuatro anclas la estiran)
        readonly property real areaWidth: screen?.width ?? 0
        readonly property real areaHeight: screen?.height ?? 0

        visible: root.opened
        screen: Quickshell.screens.find(s => s.name === GlobalStates.plasmaKickoffScreen)
            ?? Quickshell.screens.find(s => s.name === Hyprland.focusedMonitor?.name) ?? Quickshell.screens[0]
        color: "transparent"
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "quickshell:plasmaKickoff"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: root.opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
        anchors { top: true; bottom: true; left: true; right: true }

        // Pulsar fuera: como hideOnWindowDeactivate de un plasmoide (no se cierra si está fijado)
        MouseArea {
            anchors.fill: parent
            onClicked: if (kickoff.hideOnWindowDeactivate) root.close()
        }

        KSvg.FrameSvgItem {
            id: frame
            // Plasma usa la variante translúcida sólo con el efecto de desenfoque de KWin; Breeze no
            // desenfoca (decoration.blur apagado), así que, como Plasma sin desenfoque, la sólida
            imagePath: "solid/dialogs/background"
            // Pegado al panel: sin el borde que lo toca, como PlasmaQuick::Dialog
            enabledBorders: win.floatingPanel ? KSvg.FrameSvgItem.AllBorders
                : ({ bottom: KSvg.FrameSvgItem.AllBorders & ~KSvg.FrameSvgItem.BottomBorder,
                     top: KSvg.FrameSvgItem.AllBorders & ~KSvg.FrameSvgItem.TopBorder,
                     left: KSvg.FrameSvgItem.AllBorders & ~KSvg.FrameSvgItem.LeftBorder,
                     right: KSvg.FrameSvgItem.AllBorders & ~KSvg.FrameSvgItem.RightBorder })[win.edge]
                  ?? KSvg.FrameSvgItem.AllBorders

            width: Math.min(win.areaWidth, kickoff.implicitWidth + margins.left + margins.right)
            height: Math.min(win.areaHeight - win.distance, kickoff.implicitHeight + margins.top + margins.bottom)

            readonly property real anchorX: GlobalStates.plasmaKickoffAnchorX
            readonly property real anchorY: GlobalStates.plasmaPopupAnchorY
            function clamp(v, size, total) {
                return Math.max(win.gap, Math.min(total - size - win.gap, v));
            }
            x: win.edge === "left" ? win.distance
                : win.edge === "right" ? win.areaWidth - width - win.distance
                : clamp(anchorX >= 0 ? anchorX - width / 2 : 0, width, win.areaWidth)
            y: win.edge === "top" ? win.distance
                : win.edge === "bottom" ? win.areaHeight - height - win.distance
                : clamp(anchorY >= 0 ? anchorY - height / 2 : 0, height, win.areaHeight)

            // Que los clics dentro no cierren
            MouseArea {
                anchors.fill: parent
            }

            Kickoff {
                id: kickoff
                x: frame.margins.left
                y: frame.margins.top
                width: frame.width - frame.margins.left - frame.margins.right
                height: frame.height - frame.margins.top - frame.margins.bottom
                focus: root.opened
            }
        }

        onVisibleChanged: if (visible) Qt.callLater(() => kickoff.forceActiveFocus())
    }
}
