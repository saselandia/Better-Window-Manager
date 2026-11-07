"""Reinicio de una app (Steam al cambiar de fondo): focus_on_activate apagado mientras dura, y su
valor original de vuelta al acabar el último reinicio aunque se solapen varios."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'config/hypr/scripts'))
import bwm_windows


class FakeHyprctl:
    def __init__(self, value=True):
        self.value = value

    def run(self, args, **kw):
        if args[:2] == ['hyprctl', 'getoption']:
            return subprocess.CompletedProcess(args, 0, stdout='{"bool": %s}' % str(self.value).lower())
        if args[:2] == ['hyprctl', 'eval']:
            self.value = 'focus_on_activate = true' in args[2]
        return subprocess.CompletedProcess(args, 0, stdout='')


class QuietActivationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.hypr = FakeHyprctl()
        for p in (patch.object(bwm_windows.quiet_activation, 'DIR', Path(self.tmp.name)),
                  patch.object(bwm_windows.subprocess, 'run', self.hypr.run)):
            p.start()
            self.addCleanup(p.stop)

    def holder(self, pid):
        with patch.object(bwm_windows.os, 'getpid', return_value=pid):
            q = bwm_windows.quiet_activation()
            q.__enter__()
        return lambda: self._leave(q, pid)

    def _leave(self, q, pid):
        with patch.object(bwm_windows.os, 'getpid', return_value=pid):
            q.__exit__(None, None, None)

    def test_off_while_restarting_and_back_after(self):
        with bwm_windows.quiet_activation():
            self.assertFalse(self.hypr.value)
        self.assertTrue(self.hypr.value)

    def test_overlapping_restarts_restore_after_the_last(self):
        # PIDs vivos de verdad: el de este proceso y el de su padre
        leave_a = self.holder(os.getpid())
        leave_b = self.holder(os.getppid())
        self.assertFalse(self.hypr.value)
        leave_a()
        self.assertFalse(self.hypr.value)  # Firefox aún se está reabriendo
        leave_b()
        self.assertTrue(self.hypr.value)

    def test_keeps_an_original_false(self):
        self.hypr.value = False
        with bwm_windows.quiet_activation():
            pass
        self.assertFalse(self.hypr.value)

    def test_dead_holder_does_not_block_the_restore(self):
        (Path(self.tmp.name) / 'pid-999999999').touch()
        with bwm_windows.quiet_activation():
            pass
        self.assertTrue(self.hypr.value)


if __name__ == '__main__':
    unittest.main()
