#!/usr/bin/env python3
"""Local R1 smoke test. Run in the graphical session; never exits/restarts a compositor.

Without --run only checks read-only access. Report contains fixture identities, not user titles.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

import bwm_windows as windows


def command(*args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=45)
    if result.returncode:
        raise RuntimeError(f'{args[0]}: {result.stderr.strip() or result.stdout.strip()}')
    return result.stdout.strip()


def query(name):
    return json.loads(command('hyprctl', '-j', name))


def dispatch(body):
    result = command('hyprctl', 'dispatch', body)
    if result != 'ok':
        raise RuntimeError('Dispatcher rejected the test action: ' + result)


def wait_for(predicate, label):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        result = predicate()
        if result:
            return result
        time.sleep(.1)
    raise RuntimeError('Timeout: ' + label)


def stable_identity(client):
    generation = (client['_bwm_process_generation'] if '_bwm_process_generation' in client
                  else windows.process_generation(client.get('pid')))
    return (client.get('address'), client.get('pid'), generation)


def assert_preserved(original, current):
    """Only compare identity/workspace; tiling geometry legitimately changes between skins."""
    now = {stable_identity(c): c for c in current}
    for before in original:
        after = now.get(stable_identity(before))
        if after is None:
            raise RuntimeError('A pre-existing window disappeared; matrix stopped')
        if after.get('workspace', {}).get('name') != before.get('workspace', {}).get('name'):
            raise RuntimeError('A pre-existing window changed workspace; matrix stopped')


def matrix(args, report, target, original_clients, original_skin, snapshot):
    """Real compositor checks only. No physical key, mouse or rendering assertions."""
    manager = str(Path(__file__).with_name('bwm-theme-manager.py'))
    focus = str(Path(__file__).with_name('bwm-focus.py'))
    address, pid = target['address'], target['pid']

    def live():
        return next((c for c in query('clients') if c.get('address') == address and c.get('pid') == pid), None)

    def ensure_fixture():
        current = live()
        if not current or current.get('workspace', {}).get('name') != 'special:magic':
            raise RuntimeError('Matrix fixture lost its identity or special origin')

    def is_open():
        return any(m.get('specialWorkspace', {}).get('name') == 'special:magic' for m in query('monitors'))

    def close_magic():
        if is_open():
            dispatch('hl.dsp.workspace.toggle_special("magic")')
            wait_for(lambda: not is_open(), 'hide Magic before transition')

    def switch(skin):
        print('Comprobando skin:', skin, flush=True)
        command(sys.executable, manager, 'set', skin)
        errors = command('hyprctl', 'configerrors')
        if errors and errors != 'ok':
            raise RuntimeError('Hyprland configuration errors after skin transition')
        ensure_fixture()
        assert_preserved(original_clients, query('clients'))

    def monitor_ready(selector):
        focused = next((m for m in query('monitors') if m.get('focused')), None)
        return focused if focused and 'desc:' + focused.get('description', '') == selector else None

    def diagnose(selector, stage):
        # No client titles or other user window contents in the report.
        report['matrix_diagnostic'] = {'requested_monitor': selector, 'stage': stage,
            'monitors': [{k: m.get(k) for k in ('id', 'description', 'focused', 'specialWorkspace')}
                         for m in query('monitors')],
            'fixture_monitor': (live() or {}).get('monitor')}

    report['matrix'] = []
    report['matrix_scope'] = 'activation per connected monitor and skin changes with Magic open/closed'
    # No hard-coded connector: use stable descriptions, or fail without moving workspaces.
    selectors = ['desc:' + m['description'] for m in query('monitors') if m.get('description')]
    if len(selectors) != len(query('monitors')) or len(set(selectors)) != len(selectors):
        raise RuntimeError('Monitor descriptions missing or ambiguous')
    for skin in ('default', 'plasma', 'retro'):
        close_magic()
        switch(skin)
        if is_open():
            raise RuntimeError('Skin transition unexpectedly opened Magic')
        for selector in selectors:
            print('Comprobando monitor:', selector, flush=True)
            try:
                monitor = next(m for m in query('monitors') if 'desc:' + m.get('description', '') == selector)
                x, y, width, height = windows.monitor_box(monitor)
                if width <= 0 or height <= 0:
                    raise RuntimeError('Invalid logical monitor geometry')
                # Selecting a monitor need not warp the pointer. Emulate choosing that
                # monitor physically, so follow_mouse/activation cannot bounce to the old one.
                dispatch(f'hl.dsp.cursor.move({{x={int(x + width/2)},y={int(y + height/2)}}})')
                dispatch('hl.dsp.focus({monitor=' + json.dumps(selector, ensure_ascii=False) + '})')
                wait_for(lambda: monitor_ready(selector), 'select matrix monitor')
                command(sys.executable, focus, address, '--pid', str(pid))
                wait_for(is_open, 'Magic visible on matrix monitor')
                focused = wait_for(lambda: monitor_ready(selector), 'activation remains on requested monitor')
            except Exception:
                diagnose(selector, 'monitor selection or first activation')
                raise
            if focused.get('specialWorkspace', {}).get('name') != 'special:magic':
                raise RuntimeError('Magic is not on the requested monitor')
            command(sys.executable, focus, address, '--pid', str(pid))
            wait_for(lambda: query('activewindow').get('address') == address, 'repeat focus on matrix monitor')
            ensure_fixture()
            report['matrix'].append({'skin': skin, 'monitor': selector, 'activation': 'passed'})
            close_magic()
        if args.interactive:
            windows.restore_focus(snapshot)
            manual_review(report)
            close_magic()
            ensure_fixture()
            assert_preserved(original_clients, query('clients'))
        # Also exercise transitions with the special workspace already visible.
        command(sys.executable, focus, address, '--pid', str(pid))
        wait_for(is_open, 'Magic visible before transition')
        switch('plasma' if skin != 'plasma' else 'retro')
        if not is_open():
            raise RuntimeError('Skin transition closed visible Magic')
        report['checks'].append('skin transition with Magic visible from ' + skin)
    close_magic()
    switch(original_skin)
    report['checks'].append('original skin restored after matrix')


def manual_review(report):
    """Explicit user observations; never inferred from IPC or an automatic screenshot."""
    skin = windows.current_skin()
    print('\nComprobación manual de', skin, ': quedan las dos ventanas «BWM R1 test».')
    print('Usa sólo esas ventanas. Puedes responder s (sí), n (falló), o Enter (pendiente).')
    prompts = {
        'physical_alt_s': 'Prueba Alt+S físico en cada monitor: ¿abre/cierra Magic delante, sin ventanas detrás?',
        'physical_alt_tab': 'Sólo en Breeze con miniaturas desactivadas: Alt+Tab con Magic visible y oculto, ¿lista/foco correctos?',
        'panel_dock_click': 'En cada monitor, activa/restaura el fixture con clic real en panel/dock: ¿conserva Magic? Enter si no hay dock disponible.',
        'fullscreen_desktop': 'Prueba fullscreen del fixture y Mostrar escritorio (minimiza temporalmente las apps abiertas), y restaura: ¿correcto?',
        'visual_depth_order': 'Con ventanas superpuestas: ¿Magic queda encima y sólo recibe entrada cuando está visible?',
    }
    report['manual'] = {}
    for key, prompt in prompts.items():
        if key == 'physical_alt_tab' and windows.current_skin() != 'plasma':
            report['manual'][key] = 'pending'
            print('Alt+Tab físico pendiente: se limita a Breeze mientras el crash de capturas no esté resuelto.')
            continue
        answer = input(prompt + ' [s/n/Enter] ').strip().lower()
        report['manual'][key] = 'user-confirmed' if answer == 's' else 'failed' if answer == 'n' else 'pending'
        if windows.current_skin() != skin:
            report['manual'][key] = 'pending'
            print('La skin cambió durante la observación; resultado pendiente.')
    report['visual_verification_method'] = 'user observations; no automatic rendering comparison'
    report.setdefault('manual_by_skin', {})[skin] = report['manual'].copy()
    report['current_skin_observations_verified'] = all(v == 'user-confirmed' for v in report['manual'].values())
    report['visual_verified'] = (set(report['manual_by_skin']) == {'default', 'plasma', 'retro'}
        and all(value == 'user-confirmed' for observations in report['manual_by_skin'].values()
                for value in observations.values()))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', help='Create disposable windows and exercise Magic')
    parser.add_argument('--matrix', action='store_true', help='Cycle three skins on each monitor; restores original skin')
    parser.add_argument('--interactive', action='store_true', help='Collect explicit keyboard/mouse/visual observations')
    parser.add_argument('--report', type=Path, default=Path('/tmp/bwm-r1-session-results.json'))
    args = parser.parse_args(argv)
    if (args.matrix or args.interactive) and not args.run:
        parser.error('--matrix and --interactive require --run')
    report = {'checks': [], 'visual_verified': False, 'compositor_restarted': False}
    children = []
    fixtures = []
    rule = None
    snapshot = None
    changed_special = False
    original_skin = None
    matrix_started = False
    cursor_snapshot = None
    try:
        version = query('version')
        clients = query('clients')
        monitors = query('monitors')
        if not isinstance(clients, list) or not isinstance(monitors, list):
            raise RuntimeError('Invalid compositor data; no test actions performed')
        for client in clients:
            client['_bwm_process_generation'] = windows.process_generation(client.get('pid'))
        report['version'] = version.get('version', version.get('tag', 'unknown'))
        report['checks'].append('IPC accessible')
        if not args.run:
            report['status'] = 'read-only preflight passed'
            return 0
        if not shutil.which('kitty'):
            raise RuntimeError('kitty is required for the disposable fixtures')
        # Never borrow, hide, move or minimize an existing scratchpad window.
        if any(c.get('workspace', {}).get('name') == 'special:magic' for c in clients):
            raise RuntimeError('Magic contains user windows: test refused without moving them')
        if any(m.get('specialWorkspace', {}).get('id', 0) < 0 for m in monitors):
            raise RuntimeError('A special workspace is visible: close it before running this test')
        if args.matrix:
            original_skin = windows.current_skin()
            if original_skin not in ('default', 'retro', 'plasma'):
                raise RuntimeError('Unknown original skin; matrix refused')
            if 'breezebars' not in command('hyprctl', 'plugin', 'list').lower():
                raise RuntimeError('Breeze plugin not loaded; matrix cannot validate Breeze. No hot loading attempted.')
            cursor_snapshot = query('cursorpos')
            if not isinstance(cursor_snapshot, dict) or not all(isinstance(cursor_snapshot.get(k), (int, float)) for k in ('x', 'y')):
                raise RuntimeError('Cannot save cursor position; matrix refused')
        used = {c.get('workspace', {}).get('id') for c in clients}
        used.update(w.get('id') for w in query('workspaces'))
        workspace = next((n for n in range(81, 99) if n not in used), None)
        if workspace is None:
            raise RuntimeError('No unused test workspace available')
        snapshot = windows.snapshot_focus(media=False)
        token = uuid.uuid4().hex[:10]
        app_class = 'org.bwm.r1-test-' + token
        rule = 'tmp-bwm-r1-' + token
        windows.hold_new_windows(rule, [app_class], workspace)
        for index in range(2):
            children.append(subprocess.Popen(['kitty', '--class', app_class,
                '--title', f'BWM R1 test {index}', 'sleep', '1800'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        def fixture_clients():
            values = [c for c in query('clients') if c.get('class') == app_class]
            # Save each fixture identity immediately so partial startup is cleaned too.
            for c in values:
                ident = (c['address'], c['pid'])
                if ident not in fixtures:
                    fixtures.append(ident)
            return values if len(values) == 2 else None
        values = wait_for(fixture_clients, 'two disposable windows')
        if any(c.get('workspace', {}).get('id') != workspace for c in values):
            raise RuntimeError('Fixture placement rule not applied; test stopped')
        target = values[0]
        address, pid = target['address'], target['pid']
        def live():
            return next((c for c in query('clients') if c.get('address') == address and c.get('pid') == pid), None)
        def window_action(body):
            dispatch(f'(function() local w=hl.get_window({json.dumps("address:" + address)}); '
                f'if not w or w.pid~={pid} then return hl.dsp.no_op() end {body} return hl.dsp.no_op() end)()')
        window_action('hl.dispatch(hl.dsp.window.move({workspace="special:magic",follow=false,window=w}))')
        wait_for(lambda: (live() or {}).get('workspace', {}).get('name') == 'special:magic', 'send to Magic')
        report['checks'].append('test window moved into canonical Magic')
        def magic_open():
            return any(m.get('specialWorkspace', {}).get('name') == 'special:magic' for m in query('monitors'))
        dispatch('hl.dsp.workspace.toggle_special("magic")')
        changed_special = True
        wait_for(magic_open, 'show Magic')
        dispatch('hl.dsp.workspace.toggle_special("magic")')
        wait_for(lambda: not magic_open(), 'hide Magic')
        changed_special = False
        report['checks'].append('Alt+S dispatcher shows and hides Magic')
        focus = str(Path(__file__).with_name('bwm-focus.py'))
        for _ in range(2):
            command(sys.executable, focus, address, '--pid', str(pid))
            changed_special = True
            wait_for(magic_open, 'idempotent activation reveals Magic')
            wait_for(lambda: query('activewindow').get('address') == address, 'focus fixture')
            if (live() or {}).get('workspace', {}).get('name') != 'special:magic':
                raise RuntimeError('Activation extracted the fixture from Magic')
        report['checks'].append('repeated common activation keeps Magic open and focuses fixture')
        spec = importlib.util.spec_from_file_location('session_minimizer', Path(__file__).with_name('toggle-minimize.py'))
        minimizer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(minimizer)
        minimizer.minimize_win(live())
        wait_for(lambda: (live() or {}).get('workspace', {}).get('name') == 'special:minimized', 'minimize fixture')
        command(sys.executable, focus, address, '--pid', str(pid), '--restore-on-current')
        wait_for(lambda: (live() or {}).get('workspace', {}).get('name') == 'special:magic', 'dock-policy restore to Magic')
        report['checks'].append('minimize and common dock-policy restore preserve special origin')
        before = live().get('workspace')
        stale = subprocess.run([sys.executable, focus, address, '--pid', str(pid + 1000000)], capture_output=True, text=True, timeout=12)
        if stale.returncode == 0 or live().get('workspace') != before:
            raise RuntimeError('Stale PID was not safely rejected')
        report['checks'].append('stale PID rejected without moving fixture')
        if args.matrix:
            matrix_started = True
            matrix(args, report, target, clients, original_skin, snapshot)
        if args.interactive and not args.matrix:
            # Restore terminal access before asking for actual observations.
            if magic_open():
                dispatch('hl.dsp.workspace.toggle_special("magic")')
            windows.restore_focus(snapshot)
            manual_review(report)
        report['status'] = 'automated smoke passed; visual and complete matrix still pending'
        if args.matrix:
            report['status'] = 'automated matrix passed; physical observations recorded separately'
        if any(value == 'failed' for observations in report.get('manual_by_skin', {}).values()
               for value in observations.values()):
            report['status'] = 'manual check failed; inspect report'
            return 1
        return 0
    except KeyboardInterrupt:
        report['status'] = 'aborted'
        return 130
    except Exception as error:
        report['status'] = 'failed or blocked'
        report['error'] = str(error)
        return 1
    finally:
        cleanup_errors = []
        if matrix_started:
            try:
                if windows.current_skin() != original_skin:
                    command(sys.executable, str(Path(__file__).with_name('bwm-theme-manager.py')), 'set', original_skin)
            except Exception as error:
                cleanup_errors.append('Original skin restoration: ' + str(error))
        for address, pid in fixtures:
            try:
                dispatch(f'(function() local w=hl.get_window({json.dumps("address:" + address)}); '
                    f'if w and w.pid=={pid} then hl.dispatch(hl.dsp.window.close({{window=w}})) end return hl.dsp.no_op() end)()')
            except Exception as error:
                cleanup_errors.append(str(error))
        for child in children:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(3)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
        if changed_special:
            try:
                if any(m.get('specialWorkspace', {}).get('name') == 'special:magic' for m in query('monitors')):
                    dispatch('hl.dsp.workspace.toggle_special("magic")')
            except Exception as error:
                cleanup_errors.append(str(error))
        if rule:
            try:
                windows.release_new_windows(rule)
            except Exception as error:
                cleanup_errors.append(str(error))
        if snapshot:
            try:
                windows.restore_focus(snapshot)
            except Exception as error:
                cleanup_errors.append(str(error))
        if cursor_snapshot is not None:
            try:
                dispatch(f'hl.dsp.cursor.move({{x={int(cursor_snapshot["x"])},y={int(cursor_snapshot["y"])}}})')
            except Exception as error:
                cleanup_errors.append('Cursor restoration: ' + str(error))
        report['cleanup_errors'] = cleanup_errors
        if cleanup_errors:
            report['status'] = 'cleanup incomplete; inspect report'
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(report, ensure_ascii=False, indent=2))
        print('Report:', args.report)
        if report.get('error'):
            print('R1 detenido: ' + report['error'] + '; informe: ' + str(args.report), file=sys.stderr, flush=True)
        if cleanup_errors:
            raise RuntimeError('Fixture cleanup incomplete; see ' + str(args.report))


if __name__ == '__main__':
    raise SystemExit(main())
