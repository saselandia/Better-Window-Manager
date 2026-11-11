"""Selectores de monitor que llegan de breezebars y el booleano del plugin en kwin-tiles.py.

Hyprland guarda dos descripciones: la de `hyprctl monitors` y otra con el conector al final,
«… (DP-2)». El plugin cargado mandaba la larga y kwin-tiles.py nunca encontraba el monitor, así
que soltar una ventana en un borde no la encajaba. Además Hyprland 0.56 devuelve las opciones
booleanas de un plugin como {"bool": true}, no {"int": 1}.
"""
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "config/hypr/scripts"))
import bwm_windows  # noqa: E402

MSI = {"id": 1, "name": "DP-2", "description": "Micro-Star Int'l Co. Ltd. MAG 274Q X24 0x01010101"}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class MonitorSelectorTest(unittest.TestCase):
    def test_short_long_and_name(self):
        self.assertTrue(bwm_windows.monitor_matches(MSI, "desc:" + MSI["description"]))
        self.assertTrue(bwm_windows.monitor_matches(MSI, "desc:" + MSI["description"] + " (DP-2)"))
        self.assertTrue(bwm_windows.monitor_matches(MSI, "DP-2"))

    def test_rejects_other_monitors(self):
        self.assertFalse(bwm_windows.monitor_matches(MSI, "desc:" + MSI["description"] + " (DP-1)"))
        self.assertFalse(bwm_windows.monitor_matches(MSI, "desc:Micro-Star"))
        self.assertFalse(bwm_windows.monitor_matches(MSI, ""))
        self.assertFalse(bwm_windows.monitor_matches({"name": "", "description": ""}, "desc:"))


class KWinTilesApplyTest(unittest.TestCase):
    def run_apply(self, option):
        tiles = load("bwm_test_kwin_tiles", ROOT / "config/hypr/skins/plasma/scripts/kwin-tiles.py")
        client = {"address": "0x1", "pid": 7, "monitor": 1, "workspace": {"id": 9}}
        kw = mock.Mock()
        kw.find_client.return_value = client
        kw.hypr_json.side_effect = lambda *a: [dict(MSI, activeWorkspace={"id": 9})] if a == ("monitors",) else option
        with mock.patch.object(tiles, "module", return_value=kw), \
             mock.patch.object(tiles, "apply_frame", return_value=True) as apply:
            code = tiles.main(["apply", "0x1", "--pid", "7", "--monitor", "desc:" + MSI["description"] + " (DP-2)",
                               "--direction", "left", "--frame", "0,720,1280,1396"])
        return code, apply.called

    def test_plugin_bool_option_and_long_description(self):
        self.assertEqual(self.run_apply({"option": "plugin:breezebars:enabled", "bool": True, "set": True}), (0, True))

    def test_disabled_plugin_is_not_snapped(self):
        self.assertEqual(self.run_apply({"option": "plugin:breezebars:enabled", "bool": False, "set": True}), (1, False))
        self.assertEqual(self.run_apply({"option": "plugin:breezebars:enabled", "int": 0}), (1, False))


if __name__ == "__main__":
    unittest.main()
