#!/usr/bin/env python3
"""Seed Nautilus' native New Document menu once, preserving user templates."""

import os
from pathlib import Path
import subprocess


SOURCE = Path(__file__).resolve().parents[1] / "nautilus-templates"


def setup_templates(home=None, state_home=None):
    home = Path.home() if home is None else Path(home)
    state_home = Path(os.environ.get("XDG_STATE_HOME", home / ".local/state")) if state_home is None else Path(state_home)
    marker = state_home / "bwm/retro/nautilus-templates-v1"
    if marker.exists():
        return
    result = subprocess.run(["xdg-user-dir", "TEMPLATES"], check=True, capture_output=True, text=True, timeout=5)
    folder = Path(result.stdout.strip())
    if not folder.is_absolute():
        raise ValueError("xdg-user-dir TEMPLATES returned a non-absolute path")
    if folder == home:
        # XDG pointing at HOME means disabled; enable only Templates, not all dirs.
        folder = home / "Templates"
        folder.mkdir(parents=True, exist_ok=True)
        subprocess.run(["xdg-user-dirs-update", "--set", "TEMPLATES", str(folder)], check=True, timeout=5)
    else:
        folder.mkdir(parents=True, exist_ok=True)
    for source in SOURCE.iterdir():
        if not source.is_file():
            continue
        try:
            with (folder / source.name).open("xb") as destination:
                destination.write(source.read_bytes())
        except FileExistsError:
            pass
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(str(folder) + "\n", encoding="utf-8")


if __name__ == "__main__":
    setup_templates()
