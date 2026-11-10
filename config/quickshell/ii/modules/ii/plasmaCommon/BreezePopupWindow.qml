import qs.modules.plasma.panel
import qs
import qs.modules.common
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
    // Docked panel: flush with it. Floating panel: float with the same gap as the panel
    readonly property int edgeGap: PlasmaPanelState.gapFor(win.screen?.name ?? "")
    property int bottomMargin: PlasmaPanelState.panelEdgeOffset(win.screen?.name ?? "")
    // Leave the taskbar uncovered so its buttons keep receiving clicks while open
    property bool passBarClicks: false
    default property alias content: card.data
    signal closeRequested()

    // Plasma panel edge: popups slide out of it (bottom by default, top if the bar is on top)
    readonly property string edge: PanelState.edgeFor(win.screen?.name ?? "")
    readonly property bool atTop: edge === "top"
    readonly property bool vertical: edge === "left" || edge === "right"
    // Opening/closing state; the slide is a transform offset (not the card's y), so the
    // layer surface being resized after it maps can never make the card travel across the screen
    readonly property bool shown: opened

    visible: opened || card.opacity > 0
    screen: Quickshell.screens.find(s => s.name === win.screenName) ?? Quickshell.screens[0]
    color: "transparent"
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: win.namespace
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: win.opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    anchors { top: true; bottom: true; left: true; right: true }
    margins.bottom: passBarClicks && edge === "bottom" ? PlasmaPanelState.panelEdgeOffset(win.screen?.name ?? "") : 0
    margins.top: passBarClicks && edge === "top" ? PlasmaPanelState.panelEdgeOffset(win.screen?.name ?? "") : 0

    margins.left: passBarClicks && edge === "left" ? PanelState.distanceFor(win.screen?.name ?? "") : 0
    margins.right: passBarClicks && edge === "right" ? PanelState.distanceFor(win.screen?.name ?? "") : 0

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
            if (win.edge === "left") return win.bottomMargin;
            if (win.edge === "right") return win.width - width - win.bottomMargin;
            const centered = win.anchorX >= 0 ? win.anchorX - width / 2 : win.width - width;
            return Math.max(win.edgeGap, Math.min(win.width - width - win.edgeGap, centered));
        }
        y: {
            if (!win.vertical) return win.atTop ? win.bottomMargin : win.height-height-win.bottomMargin;
            const centered=GlobalStates.plasmaPopupAnchorY>=0 ? GlobalStates.plasmaPopupAnchorY-height/2 : win.height-height;
            return Math.max(win.edgeGap,Math.min(win.height-height-win.edgeGap,centered));
        }
        opacity: win.shown ? 1 : 0
        property real slide: win.shown ? 0 : (win.atTop ? -12 : 12)
        transform: Translate { y: card.slide }
        color: Breeze.panelBg
        border.width: 1
        border.color: Breeze.border
        // Docked to the panel: only the top corners are rounded
        radius: win.edgeGap > 0 ? 7 : 0
        topLeftRadius: win.atTop && win.edgeGap === 0 ? 0 : 7
        topRightRadius: win.atTop && win.edgeGap === 0 ? 0 : 7
        bottomLeftRadius: !win.atTop && win.edgeGap === 0 ? 0 : 7
        bottomRightRadius: !win.atTop && win.edgeGap === 0 ? 0 : 7
        clip: true

        Behavior on opacity { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
        Behavior on slide { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }

        MouseArea { anchors.fill: parent } // Block backdrop click-through
    }
}
