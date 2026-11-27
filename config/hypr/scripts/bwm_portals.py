#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Selecciona interfaces del portal declaradas por la skin, sólo para su servicio.

No cambia XDG_CURRENT_DESKTOP de apps ni el portals.conf del usuario. Una copia
efímera conserva las demás preferencias y un drop-in de systemd limita su XDG_CONFIG_HOME.
"""
import configparser
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import bwm_skins
from bwm_wallpaper import atomic_write

CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
RUNTIME = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
PROFILE = RUNTIME / "bwm-portals"
DROPIN = RUNTIME / "systemd/user/xdg-desktop-portal.service.d/50-bwm.conf"

def preferred_config():
    desktops = [name.lower() for name in os.environ.get("XDG_CURRENT_DESKTOP", "Hyprland").split(":") if name]
    roots = [CONFIG, *map(Path, os.environ.get("XDG_CONFIG_DIRS", "/etc/xdg").split(":")),
             Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")),
             *map(Path, os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":"))]
    for root in roots:
        for filename in [*(name + "-portals.conf" for name in desktops), "portals.conf"]:
            path = root / "xdg-desktop-portal" / filename
            if path.is_file():
                return path
    return None

def apply(skin_id, restart=True):
    overrides = bwm_skins.skin(skin_id).get("portals", {})
    config = configparser.ConfigParser(interpolation=None)
    config.optionxform = str
    source = preferred_config()
    if source:
        config.read(source)
    if not config.has_section("preferred"):
        config.add_section("preferred")
        config.set("preferred", "default", "hyprland;gtk;")
    # Respect a deliberate FileChooser override. BWM's distributed baseline is gtk.
    chooser = config.get("preferred", "org.freedesktop.impl.portal.FileChooser", fallback="gtk;")
    if chooser.strip("; ") != "gtk":
        overrides = {}
    changed = False
    if overrides:
        for interface, backends in overrides.items():
            if not interface.isidentifier() or not all(b.replace("-", "").isalnum() for b in backends):
                raise ValueError("Invalid portal interface/backend")
            config.set("preferred", "org.freedesktop.impl.portal." + interface, ";".join(backends) + ";")
        rendered = io.StringIO()
        config.write(rendered, space_around_delimiters=False)
        target = PROFILE / "xdg-desktop-portal/portals.conf"
        dropin = "# BWM: scoped portal configuration; removed outside this skin.\n[Service]\nEnvironment=" + json.dumps("XDG_CONFIG_HOME=" + str(PROFILE)) + "\n"
        if not target.exists() or target.read_text() != rendered.getvalue() or not DROPIN.exists() or DROPIN.read_text() != dropin:
            PROFILE.mkdir(parents=True, exist_ok=True, mode=0o700)
            atomic_write(target, rendered.getvalue())
            atomic_write(DROPIN, dropin)
            changed = True
    elif DROPIN.exists() and DROPIN.read_text().startswith("# BWM:"):
        DROPIN.unlink()
        changed = True
    if changed and restart:
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True, timeout=5)
        subprocess.run(["systemctl", "--user", "try-restart", "xdg-desktop-portal.service"], check=True, timeout=15)
    return {"changed": changed, "skin": skin_id, "source": str(source) if source else None, "overrides": overrides}

if __name__ == "__main__":
    try:
        print(json.dumps(apply(sys.argv[1])))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"BWM portals: {error}", file=sys.stderr)
        raise SystemExit(1)
