# SPDX-License-Identifier: GPL-2.0-or-later
"""Caller environment and serialized native application-start handoff."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SKIN=ROOT/'config/hypr/skins/plasma/scripts'
spec=importlib.util.spec_from_file_location('r4_launch_tasks',SKIN/'native-tasks.py')
tasks=importlib.util.module_from_spec(spec);spec.loader.exec_module(tasks)
context=tasks.launch_context


class LaunchContextTest(unittest.TestCase):
    def test_only_selected_caller_values_are_restored_and_host_flags_do_not_escape(self):
        caller={'XDG_CONFIG_HOME':'/own/config','DBUS_SESSION_BUS_ADDRESS':'unix:path=/own/bus','QT_QPA_PLATFORM':'offscreen'}
        host={'XDG_CONFIG_HOME':'/temporary','XDG_DATA_DIRS':'/temporary/data','QT_PLUGIN_PATH':'/temporary/plugins',
              'QT_QPA_PLATFORMTHEME':'host-theme','BWM_R4_TASK_ACTIONS':'1','BWM_R4_OUTPUT':'private',
              'BWM_SKIN_SWITCH':'1','WAYLAND_SOCKET':'123','PATH':'/own/bin',context.VARIABLE:context.capture(caller)}
        restored=context.restore(host)
        self.assertEqual(restored,{**caller,'PATH':'/own/bin'})
        self.assertEqual(host['XDG_CONFIG_HOME'],'/temporary')

    def test_absent_partial_oversized_or_wrong_type_context_fails(self):
        valid=json.loads(context.capture({}))
        for payload in ('','null','[]','x'*131073,json.dumps({'version':True,'values':valid['values']}),
                        json.dumps({'version':1,'values':{}}),
                        json.dumps({'version':1,'values':dict(valid['values'],XDG_CONFIG_HOME=True)}),
                        json.dumps({'version':1,'values':dict(valid['values'],XDG_CONFIG_HOME='bad\0value')})):
            with self.subTest(payload=payload[:80]),self.assertRaises(ValueError):context.restore({context.VARIABLE:payload})


class NativeLaunchActionTest(unittest.TestCase):
    def test_serialized_revalidation_precedes_original_session_handoff(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);root.chmod(0o700);config=root/'illogical-impulse';config.mkdir()
            (config/'config.json').write_text('{"appearance":{"bwmTheme":"plasma"}}')
            binary=root/'host';binary.write_text('#!/bin/false\n');binary.chmod(0o700)
            environment=dict(os.environ,XDG_RUNTIME_DIR=str(root),XDG_CONFIG_HOME=str(root),BWM_R4_TASK_ACTIONS='1')
            original=dict(environment,XDG_DATA_HOME=str(root/'caller-data'),DBUS_SESSION_BUS_ADDRESS='unix:path=/caller-bus')
            environment[context.VARIABLE]=context.capture(original)
            client={'address':'0xabc','pid':123,'class':'own.app','mapped':True,'workspace':{'id':1,'name':'1'},'tags':[]}
            request={'version':1,'action':'new-instance','address':'0xabc','pid':123,'generation':'1'}
            success=json.dumps({'version':1,'accepted':True,'launchHandedOff':True})
            with patch.dict(os.environ,environment,clear=True),patch.object(tasks,'query',return_value=[client]) as query, \
                 patch.object(tasks.bwm_windows,'process_generation',return_value='1'), \
                 patch.object(tasks.subprocess,'run',return_value=subprocess.CompletedProcess([],0,stdout=success)) as run:
                self.assertEqual(tasks.action(request,binary),{'version':1,'accepted':True})
                query.assert_called_once_with('clients')
                self.assertEqual(run.call_args.args[0],[binary,'--launch-task-application'])
                sent=json.loads(run.call_args.kwargs['input']);self.assertEqual(sent,{'version':1,'action':'new-instance','appId':'own.app','pid':123,'urls':[]})
                self.assertEqual(run.call_args.kwargs['env']['XDG_DATA_HOME'],str(root/'caller-data'))
                self.assertTrue(run.call_args.kwargs['start_new_session'])
                self.assertFalse(any(key.startswith('BWM_R4_') for key in run.call_args.kwargs['env']))
                run.reset_mock()
                with self.assertRaisesRegex(ValueError,'identity changed'):tasks.action(dict(request,generation='stale'),binary)
                run.assert_not_called()
                for urls in ([],[True],['relative\0file'],['x'*4097],['x']*129):
                    with self.subTest(urls=str(urls)[:60]),self.assertRaises(ValueError):tasks.action(dict(request,action='open-urls',urls=urls),binary)
                run.assert_not_called()
                for reply in ('{}','null',json.dumps({'version':True,'accepted':True,'launchHandedOff':True}),
                              json.dumps({'version':1,'accepted':True}),json.dumps({'version':1,'accepted':False,'launchHandedOff':True})):
                    run.return_value=subprocess.CompletedProcess([],0,stdout=reply)
                    with self.subTest(reply=reply),self.assertRaises(ValueError):tasks.action(request,binary)
                (config/'config.json').write_text('{"appearance":{"bwmTheme":"retro"}}');run.reset_mock();query.reset_mock()
                with self.assertRaisesRegex(ValueError,'Breeze'):tasks.action(request,binary)
                run.assert_not_called();query.assert_not_called()

    def test_pinned_launcher_and_service_action_hand_off_without_window_query(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);root.chmod(0o700);config=root/'illogical-impulse';config.mkdir()
            (config/'config.json').write_text('{"appearance":{"bwmTheme":"plasma"}}')
            binary=root/'host';binary.write_text('#!/bin/false\n');binary.chmod(0o700)
            environment=dict(os.environ,XDG_RUNTIME_DIR=str(root),XDG_CONFIG_HOME=str(root),BWM_R4_TASK_ACTIONS='1')
            environment[context.VARIABLE]=context.capture(dict(environment,DBUS_SESSION_BUS_ADDRESS='unix:path=/caller-bus'))
            success=json.dumps({'version':1,'accepted':True,'launchHandedOff':True})
            launcher={'version':1,'action':'launcher','launcherUrl':'applications:own.app.desktop','urls':['file:///tmp/a%20b']}
            service={'version':1,'action':'service-action','launcherUrl':'file:///own/own.app.desktop','serviceAction':'new-private'}
            with patch.dict(os.environ,environment,clear=True),patch.object(tasks,'query') as query, \
                 patch.object(tasks.subprocess,'run',return_value=subprocess.CompletedProcess([],0,stdout=success)) as run:
                for request in (launcher,dict(launcher,urls=[]),service,dict(launcher,launcherUrl='preferred://browser')):
                    run.reset_mock()
                    self.assertEqual(tasks.action(request,binary),{'version':1,'accepted':True})
                    self.assertEqual(json.loads(run.call_args.kwargs['input']),request)
                    self.assertEqual(run.call_args.kwargs['env']['DBUS_SESSION_BUS_ADDRESS'],'unix:path=/caller-bus')
                    self.assertTrue(run.call_args.kwargs['start_new_session'])
                query.assert_not_called() # No window identity to revalidate.
                run.reset_mock()
                for bad in (dict(launcher,launcherUrl='https://example.invalid/'),dict(launcher,launcherUrl=''),
                            dict(launcher,launcherUrl='applications:x\0'),dict(launcher,urls=[True]),dict(launcher,pid=1),
                            dict(service,serviceAction='../x'),dict(service,serviceAction=''),dict(service,urls=[]),
                            dict(service,serviceAction='a'*257)):
                    with self.subTest(bad=str(bad)[:80]),self.assertRaises(ValueError):tasks.action(bad,binary)
                run.assert_not_called()
                (config/'config.json').write_text('{"appearance":{"bwmTheme":"default"}}')
                with self.assertRaisesRegex(ValueError,'Breeze'):tasks.action(launcher,binary)
                run.assert_not_called()


class HostLaunchPolicyTest(unittest.TestCase):
    def test_policy_is_immutable_exclusive_and_never_follows_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)/'defaults';root.mkdir(mode=0o700)
            context.write_host_policy(root)
            text=(root/'kdeglobals').read_text()
            self.assertIn('[KDE Action Restrictions][$i]\nrun_desktop_files=false\nshell_access=false\n',text)
            self.assertEqual((root/'kdeglobals').stat().st_mode&0o777,0o600)
            with self.assertRaises(ValueError):context.write_host_policy(root) # Never overwrite.
            linked=Path(temporary)/'linked';linked.symlink_to(root)
            with self.assertRaises(ValueError):context.write_host_policy(linked)
            with self.assertRaises(ValueError):context.write_host_policy('relative')

if __name__=='__main__':unittest.main()
