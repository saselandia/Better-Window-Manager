#!/usr/bin/env python3
"""
Autostart Manager for Hyprland & Quickshell
Handles standard XDG Autostart entries (~/.config/autostart/*.desktop)
Compatible with KDE & GNOME autostart standards.
"""

import sys
import os
import glob
import json
import re
import argparse
import subprocess
import time
from typing import List, Dict, Any, Optional

AUTOSTART_DIR = os.path.expanduser("~/.config/autostart")
LOG_FILE = os.path.expanduser("~/.cache/hypr-autostart.log")

def get_app_directories() -> List[str]:
    """Returns list of directories where .desktop files are stored."""
    dirs = [
        os.path.expanduser("~/.local/share/applications"),
        os.path.expanduser("~/.local/share/flatpak/exports/share/applications"),
        "/var/lib/flatpak/exports/share/applications",
        "/usr/local/share/applications",
        "/usr/share/applications"
    ]
    env_dirs = os.environ.get("XDG_DATA_DIRS", "").split(":")
    for d in env_dirs:
        if d:
            app_dir = os.path.join(d, "applications")
            if app_dir not in dirs and os.path.isdir(app_dir):
                dirs.append(app_dir)
    return [d for d in dirs if os.path.isdir(d)]

def clean_exec_command(exec_cmd: str) -> str:
    """Strips standard desktop entry field codes (%f, %F, %u, %U, %i, %c, %k, @@u, etc.)."""
    # Remove @@u %U @@ flatpak wrapper syntax if present
    cmd = re.sub(r'@@[a-zA-Z]?\s+', '', exec_cmd)
    cmd = re.sub(r'\s+@@', '', cmd)
    # Remove %f, %F, %u, %U, %d, %D, %n, %N, %i, %c, %k, %v, %m
    cmd = re.sub(r'%[fFuUdDnNickvm]', '', cmd)
    return cmd.strip()

def parse_desktop_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Robust parser for .desktop files."""
    if not os.path.isfile(filepath):
        return None
    
    data = {
        "file": os.path.basename(filepath),
        "path": filepath,
        "name": "",
        "exec": "",
        "raw_exec": "",
        "icon": "application-x-executable",
        "comment": "",
        "enabled": True,
        "hidden": False,
        "terminal": False,
        "type": "Application",
        "nodisplay": False
    }

    in_desktop_entry = False
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    in_desktop_entry = (line == "[Desktop Entry]")
                    continue
                if not in_desktop_entry:
                    continue
                
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip()
                    
                    # Exact or localized key check
                    if key == "Name" and not data["name"]:
                        data["name"] = val
                    elif key == "Exec":
                        data["raw_exec"] = val
                        data["exec"] = clean_exec_command(val)
                    elif key == "Icon":
                        data["icon"] = val
                    elif key == "Comment" and not data["comment"]:
                        data["comment"] = val
                    elif key == "Type":
                        data["type"] = val
                    elif key == "Terminal":
                        data["terminal"] = val.lower() == "true"
                    elif key == "NoDisplay":
                        data["nodisplay"] = val.lower() == "true"
                    elif key == "Hidden":
                        data["hidden"] = val.lower() == "true"
                    elif key == "X-GNOME-Autostart-enabled":
                        if val.lower() == "false":
                            data["enabled"] = False
                    elif key == "X-KDE-autostart-condition":
                        if "false" in val.lower():
                            data["enabled"] = False
    except Exception as e:
        return None

    if not data["name"]:
        data["name"] = os.path.splitext(os.path.basename(filepath))[0]
    
    # If hidden=true, consider disabled
    if data["hidden"]:
        data["enabled"] = False

    return data

def list_autostart_entries() -> List[Dict[str, Any]]:
    """Lists all entries currently in ~/.config/autostart/."""
    os.makedirs(AUTOSTART_DIR, exist_ok=True)
    entries = []
    for filepath in sorted(glob.glob(os.path.join(AUTOSTART_DIR, "*.desktop"))):
        entry = parse_desktop_file(filepath)
        if entry:
            entries.append(entry)
    return entries

def list_system_applications() -> List[Dict[str, Any]]:
    """Scans system and user applications to provide a picker list."""
    apps = []
    seen = set()
    for d in get_app_directories():
        for filepath in glob.glob(os.path.join(d, "*.desktop")):
            basename = os.path.basename(filepath)
            if basename in seen:
                continue
            seen.add(basename)
            entry = parse_desktop_file(filepath)
            if entry and entry["type"] == "Application" and not entry["nodisplay"] and entry["exec"]:
                apps.append({
                    "id": basename,
                    "name": entry["name"],
                    "icon": entry["icon"],
                    "comment": entry["comment"],
                    "exec": entry["exec"],
                    "path": filepath
                })
    apps.sort(key=lambda x: x["name"].lower())
    return apps

def toggle_autostart_entry(filename: str, enable: bool) -> bool:
    """Toggles enabled status by modifying X-GNOME-Autostart-enabled and Hidden."""
    filepath = os.path.join(AUTOSTART_DIR, filename)
    if not os.path.isfile(filepath):
        return False
    
    lines = []
    has_gnome_key = False
    has_hidden_key = False
    in_desktop_entry = False

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            stripped = line.strip()
            if stripped == "[Desktop Entry]":
                in_desktop_entry = True
                lines.append(line)
                continue
            elif stripped.startswith("["):
                in_desktop_entry = False

            if in_desktop_entry:
                if stripped.startswith("X-GNOME-Autostart-enabled="):
                    lines.append(f"X-GNOME-Autostart-enabled={'true' if enable else 'false'}\n")
                    has_gnome_key = True
                    continue
                elif stripped.startswith("Hidden="):
                    lines.append(f"Hidden={'false' if enable else 'true'}\n")
                    has_hidden_key = True
                    continue
            lines.append(line)

    # Append missing keys under [Desktop Entry]
    if not has_gnome_key or not has_hidden_key:
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if line.strip() == "[Desktop Entry]":
                if not has_gnome_key:
                    new_lines.append(f"X-GNOME-Autostart-enabled={'true' if enable else 'false'}\n")
                if not has_hidden_key:
                    new_lines.append(f"Hidden={'false' if enable else 'true'}\n")
        lines = new_lines

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return True

def remove_autostart_entry(filename: str) -> bool:
    """Deletes an autostart desktop entry."""
    filepath = os.path.join(AUTOSTART_DIR, filename)
    if os.path.isfile(filepath):
        os.remove(filepath)
        return True
    return False

def add_app_by_id_or_path(app_id_or_path: str) -> bool:
    """Adds an installed application to ~/.config/autostart/."""
    os.makedirs(AUTOSTART_DIR, exist_ok=True)
    source_path = None
    if os.path.isfile(app_id_or_path):
        source_path = app_id_or_path
    else:
        # Search directories
        filename = app_id_or_path if app_id_or_path.endswith(".desktop") else f"{app_id_or_path}.desktop"
        for d in get_app_directories():
            cand = os.path.join(d, filename)
            if os.path.isfile(cand):
                source_path = cand
                break
    
    if not source_path:
        return False
    
    target_filename = os.path.basename(source_path)
    target_path = os.path.join(AUTOSTART_DIR, target_filename)

    # Read source and write target with autostart enabled
    with open(source_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    lines = content.splitlines()
    new_lines = []
    in_section = False
    has_gnome = False
    has_hidden = False

    for line in lines:
        s = line.strip()
        if s == "[Desktop Entry]":
            in_section = True
            new_lines.append(line)
            continue
        elif s.startswith("["):
            in_section = False

        if in_section:
            if s.startswith("X-GNOME-Autostart-enabled="):
                new_lines.append("X-GNOME-Autostart-enabled=true")
                has_gnome = True
                continue
            if s.startswith("Hidden="):
                new_lines.append("Hidden=false")
                has_hidden = True
                continue
        new_lines.append(line)

    if not has_gnome or not has_hidden:
        final_lines = []
        for line in new_lines:
            final_lines.append(line)
            if line.strip() == "[Desktop Entry]":
                if not has_gnome:
                    final_lines.append("X-GNOME-Autostart-enabled=true")
                if not has_hidden:
                    final_lines.append("Hidden=false")
        new_lines = final_lines

    with open(target_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")
    return True

def add_custom_entry(name: str, exec_cmd: str, icon: str = "application-x-executable", comment: str = "") -> bool:
    """Creates a custom autostart desktop entry."""
    os.makedirs(AUTOSTART_DIR, exist_ok=True)
    # Generate clean filename
    slug = re.sub(r'[^a-zA-Z0-9_-]', '_', name.lower()).strip('_')
    if not slug:
        slug = f"autostart_{int(time.time())}"
    filename = f"{slug}.desktop"
    target_path = os.path.join(AUTOSTART_DIR, filename)

    content = f"""[Desktop Entry]
Type=Application
Name={name}
Exec={exec_cmd}
Icon={icon or 'application-x-executable'}
Comment={comment or 'Custom autostart command'}
Terminal=false
X-GNOME-Autostart-enabled=true
Hidden=false
"""
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)
    return True

def is_process_running(cmd: str) -> bool:
    """Checks if a command / binary is already running without false positives."""
    parts = cmd.split()
    if not parts:
        return False
    binary = os.path.basename(parts[0])
    # Ignore wrappers like /usr/bin/flatpak or env or bash
    if binary in ("flatpak", "env", "bash", "sh", "python", "python3") and len(parts) > 1:
        for p in parts[1:]:
            if not p.startswith("-") and "." in p:
                binary = p
                break
    
    current_pid = os.getpid()
    target_clean = os.path.splitext(binary)[0].lower()

    for pid_str in os.listdir("/proc"):
        if not pid_str.isdigit() or int(pid_str) == current_pid:
            continue
        try:
            with open(f"/proc/{pid_str}/comm", "r", errors="ignore") as f:
                comm = f.read().strip().lower()
            if comm == target_clean or comm == binary.lower():
                return True

            with open(f"/proc/{pid_str}/cmdline", "rb") as f:
                raw = f.read().decode("utf-8", "ignore")
                cmdline = [arg for arg in raw.split("\x00") if arg]
            
            # Avoid matching python scripts or inspectors
            if "python" in comm and any("autostart" in a for a in cmdline):
                continue

            if any(binary in arg or target_clean in arg.lower() for arg in cmdline):
                return True
        except (IOError, OSError):
            continue

    return False

def ensure_display_env() -> None:
    """Ensures WAYLAND_DISPLAY and DISPLAY are set in environment."""
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    os.environ["XDG_RUNTIME_DIR"] = runtime_dir
    
    if not os.environ.get("WAYLAND_DISPLAY"):
        for sock in sorted(glob.glob(os.path.join(runtime_dir, "wayland-[0-9]*"))):
            if os.path.exists(sock):
                os.environ["WAYLAND_DISPLAY"] = os.path.basename(sock)
                break
        if not os.environ.get("WAYLAND_DISPLAY"):
            os.environ["WAYLAND_DISPLAY"] = "wayland-1"

    if not os.environ.get("DISPLAY"):
        os.environ["DISPLAY"] = ":0"

    os.environ.setdefault("XDG_CURRENT_DESKTOP", "Hyprland")
    os.environ.setdefault("XDG_SESSION_TYPE", "wayland")
    os.environ.setdefault("XDG_SESSION_DESKTOP", "Hyprland")

def run_single_entry(filename: str) -> bool:
    """Executes a single autostart entry detached."""
    ensure_display_env()
    filepath = os.path.join(AUTOSTART_DIR, filename)
    entry = parse_desktop_file(filepath)
    if not entry or not entry["exec"]:
        return False
    
    try:
        subprocess.Popen(
            entry["exec"],
            shell=True,
            start_new_session=True,
            env=os.environ.copy(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except Exception:
        return False

def run_all_autostart(force: bool = False) -> None:
    """Runs all enabled autostart desktop entries at system/hyprland boot."""
    ensure_display_env()
    instance_sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "default")
    user = os.environ.get("USER", "user")
    lock_file = f"/tmp/hypr-autostart-{user}-{instance_sig}.lock"

    import fcntl
    try:
        lock_fd = open(lock_file, "a+")
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, BlockingIOError):
        # Another instance is already running
        return

    entries = list_autostart_entries()

    if not force:
        lock_fd.seek(0)
        content = lock_fd.read().strip()
        if content:
            all_running = True
            for e in entries:
                if e["enabled"] and e["exec"] and not is_process_running(e["exec"]):
                    all_running = False
                    break
            if all_running:
                return

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"\n--- Autostart session started at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        
        for entry in entries:
            name = entry["name"]
            exec_cmd = entry["exec"]
            enabled = entry["enabled"]

            if not enabled:
                log.write(f"[SKIP] '{name}' is disabled.\n")
                continue
            
            if not exec_cmd:
                log.write(f"[SKIP] '{name}' has no Exec command.\n")
                continue

            # Check if already running to prevent multi-windows
            if is_process_running(exec_cmd):
                log.write(f"[RUNNING] '{name}' is already running. Skipping duplicate launch.\n")
                continue

            try:
                proc = subprocess.Popen(
                    exec_cmd,
                    shell=True,
                    start_new_session=True,
                    env=os.environ.copy(),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                log.write(f"[START] Launched '{name}' (PID {proc.pid}): {exec_cmd}\n")
                # Stagger launches slightly to prevent sudden spike during startup
                time.sleep(0.4)
            except Exception as e:
                log.write(f"[ERROR] Failed to launch '{name}': {e}\n")

    # Mark lock file after launch
    try:
        lock_fd.seek(0)
        lock_fd.truncate()
        lock_fd.write(str(time.time()))
        lock_fd.flush()
    except Exception:
        pass

def main():
    parser = argparse.ArgumentParser(description="Autostart Manager for Hyprland & Quickshell")
    subparsers = parser.add_subparsers(dest="command")

    # list
    subparsers.add_parser("list", help="List autostart applications as JSON")

    # list-apps
    subparsers.add_parser("list-apps", help="List all installed system/flatpak applications as JSON")

    # toggle
    toggle_p = subparsers.add_parser("toggle", help="Toggle enabled status")
    toggle_p.add_argument("filename", help="Desktop file name in ~/.config/autostart/")
    toggle_p.add_argument("state", help="true or false")

    # remove
    remove_p = subparsers.add_parser("remove", help="Remove autostart entry")
    remove_p.add_argument("filename", help="Desktop file name")

    # add-app
    add_app_p = subparsers.add_parser("add-app", help="Add application by ID or path")
    add_app_p.add_argument("app_id", help="Desktop file name or full path")

    # add-custom
    add_cust_p = subparsers.add_parser("add-custom", help="Add custom command")
    add_cust_p.add_argument("--name", required=True, help="Application display name")
    add_cust_p.add_argument("--exec", required=True, dest="exec_cmd", help="Command line to execute")
    add_cust_p.add_argument("--icon", default="application-x-executable", help="Icon name")
    add_cust_p.add_argument("--comment", default="", help="Description")

    # run-one
    run_one_p = subparsers.add_parser("run-one", help="Run a single autostart entry")
    run_one_p.add_argument("filename", help="Desktop file name")

    # run-all
    run_all_p = subparsers.add_parser("run-all", help="Run all enabled autostart entries")
    run_all_p.add_argument("--force", action="store_true", help="Force run even if lock file exists")

    args = parser.parse_args()

    if args.command == "list":
        print(json.dumps(list_autostart_entries(), indent=2))
    elif args.command == "list-apps":
        print(json.dumps(list_system_applications(), indent=2))
    elif args.command == "toggle":
        enable = args.state.lower() in ("true", "1", "yes", "on")
        ok = toggle_autostart_entry(args.filename, enable)
        print(json.dumps({"success": ok}))
    elif args.command == "remove":
        ok = remove_autostart_entry(args.filename)
        print(json.dumps({"success": ok}))
    elif args.command == "add-app":
        ok = add_app_by_id_or_path(args.app_id)
        print(json.dumps({"success": ok}))
    elif args.command == "add-custom":
        ok = add_custom_entry(args.name, args.exec_cmd, args.icon, args.comment)
        print(json.dumps({"success": ok}))
    elif args.command == "run-one":
        ok = run_single_entry(args.filename)
        print(json.dumps({"success": ok}))
    elif args.command == "run-all":
        run_all_autostart(force=args.force)
        print(json.dumps({"success": True}))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
