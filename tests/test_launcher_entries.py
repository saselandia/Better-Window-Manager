"""Unity LauncherEntry listener of Breeze (skins/plasma/scripts/launcher-entries.py)."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'config/hypr/skins/plasma/scripts/launcher-entries.py'

spec = importlib.util.spec_from_file_location('launcher_entries', SCRIPT)
le = importlib.util.module_from_spec(spec)
spec.loader.exec_module(le)


class LogicTests(unittest.TestCase):
    def test_normalize_storage_ids(self):
        self.assertEqual(le.normalize('application://org.telegram.desktop.desktop'), 'org.telegram.desktop')
        self.assertEqual(le.normalize('application://Firefox.desktop'), 'firefox')
        self.assertEqual(le.normalize('vesktop.desktop'), 'vesktop')
        self.assertEqual(le.normalize(None), '')

    def test_apply_sanitizes_like_plasma_backend(self):
        entry = {'count': 0, 'countVisible': False, 'progress': 0, 'progressVisible': False, 'urgent': False}
        self.assertTrue(le.apply(entry, {'count': 7, 'count-visible': True, 'progress': 0.426,
                                         'progress-visible': True, 'urgent': True}))
        self.assertEqual(entry, {'count': 7, 'countVisible': True, 'progress': 43,
                                 'progressVisible': True, 'urgent': True})
        # NaN progress is zero; absurd counts are ignored; nothing else changes.
        self.assertTrue(le.apply(entry, {'progress': float('nan'), 'count': 2**40}))
        self.assertEqual((entry['progress'], entry['count']), (0, 7))
        self.assertFalse(le.apply(entry, {'count': 7}))
        le.apply(entry, {'progress': 5.0})
        self.assertEqual(entry['progress'], 100)


@unittest.skipUnless(shutil.which('dbus-run-session') and shutil.which('gdbus'), 'needs dbus-run-session and gdbus')
class PrivateBusTests(unittest.TestCase):
    def test_signals_on_a_private_session_bus(self):
        # The listener, the emitter and the name check all run on a private bus,
        # never on the user's session bus.
        driver = r'''
set -e
python3 -u "$SCRIPT" > "$OUT" &
pid=$!
for i in $(seq 1 50); do grep -q reset "$OUT" 2>/dev/null && break; sleep 0.1; done
gdbus call --session --dest org.freedesktop.DBus --object-path /org/freedesktop/DBus \
  --method org.freedesktop.DBus.NameHasOwner com.canonical.Unity >> "$OUT.owner"
python3 - <<'PY'
from gi.repository import Gio, GLib
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
bus.emit_signal(None, "/org/example/mail", "com.canonical.Unity.LauncherEntry", "Update",
    GLib.Variant("(sa{sv})", ("application://org.example.Mail.desktop",
        {"count": GLib.Variant("x", 3), "count-visible": GLib.Variant("b", True),
         "progress": GLib.Variant("d", 0.5), "progress-visible": GLib.Variant("b", True)})))
bus.flush_sync(None)
import time; time.sleep(0.5)
PY
for i in $(seq 1 50); do grep -q removed "$OUT" 2>/dev/null && break; sleep 0.1; done
kill $pid
'''
        tmp = Path(os.environ.get('XDG_RUNTIME_DIR', '/tmp')) / f'bwm-le-test-{os.getpid()}'
        out = tmp.with_suffix('.jsonl')
        try:
            env = {k: v for k, v in os.environ.items() if k != 'DBUS_SESSION_BUS_ADDRESS'}
            env.update(SCRIPT=str(SCRIPT), OUT=str(out))
            result = subprocess.run(['dbus-run-session', '--', 'bash', '-c', driver], env=env,
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            lines = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
            self.assertEqual(lines[0], {'reset': True})
            self.assertIn({'id': 'org.example.mail', 'count': 3, 'countVisible': True,
                           'progress': 50, 'progressVisible': True, 'urgent': False}, lines)
            # The emitter left the bus: its entry is forgotten, as Backend::onServiceUnregistered.
            self.assertEqual(lines[-1], {'id': 'org.example.mail', 'removed': True})
            self.assertIn('true', Path(str(out) + '.owner').read_text())
        finally:
            for p in (out, Path(str(out) + '.owner')):
                p.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
