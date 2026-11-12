/*
    SPDX-FileCopyrightText: 2013 Sebastian Kügler <sebas@kde.org>
    SPDX-FileCopyrightText: 2015 Marco Martin <mart@kde.org>

    SPDX-License-Identifier: LGPL-2.0-or-later
*/

import QtQuick

import org.kde.kirigami as Kirigami
import org.kde.plasma.core as PlasmaCore


PlasmaCore.ToolTipArea {
    id: tooltip
    // BWM: tray state supplied by our host, no PlasmaShell singleton.
    property bool expanded:false
    property string edge:"bottom"
    signal toggleRequested(bool expanded)

    readonly property int arrowAnimationDuration: Kirigami.Units.shortDuration
    property bool vertical:edge === "left" || edge === "right"
    property int iconSize: Kirigami.Units.iconSizes.smallMedium
    implicitWidth: iconSize
    implicitHeight: iconSize
    activeFocusOnTab: true

    Accessible.name: subText
    Accessible.description: qsTr("Show all the items in the system tray in a popup")
    Accessible.role: Accessible.Button
    Accessible.onPressAction: tooltip.toggleRequested(!tooltip.expanded)

    Keys.onPressed: event => {
        switch (event.key) {
        case Qt.Key_Space:
        case Qt.Key_Enter:
        case Qt.Key_Return:
        case Qt.Key_Select:
            tooltip.toggleRequested(!tooltip.expanded);
        }
    }

    subText: tooltip.expanded ? qsTr("Close popup") : qsTr("Show hidden icons")

    property bool wasExpanded

    TapHandler {
        onPressedChanged: {
            if (pressed) {
                tooltip.wasExpanded = tooltip.expanded;
            }
        }
        onTapped: (eventPoint, button) => {
            tooltip.toggleRequested(!tooltip.wasExpanded);
            // BWM: hidden selection belongs to the popup.
        }
    }

    Kirigami.Icon {
        anchors.fill: parent

        rotation: tooltip.expanded ? 180 : 0
        Behavior on rotation {
            RotationAnimation {
                duration: tooltip.arrowAnimationDuration
            }
        }
        opacity: tooltip.expanded ? 0 : 1
        Behavior on opacity {
            NumberAnimation {
                duration: tooltip.arrowAnimationDuration
            }
        }

        source: {
            if (tooltip.edge === "top") {
                return "arrow-down-symbolic";
            } else if (tooltip.edge === "left") {
                return "arrow-right-symbolic";
            } else if (tooltip.edge === "right") {
                return "arrow-left-symbolic";
            } else {
                return "arrow-up-symbolic";
            }
        }
    }

    Kirigami.Icon {
        anchors.fill: parent

        rotation: tooltip.expanded ? 0 : -180
        Behavior on rotation {
            RotationAnimation {
                duration: tooltip.arrowAnimationDuration
            }
        }
        opacity: tooltip.expanded ? 1 : 0
        Behavior on opacity {
            NumberAnimation {
                duration: tooltip.arrowAnimationDuration
            }
        }

        source: {
            if (tooltip.edge === "top") {
                return "arrow-up-symbolic";
            } else if (tooltip.edge === "left") {
                return "arrow-left-symbolic";
            } else if (tooltip.edge === "right") {
                return "arrow-right-symbolic";
            } else {
                return "arrow-down-symbolic";
            }
        }
    }
}
