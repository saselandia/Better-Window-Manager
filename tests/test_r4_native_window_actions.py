# SPDX-License-Identifier: GPL-2.0-or-later
"""Native move/resize, no-border and hide-from-capture through the common manager (§252)."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'config/hypr/skins/plasma/scripts'
spec=importlib.util.spec_from_file_location('r4_window_actions',SCRIPTS/'kwin-window.py')
kw=importlib.util.module_from_spec(spec);spec.loader.exec_module(kw)
spec=importlib.util.spec_from_file_location('r4_window_tasks',SCRIPTS/'native-tasks.py')
nt=importlib.util.module_from_spec(spec);spec.loader.exec_module(nt)


def done(stdout='',code=0):return subprocess.CompletedProcess([],code,stdout=stdout)


class KwinWindowNativeTest(unittest.TestCase):
    def setUp(self):
        self.client={'address':'0xabc','pid':123,'mapped':True,'hidden':False,'floating':True,'fullscreen':0,
                     'workspace':{'id':2,'name':'2'},'tags':[]}

    def test_tag_is_desired_state_with_receipt_and_fresh_readback(self):
        tagged=dict(self.client,tags=[kw.TAG_NO_CAPTURE])
        with patch.object(kw.subprocess,'run',return_value=done('bwm-r4-tag-ok')) as run, \
             patch.object(kw,'hypr_json',return_value=[tagged]):
            self.assertTrue(kw.native_tag(self.client,kw.TAG_NO_CAPTURE,True))
            self.assertEqual(run.call_args.args[0][:2],['hyprctl','repl'])
            self.assertIn('"+bwm-no-capture"',run.call_args.args[0][2])
            run.reset_mock()
            self.assertTrue(kw.native_tag(tagged,kw.TAG_NO_CAPTURE,True)) # Already set: idempotent, no dispatch.
            run.assert_not_called()
        with patch.object(kw.subprocess,'run',return_value=done('bwm-r4-tag-ok')), \
             patch.object(kw,'hypr_json',return_value=[self.client]):
            self.assertFalse(kw.native_tag(self.client,kw.TAG_NO_CAPTURE,True)) # Readback disagrees.
        with patch.object(kw.subprocess,'run',return_value=done('bwm-r4-tag-ok')), \
             patch.object(kw,'hypr_json',return_value=[dict(tagged,pid=456)]):
            self.assertFalse(kw.native_tag(self.client,kw.TAG_NO_CAPTURE,True)) # Reused address.
        for receipt in ('ok','','bwm-r4-tag-rejected'):
            with self.subTest(receipt=receipt),patch.object(kw.subprocess,'run',return_value=done(receipt)),patch.object(kw,'hypr_json') as fresh:
                self.assertFalse(kw.native_tag(self.client,kw.TAG_NO_BORDER,True));fresh.assert_not_called()
        for changes in ({'hidden':True},{'pinned':True},{'mapped':False},{'workspace':{'id':-98,'name':'special:minimized'}}):
            with self.subTest(changes=changes),patch.object(kw.subprocess,'run') as run:
                self.assertFalse(kw.native_tag(dict(self.client,**changes),kw.TAG_NO_BORDER,True));run.assert_not_called()

    @unittest.skipUnless(shutil.which('lua'),'lua required')
    def test_tag_lua_guards_run_before_dispatch(self):
        prefix='''local calls=0
local w={pid=123,mapped=true,hidden=false,pinned=false,workspace={id=2,name="2"}}
package.loaded["modules.theme"]={name="plasma"}
hl={dsp={window={tag=function(o) return o end}}}
hl.get_window=function() return w end
hl.dispatch=function(o) calls=calls+1 assert(o.tag=="+bwm-no-border" and o.window==w) return {ok=true} end
'''
        code=kw.native_tag_lua(self.client,kw.TAG_NO_BORDER,True)
        for mutation,receipt,count in [('','ok',1),('w.pid=456','rejected',0),('w.hidden=true','rejected',0),('w.pinned=true','rejected',0),
                                       ('w.workspace.id=99','rejected',0),('w.workspace.name="special:minimized"','rejected',0),
                                       ('package.loaded["modules.theme"].name="retro"','rejected',0)]:
            with self.subTest(mutation=mutation):
                reply=subprocess.run(['lua','-'],input=prefix+mutation+'\nprint('+code+')\nprint(calls)',capture_output=True,text=True,timeout=2)
                self.assertEqual(reply.returncode,0,reply.stderr)
                self.assertEqual(reply.stdout.splitlines(),['bwm-r4-tag-'+receipt,str(count)])

    def test_interactive_requires_floating_normal_window_and_plugin_ok(self):
        with patch.object(kw.subprocess,'run',return_value=done('ok\n')) as run:
            self.assertTrue(kw.native_interactive(self.client,'move'))
            self.assertEqual(run.call_args.args[0],['hyprctl','breezebars-interactive','move 0xabc'])
            for changes in ({'floating':False},{'fullscreen':1},{'hidden':True},{'workspace':{'id':-98,'name':'special:minimized'}}):
                run.reset_mock()
                with self.subTest(changes=changes):self.assertFalse(kw.native_interactive(dict(self.client,**changes),'resize'));run.assert_not_called()
        for reply in ('no se puede','unknown request',''):
            with self.subTest(reply=reply),patch.object(kw.subprocess,'run',return_value=done(reply)):
                self.assertFalse(kw.native_interactive(self.client,'resize'))

    def test_native_cli_requires_identity_and_explicit_state(self):
        for argv in (['--native-serialized','no-capture','0xabc'],
                     ['--native-serialized','--pid','123','--expected-generation','1','no-border','--state','toggle','0xabc'],
                     ['--native-serialized','interactive','move','0xabc'],
                     ['--native-serialized','--pid','123','--expected-generation','1','pin','0xabc']):
            with self.subTest(argv=argv),self.assertRaises(SystemExit):kw.main(argv)

    def test_daily_toggle_unchanged_and_state_option_is_idempotent(self):
        with patch.object(kw,'find_client',return_value=self.client),patch.object(kw,'toggle_tag') as toggle:
            self.assertEqual(kw.main(['no-capture','0xabc']),0);toggle.assert_called_once()
            toggle.reset_mock();self.assertEqual(kw.main(['no-capture','--state','off','0xabc']),0);toggle.assert_not_called()
            self.assertEqual(kw.main(['no-border','--state','on','0xabc']),0);toggle.assert_called_once()


class NativeTasksWindowActionTest(unittest.TestCase):
    def setUp(self):
        self.client={'address':'0xabc','pid':123,'mapped':True,'hidden':False,'floating':True,'fullscreen':0,'workspace':{'id':2,'name':'2'},
                     'at':[100,200],'size':[800,600],'class':'fixture','title':'Title','tags':['bwm-no-capture'],'monitor':0}
        self.monitors=[{'id':0,'x':0,'y':0,'width':1920,'height':1080,'scale':1,'transform':0,'specialWorkspace':{'id':0}}]
        p=patch.object(nt.bwm_windows,'process_generation',return_value='123456');p.start();self.addCleanup(p.stop)

    def test_snapshot_fields(self):
        row=nt.record(self.client,{},self.monitors)
        self.assertEqual({k:row[k] for k in ('movable','windowTagsSettable','noBorder','excludedFromCapture')},
                         {'movable':True,'windowTagsSettable':True,'noBorder':False,'excludedFromCapture':True})
        self.assertFalse(nt.record(dict(self.client,floating=False),{},self.monitors)['movable'])
        hidden=dict(self.client,workspace={'id':-98,'name':'special:minimized'},tags=['omarchy-minimized-from-2'])
        row=nt.record(hidden,{},self.monitors);self.assertFalse(row['movable']);self.assertFalse(row['windowTagsSettable'])

    def test_actions_forward_to_common_manager(self):
        with tempfile.TemporaryDirectory() as tmp:
            config=Path(tmp)/'illogical-impulse';config.mkdir();(config/'config.json').write_text('{"appearance":{"bwmTheme":"plasma"}}')
            req={'version':1,'address':'0xabc','pid':123,'generation':'123456'}
            with patch.dict(os.environ,{'XDG_CONFIG_HOME':tmp}),patch.object(nt,'query',return_value=[self.client]), \
                 patch.object(nt.subprocess,'run',return_value=done()) as run:
                for request,tail in ((dict(req,action='move'),['interactive','move','0xabc']),(dict(req,action='resize'),['interactive','resize','0xabc']),
                                     (dict(req,action='no-border',state=True),['no-border','--state','on','0xabc']),
                                     (dict(req,action='no-capture',state=False),['no-capture','--state','off','0xabc'])):
                    self.assertTrue(nt.action(request)['accepted'])
                    self.assertEqual(run.call_args.args[0][-len(tail):],tail)
                    self.assertIn('--native-serialized',run.call_args.args[0])
                run.reset_mock()
                for bad in (dict(req,action='no-border'),dict(req,action='no-capture',state='on'),dict(req,action='keep-above')):
                    with self.subTest(bad=bad),self.assertRaises(ValueError):nt.action(bad)
                run.assert_not_called()


class PlacesSnapshotTest(unittest.TestCase):
    def test_read_only_copy_bounded_and_exclusive(self):
        context=nt.launch_context
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'source';host=Path(tmp)/'host';source.mkdir();host.mkdir()
            self.assertFalse(context.snapshot_places(source,host)) # No user file: KDE defaults later.
            (source/'user-places.xbel').write_text('<xbel/>')
            before=(source/'user-places.xbel').stat().st_mtime_ns
            self.assertTrue(context.snapshot_places(source,host))
            self.assertEqual((host/'user-places.xbel').read_text(),'<xbel/>')
            self.assertEqual((host/'user-places.xbel').stat().st_mode&0o777,0o600)
            self.assertEqual((source/'user-places.xbel').stat().st_mtime_ns,before)
            with self.assertRaises(ValueError):context.snapshot_places(source,host)
            (host/'user-places.xbel').unlink();(source/'user-places.xbel').write_text('x'*20)
            with self.assertRaises(ValueError):context.snapshot_places(source,host,limit=10)
            (source/'user-places.xbel').unlink();(source/'user-places.xbel').mkdir()
            with self.assertRaises((ValueError,IsADirectoryError,OSError)):context.snapshot_places(source,host)


if __name__=='__main__':unittest.main()
