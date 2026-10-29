#!/usr/bin/env python3
"""
Quick Tile / Window Snapping script for Hyprland (KDE Plasma Style).
Usage: quick-tile.py <direction> [window_address] [--monitor desc:...] [--edge]
Directions: left, right, top, bottom, top-left, top-right, bottom-left, bottom-right, center, maximize
"""

import sys
import argparse
import os
import json
import subprocess
PRESNAP_JSON = "/tmp/hypr_presnap_sizes.json"
PRESNAP_TXT  = "/tmp/hypr_presnap_sizes.txt"

def get_saved_presnap(addr: str):
    # Try .txt first (used by hyprbars plugin)
    try:
        if os.path.exists(PRESNAP_TXT):
            with open(PRESNAP_TXT, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(addr + ":"):
                        parts = line.split(":", 1)[1].split(",")
                        return [int(parts[0]), int(parts[1])]
    except Exception:
        pass
    # Try .json
    try:
        if os.path.exists(PRESNAP_JSON):
            with open(PRESNAP_JSON, "r") as f:
                data = json.load(f)
                return data.get(addr)
    except Exception:
        pass
    return None

def save_presnap(addr: str, size: list):
    # Save to JSON
    try:
        data = {}
        if os.path.exists(PRESNAP_JSON):
            try:
                with open(PRESNAP_JSON, "r") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data[addr] = size
        with open(PRESNAP_JSON, "w") as f:
            json.dump(data, f)
    except Exception:
        pass
    # Save to TXT
    try:
        txt_data = {}
        if os.path.exists(PRESNAP_TXT):
            try:
                with open(PRESNAP_TXT, "r") as f:
                    for line in f:
                        line = line.strip()
                        if ":" in line and "," in line:
                            k, v = line.split(":", 1)
                            w, h = v.split(",", 1)
                            txt_data[k] = (int(w), int(h))
            except Exception:
                txt_data = {}
        txt_data[addr] = (int(size[0]), int(size[1]))
        with open(PRESNAP_TXT, "w") as f:
            for k, (w, h) in txt_data.items():
                f.write(f"{k}:{w},{h}\n")
    except Exception:
        pass

def remove_presnap(addr: str):
    try:
        if os.path.exists(PRESNAP_JSON):
            with open(PRESNAP_JSON, "r") as f:
                data = json.load(f)
            if addr in data:
                del data[addr]
                with open(PRESNAP_JSON, "w") as f:
                    json.dump(data, f)
    except Exception:
        pass
    try:
        if os.path.exists(PRESNAP_TXT):
            lines = []
            with open(PRESNAP_TXT, "r") as f:
                for line in f:
                    if not line.strip().startswith(addr + ":"):
                        lines.append(line)
            with open(PRESNAP_TXT, "w") as f:
                f.writelines(lines)
    except Exception:
        pass


def run_lua(lua: str):
    subprocess.run(["hyprctl", "dispatch", lua], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def is_plasma_active() -> bool:
    try:
        theme_path = os.path.expanduser("~/.config/hypr/modules/theme.lua")
        with open(theme_path, "r", encoding="utf-8") as f:
            return 'name = "plasma"' in f.read()
    except Exception:
        return False

def usable_geometry(mon):
    """Área de trabajo global en píxeles lógicos; reserved ya viene en unidades lógicas."""
    from bwm_windows import monitor_box
    x, y, width, height = monitor_box(mon)
    left, top, right, bottom = (list(mon.get("reserved", [])) + [0, 0, 0, 0])[:4]
    return (int(x + left), int(y + top), max(1, int(width - left - right)),
            max(1, int(height - top - bottom)))


def drag_monitor(monitors, point, direction):
    """Usar el borde mostrado, aunque la ventana o el puntero hayan cruzado ligeramente la unión."""
    from bwm_windows import monitor_box
    x, y = point["x"], point["y"]
    candidates = []
    for mon in monitors:
        mx, my, mw, mh = monitor_box(mon)
        if not (mx - 40 <= x <= mx + mw + 40 and my - 40 <= y <= my + mh + 40):
            continue
        dx = abs(x - mx) if "left" in direction else abs(x - mx - mw) if "right" in direction else 0
        dy = abs(y - my) if "top" in direction or direction in ("up", "maximize") else abs(y - my - mh) if "bottom" in direction or direction == "down" else 0
        if max(dx, dy) <= 40:
            candidates.append((dx + dy, mon))
    if candidates:
        return min(candidates, key=lambda c: c[0])[1]
    return next((m for m in monitors if (lambda b: b[0] <= x < b[0] + b[2]
                 and b[1] <= y < b[1] + b[3])(monitor_box(m))), None)


def content_geometry(x, y, width, height, titlebar):
    """La previsualización mide el marco completo; Hyprland mueve/redimensiona el contenido."""
    return int(x), int(y + titlebar), int(width), max(1, int(height - titlebar))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("direction", choices=["left", "right", "top", "bottom", "top-left", "top-right",
        "bottom-left", "bottom-right", "up", "down", "up-left", "up-right", "down-left", "down-right",
        "center", "maximize"])
    parser.add_argument("window_address", nargs="?")
    parser.add_argument("--monitor", help="Monitor del destino de la previsualización (desc:descripción)")
    parser.add_argument("--pid", type=int, help="PID de la ventana al comenzar el snap")
    parser.add_argument("--edge", action="store_true", help="Arrastre: destino exacto, sin alternar/restaurar")
    args = parser.parse_args(argv)
    direction = args.direction
    target_addr = args.window_address
    # El plugin antiguo sólo pasaba una dirección y la dirección de ventana: también es arrastre.
    edge = args.edge or target_addr is not None
    try:
        clients = json.loads(subprocess.check_output(["hyprctl", "clients", "-j"]))
        if target_addr:
            target_win = next((c for c in clients if c.get("address") == target_addr), None)
        else:
            target_win = json.loads(subprocess.check_output(["hyprctl", "activewindow", "-j"]))
        monitors = json.loads(subprocess.check_output(["hyprctl", "monitors", "-j"]))
    except (OSError, ValueError, subprocess.SubprocessError):
        return
    if not target_win or not target_win.get("address"):
        return  # no sustituir una ventana explícita desaparecida por la ventana con foco
    if args.pid is not None and target_win.get("pid") != args.pid:
        return
    addr = target_win["address"]
    mon_id = target_win.get("monitor")
    target_mon = None
    if args.monitor:
        target_mon = next((m for m in monitors if "desc:" + m.get("description", "") == args.monitor), None)
        if target_mon is None:
            parser.error("El monitor de la previsualización ya no está conectado")
    elif edge:
        try:
            point = json.loads(subprocess.check_output(["hyprctl", "cursorpos", "-j"]))
            target_mon = drag_monitor(monitors, point, direction)
        except (OSError, ValueError, subprocess.SubprocessError, KeyError):
            pass
    target_mon = target_mon or next((m for m in monitors if m.get("id") == mon_id), None)
    if not target_mon:
        return
    usable_x, usable_y, usable_w, usable_h = usable_geometry(target_mon)
    # El workspace queda fijado antes de redimensionar: el centro puede cruzar otro monitor.
    same_monitor = target_mon["id"] == mon_id
    workspace = target_win["workspace"]["id"] if same_monitor else target_mon["activeWorkspace"]["id"]
    place_workspace = f"hl.dispatch(hl.dsp.window.move({{ workspace = {workspace}, follow = false, window = win }}))"
    titlebar = 0
    if is_plasma_active():
        try:
            from bwm_windows import titlebars, has_titlebar
            if has_titlebar(target_win, titlebars()):
                opt = json.loads(subprocess.check_output(["hyprctl", "getoption", "plugin:hyprbars:bar_height", "-j"]))
                titlebar = max(0, opt.get("int", 30))
        except (OSError, ValueError, subprocess.SubprocessError):
            titlebar = 30

    tags = target_win.get("tags", [])
    is_snapped = "snapped" in tags
    is_fullscreen = target_win.get("fullscreen", 0) > 0 or target_win.get("fullscreenClient", 0) > 0

    if not is_snapped and not is_fullscreen:
        cur_sz = target_win.get("size", [900, 600])
        if cur_sz and len(cur_sz) == 2 and cur_sz[0] > 100 and cur_sz[1] > 100:
            save_presnap(addr, cur_sz)

    def restore():
        saved = get_saved_presnap(addr)
        if saved and len(saved) == 2 and saved[0] > 100 and saved[1] > 100:
            target_w = saved[0]
            target_h = saved[1]
            remove_presnap(addr)
        elif is_fullscreen and not is_snapped:
            lua = f"""(function()
                local win = hl.get_window("address:{addr}")
                if not win then return hl.dsp.no_op() end
                hl.dispatch(hl.dsp.window.fullscreen({{ mode = 1, action = 'unset', window = win }}))
                hl.dispatch(hl.dsp.window.fullscreen({{ mode = 0, action = 'unset', window = win }}))
                return hl.dsp.no_op()
            end)()"""
            run_lua(lua)
            return
        else:
            target_w = int(usable_w * 0.65)
            target_h = int(usable_h * 0.70)
        target_x = usable_x + (usable_w - target_w) // 2
        target_y = usable_y + (usable_h - target_h) // 2
        lua = f"""(function()
            local win = hl.get_window("address:{addr}")
            if not win then return hl.dsp.no_op() end
            hl.dispatch(hl.dsp.window.fullscreen({{ mode = 1, action = 'unset', window = win }}))
            hl.dispatch(hl.dsp.window.fullscreen({{ mode = 0, action = 'unset', window = win }}))
            {place_workspace}
            hl.dispatch(hl.dsp.window.clear_tags({{ window = win }}))
            hl.dispatch(hl.dsp.window.float({{ action = 'enable', window = win }}))
            hl.dispatch(hl.dsp.window.resize({{ x = {int(target_w)}, y = {int(target_h)}, relative = false, window = win }}))
            hl.dispatch(hl.dsp.window.move({{ x = {int(target_x)}, y = {int(target_y)}, relative = false, window = win }}))
            return hl.dsp.no_op()
        end)()"""
        run_lua(lua)

    def apply_snap(dir_name: str, x: int, y: int, w: int, h: int):
        x, y, w, h = content_geometry(x, y, w, h, titlebar)
        float_cmd = "hl.dispatch(hl.dsp.window.float({ action = 'enable', window = win }))"
        lua = f"""(function()
            local win = hl.get_window("address:{addr}")
            if not win then return hl.dsp.no_op() end
            {float_cmd}
            hl.dispatch(hl.dsp.window.fullscreen({{ mode = 1, action = 'unset', window = win }}))
            hl.dispatch(hl.dsp.window.fullscreen({{ mode = 0, action = 'unset', window = win }}))
            {place_workspace}
            hl.dispatch(hl.dsp.window.clear_tags({{ window = win }}))
            hl.dispatch(hl.dsp.window.tag({{ tag = "snapped", window = win }}))
            hl.dispatch(hl.dsp.window.tag({{ tag = "snapped_{dir_name}", window = win }}))
            hl.dispatch(hl.dsp.window.resize({{ x = {int(w)}, y = {int(h)}, relative = false, window = win }}))
            hl.dispatch(hl.dsp.window.move({{ x = {int(x)}, y = {int(y)}, relative = false, window = win }}))
            return hl.dsp.no_op()
        end)()"""
        run_lua(lua)

    # 5. Snap to halves / quarters with 0 gaps touching edges & bottom bar flush
    half_w = usable_w // 2
    half_h = usable_h // 2
    rem_w  = usable_w - half_w
    rem_h  = usable_h - half_h

    if edge:
        # Un arrastre siempre aplica exactamente el destino mostrado, incluso si ya estaba encajada.
        boxes = {
            "left": (usable_x, usable_y, half_w, usable_h),
            "right": (usable_x + half_w, usable_y, rem_w, usable_h),
            "top": (usable_x, usable_y, usable_w, usable_h),
            "maximize": (usable_x, usable_y, usable_w, usable_h),
            "bottom": (usable_x, usable_y + half_h, usable_w, rem_h),
            "top-left": (usable_x, usable_y, half_w, half_h),
            "top-right": (usable_x + half_w, usable_y, rem_w, half_h),
            "bottom-left": (usable_x, usable_y + half_h, half_w, rem_h),
            "bottom-right": (usable_x + half_w, usable_y + half_h, rem_w, rem_h),
        }
        canonical = direction.replace("up", "top").replace("down", "bottom")
        if canonical in boxes:
            apply_snap(canonical, *boxes[canonical])
            return

    cur_at = target_win.get("at", [0, 0])
    cur_sz = target_win.get("size", [0, 0])
    cur_x, cur_y = cur_at[0], cur_at[1]
    cur_w, cur_h = cur_sz[0], cur_sz[1] + titlebar
    cur_y -= titlebar

    # Precise detection of current snapped position (via tags or geometry)
    is_top_left = "snapped_top-left" in tags or "snapped_up-left" in tags or (abs(cur_x - usable_x) <= 25 and abs(cur_y - usable_y) <= 25 and cur_w <= half_w + 35 and cur_h <= half_h + 35)
    is_bottom_left = "snapped_bottom-left" in tags or "snapped_down-left" in tags or (abs(cur_x - usable_x) <= 25 and abs(cur_y - (usable_y + half_h)) <= 35 and cur_w <= half_w + 35 and cur_h <= rem_h + 35)
    is_top_right = "snapped_top-right" in tags or "snapped_up-right" in tags or (abs(cur_x - (usable_x + half_w)) <= 35 and abs(cur_y - usable_y) <= 25 and cur_w <= rem_w + 35 and cur_h <= half_h + 35)
    is_bottom_right = "snapped_bottom-right" in tags or "snapped_down-right" in tags or (abs(cur_x - (usable_x + half_w)) <= 35 and abs(cur_y - (usable_y + half_h)) <= 35 and cur_w <= rem_w + 35 and cur_h <= rem_h + 35)

    is_left_side = ("snapped_left" in tags or (abs(cur_x - usable_x) <= 25 and cur_w <= half_w + 35 and cur_h > usable_h * 0.7)) and not (is_top_left or is_bottom_left)
    is_right_side = ("snapped_right" in tags or (abs(cur_x - (usable_x + half_w)) <= 35 and cur_w <= rem_w + 35 and cur_h > usable_h * 0.7)) and not (is_top_right or is_bottom_right)

    # 1. Down / Bottom
    if direction in ("bottom", "down"):
        if is_left_side or is_top_left:
            apply_snap("bottom-left", usable_x, usable_y + half_h, half_w, rem_h)
            return
        elif is_right_side or is_top_right:
            apply_snap("bottom-right", usable_x + half_w, usable_y + half_h, rem_w, rem_h)
            return
        elif is_bottom_left or is_bottom_right or is_snapped or is_fullscreen:
            restore()
            return
        else:
            restore()
            return

    # 2. Up / Top / Maximize
    if direction in ("top", "maximize", "up"):
        if is_left_side or is_bottom_left:
            apply_snap("top-left", usable_x, usable_y, half_w, half_h)
            return
        elif is_right_side or is_bottom_right:
            apply_snap("top-right", usable_x + half_w, usable_y, rem_w, half_h)
            return
        elif is_top_left or is_top_right:
            apply_snap("top", usable_x, usable_y, usable_w, usable_h)
            return
        elif "snapped_top" in tags or "snapped_maximize" in tags or is_fullscreen:
            restore()
            return
        else:
            apply_snap("top", usable_x, usable_y, usable_w, usable_h)
            return

    # 3. Left
    if direction == "left":
        if is_top_right:
            apply_snap("top-left", usable_x, usable_y, half_w, half_h)
            return
        elif is_bottom_right:
            apply_snap("bottom-left", usable_x, usable_y + half_h, half_w, rem_h)
            return
        elif is_top_left or is_bottom_left:
            apply_snap("left", usable_x, usable_y, half_w, usable_h)
            return
        elif "snapped_left" in tags or is_left_side:
            restore()
            return
        else:
            apply_snap("left", usable_x, usable_y, half_w, usable_h)
            return

    # 4. Right
    if direction == "right":
        if is_top_left:
            apply_snap("top-right", usable_x + half_w, usable_y, rem_w, half_h)
            return
        elif is_bottom_left:
            apply_snap("bottom-right", usable_x + half_w, usable_y + half_h, rem_w, rem_h)
            return
        elif is_top_right or is_bottom_right:
            apply_snap("right", usable_x + half_w, usable_y, rem_w, usable_h)
            return
        elif "snapped_right" in tags or is_right_side:
            restore()
            return
        else:
            apply_snap("right", usable_x + half_w, usable_y, rem_w, usable_h)
            return

    # 5. Center mode
    if direction == "center":
        restore()
        return

    # 6. Specific corner directives
    if direction in ("top-left", "up-left"):
        apply_snap(direction, usable_x, usable_y, half_w, half_h)
    elif direction in ("top-right", "up-right"):
        apply_snap(direction, usable_x + half_w, usable_y, rem_w, half_h)
    elif direction in ("bottom-left", "down-left"):
        apply_snap(direction, usable_x, usable_y + half_h, half_w, rem_h)
    elif direction in ("bottom-right", "down-right"):
        apply_snap(direction, usable_x + half_w, usable_y + half_h, rem_w, rem_h)
    else:
        apply_snap(direction, usable_x, usable_y, half_w, usable_h)

if __name__ == "__main__":
    main()
