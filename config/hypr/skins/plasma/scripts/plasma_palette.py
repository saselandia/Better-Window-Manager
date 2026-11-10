#!/usr/bin/env python3
"""Paleta de la skin Breeze leída del esquema de color de Plasma (kdeglobals o un .colors).

Fase 1 de docs/BREEZE_PLAN.md: el esquema de color de KDE es la única fuente de colores de Breeze.
De él salen los roles Material 3 que usan las plantillas de matugen (GTK, Vesktop, Firefox,
Steam, Stremio, Omacalc, Quickshell...), la paleta de kitty, los colores de Hyprland y los de rofi.
No se inventa un formato propio: se lee el de Plasma tal cual (regla 11).

  plasma_palette.py m3 [archivo]        roles Material 3 en JSON
  plasma_palette.py groups [archivo]    grupos del esquema (Window, View, ..., WM) en JSON
"""
from __future__ import annotations

import configparser
import json
import os
import sys
from pathlib import Path

HOME = Path.home()
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME") or HOME / ".config")
KDEGLOBALS = CONFIG / "kdeglobals"

# Breeze Dark de Plasma 6.7.5 (/usr/share/color-schemes/BreezeDark.colors): sólo se usa para lo que
# un esquema incompleto no traiga, como hace KColorScheme con sus valores por defecto.
FALLBACK = {
    "Colors:Window": {"BackgroundNormal": "32,35,38", "BackgroundAlternate": "41,44,48", "ForegroundNormal": "252,252,252",
                      "ForegroundInactive": "161,169,177", "ForegroundNegative": "218,68,83", "ForegroundNeutral": "246,116,0",
                      "ForegroundPositive": "39,174,96", "ForegroundLink": "29,153,243", "ForegroundVisited": "155,89,182",
                      "DecorationFocus": "61,174,233", "DecorationHover": "61,174,233"},
    "Colors:View": {"BackgroundNormal": "20,22,24", "BackgroundAlternate": "29,31,34", "ForegroundNormal": "252,252,252",
                    "ForegroundInactive": "161,169,177"},
    "Colors:Button": {"BackgroundNormal": "41,44,48", "ForegroundNormal": "252,252,252"},
    "Colors:Selection": {"BackgroundNormal": "61,174,233", "ForegroundNormal": "252,252,252"},
    "Colors:Tooltip": {"BackgroundNormal": "41,44,48", "ForegroundNormal": "252,252,252"},
    "Colors:Complementary": {"BackgroundNormal": "32,35,38", "ForegroundNormal": "252,252,252"},
    "Colors:Header": {"BackgroundNormal": "41,44,48", "ForegroundNormal": "252,252,252"},
    "WM": {"activeBackground": "39,44,49", "activeForeground": "252,252,252",
           "inactiveBackground": "32,36,40", "inactiveForeground": "161,169,177"},
}
GROUPS = ("Window", "View", "Button", "Selection", "Tooltip", "Complementary", "Header")
ROLES = ("BackgroundNormal", "BackgroundAlternate", "ForegroundNormal", "ForegroundInactive", "ForegroundActive",
         "ForegroundLink", "ForegroundVisited", "ForegroundNegative", "ForegroundNeutral", "ForegroundPositive",
         "DecorationFocus", "DecorationHover")

# Paleta ANSI de Konsole «Breeze» (konsole/data/color-schemes/Breeze.colorscheme). Plasma no
# tiene esquema de terminal en kdeglobals; fondo y texto salen del grupo View del esquema activo.
KONSOLE_BREEZE = ("#232627", "#ed1515", "#11d116", "#f67400", "#1d99f3", "#9b59b6", "#1abc9c", "#fcfcfc",
                  "#7f8c8d", "#c0392b", "#1cdc9a", "#fdbc4b", "#3daee9", "#8e44ad", "#16a085", "#ffffff")


def _ini() -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None, strict=False, delimiters=("=",))
    parser.optionxform = str
    return parser


def read_scheme(path: Path | None = None) -> dict:
    """Secciones del esquema (o de kdeglobals) como dict; las claves se conservan tal cual."""
    path = Path(path) if path else KDEGLOBALS
    parser = _ini()
    try:
        parser.read(path, encoding="utf-8")
    except (configparser.Error, OSError):
        pass
    return {s: dict(parser[s]) for s in parser.sections()}


def parse_color(value: str) -> tuple[int, int, int] | None:
    value = (value or "").strip()
    try:
        if value.startswith("#"):
            h = value[1:]
            if len(h) == 8:  # #aarrggbb (formato de Qt)
                h = h[2:]
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
        parts = [int(p) for p in value.split(",")]
        if len(parts) >= 3:
            return tuple(max(0, min(255, p)) for p in parts[:3])
    except ValueError:
        pass
    return None


def hexc(rgb) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def mix(a, b, t: float):
    """t = 0 → a, t = 1 → b."""
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def luminance(rgb) -> float:
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


class Scheme:
    """Acceso a un esquema de color de KDE con los mismos valores por defecto que KColorScheme."""

    def __init__(self, sections: dict):
        self.sections = sections

    def get(self, group: str, role: str):
        section = group if group == "WM" else f"Colors:{group}"
        value = parse_color(self.sections.get(section, {}).get(role, ""))
        if value is None:
            value = parse_color(self.sections.get("Colors:Window", {}).get(role, "")) if section != "WM" else None
        if value is None:
            value = parse_color(FALLBACK.get(section, {}).get(role, "") or FALLBACK["Colors:Window"].get(role, ""))
        return value or (0, 0, 0)

    @property
    def name(self) -> str:
        general = self.sections.get("General", {})
        # KConfig no escribe el valor por defecto: sin ColorScheme, kdeglobals es Breeze Claro
        return general.get("ColorScheme") or general.get("Name") or "BreezeLight"

    @property
    def accent(self):
        general = self.sections.get("General", {})
        if general.get("accentColorFromWallpaper", "false").lower() != "true":
            accent = parse_color(general.get("AccentColor", ""))
            if accent:
                return accent
        return self.get("Selection", "BackgroundNormal")

    @property
    def dark(self) -> bool:
        return luminance(self.get("Window", "BackgroundNormal")) < 0.25

    def groups(self) -> dict:
        out = {g: {r: hexc(self.get(g, r)) for r in ROLES} for g in GROUPS}
        out["WM"] = {k: hexc(self.get("WM", k)) for k in
                     ("activeBackground", "activeForeground", "inactiveBackground", "inactiveForeground",
                      "activeBlend", "inactiveBlend", "frame", "inactiveFrame")}
        return out


def m3(scheme: Scheme) -> dict:
    """Roles Material 3 (nombres de matugen) a partir del esquema de Plasma."""
    win = scheme.get("Window", "BackgroundNormal")
    view = scheme.get("View", "BackgroundNormal")
    fg = scheme.get("Window", "ForegroundNormal")
    muted = scheme.get("Window", "ForegroundInactive")
    accent = scheme.accent
    on_accent = scheme.get("Selection", "ForegroundNormal")
    tertiary = scheme.get("Window", "ForegroundPositive")
    error = scheme.get("Window", "ForegroundNegative")
    on_error = (252, 252, 252) if luminance(error) < 0.4 else (0, 0, 0)
    tone = lambda c: mix(c, win, 0.65)  # contenedor de un color sobre el fondo de ventana
    h = hexc
    out = {
        "primary": h(accent), "on_primary": h(on_accent), "primary_container": h(tone(accent)), "on_primary_container": h(fg),
        "inverse_primary": h(accent), "surface_tint": h(accent),
        "secondary": h(accent), "on_secondary": h(on_accent), "secondary_container": h(mix(accent, win, 0.75)),
        "on_secondary_container": h(fg),
        "tertiary": h(tertiary), "on_tertiary": h(on_accent), "tertiary_container": h(tone(tertiary)), "on_tertiary_container": h(fg),
        "background": h(win), "on_background": h(fg),
        "surface": h(win), "surface_dim": h(mix(win, view, 0.5)), "surface_bright": h(mix(win, fg, 0.10)),
        "surface_container_lowest": h(view), "surface_container_low": h(mix(win, view, 0.5)), "surface_container": h(win),
        "surface_container_high": h(mix(win, fg, 0.05)), "surface_container_highest": h(mix(win, fg, 0.10)),
        "on_surface": h(fg), "surface_variant": h(mix(win, fg, 0.10)), "on_surface_variant": h(muted),
        "inverse_surface": h(fg), "inverse_on_surface": h(win),
        "outline": h(mix(win, fg, 0.30)), "outline_variant": h(mix(win, fg, 0.18)), "shadow": "#000000", "scrim": "#000000",
        "error": h(error), "on_error": h(on_error), "error_container": h(tone(error)), "on_error_container": h(fg),
        "primary_fixed": h(accent), "primary_fixed_dim": h(mix(accent, (0, 0, 0), 0.2)),
        "on_primary_fixed": h(on_accent), "on_primary_fixed_variant": h(on_accent),
        "secondary_fixed": h(accent), "secondary_fixed_dim": h(mix(accent, (0, 0, 0), 0.2)),
        "on_secondary_fixed": h(on_accent), "on_secondary_fixed_variant": h(on_accent),
        "tertiary_fixed": h(tertiary), "tertiary_fixed_dim": h(mix(tertiary, (0, 0, 0), 0.2)),
        "on_tertiary_fixed": h(on_accent), "on_tertiary_fixed_variant": h(on_accent),
        "success": h(tertiary), "on_success": h(on_accent), "success_container": h(tone(tertiary)), "on_success_container": h(fg),
    }
    return out


def kitty(scheme: Scheme) -> str:
    bg = hexc(scheme.get("View", "BackgroundNormal"))
    fg = hexc(scheme.get("View", "ForegroundNormal"))
    sel = hexc(scheme.accent)
    sel_fg = hexc(scheme.get("Selection", "ForegroundNormal"))
    tab = hexc(scheme.get("Window", "BackgroundNormal"))
    tab_fg = hexc(scheme.get("Window", "ForegroundInactive"))
    ansi = list(KONSOLE_BREEZE)
    if not scheme.dark:
        # En claro, el «negro» y el «blanco» de la terminal se intercambian para seguir legibles
        ansi[0], ansi[7], ansi[8], ansi[15] = "#fcfcfc", "#232627", "#bdc3c7", "#000000"
    lines = [f"# Generado por skins/plasma/scripts/plasma_palette.py del esquema «{scheme.name or 'Breeze'}»",
             f"background {bg}", f"foreground {fg}", f"selection_background {sel}", f"selection_foreground {sel_fg}",
             f"cursor {sel}", f"cursor_text_color {bg}", f"url_color {hexc(scheme.get('View', 'ForegroundLink'))}",
             f"active_tab_background {sel}", f"active_tab_foreground {sel_fg}",
             f"inactive_tab_background {tab}", f"inactive_tab_foreground {tab_fg}",
             f"active_border_color {tab}", f"inactive_border_color {tab}"]
    lines += [f"color{i} {c}" for i, c in enumerate(ansi)]
    return "\n".join(lines) + "\n"


def hypr_lua(scheme: Scheme) -> str:
    accent = hexc(scheme.accent).lstrip("#")
    bg = hexc(scheme.get("Window", "BackgroundNormal")).lstrip("#")
    return ("-- Generado por bwm-theme-manager.py con el esquema de color de Plasma activo"
            f" («{scheme.name or 'Breeze'}», skins/plasma/scripts/plasma_palette.py)\n"
            "local plasma_colors = {\n"
            f'    accent = "rgba({accent}ee)",\n    secondary = "rgba({accent}ee)",\n    bg = "rgba({bg}ee)",\n'
            '    border = "rgba(00000000)",\n    border_inactive = "rgba(00000000)",\n}\nreturn plasma_colors\n')


def rofi(scheme: Scheme) -> str:
    win = scheme.get("Window", "BackgroundNormal")
    fg = scheme.get("Window", "ForegroundNormal")
    return ("* {\n"
            f"    accent: {hexc(scheme.accent)};\n    secondary: {hexc(scheme.get('Window', 'ForegroundLink'))};\n"
            f"    bg: {hexc(win)}f4;\n    bg-card: {hexc(mix(win, fg, 0.08))};\n"
            f"    bg-input: {hexc(scheme.get('View', 'BackgroundNormal'))};\n    fg: {hexc(fg)};\n"
            f"    muted: {hexc(scheme.get('Window', 'ForegroundInactive'))};\n    dim: {hexc(mix(win, fg, 0.4))};\n"
            f"    border: {hexc(scheme.accent)};\n    bg-selected-text: {hexc(scheme.get('Selection', 'ForegroundNormal'))};\n"
            "}\n")


def load(path: Path | None = None) -> Scheme:
    return Scheme(read_scheme(path))


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("m3", "groups"):
        print(__doc__)
        sys.exit(1)
    s = load(Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    data = m3(s) if sys.argv[1] == "m3" else s.groups()
    data["darkmode"] = s.dark
    data["scheme"] = s.name
    print(json.dumps(data, indent=2))
