"""Execute activation Lua against a stateful dispatcher fixture, without compositor IPC."""
import importlib.util
import json
from pathlib import Path
import shutil
import os
import tempfile
import subprocess
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "config/hypr/scripts"
sys.path.insert(0, str(SCRIPTS))
import bwm_windows as windows


class ActivationTest(unittest.TestCase):
    def execute(self, workspace, actual_pid=17, repeats=1):
        if not shutil.which("lua"):
            self.skipTest("lua is needed for dispatcher fixture")
        with mock.patch.object(windows, "dispatch") as dispatch:
            windows.focus_window({"address": "0x123", "pid": 17})
        code = dispatch.call_args.args[0][0]
        prelude = '''
            local actions = {}
            local w = {pid = PID, workspace = {id = WSID, name = WSNAME}}
            local function action(kind, args) args.kind = kind; return args end
            hl = {dsp = {window = {}, cursor = {}}, get_window = function() return w end,
                  get_cursor_pos = function() return nil end}
            hl.dsp.no_op = function() return {} end
            hl.dsp.focus = function(args) return action("focus", args) end
            hl.dsp.window.bring_to_top = function(args) return action("raise", args) end
            hl.dsp.window.alter_zorder = function(args) return action("order", args) end
            hl.dispatch = function(a)
                if a.workspace then table.insert(actions, "show:" .. a.workspace)
                elseif a.kind then table.insert(actions, a.kind) end
            end
        '''.replace("PID", str(actual_pid)).replace("WSID", str(workspace["id"])).replace("WSNAME", json.dumps(workspace["name"]))
        program = prelude + ("\n(function() " + code + " end)();\n") * repeats + '\nprint(table.concat(actions, ","))'
        return subprocess.run(["lua", "-"], input=program, text=True, capture_output=True, check=True).stdout.strip()

    def test_special_is_shown_before_focus_and_never_toggled(self):
        self.assertEqual(self.execute({"id": -97, "name": "special:magic"}, repeats=2),
                         "show:special:magic,focus,raise,order,show:special:magic,focus,raise,order")

    def test_normal_window_uses_existing_workspace(self):
        self.assertEqual(self.execute({"id": 2, "name": "2"}), "focus,raise,order")

    def test_storage_never_becomes_visible(self):
        for ws in ({"id": -98, "name": "special:minimized"}, {"id": 99, "name": "99"}):
            self.assertEqual(self.execute(ws), "")

    def test_reused_address_does_not_activate(self):
        self.assertEqual(self.execute({"id": -97, "name": "special:magic"}, actual_pid=99), "")

    def test_cli_rejects_stale_pid_before_restoring(self):
        spec = importlib.util.spec_from_file_location("bwm_focus", SCRIPTS / "bwm-focus.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with mock.patch.object(windows, "hypr_json", return_value=[{"address": "0x123", "pid": 99}]), mock.patch.object(windows, "focus_window") as focus:
            self.assertEqual(module.main(["0x123", "--pid", "17"]), 1)
            focus.assert_not_called()

    def test_switcher_only_includes_visible_magic(self):
        runner = Path('/usr/lib64/qt6/bin/qmltestrunner')
        if not runner.is_file():
            self.skipTest('qmltestrunner needed for JavaScript fixture')
        source = (ROOT / "config/quickshell/ii/modules/ii/altTab/AltTab.qml").read_text()
        # Extract using balanced braces so nested object literals remain intact.
        start = source.index("    function getVisibleWindows(")
        brace = source.index("{", start)
        level = 1
        end = brace + 1
        while level:
            level += (source[end] == "{") - (source[end] == "}")
            end += 1
        method = source[start:end]
        method = method.replace('Appearance.isPlasma', 'root.plasma')
        fixture = """import QtQuick
import QtTest
TestCase {
    id: root
    name: "SpecialWorkspaceFilter"
    property bool plasma: true
    property bool appFilterFromActive: false
    property string appFilter: ""
    function findToplevel() { return null; }
    METHOD
    function test_visible_special() {
        const clients = [{address:"0x1", pid:17, class:"test", workspace:{id:-97,name:"special:magic"}}];
        compare(getVisibleWindows(clients,[{activeWorkspace:{id:1},specialWorkspace:{id:-97}}]).length, 1);
        compare(getVisibleWindows(clients,[{activeWorkspace:{id:1},specialWorkspace:{id:0}}]).length, 0);
        plasma = false;
        compare(getVisibleWindows(clients,[{activeWorkspace:{id:1},specialWorkspace:{id:-97}}]).length, 1);
        compare(getVisibleWindows(clients,[{activeWorkspace:{id:1},specialWorkspace:{id:0}}]).length, 0);
    }
}
""".replace('METHOD', method)
        with tempfile.TemporaryDirectory(prefix='bwm-r1-js-') as temp:
            path = Path(temp) / 'tst_filter.qml'
            path.write_text(fixture)
            env = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software', QML_DISABLE_DISK_CACHE='1')
            out = subprocess.run([str(runner), '-input', str(path)], env=env, capture_output=True, text=True, timeout=20)
            self.assertEqual(out.returncode, 0, out.stdout + out.stderr)


    def test_hidden_fallback_never_requests_capture(self):
        runner = Path('/usr/lib64/qt6/bin/qmltestrunner')
        if not runner.is_file():
            self.skipTest('qmltestrunner needed for binding test')
        source = (ROOT / 'config/quickshell/ii/modules/ii/altTab/AltTab.qml').read_text()
        binding = next(line.split('captureSource:', 1)[1].strip() for line in source.splitlines() if 'captureSource:' in line)
        fixture = """import QtQuick
import QtTest
TestCase {
    id: root
    name: "HiddenFallbackCapture"
    property bool isOpen: true
    property QtObject panelWindow: QtObject { property bool visible: false }
    property var modelData: ({toplevel: ({identity: "fake"})})
    property var captureSource: BINDING
    function test_visibility_gate() {
        compare(captureSource, null);
        panelWindow.visible = true;
        compare(captureSource, modelData.toplevel);
        isOpen = false;
        compare(captureSource, null);
        isOpen = true;
        panelWindow.visible = false;
        compare(captureSource, null);
    }
}
""".replace('BINDING', binding)
        with tempfile.TemporaryDirectory(prefix='bwm-hidden-capture-') as temp:
            path = Path(temp) / 'tst_capture.qml'
            path.write_text(fixture)
            result = subprocess.run([str(runner), '-input', str(path)],
                env=dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software'),
                capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
