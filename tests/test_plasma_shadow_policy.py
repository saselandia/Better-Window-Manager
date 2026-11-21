"""Containment: keep unvalidated custom shadows out of the render/capture path."""
from pathlib import Path
import shutil
import subprocess
import unittest


class ShadowPolicyTest(unittest.TestCase):
    def test_default_disables_unvalidated_shadow_and_no_border_remains_shadowless(self):
        if not shutil.which("lua"):
            self.skipTest("lua is needed for rule evaluation")
        path = Path(__file__).resolve().parents[1] / "config/hypr/skins/plasma/hypr/rules.lua"
        prelude = '''
            local rules = {}
            local layers = {}
            hl = {
                window_rule = function(rule) rules[rule.name] = rule end,
                layer_rule = function(rule) layers[rule.name] = rule end,
            }
        '''
        assertions = '''
            assert(rules["breeze-float-all"].float == true)
            assert(rules["breeze-float-all"].no_shadow == true, "Custom shadows need capture-path validation before enabling")
            assert(rules["breeze-no-border"].no_shadow == true)
            assert(rules["breeze-no-border"].decorate == false)
            local blur = assert(layers["breeze-blur-frames"], "breeze-blur-frames layer rule missing")
            assert(blur.ignore_alpha == 0.01)
            assert(blur.blur_popups == true)
            for _, ns in ipairs({ "plasmaPanel", "plasmaKickoff", "plasmaNotifications", "altTab", "plasmaMenu", "bwm-plasma-osd", "krunner" }) do
                assert(blur.match.namespace:find(ns, 1, true), "breeze-blur-frames missing " .. ns)
            end
        '''
        result = subprocess.run(["lua", "-"], input=prelude + path.read_text() + assertions,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
