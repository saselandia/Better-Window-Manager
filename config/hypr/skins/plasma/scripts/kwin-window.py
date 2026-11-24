#!/usr/bin/env python3
"""Minimizar, maximizar y restaurar como KWin, en un solo sitio (F8 de docs/BREEZE_PLAN.md).

  kwin-window.py maximize [--mode toggle|full|vertical|horizontal|restore] [dirección]
  kwin-window.py alt-enter [dirección]   (Alt+Intro: maximizar; en juegos, pantalla completa real)
  kwin-window.py minimize [dirección]
  kwin-window.py unminimize <dirección>
  kwin-window.py activate <dirección>     (tarea del panel: restaura, enfoca o minimiza la activa)
  kwin-window.py toggle-minimize [dirección]
  kwin-window.py show-desktop [enter|leave]
  kwin-window.py state [dirección]          (JSON: modo, geometría de restauración, bordes)

Acciones del menú de la ventana (F9, useractions.cpp de KWin), todas con la dirección:
  kwin-window.py menu [dirección]           abre el menú de la ventana (Alt+F3) sobre su barra
  kwin-window.py interactive move|resize    mover o redimensionar con el ratón hasta el clic (breezebars)
  kwin-window.py fullscreen | no-border | no-capture | pin | close
  kwin-window.py to-desktop <n> | to-screen <desc:monitor>
  kwin-window.py rules window|application   ajustes especiales (editor de reglas de F10)

Maximizar sigue a XdgToplevelWindow::maximize de kwin v6.7.5 (src/xdgshellwindow.cpp): el modo
tiene dos ejes (vertical, horizontal; los dos = completo), el marco ocupa el área útil en los ejes
maximizados, y al dejar de maximizar un eje se vuelve a su tamaño y centro de antes
(geometryRestore). Desde un mosaico rápido (quick tile) la geometría de restauración es la de antes
del mosaico y maximizar sale del mosaico. Las cuentas se hacen con el marco completo (barra de la
decoración incluida), así la barra queda dentro del área útil y el panel a la vista.

El modo vive en etiquetas de la ventana, que lee también el plugin breezebars: bwm-max-v,
bwm-max-h y bwm-maximized (los dos ejes; regla de redondeo cero en rules.lua). La geometría de
restauración, en $XDG_RUNTIME_DIR/bwm-kwin-windows.json por dirección y PID (Hyprland reutiliza
direcciones). Minimizar usa el formato común de toggle-minimize.py (special:minimized y
omarchy-minimized-from-<n>, §3.114) sin cambiarlo.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bwm_windows

RESTORE = 0
VERTICAL = 1
HORIZONTAL = 2
FULL = VERTICAL | HORIZONTAL

TAG_V, TAG_H, TAG_FULL = "bwm-max-v", "bwm-max-h", "bwm-maximized"
# «Sin barra de título ni marco» y «Ocultar de capturas»: etiquetas que leen breezebars y rules.lua
TAG_NO_BORDER, TAG_NO_CAPTURE = "bwm-no-border", "bwm-no-capture"
SNAP_TAGS = ("snapped",)
STATE = Path(os.environ.get("XDG_RUNTIME_DIR") or "/tmp") / "bwm-kwin-windows.json"


# ───────────────────────────────────────────── cálculo (sin Hyprland)

def mode_from_tags(tags) -> int:
    clean = {str(t).rstrip("*") for t in tags or []}
    return (VERTICAL if TAG_V in clean else 0) | (HORIZONTAL if TAG_H in clean else 0)


def next_mode(current: int, request: str) -> int:
    """Como DecoratedWindowImpl/useractions de KWin: izquierdo alterna completo; central y derecho
    alternan un eje (maximizeMode() ^ Vertical/Horizontal)."""
    if request == "toggle":
        return RESTORE if current == FULL else FULL
    if request == "vertical":
        return current ^ VERTICAL
    if request == "horizontal":
        return current ^ HORIZONTAL
    if request == "full":
        return FULL
    return RESTORE


def maximize_geometry(frame, area, old_mode: int, new_mode: int, restore, tiled: bool = False):
    """Marco nuevo y geometría de restauración nueva (x, y, w, h), como XdgToplevelWindow::maximize.

    frame: marco actual; area: área útil (MaximizeArea); restore: geometryRestore guardada o None.
    Devuelve (marco, restauración)."""
    fx, fy, fw, fh = frame
    if new_mode == old_mode:
        return tuple(frame), restore
    saved = list(restore) if restore else [fx, fy, fw, fh]
    if not tiled:
        # Sólo se actualizan los ejes que no estaban ya maximizados
        if not old_mode & VERTICAL:
            saved[1], saved[3] = fy, fh
        if not old_mode & HORIZONTAL:
            saved[0], saved[2] = fx, fw
    valid = restore is not None or not tiled
    x, y, w, h = fx, fy, fw, fh
    ax, ay, aw, ah = area
    if new_mode & HORIZONTAL:
        x, w = ax, aw
    elif old_mode & HORIZONTAL:
        if valid:
            w = saved[2]
            x = saved[0] + saved[2] / 2 - w / 2  # mismo centro horizontal que la restauración
        else:
            x, w = ax, int(aw * 0.65)
    if new_mode & VERTICAL:
        y, h = ay, ah
    elif old_mode & VERTICAL:
        if valid:
            h = saved[3]
            y = saved[1] + saved[3] / 2 - h / 2
        else:
            y, h = ay, int(ah * 0.70)
    return (int(round(x)), int(round(y)), int(round(w)), int(round(h))), tuple(int(round(v)) for v in saved)


def content_from_frame(frame, borders):
    x, y, w, h = frame
    return (x + borders["left"], y + borders["top"], max(1, w - borders["left"] - borders["right"]),
            max(1, h - borders["top"] - borders["bottom"]))


def frame_from_client(client, borders):
    (x, y), (w, h) = client.get("at", [0, 0]), client.get("size", [1, 1])
    return (x - borders["left"], y - borders["top"], w + borders["left"] + borders["right"],
            h + borders["top"] + borders["bottom"])


def tag_changes(old_mode: int, new_mode: int) -> list:
    """Etiquetas a poner (+) o quitar (-) para pasar de un modo a otro."""
    out = []
    for bit, tag in ((VERTICAL, TAG_V), (HORIZONTAL, TAG_H)):
        if (new_mode & bit) and not (old_mode & bit):
            out.append("+" + tag)
        elif (old_mode & bit) and not (new_mode & bit):
            out.append("-" + tag)
    if new_mode == FULL and old_mode != FULL:
        out.append("+" + TAG_FULL)
    elif old_mode == FULL and new_mode != FULL:
        out.append("-" + TAG_FULL)
    return out


# ───────────────────────────────────────────── estado

def load_state() -> dict:
    try:
        data = json.loads(STATE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_state(data: dict):
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    os.replace(tmp, STATE)


def stored_restore(client: dict):
    entry = load_state().get(client.get("address", ""))
    if isinstance(entry, dict) and entry.get("pid") == client.get("pid") and isinstance(entry.get("restore"), list) \
            and len(entry["restore"]) == 4:
        return tuple(entry["restore"])
    return None


def store_restore(client: dict, restore):
    data = load_state()
    addresses = {c.get("address") for c in hypr_json("clients") or []}
    data = {a: e for a, e in data.items() if a in addresses}  # sin entradas de ventanas cerradas
    if restore is None:
        data.pop(client["address"], None)
    else:
        data[client["address"]] = {"pid": client.get("pid"), "restore": list(restore)}
    save_state(data)


# ───────────────────────────────────────────── Hyprland

def hypr_json(*args):
    try:
        return json.loads(subprocess.check_output(["hyprctl", "-j", *args], stderr=subprocess.DEVNULL))
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def run_lua(code: str):
    subprocess.run(["hyprctl", "dispatch", code], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def find_client(address: str | None):
    if address:
        return next((c for c in hypr_json("clients") or [] if c.get("address") == address), None)
    active = hypr_json("activewindow")
    return active if isinstance(active, dict) and active.get("address") else None


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def minimizer():
    return load_script("toggle_minimize", "toggle-minimize.py")


def window_borders(client: dict) -> dict:
    from bwm_windows import decoration_extents, titlebars
    return decoration_extents(client, titlebars())


def work_area(client: dict):
    monitors = hypr_json("monitors") or []
    mon = next((m for m in monitors if m.get("id") == client.get("monitor")), monitors[0] if monitors else None)
    if not mon:
        return None
    from bwm_windows import monitor_box
    x, y, w, h = monitor_box(mon, round_to_nearest=True)
    left, top, right, bottom = (list(mon.get("reserved", [])) + [0, 0, 0, 0])[:4]
    return (int(x + left), int(y + top), max(1, int(w - left - right)), max(1, int(h - top - bottom)))


GAME_CLASS = re.compile(r"^(steam_app_[0-9]+|gamescope|.*\.exe)$", re.IGNORECASE)


def is_game_or_fullscreen(client: dict) -> bool:
    """Juegos (misma clase que la regla games-main-monitor) o ventanas ya a pantalla completa real."""
    return (client.get("fullscreen", 0) == 2 or client.get("fullscreenClient", 0) == 2
            or bool(GAME_CLASS.match(client.get("class") or "")))


def alt_enter(client: dict) -> None:
    """Alt+Intro de Breeze: maximizar como KWin, salvo en juegos/pantalla completa, donde alterna
    la pantalla completa real como en las otras skins (maximizar un juego no tiene sentido y,
    a pantalla completa, maximize() no hacía nada y la tecla no llegaba a ningún sitio)."""
    if is_game_or_fullscreen(client):
        action = "unset" if client.get("fullscreen", 0) == 2 else "set"
        run_lua(window_lua(client, f"hl.dispatch(hl.dsp.window.fullscreen({{ mode = 0, action = '{action}', window = w }}))"))
    else:
        maximize(client, "toggle")


def maximize(client: dict, request: str) -> bool:
    if client.get("fullscreen", 0) == 2 or client.get("fullscreenClient", 0) == 2:
        return False  # pantalla completa real (juegos, vídeo): no es maximizar
    area = work_area(client)
    if not area:
        return False
    addr, pid = client["address"], int(client.get("pid") or 0)
    tags = client.get("tags", []) or []
    old_mode = mode_from_tags(tags)
    hypr_maximized = client.get("fullscreen", 0) == 1  # maximizado de Hyprland (de antes de F8)
    if hypr_maximized and old_mode == RESTORE:
        old_mode = FULL
    new_mode = next_mode(old_mode, request)
    if new_mode == old_mode:
        return False
    borders = window_borders(client)
    frame = frame_from_client(client, borders)
    tiled = any(str(t).rstrip("*") in SNAP_TAGS for t in tags)
    restore = stored_restore(client) if old_mode != RESTORE else None
    if tiled and restore is None:
        # Restauración de antes del mosaico: quick-tile.py sólo guarda el tamaño; centro del mosaico
        qt = load_script("quick_tile", "quick-tile.py")
        size = qt.get_saved_presnap(addr)
        if size and len(size) == 2:
            w = size[0] + borders["left"] + borders["right"]
            h = size[1] + borders["top"] + borders["bottom"]
            restore = (int(frame[0] + frame[2] / 2 - w / 2), int(frame[1] + frame[3] / 2 - h / 2), w, h)
            qt.remove_presnap(addr)
    if hypr_maximized:
        restore = None  # Hyprland guarda la suya; al salir de su maximizado se usa la de KWin si hay
    new_frame, new_restore = maximize_geometry(frame, area, old_mode, new_mode, restore, tiled)
    if hypr_maximized and new_mode == RESTORE:
        lua_geometry = ""  # Hyprland devuelve su propia geometría al quitar su maximizado
    else:
        x, y, w, h = content_from_frame(new_frame, borders)
        lua_geometry = (f"hl.dispatch(hl.dsp.window.resize({{ x = {w}, y = {h}, relative = false, window = w }})) "
                        f"hl.dispatch(hl.dsp.window.move({{ x = {x}, y = {y}, relative = false, window = w }}))")
    changes = tag_changes(old_mode, new_mode)
    if new_mode != RESTORE:
        # Maximizar sale del mosaico rápido (exitQuickTileMode): sólo sus etiquetas
        changes += ["-" + t.rstrip("*") for t in tags if str(t).rstrip("*") == "snapped" or str(t).startswith("snapped_")]
    tag_lua = " ".join(f'pcall(function() hl.dispatch(hl.dsp.window.tag({{ tag = "{t}", window = w }})) end)' for t in changes)
    run_lua(f"""(function()
        local w = hl.get_window("address:{addr}")
        if not w or w.pid ~= {pid} then return hl.dsp.no_op() end
        hl.dispatch(hl.dsp.window.fullscreen({{ mode = 1, action = 'unset', window = w }}))
        hl.dispatch(hl.dsp.window.float({{ action = 'enable', window = w }}))
        {lua_geometry}
        {tag_lua}
        return hl.dsp.no_op()
    end)()""")
    store_restore(client, None if new_mode == RESTORE else new_restore)
    if new_mode != RESTORE:
        # Arrastrar una ventana maximizada la restaura (breezebars lee este tamaño, como en el mosaico)
        qt = load_script("quick_tile", "quick-tile.py")
        rw = new_restore[2] - borders["left"] - borders["right"]
        rh = new_restore[3] - borders["top"] - borders["bottom"]
        if rw > 100 and rh > 100:
            qt.save_presnap(addr, [rw, rh])
    return True


def focus(client: dict):
    run_lua(window_lua(client, bwm_windows.focus_body_lua()))


def has_tag(client: dict, tag: str) -> bool:
    return tag in {str(t).rstrip("*") for t in client.get("tags", []) or []}


def window_lua(client: dict, body: str) -> str:
    """Una acción sobre la ventana, comprobando el PID (Hyprland reutiliza direcciones)."""
    return f"""(function()
        local w = hl.get_window("address:{client['address']}")
        if not w or w.pid ~= {int(client.get('pid') or 0)} then return hl.dsp.no_op() end
        {body}
        return hl.dsp.no_op()
    end)()"""


def native_fullscreen_allowed(client: dict, *, minimized=None) -> bool:
    """Native task capability: ordinary mapped windows, never minimized/special storage."""
    space = client.get("workspace")
    number = space.get("id") if isinstance(space, dict) else None
    return (client.get("mapped") is True and not client.get("hidden", False) and not client.get("pinned", False)
            and type(number) is int and number > 0 and number != 99
            and not (minimizer().is_minimized(client) if minimized is None else minimized))


def native_fullscreen_lua(client: dict, state: bool) -> str:
    """Set a desired state with live guards and an explicit dispatcher receipt."""
    action = "set" if state else "unset"
    return f'''(function()
        local theme = package.loaded["modules.theme"]
        local w = hl.get_window("address:{client['address']}")
        if not theme or theme.name ~= "plasma" or not w or w.pid ~= {int(client['pid'])}
            or not w.mapped or w.hidden or w.pinned then return "bwm-r4-fullscreen-rejected" end
        local ws = w.workspace
        if not ws or ws.id < 1 or ws.id == 99 or ws.name == "special:minimized" then return "bwm-r4-fullscreen-rejected" end
        local result = hl.dispatch(hl.dsp.window.fullscreen({{ mode = 0, action = "{action}", window = w }}))
        local mode = w.fullscreen
        if type(result) == "table" and result.ok == true and type(mode) == "number"
            and (mode == 2) == {str(state).lower()} then return "bwm-r4-fullscreen-ok" end
        return "bwm-r4-fullscreen-rejected"
    end)()'''


def native_fullscreen(client: dict, state: bool) -> bool:
    if not native_fullscreen_allowed(client):
        return False
    reply = subprocess.run(["hyprctl", "repl", native_fullscreen_lua(client, state)],
                           capture_output=True, text=True, timeout=2)
    return reply.returncode == 0 and reply.stdout.strip() == "bwm-r4-fullscreen-ok"


def native_window_allowed(client: dict) -> bool:
    """Native move/resize/no-border/no-capture: same ordinary-window guard as fullscreen."""
    return native_fullscreen_allowed(client)


def native_tag_lua(client: dict, tag: str, state: bool) -> str:
    sign = "+" if state else "-"
    return f'''(function()
        local theme = package.loaded["modules.theme"]
        local w = hl.get_window("address:{client['address']}")
        if not theme or theme.name ~= "plasma" or not w or w.pid ~= {int(client['pid'])}
            or not w.mapped or w.hidden or w.pinned then return "bwm-r4-tag-rejected" end
        local ws = w.workspace
        if not ws or ws.id < 1 or ws.id == 99 or ws.name == "special:minimized" then return "bwm-r4-tag-rejected" end
        local result = hl.dispatch(hl.dsp.window.tag({{ tag = "{sign}{tag}", window = w }}))
        if type(result) == "table" and result.ok == true then return "bwm-r4-tag-ok" end
        return "bwm-r4-tag-rejected"
    end)()'''


def native_tag(client: dict, tag: str, state: bool) -> bool:
    """Desired tag state with live guards, dispatcher receipt and a fresh IPC readback."""
    if not native_window_allowed(client):
        return False
    if has_tag(client, tag) == state:
        return True  # Idempotent: duplicated requests never invert the state.
    reply = subprocess.run(["hyprctl", "repl", native_tag_lua(client, tag, state)],
                           capture_output=True, text=True, timeout=2)
    if reply.returncode != 0 or reply.stdout.strip() != "bwm-r4-tag-ok":
        return False
    fresh = next((c for c in hypr_json("clients") or [] if c.get("address") == client.get("address")
                  and c.get("pid") == client.get("pid")), None)
    return bool(fresh) and has_tag(fresh, tag) == state


def native_interactive(client: dict, operation: str) -> bool:
    """Pointer-driven move/resize of breezebars; its hyprctl handler answers "ok"."""
    if not native_window_allowed(client) or not client.get("floating") or client.get("fullscreen", 0):
        return False
    reply = subprocess.run(["hyprctl", "breezebars-interactive", f"{operation} {client['address']}"],
                           capture_output=True, text=True, timeout=2)
    return reply.returncode == 0 and reply.stdout.strip() == "ok"


def toggle_tag(client: dict, tag: str):
    sign = "-" if has_tag(client, tag) else "+"
    run_lua(window_lua(client, f'hl.dispatch(hl.dsp.window.tag({{ tag = "{sign}{tag}", window = w }}))'))


def to_screen(client: dict, monitor: str):
    """Mover a otra pantalla conservando la posición relativa (como KWin sendToOutput)."""
    monitors = hypr_json("monitors") or []
    from bwm_windows import monitor_matches
    target = next((m for m in monitors if monitor_matches(m, monitor)), None)
    source = next((m for m in monitors if m.get("id") == client.get("monitor")), None)
    if not target or not source or target is source:
        return
    from bwm_windows import monitor_box
    sx, sy, sw, sh = monitor_box(source)
    tx, ty, tw, th = monitor_box(target)
    (x, y), (w, h) = client.get("at", [sx, sy]), client.get("size", [1, 1])
    nx = tx + (x - sx) * tw / max(1, sw)
    ny = ty + (y - sy) * th / max(1, sh)
    w, h = min(w, tw), min(h, th)
    nx = max(tx, min(nx, tx + tw - w))
    ny = max(ty, min(ny, ty + th - h))
    ws = target.get("activeWorkspace", {}).get("id")
    geometry = ""
    if client.get("floating"):
        geometry = (f"hl.dispatch(hl.dsp.window.resize({{ x = {int(w)}, y = {int(h)}, relative = false, window = w }})) "
                    f"hl.dispatch(hl.dsp.window.move({{ x = {int(nx)}, y = {int(ny)}, relative = false, window = w }}))")
    # El workspace antes que la geometría (regla 17)
    run_lua(window_lua(client, f"hl.dispatch(hl.dsp.window.move({{ workspace = {ws}, follow = false, window = w }})) {geometry}"))


def open_menu(client: dict):
    """Alt+F3: el menú de la ventana bajo el borde izquierdo de su barra de título."""
    borders = window_borders(client)
    x, y, w, h = frame_from_client(client, borders)
    top = borders["top"] or 0
    subprocess.Popen(["qs", "-c", "ii", "ipc", "call", "plasmaWindowMenu", "open", client["address"], str(int(x + 4)),
                      str(int(y + top))], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def open_rules(client: dict, kind: str):
    """F10 uses the original editor. KWin's UUID-based preselection needs its D-Bus service,
    so class/title are selected manually; never send a Hyprland address as a KWin UUID."""
    subprocess.Popen(["kcmshell6", "kcm_kwinrules"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     start_new_session=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pid", type=int, help="Expected process for a panel task")
    parser.add_argument("--native-serialized", action="store_true", help="Experimental native adapter transaction; requires Breeze and a private runtime")
    parser.add_argument("--expected-generation", help="Expected Linux process start, rechecked after acquiring the native transaction")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("maximize")
    p.add_argument("--mode", choices=["toggle", "full", "vertical", "horizontal", "restore"], default="toggle")
    p.add_argument("address", nargs="?")
    sub.add_parser("alt-enter").add_argument("address", nargs="?")
    for name in ("minimize", "toggle-minimize", "state"):
        sub.add_parser(name).add_argument("address", nargs="?")
    for name in ("unminimize", "activate", "focus"):
        sub.add_parser(name).add_argument("address")
    sub.add_parser("show-desktop").add_argument("leave", nargs="?", choices=["enter", "leave"])
    p = sub.add_parser("fullscreen")
    p.add_argument("--state", choices=("toggle", "on", "off"), default="toggle")
    p.add_argument("address", nargs="?")
    for name in ("menu", "pin", "close"):
        sub.add_parser(name).add_argument("address", nargs="?")
    for name in ("no-border", "no-capture"):
        p = sub.add_parser(name)
        p.add_argument("--state", choices=("toggle", "on", "off"), default="toggle")
        p.add_argument("address", nargs="?")
    p = sub.add_parser("interactive")
    p.add_argument("operation", choices=["move", "resize"])
    p.add_argument("address", nargs="?")
    p = sub.add_parser("to-desktop")
    p.add_argument("workspace", type=int)
    p.add_argument("address", nargs="?")
    p = sub.add_parser("to-screen")
    p.add_argument("monitor")
    p.add_argument("address", nargs="?")
    p = sub.add_parser("rules")
    p.add_argument("kind", choices=["window", "application"])
    p.add_argument("address", nargs="?")
    args = parser.parse_args(argv)

    if args.expected_generation and (not args.native_serialized or args.pid is None):
        parser.error('--expected-generation requires --native-serialized and --pid')
    if args.native_serialized:
        if args.cmd not in ('focus','toggle-minimize','maximize','close','show-desktop','fullscreen','interactive','no-border','no-capture'):
            parser.error('Unsupported native adapter operation')
        if args.cmd in ('fullscreen','no-border','no-capture') and (not args.expected_generation or args.pid is None or args.state == 'toggle'):
            parser.error('Native state changes require --expected-generation, --pid and --state on|off')
        if args.cmd == 'interactive' and (not args.expected_generation or args.pid is None):
            parser.error('Native interactive operations require --expected-generation and --pid')
        from native_guard import action_lock, require_breeze
        try:
            with action_lock():
                require_breeze()
                return execute(args)
        except (OSError,KeyError,ValueError,TimeoutError,subprocess.SubprocessError):
            print('BWM: native transaction unavailable or rejected',file=sys.stderr)
            return 1
    return execute(args)


def execute(args) -> int:

    if args.cmd == "show-desktop":
        tm = minimizer()
        active = hypr_json("activewindow") or {}
        tm.show_desktop(hypr_json("clients") or [], leave=args.leave == "leave", keep_focus=active.get("address", ""),
                        **({"enter": True} if args.leave == "enter" else {}))
        return 0

    client = find_client(getattr(args, "address", None))
    if not client or (args.pid is not None and client.get("pid") != args.pid):
        return 1
    if args.expected_generation and bwm_windows.process_generation(client.get('pid'))!=args.expected_generation:
        return 1
    if args.cmd == "maximize":
        maximize(client, args.mode)
    elif args.cmd == "alt-enter":
        alt_enter(client)
    elif args.cmd == "minimize":
        minimizer().minimize_win(client)
    elif args.cmd == "unminimize":
        minimizer().restore_win(client)
    elif args.cmd == "toggle-minimize":
        tm = minimizer()
        tm.restore_win(client) if tm.is_minimized(client) else tm.minimize_win(client)
    elif args.cmd == "focus":
        if minimizer().is_minimized(client):
            minimizer().restore_win(client)
        else:
            focus(client)
    elif args.cmd == "activate":
        # Como la barra de tareas de Plasma: minimizada → restaurar; activa → minimizar; otra → enfocar
        tm = minimizer()
        active = hypr_json("activewindow") or {}
        if tm.is_minimized(client):
            tm.restore_win(client)
        elif client.get("address") == active.get("address"):
            tm.minimize_win(client)
        else:
            focus(client)
    elif args.cmd == "menu":
        open_menu(client)
    elif args.cmd == "interactive":
        if args.native_serialized:
            return 0 if native_interactive(client, args.operation) else 1
        subprocess.run(["hyprctl", "breezebars-interactive", f"{args.operation} {client['address']}"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif args.cmd == "fullscreen":
        if args.native_serialized:
            return 0 if native_fullscreen(client, args.state == "on") else 1
        action = {"toggle": "toggle", "on": "set", "off": "unset"}[args.state]
        run_lua(window_lua(client, f"hl.dispatch(hl.dsp.window.fullscreen({{ mode = 0, action = '{action}', window = w }}))"))
    elif args.cmd in ("no-border", "no-capture"):
        tag = TAG_NO_BORDER if args.cmd == "no-border" else TAG_NO_CAPTURE
        if args.native_serialized:
            return 0 if native_tag(client, tag, args.state == "on") else 1
        if args.state == "toggle":
            toggle_tag(client, tag)
        elif has_tag(client, tag) != (args.state == "on"):
            toggle_tag(client, tag)
    elif args.cmd == "pin":
        if not client.get("floating"):
            run_lua(window_lua(client, "hl.dispatch(hl.dsp.window.float({ action = 'enable', window = w }))"))
        run_lua(window_lua(client, "hl.dispatch(hl.dsp.window.pin({ action = 'toggle', window = w }))"))
    elif args.cmd == "close":
        run_lua(window_lua(client, "hl.dispatch(hl.dsp.window.close({ window = w }))"))
    elif args.cmd == "to-desktop":
        if args.workspace >= 1:
            run_lua(window_lua(client, f"hl.dispatch(hl.dsp.window.move({{ workspace = {args.workspace}, follow = false, window = w }}))"))
    elif args.cmd == "to-screen":
        to_screen(client, args.monitor)
    elif args.cmd == "rules":
        open_rules(client, args.kind)
    elif args.cmd == "state":
        borders = window_borders(client)
        print(json.dumps({"address": client["address"], "mode": mode_from_tags(client.get("tags")),
                          "restore": stored_restore(client), "borders": borders,
                          "frame": frame_from_client(client, borders), "area": work_area(client)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
