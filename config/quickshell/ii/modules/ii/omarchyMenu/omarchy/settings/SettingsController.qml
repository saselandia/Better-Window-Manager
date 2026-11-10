import QtQuick
import Quickshell
import Quickshell.Io
import qs.modules.common
import "Catalog.js" as Catalog

// Owned by the Retro menu; Config.options and BWM's managers remain authoritative.
QtObject {
    id: root
    property var options: Config.options
    property string managerScript: Quickshell.env("HOME") + "/.config/hypr/skins/retro/scripts/settings.py"
    property var managerData: ({})
    property var drafts: ({})
    property var queries: ({})
    property var limits: ({})
    readonly property var entries: {
        let rows = Catalog.entries();
        for (const data of Object.values(managerData)) rows = rows.concat(data.entries ?? [], Catalog.fieldEntries(data.fields ?? []));
        return rows;
    }
    readonly property var fields: {
        let list = Catalog.fields();
        for (const data of Object.values(managerData)) list = list.concat(data.fields ?? []);
        return list;
    }
    property int revision: 0
    property var editing: null
    property var page: null
    property string feedback: ""
    property string currentMenu: ""
    property string pendingCategory: ""
    readonly property bool busy: managerChange.running
    readonly property bool loading: managerList.running || searchTimer.running
    property Process managerList: Process {
        property string category: ""
        property string result: ""
        onStarted: result = ""
        stdout: StdioCollector { onStreamFinished: managerList.result = text }
        onExited: code => {
            try {
                const data = JSON.parse(result);
                if (code !== 0 || data.ok === false) throw new Error(data.message);
                const next = Object.assign({}, root.managerData);
                next[category] = data;
                root.managerData = next;
                root.revision++;
                root.catalogChanged();
                if (data.message) root.notify(data.message);
            } catch (error) { root.notify("No se pudo leer la sección"); }
            if (root.pendingCategory) { const next = root.pendingCategory; root.pendingCategory = ""; root.load(next); }
        }
    }
    property Process managerChange: Process {
        property var savedField: null
        property string result: ""
        onStarted: result = ""
        stdout: StdioCollector { onStreamFinished: managerChange.result = text }
        onExited: code => {
            let data = {};
            try { data = JSON.parse(result); } catch (e) { }
            if (code !== 0 || data.ok === false) { root.notify(data.message || "No se pudo guardar"); return; }
            if (savedField.operation === "create") {
                const next = Object.assign({}, root.drafts);
                delete next[savedField.category];
                root.drafts = next;
            }
            root.load(savedField.category, true);
            root.notify("Guardado");
            const route = Catalog.route(savedField.category);
            if (root.currentMenu.startsWith(route) && ["create", "remove", "purge", "add-app"].includes(savedField.operation)) root.navigate(route);
        }
    }
    property Timer feedbackTimer: Timer { interval: 3000; onTriggered: root.feedback = "" }
    property Timer searchTimer: Timer {
        property string category: ""
        interval: 180
        onTriggered: root.load(category)
    }
    signal changed()
    signal catalogChanged()
    signal choiceSaved(string fieldId)
    signal focusSearch()
    signal navigate(string route)

    function notify(text) { feedback = text; feedbackTimer.restart(); changed(); }
    function route(name) { return Catalog.route(name); }
    function resolve(id) { return Catalog.resolve(id); }
    function field(id) { return fields.find(f => f.id === id) ?? null; }
    function isSettings(id) { return id === "setup" || id.startsWith("setup.") || id === "appearance.retro-palette.catalog"; }
    function enter(id) {
        currentMenu = id;
        const p = Catalog.pages.find(p => ["cursor", "defaultapps", "autostart", "keybinds", "plugins", "plugin-catalog", "themes"].includes(p[0]) && (id === p[1] || id.startsWith(p[1] + ".")));
        if (p && (!managerData[p[0]] || id === p[1])) load(p[0]);
    }
    function refresh() { enter(currentMenu); }
    function search(query) {
        const p = Catalog.pages.find(p => ["themes", "plugin-catalog"].includes(p[0]) && currentMenu === p[1]);
        if (!p || (queries[p[0]] ?? "") === query) return;
        queries = Object.assign({}, queries, {[p[0]]:query});
        limits = Object.assign({}, limits, {[p[0]]:60});
        searchTimer.category = p[0];
        searchTimer.restart();
    }
    function load(category, force = false) {
        const command = ["python3", managerScript, "list", category, queries[category] ?? "", String(limits[category] ?? 60)];
        if (managerList.running) {
            if (force || JSON.stringify(managerList.command) !== JSON.stringify(command)) pendingCategory = category;
            return;
        }
        managerList.category = category;
        managerList.command = command;
        managerList.running = true;
    }
    function value(f) {
        if (f.draft) return drafts[f.category]?.[f.key] ?? f.value;
        if (f.backend === "manager") return f.value;
        return Catalog.read(options, f.path);
    }
    function summary(id) {
        const unused = revision;
        const f = field(id);
        if (f) return f.type === "action" ? "" : Catalog.summary(f, value(f));
        const parent = fields.find(f => f.choices && id.startsWith(f.id + ".value"));
        if (parent) {
            const i = Number(id.slice((parent.id + ".value").length));
            return parent.choices[i]?.value === value(parent) ? "✓" : "";
        }
        return "";
    }
    function canEdit(id) {
        const f = field(id) ?? fields.find(f => f.choices && id.startsWith(f.id + ".value"));
        if (f?.showIf && f.showIf !== (drafts[f.category]?.action_type ?? "exec")) return false;
        return !f || f.type === "action" || value(f) !== undefined;
    }
    function activate(id) {
        const f = field(id);
        if (f && f.type !== "choice") {
            if (f.type === "action") save(f, null);
            else if (value(f) === undefined) return true;
            else if (f.type === "bool") save(f, !value(f));
            else editing = f;
            return true;
        }
        const parent = fields.find(f => f.choices && id.startsWith(f.id + ".value"));
        if (parent) {
            const i = Number(id.slice((parent.id + ".value").length));
            if (parent.choices[i] && save(parent, parent.choices[i].value)) choiceSaved(parent.id);
            return true;
        }
        const direct = Catalog.pages.find(p => p[1] === id && !!p[4]);
        if (direct) { page = direct; return true; }
        return false;
    }
    function save(f, value) {
        if (f.operation === "more") {
            limits = Object.assign({}, limits, {[f.category]:(limits[f.category] ?? 60) + 60});
            load(f.category);
            return true;
        } else if (f.draft) {
            const next = Object.assign({}, drafts);
            next[f.category] = Object.assign({}, next[f.category] ?? {}, {[f.key]:value});
            drafts = next;
        } else if (f.backend === "manager") {
            if (busy) return false;
            managerChange.savedField = f;
            managerChange.command = ["python3", managerScript, "save", JSON.stringify(f), JSON.stringify(value), JSON.stringify(drafts[f.category] ?? {})];
            managerChange.running = true;
            return true;
        } else if (!Catalog.write(options, f.path, value)) return false;
        revision++;
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
    function editText(f, v) { return Catalog.editText(f, v); }
    function parseNumber(f, text) { return Catalog.parseNumber(f, text); }
    function validation(text) { return editing ? Catalog.validate(editing, text) : {ok:true}; }
    function back() {
        if (editing) { editing = null; focusSearch(); return true; }
        if (page) { page = null; focusSearch(); return true; }
        return false;
    }
    function reset() { editing = null; page = null; drafts = ({}); queries = ({}); limits = ({}); searchTimer.stop(); feedback = ""; currentMenu = ""; }
}
