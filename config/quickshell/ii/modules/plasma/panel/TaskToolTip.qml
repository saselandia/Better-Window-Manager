// BWM: Plasma ToolTipDelegate's window list, using Quickshell ScreencopyView (no KWin protocol).
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Widgets
import Quickshell.Wayland
import org.kde.ksvg as KSvg
import org.kde.plasma.components as PC3
PopupWindow {
    id:popup
    required property var taskItem
    required property var group
    required property var tasksModel
    property string edge:"bottom"
    property bool opened:false
    visible:opened && (group?.toplevels.length??0)>0
    color:"transparent"
    anchor {
        item:popup.taskItem
        edges:popup.edge==="bottom"?Edges.Top:popup.edge==="top"?Edges.Bottom:popup.edge==="left"?Edges.Right:Edges.Left
        gravity:popup.edge==="bottom"?Edges.Top:popup.edge==="top"?Edges.Bottom:popup.edge==="left"?Edges.Right:Edges.Left
    }
    implicitWidth:row.implicitWidth+16; implicitHeight:row.implicitHeight+16
    Connections {
        target:popup.taskItem
        function onContainsMouseChanged() {
            if(popup.taskItem.containsMouse) { closeTimer.stop(); openTimer.restart(); }
            else { openTimer.stop(); closeTimer.restart(); }
        }
    }
    Timer { id:openTimer; interval:400; onTriggered:popup.opened=(popup.group?.toplevels.length??0)>0 }
    Timer { id:closeTimer; interval:400; onTriggered:if(!hover.hovered) popup.opened=false }
    HoverHandler { id:hover; onHoveredChanged:if(!hovered) closeTimer.restart() }
    KSvg.FrameSvgItem { anchors.fill:parent; imagePath:"dialogs/background" }
    RowLayout {
        id:row; anchors.centerIn:parent; spacing:8
        Repeater {
            model:popup.group?.toplevels??[]
            delegate:MouseArea {
                id:card
                required property var modelData
                implicitWidth:190; implicitHeight:140
                onClicked: { popup.tasksModel.activate(modelData); popup.opened=false; }
                ColumnLayout {
                    anchors.fill:parent
                    PC3.Label { Layout.maximumWidth:180; text:card.modelData.title; elide:Text.ElideRight }
                    ScreencopyView { Layout.fillWidth:true; Layout.fillHeight:true; captureSource:card.modelData; live:popup.visible }
                }
            }
        }
    }
}
