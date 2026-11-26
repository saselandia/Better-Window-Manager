#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Automated tests for Breeze III T2: kcm_bwm_input, input-manager.py, plasma-localerc LC_* loading,
and KAuthorized systemsettings profile."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
INPUT_MGR = REPO / "config" / "hypr" / "scripts" / "input-manager.py"
NATIVE_SETTINGS = REPO / "config" / "hypr" / "skins" / "plasma" / "scripts" / "native-settings.py"
ENV_LUA = REPO / "config" / "hypr" / "modules" / "environment.lua"
SETTINGS_PROFILE = REPO / "config" / "hypr" / "skins" / "plasma" / "settings-profile"


def _find_lua() -> str | None:
    for cand in ("lua5.4", "lua"):
        p = shutil.which(cand)
        if p:
            return p
    return None


class TestBreezeT2(unittest.TestCase):
    def test_input_manager_discovery_apply_and_lua_syntax(self):
        with tempfile.TemporaryDirectory(prefix="bwm-t2-input-") as td:
            hypr_dir = Path(td) / "hypr"
            hypr_dir.mkdir()
            fake_devices = {
                "mice": [
                    {"name": "semico---usb-gaming-keyboard--consumer-control-1", "defaultSpeed": 0.0},
                    {"name": "2.4g-wireless-device-1", "defaultSpeed": 0.0},
                    {"name": "elan0676:00-04f3:3195-touchpad", "defaultSpeed": 0.1},
                ]
            }
            env = {
                **os.environ,
                "BWM_INPUT_HYPR_DIR": str(hypr_dir),
                "BWM_INPUT_DEVICES_JSON": json.dumps(fake_devices),
            }
            out = subprocess.run(["python3", str(INPUT_MGR), "get"], env=env, capture_output=True, text=True, check=True)
            state = json.loads(out.stdout)
            names = [d["name"] for d in state["devices"]]
            self.assertEqual(names, ["2.4g-wireless-device-1", "elan0676:00-04f3:3195-touchpad"])
            self.assertFalse(state["devices"][0]["is_touchpad"])
            self.assertTrue(state["devices"][1]["is_touchpad"])

            payload = {
                "global": {
                    "sensitivity": -0.25,
                    "accel_profile": "flat",
                    "natural_scroll": True,
                    "left_handed": False,
                    "touchpad_natural_scroll": True,
                    "touchpad_tap_to_click": False,
                    "touchpad_disable_while_typing": True,
                },
                "devices": {
                    "2.4g-wireless-device-1": {
                        "sensitivity": 0.4,
                        "accel_profile": "adaptive",
                        "natural_scroll": False,
                        "left_handed": True,
                    },
                    "elan0676:00-04f3:3195-touchpad": {
                        "sensitivity": 0.15,
                        "accel_profile": "",
                        "natural_scroll": True,
                        "left_handed": False,
                        "tap_to_click": True,
                    },
                },
            }
            res = subprocess.run(
                ["python3", str(INPUT_MGR), "apply", json.dumps(payload), "--no-reload"],
                env=env, capture_output=True, text=True, check=True,
            )
            applied = json.loads(res.stdout)
            self.assertTrue(applied["success"])

            lua_path = hypr_dir / "modules" / "input_devices.lua"
            self.assertTrue(lua_path.is_file())

            # Validate generated Lua executes cleanly against a stub hl table
            lua_bin = _find_lua()
            if lua_bin:
                harness = (
                    "local configs, devices = {}, {}\n"
                    "hl = {\n"
                    "  config = function(t) table.insert(configs, t) end,\n"
                    "  device = function(t) table.insert(devices, t) end,\n"
                    "}\n"
                    f"dofile({json.dumps(str(lua_path))})\n"
                    "assert(#configs == 1)\n"
                    "assert(configs[1].input.accel_profile == 'flat')\n"
                    "assert(configs[1].input.natural_scroll == true)\n"
                    "assert(configs[1].input.touchpad['tap-to-click'] == false)\n"
                    "assert(#devices == 2)\n"
                )
                lr = subprocess.run([lua_bin, "-e", harness], capture_output=True, text=True)
                self.assertEqual(lr.returncode, 0, lr.stderr)

            # Reject invalid sensitivity
            bad = {"global": {"sensitivity": 9.9}}
            br = subprocess.run(
                ["python3", str(INPUT_MGR), "apply", json.dumps(bad), "--no-reload"],
                env=env, capture_output=True, text=True,
            )
            self.assertNotEqual(br.returncode, 0)

    def test_native_settings_input_roundtrip(self):
        with tempfile.TemporaryDirectory(prefix="bwm-t2-ns-") as td:
            hypr_dir = Path(td) / "hypr"
            hypr_dir.mkdir()
            fake_devices = {"mice": [{"name": "test-mouse-1", "defaultSpeed": 0.0}]}
            env = {
                **os.environ,
                "XDG_CONFIG_HOME": td,
                "XDG_STATE_HOME": str(Path(td) / "state"),
                "BWM_INPUT_HYPR_DIR": str(hypr_dir),
                "BWM_INPUT_DEVICES_JSON": json.dumps(fake_devices),
            }
            load_res = subprocess.run(
                ["python3", str(NATIVE_SETTINGS), "input", "load"],
                env=env, capture_output=True, text=True, check=True,
            )
            loaded = json.loads(load_res.stdout)
            keys = {f["key"] for f in loaded["fields"]}
            self.assertIn("global\x1fsensitivity", keys)
            self.assertIn("global\x1faccel_profile", keys)
            self.assertIn("device\x1ftest-mouse-1\x1fleft_handed", keys)
            self.assertIn("revision", loaded)

    def test_plasma_localerc_applied_without_overriding_user_lang(self):
        lua_bin = _find_lua()
        if not lua_bin:
            self.skipTest("lua interpreter not installed")
        with tempfile.TemporaryDirectory(prefix="bwm-t2-locale-") as td:
            cfg = Path(td)
            (cfg / "plasma-localerc").write_text(
                "[Formats]\n"
                "LANG=fr_FR.UTF-8\n"
                "LC_NUMERIC=en_US.UTF-8\n"
                "LC_TIME=de_DE.UTF-8\n"
                "LC_MONETARY=es_ES.UTF-8\n"
                "LC_PAPER=bad;rm -rf /\n"
                "\n[Translations]\nLANGUAGE=es\n",
                encoding="utf-8",
            )
            harness = (
                "local exported = {}\n"
                "hl = { env = function(k, v) exported[k] = v end }\n"
                f"dofile({json.dumps(str(ENV_LUA))})\n"
                "for k, v in pairs(exported) do print(k .. '=' .. tostring(v)) end\n"
            )
            # Case 1: user already has LANG=es_ES.UTF-8 -> LANG must NOT be overridden, LC_* must be exported
            env1 = {**os.environ, "XDG_CONFIG_HOME": str(cfg), "LANG": "es_ES.UTF-8"}
            r1 = subprocess.run([lua_bin, "-e", harness], env=env1, capture_output=True, text=True, check=True)
            kv1 = dict(line.split("=", 1) for line in r1.stdout.splitlines() if "=" in line)
            self.assertNotIn("LANG", kv1)
            self.assertEqual(kv1.get("LC_NUMERIC"), "en_US.UTF-8")
            self.assertEqual(kv1.get("LC_TIME"), "de_DE.UTF-8")
            self.assertEqual(kv1.get("LC_MONETARY"), "es_ES.UTF-8")
            self.assertNotIn("LC_PAPER", kv1)

            # Case 2: LANG is C -> plasma-localerc LANG may apply
            env2 = {**os.environ, "XDG_CONFIG_HOME": str(cfg), "LANG": "C"}
            r2 = subprocess.run([lua_bin, "-e", harness], env=env2, capture_output=True, text=True, check=True)
            kv2 = dict(line.split("=", 1) for line in r2.stdout.splitlines() if "=" in line)
            self.assertEqual(kv2.get("LANG"), "fr_FR.UTF-8")

            # Case 3: useDetailed=false -> LC_* not exported
            (cfg / "plasma-localerc").write_text(
                "[Formats]\nuseDetailed=false\nLC_TIME=de_DE.UTF-8\n", encoding="utf-8"
            )
            r3 = subprocess.run([lua_bin, "-e", harness], env=env1, capture_output=True, text=True, check=True)
            kv3 = dict(line.split("=", 1) for line in r3.stdout.splitlines() if "=" in line)
            self.assertNotIn("LC_TIME", kv3)

    def test_systemsettings_profile_visibility(self):
        if not shutil.which("systemsettings"):
            self.skipTest("systemsettings not installed")
        plugin_path = str(Path.home() / ".local/share/bwm/systemsettings/lib/qt6/plugins")
        env = {
            **os.environ,
            "QT_PLUGIN_PATH": plugin_path + (":" + os.environ["QT_PLUGIN_PATH"] if os.environ.get("QT_PLUGIN_PATH") else ""),
            "XDG_CONFIG_DIRS": f"{SETTINGS_PROFILE}:/etc/xdg",
            "QT_QPA_PLATFORM": "offscreen",
        }
        res = subprocess.run(["systemsettings", "--list"], env=env, capture_output=True, text=True, check=True)
        modules = {line.split()[0] for line in res.stdout.splitlines() if line.strip() and not line.startswith("The following")}
        for hidden in (
            "kcm_mouse", "kcm_touchpad", "kcm_kwinscreenedges",
            "kcm_kwintouchscreen", "kcm_touchscreen", "kcm_access",
            "kcm_smserver", "kcm_activities",
        ):
            self.assertNotIn(hidden, modules, f"{hidden} should be hidden by KAuthorized profile")
        for expected in ("kcm_bwm_input", "kcm_notifications", "kcm_regionandlang"):
            self.assertIn(expected, modules, f"{expected} should be visible")


if __name__ == "__main__":
    unittest.main()
