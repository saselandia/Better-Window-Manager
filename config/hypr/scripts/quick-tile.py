#!/usr/bin/env python3
"""
Quick Tile / Window Snapping script for Hyprland (KDE Plasma Style).
Usage: quick-tile.py <direction> [window_address]
Directions: left, right, top, bottom, top-left, top-right, bottom-left, bottom-right, center, maximize
"""

import sys
import os
import json
import subprocess

def run_lua(lua: str):
    subprocess.run(["hyprctl", "dispatch", lua], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def is_plasma_active() -> bool:
    try:
        theme_path = os.path.expanduser("~/.config/hypr/modules/theme.lua")
        with open(theme_path, "r", encoding="utf-8") as f:
            return 'name = "plasma"' in f.read()
    except Exception:
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: quick-tile.py <direction> [window_address]")
        sys.exit(1)

    direction = sys.argv[1].lower().strip()
    target_addr = sys.argv[2].strip() if len(sys.argv) > 2 else None

    # Fetch clients to locate window
    clients = []
    try:
        clients_str = subprocess.check_output(["hyprctl", "clients", "-j"]).decode("utf-8")
        clients = json.loads(clients_str)
    except Exception:
        pass

    target_win = None
    if target_addr:
        target_win = next((c for c in clients if c.get("address") == target_addr), None)

    if not target_win:
        try:
            active_str = subprocess.check_output(["hyprctl", "activewindow", "-j"]).decode("utf-8")
            target_win = json.loads(active_str)
        except Exception:
            target_win = None

    if not target_win or not target_win.get("address"):
        sys.exit(0)

    addr = target_win.get("address")
    mon_id = target_win.get("monitor", 0)

    # Fetch monitors
    try:
        mon_str = subprocess.check_output(["hyprctl", "monitors", "-j"]).decode("utf-8")
        monitors = json.loads(mon_str)
    except Exception:
        monitors = []

    target_mon = next((m for m in monitors if m.get("id") == mon_id), None)
    if not target_mon and monitors:
        target_mon = monitors[0]

    if not target_mon:
        sys.exit(0)

    mx = target_mon.get("x", 0)
    my = target_mon.get("y", 0)
    mw = target_mon.get("width", 1920)
    mh = target_mon.get("height", 1080)

    # Reserved space from bars (e.g. Quickshell bottom bar)
    res = target_mon.get("reserved", [0, 0, 0, 44])
    res_l = res[0] if len(res) > 0 else 0
    res_t = res[1] if len(res) > 1 else 0
    res_r = res[2] if len(res) > 2 else 0
    res_b = res[3] if len(res) > 3 else 44
    if res_b == 0:
        res_b = 44  # Guarantee 44px panel space

    usable_x = mx + res_l
    usable_y = my + res_t
    usable_w = mw - res_l - res_r
    usable_h = mh - res_t - res_b

    tags = target_win.get("tags", [])
    is_snapped = "snapped" in tags
    is_fullscreen = target_win.get("fullscreen", 0) > 0 or target_win.get("fullscreenClient", 0) > 0
    is_floating = target_win.get("floating", True)

    def restore():
        target_w = int(usable_w * 0.65)
        target_h = int(usable_h * 0.70)
        target_x = usable_x + (usable_w - target_w) // 2
        target_y = usable_y + (usable_h - target_h) // 2
        lua = f"""(function()
            local win = hl.get_window("address:{addr}")
            if not win then return hl.dsp.no_op() end
            hl.dispatch(hl.dsp.window.fullscreen({{ mode = 1, action = 'unset', window = win }}))
            hl.dispatch(hl.dsp.window.fullscreen({{ mode = 0, action = 'unset', window = win }}))
            hl.dispatch(hl.dsp.window.clear_tags({{ window = win }}))
            hl.dispatch(hl.dsp.window.resize({{ x = {int(target_w)}, y = {int(target_h)}, relative = false, window = win }}))
            hl.dispatch(hl.dsp.window.move({{ x = {int(target_x)}, y = {int(target_y)}, relative = false, window = win }}))
            return hl.dsp.no_op()
        end)()"""
        run_lua(lua)

    def apply_snap(dir_name: str, x: int, y: int, w: int, h: int):
        float_cmd = ""
        if not is_floating:
            float_cmd = "hl.dispatch(hl.dsp.window.float({ window = win }))"

        lua = f"""(function()
            local win = hl.get_window("address:{addr}")
            if not win then return hl.dsp.no_op() end
            {float_cmd}
            hl.dispatch(hl.dsp.window.fullscreen({{ mode = 1, action = 'unset', window = win }}))
            hl.dispatch(hl.dsp.window.fullscreen({{ mode = 0, action = 'unset', window = win }}))
            hl.dispatch(hl.dsp.window.clear_tags({{ window = win }}))
            hl.dispatch(hl.dsp.window.tag({{ tag = "snapped", window = win }}))
            hl.dispatch(hl.dsp.window.tag({{ tag = "snapped_{dir_name}", window = win }}))
            hl.dispatch(hl.dsp.window.resize({{ x = {int(w)}, y = {int(h)}, relative = false, window = win }}))
            hl.dispatch(hl.dsp.window.move({{ x = {int(x)}, y = {int(y)}, relative = false, window = win }}))
            return hl.dsp.no_op()
        end)()"""
        run_lua(lua)

    # 1. Super+Up / Maximize
    if direction in ("top", "maximize"):
        if f"snapped_{direction}" in tags or "snapped_top" in tags or "snapped_maximize" in tags or is_fullscreen:
            restore()
        else:
            apply_snap("top", usable_x, usable_y, usable_w, usable_h)
        return

    # 2. Super+Down / Restore
    if direction == "bottom":
        if is_fullscreen or is_snapped:
            restore()
            return

    # 3. Toggle off if already snapped to the same direction
    if f"snapped_{direction}" in tags:
        restore()
        return

    # 4. Center mode
    if direction == "center":
        restore()
        return

    # 5. Snap to halves / quarters with 0 gaps touching edges & bottom bar flush
    half_w = usable_w // 2
    half_h = usable_h // 2
    rem_w  = usable_w - half_w
    rem_h  = usable_h - half_h

    if direction == "left":
        apply_snap(direction, usable_x, usable_y, half_w, usable_h)
    elif direction == "right":
        apply_snap(direction, usable_x + half_w, usable_y, rem_w, usable_h)
    elif direction == "bottom":
        apply_snap(direction, usable_x, usable_y + half_h, usable_w, rem_h)
    elif direction in ("top-left", "up-left"):
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
