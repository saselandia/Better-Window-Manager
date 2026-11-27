#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""T7 inner client for check-focus-safety.py. Reviewed Store packages only.

Set BWM_STORE_WORK to a disposable store-compat.py work directory. This client
captures only its child compositor, renders KDE resources without copying QML,
and records each case independently. It never injects input or runs real power
actions. The explicit review ledger is mandatory before any external QML runs.
"""
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('store_compat', HERE / 'store-compat.py')
store = importlib.util.module_from_spec(spec); spec.loader.exec_module(store)


def main():
    assert os.environ.get('BWM_FOCUS_NESTED') == '1'
    instances = json.loads(subprocess.check_output(['hyprctl', 'instances', '-j'], text=True))
    assert any(i['pid'] == int(os.environ['BWM_FOCUS_COMPOSITOR_PID']) and
               i['instance'] == os.environ['HYPRLAND_INSTANCE_SIGNATURE'] for i in instances)
    work = store.private_root(Path(os.environ['BWM_STORE_WORK']))
    review = json.loads((work / 'review.json').read_text())
    binary = ROOT / 'build/bwm-plasma-host-tests/store-preview'
    results = []

    def env_for(item):
        env = store.environment(item)
        env.update(WAYLAND_DISPLAY=os.environ['WAYLAND_DISPLAY'], QT_QPA_PLATFORM='wayland',
                   BWM_FOCUS_NESTED='1', HYPRLAND_INSTANCE_SIGNATURE=os.environ['HYPRLAND_INSTANCE_SIGNATURE'],
                   PULSE_SERVER='unix:' + str(item / 'no-audio'), PIPEWIRE_REMOTE='bwm-no-pipewire')
        return env

    def case(item, mode, resource):
        name = mode + '-' + str(len(results))
        output = item / (name + '.json'); capture = item / ('capture-' + name + '.png')
        output.unlink(missing_ok=True)
        env = env_for(item)
        argv = store.sandbox(work, item, ['dbus-run-session', '--', binary, mode, resource, output])
        # Downloads need networking; rendering reviewed resources does not.
        argv.insert(argv.index('--new-session'), '--unshare-net')
        with (item / (name + '.log')).open('w') as log:
            process = subprocess.Popen(argv, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                end = time.monotonic() + 12
                while not output.exists() and process.poll() is None and time.monotonic() < end: time.sleep(.1)
                if not output.exists(): raise RuntimeError('No resource report: '+name)
                result = json.loads(output.read_text())
                time.sleep(.2)
                subprocess.run(['grim', str(capture)], env=dict(os.environ), check=True, timeout=4, capture_output=True)
                result.update(item=item.name, capture=capture.name)
                results.append(result)
                (work / 'visual.json').write_text(json.dumps(results, ensure_ascii=False, indent=2))
            finally:
                if process.poll() is None: os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=5)

    for item in sorted(work.iterdir()):
        if not (item / 'install.json').exists() or item.name.startswith('lookandfeel-'): continue
        env_for(item)
        data = item / 'data'
        if item.name.startswith('colorschemes-'):
            for path in sorted((data / 'color-schemes').glob('*.colors')): case(item, 'colors', str(path))
        elif item.name.startswith('icons-'):
            for path in sorted((data / 'icons').iterdir()):
                if (path / 'index.theme').exists(): case(item, 'icons', path.name)
        elif item.name.startswith('plasma-themes-'):
            for path in sorted((data / 'plasma/desktoptheme').iterdir()): case(item, 'desktoptheme', path.name)
        elif item.name.startswith('plasmoids-'):
            assert review[item.name]['approved'], 'Widget must be reviewed first'
            assert review[item.name]['sha256'] == store.tree_hash(data / 'plasma'), 'Review is stale'
            for path in sorted((data / 'plasma/plasmoids').iterdir()):
                plugin = json.loads((path / 'metadata.json').read_text())['KPlugin']['Id']
                case(item, 'widget', plugin)
        elif item.name.startswith('isolated-lookandfeel-'):
            assert review[item.name]['approved'], 'Global QML/layout must be reviewed first'
            assert review[item.name]['sha256'] == store.tree_hash(data / 'plasma'), 'Review is stale'
            selected = review[item.name]['package']
            for mode in ['layout', 'splash', 'logout']: case(item, mode, selected)
        elif item.name.startswith(('aurorae-', 'window-decorations-', 'cpp-')):
            for path in sorted(item.glob('decoration-*.png')): case(item, 'decoration', str(path))
        elif item.name.startswith('xcursor-'):
            for path in sorted(item.glob('cursor-*.png')): case(item, 'cursor', str(path))
    print(json.dumps({'cases': len(results), 'loaded': sum(bool(x.get('loaded')) for x in results)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
