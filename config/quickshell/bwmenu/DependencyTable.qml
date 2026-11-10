import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "ThemeUtils.js" as Theme

Rectangle {
    id: table
    required property var rows
    required property var style
    property string fontFamily: "sans-serif"
    property string expandedId: ""
    readonly property color baseColor: style.background
    readonly property color surfaceColor: style.surface
    readonly property color ink: Theme.ink(baseColor)
    implicitHeight: contents.implicitHeight + 2
    color: baseColor
    border.color: style.border
    radius: Math.min(style.radius, 7)
    clip: true

    function reference(row) {
        return row.versionPolicy === "commit exacto de Hyprland" ? "Commit exacto" : row.referenceVersion || (row.minimumVersion ? "≥ " + row.minimumVersion : "—");
    }
    function details(row) {
        return [(row.optional ? "Opcional. " : "") + row.why, row.versionReason || "", row.detail || "",
                row.minimumVersion ? "Mínimo compatible: " + row.minimumVersion : "",
                row.testedVersion ? "Probada con " + row.testedVersion : "", "Instalada: " + (row.version || "sin dato")].filter(x => x).join("\n");
    }
    component Cell: Text {
        color: table.ink
        font.family: table.fontFamily
        font.pixelSize: 12
        textFormat: Text.PlainText
        elide: Text.ElideRight
        verticalAlignment: Text.AlignVCenter
    }
    ColumnLayout {
        id: contents
        x: 1
        y: 1
        width: table.width - 2
        spacing: 0
        Rectangle {
            id: tableHeader
            Layout.fillWidth: true
            implicitHeight: 32
            color: table.surfaceColor
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                spacing: 10
                Item { Layout.preferredWidth: 20 }
                Cell { text: "Dependencia"; color: Theme.ink(tableHeader.color); Layout.fillWidth: true; font.bold: true }
                Cell { text: "Instalada"; color: Theme.ink(tableHeader.color); Layout.preferredWidth: table.width > 750 ? 220 : 160; font.bold: true }
                Cell { text: "Referencia BWM"; color: Theme.ink(tableHeader.color); Layout.preferredWidth: 115; font.bold: true }
            }
        }
        Repeater {
            model: table.rows
            ColumnLayout {
                id: entry
                required property var modelData
                required property int index
                Layout.fillWidth: true
                spacing: 0
                Rectangle {
                    id: row
                    Layout.fillWidth: true
                    implicitHeight: 34
                    color: hover.containsMouse || table.expandedId === entry.modelData.id ? table.style.selection : entry.index % 2 ? Theme.mix(table.baseColor, table.surfaceColor, 0.35) : table.baseColor
                    activeFocusOnTab: true
                    Keys.onReturnPressed: table.expandedId = table.expandedId === entry.modelData.id ? "" : entry.modelData.id
                    Keys.onSpacePressed: table.expandedId = table.expandedId === entry.modelData.id ? "" : entry.modelData.id
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: 10
                        StatusLight { state: entry.modelData.versionState || (entry.modelData.status === "ok" ? "ok" : "error"); description: entry.modelData.versionReason || entry.modelData.detail || "" }
                        Cell { text: entry.modelData.label; color: Theme.ink(row.color); Layout.fillWidth: true }
                        Cell { text: ["missing", "pending"].includes(entry.modelData.status) ? "Falta" : entry.modelData.version || "—"; color: Theme.ink(row.color); Layout.preferredWidth: table.width > 750 ? 220 : 160 }
                        Cell { text: table.reference(entry.modelData); color: Theme.ink(row.color); Layout.preferredWidth: 115 }
                    }
                    MouseArea {
                        id: hover
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: { row.forceActiveFocus(); table.expandedId = table.expandedId === entry.modelData.id ? "" : entry.modelData.id; }
                    }
                    ToolTip.visible: hover.containsMouse && table.expandedId !== entry.modelData.id
                    ToolTip.text: entry.modelData.versionReason || entry.modelData.detail || "Ver detalle"
                    ToolTip.delay: 500
                    Rectangle { visible: row.activeFocus; anchors.fill: parent; color: "transparent"; border.color: table.ink; border.width: 1 }
                }
                Rectangle {
                    id: explanationPanel
                    visible: table.expandedId === entry.modelData.id
                    Layout.fillWidth: true
                    implicitHeight: explanation.implicitHeight + 18
                    color: table.surfaceColor
                    Cell {
                        id: explanation
                        x: 42
                        y: 9
                        width: parent.width - 55
                        text: table.details(entry.modelData)
                        color: Theme.ink(explanationPanel.color)
                        font.pixelSize: 11
                        wrapMode: Text.Wrap
                        elide: Text.ElideNone
                        lineHeight: 1.3
                    }
                }
                Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: table.style.border; opacity: 0.6 }
            }
        }
    }
}
