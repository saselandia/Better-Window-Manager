"""R4 hook publication stays in explicitly registered private preview files."""
import ast
import builtins
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('r4_panel_session',ROOT/'config/hypr/skins/plasma/scripts/panel-session.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
sys.path.insert(0,str(ROOT/'config/hypr/scripts'))
import bwm_settings_hooks as hooks
import bwm_skins


class PanelSessionTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='bwm-r4-session-test-');self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.runtime=self.root/'runtime';self.runtime.mkdir(mode=0o700)
        patch=mock.patch.dict(os.environ,{'XDG_RUNTIME_DIR':str(self.runtime)});patch.start();self.addCleanup(patch.stop)
        self.control=self.root/'control';self.control.mkdir(mode=0o700);self.token='a'*64
        self.write('control.json',{'version':1,'token':self.token,'revision':0,'command':'skin','skin':'default'})
        self.write('ack.json',{'version':1,'token':self.token,'revision':0,'ok':True,'command':'skin','skin':'default'})

    def write(self,name,value):m.atomic_json(self.control/name,value)
    def register(self):m.register(self.control,os.getpid(),self.token);return m.active_registration()

    def test_no_registration_is_noop_and_does_not_create_runtime_files(self):
        self.assertEqual(m.event('before','plasma','retro'),{'status':'inactive'})
        self.assertEqual(m.event('after','retro','plasma'),{'status':'inactive'})
        self.assertEqual(list(self.runtime.iterdir()),[])

    def test_register_requires_matching_ack_and_preserves_an_existing_session(self):
        self.write('ack.json',{'token':'b'*64,'ok':True})
        with self.assertRaises(ValueError):self.register()
        self.write('ack.json',{'version':1,'token':self.token,'ok':True,'command':'skin'})
        registration=self.register();self.assertEqual(registration['processStart'],m.process_start(os.getpid()))
        before=(m.registry_directory()/'active.json').read_bytes()
        with self.assertRaises(ValueError):self.register()
        self.assertEqual((m.registry_directory()/'active.json').read_bytes(),before)

    def test_dead_or_reused_pid_registration_is_ignored_without_writing_control(self):
        registration=self.register();before=(self.control/'control.json').read_bytes()
        registration['processStart']='stale'
        m.atomic_json(m.registry_directory()/'active.json',registration)
        self.assertEqual(m.event('after','retro','plasma'),{'status':'inactive'})
        self.assertEqual((self.control/'control.json').read_bytes(),before)

    def test_unregister_requires_current_token(self):
        self.register();path=m.registry_directory()/'active.json';before=path.read_bytes()
        m.unregister('b'*64);self.assertEqual(path.read_bytes(),before)
        m.unregister(self.token);self.assertFalse(path.exists())

    def test_before_only_withdraws_when_leaving_plasma_and_custom_skin_maps_inactive(self):
        registration=self.register()
        with mock.patch.object(m,'command',return_value={'status':'acknowledged'}) as send:
            self.assertEqual(m.event('before','retro','plasma'),{'status':'not-needed'});send.assert_not_called()
            m.event('before','plasma','retro');send.assert_called_once_with(registration,'skin','retro')
            send.reset_mock();m.event('after','retro','plasma');send.assert_called_once_with(registration,'skin','plasma')
            send.reset_mock();m.event('before','plasma','third-party');send.assert_called_once_with(registration,'skin','default')

    def test_control_with_wrong_token_or_non_integer_revision_is_not_replaced(self):
        registration=self.register()
        for bad in ({'version':1,'token':'b'*64,'revision':0},{'version':1,'token':self.token,'revision':True},{'version':1,'token':self.token,'revision':2**53}):
            self.write('control.json',bad);before=(self.control/'control.json').read_bytes()
            with self.assertRaises(ValueError):m.command(registration,'skin','plasma',timeout=.01)
            self.assertEqual((self.control/'control.json').read_bytes(),before)

    def test_busy_transaction_does_not_write(self):
        registration=self.register();before=(self.control/'control.json').read_bytes()
        with m.locked(self.control/'transaction.lock'):
            with self.assertRaises(BlockingIOError):m.command(registration,'skin','plasma',timeout=.01)
        self.assertEqual((self.control/'control.json').read_bytes(),before)

    def test_missing_ack_is_reported_not_assumed_applied(self):
        registration=self.register()
        with self.assertRaises(TimeoutError):m.command(registration,'skin','plasma',timeout=.02)
        control=m.read_json(self.control/'control.json')
        self.assertEqual((control['revision'],control['skin']),(1,'plasma'))
        self.assertEqual(m.read_json(self.control/'ack.json')['revision'],0)

    def test_status_without_registration_does_not_create_files(self):
        self.assertEqual(m.status(),{'active':False})
        self.assertEqual(list(self.runtime.iterdir()),[])

    def test_status_requires_a_new_ack_even_with_a_live_pid(self):
        registration=self.register()
        with self.assertRaises(TimeoutError):m.command(registration,'status',timeout=.02)
        self.assertEqual(m.read_json(self.control/'control.json')['command'],'status')
        self.assertEqual(m.read_json(self.control/'ack.json')['revision'],0)

    def status_response(self, runtime):
        original=m.atomic_json
        def respond(path,value):
            original(path,value)
            if path.name=='control.json':
                original(self.control/'ack.json',{'version':1,'token':self.token,'revision':value['revision'],
                         'ok':True,'command':'status','skin':'plasma','runtime':runtime})
        return mock.patch.object(m,'atomic_json',side_effect=respond)

    def test_status_uses_current_skin_and_returns_native_runtime_without_skin_change(self):
        self.register()
        runtime={'version':1,'scope':'isolated-preview','skin':'plasma','renderReady':True,
                 'replacementReady':False,'panels':[{'containmentId':7,'renderReady':True}],
                 'blockers':['isolated-preview-only','reserved-area-unavailable']}
        with self.status_response(runtime):result=m.status()
        self.assertEqual(result,{'active':True,'status':'acknowledged','revision':1,'skin':'plasma','runtime':runtime})
        self.assertEqual(m.read_json(self.control/'control.json')['command'],'status')

    def test_status_rejects_missing_incompatible_or_production_readiness(self):
        registration=self.register()
        valid={'version':1,'scope':'isolated-preview','skin':'plasma','renderReady':False,
               'replacementReady':False,'panels':[],'blockers':[]}
        for runtime in (None,{},dict(valid,version=2),dict(valid,skin='retro'),dict(valid,scope='production'),
                        dict(valid,replacementReady=True),dict(valid,renderReady='true'),dict(valid,panels={})):
            with self.subTest(runtime=runtime),self.status_response(runtime):
                with self.assertRaisesRegex(ValueError,'compatible'):m.command(registration,'status',timeout=.02)

    def test_drain_waits_for_stop_reader_without_removing_ack(self):
        before=(self.control/'ack.json').read_bytes()
        with m.locked(self.control/'transaction.lock'):
            with self.assertRaises(TimeoutError):m.drain(self.control,timeout=.01)
        self.assertEqual((self.control/'ack.json').read_bytes(),before)
        m.drain(self.control)

    def test_non_private_directory_is_rejected_without_permission_changes(self):
        self.control.chmod(0o755)
        with self.assertRaises(ValueError):self.register()
        self.assertEqual(self.control.stat().st_mode & 0o777,0o755)

    def test_symlink_control_is_rejected(self):
        registration=self.register();control=self.control/'control.json';target=self.root/'unrelated.json'
        target.write_bytes(control.read_bytes());control.unlink();control.symlink_to(target)
        before=target.read_bytes()
        with self.assertRaises(ValueError):m.command(registration,'skin','plasma',timeout=.01)
        self.assertEqual(target.read_bytes(),before)

    def test_symlink_registration_directory_is_not_followed(self):
        target=self.root/'unrelated';target.mkdir(mode=0o700)
        (target/'keep').write_text('unchanged');m.registry_directory().symlink_to(target,target_is_directory=True)
        with self.assertRaises(ValueError):m.active_registration()
        self.assertEqual((target/'keep').read_text(),'unchanged')

    def test_process_identity_rejects_zombie_and_non_pid_values(self):
        with mock.patch.object(Path,'read_text',return_value='123 (test ) name) Z '+' '.join(['0']*18+['123456'])):
            self.assertIsNone(m.process_start(123))
        self.assertIsNone(m.process_start(True));self.assertIsNone(m.process_start(-1))

    def test_common_hooks_confine_script_and_notify_each_involved_skin_once(self):
        skin={'dir':str(self.root),'hooks':{'skinChanged':'panel.py'}}
        with mock.patch.object(bwm_skins,'skin',return_value=skin),mock.patch.object(hooks.subprocess,'run',return_value=mock.Mock(returncode=0)) as run:
            self.assertTrue(hooks.skin_changed('after','plasma','plasma'));self.assertEqual(run.call_count,1)
            self.assertEqual(run.call_args.args[0][-4:],['event','after','plasma','plasma'])
        skin['hooks']['skinChanged']='../escape.py'
        with mock.patch.object(bwm_skins,'skin',return_value=skin),mock.patch.object(hooks.subprocess,'run') as run:
            self.assertFalse(hooks.skin_changed('before','plasma','retro'));run.assert_not_called()

    def test_common_hook_failure_propagates_to_before_phase(self):
        skin={'dir':str(self.root),'hooks':{'skinChanged':'panel.py'}}
        with mock.patch.object(bwm_skins,'skin',return_value=skin),mock.patch.object(hooks.subprocess,'run',return_value=mock.Mock(returncode=1,stderr='unacknowledged')):
            self.assertFalse(hooks.skin_changed('before','plasma','retro'))

    def test_manager_aborts_and_restores_companion_before_profile_mutations(self):
        source=ROOT/'config/hypr/scripts/bwm-theme-manager.py'
        node=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='apply_theme')
        profiles=mock.Mock()
        context={'THEMES':{'retro':{}},'get_current_theme':lambda:'plasma',
                 'save_current_theme_config':profiles,'open':lambda *args,**kwargs:builtins.open(self.root/'manager.lock','w')}
        exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),context)
        with mock.patch.object(hooks,'skin_changed',side_effect=[False,True]) as notify:
            with self.assertRaisesRegex(RuntimeError,'no se han cambiado los perfiles'):
                context['apply_theme']('retro')
        profiles.assert_not_called()
        self.assertEqual(notify.call_args_list,[mock.call('before','plasma','retro'),mock.call('after','plasma','plasma')])


if __name__=='__main__':unittest.main()
