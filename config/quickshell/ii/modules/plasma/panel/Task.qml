/*
    SPDX-FileCopyrightText: 2012-2013 Eike Hein <hein@kde.org>
    SPDX-FileCopyrightText: 2024 Nate Graham <nate@kde.org>
    SPDX-License-Identifier: GPL-2.0-or-later
*/
// BWM: reduced icons-only Task.qml, model/actions/drag use the Hyprland adapter.
// The original widgets/tasks frame, prefixes and group indicator are retained.
import QtQuick
import Quickshell
import org.kde.ksvg as KSvg
import org.kde.kirigami as Kirigami
import "TaskPrefixes.js" as Prefixes
Item {
    id: task
    required property var group
    required property var tasksModel
    property string edge:"bottom"
    property bool vertical:edge==="left"||edge==="right"
    readonly property string appId:group?.appId??""
    readonly property var toplevels:group?.toplevels??[]
    readonly property bool isActive:task.toplevels.some(t=>!!t.activated)
    readonly property bool isMinimized:!!(task.toplevels.length>0 && task.toplevels.every(t=>(tasksModel?.minimized(t)??false)))
    readonly property bool attention:task.toplevels.some(t=>!!t.urgent)
    readonly property string basePrefix:!task.toplevels.length ? "" : attention ? "attention" : isMinimized ? "minimized" : isActive ? "focus" : "normal"
    // BWM: icon geometry follows Task.qml/LayoutMetrics, using the active theme's frame.
    readonly property real horizontalMargins:metrics.margins.left+metrics.margins.right
    readonly property real verticalMargins:metrics.margins.top+metrics.margins.bottom
    readonly property real iconExtent:Math.max(16,Math.min(48,task.width-horizontalMargins,task.height-verticalMargins))
    readonly property bool containsMouse: hover.hovered
    signal contextRequested(var button)
    implicitWidth:44; implicitHeight:44
    // BWM: match Plasma's pointer handlers; a child DragHandler steals MouseArea clicks.
    HoverHandler { id:hover }
    TapHandler {
        acceptedButtons:Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
        onTapped:(eventPoint,button)=>{
            if(button===Qt.RightButton) task.contextRequested(task);
            else if(button===Qt.MiddleButton) task.tasksModel.launch(task.appId);
            else task.tasksModel.click(task.group);
        }
    }
    // BWM: a wheel-only area also works inside Quickshell's Flickable host.
    MouseArea {
        anchors.fill:parent; acceptedButtons:Qt.NoButton
        onWheel:event=>{ task.tasksModel.cycle(task.group,event.angleDelta.y>0?-1:1); event.accepted=true; }
    }
    // BWM: stable normal-state metrics, as in upstream main.qml's taskFrame.
    KSvg.FrameSvgItem {
        id:metrics; visible:false; imagePath:"widgets/tasks"
        prefix:Prefixes.taskPrefix("normal",task.edge)
    }
    KSvg.FrameSvgItem {
        id:frame; anchors.fill:parent; imagePath:"widgets/tasks"
        prefix:task.containsMouse ? Prefixes.taskPrefixHovered(task.basePrefix,task.edge) : Prefixes.taskPrefix(task.basePrefix,task.edge)
        visible:task.containsMouse||task.toplevels.length>0
    }
    Item {
        id:visual
        x:0; y:0; width:task.width; height:task.height
        Drag.active:drag.active; Drag.source:task; Drag.keys:["bwm-plasma-task"]
        Drag.hotSpot.x:width/2; Drag.hotSpot.y:height/2
        Kirigami.Icon {
            anchors.centerIn:parent
            width:task.iconExtent; height:width
            active:task.containsMouse
            source:Quickshell.iconPath(task.tasksModel?.entry(task.appId)?.icon || "application-x-executable")
        }
        DragHandler {
            id:drag; target:visual
            onActiveChanged: if(!active) { visual.Drag.drop(); visual.x=0; visual.y=0; }
        }
    }
    DropArea {
        anchors.fill:parent; keys:["bwm-plasma-task"]
        onDropped:drop=>{ if(drop.source && drop.source.appId!==task.appId) task.tasksModel.move(drop.source.appId,task.appId); }
    }
    KSvg.SvgItem {
        width:8; height:8; visible:task.toplevels.length>1
        x: task.edge==="left"?0:task.edge==="right"?task.width-width:(task.width-width)/2
        y: task.edge==="top"?0:task.edge==="bottom"?task.height-height:(task.height-height)/2
        imagePath:"widgets/tasks"; elementId:"group-expander-"+task.edge
    }
    TaskToolTip { taskItem:task; group:task.group; tasksModel:task.tasksModel; edge:task.edge }
}
