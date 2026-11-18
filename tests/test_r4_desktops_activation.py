# SPDX-License-Identifier: GPL-2.0-or-later
"""Explicit focus-cycle routing, counters, restoration and existing lock protocol."""
import copy
import fcntl
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
spec = importlib.util.spec_from_file_location('r4_desktops_activation', ROOT/'src/bwm-plasma-host/check-desktops-activation.py')
m = importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class NativeFocusCycleTest(unittest.TestCase):
    def setUp(self):
        self.before = {'desktopIds': ['1', '2', '10'], 'current': '1', 'configuredCount': 10, 'countRevision': 1,
                       'outputs': [{'description': 'LG fixture', 'current': '10', 'geometry': [2560, 0, 3840, 2160]},
                                   {'description': 'MSI fixture', 'current': '1', 'geometry': [0, 720, 2560, 1440]}]}
        self.native = {'version': 1, 'readOnly': False, 'passed': True, 'paused': True, 'restoredInitialOutput': True,
                       'activationRequestsSent': 2, 'windowCount': 0,
                       'steps': [{'description': 'LG fixture', 'current': '10', 'verified': True},
                                 {'description': 'MSI fixture', 'current': '1', 'verified': True}]}
        self.first = dict.fromkeys(m.COUNTERS, 4)
        self.last = dict(self.first)
        for key in ('acceptedRequests', 'appliedActivations', 'observedActivations', 'dispatchedActivations'):
            self.last[key] += 2

    def compare(self, **changes):
        return m.compare_cycle(changes.get('before', self.before), changes.get('after', self.before),
                               changes.get('native', self.native), self.first, changes.get('counts_after', self.last))

    def test_visits_already_active_pairs_and_returns_to_original_monitor(self):
        delta = self.compare()
        self.assertEqual(delta['appliedActivations'], 2);self.assertEqual(delta['activationNoops'], 0)

    def test_restoration_pause_and_real_native_success_are_required(self):
        for change in ({'paused': False}, {'restoredInitialOutput': False}, {'passed': False},
                       {'readOnly': True}, {'windowCount': 1}, {'version': True}, {'windowCount': False},
                       {'activationRequestsSent': 1}, {'activationRequestsSent': True}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.compare(native=dict(self.native, **change))

    def test_route_must_use_current_pairs_and_return_last(self):
        for steps in (self.native['steps'][::-1], self.native['steps'][:1],
                      [dict(self.native['steps'][0], current='2'), self.native['steps'][1]],
                      [dict(self.native['steps'][0], verified=False), self.native['steps'][1]]):
            with self.subTest(steps=steps), self.assertRaises(ValueError):
                self.compare(native=dict(self.native, steps=steps))

    def test_changed_assignments_focus_or_count_revision_never_certify_restoration(self):
        for key, value in (('current', '10'), ('countRevision', 2), ('desktopIds', ['1', '2'])):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.compare(after=dict(self.before, **{key: value}))
        after = copy.deepcopy(self.before);after['outputs'][0]['current'] = '2'
        with self.assertRaises(ValueError):self.compare(after=after)

    def test_provider_counters_must_agree_and_have_no_failure_cancellation_or_noop(self):
        for key in m.COUNTERS:
            changed = dict(self.last);changed[key] += 1
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.compare(counts_after=changed)
        with self.assertRaises(ValueError):self.compare(counts_after=self.first)

    def test_counter_query_rejects_invalid_types_and_errors(self):
        provider = dict(self.first, lastError='', lastActivationError='')
        with patch.object(m.session, 'query', return_value=provider):self.assertEqual(m.counters(), self.first)
        for change in ({'lastError': 'unavailable'}, {'lastActivationError': 'readback failed'},
                       {'acceptedRequests': True}, {'appliedActivations': -1}):
            with self.subTest(change=change), patch.object(m.session, 'query', return_value=dict(provider, **change)), self.assertRaises(ValueError):
                m.counters()

    def test_historical_activation_error_does_not_permanently_block_a_future_explicit_retry(self):
        provider = dict(self.first, lastError='', lastActivationError='old readback failure')
        with patch.object(m.session, 'query', return_value=provider):
            self.assertEqual(m.counters(require_clean=False), self.first)
            with self.assertRaises(ValueError):m.counters()

    def test_cycle_preflight_requires_updated_loaded_routing_without_weakening_read_only_diagnostics(self):
        provider = dict(self.first, lastError='', lastActivationError='old error')
        for version in (None, 1, True, '2'):
            with self.subTest(version=version), patch.object(m.session, 'query', return_value=dict(provider, activationRoutingVersion=version)):
                with self.assertRaisesRegex(ValueError, 'ruta anterior'):
                    m.counters(require_clean=False, require_routing=True)
        with patch.object(m.session, 'query', return_value=dict(provider, activationRoutingVersion=2)):
            self.assertEqual(m.counters(require_clean=False, require_routing=True), self.first)

    def test_read_only_diagnosis_needs_no_host_and_never_acquires_action_guards(self):
        provider = dict(self.first, lastActivationError='activation-readback-mismatch')
        with patch.object(m, 'provider_diagnostic', return_value=provider), \
             patch.object(m.session, 'session_snapshot', return_value=self.before), \
             patch.object(m, 'stable_skin') as skin, patch.object(m, 'action_lock') as lock, \
             patch.object(m.subprocess, 'run') as run, redirect_stdout(StringIO()) as output:
            self.assertEqual(m.main(['--diagnose-last', '--binary', '/does/not/exist']), 0)
        report = json.loads(output.getvalue())
        self.assertTrue(report['readOnly']);self.assertTrue(report['diagnosticComplete'])
        self.assertFalse(report['activationAttempted']);self.assertNotIn('passed', report)
        self.assertEqual(report['provider']['lastActivationError'], 'activation-readback-mismatch')
        skin.assert_not_called();lock.assert_not_called();run.assert_not_called()

    def test_read_only_diagnosis_keeps_provider_error_when_session_snapshot_cannot_settle(self):
        with patch.object(m, 'provider_diagnostic', return_value={'lastActivationError': 'monitor-focus-failed'}), \
             patch.object(m.session, 'session_snapshot', side_effect=ValueError('Focused output changed')), \
             redirect_stdout(StringIO()) as output:
            self.assertEqual(m.main(['--diagnose-last']), 1)
        report = json.loads(output.getvalue())
        self.assertFalse(report['diagnosticComplete'])
        self.assertEqual(report['provider']['lastActivationError'], 'monitor-focus-failed')
        self.assertIn('Focused output changed', report['sessionReadError'])

    def test_provider_diagnostic_excludes_unrelated_fields_and_accepts_failure_counters(self):
        provider = dict(self.first, lastActivationError='workspace-action-failed', current='1', privateEnvironment='not reported')
        with patch.object(m.session, 'query', return_value=provider):
            report = m.provider_diagnostic()
        self.assertEqual(report['lastActivationError'], 'workspace-action-failed')
        self.assertNotIn('privateEnvironment', report)

    def test_visible_special_or_incomplete_monitor_state_rejects_focus_cycle(self):
        with patch.object(m.session, 'query', return_value=[{'specialWorkspace': {'id': 0}}]):
            m.require_no_special_outputs()
        for monitors in ([], [{}], [{'specialWorkspace': {'id': -9}}], [{'specialWorkspace': {'id': False}}]):
            with self.subTest(monitors=monitors), patch.object(m.session, 'query', return_value=monitors), self.assertRaises(ValueError):
                m.require_no_special_outputs()

    def test_uses_shared_skin_lock_without_truncation_and_fails_if_manager_owns_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'skin.lock';path.write_text('preserved');inode = path.stat().st_ino
            with path.open('r') as manager:
                fcntl.flock(manager, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with self.assertRaises(BlockingIOError):
                    with m.stable_skin(path):self.fail('Must not run while a skin change owns the lock')
            with m.stable_skin(path):
                with path.open('r') as manager:
                    with self.assertRaises(BlockingIOError):fcntl.flock(manager, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(path.read_text(), 'preserved');self.assertEqual(path.stat().st_ino, inode)

    def test_skin_lock_rejects_links_and_writable_shared_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'skin.lock';path.touch();link = Path(tmp)/'link';link.symlink_to(path)
            with self.assertRaises(OSError):
                with m.stable_skin(link):pass
            path.chmod(0o666)
            with self.assertRaises(ValueError):
                with m.stable_skin(path):pass
            path.chmod(0o600);os.link(path, Path(tmp)/'hardlink')
            with self.assertRaises(ValueError):
                with m.stable_skin(path):pass

    def test_without_explicit_opt_in_no_native_client_or_session_query_runs(self):
        with patch.object(m.subprocess, 'run') as run, patch.object(m.session, 'session_snapshot') as snapshot:
            with self.assertRaises(SystemExit):m.main([])
            run.assert_not_called();snapshot.assert_not_called()

    def test_wrapper_runs_native_client_under_both_guards_and_rechecks_breeze(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp)/'host';binary.touch();binary.chmod(0o700)
            with patch.object(m, 'stable_skin', return_value=nullcontext()) as skin, \
                 patch.object(m, 'action_lock', return_value=nullcontext()) as lock, \
                 patch.object(m, 'require_breeze') as breeze, \
                 patch.object(m, 'require_no_special_outputs'), \
                 patch.object(m.session, 'session_snapshot', side_effect=[self.before, self.before]), \
                 patch.object(m, 'counters', side_effect=[self.first, self.last]), \
                 patch.dict(os.environ, {'WAYLAND_SOCKET': ''}), \
                 patch.object(m.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, stdout=json.dumps(self.native))) as run, \
                 redirect_stdout(StringIO()) as output:
                self.assertEqual(m.main(['--focus-cycle', '--binary', str(binary)]), 0)
            self.assertTrue(json.loads(output.getvalue())['passed'])
            skin.assert_called_once();lock.assert_called_once();self.assertEqual(breeze.call_count, 2)
            self.assertEqual(run.call_args.args[0], [str(binary), '--check-native-desktops-focus-cycle', 'MSI fixture', 'LG fixture', 'MSI fixture'])
            self.assertEqual(run.call_args.kwargs['timeout'], 20)
            self.assertNotIn('HYPRLAND_INSTANCE_SIGNATURE', run.call_args.kwargs['env'])

    def test_wrong_skin_or_busy_guard_prevents_starting_the_native_cycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp)/'host';binary.touch();binary.chmod(0o700)
            with patch.object(m, 'stable_skin', return_value=nullcontext()), \
                 patch.object(m, 'action_lock', return_value=nullcontext()), \
                 patch.object(m, 'require_breeze', side_effect=ValueError('Breeze no longer active')), \
                 patch.object(m.subprocess, 'run') as run, redirect_stdout(StringIO()) as output:
                self.assertEqual(m.main(['--focus-cycle', '--binary', str(binary)]), 1)
            self.assertFalse(json.loads(output.getvalue())['activationAttempted']);run.assert_not_called()

    def test_failed_child_keeps_restoration_result_and_error_without_fallback_actions(self):
        failed = dict(self.native, passed=False, restoredInitialOutput=False, error='Native activation not observed')
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp)/'host';binary.touch();binary.chmod(0o700)
            with patch.object(m, 'stable_skin', return_value=nullcontext()), \
                 patch.object(m, 'action_lock', return_value=nullcontext()), patch.object(m, 'require_breeze'), \
                 patch.object(m, 'require_no_special_outputs'), \
                 patch.object(m, 'provider_diagnostic', return_value={'lastActivationError': 'activation-readback-mismatch'}), \
                 patch.object(m.session, 'session_snapshot', return_value=self.before), \
                 patch.object(m, 'counters', return_value=self.first), patch.dict(os.environ, {'WAYLAND_SOCKET': ''}), \
                 patch.object(m.subprocess, 'run', return_value=subprocess.CompletedProcess([], 2, stdout=json.dumps(failed))) as run, \
                 redirect_stdout(StringIO()) as output:
                self.assertEqual(m.main(['--focus-cycle', '--binary', str(binary)]), 1)
            report = json.loads(output.getvalue())
            self.assertFalse(report['passed']);self.assertFalse(report['restoredInitialOutput'])
            self.assertIn('not observed', report['error']);run.assert_called_once()
            self.assertEqual(report['nativeDiagnostic'], failed)
            self.assertEqual(report['providerAfter']['lastActivationError'], 'activation-readback-mismatch')


if __name__ == '__main__':
    unittest.main()
