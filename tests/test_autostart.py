"""Autoarranque: qué ventanas son de cada app de inicio (por clase o por descender del proceso
lanzado), para que todas las suyas, no sólo la primera, vayan a su workspace."""
import importlib.util
import os
import subprocess
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'config/hypr/scripts/autostart-manager.py'
spec = importlib.util.spec_from_file_location('autostart_manager', SCRIPT)
am = importlib.util.module_from_spec(spec)
spec.loader.exec_module(am)


class EntryClassesTest(unittest.TestCase):
    def test_flatpak_wrapper_is_not_a_class(self):
        entry = {'file': 'dev.vencord.Vesktop.desktop', 'name': 'Vesktop', 'wm_class': 'vesktop',
                 'exec': '/usr/bin/flatpak run --branch=stable dev.vencord.Vesktop'}
        classes = am.entry_classes(entry)
        self.assertIn('vesktop', classes)
        self.assertIn('dev.vencord.Vesktop', classes)
        self.assertNotIn('flatpak', classes)

    def test_binary_and_name_in_both_cases(self):
        entry = {'file': 'steam.desktop', 'name': 'Steam', 'wm_class': '', 'exec': 'steam'}
        classes = am.entry_classes(entry)
        self.assertIn('steam', classes)
        self.assertIn('Steam', classes)
        self.assertEqual(len(classes), len(set(classes)))

    def test_workspace_only_for_1_to_10(self):
        self.assertEqual(am.target_workspace({'workspace': '4'}), 4)
        self.assertIsNone(am.target_workspace({'workspace': 'default'}))
        self.assertIsNone(am.target_workspace({'workspace': '11'}))


class DescendsFromTest(unittest.TestCase):
    def test_child_of_launched_process(self):
        parent = subprocess.Popen(['sh', '-c', 'sleep 5 & wait'])
        try:
            children = []
            for _ in range(50):
                out = subprocess.run(['pgrep', '-P', str(parent.pid)], capture_output=True, text=True).stdout
                children = [int(p) for p in out.split()]
                if children:
                    break
                subprocess.run(['sleep', '0.05'])
            self.assertTrue(children)
            self.assertTrue(am.descends_from(children[0], {parent.pid}))
            self.assertFalse(am.descends_from(os.getpid(), {parent.pid}))
        finally:
            parent.kill()
            parent.wait()


if __name__ == '__main__':
    unittest.main()
