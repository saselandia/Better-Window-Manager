//@ pragma UseQApplication
//@ pragma AppId org.bwm.menu
//@ pragma Env QS_NO_RELOAD_POPUP=1
//@ pragma Env QT_QUICK_CONTROLS_STYLE=Basic

// Instancia autónoma: no importa la configuración, los servicios ni los paneles de ii.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io

ApplicationWindow {
    id: root
    visible: true
    title: "BWMenu"
    width: 1180
    height: 790
    minimumWidth: 940
    minimumHeight: 640
    color: look.background
    onClosing: event => { if (action.running) event.accepted = false; else Qt.quit(); }
    readonly property string scripts: Quickshell.shellPath("../../hypr/scripts")
    readonly property string previewFile: Quickshell.env("BWM_MENU_PREVIEW") || ""
    readonly property bool previewMode: previewFile.length > 0
    property var look: ({background:"#202326", foreground:"#eff0f1", accent:"#3daee9", onAccent:"#111111",
                         surface:"#31363b", border:"#4d5257", selection:"#26404f", muted:"#a1a9b1", error:"#da4453",
                         font:"sans-serif", radius:12, buttonRadius:8, skins:[], skin:"", skinName:"BWM", themeName:""})
    property var report: ({core:{requires:[], recommends:[]}, skins:[], hyprland:{}, shellPids:[]})
    property string page: "Skins"
    onPageChanged: Qt.callLater(() => { if (pageScroll.contentItem) pageScroll.contentItem.contentY = 0; })
    property string selectedSkin: ""
    property string dependencyGroup: "core"
    property string query: ""
    property string notice: ""
    property string actionOutput: ""
    property string shellLog: ""
    property bool diagnosticsReady: false
    readonly property var card: look.skins.find(s => s.id === selectedSkin) || look.skins[0] || ({})
    readonly property var selectedReport: report.skins.find(s => s.id === selectedSkin) || ({})
    readonly property var activeReport: report.skins.find(s => s.id === look.skin) || ({})
    readonly property var depGroup: dependencyGroup === "core" ? report.core : report.skins.find(s => s.id === dependencyGroup) || report.core
    readonly property var dependencies: (depGroup.requires || []).map(x => Object.assign({}, x, {optional:false}))
                                      .concat((depGroup.recommends || []).map(x => Object.assign({}, x, {optional:true})))
                                      .filter(x => !query || (x.label + " " + (x.version || "")).toLowerCase().includes(query.toLowerCase()))
    readonly property bool busy: action.running
    readonly property int problemCount: [report.core].concat(report.skins).reduce((n, g) => n + (g.requires || []).filter(r => r.status !== "ok").length, 0)

    function refresh() { if (!diagnostic.running) diagnostic.running = true; }
    function acceptAppearance(value) {
        const old = look.skin;
        look = value;
        if (!selectedSkin) selectedSkin = value.skin;
        if (old && old !== value.skin) refresh();
    }
    function run(command, message) {
        if (previewMode || busy) return;
        if (!report.hyprland || !report.hyprland.version) { notice = "Sin conexión con Hyprland. Puedes consultar el diagnóstico y la ayuda."; return; }
        notice = message;
        actionOutput = "";
        action.command = command;
        action.running = true;
    }
    function requirements(id) { dependencyGroup = id; page = "Dependencias"; }
    function planText(group) {
        let result = [];
        for (const pair of [["plan", "Necesario"], ["recommendPlan", "Opcional"]]) {
            const plan = group[pair[0]] || {};
            const items = (plan.commands || []).concat(plan.manual || [], plan.notes || []);
            if (items.length) result.push(pair[1] + "\n" + items.join("\n"));
        }
        return result.join("\n\n") || "Todos los requisitos de este grupo están completos.";
    }

    Component.onCompleted: refresh()
    IpcHandler {
        target: "bwmenu"
        function inspect(): string { return JSON.stringify({page:root.page, skin:root.look.skin, theme:root.look.themeName, background:root.look.background, accent:root.look.accent, font:root.look.font, radius:root.look.radius, preview:root.previewMode, busy:root.busy, ready:root.diagnosticsReady}); }
        function navigate(name: string): void { if (["Skins", "Estado", "Dependencias", "Recuperación", "Ayuda"].includes(name)) root.page = name; }
        function selectSkin(id: string): void { if (root.look.skins.some(s => s.id === id)) root.selectedSkin = id; }
    }
    Shortcut { sequence: "Escape"; onActivated: { if (page !== "Skins") page = "Skins"; else if (!busy) Qt.quit(); } }
    Shortcut { sequence: "Ctrl+R"; onActivated: refresh() }

    Process {
        id: diagnostic
        command: ["python3", root.scripts + "/bwm-menu.py", "--json"]
        stdout: StdioCollector {
            onStreamFinished: {
                try { root.report = JSON.parse(text); root.diagnosticsReady = true; if (root.report.error) root.notice = root.report.error; }
                catch (e) { root.notice = "No se pudo leer el diagnóstico. Usa el modo de consola para consultar los errores."; }
            }
        }
    }
    Process {
        id: watcher
        running: !root.previewMode
        command: ["python3", root.scripts + "/bwm-menu.py", "--watch-appearance"]
        stdout: SplitParser {
            onRead: data => { try { root.acceptAppearance(JSON.parse(data)); } catch (e) { console.warn("BWMenu: paleta incompleta", e); } }
        }
    }
    Timer { interval: 5000; running: !root.previewMode; repeat: true; onTriggered: { if (!watcher.running) watcher.running = true; } }
    FileView {
        path: root.previewFile
        printErrors: false
        watchChanges: root.previewMode
        onFileChanged: reload()
        onLoaded: { if (root.previewMode) { try { root.acceptAppearance(JSON.parse(text())); } catch (e) {} } }
    }
    Process {
        id: action
        stdout: StdioCollector { onStreamFinished: root.actionOutput += text }
        stderr: StdioCollector { onStreamFinished: root.actionOutput += text }
        onExited: (exitCode, exitStatus) => {
            root.notice = exitCode === 0 ? "Orden terminada. Consulta el estado actualizado." : "La orden necesita revisión. Consulta el registro de la acción.";
            root.refresh();
        }
    }
    Process {
        id: logReader
        command: ["python3", root.scripts + "/bwm-menu.py", "--shell-log"]
        stdout: StdioCollector { onStreamFinished: root.shellLog = text }
    }

    component Label: Text {
        color: root.look.foreground
        font.family: root.look.font
        font.pixelSize: 13
        textFormat: Text.PlainText
        wrapMode: Text.Wrap
    }
    component Surface: Rectangle {
        color: root.look.surface
        radius: root.look.radius
        border.color: root.look.border
        border.width: 1
    }
    component Chip: Rectangle {
        property alias text: chipLabel.text
        implicitWidth: chipLabel.implicitWidth + 22
        implicitHeight: 30
        radius: Math.min(root.look.radius, 15)
        color: root.look.selection
        Label { id: chipLabel; anchors.centerIn: parent; color: root.look.accent; font.pixelSize: 11 }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0
        Rectangle {
            Layout.preferredWidth: 198
            Layout.fillHeight: true
            color: root.look.surface
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 9
                Label { text: "✦"; color: root.look.accent; font.pixelSize: 38 }
                Label { text: "BWMenu"; font.pixelSize: 26; font.bold: true }
                Label { text: "Tu escritorio,\na mano."; color: root.look.muted; lineHeight: 1.3; Layout.bottomMargin: 22 }
                Repeater {
                    model: ["Skins", "Estado", "Dependencias", "Recuperación", "Ayuda"]
                    MenuButton {
                        required property string modelData
                        Layout.fillWidth: true
                        style: root.look
                        text: modelData
                        chosen: root.page === modelData
                        onClicked: root.page = modelData
                    }
                }
                Item { Layout.fillHeight: true }
                Label { text: root.previewMode ? "Vista previa" : "●  " + root.look.skinName; color: root.look.accent; font.pixelSize: 11; Layout.fillWidth: true }
                Label { text: root.look.themeName; color: root.look.muted; font.pixelSize: 11; Layout.fillWidth: true }
                MenuButton { style: root.look; text: "Actualizar"; Layout.fillWidth: true; enabled: !root.busy; onClicked: root.refresh() }
                Label { text: "+ y −  ·  abrir\nEsc  ·  volver / cerrar"; color: root.look.muted; font.pixelSize: 10; Layout.topMargin: 10 }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 28
            spacing: 16
            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    Label { text: root.page === "Skins" ? "Elige tu escritorio." : root.page; font.pixelSize: 30; font.bold: true; Layout.fillWidth: true }
                    Label { text: root.page === "Skins" ? "Tres formas de trabajar. Un mismo BWM." : "Diagnóstico y recuperación de tu escritorio"; color: root.look.muted }
                }
            }
            RowLayout {
                Layout.fillWidth: true
                Chip { text: root.look.skinName + " / " + root.look.themeName }
                Chip { text: !root.diagnosticsReady ? "Comprobando…" : root.problemCount ? root.problemCount + " requisitos por revisar" : "✓ Requisitos completos" }
                Item { Layout.fillWidth: true }
                Row { spacing: 5; Repeater { model: [root.look.background, root.look.surface, root.look.accent, root.look.foreground]; Rectangle { required property string modelData; width: 13; height: 13; radius: Math.min(root.look.radius, 7); color: modelData; border.color: root.look.border; border.width: 1 } } }
                Label { text: "Colores en vivo"; color: root.look.muted; font.pixelSize: 10 }
            }
            Rectangle {
                visible: root.notice.length > 0
                Layout.fillWidth: true
                implicitHeight: noticeText.implicitHeight + 22
                radius: Math.min(root.look.radius, 10)
                color: root.look.selection
                Label { id: noticeText; anchors.fill: parent; anchors.margins: 11; text: (root.busy ? "◌  " : "") + root.notice; color: root.look.accent }
            }

            ScrollView {
                id: pageScroll
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                contentWidth: availableWidth
                ColumnLayout {
                    width: parent.width
                    spacing: 18

                    ColumnLayout {
                        visible: root.page === "Skins"
                        Layout.fillWidth: true
                        spacing: 18
                        GridLayout {
                            Layout.fillWidth: true
                            columns: 3
                            columnSpacing: 14
                            Repeater {
                                model: root.look.skins
                                SkinCard {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    skin: modelData
                                    style: root.look
                                    selected: modelData.id === root.selectedSkin
                                    active: modelData.id === root.look.skin
                                    ready: (root.report.skins.find(s => s.id === modelData.id) || {}).ready || false
                                    onChosen: root.selectedSkin = modelData.id
                                }
                            }
                        }
                        Surface {
                            Layout.fillWidth: true
                            implicitHeight: detailColumn.implicitHeight + 36
                            ColumnLayout {
                                id: detailColumn
                                anchors.fill: parent
                                anchors.margins: 18
                                spacing: 12
                                Label { text: root.card.name || "Cargando skins…"; font.family: root.card.font || root.look.font; font.pixelSize: 21; font.bold: true }
                                Label { text: root.card.description || ""; Layout.fillWidth: true; lineHeight: 1.3 }
                                Label { text: root.card.themes?.builtIn || ""; color: root.look.muted; Layout.fillWidth: true; font.pixelSize: 11 }
                                RowLayout {
                                    Layout.fillWidth: true
                                    MenuButton {
                                        style: root.look
                                        primary: true
                                        text: root.selectedSkin === root.look.skin ? "Skin activa" : "Aplicar " + (root.card.name || "skin")
                                        enabled: !root.previewMode && !root.busy && !!root.selectedReport.ready && root.selectedSkin !== root.look.skin
                                        onClicked: root.run([root.scripts + "/bwm", "skin", root.selectedSkin], "Aplicando " + root.card.name + "…")
                                    }
                                    MenuButton { style: root.look; text: "Ver requisitos"; onClicked: root.requirements(root.selectedSkin) }
                                    Item { Layout.fillWidth: true }
                                }
                            }
                        }
                    }

                    ColumnLayout {
                        visible: root.page === "Estado"
                        Layout.fillWidth: true
                        spacing: 12
                        Repeater {
                            model: [
                                ["BWM", root.report.version || "Consultando…"],
                                ["Hyprland en ejecución", root.report.hyprland?.version || "Sin conexión"],
                                ["Hyprland instalado", root.report.installedHyprland || "Sin dato"],
                                ["Barra y paneles", root.report.shellPids.length ? "En marcha · PID " + root.report.shellPids.join(", ") : "Sin instancia detectada"],
                                ["Configuración", root.report.hyprland?.version ? root.report.configErrors || "Sin errores detectados" : "Sin conexión"],
                                ["Carpeta de BWM", root.report.repo || ""]]
                            Surface {
                                required property var modelData
                                Layout.fillWidth: true
                                implicitHeight: statusRow.implicitHeight + 28
                                RowLayout { id: statusRow; anchors.fill: parent; anchors.margins: 14; Label { text: modelData[0]; color: root.look.muted; Layout.preferredWidth: 190 } Label { text: modelData[1]; Layout.fillWidth: true } }
                            }
                        }
                    }

                    ColumnLayout {
                        visible: root.page === "Dependencias"
                        Layout.fillWidth: true
                        spacing: 12
                        Flow {
                            Layout.fillWidth: true
                            spacing: 7
                            MenuButton { style: root.look; text: "Núcleo"; chosen: root.dependencyGroup === "core"; onClicked: root.dependencyGroup = "core" }
                            Repeater { model: root.report.skins; MenuButton { required property var modelData; style: root.look; text: modelData.name; chosen: root.dependencyGroup === modelData.id; onClicked: root.dependencyGroup = modelData.id } }
                        }
                        TextField {
                            Layout.fillWidth: true
                            placeholderText: "Buscar dependencia o versión…"
                            color: root.look.foreground
                            placeholderTextColor: root.look.muted
                            selectionColor: root.look.accent
                            font.family: root.look.font
                            onTextChanged: root.query = text
                            background: Rectangle { color: root.look.surface; radius: Math.min(root.look.radius, 10); border.color: root.look.border; border.width: 1 }
                        }
                        Repeater {
                            model: root.dependencies
                            Surface {
                                required property var modelData
                                Layout.fillWidth: true
                                implicitHeight: requirement.implicitHeight + 26
                                ColumnLayout {
                                    id: requirement
                                    anchors.fill: parent
                                    anchors.margins: 13
                                    spacing: 5
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Label { text: modelData.status === "ok" ? "✓" : "!"; color: modelData.status === "ok" ? root.look.accent : root.look.error; font.bold: true }
                                        Label { text: modelData.label; font.bold: true; Layout.fillWidth: true }
                                        Label { text: modelData.optional ? "Opcional" : "Necesario"; color: root.look.muted; font.pixelSize: 10 }
                                    }
                                    Label { text: (modelData.version || "Versión sin dato") + "   ·   " + (modelData.versionPolicy || ""); color: root.look.accent; Layout.fillWidth: true; font.pixelSize: 12 }
                                    Label { text: modelData.why + (modelData.status !== "ok" && modelData.detail ? "\n" + modelData.detail : ""); color: root.look.muted; Layout.fillWidth: true; font.pixelSize: 11 }
                                }
                            }
                        }
                        Label { text: "OK significa que cumple la comprobación declarada. Sin mínimo declarado no se certifica una versión concreta."; color: root.look.muted; Layout.fillWidth: true; font.pixelSize: 11 }
                        Surface {
                            Layout.fillWidth: true
                            implicitHeight: plan.implicitHeight + 28
                            Label { id: plan; width: parent.width - 28; anchors.left: parent.left; anchors.top: parent.top; anchors.margins: 14; text: root.planText(root.depGroup); font.pixelSize: 11 }
                        }
                    }

                    ColumnLayout {
                        visible: root.page === "Recuperación"
                        Layout.fillWidth: true
                        spacing: 14
                        Label { text: "Recupera tu escritorio"; font.pixelSize: 24; font.bold: true }
                        Label { text: "Las aplicaciones permanecen abiertas. El reinicio de barra y paneles puede tardar unos diez segundos."; Layout.fillWidth: true; color: root.look.muted }
                        MenuButton { style: root.look; text: "Reiniciar barra y paneles"; primary: true; enabled: !root.previewMode && !root.busy && root.diagnosticsReady; onClicked: root.run(["python3", root.scripts + "/bwm-theme-manager.py", "set", root.report.current, "--restart-shell"], "Reiniciando barra y paneles…") }
                        MenuButton { style: root.look; text: "Recargar configuración de Hyprland"; enabled: !root.previewMode && !root.busy; onClicked: root.run(["hyprctl", "reload"], "Recargando configuración…") }
                        MenuButton { style: root.look; text: "Ver registro de la barra"; onClicked: logReader.running = true }
                        MenuButton { style: root.look; text: "Abrir consola de rescate"; enabled: !root.previewMode && !root.busy; onClicked: { Quickshell.execDetached(["python3", root.scripts + "/bwm-menu.py", "--open", "--tui"]); Qt.quit(); } }
                        Label { text: root.actionOutput || "Las incidencias de la acción aparecerán aquí."; Layout.fillWidth: true; color: root.look.muted; font.pixelSize: 11 }
                        Label { text: root.shellLog; visible: text.length > 0; Layout.fillWidth: true; color: root.look.muted; font.pixelSize: 11 }
                    }
                    ColumnLayout {
                        visible: root.page === "Ayuda"
                        Layout.fillWidth: true
                        spacing: 16
                        Label { text: "Siempre una forma de volver."; font.pixelSize: 25; font.bold: true }
                        Label { text: "BWMenu es una ventana independiente de la barra y sus paneles. Su aspecto sigue los colores, fuentes y formas de la skin activa, también al cambiar de tema."; Layout.fillWidth: true; lineHeight: 1.4 }
                        Label { text: "Si falla la interfaz gráfica de BWMenu, se abre su consola de rescate. Puedes pedirla directamente con:\n\nbwm menu --open --tui\n\nSi cae todo Hyprland: Ctrl+Alt+F3, inicia sesión y ejecuta:\n\nbwm menu --tui\n\nLas instalaciones con sudo se realizan en tu terminal. Los comandos necesarios aparecen en Dependencias."; Layout.fillWidth: true; color: root.look.muted; lineHeight: 1.4 }
                    }
                }
            }
            RowLayout {
                Layout.fillWidth: true
                Label { text: "BWM · " + (root.report.version || "…"); color: root.look.muted; font.pixelSize: 10; Layout.fillWidth: true; elide: Text.ElideRight; wrapMode: Text.NoWrap }
                Label { text: root.busy ? "Aplicando cambios…" : "Tu sesión permanece abierta"; color: root.look.muted; font.pixelSize: 10 }
            }
        }
    }
}
