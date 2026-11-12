/* SPDX-FileCopyrightText: 2016 Marco Martin <mart@kde.org>
   SPDX-FileCopyrightText: 2020 Konrad Materka <materka@gmail.com>
   SPDX-FileCopyrightText: 2020 Nate Graham <nate@kde.org>
   SPDX-License-Identifier: LGPL-2.0-or-later */
// BWM: systemtray containment/expanded header and hidden grid, with explicit applet adapters.
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Services.SystemTray as Sni
import org.kde.plasma.components as PC3
import org.kde.plasma.core as PlasmaCore
import org.kde.kirigami as Kirigami
import qs.modules.common
import qs.services
import "TrayLogic.js" as Logic
Item {
    id:root
    property bool vertical:false
    property string edge:"bottom"
    // BWM: systemtray/main.qml grid formula, native Appearance defaults.
    property var appearance:Config.options.bar.plasma.systemTray ?? ({})
    readonly property int smallIconSize:Kirigami.Units.iconSizes.smallMedium
    readonly property bool autoSize:appearance.scaleIconsToFit ?? false
    readonly property int gridThickness:vertical?width:height
    readonly property int lanes:autoSize?1:Math.max(1,Math.min(entries.length,Math.floor(gridThickness/(smallIconSize+Kirigami.Units.smallSpacing))))
    readonly property int itemSize:autoSize?Kirigami.Units.iconSizes.roundedIconSize(Math.min(gridThickness/lanes,Kirigami.Units.iconSizes.enormous)):smallIconSize
    readonly property int cellSpacing:Kirigami.Units.smallSpacing*(appearance.iconSpacing ?? 2)
    readonly property int cellLength:itemSize+(gridThickness<itemSize?0:cellSpacing)
    readonly property var entries:visibleItems.map(i=>({kind:"sni",item:i})).concat(visibleApplets.map(a=>({kind:"applet",item:a})))
    property bool configurable:true
    property bool readOnly:false
    property var appletProperties: ({})
    property var items:Sni.SystemTray.items.values
    property var settings:Config.options.bar.plasma.trayItems
    property var applets:[
        ({id:"network",title:qsTr("Networks"),icon:Network.ethernet?"network-wired":Network.wifiEnabled?"network-wireless":"network-wireless-offline",active:true}),
        ({id:"bluetooth",title:qsTr("Bluetooth"),icon:BluetoothStatus.enabled?"bluetooth-active":"bluetooth-disabled",active:BluetoothStatus.connected}),
        ({id:"audio",title:qsTr("Audio Volume"),icon:Audio.sink?.audio.muted?"audio-volume-muted":"audio-volume-high",active:true}),
        ({id:"notifications",title:qsTr("Notifications"),icon:Notifications.silent?"notifications-disabled":"notifications",active:Notifications.silent||Notifications.unread>0}),
        ({id:"media",title:qsTr("Media Player"),icon:"media-playback-start",active:MprisController.activePlayer?.isPlaying??false}),
        ({id:"clipboard",title:qsTr("Clipboard"),icon:"klipper",active:false}),
        ({id:"power",title:qsTr("Battery and Brightness"),icon:"battery",active:Battery.available})
    ]
    readonly property var visibleItems:items.filter(i=>Logic.visible(settings,i.id,i.status!==Sni.Status.Passive))
    readonly property var hiddenItems:items.filter(i=>!Logic.visible(settings,i.id,i.status!==Sni.Status.Passive))
    readonly property var visibleApplets:applets.filter(a=>Logic.visible(settings,"applet:"+a.id,a.active))
    readonly property var hiddenApplets:applets.filter(a=>!Logic.visible(settings,"applet:"+a.id,a.active))
    readonly property string screenName:QsWindow.window?.screen?.name||""
    readonly property bool expanded:TrayState.expanded&&TrayState.screenName===screenName
    readonly property string activeApplet:TrayState.applet
    property bool configuring:false
    onActiveAppletChanged:configuring=false
    readonly property var hiddenLayout:({currentIndex:-1})
    readonly property real contentLength:cellLength*Math.ceil(entries.length/lanes)+(expander.visible?itemSize:0)+Kirigami.Units.smallSpacing
    implicitWidth:vertical?Kirigami.Units.iconSizes.medium:contentLength
    implicitHeight:vertical?contentLength:Kirigami.Units.iconSizes.medium
    function openApplet(id) { TrayState.toggle(id,screenName); }
    function openMenu(item,button) { if(readOnly)return; menu.openFor(item.menu,button); }
    function setMode(id,value) { if(!readOnly)Config.options.bar.plasma.trayItems=Logic.update(settings,id,value); }
    GridLayout {
        anchors.fill:parent;rowSpacing:0;columnSpacing:0
        rows:root.vertical?2:1;columns:root.vertical?1:2
        GridView {
            id:layout
            Layout.alignment:Qt.AlignCenter
            implicitWidth:root.vertical?root.width:cellWidth*Math.ceil(count/root.lanes)
            implicitHeight:root.vertical?cellHeight*Math.ceil(count/root.lanes):root.height
            interactive:false
            flow:root.vertical?GridView.LeftToRight:GridView.TopToBottom
            cellWidth:root.vertical?Math.floor(root.width/root.lanes):root.cellLength
            cellHeight:root.vertical?root.cellLength:Math.floor(root.height/root.lanes)
            model:root.entries
            delegate:Loader {
                id:entry
                required property var modelData
                required property int index
                width:layout.cellWidth;height:layout.cellHeight
                sourceComponent:modelData.kind==="sni"?sniComponent:appletComponent
                Component {
                    id:sniComponent
                    StatusNotifierItem {
                        item:entry.modelData.item;index:entry.index;model:({});tray:root
                        effectiveStatus:PlasmaCore.Types.ActiveStatus
                    }
                }
                Component {
                    id:appletComponent
                    AppletItem {
                        applet:entry.modelData.item;index:entry.index;model:({});tray:root
                        effectiveStatus:PlasmaCore.Types.ActiveStatus
                    }
                }
            }
        }
        ExpanderArrow {
            id:expander;vertical:root.vertical;edge:root.edge
            iconSize:root.itemSize;expanded:root.expanded
            visible:root.hiddenItems.length+root.hiddenApplets.length>0
            Layout.fillWidth:root.vertical;Layout.fillHeight:!root.vertical
            onToggleRequested:value=>{root.configuring=false;if(value)TrayState.open("",root.screenName);else TrayState.close()}
        }
    }
    TrayMenu { id:menu }
    readonly property alias popupWindow:expandedWindow
    TrayPopup { id:expandedWindow;tray:root; anchorItem:expander }
}
