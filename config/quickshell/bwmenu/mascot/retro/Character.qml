pragma ComponentBehavior: Bound
import QtQuick

// Omarchy: píxeles y pocos colores del tema, patinete y estela hacia atrás.
Item {
    id: scene
    property var style: ({accent:"#81a1c1", background:"#2e3440", surface:"#3b4252", foreground:"#eceff4", onAccent:"#15191e"})
    property bool blinking: false
    property bool greeting: false
    property bool motionEnabled: true
    property real gait: 0
    property real travel: 0
    property real charge: 0
    readonly property color body: style.accent
    readonly property color ink: style.onAccent
    readonly property bool reacting: push.running
    function activate() { push.restart(); }
    onMotionEnabledChanged: if (!motionEnabled) { push.stop(); charge = 0; }

    // Sólo aire en movimiento: sin paisaje, rectángulo de fondo ni suelo.
    Repeater {
        model: 4
        Rectangle {
            required property int index
            readonly property real progress: (index / 4 + scene.travel) % 1
            x: 21 - progress * 23
            y: 44 + index * 8
            width: 7 + progress * 12; height: 2
            color: index % 2 ? scene.style.foreground : scene.style.accent
            opacity: (1 - progress) * (0.35 + scene.charge * 0.3)
        }
    }
    Item {
        width: 108; height: 94
        x: 14
        y: 5 + Math.round(Math.sin(scene.gait))
        rotation: 3 + Math.sin(scene.gait) * 0.6 + scene.charge * 2
        transformOrigin: Item.Bottom
        Repeater {
            model: [19, 80]
            Rectangle {
                required property int modelData
                x: modelData; y: 79; width: 9; height: 9
                color: scene.style.surface
                border.color: scene.style.accent; border.width: 2
                Rectangle { anchors.centerIn: parent; width: 1; height: 5; rotation: scene.travel * 360; color: scene.style.foreground }
            }
        }
        Rectangle { x: 5; y: 73; width: 96; height: 6; color: scene.style.accent }
        Rectangle { x: 9; y: 73; width: 88; height: 2; color: scene.style.foreground; opacity: 0.7 }
        Rectangle { x: 92; y: 38; width: 3; height: 35; color: scene.style.accent }
        Rectangle { x: 83; y: 35; width: 17; height: 4; color: scene.style.foreground }
        Item {
            x: 18; y: 9; width: 72; height: 68
            Rectangle { x: 17; y: 4; width: 4; height: 12; color: scene.body }
            Rectangle { x: 13; y: 2; width: 8; height: 4; color: scene.style.foreground }
            Rectangle { x: 51; y: 4; width: 4; height: 12; color: scene.body }
            Rectangle { x: 51; y: 2; width: 8; height: 4; color: scene.style.foreground }
            Rectangle { x: 12; y: 16; width: 48; height: 40; color: scene.body }
            Rectangle { x: 8; y: 20; width: 56; height: 32; color: scene.body }
            Rectangle { x: 3; y: 34; width: 7; height: 9; color: scene.body }
            Rectangle { x: 62; y: 28; width: 12; height: 7; color: scene.body }
            Rectangle { x: 18; y: 56; width: 12; height: 6; color: scene.body }
            Rectangle { x: 42; y: 56; width: 12; height: 6; color: scene.body }
            // Las mismas cuatro marcas que las otras variantes, en píxeles.
            Repeater {
                model: 4
                Rectangle { required property int index; x: 31 + (index % 2) * 4; y: 20 + Math.floor(index / 2) * 4; width: 2; height: 2; color: scene.ink; opacity: 0.65 }
            }
            Rectangle { x: 10; y: 30; width: 52; height: 3; color: scene.ink }
            Repeater {
                model: [15, 39]
                Item {
                    required property int modelData
                    x: modelData; y: 30
                    Rectangle { width: 18; height: scene.blinking ? 7 : 12; color: scene.ink }
                    Rectangle { x: 3; y: 3; width: 4; height: 2; color: scene.style.accent }
                    Rectangle { x: 7; y: 5; width: 4; height: 2; color: scene.style.foreground; opacity: 0.75 }
                }
            }
            Rectangle { x: 29; y: 48; width: 14; height: 3; color: scene.ink }
            Rectangle { x: 26; y: 45; width: 3; height: 3; color: scene.ink }
            Rectangle { x: 43; y: 45; width: 3; height: 3; color: scene.ink }
        }
    }
    NumberAnimation on gait { running: scene.motionEnabled; from: 0; to: 6.283185; duration: 1450; loops: Animation.Infinite }
    NumberAnimation on travel { running: scene.motionEnabled; from: 0; to: 1; duration: 850; loops: Animation.Infinite }
    SequentialAnimation {
        id: push
        NumberAnimation { target: scene; property: "charge"; to: 1; duration: 200; easing.type: Easing.OutCubic }
        NumberAnimation { target: scene; property: "charge"; to: 0; duration: 650; easing.type: Easing.InOutSine }
    }
}
