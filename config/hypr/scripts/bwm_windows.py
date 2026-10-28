#!/usr/bin/env python3
"""Colocación de ventanas al cambiar de skin (común a todas; lo usan bwm-theme-manager.py,
bwm_omarchy.restart_app y reload-spotify.py).

En KDE Plasma todas las ventanas flotan. Una ventana que venía en mosaico (Default/Retro) se
queda en el mismo sitio: el mismo rectángulo en pantalla, contando la barra de título Breeze que
hyprbars le pone encima si la lleva, metido en el área útil de Plasma (encima del panel) con un
margen sutil respecto a los bordes del monitor para que se note que ya no está en mosaico.
"""
import json
import subprocess
from pathlib import Path

PLASMA_PANEL = 44     # panel inferior de Plasma (THEMES["plasma"]["bar_height"])
PLASMA_TITLEBAR = 30  # barra de hyprbars, por encima de la ventana (plugin:hyprbars:bar_height)
EDGE_MARGIN = 10      # separación de los bordes del monitor y del panel
MIN_W, MIN_H = 320, 200
THEME_MANAGER = Path(__file__).resolve().parent / "bwm-theme-manager.py"


def hypr_json(what: str):
    try:
        return json.loads(subprocess.run(["hyprctl", what, "-j"], capture_output=True, text=True,
                                         timeout=3).stdout)
    except (OSError, ValueError, subprocess.SubprocessError):
        return []


def current_skin() -> str:
    out = subprocess.run(["python3", str(THEME_MANAGER), "get"], capture_output=True, text=True)
    return out.stdout.strip().splitlines()[-1] if out.stdout.strip() else ""


def monitor_box(mon: dict) -> tuple:
    """(x, y, ancho, alto) lógicos del monitor (escala y rotación)."""
    scale = mon.get("scale") or 1
    w, h = mon["width"] / scale, mon["height"] / scale
    if mon.get("transform", 0) % 2:
        w, h = h, w
    return mon["x"], mon["y"], int(w), int(h)


def monitor_for(at, size, monitors: list):
    """El monitor que contiene el centro de la ventana (o el primero)."""
    cx, cy = at[0] + size[0] / 2, at[1] + size[1] / 2
    for mon in monitors:
        x, y, w, h = monitor_box(mon)
        if x <= cx < x + w and y <= cy < y + h:
            return mon
    return monitors[0] if monitors else None


def titlebars() -> set:
    """(clase, título[:40]) de las ventanas a las que hyprbars pone barra (`hyprctl hyprbars-csd`)."""
    out = subprocess.run(["hyprctl", "hyprbars-csd"], capture_output=True, text=True).stdout
    bars = set()
    for line in out.splitlines():
        parts = [p.strip() for p in line.split(" | ")]
        if len(parts) >= 3 and parts[2] == "barra=si":
            bars.add((parts[0], parts[1]))
    return bars


def has_titlebar(client: dict, bars: set) -> bool:
    return (client.get("class", ""), client.get("title", "")[:40].strip()) in bars


def plasma_box(at, size, mon: dict, titlebar: bool) -> tuple:
    """Posición y tamaño (del contenido) de una ventana flotante de Plasma que ocupe el rectángulo
    `at`/`size` que tenía (en mosaico), dentro del área útil con EDGE_MARGIN."""
    mx, my, mw, mh = monitor_box(mon)
    left, top = mx + EDGE_MARGIN, my + EDGE_MARGIN
    right, bottom = mx + mw - EDGE_MARGIN, my + mh - PLASMA_PANEL - EDGE_MARGIN
    x0, y0 = max(at[0], left), max(at[1], top)
    x1, y1 = min(at[0] + size[0], right), min(at[1] + size[1], bottom)
    bar = PLASMA_TITLEBAR if titlebar else 0
    w, h = max(MIN_W, x1 - x0), max(MIN_H, y1 - y0 - bar)
    x = min(x0, right - w)
    y = min(y0 + bar, bottom - h)
    return int(x), int(y), int(w), int(h)


def place_lua(addr: str, workspace=None, box=None, make_floating=False) -> str:
    """Lua de Hyprland 0.55+ que mueve una ventana a su workspace y, con `box`, la deja flotante
    en esa posición/tamaño."""
    lua = f"local w = hl.get_window('address:{addr}'); if w then "
    if workspace is not None:
        target = workspace if str(workspace).lstrip("-").isdigit() else json.dumps(str(workspace))
        lua += f"hl.dispatch(hl.dsp.window.move({{ workspace = {target}, follow = false, window = w }})) "
    if make_floating:
        lua += "hl.dispatch(hl.dsp.window.float({ window = w })) "
    if box:
        x, y, bw, bh = box
        lua += (f"hl.dispatch(hl.dsp.window.resize({{ x = {bw}, y = {bh}, relative = false, window = w }})) "
                f"hl.dispatch(hl.dsp.window.move({{ x = {x}, y = {y}, relative = false, window = w }})) ")
    return lua + "end "


def dispatch(lua_blocks: list):
    if not lua_blocks:
        return
    code = "(function() " + " ".join(f"do {b} end" for b in lua_blocks) + " return hl.dsp.no_op() end)()"
    subprocess.run(["hyprctl", "dispatch", code], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def float_for_plasma(clients: list = None):
    """Todas las ventanas en mosaico pasan a flotar en su mismo sitio (con su barra y margen)."""
    clients = clients if clients is not None else hypr_json("clients")
    monitors = hypr_json("monitors")
    bars = titlebars()
    blocks = []
    for c in clients:
        if c.get("floating") or c.get("fullscreen", 0) or not c.get("address") or not c.get("mapped", True):
            continue
        mon = next((m for m in monitors if m.get("id") == c.get("monitor")), None) \
            or monitor_for(c["at"], c["size"], monitors)
        if not mon:
            continue
        box = plasma_box(c["at"], c["size"], mon, has_titlebar(c, bars))
        blocks.append(place_lua(c["address"], box=box, make_floating=True))
    dispatch(blocks)
    return len(blocks)


def restored_box(record: dict, client: dict):
    """Geometría para una ventana que vuelve tras reiniciar su app: la que tenía si flotaba; si
    estaba en mosaico y ahora flota (en Plasma), la de float_for_plasma; si no, ninguna."""
    if not client.get("floating"):
        return None
    if record.get("floating"):
        return (*record["at"], *record["size"])
    if current_skin() != "plasma":
        return None
    monitors = hypr_json("monitors")
    mon = monitor_for(record["at"], record["size"], monitors)
    return plasma_box(record["at"], record["size"], mon, has_titlebar(client, titlebars())) if mon else None


def _active_workspace_id(mon: dict):
    ws = mon.get("activeWorkspace") or {}
    return ws.get("id") if ws.get("id", 0) > 0 else None


def mpris_playing() -> list:
    """Reproductores MPRIS (Stremio, Spotify, navegadores…) que están sonando."""
    try:
        names = subprocess.run(["busctl", "--user", "--no-legend", "list"], capture_output=True, text=True,
                               timeout=3).stdout.split("\n")
    except (OSError, subprocess.SubprocessError):
        return []
    playing = []
    for line in names:
        name = line.split(" ")[0]
        if not name.startswith("org.mpris.MediaPlayer2.") or name.endswith("playerctld"):
            continue
        out = subprocess.run(["busctl", "--user", "get-property", name, "/org/mpris/MediaPlayer2",
                              "org.mpris.MediaPlayer2.Player", "PlaybackStatus"],
                             capture_output=True, text=True).stdout
        if "Playing" in out:
            playing.append(name)
    return playing


def snapshot_focus() -> dict:
    """Workspace visible de cada monitor, monitor y ventana con el foco, y qué estaba sonando.
    Una app que se reabre toma el foco (focus_on_activate) y te cambia de workspace, y lo que
    queda oculto puede pausarse: restore_focus lo deja como estaba."""
    monitors = hypr_json("monitors")
    active = subprocess.run(["hyprctl", "activewindow", "-j"], capture_output=True, text=True).stdout
    try:
        win = json.loads(active) if active.strip() not in ("", "{}") else {}
    except ValueError:
        win = {}
    return {"workspaces": {m["name"]: _active_workspace_id(m) for m in monitors},
            "focused_monitor": next((m["name"] for m in monitors if m.get("focused")), None),
            "window": win.get("address"), "playing": mpris_playing()}


def restore_focus(snap: dict):
    """Vuelve a los workspaces, al monitor y a la ventana de snapshot_focus y reanuda lo que
    sonaba y se pausó."""
    monitors = {m["name"]: m for m in hypr_json("monitors")}
    blocks = []
    for name, ws in snap["workspaces"].items():
        mon = monitors.get(name)
        if ws and mon and _active_workspace_id(mon) != ws:
            blocks.append(f"hl.dispatch(hl.dsp.focus({{ monitor = '{name}' }})) "
                          f"hl.dispatch(hl.dsp.focus({{ workspace = {ws} }}))")
    if snap.get("focused_monitor") in monitors:
        blocks.append(f"hl.dispatch(hl.dsp.focus({{ monitor = '{snap['focused_monitor']}' }}))")
    if snap.get("window") and any(c["address"] == snap["window"] for c in hypr_json("clients")):
        blocks.append(f"hl.dispatch(hl.dsp.focus({{ window = 'address:{snap['window']}' }}))")
    dispatch(blocks)
    now = set(mpris_playing())
    for name in snap.get("playing", []):
        if name not in now:
            subprocess.run(["busctl", "--user", "call", name, "/org/mpris/MediaPlayer2",
                            "org.mpris.MediaPlayer2.Player", "Play"], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=5)


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["float-for-plasma"]:
        print(float_for_plasma())
    else:
        print("Uso: bwm_windows.py float-for-plasma", file=sys.stderr)
        sys.exit(2)
