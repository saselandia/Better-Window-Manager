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
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
BINARY = ROOT / 'build/bwm-plasma-host/test-editmode-session'
FRACTIONAL_SCALES = ((1920, 1080, 1.25, 1536, 864), (1920, 1080, 1.5, 1280, 720), (1920, 1080, 1.6, 1200, 675))


def hypr(*args):
    reply = subprocess.run(['hyprctl', *args], capture_output=True, text=True, timeout=5)
    if reply.returncode != 0:
        raise RuntimeError(f'hyprctl {" ".join(args)}: {(reply.stderr or reply.stdout).strip()}')
    return reply.stdout


def monitors():
    return json.loads(hypr('-j', 'monitors'))


def focused_output():
    focused = [m.get('description', '').strip() for m in monitors() if m.get('focused') is True]
    if len(focused) != 1 or not focused[0]:
        raise ValueError('No se pudo identificar el monitor enfocado; indica --output.')
    return focused[0]


def run_fractional_scales(args, display, runtime):
    physical_before = sorted((m['name'], m['x'], m['y'], m['width'], m['height'], m['scale'])
                             for m in monitors() if not str(m.get('name', '')).startswith('BWMR5-'))
    name = 'BWMR5-' + uuid.uuid4().hex[:8]
    created = False
    all_steps = []
    passed = True
    try:
        hypr('output', 'create', 'headless', name)
        created = True
        for phys_w, phys_h, scale, exp_w, exp_h in FRACTIONAL_SCALES:
            hypr('eval', f'hl.monitor({{output="{name}",mode="{phys_w}x{phys_h}@60",position="7000x0",scale={scale}}})')
            deadline = time.monotonic() + 5.0
            while time.monotonic() < deadline:
                found = [m for m in monitors() if m.get('name') == name and abs(float(m.get('scale', 0)) - scale) < 0.02]
                if found:
                    break
                time.sleep(0.08)
            else:
                raise RuntimeError(f'La salida temporal {name} no aplicó la escala {scale}')
            time.sleep(0.4)
            with tempfile.TemporaryDirectory(prefix='bwm-r5-fractional-') as directory:
                root = Path(directory)
                env = {k: v for k, v in os.environ.items()
                       if not k.startswith(('DBUS_', 'BWM_R4_', 'BWM_R5_', 'QT_')) and k not in ('DISPLAY', 'WAYLAND_SOCKET')}
                for variable, sub in {'XDG_CONFIG_HOME': 'config', 'XDG_CACHE_HOME': 'cache', 'XDG_DATA_HOME': 'data',
                                      'XDG_RUNTIME_DIR': 'runtime', 'XDG_STATE_HOME': 'state'}.items():
                    (root / sub).mkdir(mode=0o700)
                    env[variable] = str(root / sub)
                env.update(WAYLAND_DISPLAY=str(display.resolve(strict=True)), QT_QPA_PLATFORM='wayland',
                           BWM_R5_HEADLESS_OUTPUT=name, BWM_R5_HYPR_RUNTIME=runtime,
                           BWM_R5_EXPECTED_SCALE=str(scale), BWM_R5_EXPECTED_W=str(exp_w), BWM_R5_EXPECTED_H=str(exp_h),
                           DBUS_SESSION_BUS_ADDRESS=f'unix:path={root}/no-session-bus',
                           DBUS_SYSTEM_BUS_ADDRESS=f'unix:path={root}/no-system-bus')
                reply = subprocess.run([args.binary, 'fractionalScaleEditModeInHyprland'], env=env,
                                       capture_output=True, text=True, timeout=60)
                for line in reply.stdout.splitlines():
                    if line.startswith('{"steps"'):
                        all_steps.extend(json.loads(line)['steps'])
                if reply.returncode != 0:
                    passed = False
                    sys.stderr.write(reply.stdout[-4000:] + reply.stderr[-4000:])
                    break
    finally:
        if created:
            try:
                hypr('output', 'remove', name)
            except RuntimeError as error:
                passed = False
                sys.stderr.write(f'{error}\n')
        time.sleep(0.3)
    physical_after = sorted((m['name'], m['x'], m['y'], m['width'], m['height'], m['scale'])
                            for m in monitors() if not str(m.get('name', '')).startswith('BWMR5-'))
    leftover = [m['name'] for m in monitors() if str(m.get('name', '')).startswith('BWMR5-')]
    cleanup_ok = not leftover and physical_before == physical_after
    print(json.dumps({'passed': passed and cleanup_ok, 'headlessOutput': name,
                      'physicalOutputsUnchanged': physical_before == physical_after,
                      'steps': all_steps}, ensure_ascii=False, indent=2))
    return 0 if (passed and cleanup_ok) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', help='Descripción del monitor (por defecto, el enfocado)')
    parser.add_argument('--binary', default=str(BINARY))
    parser.add_argument('--case', help='Run one QtTest case instead of the full session suite')
    parser.add_argument('--fractional-scale', action='store_true',
                        help='Prueba el editor a escalas fraccionarias (1.25, 1.5, 1.6) en una salida headless temporal')
    args = parser.parse_args()
    if not os.environ.get('WAYLAND_DISPLAY') or not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):
        parser.error('Ejecútalo desde la sesión de Hyprland.')
    runtime = os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')
    display = Path(os.environ['WAYLAND_DISPLAY'])
    if not display.is_absolute():
        display = Path(runtime) / display
    if args.fractional_scale:
        return run_fractional_scales(args, display, runtime)
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
        reply = subprocess.run([args.binary] + ([args.case] if args.case else []), env=env, capture_output=True, text=True, timeout=180)
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
