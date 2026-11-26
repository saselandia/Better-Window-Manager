#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Puente T3: Plasma conserva su fondo por pantalla; BWM publica el principal."""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from bwm_wallpaper import atomic_write, publish

spec = importlib.util.spec_from_file_location("plasma_host", HERE / "plasma-host.py")
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
STATE = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "bwm/plasma-wallpaper.json"
PENDING = CONFIG / "bwm-plasma-host/wallpaper-request.json"


def request(source):
    source = str(Path(source).resolve(strict=True))
    video = Path(source).suffix.lower() in (".mp4", ".m4v", ".mov", ".webm", ".mkv", ".avi")
    still = source
    if video:
        still = subprocess.check_output([str(SCRIPTS / "bwm-video-wallpaper"), "poster", source], text=True, timeout=40).strip()
    return {"source": source, "still": still, "video": video}


def route(source):
    if host.current_skin() != "plasma":
        return 1
    # Skin entry restores the native per-screen layout, never flattens it to the
    # representative path saved for lock/fallback. An explicit offline selection does.
    if os.environ.get("BWM_SKIN_SWITCH") == "1":
        return 1
    req = request(source)
    atomic_write(PENDING, json.dumps(req))
    if not host.native_host_enabled():
        return 1
    if host.host_ctl("wallpaper-set " + json.dumps(req, ensure_ascii=False)) != "ok":
        return 1  # normal set-wallpaper.sh keeps swww/mpvpaper usable without the host
    PENDING.unlink(missing_ok=True)
    publish(req["source"], req["still"], "plasma")
    stop_engines()
    render_boot()
    return 0


def stop_engines():
    # Do not shut down a daemon belonging to another skin during a late export.
    if host.current_skin() != "plasma" or not host.native_host_enabled():
        return
    subprocess.run([str(SCRIPTS / "bwm-video-wallpaper"), "stop"], check=False, timeout=5)
    for name in ("swww", "awww"):
        try:
            subprocess.run([name, "kill"], capture_output=True, timeout=2, check=False)
        except (OSError, subprocess.TimeoutExpired):
            pass


def render_boot():
    subprocess.run([sys.executable, str(SCRIPTS / "bwm_boot.py"), "render"],
                   stdout=subprocess.DEVNULL, check=False, timeout=10)


def export(state):
    if host.current_skin() != "plasma" or not host.native_host_enabled() or state.get("hostPid") != host.ready_pid():
        return 1  # stale child after leaving Breeze or a previous host generation
    screens = state.get("screens", [])
    if not screens:
        return 1
    selected = next((screen for screen in screens if screen.get("primary")), screens[0])
    publish(selected["source"], selected["still"], "plasma")
    atomic_write(STATE, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    # Content-addressed stills avoid Qt's image cache returning an old frame.
    # Keep recent snapshots plus every still referenced by the current screens.
    active = {screen.get("still") for screen in screens}
    snapshots = sorted((CACHE / "bwm/plasma-wallpaper").glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in snapshots[8:]:
        if str(old) not in active:
            old.unlink(missing_ok=True)
    stop_engines()
    render_boot()
    return 0


def resume():
    if host.current_skin() != "plasma" or not host.native_host_enabled() or host.ready_pid() is None:
        return 1
    status = host.host_ctl("wallpaper-status")
    if not status or json.loads(status).get("version") != 1:
        return 1
    if PENDING.is_file():
        req = json.loads(PENDING.read_text())
        if host.host_ctl("wallpaper-set " + json.dumps(req, ensure_ascii=False)) != "ok":
            return 1
        PENDING.unlink(missing_ok=True)
    stop_engines()
    return 0


def fallback():
    if host.current_skin() != "plasma" or (host.native_host_enabled() and host.ready_pid() is not None):
        return 0
    source = (CACHE / "current_wallpaper").read_text().strip()
    req = request(source)
    import shutil
    import bwm_session
    binary = shutil.which("swww") or shutil.which("awww")
    if not binary:
        return 1
    query = subprocess.run([binary, "query"], capture_output=True, timeout=3)
    if query.returncode:
        if not bwm_session.spawn([binary + "-daemon"], allow_fallback=False):
            return 1
        import time
        for _ in range(20):
            if subprocess.run([binary, "query"], capture_output=True, timeout=2).returncode == 0: break
            time.sleep(.1)
    subprocess.run([binary, "img", req["still"], "--transition-type", "none"], check=True, timeout=5)
    subprocess.run([str(SCRIPTS / "bwm-video-wallpaper"), "sync", "plasma"], check=False, timeout=5)
    return 0


def install():
    target = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "plasma/wallpapers/org.bwm.video"
    source = HERE.parent / "share/plasma/wallpapers/org.bwm.video"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() and target.resolve() == source:
        return 0
    if target.exists() or target.is_symlink():
        raise ValueError(f"No se sustituye el paquete existente {target}")
    target.symlink_to(source, target_is_directory=True)
    return 0


def main(args):
    try:
        if args[0] == "route": return route(args[1])
        if args[0] == "export": return export(json.load(sys.stdin))
        if args[0] == "resume": return resume()
        if args[0] == "fallback": return fallback()
        if args[0] == "install": return install()
        return 2
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f"Fondo Plasma: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
