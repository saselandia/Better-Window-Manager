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

    // Omarchy's "Apps" launcher (Super+Alt+Space, the menu's Apps entry): every app on a grid
    OM.AppGrid {
        id: appGrid
        appLibrary: appLibrary
    }

    IpcHandler {
        target: "omarchyApps"
        function toggle(): void { appGrid.toggle(); }
        function open(): void { appGrid.open(); }
        function close(): void { appGrid.close(); }
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
        // BWM: abre <route> con la fila <item> marcada (p. ej. al volver de una página de Ajustes)
        function summonSelect(route: string, item: string): void { menu.open(JSON.stringify({ menu: route, select: item })); }
        // Omarchy's full payload: {"menu": ...} or the select / input modes of omarchy-menu-select
        function openPayload(payload: string): void { menu.open(payload); }
        function refresh(): void { menu.refresh(); }
        function state(): string { return menu.opened ? menu.activeMenu : "closed"; }
        function selected(): string { return menu.selectedItemId(); }
        // Same as Escape: back out of a submenu, close at the root
        function back(): string { return menu.goBack() ? menu.activeMenu : (menu.close(), "closed"); }
    }
}
