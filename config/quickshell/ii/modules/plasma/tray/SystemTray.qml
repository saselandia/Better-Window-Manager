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
    property int itemSize:22
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
    implicitWidth:layout.implicitWidth;implicitHeight:layout.implicitHeight
    function openApplet(id) { TrayState.toggle(id,screenName); }
    function openMenu(item,button) { if(readOnly)return; menu.openFor(item.menu,button); }
    function setMode(id,value) { if(!readOnly)Config.options.bar.plasma.trayItems=Logic.update(settings,id,value); }
    GridLayout {
        id:layout; anchors.fill:parent;columns:root.vertical?1:-1;rows:root.vertical?-1:1;rowSpacing:4;columnSpacing:4
        Repeater {
            model:root.visibleItems
            StatusNotifierItem {
                required property var modelData
                required index
                item:modelData;model:({});tray:root
                effectiveStatus:PlasmaCore.Types.ActiveStatus
                Layout.preferredWidth:root.itemSize+6;Layout.preferredHeight:root.itemSize+6
            }
        }
        Repeater {
            model:root.visibleApplets
            PC3.ToolButton { required property var modelData; icon.name:modelData.icon;icon.width:22;icon.height:22;text:modelData.title;display:PC3.AbstractButton.IconOnly;implicitWidth:32;implicitHeight:32;checked:root.expanded&&root.activeApplet===modelData.id;onClicked:root.openApplet(modelData.id);PC3.ToolTip { text:parent.text } }
        }
        PC3.ToolButton { id:expander;icon.name:root.vertical?"arrow-left":"arrow-up";icon.width:16;icon.height:16;text:qsTr("Status and Notifications");implicitWidth:28;implicitHeight:28;onClicked:{root.configuring=false;TrayState.toggle("",root.screenName)} }
    }
    TrayMenu { id:menu }
    readonly property alias popupWindow:expandedWindow
    TrayPopup { id:expandedWindow;tray:root; anchorItem:expander }
}
