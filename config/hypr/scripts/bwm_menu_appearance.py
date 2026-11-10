"""BWMenu consume las paletas originales; no guarda ni aplica temas propios."""
import configparser
import json
import os
import re
import time
import tomllib
from pathlib import Path

import bwm_skins

REPO = Path(__file__).resolve().parents[3]
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
STATE = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))


def read_json(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def read_toml(path):
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def read_text(path, fallback=""):
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return fallback


def color(value, fallback):
    # Originales con #RGB/#RRGGBB o los tripletes RGB de kdeglobals.
    value = str(value or "").strip()
    if re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        return value.lower()
    if re.fullmatch(r"#[0-9a-fA-F]{3}", value):
        return "#" + "".join(c * 2 for c in value[1:]).lower()
    match = re.search(r"rgba?\(([0-9a-fA-F]{6})(?:[0-9a-fA-F]{2})?\)", value)
    if match:
        return "#" + match[1].lower()
    if re.fullmatch(r"\d{1,3},\d{1,3},\d{1,3}", value):
        rgb = [int(c) for c in value.split(",")]
        if max(rgb) <= 255:
            return "#" + "".join(f"{c:02x}" for c in rgb)
    return fallback


def omarchy_color(value, shell, native, fallback, seen=None):
    seen = set() if seen is None else seen
    if not isinstance(value, str) or value in seen:
        return fallback
    seen.add(value)
    if "." in value:
        section, _, key = value.partition(".")
        target = shell.get(section, {}).get(key)
    else:
        target = native.get(value)
    return omarchy_color(target, shell, native, fallback, seen) if target else color(value, fallback)


def mix(first, second, weight):
    a, b = first.lstrip("#"), second.lstrip("#")
    return "#" + "".join(f"{round(int(a[i:i+2], 16) * (1-weight) + int(b[i:i+2], 16) * weight):02x}"
                          for i in (0, 2, 4))


def contrast(background):
    def linear(v):
        v /= 255
        return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
    rgb = [linear(int(background[i:i+2], 16)) for i in (1, 3, 5)]
    return "#111111" if sum(v*w for v, w in zip(rgb, (.2126, .7152, .0722))) > .179 else "#ffffff"


def current_skin(config=CONFIG):
    settings = read_json(config / "illogical-impulse/config.json").get("appearance", {})
    active = settings.get("bwmTheme") if isinstance(settings, dict) else None
    if isinstance(active, str) and active:
        return active
    match = re.search(r'name\s*=\s*"([^"]+)"', read_text(config / "hypr/modules/theme.lua"))
    return match[1] if match else "default"


def palette(skin, config=CONFIG, state=STATE):
    generated = read_json(state / "quickshell/user/generated/colors.json")
    bg = color(generated.get("background"), "#202326")
    fg = color(generated.get("on_background"), "#eff0f1")
    accent = color(generated.get("primary"), "#3daee9")
    surface = color(generated.get("surface_container_high"), mix(bg, fg, .06))
    error = color(generated.get("error"), "#da4453")
    theme = (skin.get("defaultTheme") or {}).get("name", "")
    engine = skin.get("palette")
    if engine == "omarchy":
        native = read_toml(state / "bwm/omarchy/colors.toml")
        shell = read_toml(state / "bwm/omarchy/shell.toml")
        # shell.toml del tema y el del usuario tienen la misma precedencia que en Omarchy.
        for section, values in read_toml(config / "omarchy/shell.toml").items():
            if isinstance(values, dict):
                shell.setdefault(section, {}).update(values)
        menu = shell.get("menu", {})
        bg = omarchy_color(menu.get("background"), shell, native, color(native.get("background"), bg))
        fg = omarchy_color(menu.get("text"), shell, native, color(native.get("foreground"), fg))
        accent = color(native.get("accent"), accent)
        surface = color(native.get("lighter_background"), mix(bg, fg, .07))
        error = color(native.get("red"), error)
        mode = read_text(state / "bwm/omarchy/theme.mode")
        theme = read_text(state / "bwm/omarchy/theme.name").replace("-", " ").title() if mode == "static" else "Paleta dinámica"
    elif engine == "breeze":
        kde = configparser.ConfigParser(interpolation=None)
        try:
            kde.read(config / "kdeglobals", encoding="utf-8")
        except configparser.Error:
            pass
        bg = color(kde.get("Colors:Window", "BackgroundNormal", fallback=""), bg)
        fg = color(kde.get("Colors:Window", "ForegroundNormal", fallback=""), fg)
        accent = color(kde.get("Colors:Selection", "BackgroundNormal", fallback=""), accent)
        surface = color(kde.get("Colors:Button", "BackgroundNormal", fallback=""), surface)
        theme = kde.get("General", "ColorScheme", fallback=theme)
        if theme == "BWM":
            theme = (skin.get("defaultTheme") or {}).get("name", theme)
    return {"background": bg, "foreground": fg, "accent": accent, "surface": surface,
            "muted": mix(fg, bg, .32), "border": mix(bg, fg, .19), "error": error,
            "onAccent": contrast(accent), "selection": mix(bg, accent, .22),
            "themeName": theme}


def appearance(config=CONFIG, state=STATE):
    skins = bwm_skins.all_skins()
    sid = current_skin(config)
    skin = next((s for s in skins if s["id"] == sid), skins[0] if skins else {})
    profile = read_json(config / "illogical-impulse/config.json")
    settings = profile.get("appearance", {})
    fonts = settings.get("fonts", {}) if isinstance(settings, dict) else {}
    if not isinstance(fonts, dict):
        fonts = {}
    # Los perfiles actuales pueden contener strings o grupos de familias.
    family = fonts.get("main") or skin.get("fonts", {}).get("main", "sans-serif")
    if not isinstance(family, str):
        family = skin.get("fonts", {}).get("main", "sans-serif")
    if skin.get("palette") == "omarchy":
        family = fonts.get("monospace") or skin.get("fonts", {}).get("monospace", "monospace")
        if not isinstance(family, str):
            family = skin.get("fonts", {}).get("monospace", "monospace")
    rounding = skin.get("look", {}).get("rounding", 8)
    cards = []
    for entry in skins:
        preview = Path(entry.get("preview", ""))
        if not preview.is_absolute():
            preview = REPO / preview
        saved = profile if entry["id"] == sid else read_json(config / f"illogical-impulse/config-{entry['id']}.json")
        background = saved.get("background", {})
        wallpaper = background.get("wallpaperPath", "") if isinstance(background, dict) else ""
        if not isinstance(wallpaper, str):
            wallpaper = ""
        if not wallpaper or not Path(wallpaper).is_file():
            wallpaper = read_text(Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / f"current_wallpaper_{entry['id']}")
        cards.append({"id": entry["id"], "name": entry["name"], "preview": str(preview),
                      "wallpaper": wallpaper if Path(wallpaper).is_file() and Path(wallpaper).suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".avif", ".bmp", ".svg", ".gif") else "",
                      "barBottom": entry.get("bar", {}).get("bottom", False),
                      "description": entry.get("description", ""), "imitates": entry.get("imitates", ""),
                      "windows": entry.get("windows", "tiling"), "rounding": entry.get("look", {}).get("rounding", 8),
                      "font": entry.get("fonts", {}).get("main", "sans-serif"),
                      "theme": entry.get("defaultTheme", {}), "themes": entry.get("themes", {})})
    return {"skin": sid, "skinName": skin.get("name", sid), "font": family,
            "radius": rounding, "buttonRadius": min(rounding, 20), "skins": cards,
            **palette(skin, config, state)}


def watched_paths(config=CONFIG, state=STATE):
    return [config / "illogical-impulse/config.json", config / "hypr/modules/theme.lua",
            state / "quickshell/user/generated/colors.json", state / "bwm/omarchy/colors.toml",
            state / "bwm/omarchy/shell.toml", config / "omarchy/shell.toml", config / "kdeglobals",
            state / "bwm/omarchy/theme.name", state / "bwm/omarchy/theme.mode",
            *[config / f"illogical-impulse/config-{s['id']}.json" for s in bwm_skins.all_skins()],
            *[Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / f"current_wallpaper_{s['id']}" for s in bwm_skins.all_skins()],
            *bwm_skins.SKINS_DIR.glob("*/skin.json"), *bwm_skins.USER_SKINS_DIR.glob("*/skin.json")]


def stamp(config=CONFIG, state=STATE):
    result = []
    for path in watched_paths(config, state):
        try:
            info = path.stat()
            result.append((str(path), info.st_mtime_ns, info.st_size, info.st_ino))
        except OSError:
            result.append((str(path), None))
    return result


def watch(config=CONFIG, state=STATE):
    previous, payload = None, None
    while True:
        signature = stamp(config, state)
        if signature != previous:
            time.sleep(.12)
            # No mostrar el perfil nuevo con la paleta vieja a mitad del cambio de skin.
            from bwm_session import theme_manager_busy
            if theme_manager_busy():
                time.sleep(.2)
                continue
            current = appearance(config, state)
            encoded = json.dumps(current, ensure_ascii=False, sort_keys=True)
            if encoded != payload:
                print(encoded, flush=True)
                payload = encoded
            previous = signature
        time.sleep(.25)
