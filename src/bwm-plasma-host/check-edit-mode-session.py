#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""R5: drive the original Panel Settings of a disposable panel in the running Hyprland.

The test panel lives 64 px above the chosen edge of one output, never reserves space
and is removed at the end. Every XDG root is temporary; no pointer or keyboard device
is used. hyprctl only reads the layer list of the session.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BINARY = ROOT / 'build/bwm-plasma-host/test-editmode-session'


def focused_output():
    monitors = json.loads(subprocess.run(['hyprctl', '-j', 'monitors'], capture_output=True, text=True,
                                         timeout=3, check=True).stdout)
    focused = [m.get('description', '').strip() for m in monitors if m.get('focused') is True]
    if len(focused) != 1 or not focused[0]:
        raise ValueError('No se pudo identificar el monitor enfocado; indica --output.')
    return focused[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', help='Descripción del monitor (por defecto, el enfocado)')
    parser.add_argument('--binary', default=str(BINARY))
    args = parser.parse_args()
    if not os.environ.get('WAYLAND_DISPLAY') or not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):
        parser.error('Ejecútalo desde la sesión de Hyprland.')
    runtime = os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')
    display = Path(os.environ['WAYLAND_DISPLAY'])
    if not display.is_absolute():
        display = Path(runtime) / display
    output = args.output.strip() if args.output else focused_output()
    with tempfile.TemporaryDirectory(prefix='bwm-r5-edit-session-') as directory:
        root = Path(directory)
        env = {k: v for k, v in os.environ.items()
               if not k.startswith(('DBUS_', 'BWM_R4_', 'BWM_R5_', 'QT_')) and k not in ('DISPLAY', 'WAYLAND_SOCKET')}
        for variable, name in {'XDG_CONFIG_HOME': 'config', 'XDG_CACHE_HOME': 'cache', 'XDG_DATA_HOME': 'data',
                               'XDG_RUNTIME_DIR': 'runtime', 'XDG_STATE_HOME': 'state'}.items():
            (root / name).mkdir(mode=0o700)
            env[variable] = str(root / name)
        env.update(WAYLAND_DISPLAY=str(display.resolve(strict=True)), QT_QPA_PLATFORM='wayland',
                   BWM_R5_OUTPUT=output, BWM_R5_HYPR_RUNTIME=runtime,
                   DBUS_SESSION_BUS_ADDRESS=f'unix:path={root}/no-session-bus',
                   DBUS_SYSTEM_BUS_ADDRESS=f'unix:path={root}/no-system-bus')
        reply = subprocess.run([args.binary], env=env, capture_output=True, text=True, timeout=120)
    steps = None
    for line in reply.stdout.splitlines():
        if line.startswith('{"steps"'):
            steps = (steps or []) + json.loads(line)['steps']
    print(json.dumps({'passed': reply.returncode == 0, 'output': output, 'steps': steps}, ensure_ascii=False, indent=2))
    if reply.returncode != 0:
        sys.stderr.write(reply.stdout[-6000:] + reply.stderr[-6000:])
    return 0 if reply.returncode == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
