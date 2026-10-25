#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Default applications for BWM (Settings → Default applications), shared by every theme.

  default-apps.py list [kind]        installed candidates + current choice (JSON)
  default-apps.py set <kind> <id>    make <id> the default <kind>

Kinds and where each choice goes:
  terminal     ~/.config/bwm/default-apps.json (read by bwm-terminal, which the Retro task
               manager and Omarchy plugins use), Quickshell's apps.terminal, xdg-terminals.list
  browser      xdg-settings default-web-browser (+ http/https/html MIME types)
  files        xdg-mime inode/directory
  editor       xdg-mime text/plain
  taskmanager  ~/.config/bwm/default-apps.json + Quickshell's apps.taskManager; terminal
               programs (btop, htop) open in the default terminal
"""

import configparser
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
STATE = HOME / ".config" / "bwm" / "default-apps.json"
QS_CONFIG = HOME / ".config" / "illogical-impulse" / "config.json"
TERMINAL_LAUNCHER = HOME / ".config" / "hypr" / "scripts" / "bwm-terminal"

CATEGORY = {"terminal": "TerminalEmulator", "browser": "WebBrowser", "files": "FileManager", "editor": "TextEditor"}
MIME = {"files": ["inode/directory"], "editor": ["text/plain"],
        "browser": ["x-scheme-handler/http", "x-scheme-handler/https", "text/html"]}
# Task managers: terminal ones run in the default terminal
TASK_MANAGERS = [
    ("btop", "btop", True), ("htop", "htop", True),
    ("missioncenter", "Mission Center", False), ("gnome-system-monitor", "GNOME System Monitor", False),
    ("plasma-systemmonitor", "Plasma System Monitor", False),
]


def data_dirs():
    dirs = [Path(os.environ.get("XDG_DATA_HOME", HOME / ".local" / "share"))]
    dirs += [Path(d) for d in os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":") if d]
    dirs.append(HOME / ".local" / "share" / "flatpak" / "exports" / "share")
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
        return json.loads(STATE.read_text())
    except Exception:
        return {}


def save_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2) + "\n")


def terminal_binary(exec_line):
    try:
        return Path(shlex.split(exec_line)[0]).name
    except Exception:
        return ""


def current(kind, state):
    if kind in ("terminal", "taskmanager"):
        return state.get(kind, "kitty" if kind == "terminal" else "btop")
    if kind == "browser":
        out = subprocess.run(["xdg-settings", "get", "default-web-browser"], capture_output=True, text=True)
        return out.stdout.strip()
    out = subprocess.run(["xdg-mime", "query", "default", MIME[kind][0]], capture_output=True, text=True)
    return out.stdout.strip()


def candidates(kind, entries):
    if kind == "taskmanager":
        return [{"id": b, "name": n + (" (terminal)" if term else "")} for b, n, term in TASK_MANAGERS if shutil.which(b)]
    out = []
    for did, (name, cats, exe) in entries.items():
        if CATEGORY[kind] in cats:
            item = {"id": did, "name": name}
            if kind == "terminal":   # terminals are stored by binary name (bwm-terminal maps the flags)
                binary = terminal_binary(exe)
                if not binary or binary.startswith("vte") or not shutil.which(binary):
                    continue   # GTK's VTE test app and broken entries are not terminals to choose
                item["id"] = binary
            out.append(item)
    uniq = {}
    for item in out:
        uniq.setdefault(item["id"], item)
    return sorted(uniq.values(), key=lambda i: i["name"].lower())


def cmd_list(kinds):
    entries = desktop_entries()
    state = load_state()
    print(json.dumps({k: {"current": current(k, state), "options": candidates(k, entries)} for k in kinds}))


def set_qs_apps(key, value):
    try:
        cfg = json.loads(QS_CONFIG.read_text())
    except Exception:
        return
    cfg.setdefault("apps", {})[key] = value
    tmp = QS_CONFIG.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cfg, indent=2) + "\n")
    os.replace(tmp, QS_CONFIG)


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
            (HOME / ".config" / "xdg-terminals.list").write_text(did + "\n")
        # The task manager follows the terminal when it is a terminal program
        if state.get("taskmanager", "btop") in ("btop", "htop"):
            cmd_set("taskmanager", state.get("taskmanager", "btop"))
    elif kind == "taskmanager":
        term = next((t for b, _, t in TASK_MANAGERS if b == value), None)
        if term is None or not shutil.which(value):
            sys.exit(f"{value} no está instalado")
        state["taskmanager"] = value
        save_state(state)
        set_qs_apps("taskManager", f"{TERMINAL_LAUNCHER} --class org.omarchy.{value} -- {value}" if term else value)
    elif kind == "browser":
        subprocess.run(["xdg-settings", "set", "default-web-browser", value], check=False)
        for mime in MIME["browser"]:
            subprocess.run(["xdg-mime", "default", value, mime], check=False)
    elif kind in MIME:
        for mime in MIME[kind]:
            subprocess.run(["xdg-mime", "default", value, mime], check=False)
    else:
        sys.exit(f"tipo desconocido: {kind}")


if __name__ == "__main__":
    args = sys.argv[1:]
    kinds = ["terminal", "browser", "files", "editor", "taskmanager"]
    if args[:1] == ["list"]:
        cmd_list(args[1:] or kinds)
    elif len(args) == 3 and args[0] == "set":
        cmd_set(args[1], args[2])
    else:
        print(__doc__)
