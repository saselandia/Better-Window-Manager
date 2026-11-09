pragma Singleton
pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons as Commons

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
        // In Retro, omarchy-shell's host (omarchyShell/OmarchyShell.qml) owns the services
        if (root.omarchyShell)
            return root.omarchyShell.firstPartyServiceFor(String(id));
        // Outside Retro nothing on the desktop uses Omarchy's first-party services
        return null;
    }

    // omarchy-shell's host while Retro runs it (it registers itself): the bar, its panels and their
    // plugins are its; the menu and the overlays below stay here (summonLocal and the like).
    property var omarchyShell: null
    function summon(id, payloadJson) {
        return root.omarchyShell ? root.omarchyShell.summon(id, payloadJson) : root.summonLocal(id, payloadJson);
    }
    function hide(id) {
        return root.omarchyShell ? root.omarchyShell.hide(id) : root.hideLocal(id);
    }
    function toggle(id, payloadJson) {
        return root.omarchyShell ? root.omarchyShell.toggle(id, payloadJson) : root.toggleLocal(id, payloadJson);
    }
    // The Retro menu (OmarchyMenu), as the omarchy-shell shim does for `shell summon omarchy.menu`
    function menuIpc(method, payload) {
        const args = ["qs", "-c", "ii", "ipc", "call", "omarchyMenu", method];
        if (payload !== undefined)
            args.push(payload);
        Quickshell.execDetached(args);
        return true;
    }
    function summonLocal(id, payloadJson) {
        if (String(id) === "omarchy.menu")
            return root.menuIpc("openPayload", payloadJson || "{}");
        const strId = String(id || "");
        const normId = strId.startsWith("omarchy.") ? strId : ("omarchy." + strId);
        if (normId === "omarchy.clipboard") {
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

    function hideLocal(id) {
        if (String(id) === "omarchy.menu")
            return root.menuIpc("close");
        const strId = String(id || "");
        const normId = strId.startsWith("omarchy.") ? strId : ("omarchy." + strId);
        if (normId === "omarchy.clipboard") {
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

    function toggleLocal(id, payloadJson) {
        if (String(id) === "omarchy.menu")
            return root.menuIpc("toggle");
        const strId = String(id || "");
        const normId = strId.startsWith("omarchy.") ? strId : ("omarchy." + strId);
        if (normId === "omarchy.clipboard") {
            if (clipboardLoader.item?.opened) root.hideLocal(normId);
            else root.summonLocal(normId, payloadJson || "{}");
            return true;
        } else if (normId === "omarchy.emojis") {
            if (emojisLoader.item?.opened) root.hideLocal(normId);
            else root.summonLocal(normId, payloadJson || "{}");
            return true;
        } else if (normId === "omarchy.image-picker" || normId === "omarchy.image-selector") {
            if (imagePickerLoader.item?.opened) root.hideLocal(normId);
            else root.summonLocal(normId, payloadJson || "{}");
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
            if (p.service && !disabled.includes(p.id)
                    && (p.builtin || root.isEnabled(p.id)))
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
        // Omarchy's original image-selector protocol (shell/shell.qml):
        // omarchy-menu-images supplies cached rows and waits for doneFile.
        target: "omarchy.image-selector"
        function open(imageDirs: string, imageRowsB64: string, selectedImage: string,
                      selectionFile: string, doneFile: string,
                      showLabels: string, filterable: string): string {
            const payload = JSON.stringify({
                imageDirs, imageRows: Commons.Util.decodeBase64(imageRowsB64),
                selectedImage, selectionFile, doneFile, showLabels, filterable
            });
            const accepted = root.summon("omarchy.image-picker", payload);
            return accepted && imagePickerLoader.status !== Loader.Error ? "ok" : "unknown";
        }
        function preload(imageRowsB64: string, selectedImage: string,
                         showLabels: string, filterable: string): string {
            imagePickerLoader.item?.preloadRows(Commons.Util.decodeBase64(imageRowsB64),
                                               selectedImage, showLabels, filterable);
            return "ok";
        }
        function cancel(doneFile: string): string {
            if (imagePickerLoader.item) imagePickerLoader.item.closeSelector(doneFile || "");
            return "ok";
        }
        function ping(): string { return "ok"; }
        function inspect(): string {
            const picker = imagePickerLoader.item;
            return JSON.stringify({opened: picker?.opened ?? false,
                count: picker?.imageArray.length ?? 0,
                selected: picker?.currentPath() ?? "",
                ready: picker?.layoutSettled ?? false,
                themeMode: picker?.themeMode ?? false,
                skinMode: picker?.skinMode ?? false});
        }
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

    // The one `shell` target of every skin. In Retro it also answers what omarchy-shell's own does
    // (omarchy-bar, omarchy-plugin…), through its host; elsewhere those say "no-shell".
    IpcHandler {
        target: "shell"
        function summon(id: string, payload: string): void { root.summon(id, payload ?? "{}"); }
        function toggle(id: string, payload: string): void { root.toggle(id, payload ?? "{}"); }
        function hide(id: string): void { root.hide(id); }
        function rescanPlugins(): void { root.omarchyShell?.ipc.rescanPlugins(); }
        function reloadPlugins(): void { root.omarchyShell?.ipc.reloadPlugins(); }
        function reloadConfig(): string { return root.omarchyShell ? root.omarchyShell.ipc.reloadConfig() : "no-shell"; }
        function toggleBarTransparency(): string { return root.omarchyShell ? root.omarchyShell.ipc.toggleBarTransparency() : "no-shell"; }
        function setPluginEnabled(id: string, enabled: string): string { return root.omarchyShell ? root.omarchyShell.ipc.setPluginEnabled(id, enabled) : "no-shell"; }
        function enablePlugin(id: string, placementJson: string): string { return root.omarchyShell ? root.omarchyShell.ipc.enablePlugin(id, placementJson) : "no-shell"; }
        function putBarWidget(id: string, placementJson: string): string { return root.omarchyShell ? root.omarchyShell.ipc.putBarWidget(id, placementJson) : "no-shell"; }
        function moveBarWidget(id: string, placementJson: string): string { return root.omarchyShell ? root.omarchyShell.ipc.moveBarWidget(id, placementJson) : "no-shell"; }
        function setBarWidget(id: string, key: string, valueJson: string, selectorJson: string): string { return root.omarchyShell ? root.omarchyShell.ipc.setBarWidget(id, key, valueJson, selectorJson) : "no-shell"; }
        function listPlugins(): string { return root.omarchyShell ? root.omarchyShell.ipc.listPlugins() : "[]"; }
        function listShellConfig(): string { return root.omarchyShell ? root.omarchyShell.ipc.listShellConfig() : "{}"; }
        function debugBarGeometry(): string { return root.omarchyShell ? root.omarchyShell.ipc.debugBarGeometry() : "[]"; }
        function togglePanelAt(section: string, index: string): string { return root.omarchyShell ? root.omarchyShell.ipc.togglePanelAt(section, index) : "unknown"; }
        function call(id: string, method: string, arg: string): string { return root.omarchyShell ? root.omarchyShell.ipc.call(id, method, arg) : ""; }
    }

    Component.onCompleted: reload()
}
