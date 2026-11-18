# SPDX-License-Identifier: GPL-2.0-or-later
"""Safe selection of unused bound workspaces and same-output native cycle receipts."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from contextlib import nullcontext, redirect_stdout
from io import StringIO
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('r4_workspace_cycle', ROOT/'src/bwm-plasma-host/check-desktops-activation.py')
m = importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class WorkspaceCycleTest(unittest.TestCase):
    def setUp(self):
        self.before = {'desktopIds': [str(n) for n in range(1, 11)], 'current': '1', 'configuredCount': 10,
                       'countRevision': 1, 'outputs': [
                           {'description': 'LG fixture', 'current': '10', 'geometry': [2560, 0, 3840, 2160]},
                           {'description': 'MSI fixture', 'current': '1', 'geometry': [0, 720, 2560, 1440]}]}
        self.workspaces = [{'id': 1}, {'id': 10}, {'id': -9}, {'id': 99}]
        self.rules = [{'workspaceString': str(n), 'enabled': True, 'monitor': 'desc:MSI fixture', 'persistent': n == 1}
                      for n in range(1, 10)]
        self.rules += [{'workspaceString': '10', 'enabled': True, 'monitor': 'desc:LG fixture', 'persistent': True}]
        self.monitors = [{'description': 'MSI fixture', 'name': 'DP-7', 'focused': True, 'activeWorkspace': {'id': 1}},
                         {'description': 'LG fixture', 'name': 'DP-1', 'focused': False, 'activeWorkspace': {'id': 10}}]
        self.native = {'version': 1, 'readOnly': False, 'passed': True, 'paused': True, 'restoredInitialOutput': True,
                       'windowCount': 0, 'navigationTarget': '2', 'activationMethod': 'requestActivate', 'activationRequestsSent': 2,
                       'steps': [{'description': 'MSI fixture', 'current': '2', 'verified': True},
                                 {'description': 'MSI fixture', 'current': '1', 'verified': True}]}
        self.first = dict.fromkeys(m.COUNTERS, 0);self.last = dict(self.first)
        for key in ('acceptedRequests', 'appliedActivations', 'observedActivations', 'dispatchedActivations'):
            self.last[key] = 2

    def choose(self):
        values = {'workspaces': self.workspaces, 'workspacerules': self.rules, 'monitors': self.monitors}
        with patch.object(m.session, 'query', side_effect=values.__getitem__):
            return m.select_workspace_target(self.before)

    def test_unused_configured_id_requires_explicit_binding_to_current_output(self):
        self.assertEqual(self.choose(), '2')
        self.workspaces.append({'id': 2})
        self.assertEqual(self.choose(), '3')
        self.rules[2]['monitor'] = 'desc:LG fixture'
        self.assertEqual(self.choose(), '4')

    def test_no_personal_workspace_is_reused_even_when_it_has_zero_windows(self):
        self.workspaces += [{'id': n, 'windows': 0} for n in range(2, 10)]
        with self.assertRaisesRegex(ValueError, 'No unused'):
            self.choose()

    def test_creation_hooks_persistence_disabled_or_duplicate_rules_are_not_used(self):
        original = copy.deepcopy(self.rules)
        for update in ({'onCreatedEmpty': 'exec a-user-command'}, {'persistent': True}, {'enabled': False}, {'monitor': ''}):
            self.rules = copy.deepcopy(original);self.rules[1].update(update)
            with self.subTest(update=update):self.assertEqual(self.choose(), '3')
        self.rules = original+[dict(original[1])]
        self.assertEqual(self.choose(), '3')

    def test_unknown_binding_or_hook_selectors_and_incomplete_types_fail_closed(self):
        original = copy.deepcopy(self.rules)
        for extra in ({'workspaceString': 'r[1-9]', 'enabled': True, 'monitor': 'desc:LG fixture'},
                      {'workspaceString': 'w[0]', 'enabled': True, 'onCreatedEmpty': 'exec command'},
                      {'workspaceString': '2', 'enabled': True, 'persistent': 'false'},
                      {'workspaceString': '2', 'enabled': True, 'onCreatedEmpty': False},
                      {'workspaceString': '2', 'monitor': 'desc:MSI fixture'}):
            self.rules = original+[extra]
            with self.subTest(extra=extra), self.assertRaises(ValueError):self.choose()

    def test_special_rules_and_ephemeral_connector_binding_do_not_change_identity(self):
        self.rules.append({'workspaceString': 'special:magic', 'enabled': True,
                           'monitor': 'desc:LG fixture', 'onCreatedEmpty': 'user special command'})
        self.rules[1]['monitor'] = 'DP-7'
        self.assertEqual(self.choose(), '2')

    def test_focus_change_or_malformed_live_workspace_prevents_selection(self):
        self.monitors[0]['focused'] = False
        with self.assertRaisesRegex(ValueError, 'Focused output changed'):self.choose()
        self.monitors[0]['focused'] = True;self.workspaces.append({'id': True})
        with self.assertRaisesRegex(ValueError, 'Invalid live workspace'):self.choose()

    def test_navigation_receipts_describe_current_output_target_and_return(self):
        delta = m.compare_cycle(self.before, self.before, self.native, self.first, self.last, navigation_target='2')
        self.assertEqual(delta['appliedActivations'], 2)
        for change in ({'activationMethod': 'requestActivateOnScreen'}, {'navigationTarget': '10'},
                       {'steps': [{'description': 'LG fixture', 'current': '2', 'verified': True}, self.native['steps'][1]]}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                m.compare_cycle(self.before, self.before, dict(self.native, **change), self.first, self.last, navigation_target='2')
        with self.assertRaises(ValueError):
            m.compare_cycle(self.before, self.before, dict(self.native, navigationTarget='10'), self.first, self.last, navigation_target='10')

    def test_other_output_change_or_unrestored_state_is_not_a_success(self):
        changed = copy.deepcopy(self.before);changed['outputs'][0]['current'] = '2'
        with self.assertRaisesRegex(ValueError, 'not restored'):
            m.compare_cycle(self.before, changed, self.native, self.first, self.last, navigation_target='2')

    def run_wrapper(self, selections):
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp)/'host';binary.touch();binary.chmod(0o700)
            with patch.object(m, 'stable_skin', return_value=nullcontext()), \
                 patch.object(m, 'action_lock', return_value=nullcontext()), patch.object(m, 'require_breeze'), \
                 patch.object(m, 'require_no_special_outputs'), \
                 patch.object(m.session, 'session_snapshot', side_effect=[self.before, self.before]), \
                 patch.object(m, 'counters', side_effect=[self.first, self.last]), \
                 patch.object(m, 'select_workspace_target', side_effect=selections), \
                 patch.dict(os.environ, {'WAYLAND_SOCKET': ''}), \
                 patch.object(m.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, stdout=json.dumps(self.native))) as run, \
                 redirect_stdout(StringIO()) as output:
                code = m.main(['--workspace-cycle', '--binary', str(binary)])
            return code, json.loads(output.getvalue()), run.call_args_list

    def test_workspace_wrapper_selects_rechecks_and_passes_target_as_a_distinct_argument(self):
        code, report, calls = self.run_wrapper(['2', '2'])
        self.assertEqual(code, 0);self.assertTrue(report['passed']);self.assertEqual(report['selectedDesktop'], '2')
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].args[0][1:], ['--check-native-desktops-workspace-cycle', 'MSI fixture', '2', 'LG fixture', 'MSI fixture'])

    def test_selection_race_never_starts_an_activation(self):
        code, report, calls = self.run_wrapper(['2', '3'])
        self.assertEqual(code, 1);self.assertFalse(report['activationAttempted'])
        self.assertIn('selection changed', report['error']);self.assertEqual(calls, [])


if __name__ == '__main__':
    unittest.main()
