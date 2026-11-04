import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland

// Omarchy's keybindings picker uses its ordinary menu-select surface (800×500).
// Keep the existing cheatsheet IPC/shortcuts while sharing Retro's actual menu.
Scope {
    id: root
    required property var menu
    property var entries: []
    property bool requested: false
    property bool loading: false
    readonly property string requestTag: "bwm.keybindings"
    readonly property bool opened: menu.opened && menu.dmenuRequestTag === requestTag
    signal opening()
    signal commandSelected(var command)
    property bool dispatchCommands: true
    function showEntries(preserveQuery = true) {
        const query = preserveQuery && opened ? menu.filterText : "";
        menu.open(JSON.stringify({mode:"select", requestTag:requestTag, prompt:"Atajos de teclado", width:800, maxHeight:500,
            options:entries.length ? entries.map(row => row.label) : [loading ? "Cargando atajos…" : "No hay atajos disponibles"]}));
        if (query) menu.setFilter(query);
    }
    function open() {
        opening();
        requested = true;
        entries = [];
        loading = true;
        showEntries(false);
        reader.running = true;
    }
    function close() {
        requested = false;
        if (opened) menu.close();
    }
    function toggle() { if (opened) close(); else open(); }
    Connections {
        target: root.menu
        function onSelectionAccepted(tag, value) {
            if (tag !== root.requestTag) return;
            const entry = root.entries.find(row => row.label === value);
            root.requested = false;
            if (!entry || !entry.command?.length) return;
            root.commandSelected(entry.command);
            if (root.dispatchCommands) { dispatchTimer.command = entry.command; dispatchTimer.restart(); }
        }
    }
    Timer {
        id: dispatchTimer
        property var command: []
        interval: 100
        onTriggered: Quickshell.execDetached(command)
    }
    Process {
        id: reader
        command: ["python3", Quickshell.env("HOME")+"/.config/hypr/skins/retro/scripts/keybindings.py"]
        stdout: StdioCollector {
            onStreamFinished: {
                if (!root.requested || !root.opened) return;
                root.loading = false;
                try { root.entries = JSON.parse(text); } catch (error) { root.entries = []; }
                root.showEntries();
            }
        }
    }
    Connections {
        target: Hyprland
        function onRawEvent(event) { if (event.name === "configreloaded" && root.opened) reader.running = true; }
    }
    IpcHandler {
        target: "cheatsheet"
        function open(): void { root.open(); }
        function toggle(): void { root.toggle(); }
        function close(): void { root.close(); }
        function inspect(): string { return JSON.stringify({opened:root.opened,count:root.entries.length}); }
    }
    GlobalShortcut { name:"cheatsheetToggle"; description:"Toggle keybindings"; onPressed:root.toggle() }
    GlobalShortcut { name:"cheatsheetOpen"; description:"Open keybindings"; onPressed:root.open() }
    GlobalShortcut { name:"cheatsheetClose"; description:"Close keybindings"; onPressed:root.close() }
}
