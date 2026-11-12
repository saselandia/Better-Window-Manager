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
            // En Plasma el diálogo es una ventana propia y su borde recorta lo que se extiende hacia sus
            // márgenes (las pestañas del pie bajan bottomPadding); aquí la capa ocupa toda la pantalla y eso
            // tapaba 3 px del panel: se recorta en el borde del diálogo
            clip: true
            // Pegado al panel: sin el borde que lo toca, como PlasmaQuick::Dialog
            enabledBorders: win.floatingPanel ? KSvg.FrameSvgItem.AllBorders
                : ({ bottom: KSvg.FrameSvgItem.AllBorders & ~KSvg.FrameSvgItem.BottomBorder,
                     top: KSvg.FrameSvgItem.AllBorders & ~KSvg.FrameSvgItem.TopBorder,
                     left: KSvg.FrameSvgItem.AllBorders & ~KSvg.FrameSvgItem.LeftBorder,
                     right: KSvg.FrameSvgItem.AllBorders & ~KSvg.FrameSvgItem.RightBorder })[win.edge]
                  ?? KSvg.FrameSvgItem.AllBorders

            // CompactApplet.qml (plasma-desktop 6.7.5): a popup docked to the panel draws a 1 px
            // «widgets/line» against it and grows by that pixel (appletParent.extraWidth/extraHeight)
            readonly property bool horizontalPanel: win.edge === "top" || win.edge === "bottom"
            readonly property int lineX: !win.floatingPanel && !horizontalPanel ? 1 : 0
            readonly property int lineY: !win.floatingPanel && horizontalPanel ? 1 : 0
            width: Math.min(win.areaWidth, kickoff.implicitWidth + margins.left + margins.right + lineX)
            height: Math.min(win.areaHeight - win.distance, kickoff.implicitHeight + margins.top + margins.bottom + lineY)

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
                x: frame.margins.left + (win.edge === "left" ? frame.lineX : 0)
                y: frame.margins.top + (win.edge === "top" ? frame.lineY : 0)
                width: frame.width - frame.margins.left - frame.margins.right - frame.lineX
                height: frame.height - frame.margins.top - frame.margins.bottom - frame.lineY
                focus: root.opened
            }

            // Línea entre el menú y el panel, encima del contenido como en Plasma (z 999)
            KSvg.SvgItem {
                visible: frame.lineX + frame.lineY > 0
                z: 999
                imagePath: "widgets/line"
                elementId: frame.horizontalPanel ? "horizontal-line" : "vertical-line"
                x: win.edge === "right" ? frame.width - 1 : 0
                y: win.edge === "bottom" ? frame.height - 1 : 0
                width: frame.horizontalPanel ? frame.width : 1
                height: frame.horizontalPanel ? 1 : frame.height
            }
        }

        onVisibleChanged: if (visible) Qt.callLater(() => kickoff.forceActiveFocus())
    }
}
