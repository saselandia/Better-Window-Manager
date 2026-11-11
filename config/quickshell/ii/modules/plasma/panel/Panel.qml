// BWM: Plasma PanelView host implemented with layer-shell instead of PlasmaShell/KWin.
import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Io
import qs
import qs.services
import qs.modules.common
import org.kde.kirigami as Kirigami
import qs.modules.plasma.menus
import qs.modules.plasma.tray as PlasmaTray
import "PanelLogic.js" as Logic
Scope {
    id:root
    IpcHandler {
        target:"plasmaPanel"
        function inspect(): string { return JSON.stringify(PanelState.panels); }
        function edit(screenName: string): void { PanelState.setEditing(screenName,true); }
    }
    Variants {
        model:Quickshell.screens.filter(s=>!Config.options.bar.screenList.length||Config.options.bar.screenList.includes(s.name))
        delegate:PanelWindow {
            id:win
            required property var modelData
            screen:modelData
            readonly property var config:Config.options.bar.plasma
            property bool revealed:false
            readonly property bool editing:PanelState.editing[screen.name]??false
            readonly property var monitor:HyprlandData.monitors.find(m=>m.name===screen.name)
            readonly property var base:Logic.geometry(screen.width,screen.height,config,Config.options.bar.bottom,false,true)
            readonly property bool touching:Logic.touching(monitor,HyprlandData.windowList,base)
            readonly property var geo:Logic.geometry(screen.width,screen.height,config,Config.options.bar.bottom,touching,revealed||editing||(PlasmaTray.TrayState.expanded&&PlasmaTray.TrayState.screenName===screen.name))
            readonly property bool vertical:geo.vertical
            readonly property real shadowPad:Math.max(8,background.shadowMargins.left,background.shadowMargins.right,background.shadowMargins.top,background.shadowMargins.bottom)
            color:"transparent"
            visible:GlobalStates.barOpen&&!GlobalStates.screenLocked
            WlrLayershell.namespace:"quickshell:plasmaPanel"
            WlrLayershell.layer:WlrLayer.Top
            exclusionMode:ExclusionMode.Ignore
            exclusiveZone:geo.reserve
            implicitWidth:vertical?geo.thickness+geo.gap+shadowPad:screen.width
            implicitHeight:vertical?screen.height:geo.thickness+geo.gap+shadowPad
            anchors.top:geo.edge==="top"||vertical
            anchors.bottom:geo.edge==="bottom"||vertical
            anchors.left:geo.edge==="left"||!vertical
            anchors.right:geo.edge==="right"||!vertical
            mask:Region { item:hitArea }
            Component.onCompleted: { PanelState.update(screen.name,geo); HyprlandData.updateAll(); }
            Component.onDestruction:PanelState.remove(screen.name)
            onGeoChanged:PanelState.update(screen.name,geo)
            MouseArea {
                id:hitArea
                x:win.vertical ? (win.geo.edge==="left"?0:win.width-width) : win.geo.start
                y:win.vertical ? win.geo.start : (win.geo.edge==="top"?0:win.height-height)
                width:win.vertical?(win.geo.hidden?2:win.width):win.geo.length
                height:win.vertical?win.geo.length:(win.geo.hidden?2:win.height)
                hoverEnabled:true; acceptedButtons:Qt.RightButton
                onEntered: { closeDelay.stop(); win.revealed=true; }
                onExited:closeDelay.restart()
                // F9: menú del panel de Plasma (Añadir elementos, modo de edición)
                onClicked:mouse=>PlasmaMenus.openLocal("panel",win.screen.name,
                    mouse.x+hitArea.x+(win.geo.edge==="right"?win.screen.width-win.width:0),
                    mouse.y+hitArea.y+(win.geo.edge==="bottom"?win.screen.height-win.height:0),
                    {panelScreen:win.screen.name,editing:win.editing,edge:win.geo.edge})
            }
            Connections {
                target:PlasmaMenus
                function onEditModeRequested(name,value) { if(name===win.screen.name) PanelState.setEditing(name,value); }
            }
            Timer { id:closeDelay; interval:500; onTriggered:if(!panelHover.hovered) win.revealed=false }
            Item {
                id:panel
                Kirigami.Theme.colorSet:Kirigami.Theme.Complementary
                Kirigami.Theme.inherit:false
                visible:!win.geo.hidden
                x:win.vertical?(win.geo.edge==="left"?win.geo.gap:win.shadowPad):win.geo.start
                y:win.vertical?win.geo.start:(win.geo.edge==="top"?win.geo.gap:win.shadowPad)
                width:win.geo.width; height:win.geo.height
                HoverHandler {
                    id:panelHover
                    onHoveredChanged: {
                        if(hovered) { closeDelay.stop(); win.revealed=true; }
                        else closeDelay.restart();
                    }
                }
                PanelBackground {
                    id:background; anchors.fill:parent
                    edge:win.geo.edge; floating:win.geo.gap>0; touchingWindow:win.touching
                    touchesLeft:win.geo.x<=0;touchesTop:win.geo.y<=0
                    touchesRight:win.geo.x+win.geo.width>=win.screen.width
                    touchesBottom:win.geo.y+win.geo.height>=win.screen.height
                    opacityMode:win.config.style==="floating"?"adaptive":win.config.style
                }
                PanelContent {
                    anchors.fill:parent
                    anchors.leftMargin:Math.min(8,background.frameMargins.left)
                    anchors.rightMargin:Math.min(8,background.frameMargins.right)
                    anchors.topMargin:Math.min(6,background.frameMargins.top)
                    anchors.bottomMargin:Math.min(6,background.frameMargins.bottom)
                    panelWindow:win; edge:win.geo.edge
                }
            }
        }
    }
}
