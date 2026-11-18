#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Opt-in R4 check of maximize/area tracking on other scales and transforms.

The physical monitors are never reconfigured. ``--run`` creates one temporary
Hyprland headless output with a unique name, applies the requested mode, scale
and transform with a monitor rule, and changes its reserved area through the
same rule (``reserved``), which Hyprland 0.56 adds to the layer reservations.
An owned Qt window (the R4 maximize fixture) is maximized there with the common
KWin-style manager, and its frame is compared with the useful area computed
independently by r4-maximized-check.useful_area(). The automatic adjustment of
the existing bridge observer is read before any explicit re-maximize.

Headless outputs have no EDID description, so this check addresses only the
output it created by its connector name. The native panel host keeps its
description-only identity; reservations by the native panel on these
geometries are outside this check.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[5]
BINARY = ROOT / 'build/bwm-plasma-host/bwm-plasma-host'
spec = importlib.util.spec_from_file_location('r4_geometry_maximized', Path(__file__).with_name('r4-maximized-check.py'))
maximized = importlib.util.module_from_spec(spec); spec.loader.exec_module(maximized)
sys.path.insert(0, str(ROOT / 'config/hypr/scripts'))
import bwm_windows  # noqa: E402

# mode, scale, transform. Every logical size is integral: Hyprland 0.56 rejects
# scales that are not clean divisors of the mode and would pick another one.
DEFAULT_CASES = [('1920x1200', 1.25, 1), ('1920x1080', 1.5, 3), ('2560x1600', 1.6, 2), ('1920x1200', 1.25, 5)]
RESERVED = {'top': 48}
CASE = re.compile(r'^(\d{3,5})x(\d{3,5}):(\d+(?:\.\d+)?):([0-7])$')


def parse_case(text):
    match = CASE.match(text)
    if not match: raise argparse.ArgumentTypeError('Formato: ANCHOxALTO:ESCALA:GIRO (giro 0-7)')
    width, height, scale, transform = int(match[1]), int(match[2]), float(match[3]), int(match[4])
    logical = (height, width) if transform % 2 else (width, height)
    if not 0.5 <= scale <= 4 or any(abs(v / scale - round(v / scale)) > 1e-6 for v in logical):
        raise argparse.ArgumentTypeError('La escala debe dividir el modo exactamente (Hyprland la rechazaría)')
    return (f'{width}x{height}', scale, transform)


def hypr(*args, timeout=4):
    reply = subprocess.run(['hyprctl', *args], capture_output=True, text=True, timeout=timeout)
    if reply.returncode: raise RuntimeError(f"hyprctl {' '.join(args[:2])}: {(reply.stderr or reply.stdout).strip()[-300:]}")
    return reply.stdout


def monitors():
    data = json.loads(hypr('-j', 'monitors'))
    if not isinstance(data, list): raise RuntimeError('Lista de monitores inválida')
    return data


def lua_rule(name, mode, scale, transform, reserved=None):
    gap = '0' if not reserved else '{' + ', '.join(f'{k}={int(v)}' for k, v in reserved.items()) + '}'
    return (f'hl.monitor({{output="{name}", mode="{mode}@60", position="12000x0", '
            f'scale={scale}, transform={transform}, reserved={gap}}})')


def wait_monitor(name, predicate, seconds=5):
    deadline = time.monotonic() + seconds
    last = None
    while True:
        last = next((m for m in monitors() if m.get('name') == name), None)
        if last is not None and predicate(last):
            # Layer reservations (the daily panel on this output) follow the
            # monitor change asynchronously: require the same value twice.
            time.sleep(.4)
            again = next((m for m in monitors() if m.get('name') == name), None)
            if again is not None and predicate(again) and again.get('reserved') == last.get('reserved'): return again
        if time.monotonic() >= deadline: raise RuntimeError(f'La salida temporal no alcanzó el estado esperado: {last}')
        time.sleep(.15)


def configured(mode, scale, transform):
    width, height = (int(v) for v in mode.split('x'))
    return lambda m: (m.get('width'), m.get('height'), m.get('transform')) == (width, height, transform) and abs(m.get('scale', 0) - scale) < 1e-6


def physical_state():
    return {m['description']: [m.get(k) for k in ('x', 'y', 'width', 'height', 'scale', 'transform', 'reserved')] + [m.get('activeWorkspace', {}).get('id')]
            for m in monitors() if m.get('description')}


def phase(fixture, monitor):
    """Automatic reading first; an explicit re-maximize only if it does not match."""
    automatic = fixture.measure(monitor, remaximize=False)
    result = {'automatic': automatic, 'remaximized': False}
    if not automatic.get('matches'):
        result['explicit'] = fixture.measure(monitor)
        result['remaximized'] = True
    return result


def run_case(fixture, name, case):
    mode, scale, transform = case
    hypr('eval', lua_rule(name, mode, scale, transform))
    base = wait_monitor(name, configured(mode, scale, transform))
    record = {'mode': mode, 'scale': scale, 'transform': transform, 'logicalArea': maximized.useful_area(dict(base, reserved=[0, 0, 0, 0]))}
    record['before'] = {'reserved': base['reserved'], **fixture.measure(base)}
    hypr('eval', lua_rule(name, mode, scale, transform, RESERVED))
    grown = wait_monitor(name, lambda m: configured(mode, scale, transform)(m) and m['reserved'][1] >= base['reserved'][1] + RESERVED['top'])
    record['withReserved'] = {'reserved': grown['reserved'], **phase(fixture, grown)}
    hypr('eval', lua_rule(name, mode, scale, transform))
    back = wait_monitor(name, lambda m: configured(mode, scale, transform)(m) and m['reserved'] == base['reserved'])
    record['after'] = {'reserved': back['reserved'], **phase(fixture, back)}
    record['explicitVerified'] = record['before'].get('matches') is True and all(
        p.get('automatic', {}).get('matches') or p.get('explicit', {}).get('matches') for p in (record['withReserved'], record['after']))
    record['dynamicVerified'] = record['withReserved']['automatic'].get('matches') is True and record['after']['automatic'].get('matches') is True
    return record


def run(args):
    if not args.binary.is_file() or not os.access(args.binary, os.X_OK):
        raise SystemExit(f'Falta el auxiliar compilado: {args.binary}')
    skin = subprocess.run([sys.executable, str(ROOT / 'config/hypr/scripts/bwm-theme-manager.py'), 'get'], capture_output=True, text=True, timeout=10).stdout.strip()
    if skin != 'plasma': raise SystemExit('El observador de área sólo actúa en Breeze: activa la skin plasma')
    report = {'version': 1, 'scope': 'temporary-headless-output', 'physicalOutputsTouched': False, 'cases': [], 'errors': []}
    physical = physical_state()
    focus = bwm_windows.snapshot_focus(media=False)
    name = 'BWMR4-' + uuid.uuid4().hex[:8]
    rule = 'tmp-bwm-r4-geometry-' + name.lower()
    fixture = None
    created = False
    try:
        if args.refresh_area_watcher:
            report['areaObserverReload'] = maximized.refresh_area_observer()
        hypr('output', 'create', 'headless', name); created = True
        first = args.case[0]
        hypr('eval', lua_rule(name, *first))
        monitor = wait_monitor(name, configured(*first))
        workspace = monitor['activeWorkspace']['id']
        fixture = maximized.Fixture(args.binary, name, selector=name)
        # Map the owned window directly on the temporary output, without focus.
        hypr('eval', f'hl.window_rule({{ name = "{rule}", match = {{ class = "^{fixture.app_id.replace(".", "[.]")}$" }}, workspace = "{workspace} silent" }})')
        fixture.start()
        for case in args.case:
            try: report['cases'].append(run_case(fixture, name, case))
            except (RuntimeError, ValueError) as error:
                report['errors'].append(f'{case}: {error}'); break
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError, TimeoutError) as error:
        report['errors'].append(str(error))
    finally:
        if fixture is not None: fixture.close()
        try: hypr('eval', f'hl.window_rule({{ name = "{rule}", match = {{ class = "^bwm-r4-geometry-never-matches$" }}, workspace = "1 silent" }})')
        except RuntimeError as error: report['errors'].append(f'regla temporal: {error}')
        if created:
            try: hypr('output', 'remove', name)
            except RuntimeError as error: report['errors'].append(f'salida temporal: {error}')
        try: bwm_windows.restore_focus(focus)
        except Exception as error: report['errors'].append(f'foco: {error}')
        time.sleep(.5)
        left = [m.get('name') for m in monitors() if str(m.get('name', '')).startswith('BWMR4-')]
        report['cleanupVerified'] = not left and physical_state() == physical
        if not report['cleanupVerified']: report['errors'].append(f'Limpieza incompleta: salidas {left}, físicas {physical_state()}')
    report['explicitVerified'] = bool(report['cases']) and len(report['cases']) == len(args.case) and all(c['explicitVerified'] for c in report['cases'])
    report['dynamicVerified'] = report['explicitVerified'] and all(c['dynamicVerified'] for c in report['cases'])
    report['passed'] = report['explicitVerified'] and report['dynamicVerified'] and report['cleanupVerified'] and not report['errors']
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--run', action='store_true', help='Crear la salida temporal y medir')
    parser.add_argument('--case', action='append', type=parse_case, help='ANCHOxALTO:ESCALA:GIRO; repetible')
    parser.add_argument('--refresh-area-watcher', action='store_true', help='Recargar antes el puente existente')
    parser.add_argument('--binary', type=Path, default=BINARY)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args(argv)
    if not args.run: parser.error('Indica --run: crea una salida headless temporal')
    args.case = args.case or DEFAULT_CASES
    report = run(args)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.report:
        args.report.write_text(text + '\n'); os.chmod(args.report, 0o600)
    print(text)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
