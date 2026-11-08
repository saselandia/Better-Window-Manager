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

SHELL_CMD = ["quickshell", "-n", "-c", "ii"]
SHELL_LOG = f"/run/user/{os.getuid()}/quickshell-session.log"
THEME_LOCK = "/tmp/bwm-theme-manager.lock"


def _lua_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def spawn(argv: list, log: str = None) -> bool:
    """Lanza argv como hijo de Hyprland; si no hay compositor, como proceso aparte. ¿Lanzado?"""
    command = shlex.join(argv) + (f" >{shlex.quote(log)} 2>&1" if log else "")
    try:
        out = subprocess.run(["hyprctl", "dispatch", f"hl.dsp.exec_cmd({_lua_string(command)})"],
                             capture_output=True, text=True, timeout=5)
        if out.returncode == 0 and out.stdout.strip() == "ok":
            return True
    except (OSError, subprocess.SubprocessError):
        pass
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


def start_shell() -> bool:
    return spawn(SHELL_CMD, SHELL_LOG)


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
