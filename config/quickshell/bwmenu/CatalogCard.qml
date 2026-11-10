import QtQuick
import QtQuick.Layouts

Rectangle {
    id: card
    required property var entry
    required property var style
    signal openRequested()
    implicitHeight: 282
    radius: 0
    color: style.surface
    border.color: style.border
    border.width: 1
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 9
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 135
            radius: 0
            color: card.style.background
            clip: true
            Image { id: image; anchors.fill: parent; source: card.entry.preview; fillMode: Image.PreserveAspectCrop; asynchronous: true; mipmap: true }
            Text { anchors.centerIn: parent; visible: image.status === Image.Error; text: "✦"; color: card.style.accent; font.pixelSize: 32 }
        }
        Text { Layout.fillWidth: true; text: card.entry.name; textFormat: Text.PlainText; color: card.style.foreground; font.family: card.style.font; font.pixelSize: 17; font.bold: true; elide: Text.ElideRight }
        Text { Layout.fillWidth: true; text: card.entry.description; textFormat: Text.PlainText; color: card.style.muted; font.family: card.style.font; font.pixelSize: 11; maximumLineCount: 2; wrapMode: Text.Wrap; elide: Text.ElideRight }
        RowLayout {
            Layout.fillWidth: true
            Text { Layout.fillWidth: true; text: card.entry.version + " · " + (card.entry.installed ? "Instalada" : "Disponible"); color: card.style.accent; font.family: card.style.font; font.pixelSize: 11; elide: Text.ElideRight }
            MenuButton { style: card.style; text: card.entry.installed ? "Ver skin" : "Ver instalación"; onClicked: card.openRequested() }
        }
    }
}
