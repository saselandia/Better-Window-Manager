import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOADER = ROOT / "config/hypr/modules/app_rules.lua"
APPS = ROOT / "config/quickshell/ii/Commons/omarchy/default/hypr/apps"

# Runs modules/app_rules.lua with a fake hl and the given skin; prints the rules as JSON.
HARNESS = r"""
local skin, windows, apps = ...
package.loaded["modules.theme"] = { name = skin, windows = windows }
local rules = {}
hl = { window_rule = function(r) rules[#rules + 1] = r end }
local errors = {}
local real_print = print
print = function(...) errors[#errors + 1] = table.concat({ ... }, " ") end
dofile(LOADER)
print = real_print
local function enc(v)
  if type(v) == "table" then
    local parts = {}
    for k, x in pairs(v) do parts[#parts + 1] = string.format("%q:%s", tostring(k), enc(x)) end
    return "{" .. table.concat(parts, ",") .. "}"
  elseif type(v) == "string" then return string.format("%q", v)
  else return tostring(v) end
end
local out = {}
for i, r in ipairs(rules) do out[i] = enc(r) end
io.write('{"rules":[' .. table.concat(out, ",") .. '],"errors":' .. #errors .. '}')
"""


def load(skin, windows):
    # The loader reads the rules from HOME/.config/quickshell/ii/…: a temporary HOME pointing at the repo
    with tempfile.TemporaryDirectory(prefix="bwm-app-rules-") as home:
        (Path(home) / ".config").mkdir()
        (Path(home) / ".config" / "quickshell").symlink_to(ROOT / "config/quickshell")
        script = "LOADER = " + json.dumps(str(LOADER)) + "\n" + HARNESS
        call = "local f = load(" + json.dumps(script) + ")\nf(" + json.dumps(skin) + ", " + json.dumps(windows) + ")"
        out = subprocess.run(["lua", "-e", call], capture_output=True, text=True, check=True,
                             env={"HOME": home, "PATH": "/usr/bin:/bin"}).stdout
    return json.loads(out)


@unittest.skipUnless(shutil.which("lua"), "lua no está instalado")
class AppRulesTests(unittest.TestCase):
    def test_every_omarchy_file_loads_and_every_rule_has_a_match(self):
        data = load("retro", "tiling")
        self.assertEqual(data["errors"], 0)
        self.assertGreater(len(data["rules"]), 30)
        self.assertTrue(all(r.get("match") for r in data["rules"]))

    def test_picture_in_picture_floats_pinned_in_the_corner(self):
        rules = load("default", "tiling")["rules"]
        pip = [r for r in rules if r["match"].get("tag") == "pip" and r.get("pin") is True]
        self.assertTrue(pip)
        self.assertIs(pip[0]["float"], True)

    def test_traditional_skins_keep_everything_floating(self):
        tiling = load("retro", "tiling")["rules"]
        traditional = load("plasma", "traditional")["rules"]
        self.assertTrue(any("tile" in r for r in tiling))
        self.assertFalse(any("tile" in r for r in traditional))

    def test_password_managers_stay_out_of_screen_captures(self):
        rules = load("plasma", "traditional")["rules"]
        hidden = [r["match"].get("class", "") for r in rules if r.get("no_screen_share") is True]
        self.assertTrue(any("assword" in c for c in hidden))
        self.assertTrue(any("itwarden" in c for c in hidden))


if __name__ == "__main__":
    unittest.main()
