#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Opt-in loading of the native Plasma desktop provider at Hyprland start (R4 §255).

Run with python3 ~/.config/hypr/skins/plasma/scripts/native-desktops.py followed by:
  enable    opt in; takes effect at the next login
  disable   opt out; takes effect at the next login
  status    opt-in, installation, this session and last startup
  startup   only from autostart.sh, once per Hyprland start

The module is never loaded or unloaded during a running session by anything else
(hot load/unload is unsafe). Startup protection: a pending marker is kept for the
first STABLE_SECONDS after loading; if a later Hyprland start finds it still pending
(the previous session ended or crashed early), the opt-in is switched off and the user
is notified, so a faulty module cannot cause a login crash loop.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

MODULE = 'bwm-plasma-desktops'
STABLE_SECONDS = 60
# Only for check-desktops-hyprland.py --via-startup (disposable nested Hyprland).
if os.environ.get('BWM_R4_NESTED_HYPRLAND') == '1' and os.environ.get('BWM_NATIVE_DESKTOPS_STABLE_SECONDS', '').isdigit():
    STABLE_SECONDS = int(os.environ['BWM_NATIVE_DESKTOPS_STABLE_SECONDS'])
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', Path.home()/'.config'))
STATE = Path(os.environ.get('XDG_STATE_HOME', Path.home()/'.local/state'))/'bwm/plasma'
RUNTIME = Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}'))
OPT_IN = CONFIG/'bwm/native-desktops.json'
PLUGIN = CONFIG/'hypr/plugins'/(MODULE+'.so')
GUARD = STATE/'native-desktops-guard.json'
SESSION = RUNTIME/'bwm-native-desktops.json'


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name('.'+path.name+'.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    os.replace(temporary, path)


def read_json(path):
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def opted_in():
    value = read_json(OPT_IN)
    return value.get('version') == 1 and value.get('enabled') is True


def instance():
    return os.environ.get('HYPRLAND_INSTANCE_SIGNATURE', '')


def loaded_in_this_session():
    """Cheap check for adapters: the startup marker of THIS Hyprland instance."""
    marker = read_json(SESSION)
    return bool(instance()) and marker.get('instance') == instance() and marker.get('loaded') is True


def hyprctl(*args, timeout=3):
    return subprocess.run(['hyprctl', *args], capture_output=True, text=True, timeout=timeout)


def running_commit():
    try:
        return json.loads(hyprctl('-j', 'version').stdout).get('commit', '')
    except (ValueError, OSError, subprocess.SubprocessError):
        return ''


def built_for_running(commit):
    try:
        data = PLUGIN.read_bytes()
    except OSError:
        return False
    return bool(commit) and commit.encode() in data


def notify(message):
    try:
        subprocess.run(['notify-send', '-a', 'BWM', 'Escritorios nativos de Plasma', message], timeout=3,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        pass


def set_opt_in(enabled, reason=None):
    value = {'version': 1, 'enabled': enabled}
    if reason:
        value['reason'] = reason
    write_json(OPT_IN, value)


def startup(clock=time.monotonic, sleep=time.sleep):
    """Return a report; never raises. Called once per Hyprland start by autostart.sh."""
    report = {'version': 1, 'action': 'startup', 'loaded': False}
    current = instance()
    if not current:
        report['skipped'] = 'no-hyprland-instance'
        return report
    guard = read_json(GUARD)
    if guard.get('pending') is True and guard.get('instance') != current:
        # The previous start loaded the module but did not reach the stable mark.
        set_opt_in(False, 'previous-start-did-not-stabilise')
        GUARD.unlink(missing_ok=True)
        notify('El inicio anterior con el proveedor no terminó bien: queda desactivado. '
               'Reactívalo con python3 ~/.config/hypr/skins/plasma/scripts/native-desktops.py enable si fue un cierre normal.')
        report['skipped'] = 'disabled-after-unstable-start'
        return report
    if not opted_in():
        SESSION.unlink(missing_ok=True)
        report['skipped'] = 'not-opted-in'
        return report
    if not PLUGIN.is_file():
        report['error'] = 'module-not-installed'
        notify('No está instalado: make install en src/bwm-plasma-desktops.')
        return report
    deadline = clock()+30
    commit = ''
    while clock() < deadline and not commit:
        commit = running_commit()
        if not commit:
            sleep(.25)
    if not built_for_running(commit):
        report['error'] = 'module-built-for-another-hyprland'
        notify('El módulo no corresponde al Hyprland en ejecución: recompílalo (make install) y vuelve a entrar.')
        return report
    listed = hyprctl('plugin', 'list').stdout
    if MODULE not in listed:
        write_json(GUARD, {'version': 1, 'pending': True, 'instance': current, 'started': time.time()})
        reply = hyprctl('plugin', 'load', str(PLUGIN), timeout=10)
        if reply.stdout.strip() != 'ok':
            GUARD.unlink(missing_ok=True)
            report['error'] = 'load-failed: '+(reply.stdout or reply.stderr).strip()[:200]
            notify('No se pudo cargar el proveedor; sigue el escritorio sin él.')
            return report
    enable = hyprctl('eval', 'hl.config({ plugin = { bwm_plasma_desktops = { enabled = true } } })')
    try:
        diagnostic = json.loads(hyprctl('-j', MODULE).stdout)
    except ValueError:
        diagnostic = {}
    if enable.stdout.strip() != 'ok' or diagnostic.get('enabled') is not True:
        report['error'] = 'enable-failed'
        return report
    write_json(SESSION, {'version': 1, 'instance': current, 'loaded': True})
    report['loaded'] = True
    # Publish the shared count once now; the common shell keeps it current.
    script = Path(__file__).with_name('native_workspaces.py')
    subprocess.run([sys.executable, str(script), 'shared'], capture_output=True, timeout=5)
    sleep(STABLE_SECONDS)
    if instance() == current:
        GUARD.unlink(missing_ok=True)
        report['stable'] = True
    return report


def status():
    marker = read_json(SESSION)
    try:
        diagnostic = json.loads(hyprctl('-j', MODULE).stdout) if instance() else {}
    except (ValueError, OSError, subprocess.SubprocessError):
        diagnostic = {}
    return {'version': 1, 'optedIn': opted_in(), 'optIn': read_json(OPT_IN), 'installed': PLUGIN.is_file(),
            'builtForRunningHyprland': built_for_running(running_commit()),
            'loadedInThisSession': loaded_in_this_session(), 'sessionMarker': marker,
            'startupGuard': read_json(GUARD),
            'provider': {k: diagnostic.get(k) for k in ('enabled', 'providerAvailable', 'arbitrationState', 'desktops', 'current', 'lastError')
                         } if diagnostic else None}


def main(argv):
    if argv == ['enable']:
        set_opt_in(True)
        GUARD.unlink(missing_ok=True)
        print('Activado. Se cargará al iniciar sesión la próxima vez (no se carga en caliente).')
        return 0
    if argv == ['disable']:
        set_opt_in(False, 'user')
        print('Desactivado. Dejará de cargarse en el próximo inicio de sesión.')
        return 0
    if argv == ['status']:
        print(json.dumps(status(), ensure_ascii=False, indent=2))
        return 0
    if argv == ['startup']:
        report = startup()
        write_json(STATE/'native-desktops-last-startup.json', report)
        return 0 if report.get('loaded') or report.get('skipped') == 'not-opted-in' else 1
    print(__doc__.strip(), file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
