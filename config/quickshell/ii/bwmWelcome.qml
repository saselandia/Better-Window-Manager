//@ pragma UseQApplication
//@ pragma Env QS_NO_RELOAD_POPUP=1
//@ pragma Env QT_QUICK_CONTROLS_STYLE=Basic
//@ pragma Env QT_QUICK_FLICKABLE_WHEEL_DECELERATION=10000

// Adjust this to make the app smaller or larger
//@ pragma Env QT_SCALE_FACTOR=1

// Bienvenida de BWM, al estilo de un asistente de Calamares: pasos a la izquierda y una página
// por paso. Se abre al iniciar sesión hasta que se desactiva (`bwm startup off`, interruptor de
// abajo) y siempre con `bwm`. Las skins y sus requisitos salen de bwm-requirements.py --json
// (manifiestos de config/hypr/skins); es una ventana aparte (qs -p), no la barra.

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import Quickshell
import Quickshell.Io
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.common.functions

ApplicationWindow {
    id: root
    readonly property string scriptsDir: FileUtils.trimFileProtocol(Quickshell.shellPath("../../hypr/scripts"))
    readonly property color colReady: "#3fb950"
    readonly property var steps: [
        { name: "Bienvenida", icon: "waving_hand" },
        { name: "Skins", icon: "palette" },
        { name: "Añadir skins", icon: "add_circle" },
        { name: "Listo", icon: "check_circle" }
    ]
    property int page: 0
    property var report: null
    property bool loading: true
    property string loadError: ""
    property bool showAtStartup: true
    property string switching: ""   // skin que se está activando

    readonly property var readySkins: (root.report?.skins ?? []).filter(s => s.ready)
    readonly property var communitySkins: (root.report?.skins ?? []).filter(s => !s.builtin)

    function refresh() {
        root.loading = true;
        checkProc.running = true;
    }
    function skinName(id) {
        const skin = (root.report?.skins ?? []).find(s => s.id === id);
        return skin ? skin.name : id;
    }
    function hyprlandVersion() {
        const req = (root.report?.core.requires ?? []).find(r => r.id === "hyprland");
        return req ? req.detail : "";
    }
    function planText(plan) {
        if (!plan) return "";
        return plan.commands.concat(plan.manual.map(m => "# " + m)).join("\n");
    }
    function copy(text) {
        Quickshell.execDetached(["wl-copy", text]);
    }
    function activate(id) {
        root.switching = id;
        Quickshell.execDetached(["python3", root.scriptsDir + "/bwm-theme-manager.py", "set", id]);
        switchTimer.restart();
    }

    visible: true
    title: "Bienvenido a BWM"
    onClosing: Qt.quit()
    minimumWidth: 860
    minimumHeight: 560
    width: 1040
    height: 700
    color: Appearance.m3colors.m3background

    Component.onCompleted: {
        MaterialThemeLoader.reapplyTheme();
        root.refresh();
        startupProc.running = true;
    }

    Process {
        id: checkProc
        command: ["python3", root.scriptsDir + "/bwm-requirements.py", "check", "--json"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.report = JSON.parse(this.text);
                    root.loadError = "";
                } catch (e) {
                    root.loadError = "No se pudieron leer los requisitos (bwm-requirements.py).";
                }
                root.loading = false;
            }
        }
    }

    Process {
        id: startupProc
        command: [root.scriptsDir + "/bwm", "startup", "status"]
        stdout: StdioCollector {
            onStreamFinished: root.showAtStartup = this.text.trim() !== "off"
        }
    }

    Timer { // el gestor de skins reinicia Quickshell (~10 s); luego se relee cuál está activa
        id: switchTimer
        interval: 14000
        onTriggered: {
            root.switching = "";
            root.refresh();
        }
    }

    // ── Piezas ──────────────────────────────────────────────────────────────

    component PageTitle: StyledText {
        Layout.fillWidth: true
        wrapMode: Text.Wrap
        color: Appearance.colors.colOnLayer0
        font {
            family: Appearance.font.family.title
            pixelSize: Appearance.font.pixelSize.hugeass + 6
            variableAxes: Appearance.font.variableAxes.title
        }
    }

    component Paragraph: StyledText {
        Layout.fillWidth: true
        wrapMode: Text.Wrap
        color: Appearance.colors.colOnLayer0
        font.pixelSize: Appearance.font.pixelSize.normal
        lineHeight: 1.15
    }

    component Subtle: StyledText {
        Layout.fillWidth: true
        wrapMode: Text.Wrap
        color: Appearance.colors.colSubtext
        font.pixelSize: Appearance.font.pixelSize.small
    }

    component Pill: Rectangle {
        property alias text: pillText.text
        property color tint: Appearance.colors.colPrimary
        radius: Appearance.rounding.full
        color: ColorUtils.transparentize(tint, 0.82)
        border.width: 1
        border.color: tint
        implicitHeight: pillText.implicitHeight + 8
        implicitWidth: pillText.implicitWidth + 20
        StyledText {
            id: pillText
            anchors.centerIn: parent
            color: parent.tint
            font.pixelSize: Appearance.font.pixelSize.smaller
            font.weight: Font.DemiBold
        }
    }

    component PrimaryButton: DialogButton {
        colBackground: Appearance.colors.colPrimary
        colBackgroundHover: Appearance.colors.colPrimaryHover
        colRipple: Appearance.colors.colPrimaryActive
        colText: Appearance.colors.colOnPrimary
    }

    component CommandBox: Rectangle { // comandos para la distro detectada, seleccionables y copiables
        id: box
        property string text
        visible: text.length > 0
        Layout.fillWidth: true
        radius: Appearance.rounding.small
        color: Appearance.colors.colLayer2
        implicitHeight: boxRow.implicitHeight + 20
        RowLayout {
            id: boxRow
            anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 10 }
            TextEdit {
                Layout.fillWidth: true
                text: box.text
                readOnly: true
                selectByMouse: true
                wrapMode: TextEdit.Wrap
                color: Appearance.colors.colOnLayer2
                selectionColor: Appearance.colors.colPrimary
                selectedTextColor: Appearance.colors.colOnPrimary
                font.family: Appearance.font.family.monospace
                font.pixelSize: Appearance.font.pixelSize.smaller
            }
            DialogButton {
                Layout.alignment: Qt.AlignTop
                buttonText: "Copiar"
                onClicked: root.copy(box.text)
            }
        }
    }

    component RequirementRow: RowLayout {
        required property var modelData
        readonly property bool ok: modelData.status === "ok"
        Layout.fillWidth: true
        spacing: 8
        MaterialSymbol {
            Layout.alignment: Qt.AlignTop
            text: parent.ok ? "check_circle" : (modelData.status === "pending" || modelData.status === "build" ? "schedule" : "cancel")
            iconSize: 18
            color: parent.ok ? root.colReady : (modelData.status === "build" ? Appearance.colors.colTertiary : Appearance.colors.colError)
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 0
            StyledText {
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                text: modelData.label + (modelData.detail ? `  ·  ${modelData.detail}` : "")
                color: Appearance.colors.colOnLayer1
                font.pixelSize: Appearance.font.pixelSize.small
            }
            Subtle {
                visible: !parent.parent.ok
                text: modelData.why
            }
        }
    }

    component SkinCard: Rectangle {
        id: card
        required property var modelData
        property bool expanded: false
        readonly property bool active: root.report?.current === modelData.id
        readonly property var missingRecommends: modelData.recommends.filter(r => r.status !== "ok")
        Layout.fillWidth: true
        radius: Appearance.rounding.normal
        color: Appearance.colors.colLayer1
        border.width: 1
        border.color: modelData.ready ? ColorUtils.transparentize(root.colReady, 0.4) : ColorUtils.transparentize(Appearance.colors.colError, 0.4)
        implicitHeight: cardColumn.implicitHeight + 24

        ColumnLayout {
            id: cardColumn
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
            spacing: 12

            RippleButton { // cabecera: despliega la ficha
                Layout.fillWidth: true
                implicitHeight: headerRow.implicitHeight + 12
                buttonRadius: Appearance.rounding.small
                onClicked: card.expanded = !card.expanded
                contentItem: RowLayout {
                    id: headerRow
                    spacing: 14
                    Rectangle {
                        Layout.preferredWidth: 136
                        Layout.preferredHeight: 85
                        radius: Appearance.rounding.small
                        clip: true
                        color: Appearance.colors.colLayer2
                        Image {
                            anchors.fill: parent
                            source: card.modelData.preview ? "file://" + card.modelData.preview : ""
                            fillMode: Image.PreserveAspectCrop
                            asynchronous: true
                            mipmap: true
                            sourceSize.width: 272
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 3
                        RowLayout {
                            spacing: 8
                            Rectangle { // punto verde = requisitos completos
                                implicitWidth: 10
                                implicitHeight: 10
                                radius: 5
                                color: card.modelData.ready ? root.colReady : Appearance.colors.colError
                            }
                            StyledText {
                                text: card.modelData.name
                                color: Appearance.colors.colOnLayer1
                                font.pixelSize: Appearance.font.pixelSize.huge
                                font.weight: Font.DemiBold
                            }
                        }
                        Subtle { text: "Imita: " + card.modelData.imitates }
                        Subtle {
                            text: "Tema por defecto: " + card.modelData.defaultTheme.name + " · "
                                + (card.modelData.defaultTheme.mode === "dynamic" ? "dinámico (cambia con el fondo)" : "estático")
                        }
                    }
                    ColumnLayout {
                        spacing: 6
                        Pill {
                            Layout.alignment: Qt.AlignRight
                            tint: card.modelData.ready ? root.colReady : Appearance.colors.colError
                            text: card.modelData.ready ? "Instalada · requisitos completos" : "Faltan requisitos"
                        }
                        Pill {
                            Layout.alignment: Qt.AlignRight
                            visible: card.active || root.switching === card.modelData.id
                            text: root.switching === card.modelData.id ? "Activando…" : "Activa"
                        }
                    }
                    MaterialSymbol {
                        text: "expand_more"
                        iconSize: 24
                        rotation: card.expanded ? 180 : 0
                        color: Appearance.colors.colOnLayer1
                        Behavior on rotation { NumberAnimation { duration: 150 } }
                    }
                }
            }

            ColumnLayout { // ficha desplegada
                visible: card.expanded
                Layout.fillWidth: true
                Layout.leftMargin: 6
                Layout.rightMargin: 6
                spacing: 8

                Paragraph { text: card.modelData.description }
                Subtle { text: card.modelData.defaultTheme.description }
                Subtle { text: "Temas: " + card.modelData.themes.builtIn }
                Subtle { text: "Compatibilidad: " + card.modelData.themes.compatibility }

                StyledText {
                    Layout.topMargin: 6
                    text: "Requisitos de la skin"
                    color: Appearance.colors.colOnLayer1
                    font.pixelSize: Appearance.font.pixelSize.normal
                    font.weight: Font.DemiBold
                }
                Repeater {
                    model: card.modelData.requires
                    delegate: RequirementRow {}
                }
                Subtle {
                    visible: card.missingRecommends.length > 0
                    text: "Recomendado (opcional): " + card.missingRecommends.map(r => r.label).join(", ")
                }
                Subtle {
                    visible: !root.report?.core.ok
                    color: Appearance.colors.colError
                    text: "También faltan requisitos del núcleo: míralos arriba."
                }
                CommandBox { text: root.planText(card.modelData.plan) }
                CommandBox {
                    text: root.planText(card.modelData.recommendPlan)
                    visible: card.modelData.ready && text.length > 0
                }

                RowLayout {
                    Layout.topMargin: 4
                    spacing: 8
                    PrimaryButton {
                        visible: card.modelData.ready && !card.active
                        buttonText: "Activar esta skin"
                        enabled: root.switching === ""
                        onClicked: root.activate(card.modelData.id)
                    }
                    Subtle {
                        visible: !card.modelData.ready
                        Layout.fillWidth: false
                        text: "Instala lo que falta para poder activarla."
                    }
                    DialogButton {
                        visible: !!card.modelData.upstream
                        buttonText: "Original"
                        onClicked: Qt.openUrlExternally(card.modelData.upstream)
                    }
                    Subtle {
                        visible: root.switching === card.modelData.id
                        text: "Cambiando de skin: las barras parpadean unos segundos."
                    }
                }
            }
        }
    }

    // ── Ventana ─────────────────────────────────────────────────────────────

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle { // barra lateral con los pasos, como Calamares
            Layout.fillHeight: true
            Layout.preferredWidth: 250
            color: Appearance.colors.colLayer1

            ColumnLayout {
                anchors { fill: parent; margins: 20 }
                spacing: 6

                Image {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: 110
                    Layout.preferredHeight: 110
                    source: Quickshell.shellPath("../../hypr/omarchy/boot/logo.png")
                    fillMode: Image.PreserveAspectFit
                    mipmap: true
                    sourceSize.width: 220
                }
                StyledText {
                    Layout.alignment: Qt.AlignHCenter
                    text: "BWM"
                    color: Appearance.colors.colOnLayer1
                    font {
                        family: Appearance.font.family.title
                        pixelSize: Appearance.font.pixelSize.hugeass + 4
                        variableAxes: Appearance.font.variableAxes.title
                    }
                }
                StyledText {
                    Layout.alignment: Qt.AlignHCenter
                    text: "Better Window Manager"
                    color: Appearance.colors.colSubtext
                    font.pixelSize: Appearance.font.pixelSize.small
                }
                Item { Layout.preferredHeight: 18 }

                Repeater {
                    model: root.steps
                    delegate: RippleButton {
                        required property var modelData
                        required property int index
                        Layout.fillWidth: true
                        implicitHeight: 44
                        buttonRadius: Appearance.rounding.full
                        toggled: root.page === index
                        onClicked: root.page = index
                        contentItem: RowLayout {
                            spacing: 12
                            Item { implicitWidth: 2 }
                            MaterialSymbol {
                                text: modelData.icon
                                iconSize: 20
                                color: root.page === index ? Appearance.colors.colOnPrimary : Appearance.colors.colOnLayer1
                            }
                            StyledText {
                                Layout.fillWidth: true
                                text: modelData.name
                                color: root.page === index ? Appearance.colors.colOnPrimary : Appearance.colors.colOnLayer1
                                font.pixelSize: Appearance.font.pixelSize.normal
                            }
                        }
                    }
                }

                Item { Layout.fillHeight: true }
                Subtle {
                    horizontalAlignment: Text.AlignHCenter
                    text: root.report ? root.report.distro.name : ""
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            StackLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: root.page

                // 1. Bienvenida
                StyledFlickable {
                    contentHeight: welcomeColumn.implicitHeight + 64
                    clip: true
                    ColumnLayout {
                        id: welcomeColumn
                        x: 36
                        y: 32
                        width: parent.width - 72
                        spacing: 16

                        PageTitle { text: "¡Gracias por instalar BWM!" }
                        Paragraph {
                            text: "BWM es un gestor de ventanas que reúne a los demás como skins. Cada skin reproduce otro escritorio "
                                + "—su barra, sus menús, sus atajos y sus temas— y las aplicaciones cambian con ella. Puedes pasar "
                                + "de una a otra cuando quieras sin cerrar nada."
                        }
                        Paragraph {
                            text: "La meta es la compatibilidad: si en la skin KDE Plasma pones un tema de Plasma descargado de "
                                + "internet, o en Retro uno de Omarchy, debe aplicarse y funcionar igual que en el original."
                        }

                        GridLayout {
                            Layout.topMargin: 8
                            Layout.fillWidth: true
                            columns: 3
                            columnSpacing: 12
                            rowSpacing: 12
                            Repeater {
                                model: [
                                    { label: "Sistema", value: root.report?.distro.name ?? "…" },
                                    { label: "Hyprland", value: root.hyprlandVersion() || "…" },
                                    { label: "Skin activa", value: root.report ? root.skinName(root.report.current) : "…" }
                                ]
                                delegate: Rectangle {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    implicitHeight: infoColumn.implicitHeight + 24
                                    radius: Appearance.rounding.normal
                                    color: Appearance.colors.colLayer1
                                    ColumnLayout {
                                        id: infoColumn
                                        anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 14 }
                                        spacing: 2
                                        Subtle { text: modelData.label }
                                        StyledText {
                                            Layout.fillWidth: true
                                            elide: Text.ElideRight
                                            text: modelData.value
                                            color: Appearance.colors.colOnLayer1
                                            font.pixelSize: Appearance.font.pixelSize.large
                                            font.weight: Font.DemiBold
                                        }
                                    }
                                }
                            }
                        }

                        StyledText {
                            Layout.topMargin: 8
                            text: "Para empezar"
                            color: Appearance.colors.colOnLayer0
                            font.pixelSize: Appearance.font.pixelSize.larger
                            font.weight: Font.DemiBold
                        }
                        GridLayout {
                            Layout.fillWidth: true
                            columns: 2
                            columnSpacing: 18
                            rowSpacing: 8
                            Repeater {
                                model: [
                                    ["Alt + T", "Cambiar de skin"],
                                    ["Alt + R", "Temas de la skin Retro"],
                                    ["Alt + W", "Fondo de pantalla (la skin Default toma sus colores)"],
                                    ["Super + I", "Ajustes"],
                                    ["bwm", "Abre esta ventana desde la terminal"],
                                    ["bwm check", "Requisitos y comandos para instalarlos"]
                                ]
                                delegate: RowLayout {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    spacing: 10
                                    Rectangle {
                                        implicitWidth: keyText.implicitWidth + 16
                                        implicitHeight: keyText.implicitHeight + 8
                                        radius: Appearance.rounding.small
                                        color: Appearance.colors.colLayer2
                                        StyledText {
                                            id: keyText
                                            anchors.centerIn: parent
                                            text: modelData[0]
                                            color: Appearance.colors.colOnLayer2
                                            font.family: Appearance.font.family.monospace
                                            font.pixelSize: Appearance.font.pixelSize.smaller
                                        }
                                    }
                                    StyledText {
                                        Layout.fillWidth: true
                                        wrapMode: Text.Wrap
                                        text: modelData[1]
                                        color: Appearance.colors.colOnLayer0
                                        font.pixelSize: Appearance.font.pixelSize.small
                                    }
                                }
                            }
                        }
                    }
                }

                // 2. Skins
                StyledFlickable {
                    contentHeight: skinsColumn.implicitHeight + 64
                    clip: true
                    ColumnLayout {
                        id: skinsColumn
                        x: 36
                        y: 32
                        width: parent.width - 72
                        spacing: 14

                        PageTitle { text: "Skins instaladas" }
                        Paragraph {
                            text: "BWM trae tres. En verde las que tienen todos sus requisitos; despliega una para ver qué "
                                + "usa, su tema por defecto y activarla."
                        }
                        RowLayout {
                            visible: root.loading
                            spacing: 10
                            MaterialLoadingIndicator { loading: root.loading; implicitSize: 28 }
                            Subtle { text: "Comprobando el sistema…" }
                        }
                        RowLayout {
                            visible: root.loadError.length > 0 && !root.loading
                            Subtle { text: root.loadError; color: Appearance.colors.colError }
                            DialogButton { buttonText: "Reintentar"; onClicked: root.refresh() }
                        }

                        Rectangle { // núcleo incompleto: afecta a todas
                            visible: !!root.report && !root.report.core.ok
                            Layout.fillWidth: true
                            radius: Appearance.rounding.normal
                            color: ColorUtils.transparentize(Appearance.colors.colError, 0.88)
                            border.width: 1
                            border.color: Appearance.colors.colError
                            implicitHeight: coreColumn.implicitHeight + 24
                            ColumnLayout {
                                id: coreColumn
                                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
                                spacing: 8
                                StyledText {
                                    text: "Faltan requisitos del núcleo (los usan todas las skins)"
                                    color: Appearance.colors.colError
                                    font.pixelSize: Appearance.font.pixelSize.normal
                                    font.weight: Font.DemiBold
                                }
                                Repeater {
                                    model: (root.report?.core.requires ?? []).filter(r => r.status !== "ok")
                                    delegate: RequirementRow {}
                                }
                                CommandBox { text: root.planText(root.report?.core.plan) }
                            }
                        }

                        Repeater {
                            model: root.report?.skins.filter(s => s.builtin) ?? []
                            delegate: SkinCard {}
                        }

                        RowLayout {
                            visible: !root.loading
                            spacing: 8
                            DialogButton { buttonText: "Volver a comprobar"; onClicked: root.refresh() }
                            DialogButton { buttonText: "Añadir skins"; onClicked: root.page = 2 }
                        }
                    }
                }

                // 3. Añadir skins
                StyledFlickable {
                    contentHeight: addColumn.implicitHeight + 64
                    clip: true
                    ColumnLayout {
                        id: addColumn
                        x: 36
                        y: 32
                        width: parent.width - 72
                        spacing: 16

                        PageTitle { text: "Añadir skins" }
                        Paragraph {
                            text: "Cada skin nueva es otro gestor de ventanas o escritorio reproducido dentro de BWM, con sus temas "
                                + "y sus requisitos. Todavía no hay skins de la comunidad: cuando las haya aparecerán aquí para activarlas."
                        }
                        Repeater {
                            model: root.communitySkins
                            delegate: SkinCard {}
                        }
                        Rectangle {
                            visible: root.communitySkins.length === 0
                            Layout.fillWidth: true
                            radius: Appearance.rounding.normal
                            color: Appearance.colors.colLayer1
                            implicitHeight: emptyRow.implicitHeight + 32
                            RowLayout {
                                id: emptyRow
                                anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 16 }
                                spacing: 14
                                MaterialSymbol {
                                    text: "extension"
                                    iconSize: 36
                                    color: Appearance.colors.colPrimary
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2
                                    StyledText {
                                        text: "Sin skins de la comunidad por ahora"
                                        color: Appearance.colors.colOnLayer1
                                        font.pixelSize: Appearance.font.pixelSize.large
                                        font.weight: Font.DemiBold
                                    }
                                    Subtle { text: "La wiki explica qué es una skin, qué debe declarar y cómo se propone una." }
                                }
                            }
                        }
                        RowLayout {
                            spacing: 8
                            PrimaryButton {
                                buttonText: "Abrir la wiki"
                                onClicked: Qt.openUrlExternally(root.report?.links.wiki ?? "")
                            }
                            DialogButton {
                                buttonText: "Guía de requisitos"
                                onClicked: Qt.openUrlExternally(root.report?.links.requirements ?? "")
                            }
                        }
                    }
                }

                // 4. Listo
                StyledFlickable {
                    contentHeight: doneColumn.implicitHeight + 64
                    clip: true
                    ColumnLayout {
                        id: doneColumn
                        x: 36
                        y: 32
                        width: parent.width - 72
                        spacing: 16

                        PageTitle { text: "Todo listo" }
                        Paragraph {
                            text: root.report
                                ? `${root.readySkins.length} de ${root.report.skins.length} skins tienen todos sus requisitos. `
                                    + `Estás en ${root.skinName(root.report.current)}.`
                                : "Comprobando el sistema…"
                        }
                        Paragraph {
                            text: "Esta ventana se abre cada vez que inicias sesión. Si no quieres verla más, apaga "
                                + "«Mostrar al iniciar sesión» abajo; podrás abrirla cuando quieras escribiendo bwm en la terminal."
                        }
                        RowLayout {
                            spacing: 8
                            PrimaryButton {
                                buttonText: "Abrir Ajustes"
                                onClicked: Quickshell.execDetached([root.scriptsDir + "/open-settings.sh"])
                            }
                            DialogButton {
                                buttonText: "Ver las skins"
                                onClicked: root.page = 1
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 1
                color: Appearance.m3colors.m3outlineVariant
            }

            RowLayout { // pie: mostrar al iniciar sesión y navegación
                Layout.fillWidth: true
                Layout.margins: 14
                Layout.leftMargin: 24
                spacing: 10

                StyledSwitch {
                    checked: root.showAtStartup
                    onClicked: {
                        root.showAtStartup = checked;
                        Quickshell.execDetached([root.scriptsDir + "/bwm", "startup", checked ? "on" : "off"]);
                    }
                }
                StyledText {
                    text: "Mostrar al iniciar sesión"
                    color: Appearance.colors.colOnLayer0
                    font.pixelSize: Appearance.font.pixelSize.small
                }
                Item { Layout.fillWidth: true }
                DialogButton {
                    buttonText: "Atrás"
                    enabled: root.page > 0
                    onClicked: root.page -= 1
                }
                PrimaryButton {
                    buttonText: root.page < root.steps.length - 1 ? "Siguiente" : "Cerrar"
                    onClicked: {
                        if (root.page < root.steps.length - 1)
                            root.page += 1;
                        else
                            root.close();
                    }
                }
            }
        }
    }
}
