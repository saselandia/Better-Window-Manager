"""Cada skin (config/hypr/skins/<id>/skin.json) está completa y bien formada."""
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKINS = REPO / 'config/hypr/skins'
sys.path.insert(0, str(REPO / 'config/hypr/scripts'))
import bwm_skins

REQUIRED = ('id', 'name', 'imitates', 'description', 'preview', 'windows', 'palette',
            'defaultTheme', 'themes', 'look', 'bar', 'fonts', 'parts', 'requires')


class SkinManifestTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((SKINS / 'requirements.json').read_text())['catalog']
        self.skins = bwm_skins.all_skins()

    def test_release_skins_are_found_and_template_is_not(self):
        ids = [s['id'] for s in self.skins]
        for sid in ('default', 'retro', 'plasma'):
            self.assertIn(sid, ids)
        self.assertNotIn('mi-skin', ids)

    def test_every_skin_has_its_fields_and_folder_matches_id(self):
        for s in (x for x in self.skins if x['builtin']):
            for key in REQUIRED:
                self.assertIn(key, s, f'{s["id"]}: falta "{key}"')
            self.assertEqual(Path(s['dir']).name, s['id'])
            self.assertIn(s['palette'], ('matugen', 'omarchy', 'breeze'))

    def test_windows_variable(self):
        for s in self.skins:
            self.assertIn(s['windows'], bwm_skins.WINDOWS, s['id'])
            if s['windows'] == 'traditional':
                block = s.get('traditional', {})
                for key in ('titlebar', 'panel', 'edgeMargin', 'gap'):
                    self.assertIn(key, block, f'{s["id"]}: traditional sin "{key}"')
            else:
                self.assertNotIn('traditional', s, f'{s["id"]}: tiling no lleva bloque traditional')
        self.assertEqual(bwm_skins.windows('plasma'), 'traditional')
        self.assertEqual(bwm_skins.windows('retro'), 'tiling')
        self.assertEqual(bwm_skins.windows('no-existe'), 'tiling')

    def test_parts_exist(self):
        for s in (x for x in self.skins if x['builtin']):
            for group, paths in s['parts'].items():
                for path in paths:
                    self.assertTrue((REPO / path).exists(), f'{s["id"]}.parts.{group}: no existe {path}')

    def test_requirements_are_in_the_catalog(self):
        for s in self.skins:
            catalog = {**self.catalog, **s.get('catalog', {})}
            for rid in s.get('requires', []) + s.get('recommends', []):
                self.assertIn(rid, catalog, f'{s["id"]}: requisito desconocido {rid}')

    def test_theme_table_has_what_the_manager_uses(self):
        table = bwm_skins.theme_table(Path('/tmp'))
        for sid, cfg in table.items():
            for key in ('rounding', 'rounding_power', 'border_size', 'gaps_in', 'gaps_out', 'bar_height',
                        'bar_bottom', 'bar_corner_style', 'show_app_icons', 'always_show_numbers', 'fonts',
                        'btop_rounded', 'wallpaper', 'windows', 'is_retro', 'is_plasma'):
                self.assertIn(key, cfg, f'{sid}: falta {key}')
        self.assertTrue(table['plasma']['is_plasma'] and table['retro']['is_retro'])

    def test_template_is_valid_json_with_every_field(self):
        template = json.loads((SKINS / '_template/skin.json').read_text())
        for key in REQUIRED:
            self.assertIn(key, template)
        self.assertIn(template['windows'], bwm_skins.WINDOWS)


if __name__ == '__main__':
    unittest.main()
