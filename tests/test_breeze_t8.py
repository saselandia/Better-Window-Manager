"""T8 unit tests: Breeze overview/grid/windowview actions, fallback, keybinds and KCM unlock."""
import importlib.util
import json
import os
from pathlib import Path
import socket
import threading
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
ACTIONS_PATH = ROOT / "config/hypr/skins/plasma/scripts/desktop-actions.py"
KEYBINDS_MGR = ROOT / "config/hypr/scripts/keybinds-manager.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class BreezeT8Tests(unittest.TestCase):
    def test_overview_routes_to_native_host_socket_when_available(self):
        mod = load_module("desktop_actions_t8_sock", ACTIONS_PATH)
        with tempfile.TemporaryDirectory(prefix="bwm-t8-sock-") as tmp:
            sock_path = Path(tmp) / "bwm-plasma-host.sock"
            received = []

            srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            srv.bind(str(sock_path))
            srv.listen(4)

            def accept_one():
                conn, _ = srv.accept()
                with conn:
                    received.append(conn.recv(256).decode("utf-8").strip())
                    conn.sendall(b"ok\n")

            t = threading.Thread(target=accept_one, daemon=True)
            t.start()
            try:
                mod.HOST_SOCK = sock_path
                with mock.patch.object(mod, "skin", return_value="plasma"):
                    self.assertEqual(mod.main(["grid"]), 0)
                t.join(timeout=2)
            finally:
                srv.close()
            self.assertEqual(received, ["overview-toggle grid"])

    def test_overview_falls_back_to_quickshell_without_host_socket(self):
        mod = load_module("desktop_actions_t8_fb", ACTIONS_PATH)
        with tempfile.TemporaryDirectory(prefix="bwm-t8-nosock-") as tmp:
            mod.HOST_SOCK = Path(tmp) / "missing.sock"
            with mock.patch.object(mod, "skin", return_value="plasma"), \
                 mock.patch.object(mod.bwm_session, "spawn", return_value=True) as spawn_mock:
                self.assertEqual(mod.main(["overview"]), 0)
                spawn_mock.assert_called_once()
                argv = spawn_mock.call_args.args[0]
                self.assertEqual(argv[-4:], ["ipc", "call", "overview", "toggle"])

    def test_overview_refuses_outside_breeze(self):
        mod = load_module("desktop_actions_t8_skin", ACTIONS_PATH)
        with mock.patch.object(mod, "skin", return_value="retro"):
            self.assertEqual(mod.main(["overview"]), 1)
            self.assertEqual(mod.main(["windowview-all"]), 1)

    def test_kcm_kwinscreenedges_unlocked_and_touchscreen_still_restricted(self):
        kdeglobals = (ROOT / "config/hypr/skins/plasma/settings-profile/kdeglobals").read_text()
        self.assertNotIn("kcm_kwinscreenedges=false", kdeglobals)
        self.assertIn("kcm_kwinscreenedges_x11=false", kdeglobals)
        self.assertIn("kcm_kwintouchscreen=false", kdeglobals)

    def test_factory_and_active_keybinds_are_plasma_only(self):
        mgr = load_module("keybinds_mgr_t8", KEYBINDS_MGR)
        expected = {
            "plasma_overview": (["SUPER"], "W"),
            "plasma_grid": (["SUPER"], "G"),
            "plasma_windowview": (["CTRL"], "F9"),
            "plasma_windowview_all": (["CTRL"], "F10"),
        }
        for bid, (mods, key) in expected.items():
            self.assertIn(bid, mgr.DEFAULT_DICT)
            entry = mgr.DEFAULT_DICT[bid]
            self.assertEqual(entry["skins"], ["plasma"])
            self.assertEqual(entry["mods"], mods)
            self.assertEqual(entry["key"], key)

        live = json.loads((ROOT / "config/hypr/keybinds.json").read_text())
        for action in ("overview", "grid", "windowview", "windowview-all"):
            matches = [b for b in live if (b.get("exec") or "").endswith("desktop-actions.py " + action)]
            self.assertTrue(matches, f"Missing live keybind for {action}")
            self.assertEqual(matches[0].get("skins"), ["plasma"])


if __name__ == "__main__":
    unittest.main()
