pragma ComponentBehavior: Bound
import QtQuick

// Material You / end-4: una silueta blanda y cuatro puntos que florecen al pulsar.
Item {
    id: scene
    property var style: ({accent:"#b9c3ff", background:"#171b2b", surface:"#272b40", foreground:"#e2e4ff", onAccent:"#20254d"})
    property bool blinking: false
    property bool greeting: false
    property bool motionEnabled: true
    property real breath: 0
    property real bloom: 0
    property real turn: 0
    readonly property bool reacting: flourish.running
    function activate() { flourish.restart(); }
    onMotionEnabledChanged: if (!motionEnabled) { flourish.stop(); bloom = 0; turn = 0; }

    Item {
        x: 32; y: 15 - scene.breath * 2 - scene.bloom * 2
        width: 72; height: 68
        transform: Scale { origin.x: 36; origin.y: 62; xScale: 1 + scene.bloom * 0.055; yScale: 1 + scene.breath * 0.02 - scene.bloom * 0.04 }
        Rectangle { x: 18; y: 5; width: 4; height: 16; radius: 2; rotation: -16; color: scene.style.accent }
        Rectangle { x: 14; y: 3; width: 9; height: 9; radius: 5; color: scene.style.foreground }
        Rectangle { x: 50; y: 5; width: 4; height: 16; radius: 2; rotation: 16; color: scene.style.accent }
        Rectangle { x: 49; y: 3; width: 9; height: 9; radius: 5; color: scene.style.foreground }
        Rectangle { x: 17; y: 50; width: 14; height: 13; radius: 7; rotation: 12; color: scene.style.accent }
        Rectangle { x: 41; y: 50; width: 14; height: 13; radius: 7; rotation: -12; color: scene.style.accent }
        Rectangle { x: 3; y: 35 - scene.bloom * 5; width: 11; height: 17; radius: 6; rotation: 15 - scene.bloom * 25; color: scene.style.accent }
        Rectangle { x: 58; y: 35 - scene.bloom * 5; width: 11; height: 17; radius: 6; rotation: -15 + scene.bloom * 25; color: scene.style.accent }
        Rectangle {
            x: 8; y: 15; width: 56; height: 43; radius: 16
            color: scene.style.accent
            Rectangle { x: 4; y: 3; width: 48; height: 15; radius: 10; color: scene.style.onAccent; opacity: 0.08 }
            Rectangle { x: 5; y: 18; width: 46; height: 19; radius: 12; color: scene.style.foreground; opacity: 0.05 }
            Item {
                x: 21; y: 4; width: 14; height: 14
                rotation: scene.turn
                Repeater {
                    model: 4
                    Rectangle {
                        required property int index
                        x: (index % 2) * (7 + scene.bloom * 3) - scene.bloom * 1.5
                        y: Math.floor(index / 2) * (7 + scene.bloom * 3) - scene.bloom * 1.5
                        width: 3; height: 3; radius: 2
                        color: scene.style.onAccent
                        opacity: [0.95, 0.55, 0.55, 0.95][index]
                    }
                }
            }
            Repeater {
                model: [16, 35]
                Rectangle { required property int modelData; x: modelData; y: 22; width: 5; height: scene.blinking ? 2 : 7; radius: 3; color: scene.style.onAccent }
            }
            Rectangle { x: 9; y: 31; width: 7; height: 4; radius: 2; color: scene.style.onAccent; opacity: 0.15 }
            Rectangle { x: 40; y: 31; width: 7; height: 4; radius: 2; color: scene.style.onAccent; opacity: 0.15 }
            Rectangle { x: 24; y: 33; width: 9; height: scene.reacting ? 6 : 4; radius: 4; color: scene.style.onAccent }
            Rectangle { x: 23; y: 31; width: 11; height: 3; color: scene.style.accent }
        }
    }
    SequentialAnimation on breath {
        running: scene.motionEnabled; loops: Animation.Infinite
        NumberAnimation { from: 0; to: 1; duration: 1600; easing.type: Easing.InOutSine }
        NumberAnimation { from: 1; to: 0; duration: 1600; easing.type: Easing.InOutSine }
    }
    SequentialAnimation {
        id: flourish
        ParallelAnimation {
            NumberAnimation { target: scene; property: "bloom"; to: 1; duration: 300; easing.type: Easing.OutCubic }
            NumberAnimation { target: scene; property: "turn"; from: 0; to: 45; duration: 300; easing.type: Easing.InOutSine }
        }
        ParallelAnimation {
            NumberAnimation { target: scene; property: "bloom"; to: 0; duration: 450; easing.type: Easing.InOutSine }
            NumberAnimation { target: scene; property: "turn"; to: 90; duration: 450; easing.type: Easing.OutCubic }
        }
        PropertyAction { target: scene; property: "turn"; value: 0 }
    }
}
