/* SPDX-FileCopyrightText: 2016 Marco Martin <mart@kde.org>
   SPDX-FileCopyrightText: 2020 Nate Graham <nate@kde.org>
   SPDX-License-Identifier: LGPL-2.0-or-later */
// BWM: ExpandedRepresentation header/hidden grid with Quickshell PopupWindow and applet loaders.
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import org.kde.ksvg as KSvg
import org.kde.kirigami as Kirigami
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PC3
import org.kde.plasma.extras as PlasmaExtras
import qs.modules.plasma.panel
import qs.modules.plasma.applets as Applets
import "TrayLogic.js" as Logic
PopupWindow {
    id:trayWindow
    readonly property alias appletItem:page.item
    readonly property alias renderItem:surface
    required property var tray
    required property var anchorItem
    readonly property string edge:PanelState.edgeFor(anchorItem.QsWindow.window?.screen?.name||"")
    visible:tray.expanded
    onVisibleChanged:if(visible)Qt.callLater(()=>surface.forceActiveFocus())
    color:"transparent";implicitWidth:tray.activeApplet==="calendar"?440:460;implicitHeight:540
    // BWM: PlasmaQuick::Dialog docks against the panel edge, not against the icon (which sits inside
    // the containment margins): the anchor rect spans the panel thickness. Floating panels keep
    // CompactApplet's largeSpacing margin.
    readonly property string screenName:anchorItem.QsWindow.window?.screen?.name||""
    readonly property bool docked:PanelState.gapFor(screenName)<=0
    readonly property var container:{ let item=anchorItem; while(item&&item.parent){ item=item.parent; if(item.isAppletContainer)return item; } return null; }
    readonly property bool horizontalPanel:edge==="top"||edge==="bottom"
    readonly property rect panelSpan:{
        // depend on the geometry that moves the icon inside the panel
        void(anchorItem.x+anchorItem.y+anchorItem.width+anchorItem.height+(container?container.width+container.height:0)+visible);
        if(!container)return Qt.rect(0,0,anchorItem.width,anchorItem.height);
        const p=anchorItem.mapToItem(container,0,0);
        const margin=docked?0:Kirigami.Units.largeSpacing;
        if(horizontalPanel){
            const top=-(p.y+container.getMargins("top",true))-margin;
            const bottom=container.height-p.y+container.getMargins("bottom",true)+margin;
            return Qt.rect(0,top,anchorItem.width,bottom-top);
        }
        const left=-(p.x+container.getMargins("left",true))-margin;
        const right=container.width-p.x+container.getMargins("right",true)+margin;
        return Qt.rect(left,0,right-left,anchorItem.height);
    }
    anchor.item:anchorItem
    anchor.rect.x:panelSpan.x;anchor.rect.y:panelSpan.y
    anchor.rect.width:panelSpan.width;anchor.rect.height:panelSpan.height
    anchor.edges:edge==="bottom"?Edges.Top:edge==="top"?Edges.Bottom:edge==="left"?Edges.Right:Edges.Left
    anchor.gravity:anchor.edges
    HyprlandFocusGrab { active:trayWindow.visible;windows:[trayWindow, trayWindow.anchorItem.QsWindow.window].filter(w=>w);onCleared:TrayState.close() }
    Item {
    id:surface
    anchors.fill:parent
    focus:true
    Keys.onEscapePressed:event=>{TrayState.close();event.accepted=true;}
    KSvg.FrameSvgItem {
        anchors.fill:parent;imagePath:"solid/dialogs/background";prefix:""
        // Docked to the panel: no border on that side, as PlasmaQuick::Dialog
        enabledBorders:!trayWindow.docked?KSvg.FrameSvgItem.AllBorders
            :({bottom:KSvg.FrameSvgItem.AllBorders&~KSvg.FrameSvgItem.BottomBorder,
               top:KSvg.FrameSvgItem.AllBorders&~KSvg.FrameSvgItem.TopBorder,
               left:KSvg.FrameSvgItem.AllBorders&~KSvg.FrameSvgItem.LeftBorder,
               right:KSvg.FrameSvgItem.AllBorders&~KSvg.FrameSvgItem.RightBorder})[trayWindow.edge]??KSvg.FrameSvgItem.AllBorders
    }
    // CompactApplet.qml: 1 px «widgets/line» between a docked popup and the panel, drawn on top
    KSvg.SvgItem {
        visible:trayWindow.docked;z:999
        imagePath:"widgets/line";elementId:trayWindow.horizontalPanel?"horizontal-line":"vertical-line"
        x:trayWindow.edge==="right"?parent.width-1:0;y:trayWindow.edge==="bottom"?parent.height-1:0
        width:trayWindow.horizontalPanel?parent.width:1;height:trayWindow.horizontalPanel?1:parent.height
    }
    ColumnLayout {
        anchors.fill:parent;anchors.margins:10;spacing:6
        RowLayout {
            PC3.ToolButton { icon.name:"go-previous";visible:trayWindow.tray.activeApplet!==""||trayWindow.tray.configuring;onClicked:{TrayState.applet="";trayWindow.tray.configuring=false} }
            Kirigami.Heading { Layout.fillWidth:true;level:2;text:trayWindow.tray.configuring?qsTr("System Tray Settings"):trayWindow.tray.applets.find(a=>a.id===trayWindow.tray.activeApplet)?.title||(trayWindow.tray.activeApplet==="calendar"?qsTr("Calendar"):qsTr("Status and Notifications"));elide:Text.ElideRight }
            PC3.ToolButton { visible:trayWindow.tray.configurable??true;icon.name:"configure";text:qsTr("Configure");onClicked:trayWindow.tray.configuring=!trayWindow.tray.configuring }
            PC3.ToolButton { icon.name:"window-close";onClicked:TrayState.close() }
        }
        PC3.ScrollView {
            visible:trayWindow.tray.configuring;Layout.fillWidth:true;Layout.fillHeight:true
            ColumnLayout {
                width:parent.width
                Repeater {
                    model:trayWindow.tray.items.map(i=>({id:i.id,title:i.title||i.id})).concat(trayWindow.tray.applets.map(a=>({id:"applet:"+a.id,title:a.title})))
                    RowLayout {
                        required property var modelData
                        Layout.fillWidth:true
                        PC3.Label { Layout.fillWidth:true;text:modelData.title;elide:Text.ElideRight;textFormat:Text.PlainText }
                        PC3.ComboBox {
                            model:[qsTr("Automatic"),qsTr("Always shown"),qsTr("Always hidden")]
                            currentIndex:["auto","shown","hidden"].indexOf(Logic.mode(trayWindow.tray.settings,parent.modelData.id))
                            enabled:!trayWindow.tray.readOnly
                            onActivated:trayWindow.tray.setMode(parent.modelData.id,["auto","shown","hidden"][currentIndex])
                        }
                    }
                }
            }
        }
        PC3.ScrollView {
            visible:!trayWindow.tray.configuring&&trayWindow.tray.activeApplet==="";Layout.fillWidth:true;Layout.fillHeight:true
            GridLayout {
                width:parent.width;columns:2;rowSpacing:8;columnSpacing:8
                Repeater {
                    model:trayWindow.tray.hiddenItems
                    StatusNotifierItem {
                        required property var modelData
                        required index
                        item:modelData;model:({});tray:trayWindow.tray
                        effectiveStatus:PlasmaCore.Types.PassiveStatus
                        Layout.fillWidth:true;Layout.preferredHeight:64
                    }
                }
                Repeater {
                    model:trayWindow.tray.hiddenApplets
                    PC3.ToolButton { required property var modelData;Layout.fillWidth:true;Layout.preferredHeight:64;icon.name:modelData.icon;text:modelData.title;display:PC3.AbstractButton.TextBesideIcon;onClicked:trayWindow.tray.openApplet(modelData.id) }
                }
                PC3.Label { visible:(trayWindow.tray.hiddenItems?.length??0)+(trayWindow.tray.hiddenApplets?.length??0)===0;text:qsTr("No hidden items") }
            }
        }
        Loader {
            id:page
            Layout.fillWidth:true;Layout.fillHeight:true
            active:trayWindow.visible&&!trayWindow.tray.configuring&&trayWindow.tray.activeApplet!==""
            // Source is skin-local, no real applet/service exists until its page is opened.
            readonly property string appletSource:active?Qt.resolvedUrl("../applets/"+({audio:"audio/Audio",network:"network/Network",media:"media/Media",calendar:"calendar/Calendar",bluetooth:"Bluetooth",notifications:"Notifications",clipboard:"Clipboard",power:"Power"})[trayWindow.tray.activeApplet]+"Applet.qml"):""
            onAppletSourceChanged: { if(appletSource)setSource(appletSource,trayWindow.tray.appletProperties);else source=""; }
        }
    }
    }
    Shortcut { sequence:"Escape";context:Qt.ApplicationShortcut;enabled:trayWindow.visible;onActivated:TrayState.close() }
}
