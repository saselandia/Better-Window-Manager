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

    // Drag & Drop Commit with Magnetic Snapping
    function commitMonitorDrag(index, canvasX, canvasY, rectW, rectH) {
        if (!monitors || index >= monitors.length) return;
        let updated = JSON.parse(JSON.stringify(monitors));
        let target = updated[index];
        if (target.disabled) return;

        // Convert canvas drop position to normalized layout coordinates
        let dropNormX = canvasX - monitorViewport.offsetX;
        let dropNormY = canvasY - monitorViewport.offsetY;
        let targetNormW = target.width * monitorViewport.scaleFactor;
        let targetNormH = target.height * monitorViewport.scaleFactor;

        const snapDist = 20; // Canvas pixels threshold
        let bestSnapX = null;
        let minDeltaX = snapDist;
        let bestSnapY = null;
        let minDeltaY = snapDist;

        for (let j = 0; j < updated.length; j++) {
            if (j === index || updated[j].disabled) continue;
            let other = updated[j];
            let otherNormX = other.x * monitorViewport.scaleFactor;
            let otherNormY = other.y * monitorViewport.scaleFactor;
            let otherNormW = other.width * monitorViewport.scaleFactor;
            let otherNormH = other.height * monitorViewport.scaleFactor;

            // Snap X candidates:
            // 1. Target Left to Other Right
            let d = Math.abs(dropNormX - (otherNormX + otherNormW));
            if (d < minDeltaX) {
                minDeltaX = d;
                bestSnapX = other.x + other.width;
            }
            // 2. Target Right to Other Left
            d = Math.abs((dropNormX + targetNormW) - otherNormX);
            if (d < minDeltaX) {
                minDeltaX = d;
                bestSnapX = other.x - target.width;
            }
            // 3. Target Left to Other Left
            d = Math.abs(dropNormX - otherNormX);
            if (d < minDeltaX) {
                minDeltaX = d;
                bestSnapX = other.x;
            }
            // 4. Target Right to Other Right
            d = Math.abs((dropNormX + targetNormW) - (otherNormX + otherNormW));
            if (d < minDeltaX) {
                minDeltaX = d;
                bestSnapX = other.x + other.width - target.width;
            }

            // Snap Y candidates:
            // 1. Target Top to Other Bottom
            d = Math.abs(dropNormY - (otherNormY + otherNormH));
            if (d < minDeltaY) {
                minDeltaY = d;
                bestSnapY = other.y + other.height;
            }
            // 2. Target Bottom to Other Top
            d = Math.abs((dropNormY + targetNormH) - otherNormY);
            if (d < minDeltaY) {
                minDeltaY = d;
                bestSnapY = other.y - target.height;
            }
            // 3. Target Top to Other Top
            d = Math.abs(dropNormY - otherNormY);
            if (d < minDeltaY) {
                minDeltaY = d;
                bestSnapY = other.y;
            }
            // 4. Target Bottom to Other Bottom
            d = Math.abs((dropNormY + targetNormH) - (otherNormY + otherNormH));
            if (d < minDeltaY) {
                minDeltaY = d;
                bestSnapY = other.y + other.height - target.height;
            }
        }

        let finalRealX = (bestSnapX !== null) ? bestSnapX : Math.round(dropNormX / monitorViewport.scaleFactor / 10) * 10;
        let finalRealY = (bestSnapY !== null) ? bestSnapY : Math.round(dropNormY / monitorViewport.scaleFactor / 10) * 10;

        target.x = finalRealX;
        target.y = finalRealY;

        // Normalization: find minX and minY among enabled monitors
        let minX = Infinity;
        let minY = Infinity;
        for (let m of updated) {
            if (!m.disabled) {
                if (m.x < minX) minX = m.x;
                if (m.y < minY) minY = m.y;
            }
        }
        if (minX !== Infinity && minY !== Infinity && (minX !== 0 || minY !== 0)) {
            for (let m of updated) {
                if (!m.disabled) {
                    m.x = Math.max(0, m.x - minX);
                    m.y = Math.max(0, m.y - minY);
                }
            }
        }

        root.monitors = updated;
        showFeedback(Translation.tr("Position of %1 updated in preview").arg(target.name), false);
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
            implicitHeight: 280
            radius: Appearance.rounding.windowRounding
            color: Appearance.colors.colLayer2
            border.width: 1
            border.color: Appearance.colors.colOutlineVariant
            clip: true

            StyledText {
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.margins: 12
                text: Translation.tr("Drag displays to arrange their positions, or click to configure")
                font.pixelSize: Appearance.font.pixelSize.small
                color: Appearance.colors.colOnSurfaceVariant
            }

            Item {
                id: monitorViewport
                anchors.fill: parent
                anchors.margins: 25

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
                property real scaleFactor: Math.min(width / Math.max(1, totalWidth), height / Math.max(1, totalHeight)) * 0.82
                property real offsetX: Math.max(0, (width - (totalWidth * scaleFactor)) / 2)
                property real offsetY: Math.max(0, (height - (totalHeight * scaleFactor)) / 2)

                Repeater {
                    model: root.monitors

                    Rectangle {
                        id: monitorRect
                        required property int index
                        required property var modelData

                        readonly property bool isSelected: root.selectedIndex === index
                        readonly property bool isDisabled: modelData.disabled ?? false
                        readonly property bool isDragging: dragArea.drag.active

                        z: isDragging ? 30 : (isSelected ? 10 : 1)
                        scale: isDragging ? 1.04 : 1.0
                        opacity: isDisabled ? 0.45 : (isDragging ? 0.92 : 1.0)

                        Behavior on scale { NumberAnimation { duration: 150 } }
                        Behavior on opacity { NumberAnimation { duration: 150 } }

                        x: monitorViewport.offsetX + (modelData.x * monitorViewport.scaleFactor)
                        y: monitorViewport.offsetY + (modelData.y * monitorViewport.scaleFactor)

                        Binding {
                            target: monitorRect
                            property: "x"
                            value: monitorViewport.offsetX + (modelData.x * monitorViewport.scaleFactor)
                            when: !monitorRect.isDragging
                        }

                        Binding {
                            target: monitorRect
                            property: "y"
                            value: monitorViewport.offsetY + (modelData.y * monitorViewport.scaleFactor)
                            when: !monitorRect.isDragging
                        }

                        Behavior on x {
                            enabled: !monitorRect.isDragging
                            NumberAnimation { duration: 200; easing.type: Easing.OutCubic }
                        }
                        Behavior on y {
                            enabled: !monitorRect.isDragging
                            NumberAnimation { duration: 200; easing.type: Easing.OutCubic }
                        }

                        width: Math.max(80, modelData.width * monitorViewport.scaleFactor)
                        height: Math.max(50, modelData.height * monitorViewport.scaleFactor)

                        radius: Appearance.rounding.small
                        color: isDisabled ? Appearance.colors.colLayer1 : (isSelected ? Appearance.colors.colPrimaryContainer : Appearance.colors.colSurfaceContainerHigh)
                        border.width: isSelected || isDragging ? 2 : 1
                        border.color: isSelected || isDragging ? Appearance.colors.colPrimary : Appearance.colors.colOutline

                        MouseArea {
                            id: dragArea
                            anchors.fill: parent
                            cursorShape: drag.active ? Qt.ClosedHandCursor : Qt.OpenHandCursor
                            drag.target: monitorRect
                            drag.axis: Drag.XAndYAxis
                            drag.minimumX: -50
                            drag.maximumX: canvasContainer.width - monitorRect.width + 50
                            drag.minimumY: -50
                            drag.maximumY: canvasContainer.height - monitorRect.height + 50

                            onPressed: {
                                root.selectedIndex = index;
                            }

                            onReleased: {
                                root.commitMonitorDrag(index, monitorRect.x, monitorRect.y, monitorRect.width, monitorRect.height);
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
                            StyledText {
                                Layout.alignment: Qt.AlignHCenter
                                text: monitorRect.isDragging ? `(${Math.max(0, Math.round((monitorRect.x - monitorViewport.offsetX) / monitorViewport.scaleFactor))}, ${Math.max(0, Math.round((monitorRect.y - monitorViewport.offsetY) / monitorViewport.scaleFactor))})` : `(${modelData.x}, ${modelData.y})`
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
