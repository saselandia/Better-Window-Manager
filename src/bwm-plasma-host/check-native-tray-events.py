#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Run native tray model and action tests on a private D-Bus without service activation."""
import argparse
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
BINARY = ROOT / 'build/bwm-plasma-host/test-plasma-tray-events'
PROXY = BINARY.parent / 'tray-proxy/xdg-dbus-proxy'


def wayland_display(environment):
    display = environment.get('WAYLAND_DISPLAY')
    if not display:
        raise ValueError('Ejecuta --menu-wayland desde una sesión Wayland.')
    socket = Path(display)
    if not socket.is_absolute():
        socket = Path(environment.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')) / socket
    socket = socket.resolve(strict=True)
    info = socket.stat()
    if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid():
        raise ValueError('El socket Wayland debe pertenecer al usuario de la sesión.')
    return str(socket)


def focused_output(run=subprocess.run):
    try:
        reply = run(['hyprctl', '-j', 'monitors'], capture_output=True, text=True, timeout=3, check=True)
        monitors = json.loads(reply.stdout)
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        raise ValueError('No se pudo consultar el monitor enfocado de Hyprland. Indica su descripción con --output.') from error
    if not isinstance(monitors, list) or not all(isinstance(monitor, dict) for monitor in monitors):
        raise ValueError('Hyprland devolvió una lista de monitores inválida.')
    focused = [monitor.get('description') for monitor in monitors if monitor.get('focused') is True]
    if len(focused) != 1 or not isinstance(focused[0], str) or not focused[0].strip():
        raise ValueError('No se pudo identificar un monitor enfocado. Indica su descripción con --output.')
    return focused[0].strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--filtered', action='store_true', help='Use the local exact-object proxy for the KDE client')
    modes.add_argument('--actions', action='store_true', help='Send native tray actions to the isolated fixture item')
    modes.add_argument('--menu', action='store_true', help='Import a menu exported by KDE and invoke an item')
    modes.add_argument('--menu-wayland', action='store_true', help='Verify the menu on a temporary layer with real pointer input')
    parser.add_argument('--output', help='Monitor description for --menu-wayland, defaults to the focused Hyprland monitor')
    args = parser.parse_args()
    if args.output is not None and (not args.menu_wayland or not args.output.strip()):
        parser.error('--output requiere --menu-wayland y una descripción de monitor.')
    if args.menu_wayland:
        try:
            display = wayland_display(os.environ)
            output = args.output.strip() if args.output is not None else focused_output()
        except (OSError, ValueError) as error:
            parser.error(str(error))
    with tempfile.TemporaryDirectory(prefix='bwm-r4-tray-events-', dir='/tmp') as directory:
        root = Path(directory)
        env = {key: value for key, value in os.environ.items()
               if not key.startswith(('DBUS_', 'BWM_R4_', 'QT_')) and key not in
               ('DISPLAY', 'WAYLAND_DISPLAY', 'WAYLAND_SOCKET', 'HYPRLAND_INSTANCE_SIGNATURE', 'KSNI_NO_DBUSMENU',
                'XDG_ACTIVATION_TOKEN', 'DESKTOP_STARTUP_ID')}
        for variable, name in {'XDG_CONFIG_HOME': 'config', 'XDG_CACHE_HOME': 'cache', 'XDG_DATA_HOME': 'data',
                               'XDG_RUNTIME_DIR': 'runtime', 'XDG_CONFIG_DIRS': 'defaults', 'XDG_STATE_HOME': 'state'}.items():
            path = root / name
            path.mkdir(mode=0o700)
            env[variable] = str(path)
        env.update(QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software', XDG_DATA_DIRS='/usr/local/share:/usr/share',
                   DBUS_SYSTEM_BUS_ADDRESS=f'unix:path={root}/no-system-bus')
        if args.filtered:
            env['BWM_R4_TRAY_TEST_PROXY'] = str(PROXY)
        if args.actions:
            env['BWM_R4_TRAY_TEST_ACTIONS'] = '1'
        if args.menu_wayland:
            env.update(QT_QPA_PLATFORM='wayland', WAYLAND_DISPLAY=display, BWM_R4_TRAY_TEST_MENU_WAYLAND='1',
                       BWM_R4_TRAY_TEST_OUTPUT=output)
        bus = root / 'runtime/tray-events-bus'
        config = root / 'bus.conf'
        config.write_text(f'''<busconfig>
  <type>session</type>
  <listen>unix:path={bus}</listen>
  <auth>EXTERNAL</auth>
  <policy context="default">
    <allow send_destination="*"/>
    <allow receive_sender="*"/>
    <allow own="*"/>
  </policy>
</busconfig>
''', encoding='utf-8')
        cases = ['pixmapWireSignature']
        if not args.menu_wayland:
            cases.append('offscreenActivationFallback')
        cases.append('originalTrayImportsMenu' if args.menu or args.menu_wayland else 'originalTrayTracksItemLifecycle')
        command = ['dbus-run-session', f'--config-file={config}', '--', BINARY, *cases]
        with subprocess.Popen(command, env=env, start_new_session=True) as test:
            try:
                return test.wait(timeout=65 if args.menu_wayland else 40)
            except subprocess.TimeoutExpired:
                print('El ensayo de bandeja agotó el plazo.', file=sys.stderr)
                return 2
            except KeyboardInterrupt:
                return 130
            finally:
                if test.poll() is None:
                    try:
                        os.killpg(test.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass


if __name__ == '__main__':
    raise SystemExit(main())
