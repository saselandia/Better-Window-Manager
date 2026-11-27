#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Acciones de escritorio de Breeze: Emoji Selector y zoom de Hyprland."""
import fcntl
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
import bwm_session

RUNTIME = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
STATE = RUNTIME / "bwm-plasma-zoom.json"
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))

def skin():
    return json.loads((CONFIG / "illogical-impulse/config.json").read_text()).get("appearance", {}).get("bwmTheme")

def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=3).stdout

def zoom(action):
    with (RUNTIME / "bwm-plasma-zoom.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        current = float(json.loads(run("hyprctl", "getoption", "cursor:zoom_factor", "-j"))["float"])
        if not math.isfinite(current):
            raise ValueError("Invalid cursor zoom factor")
        saved = json.loads(STATE.read_text()) if STATE.exists() else {"previous": current}
        if action == "leave":
            if not STATE.exists():
                return 0
            target = saved["previous"] if math.isclose(current, saved["last"]) else current
        else:
            if skin() != "plasma":
                return 1
            target = 1.0 if action == "reset" else min(8.0, max(1.0, current * (1.2 if action == "in" else 1 / 1.2)))
        if not math.isclose(current, target):
            run("hyprctl", "eval", f"hl.config({{cursor={{zoom_factor={target:.8f}}}}})")
        if action == "leave":
            STATE.unlink(missing_ok=True)
        else:
            saved["last"] = round(target, 8)
            STATE.write_text(json.dumps(saved))
            STATE.chmod(0o600)
    return 0

def main(args):
    if args == ["emoji"]:
        if skin() != "plasma":
            return 1
        executable = shutil.which("plasma-emojier")
        if not executable:
            subprocess.run(["notify-send", "Breeze", "Falta plasma-emojier (plasma-desktop)"], check=False)
            return 1
        return 0 if bwm_session.spawn([executable], allow_fallback=False) else 1
    if len(args) == 2 and args[0] == "zoom" and args[1] in ("in", "out", "reset", "leave"):
        return zoom(args[1])
    return 2

if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f"Breeze: {error}", file=sys.stderr)
        raise SystemExit(1)
