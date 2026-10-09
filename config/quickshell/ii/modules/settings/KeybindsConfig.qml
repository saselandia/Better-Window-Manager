import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Quickshell
import Quickshell.Io
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.common.functions
import org.kde.kirigami as Kirigami

ContentPage {
    id: root
    forceWidth: true

    property var keybindsList: []
    property string searchQuery: ""
    property string selectedCategory: "Todos"
    property bool showForm: false
    property bool isEditing: false
    property string editingId: ""

    // Form fields
    property string formCategory: "Personalizados"
    property string formDesc: ""
    property bool formModSuper: true
    property bool formModCtrl: false
    property bool formModAlt: false
    property bool formModShift: false
    property string formKey: "B"
    property string formActionType: "exec" // "exec" | "dispatcher"
    property string formExecCmd: ""
    property string formDispatcher: "window.close"
    property string formDispatcherArg: ""

    property string feedbackMessage: ""
    property bool feedbackIsError: false

    readonly property string managerScript: FileUtils.trimFileProtocol(Directories.home) + "/.config/hypr/scripts/keybinds-manager.py"

    readonly property var categoryTabs: [
        "Todos",
        "Lanzadores",
        "Ventanas",
        "Navegación",
        "Espacios de trabajo",
        "Sistema",
        "Multimedia",
        "Personalizados"
    ]

    readonly property var dispatcherPresets: [
        { name: "Cerrar ventana activa", dispatcher: "window.close", arg: "" },
        { name: "Pantalla completa (Fullscreen)", dispatcher: "window.fullscreen", arg: "" },
        { name: "Alternar división (Split)", dispatcher: "layout", arg: "togglesplit" },
        { name: "Recordar regla flotante persistente", dispatcher: "toggle_float", arg: "" },
        { name: "Mostrar/Ocultar espacio especial (Magic)", dispatcher: "workspace.toggle_special", arg: "magic" },
        { name: "Enviar ventana a espacio especial (Magic)", dispatcher: "workspace_window_move", arg: "special:magic" },
        { name: "Cambiar a Espacio 1", dispatcher: "workspace_focus", arg: "1" },
        { name: "Cambiar a Espacio 2", dispatcher: "workspace_focus", arg: "2" },
        { name: "Cambiar a Espacio 3", dispatcher: "workspace_focus", arg: "3" },
        { name: "Cambiar a Espacio 4", dispatcher: "workspace_focus", arg: "4" },
        { name: "Cambiar a Espacio 5", dispatcher: "workspace_focus", arg: "5" },
        { name: "Mover ventana a Espacio 1", dispatcher: "workspace_window_move", arg: "1" },
        { name: "Mover ventana a Espacio 2", dispatcher: "workspace_window_move", arg: "2" },
        { name: "Mover ventana a Espacio 3", dispatcher: "workspace_window_move", arg: "3" },
        { name: "Mover ventana a Espacio 4", dispatcher: "workspace_window_move", arg: "4" },
        { name: "Mover ventana a Espacio 5", dispatcher: "workspace_window_move", arg: "5" },
        { name: "Mover foco a la izquierda", dispatcher: "focus_direction", arg: "left" },
        { name: "Mover foco a la derecha", dispatcher: "focus_direction", arg: "right" },
        { name: "Mover foco hacia arriba", dispatcher: "focus_direction", arg: "up" },
        { name: "Mover foco hacia abajo", dispatcher: "focus_direction", arg: "down" },
        { name: "Menú de apagado / Salir de Hyprland", dispatcher: "exit", arg: "" }
    ]

    readonly property var commonKeys: [
        "RETURN", "SPACE", "TAB", "Escape", "Print",
        "A", "B", "C", "D", "E", "F", "J", "L", "M", "Q", "S", "W", "X",
        "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
        "left", "right", "up", "down"
    ]

    function refresh() {
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

    function openAddDialog() {
        root.isEditing = false;
        root.editingId = "";
        root.formCategory = "Personalizados";
        root.formDesc = "";
        root.formModSuper = true;
        root.formModCtrl = false;
        root.formModAlt = false;
        root.formModShift = false;
        root.formKey = "B";
        root.formActionType = "exec";
        root.formExecCmd = "";
        root.formDispatcher = "window.close";
        root.formDispatcherArg = "";
        root.showForm = true;
    }

    function openEditDialog(item) {
        root.isEditing = true;
        root.editingId = item.id;
        root.formCategory = item.category || "Personalizados";
        root.formDesc = item.description || "";
        const mods = item.mods || [];
        root.formModSuper = mods.includes("SUPER");
        root.formModCtrl = mods.includes("CTRL");
        root.formModAlt = mods.includes("ALT");
        root.formModShift = mods.includes("SHIFT");
        root.formKey = item.key || "";
        root.formActionType = item.action_type || "exec";
        root.formExecCmd = item.exec || "";
        root.formDispatcher = item.dispatcher || "window.close";
        root.formDispatcherArg = item.dispatcher_arg || "";
        root.showForm = true;
    }

    function saveCurrentForm() {
        if (!root.formKey.trim()) {
            showFeedback(Translation.tr("Debes especificar una tecla"), true);
            return;
        }
        if (!root.formDesc.trim()) {
            showFeedback(Translation.tr("Debes indicar una descripción para el atajo"), true);
            return;
        }

        const modsList = [];
        if (root.formModSuper) modsList.push("SUPER");
        if (root.formModCtrl) modsList.push("CTRL");
        if (root.formModAlt) modsList.push("ALT");
        if (root.formModShift) modsList.push("SHIFT");

        if (root.formActionType === "exec") {
            if (!root.formExecCmd.trim()) {
                showFeedback(Translation.tr("Debes indicar el comando a ejecutar"), true);
                return;
            }
            if (root.isEditing) {
                actionProcess.command = [
                    "python3", root.managerScript, "update",
                    "--id", root.editingId,
                    "--desc", root.formDesc.trim(),
                    "--mods", modsList.join(","),
                    "--key", root.formKey.trim(),
                    "--type", "exec",
                    "--exec", root.formExecCmd.trim()
                ];
            } else {
                actionProcess.command = [
                    "python3", root.managerScript, "add",
                    "--category", root.formCategory.trim() || "Personalizados",
                    "--desc", root.formDesc.trim(),
                    "--mods", modsList.join(","),
                    "--key", root.formKey.trim(),
                    "--type", "exec",
                    "--exec", root.formExecCmd.trim()
                ];
            }
        } else {
            // Dispatcher
            if (root.isEditing) {
                actionProcess.command = [
                    "python3", root.managerScript, "update",
                    "--id", root.editingId,
                    "--desc", root.formDesc.trim(),
                    "--mods", modsList.join(","),
                    "--key", root.formKey.trim(),
                    "--type", "dispatcher",
                    "--dispatcher", root.formDispatcher,
                    "--dispatcher-arg", root.formDispatcherArg || ""
                ];
            } else {
                actionProcess.command = [
                    "python3", root.managerScript, "add",
                    "--category", root.formCategory.trim() || "Personalizados",
                    "--desc", root.formDesc.trim(),
                    "--mods", modsList.join(","),
                    "--key", root.formKey.trim(),
                    "--type", "dispatcher",
                    "--dispatcher", root.formDispatcher,
                    "--dispatcher-arg", root.formDispatcherArg || ""
                ];
            }
        }

        actionProcess.running = true;
        root.showForm = false;
        showFeedback(root.isEditing ? Translation.tr("Atajo actualizado correctamente") : Translation.tr("Nuevo atajo añadido"), false);
    }

    function deleteItem(item) {
        actionProcess.command = ["python3", root.managerScript, "delete", "--id", item.id];
        actionProcess.running = true;
        showFeedback(Translation.tr("Atajo '%1' eliminado").arg(item.description || item.id), false);
    }

    function resetItem(item) {
        actionProcess.command = ["python3", root.managerScript, "reset", "--id", item.id];
        actionProcess.running = true;
        showFeedback(Translation.tr("Atajo '%1' restaurado a sus valores por defecto").arg(item.description || item.id), false);
    }

    function resetAllBinds() {
        actionProcess.command = ["python3", root.managerScript, "reset"];
        actionProcess.running = true;
        showFeedback(Translation.tr("Todos los atajos se han restaurado a la configuración original"), false);
    }

    function getFilteredList() {
        let list = root.keybindsList || [];
        if (root.selectedCategory !== "Todos") {
            list = list.filter(b => (b.category || "Otros").toLowerCase() === root.selectedCategory.toLowerCase());
        }
        if (root.searchQuery.trim() !== "") {
            const q = root.searchQuery.toLowerCase().trim();
            list = list.filter(b => {
                const desc = (b.description || "").toLowerCase();
                const key = (b.key || "").toLowerCase();
                const mods = (b.mods || []).join(" ").toLowerCase();
                const exec = (b.exec || "").toLowerCase();
                const cat = (b.category || "").toLowerCase();
                return desc.includes(q) || key.includes(q) || mods.includes(q) || exec.includes(q) || cat.includes(q);
            });
        }
        return list;
    }

    function getCategoryCount(cat) {
        if (!root.keybindsList) return 0;
        if (cat === "Todos") return root.keybindsList.length;
        return root.keybindsList.filter(b => (b.category || "Otros").toLowerCase() === cat.toLowerCase()).length;
    }

    // Backend process to list current keybinds
    Process {
        id: listProcess
        running: true
        command: ["python3", root.managerScript, "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                if (!text || !text.trim()) {
                    root.keybindsList = [];
                    return;
                }
                try {
                    root.keybindsList = JSON.parse(text);
                } catch (e) {
                    console.error("[KeybindsManager] Error parsing keybinds list:", e);
                }
            }
        }
    }

    // Mutation process (add, update, delete, reset)
    Process {
        id: actionProcess
        onExited: (exitCode, exitStatus) => {
            root.refresh();
        }
    }

    Component.onCompleted: {
        root.refresh();
    }

    // --- UI CONTENT ---

    ContentSection {
        icon: "keyboard"
        title: Translation.tr("Atajos de teclado (Keybinds)")

        // Banner informativo
        NoticeBox {
            Layout.fillWidth: true
            text: Translation.tr("Configura los atajos de teclado de Hyprland fácilmente sin editar archivos Lua. Cualquier cambio se compila y aplica al sistema en tiempo real.")
        }

        // Notificación flotante de feedback
        Revealer {
            reveal: root.feedbackMessage !== ""
            vertical: true
            Layout.fillWidth: true
            Rectangle {
                width: parent.width
                implicitHeight: 38
                radius: Appearance.rounding.small
                color: root.feedbackIsError ? Appearance.colors.colErrorContainer : Appearance.colors.colPrimaryContainer

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    anchors.rightMargin: 14
                    spacing: 10
                    MaterialSymbol {
                        iconSize: 20
                        text: root.feedbackIsError ? "error" : "check_circle"
                        color: root.feedbackIsError ? Appearance.colors.colOnErrorContainer : Appearance.colors.colOnPrimaryContainer
                    }
                    StyledText {
                        Layout.fillWidth: true
                        text: root.feedbackMessage
                        font.pixelSize: Appearance.font.pixelSize.small
                        font.weight: Font.Medium
                        color: root.feedbackIsError ? Appearance.colors.colOnErrorContainer : Appearance.colors.colOnPrimaryContainer
                    }
                }
            }
        }

        // Barra superior de acciones
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            RippleButtonWithIcon {
                Layout.fillWidth: true
                materialIcon: "add"
                mainText: Translation.tr("Añadir atajo")
                colBackground: Appearance.colors.colPrimaryContainer
                onClicked: {
                    if (root.showForm && !root.isEditing) {
                        root.showForm = false;
                    } else {
                        root.openAddDialog();
                    }
                }
            }

            RippleButtonWithIcon {
                Layout.fillWidth: false
                materialIcon: "restart_alt"
                mainText: Translation.tr("Restaurar por defecto")
                colBackground: Appearance.colors.colLayer2
                onClicked: root.resetAllBinds()
                StyledToolTip {
                    text: Translation.tr("Restaurar todos los atajos originales del sistema")
                }
            }

            RippleButton {
                Layout.fillWidth: false
                implicitWidth: 38
                implicitHeight: 35
                buttonRadius: Appearance.rounding.small
                colBackground: Appearance.colors.colLayer2
                onClicked: root.refresh()
                contentItem: MaterialSymbol {
                    anchors.centerIn: parent
                    iconSize: 18
                    text: "refresh"
                    color: Appearance.colors.colOnSecondaryContainer
                }
                StyledToolTip {
                    text: Translation.tr("Actualizar lista de atajos")
                }
            }
        }

        // --- FORMULARIO EXPANDIBLE (Añadir / Editar Atajo) ---
        Revealer {
            reveal: root.showForm
            vertical: true
            Layout.fillWidth: true

            Rectangle {
                width: parent.width
                implicitHeight: formColumn.implicitHeight + 28
                radius: Appearance.rounding.normal
                color: Appearance.colors.colLayer2
                border.width: 1
                border.color: Appearance.colors.colPrimary

                ColumnLayout {
                    id: formColumn
                    anchors {
                        top: parent.top
                        left: parent.left
                        right: parent.right
                        margins: 14
                    }
                    spacing: 12

                    // Cabecera del formulario
                    RowLayout {
                        Layout.fillWidth: true
                        MaterialSymbol {
                            iconSize: 22
                            text: root.isEditing ? "edit" : "add_circle"
                            color: Appearance.colors.colPrimary
                        }
                        StyledText {
                            text: root.isEditing ? Translation.tr("Editar atajo de teclado") : Translation.tr("Añadir nuevo atajo de teclado")
                            font.pixelSize: Appearance.font.pixelSize.normal
                            font.weight: Font.DemiBold
                            color: Appearance.colors.colOnSecondaryContainer
                            Layout.fillWidth: true
                        }
                        RippleButton {
                            implicitWidth: 32
                            implicitHeight: 32
                            buttonRadius: Appearance.rounding.full
                            onClicked: root.showForm = false
                            contentItem: MaterialSymbol {
                                anchors.centerIn: parent
                                iconSize: 18
                                text: "close"
                                color: Appearance.colors.colOnSecondaryContainer
                            }
                        }
                    }

                    // Descripción
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        StyledText {
                            text: Translation.tr("Descripción o nombre del atajo")
                            font.pixelSize: Appearance.font.pixelSize.smaller
                            color: Appearance.colors.colOutline
                        }
                        MaterialTextField {
                            Layout.fillWidth: true
                            placeholderText: Translation.tr("Ej: Abrir navegador, Cerrar ventana, etc.")
                            text: root.formDesc
                            onTextChanged: root.formDesc = text
                        }
                    }

                    // Fila de Modificadores Interactivos
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        StyledText {
                            text: Translation.tr("Teclas modificadoras (haz clic para alternar)")
                            font.pixelSize: Appearance.font.pixelSize.smaller
                            color: Appearance.colors.colOutline
                        }

                        RowLayout {
                            spacing: 8
                            Layout.fillWidth: true

                            // Botón SUPER
                            Rectangle {
                                implicitWidth: 80
                                implicitHeight: 36
                                radius: Appearance.rounding.small
                                color: root.formModSuper ? Appearance.colors.colPrimary : Appearance.colors.colLayer3
                                border.width: 1
                                border.color: root.formModSuper ? Appearance.colors.colPrimary : Appearance.colors.colOutlineVariant
                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: root.formModSuper = !root.formModSuper
                                }
                                StyledText {
                                    anchors.centerIn: parent
                                    text: " SUPER"
                                    font.pixelSize: Appearance.font.pixelSize.smaller
                                    font.weight: Font.DemiBold
                                    color: root.formModSuper ? Appearance.colors.colOnPrimary : Appearance.colors.colOnSecondaryContainer
                                }
                            }

                            // Botón CTRL
                            Rectangle {
                                implicitWidth: 80
                                implicitHeight: 36
                                radius: Appearance.rounding.small
                                color: root.formModCtrl ? Appearance.colors.colPrimary : Appearance.colors.colLayer3
                                border.width: 1
                                border.color: root.formModCtrl ? Appearance.colors.colPrimary : Appearance.colors.colOutlineVariant
                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: root.formModCtrl = !root.formModCtrl
                                }
                                StyledText {
                                    anchors.centerIn: parent
                                    text: "󰘴 CTRL"
                                    font.pixelSize: Appearance.font.pixelSize.smaller
                                    font.weight: Font.DemiBold
                                    color: root.formModCtrl ? Appearance.colors.colOnPrimary : Appearance.colors.colOnSecondaryContainer
                                }
                            }

                            // Botón ALT
                            Rectangle {
                                implicitWidth: 80
                                implicitHeight: 36
                                radius: Appearance.rounding.small
                                color: root.formModAlt ? Appearance.colors.colPrimary : Appearance.colors.colLayer3
                                border.width: 1
                                border.color: root.formModAlt ? Appearance.colors.colPrimary : Appearance.colors.colOutlineVariant
                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: root.formModAlt = !root.formModAlt
                                }
                                StyledText {
                                    anchors.centerIn: parent
                                    text: "󰘵 ALT"
                                    font.pixelSize: Appearance.font.pixelSize.smaller
                                    font.weight: Font.DemiBold
                                    color: root.formModAlt ? Appearance.colors.colOnPrimary : Appearance.colors.colOnSecondaryContainer
                                }
                            }

                            // Botón SHIFT
                            Rectangle {
                                implicitWidth: 80
                                implicitHeight: 36
                                radius: Appearance.rounding.small
                                color: root.formModShift ? Appearance.colors.colPrimary : Appearance.colors.colLayer3
                                border.width: 1
                                border.color: root.formModShift ? Appearance.colors.colPrimary : Appearance.colors.colOutlineVariant
                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: root.formModShift = !root.formModShift
                                }
                                StyledText {
                                    anchors.centerIn: parent
                                    text: "󰘶 SHIFT"
                                    font.pixelSize: Appearance.font.pixelSize.smaller
                                    font.weight: Font.DemiBold
                                    color: root.formModShift ? Appearance.colors.colOnPrimary : Appearance.colors.colOnSecondaryContainer
                                }
                            }

                            Item { Layout.fillWidth: true }

                            // Vista previa visual de la combinación
                            Rectangle {
                                implicitHeight: 36
                                implicitWidth: previewRow.implicitWidth + 16
                                radius: Appearance.rounding.small
                                color: Appearance.colors.colLayer1
                                border.width: 1
                                border.color: Appearance.colors.colOutlineVariant

                                RowLayout {
                                    id: previewRow
                                    anchors.centerIn: parent
                                    spacing: 4
                                    StyledText {
                                        text: Translation.tr("Atajo:")
                                        font.pixelSize: Appearance.font.pixelSize.smaller
                                        color: Appearance.colors.colOutline
                                    }
                                    KeyboardKey { visible: root.formModSuper; key: "SUPER" }
                                    KeyboardKey { visible: root.formModCtrl; key: "CTRL" }
                                    KeyboardKey { visible: root.formModAlt; key: "ALT" }
                                    KeyboardKey { visible: root.formModShift; key: "SHIFT" }
                                    StyledText {
                                        text: "+"
                                        font.pixelSize: Appearance.font.pixelSize.smaller
                                        color: Appearance.colors.colOutline
                                    }
                                    KeyboardKey { key: root.formKey || "?" }
                                }
                            }
                        }
                    }

                    // Selector de Tecla
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        StyledText {
                            text: Translation.tr("Tecla principal (escribe o selecciona de los botones rápidos)")
                            font.pixelSize: Appearance.font.pixelSize.smaller
                            color: Appearance.colors.colOutline
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            MaterialTextField {
                                Layout.preferredWidth: 160
                                placeholderText: Translation.tr("Ej: B, RETURN, F1...")
                                text: root.formKey
                                onTextChanged: root.formKey = text
                            }

                            // Botones rápidos de teclas comunes
                            Flickable {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 36
                                contentWidth: keyChipsRow.implicitWidth
                                clip: true
                                Row {
                                    id: keyChipsRow
                                    spacing: 6
                                    Repeater {
                                        model: root.commonKeys
                                        delegate: Rectangle {
                                            required property string modelData
                                            implicitWidth: chipText.implicitWidth + 16
                                            implicitHeight: 32
                                            radius: Appearance.rounding.small
                                            color: (root.formKey.toLowerCase() === modelData.toLowerCase()) ? Appearance.colors.colSecondaryContainer : Appearance.colors.colLayer3
                                            border.width: 1
                                            border.color: (root.formKey.toLowerCase() === modelData.toLowerCase()) ? Appearance.colors.colPrimary : Appearance.colors.colOutlineVariant
                                            MouseArea {
                                                anchors.fill: parent
                                                cursorShape: Qt.PointingHandCursor
                                                onClicked: root.formKey = modelData
                                            }
                                            StyledText {
                                                id: chipText
                                                anchors.centerIn: parent
                                                text: modelData
                                                font.pixelSize: Appearance.font.pixelSize.smaller - 1
                                                font.family: Appearance.font.family.monospace
                                                color: Appearance.colors.colOnSecondaryContainer
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // Selector de Tipo de Acción
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12

                        Rectangle {
                            implicitHeight: 34
                            implicitWidth: 160
                            radius: Appearance.rounding.small
                            color: root.formActionType === "exec" ? Appearance.colors.colSecondaryContainer : Appearance.colors.colLayer3
                            border.width: 1
                            border.color: root.formActionType === "exec" ? Appearance.colors.colPrimary : Appearance.colors.colOutlineVariant
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.formActionType = "exec"
                            }
                            RowLayout {
                                anchors.centerIn: parent
                                spacing: 6
                                MaterialSymbol { iconSize: 18; text: "terminal"; color: Appearance.colors.colOnSecondaryContainer }
                                StyledText { text: Translation.tr("Ejecutar comando"); font.pixelSize: Appearance.font.pixelSize.smaller; font.weight: Font.Medium }
                            }
                        }

                        Rectangle {
                            implicitHeight: 34
                            implicitWidth: 160
                            radius: Appearance.rounding.small
                            color: root.formActionType === "dispatcher" ? Appearance.colors.colSecondaryContainer : Appearance.colors.colLayer3
                            border.width: 1
                            border.color: root.formActionType === "dispatcher" ? Appearance.colors.colPrimary : Appearance.colors.colOutlineVariant
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.formActionType = "dispatcher"
                            }
                            RowLayout {
                                anchors.centerIn: parent
                                spacing: 6
                                MaterialSymbol { iconSize: 18; text: "tune"; color: Appearance.colors.colOnSecondaryContainer }
                                StyledText { text: Translation.tr("Acción de ventana"); font.pixelSize: Appearance.font.pixelSize.smaller; font.weight: Font.Medium }
                            }
                        }

                        Item { Layout.fillWidth: true }
                    }

                    // Campo según el tipo de acción
                    ColumnLayout {
                        visible: root.formActionType === "exec"
                        Layout.fillWidth: true
                        spacing: 4
                        StyledText {
                            text: Translation.tr("Comando a ejecutar (binario, script o comando shell)")
                            font.pixelSize: Appearance.font.pixelSize.smaller
                            color: Appearance.colors.colOutline
                        }
                        MaterialTextField {
                            Layout.fillWidth: true
                            placeholderText: Translation.tr("Ej: firefox, flatpak run ..., kitty -e btop, etc.")
                            text: root.formExecCmd
                            onTextChanged: root.formExecCmd = text
                        }
                    }

                    ColumnLayout {
                        visible: root.formActionType === "dispatcher"
                        Layout.fillWidth: true
                        spacing: 4
                        StyledText {
                            text: Translation.tr("Acción predefinida de Hyprland")
                            font.pixelSize: Appearance.font.pixelSize.smaller
                            color: Appearance.colors.colOutline
                        }
                        StyledComboBox {
                            Layout.fillWidth: true
                            textRole: "name"
                            model: root.dispatcherPresets
                            currentIndex: 0
                            onActivated: (index) => {
                                root.formDispatcher = model[index].dispatcher;
                                root.formDispatcherArg = model[index].arg || "";
                            }
                        }
                    }

                    // Botones de guardar / cancelar
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.topMargin: 6
                        Item { Layout.fillWidth: true }

                        DialogButton {
                            buttonText: Translation.tr("Cancelar")
                            onClicked: root.showForm = false
                        }

                        RippleButtonWithIcon {
                            materialIcon: "check"
                            mainText: root.isEditing ? Translation.tr("Guardar cambios") : Translation.tr("Añadir atajo")
                            buttonRadius: Appearance.rounding.small
                            colBackground: Appearance.colors.colPrimaryContainer
                            onClicked: root.saveCurrentForm()
                        }
                    }
                }
            }
        }

        // --- FILTROS Y BÚSQUEDA ---
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            // Campo de búsqueda
            MaterialTextField {
                Layout.fillWidth: true
                placeholderText: Translation.tr("Buscar atajo por tecla, descripción, comando o categoría...")
                text: root.searchQuery
                onTextChanged: root.searchQuery = text
            }

            RippleButton {
                visible: root.searchQuery.length > 0
                implicitWidth: 36
                implicitHeight: 36
                buttonRadius: Appearance.rounding.full
                colBackground: Appearance.colors.colLayer2
                onClicked: root.searchQuery = ""
                contentItem: MaterialSymbol {
                    anchors.centerIn: parent
                    iconSize: 18
                    text: "close"
                    color: Appearance.colors.colOnSecondaryContainer
                }
            }
        }

        // Chips de Categorías
        Flickable {
            Layout.fillWidth: true
            Layout.preferredHeight: 38
            contentWidth: catChipsRow.implicitWidth
            clip: true
            Row {
                id: catChipsRow
                spacing: 8
                Repeater {
                    model: root.categoryTabs
                    delegate: Rectangle {
                        required property string modelData
                        property bool isSelected: root.selectedCategory === modelData
                        implicitWidth: catLabel.implicitWidth + 24
                        implicitHeight: 34
                        radius: Appearance.rounding.full
                        color: isSelected ? Appearance.colors.colPrimaryContainer : Appearance.colors.colLayer2
                        border.width: 1
                        border.color: isSelected ? Appearance.colors.colPrimary : Appearance.colors.colOutlineVariant

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.selectedCategory = modelData
                        }

                        RowLayout {
                            id: catLabel
                            anchors.centerIn: parent
                            spacing: 6
                            StyledText {
                                text: modelData
                                font.pixelSize: Appearance.font.pixelSize.smaller
                                font.weight: isSelected ? Font.DemiBold : Font.Normal
                                color: isSelected ? Appearance.colors.colOnPrimaryContainer : Appearance.colors.colOnSecondaryContainer
                            }
                            Rectangle {
                                implicitWidth: countText.implicitWidth + 8
                                implicitHeight: 18
                                radius: Appearance.rounding.full
                                color: isSelected ? Appearance.colors.colPrimary : Appearance.colors.colLayer3
                                StyledText {
                                    id: countText
                                    anchors.centerIn: parent
                                    text: root.getCategoryCount(modelData)
                                    font.pixelSize: Appearance.font.pixelSize.smaller - 2
                                    font.weight: Font.Bold
                                    color: isSelected ? Appearance.colors.colOnPrimary : Appearance.colors.colOutline
                                }
                            }
                        }
                    }
                }
            }
        }

        // --- LISTA DE ATAJOS DE TECLADO ---
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8

            // Estado vacío cuando no hay coincidencias
            Rectangle {
                visible: root.getFilteredList().length === 0
                Layout.fillWidth: true
                implicitHeight: 140
                radius: Appearance.rounding.normal
                color: Appearance.colors.colLayer2
                border.width: 1
                border.color: Appearance.colors.colOutlineVariant

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 8
                    MaterialSymbol {
                        Layout.alignment: Qt.AlignHCenter
                        iconSize: 38
                        text: "search_off"
                        color: Appearance.colors.colOutline
                    }
                    StyledText {
                        Layout.alignment: Qt.AlignHCenter
                        text: Translation.tr("No se encontraron atajos de teclado")
                        font.pixelSize: Appearance.font.pixelSize.normal
                        font.weight: Font.DemiBold
                        color: Appearance.colors.colOnSecondaryContainer
                    }
                    StyledText {
                        Layout.alignment: Qt.AlignHCenter
                        text: Translation.tr("Prueba con otros términos de búsqueda o selecciona otra categoría.")
                        font.pixelSize: Appearance.font.pixelSize.small
                        color: Appearance.colors.colOutline
                    }
                }
            }

            // Repeater de Atajos
            Repeater {
                model: root.getFilteredList()

                delegate: Rectangle {
                    id: bindCard
                    required property var modelData
                    Layout.fillWidth: true
                    implicitHeight: 70
                    radius: Appearance.rounding.normal
                    color: Appearance.colors.colLayer2
                    border.width: 1
                    border.color: Appearance.colors.colOutlineVariant

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 16
                        anchors.rightMargin: 16
                        spacing: 16

                        // Insignias Visuales de Teclado
                        RowLayout {
                            spacing: 4
                            Layout.preferredWidth: 210
                            Layout.fillWidth: false
                            Layout.alignment: Qt.AlignVCenter

                            Repeater {
                                model: modelData.mods || []
                                delegate: RowLayout {
                                    spacing: 4
                                    required property string modelData
                                    KeyboardKey {
                                        key: modelData
                                    }
                                    StyledText {
                                        text: "+"
                                        font.pixelSize: Appearance.font.pixelSize.smaller
                                        color: Appearance.colors.colOutline
                                    }
                                }
                            }

                            KeyboardKey {
                                key: modelData.key || ""
                            }
                        }

                        // Columna Informativa
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 3
                            Layout.alignment: Qt.AlignVCenter

                            RowLayout {
                                spacing: 8
                                // Chip de Categoría
                                Rectangle {
                                    implicitWidth: catTagText.implicitWidth + 10
                                    implicitHeight: 18
                                    radius: Appearance.rounding.small
                                    color: Appearance.colors.colSurfaceContainerHigh

                                    StyledText {
                                        id: catTagText
                                        anchors.centerIn: parent
                                        text: modelData.category || "General"
                                        font.pixelSize: Appearance.font.pixelSize.smaller - 2
                                        font.weight: Font.Medium
                                        color: Appearance.colors.colOutline
                                    }
                                }

                                StyledText {
                                    text: modelData.description || modelData.id
                                    font.pixelSize: Appearance.font.pixelSize.normal
                                    font.weight: Font.DemiBold
                                    color: Appearance.colors.colOnSecondaryContainer
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                            }

                            // Comando o acción en fuente monoespaciada
                            StyledText {
                                text: modelData.action_type === "exec" ? (modelData.exec || "") : ("Acción: " + (modelData.dispatcher || "") + (modelData.dispatcher_arg ? " (" + modelData.dispatcher_arg + ")" : ""))
                                font.pixelSize: Appearance.font.pixelSize.smaller
                                font.family: Appearance.font.family.monospace
                                color: Appearance.colors.colOutline
                                elide: Text.ElideMiddle
                                Layout.fillWidth: true
                            }
                        }

                        // Insignia de Estado (Personalizado / Default)
                        Rectangle {
                            visible: !modelData.is_default
                            implicitWidth: badgeText.implicitWidth + 12
                            implicitHeight: 22
                            radius: Appearance.rounding.full
                            color: Appearance.colors.colPrimaryContainer

                            StyledText {
                                id: badgeText
                                anchors.centerIn: parent
                                text: Translation.tr("Personalizado")
                                font.pixelSize: Appearance.font.pixelSize.smaller - 1
                                font.weight: Font.Medium
                                color: Appearance.colors.colOnPrimaryContainer
                            }
                        }

                        // Botón Editar
                        RippleButton {
                            implicitWidth: 36
                            implicitHeight: 36
                            buttonRadius: Appearance.rounding.full
                            colBackground: Appearance.colors.colLayer3
                            onClicked: root.openEditDialog(modelData)
                            contentItem: MaterialSymbol {
                                anchors.centerIn: parent
                                iconSize: 18
                                text: "edit"
                                color: Appearance.colors.colOnSecondaryContainer
                            }
                            StyledToolTip {
                                text: Translation.tr("Editar combinación o acción")
                            }
                        }

                        // Botón Eliminar o Restaurar
                        RippleButton {
                            implicitWidth: 36
                            implicitHeight: 36
                            buttonRadius: Appearance.rounding.full
                            colBackground: Appearance.colors.colLayer3
                            colBackgroundHover: modelData.is_default ? Appearance.colors.colLayer3 : Appearance.colors.colErrorContainer
                            colRipple: modelData.is_default ? Appearance.colors.colPrimary : Appearance.colors.colError
                            onClicked: {
                                if (modelData.is_default) {
                                    root.resetItem(modelData);
                                } else {
                                    root.deleteItem(modelData);
                                }
                            }
                            contentItem: MaterialSymbol {
                                anchors.centerIn: parent
                                iconSize: 18
                                text: modelData.is_default ? "undo" : "delete"
                                color: modelData.is_default ? Appearance.colors.colOutline : Appearance.colors.colOnSecondaryContainer
                            }
                            StyledToolTip {
                                text: modelData.is_default ? Translation.tr("Restaurar tecla original") : Translation.tr("Eliminar atajo")
                            }
                        }
                    }
                }
            }
        }
    }
}
