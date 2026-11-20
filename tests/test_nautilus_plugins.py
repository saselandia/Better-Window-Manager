"""Nautilus menu providers: optional LocalSend and D-Bus activation PATH."""

import importlib.util
import os
from pathlib import Path
import shlex
import subprocess
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'config/hypr/scripts'
sys.path.insert(0, str(SCRIPTS))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


requirements = load('nautilus_requirements_test', SCRIPTS / 'bwm-requirements.py')

try:
    import gi
    gi.require_version('Nautilus', '4.1')
    from gi.repository import Gio, GLib
    EXT = ROOT / 'config/hypr/skins/retro/nautilus-python/extensions'
    localsend = load('bwm_test_localsend', EXT / 'localsend.py')
    transcode = load('bwm_test_transcode', EXT / 'transcode.py')
except (ImportError, ValueError):
    Gio = None


class RequirementTests(unittest.TestCase):
    def test_native_flatpak_missing_and_failed_probe(self):
        spec = {'check': {'type': 'cmd', 'any': ['localsend'],
                          'flatpak': 'org.localsend.localsend_app'}}
        for native, flatpak, result, expected in [
            (True, True, 1, 'ok'),
            (False, True, 0, 'ok'),
            (False, True, 1, 'missing'),
            (False, False, 0, 'missing'),
            (False, True, OSError('not available'), 'missing'),
            (False, True, subprocess.TimeoutExpired('flatpak', 5), 'missing'),
        ]:
            with self.subTest(native=native, flatpak=flatpak, result=result):
                def which(name):
                    return '/usr/bin/' + name if {'localsend': native, 'flatpak': flatpak}[name] else None
                with mock.patch.object(requirements, 'which', side_effect=which), \
                        mock.patch.object(requirements.subprocess, 'run') as run:
                    if isinstance(result, Exception):
                        run.side_effect = result
                    else:
                        run.return_value.returncode = result
                    self.assertEqual(requirements.check_requirement(spec, {})[0], expected)
                    if native or not flatpak:
                        run.assert_not_called()


@unittest.skipIf(Gio is None, 'requires Nautilus 4.1 introspection')
class MenuTests(unittest.TestCase):
    def test_absent_flatpak_app_hides_menu_without_exception(self):
        action = localsend.SendViaLocalSendAction()
        with mock.patch.object(localsend, '_which', side_effect=lambda name: '/usr/bin/flatpak' if name == 'flatpak' else None), \
                mock.patch.object(localsend.Gio.Subprocess, 'new') as spawn:
            spawn.return_value.wait_check.side_effect = GLib.Error('app not installed')
            self.assertIsNone(action._resolve_command())

    def test_flatpak_file_forwarding_preserves_filenames(self):
        action = localsend.SendViaLocalSendAction()
        command = ['/usr/bin/flatpak', 'run', '--file-forwarding', 'org.localsend.localsend_app', '@@']
        paths = ['/tmp/a file.png', '/tmp/quote\' $(false).png']
        with mock.patch.object(action, '_resolve_command', return_value=command), \
                mock.patch.object(localsend.Gio.Subprocess, 'new') as spawn:
            action._launch_localsend(paths)
            self.assertEqual(spawn.call_args.args[0], command + paths + ['@@'])

    def test_transcode_children_receive_helpers_path_and_quoted_files(self):
        paths = ['/tmp/a file.png', '/tmp/quote\' $(false).mp4']
        with mock.patch.dict(os.environ, {'PATH': '/usr/bin:/bin'}), \
                mock.patch.object(transcode, '_which', side_effect=lambda name: '/bwm/shims/' + name), \
                mock.patch.object(transcode.Gio.SubprocessLauncher, 'new') as create:
            transcode.TranscodeAction()._launch_transcode(paths)
            launcher = create.return_value
            name, path, overwrite = launcher.setenv.call_args.args
            self.assertEqual(name, 'PATH')
            self.assertTrue(overwrite)
            self.assertIn(os.path.expanduser('~/.local/bin'), path.split(':'))
            self.assertIn(os.path.expanduser('~/.config/hypr/scripts/omarchy-shims'), path.split(':'))
            wrapper, command = launcher.spawnv.call_args.args[0]
            self.assertTrue(wrapper.endswith('/omarchy-launch-floating-terminal-with-presentation'))
            for file in paths:
                self.assertIn(shlex.quote(file), command)


if __name__ == '__main__':
    unittest.main()
