pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Io
import qs.modules.ii.bar.omarchy
import "omarchy" as OM

/**
 * Retro's menu / command palette: Omarchy's own menu (omarchy/Menu.qml + MenuModel.js, from
 * Omarchy's shell/plugins/menu, MIT) reading BWM's catalog hypr/omarchy/bwm-menu.jsonc, with the
 * user's overlay at ~/.config/bwm/extensions/menu.jsonc. Hierarchical entries, live `when`
 * (show/hide), `checked` (✓) and `disabled` guards, providers (apps, fonts) and search.
 *
 * IPC: qs -c ii ipc call omarchyMenu toggle|open|close
 *      qs -c ii ipc call omarchyMenu summon <route>   (e.g. system, appearance.font, setup)
 */
Scope {
    id: root

    AppLibrary {
        id: appLibrary
    }

    // The part of omarchy-shell the menu talks to
    QtObject {
        id: shellApi
        readonly property var appLibrary: appLibrary
        function summon(id, payload) {
            if (id === "omarchy.menu") {
                menu.open(payload || "{}");
                return true;
            }
            return OmarchyPlugins.summon(id, payload);
        }
    }

    OM.Menu {
        id: menu
        shell: shellApi
    }

    IpcHandler {
        target: "omarchyMenu"
        function toggle(): void {
            if (menu.opened)
                menu.close();
            else
                menu.open("{}");
        }
        function open(): void { menu.open("{}"); }
        function close(): void { menu.close(); }
        function summon(route: string): void { menu.open(JSON.stringify({ menu: route })); }
        function refresh(): void { menu.refresh(); }
    }
}
