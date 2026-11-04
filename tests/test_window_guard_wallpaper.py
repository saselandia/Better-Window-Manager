"""window-guard: un monitor que vuelve en negro (swww muestra un color) recibe otra vez el fondo."""
import importlib.util
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / 'config/hypr/scripts/window-guard.py'
spec = importlib.util.spec_from_file_location('window_guard', SCRIPT)
wg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wg)

QUERY = (": DP-1: 3840x2160, scale: 1, currently displaying: image: /w.jpg\n"
         ": DP-2: 2560x1440, scale: 1, currently displaying: color: 000000\n")


class WallpaperTest(unittest.TestCase):
    def test_black_outputs_only_color(self):
        with mock.patch.object(wg.subprocess, 'run', return_value=mock.Mock(stdout=QUERY)):
            self.assertEqual(wg.black_outputs(), ['DP-2'])

    def test_restore_targets_black_output(self):
        calls = []

        def run(cmd, **kw):
            calls.append(cmd)
            if cmd[:2] == ['pgrep', '-x']:
                return mock.Mock(returncode=1)
            return mock.Mock(stdout=QUERY if len(calls) < 3 else QUERY.replace('color: 000000', 'image: /w.jpg'))
        with mock.patch.object(wg, 'WALL_BIN', 'swww'), \
                mock.patch.object(wg, 'current_wallpaper', return_value='/w.jpg'), \
                mock.patch.object(wg.subprocess, 'run', side_effect=run), \
                mock.patch.object(wg.time, 'sleep'):
            wg.restore_wallpapers()
        img = [c for c in calls if c[1:2] == ['img']]
        self.assertEqual(len(img), 1)
        self.assertEqual(img[0][img[0].index('--outputs') + 1], 'DP-2')

    def test_video_wallpaper_is_left_alone(self):
        with mock.patch.object(wg, 'WALL_BIN', 'swww'), \
                mock.patch.object(wg.subprocess, 'run', return_value=mock.Mock(returncode=0)) as run:
            wg.restore_wallpapers()
        self.assertEqual(run.call_count, 1)  # sólo el pgrep de mpvpaper


if __name__ == '__main__':
    unittest.main()
