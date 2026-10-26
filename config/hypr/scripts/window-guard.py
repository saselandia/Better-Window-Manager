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

Los juegos colocan y redimensionan la ventana después de mapearla y Hyprland no emite
eventos por eso, así que cada ventana nueva se revisa varias veces durante ~20 s.

Uso: window-guard.py watch | check
"""
import importlib.util
import json
import os
import socket
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("xwayland_primary", os.path.join(HERE, "xwayland-primary.py"))
xwayland_primary = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(xwayland_primary)

CHECK_DELAYS = (0.3, 1, 2, 4, 7, 12, 20)
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
        if win["workspace"]["name"].startswith("special:") or win["workspace"]["id"] == 99:
            return  # minimizadas (toggle-minimize.py) y scratchpads: no tocar
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


def on_monitors_changed():
    # Los outputs de XWayland aparecen un poco después que el monitor
    time.sleep(1.5)
    xwayland_primary.apply_retrying(tries=5)
    check_all()


def watch():
    xwayland_primary.apply_retrying()
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
    sys.exit(watch())
