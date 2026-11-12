"""Isolated native Plasma panel components: typography, sizing and pointer input."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest
import uuid

ROOT=Path(__file__).resolve().parents[1]
SHELL=ROOT/'config/quickshell/ii'
HARNESS=r'''//@ pragma UseQApplication
//@ pragma Env QT_QPA_PLATFORMTHEME=kde
//@ pragma Env QT_QUICK_CONTROLS_STYLE=org.kde.desktop
import QtQuick
import QtQuick.Layouts
import QtTest
import Quickshell
import qs.modules.common
import qs.modules.plasma.panel as Panel
import qs.modules.plasma.tray as Tray
ShellRoot {
    id:root
    property int toggles:0
    property int desktopToggles:0
    property int arrowToggles:0
    Component.onCompleted:Config.blockWrites=true
    FloatingWindow {
        id:host;title:"bwm-native-panel-test"
        implicitWidth:600;implicitHeight:140
        RowLayout {
            anchors.centerIn:parent
            Panel.KickoffButton {
                id:kickoff;Layout.preferredHeight:32;Layout.preferredWidth:32
                onToggleRequested:value=>{root.toggles++;expanded=value}
            }
            Panel.DigitalClock {
                id:clock
                vertical:Quickshell.env("NATIVE_VERTICAL")==="1"
                Layout.preferredHeight:vertical?implicitHeight:Number(Quickshell.env("NATIVE_HEIGHT"))
                Layout.maximumHeight:vertical?-1:Number(Quickshell.env("NATIVE_HEIGHT"))
                Layout.preferredWidth:vertical?44:implicitWidth
            }
            Panel.ShowDesktopButton { id:desktop;onToggleRequested:root.desktopToggles++ }
            Tray.SystemTray {
                id:tray;readOnly:true;items:[]
                applets:[({id:"demo",title:"Demo",icon:"dialog-information",active:true})]
                appearance:({scaleIconsToFit:Quickshell.env("NATIVE_AUTOSIZE")==="1"})
                Layout.preferredHeight:32;Layout.preferredWidth:implicitWidth
            }
            Tray.ExpanderArrow {
                id:arrow;Layout.preferredWidth:22;Layout.preferredHeight:32
                onToggleRequested:value=>{root.arrowToggles++;expanded=value}
            }
        }
        TestCase { id:driver;name:"NativePanel";when:false }
    }
    Timer {
        running:true;interval:700
        onTriggered:{
            const time=driver.findChild(clock,"plasma-clock-time");
            const date=driver.findChild(clock,"plasma-clock-date");
            driver.mouseClick(kickoff,16,16);driver.mouseClick(kickoff,16,16);
            driver.mouseClick(desktop,16,16);
            driver.mouseClick(arrow,11,16);driver.mouseClick(arrow,11,16);
            console.log("NATIVEPANEL "+JSON.stringify({state:clock.state,height:clock.height,width:clock.width,timePixels:time.font.pixelSize,timeHeight:time.height,datePixels:date.font.pixelSize,bold:time.font.bold,desktopWidth:desktop.width,desktopHeight:desktop.height,arrowWidth:arrow.width,trayIcon:tray.itemSize,trayCell:tray.cellLength,trayLanes:tray.lanes,toggles:root.toggles,closed:!kickoff.expanded,desktopToggles:root.desktopToggles,arrowToggles:root.arrowToggles,arrowClosed:!arrow.expanded}));
            Qt.quit();
        }
    }
    Timer {running:true;interval:5000;onTriggered:Qt.quit()}
}
'''

@unittest.skipUnless(os.environ.get('BWM_RUN_QML_TESTS')=='1' and shutil.which('qs'),
                     'optional native panel UI checks')
class NativePanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path=SHELL/('zz_prueba_native_'+uuid.uuid4().hex+'.qml')
        cls.path.write_text(HARNESS)
        # Every action is a local counter. Never call power, IPC, window or backend actions.
        for action in ['execDetached','Hyprland.dispatch','ipc call','DesktopState.toggle']:
            assert action not in HARNESS
        subprocess.run(['hyprctl','eval','hl.window_rule({name="tmp-native-panel-test",match={title="^bwm-native-panel-test$"},workspace="9 silent"})'],capture_output=True,check=True,timeout=5)
    @classmethod
    def tearDownClass(cls):
        cls.path.unlink(missing_ok=True)
        subprocess.run(['hyprctl','reload'],capture_output=True,check=True,timeout=5)
    def run_case(self,height,vertical=False,auto=False):
        result=subprocess.run(['qs','-p',str(self.path)],capture_output=True,text=True,timeout=10,
                              env={**os.environ,'NATIVE_HEIGHT':str(height),'NATIVE_VERTICAL':'1' if vertical else '0','NATIVE_AUTOSIZE':'1' if auto else '0'})
        out=result.stdout+result.stderr
        for error in ['ReferenceError:','TypeError:','failed to load','Binding loop']:
            self.assertNotIn(error,out)
        value=next((json.loads(l.split('NATIVEPANEL ',1)[1]) for l in out.splitlines() if 'NATIVEPANEL ' in l),None)
        self.assertIsNotNone(value,out)
        self.assertEqual(value['toggles'],2,out);self.assertTrue(value['closed'])
        self.assertEqual(value['desktopToggles'],1,out)
        self.assertEqual(value['arrowToggles'],2,out);self.assertTrue(value['arrowClosed'])
        self.assertEqual((value['desktopWidth'],value['desktopHeight']),(32,32))
        self.assertEqual(value['arrowWidth'],22)
        self.assertEqual(value['trayIcon'],32 if auto else 22)
        self.assertEqual(value['trayCell'],40 if auto else 30)
        self.assertEqual(value['trayLanes'],1)
        self.assertFalse(value['bold'])
        self.assertGreater(value['width'],0)
        return value
    def test_native_clock_fits_panel_instead_of_using_fixed_font(self):
        for height in (32,44):
            with self.subTest(height=height):
                v=self.run_case(height)
                self.assertEqual(v['state'],'horizontalPanel')
                self.assertAlmostEqual(v['timePixels'],height*.56,delta=1)
                self.assertAlmostEqual(v['datePixels'],v['timeHeight']*.8,delta=1)
    def test_one_line_clock_on_small_panel(self):
        self.assertEqual(self.run_case(20)['state'],'oneLineDate')
    def test_vertical_clock(self):
        self.assertEqual(self.run_case(44,True)['state'],'verticalPanel')

    def test_tray_native_auto_size_setting(self):
        self.run_case(32,auto=True)
