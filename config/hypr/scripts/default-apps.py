#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Default applications for BWM (Settings → Default applications), shared by every theme.

  default-apps.py list [kind]             installed candidates + current choice (JSON)
  default-apps.py set <kind> <id>         make <id> the default <kind>
  default-apps.py apply-skin [skin]       sync inode/directory when files mode is per-skin
  default-apps.py resolve-files [skin]    resolve effective file manager desktop + argv (JSON)

Kinds and where each choice goes:
  terminal     ~/.config/bwm/default-apps.json (read by bwm-terminal, which the Retro task
               manager and Omarchy plugins use), Quickshell's apps.terminal, xdg-terminals.list
  browser      xdg-settings default-web-browser (+ http/https/html MIME types)
  files        ~/.config/bwm/default-apps.json (files_mode: "per-skin" or "fixed") + xdg-mime
               inode/directory. In "per-skin" mode each skin uses its manifest's fileManager
               (Dolphin in default/Breeze, Nautilus in Retro) and shares bookmarks automatically.
  editor       xdg-mime text/plain
  taskmanager  ~/.config/bwm/default-apps.json + Quickshell's apps.taskManager; terminal
               programs (btop, htop) open in the default terminal
"""

import configparser
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import bwm_skins  # noqa: E402

FILES_PER_SKIN = "per-skin"
FILES_PER_SKIN_LABEL = "Según la skin (Dolphin / Nautilus en Retro)"
DOLPHIN_DESKTOP = "org.kde.dolphin.desktop"
NAUTILUS_DESKTOP = "org.gnome.Nautilus.desktop"

CATEGORY = {"terminal": "TerminalEmulator", "browser": "WebBrowser", "files": "FileManager", "editor": "TextEditor"}
MIME = {"files": ["inode/directory"], "editor": ["text/plain"],
        "browser": ["x-scheme-handler/http", "x-scheme-handler/https", "text/html"]}
# Task managers: terminal ones run in the default terminal
TASK_MANAGERS = [
    ("btop", "btop", True), ("htop", "htop", True),
    ("missioncenter", "Mission Center", False), ("gnome-system-monitor", "GNOME System Monitor", False),
    ("plasma-systemmonitor", "Plasma System Monitor", False),
]


def _home() -> Path:
    return Path.home()


def _config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", _home() / ".config"))


def _state_path() -> Path:
    return _config_home() / "bwm" / "default-apps.json"


def _qs_config_path() -> Path:
    return _config_home() / "illogical-impulse" / "config.json"


def _terminal_launcher() -> Path:
    return _config_home() / "hypr" / "scripts" / "bwm-terminal"


def data_dirs():
    home = _home()
    dirs = [Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))]
    dirs += [Path(d) for d in os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":") if d]
    dirs.append(home / ".local" / "share" / "flatpak" / "exports" / "share")
    dirs.append(Path("/var/lib/flatpak/exports/share"))
    return dirs


def desktop_entries():
    """id -> (name, categories, exec) of visible applications, first one found wins."""
    seen = {}
    for base in data_dirs():
        apps = base / "applications"
        if not apps.is_dir():
            continue
        for f in sorted(apps.rglob("*.desktop")):
            did = str(f.relative_to(apps)).replace("/", "-")
            if did in seen:
                continue
            cp = configparser.ConfigParser(interpolation=None, strict=False)
            try:
                cp.read(f, encoding="utf-8")
                e = cp["Desktop Entry"]
            except Exception:
                continue
            if e.get("NoDisplay", "false").lower() == "true" or e.get("Hidden", "false").lower() == "true":
                seen[did] = None
                continue
            seen[did] = (e.get("Name", did), e.get("Categories", "").split(";"), e.get("Exec", ""))
    return {k: v for k, v in seen.items() if v}


def load_state():
    try:
        data = json.loads(_state_path().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_state(state):
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def current_skin() -> str:
    """Detect the active BWM skin from Quickshell config or Hyprland theme.lua."""
    known = {s["id"] for s in bwm_skins.all_skins()}
    qs = _qs_config_path()
    if qs.exists():
        try:
            theme = json.loads(qs.read_text(encoding="utf-8")).get("appearance", {}).get("bwmTheme")
            if theme in known:
                return theme
        except Exception:
            pass
    theme_lua = _config_home() / "hypr" / "modules" / "theme.lua"
    if theme_lua.exists():
        try:
            for line in theme_lua.read_text(encoding="utf-8").splitlines():
                if "name =" in line and '"' in line:
                    t_name = line.split('"')[1]
                    if t_name in known:
                        return t_name
        except Exception:
            pass
    return "default"


def terminal_binary(exec_line):
    try:
        return Path(shlex.split(exec_line)[0]).name
    except Exception:
        return ""


def friendly_name(kind: str, did: str, name: str) -> str:
    if kind == "files" and did == NAUTILUS_DESKTOP and "nautilus" not in name.lower():
        return f"{name} (Nautilus)"
    return name


def files_mode(state: dict) -> str:
    mode = state.get("files_mode")
    if mode == "fixed" and state.get("files"):
        return "fixed"
    if mode == FILES_PER_SKIN:
        return FILES_PER_SKIN
    return FILES_PER_SKIN


def _query_xdg_mime(mime: str) -> str:
    try:
        out = subprocess.run(["xdg-mime", "query", "default", mime], capture_output=True, text=True, timeout=5)
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _set_xdg_mime(desktop_id: str, mime: str):
    try:
        subprocess.run(["xdg-mime", "default", desktop_id, mime], check=False, timeout=5)
    except (OSError, subprocess.SubprocessError):
        pass


def skin_file_manager(skin_id: str, entries: dict) -> str:
    """Resolve the best available file manager .desktop for the given skin."""
    preferred = bwm_skins.file_manager(skin_id)
    if preferred in entries:
        return preferred
    for fallback in (DOLPHIN_DESKTOP, NAUTILUS_DESKTOP):
        if fallback in entries:
            return fallback
    existing = _query_xdg_mime("inode/directory")
    if existing and (not entries or existing in entries):
        return existing
    for did, (_, cats, _) in entries.items():
        if "FileManager" in cats:
            return did
    return preferred


def effective_files(state: dict, entries: dict, skin_id: str = None) -> str:
    if files_mode(state) == "fixed":
        chosen = state.get("files", "")
        if chosen and (not entries or chosen in entries):
            return chosen
    return skin_file_manager(skin_id or current_skin(), entries)


def resolve_files_argv(desktop_id: str, entries: dict) -> list:
    """Return the launch argv (without target paths) for a file manager .desktop."""
    if desktop_id == DOLPHIN_DESKTOP and shutil.which("dolphin"):
        return ["dolphin", "--new-window"]
    if desktop_id == NAUTILUS_DESKTOP and shutil.which("nautilus"):
        return ["nautilus", "--new-window"]
    if desktop_id in entries:
        _, _, exe = entries[desktop_id]
        if exe:
            try:
                parts = [p for p in shlex.split(exe) if not re.fullmatch(r"%[a-zA-Z]", p)]
            except ValueError:
                parts = []
            if parts and shutil.which(parts[0]):
                return parts
    for binary in ("dolphin", "nautilus"):
        if shutil.which(binary):
            return [binary, "--new-window"]
    return []


def current(kind, state, entries=None):
    if kind in ("terminal", "taskmanager"):
        return state.get(kind, "kitty" if kind == "terminal" else "btop")
    if kind == "files":
        if files_mode(state) == FILES_PER_SKIN:
            return FILES_PER_SKIN
        return state.get("files") or _query_xdg_mime(MIME["files"][0])
    if kind == "browser":
        try:
            out = subprocess.run(["xdg-settings", "get", "default-web-browser"], capture_output=True, text=True, timeout=5)
            return out.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ""
    return _query_xdg_mime(MIME[kind][0])


def candidates(kind, entries):
    if kind == "taskmanager":
        return [{"id": b, "name": n + (" (terminal)" if term else "")} for b, n, term in TASK_MANAGERS if shutil.which(b)]
    out = []
    for did, (name, cats, exe) in entries.items():
        if CATEGORY[kind] in cats:
            item = {"id": did, "name": friendly_name(kind, did, name)}
            if kind == "terminal":   # terminals are stored by binary name (bwm-terminal maps the flags)
                binary = terminal_binary(exe)
                if not binary or binary.startswith("vte") or not shutil.which(binary):
                    continue   # GTK's VTE test app and broken entries are not terminals to choose
                item["id"] = binary
            out.append(item)
    uniq = {}
    for item in out:
        uniq.setdefault(item["id"], item)
    result = sorted(uniq.values(), key=lambda i: i["name"].lower())
    if kind == "files":
        result.insert(0, {"id": FILES_PER_SKIN, "name": FILES_PER_SKIN_LABEL})
    return result


def build_list(kinds):
    entries = desktop_entries()
    state = load_state()
    skin = current_skin()
    payload = {}
    for k in kinds:
        info = {"current": current(k, state, entries), "options": candidates(k, entries)}
        if k == "files":
            eff = effective_files(state, entries, skin)
            eff_name = friendly_name("files", eff, entries[eff][0]) if eff in entries else eff
            info.update({
                "mode": files_mode(state),
                "skin": skin,
                "effective": eff,
                "effectiveName": eff_name,
            })
        payload[k] = info
    return payload


def cmd_list(kinds):
    print(json.dumps(build_list(kinds), ensure_ascii=False))


def set_qs_apps(key, value):
    qs = _qs_config_path()
    try:
        cfg = json.loads(qs.read_text(encoding="utf-8"))
    except Exception:
        return
    cfg.setdefault("apps", {})[key] = value
    tmp = qs.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, qs)


def apply_skin_files(skin_id: str = None) -> dict:
    """Apply the skin's file manager to inode/directory when files_mode is per-skin."""
    entries = desktop_entries()
    state = load_state()
    skin = skin_id or current_skin()
    mode = files_mode(state)
    desktop = effective_files(state, entries, skin)
    changed = False
    if mode == FILES_PER_SKIN and desktop:
        existing = _query_xdg_mime("inode/directory")
        if existing != desktop:
            for mime in MIME["files"]:
                _set_xdg_mime(desktop, mime)
            changed = True
    return {"mode": mode, "skin": skin, "desktop": desktop, "changed": changed}


def resolve_files(skin_id: str = None) -> dict:
    entries = desktop_entries()
    state = load_state()
    skin = skin_id or current_skin()
    mode = files_mode(state)
    desktop = effective_files(state, entries, skin)
    argv = resolve_files_argv(desktop, entries)
    return {"mode": mode, "skin": skin, "desktop": desktop, "argv": argv}


def cmd_set(kind, value):
    state = load_state()
    if kind == "terminal":
        if not shutil.which(value):
            sys.exit(f"{value} no está instalado")
        state["terminal"] = value
        save_state(state)
        # Quickshell's "shell actions" terminal (kitty keeps its single-instance flag)
        set_qs_apps("terminal", "kitty -1" if value == "kitty" else value)
        # xdg-terminal-exec (used by Omarchy-style launchers and some apps)
        entries = desktop_entries()
        did = next((d for d, (_, cats, exe) in entries.items()
                    if "TerminalEmulator" in cats and terminal_binary(exe) == value), None)
        if did:
            (_config_home() / "xdg-terminals.list").write_text(did + "\n", encoding="utf-8")
        # The task manager follows the terminal when it is a terminal program
        if state.get("taskmanager", "btop") in ("btop", "htop"):
            cmd_set("taskmanager", state.get("taskmanager", "btop"))
    elif kind == "taskmanager":
        term = next((t for b, _, t in TASK_MANAGERS if b == value), None)
        if term is None or not shutil.which(value):
            sys.exit(f"{value} no está instalado")
        state["taskmanager"] = value
        save_state(state)
        set_qs_apps("taskManager", f"{_terminal_launcher()} --class org.omarchy.{value} -- {value}" if term else value)
    elif kind == "files":
        entries = desktop_entries()
        if value == FILES_PER_SKIN:
            state["files_mode"] = FILES_PER_SKIN
            save_state(state)
            eff = effective_files(state, entries)
            if eff:
                for mime in MIME["files"]:
                    _set_xdg_mime(eff, mime)
        else:
            state["files_mode"] = "fixed"
            state["files"] = value
            save_state(state)
            for mime in MIME["files"]:
                _set_xdg_mime(value, mime)
    elif kind == "browser":
        subprocess.run(["xdg-settings", "set", "default-web-browser", value], check=False)
        for mime in MIME["browser"]:
            _set_xdg_mime(value, mime)
    elif kind in MIME:
        for mime in MIME[kind]:
            _set_xdg_mime(value, mime)
    else:
        sys.exit(f"tipo desconocido: {kind}")
    import bwm_settings_hooks
    bwm_settings_hooks.changed()


if __name__ == "__main__":
    args = sys.argv[1:]
    kinds = ["terminal", "browser", "files", "editor", "taskmanager"]
    if args[:1] == ["list"]:
        cmd_list(args[1:] or kinds)
    elif len(args) == 3 and args[0] == "set":
        cmd_set(args[1], args[2])
    elif args[:1] == ["apply-skin"]:
        skin_arg = args[1] if len(args) > 1 else None
        print(json.dumps(apply_skin_files(skin_arg), ensure_ascii=False))
    elif args[:1] == ["resolve-files"]:
        skin_arg = args[1] if len(args) > 1 else None
        print(json.dumps(resolve_files(skin_arg), ensure_ascii=False))
    else:
        print(__doc__)
