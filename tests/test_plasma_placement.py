import json
import shutil
import subprocess
import unittest
from pathlib import Path

PLACEMENT = Path(__file__).resolve().parents[1] / "config/hypr/skins/plasma/hypr/placement.lua"

# Runs placement.lua with a fake hl: a 1920x1080 monitor with a 24 px bar on top, the windows
# already on the workspace and the new one; prints where the new window was moved (or null).
HARNESS = r"""
local others, new, policy = ...
package.loaded["skins.plasma.hypr.kwin"] = { placement = policy }
local moved = "null"
local monitor = { x = 0, y = 0, width = 1920, height = 1080, scale = 1, transform = 0,
                  reserved = { left = 0, top = 24, right = 0, bottom = 0 } }
local function window(spec, address)
    return { address = address, pid = spec.pid or 100, class = spec.class or "app", title = spec.title or "",
             floating = true, fullscreen = 0, pinned = false, mapped = true, hidden = false,
             at = { x = spec.x, y = spec.y }, size = { x = spec.w, y = spec.h },
             workspace = { id = 1 }, monitor = monitor }
end
local list = {}
for i, spec in ipairs(others) do list[i] = window(spec, "0x" .. i) end
local handler
hl = {
    on = function(_, f) handler = f end,
    get_workspace_windows = function() return list end,
    dispatch = function(d) moved = string.format('{"x": %d, "y": %d}', d.x, d.y) end,
    dsp = { window = { move = function(args) return args end } },
}
dofile(PLACEMENT)
if new.pid == nil then new.pid = 200 end
handler(window(new, "0xnew"))
print(moved)
"""


def place(others, new, policy="Smart"):
    script = "PLACEMENT = " + json.dumps(str(PLACEMENT)) + "\n" + HARNESS
    lua_table = lambda d: "{" + ", ".join(f"{k} = {json.dumps(v)}" for k, v in d.items()) + "}"
    call = "local f = load(" + json.dumps(script) + ")\nf({" + ", ".join(map(lua_table, others)) + "}, " + lua_table(new) + ", " + json.dumps(policy) + ")"
    out = subprocess.run(["lua", "-e", call], capture_output=True, text=True, check=True).stdout.strip()
    return json.loads(out)


@unittest.skipUnless(shutil.which("lua"), "lua no está instalado")
class PlasmaPlacementTests(unittest.TestCase):
    def test_alone_keeps_hyprland_position(self):
        self.assertIsNone(place([], {"x": 510, "y": 240, "w": 900, "h": 600}))

    def test_free_center_is_kept(self):
        moved = place([{"x": 10, "y": 74, "w": 300, "h": 300}], {"x": 510, "y": 240, "w": 800, "h": 500})
        self.assertEqual(moved, {"x": 560, "y": 34 + (1036 - 530) // 2 + 30})

    def test_goes_to_free_space_beside_the_other(self):
        moved = place([{"x": 10, "y": 64, "w": 900, "h": 900}], {"x": 510, "y": 240, "w": 900, "h": 600})
        self.assertGreaterEqual(moved["x"], 10 + 900 + 10)
        self.assertEqual(moved["y"], 34 + 30)

    def test_dialogs_of_the_same_app_are_left_alone(self):
        self.assertIsNone(place([{"x": 10, "y": 64, "w": 900, "h": 900, "pid": 7}],
                                {"x": 510, "y": 240, "w": 400, "h": 300, "pid": 7}))

    def test_centered_policy_even_for_first_window(self):
        moved = place([], {"x": 10, "y": 64, "w": 800, "h": 500}, "Centered")
        self.assertEqual(moved, {"x": 560, "y": 317})

    def test_top_left_and_no_placement_policies(self):
        new = {"x": 510, "y": 240, "w": 900, "h": 600}
        self.assertEqual(place([], new, "ZeroCornered"), {"x": 10, "y": 64})
        self.assertIsNone(place([], new, "NoPlacement"))

    def test_file_dialogs_keep_their_rule(self):
        self.assertIsNone(place([{"x": 10, "y": 64, "w": 900, "h": 900}],
                                {"x": 510, "y": 240, "w": 400, "h": 300, "title": "Abrir archivo"}))


if __name__ == "__main__":
    unittest.main()
