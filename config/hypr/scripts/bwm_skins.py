#!/usr/bin/env python3
"""Las skins de BWM: una carpeta por skin con su skin.json (config/hypr/skins/<id>/skin.json).

Es la única fuente de datos de una skin: qué imita, cómo gestiona las ventanas ("windows":
"tiling" = mosaico, "traditional" = ventanas flotantes con barra de título, como un escritorio
tradicional), su motor de colores ("palette"), su aspecto ("look", "bar", "fonts"), sus
requisitos y el mapa de archivos que le pertenecen ("parts"). Lo leen bwm-theme-manager.py,
bwm_windows.py, bwm-requirements.py y la bienvenida. Guía y plantilla: config/hypr/skins/README.md
y config/hypr/skins/_template/skin.json.

  bwm_skins.py list            ids de las skins instaladas
  bwm_skins.py show <id>       su skin.json
"""
import json
import os
import sys
from pathlib import Path

SKINS_DIR = Path(__file__).resolve().parents[1] / "skins"
USER_SKINS_DIR = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "bwm" / "skins"
ORDER = ["default", "retro", "plasma"]
WINDOWS = ("tiling", "traditional")


def _read(path: Path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) and data.get("id") else None


def all_skins() -> list:
    """Las de la release y las del usuario (~/.local/share/bwm/skins/<id>/skin.json), en orden.
    Las carpetas que empiezan por «_» (la plantilla) no son skins."""
    found = {}
    for folder, builtin in ((SKINS_DIR, True), (USER_SKINS_DIR, False)):
        for path in sorted(folder.glob("*/skin.json")) if folder.is_dir() else []:
            if path.parent.name.startswith("_"):
                continue
            skin = _read(path)
            if skin and skin["id"] not in found:
                found[skin["id"]] = {**skin, "builtin": builtin, "dir": str(path.parent)}
    return sorted(found.values(), key=lambda s: (ORDER.index(s["id"]) if s["id"] in ORDER else 99, s["id"]))


def skin(skin_id: str) -> dict:
    return next((s for s in all_skins() if s["id"] == skin_id), {})


def windows(skin_id: str) -> str:
    """"tiling" (mosaico) o "traditional" (WM tradicional: ventanas flotantes)."""
    value = skin(skin_id).get("windows", "tiling")
    return value if value in WINDOWS else "tiling"


def is_traditional(skin_id: str) -> bool:
    return windows(skin_id) == "traditional"


def traditional(skin_id: str) -> dict:
    """Geometría de una skin tradicional: barra de título, panel, margen y hueco entre ventanas."""
    return skin(skin_id).get("traditional", {}) if is_traditional(skin_id) else {}


def theme_table(wallpapers_dir: Path) -> dict:
    """Las skins con las claves que usa bwm-theme-manager.py (THEMES)."""
    table = {}
    for s in all_skins():
        look, bar = s.get("look", {}), s.get("bar", {})
        palette = s.get("palette", "matugen")
        table[s["id"]] = {
            "title": s.get("name", s["id"]),
            "description": s.get("description", ""),
            "wallpaper": str(wallpapers_dir / look.get("wallpaper", "default.jpg")),
            "rounding": look.get("rounding", 10),
            "rounding_power": look.get("roundingPower", 2),
            "border_size": look.get("borderSize", 2),
            "gaps_in": look.get("gapsIn", 4),
            "gaps_out": look.get("gapsOut", 8),
            "btop_rounded": look.get("btopRounded", True),
            "bar_corner_style": bar.get("cornerStyle", 2),
            "bar_height": bar.get("height", 40),
            "bar_bottom": bar.get("bottom", False),
            "show_app_icons": bar.get("showAppIcons", True),
            "always_show_numbers": bar.get("alwaysShowNumbers", True),
            "fonts": s.get("fonts", {}),
            "palette": palette,
            "windows": windows(s["id"]),
            # Motores de color de cada skin: Omarchy (Retro) y Breeze estático (Plasma)
            "is_retro": palette == "omarchy",
            "is_plasma": palette == "breeze",
        }
    return table


if __name__ == "__main__":
    if sys.argv[1:] == ["list"]:
        for s in all_skins():
            print(f"{s['id']:<10} {s.get('windows', 'tiling'):<12} {s.get('name', '')}")
    elif len(sys.argv) == 3 and sys.argv[1] == "show":
        print(json.dumps(skin(sys.argv[2]), ensure_ascii=False, indent=2))
    else:
        print(__doc__.strip().splitlines()[-2:][0].strip(), file=sys.stderr)
        sys.exit(2)
