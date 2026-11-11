"""Fase 8 de docs/BREEZE_PLAN.md: cálculo de maximizar/restaurar como KWin (kwin-window.py).

Sólo las funciones puras (sin Hyprland): modos por ejes, geometría de restauración por eje como
XdgToplevelWindow::maximize de kwin v6.7.5, mosaico rápido, etiquetas y marco/contenido.
"""
import importlib.util
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("kwin_window", ROOT / "config/hypr/skins/plasma/scripts/kwin-window.py")
kw = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kw)

AREA = (0, 720, 2560, 1396)      # MSI 1440p menos un panel de 44 px abajo
FRAME = (300, 900, 1000, 700)    # marco de la ventana (barra incluida)


class ModesTest(unittest.TestCase):
    def test_next_mode_like_kwin(self):
        self.assertEqual(kw.next_mode(kw.RESTORE, "toggle"), kw.FULL)
        self.assertEqual(kw.next_mode(kw.FULL, "toggle"), kw.RESTORE)
        self.assertEqual(kw.next_mode(kw.VERTICAL, "toggle"), kw.FULL)        # izquierdo: completo
        self.assertEqual(kw.next_mode(kw.RESTORE, "vertical"), kw.VERTICAL)   # central
        self.assertEqual(kw.next_mode(kw.VERTICAL, "horizontal"), kw.FULL)    # derecho: suma el eje
        self.assertEqual(kw.next_mode(kw.FULL, "vertical"), kw.HORIZONTAL)    # quita un eje
        self.assertEqual(kw.next_mode(kw.FULL, "restore"), kw.RESTORE)

    def test_mode_from_tags(self):
        self.assertEqual(kw.mode_from_tags(["bwm-max-v", "bwm-max-h*", "bwm-maximized"]), kw.FULL)
        self.assertEqual(kw.mode_from_tags(["bwm-max-h"]), kw.HORIZONTAL)
        self.assertEqual(kw.mode_from_tags(["snapped"]), kw.RESTORE)
        self.assertEqual(kw.mode_from_tags(None), kw.RESTORE)

    def test_tag_changes(self):
        self.assertEqual(kw.tag_changes(kw.RESTORE, kw.FULL), ["+bwm-max-v", "+bwm-max-h", "+bwm-maximized"])
        self.assertEqual(kw.tag_changes(kw.FULL, kw.HORIZONTAL), ["-bwm-max-v", "-bwm-maximized"])
        self.assertEqual(kw.tag_changes(kw.VERTICAL, kw.RESTORE), ["-bwm-max-v"])


class GeometryTest(unittest.TestCase):
    def test_full_and_exact_restore(self):
        frame, restore = kw.maximize_geometry(FRAME, AREA, kw.RESTORE, kw.FULL, None)
        self.assertEqual(frame, AREA)
        self.assertEqual(restore, FRAME)
        back, _ = kw.maximize_geometry(frame, AREA, kw.FULL, kw.RESTORE, restore)
        self.assertEqual(back, FRAME)

    def test_vertical_then_horizontal_then_restore(self):
        frame, restore = kw.maximize_geometry(FRAME, AREA, kw.RESTORE, kw.VERTICAL, None)
        self.assertEqual(frame, (300, 720, 1000, 1396))          # x y ancho se quedan
        frame, restore = kw.maximize_geometry(frame, AREA, kw.VERTICAL, kw.FULL, restore)
        self.assertEqual(frame, AREA)
        self.assertEqual(restore, FRAME)                          # el eje vertical no se pisa
        frame, restore = kw.maximize_geometry(frame, AREA, kw.FULL, kw.HORIZONTAL, restore)
        self.assertEqual(frame, (0, 900, 2560, 700))              # vuelve el vertical, a su centro
        frame, _ = kw.maximize_geometry(frame, AREA, kw.HORIZONTAL, kw.RESTORE, restore)
        self.assertEqual(frame, FRAME)

    def test_restore_keeps_center_of_saved_axis(self):
        # Mover una ventana maximizada en vertical no cambia la restauración de ese eje
        frame, restore = kw.maximize_geometry(FRAME, AREA, kw.RESTORE, kw.VERTICAL, None)
        moved = (800, frame[1], frame[2], frame[3])
        back, _ = kw.maximize_geometry(moved, AREA, kw.VERTICAL, kw.RESTORE, restore)
        self.assertEqual(back, (800, 900, 1000, 700))             # x actual, y/alto de antes

    def test_quick_tile_keeps_pre_tile_restore(self):
        tile = (0, 720, 1280, 1396)
        pre_tile = (500, 1000, 900, 600)
        frame, restore = kw.maximize_geometry(tile, AREA, kw.RESTORE, kw.FULL, pre_tile, tiled=True)
        self.assertEqual(frame, AREA)
        self.assertEqual(restore, pre_tile)
        back, _ = kw.maximize_geometry(frame, AREA, kw.FULL, kw.RESTORE, restore)
        self.assertEqual(back, pre_tile)

    def test_no_valid_restore_uses_a_preferred_size(self):
        # Ventana abierta ya maximizada (KWin pide a la app su tamaño preferido): no 0×0
        frame, _ = kw.maximize_geometry(AREA, AREA, kw.FULL, kw.RESTORE, None, tiled=True)
        self.assertGreater(frame[2], 100)
        self.assertGreater(frame[3], 100)
        self.assertLess(frame[2], AREA[2])

    def test_same_mode_is_a_no_op(self):
        self.assertEqual(kw.maximize_geometry(FRAME, AREA, kw.FULL, kw.FULL, FRAME), (FRAME, FRAME))

    def test_second_monitor_area(self):
        lg = (2560, 0, 2560, 1440)  # LG a escala 1,5: 3840/1,5
        frame, restore = kw.maximize_geometry((3000, 200, 900, 600), lg, kw.RESTORE, kw.FULL, None)
        self.assertEqual(frame, lg)
        self.assertEqual(restore, (3000, 200, 900, 600))


class FrameTest(unittest.TestCase):
    def test_frame_and_content_round_trip(self):
        borders = {"left": 0, "top": 28, "right": 0, "bottom": 0}
        client = {"at": [300, 928], "size": [1000, 672]}
        frame = kw.frame_from_client(client, borders)
        self.assertEqual(frame, FRAME)
        # Maximizado: el contenido deja la barra dentro del área útil (KWin maximiza el marco)
        self.assertEqual(kw.content_from_frame(AREA, borders), (0, 748, 2560, 1368))
        aurorae = {"left": 4, "top": 30, "right": 4, "bottom": 4}
        self.assertEqual(kw.content_from_frame(kw.frame_from_client(client, aurorae), aurorae), (300, 928, 1000, 672))


if __name__ == "__main__":
    unittest.main()


class TaskActivationTests(unittest.TestCase):
    def test_focus_raises_the_requested_pid_without_minimizing(self):
        client={'address':'0x123','pid':17}
        with mock.patch.object(kw,'run_lua') as run:
            kw.focus(client)
        lua=run.call_args.args[0]
        self.assertIn('w.pid ~= 17',lua)
        self.assertIn('bring_to_top',lua)
        self.assertIn('mode = "top"',lua)
        self.assertNotIn('minimize',lua)

    def test_reused_address_from_panel_does_nothing(self):
        with mock.patch.object(kw,'find_client',return_value={'address':'0x123','pid':99}), mock.patch.object(kw,'focus') as focus:
            self.assertEqual(kw.main(['--pid','17','focus','0x123']),1)
            focus.assert_not_called()
