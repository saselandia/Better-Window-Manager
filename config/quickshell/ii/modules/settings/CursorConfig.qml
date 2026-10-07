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

    property var themes: []
    property string selectedTheme: "Bibata-Modern-Classic"
    property int selectedSize: 24
    property string feedbackMessage: ""
    property bool feedbackIsError: false

    readonly property string managerScript: FileUtils.trimFileProtocol(Directories.home) + "/.config/hypr/scripts/cursor-manager.py"
    readonly property var currentThemeData: {
        for (let i = 0; i < themes.length; i++) {
            if (themes[i].id === selectedTheme) return themes[i];
        }
        return themes.length > 0 ? themes[0] : null;
    }

    function refreshThemes() {
        listProcess.running = false;
        listProcess.running = true;
        getProcess.running = false;
        getProcess.running = true;
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

    function applyConfiguration() {
        if (!root.selectedTheme) return;
        applyProcess.command = ["python3", root.managerScript, "apply", root.selectedTheme, root.selectedSize.toString()];
        applyProcess.running = true;
    }

    // Process: List cursor themes
    Process {
        id: listProcess
        running: true
        command: ["python3", root.managerScript, "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                if (!text || !text.trim()) return;
                try {
                    root.themes = JSON.parse(text);
                } catch (e) {
                    console.error("[CursorConfig] Error parsing themes:", e);
                }
            }
        }
    }

    // Process: Get current cursor settings
    Process {
        id: getProcess
        running: true
        command: ["python3", root.managerScript, "get"]
        stdout: StdioCollector {
            onStreamFinished: {
                if (!text || !text.trim()) return;
                try {
                    const data = JSON.parse(text);
                    if (data.theme) root.selectedTheme = data.theme;
                    if (data.size) root.selectedSize = data.size;
                } catch (e) {
                    console.error("[CursorConfig] Error parsing current:", e);
                }
            }
        }
    }

    // Process: Apply cursor settings
    Process {
        id: applyProcess
        stdout: StdioCollector {
            onStreamFinished: {
                root.showFeedback(Translation.tr("Cursor applied successfully"), false);
                getProcess.running = true;
            }
        }
        stderr: StdioCollector {
            onStreamFinished: {
                if (text && text.trim()) {
                    root.showFeedback(Translation.tr("Error applying cursor: %1").arg(text.trim()), true);
                }
            }
        }
    }

    ContentSection {
        icon: "near_me"
        title: Translation.tr("Cursor Settings")

        // Feedback / Status Banner
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

        // Active Cursor Hero Card (Preview of active theme)
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 120
            radius: Appearance.rounding.windowRounding
            color: Appearance.colors.colLayer2
            border.width: 1
            border.color: Appearance.colors.colOutlineVariant

            RowLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 20

                // Main preview image
                Rectangle {
                    implicitWidth: 80
                    implicitHeight: 80
                    radius: Appearance.rounding.normal
                    color: Appearance.colors.colSurfaceContainerHigh
                    border.width: 1
                    border.color: Appearance.colors.colOutline

                    Image {
                        id: heroImg
                        anchors.centerIn: parent
                        width: Math.min(48, root.selectedSize * 1.5)
                        height: width
                        fillMode: Image.PreserveAspectFit
                        source: root.currentThemeData && root.currentThemeData.preview ? ("file://" + root.currentThemeData.preview) : ""
                        visible: status === Image.Ready
                    }

                    MaterialSymbol {
                        anchors.centerIn: parent
                        text: "near_me"
                        iconSize: 32
                        color: Appearance.colors.colPrimary
                        visible: heroImg.status !== Image.Ready
                    }
                }

                // Theme details & metadata
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4

                    StyledText {
                        text: root.currentThemeData ? root.currentThemeData.name : root.selectedTheme
                        font.pixelSize: Appearance.font.pixelSize.larger
                        font.weight: Font.Bold
                        color: Appearance.colors.colOnSurface
                    }

                    StyledText {
                        text: root.currentThemeData && root.currentThemeData.comment ? root.currentThemeData.comment : Translation.tr("Custom Cursor Theme")
                        font.pixelSize: Appearance.font.pixelSize.small
                        color: Appearance.colors.colOnSurfaceVariant
                    }

                    RowLayout {
                        spacing: 8
                        Layout.topMargin: 4

                        // Size badge
                        Rectangle {
                            implicitHeight: 24
                            implicitWidth: sizeLabel.implicitWidth + 14
                            radius: Appearance.rounding.full
                            color: Appearance.colors.colSecondaryContainer

                            StyledText {
                                id: sizeLabel
                                anchors.centerIn: parent
                                text: `${root.selectedSize} px`
                                font.pixelSize: Appearance.font.pixelSize.smaller
                                font.weight: Font.Medium
                                color: Appearance.colors.colOnSecondaryContainer
                            }
                        }

                        // Hyprcursor badge
                        Rectangle {
                            visible: root.currentThemeData ? root.currentThemeData.has_hyprcursor : true
                            implicitHeight: 24
                            implicitWidth: hyprLabel.implicitWidth + 14
                            radius: Appearance.rounding.full
                            color: Appearance.colors.colPrimaryContainer

                            StyledText {
                                id: hyprLabel
                                anchors.centerIn: parent
                                text: "Hyprcursor"
                                font.pixelSize: Appearance.font.pixelSize.smaller
                                font.weight: Font.Medium
                                color: Appearance.colors.colOnPrimaryContainer
                            }
                        }

                        // XCursor badge
                        Rectangle {
                            visible: root.currentThemeData ? root.currentThemeData.has_xcursor : true
                            implicitHeight: 24
                            implicitWidth: xcurLabel.implicitWidth + 14
                            radius: Appearance.rounding.full
                            color: Appearance.colors.colLayer3

                            StyledText {
                                id: xcurLabel
                                anchors.centerIn: parent
                                text: "XCursor"
                                font.pixelSize: Appearance.font.pixelSize.smaller
                                font.weight: Font.Medium
                                color: Appearance.colors.colOnLayer3
                            }
                        }
                    }
                }

                // Multi-state cursor preview row (pointer, hand, text, wait)
                RowLayout {
                    spacing: 12
                    visible: root.currentThemeData !== null

                    Repeater {
                        model: [
                            { name: Translation.tr("Pointer"), key: "preview" },
                            { name: Translation.tr("Hand"), key: "preview_hand" },
                            { name: Translation.tr("Text"), key: "preview_text" },
                            { name: Translation.tr("Wait"), key: "preview_wait" }
                        ]

                        ColumnLayout {
                            spacing: 4
                            required property var modelData

                            Rectangle {
                                implicitWidth: 42
                                implicitHeight: 42
                                radius: Appearance.rounding.small
                                color: Appearance.colors.colLayer3

                                Image {
                                    anchors.centerIn: parent
                                    width: 24
                                    height: 24
                                    fillMode: Image.PreserveAspectFit
                                    source: (root.currentThemeData && root.currentThemeData[modelData.key]) ? ("file://" + root.currentThemeData[modelData.key]) : ""
                                }
                            }

                            StyledText {
                                Layout.alignment: Qt.AlignHCenter
                                text: modelData.name
                                font.pixelSize: Appearance.font.pixelSize.smaller - 2
                                color: Appearance.colors.colSubtext
                            }
                        }
                    }
                }
            }
        }
    }

    // Cursor Theme Selection Section
    ContentSection {
        icon: "style"
        title: Translation.tr("Installed Cursor Themes")

        // Folder Location & Help Card
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: infoLayout.implicitHeight + 24
            radius: Appearance.rounding.normal
            color: Appearance.colors.colLayer3
            border.width: 1
            border.color: Appearance.colors.colOutlineVariant

            RowLayout {
                id: infoLayout
                anchors.fill: parent
                anchors.margins: 14
                spacing: 14

                MaterialSymbol {
                    text: "folder_special"
                    iconSize: 28
                    color: Appearance.colors.colPrimary
                    Layout.alignment: Qt.AlignVCenter
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    StyledText {
                        text: Translation.tr("Where to add new cursor themes")
                        font.weight: Font.Bold
                        font.pixelSize: Appearance.font.pixelSize.normal
                        color: Appearance.colors.colOnLayer3
                    }

                    StyledText {
                        Layout.fillWidth: true
                        text: Translation.tr("Place your extracted cursor folders into %1 (recommended) or %2.<br>Both Hyprcursor and standard XCursor formats are automatically detected.").arg("<b>~/.local/share/icons/</b>").arg("<b>~/.icons/</b>")
                        wrapMode: Text.Wrap
                        textFormat: Text.RichText
                        font.pixelSize: Appearance.font.pixelSize.smaller
                        color: Appearance.colors.colSubtext
                    }
                }

                RowLayout {
                    spacing: 8
                    Layout.alignment: Qt.AlignVCenter

                    RippleButtonWithIcon {
                        materialIcon: "folder_open"
                        mainText: Translation.tr("Open Folder")
                        colBackground: Appearance.colors.colSecondaryContainer
                        onClicked: {
                            const p = FileUtils.trimFileProtocol(Directories.home) + "/.local/share/icons";
                            Qt.openUrlExternally("file://" + p);
                        }
                    }

                    RippleButtonWithIcon {
                        id: copyBtn
                        property bool copied: false
                        materialIcon: copied ? "check" : "content_copy"
                        mainText: copied ? Translation.tr("Copied!") : Translation.tr("Copy Path")
                        colBackground: Appearance.colors.colLayer2
                        onClicked: {
                            const p = FileUtils.trimFileProtocol(Directories.home) + "/.local/share/icons";
                            Quickshell.clipboardText = p;
                            copyBtn.copied = true;
                            copyTimer.restart();
                            root.showFeedback(Translation.tr("Path copied to clipboard: %1").arg(p), false);
                        }

                        Timer {
                            id: copyTimer
                            interval: 2000
                            onTriggered: copyBtn.copied = false
                        }
                    }
                }
            }
        }

        ContentSubsection {
            title: Translation.tr("Select a cursor theme from your system")
            Layout.fillWidth: true

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 8

                Repeater {
                    model: root.themes

                    Rectangle {
                        id: themeCard
                        Layout.fillWidth: true
                        implicitHeight: 64
                        radius: Appearance.rounding.normal

                        required property int index
                        required property var modelData

                        readonly property bool isSelected: root.selectedTheme === modelData.id

                        color: isSelected ? Appearance.colors.colSecondaryContainer : (themeMouseArea.containsMouse ? Appearance.colors.colLayer2Hover : Appearance.colors.colLayer2)
                        border.width: isSelected ? 2 : 1
                        border.color: isSelected ? Appearance.colors.colPrimary : Appearance.colors.colOutlineVariant

                        Behavior on color { animation: Appearance.animation.elementMoveFast.colorAnimation.createObject(this) }

                        MouseArea {
                            id: themeMouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                root.selectedTheme = modelData.id;
                            }
                        }

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 16
                            anchors.rightMargin: 16
                            spacing: 14

                            // Cursor thumbnail
                            Rectangle {
                                implicitWidth: 44
                                implicitHeight: 44
                                radius: Appearance.rounding.small
                                color: Appearance.colors.colLayer1

                                Image {
                                    id: cardThumb
                                    anchors.centerIn: parent
                                    width: 28
                                    height: 28
                                    fillMode: Image.PreserveAspectFit
                                    source: modelData.preview ? ("file://" + modelData.preview) : ""
                                    visible: status === Image.Ready
                                }

                                MaterialSymbol {
                                    anchors.centerIn: parent
                                    text: "near_me"
                                    iconSize: 22
                                    color: Appearance.colors.colOnSurfaceVariant
                                    visible: cardThumb.status !== Image.Ready
                                }
                            }

                            // Theme Name & description
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2

                                RowLayout {
                                    spacing: 8
                                    StyledText {
                                        text: modelData.name
                                        font.weight: Font.Bold
                                        font.pixelSize: Appearance.font.pixelSize.normal
                                        color: isSelected ? Appearance.colors.colOnSecondaryContainer : Appearance.colors.colOnLayer2
                                    }

                                    // Format Tag
                                    Rectangle {
                                        implicitHeight: 20
                                        implicitWidth: tagText.implicitWidth + 10
                                        radius: Appearance.rounding.full
                                        color: modelData.has_hyprcursor ? Appearance.colors.colPrimaryContainer : Appearance.colors.colLayer3

                                        StyledText {
                                            id: tagText
                                            anchors.centerIn: parent
                                            text: modelData.has_hyprcursor ? "Hyprcursor" : "XCursor"
                                            font.pixelSize: Appearance.font.pixelSize.smaller - 2
                                            font.weight: Font.Medium
                                            color: modelData.has_hyprcursor ? Appearance.colors.colOnPrimaryContainer : Appearance.colors.colOnLayer3
                                        }
                                    }
                                }

                                StyledText {
                                    Layout.fillWidth: true
                                    text: modelData.comment ? modelData.comment : modelData.path
                                    elide: Text.ElideRight
                                    font.pixelSize: Appearance.font.pixelSize.smaller
                                    color: isSelected ? Appearance.colors.colOnSecondaryContainer : Appearance.colors.colSubtext
                                }
                            }

                            // Selection Indicator Radio / Check
                            MaterialSymbol {
                                text: isSelected ? "check_circle" : "radio_button_unchecked"
                                iconSize: 24
                                color: isSelected ? Appearance.colors.colPrimary : Appearance.colors.colOutline
                            }
                        }
                    }
                }
            }
        }
    }

    // Cursor Size Section
    ContentSection {
        icon: "format_size"
        title: Translation.tr("Cursor Size")

        ContentSubsection {
            title: Translation.tr("Pointer size in pixels")
            Layout.fillWidth: true

            StyledComboBox {
                id: sizeCombo
                Layout.fillWidth: true
                buttonIcon: "aspect_ratio"
                textRole: "name"
                model: [
                    { name: "20 px (" + Translation.tr("Small") + ")", value: 20 },
                    { name: "24 px (" + Translation.tr("Default") + ")", value: 24 },
                    { name: "28 px (" + Translation.tr("Medium") + ")", value: 28 },
                    { name: "32 px (" + Translation.tr("Large") + ")", value: 32 },
                    { name: "36 px (" + Translation.tr("Extra Large") + ")", value: 36 },
                    { name: "48 px (" + Translation.tr("HiDPI / Ultra") + ")", value: 48 }
                ]
                currentIndex: {
                    const idx = model.findIndex(item => item.value === root.selectedSize);
                    return idx >= 0 ? idx : 1;
                }
                onActivated: function(index) {
                    if (model && model[index]) {
                        root.selectedSize = model[index].value;
                    }
                }
            }
        }
    }

    // Interactive Test Playground (Hover zones to test cursor states live)
    ContentSection {
        icon: "ads_click"
        title: Translation.tr("Interactive Test Playground")

        ContentSubsection {
            title: Translation.tr("Hover over these interactive tiles to test the cursor behavior in real time")
            Layout.fillWidth: true

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                // Arrow Tile
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 80
                    radius: Appearance.rounding.normal
                    color: testArrowArea.containsMouse ? Appearance.colors.colLayer2Hover : Appearance.colors.colLayer2
                    border.width: 1
                    border.color: Appearance.colors.colOutlineVariant

                    MouseArea {
                        id: testArrowArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.ArrowCursor
                    }

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 4
                        MaterialSymbol {
                            Layout.alignment: Qt.AlignHCenter
                            text: "near_me"
                            iconSize: 24
                            color: Appearance.colors.colPrimary
                        }
                        StyledText {
                            Layout.alignment: Qt.AlignHCenter
                            text: Translation.tr("Default Arrow")
                            font.pixelSize: Appearance.font.pixelSize.small
                            color: Appearance.colors.colOnLayer2
                        }
                    }
                }

                // Pointer / Hand Tile
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 80
                    radius: Appearance.rounding.normal
                    color: testHandArea.containsMouse ? Appearance.colors.colLayer2Hover : Appearance.colors.colLayer2
                    border.width: 1
                    border.color: Appearance.colors.colOutlineVariant

                    MouseArea {
                        id: testHandArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                    }

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 4
                        MaterialSymbol {
                            Layout.alignment: Qt.AlignHCenter
                            text: "touch_app"
                            iconSize: 24
                            color: Appearance.colors.colPrimary
                        }
                        StyledText {
                            Layout.alignment: Qt.AlignHCenter
                            text: Translation.tr("Link / Click")
                            font.pixelSize: Appearance.font.pixelSize.small
                            color: Appearance.colors.colOnLayer2
                        }
                    }
                }

                // Text Select Tile
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 80
                    radius: Appearance.rounding.normal
                    color: testTextArea.containsMouse ? Appearance.colors.colLayer2Hover : Appearance.colors.colLayer2
                    border.width: 1
                    border.color: Appearance.colors.colOutlineVariant

                    MouseArea {
                        id: testTextArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.IBeamCursor
                    }

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 4
                        MaterialSymbol {
                            Layout.alignment: Qt.AlignHCenter
                            text: "text_fields"
                            iconSize: 24
                            color: Appearance.colors.colPrimary
                        }
                        StyledText {
                            Layout.alignment: Qt.AlignHCenter
                            text: Translation.tr("Text Selection")
                            font.pixelSize: Appearance.font.pixelSize.small
                            color: Appearance.colors.colOnLayer2
                        }
                    }
                }

                // Move Tile
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 80
                    radius: Appearance.rounding.normal
                    color: testMoveArea.containsMouse ? Appearance.colors.colLayer2Hover : Appearance.colors.colLayer2
                    border.width: 1
                    border.color: Appearance.colors.colOutlineVariant

                    MouseArea {
                        id: testMoveArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.SizeAllCursor
                    }

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 4
                        MaterialSymbol {
                            Layout.alignment: Qt.AlignHCenter
                            text: "open_with"
                            iconSize: 24
                            color: Appearance.colors.colPrimary
                        }
                        StyledText {
                            Layout.alignment: Qt.AlignHCenter
                            text: Translation.tr("Move / Drag")
                            font.pixelSize: Appearance.font.pixelSize.small
                            color: Appearance.colors.colOnLayer2
                        }
                    }
                }
            }
        }
    }

    // Action Buttons
    RowLayout {
        Layout.fillWidth: true
        Layout.topMargin: 10
        spacing: 12

        RippleButtonWithIcon {
            Layout.fillWidth: true
            materialIcon: "check"
            mainText: Translation.tr("Apply and Save Cursor")
            colBackground: Appearance.colors.colPrimaryContainer
            onClicked: root.applyConfiguration()
        }

        RippleButtonWithIcon {
            Layout.fillWidth: true
            materialIcon: "refresh"
            mainText: Translation.tr("Refresh Themes")
            colBackground: Appearance.colors.colLayer2
            onClicked: root.refreshThemes()
        }
    }
}
