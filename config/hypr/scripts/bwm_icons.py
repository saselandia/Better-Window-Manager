#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Icon theme per BWM skin, like Omarchy's icons.theme (each Omarchy theme picks a Yaru
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
    write_kdeglobals()
    return icons


# ------------------------------------------------------------------------------ KDE / Qt flatpaks
QT6CT_COLORS = HOME / ".config" / "qt6ct" / "colors" / "bwm.conf"
KDEGLOBALS = HOME / ".config" / "kdeglobals"
# Order of the colours in a qt6ct scheme (QPalette roles)
QT_ROLES = ("WindowText", "Button", "Light", "Midlight", "Dark", "Mid", "Text", "BrightText",
            "ButtonText", "Base", "Window", "Shadow", "Highlight", "HighlightedText", "Link",
            "LinkVisited", "AlternateBase", "NoRole", "ToolTipBase", "ToolTipText",
            "PlaceholderText", "Accent")


def _rgb(hex_color: str) -> str:
    h = hex_color.strip().lstrip("#")[-6:]
    return ",".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def write_kdeglobals():
    """kdeglobals with the qt6ct palette (bwm.conf, the one of the active skin/theme): KDE apps and
    Qt flatpaks on the KDE runtime (Kate, ProtonUp-Qt...) read their colours from it, as they do
    not see qt6ct. Only BWM's own kdeglobals is rewritten (marked [BWM]); a real one is kept."""
    try:
        text = QT6CT_COLORS.read_text(encoding="utf-8")
    except Exception:
        return
    rows = {}
    for line in text.splitlines():
        if "=" in line and line.split("=", 1)[0] in ("active_colors", "disabled_colors", "inactive_colors"):
            key, val = line.split("=", 1)
            rows[key] = dict(zip(QT_ROLES, (v.strip() for v in val.split(","))))
    p = rows.get("active_colors")
    if not p:
        return
    if KDEGLOBALS.is_file() and "[BWM]" not in KDEGLOBALS.read_text(encoding="utf-8", errors="replace"):
        backup = KDEGLOBALS.with_name("kdeglobals.bwm-backup")
        if not backup.exists():
            shutil.copy2(KDEGLOBALS, backup)
    d = rows.get("disabled_colors", p)
    neg, neu, pos = "#da4453", "#f67400", "#27ae60"

    def group(name, bg, alt, fg):
        return (f"[Colors:{name}]\nBackgroundNormal={_rgb(bg)}\nBackgroundAlternate={_rgb(alt)}\n"
                f"ForegroundNormal={_rgb(fg)}\nForegroundInactive={_rgb(p['PlaceholderText'])}\n"
                f"ForegroundActive={_rgb(p['Highlight'])}\nForegroundLink={_rgb(p['Link'])}\n"
                f"ForegroundVisited={_rgb(p['LinkVisited'])}\nForegroundNegative={_rgb(neg)}\n"
                f"ForegroundNeutral={_rgb(neu)}\nForegroundPositive={_rgb(pos)}\n"
                f"DecorationFocus={_rgb(p['Highlight'])}\nDecorationHover={_rgb(p['Highlight'])}\n\n")

    out = ("[BWM]\nGenerated=bwm_icons.py write_kdeglobals (paleta de ~/.config/qt6ct/colors/bwm.conf)\n\n"
           "[General]\nColorScheme=BWM\n\n"
           + group("Window", p["Window"], p["AlternateBase"], p["WindowText"])
           + group("View", p["Base"], p["AlternateBase"], p["Text"])
           + group("Button", p["Button"], p["Mid"], p["ButtonText"])
           + group("Selection", p["Highlight"], p["Highlight"], p["HighlightedText"])
           + group("Tooltip", p["ToolTipBase"], p["ToolTipBase"], p["ToolTipText"])
           + group("Complementary", p["Window"], p["AlternateBase"], p["WindowText"])
           + group("Header", p["Window"], p["AlternateBase"], p["WindowText"])
           + f"[Colors:Header][Inactive]\nBackgroundNormal={_rgb(p['Window'])}\nForegroundNormal={_rgb(d['WindowText'])}\n\n"
           + f"[WM]\nactiveBackground={_rgb(p['Window'])}\nactiveForeground={_rgb(p['WindowText'])}\n"
             f"inactiveBackground={_rgb(p['Window'])}\ninactiveForeground={_rgb(p['PlaceholderText'])}\n\n"
           + _kde_fonts()
           + "[KDE]\nwidgetStyle=Fusion\n\n"
           + f"[Icons]\nTheme={_current_icons()}\n")
    KDEGLOBALS.write_text(out, encoding="utf-8")


def _kde_fonts() -> str:
    """The qt6ct fonts (Retro: the system monospace font) as KDE font entries, in [General]."""
    fonts = {}
    try:
        for line in QT6CT_CONF.read_text(encoding="utf-8").splitlines():
            if line.startswith(("general=", "fixed=")):
                key, val = line.split("=", 1)
                family, _, size = val.strip('"').rpartition(",")
                fonts[key] = f"{family},{size or 10},-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
    except Exception:
        pass
    if not fonts:
        return ""
    out = "[General]\n"
    if "general" in fonts:
        out += f"font={fonts['general']}\nmenuFont={fonts['general']}\ntoolBarFont={fonts['general']}\n"
    if "fixed" in fonts:
        out += f"fixed={fonts['fixed']}\n"
    return out + "\n"


def _current_icons() -> str:
    try:
        for line in QT6CT_CONF.read_text(encoding="utf-8").splitlines():
            if line.startswith("icon_theme="):
                return line.split("=", 1)[1]
    except Exception:
        pass
    return "breeze-dark"


FLATPAK_FILESYSTEMS = ("xdg-config/gtk-3.0:ro", "xdg-config/gtk-4.0:ro", "xdg-config/kdeglobals:ro",
                       "xdg-config/qt6ct:ro", "~/.local/share/themes:ro", "~/.local/share/icons:ro",
                       "~/Projects/hyprland-de/config:ro")


def flatpak_overrides():
    """All flatpaks (also ones installed later) see the GTK theme/colours, kdeglobals and the icons,
    and Qt apps on the KDE runtime use the KDE platform theme, which reads kdeglobals. The config
    dirs are links into the repo, which is exposed read-only so the links resolve."""
    if not shutil.which("flatpak"):
        return
    try:
        current = subprocess.run(["flatpak", "override", "--user", "--show"], capture_output=True,
                                 text=True).stdout
    except Exception:
        return
    args = [f"--filesystem={fs}" for fs in FLATPAK_FILESYSTEMS if fs not in current]
    if "QT_QPA_PLATFORMTHEME=kde" not in current:
        args.append("--env=QT_QPA_PLATFORMTHEME=kde")
    if args:
        subprocess.run(["flatpak", "override", "--user", *args], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    # GTK 3 in a flatpak looks for themes in ~/.themes
    themes = HOME / ".themes"
    if not themes.exists() and not themes.is_symlink():
        themes.symlink_to(HOME / ".local" / "share" / "themes")
    if "~/.themes:ro" not in current:
        subprocess.run(["flatpak", "override", "--user", "--filesystem=~/.themes:ro"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def qt_sync():
    """After bwm.conf changes (matugen/Breeze/Omarchy post_hook): kdeglobals and flatpak access."""
    write_kdeglobals()
    flatpak_overrides()


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "qt-sync":
        qt_sync()
    elif len(sys.argv) >= 3 and sys.argv[1] == "apply":
        print(apply(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "",
                    len(sys.argv) > 4 and sys.argv[4] == "light"))
    else:
        print(__doc__)
