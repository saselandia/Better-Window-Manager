# SPDX-License-Identifier: GPL-2.0-or-later
"""Common shared-settings delivery, without a session, shell panels or real IPC."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'config/hypr/scripts'))
import bwm_settings_hooks as hooks
import bwm_skins


class SharedDeliveryTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='bwm-shared-test-');self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.config=self.root/'config';self.state=self.root/'state'
        self.env=mock.patch.dict(os.environ,{'XDG_CONFIG_HOME':str(self.config),'XDG_STATE_HOME':str(self.state),'XDG_DATA_HOME':str(self.root/'data')})
        self.env.start();self.addCleanup(self.env.stop)
        self.options=self.config/'illogical-impulse/config.json';self.options.parent.mkdir(parents=True)
        self.options.write_text(json.dumps({'appearance':{'bwmTheme':'retro'},'bar':{'workspaces':{'shown':6}},'unknown':42}))

    def skin(self,**entry):
        return {'id':'reviewed','builtin':True,'dir':str(self.root/'skin'),'hooks':{'sharedSettings':{'script':'hook.py','requiresConfigFile':'hypr/plugins/test.so','intervalMs':2000,**entry}}}

    def test_uninstalled_adapter_is_noop_even_from_another_skin(self):
        with mock.patch.object(hooks.subprocess,'run') as run:
            report=hooks.shared()
        run.assert_not_called();self.assertEqual(report['retryMs'],0)
        self.assertFalse(any(a['active'] for a in report['adapters']))
        self.assertFalse(self.state.exists())

    def test_effective_options_uses_current_skin_overrides_and_never_writes_user_file(self):
        user=self.config/'bwm/user/shell.jsonc';user.parent.mkdir(parents=True)
        text='{"all":{"bar":{"workspaces":{"shown":9}}},"skins":{"retro":{"bar":{"workspaces":{"shown":11}}}}}'
        user.write_text(text)
        self.assertEqual(hooks.effective_options()['bar']['workspaces']['shown'],11)
        options=json.loads(self.options.read_text());options['appearance']['bwmTheme']='default';self.options.write_text(json.dumps(options))
        self.assertEqual(hooks.effective_options()['bar']['workspaces']['shown'],9)
        self.assertEqual(user.read_text(),text)

    def test_unselected_downloaded_skin_does_not_register_background_execution(self):
        skin=self.skin();skin['builtin']=False
        with mock.patch.object(bwm_skins,'all_skins',return_value=[skin]),mock.patch.object(hooks.subprocess,'run') as run:
            self.assertEqual(hooks.shared()['adapters'],[])
        run.assert_not_called()

    def test_invalid_script_prerequisite_or_interval_is_rejected_before_execution(self):
        for entry in [{'script':'../escape.py'},{'requiresConfigFile':'../escape'},{'requiresConfigFile':'/tmp/outside'},{'intervalMs':True},{'intervalMs':20}]:
            with self.subTest(entry=entry),mock.patch.object(bwm_skins,'all_skins',return_value=[self.skin(**entry)]),mock.patch.object(hooks.subprocess,'run') as run:
                report=hooks.shared();self.assertIn('error',report['adapters'][0]);run.assert_not_called()

    def test_timeout_or_bad_receipt_keeps_bounded_retry_without_claiming_application(self):
        prerequisite=self.config/'hypr/plugins/test.so';prerequisite.parent.mkdir(parents=True);prerequisite.touch()
        for result in [subprocess.TimeoutExpired('fixture',3),subprocess.CompletedProcess([],0,'{"version":true,"applied":true}',''),subprocess.CompletedProcess([],0,'{}',''),
                       subprocess.CompletedProcess([],0,'{"version":1,"applied":false,"error":"fixture unavailable"}','')]:
            kwargs={'side_effect':result} if isinstance(result,Exception) else {'return_value':result}
            with mock.patch.object(bwm_skins,'all_skins',return_value=[self.skin()]),mock.patch.object(hooks.subprocess,'run',**kwargs):
                report=hooks.shared();self.assertEqual(report['retryMs'],2000)
                self.assertTrue(report['adapters'][0]['active']);self.assertFalse(report['adapters'][0]['applied'])
                if not isinstance(result,Exception) and 'fixture unavailable' in result.stdout:self.assertEqual(report['adapters'][0]['error'],'fixture unavailable')

    @unittest.skipUnless((ROOT/'build/bwm-plasma-host/desktop-protocol/test-workspace-projection').is_file(),'native receipt fixture not built')
    def test_actual_hook_cli_tracks_default_retro_breeze_with_native_receipts(self):
        plugin=self.config/'hypr/plugins/bwm-plasma-desktops.so';plugin.parent.mkdir(parents=True);plugin.touch()
        user=self.config/'bwm/user/shell.jsonc';user.parent.mkdir(parents=True)
        user_text='{"all":{"bar":{"workspaces":{"shown":9}}},"skins":{"retro":{"bar":{"workspaces":{"shown":11}}}}}'
        user.write_text(user_text)
        log=self.root/'commands.jsonl';binary=ROOT/'build/bwm-plasma-host/desktop-protocol/test-workspace-projection'
        bindir=self.root/'bin';bindir.mkdir();hyprctl=bindir/'hyprctl'
        hyprctl.write_text('#!'+sys.executable+'\nimport json,subprocess,sys\nfrom pathlib import Path\n'
            +f'with open({str(log)!r},"a") as f:f.write(json.dumps(sys.argv[1:])+"\\n")\n'
            +f'r=subprocess.run([{str(binary)!r},"--receipt"," ".join(sys.argv[1:])],capture_output=True,text=True,check=True)\nprint(r.stdout,end="")\n')
        hyprctl.chmod(0o700)
        with mock.patch.dict(os.environ,{'PATH':str(bindir)+os.pathsep+os.environ['PATH']}):
            for skin in ['default','retro','plasma']:
                options=json.loads(self.options.read_text());options['appearance']['bwmTheme']=skin;self.options.write_text(json.dumps(options))
                report=hooks.shared();self.assertEqual(report['retryMs'],2000)
                self.assertTrue(next(a for a in report['adapters'] if a['skin']=='plasma')['applied'])
        self.assertEqual([json.loads(line) for line in log.read_text().splitlines()],
            [['bwm-plasma-desktops-count','9'],['bwm-plasma-desktops-count','11'],['bwm-plasma-desktops-count','9']])
        self.assertEqual(user.read_text(),user_text);self.assertEqual(json.loads(self.options.read_text())['unknown'],42)
        self.assertFalse((self.config/'kwinrc').exists());self.assertFalse((self.state/'bwm/plasma/bridge.json').exists())

    @unittest.skipUnless(shutil.which('qs') and (ROOT/'build/bwm-plasma-host/desktop-protocol/test-workspace-projection').is_file(),'shared pipeline fixtures unavailable')
    def test_headless_coordinator_to_dispatcher_adapter_and_native_receipts(self):
        plugin=self.config/'hypr/plugins/bwm-plasma-desktops.so';plugin.parent.mkdir(parents=True);plugin.touch()
        options=json.loads(self.options.read_text());options['appearance']['bwmTheme']='default';options['bar']['workspaces']['shown']=3
        self.options.write_text(json.dumps(options))
        log=self.root/'pipeline.jsonl';bindir=self.root/'bin';bindir.mkdir()
        binary=ROOT/'build/bwm-plasma-host/desktop-protocol/test-workspace-projection'
        script=bindir/'hyprctl';script.write_text('#!'+sys.executable+'\nimport json,subprocess,sys\nfrom pathlib import Path\n'
            +f'p=Path({str(log)!r});config=Path({str(self.options)!r})\n'
            +'n=len(p.read_text().splitlines()) if p.exists() else 0\n'
            +'with p.open("a") as f:f.write(json.dumps(sys.argv[1:])+"\\n")\n'
            +f'r=subprocess.run([{str(binary)!r},"--receipt"," ".join(sys.argv[1:])],capture_output=True,text=True,check=True)\n'
            +'if n<2:\n v=json.loads(config.read_text());v["appearance"]["bwmTheme"]=["retro","plasma"][n];v["bar"]["workspaces"]["shown"]=[7,5][n];config.write_text(json.dumps(v))\n'
            +'print(r.stdout,end="")\n');script.chmod(0o700)
        runtime=self.root/'runtime';runtime.mkdir(mode=0o700)
        command=json.dumps([sys.executable,str(ROOT/'config/hypr/scripts/bwm_settings_hooks.py'),'shared'])
        qml=self.root/'pipeline.qml';qml.write_text('''import QtQuick
import Quickshell
import "'''+(ROOT/'config/quickshell/ii/services').as_uri()+'''" as Services
Scope {
    Services.SharedSettingsRuntime {
        id: service
        ready:true; workspaceCount:3; skin:"default"; dispatcherCommand:'''+command+'''
        onPassFinished: report => {
            if (!report.adapters || !report.adapters.some(a => a.applied)) {console.log("PIPELINE false");Qt.quit();return;}
            if(completedPasses===1){skin="retro";workspaceCount=7;}
            else if(completedPasses===2){skin="plasma";workspaceCount=5;}
            else {console.log("PIPELINE true");Qt.quit();}
        }
    }
    Timer {interval:6500;running:true;onTriggered:{console.log("PIPELINE timeout");Qt.quit();}}
}
''')
        env={**os.environ,'PATH':str(bindir)+os.pathsep+os.environ['PATH'],'QT_QPA_PLATFORM':'offscreen',
             'XDG_RUNTIME_DIR':str(runtime),'DBUS_SESSION_BUS_ADDRESS':'unix:path='+str(self.root/'no-bus')}
        for name in ['DISPLAY','WAYLAND_DISPLAY','WAYLAND_SOCKET','HYPRLAND_INSTANCE_SIGNATURE']:env.pop(name,None)
        result=subprocess.run(['qs','-p',str(qml)],env=env,capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr);self.assertIn('PIPELINE true',result.stdout+result.stderr)
        self.assertEqual([json.loads(line) for line in log.read_text().splitlines()],
            [['bwm-plasma-desktops-count','3'],['bwm-plasma-desktops-count','7'],['bwm-plasma-desktops-count','5']])
        self.assertFalse((self.config/'kwinrc').exists())


@unittest.skipUnless(shutil.which('qs'),'Quickshell unavailable')
class SharedCoordinatorTest(unittest.TestCase):
    def run_case(self,case):
        with tempfile.TemporaryDirectory(prefix='bwm-shared-qml-') as tmp:
            root=Path(tmp);runtime=root/'runtime';runtime.mkdir(mode=0o700);log=root/'processes.jsonl'
            worker=root/'worker.py'
            worker.write_text('import json,os,time\nfrom pathlib import Path\n'+f'p=Path({str(log)!r})\n'
                +'n=len(p.read_text().splitlines())//2 if p.exists() else 0\n'
                +'with p.open("a") as f:f.write(json.dumps(["start",os.getpid()])+"\\n")\n'
                +'time.sleep(.2)\n'
                +f'print("invalid" if {case!r}=="bad" and n==0 else json.dumps({{"version":1,"retryMs":1000 if {case!r}=="retry" and n==0 else 0}}))\n'
                +'with p.open("a") as f:f.write(json.dumps(["end",os.getpid()])+"\\n")\n')
            command=json.dumps([sys.executable,str(worker)]);service=(ROOT/'config/quickshell/ii/services').as_uri()
            qml=root/'test.qml';qml.write_text('''import QtQuick
import Quickshell
import "'''+service+'''" as Services
Scope {
    property string testCase: '''+json.dumps(case)+'''
    property int burst: 0
    property bool sawFailure: false
    Services.SharedSettingsRuntime {
        id: service
        ready: testCase !== "not-ready"
        workspaceCount: 4
        skin: "retro"
        dispatcherCommand: testCase === "missing" ? ["/nonexistent-bwm-shared-fixture"] : '''+command+'''
        onBusyChanged: if (busy && testCase === "burst" && burst === 0) edits.start()
        onPassFinished: report => {
            if (report.error) sawFailure = true;
            if (completedPasses === 1 && (testCase === "missing" || testCase === "bad")) {
                dispatcherCommand = '''+command+'''; workspaceCount++;
            }
            const expected = testCase === "not-ready" ? 1 : 2;
            if (completedPasses >= expected) {
                console.log("SHAREDRESULT "+JSON.stringify({passed:!report.error,passes:completedPasses,count:workspaceCount,sawFailure:sawFailure}));
                Qt.quit();
            }
        }
    }
    Timer { id: edits; interval:20; repeat:true; onTriggered:{service.workspaceCount++;burst++;if(burst===5)stop();} }
    Timer { interval:400; running:testCase==="not-ready"; onTriggered:{if(service.completedPasses!==0)throw new Error("ran before ready");service.ready=true;} }
    Timer { interval:6500; running:true; onTriggered:{console.log("SHAREDRESULT "+JSON.stringify({passed:false,timeout:true,passes:service.completedPasses}));Qt.quit();} }
}
''')
            env={**os.environ,'QT_QPA_PLATFORM':'offscreen','XDG_RUNTIME_DIR':str(runtime),'DBUS_SESSION_BUS_ADDRESS':'unix:path='+str(root/'no-bus')}
            for name in ['DISPLAY','WAYLAND_DISPLAY','WAYLAND_SOCKET','HYPRLAND_INSTANCE_SIGNATURE']:env.pop(name,None)
            result=subprocess.run(['qs','-p',str(qml)],env=env,capture_output=True,text=True,timeout=10)
            output=result.stdout+result.stderr
            self.assertEqual(result.returncode,0,output)
            values=[json.loads(line.split('SHAREDRESULT ',1)[1]) for line in output.splitlines() if 'SHAREDRESULT ' in line]
            self.assertTrue(values,output);self.assertTrue(values[-1]['passed'],output)
            events=[json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual([e[0] for e in events],['start','end']*(len(events)//2))
            return values[-1],len(events)//2

    def test_changes_during_delivery_coalesce_without_overlapping_processes(self):
        result,calls=self.run_case('burst');self.assertEqual(calls,2);self.assertEqual(result['count'],9)

    def test_armed_adapter_retries_without_another_preference_change(self):
        result,calls=self.run_case('retry');self.assertEqual(calls,2)

    def test_invalid_receipt_recovers_on_new_change(self):
        result,calls=self.run_case('bad');self.assertTrue(result['sawFailure']);self.assertEqual(calls,2)

    def test_failed_to_start_does_not_leave_coordinator_busy(self):
        result,calls=self.run_case('missing');self.assertTrue(result['sawFailure']);self.assertEqual(calls,1)

    def test_does_not_deliver_before_settings_are_ready(self):
        result,calls=self.run_case('not-ready');self.assertEqual(calls,1)
