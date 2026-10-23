import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import QtQuick.Layouts
import Quickshell.Widgets
import qs.modules.ii.plasmaCommon

Item {
    id: root
    required property real value
    required property string icon
    required property string name
    property bool rotateIcon: false
    property bool scaleIcon: false
    property alias from: valueProgressBar.from
    property alias to: valueProgressBar.to

    // KDE Plasma theme: Breeze-styled OSD (icon from assets/icons/breeze-dark/audio/<name>.svg)
    readonly property bool plasma: Appearance.isPlasma
    property string breezeIcon: "video-display-brightness"
    property bool breezeMuted: false

    property real valueIndicatorVerticalPadding: 9
    property real valueIndicatorLeftPadding: 10
    property real valueIndicatorRightPadding: 20 // An icon is circle ish, a column isn't, hence the extra padding

    implicitWidth: plasma ? 286 : Appearance.sizes.osdWidth + 2 * Appearance.sizes.elevationMargin
    implicitHeight: plasma ? 72 : valueIndicator.implicitHeight + 2 * Appearance.sizes.elevationMargin

    // Plasma OSD: dark Breeze card, 32px icon, thin accent bar and percentage
    Rectangle {
        id: plasmaOsd
        visible: root.plasma
        anchors { fill: parent; margins: 8 }
        radius: 7
        color: "#f2232629"
        border.width: 1
        border.color: Breeze.border

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 14
            anchors.rightMargin: 14
            spacing: 12

            Image {
                Layout.preferredWidth: 32
                Layout.preferredHeight: 32
                sourceSize: Qt.size(64, 64)
                source: Breeze.icon("audio", root.breezeIcon)
            }
            Rectangle { // progress groove
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredHeight: 6
                radius: 3
                color: Breeze.buttonBg
                border.width: 1
                border.color: Breeze.buttonBorder
                Rectangle {
                    width: Math.max(0, Math.min(1, (root.value - valueProgressBar.from) / (valueProgressBar.to - valueProgressBar.from))) * parent.width
                    height: parent.height
                    radius: 3
                    color: root.breezeMuted ? Breeze.textMuted : Breeze.accent
                    Behavior on width { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
                }
            }
            Text {
                Layout.preferredWidth: 40
                horizontalAlignment: Text.AlignRight
                text: Math.round(root.value * 100) + "%"
                color: Breeze.text
                font.family: Breeze.fontFamily
                font.pixelSize: 14
            }
        }
    }

    StyledRectangularShadow {
        visible: !root.plasma
        target: valueIndicator
    }
    Rectangle {
        id: valueIndicator
        visible: !root.plasma
        anchors {
            fill: parent
            margins: Appearance.sizes.elevationMargin
        }
        radius: Appearance.rounding.full
        color: Appearance.colors.colLayer0

        implicitWidth: valueRow.implicitWidth
        implicitHeight: valueRow.implicitHeight

        RowLayout { // Icon on the left, stuff on the right
            id: valueRow
            Layout.margins: 10
            anchors.fill: parent
            spacing: 10

            Item {
                implicitWidth: 30
                implicitHeight: 30
                Layout.alignment: Qt.AlignVCenter
                Layout.leftMargin: valueIndicatorLeftPadding
                Layout.topMargin: valueIndicatorVerticalPadding
                Layout.bottomMargin: valueIndicatorVerticalPadding

                MaterialSymbol { // Icon
                    anchors {
                        centerIn: parent
                        alignWhenCentered: !root.rotateIcon
                    }
                    color: Appearance.colors.colOnLayer0
                    renderType: Text.QtRendering

                    text: root.icon
                    iconSize: 20 + 10 * (root.scaleIcon ? value : 1)
                    rotation: 180 * (root.rotateIcon ? value : 0)

                    Behavior on iconSize {
                        animation: Appearance.animation.elementMoveEnter.numberAnimation.createObject(this)
                    }
                    Behavior on rotation {
                        animation: Appearance.animation.elementMoveEnter.numberAnimation.createObject(this)
                    }
                
                }
            }
            ColumnLayout { // Stuff
                Layout.alignment: Qt.AlignVCenter
                Layout.rightMargin: valueIndicatorRightPadding
                spacing: 5

                RowLayout { // Name fill left, value on the right end
                    Layout.leftMargin: valueProgressBar.height / 2 // Align text with progressbar radius curve's left end
                    Layout.rightMargin: valueProgressBar.height / 2 // Align text with progressbar radius curve's left end

                    StyledText {
                        color: Appearance.colors.colOnLayer0
                        font.pixelSize: Appearance.font.pixelSize.small
                        Layout.fillWidth: true
                        text: root.name
                    }

                    StyledText {
                        color: Appearance.colors.colOnLayer0
                        font.pixelSize: Appearance.font.pixelSize.small
                        Layout.fillWidth: false
                        text: Math.round(root.value * 100)
                    }
                }
                
                StyledProgressBar {
                    id: valueProgressBar
                    Layout.fillWidth: true
                    value: root.value
                }
            }
        }
    }
}
