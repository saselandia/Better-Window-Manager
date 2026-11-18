# SPDX-License-Identifier: GPL-2.0-or-later
import copy
import contextlib
import io
import json
import os
import importlib.util
from pathlib import Path
import signal
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('r4_smoke', ROOT / 'config/hypr/skins/plasma/scripts/r4-reservation-smoke.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def snapshots():
    before = {'status': 'access-ok-no-native-preview', 'preview': {'active': False}, 'nativeLayers': [],
              'monitors': [{'name': 'DP-A', 'description': 'Exact A', 'x': 0, 'y': 720, 'width': 2560,
                            'height': 1440, 'scale': 1, 'transform': 0, 'reserved': [0, 0, 0, 44]},
                           {'name': 'DP-B', 'description': 'Exact B', 'x': 2560, 'y': 0, 'width': 3840,
                            'height': 2160, 'scale': 1, 'transform': 0, 'reserved': [0, 0, 0, 44]}]}
    during = copy.deepcopy(before)
    during['status'] = 'observations-collected'
    during['monitors'][0]['reserved'][3] = 92
    during['nativeLayers'] = [{'namespace': 'bwm-r4-native-policy', 'output': 'DP-A'}]
    during['preview'] = {'active': True, 'runtime': {'nativePanelPolicy': True, 'skin': 'plasma',
                         'panels': [{'exclusiveZoneRequested': 48, 'reservationRequested': True,
                                     'renderReady': True, 'outputDescription': 'Exact A'}]}}
    return before, during, copy.deepcopy(before)


class SmokeTest(unittest.TestCase):
    def test_second_edge_uses_original_baseline_and_stops_after_failure(self):
        before, _, _ = snapshots()
        args = SimpleNamespace(edge=['left','right','bottom'], output=['Exact A','Exact B'], maximize=False)
        left = {'before':before, 'requestedEdge':'left','reservationDeltaVerified':True,'errors':[]}
        right = {'before':before, 'requestedEdge':'right','reservationDeltaVerified':False,'errors':['changed']}
        with patch.object(m,'run_trial',side_effect=[left,right]) as trial:
            report = m.run_trials(args)
        self.assertEqual(trial.call_args_list, [unittest.mock.call(args,'left',None),
                                               unittest.mock.call(args,'right',m.by_description(before))])
        self.assertEqual(report['trials'], [left,right])
        self.assertFalse(report['reservationDeltaVerified'])

    def test_maximized_sequence_requires_every_requested_edge(self):
        before, _, _ = snapshots()
        args = SimpleNamespace(edge=['top', 'left', 'right'], output=['Exact A'], maximize=True)
        trials = [{'before': before, 'requestedEdge': edge, 'reservationDeltaVerified': True,
                   'maximizedWindowVerified': True, 'dynamicMaximizedWindowVerified': edge != 'left', 'errors': []}
                  for edge in args.edge]
        with patch.object(m, 'run_trial', side_effect=trials) as trial:
            report = m.run_trials(args)
        self.assertEqual(trial.call_args_list, [unittest.mock.call(args, 'top', None)] + [
            unittest.mock.call(args, edge, m.by_description(before)) for edge in ('left', 'right')])
        self.assertTrue(report['reservationDeltaVerified'])
        self.assertTrue(report['maximizedWindowVerified'])
        self.assertTrue(report['realAreaVerified'])
        self.assertFalse(report['dynamicMaximizedWindowVerified'])

        trials[1]['maximizedWindowVerified'] = False
        with patch.object(m, 'run_trial', side_effect=trials) as trial:
            failed = m.run_trials(args)
        self.assertEqual(trial.call_count, 2)
        self.assertEqual([t['requestedEdge'] for t in failed['trials']], ['top', 'left'])
        self.assertFalse(failed['maximizedWindowVerified'])
        self.assertFalse(failed['realAreaVerified'])

    def test_foreign_process_is_not_sent_a_stop_command(self):
        child=Mock(pid=1234);child.poll.return_value=None
        registration={'pid':5678,'processStart':'9000','compositorInstance':'fixture','reportsExit':True}
        stat='5678 (a process) S 4321 '+'0 '*17+'9000'
        with patch.dict(os.environ,{'HYPRLAND_INSTANCE_SIGNATURE':'fixture'}), \
             patch.object(m.session,'active_registration',return_value=registration), \
             patch.object(m.Path,'read_text',return_value=stat), patch.object(m.session,'command') as command:
            with self.assertRaisesRegex(ValueError,'otro ensayo'):
                m.confirm_fixture_exit(child)
            command.assert_not_called()

    def test_two_outputs_reserve_each_of_the_four_edges_independently(self):
        for index,edge in enumerate(('left','top','right','bottom')):
            with self.subTest(edge=edge):
                before,during,after=snapshots()
                zones=(48,60)
                panels=[{'outputDescription':desc,'edge':edge,'exclusiveZoneRequested':zone,
                         'reservationRequested':True,'renderReady':True} for desc,zone in zip(('Exact A','Exact B'),zones)]
                during['preview']['runtime']['panels']=list(reversed(panels))
                for monitor,original,zone in zip(during['monitors'],before['monitors'],zones):
                    monitor['reserved']=original['reserved'].copy()
                    monitor['reserved'][index]+=zone
                during['nativeLayers'].append({'namespace':'bwm-r4-native-policy','output':'DP-B'})
                result=m.evaluate(before,during,after,['Exact A','Exact B'],edge)
                self.assertTrue(result['reservationDeltaVerified'],result['errors'])
                self.assertEqual([p['requestedZone'] for p in result['reservationsByOutput']],list(zones))
                self.assertFalse(result['realAreaVerified'])
                for change in ('wrong-edge','missing-edge','same-output','same-layer','partial-cleanup'):
                    current,cleaned=copy.deepcopy((during,after))
                    if change=='wrong-edge':current['preview']['runtime']['panels'][1]['edge']='top' if edge!='top' else 'bottom'
                    if change=='missing-edge':current['preview']['runtime']['panels'][1].pop('edge')
                    if change=='same-output':current['preview']['runtime']['panels'][1]['outputDescription']='Exact B'
                    if change=='same-layer':current['nativeLayers'][1]['output']='DP-A'
                    if change=='partial-cleanup':cleaned['monitors'][1]['reserved'][index]+=60
                    self.assertFalse(m.evaluate(before,current,cleaned,['Exact A','Exact B'],edge)['reservationDeltaVerified'],change)

    def test_matching_delta_and_cleanup_do_not_certify_maximization_or_r4(self):
        self.assertEqual(m.ROOT, ROOT)
        r = m.evaluate(*snapshots(), 'Exact A')
        self.assertTrue(r['reservationDeltaVerified'])
        self.assertFalse(r['maximizedWindowVerified'])
        self.assertFalse(r['realAreaVerified'])
        self.assertFalse(r['r4Complete'])

    def test_no_delta_or_wrong_delta_is_not_passed(self):
        for bottom in (44, 48, 91, 93):
            a, b, c = snapshots();b['monitors'][0]['reserved'][3] = bottom
            self.assertFalse(m.evaluate(a, b, c, 'Exact A')['reservationDeltaVerified'])

    def test_other_output_and_other_edge_changes_are_rejected(self):
        for output, edge in ((1, 3), (0, 0), (0, 1), (0, 2)):
            a, b, c = snapshots();b['monitors'][output]['reserved'][edge] += 1
            self.assertFalse(m.evaluate(a, b, c, 'Exact A')['reservationDeltaVerified'])

    def test_cleanup_must_restore_original_reservations_and_registration(self):
        for change in ('reservation', 'layer', 'preview'):
            a, b, c = snapshots()
            if change == 'reservation': c['monitors'][0]['reserved'][3] = 92
            elif change == 'layer': c['nativeLayers'] = b['nativeLayers']
            else: c['status'] = 'observations-collected'
            self.assertFalse(m.evaluate(a, b, c, 'Exact A')['reservationDeltaVerified'])

    def test_changed_scale_or_hotplug_is_not_a_comparable_measurement(self):
        for change in ('scale', 'hotplug', 'ambiguous'):
            a, b, c = snapshots()
            if change == 'scale': b['monitors'][0]['scale'] = 1.25
            elif change == 'hotplug': c['monitors'].pop()
            else: b['monitors'][1]['description'] = 'Exact A'
            self.assertFalse(m.evaluate(a, b, c, 'Exact A')['reservationDeltaVerified'])

    def test_panel_must_confirm_frame_request_and_exact_output(self):
        for key, value in (('renderReady', False), ('reservationRequested', False), ('exclusiveZoneRequested', True), ('exclusiveZoneRequested', 0), ('outputDescription', 'Other')):
            a, b, c = snapshots();b['preview']['runtime']['panels'][0][key] = value
            self.assertFalse(m.evaluate(a, b, c, 'Exact A')['reservationDeltaVerified'])

    def test_missing_or_foreign_layer_is_not_passed(self):
        for layers in ([], [{'namespace': 'bwm-r4-native-policy', 'output': 'DP-B'}]):
            a, b, c = snapshots();b['nativeLayers'] = layers
            self.assertFalse(m.evaluate(a, b, c, 'Exact A')['reservationDeltaVerified'])

    def test_failed_query_is_not_passed(self):
        a, b, c = snapshots()
        self.assertFalse(m.evaluate(a, {'status': 'ipc-unavailable'}, c, 'Exact A')['reservationDeltaVerified'])

    def test_stop_targets_only_owned_process_group_then_escalates_if_hung(self):
        child = Mock(pid=123456);child.poll.return_value = None
        child.wait.side_effect = [subprocess.TimeoutExpired('fixture', 7), None]
        with patch.object(m.os, 'killpg') as kill:
            m.stop_child(child)
        self.assertEqual(kill.call_args_list, [unittest.mock.call(123456, signal.SIGINT), unittest.mock.call(123456, signal.SIGTERM)])

    def test_exited_child_is_not_signalled(self):
        child = Mock();child.poll.return_value = 0
        with patch.object(m.os, 'killpg') as kill:
            m.stop_child(child)
        kill.assert_not_called()

    def run_maximized_main(self, fail_measure=False, refresh=False, shrink=True, grow=False, fail_stop=False,
                           edge=None, second_output=False, fail_second_start=False):
        before, during, after = snapshots()
        during['preview']['runtime']['renderReady']=True
        outputs = ['Exact A']
        if second_output:
            outputs.append('Exact B')
            edge = edge or 'bottom'
            panel = dict(during['preview']['runtime']['panels'][0], outputDescription='Exact B')
            during['preview']['runtime']['panels'].append(panel)
            during['nativeLayers'].append({'namespace':'bwm-r4-native-policy','output':'DP-B'})
        if edge is not None:
            for original, monitor, panel in zip(before['monitors'], during['monitors'], during['preview']['runtime']['panels']):
                monitor['reserved'] = original['reserved'].copy()
                monitor['reserved'][m.RESERVED_INDEX[edge]] += 48
                panel['edge'] = edge
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp);(root/'illogical-impulse').mkdir()
            (root/'illogical-impulse/config.json').write_text('{"appearance":{"bwmTheme":"plasma"}}')
            binary=root/'fixture';binary.touch();package=root/'package';package.mkdir();(package/'metadata.json').write_text('{}')
            report=root/'report.json'
            child=Mock(returncode=0);child.poll.return_value=None
            fixture=Mock();fixture.child.returncode=-15
            events=[];fixture.start.side_effect=lambda:events.append('fixture')
            results = [{'matches': True}, {'matches': shrink}]
            if not shrink: results.append({'matches': True})
            results.append({'matches': grow})
            if not grow: results.append({'matches': True})
            fixture.measure.side_effect = [{'matches': True}, ValueError('injected fixture error')] if fail_measure else results
            fixtures = [fixture]
            if second_output:
                second = Mock()
                second.child.returncode = -15
                second.measure.side_effect = [{'matches': True}, {'matches': True}, {'matches': False}, {'matches': True}]
                if fail_second_start:
                    second.start.side_effect = ValueError('injected second window startup error')
                fixtures.append(second)
            def stop(_):child.poll.return_value=130
            def confirm(_):
                if fail_stop:raise TimeoutError('injected stop error')
                child.poll.return_value=0
                return {'exitConfirmed':True,'status':'stopped','revision':4}
            argv=['smoke','--run','--maximize','--output','Exact A','--binary',str(binary),'--package',str(package),'--report',str(report)]
            if second_output:argv.extend(['--output', 'Exact B'])
            if refresh:argv.append('--refresh-area-watcher')
            if edge is not None:argv.extend(['--edge', edge])
            def reload_observer():events.append('refresh');return {'ready':True,'version':1}
            def start_panel(*args,**kwargs):events.append('panel');return child
            with patch.dict(os.environ,{'XDG_CONFIG_HOME':str(root)}),patch.object(m.sys,'argv',argv), \
                 patch.object(m.check,'collect',side_effect=[before,during,during,after]), \
                 patch.object(m.subprocess,'Popen',side_effect=start_panel),patch.object(m,'stop_child',side_effect=stop), \
                 patch.object(m,'confirm_fixture_exit',side_effect=confirm), \
                 patch.object(m,'prepare_profile',return_value=({'directory':'fixture-profile','panels':[{} for _ in outputs]},root/'unused-data')) as prepare, \
                 patch.object(m.maximized,'Fixture',side_effect=fixtures) as create,patch.object(m.maximized,'refresh_area_observer',side_effect=reload_observer), \
                 patch.object(m.time,'sleep'),contextlib.redirect_stdout(io.StringIO()):
                code=m.main()
            self.assertEqual([call.args[1] for call in create.call_args_list], outputs)
            for window in fixtures:
                window.close.assert_called_once()
            if edge is not None and not fail_second_start:
                self.assertEqual(prepare.call_args.args[-2:], (outputs, edge))
            self.maximize_events=events
            self.measure_calls=fixture.measure.call_args_list
            self.measure_calls_by_output = {output: window.measure.call_args_list for output, window in zip(outputs, fixtures)}
            return code,json.loads(report.read_text())

    def test_maximized_cli_measures_the_actual_side_reservation(self):
        code, report = self.run_maximized_main(edge='left', grow=True)
        self.assertEqual(code, 0)
        self.assertEqual(report['requestedEdge'], 'left')
        self.assertTrue(report['dynamicMaximizedWindowVerified'])
        measured = [m.maximized.useful_area(call.args[0]) for call in self.measure_calls]
        self.assertEqual(measured, [[0, 720, 2560, 1396], [48, 720, 2512, 1396], [0, 720, 2560, 1396]])

    def test_simultaneous_maximization_reports_each_output_and_its_own_fallback(self):
        code, report = self.run_maximized_main(edge='top', grow=True, second_output=True)
        self.assertEqual(code, 0)
        self.assertTrue(report['maximizedWindowVerified'])
        self.assertFalse(report['dynamicMaximizedWindowVerified'])
        frames = report['maximizedByOutput']
        self.assertEqual(frames['Exact A']['remaximizedPhases'], [])
        self.assertEqual(frames['Exact B']['remaximizedPhases'], ['after'])
        for output, calls in self.measure_calls_by_output.items():
            self.assertTrue(all(call.args[0]['description'] == output for call in calls))
            self.assertEqual(calls[1].args[0]['reserved'], [0,48,0,44])
            self.assertEqual(calls[-1].args[0]['reserved'], [0,0,0,44])

    def test_failure_starting_second_window_closes_both_and_leaves_panel_unopened(self):
        code, report = self.run_maximized_main(second_output=True, fail_second_start=True)
        self.assertEqual(code, 2)
        self.assertEqual(self.maximize_events, ['fixture'])
        self.assertEqual([frame['fixtureExitCode'] for frame in report['maximizedByOutput'].values()], [-15, -15])
        self.assertEqual(report['errors'], ['injected second window startup error'])

    def test_optional_maximized_measurement_keeps_dynamic_result_separate(self):
        code,report=self.run_maximized_main()
        self.assertEqual(code,0)
        self.assertTrue(report['maximizedWindowVerified'])
        self.assertTrue(report['realAreaVerified'])
        self.assertFalse(report['dynamicMaximizedWindowVerified'])
        self.assertFalse(report['r4Complete'])

    def test_fixture_measurement_error_still_closes_and_saves_failure(self):
        code,report=self.run_maximized_main(fail_measure=True)
        self.assertEqual(code,2)
        self.assertFalse(report['maximizedWindowVerified'])
        self.assertFalse(report['realAreaVerified'])
        self.assertTrue(report['reservationDeltaVerified'])
        self.assertEqual(report['reservationCheckErrors'],[])
        self.assertIn('injected fixture error',report['errors'])

    def test_restored_geometry_does_not_hide_missing_exit_receipt(self):
        code,report=self.run_maximized_main(fail_stop=True)
        self.assertEqual(code,2)
        self.assertFalse(report['reservationDeltaVerified'])
        self.assertFalse(report['previewExitVerified'])
        self.assertIn('injected stop error',report['previewStopError'])

    def test_observer_refresh_precedes_native_panel_and_window(self):
        code,report=self.run_maximized_main(refresh=True)
        self.assertEqual(code,0);self.assertTrue(report['areaObserverReload']['ready'])
        self.assertEqual(self.maximize_events,['refresh','fixture','panel'])

    def test_dynamic_requires_both_panel_appearance_and_withdrawal_without_remaximizing(self):
        for shrink,grow in ((True,True),(False,True),(True,False),(False,False)):
            with self.subTest(shrink=shrink,grow=grow):
                code,report=self.run_maximized_main(shrink=shrink,grow=grow)
                self.assertEqual(code,0) # Explicit measurements remain independent.
                self.assertEqual(report['dynamicMaximizedWindowVerified'],shrink and grow)
                self.assertEqual(report['dynamicMaximizedContract'],'panel-appearance-and-withdrawal')
                fallbacks = [phase for phase, matched in (('during', shrink), ('after', grow)) if not matched]
                self.assertEqual(report['remaximizedPhases'], fallbacks)
                expected = [{}]
                for matched in (shrink, grow):
                    expected.append({'remaximize': False})
                    if not matched: expected.append({})
                self.assertEqual([call.kwargs for call in self.measure_calls], expected)


if __name__ == '__main__': unittest.main()
