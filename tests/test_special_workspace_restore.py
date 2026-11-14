"""R1: normal dock policy, special origins, identity and the actual QML entry point."""
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

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'config/hypr/scripts'
sys.path.insert(0, str(SCRIPTS))


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


tm = load('restore_test_minimizer', 'toggle-minimize.py')
cli = load('restore_test_focus', 'bwm-focus.py')


class RestorePolicyTest(unittest.TestCase):
    def code(self, origin, current=False):
        tag = (tm.SPECIAL_TAG_PREFIX + origin.encode().hex() if isinstance(origin, str)
               else tm.TAG_PREFIX + str(origin))
        client = {'address': '0x123', 'pid': 17, 'floating': True,
                  'workspace': {'id': -98, 'name': tm.MINIMIZED_WS}, 'tags': [tag]}
        geometry = {'0x123': {'pid': 17, 'generation': '', 'at': [30, 40], 'size': [600, 400]}}
        with mock.patch.object(tm, 'load_geometries', return_value=geometry), mock.patch.object(tm, 'save_geometries'), mock.patch.object(tm.bwm_windows, 'process_generation', return_value=''), mock.patch.object(tm, 'run_lua') as run:
            tm.restore_win(client, on_current_workspace=current)
        return run.call_args.args[0]

    def execute(self, origin, current=False, pid=17, replacement_pid=None):
        if not shutil.which('lua'):
            self.skipTest('lua needed for generated transaction')
        prelude = '''
local w = {pid=PID, workspace={id=-98,name="special:minimized"}}
local callbacks = {}
hl = {dsp={window={},cursor={}}, get_window=function() return w end,
      get_cursor_pos=function() return nil end,
      get_active_workspace=function() return {id=8,name="8"} end,
      timer=function(fn) table.insert(callbacks,fn) end}
local function action(kind,args) args.kind=kind; return args end
for _,name in ipairs({"move","resize","tag","set_prop","bring_to_top","alter_zorder"}) do
 hl.dsp.window[name]=function(args) return action(name,args) end
end
hl.dsp.focus=function(args) return action("focus",args) end
hl.dsp.no_op=function() return {} end
local events={}
hl.dispatch=function(a)
 if a.kind=="move" and a.workspace then
  if type(a.workspace)=="string" then w.workspace={id=-97,name=a.workspace}
  else w.workspace={id=a.workspace,name=tostring(a.workspace)} end
  table.insert(events,"move:"..tostring(a.workspace))
 elseif a.kind=="resize" then table.insert(events,"geometry")
 elseif a.kind=="focus" and a.workspace then table.insert(events,"show:"..a.workspace)
 elseif a.kind=="focus" then table.insert(events,"focus")
 elseif a.kind=="set_prop" then table.insert(events,"animation:"..a.value)
 end
end
'''.replace('PID', str(pid))
        program = prelude + self.code(origin, current) + ';\n'
        if replacement_pid is not None:
            program += 'w.pid=' + str(replacement_pid) + '\n'
        program += 'for _,fn in ipairs(callbacks) do fn() end\nprint(table.concat(events,","))'
        result = subprocess.run(['lua', '-'], input=program, text=True, capture_output=True, check=True)
        return result.stdout.strip()

    def test_common_restore_returns_normal_origin_and_geometry(self):
        self.assertEqual(self.execute(3), 'move:3,geometry,focus')

    def test_retro_normal_restore_uses_current_workspace_without_old_geometry(self):
        self.assertEqual(self.execute(3, current=True), 'animation:1,move:8,focus,animation:unset')

    def test_retro_special_restore_preserves_origin_and_geometry(self):
        self.assertEqual(self.execute('special:magic', current=True),
                         'move:special:magic,geometry,show:special:magic,focus')

    def test_unnamed_and_other_specials_are_not_renamed_to_magic(self):
        for name in ('special', 'special:other'):
            self.assertIn('move:' + name, self.execute(name, current=True))

    def test_stale_pid_blocks_the_entire_transaction(self):
        self.assertEqual(self.execute('special:magic', current=True, pid=99), '')

    def test_delayed_animation_cleanup_rechecks_pid(self):
        self.assertEqual(self.execute(3, current=True, replacement_pid=99), 'animation:1,move:8,focus')

    def test_cli_delegates_dock_policy(self):
        client = {'address': '0x123', 'pid': 17, 'workspace': {'name': tm.MINIMIZED_WS}}
        with mock.patch.object(cli.bwm_windows, 'hypr_json', return_value=[client]), mock.patch.object(cli, 'load_minimizer', return_value=tm), mock.patch.object(tm, 'restore_win') as restore:
            self.assertEqual(cli.main(['0x123', '--pid', '17', '--restore-on-current']), 0)
            restore.assert_called_once_with(client, on_current_workspace=True)

    def test_unreadable_ipc_payload_is_rejected_without_activating(self):
        for value in (None, {}, ['bad'], []):
            with mock.patch.object(cli.bwm_windows, 'hypr_json', return_value=value), mock.patch.object(cli, 'load_minimizer') as load:
                self.assertEqual(cli.main(['0x123', '--pid', '17']), 1)
                load.assert_not_called()

    def test_closed_explicit_target_never_falls_back_to_active_window(self):
        active = {'address': '0x999', 'pid': 99}
        for action in ('min', 'toggle'):
            with mock.patch.object(tm.sys, 'argv', ['toggle-minimize.py', action, '0x123']), mock.patch.object(tm, 'get_clients', return_value=[active]), mock.patch.object(tm, 'get_active_window', return_value=active), mock.patch.object(tm, 'minimize_win') as minimize, mock.patch.object(tm, 'toggle_win') as toggle:
                tm.main()
                minimize.assert_not_called()
                toggle.assert_not_called()

    def test_retro_qml_dispatches_pid_and_policy_without_shell(self):
        runner = Path('/usr/lib64/qt6/bin/qmltestrunner')
        if not runner.is_file():
            self.skipTest('qmltestrunner needed for dock action')
        source = (ROOT / 'config/quickshell/ii/modules/ii/omarchyDock/Dock.qml').read_text()
        method = source[source.index('  function bringForward('):source.index('  function quit(')]
        method = method.replace('Quickshell.execDetached', 'root.execDetached')
        fixture = '''import QtQuick
import QtTest
TestCase {
 id: root
 name: "RetroDockIdentity"
 property var command: null
 function execDetached(args) { command=args; }
 METHOD
 function test_entry() {
  bringForward({address:"123",pid:17,minimized:true});
  compare(command.join("|"),"python3|/home/sasel/.config/hypr/scripts/bwm-focus.py|0x123|--pid|17|--restore-on-current");
  command=null;
  bringForward({address:"123",pid:0,minimized:true});
  compare(command,null);
 }
}'''.replace('METHOD', method)
        with tempfile.TemporaryDirectory(prefix='bwm-r1-retro-') as temp:
            path = Path(temp) / 'tst_dock.qml'
            path.write_text(fixture)
            result = subprocess.run([str(runner), '-input', str(path)],
                env=dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software'),
                capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
