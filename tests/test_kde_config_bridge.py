"""Bridge authority, lossless updates, conflicts, atomic saves and watcher behaviour."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "config/hypr/skins/plasma/scripts/kde-config-bridge.py"


class BridgeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = self.root / "config"
        self.state = self.root / "state/bwm/plasma"
        self.env = mock.patch.dict(os.environ, {
            "XDG_CONFIG_HOME": str(self.config), "XDG_STATE_HOME": str(self.root / "state"),
            "XDG_DATA_HOME": str(self.root / "data"), "XDG_CONFIG_DIRS": str(self.root / "system"),
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        spec = importlib.util.spec_from_file_location("kde_bridge_test", SCRIPT)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.options = self.config / "illogical-impulse/config.json"
        self.write(self.options, json.dumps({
            "appearance": {"bwmTheme": "plasma", "fonts": {"main": "BWM Sans", "title": "BWM Title"}},
            "bar": {"workspaces": {"shown": 6}}, "language": {"ui": "es_ES"},
            "apps": {"terminal": "kitty -1"}, "unknown": {"keep": 42},
        }))
        self.write(self.config / "hypr/modules/cursor.lua",
                   'hl.env("XCURSOR_THEME", "User-Cursor")\nhl.env("XCURSOR_SIZE", "32")\n')
        self.run = mock.patch.object(self.m, "run", return_value=subprocess.CompletedProcess([], 0, "", ""))
        self.calls = self.run.start()
        self.addCleanup(self.run.stop)

    def write(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def kde(self, file):
        return self.m.ini(self.m.read(self.config / file))

    def test_round_trip_shared_settings_preserves_foreign_keys(self):
        foreign = "# A comment\n[Mouse]\ncursorTheme=Before\nForeign=untouched\n\n[Other][Nested]\nK[$e]=value\n"
        self.write(self.config / "kcminputrc", foreign)
        self.m.enter()
        self.assertEqual(self.kde("kcminputrc")["Mouse"]["cursorTheme"], "User-Cursor")
        self.assertEqual(self.kde("kcminputrc")["Mouse"]["cursorSize"], "32")
        self.assertEqual(self.kde("kwinrc")["Desktops"]["Number"], "6")
        self.assertEqual(self.kde("plasma-localerc")["Translations"]["LANGUAGE"], "es_ES")
        # A shared KDE edit loses to BWM; its unknown neighbours survive.
        self.write(self.config / "kcminputrc", self.m.read(self.config / "kcminputrc").replace("User-Cursor", "KDE-Cursor") + "\n[Extra]\nX=Y\n")
        self.m.reconcile()
        self.assertEqual(self.kde("kcminputrc")["Mouse"]["cursorTheme"], "User-Cursor")
        self.m.leave()
        restored = self.m.read(self.config / "kcminputrc")
        self.assertIn("# A comment", restored)
        self.assertIn("K[$e]=value", restored)
        self.assertEqual(self.kde("kcminputrc")["Mouse"]["cursorTheme"], "Before")
        self.assertNotIn("cursorSize", self.kde("kcminputrc")["Mouse"])
        self.assertEqual(self.kde("kcminputrc")["Extra"]["X"], "Y")

    def test_leave_does_not_undo_concurrent_foreign_edit(self):
        self.write(self.config / "kcminputrc", "[Mouse]\ncursorTheme=Before\n")
        self.m.enter()
        self.write(self.config / "kcminputrc", self.m.read(self.config / "kcminputrc").replace("User-Cursor", "NewExternalValue"))
        self.m.leave()
        self.assertEqual(self.kde("kcminputrc")["Mouse"]["cursorTheme"], "NewExternalValue")

    def test_atomic_rejects_stale_input_and_preserves_symlink(self):
        target = self.root / "real/foreign.ini"
        self.write(target, "newer")
        link = self.config / "foreign.ini"
        link.symlink_to(target)
        with self.assertRaises(self.m.Conflict):
            self.m.atomic(link, "overwrite", expected="stale")
        self.assertEqual(target.read_text(), "newer")
        self.m.atomic(link, "updated", expected="newer")
        self.assertTrue(link.is_symlink())
        protected = self.config / "bwm/user/shell.jsonc"
        with self.assertRaises(ValueError):
            self.m.atomic(protected, "forbidden")

    def test_import_only_breeze_appearance_user_wins_and_file_untouched(self):
        user = self.config / "bwm/user/shell.jsonc"
        text = '{"all":{"bar":{"workspaces":{"shown":9}}},"skins":{"plasma":{"appearance":{"fonts":{"main":"My Font"}}}}}'
        self.write(user, text)
        self.write(self.config / "kdeglobals", "[General]\nfont=KDE Font,12,-1,5,50,0\n[WM]\nactiveFont=Title Font,11\n[Icons]\nTheme=ThirdParty\n")
        self.write(self.config / "kwinrc", "[NightColor]\nNightTemperature=2000\n[Windows]\nFocusPolicy=FocusFollowsMouse\nBorderSnapZone=17\n")
        self.m.enter()
        cfg = self.m.load_json(self.options)
        self.assertEqual(cfg["appearance"]["fonts"]["main"], "My Font")
        self.assertEqual(cfg["appearance"]["fonts"]["title"], "Title Font")
        self.assertEqual(cfg["bar"]["workspaces"]["shown"], 9)
        self.assertEqual(cfg["unknown"], {"keep": 42})
        self.assertEqual(self.kde("kdeglobals")["General"]["font"], "My Font,12,-1,5,50,0")
        self.assertEqual(self.kde("kdeglobals")["Icons"]["Theme"], "ThirdParty")
        self.assertEqual(self.kde("kwinrc")["NightColor"]["NightTemperature"], "4000")
        self.assertIn('focus = "FocusFollowsMouse"', self.m.KWIN_STATE.read_text())
        self.assertEqual(user.read_text(), text)

    def test_font_changes_in_both_directions_and_simultaneous_conflict(self):
        self.write(self.config / "kdeglobals", "[General]\nfont=First,10\n")
        self.m.enter()
        cfg = self.m.load_json(self.options)
        cfg["appearance"]["fonts"]["main"] = "BWM Changed"
        self.write(self.options, json.dumps(cfg))
        self.m.reconcile()
        self.assertEqual(self.kde("kdeglobals")["General"]["font"], "BWM Changed,10")
        cfg["appearance"]["fonts"]["main"] = "BWM Simultaneous"
        self.write(self.options, json.dumps(cfg))
        text = self.m.read(self.config / "kdeglobals").replace("BWM Changed,10", "KDE Simultaneous,12")
        self.write(self.config / "kdeglobals", text)
        self.m.reconcile()
        self.assertEqual(self.m.load_json(self.options)["appearance"]["fonts"]["main"], "KDE Simultaneous")

    def test_reconcile_is_idempotent_and_reloads_once_for_kwin_change(self):
        self.m.enter()
        initial = {str(p): p.stat().st_mtime_ns for p in self.config.glob("*rc")}
        self.calls.reset_mock()
        self.m.reconcile()
        self.m.reconcile()
        self.assertFalse(any(c.args[0] == ["hyprctl", "reload"] for c in self.calls.call_args_list))
        self.assertEqual(initial, {str(p): p.stat().st_mtime_ns for p in self.config.glob("*rc")})
        self.write(self.config / "kwinrc", self.m.read(self.config / "kwinrc") + "\n[Windows]\nFocusPolicy=FocusFollowsMouse\n")
        self.m.reconcile()
        self.m.reconcile()
        self.assertEqual(sum(c.args[0] == ["hyprctl", "reload"] for c in self.calls.call_args_list), 1)

    def test_no_import_or_export_outside_breeze(self):
        cfg = self.m.load_json(self.options)
        cfg["appearance"]["bwmTheme"] = "retro"
        self.write(self.options, json.dumps(cfg))
        self.assertFalse(self.m.reconcile())
        self.assertFalse((self.config / "kcminputrc").exists())
        self.assertFalse(self.m.KWIN_STATE.exists())

    def test_snap_distances_are_lua_integers_and_factor_can_be_fractional(self):
        self.write(self.config / "kwinrc", "[Windows]\nWindowSnapZone=19\nBorderSnapZone=7\n")
        self.write(self.config / "kdeglobals", "[KDE]\nAnimationDurationFactor=0.5\n")
        self.m.enter()
        k = self.m.kwin_settings()
        self.assertIs(type(k["windowSnap"]), int)
        self.assertIs(type(k["borderSnap"]), int)
        self.assertEqual(k["animationFactor"], 0.5)
        self.assertIn("windowSnap = 19,", self.m.KWIN_STATE.read_text())

    def test_inotify_observes_atomic_replacement_and_new_directories(self):
        watcher = self.m.Inotify()
        self.addCleanup(watcher.close)
        watcher.wait(0)
        tmp = self.options.with_suffix(".tmp")
        self.write(tmp, self.options.read_text() + "\n")
        os.replace(tmp, self.options)
        self.assertTrue(watcher.wait(1))
        self.write(self.config / "kdedefaults/kwinrc", "[Windows]\nPlacement=Centered\n")
        self.assertTrue(watcher.wait(1))
        self.assertIn((self.config / "kdedefaults").resolve(), watcher.dirs)

    def test_invalid_json_does_not_overwrite_any_file(self):
        self.m.enter()
        path = self.config / "kcminputrc"
        text = path.read_text()
        self.write(self.options, '{"incomplete":')
        with self.assertRaises(ValueError):
            self.m.reconcile()
        self.assertEqual(path.read_text(), text)

    def test_kded_guards_preserve_other_modules_and_custom_notification_owner(self):
        self.write(self.config / "kded5rc", "[Module-mine]\nautoload=true\n")
        service = self.root / "data/dbus-1/services/org.freedesktop.Notifications.service"
        self.write(service, "[D-BUS Service]\nName=org.freedesktop.Notifications\nExec=my-server\n")
        self.m.guards()
        self.assertEqual(self.kde("kded5rc")["Module-mine"]["autoload"], "true")
        if Path("/usr/bin/plasma_waitforname").exists():
            self.assertEqual(self.kde("kded5rc")["Module-statusnotifierwatcher"]["autoload"], "false")
        self.assertIn("Exec=my-server", service.read_text())

    def test_external_krdb_does_not_leak_legacy_settings_or_erase_foreign_lines(self):
        self.write(self.config / "gtkrc-2.0", '# mine\ngtk-font-name="Mine"\n')
        self.write(self.config / "Trolltech.conf", "[qt]\nfont=Mine,10\nUnknown=keep\n")
        self.m.enter()
        self.write(self.config / "gtkrc-2.0", '# created by KDE Plasma, today\n#\ngtk-alternative-button-order = 1\ninclude "/a/theme/gtkrc"\ngtk-theme-name="ThirdParty"\n# my new comment\ngtk-extra=1\n')
        self.write(self.config / "Trolltech.conf", "[qt]\nfont=ThirdParty,12\nUnknown=keep\nNewKey=preserved\nPalette\\active=red\n")
        self.m.reconcile()
        self.assertEqual((self.config / "gtkrc-2.0").read_text(), '# mine\ngtk-font-name="Mine"\n# my new comment\ngtk-extra=1\n')
        qt = self.kde("Trolltech.conf")["qt"]
        self.assertEqual(qt["font"], "Mine,10")
        self.assertEqual(qt["Unknown"], "keep")
        self.assertEqual(qt["NewKey"], "preserved")
        self.assertNotIn("Palette\\active", qt)

    def test_lua_data_cannot_inject_commands(self):
        self.write(self.config / "kwinrc", '[Windows]\nTitlebarDoubleClickCommand=\"); os.execute("bad") --\n')
        self.m.enter()
        self.assertIn('doubleClick = "\\\"); os.execute(\\"bad\\") --"', self.m.KWIN_STATE.read_text())

    def test_patch_preserves_unrelated_content_and_final_line_without_newline(self):
        self.assertEqual(self.m.patch_ini("# own\n[Other]\nKey=100%", {("Other", "New"): "yes"}),
                         "# own\n[Other]\nKey=100%\nNew=yes\n")
        self.assertEqual(self.m.patch_ini("[A]\nX=old\nY=keep\n", {("A", "X"): None}), "[A]\nY=keep\n")


if __name__ == "__main__":
    unittest.main()
