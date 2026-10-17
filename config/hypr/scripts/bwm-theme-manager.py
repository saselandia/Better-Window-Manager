#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BWM Theme Manager (Better Window Manager)
Manages and switches themes between Default (Material You) and Retro variants
(Frost Cyan, Ash Dark Rose, Cyberpunk Neon).
Synchronizes Quickshell, Hyprland window decorations, fonts, btop, Kitty, and wallpapers.
"""

import sys
import os
import json
import argparse
import subprocess
from pathlib import Path

CONFIG_DIR = Path.home() / ".config"
HYPR_THEME_LUA = CONFIG_DIR / "hypr" / "modules" / "theme.lua"
II_CONFIG_JSON = CONFIG_DIR / "illogical-impulse" / "config.json"
BTOP_CONF = CONFIG_DIR / "btop" / "btop.conf"

REPO_DIR = Path("/mnt/HDD1TB/Projects/hyprland-de")
REPO_HYPR_THEME_LUA = REPO_DIR / "config" / "hypr" / "modules" / "theme.lua"
REPO_II_CONFIG_JSON = REPO_DIR / "config" / "illogical-impulse" / "config.json"
REPO_BTOP_CONF = REPO_DIR / "config" / "btop" / "btop.conf"

WALLPAPERS_DIR = Path.home() / "Pictures" / "Wallpapers"

THEMES = {
    "default": {
        "title": "Default (Material You)",
        "description": "Estilo Material 3 / End_4 con esquinas redondeadas y fuentes sans-serif",
        "wallpaper": str(WALLPAPERS_DIR / "default.jpg"),
        "rounding": 14,
        "rounding_power": 2,
        "border_size": 2,
        "gaps_in": 4,
        "gaps_out": 8,
        "bar_corner_style": 2,
        "show_app_icons": True,
        "is_retro": False,
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
        "title": "Retro Frost (Omarchy Cyan)",
        "description": "Estilo minimalista Omarchy con paleta Frost cian, barra compacta de 24px y bordes rectos",
        "wallpaper": str(WALLPAPERS_DIR / "omarchy-frost.jpg"),
        "rounding": 0,
        "rounding_power": 2,
        "border_size": 2,
        "gaps_in": 3,
        "gaps_out": 5,
        "bar_corner_style": 2,
        "show_app_icons": False,
        "is_retro": True,
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
    "retro-ash": {
        "title": "Retro Ash (Omarchy Dark Rose)",
        "description": "Estilo minimalista Omarchy con paleta carbón y fondo dark rose",
        "wallpaper": str(WALLPAPERS_DIR / "omarchy-ash.jpg"),
        "rounding": 0,
        "rounding_power": 2,
        "border_size": 2,
        "gaps_in": 3,
        "gaps_out": 5,
        "bar_corner_style": 2,
        "show_app_icons": False,
        "is_retro": True,
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
    "retro-cyberpunk": {
        "title": "Retro Cyberpunk (Omarchy Neon)",
        "description": "Estilo minimalista Omarchy con tonos neón y fondo cyberpunk",
        "wallpaper": str(WALLPAPERS_DIR / "cyberpunk.jpg"),
        "rounding": 0,
        "rounding_power": 2,
        "border_size": 2,
        "gaps_in": 3,
        "gaps_out": 5,
        "bar_corner_style": 2,
        "show_app_icons": False,
        "is_retro": True,
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
    }
}

def get_current_theme() -> str:
    """Reads current theme name from II config or Hyprland theme.lua."""
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
    if II_CONFIG_JSON.exists():
        try:
            with open(II_CONFIG_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                theme = data.get("appearance", {}).get("bwmTheme")
                if theme in THEMES:
                    return theme
        except Exception:
            pass
    return "default"

def update_hypr_theme_lua(theme_name: str, cfg: dict):
    """Writes config/hypr/modules/theme.lua."""
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
    gaps_out = {cfg['gaps_out']},
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

def update_ii_config_json(theme_name: str, cfg: dict):
    """Updates appearance and bar in illogical-impulse config.json."""
    bwm_flag = "retro" if cfg.get("is_retro", False) else "default"
    for target in [II_CONFIG_JSON, REPO_II_CONFIG_JSON]:
        if not target.exists():
            continue
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if "appearance" not in data:
                data["appearance"] = {}
            data["appearance"]["bwmTheme"] = bwm_flag
            
            if "fonts" not in data["appearance"]:
                data["appearance"]["fonts"] = {}
            for font_key, font_val in cfg["fonts"].items():
                data["appearance"]["fonts"][font_key] = font_val

            if "bar" not in data:
                data["bar"] = {}
            data["bar"]["cornerStyle"] = cfg["bar_corner_style"]

            if "workspaces" not in data["bar"]:
                data["bar"]["workspaces"] = {}
            data["bar"]["workspaces"]["showAppIcons"] = cfg["show_app_icons"]
            data["bar"]["workspaces"]["alwaysShowNumbers"] = True

            with open(target, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Warning] Error actualizando {target}: {e}", file=sys.stderr)

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

def apply_theme(theme_name: str):
    """Applies theme across all subsystems."""
    if theme_name not in THEMES:
        print(f"Error: Tema '{theme_name}' no reconocido. Opciones: {list(THEMES.keys())}", file=sys.stderr)
        sys.exit(1)

    cfg = THEMES[theme_name]
    print(f"Aplicando tema: {cfg['title']}...")

    update_hypr_theme_lua(theme_name, cfg)
    update_ii_config_json(theme_name, cfg)
    update_btop_conf(theme_name, cfg)

    # Aplicar wallpaper específico del tema si existe (lo que regenera Matugen para todo el sistema)
    wp = cfg.get("wallpaper")
    set_wp_script = CONFIG_DIR / "hypr" / "scripts" / "set-wallpaper.sh"
    if wp and os.path.exists(wp) and set_wp_script.exists():
        subprocess.run([str(set_wp_script), wp], check=False)
    else:
        # Recargar Hyprland y Quickshell si no se ejecutó set-wallpaper
        try:
            subprocess.run(["hyprctl", "reload"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

        try:
            subprocess.run(["quickshell", "-c", "ii", "ipc", "call", "theme", "reload"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    # Reiniciar Quickshell para aplicar altura de barra y diseño de barra
    try:
        subprocess.run(["pkill", "quickshell"], check=False)
        import time
        time.sleep(0.5)
        subprocess.Popen(["quickshell", "-c", "ii"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    except Exception:
        pass

    # Notificación al usuario
    try:
        subprocess.run([
            "notify-send",
            "BWM Theme Manager",
            f"Tema activado: {cfg['title']}",
            "-i", "preferences-desktop-theme",
            "-a", "BWM"
        ], check=False)
    except Exception:
        pass

    print(f"✓ Tema '{theme_name}' aplicado correctamente.")

def main():
    parser = argparse.ArgumentParser(description="Gestor de temas de BWM")
    subparsers = parser.add_subparsers(dest="action")

    subparsers.add_parser("get", help="Obtener tema actual")
    subparsers.add_parser("list", help="Listar temas disponibles")
    subparsers.add_parser("toggle", help="Alternar entre temas")

    set_parser = subparsers.add_parser("set", help="Activar un tema específico")
    set_parser.add_argument("theme", choices=list(THEMES.keys()), help="Nombre del tema")

    args = parser.parse_args()

    if args.action == "get":
        print(get_current_theme())
    elif args.action == "list":
        for k, v in THEMES.items():
            print(f"{k}: {v['title']} - {v['description']}")
    elif args.action == "toggle":
        curr = get_current_theme()
        nxt = "retro" if curr == "default" else "default"
        apply_theme(nxt)
    elif args.action == "set":
        apply_theme(args.theme)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
