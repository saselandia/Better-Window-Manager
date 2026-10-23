import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland

import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.common.functions

Scope {
    id: root

    property bool isOpen: false
    property var windowList: []
    property int selectedIndex: 0
    property var focusedScreen: Quickshell.screens.find(s => s.name === Hyprland.focusedMonitor?.name) ?? Quickshell.screens[0]

    Connections {
        target: Hyprland
        function onFocusedMonitorChanged() {
            root.focusedScreen = Quickshell.screens.find(s => s.name === Hyprland.focusedMonitor?.name) ?? Quickshell.screens[0];
        }
    }

    // Monitor a nivel de hardware que detecta en milisegundos cuando se suelta Alt
    Process {
        id: altMonitor
        command: ["/home/sasel/.config/hypr/scripts/alt-release-monitor.py"]
        onExited: (exitCode, exitStatus) => {
            console.log("[AltTab] altMonitor detected Alt release, isOpen:", root.isOpen);
            root.selectAndClose();
        }
    }

    function findToplevel(address, title, appClass) {
        var toplevels = ToplevelManager.toplevels.values || [];
        var cleanAddr = address ? address.toLowerCase().replace(/^0x/, "") : "";

        // 1. Coincidencia por dirección de Hyprland
        if (cleanAddr.length > 0) {
            for (var i = 0; i < toplevels.length; i++) {
                var top = toplevels[i];
                if (!top) continue;
                var topAddr = (top.HyprlandToplevel?.address || "").toLowerCase().replace(/^0x/, "");
                if (topAddr === cleanAddr) return top;
            }
        }

        // 2. Coincidencia por título exacto
        if (title && title.length > 0) {
            for (var j = 0; j < toplevels.length; j++) {
                var top2 = toplevels[j];
                if (top2 && top2.title === title) return top2;
            }
        }

        // 3. Coincidencia por appId / clase
        if (appClass && appClass.length > 0) {
            var lowerClass = appClass.toLowerCase();
            for (var k = 0; k < toplevels.length; k++) {
                var top3 = toplevels[k];
                if (top3 && top3.appId && top3.appId.toLowerCase() === lowerClass) return top3;
            }
        }

        return null;
    }

    property string appFilter: ""   // non-empty: only windows of this class (Alt+` mode)
    property bool appFilterFromActive: false // Alt+`: take the class of the focused window

    // The switcher opens from a fresh `hyprctl clients/monitors` snapshot. HyprlandData drops
    // refreshes that arrive while one is running, so its focus history (the MRU order) was
    // often stale: a single Alt+Tab then selected the wrong window or the current one.
    property bool opening: false
    property int pendingSteps: 0      // Tab / Shift+Tab presses received while opening
    property bool releasedEarly: false // Alt released before the snapshot arrived (quick tap)

    function getVisibleWindows(clients, monitors) {
        const activeWorkspaceIds = (monitors || []).map(m => m.activeWorkspace?.id);
        if (root.appFilterFromActive) {
            root.appFilter = (clients || []).find(w => w.focusHistoryID === 0)?.class ?? "";
            root.appFilterFromActive = false;
        }
        var visible = [];
        for (var i = 0; i < clients.length; i++) {
            var c = clients[i];
            if (!c || !c.class || c.class.length === 0) continue;
            if (c.mapped === false || c.hidden === true) continue;
            if (!c.workspace || c.workspace.id <= 0) continue;
            // KDE Plasma: like KWin's default, only windows of the visible workspaces
            // (plus minimized ones, which live on workspace 99) and, for Alt+`, one app
            if (Appearance.isPlasma && c.workspace.id !== 99 && !activeWorkspaceIds.includes(c.workspace.id)) continue;
            if (appFilter !== "" && c.class !== appFilter) continue;
            visible.push({
                address: c.address,
                title: c.title || "",
                class: c.class || "",
                workspace: c.workspace,
                focusHistoryID: (c.focusHistoryID !== undefined) ? c.focusHistoryID : 999,
                toplevel: findToplevel(c.address, c.title, c.class)
            });
        }

        // Ordenar por focusHistoryID (orden MRU: 0 es actual, 1 es la anterior, etc.)
        visible.sort(function(a, b) {
            return a.focusHistoryID - b.focusHistoryID;
        });

        return visible;
    }

    // Focus is only changed on release (like KWin): the highlighted window is shown by the
    // switcher itself, so no focus changes (and frame flicker) while navigating
    property string origAddress: ""

    // Alt+` : cycle through the windows of the focused application only
    function nextApp(backwards) {
        if (!root.isOpen && !root.opening) {
            root.appFilterFromActive = true;
            root.next();
            if (backwards) { root.prev(); root.prev(); }
        } else if (backwards) root.prev(); else root.next();
    }

    function next() {
        console.log("[AltTab] next() called, current isOpen:", root.isOpen);
        if (root.opening) {
            root.pendingSteps++;
        } else if (!root.isOpen) {
            root.opening = true;
            root.pendingSteps = 0;
            root.releasedEarly = false;
            snapshot.running = true;
            altMonitor.running = false;
            altMonitor.running = true;
        } else {
            if (root.windowList.length > 0) {
                root.selectedIndex = (root.selectedIndex + 1) % root.windowList.length;
            }
            if (!altMonitor.running) {
                altMonitor.running = true;
            }
        }
    }

    function prev() {
        console.log("[AltTab] prev() called, current isOpen:", root.isOpen);
        if (root.opening) {
            root.pendingSteps--;
        } else if (root.isOpen && root.windowList.length > 0) {
            root.selectedIndex = (root.selectedIndex - 1 + root.windowList.length) % root.windowList.length;
            if (!altMonitor.running) {
                altMonitor.running = true;
            }
        }
    }

    // Focus + bring to the front of the stacking order (floating windows are not raised by focus alone)
    function focusAndRaise(address) {
        const w = "\"address:" + address + "\"";
        Hyprland.dispatch("hl.dsp.focus({window = " + w + "})");
        Hyprland.dispatch("hl.dsp.window.bring_to_top({window = " + w + "})");
        Hyprland.dispatch("hl.dsp.window.alter_zorder({mode = \"top\", window = " + w + "})");
    }

    function focusTarget(target) {
        if (!target || !target.address) return;
        const minimized = (target.workspace?.id ?? 0) === 99;
        // minimized window: restore it first
        if (minimized)
            Quickshell.execDetached(["/home/sasel/.config/hypr/scripts/toggle-minimize.py", "restore", target.address]);
        else
            root.focusAndRaise(target.address);
        // The switcher layer still holds the keyboard until it unmaps; focus again once it is gone
        pendingFocus = target.address;
        focusTimer.interval = minimized ? 160 : 70;
        focusTimer.restart();
    }
    property string pendingFocus: ""
    Timer {
        id: focusTimer
        interval: 160
        onTriggered: root.focusAndRaise(root.pendingFocus)
    }

    // Fresh window list + monitors, then the switcher opens
    Process {
        id: snapshot
        command: ["sh", "-c", "printf '['; hyprctl -j clients; printf ','; hyprctl -j monitors; printf ']'"]
        stdout: StdioCollector {
            onStreamFinished: {
                let clients = [], monitors = [];
                try {
                    [clients, monitors] = JSON.parse(text);
                } catch (e) {
                    clients = HyprlandData.windowList || [];
                    monitors = HyprlandData.monitors || [];
                }
                root.opening = false;
                const list = root.getVisibleWindows(clients, monitors);
                if (list.length === 0) {
                    altMonitor.running = false;
                    return;
                }
                root.windowList = list;
                // KDE order: current window first, selection starts on the previous one
                root.origAddress = list[0].address;
                const start = list.length > 1 ? 1 : 0;
                root.selectedIndex = ((start + root.pendingSteps) % list.length + list.length) % list.length;
                root.focusedScreen = Quickshell.screens.find(s => s.name === Hyprland.focusedMonitor?.name) ?? Quickshell.screens[0];
                root.isOpen = true;
                // Quick tap: Alt was already released, switch straight away
                if (root.releasedEarly)
                    root.selectAndClose();
            }
        }
    }

    function selectAndClose() {
        console.log("[AltTab] selectAndClose() called, isOpen:", root.isOpen, "selectedIndex:", root.selectedIndex);
        if (root.opening) {
            root.releasedEarly = true;
            return;
        }
        if (root.isOpen) {
            root.isOpen = false;
            altMonitor.running = false;
            if (root.windowList.length > 0 && root.selectedIndex >= 0 && root.selectedIndex < root.windowList.length) {
                var target = root.windowList[root.selectedIndex];
                if (target && target.address) {
                    root.focusTarget(target);
                }
            }
        }
    }

    function selectWindow(index) {
        console.log("[AltTab] selectWindow() clicked, index:", index);
        if (root.isOpen) {
            root.isOpen = false;
            altMonitor.running = false;
            if (index >= 0 && index < root.windowList.length) {
                var target = root.windowList[index];
                if (target && target.address) {
                    root.focusTarget(target);
                }
            }
        }
    }

    function cancel() {
        console.log("[AltTab] cancel() called");
        root.opening = false;
        if (root.isOpen) {
            root.isOpen = false;
            altMonitor.running = false;

        }
    }

    IpcHandler {
        target: "altTab"

        function next(): void {
            if (!root.isOpen && !root.opening) {
                root.appFilter = "";
                root.appFilterFromActive = false;
            }
            root.next();
        }

        function prev(): void {
            root.prev();
        }

        function nextApp(): void {
            root.nextApp(false);
        }

        function prevApp(): void {
            root.nextApp(true);
        }

        function release(): void {
            root.selectAndClose();
        }

        function cancel(): void {
            root.cancel();
        }

        function close(): void {
            root.cancel();
        }
    }

    PanelWindow {
        id: panelWindow
        visible: root.isOpen && !Appearance.isPlasma
        screen: root.focusedScreen

        WlrLayershell.namespace: "quickshell:altTab"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
        color: "transparent"
        exclusionMode: ExclusionMode.Ignore
        exclusiveZone: 0

        anchors {
            top: true
            bottom: true
            left: true
            right: true
        }

        // Fondo oscuro que captura clics exteriores para cancelar
        Rectangle {
            anchors.fill: parent
            color: ColorUtils.applyAlpha(Appearance.m3colors.m3scrim, 0.45)
            opacity: root.isOpen ? 1.0 : 0.0

            Behavior on opacity {
                NumberAnimation { duration: 140; easing.type: Easing.OutQuad }
            }

            MouseArea {
                anchors.fill: parent
                onClicked: root.cancel()
            }
        }

        // Ventana central HUD Material You
        Rectangle {
            id: hudCard
            anchors.centerIn: parent
            width: Math.min(panelWindow.width * 0.94, Math.max(listView.contentWidth + 56, 440))
            height: Math.min(panelWindow.height * 0.75, mainColumn.implicitHeight + 48)
            radius: 24
            color: ColorUtils.applyAlpha(Appearance.colors.colLayer0Base, 0.96)
            border.color: Appearance.colors.colLayer0Border
            border.width: 1.5

            scale: root.isOpen ? 1.0 : 0.94
            opacity: root.isOpen ? 1.0 : 0.0
            Behavior on scale {
                NumberAnimation { duration: 150; easing.type: Easing.OutCubic }
            }
            Behavior on opacity {
                NumberAnimation { duration: 150; easing.type: Easing.OutQuad }
            }

            MouseArea {
                anchors.fill: parent
                // Captura clics dentro de la tarjeta para no cerrar accidentalmente
            }

            ColumnLayout {
                id: mainColumn
                anchors.fill: parent
                anchors.margins: 20
                spacing: 16

                // Encabezado
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Text {
                        text: ""
                        font.family: Appearance.font.family.iconNerd
                        font.pixelSize: Appearance.font.pixelSize.large
                        color: Appearance.m3colors.m3primary
                    }

                    Text {
                        text: "Alternar ventanas"
                        font.family: Appearance.font.family.title
                        font.pixelSize: Appearance.font.pixelSize.large
                        font.weight: Font.Bold
                        color: Appearance.m3colors.m3onSurface
                    }

                    Item { Layout.fillWidth: true }

                    // Píldora de contador
                    Rectangle {
                        height: 24
                        width: countText.implicitWidth + 16
                        radius: 12
                        color: Appearance.colors.colPrimaryContainer

                        Text {
                            id: countText
                            anchors.centerIn: parent
                            text: (root.selectedIndex + 1) + " / " + root.windowList.length
                            font.family: Appearance.font.family.numbers
                            font.pixelSize: Appearance.font.pixelSize.smaller
                            font.weight: Font.Bold
                            color: Appearance.m3colors.m3onPrimaryContainer
                        }
                    }
                }

                // Lista horizontal con vistas previas en tiempo real (Screencopy)
                ListView {
                    id: listView
                    Layout.fillWidth: true
                    Layout.preferredHeight: 225
                    orientation: ListView.Horizontal
                    spacing: 16
                    clip: true
                    model: root.windowList
                    currentIndex: root.selectedIndex

                    onCurrentIndexChanged: {
                        positionViewAtIndex(currentIndex, ListView.Contain);
                    }

                    delegate: Rectangle {
                        id: card
                        required property var modelData
                        required property int index

                        readonly property bool isSelected: (index === root.selectedIndex)
                        width: 260
                        height: 225
                        radius: 18

                        color: isSelected 
                            ? Appearance.colors.colPrimaryContainer 
                            : (cardMouse.containsMouse ? Appearance.colors.colLayer1Hover : Appearance.colors.colLayer1Base)

                        border.color: isSelected 
                            ? Appearance.m3colors.m3primary 
                            : Appearance.colors.colLayer1
                        border.width: isSelected ? 2.5 : 1

                        scale: isSelected ? 1.03 : 1.0

                        Behavior on scale {
                            NumberAnimation { duration: 120; easing.type: Easing.OutQuad }
                        }
                        Behavior on color {
                            ColorAnimation { duration: 100 }
                        }
                        Behavior on border.color {
                            ColorAnimation { duration: 100 }
                        }

                        MouseArea {
                            id: cardMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onEntered: root.selectedIndex = index
                            onClicked: root.selectWindow(index)
                        }

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 8

                            // Cabecera de la tarjeta: Icono de app + Nombre de app + Workspace
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8

                                Image {
                                    width: 22
                                    height: 22
                                    sourceSize: Qt.size(22, 22)
                                    fillMode: Image.PreserveAspectFit
                                    source: Quickshell.iconPath(AppSearch.guessIcon(modelData.class), "image-missing")
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: {
                                        var cls = modelData.class || "";
                                        if (cls.length > 0) return cls.charAt(0).toUpperCase() + cls.slice(1);
                                        return "Ventana";
                                    }
                                    font.family: Appearance.font.family.title
                                    font.pixelSize: Appearance.font.pixelSize.smallie
                                    font.weight: Font.Bold
                                    elide: Text.ElideRight
                                    color: card.isSelected 
                                        ? Appearance.m3colors.m3onPrimaryContainer 
                                        : Appearance.m3colors.m3onSurface
                                }

                                Rectangle {
                                    height: 20
                                    width: wsText.implicitWidth + 10
                                    radius: 10
                                    color: card.isSelected 
                                        ? ColorUtils.mix(Appearance.m3colors.m3primary, Appearance.m3colors.m3primaryContainer, 0.4)
                                        : Appearance.colors.colSecondaryContainer

                                    Text {
                                        id: wsText
                                        anchors.centerIn: parent
                                        text: "󰍹 " + (modelData.workspace?.name || modelData.workspace?.id || "1")
                                        font.family: Appearance.font.family.main
                                        font.pixelSize: Appearance.font.pixelSize.smallest
                                        font.weight: Font.DemiBold
                                        color: card.isSelected 
                                            ? Appearance.m3colors.m3onPrimaryContainer 
                                            : Appearance.m3colors.m3onSecondaryContainer
                                    }
                                }
                            }

                            // Área de captura visual en tiempo real (Imagen / Screencopy)
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                radius: 12
                                clip: true
                                color: ColorUtils.applyAlpha(Appearance.colors.colLayer0Base, 0.6)
                                border.color: card.isSelected ? Appearance.m3colors.m3primary : Appearance.colors.colLayer0Border
                                border.width: 1

                                // Icono grande de respaldo centrado
                                Image {
                                    anchors.centerIn: parent
                                    width: 56
                                    height: 56
                                    sourceSize: Qt.size(56, 56)
                                    fillMode: Image.PreserveAspectFit
                                    source: Quickshell.iconPath(AppSearch.guessIcon(modelData.class), "image-missing")
                                    opacity: (screencopy.visible && modelData.toplevel) ? 0.35 : 0.90
                                }

                                ScreencopyView {
                                    id: screencopy
                                    anchors.centerIn: parent
                                    captureSource: (root.isOpen && modelData.toplevel) ? modelData.toplevel : null
                                    live: true
                                    paintCursor: false
                                    constraintSize: Qt.size(240, 125)
                                    visible: (modelData.toplevel != null)
                                }
                            }

                            // Título detallado de la pestaña / ventana
                            Text {
                                Layout.fillWidth: true
                                horizontalAlignment: Text.AlignHCenter
                                text: modelData.title || ""
                                font.family: Appearance.font.family.main
                                font.pixelSize: Appearance.font.pixelSize.smaller
                                elide: Text.ElideRight
                                maximumLineCount: 1
                                opacity: 0.90
                                color: card.isSelected 
                                    ? Appearance.m3colors.m3onPrimaryContainer 
                                    : Appearance.m3colors.m3onSurfaceVariant
                            }
                        }
                    }
                }

                // Pie con atajos
                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 2
                    spacing: 6

                    Item { Layout.fillWidth: true }

                    Text {
                        text: "󰌌  Mantén Alt + pulsa Tab para cambiar  •  Suelta Alt para enfocar"
                        font.family: Appearance.font.family.main
                        font.pixelSize: Appearance.font.pixelSize.smaller
                        color: Appearance.m3colors.m3outline
                    }

                    Item { Layout.fillWidth: true }
                }
            }
        }
    }

    PlasmaSwitcher {
        controller: root
    }
}
