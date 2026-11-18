#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Read-only comparison of original KDE desktop information on every Hyprland output.

No panels, captures, activation requests or changes to the provider/configuration.
Run from the user's session terminal; this is not an automatic acceptance test.
"""
import argparse
import json
import math
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'config/hypr/scripts'))
from bwm_windows import monitor_box


def query(name):
    reply = subprocess.run(['hyprctl', '-j', name], capture_output=True, text=True, timeout=2, check=True)
    if len(reply.stdout) > 262144:
        raise ValueError('Compositor diagnostic exceeds the size limit')
    return json.loads(reply.stdout)


def ordinary(value):
    return type(value) is int and 0 < value <= 2147483647 and value != 99


def session_snapshot():
    provider = query('bwm-plasma-desktops')
    monitors, workspaces = query('monitors'), query('workspaces')
    if not isinstance(provider, dict) or not isinstance(monitors, list) or not isinstance(workspaces, list):
        raise ValueError('Invalid compositor diagnostic')
    required = ('enabled', 'providerAvailable', 'configuredCountAvailable')
    if (any(provider.get(key) is not True for key in required)
            or provider.get('arbitrationState') != 'active'
            or provider.get('providerRestartRequired') is not False):
        raise ValueError('The desktop provider is not available with active arbitration')
    count = provider.get('configuredCount')
    if type(count) is not int or not 1 <= count <= 100:
        raise ValueError('Invalid shared desktop count')
    ids = {n for n in range(1, count+1) if ordinary(n)}
    for space in workspaces:
        if not isinstance(space, dict):
            raise ValueError('Invalid workspace diagnostic')
        if ordinary(space.get('id')):
            ids.add(space['id'])
    outputs, descriptions, geometries, focused = [], set(), set(), []
    if not 1 <= len(monitors) <= 32:
        raise ValueError('Expected 1–32 active outputs')
    for monitor in monitors:
        description = monitor.get('description') if isinstance(monitor, dict) else None
        if not isinstance(description, str) or not description or len(description) > 1024 or description in descriptions:
            raise ValueError('Missing or ambiguous output description')
        descriptions.add(description)
        active = monitor.get('activeWorkspace', {}).get('id')
        if not ordinary(active):
            raise ValueError('Output has no ordinary active workspace')
        ids.add(active)
        values = [monitor.get(k) for k in ('x', 'y', 'width', 'height', 'scale')]
        if any(type(n) not in (int, float) or not math.isfinite(n) for n in values):
            raise ValueError('Invalid output geometry')
        x, y, width, height, scale = values
        transform = monitor.get('transform', 0)
        if (scale <= 0 or width <= 0 or height <= 0 or type(transform) is not int or transform not in range(8)
                or x != int(x) or y != int(y)):
            raise ValueError('Invalid output scale/transform/position')
        geometry = tuple(monitor_box(monitor))
        if geometry in geometries or min(geometry[2:]) <= 0:
            raise ValueError('Overlapping identical output rectangles cannot be distinguished by the KDE geometry API')
        geometries.add(geometry)
        outputs.append({'description': description, 'geometry': list(geometry),
                        'current': str(active)})
        if monitor.get('focused') is True:
            focused.append(str(active))
    if len(focused) != 1 or provider.get('current') != focused[0]:
        raise ValueError('Focused output and desktop provider disagree; retry with a stable workspace')
    expected_ids = [str(n) for n in sorted(ids)]
    if type(provider.get('desktops')) is not int or provider['desktops'] != len(expected_ids):
        raise ValueError('Desktop provider has not reconciled its workspace inventory; retry')
    # Only keep fields needed for consistency. No client/window data, desktop
    # names, runtime paths, PIDs or environment contents enter the report.
    return {'desktopIds': expected_ids, 'current': focused[0], 'configuredCount': count,
            'outputs': sorted(outputs, key=lambda output: output['description']),
            'countRevision': provider.get('countRevision')}


def compare(before, after, native):
    if before != after:
        raise ValueError('Workspaces or outputs changed during measurement; retry without switching')
    if (not isinstance(native, dict) or type(native.get('version')) is not int or native['version'] != 1
            or native.get('readOnly') is not True or native.get('ready') is not True):
        raise ValueError('The original KDE consumer did not return a ready read-only snapshot')
    control = native.get('control', {})
    if (not isinstance(control, dict) or control.get('bindingVerified') is not True
            or control.get('providerAvailable') is not True or control.get('resumed') is not False
            or type(control.get('serial')) is not int or control['serial'] != 0
            or type(native.get('windowCount')) is not int or native['windowCount'] != 0):
        raise ValueError('The native consumer is not a read-only connection with a verified provider')
    if (native.get('desktopIds') != before['desktopIds'] or native.get('current') != before['current']
            or type(native.get('desktops')) is not int or native['desktops'] != len(before['desktopIds'])):
        raise ValueError('KDE and Hyprland desktop inventories/current desktop disagree')
    outputs = native.get('outputs')
    if (not isinstance(outputs, list) or len(outputs) != len(before['outputs'])
            or type(native.get('qtScreenCount')) is not int or native['qtScreenCount'] != len(outputs)):
        raise ValueError('KDE and Hyprland output counts disagree')
    result = []
    for expected, observed in zip(before['outputs'], outputs):
        if (not isinstance(observed, dict) or observed.get('description') != expected['description']
                or observed.get('match') != 'matched' or observed.get('geometry') != expected['geometry']
                or observed.get('currentByName') != expected['current']
                or observed.get('currentByGeometry') != expected['current']):
            raise ValueError('KDE output identity/geometry/current desktop disagrees with Hyprland')
        result.append(dict(expected, verified=True))
    return result


def isolated_environment(root, source):
    runtime = Path(source.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}'))
    display = Path(source.get('WAYLAND_DISPLAY', 'wayland-0'))
    if not display.is_absolute():
        display = runtime/display
    env = dict(source, QT_QPA_PLATFORM='wayland', WAYLAND_DISPLAY=str(display),
               DBUS_SESSION_BUS_ADDRESS='unix:path='+str(root/'no-bus'),
               XDG_DATA_DIRS='/usr/local/share:/usr/share')
    for key in tuple(env):
        if key.startswith('BWM_R4_') or key in ('HYPRLAND_INSTANCE_SIGNATURE', 'KDESYCOCA', 'DISPLAY'):
            env.pop(key)
    for variable, directory in (('XDG_CONFIG_HOME', 'config'), ('XDG_DATA_HOME', 'data'),
                                ('XDG_CACHE_HOME', 'cache'), ('XDG_RUNTIME_DIR', 'runtime'),
                                ('XDG_CONFIG_DIRS', 'defaults')):
        env[variable] = str(root/directory)
    return env


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, default=Path(__file__).resolve().parents[2]/'build/bwm-plasma-host/bwm-plasma-host')
    args = parser.parse_args(argv)
    binary = args.binary.expanduser().resolve()
    report = {'version': 1, 'readOnly': True, 'passed': False,
              'sessionModified': False, 'panelsOpened': False, 'capturesStarted': False,
              'activationTested': False, 'replacementReady': False}
    try:
        if not binary.is_file() or not os.access(binary, os.X_OK):
            raise ValueError('No executable host at '+str(binary))
        before = session_snapshot()
        inherited = ()
        if os.environ.get('WAYLAND_SOCKET'):
            descriptor = int(os.environ['WAYLAND_SOCKET'])
            os.fstat(descriptor);inherited = (descriptor,)
        with tempfile.TemporaryDirectory(prefix='bwm-r4-desktops-check-') as tmp:
            root = Path(tmp)
            for directory in ('config', 'data', 'cache', 'runtime', 'defaults'):
                (root/directory).mkdir(mode=0o700)
            def no_core():
                resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            reply = subprocess.run([str(binary), '--check-native-desktops-session',
                                    *(output['description'] for output in before['outputs'])],
                                   env=isolated_environment(root, os.environ), pass_fds=inherited,
                                   capture_output=True, text=True, timeout=8, preexec_fn=no_core)
            if len(reply.stdout) > 65536:
                raise ValueError('Native KDE desktop diagnostic exceeds the size limit')
            try:
                native = json.loads(reply.stdout)
            except ValueError:
                raise ValueError('Native KDE desktop diagnostic returned no JSON (exit '+str(reply.returncode)+')') from None
            if reply.returncode:
                detail = native.get('error', 'snapshot not ready') if isinstance(native, dict) else 'invalid diagnostic'
                raise ValueError('Native KDE desktop diagnostic failed: '+str(detail))
        after = session_snapshot()
        report['outputs'] = compare(before, after, native)
        report.update(passed=True, desktopIds=before['desktopIds'], current=before['current'],
                      configuredCount=before['configuredCount'], bindingVerified=True,
                      activationRequestsSent=0, windowCount=0)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, subprocess.SubprocessError) as error:
        report['error'] = str(error)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
