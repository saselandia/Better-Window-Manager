#!/usr/bin/env python3
"""
Quick Tile / Window Snapping script for Hyprland (KDE Plasma Style).
Usage: quick-tile.py <left|right|top|bottom|top-left|top-right|bottom-left|bottom-right|center|maximize>
"""

import sys
import json
import subprocess

def run_dispatch(cmd: str):
    subprocess.run(["hyprctl", "dispatch", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    if len(sys.argv) < 2:
        print("Usage: quick-tile.py <direction>")
        sys.exit(1)

    direction = sys.argv[1].lower().strip()

    try:
        active_str = subprocess.check_output(["hyprctl", "activewindow", "-j"]).decode("utf-8")
        active = json.loads(active_str)
    except Exception:
        sys.exit(0)

    if not active or not active.get("address"):
        sys.exit(0)

    mon_id = active.get("monitor", 0)

    try:
        mon_str = subprocess.check_output(["hyprctl", "monitors", "-j"]).decode("utf-8")
        monitors = json.loads(mon_str)
    except Exception:
        sys.exit(0)

    target_mon = next((m for m in monitors if m.get("id") == mon_id), None)
    if not target_mon and monitors:
        target_mon = monitors[0]

    if not target_mon:
        sys.exit(0)

    # Monitor geometry
    mx = target_mon.get("x", 0)
    my = target_mon.get("y", 0)
    mw = target_mon.get("width", 1920)
    mh = target_mon.get("height", 1080)

    # Reserved bounds [left, top, right, bottom] (e.g. Quickshell bar)
    res = target_mon.get("reserved", [0, 0, 0, 0])
    res_l = res[0] if len(res) > 0 else 0
    res_t = res[1] if len(res) > 1 else 0
    res_r = res[2] if len(res) > 2 else 0
    res_b = res[3] if len(res) > 3 else 0

    usable_x = mx + res_l
    usable_y = my + res_t
    usable_w = mw - res_l - res_r
    usable_h = mh - res_t - res_b

    is_fullscreen = active.get("fullscreen", 0) > 0 or active.get("fullscreenClient", 0) > 0

    if direction in ("top", "maximize"):
        # KDE style: Super+Up maximizes, or restores if already fullscreen
        run_dispatch("hl.dsp.window.fullscreen({ mode = 1, action = 'toggle' })")
        return

    if direction == "bottom":
        # If currently maximized, Super+Down restores window
        if is_fullscreen:
            run_dispatch("hl.dsp.window.fullscreen({ mode = 1, action = 'disable' })")
            return

    # If currently fullscreen and snapping to a side/quarter, disable fullscreen first
    if is_fullscreen:
        run_dispatch("hl.dsp.window.fullscreen({ mode = 1, action = 'disable' })")

    # Ensure window is floating
    if not active.get("floating", False):
        run_dispatch("hl.dsp.window.float({ action = 'enable' })")

    gap = 6
    half_w = (usable_w // 2) - gap - (gap // 2)
    half_h = (usable_h // 2) - gap - (gap // 2)
    full_h = usable_h - (gap * 2)
    full_w = usable_w - (gap * 2)

    left_x = usable_x + gap
    right_x = usable_x + (usable_w // 2) + (gap // 2)
    top_y = usable_y + gap
    bottom_y = usable_y + (usable_h // 2) + (gap // 2)

    target_x = usable_x
    target_y = usable_y
    target_w = full_w
    target_h = full_h

    if direction == "left":
        target_x = left_x
        target_y = top_y
        target_w = half_w
        target_h = full_h
    elif direction == "right":
        target_x = right_x
        target_y = top_y
        target_w = half_w
        target_h = full_h
    elif direction == "bottom":
        target_x = left_x
        target_y = bottom_y
        target_w = full_w
        target_h = half_h
    elif direction in ("top-left", "up-left"):
        target_x = left_x
        target_y = top_y
        target_w = half_w
        target_h = half_h
    elif direction in ("top-right", "up-right"):
        target_x = right_x
        target_y = top_y
        target_w = half_w
        target_h = half_h
    elif direction in ("bottom-left", "down-left"):
        target_x = left_x
        target_y = bottom_y
        target_w = half_w
        target_h = half_h
    elif direction in ("bottom-right", "down-right"):
        target_x = right_x
        target_y = bottom_y
        target_w = half_w
        target_h = half_h
    elif direction == "center":
        target_w = int(usable_w * 0.70)
        target_h = int(usable_h * 0.75)
        target_x = usable_x + (usable_w - target_w) // 2
        target_y = usable_y + (usable_h - target_h) // 2

    # Apply resize and move
    run_dispatch(f"hl.dsp.window.resize({{ x = {int(target_w)}, y = {int(target_h)}, relative = false }})")
    run_dispatch(f"hl.dsp.window.move({{ x = {int(target_x)}, y = {int(target_y)}, relative = false }})")

if __name__ == "__main__":
    main()
