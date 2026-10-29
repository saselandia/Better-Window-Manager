#!/usr/bin/env python3
"""Colocación de ventanas al cambiar de skin (común a todas; lo usan bwm-theme-manager.py,
bwm_omarchy.restart_app y reload-spotify.py).

Cada skin dice en su skin.json (config/hypr/skins/<id>/skin.json) cómo gestiona las ventanas con la
variable "windows": "tiling" (mosaico: Default, Retro) o "traditional" (WM tradicional, ventanas
flotantes con barra de título: KDE Plasma). Al pasar de una de mosaico a una tradicional, cada ventana
se queda en el mismo sitio: el mismo rectángulo, contando la barra de título que la skin le pone encima
("traditional.titlebar") si la lleva, dentro del área útil (sin el panel, "panel") con un margen sutil
con los bordes ("edgeMargin") y un hueco entre ventanas ("gap"), para que se note que ya no están en
mosaico. Los datos los da bwm_skins.py.
"""
import json
import re
import subprocess
from pathlib import Path

MIN_W, MIN_H = 320, 200
THEME_MANAGER = Path(__file__).resolve().parent / "bwm-theme-manager.py"
import bwm_skins  # noqa: E402  (mismo directorio)


def windowing(skin: str) -> dict:
    """Geometría de ventanas de una skin tradicional ({} en las de mosaico)."""
    return bwm_skins.traditional(skin)


def is_traditional(skin: str) -> bool:
    """¿La skin es de WM tradicional (ventanas flotantes) en vez de mosaico?"""
    return bwm_skins.is_traditional(skin)


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


def traditional_box(at, size, mon: dict, titlebar: bool, win: dict) -> tuple:
    """Posición y tamaño (del contenido) de una ventana flotante que ocupe el rectángulo `at`/`size`
    que tenía en mosaico, separada de las vecinas (`gap`) y dentro del área útil de la skin
    tradicional `win` (su bloque "traditional")."""
    mx, my, mw, mh = monitor_box(mon)
    margin, half_gap = win.get("edgeMargin", 10), win.get("gap", 0) / 2
    panel = win.get("panel", {})
    reserve = {e: (panel.get("size", 0) if panel.get("edge") == e else 0) for e in ("top", "bottom", "left", "right")}
    left, top = mx + reserve["left"] + margin, my + reserve["top"] + margin
    right, bottom = mx + mw - reserve["right"] - margin, my + mh - reserve["bottom"] - margin
    x0, y0 = max(at[0] + half_gap, left), max(at[1] + half_gap, top)
    x1, y1 = min(at[0] + size[0] - half_gap, right), min(at[1] + size[1] - half_gap, bottom)
    bar = win.get("titlebar", 0) if titlebar else 0
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
        lua += "hl.dispatch(hl.dsp.window.float({ action = 'enable', window = w })) "
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


def float_in_place(skin: str, clients: list = None):
    """Al entrar en una skin tradicional, las ventanas en mosaico pasan a flotar en su mismo sitio
    (con su barra de título, el margen y el hueco de la skin)."""
    win = windowing(skin)
    clients = clients if clients is not None else hypr_json("clients")
    monitors = hypr_json("monitors")
    bars = titlebars()
    blocks = []
    for c in clients:
        if (c.get("floating") or c.get("fullscreen", 0) or c.get("pinned") or not c.get("address")
                or not c.get("mapped", True) or c.get("workspace", {}).get("id", 0) <= 0
                or c.get("workspace", {}).get("id") == 99):
            continue
        mon = next((m for m in monitors if m.get("id") == c.get("monitor")), None) \
            or monitor_for(c["at"], c["size"], monitors)
        if not mon:
            continue
        box = traditional_box(c["at"], c["size"], mon, has_titlebar(c, bars), win)
        blocks.append(place_lua(c["address"], box=box, make_floating=True))
    dispatch(blocks)
    return len(blocks)


def restored_box(record: dict, client: dict):
    """Geometría para una ventana que vuelve tras reiniciar su app: la que tenía si flotaba; si
    estaba en mosaico y ahora flota (skin tradicional), la de float_in_place; si no, ninguna."""
    if not client.get("floating"):
        return None
    if record.get("floating"):
        return (*record["at"], *record["size"])
    skin = current_skin()
    if not is_traditional(skin):
        return None
    monitors = hypr_json("monitors")
    mon = monitor_for(record["at"], record["size"], monitors)
    return traditional_box(record["at"], record["size"], mon, has_titlebar(client, titlebars()),
                        windowing(skin)) if mon else None


def hold_new_windows(name: str, classes: list, workspace):
    """Regla temporal: las ventanas nuevas de esas clases (la de carga de Steam, diálogos de una
    app que se reinicia) se abren directamente en `workspace`, sin robar el foco ni aparecer en el
    workspace que estás mirando. release_new_windows la retira."""
    pattern = "^(" + "|".join(re.escape(c) for c in classes if c) + ")$"
    ws = str(workspace)
    subprocess.run(["hyprctl", "eval", f"hl.window_rule({{ name = {json.dumps(name)}, match = {{ class = {json.dumps(pattern)} }}, "
                    f"workspace = {json.dumps(ws + ' silent')}, no_initial_focus = true, focus_on_activate = false }})"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def release_new_windows(name: str):
    """Quita la regla de hold_new_windows: redefinida con el mismo nombre no casa con nada."""
    subprocess.run(["hyprctl", "eval", f"hl.window_rule({{ name = {json.dumps(name)}, match = {{ class = \"^$BWM-none^\" }}, "
                    "workspace = \"1 silent\" })"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


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
            "window": win.get("address"), "window_pid": win.get("pid"), "playing": mpris_playing()}


def restore_focus(snap: dict):
    """Vuelve a los workspaces, al monitor y a la ventana de snapshot_focus y reanuda lo que
    sonaba y se pausó."""
    monitors = {m["name"]: m for m in hypr_json("monitors")}
    blocks = []
    for name, ws in snap["workspaces"].items():
        mon = monitors.get(name)
        if ws and mon and _active_workspace_id(mon) != ws:
            selector = "desc:" + mon["description"] if mon.get("description") else name
            blocks.append(f"hl.dispatch(hl.dsp.focus({{ monitor = {json.dumps(selector)} }})) "
                          f"hl.dispatch(hl.dsp.focus({{ workspace = {ws} }}))")
    focused = next((m["name"] for m in monitors.values() if m.get("focused")), None)
    wanted = monitors.get(snap.get("focused_monitor"))
    if wanted and (blocks or focused != snap["focused_monitor"]):
        selector = "desc:" + wanted["description"] if wanted.get("description") else wanted["name"]
        blocks.append(f"hl.dispatch(hl.dsp.focus({{ monitor = {json.dumps(selector)} }}))")
    # Hyprland reutiliza direcciones; una ventana distinta no debe llevarnos a otro workspace.
    win = next((c for c in hypr_json("clients") if c["address"] == snap.get("window")
                and c.get("pid") == snap.get("window_pid")), None)
    active = hypr_json("activewindow")
    if (win and isinstance(active, dict) and active.get("address") != win["address"]
            and win.get("workspace", {}).get("id") in snap["workspaces"].values()):
        blocks.append(f"hl.dispatch(hl.dsp.focus({{ window = 'address:{win['address']}' }}))")
    dispatch(blocks)
    now = set(mpris_playing())
    for name in snap.get("playing", []):
        if name not in now:
            subprocess.run(["busctl", "--user", "call", name, "/org/mpris/MediaPlayer2",
                            "org.mpris.MediaPlayer2.Player", "Play"], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=5)


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == "float-in-place":
        print(float_in_place(sys.argv[2]))
    else:
        print("Uso: bwm_windows.py float-in-place <skin>", file=sys.stderr)
        sys.exit(2)
