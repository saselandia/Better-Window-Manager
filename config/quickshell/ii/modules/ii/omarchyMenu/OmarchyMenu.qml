pragma ComponentBehavior: Bound

import qs
import qs.services
import qs.modules.common
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland

/**
 * Omarchy-style launcher menu (Retro theme).
 * - Compact, slim window (cardWidth: 260px, rowHeight: 36px).
 * - Root shows categorized entries ("Apps", "Aprender", "Acciones", "Estilo", "Ajustes", "Sistema").
 * - Typing directly searches individual applications (e.g. "fi" -> Firefox) and actions,
 *   hiding category containers.
 * - IPC: quickshell -c ii ipc call omarchyMenu toggle|open|close
 */
Scope {
    id: root

    property bool opened: false
    property string activeMenu: "root"
    property var navStack: []
    property string filterText: ""
    property int selectedIndex: 0

    // Dynamic Omarchy palette derived from active wallpaper
    readonly property color colBg: Appearance.m3colors.m3background
    readonly property color colFg: Appearance.m3colors.m3onBackground
    readonly property color colAccent: Appearance.m3colors.m3primary
    readonly property color colSelectedBg: Qt.rgba(colAccent.r, colAccent.g, colAccent.b, 0.16)
    readonly property string fontFamily: "JetBrainsMono Nerd Font"

    // Slim, authentic Omarchy dimensions
    readonly property int cardWidth: 260
    readonly property int rowHeight: 36
    readonly property int headerHeight: 32
    readonly property int padding: 12
    readonly property int maxVisibleRows: 10

    function g(cp) { return String.fromCodePoint(cp); }

    readonly property string hypr: "/home/sasel/.config/hypr/scripts"

    // Hierarchical menu tree
    readonly property var menu: ({
        "root": { label: "Go", children: ["apps", "learn", "trigger", "style", "setup", "system"] },
        "apps": { icon: g(0xf003b), label: "Apps", provider: "apps" },
        "learn": { icon: g(0xf09d1), label: "Aprender", children: ["learn.keys", "learn.hyprland", "learn.arch"] },
        "learn.keys": { icon: g(0xf11c), label: "Atajos de teclado", cmd: ["quickshell", "-c", "ii", "ipc", "call", "cheatsheet", "toggle"] },
        "learn.hyprland": { icon: g(0xf359), label: "Hyprland Wiki", cmd: ["xdg-open", "https://wiki.hypr.land/"] },
        "learn.arch": { icon: g(0xf08c7), label: "Arch Wiki", cmd: ["xdg-open", "https://wiki.archlinux.org/"] },
        "trigger": { icon: g(0xf14de), label: "Acciones", children: ["trigger.shot", "trigger.color", "trigger.term", "trigger.files"] },
        "trigger.shot": { icon: g(0xf030), label: "Captura de pantalla", cmd: ["quickshell", "-c", "ii", "ipc", "call", "region", "screenshot"] },
        "trigger.color": { icon: g(0xf00c9), label: "Selector de color", cmd: ["hyprpicker", "-a"] },
        "trigger.term": { icon: g(0xf120), label: "Terminal", cmd: ["kitty"] },
        "trigger.files": { icon: g(0xf07b), label: "Archivos", cmd: ["nautilus"] },
        "style": { icon: g(0xebcf), label: "Estilo", children: ["style.theme", "style.background", "style.toggle"] },
        "style.theme": { icon: g(0xf0e0c), label: "Tema", cmd: [hypr + "/theme-picker.sh"] },
        "style.background": { icon: g(0xf03e), label: "Fondo de pantalla", cmd: [hypr + "/wallpaper-picker.sh"] },
        "style.toggle": { icon: g(0xf0e0c), label: "Alternar Retro / Default", cmd: ["python3", hypr + "/bwm-theme-manager.py", "toggle"] },
        "setup": { icon: g(0xe615), label: "Ajustes", children: ["setup.settings", "setup.quick", "setup.autostart"] },
        "setup.settings": { icon: g(0xe615), label: "Configuración", cmd: ["qs", "-p", "/home/sasel/.config/quickshell/ii/settings.qml"] },
        "setup.quick": { icon: g(0xf1de), label: "Ajustes rápidos", cmd: ["quickshell", "-c", "ii", "ipc", "call", "sidebarRight", "toggle"] },
        "setup.autostart": { icon: g(0xf0e7), label: "Inicio automático", cmd: [hypr + "/open-autostart.sh"] },
        "system": { icon: g(0xf011), label: "Sistema", children: ["system.lock", "system.suspend", "system.logout", "system.reboot", "system.shutdown"] },
        "system.lock": { icon: g(0xf023), label: "Bloquear", cmd: ["quickshell", "-c", "ii", "ipc", "call", "lock", "activate"] },
        "system.suspend": { icon: g(0xf04b2), label: "Suspender", cmd: ["systemctl", "suspend"] },
        "system.logout": { icon: g(0xf0343), label: "Cerrar sesión", cmd: ["bash", "-c", "command -v hyprshutdown >/dev/null 2>&1 && hyprshutdown || hyprctl dispatch 'hl.dsp.exit()'"] },
        "system.reboot": { icon: g(0xf0709), label: "Reiniciar", cmd: ["systemctl", "reboot"] },
        "system.shutdown": { icon: g(0xf0425), label: "Apagar", cmd: ["systemctl", "poweroff"] }
    })

    function appRow(entry) {
        return {
            kind: "app",
            id: "app:" + (entry.id || entry.name),
            label: entry.name,
            icon: "",
            appIcon: entry.icon || "",
            entry: entry,
            detail: ""
        };
    }

    function menuRow(id, withPath) {
        const m = menu[id];
        if (!m) return null;
        const isMenu = !!(m.children || m.provider);
        let detail = "";
        if (withPath) {
            const parentId = id.indexOf(".") > 0 ? id.substring(0, id.lastIndexOf(".")) : "";
            detail = parentId && menu[parentId] ? menu[parentId].label : "";
        }
        return {
            kind: isMenu ? "menu" : "action",
            id: id,
            label: m.label,
            icon: m.icon || "",
            appIcon: "",
            entry: null,
            detail: detail
        };
    }

    readonly property var sortedApps: {
        const list = AppSearch.list ? Array.from(AppSearch.list) : [];
        return list.slice().sort((a, b) => a.name.localeCompare(b.name));
    }

    readonly property var rows: {
        const q = filterText.trim();
        if (q.length > 0) {
            // Search mode: show matching applications and matching actions directly.
            // Category containers ("Apps", "Aprender", etc.) are hidden.
            const ql = q.toLowerCase();
            const rawApps = AppSearch.fuzzyQuery(q) || [];
            const apps = Array.from(rawApps).slice(0, 30).map(e => appRow(e));
            const actions = Object.keys(menu)
                .filter(id => id !== "root" && !menu[id].children && !menu[id].provider)
                .filter(id => menu[id].label.toLowerCase().indexOf(ql) !== -1)
                .map(id => menuRow(id, true))
                .filter(r => r !== null);
            return apps.concat(actions);
        }

        const m = menu[activeMenu];
        if (!m) return [];
        if (m.provider === "apps") {
            return sortedApps.map(e => appRow(e));
        }
        return (m.children || []).map(id => menuRow(id, false)).filter(r => r !== null);
    }

    onRowsChanged: selectedIndex = 0

    function open() {
        activeMenu = "root";
        navStack = [];
        filterText = "";
        selectedIndex = 0;
        opened = true;
    }
    function close() {
        opened = false;
    }
    function toggle() { if (opened) close(); else open(); }

    function enter(id) {
        navStack = navStack.concat([activeMenu]);
        activeMenu = id;
        filterText = "";
    }
    function back() {
        if (navStack.length === 0) { close(); return; }
        activeMenu = navStack[navStack.length - 1];
        navStack = navStack.slice(0, -1);
        filterText = "";
    }

    function activate(row) {
        if (!row) return;
        if (row.kind === "menu") {
            enter(row.id);
            return;
        }
        close();
        if (row.kind === "app") {
            // Terminal apps (btop++, htop...) open in the default terminal (Settings → Default
            // apps, bwm-terminal); DesktopEntry.execute() alone starts them with no terminal
            if (row.entry && row.entry.runInTerminal && row.entry.command && row.entry.command.length > 0) {
                Quickshell.execDetached([Quickshell.env("HOME") + "/.config/hypr/scripts/bwm-terminal", "--"].concat(Array.from(row.entry.command)));
            } else if (row.entry && typeof row.entry.execute === "function") {
                row.entry.execute();
            }
        } else if (menu[row.id] && menu[row.id].cmd) {
            Quickshell.execDetached(menu[row.id].cmd);
        }
    }

    IpcHandler {
        target: "omarchyMenu"
        function toggle(): void { root.toggle(); }
        function open(): void { root.open(); }
        function close(): void { root.close(); }
        function setFilter(text: string): void { root.open(); root.filterText = text; }
        function enterMenu(id: string): void { root.open(); root.enter(id); }
    }

    PanelWindow {
        id: win
        visible: root.opened
        screen: Quickshell.screens.find(s => s.name === Hyprland.focusedMonitor?.name) ?? Quickshell.screens[0]
        color: "transparent"
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "quickshell:omarchyMenu"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: root.opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
        anchors { top: true; bottom: true; left: true; right: true }

        onVisibleChanged: {
            if (visible) {
                Qt.callLater(() => {
                    input.forceActiveFocus();
                });
            }
        }

        // Darkened Scrim (closing on backdrop click)
        Rectangle {
            anchors.fill: parent
            color: Qt.rgba(root.colBg.r, root.colBg.g, root.colBg.b, 0.55)
            MouseArea { anchors.fill: parent; onClicked: root.close() }
        }

        // Slim Omarchy Floating Card
        Rectangle {
            id: card
            width: root.cardWidth
            height: root.padding * 2 + root.headerHeight + 8 + list.height
            anchors.centerIn: parent
            color: root.colBg
            border.width: 2
            border.color: root.colAccent
            radius: 0

            MouseArea { anchors.fill: parent } // swallow inside clicks

            // Header (Filter Search / Navigation Breadcrumb)
            Item {
                id: header
                x: root.padding
                y: root.padding
                width: parent.width - (root.padding * 2)
                height: root.headerHeight

                TextInput {
                    id: input
                    anchors.fill: parent
                    verticalAlignment: TextInput.AlignVCenter
                    color: root.colFg
                    selectionColor: root.colAccent
                    selectedTextColor: root.colBg
                    font.family: root.fontFamily
                    font.pixelSize: 15
                    clip: true
                    focus: root.opened
                    text: root.filterText
                    onTextChanged: {
                        if (text !== root.filterText) root.filterText = text;
                    }

                    Keys.onPressed: event => {
                        const n = root.rows.length;
                        if (event.key === Qt.Key_Escape) {
                            if (root.filterText.length > 0) {
                                root.filterText = "";
                            } else {
                                root.back();
                            }
                            event.accepted = true;
                        } else if (event.key === Qt.Key_Down || (event.key === Qt.Key_Tab && !(event.modifiers & Qt.ShiftModifier)) || (event.key === Qt.Key_J && (event.modifiers & Qt.ControlModifier))) {
                            if (n > 0) root.selectedIndex = (root.selectedIndex + 1) % n;
                            event.accepted = true;
                        } else if (event.key === Qt.Key_Up || event.key === Qt.Key_Backtab || (event.key === Qt.Key_K && (event.modifiers & Qt.ControlModifier))) {
                            if (n > 0) root.selectedIndex = (root.selectedIndex - 1 + n) % n;
                            event.accepted = true;
                        } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                            if (n > 0 && root.selectedIndex >= 0 && root.selectedIndex < n) {
                                root.activate(root.rows[root.selectedIndex]);
                            }
                            event.accepted = true;
                        } else if ((event.key === Qt.Key_Backspace || event.key === Qt.Key_Left) && root.filterText.length === 0) {
                            if (root.navStack.length > 0) root.back();
                            event.accepted = true;
                        } else if (event.key === Qt.Key_Right && root.filterText.length === 0) {
                            if (n > 0 && root.selectedIndex >= 0 && root.selectedIndex < n) {
                                const r = root.rows[root.selectedIndex];
                                if (r && r.kind === "menu") root.enter(r.id);
                            }
                            event.accepted = true;
                        }
                    }
                }

                // Placeholder / Breadcrumb Title
                Text {
                    anchors.fill: parent
                    verticalAlignment: Text.AlignVCenter
                    visible: root.filterText.length === 0
                    text: (root.menu[root.activeMenu] ? root.menu[root.activeMenu].label : "Go") + "…"
                    color: root.colFg
                    opacity: 0.50
                    font.family: root.fontFamily
                    font.pixelSize: 15
                    elide: Text.ElideRight
                }
            }

            // Results / Navigation List
            ListView {
                id: list
                x: root.padding
                y: header.y + header.height + 8
                width: parent.width - (root.padding * 2)
                height: Math.max(root.rowHeight, Math.min(count, root.maxVisibleRows) * (root.rowHeight + 2))
                clip: true
                spacing: 2
                boundsBehavior: Flickable.StopAtBounds
                model: root.rows
                currentIndex: root.selectedIndex
                highlightFollowsCurrentItem: false
                onCurrentIndexChanged: positionViewAtIndex(currentIndex, ListView.Contain)

                delegate: Rectangle {
                    id: row
                    required property var modelData
                    required property int index
                    readonly property bool hasCursor: index === root.selectedIndex
                    width: ListView.view.width
                    height: root.rowHeight
                    radius: 0
                    color: hasCursor ? root.colSelectedBg : "transparent"

                    // Glyph for Categories & Actions
                    Text {
                        id: glyph
                        visible: row.modelData.kind !== "app"
                        text: row.modelData.icon
                        width: 26
                        anchors.left: parent.left
                        anchors.leftMargin: 4
                        anchors.verticalCenter: parent.verticalCenter
                        horizontalAlignment: Text.AlignHCenter
                        color: row.hasCursor ? root.colAccent : root.colFg
                        font.family: root.fontFamily
                        font.pixelSize: 16
                    }

                    // Desktop App Icon
                    Image {
                        visible: row.modelData.kind === "app"
                        width: 18; height: 18
                        anchors.left: parent.left
                        anchors.leftMargin: 8
                        anchors.verticalCenter: parent.verticalCenter
                        sourceSize.width: 36; sourceSize.height: 36
                        asynchronous: true
                        fillMode: Image.PreserveAspectFit
                        source: row.modelData.kind === "app" ? Quickshell.iconPath(AppSearch.guessIcon(row.modelData.appIcon), "image-missing") : ""
                    }

                    // Label and Subtitle/Detail
                    Column {
                        anchors.left: parent.left
                        anchors.leftMargin: 38
                        anchors.right: chevron.left
                        anchors.rightMargin: 4
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 0

                        Text {
                            width: parent.width
                            text: row.modelData.label
                            color: row.hasCursor ? root.colAccent : root.colFg
                            font.family: root.fontFamily
                            font.pixelSize: 14
                            font.weight: Font.Medium
                            elide: Text.ElideRight
                        }
                        Text {
                            width: parent.width
                            visible: row.modelData.detail.length > 0
                            text: row.modelData.detail
                            color: root.colFg
                            opacity: 0.50
                            font.family: root.fontFamily
                            font.pixelSize: 10
                            elide: Text.ElideRight
                        }
                    }

                    // Chevron Indicator for Submenus
                    Text {
                        id: chevron
                        anchors.right: parent.right
                        anchors.rightMargin: 6
                        anchors.verticalCenter: parent.verticalCenter
                        text: row.modelData.kind === "menu" ? "›" : ""
                        color: row.hasCursor ? root.colAccent : root.colFg
                        opacity: row.hasCursor ? 0.70 : 0.35
                        font.family: root.fontFamily
                        font.pixelSize: 15
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onEntered: root.selectedIndex = row.index
                        onClicked: root.activate(row.modelData)
                    }
                }

                // Empty Results Feedback
                Text {
                    anchors.centerIn: parent
                    visible: list.count === 0
                    text: "Sin resultados para \"" + root.filterText + "\""
                    color: root.colFg
                    opacity: 0.70
                    font.family: root.fontFamily
                    font.pixelSize: 13
                }
            }
        }
    }
}
