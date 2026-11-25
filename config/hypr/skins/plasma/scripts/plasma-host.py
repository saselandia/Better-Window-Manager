#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Gestor del anfitrión nativo de Plasma (bwm-plasma-host --session) para Breeze (R4–R5).

  plasma-host.py build    compila e instala src/bwm-plasma-host en ~/.local/share/bwm/bin/
  plasma-host.py install  instala atómicamente el binario compilado
  plasma-host.py start    arranca bwm-plasma-host --session (sólo en Breeze)
  plasma-host.py stop     detiene bwm-plasma-host limpiamente (guardando layout)
  plasma-host.py status   JSON con estado del binario y proceso
  plasma-host.py ready    éxito sólo si el PID de la marca ready sigue siendo el host
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
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
SOURCE_DIR = REPO_ROOT / "src" / "bwm-plasma-host"
BUILD_DIR = REPO_ROOT / "build" / "bwm-plasma-host"
BIN_DIR = Path.home() / ".local" / "share" / "bwm" / "bin"
BINARY = BIN_DIR / "bwm-plasma-host"
RUNTIME_DIR = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
PID_FILE = RUNTIME_DIR / "bwm-plasma-host.pid"
READY_FILE = RUNTIME_DIR / "bwm-plasma-host.ready"
STATE_DIR = Path.home() / ".local" / "state" / "bwm"
LOG_FILE = STATE_DIR / "plasma-host.log"
TRAY_SERVICE = "org.kde.StatusNotifierWatcher"


def tray_call(*arguments):
    try:
        return subprocess.run(
            ["busctl", "--user", "--auto-start=no", "--timeout=500ms", *arguments],
            capture_output=True, text=True, timeout=1,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.SubprocessError):
        return None


def ensure_tray_watcher():
    """Activate only a missing watcher object owned by kded, keeping its other modules."""
    probe = tray_call("get-property", TRAY_SERVICE, "/StatusNotifierWatcher", TRAY_SERVICE,
                      "RegisteredStatusNotifierItems")
    if probe is None or probe.returncode == 0 or not any(
        reason in probe.stderr for reason in ("No such object", "UnknownObject")
    ):
        return
    owner = tray_call("call", "org.freedesktop.DBus", "/org/freedesktop/DBus",
                      "org.freedesktop.DBus", "GetConnectionUnixProcessID", "s", TRAY_SERVICE)
    try:
        if owner is None or owner.returncode != 0:
            return
        signature, value = owner.stdout.strip().split()
        process = Path("/proc") / str(int(value))
        if signature != "u" or process.stat().st_uid != os.getuid() or (process / "exe").resolve(strict=True).name != "kded6":
            return
    except (OSError, ValueError):
        return
    loaded = tray_call("call", "org.kde.kded6", "/kded", "org.kde.kded6", "loadModule", "s", "statusnotifierwatcher")
    if loaded is None or loaded.returncode != 0 or loaded.stdout.strip() != "b true":
        return
    available = tray_call("get-property", TRAY_SERVICE, "/StatusNotifierWatcher", TRAY_SERVICE,
                          "RegisteredStatusNotifierItems")
    if available is None or available.returncode != 0:
        return
    # Clients saw the bus name before its object existed, so NameOwnerChanged will
    # not make them retry. Re-register existing, same-UID standard SNI endpoints.
    listing = tray_call("list", "--no-legend", "--no-pager")
    if listing is None or listing.returncode != 0:
        return
    peers = []
    for line in listing.stdout.splitlines()[:512]:
        fields = line.split()
        try:
            if len(fields) < 2 or (Path("/proc") / str(int(fields[1]))).stat().st_uid != os.getuid():
                continue
        except (OSError, ValueError):
            continue
        name = fields[0]
        if name.startswith("org.kde.StatusNotifierHost-"):
            tray_call("call", TRAY_SERVICE, "/StatusNotifierWatcher", TRAY_SERVICE,
                      "RegisterStatusNotifierHost", "s", name)
        elif name.startswith(":"):
            peers.append(name)
    def item(name):
        result = tray_call("get-property", name, "/StatusNotifierItem", "org.kde.StatusNotifierItem", "Id")
        return name if result is not None and result.returncode == 0 else None
    with ThreadPoolExecutor(max_workers=8) as pool:
        for name in pool.map(item, peers[:64]):
            if name:
                tray_call("call", TRAY_SERVICE, "/StatusNotifierWatcher", TRAY_SERVICE,
                          "RegisterStatusNotifierItem", "s", name)


def current_skin() -> str:
    cfg = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "illogical-impulse" / "config.json"
    try:
        return json.loads(cfg.read_text()).get("appearance", {}).get("bwmTheme", "default")
    except (OSError, ValueError):
        return "default"


def native_host_enabled() -> bool:
    """Use the same default/setting as Quickshell's nativePlasmaHost binding."""
    override = os.environ.get("BWM_PLASMA_NATIVE_HOST")
    if override is not None:
        return override == "1"
    cfg = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "illogical-impulse" / "config.json"
    try:
        value = json.loads(cfg.read_text()).get("bar", {}).get("plasma", {}).get("nativeHost", True)
        return True if value is None else bool(value)
    except (OSError, ValueError):
        return True


def is_host_pid(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        if Path(f"/proc/{pid}").stat().st_uid != os.getuid():
            return False
        cmd = Path(f"/proc/{pid}/cmdline").read_bytes().decode("utf-8", "ignore").rstrip("\0").split("\0")
    except OSError:
        return False
    return bool(cmd) and Path(cmd[0]).name == "bwm-plasma-host" and cmd[1:] == ["--session"]


def find_running_pids() -> list[int]:
    pids: list[int] = []
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            if is_host_pid(pid):
                pids.append(pid)
        except (OSError, ValueError):
            pass
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid not in pids and is_host_pid(pid):
            pids.append(pid)
    return pids


def ready_pid() -> int | None:
    """A crash leaves the marker behind: its existence alone is not readiness."""
    try:
        pid = int(READY_FILE.read_text().strip())
    except (OSError, ValueError):
        return None
    return pid if is_host_pid(pid) else None


def install_binary() -> int:
    built = BUILD_DIR / "bwm-plasma-host"
    if not built.is_file():
        print(f"No existe el binario compilado: {built}", file=sys.stderr)
        return 1
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".bwm-plasma-host-", dir=BIN_DIR)
    os.close(fd)
    try:
        shutil.copy2(built, tmp_name)
        os.chmod(tmp_name, 0o755)
        os.replace(tmp_name, BINARY)
    finally:
        Path(tmp_name).unlink(missing_ok=True)
    return 0


def build_and_install() -> int:
    r = subprocess.run(
        ["cmake", "-S", str(SOURCE_DIR), "-B", str(BUILD_DIR), "-DBUILD_TESTING=OFF"],
        check=False,
    )
    if r.returncode != 0:
        return r.returncode
    r = subprocess.run(
        ["cmake", "--build", str(BUILD_DIR), f"-j{os.cpu_count() or 4}"],
        check=False,
    )
    if r.returncode != 0:
        return r.returncode
    return install_binary()


def start_host(force: bool = False) -> int:
    if not force and not native_host_enabled():
        return 0
    if current_skin() != "plasma":
        return 0
    if not BINARY.is_file() or not os.access(BINARY, os.X_OK):
        return 0
    ensure_tray_watcher()
    if find_running_pids():
        return 0

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    READY_FILE.unlink(missing_ok=True)

    env = dict(os.environ)
    env.pop("BWM_SKIN_SWITCH", None)
    xdg_config = str(Path(env.get("XDG_CONFIG_HOME", Path.home() / ".config")).resolve())
    kdedefaults = str(Path.home() / ".config" / "kdedefaults")
    env["QT_QPA_PLATFORM"] = "wayland"
    env["QT_QPA_PLATFORMTHEME"] = "kde"
    env["XDG_CONFIG_DIRS"] = f"{kdedefaults}:/etc/xdg"
    env["BWM_R4_TASK_ACTIONS"] = "1"
    env["BWM_R4_TASK_RUNTIME"] = str(RUNTIME_DIR)
    env["BWM_R4_TASK_CONFIG"] = xdg_config
    env["BWM_R4_TASK_THUMBNAILS"] = "1"
    env["BWM_R4_DESKTOP_ACTIONS"] = "1"
    env["BWM_R4_DESKTOP_RUNTIME"] = str(RUNTIME_DIR)
    env["BWM_R4_DESKTOP_CONFIG"] = xdg_config
    env["BWM_R5_HYPR_RUNTIME"] = str(RUNTIME_DIR)

    sys.path.insert(0, str(SCRIPT_DIR))
    sys.path.insert(0, str(SCRIPT_DIR.parents[2] / "scripts"))
    import native_launch
    import bwm_session
    env[native_launch.VARIABLE] = native_launch.capture(os.environ)
    # A durable session process must belong to Hyprland's scope, not the terminal
    # or assistant that activated it. Pass only launcher/host variables explicitly.
    command = ["env", "-u", "BWM_SKIN_SWITCH", "-u", "WAYLAND_SOCKET"]
    keys = set(native_launch.KEYS) | {key for key in env if key.startswith(("BWM_R4_", "BWM_R5_"))}
    assignments = []
    for key in sorted(keys):
        if key in env:
            assignments.append(f"{key}={env[key]}")
        else:
            command.extend(["-u", key])
    command += assignments + [str(BINARY), "--session"]
    if not bwm_session.spawn(command, str(LOG_FILE), allow_fallback=False):
        print("No se pudo iniciar el anfitrión de Plasma desde Hyprland.", file=sys.stderr)
        return 1

    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        pids = find_running_pids()
        ready = ready_pid()
        if ready is not None and ready in pids:
            PID_FILE.write_text(f"{ready}\n")
            ensure_tray_watcher()
            return 0
        time.sleep(0.05)
    stop_host()
    print(f"El anfitrión de Plasma no confirmó el arranque; consulta {LOG_FILE}.", file=sys.stderr)
    return 1


def stop_host() -> int:
    pids = find_running_pids()
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline and any(is_host_pid(p) for p in pids):
        time.sleep(0.05)
    for pid in pids:
        if is_host_pid(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    PID_FILE.unlink(missing_ok=True)
    READY_FILE.unlink(missing_ok=True)
    return 0


def status_host() -> int:
    pids = find_running_pids()
    info = {
        "binary": str(BINARY),
        "installed": BINARY.is_file() and os.access(BINARY, os.X_OK),
        "enabled": native_host_enabled(),
        "running": bool(pids),
        "pid": pids[0] if pids else None,
        "ready": ready_pid() in pids,
    }
    print(json.dumps(info, indent=2))
    return 0


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "status"
    if cmd == "build":
        return build_and_install()
    if cmd == "install":
        return install_binary()
    if cmd == "start":
        return start_host(force="--force" in argv[1:])
    if cmd == "stop":
        return stop_host()
    if cmd == "status":
        return status_host()
    if cmd == "ready":
        return 0 if ready_pid() is not None else 1
    print("Uso: plasma-host.py build|install|start|stop|status|ready", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
