pragma ComponentBehavior: Bound
import QtQuick

// Cabecera gris de ventana Breeze; el clic produce un balanceo amortiguado.
Item {
    id: scene
    property var style: ({accent:"#3daee9", background:"#232629", surface:"#31363b", foreground:"#eff0f1", onAccent:"#112935"})
    property bool blinking: false
    property bool greeting: false
    property bool motionEnabled: true
    property real drift: 0
    property real sway: 0
    readonly property color frameInk: style.foreground
    readonly property color cap: Qt.tint(style.surface, Qt.rgba(frameInk.r, frameInk.g, frameInk.b, 0.18))
    readonly property bool reacting: nudge.running
    function activate() { nudge.restart(); }
    onMotionEnabledChanged: if (!motionEnabled) { nudge.stop(); sway = 0; }

    Item {
        x: 32 + scene.sway * 6; y: 15 + scene.drift
        width: 72; height: 68
        rotation: scene.sway * 7
        transformOrigin: Item.Center
        Rectangle { x: 18; y: 6; width: 3; height: 12; radius: 1; color: scene.style.accent }
        Rectangle { x: 15; y: 2; width: 8; height: 8; radius: 2; rotation: 45; color: scene.style.accent; border.color: Qt.lighter(scene.style.accent, 1.4) }
        Rectangle { x: 51; y: 6; width: 3; height: 12; radius: 1; color: scene.style.accent }
        Rectangle { x: 49; y: 2; width: 8; height: 8; radius: 2; rotation: 45; color: scene.style.accent; border.color: Qt.lighter(scene.style.accent, 1.4) }
        Rectangle { x: 17; y: 53; width: 14; height: 9; radius: 3; color: Qt.darker(scene.style.accent, 1.15) }
        Rectangle { x: 41; y: 53; width: 14; height: 9; radius: 3; color: Qt.darker(scene.style.accent, 1.15) }
        Rectangle { x: 3; y: 34; width: 8; height: 15; radius: 4; color: scene.style.accent }
        Rectangle { x: 61; y: 34; width: 8; height: 15; radius: 4; color: scene.style.accent }
        Rectangle {
            x: 8; y: 15; width: 56; height: 43; radius: 8
            border.color: Qt.lighter(scene.style.accent, 1.4)
            gradient: Gradient {
                GradientStop { position: 0; color: Qt.lighter(scene.style.accent, 1.2) }
                GradientStop { position: 1; color: Qt.darker(scene.style.accent, 1.12) }
            }
            // Los tres controles del marco, con la cabecera sobre la cara.
            Rectangle { x: 0; y: 0; width: 56; height: 15; radius: 8; color: scene.cap }
            Rectangle { x: 0; y: 8; width: 56; height: 7; color: scene.cap }
            Rectangle { x: 5; y: 14; width: 46; height: 1; color: scene.style.foreground; opacity: 0.18 }
            Repeater {
                model: 4
                Rectangle { required property int index; x: 6 + (index % 2) * 4; y: 4 + Math.floor(index / 2) * 4; width: 2; height: 2; radius: 1; color: scene.style.foreground; opacity: 0.8 }
            }
            Rectangle { x: 17; y: 6; width: 7; height: 2; radius: 1; color: scene.style.foreground; opacity: 0.5 }
            Rectangle { x: 31; y: 8; width: 5; height: 1; color: scene.style.foreground }
            Rectangle { x: 40; y: 5; width: 5; height: 5; color: "transparent"; border.color: scene.style.foreground; border.width: 1 }
            Rectangle { x: 49; y: 7; width: 5; height: 1; rotation: 45; color: scene.style.foreground }
            Rectangle { x: 49; y: 7; width: 5; height: 1; rotation: -45; color: scene.style.foreground }
            Repeater {
                model: [16, 35]
                Rectangle { required property int modelData; x: modelData; y: 21; width: 5; height: scene.blinking ? 2 : 8; radius: 2; color: scene.style.onAccent }
            }
            Rectangle { x: 23; y: 33; width: 10; height: scene.reacting ? 6 : 4; radius: 3; color: scene.style.onAccent }
            Rectangle { x: 22; y: 31; width: 12; height: 3; color: scene.style.accent }
        }
    }
    SequentialAnimation on drift {
        running: scene.motionEnabled; loops: Animation.Infinite
        NumberAnimation { from: 0; to: -5; duration: 1850; easing.type: Easing.InOutSine }
        NumberAnimation { from: -5; to: 0; duration: 1850; easing.type: Easing.InOutSine }
    }
    SequentialAnimation {
        id: nudge
        NumberAnimation { target: scene; property: "sway"; to: 1; duration: 260; easing.type: Easing.InOutSine }
        NumberAnimation { target: scene; property: "sway"; to: -0.6; duration: 420; easing.type: Easing.InOutSine }
        NumberAnimation { target: scene; property: "sway"; to: 0.25; duration: 360; easing.type: Easing.InOutSine }
        NumberAnimation { target: scene; property: "sway"; to: 0; duration: 300; easing.type: Easing.InOutSine }
    }
}
