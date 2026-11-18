# SPDX-License-Identifier: GPL-2.0-or-later
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('r4_check', ROOT / 'config/hypr/skins/plasma/scripts/r4-session-check.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

MONITOR = {'name': 'DP-fixture', 'description': 'BWM Fixture', 'x': -1280, 'y': 720,
           'width': 1280, 'height': 800, 'scale': 1.25, 'transform': 0,
           'reserved': [0, 0, 0, 44], 'activeWorkspace': {'name': 'private'}}


def response(value):
    return subprocess.CompletedProcess([], 0, json.dumps(value), '')


class SessionCheckTest(unittest.TestCase):
    def test_tray_watcher_uses_unique_owner_without_exposing_items(self):
        replies = ['b true', 's ":1.42"', f'u {os.getpid()}', 'as 2 "secret-id" "other item"', 'b true', 's ":1.42"']
        run = Mock(side_effect=[subprocess.CompletedProcess([],0,x,'') for x in replies])
        result = m.tray_services(run)
        self.assertTrue(result['watcherVerified'])
        self.assertEqual(result['registeredItemCount'],2)
        self.assertTrue(result['hostRegistered'])
        self.assertFalse(result['replacementReady'])
        self.assertNotIn('secret',json.dumps(result))
        self.assertNotIn(':1.42',json.dumps(result))
        for call in run.call_args_list:
            args = call.args[0]
            self.assertIn('--auto-start=no',args)
            if args[4] == 'get-property': self.assertEqual(args[5],':1.42')

    def test_absent_watcher_and_changing_owner_are_distinct(self):
        absent = Mock(return_value=subprocess.CompletedProcess([],0,'b false',''))
        self.assertEqual(m.tray_services(absent)['status'],'watcher-absent')
        absent.assert_called_once()
        replies = ['b true','s ":1.42"','u 1000','as 0','b false','s ":1.43"']
        changed = Mock(side_effect=[subprocess.CompletedProcess([],0,x,'') for x in replies])
        result = m.tray_services(changed)
        self.assertFalse(result['watcherVerified'])
        self.assertEqual(result['status'],'watcher-owner-changed')
        self.assertNotIn('registeredItemCount',result)

    def test_tray_watcher_rejects_inconsistent_item_count(self):
        replies = ['b true','s ":1.42"','u 1000','as 2 "one item"','b false']
        run = Mock(side_effect=[subprocess.CompletedProcess([],0,x,'') for x in replies])
        result = m.tray_services(run)
        self.assertFalse(result['watcherVerified'])
        self.assertEqual(result['status'],'watcher-unverified')
    def test_denied_ipc_stops_without_other_commands(self):
        run = Mock(return_value=subprocess.CompletedProcess([], 1, '', "Couldn't open a socket (1)"))
        r = m.collect(run, {})
        self.assertEqual(r['status'], 'ipc-unavailable')
        self.assertFalse(r['realAreaVerified'])
        self.assertEqual(run.call_count, 1)

    def test_timeout_is_bounded_and_reported(self):
        run = Mock(side_effect=subprocess.TimeoutExpired('hyprctl', 3))
        self.assertEqual(m.collect(run, {})['status'], 'ipc-unavailable')
        self.assertEqual(run.call_args.kwargs['timeout'], 3)

    def test_missing_program_and_malformed_json_are_reported(self):
        for run in (Mock(side_effect=FileNotFoundError()), Mock(return_value=subprocess.CompletedProcess([], 0, 'broken', ''))):
            self.assertEqual(m.collect(run, {})['status'], 'ipc-unavailable')

    def test_invalid_monitor_response_does_not_continue(self):
        for value in ([], {}, [dict(MONITOR, scale=0)], [dict(MONITOR, reserved=[0])], [dict(MONITOR, width=True)], [dict(MONITOR, x=float('nan'))]):
            run = Mock(return_value=response(value))
            self.assertEqual(m.collect(run, {})['status'], 'invalid-monitor-response')
            self.assertEqual(run.call_count, 1)

    def test_layers_failure_does_not_query_preview(self):
        run = Mock(side_effect=[response([MONITOR]), subprocess.CompletedProcess([], 1, '', 'denied')])
        self.assertEqual(m.collect(run, {})['status'], 'layers-unavailable')
        self.assertEqual(run.call_count, 2)

    def test_success_sanitizes_layers_and_never_certifies_r4(self):
        layers = {'DP-fixture': {'levels': {'2': [
            {'namespace': 'private-app', 'address': 'secret'},
            {'namespace': 'bwm-r4-native-policy', 'x': -1280, 'y': 1476, 'w': 640, 'h': 44, 'pid': 55, 'address': 'secret'}]}}}
        run = Mock(side_effect=[response([MONITOR]), response(layers), response({'active': True, 'runtime': {'replacementReady': False}})])
        r = m.collect(run, {})
        self.assertEqual(r['status'], 'observations-collected')
        self.assertEqual(len(r['nativeLayers']), 1)
        for word in ('secret', 'private-app', 'activeWorkspace'):
            self.assertNotIn(word, json.dumps(r))
        self.assertFalse(r['realAreaVerified'])
        self.assertFalse(r['r4Complete'])
        self.assertEqual(run.call_args.args[0][-1], 'status')

    def test_no_preview_is_pending_even_with_existing_reservations(self):
        run = Mock(side_effect=[response([MONITOR]), response({}), response({'active': False})])
        r = m.collect(run, {})
        self.assertEqual(r['status'], 'access-ok-no-native-preview')
        self.assertFalse(r['realAreaVerified'])

    def test_bad_layers_and_preview_do_not_pass(self):
        run = Mock(side_effect=[response([MONITOR]), response({'fixture': {}})])
        self.assertEqual(m.collect(run, {})['status'], 'invalid-layer-response')
        for value in ({}, {'active': 1}, []):
            run = Mock(side_effect=[response([MONITOR]), response({}), response(value)])
            self.assertEqual(m.collect(run, {})['status'], 'invalid-preview-response')

    def test_socket_metadata_does_not_include_signature(self):
        r = m.sockets({'XDG_RUNTIME_DIR': '/unavailable', 'HYPRLAND_INSTANCE_SIGNATURE': 'private-signature'})
        self.assertTrue(r['instanceSignaturePresent'])
        self.assertNotIn('private-signature', json.dumps(r))

    def test_report_is_private_and_symlink_target_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'report.json'
            m.save_report(target, {'status': 'fixture'})
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            m.save_report(target, {'status': 'replaced'})
            link = Path(tmp) / 'link.json'
            link.symlink_to(target)
            before = target.read_bytes()
            with self.assertRaises(ValueError): m.save_report(link, {})
            self.assertEqual(target.read_bytes(), before)


if __name__ == '__main__': unittest.main()
