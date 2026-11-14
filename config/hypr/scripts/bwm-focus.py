#!/usr/bin/env python3
"""Common, PID-checked activation of normal, special and minimized windows."""
import argparse
import importlib.util
import re
from pathlib import Path

import bwm_windows


def load_minimizer():
    spec = importlib.util.spec_from_file_location("bwm_minimize", Path(__file__).with_name("toggle-minimize.py"))
    minimizer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(minimizer)
    return minimizer


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("address")
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--restore-on-current", action="store_true",
                        help="Dock policy: restore normal windows here, preserve special origins")
    args = parser.parse_args(argv)
    if args.pid <= 0 or not re.fullmatch(r"0x[0-9a-fA-F]+", args.address):
        parser.error("a window address and a positive PID are required")
    clients = bwm_windows.hypr_json("clients")
    if not isinstance(clients, list):
        return 1
    client = next((c for c in clients if isinstance(c, dict)
                   if c.get("address") == args.address and c.get("pid") == args.pid), None)
    if not client:
        return 1
    minimizer = load_minimizer()
    if minimizer.is_minimized(client):
        minimizer.restore_win(client, on_current_workspace=args.restore_on_current)
    else:
        bwm_windows.focus_window(client)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
