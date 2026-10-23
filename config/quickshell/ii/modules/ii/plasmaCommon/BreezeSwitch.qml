import QtQuick

// Breeze toggle switch
MouseArea {
    id: sw
    property bool checked: false
    signal toggled()
    implicitWidth: 36
    implicitHeight: 20
    hoverEnabled: true
    cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
    opacity: enabled ? 1 : 0.4
    onClicked: sw.toggled()

    Rectangle {
        anchors.fill: parent
        radius: height / 2
        color: sw.checked ? Breeze.accent : Breeze.buttonBg
        border.width: 1
        border.color: (sw.checked || sw.containsMouse) ? Breeze.accent : Breeze.buttonBorder
        Behavior on color { ColorAnimation { duration: 120 } }

        Rectangle {
            width: 16
            height: 16
            radius: 8
            anchors.verticalCenter: parent.verticalCenter
            x: sw.checked ? parent.width - width - 2 : 2
            color: sw.checked ? "#fcfcfc" : "#bdc3c7"
            Behavior on x { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
        }
    }
}
