"""Apps Qt de default (end-4): el sustituto de plasma-apply-colorscheme y kdeglobals de BWM con el
esquema de kde-material-you-colors."""
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SHIM = ROOT / 'config/hypr/skins/default/scripts/kde-shims/plasma-apply-colorscheme'
spec = importlib.util.spec_from_file_location('bwm_icons', ROOT / 'config/hypr/scripts/bwm_icons.py')
icons = importlib.util.module_from_spec(spec)
spec.loader.exec_module(icons)

SCHEME = """[General]
Name=Material You Dark

[ColorEffects:Disabled]
Color=#1e1e16

[Colors:Window]
BackgroundNormal=#1e1e16
ForegroundNormal=#e6e3d5

[KDE]
contrast=4

[WM]
activeBackground=#1e1e16
"""
BWM_GLOBALS = """[BWM]
Generated=x

[General]
ColorScheme=BWM

[General]
font=Foo,10

[Colors:Window]
BackgroundNormal=1,2,3

[Colors:Header][Inactive]
BackgroundNormal=1,1,1

[KDE]
widgetStyle=Fusion

[Icons]
Theme=Adwaita
"""


class ShimTest(unittest.TestCase):
    def test_replaces_colour_groups_and_keeps_the_rest(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / '.config').mkdir()
            (home / '.config/kdeglobals').write_text(BWM_GLOBALS)
            scheme = home / 'MaterialYouDark.colors'
            scheme.write_text(SCHEME)
            env = {**os.environ, 'HOME': tmp, 'XDG_CONFIG_HOME': f'{tmp}/.config',
                   'XDG_DATA_HOME': f'{tmp}/.local/share', 'DBUS_SESSION_BUS_ADDRESS': 'disabled:'}
            out = subprocess.run([str(SHIM), str(scheme)], env=env, capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            text = (home / '.config/kdeglobals').read_text()
            self.assertIn('[BWM]', text)
            self.assertIn('ColorScheme=MaterialYouDark', text)
            self.assertIn('font=Foo,10', text)
            self.assertIn('BackgroundNormal=#1e1e16', text)
            self.assertNotIn('1,2,3', text)
            self.assertNotIn('Colors:Header][Inactive', text)
            self.assertIn('[ColorEffects:Disabled]', text)
            self.assertIn('contrast=4', text)
            self.assertIn('Theme=Adwaita', text)

    def test_unknown_scheme_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, 'HOME': tmp, 'XDG_DATA_HOME': f'{tmp}/share'}
            out = subprocess.run([str(SHIM), 'NoSuchScheme'], env=env, capture_output=True, text=True)
            self.assertNotEqual(out.returncode, 0)


class KdeglobalsTest(unittest.TestCase):
    def test_end4_scheme_replaces_bwm_colours(self):
        with tempfile.TemporaryDirectory() as tmp:
            scheme = Path(tmp) / 'MaterialYouDark.colors'
            scheme.write_text(SCHEME)
            with mock.patch.object(icons, '_darkly_installed', return_value=True):
                text = icons._with_end4_scheme(BWM_GLOBALS, scheme)
            self.assertIn('[BWM]', text)
            self.assertIn('ColorScheme=MaterialYouDark', text)
            self.assertIn('widgetStyle=Darkly', text)
            self.assertIn('font=Foo,10', text)
            self.assertNotIn('1,2,3', text)

    def test_only_default_with_qt_apps(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / '.config/illogical-impulse').mkdir(parents=True)
            schemes = home / 'schemes'
            schemes.mkdir()
            (schemes / 'MaterialYouDark.colors').write_text(SCHEME)
            config = home / '.config/illogical-impulse/config.json'
            dark = mock.Mock(stdout="'prefer-dark'\n")
            with mock.patch.object(icons, 'HOME', home), \
                    mock.patch.object(icons, 'COLOR_SCHEMES', schemes), \
                    mock.patch.object(icons.subprocess, 'run', return_value=dark):
                cases = [({'bwmTheme': 'default'}, True),
                         ({'bwmTheme': 'retro'}, False),
                         ({'bwmTheme': 'default', 'wallpaperTheming': {'enableQtApps': False}}, False)]
                for appearance, expected in cases:
                    config.write_text(json.dumps({'appearance': appearance}))
                    self.assertEqual(icons._end4_qt_scheme() is not None, expected, appearance)


if __name__ == '__main__':
    unittest.main()
