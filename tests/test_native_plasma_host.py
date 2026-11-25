"""Native host readiness: stale marker files must never hide the fallback panel."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch, MagicMock

SCRIPT = Path(__file__).resolve().parents[1] / 'config/hypr/skins/plasma/scripts/plasma-host.py'
spec = importlib.util.spec_from_file_location('native_plasma_host', SCRIPT)
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)


class TrayRecoveryTests(unittest.TestCase):
    def test_healthy_watcher_is_not_changed(self):
        with patch.object(host, 'tray_call', return_value=subprocess.CompletedProcess([],0,'as 0','')) as call:
            host.ensure_tray_watcher()
            self.assertEqual(call.call_count,1)

    def test_timeout_or_unknown_failure_does_not_load_modules(self):
        for reply in (None, subprocess.CompletedProcess([],1,'','Access denied')):
            with patch.object(host, 'tray_call', return_value=reply) as call:
                host.ensure_tray_watcher()
                self.assertEqual(call.call_count,1)

    def test_only_stale_kded_object_is_repaired_without_stopping_anything(self):
        process=MagicMock();process.stat.return_value.st_uid=host.os.getuid()
        process.__truediv__.return_value.resolve.return_value.name='kded6'
        path=MagicMock();path.__truediv__.return_value=process
        replies=[subprocess.CompletedProcess([],1,'',"No such object path"),
                 subprocess.CompletedProcess([],0,'u 123',''),
                 subprocess.CompletedProcess([],0,'b true',''),
                 subprocess.CompletedProcess([],0,'as 0',''),
                 subprocess.CompletedProcess([],0,'','')]
        with patch.object(host, 'Path', return_value=path), \
             patch.object(host, 'tray_call', side_effect=replies) as call, \
             patch.object(host.os, 'kill') as kill:
            host.ensure_tray_watcher()
            self.assertEqual(call.call_args_list[2].args[-3:],('loadModule','s','statusnotifierwatcher'))
            self.assertFalse(any('unloadModule' in c.args or 'quit' in c.args for c in call.call_args_list))
            kill.assert_not_called()

    def test_foreign_owner_is_not_repaired(self):
        replies=[subprocess.CompletedProcess([],1,'',"No such object path"),
                 subprocess.CompletedProcess([],0,f'u {os.getpid()}','')]
        with patch.object(host, 'tray_call', side_effect=replies) as call:
            host.ensure_tray_watcher()
            self.assertEqual(call.call_count,2)


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='bwm-host-readiness-')
        self.addCleanup(self.directory.cleanup)
        self.marker = Path(self.directory.name) / 'ready'
        self.ready_patch = patch.object(host, 'READY_FILE', self.marker)
        self.ready_patch.start()
        self.addCleanup(self.ready_patch.stop)

    def test_missing_or_malformed_marker_is_not_ready(self):
        for text in (None, '', 'not a pid', '0', '-1'):
            if text is not None:
                self.marker.write_text(text)
            self.assertEqual(host.main(['ready']), 1)

    def test_existing_marker_for_an_unrelated_live_process_is_not_ready(self):
        self.marker.write_text(str(os.getpid()))
        self.assertEqual(host.main(['ready']), 1)
        self.assertTrue(self.marker.exists())

    def test_crashed_host_does_not_need_to_remove_its_marker(self):
        self.marker.write_text('12345\n')
        with patch.object(host, 'is_host_pid', return_value=True):
            self.assertEqual(host.ready_pid(), 12345)
            self.assertEqual(host.main(['ready']), 0)
        with patch.object(host, 'is_host_pid', return_value=False):
            self.assertEqual(host.main(['ready']), 1)
        self.assertEqual(self.marker.read_text(), '12345\n')

    def test_another_running_host_does_not_validate_a_stale_marker(self):
        self.marker.write_text('12345\n')
        with patch.object(host, 'is_host_pid', return_value=False), \
             patch.object(host, 'find_running_pids', return_value=[54321]):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                host.status_host()
            status = json.loads(output.getvalue())
            self.assertTrue(status['running'])
            self.assertFalse(status['ready'])

    def test_ready_probe_does_not_scan_or_mutate_the_session(self):
        self.marker.write_text('12345')
        with patch.object(host, 'is_host_pid', return_value=True), \
             patch.object(host, 'find_running_pids') as scan, \
             patch.object(host.os, 'kill') as kill, \
             patch.object(host.subprocess, 'run') as run:
            self.assertEqual(host.main(['ready']), 0)
            scan.assert_not_called()
            kill.assert_not_called()
            run.assert_not_called()
        self.assertTrue(self.marker.exists())

    @unittest.skipUnless(shutil.which('cc'), 'C compiler needed for a disposable process fixture')
    def test_sigkill_leaves_a_marker_but_revokes_readiness(self):
        root = Path(self.directory.name)
        source = root / 'process.c'
        source.write_text('#include <unistd.h>\nint main(void) { for (;;) pause(); }\n')
        binary = root / 'bwm-plasma-host'
        subprocess.run(['cc', str(source), '-o', str(binary)], check=True,
                       capture_output=True, timeout=10)
        with subprocess.Popen([str(binary), '--session'], stdin=subprocess.DEVNULL,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) as process:
            try:
                self.marker.write_text(str(process.pid))
                self.assertEqual(host.main(['ready']), 0)
                process.kill()
                process.wait(timeout=3)
                self.assertTrue(self.marker.exists())
                self.assertEqual(host.main(['ready']), 1)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=3)


@unittest.skipUnless(os.environ.get('BWM_RUN_QML_TESTS') == '1' and shutil.which('qs'),
                     'optional isolated Quickshell readiness checks')
class ShellProbeTests(unittest.TestCase):
    def test_ready_crash_and_failed_to_start_restore_the_fallback(self):
        # Execute the actual Process block, without the family imports/loaders or
        # session services. The standalone shell has no windows and no live actions.
        source = SCRIPT.parents[4] / 'quickshell/ii/panelFamilies/IllogicalImpulseFamily.qml'
        text = source.read_text()
        begin = text.index('    Process {\n        id: nativeHostProbe')
        end = text.index('\n    Timer {', begin)
        process = text[begin:end].replace('["python3",', '[familyRoot.interpreter,')
        with tempfile.TemporaryDirectory(prefix='bwm-readiness-qml-') as directory:
            root = Path(directory)
            for code in (0, 1):
                (root / f'exit{code}.py').write_text(f'raise SystemExit({code})\n')
            harness = '''import QtQuick
import Quickshell
import Quickshell.Io
ShellRoot {
    id: familyRoot
    property bool _nativeHostReady: false
    property string _nativeHostHelper: %s
    property string interpreter: "python3"
    property int step: 0
%s
    Timer {
        running: true; repeat: true; interval: 50
        onTriggered: {
            if (nativeHostProbe.running) return;
            if (step === 1 || step === 3) {
                if (!familyRoot._nativeHostReady) throw new Error("live host lost");
            }
            if (step === 2 || step === 4) {
                if (familyRoot._nativeHostReady) throw new Error("stale host retained");
            }
            if (step === 4) { console.log("READYPROBE OK"); Qt.quit(); return; }
            if (step === 1) familyRoot._nativeHostHelper = %s;
            if (step === 2) familyRoot._nativeHostHelper = %s;
            if (step === 3) familyRoot.interpreter = "/bwm-test-no-such-interpreter";
            step++;
            nativeHostProbe.check();
        }
    }
    Timer { running: true; interval: 5000; onTriggered: Qt.quit() }
}
''' % (json.dumps(str(root / 'exit0.py')), process,
       json.dumps(str(root / 'exit1.py')), json.dumps(str(root / 'exit0.py')))
            qml = root / 'probe.qml'
            qml.write_text(harness)
            reply = subprocess.run(['qs', '-p', str(qml)], capture_output=True, text=True, timeout=8,
                                   env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen'})
            output = reply.stdout + reply.stderr
            self.assertEqual(reply.returncode, 0, output)
            self.assertIn('READYPROBE OK', output)
            self.assertNotIn('Error:', output)


if __name__ == '__main__':
    unittest.main()
