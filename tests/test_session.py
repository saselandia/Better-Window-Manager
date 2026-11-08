"""bwm_session: demonios como hijos de Hyprland; window-guard relanza la barra si desaparece."""
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / 'config/hypr/scripts'
sys.path.insert(0, str(SCRIPTS))
import bwm_session  # noqa: E402

spec = importlib.util.spec_from_file_location('window_guard', SCRIPTS / 'window-guard.py')
wg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wg)


class SpawnTest(unittest.TestCase):
    def test_spawn_goes_through_hyprland(self):
        with mock.patch.object(bwm_session.subprocess, 'run',
                               return_value=mock.Mock(returncode=0, stdout='ok\n')) as run, \
                mock.patch.object(bwm_session.subprocess, 'Popen') as popen:
            self.assertTrue(bwm_session.spawn(['quickshell', '-n', '-c', 'ii'], '/run/x "y".log'))
        code = run.call_args.args[0][2]
        self.assertTrue(code.startswith('hl.dsp.exec_cmd("quickshell -n -c ii >'))
        self.assertIn('\\"y\\"', code)  # comillas escapadas para Lua
        popen.assert_not_called()

    def test_spawn_falls_back_without_hyprland(self):
        with mock.patch.object(bwm_session.subprocess, 'run',
                               return_value=mock.Mock(returncode=7, stdout='error')), \
                mock.patch.object(bwm_session.subprocess, 'Popen') as popen:
            self.assertTrue(bwm_session.spawn(['swaync']))
        self.assertEqual(popen.call_args.args[0], ['sh', '-c', 'exec swaync'])
        self.assertNotIn('BWM_SKIN_SWITCH', popen.call_args.kwargs['env'])

    def test_no_instances_without_json(self):
        with mock.patch.object(bwm_session.subprocess, 'run', return_value=mock.Mock(stdout='')):
            self.assertEqual(bwm_session.shell_instances(), [])

    def test_ensure_shell_never_starts_a_second(self):
        with mock.patch.object(bwm_session, 'shell_instances', return_value=[{'pid': 1}]), \
                mock.patch.object(bwm_session, 'start_shell') as start:
            self.assertFalse(bwm_session.ensure_shell())
        start.assert_not_called()


class KeepShellTest(unittest.TestCase):
    def run_checks(self, states, busy=False):
        states = list(states)
        with mock.patch.object(wg.bwm_session, 'shell_instances', side_effect=lambda: states.pop(0)), \
                mock.patch.object(wg.bwm_session, 'theme_manager_busy', return_value=busy), \
                mock.patch.object(wg.bwm_session, 'start_shell') as start:
            wg.keep_shell(checks=len(states), sleep=lambda s: None)
        return start.call_count

    def test_one_miss_is_tolerated(self):
        self.assertEqual(self.run_checks([[], [{'pid': 1}], [], [{'pid': 1}]]), 0)

    def test_two_misses_restart(self):
        self.assertEqual(self.run_checks([[], []]), 1)

    def test_skin_change_in_progress_waits(self):
        self.assertEqual(self.run_checks([[], [], []], busy=True), 0)


if __name__ == '__main__':
    unittest.main()
