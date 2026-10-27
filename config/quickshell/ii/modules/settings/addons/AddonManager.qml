import QtQuick
import Quickshell
import Quickshell.Io

// Both pages share transport and state handling. No third-party QML is loaded here.
Scope {
    id: root
    required property string kind
    readonly property string scripts: Quickshell.env("HOME") + "/.config/hypr/scripts/"
    property var data: ({ themes: [], plugins: [], layout: { bar: [] } })
    property var results: []
    property int resultCount: 0
    property int nextOffset: 0
    property string searchedQuery: ""
    property string statusText: ""
    property string searchStatus: ""
    property string lastRepository: ""
    property bool failed: false
    readonly property bool busy: operation.running
    readonly property bool loading: catalog.running
    readonly property bool searching: discovery.running
    readonly property var themes: data.themes ?? []
    readonly property var plugins: data.plugins ?? []
    readonly property int activePlugins: plugins.filter(p => pluginEnabled(p)).length
    readonly property var positions: [
        { name: "Izquierda", icon: "", value: "left" },
        { name: "Antes de la hora", icon: "", value: "center" },
        { name: "Después de la hora", icon: "", value: "centerEnd" },
        { name: "Extremo derecho", icon: "", value: "right" }
    ]
    property bool appendResults: false

    function pluginName(plugin) {
        const names = { "akitaonrails.ai-usagebar": "Uso de IA", "crmne.active-window": "Ventana activa",
            "omarchy.elsewhen": "Relojes del mundo", "crmne.mpris": "Controles multimedia",
            "omarchy.weather": "El tiempo", "crmne.omastats": "OmaStats" };
        return plugin.builtin ? (names[plugin.id] ?? plugin.name) : plugin.name;
    }
    function pluginDescription(plugin) {
        const descriptions = {
            "akitaonrails.ai-usagebar": "Uso y límites de tus asistentes de IA. Requiere el programa ai-usagebar.",
            "crmne.active-window": "El icono y el título de la ventana que estás usando.",
            "omarchy.elsewhen": "La hora de otras ciudades y zonas horarias junto al reloj.",
            "crmne.mpris": "Carátula, canción y controles para tus reproductores multimedia.",
            "omarchy.weather": "El tiempo actual y la previsión de tu ciudad.",
            "crmne.omastats": "Uso de CPU, memoria, red y almacenamiento."
        };
        return plugin.builtin ? (descriptions[plugin.id] ?? plugin.description ?? "") : (plugin.description ?? "");
    }
    function matches(item, query) {
        const haystack = [item.name, item.id, item.description,
            root.kind === "plugins" ? pluginName(item) : "",
            root.kind === "plugins" ? pluginDescription(item) : ""].join(" ").toLowerCase();
        return query.toLowerCase().split(/\s+/).filter(Boolean).every(word => haystack.includes(word));
    }
    function pluginEnabled(plugin) {
        if ((data.layout?.disabled ?? []).includes(plugin.id)) return false;
        return plugin.builtin || (data.layout?.bar ?? []).some(e => e.id === plugin.id);
    }
    function pluginPosition(plugin) {
        return (data.layout?.bar ?? []).find(e => e.id === plugin.id)?.section ?? plugin.defaultSection;
    }
    function resultInstalled(result) {
        return kind === "plugins" ? plugins.some(p => p.id === result.id) : themes.some(t => t.url === result.url);
    }
    function reload() { if (!catalog.running) catalog.running = true; }
    function run(command) {
        if (root.busy) return;
        root.failed = false;
        root.statusText = "Aplicando cambios…";
        operation.command = command;
        operation.running = true;
    }
    function addon(action, argument) {
        if (root.busy) return;
        root.lastRepository = action.startsWith("install-") ? argument : "";
        run(["python3", root.scripts + "bwm-addons.py", action, argument]);
    }
    function search(query, force, append) {
        if (discovery.running) return;
        root.searchStatus = "Consultando el catálogo de Omarchy…";
        root.appendResults = append === true;
        if (!root.appendResults) {
            root.searchedQuery = query;
            root.nextOffset = 0;
            root.results = [];
        }
        let command = ["python3", root.scripts + "bwm-addons.py", "discover", root.kind,
            root.searchedQuery, "--offset", String(root.nextOffset)];
        if (force) command.push("--refresh");
        discovery.command = command;
        discovery.running = true;
    }
    Component.onCompleted: reload()
    Process {
        id: catalog
        command: ["python3", root.scripts + "bwm-addons.py", "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const parsed = JSON.parse(text);
                    if (parsed.ok === false) {
                        root.failed = true;
                        root.statusText = parsed.message;
                    } else root.data = parsed;
                } catch (error) {
                    root.failed = true;
                    root.statusText = "No se pudo leer la lista de instalados.";
                }
            }
        }
    }
    Process {
        id: operation
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const response = JSON.parse(text);
                    root.statusText = response.message ?? "Cambios guardados.";
                    root.failed = response.ok === false;
                } catch (error) {
                    root.statusText = text.trim() || "Cambios guardados.";
                }
            }
        }
        stderr: StdioCollector {
            onStreamFinished: if (text.trim()) {
                root.failed = true;
                root.statusText = text.trim();
            }
        }
        onExited: (exitCode, exitStatus) => {
            if (exitCode !== 0) {
                root.failed = true;
                if (root.statusText === "Aplicando cambios…" || root.statusText === "Cambios guardados.")
                    root.statusText = "No se pudieron guardar los cambios.";
            }
            root.reload();
        }
    }
    Process {
        id: discovery
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const response = JSON.parse(text);
                    root.results = root.appendResults ? root.results.concat(response.results ?? []) : (response.results ?? []);
                    root.resultCount = response.total ?? 0;
                    root.nextOffset = response.nextOffset ?? root.results.length;
                    root.searchStatus = response.message || (root.resultCount === 0 ? "No hay resultados para esta búsqueda." : "");
                } catch (error) {
                    root.searchStatus = "No se pudo consultar el catálogo. Puedes abrir su web o instalar por URL.";
                }
            }
        }
    }
    FileView {
        path: Quickshell.env("HOME") + "/.config/bwm/omarchy-plugins.json"
        watchChanges: true
        printErrors: false
        onFileChanged: root.reload()
    }
    FileView {
        path: Quickshell.env("HOME") + "/.local/state/bwm/omarchy/theme.name"
        watchChanges: true
        printErrors: false
        onFileChanged: root.reload()
    }
}
