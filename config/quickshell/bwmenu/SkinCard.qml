import QtQuick
import QtQuick.Layouts

Rectangle {
    id: card
    required property var skin
    required property var style
    property bool selected: false
    property bool active: false
    property bool ready: false
    signal chosen()
    implicitHeight: 254
    radius: skin.rounding
    color: selected ? style.selection : style.surface
    border.color: selected || active ? style.accent : style.border
    border.width: selected ? 2 : 1
    activeFocusOnTab: true
    Keys.onReturnPressed: chosen()
    Keys.onSpacePressed: chosen()

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 146
            radius: Math.min(card.skin.rounding, 10)
            color: card.style.background
            clip: true
            Image {
                anchors.fill: parent
                source: "file://" + (card.active && card.skin.wallpaper ? card.skin.wallpaper : card.skin.preview)
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
                mipmap: true
            }
            Rectangle {
                visible: card.active && !!card.skin.wallpaper
                width: parent.width * 0.75
                height: parent.height * 0.55
                anchors.centerIn: parent
                radius: Math.min(card.skin.rounding, 8)
                color: card.style.background
                border.color: card.style.accent
                border.width: 1
                Column {
                    anchors.centerIn: parent
                    spacing: 7
                    Text { text: card.style.themeName; color: card.style.accent; font.family: card.style.font; font.pixelSize: 11; font.bold: true }
                    Row { spacing: 4; Repeater { model: [card.style.accent, card.style.foreground, card.style.surface]; Rectangle { required property string modelData; width: 22; height: 5; color: modelData; radius: Math.min(card.skin.rounding, 3) } } }
                }
            }
            Rectangle {
                anchors.fill: parent
                gradient: Gradient {
                    GradientStop { position: 0.3; color: "transparent" }
                    GradientStop { position: 1; color: "#bb000000" }
                }
            }
            Text {
                anchors.left: parent.left
                anchors.bottom: parent.bottom
                anchors.margins: 10
                text: card.skin.windows === "traditional" ? "VENTANAS LIBRES" : "MOSAICO"
                color: "white"
                font.pixelSize: 10
                font.bold: true
                font.letterSpacing: 1
            }
            Rectangle {
                visible: card.active
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 8
                width: activeText.implicitWidth + 16
                height: 24
                radius: Math.min(card.skin.rounding, 12)
                color: card.style.accent
                Text { id: activeText; anchors.centerIn: parent; text: "● ACTIVA"; color: card.style.onAccent; font.pixelSize: 10; font.bold: true }
            }
        }
        Text {
            Layout.fillWidth: true
            text: card.skin.name
            color: card.style.foreground
            font.family: card.skin.font
            font.pixelSize: 17
            font.bold: true
            elide: Text.ElideRight
        }
        Text {
            Layout.fillWidth: true
            text: card.ready ? "✓  Requisitos completos" : "!  Revisar requisitos"
            color: card.ready ? card.style.muted : card.style.error
            font.family: card.style.font
            font.pixelSize: 11
            elide: Text.ElideRight
        }
    }
    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: { card.forceActiveFocus(); card.chosen(); }
    }
    Rectangle {
        visible: card.activeFocus
        anchors.fill: parent
        anchors.margins: -3
        color: "transparent"
        radius: card.radius
        border.color: card.style.accent
        border.width: 1
    }
}
