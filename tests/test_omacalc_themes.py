"""Native Omacalc palettes from real Omarchy themes and Matugen wallpapers."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "config/hypr/scripts"
sys.path.insert(0, str(SCRIPTS))
import bwm_omarchy as retro

TEMPLATE = ROOT / "config/matugen/templates/omacalc-colors.toml"


class OmacalcThemesTest(unittest.TestCase):
    def test_static_themes_keep_the_original_omacalc_colors(self):
        for name in ("gruvbox", "catppuccin-latte", "tokyo-night"):
            with self.subTest(theme=name):
                colors = retro.complete_colors(tomllib.loads((retro.theme_directory(name) / "colors.toml").read_text()))
                actual = tomllib.loads(retro.render_matugen(TEMPLATE.read_text(), retro.m3_roles(colors), ""))
                self.assertEqual(actual, {key: colors[key] for key in ("background", "foreground", "accent", "selection")})

    def test_breeze_uses_its_shared_palette(self):
        # Breeze sigue el esquema de color de Plasma; sin esquema, los valores de Breeze Oscuro
        spec = importlib.util.spec_from_file_location("plasma_palette", ROOT / "config/hypr/skins/plasma/scripts/plasma_palette.py")
        plasma = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plasma)
        palette = tomllib.loads(retro.render_matugen(TEMPLATE.read_text(), plasma.m3(plasma.Scheme({})), ""))
        self.assertEqual(palette["background"], "#202326")
        self.assertEqual(palette["accent"], "#3daee9")

    def test_retro_dynamic_colors_follow_the_wallpaper(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as folder:
            accents = []
            for name, color in (("red", "#dd3344"), ("blue", "#3366dd")):
                image = Path(folder) / (name + ".png")
                Image.new("RGB", (64, 64), color).save(image)
                colors = retro.complete_colors(retro.build_colors(retro.extract_vivid_palette(str(image))))
                palette = tomllib.loads(retro.render_matugen(TEMPLATE.read_text(), retro.m3_roles(colors), ""))
                self.assertEqual(palette["accent"], colors["accent"])
                accents.append(palette["accent"])
            self.assertNotEqual(*accents)

    @unittest.skipUnless(shutil.which("matugen"), "Real default palettes require Matugen")
    def test_default_dynamic_colors_and_light_mode(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            output = folder / "colors.toml"
            config = folder / "matugen.toml"
            config.write_text('[config]\nreload_apps = false\nsource_color_index = 0\n'
                              '[templates.omacalc]\ninput_path = ' + json.dumps(str(TEMPLATE))
                              + '\noutput_path = ' + json.dumps(str(output)) + '\n')
            palettes = []
            for name, color, mode in (("red", "#dd3344", "dark"), ("blue", "#3366dd", "dark"),
                                      ("light", "#3366dd", "light")):
                image = folder / (name + ".png")
                Image.new("RGB", (64, 64), color).save(image)
                subprocess.run(["matugen", "image", str(image), "--mode", mode, "--config", str(config)],
                               check=True, capture_output=True, timeout=15)
                palettes.append(tomllib.loads(output.read_text()))
            self.assertNotEqual(palettes[0]["accent"], palettes[1]["accent"])
            self.assertNotEqual(palettes[1]["background"], palettes[2]["background"])
            for palette in palettes:
                for value in palette.values():
                    self.assertRegex(value, r"^#[0-9a-fA-F]{6}$")


if __name__ == "__main__":
    unittest.main()
