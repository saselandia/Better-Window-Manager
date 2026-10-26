pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
import qs.modules.common

// Omarchy's bar indicators (shell/plugins/bar/widgets/Indicators.qml, MIT) next to the clock in
// the Retro bar: one glyph per state, only the active ones show; hovering the group reveals
// the inactive ones at 45 % so they can be turned on. Recording calls attention in red, as
// Omarchy's `bar.active` colour does. Same glyphs as Omarchy's indicators.
Row {
    id: root

    property color foreground: "white"
    property color urgent: "#f7768e"
    property int itemHeight: 24
    property int fontSize: 13
    // Omarchy reveals the inactive ones while the clock section is hovered too
    property bool revealHeld: false
    property bool hovered: hover.hovered || revealHeld

    spacing: 0
    height: itemHeight

    property bool recording: false
    Process {
        id: recordingProbe
        // BWM's recorder (wf-recorder) or Omarchy's capture (gpu-screen-recorder / wf-recorder)
        command: ["bash", "-c", "pgrep -x wf-recorder >/dev/null || pgrep -f '^gpu-screen-recorder' >/dev/null"]
        onExited: code => root.recording = code === 0
    }
    Timer {
        interval: 2000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: recordingProbe.running = true
    }

    // Reminders (omarchy-reminder, Omarchy's bar/indicators/Reminder.qml): count of active timers
    property int reminderCount: 0
    property string reminderTip: ""
    Process {
        id: reminderProbe
        command: ["omarchy-reminder", "show", "--json"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const d = JSON.parse(text);
                    root.reminderCount = Number(d.count || 0);
                    root.reminderTip = String(d.tooltip || "");
                } catch (e) {
                    root.reminderCount = 0;
                }
            }
        }
    }
    Timer {
        interval: 15000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: reminderProbe.running = true
    }

    HoverHandler { id: hover }

    Repeater {
        model: [
            { glyph: "󰻂", active: root.recording, urgent: true, tip: "Stop recording",
              run: () => Quickshell.execDetached(["bash", "-c", "omarchy-capture-screenrecording --status && omarchy-capture-screenrecording --stop-recording || " + Directories.recordScriptPath]) },
            { glyph: "󰔎", active: Hyprsunset.temperatureActive, urgent: false, tip: "Night light",
              run: () => Hyprsunset.toggleTemperature() },
            { glyph: "󰂛", active: Notifications.silent, urgent: false, tip: "Do not disturb",
              run: () => { Notifications.silent = !Notifications.silent; } },
            { glyph: "", active: Idle.inhibit, urgent: false, tip: "Stay awake",
              run: () => Idle.toggleInhibit() },
            { glyph: "󰢌", active: root.reminderCount > 0, urgent: false, tip: root.reminderTip || "Reminder",
              run: () => Quickshell.execDetached(["omarchy-reminder", root.reminderCount > 0 ? "show" : "-i"]) }
        ]

        delegate: MouseArea {
            id: ind
            required property var modelData
            readonly property bool shown: modelData.active || root.hovered
            width: shown ? Math.round(root.itemHeight * 1.15) : 0
            height: root.itemHeight
            visible: width > 0
            opacity: modelData.active ? 1 : 0.45
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: modelData.run()

            Behavior on width { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }

            Text {
                anchors.centerIn: parent
                text: ind.modelData.glyph
                color: ind.modelData.active && ind.modelData.urgent ? root.urgent : root.foreground
                font.family: Appearance.font.family.iconNerd
                font.pixelSize: root.fontSize
            }
        }
    }
}
