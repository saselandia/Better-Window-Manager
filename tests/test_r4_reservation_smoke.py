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

    def run_maximized_main(self, fail_measure=False, refresh=False, shrink=True, grow=False):
        before, during, after = snapshots()
        during['preview']['runtime']['renderReady']=True
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp);(root/'illogical-impulse').mkdir()
            (root/'illogical-impulse/config.json').write_text('{"appearance":{"bwmTheme":"plasma"}}')
            binary=root/'fixture';binary.touch();package=root/'package';package.mkdir();(package/'metadata.json').write_text('{}')
            report=root/'report.json'
            child=Mock(returncode=130);child.poll.return_value=None
            fixture=Mock();fixture.child.returncode=-15
            events=[];fixture.start.side_effect=lambda:events.append('fixture')
            fixture.measure.side_effect=[{'matches':True},ValueError('injected fixture error')] if fail_measure else [
                {'matches':True},{'matches':shrink},{'matches':True},{'matches':grow},{'matches':True}]
            def stop(_):child.poll.return_value=130
            argv=['smoke','--run','--maximize','--output','Exact A','--binary',str(binary),'--package',str(package),'--report',str(report)]
            if refresh:argv.append('--refresh-area-watcher')
            def reload_observer():events.append('refresh');return {'ready':True,'version':1}
            def start_panel(*args,**kwargs):events.append('panel');return child
            with patch.dict(os.environ,{'XDG_CONFIG_HOME':str(root)}),patch.object(m.sys,'argv',argv), \
                 patch.object(m.check,'collect',side_effect=[before,during,during,after]), \
                 patch.object(m.subprocess,'Popen',side_effect=start_panel),patch.object(m,'stop_child',side_effect=stop), \
                 patch.object(m.maximized,'Fixture',return_value=fixture),patch.object(m.maximized,'refresh_area_observer',side_effect=reload_observer), \
                 patch.object(m.time,'sleep'),contextlib.redirect_stdout(io.StringIO()):
                code=m.main()
            fixture.close.assert_called_once()
            self.maximize_events=events
            self.measure_calls=fixture.measure.call_args_list
            return code,json.loads(report.read_text())

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

    def test_observer_refresh_precedes_native_panel_and_window(self):
        code,report=self.run_maximized_main(refresh=True)
        self.assertEqual(code,0);self.assertTrue(report['areaObserverReload']['ready'])
        self.assertEqual(self.maximize_events,['refresh','fixture','panel'])

    def test_dynamic_requires_both_panel_appearance_and_withdrawal_without_remaximizing(self):
        for shrink,grow in ((True,True),(False,True),(True,False)):
            with self.subTest(shrink=shrink,grow=grow):
                code,report=self.run_maximized_main(shrink=shrink,grow=grow)
                self.assertEqual(code,0) # Explicit measurements remain independent.
                self.assertEqual(report['dynamicMaximizedWindowVerified'],shrink and grow)
                self.assertEqual(report['dynamicMaximizedContract'],'panel-appearance-and-withdrawal')
                self.assertEqual([call.kwargs for call in self.measure_calls],
                                 [{},{'remaximize':False},{},{'remaximize':False},{}])


if __name__ == '__main__': unittest.main()
