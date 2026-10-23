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

/**
 * KDE Plasma 6 Notifications applet recreated in Breeze Dark.
 * - Opened from the bell in the Plasma taskbar tray, anchored above it.
 * - Header: "Do not disturb" switch and "Clear all".
 * - Notification history, newest first: app icon, app name, relative time,
 *   summary, body, action buttons and a close button per notification.
 * - Opening it marks everything as read and hides the on-screen popups.
 * - IPC: quickshell -c ii ipc call plasmaNotifications toggle|open|close
 */
Scope {
    id: root

    readonly property bool opened: GlobalStates.plasmaNotificationsOpen
    readonly property var notifications: [...Notifications.list].reverse()
    property real now: Date.now()

    function icon(name) {
        return Breeze.icon("notifications", name);
    }

    function open() {
        GlobalStates.plasmaNotificationsOpen = true;
    }
    function close() {
        GlobalStates.plasmaNotificationsOpen = false;
    }
    function toggle() {
        GlobalStates.plasmaNotificationsOpen = !GlobalStates.plasmaNotificationsOpen;
    }

    function relativeTime(time) {
        const minutes = Math.floor((root.now - time) / 60000);
        if (minutes < 1) return "Ahora";
        if (minutes < 60) return `Hace ${minutes} min`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `Hace ${hours} h`;
        return Qt.locale("es_ES").toString(new Date(time), "d MMM, HH:mm");
    }

    onOpenedChanged: {
        if (opened) {
            root.now = Date.now();
            Notifications.timeoutAll();
            Notifications.markAllRead();
        }
    }

    Timer {
        interval: 30000
        repeat: true
        running: root.opened
        onTriggered: root.now = Date.now()
    }

    IpcHandler {
        target: "plasmaNotifications"
        function toggle(): void { root.toggle(); }
        function open(): void { root.open(); }
        function close(): void { root.close(); }
    }

    component NotificationItem: Rectangle {
        id: item
        required property var modelData
        readonly property var notif: modelData
        readonly property bool hovered: itemMouse.containsMouse || closeBtn.containsMouse

        Layout.fillWidth: true
        implicitHeight: col.implicitHeight + 16
        radius: 4
        color: item.hovered ? Breeze.hover : "transparent"
        border.width: item.hovered ? 1 : 0
        border.color: Breeze.accentBorder

        MouseArea {
            id: itemMouse
            anchors.fill: parent
            hoverEnabled: true
        }

        ColumnLayout {
            id: col
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
                margins: 8
            }
            spacing: 4

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                IconImage {
                    implicitSize: 16
                    source: Quickshell.iconPath(item.notif.appIcon || item.notif.appName.toLowerCase(), true)
                        || root.icon("preferences-desktop-notification-bell")
                }
                Text {
                    Layout.fillWidth: true
                    text: item.notif.appName || "Notificación"
                    elide: Text.ElideRight
                    color: Breeze.textMuted
                    font.family: Breeze.fontFamily
                    font.pixelSize: 11
                }
                Text {
                    text: root.relativeTime(item.notif.time)
                    color: Breeze.textMuted
                    font.family: Breeze.fontFamily
                    font.pixelSize: 11
                }
                BreezeToolButton {
                    id: closeBtn
                    implicitWidth: 22
                    implicitHeight: 22
                    iconSource: root.icon("window-close")
                    onClicked: Notifications.discardNotification(item.notif.notificationId)
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Image {
                    // Images of notifications restored from history are gone after a restart
                    visible: item.notif.image.length > 0 && status !== Image.Error
                    Layout.preferredWidth: 48
                    Layout.preferredHeight: 48
                    Layout.alignment: Qt.AlignTop
                    fillMode: Image.PreserveAspectCrop
                    source: item.notif.image
                    sourceSize: Qt.size(96, 96)
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Text {
                        Layout.fillWidth: true
                        text: item.notif.summary
                        textFormat: Text.PlainText
                        wrapMode: Text.Wrap
                        maximumLineCount: 2
                        elide: Text.ElideRight
                        color: Breeze.text
                        font.family: Breeze.fontFamily
                        font.pixelSize: 13
                        font.weight: Font.DemiBold
                    }
                    Text {
                        visible: text.length > 0
                        Layout.fillWidth: true
                        text: item.notif.body
                        textFormat: Text.StyledText
                        wrapMode: Text.Wrap
                        maximumLineCount: 4
                        elide: Text.ElideRight
                        color: Breeze.text
                        opacity: 0.85
                        font.family: Breeze.fontFamily
                        font.pixelSize: 12
                        onLinkActivated: link => Qt.openUrlExternally(link)
                    }
                }
            }

            Flow {
                visible: item.notif.actions.length > 0
                Layout.fillWidth: true
                Layout.topMargin: 2
                spacing: 6
                Repeater {
                    model: item.notif.actions
                    delegate: BreezeButton {
                        required property var modelData
                        label: modelData.text
                        onClicked: Notifications.attemptInvokeAction(item.notif.notificationId, modelData.identifier)
                    }
                }
            }
        }
    }

    BreezePopupWindow {
        opened: root.opened
        anchorX: GlobalStates.plasmaNotificationsAnchorX
        screenName: GlobalStates.plasmaNotificationsScreen
        namespace: "quickshell:plasmaNotifications"
        popupWidth: 400
        popupHeight: 480
        onCloseRequested: root.close()

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 1
            spacing: 0

            BreezeHeader {
                BreezeSwitch {
                    checked: Notifications.silent
                    onToggled: Notifications.silent = !Notifications.silent
                }
                Image {
                    Layout.preferredWidth: 16
                    Layout.preferredHeight: 16
                    sourceSize: Qt.size(16, 16)
                    source: root.icon(Notifications.silent ? "notifications-disabled" : "notifications")
                }
                Text {
                    Layout.fillWidth: true
                    text: "No molestar"
                    color: Breeze.text
                    font.family: Breeze.fontFamily
                    font.pixelSize: 12
                }
                BreezeToolButton {
                    enabled: Notifications.list.length > 0
                    iconSource: root.icon("edit-clear-history")
                    label: "Borrar todo"
                    onClicked: Notifications.discardAllNotifications()
                }
            }

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                BreezePlaceholder {
                    anchors.centerIn: parent
                    visible: root.notifications.length === 0
                    iconSource: root.icon("notification-empty")
                    text: Notifications.silent ? "No hay notificaciones nuevas.\nNo molestar está activado." : "No hay notificaciones nuevas"
                }

                Flickable {
                    id: flick
                    anchors.fill: parent
                    anchors.margins: 6
                    visible: root.notifications.length > 0
                    contentHeight: listCol.implicitHeight
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds

                    ColumnLayout {
                        id: listCol
                        width: flick.width
                        spacing: 2

                        Repeater {
                            model: ScriptModel {
                                objectProp: "notificationId"
                                values: root.notifications
                            }
                            delegate: NotificationItem {}
                        }
                    }
                }
            }
        }
    }
}
