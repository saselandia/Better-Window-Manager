"""Retro collections and Omarchy's file-selection protocol, without the live shell."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "config/hypr/skins/retro/scripts/wallpaper-picker.py"
spec = importlib.util.spec_from_file_location("retro_wallpapers", SCRIPT)
picker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(picker)


class CollectionsTest(unittest.TestCase):
    def test_static_theme_custom_backgrounds_and_shared_collection(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            config = home / "config"
            theme = home / "installed-community-theme"
            expected = [theme / "backgrounds", config / "omarchy/backgrounds/custom", home / "Pictures/Wallpapers"]
            for directory in expected:
                directory.mkdir(parents=True)
            with patch.object(picker.omarchy, "HOME", home), patch.object(picker.omarchy, "CONFIG_DIR", config), \
                 patch.object(picker.omarchy, "get_retro_mode", return_value=("static", "custom")), \
                 patch.object(picker.omarchy, "theme_directory", return_value=theme) as resolve:
                self.assertEqual(picker.background_directories(), expected)
                resolve.assert_called_once_with("custom")

    def test_dynamic_mode_ignores_stale_generated_theme_backgrounds(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            shared = home / "Pictures/Wallpapers"
            shared.mkdir(parents=True)
            with patch.object(picker.omarchy, "HOME", home), patch.object(picker.omarchy, "CONFIG_DIR", home / "config"), \
                 patch.object(picker.omarchy, "get_retro_mode", return_value=("dynamic", "dynamic")), \
                 patch.object(picker.omarchy, "theme_directory") as resolve:
                self.assertEqual(picker.background_directories(), [shared])
                resolve.assert_not_called()

    def test_removed_theme_still_offers_shared_wallpapers(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            shared = home / "Pictures/Wallpapers"
            shared.mkdir(parents=True)
            with patch.object(picker.omarchy, "HOME", home), patch.object(picker.omarchy, "CONFIG_DIR", home / "config"), \
                 patch.object(picker.omarchy, "get_retro_mode", return_value=("static", "removed")), \
                 patch.object(picker.omarchy, "theme_directory", side_effect=ValueError):
                self.assertEqual(picker.background_directories(), [shared])


class ApplyTest(unittest.TestCase):
    def test_selection_uses_the_shared_setter_with_a_literal_path(self):
        selected = "/tmp/Fondo café con espacios.png"
        answers = [subprocess.CompletedProcess([], 0, selected + "\n", ""),
                   subprocess.CompletedProcess([], 0, "retro\n", ""),
                   subprocess.CompletedProcess([], 0)]
        with patch.object(picker.sys, "argv", [str(SCRIPT)]), \
             patch.object(picker, "background_directories", return_value=[Path("/tmp")]), \
             patch.object(picker, "current_background", return_value=""), \
             patch.object(picker.subprocess, "run", side_effect=answers) as run:
            self.assertEqual(picker.main(), 0)
            self.assertEqual(run.call_args.args[0],
                             [str(picker.SCRIPTS / "omarchy-shims/omarchy-theme-bg-set"), selected])

    def test_switching_skin_while_choosing_does_not_apply_to_the_new_skin(self):
        answers = [subprocess.CompletedProcess([], 0, "/tmp/background.png\n", ""),
                   subprocess.CompletedProcess([], 0, "plasma\n", "")]
        with patch.object(picker.sys, "argv", [str(SCRIPT)]), \
             patch.object(picker, "background_directories", return_value=[Path("/tmp")]), \
             patch.object(picker, "current_background", return_value=""), \
             patch.object(picker.subprocess, "run", side_effect=answers) as run:
            self.assertEqual(picker.main(), 0)
            self.assertEqual(run.call_count, 2)


@unittest.skipUnless(shutil.which("magick"), "ImageMagick is needed for real thumbnail tests")
class ImageProtocolTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.images = self.folder / "images"
        self.images.mkdir()
        self.script = self.folder / "omarchy-menu-images"
        shutil.copy2(ROOT / "config/hypr/scripts/omarchy-shims/omarchy-menu-images", self.script)
        # The only IPC endpoint is a local fake; no live shell or wallpaper action.
        ipc = self.folder / "omarchy-shell"
        ipc.write_text('''#!/usr/bin/env python3
import base64, json, os, pathlib, sys
a = sys.argv[1:]
rows = base64.b64decode(a[3]).decode("utf-8").splitlines()
pathlib.Path(os.environ["BWM_TEST_REQUEST"]).write_text(json.dumps({"rows":rows,"selected":a[4]}))
if os.environ.get("BWM_TEST_CANCEL") != "1":
    pathlib.Path(a[5]).write_text(rows[-1].split("\\t")[0]+"\\n")
pathlib.Path(a[6]).touch()
print("ok")
''')
        ipc.chmod(0o755)
        self.env = {**os.environ, "XDG_CACHE_HOME": str(self.folder / "cache"),
                    "BWM_TEST_REQUEST": str(self.folder / "request.json")}

    def image(self, name, color="red"):
        path = self.images / name
        subprocess.run(["magick", "-size", "64x40", "xc:" + color, str(path)], check=True)
        return path

    def run_picker(self, *args):
        return subprocess.run([str(self.script), *map(str, args), str(self.images)],
                              env=self.env, text=True, capture_output=True, check=True, timeout=15).stdout

    def test_unicode_filename_and_selection_round_trip(self):
        path = self.image("Fondo café con espacios.png")
        self.assertEqual(self.run_picker("--selected", path).rstrip("\n"), str(path))
        request = json.loads((self.folder / "request.json").read_text())
        self.assertEqual(request["selected"], str(path))
        image, thumbnail = request["rows"][0].split("\t")
        self.assertEqual(image, str(path))
        self.assertTrue(Path(thumbnail).is_file())

    def test_cancel_returns_no_selection(self):
        self.image("background.png")
        self.env["BWM_TEST_CANCEL"] = "1"
        self.assertEqual(self.run_picker(), "")

    def test_empty_collection_does_not_open_an_invisible_overlay(self):
        self.assertEqual(self.run_picker(), "")
        self.assertFalse((self.folder / "request.json").exists())

    def test_replaced_image_gets_a_new_thumbnail_without_directory_changes(self):
        path = self.image("background.png")
        before = self.run_picker("--print-rows").strip().split("\t")[1]
        self.image(path.name, "blue")
        stamp = path.stat().st_mtime + 2
        os.utime(path, (stamp, stamp))
        after = self.run_picker("--print-rows").strip().split("\t")[1]
        self.assertNotEqual(before, after)
        self.assertTrue(Path(after).is_file())

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg is needed for video previews")
    def test_video_has_a_real_image_thumbnail(self):
        video = self.images / "animated.mp4"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i",
                        "color=blue:s=64x40:d=0.1", "-y", str(video)], check=True)
        row = self.run_picker("--print-rows").strip().split("\t")
        self.assertEqual(row[0], str(video))
        subprocess.run(["magick", "identify", row[1]], check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
