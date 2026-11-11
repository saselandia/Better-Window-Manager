"""Fase 9 de docs/BREEZE_PLAN.md: menús contextuales de Plasma en Breeze (modules/plasma/menus).

Pruebas opcionales en una instancia aparte (qs -p) que carga MenuHost como el shell, con una kitty de
prueba en el workspace 9 (regla temporal, sin foco). Necesitan la sesión Wayland y plasma-workspace:

    BWM_RUN_QML_TESTS=1 python3 -m unittest tests.test_plasma_menus_ui -v

Comprueban la estructura de los cuatro menús (ventana como UserActionsMenu de KWin, gestor de tareas
como ContextMenu.qml, escritorio y panel), que se abren dentro de la pantalla, la traducción al
español del catálogo propio y dos acciones reales sobre la ventana de prueba (maximizar, sin barra).
No escriben la configuración (Config.blockWrites), no tocan el shell real y cierran la ventana.
"""
import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "config/quickshell/ii"

HARNESS = r'''//@ pragma UseQApplication
//@ pragma Env QS_NO_RELOAD_POPUP=1
import QtQuick
import Quickshell
import Quickshell.Wayland
import qs
import qs.services
import qs.modules.common
import qs.modules.plasma.menus as M

ShellRoot {
    id: shell
    function report(key, value) { console.log("MENUSTEST " + JSON.stringify({ key: key, value: value })); }
    M.MenuHost { id: host }

    // Un submenú cerrado tiene todas sus entradas invisibles: ahí no se filtra por visibilidad
    function items(menu, closedSubmenu) {
        const out = [];
        if (!menu) return out;
        for (let i = 0; i < menu.count; i++) {
            const it = menu.itemAt(i);
            if (!it || (!closedSubmenu && (it.visible === false || it.height === 0))) continue;
            out.push(it.subMenu ? "▸ " + it.subMenu.title : (it.text || "—"));
        }
        return out;
    }
    function find(menu, text) {
        for (let i = 0; i < menu.count; i++) if (menu.itemAt(i)?.text === text) return menu.itemAt(i);
        return null;
    }
    function inScreen(menu) {
        const s = Quickshell.screens.find(x => x.name === M.PlasmaMenus.screenName);
        return !!menu && !!s && menu.x >= 0 && menu.y >= 0 && menu.x + menu.width <= s.width + 1 && menu.y + menu.height <= s.height + 1;
    }

    property int step: 0
    Timer { interval: 500; repeat: true; running: true; onTriggered: shell.next() }
    function next() {
        step++;
        const addr = "@ADDRESS@";
        switch (step) {
        case 1:
            Config.blockWrites = true;
            HyprlandData.updateAll();
            break;
        case 3: {
            const c = HyprlandData.windowList.find(w => w.address === addr);
            M.PlasmaMenus.openAt("window", (c?.at?.[0] ?? 100) + 10, (c?.at?.[1] ?? 100) - 10, { address: addr });
            break;
        }
        case 5: {
            const m = host.menu;
            report("windowOpen", !!m && m.opened);
            report("windowItems", items(m));
            report("windowInScreen", inScreen(m));
            const more = (() => { for (let i = 0; i < m.count; i++) if (m.itemAt(i)?.subMenu) { const sm = m.itemAt(i).subMenu; if (sm.title.indexOf("More") >= 0 || sm.title.indexOf("Más") >= 0) return sm; } return null; })();
            report("moreItems", items(more, true));
            const max = find(m, m.tr("Ma&ximize"));
            report("windowMenuSubmenuOk", !!more);
            report("maximizeChecked", max?.checked ?? null);
            if (max) max.triggered();
            M.PlasmaMenus.close();
            break;
        }
        case 7: {
            HyprlandData.updateAll();
            const top = ToplevelManager.toplevels.values.find(t => HyprlandData.clientForToplevel(t)?.address === addr);
            report("toplevelFound", !!top);
            M.PlasmaMenus.openLocal("task", Quickshell.screens[0].name, 200, Quickshell.screens[0].height - 50,
                                    { group: { appId: "kitty", toplevels: top ? [top] : [] }, edge: "bottom" });
            break;
        }
        case 10: {
            const m = host.menu;
            report("taskOpen", !!m && m.opened);
            report("taskItems", items(m));
            report("taskInScreen", inScreen(m));
            M.PlasmaMenus.openLocal("desktop", Quickshell.screens[0].name, 300, 300, {});
            break;
        }
        case 12:
            report("desktopItems", items(host.menu));
            report("desktopInScreen", inScreen(host.menu));
            M.PlasmaMenus.openLocal("panel", Quickshell.screens[0].name, 400, Quickshell.screens[0].height - 20,
                                    { panelScreen: Quickshell.screens[0].name, editing: false, edge: "bottom" });
            break;
        case 14:
            report("panelItems", items(host.menu));
            report("panelInScreen", inScreen(host.menu));
            M.PlasmaMenus.close();
            break;
        case 15:
            report("closed", !M.PlasmaMenus.opened && !host.menu);
            report("done", true);
            Qt.quit();
            break;
        }
    }
}
'''


def hypr(*args):
    return json.loads(subprocess.check_output(["hyprctl", "-j", *args]))


@unittest.skipUnless(os.environ.get("BWM_RUN_QML_TESTS") == "1", "pruebas de interfaz opcionales (BWM_RUN_QML_TESTS=1)")
class PlasmaMenusUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("qs") or not os.environ.get("WAYLAND_DISPLAY") or not shutil.which("kitty"):
            raise unittest.SkipTest("hace falta Quickshell y kitty en una sesión Wayland")
        cls.cls_name = "bwm-menus-" + uuid.uuid4().hex[:6]
        subprocess.run(["hyprctl", "eval", f'hl.window_rule({{ name = "tmp-{cls.cls_name}", match = {{ class = "^{cls.cls_name}$" }}, '
                        f'workspace = "9 silent", float = true, no_initial_focus = true }})'], capture_output=True)
        cls.proc = subprocess.Popen(["kitty", "--class", cls.cls_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cls.client = None
        for _ in range(40):
            cls.client = next((c for c in hypr("clients") if c["class"] == cls.cls_name), None)
            if cls.client:
                break
            time.sleep(0.25)
        if not cls.client:
            cls.tearDownClass()
            raise unittest.SkipTest("no apareció la ventana de prueba")
        cls.results = {}
        cls.log = ""
        cls.after = None
        for lang in ("en", "es"):
            harness = SHELL / f"zz_test_menus_{uuid.uuid4().hex[:8]}.qml"
            harness.write_text(HARNESS.replace("@ADDRESS@", cls.client["address"]))
            env = dict(os.environ, LANGUAGE=lang)
            try:
                out = subprocess.run(["qs", "-p", str(harness)], env=env, capture_output=True, text=True, timeout=60)
            finally:
                harness.unlink(missing_ok=True)
            cls.log += out.stdout + out.stderr
            res = {}
            for line in (out.stdout + out.stderr).splitlines():
                if "MENUSTEST " in line:
                    item = json.loads(line.split("MENUSTEST ", 1)[1])
                    res[item["key"]] = item["value"]
            cls.results[lang] = res
            if lang == "en":
                time.sleep(0.8)
                cls.after = next((c for c in hypr("clients") if c["address"] == cls.client["address"]), None)
                # Deshacer el maximizado de la prueba antes de la segunda pasada
                subprocess.run(["python3", str(ROOT / "config/hypr/skins/plasma/scripts/kwin-window.py"), "maximize", "--mode",
                                "restore", cls.client["address"]], capture_output=True)

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "proc", None):
            cls.proc.terminate()
        subprocess.run(["hyprctl", "reload"], capture_output=True)

    def test_window_menu_like_kwin(self):
        r = self.results["en"]
        self.assertTrue(r.get("done"), self.log[-3000:])
        self.assertTrue(r["windowOpen"])
        self.assertTrue(r["windowInScreen"])
        items = r["windowItems"]
        # Orden de UserActionsMenu::init() (los submenús de escritorios/pantallas, sólo si hay más de uno)
        core = [i for i in items if not i.startswith("▸ &Desktops") and not i.startswith("▸ Move to &Screen")]
        self.assertEqual(core, ["Ma&ximize", "Mi&nimize", "Keep &Above Others", "▸ &More Actions", "—", "&Close"], items)
        self.assertIn("▸ &Desktops", items)
        if len(hypr("monitors")) > 1:
            self.assertIn("▸ Move to &Screen", items)
        self.assertEqual(r["moreItems"][:6], ["&Move", "&Resize", "Keep &Below Others", "&Fullscreen", "&No Titlebar and Frame",
                                              "&Hide from Screenshots and Screen Recordings"])
        self.assertIn("Configure Special &Window Settings…", r["moreItems"])
        self.assertFalse(r["maximizeChecked"])

    def test_window_menu_action_runs(self):
        tags = {t.rstrip("*") for t in (self.after or {}).get("tags", [])}
        self.assertIn("bwm-maximized", tags, "«Maximizar» del menú maximiza con kwin-window.py")

    def test_task_menu_like_plasma(self):
        r = self.results["en"]
        self.assertTrue(r["toplevelFound"])
        self.assertTrue(r["taskOpen"])
        self.assertTrue(r["taskInScreen"])
        items = r["taskItems"]
        for expected in ("Open New Window", "▸ Move to &Desktop", "▸ More", "Enter Edit Mode", "&Close"):
            self.assertIn(expected, items)
        self.assertTrue("&Pin to Task Manager" in items or "Unpin from Task Manager" in items, items)
        self.assertLess(items.index("Open New Window"), items.index("▸ More"))
        self.assertEqual(items[-1], "&Close")

    def test_desktop_and_panel_menus(self):
        r = self.results["en"]
        self.assertEqual([i for i in r["desktopItems"] if i != "—"][:3], ["Open Terminal", "Lock Screen", "Show Logout Screen"])
        self.assertIn("Desktop and Wallpaper", r["desktopItems"])
        self.assertIn("Display Configuration", r["desktopItems"])
        self.assertTrue(r["desktopInScreen"])
        self.assertEqual(r["panelItems"], ["Add or Manage Widgets…", "—", "Enter Edit Mode"])
        self.assertTrue(r["panelInScreen"])
        self.assertTrue(r["closed"])

    def test_spanish_catalog(self):
        r = self.results["es"]
        self.assertTrue(r.get("done"), self.log[-3000:])
        self.assertIn("Ma&ximizar", r["windowItems"])
        self.assertIn("Abrir una nueva ventana", r["taskItems"])
        self.assertIn("Bloquear pantalla", r["desktopItems"])


if __name__ == "__main__":
    unittest.main()
