# SPDX-License-Identifier: GPL-2.0-or-later
"""Breeze III T5: modules/kde_shortcuts.lua and kde-shortcuts.py without a session."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
LUA = shutil.which("lua5.4") or shutil.which("lua")


@unittest.skipUnless(LUA, "lua not installed")
class ModuleTests(unittest.TestCase):
    def run_module(self, skin, state_text):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "modules").mkdir()
            (root / "modules" / "theme.lua").write_text(f'return {{ name = "{skin}" }}\n')
            (root / "state" / "bwm").mkdir(parents=True)
            if state_text is not None:
                (root / "state" / "bwm" / "kde-shortcuts.lua").write_text(state_text)
            script = (f'package.path = "{root}/?.lua;{REPO}/config/hypr/?.lua;" .. package.path\n'
                      'BINDS = {}\nhl = { bind = function(spec) BINDS[#BINDS+1] = spec; return {} end,\n'
                      '       dsp = { exec_cmd = function(c) return c end } }\n'
                      'require("modules.kde_shortcuts")\nprint(#BINDS)\n')
            env = {**os.environ, "XDG_STATE_HOME": str(root / "state")}
            r = subprocess.run([LUA, "-e", script], capture_output=True, text=True, env=env, timeout=5)
            self.assertEqual(r.returncode, 0, r.stderr)
            return int(r.stdout.strip())

    STATE = 'hl.bind("SUPER + SHIFT + k", hl.dsp.exec_cmd("x"))\n'

    def test_breeze_loads_state(self):
        self.assertEqual(self.run_module("plasma", self.STATE), 1)

    def test_other_skins_never_bind(self):
        self.assertEqual(self.run_module("retro", self.STATE), 0)
        self.assertEqual(self.run_module("default", self.STATE), 0)

    def test_missing_state_is_fine(self):
        self.assertEqual(self.run_module("plasma", None), 0)


def load_supervisor():
    spec = importlib.util.spec_from_file_location(
        "kde_shortcuts", REPO / "config/hypr/skins/plasma/scripts/kde-shortcuts.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SupervisorTests(unittest.TestCase):
    def test_start_is_a_no_op_outside_breeze(self):
        sup = load_supervisor()
        with mock.patch.object(sup, "current_skin", return_value="retro"), \
             mock.patch.object(sup, "find_running_pids", side_effect=AssertionError("must not look")):
            self.assertEqual(sup.start_daemon(), 0)

    def test_start_refuses_a_foreign_service_owner(self):
        sup = load_supervisor()
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / "bwm-kglobalaccel"
            binary.write_text("#!/bin/sh\n")
            binary.chmod(0o755)
            with mock.patch.object(sup, "current_skin", return_value="plasma"), \
                 mock.patch.object(sup, "BINARY", binary), \
                 mock.patch.object(sup, "find_running_pids", return_value=[]), \
                 mock.patch.object(sup, "service_owner_pid", return_value=4242):
                self.assertEqual(sup.start_daemon(), 1)

    def test_stop_drops_state_even_without_daemon(self):
        sup = load_supervisor()
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "kde-shortcuts.lua"
            state.write_text("-- stale\n")
            with mock.patch.object(sup, "STATE_FILE", state), \
                 mock.patch.object(sup, "find_running_pids", return_value=[]):
                self.assertEqual(sup.stop_daemon(), 0)
            self.assertFalse(state.exists())

    def test_test_daemons_are_not_the_session_daemon(self):
        sup = load_supervisor()
        self.assertFalse(sup.is_daemon_pid(os.getpid()))


if __name__ == "__main__":
    unittest.main()
