#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Icon theme per BWM theme, like Omarchy's icons.theme (each Omarchy theme picks a Yaru
colour). Yaru is not packaged for Gentoo, so Retro uses Papirus-Dark (Papirus-Light with a
light Omarchy theme) with the folder colour closest to the wallpaper accent (what papirus-folders does: a small user theme,
BWM-Papirus, that points the folder icons at one of Papirus' colour variants).

  Default -> Adwaita (as before)
  Plasma  -> breeze-dark
  Retro   -> BWM-Papirus (Papirus-Dark/-Light + accent folders) if x11-themes/papirus-icon-theme
             is installed, Adwaita otherwise

It also keeps qt6ct (Qt apps) on the same icon theme and on the palette that the colour
templates render into ~/.config/qt6ct/colors/bwm.conf.

  bwm_icons.py apply <default|plasma|retro> [accent] [light]
"""

import colorsys
import os
import shutil
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
USER_ICONS = HOME / ".local" / "share" / "icons"
VARIANT = "BWM-Papirus"
QT6CT_CONF = HOME / ".config" / "qt6ct" / "qt6ct.conf"
_rebuilt = False  # BWM-Papirus rewritten in this run

# Papirus folder colours (papirus-folders names) with their representative colour
PAPIRUS_FOLDERS = {
    "blue": "#5294e2", "bluegrey": "#607d8b", "brown": "#ae8e6c", "cyan": "#00bcd4",
    "deeporange": "#ff5722", "green": "#87b158", "grey": "#8e8e8e", "indigo": "#5c6bc0",
    "magenta": "#ca71df", "orange": "#ee923a", "pink": "#f06292", "red": "#e25252",
    "teal": "#16a085", "violet": "#7e57c2", "yellow": "#f9bd30",
}


def _papirus_root():
    for base in (Path("/usr/share/icons"), USER_ICONS):
        if (base / "Papirus").is_dir():
            return base / "Papirus"
    return None


def closest_folder_color(accent: str) -> str:
    def hls(h):
        h = h.lstrip("#")
        return colorsys.rgb_to_hls(*(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)))
    ah, al, as_ = hls(accent)
    if as_ < 0.15:
        return "grey"

    def dist(c):
        h, l, s = hls(c)
        dh = min(abs(h - ah), 1 - abs(h - ah))
        return dh * 10 + abs(s - as_) * 1.0 + abs(l - al) * 0.3
    return min(PAPIRUS_FOLDERS, key=lambda name: dist(PAPIRUS_FOLDERS[name]))


def build_papirus_variant(color: str, light: bool = False):
    """User icon theme inheriting Papirus-Dark (Papirus-Light for light themes, dark symbolic
    icons) whose folder icons are Papirus' `color` ones."""
    papirus = _papirus_root()
    if not papirus:
        return None
    base = "Papirus-Light" if light else "Papirus-Dark"
    dest = USER_ICONS / VARIANT
    stamp = dest / ".bwm-folder-color"
    if stamp.is_file() and stamp.read_text().strip() == f"{color} {base}":
        return VARIANT
    global _rebuilt
    _rebuilt = True
    shutil.rmtree(dest, ignore_errors=True)
    dirs = []
    for size_dir in sorted(papirus.iterdir()):
        places = size_dir / "places"
        if not places.is_dir():
            continue
        links = []
        for icon in places.iterdir():
            name = icon.name
            if name.startswith(f"folder-{color}"):
                links.append((name.replace(f"folder-{color}", "folder", 1), icon))
            elif name.startswith(f"user-{color}-"):
                links.append((name.replace(f"user-{color}-", "user-", 1), icon))
        if not links:
            continue
        out = dest / size_dir.name / "places"
        out.mkdir(parents=True, exist_ok=True)
        for new_name, target in links:
            (out / new_name).symlink_to(target.resolve())
        dirs.append(f"{size_dir.name}/places")
    if not dirs:
        return None
    fallback = "breeze" if light else "breeze-dark"
    lines = ["[Icon Theme]", f"Name={VARIANT}", f"Comment={base} with {color} folders (BWM Retro)",
             f"Inherits={base},{fallback},Adwaita,hicolor", f"Directories={','.join(dirs)}", ""]
    for d in dirs:
        size = d.split("x")[0]
        scale = "@2" in d
        lines += [f"[{d}]", "Context=Places", f"Size={size.split('@')[0]}", "Type=Fixed"]
        if scale:
            lines.append("Scale=2")
        lines.append("")
    (dest / "index.theme").write_text("\n".join(lines), encoding="utf-8")
    stamp.write_text(f"{color} {base}")
    subprocess.run(["gtk-update-icon-cache", "-f", "-q", str(dest)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return VARIANT


def icon_theme_for(theme: str, accent: str = "", light: bool = False) -> str:
    if theme == "plasma":
        return "breeze-dark"
    if theme == "retro":
        return build_papirus_variant(closest_folder_color(accent or "#7aa2f7"), light) or "Adwaita"
    return "Adwaita"


def write_qt6ct(icon_theme: str, mono_font: str = ""):
    """qt6ct: Fusion with the theme palette (colors/bwm.conf) and the same icons. With
    `mono_font` (Retro) the whole UI uses the system monospace font, like the GTK TUI overlay."""
    QT6CT_CONF.parent.mkdir(parents=True, exist_ok=True)
    text = (
        "[Appearance]\n"
        f"color_scheme_path={HOME}/.config/qt6ct/colors/bwm.conf\n"
        "custom_palette=true\n"
        f"icon_theme={icon_theme}\n"
        "standard_dialogs=xdgdesktopportal\n"
        "style=Fusion\n")
    if mono_font:
        text += f'\n[Fonts]\nfixed="{mono_font},10"\ngeneral="{mono_font},10"\n'
    QT6CT_CONF.write_text(text, encoding="utf-8")


def apply(theme: str, accent: str = "", light: bool = False):
    icons = icon_theme_for(theme, accent, light)
    if _rebuilt:
        # Same theme name, new contents: running apps only reload icons when the name changes
        subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", "Adwaita"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", icons],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    mono = ""
    if theme == "retro":
        try:
            import bwm_omarchy
            mono = bwm_omarchy.system_font()
        except Exception:
            mono = "JetBrainsMono Nerd Font"
    write_qt6ct(icons, mono)
    return icons


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "apply":
        print(apply(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "",
                    len(sys.argv) > 4 and sys.argv[4] == "light"))
    else:
        print(__doc__)
