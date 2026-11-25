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
                PC3.ToolButton {
                    objectName:"plasma-bt-scan"
                    icon.name:"view-refresh"
                    text:root.scanning?root.i18n("Stop Searching"):root.i18n("Find Devices")
                    checkable:true; checked:root.scanning
                    enabled:!root.readOnly&&!!root.adapter&&root.backend.enabled
                    onClicked: {
                        if(root.adapter.discovering) {
                            root.stopOwnedDiscovery(true);
                        } else {
                            root.adapter.discovering=true;
                            root.initiatedDiscovery=true;
                            scanTimeout.restart();
                        }
                    }
                }
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
                    subtitle:modelData.pairing?root.i18n("Pairing…"):modelData.connected?root.i18n("Connected"):modelData.paired?root.i18n("Not Connected"):root.i18n("Available")
                    isBusy:modelData.pairing||modelData.state===BluetoothDeviceState.Connecting||modelData.state===BluetoothDeviceState.Disconnecting
                    defaultActionButtonAction: QQC2.Action {
                        icon.name:row.modelData.pairing?"dialog-cancel":row.modelData.connected?"network-disconnect-symbolic":"network-connect-symbolic"
                        text:row.modelData.pairing?root.i18n("Cancel"):row.modelData.connected?root.i18n("Disconnect"):root.i18n("Connect")
                        enabled:!root.readOnly&&(!row.isBusy||(row.modelData.pairing&&typeof row.modelData.cancelPair==="function"))
                        onTriggered: {
                            if(row.modelData.pairing&&typeof row.modelData.cancelPair==="function") row.modelData.cancelPair();
                            else if(row.modelData.connected) row.modelData.disconnect();
                            else if(row.modelData.paired) row.modelData.connect();
                            else row.modelData.pair();
                        }
                    }
                    customExpandedViewContent: Component {
                        ColumnLayout {
                            PC3.Label { text:row.modelData.address; textFormat:Text.PlainText }
                            PC3.Label { visible:row.modelData.batteryAvailable; text:root.i18n("Battery")+": "+Math.round(row.modelData.battery*100)+" %" }
                            PC3.CheckBox {
                                objectName:"plasma-bt-trusted"
                                visible:row.modelData.trusted!==undefined
                                text:root.i18n("Trusted")
                                checked:Boolean(row.modelData.trusted)
                                enabled:!root.readOnly&&!row.isBusy
                                onToggled:row.modelData.trusted=checked
                            }
                            PC3.CheckBox {
                                objectName:"plasma-bt-blocked"
                                visible:row.modelData.blocked!==undefined
                                text:root.i18n("Blocked")
                                checked:Boolean(row.modelData.blocked)
                                enabled:!root.readOnly&&!row.isBusy
                                onToggled:row.modelData.blocked=checked
                            }
                            PC3.Button { text:root.i18n("Forget Device"); enabled:!root.readOnly&&!row.isBusy; onClicked: { confirm.device=row.modelData; confirm.open(); } }
                        }
                    }
                }
                PlasmaExtras.PlaceholderMessage { anchors.centerIn:parent; visible:devices.count===0; text:root.backend.available?root.i18n("No devices found"):root.i18n("No Bluetooth adapters found") }
            }
        }
    }
    property bool scanning:adapter?.discovering??false
    function stopOwnedDiscovery(force) {
        scanTimeout.stop();
        if((force||initiatedDiscovery)&&adapter) adapter.discovering=false;
        initiatedDiscovery=false;
    }
    Timer { id:scanTimeout; interval:30000; onTriggered:root.stopOwnedDiscovery(false) }
    Component.onDestruction:root.stopOwnedDiscovery(false)
    onExpandedChanged:if(!expanded) root.stopOwnedDiscovery(false)
    PC3.Dialog {
        id:confirm
        property var device:null
        anchors.centerIn:parent
        modal:true
        closePolicy:QQC2.Popup.CloseOnEscape|QQC2.Popup.CloseOnPressOutside
        title:root.i18n("Forget Device")
        standardButtons:QQC2.Dialog.Ok|QQC2.Dialog.Cancel
        width:Math.min(Math.max(root.width-Kirigami.Units.largeSpacing*2,Kirigami.Units.gridUnit*12),Math.max(Kirigami.Units.gridUnit*14,confirmLabel.implicitWidth+leftPadding+rightPadding))
        implicitHeight:implicitHeaderHeight+confirmLabel.implicitHeight+implicitFooterHeight+topPadding+bottomPadding
        header:Kirigami.Heading { level:3; text:confirm.title; padding:Kirigami.Units.smallSpacing; horizontalAlignment:Text.AlignHCenter; elide:Text.ElideRight }
        onAccepted:if(!root.readOnly&&device)device.forget()
        PC3.Label { id:confirmLabel; width:confirm.availableWidth; text:confirm.device?.name||confirm.device?.address||""; wrapMode:Text.WordWrap; horizontalAlignment:Text.AlignHCenter }
    }
}
