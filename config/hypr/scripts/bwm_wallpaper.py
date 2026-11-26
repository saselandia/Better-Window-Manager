#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Publicación común del fondo: cachés y perfiles, sin pintar ni recolorear."""
import fcntl
import json
import os
import re
from pathlib import Path
import sys
import tempfile


def native_plasma_ready():
    """La marca sola no acredita un proceso vivo (ni la skin activa)."""
    config = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
    try:
        data = json.loads((config / "illogical-impulse/config.json").read_text())
        if data.get("appearance", {}).get("bwmTheme") != "plasma": return False
        if data.get("bar", {}).get("plasma", {}).get("nativeHost") is False: return False
        pid = int((runtime / "bwm-plasma-host.ready").read_text())
        process = Path(f"/proc/{pid}")
        if pid <= 0 or process.stat().st_uid != os.getuid(): return False
        argv = (process / "cmdline").read_bytes().rstrip(b"\0").split(b"\0")
        return Path(os.fsdecode(argv[0])).name == "bwm-plasma-host" and argv[1:] == [b"--session"]
    except (OSError, ValueError, IndexError):
        return False


def atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def publish(source, still, skin):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", skin):
        raise ValueError("Identificador de skin inválido")
    if not Path(source).is_file() or not Path(still).is_file():
        raise ValueError("El fondo y su imagen fija deben existir")
    cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    config = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    cache.mkdir(parents=True, exist_ok=True)
    with (cache / "bwm-wallpaper.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        atomic_write(cache / "current_wallpaper", source + "\n")
        atomic_write(cache / f"current_wallpaper_{skin}", source + "\n")
        for name in ("config.json", f"config-{skin}.json"):
            path = config / "illogical-impulse" / name
            if not path.is_file():
                continue
            data = json.loads(path.read_text())
            data.setdefault("background", {}).update(wallpaperPath=source, thumbnailPath=still)
            atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    publish(*sys.argv[1:])
