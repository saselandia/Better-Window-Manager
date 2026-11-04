"""Steam tras un cambio de skin: se reinicia sólo cuando termina el cambio y si su tema se instaló
después de arrancar Steam."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'config/hypr/scripts'))
import bwm_omarchy  # noqa: E402


class AfterSwitchTest(unittest.TestCase):
    def run_after_switch(self, started, installed, wait=True):
        stat = mock.Mock(st_mtime=installed)
        with mock.patch.object(bwm_omarchy, '_wait_skin_switch_end', return_value=wait), \
                mock.patch.object(bwm_omarchy, '_steam_started_at', return_value=started), \
                mock.patch.object(bwm_omarchy, 'STEAM_INSTALL_LOG', mock.Mock(stat=lambda: stat)), \
                mock.patch.object(bwm_omarchy, '_alive', return_value=False) as alive, \
                mock.patch('time.sleep'):
            bwm_omarchy.restart_steam(after_switch=True)
        return alive.called

    def test_theme_newer_than_steam_goes_on(self):
        self.assertTrue(self.run_after_switch(started=100, installed=200))

    def test_theme_older_than_steam_does_nothing(self):
        self.assertFalse(self.run_after_switch(started=300, installed=200))

    def test_switch_never_ends_does_nothing(self):
        self.assertFalse(self.run_after_switch(started=100, installed=200, wait=False))

    def test_plain_call_during_switch_does_nothing(self):
        with mock.patch.object(bwm_omarchy.bwm_transition, 'switching', return_value=True), \
                mock.patch.object(bwm_omarchy, '_alive') as alive:
            bwm_omarchy.restart_steam()
        alive.assert_not_called()


class GameOpenTest(unittest.TestCase):
    def setUp(self):
        # The real session may have a waiter holding the real lock
        self.tmp = tempfile.TemporaryDirectory()
        patcher = mock.patch.object(bwm_omarchy, 'STEAM_RESTART_LOCK', self.tmp.name + '/lock')
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

    def test_waits_for_the_game_then_restarts(self):
        running = iter([True, True, False])
        restarted = []
        with mock.patch.object(bwm_omarchy.bwm_transition, 'switching', return_value=False), \
                mock.patch.object(bwm_omarchy, '_alive', return_value=True), \
                mock.patch.object(bwm_omarchy, '_steam_game_running', side_effect=lambda: next(running)), \
                mock.patch.object(bwm_omarchy, '_steam_started_at', return_value=100), \
                mock.patch.object(bwm_omarchy, 'STEAM_INSTALL_LOG', mock.Mock(stat=lambda: mock.Mock(st_mtime=200))), \
                mock.patch.object(bwm_omarchy, '_hypr_clients', return_value=[{'class': 'steam'}]), \
                mock.patch.object(bwm_omarchy, '_detached'), \
                mock.patch.object(bwm_omarchy, 'restart_app', side_effect=lambda *a, **k: restarted.append(1)), \
                mock.patch('time.sleep'):
            bwm_omarchy.restart_steam()
        self.assertEqual(restarted, [1])

    def test_steam_restarted_meanwhile_is_left_alone(self):
        running = iter([True, False])
        with mock.patch.object(bwm_omarchy.bwm_transition, 'switching', return_value=False), \
                mock.patch.object(bwm_omarchy, '_alive', return_value=True), \
                mock.patch.object(bwm_omarchy, '_steam_game_running', side_effect=lambda: next(running)), \
                mock.patch.object(bwm_omarchy, '_steam_started_at', return_value=300), \
                mock.patch.object(bwm_omarchy, 'STEAM_INSTALL_LOG', mock.Mock(stat=lambda: mock.Mock(st_mtime=200))), \
                mock.patch.object(bwm_omarchy, '_detached'), \
                mock.patch.object(bwm_omarchy, 'restart_app') as restart, \
                mock.patch('time.sleep'):
            bwm_omarchy.restart_steam()
        restart.assert_not_called()


if __name__ == '__main__':
    unittest.main()
