"""A KDE helper process is only a conflict when it owns a BWM service."""
import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('shell_conflicts', Path(__file__).resolve().parents[1] / 'config/hypr/scripts/bwm-shell-conflicts.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class ShellConflictsTest(unittest.TestCase):
    def owner(self, name):
        process = mock.MagicMock()
        process.stat.return_value.st_uid = helper.os.getuid()
        process.__truediv__.return_value.resolve.return_value.name = name
        root = mock.MagicMock()
        root.__truediv__.return_value = process
        return mock.patch.object(helper, 'Path', return_value=root)

    def test_harmless_kded_is_not_detected_from_process_presence(self):
        with mock.patch.object(helper.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'busctl')):
            self.assertIsNone(helper.conflict('trays'))

    def test_kded_with_watcher_name_is_a_conflict_even_if_object_is_stale(self):
        with self.owner('kded6'), mock.patch.object(helper.subprocess, 'run', return_value=mock.Mock(stdout='u 123\n')):
            self.assertEqual(helper.conflict('trays'), {'pid': 123, 'name': 'kded6'})

    def test_our_shell_and_notification_owner_are_not_conflicts(self):
        for name in ('quickshell', 'swaync'):
            with self.owner(name), mock.patch.object(helper.subprocess, 'run', return_value=mock.Mock(stdout='u 123\n')):
                self.assertIsNone(helper.conflict('trays'))
                self.assertIsNone(helper.conflict('notifications'))

    def test_resolution_rechecks_owner_and_targets_only_that_pid(self):
        owner = {'pid': 123, 'name': 'kded6'}
        with mock.patch.object(helper, 'conflict', return_value=owner), mock.patch.object(helper.os, 'kill') as kill:
            helper.resolve('trays')
            kill.assert_called_once_with(123, helper.signal.SIGTERM)
        with mock.patch.object(helper, 'conflict', side_effect=[owner, None]), mock.patch.object(helper.os, 'kill') as kill:
            helper.resolve('trays')
            kill.assert_not_called()
