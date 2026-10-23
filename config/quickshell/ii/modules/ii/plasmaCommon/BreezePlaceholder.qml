import QtQuick
import QtQuick.Layouts

// PlasmaExtras.PlaceholderMessage: big icon, message and optional action
ColumnLayout {
    id: ph
    property url iconSource: ""
    property string text: ""
    property string actionLabel: ""
    property url actionIcon: ""
    property int maxTextWidth: 320
    signal triggered()
    spacing: 10

    Image {
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 64
        Layout.preferredHeight: 64
        sourceSize: Qt.size(64, 64)
        source: ph.iconSource
        opacity: 0.6
    }
    Text {
        Layout.alignment: Qt.AlignHCenter
        Layout.maximumWidth: ph.maxTextWidth
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.WordWrap
        text: ph.text
        color: Breeze.textMuted
        font.family: Breeze.fontFamily
        font.pixelSize: 15
    }
    BreezeButton {
        visible: ph.actionLabel.length > 0
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: 4
        iconSource: ph.actionIcon
        label: ph.actionLabel
        onClicked: ph.triggered()
    }
}
