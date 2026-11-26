#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Gestor común de ratón y panel táctil sobre Hyprland (compartido entre skins).

Guarda la configuración en ~/.config/hypr/input-devices.json y genera
~/.config/hypr/modules/input_devices.lua (cargado por hyprland.lua antes del
Lua del usuario ~/.config/bwm/user/hyprland.lua).

Uso:
  input-manager.py get
  input-manager.py apply '<json>' [--no-reload]
  input-manager.py generate
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys

HYPR_DIR = Path(os.environ.get("BWM_INPUT_HYPR_DIR") or (Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "hypr"))
CONFIG_FILE = HYPR_DIR / "input-devices.json"
LUA_FILE = HYPR_DIR / "modules" / "input_devices.lua"

VALID_PROFILES = ("", "flat", "adaptive")
IGNORED_DEVICE_TOKENS = ("consumer-control", "system-control", "power-button", "sleep-button", "video-bus")
TOUCHPAD_TOKENS = ("touchpad", "trackpad", "synaptics", "elan", "alps", "bcm5974", "magic-trackpad")

DEFAULT_GLOBAL = {
    "sensitivity": 0.0,
    "accel_profile": "",
    "natural_scroll": False,
    "left_handed": False,
    "touchpad_natural_scroll": False,
    "touchpad_tap_to_click": True,
    "touchpad_disable_while_typing": True,
}


def is_touchpad_name(name: str) -> bool:
    low = name.lower()
    return any(tok in low for tok in TOUCHPAD_TOKENS)


def is_ignored_mouse(name: str) -> bool:
    low = name.lower()
    return any(tok in low for tok in IGNORED_DEVICE_TOKENS)


def _clamp_sensitivity(value) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("La sensibilidad debe ser un número entre -1.0 y 1.0")
    val = round(float(value), 2)
    if not (-1.0 <= val <= 1.0):
        raise ValueError("La sensibilidad debe estar entre -1.0 y 1.0")
    return val


def _check_profile(value) -> str:
    if not isinstance(value, str) or value not in VALID_PROFILES:
        raise ValueError(f"Perfil de aceleración no válido: {value!r}")
    return value


def _check_bool(value, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"Se esperaba un booleano para {field_name}")
    return value


def _check_device_name(name: str) -> str:
    if not isinstance(name, str) or not name.strip() or "\n" in name or "\r" in name or "\0" in name:
        raise ValueError("Nombre de dispositivo no válido")
    if not re.fullmatch(r"[ -~]+", name):
        raise ValueError("El nombre del dispositivo contiene caracteres no admitidos")
    return name


def load_saved() -> dict:
    if not CONFIG_FILE.is_file():
        return {"global": dict(DEFAULT_GLOBAL), "devices": {}}
    try:
        raw = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"global": dict(DEFAULT_GLOBAL), "devices": {}}
    g = dict(DEFAULT_GLOBAL)
    if isinstance(raw.get("global"), dict):
        for k, default in DEFAULT_GLOBAL.items():
            if k in raw["global"]:
                try:
                    if k == "sensitivity":
                        g[k] = _clamp_sensitivity(raw["global"][k])
                    elif k == "accel_profile":
                        g[k] = _check_profile(raw["global"][k])
                    else:
                        g[k] = _check_bool(raw["global"][k], k)
                except ValueError:
                    g[k] = default
    devices: dict[str, dict] = {}
    if isinstance(raw.get("devices"), dict):
        for name, cfg in raw["devices"].items():
            if not isinstance(cfg, dict):
                continue
            try:
                clean_name = _check_device_name(name)
                entry = {
                    "sensitivity": _clamp_sensitivity(cfg.get("sensitivity", g["sensitivity"])),
                    "accel_profile": _check_profile(cfg.get("accel_profile", "")),
                    "natural_scroll": _check_bool(cfg.get("natural_scroll", False), "natural_scroll"),
                    "left_handed": _check_bool(cfg.get("left_handed", False), "left_handed"),
                }
                if is_touchpad_name(clean_name) or "tap_to_click" in cfg:
                    entry["tap_to_click"] = _check_bool(cfg.get("tap_to_click", True), "tap_to_click")
                devices[clean_name] = entry
            except ValueError:
                continue
    return {"global": g, "devices": devices}


def live_mice() -> list[dict]:
    override = os.environ.get("BWM_INPUT_DEVICES_JSON")
    if override:
        try:
            data = json.loads(override)
            return data.get("mice", []) if isinstance(data, dict) else []
        except ValueError:
            return []
    try:
        out = subprocess.run(
            ["hyprctl", "-j", "devices"],
            capture_output=True, text=True, timeout=3, check=False,
        )
        if out.returncode != 0:
            return []
        data = json.loads(out.stdout)
        return data.get("mice", []) if isinstance(data, dict) else []
    except (OSError, ValueError, subprocess.SubprocessError):
        return []


def get_state() -> dict:
    saved = load_saved()
    g = saved["global"]
    saved_devices = saved["devices"]
    seen: set[str] = set()
    devices: list[dict] = []

    for dev in live_mice():
        name = str(dev.get("name", "")).strip()
        if not name or name in seen:
            continue
        if is_ignored_mouse(name) and name not in saved_devices:
            continue
        seen.add(name)
        cfg = saved_devices.get(name)
        tp = is_touchpad_name(name) or (isinstance(cfg, dict) and "tap_to_click" in cfg)
        entry = {
            "name": name,
            "connected": True,
            "is_touchpad": tp,
            "sensitivity": cfg["sensitivity"] if cfg else round(float(dev.get("defaultSpeed", g["sensitivity"])), 2),
            "accel_profile": cfg["accel_profile"] if cfg else "",
            "natural_scroll": cfg["natural_scroll"] if cfg else False,
            "left_handed": cfg["left_handed"] if cfg else False,
        }
        if tp:
            entry["tap_to_click"] = cfg.get("tap_to_click", g["touchpad_tap_to_click"]) if cfg else g["touchpad_tap_to_click"]
        devices.append(entry)

    for name, cfg in saved_devices.items():
        if name in seen:
            continue
        tp = is_touchpad_name(name) or "tap_to_click" in cfg
        entry = {
            "name": name,
            "connected": False,
            "is_touchpad": tp,
            "sensitivity": cfg["sensitivity"],
            "accel_profile": cfg["accel_profile"],
            "natural_scroll": cfg["natural_scroll"],
            "left_handed": cfg["left_handed"],
        }
        if tp:
            entry["tap_to_click"] = cfg.get("tap_to_click", g["touchpad_tap_to_click"])
        devices.append(entry)

    return {"global": g, "devices": devices}


def _lua_quote(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _lua_bool(value: bool) -> str:
    return "true" if value else "false"


def render_lua(data: dict) -> str:
    g = data["global"]
    lines = [
        "-- Generado por input-manager.py (configuración común de ratón y touchpad)",
        "-- Se carga antes de ~/.config/bwm/user/hyprland.lua.",
        "hl.config({",
        "    input = {",
        f"        sensitivity = {g['sensitivity']:.2f},",
        f"        accel_profile = {_lua_quote(g['accel_profile'])},",
        f"        natural_scroll = {_lua_bool(g['natural_scroll'])},",
        f"        left_handed = {_lua_bool(g['left_handed'])},",
        "        touchpad = {",
        f"            natural_scroll = {_lua_bool(g['touchpad_natural_scroll'])},",
        f"            [\"tap-to-click\"] = {_lua_bool(g['touchpad_tap_to_click'])},",
        f"            disable_while_typing = {_lua_bool(g['touchpad_disable_while_typing'])},",
        "        },",
        "    },",
        "})",
        "",
    ]
    for name in sorted(data["devices"].keys()):
        cfg = data["devices"][name]
        lines.append("hl.device({")
        lines.append(f"    name = {_lua_quote(name)},")
        lines.append(f"    sensitivity = {cfg['sensitivity']:.2f},")
        if cfg["accel_profile"]:
            lines.append(f"    accel_profile = {_lua_quote(cfg['accel_profile'])},")
        lines.append(f"    natural_scroll = {_lua_bool(cfg['natural_scroll'])},")
        lines.append(f"    left_handed = {_lua_bool(cfg['left_handed'])},")
        if "tap_to_click" in cfg:
            lines.append(f"    [\"tap-to-click\"] = {_lua_bool(cfg['tap_to_click'])},")
        lines.append("})")
        lines.append("")
    return "\n".join(lines)


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def apply_state(payload: dict, reload_hypr: bool = True) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Se esperaba un objeto JSON")
    saved = load_saved()
    g = dict(saved["global"])
    if isinstance(payload.get("global"), dict):
        for k, v in payload["global"].items():
            if k not in DEFAULT_GLOBAL:
                raise ValueError(f"Opción global desconocida: {k}")
            if k == "sensitivity":
                g[k] = _clamp_sensitivity(v)
            elif k == "accel_profile":
                g[k] = _check_profile(v)
            else:
                g[k] = _check_bool(v, k)

    devices = dict(saved["devices"])
    raw_devices = payload.get("devices")
    if isinstance(raw_devices, list):
        for item in raw_devices:
            if not isinstance(item, dict):
                raise ValueError("Entrada de dispositivo no válida")
            name = _check_device_name(item.get("name", ""))
            entry = {
                "sensitivity": _clamp_sensitivity(item.get("sensitivity", g["sensitivity"])),
                "accel_profile": _check_profile(item.get("accel_profile", "")),
                "natural_scroll": _check_bool(item.get("natural_scroll", False), "natural_scroll"),
                "left_handed": _check_bool(item.get("left_handed", False), "left_handed"),
            }
            if is_touchpad_name(name) or "tap_to_click" in item:
                entry["tap_to_click"] = _check_bool(item.get("tap_to_click", g["touchpad_tap_to_click"]), "tap_to_click")
            devices[name] = entry
    elif isinstance(raw_devices, dict):
        for name, item in raw_devices.items():
            if not isinstance(item, dict):
                raise ValueError("Entrada de dispositivo no válida")
            clean_name = _check_device_name(name)
            entry = {
                "sensitivity": _clamp_sensitivity(item.get("sensitivity", g["sensitivity"])),
                "accel_profile": _check_profile(item.get("accel_profile", "")),
                "natural_scroll": _check_bool(item.get("natural_scroll", False), "natural_scroll"),
                "left_handed": _check_bool(item.get("left_handed", False), "left_handed"),
            }
            if is_touchpad_name(clean_name) or "tap_to_click" in item:
                entry["tap_to_click"] = _check_bool(item.get("tap_to_click", g["touchpad_tap_to_click"]), "tap_to_click")
            devices[clean_name] = entry

    to_save = {"global": g, "devices": devices}
    _atomic_write(CONFIG_FILE, json.dumps(to_save, indent=2, ensure_ascii=False) + "\n")
    _atomic_write(LUA_FILE, render_lua(to_save))

    if reload_hypr:
        subprocess.run(["hyprctl", "reload"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import bwm_settings_hooks
            bwm_settings_hooks.notify("input")
        except Exception:
            pass

    return {"success": True, "state": get_state()}


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "get"
    try:
        if cmd == "get":
            print(json.dumps(get_state(), ensure_ascii=False))
            return 0
        if cmd == "generate":
            saved = load_saved()
            _atomic_write(LUA_FILE, render_lua(saved))
            print(json.dumps({"success": True}))
            return 0
        if cmd == "apply" and len(argv) >= 2:
            payload = json.loads(argv[1])
            no_reload = "--no-reload" in argv[2:]
            res = apply_state(payload, reload_hypr=not no_reload)
            print(json.dumps(res, ensure_ascii=False))
            return 0
        print(json.dumps({"success": False, "message": "Uso: input-manager.py get|generate|apply <json> [--no-reload]"}))
        return 2
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"success": False, "message": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
