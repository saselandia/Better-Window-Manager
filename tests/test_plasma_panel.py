"""PanelView adapter geometry; Qt executes the same JavaScript used by the QML host."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
LOGIC=ROOT/"config/quickshell/ii/modules/plasma/panel/PanelLogic.js"

def evaluate(expression):
    with tempfile.TemporaryDirectory() as folder:
        p=Path(folder)/"test.qml"
        p.write_text('import QtQuick\nimport "'+LOGIC.as_uri()+'" as Logic\nItem { Component.onCompleted: { console.log("RESULT",JSON.stringify('+expression+')); Qt.quit(); } }')
        out=subprocess.run(["qml6",str(p)],env={**os.environ,"QT_QPA_PLATFORM":"offscreen"},capture_output=True,text=True,timeout=10)
        lines=(out.stdout+out.stderr).splitlines()
        result=next((s.split("RESULT ",1)[1] for s in lines if "RESULT " in s),None)
        if result is None: raise AssertionError(out.stdout+out.stderr)
        return json.loads(result)

@unittest.skipUnless(shutil.which("qml6"),"Qt QML runner unavailable")
class PanelTest(unittest.TestCase):
    def test_four_edges_reserve_only_thickness(self):
        for edge in ["bottom","top","left","right"]:
            with self.subTest(edge=edge):
                g=evaluate('Logic.geometry(1200,800,{edge:'+json.dumps(edge)+',floating:true,thickness:44,length:1},true,false,true)')
                self.assertEqual(g["reserve"],44)
                self.assertEqual(g["gap"],8)
                self.assertEqual(g["vertical"],edge in ["left","right"])
                self.assertGreaterEqual(g["x"],0);self.assertGreaterEqual(g["y"],0)
                self.assertLessEqual(g["x"]+g["width"],1200)
                self.assertLessEqual(g["y"]+g["height"],800)
    def test_auto_hide_dodge_and_go_below_never_reserve(self):
        for mode in ["autoHide","dodge","windowsGoBelow"]:
            for touching in [True,False]:
                cfg={"edge":"top","visibility":mode}
                g=evaluate('Logic.geometry(1200,800,'+json.dumps(cfg)+',true,'+str(touching).lower()+',false)')
                self.assertEqual(g["reserve"],0)
                self.assertEqual(g["hidden"],mode=="autoHide" or mode=="dodge" and touching)
    def test_docking_floating_gap_and_reveal(self):
        expr='Logic.geometry(1200,800,{edge:"right",floating:true,visibility:"autoHide"},true,true,true)'
        g=evaluate(expr)
        self.assertEqual(g["gap"],0)
        self.assertFalse(g["hidden"])
    def test_alignment_and_length(self):
        for alignment in ["start","center","end"]:
            g=evaluate('Logic.geometry(1000,700,{edge:"bottom",length:0.5,floating:true,alignment:'+json.dumps(alignment)+'},true,false,true)')
            self.assertEqual(g["length"],492)
            self.assertEqual(g["start"],{"start":8,"center":254,"end":500}[alignment])
    def test_touching_ignores_other_workspaces_hidden_and_monitor(self):
        m={"id":2,"x":1000,"y":0,"activeWorkspace":{"id":1},"specialWorkspace":{"id":0}}
        rect={"x":0,"y":740,"width":1000,"height":60}
        c={"monitor":2,"workspace":{"id":1},"at":[1000,750],"size":[100,50]}
        for key,value in [("monitor",1),("hidden",True),("workspace",{"id":5})]:
            client={**c,key:value}
            self.assertFalse(evaluate('Logic.touching('+json.dumps(m)+','+json.dumps([client])+','+json.dumps(rect)+')'))
        self.assertTrue(evaluate('Logic.touching('+json.dumps(m)+','+json.dumps([c])+','+json.dumps(rect)+')'))
    def test_reorder_is_stable_and_has_no_duplicate(self):
        self.assertEqual(evaluate('Logic.reorder(["a","b","c"],"c","a")'),["c","a","b"])
        self.assertEqual(evaluate('Logic.reorder(["a","b","c"],"a","a")'),["a","b","c"])

class ReservedAreaTest(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0,str(ROOT/"config/hypr/scripts"))
        spec=importlib.util.spec_from_file_location("windows",ROOT/"config/hypr/scripts/bwm_windows.py")
        self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
    def test_compositor_reserved_replaces_manifest_on_each_edge(self):
        for edge in range(4):
            reserve=[0,0,0,0];reserve[edge]=60
            monitor={"x":0,"y":0,"width":1000,"height":800,"scale":1,"reserved":reserve}
            x,y,w,h=self.m.traditional_box([0,0],[1000,800],monitor,False,{"panel":{"edge":"bottom","size":44},"edgeMargin":0})
            if edge==0:self.assertEqual(x,60)
            if edge==1:self.assertEqual(y,60)
            if edge==2:self.assertEqual(x+w,940)
            if edge==3:self.assertEqual(y+h,740)
    def test_zero_reserved_does_not_restore_hidden_panel(self):
        monitor={"x":0,"y":0,"width":1000,"height":800,"scale":1,"reserved":[0,0,0,0]}
        _,y,_,h=self.m.traditional_box([0,0],[1000,800],monitor,False,{"panel":{"edge":"bottom","size":44},"edgeMargin":0})
        self.assertEqual(y+h,800)

if __name__=="__main__":unittest.main()
