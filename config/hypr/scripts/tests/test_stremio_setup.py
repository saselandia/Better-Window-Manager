"""Optional app setup must not touch the system when Stremio is absent."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location(
    'stremio_theme', Path(__file__).resolve().parents[1] / 'stremio-theme.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class OptionalStremioSetup(unittest.TestCase):
    def test_without_flatpak_no_commands_or_configuration(self):
        with patch.object(module.shutil, 'which', return_value=None), \
                patch.object(module.subprocess, 'run') as run, \
                patch.object(module, 'STATE') as state, patch('sys.argv', ['setup']):
            module.main()
            run.assert_not_called()
            state.mkdir.assert_not_called()

    def test_without_stremio_no_overrides_or_configuration(self):
        with patch.object(module.shutil, 'which', return_value='/usr/bin/flatpak'), \
                patch.object(module.subprocess, 'run', return_value=Mock(returncode=1)) as run, \
                patch.object(module, 'STATE') as state, patch('sys.argv', ['setup']):
            module.main()
            self.assertEqual(len(run.call_args_list), 1)
            self.assertEqual(run.call_args.args[0], ['flatpak', 'info', module.APP])
            state.mkdir.assert_not_called()

    def test_installer_setup_only_does_not_restart_apps(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(module, 'installed', return_value=True), \
                patch.object(module, 'STATE', Path(directory)), \
                patch.object(module, 'configure') as configure, \
                patch.object(module.subprocess, 'run') as run, \
                patch('sys.argv', ['setup', '--setup-only']):
            module.main()
            configure.assert_called_once()
            run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
