pragma Singleton

import qs.modules.common
import qs.modules.common.functions
import QtQuick
import Quickshell
import Quickshell.Io

Singleton {
    id: root

    readonly property string conflictHelper: FileUtils.trimFileProtocol(Quickshell.shellPath("../..")) + "/hypr/scripts/bwm-shell-conflicts.py"
    property string killDialogQmlPath: FileUtils.trimFileProtocol(Quickshell.shellPath("killDialog.qml"))

    function load() {
        // dummy to force init
    }

    Connections {
        target: Config
        function onReadyChanged() {
            if (Config.ready) checkConflictsProc.running = true
        }
    }

    Process {
        id: checkConflictsProc
        command: ["python3", root.conflictHelper, "--repair-stale"]
        stdout: StdioCollector {
            onStreamFinished: {
                const conflicts = JSON.parse(this.text);
                const conflictingTrays = !!conflicts.trays;
                const conflictingNotifications = !!conflicts.notifications;
                var openDialog = false;
                if (conflictingTrays) {
                    if (!Config.options.conflictKiller.autoKillTrays) openDialog = true;
                    else Quickshell.execDetached(["python3", root.conflictHelper, "resolve", "trays"])
                }
                if (conflictingNotifications) {
                    if (!Config.options.conflictKiller.autoKillNotificationDaemons) openDialog = true;
                    else Quickshell.execDetached(["python3", root.conflictHelper, "resolve", "notifications"])
                }
                if (openDialog) {
                    Quickshell.execDetached(["qs", "-p", root.killDialogQmlPath])
                }
            }
        }
    }
}
