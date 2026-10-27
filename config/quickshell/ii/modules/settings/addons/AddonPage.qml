pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import Quickshell
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.settings.addons

ContentPage {
    id: page
    required property string kind
    readonly property bool themesPage: kind === "themes"
    readonly property var manager: backend
    property int currentView: 0
    property bool showRepository: false
    property string pluginFilter: "all"
    forceWidth: true
    bottomContentPadding: 40

    readonly property var items: (page.themesPage ? backend.themes : backend.plugins).filter(item =>
        backend.matches(item, filterField.text) && (page.themesPage || page.pluginFilter === "all"
            || backend.pluginEnabled(item) === (page.pluginFilter === "on")))

    component ViewButton: RippleButtonWithIcon {
        colBackgroundToggled: Appearance.colors.colSecondaryContainer
        colBackgroundToggledHover: Appearance.colors.colSecondaryContainerHover
    }

    AddonManager { id: backend; kind: page.kind }

    ContentSection {
        title: page.themesPage ? "Temas" : "Plugins"
        icon: page.themesPage ? "palette" : "extension"
        StyledText {
            Layout.fillWidth: true
            wrapMode: Text.Wrap
            text: page.themesPage
                ? "Elige los colores del estilo Retro o descubre un tema de Omarchy. Al aplicar un tema se activa Retro."
                : "Personaliza la barra Retro: activa tus plugins y elige dónde aparecen."
            color: Appearance.colors.colSubtext
        }
        StyledText {
            Layout.fillWidth: true
            text: page.themesPage ? backend.themes.length + " temas instalados · "
                    + (backend.data.themeMode === "dynamic" ? "Paleta del fondo" :
                        (backend.themes.find(t => t.id === backend.data.theme)?.name ?? backend.data.theme ?? ""))
                : backend.activePlugins + (backend.activePlugins === 1 ? " activado · " : " activados · ")
                    + backend.plugins.length + " instalados"
            textFormat: Text.PlainText
            font.pixelSize: Appearance.font.pixelSize.small
            color: Appearance.colors.colPrimary
            wrapMode: Text.Wrap
        }
        Flow {
            Layout.fillWidth: true
            Layout.topMargin: 8
            spacing: 8
            ViewButton {
                materialIcon: "inventory_2"
                mainText: "Instalados"
                toggled: page.currentView === 0
                onClicked: page.currentView = 0
            }
            ViewButton {
                materialIcon: "travel_explore"
                mainText: "Descubrir"
                toggled: page.currentView === 1
                onClicked: {
                    page.currentView = 1;
                    if (backend.results.length === 0) backend.search("", false, false);
                }
            }
            ViewButton {
                materialIcon: "link"
                mainText: "Instalar por URL"
                toggled: page.showRepository
                onClicked: page.showRepository = !page.showRepository
            }
        }
        StyledText {
            visible: backend.statusText !== ""
            Layout.fillWidth: true
            wrapMode: Text.Wrap
            textFormat: Text.PlainText
            text: backend.statusText
            color: backend.failed ? Appearance.colors.colError : Appearance.colors.colPrimary
        }
    }
    ContentSection {
        visible: page.showRepository
        title: "Desde un repositorio"
        icon: "link"
        MaterialTextField {
            id: repository
            Layout.fillWidth: true
            placeholderText: "https://github.com/autor/repositorio"
            enabled: !backend.busy
            wrapMode: TextInput.NoWrap
            onAccepted: if (text.trim() !== "") backend.addon(page.themesPage ? "install-theme" : "install-plugin", text.trim())
        }
        RippleButtonWithIcon {
            materialIcon: "download"
            mainText: backend.busy ? "Instalando…" : (page.themesPage ? "Instalar tema" : "Instalar plugin")
            enabled: !backend.busy && repository.text.trim() !== ""
            onClicked: backend.addon(page.themesPage ? "install-theme" : "install-plugin", repository.text.trim())
        }
    }
    ContentSection {
        visible: page.currentView === 0
        icon: page.themesPage ? "palette" : "widgets"
        title: page.themesPage ? "Tu colección" : "Tus plugins"
        RowLayout {
            Layout.fillWidth: true
            MaterialTextField {
                id: filterField
                Layout.fillWidth: true
                placeholderText: page.themesPage ? "Filtrar temas instalados…" : "Filtrar plugins instalados…"
            }
            RippleButtonWithIcon {
                materialIcon: "refresh"
                mainText: "Actualizar"
                enabled: !backend.busy && !backend.loading
                onClicked: backend.reload()
            }
        }
        ConfigSelectionArray {
            visible: !page.themesPage
            currentValue: page.pluginFilter
            options: [
                { displayName: "Todos", icon: "widgets", value: "all" },
                { displayName: "Activados", icon: "check_circle", value: "on" },
                { displayName: "Desactivados", icon: "pause_circle", value: "off" }
            ]
            onSelected: value => page.pluginFilter = value
        }
        Flow {
            visible: page.themesPage
            Layout.fillWidth: true
            Layout.topMargin: 8
            spacing: 8
            ViewButton {
                materialIcon: "wallpaper"
                mainText: "Paleta del fondo"
                toggled: backend.data.themeMode === "dynamic"
                enabled: !backend.busy
                onClicked: backend.addon("apply-theme", "dynamic")
            }
            RippleButtonWithIcon {
                materialIcon: "view_carousel"
                mainText: "Abrir carrusel"
                enabled: Appearance.isRetro
                onClicked: Quickshell.execDetached([backend.scripts + "omarchy-shims/omarchy-theme-switcher"])
            }
        }
        GridLayout {
            visible: page.themesPage
            Layout.fillWidth: true
            columns: 2
            rowSpacing: 12
            columnSpacing: 12
            Repeater {
                model: page.themesPage ? page.items : []
                delegate: Rectangle {
                    id: themeCard
                    required property var modelData
                    readonly property bool chosen: backend.data.themeMode === "static" && backend.data.theme === modelData.id
                    Layout.fillWidth: true
                    Layout.preferredWidth: (page.baseWidth - 12) / 2
                    implicitHeight: themeContent.implicitHeight + 24
                    radius: Appearance.rounding.small
                    color: Appearance.colors.colLayer2
                    border.width: chosen ? 2 : 0
                    border.color: Appearance.colors.colPrimary

                    ColumnLayout {
                        id: themeContent
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 12
                        spacing: 8
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 128
                            color: themeCard.modelData.colors?.[0] ?? "#202020"
                            clip: true
                            Image {
                                anchors.fill: parent
                                source: themeCard.modelData.preview ? "file://" + themeCard.modelData.preview : ""
                                sourceSize: Qt.size(360, 180)
                                fillMode: Image.PreserveAspectCrop
                                asynchronous: true
                            }
                            StyledText {
                                visible: !themeCard.modelData.preview
                                anchors.centerIn: parent
                                text: "BWM"
                                font.pixelSize: 32
                                font.weight: Font.Bold
                                color: themeCard.modelData.colors?.[2] ?? "white"
                            }
                        }
                        StyledText {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 36
                            text: themeCard.modelData.name
                            textFormat: Text.PlainText
                            font.weight: Font.DemiBold
                            wrapMode: Text.Wrap
                            maximumLineCount: 2
                            elide: Text.ElideRight
                        }
                        Row {
                            spacing: 0
                            Repeater {
                                model: themeCard.modelData.colors ?? []
                                delegate: Rectangle {
                                    required property var modelData
                                    width: 20
                                    height: 8
                                    color: modelData
                                }
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            StyledText {
                                Layout.fillWidth: true
                                text: themeCard.modelData.builtin ? "Incluido" : "Comunidad"
                                color: Appearance.colors.colSubtext
                                font.pixelSize: Appearance.font.pixelSize.small
                            }
                            RippleButtonWithIcon {
                                materialIcon: themeCard.chosen ? "check" : "palette"
                                mainText: themeCard.chosen ? "Elegido" : "Aplicar"
                                enabled: !backend.busy
                                onClicked: backend.addon("apply-theme", themeCard.modelData.id)
                            }
                        }
                    }
                }
            }
        }
        Repeater {
            model: page.themesPage ? [] : page.items
            delegate: Rectangle {
                id: pluginCard
                required property var modelData
                Layout.fillWidth: true
                Layout.topMargin: 8
                implicitHeight: pluginContent.implicitHeight + 24
                radius: Appearance.rounding.small
                color: Appearance.colors.colLayer2
                ColumnLayout {
                    id: pluginContent
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 12
                    spacing: 10
                    RowLayout {
                        Layout.fillWidth: true
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 3
                            StyledText {
                                Layout.fillWidth: true
                                text: backend.pluginName(pluginCard.modelData)
                                textFormat: Text.PlainText
                                font.weight: Font.DemiBold
                                wrapMode: Text.Wrap
                            }
                            StyledText {
                                Layout.fillWidth: true
                                text: (pluginCard.modelData.builtin ? "Incluido" : "Comunidad")
                                    + (pluginCard.modelData.version ? " · v" + pluginCard.modelData.version : "")
                                color: Appearance.colors.colSubtext
                                font.pixelSize: Appearance.font.pixelSize.small
                            }
                        }
                        StyledSwitch {
                            id: enabledSwitch
                            enabled: !backend.busy
                            Binding { target: enabledSwitch; property: "checked"; value: backend.pluginEnabled(pluginCard.modelData) }
                            onClicked: backend.run([backend.scripts + "bwm-plugin.sh",
                                backend.pluginEnabled(pluginCard.modelData) ? "disable" : "enable", pluginCard.modelData.id])
                        }
                    }
                    StyledText {
                        Layout.fillWidth: true
                        text: backend.pluginDescription(pluginCard.modelData)
                        textFormat: Text.PlainText
                        wrapMode: Text.Wrap
                        color: Appearance.colors.colSubtext
                        font.pixelSize: Appearance.font.pixelSize.small
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        visible: !!pluginCard.modelData.barWidget || !pluginCard.modelData.builtin
                        StyledText {
                            visible: !!pluginCard.modelData.barWidget
                            text: "Posición"
                            font.pixelSize: Appearance.font.pixelSize.small
                        }
                        StyledComboBox {
                            visible: !!pluginCard.modelData.barWidget
                            enabled: !backend.busy && backend.pluginEnabled(pluginCard.modelData)
                            Layout.fillWidth: true
                            textRole: "name"
                            model: backend.positions
                            currentIndex: backend.positions.findIndex(p => p.value === backend.pluginPosition(pluginCard.modelData))
                            onActivated: index => backend.run([backend.scripts + "bwm-plugin.sh", "enable", pluginCard.modelData.id,
                                "--section", backend.positions[index].value])
                        }
                        RippleButtonWithIcon {
                            visible: !pluginCard.modelData.builtin
                            materialIcon: "delete"
                            mainText: "Quitar"
                            enabled: !backend.busy
                            onClicked: backend.run([backend.scripts + "bwm-plugin.sh", "remove", pluginCard.modelData.id])
                        }
                    }
                }
            }
        }
        StyledText {
            visible: page.items.length === 0
            text: backend.loading ? "Cargando…" : "No hay resultados con este filtro."
            color: Appearance.colors.colSubtext
            Layout.topMargin: 12
        }
    }
    AddonBrowser {
        visible: page.currentView === 1
        manager: backend
    }
}
