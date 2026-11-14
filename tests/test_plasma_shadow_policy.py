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
            hl = {window_rule = function(rule) rules[rule.name] = rule end}
        '''
        assertions = '''
            assert(rules["breeze-float-all"].float == true)
            assert(rules["breeze-float-all"].no_shadow == true, "Custom shadows need capture-path validation before enabling")
            assert(rules["breeze-no-border"].no_shadow == true)
            assert(rules["breeze-no-border"].decorate == false)
        '''
        result = subprocess.run(["lua", "-"], input=prelude + path.read_text() + assertions,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
