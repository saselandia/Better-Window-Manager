"""Lanzador de Stremio sin barra de título GTK: copia del de Flatpak con --no-window-decorations,
sin pisar uno propio del usuario."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / 'config/hypr/scripts/stremio-theme.py'
spec = importlib.util.spec_from_file_location('stremio_theme', SCRIPT)
st = importlib.util.module_from_spec(spec)
spec.loader.exec_module(st)

DESKTOP = """[Desktop Entry]
Name=Stremio
Exec=/usr/bin/flatpak run --branch=stable --command=stremio --file-forwarding com.stremio.Stremio @@u %u @@
"""


class LauncherTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        exports = self.base / 'exports'
        exports.mkdir()
        (exports / 'com.stremio.Stremio.desktop').write_text(DESKTOP)
        self.launcher = self.base / 'apps/com.stremio.Stremio.desktop'
        for name, value in (('EXPORTS', (exports,)), ('LAUNCHER', self.launcher)):
            patcher = mock.patch.object(st, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_adds_the_flag_after_the_app_id(self):
        st.launcher()
        text = self.launcher.read_text()
        self.assertIn('com.stremio.Stremio --no-window-decorations @@u %u @@', text)
        self.assertIn(st.MARK, text)
        st.launcher()
        self.assertEqual(text.count('--no-window-decorations'), self.launcher.read_text().count('--no-window-decorations'))

    def test_keeps_the_users_own_launcher(self):
        self.launcher.parent.mkdir(parents=True)
        self.launcher.write_text('[Desktop Entry]\nExec=mi-stremio\n')
        st.launcher()
        self.assertEqual(self.launcher.read_text(), '[Desktop Entry]\nExec=mi-stremio\n')


if __name__ == '__main__':
    unittest.main()
