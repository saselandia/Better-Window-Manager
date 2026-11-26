# SPDX-License-Identifier: GPL-2.0-or-later
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch,Mock

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"config/hypr/skins/plasma/scripts/session-ui.py"
class SessionTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="bwm-t4-unit-");self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.env=patch.dict(os.environ,{"XDG_CONFIG_HOME":str(self.root/"config"),"XDG_STATE_HOME":str(self.root/"state"),"XDG_RUNTIME_DIR":str(self.root/"runtime"),"XDG_CONFIG_DIRS":str(self.root/"defaults")})
        self.env.start();self.addCleanup(self.env.stop)
        spec=importlib.util.spec_from_file_location("t4_under_test",SCRIPT);self.ui=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.ui)
        self.ui.CONFIG.mkdir();self.ui.LEGACY.mkdir();self.ui.RUNTIME.mkdir()
        (self.ui.CONFIG/"illogical-impulse").mkdir()
        (self.ui.CONFIG/"illogical-impulse/config.json").write_text('{"appearance":{"bwmTheme":"plasma"}}')
    def generation(self,name):
        path=self.ui.STATE/"bwm/plasma/session-profiles"/name;path.mkdir(parents=True)
        files={}
        for filename in ("appletsrc","plasmashellrc","assignments.json","desktop-assignments.json"):
            data=(name+filename).encode();(path/filename).write_bytes(data);files[filename]=hashlib.sha256(data).hexdigest()
        (path/"session.json").write_text(json.dumps({"version":1,"directory":str(path),"files":files}))
        return path
    def test_none_in_ksplashrc_is_respected(self):
        path=self.ui.CONFIG/"ksplashrc"
        path.write_text('[KSplash]\nEngine=None\nTheme=org.kde.breeze.desktop\n')
        self.assertIsNone(self.ui.splash_settings())
        path.write_text('[KSplash]\nEngine=KSplashQML\nTheme=Sweet\n')
        self.assertEqual(self.ui.splash_settings(),"Sweet")
    def test_splash_never_completes_foreign_owner(self):
        with patch.object(self.ui,"bus",return_value="u 456") as bus:
            self.ui.finish_splash(123);self.assertEqual(bus.call_count,1)
        with patch.object(self.ui,"bus",side_effect=["u 123",None,None,None,None]) as bus:
            self.ui.finish_splash(123);self.assertEqual(bus.call_count,5)
            self.assertEqual([call.args[-1] for call in bus.call_args_list[1:]], ["startPlasma","kcminit","ksmserver","desktop"])
    def test_generation_inventory_and_hashes_are_checked(self):
        root=self.generation("a");self.assertEqual(self.ui.validate_generation(str(root)),root)
        (root/"appletsrc").write_text("changed")
        with self.assertRaises(ValueError):self.ui.validate_generation(str(root))
        root=self.generation("b");data=json.loads((root/"session.json").read_text());data["files"]={}
        (root/"session.json").write_text(json.dumps(data))
        with self.assertRaises(ValueError):self.ui.validate_generation(str(root))
    def test_splash_start_does_not_adopt_a_racing_foreign_owner(self):
        with patch.dict(os.environ,HYPRLAND_INSTANCE_SIGNATURE="t4-foreign"),patch.object(self.ui.host,"current_skin",return_value="plasma"),patch.object(self.ui,"bus",side_effect=[None]+["u 456"]*40),patch.object(self.ui.bwm_session,"spawn",return_value=True),patch.object(Path,"read_bytes",return_value=b"BWM_KSPLASH_TOKEN=foreign\0"),patch.object(self.ui.time,"sleep"),patch.object(self.ui,"finish_splash") as finish:
            self.assertEqual(self.ui.splash_start(),1);finish.assert_not_called()
    def test_splash_start_finishes_the_process_it_launched(self):
        launched=[]
        def spawn(argv,**kwargs):launched.extend(argv);return True
        def environment(path):return (launched[1]+"\0").encode()
        with patch.dict(os.environ,HYPRLAND_INSTANCE_SIGNATURE="t4-own"),patch.object(self.ui.host,"current_skin",return_value="plasma"),patch.object(self.ui.host,"ready_pid",return_value=123),patch.object(self.ui,"bus",side_effect=[None,"u 123"]),patch.object(self.ui.bwm_session,"spawn",side_effect=spawn),patch.object(Path,"read_bytes",environment),patch.object(self.ui,"finish_splash") as finish:
            self.assertEqual(self.ui.splash_start(),0);finish.assert_called_once_with(123)
    def test_new_generation_is_selected_after_old_owner_exits(self):
        candidate=self.generation("candidate");previous=self.generation("previous")
        status=json.dumps({"registered":True,"root":str(candidate),"desktops":1,"panels":[{"status":"visible"}]})
        with patch.object(self.ui.host,"is_host_pid",return_value=False),patch.object(self.ui.host,"start_host",return_value=0),patch.object(self.ui.host,"ready_pid",return_value=123),patch.object(self.ui.host,"host_ctl",return_value=status):
            self.assertEqual(self.ui.replace_layout(1,str(candidate),str(previous)),0)
        self.assertEqual(json.loads((self.ui.LEGACY/"active-session.json").read_text())["directory"],str(candidate))
        self.assertEqual((previous/"appletsrc").read_bytes(),b"previousappletsrc")
    def test_failed_start_rolls_back_to_previous_generation(self):
        candidate=self.generation("candidate");previous=self.generation("previous")
        with patch.object(self.ui.host,"is_host_pid",return_value=False),patch.object(self.ui.host,"start_host",side_effect=[1,0]),patch.object(self.ui.host,"ready_pid",return_value=123),patch.object(self.ui.host,"stop_host") as stop:
            self.assertEqual(self.ui.replace_layout(1,str(candidate),str(previous)),1);stop.assert_called_once()
        self.assertEqual(json.loads((self.ui.LEGACY/"active-session.json").read_text())["directory"],str(previous))
        self.assertTrue(json.loads((self.ui.LEGACY/"last-layout.json").read_text())["restored"])
    def test_another_skin_cancels_activation(self):
        candidate=self.generation("candidate");previous=self.generation("previous")
        with patch.object(self.ui.host,"is_host_pid",return_value=False),patch.object(self.ui.host,"current_skin",return_value="retro"),patch.object(self.ui.host,"start_host") as start:
            self.assertEqual(self.ui.replace_layout(1,str(candidate),str(previous)),1);start.assert_not_called()
        self.assertFalse((self.ui.LEGACY/"active-session.json").exists())
    def test_host_pid_must_belong_to_this_runtime(self):
        pid=os.getpid()
        def read(path):
            if path.name=="cmdline":return b"/some/bwm-plasma-host\0--session\0"
            if path.name=="environ":return b"XDG_RUNTIME_DIR=/another/session\0"
            return b""
        with patch.object(Path,"read_bytes",read):self.assertFalse(self.ui.host.is_host_pid(pid))
        def own(path):
            if path.name=="environ":return b"XDG_RUNTIME_DIR="+str(self.ui.RUNTIME).encode()+b"\0"
            return read(path)
        with patch.object(Path,"read_bytes",own):self.assertTrue(self.ui.host.is_host_pid(pid))

if __name__=="__main__":unittest.main()
