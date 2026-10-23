import QtQuick
import QtQuick.Layouts

// PlasmoidHeading: darker toolbar with bottom border and optional indeterminate busy bar
Rectangle {
    id: hdr
    property bool busy: false
    default property alias content: row.data
    Layout.fillWidth: true
    Layout.preferredHeight: 44
    color: Breeze.headerBg
    topLeftRadius: 6
    topRightRadius: 6

    RowLayout {
        id: row
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 6
        spacing: 6
    }

    Rectangle {
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: 1
        color: Breeze.border
    }

    Item {
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: 2
        clip: true
        visible: hdr.busy
        Rectangle {
            id: busyBar
            width: parent.width / 3
            height: parent.height
            color: Breeze.accent
            NumberAnimation on x {
                running: hdr.busy
                from: -busyBar.width
                to: hdr.width
                duration: 1200
                loops: Animation.Infinite
            }
        }
    }
}
