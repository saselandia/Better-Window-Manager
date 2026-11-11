"""Exact frame application uses the preview monitor and always checks window identity."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'config/hypr/skins/plasma/scripts'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=load('f10_tile_apply',SCRIPTS/'kwin-tiles.py')
kwin=load('f10_tile_window',SCRIPTS/'kwin-window.py')

class FrameApplicationTests(unittest.TestCase):
    def setUp(self):
        self.client={'address':'0xa','pid':10,'monitor':0,'workspace':{'id':10},'size':[700,600],'tags':['user-keep','bwm-rule*']}
        self.monitor={'id':1,'description':'stable display','x':0,'y':720,'width':2560,'height':1440,'scale':1,'reserved':[0,40,0,0],'activeWorkspace':{'id':2}}
        fresh={**self.client,'monitor':1,'workspace':{'id':2}}
        self.save=Mock();self.kw=SimpleNamespace(run_lua=Mock(),window_lua=kwin.window_lua,find_client=Mock(return_value=fresh),maximize=Mock(),
                window_borders=Mock(return_value={'left':4,'top':28,'right':4,'bottom':4}),content_from_frame=kwin.content_from_frame,
                has_tag=kwin.has_tag,mode_from_tags=kwin.mode_from_tags,load_script=Mock(return_value=SimpleNamespace(save_presnap=self.save)))
    def test_workspace_first_exact_frame_all_edges_and_no_user_tag_loss(self):
        self.assertTrue(m.apply_frame(self.kw,self.client,self.monitor,[1280,760,1280,1400],'right'))
        first,last=[c.args[0] for c in self.kw.run_lua.call_args_list]
        self.assertIn('workspace=2',first);self.assertNotIn('window.resize',first)
        self.assertIn('w.pid ~= 10',last)
        self.assertIn('x=1284,y=788',last);self.assertIn('x=1272,y=1368',last)
        self.assertNotIn('clear_tags',last);self.assertNotIn('-user-keep',last)
    def test_new_pid_after_transfer_prevents_geometry_change(self):
        self.kw.find_client.return_value={**self.client,'pid':11}
        self.assertFalse(m.apply_frame(self.kw,self.client,self.monitor,[0,760,1280,1400],'left'))
        self.assertEqual(self.kw.run_lua.call_count,1)
    def test_outdated_reserved_area_never_applies_another_preview(self):
        self.assertFalse(m.apply_frame(self.kw,self.client,self.monitor,[0,720,1280,1440],'left'))
        self.kw.run_lua.assert_not_called()
    def test_top_border_uses_f8_full_maximize(self):
        self.assertTrue(m.apply_frame(self.kw,self.client,self.monitor,[0,760,2560,1400],'maximize'))
        self.kw.maximize.assert_called_once();self.assertEqual(self.kw.maximize.call_args.args[1],'full')
