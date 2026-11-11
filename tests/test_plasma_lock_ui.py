"""Bloqueo de Breeze (modules/ii/plasmaLock): el campo de contraseña conserva el foco al escribir.

Prueba opcional en una instancia aparte (qs -p) con PlasmaLockSurface dentro de una ventana flotante
(regla temporal), no en un bloqueo real. Teclas reales de QtTest. Las teclas sólo llegan a una ventana
con el foco del teclado: se abre unos segundos, pequeña, en el workspace visible que se indique, y
después se devuelve el foco a la ventana que lo tenía:

    BWM_RUN_QML_TESTS=1 BWM_LOCK_TEST_WORKSPACE=10 python3 -m unittest tests.test_plasma_lock_ui -v

Antes, cada letra llamaba a wake(), que daba el foco al Rectangle de BreezeTextField y no a su
TextInput: había que volver a pulsar el campo para escribir la siguiente. No se llama a PAM.
"""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "config/quickshell/ii"

HARNESS = r'''//@ pragma UseQApplication
//@ pragma Env QS_NO_RELOAD_POPUP=1
import QtQuick
import QtTest
import Quickshell
import qs
import qs.modules.common
import qs.modules.common.panels.lock
import qs.modules.ii.plasmaLock

ShellRoot {
    function report(key, value) { console.log("LOCKTEST " + JSON.stringify({ key: key, value: value })); }
    Component.onCompleted: Config.blockWrites = true
    LockContext { id: ctx }
    FloatingWindow {
        id: win
        title: "BWM Plasma Lock Test"
        implicitWidth: 700
        implicitHeight: 520
        PlasmaLockSurface { id: surface; anchors.fill: parent; context: ctx }
        // QtTest como conductor (qs no ejecuta las funciones test_*): teclas reales a la ventana
        TestCase { id: driver; name: "PlasmaLockDriver"; when: false }
        // Como al despertar la pantalla: mover el ratón muestra el formulario y enfoca el campo
        Timer { interval: 1000; running: true; onTriggered: driver.mouseMove(surface, 30, 30) }
        Timer {
            interval: 1600
            running: true
            onTriggered: {
                for (const ch of "abc1") { driver.keyClick(ch, Qt.NoModifier, 1); driver.wait(30); }
                report("text", ctx.currentText);
                report("uiShown", surface.uiShown);
                report("inputFocused", surface.Window.activeFocusItem instanceof TextInput);
                report("done", true);
                Qt.quit();
            }
        }
    }
}
'''


@unittest.skipUnless(os.environ.get("BWM_RUN_QML_TESTS") == "1" and os.environ.get("BWM_LOCK_TEST_WORKSPACE"),
                     "prueba de interfaz opcional (BWM_RUN_QML_TESTS=1 y BWM_LOCK_TEST_WORKSPACE=<workspace visible>)")
class PlasmaLockUiTest(unittest.TestCase):
    def test_password_keeps_focus_while_typing(self):
        rule = "tmp-plasma-lock-test"
        workspace = int(os.environ["BWM_LOCK_TEST_WORKSPACE"])
        previous = json.loads(subprocess.check_output(["hyprctl", "-j", "activewindow"])).get("address")
        subprocess.run(["hyprctl", "eval", f'hl.window_rule({{name="{rule}", match={{title="^BWM Plasma Lock Test$"}}, '
                        f'workspace="{workspace}", float=true, size="700 520", move="20 20"}})'],
                       check=True, capture_output=True)
        harness = SHELL / "zz_plasma_lock_test.qml"
        try:
            harness.write_text(HARNESS)
            out = subprocess.run(["qs", "-p", str(harness)], capture_output=True, text=True, timeout=40).stdout
        finally:
            harness.unlink(missing_ok=True)
            subprocess.run(["hyprctl", "eval", f'hl.window_rule({{name="{rule}", match={{title="^$NADA^"}}}})'],
                           capture_output=True)
            if previous:
                subprocess.run(["hyprctl", "dispatch", f'hl.dsp.focus({{ window = "address:{previous}" }})'],
                               capture_output=True)
        results = {}
        for line in out.splitlines():
            if "LOCKTEST " in line:
                data = json.loads(line.split("LOCKTEST ", 1)[1])
                results[data["key"]] = data["value"]
        self.assertTrue(results.get("done"), out[-3000:])
        self.assertEqual(results["text"], "abc1")
        self.assertTrue(results["uiShown"])
        self.assertTrue(results["inputFocused"])


if __name__ == "__main__":
    unittest.main()
