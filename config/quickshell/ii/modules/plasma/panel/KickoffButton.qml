/*
    SPDX-FileCopyrightText: 2011 Martin Gräßlin <mgraesslin@kde.org>
    SPDX-FileCopyrightText: 2012 Gregor Taetzner <gregor@freenet.de>
    SPDX-FileCopyrightText: 2012 Marco Martin <mart@kde.org>
    SPDX-FileCopyrightText: 2013 David Edmundson <davidedmundson@kde.org>
    SPDX-FileCopyrightText: 2015 Eike Hein <hein@kde.org>
    SPDX-FileCopyrightText: 2021 Mikel Johnson <mikel5764@gmail.com>
    SPDX-FileCopyrightText: 2021 Noah Davis <noahadvs@gmail.com>

    SPDX-License-Identifier: GPL-2.0-or-later
*/

// BWM: native compact representation, expansion delegated to BWM.
import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PC3
MouseArea {
    id: compactRoot
    // BWM: containment expansion and configuration are supplied by the panel.
    property bool vertical:false
    property string icon:"start-here-kde-symbolic"
    property string menuLabel:""
    property bool expanded:false
    signal toggleRequested(bool expanded)

    // Taken from DigitalClock to ensure uniform sizing when next to each other
    readonly property bool tooSmall: !compactRoot.vertical && Math.round(2 * (compactRoot.height / 5)) <= Kirigami.Theme.smallFont.pixelSize

    readonly property bool shouldHaveIcon: compactRoot.vertical || compactRoot.icon !== ""
    readonly property bool shouldHaveLabel: !compactRoot.vertical && compactRoot.menuLabel !== ""

    readonly property int iconSize: Kirigami.Units.iconSizes.large

    readonly property var sizing: {
        const displayedIcon = imageFallback.visible ? imageFallback : (buttonIcon.valid ? buttonIcon : buttonIconFallback);

        let impWidth = 0;
        if (shouldHaveIcon) {
            impWidth += displayedIcon.width;
        }
        if (shouldHaveLabel) {
            impWidth += labelTextField.contentWidth + labelTextField.Layout.leftMargin + labelTextField.Layout.rightMargin;
        }
        const impHeight = displayedIcon.height > 0 ? displayedIcon.height : iconSize

        // at least square, but can be wider/taller
        if (true) {
            if (compactRoot.vertical) {
                return {
                    preferredWidth: iconSize,
                    preferredHeight: impHeight
                };
            } else { // horizontal
                return {
                    preferredWidth: impWidth,
                    preferredHeight: iconSize
                };
            }
        } else {
            return {
                preferredWidth: impWidth,
                preferredHeight: Kirigami.Units.iconSizes.small,
            };
        }
    }

    implicitWidth: iconSize
    implicitHeight: iconSize

    Layout.preferredWidth: sizing.preferredWidth
    Layout.preferredHeight: sizing.preferredHeight
    Layout.minimumWidth: Layout.preferredWidth
    Layout.minimumHeight: Layout.preferredHeight

    hoverEnabled: true

    property bool wasExpanded

    Accessible.name: qsTr("Application Launcher")
    Accessible.role: Accessible.Button

    onPressed: wasExpanded = compactRoot.expanded
    onClicked: compactRoot.toggleRequested(!wasExpanded)

    DropArea {
        id: compactDragArea
        anchors.fill: parent
        onEntered: drag => {
            if (drag.hasUrls) {
                expandOnDragTimer.start()
            }
        }
        onExited: expandOnDragTimer.stop()
    }

    Timer {
        id: expandOnDragTimer
        // this is an interaction and not an animation, so we want it as a constant
        interval: 250
        onTriggered: compactRoot.toggleRequested(true)
    }

    RowLayout {
        id: iconLabelRow
        anchors.fill: parent
        spacing: 0

        Kirigami.Icon {
            id: buttonIcon

            Layout.fillWidth: compactRoot.vertical
            Layout.fillHeight: !compactRoot.vertical
            Layout.preferredWidth: compactRoot.vertical ? -1 : height / (implicitHeight / implicitWidth)
            Layout.preferredHeight: !compactRoot.vertical ? -1 : width * (implicitHeight / implicitWidth)
            Layout.maximumHeight: Kirigami.Units.iconSizes.huge
            Layout.maximumWidth: Kirigami.Units.iconSizes.huge
            Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
            source: (compactRoot.vertical && !compactRoot.icon ? "start-here-kde-symbolic" : compactRoot.icon)
            active: compactRoot.containsMouse || compactDragArea.containsDrag
            roundToIconSize: implicitHeight === implicitWidth
            visible: valid && !imageFallback.visible
        }

        Kirigami.Icon {
            id: buttonIconFallback
            // fallback is assumed to be square
            Layout.fillWidth: compactRoot.vertical
            Layout.fillHeight: !compactRoot.vertical
            Layout.preferredWidth: compactRoot.vertical ? -1 : height
            Layout.preferredHeight: !compactRoot.vertical ? -1 : width
            Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter

            source: buttonIcon.valid ? null : "start-here-kde-symbolic"
            active: compactRoot.containsMouse || compactDragArea.containsDrag
            visible: !buttonIcon.valid && compactRoot.icon !== "" && !imageFallback.visible
        }

        Image {
            id: imageFallback

            readonly property bool nonSquareImage: sourceSize.width != sourceSize.height

            visible: nonSquareImage && status == Image.Ready
            source: compactRoot.icon.startsWith("/") ? "file:" + compactRoot.icon.split("/").map(encodeURIComponent).join("/") : ""

            Layout.fillWidth: compactRoot.vertical
            Layout.fillHeight: !compactRoot.vertical
            Layout.preferredWidth: compactRoot.vertical ? -1 : height / (implicitHeight / implicitWidth)
            Layout.preferredHeight: !compactRoot.vertical ? -1 : width * (implicitHeight / implicitWidth)
            Layout.maximumHeight: compactRoot.vertical ? -1 : Kirigami.Units.iconSizes.huge
            Layout.maximumWidth: compactRoot.vertical ? Kirigami.Units.iconSizes.huge : -1
            Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
            fillMode: Image.PreserveAspectFit
            mipmap: true
        }

        PC3.Label {
            id: labelTextField

            Layout.fillHeight: true
            Layout.leftMargin: Kirigami.Units.smallSpacing
            Layout.rightMargin: Kirigami.Units.smallSpacing

            text: compactRoot.menuLabel
            textFormat: Text.StyledText
            horizontalAlignment: Text.AlignLeft
            verticalAlignment: Text.AlignVCenter
            wrapMode: Text.NoWrap
            fontSizeMode: Text.VerticalFit
            font.pixelSize: compactRoot.tooSmall ? Kirigami.Theme.defaultFont.pixelSize : Kirigami.Units.iconSizes.roundedIconSize(Kirigami.Units.gridUnit * 2)
            minimumPointSize: Kirigami.Theme.smallFont.pointSize
            visible: compactRoot.shouldHaveLabel
        }
    }
}
