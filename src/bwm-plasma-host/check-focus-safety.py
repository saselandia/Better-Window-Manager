#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise focus grabs/native editing in a nested Hyprland on a temporary headless output.

No daily host, user layout, physical input device, capture or plugin is used. Every
keyboard/pointer focus change made by Qt belongs to the disposable child compositor.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time


def hypr(*args, instance=None):
    return subprocess.run(['hyprctl', *(['-i', instance] if instance else []), *args],
                          check=True, capture_output=True, text=True, timeout=5).stdout


def wait(predicate, message):
    end = time.monotonic() + 15
    while time.monotonic() < end:
        value = predicate()
        if value:
            return value
        time.sleep(.1)
    raise TimeoutError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--edit-mode', action='store_true',
                        help='Run native panel settings, widget explorer and desktop edit mode with direct disposable views')
    parser.add_argument('--client-timeout', type=int, default=55,
                        help='Deadline for a disposable client matrix (default 55 seconds, maximum 600)')
    args = parser.parse_args()
    if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):
        parser.error('A Hyprland parent session is required')
    before = {i['instance'] for i in json.loads(hypr('instances', '-j'))}
    if any(c.get('class') == 'aquamarine' for c in json.loads(hypr('-j', 'clients'))):
        parser.error('Another nested compositor is already open')
    physical = lambda: [{k: m[k] for k in ('name', 'x', 'y', 'width', 'height', 'scale', 'transform')}
                        for m in json.loads(hypr('-j', 'monitors')) if m['name'] != output]
    output = f'BWM-FOCUS-{os.getpid()}'
    rule = f'bwm-focus-{os.getpid()}'
    previous_outputs = physical()
    created = rule_added = False
    nested = None
    report = {'passed': False, 'dailyHostStarted': False, 'pluginsLoaded': False}
    with tempfile.TemporaryDirectory(prefix='bwm-focus-safety-') as temporary:
        root = Path(temporary)
        try:
            hypr('output', 'create', 'headless', output)
            created = True
            hypr('eval', f'hl.monitor({{output="{output}",mode="1280x800@60",position="20000x20000",scale=1}})')
            monitor = wait(lambda: next((m for m in json.loads(hypr('-j', 'monitors')) if m['name'] == output), None),
                           'Temporary output did not appear')
            workspace = monitor['activeWorkspace']['id']
            hypr('eval', f'hl.window_rule({{name="{rule}",match={{class="^aquamarine$"}},workspace="{workspace} silent",no_initial_focus=true}})')
            rule_added = True
            config = root / 'hyprland.lua'
            config.write_text('''hl.monitor({output="",mode="1280x800",position="0x0",scale=1})
hl.config({misc={disable_hyprland_logo=true,disable_splash_rendering=true},animations={enabled=false},
 xwayland={enabled=false},input={follow_mouse=2},decoration={blur={enabled=false}}})
hl.window_rule({name="typing-fixture",match={title="^BWM typing fixture$"},float=true,size="500 300",move="300 200"})
''')
            env = {k: v for k, v in os.environ.items() if not k.startswith(('QT_', 'BWM_R4_', 'BWM_R5_', 'DBUS_'))
                   and k not in ('HYPRLAND_INSTANCE_SIGNATURE', 'WAYLAND_SOCKET', 'DISPLAY', 'XDG_ACTIVATION_TOKEN')}
            for variable, name in [('XDG_CONFIG_HOME', 'config'), ('XDG_DATA_HOME', 'data'), ('XDG_CACHE_HOME', 'cache')]:
                (root / name).mkdir(mode=0o700)
                env[variable] = str(root / name)
            env.update(DBUS_SESSION_BUS_ADDRESS='unix:path='+str(root/'no-bus'), DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(root/'no-system-bus'))
            with (root/'hypr.log').open('w') as log:
                nested = subprocess.Popen(['Hyprland', '--config', str(config)], env=env, stdout=log,
                                          stderr=subprocess.STDOUT, start_new_session=True)
            instance = wait(lambda: next((i for i in json.loads(hypr('instances', '-j')) if i['pid'] == nested.pid), None),
                            'Nested compositor did not start')
            signature = instance['instance']
            monitors = wait(lambda: json.loads(hypr('-j', 'monitors', instance=signature)), 'Nested output missing')
            runtime = Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}'))
            env.update(WAYLAND_DISPLAY=str(runtime/instance['wl_socket']), HYPRLAND_INSTANCE_SIGNATURE=signature,
                       QT_QPA_PLATFORM='wayland', QT_QUICK_BACKEND='software', BWM_FOCUS_NESTED='1',
                       BWM_FOCUS_COMPOSITOR_PID=str(nested.pid), BWM_FOCUS_CONFIG=str(config))
            cases = []
            if args.edit_mode:
                env.update(BWM_R5_OUTPUT=monitors[0]['description'], BWM_R5_HYPR_RUNTIME=str(runtime))
                cases = ['inputFixtureRejectsWrongPeer', 'typingSurvivesNativeSurfaces',
                         'originalEditorAndExplorerOnNestedOutput', 'originalDesktopEditModeOnNestedOutput']
            reply = subprocess.run([str(args.binary.resolve()), *cases], env=env, capture_output=True, text=True,
                                   timeout=100 if args.edit_mode else min(600, max(1, args.client_timeout)))
            report.update(passed=reply.returncode == 0, testExit=reply.returncode,
                          testOutput=reply.stdout, diagnostics=reply.stderr,
                          nestedConfigErrors=hypr('configerrors', instance=signature).strip())
            if args.edit_mode:
                report['missingVisualParentWarning'] = 'QML PanelConfigView: Exposed with no visual parent' in (reply.stdout + reply.stderr)
                report['passed'] = report['passed'] and not report['missingVisualParentWarning']
            if report['nestedConfigErrors']:
                report['passed'] = False
        except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError) as error:
            report.update(passed=False, error=str(error))
            if isinstance(error, subprocess.TimeoutExpired):
                report['testOutput'] = (error.stdout or b'').decode(errors='replace') if isinstance(error.stdout, bytes) else (error.stdout or '')
                report['diagnostics'] = (error.stderr or b'').decode(errors='replace') if isinstance(error.stderr, bytes) else (error.stderr or '')
            if (root/'hypr.log').exists():
                report['nestedLogTail'] = (root/'hypr.log').read_text(errors='replace')[-1800:]
        finally:
            if nested and nested.poll() is None:
                os.killpg(nested.pid, signal.SIGTERM)
                try:
                    nested.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(nested.pid, signal.SIGKILL)
                    nested.wait(timeout=5)
            if rule_added:
                hypr('eval', f'hl.window_rule({{name="{rule}",match={{class="^bwm-focus-never$"}}}})')
            if created:
                hypr('output', 'remove', output)
            report['physicalOutputsUnchanged'] = physical() == previous_outputs
            report['cleanupVerified'] = (nested is None or nested.poll() is not None) and not any(
                i['pid'] == (nested.pid if nested else -1) for i in json.loads(hypr('instances', '-j')))
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['passed'] and report['cleanupVerified'] and report['physicalOutputsUnchanged'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
