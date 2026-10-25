pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import qs.services
import qs.modules.common

// Retro's notification daemon: Omarchy's own (Service.qml, from Omarchy's
// shell/plugins/notifications, MIT): grouped cards under the bar, Omarchy glyphs, inline
// actions (e.g. "Open" on a finished screen recording, sent by omarchy-notification-send),
// copyable codes, Do Not Disturb and history (~/.local/state/omarchy/notifications).
// Loaded only in Retro (panelFamilies/IllogicalImpulseFamily.qml); BWM's own server
// (services/Notifications.qml) steps aside there and comes back in the other themes.
Scope {
    id: root

    // What the service asks of omarchy-shell: where the bar is and how thick, to hang the
    // cards just below it
    QtObject {
        id: shellApi
        readonly property QtObject bar: QtObject {
            readonly property string position: (Config.options?.bar?.bottom ?? false) ? "bottom" : "top"
            readonly property int barSize: Appearance.sizes.baseBarHeight
            readonly property bool barHidden: false
        }
    }

    Service {
        id: service
        shell: shellApi
    }

    // One Do Not Disturb for the whole desktop: BWM's (Retro indicator, menu ✓, bwmNotifications
    // IPC) and Omarchy's (its cards, `notifications` IPC) follow each other
    Connections {
        target: Notifications
        function onSilentChanged() {
            if (service.doNotDisturb !== Notifications.silent)
                service.setDoNotDisturb(Notifications.silent);
        }
    }
    Connections {
        target: service
        function onDoNotDisturbChanged() {
            if (Notifications.silent !== service.doNotDisturb)
                Notifications.silent = service.doNotDisturb;
        }
    }
    Component.onCompleted: {
        if (Notifications.silent)
            service.setDoNotDisturb(true);
        else if (service.doNotDisturb)
            Notifications.silent = true;
    }
}
