"""Metadata for About must reflect the running session and handle missing dates."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('bwm_about_data', Path(__file__).resolve().parents[1] / 'bwm-about-data.py')
about = importlib.util.module_from_spec(spec)
spec.loader.exec_module(about)


class AboutDataTests(unittest.TestCase):
    def test_duration_boundaries(self):
        self.assertEqual(about.duration(0), '0m')
        self.assertEqual(about.duration(3599), '59m')
        self.assertEqual(about.duration(3600), '1h 0m')
        self.assertEqual(about.duration(90061), '1d 1h')

    def test_age_unknown_does_not_become_thousands_of_days(self):
        with patch.object(about.subprocess, 'check_output', return_value='0\n'):
            self.assertEqual(about.value('age'), '—')

    def test_revision_without_checkout_has_a_name(self):
        with patch.object(about, 'git', return_value=''):
            self.assertEqual(about.value('revision'), 'BWM')

    def test_wm_uses_the_running_compositor(self):
        with patch.object(about.subprocess, 'check_output', return_value='{"version":"0.55.4","tag":"v0.55.4"}') as run:
            self.assertEqual(about.value('wm'), 'Hyprland 0.55.4 (Wayland)')
            self.assertEqual(run.call_args.args[0], ['hyprctl', 'version', '-j'])

    def test_missing_dmi_falls_back_to_hostname(self):
        with patch.object(about, 'read', return_value=''), patch.object(about.socket, 'gethostname', return_value='test-pc'):
            self.assertEqual(about.value('host'), 'test-pc')

    def test_dynamic_theme_is_named_as_such(self):
        with patch.object(about, 'read', side_effect=lambda path, fallback='': 'dynamic' if path.name == 'theme.mode' else 'old-theme'):
            self.assertEqual(about.value('theme'), 'Dynamic')


if __name__ == '__main__':
    unittest.main()
