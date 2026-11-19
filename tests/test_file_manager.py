"""Tests for per-skin/fixed file manager selection, launcher, keybinds, and Retro Nautilus plugins."""

import importlib.util
import json
import os
import py_compile
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "config" / "hypr" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import bwm_skins  # noqa: E402


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FAKE_ENTRIES = {
    "org.kde.dolphin.desktop": ("Dolphin", ["Qt", "KDE", "System", "FileManager"], "dolphin %u"),
    "org.gnome.Nautilus.desktop": ("Files", ["GNOME", "GTK", "FileManager"], "nautilus --new-window %U"),
    "thunar.desktop": ("Thunar", ["GTK", "FileManager"], "thunar %F"),
}


class FileManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cfg = Path(self.tmp.name) / "config"
        self.data = Path(self.tmp.name) / "share"
        self.cfg.mkdir(parents=True)
        self.data.mkdir(parents=True)
        self.env = mock.patch.dict(os.environ, {
            "XDG_CONFIG_HOME": str(self.cfg),
            "XDG_DATA_HOME": str(self.data),
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.da = load_module("default_apps_test", SCRIPTS / "default-apps.py")

    def _set_skin(self, skin_id: str):
        qs = self.cfg / "illogical-impulse" / "config.json"
        qs.parent.mkdir(parents=True, exist_ok=True)
        qs.write_text(json.dumps({"appearance": {"bwmTheme": skin_id}}), encoding="utf-8")

    def test_skin_manifests_declare_expected_file_managers(self):
        self.assertEqual(bwm_skins.file_manager("default"), "org.kde.dolphin.desktop")
        self.assertEqual(bwm_skins.file_manager("plasma"), "org.kde.dolphin.desktop")
        self.assertEqual(bwm_skins.file_manager("retro"), "org.gnome.Nautilus.desktop")
        self.assertEqual(bwm_skins.file_manager("nonexistent"), "org.kde.dolphin.desktop")

    def test_per_skin_and_fixed_modes_and_apply_skin(self):
        self._set_skin("default")
        mime_calls = []
        current_mime = {"inode/directory": "org.gnome.Nautilus.desktop"}

        def fake_query(mime):
            return current_mime.get(mime, "")

        def fake_set(desktop, mime):
            mime_calls.append((desktop, mime))
            current_mime[mime] = desktop

        with mock.patch.object(self.da, "desktop_entries", return_value=FAKE_ENTRIES), \
             mock.patch.object(self.da, "_query_xdg_mime", side_effect=fake_query), \
             mock.patch.object(self.da, "_set_xdg_mime", side_effect=fake_set), \
             mock.patch("bwm_settings_hooks.changed"):

            # Default mode is per-skin
            listed = self.da.build_list(["files"])["files"]
            self.assertEqual(listed["mode"], "per-skin")
            self.assertEqual(listed["current"], "per-skin")
            self.assertEqual(listed["effective"], "org.kde.dolphin.desktop")
            self.assertEqual(listed["options"][0]["id"], "per-skin")
            self.assertTrue(any(o["id"] == "org.gnome.Nautilus.desktop" and "Nautilus" in o["name"] for o in listed["options"]))

            # apply-skin switches inode/directory per skin
            res_def = self.da.apply_skin_files("default")
            self.assertEqual(res_def["desktop"], "org.kde.dolphin.desktop")
            self.assertTrue(res_def["changed"])
            self.assertEqual(current_mime["inode/directory"], "org.kde.dolphin.desktop")

            res_retro = self.da.apply_skin_files("retro")
            self.assertEqual(res_retro["desktop"], "org.gnome.Nautilus.desktop")
            self.assertTrue(res_retro["changed"])
            self.assertEqual(current_mime["inode/directory"], "org.gnome.Nautilus.desktop")

            res_plasma = self.da.apply_skin_files("plasma")
            self.assertEqual(res_plasma["desktop"], "org.kde.dolphin.desktop")
            self.assertTrue(res_plasma["changed"])

            # Fixing a single file manager keeps it across skins
            self.da.cmd_set("files", "org.kde.dolphin.desktop")
            self.assertEqual(self.da.build_list(["files"])["files"]["mode"], "fixed")
            self.assertEqual(self.da.build_list(["files"])["files"]["current"], "org.kde.dolphin.desktop")

            mime_calls.clear()
            res_fixed_retro = self.da.apply_skin_files("retro")
            self.assertEqual(res_fixed_retro["mode"], "fixed")
            self.assertEqual(res_fixed_retro["desktop"], "org.kde.dolphin.desktop")
            self.assertFalse(res_fixed_retro["changed"])
            self.assertEqual(mime_calls, [])

            # Switching back to per-skin resumes per-skin resolution
            self._set_skin("retro")
            self.da.cmd_set("files", "per-skin")
            self.assertEqual(current_mime["inode/directory"], "org.gnome.Nautilus.desktop")
            self.assertEqual(self.da.resolve_files("retro")["desktop"], "org.gnome.Nautilus.desktop")
            self.assertEqual(self.da.resolve_files("plasma")["desktop"], "org.kde.dolphin.desktop")

    def test_fallback_when_preferred_manager_is_not_installed(self):
        only_dolphin = {"org.kde.dolphin.desktop": FAKE_ENTRIES["org.kde.dolphin.desktop"]}
        with mock.patch.object(self.da, "desktop_entries", return_value=only_dolphin):
            self.assertEqual(self.da.skin_file_manager("retro", only_dolphin), "org.kde.dolphin.desktop")

    def test_bwm_file_manager_print_resolves_per_skin(self):
        out_def = json.loads(subprocess.check_output(
            [str(SCRIPTS / "bwm-file-manager"), "--skin", "default", "--print"],
            text=True,
            env={**os.environ, "XDG_CONFIG_HOME": str(self.cfg)},
        ))
        out_retro = json.loads(subprocess.check_output(
            [str(SCRIPTS / "bwm-file-manager"), "--skin", "retro", "--print"],
            text=True,
            env={**os.environ, "XDG_CONFIG_HOME": str(self.cfg)},
        ))
        out_plasma = json.loads(subprocess.check_output(
            [str(SCRIPTS / "bwm-file-manager"), "--skin", "plasma", "--print"],
            text=True,
            env={**os.environ, "XDG_CONFIG_HOME": str(self.cfg)},
        ))
        self.assertEqual(out_def["desktop"], "org.kde.dolphin.desktop")
        self.assertEqual(out_plasma["desktop"], "org.kde.dolphin.desktop")
        self.assertEqual(out_retro["desktop"], "org.gnome.Nautilus.desktop")
        self.assertEqual(out_def["command"][0], "dolphin")
        self.assertEqual(out_retro["command"][0], "nautilus")

    def test_keybinds_alt_e_and_super_e_use_bwm_file_manager(self):
        kb = json.loads((ROOT / "config/hypr/keybinds.json").read_text(encoding="utf-8"))
        by_id = {entry["id"]: entry for entry in kb}
        self.assertTrue(by_id["file_manager"]["exec"].endswith("/bwm-file-manager"))
        self.assertTrue(by_id["file_manager_alt"]["exec"].endswith("/bwm-file-manager"))
        self.assertEqual(by_id["file_manager_alt"]["mods"], ["ALT"])
        self.assertEqual(by_id["file_manager_alt"]["key"], "E")
        self.assertTrue(by_id["file_manager_alt"]["enabled"])

    def test_retro_nautilus_extensions_install_safely_and_compile(self):
        ext_src = ROOT / "config/hypr/skins/retro/nautilus-python/extensions"
        for name in ("localsend.py", "transcode.py"):
            py_compile.compile(str(ext_src / name), doraise=True)

        installer = ROOT / "config/hypr/skins/retro/scripts/setup-nautilus-plugins.sh"
        dst_dir = self.data / "nautilus-python" / "extensions"
        dst_dir.mkdir(parents=True)
        # User custom file and user override must not be overwritten
        (dst_dir / "custom.py").write_text("# user plugin\n", encoding="utf-8")
        (dst_dir / "localsend.py").write_text("# user override\n", encoding="utf-8")

        subprocess.run(
            ["bash", str(installer)],
            check=True,
            env={**os.environ, "XDG_DATA_HOME": str(self.data)},
        )
        self.assertTrue((dst_dir / "transcode.py").is_symlink())
        self.assertEqual((dst_dir / "transcode.py").resolve(), (ext_src / "transcode.py").resolve())
        self.assertFalse((dst_dir / "localsend.py").is_symlink())
        self.assertEqual((dst_dir / "localsend.py").read_text(encoding="utf-8"), "# user override\n")
        self.assertEqual((dst_dir / "custom.py").read_text(encoding="utf-8"), "# user plugin\n")


if __name__ == "__main__":
    unittest.main()
