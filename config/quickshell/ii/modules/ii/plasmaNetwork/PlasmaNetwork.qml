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
 * KDE Plasma 6 Networks applet (plasma-nm) recreated in Breeze Dark.
 * - Opened from the network button of the Plasma taskbar, anchored above it.
 * - Header: Wi-Fi switch, airplane mode switch, search filter and "Configure network connections…".
 * - Sections: Connected / Available. Wired + Wi-Fi connections as expandable list items with
 *   default action (Connect / Disconnect), inline password entry for secured networks,
 *   "Speed" tab (live up/down graph) and "Details" tab (IP, gateway, DNS, MAC, frequency…).
 * - Backend: NetworkManager via nmcli (Network service + local nmcli calls).
 * - IPC: quickshell -c ii ipc call plasmaNetwork toggle|open|close
 */
Scope {
    id: root

    readonly property bool opened: GlobalStates.plasmaNetworkOpen
    property string filterText: ""
    property bool searchVisible: false

    // nmcli state that the Network service does not expose
    property var devices: []          // [{ dev, type, state, connection }]
    property var savedWifi: []        // saved 802-11-wireless connection names
    readonly property var wifiDevice: devices.find(d => d.type === "wifi") ?? null
    readonly property var wiredDevices: devices.filter(d => d.type === "ethernet")

    // Connection attempt state, keyed by entry key
    property string pendingKey: ""
    property var needsPassword: ({})
    property var errors: ({})

    // Live traffic per interface: { dev: { rx, tx, rxRate, txRate, rxHist: [], txHist: [] } }
    property var traffic: ({})
    readonly property int historyLength: 60

    // Airplane mode: everything radio off (remembers previous Wi-Fi/Bluetooth state)
    property bool airplaneMode: false
    property bool wifiBeforeAirplane: true
    property bool btBeforeAirplane: false

    function icon(name) {
        return Breeze.icon("network", name);
    }
    function sharedIcon(name) {
        return Breeze.icon("bluetooth", name);
    }

    function signalBucket(strength) {
        if (strength >= 80) return 100;
        if (strength >= 60) return 80;
        if (strength >= 40) return 60;
        if (strength >= 20) return 40;
        if (strength >= 5) return 20;
        return 0;
    }

    function formatRate(bytesPerSec) {
        const units = ["B/s", "KiB/s", "MiB/s", "GiB/s"];
        let v = Math.max(0, bytesPerSec);
        let i = 0;
        while (v >= 1024 && i < units.length - 1) {
            v /= 1024;
            i++;
        }
        return `${v < 10 && i > 0 ? v.toFixed(1) : Math.round(v)} ${units[i]}`;
    }

    function securityLabel(security) {
        if (!security || security.length === 0) return "Abierta";
        if (security.includes("WPA3") || security.includes("SAE")) return "WPA3";
        if (security.includes("802.1X")) return "WPA2 Enterprise";
        if (security.includes("WPA2")) return "WPA2";
        if (security.includes("WPA")) return "WPA";
        if (security.includes("WEP")) return "WEP";
        return security;
    }

    function setMap(prop, key, value) {
        const m = Object.assign({}, root[prop]);
        if (value === undefined) delete m[key]; else m[key] = value;
        root[prop] = m;
    }

    // ------------------------------------------------------------------
    // Entries model (wired + Wi-Fi), filtered by the search field
    // ------------------------------------------------------------------
    readonly property var entries: {
        const list = [];
        for (const d of root.wiredDevices) {
            list.push({
                key: "wired:" + d.dev,
                kind: "wired",
                name: d.connection || "Conexión cableada",
                dev: d.dev,
                active: d.state === "connected",
                connecting: d.state.startsWith("connecting"),
                available: d.state !== "unavailable",
                connection: d.connection
            });
        }
        if (Network.wifiEnabled && root.wifiDevice) {
            const wd = root.wifiDevice;
            for (const ap of Network.friendlyWifiNetworks) {
                const isActive = ap.active;
                list.push({
                    key: "wifi:" + ap.ssid,
                    kind: "wifi",
                    name: ap.ssid,
                    dev: wd.dev,
                    ap: ap,
                    active: isActive,
                    connecting: isActive && wd.state.startsWith("connecting"),
                    available: true,
                    saved: root.savedWifi.includes(ap.ssid),
                    connection: isActive ? (wd.connection || ap.ssid) : ap.ssid
                });
            }
        }
        const f = root.filterText.trim().toLowerCase();
        return f.length > 0 ? list.filter(e => e.name.toLowerCase().includes(f)) : list;
    }
    readonly property var connectedEntries: entries.filter(e => e.active || root.pendingKey === e.key)
    readonly property var availableEntries: entries.filter(e => !e.active && root.pendingKey !== e.key && e.available)

    // ------------------------------------------------------------------
    // Actions
    // ------------------------------------------------------------------
    function open() {
        GlobalStates.plasmaNetworkOpen = true;
    }
    function close() {
        GlobalStates.plasmaNetworkOpen = false;
    }
    function toggle() {
        GlobalStates.plasmaNetworkOpen = !GlobalStates.plasmaNetworkOpen;
    }

    function refresh() {
        devicesProc.running = true;
        savedProc.running = true;
    }

    function runAction(key, command, env) {
        root.pendingKey = key;
        root.setMap("errors", key, undefined);
        actionProc.key = key;
        actionProc.environment = Object.assign({ LANG: "C", LC_ALL: "C" }, env ?? {});
        actionProc.command = command;
        actionProc.running = true;
    }

    function connectEntry(entry, password) {
        if (!entry) return;
        if (entry.kind === "wired") {
            if (entry.connection)
                runAction(entry.key, ["nmcli", "connection", "up", "id", entry.connection]);
            else
                runAction(entry.key, ["nmcli", "device", "connect", entry.dev]);
            return;
        }
        const needsPw = entry.ap?.isSecure && !entry.saved;
        if (password !== undefined && password.length > 0) {
            if (entry.saved) {
                runAction(entry.key, ["sh", "-c", 'nmcli connection modify id "$SSID" wifi-sec.psk "$PW" && nmcli connection up id "$SSID"'], { SSID: entry.name, PW: password });
            } else {
                runAction(entry.key, ["sh", "-c", 'nmcli device wifi connect "$SSID" password "$PW" ifname "$DEV"'], { SSID: entry.name, PW: password, DEV: entry.dev });
            }
        } else if (needsPw) {
            root.setMap("needsPassword", entry.key, true);
        } else if (entry.saved) {
            runAction(entry.key, ["nmcli", "connection", "up", "id", entry.name]);
        } else {
            runAction(entry.key, ["nmcli", "device", "wifi", "connect", entry.name, "ifname", entry.dev]);
        }
    }

    function disconnectEntry(entry) {
        if (!entry) return;
        if (entry.connection)
            runAction(entry.key, ["nmcli", "connection", "down", "id", entry.connection]);
        else
            runAction(entry.key, ["nmcli", "device", "disconnect", entry.dev]);
    }

    function forgetEntry(entry) {
        if (!entry) return;
        runAction(entry.key, ["nmcli", "connection", "delete", "id", entry.name]);
    }

    function setAirplaneMode(on) {
        if (on === root.airplaneMode) return;
        root.airplaneMode = on;
        if (on) {
            root.wifiBeforeAirplane = Network.wifiEnabled;
            root.btBeforeAirplane = BluetoothStatus.enabled;
            Quickshell.execDetached(["nmcli", "radio", "all", "off"]);
            if (Bluetooth.defaultAdapter) Bluetooth.defaultAdapter.enabled = false;
        } else {
            if (root.wifiBeforeAirplane) Quickshell.execDetached(["nmcli", "radio", "wifi", "on"]);
            if (root.btBeforeAirplane && Bluetooth.defaultAdapter) Bluetooth.defaultAdapter.enabled = true;
        }
    }

    function openSettings() {
        root.close();
        // plasma-nm KCM if present, otherwise nm-connection-editor, otherwise nmtui in a terminal
        Quickshell.execDetached(["bash", "-c",
            "if kcmshell6 --list 2>/dev/null | grep -q '^kcm_networkmanagement'; then exec kcmshell6 kcm_networkmanagement; " +
            "elif command -v nm-connection-editor >/dev/null; then exec nm-connection-editor; " +
            "else exec kitty -1 --class nmtui nmtui; fi"]);
    }

    onOpenedChanged: {
        if (opened) {
            root.refresh();
            if (Network.wifiEnabled) Network.rescanWifi();
        } else {
            root.searchVisible = false;
            root.filterText = "";
        }
    }

    // ------------------------------------------------------------------
    // Processes
    // ------------------------------------------------------------------
    Process {
        id: devicesProc
        command: ["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device"]
        environment: ({ LANG: "C", LC_ALL: "C" })
        stdout: StdioCollector {
            onStreamFinished: {
                root.devices = text.trim().split("\n").filter(l => l.length > 0).map(l => {
                    const p = l.replace(/\\:/g, "\u0001").split(":").map(s => s.replace(/\u0001/g, ":"));
                    return { dev: p[0], type: p[1], state: p[2] ?? "", connection: p[3] ?? "" };
                }).filter(d => d.type === "ethernet" || d.type === "wifi");
            }
        }
    }

    Process {
        id: savedProc
        command: ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"]
        environment: ({ LANG: "C", LC_ALL: "C" })
        stdout: StdioCollector {
            onStreamFinished: {
                root.savedWifi = text.trim().split("\n")
                    .map(l => l.replace(/\\:/g, "\u0001").split(":"))
                    .filter(p => p[1] === "802-11-wireless")
                    .map(p => p[0].replace(/\u0001/g, ":"));
            }
        }
    }

    Process {
        id: actionProc
        property string key: ""
        stderr: StdioCollector { id: actionErr }
        onExited: (exitCode, exitStatus) => {
            const k = actionProc.key;
            const err = actionErr.text.trim();
            if (exitCode !== 0) {
                if (/secrets were required|password|802-11-wireless-security\.psk|property is missing/i.test(err)) {
                    root.setMap("needsPassword", k, true);
                    root.setMap("errors", k, "Contraseña incorrecta o necesaria");
                } else {
                    root.setMap("errors", k, err.replace(/^Error:\s*/, "").split("\n")[0] || "No se pudo completar la acción");
                }
            } else {
                root.setMap("needsPassword", k, undefined);
            }
            root.pendingKey = "";
            root.refresh();
            Network.update();
        }
    }

    // Traffic sampler (only while the popup is open)
    Process {
        id: trafficProc
        environment: ({ LANG: "C", LC_ALL: "C" })
        stdout: StdioCollector {
            onStreamFinished: {
                const t = Object.assign({}, root.traffic);
                for (const line of text.trim().split("\n")) {
                    const [dev, rxS, txS] = line.split(" ");
                    const rx = parseInt(rxS), tx = parseInt(txS);
                    if (!dev || isNaN(rx) || isNaN(tx)) continue;
                    const prev = t[dev];
                    const rxRate = prev ? Math.max(0, rx - prev.rx) : 0;
                    const txRate = prev ? Math.max(0, tx - prev.tx) : 0;
                    const rxHist = (prev?.rxHist ?? []).concat([rxRate]).slice(-root.historyLength);
                    const txHist = (prev?.txHist ?? []).concat([txRate]).slice(-root.historyLength);
                    t[dev] = { rx, tx, rxRate, txRate, rxHist, txHist };
                }
                root.traffic = t;
            }
        }
    }

    Timer {
        interval: 1000
        repeat: true
        running: root.opened
        triggeredOnStart: true
        onTriggered: {
            const devs = root.devices.filter(d => d.state === "connected").map(d => d.dev);
            if (devs.length === 0) return;
            trafficProc.command = ["sh", "-c",
                'for d in "$@"; do echo "$d $(cat /sys/class/net/$d/statistics/rx_bytes) $(cat /sys/class/net/$d/statistics/tx_bytes)"; done',
                "sh", ...devs];
            trafficProc.running = true;
        }
    }

    // Keep device states fresh while open (nmcli monitor already drives the Network service)
    Timer {
        interval: 4000
        repeat: true
        running: root.opened
        onTriggered: root.refresh()
    }
    Timer {
        interval: 20000
        repeat: true
        running: root.opened && Network.wifiEnabled
        onTriggered: Network.rescanWifi()
    }
    Connections {
        target: Network
        function onWifiStatusChanged() { root.refresh(); }
        function onEthernetChanged() { root.refresh(); }
        function onNetworkNameChanged() { root.refresh(); }
        function onWifiEnabledChanged() { root.refresh(); }
    }

    IpcHandler {
        target: "plasmaNetwork"
        function toggle(): void { root.toggle(); }
        function open(): void { root.open(); }
        function close(): void { root.close(); }
    }

    // ------------------------------------------------------------------
    // Live speed graph (plasma-nm "Speed" tab)
    // ------------------------------------------------------------------
    component TrafficGraph: Canvas {
        id: graph
        property var rxHist: []
        property var txHist: []
        onRxHistChanged: requestPaint()
        onTxHistChanged: requestPaint()
        onPaint: {
            const ctx = getContext("2d");
            ctx.reset();
            const w = width, h = height;
            ctx.strokeStyle = Qt.rgba(1, 1, 1, 0.08);
            ctx.lineWidth = 1;
            for (let i = 1; i < 4; i++) {
                ctx.beginPath();
                ctx.moveTo(0, Math.round(h * i / 4) + 0.5);
                ctx.lineTo(w, Math.round(h * i / 4) + 0.5);
                ctx.stroke();
            }
            const max = Math.max(1024, ...graph.rxHist, ...graph.txHist) * 1.15;
            const n = root.historyLength;
            const draw = (hist, color, fill) => {
                if (hist.length < 2) return;
                const step = w / (n - 1);
                const x0 = w - (hist.length - 1) * step;
                ctx.beginPath();
                ctx.moveTo(x0, h);
                hist.forEach((v, i) => ctx.lineTo(x0 + i * step, h - (v / max) * h));
                ctx.lineTo(w, h);
                ctx.closePath();
                ctx.fillStyle = fill;
                ctx.fill();
                ctx.beginPath();
                hist.forEach((v, i) => {
                    const x = x0 + i * step, y = h - (v / max) * h;
                    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
                });
                ctx.strokeStyle = color;
                ctx.lineWidth = 1.5;
                ctx.stroke();
            };
            draw(graph.txHist, Breeze.neutral, Qt.rgba(0.96, 0.45, 0, 0.15));
            draw(graph.rxHist, Breeze.accent, Qt.rgba(0.24, 0.68, 0.91, 0.2));
        }
    }

    // ------------------------------------------------------------------
    // Plasma "ConnectionItem" (ExpandableListItem)
    // ------------------------------------------------------------------
    component ConnectionItem: Rectangle {
        id: item
        required property var modelData
        readonly property var entry: modelData
        readonly property bool isWifi: entry.kind === "wifi"
        readonly property bool busy: root.pendingKey === entry.key || entry.connecting
        readonly property bool askPassword: root.needsPassword[entry.key] === true
        readonly property string error: root.errors[entry.key] ?? ""
        readonly property var stats: root.traffic[entry.dev]
        property bool expanded: false
        property int tab: 0 // 0 = speed, 1 = details
        property var details: ({})
        readonly property bool hovered: rowMouse.containsMouse || actionBtn.containsMouse || expandBtn.containsMouse

        Layout.fillWidth: true
        implicitHeight: itemCol.implicitHeight + 12
        radius: 4
        color: item.expanded ? Breeze.accentSubtle : (item.hovered ? Breeze.hover : "transparent")
        border.width: (item.expanded || item.hovered) ? 1 : 0
        border.color: Breeze.accentBorder
        Behavior on color { ColorAnimation { duration: 100 } }

        onAskPasswordChanged: if (askPassword) {
            expanded = true;
            Qt.callLater(() => pwField.input.forceActiveFocus());
        }
        onExpandedChanged: if (expanded && entry.active) detailsProc.running = true

        Process {
            id: detailsProc
            command: ["nmcli", "-t", "-f", "GENERAL.HWADDR,IP4.ADDRESS,IP4.GATEWAY,IP4.DNS,IP6.ADDRESS", "device", "show", item.entry.dev]
            environment: ({ LANG: "C", LC_ALL: "C" })
            stdout: StdioCollector {
                onStreamFinished: {
                    const d = {};
                    for (const line of text.trim().split("\n")) {
                        const i = line.indexOf(":");
                        const k = line.slice(0, i).replace(/\[\d+\]$/, "");
                        const v = line.slice(i + 1).replace(/\\:/g, ":");
                        if (!v) continue;
                        d[k] = d[k] ? d[k] : v; // keep the first address of each kind
                    }
                    item.details = d;
                }
            }
        }

        function statusText() {
            const e = item.entry;
            if (item.busy) return e.active && root.pendingKey === e.key ? "Desconectando…" : "Conectando…";
            if (item.error.length > 0) return item.error;
            if (e.active) {
                if (item.stats) return `Conectado, ⬇ ${root.formatRate(item.stats.rxRate)}, ⬆ ${root.formatRate(item.stats.txRate)}`;
                return "Conectado";
            }
            if (!item.isWifi) return "Disponible";
            const parts = [e.saved ? "Guardada" : "Disponible", root.securityLabel(e.ap?.security), `${e.ap?.strength ?? 0} %`];
            return parts.join(" · ");
        }

        function itemIcon() {
            const e = item.entry;
            if (!item.isWifi) return e.active ? "network-wired-activated" : "network-wired-disconnected";
            const b = root.signalBucket(e.ap?.strength ?? 0);
            return `network-wireless-${b}${e.ap?.isSecure ? "-locked" : ""}`;
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
                    source: root.icon(item.itemIcon())
                    opacity: item.entry.active ? 1 : 0.8
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignVCenter
                    spacing: 1
                    Text {
                        Layout.fillWidth: true
                        text: item.entry.name
                        textFormat: Text.PlainText
                        elide: Text.ElideRight
                        color: Breeze.text
                        font.family: Breeze.fontFamily
                        font.pixelSize: 13
                        font.weight: item.entry.active ? Font.DemiBold : Font.Normal
                    }
                    Text {
                        Layout.fillWidth: true
                        text: item.statusText()
                        elide: Text.ElideRight
                        color: item.error.length > 0 ? Breeze.negative : (item.entry.active ? Breeze.accent : Breeze.textMuted)
                        font.family: Breeze.fontFamily
                        font.pixelSize: 11
                    }
                }

                Image {
                    id: busyIcon
                    visible: item.busy
                    Layout.preferredWidth: 16
                    Layout.preferredHeight: 16
                    sourceSize: Qt.size(16, 16)
                    source: root.sharedIcon("view-refresh")
                    RotationAnimator on rotation {
                        running: busyIcon.visible
                        from: 0; to: 360
                        duration: 1000
                        loops: Animation.Infinite
                    }
                }

                BreezeButton {
                    id: actionBtn
                    visible: (item.hovered || item.expanded) && !item.busy
                    iconSource: root.sharedIcon(item.entry.active ? "network-disconnect" : "network-connect")
                    label: item.entry.active ? "Desconectar" : "Conectar"
                    onClicked: {
                        if (item.entry.active) root.disconnectEntry(item.entry);
                        else root.connectEntry(item.entry);
                    }
                }

                BreezeToolButton {
                    id: expandBtn
                    implicitWidth: 24
                    implicitHeight: 24
                    iconSource: root.sharedIcon(item.expanded ? "arrow-up" : "arrow-down")
                    onClicked: item.expanded = !item.expanded
                }
            }

            // Password prompt for secured, not yet saved networks
            RowLayout {
                visible: item.expanded && item.askPassword && !item.entry.active
                Layout.fillWidth: true
                Layout.leftMargin: 42
                spacing: 6

                BreezeTextField {
                    id: pwField
                    Layout.fillWidth: true
                    placeholder: "Contraseña…"
                    iconSource: root.icon("object-locked")
                    echoMode: showPw.checked ? TextInput.Normal : TextInput.Password
                    onAccepted: if (text.length > 0) root.connectEntry(item.entry, text)
                }
                BreezeToolButton {
                    id: showPw
                    implicitWidth: 28
                    iconSource: root.icon(checked ? "password-show-off" : "password-show-on")
                    onClicked: checked = !checked
                }
                BreezeButton {
                    enabled: pwField.text.length > 0 && !item.busy
                    label: "Conectar"
                    onClicked: root.connectEntry(item.entry, pwField.text)
                }
            }

            // Active connection: Speed / Details tabs
            ColumnLayout {
                visible: item.expanded && item.entry.active
                Layout.fillWidth: true
                spacing: 6

                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 2
                    BreezeToolButton {
                        label: "Velocidad"
                        checked: item.tab === 0
                        onClicked: item.tab = 0
                    }
                    BreezeToolButton {
                        label: "Detalles"
                        checked: item.tab === 1
                        onClicked: {
                            item.tab = 1;
                            detailsProc.running = true;
                        }
                    }
                }

                ColumnLayout {
                    visible: item.tab === 0
                    Layout.fillWidth: true
                    spacing: 4

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 80
                        radius: 4
                        color: Breeze.inputBg
                        border.width: 1
                        border.color: Breeze.border

                        TrafficGraph {
                            anchors.fill: parent
                            anchors.margins: 2
                            rxHist: item.stats?.rxHist ?? []
                            txHist: item.stats?.txHist ?? []
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 16
                        spacing: 6
                        Rectangle { Layout.preferredWidth: 10; Layout.preferredHeight: 10; radius: 2; color: Breeze.accent }
                        Text {
                            text: `Descarga: ${root.formatRate(item.stats?.rxRate ?? 0)}`
                            color: Breeze.text
                            font.family: Breeze.fontFamily
                            font.pixelSize: 11
                        }
                        Item { Layout.fillWidth: true }
                        Rectangle { Layout.preferredWidth: 10; Layout.preferredHeight: 10; radius: 2; color: Breeze.neutral }
                        Text {
                            text: `Subida: ${root.formatRate(item.stats?.txRate ?? 0)}`
                            color: Breeze.text
                            font.family: Breeze.fontFamily
                            font.pixelSize: 11
                        }
                    }
                }

                GridLayout {
                    visible: item.tab === 1
                    Layout.fillWidth: true
                    Layout.leftMargin: 20
                    columns: 2
                    columnSpacing: 10
                    rowSpacing: 3

                    BreezeDetailKey { text: "Interfaz:" }
                    BreezeDetailValue { text: item.entry.dev }
                    BreezeDetailKey { text: "Dirección IPv4:" }
                    BreezeDetailValue { text: (item.details["IP4.ADDRESS"] ?? "—").replace(/\/\d+$/, "") }
                    BreezeDetailKey { text: "Puerta de enlace:" }
                    BreezeDetailValue { text: item.details["IP4.GATEWAY"] ?? "—" }
                    BreezeDetailKey { text: "DNS:" }
                    BreezeDetailValue { text: item.details["IP4.DNS"] ?? "—" }
                    BreezeDetailKey { visible: !!item.details["IP6.ADDRESS"]; text: "Dirección IPv6:" }
                    BreezeDetailValue { visible: !!item.details["IP6.ADDRESS"]; text: (item.details["IP6.ADDRESS"] ?? "").replace(/\/\d+$/, "") }
                    BreezeDetailKey { text: "Dirección MAC:" }
                    BreezeDetailValue { text: item.details["GENERAL.HWADDR"] ?? "—" }
                    BreezeDetailKey { visible: item.isWifi; text: "Punto de acceso:" }
                    BreezeDetailValue { visible: item.isWifi; text: item.entry.ap?.bssid ?? "—" }
                    BreezeDetailKey { visible: item.isWifi; text: "Frecuencia:" }
                    BreezeDetailValue { visible: item.isWifi; text: `${item.entry.ap?.frequency ?? 0} MHz` }
                    BreezeDetailKey { visible: item.isWifi; text: "Seguridad:" }
                    BreezeDetailValue { visible: item.isWifi; text: root.securityLabel(item.entry.ap?.security) }
                    BreezeDetailKey { visible: item.isWifi; text: "Intensidad:" }
                    BreezeDetailValue { visible: item.isWifi; text: `${item.entry.ap?.strength ?? 0} %` }
                }
            }

            // Not connected: info + forget for saved Wi-Fi
            RowLayout {
                visible: item.expanded && !item.entry.active && !item.askPassword
                Layout.fillWidth: true
                Layout.leftMargin: 42
                Layout.bottomMargin: 2
                spacing: 6
                Text {
                    Layout.fillWidth: true
                    visible: item.isWifi
                    text: item.isWifi ? `${root.securityLabel(item.entry.ap?.security)} · ${item.entry.ap?.frequency ?? 0} MHz · ${item.entry.ap?.bssid ?? ""}` : ""
                    elide: Text.ElideRight
                    color: Breeze.textMuted
                    font.family: Breeze.fontFamily
                    font.pixelSize: 11
                }
                Item { visible: !item.isWifi; Layout.fillWidth: true }
                BreezeButton {
                    visible: item.isWifi && (item.entry.saved ?? false)
                    destructive: true
                    iconSource: root.sharedIcon("edit-delete")
                    label: "Olvidar"
                    onClicked: root.forgetEntry(item.entry)
                }
            }
        }
    }

    // ------------------------------------------------------------------
    // Popup
    // ------------------------------------------------------------------
    BreezePopupWindow {
        opened: root.opened
        anchorX: GlobalStates.plasmaNetworkAnchorX
        screenName: GlobalStates.plasmaNetworkScreen
        namespace: "quickshell:plasmaNetwork"
        popupWidth: 400
        popupHeight: 480
        onCloseRequested: root.close()

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 1
            spacing: 0

            BreezeHeader {
                busy: Network.wifiScanning || root.pendingKey.length > 0

                BreezeSwitch {
                    enabled: !!root.wifiDevice && !root.airplaneMode
                    checked: Network.wifiEnabled
                    onToggled: Network.enableWifi(!Network.wifiEnabled)
                }
                Image {
                    Layout.preferredWidth: 16
                    Layout.preferredHeight: 16
                    sourceSize: Qt.size(16, 16)
                    source: root.icon(Network.wifiEnabled ? "network-wireless-on" : "network-wireless-off")
                }
                Text {
                    text: "Wi-Fi"
                    color: Breeze.text
                    font.family: Breeze.fontFamily
                    font.pixelSize: 12
                }
                Item { Layout.preferredWidth: 6 }
                BreezeSwitch {
                    checked: root.airplaneMode
                    onToggled: root.setAirplaneMode(!root.airplaneMode)
                }
                Image {
                    Layout.preferredWidth: 16
                    Layout.preferredHeight: 16
                    sourceSize: Qt.size(16, 16)
                    source: root.icon(root.airplaneMode ? "network-flightmode-on" : "network-flightmode-off")
                }
                Item { Layout.fillWidth: true }
                BreezeToolButton {
                    iconSource: root.icon("edit-find")
                    checked: root.searchVisible
                    onClicked: {
                        root.searchVisible = !root.searchVisible;
                        if (!root.searchVisible) root.filterText = "";
                        else Qt.callLater(() => searchField.input.forceActiveFocus());
                    }
                }
                BreezeToolButton {
                    iconSource: root.sharedIcon("configure")
                    onClicked: root.openSettings()
                }
            }

            BreezeTextField {
                id: searchField
                visible: root.searchVisible
                Layout.fillWidth: true
                Layout.margins: 6
                Layout.bottomMargin: 0
                placeholder: "Buscar…"
                iconSource: root.icon("edit-find")
                onTextChanged: root.filterText = text
                onEscapePressed: {
                    root.searchVisible = false;
                    root.filterText = "";
                    searchField.text = "";
                }
            }

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                BreezePlaceholder {
                    anchors.centerIn: parent
                    visible: root.airplaneMode
                    iconSource: root.icon("network-flightmode-on")
                    text: "El modo avión está activado"
                    actionLabel: "Desactivar"
                    onTriggered: root.setAirplaneMode(false)
                }

                BreezePlaceholder {
                    anchors.centerIn: parent
                    visible: !root.airplaneMode && root.entries.length === 0
                    iconSource: root.filterText.length > 0 ? root.icon("edit-find")
                        : root.icon(Network.wifiEnabled ? "network-wireless-acquiring" : "network-wireless-off")
                    text: root.filterText.length > 0 ? "No hay coincidencias"
                        : (Network.wifiEnabled ? "Buscando redes…" : "La red inalámbrica está desactivada")
                    actionLabel: (root.filterText.length === 0 && !Network.wifiEnabled && !!root.wifiDevice) ? "Activar Wi-Fi" : ""
                    onTriggered: Network.enableWifi(true)
                }

                Flickable {
                    id: flick
                    anchors.fill: parent
                    anchors.margins: 6
                    visible: !root.airplaneMode && root.entries.length > 0
                    contentHeight: listCol.implicitHeight
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds

                    ColumnLayout {
                        id: listCol
                        width: flick.width
                        spacing: 2

                        BreezeSectionHeader {
                            visible: root.connectedEntries.length > 0
                            title: "Conectadas"
                        }
                        Repeater {
                            model: ScriptModel {
                                objectProp: "key"
                                values: root.connectedEntries
                            }
                            delegate: ConnectionItem {}
                        }

                        BreezeSectionHeader {
                            visible: root.availableEntries.length > 0
                            title: "Disponibles"
                        }
                        Repeater {
                            model: ScriptModel {
                                objectProp: "key"
                                values: root.availableEntries
                            }
                            delegate: ConnectionItem {}
                        }

                        // Wi-Fi radio off but wired present: hint like plasma-nm
                        Text {
                            visible: !Network.wifiEnabled && !!root.wifiDevice && root.filterText.length === 0
                            Layout.fillWidth: true
                            Layout.topMargin: 10
                            horizontalAlignment: Text.AlignHCenter
                            text: "La red inalámbrica está desactivada"
                            color: Breeze.textMuted
                            font.family: Breeze.fontFamily
                            font.pixelSize: 12
                        }
                    }
                }
            }
        }
    }
}
