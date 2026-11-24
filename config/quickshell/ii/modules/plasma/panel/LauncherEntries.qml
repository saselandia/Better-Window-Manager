pragma Singleton
// BWM: data side of Plasma's SmartLauncher::Item (plasma-desktop 6.7.5,
// applets/taskmanager/smartlauncheritem.cpp, GPL-2.0-or-later). The applet's private
// QML module only exists inside plasmashell, so the session-bus listener is
// skins/plasma/scripts/launcher-entries.py and this singleton keeps its state.
// Like Backend::count()/countVisible(), badges are hidden while do-not-disturb is on.
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
import qs.modules.common
import "LauncherEntries.js" as Logic
Singleton {
    id: root
    property var entries: ({})
    readonly property bool doNotDisturb: Notifications.silent
    readonly property string script: Quickshell.env("HOME") + "/.config/hypr/skins/plasma/scripts/launcher-entries.py"

    function lookup(appId, desktopId) { return Logic.lookup(root.entries, appId, desktopId); }
    function countVisible(e) { return Logic.countVisible(e, root.doNotDisturb); }
    function progressVisible(e) { return Logic.progressVisible(e); }
    function handle(line) { root.entries = Logic.handle(root.entries, line); }

    Process {
        id: listener
        running: Appearance.isPlasma
        command: ["python3", root.script]
        stdout: SplitParser { onRead: line => root.handle(line) }
        onExited: if (Appearance.isPlasma) restart.start()
    }
    Timer { id: restart; interval: 5000; onTriggered: listener.running = Appearance.isPlasma }
}
