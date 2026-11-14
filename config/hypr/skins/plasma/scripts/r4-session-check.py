#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Bounded R4 access diagnostic. No dispatch, window launch, restart or socket bridge."""
import argparse
import json
import math
import os
from pathlib import Path
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
    parser.add_argument('--report', type=Path, default=Path(tempfile.gettempdir()) / f'bwm-r4-access-{os.getuid()}.json')
    args = parser.parse_args()
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
