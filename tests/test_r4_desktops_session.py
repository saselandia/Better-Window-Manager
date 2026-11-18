# SPDX-License-Identifier: GPL-2.0-or-later
"""Read-only KDE/Hyprland comparison, race rejection and disposable environment."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('r4_desktops_session', ROOT/'src/bwm-plasma-host/check-desktops-session.py')
m = importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class DesktopSessionTest(unittest.TestCase):
    def setUp(self):
        self.provider = {'enabled': True, 'providerAvailable': True, 'configuredCountAvailable': True,
                         'arbitrationState': 'active', 'providerRestartRequired': False,
                         'configuredCount': 3, 'desktops': 3, 'current': '1', 'countRevision': 1}
        self.monitors = [
            {'description': 'BWM A serial-A', 'name': 'DP-8', 'x': 0, 'y': 720, 'width': 2560, 'height': 1440,
             'scale': 1, 'transform': 0, 'focused': True, 'activeWorkspace': {'id': 1}},
            {'description': 'BWM B serial-B', 'name': 'DP-1', 'x': 2560, 'y': 0, 'width': 3840, 'height': 2160,
             'scale': 1, 'transform': 0, 'focused': False, 'activeWorkspace': {'id': 2}},
        ]
        self.spaces = [{'id': 1, 'name': 'private-title-not-reported'}, {'id': 2}, {'id': -9}, {'id': 99}]

    def snapshot(self):
        values = {'bwm-plasma-desktops': self.provider, 'monitors': self.monitors, 'workspaces': self.spaces}
        with patch.object(m, 'query', side_effect=values.__getitem__):
            return m.session_snapshot()

    def native(self, before):
        return {'version': 1, 'readOnly': True, 'ready': True, 'desktops': len(before['desktopIds']),
                'current': before['current'], 'desktopIds': before['desktopIds'], 'windowCount': 0,
                'qtScreenCount': len(before['outputs']),
                'control': {'bindingVerified': True, 'providerAvailable': True, 'resumed': False, 'serial': 0},
                'outputs': [dict(output, match='matched', currentByName=output['current'],
                                 currentByGeometry=output['current']) for output in before['outputs']]}

    def test_projection_matches_provider_and_reports_only_needed_metadata(self):
        before = self.snapshot()
        self.assertEqual(before['desktopIds'], ['1', '2', '3'])
        self.assertEqual(before['outputs'][0]['geometry'], [0, 720, 2560, 1440])
        self.assertEqual(before['outputs'][1]['current'], '2')
        self.assertNotIn('private-title', json.dumps(before))
        self.assertNotIn('DP-', json.dumps(before))
        self.assertEqual(len(m.compare(before, before, self.native(before))), 2)

    def test_live_and_active_workspaces_survive_reduced_count(self):
        self.provider.update(configuredCount=1, desktops=4)
        self.spaces += [{'id': 7}, {'id': 3}]
        self.assertEqual(self.snapshot()['desktopIds'], ['1', '2', '3', '7'])

    def test_geometry_uses_common_scale_and_rotation_contract(self):
        self.monitors[0].update(scale=1.5, transform=1)
        self.assertEqual(self.snapshot()['outputs'][0]['geometry'], [0, 720, 960, 1706])

    def test_inactive_provider_unknown_count_or_unreconciled_state_is_rejected(self):
        original = copy.deepcopy(self.provider)
        for change in ({'enabled': False}, {'providerAvailable': False}, {'configuredCountAvailable': False},
                       {'providerRestartRequired': True}, {'arbitrationState': 'claiming'},
                       {'configuredCount': True}, {'configuredCount': 0}, {'desktops': 4}, {'current': '2'}):
            with self.subTest(change=change):
                self.provider = dict(original, **change)
                with self.assertRaises(ValueError):
                    self.snapshot()

    def test_ambiguous_or_invalid_outputs_fail_without_selecting_an_arbitrary_screen(self):
        original = copy.deepcopy(self.monitors)
        for change in ({'description': ''}, {'description': 'BWM A serial-A'}, {'scale': 0}, {'scale': True},
                       {'transform': 8}, {'x': float('nan')}, {'activeWorkspace': {'id': -9}}, {'focused': True}):
            with self.subTest(change=change):
                self.monitors = [original[0], dict(original[1], **change)]
                with self.assertRaises(ValueError):
                    self.snapshot()
        self.monitors = [original[0], dict(original[0], description='Mirror with distinct description', focused=False)]
        with self.assertRaisesRegex(ValueError, 'identical output rectangles'):
            self.snapshot()

    def test_measurement_changed_between_brackets_is_inconclusive(self):
        before = self.snapshot()
        after = copy.deepcopy(before);after['outputs'][0]['current'] = '3'
        with self.assertRaisesRegex(ValueError, 'changed during measurement'):
            m.compare(before, after, self.native(before))

    def test_no_success_for_resumed_connection_missing_binding_or_created_window(self):
        before = self.snapshot()
        for change in ({'bindingVerified': False}, {'providerAvailable': False}, {'resumed': True}, {'serial': 1}, {'serial': False}):
            native = self.native(before);native['control'].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                m.compare(before, before, native)
        for change in ({'windowCount': 1}, {'windowCount': False}, {'ready': False}, {'readOnly': False}, {'version': True}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                m.compare(before, before, dict(self.native(before), **change))

    def test_both_output_apis_identity_and_geometry_must_agree(self):
        before = self.snapshot()
        for change in ({'description': 'another'}, {'match': 'ambiguous-output-description'},
                       {'currentByName': '1'}, {'currentByGeometry': '1'}, {'geometry': [0, 0, 3840, 2160]}):
            native = self.native(before);native['outputs'][1].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                m.compare(before, before, native)
        for change in ({'desktopIds': ['1', '2', '4']}, {'current': '2'}, {'qtScreenCount': 1},
                       {'outputs': []}, {'desktops': True}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                m.compare(before, before, dict(self.native(before), **change))

    def test_disposable_environment_keeps_wayland_connection_but_no_action_flags(self):
        root = Path('/tmp/read-only-check')
        source = {'XDG_RUNTIME_DIR': '/run/user/1000', 'WAYLAND_DISPLAY': 'wayland-1',
                  'WAYLAND_SOCKET': '11', 'BWM_R4_NATIVE_DESKTOPS': '1', 'BWM_R4_TASK_ACTIONS': '1',
                  'BWM_R4_TASK_THUMBNAILS': '1', 'HYPRLAND_INSTANCE_SIGNATURE': 'private', 'KDESYCOCA': '/private/db'}
        env = m.isolated_environment(root, source)
        self.assertEqual(env['WAYLAND_DISPLAY'], '/run/user/1000/wayland-1')
        self.assertEqual(env['WAYLAND_SOCKET'], '11')
        self.assertEqual(env['XDG_RUNTIME_DIR'], str(root/'runtime'))
        self.assertEqual(env['DBUS_SESSION_BUS_ADDRESS'], 'unix:path='+str(root/'no-bus'))
        self.assertFalse(any(key.startswith('BWM_R4_') for key in env))
        self.assertNotIn('HYPRLAND_INSTANCE_SIGNATURE', env);self.assertNotIn('KDESYCOCA', env)

    def test_wrapper_passes_only_output_descriptions_and_never_uses_mutating_ipc(self):
        before = self.snapshot()
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp)/'host';binary.touch();binary.chmod(0o700)
            reply = subprocess.CompletedProcess([], 0, stdout=json.dumps(self.native(before)))
            with patch.object(m, 'session_snapshot', side_effect=[before, before]), \
                 patch.dict(os.environ, {'WAYLAND_SOCKET': ''}), \
                 patch.object(m.subprocess, 'run', return_value=reply) as run, redirect_stdout(StringIO()) as output:
                self.assertEqual(m.main(['--binary', str(binary)]), 0)
            report = json.loads(output.getvalue())
            self.assertTrue(report['passed']);self.assertFalse(report['activationTested'])
            self.assertEqual(report['activationRequestsSent'], 0)
            self.assertEqual(run.call_args.args[0], [str(binary), '--check-native-desktops-session',
                                                    'BWM A serial-A', 'BWM B serial-B'])
            self.assertNotIn('HYPRLAND_INSTANCE_SIGNATURE', run.call_args.kwargs['env'])

    def test_native_failure_preserves_cause_instead_of_certifying_empty_data(self):
        before = self.snapshot()
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp)/'host';binary.touch();binary.chmod(0o700)
            for reply, message in ((subprocess.CompletedProcess([], 2, stdout='{"error":"registry timed out"}'), 'registry timed out'),
                                   (subprocess.CompletedProcess([], -6, stdout=''), 'no JSON')):
                with self.subTest(message=message), patch.object(m, 'session_snapshot', return_value=before), \
                     patch.dict(os.environ, {'WAYLAND_SOCKET': ''}), \
                     patch.object(m.subprocess, 'run', return_value=reply), redirect_stdout(StringIO()) as output:
                    self.assertEqual(m.main(['--binary', str(binary)]), 1)
                report = json.loads(output.getvalue())
                self.assertFalse(report['passed']);self.assertIn(message, report['error'])

    def test_query_only_reads_hyprland_json_endpoints(self):
        with patch.object(m.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, stdout='{}')) as run:
            m.query('monitors')
            self.assertEqual(run.call_args.args[0], ['hyprctl', '-j', 'monitors'])


if __name__ == '__main__':
    unittest.main()
