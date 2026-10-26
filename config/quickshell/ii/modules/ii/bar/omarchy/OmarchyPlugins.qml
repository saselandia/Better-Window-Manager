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

    readonly property string layoutPath: Quickshell.env("BWM_OMARCHY_LAYOUT")
        || ((Quickshell.env("XDG_CONFIG_HOME") || (Quickshell.env("HOME") + "/.config")) + "/bwm/omarchy-plugins.json")
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
        // omarchy.media (MPRIS, for the bar's media widget); BWM has its own equivalents of the rest
        if (String(id) === "omarchy.media")
            return mediaServiceLoader.item;
        return null;
    }
    function summon(id, payloadJson) {
        const strId = String(id || "");
        const normId = strId.startsWith("omarchy.") ? strId : ("omarchy." + strId);
        if (normId === "omarchy.speedtest") {
            if (!speedtestLoader.item) speedtestLoader.active = true;
            if (speedtestLoader.item) speedtestLoader.item.open(payloadJson);
            else speedtestLoader.loaded.connect(function() { speedtestLoader.item.open(payloadJson); });
            return true;
        } else if (normId === "omarchy.disk-speedtest") {
            if (!diskSpeedtestLoader.item) diskSpeedtestLoader.active = true;
            if (diskSpeedtestLoader.item) diskSpeedtestLoader.item.open(payloadJson);
            else diskSpeedtestLoader.loaded.connect(function() { diskSpeedtestLoader.item.open(payloadJson); });
            return true;
        } else if (normId === "omarchy.wifiqr") {
            if (!wifiqrLoader.item) wifiqrLoader.active = true;
            if (wifiqrLoader.item) wifiqrLoader.item.open(payloadJson);
            else wifiqrLoader.loaded.connect(function() { wifiqrLoader.item.open(payloadJson); });
            return true;
        } else if (normId === "omarchy.clipboard") {
            if (!clipboardLoader.item) clipboardLoader.active = true;
            if (clipboardLoader.item) clipboardLoader.item.open(payloadJson);
            else clipboardLoader.loaded.connect(function() { clipboardLoader.item.open(payloadJson); });
            return true;
        } else if (normId === "omarchy.emojis") {
            if (!emojisLoader.item) emojisLoader.active = true;
            if (emojisLoader.item) emojisLoader.item.open(payloadJson);
            else emojisLoader.loaded.connect(function() { emojisLoader.item.open(payloadJson); });
            return true;
        } else if (normId === "omarchy.image-picker" || normId === "omarchy.image-selector") {
            if (!imagePickerLoader.item) imagePickerLoader.active = true;
            if (imagePickerLoader.item) imagePickerLoader.item.open(payloadJson);
            else imagePickerLoader.loaded.connect(function() { imagePickerLoader.item.open(payloadJson); });
            return true;
        } else if (normId === "omarchy.reminders") {
            if (!remindersLoader.item) remindersLoader.active = true;
            if (remindersLoader.item) remindersLoader.item.open(payloadJson);
            else remindersLoader.loaded.connect(function() { remindersLoader.item.open(payloadJson); });
            return true;
        }
        console.info(`[OmarchyPlugins] ${id} is an unknown overlay`);
        return false;
    }

    function hide(id) {
        const strId = String(id || "");
        const normId = strId.startsWith("omarchy.") ? strId : ("omarchy." + strId);
        if (normId === "omarchy.speedtest") {
            speedtestLoader.item?.close();
            return true;
        } else if (normId === "omarchy.disk-speedtest") {
            diskSpeedtestLoader.item?.close();
            return true;
        } else if (normId === "omarchy.wifiqr") {
            wifiqrLoader.item?.close();
            return true;
        } else if (normId === "omarchy.clipboard") {
            clipboardLoader.item?.close();
            return true;
        } else if (normId === "omarchy.emojis") {
            emojisLoader.item?.close();
            return true;
        } else if (normId === "omarchy.image-picker" || normId === "omarchy.image-selector") {
            imagePickerLoader.item?.close();
            return true;
        } else if (normId === "omarchy.reminders") {
            remindersLoader.item?.close();
            return true;
        }
        return false;
    }

    function toggle(id, payloadJson) {
        const strId = String(id || "");
        const normId = strId.startsWith("omarchy.") ? strId : ("omarchy." + strId);
        if (normId === "omarchy.speedtest") {
            if (speedtestLoader.item?.opened) root.hide(normId);
            else root.summon(normId, payloadJson || "{}");
            return true;
        } else if (normId === "omarchy.disk-speedtest") {
            if (diskSpeedtestLoader.item?.opened) root.hide(normId);
            else root.summon(normId, payloadJson || "{}");
            return true;
        } else if (normId === "omarchy.wifiqr") {
            if (wifiqrLoader.item?.opened) root.hide(normId);
            else root.summon(normId, payloadJson || "{}");
            return true;
        } else if (normId === "omarchy.clipboard") {
            if (clipboardLoader.item?.opened) root.hide(normId);
            else root.summon(normId, payloadJson || "{}");
            return true;
        } else if (normId === "omarchy.emojis") {
            if (emojisLoader.item?.opened) root.hide(normId);
            else root.summon(normId, payloadJson || "{}");
            return true;
        } else if (normId === "omarchy.image-picker" || normId === "omarchy.image-selector") {
            if (imagePickerLoader.item?.opened) root.hide(normId);
            else root.summon(normId, payloadJson || "{}");
            return true;
        }
        return false;
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
        if (clipboardLoader.active) {
            clipboardLoader.active = false;
            clipboardLoader.active = true;
        }
        if (emojisLoader.active) {
            emojisLoader.active = false;
        }
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

    Loader {
        id: speedtestLoader
        active: false
        source: Qt.resolvedUrl("speedtest/Panel.qml")
        onLoaded: {
            item.shell = root;
            item.manifest = { id: "omarchy.speedtest" };
        }
    }

    Loader {
        id: diskSpeedtestLoader
        active: false
        source: Qt.resolvedUrl("disk-speedtest/Panel.qml")
        onLoaded: {
            item.shell = root;
            item.manifest = { id: "omarchy.disk-speedtest" };
        }
    }

    Loader {
        id: wifiqrLoader
        active: false
        source: Qt.resolvedUrl("wifiqr/Panel.qml")
        onLoaded: {
            item.shell = root;
            item.manifest = { id: "omarchy.wifiqr" };
        }
    }

    Loader {
        id: clipboardLoader
        active: true
        source: Qt.resolvedUrl("clipboard/Clipboard.qml")
        onLoaded: {
            item.shell = root;
            item.manifest = { id: "omarchy.clipboard" };
        }
    }

    Loader {
        id: emojisLoader
        active: false
        source: Qt.resolvedUrl("emojis/Emojis.qml")
        onLoaded: {
            item.shell = root;
            item.manifest = { id: "omarchy.emojis" };
        }
    }

    // Omarchy's media service (shell/plugins/services/media, MIT): players, active one, IPC `media`
    Loader {
        id: mediaServiceLoader
        active: true
        source: Qt.resolvedUrl("media/Service.qml")
        onLoaded: {
            item.shell = root;
        }
    }

    // Omarchy's interactive reminder flow (omarchy-reminder -i), from shell/plugins/reminders (MIT)
    Loader {
        id: remindersLoader
        active: false
        source: Qt.resolvedUrl("reminders/ReminderFlow.qml")
        onLoaded: {
            item.shell = root;
            item.manifest = { id: "omarchy.reminders" };
        }
    }

    Loader {
        id: imagePickerLoader
        active: false
        source: Qt.resolvedUrl("image-picker/ImagePicker.qml")
        onLoaded: {
            item.shell = root;
            item.manifest = { id: "omarchy.image-picker" };
        }
    }

    IpcHandler {
        target: "omarchy.speedtest"
        function open(): void { root.summon("omarchy.speedtest", "{}"); }
        function close(): void { root.hide("omarchy.speedtest"); }
        function toggle(): void { root.toggle("omarchy.speedtest", "{}"); }
    }

    IpcHandler {
        target: "omarchy.disk-speedtest"
        function open(): void { root.summon("omarchy.disk-speedtest", "{}"); }
        function close(): void { root.hide("omarchy.disk-speedtest"); }
        function toggle(): void { root.toggle("omarchy.disk-speedtest", "{}"); }
    }

    IpcHandler {
        target: "omarchy.wifiqr"
        function open(): void { root.summon("omarchy.wifiqr", "{}"); }
        function close(): void { root.hide("omarchy.wifiqr"); }
        function toggle(): void { root.toggle("omarchy.wifiqr", "{}"); }
    }

    IpcHandler {
        target: "omarchy.clipboard"
        function open(): void { root.summon("omarchy.clipboard", "{}"); }
        function close(): void { root.hide("omarchy.clipboard"); }
        function toggle(): void { root.toggle("omarchy.clipboard", "{}"); }
    }

    IpcHandler {
        target: "clipboard"
        function open(): void { root.summon("omarchy.clipboard", "{}"); }
        function close(): void { root.hide("omarchy.clipboard"); }
        function toggle(): void { root.toggle("omarchy.clipboard", "{}"); }
    }

    IpcHandler {
        target: "omarchy.emojis"
        function open(): void { root.summon("omarchy.emojis", "{}"); }
        function close(): void { root.hide("omarchy.emojis"); }
        function toggle(): void { root.toggle("omarchy.emojis", "{}"); }
    }

    IpcHandler {
        target: "emojis"
        function open(): void { root.summon("omarchy.emojis", "{}"); }
        function close(): void { root.hide("omarchy.emojis"); }
        function toggle(): void { root.toggle("omarchy.emojis", "{}"); }
    }

    IpcHandler {
        target: "omarchy.image-picker"
        function open(): void { root.summon("omarchy.image-picker", "{}"); }
        function openPayload(payload: string): void { root.summon("omarchy.image-picker", payload); }
        function close(): void { root.hide("omarchy.image-picker"); }
        function toggle(): void { root.toggle("omarchy.image-picker", "{}"); }
    }

    IpcHandler {
        target: "image-picker"
        function open(): void { root.summon("omarchy.image-picker", "{}"); }
        function openPayload(payload: string): void { root.summon("omarchy.image-picker", payload); }
        function close(): void { root.hide("omarchy.image-picker"); }
        function toggle(): void { root.toggle("omarchy.image-picker", "{}"); }
    }

    IpcHandler {
        target: "shell"
        function summon(id: string, payload: string): void { root.summon(id, payload ?? "{}"); }
        function toggle(id: string, payload: string): void { root.toggle(id, payload ?? "{}"); }
        function hide(id: string): void { root.hide(id); }
    }

    Component.onCompleted: reload()
}
