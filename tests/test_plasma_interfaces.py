"""F12: original KDE configuration and theme hosting, with no real lock/auth/window actions."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import sys
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT/'config/quickshell/ii'
SCRIPT = ROOT/'config/hypr/skins/plasma/scripts/interface-theme.py'
spec = importlib.util.spec_from_file_location('plasma_interfaces', SCRIPT)
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


class InterfaceConfigTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='bwm-f12-')
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)
        self.env = {f'XDG_{kind}_HOME':str(self.path/kind.lower()) for kind in ('CONFIG','DATA','CACHE')}
        self.env['XDG_CONFIG_DIRS'] = str(self.path/'system')
        self.env['XDG_DATA_DIRS'] = str(self.path/'system-data')
        self.patch = mock.patch.dict(os.environ,self.env)
        self.patch.start();self.addCleanup(self.patch.stop)
        (self.path/'config/kdedefaults').mkdir(parents=True)

    def test_kde_defaults_then_explicit_user_selection(self):
        (self.path/'config/kdedefaults/kwinrc').write_text('[TabBox]\nLayoutName=from-global-theme\n')
        self.assertEqual(runtime.snapshot()['layout'],'from-global-theme')
        (self.path/'config/kwinrc').write_text('[TabBox]\nLayoutName=thumbnail_grid\n')
        self.assertEqual(runtime.snapshot()['layout'],'thumbnail_grid')

    def test_original_lookandfeel_entry_points(self):
        theme=self.path/'data/plasma/look-and-feel/test.theme/contents/lockscreen'
        theme.mkdir(parents=True);(theme/'LockScreenUi.qml').write_text('import QtQuick\nItem {}')
        (self.path/'config/kdeglobals').write_text('[KDE]\nLookAndFeelPackage=test.theme\n')
        self.assertEqual(runtime.snapshot()['lockSource'],str(theme/'LockScreenUi.qml'))
        self.assertEqual(runtime.snapshot()['osdSource'],'')

    def test_installed_switcher_is_adapted_without_modifying_package(self):
        package=self.path/'data/kwin/tabbox/test.grid'
        ui=package/'contents/ui';ui.mkdir(parents=True)
        (package/'metadata.json').write_text('{}')
        source='pragma ComponentBehavior: Bound\nimport QtQuick\nimport org.kde.kwin 3.0 as KWin\nKWin.TabBoxSwitcher {}'
        (ui/'main.qml').write_text(source)
        (package/'contents/assets').mkdir();(package/'contents/assets/example.svg').write_text('<svg/>')
        (self.path/'config/kwinrc').write_text('[TabBox]\nLayoutName=test.grid\n')
        result=Path(runtime.snapshot()['switcherSource'])
        self.assertNotEqual(result,ui/'main.qml')
        self.assertNotIn('import org.kde.kwin',result.read_text())
        self.assertLess(result.read_text().index('pragma '),result.read_text().index('import '))
        self.assertTrue((result.parent.parent/'assets/example.svg').is_file())
        self.assertEqual((ui/'main.qml').read_text(),source)
        self.assertEqual(runtime.snapshot()['switcherSource'],str(result))

    def test_package_id_cannot_escape_data_directories(self):
        self.assertIsNone(runtime.package('kwin/tabbox','../outside'))
        self.assertIsNone(runtime.package('plasma/look-and-feel','/absolute'))


class PolkitOwnershipTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,str(ROOT/'config/hypr/scripts'))
        import bwm_polkit
        cls.agent=bwm_polkit

    def test_a_delayed_skin_hook_does_not_replace_the_current_agent(self):
        with tempfile.TemporaryDirectory(prefix='bwm-f12-session-') as directory, \
             mock.patch.dict(os.environ,{'HYPRLAND_INSTANCE_SIGNATURE':'current'}):
            process=Path(directory)
            (process/'environ').write_bytes(b'HYPRLAND_INSTANCE_SIGNATURE=another\0')
            self.assertFalse(self.agent.session_matches(process))
            (process/'environ').write_bytes(b'HYPRLAND_INSTANCE_SIGNATURE=current\0')
            self.assertTrue(self.agent.session_matches(process))
        with mock.patch.object(self.agent,'active_skin',return_value='retro'), \
             mock.patch.object(self.agent.os,'kill') as kill, \
             mock.patch.object(self.agent.bwm_session,'spawn') as spawn:
            self.assertFalse(self.agent.configure('plasma'))
        kill.assert_not_called();spawn.assert_not_called()

    def test_registration_retry_is_serial_and_unmasks_signals(self):
        with tempfile.TemporaryDirectory(prefix='bwm-f12-polkit-') as directory, \
             mock.patch.dict(os.environ,{'XDG_RUNTIME_DIR':directory}), \
             mock.patch.object(self.agent,'active_skin',return_value='plasma'), \
             mock.patch.object(self.agent,'executable',return_value='/mock/agent'), \
             mock.patch.object(self.agent.signal,'pthread_sigmask') as unmask, \
             mock.patch.object(self.agent.time,'sleep'), \
             mock.patch.object(self.agent.subprocess,'run',side_effect=[mock.Mock(returncode=1),mock.Mock(returncode=0)]) as run:
            self.assertTrue(self.agent.run_agent('plasma'))
            self.assertEqual(run.call_count,2)
            self.assertEqual(run.call_args.args[0],['/mock/agent'])
            unmask.assert_called_once()


@unittest.skipUnless(os.environ.get('BWM_RUN_QML_TESTS')=='1','optional isolated QML checks')
class InterfaceUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(['hyprctl','eval','hl.window_rule({name="tmp-f12-tests",match={title="^BWM F12 Test$"},workspace="9 silent",no_initial_focus=true})'],check=True,capture_output=True)

    @classmethod
    def tearDownClass(cls):
        subprocess.run(['hyprctl','reload'],capture_output=True)

    def run_qml(self,text):
        # A separate qs -p, never the live shell. Only mock callbacks may authenticate/focus.
        for forbidden in ('WlSessionLock','PamContext','Hyprland.dispatch(','Quickshell.execDetached(','bwm-power'):
            self.assertNotIn(forbidden,text)
        with tempfile.NamedTemporaryFile(dir=SHELL,prefix='zz_f12_',suffix='.qml',mode='w',delete=False) as f:
            f.write(text);probe=Path(f.name)
        self.addCleanup(probe.unlink,missing_ok=True)
        env=os.environ|{'QML_IMPORT_PATH':str(Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))/'bwm/qml')}
        result=subprocess.run(['qs','-p',str(probe)],env=env,capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        return result.stdout+result.stderr

    def test_native_osd_lock_controls_and_theme_quit_isolation(self):
        with tempfile.TemporaryDirectory(prefix='bwm-f12-theme-') as temp:
            theme=Path(temp)/'main.qml'
            theme.write_text('import QtQuick\nItem {Component.onCompleted:{authenticator.startAuthenticating();Qt.quit();}}')
            text='''//@ pragma UseQApplication
import QtQuick
import Quickshell
import org.bwm.kcm
import qs.modules.common
import "modules/plasma/lock" as Lock
import "modules/plasma/osd" as Osd
import "modules/plasma/switcher" as Switcher
ShellRoot {
 Component.onCompleted:Config.blockWrites=true
 property int requests:0
 property bool intercepted:false
 QtObject {
  id:mockContext
  property string currentText:""
  property bool unlockInProgress:false
  property bool showFailure:false
  property bool fingerprintsConfigured:true
  signal failed()
  function tryUnlock(inhibit){requests++;}
  function clearText(){currentText="";}
 }
 Lock.Authenticator {id:auth;busy:mockContext.unlockInProgress;onAuthenticateRequested:mockContext.tryUnlock(false);onResponseSubmitted:text=>mockContext.currentText=text}
 QtObject {
  id:controller
  property bool isOpen:false
  property var focusedScreen:Quickshell.screens[0]
  property var windowList:[]
  property int selectedIndex:0
  function selectWindow(i){}
  function closeWindow(a){}
  function cancel(){}
  function selectAndClose(){}
  function findToplevel(a,b,c){return null;}
 }
 FloatingWindow {title:"BWM F12 Test";implicitWidth:1000;implicitHeight:700;Lock.LockSurface{anchors.fill:parent;context:mockContext}}
 Switcher.Switcher {controller:controller}
 Osd.Osd {id:osd}
 ThemeHost {id:host;source:THEME;contextProperties:({authenticator:auth});onQuitRequested:intercepted=true}
 Timer {interval:1500;running:true;onTriggered:{
  if(!host.ready||!intercepted||requests!==1)throw Error("theme authentication/quit contract failed");
  osd.osdValue=75;osd.osdMaxValue=100;osd.icon="audio-volume-high";osd.showingProgress=true;
  console.log("F12_UI_OK");Qt.quit();
 }}
}
'''.replace('THEME',json.dumps(theme.as_uri()))
            output=self.run_qml(text)
        self.assertIn('F12_UI_OK',output)
        active=output.split('F12_UI_OK')[0]
        self.assertNotRegex(active,r'ReferenceError|TypeError|is not a type|failed to load')

    def test_alt_tab_accumulates_and_only_selects_on_release(self):
        original=(SHELL/'modules/ii/altTab/AltTab.qml').read_text()
        controller=original.split('    IpcHandler {',1)[0]+'}\n'
        controller=controller.replace('Hyprland.dispatch(','console.log(').replace('Quickshell.execDetached(','console.log(')
        controller=controller.replace('command: ["/home/sasel/.config/hypr/scripts/alt-release-monitor.py"]','command: ["sleep", "3"]')
        with tempfile.TemporaryDirectory(prefix='bwm-f12-mru-') as temp:
            clients=[dict(address=f'0xf12{i}',title=f'BWM F12 fake {i}',**{'class':'f12'},workspace={'id':9},focusHistoryID=i,mapped=True) for i in range(4)]
            snapshot=Path(temp)/'snapshot.py'
            snapshot.write_text('import time\ntime.sleep(0.2)\nprint('+repr(json.dumps([clients,[{'activeWorkspace':{'id':9}}]]))+')\n')
            line=next(l for l in controller.splitlines() if 'command: ["sh", "-c", "printf' in l)
            controller=controller.replace(line,'        command: ["python3", '+json.dumps(str(snapshot))+']')
            controller=controller.replace('    property string origAddress: ""','    property string origAddress: ""\n    property string recordedAddress: ""\n    property int recordedCount: 0')
            controller=controller.replace('root.focusTarget(target);','root.recordedAddress=target.address;root.recordedCount++;')
            for forbidden in ('Hyprland.dispatch(', 'Quickshell.execDetached(', 'alt-release-monitor.py', 'hyprctl -j clients', 'PamContext', 'WlSessionLock'):
                self.assertNotIn(forbidden,controller)
            self.assertEqual(controller.count('Process {'),2)  # Only the fake snapshot and sleep watcher.
            probe=SHELL/'zz_f12_controller.qml';probe.write_text(controller)
            self.addCleanup(probe.unlink,missing_ok=True)
            output=self.run_qml('''import QtQuick
import Quickshell
ShellRoot {
 property bool failed:false
 Loader {id:loader;source:"zz_f12_controller.qml";onLoaded:item.next()}
 Timer {interval:30;running:true;onTriggered:{loader.item.next();loader.item.next();loader.item.selectAndClose();}}
 Timer {interval:550;running:true;onTriggered:{if(loader.item.recordedCount!==1||loader.item.recordedAddress!=="0xf123")failed=true;loader.item.next();}}
 Timer {interval:950;running:true;onTriggered:{if(loader.item.recordedCount!==1||!loader.item.isOpen)failed=true;loader.item.selectAndClose();}}
 Timer {interval:1200;running:true;onTriggered:{if(failed||loader.item.recordedCount!==2||loader.item.recordedAddress!=="0xf121")console.log("F12_MRU_FAILED");else console.log("F12_MRU_OK");Qt.quit();}}
}''')
        self.assertIn('F12_MRU_OK',output)
        self.assertNotIn('F12_MRU_FAILED',output)

if __name__=='__main__':unittest.main()
