# SPDX-License-Identifier: GPL-2.0-or-later
import importlib.util
import json
import subprocess
import os
import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('r4_maximize', ROOT / 'config/hypr/skins/plasma/scripts/r4-maximized-check.py')
m = importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class MaximizedTest(unittest.TestCase):
    def test_expected_area_is_independent_of_manager_and_includes_all_reservations(self):
        monitor = {'x': 0, 'y': 720, 'width': 2560, 'height': 1440, 'scale': 1, 'transform': 0, 'reserved': [0,0,0,92]}
        self.assertEqual(m.useful_area(monitor), [0,720,2560,1348])
        monitor['reserved'] = [8,20,12,44]
        self.assertEqual(m.useful_area(monitor), [8,740,2540,1376])

    def test_unsupported_geometry_does_not_get_certified(self):
        monitor = {'x': 0, 'y': 0, 'width': 100, 'height': 100, 'scale': 1, 'transform': 0, 'reserved': [0,0,0,0]}
        for key, value in [('scale',1.25),('transform',1),('reserved',[0,0,0,101])]:
            with self.assertRaises(ValueError): m.useful_area(dict(monitor, **{key:value}))

    def test_full_frame_must_match_not_just_content_or_mode(self):
        expected = [0,720,2560,1348]
        self.assertTrue(m.frame_matches({'mode':3,'frame':expected}, expected))
        for state in ({'mode':0,'frame':expected}, {'mode':3,'frame':[0,750,2560,1318]},
                      {'mode':3,'frame':[0,720,2560,1396]}, {'mode':3,'frame':[0,720,2560,float('nan')]}, {'mode':3,'frame':[True,720,2560,1348]}):
            self.assertFalse(m.frame_matches(state,expected))

    def test_only_live_fixture_pid_class_and_valid_address_are_selected(self):
        own = {'pid':123,'class':'fixture','mapped':True,'address':'0xabc','title':'private'}
        foreign = dict(own,pid=456)
        self.assertEqual(m.select_client([foreign,own],123,'fixture'),{'pid':123,'address':'0xabc'})
        for clients in ([foreign], [dict(own, **{'class':'other'})], [own,own], [dict(own,mapped=False)], [dict(own,address='0xabc;evil')]):
            with self.assertRaises(ValueError):m.select_client(clients,123,'fixture')

    def test_commands_are_addressed_and_guarded_by_own_pid(self):
        fixture = m.Fixture(Path('/fixture'), 'Exact output')
        fixture.child = Mock(pid=123);fixture.child.poll.return_value = None
        own = {'pid':123,'class':fixture.app_id,'mapped':True,'address':'0xabc'}
        fixture.run = Mock(side_effect=[json.dumps([own]), 'ok'])
        self.assertEqual(fixture.command('maximize','--mode','full'),'ok')
        argv = fixture.run.call_args.args[0]
        self.assertEqual(argv[-6:],['--pid','123','maximize','--mode','full','0xabc'])

    def test_dead_or_replaced_fixture_is_never_mutated(self):
        fixture = m.Fixture(Path('/fixture'), 'Exact output')
        fixture.child = Mock(pid=123);fixture.child.poll.return_value = 0
        fixture.run = Mock()
        with self.assertRaises(ValueError):fixture.command('maximize','--mode','full')
        fixture.run.assert_not_called()
        fixture.child.poll.return_value = None
        fixture.run.return_value = json.dumps([{'pid':123,'class':'other','mapped':True,'address':'0xabc'}])
        with self.assertRaises(ValueError):fixture.command('maximize','--mode','full')
        self.assertEqual(fixture.run.call_count,1) # Query only; no mutation.

    def test_fixture_start_uses_the_actual_to_screen_parser_contract(self):
        spec=importlib.util.spec_from_file_location('r4_real_manager',ROOT/'config/hypr/skins/plasma/scripts/kwin-window.py')
        manager=importlib.util.module_from_spec(spec);spec.loader.exec_module(manager)
        fixture=m.Fixture(Path('/fixture'),'Exact output')
        child=Mock(pid=123);child.poll.return_value=None
        own={'pid':123,'class':fixture.app_id,'mapped':True,'address':'0xabc'}
        def invoke(argv):
            if argv[0]=='hyprctl':return json.dumps([own])
            code=manager.main(argv[2:]) # Actual argparse + PID/address guard, no IPC.
            if code:raise ValueError(f'parser rejected command: {code}')
            return ''
        fixture.run=Mock(side_effect=invoke)
        try:
            with patch.object(m.subprocess,'Popen',return_value=child), \
                 patch.object(manager,'find_client',side_effect=lambda address:own if address=='0xabc' else None), \
                 patch.object(manager,'to_screen') as move:
                fixture.start()
                move.assert_called_once_with(own,'desc:Exact output')
        finally:
            child.poll.return_value=0;fixture.close()

    def test_rejected_operation_reports_action_exit_code_and_fallback_output(self):
        fixture=m.Fixture(Path('/fixture'),'Exact output')
        with patch.object(m.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'','')):
            with self.assertRaisesRegex(ValueError,r'kwin-window to-screen \(código 1\).*sin mensaje'):
                fixture.run(['python3',str(fixture.manager),'--pid','123','to-screen','desc:Exact output','0xabc'])
        with patch.object(m.subprocess,'run',return_value=subprocess.CompletedProcess([],2,'explicit error','')):
            with self.assertRaisesRegex(ValueError,'código 2.*explicit error'):
                fixture.run(['python3',str(fixture.manager),'state','0xabc'])

    def test_correct_client_geometry_without_decoration_authority_stays_pending(self):
        fixture=m.Fixture(Path('/fixture'),'Exact output')
        borders=dict.fromkeys(('left','top','right','bottom'),0)
        fixture.command=Mock(return_value=json.dumps({'mode':3,'frame':[0,0,100,100],'borders':borders}))
        fixture.client=Mock(return_value={'address':'0xabc','pid':123})
        monitor={'x':0,'y':0,'width':100,'height':100,'scale':1,'reserved':[0,0,0,0]}
        for windows,expected in [([],False),([{'address':'0xabc','pid':456,'visible':True}],False),([{'address':'0xabc','pid':123,'visible':True,'borders':borders}],True),([{'address':'0xabc','pid':123,'visible':True,'borders':dict(borders,top=30)}],False),([{'address':'0xabc','pid':123,'visible':True,'borders':None}],False)]:
            fixture.run=Mock(return_value=json.dumps({'version':1,'api':'breezebars-csd','windows':windows}))
            with patch.object(m.time,'monotonic',side_effect=[0,5]):
                self.assertEqual(fixture.measure(monitor,remaximize=False)['matches'],expected)

    def test_bridge_refresh_requires_fresh_private_live_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker=Path(tmp)/'bwm/plasma/area-observer.json';marker.parent.mkdir(parents=True)
            start=Path(f'/proc/{os.getpid()}/stat').read_text().rsplit(')',1)[1].split()[19]
            data={'version':1,'ready':True,'pid':os.getpid(),'processStart':start,'startedAt':101}
            marker.write_text(json.dumps(data));marker.chmod(0o600)
            with patch.dict(os.environ,{'XDG_STATE_HOME':tmp}),patch.object(m.time,'time',return_value=100), \
                 patch.object(m.subprocess,'run') as restart:
                self.assertTrue(m.refresh_area_observer()['ready'])
            self.assertEqual(restart.call_args.args[0][-1],'restart')
            self.assertEqual(restart.call_args.kwargs['timeout'],20)
            data['startedAt']=99;marker.write_text(json.dumps(data))
            with patch.dict(os.environ,{'XDG_STATE_HOME':tmp}),patch.object(m.time,'time',return_value=100), \
                 patch.object(m.time,'monotonic',side_effect=[0,1,9]),patch.object(m.time,'sleep'),patch.object(m.subprocess,'run'):
                with self.assertRaises(TimeoutError):m.refresh_area_observer()

    def test_bridge_refresh_does_not_continue_after_failed_restart(self):
        with patch.object(m.subprocess,'run',side_effect=subprocess.CalledProcessError(1,'bridge')):
            with self.assertRaises(subprocess.CalledProcessError):m.refresh_area_observer()


if __name__ == '__main__':unittest.main()
