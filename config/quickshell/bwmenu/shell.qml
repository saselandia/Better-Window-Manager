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
import "ThemeUtils.js" as Theme

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
    property bool showPlan: false
    onDependencyGroupChanged: { showPlan = false; Qt.callLater(() => { requirementsTable.expandedId = ""; if (pageScroll.contentItem) pageScroll.contentItem.contentY = 0; }); }
    readonly property color dependencyBackground: look.background
    readonly property color dependencyField: look.surface
    readonly property color dependencyInk: Theme.ink(dependencyBackground)
    readonly property color dependencyFieldInk: Theme.ink(dependencyField)
    readonly property var dependencyStyle: Object.assign({}, look, {foreground:dependencyFieldInk})
    property string notice: ""
    property string actionOutput: ""
    property string shellLog: ""
    property var catalogData: ({skins:[], source:"", warning:"", publishingGuide:"", repository:""})
    property bool catalogReady: false
    property string catalogQuery: ""
    property string catalogError: ""
    readonly property var catalogSkins: catalogData.skins.filter(s => !catalogQuery || (s.name + " " + s.description + " " + s.imitates).toLowerCase().includes(catalogQuery.toLowerCase()))
    property bool diagnosticsReady: false
    readonly property var card: look.skins.find(s => s.id === selectedSkin) || look.skins[0] || ({})
    readonly property var selectedReport: report.skins.find(s => s.id === selectedSkin) || ({})
    readonly property var activeReport: report.skins.find(s => s.id === look.skin) || ({})
    readonly property var depGroup: dependencyGroup === "core" ? report.core : report.skins.find(s => s.id === dependencyGroup) || report.core
    readonly property var dependencies: (depGroup.requires || []).map(x => Object.assign({}, x, {optional:false}))
                                      .concat((depGroup.recommends || []).map(x => Object.assign({}, x, {optional:true})))
                                      .filter(x => !query || (x.label + " " + (x.version || "")).toLowerCase().includes(query.toLowerCase()))
    readonly property bool busy: action.running

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
    function openCatalog(force) {
        page = "Añadir skins";
        if (catalogLoader.running || (!force && catalogReady)) return;
        catalogError = "";
        catalogLoader.command = ["python3", scripts + "/bwm-skin-catalog.py", "discover"].concat(previewMode ? ["--local"] : force ? ["--refresh"] : []);
        catalogLoader.running = true;
    }
    function hasPlan(group) {
        return [group.plan || {}, group.recommendPlan || {}].some(p => (p.commands || []).length || (p.manual || []).length);
    }
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
        function inspect(): string { return JSON.stringify({page:root.page, skin:root.look.skin, theme:root.look.themeName, background:root.look.background, accent:root.look.accent, font:root.look.font, radius:root.look.radius, preview:root.previewMode, busy:root.busy, ready:root.diagnosticsReady, health:root.report.skins.map(s => ({id:s.id, state:s.versionHealth?.state || "unknown"})), rows:root.dependencies.length, catalogCount:root.catalogData.skins.length, catalogSource:root.catalogData.source, catalogLoading:catalogLoader.running, mascot:{variant:mascot.variant, ready:mascot.ready, moving:mascot.moving}}); }
        function navigate(name: string): void { if (["Skins", "Estado", "Dependencias", "Recuperación", "Ayuda"].includes(name)) root.page = name; }
        function selectSkin(id: string): void { if (root.look.skins.some(s => s.id === id)) root.selectedSkin = id; }
        function requirementsFor(id: string): void { if (id === "core" || root.report.skins.some(s => s.id === id)) root.requirements(id); }
        function catalog(): void { root.openCatalog(false); }
        function refreshCatalog(): void { root.openCatalog(true); }
        function closeMenu(): void { closeButton.clicked(); }
    }
    Shortcut { sequence: "Escape"; onActivated: { if (page !== "Skins") page = "Skins"; else if (!busy) Qt.quit(); } }
    Shortcut { sequence: "Ctrl+R"; onActivated: root.page === "Añadir skins" ? root.openCatalog(true) : root.refresh() }

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
    Process {
        id: catalogLoader
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const result = JSON.parse(text);
                    if (result.error) root.catalogError = result.error;
                    else { root.catalogData = result; root.catalogReady = true; }
                } catch (e) { root.catalogError = "No se pudo leer el catálogo."; }
            }
        }
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
    RowLayout {
        anchors.fill: parent
        spacing: 0
        Rectangle {
            Layout.preferredWidth: 180
            Layout.fillHeight: true
            color: root.look.surface
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 7
                RowLayout {
                    Layout.bottomMargin: 26
                    Label { text: "✦"; color: root.look.accent; font.pixelSize: 25 }
                    Label { text: "BWMenu"; font.pixelSize: 22; font.bold: true }
                }
                Repeater {
                    model: ["Skins", "Estado", "Dependencias", "Recuperación", "Ayuda"]
                    MenuButton {
                        required property string modelData
                        Layout.fillWidth: true
                        style: root.look
                        text: modelData
                        chosen: root.page === modelData || (modelData === "Skins" && root.page === "Añadir skins")
                        onClicked: root.page = modelData
                    }
                }
                Item { Layout.fillHeight: true }
                BwmMascot {
                    id: mascot
                    Layout.alignment: Qt.AlignHCenter
                    Layout.bottomMargin: 9
                    style: root.look
                    motionEnabled: root.visible
                }
                Label { text: root.previewMode ? "Vista previa" : root.look.skinName; color: root.look.accent; font.pixelSize: 11; Layout.fillWidth: true }
                Label { text: root.look.themeName; color: root.look.muted; font.pixelSize: 11; Layout.fillWidth: true }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 28
            spacing: 18
            RowLayout {
                Layout.fillWidth: true
                Label { text: root.page; color: root.page === "Dependencias" ? root.dependencyInk : root.look.foreground; font.pixelSize: 26; font.bold: true; Layout.fillWidth: true }
                MenuButton { visible: root.page === "Skins"; style: root.look; text: "+ Añadir skins"; onClicked: root.openCatalog(false) }
                MenuButton { visible: root.page === "Añadir skins"; style: root.look; text: "Instaladas"; onClicked: root.page = "Skins" }
                MenuButton { id: closeButton; style: root.page === "Dependencias" ? root.dependencyStyle : root.look; text: "×"; enabled: !root.busy; onClicked: root.close(); Accessible.name: "Cerrar BWMenu"; ToolTip.text: "Cerrar"; ToolTip.visible: hovered }
            }
            Rectangle {
                visible: root.notice.length > 0
                Layout.fillWidth: true
                implicitHeight: noticeText.implicitHeight + 22
                radius: Math.min(root.look.radius, 10)
                color: root.look.selection
                Label { id: noticeText; anchors.fill: parent; anchors.margins: 11; text: (root.busy ? "◌  " : "") + root.notice; color: root.page === "Dependencias" ? Theme.ink(parent.color) : root.look.accent }
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
                                    health: (root.report.skins.find(s => s.id === modelData.id) || {}).versionHealth || ({state:"unknown", description:"Comprobando"})
                                    onChosen: root.selectedSkin = modelData.id
                                }
                            }
                        }
                        Surface {
                            Layout.fillWidth: true
                            implicitHeight: detailRow.implicitHeight + 32
                            RowLayout {
                                id: detailRow
                                anchors.fill: parent
                                anchors.margins: 16
                                spacing: 14
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 4
                                    Label { text: root.card.name || "…"; font.family: root.card.font || root.look.font; font.pixelSize: 18; font.bold: true; Layout.fillWidth: true }
                                    Label { text: (root.card.imitates || "").replace(/\s*\(.*\)/, ""); color: root.look.muted; Layout.fillWidth: true; font.pixelSize: 11; elide: Text.ElideRight; wrapMode: Text.NoWrap }
                                }
                                MenuButton {
                                        style: root.look
                                        primary: true
                                        text: root.selectedSkin === root.look.skin ? "Activa" : "Aplicar"
                                        enabled: !root.previewMode && !root.busy && !!root.selectedReport.ready && root.selectedSkin !== root.look.skin
                                        onClicked: root.run([root.scripts + "/bwm", "skin", root.selectedSkin], "Aplicando " + root.card.name + "…")
                                }
                                MenuButton { style: root.look; text: "Dependencias"; onClicked: root.requirements(root.selectedSkin) }
                            }
                        }
                    }

                    ColumnLayout {
                        visible: root.page === "Añadir skins"
                        Layout.fillWidth: true
                        spacing: 13
                        RowLayout {
                            Layout.fillWidth: true
                            TextField {
                                Layout.fillWidth: true
                                placeholderText: "Buscar skins…"
                                color: root.dependencyFieldInk
                                placeholderTextColor: root.dependencyFieldInk
                                font.family: root.look.font
                                font.pixelSize: 12
                                onTextChanged: root.catalogQuery = text
                                background: Rectangle { color: root.look.surface; radius: Math.min(root.look.radius, 6); border.color: root.look.border; border.width: 1 }
                            }
                            MenuButton { style: root.look; text: "Actualizar"; enabled: !catalogLoader.running; onClicked: root.openCatalog(true) }
                            MenuButton { style: root.look; text: "Repositorio"; enabled: root.catalogData.repository.length > 0; onClicked: Qt.openUrlExternally(root.catalogData.repository) }
                            MenuButton { style: root.look; text: "Cómo publicar"; enabled: root.catalogData.publishingGuide.length > 0; onClicked: Qt.openUrlExternally(root.catalogData.publishingGuide) }
                        }
                        Label { visible: catalogLoader.running; text: "Consultando catálogo…"; color: root.look.muted; font.pixelSize: 11 }
                        Label { visible: root.catalogError.length > 0 || root.catalogData.warning.length > 0; text: root.catalogError || root.catalogData.warning; Layout.fillWidth: true; color: root.look.muted; font.pixelSize: 11 }
                        GridLayout {
                            Layout.fillWidth: true
                            columns: 2
                            columnSpacing: 14
                            rowSpacing: 14
                            Repeater {
                                model: root.catalogSkins
                                CatalogCard {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    entry: modelData
                                    style: root.look
                                    onOpenRequested: {
                                        if (modelData.installed) { root.selectedSkin = modelData.id; root.page = "Skins"; }
                                        else if (!root.previewMode) Qt.openUrlExternally(modelData.installationUrl);
                                    }
                                }
                            }
                        }
                        Label { visible: !catalogLoader.running && !root.catalogSkins.length; text: root.catalogQuery ? "Sin skins para esta búsqueda." : "Aún no hay skins adicionales publicadas."; color: root.look.muted }
                    }

                    ColumnLayout {
                        visible: root.page === "Estado"
                        Layout.fillWidth: true
                        spacing: 12
                        Repeater {
                            model: [
                                ["BWM", root.report.version || "Consultando…"],
                                ["Referencias de versiones", root.report.referenceEnvironment?.recorded || "Sin fecha"],
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
                        spacing: 10
                        Flow {
                            Layout.fillWidth: true
                            spacing: 7
                            MenuButton { style: root.dependencyStyle; text: "Núcleo"; statusHealth: root.report.core.versionHealth || ({state:"unknown", description:"Comprobando"}); chosen: root.dependencyGroup === "core"; onClicked: root.dependencyGroup = "core" }
                            Repeater { model: root.report.skins; MenuButton { required property var modelData; style: root.dependencyStyle; text: modelData.name; statusHealth: modelData.versionHealth || ({state:"unknown", description:"Comprobando"}); chosen: root.dependencyGroup === modelData.id; onClicked: root.dependencyGroup = modelData.id } }
                        }
                        TextField {
                            Layout.fillWidth: true
                            placeholderText: "Buscar…"
                            color: root.dependencyFieldInk
                            placeholderTextColor: root.dependencyFieldInk
                            selectionColor: root.look.accent
                            selectedTextColor: root.look.onAccent
                            font.family: root.look.font
                            font.pixelSize: 12
                            onTextChanged: root.query = text
                            background: Rectangle { color: root.dependencyField; radius: Math.min(root.look.radius, 6); border.color: root.look.border; border.width: 1 }
                        }
                        RowLayout {
                            spacing: 15
                            Repeater {
                                model: [{state:"ok", label:"Correcta"}, {state:"error", label:"Falta"}, {state:"newer", label:"Desactualizado"}]
                                RowLayout {
                                    required property var modelData
                                    spacing: 3
                                    StatusLight { state: modelData.state; description: modelData.label }
                                    Label { text: modelData.label; color: root.dependencyInk; font.pixelSize: 11 }
                                }
                            }
                        }
                        DependencyTable {
                            id: requirementsTable
                            Layout.fillWidth: true
                            rows: root.dependencies
                            style: root.dependencyStyle
                            fontFamily: root.look.font
                        }
                        MenuButton { visible: root.hasPlan(root.depGroup); style: root.dependencyStyle; text: root.showPlan ? "Ocultar comandos" : "Resolver incidencias"; onClicked: root.showPlan = !root.showPlan }
                        Rectangle {
                            visible: root.showPlan && root.hasPlan(root.depGroup)
                            Layout.fillWidth: true
                            radius: 6
                            color: root.dependencyField
                            implicitHeight: plan.implicitHeight + 28
                            Label { id: plan; width: parent.width - 28; anchors.left: parent.left; anchors.top: parent.top; anchors.margins: 14; text: root.planText(root.depGroup); color: root.dependencyFieldInk; font.pixelSize: 11 }
                        }
                    }

                    ColumnLayout {
                        visible: root.page === "Recuperación"
                        Layout.fillWidth: true
                        spacing: 14
                        MenuButton { style: root.look; text: "Reiniciar barra y paneles"; primary: true; enabled: !root.previewMode && !root.busy && root.diagnosticsReady; onClicked: root.run(["python3", root.scripts + "/bwm-theme-manager.py", "set", root.report.current, "--restart-shell"], "Reiniciando barra y paneles…") }
                        MenuButton { style: root.look; text: "Recargar configuración de Hyprland"; enabled: !root.previewMode && !root.busy; onClicked: root.run(["hyprctl", "reload"], "Recargando configuración…") }
                        MenuButton { style: root.look; text: "Ver registro de la barra"; onClicked: logReader.running = true }
                        MenuButton { style: root.look; text: "Abrir consola de rescate"; enabled: !root.previewMode && !root.busy; onClicked: { Quickshell.execDetached(["python3", root.scripts + "/bwm-menu.py", "--open", "--tui"]); Qt.quit(); } }
                        Label { text: root.actionOutput; visible: text.length > 0; Layout.fillWidth: true; color: root.look.muted; font.pixelSize: 11 }
                        Label { text: root.shellLog; visible: text.length > 0; Layout.fillWidth: true; color: root.look.muted; font.pixelSize: 11 }
                    }
                    ColumnLayout {
                        visible: root.page === "Ayuda"
                        Layout.fillWidth: true
                        spacing: 16
                        Label { text: "Consola de rescate\n\nbwm menu --open --tui\n\nSi cae Hyprland: Ctrl+Alt+F3, inicia sesión y ejecuta:\n\nbwm menu --tui\n\nActualizar: Ctrl+R · Cerrar o volver: Esc"; Layout.fillWidth: true; color: root.look.foreground; lineHeight: 1.4 }
                    }
                }
            }
        }
    }
}
