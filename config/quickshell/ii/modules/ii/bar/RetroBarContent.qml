import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import Quickshell.Services.UPower
import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.common.models

Item {
    id: root

    property var screen: root.QsWindow.window?.screen
    readonly property HyprlandMonitor monitor: Hyprland.monitorFor(screen)
    readonly property int activeWsId: monitor?.activeWorkspace?.id ?? 1

    // -----------------------------------------------------------------
    // Left Section: Monospace Workspace Numbers [ 1 ]  2  3  4  5
    // -----------------------------------------------------------------
    MouseArea {
        id: wsArea
        anchors {
            left: parent.left
            leftMargin: 10
            top: parent.top
            bottom: parent.bottom
        }
        width: wsRow.implicitWidth + 8

        onWheel: event => {
            if (event.angleDelta.y > 0) {
                let nextId = Math.max(1, root.activeWsId - 1);
                Hyprland.dispatch(`hl.dsp.focus({workspace = ${nextId}})`);
            } else if (event.angleDelta.y < 0) {
                let nextId = Math.min(10, root.activeWsId + 1);
                Hyprland.dispatch(`hl.dsp.focus({workspace = ${nextId}})`);
            }
        }

        Row {
            id: wsRow
            anchors.centerIn: parent
            spacing: 6

            Repeater {
                model: 10
                delegate: Item {
                    id: wsItem
                    property int wsId: index + 1
                    property bool isActive: root.activeWsId === wsId
                    property bool isOccupied: Hyprland.workspaces.values.some(ws => ws.id === wsId)

                    implicitWidth: wsLabel.implicitWidth + (isActive ? 8 : 4)
                    implicitHeight: root.height

                    Text {
                        id: wsLabel
                        anchors.centerIn: parent
                        text: wsItem.isActive ? `[ ${wsItem.wsId} ]` : `${wsItem.wsId}`
                        font.family: "JetBrains Mono NF"
                        font.pixelSize: 11
                        font.weight: wsItem.isActive ? Font.Bold : Font.Normal
                        color: wsItem.isActive 
                            ? Appearance.colors.colPrimary 
                            : (wsBtnMouse.containsMouse 
                                ? Appearance.colors.colPrimary 
                                : (wsItem.isOccupied ? Appearance.colors.colOnSurface : Appearance.colors.colOutline))

                        Behavior on color {
                            ColorAnimation { duration: 100 }
                        }
                    }

                    MouseArea {
                        id: wsBtnMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            Hyprland.dispatch(`hl.dsp.focus({workspace = ${wsItem.wsId}})`);
                        }
                    }
                }
            }
        }
    }

    // -----------------------------------------------------------------
    // Center Section: Minimalist Monospace Clock (e.g. Sunday 14:19)
    // -----------------------------------------------------------------
    MouseArea {
        id: centerClockArea
        anchors.centerIn: parent
        implicitWidth: centerClockText.implicitWidth + 16
        implicitHeight: root.height
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor

        onClicked: {
            GlobalStates.sidebarRightOpen = !GlobalStates.sidebarRightOpen;
        }

        Text {
            id: centerClockText
            anchors.centerIn: parent
            text: Qt.formatDateTime(DateTime.clock.date, "dddd HH:mm")
            font.family: "JetBrains Mono NF"
            font.pixelSize: 11
            font.weight: Font.DemiBold
            color: centerClockArea.containsMouse ? Appearance.colors.colPrimary : Appearance.colors.colOnSurface

            Behavior on color {
                ColorAnimation { duration: 120 }
            }
        }
    }

    // -----------------------------------------------------------------
    // Right Section: Telemetry & Status Indicators
    // -----------------------------------------------------------------
    RowLayout {
        id: rightStatusRow
        anchors {
            right: parent.right
            rightMargin: 12
            top: parent.top
            bottom: parent.bottom
        }
        spacing: 12

        // System Tray (Compact)
        SysTray {
            Layout.alignment: Qt.AlignVCenter
            Layout.fillHeight: true
        }

        // Audio Volume Readout
        MouseArea {
            id: volArea
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: volContent.implicitWidth + 4
            implicitHeight: root.height
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor

            onClicked: {
                if (Audio.sink?.audio) {
                    Audio.sink.audio.muted = !Audio.sink.audio.muted;
                }
            }
            onWheel: event => {
                if (event.angleDelta.y > 0) Audio.incrementVolume();
                else Audio.decrementVolume();
            }

            Row {
                id: volContent
                anchors.centerIn: parent
                spacing: 4

                Text {
                    text: (Audio.sink?.audio?.muted ?? false) ? "󰝟" : ""
                    font.family: "JetBrains Mono NF"
                    font.pixelSize: 12
                    color: (Audio.sink?.audio?.muted ?? false) ? Appearance.colors.colError : (volArea.containsMouse ? Appearance.colors.colPrimary : Appearance.colors.colOnSurface)
                    anchors.verticalCenter: parent.verticalCenter
                }

                Text {
                    text: `${Math.round((Audio.sink?.audio?.volume ?? 0) * 100)}%`
                    font.family: "JetBrains Mono NF"
                    font.pixelSize: 11
                    color: volArea.containsMouse ? Appearance.colors.colPrimary : Appearance.colors.colOnSurface
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }

        // Network Status
        MouseArea {
            id: netArea
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: netIcon.implicitWidth + 4
            implicitHeight: root.height
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: {
                GlobalStates.sidebarRightOpen = !GlobalStates.sidebarRightOpen;
            }

            Text {
                id: netIcon
                anchors.centerIn: parent
                text: Network.connected ? "󰖩" : "󰤮"
                font.family: "JetBrains Mono NF"
                font.pixelSize: 12
                color: Network.connected ? Appearance.colors.colPrimary : Appearance.colors.colOutline
            }
        }

        // Battery Status (if available)
        Item {
            visible: Battery.available
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: batContent.implicitWidth + 4
            implicitHeight: root.height

            Row {
                id: batContent
                anchors.centerIn: parent
                spacing: 4

                Text {
                    text: Battery.charging ? "󰂄" : (Battery.percentage > 80 ? "󰁹" : (Battery.percentage > 40 ? "󰁿" : "󰁻"))
                    font.family: "JetBrains Mono NF"
                    font.pixelSize: 12
                    color: Battery.percentage < 20 ? Appearance.colors.colError : Appearance.colors.colPrimary
                    anchors.verticalCenter: parent.verticalCenter
                }

                Text {
                    text: `${Math.round(Battery.percentage)}%`
                    font.family: "JetBrains Mono NF"
                    font.pixelSize: 11
                    color: Appearance.colors.colOnSurface
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }

        // Theme Picker Quick Action
        MouseArea {
            id: themeBtn
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: 18
            implicitHeight: root.height
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: {
                Quickshell.execDetached(["/home/sasel/.config/hypr/scripts/theme-picker.sh"]);
            }

            Text {
                anchors.centerIn: parent
                text: "󰔎"
                font.family: "JetBrains Mono NF"
                font.pixelSize: 12
                color: themeBtn.containsMouse ? Appearance.colors.colPrimary : Appearance.colors.colOutline
            }
        }
    }
}
