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
    property string repliedText:""
    property string editedText:""
    QtObject {
        id:mock
        property bool available:true
        property bool enabled:true
        property bool connected:false
        property bool silent:false
        property var friendlyDeviceList:[device]
        property var entries:["1\tDemo clipboard entry","2\t[[ binary data 1 KiB png 40x20 ]]"]
        property string cliphistBinary:Quickshell.env("F5_FAKE_CLIPHIST")||"cliphist"
        function entryIsImage(entry){return /^\d+\t\[\[.*binary data.*\d+x\d+.*\]\]$/.test(entry)}
        readonly property var popupList:list
        function cancelTimeout(id){}
        function timeoutNotification(id){}
        property var list:[({notificationId:1,appName:"BWM test",appIcon:"notifications",summary:"Example notification",body:"Safe test content",image:"",actions:[{identifier:"test",text:"Test action"}],hasInlineReply:Quickshell.env("F5_CASE")==="Reply",inlineReplyPlaceholder:"Reply to BWM"})]
        function sendInlineReply(id,text){root.repliedText=text;return true}
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
        function setText(text){root.editedText=text}
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
            if(name==="Notifications"||name==="Clipboard"||name==="Reply")props={backend:mock};
            if(name==="Tray")props={readOnly:true,items:[{id:"demo",title:"Demo tray item",tooltipTitle:"Demo",tooltipDescription:"Safe fixture",icon:"applications-system",status:1}],applets:[{id:"notifications",title:"Notifications",icon:"notifications",active:true}],settings:{},appletProperties:{readOnly:true,backend:mock}};
            if(name==="Power")props={readOnly:true,battery:mock,monitors:[]};
            if(name==="CalendarZones")Config.options.bar.plasma.clock={selectedTimeZones:["Local","Asia/Tokyo","America/New_York"],lastSelectedTimezone:"Local",displayTimezoneFormat:1};
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
                if(name==="Reply") {
                    const b=root.findText(loader.item,"Reply");
                    result.control=!!b;
                    if(b){const pos=b.mapToItem(loader.item,b.width/2,b.height/2);driver.mouseClick(loader.item,pos.x,pos.y);driver.wait(400);}
                    let field=null;const walk=i=>{if(!field&&i.placeholderText==="Reply to BWM")field=i;for(const c of i.children??[])walk(c);if(i.contentItem)walk(i.contentItem)};
                    walk(loader.item);
                    result.field=!!field;result.fieldFocused=!!field&&field.activeFocus;
                    if(field){field.text="Hola";field.accepted();driver.wait(50);}
                    result.replied=root.repliedText;
                }
                if(name==="Clipboard") {
                    result.entries=loader.item.backend.entries.length;
                    const found=[];const walk=i=>{if(i.objectName==="plasma-clipboard-image"&&!found.includes(i))found.push(i);for(const c of i.children??[])walk(c);if(i.contentItem)walk(i.contentItem)};
                    walk(loader.item.fullRepresentationItem??loader.item);
                    const img=found[0];
                    result.imageRows=found.length;
                    result.decoration=img?String(img.decoration):"";
                    let pic=null;const walk2=i=>{if(!pic&&i.sourceSize!==undefined&&i.status!==undefined&&String(i.source)!=="")pic=i;for(const c of i.children??[])walk2(c)};
                    if(img)walk2(img);
                    result.imageReady=!!pic&&pic.status===Image.Ready;result.imageWidth=pic?pic.width:0;result.imageHeight=pic?pic.height:0;
                    if(img)img.clicked();
                    result.copied=root.copied;
                    // Klipper's tool buttons: QR code page and edit page on the text row.
                    const stack=(function f(i){if(i.objectName==="plasma-clipboard-stack")return i;for(const c of i.children??[]){const r=f(c);if(r)return r}if(i.contentItem&&i.contentItem!==i){const r=f(i.contentItem);if(r)return r}return null})(loader.item.fullRepresentationItem??loader.item);
                    const qr=root.findText(loader.item.fullRepresentationItem??loader.item,"Show QR code");
                    result.qrButton=!!qr;
                    if(qr){qr.clicked();driver.wait(400);}
                    result.qrDepth=stack?stack.depth:0;
                    result.qrValid=!!stack?.currentItem?.valid;
                    if(stack&&stack.depth>1){stack.pop(null);driver.wait(300);}
                    const ed=root.findText(loader.item.fullRepresentationItem??loader.item,"Edit contents");
                    result.editButton=!!ed;
                    if(ed){ed.clicked();driver.wait(400);}
                    result.editDepth=stack?stack.depth:0;
                    const page=stack?.currentItem;
                    result.editText=page?.text??"";
                    if(page&&page.saveAndExit){page.text="Edited entry";page.saveAndExit();driver.wait(300);}
                    result.edited=root.editedText;result.removedAfterEdit=root.removed;result.backDepth=stack?stack.depth:0;
                }
                if(name==="Calendar") {result.calendar=!!loader.item.fullRepresentationItem?.monthView;}
                if(name==="CalendarZones") {const v=loader.item.fullRepresentationItem;result.calendar=!!v?.monthView;result.zones=loader.item.selectedTimeZonesDeduplicatingExplicitLocalTimeZone();result.showClocks=!!v?.showClocks;result.later=loader.item.formatOffset(new Date(loader.item.currentTime.getTime()+2*3600000));result.same=loader.item.formatOffset(loader.item.currentTime);result.current=loader.item.currentTimeZone;}
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
    def run_case(self,name,url,env=None):
        r=subprocess.run(['qs','-p',str(self.path)],env={**os.environ,'F5_CASE':name,'F5_URL':url,'LC_ALL':'C.UTF-8',**(env or {})},capture_output=True,text=True,timeout=12)
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
    def test_calendar_time_zones_from_native_keys(self):
        r=self.run_case('CalendarZones','applets/calendar/CalendarApplet.qml')
        self.assertTrue(r['calendar']);self.assertTrue(r['showClocks'])
        self.assertEqual(sorted(r['zones']),['America/New_York','Asia/Tokyo','Local'])
        self.assertIn('2',r['later']);self.assertIn('later',r['later'])
        self.assertEqual(r['same'],'')
        self.assertTrue(r['current'])
    def test_calendar(self):self.assertTrue(self.run_case('Calendar','applets/calendar/CalendarApplet.qml')['calendar'])
    def test_bluetooth_uses_mock_and_does_not_discover_on_open(self):
        result=self.run_case('Bluetooth','applets/BluetoothApplet.qml')
        self.assertTrue(result['control']);self.assertEqual(result['actions'],1);self.assertFalse(result['discovery'])
    def test_notification_action_uses_existing_backend(self):
        result=self.run_case('Notifications','applets/NotificationsApplet.qml')
        self.assertTrue(result['control']);self.assertEqual(result['actions'],1)
    def test_notification_inline_reply_like_plasma(self):
        # Plasma's ActionContainer shows "Reply" first, opens NotificationReplyField and
        # sends the text through the server (sendInlineReply), never by an action.
        result=self.run_case('Reply','applets/NotificationsApplet.qml')
        self.assertTrue(result['control'],result);self.assertTrue(result['field'],result)
        self.assertTrue(result['fieldFocused'],result)
        self.assertEqual(result['replied'],'Hola');self.assertEqual(result['actions'],0)
    def test_clipboard_text_and_image_entries(self):
        # Klipper shows images with ImageItemDelegate; the cliphist entry is decoded by a fake
        # binary into a private runtime directory, never into the user's clipboard.
        with tempfile.TemporaryDirectory() as tmp:
            png=Path(tmp)/'img.png'
            subprocess.run(['magick','-size','40x20','xc:#3daee9',str(png)],check=True)
            fake=Path(tmp)/'cliphist'
            fake.write_text('#!/bin/sh\n[ "$1" = decode ] && [ "$2" = 2 ] && exec cat '+str(png)+'\nexit 1\n')
            fake.chmod(0o755)
            runtime=Path(tmp)/'run';runtime.mkdir(mode=0o700)
            r=self.run_case('Clipboard','applets/ClipboardApplet.qml',env={'F5_FAKE_CLIPHIST':str(fake),'XDG_RUNTIME_DIR':str(runtime),
                'WAYLAND_DISPLAY':os.path.join(os.environ['XDG_RUNTIME_DIR'],os.environ.get('WAYLAND_DISPLAY','wayland-1'))})
            self.assertEqual(r['entries'],2);self.assertEqual(r['imageRows'],1)
            self.assertTrue(r['decoration'].endswith('/bwm-plasma-clipboard/2'),r)
            self.assertTrue(r['imageReady'],r)
            self.assertEqual((r['imageWidth'],r['imageHeight']),(40,20))
            self.assertEqual(r['copied'],1)
            self.assertTrue(r['qrButton'],r);self.assertEqual(r['qrDepth'],2);self.assertTrue(r['qrValid'],r)
            self.assertTrue(r['editButton'],r);self.assertEqual(r['editDepth'],2)
            self.assertEqual(r['editText'],'Demo clipboard entry')
            self.assertEqual(r['edited'],'Edited entry');self.assertEqual(r['removedAfterEdit'],1)
            self.assertEqual(r['backDepth'],1)
            self.assertEqual(oct((runtime/'bwm-plasma-clipboard').stat().st_mode&0o777),'0o700')
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


class BluetoothAppletTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('BWM_RUN_QML_TESTS') == '1' and shutil.which('qs'),
                         'optional isolated Wayland UI tests')
    def test_bluetooth_forget_device_unpaired_and_dialog_geometry(self):
        harness = r'''//@ pragma UseQApplication
import QtQuick
import QtTest
import Quickshell
import Quickshell.Bluetooth
import qs.modules.plasma.applets as Applets
ShellRoot {
    id: root
    property int forgot: 0
    QtObject {
        id: dev
        property string name: "Gamepad"
        property string address: "11:22:33:44:55:66"
        property string icon: "input-gaming"
        property bool connected: false
        property bool paired: false
        property bool pairing: false
        property int state: BluetoothDeviceState.Disconnected
        property bool batteryAvailable: false
        property real battery: 0
        function forget() { root.forgot++; }
        function connect() {}
        function disconnect() {}
        function pair() {}
    }
    QtObject { id: mockBackend; property bool available: true; property bool enabled: true; property var friendlyDeviceList: [dev] }
    QtObject { id: mockAdapter; property bool discovering: false; property bool enabled: true }
    FloatingWindow {
        id: win
        title: "bwm-bt-forget-test"
        implicitWidth: 360; implicitHeight: 420
        Applets.BluetoothApplet { id: applet; anchors.fill: parent; backend: mockBackend; adapter: mockAdapter }
        TestCase { id: driver; name: "BtForget"; when: false }
    }
    Timer { running: true; interval: 4000; onTriggered: Qt.quit() }
    function findText(item, txt) {
        if (!item) return null;
        if (item.text === txt && item.visible) return item;
        for (const c of (item.children || [])) { const r = findText(c, txt); if (r) return r; }
        return null;
    }
    function findDialog(item) {
        if (!item) return null;
        if (item.standardButtons !== undefined && item.open !== undefined) return item;
        for (const c of (item.children || [])) { const r = findDialog(c); if (r) return r; }
        for (const d of (item.data || [])) { const r = findDialog(d); if (r) return r; }
        return null;
    }
    Timer {
        running: true; interval: 400
        onTriggered: {
            const row = findText(applet, "Gamepad");
            if (row) {
                const pos = row.mapToItem(applet, row.width / 2, row.height / 2);
                driver.mouseClick(applet, pos.x, pos.y);
                driver.wait(200);
            }
            const btn = findText(applet, "Forget Device");
            const btnEnabled = btn ? btn.enabled : false;
            if (btn && btn.enabled) {
                const bpos = btn.mapToItem(applet, btn.width / 2, btn.height / 2);
                driver.mouseClick(applet, bpos.x, bpos.y);
                driver.wait(200);
            }
            const dlg = findDialog(applet);
            const dlgVisible = dlg ? dlg.visible : false;
            const dlgX = dlg ? dlg.x : -1;
            const dlgY = dlg ? dlg.y : -1;
            const dlgH = dlg ? dlg.height : 0;
            if (dlg && dlg.visible) {
                const okBtn = findText(dlg.footer, "OK") || findText(dlg.contentItem?.parent, "OK");
                if (okBtn) {
                    const opos = okBtn.mapToItem(win.contentItem, okBtn.width / 2, okBtn.height / 2);
                    driver.mouseClick(win.contentItem, opos.x, opos.y);
                    driver.wait(150);
                }
            }
            console.log("BTFORGET " + JSON.stringify({ btnEnabled, dlgVisible, dlgX, dlgY, dlgH, forgot: root.forgot }));
            Qt.quit();
        }
    }
}
'''
        rule = 'hl.window_rule({name="tmp-bwm-bt-forget",match={title="^bwm-bt-forget-test$"},workspace="9 silent"})'
        if shutil.which('hyprctl'):
            subprocess.run(['hyprctl', 'eval', rule], capture_output=True, text=True, timeout=5)
        tmp = tempfile.NamedTemporaryFile('w', dir=ROOT / 'config/quickshell/ii', prefix='zz_prueba_bt_', suffix='.qml', delete=False)
        try:
            tmp.write(harness)
            tmp.close()
            r = subprocess.run(['qs', '-p', tmp.name], env={**os.environ, 'LC_ALL': 'C.UTF-8'}, capture_output=True, text=True, timeout=12)
        finally:
            Path(tmp.name).unlink(missing_ok=True)
            if shutil.which('hyprctl'):
                subprocess.run(['hyprctl', 'reload'], capture_output=True, text=True, timeout=5)
        log = r.stdout + r.stderr
        self.assertEqual(r.returncode, 0, log)
        line = next((l for l in log.splitlines() if 'BTFORGET ' in l), '')
        self.assertTrue(line, log)
        data = json.loads(line.split('BTFORGET ', 1)[1])
        self.assertTrue(data['btnEnabled'], data)
        self.assertTrue(data['dlgVisible'], data)
        self.assertGreater(data['dlgX'], 0, data)
        self.assertGreater(data['dlgY'], 0, data)
        self.assertGreater(data['dlgH'], 80, data)
        self.assertEqual(data['forgot'], 1, data)


class TrayMenuAndCursorCloseTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('BWM_RUN_QML_TESTS') == '1' and shutil.which('qs'),
                         'optional isolated Wayland UI tests')
    def test_tray_sni_menu_opens_in_overlay_above_44px_panel_and_closes_on_outside_click(self):
        harness = r'''//@ pragma UseQApplication
import QtQuick
import QtTest
import Quickshell
import Quickshell.Wayland
import qs.modules.common
import qs.modules.plasma.menus as M
import qs.modules.plasma.tray as TrayPort
ShellRoot {
    id: root
    Component.onCompleted: Config.blockWrites = true
    M.MenuHost { id: menuHost }
    PanelWindow {
        id: panelWin
        implicitWidth: 600; implicitHeight: 44
        anchors { bottom: true; left: true; right: true }
        WlrLayershell.layer: WlrLayer.Top
        exclusionMode: ExclusionMode.Ignore
        TrayPort.SystemTray {
            id: tray
            anchors.centerIn: parent
            items: [mockItem]
            applets: []
            settings: ({ demo: "shown" })
        }
        TestCase { id: driver; name: "TrayMenuOverlay"; when: false }
    }
    QtObject {
        id: subEntry
        property bool hasChildren: false
        property bool isSeparator: false
        property string text: "Sub Action"
        property bool enabled: true
        property int buttonType: 0
        property int checkState: Qt.Unchecked
        property string icon: ""
        function triggered() {}
    }
    QtObject {
        id: entry1
        property bool hasChildren: true
        property bool isSeparator: false
        property string text: "Options"
        property var mockEntries: [subEntry]
    }
    QtObject {
        id: sepEntry
        property bool hasChildren: false
        property bool isSeparator: true
    }
    QtObject {
        id: entry2
        property bool hasChildren: false
        property bool isSeparator: false
        property string text: "Quit Application"
        property bool enabled: true
        property int buttonType: 0
        property int checkState: Qt.Unchecked
        property string icon: "application-exit"
        function triggered() {}
    }
    QtObject {
        id: mockMenu
        property var mockEntries: [entry1, sepEntry, entry2]
    }
    QtObject {
        id: mockItem
        property string id: "demo"
        property string title: "Demo SNI"
        property string tooltipTitle: "Demo SNI"
        property string tooltipDescription: ""
        property string icon: "applications-system"
        property int status: 1
        property bool onlyMenu: false
        property var menu: mockMenu
    }
    Timer { running: true; interval: 4000; onTriggered: Qt.quit() }
    Timer {
        running: true; interval: 450
        onTriggered: {
            tray.openMenu(mockItem, tray);
            driver.wait(200);
            const m = menuHost.menu;
            const opened = M.PlasmaMenus.opened && !!m && m.opened;
            const kind = M.PlasmaMenus.kind;
            const menuH = m ? m.height : 0;
            const menuW = m ? m.width : 0;
            const count = m ? m.count : 0;
            const subTitle = m && m.count > 0 && m.itemAt(0).subMenu ? m.itemAt(0).subMenu.title : "";
            // Click outside the menu on the MenuHost overlay catcher
            const hostItem = m ? m.parent : null;
            const catcher = hostItem ? hostItem.parent.children[0] : null;
            if (catcher) {
                driver.mouseClick(catcher, 10, 10);
                driver.wait(100);
            }
            const closedOnOutsideClick = !M.PlasmaMenus.opened && !menuHost.menu;
            console.log("TRAYMENUHOST " + JSON.stringify({
                opened, kind, menuH, menuW, count, subTitle, closedOnOutsideClick
            }));
            Qt.quit();
        }
    }
}
'''
        tmp = tempfile.NamedTemporaryFile('w', dir=ROOT / 'config/quickshell/ii', prefix='zz_prueba_traymenu_', suffix='.qml', delete=False)
        try:
            tmp.write(harness)
            tmp.close()
            r = subprocess.run(['qs', '-p', tmp.name], env={**os.environ, 'LC_ALL': 'C.UTF-8'}, capture_output=True, text=True, timeout=12)
        finally:
            Path(tmp.name).unlink(missing_ok=True)
        log = r.stdout + r.stderr
        self.assertEqual(r.returncode, 0, log)
        self.assertNotIn('TypeError:', log)
        line = next((l for l in log.splitlines() if 'TRAYMENUHOST ' in l), '')
        self.assertTrue(line, log)
        data = json.loads(line.split('TRAYMENUHOST ', 1)[1])
        self.assertTrue(data['opened'], data)
        self.assertEqual(data['kind'], 'tray', data)
        self.assertGreater(data['menuH'], 60, data)  # Not clipped to the 44px panel!
        self.assertGreater(data['menuW'], 100, data)
        self.assertEqual(data['count'], 3, data)
        self.assertEqual(data['subTitle'], 'Options', data)
        self.assertTrue(data['closedOnOutsideClick'], data)

    def test_breeze_window_close_targets_window_under_cursor(self):
        user_binds = (ROOT / 'config/hypr/modules/user_binds.lua').read_text(encoding='utf-8')
        self.assertIn('local function close_window_target()', user_binds)
        self.assertIn('(is_plasma and close_window_target or hl.dsp.window.close)()', user_binds)


