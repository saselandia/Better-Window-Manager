"""Regresiones de snapping en límites entre pantallas y con escalas distintas."""
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'config/hypr/scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('quick_tile', SCRIPTS / 'quick-tile.py')
qt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qt)

HP = {'id': 1, 'description': 'HP principal', 'x': 0, 'y': 1080,
      'width': 1920, 'height': 1080, 'scale': 1, 'reserved': [0, 0, 0, 44],
      'activeWorkspace': {'id': 1}}
LG = {'id': 0, 'description': 'LG derecha', 'x': 1920, 'y': 0,
      'width': 3840, 'height': 2160, 'scale': 1, 'reserved': [0, 0, 0, 44],
      'activeWorkspace': {'id': 10}}


class QuickTileTests(unittest.TestCase):
    def test_monitor_at_shared_edge_is_not_window_monitor(self):
        self.assertEqual(qt.drag_monitor([LG, HP], {'x': 1919, 'y': 1500}, 'right'), HP)
        # Unos píxeles después de cruzar sigue siendo el borde derecho que se mostró.
        self.assertEqual(qt.drag_monitor([LG, HP], {'x': 1921, 'y': 1500}, 'right'), HP)
        self.assertEqual(qt.drag_monitor([LG, HP], {'x': 1921, 'y': 1500}, 'left'), LG)

    def test_fractional_scale_and_real_top_panel(self):
        mon = {'x': -2560, 'y': 0, 'width': 3840, 'height': 2160, 'scale': 1.5,
               'reserved': [0, 40, 0, 0]}
        self.assertEqual(qt.usable_geometry(mon), (-2560, 40, 2560, 1400))

    def test_rotated_monitor_and_no_phantom_panel(self):
        mon = {'x': 0, 'y': 0, 'width': 1920, 'height': 1080, 'scale': 1,
               'transform': 1, 'reserved': [0, 0, 0, 0]}
        self.assertEqual(qt.usable_geometry(mon), (0, 0, 1080, 1920))

    def test_titlebar_stays_inside_preview(self):
        self.assertEqual(qt.content_geometry(960, 1080, 960, 1036, 30), (960, 1110, 960, 1006))

    def exercise(self, args, windows=None):
        import json
        win = {'address': '0xabc', 'pid': 17, 'monitor': 0, 'workspace': {'id': 10},
               'at': [1800, 1200], 'size': [1200, 700], 'floating': True,
               'tags': ['snapped', 'snapped_right'], 'class': 'test', 'title': 'test'}
        def output(command):
            if command[1] == 'clients': return json.dumps([win] if windows is None else windows).encode()
            if command[1] == 'monitors': return json.dumps([LG, HP]).encode()
            if command[1] == 'cursorpos': return b'{"x":1919,"y":1500}'
            if command[1] == 'activewindow': return json.dumps(win).encode()
            raise AssertionError(command)
        with patch.object(qt.subprocess, 'check_output', side_effect=output) as out, \
                patch.object(qt, 'is_plasma_active', return_value=False), \
                patch.object(qt, 'save_presnap'), patch.object(qt, 'run_lua') as lua:
            qt.main(args)
        return lua, out

    def test_legacy_plugin_drop_applies_primary_right_without_toggle_restore(self):
        lua, _ = self.exercise(['right', '0xabc'])
        code = lua.call_args.args[0]
        self.assertIn('x = 960, y = 1080', code)
        self.assertIn('x = 960, y = 1036', code)
        self.assertIn('workspace = 1, follow = false', code)
        self.assertIn('snapped_right', code)
        self.assertIn("action = 'enable'", code)

    def test_explicit_preview_monitor_wins(self):
        lua, out = self.exercise(['right', '0xabc', '--monitor', 'desc:HP principal', '--pid', '17', '--edge'])
        self.assertIn('x = 960, y = 1080', lua.call_args.args[0])
        self.assertFalse(any(call.args[0][1] == 'cursorpos' for call in out.call_args_list))

    def test_workspace_transfer_precedes_absolute_geometry(self):
        lua, _ = self.exercise(['right', '0xabc'])
        code = lua.call_args.args[0]
        self.assertLess(code.index('workspace = 1, follow = false'), code.index('window.resize'))
        self.assertEqual(code.count('workspace = 1, follow = false'), 1)

    def test_keyboard_targets_window_monitor_instead_of_pointer(self):
        lua, out = self.exercise(['top-right'])
        self.assertIn('x = 3840, y = 0', lua.call_args.args[0])
        self.assertFalse(any(call.args[0][1] == 'cursorpos' for call in out.call_args_list))

    def test_disappeared_window_never_snaps_active_window(self):
        lua, out = self.exercise(['right', '0xabc'], windows=[])
        lua.assert_not_called()
        self.assertFalse(any(call.args[0][1] == 'activewindow' for call in out.call_args_list))

    def test_reused_address_with_different_pid_does_nothing(self):
        lua, _ = self.exercise(['right', '0xabc', '--pid', '999'])
        lua.assert_not_called()


if __name__ == '__main__':
    unittest.main()
