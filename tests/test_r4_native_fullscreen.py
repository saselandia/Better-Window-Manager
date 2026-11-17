# SPDX-License-Identifier: GPL-2.0-or-later
"""Native full-screen desired states, compositor-side guards and checked receipts."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('r4_fullscreen', ROOT/'config/hypr/skins/plasma/scripts/kwin-window.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class NativeFullscreenTest(unittest.TestCase):
    def setUp(self):
        self.client = {'address': '0xabc', 'pid': 123, 'mapped': True, 'hidden': False,
                       'workspace': {'id': 2, 'name': '2'}, 'tags': []}

    def test_capability_rejects_nonordinary_or_hidden_windows(self):
        self.assertTrue(m.native_fullscreen_allowed(self.client))
        for changes in ({'mapped': False}, {'hidden': True}, {'pinned': True}, {'workspace': None},
                        {'workspace': {'id': -9, 'name': 'special:magic'}},
                        {'workspace': {'id': 99}}, {'workspace': {'id': True}},
                        {'workspace': {'id': '2'}}):
            with self.subTest(changes=changes):
                self.assertFalse(m.native_fullscreen_allowed(dict(self.client, **changes)))

    def test_success_requires_the_exact_receipt_not_only_exit_status(self):
        for stdout, code, success in [('bwm-r4-fullscreen-ok\n', 0, True), ('ok\n', 0, False),
                                     ('bwm-r4-fullscreen-rejected\n', 0, False), ('', 0, False),
                                     ('bwm-r4-fullscreen-ok\n', 1, False),
                                     ('error: failed\nbwm-r4-fullscreen-ok\n', 0, False)]:
            with self.subTest(stdout=stdout, code=code), patch.object(m.subprocess, 'run',
                    return_value=subprocess.CompletedProcess([], code, stdout=stdout)) as run:
                self.assertEqual(m.native_fullscreen(self.client, True), success)
                self.assertEqual(run.call_args.args[0][:2], ['hyprctl', 'repl'])
                self.assertEqual(run.call_args.kwargs['timeout'], 2)
        with patch.object(m.subprocess, 'run') as run:
            self.assertFalse(m.native_fullscreen(dict(self.client, hidden=True), True))
            run.assert_not_called()

    def test_native_entry_rechecks_identity_and_fails_cleanly_on_timeout(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'XDG_RUNTIME_DIR': tmp, 'XDG_CONFIG_HOME': tmp}):
            config = Path(tmp)/'illogical-impulse'
            config.mkdir()
            (config/'config.json').write_text('{"appearance":{"bwmTheme":"plasma"}}')
            args = ['--native-serialized', '--expected-generation', '7', '--pid', '123', 'fullscreen', '--state', 'on', '0xabc']
            with patch.object(m, 'find_client', return_value=self.client), \
                 patch.object(m.bwm_windows, 'process_generation', return_value='stale'), \
                 patch.object(m, 'native_fullscreen') as apply:
                self.assertEqual(m.main(args), 1)
                apply.assert_not_called()
            with patch.object(m, 'find_client', return_value=self.client), \
                 patch.object(m.bwm_windows, 'process_generation', return_value='7'), \
                 patch.object(m.subprocess, 'run', side_effect=subprocess.TimeoutExpired('hyprctl', 2)):
                self.assertEqual(m.main(args), 1)

    def test_native_parser_requires_explicit_state_and_generation(self):
        with patch.object(m, 'execute') as execute:
            for args in (['--native-serialized', '--pid', '123', 'fullscreen', '0xabc'],
                         ['--native-serialized', '--pid', '123', 'fullscreen', '--state', 'on', '0xabc'],
                         ['--native-serialized', '--expected-generation', '7', '--pid', '123', 'fullscreen', '0xabc']):
                with self.subTest(args=args), self.assertRaises(SystemExit):
                    m.main(args)
            execute.assert_not_called()

    def test_daily_fullscreen_keeps_existing_toggle_semantics(self):
        with patch.object(m, 'find_client', return_value=self.client), patch.object(m, 'run_lua') as run:
            self.assertEqual(m.main(['fullscreen', '0xabc']), 0)
            self.assertIn("action = 'toggle'", run.call_args.args[0])
            self.assertIn('w.pid ~= 123', run.call_args.args[0])

    @unittest.skipUnless(shutil.which('lua'), 'Lua interpreter required for actual generated guard execution')
    def test_actual_lua_guards_and_idempotent_setters(self):
        prefix = '''local calls=0
local w={pid=123,mapped=true,hidden=false,workspace={id=2},fullscreen=0}
package.loaded["modules.theme"]={name="plasma"}
local succeeds=true
local unchanged=false
hl={get_window=function() return w end,dsp={window={fullscreen=function(o) return o end}}}
hl.dispatch=function(o)
 assert(o.window==w and o.mode==0)
 calls=calls+1
 if not succeeds then return {ok=false} end
 if unchanged then return {ok=true} end
 assert(o.action=="set" or o.action=="unset")
 w.fullscreen=o.action=="set" and 2 or 0
 return {ok=true}
end
'''
        code = m.native_fullscreen_lua(self.client, True)
        for mutation, receipt, count in [('', 'ok', 1), ('w.pid=456', 'rejected', 0),
                                       ('w.mapped=false', 'rejected', 0), ('w.hidden=true', 'rejected', 0),
                                       ('w.pinned=true', 'rejected', 0),
                                       ('w.workspace=nil', 'rejected', 0), ('w.workspace.id=-9', 'rejected', 0),
                                       ('w.workspace.id=99', 'rejected', 0),
                                       ('w.workspace.name="special:minimized"', 'rejected', 0),
                                       ('package.loaded["modules.theme"].name="retro"', 'rejected', 0),
                                       ('succeeds=false', 'rejected', 1), ('unchanged=true', 'rejected', 1)]:
            with self.subTest(mutation=mutation):
                reply = subprocess.run(['lua', '-'], input=prefix+'\n'+mutation+'\nlocal receipt='+code+'\nprint(receipt)\nprint(calls)',
                                       capture_output=True, text=True, timeout=2)
                self.assertEqual(reply.returncode, 0, reply.stderr)
                self.assertEqual(reply.stdout.splitlines(), ['bwm-r4-fullscreen-'+receipt, str(count)])
        program = prefix+'\nlocal first='+code+'\nlocal second='+code+'\nprint(w.fullscreen)\nlocal third='
        program += m.native_fullscreen_lua(self.client, False)+'\nprint(w.fullscreen)\nprint(calls)'
        reply = subprocess.run(['lua', '-'], input=program, capture_output=True, text=True, timeout=2)
        self.assertEqual(reply.returncode, 0, reply.stderr)
        self.assertEqual(reply.stdout.splitlines(), ['2', '0', '3'])


if __name__ == '__main__':
    unittest.main()
