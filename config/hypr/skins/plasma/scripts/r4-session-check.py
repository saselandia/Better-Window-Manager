#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Bounded R4 access diagnostic. No dispatch, window launch, restart or socket bridge."""
import argparse
import json
import math
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import tempfile


def query(argv, run=subprocess.run):
    try:
        result = run(argv, capture_output=True, text=True, timeout=3, check=False)
        if result.returncode:
            return {'ok': False, 'error': (result.stderr or result.stdout).strip()[:1000]}
        return {'ok': True, 'data': json.loads(result.stdout)}
    except subprocess.TimeoutExpired:
        return {'ok': False, 'error': 'Tiempo límite de 3 segundos agotado'}
    except (OSError, ValueError) as exc:
        return {'ok': False, 'error': str(exc)[:1000]}


def sockets(environment):
    root = Path(environment.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}'))
    signature = environment.get('HYPRLAND_INSTANCE_SIGNATURE', '')
    result = {'runtimeExists': root.is_dir(), 'instanceSignaturePresent': bool(signature)}
    # Never discover another session or serialize the instance signature.
    if signature and '/' not in signature and signature not in ('.', '..'):
        for name in ('.socket.sock', '.socket2.sock'):
            try:
                info = (root / 'hypr' / signature / name).lstat()
                result[name] = {'exists': True, 'isSocket': stat.S_ISSOCK(info.st_mode),
                                'ownedByCurrentUser': info.st_uid == os.getuid()}
            except OSError:
                result[name] = {'exists': False}
    return result


def monitors(value):
    if not isinstance(value, list) or not value:
        raise ValueError('No hay una lista de monitores activa válida')
    result = []
    for monitor in value:
        if not isinstance(monitor, dict): raise ValueError('Monitor inválido')
        for key in ('x', 'y', 'width', 'height', 'scale'):
            n = monitor.get(key)
            if type(n) not in (int, float) or not math.isfinite(n) or (key in ('width', 'height', 'scale') and n <= 0):
                raise ValueError(f'Geometría inválida: {key}')
        reserved = monitor.get('reserved')
        if not isinstance(reserved, list) or len(reserved) != 4 or any(type(n) not in (int, float) or not math.isfinite(n) or n < 0 for n in reserved):
            raise ValueError('Reserva de monitor inválida')
        # No client titles, addresses, workspace contents or arbitrary metadata.
        result.append({key: monitor[key] for key in ('name', 'description', 'x', 'y', 'width', 'height', 'scale', 'transform', 'reserved') if key in monitor})
    return result


def native_layers(value):
    if not isinstance(value, dict): raise ValueError('Respuesta de capas inválida')
    result = []
    for output, groups in value.items():
        if not isinstance(groups, dict) or not isinstance(groups.get('levels'), dict):
            raise ValueError('Grupos de capas inválidos')
        for level, entries in groups['levels'].items():
            if not isinstance(entries, list): raise ValueError('Lista de capas inválida')
            for entry in entries:
                if not isinstance(entry, dict): raise ValueError('Capa inválida')
                namespace = entry.get('namespace', '')
                if isinstance(namespace, str) and namespace.startswith('bwm-r4-'):
                    result.append({'output': output, 'level': level,
                                   **{k: entry[k] for k in ('namespace', 'x', 'y', 'w', 'h') if k in entry}})
    return result


def collect(run=subprocess.run, environment=None):
    result = {'version': 1, 'sessionModified': False, 'r4Complete': False,
              'realAreaVerified': False, 'environment': sockets(os.environ if environment is None else environment)}
    reply = query(['hyprctl', '-j', 'monitors'], run)
    if not reply['ok']:
        return {**result, 'status': 'ipc-unavailable', 'hyprland': reply}
    try:
        result['monitors'] = monitors(reply['data'])
    except ValueError as exc:
        return {**result, 'status': 'invalid-monitor-response', 'error': str(exc)}
    reply = query(['hyprctl', '-j', 'layers'], run)
    if not reply['ok']:
        return {**result, 'status': 'layers-unavailable', 'layers': reply}
    try:
        result['nativeLayers'] = native_layers(reply['data'])
    except ValueError as exc:
        return {**result, 'status': 'invalid-layer-response', 'error': str(exc)}
    reply = query([sys.executable, str(Path(__file__).with_name('panel-session.py')), 'status'], run)
    if not reply['ok']:
        return {**result, 'status': 'preview-status-unavailable', 'preview': reply}
    preview = reply['data']
    if not isinstance(preview, dict) or type(preview.get('active')) is not bool:
        return {**result, 'status': 'invalid-preview-response'}
    result['preview'] = preview
    result['status'] = 'observations-collected' if preview['active'] else 'access-ok-no-native-preview'
    return result


TRAY_WATCHER = 'org.kde.StatusNotifierWatcher'


def tray_services(run=subprocess.run):
    return tray_observation(run)[0]


def tray_observation(run=subprocess.run):
    """Inspect the current watcher on its unique name without starting or registering services."""
    base = ['busctl', '--user', '--auto-start=no', '--timeout=1']
    bus = ['org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus']
    result = {'version': 1, 'scope': 'status-notifier-watcher', 'readOnly': True,
              'sessionModified': False, 'watcherVerified': False, 'replacementReady': False}

    def call(arguments):
        reply = run(base + arguments, capture_output=True, text=True, timeout=2, check=True)
        return shlex.split(reply.stdout)

    def owner():
        value = call(['call', *bus, 'GetNameOwner', 's', TRAY_WATCHER])
        if len(value) != 2 or value[0] != 's' or not re.fullmatch(r':\d+\.\d+', value[1]):
            raise ValueError('Nombre único de D-Bus inválido')
        return value[1]

    phase = 'bus-unavailable'
    try:
        present = call(['call', *bus, 'NameHasOwner', 's', TRAY_WATCHER])
        if present == ['b', 'false']:
            return {**result, 'status': 'watcher-absent'}, None
        if present != ['b', 'true']:
            raise ValueError('La consulta de propietario de D-Bus devolvió un valor inválido')
        phase = 'watcher-unverified'
        current = owner()
        pid_reply = call(['call', *bus, 'GetConnectionUnixProcessID', 's', current])
        if len(pid_reply) != 2 or pid_reply[0] != 'u' or not pid_reply[1].isdigit() or int(pid_reply[1]) <= 0:
            raise ValueError('PID del dueño de la bandeja inválido')
        process = Path('/proc') / pid_reply[1]
        try:
            name = (process/'exe').resolve(strict=True).name if process.stat().st_uid == os.getuid() else ''
        except OSError:
            name = ''
        watcher = ['get-property', current, '/StatusNotifierWatcher', TRAY_WATCHER]
        items = call(watcher + ['RegisteredStatusNotifierItems'])
        host = call(watcher + ['IsStatusNotifierHostRegistered'])
        if (len(items) < 2 or items[0] != 'as' or not items[1].isdigit() or int(items[1]) != len(items)-2 or
                host not in (['b', 'true'], ['b', 'false'])):
            raise ValueError('Las propiedades de la bandeja no tienen el formato esperado')
        if owner() != current:
            return {**result, 'status': 'watcher-owner-changed'}, None
        kind = name if name in ('quickshell', 'kded6', 'plasmashell') else 'other' if name else 'unknown'
        return ({**result, 'status': 'watcher-observed', 'watcherVerified': True, 'ownerKind': kind,
                 'registeredItemCount': int(items[1]), 'hostRegistered': host[1] == 'true'},
                (current, tuple(sorted(items[2:]))))
    except (OSError, ValueError, subprocess.SubprocessError):
        return {**result, 'status': phase}, None


def save_report(path, result):
    path = Path(path).absolute()
    if path.exists() or path.is_symlink():
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise ValueError('El informe existente no es un archivo propio regular')
    fd, temporary = tempfile.mkstemp(prefix='.bwm-r4-check-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as file:
            json.dump(result, file, ensure_ascii=False, indent=2)
            file.write('\n')
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tray', action='store_true', help='Read-only StatusNotifierWatcher ownership and counts over D-Bus')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.tray:
        result = tray_services()
        if args.report is not None: save_report(args.report, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['watcherVerified'] else 2
    if args.report is None: args.report = Path(tempfile.gettempdir()) / f'bwm-r4-access-{os.getuid()}.json'
    result = collect()
    save_report(args.report, result)
    print(json.dumps({'status': result['status'], 'report': str(args.report.absolute()),
                      'r4Complete': False, 'realAreaVerified': False}, ensure_ascii=False, indent=2))
    return 0 if result['status'] in ('observations-collected', 'access-ok-no-native-preview') else 2


if __name__ == '__main__':
    try: raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f'BWM R4: {exc}', file=sys.stderr)
        raise SystemExit(1)
