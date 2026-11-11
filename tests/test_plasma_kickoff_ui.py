"""Fase 4 de docs/BREEZE_PLAN.md: Kickoff de Plasma 6.7.5 portado (modules/plasma/kickoff).

Pruebas opcionales con eventos de teclado reales de QtTest en una instancia aparte (qs -p), como
tests/test_retro_ui.py. Necesitan la sesión Wayland, plasma-workspace (modelos de Kicker) y
QtTest:

    BWM_RUN_QML_TESTS=1 python3 -m unittest tests.test_plasma_kickoff_ui -v

No arrancan ni reinician el shell real, no escriben la configuración (Config.blockWrites) y usan
otro cliente de favoritos de KActivities (BWM_KICKOFF_ID), que se vacía al terminar. La app que se
lanza es un .desktop de prueba en un XDG_DATA_HOME temporal que sólo crea un archivo.
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
//@ pragma Env QT_QUICK_CONTROLS_STYLE=Basic
import QtQuick
import QtTest
import Quickshell
import Quickshell.Wayland
import org.kde.kitemmodels as KItemModels
import qs
import qs.modules.common
import qs.modules.plasma.kickoff as K

ShellRoot {
    id: shell
    property var results: ({})
    readonly property var kickoff: loader.item
    function report(key, value) { results[key] = value; console.log("KICKOFFTEST " + JSON.stringify({ key: key, value: value })); }

    PanelWindow {
        id: win
        screen: Quickshell.screens.find(s => s.name === "@SCREEN@") ?? Quickshell.screens[0]
        anchors { top: true; left: true }
        implicitWidth: kickoff ? kickoff.implicitWidth : 700
        implicitHeight: kickoff ? kickoff.implicitHeight : 500
        color: "#202326"
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "bwm-test-kickoff"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive

        // Asíncrono, como el PanelLoader del shell: una propiedad requerida sin dar aborta la
        // creación sólo así (de forma síncrona es un aviso)
        Loader {
            id: loader
            anchors.fill: parent
            asynchronous: true
            focus: true
            sourceComponent: K.Kickoff { focus: true }
            onStatusChanged: if (status === Loader.Error) shell.report("loaderError", true)
        }

        TestCase {
            id: driver
            name: "KickoffPort"
            when: false
        }
    }

    function focusName() {
        const item = win.contentItem?.Window?.activeFocusItem ?? null;
        if (!item) return "none";
        if (item === kickoff.searchField) return "search";
        let p = item;
        while (p) {
            if (p === kickoff.sideBar) return "sidebar";
            if (p === kickoff.contentArea) return "content";
            if (p === kickoff.footer) return "footer";
            p = p.parent;
        }
        return "other";
    }

    function favoriteIds() {
        const fav = kickoff.rootModel.favoritesModel;
        const role = fav.KItemModels.KRoleNames.role("favoriteId");
        const ids = [];
        for (let i = 0; i < fav.count; i++) ids.push(fav.data(fav.index(i, 0), role));
        return ids;
    }

    property int step: 0
    Timer {
        id: tick
        interval: 400
        repeat: true
        running: loader.status === Loader.Ready
        onTriggered: shell.next()
    }

    function key(k) { driver.keyClick(k, Qt.NoModifier, 5); }

    function next() {
        step++;
        switch (step) {
        case 1:
            Config.blockWrites = true;
            GlobalStates.plasmaKickoffOpen = true;
            kickoff.forceActiveFocus();
            break;
        case 4:
            report("rootRows", kickoff.rootModel.count);
            report("allApps", kickoff.rootModel.modelForRow(1)?.count ?? -1);
            report("favorites", favoriteIds());
            kickoff.searchField.forceActiveFocus();
            report("startFocus", focusName());
            for (const ch of "bwmkickoffstub") driver.keyClick(ch, Qt.NoModifier, 5);
            break;
        case 9: {
            const results = kickoff.runnerModel.count ? kickoff.runnerModel.modelForRow(0) : null;
            report("searchResults", results ? results.count : 0);
            report("firstResult", results && results.count ? results.data(results.index(0, 0), Qt.DisplayRole) : "");
            key(Qt.Key_Return);
            break;
        }
        case 11:
            report("closedAfterLaunch", !GlobalStates.plasmaKickoffOpen);
            GlobalStates.plasmaKickoffOpen = true;
            kickoff.searchField.text = "";
            kickoff.searchField.forceActiveFocus();
            break;
        case 13:
            key(Qt.Key_Down);
            break;
        case 14:
            report("downFromSearch", focusName());
            report("contentIndex0", kickoff.contentArea?.currentIndex ?? -2);
            key(Qt.Key_Right);
            break;
        case 15:
            // Los favoritos son una rejilla: → pasa al siguiente y ← vuelve; desde la primera columna,
            // ← sale a la barra lateral
            report("contentIndex1", kickoff.contentArea?.currentIndex ?? -2);
            key(Qt.Key_Left);
            key(Qt.Key_Left);
            break;
        case 16:
            report("leftToSidebar", focusName());
            report("sidebarIndex0", kickoff.sideBar?.currentIndex ?? -2);
            key(Qt.Key_Down);
            key(Qt.Key_Down);
            break;
        case 17:
            report("sidebarIndex2", kickoff.sideBar?.currentIndex ?? -2);
            report("categoryAfterDown", kickoff.sideBar?.currentItem?.text ?? "");
            key(Qt.Key_Right);
            break;
        case 18:
            report("rightToContent", focusName());
            key(Qt.Key_Menu);
            break;
        case 19: {
            const menu = K.ActionMenu.menu.current;
            report("contextMenuOpen", !!menu && menu.visible);
            const texts = [];
            if (menu) for (let i = 0; i < menu.count; i++) texts.push(menu.itemAt(i)?.text ?? "");
            report("contextMenuItems", texts);
            if (menu) menu.close();
            break;
        }
        case 20:
            kickoff.searchField.forceActiveFocus();
            report("focusBeforeEscape", focusName());
            key(Qt.Key_Escape);
            break;
        case 21: {
            // Botones de sesión: sólo las acciones que lleva bwm-power
            const texts = [];
            function visit(item) {
                if (!item) return;
                if (item.visible && typeof item.text === "string" && item.text && item.icon && item.icon.name) texts.push(item.text);
                for (const c of item.children ?? []) visit(c);
            }
            visit(kickoff.footer);
            report("footerButtons", texts);
            report("closedByEscape", !GlobalStates.plasmaKickoffOpen);
            report("searchTextAtEscape", kickoff.searchField.text);
            break;
        }
        case 22: {
            const fav = kickoff.rootModel.favoritesModel;
            for (const id of favoriteIds()) fav.removeFavorite(id);
            break;
        }
        case 25:
            report("favoritesAfterCleanup", favoriteIds().length);
            report("done", true);
            Qt.quit();
            break;
        }
    }
}
'''

STUB = """[Desktop Entry]
Type=Application
Name=BWM Kickoff Stub
Comment=Prueba de Kickoff
Keywords=bwmkickoffstub;
Exec=sh -c 'echo launched > {marker}'
Icon=utilities-terminal
Categories=Utility;
"""


@unittest.skipUnless(os.environ.get("BWM_RUN_QML_TESTS") == "1", "pruebas de interfaz opcionales (BWM_RUN_QML_TESTS=1)")
class PlasmaKickoffUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("qs") or not os.environ.get("WAYLAND_DISPLAY"):
            raise unittest.SkipTest("hace falta Quickshell en una sesión Wayland")
        cls.tmp = tempfile.TemporaryDirectory()
        tmp = Path(cls.tmp.name)
        cls.marker = tmp / "launched"
        data, cache = tmp / "data", tmp / "cache"
        (data / "applications").mkdir(parents=True)
        (data / "applications" / "bwm-kickoff-stub.desktop").write_text(STUB.format(marker=cls.marker))
        # La app de prueba en XDG_DATA_DIRS: XDG_DATA_HOME sigue siendo el real porque los favoritos y
        # recientes leen la base de datos de kactivitymanagerd de ahí
        data_dirs = os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share"
        env = dict(os.environ, XDG_DATA_DIRS=f"{data}:{data_dirs}", XDG_CACHE_HOME=str(cache), XDG_MENU_PREFIX="plasma-",
                   BWM_KICKOFF_ID="bwm-test-" + uuid.uuid4().hex[:8])
        subprocess.run(["kbuildsycoca6", "--noincremental"], env=env, capture_output=True, timeout=120)
        harness = SHELL / f"zz_test_kickoff_{uuid.uuid4().hex[:8]}.qml"
        screen = os.environ.get("BWM_TEST_SCREEN", "DP-1")
        harness.write_text(HARNESS.replace("@SCREEN@", screen))
        try:
            out = subprocess.run(["qs", "-p", str(harness)], env=env, capture_output=True, text=True, timeout=60)
        finally:
            harness.unlink(missing_ok=True)
        cls.log = out.stdout + out.stderr
        cls.results = {}
        for line in cls.log.splitlines():
            if "KICKOFFTEST " in line:
                item = json.loads(line.split("KICKOFFTEST ", 1)[1])
                cls.results[item["key"]] = item["value"]
        # La app de prueba se lanza aparte (KIO): dale un momento
        for _ in range(20):
            if cls.marker.exists():
                break
            time.sleep(0.25)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_models_load(self):
        self.assertNotIn("loaderError", self.results)
        self.assertNotIn("was not initialized", self.log)
        self.assertTrue(self.results.get("done"), self.log[-2000:])
        self.assertGreater(self.results["rootRows"], 3)
        self.assertGreater(self.results["allApps"], 0)
        self.assertEqual(len(self.results["favorites"]), 4, self.results["favorites"])

    def test_search_and_launch(self):
        self.assertEqual(self.results["startFocus"], "search")
        self.assertGreaterEqual(self.results["searchResults"], 1)
        self.assertEqual(self.results["firstResult"], "BWM Kickoff Stub")
        self.assertTrue(self.marker.exists(), "Intro en la búsqueda debe lanzar el primer resultado")
        self.assertTrue(self.results["closedAfterLaunch"])

    def test_keyboard_navigation(self):
        # Como en Kickoff 6.7.5: ↓ desde la búsqueda va al contenido, ← a la barra lateral
        # (que cambia de categoría al moverse) y → vuelve al contenido
        self.assertEqual(self.results["downFromSearch"], "content")  # rejilla de favoritos
        self.assertEqual(self.results["contentIndex1"], self.results["contentIndex0"] + 1)
        self.assertEqual(self.results["leftToSidebar"], "sidebar")
        # Dos ↓ en la barra lateral: dos categorías más abajo (el separador se salta)
        self.assertGreater(self.results["sidebarIndex2"], self.results["sidebarIndex0"] + 1)
        self.assertNotEqual(self.results["categoryAfterDown"], "Favorites")
        self.assertEqual(self.results["rightToContent"], "content")

    def test_context_menu(self):
        self.assertTrue(self.results["contextMenuOpen"])
        items = self.results["contextMenuItems"]
        self.assertTrue(any("Favorite" in t for t in items), items)
        self.assertNotEqual(items[0], "", "sin separador al principio")
        if not shutil.which("kmenuedit"):
            self.assertFalse(any("Edit Application" in t for t in items), items)

    def test_escape_and_session_buttons(self):
        self.assertTrue(self.results["closedByEscape"])
        for text in self.results["footerButtons"]:
            self.assertNotIn("Switch User", text)
        self.assertEqual(self.results["favoritesAfterCleanup"], 0)


if __name__ == "__main__":
    unittest.main()
