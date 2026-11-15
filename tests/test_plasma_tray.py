"""Plasma tray visibility rules and isolated UI checks (no radio changes or extra notification server).

BWM_RUN_QML_TESTS=1 python3 -m unittest tests.test_plasma_tray -v
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import uuid

ROOT=Path(__file__).resolve().parents[1]
SHELL=ROOT/'config/quickshell/ii'
LOGIC=SHELL/'modules/plasma/tray/TrayLogic.js'

@unittest.skipUnless(shutil.which('qml6'),'qml6 unavailable')
class VisibilityTests(unittest.TestCase):
    def evaluate(self,expression):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'check.qml'
            p.write_text('import QtQuick\nimport "'+LOGIC.as_uri()+'" as L\nItem { Component.onCompleted:{ console.log("TRAYRESULT "+JSON.stringify('+expression+'));Qt.quit(); } }')
            r=subprocess.run(['qml6',str(p)],env={**os.environ,'QT_QPA_PLATFORM':'offscreen'},capture_output=True,text=True,timeout=10)
            for line in (r.stdout+r.stderr).splitlines():
                if 'TRAYRESULT ' in line:return json.loads(line.split('TRAYRESULT ',1)[1])
            self.fail(r.stdout+r.stderr)
    def test_auto_follows_activity(self):
        self.assertEqual(self.evaluate('[L.visible({},"a",true),L.visible({},"a",false)]'),[True,False])
    def test_missing_or_unknown_modes_fall_back_to_auto(self):
        self.assertEqual(self.evaluate('[L.visible(null,"a",true),L.visible({a:"invalid"},"a",true)]'),[True,True])
    def test_explicit_modes_override_activity(self):
        self.assertEqual(self.evaluate('[L.visible({a:"shown"},"a",false),L.visible({a:"hidden"},"a",true)]'),[True,False])
    def test_modes_are_per_id_and_do_not_mutate_other_items(self):
        self.assertEqual(self.evaluate('L.update({a:"shown",b:"hidden"},"a","auto")'),{'b':'hidden'})
        self.assertEqual(self.evaluate('L.update({a:"shown"},"applet:audio","hidden")'),{'a':'shown','applet:audio':'hidden'})

HARNESS=r'''//@ pragma UseQApplication
//@ pragma Env QS_NO_RELOAD_POPUP=1
import QtQuick
import QtTest
import Quickshell
import Quickshell.Wayland
import qs.modules.common
import qs.modules.plasma.tray as TrayPort
ShellRoot {
    id:root
    property var toastScope:null
    property var compiled:[]
    property int actions:0
    property int copied:0
    property int removed:0
    QtObject {
        id:mock
        property bool available:true
        property bool enabled:true
        property bool connected:false
        property bool silent:false
        property var friendlyDeviceList:[device]
        property var entries:["1\tDemo clipboard entry"]
        readonly property var popupList:list
        function cancelTimeout(id){}
        function timeoutNotification(id){}
        property var list:[({notificationId:1,appName:"BWM test",appIcon:"notifications",summary:"Example notification",body:"Safe test content",image:"",actions:[{identifier:"test",text:"Test action"}]})]
        property real percentage:.5
        property real health:95
        property bool isPluggedIn:false
        property int chargeState:2
        property bool isCharging:false
        property real timeToFull:0
        property real timeToEmpty:3600
        function markAllRead(){}
        function timeoutAll(){}
        function discardNotification(id){root.removed++}
        function discardAllNotifications(){root.removed++}
        function attemptInvokeAction(id,action){root.actions++}
        function refresh(){}
        function copy(entry){root.copied++}
        function deleteEntry(entry){root.removed++}
    }
    QtObject {
        id:device
        property string name:"Test headset"
        property string icon:"audio-headphones"
        property string address:"00:00:00:00:00:01"
        property bool connected:false
        property bool paired:true
        property bool pairing:false
        property int state:0
        property bool batteryAvailable:true
        property real battery:.7
        function connect(){root.actions++}
        function disconnect(){root.actions++}
        function pair(){root.actions++}
    }
    QtObject { id:adapter;property bool enabled:true;property bool discovering:false }
    Component.onCompleted:Config.blockWrites=true
    PanelWindow {
        id:host
        anchors { top:true;left:true }
        margins.top:64;margins.left:16
        color:"transparent";exclusionMode:ExclusionMode.Ignore
        WlrLayershell.namespace:"bwm-f5-test"
        WlrLayershell.layer:WlrLayer.Overlay
        implicitWidth:500;implicitHeight:560
        Loader { id:loader;anchors.fill:parent }
        TestCase { id:driver;name:"BwmTray";when:false }
    }
    function findText(item,text) {
        if(item.text===text)return item;
        for(const child of item.children??[]) { const result=findText(child,text);if(result)return result; }
        return null;
    }
    Timer {
        interval:400;running:true
        onTriggered:{
            const name=Quickshell.env("F5_CASE");let props={readOnly:true};
            if(name==="Bluetooth")props={backend:mock,adapter:adapter};
            if(name==="Notifications"||name==="Clipboard")props={backend:mock};
            if(name==="Tray")props={readOnly:true,items:[{id:"demo",title:"Demo tray item",tooltipTitle:"Demo",tooltipDescription:"Safe fixture",icon:"applications-system",status:1}],applets:[{id:"notifications",title:"Notifications",icon:"notifications",active:true}],settings:{},appletProperties:{readOnly:true,backend:mock}};
            if(name==="Power")props={readOnly:true,battery:mock,monitors:[]};
            if(name==="Compile") {
                root.compiled=["panel/Panel.qml","panel/PanelContent.qml","tray/TrayController.qml"].map(path=>Qt.createComponent(Qt.resolvedUrl("modules/plasma/"+path)));
                for(const component of root.compiled)if(component.status===Component.Error)console.log("COMPILEERROR "+component.errorString());
            } else if(name==="Toast") {
                const component=Qt.createComponent(Qt.resolvedUrl("modules/plasma/applets/NotificationPopups.qml"));
                root.toastScope=component.createObject(root,{backend:mock});
            } else loader.setSource(Qt.resolvedUrl("modules/plasma/"+Quickshell.env("F5_URL")),props);
            if(name==="Tray")TrayPort.TrayState.open("notifications",host.screen.name);
            finish.start();
        }
    }
    Timer {
        id:finish;interval:1600
        onTriggered:{
            const name=Quickshell.env("F5_CASE");
            const result={name:name,loaded:name==="Compile"?root.compiled.every(c=>c.status===Component.Ready):name==="Toast"?!!root.toastScope:loader.status===Loader.Ready,actions:0};
            if(name==="Toast")result.toastHeight=root.toastScope?.renderItem.children.find(c=>c.modelData!==undefined)?.height??0;
            if(name==="Tray") {
                result.pageLoaded=!!loader.item?.popupWindow?.appletItem;
                result.grabReady=!!loader.item?.popupWindow?.grabReady;
                const cfg=root.findText(loader.item.popupWindow.renderItem,"Configure");
                if(cfg){driver.mouseClick(cfg,cfg.width/2,cfg.height/2);driver.wait(60);}
                result.popupInteractive=!!loader.item?.configuring;
                if(cfg&&loader.item.configuring){driver.mouseClick(cfg,cfg.width/2,cfg.height/2);driver.wait(60);}
                const opener=root.findText(loader.item,"Notifications");
                if(opener)driver.mouseClick(opener,opener.width/2,opener.height/2);
                driver.wait(80);
                result.secondClickCloses=!!opener&&!TrayPort.TrayState.expanded;
                if(opener)driver.mouseClick(opener,opener.width/2,opener.height/2);
                driver.wait(80);
                driver.keyClick(Qt.Key_Escape);driver.wait(80);
                result.escapeCloses=!TrayPort.TrayState.expanded;
            }
            if(loader.item) {
                if(name==="Bluetooth") { const b=root.findText(loader.item,"Connect");if(b){const pos=b.mapToItem(loader.item,b.width/2,b.height/2);driver.mouseClick(loader.item,pos.x,pos.y);driver.wait(80);}result.control=!!b;result.actions=root.actions;result.discovery=adapter.discovering; }
                if(name==="Notifications") { const b=root.findText(loader.item,"Test action");if(b){const pos=b.mapToItem(loader.item,b.width/2,b.height/2);driver.mouseClick(loader.item,pos.x,pos.y);driver.wait(80);}result.control=!!b;result.actions=root.actions; }
                if(name==="Clipboard") { result.entries=loader.item.backend.entries.length; }
                if(name==="Calendar") {result.calendar=!!loader.item.fullRepresentationItem?.monthView;}
            }
            console.log("F5RESULT "+JSON.stringify(result));
            const output=Quickshell.env("F5_CAPTURE");
            if(output&&(loader.item||root.toastScope)){const imageItem=name==="Toast"?root.toastScope.renderItem:name==="Tray"?loader.item.popupWindow.renderItem:loader.item;imageItem.grabToImage(image=>{image.saveToFile(output);Qt.quit()})}else Qt.quit();
        }
    }
    Timer {interval:7000;running:true;onTriggered:Qt.quit()}
}
'''

@unittest.skipUnless(os.environ.get('BWM_RUN_QML_TESTS')=='1','optional isolated Wayland UI tests')
class AppletUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path=SHELL/('zz_prueba_f5_'+uuid.uuid4().hex+'.qml')
        cls.path.write_text(HARNESS)
    @classmethod
    def tearDownClass(cls):
        cls.path.unlink(missing_ok=True)
    def run_case(self,name,url):
        r=subprocess.run(['qs','-p',str(self.path)],env={**os.environ,'F5_CASE':name,'F5_URL':url,'LC_ALL':'C.UTF-8'},capture_output=True,text=True,timeout=12)
        output=r.stdout+r.stderr
        self.assertNotIn('failed to load',output.lower())
        self.assertNotIn('TypeError:',output)
        self.assertNotIn('ReferenceError:',output)
        self.assertNotIn('is not a type',output)
        result=next((json.loads(l.split('F5RESULT ',1)[1]) for l in output.splitlines() if 'F5RESULT ' in l),None)
        self.assertIsNotNone(result,output)
        self.assertTrue(result['loaded'],output)
        return result
    def test_tray_status_notifier_adapter(self):
        result=self.run_case('Tray','tray/SystemTray.qml')
        self.assertTrue(result['pageLoaded'])
        self.assertTrue(result['grabReady'])
        self.assertTrue(result['popupInteractive'])
        self.assertTrue(result['secondClickCloses'])
        self.assertTrue(result['escapeCloses'])
    def test_toast_without_extra_notification_server(self):self.assertGreater(self.run_case("Toast","applets/NotificationPopups.qml")["toastHeight"],0)
    def test_panel_and_ipc_controller_compile(self):self.run_case("Compile","panel/Panel.qml")
    def test_audio(self):self.run_case('Audio','applets/audio/AudioApplet.qml')
    def test_network_read_only(self):self.run_case('Network','applets/network/NetworkApplet.qml')
    def test_media(self):self.run_case('Media','applets/media/MediaApplet.qml')
    def test_calendar(self):self.assertTrue(self.run_case('Calendar','applets/calendar/CalendarApplet.qml')['calendar'])
    def test_bluetooth_uses_mock_and_does_not_discover_on_open(self):
        result=self.run_case('Bluetooth','applets/BluetoothApplet.qml')
        self.assertTrue(result['control']);self.assertEqual(result['actions'],1);self.assertFalse(result['discovery'])
    def test_notification_action_uses_existing_backend(self):
        result=self.run_case('Notifications','applets/NotificationsApplet.qml')
        self.assertTrue(result['control']);self.assertEqual(result['actions'],1)
    def test_clipboard(self):self.assertEqual(self.run_case('Clipboard','applets/ClipboardApplet.qml')['entries'],1)
    def test_power_without_daemon(self):self.run_case('Power','applets/PowerApplet.qml')


class ToolTipAreaTests(unittest.TestCase):
    def test_no_plasma_core_tooltip_area_in_panel_or_tray(self):
        for folder in ('panel', 'tray'):
            for qml in sorted((ROOT / 'config/quickshell/ii/modules/plasma' / folder).glob('*.qml')):
                self.assertNotIn('PlasmaCore.ToolTipArea', qml.read_text(), str(qml))

    @unittest.skipUnless(os.environ.get('BWM_RUN_QML_TESTS') == '1' and shutil.which('qs'),
                         'optional isolated Wayland UI tests')
    def test_tooltips_never_block_first_click_or_spawn_tooltip_dialog(self):
        harness = r'''//@ pragma UseQApplication
import QtQuick
import QtTest
import Quickshell
import qs.modules.plasma.tray as TrayPort
import qs.modules.plasma.panel as PanelPort
ShellRoot {
    id: root
    property int opened: 0
    property int arrowToggles: 0
    property int desktopToggles: 0
    QtObject {
        id: trayMock
        property bool expanded: false
        property string activeApplet: ""
        property int itemSize: 22
        property var hiddenLayout: QtObject { property int currentIndex: -1 }
        function openApplet(id) { root.opened++; trayMock.expanded = true; trayMock.activeApplet = id; }
    }
    FloatingWindow {
        id: win
        title: "bwm-tooltip-test"
        implicitWidth: 220; implicitHeight: 80
        Row {
            anchors.centerIn: parent; spacing: 12
            TrayPort.AppletItem {
                id: appletBtn; width: 32; height: 32; tray: trayMock
                applet: ({id: "volume", title: "Audio Volume", icon: "audio-volume-high", summary: "Volume at 50%"})
            }
            TrayPort.ExpanderArrow {
                id: arrowBtn; width: 32; height: 32
                onToggleRequested: expanded => { root.arrowToggles++; arrowBtn.expanded = expanded; }
            }
            PanelPort.ShowDesktopButton {
                id: desktopBtn; width: 32; height: 32
                onToggleRequested: root.desktopToggles++
            }
        }
        TestCase { id: driver; name: "ToolTipFirstClick"; when: false }
    }
    Timer { running: true; interval: 4000; onTriggered: Qt.quit() }
    Timer {
        running: true; interval: 450
        onTriggered: {
            appletBtn.showToolTip();
            driver.wait(40);
            const shownBeforeClick = appletBtn.toolTipVisible;
            driver.mouseClick(appletBtn, 16, 16);
            driver.wait(40);
            const hiddenAfterAppletClick = !appletBtn.toolTipVisible;
            const appletOpenedOnFirstClick = root.opened;

            arrowBtn.showToolTip();
            driver.wait(40);
            const arrowShown = arrowBtn.toolTipVisible;
            driver.mouseClick(arrowBtn, 16, 16);
            driver.wait(40);
            const arrowToggledOnFirstClick = root.arrowToggles;
            const arrowHiddenAfterClick = !arrowBtn.toolTipVisible;

            const desktopTip = driver.findChild(desktopBtn, "toolTip");
            desktopBtn.children; // force binding eval
            let tipChild = null;
            for (let i = 0; i < desktopBtn.children.length; i++) {
                const c = desktopBtn.children[i];
                for (let j = 0; c && c.children && j < c.children.length; j++) {
                    if (typeof c.children[j].showToolTip === "function") tipChild = c.children[j];
                }
            }
            let desktopShown = false, desktopHidden = false;
            if (tipChild) {
                tipChild.showToolTip();
                driver.wait(40);
                desktopShown = tipChild.toolTipVisible;
            }
            driver.mouseClick(desktopBtn, 16, 16);
            driver.wait(40);
            desktopHidden = tipChild ? !tipChild.toolTipVisible : false;

            console.log("TOOLTIPRESULT " + JSON.stringify({
                shownBeforeClick, hiddenAfterAppletClick, appletOpenedOnFirstClick,
                arrowShown, arrowToggledOnFirstClick, arrowHiddenAfterClick,
                desktopShown, desktopHidden, desktopTogglesOnFirstClick: root.desktopToggles
            }));
            Qt.quit();
        }
    }
}
'''
        rule = 'hl.window_rule({name="tmp-bwm-tooltip-test",match={title="^bwm-tooltip-test$"},workspace="9 silent"})'
        if shutil.which('hyprctl'):
            subprocess.run(['hyprctl', 'eval', rule], capture_output=True, text=True, timeout=5)
        tmp = tempfile.NamedTemporaryFile('w', dir=ROOT / 'config/quickshell/ii', prefix='zz_prueba_tip_', suffix='.qml', delete=False)
        try:
            tmp.write(harness)
            tmp.close()
            r = subprocess.run(['qs', '-p', tmp.name], env={**os.environ, 'LC_ALL': 'C.UTF-8'}, capture_output=True, text=True, timeout=12)
        finally:
            Path(tmp.name).unlink(missing_ok=True)
            if shutil.which('hyprctl'):
                subprocess.run(['hyprctl', 'reload'], capture_output=True, text=True, timeout=5)
        log = r.stdout + r.stderr
        self.assertNotIn('ToolTipDialog', log)
        self.assertEqual(r.returncode, 0, log)
        line = next((l for l in log.splitlines() if 'TOOLTIPRESULT ' in l), '')
        self.assertTrue(line, log)
        data = json.loads(line.split('TOOLTIPRESULT ', 1)[1])
        self.assertTrue(data['shownBeforeClick'], data)
        self.assertTrue(data['hiddenAfterAppletClick'], data)
        self.assertEqual(data['appletOpenedOnFirstClick'], 1, data)
        self.assertTrue(data['arrowShown'], data)
        self.assertEqual(data['arrowToggledOnFirstClick'], 1, data)
        self.assertTrue(data['arrowHiddenAfterClick'], data)
        self.assertTrue(data['desktopShown'], data)
        self.assertTrue(data['desktopHidden'], data)
        self.assertEqual(data['desktopTogglesOnFirstClick'], 1, data)

