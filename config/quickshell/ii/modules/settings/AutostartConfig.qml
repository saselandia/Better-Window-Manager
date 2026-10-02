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

    property var autostartItems: []
    property var installedApps: []
    property string searchQuery: ""
    property bool showAppPicker: false
    property bool showCustomDialog: false
    property string feedbackMessage: ""
    property bool feedbackIsError: false

    // Custom form fields
    property string customNameText: ""
    property string customExecText: ""
    property string customIconText: "application-x-executable"
    property string customCommentText: ""

    readonly property string managerScript: FileUtils.trimFileProtocol(Directories.home) + "/.config/hypr/scripts/autostart-manager.py"

    function refresh() {
        listProcess.running = false;
        listProcess.running = true;
    }

    function loadInstalledApps() {
        if (installedApps.length === 0) {
            appsProcess.running = false;
            appsProcess.running = true;
        }
    }

    function showFeedback(msg, isError) {
        root.feedbackMessage = msg;
        root.feedbackIsError = !!isError;
        feedbackTimer.restart();
    }

    Timer {
        id: feedbackTimer
        interval: 3500
        onTriggered: root.feedbackMessage = ""
    }

    function toggleItem(filename, enable) {
        actionProcess.command = ["python3", root.managerScript, "toggle", filename, enable ? "true" : "false"];
        actionProcess.running = true;
        showFeedback(enable ? Translation.tr("Aplicación activada en inicio") : Translation.tr("Aplicación desactivada de inicio"), false);
    }

    function removeItem(filename, name) {
        actionProcess.command = ["python3", root.managerScript, "remove", filename];
        actionProcess.running = true;
        showFeedback(Translation.tr("'%1' eliminada de inicio automático").arg(name || filename), false);
    }

    function addApp(appId, appName) {
        actionProcess.command = ["python3", root.managerScript, "add-app", appId];
        actionProcess.running = true;
        showFeedback(Translation.tr("'%1' añadida al inicio automático").arg(appName || appId), false);
    }

    function addCustom(name, execCmd, icon, comment) {
        if (!name.trim() || !execCmd.trim()) {
            showFeedback(Translation.tr("El nombre y el comando son obligatorios"), true);
            return;
        }
        actionProcess.command = [
            "python3", root.managerScript, "add-custom",
            "--name", name.trim(),
            "--exec", execCmd.trim(),
            "--icon", icon.trim() || "application-x-executable",
            "--comment", comment.trim()
        ];
        actionProcess.running = true;
        root.showCustomDialog = false;
        root.customNameText = "";
        root.customExecText = "";
        root.customIconText = "application-x-executable";
        root.customCommentText = "";
        showFeedback(Translation.tr("Comando '%1' añadido al inicio").arg(name), false);
    }

    function testRun(filename, name) {
        testRunProcess.command = ["python3", root.managerScript, "run-one", filename];
        testRunProcess.running = true;
        showFeedback(Translation.tr("Ejecutando '%1'...").arg(name || filename), false);
    }

    function runAllAutostart() {
        actionProcess.command = ["python3", root.managerScript, "run-all", "--force"];
        actionProcess.running = true;
        showFeedback(Translation.tr("Ejecutando todas las aplicaciones activas de inicio..."), false);
    }

    function isAppInAutostart(appId) {
        for (let i = 0; i < root.autostartItems.length; i++) {
            if (root.autostartItems[i].file === appId || 
                root.autostartItems[i].name.toLowerCase() === appId.toLowerCase()) {
                return true;
            }
        }
        return false;
    }

    // Backend process to list current autostart entries
    Process {
        id: listProcess
        running: true
        command: ["python3", root.managerScript, "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                if (!text || !text.trim()) {
                    root.autostartItems = [];
                    return;
                }
                try {
                    root.autostartItems = JSON.parse(text);
                } catch (e) {
                    console.error("[Autostart] Error parsing autostart items:", e, "raw text:", text);
                }
            }
        }
    }

    // Backend process to list installed system & flatpak apps
    Process {
        id: appsProcess
        command: ["python3", root.managerScript, "list-apps"]
        stdout: StdioCollector {
            onStreamFinished: {
                if (!text || !text.trim()) return;
                try {
                    root.installedApps = JSON.parse(text);
                } catch (e) {
                    console.error("[Autostart] Error parsing installed apps:", e);
                }
            }
        }
    }

    // Single run-one process
    Process {
        id: testRunProcess
    }

    // Mutation process (toggle, remove, add, run-all)
    Process {
        id: actionProcess
        onExited: (exitCode, exitStatus) => {
            root.refresh();
        }
    }

    Component.onCompleted: {
        root.refresh();
    }

    // --- UI Content ---

    ContentSection {
        icon: "rocket_launch"
        title: Translation.tr("Inicio Automático (Autostart)")

        // Information banner
        NoticeBox {
            Layout.fillWidth: true
            text: Translation.tr("Las aplicaciones configuradas aquí se iniciarán automáticamente al encender el equipo e iniciar sesión en Hyprland. Es compatible con el estándar XDG de GNOME y KDE (~/.config/autostart).")
        }

        // Feedback notification badge
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

        // Action Buttons Row
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            RippleButtonWithIcon {
                Layout.fillWidth: true
                materialIcon: "add"
                mainText: Translation.tr("Añadir aplicación")
                colBackground: Appearance.colors.colPrimaryContainer
                onClicked: {
                    root.showCustomDialog = false;
                    root.showAppPicker = !root.showAppPicker;
                    if (root.showAppPicker) {
                        root.loadInstalledApps();
                    }
                }
            }

            RippleButtonWithIcon {
                Layout.fillWidth: true
                materialIcon: "terminal"
                mainText: Translation.tr("Comando personalizado")
                colBackground: Appearance.colors.colLayer2
                onClicked: {
                    root.showAppPicker = false;
                    root.showCustomDialog = !root.showCustomDialog;
                }
            }

            RippleButtonWithIcon {
                Layout.fillWidth: false
                materialIcon: "play_arrow"
                mainText: Translation.tr("Ejecutar ahora")
                colBackground: Appearance.colors.colLayer2
                onClicked: root.runAllAutostart()
                StyledToolTip {
                    text: Translation.tr("Ejecuta todas las aplicaciones habilitadas ahora mismo")
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
                    text: Translation.tr("Actualizar lista")
                }
            }
        }

        // --- EXPANDABLE: App Picker View ---
        Revealer {
            reveal: root.showAppPicker
            vertical: true
            Layout.fillWidth: true

            Rectangle {
                width: parent.width
                implicitHeight: appPickerColumn.implicitHeight + 24
                radius: Appearance.rounding.normal
                color: Appearance.colors.colLayer2
                border.width: 1
                border.color: Appearance.colors.colOutlineVariant

                ColumnLayout {
                    id: appPickerColumn
                    anchors {
                        top: parent.top
                        left: parent.left
                        right: parent.right
                        margins: 14
                    }
                    spacing: 12

                    // Picker Header
                    RowLayout {
                        Layout.fillWidth: true
                        MaterialSymbol {
                            iconSize: 22
                            text: "grid_view"
                            color: Appearance.colors.colPrimary
                        }
                        StyledText {
                            text: Translation.tr("Seleccionar aplicación para inicio automático")
                            font.pixelSize: Appearance.font.pixelSize.normal
                            font.weight: Font.DemiBold
                            color: Appearance.colors.colOnSecondaryContainer
                            Layout.fillWidth: true
                        }
                        RippleButton {
                            implicitWidth: 32
                            implicitHeight: 32
                            buttonRadius: Appearance.rounding.full
                            onClicked: root.showAppPicker = false
                            contentItem: MaterialSymbol {
                                anchors.centerIn: parent
                                iconSize: 18
                                text: "close"
                                color: Appearance.colors.colOnSecondaryContainer
                            }
                        }
                    }

                    // Search Input
                    MaterialTextField {
                        id: appSearchField
                        Layout.fillWidth: true
                        placeholderText: Translation.tr("Buscar por nombre o comando (ej: Discord, Steam, Kate...)")
                        text: root.searchQuery
                        onTextChanged: root.searchQuery = text
                    }

                    // Loading indicator if apps are still loading
                    Item {
                        visible: root.installedApps.length === 0
                        Layout.fillWidth: true
                        implicitHeight: 80
                        RowLayout {
                            anchors.centerIn: parent
                            spacing: 12
                            MaterialLoadingIndicator {
                                implicitSize: 28
                            }
                            StyledText {
                                text: Translation.tr("Cargando lista de aplicaciones instaladas...")
                                color: Appearance.colors.colOutline
                            }
                        }
                    }

                    // Filtered List of Apps
                    StyledFlickable {
                        visible: root.installedApps.length > 0
                        Layout.fillWidth: true
                        implicitHeight: Math.min(320, appListColumn.implicitHeight)
                        contentHeight: appListColumn.implicitHeight
                        clip: true

                        ColumnLayout {
                            id: appListColumn
                            width: parent.width
                            spacing: 6

                            Repeater {
                                model: {
                                    const q = root.searchQuery.trim().toLowerCase();
                                    if (!q) return root.installedApps;
                                    return root.installedApps.filter(app => {
                                        return (app.name && app.name.toLowerCase().includes(q)) ||
                                               (app.exec && app.exec.toLowerCase().includes(q)) ||
                                               (app.id && app.id.toLowerCase().includes(q));
                                    });
                                }

                                delegate: Rectangle {
                                    id: appRow
                                    required property var modelData
                                    Layout.fillWidth: true
                                    implicitHeight: 52
                                    radius: Appearance.rounding.small
                                    color: mouseArea.containsMouse ? Appearance.colors.colLayer3 : Appearance.colors.colLayer1

                                    readonly property bool alreadyAdded: root.isAppInAutostart(modelData.id)

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 12
                                        anchors.rightMargin: 12
                                        spacing: 12

                                        Kirigami.Icon {
                                            implicitWidth: 32
                                            implicitHeight: 32
                                            source: modelData.icon || "application-x-executable"
                                            roundToIconSize: false
                                        }

                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: 2
                                            StyledText {
                                                text: modelData.name
                                                font.pixelSize: Appearance.font.pixelSize.small
                                                font.weight: Font.DemiBold
                                                color: Appearance.colors.colOnSecondaryContainer
                                                elide: Text.ElideRight
                                            }
                                            StyledText {
                                                text: modelData.exec || modelData.comment || modelData.id
                                                font.pixelSize: Appearance.font.pixelSize.smaller
                                                font.family: Appearance.font.family.monospace
                                                color: Appearance.colors.colOutline
                                                elide: Text.ElideRight
                                                Layout.fillWidth: true
                                            }
                                        }

                                        // Status badge or Add button
                                        Item {
                                            implicitWidth: addButton.implicitWidth
                                            implicitHeight: addButton.implicitHeight

                                            RippleButtonWithIcon {
                                                id: addButton
                                                visible: !appRow.alreadyAdded
                                                materialIcon: "add"
                                                mainText: Translation.tr("Añadir")
                                                buttonRadius: Appearance.rounding.small
                                                colBackground: Appearance.colors.colPrimaryContainer
                                                onClicked: {
                                                    root.addApp(modelData.id, modelData.name);
                                                }
                                            }

                                            Rectangle {
                                                visible: appRow.alreadyAdded
                                                anchors.centerIn: parent
                                                implicitWidth: 90
                                                implicitHeight: 28
                                                radius: Appearance.rounding.full
                                                color: Appearance.colors.colSurfaceContainerHigh
                                                RowLayout {
                                                    anchors.centerIn: parent
                                                    spacing: 4
                                                    MaterialSymbol {
                                                        iconSize: 14
                                                        text: "check"
                                                        color: Appearance.colors.colOutline
                                                    }
                                                    StyledText {
                                                        text: Translation.tr("Añadida")
                                                        font.pixelSize: Appearance.font.pixelSize.smaller
                                                        color: Appearance.colors.colOutline
                                                    }
                                                }
                                            }
                                        }
                                    }

                                    MouseArea {
                                        id: mouseArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        acceptedButtons: Qt.LeftButton
                                        onClicked: {
                                            if (!appRow.alreadyAdded) {
                                                root.addApp(modelData.id, modelData.name);
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // --- EXPANDABLE: Custom Command Dialog ---
        Revealer {
            reveal: root.showCustomDialog
            vertical: true
            Layout.fillWidth: true

            Rectangle {
                width: parent.width
                implicitHeight: customFormColumn.implicitHeight + 24
                radius: Appearance.rounding.normal
                color: Appearance.colors.colLayer2
                border.width: 1
                border.color: Appearance.colors.colOutlineVariant

                ColumnLayout {
                    id: customFormColumn
                    anchors {
                        top: parent.top
                        left: parent.left
                        right: parent.right
                        margins: 14
                    }
                    spacing: 12

                    RowLayout {
                        Layout.fillWidth: true
                        MaterialSymbol {
                            iconSize: 22
                            text: "terminal"
                            color: Appearance.colors.colPrimary
                        }
                        StyledText {
                            text: Translation.tr("Añadir comando personalizado a inicio")
                            font.pixelSize: Appearance.font.pixelSize.normal
                            font.weight: Font.DemiBold
                            color: Appearance.colors.colOnSecondaryContainer
                            Layout.fillWidth: true
                        }
                        RippleButton {
                            implicitWidth: 32
                            implicitHeight: 32
                            buttonRadius: Appearance.rounding.full
                            onClicked: root.showCustomDialog = false
                            contentItem: MaterialSymbol {
                                anchors.centerIn: parent
                                iconSize: 18
                                text: "close"
                                color: Appearance.colors.colOnSecondaryContainer
                            }
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        StyledText {
                            text: Translation.tr("Nombre visible")
                            font.pixelSize: Appearance.font.pixelSize.smaller
                            color: Appearance.colors.colOutline
                        }
                        MaterialTextField {
                            id: customNameInput
                            Layout.fillWidth: true
                            placeholderText: Translation.tr("Ej: Discord minimizado, Script de sincronización...")
                            text: root.customNameText
                            onTextChanged: root.customNameText = text
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        StyledText {
                            text: Translation.tr("Comando a ejecutar")
                            font.pixelSize: Appearance.font.pixelSize.smaller
                            color: Appearance.colors.colOutline
                        }
                        MaterialTextField {
                            id: customExecInput
                            Layout.fillWidth: true
                            placeholderText: Translation.tr("Ej: vesktop --start-minimized, flatpak run ..., o ruta completa")
                            text: root.customExecText
                            onTextChanged: root.customExecText = text
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            StyledText {
                                text: Translation.tr("Icono (opcional)")
                                font.pixelSize: Appearance.font.pixelSize.smaller
                                color: Appearance.colors.colOutline
                            }
                            MaterialTextField {
                                Layout.fillWidth: true
                                placeholderText: Translation.tr("Ej: terminal, vesktop, application-x-executable")
                                text: root.customIconText
                                onTextChanged: root.customIconText = text
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            StyledText {
                                text: Translation.tr("Descripción (opcional)")
                                font.pixelSize: Appearance.font.pixelSize.smaller
                                color: Appearance.colors.colOutline
                            }
                            MaterialTextField {
                                Layout.fillWidth: true
                                placeholderText: Translation.tr("Descripción corta del comando")
                                text: root.customCommentText
                                onTextChanged: root.customCommentText = text
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.topMargin: 6
                        Item { Layout.fillWidth: true }

                        DialogButton {
                            buttonText: Translation.tr("Cancelar")
                            onClicked: root.showCustomDialog = false
                        }

                        RippleButtonWithIcon {
                            materialIcon: "check"
                            mainText: Translation.tr("Guardar y añadir")
                            buttonRadius: Appearance.rounding.small
                            colBackground: Appearance.colors.colPrimaryContainer
                            onClicked: {
                                root.addCustom(root.customNameText, root.customExecText, root.customIconText, root.customCommentText);
                            }
                        }
                    }
                }
            }
        }
    }

    // --- LIST OF AUTOSTART APPLICATIONS ---
    ContentSection {
        icon: "apps"
        title: Translation.tr("Aplicaciones configuradas (%1)").arg(root.autostartItems.length)

        // Empty State Banner
        Rectangle {
            visible: root.autostartItems.length === 0
            Layout.fillWidth: true
            implicitHeight: 160
            radius: Appearance.rounding.normal
            color: Appearance.colors.colLayer2
            border.width: 1
            border.color: Appearance.colors.colOutlineVariant

            ColumnLayout {
                anchors.centerIn: parent
                spacing: 10
                MaterialSymbol {
                    Layout.alignment: Qt.AlignHCenter
                    iconSize: 42
                    text: "playlist_add"
                    color: Appearance.colors.colOutline
                }
                StyledText {
                    Layout.alignment: Qt.AlignHCenter
                    text: Translation.tr("No hay aplicaciones en el inicio automático")
                    font.pixelSize: Appearance.font.pixelSize.normal
                    font.weight: Font.DemiBold
                    color: Appearance.colors.colOnSecondaryContainer
                }
                StyledText {
                    Layout.alignment: Qt.AlignHCenter
                    text: Translation.tr("Haz clic en '+ Añadir aplicación' para seleccionar programas como Discord, Spotify o Steam.")
                    font.pixelSize: Appearance.font.pixelSize.small
                    color: Appearance.colors.colOutline
                }
            }
        }

        // List of entries
        ColumnLayout {
            visible: root.autostartItems.length > 0
            Layout.fillWidth: true
            spacing: 8

            Repeater {
                model: root.autostartItems

                delegate: Rectangle {
                    id: entryCard
                    required property var modelData
                    Layout.fillWidth: true
                    implicitHeight: 68
                    radius: Appearance.rounding.normal
                    color: modelData.enabled ? Appearance.colors.colLayer2 : Appearance.colors.colLayer1
                    border.width: 1
                    border.color: modelData.enabled ? Appearance.colors.colOutlineVariant : Appearance.colors.colSurfaceContainerLowest

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 16
                        anchors.rightMargin: 16
                        spacing: 14

                        // App Icon
                        Kirigami.Icon {
                            implicitWidth: 38
                            implicitHeight: 38
                            source: modelData.icon || "application-x-executable"
                            opacity: modelData.enabled ? 1.0 : 0.4
                            roundToIconSize: false
                        }

                        // App Info Column
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 3

                            RowLayout {
                                spacing: 8
                                StyledText {
                                    text: modelData.name
                                    font.pixelSize: Appearance.font.pixelSize.normal
                                    font.weight: Font.DemiBold
                                    color: modelData.enabled ? Appearance.colors.colOnSecondaryContainer : Appearance.colors.colOutline
                                    opacity: modelData.enabled ? 1.0 : 0.6
                                    elide: Text.ElideRight
                                }

                                // Status badge
                                Rectangle {
                                    implicitWidth: statusText.implicitWidth + 12
                                    implicitHeight: 20
                                    radius: Appearance.rounding.full
                                    color: modelData.enabled ? Appearance.colors.colPrimaryContainer : Appearance.colors.colSurfaceContainerHigh

                                    StyledText {
                                        id: statusText
                                        anchors.centerIn: parent
                                        text: modelData.enabled ? Translation.tr("Activo") : Translation.tr("Desactivado")
                                        font.pixelSize: Appearance.font.pixelSize.smaller - 1
                                        font.weight: Font.Medium
                                        color: modelData.enabled ? Appearance.colors.colOnPrimaryContainer : Appearance.colors.colOutline
                                    }
                                }
                            }

                            StyledText {
                                text: modelData.exec || modelData.file
                                font.pixelSize: Appearance.font.pixelSize.smaller
                                font.family: Appearance.font.family.monospace
                                color: Appearance.colors.colOutline
                                elide: Text.ElideMiddle
                                opacity: modelData.enabled ? 0.9 : 0.4
                                Layout.fillWidth: true
                            }
                        }

                        // Toggle Switch
                        StyledSwitch {
                            checked: modelData.enabled
                            onClicked: {
                                root.toggleItem(modelData.file, !modelData.enabled);
                            }
                            StyledToolTip {
                                text: modelData.enabled ? Translation.tr("Desactivar del inicio") : Translation.tr("Activar en inicio")
                            }
                        }

                        // Test run button
                        RippleButton {
                            implicitWidth: 36
                            implicitHeight: 36
                            buttonRadius: Appearance.rounding.full
                            colBackground: Appearance.colors.colLayer3
                            onClicked: root.testRun(modelData.file, modelData.name)
                            contentItem: MaterialSymbol {
                                anchors.centerIn: parent
                                iconSize: 18
                                text: "play_arrow"
                                color: Appearance.colors.colOnSecondaryContainer
                            }
                            StyledToolTip {
                                text: Translation.tr("Probar ejecución ahora")
                            }
                        }

                        // Delete button
                        RippleButton {
                            implicitWidth: 36
                            implicitHeight: 36
                            buttonRadius: Appearance.rounding.full
                            colBackground: Appearance.colors.colLayer3
                            colBackgroundHover: Appearance.colors.colErrorContainer
                            colRipple: Appearance.colors.colError
                            onClicked: root.removeItem(modelData.file, modelData.name)
                            contentItem: MaterialSymbol {
                                anchors.centerIn: parent
                                iconSize: 18
                                text: "delete"
                                color: Appearance.colors.colOnSecondaryContainer
                            }
                            StyledToolTip {
                                text: Translation.tr("Eliminar de inicio automático")
                            }
                        }
                    }
                }
            }
        }
    }
}
