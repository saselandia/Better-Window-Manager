/*
    SPDX-FileCopyrightText: 2014 Ashish Madeti <ashishmadeti@gmail.com>
    SPDX-FileCopyrightText: 2016 Kai Uwe Broulik <kde@privat.broulik.de>
    SPDX-FileCopyrightText: 2022 ivan (@ratijas) tkachenko <me@ratijas.tk>

    SPDX-License-Identifier: GPL-2.0-or-later
*/

import QtQuick
import QtQuick.Layouts

import org.kde.plasma.core as PlasmaCore
import org.kde.kirigami as Kirigami
import org.kde.ksvg as KSvg

import "." as PanelLocal

Item {
    id: root

    // BWM: the shared minimize state replaces KWin's controllers.
    property bool vertical:false
    property string edge:"bottom"
    readonly property var activeController:({active:PanelLocal.DesktopState.showingDesktop})
    readonly property string title:qsTr("Show Desktop")
    readonly property string toolTipSubText:qsTr("Show the desktop")
    implicitWidth:Kirigami.Units.iconSizes.medium
    implicitHeight:Kirigami.Units.iconSizes.medium
    Layout.minimumWidth:implicitWidth; Layout.maximumWidth:implicitWidth
    Layout.minimumHeight:implicitHeight; Layout.maximumHeight:implicitHeight
    Layout.preferredWidth:implicitWidth; Layout.preferredHeight:implicitHeight
    signal toggleRequested()
    MouseArea {
        id: mouseArea
        anchors.fill: parent

        activeFocusOnTab: true
        hoverEnabled: true

        onClicked: root.toggleRequested();

        Keys.onPressed: event => {
            switch (event.key) {
            case Qt.Key_Space:
            case Qt.Key_Enter:
            case Qt.Key_Return:
            case Qt.Key_Select:
                root.toggleRequested();
                break;
            }
        }

        Accessible.name: root.title
        Accessible.description: root.toolTipSubText
        Accessible.role: Accessible.Button
        Accessible.onPressAction: root.toggleRequested()

        Kirigami.Icon {
            anchors.fill: parent
            active: mouseArea.containsMouse || root.activeController.active
            source: "user-desktop-symbolic"
        }

        // also activate when dragging an item over the plasmoid so a user can easily drag data to the desktop
        DropArea {
            anchors.fill: parent
            onEntered: activateTimer.start()
            onExited: activateTimer.stop()
        }

        Timer {
            id: activateTimer
            interval: 250 // to match TaskManager
            onTriggered: root.toggleRequested()
        }

        // Active/not active indicator
        KSvg.FrameSvgItem {
            Accessible.name: qsTr("Show Desktop Active Indicator")  // qmllint disable unqualified
            property var containerMargins: {
                let item = this;
                while (item.parent) {
                    item = item.parent;
                    if (item.isAppletContainer) {
                        return item.getMargins;
                    }
                }
                return undefined;
            }

            anchors {
                fill: parent
                property bool returnAllMargins: true
                // The above makes sure margin is returned even for side margins
                // that would be otherwise turned off.
                topMargin: !root.vertical && containerMargins ? -containerMargins('top', returnAllMargins) : 0
                leftMargin: root.vertical && containerMargins ? -containerMargins('left', returnAllMargins) : 0
                rightMargin: root.vertical && containerMargins ? -containerMargins('right', returnAllMargins) : 0
                bottomMargin: !root.vertical && containerMargins ? -containerMargins('bottom', returnAllMargins) : 0
            }
            imagePath: "widgets/tabbar"
            visible: opacity > 0
            prefix: {
                let prefix;
                switch (root.edge) {
                case "left":
                    prefix = "west-active-tab";
                    break;
                case "top":
                    prefix = "north-active-tab";
                    break;
                case "right":
                    prefix = "east-active-tab";
                    break;
                default:
                    prefix = "south-active-tab";
                }
                if (!hasElementPrefix(prefix)) {
                    prefix = "active-tab";
                }
                return prefix;
            }
            opacity: root.activeController.active ? 1 : 0

            Behavior on opacity {
                NumberAnimation {
                    duration: Kirigami.Units.shortDuration
                    easing.type: Easing.InOutQuad
                }
            }
        }

        PlasmaCore.ToolTipArea {
            id: toolTip
            anchors.fill: parent
            mainText: root.title
            subText: root.toolTipSubText
            textFormat: Text.PlainText
        }
    }

}
