# SPDX-License-Identifier: GPL-2.0-or-later
"""Preview startup failures must be actionable before reaching the live session."""
import os
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import importlib.util
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'src/bwm-plasma-host/preview-isolated.py'
spec=importlib.util.spec_from_file_location('r4_previewchecks',SCRIPT.with_name('previewchecks.py'))
checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)


class TaskStartupTest(unittest.TestCase):
    def test_dead_child_and_missing_ack_report_startup_cause(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);child=Mock();child.poll.return_value=8
            with self.assertRaisesRegex(ValueError,'código 8'):
                checks.wait_initial_ack(root,child)
            self.assertFalse((root/'ack.json').exists())
            (root/'ack.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'código 8'):
                checks.wait_initial_ack(root,child)
            child.poll.return_value=None;checks.wait_initial_ack(root,child)

    def test_initial_ack_timeout_is_distinct_from_child_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            now=[0.0];child=Mock();child.poll.return_value=None
            with self.assertRaisesRegex(TimeoutError,'arranque a tiempo'):
                checks.wait_initial_ack(Path(tmp),child,timeout=.03,clock=lambda:now[0],pause=lambda s:now.__setitem__(0,now[0]+s))

    def test_thumbnail_preview_requires_capture_protocols(self):
        now=[0.0];session=Mock();child=Mock();child.poll.return_value=None
        session.command.return_value={'runtime':self.ready(thumbnails={'enabled':True,'protocolsReady':False})}
        with self.assertRaisesRegex(TimeoutError,'protocolos de captura'):
            checks.wait_task_source(session,{},child,require_thumbnails=True,timeout=.2,clock=lambda:now[0],pause=lambda seconds:now.__setitem__(0,now[0]+seconds))
        session.command.return_value={'runtime':self.ready(thumbnails={'enabled':True,'protocolsReady':True})}
        self.assertEqual(checks.wait_task_source(session,{},child,require_thumbnails=True)['windowCount'],2)
    def ready(self,**values):
        return {'taskSource':{'enabled':True,'snapshotAvailable':True,'suspended':False,'windowCount':2,'boundModels':1,
            'taskViewDiagnosticsVersion':1,'viewModels':2,'currentDesktopFilteringViews':0,'visibleWindowRows':2,'launcherRows':0,
            'applicationLauncher':{'inProcessLaunchDenied':True},**values}}

    def test_task_ready_requires_kiosk_denial_of_in_process_launches(self):
        for launch in ({},{'inProcessLaunchDenied':False},{'inProcessLaunchDenied':1},None):
            with self.subTest(launch=launch):self.assertIsNone(checks.task_source_summary(self.ready(applicationLauncher=launch)))

    def test_task_ready_requires_valid_source_and_only_reports_counts(self):
        self.assertEqual(checks.task_source_summary(self.ready(lastError='Historical error',privateWindows=['not exported'])),{'windowCount':2,'boundModels':1,'visibleWindowRows':2,'launcherRows':0})
        self.assertEqual(checks.task_source_summary(self.ready(windowCount=0,visibleWindowRows=0)),{'windowCount':0,'boundModels':1,'visibleWindowRows':0,'launcherRows':0})
        for bad in ({'enabled':False},{'snapshotAvailable':False},{'suspended':True},{'boundModels':0},{'boundModels':True},{'windowCount':True},{'windowCount':-1},
                    {'taskViewDiagnosticsVersion':0},{'taskViewDiagnosticsVersion':True},{'viewModels':0}):
            with self.subTest(bad=bad):self.assertIsNone(checks.task_source_summary(self.ready(**bad)))

    def test_waits_for_connected_source_instead_of_accepting_running_launchers(self):
        now=[0.0];session=Mock();child=Mock();child.poll.return_value=None
        session.command.side_effect=[{'runtime':self.ready(boundModels=0)},{'runtime':self.ready(snapshotAvailable=False)},{'runtime':self.ready()}]
        result=checks.wait_task_source(session,{},child,timeout=1,clock=lambda:now[0],pause=lambda seconds:now.__setitem__(0,now[0]+seconds))
        self.assertEqual(result,{'windowCount':2,'boundModels':1,'visibleWindowRows':2,'launcherRows':0});self.assertEqual(session.command.call_count,3)
        self.assertTrue(all(call.args[1]=='status' for call in session.command.call_args_list))

    def test_missing_source_or_dead_child_is_not_reported_as_ready(self):
        now=[0.0];session=Mock();child=Mock();child.poll.return_value=None
        session.command.return_value={'runtime':self.ready(boundModels=0,lastError='Task snapshot unavailable')}
        with self.assertRaisesRegex(TimeoutError,'Task snapshot unavailable'):
            checks.wait_task_source(session,{},child,timeout=.2,clock=lambda:now[0],pause=lambda seconds:now.__setitem__(0,now[0]+seconds))
        child.poll.return_value=1;session.command.reset_mock()
        with self.assertRaisesRegex(ValueError,'terminó'):
            checks.wait_task_source(session,{},child)
        session.command.assert_not_called()

    def test_current_desktop_filter_requires_confirmed_native_provider(self):
        runtime=self.ready(currentDesktopFilteringViews=2,visibleWindowRows=0,launcherRows=4)
        self.assertIsNone(checks.task_source_summary(runtime))
        runtime['nativeDesktopControl']={'resumed':True}
        self.assertIsNotNone(checks.task_source_summary(runtime))
        for invalid in (None,[],{}, {'taskSource':None}):
            self.assertIsNone(checks.task_source_summary(invalid))


class PreviewStartupTest(unittest.TestCase):
    def test_profile_recovery_is_offscreen_and_bypasses_broken_head_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);profile=root/'profile';profile.mkdir();(profile/'head.json').write_text('{broken')
            # Keep the spelling of an alias so native canonical-path validation
            # can reject it; the wrapper must not silently resolve it first.
            alias=root/'alias';alias.symlink_to(profile,target_is_directory=True)
            binary=root/'probe';observed=root/'observed.json';snapshot='1a'*16
            binary.write_text('#!'+sys.executable+'\nimport json,os,sys\nfrom pathlib import Path\n'
                +'assert sys.argv[1:]==["--recover-profile",'+repr(str(alias/'snapshots'/snapshot))+']\n'
                +'assert os.environ["QT_QPA_PLATFORM"]=="offscreen"\n'
                +'assert not any(k in os.environ for k in ("DISPLAY","WAYLAND_DISPLAY","HYPRLAND_INSTANCE_SIGNATURE","BWM_R4_NATIVE_DESKTOPS","BWM_R4_TASK_ACTIONS","BWM_R4_DESKTOP_ACTIONS","BWM_R4_NATIVE_PANEL_POLICY"))\n'
                +'assert not Path(os.environ["DBUS_SESSION_BUS_ADDRESS"].split("unix:path=",1)[1]).exists()\n'
                +'Path('+repr(str(observed))+').write_text(json.dumps({k:os.environ[k] for k in ("XDG_CONFIG_HOME","XDG_DATA_HOME","XDG_CACHE_HOME","XDG_RUNTIME_DIR")}))\n'
                +'print(json.dumps({"status":"native-profile-recovered","activationAllowed":False}))\n');binary.chmod(0o700)
            reply=subprocess.run([sys.executable,str(SCRIPT),'--binary',str(binary),'--profile',str(alias),'--recover-snapshot',snapshot],
                env=dict(os.environ,DISPLAY=':fake',WAYLAND_DISPLAY='fake',HYPRLAND_INSTANCE_SIGNATURE='fake',
                         BWM_R4_NATIVE_DESKTOPS='1',BWM_R4_TASK_ACTIONS='1',BWM_R4_DESKTOP_ACTIONS='1',BWM_R4_NATIVE_PANEL_POLICY='1'),
                capture_output=True,text=True,timeout=5)
            self.assertEqual(reply.returncode,0,reply.stderr);self.assertFalse(json.loads(reply.stdout)['activationAllowed'])
            self.assertEqual((profile/'head.json').read_text(),'{broken')
            self.assertTrue(all(not Path(path).exists() for path in json.loads(observed.read_text()).values()))

    def test_profile_recovery_requires_explicit_id_and_excludes_preview_modes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);marker=root/'executed';binary=root/'probe'
            binary.write_text('#!'+sys.executable+'\nfrom pathlib import Path\nPath('+repr(str(marker))+').touch()\n');binary.chmod(0o700)
            for args in (['--recover-snapshot','../escape'],['--recover-snapshot','AB'*16],
                         ['--recover-snapshot','1a'*16,'--follow-skin'],['--recover-snapshot','1a'*16,'--export-as','test'],
                         ['--recover-snapshot','1a'*16,'--native-panel'],['--recover-snapshot','1a'*16,'--task-actions'],
                         ['--recover-snapshot','1a'*16,'--output','Fixture output']):
                with self.subTest(args=args):
                    reply=subprocess.run([sys.executable,str(SCRIPT),'--binary',str(binary),'--profile',str(root/'profile'),*args],capture_output=True,text=True,timeout=5)
                    self.assertEqual(reply.returncode,2);self.assertNotIn('Traceback',reply.stderr);self.assertFalse(marker.exists())

    def test_profile_recovery_reports_native_refusal_without_starting_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary=Path(tmp)/'probe';binary.write_text('#!'+sys.executable+'\nimport sys\nsys.stderr.write("Another process owns this native profile\\n")\nraise SystemExit(7)\n');binary.chmod(0o700)
            reply=subprocess.run([sys.executable,str(SCRIPT),'--binary',str(binary),'--profile',str(Path(tmp)/'profile'),
                '--recover-snapshot','1a'*16],capture_output=True,text=True,timeout=5)
            self.assertEqual(reply.returncode,2);self.assertIn('Another process owns',reply.stderr);self.assertNotIn('Traceback',reply.stderr)

    def test_compositor_check_only_uses_readonly_mode_and_private_stores(self):
        script=SCRIPT.with_name('check-thumbnail-compositor.py')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);runtime=root/'runtime';runtime.mkdir()
            binary=root/'probe';binary.write_text('#!'+sys.executable+'\nimport json,os,sys\n'
                +'assert sys.argv[1:]==["--check-thumbnail-compositor"]\n'
                +'assert "BWM_R4_TASK_ACTIONS" not in os.environ\n'
                +'print(json.dumps({"verified":False,"reason":"cannot-read-peer-executable",'
                +'"display":os.environ["WAYLAND_DISPLAY"],"runtime":os.environ["XDG_RUNTIME_DIR"],"guardRuntime":os.environ["BWM_R4_GUARD_RUNTIME"]}))\n'
                +'raise SystemExit(2)\n');binary.chmod(0o700)
            reply=subprocess.run([sys.executable,str(script),'--binary',str(binary)],
                env=dict(os.environ,WAYLAND_DISPLAY='own-fixture',XDG_RUNTIME_DIR=str(runtime),BWM_R4_TASK_ACTIONS='1',BWM_R4_GUARD_RUNTIME='/wrong-inherited-runtime'),
                capture_output=True,text=True,timeout=5)
            self.assertEqual(reply.returncode,2);result=json.loads(reply.stdout)
            self.assertFalse(result['capturesStarted']);self.assertFalse(result['sessionModified'])
            self.assertEqual(result['guard']['display'],str(runtime/'own-fixture'))
            self.assertNotEqual(result['guard']['runtime'],str(runtime))
            self.assertEqual(result['guard']['guardRuntime'],str(runtime))
            self.assertEqual(result['guard']['reason'],'cannot-read-peer-executable')

    def test_task_thumbnails_cannot_modify_saved_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);binary=root/'unused';binary.write_text('#!/bin/false\n');binary.chmod(0o700)
            profile=root/'profile';profile.mkdir();marker=profile/'unchanged';marker.write_text('preserve')
            reply=subprocess.run([sys.executable,str(SCRIPT),'--binary',str(binary),'--profile',str(profile),
                '--follow-skin','--task-actions','--all-desktops','--task-thumbnails'],capture_output=True,text=True,timeout=5)
            self.assertEqual(reply.returncode,2);self.assertIn('not --profile',reply.stderr)
            self.assertEqual(marker.read_text(),'preserve')
    def test_session_appearance_cannot_modify_saved_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);binary=root/'unused';binary.write_text('#!/bin/false\n');binary.chmod(0o700)
            profile=root/'profile';profile.mkdir();marker=profile/'unchanged';marker.write_text('preserve')
            reply=subprocess.run([sys.executable,str(SCRIPT),'--binary',str(binary),'--profile',str(profile),
                '--follow-skin','--session-appearance'],capture_output=True,text=True,timeout=5)
            self.assertEqual(reply.returncode,2);self.assertIn('not --profile',reply.stderr)
            self.assertEqual(marker.read_text(),'preserve');self.assertEqual(list(profile.iterdir()),[marker])

    def test_all_desktops_cannot_modify_saved_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);binary=root/'unused';binary.write_text('#!/bin/false\n');binary.chmod(0o700)
            profile=root/'profile';profile.mkdir();marker=profile/'unchanged';marker.write_text('preserve')
            reply=subprocess.run([sys.executable,str(SCRIPT),'--binary',str(binary),'--profile',str(profile),
                '--follow-skin','--task-actions','--all-desktops'],capture_output=True,text=True,timeout=5)
            self.assertEqual(reply.returncode,2);self.assertIn('not --profile',reply.stderr)
            self.assertEqual(marker.read_text(),'preserve');self.assertEqual(list(profile.iterdir()),[marker])

    def test_task_preview_cannot_silently_use_unavailable_desktop_filter(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary=Path(tmp)/'unused';binary.write_text('#!/bin/false\n');binary.chmod(0o700)
            reply=subprocess.run([sys.executable,str(SCRIPT),'--binary',str(binary),'--builtin','org.kde.plasma.taskmanager',
                '--native-panel','--layer-panel','--follow-skin','--task-actions','--output','Fixture output'],
                capture_output=True,text=True,timeout=5)
            self.assertEqual(reply.returncode,2);self.assertIn('requires --all-desktops',reply.stderr)
            self.assertNotIn('Native actions require',reply.stderr)
    def test_task_preview_defaults_to_one_instance_and_comparison_is_explicit(self):
        for requested,expected in (([],"1"),(["--instances","2"],"2")):
            with self.subTest(requested=requested),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);config=root/'config/illogical-impulse';config.mkdir(parents=True)
                (config/'config.json').write_text('{"appearance":{"bwmTheme":"plasma"}}')
                runtime=root/'runtime';runtime.mkdir(mode=0o700)
                observed=root/'observed.json';binary=root/'probe'
                binary.write_text('#!'+sys.executable+'\nimport json,os,sys\nfrom pathlib import Path\n'
                    +'Path('+repr(str(observed))+').write_text(json.dumps({"instances":os.environ["BWM_R4_PREVIEW_INSTANCES"],"args":sys.argv[1:]}))\n'
                    +'raise SystemExit(8)\n');binary.chmod(0o700)
                fake=root/'hyprctl';fake.write_text('#!/bin/sh\nprintf \'[]\'\n');fake.chmod(0o700)
                reply=subprocess.run([sys.executable,str(SCRIPT),'--binary',str(binary),'--builtin','org.kde.plasma.taskmanager',
                    '--native-panel','--layer-panel','--follow-skin','--task-actions','--all-desktops','--output','Fixture output',*requested],
                    env=dict(os.environ,XDG_CONFIG_HOME=str(root/'config'),XDG_RUNTIME_DIR=str(runtime),
                        BWM_R4_PREVIEW_INSTANCES='invalid-inherited',PATH=str(root)+os.pathsep+os.environ.get('PATH','')),
                    capture_output=True,text=True,timeout=5)
                self.assertEqual(reply.returncode,1)
                self.assertEqual(json.loads(observed.read_text()),{'instances':expected,'args':['--follow-panel-preview','org.kde.plasma.taskmanager']})
                self.assertNotIn('Traceback',reply.stderr)

    def test_instance_selection_cannot_change_saved_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);profile=root/'profile';profile.mkdir();marker=profile/'unchanged';marker.write_text('preserve')
            binary=root/'unused';binary.write_text('#!/bin/false\n');binary.chmod(0o700)
            reply=subprocess.run([sys.executable,str(SCRIPT),'--binary',str(binary),'--profile',str(profile),
                '--follow-skin','--native-panel','--instances','1'],capture_output=True,text=True,timeout=5)
            self.assertEqual(reply.returncode,2);self.assertIn('--instances requires a disposable',reply.stderr)
            self.assertEqual(marker.read_text(),'preserve');self.assertEqual(list(profile.iterdir()),[marker])

    def native_provider_preview(self,provider):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);config=root/'config/illogical-impulse';config.mkdir(parents=True)
            (config/'config.json').write_text('{"appearance":{"bwmTheme":"plasma"}}')
            runtime=root/'runtime';runtime.mkdir(mode=0o700)
            binary=root/'unavailable-loader';binary.write_text('#!/does-not-exist-r4-loader\n');binary.chmod(0o700)
            fake=root/'hyprctl';calls=root/'calls'
            fake.write_text('#!'+sys.executable+'\nimport sys\nfrom pathlib import Path\n'
                +'with Path('+repr(str(calls))+').open("a") as f:f.write(sys.argv[-1]+"\\n")\n'
                +'print("[]" if sys.argv[-1]=="monitors" else '+repr(json.dumps(provider))+')\n');fake.chmod(0o700)
            reply=subprocess.run([sys.executable,str(SCRIPT),'--binary',str(binary),'--builtin','org.kde.plasma.showdesktop',
                '--native-panel','--layer-panel','--follow-skin','--native-desktops','--output','Fixture output'],
                env=dict(os.environ,XDG_CONFIG_HOME=str(root/'config'),XDG_RUNTIME_DIR=str(runtime),PATH=str(root)+os.pathsep+os.environ.get('PATH','')),
                capture_output=True,text=True,timeout=5)
            return reply,calls.read_text(),list(runtime.iterdir())

    def test_native_desktops_rejects_missing_disabled_or_old_provider_before_launch(self):
        valid={'version':1,'protocolVersion':4,'barrierProtocolVersion':2,'enabled':True,'providerAvailable':True,'perClientBarrierSupported':True,
               'serverArbitrationVersion':1,'arbitrationState':'active','providerRestartRequired':False,'providerLifecycleVersion':1,'observerStartup':'deferred-event-loop','countMirrorVersion':1,'configuredCountAvailable':True,'activationReadbackVersion':1}
        for provider in ({},dict(valid,version=True),dict(valid,enabled=False),dict(valid,providerAvailable=False),dict(valid,barrierProtocolVersion=0),dict(valid,barrierProtocolVersion=1),dict(valid,perClientBarrierSupported=False),
                         dict(valid,serverArbitrationVersion=0),dict(valid,serverArbitrationVersion=True),dict(valid,arbitrationState='publishing'),dict(valid,arbitrationState='retired'),dict(valid,providerRestartRequired=True),dict(valid,providerRestartRequired=None),
                         dict(valid,providerLifecycleVersion=None),dict(valid,providerLifecycleVersion=0),dict(valid,providerLifecycleVersion=True),dict(valid,observerStartup=None),dict(valid,observerStartup='eager'),dict(valid,countMirrorVersion=None),dict(valid,countMirrorVersion=True),dict(valid,configuredCountAvailable=False),dict(valid,activationReadbackVersion=None),dict(valid,activationReadbackVersion=True),dict(valid,activationReadbackVersion=0)):
            with self.subTest(provider=provider):
                reply,calls,files=self.native_provider_preview(provider)
                self.assertEqual(reply.returncode,2);self.assertIn('barrera por conexión',reply.stderr)
                self.assertNotIn('No se pudo ejecutar',reply.stderr);self.assertNotIn('Traceback',reply.stderr)
                self.assertEqual(calls.splitlines(),['monitors','bwm-plasma-desktops']);self.assertEqual(files,[])

    def test_native_desktop_preflight_only_reads_and_does_not_certify_or_load_plugin(self):
        reply,calls,files=self.native_provider_preview({'version':1,'protocolVersion':4,'barrierProtocolVersion':2,'enabled':True,'providerAvailable':True,'perClientBarrierSupported':True,'operationalVerified':False,
            'serverArbitrationVersion':1,'arbitrationState':'active','providerRestartRequired':False,'providerLifecycleVersion':1,'observerStartup':'deferred-event-loop','countMirrorVersion':1,'configuredCountAvailable':True,'activationReadbackVersion':1})
        self.assertEqual(reply.returncode,2);self.assertIn('No se pudo ejecutar',reply.stderr)
        self.assertNotIn('Traceback',reply.stderr);self.assertEqual(calls.splitlines(),['monitors','bwm-plasma-desktops']);self.assertEqual(files,[])

    def test_missing_or_non_executable_binary_fails_before_skin_or_ipc(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for exists in (False,True):
                binary=root/('non-executable' if exists else 'missing')
                if exists:binary.write_text('not an executable');binary.chmod(0o600)
                with self.subTest(exists=exists):
                    reply=subprocess.run([sys.executable,str(SCRIPT),'--binary',str(binary),
                        '--builtin','org.kde.plasma.showdesktop','--native-panel','--layer-panel',
                        '--follow-skin','--desktop-actions','--output','Fixture output'],
                        env=dict(os.environ,XDG_CONFIG_HOME=str(root)),capture_output=True,text=True,timeout=5)
                    self.assertEqual(reply.returncode,2)
                    self.assertIn('cmake --build',reply.stderr)
                    self.assertIn(str(ROOT/'build/bwm-plasma-host/bwm-plasma-host'),reply.stderr)
                    self.assertNotIn('requires Breeze',reply.stderr)
                    self.assertNotIn('Traceback',reply.stderr)

    def test_unavailable_executable_interpreter_reports_launch_error_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary=Path(tmp)/'broken';binary.write_text('#!/does-not-exist-bwm-r4\n');binary.chmod(0o700)
            reply=subprocess.run([sys.executable,str(SCRIPT),'--binary',str(binary),
                '--builtin','org.kde.plasma.showdesktop'],capture_output=True,text=True,timeout=5)
            self.assertEqual(reply.returncode,2)
            self.assertIn('No se pudo ejecutar el auxiliar',reply.stderr)
            self.assertNotIn('Traceback',reply.stderr)


if __name__=='__main__':unittest.main()
