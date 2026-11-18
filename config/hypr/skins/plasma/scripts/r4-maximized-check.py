#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Own-window fixture controller for the opt-in R4 session runner."""
import json
import importlib.util
import math
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import tempfile
import time
import uuid


def refresh_area_observer():
    """Reload only the existing bridge and require its fresh baseline handshake."""
    minimum=time.time()
    subprocess.run([sys.executable,str(Path(__file__).with_name('kde-config-bridge.py')),'restart'],
                   capture_output=True,text=True,timeout=20,check=True)
    state=Path(os.environ.get('XDG_STATE_HOME',Path.home()/'.local/state'))/'bwm/plasma/area-observer.json'
    spec=importlib.util.spec_from_file_location('r4_area_metadata',Path(__file__).with_name('kwin_area.py'))
    area_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(area_module)
    deadline=time.monotonic()+8
    while time.monotonic()<deadline:
        try:
            info=state.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o077 or info.st_size>4096:
                raise ValueError('Metadatos del vigilante no privados')
            ready=json.loads(state.read_text())
            if not isinstance(ready,dict):raise ValueError('Metadatos del vigilante inválidos')
            pid=ready.get('pid');started=ready.get('startedAt')
            if ready.get('version')==1 and ready.get('ready') is True and type(pid) is int and pid>0 and type(started) in (int,float) and started>=minimum and ready.get('processStart') and area_module.process_start(pid)==ready['processStart']:
                return {'ready':True,'version':1,'startedAt':started}
        except FileNotFoundError:pass
        time.sleep(.1)
    raise TimeoutError('El puente reiniciado no confirmó el observador nuevo; revisar bridge.log')


def useful_area(monitor):
    x, y, width, height, scale = (monitor.get(key) for key in ('x', 'y', 'width', 'height', 'scale'))
    if any(type(value) not in (int, float) or not math.isfinite(value) for value in (x, y, width, height, scale)):
        raise ValueError('Geometría de monitor inválida')
    if min(width, height, scale) <= 0:
        raise ValueError('Tamaño o escala de monitor inválidos')
    transform = monitor.get('transform', 0)
    if type(transform) is not int or not 0 <= transform <= 7:
        raise ValueError('Transformación de monitor inválida')
    reserved = monitor.get('reserved')
    if not isinstance(reserved, list) or len(reserved) != 4 or any(
            type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in reserved):
        raise ValueError('Reserva de monitor inválida')

    # Hyprland 0.56 reports mode pixels and rounds the transformed size / scale.
    # The origin and reservations already use logical coordinates.
    if transform % 2:
        width, height = height, width
    width, height = width / scale, height / scale
    if not math.isfinite(width) or not math.isfinite(height):
        raise ValueError('Tamaño lógico inválido')
    left, top, right, bottom = reserved
    area = [x + left, y + top, math.floor(width + 0.5) - left - right, math.floor(height + 0.5) - top - bottom]
    if not all(math.isfinite(value) for value in area) or min(area[2:]) <= 0:
        raise ValueError('Área útil inválida')
    return area


def frame_matches(state, expected):
    frame = state.get('frame')
    return state.get('mode') == 3 and isinstance(frame, list) and len(frame) == 4 and all(
        type(n) in (int, float) and math.isfinite(n) and abs(n - target) <= 1 for n, target in zip(frame, expected))


def select_client(clients, pid, app_id):
    if not isinstance(clients, list): raise ValueError('Lista de clientes inválida')
    own = [c for c in clients if isinstance(c, dict) and c.get('pid') == pid and c.get('class') == app_id and c.get('mapped') is True]
    if len(own) != 1: raise ValueError('La ventana de prueba aún no es única/visible')
    address = own[0].get('address', '')
    if not isinstance(address, str) or not address.startswith('0x') or any(c not in '0123456789abcdefABCDEF' for c in address[2:]) or len(address) <= 2:
        raise ValueError('Dirección de la ventana de prueba inválida')
    return {'address': address, 'pid': pid} # Never serialize other client details/titles.


class Fixture:
    def __init__(self, binary, output, selector=None):
        self.binary, self.output = binary, output
        # Monitor selector for kwin-window to-screen. Physical outputs are always
        # addressed by description; only the temporary headless geometry check
        # passes the connector name of the output it created itself.
        self.selector = selector or 'desc:' + output
        self.app_id = 'org.bwm.r4.maximize.' + uuid.uuid4().hex
        self.child = None
        self.directory = None
        self.manager = Path(__file__).with_name('kwin-window.py')

    def run(self, argv):
        reply = subprocess.run(argv, capture_output=True, text=True, timeout=4)
        if reply.returncode:
            operation = 'hyprctl ' + ' '.join(argv[1:3]) if argv[0] == 'hyprctl' else 'kwin-window ' + next((a for a in argv if a in ('to-screen','maximize','state')), 'operación')
            detail = (reply.stderr or reply.stdout).strip()[-500:] or 'el gestor rechazó la operación sin mensaje'
            raise ValueError(f'Falló {operation} (código {reply.returncode}): {detail}')
        return reply.stdout

    def client(self):
        if self.child is None or self.child.poll() is not None: raise ValueError('La ventana de prueba terminó')
        return select_client(json.loads(self.run(['hyprctl', '-j', 'clients'])), self.child.pid, self.app_id)

    def command(self, action, *args):
        client = self.client() # Recheck PID/class/mapped before every mutation.
        return self.run([sys.executable, str(self.manager), '--pid', str(client['pid']), action, *args, client['address']])

    def start(self):
        self.directory = tempfile.TemporaryDirectory(prefix='bwm-r4-maximize-')
        root = Path(self.directory.name)
        env = dict(os.environ, QT_QPA_PLATFORM='wayland', DBUS_SESSION_BUS_ADDRESS='unix:path=' + str(root / 'no-bus'),
                   QT_WAYLAND_DISABLE_WINDOWDECORATION='1')
        if env.get('WAYLAND_DISPLAY') and not env['WAYLAND_DISPLAY'].startswith('/'):
            env['WAYLAND_DISPLAY'] = str(Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')) / env['WAYLAND_DISPLAY'])
        for key, name in [('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache'),('XDG_RUNTIME_DIR','runtime')]:
            path = root / name;path.mkdir(mode=0o700);env[key] = str(path)
        env['XDG_CONFIG_DIRS'] = str(root / 'defaults')
        self.child = subprocess.Popen([str(self.binary), '--maximize-fixture', self.app_id], env=env,
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        deadline = time.monotonic() + 5
        while True:
            try: self.client();break
            except ValueError:
                if time.monotonic() >= deadline or self.child.poll() is not None: raise
                time.sleep(.1)
        # The real CLI signature is: to-screen MONITOR [ADDRESS].
        self.command('to-screen', self.selector)

    def measure(self, monitor, remaximize=True):
        expected = useful_area(monitor)
        if remaximize:
            self.command('maximize', '--mode', 'restore')
            self.command('maximize', '--mode', 'full')
        deadline = time.monotonic() + 4
        while True:
            state = json.loads(self.command('state'))
            if not isinstance(state, dict): raise ValueError('Estado de maximizado inválido')
            authority = False
            try:
                own = self.client()
                decorations = json.loads(self.run(['hyprctl', '-j', 'breezebars-csd']))
                records = [r for r in decorations.get('windows', []) if r.get('pid') == own['pid'] and r.get('address') == own['address']]
                authority = decorations.get('version') == 1 and decorations.get('api') == 'breezebars-csd' and len(records) == 1 and type(records[0].get('visible')) is bool
                if authority:
                    raw = records[0].get('borders', {}) if records[0]['visible'] else dict.fromkeys(('left','top','right','bottom'),0)
                    valid = all(type(raw.get(k)) in (int,float) and math.isfinite(raw[k]) and raw[k]>=0 for k in ('left','top','right','bottom'))
                    authority = valid and state.get('borders') == {k:math.ceil(raw[k]) for k in ('left','top','right','bottom')}
            except (ValueError, OSError, TypeError, AttributeError, subprocess.SubprocessError): authority=False
            result = {'expected': expected, 'observedFrame': state.get('frame'), 'mode': state.get('mode'),
                      'borders': state.get('borders'), 'decorationRecordAvailable': authority,
                      'matches': authority and frame_matches(state, expected)}
            if not result['matches']:
                result['reason'] = 'Marco distinto del área útil' if authority else 'No se confirmó un registro de decoración propio y coherente'
            if result['matches'] or time.monotonic() >= deadline: return result
            time.sleep(.1)

    def close(self):
        try:
            if self.child is not None and self.child.poll() is None:
                try:
                    own = self.client()
                    self.command('maximize', '--mode', 'restore')
                    # Maximize also stores this fixture's presnap size. Remove
                    # only that entry through the existing API while PID is alive.
                    self.client()
                    path = Path(__file__).resolve().parents[3] / 'scripts/quick-tile.py'
                    spec = importlib.util.spec_from_file_location('r4_quick_tile', path)
                    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                    module.remove_presnap(own['address'])
                except (ValueError, OSError, subprocess.SubprocessError): pass
        finally:
            if self.child is not None and self.child.poll() is None:
                self.child.terminate()
                try: self.child.wait(timeout=3)
                except subprocess.TimeoutExpired: self.child.kill();self.child.wait(timeout=2)
            if self.directory is not None: self.directory.cleanup()
