pragma ComponentBehavior: Bound

import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Quickshell
import Quickshell.Widgets
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland

/**
 * Authentic KDE Plasma Kickoff Application Launcher
 * - Anchored right above the bottom taskbar at the bottom-left corner.
 * - Breeze Dark styling (#24292e, accent #3daee9).
 * - Split view: Left Categories sidebar, Right Applications view.
 * - Real-time fast fuzzy search with clear button.
 * - System Places & Quick Favorites.
 * - KDE Plasma Session & Power actions (Lock, Suspend, Reboot, Logout, Shutdown).
 * - Full keyboard navigation (Arrows, Enter, Escape, Tab).
 * - IPC: quickshell -c ii ipc call plasmaKickoff toggle|open|close
 */
Scope {
    id: root

    property bool opened: false
    property string filterText: ""
    property int selectedCategory: 0
    property int selectedAppIndex: 0

    // KDE Plasma Breeze Dark Palette
    readonly property color colPanelBg: "#f024292e"
    readonly property color colSidebarBg: "#1a1e22"
    readonly property color colBorder: "#31363b"
    readonly property color colAccent: "#3daee9"
    readonly property color colAccentHover: "#4fc3f7"
    readonly property color colAccentSubtle: "#283daee9"
    readonly property color colText: "#eff0f1"
    readonly property color colTextMuted: "#a1a9b1"
    readonly property color colHover: "#18ffffff"
    readonly property color colActive: "#2e3daee9"
    readonly property color colInputBg: "#1c2024"

    // Dimensions (Authentic KDE Plasma 6 Kickoff proportions)
    readonly property int kickoffWidth: 650
    readonly property int kickoffHeight: 540
    readonly property int sidebarWidth: 180

    // Categories definition
    readonly property var categories: [
        { id: "favorites", name: "Favoritos", icon: "bookmarks" },
        { id: "all", name: "Todas las aplicaciones", icon: "applications-all" },
        { id: "internet", name: "Internet", icon: "applications-internet", filter: ["Network", "WebBrowser", "Email", "Feed", "InstantMessaging", "Chat", "FileTransfer", "P2P"] },
        { id: "development", name: "Desarrollo", icon: "applications-development", filter: ["Development", "IDE", "Debugger", "Building", "RevisionControl", "Translation", "GUIDesigner"] },
        { id: "office", name: "Oficina", icon: "applications-office", filter: ["Office", "WordProcessor", "Spreadsheet", "Presentation", "Publishing", "Viewer"] },
        { id: "graphics", name: "Gráficos", icon: "applications-graphics", filter: ["Graphics", "2DGraphics", "VectorGraphics", "RasterGraphics", "Photography", "Scanning", "OCR"] },
        { id: "multimedia", name: "Multimedia", icon: "applications-multimedia", filter: ["AudioVideo", "Audio", "Video", "Player", "Recorder", "Midi", "Mixer", "Sequencer"] },
        { id: "system", name: "Sistema", icon: "applications-system", filter: ["System", "Emulator", "FileManager", "TerminalEmulator", "Monitor", "Security"] },
        { id: "utilities", name: "Utilidades", icon: "applications-utilities", filter: ["Utility", "Archiving", "Calculator", "Clock", "TextEditor", "Compression", "FileTools"] },
        { id: "settings", name: "Preferencias", icon: "preferences-system", filter: ["Settings", "DesktopSettings", "HardwareSettings", "PackageManager"] },
        { id: "places", name: "Lugares", icon: "folder" }
    ]

    readonly property var defaultFavorites: [
        "firefox", "firefox-bin", "google-chrome", "brave-browser",
        "org.gnome.Nautilus", "dolphin",
        "kitty", "konsole",
        "code", "antigravity", "antigravity-ide",
        "dev.vencord.Vesktop", "discord",
        "spotify", "org.pulseaudio.pavucontrol"
    ]

    readonly property var places: [
        { name: "Carpeta personal", subtitle: "~", icon: "folder-home", isPlace: true, cmd: ["xdg-open", Quickshell.env("HOME") || "/home/sasel"] },
        { name: "Descargas", subtitle: "~/Descargas", icon: "folder-download", isPlace: true, cmd: ["xdg-open", (Quickshell.env("HOME") || "/home/sasel") + "/Descargas"] },
        { name: "Documentos", subtitle: "~/Documentos", icon: "folder-documents", isPlace: true, cmd: ["xdg-open", (Quickshell.env("HOME") || "/home/sasel") + "/Documentos"] },
        { name: "Imágenes", subtitle: "~/Imágenes", icon: "folder-pictures", isPlace: true, cmd: ["xdg-open", (Quickshell.env("HOME") || "/home/sasel") + "/Imágenes"] },
        { name: "Música", subtitle: "~/Música", icon: "folder-music", isPlace: true, cmd: ["xdg-open", (Quickshell.env("HOME") || "/home/sasel") + "/Música"] },
        { name: "Vídeos", subtitle: "~/Vídeos", icon: "folder-videos", isPlace: true, cmd: ["xdg-open", (Quickshell.env("HOME") || "/home/sasel") + "/Vídeos"] },
        { name: "Papelera", subtitle: "trash:///", icon: "user-trash", isPlace: true, cmd: ["xdg-open", "trash:///"] },
        { name: "Sistema de archivos", subtitle: "/", icon: "drive-harddisk", isPlace: true, cmd: ["xdg-open", "/"] }
    ]

    readonly property var allApps: {
        const list = AppSearch.list ? Array.from(AppSearch.list) : [];
        return list.slice().sort((a, b) => (a.name || "").localeCompare(b.name || ""));
    }

    readonly property var displayedItems: {
        const q = filterText.trim();
        if (q.length > 0) {
            const rawApps = AppSearch.fuzzyQuery(q) || [];
            const apps = Array.from(rawApps).slice(0, 35);
            const ql = q.toLowerCase();
            const matchedPlaces = places.filter(p => p.name.toLowerCase().includes(ql) || p.subtitle.toLowerCase().includes(ql));
            return apps.concat(matchedPlaces);
        }

        const cat = categories[selectedCategory] || categories[0];
        if (cat.id === "favorites") {
            const pinned = (Config.options?.launcher?.pinnedApps || []).map(id => DesktopEntries.byId(id)).filter(e => !!e);
            if (pinned.length > 0) return pinned;
            return allApps.filter(a => defaultFavorites.some(f => (a.id || "").toLowerCase().includes(f.toLowerCase())));
        } else if (cat.id === "all") {
            return allApps;
        } else if (cat.id === "places") {
            return places;
        } else if (cat.filter) {
            return allApps.filter(a => a.categories && a.categories.some(c => cat.filter.indexOf(c) !== -1));
        }
        return [];
    }

    onDisplayedItemsChanged: {
        selectedAppIndex = 0;
    }

    function open() {
        filterText = "";
        selectedCategory = 0;
        selectedAppIndex = 0;
        opened = true;
    }

    function close() {
        opened = false;
        filterText = "";
    }

    function toggle() {
        if (opened) close(); else open();
    }

    function launchItem(item) {
        if (!item) return;
        close();
        if (item.isPlace && item.cmd) {
            Quickshell.execDetached(item.cmd);
        } else if (typeof item.execute === "function") {
            item.execute();
        }
    }

    IpcHandler {
        target: "plasmaKickoff"
        function toggle(): void { root.toggle(); }
        function open(): void { root.open(); }
        function close(): void { root.close(); }
    }

    PanelWindow {
        id: win
        visible: root.opened
        screen: Quickshell.screens.find(s => s.name === Hyprland.focusedMonitor?.name) ?? Quickshell.screens[0]
        color: "transparent"
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "quickshell:plasmaKickoff"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: root.opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
        anchors { top: true; bottom: true; left: true; right: true }

        onVisibleChanged: {
            if (visible) {
                Qt.callLater(() => {
                    searchInput.forceActiveFocus();
                });
            }
        }

        // Click-outside backdrop scrim
        MouseArea {
            anchors.fill: parent
            onClicked: root.close()
        }

        // Kickoff Window Container (Anchored right above bottom panel)
        Rectangle {
            id: kickoffCard
            width: root.kickoffWidth
            height: root.kickoffHeight
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 48
            anchors.left: parent.left
            anchors.leftMargin: 6
            color: root.colPanelBg
            border.width: 1
            border.color: root.colBorder
            radius: 8
            clip: true

            MouseArea { anchors.fill: parent } // Prevent backdrop click through

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                // =============================================================
                // 1. TOP HEADER: Breeze Search Bar
                // =============================================================
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 52
                    color: "transparent"

                    Rectangle {
                        anchors.fill: parent
                        anchors.margins: 8
                        color: root.colInputBg
                        radius: 6
                        border.width: searchInput.activeFocus ? 1.5 : 1
                        border.color: searchInput.activeFocus ? root.colAccent : root.colBorder

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 8
                            spacing: 8

                            IconImage {
                                Layout.preferredWidth: 18
                                Layout.preferredHeight: 18
                                Layout.alignment: Qt.AlignVCenter
                                source: Quickshell.iconPath("system-search", "edit-find")
                            }

                            TextInput {
                                id: searchInput
                                Layout.fillWidth: true
                                verticalAlignment: TextInput.AlignVCenter
                                color: root.colText
                                font.family: "Google Sans Flex"
                                font.pixelSize: 13
                                clip: true
                                focus: root.opened
                                text: root.filterText

                                onTextChanged: {
                                    if (text !== root.filterText) {
                                        root.filterText = text;
                                    }
                                }

                                Text {
                                    anchors.left: parent.left
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: "Escriba para buscar..."
                                    color: root.colTextMuted
                                    font.family: "Google Sans Flex"
                                    font.pixelSize: 13
                                    visible: !searchInput.text && !searchInput.inputMethodComposing
                                }

                                Keys.onPressed: event => {
                                    const total = root.displayedItems.length;
                                    if (event.key === Qt.Key_Escape) {
                                        if (root.filterText.length > 0) {
                                            root.filterText = "";
                                        } else {
                                            root.close();
                                        }
                                        event.accepted = true;
                                    } else if (event.key === Qt.Key_Down) {
                                        if (total > 0) {
                                            root.selectedAppIndex = Math.min(root.selectedAppIndex + 1, total - 1);
                                            appsList.positionViewAtIndex(root.selectedAppIndex, ListView.Contain);
                                        }
                                        event.accepted = true;
                                    } else if (event.key === Qt.Key_Up) {
                                        if (total > 0) {
                                            root.selectedAppIndex = Math.max(root.selectedAppIndex - 1, 0);
                                            appsList.positionViewAtIndex(root.selectedAppIndex, ListView.Contain);
                                        }
                                        event.accepted = true;
                                    } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                                        if (total > 0 && root.selectedAppIndex >= 0 && root.selectedAppIndex < total) {
                                            root.launchItem(root.displayedItems[root.selectedAppIndex]);
                                        }
                                        event.accepted = true;
                                    }
                                }
                            }

                            // Clear button (✕)
                            MouseArea {
                                Layout.preferredWidth: 24
                                Layout.preferredHeight: 24
                                Layout.alignment: Qt.AlignVCenter
                                visible: root.filterText.length > 0
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    root.filterText = "";
                                    searchInput.forceActiveFocus();
                                }

                                Rectangle {
                                    anchors.centerIn: parent
                                    width: 18
                                    height: 18
                                    radius: 9
                                    color: parent.containsMouse ? root.colHover : "transparent"
                                    Text {
                                        anchors.centerIn: parent
                                        text: "✕"
                                        color: root.colTextMuted
                                        font.pixelSize: 11
                                    }
                                }
                            }
                        }
                    }
                }

                // Divider line below search
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: root.colBorder
                }

                // =============================================================
                // 2. CENTER: Split View (Categories Left + Apps Right)
                // =============================================================
                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 0

                    // ---------------------------------------------------------
                    // Left Column: Categories Sidebar
                    // ---------------------------------------------------------
                    Rectangle {
                        Layout.preferredWidth: root.sidebarWidth
                        Layout.fillHeight: true
                        color: root.colSidebarBg

                        ListView {
                            id: categoriesList
                            anchors.fill: parent
                            anchors.topMargin: 4
                            anchors.bottomMargin: 4
                            clip: true
                            model: root.categories

                            delegate: MouseArea {
                                id: catMouse
                                width: categoriesList.width
                                height: 36
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor

                                readonly property bool isSelected: root.selectedCategory === index && root.filterText.length === 0

                                Rectangle {
                                    anchors.fill: parent
                                    anchors.leftMargin: 4
                                    anchors.rightMargin: 4
                                    radius: 4
                                    color: catMouse.isSelected ? root.colActive : (catMouse.containsMouse ? root.colHover : "transparent")
                                    border.width: catMouse.isSelected ? 1 : 0
                                    border.color: "#333daee9"

                                    // Left vertical accent stripe on active category (KDE Plasma signature)
                                    Rectangle {
                                        anchors.left: parent.left
                                        anchors.verticalCenter: parent.verticalCenter
                                        width: 3
                                        height: 18
                                        radius: 1.5
                                        color: root.colAccent
                                        visible: catMouse.isSelected
                                    }

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 10
                                        anchors.rightMargin: 8
                                        spacing: 10

                                        IconImage {
                                            Layout.preferredWidth: 20
                                            Layout.preferredHeight: 20
                                            Layout.alignment: Qt.AlignVCenter
                                            source: Quickshell.iconPath(modelData.icon, "applications-other")
                                        }

                                        Text {
                                            Layout.fillWidth: true
                                            Layout.alignment: Qt.AlignVCenter
                                            text: modelData.name
                                            color: catMouse.isSelected ? root.colText : (catMouse.containsMouse ? root.colText : root.colTextMuted)
                                            font.family: "Google Sans Flex"
                                            font.pixelSize: 13
                                            font.weight: catMouse.isSelected ? Font.DemiBold : Font.Normal
                                            elide: Text.ElideRight
                                        }
                                    }
                                }

                                onClicked: {
                                    root.selectedCategory = index;
                                    root.filterText = "";
                                    root.selectedAppIndex = 0;
                                    searchInput.forceActiveFocus();
                                }
                            }
                        }
                    }

                    // Vertical Divider
                    Rectangle {
                        Layout.preferredWidth: 1
                        Layout.fillHeight: true
                        color: root.colBorder
                    }

                    // ---------------------------------------------------------
                    // Right Column: Applications List / Search Results
                    // ---------------------------------------------------------
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        ListView {
                            id: appsList
                            anchors.fill: parent
                            anchors.margins: 4
                            clip: true
                            spacing: 2
                            model: root.displayedItems

                            delegate: MouseArea {
                                id: appMouse
                                width: appsList.width
                                height: 48
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor

                                readonly property bool isSelected: root.selectedAppIndex === index

                                Rectangle {
                                    anchors.fill: parent
                                    radius: 5
                                    color: appMouse.isSelected ? root.colActive : (appMouse.containsMouse ? root.colHover : "transparent")
                                    border.width: appMouse.isSelected ? 1 : 0
                                    border.color: root.colAccent

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 10
                                        anchors.rightMargin: 10
                                        spacing: 12

                                        // App Icon
                                        IconImage {
                                            Layout.preferredWidth: 32
                                            Layout.preferredHeight: 32
                                            Layout.alignment: Qt.AlignVCenter
                                            source: modelData.isPlace
                                                ? Quickshell.iconPath(modelData.icon, "folder")
                                                : (modelData.icon ? Quickshell.iconPath(modelData.icon, "application-x-executable") : Quickshell.iconPath(AppSearch.guessIcon(modelData.id), "application-x-executable"))
                                        }

                                        // App Title & Generic Name Subtitle
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Layout.alignment: Qt.AlignVCenter
                                            spacing: 1

                                            Text {
                                                Layout.fillWidth: true
                                                text: modelData.name || ""
                                                color: root.colText
                                                font.family: "Google Sans Flex"
                                                font.pixelSize: 13
                                                font.weight: Font.DemiBold
                                                elide: Text.ElideRight
                                            }

                                            Text {
                                                Layout.fillWidth: true
                                                text: modelData.isPlace ? modelData.subtitle : (modelData.genericName || modelData.comment || "")
                                                color: root.colTextMuted
                                                font.family: "Google Sans Flex"
                                                font.pixelSize: 11
                                                elide: Text.ElideRight
                                                visible: text.length > 0
                                            }
                                        }
                                    }
                                }

                                onEntered: {
                                    root.selectedAppIndex = index;
                                }

                                onClicked: {
                                    root.launchItem(modelData);
                                }
                            }

                            // Empty state indicator
                            Text {
                                anchors.centerIn: parent
                                text: root.filterText.length > 0 ? "No se encontraron aplicaciones" : "No hay aplicaciones en esta categoría"
                                color: root.colTextMuted
                                font.family: "Google Sans Flex"
                                font.pixelSize: 13
                                visible: root.displayedItems.length === 0
                            }
                        }
                    }
                }

                // Divider line above footer
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: root.colBorder
                }

                // =============================================================
                // 3. BOTTOM FOOTER: User Profile & KDE Plasma Session Actions
                // =============================================================
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 48
                    color: root.colSidebarBg

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: 8

                        // User Avatar & Name
                        RowLayout {
                            Layout.alignment: Qt.AlignVCenter
                            spacing: 8

                            Rectangle {
                                width: 28
                                height: 28
                                radius: 14
                                color: root.colActive
                                border.width: 1
                                border.color: root.colAccent

                                IconImage {
                                    anchors.centerIn: parent
                                    implicitSize: 16
                                    source: Quickshell.iconPath("user-identity", "avatar-default")
                                }
                            }

                            Text {
                                text: Quickshell.env("USER") || "sasel"
                                color: root.colText
                                font.family: "Google Sans Flex"
                                font.pixelSize: 13
                                font.weight: Font.DemiBold
                            }
                        }

                        Item { Layout.fillWidth: true } // Spacer

                        // Session Actions (Breeze Icons & Clean actions)
                        RowLayout {
                            Layout.alignment: Qt.AlignVCenter
                            spacing: 4

                            // 1. Lock screen
                            MouseArea {
                                id: lockBtn
                                width: 32
                                height: 32
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    root.close();
                                    Quickshell.execDetached(["quickshell", "-c", "ii", "ipc", "call", "lock", "activate"]);
                                }

                                Rectangle {
                                    anchors.fill: parent
                                    radius: 4
                                    color: lockBtn.containsMouse ? root.colHover : "transparent"
                                    IconImage {
                                        anchors.centerIn: parent
                                        implicitSize: 18
                                        source: Quickshell.iconPath("system-lock-screen", "lock")
                                    }
                                }
                            }

                            // 2. Suspend
                            MouseArea {
                                id: suspBtn
                                width: 32
                                height: 32
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    root.close();
                                    Quickshell.execDetached(["systemctl", "suspend"]);
                                }

                                Rectangle {
                                    anchors.fill: parent
                                    radius: 4
                                    color: suspBtn.containsMouse ? root.colHover : "transparent"
                                    IconImage {
                                        anchors.centerIn: parent
                                        implicitSize: 18
                                        source: Quickshell.iconPath("system-suspend", "system-suspend-symbolic")
                                    }
                                }
                            }

                            // 3. Reboot
                            MouseArea {
                                id: rebBtn
                                width: 32
                                height: 32
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    root.close();
                                    Quickshell.execDetached(["systemctl", "reboot"]);
                                }

                                Rectangle {
                                    anchors.fill: parent
                                    radius: 4
                                    color: rebBtn.containsMouse ? root.colHover : "transparent"
                                    IconImage {
                                        anchors.centerIn: parent
                                        implicitSize: 18
                                        source: Quickshell.iconPath("system-reboot", "system-reboot-symbolic")
                                    }
                                }
                            }

                            // 4. Logout
                            MouseArea {
                                id: logBtn
                                width: 32
                                height: 32
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    root.close();
                                    Quickshell.execDetached(["bash", "-c", "command -v hyprshutdown >/dev/null 2>&1 && hyprshutdown || hyprctl dispatch 'hl.dsp.exit()'"]);
                                }

                                Rectangle {
                                    anchors.fill: parent
                                    radius: 4
                                    color: logBtn.containsMouse ? root.colHover : "transparent"
                                    IconImage {
                                        anchors.centerIn: parent
                                        implicitSize: 18
                                        source: Quickshell.iconPath("system-log-out", "system-log-out-symbolic")
                                    }
                                }
                            }

                            // 5. Shutdown
                            MouseArea {
                                id: shutBtn
                                width: 32
                                height: 32
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    root.close();
                                    Quickshell.execDetached(["systemctl", "poweroff"]);
                                }

                                Rectangle {
                                    anchors.fill: parent
                                    radius: 4
                                    color: shutBtn.containsMouse ? "#33da4453" : "transparent"
                                    IconImage {
                                        anchors.centerIn: parent
                                        implicitSize: 18
                                        source: Quickshell.iconPath("system-shutdown", "system-shutdown-symbolic")
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
