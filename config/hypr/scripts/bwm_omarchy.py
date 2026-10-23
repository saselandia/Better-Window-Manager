#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BWM Retro theme: Omarchy-style app theming that follows the wallpaper.

Omarchy (https://github.com/basecamp/omarchy, MIT) describes a theme with a
colors.toml (16 ANSI colours plus background/foreground/accent variants) and
renders per-app templates from it; omarchy-theme-hook does the same for apps
Omarchy itself does not cover (Spotify through Spicetify, GTK, Discord...).

Here the colors.toml is generated from the wallpaper palette instead of being
hand-written, and every app gets:
  * kitty / btop      -> Omarchy's own templates (config/hypr/omarchy/themed)
  * GTK 3/4, Vesktop, swaync, Firefox, Pywalfox
                      -> our matugen templates filled with the Omarchy palette,
                         plus a TUI overlay (monospace, square, flat, thin accent
                         borders) from config/hypr/omarchy/overlays
  * Spotify           -> "BWM-Omarchy" Spicetify theme (terminal-style user.css)
  * VSCodium          -> workbench.colorCustomizations, applied live

restore_non_retro() undoes what other themes do not regenerate themselves
(Spicetify theme, btop theme name, VSCodium colours) when leaving Retro.
"""

import colorsys
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

HOME = Path.home()
CONFIG_DIR = HOME / ".config"
ASSETS_DIR = CONFIG_DIR / "hypr" / "omarchy"
STATE_DIR = HOME / ".local" / "state" / "bwm" / "omarchy"
COLORS_TOML = STATE_DIR / "colors.toml"

KITTY_COLORS_CONF = CONFIG_DIR / "kitty" / "kitty-colors.conf"
BTOP_CONF = CONFIG_DIR / "btop" / "btop.conf"
BTOP_THEME = CONFIG_DIR / "btop" / "themes" / "omarchy.theme"
SPICETIFY_THEME_DIR = CONFIG_DIR / "spicetify" / "Themes" / "BWM-Omarchy"
VSCODIUM_SETTINGS = CONFIG_DIR / "VSCodium" / "User" / "settings.json"
VSCODIUM_MARKER = "bwm.retroColorCustomizations"

# In Retro every matugen template is rendered here with the Omarchy palette (matugen itself
# does not run), and these get a TUI overlay appended
MATUGEN_OVERLAYS = {
    "gtk3": "gtk.css",
    "gtk4": "gtk.css",
    "vesktop": "vesktop.css",
    "vesktop_quickcss": "vesktop.css",
    "swaync": "swaync.css",
    "firefox": "firefox.css",
}
# Templates handled by their own Omarchy step instead (kitty template, BWM-Omarchy Spicetify theme)
MATUGEN_SKIPPED = {"kitty", "spicetify"}

# Stateless GTK 3 windows reopened when the GTK palette changes (GTK 3 reads gtk.css at startup)
GTK_RELAUNCH_APPS = ("blueman-manager", "pavucontrol", "nm-connection-editor")


# ------------------------------------------------------------------------------
# Palette
# ------------------------------------------------------------------------------
def _hex(h, l, s):
    r, g, b = colorsys.hls_to_rgb(h % 1.0, max(0.0, min(1.0, l)), max(0.0, min(1.0, s)))
    return f"#{int(r * 255 + 0.5):02x}{int(g * 255 + 0.5):02x}{int(b * 255 + 0.5):02x}"

def _hls(hex_color):
    v = hex_color.lstrip("#")
    return colorsys.rgb_to_hls(int(v[0:2], 16) / 255, int(v[2:4], 16) / 255, int(v[4:6], 16) / 255)

def _toward(hue, target, amount):
    """Rotate `hue` towards `target` by `amount` (0..1) along the shortest arc."""
    d = ((target - hue + 0.5) % 1.0) - 0.5
    return (hue + d * amount) % 1.0

def build_colors(palette: dict) -> dict:
    """Omarchy colors.toml keys from the wallpaper palette of extract_vivid_palette()."""
    ah, al, as_ = _hls(palette["accent"])
    # Omarchy accents are light enough to be read as text on the dark background
    accent = _hex(ah, max(al, 0.66), min(max(as_, 0.65), 0.92))

    # Dark, slightly tinted backgrounds/foregrounds, like Omarchy's hand-made themes
    c = {
        "mode": "dark",
        "accent": accent,
        "background": _hex(ah, 0.085, 0.28),
        "dark_background": _hex(ah, 0.065, 0.28),
        "darker_background": _hex(ah, 0.045, 0.28),
        "lighter_background": _hex(ah, 0.13, 0.24),
        "selection": _hex(ah, 0.19, 0.32),
        "muted": _hex(ah, 0.34, 0.16),
        "foreground": _hex(ah, 0.82, 0.18),
        "dark_foreground": _hex(ah, 0.52, 0.14),
        "light_foreground": _hex(ah, 0.87, 0.16),
        "bright_foreground": _hex(ah, 0.94, 0.20),
    }
    # ANSI colours harmonised with the wallpaper: classic hues pulled 6% towards the accent
    hues = {"red": 0.985, "orange": 0.07, "yellow": 0.12, "green": 0.31, "cyan": 0.50,
            "blue": 0.60, "magenta": 0.81, "brown": 0.06}
    for name, hue in hues.items():
        h = _toward(hue, ah, 0.06)
        if name == "brown":
            c[name] = _hex(h, 0.34, 0.40)
            continue
        c[name] = _hex(h, 0.66, 0.72)
        c["bright_" + name] = _hex(h, 0.75, 0.85)
    c["selection_background"] = c["selection"]
    c["selection_foreground"] = c["bright_foreground"]
    c["cursor"] = accent
    return c

def write_colors_toml(colors: dict):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    lines = ["# Omarchy-format palette generated from the wallpaper by BWM (bwm_omarchy.py)"]
    lines += [f'{k} = "{v}"' for k, v in colors.items()]
    _write_if_changed(COLORS_TOML, "\n".join(lines) + "\n")

def m3_roles(c: dict) -> dict:
    """Material 3 roles used by the matugen templates, mapped onto the Omarchy palette."""
    return {
        "primary": c["accent"], "on_primary": c["background"],
        "primary_container": c["selection"], "on_primary_container": c["bright_foreground"],
        "inverse_primary": c["accent"], "surface_tint": c["accent"],
        "secondary": c["cyan"], "on_secondary": c["background"],
        "secondary_container": c["lighter_background"], "on_secondary_container": c["foreground"],
        "tertiary": c["magenta"], "on_tertiary": c["background"],
        "tertiary_container": c["lighter_background"], "on_tertiary_container": c["foreground"],
        "background": c["background"], "on_background": c["foreground"],
        "surface": c["background"], "surface_dim": c["dark_background"], "surface_bright": c["lighter_background"],
        "surface_container_lowest": c["darker_background"], "surface_container_low": c["dark_background"],
        "surface_container": c["background"], "surface_container_high": c["lighter_background"],
        "surface_container_highest": c["selection"],
        "on_surface": c["foreground"], "surface_variant": c["lighter_background"],
        "on_surface_variant": c["dark_foreground"],
        "inverse_surface": c["foreground"], "inverse_on_surface": c["background"],
        "outline": c["muted"], "outline_variant": c["selection"], "shadow": "#000000", "scrim": "#000000",
        "error": c["red"], "on_error": c["background"], "error_container": c["brown"], "on_error_container": c["bright_foreground"],
        "primary_fixed": c["accent"], "primary_fixed_dim": c["accent"], "on_primary_fixed": c["background"],
        "on_primary_fixed_variant": c["background"],
        "secondary_fixed": c["cyan"], "secondary_fixed_dim": c["cyan"], "on_secondary_fixed": c["background"],
        "on_secondary_fixed_variant": c["background"],
        "tertiary_fixed": c["magenta"], "tertiary_fixed_dim": c["magenta"], "on_tertiary_fixed": c["background"],
        "on_tertiary_fixed_variant": c["background"],
    }


# ------------------------------------------------------------------------------
# Rendering helpers
# ------------------------------------------------------------------------------
def _write_if_changed(path: Path, content: str) -> bool:
    try:
        if path.is_file() and path.read_text(encoding="utf-8") == content:
            return False
    except Exception:
        pass
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".bwm-tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)
    return True

def render_omarchy(template: str, colors: dict) -> str:
    """Omarchy template syntax: {{ key }}, {{ key_strip }} (no #), {{ key_rgb }} (r,g,b)."""
    def fill(m):
        key = m.group(1).strip()
        for suffix, fmt in (("_strip", lambda v: v.lstrip("#")),
                            ("_rgb", lambda v: ",".join(str(int(v.lstrip("#")[i:i + 2], 16)) for i in (0, 2, 4)))):
            if key.endswith(suffix) and key[: -len(suffix)] in colors:
                return fmt(colors[key[: -len(suffix)]])
        return colors.get(key, m.group(0))
    return re.sub(r"\{\{([^}]*)\}\}", fill, template)

def render_matugen(template: str, roles: dict, wallpaper: str) -> str:
    def fill(m):
        expr = m.group(1).strip()
        if expr == "image":
            return wallpaper
        mm = re.fullmatch(r"colors\.([a-z_]+)\.(?:default|dark|light)\.(hex|hex_stripped)", expr)
        if not mm or mm.group(1) not in roles:
            return m.group(0)
        value = roles[mm.group(1)]
        return value.lstrip("#") if mm.group(2) == "hex_stripped" else value
    return re.sub(r"\{\{([^}]*)\}\}", fill, template)

def _detached(cmd: str):
    subprocess.Popen(["sh", "-c", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     start_new_session=True)

def _running(name: str) -> bool:
    # pgrep -x only sees the first 15 characters of a process name (nm-connection-editor)
    return subprocess.run(["pgrep", "-f", f"(^|/){name}( |$)"], stdout=subprocess.DEVNULL).returncode == 0


# ------------------------------------------------------------------------------
# Apps
# ------------------------------------------------------------------------------
def apply_kitty(colors: dict):
    tpl = (ASSETS_DIR / "themed" / "kitty.conf.tpl").read_text(encoding="utf-8")
    content = render_omarchy(tpl, colors) + f"\ninactive_border_color {colors['muted']}\nurl_color {colors['accent']}\n"
    if _write_if_changed(KITTY_COLORS_CONF, content):
        subprocess.run(["pkill", "-SIGUSR1", "-x", "kitty"], check=False)

def set_btop_theme(name: str):
    if not BTOP_CONF.is_file():
        return
    text = BTOP_CONF.read_text(encoding="utf-8")
    new = re.sub(r'^color_theme\s*=.*$', f'color_theme = "{name}"', text, flags=re.M)
    if new == text and "color_theme" not in text:
        new = text + f'color_theme = "{name}"\n'
    _write_if_changed(BTOP_CONF, new)

def apply_btop(colors: dict):
    tpl = (ASSETS_DIR / "themed" / "btop.theme.tpl").read_text(encoding="utf-8")
    _write_if_changed(BTOP_THEME, render_omarchy(tpl, colors))
    set_btop_theme("omarchy")

def apply_matugen_apps(colors: dict, wallpaper: str) -> set:
    """Our matugen templates filled with the Omarchy palette + the TUI overlays. Returns changed names."""
    try:
        with open(CONFIG_DIR / "matugen" / "config.toml", "rb") as f:
            templates = tomllib.load(f).get("templates", {})
    except Exception as e:
        print(f"[Warning] No se pudo leer matugen/config.toml: {e}", file=sys.stderr)
        return set()

    roles = m3_roles(colors)
    changed = set()
    hooks = []
    for name, tpl in templates.items():
        if name in MATUGEN_SKIPPED:
            continue
        overlay = MATUGEN_OVERLAYS.get(name)
        src = Path(os.path.expanduser(tpl.get("input_path", "")))
        dst = Path(os.path.expanduser(tpl.get("output_path", "")))
        if not src.is_file():
            continue
        content = render_matugen(src.read_text(encoding="utf-8"), roles, wallpaper)
        if overlay:
            content += (ASSETS_DIR / "overlays" / overlay).read_text(encoding="utf-8")
        try:
            if _write_if_changed(dst, content):
                changed.add(name)
                if tpl.get("post_hook"):
                    hooks.append(tpl["post_hook"])
        except Exception as e:
            print(f"[Warning] Error escribiendo {dst}: {e}", file=sys.stderr)
    # The same reload hooks matugen would run (Quickshell, Pywalfox, Nautilus, swaync, Hyprland...)
    for hook in hooks:
        _detached(hook)
    return changed

def apply_spotify(colors: dict):
    """BWM-Omarchy Spicetify theme; only re-applied (Spotify restart) when something changed."""
    if not subprocess.run(["sh", "-c", "command -v spicetify"], stdout=subprocess.DEVNULL).returncode == 0:
        return
    s = lambda k: colors[k].lstrip("#")
    color_ini = f"""[Base]
text               = {s('foreground')}
subtext            = {s('dark_foreground')}
nav-active-text    = {s('accent')}
main               = {s('background')}
main-elevated      = {s('lighter_background')}
sidebar            = {s('background')}
player             = {s('background')}
card               = {s('lighter_background')}
shadow             = {s('darker_background')}
selected-row       = {s('selection')}
button             = {s('accent')}
button-active      = {s('bright_foreground')}
button-secondary   = {s('foreground')}
button-disabled    = {s('muted')}
tab-active         = {s('selection')}
notification       = {s('accent')}
notification-error = {s('red')}
misc               = {s('accent')}
highlight          = {s('selection')}
highlight-elevated = {s('lighter_background')}
"""
    changed = _write_if_changed(SPICETIFY_THEME_DIR / "color.ini", color_ini)
    changed |= _write_if_changed(SPICETIFY_THEME_DIR / "user.css",
                                 (ASSETS_DIR / "spicetify" / "user.css").read_text(encoding="utf-8"))
    changed |= _set_spicetify_theme("BWM-Omarchy", "Base")
    if changed:
        _detached("~/.config/hypr/scripts/reload-spotify.sh")

def _spicetify_get(key: str) -> str:
    # Read the ini directly: "spicetify config a b" would *set* a = b
    try:
        text = (CONFIG_DIR / "spicetify" / "config-xpui.ini").read_text(encoding="utf-8")
    except Exception:
        return ""
    m = re.search(rf"^{re.escape(key)}\s*=\s*(.*)$", text, flags=re.M)
    return m.group(1).strip() if m else ""

def _set_spicetify_theme(theme: str, scheme: str) -> bool:
    if (_spicetify_get("current_theme"), _spicetify_get("color_scheme")) == (theme, scheme):
        return False
    subprocess.run(["spicetify", "-q", "config", "current_theme", theme, "color_scheme", scheme],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True

def _vscodium_colors(c: dict) -> dict:
    return {
        "editor.background": c["background"], "editor.foreground": c["foreground"],
        "editor.lineHighlightBackground": c["lighter_background"],
        "editor.selectionBackground": c["selection"], "editorCursor.foreground": c["accent"],
        "editorLineNumber.foreground": c["muted"], "editorLineNumber.activeForeground": c["accent"],
        "sideBar.background": c["dark_background"], "sideBar.foreground": c["foreground"],
        "sideBarSectionHeader.background": c["background"], "sideBar.border": c["muted"],
        "activityBar.background": c["darker_background"], "activityBar.foreground": c["accent"],
        "activityBar.inactiveForeground": c["dark_foreground"], "activityBarBadge.background": c["accent"],
        "activityBarBadge.foreground": c["background"],
        "titleBar.activeBackground": c["darker_background"], "titleBar.activeForeground": c["foreground"],
        "titleBar.inactiveBackground": c["darker_background"],
        "statusBar.background": c["accent"], "statusBar.foreground": c["background"],
        "statusBar.noFolderBackground": c["accent"], "statusBar.debuggingBackground": c["magenta"],
        "tab.activeBackground": c["background"], "tab.inactiveBackground": c["dark_background"],
        "tab.activeForeground": c["bright_foreground"], "tab.inactiveForeground": c["dark_foreground"],
        "tab.activeBorderTop": c["accent"], "tab.border": c["darker_background"],
        "editorGroupHeader.tabsBackground": c["dark_background"],
        "panel.background": c["dark_background"], "panel.border": c["muted"],
        "terminal.background": c["background"], "terminal.foreground": c["foreground"],
        "terminalCursor.foreground": c["accent"],
        "terminal.ansiBlack": c["background"], "terminal.ansiRed": c["red"], "terminal.ansiGreen": c["green"],
        "terminal.ansiYellow": c["yellow"], "terminal.ansiBlue": c["blue"], "terminal.ansiMagenta": c["magenta"],
        "terminal.ansiCyan": c["cyan"], "terminal.ansiWhite": c["foreground"],
        "terminal.ansiBrightBlack": c["muted"], "terminal.ansiBrightRed": c["bright_red"],
        "terminal.ansiBrightGreen": c["bright_green"], "terminal.ansiBrightYellow": c["bright_yellow"],
        "terminal.ansiBrightBlue": c["bright_blue"], "terminal.ansiBrightMagenta": c["bright_magenta"],
        "terminal.ansiBrightCyan": c["bright_cyan"], "terminal.ansiBrightWhite": c["bright_foreground"],
        "input.background": c["darker_background"], "input.border": c["muted"], "focusBorder": c["accent"],
        "button.background": c["accent"], "button.foreground": c["background"],
        "list.activeSelectionBackground": c["selection"], "list.hoverBackground": c["lighter_background"],
        "list.focusOutline": c["accent"], "badge.background": c["accent"], "badge.foreground": c["background"],
        "editorWidget.background": c["dark_background"], "editorWidget.border": c["accent"],
        "dropdown.background": c["darker_background"], "menu.background": c["dark_background"],
        "menu.selectionBackground": c["selection"], "quickInput.background": c["dark_background"],
    }

def _load_vscodium_settings():
    if not VSCODIUM_SETTINGS.is_file():
        return None
    try:
        return json.loads(VSCODIUM_SETTINGS.read_text(encoding="utf-8"))
    except Exception:
        # JSON with comments: leave the user's file alone rather than rewrite it
        return None

def apply_vscodium(colors: dict):
    settings = _load_vscodium_settings()
    if settings is None:
        return
    if VSCODIUM_MARKER not in settings:
        # Remember the user's own customizations to give them back when leaving Retro
        settings[VSCODIUM_MARKER] = {"previous": settings.get("workbench.colorCustomizations")}
    settings["workbench.colorCustomizations"] = _vscodium_colors(colors)
    _write_if_changed(VSCODIUM_SETTINGS, json.dumps(settings, indent=4, ensure_ascii=False) + "\n")

def restore_vscodium():
    settings = _load_vscodium_settings()
    if not settings or VSCODIUM_MARKER not in settings:
        return
    previous = settings.pop(VSCODIUM_MARKER).get("previous")
    if previous is None:
        settings.pop("workbench.colorCustomizations", None)
    else:
        settings["workbench.colorCustomizations"] = previous
    _write_if_changed(VSCODIUM_SETTINGS, json.dumps(settings, indent=4, ensure_ascii=False) + "\n")


# ------------------------------------------------------------------------------
# Entry points
# ------------------------------------------------------------------------------
def apply_retro_apps(palette: dict, wallpaper: str = ""):
    """Retro theme: Omarchy-style themes for every app, from the wallpaper palette."""
    colors = build_colors(palette)
    write_colors_toml(colors)

    for step in (apply_kitty, apply_btop, apply_vscodium, apply_spotify):
        try:
            step(colors)
        except Exception as e:
            print(f"[Warning] {step.__name__}: {e}", file=sys.stderr)

    changed = apply_matugen_apps(colors, wallpaper)

    if "gtk3" in changed:
        for app in GTK_RELAUNCH_APPS:
            if _running(app):
                subprocess.run(["pkill", "-f", f"(^|/){app}( |$)"], check=False)
                _detached(f"sleep 0.5; exec {app}")
    return colors

def restore_non_retro():
    """Leaving Retro: give back what the other themes do not regenerate by themselves."""
    set_btop_theme("matugen")
    restore_vscodium()
    try:
        if _set_spicetify_theme("MaterialYou", "MaterialYou"):
            _detached("~/.config/hypr/scripts/reload-spotify.sh")
    except Exception:
        pass


if __name__ == "__main__":
    print(json.dumps(build_colors({"accent": sys.argv[1] if len(sys.argv) > 1 else "#38bdf8"}), indent=2))
