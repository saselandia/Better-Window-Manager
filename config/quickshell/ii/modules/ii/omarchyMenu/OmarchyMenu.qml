pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons as Commons
import qs.modules.common
import qs.modules.ii.bar.omarchy
import "omarchy" as OM
import "omarchy/settings" as Settings

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

    readonly property alias menu: mainMenu

    AppLibrary {
        id: appLibrary
    }
    Settings.SettingsController { id: settingsController }
    Loader {
        id: keybindingsLoader
        active: Config.ready && Appearance.isRetro
        sourceComponent: Keybindings { menu: mainMenu; onOpening: root.closeApps() }
    }

    function closeApps() {
        Commons.IpcRegistry.call("omarchy.dock", "closeApps", []);
        appGrid.close();
    }
    function openApps(toggle) {
        menu.close();
        const dock = Commons.IpcRegistry.call("omarchy.dock", toggle ? "apps" : "openApps", []);
        if (dock.ran) { appGrid.close(); return; }
        if (toggle) appGrid.toggle();
        else appGrid.open();
    }
    function openMenu(payload) {
        root.closeApps();
        menu.open(payload);
    }

    function openSettings(page) {
        root.closeApps();
        const route = settingsController.route(page);
        menu.open(JSON.stringify({ menu: route }));
    }

    // The part of omarchy-shell the menu talks to
    QtObject {
        id: shellApi
        readonly property var appLibrary: appLibrary
        function summon(id, payload) {
            if (id === "bwm.keybindings" && keybindingsLoader.item) { keybindingsLoader.item.open(); return true; }
            if (id === "bwm.apps") { root.openApps(false); return true; }
            if (id === "bwm.settings") {
                let data = {};
                try { data = JSON.parse(payload || "{}"); } catch (e) { }
                root.openSettings(data.page || "all");
                return true;
            }
            if (id === "omarchy.menu") {
                root.openMenu(payload || "{}");
                return true;
            }
            return OmarchyPlugins.summon(id, payload);
        }
    }

    OM.Menu {
        id: mainMenu
        shell: shellApi
        settingsAdapter: settingsController
    }

    // One Apps launcher for the menu, Alt+Space and Super+Space.
    OM.AppGrid {
        id: appGrid
        appLibrary: appLibrary
        onSettingsRequested: root.openSettings("all")
    }

    IpcHandler {
        target: "omarchyApps"
        function toggle(): void { root.openApps(true); }
        function open(): void { root.openApps(false); }
        function close(): void { root.closeApps(); }
        function inspect(): string {
            const dock = Commons.IpcRegistry.call("omarchy.dock", "inspectApps", []);
            return dock.ran && dock.output ? dock.output : appGrid.inspect();
        }
    }

    IpcHandler {
        target: "omarchyMenu"
        function toggle(): void {
            if (menu.opened)
                menu.close();
            else
                root.openMenu("{}");
        }
        function open(): void { root.openMenu("{}"); }
        function close(): void { menu.close(); }
        function summon(route: string): void { root.openMenu(JSON.stringify({ menu: route })); }
        // BWM: abre <route> con la fila <item> marcada (p. ej. al volver de una página de Ajustes)
        function summonSelect(route: string, item: string): void { root.openMenu(JSON.stringify({ menu: route, select: item })); }
        // Omarchy's full payload: {"menu": ...} or the select / input modes of omarchy-menu-select
        function openPayload(payload: string): void { root.openMenu(payload); }
        function refresh(): void { menu.refresh(); }
        function settings(page: string): void { root.openSettings(page); }
        function state(): string { return menu.opened ? menu.activeMenu : "closed"; }
        function inspect(): string { return menu.inspect(); }
        function selected(): string { return menu.selectedItemId(); }
        // Same as Escape: back out of a submenu, close at the root
        function back(): string { return menu.goBack() ? menu.activeMenu : (menu.close(), "closed"); }
    }
}
