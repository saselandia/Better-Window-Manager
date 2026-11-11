"""Fase 6b de docs/BREEZE_PLAN.md: el plugin breezebars como pegamento de bwm-decorator.

El plugin sólo se puede cargar en Hyprland al iniciar sesión (regla 1), así que aquí se prueba lo que
no depende de Hyprland con el mismo código que compila el plugin (src/breezebars/DecoWire.hpp y
DecoLogic.hpp): lectura y escritura del protocolo, piezas del marco, daños a escala, sombra de nueve
trozos como KWin, secciones de redimensionado, rueda y maximizado por ejes, colores de los tooltips.
Después habla con el auxiliar real (tests/breezebars_wire_test.cpp) como lo hará el plugin: estado,
imagen, sombra, pulsación en la barra sin aceptar (sección 9 → mover), rueda y cambio de tamaño.
Comprueba también que el plugin compila y no deja símbolos sin resolver contra el Hyprland instalado.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "src" / "breezebars"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_bwm_decorator as td  # noqa: E402


def compile_wire_test(out: Path):
    cmd = [os.environ.get("CXX", "g++"), "-std=c++2b", "-O1", "-Wall", "-I", str(PLUGIN),
           str(ROOT / "tests" / "breezebars_wire_test.cpp"), "-o", str(out)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise AssertionError("no compila la prueba del protocolo:\n" + res.stderr[-3000:])


class BreezebarsLogicTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="breezebars-"))
        cls.binary = cls.tmp / "wire_test"
        compile_wire_test(cls.binary)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_logic_without_helper(self):
        res = subprocess.run([str(self.binary)], capture_output=True, text=True, timeout=30)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        for name in ("secciones", "piezas", "daños", "sombra", "acciones", "mensajes"):
            self.assertIn(f"ok {name}", res.stdout)


class BreezebarsHelperTest(unittest.TestCase):
    """Con el auxiliar real (necesita KDecoration3, como las pruebas de F6a)."""

    @classmethod
    def setUpClass(cls):
        td.BwmDecoratorTest.setUpClass()  # compila bwm-decorator (o salta sin KDecoration3)
        cls.binary = td.BwmDecoratorTest.binary
        cls.tmp = Path(tempfile.mkdtemp(prefix="breezebars-"))
        cls.wire = cls.tmp / "wire_test"
        compile_wire_test(cls.wire)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_talks_to_helper_like_the_plugin(self):
        h = td.Helper(self, kdeglobals=td.scheme("BreezeDark"))
        self.addCleanup(h.close)
        h.client.close()  # el cliente Python no hace falta: habla el C++ del plugin
        res = subprocess.run([str(self.wire), str(h.socket)], capture_output=True, text=True, timeout=60)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("ok auxiliar", res.stdout)


@unittest.skipUnless(Path("/usr/include/hyprland/src/plugins/PluginAPI.hpp").exists(), "faltan las cabeceras de Hyprland")
class BreezebarsBuildTest(unittest.TestCase):
    def test_plugin_builds_and_resolves(self):
        """Compila el plugin en una copia (no toca el .so instalado) y busca símbolos sin resolver."""
        tmp = Path(tempfile.mkdtemp(prefix="breezebars-build-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        src = tmp / "src"
        shutil.copytree(PLUGIN, src / "breezebars", ignore=shutil.ignore_patterns("*.so"))
        shutil.copytree(ROOT / "src" / "bwm-decorator", src / "bwm-decorator", ignore=shutil.ignore_patterns("*.o", "moc_*", "bwm-decorator"))
        res = subprocess.run(["make", "-C", str(src / "breezebars")], capture_output=True, text=True, timeout=900)
        self.assertEqual(res.returncode, 0, res.stderr[-3000:])
        so = src / "breezebars" / "breezebars.so"
        hypr = shutil.which("Hyprland")
        if not hypr:
            self.skipTest("Hyprland no está instalado")
        hypr = os.path.realpath(hypr)
        defined = set()
        libs = [hypr] + [l.split("=>")[1].split()[0] for l in subprocess.run(["ldd", hypr], capture_output=True, text=True).stdout.splitlines()
                         if "=>" in l and len(l.split("=>")[1].split()) > 0 and l.split("=>")[1].split()[0].startswith("/")]
        for lib in libs:
            out = subprocess.run(["nm", "-D", "--defined-only", lib], capture_output=True, text=True).stdout
            defined.update(line.split()[-1].split("@")[0] for line in out.splitlines() if line.strip())
        undefined = [line.split()[-1].split("@")[0] for line in
                     subprocess.run(["nm", "-D", "--undefined-only", str(so)], capture_output=True, text=True).stdout.splitlines()
                     if line.strip() and not line.strip().startswith("w ")]
        missing = sorted(set(undefined) - defined)
        self.assertEqual(missing, [], "símbolos sin resolver contra Hyprland")


if __name__ == "__main__":
    unittest.main()
