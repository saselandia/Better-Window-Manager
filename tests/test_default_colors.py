"""Exercise end-4's selection entry point without touching the running desktop."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DefaultColorsTests(unittest.TestCase):
    def run_selection(self, palette=None, mode="prefer-dark", enabled=True, flags=(), detected="scheme-neutral", failure=False):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            config = base / "config"
            (config / "illogical-impulse").mkdir(parents=True)
            helpers = config / "hypr/skins/default/scripts"
            helpers.mkdir(parents=True)
            image = base / "wall paper.jpg"
            image.touch()
            cfg = {"appearance": {"palette": palette or {"type": "auto", "accentColor": ""},
                    "wallpaperTheming": {"enableAppsAndShell": enabled}},
                   "background": {"wallpaperPath": str(image)}}
            target = config / "illogical-impulse/config.json"
            target.write_text(json.dumps(cfg))
            (helpers / "colors-python.sh").write_text(
                '#!/bin/bash\ncase "$1" in\n'
                ' --check) echo "colors-runtime 1";;\n'
                ' */scheme_for_image.py) echo "$DETECTED";;\n'
                ' *) echo "$*" >> "$GENERATOR_LOG";;\nesac\n')
            (helpers / "matugen-fast.py").write_text(
                'import subprocess, sys\nsys.exit(subprocess.run(["matugen", *sys.argv[1:]]).returncode)\n')
            script = base / "switchwall.sh"
            original = (ROOT / "config/quickshell/ii/scripts/colors/switchwall.sh").read_text()
            # Override only desktop side effects, retaining the real parser/selection/generation.
            script.write_text(original.rsplit('main "$@"', 1)[0] +
                              'pre_process() { :; }\nmain "$@"\n')
            apply = base / "applycolor.sh"
            apply.write_text('#!/bin/bash\nexit 0\n')
            apply.chmod(0o755)
            binaries = base / "bin"
            binaries.mkdir()
            for name, text in {
                "gsettings": '#!/bin/bash\necho "$TEST_MODE"\n',
                "matugen": '#!/bin/bash\nprintf "%s\\n" "$@" > "$MATUGEN_LOG"\nexit "$MATUGEN_STATUS"\n',
            }.items():
                path = binaries / name
                path.write_text(text)
                path.chmod(0o755)
            env = {**os.environ, "XDG_CONFIG_HOME": str(config), "XDG_STATE_HOME": str(base / "state"),
                   "PATH": str(binaries) + os.pathsep + os.environ["PATH"], "TEST_MODE": mode,
                   "DETECTED": detected, "MATUGEN_LOG": str(base / "args"), "BWM_COLORS_REQUEST": "fixture",
                   "GENERATOR_LOG": str(base / "generator"), "MATUGEN_STATUS": "1" if failure else "0"}
            result = subprocess.run(["bash", str(script), "--colors-only", *flags,
                                     *([] if "--noswitch" in flags else ["--image", str(image)])],
                                    env=env, capture_output=True, text=True)
            args = (base / "args").read_text().splitlines() if (base / "args").exists() else []
            generated = (base / "generator").exists()
            return result, args, generated, json.loads(target.read_text())

    def test_configured_scheme_and_dark_mode_reach_matugen(self):
        result, args, generated, _ = self.run_selection({"type": "scheme-fidelity"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(args[-4:], ["--mode", "dark", "--type", "scheme-fidelity"])
        self.assertTrue(generated)
        self.assertEqual(args[:3], ["--source-color-index", "0", "image"])

    def test_auto_uses_classifier_instead_of_matugen_default(self):
        result, args, _, _ = self.run_selection()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(args[-1], "scheme-neutral")

    def test_light_mode_and_explicit_scheme(self):
        _, args, _, _ = self.run_selection(mode="prefer-light", flags=("--type", "scheme-content"))
        self.assertEqual(args[-4:], ["--mode", "light", "--type", "scheme-content"])

    def test_old_disabled_option_no_longer_skips_generation(self):
        # «Shell y utilidades» se quitó: los colores se generan siempre
        result, args, generated, _ = self.run_selection(enabled=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(args)
        self.assertTrue(generated)

    def test_new_wallpaper_clears_accent_like_upstream(self):
        _, args, _, cfg = self.run_selection({"type": "auto", "accentColor": "#ff9900"})
        self.assertEqual(args[2], "image")
        self.assertEqual(cfg["appearance"]["palette"]["accentColor"], "")

    def test_noswitch_preserves_custom_accent(self):
        _, args, _, _ = self.run_selection({"type": "auto", "accentColor": "#ff9900"}, flags=("--noswitch",))
        self.assertEqual(args[2:5], ["color", "hex", "#ff9900"])

    def test_failed_matugen_does_not_claim_success(self):
        result, _, generated, _ = self.run_selection(failure=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(generated)


if __name__ == "__main__":
    unittest.main()
