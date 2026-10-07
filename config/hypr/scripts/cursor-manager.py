#!/usr/bin/env python3
"""
Cursor Manager for Hyprland (Hyprcursor & XCursor) + GTK & Quickshell
Handles scanning installed cursor themes, extracting visual previews,
and applying configuration across Hyprland, GTK, and X11/XDG standards.
"""

import os
import sys
import json
import struct
import zipfile
import subprocess
from pathlib import Path
from PIL import Image

CACHE_DIR = Path.home() / ".cache" / "cursor_previews"
CONFIG_DIR = Path.home() / ".config"

SEARCH_DIRS = [
    Path.home() / ".local" / "share" / "icons",
    Path.home() / ".icons",
    Path("/usr/local/share/icons"),
    Path("/usr/share/icons"),
]

def extract_xcursor_image(cursor_file: Path, out_png: Path) -> bool:
    """Extract a 32px or 24px frame from an XCursor binary file and save as PNG."""
    try:
        with open(cursor_file, "rb") as f:
            magic = f.read(4)
            if magic != b"Xcur":
                return False
            _, _, ntoc = struct.unpack("<III", f.read(12))
            best_img = None
            for _ in range(ntoc):
                chunk_type, _, chunk_pos = struct.unpack("<III", f.read(12))
                if chunk_type == 0xfffd0002: # IMAGE
                    saved = f.tell()
                    f.seek(chunk_pos)
                    _, _, _, _, width, height, _, _, _ = struct.unpack("<IIIIIIIII", f.read(36))
                    raw = f.read(width * height * 4)
                    f.seek(saved)
                    if best_img is None or (width >= 32 and (best_img[1] < 32 or width <= best_img[1])):
                        best_img = (raw, width, height)
            if best_img:
                raw, w, h = best_img
                img = Image.frombytes("RGBA", (w, h), raw, "raw", "BGRA")
                out_png.parent.mkdir(parents=True, exist_ok=True)
                img.save(out_png)
                return True
    except Exception:
        pass
    return False

def extract_hyprcursor_svg(hlc_file: Path, out_file: Path) -> bool:
    """Extract SVG or PNG from a hyprcursor .hlc zip archive."""
    try:
        with zipfile.ZipFile(hlc_file, "r") as z:
            for name in z.namelist():
                if name.endswith(".svg") or name.endswith(".png"):
                    out_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(out_file, "wb") as out:
                        out.write(z.read(name))
                    return True
    except Exception:
        pass
    return False

def generate_previews(theme_name: str, theme_path: Path) -> dict:
    """Generate or retrieve cached preview image paths for a cursor theme."""
    out_dir = CACHE_DIR / theme_name
    out_dir.mkdir(parents=True, exist_ok=True)

    result = {}
    shapes = [
        ("pointer", ["left_ptr", "arrow", "default"]),
        ("hand", ["hand2", "hand1", "pointer", "link"]),
        ("text", ["xterm", "ibeam", "text"]),
        ("wait", ["wait", "left_ptr_watch", "watch"])
    ]

    for shape_key, candidates in shapes:
        cached_target = out_dir / f"{shape_key}.png"
        cached_svg = out_dir / f"{shape_key}.svg"
        if cached_svg.exists():
            result[shape_key] = str(cached_svg)
            continue
        if cached_target.exists():
            result[shape_key] = str(cached_target)
            continue

        found = False
        # 1. Try hyprcursors
        hypr_dir = theme_path / "hyprcursors"
        if hypr_dir.is_dir():
            for c in candidates:
                hlc = hypr_dir / f"{c}.hlc"
                if hlc.exists():
                    if extract_hyprcursor_svg(hlc, cached_svg):
                        result[shape_key] = str(cached_svg)
                        found = True
                        break

        # 2. Try xcursors
        if not found:
            xcur_dir = theme_path / "cursors"
            if xcur_dir.is_dir():
                for c in candidates:
                    cur_f = xcur_dir / c
                    if cur_f.exists() and cur_f.is_file():
                        if extract_xcursor_image(cur_f, cached_target):
                            result[shape_key] = str(cached_target)
                            found = True
                            break

        if not found and shape_key == "pointer" and "pointer" not in result:
            result[shape_key] = ""

    return result

def list_themes():
    """List all available cursor themes."""
    themes = {}

    for base in SEARCH_DIRS:
        if not base.is_dir():
            continue
        for item in base.iterdir():
            if not item.is_dir() or item.name in themes:
                continue
            has_xcursor = (item / "cursors").is_dir()
            has_hyprcursor = (item / "hyprcursors").is_dir()
            if not (has_xcursor or has_hyprcursor or (item / "cursor.theme").exists()):
                continue

            name = item.name
            comment = ""
            index_theme = item / "index.theme"
            if index_theme.is_file():
                try:
                    with open(index_theme, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("Name=") and not comment:
                                name = line.split("=", 1)[1].strip()
                            elif line.startswith("Comment="):
                                comment = line.split("=", 1)[1].strip()
                except Exception:
                    pass

            previews = generate_previews(item.name, item)

            themes[item.name] = {
                "id": item.name,
                "name": name if name else item.name,
                "comment": comment,
                "path": str(item),
                "has_hyprcursor": has_hyprcursor,
                "has_xcursor": has_xcursor,
                "preview": previews.get("pointer", ""),
                "preview_hand": previews.get("hand", ""),
                "preview_text": previews.get("text", ""),
                "preview_wait": previews.get("wait", "")
            }

    # Sort themes alphabetically with Bibata / Adwaita first
    def sort_key(t):
        t_id = t["id"].lower()
        if "bibata-modern-classic" in t_id:
            return (0, t_id)
        if "bibata" in t_id:
            return (1, t_id)
        if "adwaita" in t_id:
            return (2, t_id)
        return (3, t_id)

    res = sorted(list(themes.values()), key=sort_key)
    print(json.dumps(res, indent=2))

def get_current():
    """Get currently active cursor theme and size."""
    theme = "Bibata-Modern-Classic"
    size = 24

    cursor_lua = CONFIG_DIR / "hypr" / "modules" / "cursor.lua"
    if cursor_lua.exists():
        try:
            with open(cursor_lua, "r") as f:
                for line in f:
                    if 'hl.env("HYPRCURSOR_THEME"' in line or 'hl.env("XCURSOR_THEME"' in line:
                        parts = line.split('"')
                        if len(parts) >= 4:
                            theme = parts[3]
                    elif 'hl.env("HYPRCURSOR_SIZE"' in line or 'hl.env("XCURSOR_SIZE"' in line:
                        parts = line.split('"')
                        if len(parts) >= 4:
                            try:
                                size = int(parts[3])
                            except ValueError:
                                pass
        except Exception:
            pass
    else:
        # Fallback to gsettings
        try:
            out = subprocess.check_output(["gsettings", "get", "org.gnome.desktop.interface", "cursor-theme"], text=True).strip().strip("'\"")
            if out:
                theme = out
            s_out = subprocess.check_output(["gsettings", "get", "org.gnome.desktop.interface", "cursor-size"], text=True).strip()
            if s_out:
                size = int(s_out)
        except Exception:
            pass

    print(json.dumps({"theme": theme, "size": size}))

def update_ini_file(filepath: Path, section: str, updates: dict):
    """Safely update keys in an INI file while preserving formatting."""
    lines = []
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

    section_header = f"[{section}]"
    in_section = False
    section_found = False
    updated_keys = set()
    new_lines = []

    for line in lines:
        sline = line.strip()
        if sline.startswith("[") and sline.endswith("]"):
            if in_section:
                # Add any missing keys before leaving section
                for k, v in updates.items():
                    if k not in updated_keys:
                        new_lines.append(f"{k}={v}\n")
                        updated_keys.add(k)
            in_section = (sline == section_header)
            if in_section:
                section_found = True
            new_lines.append(line)
            continue

        if in_section and "=" in line:
            k = line.split("=", 1)[0].strip()
            if k in updates:
                new_lines.append(f"{k}={updates[k]}\n")
                updated_keys.add(k)
                continue

        new_lines.append(line)

    if in_section:
        for k, v in updates.items():
            if k not in updated_keys:
                new_lines.append(f"{k}={v}\n")
                updated_keys.add(k)

    if not section_found:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines.append("\n")
        new_lines.append(f"\n{section_header}\n")
        for k, v in updates.items():
            new_lines.append(f"{k}={v}\n")

    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

def apply_cursor(theme: str, size: int):
    """Apply cursor theme and size system-wide."""
    size_str = str(size)

    # 1. Apply live in Hyprland
    try:
        subprocess.run(["hyprctl", "setcursor", theme, size_str], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # 2. Write Hyprland persistent lua module
    cursor_lua = CONFIG_DIR / "hypr" / "modules" / "cursor.lua"
    cursor_lua.parent.mkdir(parents=True, exist_ok=True)
    lua_content = f"""-----------------------------------------
---- HYPRCURSOR & XCURSOR ENVIRONMENT ----
-----------------------------------------
-- Archivo gestionado automáticamente por Quickshell Cursor Settings
-- Theme: {theme} | Size: {size}

hl.env("HYPRCURSOR_THEME", "{theme}")
hl.env("HYPRCURSOR_SIZE", "{size_str}")
hl.env("XCURSOR_THEME", "{theme}")
hl.env("XCURSOR_SIZE", "{size_str}")
"""
    with open(cursor_lua, "w", encoding="utf-8") as f:
        f.write(lua_content)

    # 3. Apply GTK gsettings
    try:
        subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "cursor-theme", theme], check=False)
        subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "cursor-size", size_str], check=False)
    except Exception:
        pass

    # 4. Write GTK-3 and GTK-4 settings.ini
    gtk_updates = {
        "gtk-cursor-theme-name": theme,
        "gtk-cursor-theme-size": size_str
    }
    update_ini_file(CONFIG_DIR / "gtk-3.0" / "settings.ini", "Settings", gtk_updates)
    update_ini_file(CONFIG_DIR / "gtk-4.0" / "settings.ini", "Settings", gtk_updates)

    # 5. Write default X11/XDG index.theme fallback
    default_icons = Path.home() / ".icons" / "default" / "index.theme"
    default_icons.parent.mkdir(parents=True, exist_ok=True)
    with open(default_icons, "w", encoding="utf-8") as f:
        f.write(f"""[Icon Theme]
Name=Default
Comment=Default Cursor Theme
Inherits={theme}
""")

    # 6. Write xsettingsd if present or create it
    xsettingsd_file = CONFIG_DIR / "xsettingsd" / "xsettingsd.conf"
    if xsettingsd_file.parent.exists():
        try:
            xcontent = f"""Gtk/CursorThemeName "{theme}"
Gtk/CursorThemeSize {size}
"""
            with open(xsettingsd_file, "w", encoding="utf-8") as f:
                f.write(xcontent)
        except Exception:
            pass

    # 7. Reload Hyprland
    try:
        subprocess.run(["hyprctl", "reload"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    print(json.dumps({"status": "success", "theme": theme, "size": size}))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: cursor-manager.py [list|get|apply <theme> <size>]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "list":
        list_themes()
    elif cmd == "get":
        get_current()
    elif cmd == "apply":
        if len(sys.argv) < 4:
            print("Usage: cursor-manager.py apply <theme> <size>")
            sys.exit(1)
        apply_cursor(sys.argv[2], int(sys.argv[3]))
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
