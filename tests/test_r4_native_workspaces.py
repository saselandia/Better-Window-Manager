# SPDX-License-Identifier: GPL-2.0-or-later
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('r4_native_workspaces',ROOT/'config/hypr/skins/plasma/scripts/native_workspaces.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class SharedCountTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.plugin=self.root/'hypr/plugins/bwm-plasma-desktops.so'
        self.time=0
        self.bridge=SimpleNamespace(CONFIG=self.root,effective_options=Mock(return_value={'bar':{'workspaces':{'shown':7}}}),run=Mock(side_effect=self.reply))
        self.runtime=m.Runtime(self.bridge,clock=lambda:self.time)

    def installed(self):
        self.plugin.parent.mkdir(parents=True);self.plugin.touch()

    def reply(self,argv,**kwargs):
        return subprocess.CompletedProcess(argv,0,json.dumps({'version':1,'accepted':True,'configuredCount':int(argv[-1]),'revision':1}),'')

    def test_uninstalled_module_has_no_ipc_or_new_files(self):
        self.assertFalse(self.runtime.tick());self.bridge.run.assert_not_called();self.bridge.effective_options.assert_not_called()
        self.assertEqual(list(self.root.iterdir()),[])

    def test_uses_effective_common_preferences_without_writing_or_reloading(self):
        self.installed();raw=self.root/'config.json';raw.write_text('{"bar":{"workspaces":{"shown":3}},"foreign":"keep"}')
        before={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertTrue(self.runtime.tick())
        self.bridge.run.assert_called_once_with(['hyprctl','bwm-plasma-desktops-count','7'],timeout=2)
        self.assertEqual(before,{p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_default_matches_common_model_and_invalid_values_never_reach_ipc(self):
        self.assertEqual(m.configured_count({}),10)
        self.installed()
        for value in [True,False,0,101,7.0,'7',None,[],{}]:
            self.bridge.effective_options.return_value={'bar':{'workspaces':{'shown':value}}}
            with contextlib.redirect_stderr(io.StringIO()):self.assertFalse(self.runtime.tick(force=True))
        self.bridge.run.assert_not_called()

    def test_rejects_receipts_that_only_claim_process_success(self):
        self.installed();valid={'version':1,'accepted':True,'configuredCount':7,'revision':1}
        for result in [None,{},dict(valid,version=True),dict(valid,accepted=False),dict(valid,configuredCount=8),dict(valid,configuredCount=True),dict(valid,revision=True),dict(valid,revision=0)]:
            self.bridge.run.side_effect=None;self.bridge.run.return_value=subprocess.CompletedProcess([],0,json.dumps(result),'')
            with contextlib.redirect_stderr(io.StringIO()):self.assertFalse(self.runtime.tick(force=True))

    def test_bounded_retry_recovers_when_module_appears_later(self):
        self.installed();self.bridge.run.side_effect=None
        self.bridge.run.return_value=subprocess.CompletedProcess([],0,'unknown request','')
        with contextlib.redirect_stderr(io.StringIO()):self.assertFalse(self.runtime.tick())
        self.bridge.run.side_effect=self.reply;self.time=1
        self.assertFalse(self.runtime.tick());self.assertEqual(self.bridge.run.call_count,1)
        self.time=2.1;self.assertTrue(self.runtime.tick());self.assertEqual(self.bridge.run.call_count,2)
        self.assertEqual(self.runtime.last_error,'')

    def test_partial_edit_keeps_last_success_and_recovers_final_shared_count(self):
        self.installed();self.assertTrue(self.runtime.tick())
        self.time=2.1;self.bridge.effective_options.side_effect=ValueError('partial config')
        with contextlib.redirect_stderr(io.StringIO()):self.assertFalse(self.runtime.tick())
        self.assertEqual(self.bridge.run.call_count,1)
        self.bridge.effective_options.side_effect=None;self.bridge.effective_options.return_value={'bar':{'workspaces':{'shown':12}}}
        self.time=4.2;self.assertTrue(self.runtime.tick())
        self.assertEqual(self.bridge.run.call_args.args[0],['hyprctl','bwm-plasma-desktops-count','12'])

    def test_failure_does_not_escape_bridge_or_loop_and_logs_only_changed_error(self):
        self.installed();self.bridge.run.side_effect=subprocess.TimeoutExpired('hyprctl',2)
        output=io.StringIO()
        with contextlib.redirect_stderr(output):
            self.assertFalse(self.runtime.tick());self.time=2.1;self.assertFalse(self.runtime.tick())
        self.assertEqual(output.getvalue().count('native workspaces:'),1)

    def test_busy_existing_bridge_lock_retries_without_waiting_or_ipc(self):
        self.installed()
        @contextlib.contextmanager
        def busy(blocking):
            self.assertFalse(blocking)
            raise BlockingIOError('bridge busy')
            yield
        self.bridge.lock=busy
        with contextlib.redirect_stderr(io.StringIO()) as output:self.assertFalse(self.runtime.tick())
        self.assertEqual(output.getvalue(),'');self.bridge.run.assert_not_called()
        self.bridge.lock=lambda blocking:contextlib.nullcontext();self.time=0.3
        self.assertTrue(self.runtime.tick())

    def test_reconcile_already_holding_the_guard_never_locks_recursively(self):
        self.installed();self.bridge.lock=Mock(side_effect=AssertionError('recursive lock'))
        self.assertTrue(self.runtime.tick(force=True,locked=True));self.bridge.lock.assert_not_called()


if __name__=='__main__':unittest.main()
