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
MouseArea {
    id: task
    required property var group
    required property var tasksModel
    property string edge:"bottom"
    property bool vertical:edge==="left"||edge==="right"
    readonly property string appId:group?.appId??""
    readonly property var toplevels:group?.toplevels??[]
    readonly property bool isActive:task.toplevels.some(t=>t.activated)
    readonly property bool isMinimized:task.toplevels.length>0 && task.toplevels.every(t=>(tasksModel?.minimized(t)??false))
    readonly property bool attention:task.toplevels.some(t=>t.urgent)
    readonly property string basePrefix:!task.toplevels.length ? "" : attention ? "attention" : isMinimized ? "minimized" : isActive ? "focus" : "normal"
    signal contextRequested(var button)
    implicitWidth:44; implicitHeight:44
    hoverEnabled:true; acceptedButtons:Qt.LeftButton|Qt.RightButton|Qt.MiddleButton
    onClicked:mouse=>{
        if(mouse.button===Qt.RightButton) contextRequested(task);
        else if(mouse.button===Qt.MiddleButton) tasksModel.launch(appId);
        else tasksModel.click(group);
    }
    onWheel:wheel=>{ tasksModel.cycle(group,wheel.angleDelta.y>0?-1:1); wheel.accepted=true; }
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
            width:Math.min(32,task.width-8); height:width
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
