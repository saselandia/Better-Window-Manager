pragma ComponentBehavior: Bound

import qs
import qs.services
import qs.modules.common
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
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

    // KDE Plasma Breeze Dark Palette (same tokens as PlasmaKickoff)
    readonly property color colPanelBg: "#f024292e"
    readonly property color colHeaderBg: "#2a2e32"
    readonly property color colBorder: "#2e353b"
    readonly property color colAccent: "#3daee9"
    readonly property color colAccentSubtle: "#283daee9"
    readonly property color colAccentBorder: "#803daee9"
    readonly property color colText: "#eff0f1"
    readonly property color colTextMuted: "#a1a9b1"
    readonly property color colHover: "#15ffffff"
    readonly property color colButtonBg: "#31363b"
    readonly property color colButtonBorder: "#4d5257"
    readonly property color colNegative: "#da4453"
    readonly property string fontFamily: "Google Sans Flex"

    readonly property int popupWidth: 380
    readonly property int popupHeight: 440

    readonly property string iconsDir: Directories.assetsPath + "/icons/breeze-dark/bluetooth"
    function icon(name) {
        return "file://" + root.iconsDir + "/" + name + ".svg";
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

    // =================================================================
    // Reusable Breeze controls
    // =================================================================
    component BreezeSwitch: MouseArea {
        id: sw
        property bool checked: false
        signal toggled()
        implicitWidth: 36
        implicitHeight: 20
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: sw.toggled()

        Rectangle {
            anchors.fill: parent
            radius: height / 2
            color: sw.checked ? root.colAccent : root.colButtonBg
            border.width: 1
            border.color: sw.checked ? root.colAccent : (sw.containsMouse ? root.colAccent : root.colButtonBorder)
            Behavior on color { ColorAnimation { duration: 120 } }

            Rectangle {
                width: 16
                height: 16
                radius: 8
                anchors.verticalCenter: parent.verticalCenter
                x: sw.checked ? parent.width - width - 2 : 2
                color: sw.checked ? "#fcfcfc" : "#bdc3c7"
                Behavior on x { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
            }
        }
    }

    // Flat tool button (Plasma header style): transparent, hover fill + accent frame
    component BreezeToolButton: MouseArea {
        id: tb
        property string iconName: ""
        property string label: ""
        property string tooltip: ""
        implicitHeight: 28
        implicitWidth: tbRow.implicitWidth + (label.length > 0 ? 16 : 10)
        hoverEnabled: true
        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        opacity: enabled ? 1 : 0.4

        Rectangle {
            anchors.fill: parent
            radius: 4
            color: tb.containsPress ? root.colAccentSubtle : (tb.containsMouse ? root.colHover : "transparent")
            border.width: tb.containsMouse ? 1 : 0
            border.color: root.colAccentBorder
        }

        RowLayout {
            id: tbRow
            anchors.centerIn: parent
            spacing: 6
            Image {
                visible: tb.iconName.length > 0
                Layout.preferredWidth: 16
                Layout.preferredHeight: 16
                sourceSize: Qt.size(16, 16)
                source: tb.iconName.length > 0 ? root.icon(tb.iconName) : ""
            }
            Text {
                visible: tb.label.length > 0
                text: tb.label
                color: root.colText
                font.family: root.fontFamily
                font.pixelSize: 12
            }
        }
    }

    // Push button (Breeze frame)
    component BreezeButton: MouseArea {
        id: bb
        property string iconName: ""
        property string label: ""
        property bool destructive: false
        implicitHeight: 28
        implicitWidth: bbRow.implicitWidth + 20
        hoverEnabled: true
        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        opacity: enabled ? 1 : 0.4

        Rectangle {
            anchors.fill: parent
            radius: 4
            color: bb.containsPress ? root.colAccentSubtle : root.colButtonBg
            border.width: 1
            border.color: bb.containsMouse ? (bb.destructive ? root.colNegative : root.colAccent) : root.colButtonBorder
            Behavior on border.color { ColorAnimation { duration: 100 } }
        }

        RowLayout {
            id: bbRow
            anchors.centerIn: parent
            spacing: 6
            Image {
                visible: bb.iconName.length > 0
                Layout.preferredWidth: 16
                Layout.preferredHeight: 16
                sourceSize: Qt.size(16, 16)
                source: bb.iconName.length > 0 ? root.icon(bb.iconName) : ""
            }
            Text {
                text: bb.label
                color: root.colText
                font.family: root.fontFamily
                font.pixelSize: 12
            }
        }
    }

    component SectionHeader: RowLayout {
        id: sh
        property string title: ""
        Layout.fillWidth: true
        Layout.topMargin: 6
        Layout.leftMargin: 6
        Layout.rightMargin: 6
        spacing: 8
        Text {
            text: sh.title
            color: root.colTextMuted
            font.family: root.fontFamily
            font.pixelSize: 11
            font.weight: Font.DemiBold
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: root.colBorder
        }
    }

    component DetailKey: Text {
        Layout.alignment: Qt.AlignRight | Qt.AlignTop
        color: root.colTextMuted
        font.family: root.fontFamily
        font.pixelSize: 11
    }
    component DetailValue: Text {
        Layout.fillWidth: true
        color: root.colText
        font.family: root.fontFamily
        font.pixelSize: 11
        elide: Text.ElideRight
        textFormat: Text.PlainText
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
        color: item.expanded ? root.colAccentSubtle : (item.hovered ? root.colHover : "transparent")
        border.width: (item.expanded || item.hovered) ? 1 : 0
        border.color: root.colAccentBorder
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
                        color: root.colText
                        font.family: root.fontFamily
                        font.pixelSize: 13
                    }
                    Text {
                        Layout.fillWidth: true
                        text: root.deviceStatus(item.device)
                        elide: Text.ElideRight
                        color: (item.device?.connected ?? false) ? root.colAccent : root.colTextMuted
                        font.family: root.fontFamily
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
                    iconName: item.device?.connected ? "network-disconnect" : (item.device?.paired ? "network-connect" : "list-add")
                    label: item.device?.connected ? "Desconectar" : (item.device?.paired ? "Conectar" : "Emparejar")
                    onClicked: {
                        const d = item.device;
                        if (!d) return;
                        if (d.connected) d.disconnect();
                        else if (d.paired) d.connect();
                        else d.pair();
                    }
                }

                MouseArea {
                    id: expandBtn
                    Layout.preferredWidth: 24
                    Layout.preferredHeight: 24
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: item.expanded = !item.expanded
                    Rectangle {
                        anchors.fill: parent
                        radius: 4
                        color: expandBtn.containsMouse ? root.colHover : "transparent"
                    }
                    Image {
                        anchors.centerIn: parent
                        width: 16
                        height: 16
                        sourceSize: Qt.size(16, 16)
                        source: root.icon(item.expanded ? "arrow-up" : "arrow-down")
                    }
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


                DetailKey { text: "Nombre:" }
                DetailValue { text: item.device?.deviceName || item.device?.name || "—" }
                DetailKey { text: "Dirección:" }
                DetailValue { text: item.device?.address ?? "—" }
                DetailKey { text: "Tipo:" }
                DetailValue { text: root.deviceType(item.device) }
                DetailKey { visible: item.device?.batteryAvailable ?? false; text: "Batería:" }
                DetailValue { visible: item.device?.batteryAvailable ?? false; text: `${Math.round((item.device?.battery ?? 0) * 100)} %` }
                DetailKey { text: "De confianza:" }
                DetailValue { text: (item.device?.trusted ?? false) ? "Sí" : "No" }
                DetailKey { text: "Adaptador:" }
                DetailValue { text: root.adapter?.name ?? "—" }
            }

            RowLayout {
                visible: item.expanded && (item.device?.paired ?? false)
                Layout.fillWidth: true
                Layout.leftMargin: 42
                Layout.bottomMargin: 2
                spacing: 6
                BreezeButton {
                    iconName: "dialog-ok-apply"
                    label: (item.device?.trusted ?? false) ? "Dejar de confiar" : "Confiar"
                    onClicked: item.device.trusted = !item.device.trusted
                }
                BreezeButton {
                    destructive: true
                    iconName: "edit-delete"
                    label: "Olvidar"
                    onClicked: item.device.forget()
                }
                Item { Layout.fillWidth: true }
            }
        }
    }

    // Big centered message with optional action (PlasmaExtras.PlaceholderMessage)
    component Placeholder: ColumnLayout {
        id: ph
        property string iconName: "network-bluetooth-inactive"
        property string text: ""
        property string actionLabel: ""
        property string actionIcon: ""
        signal triggered()
        spacing: 10

        Image {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 64
            Layout.preferredHeight: 64
            sourceSize: Qt.size(64, 64)
            source: root.icon(ph.iconName)
            opacity: 0.6
        }
        Text {
            Layout.alignment: Qt.AlignHCenter
            Layout.maximumWidth: root.popupWidth - 60
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            text: ph.text
            color: root.colTextMuted
            font.family: root.fontFamily
            font.pixelSize: 15
        }
        BreezeButton {
            visible: ph.actionLabel.length > 0
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: 4
            iconName: ph.actionIcon
            label: ph.actionLabel
            onClicked: ph.triggered()
        }
    }

    // =================================================================
    // Popup window
    // =================================================================
    PanelWindow {
        id: win
        visible: root.opened || card.opacity > 0
        screen: Quickshell.screens.find(s => s.name === GlobalStates.plasmaBluetoothScreen) ?? Quickshell.screens[0]
        color: "transparent"
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "quickshell:plasmaBluetooth"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: root.opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
        anchors { top: true; bottom: true; left: true; right: true }

        // Click-outside closes (also catches the taskbar button -> natural toggle)
        MouseArea {
            anchors.fill: parent
            onClicked: root.close()
        }

        Item {
            anchors.fill: parent
            focus: root.opened
            Keys.onEscapePressed: root.close()
        }

        Rectangle {
            id: card
            width: root.popupWidth
            height: root.popupHeight
            // Centered over the taskbar button, clamped to the screen edges
            x: {
                const ax = GlobalStates.plasmaBluetoothAnchorX;
                const centered = ax >= 0 ? ax - width / 2 : win.width - width - 6;
                return Math.max(6, Math.min(win.width - width - 6, centered));
            }
            y: win.height - height - 46 + (root.opened ? 0 : 12)
            opacity: root.opened ? 1 : 0
            color: root.colPanelBg
            border.width: 1
            border.color: root.colBorder
            radius: 7
            clip: true

            Behavior on opacity { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
            Behavior on y { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }

            MouseArea { anchors.fill: parent } // Block backdrop click-through

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 1
                spacing: 0

                // ---------------------------------------------------------
                // Header (PlasmoidHeading)
                // ---------------------------------------------------------
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 44
                    color: root.colHeaderBg
                    topLeftRadius: 6
                    topRightRadius: 6

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 6
                        spacing: 6

                        BreezeSwitch {
                            enabled: !!root.adapter
                            checked: root.adapterEnabled
                            onToggled: {
                                if (!root.adapter) return;
                                root.adapter.enabled = !root.adapter.enabled;
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "Bluetooth"
                            color: root.colText
                            font.family: root.fontFamily
                            font.pixelSize: 13
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                        }
                        BreezeToolButton {
                            enabled: root.adapterEnabled
                            iconName: root.discovering ? "view-refresh" : "list-add"
                            label: root.discovering ? "Buscando…" : "Emparejar dispositivo…"
                            onClicked: root.setDiscovering(!root.discovering)
                        }
                        BreezeToolButton {
                            iconName: "configure"
                            onClicked: {
                                root.close();
                                Quickshell.execDetached(["bash", "-c", Config.options.apps.bluetooth]);
                            }
                        }
                    }

                    Rectangle {
                        anchors.bottom: parent.bottom
                        anchors.left: parent.left
                        anchors.right: parent.right
                        height: 1
                        color: root.colBorder
                    }

                    // Indeterminate scan bar
                    Item {
                        anchors.bottom: parent.bottom
                        anchors.left: parent.left
                        anchors.right: parent.right
                        height: 2
                        clip: true
                        visible: root.discovering
                        Rectangle {
                            id: scanBar
                            width: parent.width / 3
                            height: parent.height
                            color: root.colAccent
                            NumberAnimation on x {
                                running: root.discovering
                                from: -scanBar.width
                                to: root.popupWidth
                                duration: 1200
                                loops: Animation.Infinite
                            }
                        }
                    }
                }

                // ---------------------------------------------------------
                // Body
                // ---------------------------------------------------------
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    Placeholder {
                        anchors.centerIn: parent
                        visible: !BluetoothStatus.available
                        iconName: "network-bluetooth-inactive"
                        text: "No se encontraron adaptadores Bluetooth"
                    }

                    Placeholder {
                        anchors.centerIn: parent
                        visible: BluetoothStatus.available && !root.adapterEnabled
                        iconName: "network-bluetooth-inactive"
                        text: "Bluetooth está desactivado"
                        actionLabel: "Activar"
                        actionIcon: "network-bluetooth"
                        onTriggered: root.adapter.enabled = true
                    }

                    Placeholder {
                        anchors.centerIn: parent
                        visible: root.adapterEnabled && !root.hasAnyDevice
                        iconName: "preferences-system-bluetooth"
                        text: root.discovering ? "Buscando dispositivos cercanos…" : "No hay dispositivos emparejados"
                        actionLabel: root.discovering ? "" : "Emparejar dispositivo…"
                        actionIcon: "list-add"
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

                            SectionHeader {
                                visible: BluetoothStatus.connectedDevices.length > 0
                                title: "Conectados"
                            }
                            Repeater {
                                model: ScriptModel { values: BluetoothStatus.connectedDevices }
                                delegate: DeviceItem {}
                            }

                            SectionHeader {
                                visible: BluetoothStatus.pairedButNotConnectedDevices.length > 0
                                title: "Disponibles"
                            }
                            Repeater {
                                model: ScriptModel { values: BluetoothStatus.pairedButNotConnectedDevices }
                                delegate: DeviceItem {}
                            }

                            SectionHeader {
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
}
