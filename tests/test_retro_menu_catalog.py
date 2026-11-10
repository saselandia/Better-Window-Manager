import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "config/hypr/omarchy/bwm-menu.jsonc"
SHIMS = ROOT / "config/hypr/scripts/omarchy-shims"
MISC = ROOT / "config/hypr/skins/retro/hypr/misc.lua"
TOGGLES = ROOT / "config/quickshell/ii/Commons/omarchy/default/hypr/toggles"
I18N = ROOT / "config/quickshell/ii/Commons/omarchy/default/i18n"


def load_catalog():
    # Same reading as the menu: only whole-line // comments, and a duplicated id would silently
    # replace the first one, so it is an error here.
    text = "\n".join(l for l in CATALOG.read_text().splitlines() if not l.lstrip().startswith("//"))

    def no_duplicates(pairs):
        ids = [k for k, _ in pairs]
        duplicated = sorted({k for k in ids if ids.count(k) > 1})
        if duplicated:
            raise AssertionError(f"ids repetidos en el catálogo: {duplicated}")
        return dict(pairs)

    return json.loads(text, object_pairs_hook=no_duplicates)


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog()

    def test_every_entry_has_its_parent_and_every_link_its_target(self):
        orphans = [k for k in self.catalog if "." in k and k.rsplit(".", 1)[0] not in self.catalog]
        broken = [(k, v["target"]) for k, v in self.catalog.items() if v.get("target") and v["target"] not in self.catalog]
        self.assertEqual(orphans, [])
        self.assertEqual(broken, [])

    def test_omarchy_commands_used_by_entries_exist_as_shims(self):
        shims = {p.name for p in SHIMS.iterdir()}
        missing = {}
        for entry_id, entry in self.catalog.items():
            for field in ("action", "when", "checked", "disabled"):
                for command in re.findall(r"(?<![/\w-])omarchy-[a-z0-9][a-z0-9-]*", entry.get(field, "")):
                    if command not in shims:
                        missing.setdefault(command, []).append(entry_id)
        self.assertEqual(missing, {})

    def test_bar_menu_follows_omarchys(self):
        bar = self.catalog
        self.assertEqual({k for k in bar if k.startswith("appearance.top-bar.") and k.count(".") == 2},
                         {"appearance.top-bar.hide", "appearance.top-bar.show", "appearance.top-bar.position",
                          "appearance.top-bar.background", "appearance.top-bar.indicators", "appearance.top-bar.settings"})
        for position in ("top", "bottom", "left", "right"):
            self.assertIn(f"omarchy-bar position {position}", bar[f"appearance.top-bar.position.{position}"]["action"])
        for background, command in (("opaque", "opaque"), ("glassy", "glassy"), ("clear", "none")):
            self.assertIn(f"omarchy-bar background {command}", bar[f"appearance.top-bar.background.{background}"]["action"])
        # hide and show are the same toggle, each visible in one state only
        self.assertEqual(bar["appearance.top-bar.hide"]["action"], bar["appearance.top-bar.show"]["action"])
        self.assertNotEqual(bar["appearance.top-bar.hide"]["when"], bar["appearance.top-bar.show"]["when"])

    def test_laptop_only_entries_wait_for_a_battery(self):
        for entry_id in ("appearance.top-bar.indicators.battery-percentage-on", "appearance.top-bar.indicators.battery-percentage-off"):
            self.assertIn("omarchy-battery-present", self.catalog[entry_id]["when"])
            self.assertNotIn("omarchy-hw-laptop", self.catalog[entry_id]["when"])

    def test_clock_formats_are_only_offered_for_the_bar_orientation_that_uses_them(self):
        for entry_id, entry in self.catalog.items():
            if entry_id.startswith("appearance.top-bar.indicators.clock.") and entry.get("action"):
                key = "verticalFormat" if "stacked" in entry_id else "format"
                self.assertIn(f"omarchy-bar set omarchy.clock {key} ", entry["action"], entry_id)

    def test_branding_needs_what_it_runs(self):
        self.assertIn("fastfetch", self.catalog["appearance.branding.about"]["when"])
        self.assertIn("omarchy-screensaver", self.catalog["appearance.branding.screensaver"]["when"])
        for part in ("about", "screensaver"):
            self.assertIn("magick", self.catalog[f"appearance.branding.{part}.image"]["when"])

    def test_language_comes_from_the_languages_provider(self):
        self.assertEqual(self.catalog["setup.language"]["provider"], "languages")


class ShimTests(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="bwm-test-")
        self.addCleanup(shutil.rmtree, self.home, True)
        self.bin = Path(self.home) / "bin"
        self.bin.mkdir()
        self.calls = Path(self.home) / "calls"
        for name in ("hyprctl", "omarchy-shell", "omarchy-notification-send"):
            stub = self.bin / name
            stub.write_text(f'#!/bin/bash\necho "{name} $*" >> "{self.calls}"\n')
            stub.chmod(0o755)
        self.env = {
            "HOME": self.home,
            "PATH": f"{self.bin}:{SHIMS}:/usr/bin:/bin",
            "OMARCHY_PATH": str(ROOT / "config/hypr/omarchy"),
        }

    def run_shim(self, *args):
        return subprocess.run(list(args), env=self.env, capture_output=True, text=True)

    def state(self, *parts):
        return Path(self.home, ".local/state/omarchy", *parts)

    def test_toggle_flag_round_trip(self):
        self.assertNotEqual(self.run_shim("omarchy-toggle-enabled", "bar-off").returncode, 0)
        self.run_shim("omarchy-toggle-bar")
        self.assertEqual(self.run_shim("omarchy-toggle-enabled", "bar-off").returncode, 0)
        self.run_shim("omarchy-toggle-bar")
        self.assertNotEqual(self.run_shim("omarchy-toggle-enabled", "bar-off").returncode, 0)
        # the shell is nudged to read the flag, as upstream does
        self.assertIn("-q omarchy.bar syncHidden", self.calls.read_text())

    def test_animations_toggle_copies_and_removes_the_hyprland_flag(self):
        flag = self.state("toggles/hypr/no-animations.lua")
        self.assertNotEqual(self.run_shim("omarchy-hyprland-animations-off").returncode, 0)  # animations start on
        self.assertEqual(self.run_shim("omarchy-toggle-animations", "off").returncode, 0)
        self.assertTrue(flag.is_file())
        self.assertEqual(flag.read_text(), (TOGGLES / "no-animations.lua").read_text())
        self.assertEqual(self.run_shim("omarchy-hyprland-animations-off").returncode, 0)
        self.assertEqual(self.run_shim("omarchy-toggle-animations", "on").returncode, 0)
        self.assertFalse(flag.exists())
        self.assertIn("hyprctl", self.calls.read_text())  # Hyprland is reloaded each time

    def test_language_lists_only_what_bwm_translates(self):
        rows = [r.split("\t") for r in self.run_shim("omarchy-language", "list").stdout.splitlines()]
        translated = sorted(p.name for p in I18N.iterdir() if p.is_dir())
        self.assertEqual(sorted(r[1] for r in rows), translated)
        self.assertEqual(rows[0][1], "en")

    def test_language_set_writes_the_file_the_shell_watches(self):
        self.assertEqual(self.run_shim("omarchy-language").stdout.strip(), "en")
        self.assertEqual(self.run_shim("omarchy-language", "es-MX").returncode, 0)
        self.assertEqual(Path(self.home, ".config/omarchy/language").read_text().strip(), "es-MX")
        self.assertEqual(self.run_shim("omarchy-language").stdout.strip(), "es-MX")
        refused = self.run_shim("omarchy-language", "xx")
        self.assertNotEqual(refused.returncode, 0)
        self.assertEqual(Path(self.home, ".config/omarchy/language").read_text().strip(), "es-MX")

    def test_branding_reset_removes_the_users_copy_and_text_seeds_it_from_the_default(self):
        for name in ("omarchy-launch-about",):
            stub = self.bin / name
            stub.write_text("#!/bin/bash\nexit 0\n")
            stub.chmod(0o755)
        branding = Path(self.home, ".config/omarchy/branding/about.txt")
        branding.parent.mkdir(parents=True)
        branding.write_text("mine")
        self.assertEqual(self.run_shim("omarchy-branding-about", "reset").returncode, 0)
        self.assertFalse(branding.exists())
        self.assertNotEqual(self.run_shim("omarchy-branding-about", "nonsense").returncode, 0)


@unittest.skipUnless(shutil.which("lua"), "lua no está instalado")
class RetroToggleLoaderTests(unittest.TestCase):
    def loaded(self, flags):
        home = tempfile.mkdtemp(prefix="bwm-test-")
        self.addCleanup(shutil.rmtree, home, True)
        flag_dir = Path(home, ".local/state/omarchy/toggles/hypr")
        flag_dir.mkdir(parents=True)
        for name in flags:
            # each flag announces itself when Hyprland would read it
            (flag_dir / f"{name}.lua").write_text(f'LOADED[#LOADED + 1] = "{name}"\n')
        script = (
            f'HOME = {json.dumps(home)}\nLOADED = {{}}\n'
            'os.getenv = (function(real) return function(k) if k == "HOME" then return HOME end if k == "XDG_STATE_HOME" then return nil end return real(k) end end)(os.getenv)\n'
            'hl = { config = function() end, get_config = function() return nil end }\n'
            f'dofile({json.dumps(str(MISC))})\n'
            'print(table.concat(LOADED, ","))\n'
        )
        out = subprocess.run(["lua", "-e", script], capture_output=True, text=True, check=True).stdout.strip()
        return out.split(",") if out else []

    def test_reads_the_toggles_bwm_supports(self):
        self.assertEqual(self.loaded(["no-animations", "bar-glassy"]), ["bar-glassy", "no-animations"])

    def test_ignores_toggles_that_need_pieces_bwm_does_not_have(self):
        self.assertEqual(self.loaded(["window-glassy", "window-no-gaps"]), [])


if __name__ == "__main__":
    unittest.main()
