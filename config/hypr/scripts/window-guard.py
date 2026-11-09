#!/usr/bin/env python3
"""
Vigilante de ventanas para juegos y apps a pantalla completa (todos los temas).

- Mantiene el monitor principal de XWayland (xwayland-primary.py) al conectar/quitar
  monitores, recargar o mover workspaces.
- Ventanas flotantes que quedan fuera de todas las pantallas (Wine colocó Fallout 3 justo
  debajo del HP, en 0,2160): las devuelve al monitor de su workspace.
- Ventanas XWayland sin bordes del tamaño exacto de un monitor ("pantalla completa en
  ventana" de Wine/Proton, que no pide _NET_WM_STATE_FULLSCREEN): las pone en pantalla
  completa en ese monitor, así no quedan tapadas por otras ventanas ni por la barra.
  Sólo una vez por ventana (por PID, Hyprland reutiliza direcciones): si el usuario la saca
  de pantalla completa no se vuelve a forzar.
- Fondo de pantalla: un monitor que se desconecta y vuelve (reposo, cambio de entrada) queda en
  negro en swww/awww; al volver se le pone otra vez el fondo actual.
- Barra: si no queda ninguna instancia de Quickshell `ii` durante dos comprobaciones seguidas
  (~20 s, sin un cambio de skin en curso), la vuelve a lanzar como hijo de Hyprland (bwm_session.py).

Los juegos colocan y redimensionan la ventana después de mapearla y Hyprland no emite
eventos por eso, así que cada ventana nueva se revisa varias veces durante ~20 s.

Uso: window-guard.py watch | check | wallpaper
"""
import importlib.util
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("xwayland_primary", os.path.join(HERE, "xwayland-primary.py"))
xwayland_primary = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(xwayland_primary)

sys.path.insert(0, HERE)
import bwm_session  # noqa: E402

CHECK_DELAYS = (0.3, 1, 2, 4, 7, 12, 20)
SHELL_CHECK_SECS = 10
MONITOR_EVENTS = (b"monitoradded", b"monitorremoved", b"configreloaded", b"moveworkspace")
SIZE_TOLERANCE = 2

_lock = threading.Lock()
_fullscreened = set()  # (address, pid) ya puestas en pantalla completa por el vigilante
_title_checked = {}    # dirección -> última revisión por cambio de título (los navegadores cambian mucho)


def hyprctl_json(what):
    try:
        out = subprocess.run(["hyprctl", what, "-j"], capture_output=True, text=True, timeout=5)
        return json.loads(out.stdout or "null") or []
    except (OSError, ValueError, subprocess.SubprocessError):
        return []


def dispatch(code):
    subprocess.run(["hyprctl", "dispatch", code], capture_output=True, timeout=5)


def logical(mon):
    scale = mon.get("scale") or 1
    w, h = mon["width"] / scale, mon["height"] / scale
    if mon.get("transform", 0) % 2:
        w, h = h, w
    return mon["x"], mon["y"], w, h


def overlaps(win, mon):
    (x, y), (w, h) = win["at"], win["size"]
    mx, my, mw, mh = logical(mon)
    # Al menos 64 px visibles en cada eje
    return min(x + w, mx + mw) - max(x, mx) >= 64 and min(y + h, my + mh) - max(y, my) >= 64


def check_window(addr):
    with _lock:
        clients = hyprctl_json("clients")
        win = next((c for c in clients if c["address"] == addr), None)
        if not win or not win.get("mapped") or win.get("hidden") or win.get("fullscreen"):
            return
        if win["workspace"]["name"].startswith("special:"):
            return  # minimizadas (special:minimized) y scratchpads: no tocar
        if not win.get("floating"):
            return
        mons = [m for m in hyprctl_json("monitors") if not m.get("disabled")]
        if not mons:
            return
        home = next((m for m in mons if m["id"] == win["monitor"]), mons[0])
        w, h = win["size"]
        target = f'"address:{addr}"'

        # Ventana sin bordes del tamaño de un monitor -> pantalla completa en ese monitor
        same = [m for m in mons
                if abs(w - logical(m)[2]) <= SIZE_TOLERANCE and abs(h - logical(m)[3]) <= SIZE_TOLERANCE]
        key = (addr, win.get("pid"))
        if win.get("xwayland") and same and key not in _fullscreened:
            mon = home if home in same else same[0]
            mx, my, _, _ = logical(mon)
            _fullscreened.add(key)
            dispatch(f"hl.dsp.window.move({{ x = {int(mx)}, y = {int(my)}, relative = false, window = {target} }})")
            if any(m["activeWorkspace"]["id"] == win["workspace"]["id"] for m in mons):
                dispatch(f"hl.dsp.focus({{ window = {target} }})")  # no saltar a un workspace oculto
            dispatch(f"hl.dsp.window.fullscreen({{ mode = 0, action = 'set', window = {target} }})")
            return

        # Fuera de todas las pantallas -> al monitor de su workspace
        if not any(overlaps(win, m) for m in mons):
            mx, my, mw, mh = logical(home)
            nx = mx + max(0, (mw - w) / 2)
            ny = my + max(0, (mh - h) / 2)
            dispatch(f"hl.dsp.window.move({{ x = {int(nx)}, y = {int(ny)}, relative = false, window = {target} }})")


def schedule(addr):
    for delay in CHECK_DELAYS:
        threading.Timer(delay, check_window, (addr,)).start()


def check_all():
    for c in hyprctl_json("clients"):
        check_window(c["address"])


WALL_BIN = shutil.which("swww") or shutil.which("awww")
BLACK_OUTPUT = re.compile(r"(\S+): \d+x\d+.*currently displaying: color")


def current_wallpaper():
    try:
        path = open(os.path.expanduser("~/.cache/current_wallpaper"), encoding="utf-8").read().strip()
        if os.path.isfile(path):
            return path
    except OSError:
        pass
    try:
        with open(os.path.expanduser("~/.config/illogical-impulse/config.json"), encoding="utf-8") as f:
            path = json.load(f).get("background", {}).get("wallpaperPath", "")
        return path if os.path.isfile(path) else ""
    except (OSError, ValueError):
        return ""


def black_outputs():
    try:
        out = subprocess.run([WALL_BIN, "query"], capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [m.group(1) for line in out.splitlines() if (m := BLACK_OUTPUT.search(line))]


def restore_wallpapers(tries=10):
    """Pone el fondo actual en los monitores que swww/awww muestra en negro (un color)."""
    if not WALL_BIN or subprocess.run(["pgrep", "-x", "mpvpaper"], stdout=subprocess.DEVNULL).returncode == 0:
        return  # sin swww, o con un fondo de vídeo (mpvpaper) no hay nada que reponer
    for _ in range(tries):
        outputs = black_outputs()
        wallpaper = current_wallpaper()
        if not outputs or not wallpaper:
            return
        # Un fondo de vídeo: su primer fotograma (lo reproduce OWE en Retro, debajo)
        still = subprocess.run([os.path.expanduser("~/.config/hypr/scripts/bwm-video-wallpaper"), "still", wallpaper],
                               capture_output=True, text=True).stdout.strip() or wallpaper
        subprocess.run([WALL_BIN, "img", still, "--outputs", ",".join(outputs),
                        "--transition-type", "none"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.5)


def on_monitors_changed():
    # Los outputs de XWayland aparecen un poco después que el monitor
    time.sleep(1.5)
    xwayland_primary.apply_retrying(tries=5)
    restore_wallpapers()
    check_all()


def keep_shell(checks=None, sleep=time.sleep):
    """Relanza la barra si desaparece. Dos fallos seguidos: un reinicio normal tarda < 2 s."""
    missing = 0
    while checks is None or checks > 0:
        if checks is not None:
            checks -= 1
        sleep(SHELL_CHECK_SECS)
        if bwm_session.shell_instances() or bwm_session.theme_manager_busy():
            missing = 0
            continue
        missing += 1
        if missing >= 2:
            print("window-guard: no hay Quickshell ii; se vuelve a lanzar", file=sys.stderr, flush=True)
            bwm_session.start_shell()
            missing = 0


def watch():
    threading.Thread(target=keep_shell, daemon=True).start()
    xwayland_primary.apply_retrying()
    restore_wallpapers()
    check_all()
    sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
    run = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    if not sig:
        return 1
    path = f"{run}/hypr/{sig}/.socket2.sock"
    while True:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.connect(path)
                buf = b""
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    buf += chunk
                    *lines, buf = buf.split(b"\n")
                    monitors_changed = False
                    for line in lines:
                        name, _, data = line.partition(b">>")
                        if name == b"openwindow":
                            schedule("0x" + data.split(b",", 1)[0].decode())
                        elif name == b"windowtitlev2":
                            # Los juegos cambian el título al pasar del lanzador/carga al juego
                            addr = "0x" + data.split(b",", 1)[0].decode()
                            now = time.monotonic()
                            if now - _title_checked.get(addr, 0) > 3:
                                _title_checked[addr] = now
                                threading.Timer(0.5, check_window, (addr,)).start()
                        elif name == b"closewindow":
                            addr = "0x" + data.decode()
                            _title_checked.pop(addr, None)
                            with _lock:
                                _fullscreened.difference_update({k for k in _fullscreened if k[0] == addr})
                        elif name in MONITOR_EVENTS:
                            monitors_changed = True
                    if monitors_changed:
                        threading.Thread(target=on_monitors_changed, daemon=True).start()
        except OSError:
            pass
        if not os.path.exists(path):
            return 0  # Hyprland ha terminado
        time.sleep(2)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "watch"
    if cmd == "check":
        check_all()
        sys.exit(0)
    if cmd == "wallpaper":
        restore_wallpapers()
        sys.exit(0)
    sys.exit(watch())
