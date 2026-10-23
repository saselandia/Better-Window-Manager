import QtQuick

// Breeze slider: thin groove, accent fill, round handle that grows on hover/press
Item {
    id: sl
    property real value: 0          // 0..1, bound to the model while not dragging
    property real maxValue: 1
    signal moved(real value)
    implicitHeight: 22
    implicitWidth: 120
    opacity: enabled ? 1 : 0.4

    readonly property real visualPos: Math.max(0, Math.min(1, (area.pressed ? area.dragValue : sl.value) / sl.maxValue))

    Rectangle { // groove
        anchors.verticalCenter: parent.verticalCenter
        width: parent.width
        height: 4
        radius: 2
        color: Breeze.buttonBg
        border.width: 1
        border.color: Breeze.buttonBorder

        Rectangle { // fill
            width: sl.visualPos * parent.width
            height: parent.height
            radius: 2
            color: Breeze.accent
        }
    }

    Rectangle { // handle
        property real d: area.pressed || area.containsMouse ? 16 : 14
        width: d
        height: d
        radius: d / 2
        anchors.verticalCenter: parent.verticalCenter
        x: sl.visualPos * (sl.width - 14) - (d - 14) / 2
        color: area.pressed ? Breeze.accent : "#fcfcfc"
        border.width: 1
        border.color: (area.pressed || area.containsMouse) ? Breeze.accent : Breeze.buttonBorder
        Behavior on d { NumberAnimation { duration: 80 } }
    }

    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        property real dragValue: 0
        function update(mouseX) {
            dragValue = Math.max(0, Math.min(1, (mouseX - 7) / (sl.width - 14))) * sl.maxValue;
            sl.moved(dragValue);
        }
        onPressed: mouse => update(mouse.x)
        onPositionChanged: mouse => { if (pressed) update(mouse.x); }
        onWheel: wheel => {
            const step = 0.02 * sl.maxValue * (wheel.angleDelta.y > 0 ? 1 : -1);
            sl.moved(Math.max(0, Math.min(sl.maxValue, sl.value + step)));
        }
    }
}
