import QtQuick
import QtQuick.Controls

// Anfitrión común: cada skin dibuja y anima su propia mascota.
Item {
    id: mascot
    required property var style
    property bool motionEnabled: true
    readonly property string variant: style.skin === "retro" ? "retro" : style.skin === "plasma" ? "plasma" : "default"
    readonly property bool moving: motionEnabled && visible
    readonly property bool ready: character.status === Loader.Ready
    readonly property var artwork: character.item
    property bool blinking: false
    property real shiftX: 0
    property real shiftY: 0
    readonly property bool reacting: glide.running
    implicitWidth: 136
    implicitHeight: 108
    Accessible.name: "Mascota de BWM"
    Accessible.role: Accessible.Button
    Accessible.onPressAction: mascot.activate()
    activeFocusOnTab: true
    Keys.onReturnPressed: activate()
    Keys.onSpacePressed: activate()

    function activate() {
        if (moving && ready) { artwork.activate(); glide.restart(); }
    }
    Loader {
        id: character
        anchors.fill: parent
        transform: Translate { x: mascot.shiftX; y: mascot.shiftY }
        source: Qt.resolvedUrl("mascot/" + mascot.variant + "/Character.qml")
        onLoaded: {
            item.style = Qt.binding(() => mascot.style);
            item.blinking = Qt.binding(() => mascot.blinking);
            item.greeting = Qt.binding(() => pointer.containsMouse || mascot.activeFocus);
            item.motionEnabled = Qt.binding(() => mascot.moving);
        }
    }
    Timer {
        interval: 4200
        running: mascot.moving
        repeat: true
        onTriggered: blink.restart()
    }
    SequentialAnimation {
        id: blink
        PropertyAction { target: mascot; property: "blinking"; value: true }
        PauseAnimation { duration: 140 }
        PropertyAction { target: mascot; property: "blinking"; value: false }
    }
    SequentialAnimation {
        id: glide
        ParallelAnimation {
            NumberAnimation { target: mascot; property: "shiftX"; to: 12; duration: 200; easing.type: Easing.OutCubic }
            NumberAnimation { target: mascot; property: "shiftY"; to: -8; duration: 200; easing.type: Easing.OutCubic }
        }
        ParallelAnimation {
            NumberAnimation { target: mascot; property: "shiftX"; to: -6; duration: 300; easing.type: Easing.InOutSine }
            NumberAnimation { target: mascot; property: "shiftY"; to: -16; duration: 300; easing.type: Easing.InOutSine }
        }
        ParallelAnimation {
            NumberAnimation { target: mascot; property: "shiftX"; to: 0; duration: 430; easing.type: Easing.OutBack }
            NumberAnimation { target: mascot; property: "shiftY"; to: 0; duration: 430; easing.type: Easing.OutBack }
        }
    }
    onMovingChanged: if (!moving) { blink.stop(); blinking = false; glide.stop(); shiftX = 0; shiftY = 0; }
    MouseArea {
        id: pointer
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: { mascot.forceActiveFocus(Qt.MouseFocusReason); mascot.activate(); }
    }
    ToolTip.visible: pointer.containsMouse
    ToolTip.text: "BWM"
    ToolTip.delay: 600
}
