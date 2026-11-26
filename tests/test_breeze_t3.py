# SPDX-License-Identifier: GPL-2.0-or-later
"""T3: publication, offline requests, stale exports and fallback in isolated XDG."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "config/hypr/scripts"
sys.path.insert(0, str(SCRIPTS))
import bwm_wallpaper


class WallpaperTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="bwm-wallpaper-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.env = {f"XDG_{kind}_HOME": str(self.root / kind.lower()) for kind in ("CONFIG", "CACHE", "STATE", "DATA")}
        self.env["XDG_RUNTIME_DIR"] = str(self.root / "runtime")
        self.environment = patch.dict(os.environ, self.env)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        cfg = Path(self.env["XDG_CONFIG_HOME"]) / "illogical-impulse"
        cfg.mkdir(parents=True)
        self.config = cfg / "config.json"
        for name in ("config.json", "config-plasma.json"):
            (cfg / name).write_text(json.dumps({"appearance": {"bwmTheme": "plasma"}, "background": {"other": 42}}))
        self.image = self.root / "fondo ñ con espacio.png"
        self.image.write_bytes(b"image")
        spec = importlib.util.spec_from_file_location("wallpaper_sync_test", ROOT / "config/hypr/skins/plasma/scripts/wallpaper-sync.py")
        self.sync = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.sync)

    def test_common_publication_preserves_fields_and_uses_still(self):
        video = self.root / "video.mp4"
        video.write_bytes(b"video")
        bwm_wallpaper.publish(str(video), str(self.image), "plasma")
        for name in ("config.json", "config-plasma.json"):
            data = json.loads(self.config.with_name(name).read_text())
            self.assertEqual(data["background"], {"other":42, "wallpaperPath":str(video), "thumbnailPath":str(self.image)})
        self.assertEqual((Path(self.env["XDG_CACHE_HOME"]) / "current_wallpaper_plasma").read_text().strip(),str(video))

    def test_common_publication_accepts_catalog_skins_and_rejects_paths(self):
        bwm_wallpaper.publish(str(self.image),str(self.image),"community-skin")
        self.assertTrue((Path(self.env["XDG_CACHE_HOME"]) / "current_wallpaper_community-skin").exists())
        with self.assertRaises(ValueError):
            bwm_wallpaper.publish(str(self.image),str(self.image),"../outside")

    def test_export_selects_primary_and_rejects_stale_generation(self):
        secondary = self.root / "secondary.png"
        secondary.write_bytes(b"other")
        state = {"hostPid": 123, "screens": [
            {"primary":False,"source":str(secondary),"still":str(secondary)},
            {"primary":True,"source":str(self.image),"still":str(self.image)}]}
        with patch.object(self.sync.host, "ready_pid", return_value=999):
            self.assertEqual(self.sync.export(state),1)
        self.assertFalse(self.sync.STATE.exists())
        with patch.object(self.sync.host,"ready_pid",return_value=123), patch.object(self.sync,"stop_engines"), patch.object(self.sync,"render_boot"):
            self.assertEqual(self.sync.export(state),0)
        self.assertEqual(json.loads(self.config.read_text())["background"]["wallpaperPath"],str(self.image))
        self.assertEqual(len(json.loads(self.sync.STATE.read_text())["screens"]),2)
        self.config.write_text('{"appearance":{"bwmTheme":"retro"}}')
        with patch.object(self.sync.host,"ready_pid",return_value=123), patch.object(self.sync,"stop_engines") as stop:
            self.assertEqual(self.sync.export(state),1)
            stop.assert_not_called()

    def test_offline_request_replayed_without_flattening_skin_entry(self):
        with patch.object(self.sync.host,"host_ctl",return_value=None):
            self.assertEqual(self.sync.route(str(self.image)),1)
        pending = json.loads(self.sync.PENDING.read_text())
        self.assertEqual(pending["source"],str(self.image))
        with patch.object(self.sync.host,"ready_pid",return_value=123), patch.object(self.sync.host,"host_ctl",side_effect=['{"version":1}',"ok"]) as ctl, patch.object(self.sync,"stop_engines"):
            self.assertEqual(self.sync.resume(),0)
            self.assertEqual(json.loads(ctl.call_args.args[0].split(" ",1)[1]),pending)
        self.assertFalse(self.sync.PENDING.exists())
        with patch.dict(os.environ,{"BWM_SKIN_SWITCH":"1"}), patch.object(self.sync.host,"host_ctl") as ctl:
            self.assertEqual(self.sync.route(str(self.image)),1)
            ctl.assert_not_called()
        self.assertFalse(self.sync.PENDING.exists())

    def test_successful_route_does_not_extract_palette(self):
        with patch.object(self.sync.host,"host_ctl",return_value="ok"), patch.object(self.sync,"stop_engines") as stop, patch.object(self.sync,"render_boot") as boot:
            self.assertEqual(self.sync.route(str(self.image)),0)
        stop.assert_called_once()
        boot.assert_called_once()
        self.assertEqual(json.loads(self.config.read_text())["appearance"],{"bwmTheme":"plasma"})

    def test_fallback_never_starts_with_live_host_or_other_skin(self):
        with patch.object(self.sync.host,"ready_pid",return_value=123), patch.object(self.sync.subprocess,"run") as run:
            self.assertEqual(self.sync.fallback(),0)
            run.assert_not_called()
        self.config.write_text('{"appearance":{"bwmTheme":"default"}}')
        with patch.object(self.sync.subprocess,"run") as run:
            self.assertEqual(self.sync.fallback(),0)
            run.assert_not_called()

    def test_stale_ready_file_does_not_hide_fallback(self):
        runtime=Path(self.env["XDG_RUNTIME_DIR"])
        runtime.mkdir()
        (runtime / "bwm-plasma-host.ready").write_text("9999999999")
        self.assertFalse(bwm_wallpaper.native_plasma_ready())

    def test_native_host_false_routes_to_fallback_even_with_ready_marker(self):
        data=json.loads(self.config.read_text())
        data["bar"]={"plasma":{"nativeHost":False}}
        self.config.write_text(json.dumps(data))
        with patch.object(self.sync.host,"ready_pid",return_value=123), patch.object(self.sync.host,"host_ctl") as ctl:
            self.assertEqual(self.sync.route(str(self.image)),1)
            self.assertEqual(self.sync.resume(),1)
            self.assertEqual(self.sync.export({"hostPid":123,"screens":[]}),1)
            ctl.assert_not_called()


if __name__ == "__main__": unittest.main()
