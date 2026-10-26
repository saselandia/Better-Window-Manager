//@ pragma UseQApplication
//@ pragma Env QS_NO_RELOAD_POPUP=1
//@ pragma Env QT_QUICK_CONTROLS_STYLE=Basic
//@ pragma Env QT_QUICK_FLICKABLE_WHEEL_DECELERATION=10000
//@ pragma Env QT_SCALE_FACTOR=1

// KDE Plasma skin settings app, modelled on Plasma 6 "System Settings" (Breeze Dark).
// It loads exactly the same pages as settings.qml (default / Omarchy themes), except the
// taskbar page, which has the Plasma panel options. Options are stored in config.json:
// aesthetic sections are kept per theme and the rest is shared between the three skins
// by bwm-theme-manager.py. Launch: qs -p ~/.config/quickshell/ii/plasmaSettings.qml
// (or open-settings.sh, which picks the right app for the active theme).

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import Quickshell
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.ii.plasmaCommon
import qs.modules.common.functions as CF

ApplicationWindow {
    id: root
    property string filterText: ""
    property var pages: [
        { id: "quick", name: "Ajustes rápidos", icon: "preferences-desktop-theme-global", keywords: "quick rapido tema estilo skin", component: "modules/settings/QuickConfig.qml" },
        { id: "general", name: "General", icon: "preferences-system", keywords: "general audio bateria idioma", component: "modules/settings/GeneralConfig.qml" },
        { id: "bar", name: "Barra de tareas", icon: "preferences-desktop-plasma", keywords: "bar panel barra flotante opaco transparente iconos centrados", component: "modules/settings/PlasmaBarConfig.qml" },
        { id: "background", name: "Fondo de escritorio", icon: "preferences-desktop-wallpaper", keywords: "background wallpaper fondo", component: "modules/settings/BackgroundConfig.qml" },
        { id: "interface", name: "Interfaz", icon: "preferences-desktop-theme-applications", keywords: "interface interfaz dock sidebar overview", component: "modules/settings/InterfaceConfig.qml" },
        { id: "keybinds", name: "Atajos de teclado", icon: "preferences-desktop-keyboard-shortcut", keywords: "keybinds shortcuts atajos teclado", component: "modules/settings/KeybindsConfig.qml" },
        { id: "services", name: "Servicios", icon: "preferences-system-services", keywords: "services servicios ai weather", component: "modules/settings/ServicesConfig.qml" },
        { id: "autostart", name: "Inicio automático", icon: "preferences-system-login", keywords: "autostart inicio arranque", component: "modules/settings/AutostartConfig.qml" },
        { id: "display", name: "Pantalla y monitor", icon: "preferences-desktop-display-randr", keywords: "display pantalla monitor resolucion", component: "modules/settings/DisplayConfig.qml" },
        { id: "workspaces", name: "Escritorios virtuales", icon: "preferences-desktop-virtual", keywords: "workspaces escritorios", component: "modules/settings/WorkspaceConfig.qml" },
        { id: "defaultapps", name: "Aplicaciones predeterminadas", icon: "preferences-desktop-default-applications", keywords: "default apps aplicaciones predeterminadas terminal navegador browser archivos editor gestor de tareas task manager", component: "modules/settings/DefaultAppsConfig.qml" },
        { id: "style", name: "Estilo", icon: "preferences-desktop-font", keywords: "style estilo fonts fuentes tipografia glass translucido salvapantallas screensaver arranque plymouth sddm", component: "modules/settings/StyleConfig.qml" },
        { id: "cursor", name: "Cursores", icon: "preferences-desktop-cursors", keywords: "cursor raton", component: "modules/settings/CursorConfig.qml" },
        { id: "advanced", name: "Avanzado", icon: "preferences-other", keywords: "advanced avanzado", component: "modules/settings/AdvancedConfig.qml" },
        { id: "about", name: "Acerca de este sistema", icon: "hwinfo", keywords: "about acerca info", component: "modules/settings/About.qml" }
    ]
    readonly property var visiblePages: {
        const f = root.filterText.trim().toLowerCase();
        return root.pages.map((p, i) => Object.assign({ index: i }, p))
            .filter(p => f.length === 0 || p.name.toLowerCase().includes(f) || p.keywords.includes(f));
    }
    property int currentPage: 0

    function icon(name) {
        return Breeze.icon("settings", name);
    }

    visible: true
    onClosing: Qt.quit()
    title: "Preferencias del sistema"
    minimumWidth: 800
    minimumHeight: 500
    width: 1100
    height: 750
    color: "#202326"

    Component.onCompleted: {
        // Breeze look for the shared pages (this is its own process, the shell is untouched)
        MaterialThemeLoader.forceBreeze = true;
        Appearance.rounding.unsharpen = 1;
        Appearance.rounding.unsharpenmore = 2;
        Appearance.rounding.verysmall = 3;
        Appearance.rounding.small = 4;
        Appearance.rounding.normal = 5;
        Appearance.rounding.large = 6;
        Appearance.rounding.verylarge = 8;
        Appearance.rounding.windowRounding = 8;
        for (const f of ["main", "title", "numbers", "reading", "expressive"])
            Appearance.font.family[f] = Breeze.fontFamily;
        Config.readWriteDelay = 0; // Settings app always only sets one var at a time
        const pageEnv = Quickshell.env("SETTINGS_PAGE");
        if (pageEnv) {
            const p = pageEnv.toLowerCase();
            const i = root.pages.findIndex(pg => pg.id === p || pg.name.toLowerCase() === p);
            if (i >= 0) root.currentPage = i;
        }
    }

    Shortcut {
        sequences: ["Ctrl+PgDown", "Ctrl+Tab"]
        onActivated: root.currentPage = (root.currentPage + 1) % root.pages.length
    }
    Shortcut {
        sequences: ["Ctrl+PgUp", "Ctrl+Shift+Tab"]
        onActivated: root.currentPage = (root.currentPage - 1 + root.pages.length) % root.pages.length
    }
    Shortcut {
        sequence: "Ctrl+F"
        onActivated: searchField.input.forceActiveFocus()
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // =============================================================
        // Sidebar (System Settings category list)
        // =============================================================
        Rectangle {
            Layout.fillHeight: true
            Layout.preferredWidth: 270
            color: "#202326"

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                // Toolbar with search, same height as the page header
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 46
                    color: Breeze.headerBg

                    BreezeTextField {
                        id: searchField
                        anchors.fill: parent
                        anchors.margins: 8
                        placeholder: "Buscar…"
                        iconSource: root.icon("edit-find")
                        onTextChanged: root.filterText = text
                        onEscapePressed: text = ""
                        onAccepted: if (root.visiblePages.length > 0) root.currentPage = root.visiblePages[0].index
                    }
                    Rectangle {
                        anchors.bottom: parent.bottom
                        width: parent.width
                        height: 1
                        color: Breeze.border
                    }
                }

                ListView {
                    id: categoryList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.margins: 6
                    clip: true
                    spacing: 2
                    boundsBehavior: Flickable.StopAtBounds
                    model: root.visiblePages

                    delegate: MouseArea {
                        id: cat
                        required property var modelData
                        readonly property bool selected: root.currentPage === modelData.index
                        width: ListView.view.width
                        height: 38
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.currentPage = modelData.index

                        Rectangle {
                            anchors.fill: parent
                            radius: 4
                            color: cat.selected ? Breeze.accentSubtle : (cat.containsMouse ? Breeze.hover : "transparent")
                            border.width: (cat.selected || cat.containsMouse) ? 1 : 0
                            border.color: cat.selected ? Breeze.accent : Breeze.accentBorder
                        }

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 8
                            anchors.rightMargin: 8
                            spacing: 10
                            Image {
                                Layout.preferredWidth: 24
                                Layout.preferredHeight: 24
                                sourceSize: Qt.size(24, 24)
                                source: root.icon(cat.modelData.icon)
                            }
                            Text {
                                Layout.fillWidth: true
                                text: cat.modelData.name
                                elide: Text.ElideRight
                                color: Breeze.text
                                font.family: Breeze.fontFamily
                                font.pixelSize: 13
                            }
                        }
                    }

                    Text {
                        anchors.centerIn: parent
                        visible: root.visiblePages.length === 0
                        text: "Sin coincidencias"
                        color: Breeze.textMuted
                        font.family: Breeze.fontFamily
                        font.pixelSize: 13
                    }
                }
            }
        }

        Rectangle {
            Layout.fillHeight: true
            Layout.preferredWidth: 1
            color: Breeze.border
        }

        // =============================================================
        // Page header + page content
        // =============================================================
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 46
                color: Breeze.headerBg

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 16
                    anchors.rightMargin: 8
                    spacing: 8

                    Image {
                        Layout.preferredWidth: 22
                        Layout.preferredHeight: 22
                        sourceSize: Qt.size(22, 22)
                        source: root.icon(root.pages[root.currentPage].icon)
                    }
                    Text {
                        Layout.fillWidth: true
                        text: root.pages[root.currentPage].name
                        color: Breeze.text
                        font.family: Breeze.fontFamily
                        font.pixelSize: 15
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    BreezeToolButton {
                        iconSource: root.icon("document-edit")
                        label: "Archivo de configuración"
                        onClicked: Qt.openUrlExternally(`${Directories.config}/illogical-impulse/config.json`)
                    }
                }
                Rectangle {
                    anchors.bottom: parent.bottom
                    width: parent.width
                    height: 1
                    color: Breeze.border
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: Appearance.m3colors.m3surfaceContainerLow

                Loader {
                    id: pageLoader
                    anchors.fill: parent
                    active: Config.ready
                    source: root.pages[root.currentPage].component

                    // Plasma-like quick fade between pages
                    onSourceChanged: fadeIn.restart()
                    NumberAnimation {
                        id: fadeIn
                        target: pageLoader
                        property: "opacity"
                        from: 0
                        to: 1
                        duration: 150
                        easing.type: Easing.OutCubic
                    }
                }
            }
        }
    }
}
