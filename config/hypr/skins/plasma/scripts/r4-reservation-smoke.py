#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Explicit R4 reservation/own-window test, with optional existing bridge refresh."""
import argparse
from contextlib import ExitStack
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

spec = importlib.util.spec_from_file_location('r4_check', Path(__file__).with_name('r4-session-check.py'))
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)
ROOT = Path(__file__).resolve().parents[5]
fixture_spec = importlib.util.spec_from_file_location('r4_maximized', Path(__file__).with_name('r4-maximized-check.py'))
maximized = importlib.util.module_from_spec(fixture_spec)
fixture_spec.loader.exec_module(maximized)
session_spec = importlib.util.spec_from_file_location('r4_panel_session', Path(__file__).with_name('panel-session.py'))
session = importlib.util.module_from_spec(session_spec)
session_spec.loader.exec_module(session)


def by_description(snapshot):
    result = {}
    for monitor in snapshot.get('monitors', []):
        description = monitor.get('description')
        if not description or description in result: raise ValueError('Descripción de salida ausente o ambigua')
        result[description] = monitor
    return result


RESERVED_INDEX = {'left': 0, 'top': 1, 'right': 2, 'bottom': 3}


def evaluate(before, during, after, description, edge=None):
    """Compare logical reservation deltas for one panel per requested output."""
    descriptions = (description,) if isinstance(description, str) else tuple(description)
    index = RESERVED_INDEX[edge or 'bottom']
    errors = []
    measurements = []
    try:
        states = [by_description(s) for s in (before, during, after)]
        if (not descriptions or len(set(descriptions)) != len(descriptions) or
                any(set(s) != set(states[0]) for s in states) or not set(descriptions) <= states[0].keys()):
            raise ValueError('Las salidas cambiaron durante el ensayo')
        for s in (before, after):
            if s.get('status') != 'access-ok-no-native-preview' or s.get('nativeLayers'):
                errors.append('Ensayo previo existente o limpieza sin confirmar')
        runtime = during.get('preview', {}).get('runtime', {})
        panels = runtime.get('panels', [])
        if (during.get('status') != 'observations-collected' or runtime.get('nativePanelPolicy') is not True or
                runtime.get('skin') != 'plasma' or len(panels) != len(descriptions)):
            raise ValueError('No se confirmó un panel nativo por cada salida solicitada')
        zones = {}
        for panel in panels:
            output = panel.get('outputDescription')
            zone = panel.get('exclusiveZoneRequested')
            if (output not in descriptions or output in zones or
                    panel.get('edge', 'bottom' if edge is None else None) != (edge or 'bottom') or
                    type(zone) is not int or zone <= 0 or panel.get('reservationRequested') is not True or
                    panel.get('renderReady') is not True):
                raise ValueError('El panel no confirmó salida, borde, fotograma y petición de reserva')
            zones[output] = zone
        for output, original in states[0].items():
            observed, restored = states[1][output], states[2][output]
            for key in ('name', 'x', 'y', 'width', 'height', 'scale', 'transform'):
                if original.get(key) != observed.get(key) or original.get(key) != restored.get(key):
                    errors.append(f'{output}: cambió la salida o su geometría durante el ensayo')
                    break
            expected = original['reserved'].copy()
            expected[index] += zones.get(output, 0)
            if observed['reserved'] != expected:
                errors.append(f'{output}: la reserva observada no coincide con la esperada')
            if restored['reserved'] != original['reserved']:
                errors.append(f'{output}: no se restauró la reserva original')
            measurements.append({'outputDescription': output, 'requestedZone': zones.get(output, 0),
                                 'before': original['reserved'], 'observed': observed['reserved'],
                                 'expected': expected, 'after': restored['reserved']})
        layers = [l for l in during.get('nativeLayers', []) if l.get('namespace') == 'bwm-r4-native-policy']
        outputs = [states[1][output]['name'] for output in descriptions]
        if len(layers) != len(outputs) or {l.get('output') for l in layers} != set(outputs):
            errors.append('No se confirma una única capa nativa por salida solicitada')
    except (ValueError, KeyError, TypeError, IndexError) as exc:
        errors.append(str(exc))
    return {'reservationDeltaVerified': not errors, 'maximizedWindowVerified': False,
            'realAreaVerified': False, 'r4Complete': False, 'errors': errors, 'reservationsByOutput': measurements}


def prepare_profile(root, binary, package, descriptions, edge):
    """Build a disposable profile using the same native migration/import as BWM."""
    for name in ('config', 'data', 'cache', 'runtime', 'defaults'):
        (root/name).mkdir(mode=0o700)
    env = {key: value for key, value in os.environ.items() if not key.startswith('BWM_R4_') and key not in
           ('DISPLAY', 'WAYLAND_DISPLAY', 'WAYLAND_SOCKET', 'HYPRLAND_INSTANCE_SIGNATURE', 'KDESYCOCA')}
    env.update(QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software', XDG_CONFIG_HOME=str(root/'config'),
               XDG_DATA_HOME=str(root/'data'), XDG_CACHE_HOME=str(root/'cache'), XDG_RUNTIME_DIR=str(root/'runtime'),
               XDG_CONFIG_DIRS=str(root/'defaults'), XDG_DATA_DIRS='/usr/local/share:/usr/share',
               DBUS_SESSION_BUS_ADDRESS='unix:path='+str(root/'no-bus'))
    policy_spec = importlib.util.spec_from_file_location('r4_reservation_policy', ROOT/'config/hypr/skins/plasma/scripts/native_launch.py')
    policy = importlib.util.module_from_spec(policy_spec)
    policy_spec.loader.exec_module(policy)
    policy.write_host_policy(root/'defaults')
    packageroot = root/'data/plasma/plasmoids'
    packageroot.mkdir(parents=True)
    widget = json.loads((package/'metadata.json').read_text())['KPlugin']['Id']
    legacy = json.dumps({'bar': {'plasma': {'edge': edge, 'thickness': 48, 'style': 'opaque'}}})
    plan = {'version': 1, 'legacyJson': legacy, 'sourceSha256': hashlib.sha256(legacy.encode()).hexdigest(),
            'panels': [{'outputDescription': output, 'containmentPackage': 'org.kde.panel',
                        'widgets': [{'package': widget, 'nativeSettings': {}}]} for output in descriptions]}
    proposal = root/'proposal.json'
    proposal.write_text(json.dumps(plan))

    def run(*arguments):
        result = subprocess.run(arguments, env=env, capture_output=True, text=True, timeout=12)
        if result.returncode:
            raise ValueError('No se pudo preparar el perfil de prueba: ' + (result.stderr or result.stdout)[-900:])
        return result.stdout

    run('kpackagetool6', '--type', 'Plasma/Applet', '--packageroot', str(packageroot), '--install', str(package.resolve()))
    stage = json.loads(run(str(binary.resolve()), '--stage-migration', str(proposal)))
    profile = json.loads(run(str(binary.resolve()), '--import-profile', stage['directory']))
    return profile, root/'data'


def stop_child(child):
    if child.poll() is not None: return
    # The wrapper converts group Ctrl+C into its acknowledged stop/flush/cleanup.
    for sig, timeout in ((signal.SIGINT, 7), (signal.SIGTERM, 2), (signal.SIGKILL, 2)):
        try: os.killpg(child.pid, sig)
        except ProcessLookupError: pass
        try:
            child.wait(timeout=timeout)
            return
        except subprocess.TimeoutExpired: pass
    raise TimeoutError('No se confirmó la terminación del auxiliar temporal')


def confirm_fixture_exit(child):
    registration = session.active_registration()
    instance = os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')
    if (not instance or registration is None or registration.get('compositorInstance') != instance or
            registration.get('reportsExit') is not True or child.poll() is not None):
        raise ValueError('No hay un anfitrión de prueba propio con confirmación de salida')
    stat = Path(f"/proc/{registration['pid']}/stat").read_text().rsplit(')', 1)[1].split()
    if int(stat[1]) != child.pid or stat[19] != registration['processStart']:
        raise ValueError('El anfitrión registrado pertenece a otro ensayo')
    receipt = session.command(registration, 'stop', timeout=2, exit_timeout=5)
    if child.wait(timeout=3) != 0:
        raise ValueError('El envoltorio de prueba no terminó limpiamente')
    return receipt


def measure_transition(fixtures, frames, snapshot, phase):
    outputs = by_description(snapshot)
    key = f'maximized{phase.capitalize()}'
    for output, fixture in fixtures.items():
        observed = fixture.measure(outputs[output], remaximize=False)
        frames[output][key + 'WithoutRemaximize'] = observed
        frames[output][key] = observed
    # Read every automatic result before invoking an explicit fallback on any window.
    for output, fixture in fixtures.items():
        if not frames[output][key]['matches']:
            frames[output]['remaximizedPhases'].append(phase)
            frames[output][key] = fixture.measure(outputs[output])


def run_trial(args, profile_edge, baseline=None):
    before = check.collect()
    report = {'version': 1, 'before': before, 'r4Complete': False, 'realAreaVerified': False,
              'requestedOutputs': args.output, 'requestedEdge': profile_edge or 'bottom',
              'previewExitVerified': False,
              'reservationDeltaVerified': False, 'maximizedWindowVerified': False,
              'binary': str(args.binary.resolve()), 'package': str(args.package.resolve())}
    child = None
    fixtures = {}
    frames = {}
    try:
        if before['status'] != 'access-ok-no-native-preview' or before.get('nativeLayers'):
            raise ValueError('Hace falta acceso a Hyprland y ninguna prueba R4 activa')
        before_outputs = by_description(before)
        if baseline is not None and before_outputs != baseline:
            raise ValueError('Cambió la geometría o la reserva inicial entre bordes')
        if not set(args.output) <= before_outputs.keys(): raise ValueError('Descripción de salida no encontrada o ambigua')
        config = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'illogical-impulse/config.json'
        if json.loads(config.read_text()).get('appearance', {}).get('bwmTheme') != 'plasma':
            raise ValueError('El ensayo requiere Breeze activo; no cambiará de skin automáticamente')
        if not args.binary.is_file() or not (args.package / 'metadata.json').is_file():
            raise ValueError('Falta binario o paquete de ensayo; revisar --binary/--package')
        if args.maximize:
            for output in args.output:
                maximized.useful_area(before_outputs[output])
        if args.refresh_area_watcher and baseline is None:
            print('Actualizando el puente de Breeze y esperando su observador de área útil.',flush=True)
            report['areaObserverReload']=maximized.refresh_area_observer()
        if args.maximize:
            report['dynamicMaximizedContract'] = 'panel-appearance-and-withdrawal'
            for output in args.output:
                frames[output] = {'remaximizedPhases': []}
                fixtures[output] = maximized.Fixture(args.binary, output)
                fixtures[output].start()
            for output, fixture in fixtures.items():
                frames[output]['maximizedBefore'] = fixture.measure(before_outputs[output])
        with ExitStack() as resources:
            log = resources.enter_context(tempfile.TemporaryFile(mode='w+'))
            argv = [sys.executable, str(ROOT / 'src/bwm-plasma-host/preview-isolated.py'),
                    '--binary', str(args.binary), '--follow-skin', '--native-policy']
            preview_env = dict(os.environ, QT_QPA_PLATFORM='wayland')
            if profile_edge is not None:
                root = Path(resources.enter_context(tempfile.TemporaryDirectory(prefix='bwm-r4-reservation-')))
                profile, data = prepare_profile(root, args.binary, args.package, args.output, profile_edge)
                report['fixturePanelCount'] = len(profile['panels'])
                argv.extend(['--profile', profile['directory']])
                preview_env['XDG_DATA_HOME'] = str(data)
            else:
                argv.extend(['--package', str(args.package), '--native-panel', '--layer-panel', '--output', args.output[0]])
            print(f'Midiendo la reserva del borde {profile_edge or "bottom"}. El ensayo se cerrará solo.', flush=True)
            try:
                # This opt-in session test requires real Wayland layer surfaces.
                # Do not inherit xcb/offscreen selection from a terminal's Qt env.
                child = subprocess.Popen(argv, stdout=log, stderr=log, start_new_session=True,
                                         env=preview_env)
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline and child.poll() is None:
                    snapshot = check.collect()
                    report['during'] = snapshot
                    runtime = snapshot.get('preview', {}).get('runtime', {})
                    if runtime.get('renderReady') is True and sum(l.get('namespace') == 'bwm-r4-native-policy' for l in snapshot.get('nativeLayers', [])) == len(args.output):
                        break
                    time.sleep(.15)
                else:
                    runtime = report.get('during', {}).get('preview', {}).get('runtime', {})
                    if any(p.get('status') == 'output-unavailable' for p in runtime.get('panels', [])):
                        raise ValueError('Qt no identifica la salida solicitada; revisar qtPlatform/availableOutputs en during.preview.runtime del informe')
                    raise TimeoutError('El panel no confirmó fotograma y capa a tiempo')
                # Wait for layer commits/arrangement after the first frame.
                time.sleep(.4)
                report['during'] = check.collect()
                if fixtures:
                    measure_transition(fixtures, frames, report['during'], 'during')
            finally:
                if child is not None:
                    try:
                        report['previewExitReceipt'] = confirm_fixture_exit(child)
                        report['previewExitVerified'] = True
                    except (OSError, ValueError, IndexError, TimeoutError, subprocess.SubprocessError) as exc:
                        report['previewStopError'] = str(exc)
                        stop_child(child)
                    finally:
                        report['previewExitCode'] = child.returncode
                        if not report['previewExitVerified']:
                            log.seek(0)
                            report['previewError'] = log.read()[-2000:]
        deadline = time.monotonic() + 5
        while True:
            after = check.collect()
            report['after'] = after
            if after.get('status') == 'access-ok-no-native-preview' and not after.get('nativeLayers'): break
            if time.monotonic() >= deadline: break
            time.sleep(.15)
        report.update(evaluate(before, report['during'], report['after'], args.output, profile_edge))
        if fixtures:
            measure_transition(fixtures, frames, report['after'], 'after')
            report['dynamicMaximizedWindowVerified'] = report['reservationDeltaVerified'] and all(
                frame['maximizedBefore']['matches'] and frame['maximizedDuringWithoutRemaximize']['matches'] and
                frame['maximizedAfterWithoutRemaximize']['matches'] for frame in frames.values())
            verified = report['reservationDeltaVerified'] and all(
                frame['maximizedBefore']['matches'] and frame['maximizedDuring']['matches'] and
                frame['maximizedAfter']['matches'] for frame in frames.values())
            report['maximizedWindowVerified'] = verified
            report['realAreaVerified'] = verified
            if not verified: report['errors'].append('El marco maximizado no coincide con el área útil observada')
        if not report['previewExitVerified']:
            report['reservationDeltaVerified'] = False
            report['maximizedWindowVerified'] = report['realAreaVerified'] = False
            report['dynamicMaximizedWindowVerified'] = False
            report['errors'].append('El auxiliar no confirmó el guardado y la salida')
    except (OSError, ValueError, KeyError, TypeError, TimeoutError, subprocess.SubprocessError, KeyboardInterrupt) as exc:
        report['errors'] = [str(exc) or 'Interrumpido por el usuario']
        report['reservationDeltaVerified'] = False
        report['maximizedWindowVerified'] = report['realAreaVerified'] = False
        report['dynamicMaximizedWindowVerified'] = False
        if child is not None and child.poll() is not None: report['after'] = check.collect()
        # A fixture failure must not erase an independently observed panel delta.
        if report['previewExitVerified'] and 'during' in report and 'after' in report:
            reservation = evaluate(before, report['during'], report['after'], args.output, profile_edge)
            report['reservationDeltaVerified'] = reservation['reservationDeltaVerified']
            report['reservationCheckErrors'] = reservation['errors']
    finally:
        for output, fixture in reversed(fixtures.items()):
            try:
                fixture.close()
                frames[output]['fixtureExitCode'] = fixture.child.returncode if fixture.child else None
            except (OSError, ValueError, subprocess.SubprocessError, KeyboardInterrupt) as exc:
                report.setdefault('errors', []).append(f'{output}: limpieza de ventana propia: {str(exc) or "interrumpida"}')
                report['maximizedWindowVerified'] = report['realAreaVerified'] = False
                report['dynamicMaximizedWindowVerified'] = False
        if frames:
            if len(args.output) == 1:
                report.update(frames[args.output[0]])
            else:
                report['maximizedByOutput'] = frames
    return report


def run_trials(args):
    edges = args.edge or ['bottom' if len(args.output) > 1 else None]
    if len(edges) == 1:
        return run_trial(args, edges[0])
    trials = []
    baseline = None
    for edge in edges:
        trial = run_trial(args, edge, baseline)
        trials.append(trial)
        if not trial['reservationDeltaVerified'] or (args.maximize and not trial['maximizedWindowVerified']):
            break
        if baseline is None:
            baseline = by_description(trial['before'])
    completed = len(trials) == len(edges)
    maximized_verified = args.maximize and completed and all(t['maximizedWindowVerified'] for t in trials)
    return {'version': 1, 'r4Complete': False, 'realAreaVerified': maximized_verified, 'requestedOutputs': args.output,
            'requestedEdges': edges, 'trials': trials,
            'reservationDeltaVerified': completed and all(t['reservationDeltaVerified'] for t in trials),
            'maximizedWindowVerified': maximized_verified,
            'dynamicMaximizedWindowVerified': args.maximize and completed and all(
                t.get('dynamicMaximizedWindowVerified', False) for t in trials),
            'errors': [f"{t['requestedEdge']}: {error}" for t in trials for error in t.get('errors', [])]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', help='Start and automatically close the isolated original KDE panels')
    parser.add_argument('--maximize', action='store_true', help='Measure an owned maximized window on each requested output against the real usable area')
    parser.add_argument('--refresh-area-watcher', action='store_true', help='Reload the existing Breeze bridge to enable automatic maximized-area tracking; requires --maximize')
    parser.add_argument('--output', action='append', required=True, help='Exact monitor description; repeat to test multiple outputs')
    parser.add_argument('--edge', action='append', choices=RESERVED_INDEX, help='Panel edge; repeat to run each edge in sequence')
    parser.add_argument('--binary', type=Path, default=ROOT / 'build/bwm-plasma-host/bwm-plasma-host')
    parser.add_argument('--package', type=Path, default=ROOT / 'src/bwm-plasma-host/tests/shared-config',
                        help='Disposable local fixture by default; --package accepts an explicitly selected original KDE package')
    parser.add_argument('--report', type=Path, default=Path(tempfile.gettempdir()) / f'bwm-r4-reservation-session-{os.getuid()}.json')
    args = parser.parse_args()
    if not args.run: parser.error('El ensayo exige --run; modifica temporalmente la reserva de las salidas elegidas')
    if args.refresh_area_watcher and not args.maximize:parser.error('--refresh-area-watcher requires --maximize')
    if len(set(args.output)) != len(args.output):parser.error('Cada salida debe indicarse una sola vez')
    if args.edge and len(set(args.edge)) != len(args.edge):parser.error('Cada borde debe indicarse una sola vez')
    report = run_trials(args)
    check.save_report(args.report, report)
    summary = {'reservationDeltaVerified': report['reservationDeltaVerified'],
               'maximizedWindowVerified': report['maximizedWindowVerified'],
               'dynamicMaximizedWindowVerified': report.get('dynamicMaximizedWindowVerified', False),
               'errors': report.get('errors', []), 'report': str(args.report), 'r4Complete': False}
    if 'trials' in report:
        summary['edges'] = {t['requestedEdge']: t['reservationDeltaVerified'] for t in report['trials']}
        if args.maximize:
            summary['maximizedEdges'] = {t['requestedEdge']: {
                'frameVerified': t['maximizedWindowVerified'],
                'dynamicVerified': t.get('dynamicMaximizedWindowVerified', False),
            } for t in report['trials']}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if report['reservationDeltaVerified'] and (not args.maximize or report['maximizedWindowVerified']) else 2


if __name__ == '__main__': raise SystemExit(main())
