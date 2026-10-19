#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BWM Theme Manager (Better Window Manager)
Manages and switches themes between:
  1. Default (Material You)
  2. Retro (Omarchy)
  3. KDE Plasma (Breeze Dark)
Provides complete settings isolation (config-default.json, config-retro.json, config-plasma.json),
dynamic wallpaper color adaptation (omitted in Plasma to maintain official Breeze Dark palette),
and Hyprland / Quickshell synchronization.
"""

import sys
import os
import json
import argparse
import subprocess
import colorsys
from pathlib import Path
from PIL import Image
from collections import defaultdict

CONFIG_DIR = Path.home() / ".config"
HYPR_THEME_LUA = CONFIG_DIR / "hypr" / "modules" / "theme.lua"
II_CONFIG_JSON = CONFIG_DIR / "illogical-impulse" / "config.json"
CONFIG_DEFAULT_JSON = CONFIG_DIR / "illogical-impulse" / "config-default.json"
CONFIG_RETRO_JSON = CONFIG_DIR / "illogical-impulse" / "config-retro.json"
CONFIG_PLASMA_JSON = CONFIG_DIR / "illogical-impulse" / "config-plasma.json"
BTOP_CONF = CONFIG_DIR / "btop" / "btop.conf"
KITTY_COLORS_CONF = CONFIG_DIR / "kitty" / "kitty-colors.conf"
RETRO_COLORS_JSON = Path.home() / ".local" / "state" / "quickshell" / "user" / "generated" / "retro-colors.json"
HYPR_RETRO_COLORS_LUA = CONFIG_DIR / "hypr" / "modules" / "retro_colors.lua"
HYPR_PLASMA_COLORS_LUA = CONFIG_DIR / "hypr" / "modules" / "plasma_colors.lua"

REPO_DIR = Path("/mnt/HDD1TB/Projects/hyprland-de")
REPO_HYPR_THEME_LUA = REPO_DIR / "config" / "hypr" / "modules" / "theme.lua"
REPO_II_CONFIG_JSON = REPO_DIR / "config" / "illogical-impulse" / "config.json"
REPO_CONFIG_DEFAULT_JSON = REPO_DIR / "config" / "illogical-impulse" / "config-default.json"
REPO_CONFIG_RETRO_JSON = REPO_DIR / "config" / "illogical-impulse" / "config-retro.json"
REPO_CONFIG_PLASMA_JSON = REPO_DIR / "config" / "illogical-impulse" / "config-plasma.json"
REPO_BTOP_CONF = REPO_DIR / "config" / "btop" / "btop.conf"
REPO_KITTY_COLORS_CONF = REPO_DIR / "config" / "kitty" / "kitty-colors.conf"
REPO_HYPR_RETRO_COLORS_LUA = REPO_DIR / "config" / "hypr" / "modules" / "retro_colors.lua"
REPO_HYPR_PLASMA_COLORS_LUA = REPO_DIR / "config" / "hypr" / "modules" / "plasma_colors.lua"

WALLPAPERS_DIR = Path.home() / "Pictures" / "Wallpapers"

THEMES = {
    "default": {
        "title": "Default (Material You)",
        "description": "Estilo Material 3 / End_4 con esquinas redondeadas y paleta tonal dinámica",
        "wallpaper": str(WALLPAPERS_DIR / "default.jpg"),
        "rounding": 14,
        "rounding_power": 2,
        "border_size": 2,
        "gaps_in": 4,
        "gaps_out": 8,
        "bar_corner_style": 2,
        "bar_height": 40,
        "bar_bottom": False,
        "show_app_icons": True,
        "always_show_numbers": False,
        "is_retro": False,
        "is_plasma": False,
        "fonts": {
            "main": "Google Sans Flex",
            "numbers": "Google Sans Flex",
            "title": "Google Sans Flex",
            "monospace": "JetBrains Mono NF",
            "reading": "Readex Pro",
            "expressive": "Space Grotesk",
            "iconNerd": "JetBrains Mono NF"
        },
        "btop_rounded": True
    },
    "retro": {
        "title": "Retro (Omarchy)",
        "description": "Estilo minimalista Omarchy con barra compacta, bordes vivos y paleta adaptativa",
        "wallpaper": str(WALLPAPERS_DIR / "omarchy-frost.jpg"),
        "rounding": 0,
        "rounding_power": 2,
        "border_size": 2,
        "gaps_in": 3,
        "gaps_out": 5,
        "bar_corner_style": 2,
        "bar_height": 24,
        "bar_bottom": False,
        "show_app_icons": False,
        "always_show_numbers": True,
        "is_retro": True,
        "is_plasma": False,
        "fonts": {
            "main": "JetBrains Mono NF",
            "numbers": "JetBrains Mono NF",
            "title": "JetBrains Mono NF",
            "monospace": "JetBrains Mono NF",
            "reading": "JetBrains Mono NF",
            "expressive": "JetBrains Mono NF",
            "iconNerd": "JetBrains Mono NF"
        },
        "btop_rounded": False
    },
    "plasma": {
        "title": "KDE Plasma (Breeze Dark)",
        "description": "Estilo KDE Plasma 6 con barra inferior Breeze Dark, ventanas flotantes con barra superior y paleta estática",
        "wallpaper": str(WALLPAPERS_DIR / "plasma.png"),
        "rounding": 5,
        "rounding_power": 2,
        "border_size": 2,
        "gaps_in": 0,
        "gaps_out": 0,
        "bar_corner_style": 2,
        "bar_height": 44,
        "bar_bottom": True,
        "show_app_icons": True,
        "always_show_numbers": True,
        "is_retro": False,
        "is_plasma": True,
        "fonts": {
            "main": "Google Sans Flex",
            "numbers": "Google Sans Flex",
            "title": "Google Sans Flex",
            "monospace": "JetBrains Mono NF",
            "reading": "Readex Pro",
            "expressive": "Space Grotesk",
            "iconNerd": "JetBrains Mono NF"
        },
        "btop_rounded": True
    }
}

def get_current_theme() -> str:
    """Reads current theme name from II config or Hyprland theme.lua."""
    if II_CONFIG_JSON.exists():
        try:
            with open(II_CONFIG_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                theme = data.get("appearance", {}).get("bwmTheme")
                if theme in THEMES:
                    return theme
        except Exception:
            pass
    if HYPR_THEME_LUA.exists():
        try:
            with open(HYPR_THEME_LUA, "r", encoding="utf-8") as f:
                for line in f:
                    if "name =" in line:
                        t_name = line.split('"')[1]
                        if t_name in THEMES:
                            return t_name
        except Exception:
            pass
    return "default"

def get_theme_wallpaper(theme_name: str) -> str:
    """Returns the persistent wallpaper for the given theme, falling back to theme default."""
    # 1. Comprobar archivo de caché específico del tema
    theme_cache = Path.home() / ".cache" / f"current_wallpaper_{theme_name}"
    if theme_cache.exists():
        try:
            with open(theme_cache, "r", encoding="utf-8") as f:
                wp = f.read().strip()
                if wp and os.path.exists(wp):
                    return wp
        except Exception:
            pass

    # 2. Comprobar perfil JSON del tema
    if theme_name == "plasma":
        profile = CONFIG_PLASMA_JSON
    elif theme_name == "retro":
        profile = CONFIG_RETRO_JSON
    else:
        profile = CONFIG_DEFAULT_JSON

    if profile.exists():
        try:
            with open(profile, "r", encoding="utf-8") as f:
                data = json.load(f)
                wp = data.get("background", {}).get("wallpaperPath")
                if wp and os.path.exists(wp):
                    return wp
        except Exception:
            pass

    # 3. Fallback al fondo predeterminado del tema
    fallback = THEMES.get(theme_name, {}).get("wallpaper")
    if fallback and os.path.exists(fallback):
        return fallback

    return str(WALLPAPERS_DIR / "default.jpg")

def save_current_theme_config(theme_name: str):
    """Saves the current config.json state to the corresponding profile file, preserving wallpaper."""
    if not II_CONFIG_JSON.exists():
        return
    try:
        with open(II_CONFIG_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Sincronizar wallpaper actual con el perfil del tema saliente
        cache_file = Path.home() / ".cache" / "current_wallpaper"
        current_wp = None
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as cf:
                    current_wp = cf.read().strip()
            except Exception:
                pass
        if not current_wp:
            current_wp = data.get("background", {}).get("wallpaperPath")

        if current_wp and os.path.exists(current_wp):
            if "background" not in data:
                data["background"] = {}
            data["background"]["wallpaperPath"] = current_wp
            theme_cache = Path.home() / ".cache" / f"current_wallpaper_{theme_name}"
            try:
                with open(theme_cache, "w", encoding="utf-8") as tf:
                    tf.write(current_wp)
            except Exception:
                pass

        if theme_name == "plasma":
            target = CONFIG_PLASMA_JSON
            repo_target = REPO_CONFIG_PLASMA_JSON
        elif theme_name == "retro":
            target = CONFIG_RETRO_JSON
            repo_target = REPO_CONFIG_RETRO_JSON
        else:
            target = CONFIG_DEFAULT_JSON
            repo_target = REPO_CONFIG_DEFAULT_JSON

        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        if repo_target.parent.exists():
            try:
                with open(repo_target, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except Exception:
                pass
    except Exception as e:
        print(f"[Warning] Error guardando config para {theme_name}: {e}", file=sys.stderr)

def load_theme_config(target_theme: str, cfg: dict):
    """
    Restores the isolated config for the target theme, ensuring settings
    between Default, Retro, and Plasma remain completely isolated and persistent.
    """
    if target_theme == "plasma":
        profile = CONFIG_PLASMA_JSON
    elif target_theme == "retro":
        profile = CONFIG_RETRO_JSON
    else:
        profile = CONFIG_DEFAULT_JSON

    data = None
    if profile.exists():
        try:
            with open(profile, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = None

    if not data and II_CONFIG_JSON.exists():
        try:
            with open(II_CONFIG_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    if not data:
        data = {}

    # Update theme tokens
    if "appearance" not in data:
        data["appearance"] = {}
    data["appearance"]["bwmTheme"] = target_theme

    # Preserve user fonts in profile if already present, otherwise apply defaults
    if "fonts" not in data["appearance"] or not data["appearance"]["fonts"]:
        data["appearance"]["fonts"] = {}
        for font_key, font_val in cfg["fonts"].items():
            data["appearance"]["fonts"][font_key] = font_val

    if "bar" not in data:
        data["bar"] = {}
    data["bar"]["cornerStyle"] = cfg["bar_corner_style"]
    data["bar"]["bottom"] = cfg.get("bar_bottom", False)
    data["bar"]["height"] = cfg.get("bar_height", 44 if target_theme == "plasma" else (24 if target_theme == "retro" else 40))

    if "workspaces" not in data["bar"]:
        data["bar"]["workspaces"] = {}
    data["bar"]["workspaces"]["showAppIcons"] = cfg["show_app_icons"]
    data["bar"]["workspaces"]["alwaysShowNumbers"] = cfg.get("always_show_numbers", True)

    # Restaurar el wallpaper persistente del tema objetivo
    wp = get_theme_wallpaper(target_theme)
    if "background" not in data:
        data["background"] = {}
    data["background"]["wallpaperPath"] = wp

    # Guardar en config.json activo y en el perfil
    for target in [II_CONFIG_JSON, REPO_II_CONFIG_JSON]:
        if target.parent.exists():
            try:
                with open(target, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[Warning] No se pudo escribir en {target}: {e}", file=sys.stderr)

    try:
        with open(profile, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def update_hypr_theme_lua(theme_name: str, cfg: dict):
    """Writes config/hypr/modules/theme.lua."""
    gaps_out_val = cfg["gaps_out"]
    if isinstance(gaps_out_val, dict):
        gaps_out_str = f"{{ top = {gaps_out_val.get('top', 5)}, right = {gaps_out_val.get('right', 5)}, bottom = {gaps_out_val.get('bottom', 5)}, left = {gaps_out_val.get('left', 5)} }}"
    elif isinstance(gaps_out_val, str) and "{" in gaps_out_val:
        gaps_out_str = gaps_out_val
    else:
        gaps_out_str = str(gaps_out_val)

    content = f"""-- =============================================================================
-- Better Window Manager (BWM) - Configuración del Tema Activo
-- Archivo gestionado automáticamente por bwm-theme-manager.py
-- =============================================================================

local theme = {{
    name = "{theme_name}",
    rounding = {cfg['rounding']},
    rounding_power = {cfg['rounding_power']},
    border_size = {cfg['border_size']},
    gaps_in = {cfg['gaps_in']},
    gaps_out = {gaps_out_str},
}}

return theme
"""
    for target in [HYPR_THEME_LUA, REPO_HYPR_THEME_LUA]:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"[Warning] No se pudo escribir en {target}: {e}", file=sys.stderr)

def update_btop_conf(theme_name: str, cfg: dict):
    """Updates rounded_corners in btop.conf."""
    rounded_str = "True" if cfg["btop_rounded"] else "False"
    for target in [BTOP_CONF, REPO_BTOP_CONF]:
        if not target.exists():
            continue
        try:
            with open(target, "r", encoding="utf-8") as f:
                lines = f.readlines()
            new_lines = []
            found = False
            for line in lines:
                if line.strip().startswith("rounded_corners"):
                    new_lines.append(f"rounded_corners = {rounded_str}\n")
                    found = True
                else:
                    new_lines.append(line)
            if not found:
                new_lines.append(f"rounded_corners = {rounded_str}\n")
            with open(target, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
        except Exception as e:
            print(f"[Warning] Error actualizando {target}: {e}", file=sys.stderr)

def extract_vivid_palette(img_path: str):
    """Extracts a vivid, high-saturation palette from a wallpaper for Retro mode."""
    if not os.path.exists(img_path):
        return None
    try:
        img = Image.open(img_path).convert("RGB").resize((120, 120))
        colors = img.getcolors(15000)
        
        bins = defaultdict(lambda: {"weight": 0.0, "count": 0, "samples": []})
        
        for count, (r, g, b) in colors:
            h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
            
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
            accent = f"#{int(r_v*255):02x}{int(g_v*255):02x}{int(b_v*255):02x}"
        
        h_sec = (h + 0.12) % 1.0
        r_sec, g_sec, b_sec = colorsys.hls_to_rgb(h_sec, min(0.68, max(0.50, l)), s_vivid)
        secondary = f"#{int(r_sec*255):02x}{int(g_sec*255):02x}{int(b_sec*255):02x}"
        
        r_bg, g_bg, b_bg = colorsys.hls_to_rgb(h, 0.05, 0.25)
        bg = f"#{int(r_bg*255):02x}{int(g_bg*255):02x}{int(b_bg*255):02x}"
        
        hues = [0.0, 0.33, 0.14, 0.58, 0.83, 0.50]
        term = [bg]
        for hu in hues:
            cr, cg, cb = colorsys.hls_to_rgb(hu, 0.60, 0.90)
            term.append(f"#{int(cr*255):02x}{int(cg*255):02x}{int(cb*255):02x}")
        term.append("#f8fafc")
        term.append("#475569")
        for hu in hues:
            cr, cg, cb = colorsys.hls_to_rgb(hu, 0.70, 0.95)
            term.append(f"#{int(cr*255):02x}{int(cg*255):02x}{int(cb*255):02x}")
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
        return None

def apply_retro_kitty_colors(palette: dict):
    """Writes Kitty terminal colors config from extracted palette."""
    cols = palette["colors"]
    content = f"""# Omarchy Vibrant Colors for Kitty (Synced with Wallpaper)
background {palette['bg']}
foreground {palette['fg']}
selection_background {palette['colors'][8]}
selection_foreground #ffffff
cursor {palette['accent']}
cursor_text_color {palette['bg']}
url_color {palette['accent']}

# Tabs
active_tab_background {palette['accent']}
active_tab_foreground {palette['bg']}
inactive_tab_background {palette['colors'][0]}
inactive_tab_foreground {palette['fg']}

# Normal colors
color0  {cols[0]}
color1  {cols[1]}
color2  {cols[2]}
color3  {cols[3]}
color4  {cols[4]}
color5  {cols[5]}
color6  {cols[6]}
color7  {cols[7]}

# Bright colors
color8  {cols[8]}
color9  {cols[9]}
color10 {cols[10]}
color11 {cols[11]}
color12 {cols[12]}
color13 {cols[13]}
color14 {cols[14]}
color15 {cols[15]}

# Window borders
active_border_color {palette['border']}
inactive_border_color {cols[8]}
"""
    for target in [KITTY_COLORS_CONF, REPO_KITTY_COLORS_CONF]:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"[Warning] No se pudo escribir en {target}: {e}", file=sys.stderr)

    try:
        subprocess.run(["pkill", "-SIGUSR1", "kitty"], check=False)
    except Exception:
        pass

def apply_plasma_colors():
    """
    Applies the official static KDE Plasma 6 Breeze Dark palette to Kitty,
    Rofi, and Hyprland. Independent of wallpaper changes.
    """
    # 1. Kitty Terminal Breeze Dark palette
    kitty_content = """# KDE Plasma Breeze Dark Colors for Kitty (Fixed Palette)
background #24292e
foreground #eff0f1
selection_background #3daee9
selection_foreground #ffffff
cursor #3daee9
cursor_text_color #24292e
url_color #3daee9

# Tabs
active_tab_background #3daee9
active_tab_foreground #ffffff
inactive_tab_background #31363b
inactive_tab_foreground #bdc3c7

# Normal colors (Breeze Dark Konsole)
color0  #232629
color1  #ed1515
color2  #11d116
color3  #f67400
color4  #1d99f3
color5  #9b59b6
color6  #1abc9c
color7  #eff0f1

# Bright colors
color8  #7f8c8d
color9  #c0392b
color10 #27ae60
color11 #fdbc4b
color12 #3daee9
color13 #8e44ad
color14 #16a085
color15 #ffffff

# Window borders
active_border_color #31363b
inactive_border_color #31363b
"""
    for target in [KITTY_COLORS_CONF, REPO_KITTY_COLORS_CONF]:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(kitty_content)
        except Exception as e:
            print(f"[Warning] No se pudo escribir en {target}: {e}", file=sys.stderr)

    try:
        subprocess.run(["pkill", "-SIGUSR1", "kitty"], check=False)
    except Exception:
        pass

    # 2. Hyprland plasma_colors.lua
    lua_content = """-- Generado por bwm-theme-manager.py para el tema KDE Plasma (Breeze Dark estático)
local plasma_colors = {
    accent = "rgba(3daee9ee)",
    secondary = "rgba(3daee9ee)",
    bg = "rgba(24292eee)",
    border = "rgba(31363baa)",
    border_inactive = "rgba(31363baa)",
}
return plasma_colors
"""
    for target in [HYPR_PLASMA_COLORS_LUA, REPO_HYPR_PLASMA_COLORS_LUA]:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(lua_content)
        except Exception as e:
            print(f"[Warning] Error guardando {target}: {e}", file=sys.stderr)

    # 3. Rofi plasma-colors.rasi
    rofi_colors = """* {
    accent: #3daee9;
    secondary: #1d99f3;
    bg: #24292ef4;
    bg-card: #31363b;
    bg-input: #1e2227;
    fg: #eff0f1;
    muted: #bdc3c7;
    dim: #7f8c8d;
    border: #3daee9;
    bg-selected-text: #ffffff;
}
"""
    for target in [CONFIG_DIR / "rofi" / "plasma-colors.rasi", REPO_DIR / "config" / "rofi" / "plasma-colors.rasi"]:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(rofi_colors)
        except Exception as e:
            print(f"[Warning] Error guardando {target}: {e}", file=sys.stderr)

def apply_retro_wallpaper_colors(wallpaper_path: str = None):
    """Applies a vivid, saturated Omarchy palette to Kitty, Quickshell retro-colors.json, and Hyprland."""
    wp = wallpaper_path
    if not wp:
        try:
            cache_file = Path.home() / ".cache" / "current_wallpaper"
            if cache_file.exists():
                with open(cache_file, "r") as f:
                    wp = f.read().strip()
        except Exception:
            wp = None

    if not wp or not os.path.exists(wp):
        wp = str(WALLPAPERS_DIR / "omarchy-frost.jpg")

    palette = extract_vivid_palette(wp)
    if not palette:
        return

    # 1. Kitty Terminal
    apply_retro_kitty_colors(palette)

    # 2. Quickshell retro-colors.json
    try:
        RETRO_COLORS_JSON.parent.mkdir(parents=True, exist_ok=True)
        retro_data = {
            "accent": palette["accent"],
            "secondary": palette["secondary"],
            "bg": palette["bg"],
            "border": palette["border"],
            "fg": palette["fg"],
            "dim": "#475569",
            "muted": "#94a3b8"
        }
        tmp_target = RETRO_COLORS_JSON.with_suffix(".tmp")
        with open(tmp_target, "w", encoding="utf-8") as f:
            json.dump(retro_data, f, indent=2)
        os.replace(tmp_target, RETRO_COLORS_JSON)
    except Exception as e:
        print(f"[Warning] Error guardando {RETRO_COLORS_JSON}: {e}", file=sys.stderr)

    # 3. Hyprland retro_colors.lua
    hex_acc = palette["accent"].lstrip("#")
    hex_sec = palette["secondary"].lstrip("#")
    hex_bg = palette["bg"].lstrip("#")
    lua_content = f"""-- Generado automáticamente por bwm-theme-manager.py a partir del wallpaper
local retro_colors = {{
    accent = "rgba({hex_acc}ee)",
    secondary = "rgba({hex_sec}ee)",
    bg = "rgba({hex_bg}ee)",
    border = "rgba({hex_acc}ee)",
    border_inactive = "rgba(101520aa)",
}}
return retro_colors
"""
    for target in [HYPR_RETRO_COLORS_LUA, REPO_HYPR_RETRO_COLORS_LUA]:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(lua_content)
        except Exception as e:
            print(f"[Warning] Error guardando {target}: {e}", file=sys.stderr)

    # 4. Rofi Omarchy omarchy-colors.rasi
    rofi_colors = f"""* {{
    accent: {palette['accent']};
    secondary: {palette['secondary']};
    bg: {palette['bg']}f5;
    bg-input: #121820;
    fg: {palette['fg']};
    muted: #94a3b8;
    dim: #475569;
    bg-selected-text: #090c0f;
}}
"""
    rofi_colors_path = CONFIG_DIR / "rofi" / "omarchy-colors.rasi"
    repo_rofi_colors_path = REPO_DIR / "config" / "rofi" / "omarchy-colors.rasi"
    for target in [rofi_colors_path, repo_rofi_colors_path]:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(rofi_colors)
        except Exception as e:
            print(f"[Warning] Error guardando {target}: {e}", file=sys.stderr)

    # 5. Trigger reload in Hyprland and Quickshell
    try:
        subprocess.run(["hyprctl", "reload"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
    try:
        subprocess.run(["quickshell", "-c", "ii", "ipc", "call", "theme", "reload"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["quickshell", "-c", "ii", "ipc", "call", "retro", "reload"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def sync_floating_windows(to_plasma: bool):
    """
    Transitions window tiling/floating mode between themes:
    - to_plasma=True: Makes all open windows floating (non-tiling layout) and adds top draggable groupbars.
    - to_plasma=False: Ungroups windows and restores tiled layout for windows that aren't marked as persistent float in persistent_rules.json.
    """
    try:
        res = subprocess.run(["hyprctl", "clients", "-j"], capture_output=True, text=True, timeout=2)
        clients = json.loads(res.stdout)
    except Exception as e:
        print(f"[Warning] Error consultando clientes de Hyprland: {e}", file=sys.stderr)
        return

    plugin_path = str(CONFIG_DIR / "hypr" / "plugins" / "hyprbars.so")
    if to_plasma:
        subprocess.run(["hyprctl", "plugin", "load", plugin_path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["hyprctl", "keyword", "plugin:hyprbars:enabled", "true"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        # DO NOT unload plugins dynamically at runtime to prevent compositor segfaults
        subprocess.run(["hyprctl", "keyword", "plugin:hyprbars:enabled", "false"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    persistent_float_classes = set()
    persist_json = CONFIG_DIR / "hypr" / "persistent_rules.json"
    if persist_json.exists():
        try:
            with open(persist_json, "r", encoding="utf-8") as f:
                rules = json.load(f)
                for k, v in rules.items():
                    if v.get("float", True):
                        c = v.get("match", {}).get("class", "")
                        clean_c = c.replace("^", "").replace("$", "").replace("\\", "")
                        if clean_c:
                            persistent_float_classes.add(clean_c)
        except Exception:
            pass

    for client in clients:
        addr = client.get("address")
        cls = client.get("class", "")
        is_floating = client.get("floating", False)
        grouped = client.get("grouped", [])
        if not addr:
            continue

        is_terminal = any(term in cls.lower() for term in ["kitty", "alacritty", "xterm", "foot", "wezterm", "ghostty"])

        if to_plasma:
            # 1. Todas las ventanas en modo flotante individual
            if not is_floating:
                subprocess.run(["hyprctl", "dispatch", f'hl.dsp.focus({{ window = "address:{addr}" }})'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["hyprctl", "dispatch", 'hl.dsp.window.float({ action = "set" })'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # 2. Asegurar que NINGUNA ventana esté agrupada (todas 100% individuales)
            if len(grouped) > 0:
                subprocess.run(["hyprctl", "dispatch", f'hl.dsp.focus({{ window = "address:{addr}" }})'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["hyprctl", "dispatch", 'hl.dsp.group.toggle()'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            # Al salir de plasma: desagrupar cualquier grupo remanente
            if len(grouped) > 0:
                subprocess.run(["hyprctl", "dispatch", f'hl.dsp.focus({{ window = "address:{addr}" }})'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["hyprctl", "dispatch", 'hl.dsp.group.toggle()'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Restaurar mosaico si la ventana no estaba guardada como flotante persistente
            is_persistent = False
            for p_cls in persistent_float_classes:
                if p_cls.lower() in cls.lower():
                    is_persistent = True
                    break
            if not is_persistent and is_floating:
                subprocess.run(["hyprctl", "dispatch", f'hl.dsp.focus({{ window = "address:{addr}" }})'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["hyprctl", "dispatch", 'hl.dsp.window.float({ action = "unset" })'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def apply_theme(theme_name: str):
    """Applies theme across all subsystems, with complete isolation."""
    if theme_name not in THEMES:
        print(f"Error: Tema '{theme_name}' no reconocido. Opciones: {list(THEMES.keys())}", file=sys.stderr)
        sys.exit(1)

    curr_theme = get_current_theme()
    cfg = THEMES[theme_name]
    print(f"Aplicando tema: {cfg['title']}...")

    # 1. Guardar la configuración del tema actual antes de cambiar
    save_current_theme_config(curr_theme)

    # 2. Cargar el perfil de configuración aislado del tema seleccionado
    load_theme_config(theme_name, cfg)

    # 3. Actualizar configuraciones de Hyprland y btop
    update_hypr_theme_lua(theme_name, cfg)
    update_btop_conf(theme_name, cfg)

    # 4. Aplicar Wallpaper Persistente y Esquema de Colores
    wp = get_theme_wallpaper(theme_name)
    set_wp_script = CONFIG_DIR / "hypr" / "scripts" / "set-wallpaper.sh"

    # Actualizar cachés con el wallpaper persistente
    try:
        with open(Path.home() / ".cache" / "current_wallpaper", "w", encoding="utf-8") as f:
            f.write(wp)
        with open(Path.home() / ".cache" / f"current_wallpaper_{theme_name}", "w", encoding="utf-8") as f:
            f.write(wp)
    except Exception:
        pass

    if wp and os.path.exists(wp) and set_wp_script.exists():
        subprocess.run([str(set_wp_script), wp], check=False)

    if cfg.get("is_plasma"):
        apply_plasma_colors()
    elif cfg.get("is_retro"):
        apply_retro_wallpaper_colors(wp)

    # 5. Sincronizar el estado flotante / mosaico de las ventanas abiertas
    sync_floating_windows(cfg.get("is_plasma", False))

    # 6. Recargar Hyprland y Quickshell
    try:
        subprocess.run(["hyprctl", "reload"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    try:
        subprocess.run(["quickshell", "-c", "ii", "ipc", "call", "theme", "reload"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # Reiniciar Quickshell para aplicar altura de barra, orientación inferior y diseño
    try:
        subprocess.run(["pkill", "quickshell"], check=False)
        import time
        time.sleep(0.4)
        subprocess.Popen(["quickshell", "-c", "ii"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    except Exception:
        pass

    print(f"✓ Tema '{theme_name}' aplicado correctamente con configuración aislada.")

def main():
    parser = argparse.ArgumentParser(description="Gestor de temas de BWM")
    subparsers = parser.add_subparsers(dest="action")

    subparsers.add_parser("get", help="Obtener tema actual")
    subparsers.add_parser("list", help="Listar temas disponibles")
    subparsers.add_parser("toggle", help="Alternar entre temas (Default -> Retro -> Plasma)")

    set_parser = subparsers.add_parser("set", help="Activar un tema específico")
    set_parser.add_argument("theme", choices=list(THEMES.keys()), help="Nombre del tema")

    col_parser = subparsers.add_parser("apply-wallpaper-colors", help="Aplicar colores vivos a partir del wallpaper (Retro)")
    col_parser.add_argument("wallpaper", help="Ruta al wallpaper")

    subparsers.add_parser("apply-plasma-colors", help="Aplicar colores Breeze Dark estáticos (Plasma)")

    args = parser.parse_args()

    if args.action == "get":
        print(get_current_theme())
    elif args.action == "list":
        for k, v in THEMES.items():
            print(f"{k}: {v['title']} - {v['description']}")
    elif args.action == "toggle":
        curr = get_current_theme()
        cycle = ["default", "retro", "plasma"]
        try:
            idx = cycle.index(curr)
            nxt = cycle[(idx + 1) % len(cycle)]
        except ValueError:
            nxt = "default"
        apply_theme(nxt)
    elif args.action == "set":
        apply_theme(args.theme)
    elif args.action == "apply-wallpaper-colors":
        apply_retro_wallpaper_colors(args.wallpaper)
    elif args.action == "apply-plasma-colors":
        apply_plasma_colors()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
