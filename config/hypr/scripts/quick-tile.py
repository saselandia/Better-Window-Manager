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

    # 5. Snap to halves / quarters with 0 gaps touching edges & bottom bar flush
    half_w = usable_w // 2
    half_h = usable_h // 2
    rem_w  = usable_w - half_w
    rem_h  = usable_h - half_h

    cur_at = target_win.get("at", [0, 0])
    cur_sz = target_win.get("size", [0, 0])
    cur_x, cur_y = cur_at[0], cur_at[1]
    cur_w, cur_h = cur_sz[0], cur_sz[1]

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
