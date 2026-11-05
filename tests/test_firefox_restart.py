"""Firefox tras entrar o salir de Retro: se reinicia cuando termina el cambio de skin, sólo si ya
estaba abierto antes."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'config/hypr/scripts'))
import bwm_omarchy  # noqa: E402


class AfterSwitchTest(unittest.TestCase):
    def run_after_switch(self, started, wait=True, clients=({'class': 'firefox-bin', 'pid': 7},)):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        with mock.patch.object(bwm_omarchy, '_wait_skin_switch_end', return_value=wait), \
                mock.patch.object(bwm_omarchy, '_hypr_clients', return_value=list(clients)), \
                mock.patch.object(bwm_omarchy, '_proc_start', return_value=started), \
                mock.patch.object(bwm_omarchy, '_firefox_cmd', return_value=['firefox']), \
                mock.patch.object(bwm_omarchy, 'RESTART_LOCK', Path(tmp.name) / 'lock'), \
                mock.patch.object(bwm_omarchy, 'FIREFOX_CHROME_CSS', Path(tmp.name) / 'none.css'), \
                mock.patch.object(bwm_omarchy, 'restart_app') as restart, \
                mock.patch('time.time', return_value=1000), \
                mock.patch('time.sleep'):
            bwm_omarchy.restart_firefox(after_switch=True)
        return restart.called

    def test_firefox_from_before_the_switch_restarts(self):
        self.assertTrue(self.run_after_switch(started=500))

    def test_firefox_opened_after_does_nothing(self):
        self.assertFalse(self.run_after_switch(started=2000))

    def test_switch_never_ends_does_nothing(self):
        self.assertFalse(self.run_after_switch(started=500, wait=False))

    def test_no_firefox_does_nothing(self):
        self.assertFalse(self.run_after_switch(started=500, clients=()))


if __name__ == '__main__':
    unittest.main()
