import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Quickshell
import Quickshell.Io
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.common.functions

ContentPage {
    id: root
    forceWidth: true

    property var monitors: []
    property string feedbackMessage: ""
    property bool feedbackIsError: false

    readonly property string managerScript: FileUtils.trimFileProtocol(Directories.home) + "/.config/hypr/scripts/monitor-manager.py"

    function refreshMonitors() {
        listProcess.running = false;
        listProcess.running = true;
    }

    function showFeedback(msg, isError) {
        root.feedbackMessage = msg;
        root.feedbackIsError = !!isError;
        feedbackTimer.restart();
    }

    Timer {
        id: feedbackTimer
        interval: 4000
        onTriggered: root.feedbackMessage = ""
    }

    function setPrimary(index) {
        if (!monitors || index >= monitors.length) return;
        let updated = JSON.parse(JSON.stringify(monitors));
        for (let i = 0; i < updated.length; i++) {
            if (i === index) {
                updated[i].is_primary = true;
                updated[i].workspaces = "1-9";
            } else {
                updated[i].is_primary = false;
                updated[i].workspaces = "10";
            }
        }
        root.monitors = updated;
    }

    function applyConfiguration() {
        if (!monitors || monitors.length === 0) return;
        applyProcess.command = ["python3", root.managerScript, "apply", JSON.stringify(monitors)];
        applyProcess.running = true;
    }

    // Process: List monitors
    Process {
        id: listProcess
        running: true
        command: ["python3", root.managerScript, "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                if (!text || !text.trim()) return;
                try {
                    root.monitors = JSON.parse(text);
                } catch (e) {
                    console.error("[WorkspaceConfig] Error parsing monitors:", e);
                }
            }
        }
    }

    // Process: Apply configuration
    Process {
        id: applyProcess
        stdout: StdioCollector {
            onStreamFinished: {
                root.showFeedback(Translation.tr("Configuración de espacios de trabajo aplicada con éxito"), false);
                root.refreshMonitors();
            }
        }
        stderr: StdioCollector {
            onStreamFinished: {
                if (text && text.trim()) {
                    root.showFeedback(Translation.tr("Error al aplicar configuración: %1").arg(text.trim()), true);
                }
            }
        }
    }

    ContentSection {
        icon: "view_carousel"
        title: Translation.tr("Espacios de Trabajo y Pantalla Principal")

        // Status alert
        Rectangle {
            visible: root.feedbackMessage.length > 0
            Layout.fillWidth: true
            implicitHeight: 40
            radius: Appearance.rounding.small
            color: root.feedbackIsError ? Appearance.colors.colErrorContainer : Appearance.colors.colPrimaryContainer

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                spacing: 10
                MaterialSymbol {
                    text: root.feedbackIsError ? "error" : "check_circle"
                    color: root.feedbackIsError ? Appearance.colors.colOnErrorContainer : Appearance.colors.colOnPrimaryContainer
                }
                StyledText {
                    Layout.fillWidth: true
                    text: root.feedbackMessage
                    font.weight: Font.Medium
                    color: root.feedbackIsError ? Appearance.colors.colOnErrorContainer : Appearance.colors.colOnPrimaryContainer
                }
            }
        }

        // Info box
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: infoLayout.implicitHeight + 20
            radius: Appearance.rounding.small
            color: Appearance.colors.colLayer2
            border.width: 1
            border.color: Appearance.colors.colOutlineVariant

            RowLayout {
                id: infoLayout
                anchors.fill: parent
                anchors.margins: 12
                spacing: 12

                MaterialSymbol {
                    text: "info"
                    iconSize: 24
                    color: Appearance.colors.colPrimary
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 3

                    StyledText {
                        text: Translation.tr("Asignación de Monitores y Workspaces")
                        font.weight: Font.Bold
                        color: Appearance.colors.colOnSurface
                    }

                    StyledText {
                        Layout.fillWidth: true
                        text: Translation.tr("Selecciona qué pantalla actúa como Pantalla Principal para albergar los Workspaces 1 al 9 (atajos Alt+1 a Alt+9). La pantalla secundaria albergará el Workspace 10 (Alt+0).")
                        font.pixelSize: Appearance.font.pixelSize.small
                        color: Appearance.colors.colOnSurfaceVariant
                        wrapMode: Text.Wrap
                    }
                }
            }
        }
    }

    // Monitor cards repeater
    Repeater {
        model: root.monitors

        ContentSection {
            required property int index
            required property var modelData

            icon: (modelData.is_primary ?? false) ? "star" : "desktop_windows"
            title: `${modelData.model || modelData.name} (${modelData.name})`

            // Primary switch
            ConfigSwitch {
                buttonIcon: "star"
                text: Translation.tr("Establecer como Pantalla Principal (Workspaces 1-9)")
                checked: modelData.is_primary ?? false
                onCheckedChanged: {
                    if ((modelData.is_primary ?? false) !== checked) {
                        if (checked) {
                            root.setPrimary(index);
                        } else {
                            // Find another monitor to be primary
                            let updated = JSON.parse(JSON.stringify(root.monitors));
                            updated[index].is_primary = false;
                            updated[index].workspaces = "10";
                            for (let i = 0; i < updated.length; i++) {
                                if (i !== index) {
                                    updated[i].is_primary = true;
                                    updated[i].workspaces = "1-9";
                                    break;
                                }
                            }
                            root.monitors = updated;
                        }
                    }
                }
            }

            // Workspace selector
            ContentSubsection {
                title: Translation.tr("Workspaces Asignados")
                Layout.fillWidth: true

                StyledComboBox {
                    Layout.fillWidth: true
                    buttonIcon: "view_carousel"
                    textRole: "name"
                    model: [
                        { name: Translation.tr("Workspaces 1 al 9 (Principal)"), value: "1-9" },
                        { name: Translation.tr("Workspace 10 (Secundario)"), value: "10" },
                        { name: Translation.tr("Workspaces 1 al 5"), value: "1-5" },
                        { name: Translation.tr("Workspaces 6 al 10"), value: "6-10" }
                    ]
                    currentIndex: {
                        const ws = modelData.workspaces || (modelData.is_primary ? "1-9" : "10");
                        const values = ["1-9", "10", "1-5", "6-10"];
                        const idx = values.indexOf(ws);
                        return idx >= 0 ? idx : (modelData.is_primary ? 0 : 1);
                    }
                    onActivated: function(selIdx) {
                        if (!model || !model[selIdx]) return;
                        const val = model[selIdx].value;
                        let updated = JSON.parse(JSON.stringify(root.monitors));
                        updated[index].workspaces = val;
                        if (val === "1-9") {
                            updated[index].is_primary = true;
                            for (let i = 0; i < updated.length; i++) {
                                if (i !== index && updated[i].is_primary) {
                                    updated[i].is_primary = false;
                                    if (updated[i].workspaces === "1-9") updated[i].workspaces = "10";
                                }
                            }
                        } else if (updated[index].is_primary) {
                            updated[index].is_primary = false;
                        }
                        root.monitors = updated;
                    }
                }
            }

            // Detailed status chip
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: statusRow.implicitHeight + 16
                radius: Appearance.rounding.small
                color: (modelData.is_primary ?? false) ? Appearance.colors.colPrimaryContainer : Appearance.colors.colLayer2

                RowLayout {
                    id: statusRow
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10

                    MaterialSymbol {
                        text: (modelData.is_primary ?? false) ? "verified" : "monitor"
                        iconSize: 20
                        color: (modelData.is_primary ?? false) ? Appearance.colors.colOnPrimaryContainer : Appearance.colors.colOnSurfaceVariant
                    }

                    StyledText {
                        Layout.fillWidth: true
                        text: (modelData.is_primary ?? false) 
                            ? Translation.tr("✓ Pantalla Principal: Atajos Alt+1 a Alt+9 cambiarán a los espacios 1 al 9 en este monitor.")
                            : Translation.tr("✓ Pantalla Secundaria: Atajo Alt+0 cambiará al espacio 10 en este monitor.")
                        font.pixelSize: Appearance.font.pixelSize.small
                        font.weight: Font.Medium
                        color: (modelData.is_primary ?? false) ? Appearance.colors.colOnPrimaryContainer : Appearance.colors.colOnSurfaceVariant
                        wrapMode: Text.Wrap
                    }
                }
            }
        }
    }

    // Action buttons
    RowLayout {
        Layout.fillWidth: true
        Layout.topMargin: 10
        spacing: 12

        RippleButtonWithIcon {
            Layout.fillWidth: true
            materialIcon: "check"
            mainText: Translation.tr("Aplicar y Guardar Cambios")
            colBackground: Appearance.colors.colPrimaryContainer
            onClicked: root.applyConfiguration()
        }

        RippleButtonWithIcon {
            Layout.fillWidth: true
            materialIcon: "refresh"
            mainText: Translation.tr("Detectar Pantallas")
            colBackground: Appearance.colors.colLayer2
            onClicked: root.refreshMonitors()
        }
    }
}
