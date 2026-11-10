"""Diagnóstico de rescate: versiones reales y acciones seguras, sin tocar la sesión."""
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "config/hypr/scripts"
sys.path.insert(0, str(SCRIPTS))
import bwm_versions


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


menu = module("bwmenu", "bwm-menu.py")
requirements = module("requirements", "bwm-requirements.py")
keybinds = module("keybinds", "keybinds-manager.py")


class VersionsTest(unittest.TestCase):
    def test_reference_is_separate_from_minimum_compatibility(self):
        spec = {"referenceVersion": "0.56.2", "check": {"type": "version", "min": "0.55.0", "cmd": ["tool", "--version"], "regex": r"tool ([0-9.]+)"}}
        with patch.object(requirements, "which", return_value="/bin/tool"), \
                patch.object(requirements, "run", return_value="tool 0.55.0"):
            status, detail = requirements.check_requirement(spec, {})
        self.assertEqual(status, "ok")
        old = bwm_versions.requirement_versions(spec, "gentoo", detail, status)
        current = bwm_versions.requirement_versions(spec, "gentoo", "0.56.2", "ok")
        newer = bwm_versions.requirement_versions(spec, "gentoo", "0.57.0", "ok")
        self.assertEqual(old["minimumVersion"], "0.55.0")
        self.assertEqual(old["referenceVersion"], "0.56.2")
        self.assertEqual(old["versionState"], "error")
        self.assertEqual(current["versionState"], "ok")
        self.assertEqual(newer["versionState"], "newer")

    def test_package_name_digits_are_not_used_as_the_installed_version(self):
        spec = {"referenceVersion": "0.11", "check": {"type": "cmd"}}
        with patch.object(bwm_versions, "package_versions", return_value="qt6ct 0.11"):
            row = bwm_versions.requirement_versions(spec, "gentoo", "", "ok")
        self.assertEqual(row["versionState"], "ok")

    def test_lights_compare_numeric_versions_against_declared_minimum(self):
        for version, minimum, expected in (("0.55.0", "0.55", "ok"), ("2.10.0", "2.9", "newer"),
                                          ("3.10.9", "3.11", "error"), ("v6.11.2", "6.10.0", "newer")):
            with self.subTest(version=version, minimum=minimum):
                self.assertEqual(bwm_versions.version_state("ok", version, minimum)[0], expected)

    def test_failure_takes_priority_over_a_newer_version_and_plugins_require_exact_commit(self):
        self.assertEqual(bwm_versions.version_state("missing", "9.0", "1.0")[0], "error")
        self.assertEqual(bwm_versions.version_state("build", "abcdef99", "", "hyprland-plugin")[0], "error")
        self.assertEqual(bwm_versions.version_state("ok", "abcdef99", "", "hyprland-plugin")[0], "ok")

    def test_no_minimum_checks_presence_without_inventing_a_version_comparison(self):
        state, reason = bwm_versions.version_state("ok", "tool 19.0", "")
        self.assertEqual(state, "ok")
        self.assertIn("sin versión mínima", reason)
        self.assertEqual(bwm_versions.version_state("ok", "unknown", "1.0")[0], "unknown")

    def test_skin_light_inherits_core_and_includes_optional_failures(self):
        core = {"id": "python", "versionState": "newer"}
        good = {"id": "skin", "versionState": "ok"}
        missing_optional = {"id": "optional", "versionState": "error"}
        self.assertEqual(bwm_versions.version_health([core, good])["state"], "newer")
        health = bwm_versions.version_health([core, good, core, missing_optional])
        self.assertEqual(health["state"], "error")
        self.assertEqual(health["counts"], {"ok": 1, "newer": 1, "error": 1, "unknown": 0})
        self.assertEqual(bwm_versions.version_health([])["state"], "unknown")

    def test_gentoo_multiple_slots_do_not_include_similarly_named_packages(self):
        with tempfile.TemporaryDirectory() as root:
            for name in ("python-3.13.1", "python-3.14.7", "python-exec-2.4.10"):
                (Path(root) / "dev-lang" / name).mkdir(parents=True)
            result = bwm_versions.package_versions(
                {"packages": {"gentoo": "overlay:dev-lang/python[sqlite]"}}, "gentoo", Path(root))
        self.assertIn("python 3.13.1", result)
        self.assertIn("python 3.14.7", result)
        self.assertNotIn("exec", result)

    def test_failed_package_query_does_not_report_error_text_as_version(self):
        spec = {"packages": {"arch": "aur:missing-package"}}
        with patch.object(bwm_versions.subprocess, "run") as run:
            run.return_value.returncode = 1
            run.return_value.stdout = "error: not installed"
            self.assertEqual(bwm_versions.package_versions(spec, "arch"), "")

    def test_presence_check_does_not_invent_a_minimum(self):
        with patch.object(bwm_versions, "package_versions", return_value="tool 9.0"):
            row = bwm_versions.requirement_versions({"check": {"type": "cmd"}}, "gentoo", "", "ok")
        self.assertEqual(row["version"], "tool 9.0")
        self.assertEqual(row["minimumVersion"], "")
        self.assertEqual(row["versionPolicy"], "sin mínimo declarado")

    def test_explicit_stderr_probe_extracts_only_the_version(self):
        spec = {"check": {"type": "cmd"}, "versionProbes": [
            {"cmd": ["cliphist", "version"], "regex": r"^version\s+(\S+)", "stderr": True}]}
        with patch.object(bwm_versions.subprocess, "run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = ""
            run.return_value.stderr = "version\t0.7.0\nconfig-path\t/private/path\n"
            row = bwm_versions.requirement_versions(spec, "gentoo", "", "ok")
        self.assertEqual(row["version"], "0.7.0")

    def test_source_install_reads_upstream_version_metadata_only_when_installed(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "DarklyConfigVersion.cmake"
            path.write_text('set(PACKAGE_VERSION "0.5.43")\n')
            spec = {"check": {"type": "qtplugin"}, "versionFiles": [
                {"path": str(path), "regex": r'^set\(PACKAGE_VERSION "([0-9.]+)"\)'}]}
            installed = bwm_versions.requirement_versions(spec, "gentoo", "", "ok")
            missing = bwm_versions.requirement_versions(spec, "gentoo", "", "missing")
        self.assertEqual(installed["version"], "0.5.43")
        self.assertEqual(installed["versionSource"], str(path))
        self.assertEqual(missing["version"], "")

    def test_runtime_hyprland_cannot_be_hidden_by_a_newer_installed_binary(self):
        spec = {"check": {"type": "version", "cmd": ["Hyprland", "--version"],
                          "regex": r"Hyprland ([0-9.]+)", "min": "0.55.0"}}
        with patch.dict(os.environ, {"HYPRLAND_INSTANCE_SIGNATURE": "test"}), \
                patch.object(requirements, "which", return_value="/bin/tool"), \
                patch.object(requirements, "run", side_effect=["Hyprland 0.56.2", json.dumps({"version": "0.54.3"})]):
            state, detail = requirements.check_requirement(spec, {})
        self.assertEqual(state, "outdated")
        self.assertIn("0.54.3", detail)


class RecoveryTest(unittest.TestCase):
    def test_graphical_failure_falls_back_to_the_independent_console(self):
        with tempfile.TemporaryDirectory() as runtime, \
                patch.dict(os.environ, {"XDG_RUNTIME_DIR": runtime}), \
                patch.object(menu.subprocess, "Popen") as popen, \
                patch.object(menu, "open_window", return_value=0) as fallback:
            popen.return_value.wait.return_value = 1
            self.assertEqual(menu.graphical(), 0)
        fallback.assert_called_once_with(terminal=True)
        self.assertNotIn("-c", popen.call_args.args[0])

    def test_normal_graphical_close_does_not_open_a_console(self):
        with tempfile.TemporaryDirectory() as runtime, \
                patch.dict(os.environ, {"XDG_RUNTIME_DIR": runtime}), \
                patch.object(menu.subprocess, "Popen") as popen, \
                patch.object(menu, "open_window") as fallback:
            popen.return_value.wait.return_value = 0
            self.assertEqual(menu.graphical(), 0)
        fallback.assert_not_called()

    def test_snapshot_remains_available_when_shell_and_compositor_are_down(self):
        report = {"current": "retro", "core": {"ok": False}, "skins": []}
        backend = unittest.mock.Mock()
        backend.report.return_value = report
        with patch.object(menu, "requirements_module", return_value=backend), \
                patch.object(menu, "output", return_value=""), \
                patch("bwm_session.shell_instances", return_value=[]):
            data = menu.snapshot()
        self.assertEqual(data["shellPids"], [])
        self.assertEqual(data["hyprland"], {})
        self.assertIn("sin conexión", menu.plain_report(data))

    def test_corrupt_requirements_do_not_close_the_rescue_menu(self):
        with patch.object(menu, "requirements_module", side_effect=ValueError("bad catalog")), \
                patch.object(menu, "output", return_value=""), \
                patch("bwm_session.shell_instances", return_value=[]):
            data = menu.snapshot()
        self.assertIn("bad catalog", data["error"])
        self.assertIn("bad catalog", menu.plain_report(data))

    def test_offline_action_does_not_start_shell_or_change_skin(self):
        ui = menu.Menu()
        ui.data = {"hyprland": {}}
        with patch.object(menu.subprocess, "run") as run:
            ui.apply_skin("retro")
        run.assert_not_called()
        self.assertIn("No hay conexión", ui.pages[-1]["rows"][0]["label"])

    def test_recovery_uses_existing_manager_and_current_skin(self):
        ui = menu.Menu()
        ui.data = {"current": "retro", "skins": [{"id": "retro"}]}
        with patch.object(ui, "execute") as execute:
            ui.restart()
        self.assertEqual(execute.call_args.args[0],
                         [sys.executable, str(SCRIPTS / "bwm-theme-manager.py"), "set", "retro", "--restart-shell"])

    def test_apply_routes_through_requirements_guard(self):
        with patch.object(menu.Menu, "execute") as execute:
            menu.Menu().apply_skin("plasma")
        self.assertEqual(execute.call_args.args[0], [str(SCRIPTS / "bwm"), "skin", "plasma"])

    def test_hostile_log_cannot_emit_terminal_control_sequences(self):
        cleaned = menu.clean("registro\x1b[2J\x07\r\ntexto")
        self.assertNotIn("\x1b", cleaned)
        self.assertNotIn("\x07", cleaned)
        self.assertIn("\ntexto", cleaned)

    def test_both_chord_orders_and_keypads_are_generated_without_single_key_binds(self):
        lua = keybinds.generate_lua([])
        self.assertIn('hl.bind("plus + minus"', lua)
        self.assertIn('hl.bind("minus + plus"', lua)
        self.assertIn('hl.bind("KP_Add + KP_Subtract"', lua)
        self.assertIn('hl.bind("KP_Subtract + KP_Add"', lua)
        self.assertNotIn('hl.bind("plus",', lua)
        self.assertNotIn('hl.bind("minus",', lua)


if __name__ == "__main__":
    unittest.main()
