#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor Manager for Hyprland (Hyprcursor & XCursor) + GTK & Quickshell
Handles scanning installed cursor themes, extracting visual previews,
auto-converting legacy XCursor themes to compiled Hyprcursor format,
and synchronizing theme selections live across Hyprland, GTK, X11, and user environments.
"""

import sys
import os
import json
import struct
import subprocess
import shutil
import re
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
            best_diff = 9999
            for _ in range(ntoc):
                chunk_type, chunk_subtype, chunk_pos = struct.unpack("<III", f.read(12))
                if chunk_type == 0xfffd0002: # IMAGE chunk
                    diff = abs(chunk_subtype - 32)
                    if diff < best_diff:
                        best_diff = diff
                        best_img = chunk_pos

            if best_img is None:
                return False

            f.seek(best_img)
            header, chunk_type, chunk_subtype, ver, width, height, xhot, yhot, delay = struct.unpack("<IIIIIIIII", f.read(36))
            raw_pixels = f.read(width * height * 4)
            img = Image.frombytes("RGBA", (width, height), raw_pixels, "raw", "BGRA")
            out_png.parent.mkdir(parents=True, exist_ok=True)
            img.save(out_png)
            return True
    except Exception:
        return False

def extract_hyprcursor_svg(hlc_file: Path, out_file: Path) -> bool:
    """Extract SVG or PNG from a hyprcursor .hlc zip archive."""
    import zipfile
    try:
        with zipfile.ZipFile(hlc_file, 'r') as zf:
            namelist = zf.namelist()
            svgs = [n for n in namelist if n.endswith('.svg')]
            pngs = [n for n in namelist if n.endswith('.png')]
            target = svgs[0] if svgs else (pngs[0] if pngs else None)
            if target:
                out_file.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(target) as src, open(out_file, 'wb') as dst:
                    dst.write(src.read())
                return True
    except Exception:
        pass
    return False

def convert_xcursor_to_hyprcursor(theme_path: Path, dest_dir: Path = None) -> bool:
    """
    Automatically converts an XCursor theme into a compiled Hyprcursor theme.
    Extracts each cursor's images, dimensions, hotspots, delays, and symlinks,
    generates manifest.hl and meta.hl files, and compiles them via hyprcursor-util.
    """
    cursors_dir = theme_path / "cursors"
    if not cursors_dir.is_dir():
        return False

    theme_name = theme_path.name
    if dest_dir is None:
        dest_dir = theme_path

    work_dir = Path(f"/tmp/hc_work_{theme_name}")
    out_dir = Path(f"/tmp/hc_out_{theme_name}")
    shutil.rmtree(work_dir, ignore_errors=True)
    shutil.rmtree(out_dir, ignore_errors=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = work_dir / "manifest.hl"
    manifest.write_text(f"""cursors_directory = hyprcursors
name = {theme_name}
description = Auto-converted from XCursor
version = 0.1
""")

    symlinks = {}
    real_files = []
    for p in cursors_dir.iterdir():
        if not re.match(r'^[A-Za-z0-9_\-\.]+$', p.name):
            continue
        if p.is_symlink():
            try:
                target = p.resolve().name
                symlinks.setdefault(target, []).append(p.name)
            except Exception:
                pass
        elif p.is_file():
            real_files.append(p)

    for rf in real_files:
        shape_name = rf.name
        shape_dir = work_dir / "hyprcursors" / shape_name
        shape_dir.mkdir(parents=True, exist_ok=True)

        try:
            with open(rf, "rb") as f:
                magic = f.read(4)
                if magic != b"Xcur":
                    continue
                _, _, ntoc = struct.unpack("<III", f.read(12))
                tocs = []
                for _ in range(ntoc):
                    ctype, subtype, pos = struct.unpack("<III", f.read(12))
                    if ctype == 0xfffd0002: # image
                        tocs.append((subtype, pos))
        except Exception:
            continue

        if not tocs:
            continue

        size_frames = {}
        hx, hy = 0.0, 0.0
        for idx, (sz, pos) in enumerate(tocs):
            try:
                with open(rf, "rb") as f:
                    f.seek(pos)
                    hdr, ctype, subtype, ver, w, h, xhot, yhot, delay = struct.unpack("<IIIIIIIII", f.read(36))
                    raw = f.read(w * h * 4)
                    img = Image.frombytes("RGBA", (w, h), raw, "raw", "BGRA")
                    png_name = f"frame_{w}x{h}_{idx}.png"
                    img.save(shape_dir / png_name)
                    size_frames.setdefault(w, []).append((png_name, delay))
                    if w > 0 and h > 0:
                        hx = xhot / w
                        hy = yhot / h
            except Exception:
                continue

        meta_lines = [
            "resize_algorithm = bilinear",
            f"hotspot_x = {hx:.3f}",
            f"hotspot_y = {hy:.3f}",
        ]

        for sz in sorted(size_frames.keys()):
            for png_name, delay in size_frames[sz]:
                if delay > 0:
                    meta_lines.append(f"define_size = {sz}, {png_name}, {delay}")
                else:
                    meta_lines.append(f"define_size = {sz}, {png_name}")

        overrides = set(symlinks.get(shape_name, []))
        if shape_name == "left_ptr":
            overrides.add("default")
            overrides.add("arrow")
        elif shape_name == "default":
            overrides.add("left_ptr")
            overrides.add("arrow")

        for ov in sorted(overrides):
            if re.match(r'^[A-Za-z0-9_\-\.]+$', ov) and ov != shape_name:
                meta_lines.append(f"define_override = {ov}")

        (shape_dir / "meta.hl").write_text("\n".join(meta_lines) + "\n")

    res = subprocess.run(["hyprcursor-util", "--create", str(work_dir), "-o", str(out_dir)], capture_output=True, text=True)
    compiled = out_dir / f"theme_{theme_name}"
    success = False
    if compiled.exists():
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(compiled / "manifest.hl", dest_dir / "manifest.hl")
        dest_hc = dest_dir / "hyprcursors"
        if dest_hc.exists():
            shutil.rmtree(dest_hc)
        shutil.copytree(compiled / "hyprcursors", dest_hc)
        success = True

    shutil.rmtree(work_dir, ignore_errors=True)
    shutil.rmtree(out_dir, ignore_errors=True)
    return success

def ensure_theme_ready(theme: str) -> bool:
    """Ensure theme exists, is symlinked between user icon dirs, and has hyprcursor support."""
    theme_path = None
    for base in SEARCH_DIRS:
        cand = base / theme
        if cand.is_dir():
            theme_path = cand
            break

    if not theme_path:
        return False

    user_icons1 = Path.home() / ".local" / "share" / "icons" / theme
    user_icons2 = Path.home() / ".icons" / theme

    # Symlink between user icon dirs
    if theme_path == user_icons1 and not user_icons2.exists():
        try:
            user_icons2.symlink_to(user_icons1, target_is_directory=True)
        except Exception:
            pass
    elif theme_path == user_icons2 and not user_icons1.exists():
        try:
            user_icons1.symlink_to(user_icons2, target_is_directory=True)
        except Exception:
            pass

    # Check if Hyprcursor is present
    has_hc = (theme_path / "manifest.hl").is_file() and (theme_path / "hyprcursors").is_dir()
    if not has_hc and (user_icons1 / "manifest.hl").is_file() and (user_icons1 / "hyprcursors").is_dir():
        has_hc = True

    if not has_hc and (theme_path / "cursors").is_dir():
        # Determine writable destination
        dest = theme_path
        if not os.access(theme_path, os.W_OK):
            dest = user_icons1
            dest.mkdir(parents=True, exist_ok=True)
            if not (dest / "cursors").exists():
                try:
                    (dest / "cursors").symlink_to(theme_path / "cursors", target_is_directory=True)
                except Exception:
                    pass
        convert_xcursor_to_hyprcursor(theme_path, dest)
        if dest != user_icons2 and not user_icons2.exists():
            try:
                user_icons2.symlink_to(dest, target_is_directory=True)
            except Exception:
                pass

    return True

def generate_previews(theme_name: str, theme_path: Path) -> dict:
    """Generate or retrieve cached preview image paths for a cursor theme."""
    theme_cache = CACHE_DIR / theme_name
    theme_cache.mkdir(parents=True, exist_ok=True)

    shapes = {
        "pointer": ["left_ptr", "default", "arrow", "top_left_arrow"],
        "hand": ["pointing_hand", "hand2", "hand1", "pointer", "link"],
        "text": ["xterm", "text", "ibeam"],
        "wait": ["wait", "watch", "progress", "left_ptr_watch"]
    }

    result = {}

    for key, candidates in shapes.items():
        cached_svg = theme_cache / f"{key}.svg"
        cached_png = theme_cache / f"{key}.png"

        if cached_svg.exists():
            result[key] = str(cached_svg)
            continue
        if cached_png.exists():
            result[key] = str(cached_png)
            continue

        # 1. Try hyprcursors
        hypr_dir = theme_path / "hyprcursors"
        found = False
        if hypr_dir.is_dir():
            for c in candidates:
                hlc = hypr_dir / f"{c}.hlc"
                if hlc.is_file():
                    if extract_hyprcursor_svg(hlc, cached_svg):
                        result[key] = str(cached_svg)
                        found = True
                        break
        if found:
            continue

        # 2. Try xcursors
        if not found:
            xcur_dir = theme_path / "cursors"
            if xcur_dir.is_dir():
                for c in candidates:
                    cur_f = xcur_dir / c
                    if cur_f.is_file():
                        cached_target = cached_png
                        if extract_xcursor_image(cur_f, cached_target):
                            result[key] = str(cached_target)
                            found = True
                            break

    return result

def list_themes():
    """List all available cursor themes."""
    (Path.home() / ".local" / "share" / "icons").mkdir(parents=True, exist_ok=True)
    (Path.home() / ".icons").mkdir(parents=True, exist_ok=True)

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
                "name": name,
                "comment": comment,
                "path": str(item),
                "has_hyprcursor": has_hyprcursor,
                "has_xcursor": has_xcursor,
                "preview": previews.get("pointer", ""),
                "preview_hand": previews.get("hand", ""),
                "preview_text": previews.get("text", ""),
                "preview_wait": previews.get("wait", "")
            }

    def sort_key(t):
        t_id = t["id"].lower()
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
        try:
            out = subprocess.check_output(["gsettings", "get", "org.gnome.desktop.interface", "cursor-theme"], text=True).strip().strip('"\'')
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

    # 1. Ensure theme has Hyprcursor files and reciprocal user symlinks
    ensure_theme_ready(theme)

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

    # 3. Export to systemd and D-Bus user environments so newly launched apps get it
    for env_cmd in [
        ["systemctl", "--user", "import-environment", "HYPRCURSOR_THEME", "HYPRCURSOR_SIZE", "XCURSOR_THEME", "XCURSOR_SIZE"],
        ["dbus-update-activation-environment", "--systemd", "HYPRCURSOR_THEME", "HYPRCURSOR_SIZE", "XCURSOR_THEME", "XCURSOR_SIZE"]
    ]:
        try:
            subprocess.run(env_cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    # 4. Apply GTK gsettings
    try:
        subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "cursor-theme", theme], check=False)
        subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "cursor-size", size_str], check=False)
    except Exception:
        pass

    # 5. Write GTK-3 and GTK-4 settings.ini
    gtk_updates = {
        "gtk-cursor-theme-name": theme,
        "gtk-cursor-theme-size": size_str
    }
    update_ini_file(CONFIG_DIR / "gtk-3.0" / "settings.ini", "Settings", gtk_updates)
    update_ini_file(CONFIG_DIR / "gtk-4.0" / "settings.ini", "Settings", gtk_updates)

    # 6. Write default X11/XDG index.theme fallbacks
    for d_path in [
        Path.home() / ".icons" / "default" / "index.theme",
        Path.home() / ".local" / "share" / "icons" / "default" / "index.theme"
    ]:
        try:
            d_path.parent.mkdir(parents=True, exist_ok=True)
            with open(d_path, "w", encoding="utf-8") as f:
                f.write(f"""[Icon Theme]
Name=Default
Comment=Default Cursor Theme
Inherits={theme}
""")
        except Exception:
            pass

    # 7. Write xsettingsd if present or create it
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

    # 8. Reload Hyprland and apply live cursor
    try:
        subprocess.run(["hyprctl", "reload"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    try:
        subprocess.run(["hyprctl", "setcursor", theme, size_str], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
