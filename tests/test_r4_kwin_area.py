# SPDX-License-Identifier: GPL-2.0-or-later
import copy
import fcntl
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('r4_area',ROOT/'config/hypr/skins/plasma/scripts/kwin_area.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class AreaTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.now=0;self.calls=[];self.actions=[]
        self.monitors=[{'id':0,'description':'MSI fixture','x':0,'y':720,'width':2560,'height':1440,'scale':1,'transform':0,'reserved':[0,0,0,92]}]
        self.clients=[{'address':'0xabc','pid':123,'monitor':0,'workspace':{'id':2,'name':'2'},'tags':['bwm-max-v','bwm-max-h'],
                       'mapped':True,'floating':True,'fullscreen':0,'fullscreenClient':0,'at':[0,748],'size':[2560,1320]}]
        self.records=[{'address':'0xabc','pid':123,'visible':True,'borders':{'left':0,'top':28,'right':0,'bottom':0}}]
        self.b=types.SimpleNamespace(STATE=Path(self.tmp.name),run=self.fake_run)
        self.runtime=m.Runtime(self.b,clock=lambda:self.now)
        self.addCleanup(self.runtime.close)
        patcher=patch.object(m,'transition_busy',return_value=False);patcher.start();self.addCleanup(patcher.stop)

    def fake_run(self,argv,timeout=None):
        self.calls.append((argv,timeout))
        if argv[1]=='dispatch':self.actions.append(argv[2]);return subprocess.CompletedProcess(argv,0,'ok','')
        data={'monitors':self.monitors,'clients':self.clients,'breezebars-csd':{'version':1,'api':'breezebars-csd','windows':self.records}}[argv[-1]]
        return subprocess.CompletedProcess(argv,0,json.dumps(data),'')

    def tick(self):
        self.runtime.tick();self.now+=.5

    def test_area_growth_reflows_and_keeps_restore_state_unchanged(self):
        restore=Path(self.tmp.name)/'restore.json';restore.write_text('{"keep":"original geometry"}')
        self.runtime.kw.STATE=restore
        self.tick();self.assertEqual(self.actions,[])
        self.monitors[0]['reserved'][3]=44;self.tick()
        self.assertEqual(len(self.actions),1)
        self.assertIn('y=1368',self.actions[0]) # Content 1396 minus the 28 px actual titlebar.
        self.assertEqual(restore.read_text(),'{"keep":"original geometry"}')
        self.assertNotIn('focus(',self.actions[0]);self.assertNotIn('window.tag(',self.actions[0])
        self.clients[0]['size'][1]=1368;self.tick();self.tick()
        self.assertEqual(len(self.actions),1)
        self.assertTrue(all(timeout==2 for _,timeout in self.calls))

    def test_output_without_edid_description_does_not_stop_tracking(self):
        # Headless/virtual outputs and monitors without EDID report an empty
        # description. They must not make the whole snapshot invalid.
        self.monitors.append(dict(self.monitors[0],id=1,name='HEADLESS-2',description='',x=4000,y=0,width=1920,height=1080,reserved=[0,0,0,44]))
        self.monitors[0]['name']='DP-2'
        self.tick();self.assertEqual(self.actions,[])
        self.monitors[0]['reserved'][3]=44;self.tick()
        self.assertEqual(len(self.actions),1)
        self.assertIn('y=1368',self.actions[0])
        self.monitors[1]['name']='';self.monitors[1]['reserved'][1]=10
        with self.assertRaisesRegex(ValueError,'identity'):self.runtime.tick()

    def test_shrink_reflows_and_each_axis_preserves_the_other(self):
        self.clients[0]['size'][1]=1368;self.tick()
        self.assertIn('y=1320',self.actions[0])
        self.assertEqual(m.target_frame((100,900,800,400),(0,720,2560,1348),1),(100,720,800,1348))
        self.assertEqual(m.target_frame((100,900,800,400),(0,720,2560,1348),2),(0,900,2560,400))

    def test_reservation_restored_before_shrink_confirmation_reflows_to_original_area(self):
        self.monitors[0].update(x=2560, y=0, width=3840, height=2160, reserved=[0,0,0,44])
        self.clients[0].update(at=[2560,28], size=[3840,2088])
        self.tick()  # Cache the original area as confirmed.
        self.assertEqual(self.actions, [])

        self.monitors[0]['reserved'][3] = 92
        self.tick()
        self.assertEqual(len(self.actions), 1)
        self.assertIn('y=2040', self.actions[0])

        # The shrink applied, but the panel disappeared before the next poll.
        self.clients[0]['size'][1] = 2040
        self.monitors[0]['reserved'][3] = 44
        self.tick()
        self.assertEqual(len(self.actions), 2)
        self.assertIn('y=2088', self.actions[1])
        self.clients[0]['size'][1] = 2088
        self.tick()
        self.assertEqual(len(self.actions), 2)

    def test_normal_native_fullscreen_special_hidden_and_optout_are_excluded(self):
        variants=[{'tags':[]},{'floating':False},{'mapped':False},{'hidden':True},{'fullscreen':2},{'fullscreen':1},
                  {'fullscreenClient':2},{'workspace':{'id':-1,'name':'special:magic'}},{'workspace':{'id':99,'name':'99'}},
                  {'tags':['bwm-max-v','bwm-ignore-kwin-rules']},{'tags':['bwm-max-v','bwm-ignore-maximized-area']},
                  {'tags':['bwm-max-v','snapped_left']},{'pid':True},{'address':'0xabc;evil'},{'workspace':'bad'}]
        for change in variants:
            with self.subTest(change=change):self.assertFalse(m.eligible(dict(self.clients[0],**change),self.runtime.kw))

    def test_minimized_window_is_reconsidered_when_restored(self):
        self.tick();self.clients[0]['workspace']={'id':-5,'name':'special:minimized'}
        self.monitors[0]['reserved'][3]=44;self.tick();self.assertFalse(self.actions)
        self.clients[0]['workspace']={'id':2,'name':'2'};self.tick();self.assertEqual(len(self.actions),1)

    def test_pid_reuse_and_missing_decoration_never_use_old_records(self):
        self.tick();self.clients[0]['pid']=456;self.monitors[0]['reserved'][3]=44
        self.tick();self.assertFalse(self.actions)
        self.records[0]['pid']=456;self.tick();self.assertEqual(len(self.actions),1)
        self.assertIn('w.pid~=456',self.actions[0])

    def test_bounded_retries_do_not_fight_forced_geometry_forever(self):
        self.clients[0]['size'][1]=1368
        with patch.object(self.runtime,'log_error') as log:
            for _ in range(7):self.tick()
            self.assertEqual(len(self.actions),3);self.assertEqual(log.call_count,1)
        self.monitors[0]['reserved'][3]=100;self.tick();self.assertEqual(len(self.actions),4)

    def test_area_transition_without_decoration_resets_old_retry_budget(self):
        self.clients[0]['size'][1] = 1368
        for _ in range(5): self.tick()
        self.assertEqual(len(self.actions), 3)

        records, self.records = self.records, []
        self.monitors[0]['reserved'][3] = 44
        self.tick()
        self.assertEqual(len(self.actions), 3)

        self.records = records
        self.monitors[0]['reserved'][3] = 92
        self.tick()
        self.assertEqual(len(self.actions), 4)

    def test_explicit_kde_force_geometry_wins_and_removal_reconsiders_window(self):
        self.runtime.rules=types.SimpleNamespace(rules=[],last_text='force size')
        resolver=Mock(return_value={'size':{'mode':2}})
        self.b.kwin_rules=types.SimpleNamespace(resolve=resolver)
        self.clients[0]['size'][1]=1368;self.tick();self.assertFalse(self.actions)
        resolver.return_value={};self.runtime.rules.last_text='force removed'
        self.tick();self.assertEqual(len(self.actions),1)

    def test_transition_busy_and_poll_coalescing_produce_no_mutations(self):
        with patch.object(m,'transition_busy',return_value=True):self.runtime.tick()
        self.assertEqual(self.calls,[])
        self.now=1;self.runtime.tick();count=len(self.calls)
        self.runtime.tick();self.assertEqual(len(self.calls),count)

    def test_projection_uses_logical_rotated_scaled_geometry(self):
        monitor=dict(self.monitors[0],x=-1920,y=0,width=3840,height=2160,scale=1.5,transform=1,reserved=[10,20,30,40])
        self.assertEqual(m.area(monitor,self.runtime.kw),(-1910,20,1400,2500))

    def test_reflow_matches_rounded_logical_extents(self):
        monitor = dict(self.monitors[0], x=-200, y=10, width=251, height=333, scale=2,
                       transform=1, reserved=[2, 3, 4, 5])
        self.assertEqual(m.area(monitor, self.runtime.kw), (-198, 13, 161, 118))

    def test_unchanged_other_output_is_not_reflowed(self):
        self.monitors.append(dict(self.monitors[0],id=1,description='Other fixture',x=2560,y=0,width=1000,height=800,reserved=[0,0,0,44]))
        self.clients.append(dict(self.clients[0],address='0xdef',pid=456,monitor=1,at=[2560,28],size=[1000,728]))
        self.records.append(dict(self.records[0],address='0xdef',pid=456))
        self.tick();self.assertFalse(self.actions)
        self.monitors[0]['reserved'][3]=44;self.tick()
        self.assertEqual(len(self.actions),1);self.assertIn('address:0xabc',self.actions[0]);self.assertNotIn('address:0xdef',self.actions[0])

    def test_changed_windows_are_batched_in_one_ipc_with_separate_pid_guards(self):
        self.clients.append(dict(self.clients[0],address='0xdef',pid=456))
        self.records.append(dict(self.records[0],address='0xdef',pid=456))
        self.tick();self.monitors[0]['reserved'][3]=44;self.tick()
        self.assertEqual(len(self.actions),1)
        self.assertIn('w.pid~=123',self.actions[0]);self.assertIn('w.pid~=456',self.actions[0])

    def test_transition_lock_probe_is_nonblocking_and_does_not_follow_aliases(self):
        path=Path(self.tmp.name)/'transition.lock'
        # Use the real implementation despite setUp's runtime safety stub.
        spec=importlib.util.spec_from_file_location('r4_lock_area',ROOT/'config/hypr/skins/plasma/scripts/kwin_area.py')
        real=importlib.util.module_from_spec(spec);spec.loader.exec_module(real)
        with path.open('w') as owner:
            self.assertFalse(real.transition_busy(path))
            fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
            self.assertTrue(real.transition_busy(path))
        alias=path.with_name('alias');alias.symlink_to(path)
        self.assertTrue(real.transition_busy(alias))

    def test_malformed_geometry_fails_closed_without_partial_dispatch(self):
        self.monitors[0]['reserved']=[0,0,0,float('nan')]
        with self.assertRaises(ValueError):self.tick()
        self.assertEqual(self.actions,[])

    def test_readiness_marker_is_private_owned_and_removed_only_by_owner(self):
        self.tick();path=self.runtime.ready
        data=json.loads(path.read_text());self.assertTrue(data['ready'])
        self.assertEqual(path.stat().st_mode&0o777,0o600)
        data['pid']=-1;path.write_text(json.dumps(data));self.runtime.close();self.assertTrue(path.exists())

    @unittest.skipUnless(shutil.which('lua'),'Lua interpreter required for compositor-side guard fixture')
    def test_generated_lua_guards_live_state_not_just_snapshot(self):
        client=self.clients[0];work=(0,720,2560,1396);borders=self.records[0]['borders']
        code=m.command(client,work,borders,self.runtime.kw)
        prefix='''local actions={}
          local w={pid=123,mapped=true,hidden=false,floating=true,fullscreen=0,fullscreen_client=0,
            workspace={id=2},monitor={id=0},tags={"bwm-max-v","bwm-max-h"}}
          package.loaded["modules.theme"]={name="plasma"}
          hl={dsp={no_op=function() return {} end,window={
            resize=function(o) o.action="resize" return o end,move=function(o) o.action="move" return o end}}}
          hl.get_window=function() return w end
          hl.dispatch=function(o) if o.action then table.insert(actions,o) end end
        '''
        for mutation,count in [('',2),('w.pid=456',0),('w.fullscreen=2',0),('w.floating=false',0),
                               ('w.workspace.id=-1',0),('w.monitor.id=1',0),('w.tags={}',0),
                               ('w.tags={"bwm-max-v","bwm-max-h","bwm-ignore-maximized-area"}',0),
                               ('package.loaded["modules.theme"].name="retro"',0)]:
            program=prefix+'\n'+mutation+'\nlocal result='+code+'\nprint(#actions)\n'
            reply=subprocess.run(['lua','-'],input=program,capture_output=True,text=True,timeout=3)
            self.assertEqual(reply.returncode,0,reply.stderr);self.assertEqual(int(reply.stdout.strip()),count)

    @unittest.skipUnless(shutil.which('lua'),'Lua interpreter required for compositor-side batch fixture')
    def test_generated_batch_lua_executes_each_guarded_target(self):
        self.clients.append(dict(self.clients[0],address='0xdef',pid=456))
        self.records.append(dict(self.records[0],address='0xdef',pid=456))
        self.tick();self.monitors[0]['reserved'][3]=44;self.tick()
        prefix='''local count=0
          local function window(pid) return {pid=pid,mapped=true,hidden=false,floating=true,
            fullscreen=0,fullscreen_client=0,workspace={id=2},monitor={id=0},tags={"bwm-max-v","bwm-max-h"}} end
          local windows={["address:0xabc"]=window(123),["address:0xdef"]=window(456)}
          package.loaded["modules.theme"]={name="plasma"}
          hl={dsp={no_op=function() return {} end,window={
            resize=function(o) o.action="resize" return o end,move=function(o) o.action="move" return o end}}}
          hl.get_window=function(address) return windows[address] end
          hl.dispatch=function(o) if o.action then count=count+1 end end
        '''
        reply=subprocess.run(['lua','-'],input=prefix+'\nlocal result='+self.actions[0]+'\nprint(count)',capture_output=True,text=True,timeout=3)
        self.assertEqual(reply.returncode,0,reply.stderr);self.assertEqual(reply.stdout.strip(),'4')


if __name__=='__main__':unittest.main()
