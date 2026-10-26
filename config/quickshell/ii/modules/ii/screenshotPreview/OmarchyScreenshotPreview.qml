pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import Quickshell.Wayland
import qs.modules.common
import qs.Commons as O

// Retro skin: the floating preview Omarchy's screenshot tool (omasnap) shows after a
// capture: the shot is already copied (and saved under ~/Pictures/Screenshots), a small card
// in the corner shows it and fades after 10 seconds unless it is pinned or hovered.
// Square, accent border and monospace text from Omarchy's own shell tokens (qs.Commons).
// Region capture itself is BWM's selector (modules/ii/regionSelector), which calls
//   qs -c ii ipc call omarchyScreenshot show <file>
Scope {
    id: root

    property string path: ""
    property bool shown: false
    property bool pinned: false
    property int stamp: 0   // cache-busts the image when a new shot has the same name

    function show(file) {
        root.path = file;
        root.stamp++;
        root.pinned = false;
        root.shown = true;
        hideTimer.restart();
    }
    function hide() {
        root.shown = false;
        root.pinned = false;
    }

    Timer {
        id: hideTimer
        interval: 10000
        onTriggered: {
            if (!root.pinned && !(cardLoader.item?.hovered ?? false))
                root.hide();
            else if (!root.pinned)
                restart();
        }
    }

    IpcHandler {
        target: "omarchyScreenshot"
        function show(file: string): void {
            root.show(file);
        }
        function hide(): void {
            root.hide();
        }
    }

    LazyLoader {
        id: cardLoader
        active: root.shown

        PanelWindow {
            id: win
            readonly property bool hovered: hover.hovered
            screen: Quickshell.screens.find(s => s.name === Hyprland.focusedMonitor?.name) ?? Quickshell.screens[0]
            anchors { bottom: true; right: true }
            margins { bottom: O.Style.gapsOut * 2 + 10; right: O.Style.gapsOut * 2 + 10 }
            exclusiveZone: 0
            WlrLayershell.layer: WlrLayer.Overlay
            WlrLayershell.namespace: "quickshell:omarchyScreenshot"
            color: "transparent"
            implicitWidth: 340
            implicitHeight: card.implicitHeight

            Rectangle {
                id: card
                anchors.fill: parent
                implicitHeight: column.implicitHeight + 24
                color: O.Color.popups.background
                border.width: 2
                border.color: root.pinned ? O.Color.accent : O.Color.popups.border
                radius: 0

                HoverHandler { id: hover }

                ColumnLayout {
                    id: column
                    anchors { fill: parent; margins: 12 }
                    spacing: 8

                    Image {
                        Layout.fillWidth: true
                        Layout.preferredHeight: Math.min(200, width * (sourceSize.height / Math.max(1, sourceSize.width)))
                        source: root.path !== "" ? `file://${root.path}?${root.stamp}` : ""
                        fillMode: Image.PreserveAspectFit
                        asynchronous: true
                        cache: false

                        MouseArea { // Open the shot, like clicking omasnap's preview
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Quickshell.execDetached(["xdg-open", root.path])
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: "> Copied · " + root.path.replace(Quickshell.env("HOME"), "~")
                        elide: Text.ElideMiddle
                        color: O.Color.popups.text
                        font.family: O.Style.font.family
                        font.pixelSize: 12
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Repeater {
                            model: [
                                { label: "edit", run: () => Quickshell.execDetached(["sh", "-c", `${Config.options.regionSelector.annotation.useSatty ? "satty" : "swappy"} -f "$1"`, "sh", root.path]) },
                                { label: "folder", run: () => Quickshell.execDetached(["xdg-open", root.path.substring(0, root.path.lastIndexOf("/"))]) },
                                { label: root.pinned ? "unpin" : "pin", run: () => { root.pinned = !root.pinned; if (!root.pinned) hideTimer.restart(); } },
                                { label: "close", run: () => root.hide() }
                            ]
                            delegate: Rectangle {
                                id: btn
                                required property var modelData
                                Layout.fillWidth: true
                                implicitHeight: 24
                                radius: 0
                                color: btnMouse.containsMouse ? Qt.rgba(O.Color.accent.r, O.Color.accent.g, O.Color.accent.b, 0.18) : "transparent"
                                border.width: 1
                                border.color: btnMouse.containsMouse ? O.Color.accent : Qt.rgba(O.Color.foreground.r, O.Color.foreground.g, O.Color.foreground.b, 0.4)
                                Text {
                                    anchors.centerIn: parent
                                    text: btn.modelData.label
                                    color: btnMouse.containsMouse ? O.Color.accent : O.Color.popups.text
                                    font.family: O.Style.font.family
                                    font.pixelSize: 12
                                }
                                MouseArea {
                                    id: btnMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: btn.modelData.run()
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
