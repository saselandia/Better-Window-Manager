import QtQuick
import Quickshell
import Quickshell.Io
import qs.modules.common
import "Catalog.js" as Catalog

// Owned by OmarchyMenu, never a second application or a second config store.
QtObject {
    id: root
    property var options: Config.options
    readonly property var entries: Catalog.entries()
    readonly property var fields: Catalog.fields()
    property int revision: 0
    property var editing: null
    property var page: null
    property string feedback: ""
    property var widgetLayout: null
    property string pendingWidget: ""
    readonly property string pluginScript: Quickshell.env("HOME") + "/.config/hypr/scripts/bwm-plugin.sh"
    property FileView languageFile: FileView {
        path: Quickshell.env("HOME") + "/.config/omarchy/language"
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: { root.revision++; root.changed(); }
    }
    property Process widgetCatalog: Process {
        command: [root.pluginScript, "catalog"]
        stdout: StdioCollector {
            onStreamFinished: {
                try { root.widgetLayout = JSON.parse(text).layout ?? {bar:[]}; root.revision++; root.changed(); } catch (e) { }
            }
        }
    }
    property Process widgetChange: Process {
        onExited: code => {
            root.pendingWidget = "";
            if (code !== 0) root.feedback = "No se pudo cambiar el widget";
            root.refresh();
        }
    }
    property Timer feedbackTimer: Timer { interval: 2500; onTriggered: root.feedback = "" }
    signal changed()
    signal choiceSaved(string fieldId)
    signal focusSearch()

    function route(name) { return Catalog.route(name); }
    function field(id) { return fields.find(f => f.id === id) ?? null; }
    function refresh() { if (!widgetCatalog.running) widgetCatalog.running = true; }
    function value(f) {
        if (f.backend === "language") return (languageFile.text() || "en").trim() || "en";
        if (f.backend === "widget") {
            if (!widgetLayout) return undefined;
            if ((widgetLayout.disabled ?? []).includes(f.widget)) return false;
            return !f.hiddenByDefault || (widgetLayout.shown ?? []).includes(f.widget);
        }
        return Catalog.read(options, f.path);
    }
    function summary(id) {
        const unused = revision;
        const f = field(id);
        if (f) return pendingWidget && f.widget === pendingWidget ? "Aplicando…" : Catalog.summary(f, value(f));
        const parent = fields.find(f => f.choices && id.startsWith(f.id + ".value"));
        if (parent) {
            const i = Number(id.slice((parent.id + ".value").length));
            return parent.choices[i]?.value === value(parent) ? "✓" : "";
        }
        return "";
    }
    function canEdit(id) {
        const f = field(id) ?? fields.find(f => f.choices && id.startsWith(f.id + ".value"));
        return !f || value(f) !== undefined;
    }
    function activate(id) {
        const f = field(id);
        if (f && f.type !== "choice") {
            if (value(f) === undefined) return true;
            if (f.type === "bool") save(f, !value(f));
            else editing = f;
            return true;
        }
        const parent = fields.find(f => f.choices && id.startsWith(f.id + ".value"));
        if (parent) {
            const i = Number(id.slice((parent.id + ".value").length));
            if (!parent.choices[i]) return true;
            save(parent, parent.choices[i].value);
            choiceSaved(parent.id);
            return true;
        }
        const direct = Catalog.pages.find(p => p[1] === id);
        if (direct && !fields.some(f => f.parent === id)) { page = direct; return true; }
        if (id.endsWith(".controls")) {
            const p = Catalog.pages.find(p => p[1] + ".controls" === id);
            if (p) { page = p; return true; }
        }
        return false;
    }
    function save(f, value) {
        if (f.backend === "widget") {
            if (widgetChange.running) return false;
            pendingWidget = f.widget;
            widgetChange.command = [pluginScript, value ? "show" : "hide", f.widget];
            widgetChange.running = true;
            return true;
        }
        if (f.backend === "language") languageFile.setText(value + "\n");
        else if (!Catalog.write(options, f.path, value)) return false;
        revision++;
        feedback = f.label + ": " + Catalog.summary(f, value);
        feedbackTimer.restart();
        changed();
        return true;
    }
    function commit(text) {
        if (!editing) return false;
        const parsed = Catalog.validate(editing, text);
        if (!parsed.ok || !save(editing, parsed.value)) return false;
        editing = null;
        focusSearch();
        return true;
    }
    function validation(text) { return editing ? Catalog.validate(editing, text) : {ok:true}; }
    function back() {
        if (editing) { editing = null; focusSearch(); return true; }
        if (page) { page = null; focusSearch(); return true; }
        return false;
    }
    function reset() { editing = null; page = null; feedback = ""; }
}
