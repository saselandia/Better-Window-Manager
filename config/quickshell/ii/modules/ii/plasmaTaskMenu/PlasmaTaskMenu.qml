import qs
import qs.services
import qs.modules.common
import qs.modules.ii.plasmaCommon
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Widgets
import Quickshell.Wayland

/**
 * KDE Plasma task manager popups for the Plasma taskbar (Breeze Dark):
 *  - Right-click context menu: app actions, new window, pin/unpin, close
 *  - Hover window list when an app has 2+ windows; hovering a thumbnail "peeks"
 *    the window (live copy drawn on top without touching the real stacking order,
 *    so nothing has to be restored afterwards); clicking one activates it
 */
Scope {
    id: root

    readonly property real barHeight: Appearance.sizes.baseBarHeight
    readonly property real edgeGap: Appearance.sizes.plasmaFloatingGap
    readonly property string minimizeScript: "/home/sasel/.config/hypr/scripts/toggle-minimize.py"

    function entryFor(appId) {
        return TaskbarApps.apps.find(a => a.appId === appId) ?? null;
    }
    function addressOf(toplevel) {
        return toplevel?.HyprlandToplevel?.address ?? "";
    }
    function isMinimized(toplevel) {
        return (HyprlandData.windowByAddress["0x" + addressOf(toplevel)]?.workspace?.id ?? 0) === 99;
    }
    function activateWindow(toplevel) {
        if (!toplevel) return;
        if (root.isMinimized(toplevel))
            Quickshell.execDetached([root.minimizeScript, "restore", "0x" + root.addressOf(toplevel)]);
        toplevel.activate();
    }
    function closeMenu() { GlobalStates.plasmaTaskMenuOpen = false; }

    IpcHandler {
        target: "plasmaTaskMenu"
        function close(): void { root.closeMenu(); }
    }

    // Close the menu and hover list when the app disappears
    Connections {
        target: GlobalStates
        function onPlasmaTaskMenuOpenChanged() {
            if (GlobalStates.plasmaTaskMenuOpen) {
                GlobalStates.plasmaTaskHoverApp = "";
                GlobalStates.plasmaTaskPeek = "";
            }
        }
    }

    // =================================================================
    // Right-click context menu
    // =================================================================
    BreezePopupWindow {
        id: menuWin
        readonly property var entry: root.entryFor(GlobalStates.plasmaTaskMenuApp)
        readonly property var desktopEntry: DesktopEntries.heuristicLookup(GlobalStates.plasmaTaskMenuApp)
        readonly property var toplevels: entry?.toplevels ?? []
        readonly property bool pinned: TaskbarApps.isPinned(GlobalStates.plasmaTaskMenuApp)
        readonly property var actions: desktopEntry?.actions ?? []
        readonly property int rowCount: (toplevels.length > 0 ? 1 : 0) + actions.length + 1 + (toplevels.length > 0 ? 1 : 0)

        passBarClicks: true   // right-clicking another taskbar button switches the menu
        bottomMargin: 0
        opened: GlobalStates.plasmaTaskMenuOpen
        anchorX: GlobalStates.plasmaTaskMenuAnchorX
        screenName: GlobalStates.plasmaTaskMenuScreen
        namespace: "quickshell:plasmaTaskMenu"
        popupWidth: 250
        popupHeight: 8 + rowCount * 30 + (actions.length > 0 || toplevels.length > 0 ? 9 : 0) + (desktopEntry ? 30 : 0)
        onCloseRequested: root.closeMenu()

        component MenuItem: Rectangle {
            id: item
            property string text
            property string iconName      // bundled Breeze menu icon
            property string iconSource    // or an explicit image source (desktop action icons)
            property bool danger: false
            signal triggered()
            Layout.fillWidth: true
            Layout.preferredHeight: 30
            Layout.leftMargin: 4
            Layout.rightMargin: 4
            radius: 3
            color: area.containsMouse ? Breeze.accentSubtle : "transparent"
            border.width: area.containsMouse ? 1 : 0
            border.color: Breeze.accentBorder

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8
                anchors.rightMargin: 8
                spacing: 8
                Item {
                    Layout.preferredWidth: 16
                    Layout.preferredHeight: 16
                    Image {
                        anchors.fill: parent
                        sourceSize: Qt.size(32, 32)
                        visible: item.iconName !== ""
                        source: item.iconName !== "" ? Breeze.icon("menu", item.iconName) : ""
                    }
                    IconImage {
                        anchors.fill: parent
                        visible: item.iconName === "" && item.iconSource !== ""
                        source: item.iconSource
                    }
                }
                Text {
                    Layout.fillWidth: true
                    text: item.text
                    elide: Text.ElideRight
                    color: item.danger && area.containsMouse ? Breeze.negative : Breeze.text
                    font.family: Breeze.fontFamily
                    font.pixelSize: 13
                }
            }
            MouseArea {
                id: area
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: { item.triggered(); root.closeMenu(); }
            }
        }

        component MenuSeparator: Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            Layout.topMargin: 4
            Layout.bottomMargin: 4
            color: Breeze.border
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.topMargin: 4
            anchors.bottomMargin: 4
            spacing: 0

            // New window (first Exec of the desktop entry)
            MenuItem {
                visible: menuWin.desktopEntry !== null
                text: "Abrir nueva ventana"
                iconName: "window-new"
                onTriggered: menuWin.desktopEntry?.execute()
            }

            // Desktop actions: "New private window", "New tab"…
            Repeater {
                model: menuWin.actions
                delegate: MenuItem {
                    required property var modelData
                    text: modelData.name
                    iconSource: modelData.icon ? Quickshell.iconPath(modelData.icon, true) : ""
                    onTriggered: modelData.execute()
                }
            }

            MenuSeparator { visible: menuWin.desktopEntry !== null }

            MenuItem {
                text: menuWin.pinned ? "Desanclar de la barra de tareas" : "Anclar a la barra de tareas"
                iconName: menuWin.pinned ? "unpin" : "pin"
                onTriggered: TaskbarApps.togglePin(GlobalStates.plasmaTaskMenuApp)
            }

            MenuSeparator { visible: menuWin.toplevels.length > 0 }

            MenuItem {
                visible: menuWin.toplevels.length > 0
                text: menuWin.toplevels.length > 1 ? "Cerrar todas (" + menuWin.toplevels.length + ")" : "Cerrar"
                iconName: "window-close"
                danger: true
                onTriggered: {
                    for (const t of menuWin.toplevels) t.close();
                }
            }
            Item { Layout.fillHeight: true }
        }
    }

    // =================================================================
    // Hover window list (apps with 2+ windows)
    // =================================================================
    PanelWindow {
        id: listWin
        // Last hovered app: GlobalStates.plasmaTaskHoverApp is cleared as soon as the pointer
        // leaves the taskbar button, but the list must stay while the pointer reaches it
        property string app: ""
        Connections {
            target: GlobalStates
            function onPlasmaTaskHoverAppChanged() {
                if (GlobalStates.plasmaTaskHoverApp !== "") listWin.app = GlobalStates.plasmaTaskHoverApp;
            }
        }
        readonly property var entry: root.entryFor(app)
        readonly property var toplevels: entry?.toplevels ?? []
        readonly property bool want: GlobalStates.plasmaTaskHoverApp !== "" && toplevels.length > 1
            && !GlobalStates.plasmaTaskMenuOpen || listHover.hovered
        property bool opened: false
        property real anchorX: GlobalStates.plasmaTaskHoverX

        onWantChanged: {
            if (want) { closeTimer.stop(); if (!opened) openTimer.restart(); }
            else { openTimer.stop(); closeTimer.restart(); }
        }
        Timer { id: openTimer; interval: 300; onTriggered: listWin.opened = true }
        Timer {
            id: closeTimer
            interval: 450
            onTriggered: { listWin.opened = false; GlobalStates.plasmaTaskPeek = ""; }
        }

        visible: opened && toplevels.length > 1
        screen: Quickshell.screens.find(s => s.name === GlobalStates.plasmaTaskHoverScreen) ?? Quickshell.screens[0]
        color: "transparent"
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "quickshell:plasmaTaskList"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
        anchors { bottom: true; left: true }
        // The window reaches down to the bar (transparent strip below the card), so the
        // pointer never leaves it while moving from the taskbar button up to a thumbnail
        margins.bottom: root.barHeight
        margins.left: Math.max(root.edgeGap, Math.min((screen?.width ?? 1920) - implicitWidth - root.edgeGap,
            anchorX - implicitWidth / 2))
        implicitWidth: listCard.width
        implicitHeight: listCard.height + root.edgeGap + 4

        HoverHandler { id: listHover }

        Rectangle {
            id: listCard
            width: cards.implicitWidth + 16
            height: cards.implicitHeight + 16
            color: Breeze.panelBg
            border.width: 1
            border.color: Breeze.border
            topLeftRadius: 7
            topRightRadius: 7
            bottomLeftRadius: root.edgeGap > 0 ? 7 : 0
            bottomRightRadius: root.edgeGap > 0 ? 7 : 0

            RowLayout {
                id: cards
                anchors.centerIn: parent
                spacing: 8

                Repeater {
                    model: listWin.toplevels
                    delegate: Rectangle {
                        id: card
                        required property var modelData
                        readonly property string address: root.addressOf(modelData)
                        readonly property bool hovered: cardArea.containsMouse || closeArea.containsMouse
                        Layout.preferredWidth: 200
                        Layout.preferredHeight: 150
                        radius: 4
                        color: hovered ? Breeze.accentSubtle : "transparent"
                        border.width: modelData.activated ? 1 : (hovered ? 1 : 0)
                        border.color: hovered ? Breeze.accentBorder : Breeze.border

                        onHoveredChanged: {
                            if (hovered && !root.isMinimized(modelData)) GlobalStates.plasmaTaskPeek = address;
                            else if (!hovered && GlobalStates.plasmaTaskPeek === address) GlobalStates.plasmaTaskPeek = "";
                        }

                        MouseArea {
                            id: cardArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                            onClicked: mouse => {
                                if (mouse.button === Qt.MiddleButton) { card.modelData.close(); return; }
                                GlobalStates.plasmaTaskPeek = "";
                                root.activateWindow(card.modelData);
                                listWin.opened = false;
                            }
                        }

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 6
                            spacing: 6

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 6
                                IconImage {
                                    implicitSize: 16
                                    source: Quickshell.iconPath(AppSearch.guessIcon(card.modelData.appId), "application-x-executable")
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: card.modelData.title
                                    elide: Text.ElideRight
                                    color: Breeze.text
                                    font.family: Breeze.fontFamily
                                    font.pixelSize: 12
                                }
                                Rectangle {
                                    Layout.preferredWidth: 20
                                    Layout.preferredHeight: 20
                                    radius: 3
                                    color: closeArea.containsMouse ? Breeze.negative : "transparent"
                                    Text {
                                        anchors.centerIn: parent
                                        text: "✕"
                                        color: Breeze.text
                                        font.pixelSize: 11
                                    }
                                    MouseArea {
                                        id: closeArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: card.modelData.close()
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                color: "#1c2024"
                                clip: true
                                ScreencopyView {
                                    anchors.centerIn: parent
                                    captureSource: listWin.visible ? card.modelData : null
                                    live: true
                                    constraintSize: Qt.size(parent.width, parent.height)
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // =================================================================
    // Window peek: live copy of the hovered window on top of everything,
    // click-through; real stacking is never modified
    // =================================================================
    PanelWindow {
        id: peekWin
        readonly property var toplevel: GlobalStates.plasmaTaskPeek === "" ? null
            : (ToplevelManager.toplevels.values.find(t => root.addressOf(t) === GlobalStates.plasmaTaskPeek) ?? null)
        readonly property var win: toplevel ? HyprlandData.windowByAddress["0x" + GlobalStates.plasmaTaskPeek] : null
        readonly property var mon: win ? HyprlandData.monitors.find(m => m.id === win.monitor) : null

        visible: toplevel !== null && win !== null && mon !== null
        screen: Quickshell.screens.find(s => s.name === mon?.name) ?? Quickshell.screens[0]
        color: "transparent"
        exclusionMode: ExclusionMode.Ignore
        mask: Region {}   // empty input region: never steals the mouse
        WlrLayershell.namespace: "quickshell:plasmaTaskPeek"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
        anchors { top: true; bottom: true; left: true; right: true }
        margins.bottom: root.barHeight + root.edgeGap

        // Dim everything else, like Plasma's "Peek at window"
        Rectangle {
            anchors.fill: parent
            color: "#66000000"
        }

        ScreencopyView {
            id: peekView
            x: (peekWin.win?.at?.[0] ?? 0) - (peekWin.mon?.x ?? 0)
            y: (peekWin.win?.at?.[1] ?? 0) - (peekWin.mon?.y ?? 0)
            width: peekWin.win?.size?.[0] ?? 0
            height: peekWin.win?.size?.[1] ?? 0
            captureSource: peekWin.visible ? peekWin.toplevel : null
            live: true

            Rectangle {
                anchors.fill: parent
                color: "transparent"
                border.width: 1
                border.color: Breeze.accent
                radius: 8
            }
        }
    }
}
