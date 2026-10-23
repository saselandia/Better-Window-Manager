pragma ComponentBehavior: Bound

import qs
import qs.services
import qs.modules.common
import qs.modules.ii.plasmaCommon
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Widgets
import Quickshell.Services.Pipewire

/**
 * KDE Plasma 6 audio applet (plasma-pa) recreated in Breeze Dark.
 * - Opened from the volume button of the Plasma taskbar (left click); middle click mutes,
 *   wheel changes the volume.
 * - Header: title, mute switch and "Configure…" (volume mixer app).
 * - Sections: Output (default device slider + other devices), Input (same for the
 *   microphone) and Applications (one volume slider per playing app).
 * - IPC: quickshell -c ii ipc call plasmaAudio toggle|open|close
 */
Scope {
    id: root

    readonly property bool opened: GlobalStates.plasmaAudioOpen

    function icon(name) { return Breeze.icon("audio", name); }
    function open() { GlobalStates.plasmaAudioOpen = true; }
    function close() { GlobalStates.plasmaAudioOpen = false; }
    function toggle() { GlobalStates.plasmaAudioOpen ? close() : open(); }

    function volumeIcon(node, isInput) {
        const a = node?.audio;
        const v = a?.volume ?? 0;
        if (isInput) {
            if (a?.muted || v <= 0) return "microphone-sensitivity-muted";
            return v < 0.34 ? "microphone-sensitivity-low" : (v < 0.67 ? "microphone-sensitivity-medium" : "microphone-sensitivity-high");
        }
        if (a?.muted || v <= 0) return "audio-volume-muted";
        if (v > 1.0) return "audio-volume-high-warning";
        return v < 0.34 ? "audio-volume-low" : (v < 0.67 ? "audio-volume-medium" : "audio-volume-high");
    }
    function deviceIcon(node, isInput) {
        if (isInput) return "audio-input-microphone";
        const n = ((node?.nickname ?? "") + " " + (node?.description ?? "") + " " + (node?.name ?? "")).toLowerCase();
        if (n.includes("headset")) return "audio-headset";
        if (n.includes("headphone") || n.includes("auricular")) return "audio-headphones";
        return "audio-card";
    }
    function appIcon(node) {
        const n = node?.properties?.["application.icon-name"] ?? node?.properties?.["application.name"] ?? "";
        return Quickshell.iconPath(AppSearch.guessIcon(n), "application-x-executable");
    }
    function percent(node) { return Math.round((node?.audio?.volume ?? 0) * 100); }

    // Needed to read/write volume and mute of nodes other than the default ones
    PwObjectTracker {
        objects: [...Audio.outputDevices, ...Audio.inputDevices, ...Audio.outputAppNodes]
    }

    IpcHandler {
        target: "plasmaAudio"
        function toggle(): void { root.toggle(); }
        function open(): void { root.open(); }
        function close(): void { root.close(); }
    }

    // One volume row: mute icon button, slider, percentage
    component VolumeRow: RowLayout {
        id: vr
        property var node
        property string iconSrc
        property bool isInput: false
        property string label: ""
        property url appIconSource: ""
        Layout.fillWidth: true
        Layout.leftMargin: 6
        Layout.rightMargin: 6
        spacing: 8

        MouseArea {
            Layout.preferredWidth: 28
            Layout.preferredHeight: 28
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: { if (vr.node?.audio) vr.node.audio.muted = !vr.node.audio.muted; }
            Rectangle {
                anchors.fill: parent
                radius: 4
                color: parent.containsMouse ? Breeze.hover : "transparent"
            }
            Image {
                anchors.centerIn: parent
                width: 22; height: 22
                sourceSize: Qt.size(44, 44)
                visible: vr.appIconSource.toString() === ""
                source: vr.iconSrc
            }
            IconImage {
                anchors.centerIn: parent
                implicitSize: 22
                visible: vr.appIconSource.toString() !== ""
                source: vr.appIconSource
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 0
            Text {
                visible: vr.label !== ""
                Layout.fillWidth: true
                text: vr.label
                elide: Text.ElideRight
                color: Breeze.text
                font.family: Breeze.fontFamily
                font.pixelSize: 12
            }
            BreezeSlider {
                Layout.fillWidth: true
                value: vr.node?.audio?.volume ?? 0
                onMoved: v => { if (vr.node?.audio) vr.node.audio.volume = v; }
            }
        }

        Text {
            Layout.preferredWidth: 38
            horizontalAlignment: Text.AlignRight
            text: root.percent(vr.node) + "%"
            color: vr.node?.audio?.muted ? Breeze.negative : Breeze.textMuted
            font.family: Breeze.fontFamily
            font.pixelSize: 12
        }
    }

    // Selectable device (Plasma's radio-style device list)
    component DeviceRow: Rectangle {
        id: dr
        property var node
        property bool isInput: false
        readonly property bool isDefault: isInput ? node === Audio.source : node === Audio.sink
        Layout.fillWidth: true
        Layout.leftMargin: 6
        Layout.rightMargin: 6
        Layout.preferredHeight: 32
        radius: 4
        color: area.containsMouse ? Breeze.hover : (isDefault ? Breeze.accentSubtle : "transparent")
        border.width: isDefault ? 1 : 0
        border.color: Breeze.accentBorder

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 8
            anchors.rightMargin: 8
            spacing: 8
            Image {
                Layout.preferredWidth: 18; Layout.preferredHeight: 18
                sourceSize: Qt.size(36, 36)
                source: root.icon(root.deviceIcon(dr.node, dr.isInput))
            }
            Text {
                Layout.fillWidth: true
                text: dr.node ? Audio.friendlyDeviceName(dr.node) : ""
                elide: Text.ElideRight
                color: Breeze.text
                font.family: Breeze.fontFamily
                font.pixelSize: 12
            }
            Text {
                visible: dr.isDefault
                text: "Predeterminado"
                color: Breeze.accent
                font.family: Breeze.fontFamily
                font.pixelSize: 11
            }
        }
        MouseArea {
            id: area
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: dr.isInput ? Audio.setDefaultSource(dr.node) : Audio.setDefaultSink(dr.node)
        }
    }

    BreezePopupWindow {
        opened: root.opened
        anchorX: GlobalStates.plasmaAudioAnchorX
        screenName: GlobalStates.plasmaAudioScreen
        namespace: "quickshell:plasmaAudio"
        popupWidth: 380
        popupHeight: 480
        onCloseRequested: root.close()

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            BreezeHeader {
                Text {
                    Layout.fillWidth: true
                    text: "Volumen"
                    color: Breeze.text
                    font.family: Breeze.fontFamily
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                }
                BreezeToolButton {
                    label: "Configurar…"
                    onClicked: Quickshell.execDetached(["bash", "-c", Config.options.apps.volumeMixer])
                }
                BreezeSwitch {
                    checked: !(Audio.sink?.audio?.muted ?? false)
                    enabled: Audio.sink?.audio !== undefined
                    onToggled: Audio.toggleMute()
                }
            }

            Flickable {
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentHeight: body.implicitHeight + 8
                clip: true
                boundsBehavior: Flickable.StopAtBounds

                ColumnLayout {
                    id: body
                    width: parent.width
                    spacing: 4

                    BreezeSectionHeader { title: "Salida" }
                    VolumeRow {
                        node: Audio.sink
                        iconSrc: root.icon(root.volumeIcon(Audio.sink, false))
                        label: Audio.sink ? Audio.friendlyDeviceName(Audio.sink) : "Sin dispositivo de salida"
                    }
                    Repeater {
                        model: Audio.outputDevices.length > 1 ? Audio.outputDevices : []
                        delegate: DeviceRow { required property var modelData; node: modelData }
                    }

                    BreezeSectionHeader { title: "Entrada" }
                    VolumeRow {
                        node: Audio.source
                        isInput: true
                        iconSrc: root.icon(root.volumeIcon(Audio.source, true))
                        label: Audio.source ? Audio.friendlyDeviceName(Audio.source) : "Sin dispositivo de entrada"
                    }
                    Repeater {
                        model: Audio.inputDevices.length > 1 ? Audio.inputDevices : []
                        delegate: DeviceRow { required property var modelData; node: modelData; isInput: true }
                    }

                    BreezeSectionHeader { title: "Aplicaciones" }
                    Repeater {
                        model: Audio.outputAppNodes
                        delegate: VolumeRow {
                            required property var modelData
                            node: modelData
                            iconSrc: ""
                            appIconSource: root.appIcon(modelData)
                            label: Audio.appNodeDisplayName(modelData)
                        }
                    }
                    Text {
                        visible: Audio.outputAppNodes.length === 0
                        Layout.fillWidth: true
                        Layout.topMargin: 8
                        horizontalAlignment: Text.AlignHCenter
                        text: "Ninguna aplicación está reproduciendo audio"
                        color: Breeze.textMuted
                        font.family: Breeze.fontFamily
                        font.pixelSize: 12
                    }
                }
            }
        }
    }
}
