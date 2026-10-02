import qs.services
import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.synchronizer
import Qt5Compat.GraphicalEffects
import Quickshell.Io
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland

Scope { // Scope
    id: root

    property bool isOpen: false
    property var targetScreen: Quickshell.screens.find(s => s.name === Hyprland.focusedMonitor?.name) ?? Quickshell.screens[0]

    function open(): void {
        root.targetScreen = Quickshell.screens.find(s => s.name === Hyprland.focusedMonitor?.name) ?? Quickshell.screens[0];
        root.isOpen = true;
    }

    function close(): void {
        root.isOpen = false;
    }

    function toggle(): void {
        if (root.isOpen) {
            root.close();
        } else {
            root.open();
        }
    }

    property var tabButtonList: [
        {
            "icon": "keyboard",
            "name": Translation.tr("Keybinds")
        },
        {
            "icon": "experiment",
            "name": Translation.tr("Elements")
        },
    ]

    PanelWindow { // Window
        id: cheatsheetRoot
        visible: root.isOpen
        screen: root.targetScreen

        anchors {
            top: true
            bottom: true
            left: true
            right: true
        }

        function hide() {
            root.close();
        }

        exclusiveZone: 0
        implicitWidth: cheatsheetBackground.width + Appearance.sizes.elevationMargin * 2
        implicitHeight: cheatsheetBackground.height + Appearance.sizes.elevationMargin * 2
        WlrLayershell.namespace: "quickshell:cheatsheet"
        WlrLayershell.keyboardFocus: root.isOpen ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None
        color: "transparent"

        mask: Region {
            item: cheatsheetBackground
        }

        onVisibleChanged: {
            if (visible) {
                GlobalFocusGrab.addDismissable(cheatsheetRoot);
                cheatsheetBackground.forceActiveFocus();
            } else {
                GlobalFocusGrab.removeDismissable(cheatsheetRoot);
            }
        }

        Connections {
            target: GlobalFocusGrab
            function onDismissed() {
                cheatsheetRoot.hide();
            }
        }

        // Background
        StyledRectangularShadow {
            target: cheatsheetBackground
        }
        Rectangle {
            id: cheatsheetBackground
            anchors.centerIn: parent
            focus: true
            color: Appearance.colors.colLayer0
            border.width: 1
            border.color: Appearance.colors.colLayer0Border
            radius: Appearance.rounding.windowRounding
            property real padding: 20
            implicitWidth: cheatsheetColumnLayout.implicitWidth + padding * 2
            implicitHeight: cheatsheetColumnLayout.implicitHeight + padding * 2

            Keys.onPressed: event => { // Esc or Alt+A to close
                if (event.key === Qt.Key_Escape || ((event.modifiers & Qt.AltModifier) && event.key === Qt.Key_A)) {
                    cheatsheetRoot.hide();
                    event.accepted = true;
                    return;
                }
                if (event.modifiers === Qt.ControlModifier) {
                    if (event.key === Qt.Key_PageDown) {
                        tabBar.incrementCurrentIndex();
                        event.accepted = true;
                    } else if (event.key === Qt.Key_PageUp) {
                        tabBar.decrementCurrentIndex();
                        event.accepted = true;
                    } else if (event.key === Qt.Key_Tab) {
                        tabBar.setCurrentIndex((tabBar.currentIndex + 1) % root.tabButtonList.length);
                        event.accepted = true;
                    } else if (event.key === Qt.Key_Backtab) {
                        tabBar.setCurrentIndex((tabBar.currentIndex - 1 + root.tabButtonList.length) % root.tabButtonList.length);
                        event.accepted = true;
                    }
                }
            }

            RippleButton { // Close button
                id: closeButton
                implicitWidth: 40
                implicitHeight: 40
                buttonRadius: Appearance.rounding.full
                anchors {
                    top: parent.top
                    right: parent.right
                    topMargin: 20
                    rightMargin: 20
                }

                onClicked: {
                    cheatsheetRoot.hide();
                }

                contentItem: MaterialSymbol {
                    anchors.centerIn: parent
                    horizontalAlignment: Text.AlignHCenter
                    font.pixelSize: Appearance.font.pixelSize.title
                    text: "close"
                }
            }

            ColumnLayout { // Real content
                id: cheatsheetColumnLayout
                anchors.centerIn: parent
                spacing: 10

                Toolbar {
                    Layout.alignment: Qt.AlignHCenter
                    enableShadow: false
                    ToolbarTabBar {
                        id: tabBar
                        tabButtonList: root.tabButtonList

                        Synchronizer on currentIndex {
                            property alias source: swipeView.currentIndex
                        }
                    }
                }

                SwipeView { // Content pages
                    id: swipeView
                    Layout.topMargin: 5
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 10
                    currentIndex: Persistent.states.cheatsheet.tabIndex
                    onCurrentIndexChanged: {
                        Persistent.states.cheatsheet.tabIndex = currentIndex;
                    }

                    implicitWidth: Math.max.apply(null, contentChildren.map(child => child.implicitWidth || 0))
                    implicitHeight: Math.max.apply(null, contentChildren.map(child => child.implicitHeight || 0))

                    clip: true
                    layer.enabled: true
                    layer.effect: OpacityMask {
                        maskSource: Rectangle {
                            width: swipeView.width
                            height: swipeView.height
                            radius: Appearance.rounding.small
                        }
                    }

                    CheatsheetKeybinds {}
                    CheatsheetPeriodicTable {}
                }
            }
        }
    }

    IpcHandler {
        target: "cheatsheet"

        function toggle(): void {
            root.toggle();
        }

        function close(): void {
            root.close();
        }

        function open(): void {
            root.open();
        }
    }

    GlobalShortcut {
        name: "cheatsheetToggle"
        description: "Toggles cheatsheet on press"

        onPressed: {
            root.toggle();
        }
    }

    GlobalShortcut {
        name: "cheatsheetOpen"
        description: "Opens cheatsheet on press"

        onPressed: {
            root.open();
        }
    }

    GlobalShortcut {
        name: "cheatsheetClose"
        description: "Closes cheatsheet on press"

        onPressed: {
            root.close();
        }
    }
}
