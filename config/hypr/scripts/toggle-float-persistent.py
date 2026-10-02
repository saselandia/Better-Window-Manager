#!/usr/bin/env python3
"""
toggle-float-persistent.py
Alterna el estado flotante de la ventana activa en Hyprland y guarda/elimina
una regla de ventana persistente en ~/.config/hypr/modules/persistent_rules.lua
para que se respete en futuras aperturas (ej: lista de amigos de Steam).
"""

import json
import os
import re
import subprocess
import sys

CONFIG_DIR = os.path.expanduser("~/.config/hypr")
JSON_PATH = os.path.join(CONFIG_DIR, "persistent_rules.json")
LUA_PATH = os.path.join(CONFIG_DIR, "modules", "persistent_rules.lua")


def get_active_window():
    try:
        res = subprocess.run(
            ["hyprctl", "activewindow", "-j"],
            capture_output=True,
            text=True,
            timeout=2,
            check=True,
        )
        data = json.loads(res.stdout)
        if not data or not data.get("class"):
            return None
        return data
    except Exception:
        return None


def slugify(text):
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return clean or "window"


def classify_window(data):
    cls = (data.get("class") or "").strip()
    title = (data.get("title") or "").strip()
    init_cls = (data.get("initialClass") or "").strip()
    init_title = (data.get("initialTitle") or "").strip()

    # 1. Caso especial: Steam (subventanas de amigos/chat vs ventana principal)
    if cls == "steam" or init_cls == "steam":
        # Amigos, chat, social
        if re.search(r"friends|amigos|chat", title, re.I) or re.search(
            r"friends|amigos|chat", init_title, re.I
        ):
            return (
                "steam_friends",
                "Steam (Amigos / Chat)",
                {
                    "class": "^steam$",
                    "title": "(?i).*(friends|amigos|chat).*",
                },
            )
        # Ventana principal de Steam
        elif title.lower() == "steam" or init_title.lower() == "steam":
            return (
                "steam_main",
                "Steam (Ventana Principal)",
                {
                    "class": "^steam$",
                    "title": "^Steam$",
                },
            )
        # Otras subventanas de Steam (Capturas, Parches, Ajustes, etc.)
        else:
            slug = slugify(title)
            return (
                f"steam_{slug}",
                f"Steam ({title})",
                {
                    "class": "^steam$",
                    "title": f"^{re.escape(title)}$",
                },
            )

    # 2. Caso especial: Picture-in-Picture (Firefox, Chromium, etc.)
    if re.search(r"picture.in.picture|imagen.en.imagen", title, re.I):
        slug = slugify(cls)
        return (
            f"{slug}_pip",
            f"{cls} (Picture-in-Picture)",
            {
                "class": f"^{re.escape(cls)}$",
                "title": "(?i).*(picture.in.picture|imagen.en.imagen).*",
            },
        )

    # 3. Caso especial: Diálogos y selectores de archivos
    if re.match(r"^(Open|Save|Select|Choose|Abrir|Guardar|Elegir)\b", title, re.I):
        slug = slugify(cls)
        return (
            f"{slug}_dialog",
            f"{cls} (Diálogo)",
            {
                "class": f"^{re.escape(cls)}$",
                "title": "^(Open|Save|Select|Choose|Abrir|Guardar|Elegir).*",
            },
        )

    # 4. Caso general: Aplicaciones completas identificadas por clase
    slug = slugify(cls)
    return (
        f"{slug}",
        cls,
        {
            "class": f"^{re.escape(cls)}$",
        },
    )


def load_rules():
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_rules(rules):
    try:
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(rules, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error guardando JSON: {e}", file=sys.stderr)


def generate_lua(rules):
    lines = [
        "-- =============================================================================",
        "-- REGLAS PERSISTENTES DE VENTANAS (Generadas dinámicamente con ALT + Q)",
        "-- Archivo gestionado automáticamente por toggle-float-persistent.py",
        "-- =============================================================================",
        "",
    ]

    for key, item in sorted(rules.items()):
        name = item.get("name", f"persist_{key}")
        desc = item.get("description", key)
        match = item.get("match", {})
        is_float = item.get("float", True)

        lines.append(f"-- {desc}")
        lines.append("hl.window_rule({")
        lines.append(f'    name  = "{name}",')
        lines.append("    match = {")
        for k, v in match.items():
            # Escapar barras invertidas y comillas dobles para literales de cadena en Lua
            safe_v = v.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'        {k} = "{safe_v}",')
        lines.append("    },")
        lines.append(f"    float = {'true' if is_float else 'false'},")
        lines.append("})")
        lines.append("")

    lines.append("return {}")
    lines.append("")

    try:
        with open(LUA_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except Exception as e:
        print(f"Error generando Lua: {e}", file=sys.stderr)




def main():
    window = get_active_window()
    if not window:
        return

    # 1. Alternar inmediatamente el estado en pantalla (cero latencia)
    subprocess.run(
        ["hyprctl", "dispatch", "hl.dsp.window.float({ action = 'toggle' })"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    currently_floating = window.get("floating", False)
    target_floating = not currently_floating

    # 2. Clasificar la ventana
    key, desc, match = classify_window(window)
    rules = load_rules()

    if target_floating:
        # Se quiere flotante: guardar la regla
        rules[key] = {
            "name": f"persist_{key}",
            "description": desc,
            "match": match,
            "float": True,
        }
    else:
        # Se quiere en mosaico (tiling)
        if key in rules and rules[key].get("float", True):
            del rules[key]
        else:
            # Si no estaba en reglas pero estaba flotando (ej: por regla externa), forzar float=false
            rules[key] = {
                "name": f"persist_{key}",
                "description": desc,
                "match": match,
                "float": False,
            }

    # 3. Guardar estado y generar archivo Lua
    save_rules(rules)
    generate_lua(rules)

    # 4. Recargar configuración de Hyprland para aplicar la nueva regla a futuros inicios
    subprocess.run(
        ["hyprctl", "reload"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


if __name__ == "__main__":
    main()
