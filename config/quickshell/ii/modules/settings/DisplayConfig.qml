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
    property int selectedIndex: 0
    property string feedbackMessage: ""
    property bool feedbackIsError: false

    readonly property string managerScript: FileUtils.trimFileProtocol(Directories.home) + "/.config/hypr/scripts/monitor-manager.py"
    readonly property var currentMonitor: (monitors && monitors.length > selectedIndex) ? monitors[selectedIndex] : null

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

    function alignSelected(direction, refMonitorName) {
        if (!currentMonitor) return;
        const ref = monitors.find(m => m.name === refMonitorName);
        if (!ref) return;

        let updated = JSON.parse(JSON.stringify(monitors));
        let target = updated[selectedIndex];
        let refTarget = updated.find(m => m.name === refMonitorName);

        if (direction === "left") {
            target.x = Math.max(0, refTarget.x - target.width);
            target.y = refTarget.y;
        } else if (direction === "right") {
            target.x = refTarget.x + refTarget.width;
            target.y = refTarget.y;
        } else if (direction === "top") {
            target.x = refTarget.x;
            target.y = Math.max(0, refTarget.y - target.height);
        } else if (direction === "bottom") {
            target.x = refTarget.x;
            target.y = refTarget.y + refTarget.height;
        }

        root.monitors = updated;
        showFeedback(Translation.tr("Position of %1 updated in preview").arg(target.name), false);
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
                    if (root.selectedIndex >= root.monitors.length) {
                        root.selectedIndex = 0;
                    }
                } catch (e) {
                    console.error("[DisplayConfig] Error parsing monitors:", e);
                }
            }
        }
    }

    // Process: Apply configuration
    Process {
        id: applyProcess
        stdout: StdioCollector {
            onStreamFinished: {
                root.showFeedback(Translation.tr("Displays configured and applied successfully"), false);
                root.refreshMonitors();
            }
        }
        stderr: StdioCollector {
            onStreamFinished: {
                if (text && text.trim()) {
                    root.showFeedback(Translation.tr("Error applying displays: %1").arg(text.trim()), true);
                }
            }
        }
    }

    ContentSection {
        icon: "desktop_windows"
        title: Translation.tr("Display Layout")

        // Feedback / status alert
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

        // Graphical preview canvas
        Rectangle {
            id: canvasContainer
            Layout.fillWidth: true
            implicitHeight: 220
            radius: Appearance.rounding.windowRounding
            color: Appearance.colors.colLayer2
            border.width: 1
            border.color: Appearance.colors.colOutlineVariant
            clip: true

            StyledText {
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.margins: 12
                text: Translation.tr("Click on a display to select and configure it")
                font.pixelSize: Appearance.font.pixelSize.small
                color: Appearance.colors.colOnSurfaceVariant
            }

            Item {
                id: monitorViewport
                anchors.centerIn: parent
                width: parent.width - 40
                height: parent.height - 50

                property real totalWidth: {
                    let maxRight = 1920;
                    for (let m of root.monitors) {
                        maxRight = Math.max(maxRight, m.x + m.width);
                    }
                    return maxRight;
                }
                property real totalHeight: {
                    let maxBottom = 1080;
                    for (let m of root.monitors) {
                        maxBottom = Math.max(maxBottom, m.y + m.height);
                    }
                    return maxBottom;
                }
                property real scaleFactor: Math.min(width / Math.max(1, totalWidth), height / Math.max(1, totalHeight)) * 0.85

                Repeater {
                    model: root.monitors

                    Rectangle {
                        id: monitorRect
                        required property int index
                        required property var modelData

                        readonly property bool isSelected: root.selectedIndex === index
                        readonly property bool isDisabled: modelData.disabled ?? false

                        x: (modelData.x * monitorViewport.scaleFactor)
                        y: (modelData.y * monitorViewport.scaleFactor)
                        width: Math.max(80, modelData.width * monitorViewport.scaleFactor)
                        height: Math.max(50, modelData.height * monitorViewport.scaleFactor)

                        radius: Appearance.rounding.small
                        color: isDisabled ? Appearance.colors.colLayer1 : (isSelected ? Appearance.colors.colPrimaryContainer : Appearance.colors.colSurfaceContainerHigh)
                        border.width: isSelected ? 2 : 1
                        border.color: isSelected ? Appearance.colors.colPrimary : Appearance.colors.colOutline

                        Behavior on x { NumberAnimation { duration: 200 } }
                        Behavior on y { NumberAnimation { duration: 200 } }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                root.selectedIndex = index;
                            }
                        }

                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 2
                            MaterialSymbol {
                                Layout.alignment: Qt.AlignHCenter
                                text: "desktop_windows"
                                iconSize: 20
                                color: isSelected ? Appearance.colors.colOnPrimaryContainer : Appearance.colors.colOnSurface
                            }
                            StyledText {
                                Layout.alignment: Qt.AlignHCenter
                                text: modelData.name
                                font.weight: Font.Bold
                                font.pixelSize: Appearance.font.pixelSize.small
                                color: isSelected ? Appearance.colors.colOnPrimaryContainer : Appearance.colors.colOnSurface
                            }
                            StyledText {
                                Layout.alignment: Qt.AlignHCenter
                                text: `${modelData.width}x${modelData.height} @ ${modelData.refreshRate}Hz`
                                font.pixelSize: Appearance.font.pixelSize.smaller
                                color: isSelected ? Appearance.colors.colOnPrimaryContainer : Appearance.colors.colOnSurfaceVariant
                            }
                        }
                    }
                }
            }
        }

        // Relative Alignment Buttons (Multi-monitor)
        ContentSubsection {
            visible: root.monitors.length > 1 && root.currentMonitor !== null
            title: Translation.tr("Align with other displays")
            Layout.fillWidth: true

            Repeater {
                model: root.monitors.map(m => m.name).filter(n => n !== (root.currentMonitor ? root.currentMonitor.name : ""))

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    required property string modelData

                    RippleButtonWithIcon {
                        materialIcon: "arrow_back"
                        mainText: Translation.tr("To the left of %1").arg(modelData)
                        colBackground: Appearance.colors.colLayer3
                        onClicked: root.alignSelected("left", modelData)
                    }

                    RippleButtonWithIcon {
                        materialIcon: "arrow_forward"
                        mainText: Translation.tr("To the right of %1").arg(modelData)
                        colBackground: Appearance.colors.colLayer3
                        onClicked: root.alignSelected("right", modelData)
                    }

                    RippleButtonWithIcon {
                        materialIcon: "arrow_upward"
                        mainText: Translation.tr("Above %1").arg(modelData)
                        colBackground: Appearance.colors.colLayer3
                        onClicked: root.alignSelected("top", modelData)
                    }

                    RippleButtonWithIcon {
                        materialIcon: "arrow_downward"
                        mainText: Translation.tr("Below %1").arg(modelData)
                        colBackground: Appearance.colors.colLayer3
                        onClicked: root.alignSelected("bottom", modelData)
                    }
                }
            }
        }
    }

    ContentSection {
        visible: root.currentMonitor !== null
        icon: "tune"
        title: Translation.tr("Settings for: %1 (%2)").arg(root.currentMonitor ? root.currentMonitor.name : "").arg(root.currentMonitor ? root.currentMonitor.model : "")

        // Resolution selector
        ContentSubsection {
            title: Translation.tr("Display Resolution")
            Layout.fillWidth: true

            StyledComboBox {
                id: resCombo
                Layout.fillWidth: true
                buttonIcon: "aspect_ratio"
                textRole: "name"
                model: {
                    if (!root.currentMonitor || !root.currentMonitor.resolutions) return [];
                    return root.currentMonitor.resolutions.map(r => ({ name: r, value: r }));
                }
                currentIndex: {
                    if (!root.currentMonitor || !root.currentMonitor.resolutions) return 0;
                    const cur = `${root.currentMonitor.width}x${root.currentMonitor.height}`;
                    const idx = root.currentMonitor.resolutions.indexOf(cur);
                    return idx >= 0 ? idx : 0;
                }
                onActivated: function(index) {
                    if (!model || !model[index]) return;
                    const selRes = model[index].value;
                    if (selRes && selRes.includes("x")) {
                        const parts = selRes.split("x");
                        let updated = JSON.parse(JSON.stringify(root.monitors));
                        updated[root.selectedIndex].width = parseInt(parts[0]);
                        updated[root.selectedIndex].height = parseInt(parts[1]);
                        
                        const availableHz = updated[root.selectedIndex].modesMap[selRes] || [60.0];
                        if (!availableHz.includes(updated[root.selectedIndex].refreshRate)) {
                            updated[root.selectedIndex].refreshRate = availableHz[0];
                        }
                        root.monitors = updated;
                    }
                }
            }
        }

        // Refresh Rate (Hz)
        ContentSubsection {
            title: Translation.tr("Refresh Rate (Hz)")
            Layout.fillWidth: true

            StyledComboBox {
                id: hzCombo
                Layout.fillWidth: true
                buttonIcon: "speed"
                textRole: "name"
                model: {
                    if (!root.currentMonitor || !root.currentMonitor.modesMap) return [];
                    const curRes = `${root.currentMonitor.width}x${root.currentMonitor.height}`;
                    const hzList = root.currentMonitor.modesMap[curRes] || [60.0];
                    return hzList.map(h => ({ name: `${h} Hz`, value: h }));
                }
                currentIndex: {
                    if (!root.currentMonitor || !root.currentMonitor.modesMap) return 0;
                    const curRes = `${root.currentMonitor.width}x${root.currentMonitor.height}`;
                    const hzList = root.currentMonitor.modesMap[curRes] || [60.0];
                    const idx = hzList.indexOf(root.currentMonitor.refreshRate);
                    return idx >= 0 ? idx : 0;
                }
                onActivated: function(index) {
                    if (!model || !model[index]) return;
                    const val = model[index].value;
                    if (val !== undefined) {
                        let updated = JSON.parse(JSON.stringify(root.monitors));
                        updated[root.selectedIndex].refreshRate = val;
                        root.monitors = updated;
                    }
                }
            }
        }

        // Interface Scale
        ContentSubsection {
            title: Translation.tr("Interface Scale")
            Layout.fillWidth: true

            StyledComboBox {
                id: scaleCombo
                Layout.fillWidth: true
                buttonIcon: "zoom_in"
                textRole: "name"
                model: [
                    { name: "1.0 (100%)", value: 1.0 },
                    { name: "1.25 (125%)", value: 1.25 },
                    { name: "1.5 (150%)", value: 1.5 },
                    { name: "1.75 (175%)", value: 1.75 },
                    { name: "2.0 (200%)", value: 2.0 }
                ]
                currentIndex: {
                    if (!root.currentMonitor) return 0;
                    const sc = root.currentMonitor.scale;
                    const scales = [1.0, 1.25, 1.5, 1.75, 2.0];
                    const idx = scales.indexOf(sc);
                    return idx >= 0 ? idx : 0;
                }
                onActivated: function(index) {
                    if (!model || !model[index]) return;
                    let updated = JSON.parse(JSON.stringify(root.monitors));
                    updated[root.selectedIndex].scale = model[index].value;
                    root.monitors = updated;
                }
            }
        }

        // Manual X and Y position
        ConfigRow {
            Layout.fillWidth: true

            ConfigSpinBox {
                icon: "open_with"
                text: Translation.tr("Position X")
                value: root.currentMonitor ? root.currentMonitor.x : 0
                from: 0
                to: 15000
                stepSize: 100
                onValueChanged: {
                    if (root.currentMonitor && root.currentMonitor.x !== value) {
                        let updated = JSON.parse(JSON.stringify(root.monitors));
                        updated[root.selectedIndex].x = value;
                        root.monitors = updated;
                    }
                }
            }

            ConfigSpinBox {
                icon: "open_with"
                text: Translation.tr("Position Y")
                value: root.currentMonitor ? root.currentMonitor.y : 0
                from: 0
                to: 15000
                stepSize: 100
                onValueChanged: {
                    if (root.currentMonitor && root.currentMonitor.y !== value) {
                        let updated = JSON.parse(JSON.stringify(root.monitors));
                        updated[root.selectedIndex].y = value;
                        root.monitors = updated;
                    }
                }
            }
        }

        // Enable / Disable monitor switch
        ConfigSwitch {
            buttonIcon: "power_settings_new"
            text: Translation.tr("Display enabled")
            checked: root.currentMonitor ? !(root.currentMonitor.disabled ?? false) : true
            onCheckedChanged: {
                if (root.currentMonitor) {
                    let updated = JSON.parse(JSON.stringify(root.monitors));
                    updated[root.selectedIndex].disabled = !checked;
                    root.monitors = updated;
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
            mainText: Translation.tr("Apply and Save Changes")
            colBackground: Appearance.colors.colPrimaryContainer
            onClicked: root.applyConfiguration()
        }

        RippleButtonWithIcon {
            Layout.fillWidth: true
            materialIcon: "refresh"
            mainText: Translation.tr("Detect Displays")
            colBackground: Appearance.colors.colLayer2
            onClicked: root.refreshMonitors()
        }
    }
}
