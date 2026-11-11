/*
 SPDX-FileCopyrightText: 2013-2014 Jan Grulich <jgrulich@redhat.com>
 SPDX-FileCopyrightText: 2014-2015 David Rosca <nowrep@gmail.com>
 SPDX-FileCopyrightText: 2020 Nate Graham <nate@kde.org>
 SPDX-FileCopyrightText: 2024 ivan tkachenko <me@ratijas.tk>
 SPDX-License-Identifier: LGPL-2.1-only OR LGPL-3.0-only OR LicenseRef-KDE-Accepted-LGPL
*/
// BWM: bluedevil FullRepresentation/DeviceItem reduced to the device list and toolbar.
// The data/actions use the shared BlueZ service. OBEX and private Bluedevil plugins are omitted.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import Quickshell.Bluetooth
import qs.services
import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PC3
import org.kde.plasma.extras as PlasmaExtras
AppletHost {
    id:root
    translationDomain:"plasma_applet_org.kde.plasma.bluetooth"
    property var backend:BluetoothStatus
    property bool initiatedDiscovery:false
    property var adapter:Bluetooth.defaultAdapter
    fullRepresentation: PlasmaExtras.Representation {
        header: PlasmaExtras.PlasmoidHeading {
            RowLayout {
                anchors.fill:parent
                PC3.Switch { text:root.i18n("Enable Bluetooth"); checked:root.backend.enabled; enabled:!root.readOnly&&!!root.adapter; onToggled:root.adapter.enabled=checked }
                Item { Layout.fillWidth:true }
                PC3.ToolButton { icon.name:"view-refresh"; text:root.i18n("Find Devices"); enabled:!root.readOnly&&!!root.adapter&&root.backend.enabled; onClicked: { root.adapter.discovering=!root.adapter.discovering; root.initiatedDiscovery=root.adapter.discovering; if(root.initiatedDiscovery) scanTimeout.restart(); } }
            }
        }
        PC3.ScrollView {
            anchors.fill:parent
            ListView {
                id:devices
                clip:true; spacing:Kirigami.Units.smallSpacing
                model:root.backend.friendlyDeviceList
                delegate:PlasmaExtras.ExpandableListItem {
                    id:row
                    required property var modelData
                    required property int index
                    width:devices.width
                    icon:modelData.icon||"bluetooth"
                    title:modelData.name
                    subtitle:modelData.connected?root.i18n("Connected"):modelData.paired?root.i18n("Not Connected"):root.i18n("Available")
                    isBusy:modelData.pairing||modelData.state===BluetoothDeviceState.Connecting||modelData.state===BluetoothDeviceState.Disconnecting
                    defaultActionButtonAction: QQC2.Action {
                        icon.name:row.modelData.connected?"network-disconnect-symbolic":"network-connect-symbolic"
                        text:row.modelData.connected?root.i18n("Disconnect"):root.i18n("Connect")
                        enabled:!root.readOnly&&!row.isBusy
                        onTriggered: { if(row.modelData.connected) row.modelData.disconnect(); else if(row.modelData.paired) row.modelData.connect(); else row.modelData.pair(); }
                    }
                    customExpandedViewContent: Component {
                        ColumnLayout {
                            PC3.Label { text:row.modelData.address; textFormat:Text.PlainText }
                            PC3.Label { visible:row.modelData.batteryAvailable; text:root.i18n("Battery")+": "+Math.round(row.modelData.battery*100)+" %" }
                            PC3.Button { text:root.i18n("Forget Device"); enabled:!root.readOnly&&row.modelData.paired; onClicked: { confirm.device=row.modelData; confirm.open(); } }
                        }
                    }
                }
                PlasmaExtras.PlaceholderMessage { anchors.centerIn:parent; visible:devices.count===0; text:root.backend.available?root.i18n("No devices found"):root.i18n("No Bluetooth adapters found") }
            }
        }
    }
    property bool scanning:adapter?.discovering??false
    Timer { id:scanTimeout; interval:30000;onTriggered:if(root.adapter)root.adapter.discovering=false }
    Component.onDestruction:if(initiatedDiscovery&&adapter)adapter.discovering=false
    onExpandedChanged:if(!expanded&&initiatedDiscovery) { scanTimeout.stop(); if(adapter)adapter.discovering=false; }
    PC3.Dialog {
        id:confirm
        property var device:null
        title:root.i18n("Forget Device")
        standardButtons:QQC2.Dialog.Ok|QQC2.Dialog.Cancel
        onAccepted:if(!root.readOnly&&device)device.forget()
        PC3.Label { text:confirm.device?.name??"" }
    }
}
