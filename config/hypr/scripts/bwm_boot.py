#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Boot splash (Plymouth) and login screen (SDDM) matching the active BWM theme, like
omarchy-plymouth-set-by-theme: Omarchy's terminal-style themes (MIT, vendored in
config/hypr/omarchy/boot) with the BWM logo, recoloured with the theme's background
and text colours. This only renders them into ~/.local/state/bwm/boot (no root);
install-boot-theme.sh copies them into the system. It runs after every wallpaper and theme
change; when the result differs it rewrites boot/.stamp, which the root service that
`install-boot-theme.sh --auto` sets up watches to update the installed themes.

  bwm_boot.py render        render for the active theme
"""

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

HOME = Path.home()
ASSETS = HOME / ".config" / "hypr" / "omarchy" / "boot"
OUT = HOME / ".local" / "state" / "bwm" / "boot"
SCRIPTS = HOME / ".config" / "hypr" / "scripts"
FAILED = "#f7768e"  # Omarchy's colour for a wrong password


def theme_colors():
    """(background, text) of the active BWM theme."""
    try:
        theme = subprocess.run([sys.executable, str(SCRIPTS / "bwm-theme-manager.py"), "get"],
                               capture_output=True, text=True).stdout.strip()
    except Exception:
        theme = "default"
    if theme == "plasma":
        return "#202326", "#fcfcfc"
    if theme == "retro":
        try:
            import tomllib
            with open(HOME / ".local" / "state" / "bwm" / "omarchy" / "colors.toml", "rb") as f:
                c = tomllib.load(f)
            return c["background"], c["foreground"]
        except Exception:
            pass
    try:
        c = json.loads((HOME / ".local" / "state" / "quickshell" / "user" / "generated" / "colors.json").read_text())
        return c["surface"], c["on_surface"]
    except Exception:
        return "#1a1b26", "#ffffff"


def tint(src: Path, dst: Path, color: str):
    """Every pixel takes `color` and keeps its alpha (magick +level-colors in Omarchy)."""
    im = Image.open(src).convert("RGBA")
    r, g, b = (int(color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    alpha = im.getchannel("A")
    out = Image.new("RGBA", im.size, (r, g, b, 255))
    out.putalpha(alpha)
    out.save(dst)


def render():
    bg, text = theme_colors()
    ply, sddm = OUT / "plymouth", OUT / "sddm"
    for d in (ply, sddm):
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)

    # Plymouth
    r, g, b = (int(bg.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
    script = (ASSETS / "plymouth" / "bwm.script").read_text(encoding="utf-8")
    script = re.sub(r"^Window\.SetBackgroundTopColor.*$", f"Window.SetBackgroundTopColor({r:.3f}, {g:.3f}, {b:.3f});", script, flags=re.M)
    script = re.sub(r"^Window\.SetBackgroundBottomColor.*$", f"Window.SetBackgroundBottomColor({r:.3f}, {g:.3f}, {b:.3f});", script, flags=re.M)
    (ply / "bwm.script").write_text(script, encoding="utf-8")
    conf = (ASSETS / "plymouth" / "bwm.plymouth").read_text(encoding="utf-8")
    conf = re.sub(r"ConsoleLogBackgroundColor=0x[0-9a-fA-F]+", f"ConsoleLogBackgroundColor=0x{bg.lstrip('#')}", conf)
    (ply / "bwm.plymouth").write_text(conf, encoding="utf-8")
    for asset in ("bullet.png", "entry.png", "lock.png", "progress_bar.png"):
        tint(ASSETS / "plymouth" / asset, ply / asset, text)
    shutil.copy(ASSETS / "plymouth" / "progress_box.png", ply / "progress_box.png")
    tint(ASSETS / "logo.png", ply / "logo.png", text)

    # SDDM
    qml = (ASSETS / "sddm" / "Main.qml").read_text(encoding="utf-8")
    qml = qml.replace("#1a1b26", bg).replace("#ffffff", text)
    (sddm / "Main.qml").write_text(qml, encoding="utf-8")
    for f in ("metadata.desktop", "theme.conf"):
        shutil.copy(ASSETS / "sddm" / f, sddm / f)
    for asset in ("bullet.png", "entry.png", "lock.png"):
        shutil.copy(ply / asset, sddm / asset)
    for asset in ("entry", "lock"):
        tint(ASSETS / "plymouth" / f"{asset}.png", sddm / f"{asset}-failed.png", FAILED)
    shutil.copy(ply / "logo.png", sddm / "logo.png")

    # Only a real change wakes the root service (bwm-boot-theme.path)
    digest = hashlib.sha256()
    for f in sorted(p for p in OUT.rglob("*") if p.is_file() and p.name != ".stamp"):
        digest.update(str(f.relative_to(OUT)).encode() + b"\0" + f.read_bytes())
    stamp = OUT / ".stamp"
    if not stamp.is_file() or stamp.read_text().strip() != digest.hexdigest():
        stamp.write_text(digest.hexdigest() + "\n")
    return bg, text


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "render":
        print("Tema de arranque generado con fondo %s y texto %s en %s" % (*render(), OUT))
    else:
        print(__doc__)
