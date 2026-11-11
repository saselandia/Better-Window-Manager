#!/usr/bin/env python3
"""Detect competing session services by D-Bus ownership, not process presence."""
import json
import os
from pathlib import Path
import signal
import shlex
import time
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


def repair_stale_tray():
    """kded queues module service names even with autoload=false (KF6 kded.cpp).

    Retire only a stale reservation with no functional watcher and only the harmless
    timezone module. A real watcher or other active KDE modules still needs a decision.
    """
    owner = conflict('trays')
    if not owner:
        return False
    try:
        args = ['busctl', '--user', '--auto-start=no', '--timeout=1']
        env = dict(os.environ, LC_ALL='C')
        probe = subprocess.run(args + ['get-property', SERVICES['trays'][0],
            '/StatusNotifierWatcher', SERVICES['trays'][0], 'RegisteredStatusNotifierItems'],
            capture_output=True, text=True, timeout=2, env=env)
        if probe.returncode == 0 or not any(reason in probe.stderr for reason in ('No such object', 'UnknownObject')):
            return False
        modules = subprocess.run(args + ['call', 'org.kde.kded6', '/kded',
            'org.kde.kded6', 'loadedModules'], capture_output=True, text=True,
            timeout=2, check=True, env=env)
        values = shlex.split(modules.stdout)
        if values[:1] != ['as'] or int(values[1]) != len(values[2:]) or set(values[2:]) - {'ktimezoned'}:
            return False
        if conflict('trays') != owner:
            return False
        os.kill(owner['pid'], signal.SIGTERM)
        for _ in range(100):
            if conflict('trays') != owner:
                return True
            time.sleep(0.02)
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        pass
    return False


def main():
    if len(sys.argv) == 3 and sys.argv[1] == 'resolve' and sys.argv[2] in SERVICES:
        resolve(sys.argv[2])
    else:
        if '--repair-stale' in sys.argv[1:]:
            repair_stale_tray()
        print(json.dumps({group: conflict(group) for group in SERVICES}))


if __name__ == '__main__':
    main()
