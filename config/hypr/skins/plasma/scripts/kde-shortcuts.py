#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Atajos globales de KDE en Breeze (Breeze III, T5): servicio org.kde.kglobalaccel.

  kde-shortcuts.py build    compila e instala src/bwm-kglobalaccel en ~/.local/share/bwm/bin/
  kde-shortcuts.py install  instala atómicamente el binario compilado
  kde-shortcuts.py start    arranca bwm-kglobalaccel (sólo en Breeze)
  kde-shortcuts.py stop     lo detiene: retira sus binds de Hyprland y su archivo de estado
  kde-shortcuts.py status   JSON con el estado del binario, el proceso y el demonio

Los atajos de BWM mandan: el demonio registra cada bind de BWM como componente «bwm» y
sólo convierte en binds de Hyprland las teclas de KDE que BWM no usa (src/bwm-kglobalaccel).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[4]
SOURCE_DIR = REPO_ROOT / "src" / "bwm-kglobalaccel"
BUILD_DIR = REPO_ROOT / "build" / "bwm-kglobalaccel"
BIN_DIR = Path.home() / ".local" / "share" / "bwm" / "bin"
BINARY = BIN_DIR / "bwm-kglobalaccel"
RUNTIME_DIR = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
STATE_DIR = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "bwm"
STATE_FILE = STATE_DIR / "kde-shortcuts.lua"
LOG_FILE = Path.home() / ".local" / "state" / "bwm" / "kde-shortcuts.log"
SERVICE = "org.kde.kglobalaccel"


def current_skin() -> str:
    cfg = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "illogical-impulse" / "config.json"
    try:
        return json.loads(cfg.read_text()).get("appearance", {}).get("bwmTheme", "default")
    except (OSError, ValueError):
        return "default"


def is_daemon_pid(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        if Path(f"/proc/{pid}").stat().st_uid != os.getuid():
            return False
        cmd = Path(f"/proc/{pid}/cmdline").read_bytes().decode("utf-8", "ignore").rstrip("\0").split("\0")
        env = dict(item.split(b"=", 1) for item in Path(f"/proc/{pid}/environ").read_bytes().split(b"\0") if b"=" in item)
        # A test daemon (private bus, own runtime directory) is never this session's daemon.
        if env.get(b"XDG_RUNTIME_DIR", b"").decode() != str(RUNTIME_DIR):
            return False
    except OSError:
        return False
    return len(cmd) == 1 and Path(cmd[0]).name == "bwm-kglobalaccel"


def find_running_pids() -> list[int]:
    return [int(e.name) for e in Path("/proc").iterdir() if e.name.isdigit() and is_daemon_pid(int(e.name))]


def daemon_status() -> dict | None:
    if not BINARY.is_file():
        return None
    try:
        r = subprocess.run([str(BINARY), "--status"], capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0 or not r.stdout.strip():
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


def service_owner_pid() -> int | None:
    try:
        r = subprocess.run(["busctl", "--user", "--auto-start=no", "--timeout=500ms", "call", "org.freedesktop.DBus",
                            "/org/freedesktop/DBus", "org.freedesktop.DBus", "GetConnectionUnixProcessID", "s", SERVICE],
                           capture_output=True, text=True, timeout=1)
    except (OSError, subprocess.SubprocessError):
        return None
    parts = r.stdout.split()
    return int(parts[1]) if r.returncode == 0 and len(parts) == 2 and parts[1].isdigit() else None


def install_binary() -> int:
    built = BUILD_DIR / "bwm-kglobalaccel"
    if not built.is_file():
        print(f"No existe el binario compilado: {built}", file=sys.stderr)
        return 1
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".bwm-kglobalaccel-", dir=BIN_DIR)
    os.close(fd)
    try:
        shutil.copy2(built, tmp_name)
        os.chmod(tmp_name, 0o755)
        os.replace(tmp_name, BINARY)  # Un demonio en marcha conserva su inodo.
    finally:
        Path(tmp_name).unlink(missing_ok=True)
    return 0


def build_and_install() -> int:
    for command in (["cmake", "-S", str(SOURCE_DIR), "-B", str(BUILD_DIR), "-DCMAKE_BUILD_TYPE=RelWithDebInfo"],
                    ["cmake", "--build", str(BUILD_DIR), f"-j{os.cpu_count() or 4}"]):
        if subprocess.run(command, check=False).returncode != 0:
            return 1
    return install_binary()


def start_daemon() -> int:
    if current_skin() != "plasma":
        return 0
    if not BINARY.is_file() or not os.access(BINARY, os.X_OK):
        return 0
    if find_running_pids():
        return 0
    owner = service_owner_pid()
    if owner is not None:
        # Otro dueño (kglobalacceld de X11, una sesión de Plasma…): un solo dueño por servicio.
        print(f"{SERVICE} ya tiene dueño (PID {owner}); no se arranca bwm-kglobalaccel.", file=sys.stderr)
        return 1
    sys.path.insert(0, str(SCRIPT_DIR.parents[2] / "scripts"))
    import bwm_session
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Hijo de Hyprland: entorno de la sesión para las apps que lanza un atajo (.desktop con
    # X-KDE-Shortcuts) y vida independiente de quien lo pidió.
    command = ["env", "-u", "BWM_SKIN_SWITCH", "-u", "WAYLAND_SOCKET", "QT_QPA_PLATFORM=wayland", str(BINARY)]
    if not bwm_session.spawn(command, str(LOG_FILE), allow_fallback=False):
        print("No se pudo iniciar bwm-kglobalaccel desde Hyprland.", file=sys.stderr)
        return 1
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if daemon_status():
            return 0
        time.sleep(0.05)
    print(f"bwm-kglobalaccel no confirmó el arranque; consulta {LOG_FILE}.", file=sys.stderr)
    stop_daemon()
    return 1


def stop_daemon() -> int:
    pids = find_running_pids()
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)  # Retira sus binds y guarda kglobalshortcutsrc.
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline and any(is_daemon_pid(p) for p in pids):
        time.sleep(0.05)
    for pid in pids:
        if is_daemon_pid(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    # Tras un SIGKILL o una caída, sus binds no deben volver en la próxima recarga.
    STATE_FILE.unlink(missing_ok=True)
    return 0


def status() -> int:
    pids = find_running_pids()
    info = {
        "binary": str(BINARY),
        "installed": BINARY.is_file() and os.access(BINARY, os.X_OK),
        "running": bool(pids),
        "pid": pids[0] if pids else None,
        "serviceOwner": service_owner_pid(),
        "daemon": daemon_status() if pids else None,
    }
    print(json.dumps(info, indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "status"
    actions = {"build": build_and_install, "install": install_binary, "start": start_daemon,
               "stop": stop_daemon, "status": status}
    if command not in actions:
        print(__doc__, file=sys.stderr)
        return 2
    return actions[command]()


if __name__ == "__main__":
    sys.exit(main())
