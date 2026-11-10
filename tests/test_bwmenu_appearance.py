"""Paletas nativas y seguimiento de temas sin cambiar el escritorio del usuario."""
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "config/hypr/scripts"
sys.path.insert(0, str(SCRIPTS))
import bwm_menu_appearance as appearance


class AppearanceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = Path(self.temp.name) / "config"
        self.state = Path(self.temp.name) / "state"

    def write(self, root, name, data):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data) if isinstance(data, dict) else data)
        return path

    def activate(self, skin):
        self.write(self.config, "illogical-impulse/config.json", {"appearance": {"bwmTheme": skin}})

    def test_material_palette_uses_generated_roles_and_manifest_shapes(self):
        self.activate("default")
        self.write(self.state, "quickshell/user/generated/colors.json", {
            "background": "#faf8ff", "on_background": "#191b20", "primary": "#4c5c92", "surface_container_high": "#ebe8f0"})
        data = appearance.appearance(self.config, self.state)
        self.assertEqual(data["background"], "#faf8ff")
        self.assertEqual(data["foreground"], "#191b20")
        self.assertEqual(data["accent"], "#4c5c92")
        self.assertEqual(data["radius"], 18)
        self.assertEqual(data["onAccent"], "#ffffff")
        self.assertEqual({s["id"] for s in data["skins"]}, {"default", "retro", "plasma"})

    def test_omarchy_light_theme_and_user_override_use_native_toml(self):
        self.activate("retro")
        self.write(self.state, "bwm/omarchy/colors.toml", 'background = "#ffffff"\nforeground = "#222222"\naccent = "#7755cc"\n')
        self.write(self.state, "bwm/omarchy/shell.toml", '[menu]\nbackground = "background"\ntext = "foreground"\n')
        self.write(self.config, "omarchy/shell.toml", '[menu]\nbackground = "#f0f0f0"\n')
        self.write(self.state, "bwm/omarchy/theme.mode", "static")
        self.write(self.state, "bwm/omarchy/theme.name", "white")
        data = appearance.appearance(self.config, self.state)
        self.assertEqual(data["background"], "#f0f0f0")
        self.assertEqual(data["foreground"], "#222222")
        self.assertEqual(data["themeName"], "White")
        self.assertEqual(data["radius"], 0)
        self.assertIn("Mono", data["font"])

    def test_breeze_reads_kde_color_scheme(self):
        self.activate("plasma")
        self.write(self.config, "kdeglobals", '[General]\nColorScheme=BreezeLight\n[Colors:Window]\nBackgroundNormal=240,241,242\nForegroundNormal=20,21,22\n[Colors:Selection]\nBackgroundNormal=61,174,233\n')
        data = appearance.appearance(self.config, self.state)
        self.assertEqual(data["background"], "#f0f1f2")
        self.assertEqual(data["accent"], "#3daee9")
        self.assertEqual(data["themeName"], "BreezeLight")
        self.assertEqual(data["radius"], 12)

    def test_omarchy_alias_cycle_is_safe_and_gradients_use_first_color(self):
        self.assertEqual(appearance.omarchy_color("menu.background", {"menu": {"background": "menu.background"}}, {}, "#000000"), "#000000")
        self.assertEqual(appearance.color("rgba(81a1c1ff) rgba(ffffff00) 45deg", "#000000"), "#81a1c1")
        self.assertEqual(appearance.color("malicious\x1b[2J", "#000000"), "#000000")

    def test_malformed_optional_profile_fields_do_not_break_rescue_appearance(self):
        self.write(self.config, "illogical-impulse/config.json", {"appearance": [], "background": ["invalid"]})
        data = appearance.appearance(self.config, self.state)
        self.assertIsInstance(data["font"], str)
        self.assertEqual(data["skin"], "default")

    def test_palette_file_replacement_updates_the_same_watcher(self):
        self.activate("default")
        path = self.write(self.state, "quickshell/user/generated/colors.json", {"primary": "#81a1c1"})
        code = "import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); import bwm_menu_appearance as m; import bwm_session; bwm_session.theme_manager_busy=lambda:False; m.watch(Path(sys.argv[2]),Path(sys.argv[3]))"
        proc = subprocess.Popen([sys.executable, "-u", "-c", code, str(SCRIPTS), str(self.config), str(self.state)], stdout=subprocess.PIPE, text=True)
        try:
            self.assertTrue(select.select([proc.stdout], [], [], 4)[0])
            first = json.loads(proc.stdout.readline())
            self.assertEqual(first["accent"], "#81a1c1")
            replacement = path.with_suffix(".new")
            replacement.write_text(json.dumps({"primary": "#d3869b"}))
            replacement.replace(path)
            self.assertTrue(select.select([proc.stdout], [], [], 4)[0])
            changed = json.loads(proc.stdout.readline())
            self.assertEqual(changed["accent"], "#d3869b")
            self.assertIsNone(proc.poll())
            self.assertFalse(select.select([proc.stdout], [], [], .5)[0])
        finally:
            proc.terminate()
            proc.wait(timeout=4)
            proc.stdout.close()


if __name__ == "__main__":
    unittest.main()
