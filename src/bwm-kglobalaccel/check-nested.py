#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""bwm-kglobalaccel against a real, disposable Hyprland (nested on a temporary headless output).

The CTest (check-daemon.py) uses a fake hyprctl; this one runs the generated Lua in Hyprland
itself: binds created, a key BWM starts using (only disabled), keys withdrawn (press and
release binds of one key go together), a config reload (modules/kde_shortcuts.lua rebuilds the
binds) and the daemon stopping. Hyprland must survive every step (a crash here once took down
the daily session). Never touches the parent session's binds; private D-Bus for the daemon.

  python3 check-nested.py --binary BUILD/bwm-kglobalaccel --client BUILD/test-client
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time

REPO = Path(__file__).resolve().parents[2]


def hypr(*args, instance=None):
    command = ['hyprctl'] + (['-i', instance] if instance else []) + list(args)
    return subprocess.run(command, capture_output=True, text=True, timeout=5).stdout


def wait(predicate, message, timeout=10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            value = predicate()
        except (ValueError, subprocess.SubprocessError):
            value = None
        if value:
            return value
        time.sleep(0.1)
    raise RuntimeError(message)


def inner(args) -> int:
    """Runs inside dbus-run-session with HYPRLAND_INSTANCE_SIGNATURE = nested compositor."""
    signature = os.environ['HYPRLAND_INSTANCE_SIGNATURE']
    nested_pid = int(os.environ['BWM_NESTED_PID'])
    root = Path(os.environ['BWM_NESTED_ROOT'])
    env = dict(os.environ)
    state = root / 'state' / 'bwm' / 'kde-shortcuts.lua'

    def alive():
        out = hypr('-j', 'version', instance=signature)
        if '"tag"' not in out or not Path(f'/proc/{nested_pid}').exists():
            raise AssertionError('nested Hyprland died')

    def ours():
        return [b for b in json.loads(hypr('-j', 'binds', instance=signature)) if b['description'].startswith('KDE: ')]

    def status():
        r = subprocess.run([args.binary, '--status'], env=env, capture_output=True, text=True, timeout=5)
        return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None

    steps = []

    def expect(c, wanted, skip=('changed taken=',)):
        # The client also reports BWM taking Alt+F1 from it ("changed taken="), at any time.
        while True:
            line = c.stdout.readline().strip()
            if line not in skip or line == wanted:
                assert line == wanted, f'expected {wanted!r}, got {line!r}'
                return
    daemon = subprocess.Popen([args.binary], env=env, stderr=subprocess.PIPE, text=True)
    clients = []
    try:
        wait(status, 'daemon did not start')
        def client():
            c = subprocess.Popen([args.client], env={**env, 'QT_QPA_PLATFORM': 'offscreen'}, stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, text=True, bufsize=1)
            clients.append(c)
            line = c.stdout.readline()
            while line.strip() == 'changed taken=':
                line = c.stdout.readline()
            assert line.startswith('assigned free=Meta+Shift+K'), f'client: {line!r}'
            return c
        first = client()
        wait(lambda: any(b['key'].lower() == 'k' and b['modmask'] == 65 for b in ours()), 'KDE bind not created')
        alive()
        mine = [b for b in ours() if b['key'].lower() == 'k']
        assert len(mine) == 2 and {b['release'] for b in mine} == {True, False}, mine
        assert not any(b['key'] == 'F1' for b in ours()), 'BWM key must not get a KDE bind'
        code = re.search(r'add\("SUPER \+ SHIFT \+ k", (\d+)', state.read_text()).group(1)
        # Run the command of the bind exactly as Hyprland would.
        cmd = f'{args.binary} --trigger press {code}'
        hypr('dispatch', f'hl.dsp.exec_cmd("{cmd}")', instance=signature)
        expect(first, 'triggered free')
        steps.append('binds created and triggered through Hyprland exec')

        # Reload: modules/kde_shortcuts.lua rebuilds the binds from the state file.
        hypr('reload', instance=signature)
        wait(lambda: len([b for b in ours() if b['key'].lower() == 'k']) == 2, 'binds lost after reload')
        alive()
        steps.append('binds rebuilt by the module after reload')

        # The client leaves: both binds of the key go (press + release, the crashing case).
        first.stdin.close()
        first.wait(timeout=5)
        wait(lambda: not any(b['key'].lower() == 'k' for b in ours()), 'binds not withdrawn')
        time.sleep(0.5)
        alive()
        steps.append('press and release binds withdrawn without crashing Hyprland')

        # Again, then BWM starts using that key: ours are only disabled, BWM's stays.
        second = client()
        wait(lambda: any(b['key'].lower() == 'k' for b in ours()), 'KDE bind not recreated')
        hypr('eval', 'hl.bind("SUPER + SHIFT + K", hl.dsp.exec_cmd("true"), { description = "BWM test bind" })',
             instance=signature)
        subprocess.run([args.binary, '--sync'], env=env, capture_output=True, timeout=5)
        expect(second, 'changed free=')
        time.sleep(1.0)
        alive()
        binds = json.loads(hypr('-j', 'binds', instance=signature))
        assert any(b['description'] == 'BWM test bind' for b in binds), 'BWM bind was removed'
        steps.append('key taken by BWM: KDE binds disabled, BWM bind kept')

        daemon.send_signal(signal.SIGTERM)
        assert daemon.wait(timeout=10) == 0
        alive()
        assert not state.exists()
        steps.append('daemon stop removes its binds and state')
        print(json.dumps({'passed': True, 'steps': steps}, indent=2))
        return 0
    except (AssertionError, RuntimeError, AttributeError, subprocess.SubprocessError) as error:
        import traceback
        print(json.dumps({'passed': False, 'steps': steps, 'error': str(error),
                          'where': traceback.format_exc().splitlines()[-3:]}, indent=2))
        return 1
    finally:
        for c in clients:
            if c.poll() is None:
                c.kill()
        if daemon.poll() is None:
            daemon.kill()


def outer(args) -> int:
    if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):
        print('A Hyprland parent session is required', file=sys.stderr)
        return 2
    output = f'BWM-KGA-{os.getpid()}'
    rule = f'bwm-kga-{os.getpid()}'
    created = rule_added = False
    nested = None
    result = 1
    with tempfile.TemporaryDirectory(prefix='bwm-kga-nested-') as temporary:
        root = Path(temporary)
        try:
            hypr('output', 'create', 'headless', output)
            created = True
            hypr('eval', f'hl.monitor({{output="{output}",mode="1280x800@60",position="20000x20000",scale=1}})')
            monitor = wait(lambda: next((m for m in json.loads(hypr('-j', 'monitors')) if m['name'] == output), None),
                           'temporary output did not appear')
            hypr('eval', f'hl.window_rule({{name="{rule}",match={{class="^aquamarine$"}},'
                         f'workspace="{monitor["activeWorkspace"]["id"]} silent",no_initial_focus=true}})')
            rule_added = True
            (root / 'modules').mkdir()
            (root / 'modules' / 'theme.lua').write_text('return { name = "plasma" }\n')
            config = root / 'hyprland.lua'
            config.write_text(
                f'package.path = "{root}/?.lua;{REPO}/config/hypr/?.lua;" .. package.path\n'
                'hl.monitor({output="",mode="1280x800",position="0x0",scale=1})\n'
                'hl.config({misc={disable_hyprland_logo=true,disable_splash_rendering=true},'
                'animations={enabled=false},xwayland={enabled=false}})\n'
                'hl.bind("ALT + F1", hl.dsp.exec_cmd("true"), { description = "BWM test kickoff" })\n'
                'pcall(require, "modules.kde_shortcuts")\n')
            env = {k: v for k, v in os.environ.items() if not k.startswith(('QT_', 'DBUS_', 'BWM_'))
                   and k not in ('HYPRLAND_INSTANCE_SIGNATURE', 'WAYLAND_SOCKET', 'DISPLAY', 'XDG_ACTIVATION_TOKEN')}
            for variable, name in [('XDG_CONFIG_HOME', 'config'), ('XDG_DATA_HOME', 'data'),
                                   ('XDG_CACHE_HOME', 'cache'), ('XDG_STATE_HOME', 'state')]:
                (root / name).mkdir(mode=0o700)
                env[variable] = str(root / name)
            # Our binds run the trigger from Hyprland's environment: point it at this daemon.
            env['BWM_KGLOBALACCEL_SOCKET'] = str(root / 'kga.sock')
            with (root / 'hypr.log').open('w') as log:
                nested = subprocess.Popen(['Hyprland', '--config', str(config)], env=env, stdout=log,
                                          stderr=subprocess.STDOUT, start_new_session=True)
            instance = wait(lambda: next((i for i in json.loads(hypr('instances', '-j')) if i['pid'] == nested.pid), None),
                            'nested compositor did not start')
            env.update(HYPRLAND_INSTANCE_SIGNATURE=instance['instance'], BWM_NESTED_PID=str(nested.pid),
                       BWM_NESTED_ROOT=str(root), BWM_KGLOBALACCEL_NO_NOTIFY='1', QT_QPA_PLATFORM='offscreen',
                       BWM_KGLOBALACCEL_SOCKET=str(root / 'kga.sock'))
            result = subprocess.run(['dbus-run-session', '--', sys.executable, __file__, '--inner',
                                     '--binary', str(Path(args.binary).resolve()),
                                     '--client', str(Path(args.client).resolve())], env=env, timeout=90).returncode
            if nested.poll() is not None:
                print('nested Hyprland exited; log tail:\n' + (root / 'hypr.log').read_text(errors='replace')[-2000:])
                result = 1
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
            print(json.dumps({'passed': False, 'error': str(error)}))
            result = 1
        finally:
            if nested and nested.poll() is None:
                os.killpg(nested.pid, signal.SIGTERM)
                try:
                    nested.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(nested.pid, signal.SIGKILL)
            if rule_added:
                hypr('eval', f'hl.window_rule({{name="{rule}",match={{class="^bwm-kga-never$"}}}})')
            if created:
                hypr('output', 'remove', output)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', required=True)
    parser.add_argument('--client', required=True)
    parser.add_argument('--inner', action='store_true')
    args = parser.parse_args()
    return inner(args) if args.inner else outer(args)


if __name__ == '__main__':
    sys.exit(main())
