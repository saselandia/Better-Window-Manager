# SPDX-License-Identifier: GPL-2.0-or-later
"""Opt-in provider loading at Hyprland start and its crash-loop guard (§255)."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT/'config/hypr/skins/plasma/scripts/native-desktops.py'
COMMIT = 'efb50993780079460b0cbed1363e2166a2de1d9f'


def load(env):
    with patch.dict(os.environ, env):
        spec = importlib.util.spec_from_file_location('r4_native_desktops', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


class FakeHyprland:
    def __init__(self, load='ok', enabled=True, loaded=False):
        self.load, self.enabled, self.loaded, self.calls = load, enabled, loaded, []

    def __call__(self, *args, timeout=3):
        self.calls.append(args)
        out = ''
        if args == ('-j', 'version'):
            out = json.dumps({'commit': COMMIT})
        elif args == ('plugin', 'list'):
            out = 'Plugin bwm-plasma-desktops by BWM\n' if self.loaded else 'Plugin breezebars\n'
        elif args[:2] == ('plugin', 'load'):
            out = self.load
            self.loaded = self.load == 'ok'
        elif args[0] == 'eval':
            out = 'ok'
        elif args == ('-j', 'bwm-plasma-desktops'):
            out = json.dumps({'enabled': self.enabled})
        return subprocess.CompletedProcess(args, 0, out, '')


class StartupTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.env = {'XDG_CONFIG_HOME': str(root/'config'), 'XDG_STATE_HOME': str(root/'state'),
                    'XDG_RUNTIME_DIR': str(root/'runtime'), 'HYPRLAND_INSTANCE_SIGNATURE': 'session-B'}
        (root/'runtime').mkdir()
        patcher = patch.dict(os.environ, self.env)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.m = load(self.env)
        self.m.PLUGIN.parent.mkdir(parents=True)
        self.m.PLUGIN.write_bytes(b'\0'+COMMIT.encode()+b'\0')
        self.notes = []
        for name, value in (('notify', self.notes.append), ):
            p = patch.object(self.m, name, value)
            p.start()
            self.addCleanup(p.stop)
        p = patch.object(self.m.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', ''))
        self.run = p.start()
        self.addCleanup(p.stop)

    def start(self, fake):
        with patch.object(self.m, 'hyprctl', fake):
            return self.m.startup(sleep=lambda seconds: None)

    def test_not_opted_in_never_loads(self):
        fake = FakeHyprland()
        self.assertEqual(self.start(fake)['skipped'], 'not-opted-in')
        self.assertFalse(any(c[:2] == ('plugin', 'load') for c in fake.calls))

    def test_opted_in_loads_enables_marks_session_and_clears_guard(self):
        self.m.main(['enable'])
        fake = FakeHyprland()
        report = self.start(fake)
        self.assertTrue(report['loaded'])
        self.assertTrue(report['stable'])
        self.assertIn(('plugin', 'load', str(self.m.PLUGIN)), fake.calls)
        self.assertEqual(json.loads(self.m.SESSION.read_text()), {'version': 1, 'instance': 'session-B', 'loaded': True})
        self.assertTrue(self.m.loaded_in_this_session())
        self.assertFalse(self.m.GUARD.exists())

    def test_previous_unstable_start_disables_opt_in_and_skips_loading(self):
        self.m.main(['enable'])
        self.m.write_json(self.m.GUARD, {'version': 1, 'pending': True, 'instance': 'session-A', 'started': 1})
        fake = FakeHyprland()
        self.assertEqual(self.start(fake)['skipped'], 'disabled-after-unstable-start')
        self.assertFalse(self.m.opted_in())
        self.assertFalse(any(c[:2] == ('plugin', 'load') for c in fake.calls))
        self.assertTrue(self.notes)
        self.assertFalse(self.m.GUARD.exists())

    def test_crash_during_stability_window_leaves_guard_for_next_start(self):
        self.m.main(['enable'])
        with patch.object(self.m, 'hyprctl', FakeHyprland()):
            # Simulated session end during the window: the instance disappears.
            def gone(seconds):
                os.environ['HYPRLAND_INSTANCE_SIGNATURE'] = ''
            report = self.m.startup(sleep=gone)
        self.assertTrue(report['loaded'])
        self.assertNotIn('stable', report)
        self.assertTrue(json.loads(self.m.GUARD.read_text())['pending'])

    def test_module_for_another_hyprland_or_failed_load_never_marks_session(self):
        self.m.main(['enable'])
        self.m.PLUGIN.write_bytes(b'built-for-0.55')
        self.assertEqual(self.start(FakeHyprland())['error'], 'module-built-for-another-hyprland')
        self.m.PLUGIN.write_bytes(COMMIT.encode())
        report = self.start(FakeHyprland(load='could not be loaded'))
        self.assertTrue(report['error'].startswith('load-failed'))
        self.assertFalse(self.m.SESSION.exists())
        self.assertFalse(self.m.GUARD.exists())
        self.assertEqual(self.start(FakeHyprland(enabled=False))['error'], 'enable-failed')
        self.assertFalse(self.m.SESSION.exists())

    def test_already_loaded_module_is_not_loaded_again(self):
        self.m.main(['enable'])
        fake = FakeHyprland(loaded=True)
        self.assertTrue(self.start(fake)['loaded'])
        self.assertFalse(any(c[:2] == ('plugin', 'load') for c in fake.calls))

    def test_disable_and_stale_session_marker(self):
        self.m.main(['enable'])
        self.m.write_json(self.m.SESSION, {'version': 1, 'instance': 'session-A', 'loaded': True})
        self.assertFalse(self.m.loaded_in_this_session())
        self.m.main(['disable'])
        self.assertFalse(self.m.opted_in())
        self.assertEqual(self.start(FakeHyprland())['skipped'], 'not-opted-in')
        self.assertFalse(self.m.SESSION.exists())


if __name__ == '__main__':
    unittest.main()
