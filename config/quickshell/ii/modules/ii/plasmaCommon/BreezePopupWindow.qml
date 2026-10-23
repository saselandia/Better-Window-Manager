import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland

/**
 * Full-screen transparent layer with a Plasma applet popup card anchored above
 * a taskbar button. Clicking outside or pressing Escape emits closeRequested().
 * Children go inside the card (filled with a ColumnLayout by the caller).
 */
PanelWindow {
    id: win
    required property bool opened
    property real anchorX: -1           // taskbar button center (window coords), -1 = right edge
    property string screenName: ""
    property string namespace: "quickshell:plasmaApplet"
    property int popupWidth: 380
    property int popupHeight: 440
    property int bottomMargin: 46       // Plasma panel height + gap
    default property alias content: card.data
    signal closeRequested()

    visible: opened || card.opacity > 0
    screen: Quickshell.screens.find(s => s.name === win.screenName) ?? Quickshell.screens[0]
    color: "transparent"
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: win.namespace
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: win.opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    anchors { top: true; bottom: true; left: true; right: true }

    // Click-outside closes (also catches the taskbar button -> natural toggle)
    MouseArea {
        anchors.fill: parent
        onClicked: win.closeRequested()
    }

    Item {
        anchors.fill: parent
        focus: win.opened
        Keys.onEscapePressed: win.closeRequested()
    }

    Rectangle {
        id: card
        width: win.popupWidth
        height: win.popupHeight
        // Centered over the taskbar button, clamped to the screen edges
        x: {
            const centered = win.anchorX >= 0 ? win.anchorX - width / 2 : win.width - width - 6;
            return Math.max(6, Math.min(win.width - width - 6, centered));
        }
        y: win.height - height - win.bottomMargin + (win.opened ? 0 : 12)
        opacity: win.opened ? 1 : 0
        color: Breeze.panelBg
        border.width: 1
        border.color: Breeze.border
        radius: 7
        clip: true

        Behavior on opacity { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
        Behavior on y { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }

        MouseArea { anchors.fill: parent } // Block backdrop click-through
    }
}
