/*
    SPDX-FileCopyrightText: 2012 Marco Martin <mart@kde.org>
    SPDX-License-Identifier: GPL-2.0-or-later
*/
// BWM: extracted from plasma-desktop v6.7.5 desktoppackage/contents/views/Panel.qml.
// PanelView/containment are properties supplied by our layer-shell host.
import QtQuick
import org.kde.ksvg as KSvg
import org.kde.kirigami as Kirigami
Item {
    id: root
    property string edge: "bottom"
    property bool floating: false
    property bool touchingWindow: false
    property string opacityMode: "adaptive"
    readonly property string direction: ({top:"north",bottom:"south",left:"west",right:"east"})[edge]
    property real panelOpacity: opacityMode === "opaque" || (opacityMode === "adaptive" && touchingWindow) ? 1 : 0
    readonly property var frameMargins: translucentItem.margins
    readonly property var shadowMargins: shadow.margins
    property bool touchesLeft:false
    property bool touchesRight:false
    property bool touchesTop:false
    property bool touchesBottom:false
    readonly property int borderMask: {
        let mask=KSvg.FrameSvg.AllBorders;
        if(!floating) mask &= ~({top:KSvg.FrameSvg.TopBorder,bottom:KSvg.FrameSvg.BottomBorder,left:KSvg.FrameSvg.LeftBorder,right:KSvg.FrameSvg.RightBorder})[edge];
        if(touchesLeft) mask &= ~KSvg.FrameSvg.LeftBorder;
        if(touchesRight) mask &= ~KSvg.FrameSvg.RightBorder;
        if(touchesTop) mask &= ~KSvg.FrameSvg.TopBorder;
        if(touchesBottom) mask &= ~KSvg.FrameSvg.BottomBorder;
        return mask;
    }
    Behavior on panelOpacity { NumberAnimation { duration:Kirigami.Units.longDuration; easing.type:Easing.OutCubic } }
    // BWM: PanelShadows' SVG pieces are composed here, rather than through KWin's shadow protocol.
    KSvg.FrameSvgItem {
        id: shadow
        x:-margins.left; y:-margins.top
        width:root.width+margins.left+margins.right; height:root.height+margins.top+margins.bottom
        imagePath:"widgets/panel-background"; prefix:"shadow"; enabledBorders:root.borderMask
    }
    KSvg.FrameSvgItem {
        id: translucentItem
        anchors.fill:parent; imagePath:"widgets/panel-background"
        prefix:[root.direction,""]; enabledBorders:root.borderMask
    }
    KSvg.FrameSvgItem {
        anchors.fill:parent; imagePath:"solid/widgets/panel-background"
        prefix:[root.direction,""]; enabledBorders:root.borderMask
        opacity:root.panelOpacity
    }
}
