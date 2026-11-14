"""Skin startup/icon state: isolated files, simulated IPC, native local Qt cache probe."""
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'config/hypr/scripts'))
import bwm_session as session
import bwm_icons as icons
spec=importlib.util.spec_from_file_location('launch_app',ROOT/'config/hypr/scripts/bwm-launch-app.py')
launch_app=importlib.util.module_from_spec(spec);spec.loader.exec_module(launch_app)

class RuntimeTests(unittest.TestCase):
    def test_desktop_launch_keeps_argv_working_directory_and_terminal(self):
        payload={'command':['app','a b','literal;$(not-a-command)'],'workingDirectory':'/tmp/work space'}
        with mock.patch.object(launch_app.bwm_session,'spawn',return_value=True) as spawn:
            self.assertEqual(launch_app.main([json.dumps(payload)]),0)
        self.assertEqual(spawn.call_args.args[0],['env','--chdir','/tmp/work space','app','a b','literal;$(not-a-command)'])
        self.assertFalse(spawn.call_args.kwargs['allow_fallback'])
        payload['terminal']=True
        args=launch_app.command_for(payload)
        self.assertTrue(args[3].endswith('/bwm-terminal'));self.assertEqual(args[4:],['--',*payload['command']])
        for invalid in ({'command':'sh -c injected'},{'command':['']},{'command':['app'],'workingDirectory':[]}):
            with self.assertRaises(ValueError):launch_app.command_for(invalid)

    @unittest.skipUnless(shutil.which('qml6'),'Qt QML runtime unavailable')
    def test_qml_launcher_sends_parsed_desktop_action_without_running_it(self):
        source=(ROOT/'config/quickshell/ii/services/AppSearch.qml').read_text()
        start=source.index('    function launch(');opening=source.index('{',start);depth=1;end=opening+1
        while depth:
            depth += (source[end]=='{')-(source[end]=='}');end+=1
        function=source[start:end]
        code='''import QtQml
QtObject { Component.onCompleted: { try {
const calls=[];
const Quickshell={env: key=>"/fixture",execDetached:args=>calls.push(args)};
FUNCTION
const entry={command:["base-app"],workingDirectory:"/work space",runInTerminal:true};
const action={command:["action-app","literal;$(not-a-command)"]};
if(!launch(entry,action))throw new Error("launch rejected");
const payload=JSON.parse(calls[0][2]);
if(payload.command[0]!=="action-app" || !payload.terminal || payload.workingDirectory!=="/work space")throw new Error("wrong payload");
if(payload.command[1]!=="literal;$(not-a-command)")throw new Error("argv modified");
if(launch(null) || launch({command:[]}))throw new Error("invalid entry accepted");
console.log("launch-payload-passed");Qt.quit();
} catch(error) { console.error(error);Qt.exit(1); } } }
'''.replace('FUNCTION',function)
        with tempfile.TemporaryDirectory(prefix='bwm-launch-qml-') as tmp:
            path=Path(tmp)/'test.qml';path.write_text(code)
            env={**os.environ,'QT_QPA_PLATFORM':'offscreen','QT_QPA_PLATFORMTHEME':'kde',
                 'DBUS_SESSION_BUS_ADDRESS':'unix:path='+tmp+'/no-bus'}
            for suffix,key in (('config','XDG_CONFIG_HOME'),('data','XDG_DATA_HOME'),('cache','XDG_CACHE_HOME'),('runtime','XDG_RUNTIME_DIR'),('defaults','XDG_CONFIG_DIRS')):
                directory=Path(tmp)/suffix;directory.mkdir(mode=0o700);env[key]=str(directory)
            result=subprocess.run(['qml6',str(path)],env=env,capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr);self.assertIn('launch-payload-passed',result.stdout+result.stderr)

    def test_shell_backend_does_not_depend_on_the_caller_skin(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugins=Path(tmp);(plugins/'KDEPlasmaPlatformTheme6.so').touch()
            for backend in ('gtk3','qt6ct','kde'):
                with mock.patch.object(session,'QT_PLATFORM_DIRS',(plugins,)), mock.patch.dict(os.environ,{'QT_QPA_PLATFORMTHEME':backend,'XDG_CONFIG_HOME':tmp,'XDG_CONFIG_DIRS':f'/vendor:{tmp}/kdedefaults:/etc/xdg'}):
                    command=session.shell_command()
                    self.assertIn('QT_QPA_PLATFORMTHEME=kde',command)
                    self.assertIn(f'XDG_CONFIG_DIRS={tmp}/kdedefaults:/vendor:/etc/xdg',command)
                    self.assertEqual(os.environ['QT_QPA_PLATFORMTHEME'],backend)
                    self.assertEqual(command[-4:],['quickshell','-n','-c','ii'])

    def test_shell_fallback_does_not_reuse_gtk_when_qt6ct_is_installed(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugins=Path(tmp);(plugins/'libqt6ct.so').touch()
            with mock.patch.object(session,'QT_PLATFORM_DIRS',(plugins,)):
                self.assertIn('QT_QPA_PLATFORMTHEME=qt6ct',session.shell_command())

    def test_activation_export_uses_hyprland_and_never_the_stale_caller_fallback(self):
        with mock.patch.object(session.subprocess,'run',return_value=mock.Mock(returncode=0,stdout='ok\n')) as run:
            self.assertTrue(session.sync_activation_environment())
        self.assertIn('dbus-update-activation-environment --systemd QT_QPA_PLATFORMTHEME XDG_CONFIG_DIRS',run.call_args.args[0][2])
        with mock.patch.object(session.subprocess,'run',return_value=mock.Mock(returncode=1,stdout='')), mock.patch.object(session.subprocess,'Popen') as popen:
            self.assertFalse(session.sync_activation_environment())
            popen.assert_not_called()

    def test_gtk_file_fallback_preserves_unknown_keys_and_groups(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(icons,'HOME',Path(tmp)):
            original='; comment\n[Settings]\ngtk-font-name=Custom 11\ngtk-icon-theme-name=Adwaita\nvendor-key=keep\n[Other]\ngtk-icon-theme-name=private\n'
            for version in ('gtk-3.0','gtk-4.0'):
                path=Path(tmp)/'.config'/version/'settings.ini';path.parent.mkdir(parents=True);path.write_text(original)
            for theme in ('breeze-dark','ThirdPartyCustom','BWM-Papirus','Adwaita'):
                icons.write_gtk_icons(theme)
                for version in ('gtk-3.0','gtk-4.0'):
                    path=Path(tmp)/'.config'/version/'settings.ini'
                    text=path.read_text()
                    self.assertIn('gtk-icon-theme-name='+theme+'\n',text)
                    self.assertIn('gtk-font-name=Custom 11',text)
                    self.assertIn('vendor-key=keep',text)
                    self.assertIn('[Other]\ngtk-icon-theme-name=private',text)
                    before=path.stat().st_mtime_ns;icons.write_gtk_icons(theme)
                    self.assertEqual(path.stat().st_mtime_ns,before)

    def test_stale_skin_jobs_are_rejected_before_committing_icons(self):
        for sequence in (['plasma'],['retro','plasma']):
            with mock.patch.object(icons,'_active_skin',side_effect=sequence), mock.patch.object(icons,'_current_icons',return_value='BreezeCustom'), mock.patch.object(icons,'icon_theme_for',return_value='BWM-Papirus'), mock.patch.object(icons.subprocess,'run') as run:
                self.assertEqual(icons.apply('retro'),'BreezeCustom');run.assert_not_called()

    def test_breeze_icon_choice_uses_theme_defaults_and_keeps_user_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);config=root/'config';defaults=config/'kdedefaults';defaults.mkdir(parents=True)
            (defaults/'kdeglobals').write_text('[Icons]\nTheme=GlobalThemeCustom\n')
            user=config/'kdeglobals';user.write_text('[General]\nColorScheme=Custom\n')
            with mock.patch.object(icons,'KDEGLOBALS',user), mock.patch.dict(os.environ,{'XDG_CONFIG_DIRS':str(root/'system')}):
                self.assertEqual(icons._plasma_icons(),'GlobalThemeCustom')
                user.write_text('[Icons]\nTheme=UserCustom\n')
                self.assertEqual(icons._plasma_icons(),'UserCustom')

    def test_native_notifications_cover_palette_fonts_style_and_all_icon_groups(self):
        with mock.patch.object(icons.subprocess,'run') as run:
            icons.notify_appearance()
        calls=[call.args[0] for call in run.call_args_list]
        self.assertEqual([c[-2:] for c in calls[:3]],[['int32:0','int32:0'],['int32:1','int32:0'],['int32:2','int32:0']])
        self.assertEqual([c[-1] for c in calls[3:]],[f'int32:{group}' for group in range(6)])

    def test_missing_gtk_settings_section_is_added_without_discarding_existing_data(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(icons,'HOME',Path(tmp)):
            path=Path(tmp)/'.config/gtk-3.0/settings.ini';path.parent.mkdir(parents=True)
            path.write_text('# keep\n[Vendor]\nkey=value')
            icons.write_gtk_icons('BreezeCustom')
            self.assertEqual(path.read_text(),'# keep\n[Vendor]\nkey=value\n[Settings]\ngtk-icon-theme-name=BreezeCustom\n')
            self.assertEqual((Path(tmp)/'.config/gtk-4.0/settings.ini').read_text(),'[Settings]\ngtk-icon-theme-name=BreezeCustom\n')

    def test_icon_and_qt_notices_follow_both_file_writes(self):
        order=[]
        with mock.patch.object(icons,'_active_skin',return_value='plasma'), mock.patch.object(icons,'icon_theme_for',return_value='UserCustom'), mock.patch.object(icons,'_rebuilt',False), mock.patch.object(icons,'write_gtk_icons',side_effect=lambda value:order.append('gtk:'+value)), mock.patch.object(icons,'write_qt6ct',side_effect=lambda *args:order.append('qt')), mock.patch.object(icons,'write_kdeglobals',side_effect=lambda:order.append('kde')), mock.patch.object(icons,'notify_appearance',side_effect=lambda:order.append('notify')), mock.patch.object(icons.subprocess,'run'):
            self.assertEqual(icons.apply('plasma'),'UserCustom')
        self.assertEqual(order,['gtk:UserCustom','qt','kde','notify'])

@unittest.skipUnless(shutil.which('pkg-config'),'native Qt build tools missing')
class NativeIconTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not any((base/'KDEPlasmaPlatformTheme6.so').is_file() for base in session.QT_PLATFORM_DIRS):
            raise unittest.SkipTest('KDE Qt platform plugin not installed')
        if not Path('/usr/include/KF6/KIconThemes/KIconLoader').exists():
            raise unittest.SkipTest('KIconThemes development headers missing')
        cls.tmp=tempfile.TemporaryDirectory(prefix='bwm-qt-icon-proof-');cls.root=Path(cls.tmp.name)
        pkg=subprocess.run(['pkg-config','--cflags','--libs','Qt6Widgets'],capture_output=True,text=True)
        if pkg.returncode:raise unittest.SkipTest('Qt Widgets development files missing')
        cls.binary=cls.root/'probe'
        command=[os.environ.get('CXX','g++'),'-std=c++20','-fPIC',str(ROOT/'tests/qt_skin_icon_probe.cpp'),'-o',str(cls.binary),
                 '-I/usr/include/KF6/KIconThemes','-I/usr/include/KF6/KConfigCore','-I/usr/include/KF6/KConfig',*shlex.split(pkg.stdout),'-lKF6IconThemes','-lKF6ConfigCore']
        build=subprocess.run(command,capture_output=True,text=True,timeout=90)
        if build.returncode:raise AssertionError(build.stderr)

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def test_one_process_retro_breeze_roundtrip_and_custom_theme(self):
        reports={}
        # GTK's platform plugin requires a real display even with Qt offscreen.
        # Session display/private D-Bus access is blocked here: test the KDE renderer
        # locally and do not claim a live transport or GTK comparison was verified.
        for backend in ('kde',):
            root=self.root/backend
            for name in ('config','data','cache','runtime','defaults'):(root/name).mkdir(parents=True,mode=0o700)
            env={**os.environ,'QT_QPA_PLATFORM':'offscreen','QT_QPA_PLATFORMTHEME':backend,'QT_QUICK_BACKEND':'software',
                 'XDG_CONFIG_HOME':str(root/'config'),'XDG_DATA_HOME':str(root/'data'),'XDG_CACHE_HOME':str(root/'cache'),
                 'XDG_RUNTIME_DIR':str(root/'runtime'),'XDG_CONFIG_DIRS':str(root/'defaults'),'XDG_DATA_DIRS':'/usr/local/share:/usr/share',
                 'GSETTINGS_BACKEND':'keyfile','NO_AT_BRIDGE':'1','GTK_A11Y':'none','QT_USE_PORTAL':'0'}
            env['DBUS_SESSION_BUS_ADDRESS']='unix:path='+str(root/'no-bus')
            result=subprocess.run([str(self.binary),'--local-refresh'],env=env,capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr)
            reports[backend]=json.loads(result.stdout)
        expected=['#c44234','#c44234','#3478c4','#c44234','#7b34c4']
        self.assertEqual([s['fresh'] for s in reports['kde']['snapshots']],expected)
        self.assertEqual([s['retained'] for s in reports['kde']['snapshots']],expected)
        self.assertFalse(reports['kde']['explicitIconThemeOverride'])
        if os.environ.get('BWM_SKIN_RUNTIME_REPORT'):
            Path(os.environ['BWM_SKIN_RUNTIME_REPORT']).write_text(json.dumps(reports,indent=2)+'\n')

if __name__=='__main__':unittest.main()
