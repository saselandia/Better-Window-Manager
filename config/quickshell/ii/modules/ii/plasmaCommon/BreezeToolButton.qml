import QtQuick
import QtQuick.Layouts

// Flat tool button (Plasma header style): transparent, hover fill + accent frame
MouseArea {
    id: tb
    property url iconSource: ""
    property string label: ""
    property bool checked: false
    implicitHeight: 28
    implicitWidth: tbRow.implicitWidth + (label.length > 0 ? 16 : 10)
    hoverEnabled: true
    cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
    opacity: enabled ? 1 : 0.4

    Rectangle {
        anchors.fill: parent
        radius: 4
        color: (tb.containsPress || tb.checked) ? Breeze.accentSubtle : (tb.containsMouse ? Breeze.hover : "transparent")
        border.width: (tb.containsMouse || tb.checked) ? 1 : 0
        border.color: Breeze.accentBorder
    }

    RowLayout {
        id: tbRow
        anchors.centerIn: parent
        spacing: 6
        Image {
            visible: tb.iconSource.toString().length > 0
            Layout.preferredWidth: 16
            Layout.preferredHeight: 16
            sourceSize: Qt.size(16, 16)
            source: tb.iconSource
        }
        Text {
            visible: tb.label.length > 0
            text: tb.label
            color: Breeze.text
            font.family: Breeze.fontFamily
            font.pixelSize: 12
        }
    }
}
