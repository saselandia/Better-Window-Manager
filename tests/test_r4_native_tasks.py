# SPDX-License-Identifier: GPL-2.0-or-later
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('r4_tasks',ROOT/'config/hypr/skins/plasma/scripts/native-tasks.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class NativeTaskTest(unittest.TestCase):
    def setUp(self):
        self.client={'address':'0xabc','pid':123,'mapped':True,'hidden':False,'workspace':{'id':2,'name':'2'},
                     'at':[100,200],'size':[800,600],'class':'fixture','title':'Test title','tags':[],'monitor':0}
        self.monitors=[{'id':0,'x':0,'y':0,'width':1920,'height':1080,'scale':1,'transform':0,'specialWorkspace':{'id':0}}]
        p=patch.object(m.bwm_windows,'process_generation',return_value='123456');p.start();self.addCleanup(p.stop)

    def test_normal_snapshot_roles_and_active_pid_are_coherent(self):
        row=m.record(self.client,{'address':'0xabc','pid':123},self.monitors)
        self.assertEqual(row['generation'],'123456');self.assertEqual(row['geometry'],[100,200,800,600])
        self.assertEqual(row['screen'],[0,0,1920,1080]);self.assertTrue(row['active']);self.assertFalse(row['minimized'])
        self.assertFalse(m.record(self.client,{'address':'0xabc','pid':456},self.monitors)['active'])

    def test_hidden_and_minimized_origins_follow_common_contract(self):
        c=copy.deepcopy(self.client);c['workspace']={'id':-98,'name':'special:minimized'};c['tags']=['omarchy-minimized-from-2']
        self.assertTrue(m.record(c,{},self.monitors)['minimized']);self.assertEqual(m.record(c,{},self.monitors)['workspace'],'2')
        c['tags']=[m.minimizer.SPECIAL_TAG_PREFIX+'special:magic'.encode().hex()]
        self.assertEqual(m.record(c,{},self.monitors)['workspace'],'special:magic')
        c['tags']=[];self.assertIsNone(m.record(c,{},self.monitors))

    def test_special_only_visible_by_monitor_workspace_id(self):
        c=copy.deepcopy(self.client);c['workspace']={'id':-9,'name':'special:magic'}
        self.assertIsNone(m.record(c,{},self.monitors))
        self.monitors[0]['specialWorkspace']={'id':-9,'name':'magic'}
        self.assertEqual(m.record(c,{},self.monitors)['workspace'],'special:magic')

    def test_invalid_or_unmapped_identity_and_geometry_are_excluded(self):
        for update in ({'pid':True},{'address':'0xabc;unsafe'},{'mapped':False},{'hidden':True},{'at':[1]}, {'size':[0,10]}):
            with self.subTest(update=update):self.assertIsNone(m.record(dict(self.client,**update),{},self.monitors))
        with patch.object(m.bwm_windows,'process_generation',return_value=''):
            self.assertIsNone(m.record(self.client,{},self.monitors))

    def test_native_maximize_and_fullscreen_are_distinct(self):
        self.assertTrue(m.record(dict(self.client,fullscreen=1),{},self.monitors)['maximized'])
        self.assertFalse(m.record(dict(self.client,fullscreen=1),{},self.monitors)['fullscreen'])
        self.assertTrue(m.record(dict(self.client,fullscreen=2),{},self.monitors)['fullscreen'])
        self.assertTrue(m.record(dict(self.client,pinned=True),{},self.monitors)['onAllDesktops'])

    def test_fullscreen_capability_excludes_minimized_and_special_storage(self):
        self.assertTrue(m.record(self.client,{},self.monitors)['fullscreenable'])
        c=copy.deepcopy(self.client);c['workspace']={'id':-98,'name':'special:minimized'};c['tags']=['omarchy-minimized-from-2']
        self.assertFalse(m.record(c,{},self.monitors)['fullscreenable'])
        c['workspace']={'id':-9,'name':'special:magic'};c['tags']=[]
        self.monitors[0]['specialWorkspace']={'id':-9,'name':'magic'}
        self.assertFalse(m.record(c,{},self.monitors)['fullscreenable'])

    def test_fullscreen_desired_state_is_validated_and_forwarded_without_toggle(self):
        with tempfile.TemporaryDirectory() as tmp:
            config=Path(tmp)/'illogical-impulse';config.mkdir();(config/'config.json').write_text('{"appearance":{"bwmTheme":"plasma"}}')
            req={'version':1,'address':'0xabc','pid':123,'generation':'123456','action':'fullscreen'}
            with patch.dict(os.environ,{'XDG_CONFIG_HOME':tmp}),patch.object(m,'query',return_value=[self.client]), \
                 patch.object(m.subprocess,'run',return_value=subprocess.CompletedProcess([],0)) as run:
                for state in (True,False):
                    self.assertTrue(m.action(dict(req,state=state))['accepted'])
                    self.assertEqual(run.call_args.args[0][-6:],['--pid','123','fullscreen','--state','on' if state else 'off','0xabc'])
                for state in (None,0,1,'on'):
                    run.reset_mock()
                    with self.assertRaises(ValueError):m.action(dict(req,state=state))
                    run.assert_not_called()
                run.reset_mock()
                hidden=dict(self.client,workspace={'id':-98,'name':'special:minimized'},tags=['omarchy-minimized-from-2'])
                with patch.object(m,'query',return_value=[hidden]):
                    with self.assertRaisesRegex(ValueError,'not available'):m.action(dict(req,state=True))
                    run.assert_not_called()
                run.return_value=subprocess.CompletedProcess([],1)
                with self.assertRaisesRegex(ValueError,'rejected'):m.action(dict(req,state=True))

    def test_duplicate_or_failed_ipc_snapshot_is_not_successful_empty_model(self):
        with patch.object(m,'query',side_effect=[[self.client,self.client],{},self.monitors]):
            with self.assertRaisesRegex(ValueError,'Duplicate'):m.snapshot()
        with patch.object(m,'query',side_effect=subprocess.TimeoutExpired('hyprctl',2)):
            with self.assertRaises(subprocess.TimeoutExpired):m.snapshot()

    def test_snapshot_preserves_bottom_to_top_client_order_after_filtering(self):
        excluded=dict(self.client,address='0x000',mapped=False)
        other=dict(self.client,address='0xdef',pid=456,focusHistoryID=0)
        first=dict(self.client,focusHistoryID=99)
        with patch.object(m,'query',side_effect=[[excluded,first,other],{},self.monitors]):
            rows=m.snapshot()['windows']
        self.assertEqual([(r['address'],r['stackingOrder']) for r in rows],[('0xabc',1),('0xdef',2)])
        with patch.object(m,'query',side_effect=[[other,first],{},self.monitors]):
            rows=m.snapshot()['windows']
        self.assertEqual([(r['address'],r['stackingOrder']) for r in rows],[('0xdef',0),('0xabc',1)])

    def test_guarded_action_routes_to_existing_manager_and_rejects_stale_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            config=Path(tmp)/'illogical-impulse';config.mkdir();(config/'config.json').write_text('{"appearance":{"bwmTheme":"plasma"}}')
            req={'version':1,'address':'0xabc','pid':123,'generation':'123456','action':'focus'}
            with patch.dict(os.environ,{'XDG_CONFIG_HOME':tmp}),patch.object(m,'query',return_value=[self.client]), \
                 patch.object(m.subprocess,'run',return_value=subprocess.CompletedProcess([],0)) as run:
                for name in ('focus','toggle-minimize','maximize','close'):
                    self.assertTrue(m.action(dict(req,action=name))['accepted'])
                    self.assertEqual(run.call_args.args[0][-4:],['--pid','123',name,'0xabc'])
                run.reset_mock()
                with self.assertRaises(ValueError):m.action(dict(req,version=True))
                run.assert_not_called()
                with self.assertRaisesRegex(ValueError,'identity'):m.action(dict(req,generation='stale'))
                run.assert_not_called()
                with self.assertRaises(ValueError):m.action(dict(req,action='exec'))
                run.assert_not_called()
                (config/'config.json').write_text('{"appearance":{"bwmTheme":"retro"}}')
                with self.assertRaisesRegex(ValueError,'Breeze'):m.action(req)
                run.assert_not_called()


if __name__=='__main__':unittest.main()
