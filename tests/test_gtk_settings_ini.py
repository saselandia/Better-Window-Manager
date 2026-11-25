"""Regresión §373: escritores simultáneos de gtk-3.0/settings.ini no corrompen la cabecera."""
import multiprocessing as mp
import os
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "config/hypr/scripts"
sys.path.insert(0, str(SCRIPTS))
import bwm_gtk_ini  # noqa: E402

BASE = "[Settings]\ngtk-theme-name=BWM-1\ngtk-icon-theme-name=breeze-dark\ngtk-cursor-theme-size=48\n"


def worker(path, key, values, rounds):
    def make(value):
        def edit(text):
            if not text.strip():
                return text
            out = [f"{key}={value}" if l.startswith(key + "=") else l for l in text.splitlines()]
            return "\n".join(out) + "\n"
        return edit
    for i in range(rounds):
        bwm_gtk_ini.update(Path(path), make(values[i % len(values)]))


class GtkSettingsIniTests(unittest.TestCase):
    def test_concurrent_writers_keep_header(self):
        with tempfile.TemporaryDirectory() as d:
            os.environ["XDG_RUNTIME_DIR"] = d
            path = Path(d) / "settings.ini"
            path.write_text(BASE)
            jobs = [("gtk-theme-name", ["BWM-1", "BWM-2"]),
                    ("gtk-icon-theme-name", ["breeze-dark", "Yaru-yellow"]),
                    ("gtk-cursor-theme-size", ["48", "40"])]
            ctx = mp.get_context("fork")
            procs = [ctx.Process(target=worker, args=(str(path), k, v, 200)) for k, v in jobs]
            for p in procs:
                p.start()
            seen_bad = 0
            while any(p.is_alive() for p in procs):
                try:
                    text = path.read_text()
                except FileNotFoundError:
                    seen_bad += 1
                    continue
                if not text.startswith("[Settings]\n"):
                    seen_bad += 1
            for p in procs:
                p.join()
                self.assertEqual(p.exitcode, 0)
            text = path.read_text()
            self.assertEqual(seen_bad, 0)
            self.assertTrue(text.startswith("[Settings]\n"))
            self.assertEqual(len(text.splitlines()), 4)
            self.assertEqual(text.count("[Settings]"), 1)

    def test_unchanged_text_does_not_write(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "settings.ini"
            path.write_text(BASE)
            ino = path.stat().st_ino
            self.assertFalse(bwm_gtk_ini.update(path, lambda t: t))
            self.assertEqual(path.stat().st_ino, ino)

    def test_symlinked_directory_keeps_link(self):
        with tempfile.TemporaryDirectory() as d:
            real = Path(d) / "repo" / "gtk-3.0"
            real.mkdir(parents=True)
            (real / "settings.ini").write_text(BASE)
            link = Path(d) / "gtk-3.0"
            link.symlink_to(real)
            bwm_gtk_ini.update(link / "settings.ini", lambda t: t.replace("BWM-1", "BWM-2"))
            self.assertTrue(link.is_symlink())
            self.assertIn("BWM-2", (real / "settings.ini").read_text())


if __name__ == "__main__":
    unittest.main()
