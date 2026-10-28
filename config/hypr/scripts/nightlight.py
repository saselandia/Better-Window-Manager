#!/usr/bin/env python3
"""Luz nocturna de BWM (panel de pantallas de Retro, menú, indicador de la barra).

Como Omarchy (`omarchy-toggle-nightlight`), usa hyprsunset si está instalado:
cambia la matriz de color del monitor y no tiñe capturas ni grabaciones.
Sin hyprsunset recurre a un `decoration:screen_shader` de Hyprland; el shader
sólo existe mientras está encendida, y `modules/nightlight.lua` lo vuelve a
poner tras `hyprctl reload`.
"""
import os
import sys
import math
import json
import shutil
import argparse
import subprocess
import time

STATE_DIR = os.path.join(os.environ.get("XDG_STATE_HOME", os.path.expanduser("~/.local/state")), "bwm")
STATE_PATH = os.path.join(STATE_DIR, "nightlight.json")
SHADER_PATH = os.path.join(STATE_DIR, "nightlight.frag")
# Ubicaciones antiguas, dentro del repo (~/.config/hypr es un enlace)
LEGACY_STATE = os.path.expanduser("~/.config/hypr/nightlight.json")
LEGACY_SHADER = os.path.expanduser("~/.config/hypr/nightlight.frag")

MIN_TEMP, MAX_TEMP = 2500, 6500
# La temperatura es de todas las skins: también la usa el servicio Hyprsunset de Default/Plasma
# (light.night.colorTemperature, sección compartida de illogical-impulse/config.json)
II_CONFIG = os.path.expanduser("~/.config/illogical-impulse/config.json")

DEFAULT_STATE = {
    "enabled": False,
    "temperature": 4000
}


def migrate_legacy():
    if not os.path.exists(STATE_PATH) and os.path.exists(LEGACY_STATE):
        try:
            os.makedirs(STATE_DIR, exist_ok=True)
            shutil.move(LEGACY_STATE, STATE_PATH)
        except OSError:
            pass
    for path in (LEGACY_STATE, LEGACY_SHADER):
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass


def load_state():
    state = dict(DEFAULT_STATE)
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        state["enabled"] = bool(data.get("enabled", False))
        state["temperature"] = int(data.get("temperature", DEFAULT_STATE["temperature"]))
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    return state


def save_state(state):
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        tmp = STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, STATE_PATH)
    except OSError as e:
        print(f"Error saving nightlight state: {e}", file=sys.stderr)


def share_temperature(temp):
    """Copia la temperatura a light.night.colorTemperature para las otras skins."""
    try:
        with open(II_CONFIG, "r", encoding="utf-8") as f:
            data = json.load(f)
        night = data.setdefault("light", {}).setdefault("night", {})
        if night.get("colorTemperature") == temp:
            return
        night["colorTemperature"] = temp
        tmp = II_CONFIG + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, II_CONFIG)
    except (OSError, ValueError, AttributeError):
        pass


def backend():
    return "hyprsunset" if shutil.which("hyprsunset") else "shader"


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
    shader_content = f"""#version 300 es
precision mediump float;
in vec2 v_texcoord;
uniform sampler2D tex;
out vec4 fragColor;

void main() {{
    vec4 pixColor = texture(tex, v_texcoord);
    fragColor = vec4(pixColor.r * {r:.4f}, pixColor.g * {g:.4f}, pixColor.b * {b:.4f}, pixColor.a);
}}
"""
    os.makedirs(STATE_DIR, exist_ok=True)
    tmp = SHADER_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(shader_content)
    os.replace(tmp, SHADER_PATH)


def hyprctl(*args):
    return subprocess.run(["hyprctl", *args], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                          text=True, timeout=3)


def set_shader(path):
    hyprctl("eval", f'hl.config({{ decoration = {{ screen_shader = "{path}" }} }})')


def ensure_hyprsunset():
    if subprocess.run(["pgrep", "-x", "hyprsunset"], stdout=subprocess.DEVNULL).returncode == 0:
        return
    subprocess.Popen(["hyprsunset"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)
    # Espera a que registre su socket (como `omarchy-toggle-nightlight`)
    for _ in range(20):
        time.sleep(0.1)
        if "Couldn't" not in (hyprctl("hyprsunset", "temperature").stdout or "Couldn't"):
            return


def apply_nightlight(enabled, temp):
    if backend() == "hyprsunset":
        # Si se instaló hyprsunset con el shader puesto, quítalo
        if os.path.exists(SHADER_PATH):
            os.remove(SHADER_PATH)
            set_shader("")
        if enabled:
            ensure_hyprsunset()
            hyprctl("hyprsunset", "temperature", str(temp))
        elif subprocess.run(["pgrep", "-x", "hyprsunset"], stdout=subprocess.DEVNULL).returncode == 0:
            hyprctl("hyprsunset", "identity")
        return

    if enabled:
        write_shader(temp)
        set_shader(SHADER_PATH)
    else:
        if os.path.exists(SHADER_PATH):
            os.remove(SHADER_PATH)
        set_shader("")


def main():
    parser = argparse.ArgumentParser(description="Gestor de Luz Nocturna para Hyprland")
    parser.add_argument("--status", action="store_true", help="Devuelve el estado actual en JSON")
    parser.add_argument("--toggle", action="store_true", help="Alterna entre encendido y apagado")
    parser.add_argument("--on", action="store_true", help="Enciende la luz nocturna")
    parser.add_argument("--off", action="store_true", help="Apaga la luz nocturna")
    parser.add_argument("--apply", action="store_true", help="Vuelve a aplicar el estado guardado (inicio de sesión)")
    parser.add_argument("--temperature", type=int, help="Establece la temperatura en Kelvin (ej. 4000)")
    parser.add_argument("--remember", type=int, metavar="K",
                        help="Sólo guarda la temperatura (la cambió otra skin), sin encender ni apagar nada")

    args = parser.parse_args()
    migrate_legacy()
    state = load_state()

    if args.status:
        print(json.dumps({**state, "backend": backend()}))
        return

    if args.remember is not None:
        state["temperature"] = max(MIN_TEMP, min(MAX_TEMP, args.remember))
        save_state(state)
        return

    changed = args.apply
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
        state["temperature"] = max(MIN_TEMP, min(MAX_TEMP, args.temperature))
        changed = True

    if changed:
        save_state(state)
        apply_nightlight(state["enabled"], state["temperature"])
        if args.temperature is not None:
            share_temperature(state["temperature"])

    print(json.dumps({**state, "backend": backend()}))


if __name__ == "__main__":
    main()
