"""Regresiones del cambio de skin: no interrumpir apps ni cambiar el foco sin necesidad."""
import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'config/hypr/scripts'
sys.path.insert(0, str(SCRIPTS))
import bwm_transition
import bwm_windows
import bwm_omarchy

spec = importlib.util.spec_from_file_location('reload_spotify', SCRIPTS / 'reload-spotify.py')
spotify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(spotify)


class SkinSwitchTests(unittest.TestCase):
    def test_detached_hooks_inherit_policy_and_parent_recovers(self):
        previous = os.environ.get('BWM_SKIN_SWITCH')
        with bwm_transition.skin_change():
            self.assertTrue(bwm_transition.switching())
            with patch('subprocess.run') as run, patch('subprocess.Popen') as popen, patch('os.kill') as kill:
                self.assertFalse(bwm_omarchy.restart_app(lambda _: True, ['firefox']))
                bwm_omarchy.restart_firefox()
                bwm_omarchy.restart_steam()
                spotify.main()
                run.assert_not_called()
                popen.assert_not_called()
                kill.assert_not_called()
        self.assertEqual(os.environ.get('BWM_SKIN_SWITCH'), previous)

    def test_unchanged_session_does_not_refocus_monitors(self):
        mon = {'name': 'test-output', 'description': 'test monitor', 'focused': True,
               'activeWorkspace': {'id': 3}}
        win = {'address': '0x1', 'pid': 17, 'workspace': {'id': 3}}
        snap = {'workspaces': {'test-output': 3}, 'focused_monitor': 'test-output',
                'window': '0x1', 'window_pid': 17, 'playing': []}
        values = {'monitors': [mon], 'clients': [win], 'activewindow': win}
        with patch.object(bwm_windows, 'hypr_json', side_effect=values.get), \
                patch.object(bwm_windows, 'dispatch') as dispatch, \
                patch.object(bwm_windows, 'mpris_playing', return_value=[]):
            bwm_windows.restore_focus(snap)
        dispatch.assert_called_once_with([])

    def test_reused_address_does_not_focus_another_workspace(self):
        mon = {'name': 'test-output', 'focused': True, 'activeWorkspace': {'id': 1}}
        reused = {'address': '0x1', 'pid': 99, 'workspace': {'id': 4}}
        snap = {'workspaces': {'test-output': 1}, 'focused_monitor': 'test-output',
                'window': '0x1', 'window_pid': 17, 'playing': []}
        values = {'monitors': [mon], 'clients': [reused], 'activewindow': {'address': '0x2'}}
        with patch.object(bwm_windows, 'hypr_json', side_effect=values.get), \
                patch.object(bwm_windows, 'dispatch') as dispatch, \
                patch.object(bwm_windows, 'mpris_playing', return_value=[]):
            bwm_windows.restore_focus(snap)
        dispatch.assert_called_once_with([])

    def test_stacking_keeps_fullscreen_and_hidden_workspaces_untouched(self):
        base = {'at': [0, 0], 'size': [1000, 700], 'pid': 1, 'monitor': 1,
                'mapped': True, 'floating': False}
        clients = [{**base, 'address': '0x1', 'workspace': {'id': 1}},
                   {**base, 'address': '0x2', 'workspace': {'id': 2}, 'fullscreen': 2},
                   {**base, 'address': '0x3', 'workspace': {'id': 99}},
                   {**base, 'address': '0x4', 'workspace': {'id': -1}}]
        mon = {'id': 1, 'x': 0, 'y': 0, 'width': 1920, 'height': 1080, 'scale': 1}
        with patch.object(bwm_windows, 'hypr_json', return_value=[mon]), \
                patch.object(bwm_windows, 'titlebars', return_value=set()), \
                patch.object(bwm_windows, 'dispatch') as dispatch:
            self.assertEqual(bwm_windows.float_in_place('plasma', clients), 1)
        lua = dispatch.call_args.args[0][0]
        self.assertIn("action = 'enable'", lua)
        self.assertIn('address:0x1', lua)
        self.assertNotIn('address:0x2', lua)
        self.assertNotIn('follow = true', lua)


if __name__ == '__main__':
    unittest.main()
