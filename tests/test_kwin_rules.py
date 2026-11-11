"""KWin format/order/modes/identity/write-conflict tests; no real desktop changes."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'config/hypr/skins/plasma/scripts'
sys.path.insert(0,str(SCRIPTS))
import kwin_rules as rules
import kwin_tiles as tiles

class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        spec=importlib.util.spec_from_file_location('f10_test_bridge',SCRIPTS/'kde-config-bridge.py')
        self.b=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.b)
        self.b.CONFIG=self.root/'config';self.b.STATE=self.root/'state';self.b.CONFIG.mkdir()
        self.b.run=Mock(return_value=subprocess.CompletedProcess([],0,'[]',''))
    def write(self,text):
        p=self.b.CONFIG/'kwinrulesrc';p.write_text(text);return p

class RuleTests(Fixture):
    def test_order_per_property_and_dont_affect(self):
        text='[General]\nrules=b,a\n[b]\nwmclass=app\nwmclassmatch=1\nnoborderrule=1\n[a]\nnoborderrule=2\nnoborder=true\npositionrule=3\nposition=20,30\n'
        parsed,issues=rules.parse(text,self.b.ini)
        self.assertFalse(issues)
        p=rules.resolve(parsed,{'class':'app'})
        self.assertEqual(p['noborder']['mode'],1)
        self.assertEqual(p['position']['value'],[20,30])
        self.assertEqual(rules.resolve(parsed,{'class':'other'})['noborder']['value'],True)
    def test_legacy_order_disabled_and_malformed_selectors_fail_closed(self):
        parsed,issues=rules.parse('[General]\ncount=3\n[1]\nEnabled=false\n[2]\nwindowrolematch=1\nwindowrole=dialog\n[3]\nwmclassmatch=3\nwmclass=[\n',self.b.ini)
        self.assertEqual(len(parsed),1);self.assertTrue(issues)
        self.assertFalse(rules.matches(parsed[0],{'class':'app'}))
    def test_types_roles_regex_and_transient(self):
        parsed,_=rules.parse('[General]\nrules=x\n[x]\nwmclassmatch=3\nwmclass=app.*\nwindowrolematch=2\nwindowrole=dlg\ntitlematch=2\ntitle=Config\ntypes=32\nhastransientparentmatch=1\nhastransientparent=true\n',self.b.ini)
        c={'class':'app2','title':'Configure','kdeMetadata':{'known':True,'role':'settings-dlg','typeMask':32,'parent':True}}
        self.assertTrue(rules.matches(parsed[0],c));c['kdeMetadata']['typeMask']=1
        self.assertFalse(rules.matches(parsed[0],c))
    def test_remember_without_initial_size_still_remembers(self):
        parsed,issues=rules.parse('[General]\nrules=a\n[a]\nsizerule=4\nsize=0,0\n',self.b.ini)
        self.assertFalse(issues)
        self.assertEqual(parsed[0]['props']['size']['mode'],4)
        self.assertIsNone(parsed[0]['props']['size']['value'])
    def test_unsupported_selector_never_broadens_rule(self):
        parsed,issues=rules.parse('[General]\nrules=x\n[x]\nwmclasscomplete=true\nwmclassmatch=1\nwmclass=instance app\nnoborderrule=2\nnoborder=true\n',self.b.ini)
        self.assertEqual(parsed,[]);self.assertTrue(issues)
    def test_unsupported_policies_reported_and_quoted_data_stays_data(self):
        text='[General]\nrules=x\n[x]\nwmclassmatch=1\nwmclass="; os.execute("bad")\naboverule=2\nabove=true\nminimizerule=5\nminimize=true\nnoborderrule=2\nnoborder=true\n'
        parsed,issues=rules.parse(text,self.b.ini)
        self.assertEqual(len(issues),2);self.assertEqual(set(parsed[0]['props']),{'noborder','minimize'})
        self.assertEqual(parsed[0]['props']['minimize']['mode'],1)
        self.write(text);rules.generate(self.b)
        content=(self.b.STATE/'kwinrules.lua').read_text()
        self.assertNotIn('os.execute',content);self.assertIn('decorate = false',content)
    def test_independent_opacity_properties_compose(self):
        text='[General]\nrules=a,b\n[a]\nopacityactiverule=2\nopacityactive=80\n[b]\nopacityinactiverule=2\nopacityinactive=45\n'
        parsed,_=rules.parse(text,self.b.ini);props=rules.resolve(parsed,{})
        key=rules.tag('opacity',(80,45))
        self.assertIn(key,rules.desired_tags(props))
        self.assertEqual(rules.native_cases(parsed)[key]['opacity'],'0.8 override 0.45 override')
    def test_apply_and_remember_are_not_native_forced_effects(self):
        text='[General]\nrules=a\n[a]\nnoborderrule=3\nnoborder=true\nexcludefromcapturerule=4\nexcludefromcapture=true\n'
        parsed,_=rules.parse(text,self.b.ini)
        self.assertFalse(rules.desired_tags(rules.resolve(parsed,{})))
        self.assertNotIn(rules.tag('noborder',True),rules.native_cases(parsed))
    def test_remember_preserves_foreign_text_and_conflicts(self):
        p=self.write('# keep\n[General]\nrules=a\n[a]\npositionrule=4\nposition=1,2\ncustom=untouched\n')
        rt=rules.Runtime(self.b)
        entry={'props':{'position':{'mode':4,'group':'a','raw':'1,2'}},'values':{'position':'10,20'}}
        rt.remember(entry)
        self.assertIn('position=10,20',p.read_text());self.assertIn('# keep',p.read_text());self.assertIn('custom=untouched',p.read_text())
        p.write_text(p.read_text().replace('10,20','500,600'));rt.remember(entry)
        self.assertIn('position=500,600',p.read_text())
    def test_apply_initial_once_force_again_and_reused_pid_is_new(self):
        self.write('[General]\nrules=a\n[a]\npositionrule=3\nposition=1,2\nsizerule=2\nsize=500,400\n')
        c={'address':'0xa','pid':1,'class':'app','at':[0,0],'size':[100,100],'workspace':{'id':1,'name':'1'},'tags':['bwm-kwin-new']}
        self.b.run.side_effect=lambda args:subprocess.CompletedProcess(args,0,json.dumps([c]) if args[-1]=='clients' else '{"windows":[]}','')
        rt=rules.Runtime(self.b);rt.apply=Mock()
        rt.tick();self.assertEqual(set(rt.apply.call_args.args[1]),{'position','size'})
        rt.tick();self.assertEqual(set(rt.apply.call_args.args[1]),{'size'})
        c['pid']=2;rt.tick();self.assertEqual(set(rt.apply.call_args.args[1]),{'position','size'})
    def test_existing_windows_do_not_receive_initial_geometry_on_skin_switch(self):
        self.write('[General]\nrules=a\n[a]\npositionrule=3\nposition=1,2\n')
        c={'address':'0xa','pid':1,'class':'app','workspace':{'id':1},'tags':[]}
        self.b.run.side_effect=lambda args:subprocess.CompletedProcess(args,0,json.dumps([c]) if args[-1]=='clients' else '{"windows":[]}','')
        rt=rules.Runtime(self.b);rt.apply=Mock();rt.tick()
        self.assertEqual(rt.apply.call_args.args[1],{})
    def test_no_rules_means_no_ipc_and_user_opt_out(self):
        rt=rules.Runtime(self.b);rt.tick();self.b.run.assert_not_called()
        self.write('[General]\nrules=a\n[a]\nsizerule=2\nsize=500,400\n')
        c={'address':'0xa','pid':1,'tags':['bwm-ignore-kwin-rules*']}
        self.b.run.side_effect=lambda args:subprocess.CompletedProcess(args,0,json.dumps([c]) if args[-1]=='clients' else '{"windows":[]}','')
        rt.apply=Mock();rt.tick();rt.apply.assert_not_called()

class TileTests(Fixture):
    def test_original_tree_nested_and_last_child_fills_remainder(self):
        tree={'layoutDirection':'horizontal','tiles':[{'width':.4,'layoutDirection':'vertical','tiles':[{'height':.6},{'height':.4}]},{'width':.1}]}
        result=tiles.leaves(tree)
        self.assertEqual(len(result),3);self.assertAlmostEqual(result[-1]['width'],.6)
        self.assertAlmostEqual(result[1]['y'],.6)
        self.assertEqual(tiles.leaves(tiles.DEFAULT)[1]['width'],.5)
    def test_split_join_and_ratio_keep_original_format(self):
        tree=tiles.split({},[],'horizontal')
        tree=tiles.resize_split(tree,[0],.3)
        self.assertEqual(tiles.leaves(tree)[0]['width'],.3)
        self.assertEqual(tiles.join(tree,[0]),{})
    def test_resize_three_columns_uses_actual_parent_proportions(self):
        tree=tiles.resize_split(tiles.DEFAULT,[1],.6)
        rects=tiles.leaves(tree)
        self.assertAlmostEqual(rects[0]['width'],.2)
        self.assertAlmostEqual(rects[1]['width'],.6)
        self.assertAlmostEqual(rects[2]['width'],.2)
    def test_odd_pixels_and_internal_half_padding(self):
        left,right=tiles.leaves({'layoutDirection':'horizontal','tiles':[{'width':.5},{'width':.5}]})
        self.assertEqual(tiles.padded_frame(left,[0,40,1001,601],0),[0,40,501,601])
        self.assertEqual(tiles.padded_frame(right,[0,40,1001,601],0),[501,40,500,601])
        a=tiles.padded_frame(left,[0,40,1000,600],4);b=tiles.padded_frame(right,[0,40,1000,600],4)
        self.assertEqual(b[0]-(a[0]+a[2]),4)
    def test_save_standard_groups_conserves_foreign_keys_and_detects_edits(self):
        p=self.b.CONFIG/'kwinrc';p.write_text('# other\n[Other]\nkeep=yes\n')
        data=tiles.inspect(self.b,{'description':'monitor stable'},2)
        data['tree']={'layoutDirection':'horizontal','tiles':[{'width':.3},{'width':.7}]}
        tiles.save(self.b,data)
        text=p.read_text();self.assertIn('[Tiling][',text);self.assertIn('keep=yes',text)
        self.assertIn('"layoutDirection":"horizontal"',text)
        with self.assertRaises(ValueError):tiles.save(self.b,data)
    def test_invalid_geometry_and_ini_injection_rejected(self):
        with self.assertRaises(ValueError):tiles.leaves({'layoutDirection':'floating','tiles':[{'x':0,'y':0,'width':float('nan'),'height':1}]})
        data=tiles.inspect(self.b,{'description':'monitor'},1);data['output']='bad]\n[Other'
        with self.assertRaises(ValueError):tiles.save(self.b,data)
