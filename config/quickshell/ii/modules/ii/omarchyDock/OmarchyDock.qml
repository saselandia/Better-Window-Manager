import QtQuick
import Quickshell
import Quickshell.Io
import qs.modules.ii.omarchyMenu

/**
 * Retro: Omarchy's dock (Dock.qml, shell/plugins/dock, MIT) with BWM's app library. Its settings
 * (position, autohide, pinned apps) live in ~/.config/bwm/dock.json, written by the omarchy-dock
 * shim; without pins of its own the dock pins BWM's usual apps.
 *
 * IPC: qs -c ii ipc call omarchy.dock apps|refresh
 */
Scope {
    id: root

    AppLibrary {
        id: appLibrary
    }

    property var dockConfig: ({})

    FileView {
        id: dockFile
        path: Quickshell.env("HOME") + "/.config/bwm/dock.json"
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: {
            try {
                root.dockConfig = JSON.parse(text()) || ({});
            } catch (e) {
                root.dockConfig = ({});
            }
        }
        onLoadFailed: root.dockConfig = ({})
    }

    // The part of omarchy-shell the dock talks to
    QtObject {
        id: shellApi
        readonly property var appLibrary: appLibrary
        readonly property var shellConfig: ({ dock: root.dockConfig })
        readonly property var defaultsConfig: ({
            dock: {
                position: "bottom",
                pinned: ["org.gnome.Nautilus", "firefox-bin", "kitty", "dev.vencord.Vesktop", "com.spotify.Client", "steam"]
            }
        })
    }

    Dock {
        shell: shellApi
    }
}
