#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Real-Hyprland acceptance of bwm-plasma-desktops in a DISPOSABLE nested Hyprland.

Starts a fresh Hyprland as a client window of the current session (sent silently to a
hidden workspace), loads the provider module ONLY into that nested instance, enables it,
opens two own kitty windows there and runs test-desktops-hyprland against it. The nested
compositor is terminated at the end. The session compositor never loads, unloads or
enables the module; its only change is one temporary window rule that is retired.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

RULE = 'bwm-r4-nested-provider'
NESTED_CONFIG = '''-- Disposable nested Hyprland for BWM R4 provider acceptance. No user modules.
hl.monitor({ output = "", mode = "1280x800", position = "0x0", scale = 1 })
hl.config({ misc = { disable_hyprland_logo = true, disable_splash_rendering = true }, animations = { enabled = false } })
hl.window_rule({ name = "bwm-r4-nested-b", match = { class = "bwm-r4-nested-b" }, workspace = "2 silent" })
'''


def hyprctl(*args, instance=None, check=True):
    command = ['hyprctl'] + (['-i', instance] if instance else []) + list(args)
    reply = subprocess.run(command, capture_output=True, text=True, timeout=5)
    if check and reply.returncode:
        raise RuntimeError(f'hyprctl {" ".join(args[:2])}: {reply.stderr.strip() or reply.stdout.strip()}')
    return reply.stdout


def wait(predicate, timeout, what):
    deadline = time.monotonic()+timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(.1)
    raise TimeoutError(what)


def parent_rule(workspace):
    match = 'aquamarine' if workspace else '^bwm-r4-never-matches$'
    body = f'hl.window_rule({{ name = "{RULE}", match = {{ class = "{match}" }}'
    body += f', workspace = "{workspace} silent", no_initial_focus = true }})' if workspace else ' })'
    hyprctl('eval', body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--module', type=Path, required=True)
    parser.add_argument('--test', type=Path, required=True)
    parser.add_argument('--workspace', type=int, default=9, help='Hidden session workspace for the nested window')
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--via-startup', action='store_true',
                        help='Load/enable/publish through native-desktops.py startup (the login path) instead of direct hyprctl')
    args = parser.parse_args()
    report = {'version': 1, 'nested': True, 'passed': False}
    if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE') or not os.environ.get('WAYLAND_DISPLAY'):
        parser.error('Run from a Hyprland session terminal (needed to host the nested compositor window)')
    runtime = Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}'))
    before = {i['instance'] for i in json.loads(hyprctl('instances', '-j'))}
    nested = None
    try:
        with tempfile.TemporaryDirectory(prefix='bwm-r4-nested-') as temporary:
            root = Path(temporary)
            (root/'hyprland.lua').write_text(NESTED_CONFIG)
            for name in ('config/illogical-impulse', 'data', 'cache'):
                (root/name).mkdir(parents=True, mode=0o700)
            (root/'config/illogical-impulse/config.json').write_text('{"appearance":{"bwmTheme":"plasma"}}')
            parent_rule(args.workspace)
            env = {k: v for k, v in os.environ.items() if k != 'HYPRLAND_INSTANCE_SIGNATURE'}
            nested = subprocess.Popen(['Hyprland', '--config', str(root/'hyprland.lua')], env=env,
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            instance = wait(lambda: next((i for i in json.loads(hyprctl('instances', '-j'))
                                          if i['instance'] not in before and i['pid'] == nested.pid), None), 20, 'Nested Hyprland did not start')
            signature, socket = instance['instance'], instance['wl_socket']
            report['nestedVersion'] = json.loads(hyprctl('-j', 'version', instance=signature)).get('tag')
            if args.via_startup:
                # Login path: opt-in file, installed module copy, shared count 4, then
                # native-desktops.py startup with this nested instance's signature.
                (root/'config/bwm').mkdir(parents=True)
                (root/'config/bwm/native-desktops.json').write_text('{"version":1,"enabled":true}')
                (root/'config/hypr/plugins').mkdir(parents=True)
                (root/'config/hypr/plugins/bwm-plasma-desktops.so').write_bytes(args.module.read_bytes())
                (root/'config/illogical-impulse/config.json').write_text('{"appearance":{"bwmTheme":"plasma"},"bar":{"workspaces":{"shown":4}}}')
                startup_env = dict(env, HYPRLAND_INSTANCE_SIGNATURE=signature, XDG_CONFIG_HOME=str(root/'config'),
                                   XDG_STATE_HOME=str(root/'state'), BWM_R4_NESTED_HYPRLAND='1', BWM_NATIVE_DESKTOPS_STABLE_SECONDS='2')
                script = Path(__file__).resolve().parents[2]/'config/hypr/skins/plasma/scripts/native-desktops.py'
                started = subprocess.run([sys.executable, str(script), 'startup'], env=startup_env, capture_output=True, text=True, timeout=60)
                report['startup'] = json.loads((root/'state/bwm/plasma/native-desktops-last-startup.json').read_text())
                if started.returncode or not report['startup'].get('loaded') or not report['startup'].get('stable'):
                    raise RuntimeError('native-desktops.py startup failed: '+json.dumps(report['startup']))
                marker = json.loads((runtime/'bwm-native-desktops.json').read_text())
                report['sessionMarkerForNestedInstance'] = marker.get('instance') == signature
                (runtime/'bwm-native-desktops.json').unlink() # Never leave a nested marker in the shared runtime.
            else:
                loaded = hyprctl('plugin', 'load', str(args.module.resolve()), instance=signature).strip()
                if loaded != 'ok':
                    raise RuntimeError('Module load in nested Hyprland failed: '+loaded)
                count = json.loads(hyprctl('bwm-plasma-desktops-count', '4', instance=signature))
                assert count.get('accepted') is True, count
                hyprctl('eval', 'hl.config({ plugin = { bwm_plasma_desktops = { enabled = true } } })', instance=signature)
            report['moduleLoadedInNestedOnly'] = True
            provider = wait(lambda: (lambda d: d if d.get('arbitrationState') == 'active' and d.get('providerAvailable') else None)(
                json.loads(hyprctl('-j', 'bwm-plasma-desktops', instance=signature))), 5, 'Provider did not become active')
            report['providerBefore'] = {k: provider.get(k) for k in ('enabled', 'providerAvailable', 'arbitrationState', 'desktops', 'current')}
            for name in ('a', 'b'):
                hyprctl('dispatch', f'hl.dsp.exec_cmd("kitty --config NONE --class bwm-r4-nested-{name}")', instance=signature)
            wait(lambda: sum(1 for c in json.loads(hyprctl('-j', 'clients', instance=signature))
                             if str(c.get('class', '')).startswith('bwm-r4-nested-')) == 2, 15, 'Fixture windows missing')
            test_env = dict(env, HYPRLAND_INSTANCE_SIGNATURE=signature, BWM_R4_NESTED_SIGNATURE=signature,
                            BWM_R4_NESTED_HYPRLAND='1', WAYLAND_DISPLAY=str(runtime/socket), QT_QPA_PLATFORM='wayland',
                            XDG_CONFIG_HOME=str(root/'config'), XDG_DATA_HOME=str(root/'data'), XDG_CACHE_HOME=str(root/'cache'),
                            DBUS_SESSION_BUS_ADDRESS='unix:path='+str(root/'no-bus'))
            for key in ('WAYLAND_SOCKET', 'KDESYCOCA'):
                test_env.pop(key, None)
            test = subprocess.run([str(args.test)], env=test_env, capture_output=True, text=True, timeout=90)
            report['testOutput'] = '\n'.join(line for line in test.stdout.splitlines() if not line.startswith('QWARN'))[-4000:]
            report['testExit'] = test.returncode
            provider = json.loads(hyprctl('-j', 'bwm-plasma-desktops', instance=signature))
            report['providerAfter'] = {k: provider.get(k) for k in ('appliedActivations', 'observedActivations', 'rejectedRequests',
                                                                    'cancelledActivations', 'lastError', 'desktops', 'current')}
            report['passed'] = test.returncode == 0
    except (OSError, ValueError, RuntimeError, TimeoutError, AssertionError, subprocess.SubprocessError) as error:
        report['error'] = str(error)
    finally:
        if nested and nested.poll() is None:
            os.killpg(nested.pid, signal.SIGTERM)
            try:
                nested.wait(10)
            except subprocess.TimeoutExpired:
                os.killpg(nested.pid, signal.SIGKILL);nested.wait(5)
        try:
            parent_rule(None)
        except (RuntimeError, OSError, subprocess.SubprocessError) as error:
            report['ruleCleanupError'] = str(error)
        after = {i['instance'] for i in json.loads(hyprctl('instances', '-j'))}
        report['cleanupVerified'] = after <= before and (nested is None or nested.poll() is not None)
        report['sessionCompositorModuleLoaded'] = 'bwm-plasma-desktops' in hyprctl('plugin', 'list', check=False)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: report.get(k) for k in ('passed', 'error', 'testExit', 'cleanupVerified', 'providerAfter')}, ensure_ascii=False))
    return 0 if report['passed'] and report['cleanupVerified'] and not report['sessionCompositorModuleLoaded'] else 1


if __name__ == '__main__':
    sys.exit(main())
