import importlib.util
import unittest
import sys
from unittest import mock
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "config/hypr/scripts/toggle-minimize.py"
sys.path.insert(0, str(SCRIPT.parent))
spec = importlib.util.spec_from_file_location("toggle_minimize", SCRIPT)
tm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tm)


class MinimizeTests(unittest.TestCase):
    def test_explicit_desktop_enter_is_idempotent_with_hidden_windows(self):
        client={'address':'0xabc','workspace':{'id':-98,'name':'special:minimized'}}
        with mock.patch.object(tm,'read_show_desktop_state',return_value=['0xabc']), \
             mock.patch.object(tm,'restore_win') as restore, mock.patch.object(tm,'minimize_win') as minimize, \
             mock.patch.object(tm,'write_show_desktop_state') as write:
            tm.show_desktop([client],enter=True)
        restore.assert_not_called();minimize.assert_not_called();write.assert_not_called()
    def test_special_workspace_and_legacy_99_are_minimized(self):
        self.assertTrue(tm.is_minimized({"workspace": {"id": -98, "name": "special:minimized"}}))
        self.assertTrue(tm.is_minimized({"workspace": {"id": 99, "name": "99"}}))
        self.assertFalse(tm.is_minimized({"workspace": {"id": 3, "name": "3"}}))
        self.assertFalse(tm.is_minimized({"workspace": {"id": -97, "name": "special:magic"}}))

    def test_origin_from_omarchy_and_legacy_tags(self):
        self.assertEqual(tm.origin_workspace({"tags": ["terminal*", "omarchy-minimized-from-4"]}), 4)
        self.assertEqual(tm.origin_workspace({"tags": ["from_ws_7"]}), 7)
        self.assertIsNone(tm.origin_workspace({"tags": ["from_ws_99", "snapped_left"]}))

    def test_only_minimize_tags_are_removed(self):
        tags = ["snapped_left", "omarchy-minimized-from-2", "from_ws_2*", "omarchy-floating-workspace"]
        self.assertEqual(tm.minimize_tags({"tags": tags}), ["omarchy-minimized-from-2", "from_ws_2"])


    def test_special_origin_round_trip_and_cleanup(self):
        for name in ('special:magic', 'special', 'special:mi espacio', 'special:日本語'):
            c = {'address': '0x123', 'pid': 17, 'workspace': {'id': -97, 'name': name}}
            with mock.patch.object(tm, 'run_lua') as run:
                tm.minimize_win(c)
            tag = tm.SPECIAL_TAG_PREFIX + name.encode().hex()
            self.assertIn('+' + tag, run.call_args.args[0])
            hidden = dict(c, workspace={'id': -98, 'name': tm.MINIMIZED_WS}, tags=[tag + '*'])
            self.assertEqual(tm.origin_workspace(hidden), name)
            with mock.patch.object(tm, 'load_geometries', return_value={}), mock.patch.object(tm, 'run_lua') as run:
                tm.restore_win(hidden)
            code = run.call_args.args[0]
            self.assertIn('local target = ' + tm.json.dumps(name, ensure_ascii=False), code)
            self.assertIn('w.pid == 17', code)
            self.assertIn('-' + tag, code)
            self.assertLess(code.index('workspace = target'), code.index('workspace = ws.name'))

    def test_bad_special_origin_never_targets_storage_or_normal_names(self):
        for suffix in ('zz', 'ff', 'minimized', '3'.encode().hex(), tm.MINIMIZED_WS.encode().hex()):
            self.assertIsNone(tm.origin_workspace({'tags': [tm.SPECIAL_TAG_PREFIX + suffix]}))

    def test_reused_address_never_receives_previous_geometry(self):
        c = {'address': '0x123', 'pid': 17, 'floating': True, 'tags': ['omarchy-minimized-from-2']}
        for pid, has_geometry in ((99, False), (17, True)):
            cached = {'0x123': {'pid': pid, 'generation': '', 'at': [20, 30], 'size': [400, 300]}}
            with mock.patch.object(tm, 'load_geometries', return_value=cached), mock.patch.object(tm, 'save_geometries'), mock.patch.object(tm.bwm_windows, 'process_generation', return_value=''), mock.patch.object(tm, 'run_lua') as run:
                tm.restore_win(c)
            self.assertEqual('hl.dsp.window.resize' in run.call_args.args[0], has_geometry)


if __name__ == "__main__":
    unittest.main()
