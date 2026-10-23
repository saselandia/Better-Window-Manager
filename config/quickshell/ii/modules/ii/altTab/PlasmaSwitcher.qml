import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Widgets
import Quickshell.Wayland

import qs.services
import qs.modules.common
import qs.modules.ii.plasmaCommon

/**
 * KDE Plasma 6 task switcher ("Breeze" thumbnail grid) recreated in Breeze Dark:
 *  - centered translucent panel with a grid of live window thumbnails, app icon over
 *    each thumbnail and the window title underneath
 *  - the selected window is also shown highlighted on the desktop with the rest dimmed
 *    (KWin's "Highlight Windows" effect)
 *  - mouse hover selects, click activates, middle click closes; arrows/Enter/Esc while open
 * Driven by AltTab.qml (root): windowList, selectedIndex, isOpen.
 */
PanelWindow {
    id: win
    required property var controller
    readonly property var root: controller

    // Grid geometry
    readonly property int cellW: 236
    readonly property int cellH: 196
    readonly property int pad: 16
    readonly property int spacing: 8
    readonly property int count: root.windowList.length
    readonly property int maxCols: Math.max(1, Math.floor((width * 0.9 - pad * 2 + spacing) / (cellW + spacing)))
    readonly property int columns: Math.max(1, Math.min(count, maxCols))
    readonly property int rows: Math.ceil(count / columns)
    property int gridColumns: columns   // read by the key handling

    // Selected window geometry for the highlight effect (same monitor only)
    readonly property var selected: root.windowList[root.selectedIndex] ?? null
    readonly property var selectedData: selected ? HyprlandData.windowByAddress[selected.address] : null
    readonly property var screenMon: HyprlandData.monitors.find(m => m.name === win.screen?.name)
    readonly property bool canHighlight: root.isOpen && selectedData !== null && screenMon !== undefined
        && selectedData.monitor === screenMon.id && (selectedData.workspace?.id ?? 0) > 0

    visible: root.isOpen
    screen: root.focusedScreen
    color: "transparent"
    exclusionMode: ExclusionMode.Ignore
    exclusiveZone: 0
    WlrLayershell.namespace: "quickshell:altTab"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: root.isOpen ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    anchors { top: true; bottom: true; left: true; right: true }

    // Dim the desktop; the selected window is redrawn on top of it
    Rectangle {
        anchors.fill: parent
        color: "#8c000000"
        opacity: root.isOpen ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 120 } }
        MouseArea { anchors.fill: parent; onClicked: root.cancel() }
    }

    ScreencopyView {
        visible: win.canHighlight
        x: (win.selectedData?.at?.[0] ?? 0) - (win.screenMon?.x ?? 0)
        y: (win.selectedData?.at?.[1] ?? 0) - (win.screenMon?.y ?? 0)
        width: win.selectedData?.size?.[0] ?? 0
        height: win.selectedData?.size?.[1] ?? 0
        captureSource: win.canHighlight ? win.selected?.toplevel ?? null : null
        live: true
    }

    Item {
        anchors.fill: parent
        focus: root.isOpen
        Keys.onPressed: event => {
            const n = win.count, i = root.selectedIndex, c = win.gridColumns;
            if (n === 0) return;
            switch (event.key) {
            case Qt.Key_Right: root.selectedIndex = (i + 1) % n; break;
            case Qt.Key_Left: root.selectedIndex = (i - 1 + n) % n; break;
            case Qt.Key_Down: root.selectedIndex = (i + c < n) ? i + c : i % c; break;
            case Qt.Key_Up: root.selectedIndex = (i - c >= 0) ? i - c : Math.min(n - 1, i + Math.floor((n - 1 - i) / c) * c); break;
            case Qt.Key_Home: root.selectedIndex = 0; break;
            case Qt.Key_End: root.selectedIndex = n - 1; break;
            case Qt.Key_Return: case Qt.Key_Enter: case Qt.Key_Space: root.selectAndClose(); break;
            case Qt.Key_Escape: root.cancel(); break;
            default: return;
            }
            event.accepted = true;
        }
    }

    Rectangle {
        id: panel
        anchors.centerIn: parent
        width: win.columns * (win.cellW + win.spacing) - win.spacing + win.pad * 2
        height: Math.min(win.height * 0.85, win.rows * (win.cellH + win.spacing) - win.spacing + win.pad * 2)
        radius: 8
        color: Breeze.panelBg
        border.width: 1
        border.color: Breeze.border
        opacity: root.isOpen ? 1 : 0
        scale: root.isOpen ? 1 : 0.96
        Behavior on opacity { NumberAnimation { duration: 120 } }
        Behavior on scale { NumberAnimation { duration: 130; easing.type: Easing.OutCubic } }

        MouseArea { anchors.fill: parent }

        Flickable {
            id: flick
            anchors.fill: parent
            anchors.margins: win.pad
            contentWidth: grid.width
            contentHeight: grid.height
            clip: true
            boundsBehavior: Flickable.StopAtBounds

            // keep the selected row visible
            Connections {
                target: root
                function onSelectedIndexChanged() {
                    const row = Math.floor(root.selectedIndex / win.columns);
                    const top = row * (win.cellH + win.spacing);
                    if (top < flick.contentY) flick.contentY = top;
                    else if (top + win.cellH > flick.contentY + flick.height) flick.contentY = top + win.cellH - flick.height;
                }
            }

            Grid {
                id: grid
                columns: win.columns
                spacing: win.spacing

                Repeater {
                    model: root.windowList
                    delegate: Rectangle {
                        id: tile
                        required property var modelData
                        required property int index
                        readonly property bool isSelected: index === root.selectedIndex
                        readonly property bool minimized: (modelData.workspace?.id ?? 0) === 99
                        width: win.cellW
                        height: win.cellH
                        radius: 5
                        color: isSelected ? Breeze.accentSubtle : (tileArea.containsMouse ? Breeze.hover : "transparent")
                        border.width: isSelected ? 1 : 0
                        border.color: Breeze.accentBorder

                        MouseArea {
                            id: tileArea
                            anchors.fill: parent
                            hoverEnabled: true
                            acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                            cursorShape: Qt.PointingHandCursor
                            onEntered: root.selectedIndex = tile.index
                            onClicked: mouse => {
                                if (mouse.button === Qt.MiddleButton) tile.modelData.toplevel?.close();
                                else root.selectWindow(tile.index);
                            }
                        }

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 6

                            Rectangle { // thumbnail
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                radius: 3
                                color: "#1c2024"
                                clip: true
                                opacity: tile.minimized ? 0.55 : 1

                                IconImage {
                                    anchors.centerIn: parent
                                    implicitSize: 48
                                    source: Quickshell.iconPath(AppSearch.guessIcon(tile.modelData.class), "application-x-executable")
                                    visible: !tile.modelData.toplevel
                                }
                                ScreencopyView {
                                    anchors.centerIn: parent
                                    captureSource: (root.isOpen && tile.modelData.toplevel) ? tile.modelData.toplevel : null
                                    live: true
                                    constraintSize: Qt.size(parent.width, parent.height)
                                }
                                // App icon over the thumbnail, bottom center (Breeze switcher)
                                IconImage {
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    anchors.bottom: parent.bottom
                                    anchors.bottomMargin: 6
                                    implicitSize: 32
                                    source: Quickshell.iconPath(AppSearch.guessIcon(tile.modelData.class), "application-x-executable")
                                }
                                // Hover close button
                                Rectangle {
                                    visible: tileArea.containsMouse
                                    anchors { top: parent.top; right: parent.right; margins: 4 }
                                    width: 20; height: 20; radius: 3
                                    color: closeArea.containsMouse ? Breeze.negative : "#cc232629"
                                    Text { anchors.centerIn: parent; text: "✕"; color: Breeze.text; font.pixelSize: 11 }
                                    MouseArea {
                                        id: closeArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: tile.modelData.toplevel?.close()
                                    }
                                }
                            }

                            Text {
                                Layout.fillWidth: true
                                horizontalAlignment: Text.AlignHCenter
                                text: tile.modelData.title || tile.modelData.class
                                elide: Text.ElideRight
                                maximumLineCount: 1
                                color: tile.isSelected ? Breeze.text : Breeze.textMuted
                                font.family: Breeze.fontFamily
                                font.pixelSize: 12
                            }
                        }
                    }
                }
            }
        }
    }
}
