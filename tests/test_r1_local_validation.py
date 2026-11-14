"""The local graphical test must fail closed when access or user state is unsuitable."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / 'config/hypr/scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('r1_local_test', SCRIPTS / 'bwm-r1-validate.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class LocalValidationSafetyTests(unittest.TestCase):
    def test_denied_ipc_never_launches_or_moves_anything(self):
        with tempfile.TemporaryDirectory() as temp, mock.patch.object(runner, 'query', side_effect=RuntimeError('IPC denied')), mock.patch.object(runner.subprocess, 'Popen') as spawn, mock.patch.object(runner, 'dispatch') as dispatch, mock.patch('builtins.print'):
            code = runner.main(['--run', '--report', str(Path(temp)/'report.json')])
            self.assertEqual(code, 1)
            spawn.assert_not_called()
            dispatch.assert_not_called()

    def test_occupied_magic_is_not_borrowed_for_the_test(self):
        values = {'version': {}, 'clients': [{'workspace': {'name': 'special:magic'}}], 'monitors': []}
        with tempfile.TemporaryDirectory() as temp, mock.patch.object(runner, 'query', side_effect=values.get), mock.patch.object(runner.shutil, 'which', return_value='/usr/bin/kitty'), mock.patch.object(runner.subprocess, 'Popen') as spawn, mock.patch.object(runner, 'dispatch') as dispatch, mock.patch('builtins.print'):
            self.assertEqual(runner.main(['--run', '--report', str(Path(temp)/'report.json')]), 1)
            spawn.assert_not_called()
            dispatch.assert_not_called()

    def test_read_only_preflight_has_no_fixture_actions(self):
        values = {'version': {'tag': 'test'}, 'clients': [], 'monitors': []}
        with tempfile.TemporaryDirectory() as temp, mock.patch.object(runner, 'query', side_effect=values.get), mock.patch.object(runner.subprocess, 'Popen') as spawn, mock.patch.object(runner, 'dispatch') as dispatch, mock.patch('builtins.print'):
            self.assertEqual(runner.main(['--report', str(Path(temp)/'report.json')]), 0)
            spawn.assert_not_called()
            dispatch.assert_not_called()

    def test_matrix_without_loaded_breeze_plugin_never_starts(self):
        values = {'version': {}, 'clients': [], 'monitors': []}
        with tempfile.TemporaryDirectory() as temp, mock.patch.object(runner, 'query', side_effect=values.get), mock.patch.object(runner.shutil, 'which', return_value='/usr/bin/kitty'), mock.patch.object(runner.windows, 'current_skin', return_value='retro'), mock.patch.object(runner, 'command', return_value='Plugin hyprbars'), mock.patch.object(runner.subprocess, 'Popen') as spawn, mock.patch.object(runner, 'dispatch') as dispatch, mock.patch('builtins.print'):
            self.assertEqual(runner.main(['--run', '--matrix', '--report', str(Path(temp)/'report.json')]), 1)
            spawn.assert_not_called()
            dispatch.assert_not_called()

    def test_matrix_detects_workspace_change(self):
        before = {'address': '0x1', 'pid': 17, 'workspace': {'name': '3'}, '_bwm_process_generation': 'old'}
        with mock.patch.object(runner.windows, 'process_generation', return_value='old'):
            with self.assertRaisesRegex(RuntimeError, 'workspace'):
                runner.assert_preserved([before], [dict(before, workspace={'name': '4'})])

    def test_matrix_detects_reused_pid_generation(self):
        before = {'address': '0x1', 'pid': 17, 'workspace': {'name': '3'}, '_bwm_process_generation': 'old'}
        now = {k: v for k, v in before.items() if k != '_bwm_process_generation'}
        with mock.patch.object(runner.windows, 'process_generation', return_value='new'):
            with self.assertRaisesRegex(RuntimeError, 'disappeared'):
                runner.assert_preserved([before], [now])

    def test_manual_skips_are_never_visual_success(self):
        report = {}
        with mock.patch('builtins.input', return_value=''), mock.patch('builtins.print'), mock.patch.object(runner.windows, 'current_skin', return_value='retro'):
            runner.manual_review(report)
        self.assertFalse(report['visual_verified'])
        self.assertEqual(report['manual']['physical_alt_tab'], 'pending')

    def test_user_observations_are_explicitly_separate_from_automatic_checks(self):
        report = {}
        with mock.patch('builtins.input', return_value='s'), mock.patch('builtins.print'), mock.patch.object(runner.windows, 'current_skin', return_value='plasma'):
            runner.manual_review(report)
        self.assertTrue(report['current_skin_observations_verified'])
        self.assertFalse(report['visual_verified'])
        self.assertIn('plasma', report['manual_by_skin'])
        self.assertIn('user observations', report['visual_verification_method'])
        self.assertNotIn('checks', report)

    def test_matrix_covers_each_skin_and_monitor_with_stateful_dispatchers(self):
        import argparse
        import json
        import re
        fixture = {'address': '0x123', 'pid': 17, 'workspace': {'name': 'special:magic'}}
        existing = {'address': '0x999', 'pid': 99, 'workspace': {'name': '4'}, '_bwm_process_generation': 'g'}
        state = {'skin': 'retro', 'monitor': 'A', 'pointer': 'A', 'open': False}
        transitions = []
        allow_pointer_move = [True]
        def query(name):
            if name == 'clients':
                return [fixture, existing]
            if name == 'activewindow':
                return fixture
            if name == 'monitors':
                return [{'description': desc, 'focused': state['monitor'] == desc,
                         'x': 0 if desc == 'A' else 1920, 'y': 0, 'width': 1920, 'height': 1080, 'scale': 1,
                         'specialWorkspace': {'name': 'special:magic' if state['open'] and state['monitor'] == desc else ''}}
                        for desc in ('A', 'B')]
            raise AssertionError(name)
        def command(*argv):
            if 'set' in argv:
                state['skin'] = argv[-1]
                transitions.append(state['skin'])
            elif 'configerrors' in argv:
                return ''
            elif any(str(arg).endswith('bwm-focus.py') for arg in argv):
                state['open'] = True
                state['monitor'] = state['pointer']
            return 'ok'
        def dispatch(code):
            if 'toggle_special' in code:
                state['open'] = not state['open']
            elif 'cursor.move' in code:
                if not allow_pointer_move[0]:
                    return
                xpos = int(re.search(r'x=(\d+)', code).group(1))
                state['pointer'] = 'A' if xpos < 1920 else 'B'
                state['monitor'] = state['pointer']
            elif 'monitor=' in code:
                state['monitor'] = json.loads(re.search(r'monitor=("[^"]+")', code).group(1)).removeprefix('desc:')
            else:
                raise AssertionError(code)
        report = {'checks': []}
        with mock.patch.object(runner, 'query', side_effect=query), mock.patch.object(runner, 'command', side_effect=command), mock.patch.object(runner, 'dispatch', side_effect=dispatch), mock.patch.object(runner.windows, 'process_generation', return_value='g'), mock.patch('builtins.print'):
            runner.matrix(argparse.Namespace(interactive=False), report, fixture, [existing], 'retro', {})
        self.assertEqual({(row['skin'], row['monitor']) for row in report['matrix']},
                         {(skin, 'desc:' + monitor) for skin in ('default','plasma','retro') for monitor in ('A','B')})
        self.assertEqual(state['skin'], 'retro')
        self.assertFalse(state['open'])
        self.assertEqual(transitions[-1], 'retro')

        # Negative control: software focus alone cannot represent physically choosing B.
        allow_pointer_move[0] = False
        state.update(skin='retro', monitor='A', pointer='A', open=False)
        failed_report = {'checks': []}
        def immediate_wait(predicate, label):
            value = predicate()
            if not value:
                raise RuntimeError(label)
            return value
        with mock.patch.object(runner, 'query', side_effect=query), mock.patch.object(runner, 'command', side_effect=command), mock.patch.object(runner, 'dispatch', side_effect=dispatch), mock.patch.object(runner, 'wait_for', side_effect=immediate_wait), mock.patch.object(runner.windows, 'process_generation', return_value='g'), mock.patch('builtins.print'):
            with self.assertRaisesRegex(RuntimeError, 'requested monitor'):
                runner.matrix(argparse.Namespace(interactive=False), failed_report, fixture, [existing], 'retro', {})
        self.assertEqual(failed_report['matrix_diagnostic']['requested_monitor'], 'desc:B')
