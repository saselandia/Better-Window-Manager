import importlib.machinery
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "config/hypr/scripts/monitor-manager.py"


def load_module():
    loader = importlib.machinery.SourceFileLoader("monitor_manager_under_test", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def screen(name, description, **extra):
    base = {"name": name, "description": description, "width": 1920, "height": 1080, "refreshRate": 60.0,
            "x": 0, "y": 0, "scale": 1.0, "transform": 0, "disabled": False, "is_primary": False,
            "workspaces": "10", "mirrorOf": ""}
    base.update(extra)
    return base


class MonitorMirrorTests(unittest.TestCase):
    def setUp(self):
        self.mm = load_module()
        tmp = tempfile.TemporaryDirectory(prefix="bwm-mirror-")
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.mm.CONFIG_PATH = str(root / "monitors.lua")
        self.mm.WORKSPACE_RULES_PATH = str(root / "workspace_rules.json")
        self.mm.LAYOUT_PATH = str(root / "monitors_layout.json")
        patcher = mock.patch.object(self.mm.subprocess, "run")
        self.run = patcher.start()
        self.addCleanup(patcher.stop)
        self.main = screen("DP-2", "Maker Main 1", is_primary=True, workspaces="1-9", width=2560, height=1440)
        self.side = screen("DP-1", "Maker Side 2", x=2560, width=3840, height=2160)

    def lua(self):
        return Path(self.mm.CONFIG_PATH).read_text()

    def test_copy_is_written_with_mirror_and_owns_no_workspaces(self):
        self.mm.set_mirror([self.main, self.side], self.side, self.main)
        self.mm.write_monitors_lua([self.main, self.side])
        lua = self.lua()
        self.assertIn('mirror   = "desc:Maker Main 1"', lua)
        self.assertEqual(lua.count("mirror   ="), 1)
        self.assertNotIn('monitor   = "desc:Maker Side 2"', lua)  # no workspace rule for the copy
        self.assertIn('monitor   = "desc:Maker Main 1"', lua)
        self.run.assert_called()  # Hyprland is reloaded

    def test_primary_that_becomes_a_copy_hands_1_9_to_the_source(self):
        self.mm.set_mirror([self.main, self.side], self.main, self.side)
        self.assertFalse(self.main["is_primary"])
        self.assertTrue(self.side["is_primary"])
        self.assertEqual(self.side["workspaces"], "1-9")
        self.assertEqual(self.main["workspaces"], "")
        self.mm.write_monitors_lua([self.main, self.side])
        self.assertEqual(json.loads(Path(self.mm.WORKSPACE_RULES_PATH).read_text())["primary_monitor"], "DP-1")

    def test_turning_the_copy_off_gives_the_screen_its_workspace_back(self):
        self.mm.set_mirror([self.main, self.side], self.side, self.main)
        self.mm.set_mirror([self.main, self.side], self.side, None)
        self.assertEqual(self.side["mirrorOf"], "")
        self.assertEqual(self.side["workspaces"], "10")
        self.mm.write_monitors_lua([self.main, self.side])
        self.assertNotIn("mirror   =", self.lua())

    def test_impossible_duplications_are_refused(self):
        third = screen("DP-3", "Maker Third 3")
        monitors = [self.main, self.side, third]
        with self.assertRaises(ValueError):
            self.mm.set_mirror(monitors, self.main, self.main)
        self.mm.set_mirror(monitors, self.side, self.main)
        with self.assertRaises(ValueError):  # copying a copy
            self.mm.set_mirror(monitors, third, self.side)
        with self.assertRaises(ValueError):  # a screen somebody copies cannot become a copy
            self.mm.set_mirror(monitors, self.main, third)
        third["disabled"] = True
        with self.assertRaises(ValueError):
            self.mm.set_mirror(monitors, self.main, third)

    def test_a_copy_of_a_screen_that_was_switched_off_is_dropped(self):
        self.mm.set_mirror([self.main, self.side], self.side, self.main)
        self.main["disabled"] = True
        self.mm.write_monitors_lua([self.main, self.side])
        self.assertEqual(self.side["mirrorOf"], "")
        self.assertNotIn("mirror   =", self.lua())
        self.assertIn('monitor   = "desc:Maker Side 2"', self.lua())

    def test_state_read_from_hyprland_reports_the_description_of_what_is_copied(self):
        hypr = [
            {"id": 0, "name": "DP-2", "description": "Maker Main 1", "width": 2560, "height": 1440, "refreshRate": 60, "x": 0, "y": 0,
             "scale": 1, "transform": 0, "availableModes": ["2560x1440@60.00Hz"], "mirrorOf": "none"},
            {"id": 1, "name": "DP-1", "description": "Maker Side 2", "width": 1920, "height": 1080, "refreshRate": 60, "x": 0, "y": 0,
             "scale": 1, "transform": 0, "availableModes": ["1920x1080@60.00Hz"], "mirrorOf": "DP-2"},
        ]
        with mock.patch.object(self.mm.subprocess, "check_output", return_value=json.dumps(hypr).encode()):
            by_name = {m["name"]: m for m in self.mm.get_monitors()}
        self.assertEqual(by_name["DP-1"]["mirrorOf"], "Maker Main 1")
        self.assertEqual(by_name["DP-2"]["mirrorOf"], "")


if __name__ == "__main__":
    unittest.main()
