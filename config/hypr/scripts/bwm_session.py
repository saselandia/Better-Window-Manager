#!/usr/bin/env python3
"""Procesos duraderos de la sesión (Quickshell, swaync, hyprpolkitagent): común a todas las skins.

Un proceso lanzado desde una terminal, un hook o una sesión de IA hereda el cgroup y la vida de quien
lo lanzó: el 2026-11-08 la barra (Quickshell) y window-guard.py, relanzados desde la app de Claude,
murieron a la vez sin ningún fallo propio. Por eso se piden a Hyprland (`hl.dsp.exec_cmd`): quedan
como hijos del compositor, en el scope de la sesión y con su entorno, igual que los de autostart.sh.

Uso: bwm_session.py ensure-shell   (arranca Quickshell `ii` si no hay ninguna instancia)
"""
import fcntl
import json
import os
import shlex
import signal
import subprocess
import sys
from pathlib import Path

QT_PLATFORM_DIRS = (Path('/usr/lib64/qt6/plugins/platformthemes'),
                    Path('/usr/lib/qt6/plugins/platformthemes'),
                    Path('/usr/lib/x86_64-linux-gnu/qt6/plugins/platformthemes'))
SHELL_LOG = f"/run/user/{os.getuid()}/quickshell-session.log"
THEME_LOCK = "/tmp/bwm-theme-manager.lock"


def _lua_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def spawn(argv: list, log: str = None, *, allow_fallback: bool = True) -> bool:
    """Lanza argv como hijo de Hyprland; si no hay compositor, como proceso aparte. ¿Lanzado?"""
    command = shlex.join(argv) + (f" >{shlex.quote(log)} 2>&1" if log else "")
    try:
        out = subprocess.run(["hyprctl", "dispatch", f"hl.dsp.exec_cmd({_lua_string(command)})"],
                             capture_output=True, text=True, timeout=5)
        if out.returncode == 0 and out.stdout.strip() == "ok":
            return True
    except (OSError, subprocess.SubprocessError):
        pass
    if not allow_fallback:
        return False
    env = os.environ.copy()
    env.pop("BWM_SKIN_SWITCH", None)
    try:
        subprocess.Popen(["sh", "-c", "exec " + command], env=env, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True,
                         preexec_fn=lambda: signal.pthread_sigmask(signal.SIG_SETMASK, []))
        return True
    except OSError:
        return False


def shell_instances() -> list:
    """Instancias vivas de la config `ii` (las de prueba con `qs -p` no cuentan)."""
    try:
        out = subprocess.run(["quickshell", "-c", "ii", "list", "-j"],
                             capture_output=True, text=True, timeout=5).stdout
        running = json.loads(out or "[]")
    except (OSError, ValueError, subprocess.SubprocessError):
        # Sin instancias `list -j` no imprime JSON
        return []
    return [i for i in running if isinstance(i, dict) and i.get("pid")
            and os.path.exists(f"/proc/{i['pid']}")]


def theme_manager_busy() -> bool:
    """¿El gestor de skins está a mitad de un cambio (puede estar reiniciando el shell)?"""
    try:
        with open(THEME_LOCK, "a") as fd:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return True
            fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError:
        pass
    return False


def shell_command() -> list:
    """Stable Qt backend for the long-lived shell, independent of the boot skin.

    App launchers retain Hyprland's per-skin environment. Only the shell uses the KDE
    backend when installed so its existing process observes KDE icon/palette changes.
    Do not use QIcon::setThemeName/QS_ICON_THEME: that bypasses native icon engines.
    """
    qml = str(Path(os.environ.get('XDG_DATA_HOME', Path.home()/'.local/share'))/'bwm/qml')
    if os.environ.get('QML_IMPORT_PATH'):
        qml += ':' + os.environ['QML_IMPORT_PATH']
    config = Path(os.environ.get('XDG_CONFIG_HOME', Path.home()/'.config'))
    defaults = str(config/'kdedefaults')
    dirs = [defaults] + [p for p in os.environ.get('XDG_CONFIG_DIRS', '/etc/xdg').split(':') if p and p != defaults]
    env = ['env', 'QML_IMPORT_PATH=' + qml, 'XDG_CONFIG_DIRS=' + ':'.join(dirs)]
    for library, name in (('KDEPlasmaPlatformTheme6.so', 'kde'), ('libqt6ct.so', 'qt6ct'),
                          ('libqxdgdesktopportal.so', 'xdgdesktopportal')):
        if any((base/library).is_file() for base in QT_PLATFORM_DIRS):
            env.append('QT_QPA_PLATFORMTHEME=' + name)
            break
    return env + ['quickshell', '-n', '-c', 'ii']


def start_shell() -> bool:
    return spawn(shell_command(), SHELL_LOG)


def sync_activation_environment() -> bool:
    """Request export from Hyprland's *current* child environment after config reload.

    The caller may be a shell born in another skin. Never export that caller's stale
    variables as fallback. Explicit user Lua overrides are preserved by this route.
    """
    return spawn(['dbus-update-activation-environment', '--systemd', 'QT_QPA_PLATFORMTHEME',
                  'XDG_CONFIG_DIRS', 'XDG_MENU_PREFIX', 'OMARCHY_PATH', 'QML_IMPORT_PATH'],
                 allow_fallback=False)


def ensure_shell() -> bool:
    """Arranca el shell si no hay ninguno; nunca un segundo (regla 2). ¿Lo ha arrancado?"""
    if shell_instances() or theme_manager_busy():
        return False
    return start_shell()


if __name__ == "__main__":
    if sys.argv[1:] == ["ensure-shell"]:
        print("arrancado" if ensure_shell() else "ya en marcha")
        sys.exit(0)
    print(__doc__.strip().splitlines()[-1], file=sys.stderr)
    sys.exit(2)
