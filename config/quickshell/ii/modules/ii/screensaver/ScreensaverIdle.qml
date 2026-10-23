import qs
import qs.services
import qs.modules.common
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

/**
 * Terminal screensaver on idle, like Omarchy's (hypridle -> omarchy-launch-screensaver).
 * After `screensaver.timeoutMinutes` without input it runs launch-screensaver.sh, and as
 * soon as there is input again it closes it (the terminals only see keys, not the mouse).
 * Honours the "keep awake" toggle and apps that inhibit idle (video players...).
 * IPC: quickshell -c ii ipc call screensaver start|stop
 */
Scope {
    id: root

    readonly property string launcher: Quickshell.env("HOME") + "/.config/hypr/scripts/launch-screensaver.sh"

    property bool running: false

    function start(force) {
        if (GlobalStates.screenLocked) return;
        root.running = true;
        Quickshell.execDetached(force ? [root.launcher, "force"] : [root.launcher]);
    }
    function stop() {
        root.running = false;
        // "--" first: otherwise pkill reads the pattern as an option of its own
        Quickshell.execDetached(["pkill", "-f", "--", "class=org\\.bwm\\.screensaver"]);
    }

    // Closes it on the first input once it is showing, also when started by hand
    // (the main monitor below only notices activity after a real idle period)
    IdleMonitor {
        enabled: root.running
        timeout: 2
        respectInhibitors: false
        onIsIdleChanged: if (!isIdle && root.running) root.stop()
    }

    IdleMonitor {
        enabled: (Config.options?.screensaver?.enable ?? true) && !Idle.inhibit
        timeout: Math.max(1, Config.options?.screensaver?.timeoutMinutes ?? 5) * 60
        respectInhibitors: true
        onIsIdleChanged: {
            if (isIdle) root.start(false);
            else if (root.running) root.stop();
        }
    }

    IpcHandler {
        target: "screensaver"
        function start(): void { root.start(true); }
        function stop(): void { root.stop(); }
    }
}
