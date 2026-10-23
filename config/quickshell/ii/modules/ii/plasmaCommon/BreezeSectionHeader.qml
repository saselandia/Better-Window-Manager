import QtQuick
import QtQuick.Layouts

// PlasmaExtras.ListSectionHeader
RowLayout {
    id: sh
    property string title: ""
    Layout.fillWidth: true
    Layout.topMargin: 6
    Layout.leftMargin: 6
    Layout.rightMargin: 6
    spacing: 8
    Text {
        text: sh.title
        color: Breeze.textMuted
        font.family: Breeze.fontFamily
        font.pixelSize: 11
        font.weight: Font.DemiBold
    }
    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 1
        color: Breeze.border
    }
}
