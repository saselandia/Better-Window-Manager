#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Publish skin events only to an explicitly registered, isolated R4 preview.

No helper spawning, panel replacement, compositor calls or user configuration writes.
"""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import time


def registry_directory():
    return Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')) / 'bwm-plasma-host-preview'


def private_directory(path, *, temporary=False, create=False):
    path = Path(path).absolute()
    if create: path.mkdir(mode=0o700, parents=False, exist_ok=True)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or path.resolve() != path or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('El directorio de la prueba debe ser privado y no un enlace')
    if temporary and Path(tempfile.gettempdir()).resolve() not in path.parents:
        raise ValueError('El control debe estar en una raíz temporal explícita')
    return path


def read_json(path):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_size > 65536:
        raise ValueError('Metadatos de prueba inválidos o no privados')
    value = json.loads(path.read_text())
    if not isinstance(value, dict): raise ValueError('Los metadatos deben ser un objeto')
    return value


def atomic_json(path, value):
    fd, name = tempfile.mkstemp(prefix='.panel-session-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as file:
            json.dump(value, file, ensure_ascii=False);file.write('\n');file.flush();os.fsync(file.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


# A transaction holder may still be in its last 10 ms poll after the host acknowledged
# (the wrapper's startup skin, a status check). Callers wait this long, never more, and
# still get BlockingIOError if the holder is a real long transaction (a session exit
# waiting for the host to save): callers' own budgets (hook 3 s, bwm-power 8 s) hold.
LOCK_WAIT = 0.5


@contextmanager
def locked(path, *, wait=0.0):
    flags = os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('El bloqueo de la prueba no es privado')
        deadline = time.monotonic() + wait
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline: raise
                time.sleep(0.01)
        yield
    finally:
        os.close(fd)


def process_start(pid):
    if type(pid) is not int or pid <= 0: return None
    try:
        fields=Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        return None if fields[0] in ('Z','X') else fields[19]
    except (OSError, IndexError):
        return None


def active_registration():
    directory = registry_directory()
    if not directory.exists(): return None
    directory = private_directory(directory)
    path = directory / 'active.json'
    if not path.exists(): return None
    registration = read_json(path)
    if registration.get('version') != 1 or not re.fullmatch('[a-f0-9]{64}', str(registration.get('token', ''))):
        raise ValueError('Registro de prueba no reconocido')
    if not registration.get('processStart') or process_start(registration.get('pid')) != registration['processStart']:
        return None  # Dead/reused PID cannot turn a stale registration into a command.
    private_directory(registration['controlDirectory'], temporary=True)
    return registration


def register(control_directory, pid, token, *, reports_exit=False):
    control = private_directory(control_directory, temporary=True)
    ack = read_json(control / 'ack.json')
    start = process_start(pid)
    if not start or not re.fullmatch('[a-f0-9]{64}', token) or ack.get('version') != 1 or ack.get('token') != token or ack.get('ok') is not True or ack.get('command') != 'skin':
        raise ValueError('El auxiliar no ha confirmado esta prueba')
    directory = private_directory(registry_directory(), create=True)
    with locked(directory / 'registry.lock'):
        if active_registration() is not None: raise ValueError('Ya hay una prueba de panel registrada')
        atomic_json(directory / 'active.json', {'version': 1, 'controlDirectory': str(control),
                    'token': token, 'pid': pid, 'processStart': start,
                    'compositorInstance': os.environ.get('HYPRLAND_INSTANCE_SIGNATURE', ''),
                    'reportsExit': reports_exit})


def unregister(token):
    directory = registry_directory()
    if not directory.exists(): return
    directory = private_directory(directory)
    with locked(directory / 'registry.lock'):
        path = directory / 'active.json'
        if path.exists() and read_json(path).get('token') == token: path.unlink()


def drain(control_directory, *, timeout=2):
    """Let a stop publisher consume its ack before the wrapper removes temporary files."""
    directory=private_directory(control_directory,temporary=True)
    deadline=time.monotonic()+timeout
    while True:
        try:
            with locked(directory/'transaction.lock'): return
        except BlockingIOError:
            if time.monotonic()>=deadline:raise TimeoutError('Sigue habiendo una transacción de la prueba en curso')
            time.sleep(.01)


def record_exit(control_directory, token, returncode):
    """Publish only after wait() has reaped the host and released its profile lease."""
    directory = private_directory(control_directory, temporary=True)
    ack = read_json(directory / 'ack.json')
    revision = ack.get('revision')
    if (ack.get('version') == 1 and ack.get('token') == token and type(revision) is int and
            ack.get('ok') is True and ack.get('command') == 'stop' and ack.get('skin') == 'default'):
        atomic_json(directory / 'exit.json', {'version': 1, 'token': token,
                    'revision': revision, 'returncode': returncode})


def wait_for_exit(directory, registration, revision, deadline):
    while time.monotonic() < deadline:
        try:
            receipt = read_json(directory / 'exit.json')
        except FileNotFoundError:
            time.sleep(0.01)
            continue
        if (receipt.get('version') != 1 or receipt.get('token') != registration['token'] or
                type(receipt.get('revision')) is not int or receipt['revision'] != revision or
                type(receipt.get('returncode')) is not int):
            raise ValueError('La confirmación de salida no corresponde a esta retirada')
        if receipt['returncode'] != 0:
            raise ValueError(f"El auxiliar de panel terminó con código {receipt['returncode']} después de retirar las vistas")
        return {'status': 'stopped', 'revision': revision, 'exitConfirmed': True}
    raise TimeoutError('El auxiliar retiró las vistas pero no confirmó el guardado y la salida')


def command(registration, action, skin='default', *, timeout=1.5, exit_timeout=None):
    if exit_timeout is not None and action != 'stop':
        raise ValueError('La confirmación de salida requiere una orden de parada')
    directory = private_directory(registration['controlDirectory'], temporary=True)
    with locked(directory / 'transaction.lock', wait=LOCK_WAIT):
        if exit_timeout is not None and process_start(registration['pid']) != registration['processStart']:
            raise ValueError('La prueba registrada ya ha terminado')
        current = read_json(directory / 'control.json')
        revision = current.get('revision')
        if current.get('version') != 1 or current.get('token') != registration['token'] or type(revision) is not int or not 0 <= revision <= 2**53 - 1:
            raise ValueError('El control pertenece a otra prueba o su revisión no es válida')
        if action not in ('skin', 'stop', 'status') or skin not in ('plasma', 'retro', 'default'):
            raise ValueError('Orden de prueba no reconocida')
        # A plain stop may already have been sent. Preserve its receipt revision.
        if exit_timeout is None or current.get('command') != 'stop':
            if revision == 2**53 - 1:
                raise ValueError('Se ha agotado la revisión del control del panel')
            revision += 1
            atomic_json(directory / 'control.json', {'version': 1, 'token': registration['token'],
                        'revision': revision, 'command': action, 'skin': skin})
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try: ack = read_json(directory / 'ack.json')
            except FileNotFoundError: ack = {}
            if (ack.get('version') == 1 and ack.get('token') == registration['token'] and
                    type(ack.get('revision')) is int and ack['revision'] == revision and ack.get('ok') is True):
                expected = ack.get('skin') if action == 'status' else ('default' if action == 'stop' else skin)
                if expected not in ('plasma', 'retro', 'default'):
                    raise ValueError('La confirmación contiene un estilo desconocido')
                if ack.get('skin') != expected or ack.get('command') != action:
                    raise ValueError('La confirmación no corresponde a la orden')
                if exit_timeout is not None:
                    return wait_for_exit(directory, registration, revision, time.monotonic() + exit_timeout)
                result = {'status': 'acknowledged', 'revision': revision, 'skin': expected}
                if action == 'status':
                    runtime = ack.get('runtime')
                    if not isinstance(runtime, dict) or runtime.get('version') != 1 or runtime.get('skin') != expected or runtime.get('scope') != 'isolated-preview' or runtime.get('replacementReady') is not False or type(runtime.get('renderReady')) is not bool or not isinstance(runtime.get('panels'), list) or not isinstance(runtime.get('blockers'), list):
                        raise ValueError('El auxiliar no ofrece un estado de previsualización compatible')
                    result['runtime'] = runtime
                return result
            time.sleep(0.01)
        raise TimeoutError('El auxiliar no confirmó la retirada/activación de la prueba')


def event(phase, previous, current):
    if phase not in ('before', 'after'): raise ValueError('Fase de cambio desconocida')
    if phase == 'before' and (previous != 'plasma' or current == 'plasma'):
        return {'status': 'not-needed'}
    registration = active_registration()
    if registration is None: return {'status': 'inactive'}
    return command(registration, 'skin', current if current in ('plasma', 'retro', 'default') else 'default')


def status():
    """Request a new snapshot; a live PID or an old ack is not a health check."""
    registration = active_registration()
    if registration is None: return {'active': False}
    return {'active': True, **command(registration, 'status')}


def session_exit():
    """Stop this compositor's registered preview before its connection goes away."""
    instance = os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')
    if not instance:
        return {'status': 'no-compositor-instance'}
    registration = active_registration()
    if not registration or registration.get('compositorInstance') != instance:
        return {'status': 'inactive'}
    if registration.get('reportsExit') is not True:
        raise ValueError('La prueba registrada no confirma su guardado al salir')
    return command(registration, 'stop', timeout=2, exit_timeout=5)


def main(argv):
    if len(argv) == 4 and argv[0] == 'event': result = event(*argv[1:])
    elif len(argv) == 4 and argv[0] == 'register':
        register(argv[1], int(argv[2]), argv[3]);result = {'status': 'registered'}
    elif len(argv) == 2 and argv[0] == 'unregister':
        unregister(argv[1]);result = {'status': 'unregistered'}
    elif argv == ['stop']:
        registration = active_registration()
        result = command(registration, 'stop') if registration else {'status': 'inactive'}
    elif argv == ['status']: result = status()
    elif argv == ['session-exit']: result = session_exit()
    else: raise ValueError('Uso: panel-session.py event before|after ANTERIOR ACTUAL | status | stop | session-exit')
    print(json.dumps(result, ensure_ascii=False));return 0


if __name__ == '__main__':
    try: raise SystemExit(main(sys.argv[1:]))
    except (OSError, ValueError, TimeoutError) as exc:
        print(f'BWM R4: {exc}', file=sys.stderr);raise SystemExit(1)
