//@ pragma UseQApplication
//@ pragma Env QS_NO_RELOAD_POPUP=1
//@ pragma Env QT_QUICK_CONTROLS_STYLE=Basic
//@ pragma Env QT_QUICK_FLICKABLE_WHEEL_DECELERATION=10000
//@ pragma Env QT_SCALE_FACTOR=1

// Ajustes de la skin Retro con el aspecto de Omarchy. Carga exactamente las mismas páginas que
// settings.qml (mismas opciones, mismo config.json), dentro de un marco de Omarchy: cabecera y
// lista como su menú, monoespaciada, esquinas rectas y colores de su paleta (qs.Commons.Color, que
// sigue en vivo al tema de Retro). Dos formas, ambas ventanas flotantes de Hyprland
// (reglas en hypr/modules/omarchy_windows.lua):
//   * ventanita de una página: SETTINGS_PAGE=<id> (menú de Retro → Ajustes → Configuración → …)
//   * ventana completa con la lista de páginas: sin SETTINGS_PAGE (Super+I)
// Teclado, como el menú de Omarchy: ↑/↓ elige página, Intro/→/Tab entra en ella, Esc o Borrar vuelve
// atrás (de la página a la lista, de la lista al menú). Con BWM_SETTINGS_FROM_MENU=<ruta> (lo ponen
// las entradas del menú) al salir se vuelve a abrir el menú en esa ruta, para seguir navegando.
// Lo abre open-settings.sh sólo en Retro; Default usa settings.qml y Plasma plasmaSettings.qml.

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import Quickshell
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.Commons as Om

ApplicationWindow {
    id: root
    property var pages: [
        { id: "general", name: "General", glyph: "󰒓", keywords: "general audio bateria idioma hora", component: "modules/settings/GeneralConfig.qml" },
        { id: "bar", name: "Barra", glyph: "󰍜", keywords: "bar barra widgets plugins idioma", component: "modules/settings/BarConfig.qml" },
        { id: "background", name: "Fondo", glyph: "󰋩", keywords: "background wallpaper fondo", component: "modules/settings/BackgroundConfig.qml" },
        { id: "interface", name: "Interfaz", glyph: "󰕮", keywords: "interface interfaz dock sidebar overview logo", component: "modules/settings/InterfaceConfig.qml" },
        { id: "keybinds", name: "Atajos de teclado", glyph: "󰌌", keywords: "keybinds shortcuts atajos teclado", component: "modules/settings/KeybindsConfig.qml" },
        { id: "services", name: "Servicios", glyph: "󰒋", keywords: "services servicios ia tiempo weather", component: "modules/settings/ServicesConfig.qml" },
        { id: "autostart", name: "Inicio automático", glyph: "󱓞", keywords: "autostart inicio arranque", component: "modules/settings/AutostartConfig.qml" },
        { id: "display", name: "Pantallas", glyph: "󰍹", keywords: "display pantalla monitor resolucion escala", component: "modules/settings/DisplayConfig.qml" },
        { id: "workspaces", name: "Workspaces", glyph: "󰕰", keywords: "workspaces escritorios", component: "modules/settings/WorkspaceConfig.qml" },
        { id: "defaultapps", name: "Aplicaciones predeterminadas", glyph: "󰀻", keywords: "default apps aplicaciones predeterminadas terminal navegador", component: "modules/settings/DefaultAppsConfig.qml" },
        { id: "plugins", name: "Plugins", glyph: "󰐱", keywords: "plugins omarchy extensiones widgets", component: "modules/settings/PluginsConfig.qml" },
        { id: "themes", name: "Temas", glyph: "󰏘", keywords: "temas themes omarchy paleta colores", component: "modules/settings/ThemesConfig.qml" },
        { id: "style", name: "Estilo", glyph: "󰛖", keywords: "style estilo fuentes glass salvapantallas arranque", component: "modules/settings/StyleConfig.qml" },
        { id: "cursor", name: "Cursor", glyph: "󰇀", keywords: "cursor raton", component: "modules/settings/CursorConfig.qml" },
        { id: "about", name: "Acerca de", glyph: "󰋼", keywords: "about acerca info", component: "modules/settings/About.qml" }
    ]
    property string filterText: ""
    readonly property var visiblePages: {
        const f = root.filterText.trim().toLowerCase();
        return root.pages.map((p, i) => Object.assign({ index: i }, p))
            .filter(p => f.length === 0 || p.name.toLowerCase().includes(f) || p.keywords.includes(f));
    }
    property int currentPage: 0
    // Ventanita de una sola página cuando se pide una concreta (como las ventanas flotantes de Omarchy)
    readonly property bool single: (Quickshell.env("SETTINGS_PAGE") ?? "").length > 0
    readonly property string fromMenu: Quickshell.env("BWM_SETTINGS_FROM_MENU") ?? ""

    // Paleta de Omarchy (popups/menú de shell.toml), en vivo con el tema
    readonly property color bg: Om.Color.popups.background
    readonly property color fg: Om.Color.popups.text
    readonly property color accent: Om.Color.accent
    readonly property color muted: Om.Util.alpha(Om.Color.popups.text, 0.55)
    readonly property color line: Om.Util.alpha(Om.Color.popups.text, 0.14)
    readonly property string mono: Om.Style.font.menuFamily

    function inPage() {
        for (let it = root.activeFocusItem; it; it = it.parent)
            if (it === pageLoader) return true;
        return false;
    }
    // Entra en la página: el foco va a su primer control (luego Tab/Shift+Tab los recorre)
    function enterPage() {
        if (!pageLoader.item) return;
        const first = pageLoader.item.nextItemInFocusChain(true);
        (first ?? pageLoader.item).forceActiveFocus();
    }
    // Atrás: buscador con texto → lo vacía; página → lista; lista (o ventanita) → sale y vuelve al menú
    function back() {
        if (!root.single && searchInput.text.length > 0) { searchInput.text = ""; return; }
        if (!root.single && root.inPage()) { pageList.forceActiveFocus(); return; }
        root.leave();
    }
    function leave() {
        if (root.fromMenu.length > 0)
            Quickshell.execDetached(["qs", "-c", "ii", "ipc", "call", "omarchyMenu", "summon", root.fromMenu]);
        Qt.quit();
    }

    function pageIndex(key) {
        const k = (key ?? "").toLowerCase().replace(/[^a-z]/g, "");
        return root.pages.findIndex(p => p.id === k || p.name.toLowerCase().replace(/[^a-z]/g, "") === k);
    }

    visible: true
    onClosing: Qt.quit()
    title: root.single ? `Configuración · ${root.pages[root.currentPage].name}` : "Configuración"
    minimumWidth: root.single ? 640 : 860
    minimumHeight: 460
    width: root.single ? 1000 : 1150
    height: root.single ? 680 : 760
    color: root.bg

    Component.onCompleted: {
        MaterialThemeLoader.reapplyTheme();
        Config.readWriteDelay = 0; // Settings app always only sets one var at a time
        Om.Style.bwmScale = 1.25; // la barra no está en este proceso: tamaño legible como en el menú
        const i = root.pageIndex(Quickshell.env("SETTINGS_PAGE"));
        if (i >= 0) root.currentPage = i;
        if (root.single) focusTimer.start();
        else pageList.forceActiveFocus();
    }
    Timer { id: focusTimer; interval: 150; onTriggered: root.enterPage() }

    // Esc y Borrar vuelven atrás; en un campo de texto Borrar sigue borrando (el campo se queda la tecla)
    Shortcut { sequence: "Escape"; onActivated: root.back() }
    Shortcut { sequence: "Backspace"; onActivated: root.back() }
    Shortcut {
        sequences: ["Ctrl+PgDown", "Ctrl+Tab"]
        enabled: !root.single
        onActivated: root.currentPage = (root.currentPage + 1) % root.pages.length
    }
    Shortcut {
        sequences: ["Ctrl+PgUp", "Ctrl+Shift+Tab"]
        enabled: !root.single
        onActivated: root.currentPage = (root.currentPage - 1 + root.pages.length) % root.pages.length
    }
    Shortcut {
        sequence: "Ctrl+F"
        enabled: !root.single
        onActivated: searchInput.forceActiveFocus()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Cabecera, como la del menú de Omarchy:  Configuración › Página          esc
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 44
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                spacing: 10
                Text {
                    text: "󰒓"
                    color: root.accent
                    font.family: root.mono
                    font.pixelSize: 18
                }
                Text {
                    text: "Configuración"
                    color: root.fg
                    font.family: root.mono
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                }
                Text {
                    visible: root.single
                    text: "›  " + root.pages[root.currentPage].name
                    color: root.accent
                    font.family: root.mono
                    font.pixelSize: 15
                }
                Item { Layout.fillWidth: true }
                Text {
                    text: root.single ? "tab moverse · esc volver al menú"
                        : (root.inPage() ? "tab moverse · esc volver a la lista" : "↑↓ página · intro entrar · ctrl+f buscar · esc salir")
                    color: root.muted
                    font.family: root.mono
                    font.pixelSize: 12
                }
            }
            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: root.line
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // Lista de páginas (sólo en la ventana completa), con las filas del menú de Omarchy
            ColumnLayout {
                visible: !root.single
                Layout.fillHeight: true
                Layout.preferredWidth: 270
                spacing: 6

                Rectangle {
                    Layout.fillWidth: true
                    Layout.margins: 10
                    Layout.bottomMargin: 2
                    Layout.preferredHeight: 34
                    color: "transparent"
                    border.width: 1
                    border.color: searchInput.activeFocus ? root.accent : root.line
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 10
                        spacing: 8
                        Text {
                            text: "❯"
                            color: root.accent
                            font.family: root.mono
                            font.pixelSize: 13
                        }
                        TextInput {
                            id: searchInput
                            Layout.fillWidth: true
                            color: root.fg
                            font.family: root.mono
                            font.pixelSize: 13
                            selectionColor: root.accent
                            clip: true
                            onTextChanged: root.filterText = text
                            Keys.onReturnPressed: {
                                if (root.visiblePages.length > 0) root.currentPage = root.visiblePages[0].index;
                                pageList.forceActiveFocus();
                            }
                            Keys.onDownPressed: pageList.forceActiveFocus()
                            Keys.onEscapePressed: event => {
                                if (text.length > 0) text = "";
                                else pageList.forceActiveFocus();
                                event.accepted = true;
                            }
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                visible: searchInput.text.length === 0
                                text: "Buscar…"
                                color: root.muted
                                font: searchInput.font
                            }
                        }
                    }
                }

                ListView {
                    id: pageList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.leftMargin: 10
                    Layout.rightMargin: 10
                    Layout.bottomMargin: 10
                    clip: true
                    spacing: 2
                    boundsBehavior: Flickable.StopAtBounds
                    model: root.visiblePages
                    keyNavigationEnabled: true
                    currentIndex: Math.max(0, root.visiblePages.findIndex(p => p.index === root.currentPage))
                    onCurrentIndexChanged: if (activeFocus && currentIndex >= 0 && currentIndex < root.visiblePages.length)
                        root.currentPage = root.visiblePages[currentIndex].index
                    Keys.onReturnPressed: root.enterPage()
                    Keys.onEnterPressed: root.enterPage()
                    Keys.onRightPressed: root.enterPage()
                    Keys.onTabPressed: root.enterPage()
                    Keys.onUpPressed: {
                        if (currentIndex <= 0) searchInput.forceActiveFocus();
                        else decrementCurrentIndex();
                    }

                    delegate: MouseArea {
                        id: row
                        required property var modelData
                        readonly property bool selected: root.currentPage === modelData.index
                        readonly property bool keyboardHere: selected && pageList.activeFocus
                        width: ListView.view.width
                        height: 34
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.currentPage = modelData.index

                        Rectangle {
                            anchors.fill: parent
                            color: row.selected ? Om.Color.menu.selectedBackground
                                : (row.containsMouse ? Om.Util.alpha(root.fg, 0.05) : "transparent")
                        }
                        Rectangle { // contorno cuando el teclado está en la lista (como el cursor del menú)
                            anchors.fill: parent
                            visible: row.keyboardHere
                            color: "transparent"
                            border.width: 1
                            border.color: Om.Util.alpha(root.accent, 0.6)
                        }
                        Rectangle { // barra de acento de la fila elegida, como en el menú
                            visible: row.selected
                            width: 3
                            height: parent.height
                            color: root.accent
                        }
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 14
                            anchors.rightMargin: 8
                            spacing: 12
                            Text {
                                Layout.preferredWidth: 20
                                text: row.modelData.glyph
                                color: row.selected ? Om.Color.menu.selectedText : root.fg
                                font.family: root.mono
                                font.pixelSize: 16
                                horizontalAlignment: Text.AlignHCenter
                            }
                            Text {
                                Layout.fillWidth: true
                                text: row.modelData.name
                                elide: Text.ElideRight
                                color: row.selected ? Om.Color.menu.selectedText : root.fg
                                font.family: root.mono
                                font.pixelSize: 13
                            }
                        }
                    }

                    Text {
                        anchors.centerIn: parent
                        visible: root.visiblePages.length === 0
                        text: "Sin coincidencias"
                        color: root.muted
                        font.family: root.mono
                        font.pixelSize: 13
                    }
                }
            }

            Rectangle {
                visible: !root.single
                Layout.fillHeight: true
                Layout.preferredWidth: 1
                color: root.line
            }

            // La página: la misma de settings.qml, sobre el fondo de la paleta
            Loader {
                id: pageLoader
                Layout.fillWidth: true
                Layout.fillHeight: true
                active: Config.ready
                source: root.pages[root.currentPage].component
            }
        }
    }
}
