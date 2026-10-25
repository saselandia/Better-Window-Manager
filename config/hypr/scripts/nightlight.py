#!/usr/bin/env python3
import os
import sys
import math
import json
import argparse
import subprocess

CONFIG_DIR = os.path.expanduser("~/.config/hypr")
STATE_PATH = os.path.join(CONFIG_DIR, "nightlight.json")
SHADER_PATH = os.path.join(CONFIG_DIR, "nightlight.frag")

DEFAULT_STATE = {
    "enabled": False,
    "temperature": 4000
}

def load_state():
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return dict(DEFAULT_STATE)

def save_state(state):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"Error saving nightlight state: {e}", file=sys.stderr)

def kelvin_to_rgb(k):
    """Calcula coeficientes RGB normalizados para una temperatura en Kelvin (1000K-10000K)"""
    t = max(1000, min(10000, k)) / 100.0
    if t <= 66:
        r = 1.0
        g = (99.4708025861 * math.log(t) - 161.1195681661) / 255.0
        if t <= 19:
            b = 0.0
        else:
            b = (138.5177312231 * math.log(t - 10) - 305.0447927307) / 255.0
    else:
        r = (329.698727446 * ((t - 60) ** -0.1332047592)) / 255.0
        g = (288.1221695283 * ((t - 60) ** -0.0755148492)) / 255.0
        b = 1.0
    return max(0.0, min(1.0, r)), max(0.0, min(1.0, g)), max(0.0, min(1.0, b))

def write_shader(k):
    r, g, b = kelvin_to_rgb(k)
    shader_content = f"""precision mediump float;
varying vec2 v_texcoord;
uniform sampler2D tex;

void main() {{
    vec4 pixColor = texture2D(tex, v_texcoord);
    pixColor.r = pixColor.r * {r:.4f};
    pixColor.g = pixColor.g * {g:.4f};
    pixColor.b = pixColor.b * {b:.4f};
    gl_FragColor = pixColor;
}}
"""
    try:
        with open(SHADER_PATH, "w", encoding="utf-8") as f:
            f.write(shader_content)
        return True
    except Exception as e:
        print(f"Error writing shader: {e}", file=sys.stderr)
        return False

def apply_nightlight(enabled, temp):
    if enabled:
        write_shader(temp)
        expr = f'hl.config({{ decoration = {{ screen_shader = "{SHADER_PATH}" }} }})'
    else:
        expr = 'hl.config({ decoration = { screen_shader = "" } })'
    subprocess.run(["hyprctl", "eval", expr], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    parser = argparse.ArgumentParser(description="Gestor de Luz Nocturna para Hyprland")
    parser.add_argument("--status", action="store_true", help="Devuelve el estado actual en JSON")
    parser.add_argument("--toggle", action="store_true", help="Alterna entre encendido y apagado")
    parser.add_argument("--on", action="store_true", help="Enciende la luz nocturna")
    parser.add_argument("--off", action="store_true", help="Apaga la luz nocturna")
    parser.add_argument("--temperature", type=int, help="Establece la temperatura en Kelvin (ej. 4000)")

    args = parser.parse_args()
    state = load_state()

    if args.status:
        print(json.dumps(state))
        return

    changed = False
    if args.toggle:
        state["enabled"] = not state.get("enabled", False)
        changed = True
    elif args.on:
        state["enabled"] = True
        changed = True
    elif args.off:
        state["enabled"] = False
        changed = True

    if args.temperature is not None:
        temp = max(2500, min(6500, args.temperature))
        state["temperature"] = temp
        changed = True

    if changed:
        save_state(state)
        apply_nightlight(state["enabled"], state["temperature"])

    print(json.dumps(state))

if __name__ == "__main__":
    main()
