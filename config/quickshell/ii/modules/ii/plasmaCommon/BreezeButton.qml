import QtQuick
import QtQuick.Layouts

// Push button with Breeze frame
MouseArea {
    id: bb
    property url iconSource: ""
    property string label: ""
    property bool destructive: false
    implicitHeight: 28
    implicitWidth: bbRow.implicitWidth + 20
    hoverEnabled: true
    cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
    opacity: enabled ? 1 : 0.4

    Rectangle {
        anchors.fill: parent
        radius: 4
        color: bb.containsPress ? Breeze.accentSubtle : Breeze.buttonBg
        border.width: 1
        border.color: bb.containsMouse ? (bb.destructive ? Breeze.negative : Breeze.accent) : Breeze.buttonBorder
        Behavior on border.color { ColorAnimation { duration: 100 } }
    }

    RowLayout {
        id: bbRow
        anchors.centerIn: parent
        spacing: 6
        Image {
            visible: bb.iconSource.toString().length > 0
            Layout.preferredWidth: 16
            Layout.preferredHeight: 16
            sourceSize: Qt.size(16, 16)
            source: bb.iconSource
        }
        Text {
            text: bb.label
            color: Breeze.text
            font.family: Breeze.fontFamily
            font.pixelSize: 12
        }
    }
}
