pragma Singleton
pragma ComponentBehavior: Bound

import qs.modules.common
import qs.modules.common.functions
import qs
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Services.Notifications

/**
 * Provides extra features not in Quickshell.Services.Notifications:
 *  - Persistent storage
 *  - Popup notifications, with timeout
 *  - Notification groups by app
 */
Singleton {
	id: root
    component Notif: QtObject {
        id: wrapper
        required property int notificationId // Could just be `id` but it conflicts with the default prop in QtObject
        property Notification notification
        property list<var> actions: notification?.actions.map((action) => ({
            "identifier": action.identifier,
            "text": action.text,
        })) ?? []
        property bool popup: false
        property bool isTransient: notification?.hints.transient ?? false
        property string appIcon: notification?.appIcon ?? ""
        property string appName: notification?.appName ?? ""
        property string body: notification?.body ?? ""
        property string image: notification?.image ?? ""
        property bool hasInlineReply: notification?.hasInlineReply ?? false
        property string inlineReplyPlaceholder: notification?.inlineReplyPlaceholder ?? ""
        property string summary: notification?.summary ?? ""
        property double time
        property string urgency: notification?.urgency.toString() ?? "normal"
        property Timer timer

        onNotificationChanged: {
            if (notification === null) {
                root.discardNotification(notificationId);
            }
        }
    }

    function notifToJSON(notif) {
        return {
            "notificationId": notif.notificationId,
            "actions": notif.actions,
            "appIcon": notif.appIcon,
            "appName": notif.appName,
            "body": notif.body,
            "image": notif.image,
            "summary": notif.summary,
            "time": notif.time,
            "urgency": notif.urgency,
        }
    }
    function notifToString(notif) {
        return JSON.stringify(notifToJSON(notif), null, 2);
    }

    component NotifTimer: Timer {
        required property int notificationId
        interval: 7000
        running: true
        onTriggered: () => {
            const index = root.list.findIndex((notif) => notif.notificationId === notificationId);
            const notifObject = root.list[index];
            print("[Notifications] Notification timer triggered for ID: " + notificationId + ", transient: " + notifObject?.isTransient);
            if (!notifObject) { destroy(); return; } // BWM: dismissed while timer was queued
            if (notifObject.isTransient) root.discardNotification(notificationId);
            else root.timeoutNotification(notificationId);
            destroy()
        }
    }

    property bool silent: false
    property double silentUntil: 0 // Unix epoch ms; 0 = until manually disabled
    property bool _syncingDndFromHost: false
    onSilentChanged: {
        if (!silent) silentUntil = 0;
        if (!root._syncingDndFromHost && root.nativePlasmaHostActive && root.nativeHostReady) {
            hostDndSetter.apply(root.silent);
        }
    }
    function setSilentFor(minutes) {
        const mins = Number(minutes) || 0;
        if (mins <= 0) {
            silentUntil = 0;
            silent = true;
            return;
        }
        silentUntil = Date.now() + mins * 60000;
        silent = true;
    }
    function clearSilentUntil() { silentUntil = 0; }
    Timer {
        id: silentExpiryTimer
        interval: 15000
        repeat: true
        running: root.silent && root.silentUntil > 0
        onTriggered: {
            if (Date.now() >= root.silentUntil) {
                root.silentUntil = 0;
                root.silent = false;
            }
        }
    }
    property int unread: 0
    property var filePath: Directories.notificationsPath
    property list<Notif> list: []
    property var popupList: list.filter((notif) => notif.popup);
    property bool popupInhibited: (GlobalStates?.sidebarRightOpen ?? false) || (GlobalStates?.plasmaNotificationsOpen ?? false) || silent
    property var latestTimeForApp: ({})
    Component {
        id: notifComponent
        Notif {}
    }
    Component {
        id: notifTimerComponent
        NotifTimer {}
    }

    function stringifyList(list) {
        return JSON.stringify(list.map((notif) => notifToJSON(notif)), null, 2);
    }
    
    onListChanged: {
        // Update latest time for each app
        root.list.forEach((notif) => {
            if (!root.latestTimeForApp[notif.appName] || notif.time > root.latestTimeForApp[notif.appName]) {
                root.latestTimeForApp[notif.appName] = Math.max(root.latestTimeForApp[notif.appName] || 0, notif.time);
            }
        });
        // Remove apps that no longer have notifications
        Object.keys(root.latestTimeForApp).forEach((appName) => {
            if (!root.list.some((notif) => notif.appName === appName)) {
                delete root.latestTimeForApp[appName];
            }
        });
    }

    function appNameListForGroups(groups) {
        return Object.keys(groups).sort((a, b) => {
            // Sort by time, descending
            return groups[b].time - groups[a].time;
        });
    }

    function groupsForList(list) {
        const groups = {};
        list.forEach((notif) => {
            if (!groups[notif.appName]) {
                groups[notif.appName] = {
                    appName: notif.appName,
                    appIcon: notif.appIcon,
                    notifications: [],
                    time: 0
                };
            }
            groups[notif.appName].notifications.push(notif);
            // Always set to the latest time in the group
            groups[notif.appName].time = latestTimeForApp[notif.appName] || notif.time;
        });
        return groups;
    }

    property var groupsByAppName: groupsForList(root.list)
    property var popupGroupsByAppName: groupsForList(root.popupList)
    property list<string> appNameList: appNameListForGroups(root.groupsByAppName)
    property list<string> popupAppNameList: appNameListForGroups(root.popupGroupsByAppName)

    // Quickshell's notification IDs starts at 1 on each run, while saved notifications
    // can already contain higher IDs. This is for avoiding id collisions
    property int idOffset
    signal initDone();
    signal notify(notification: var);
    signal discard(id: int);
    signal discardAll();
    signal timeout(id: var);

    // The D-Bus notification server ("notifications" in each skin.json).
    // Breeze: native bwm-plasma-host owns org.freedesktop.Notifications (NotificationManager::Server);
    // this server only activates as fallback if bar.plasma.nativeHost is false or the host stops.
    // Default: swaync, this one only if swaync is not installed.
    // Retro: Omarchy's own service (modules/ii/omarchyNotifications) for its toasts, glyphs and
    // actions. Only one server can hold org.freedesktop.Notifications; bwm-theme-manager.py /
    // plasma-host.py coordinate handoff cleanly. Waits for config, swaync and native-host checks
    // so it never grabs the name before knowing the active owner.
    property bool swayncChecked: false
    property bool swayncInstalled: false
    readonly property string _nativeHostHelper: FileUtils.trimFileProtocol(Quickshell.shellPath("../..")) + "/hypr/skins/plasma/scripts/plasma-host.py"
    readonly property string _dndStateFile: (Quickshell.env("XDG_RUNTIME_DIR") || "/tmp") + "/bwm-plasma-dnd"
    property bool nativeHostChecked: false
    property bool nativeHostReady: false
    property bool _nativeHostClaiming: false
    readonly property bool nativePlasmaHostActive: Appearance.isPlasma && (Config.options?.bar?.plasma?.nativeHost ?? true) && (nativeHostReady || _nativeHostClaiming)

    function updateNativeHostReady(ready) {
        root.nativeHostReady = Boolean(ready);
        root.nativeHostChecked = true;
        if (ready) {
            root._nativeHostClaiming = false;
            nativeHostClaimTimer.stop();
            hostDndFileView.reload();
        }
    }

    Timer {
        id: nativeHostClaimTimer
        interval: 6000
        repeat: false
        onTriggered: {
            root._nativeHostClaiming = false;
        }
    }
    Process {
        running: true
        command: ["sh", "-c", "command -v swaync"]
        onExited: exitCode => { root.swayncInstalled = exitCode === 0; root.swayncChecked = true; }
    }
    Process {
        running: true
        command: ["python3", root._nativeHostHelper, "ready"]
        onExited: exitCode => { root.updateNativeHostReady(exitCode === 0); }
    }
    Process {
        id: hostDndSetter
        property string pendingState: ""
        function apply(enabled) {
            pendingState = enabled ? "true" : "false";
            if (running) return;
            command = ["python3", root._nativeHostHelper, "dnd-set", pendingState];
            running = true;
        }
        onExited: {
            const sent = command[3];
            if (pendingState && pendingState !== sent) {
                const next = pendingState;
                command = ["python3", root._nativeHostHelper, "dnd-set", next];
                running = true;
            }
        }
    }
    FileView {
        id: hostDndFileView
        path: root.nativePlasmaHostActive ? Qt.resolvedUrl(root._dndStateFile) : ""
        watchChanges: root.nativePlasmaHostActive
        onFileChanged: reload()
        onLoaded: {
            if (!root.nativePlasmaHostActive) return;
            const state = text().trim() === "true";
            if (root.silent !== state) {
                root._syncingDndFromHost = true;
                root.silent = state;
                root._syncingDndFromHost = false;
            }
        }
    }
    readonly property var trackedValues: serverLoader.item ? serverLoader.item.trackedNotifications.values : []
    LazyLoader {
        id: serverLoader
        active: Config.ready && root.swayncChecked && root.nativeHostChecked && (
            (Appearance.isPlasma && !root.nativePlasmaHostActive) ||
            (!Appearance.isRetro && !Appearance.isPlasma && !root.swayncInstalled)
        )

	NotificationServer {
        id: notifServer
        // actionIconsSupported: true
        actionsSupported: true
        bodyHyperlinksSupported: true
        bodyImagesSupported: true
        bodyMarkupSupported: true
        bodySupported: true
        imageSupported: true
        // Only Breeze shows Plasma's reply field; elsewhere apps keep their own "Reply" actions.
        inlineReplySupported: Appearance.isPlasma
        keepOnReload: false
        persistenceSupported: true

        onNotification: (notification) => {
            notification.tracked = true
            const newNotifObject = notifComponent.createObject(root, {
                "notificationId": notification.id + root.idOffset,
                "notification": notification,
                "time": Date.now(),
            });
			root.list = [...root.list, newNotifObject];

            // Popup
            if (!root.popupInhibited) {
                newNotifObject.popup = true;
                if (notification.expireTimeout != 0) {
                    newNotifObject.timer = notifTimerComponent.createObject(root, {
                        "notificationId": newNotifObject.notificationId,
                        "interval": notification.expireTimeout < 0 ? (Config?.options.notifications.timeout ?? 7000) : notification.expireTimeout,
                    });
                }
                root.unread++;
            }
            root.notify(newNotifObject);
            // console.log(notifToString(newNotifObject));
            notifFileView.setText(stringifyList(root.list));
        }
    }
    }

    function markAllRead() {
        root.unread = 0;
    }

    function discardNotification(id) {
        console.log("[Notifications] Discarding notification with ID: " + id);
        const index = root.list.findIndex((notif) => notif.notificationId === id);
        const notifServerIndex = root.trackedValues.findIndex((notif) => notif.id + root.idOffset === id);
        if (index !== -1) {
            root.list.splice(index, 1);
            notifFileView.setText(stringifyList(root.list));
            triggerListChange()
        }
        if (notifServerIndex !== -1) {
            root.trackedValues[notifServerIndex].dismiss()
        }
        root.discard(id); // Emit signal
    }

    function discardAllNotifications() {
        root.list = []
        triggerListChange()
        notifFileView.setText(stringifyList(root.list));
        root.trackedValues.forEach((notif) => {
            notif.dismiss()
        })
        root.discardAll();
    }

    function sendInlineReply(id, text) {
        const notif = root.list.find((n) => n.notificationId === id);
        if (!notif?.notification?.hasInlineReply || !text)
            return false;
        notif.notification.sendInlineReply(text);
        root.discardNotification(id);
        return true;
    }

    function cancelTimeout(id) {
        const index = root.list.findIndex((notif) => notif.notificationId === id);
        if (root.list[index] != null)
            root.list[index].timer?.stop();
    }

    function timeoutNotification(id) {
        const index = root.list.findIndex((notif) => notif.notificationId === id);
        if (root.list[index] != null)
            root.list[index].popup = false;
        root.timeout(id);
    }

    function timeoutAll() {
        root.popupList.forEach((notif) => {
            root.timeout(notif.notificationId);
        })
        root.popupList.forEach((notif) => {
            notif.popup = false;
        });
    }

    function attemptInvokeAction(id, notifIdentifier) {
        console.log("[Notifications] Attempting to invoke action with identifier: " + notifIdentifier + " for notification ID: " + id);
        const notifServerIndex = root.trackedValues.findIndex((notif) => notif.id + root.idOffset === id);
        console.log("Notification server index: " + notifServerIndex);
        if (notifServerIndex !== -1) {
            const notifServerNotif = root.trackedValues[notifServerIndex];
            const action = notifServerNotif.actions.find((action) => action.identifier === notifIdentifier);
            // console.log("Action found: " + JSON.stringify(action));
            action?.invoke()
        } 
        else {
            console.log("Notification not found in server: " + id)
        }
        root.discardNotification(id);
    }

    function triggerListChange() {
        root.list = root.list.slice(0)
    }

    function refresh() {
        notifFileView.reload()
    }

    Component.onCompleted: {
        refresh()
    }

    FileView {
        id: notifFileView
        path: Qt.resolvedUrl(filePath)
        onLoaded: {
            const fileContents = notifFileView.text()
            root.list = JSON.parse(fileContents).map((notif) => {
                return notifComponent.createObject(root, {
                    "notificationId": notif.notificationId,
                    "actions": [], // Notification actions are meaningless if they're not tracked by the server or the sender is dead
                    "appIcon": notif.appIcon,
                    "appName": notif.appName,
                    "body": notif.body,
                    "image": notif.image,
                    "summary": notif.summary,
                    "time": notif.time,
                    "urgency": notif.urgency,
                });
            });
            // Find largest notificationId
            let maxId = 0
            root.list.forEach((notif) => {
                maxId = Math.max(maxId, notif.notificationId)
            })

            console.log("[Notifications] File loaded")
            root.idOffset = maxId
            root.initDone()
        }
        onLoadFailed: (error) => {
            if(error == FileViewError.FileNotFound) {
                console.log("[Notifications] File not found, creating new file.")
                root.list = []
                notifFileView.setText(stringifyList(root.list));
            } else {
                console.log("[Notifications] Error loading file: " + error)
            }
        }
    }

    // BWM: shell-readable Do Not Disturb for the Retro menu's ✓ (and anything scripted),
    // plus native Plasma host handoff notifications.
    IpcHandler {
        target: "bwmNotifications"
        function toggleDnd(): void { root.silent = !root.silent; }
        function isDnd(): string { return root.silent ? "true" : "false"; }
        function setNativeHost(active: string): void {
            const enabled = (active === "true" || active === "1");
            if (enabled) {
                root._nativeHostClaiming = true;
                nativeHostClaimTimer.restart();
            } else {
                root._nativeHostClaiming = false;
                root.nativeHostReady = false;
                nativeHostClaimTimer.stop();
            }
            root.nativeHostChecked = true;
        }
    }
}
