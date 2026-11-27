# SPDX-License-Identifier: GPL-2.0-or-later
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "config/hypr/scripts"
sys.path.insert(0, str(SCRIPTS))

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded

class ActionsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="bwm-t6-actions-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        env = patch.dict(os.environ, XDG_RUNTIME_DIR=str(self.root), XDG_CONFIG_HOME=str(self.root))
        env.start(); self.addCleanup(env.stop)
        self.actions = module("t6_actions", ROOT / "config/hypr/skins/plasma/scripts/desktop-actions.py")
        (self.root / "illogical-impulse").mkdir()
        (self.root / "illogical-impulse/config.json").write_text('{"appearance":{"bwmTheme":"plasma"}}')
        self.factor = 1.0
        def run(*args):
            if args[1] == "getoption": return json.dumps({"float": self.factor})
            self.factor = float(re.search(r"zoom_factor=([0-9.]+)", args[2]).group(1))
            return "ok"
        fake = patch.object(self.actions, "run", side_effect=run)
        fake.start(); self.addCleanup(fake.stop)

    def test_zoom_changes_live_factor_in_both_directions_and_resets(self):
        self.actions.zoom("in"); self.assertAlmostEqual(self.factor, 1.2)
        self.actions.zoom("in"); self.assertAlmostEqual(self.factor, 1.44)
        self.actions.zoom("out"); self.assertAlmostEqual(self.factor, 1.2)
        self.actions.zoom("reset"); self.assertEqual(self.factor, 1)

    def test_zoom_is_bounded_and_leaving_restores_previous_factor(self):
        self.factor = 2
        for _ in range(20): self.actions.zoom("in")
        self.assertEqual(self.factor, 8)
        self.actions.zoom("leave"); self.assertEqual(self.factor, 2)
        self.assertFalse(self.actions.STATE.exists())

    def test_leaving_does_not_replace_an_external_zoom_change(self):
        self.actions.zoom("in"); self.factor = 3
        self.actions.zoom("leave"); self.assertEqual(self.factor, 3)

    def test_actions_only_run_in_breeze_and_emoji_uses_native_app(self):
        with patch.object(self.actions.shutil, "which", return_value="/usr/bin/plasma-emojier"), patch.object(self.actions.bwm_session, "spawn", return_value=True) as spawn:
            self.assertEqual(self.actions.main(["emoji"]), 0)
            spawn.assert_called_once_with(["/usr/bin/plasma-emojier"], allow_fallback=False)
        with patch.object(self.actions, "skin", return_value="retro"), patch.object(self.actions.bwm_session, "spawn") as spawn:
            self.assertEqual(self.actions.main(["emoji"]), 1)
            self.assertEqual(self.actions.zoom("in"), 1)
            spawn.assert_not_called()

class PortalTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="bwm-t6-portals-")
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        env = patch.dict(os.environ, XDG_CONFIG_HOME=str(root / "config"), XDG_RUNTIME_DIR=str(root / "runtime"), XDG_CONFIG_DIRS=str(root / "etc"), XDG_DATA_HOME=str(root / "data"), XDG_DATA_DIRS=str(root / "share"), XDG_CURRENT_DESKTOP="Hyprland")
        env.start(); self.addCleanup(env.stop)
        self.portal = module("t6_portals", SCRIPTS / "bwm_portals.py")
        self.source = self.portal.CONFIG / "xdg-desktop-portal/portals.conf"
        self.source.parent.mkdir(parents=True)
        self.source.write_text("[preferred]\ndefault=hyprland;gtk;\norg.freedesktop.impl.portal.FileChooser=gtk;\norg.freedesktop.impl.portal.ScreenCast=hyprland;\n")
        self.original = self.source.read_bytes()
        fake = patch.object(self.portal.subprocess, "run")
        self.run = fake.start(); self.addCleanup(fake.stop)

    def test_breeze_overrides_only_filechooser_in_a_service_scoped_profile(self):
        result = self.portal.apply("plasma")
        self.assertTrue(result["changed"])
        profile = (self.portal.PROFILE / "xdg-desktop-portal/portals.conf").read_text()
        self.assertIn("FileChooser=kde;gtk;", profile)
        self.assertIn("ScreenCast=hyprland;", profile)
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertIn("XDG_CONFIG_HOME=", self.portal.DROPIN.read_text())
        self.assertNotIn("XDG_CURRENT_DESKTOP", self.portal.DROPIN.read_text())
        self.assertEqual(self.run.call_count, 2)

    def test_identical_profile_does_not_restart_portal_again(self):
        self.portal.apply("plasma"); self.run.reset_mock()
        self.assertFalse(self.portal.apply("plasma")["changed"])
        self.run.assert_not_called()

    def test_leaving_to_either_other_skin_removes_override_and_preserves_source(self):
        for skin in ("default", "retro"):
            self.portal.apply("plasma")
            self.assertTrue(self.portal.apply(skin)["changed"])
            self.assertFalse(self.portal.DROPIN.exists())
            self.assertEqual(self.source.read_bytes(), self.original)

    def test_explicit_user_chooser_wins_and_removes_previous_override(self):
        self.portal.apply("plasma")
        self.source.write_text("[preferred]\norg.freedesktop.impl.portal.FileChooser=custom;\n")
        self.assertEqual(self.portal.apply("plasma")["overrides"], {})
        self.assertFalse(self.portal.DROPIN.exists())
        self.assertIn("custom;", self.source.read_text())

class KeybindTest(unittest.TestCase):
    def test_skin_filters_survive_add_update_and_reload(self):
        manager = module("t6_keybinds", SCRIPTS / "keybinds-manager.py")
        with tempfile.TemporaryDirectory(prefix="bwm-t6-binds-") as root:
            manager.CONFIG_DIR = root
            manager.JSON_PATH = str(Path(root) / "keybinds.json")
            manager.LUA_PATH = str(Path(root) / "user_binds.lua")
            Path(manager.JSON_PATH).write_text('[{"id":"original","enabled":false}]')
            with patch.object(manager.subprocess, "run"):
                self.assertTrue(manager.add_keybind("Tests", "Plasma action", ["SUPER"], "equal", "exec", "/test/action", skins=["plasma"]))
                bind = manager.load_keybinds()[-1]
                self.assertEqual(bind["skins"], ["plasma"])
                self.assertIn('active_skin == "plasma"', Path(manager.LUA_PATH).read_text())
                self.assertTrue(manager.update_keybind(bind["id"], skins_except=["plasma"]))
                bind = manager.load_keybinds()[-1]
                self.assertNotIn("skins", bind)
                self.assertEqual(bind["skins_except"], ["plasma"])
                self.assertTrue(manager.save_keybinds(manager.load_keybinds()))
                self.assertIn('active_skin ~= "plasma"', Path(manager.LUA_PATH).read_text())

    def test_factory_desktop_actions_and_requirements_are_skin_specific(self):
        manager = module("t6_factory", SCRIPTS / "keybinds-manager.py")
        actions = [b for b in manager.DEFAULT_KEYBINDS if b["id"] in ("plasma_zoom_in", "plasma_zoom_out", "plasma_zoom_reset", "plasma_emoji")]
        self.assertEqual(len(actions), 4)
        self.assertTrue(all(b["skins"] == ["plasma"] for b in actions))
        amplify = [b for b in manager.DEFAULT_KEYBINDS if (b.get("exec") or "").endswith("desktop-actions.py zoom in")]
        self.assertEqual({(tuple(b["mods"]), b["key"]) for b in amplify}, {
            (("SUPER",), "equal"), (("SUPER",), "plus"), (("SUPER", "SHIFT"), "equal"),
            (("SUPER", "SHIFT"), "0"), (("SUPER",), "KP_Add"),
        })
        keypad_out = next(b for b in manager.DEFAULT_KEYBINDS if b["id"] == "plasma_zoom_out_keypad")
        self.assertEqual(keypad_out["key"], "KP_Subtract")
        self.assertEqual(keypad_out["skins"], ["plasma"])
        skin = json.loads((ROOT / "config/hypr/skins/plasma/skin.json").read_text())
        self.assertIn("ksystemstats", skin["recommends"])
        self.assertIn("kdeplasma-addons", skin["recommends"])
        self.assertNotIn("powerdevil", skin["recommends"])

if __name__ == "__main__":
    unittest.main()
