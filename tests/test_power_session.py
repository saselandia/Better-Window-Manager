"""Cierre de sesión con dos ventanas Firefox: nunca cerrarlas individualmente.

Sólo se extrae close_all_windows; todas las acciones de procesos/compositor se
sustituyen por funciones Bash. No se ejecuta el apagado ni se toca una app real.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'config/hypr/scripts/bwm-power'


class FirefoxSessionCloseTest(unittest.TestCase):
    def run_close(self, executable='/opt/firefox/firefox-bin', signal_status=0, dry_run=0):
        source = SCRIPT.read_text()
        function = source[source.index('close_all_windows() {'):source.index('\nexit_session() {')]
        clients = [dict(address='0x1', pid=12345, **{'class': 'firefox-bin'}),
                   dict(address='0x2', pid=12345, **{'class': 'firefox-bin'}),
                   dict(address='0x3', pid=54321, **{'class': 'kitty'})]
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / 'actions'
            # kill is a Bash builtin: override it as well as external commands.
            harness = r'''
set -uo pipefail
CLOSE_TIMEOUT=1
hyprctl() {
  if [[ $1 == clients ]]; then printf '%s' "$CLIENTS";
  else printf 'hyprctl %s\n' "$*" >> "$ACTION_LOG"; fi
}
readlink() { printf '%s\n' "$EXE"; }
kill() { printf 'kill %s\n' "$*" >> "$ACTION_LOG"; return "$SIGNAL_STATUS"; }
pidwait() { :; }
timeout() { :; }
'''
            result = subprocess.run(['bash', '-c', harness + function + '\nclose_all_windows'],
                                    env={**os.environ, 'CLIENTS': json.dumps(clients),
                                         'ACTION_LOG': str(log), 'EXE': executable,
                                         'SIGNAL_STATUS': str(signal_status), 'dry_run': str(dry_run)},
                                    capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, '')
            return log.read_text().splitlines() if log.exists() else [], result.stdout

    def test_quits_firefox_once_and_closes_other_apps(self):
        actions, _ = self.run_close()
        self.assertEqual(actions, ['kill -TERM 12345',
                                  'hyprctl dispatch hl.dsp.window.close({ window = "address:0x3" })'])

    def test_does_not_signal_an_unrelated_executable(self):
        actions, _ = self.run_close(executable='/usr/bin/kitty')
        self.assertEqual(len(actions), 3)
        self.assertTrue(all(a.startswith('hyprctl ') for a in actions))

    def test_failed_signal_falls_back_to_window_close(self):
        actions, _ = self.run_close(signal_status=1)
        self.assertEqual(len(actions), 4)
        self.assertIn('address:0x1', actions[1])
        self.assertIn('address:0x2', actions[2])

    def test_dry_run_has_no_effects(self):
        actions, output = self.run_close(dry_run=1)
        self.assertEqual(actions, [])
        self.assertIn('3 ventanas', output)

    def test_session_exit_orders_panel_flush_before_app_and_compositor_close(self):
        source=SCRIPT.read_text()
        functions=source[source.index('stop_plasma_preview() {'):source.index('\nif [[ $stage == "--inhibited" ]]')]
        harness=r'''
notify-send() { :; }
timeout() { printf 'panel-hook %s %s\n' "$1" "${*: -1}" >&2; return "$HOOK_STATUS"; }
close_all_windows() { echo apps >&2; }
run() { echo compositor >&2; }
message=closing
command=(hyprshutdown)
'''
        for status,dry_run,instance,expected in (
            ('0','0','fixture',['panel-hook 8s session-exit','apps','compositor']),
            ('1','0','fixture',['panel-hook 8s session-exit','[BWM] No se pudo confirmar el guardado del panel de prueba antes de cerrar la sesión.','apps','compositor']),
            ('0','1','fixture',['apps','compositor']),
            ('0','0','',['apps','compositor']),
        ):
            with self.subTest(status=status,dry_run=dry_run,instance=instance):
                result=subprocess.run(['bash','-c',harness+functions+'\nexit_session',str(SCRIPT)],
                    env=dict(os.environ,HOOK_STATUS=status,dry_run=dry_run,HYPRLAND_INSTANCE_SIGNATURE=instance),
                    capture_output=True,text=True,timeout=5)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(result.stderr.splitlines(),expected)


if __name__ == '__main__':
    unittest.main()
