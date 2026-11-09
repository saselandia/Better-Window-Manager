import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "config/hypr/scripts"))
import bwm_omarchy  # noqa: E402

DEFAULTS = {
    "version": 1,
    "bar": {
        "position": "top",
        "background": "opaque",
        "layout": {
            "left": [{"id": "omarchy.menu"}, {"id": "omarchy.workspaces"}],
            "centerBegin": [{"id": "omarchy.indicators"}],
            "center": [{"id": "omarchy.clock", "format": "dddd HH:mm"}],
            "centerEnd": [{"id": "omarchy.weather"}],
            "right": [{"id": "omarchy.audio"}, {"id": "omarchy.power"}],
        },
    },
}


class OmarchyShellJsonTests(unittest.TestCase):
    def test_turned_off_widgets_leave_the_bar(self):
        config = bwm_omarchy.omarchy_shell_config(DEFAULTS, {"disabled": ["omarchy.power", "omarchy.weather"]})
        layout = config["bar"]["layout"]
        self.assertEqual([e["id"] for e in layout["right"]], ["omarchy.audio"])
        self.assertEqual(layout["centerEnd"], [])

    def test_placed_plugins_keep_section_and_inline_settings(self):
        bwm = {"bar": [{"id": "crmne.mpris", "section": "centerEnd", "settings": {"maxCharacters": 48}},
                       {"id": "omarchy.clock", "section": "clock", "settings": {"format": "HH:mm"}}]}
        layout = bwm_omarchy.omarchy_shell_config(DEFAULTS, bwm)["bar"]["layout"]
        self.assertIn({"id": "crmne.mpris", "maxCharacters": 48}, layout["centerEnd"])
        self.assertEqual(layout["center"], [{"id": "omarchy.clock", "format": "HH:mm"}])

    def test_background_follows_the_old_bar_and_defaults_are_untouched(self):
        config = bwm_omarchy.omarchy_shell_config(DEFAULTS, {}, show_background=False)
        self.assertEqual(config["bar"]["background"], "none")
        self.assertEqual(DEFAULTS["bar"]["background"], "opaque")


if __name__ == "__main__":
    unittest.main()
