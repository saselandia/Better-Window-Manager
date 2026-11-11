"""Fase 1 de docs/BREEZE_PLAN.md: paleta de Breeze desde el esquema de Plasma y aplicador de temas.

Todo en un HOME temporal (XDG_*), con esquemas y un tema global falsos, sin herramientas de KDE
(kwriteconfig6/plasma-apply-*) ni el gestor de skins.
"""
import configparser
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "config" / "hypr" / "skins" / "plasma" / "scripts"

DARK = """[General]
ColorScheme=TestDark
Name=Test Dark

[Colors:Window]
BackgroundNormal=32,35,38
ForegroundNormal=252,252,252
ForegroundInactive=161,169,177

[Colors:View]
BackgroundNormal=20,22,24
ForegroundNormal=252,252,252

[Colors:Selection]
BackgroundNormal=61,174,233
ForegroundNormal=252,252,252

[WM]
activeBackground=39,44,49
"""

LIGHT = """[General]
ColorScheme=TestLight
Name=Test Light

[Colors:Window]
BackgroundNormal=239,240,241
ForegroundNormal=35,38,41

[Colors:View]
BackgroundNormal=255,255,255
ForegroundNormal=35,38,41

[Colors:Selection]
BackgroundNormal=200,80,20
ForegroundNormal=255,255,255
"""

LOOKANDFEEL = """[kdeglobals][KDE]
widgetStyle=Breeze

[kdeglobals][General]
ColorScheme=TestLight

[kdeglobals][Icons]
Theme=test-icons

[plasmarc][Theme]
name=test-style

[Wallpaper]
Image=Next

[kcminputrc][Mouse]
cursorTheme=breeze_cursors

[kwinrc][org.kde.kdecoration2]
library=org.kde.breeze
theme=Breeze
"""


def ini(path):
    parser = configparser.ConfigParser(interpolation=None, strict=False, delimiters=("=",))
    parser.optionxform = str
    parser.read(path, encoding="utf-8")
    return parser


class PlasmaThemeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.config, self.data, self.state = root / "config", root / "data", root / "state"
        for d in (self.config, self.data / "color-schemes", self.state):
            d.mkdir(parents=True)
        (self.data / "color-schemes" / "TestDark.colors").write_text(DARK)
        (self.data / "color-schemes" / "TestLight.colors").write_text(LIGHT)
        laf = self.data / "plasma" / "look-and-feel" / "org.kde.breezedark.desktop" / "contents"
        laf.mkdir(parents=True)
        (laf / "defaults").write_text(LOOKANDFEEL.replace("ColorScheme=TestLight", "ColorScheme=TestDark"))
        laf2 = self.data / "plasma" / "look-and-feel" / "test.light" / "contents"
        laf2.mkdir(parents=True)
        (laf2 / "defaults").write_text(LOOKANDFEEL)
        icons = self.data / "icons" / "test-icons"
        icons.mkdir(parents=True)
        (icons / "index.theme").write_text("[Icon Theme]\nName=Test Icons\nDirectories=16x16/apps\n")
        style = self.data / "plasma" / "desktoptheme" / "test-style"
        style.mkdir(parents=True)
        (style / "metadata.json").write_text(json.dumps({"KPlugin": {"Name": "Test Style"}}))
        env = {"XDG_CONFIG_HOME": str(self.config), "XDG_DATA_HOME": str(self.data), "XDG_STATE_HOME": str(self.state),
               "XDG_DATA_DIRS": str(root / "nodata")}
        self.env = mock.patch.dict(os.environ, env)
        self.env.start()
        self.mod = self._load()
        # Sin kwriteconfig6/plasma-apply-* (usa su propio código) ni D-Bus
        self.patches = [mock.patch.object(self.mod, "_which", return_value=None),
                        mock.patch.object(self.mod, "notify_palette"),
                        mock.patch.object(self.mod.subprocess, "run", wraps=self._run)]
        for p in self.patches:
            p.start()
        self.manager_calls = []

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.env.stop()
        self.tmp.cleanup()

    def _run(self, cmd, *args, **kwargs):
        import subprocess
        if any("bwm-theme-manager.py" in str(c) for c in cmd):
            self.manager_calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)
        if cmd and cmd[0] == "dbus-send":
            return subprocess.CompletedProcess(cmd, 0)
        return self._real_run(cmd, *args, **kwargs)

    _real_run = staticmethod(__import__("subprocess").run)

    def _load(self):
        for name in ("plasma_palette",):
            import sys
            sys.modules.pop(name, None)
        spec = importlib.util.spec_from_file_location("plasma_theme_under_test", SCRIPTS / "plasma-theme.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def set_skin(self, skin):
        cfg = self.config / "illogical-impulse"
        cfg.mkdir(exist_ok=True)
        (cfg / "config.json").write_text(json.dumps({"appearance": {"bwmTheme": skin}}))

    # ── paleta
    def test_native_global_theme_defaults_are_read_with_local_overrides(self):
        system = self.config.parent / "system"
        system.mkdir()
        (system / "kdeglobals").write_text("[General]\nColorScheme=System\n[Icons]\nTheme=system-icons\n")
        defaults = self.config / "kdedefaults"
        defaults.mkdir()
        (defaults / "kdeglobals").write_text("[General]\nColorScheme=FromGlobalTheme\n[Icons]\nTheme=global-icons\n")
        (self.config / "kdeglobals").write_text("[Icons]\nTheme=explicit-user-icons\n")
        with mock.patch.dict(os.environ, {"XDG_CONFIG_DIRS": str(system)}):
            palette = self.mod.plasma_palette
            scheme = palette.load()
            self.assertEqual(scheme.name, "FromGlobalTheme")
            self.assertEqual(scheme.sections["Icons"]["Theme"], "explicit-user-icons")
            self.assertEqual(palette.load(palette.KDEGLOBALS).name, "FromGlobalTheme")
            self.assertEqual(palette.load(self.data / "color-schemes/TestLight.colors").name, "TestLight")

    def test_palette_follows_scheme(self):
        pal = self.mod.plasma_palette
        dark = pal.load(self.data / "color-schemes" / "TestDark.colors")
        light = pal.load(self.data / "color-schemes" / "TestLight.colors")
        self.assertTrue(dark.dark)
        self.assertFalse(light.dark)
        self.assertEqual(pal.m3(dark)["background"], "#202326")
        self.assertEqual(pal.m3(light)["primary"], "#c85014")
        self.assertEqual(pal.m3(light)["on_surface"], "#232629")
        # Lo que el esquema no trae sale de los valores por defecto de Breeze, nunca vacío
        self.assertEqual(pal.m3(light)["error"], "#da4453")
        self.assertIn("background #ffffff", pal.kitty(light))
        self.assertIn("color0 #fcfcfc", pal.kitty(light))
        self.assertIn("color0 #232627", pal.kitty(dark))
        self.assertIn('accent = "rgba(c85014ee)"', pal.hypr_lua(light))

    def test_accent_color_overrides_selection(self):
        pal = self.mod.plasma_palette
        s = pal.Scheme({"General": {"AccentColor": "#ff0000"}})
        self.assertEqual(pal.m3(s)["primary"], "#ff0000")
        s = pal.Scheme({"General": {"AccentColor": "#ff0000", "accentColorFromWallpaper": "true"}})
        self.assertEqual(pal.m3(s)["primary"], "#3daee9")

    # ── aplicador
    def test_colors_replace_groups_and_keep_the_rest(self):
        (self.config / "kdeglobals").write_text("[General]\nfont=Foo,10\n\n[Colors:Window]\nBackgroundNormal=1,2,3\n\n[Icons]\nTheme=x\n")
        self.assertEqual(self.mod.apply_colors("TestLight", sync_after=False), 0)
        k = ini(self.config / "kdeglobals")
        self.assertEqual(k["General"]["ColorScheme"], "TestLight")
        self.assertEqual(k["General"]["font"], "Foo,10")
        self.assertEqual(k["Icons"]["Theme"], "x")
        self.assertEqual(k["Colors:Window"]["BackgroundNormal"], "239,240,241")
        self.assertEqual(self.mod.apply_colors("NoSuchScheme"), 1)

    def test_lookandfeel_skips_cursor_and_wallpaper(self):
        self.assertEqual(self.mod.apply_lookandfeel("test.light", sync_after=False), 0)
        k = ini(self.config / "kdeglobals")
        self.assertEqual(k["General"]["ColorScheme"], "TestLight")
        self.assertEqual(k["Icons"]["Theme"], "test-icons")
        self.assertEqual(k["KDE"]["LookAndFeelPackage"], "test.light")
        self.assertEqual(ini(self.config / "plasmarc")["Theme"]["name"], "test-style")
        self.assertEqual(ini(self.config / "kwinrc")["org.kde.kdecoration2"]["library"], "org.kde.breeze")
        self.assertFalse((self.config / "kcminputrc").exists(), "el cursor es común: lo manda BWM")
        self.assertEqual(self.mod.main(["cursor", "breeze_cursors"]), 2)

    def test_lists_use_plasma_folders(self):
        self.assertEqual([i["id"] for i in self.mod.list_colors()], ["TestDark", "TestLight"])
        self.assertEqual(self.mod.list_desktopthemes()[0]["name"], "Test Style")
        self.assertEqual(self.mod.list_icons()[0]["name"], "Test Icons")
        self.assertEqual(self.mod.apply_desktoptheme("Test Style"), 0)
        self.assertEqual(ini(self.config / "plasmarc")["Theme"]["name"], "test-style")

    def test_first_restore_replaces_bwm_palette_with_breeze_dark(self):
        (self.config / "kdeglobals").write_text("[BWM]\nGenerated=x\n\n[General]\nColorScheme=BWM\nfont=Foo,10\n\n"
                                                "[Colors:Window]\nBackgroundNormal=1,2,3\n\n[KDE]\nwidgetStyle=Fusion\n")
        self.assertEqual(self.mod.restore(), 0)
        k = ini(self.config / "kdeglobals")
        self.assertFalse(k.has_section("BWM"))
        self.assertEqual(k["General"]["ColorScheme"], "TestDark")
        self.assertEqual(k["General"]["font"], "Foo,10")
        self.assertEqual(k["KDE"]["widgetStyle"], "Breeze")
        palette = json.loads((self.state / "bwm" / "plasma" / "colors.json").read_text())
        self.assertTrue(palette["darkmode"])
        self.assertEqual(self.manager_calls, [], "restore no vuelve a aplicar: lo hace el gestor después")

    def test_save_and_restore_round_trip(self):
        self.mod.apply_colors("TestLight", sync_after=False)
        original = (self.config / "kdeglobals").read_text()
        self.assertEqual(self.mod.save(), 0)
        # Otra skin escribe su kdeglobals de BWM…
        (self.config / "kdeglobals").write_text("[BWM]\nGenerated=x\n")
        self.mod.save()  # …y guardarlo no pisa el de Breeze
        self.assertEqual((self.state / "bwm" / "plasma" / "kdeglobals").read_text(), original)
        self.mod.restore()
        self.assertEqual((self.config / "kdeglobals").read_text(), original)

    def test_sync_only_reapplies_inside_breeze(self):
        self.mod.apply_colors("TestLight", sync_after=False)
        self.mod.save()
        self.set_skin("retro")
        (self.config / "kdeglobals").write_text("[BWM]\nGenerated=x\n")
        self.mod.sync()
        palette = json.loads((self.state / "bwm" / "plasma" / "colors.json").read_text())
        self.assertEqual(palette["scheme"], "TestLight", "fuera de Breeze se usa el kdeglobals guardado")
        self.assertEqual(self.manager_calls, [])
        self.set_skin("plasma")
        self.mod.apply_colors("TestDark")
        self.assertEqual(len(self.manager_calls), 1)
        self.assertEqual(json.loads((self.state / "bwm" / "plasma" / "colors.json").read_text())["scheme"], "TestDark")


if __name__ == "__main__":
    unittest.main()
