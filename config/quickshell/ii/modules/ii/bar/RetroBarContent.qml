import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import qs
import qs.services
import qs.modules.common
import qs.modules.common.models
import qs.modules.ii.bar.omarchy
import qs.Commons as O

// The Retro bar: Omarchy's bar (shell/plugins/bar/Bar.qml, MIT) laid out like its default
// shell.json, with Omarchy's own widgets wherever BWM has them (bar/omarchy/*): menu, workspaces,
// indicators, clock, tray and the status panels, plus the Omarchy plugins installed with
// bwm-plugin.sh. Colours are Omarchy's `[bar]` tokens (Commons/Color.qml, from shell.toml), so a
// light theme gets dark text like in Omarchy.
Item {
    id: root

    property var screen: root.QsWindow.window?.screen
    readonly property HyprlandMonitor monitor: Hyprland.monitorFor(screen)

    readonly property real barH: Math.max(16, root.height)
    // Omarchy's bar paddings and the gap between its sections (Style.space scales with the bar)
    readonly property real edgeMargin: O.Style.space(8)

    // Without a background the bar sits on the wallpaper: like Omarchy's clear bar, the text takes
    // whichever of the theme's text and background colours stands out more against the wallpaper
    // under it (omarchy-bar-text-color samples it)
    readonly property bool transparentBar: !(Config.options?.bar?.showBackground ?? true)
    property color wallpaperForeground: O.Color.bar.text
    property color barForeground: transparentBar ? wallpaperForeground : O.Color.bar.text
    property color barBackground: O.Color.bar.background
    readonly property color barUrgent: O.Color.bar.active
    readonly property string fontFamily: O.Style.font.family

    // Omarchy cross-fades the bar's colours when the theme changes
    Behavior on barForeground { ColorAnimation { duration: 250; easing.type: Easing.OutCubic } }
    Behavior on barBackground { ColorAnimation { duration: 250; easing.type: Easing.OutCubic } }

    function hex(c) {
        const ch = v => Math.round(Math.max(0, Math.min(1, v)) * 255).toString(16).padStart(2, "0");
        return "#" + ch(c.r) + ch(c.g) + ch(c.b);
    }

    function refreshWallpaperForeground() {
        if (!root.transparentBar || !root.screen || textColorProc.running)
            return;
        textColorProc.command = ["bash", "-c", 'PATH="$HOME/.config/hypr/scripts/omarchy-shims:$PATH" exec omarchy-bar-text-color "$@"', "-",
            (Config.options?.bar?.bottom ?? false) ? "bottom" : "top", String(Math.round(root.barH)),
            root.hex(O.Color.bar.text), root.hex(O.Color.background), "--screen", `${root.screen.width}x${root.screen.height}`];
        textColorProc.running = true;
    }

    onTransparentBarChanged: refreshWallpaperForeground()
    Connections {
        target: O.Color.bar
        function onTextChanged() { textColorTimer.restart(); }
    }
    Timer {
        id: textColorTimer
        interval: 120
        running: root.transparentBar
        onTriggered: root.refreshWallpaperForeground()
    }
    Process {
        id: textColorProc
        stdout: SplitParser {
            onRead: line => {
                const value = String(line || "").trim();
                if (/^#[0-9A-Fa-f]{6}$/.test(value))
                    root.wallpaperForeground = value;
            }
        }
    }

    // A new wallpaper (set-wallpaper.sh writes its path there) needs a new sample
    FileView {
        path: Quickshell.env("HOME") + "/.cache/current_wallpaper"
        watchChanges: true
        printErrors: false
        onFileChanged: textColorTimer.restart()
    }

    // set-wallpaper.sh and bwm_omarchy.py still ask the bar to reload its palette: Color.qml
    // follows ~/.local/state/bwm/omarchy by itself
    IpcHandler {
        target: "retro"
        function reload(): void {}
    }

    // Omarchy's widgets (clock, plugins, their panels) scale with the bar
    Binding {
        target: O.Style
        property: "bwmScale"
        value: Math.max(0.75, Math.min(2.5, root.barH / 24))
    }

    WorkspaceModel {
        id: wsModel
        monitor: root.monitor
    }

    component Slot: OmarchyPluginSlot {
        foreground: root.barForeground
        background: root.barBackground
        urgent: root.barUrgent
        fontFamily: root.fontFamily
        barSize: root.barH
        spacing: 0
    }

    Rectangle {
        anchors.fill: parent
        color: root.barBackground
        visible: Config.options?.bar?.showBackground ?? true
    }

    // -----------------------------------------------------------------
    // left: omarchy.menu, omarchy.workspaces (+ the special workspace), plugins
    // -----------------------------------------------------------------
    Row {
        id: leftSection
        anchors.left: parent.left
        anchors.leftMargin: root.edgeMargin
        anchors.verticalCenter: parent.verticalCenter
        height: root.barH

        Slot {
            section: "left"
            anchors.verticalCenter: parent.verticalCenter
            fixedEntries: [{
                id: "omarchy.menu",
                source: Qt.resolvedUrl("omarchy/menu/BarWidget.qml"),
                settings: {
                    icon: Config.options?.cheatsheet?.superKey || "󰣇",
                    fontFamily: Appearance.font.family.iconNerd
                }
            }, {
                id: "omarchy.workspaces",
                source: Qt.resolvedUrl("omarchy/workspaces/BarWidget.qml"),
                settings: ({})
            }]
            opacity: wsModel.specialWorkspaceActive ? 0.35 : 1
            Behavior on opacity { NumberAnimation { duration: 160 } }
        }

        // Special workspace (Alt+S "magic"): the workspaces dim and a framed label shows it.
        // Click hides it again.
        MouseArea {
            id: specialWsArea
            anchors.verticalCenter: parent.verticalCenter
            readonly property bool shown: wsModel.specialWorkspaceActive
            width: shown ? specialWsLabel.implicitWidth + O.Style.space(12) : 0
            height: Math.round(root.barH * 0.78)
            visible: width > 0
            clip: true
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: Hyprland.dispatch(`hl.dsp.workspace.toggle_special("${wsModel.specialWorkspaceName}")`)

            Behavior on width {
                NumberAnimation { duration: 160; easing.type: Easing.OutCubic }
            }

            Rectangle {
                anchors.fill: parent
                color: O.Util.alpha(root.barForeground, specialWsArea.containsMouse ? 0.16 : 0.08)
                border.width: 1
                border.color: O.Util.alpha(root.barForeground, 0.5)
            }

            Text {
                id: specialWsLabel
                anchors.centerIn: parent
                text: `󰜗 ${wsModel.specialWorkspaceName}`
                font.family: root.fontFamily
                font.pixelSize: O.Style.font.body
                color: root.barForeground
            }
        }

        Slot {
            section: "left"
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    // -----------------------------------------------------------------
    // centerBegin (omarchy.indicators, plugins) | center (omarchy.clock) | centerEnd (plugins)
    // -----------------------------------------------------------------
    // Omarchy's clock (bar/omarchy/clock, from Omarchy's omarchy.clock): its formats (right click
    // cycles them) and its calendar dropdown on click. BWM's clock below is only the fallback if
    // it fails to load.
    Slot {
        id: omarchyClock
        section: "clock"
        fixedEntries: [{
            id: "omarchy.clock",
            source: Qt.resolvedUrl("omarchy/clock/BarWidget.qml"),
            settings: OmarchyPlugins.builtinSettings("omarchy.clock")
        }]
        anchors.centerIn: parent
        HoverHandler { id: omarchyClockHover }
    }

    MouseArea {
        id: centerClockArea
        visible: !omarchyClock.visible
        anchors.centerIn: parent
        implicitWidth: centerClockText.implicitWidth + O.Style.space(16)
        implicitHeight: root.barH
        hoverEnabled: true

        Text {
            id: centerClockText
            anchors.centerIn: parent
            // Omarchy's clock format ("dddd HH:mm"), the long date while hovered (its formatAlt)
            text: Qt.formatDateTime(DateTime.clock.date, centerClockArea.containsMouse ? "d MMMM 'W'ww yyyy" : "dddd HH:mm")
            font.family: root.fontFamily
            font.pixelSize: O.Style.font.body
            color: root.barForeground
        }
    }

    readonly property Item clockItem: omarchyClock.visible ? omarchyClock : centerClockArea

    OmarchyIndicators {
        id: omarchyIndicators
        anchors.right: root.clockItem.left
        anchors.verticalCenter: parent.verticalCenter
        foreground: root.barForeground
        urgent: root.barUrgent
        itemHeight: root.barH
        fontSize: O.Style.font.icon
        revealHeld: centerClockArea.containsMouse || omarchyClockHover.hovered
    }

    Slot {
        section: "center"
        // Between the left section (workspaces, active window) and the indicators
        widthBudget: Math.max(0, omarchyIndicators.x - (leftSection.x + leftSection.width) - 24)
        anchors.right: omarchyIndicators.left
        anchors.verticalCenter: parent.verticalCenter
    }

    Slot {
        id: centerEndPlugins
        section: "centerEnd"
        anchors.left: root.clockItem.right
        anchors.verticalCenter: parent.verticalCenter
    }

    // Stand-in slot for the fixed widgets on the right: plugins that size themselves from the free
    // bar space (omarchy-mpris, BarGeometry.js) count it like another widget there.
    Item {
        readonly property var activeItem: this
        readonly property string region: "right"
        x: rightSection.x + rightPlugins.width
        y: 0
        width: Math.max(0, rightSection.width - rightPlugins.width)
        height: 1
    }

    // -----------------------------------------------------------------
    // right: plugins, omarchy.tray, then Omarchy's status panels in its order
    // -----------------------------------------------------------------
    Row {
        id: rightSection
        anchors.right: parent.right
        anchors.rightMargin: root.edgeMargin
        anchors.verticalCenter: parent.verticalCenter
        height: root.barH

        Slot {
            id: rightPlugins
            section: "right"
            anchors.verticalCenter: parent.verticalCenter
            // Never over the clock or the widgets after it: plugins that do not fit are hidden
            readonly property real centerEnd: centerEndPlugins.visible ? centerEndPlugins.x + centerEndPlugins.width
                : root.clockItem.x + root.clockItem.width
            maxWidth: Math.max(0, root.width - root.edgeMargin - statusSlot.width - centerEnd - 12)
        }

        Slot {
            id: statusSlot
            section: "status"
            anchors.verticalCenter: parent.verticalCenter
            // Each one can be hidden in Settings → Bar (`disabled` of omarchy-plugins.json)
            // Off by default (shown only when listed in `shown`): media, as the mpris plugin is there
            readonly property var defaultHidden: ["omarchy.media"]
            fixedEntries: ["media", "system-update"].map(n => ({
                id: "omarchy." + n,
                source: Qt.resolvedUrl("omarchy/" + n + "/BarWidget.qml"),
                settings: OmarchyPlugins.builtinSettings("omarchy." + n)
            })).concat([{
                id: "omarchy.tray",
                source: Qt.resolvedUrl("omarchy/tray/BarWidget.qml"),
                settings: OmarchyPlugins.builtinSettings("omarchy.tray")
            }, {
                id: "omarchy.keyboard-layout",
                source: Qt.resolvedUrl("omarchy/keyboard-layout/BarWidget.qml"),
                settings: OmarchyPlugins.builtinSettings("omarchy.keyboard-layout")
            }]).concat(["agents", "tailscale", "bluetooth", "network", "audio", "monitor", "power"].map(n => ({
                id: "omarchy." + n,
                source: Qt.resolvedUrl("omarchy/" + n + "/Panel.qml"),
                settings: OmarchyPlugins.builtinSettings("omarchy." + n)
            }))).filter(e => !(OmarchyPlugins.layout.disabled ?? []).includes(e.id)
                && (!defaultHidden.includes(e.id) || (OmarchyPlugins.layout.shown ?? []).includes(e.id)))
        }
    }
}
