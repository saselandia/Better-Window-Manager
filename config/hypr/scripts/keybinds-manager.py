#!/usr/bin/env python3
"""
Keybinds Manager for Hyprland & Quickshell Settings
Manages keybindings via ~/.config/hypr/keybinds.json
Compiles to ~/.config/hypr/modules/user_binds.lua and reloads Hyprland.
"""

import sys
import os
import json
import re
import argparse
import subprocess
import time
import copy
from typing import List, Dict, Any, Optional

CONFIG_DIR = os.path.expanduser("~/.config/hypr")
JSON_PATH = os.path.join(CONFIG_DIR, "keybinds.json")
LUA_PATH = os.path.join(CONFIG_DIR, "modules", "user_binds.lua")

# Factory default keybindings
DEFAULT_KEYBINDS: List[Dict[str, Any]] = [
    # 1. General
    {
        "id": "cheatsheet",
        "category": "General",
        "description": "Guía de atajos (Cheatsheet)",
        "mods": ["ALT"],
        "key": "A",
        "action_type": "exec",
        "exec": "quickshell -c ii ipc call cheatsheet toggle",
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {},
        "is_default": True,
        "enabled": True
    },
    # 2. Lanzadores
    {
        "id": "terminal",
        "category": "Lanzadores",
        "description": "Abrir terminal (Kitty)",
        "mods": ["CTRL"],
        "key": "RETURN",
        "action_type": "exec",
        "exec": "kitty",
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "app_menu",
        "category": "Lanzadores",
        "description": "Menú de aplicaciones / Búsqueda",
        "mods": ["SUPER"],
        "key": "SUPER_L",
        "action_type": "exec",
        "exec": "quickshell -c ii ipc call search toggle || rofi -show drun",
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {"release": True},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "file_manager",
        "category": "Lanzadores",
        "description": "Explorador de archivos (Nautilus)",
        "mods": ["SUPER"],
        "key": "E",
        "action_type": "exec",
        "exec": "nautilus",
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "file_manager_alt",
        "category": "Lanzadores",
        "description": "Explorador de archivos alternativo (Alt+E)",
        "mods": ["ALT"],
        "key": "E",
        "action_type": "exec",
        "exec": "nautilus",
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "wallpaper_picker",
        "category": "Lanzadores",
        "description": "Selector de fondos de pantalla",
        "mods": ["ALT"],
        "key": "W",
        "action_type": "exec",
        "exec": os.path.expanduser("~/.config/hypr/scripts/wallpaper-picker.sh"),
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {},
        "is_default": True,
        "enabled": True
    },
    # 3. Ventanas
    {
        "id": "window_close",
        "category": "Ventanas",
        "description": "Cerrar ventana activa",
        "mods": ["ALT"],
        "key": "X",
        "action_type": "dispatcher",
        "exec": None,
        "dispatcher": "window.close",
        "dispatcher_arg": None,
        "options": {},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "window_toggle_float_persist",
        "category": "Ventanas",
        "description": "Recordar regla flotante persistente",
        "mods": ["ALT"],
        "key": "Q",
        "action_type": "exec",
        "exec": os.path.expanduser("~/.config/hypr/scripts/toggle-float-persistent.py"),
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "window_togglesplit",
        "category": "Ventanas",
        "description": "Alternar división horizontal/vertical (Split)",
        "mods": ["ALT"],
        "key": "J",
        "action_type": "dispatcher",
        "exec": None,
        "dispatcher": "layout",
        "dispatcher_arg": "togglesplit",
        "options": {},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "window_fullscreen",
        "category": "Ventanas",
        "description": "Alternar pantalla completa",
        "mods": ["ALT"],
        "key": "RETURN",
        "action_type": "dispatcher",
        "exec": None,
        "dispatcher": "window.fullscreen",
        "dispatcher_arg": None,
        "options": {},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "alt_tab",
        "category": "Ventanas",
        "description": "Selector visual de ventanas (Alt+Tab)",
        "mods": ["ALT"],
        "key": "TAB",
        "action_type": "exec",
        "exec": "quickshell -c ii ipc call altTab next",
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {"repeating": True},
        "is_default": True,
        "enabled": True
    },
    # 4. Navegación
    {
        "id": "focus_left",
        "category": "Navegación",
        "description": "Mover foco a la izquierda",
        "mods": ["ALT"],
        "key": "left",
        "action_type": "dispatcher",
        "exec": None,
        "dispatcher": "focus_direction",
        "dispatcher_arg": "left",
        "options": {},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "focus_right",
        "category": "Navegación",
        "description": "Mover foco a la derecha",
        "mods": ["ALT"],
        "key": "right",
        "action_type": "dispatcher",
        "exec": None,
        "dispatcher": "focus_direction",
        "dispatcher_arg": "right",
        "options": {},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "focus_up",
        "category": "Navegación",
        "description": "Mover foco hacia arriba",
        "mods": ["ALT"],
        "key": "up",
        "action_type": "dispatcher",
        "exec": None,
        "dispatcher": "focus_direction",
        "dispatcher_arg": "up",
        "options": {},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "focus_down",
        "category": "Navegación",
        "description": "Mover foco hacia abajo",
        "mods": ["ALT"],
        "key": "down",
        "action_type": "dispatcher",
        "exec": None,
        "dispatcher": "focus_direction",
        "dispatcher_arg": "down",
        "options": {},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "move_win_left",
        "category": "Navegación",
        "description": "Mover ventana a la izquierda",
        "mods": ["CTRL"],
        "key": "left",
        "action_type": "dispatcher",
        "exec": None,
        "dispatcher": "window_move_direction",
        "dispatcher_arg": "left",
        "options": {"repeating": True},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "move_win_right",
        "category": "Navegación",
        "description": "Mover ventana a la derecha",
        "mods": ["CTRL"],
        "key": "right",
        "action_type": "dispatcher",
        "exec": None,
        "dispatcher": "window_move_direction",
        "dispatcher_arg": "right",
        "options": {"repeating": True},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "move_win_up",
        "category": "Navegación",
        "description": "Mover ventana hacia arriba",
        "mods": ["CTRL"],
        "key": "up",
        "action_type": "dispatcher",
        "exec": None,
        "dispatcher": "window_move_direction",
        "dispatcher_arg": "up",
        "options": {"repeating": True},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "move_win_down",
        "category": "Navegación",
        "description": "Mover ventana hacia abajo",
        "mods": ["CTRL"],
        "key": "down",
        "action_type": "dispatcher",
        "exec": None,
        "dispatcher": "window_move_direction",
        "dispatcher_arg": "down",
        "options": {"repeating": True},
        "is_default": True,
        "enabled": True
    },
    # 5. Espacios de trabajo (Magic / Special)
    {
        "id": "ws_toggle_special",
        "category": "Espacios de trabajo",
        "description": "Mostrar / Ocultar espacio especial (Magic)",
        "mods": ["ALT"],
        "key": "S",
        "action_type": "dispatcher",
        "exec": None,
        "dispatcher": "workspace.toggle_special",
        "dispatcher_arg": "magic",
        "options": {},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "ws_move_special",
        "category": "Espacios de trabajo",
        "description": "Enviar ventana al espacio especial (Magic)",
        "mods": ["ALT", "SHIFT"],
        "key": "S",
        "action_type": "dispatcher",
        "exec": None,
        "dispatcher": "workspace_window_move",
        "dispatcher_arg": "special:magic",
        "options": {},
        "is_default": True,
        "enabled": True
    },
    # 6. Sistema
    {
        "id": "sidebar_right",
        "category": "Sistema",
        "description": "Panel lateral / Ajustes rápidos",
        "mods": ["SUPER"],
        "key": "A",
        "action_type": "exec",
        "exec": "quickshell -c ii ipc call sidebarRight toggle",
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "open_settings",
        "category": "Sistema",
        "description": "Configuración del sistema (Settings)",
        "mods": ["SUPER"],
        "key": "I",
        "action_type": "exec",
        "exec": "qs -p " + os.path.expanduser("~/.config/quickshell/ii/settings.qml"),
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "open_autostart",
        "category": "Sistema",
        "description": "Gestor de inicio automático (Autostart)",
        "mods": ["SUPER", "ALT"],
        "key": "A",
        "action_type": "exec",
        "exec": os.path.expanduser("~/.config/hypr/scripts/open-autostart.sh"),
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "screen_lock",
        "category": "Sistema",
        "description": "Bloquear pantalla",
        "mods": ["SUPER"],
        "key": "L",
        "action_type": "exec",
        "exec": "quickshell -c ii ipc call lock activate",
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "screenshot_print",
        "category": "Sistema",
        "description": "Captura de pantalla por región (Print)",
        "mods": [],
        "key": "Print",
        "action_type": "exec",
        "exec": "quickshell -c ii ipc call region screenshot",
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "screenshot_super",
        "category": "Sistema",
        "description": "Captura de pantalla alternativa (Super+Shift+S)",
        "mods": ["SUPER", "SHIFT"],
        "key": "S",
        "action_type": "exec",
        "exec": "quickshell -c ii ipc call region screenshot",
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "session_exit",
        "category": "Sistema",
        "description": "Menú de apagado / Salir de sesión",
        "mods": ["ALT"],
        "key": "M",
        "action_type": "exec",
        "exec": "command -v hyprshutdown >/dev/null 2>&1 && hyprshutdown || hyprctl dispatch 'hl.dsp.exit()'",
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {},
        "is_default": True,
        "enabled": True
    },
    # 7. Multimedia
    {
        "id": "vol_up",
        "category": "Multimedia",
        "description": "Subir volumen",
        "mods": [],
        "key": "XF86AudioRaiseVolume",
        "action_type": "exec",
        "exec": "wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+",
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {"locked": True, "repeating": True},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "vol_down",
        "category": "Multimedia",
        "description": "Bajar volumen",
        "mods": [],
        "key": "XF86AudioLowerVolume",
        "action_type": "exec",
        "exec": "wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-",
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {"locked": True, "repeating": True},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "vol_mute",
        "category": "Multimedia",
        "description": "Silenciar audio",
        "mods": [],
        "key": "XF86AudioMute",
        "action_type": "exec",
        "exec": "wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle",
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {"locked": True},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "mic_mute",
        "category": "Multimedia",
        "description": "Silenciar micrófono",
        "mods": [],
        "key": "XF86AudioMicMute",
        "action_type": "exec",
        "exec": "wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle",
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {"locked": True},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "bright_up",
        "category": "Multimedia",
        "description": "Subir brillo de pantalla",
        "mods": [],
        "key": "XF86MonBrightnessUp",
        "action_type": "exec",
        "exec": "quickshell -c ii ipc call brightness increment",
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {"locked": True, "repeating": True},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "bright_down",
        "category": "Multimedia",
        "description": "Bajar brillo de pantalla",
        "mods": [],
        "key": "XF86MonBrightnessDown",
        "action_type": "exec",
        "exec": "quickshell -c ii ipc call brightness decrement",
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {"locked": True, "repeating": True},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "media_play",
        "category": "Multimedia",
        "description": "Reproducir / Pausar",
        "mods": [],
        "key": "XF86AudioPlay",
        "action_type": "exec",
        "exec": "playerctl play-pause",
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {"locked": True},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "media_next",
        "category": "Multimedia",
        "description": "Pista siguiente",
        "mods": [],
        "key": "XF86AudioNext",
        "action_type": "exec",
        "exec": "playerctl next",
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {"locked": True},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "media_prev",
        "category": "Multimedia",
        "description": "Pista anterior",
        "mods": [],
        "key": "XF86AudioPrev",
        "action_type": "exec",
        "exec": "playerctl previous",
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {"locked": True},
        "is_default": True,
        "enabled": True
    },
    {
        "id": "media_stop",
        "category": "Multimedia",
        "description": "Detener reproducción",
        "mods": [],
        "key": "XF86AudioStop",
        "action_type": "exec",
        "exec": "playerctl stop",
        "dispatcher": None,
        "dispatcher_arg": None,
        "options": {"locked": True},
        "is_default": True,
        "enabled": True
    }
]

# Generate workspaces 1-10
for i in range(1, 11):
    key_char = str(i % 10)
    DEFAULT_KEYBINDS.append({
        "id": f"ws_focus_{i}",
        "category": "Espacios de trabajo",
        "description": f"Cambiar al espacio de trabajo {i}",
        "mods": ["ALT"],
        "key": key_char,
        "action_type": "dispatcher",
        "exec": None,
        "dispatcher": "workspace_focus",
        "dispatcher_arg": str(i),
        "options": {},
        "is_default": True,
        "enabled": True
    })
    DEFAULT_KEYBINDS.append({
        "id": f"ws_move_{i}",
        "category": "Espacios de trabajo",
        "description": f"Mover ventana al espacio de trabajo {i}",
        "mods": ["ALT", "SHIFT"],
        "key": key_char,
        "action_type": "dispatcher",
        "exec": None,
        "dispatcher": "workspace_window_move",
        "dispatcher_arg": str(i),
        "options": {},
        "is_default": True,
        "enabled": True
    })

DEFAULT_DICT = {item["id"]: item for item in DEFAULT_KEYBINDS}

def load_keybinds() -> List[Dict[str, Any]]:
    """Loads keybinds from JSON, merging with defaults if needed."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(JSON_PATH):
        save_keybinds(DEFAULT_KEYBINDS)
        return copy.deepcopy(DEFAULT_KEYBINDS)
    
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list) and len(data) > 0:
            return data
    except Exception as e:
        print(f"[KeybindsManager] Error reading {JSON_PATH}: {e}", file=sys.stderr)

    return copy.deepcopy(DEFAULT_KEYBINDS)

def to_lua_string(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)

def format_combo(mods: List[str], key: str) -> str:
    """Formats modifiers and key into Hyprland format."""
    parts = [m.upper().strip() for m in mods if m.strip()]
    if key.strip():
        parts.append(key.strip())
    return " + ".join(parts)

def build_dispatcher_call(action_type: str, exec_cmd: Optional[str], dispatcher: Optional[str], dispatcher_arg: Optional[str]) -> Optional[str]:
    """Generates the Lua dispatcher call."""
    if action_type == "exec":
        if not exec_cmd or not exec_cmd.strip():
            return None
        safe_cmd = to_lua_string(exec_cmd.strip())
        return f"hl.dsp.exec_cmd({safe_cmd})"
    
    elif action_type == "dispatcher":
        d = dispatcher.strip() if dispatcher else ""
        if d == "window.close":
            return "hl.dsp.window.close()"
        elif d == "window.fullscreen":
            return 'hl.dsp.window.fullscreen({ mode = 0, action = "toggle" })'
        elif d == "window.drag":
            return "hl.dsp.window.drag()"
        elif d == "window.resize":
            return "hl.dsp.window.resize()"
        elif d == "layout" and (dispatcher_arg or "").strip() == "togglesplit":
            return 'hl.dsp.layout("togglesplit")'
        elif d == "focus_direction":
            arg = (dispatcher_arg or "left").strip()
            return f'hl.dsp.focus({{ direction = "{arg}" }})'
        elif d == "window_move_direction":
            arg = (dispatcher_arg or "left").strip()
            return f'hl.dsp.window.move({{ direction = "{arg}" }})'
        elif d == "workspace_focus":
            arg = (dispatcher_arg or "1").strip()
            return f'hl.dsp.focus({{ workspace = {arg} }})'
        elif d == "workspace_window_move":
            arg = (dispatcher_arg or "1").strip()
            if arg.isdigit():
                return f'hl.dsp.window.move({{ workspace = {arg} }})'
            else:
                return f'hl.dsp.window.move({{ workspace = "{arg}" }})'
        elif d == "workspace.toggle_special":
            arg = (dispatcher_arg or "magic").strip()
            return f'hl.dsp.workspace.toggle_special("{arg}")'
        elif d == "exit":
            return "hl.dsp.exit()"
    return None

def generate_lua(binds: List[Dict[str, Any]]) -> str:
    """Generates user_binds.lua file content."""
    lines = [
        "-- =============================================================================",
        "-- ATAJOS DE TECLADO CONFIGURADOS (HYPRLAND LUA)",
        "-- Archivo gestionado automáticamente por keybinds-manager.py",
        "-- =============================================================================",
        "",
        "local terminal    = \"kitty\"",
        "local fileManager = \"nautilus\"",
        "local menu        = \"quickshell -c ii ipc call search toggle || rofi -show drun\"",
        ""
    ]

    current_cat = None
    for b in binds:
        if not b.get("enabled", True):
            continue

        cat = b.get("category", "Otros")
        if cat != current_cat:
            current_cat = cat
            lines.append(f"-- [{cat}]")

        combo = format_combo(b.get("mods", []), b.get("key", ""))
        if not combo:
            continue

        dsp_call = build_dispatcher_call(
            b.get("action_type", "exec"),
            b.get("exec"),
            b.get("dispatcher"),
            b.get("dispatcher_arg")
        )
        if not dsp_call:
            continue

        opts = []
        desc = b.get("description", "").strip()
        if desc:
            prefix = f"{cat}: " if cat and not desc.startswith(f"{cat}:") else ""
            opts.append(f"description = {to_lua_string(prefix + desc)}")
        
        options_dict = b.get("options", {})
        for k, v in options_dict.items():
            if v is True:
                opts.append(f"{k} = true")
            elif v is False:
                opts.append(f"{k} = false")
            elif isinstance(v, (int, float)):
                opts.append(f"{k} = {v}")
            elif isinstance(v, str):
                opts.append(f"{k} = {to_lua_string(v)}")

        opts_table = f"{{ {', '.join(opts)} }}" if opts else ""
        if opts_table:
            lines.append(f"hl.bind({to_lua_string(combo)}, {dsp_call}, {opts_table})")
        else:
            lines.append(f"hl.bind({to_lua_string(combo)}, {dsp_call})")

    # Extra Alt+Tab helper releases and mouse binds
    lines.append("")
    lines.append("-- Alt+Tab Helper Releases")
    lines.append('hl.bind("ALT + SHIFT + TAB", hl.dsp.exec_cmd("quickshell -c ii ipc call altTab prev"), { repeating = true })')
    lines.append('hl.bind("Alt_L", hl.dsp.exec_cmd("quickshell -c ii ipc call altTab release"), { release = true })')
    lines.append('hl.bind("Alt_R", hl.dsp.exec_cmd("quickshell -c ii ipc call altTab release"), { release = true })')
    lines.append('hl.bind("ALT + Alt_L", hl.dsp.exec_cmd("quickshell -c ii ipc call altTab release"), { release = true })')
    lines.append('hl.bind("ALT + Alt_R", hl.dsp.exec_cmd("quickshell -c ii ipc call altTab release"), { release = true })')
    lines.append('hl.bind("ALT + Escape", hl.dsp.exec_cmd("quickshell -c ii ipc call altTab cancel"))')
    lines.append("")
    lines.append("-- Mouse Window Gestures")
    lines.append('hl.bind("ALT + mouse:272", hl.dsp.window.drag(), { mouse = true, description = "Ventanas: Arrastrar ventana flotante" })')
    lines.append('hl.bind("ALT + mouse:273", hl.dsp.window.resize(), { mouse = true, description = "Ventanas: Redimensionar ventana flotante" })')
    lines.append('hl.bind("ALT + mouse_down", hl.dsp.focus({ workspace = "e+1" }), { description = "Espacios de trabajo: Espacio de trabajo siguiente" })')
    lines.append('hl.bind("ALT + mouse_up",   hl.dsp.focus({ workspace = "e-1" }), { description = "Espacios de trabajo: Espacio de trabajo anterior" })')
    lines.append("")
    lines.append("return {}")
    lines.append("")

    return "\n".join(lines)

def save_keybinds(binds: List[Dict[str, Any]]) -> bool:
    """Saves keybinds to JSON and generates user_binds.lua."""
    os.makedirs(os.path.dirname(LUA_PATH), exist_ok=True)
    try:
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(binds, f, indent=2, ensure_ascii=False)
        
        lua_code = generate_lua(binds)
        with open(LUA_PATH, "w", encoding="utf-8") as f:
            f.write(lua_code)

        subprocess.run(["hyprctl", "reload"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print(f"[KeybindsManager] Error saving keybinds: {e}", file=sys.stderr)
        return False

def add_keybind(category: str, description: str, mods: List[str], key: str, action_type: str, exec_cmd: Optional[str] = None, dispatcher: Optional[str] = None, dispatcher_arg: Optional[str] = None) -> bool:
    """Adds a new keybind."""
    binds = load_keybinds()
    bind_id = f"custom_{int(time.time())}_{len(binds)}"
    new_bind = {
        "id": bind_id,
        "category": category.strip() or "Personalizados",
        "description": description.strip(),
        "mods": [m.strip().upper() for m in mods if m.strip()],
        "key": key.strip(),
        "action_type": action_type.strip(),
        "exec": exec_cmd.strip() if exec_cmd else None,
        "dispatcher": dispatcher.strip() if dispatcher else None,
        "dispatcher_arg": dispatcher_arg.strip() if dispatcher_arg else None,
        "options": {},
        "is_default": False,
        "enabled": True
    }
    binds.append(new_bind)
    return save_keybinds(binds)

def update_keybind(bind_id: str, mods: Optional[List[str]] = None, key: Optional[str] = None, description: Optional[str] = None, action_type: Optional[str] = None, exec_cmd: Optional[str] = None, dispatcher: Optional[str] = None, dispatcher_arg: Optional[str] = None, enabled: Optional[bool] = None) -> bool:
    """Updates an existing keybind."""
    binds = load_keybinds()
    found = False
    for b in binds:
        if b["id"] == bind_id:
            if mods is not None:
                b["mods"] = [m.strip().upper() for m in mods if m.strip()]
            if key is not None:
                b["key"] = key.strip()
            if description is not None:
                b["description"] = description.strip()
            if action_type is not None:
                b["action_type"] = action_type.strip()
            if exec_cmd is not None:
                b["exec"] = exec_cmd.strip()
            if dispatcher is not None:
                b["dispatcher"] = dispatcher.strip()
            if dispatcher_arg is not None:
                b["dispatcher_arg"] = dispatcher_arg.strip()
            if enabled is not None:
                b["enabled"] = enabled
            found = True
            break
    if not found:
        return False
    return save_keybinds(binds)

def delete_keybind(bind_id: str) -> bool:
    """Deletes custom bind or disables default bind."""
    binds = load_keybinds()
    new_binds = []
    found = False
    for b in binds:
        if b["id"] == bind_id:
            found = True
            if b.get("is_default", False):
                # Disable default bind
                b["enabled"] = False
                new_binds.append(b)
            else:
                # Custom bind: remove completely
                continue
        else:
            new_binds.append(b)
    if not found:
        return False
    return save_keybinds(new_binds)

def reset_keybind(bind_id: str) -> bool:
    """Resets a default keybind to its original setting."""
    binds = load_keybinds()
    if bind_id not in DEFAULT_DICT:
        return False
    
    default_item = copy.deepcopy(DEFAULT_DICT[bind_id])
    found = False
    for i, b in enumerate(binds):
        if b["id"] == bind_id:
            binds[i] = default_item
            found = True
            break
    if not found:
        binds.append(default_item)
    return save_keybinds(binds)

def reset_all() -> bool:
    """Restores all keybinds to defaults."""
    return save_keybinds(copy.deepcopy(DEFAULT_KEYBINDS))

def main():
    parser = argparse.ArgumentParser(description="Keybinds Manager for Hyprland & Quickshell")
    subparsers = parser.add_subparsers(dest="command")

    # list
    subparsers.add_parser("list", help="List all keybinds as JSON")

    # add
    add_p = subparsers.add_parser("add", help="Add a new keybind")
    add_p.add_argument("--category", default="Personalizados")
    add_p.add_argument("--desc", required=True)
    add_p.add_argument("--mods", default="", help="Comma-separated mods (SUPER,ALT,CTRL,SHIFT)")
    add_p.add_argument("--key", required=True)
    add_p.add_argument("--type", choices=["exec", "dispatcher"], default="exec")
    add_p.add_argument("--exec", dest="exec_cmd", default=None)
    add_p.add_argument("--dispatcher", default=None)
    add_p.add_argument("--dispatcher-arg", default=None)

    # update
    up_p = subparsers.add_parser("update", help="Update an existing keybind")
    up_p.add_argument("--id", required=True)
    up_p.add_argument("--mods", default=None)
    up_p.add_argument("--key", default=None)
    up_p.add_argument("--desc", default=None)
    up_p.add_argument("--type", choices=["exec", "dispatcher"], default=None)
    up_p.add_argument("--exec", dest="exec_cmd", default=None)
    up_p.add_argument("--dispatcher", default=None)
    up_p.add_argument("--dispatcher-arg", default=None)
    up_p.add_argument("--enabled", choices=["true", "false"], default=None)

    # delete
    del_p = subparsers.add_parser("delete", help="Delete or disable a keybind")
    del_p.add_argument("--id", required=True)

    # reset
    res_p = subparsers.add_parser("reset", help="Reset a keybind or all to defaults")
    res_p.add_argument("--id", default=None)

    # reload
    subparsers.add_parser("reload", help="Compile and reload Hyprland")

    args = parser.parse_args()

    if args.command == "list":
        print(json.dumps(load_keybinds(), indent=2, ensure_ascii=False))
    elif args.command == "add":
        mods = [m.strip() for m in args.mods.split(",") if m.strip()]
        ok = add_keybind(args.category, args.desc, mods, args.key, args.type, args.exec_cmd, args.dispatcher, args.dispatcher_arg)
        print(json.dumps({"success": ok}))
    elif args.command == "update":
        mods = [m.strip() for m in args.mods.split(",")] if args.mods is not None else None
        enabled = (args.enabled == "true") if args.enabled is not None else None
        ok = update_keybind(args.id, mods, args.key, args.desc, args.type, args.exec_cmd, args.dispatcher, args.dispatcher_arg, enabled)
        print(json.dumps({"success": ok}))
    elif args.command == "delete":
        ok = delete_keybind(args.id)
        print(json.dumps({"success": ok}))
    elif args.command == "reset":
        if args.id:
            ok = reset_keybind(args.id)
        else:
            ok = reset_all()
        print(json.dumps({"success": ok}))
    elif args.command == "reload":
        binds = load_keybinds()
        ok = save_keybinds(binds)
        print(json.dumps({"success": ok}))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
