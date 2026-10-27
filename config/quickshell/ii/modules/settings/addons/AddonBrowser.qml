pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import qs.modules.common
import qs.modules.common.widgets

ContentSection {
    id: root
    required property var manager
    readonly property bool themes: manager.kind === "themes"
    title: themes ? "Descubrir temas" : "Descubrir plugins"
    icon: "travel_explore"

    RowLayout {
        Layout.fillWidth: true
        MaterialTextField {
            id: searchField
            Layout.fillWidth: true
            placeholderText: root.themes ? "Buscar un tema…" : "Nombre, autor o función…"
            onAccepted: root.manager.search(text, false, false)
        }
        RippleButtonWithIcon {
            materialIcon: "search"
            mainText: root.manager.searching ? "Buscando…" : "Buscar"
            enabled: !root.manager.searching
            onClicked: root.manager.search(searchField.text, false, false)
        }
    }
    RowLayout {
        Layout.fillWidth: true
        StyledText {
            Layout.fillWidth: true
            wrapMode: Text.Wrap
            text: root.manager.searchStatus || (root.manager.resultCount > 0
                ? root.manager.resultCount + " resultados · " + root.manager.results.length + " mostrados"
                : "Catálogo de la comunidad de Omarchy")
            color: Appearance.colors.colSubtext
            font.pixelSize: Appearance.font.pixelSize.small
        }
        RippleButtonWithIcon {
            materialIcon: "open_in_new"
            mainText: "Web"
            onClicked: Qt.openUrlExternally(root.themes ? "https://omarchy.org/themes/" : "https://plugins.omarchy.org/")
        }
        RippleButtonWithIcon {
            materialIcon: "refresh"
            mainText: "Actualizar"
            enabled: !root.manager.searching
            onClicked: root.manager.search(searchField.text, true, false)
        }
    }
    Repeater {
        model: root.manager.results
        delegate: Rectangle {
            id: resultCard
            required property var modelData
            Layout.fillWidth: true
            Layout.topMargin: 6
            implicitHeight: cardContent.implicitHeight + 24
            radius: Appearance.rounding.small
            color: Appearance.colors.colLayer2

            ColumnLayout {
                id: cardContent
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 12
                spacing: 8
                RowLayout {
                    Layout.fillWidth: true
                    StyledText {
                        Layout.fillWidth: true
                        wrapMode: Text.Wrap
                        textFormat: Text.PlainText
                        text: resultCard.modelData.name
                        font.weight: Font.DemiBold
                        font.pixelSize: Appearance.font.pixelSize.normal
                    }
                    RippleButtonWithIcon {
                        materialIcon: "open_in_new"
                        mainText: "Ver"
                        onClicked: Qt.openUrlExternally(resultCard.modelData.url)
                    }
                    RippleButtonWithIcon {
                        materialIcon: root.manager.resultInstalled(resultCard.modelData) ? "check" : "download"
                        mainText: root.manager.busy && root.manager.lastRepository === resultCard.modelData.url ? "Instalando…"
                            : (root.manager.resultInstalled(resultCard.modelData) ? "Instalado" : "Instalar")
                        enabled: !root.manager.busy && !root.manager.resultInstalled(resultCard.modelData)
                        onClicked: root.manager.addon(root.themes ? "install-theme" : "install-plugin", resultCard.modelData.url)
                    }
                }
                StyledText {
                    Layout.fillWidth: true
                    wrapMode: Text.Wrap
                    textFormat: Text.PlainText
                    text: resultCard.modelData.description
                    color: Appearance.colors.colSubtext
                    font.pixelSize: Appearance.font.pixelSize.small
                    maximumLineCount: 3
                    elide: Text.ElideRight
                }
                StyledText {
                    visible: root.manager.lastRepository === resultCard.modelData.url && root.manager.statusText !== ""
                    Layout.fillWidth: true
                    wrapMode: Text.Wrap
                    textFormat: Text.PlainText
                    text: root.manager.statusText
                    color: root.manager.failed ? Appearance.colors.colError : Appearance.colors.colPrimary
                }
            }
        }
    }
    RippleButtonWithIcon {
        visible: root.manager.results.length < root.manager.resultCount
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: 10
        materialIcon: "expand_more"
        mainText: root.manager.searching ? "Cargando…" : "Mostrar más"
        enabled: !root.manager.searching
        onClicked: root.manager.search(root.manager.searchedQuery, false, true)
    }
}
