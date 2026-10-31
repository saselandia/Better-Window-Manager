#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BWM Retro skin: Omarchy-style app theming that follows the wallpaper.

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
import shutil
import subprocess
import sys
import tomllib
import bwm_transition

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bwm_omarchy_apps  # noqa: E402
from collections import defaultdict
from pathlib import Path
from PIL import Image

HOME = Path.home()
CONFIG_DIR = HOME / ".config"
ASSETS_DIR = CONFIG_DIR / "hypr" / "omarchy"
THEMES_DIR = ASSETS_DIR / "themes"
USER_THEMES_DIR = Path(os.environ.get("XDG_DATA_HOME", HOME / ".local" / "share")) / "bwm" / "omarchy-themes"
LEGACY_THEMES_DIR = CONFIG_DIR / "omarchy" / "themes"
STATE_DIR = HOME / ".local" / "state" / "bwm" / "omarchy"
COLORS_TOML = STATE_DIR / "colors.toml"
THEME_MODE_FILE = STATE_DIR / "theme.mode"
THEME_NAME_FILE = STATE_DIR / "theme.name"

OMARCHY_STATE_DIR = HOME / ".local" / "state" / "omarchy"
OMARCHY_CURRENT_DIR = OMARCHY_STATE_DIR / "current"
OMARCHY_CURRENT_THEME_NAME = OMARCHY_CURRENT_DIR / "theme.name"
OMARCHY_CURRENT_THEME_DIR = OMARCHY_CURRENT_DIR / "theme"
OMARCHY_CURRENT_BG_LINK = OMARCHY_CURRENT_DIR / "background"

RETRO_COLORS_JSON = HOME / ".local" / "state" / "quickshell" / "user" / "generated" / "retro-colors.json"
HYPR_RETRO_COLORS_LUA = CONFIG_DIR / "hypr" / "modules" / "retro_colors.lua"
ROFI_COLORS_RASI = CONFIG_DIR / "rofi" / "omarchy-colors.rasi"
CONFIG_RETRO_JSON = CONFIG_DIR / "illogical-impulse" / "config-retro.json"
WALLPAPERS_DIR = HOME / "Pictures" / "Wallpapers"

REPO_DIR = Path("/home/sasel/Projects/hyprland-de") if Path("/home/sasel/Projects/hyprland-de").exists() else Path("/mnt/HDD1TB/Projects/hyprland-de")
REPO_HYPR_RETRO_COLORS_LUA = REPO_DIR / "config" / "hypr" / "modules" / "retro_colors.lua"
REPO_ROFI_COLORS_RASI = REPO_DIR / "config" / "rofi" / "omarchy-colors.rasi"
REPO_CONFIG_RETRO_JSON = REPO_DIR / "config" / "illogical-impulse" / "config-retro.json"

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
    "swaync": "swaync.css",
    "firefox": "firefox.css",
    "stremio": "stremio.css",
    "steam": "steam.css",
}
# Templates handled by their own Omarchy step instead (kitty template, BWM-Omarchy Spicetify
# theme, the BWM Omarchy TUI theme for Vesktop)
MATUGEN_SKIPPED = {"kitty", "spicetify", "vesktop", "vesktop_quickcss"}

# Vesktop (flatpak and native): one theme file for every skin, so a skin/theme change only
# rewrites it and Vencord reloads it live; its @name says which style it is
VESKTOP_DIRS = (HOME / ".var" / "app" / "dev.vencord.Vesktop" / "config" / "vesktop",
                CONFIG_DIR / "vesktop")
VESKTOP_THEME = "bwm.theme.css"
VESKTOP_OLD_THEMES = ("material-you.theme.css",)
VESKTOP_WATCH_STAMP = HOME / ".local" / "state" / "bwm" / "vesktop-watch-v2"

# System monospace font (font-set.sh); the TUI overlays are written with this default
FONT_STATE = HOME / ".local" / "state" / "bwm" / "font"
DEFAULT_FONT = "JetBrainsMono Nerd Font"

def system_font() -> str:
    try:
        font = FONT_STATE.read_text(encoding="utf-8").strip()
        if font:
            return font
    except Exception:
        pass
    return DEFAULT_FONT

def _asset(*parts) -> str:
    """An overlay / theme file, with the system monospace font in place of the default."""
    text = ASSETS_DIR.joinpath(*parts).read_text(encoding="utf-8")
    return text.replace(f'"{DEFAULT_FONT}"', f'"{system_font()}"')

# Stateless GTK 4 windows reopened when the GTK palette changes (GTK 4 reads gtk.css at startup;
# GTK 3 recolours live through gtk-theme.py)
GTK_RELAUNCH_APPS = ("pavucontrol",)


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

def extract_vivid_palette(img_path: str):
    """Extracts a vivid, high-saturation palette from a wallpaper for Retro mode."""
    if not img_path or not os.path.exists(img_path):
        return None
    try:
        if img_path.lower().endswith(".webp"):
            import io
            res = subprocess.run(["magick", img_path, "-resize", "120x120!", "ppm:-"],
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            if res.returncode == 0 and res.stdout:
                img = Image.open(io.BytesIO(res.stdout)).convert("RGB")
            else:
                img = Image.open(img_path).convert("RGB").resize((120, 120))
        else:
            try:
                img = Image.open(img_path).convert("RGB").resize((120, 120))
            except Exception:
                import io
                res = subprocess.run(["magick", img_path, "-resize", "120x120!", "ppm:-"],
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                if res.returncode == 0 and res.stdout:
                    img = Image.open(io.BytesIO(res.stdout)).convert("RGB")
                else:
                    raise
        colors = img.getcolors(15000)
        bins = defaultdict(lambda: {"weight": 0.0, "count": 0, "samples": []})

        for count, (r, g, b) in colors:
            h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
            if l < 0.18 and s < 0.25:
                continue
            if l < 0.06:
                continue
            if l > 0.85 and s < 0.16:
                continue
            if l > 0.96:
                continue
            if s < 0.10:
                continue

            l_factor = 1.0 - 0.45 * (abs(l - 0.52) ** 1.3)
            w = count * (s ** 0.65) * l_factor
            b_idx = int(h * 36) % 36
            bins[b_idx]["weight"] += w
            bins[b_idx]["count"] += count
            bins[b_idx]["samples"].append((w, (r, g, b), h, l, s))

        if not bins:
            h, l, s = 0.58, 0.5, 0.8
            accent = "#38bdf8"
            s_vivid = 0.85
        else:
            smoothed_bins = {}
            for i in range(36):
                prev_i = (i - 1) % 36
                next_i = (i + 1) % 36
                sw = bins[i]["weight"] * 1.6 + bins[prev_i]["weight"] * 0.7 + bins[next_i]["weight"] * 0.7
                smoothed_bins[i] = sw

            best_bin = max(smoothed_bins.keys(), key=lambda k: smoothed_bins[k])
            candidate_samples = bins[best_bin]["samples"] + bins[(best_bin - 1) % 36]["samples"] + bins[(best_bin + 1) % 36]["samples"]
            if not candidate_samples:
                candidate_samples = bins[best_bin]["samples"]

            candidate_samples.sort(key=lambda x: x[0], reverse=True)
            top_sample = candidate_samples[0]
            r, g, b = top_sample[1]
            h, l, s = top_sample[2], top_sample[3], top_sample[4]

            s_vivid = min(1.0, max(0.85, s * 1.6))
            l_vivid = min(0.62, max(0.48, l))
            r_v, g_v, b_v = colorsys.hls_to_rgb(h, l_vivid, s_vivid)
            accent = f"#{int(r_v * 255):02x}{int(g_v * 255):02x}{int(b_v * 255):02x}"

        h_sec = (h + 0.12) % 1.0
        r_sec, g_sec, b_sec = colorsys.hls_to_rgb(h_sec, min(0.68, max(0.50, l)), s_vivid)
        secondary = f"#{int(r_sec * 255):02x}{int(g_sec * 255):02x}{int(b_sec * 255):02x}"

        r_bg, g_bg, b_bg = colorsys.hls_to_rgb(h, 0.05, 0.25)
        bg = f"#{int(r_bg * 255):02x}{int(g_bg * 255):02x}{int(b_bg * 255):02x}"

        hues = [0.0, 0.33, 0.14, 0.58, 0.83, 0.50]
        term = [bg]
        for hu in hues:
            cr, cg, cb = colorsys.hls_to_rgb(hu, 0.60, 0.90)
            term.append(f"#{int(cr * 255):02x}{int(cg * 255):02x}{int(cb * 255):02x}")
        term.append("#f8fafc")
        term.append("#475569")
        for hu in hues:
            cr, cg, cb = colorsys.hls_to_rgb(hu, 0.70, 0.95)
            term.append(f"#{int(cr * 255):02x}{int(cg * 255):02x}{int(cb * 255):02x}")
        term.append("#ffffff")

        return {
            "accent": accent,
            "secondary": secondary,
            "bg": bg,
            "fg": "#f8fafc",
            "border": accent,
            "colors": term
        }
    except Exception as e:
        print(f"[Warning] Error extrayendo paleta viva: {e}", file=sys.stderr)
        return {
            "accent": "#38bdf8",
            "secondary": "#818cf8",
            "bg": "#0b1016",
            "fg": "#f8fafc",
            "border": "#38bdf8",
            "colors": []
        }

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
    # The Hyprland active border (neon accent -> secondary at 45deg, as in retro_colors.lua):
    # Omarchy's shell.toml points menu, popup and panel borders at it via shell_gradient
    if palette.get("accent") and palette.get("secondary"):
        c["hyprland_active_border"] = (f"rgba({palette['accent'].lstrip('#')}ee) "
                                       f"rgba({palette['secondary'].lstrip('#')}ee) 45deg")
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

def _mix(a: str, b: str, amount: str) -> str:
    """{{ mix a b N% }} as omarchy-theme-set-templates computes it (a towards b by N)."""
    t = float(amount.rstrip("%"))
    t = t / 100 if amount.endswith("%") or t > 1 else t
    t = max(0.0, min(1.0, t))
    ca, cb = (tuple(int(c.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) for c in (a, b))
    return "#%02x%02x%02x" % tuple(int(x * (1 - t) + y * t + 0.5) for x, y in zip(ca, cb))

def render_omarchy(template: str, colors: dict) -> str:
    """Omarchy template syntax: {{ key }}, {{ key_strip }} (no #), {{ key_rgb }} (r,g,b),
    {{ mix a b N% }} and {{ shell_gradient key fallback }} (the key's colour/gradient from
    colors.toml, else the fallback colour)."""
    def fill(m):
        key = m.group(1).strip()
        parts = key.split()
        if len(parts) == 4 and parts[0] == "mix" and parts[1] in colors and parts[2] in colors:
            return _mix(colors[parts[1]], colors[parts[2]], parts[3])
        if len(parts) == 3 and parts[0] in ("shell_gradient", "gradient_start"):
            return colors.get(parts[1]) or colors.get(parts[2], m.group(0))
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
def apply_shell_toml(colors: dict):
    """shell.toml next to colors.toml: the surface tokens Omarchy's shell libraries
    (Quickshell qs.Commons, used by the Omarchy bar plugins in Retro) read."""
    tpl = (ASSETS_DIR / "themed" / "shell.toml.tpl").read_text(encoding="utf-8")
    _write_if_changed(STATE_DIR / "shell.toml", render_omarchy(tpl, colors))

def apply_kitty(colors: dict):
    tpl = (ASSETS_DIR / "themed" / "kitty.conf.tpl").read_text(encoding="utf-8")
    content = render_omarchy(tpl, colors) + f"\ninactive_border_color {colors['muted']}\nurl_color {colors['accent']}\n"
    _write_if_changed(KITTY_COLORS_CONF, content)
    # Always: a window whose colours a program changed keeps them across a config reload
    subprocess.run([str(Path(__file__).resolve().parent / "kitty-recolor.sh")], check=False)

def set_btop_theme(name: str):
    if not BTOP_CONF.is_file():
        return
    text = BTOP_CONF.read_text(encoding="utf-8")
    new = re.sub(r'^color_theme\s*=.*$', f'color_theme = "{name}"', text, flags=re.M)
    if new == text and "color_theme" not in text:
        new = text + f'color_theme = "{name}"\n'
    _write_if_changed(BTOP_CONF, new)

def apply_btop(colors: dict):
    # The theme's own btop.theme when it ships one (Omarchy's precedence), else the template
    shipped = bwm_omarchy_apps.THEME_DIR / "btop.theme"
    if shipped.is_file():
        _write_if_changed(BTOP_THEME, shipped.read_text(encoding="utf-8"))
    else:
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
            content += _asset("overlays", overlay)
        try:
            if _write_if_changed(dst, content):
                changed.add(name)
                if tpl.get("post_hook"):
                    hooks.append(tpl["post_hook"])
            elif name == "stremio" and tpl.get("post_hook"):
                # It may have been installed since this palette was last rendered.
                hooks.append(tpl["post_hook"])
        except Exception as e:
            print(f"[Warning] Error escribiendo {dst}: {e}", file=sys.stderr)
    # The same reload hooks matugen would run (Quickshell, Pywalfox, Nautilus, swaync, Hyprland...)
    for hook in hooks:
        _detached(hook)
    return changed

VESKTOP_QUICKCSS = ("/* BWM: el estilo está en themes/bwm.theme.css (cambia con el estilo y el tema).\n"
                    "   Escribe aquí tu CSS propio: BWM no lo toca. */\n")

def _write_in_place(path: Path, content: str) -> bool:
    """Vesktop watches its files by inode (fs.watch): an atomic rename would end the watch, and
    it would keep the old colours for good. Same file, rewritten in place."""
    try:
        if path.read_text(encoding="utf-8") == content:
            return False
    except Exception:
        pass
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return True

def vesktop_quickcss(d: Path):
    """Quick CSS used to be a copy of the theme, loaded after it (it kept the old colours): back to
    an empty one, unless the user wrote their own."""
    q = d / "settings" / "quickCss.css"
    try:
        text = q.read_text(encoding="utf-8")
    except Exception:
        text = ""
    if not text.strip() or "@name BWM" in text or "@name Material You" in text:
        _write_in_place(q, VESKTOP_QUICKCSS)

def apply_vesktop(colors: dict):
    """BWM Omarchy TUI theme for Vesktop: themes/bwm.theme.css, reloaded live by Vencord."""
    content = render_omarchy(_asset("themed", "vesktop.theme.css.tpl"), colors)
    for d in VESKTOP_DIRS:
        if d.is_dir():
            _write_in_place(d / "themes" / VESKTOP_THEME, content)
            vesktop_quickcss(d)
    vesktop_enable_theme()

def _vesktop_settings_need(d: Path):
    """The enabledThemes list Vencord should have in `d`, or None if it already has it."""
    path = d / "settings" / "settings.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    themes = data.get("enabledThemes") or []
    wanted = [VESKTOP_THEME] + [x for x in themes if x != VESKTOP_THEME and x not in VESKTOP_OLD_THEMES]
    return None if themes == wanted else wanted

def vesktop_enable_theme():
    """Enable bwm.theme.css in Vencord (replacing the old material-you.theme.css). Vencord keeps
    its settings in memory and rewrites them on exit, so a running Vesktop is closed, edited and
    reopened in the same place (restart_app). Only happens once: afterwards the file name never
    changes and theme changes are live."""
    for d in VESKTOP_DIRS:
        if d.is_dir():
            vesktop_quickcss(d)
    dirs = [d for d in VESKTOP_DIRS if d.is_dir() and _vesktop_settings_need(d) is not None]
    # Before 2026-10-26 the theme files were replaced by rename, which ended Vesktop's file watch:
    # one restart so it watches the files again (VESKTOP_WATCH_STAMP)
    stale_watch = not VESKTOP_WATCH_STAMP.exists()
    if not dirs and not stale_watch:
        return

    def edit():
        for d in dirs:
            wanted = _vesktop_settings_need(d)
            if wanted is None:
                continue
            path = d / "settings" / "settings.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["enabledThemes"] = wanted
            data["useQuickCss"] = True
            _write_if_changed(path, json.dumps(data, indent=4, ensure_ascii=False))
            for old in VESKTOP_OLD_THEMES:
                (d / "themes" / old).unlink(missing_ok=True)

    windows = [c for c in _hypr_clients() if c.get("class", "").lower() == "vesktop"]
    if not windows:
        if subprocess.run(["pgrep", "-f", "vesktop.bin"], stdout=subprocess.DEVNULL).returncode == 0:
            return  # in the tray, no window: next time
        edit()
        VESKTOP_WATCH_STAMP.parent.mkdir(parents=True, exist_ok=True)
        VESKTOP_WATCH_STAMP.touch()
        return
    pid = windows[0]["pid"]
    try:
        # Electron may rewrite its argv as one space-separated string
        argv = " ".join(a.decode() for a in Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0") if a).split()
    except Exception:
        argv = []
    flatpak = (bool(argv) and argv[0].startswith("/app/")) or Path(f"/proc/{pid}/root/.flatpak-info").exists()
    if flatpak:
        flags = [a for a in argv[1:] if a.startswith("--") and not a.startswith(("--enable-speech", "--disable-gpu-sandbox", "--type="))]
        cmd = ["flatpak", "run", "dev.vencord.Vesktop", *flags]
    elif argv and shutil.which(argv[0]):
        cmd = argv
    else:
        cmd = ["vesktop"]
    if restart_app(lambda c: c.get("class", "").lower() == "vesktop", cmd, before_start=edit,
                   wait_for="vesktop.bin"):
        VESKTOP_WATCH_STAMP.parent.mkdir(parents=True, exist_ok=True)
        VESKTOP_WATCH_STAMP.touch()

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
    changed |= _write_if_changed(SPICETIFY_THEME_DIR / "user.css", _asset("spicetify", "user.css"))
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
# Entry points & Theming Engine (Dynamic vs Curated Static)
# ------------------------------------------------------------------------------
def get_retro_mode() -> tuple[str, str]:
    """Returns (mode, theme_name). Mode is 'dynamic' or 'static'."""
    mode = "dynamic"
    name = "dynamic"
    try:
        if THEME_MODE_FILE.is_file():
            val = THEME_MODE_FILE.read_text(encoding="utf-8").strip()
            if val in ("dynamic", "static"):
                mode = val
    except Exception:
        pass
    try:
        if THEME_NAME_FILE.is_file():
            val = THEME_NAME_FILE.read_text(encoding="utf-8").strip()
            if val:
                name = val
    except Exception:
        pass
    if mode == "dynamic":
        name = "dynamic"
    return mode, name

def set_retro_mode_state(mode: str, name: str):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    OMARCHY_CURRENT_DIR.mkdir(parents=True, exist_ok=True)
    _write_if_changed(THEME_MODE_FILE, mode + "\n")
    _write_if_changed(THEME_NAME_FILE, name + "\n")
    _write_if_changed(OMARCHY_CURRENT_THEME_NAME, name + "\n")

    # The generated theme directory (bwm_omarchy_apps.render_theme_dir), as in Omarchy
    target = bwm_omarchy_apps.THEME_DIR
    target.mkdir(parents=True, exist_ok=True)

    try:
        if OMARCHY_CURRENT_THEME_DIR.is_symlink() or OMARCHY_CURRENT_THEME_DIR.exists():
            OMARCHY_CURRENT_THEME_DIR.unlink()
        OMARCHY_CURRENT_THEME_DIR.symlink_to(target)
    except Exception as e:
        print(f"[Warning] Error symlinking {OMARCHY_CURRENT_THEME_DIR}: {e}", file=sys.stderr)

def theme_directory(name: str) -> Path:
    """Resolve installed community themes and the bundled Omarchy themes alike."""
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]*", name) or name == "dynamic":
        raise ValueError(f"Nombre de tema no válido: {name}")
    for root in (USER_THEMES_DIR, LEGACY_THEMES_DIR, THEMES_DIR):
        directory = root / name
        if (directory / "colors.toml").is_file():
            return directory
    raise ValueError(f"Tema estático no encontrado: {name}")


def list_omarchy_themes() -> list[dict]:
    """Bundled and user-installed themes, with the same precedence as theme_directory."""
    themes = {}
    for root in (THEMES_DIR, LEGACY_THEMES_DIR, USER_THEMES_DIR):
        # This installation's legacy path is a symlink to the bundled themes.
        if root == LEGACY_THEMES_DIR and root.resolve() == THEMES_DIR.resolve():
            continue
        if not root.is_dir():
            continue
        for entry in sorted(root.iterdir()):
            if entry.name.startswith(".") or not entry.is_dir() or not (entry / "colors.toml").is_file():
                continue
            preview = entry / "preview.png"
            bg_dir = entry / "backgrounds"
            try:
                colors = tomllib.loads((entry / "colors.toml").read_text())
            except (OSError, ValueError):
                continue
            try:
                source = json.loads((entry / ".bwm-source.json").read_text()).get("url", "")
            except (OSError, ValueError, AttributeError):
                source = ""
            themes[entry.name] = {
                "id": entry.name,
                "name": entry.name.replace("-", " ").title(),
                "path": str(entry),
                "preview": str(preview) if preview.is_file() else "",
                "backgrounds_dir": str(bg_dir) if bg_dir.is_dir() else "",
                "builtin": root.resolve() == THEMES_DIR.resolve(),
                "url": source,
                "colors": [colors.get(key, "#808080") for key in ("background", "foreground", "accent", "blue", "green", "red")]
            }
    return [themes[name] for name in sorted(themes)]

def theme_mode(c: dict) -> str:
    """Light or dark, as omarchy-theme-color resolves it: the `mode` key, the legacy `theme_type`
    key, then the background's brightness (sum of its channels over 382)."""
    mode = str(c.get("mode") or c.get("theme_type") or "").lower()
    if mode in ("light", "dark"):
        return mode
    bg = str(c.get("background", "")).lstrip("#")
    if re.fullmatch(r"[0-9a-fA-F]{6}", bg):
        return "light" if sum(int(bg[i:i + 2], 16) for i in (0, 2, 4)) > 382 else "dark"
    return "dark"

def complete_colors(raw: dict) -> dict:
    """Ensure all required Omarchy and BWM keys exist in the colors dictionary."""
    c = dict(raw)
    c["mode"] = mode = theme_mode(c)
    accent = c.get("accent", "#38bdf8")
    bg = c.get("background", "#121820")
    fg = c.get("foreground", "#f8fafc")

    c.setdefault("dark_background", bg)
    c.setdefault("darker_background", bg)
    c.setdefault("lighter_background", bg)
    c.setdefault("selection", "#292e42")
    c.setdefault("selection_background", c.get("selection", "#292e42"))
    c.setdefault("selection_foreground", c.get("bright_foreground", fg))
    c.setdefault("muted", "#94a3b8")
    c.setdefault("dark_foreground", "#565f89")
    c.setdefault("light_foreground", fg)
    c.setdefault("bright_foreground", "#ffffff")
    c.setdefault("cursor", accent)

    # ANSI colors fallback (purple and magenta are aliases, as in omarchy-theme-color)
    for a, b in (("magenta", "purple"), ("bright_magenta", "bright_purple")):
        if a not in c and b in c:
            c[a] = c[b]
    for col in ("red", "orange", "yellow", "green", "cyan", "blue", "magenta", "brown"):
        c.setdefault(col, accent)
        c.setdefault("bright_" + col, c[col])
    c.setdefault("purple", c["magenta"])
    c.setdefault("bright_purple", c["bright_magenta"])
    c["theme_type"] = mode  # legacy key some Omarchy templates read

    # No hyprland_active_border invented here: like Omarchy, a theme without one gets a solid
    # accent window border and foreground-coloured menu/launcher borders (shell.toml fallbacks)
    return c

def update_retro_config_json(mode: str, name: str):
    targets = [CONFIG_RETRO_JSON]
    if REPO_CONFIG_RETRO_JSON.is_file() and REPO_CONFIG_RETRO_JSON != CONFIG_RETRO_JSON:
        targets.append(REPO_CONFIG_RETRO_JSON)
    for cfg_path in targets:
        try:
            if cfg_path.is_file():
                data = json.loads(cfg_path.read_text(encoding="utf-8"))
                app = data.setdefault("appearance", {})
                app["retroThemeMode"] = mode
                app["retroThemeName"] = name
                _write_if_changed(cfg_path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[Warning] Error actualizando {cfg_path}: {e}", file=sys.stderr)

def _secondary(colors: dict) -> str:
    """Second colour of the Hyprland border gradient (the wallpaper's secondary in dynamic mode)."""
    m = re.findall(r"rgba?\(([0-9a-fA-F]{6})", colors.get("hyprland_active_border", ""))
    if len(m) > 1:
        return "#" + m[1].lower()
    # A solid border (or none: Omarchy then uses the accent alone)
    return "#" + m[0].lower() if m else colors["accent"]

def write_retro_sync_files(colors: dict):
    """Write Quickshell retro-colors.json, Hyprland retro_colors.lua, and Rofi omarchy-colors.rasi."""
    # 1. Quickshell retro-colors.json
    try:
        RETRO_COLORS_JSON.parent.mkdir(parents=True, exist_ok=True)
        retro_data = {
            "accent": colors["accent"],
            "secondary": _secondary(colors),
            "bg": colors["background"],
            "border": colors["accent"],
            "fg": colors["foreground"],
            "dim": colors.get("dark_foreground", "#475569"),
            "muted": colors.get("muted", "#94a3b8")
        }
        _write_if_changed(RETRO_COLORS_JSON, json.dumps(retro_data, indent=2) + "\n")
    except Exception as e:
        print(f"[Warning] Error guardando {RETRO_COLORS_JSON}: {e}", file=sys.stderr)

    # 2. Hyprland retro_colors.lua
    hex_acc = colors["accent"].lstrip("#")
    sec_color = _secondary(colors)
    hex_sec = sec_color.lstrip("#")
    hex_bg = colors["background"].lstrip("#")
    lua_content = f"""-- Generado automáticamente por bwm_omarchy.py
local retro_colors = {{
    accent = "rgba({hex_acc}ee)",
    secondary = "rgba({hex_sec}ee)",
    bg = "rgba({hex_bg}ee)",
    border = "rgba({hex_acc}ee)",
    border_inactive = "rgba(101520aa)",
}}
return retro_colors
"""
    targets = [HYPR_RETRO_COLORS_LUA]
    if REPO_HYPR_RETRO_COLORS_LUA.parent.exists() and REPO_HYPR_RETRO_COLORS_LUA != HYPR_RETRO_COLORS_LUA:
        targets.append(REPO_HYPR_RETRO_COLORS_LUA)
    for target in targets:
        try:
            _write_if_changed(target, lua_content)
        except Exception as e:
            print(f"[Warning] Error guardando {target}: {e}", file=sys.stderr)

    # 3. Rofi omarchy-colors.rasi
    rofi_colors = f"""* {{
    accent: {colors['accent']};
    secondary: {sec_color};
    bg: {colors['background']}f5;
    bg-input: {colors.get('dark_background', '#121820')};
    fg: {colors['foreground']};
    muted: {colors.get('muted', '#94a3b8')};
    dim: {colors.get('dark_foreground', '#475569')};
    bg-selected-text: {colors.get('darker_background', '#090c0f')};
}}
"""
    rofi_targets = [ROFI_COLORS_RASI]
    if REPO_ROFI_COLORS_RASI.parent.exists() and REPO_ROFI_COLORS_RASI != ROFI_COLORS_RASI:
        rofi_targets.append(REPO_ROFI_COLORS_RASI)
    for target in rofi_targets:
        try:
            _write_if_changed(target, rofi_colors)
        except Exception as e:
            print(f"[Warning] Error guardando {target}: {e}", file=sys.stderr)

RETRO_LIGHT_MARK = STATE_DIR / "light-scheme"

def _gsetting(key: str, value: str):
    """gsettings set, only when it changes (every write makes GTK apps restyle)."""
    cur = subprocess.run(["gsettings", "get", "org.gnome.desktop.interface", key],
                         capture_output=True, text=True).stdout.strip().strip("'")
    if cur != value:
        subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", key, value],
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def apply_color_scheme(mode: str):
    """Light/dark for the apps, like omarchy-theme-set-gnome: GTK 3 (adw-gtk3[-dark]), libadwaita and
    Qt through the portal's color-scheme, Electron/Chromium/Firefox through prefers-color-scheme.
    The other themes are dark: leaving Retro after a light theme puts it back (restore_non_retro)."""
    light = mode == "light"
    # GTK 3: BWM's live-reloading theme around adw-gtk3[-dark] (gtk-theme.py)
    subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "gtk-theme.py"), "set",
                    "light" if light else "dark"], check=False, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)
    _gsetting("color-scheme", "prefer-light" if light else "prefer-dark")
    pywalfox = HOME / ".local" / "share" / "pywalfox-venv" / "bin" / "pywalfox"
    if pywalfox.is_file():
        _detached(f"{pywalfox} {'light' if light else 'dark'}")
    if light:
        RETRO_LIGHT_MARK.parent.mkdir(parents=True, exist_ok=True)
        RETRO_LIGHT_MARK.touch()
    else:
        RETRO_LIGHT_MARK.unlink(missing_ok=True)

OMARCHY_LANGUAGE = CONFIG_DIR / "omarchy" / "language"
# Languages of Omarchy's shell vendored in quickshell/ii/Commons/omarchy/default/i18n
OMARCHY_LANGUAGES = ("en", "es-MX")

def ensure_omarchy_language():
    """Omarchy's shell (bar panels, menu, dock, OSD...) follows ~/.config/omarchy/language: when the
    user has not picked one, the session's language (Spanish -> es-MX, Omarchy's Spanish)."""
    if OMARCHY_LANGUAGE.exists():
        return
    lang = (os.environ.get("LC_MESSAGES") or os.environ.get("LANG") or "").lower()
    code = "es-MX" if lang.startswith("es") else "en"
    OMARCHY_LANGUAGE.parent.mkdir(parents=True, exist_ok=True)
    OMARCHY_LANGUAGE.write_text(code + "\n", encoding="utf-8")

def apply_retro_palette_colors(colors: dict, wallpaper: str = ""):
    """Apply an Omarchy-format palette dictionary to all apps, configs, and reload UI."""
    colors = complete_colors(colors)
    ensure_omarchy_language()
    write_colors_toml(colors)
    apply_task_manager(True)

    # Every Omarchy app template (default/themed) into the theme directory, a static theme's own
    # files first; then each app's omarchy-theme-set-<app> step (bwm_omarchy_apps)
    mode, name = get_retro_mode()
    static_dir = theme_directory(name) if mode == "static" else None
    try:
        bwm_omarchy_apps.render_theme_dir(colors, render_omarchy, static_dir)
        _write_if_changed(bwm_omarchy_apps.THEME_DIR / "shell.toml",
                          render_omarchy((ASSETS_DIR / "themed" / "shell.toml.tpl").read_text(encoding="utf-8"), colors))
    except Exception as e:
        print(f"[Warning] tema de Omarchy: {e}", file=sys.stderr)

    # VS Code-like editors now get Omarchy's full theme extension (bwm_omarchy_apps.apply_vscode)
    # instead of BWM's old colorCustomizations, which would override it
    restore_vscodium()
    for step in (apply_shell_toml, apply_kitty, apply_btop, apply_spotify, apply_vesktop,
                 bwm_omarchy_apps.apply_apps):
        try:
            step(colors)
        except Exception as e:
            print(f"[Warning] {step.__name__}: {e}", file=sys.stderr)

    changed = apply_matugen_apps(colors, wallpaper)

    apply_color_scheme(theme_mode(colors))

    try:
        import bwm_icons
        bwm_icons.apply("retro", colors["accent"], theme_mode(colors) == "light")
    except Exception as e:
        print(f"[Warning] iconos: {e}", file=sys.stderr)

    write_retro_sync_files(colors)

    # Firefox only reads its chrome CSS at startup: restart it (session and windows kept)
    if "firefox" in changed and not bwm_transition.switching():
        _detached(f"{sys.executable} {Path(__file__).resolve()} restart-firefox")

    if "gtk4" in changed and not bwm_transition.switching():
        for app in GTK_RELAUNCH_APPS:
            if _running(app):
                subprocess.run(["pkill", "-f", f"(^|/){app}( |$)"], check=False)
                _detached(f"sleep 0.5; exec {app}")

    run_hooks("retro")

    if not bwm_transition.switching():
        try:
            subprocess.run(["hyprctl", "reload"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["quickshell", "-c", "ii", "ipc", "call", "theme", "reload"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["quickshell", "-c", "ii", "ipc", "call", "retro", "reload"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        _detached("python3 ~/.config/hypr/scripts/bwm_boot.py render")
    return colors

def _theme_wallpaper(theme_dir: Path) -> str:
    bg_dir = theme_dir / "backgrounds"
    if not bg_dir.is_dir():
        return ""
    bgs = sorted(p for p in bg_dir.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"))
    return str(bgs[0]) if bgs else ""

def _link_background(wp: str):
    if not wp:
        return
    try:
        OMARCHY_CURRENT_DIR.mkdir(parents=True, exist_ok=True)
        if OMARCHY_CURRENT_BG_LINK.is_symlink() or OMARCHY_CURRENT_BG_LINK.exists():
            OMARCHY_CURRENT_BG_LINK.unlink()
        OMARCHY_CURRENT_BG_LINK.symlink_to(Path(wp))
    except Exception:
        pass

def _notify(body: str):
    _detached(f'notify-send -a "BWM Theme" -i preferences-desktop-theme "Tema Retro" "{body}"')

def apply_retro_static_theme(theme_name: str, set_wallpaper: bool = True, notify: bool = False) -> dict:
    """Applies one of the curated static Omarchy themes."""
    theme_dir = theme_directory(theme_name)

    try:
        with open(theme_dir / "colors.toml", "rb") as f:
            raw_colors = tomllib.load(f)
    except Exception as e:
        raise RuntimeError(f"Error leyendo colors.toml para {theme_name}: {e}")

    # Legacy Omarchy marker for light themes, beside colors.toml
    if (theme_dir / "light.mode").is_file() and "mode" not in raw_colors:
        raw_colors["mode"] = "light"
    colors = complete_colors(raw_colors)
    set_retro_mode_state("static", theme_name)
    update_retro_config_json("static", theme_name)
    display_name = theme_name.replace("-", " ").title()

    wp = _theme_wallpaper(theme_dir) if set_wallpaper else ""
    if wp:
        # set-wallpaper.sh also updates the lock screen and the Retro profile, and applies this
        # palette itself (static mode keeps it): one pass instead of two
        _link_background(wp)
        subprocess.run([str(CONFIG_DIR / "hypr" / "scripts" / "set-wallpaper.sh"), wp], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if notify:
            _notify(f"Tema estático: {display_name}")
        return colors

    try:
        wp = (HOME / ".cache" / "current_wallpaper").read_text(encoding="utf-8").strip()
    except Exception:
        wp = ""
    _link_background(wp)
    apply_retro_palette_colors(colors, wp)
    if notify:
        _notify(f"Tema estático: {display_name}")
    return colors

def apply_retro_dynamic_theme(wallpaper: str = "", notify: bool = False) -> dict:
    """Applies dynamic theme extracted from the wallpaper."""
    set_retro_mode_state("dynamic", "dynamic")
    update_retro_config_json("dynamic", "dynamic")

    wp = wallpaper
    if not wp:
        try:
            cache_file = HOME / ".cache" / "current_wallpaper"
            if cache_file.exists():
                wp = cache_file.read_text(encoding="utf-8").strip()
        except Exception:
            wp = ""
    if not wp or not os.path.exists(wp):
        wp = str(WALLPAPERS_DIR / "omarchy-frost.jpg")

    palette = extract_vivid_palette(wp)
    if not palette:
        palette = {"accent": "#38bdf8", "secondary": "#818cf8", "bg": "#0b1016", "fg": "#f8fafc", "border": "#38bdf8"}

    colors = build_colors(palette)

    _link_background(wp)

    apply_retro_palette_colors(colors, wp)
    if notify:
        _notify("Paleta dinámica sacada del fondo")
    return colors

def _bwm_theme() -> str:
    try:
        cfg = json.loads((CONFIG_DIR / "illogical-impulse" / "config.json").read_text(encoding="utf-8"))
        return cfg.get("appearance", {}).get("bwmTheme", "")
    except Exception:
        return ""

def set_theme(target: str):
    """omarchy-theme-set: a curated theme or "dynamic". Outside Retro the Retro palette would
    recolour every app of the active theme, so the choice is stored and BWM switches to Retro."""
    if target != "dynamic":
        theme_directory(target)
    if _bwm_theme() == "retro":
        if target == "dynamic":
            apply_retro_dynamic_theme(notify=True)
        else:
            apply_retro_static_theme(target, notify=True)
        return
    mode = "dynamic" if target == "dynamic" else "static"
    set_retro_mode_state(mode, target)
    update_retro_config_json(mode, target)
    wp = _theme_wallpaper(theme_directory(target)) if mode == "static" else ""
    if wp:
        (HOME / ".cache").mkdir(parents=True, exist_ok=True)
        (HOME / ".cache" / "current_wallpaper_retro").write_text(wp + "\n", encoding="utf-8")
    subprocess.run([sys.executable, str(CONFIG_DIR / "hypr" / "scripts" / "bwm-theme-manager.py"), "set", "retro"],
                   check=False)

def apply_retro_apps(palette: dict, wallpaper: str = ""):
    """Retro skin: Omarchy-style themes for every app, from the wallpaper palette (legacy wrapper)."""
    colors = build_colors(palette)
    apply_retro_palette_colors(colors, wallpaper)
    return colors

HOOKS_DIR = CONFIG_DIR / "bwm" / "hooks"

def run_hooks(theme: str):
    """Hotswap hook for any app BWM does not theme itself, like `omarchy-hook theme-set`.

    Runs ~/.config/bwm/hooks/theme-set and every executable in theme-set.d/ (sorted), in the
    background, with BWM_THEME=<default|retro|plasma> and BWM_COLORS=<Omarchy colors.toml>
    (the wallpaper palette in Retro). Drop a script there to retint an extra app live.
    """
    scripts = []
    single = HOOKS_DIR / "theme-set"
    if single.is_file() and os.access(single, os.X_OK):
        scripts.append(single)
    d = HOOKS_DIR / "theme-set.d"
    if d.is_dir():
        scripts += sorted(p for p in d.iterdir() if p.is_file() and os.access(p, os.X_OK))
    env = dict(os.environ, BWM_THEME=theme, BWM_COLORS=str(COLORS_TOML), BWM_STATE=str(STATE_DIR))
    for script in scripts:
        subprocess.Popen([str(script), theme], env=env, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)

TASK_MANAGER_DESKTOP = HOME / ".local" / "share" / "applications" / "bwm-task-manager.desktop"

RETRO_APPS = ("bwm-task-manager.desktop", "bwm-quick-settings.desktop")

def apply_task_manager(present: bool):
    """Retro-only apps (omarchy/applications, translated names and keywords): "Task Manager" /
    "Gestor de tareas" = btop in the default terminal, as in Omarchy, and "Quick Settings" /
    "Ajustes rápidos" = the centered quick settings window."""
    for name in RETRO_APPS:
        dest = TASK_MANAGER_DESKTOP.parent / name
        if present:
            tpl = (ASSETS_DIR / "applications" / name).read_text(encoding="utf-8")
            dest.parent.mkdir(parents=True, exist_ok=True)
            _write_if_changed(dest, tpl.replace("@HOME@", str(HOME)))
        else:
            dest.unlink(missing_ok=True)

def restore_non_retro():
    """Leaving Retro: give back what the other skins do not regenerate by themselves."""
    apply_task_manager(False)
    if RETRO_LIGHT_MARK.exists():
        apply_color_scheme("dark")
    set_btop_theme("matugen")
    restore_vscodium()
    bwm_omarchy_apps.restore_apps()
    try:
        if _set_spicetify_theme("MaterialYou", "MaterialYou"):
            _detached("~/.config/hypr/scripts/reload-spotify.sh")
    except Exception:
        pass


# ------------------------------------------------------------------------------
# Firefox: its chrome CSS (TUI overlay) is only read at startup
# ------------------------------------------------------------------------------
def _hypr_clients():
    try:
        return json.loads(subprocess.check_output(["hyprctl", "clients", "-j"]).decode())
    except Exception:
        return []

RESTART_LOCK = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "bwm-restart-app.lock"
FIREFOX_CHROME_CSS = HOME / ".cache" / "material-you-firefox.css"

def _proc_start(pid: int) -> float:
    try:
        return Path(f"/proc/{pid}").stat().st_ctime
    except Exception:
        return 0.0

def _alive(pattern: str) -> bool:
    return subprocess.run(["pgrep", "-f", pattern], stdout=subprocess.DEVNULL).returncode == 0

def restart_app(match, cmd, before_start=None, wait_for=None, quit_pids=None, quit_cmd=None,
                wait_secs=15, place_secs=60):
    """Close an app gracefully (SIGTERM: Firefox/Electron save their session), optionally edit
    its config, start it again with `cmd` and put every window back where it was: workspace
    (special ones too), monitor and, if floating, position and size. Windows are matched by
    title, then by order for those that still have another title after a while. A window that
    goes away soon after being placed (Steam's loading window) gives its slot back, so the real
    one is placed too; windows that come back floating where they were tiled (KDE Plasma) keep
    their place via bwm_windows.restored_box."""
    import signal
    import time

    if bwm_transition.switching():
        return False  # un cambio cosmético no cierra apps ni restaura focos antiguos
    windows = [c for c in _hypr_clients() if match(c)]
    if not windows:
        return False
    import bwm_windows
    layout = [{"title": c["title"], "ws": c["workspace"]["name"], "at": c["at"], "size": c["size"],
               "floating": c.get("floating", False)} for c in windows]
    pids = set(quit_pids or {c["pid"] for c in windows})
    if quit_cmd:  # the app's own clean shutdown (steam -shutdown)
        subprocess.run(quit_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    else:
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    for _ in range(int(wait_secs * 10)):
        if not any(Path(f"/proc/{p}").exists() for p in pids) and not (wait_for and _alive(wait_for)):
            break
        time.sleep(0.1)
    else:
        return False  # still running (a "quit?" dialog): leave it alone

    if before_start:
        try:
            before_start()
        except Exception as e:
            print(f"[Warning] {e}", file=sys.stderr)

    # Lo que la app abra mientras arranca (la ventana de carga de Steam…) va directamente a su
    # workspace, en silencio: no aparece en medio del que estás mirando ni te cambia de workspace
    hold = "bwm-restart-" + re.sub(r"[^A-Za-z0-9]+", "-", windows[0].get("class", "app")).strip("-").lower()
    bwm_windows.hold_new_windows(hold, sorted({c.get("class", "") for c in windows}), layout[0]["ws"])
    # Sólo se deshace un robo de foco de la app recién abierta; lo que hagas tú mientras se
    # reabre se respeta (antes se restauraba al final una foto del principio: con Steam, minutos)
    keeper = bwm_windows.FocusKeeper(lambda c: match(c) and c["pid"] not in pids)
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

    pending = list(layout)
    placed = {}            # address -> layout entry
    start = last_place = time.time()
    # Sigue hasta colocarlas todas y unos segundos más, por si una ventana colocada era la de
    # carga y se cierra (vuelve su hueco a pending y se coloca la definitiva)
    while time.time() - start < place_secs and (pending or time.time() - last_place < 8):
        time.sleep(0.5)
        clients = _hypr_clients()
        keeper.check(clients)
        alive = {c["address"] for c in clients}
        for addr in [a for a in placed if a not in alive]:
            pending.append(placed.pop(addr))
        for c in clients:
            if not pending:
                break
            # c["pid"] in pids: an old window not gone yet (Hyprland reuses addresses: compare PIDs)
            if not match(c) or c["address"] in placed or c["pid"] in pids:
                continue
            m = next((l for l in pending if l["title"] == c["title"]), None)
            if not m and time.time() - start > 12:
                m = pending[0]
            if not m:
                continue
            box = bwm_windows.restored_box(m, c)
            bwm_windows.dispatch([bwm_windows.place_lua(c["address"], workspace=m["ws"], box=box)])
            placed[c["address"]] = m
            pending.remove(m)
            last_place = time.time()
    bwm_windows.release_new_windows(hold)
    return True

STEAM_MAIN = r"ubuntu12_32/steam( |$)"

def restart_steam():
    """Steam only loads its skin (Adwaita-for-Steam, steam-theme.sh) at startup: restart it so the
    new colours show, unless a game is running (it would be closed). `steam -shutdown` is its clean
    exit; the main window comes back in place, or Steam starts in the tray if it was there."""
    import time
    if bwm_transition.switching():
        return
    if not _alive(STEAM_MAIN):
        return
    clients = _hypr_clients()
    if (any(c.get("class", "").startswith("steam_app_") or c.get("class") == "gamescope" for c in clients)
            or _alive("SteamLaunch AppId")):
        _detached('notify-send -a "BWM" "Steam" "El tema nuevo se aplicará cuando reinicies Steam '
                  '(no se reinicia con un juego abierto)."')
        return
    match = lambda c: c.get("class", "") == "steam"
    if any(match(c) for c in clients):
        # Steam puede tardar en volver (actualizaciones, ventana de carga): más margen para colocarla
        restart_app(match, ["steam"], quit_cmd=["steam", "-shutdown"], wait_for=STEAM_MAIN, wait_secs=60,
                    place_secs=180)
        return
    subprocess.run(["steam", "-shutdown"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    for _ in range(600):
        if not _alive(STEAM_MAIN):
            break
        time.sleep(0.1)
    else:
        return
    subprocess.Popen(["steam", "-silent"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     start_new_session=True)

def _firefox_cmd(pid: int) -> list:
    """The command Firefox was started with, without the URLs it was opened with."""
    try:
        argv = [a.decode() for a in Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0") if a]
    except Exception:
        return ["firefox"]
    cmd, keep_next = argv[:1], False
    for a in argv[1:]:
        if keep_next:
            cmd.append(a)
            keep_next = False
        elif a.startswith("-"):
            cmd.append(a)
            keep_next = a in ("-P", "-p", "--profile", "-profile", "--class", "--name", "-name")
    return cmd or ["firefox"]

def restart_firefox(force: bool = False):
    """Restart Firefox when its chrome CSS (the Retro TUI theme, or Material You/Breeze) is newer
    than the running Firefox, which only reads it at startup. Session restore relies on
    browser.startup.page = 3, forced once (resume_session_once) if unset. Waits for the CSS to
    settle first (the skin switch and the palette step can both ask for it): one restart."""
    import fcntl
    import time

    if bwm_transition.switching():
        return
    last, stable = None, 0
    for _ in range(40):
        try:
            m = FIREFOX_CHROME_CSS.stat().st_mtime
        except Exception:
            m = 0
        stable = stable + 1 if m == last else 0
        last = m
        if stable >= 4:
            break
        time.sleep(0.5)

    with open(RESTART_LOCK, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        windows = [c for c in _hypr_clients() if "firefox" in c.get("class", "").lower()]
        if not windows:
            return
        pid = min(c["pid"] for c in windows)
        if not force and _proc_start(pid) > (last or 0):
            return  # already running with this CSS
        cmd = _firefox_cmd(pid)

        def resume_session():
            for prefs in (HOME / ".mozilla" / "firefox").glob("*/prefs.js"):
                try:
                    text = prefs.read_text(encoding="utf-8")
                    if 'browser.startup.page", 3' not in text and "resume_session_once" not in text:
                        prefs.write_text(text + 'user_pref("browser.sessionstore.resume_session_once", true);\n',
                                         encoding="utf-8")
                except Exception:
                    pass

        restart_app(lambda c: "firefox" in c.get("class", "").lower(), cmd,
                    before_start=resume_session, quit_pids={pid})


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "hook" and len(sys.argv) > 2:
            run_hooks(sys.argv[2])
            sys.exit(0)
        elif cmd == "restart-firefox":
            restart_firefox(force="--force" in sys.argv)
            sys.exit(0)
        elif cmd == "restart-steam":
            restart_steam()
            sys.exit(0)
        elif cmd == "vesktop-enable":
            vesktop_enable_theme()
            sys.exit(0)
        elif cmd == "get-mode":
            mode, name = get_retro_mode()
            print(f"{mode}\t{name}")
            sys.exit(0)
        elif cmd == "list-themes":
            themes = list_omarchy_themes()
            if "--json" in sys.argv:
                print(json.dumps(themes, indent=2))
            else:
                for t in themes:
                    print(f"{t['id']}\t{t['name']}\t{t['path']}")
            sys.exit(0)
        elif cmd == "static":
            if len(sys.argv) < 3:
                print("Usage: bwm_omarchy.py static <theme_name> [--no-wallpaper]", file=sys.stderr)
                sys.exit(1)
            set_wp = "--no-wallpaper" not in sys.argv
            apply_retro_static_theme(sys.argv[2], set_wallpaper=set_wp, notify=True)
            sys.exit(0)
        elif cmd == "dynamic":
            wp = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else ""
            apply_retro_dynamic_theme(wp, notify=True)
            sys.exit(0)
        elif cmd == "set-theme":
            if len(sys.argv) < 3:
                print("Usage: bwm_omarchy.py set-theme <theme_name|dynamic>", file=sys.stderr)
                sys.exit(1)
            try:
                set_theme(sys.argv[2])
            except ValueError as e:
                print(e, file=sys.stderr)
                sys.exit(1)
            sys.exit(0)

    print(json.dumps(build_colors({"accent": sys.argv[1] if len(sys.argv) > 1 else "#38bdf8"}), indent=2))
