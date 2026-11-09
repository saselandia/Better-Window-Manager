#!/usr/bin/env python3
"""Omarchy's background collection plus BWM's shared Pictures/Wallpapers.

After Omarchy quattro cbd0029f, bin/omarchy-theme-bg-switcher (MIT,
Copyright (c) David Heinemeier Hansson). The picker and its protocol are
Omarchy's; BWM resolves its theme catalog and adds the shared directory.
"""
import argparse
from pathlib import Path
import subprocess
import sys

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import bwm_omarchy as omarchy


def background_directories():
    mode, name = omarchy.get_retro_mode()
    directories = []
    if mode == "static":
        try:
            directories.append(omarchy.theme_directory(name) / "backgrounds")
        except ValueError:
            pass
    directories.extend((omarchy.CONFIG_DIR / "omarchy" / "backgrounds" / name,
                        omarchy.HOME / "Pictures" / "Wallpapers"))
    # Symlinked copies of the same collection need only one scan.
    return list(dict.fromkeys(path.resolve() for path in directories if path.is_dir()))


def current_background():
    # This is the original media path, including videos and WebP originals;
    # Omarchy's background link can instead point at a compatibility poster.
    try:
        return (omarchy.HOME / ".cache" / "current_wallpaper_retro").read_text().strip()
    except OSError:
        return str(omarchy.OMARCHY_CURRENT_BG_LINK.resolve()) if omarchy.OMARCHY_CURRENT_BG_LINK.is_file() else ""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--select", action="store_true", help="Return the selected path without applying it")
    parser.add_argument("--print-dirs", action="store_true", help="List the current collection without opening the picker")
    parser.add_argument("--print-rows", action="store_true", help="Prepare and list the original picker's thumbnail rows")
    args = parser.parse_args()
    directories = background_directories()
    if args.print_dirs:
        print("\n".join(map(str, directories)))
        return 0
    if not directories:
        return 0
    command = [str(SCRIPTS / "omarchy-shims" / "omarchy-menu-images"),
               "--selected", current_background()]
    if args.print_rows:
        command.append("--print-rows")
    command.extend(map(str, directories))
    if args.select or args.print_rows:
        return subprocess.run(command).returncode
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        print(result.stderr, file=sys.stderr, end="")
        return result.returncode
    selected = result.stdout.rstrip("\n")
    if not selected:
        return 0
    # A skin switch may have happened while the selector was open.
    active = subprocess.run([sys.executable, str(SCRIPTS / "bwm-theme-manager.py"), "get"],
                            capture_output=True, text=True)
    if active.stdout.strip() != "retro":
        return 0
    return subprocess.run([str(SCRIPTS / "omarchy-shims" / "omarchy-theme-bg-set"), selected]).returncode


if __name__ == "__main__":
    raise SystemExit(main())
