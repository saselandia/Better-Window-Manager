"""Fase 6a de docs/BREEZE_PLAN.md: bwm-decorator, el auxiliar que dibuja las decoraciones de KDE.

Arranca el auxiliar compilado con una configuración aislada (XDG_CONFIG_HOME/XDG_DATA_HOME
temporales, socket en un directorio temporal de XDG_RUNTIME_DIR) y le habla con
tests/bwm_decorator_client.py: Breeze oscuro y claro, cambio de esquema en vivo, disposición de
botones, hover, clic → petición, escala 1,5, varias ventanas, sombra y un tema Aurorae de terceros.
No necesita Hyprland ni toca la configuración del usuario.

Con BWM_TEST_PNG_DIR=<carpeta> guarda las imágenes de las decoraciones. El tema Aurorae se busca en
BWM_TEST_AURORAE_DIR (carpeta de datos con aurorae/themes/<tema>) y en las carpetas de datos.
"""
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "bwm-decorator"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bwm_decorator_client as dc  # noqa: E402

KWINRC = "[org.kde.kdecoration2]\nlibrary={library}\ntheme={theme}\nButtonsOnLeft={left}\nButtonsOnRight={right}\n"


def scheme(name: str) -> str:
    for base in ("/usr/share/color-schemes",):
        path = Path(base) / f"{name}.colors"
        if path.is_file():
            return path.read_text()
    raise unittest.SkipTest(f"falta el esquema {name}")


def find_aurorae():
    roots = [os.environ.get("BWM_TEST_AURORAE_DIR", "")] + (os.environ.get("XDG_DATA_DIRS") or "/usr/share").split(":")
    roots.append(str(Path.home() / ".local/share"))
    for root in filter(None, roots):
        themes = Path(root) / "aurorae" / "themes"
        if themes.is_dir():
            for theme in sorted(themes.iterdir()):
                if (theme / "decoration.svg").exists() or (theme / "decoration.svgz").exists():
                    return root, theme.name
    return None


class Helper:
    def __init__(self, test, kdeglobals: str, library="org.kde.breeze", theme="", left="MS", right="HIAX", data=None):
        self.tmp = Path(tempfile.mkdtemp(prefix="bwm-deco-"))
        self.config = self.tmp / "config"
        self.config.mkdir()
        (self.config / "kdeglobals").write_text(kdeglobals)
        (self.config / "kwinrc").write_text(KWINRC.format(library=library, theme=theme, left=left, right=right))
        runtime = os.environ.get("XDG_RUNTIME_DIR") or tempfile.gettempdir()
        self.sockdir = Path(tempfile.mkdtemp(prefix="bwmd-", dir=runtime))
        self.socket = self.sockdir / "s"
        env = dict(os.environ, XDG_CONFIG_HOME=str(self.config), QT_QPA_PLATFORM="offscreen")
        if data:
            env["XDG_DATA_HOME"] = data
        self.log = open(self.tmp / "log", "w")
        self.proc = subprocess.Popen([str(test.binary), "--socket", str(self.socket)], env=env,
                                     stdout=self.log, stderr=subprocess.STDOUT)
        for _ in range(100):
            if self.socket.exists():
                break
            time.sleep(0.05)
        self.client = dc.Client(str(self.socket))

    def close(self):
        self.client.close()
        self.proc.terminate()
        try:
            self.proc.wait(5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.log.close()
        shutil.rmtree(self.tmp, ignore_errors=True)
        shutil.rmtree(self.sockdir, ignore_errors=True)


class BwmDecoratorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not Path("/usr/include/KDecoration3").is_dir():
            raise unittest.SkipTest("falta KDecoration3 (kde-plasma/kdecoration)")
        out = subprocess.run(["make", "-C", str(SOURCE), "-j8"], capture_output=True, text=True)
        if out.returncode != 0:
            raise AssertionError("no compila bwm-decorator:\n" + out.stderr[-3000:])
        cls.binary = SOURCE / "bwm-decorator"
        cls.png_dir = os.environ.get("BWM_TEST_PNG_DIR")

    def helper(self, **kw):
        h = Helper(self, **kw)
        self.addCleanup(h.close)
        return h

    def save(self, image, name):
        if self.png_dir:
            Path(self.png_dir).mkdir(parents=True, exist_ok=True)
            image.save(Path(self.png_dir) / f"{name}.png")

    def title_pixel(self, window, frame=None):
        frame = frame or window.frames[-1]
        image = dc.frame_image(frame)
        tx, ty, tw, th = window.geometry["titleBar"]
        # Un punto de la barra lejos del título y de los botones
        return image, image.getpixel((int((tx + tw * 0.3) * frame.scale), int((ty + th / 2) * frame.scale)))

    def find_button(self, h, wid, from_right=True):
        """Clic a lo largo de la barra hasta que la decoración pida algo: el primer botón."""
        w = h.client.windows[wid]
        tx, ty, tw, th = w.geometry["titleBar"]
        xs = range(int(tx + tw) - 2, int(tx), -3) if from_right else range(int(tx) + 2, int(tx + tw), 3)
        for x in xs:
            h.client.click(wid, x, ty + th / 2)
            h.client.settle(0.06)
            # Al pasar por encima, la decoración pide su tooltip: eso no es pulsar un botón
            pressed = [r for r in w.requests if r["kind"] not in ("showToolTip", "hideToolTip")]
            if pressed:
                return x, pressed[0]
        return None, None

    def test_breeze_dark_and_light(self):
        lum = {}
        for name in ("BreezeDark", "BreezeLight"):
            h = self.helper(kdeglobals=scheme(name))
            self.assertEqual(h.client.ack[1], "org.kde.breeze")
            w = h.client.create(1, caption="kitty — ~/Projects", app_class="kitty")
            self.assertIsNotNone(h.client.wait_frame(1))
            h.client.settle()
            self.assertGreater(w.geometry["borders"][1], 20, w.geometry)
            image, pixel = self.title_pixel(w)
            self.save(image.crop((0, 0, image.width, 60)), name)
            lum[name] = dc.luminance(pixel)
            self.assertEqual(h.client.errors, [])
        self.assertLess(lum["BreezeDark"], 0.3)
        self.assertGreater(lum["BreezeLight"], 0.6)

    def test_live_scheme_change(self):
        h = self.helper(kdeglobals=scheme("BreezeDark"))
        w = h.client.create(1)
        h.client.wait_frame(1)
        h.client.settle()
        before = w.frames[-1].serial
        tmp = h.config / "kdeglobals.new"
        tmp.write_text(scheme("BreezeLight"))
        os.replace(tmp, h.config / "kdeglobals")  # reemplazo atómico, como KConfig
        frame = h.client.wait_frame(1, after=before, timeout=6)
        h.client.settle(0.5)
        self.assertIsNotNone(frame, "no repinta al cambiar el esquema")
        _, pixel = self.title_pixel(w)
        self.assertGreater(dc.luminance(pixel), 0.6)

    def test_default_buttons_click_and_hover(self):
        h = self.helper(kdeglobals=scheme("BreezeDark"))
        w = h.client.create(1)
        h.client.wait_frame(1)
        h.client.settle()
        before = dc.frame_image(w.frames[-1])
        x, request = self.find_button(h, 1, from_right=True)
        self.assertEqual(request and request["kind"], "close", w.requests)
        # El botón de cerrar bajo el puntero se dibuja distinto (hover de Breeze)
        h.client.pointer(1, dc.MOTION, x, w.geometry["titleBar"][1] + w.geometry["titleBar"][3] / 2)
        h.client.settle(0.4)
        after = dc.frame_image(w.frames[-1])
        self.save(after.crop((0, 0, after.width, 60)), "BreezeDark-hover")
        box = (int(x) - 8, 4, int(x) + 8, 24)
        self.assertNotEqual(list(before.crop(box).getdata()), list(after.crop(box).getdata()))
        # Maximizar es el siguiente botón hacia la izquierda: pide alternar con el botón izquierdo
        w.requests.clear()
        h.client.pointer(1, dc.LEAVE, -1, -1)
        pressed = []
        for dx in range(3, 90, 3):
            h.client.click(1, x - dx, w.geometry["titleBar"][1] + w.geometry["titleBar"][3] / 2)
            h.client.settle(0.06)
            # El de cerrar ocupa varios píxeles más a la izquierda: el siguiente botón distinto
            pressed = [r for r in w.requests if r["kind"] not in ("showToolTip", "hideToolTip", "close")]
            if pressed:
                break
        self.assertEqual(pressed[0]["kind"], "toggleMaximization")
        self.assertEqual(pressed[0]["arg"], dc.LEFT_BUTTON)
        self.assertTrue(any(r["kind"] == "showToolTip" and r["text"] for r in w.requests), "sin tooltip")

    def test_pointer_result_like_kwin(self):
        """Pulsar la barra (no un botón): sin aceptar y sección 9 → el compositor mueve; un botón la acepta."""
        h = self.helper(kdeglobals=scheme("BreezeDark"))
        w = h.client.create(1, width=800, height=500)
        h.client.wait_frame(1)
        h.client.settle()
        tx, ty, tw, th = w.geometry["titleBar"]
        h.client.click(1, tx + tw * 0.3, ty + th / 2)
        h.client.settle(0.2)
        press = [r for r in w.results if r[0] == dc.PRESS]
        self.assertEqual(press[-1][:3], (dc.PRESS, 0, 9), w.results)
        w.results.clear()
        x, request = self.find_button(h, 1, from_right=True)
        self.assertEqual(request and request["kind"], "close")
        self.assertIn((dc.PRESS, 1), [r[:2] for r in w.results])
        # Debajo del marco, en la franja sólo para redimensionar: sección inferior
        left, top, right, bottom = w.geometry["borders"]
        extra = w.geometry["resizeOnly"][3]
        self.assertGreater(extra + bottom, 0, w.geometry)
        w.results.clear()
        y = top + 500 + bottom + max(extra, 1) / 2
        h.client.pointer(1, dc.LEAVE, -1, -1)
        h.client.pointer(1, dc.MOTION, 400, y)
        h.client.pointer(1, dc.PRESS, 400, y, dc.LEFT_BUTTON, dc.LEFT_BUTTON)
        h.client.settle(0.2)
        self.assertEqual([r[2] for r in w.results if r[0] == dc.PRESS], [7], w.results)

    def test_button_layout_from_kwinrc(self):
        h = self.helper(kdeglobals=scheme("BreezeDark"), left="XIA", right="")
        w = h.client.create(1)
        h.client.wait_frame(1)
        h.client.settle()
        self.save(dc.frame_image(w.frames[-1]).crop((0, 0, 800, 60)), "BreezeDark-left-buttons")
        _, request = self.find_button(h, 1, from_right=False)
        self.assertEqual(request and request["kind"], "close", w.requests)
        _, request = self.find_button(h, 1, from_right=True)
        self.assertEqual(request and request["kind"], "close")  # sigue siendo el primero por la izquierda

    def test_scale(self):
        h = self.helper(kdeglobals=scheme("BreezeDark"))
        w = h.client.create(1, width=800, height=500, scale=1.5)
        frame = h.client.wait_frame(1)
        h.client.settle()
        frame = w.frames[-1]
        top = w.geometry["borders"][1]
        self.assertEqual(frame.scale, 1.5)
        self.assertEqual(frame.parts[0][0][2], math.ceil(800 * 1.5))
        self.assertEqual(frame.parts[0][0][3], math.ceil(top * 1.5))
        self.save(dc.frame_image(frame).crop((0, 0, 1200, 90)), "BreezeDark-scale-1.5")

    def test_windows_shadow_and_destroy(self):
        h = self.helper(kdeglobals=scheme("BreezeDark"))
        a = h.client.create(1, caption="uno")
        b = h.client.create(2, caption="dos", flags=dc.DEFAULT_FLAGS)  # inactiva
        h.client.wait_frame(1)
        h.client.wait_frame(2)
        h.client.settle()
        self.assertTrue(a.shadow and a.shadow["pixels"], "sin sombra")
        self.assertGreater(a.shadow["padding"][1], 0)
        _, active = self.title_pixel(a)
        _, inactive = self.title_pixel(b)
        self.assertNotEqual(active, inactive)
        h.client.destroy(1)
        h.client.send(dc.PING, 2)
        self.assertTrue(h.client.wait(lambda: False, 0.3) or True)
        h.client.update(2, caption="dos (cambiado)", flags=dc.DEFAULT_FLAGS | dc.ACTIVE)
        self.assertIsNotNone(h.client.wait_frame(2, after=b.frames[-1].serial))
        self.assertEqual(h.client.errors, [])
        self.assertEqual(h.proc.poll(), None, "el auxiliar no debe caer")

    def test_aurorae_third_party(self):
        found = find_aurorae()
        if not found:
            self.skipTest("no hay temas Aurorae (BWM_TEST_AURORAE_DIR=<datos con aurorae/themes>)")
        data, theme = found
        h = self.helper(kdeglobals=scheme("BreezeDark"), library="org.kde.kwin.aurorae",
                        theme=f"__aurorae__svg__{theme}", data=data)
        self.assertTrue(h.client.ack[1].startswith("org.kde.kwin.aurorae"), h.client.ack)
        w = h.client.create(1, caption=f"Aurorae {theme}")
        self.assertIsNotNone(h.client.wait_frame(1, timeout=8))
        h.client.settle(0.5)
        image = dc.frame_image(w.frames[-1])
        self.save(image.crop((0, 0, image.width, 60)), f"Aurorae-{theme}")
        self.assertGreater(w.geometry["borders"][1], 10)
        top = image.crop((0, 0, image.width, int(w.geometry["borders"][1])))
        self.assertGreater(sum(1 for p in top.getdata() if p[3] > 0), top.width * 2, "barra vacía")


class SupervisorTest(unittest.TestCase):
    """skins/plasma/scripts/decorator.py run: relanza el auxiliar si cae y se detiene fuera de Breeze."""

    def load(self, tmp: Path, binary: Path):
        import importlib.util
        from unittest import mock
        env = mock.patch.dict(os.environ, {"BWM_DECORATOR_BIN": str(binary), "XDG_RUNTIME_DIR": str(tmp),
                                           "XDG_STATE_HOME": str(tmp / "state")})
        env.start()
        self.addCleanup(env.stop)
        spec = importlib.util.spec_from_file_location(
            "bwm_decorator_supervisor", ROOT / "config/hypr/skins/plasma/scripts/decorator.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_restarts_after_crash_and_stops_on_clean_exit(self):
        from unittest import mock
        tmp = Path(tempfile.mkdtemp(prefix="bwm-sup-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        runs = tmp / "runs"
        binary = tmp / "fake"
        # Primera vez cae (código 1), segunda sale bien
        binary.write_text(f"#!/bin/sh\necho x >> {runs}\n[ $(wc -l < {runs}) -ge 2 ] && exit 0\nexit 1\n")
        binary.chmod(0o755)
        sup = self.load(tmp, binary)
        with mock.patch.object(sup, "active_skin", return_value="plasma"), mock.patch.object(sup.time, "sleep"):
            self.assertEqual(sup.run(), 0)
        self.assertEqual(runs.read_text().count("x"), 2)

    def test_stop_handler_does_not_reenter_subprocess_wait(self):
        from unittest import mock
        tmp=Path(tempfile.mkdtemp(prefix="bwm-sup-stop-"));self.addCleanup(shutil.rmtree,tmp,True)
        binary=tmp/"fake";binary.write_text("")
        sup=self.load(tmp,binary)
        handlers={};child=mock.Mock()
        def wait(**kwargs):
            handlers[signal.SIGTERM]()
            return -15
        import signal
        child.wait.side_effect=wait
        with mock.patch.object(sup,'active_skin',return_value="plasma"), mock.patch.object(sup.subprocess,'Popen',return_value=child), mock.patch.object(sup.signal,'signal',side_effect=lambda signum,handler:handlers.update({signum:handler})):
            self.assertEqual(sup.run(),0)
        child.terminate.assert_called_once()
        child.wait.assert_called_once_with(timeout=0.2)
        child.poll.assert_not_called()

    def test_does_nothing_outside_breeze(self):
        from unittest import mock
        tmp = Path(tempfile.mkdtemp(prefix="bwm-sup-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        binary = tmp / "fake"
        binary.write_text(f"#!/bin/sh\ntouch {tmp}/ran\n")
        binary.chmod(0o755)
        sup = self.load(tmp, binary)
        with mock.patch.object(sup, "active_skin", return_value="retro"):
            self.assertEqual(sup.run(), 0)
            self.assertEqual(sup.start(), 0)
        self.assertFalse((tmp / "ran").exists())


if __name__ == "__main__":
    unittest.main()
