import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Widgets
import Quickshell.Io
import Quickshell.Hyprland
import Quickshell.Bluetooth
import Quickshell.Services.UPower
import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.common.models
import qs.modules.ii.plasmaCommon

Item {
    id: root

    property var screen: root.QsWindow.window?.screen
    readonly property HyprlandMonitor monitor: Hyprland.monitorFor(screen)

    // -----------------------------------------------------------------
    // KDE Plasma Breeze Dark Palette (Fixed, independent of wallpaper)
    // -----------------------------------------------------------------
    // Panel style (Settings > Barra de tareas): translucent/opaque, optional floating
    readonly property string panelStyle: Config.options?.bar?.plasma?.style ?? "translucent"
    // Floating panel docks while a window is maximized on this screen (Plasma 6 behaviour)
    readonly property bool floating: PlasmaPanelState.active && !PlasmaPanelState.isDocked(root.screen?.name ?? "")
    readonly property int floatingGap: floating ? Appearance.sizes.plasmaFloatingGap : 0
    readonly property int panelRadius: floating ? 18 : 0

    readonly property color colPanelBase: Config.options?.bar?.plasma?.color || "#24292e"
    readonly property color colPanelBg: Qt.rgba(colPanelBase.r, colPanelBase.g, colPanelBase.b,
        panelStyle === "opaque" ? 1 : (Config.options?.bar?.plasma?.opacity ?? 0.91))
    readonly property color colPanelBorder: "#31363b"
    readonly property color colAccent: "#3daee9"
    readonly property color colAccentHover: "#4fc3f7"
    readonly property color colAccentSubtle: "#283daee9"
    readonly property color colText: "#eff0f1"
    readonly property color colTextMuted: "#bdc3c7"
    readonly property color colHover: "#1affffff"
    readonly property color colActive: "#2e3daee9"
    readonly property color colDivider: "#383d44"

    // Opens one of the Plasma applet popups anchored above `button`
    // (only one applet popup open at a time, like Plasma)
    function togglePopup(name, button) {
        const wasOpen = GlobalStates[name + "Open"];
        for (const other of ["plasmaBluetooth", "plasmaNetwork", "plasmaCalendar", "plasmaNotifications"])
            GlobalStates[other + "Open"] = false;
        if (wasOpen) return;
        GlobalStates[name + "AnchorX"] = button.mapToItem(null, button.width / 2, 0).x;
        GlobalStates[name + "Screen"] = root.screen?.name ?? "";
        GlobalStates[name + "Open"] = true;
    }

    // The panel itself: full width docked to the bottom edge, or inset with rounded
    // corners when floating (like Plasma's floating panel)
    Item {
        id: panel
        // Animated like Plasma when the panel floats / docks
        property real gap: root.floatingGap
        Behavior on gap {
            NumberAnimation { duration: 220; easing.type: Easing.OutCubic }
        }
        // Fixed thickness: docking only removes the side/bottom gaps (no vertical growth)
        height: Appearance.sizes.plasmaPanelHeight
        readonly property bool atBottom: Config.options?.bar?.bottom ?? true
        anchors {
            left: parent.left
            right: parent.right
            bottom: panel.atBottom ? parent.bottom : undefined
            top: panel.atBottom ? undefined : parent.top
            leftMargin: panel.gap
            rightMargin: panel.gap
            bottomMargin: panel.gap
            topMargin: panel.gap
        }

        Rectangle {
            anchors.fill: parent
            color: root.colPanelBg
            radius: root.panelRadius
            Behavior on radius {
                NumberAnimation { duration: 220; easing.type: Easing.OutCubic }
            }
            border.width: root.floating ? 1 : 0
            border.color: root.colPanelBorder

            // Authentic KDE Plasma top separator border (docked panel)
            Rectangle {
                visible: !root.floating
                anchors {
                    top: parent.top
                    left: parent.left
                    right: parent.right
                }
                height: 1
                color: root.colPanelBorder
            }
        }

        // Main Layout across full width
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 4
            anchors.rightMargin: 0
            spacing: 2

            // =============================================================
            // 1. KDE Plasma Kickoff Launcher Button
            // =============================================================
            MouseArea {
                id: kickoffBtn
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredWidth: 40
                Layout.preferredHeight: 38
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor

                Rectangle {
                    anchors.fill: parent
                    radius: 4
                    color: kickoffBtn.containsPress ? root.colActive : (kickoffBtn.containsMouse ? root.colHover : "transparent")
                    border.width: (kickoffBtn.containsMouse || kickoffBtn.containsPress) ? 1 : 0
                    border.color: kickoffBtn.containsPress ? root.colAccent : "#333daee9"

                    Behavior on color {
                        ColorAnimation { duration: 120 }
                    }

                    Image {
                        id: kickoffLogo
                        anchors.centerIn: parent
                        width: 24
                        height: 24
                        source: "file:///home/sasel/.config/quickshell/ii/assets/plasma-logo.svg"
                        fillMode: Image.PreserveAspectFit
                        smooth: true
                    }
                }

                onClicked: {
                    Quickshell.execDetached(["/home/sasel/.config/hypr/scripts/app-launcher.sh"]);
                }
            }

            // Pushes the task manager to the exact horizontal center of the panel when
            // "centered icons" is enabled
            Item {
                visible: Config.options?.bar?.plasma?.centerTasks ?? false
                Layout.fillHeight: true
                Layout.preferredWidth: Math.max(0, panel.width / 2 - taskManagerList.width / 2 - kickoffBtn.width - 4 - 2 * 2)
            }

            // =============================================================
            // 2. Task Manager (Running windows & Pinned applications)
            // =============================================================
            ListView {
                id: taskManagerList
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredHeight: 38
                Layout.fillWidth: false
                implicitWidth: contentWidth
                orientation: ListView.Horizontal
                spacing: 2
                clip: true
                interactive: false

                model: ScriptModel {
                    objectProp: "appId"
                    values: TaskbarApps.apps.filter(app => app.appId !== "SEPARATOR")
                }

                delegate: MouseArea {
                    id: taskItem
                    required property var modelData
                    readonly property bool hasWindows: modelData.toplevels.length > 0
                    readonly property bool isActive: modelData.toplevels.some(t => t.activated)
                    property var desktopEntry: DesktopEntries.heuristicLookup(modelData.appId)
                    property int lastFocusedIdx: 0

                    width: 44
                    height: 38
                    hoverEnabled: true
                    acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
                    cursorShape: Qt.PointingHandCursor

                    Rectangle {
                        anchors.fill: parent
                        radius: 4
                        color: taskItem.isActive ? root.colActive : (taskItem.containsMouse ? root.colHover : "transparent")
                        border.width: (taskItem.isActive || taskItem.containsMouse) ? 1 : 0
                        border.color: taskItem.isActive ? "#403daee9" : (taskItem.containsMouse ? "#20ffffff" : "transparent")

                        Behavior on color {
                            ColorAnimation { duration: 120 }
                        }

                        IconImage {
                            anchors.centerIn: parent
                            implicitSize: 24
                            source: taskItem.desktopEntry?.icon ? Quickshell.iconPath(taskItem.desktopEntry.icon, "application-x-executable") : Quickshell.iconPath(AppSearch.guessIcon(taskItem.modelData.appId), "application-x-executable")
                        }

                        // Authentic KDE Plasma Active / Running Underline Indicator
                        Rectangle {
                            anchors.bottom: parent.bottom
                            anchors.bottomMargin: 1
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: taskItem.isActive ? 22 : (taskItem.hasWindows ? 12 : 0)
                            height: taskItem.isActive ? 3 : 2
                            radius: 1.5
                            color: taskItem.isActive ? root.colAccent : "#7f8c8d"
                            visible: taskItem.hasWindows

                            Behavior on width {
                                NumberAnimation { duration: 150; easing.type: Easing.OutQuad }
                            }
                        }
                    }

                    onClicked: mouse => {
                        if (mouse.button === Qt.LeftButton) {
                            if (taskItem.hasWindows) {
                                if (taskItem.isActive && taskItem.modelData.toplevels.length > 1) {
                                    taskItem.lastFocusedIdx = (taskItem.lastFocusedIdx + 1) % taskItem.modelData.toplevels.length;
                                    taskItem.modelData.toplevels[taskItem.lastFocusedIdx].activate();
                                } else {
                                    Quickshell.execDetached(["/home/sasel/.config/hypr/scripts/toggle-minimize.py", "toggle-app", taskItem.modelData.appId]);
                                }
                            } else if (taskItem.desktopEntry) {
                                taskItem.desktopEntry.execute();
                            }
                        } else if (mouse.button === Qt.RightButton) {
                            if (taskItem.hasWindows) {
                                taskItem.modelData.toplevels[0].close();
                            } else {
                                TaskbarApps.togglePin(taskItem.modelData.appId);
                            }
                        } else if (mouse.button === Qt.MiddleButton) {
                            if (taskItem.desktopEntry) {
                                taskItem.desktopEntry.execute();
                            }
                        }
                    }
                }
            }

            // =============================================================
            // 3. Central Spacer
            // =============================================================
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
            }

            // =============================================================
            // 4. System Tray
            // =============================================================
            SysTray {
                Layout.alignment: Qt.AlignVCenter
                Layout.fillHeight: true
                invertSide: true
                showSeparator: false
            }

            // =============================================================
            // 4b. Notifications (Plasma tray bell). Unread count in a badge when
            //     Settings > Barra de tareas > "mostrar número" is on, a dot otherwise
            // =============================================================
            MouseArea {
                id: notifBtn
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredHeight: 38
                Layout.preferredWidth: 32
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                readonly property int unread: Notifications.unread
                readonly property bool showCount: Config.options.bar.indicators.notifications.showUnreadCount
                readonly property bool popupOpen: GlobalStates.plasmaNotificationsOpen && GlobalStates.plasmaNotificationsScreen === (root.screen?.name ?? "")

                Rectangle {
                    anchors.fill: parent
                    radius: 4
                    color: notifBtn.popupOpen ? root.colActive : (notifBtn.containsMouse ? root.colHover : "transparent")
                    border.width: (notifBtn.containsMouse || notifBtn.popupOpen) ? 1 : 0
                    border.color: notifBtn.popupOpen ? "#403daee9" : "#20ffffff"

                    Image {
                        anchors.centerIn: parent
                        width: 22
                        height: 22
                        sourceSize: Qt.size(22, 22)
                        source: Breeze.icon("notifications", Notifications.silent ? "notifications-disabled"
                            : (notifBtn.unread > 0 ? "notification-active" : "notification-inactive"))
                    }

                    // Unread badge: number (option on) or dot (option off)
                    Rectangle {
                        visible: notifBtn.unread > 0 && !Notifications.silent
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.rightMargin: notifBtn.showCount ? 1 : 6
                        anchors.topMargin: notifBtn.showCount ? 5 : 9
                        width: notifBtn.showCount ? Math.max(16, countText.implicitWidth + 8) : 7
                        height: notifBtn.showCount ? 16 : 7
                        radius: height / 2
                        color: root.colAccent
                        Text {
                            id: countText
                            visible: notifBtn.showCount
                            anchors.centerIn: parent
                            text: notifBtn.unread > 99 ? "99+" : notifBtn.unread
                            color: "#fcfcfc"
                            font.family: Appearance.font.family.main
                            font.pixelSize: 10
                            font.weight: Font.Bold
                        }
                    }
                }

                // Left click: notifications applet. Middle click: toggle "Do not disturb" (like Plasma)
                onClicked: mouse => {
                    if (mouse.button === Qt.MiddleButton) {
                        Notifications.silent = !Notifications.silent;
                        return;
                    }
                    root.togglePopup("plasmaNotifications", notifBtn);
                }
            }

            // Vertical divider
            Rectangle {
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredWidth: 1
                Layout.preferredHeight: 20
                color: root.colDivider
            }

            // =============================================================
            // 5. Volume Widget (Icon + Percentage, Scroll adjust, Click mute)
            // =============================================================
            MouseArea {
                id: volBtn
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredHeight: 38
                implicitWidth: volRow.implicitWidth + 14
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor

                readonly property real currentVol: Audio.sink?.audio?.volume ?? 0.0
                readonly property bool isMuted: Audio.sink?.audio?.muted ?? false

                Rectangle {
                    anchors.fill: parent
                    radius: 4
                    color: volBtn.containsMouse ? root.colHover : "transparent"
                    border.width: volBtn.containsMouse ? 1 : 0
                    border.color: "#20ffffff"

                    RowLayout {
                        id: volRow
                        anchors.centerIn: parent
                        spacing: 4

                        MaterialSymbol {
                            iconSize: 18
                            color: volBtn.isMuted ? "#da4453" : root.colText
                            text: volBtn.isMuted ? "volume_off" : (volBtn.currentVol > 0.5 ? "volume_up" : (volBtn.currentVol > 0.0 ? "volume_down" : "volume_mute"))
                        }

                        Text {
                            font.family: Appearance.font.family.main
                            font.pixelSize: 11
                            font.weight: Font.DemiBold
                            color: volBtn.isMuted ? "#da4453" : root.colText
                            text: volBtn.isMuted ? "Mute" : `${Math.round(volBtn.currentVol * 100)}%`
                        }
                    }
                }

                onWheel: wheel => {
                    if (wheel.angleDelta.y > 0) {
                        Audio.incrementVolume();
                    } else if (wheel.angleDelta.y < 0) {
                        Audio.decrementVolume();
                    }
                }

                onClicked: {
                    if (Audio.sink?.audio) {
                        Audio.sink.audio.muted = !Audio.sink.audio.muted;
                    }
                }
            }

            // =============================================================
            // 6. Network Widget
            // =============================================================
            MouseArea {
                id: netBtn
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredHeight: 38
                Layout.preferredWidth: 32
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                readonly property bool popupOpen: GlobalStates.plasmaNetworkOpen && GlobalStates.plasmaNetworkScreen === (root.screen?.name ?? "")

                Rectangle {
                    anchors.fill: parent
                    radius: 4
                    color: netBtn.popupOpen ? root.colActive : (netBtn.containsMouse ? root.colHover : "transparent")
                    border.width: (netBtn.containsMouse || netBtn.popupOpen) ? 1 : 0
                    border.color: netBtn.popupOpen ? "#403daee9" : "#20ffffff"

                    MaterialSymbol {
                        anchors.centerIn: parent
                        iconSize: 18
                        color: root.colText
                        text: Network.materialSymbol
                    }
                }

                // Plasma Networks applet anchored above the button
                onClicked: root.togglePopup("plasmaNetwork", netBtn)
            }

            // =============================================================
            // 7. Bluetooth Widget (Visible if available)
            // =============================================================
            MouseArea {
                id: btBtn
                visible: BluetoothStatus.available
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredHeight: 38
                Layout.preferredWidth: 32
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                readonly property bool popupOpen: GlobalStates.plasmaBluetoothOpen && GlobalStates.plasmaBluetoothScreen === (root.screen?.name ?? "")

                Rectangle {
                    anchors.fill: parent
                    radius: 4
                    color: btBtn.popupOpen ? root.colActive : (btBtn.containsMouse ? root.colHover : "transparent")
                    border.width: (btBtn.containsMouse || btBtn.popupOpen) ? 1 : 0
                    border.color: btBtn.popupOpen ? "#403daee9" : "#20ffffff"

                    MaterialSymbol {
                        anchors.centerIn: parent
                        iconSize: 18
                        color: BluetoothStatus.connected ? root.colAccent : root.colText
                        text: BluetoothStatus.connected ? "bluetooth_connected" : (BluetoothStatus.enabled ? "bluetooth" : "bluetooth_disabled")
                    }
                }

                // Left click: Plasma Bluetooth applet. Middle click: toggle power (like Plasma).
                onClicked: mouse => {
                    if (mouse.button === Qt.MiddleButton) {
                        if (Bluetooth.defaultAdapter)
                            Bluetooth.defaultAdapter.enabled = !Bluetooth.defaultAdapter.enabled;
                        return;
                    }
                    root.togglePopup("plasmaBluetooth", btBtn);
                }
            }

            // =============================================================
            // 8. Battery Widget (Visible if battery is present)
            // =============================================================
            MouseArea {
                id: batBtn
                visible: Battery.available
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredHeight: 38
                implicitWidth: batRow.implicitWidth + 10
                hoverEnabled: true

                Rectangle {
                    anchors.fill: parent
                    radius: 4
                    color: batBtn.containsMouse ? root.colHover : "transparent"
                    border.width: batBtn.containsMouse ? 1 : 0
                    border.color: "#20ffffff"

                    RowLayout {
                        id: batRow
                        anchors.centerIn: parent
                        spacing: 3

                        MaterialSymbol {
                            iconSize: 18
                            color: Battery.charging ? root.colAccent : (Battery.percentage <= 15 ? "#da4453" : root.colText)
                            text: Battery.charging ? "battery_charging_full" : (Battery.percentage > 80 ? "battery_full" : (Battery.percentage > 30 ? "battery_std" : "battery_alert"))
                        }

                        Text {
                            font.family: Appearance.font.family.main
                            font.pixelSize: 11
                            color: root.colText
                            text: `${Math.round(Battery.percentage)}%`
                        }
                    }
                }
            }

            // =============================================================
            // 9. Theme Switcher (Cycle / Rofi Picker)
            // =============================================================
            MouseArea {
                id: themeSwitcherBtn
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredHeight: 38
                Layout.preferredWidth: 32
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                acceptedButtons: Qt.LeftButton | Qt.RightButton

                Rectangle {
                    anchors.fill: parent
                    radius: 4
                    color: themeSwitcherBtn.containsMouse ? root.colHover : "transparent"
                    border.width: themeSwitcherBtn.containsMouse ? 1 : 0
                    border.color: "#20ffffff"

                    MaterialSymbol {
                        anchors.centerIn: parent
                        iconSize: 18
                        color: root.colAccent
                        text: "palette"
                    }
                }

                onClicked: mouse => {
                    if (mouse.button === Qt.RightButton) {
                        Quickshell.execDetached(["/home/sasel/.config/hypr/scripts/bwm-theme-manager.py", "toggle"]);
                    } else {
                        Quickshell.execDetached(["/home/sasel/.config/hypr/scripts/theme-picker.sh"]);
                    }
                }
            }

            // Vertical divider
            Rectangle {
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredWidth: 1
                Layout.preferredHeight: 20
                color: root.colDivider
            }

            // =============================================================
            // 10. Authentic KDE Plasma 2-Line Digital Clock
            // =============================================================
            MouseArea {
                id: clockBtn
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredHeight: 38
                implicitWidth: clockCol.implicitWidth + 16
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor

                Rectangle {
                    anchors.fill: parent
                    radius: 4
                    color: clockBtn.containsMouse ? root.colHover : "transparent"
                    border.width: clockBtn.containsMouse ? 1 : 0
                    border.color: "#20ffffff"

                    ColumnLayout {
                        id: clockCol
                        anchors.centerIn: parent
                        spacing: 0

                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            font.family: Appearance.font.family.main
                            font.pixelSize: 12
                            font.weight: Font.Bold
                            color: root.colText
                            text: DateTime.time
                        }

                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            font.family: Appearance.font.family.main
                            font.pixelSize: 10
                            font.weight: Font.Normal
                            color: root.colTextMuted
                            text: DateTime.shortDate
                        }
                    }
                }

                // Plasma digital clock popup: calendar anchored above the clock
                onClicked: root.togglePopup("plasmaCalendar", clockBtn)
            }

            // =============================================================
            // 11. KDE Plasma "Show Desktop": square strip spanning the whole panel height
            //     at the far right edge. Inside a floating panel it is cut with the same
            //     curve as the panel, so it never sticks out of the rounded corners.
            // =============================================================
            MouseArea {
                id: showDesktopBtn
                Layout.fillHeight: true
                Layout.preferredWidth: 8
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                clip: true
                readonly property bool active: PlasmaPanelState.showingDesktop

                // Wider than the button and shifted left: only its right side (rounded
                // like the panel) stays inside the clipped area. 2x the radius wide so
                // the radius is not clamped and the curve matches the panel exactly
                Rectangle {
                    x: -2 * root.panelRadius
                    width: parent.width + 2 * root.panelRadius
                    height: parent.height
                    radius: root.panelRadius
                    color: (showDesktopBtn.containsMouse || showDesktopBtn.active) ? root.colAccent : root.colPanelBorder

                    Behavior on color {
                        ColorAnimation { duration: 150 }
                    }
                }

                // Minimizes every window (or brings them back), like Plasma
                onClicked: PlasmaPanelState.toggleShowDesktop()
            }
        }
    }
}
