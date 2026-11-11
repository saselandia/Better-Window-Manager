"""Fase 11 de docs/BREEZE_PLAN.md: Preferencias del sistema de Breeze (modules/plasma/settings).

Siempre: el catálogo apunta a archivos que existen, sin ids repetidos ni alias que choquen, y las
páginas que se quitaron (Interfaz, Plugins, Temas) siguen abriendo algo con su SETTINGS_PAGE.

Opcional (BWM_RUN_QML_TESTS=1, sesión Wayland, módulo org.bwm.kcm instalado): abre cada página en
una instancia qs -p aparte (workspace 9, sin foco) y comprueba que carga sin errores de QML y que
SETTINGS_PAGE elige la página pedida (ids, alias y nombres). No escribe la configuración.
"""
import json
import os
import re
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "config/quickshell/ii"
CATALOG = SHELL / "modules/plasma/settings/Catalog.js"
KCMS = Path("/usr/lib64/qt6/plugins/plasma/kcms/systemsettings")


def entries():
    text = CATALOG.read_text()
    for m in re.finditer(r'\{ id: "([a-z]+)", kind: "([a-z]+)"(.*?)(?=\n\s*\{ id:|\n\s*\] \},|\n\s*\]\s*\},)', text, re.S):
        body = m.group(3)
        comp = re.search(r'component: (BWM|PAGES) \+ "([^"]+)"', body)
        module = re.search(r'module: "([^"]+)"', body)
        aliases = re.search(r'aliases: \[([^\]]*)\]', body)
        yield {"id": m.group(1), "kind": m.group(2),
               "component": ({"BWM": "modules/settings/", "PAGES": "modules/plasma/settings/pages/"}[comp.group(1)] + comp.group(2)) if comp else None,
               "module": module.group(1) if module else None,
               "aliases": re.findall(r'"([^"]+)"', aliases.group(1)) if aliases else []}


class CatalogTest(unittest.TestCase):
    def test_pages_exist_and_ids_are_unique(self):
        found = list(entries())
        self.assertGreaterEqual(len(found), 20)
        ids = [e["id"] for e in found] + [a for e in found for a in e["aliases"]]
        self.assertEqual(len(ids), len(set(ids)), ids)
        for e in found:
            if e["component"]:
                self.assertTrue((SHELL / e["component"]).is_file(), e)
            if e["kind"] == "kcm":
                self.assertTrue(e["module"], e)
                if KCMS.is_dir():
                    self.assertTrue((KCMS / f"{e['module']}.so").is_file(), e)

    def test_removed_pages_keep_their_ids(self):
        ids = {a for e in entries() for a in [e["id"], *e["aliases"]]}
        for old in ("general", "bar", "background", "keybinds", "services", "autostart", "display",
                    "workspaces", "defaultapps", "idle", "style", "cursor", "about",
                    "interface", "plugins", "themes"):
            self.assertIn(old, ids)

    def test_no_omarchy_or_end4_only_pages(self):
        components = {e["component"] for e in entries() if e["component"]}
        for gone in ("InterfaceConfig.qml", "PluginsConfig.qml", "ThemesConfig.qml", "BackgroundConfig.qml"):
            self.assertFalse(any(c.endswith("/" + gone) for c in components), gone)


HARNESS_TITLE = "^(System Settings|Preferencias del sistema)$"


@unittest.skipUnless(os.environ.get("BWM_RUN_QML_TESTS") == "1", "pruebas de interfaz opcionales (BWM_RUN_QML_TESTS=1)")
class SettingsUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["hyprctl", "eval", 'hl.window_rule({ name = "tmp-f11-tests", match = { class = "^org.quickshell$", '
                        f'title = "{HARNESS_TITLE}" }}, workspace = "9 silent", no_initial_focus = true }})'],
                       check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        subprocess.run(["hyprctl", "eval", 'hl.window_rule({ name = "tmp-f11-tests", match = { title = "^$BWM-NADA^" } })'],
                       capture_output=True)

    def run_page(self, page):
        env = dict(os.environ, SETTINGS_PAGE=page, QT_QUICK_CONTROLS_STYLE="org.kde.desktop",
                   QML_IMPORT_PATH=str(Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "bwm/qml"))
        # Report the selected page and quit: a copy of the root with a probe, never a second ii
        probe = SHELL / f"zz_settings_probe_{os.getpid()}.qml"
        text = (SHELL / "plasmaSettings.qml").read_text().replace(
            "            SettingsState.select(\"globaltheme\", true);",
            "            SettingsState.select(\"globaltheme\", true);\n"
            "        probeTimer.start();")
        text = text.replace("    Shortcut { sequence: StandardKey.Find;",
                            "    Timer { id: probeTimer; interval: 2500; onTriggered: { console.log(\"F11PROBE \" + "
                            "SettingsState.current.entry.id); Qt.quit(); } }\n    Shortcut { sequence: StandardKey.Find;")
        probe.write_text(text)
        try:
            out = subprocess.run(["qs", "-p", str(probe)], env=env, capture_output=True, text=True, timeout=30).stdout
        finally:
            probe.unlink(missing_ok=True)
        page_id = (re.findall(r"F11PROBE (\w+)", out) or [None])[-1]
        # Only while running: Kirigami pages warn while the window is torn down after Qt.quit()
        running = out.split("F11PROBE", 1)[0]
        # Warnings inside a KCM's own QML (qrc:/kcm/…) are upstream's, also under systemsettings
        errors = [l for l in running.splitlines() if re.search(r"TypeError|ReferenceError|is not a type|Cannot assign|"
                                                           r"failed to load|crashed|Unable to assign", l)
                  and "qrc:/kcm/" not in l]
        return page_id, errors

    def test_every_page_loads(self):
        for e in entries():
            with self.subTest(page=e["id"]):
                page_id, errors = self.run_page(e["id"])
                self.assertEqual(page_id, e["id"])
                self.assertEqual(errors, [])

    def test_aliases_and_names(self):
        for page, expected in (("Autostart", "autostart"), ("interface", "behavior"), ("themes", "globaltheme"),
                               ("plugins", "bar"), ("Pantalla y monitor", "display"), ("no-such-page", "globaltheme")):
            with self.subTest(page=page):
                self.assertEqual(self.run_page(page)[0], expected)


if __name__ == "__main__":
    unittest.main()
