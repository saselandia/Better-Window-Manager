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

    def test_blur_on_request_plugin_clears_global_no_blur(self):
        if not shutil.which("lua"):
            self.skipTest("lua is needed for rule evaluation")
        path = Path(__file__).resolve().parents[1] / "config/hypr/skins/plasma/hypr/rules.lua"
        script = f'''
            local rules, layers = {{}}, {{}}
            hl = {{
                window_rule = function(r) rules[r.name] = r end,
                layer_rule = function(r) layers[r.name] = r end,
                plugin = {{ breezebars = {{}} }},
            }}
            assert(loadfile({str(path)!r}))()
            assert(rules["breeze-float-all"].no_blur == true, "older plugin must keep no_blur on all windows")

            rules = {{}}
            hl.plugin.breezebars.blur_on_request = function() return true end
            assert(loadfile({str(path)!r}))()
            assert(rules["breeze-float-all"].no_blur == nil, "blur_on_request plugin should let plugin own no_blur")
        '''
        result = subprocess.run(["lua", "-"], input=script, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_skin_switch_restores_blur_options_from_breeze(self):
        if not shutil.which("lua"):
            self.skipTest("lua is needed for appearance evaluation")
        import os
        import tempfile
        hypr_dir = Path(__file__).resolve().parents[1] / "config/hypr"
        with tempfile.TemporaryDirectory(prefix="bwm-blur-switch-") as state_home:
            kwin_state = Path(state_home) / "bwm/plasma/kwin.lua"
            kwin_state.parent.mkdir(parents=True)
            kwin_state.write_text("return { blur = true, blurStrength = 15 }\n")
            script = f'''
                package.path = {str(hypr_dir)!r} .. "/?.lua;" .. package.path
                local state = {{}}
                local function merge(dst, src)
                    for k, v in pairs(src) do
                        if type(v) == "table" and type(dst[k]) == "table" then
                            merge(dst[k], v)
                        elseif type(v) == "table" then
                            dst[k] = {{}}
                            merge(dst[k], v)
                        else
                            dst[k] = v
                        end
                    end
                end
                hl = {{
                    config = function(t) merge(state, t) end,
                    window_rule = function() end,
                    layer_rule = function() end,
                    bezier = function() end,
                    animation = function() end,
                    plugin = {{}},
                }}
                local function load_skin(skin)
                    for _, m in ipairs({{ "modules.theme", "modules.appearance", "skins.plasma.hypr.kwin" }}) do
                        package.loaded[m] = nil
                    end
                    package.preload["modules.theme"] = function() return {{ name = skin }} end
                    require("modules.appearance")
                    if skin == "plasma" then
                        require("skins.plasma.hypr.kwin")
                    end
                end

                -- 1. Breeze with KWin blur active
                load_skin("plasma")
                local b = state.decoration.blur
                assert(b.enabled == true and b.passes == 7 and b.size == 8)
                assert(b.noise == 0 and b.contrast == 1 and b.brightness == 1 and b.vibrancy == 0)

                -- 2. Switch to default (end-4): every Breeze blur key must be restored
                load_skin("default")
                b = state.decoration.blur
                assert(b.enabled == true and b.passes == 3 and b.size == 6)
                assert(math.abs(b.vibrancy - 0.2) < 1e-6)
                assert(math.abs(b.noise - 0.0117) < 1e-6)
                assert(math.abs(b.contrast - 0.8916) < 1e-6)
                assert(b.brightness == 1)

                -- 3. Switch to Retro (Omarchy): blur disabled, defaults intact
                load_skin("retro")
                b = state.decoration.blur
                assert(b.enabled == false and b.passes == 3 and b.size == 6)
                assert(math.abs(b.noise - 0.0117) < 1e-6 and math.abs(b.contrast - 0.8916) < 1e-6)
            '''
            env = dict(os.environ, XDG_STATE_HOME=state_home)
            result = subprocess.run(["lua", "-"], input=script, env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)

            # 4. Back to Breeze with blur disabled in kwinrc
            kwin_state.write_text("return { blur = false, blurStrength = 15 }\n")
            script_off = script.split("-- 1. Breeze")[0] + '\nload_skin("plasma")\nassert(state.decoration.blur.enabled == false)\n'
            result = subprocess.run(["lua", "-"], input=script_off, env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
