#!/usr/bin/env python3
"""Supervisor de bwm-decorator, el auxiliar que dibuja las decoraciones de KDE para Breeze (F6a).

  decorator.py start    lo lanza (sólo en Breeze) como hijo de Hyprland (bwm_session.spawn)
  decorator.py run      bucle: ejecuta el auxiliar y lo relanza si muere, mientras la skin sea Breeze
  decorator.py stop     detiene el supervisor y el auxiliar
  decorator.py status   JSON: binario, supervisor y socket
  decorator.py build    compila e instala src/bwm-decorator (make install, mv atómico)

El binario se instala en ~/.local/share/bwm/bin/bwm-decorator (BWM_DECORATOR_BIN lo cambia) y
escucha en $XDG_RUNTIME_DIR/bwm-decorator.sock. Un candado por socket impide dos instancias.
"""
from __future__ import annotations

import fcntl
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

HOME = Path.home()
REPO = Path(__file__).resolve().parents[5]
SOURCE = REPO / "src" / "bwm-decorator"
BINARY = Path(os.environ.get("BWM_DECORATOR_BIN") or HOME / ".local/share/bwm/bin/bwm-decorator")
RUNTIME = Path(os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}")
SOCKET = RUNTIME / "bwm-decorator.sock"
STATE = Path(os.environ.get("XDG_STATE_HOME") or HOME / ".local/state") / "bwm" / "plasma"
SUPERVISOR_LOCK = RUNTIME / "bwm-decorator-supervisor.lock"
SCRIPTS = HOME / ".config" / "hypr" / "scripts"


def active_skin() -> str:
    try:
        data = json.loads((HOME / ".config/illogical-impulse/config.json").read_text(encoding="utf-8"))
        return data.get("appearance", {}).get("bwmTheme", "default")
    except Exception:
        return "default"


def start() -> int:
    if active_skin() != "plasma" or not BINARY.is_file():
        return 0
    sys.path.insert(0, str(SCRIPTS))
    import bwm_session
    STATE.mkdir(parents=True, exist_ok=True)
    bwm_session.spawn([sys.executable, str(Path(__file__).resolve()), "run"], str(STATE / "decorator.log"))
    return 0


def run() -> int:
    fd = os.open(SUPERVISOR_LOCK, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return 0  # ya hay un supervisor
    os.ftruncate(fd, 0)
    os.write(fd, str(os.getpid()).encode())
    child: subprocess.Popen | None = None

    def terminate(*_):
        if child and child.poll() is None:
            child.terminate()
            try:
                child.wait(5)
            except subprocess.TimeoutExpired:
                child.kill()
        sys.exit(0)

    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)
    crashes: list[float] = []
    while active_skin() == "plasma" and BINARY.is_file():
        child = subprocess.Popen([str(BINARY), "--socket", str(SOCKET)])
        code = child.wait()
        if code in (0, 3):  # salida limpia u otra instancia ya en marcha
            break
        now = time.monotonic()
        crashes = [t for t in crashes if now - t < 60] + [now]
        print(f"bwm-decorator terminó con {code}; se relanza", file=sys.stderr, flush=True)
        # Si cae en bucle, esperar más en vez de relanzarlo sin parar
        time.sleep(30 if len(crashes) >= 5 else 1)
    return 0


def _supervisor_pid() -> int | None:
    try:
        fd = os.open(SUPERVISOR_LOCK, os.O_RDWR)
    except FileNotFoundError:
        return None
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(fd, fcntl.LOCK_UN)
        return None  # nadie lo tiene
    except BlockingIOError:
        try:
            pid = int(os.read(fd, 32) or b"0")
        except ValueError:
            return None
        # Comprobar que el PID sigue siendo este supervisor antes de señalarlo
        try:
            args = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
        except OSError:
            return None
        if str(Path(__file__).resolve()).encode() in args and b"run" in args:
            return pid
        return None
    finally:
        os.close(fd)


def stop() -> int:
    pid = _supervisor_pid()
    if pid:
        os.kill(pid, signal.SIGTERM)
        for _ in range(100):
            if not Path(f"/proc/{pid}").exists():
                break
            time.sleep(0.05)
    return 0


def status() -> int:
    print(json.dumps({"binary": str(BINARY), "installed": BINARY.is_file(), "supervisor": _supervisor_pid(),
                      "socket": str(SOCKET), "listening": SOCKET.exists()}, indent=2))
    return 0


def build() -> int:
    prefix = BINARY.parent.parent
    return subprocess.run(["make", "-C", str(SOURCE), "install", f"PREFIX={prefix}"]).returncode


if __name__ == "__main__":
    commands = {"start": start, "run": run, "stop": stop, "status": status, "build": build}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        print(__doc__)
        sys.exit(1)
    sys.exit(commands[sys.argv[1]]())
