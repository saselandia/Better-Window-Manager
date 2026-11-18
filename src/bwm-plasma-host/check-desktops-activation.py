#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Explicit native KDE focus or same-output workspace navigation cycle.

--focus-cycle visits already-active output/desktop pairs. --workspace-cycle
temporarily visits an unused configured ID bound to the focused output.
Both verify their return; neither relocates windows or changes configuration.
"""
import argparse
from contextlib import contextmanager
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import resource
import stat
import subprocess
import sys
import tempfile

spec = importlib.util.spec_from_file_location('desktop_session_check', Path(__file__).with_name('check-desktops-session.py'))
session = importlib.util.module_from_spec(spec);spec.loader.exec_module(session)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'config/hypr/skins/plasma/scripts'))
from native_guard import action_lock, require_breeze


@contextmanager
def stable_skin(path=Path('/tmp/bwm-theme-manager.lock')):
    # The real manager uses an exclusive nonblocking flock on this inode.
    # Share it for the short explicit diagnostic; never truncate or unlink it.
    descriptor = os.open(path, os.O_RDONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        info = os.fstat(descriptor)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) & 0o022):
            raise ValueError('Unsafe skin-change lock')
        fcntl.flock(descriptor, fcntl.LOCK_SH | fcntl.LOCK_NB)
        yield
    finally:
        os.close(descriptor)


COUNTERS = ('acceptedRequests', 'appliedActivations', 'observedActivations', 'dispatchedActivations',
            'failedActivations', 'rejectedRequests', 'cancelledActivations', 'activationNoops')
PROVIDER_FIELDS = COUNTERS + ('version', 'enabled', 'providerAvailable', 'arbitrationState',
    'providerRestartRequired', 'desktops', 'current', 'queuedActivations',
    'lastError', 'lastActivationError', 'lastActivationOutcome', 'lastRejectedOperation', 'activationRoutingVersion')


def provider_diagnostic():
    provider = session.query('bwm-plasma-desktops')
    if not isinstance(provider, dict):
        raise ValueError('Invalid provider diagnostic')
    return {key: provider[key] for key in PROVIDER_FIELDS if key in provider}


def diagnose_last():
    report = {'version': 1, 'readOnly': True, 'diagnosticComplete': False, 'activationAttempted': False}
    for key, reader in (('provider', provider_diagnostic), ('session', session.session_snapshot)):
        try:
            report[key] = reader()
        except (OSError, ValueError, TypeError, KeyError, AttributeError, subprocess.SubprocessError) as error:
            report[key+'ReadError'] = str(error)
    report['diagnosticComplete'] = 'provider' in report and 'session' in report
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['diagnosticComplete'] else 1


def counters(*, require_clean=True, require_routing=False):
    provider = session.query('bwm-plasma-desktops')
    if require_routing and (not isinstance(provider, dict) or type(provider.get('activationRoutingVersion')) is not int
                            or provider['activationRoutingVersion'] != 2):
        raise ValueError('El proveedor cargado usa la ruta anterior de activación. Instala el módulo corregido '
                         'con make install y vuelve a entrar en la sesión; no cargar/descargar en caliente.')
    if (not isinstance(provider, dict) or any(type(provider.get(key)) is not int or provider[key] < 0 for key in COUNTERS)
            or provider.get('lastError') or (require_clean and provider.get('lastActivationError'))):
        raise ValueError('Provider activation counters unavailable or error reported')
    return {key: provider[key] for key in COUNTERS}


def require_no_special_outputs():
    monitors = session.query('monitors')
    if (not isinstance(monitors, list) or not monitors
            or any(not isinstance(output, dict) or not isinstance(output.get('specialWorkspace'), dict)
                   or type(output['specialWorkspace'].get('id')) is not int or output['specialWorkspace']['id'] != 0
                   for output in monitors)):
        raise ValueError('Close visible special workspaces before the explicit focus cycle')


def select_workspace_target(before):
    """Only an unused configured ID explicitly bound here, without creation hooks.

    Hyprland 0.56.2 WorkspaceState::create consults workspace monitor bindings
    even when given the focused monitor. Audit the live rule inventory rather
    than guessing that an absent workspace will be created on this output.
    """
    original = [output for output in before['outputs'] if output['current'] == before['current']]
    if len(original) != 1:
        raise ValueError('The original focused output is ambiguous')
    workspaces, rules, monitors = (session.query(name) for name in ('workspaces', 'workspacerules', 'monitors'))
    if not all(isinstance(value, list) for value in (workspaces, rules, monitors)):
        raise ValueError('Workspace/rule/output inventory unavailable')
    live = set()
    for workspace in workspaces:
        if not isinstance(workspace, dict) or type(workspace.get('id')) is not int:
            raise ValueError('Invalid live workspace inventory')
        live.add(str(workspace['id']))
    current = [output for output in monitors if isinstance(output, dict)
               and output.get('description') == original[0]['description']]
    if (len(current) != 1 or current[0].get('focused') is not True
            or str(current[0].get('activeWorkspace', {}).get('id')) != before['current']):
        raise ValueError('Focused output changed during workspace selection')
    bindings = {'desc:'+original[0]['description']}
    if isinstance(current[0].get('name'), str) and current[0]['name']:
        bindings.add(current[0]['name'])  # Ephemeral comparison only; never persisted.
    exact = {}
    for rule in rules:
        if not isinstance(rule, dict) or type(rule.get('enabled')) is not bool:
            raise ValueError('Incomplete workspace-rule diagnostic')
        if not rule['enabled']:
            continue
        selector, binding = rule.get('workspaceString'), rule.get('monitor', '')
        if not isinstance(selector, str) or not isinstance(binding, str):
            raise ValueError('Invalid workspace binding')
        if (('onCreatedEmpty' in rule and not isinstance(rule['onCreatedEmpty'], str))
                or ('persistent' in rule and type(rule['persistent']) is not bool)):
            raise ValueError('Invalid workspace creation policy')
        if selector.isascii() and selector.isdecimal() and str(int(selector)) == selector:
            exact.setdefault(selector, []).append(rule)
        elif not selector.startswith('special:') and (binding or rule.get('onCreatedEmpty')):
            raise ValueError('Non-literal workspace binding/creation hook cannot be audited for this test')
    for desktop in before['desktopIds']:
        if (not isinstance(desktop, str) or not desktop.isascii() or not desktop.isdecimal()
                or str(int(desktop)) != desktop
                or not session.ordinary(int(desktop)) or not 1 <= int(desktop) <= before['configuredCount']
                or desktop in live):
            continue
        matches = exact.get(desktop, [])
        if len(matches) != 1:
            continue
        rule = matches[0]
        if (rule.get('monitor') in bindings and not rule.get('onCreatedEmpty')
                and rule.get('persistent') is not True):
            return desktop
    raise ValueError('No unused configured desktop explicitly bound to the focused output without creation hooks')


def compare_cycle(before, after, native, counts_before, counts_after, navigation_target=None):
    if before != after:
        raise ValueError('Output assignments or initial focus were not restored, or the desktop inventory changed')
    if (not isinstance(native, dict) or type(native.get('version')) is not int or native['version'] != 1
            or native.get('readOnly') is not False or native.get('passed') is not True
            or native.get('paused') is not True or native.get('restoredInitialOutput') is not True
            or type(native.get('windowCount')) is not int or native['windowCount'] != 0):
        raise ValueError('The native focus cycle did not complete with pause and restoration verified')
    original = [output for output in before['outputs'] if output['current'] == before['current']]
    if len(original) != 1:
        raise ValueError('The original focused output is ambiguous')
    if navigation_target is None:
        route = [output for output in before['outputs'] if output != original[0]]+[original[0]]
    else:
        if (native.get('navigationTarget') != navigation_target or native.get('activationMethod') != 'requestActivate'
                or navigation_target not in before['desktopIds']
                or navigation_target in [output['current'] for output in before['outputs']]):
            raise ValueError('Invalid native workspace navigation target or activation method')
        route = [dict(original[0], current=navigation_target), original[0]]
    steps = native.get('steps')
    if (not isinstance(steps, list) or len(steps) != len(route)
            or type(native.get('activationRequestsSent')) is not int or native['activationRequestsSent'] != len(route)):
        raise ValueError('The native focus cycle did not visit every output and return')
    for expected, observed in zip(route, steps):
        if (not isinstance(observed, dict) or observed.get('description') != expected['description']
                or observed.get('current') != expected['current'] or observed.get('verified') is not True):
            raise ValueError('A native focus step differs from the existing desktop/output pair')
    delta = {key: counts_after[key]-counts_before[key] for key in COUNTERS}
    for key in ('acceptedRequests', 'appliedActivations', 'observedActivations', 'dispatchedActivations'):
        if delta[key] != len(route):
            raise ValueError('Provider counters disagree with the native cycle (or another client activated desktops)')
    if any(delta[key] for key in ('failedActivations', 'rejectedRequests', 'cancelledActivations', 'activationNoops')):
        raise ValueError('A native activation failed, was cancelled, rejected or a no-op')
    return delta


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument('--focus-cycle', action='store_true',
                           help='Explicitly focus other outputs and then the original one using KDE requests')
    operation.add_argument('--workspace-cycle', action='store_true',
                           help='Visit an unused configured desktop on the focused output and return, using KDE requests')
    operation.add_argument('--diagnose-last', action='store_true',
                           help='Read the provider counters/errors and current output assignments without repeating the cycle')
    parser.add_argument('--binary', type=Path, default=Path(__file__).resolve().parents[2]/'build/bwm-plasma-host/bwm-plasma-host')
    args = parser.parse_args(argv)
    if args.diagnose_last:
        return diagnose_last()
    binary = args.binary.expanduser().resolve()
    report = {'version': 1, 'readOnly': False, 'passed': False, 'activationAttempted': False,
              'configurationChanged': False, 'panelsOpened': False, 'capturesStarted': False,
              'replacementReady': False}
    navigation_target = None
    try:
        if not binary.is_file() or not os.access(binary, os.X_OK):
            raise ValueError('No executable host at '+str(binary))
        with stable_skin(), action_lock():
            require_breeze()
            require_no_special_outputs()
            before = session.session_snapshot()
            if not (1 if args.workspace_cycle else 2) <= len(before['outputs']) <= 8:
                raise ValueError('Cycle requires a supported number of active outputs')
            original = [output for output in before['outputs'] if output['current'] == before['current']]
            if len(original) != 1:
                raise ValueError('The original focused output is ambiguous')
            initial_counts = counters(require_clean=False, require_routing=True)
            if args.workspace_cycle:
                navigation_target = select_workspace_target(before)
                report['selectedDesktop'] = navigation_target
            inherited = ()
            if os.environ.get('WAYLAND_SOCKET'):
                descriptor = int(os.environ['WAYLAND_SOCKET']);os.fstat(descriptor);inherited = (descriptor,)
            with tempfile.TemporaryDirectory(prefix='bwm-r4-desktop-activation-') as tmp:
                root = Path(tmp)
                for name in ('config', 'data', 'cache', 'runtime', 'defaults'):
                    (root/name).mkdir(mode=0o700)
                def no_core():
                    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
                if navigation_target is not None and select_workspace_target(before) != navigation_target:
                    raise ValueError('Workspace selection changed before the cycle')
                report['activationAttempted'] = True
                operation = ['--check-native-desktops-focus-cycle', original[0]['description']]
                if navigation_target is not None:
                    operation = ['--check-native-desktops-workspace-cycle', original[0]['description'], navigation_target]
                reply = subprocess.run([str(binary), *operation,
                                        *(output['description'] for output in before['outputs'])],
                                       env=session.isolated_environment(root, os.environ), pass_fds=inherited,
                                       capture_output=True, text=True, timeout=20, preexec_fn=no_core)
                if len(reply.stdout) > 65536:
                    raise ValueError('Native activation diagnostic exceeds the size limit')
                try:
                    native = json.loads(reply.stdout)
                except ValueError:
                    raise ValueError('Native activation diagnostic returned no JSON (exit '+str(reply.returncode)+')') from None
                if isinstance(native, dict):
                    report['nativeDiagnostic'] = native
                    report['restoredInitialOutput'] = native.get('restoredInitialOutput') is True
                    report['paused'] = native.get('paused') is True
                if reply.returncode:
                    # Keep the first failure and inspect its server-side receipt;
                    # do not discard it or issue a second activation as a probe.
                    try:
                        report['providerAfter'] = provider_diagnostic()
                    except (OSError, ValueError, subprocess.SubprocessError) as error:
                        report['providerReadError'] = str(error)
                    detail = native.get('error', 'cycle incomplete') if isinstance(native, dict) else 'invalid diagnostic'
                    raise ValueError('Native activation diagnostic failed: '+str(detail))
            require_breeze()
            require_no_special_outputs()
            after = session.session_snapshot()
            delta = compare_cycle(before, after, native, initial_counts, counters(), navigation_target=navigation_target)
            report.update(passed=True, restoredInitialOutput=True, paused=True,
                          current=after['current'], steps=native['steps'], providerCounterDelta=delta,
                          activationRequestsSent=native['activationRequestsSent'], windowCount=0)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, TimeoutError, subprocess.SubprocessError) as error:
        report['error'] = str(error)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
