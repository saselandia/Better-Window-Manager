"""Una fuente del perfil que no está instalada vuelve a la de la skin."""
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'config/hypr/scripts/bwm-theme-manager.py'
spec = importlib.util.spec_from_file_location('theme_manager', SCRIPT)
tm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tm)

DEFAULTS = {'main': 'Google Sans Flex', 'title': 'Google Sans Flex', 'reading': 'Readex Pro'}


class MissingFontsTest(unittest.TestCase):
    def test_missing_font_uses_the_skin_font(self):
        fonts = {'main': 'Rubik', 'title': 'Gabarito', 'reading': 'Readex Pro'}
        tm.replace_missing_fonts(fonts, DEFAULTS, installed={'google sans flex', 'readex pro'})
        self.assertEqual(fonts, {'main': 'Google Sans Flex', 'title': 'Google Sans Flex', 'reading': 'Readex Pro'})

    def test_installed_user_font_is_kept(self):
        fonts = {'main': 'Inter'}
        tm.replace_missing_fonts(fonts, DEFAULTS, installed={'inter', 'google sans flex'})
        self.assertEqual(fonts['main'], 'Inter')

    def test_no_change_if_the_skin_font_is_missing_too(self):
        fonts = {'main': 'Rubik'}
        tm.replace_missing_fonts(fonts, DEFAULTS, installed={'readex pro'})
        self.assertEqual(fonts['main'], 'Rubik')


if __name__ == '__main__':
    unittest.main()
