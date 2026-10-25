pragma Singleton
pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Io

// Host for Omarchy bar plugins in the Retro theme: the part of omarchy-shell that third-party
// plugins talk to (`bar.shell`). Plugins are installed by hypr/scripts/bwm-plugin.sh (like
// `omarchy plugin add`) under ~/.local/share/bwm/omarchy-plugins and placed in
// ~/.config/bwm/omarchy-plugins.json; their QML runs with Omarchy's own qs.Commons / qs.Ui
// (vendored in quickshell/ii/Commons and quickshell/ii/Ui).
//
// Only the Retro bar references this singleton, so the other themes never load a plugin.
Singleton {
    id: root

    readonly property string layoutPath: (Quickshell.env("XDG_CONFIG_HOME") || (Quickshell.env("HOME") + "/.config")) + "/bwm/omarchy-plugins.json"
    readonly property string pluginScript: Quickshell.env("HOME") + "/.config/hypr/scripts/bwm-plugin.sh"

    property var plugins: []          // catalog entries (see bwm-plugin.sh catalog)
    property var layout: ({ bar: [] })
    property var services: ({})       // plugin id -> service object

    // ---- the `bar.shell` surface plugins use ---------------------------------------------
    readonly property var pluginRegistry: ({ plugins: root.plugins })
    readonly property var barConfig: ({ position: "top", layout: root.sectionsLayout() })
    readonly property var appLibrary: null

    function serviceFor(id) {
        return root.services[String(id || "")] ?? null;
    }
    function firstPartyServiceFor(id) {
        return null; // BWM has its own equivalents of omarchy.* services
    }
    function iconPath(name, fallback) {
        return Quickshell.iconPath(String(name || ""), fallback ?? true);
    }
    // A widget saving its own settings (Omarchy writes them inline in shell.json)
    // Changed in place: reassigning `layout` would rebuild every widget (and close the panel
    // the user is using); the reload the file write triggers then finds nothing new.
    function updateEntryInline(moduleName, settings) {
        const copy = JSON.parse(JSON.stringify(settings ?? {}));
        const entries = root.layout.bar ?? (root.layout.bar = []);
        const entry = entries.find(e => e.id === moduleName);
        if (entry)
            entry.settings = copy;
        else // a built-in widget (the clock): kept so its choices survive restarts
            entries.push({ id: moduleName, section: "builtin", settings: copy });
        layoutFile.setText(JSON.stringify(root.layout, null, 2) + "\n");
    }

    // ---- what the Retro bar asks ----------------------------------------------------------
    // Saved settings of a built-in widget (see updateEntryInline)
    function builtinSettings(id) {
        return (root.layout.bar ?? []).find(e => e.id === id)?.settings ?? {};
    }
    function pluginById(id) {
        return root.plugins.find(p => p.id === id) ?? null;
    }
    // Layout entries plus the preinstalled plugins (quickshell/ii/omarchy-plugins) that the user
    // has neither placed nor turned off: those go to their default section.
    function effectiveEntries() {
        const placed = root.layout.bar ?? [];
        const disabled = root.layout.disabled ?? [];
        const extra = root.plugins.filter(p => p.builtin && p.barWidget && !disabled.includes(p.id) && !placed.some(e => e.id === p.id))
            .map(p => ({ id: p.id, section: p.defaultSection, settings: {} }));
        return placed.concat(extra);
    }
    function isEnabled(id) {
        return root.effectiveEntries().some(e => e.id === id);
    }
    // Enabled bar widgets of one section ("left", "center", "right", "clock"), in layout order
    function entriesFor(section) {
        return root.effectiveEntries().filter(e => e.section === section).map(e => {
            const p = root.pluginById(e.id);
            if (!p || !p.barWidget)
                return null;
            return {
                id: p.id,
                source: "file://" + p.barWidget,
                settings: Object.assign({}, p.defaults ?? {}, e.settings ?? {})
            };
        }).filter(e => e !== null);
    }
    function sectionsLayout() {
        const out = { left: [], center: [], centerEnd: [], right: [] };
        for (const e of root.effectiveEntries())
            (out[e.section] ?? out.right).push({ id: e.id });
        return out;
    }

    function reload() {
        catalogProc.running = false;
        catalogProc.running = true;
    }

    // Services (kind "service") of enabled plugins, created once and kept while enabled
    function syncServices() {
        const wanted = {};
        const disabled = root.layout.disabled ?? [];
        for (const p of root.plugins) {
            if (p.service && !disabled.includes(p.id))
                wanted[p.id] = p.service;
        }
        const next = {};
        for (const id in root.services) {
            if (wanted[id])
                next[id] = root.services[id];
            else
                root.services[id]?.destroy();
        }
        for (const id in wanted) {
            if (next[id])
                continue;
            const component = Qt.createComponent("file://" + wanted[id]);
            if (component.status === Component.Ready) {
                next[id] = component.createObject(root);
            } else {
                console.warn(`[OmarchyPlugins] ${id}: service failed to load: ${component.errorString()}`);
            }
        }
        root.services = next;
    }

    Process {
        id: catalogProc
        command: [root.pluginScript, "catalog"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    const layout = data.layout ?? { bar: [] };
                    const plugins = data.plugins ?? [];
                    if (JSON.stringify(plugins) !== JSON.stringify(root.plugins))
                        root.plugins = plugins;
                    if (JSON.stringify(layout) !== JSON.stringify(root.layout))
                        root.layout = layout;
                    root.syncServices();
                } catch (e) {
                    console.warn("[OmarchyPlugins] bad catalog:", e);
                }
            }
        }
    }

    FileView {
        id: layoutFile
        path: root.layoutPath
        watchChanges: true
        printErrors: false
        onFileChanged: root.reload()
    }

    IpcHandler {
        target: "omarchyPlugins"
        function reload(): void {
            root.reload();
        }
    }

    Component.onCompleted: reload()
}
