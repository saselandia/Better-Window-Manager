"""Color publication must finish before slow app hooks, with no second Kitty palette."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("fast_colors", ROOT / "config/hypr/skins/default/scripts/matugen-fast.py")
fast = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fast)


class PaletteApplyTests(unittest.TestCase):
    def test_template_roundtrip_preserves_options_and_multiline_hooks(self):
        data = {"config": {"reload_apps": True, "custom_colors": [{"name": "x", "color": "#123456"}]},
                "templates": {"custom.plugin": {"input_path": "a b", "post_hook": "echo a\necho b"}}}
        self.assertEqual(tomllib.loads(fast.toml_dump(data)), data)

    def test_shell_published_before_detached_hooks_and_kitty_has_one_owner(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config"
            state = Path(directory) / "state"
            (config / "matugen").mkdir(parents=True)
            (config / "illogical-impulse").mkdir()
            (config / "illogical-impulse/config.json").write_text(json.dumps({"appearance": {"bwmTheme": "default"}}))
            data = {"config": {"reload_apps": True}, "templates": {
                "quickshell_colors": {"input_path": "shell", "post_hook": "theme hook"},
                "hyprland_colors": {"input_path": "hypr", "post_hook": "hypr hook"},
                "kitty": {"input_path": "kitty", "post_hook": "kitty hook"},
                "custom": {"input_path": "custom", "post_hook": "slow custom hook"}}}
            (config / "matugen/config.toml").write_text(fast.toml_dump(data))
            order = []

            def run(argv, **kwargs):
                order.append(argv[0])
                if argv[0] == "matugen":
                    generated = tomllib.loads(Path(argv[-1]).read_text())
                    self.assertNotIn("kitty", generated["templates"])
                    self.assertIn("custom", generated["templates"])
                    self.assertTrue(all("post_hook" not in t for t in generated["templates"].values()))

            def popen(argv, **kwargs):
                order.append("hooks")
                self.assertEqual(json.loads(argv[-1])["hooks"], ["slow custom hook"])
                self.assertTrue(kwargs["start_new_session"])

            with patch.object(fast, "CONFIG", config), patch.object(fast, "STATE", state), \
                    patch.dict("os.environ", {}, clear=True), \
                    patch.object(fast.subprocess, "run", side_effect=run), \
                    patch.object(fast.subprocess, "Popen", side_effect=popen):
                fast.apply(["image", "wallpaper"])
            self.assertEqual(order, ["matugen", "quickshell", "hyprctl", "hooks"])

    def test_superseded_hooks_and_hooks_after_skin_switch_do_not_run(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            (state / "request").write_text("new")
            with patch.object(fast, "STATE", state), patch.object(fast.subprocess, "run") as run:
                fast.run_hooks({"token": "old", "hooks": ["must not run"]})
                run.assert_not_called()

    def test_rapid_requests_skip_obsolete_queued_wallpaper(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            config = base / "config/illogical-impulse"
            config.mkdir(parents=True)
            (config / "config.json").write_text('{"appearance":{"bwmTheme":"default"}}')
            command = base / "change.sh"
            command.write_text('echo "$1" >> "$TEST_RESULTS"\n'
                               'if [[ "$1" == first ]]; then touch "$TEST_STARTED"; '
                               'while [[ ! -f "$TEST_RELEASE" ]]; do sleep 0.02; done; fi\n')
            env = {**os.environ, "XDG_CONFIG_HOME": str(base / "config"),
                   "XDG_STATE_HOME": str(base / "state"), "TEST_RESULTS": str(base / "results"),
                   "TEST_STARTED": str(base / "started"), "TEST_RELEASE": str(base / "release")}
            env.pop("BWM_COLORS_REQUEST", None)
            request = base / "state/bwm/default-colors/request"

            def wait_for(predicate):
                deadline = time.monotonic() + 5
                while not predicate():
                    self.assertLess(time.monotonic(), deadline)
                    time.sleep(0.01)

            def start(name):
                return subprocess.Popen([sys.executable, str(Path(fast.__file__)), "--request", str(command), name], env=env)

            processes = []
            try:
                processes.append(start("first"))
                wait_for(lambda: (base / "started").exists())
                first_token = request.read_text()
                processes.append(start("obsolete"))
                wait_for(lambda: request.read_text() != first_token)
                second_token = request.read_text()
                processes.append(start("latest"))
                wait_for(lambda: request.read_text() != second_token)
                (base / "release").touch()
                self.assertEqual([p.wait(timeout=5) for p in processes], [0, 0, 0])
                self.assertEqual((base / "results").read_text().splitlines(), ["first", "latest"])
            finally:
                (base / "release").touch()
                for process in processes:
                    if process.poll() is None:
                        process.kill()
                    process.wait()


if __name__ == "__main__":
    unittest.main()
