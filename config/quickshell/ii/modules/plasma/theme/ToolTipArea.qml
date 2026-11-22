// BWM: Quickshell PopupWindow tooltip styled like Plasma DefaultToolTip + solid/dialogs/background,
// avoiding PlasmaCore.ToolTipArea / ToolTipDialog (which maps unpositioned at screen center
// on Hyprland without plasma-shell and disrupts panel clicks).
pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import Quickshell
import org.kde.kirigami as Kirigami
import org.kde.ksvg as KSvg
import org.kde.plasma.components as PC3

Item {
    id: root

    property string mainText: ""
    property string subText: ""
    property string icon: ""
    property string image: ""
    property int textFormat: Text.AutoText
    property int timeout: -1
    property bool active: true
    property bool interactive: false
    property string edge: ""
    property int location: 0
    property int preferredTextWidth: Kirigami.Units.gridUnit * 20

    readonly property bool containsMouse: hoverHandler.hovered
    readonly property bool toolTipVisible: tooltipPopup.visible
    readonly property bool hasContent: mainText !== "" || subText !== ""
    readonly property string resolvedEdge: {
        if (edge !== "")
            return edge;
        const win = root.QsWindow?.window;
        const a = win ? win.anchors : null;
        if (!a || typeof a.top !== "boolean")
            return "bottom";
        if (a.top && !a.bottom)
            return "top";
        if (a.left && !a.right)
            return "left";
        if (a.right && !a.left)
            return "right";
        return "bottom";
    }

    signal aboutToShow()

    function showToolTip() {
        if (!active || !hasContent || !visible || !root.QsWindow?.window)
            return;
        aboutToShow();
        tooltipPopup.visible = true;
    }

    function hideToolTip() {
        hideImmediately();
    }

    function hideImmediately() {
        showTimer.stop();
        tooltipPopup.visible = false;
    }

    onActiveChanged: if (!active) hideImmediately()
    onVisibleChanged: if (!visible) hideImmediately()
    onHasContentChanged: if (!hasContent) hideImmediately()
    Component.onDestruction: hideImmediately()

    HoverHandler {
        id: hoverHandler
        acceptedButtons: Qt.NoButton
        enabled: !!(root.visible && root.active)
        onHoveredChanged: {
            if (hoverHandler.hovered) {
                if (root.active && root.hasContent)
                    showTimer.restart();
            } else {
                root.hideImmediately();
            }
        }
    }

    Timer {
        id: showTimer
        interval: Kirigami.Units.toolTipDelay
        onTriggered: root.showToolTip()
    }

    PopupWindow {
        id: tooltipPopup
        visible: false
        color: "transparent"

        anchor {
            item: root
            edges: root.resolvedEdge === "bottom" ? Edges.Top
                 : root.resolvedEdge === "top" ? Edges.Bottom
                 : root.resolvedEdge === "left" ? Edges.Right : Edges.Left
            gravity: anchor.edges
        }

        implicitWidth: Math.max(1, bg.margins.left + bg.margins.right + mainLayout.implicitWidth + Kirigami.Units.smallSpacing * 2)
        implicitHeight: Math.max(1, bg.margins.top + bg.margins.bottom + mainLayout.implicitHeight + Kirigami.Units.smallSpacing * 2)

        // ToolTipDialog draws «widgets/tooltip»; with KWin's blur, its translucent variant (the
        // panel layer rule blurs its popups). Without blur, the previous solid dialog.
        BlurPath { id: tooltipPath; path: "widgets/tooltip"; withoutBlur: "solid/dialogs/background" }
        KSvg.FrameSvgItem {
            id: bg
            anchors.fill: parent
            imagePath: tooltipPath.resolved
            prefix: ""
        }

        Item {
            anchors.fill: parent
            anchors.leftMargin: bg.margins.left + Kirigami.Units.smallSpacing
            anchors.rightMargin: bg.margins.right + Kirigami.Units.smallSpacing
            anchors.topMargin: bg.margins.top + Kirigami.Units.smallSpacing
            anchors.bottomMargin: bg.margins.bottom + Kirigami.Units.smallSpacing

            Kirigami.Theme.colorSet: Kirigami.Theme.Window
            Kirigami.Theme.inherit: false

            RowLayout {
                id: mainLayout
                anchors.centerIn: parent
                spacing: Kirigami.Units.largeSpacing

                Image {
                    source: root.image
                    visible: root.image !== ""
                    Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
                }

                Kirigami.Icon {
                    animated: false
                    source: root.icon
                    Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
                    visible: root.icon !== "" && root.image === "" && valid
                    Layout.preferredWidth: Kirigami.Units.iconSizes.medium
                    Layout.preferredHeight: Kirigami.Units.iconSizes.medium
                }

                ColumnLayout {
                    Layout.maximumWidth: root.preferredTextWidth
                    spacing: 0

                    Kirigami.Heading {
                        level: 3
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                        wrapMode: Text.Wrap
                        text: root.mainText
                        textFormat: Text.PlainText
                        visible: text !== ""
                    }

                    PC3.Label {
                        Layout.fillWidth: true
                        wrapMode: Text.Wrap
                        text: root.subText
                        textFormat: root.textFormat
                        opacity: 0.75
                        visible: text !== ""
                        maximumLineCount: 8
                    }
                }
            }
        }
    }
}
