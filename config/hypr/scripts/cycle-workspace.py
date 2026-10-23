#!/usr/bin/env python3
"""
Cycle through the open workspaces of the focused monitor (Alt + mouse wheel),
like Hyprland's "e+1"/"e-1" but skipping workspace 99, where toggle-minimize.py
keeps minimized windows (otherwise scrolling would show every minimized window).

Usage: cycle-workspace.py next|prev
"""

import json
import subprocess
import sys

MINIMIZED_WS_ID = 99

def hyprctl_json(*args):
    return json.loads(subprocess.check_output(["hyprctl", "-j", *args]).decode("utf-8"))

def main():
    step = -1 if len(sys.argv) > 1 and sys.argv[1] == "prev" else 1
    try:
        monitor = next(m for m in hyprctl_json("monitors") if m.get("focused"))
        ids = sorted({
            w["id"] for w in hyprctl_json("workspaces")
            if w.get("monitor") == monitor["name"] and w["id"] > 0 and w["id"] != MINIMIZED_WS_ID
        })
    except Exception:
        return
    current = monitor.get("activeWorkspace", {}).get("id")
    if not ids or current not in ids:
        return
    target = ids[(ids.index(current) + step) % len(ids)]
    if target != current:
        subprocess.run(["hyprctl", "dispatch", f"hl.dsp.focus({{ workspace = {target} }})"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    main()
