// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import Quickshell
import Quickshell.Io

// Same R3 transaction as the native KCM: no writes until Apply, revision check and
// readback in native-settings.py. The KCM-shaped API plugs into ModuleView's footer.
QtObject {
    id: store
    property var fields: []
    property var values: ({})
    property string revision: ""
    property string error: ""
    property bool ready: false
    property bool busy: false
    property bool started: false
    property var payload: ({})
    property bool defaultsIndicatorsVisible: false
    readonly property int buttons: 6 // KCModule::Default | Apply
    readonly property bool needsSave: fields.some(f => values[f.key] !== f.value)
    readonly property bool representsDefaults: ready && fields.every(f => values[f.key] === f.default)
    readonly property string backend: Quickshell.env("HOME") + "/.config/hypr/skins/plasma/scripts/native-settings.py"

    function setValue(key, value) { values = Object.assign({}, values, { [key]: value }); }
    function defaults() {
        if (busy || !ready) return;
        const next = {};
        for (const f of fields) next[f.key] = f.default;
        values = next;
    }
    function load() { request("load", {}); }
    function save() {
        if (!ready) return;
        const changes = {};
        for (const f of fields) if (values[f.key] !== f.value) changes[f.key] = values[f.key];
        request("save", { revision: revision, changes: changes });
    }
    function request(action, data) {
        if (busy) return;
        error = "";
        payload = data;
        started = false;
        busy = true;
        worker.command = ["python3", backend, "effects", action];
        worker.stdinEnabled = true;
        worker.running = true;
        deadline.start();
    }
    property Process worker: Process {
        stdout: StdioCollector { id: output }
        onRunningChanged: {
            if (running) {
                store.started = true;
                write(JSON.stringify(store.payload));
                stdinEnabled = false;
            } else if (!store.started && store.busy) {
                store.error = Qt.locale().name.startsWith("es") ? "No se pudo iniciar el controlador de efectos." : "Could not start the effects controller.";
                deadline.stop();
                store.busy = false;
            }
        }
        onExited: (code) => {
            deadline.stop();
            try {
                const response = JSON.parse(output.text);
                if (code !== 0 || !Array.isArray(response.fields) || typeof response.revision !== "string")
                    throw new Error(response.error || "Invalid effects response");
                const next = {};
                for (const f of response.fields) next[f.key] = f.value;
                store.values = next;
                store.revision = response.revision;
                store.fields = response.fields;
                store.ready = true;
            } catch (e) {
                store.error = String(e.message || e);
            }
            store.busy = false;
        }
    }
    property Timer deadline: Timer {
        interval: 60000
        onTriggered: {
            store.error = Qt.locale().name.startsWith("es") ? "El controlador no respondió. Pulsa Restablecer para leer el estado actual." : "The controller timed out. Reset to read the current state.";
            worker.running = false;
            store.busy = false;
        }
    }
    Component.onCompleted: load()
}
