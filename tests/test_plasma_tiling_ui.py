"""Optional F10 IPC/QML tests: no visible layer, no save and no window actions.

BWM_RUN_QML_TESTS=1 python3 -m unittest discover -s tests -p test_plasma_tiling_ui.py
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest
import uuid

ROOT=Path(__file__).resolve().parents[1]
SHELL=ROOT/'config/quickshell/ii'
HARNESS='''//@ pragma UseQApplication
//@ pragma Env QS_NO_RELOAD_POPUP=1
import QtQuick
import Quickshell
import qs.modules.common
import qs.modules.plasma.tiling as T
ShellRoot {
    Component.onCompleted:Config.blockWrites=true
    T.Outline {}
    T.TileEditor {Component.onCompleted:load("","")}
    Timer {interval:20000;running:true;onTriggered:Qt.quit()}
}
'''

@unittest.skipUnless(os.environ.get('BWM_RUN_QML_TESTS')=='1' and shutil.which('qs') and os.environ.get('WAYLAND_DISPLAY'),'QML tests opt-in (Wayland)')
class PlasmaTilingUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.harness=SHELL/('zz_prueba_f10_'+uuid.uuid4().hex+'.qml')
        cls.harness.write_text(HARNESS)
        cls.folder=tempfile.TemporaryDirectory(prefix='bwm-f10-ui-')
        cls.log=Path(cls.folder.name)/'log';cls.output=cls.log.open('w')
        cls.process=subprocess.Popen(['qs','-p',str(cls.harness)],stdout=cls.output,stderr=subprocess.STDOUT)
        try:
            for _ in range(50):
                r=cls.call('plasmaTiles','inspect',check=False)
                if r.returncode==0:
                    state=json.loads(r.stdout)
                    if state.get('data'):break
                if cls.process.poll() is not None:raise AssertionError(cls.log.read_text())
                time.sleep(.1)
            else:raise AssertionError('No cargó el inspector de mosaico: '+cls.log.read_text())
        except BaseException:
            cls.tearDownClass();raise
    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()
        try:cls.process.wait(timeout=4)
        except subprocess.TimeoutExpired:cls.process.kill();cls.process.wait()
        cls.output.close();cls.harness.unlink(missing_ok=True);cls.folder.cleanup()
    @classmethod
    def call(cls,target,method,*args,check=True):
        r=subprocess.run(['qs','-p',str(cls.harness),'ipc','call',target,method,*args],capture_output=True,text=True,timeout=4)
        if check and r.returncode:raise AssertionError(r.stdout+r.stderr)
        return r
    def test_real_layout_reader_and_delegates_load_without_opening_editor(self):
        state=json.loads(self.call('plasmaTiles','inspect').stdout)
        self.assertFalse(state['opened']);self.assertFalse(state['error'])
        self.assertGreaterEqual(len(state['data']['leaves']),1)
        self.assertNotIn('Failed to load configuration',self.log.read_text())
    def test_outline_ipc_discards_late_display_and_hide(self):
        # Kept outside all monitors: PanelWindow remains invisible throughout this test.
        g={'sequence':3,'x':-100000,'y':-100000,'width':100,'height':100,'area':[-100000,-100000,100,100]}
        self.call('plasmaOutline','hide','4')
        self.call('plasmaOutline','display',json.dumps(g))
        state=json.loads(self.call('plasmaOutline','inspect').stdout)
        self.assertFalse(state['active']);self.assertEqual(state['sequence'],4)
        g['sequence']=5;self.call('plasmaOutline','display',json.dumps(g));self.call('plasmaOutline','hide','4')
        state=json.loads(self.call('plasmaOutline','inspect').stdout)
        self.assertTrue(state['active']);self.assertEqual(state['sequence'],5)
        self.call('plasmaOutline','hide','6')
