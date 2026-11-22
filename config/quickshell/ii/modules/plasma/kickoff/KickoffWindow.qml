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
import qs.modules.plasma.menus as PlasmaMenusMod
import qs.modules.plasma.panel
import qs.modules.plasma.theme
import qs.modules.plasma.tray as PlasmaTray

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
    onOpenedChanged: {
        if (opened) {
            PlasmaMenusMod.PlasmaMenus.close();
            PlasmaTray.TrayState.close();
        }
    }

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
        // When pinned (hideOnWindowDeactivate === false), never steal clicks or exclusive keyboard
        // focus outside the Kickoff frame.
        WlrLayershell.keyboardFocus: !root.opened ? WlrKeyboardFocus.None
            : (kickoff.hideOnWindowDeactivate ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.OnDemand)
        mask: Region { item: kickoff.hideOnWindowDeactivate ? backdrop : frame }
        anchors { top: true; bottom: true; left: true; right: true }

        // Pulsar fuera: como hideOnWindowDeactivate de un plasmoide (no se cierra si está fijado)
        MouseArea {
            id: backdrop
            anchors.fill: parent
            acceptedButtons: Qt.AllButtons
            onPressed: if (kickoff.hideOnWindowDeactivate) root.close()
        }

        // KWin's blur behind the dialog (ext_background_effect); the layer rule keeps its shape
        BackgroundEffect.blurRegion: Region { item: PlasmaTheme.blur && root.opened ? frame : null }
        BlurPath { id: dialogPath; path: "dialogs/background"; withoutBlur: "solid/dialogs/background" }

        KSvg.FrameSvgItem {
            id: frame
            // Plasma usa la variante translúcida sólo con el efecto de desenfoque de KWin; sin él,
            // como Plasma sin desenfoque, la sólida
            imagePath: dialogPath.resolved
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

            // R7: KWin slidingpopups slide-in (200 ms OutCubic from panel edge) without altering frame x/y/width/height
            property real slideProgress: 1
            transform: Translate {
                x: (1 - frame.slideProgress) * (win.edge === "left" ? -Kirigami.Units.gridUnit : win.edge === "right" ? Kirigami.Units.gridUnit : 0)
                y: (1 - frame.slideProgress) * (win.edge === "top" ? -Kirigami.Units.gridUnit : win.edge === "bottom" ? Kirigami.Units.gridUnit : 0)
            }
            NumberAnimation {
                id: kickoffSlideIn
                target: frame
                property: "slideProgress"
                from: 0; to: 1
                duration: Kirigami.Units.longDuration
                easing.type: Easing.OutCubic
            }
            Connections {
                target: root
                function onOpenedChanged() {
                    if (root.opened && PlasmaTheme.slidingPopups && Kirigami.Units.longDuration > 0) {
                        frame.slideProgress = 0;
                        kickoffSlideIn.restart();
                    } else {
                        kickoffSlideIn.stop();
                        frame.slideProgress = 1;
                    }
                }
            }

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

        // BWM: como en Plasma, Kickoff se abre con el cursor ya en el buscador: lo que se teclee justo
        // después de Super/Alt+F1 busca aplicaciones. Kickoff es un Item simple (no un FocusScope), así
        // que enfocarlo a él dejaba el teclado fuera del campo; se enfoca el campo, y si aún no existe
        // (la vista se construye al hacerse visible la capa) se reintenta unos instantes.
        function focusSearch() {
            const field = kickoff.searchField;
            if (field) {
                field.forceActiveFocus(Qt.ShortcutFocusReason);
                return true;
            }
            kickoff.forceActiveFocus();
            return false;
        }
        onVisibleChanged: if (visible) {
            focusRetries.remaining = 20;
            Qt.callLater(() => { if (win.focusSearch()) focusRetries.remaining = 0; else focusRetries.restart(); });
        }
        Timer {
            id: focusRetries
            property int remaining: 0
            interval: 25
            repeat: true
            running: false
            onTriggered: {
                if (!root.opened || remaining <= 0 || win.focusSearch()) {
                    stop();
                    return;
                }
                remaining--;
            }
        }
    }
}
