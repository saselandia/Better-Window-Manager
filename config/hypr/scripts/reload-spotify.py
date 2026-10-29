#!/usr/bin/env python3
"""Re-apply Spicetify and relaunch Spotify, putting its window back where it was.

Spotify only picks up a new Spicetify theme when it restarts, and a restarted window
opens on whichever workspace is active. The workspace it was on (including the special
Magic workspace, Alt+S), its monitor and, for a floating window, its geometry are saved
before closing it and restored when the new window shows up.
"""

import json
import subprocess
import sys
import time

CLASS = "spotify"


def hypr_json(cmd: str):
    try:
        return json.loads(subprocess.check_output(["hyprctl", cmd, "-j"], stderr=subprocess.DEVNULL))
    except Exception:
        return []


def spotify_windows():
    return [c for c in hypr_json("clients") if (c.get("class") or "").lower() == CLASS and c.get("mapped", True)]


def lua(code: str):
    subprocess.run(["hyprctl", "dispatch", code], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def running() -> bool:
    return subprocess.run(["pgrep", "-f", "com.spotify.Client"], stdout=subprocess.DEVNULL).returncode == 0 \
        or subprocess.run(["pgrep", "-x", "spotify"], stdout=subprocess.DEVNULL).returncode == 0


def snapshot(win: dict) -> dict:
    ws = win.get("workspace", {})
    return {
        "workspace": ws.get("name") or str(ws.get("id", 1)),
        "special": str(ws.get("name", "")).startswith("special:"),
        "floating": bool(win.get("floating")),
        "at": win.get("at"),
        "size": win.get("size"),
        "pinned": bool(win.get("pinned")),
    }


def restore(window: dict, ws: dict):
    # bwm_windows.restored_box: its old geometry if it floated, or its tiled place as a floating
    # window if it comes back floating (KDE Plasma)
    import bwm_windows
    box = bwm_windows.restored_box(ws, window) if ws.get("at") and ws.get("size") else None
    bwm_windows.dispatch([bwm_windows.place_lua(window["address"], workspace=ws["workspace"], box=box)])


def main():
    import bwm_transition
    if bwm_transition.switching():
        return  # Spicetify puede cerrar Spotify; conservar reproducción durante el cambio de skin.
    if not running():
        # Not running: just regenerate the theme in the background
        subprocess.Popen(["sh", "-c", "spicetify -n apply >/dev/null 2>&1 || true"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        return

    before = spotify_windows()
    saved = snapshot(before[0]) if before else None
    # Hyprland can reuse a window address for the new window, so tell windows apart by PID
    old_pids = {w["pid"] for w in before}

    if subprocess.run("spicetify -n apply >/dev/null 2>&1", shell=True).returncode != 0:
        subprocess.run("spicetify -n refresh >/dev/null 2>&1", shell=True)
    subprocess.run(["pkill", "-9", "-f", "com.spotify.Client"], stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "-9", "-x", "spotify"], stderr=subprocess.DEVNULL)
    time.sleep(0.5)
    # Lua config: the old "hyprctl dispatch exec <cmd>" syntax no longer works
    lua('hl.dsp.exec_cmd("flatpak run com.spotify.Client")')

    if not saved:
        return
    # The new window can take a while to map; move it as soon as it appears and check again
    # a little later, since Spotify may reopen or resize its window while it loads
    placed = set()
    deadline = time.time() + 40
    while time.time() < deadline:
        time.sleep(0.4)
        for w in spotify_windows():
            if w["pid"] in old_pids or w["address"] in placed:
                continue
            restore(w, saved)
            placed.add(w["address"])
            deadline = min(deadline, time.time() + 6)  # a few more seconds for a second window
    for w in spotify_windows():
        if w["address"] in placed:
            time.sleep(1.5)
            restore(w, saved)


if __name__ == "__main__":
    sys.exit(main())
