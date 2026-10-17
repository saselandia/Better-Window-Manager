import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import Quickshell.Bluetooth
import Quickshell.Services.UPower
import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.common.models

Item {
    id: root

    property var screen: root.QsWindow.window?.screen
    readonly property HyprlandMonitor monitor: Hyprland.monitorFor(screen)
    readonly property int activeWsId: monitor?.activeWorkspace?.id ?? 1

    // -----------------------------------------------------------------
    // Dynamic Dimensions & Proportional Scaling based on Bar Height
    // -----------------------------------------------------------------
    readonly property real barH: Math.max(16, root.height)
    readonly property real vMargin: barH <= 24 ? 1 : Math.min(4, Math.round((barH - 24) * 0.12) + 1)
    readonly property real itemHeight: Math.max(14, barH - (vMargin * 2))
    readonly property real iconBoxWidth: Math.round(itemHeight * 1.1)
    readonly property real sepHeight: Math.max(8, Math.round(itemHeight * 0.55))

    // Scale ratio relative to base 24px bar
    readonly property real scaleRatio: Math.max(0.75, Math.min(2.5, barH / 24.0))

    // Dynamic typography scaling proportionally
    readonly property int fontSizeTiny: Math.max(9, Math.round(10 * Math.pow(scaleRatio, 0.65)))
    readonly property int fontSizeSmall: Math.max(10, Math.round(11 * Math.pow(scaleRatio, 0.65)))
    readonly property int fontSizeRegular: Math.max(11, Math.round(12 * Math.pow(scaleRatio, 0.65)))
    readonly property int fontSizeMedium: Math.max(12, Math.round(13 * Math.pow(scaleRatio, 0.65)))
    readonly property int fontSizeLarge: Math.max(13, Math.round(14 * Math.pow(scaleRatio, 0.65)))

    // -----------------------------------------------------------------
    // Dynamic Omarchy Palette derived from the active wallpaper:
    // Reads directly from retro-colors.json (computed via bwm-theme-manager.py)
    // with automatic reactive fallback to boosted Appearance.m3colors.
    // -----------------------------------------------------------------
    property var retroPalette: null

    function updateRetroPalette() {
        try {
            let t = retroColorsFileView.text();
            console.log("[RetroBar] updateRetroPalette called! text len:", t ? t.length : 0);
            if (t && t.length > 5) {
                root.retroPalette = JSON.parse(t);
                console.log("[RetroBar] Successfully loaded palette accent:", root.retroPalette.accent);
            }
        } catch (e) {
            console.log("[RetroBar] Error parsing retroPalette:", e);
            root.retroPalette = null;
        }
    }

    Timer {
        id: delayedFileRead
        interval: 60
        repeat: false
        running: false
        onTriggered: {
            root.updateRetroPalette();
        }
    }

    FileView {
        id: retroColorsFileView
        path: Qt.resolvedUrl(Directories.generatedRetroThemePath)
        watchChanges: true
        onFileChanged: {
            this.reload();
            delayedFileRead.start();
        }
        onLoadedChanged: {
            delayedFileRead.start();
        }
    }

    IpcHandler {
        target: "retro"

        function reload(): void {
            retroColorsFileView.reload();
            delayedFileRead.start();
        }
    }

    Connections {
        target: Appearance.m3colors
        function onM3primaryChanged() {
            retroColorsFileView.reload();
            delayedFileRead.start();
        }
    }

    Component.onCompleted: {
        delayedFileRead.start();
    }

    readonly property color dynamicAccent: {
        if (root.retroPalette && root.retroPalette.accent) {
            return root.retroPalette.accent;
        }
        let base = Appearance.m3colors.m3primary;
        return Qt.hsva(base.hsvHue, Math.min(1.0, Math.max(0.78, base.hsvSaturation * 1.6)), 0.96, 1.0);
    }

    readonly property color dynamicSecondary: {
        if (root.retroPalette && root.retroPalette.secondary) {
            return root.retroPalette.secondary;
        }
        let base = Appearance.m3colors.m3secondary;
        return Qt.hsva((base.hsvHue + 0.12) % 1.0, Math.min(1.0, Math.max(0.72, base.hsvSaturation * 1.5)), 0.92, 1.0);
    }

    readonly property color dynamicBg: {
        if (root.retroPalette && root.retroPalette.bg) {
            return root.retroPalette.bg;
        }
        let base = Appearance.m3colors.m3primary;
        return Qt.hsva(base.hsvHue, 0.28, 0.07, 0.95);
    }

    readonly property color dynamicBorder: {
        if (root.retroPalette && root.retroPalette.border) {
            return root.retroPalette.border;
        }
        let base = Appearance.m3colors.m3primary;
        return Qt.hsva(base.hsvHue, 0.35, 0.22, 0.85);
    }

    readonly property color dynamicHoverBg: {
        let base = dynamicAccent;
        return Qt.rgba(base.r, base.g, base.b, 0.14);
    }

    readonly property color dynamicFg: "#f8fafc"
    readonly property color dynamicDim: "#475569"
    readonly property color dynamicMuted: "#94a3b8"

    readonly property var omarchyColors: {
        return {
            bg: root.dynamicBg,
            fg: root.dynamicFg,
            accent: root.dynamicAccent,
            secondary: root.dynamicSecondary,
            muted: root.dynamicMuted,
            dim: root.dynamicDim,
            border: root.dynamicBorder,
            hoverBg: root.dynamicHoverBg
        };
    }

    // Helper to format workspace labels using user config (normal, Roman, Han chars)
    function getWsLabel(id) {
        let map = Config.options?.bar?.workspaces?.numberMap;
        if (map && map.length >= id && map[id - 1]) {
            return map[id - 1];
        }
        return String(id);
    }

    // -----------------------------------------------------------------
    // Bar Background & Hairline Border (respects bar.bottom & showBackground)
    // -----------------------------------------------------------------
    Rectangle {
        id: barBg
        anchors.fill: parent
        color: root.dynamicBg
        visible: Config.options?.bar?.showBackground ?? true

        Rectangle {
            id: hairline
            anchors.left: parent.left
            anchors.right: parent.right
            height: 1
            y: (Config.options?.bar?.bottom ?? false) ? 0 : (parent.height - 1)
            color: root.dynamicBorder
            z: 1
        }
    }

    // -----------------------------------------------------------------
    // Left Section: Omarchy Logo / Menu Launcher + Workspaces
    // -----------------------------------------------------------------
    RowLayout {
        id: leftSection
        anchors {
            left: parent.left
            leftMargin: 8
            top: parent.top
            bottom: parent.bottom
        }
        spacing: Math.max(4, Math.round(6 * root.scaleRatio))

        MouseArea {
            id: wsArea
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: wsRow.implicitWidth + 4
            implicitHeight: root.itemHeight

            onWheel: event => {
                let count = Math.max(1, Config.options?.bar?.workspaces?.shown ?? 10);
                if (event.angleDelta.y > 0) {
                    let nextId = Math.max(1, root.activeWsId - 1);
                    Hyprland.dispatch(`hl.dsp.focus({workspace = ${nextId}})`);
                } else if (event.angleDelta.y < 0) {
                    let nextId = Math.min(count, root.activeWsId + 1);
                    Hyprland.dispatch(`hl.dsp.focus({workspace = ${nextId}})`);
                }
            }

            Row {
                id: wsRow
                anchors.centerIn: parent
                spacing: Math.max(2, Math.round(3 * root.scaleRatio))

                Repeater {
                    model: Math.max(1, Config.options?.bar?.workspaces?.shown ?? 10)
                    delegate: Item {
                        id: wsItem
                        property int wsId: index + 1
                        property bool isActive: root.activeWsId === wsId
                        property bool isOccupied: Hyprland.workspaces.values.some(ws => ws.id === wsId)

                        implicitWidth: wsLabel.implicitWidth + (isActive ? Math.round(12 * root.scaleRatio) : Math.round(8 * root.scaleRatio))
                        implicitHeight: root.itemHeight

                        Rectangle {
                            id: wsPill
                            anchors.fill: parent
                            radius: Math.round(3 * root.scaleRatio)
                            color: wsItem.isActive 
                                ? Qt.rgba(root.dynamicAccent.r, root.dynamicAccent.g, root.dynamicAccent.b, 0.15)
                                : (wsBtnMouse.containsMouse ? root.dynamicHoverBg : "transparent")
                            border.width: wsItem.isActive ? 1 : 0
                            border.color: Qt.rgba(root.dynamicAccent.r, root.dynamicAccent.g, root.dynamicAccent.b, 0.5)

                            Behavior on color { ColorAnimation { duration: 120 } }
                        }

                        Text {
                            id: wsLabel
                            anchors.centerIn: parent
                            text: wsItem.isActive ? `[ ${root.getWsLabel(wsItem.wsId)} ]` : `${root.getWsLabel(wsItem.wsId)}`
                            font.family: "JetBrains Mono NF"
                            font.pixelSize: root.fontSizeSmall
                            font.weight: wsItem.isActive ? Font.Bold : (wsItem.isOccupied ? Font.Medium : Font.Normal)
                            color: wsItem.isActive 
                                ? root.dynamicAccent 
                                : (wsBtnMouse.containsMouse 
                                    ? root.dynamicAccent 
                                    : (wsItem.isOccupied ? root.dynamicFg : root.dynamicDim))

                            Behavior on color { ColorAnimation { duration: 100 } }
                        }

                        MouseArea {
                            id: wsBtnMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                Hyprland.dispatch(`hl.dsp.focus({workspace = ${wsItem.wsId}})`);
                            }
                        }
                    }
                }
            }
        }
    }

    // -----------------------------------------------------------------
    // Center Section: Monospace Date & Time (Omarchy Clean Format)
    // -----------------------------------------------------------------
    MouseArea {
        id: centerClockArea
        anchors.centerIn: parent
        implicitWidth: centerClockText.implicitWidth + Math.round(16 * root.scaleRatio)
        implicitHeight: root.itemHeight
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor

        onClicked: {
            GlobalStates.sidebarRightOpen = !GlobalStates.sidebarRightOpen;
        }

        Rectangle {
            anchors.fill: parent
            radius: Math.round(4 * root.scaleRatio)
            color: centerClockArea.containsMouse ? root.dynamicHoverBg : "transparent"
            Behavior on color { ColorAnimation { duration: 120 } }
        }

        Text {
            id: centerClockText
            anchors.centerIn: parent
            text: Qt.formatDateTime(DateTime.clock.date, "ddd d MMM  HH:mm")
            font.family: "JetBrains Mono NF"
            font.pixelSize: root.fontSizeSmall
            font.weight: Font.DemiBold
            color: centerClockArea.containsMouse ? root.dynamicAccent : root.dynamicFg

            Behavior on color { ColorAnimation { duration: 120 } }
        }
    }

    // -----------------------------------------------------------------
    // Right Section: Telemetry, Utility, Weather, Audio, Network, Bluetooth, Battery, Theme
    // -----------------------------------------------------------------
    RowLayout {
        id: rightStatusRow
        anchors {
            right: parent.right
            rightMargin: 10
            top: parent.top
            bottom: parent.bottom
        }
        spacing: Math.max(4, Math.round(6 * root.scaleRatio))

        // Optional Weather Indicator (controlled by Config.options.bar.weather.enable)
        Item {
            visible: Config.options?.bar?.weather?.enable ?? false
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: weatherRow.implicitWidth + Math.round(8 * root.scaleRatio)
            implicitHeight: root.itemHeight

            MouseArea {
                id: weatherArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                acceptedButtons: Qt.LeftButton | Qt.RightButton

                Rectangle {
                    anchors.fill: parent
                    radius: Math.round(4 * root.scaleRatio)
                    color: weatherArea.containsMouse ? root.dynamicHoverBg : "transparent"
                    Behavior on color { ColorAnimation { duration: 120 } }
                }

                Row {
                    id: weatherRow
                    anchors.centerIn: parent
                    spacing: Math.max(2, Math.round(4 * root.scaleRatio))

                    Text {
                        text: (Weather.data?.temp !== undefined) ? `${Weather.data.temp}` : "󰖐"
                        font.family: "JetBrains Mono NF"
                        font.pixelSize: root.fontSizeSmall
                        color: weatherArea.containsMouse ? root.dynamicAccent : root.dynamicFg
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                onClicked: event => {
                    if (event.button === Qt.RightButton) {
                        Weather.getData();
                    } else {
                        GlobalStates.sidebarRightOpen = !GlobalStates.sidebarRightOpen;
                    }
                }
            }
        }

        // Utility Buttons (Controlled via Config.options.bar.utilButtons)
        Item {
            visible: Config.options?.bar?.utilButtons?.showScreenSnip ?? false
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: root.iconBoxWidth
            implicitHeight: root.itemHeight
            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                Rectangle {
                    anchors.fill: parent
                    radius: Math.round(4 * root.scaleRatio)
                    color: parent.containsMouse ? root.dynamicHoverBg : "transparent"
                }
                Text {
                    anchors.centerIn: parent
                    text: "󰄄"
                    font.family: "JetBrains Mono NF"
                    font.pixelSize: root.fontSizeRegular
                    color: parent.containsMouse ? root.dynamicAccent : root.dynamicFg
                }
                onClicked: Quickshell.execDetached(["grim", "-g", "$(slurp)", "- | wl-copy"]);
            }
        }

        Item {
            visible: Config.options?.bar?.utilButtons?.showColorPicker ?? false
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: root.iconBoxWidth
            implicitHeight: root.itemHeight
            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                Rectangle {
                    anchors.fill: parent
                    radius: Math.round(4 * root.scaleRatio)
                    color: parent.containsMouse ? root.dynamicHoverBg : "transparent"
                }
                Text {
                    anchors.centerIn: parent
                    text: "󰈊"
                    font.family: "JetBrains Mono NF"
                    font.pixelSize: root.fontSizeRegular
                    color: parent.containsMouse ? root.dynamicAccent : root.dynamicFg
                }
                onClicked: Quickshell.execDetached(["hyprpicker", "-a"]);
            }
        }

        Item {
            visible: Config.options?.bar?.utilButtons?.showScreenRecord ?? false
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: root.iconBoxWidth
            implicitHeight: root.itemHeight
            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                Rectangle {
                    anchors.fill: parent
                    radius: Math.round(4 * root.scaleRatio)
                    color: parent.containsMouse ? root.dynamicHoverBg : "transparent"
                }
                Text {
                    anchors.centerIn: parent
                    text: "󰕧"
                    font.family: "JetBrains Mono NF"
                    font.pixelSize: root.fontSizeRegular
                    color: parent.containsMouse ? "#ff3366" : root.dynamicFg
                }
                onClicked: Quickshell.execDetached([Directories.recordScriptPath]);
            }
        }

        Item {
            visible: Config.options?.bar?.utilButtons?.showKeyboardToggle ?? false
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: root.iconBoxWidth
            implicitHeight: root.itemHeight
            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                Rectangle {
                    anchors.fill: parent
                    radius: Math.round(4 * root.scaleRatio)
                    color: parent.containsMouse ? root.dynamicHoverBg : "transparent"
                }
                Text {
                    anchors.centerIn: parent
                    text: "󰌌"
                    font.family: "JetBrains Mono NF"
                    font.pixelSize: root.fontSizeRegular
                    color: parent.containsMouse ? root.dynamicAccent : root.dynamicFg
                }
                onClicked: GlobalStates.oskOpen = !GlobalStates.oskOpen
            }
        }

        Item {
            visible: Config.options?.bar?.utilButtons?.showMicToggle ?? false
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: root.iconBoxWidth
            implicitHeight: root.itemHeight
            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                Rectangle {
                    anchors.fill: parent
                    radius: Math.round(4 * root.scaleRatio)
                    color: parent.containsMouse ? root.dynamicHoverBg : "transparent"
                }
                Text {
                    anchors.centerIn: parent
                    text: (Audio.source?.audio?.muted ?? false) ? "󰍭" : "󰍬"
                    font.family: "JetBrains Mono NF"
                    font.pixelSize: root.fontSizeRegular
                    color: (Audio.source?.audio?.muted ?? false) ? "#ff3366" : (parent.containsMouse ? root.dynamicAccent : root.dynamicFg)
                }
                onClicked: {
                    if (Audio.source?.audio) Audio.source.audio.muted = !Audio.source.audio.muted;
                }
            }
        }

        Item {
            visible: Config.options?.bar?.utilButtons?.showDarkModeToggle ?? false
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: root.iconBoxWidth
            implicitHeight: root.itemHeight
            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                Rectangle {
                    anchors.fill: parent
                    radius: Math.round(4 * root.scaleRatio)
                    color: parent.containsMouse ? root.dynamicHoverBg : "transparent"
                }
                Text {
                    anchors.centerIn: parent
                    text: Appearance.m3colors.darkmode ? "󰖨" : "󰖔"
                    font.family: "JetBrains Mono NF"
                    font.pixelSize: root.fontSizeRegular
                    color: parent.containsMouse ? root.dynamicAccent : root.dynamicFg
                }
                onClicked: {
                    Quickshell.execDetached([Directories.wallpaperSwitchScriptPath, "--mode", Appearance.m3colors.darkmode ? "light" : "dark", "--noswitch"]);
                }
            }
        }

        // System Tray
        SysTray {
            Layout.alignment: Qt.AlignVCenter
            Layout.fillHeight: true
        }

        Rectangle {
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: 1
            implicitHeight: root.sepHeight
            color: root.dynamicBorder
        }

        // Audio Volume Module
        MouseArea {
            id: volArea
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: volContent.implicitWidth + Math.round(10 * root.scaleRatio)
            implicitHeight: root.itemHeight
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            acceptedButtons: Qt.LeftButton | Qt.RightButton

            Rectangle {
                anchors.fill: parent
                radius: Math.round(4 * root.scaleRatio)
                color: volArea.containsMouse ? root.dynamicHoverBg : "transparent"
                Behavior on color { ColorAnimation { duration: 120 } }
            }

            onClicked: event => {
                if (event.button === Qt.RightButton) {
                    GlobalStates.sidebarRightOpen = !GlobalStates.sidebarRightOpen;
                } else {
                    if (Audio.sink?.audio) {
                        Audio.sink.audio.muted = !Audio.sink.audio.muted;
                    }
                }
            }
            onWheel: event => {
                if (event.angleDelta.y > 0) Audio.incrementVolume();
                else Audio.decrementVolume();
            }

            Row {
                id: volContent
                anchors.centerIn: parent
                spacing: Math.max(2, Math.round(4 * root.scaleRatio))

                Text {
                    text: (Audio.sink?.audio?.muted ?? false) ? "󰝟" : (((Audio.sink?.audio?.volume ?? 0) > 0.5) ? "" : "")
                    font.family: "JetBrains Mono NF"
                    font.pixelSize: root.fontSizeRegular
                    color: (Audio.sink?.audio?.muted ?? false) 
                        ? "#ff3366" 
                        : (volArea.containsMouse ? root.dynamicAccent : root.dynamicFg)
                    anchors.verticalCenter: parent.verticalCenter
                }

                Text {
                    text: `${Math.round((Audio.sink?.audio?.volume ?? 0) * 100)}%`
                    font.family: "JetBrains Mono NF"
                    font.pixelSize: root.fontSizeSmall
                    color: volArea.containsMouse ? root.dynamicAccent : root.dynamicFg
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }

        // Network Module
        MouseArea {
            id: netArea
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: root.iconBoxWidth
            implicitHeight: root.itemHeight
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: {
                GlobalStates.sidebarRightOpen = !GlobalStates.sidebarRightOpen;
            }

            Rectangle {
                anchors.fill: parent
                radius: Math.round(4 * root.scaleRatio)
                color: netArea.containsMouse ? root.dynamicHoverBg : "transparent"
                Behavior on color { ColorAnimation { duration: 120 } }
            }

            Text {
                id: netIcon
                anchors.centerIn: parent
                text: Network.connected ? "󰖩" : "󰤮"
                font.family: "JetBrains Mono NF"
                font.pixelSize: root.fontSizeRegular
                color: Network.connected 
                    ? (netArea.containsMouse ? root.dynamicSecondary : root.dynamicAccent)
                    : root.dynamicDim
            }
        }

        // Bluetooth Module
        MouseArea {
            id: btArea
            visible: BluetoothStatus.available
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: root.iconBoxWidth
            implicitHeight: root.itemHeight
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            acceptedButtons: Qt.LeftButton | Qt.RightButton

            Rectangle {
                anchors.fill: parent
                radius: Math.round(4 * root.scaleRatio)
                color: btArea.containsMouse ? root.dynamicHoverBg : "transparent"
                Behavior on color { ColorAnimation { duration: 120 } }
            }

            onClicked: event => {
                if (event.button === Qt.RightButton) {
                    if (Bluetooth.defaultAdapter) {
                        Bluetooth.defaultAdapter.enabled = !Bluetooth.defaultAdapter.enabled;
                    }
                    Quickshell.execDetached(["bluetoothctl", "power", BluetoothStatus.enabled ? "off" : "on"]);
                } else {
                    GlobalStates.sidebarRightOpen = !GlobalStates.sidebarRightOpen;
                }
            }

            Text {
                id: btIcon
                anchors.centerIn: parent
                text: !BluetoothStatus.enabled ? "󰂲" : (BluetoothStatus.connected ? "󰂱" : "󰂯")
                font.family: "JetBrains Mono NF"
                font.pixelSize: root.fontSizeMedium
                color: BluetoothStatus.connected 
                    ? root.dynamicAccent 
                    : (BluetoothStatus.enabled ? (btArea.containsMouse ? root.dynamicAccent : root.dynamicFg) : root.dynamicDim)
                Behavior on color { ColorAnimation { duration: 120 } }
            }
        }

        // Battery Module (if available)
        Item {
            visible: Battery.available
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: batContent.implicitWidth + Math.round(8 * root.scaleRatio)
            implicitHeight: root.itemHeight

            MouseArea {
                id: batArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    GlobalStates.sidebarRightOpen = !GlobalStates.sidebarRightOpen;
                }

                Rectangle {
                    anchors.fill: parent
                    radius: Math.round(4 * root.scaleRatio)
                    color: batArea.containsMouse ? root.dynamicHoverBg : "transparent"
                    Behavior on color { ColorAnimation { duration: 120 } }
                }

                Row {
                    id: batContent
                    anchors.centerIn: parent
                    spacing: Math.max(2, Math.round(4 * root.scaleRatio))

                    Text {
                        text: Battery.charging ? "󰂄" : (Battery.percentage > 80 ? "󰁹" : (Battery.percentage > 40 ? "󰁿" : "󰁻"))
                        font.family: "JetBrains Mono NF"
                        font.pixelSize: root.fontSizeRegular
                        color: Battery.percentage < 20 
                            ? "#ff3366" 
                            : (Battery.charging ? root.dynamicSecondary : root.dynamicAccent)
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    Text {
                        text: `${Math.round(Battery.percentage)}%`
                        font.family: "JetBrains Mono NF"
                        font.pixelSize: root.fontSizeSmall
                        color: batArea.containsMouse ? root.dynamicAccent : root.dynamicFg
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }
        }

        Rectangle {
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: 1
            implicitHeight: root.sepHeight
            color: root.dynamicBorder
        }

        // Theme Picker Quick Action (Alt + T)
        MouseArea {
            id: themeBtn
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: root.iconBoxWidth
            implicitHeight: root.itemHeight
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            acceptedButtons: Qt.LeftButton | Qt.RightButton

            Rectangle {
                anchors.fill: parent
                radius: Math.round(4 * root.scaleRatio)
                color: themeBtn.containsMouse ? root.dynamicHoverBg : "transparent"
                Behavior on color { ColorAnimation { duration: 120 } }
            }

            onClicked: event => {
                if (event.button === Qt.RightButton) {
                    Quickshell.execDetached(["/home/sasel/.config/hypr/scripts/bwm-theme-manager.py", "toggle"]);
                } else {
                    Quickshell.execDetached(["/home/sasel/.config/hypr/scripts/theme-picker.sh"]);
                }
            }

            Text {
                anchors.centerIn: parent
                text: "󰔎"
                font.family: "JetBrains Mono NF"
                font.pixelSize: root.fontSizeRegular
                color: themeBtn.containsMouse ? root.dynamicSecondary : root.dynamicAccent
                Behavior on color { ColorAnimation { duration: 120 } }
            }
        }
    }
}
