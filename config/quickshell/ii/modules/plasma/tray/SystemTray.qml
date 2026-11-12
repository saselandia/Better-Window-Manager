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
import org.kde.ksvg as KSvg
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
        // BWM: bluedevil 6.7.5 main.qml: Active while BluezQt bluetoothOperational (adapter present and on), icon by state.
        ({id:"bluetooth",title:qsTr("Bluetooth"),icon:BluetoothStatus.connected?"network-bluetooth-activated-symbolic":(BluetoothStatus.available&&BluetoothStatus.enabled)?"network-bluetooth-symbolic":"network-bluetooth-inactive-symbolic",active:BluetoothStatus.available&&BluetoothStatus.enabled}),
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
    // BWM: CurrentItemHighLight.qml (plasma-workspace 6.7.5 systemtray): «widgets/tabbar» active tab behind
    // the open applet's icon, or behind the whole tray (out to the panel edges) for hidden items. The
    // calendar belongs to the clock, which has its own highlight.
    KSvg.FrameSvgItem {
        id:currentItemHighLight
        property bool animationEnabled:true
        property var highlightedItem:null
        readonly property bool shown:root.expanded&&root.activeApplet!=="calendar"
        property var containerMargins:{ let item=root; while(item.parent){ item=item.parent; if(item.isAppletContainer)return item.getMargins; } return undefined; }
        z:-1
        imagePath:"widgets/tabbar"
        // hasElementPrefix() is not notifiable; a prefix list lets KSvg pick the first existing one
        prefix:[(({left:"west",top:"north",right:"east"})[root.edge]??"south")+"-active-tab","active-tab"]
        visible:opacity>0
        opacity:0
        function itemFor(id) {
            for (const child of layout.contentItem.children)
                if (child.modelData?.kind==="applet"&&child.modelData.item.id===id) return child;
            return null;
        }
        function updateHighlightedItem() {
            if (shown) {
                const item=root.activeApplet!==""?itemFor(root.activeApplet):null;
                if (item) changeHighlightedItem(item,false); // applet shown in the panel
                else changeHighlightedItem(root,true); // 'Show hidden items' popup or a hidden applet
            } else {
                highlightedItem=null;
            }
            opacity=shown?1:0;
        }
        function changeHighlightedItem(nextItem,forceEdgeHighlight) {
            // do not animate the first appearance or when the highlighted item is the same
            if (!highlightedItem||highlightedItem===nextItem) animationEnabled=false;
            const p=root.mapFromItem(nextItem,0,0);
            if (containerMargins&&(root.lanes===1||forceEdgeHighlight)) {
                x=p.x-containerMargins("left",true);
                y=p.y-containerMargins("top",true);
                width=nextItem.width+containerMargins("left",true)+containerMargins("right",true);
                height=nextItem.height+containerMargins("bottom",true)+containerMargins("top",true);
            } else {
                x=p.x;y=p.y;width=nextItem.width;height=nextItem.height;
            }
            highlightedItem=nextItem;
            animationEnabled=true;
        }
        Connections {
            target:root
            function onExpandedChanged() { Qt.callLater(currentItemHighLight.updateHighlightedItem); }
            function onActiveAppletChanged() { Qt.callLater(currentItemHighLight.updateHighlightedItem); }
            function onWidthChanged() { Qt.callLater(currentItemHighLight.updateHighlightedItem); }
            function onHeightChanged() { Qt.callLater(currentItemHighLight.updateHighlightedItem); }
        }
        Behavior on opacity { NumberAnimation { duration:Kirigami.Units.shortDuration;easing.type:currentItemHighLight.shown?Easing.OutCubic:Easing.InCubic } }
        Behavior on x { enabled:currentItemHighLight.animationEnabled;NumberAnimation { duration:Kirigami.Units.longDuration;easing.type:Easing.InOutCubic } }
        Behavior on y { enabled:currentItemHighLight.animationEnabled;NumberAnimation { duration:Kirigami.Units.longDuration;easing.type:Easing.InOutCubic } }
        Behavior on width { enabled:currentItemHighLight.animationEnabled;NumberAnimation { duration:Kirigami.Units.longDuration;easing.type:Easing.InOutCubic } }
        Behavior on height { enabled:currentItemHighLight.animationEnabled;NumberAnimation { duration:Kirigami.Units.longDuration;easing.type:Easing.InOutCubic } }
    }
    TrayMenu { id:menu }
    readonly property alias popupWindow:expandedWindow
    TrayPopup { id:expandedWindow;tray:root; anchorItem:expander }
}
