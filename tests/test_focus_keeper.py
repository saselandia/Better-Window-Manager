"""Reinicios de apps por un cambio de tema: sólo se deshace un robo de foco de la app recién
abierta, nunca un cambio de workspace hecho por el usuario mientras tanto."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'config/hypr/scripts'))
import bwm_windows


class FakeHypr:
    def __init__(self):
        self.ws = 1                     # workspace visible en el único monitor
        self.active = {'address': '0xa', 'pid': 1, 'class': 'kitty', 'workspace': {'id': 1}}
        self.clients = [self.active]

    def json(self, cmd):
        if cmd == 'monitors':
            return [{'name': 'out', 'description': 'mon', 'focused': True, 'activeWorkspace': {'id': self.ws}}]
        if cmd == 'clients':
            return list(self.clients)
        if cmd == 'activewindow':
            return self.active
        return []


class FocusKeeperTests(unittest.TestCase):
    def setUp(self):
        self.h = FakeHypr()
        self.clock = [100.0]
        patches = [patch.object(bwm_windows, 'hypr_json', self.h.json),
                   patch.object(bwm_windows, 'mpris_playing', lambda: []),
                   patch.object(bwm_windows, 'restore_focus', self.restore),
                   patch('subprocess.run')]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.restored = []
        self.keeper = bwm_windows.FocusKeeper(lambda c: c.get('class') == 'steam' and c['pid'] != 9)
        self.keeper._time = lambda: self.clock[0]

    def restore(self, snap):
        self.restored.append(dict(snap['workspaces']))
        self.h.ws = snap['workspaces']['out']

    def new_window(self, ws):
        w = {'address': '0xs', 'pid': 50, 'class': 'steam', 'workspace': {'id': ws}}
        self.h.clients.append(w)
        return w

    def test_user_switch_meanwhile_is_kept(self):
        self.h.ws = 3                    # el usuario cambia de workspace mientras Steam se reabre
        self.keeper.check()
        self.new_window(4)               # Steam aparece en el suyo, sin foco
        self.keeper.check()
        self.assertEqual(self.restored, [])
        self.assertEqual(self.h.ws, 3)

    def test_steal_right_after_mapping_is_undone(self):
        self.keeper.check()
        w = self.new_window(4)
        self.h.ws, self.h.active = 4, w  # focus_on_activate: te lleva a su workspace
        self.keeper.check()
        self.assertEqual(self.restored, [{'out': 1}])
        self.assertEqual(self.h.ws, 1)

    def test_focusing_the_app_later_on_purpose_is_kept(self):
        self.keeper.check()
        w = self.new_window(4)
        self.keeper.check()
        self.clock[0] += 10              # mucho después el usuario va a Steam
        self.h.ws, self.h.active = 4, w
        self.keeper.check()
        self.assertEqual(self.restored, [])


if __name__ == '__main__':
    unittest.main()
