#!/usr/bin/env python3
"""Detect competing session services by D-Bus ownership, not process presence."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

SERVICES = {
    'trays': ('org.kde.StatusNotifierWatcher', {'kded6'}),
    'notifications': ('org.freedesktop.Notifications', {'mako', 'dunst'}),
}


def conflict(group):
    service, executables = SERVICES[group]
    try:
        result = subprocess.run(
            ['busctl', '--user', '--auto-start=no', '--timeout=1', 'call',
             'org.freedesktop.DBus', '/org/freedesktop/DBus',
             'org.freedesktop.DBus', 'GetConnectionUnixProcessID', 's', service],
            capture_output=True, text=True, timeout=2, check=True)
        signature, value = result.stdout.strip().split()
        if signature != 'u':
            return None
        pid = int(value)
        process = Path('/proc') / str(pid)
        # Never report or signal another user's service.
        if process.stat().st_uid != os.getuid():
            return None
        name = (process / 'exe').resolve(strict=True).name
        if name in executables:
            return {'pid': pid, 'name': name}
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    return None


def resolve(group):
    # Re-query at the time of the action. Do not kill all processes of that name.
    owner = conflict(group)
    if owner and conflict(group) == owner:
        try:
            os.kill(owner['pid'], signal.SIGTERM)
        except ProcessLookupError:
            pass


def main():
    if len(sys.argv) == 3 and sys.argv[1] == 'resolve' and sys.argv[2] in SERVICES:
        resolve(sys.argv[2])
    else:
        print(json.dumps({group: conflict(group) for group in SERVICES}))


if __name__ == '__main__':
    main()
