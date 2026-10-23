import qs
import qs.services
import qs.modules.common
import qs.modules.ii.plasmaCommon
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland

/**
 * Plasma "Global Theme" style picker for the BWM themes (Default, Retro, Plasma),
 * recreated in Breeze Dark: header + list of cards with a live-colored mini preview,
 * current theme marked with the accent border and a check.
 * - Opened from the palette button of the Plasma taskbar (left click) or Alt+T.
 * - IPC: quickshell -c ii ipc call plasmaThemePicker toggle|open|close
 */
Scope {
    id: root

    readonly property bool opened: GlobalStates.plasmaThemePickerOpen
    property string current: "plasma"
    property int highlighted: 0   // row under the keyboard cursor (arrows, or hover)
    readonly property string manager: "/home/sasel/.config/hypr/scripts/bwm-theme-manager.py"

    readonly property var themes: [
        {
            id: "default", title: "Material You", subtitle: "Colores dinámicos del fondo de pantalla",
            bg: "#1c1b1f", window: "#2b2930", titlebar: "#36343b", accent: "#d0bcff", panel: "#2b2930", panelPos: "floating"
        },
        {
            id: "retro", title: "Retro (Omarchy)", subtitle: "Cyberpunk con acentos neón",
            bg: "#0f0f09", window: "#14140c", titlebar: "#1b1b10", accent: "#fffd02", panel: "#0f0f09", panelPos: "top"
        },
        {
            id: "plasma", title: "Breeze Dark", subtitle: "Estilo KDE Plasma 6",
            bg: "#1b1e20", window: "#31363b", titlebar: "#2a2e32", accent: "#3daee9", panel: "#24292e", panelPos: "bottom"
        }
    ]

    // Opened without a taskbar button (Alt+T / IPC): show it on the monitor that has
    // the focus (where the mouse is), at the right edge like Plasma's tray popups
    function open() {
        GlobalStates.plasmaThemePickerScreen = Hyprland.focusedMonitor?.name ?? "";
        GlobalStates.plasmaThemePickerAnchorX = -1;
        root.highlighted = root.indexOfCurrent();
        current_proc.running = true;
        GlobalStates.plasmaThemePickerOpen = true;
    }
    function close() { GlobalStates.plasmaThemePickerOpen = false; }
    function toggle() { GlobalStates.plasmaThemePickerOpen ? close() : open(); }
    function apply(id) {
        root.close();
        if (id !== root.current) Quickshell.execDetached([root.manager, "set", id]);
    }
    function indexOfCurrent() { return Math.max(0, root.themes.findIndex(t => t.id === root.current)); }
    function moveHighlight(step) {
        root.highlighted = Math.max(0, Math.min(root.themes.length - 1, root.highlighted + step));
    }

    onOpenedChanged: if (opened) {
        current_proc.running = true;
        // The layer surface takes the keyboard only once mapped: grab focus after this frame
        Qt.callLater(() => keys.forceActiveFocus());
    }

    Process {
        id: current_proc
        command: [root.manager, "get"]
        stdout: StdioCollector {
            onStreamFinished: {
                const t = text.trim();
                if (t.length > 0) {
                    root.current = t;
                    root.highlighted = root.indexOfCurrent();
                }
            }
        }
    }

    IpcHandler {
        target: "plasmaThemePicker"
        function toggle(): void { root.toggle(); }
        function open(): void { root.open(); }
        function close(): void { root.close(); }
    }

    BreezePopupWindow {
        opened: root.opened
        anchorX: GlobalStates.plasmaThemePickerAnchorX
        screenName: GlobalStates.plasmaThemePickerScreen
        namespace: "quickshell:plasmaThemePicker"
        popupWidth: 400
        popupHeight: 44 + root.themes.length * 96 + 12 + 30
        onCloseRequested: root.close()

        // Keyboard: Up/Down move the highlight, Enter applies it, Escape closes
        Item {
            id: keys
            anchors.fill: parent
            Keys.onPressed: event => {
                if (event.key === Qt.Key_Down) root.moveHighlight(1);
                else if (event.key === Qt.Key_Up) root.moveHighlight(-1);
                else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) root.apply(root.themes[root.highlighted].id);
                else if (event.key === Qt.Key_Escape) root.close();
                else return;
                event.accepted = true;
            }
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            BreezeHeader {
                Text {
                    Layout.fillWidth: true
                    text: "Tema global"
                    color: Breeze.text
                    font.family: Breeze.fontFamily
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.margins: 6
                spacing: 4

                Repeater {
                    model: root.themes
                    delegate: Rectangle {
                        id: card
                        required property var modelData
                        required property int index
                        readonly property bool selected: root.current === modelData.id
                        Layout.fillWidth: true
                        Layout.preferredHeight: 92
                        radius: 4
                        color: (area.containsMouse || index === root.highlighted) ? Breeze.hover : (selected ? Breeze.accentSubtle : "transparent")
                        border.width: selected ? 1 : 0
                        border.color: Breeze.accentBorder

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 12

                            // Mini desktop preview in the theme's own colors
                            Rectangle {
                                Layout.preferredWidth: 128
                                Layout.fillHeight: true
                                radius: 3
                                color: card.modelData.bg
                                border.width: 1
                                border.color: Breeze.buttonBorder
                                clip: true

                                // Window with titlebar
                                Rectangle {
                                    x: 16; y: card.modelData.panelPos === "top" ? 16 : 8
                                    width: 70; height: 40
                                    radius: card.modelData.id === "retro" ? 0 : 3
                                    color: card.modelData.window
                                    border.width: card.modelData.id === "retro" ? 1 : 0
                                    border.color: card.modelData.accent
                                    Rectangle {
                                        width: parent.width; height: 9
                                        radius: parent.radius
                                        color: card.modelData.titlebar
                                    }
                                    Rectangle {
                                        x: parent.width - 11; y: 2.5; width: 4; height: 4; radius: 2
                                        color: card.modelData.accent
                                    }
                                    Rectangle { x: 6; y: 16; width: 36; height: 3; radius: 1; color: card.modelData.accent; opacity: 0.8 }
                                    Rectangle { x: 6; y: 23; width: 50; height: 2; radius: 1; color: "#80ffffff"; opacity: 0.35 }
                                    Rectangle { x: 6; y: 29; width: 42; height: 2; radius: 1; color: "#80ffffff"; opacity: 0.35 }
                                }
                                // Second, smaller window
                                Rectangle {
                                    x: 60; y: card.modelData.panelPos === "top" ? 30 : 22
                                    width: 56; height: 32
                                    radius: card.modelData.id === "retro" ? 0 : 3
                                    color: card.modelData.window
                                    border.width: 1
                                    border.color: card.modelData.id === "retro" ? card.modelData.accent : card.modelData.titlebar
                                    Rectangle { width: parent.width; height: 8; radius: parent.radius; color: card.modelData.titlebar }
                                }
                                // Panel
                                Rectangle {
                                    readonly property bool floating: card.modelData.panelPos === "floating"
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    y: card.modelData.panelPos === "top" ? 0 : parent.height - height - (floating ? 4 : 0)
                                    width: floating ? parent.width - 40 : parent.width
                                    height: 10
                                    radius: floating ? 5 : 0
                                    color: card.modelData.panel
                                    Row {
                                        anchors.verticalCenter: parent.verticalCenter
                                        anchors.left: parent.left
                                        anchors.leftMargin: 4
                                        spacing: 3
                                        Rectangle { width: 5; height: 5; radius: 2.5; color: card.modelData.accent }
                                        Rectangle { width: 5; height: 5; radius: 1; color: "#80ffffff"; opacity: 0.5 }
                                        Rectangle { width: 5; height: 5; radius: 1; color: "#80ffffff"; opacity: 0.5 }
                                    }
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.alignment: Qt.AlignVCenter
                                spacing: 2
                                Text {
                                    Layout.fillWidth: true
                                    text: card.modelData.title
                                    elide: Text.ElideRight
                                    color: Breeze.text
                                    font.family: Breeze.fontFamily
                                    font.pixelSize: 14
                                    font.weight: Font.DemiBold
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: card.modelData.subtitle
                                    wrapMode: Text.WordWrap
                                    color: Breeze.textMuted
                                    font.family: Breeze.fontFamily
                                    font.pixelSize: 12
                                }
                            }

                            // Check mark for the active theme
                            Rectangle {
                                Layout.alignment: Qt.AlignVCenter
                                Layout.preferredWidth: 20
                                Layout.preferredHeight: 20
                                radius: 10
                                visible: card.selected
                                color: Breeze.accent
                                Text {
                                    anchors.centerIn: parent
                                    text: "✓"
                                    color: "#232629"
                                    font.pixelSize: 13
                                    font.bold: true
                                }
                            }
                        }

                        MouseArea {
                            id: area
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onContainsMouseChanged: if (containsMouse) root.highlighted = card.index
                            onClicked: root.apply(card.modelData.id)
                        }
                    }
                }
            }

            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Breeze.border }
            Text {
                Layout.fillWidth: true
                Layout.preferredHeight: 28
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                text: "Clic derecho en el botón: alternar al siguiente tema"
                color: Breeze.textMuted
                font.family: Breeze.fontFamily
                font.pixelSize: 11
            }
        }
    }
}
