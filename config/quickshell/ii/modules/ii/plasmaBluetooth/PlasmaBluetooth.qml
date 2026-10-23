pragma ComponentBehavior: Bound

import qs
import qs.services
import qs.modules.common
import qs.modules.ii.plasmaCommon
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Bluetooth

/**
 * KDE Plasma 6 Bluetooth applet (Bluedevil) recreated in Breeze Dark.
 * - Opened from the Bluetooth button of the Plasma taskbar (left click), anchored above it.
 * - Header: enable switch, "Pair device…" (starts discovery) and "Configure Bluetooth…".
 * - Sections: Connected / Paired / Found devices, each row is an expandable list item
 *   with a default action (Connect / Disconnect / Pair) and a details grid.
 * - Placeholders for "no adapter", "Bluetooth disabled" and "no devices".
 * - IPC: quickshell -c ii ipc call plasmaBluetooth toggle|open|close
 */
Scope {
    id: root

    readonly property bool opened: GlobalStates.plasmaBluetoothOpen
    readonly property var adapter: Bluetooth.defaultAdapter
    readonly property bool adapterEnabled: adapter?.enabled ?? false
    readonly property bool discovering: adapter?.discovering ?? false

    function icon(name) {
        return Breeze.icon("bluetooth", name);
    }

    // BlueZ device icon names -> bundled Breeze Dark device icons
    function deviceIcon(device) {
        const n = device?.icon ?? "";
        if (n.includes("headset")) return "audio-headset";
        if (n.includes("headphone")) return "audio-headphones";
        if (n.startsWith("audio")) return "audio-card";
        if (n.includes("mouse")) return "input-mouse";
        if (n.includes("keyboard")) return "input-keyboard";
        if (n.includes("gaming") || n.includes("joystick")) return "input-gamepad";
        if (n.includes("tablet")) return "input-tablet";
        if (n.includes("phone")) return "smartphone";
        if (n.includes("laptop")) return "computer-laptop";
        if (n.includes("computer") || n.includes("video-display")) return "computer";
        if (n.includes("printer")) return "printer";
        if (n.includes("camera-video")) return "camera-video";
        if (n.includes("camera")) return "camera-photo";
        return "network-bluetooth";
    }

    function deviceType(device) {
        const n = device?.icon ?? "";
        if (n.includes("headset")) return "Auriculares con micrófono";
        if (n.includes("headphone")) return "Auriculares";
        if (n.startsWith("audio")) return "Audio";
        if (n.includes("mouse")) return "Ratón";
        if (n.includes("keyboard")) return "Teclado";
        if (n.includes("gaming") || n.includes("joystick")) return "Mando de juego";
        if (n.includes("tablet")) return "Tableta";
        if (n.includes("phone")) return "Teléfono";
        if (n.includes("computer") || n.includes("laptop")) return "Ordenador";
        if (n.includes("printer")) return "Impresora";
        if (n.includes("camera")) return "Cámara";
        if (n.includes("video-display")) return "Pantalla";
        return "Desconocido";
    }

    function deviceStatus(device) {
        if (!device) return "";
        if (device.pairing) return "Emparejando…";
        if (device.state === BluetoothDeviceState.Connecting) return "Conectando…";
        if (device.state === BluetoothDeviceState.Disconnecting) return "Desconectando…";
        let text = device.connected ? "Conectado" : (device.paired ? "No conectado" : "Disponible");
        if (device.connected && device.batteryAvailable)
            text += ` · Batería ${Math.round(device.battery * 100)} %`;
        return text;
    }

    function isBusy(device) {
        return !!device && (device.pairing
            || device.state === BluetoothDeviceState.Connecting
            || device.state === BluetoothDeviceState.Disconnecting);
    }

    // Unpaired devices without a real name are just noise (Plasma hides them too)
    readonly property var foundDevices: BluetoothStatus.unpairedDevices.filter(d => d.deviceName && d.deviceName.length > 0 && !/^([0-9A-Fa-f]{2}[-:]){5}[0-9A-Fa-f]{2}$/.test(d.deviceName))
    readonly property bool hasAnyDevice: BluetoothStatus.connectedDevices.length + BluetoothStatus.pairedButNotConnectedDevices.length + foundDevices.length > 0

    function open() {
        GlobalStates.plasmaBluetoothOpen = true;
    }
    function close() {
        GlobalStates.plasmaBluetoothOpen = false;
    }
    function toggle() {
        GlobalStates.plasmaBluetoothOpen = !GlobalStates.plasmaBluetoothOpen;
    }

    function setDiscovering(on) {
        if (!root.adapter) return;
        root.adapter.discovering = on && root.adapterEnabled;
        if (on) discoveryTimeout.restart(); else discoveryTimeout.stop();
    }

    onOpenedChanged: {
        if (!opened) setDiscovering(false);
    }

    // Plasma scans for a limited time in its pairing wizard; do the same
    Timer {
        id: discoveryTimeout
        interval: 60000
        onTriggered: root.setDiscovering(false)
    }

    IpcHandler {
        target: "plasmaBluetooth"
        function toggle(): void { root.toggle(); }
        function open(): void { root.open(); }
        function close(): void { root.close(); }
    }

    // Plasma "ExpandableListItem" for one Bluetooth device
    component DeviceItem: Rectangle {
        id: item
        required property var modelData
        readonly property var device: modelData
        property bool expanded: false
        readonly property bool hovered: rowMouse.containsMouse || actionBtn.containsMouse || expandBtn.containsMouse

        Layout.fillWidth: true
        implicitHeight: itemCol.implicitHeight + 12
        radius: 4
        color: item.expanded ? Breeze.accentSubtle : (item.hovered ? Breeze.hover : "transparent")
        border.width: (item.expanded || item.hovered) ? 1 : 0
        border.color: Breeze.accentBorder
        Behavior on color { ColorAnimation { duration: 100 } }

        // Pair -> trust -> connect, like Bluedevil's wizard does
        Connections {
            target: item.device
            function onPairedChanged() {
                if (item.device?.paired && !item.device.connected) {
                    item.device.trusted = true;
                    item.device.connect();
                }
            }
        }

        MouseArea {
            id: rowMouse
            anchors.fill: parent
            hoverEnabled: true
            onClicked: item.expanded = !item.expanded
        }

        ColumnLayout {
            id: itemCol
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
                margins: 6
                leftMargin: 8
            }
            spacing: 6

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Image {
                    Layout.preferredWidth: 32
                    Layout.preferredHeight: 32
                    Layout.alignment: Qt.AlignVCenter
                    sourceSize: Qt.size(32, 32)
                    source: root.icon(root.deviceIcon(item.device))
                    opacity: (item.device?.connected ?? false) ? 1 : 0.75
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignVCenter
                    spacing: 1
                    Text {
                        Layout.fillWidth: true
                        text: item.device?.name || "Dispositivo desconocido"
                        textFormat: Text.PlainText
                        elide: Text.ElideRight
                        color: Breeze.text
                        font.family: Breeze.fontFamily
                        font.pixelSize: 13
                    }
                    Text {
                        Layout.fillWidth: true
                        text: root.deviceStatus(item.device)
                        elide: Text.ElideRight
                        color: (item.device?.connected ?? false) ? Breeze.accent : Breeze.textMuted
                        font.family: Breeze.fontFamily
                        font.pixelSize: 11
                    }
                }

                // Busy spinner while pairing / connecting
                Image {
                    id: busyIcon
                    visible: root.isBusy(item.device)
                    Layout.preferredWidth: 16
                    Layout.preferredHeight: 16
                    sourceSize: Qt.size(16, 16)
                    source: root.icon("view-refresh")
                    RotationAnimator on rotation {
                        running: busyIcon.visible
                        from: 0; to: 360
                        duration: 1000
                        loops: Animation.Infinite
                    }
                }

                // Default action (shown on hover/expanded, like Plasma)
                BreezeButton {
                    id: actionBtn
                    visible: (item.hovered || item.expanded) && !root.isBusy(item.device)
                    iconSource: root.icon(item.device?.connected ? "network-disconnect" : (item.device?.paired ? "network-connect" : "list-add"))
                    label: item.device?.connected ? "Desconectar" : (item.device?.paired ? "Conectar" : "Emparejar")
                    onClicked: {
                        const d = item.device;
                        if (!d) return;
                        if (d.connected) d.disconnect();
                        else if (d.paired) d.connect();
                        else d.pair();
                    }
                }

                BreezeToolButton {
                    id: expandBtn
                    implicitWidth: 24
                    implicitHeight: 24
                    iconSource: root.icon(item.expanded ? "arrow-up" : "arrow-down")
                    onClicked: item.expanded = !item.expanded
                }
            }

            // Expanded details (Bluedevil "DeviceItem" details grid)
            GridLayout {
                visible: item.expanded
                Layout.fillWidth: true
                Layout.leftMargin: 42
                columns: 2
                columnSpacing: 10
                rowSpacing: 3

                BreezeDetailKey { text: "Nombre:" }
                BreezeDetailValue { text: item.device?.deviceName || item.device?.name || "—" }
                BreezeDetailKey { text: "Dirección:" }
                BreezeDetailValue { text: item.device?.address ?? "—" }
                BreezeDetailKey { text: "Tipo:" }
                BreezeDetailValue { text: root.deviceType(item.device) }
                BreezeDetailKey { visible: item.device?.batteryAvailable ?? false; text: "Batería:" }
                BreezeDetailValue { visible: item.device?.batteryAvailable ?? false; text: `${Math.round((item.device?.battery ?? 0) * 100)} %` }
                BreezeDetailKey { text: "De confianza:" }
                BreezeDetailValue { text: (item.device?.trusted ?? false) ? "Sí" : "No" }
                BreezeDetailKey { text: "Adaptador:" }
                BreezeDetailValue { text: root.adapter?.name ?? "—" }
            }

            RowLayout {
                visible: item.expanded && (item.device?.paired ?? false)
                Layout.fillWidth: true
                Layout.leftMargin: 42
                Layout.bottomMargin: 2
                spacing: 6
                BreezeButton {
                    iconSource: root.icon("dialog-ok-apply")
                    label: (item.device?.trusted ?? false) ? "Dejar de confiar" : "Confiar"
                    onClicked: item.device.trusted = !item.device.trusted
                }
                BreezeButton {
                    destructive: true
                    iconSource: root.icon("edit-delete")
                    label: "Olvidar"
                    onClicked: item.device.forget()
                }
                Item { Layout.fillWidth: true }
            }
        }
    }

    BreezePopupWindow {
        opened: root.opened
        anchorX: GlobalStates.plasmaBluetoothAnchorX
        screenName: GlobalStates.plasmaBluetoothScreen
        namespace: "quickshell:plasmaBluetooth"
        popupWidth: 380
        popupHeight: 440
        onCloseRequested: root.close()

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 1
            spacing: 0

            BreezeHeader {
                busy: root.discovering

                BreezeSwitch {
                    enabled: !!root.adapter
                    checked: root.adapterEnabled
                    onToggled: root.adapter.enabled = !root.adapter.enabled
                }
                Text {
                    Layout.fillWidth: true
                    text: "Bluetooth"
                    color: Breeze.text
                    font.family: Breeze.fontFamily
                    font.pixelSize: 13
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                BreezeToolButton {
                    enabled: root.adapterEnabled
                    iconSource: root.icon(root.discovering ? "view-refresh" : "list-add")
                    label: root.discovering ? "Buscando…" : "Emparejar dispositivo…"
                    onClicked: root.setDiscovering(!root.discovering)
                }
                BreezeToolButton {
                    iconSource: root.icon("configure")
                    onClicked: {
                        root.close();
                        Quickshell.execDetached(["bash", "-c", Config.options.apps.bluetooth]);
                    }
                }
            }

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                BreezePlaceholder {
                    anchors.centerIn: parent
                    visible: !BluetoothStatus.available
                    iconSource: root.icon("network-bluetooth-inactive")
                    text: "No se encontraron adaptadores Bluetooth"
                }

                BreezePlaceholder {
                    anchors.centerIn: parent
                    visible: BluetoothStatus.available && !root.adapterEnabled
                    iconSource: root.icon("network-bluetooth-inactive")
                    text: "Bluetooth está desactivado"
                    actionLabel: "Activar"
                    actionIcon: root.icon("network-bluetooth")
                    onTriggered: root.adapter.enabled = true
                }

                BreezePlaceholder {
                    anchors.centerIn: parent
                    visible: root.adapterEnabled && !root.hasAnyDevice
                    iconSource: root.icon("preferences-system-bluetooth")
                    text: root.discovering ? "Buscando dispositivos cercanos…" : "No hay dispositivos emparejados"
                    actionLabel: root.discovering ? "" : "Emparejar dispositivo…"
                    actionIcon: root.icon("list-add")
                    onTriggered: root.setDiscovering(true)
                }

                Flickable {
                    id: flick
                    anchors.fill: parent
                    anchors.margins: 6
                    visible: root.adapterEnabled && root.hasAnyDevice
                    contentHeight: listCol.implicitHeight
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds

                    ColumnLayout {
                        id: listCol
                        width: flick.width
                        spacing: 2

                        BreezeSectionHeader {
                            visible: BluetoothStatus.connectedDevices.length > 0
                            title: "Conectados"
                        }
                        Repeater {
                            model: ScriptModel { values: BluetoothStatus.connectedDevices }
                            delegate: DeviceItem {}
                        }

                        BreezeSectionHeader {
                            visible: BluetoothStatus.pairedButNotConnectedDevices.length > 0
                            title: "Disponibles"
                        }
                        Repeater {
                            model: ScriptModel { values: BluetoothStatus.pairedButNotConnectedDevices }
                            delegate: DeviceItem {}
                        }

                        BreezeSectionHeader {
                            visible: root.foundDevices.length > 0
                            title: "Dispositivos encontrados"
                        }
                        Repeater {
                            model: ScriptModel { values: root.foundDevices }
                            delegate: DeviceItem {}
                        }
                    }
                }
            }
        }
    }
}
