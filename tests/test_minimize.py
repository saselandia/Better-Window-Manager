import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "config/hypr/scripts/toggle-minimize.py"
spec = importlib.util.spec_from_file_location("toggle_minimize", SCRIPT)
tm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tm)


class MinimizeTests(unittest.TestCase):
    def test_special_workspace_and_legacy_99_are_minimized(self):
        self.assertTrue(tm.is_minimized({"workspace": {"id": -98, "name": "special:minimized"}}))
        self.assertTrue(tm.is_minimized({"workspace": {"id": 99, "name": "99"}}))
        self.assertFalse(tm.is_minimized({"workspace": {"id": 3, "name": "3"}}))
        self.assertFalse(tm.is_minimized({"workspace": {"id": -97, "name": "special:magic"}}))

    def test_origin_from_omarchy_and_legacy_tags(self):
        self.assertEqual(tm.origin_workspace({"tags": ["terminal*", "omarchy-minimized-from-4"]}), 4)
        self.assertEqual(tm.origin_workspace({"tags": ["from_ws_7"]}), 7)
        self.assertIsNone(tm.origin_workspace({"tags": ["from_ws_99", "snapped_left"]}))

    def test_only_minimize_tags_are_removed(self):
        tags = ["snapped_left", "omarchy-minimized-from-2", "from_ws_2*", "omarchy-floating-workspace"]
        self.assertEqual(tm.minimize_tags({"tags": tags}), ["omarchy-minimized-from-2", "from_ws_2"])


if __name__ == "__main__":
    unittest.main()
