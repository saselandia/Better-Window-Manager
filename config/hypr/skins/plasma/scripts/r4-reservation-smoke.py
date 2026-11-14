#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Explicit R4 reservation/own-window test, with optional existing bridge refresh."""
import argparse
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


def by_description(snapshot):
    result = {}
    for monitor in snapshot.get('monitors', []):
        description = monitor.get('description')
        if not description or description in result: raise ValueError('Descripción de salida ausente o ambigua')
        result[description] = monitor
    return result


def evaluate(before, during, after, description):
    """Validate the isolated bottom-panel delta; not a maximized-window test."""
    errors = []
    try:
        states = [by_description(s) for s in (before, during, after)]
        if any(set(s) != set(states[0]) for s in states) or description not in states[0]:
            raise ValueError('Las salidas cambiaron durante el ensayo')
        for output in states[0]:
            monitors = [s[output] for s in states]
            for key in ('x', 'y', 'width', 'height', 'scale', 'transform'):
                if any(m.get(key) != monitors[0].get(key) for m in monitors):
                    errors.append('Cambió geometría/escala durante el ensayo')
            if monitors[0]['reserved'] != monitors[2]['reserved']:
                errors.append('No se restauró la reserva original')
            if output != description and monitors[0]['reserved'] != monitors[1]['reserved']:
                errors.append('Cambió la reserva en una salida ajena')
        for s in (before, after):
            if s.get('status') != 'access-ok-no-native-preview' or s.get('nativeLayers'):
                errors.append('Ensayo previo existente o limpieza sin confirmar')
        runtime = during.get('preview', {}).get('runtime', {})
        panels = runtime.get('panels', [])
        if during.get('status') != 'observations-collected' or runtime.get('nativePanelPolicy') is not True or runtime.get('skin') != 'plasma' or len(panels) != 1:
            raise ValueError('No hay un único panel nativo activo confirmado')
        panel = panels[0]
        zone = panel.get('exclusiveZoneRequested')
        if type(zone) is not int or zone <= 0 or panel.get('reservationRequested') is not True or panel.get('renderReady') is not True or panel.get('outputDescription') != description:
            raise ValueError('El panel no confirmó salida, fotograma y petición de reserva')
        a, b = states[0][description], states[1][description]
        if b['reserved'] != [a['reserved'][0], a['reserved'][1], a['reserved'][2], a['reserved'][3] + zone]:
            errors.append('El incremento inferior no coincide con el grosor solicitado')
        layers = [l for l in during.get('nativeLayers', []) if l.get('namespace') == 'bwm-r4-native-policy']
        if len(layers) != 1 or layers[0].get('output') != b.get('name'):
            errors.append('No se confirma una única capa nativa en la salida elegida')
    except (ValueError, KeyError, TypeError, IndexError) as exc:
        errors.append(str(exc))
    return {'reservationDeltaVerified': not errors, 'maximizedWindowVerified': False,
            'realAreaVerified': False, 'r4Complete': False, 'errors': errors}


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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', help='Start and automatically close one isolated original KDE panel')
    parser.add_argument('--maximize', action='store_true', help='Also create one own window and measure BWM maximization against the real usable area')
    parser.add_argument('--refresh-area-watcher', action='store_true', help='Reload the existing Breeze bridge to enable automatic maximized-area tracking; requires --maximize')
    parser.add_argument('--output', required=True, help='Exact monitor description; never a connector name')
    parser.add_argument('--binary', type=Path, default=Path('/tmp/bwm-r4-panel-view-build/bwm-plasma-host'))
    parser.add_argument('--package', type=Path, default=Path('/tmp/bwm-r4-config-pages-upstream/libplasma-6.7.5/examples/applets/config'))
    parser.add_argument('--report', type=Path, default=Path(tempfile.gettempdir()) / f'bwm-r4-reservation-session-{os.getuid()}.json')
    args = parser.parse_args()
    if not args.run: parser.error('El ensayo exige --run; modifica temporalmente la reserva de la salida elegida')
    if args.refresh_area_watcher and not args.maximize:parser.error('--refresh-area-watcher requires --maximize')
    before = check.collect()
    report = {'version': 1, 'before': before, 'r4Complete': False, 'realAreaVerified': False,
              'reservationDeltaVerified': False, 'maximizedWindowVerified': False}
    child = None
    fixture = None
    try:
        if before['status'] != 'access-ok-no-native-preview' or before.get('nativeLayers'):
            raise ValueError('Hace falta acceso a Hyprland y ninguna prueba R4 activa')
        if args.output not in by_description(before): raise ValueError('Descripción de salida no encontrada o ambigua')
        config = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'illogical-impulse/config.json'
        if json.loads(config.read_text()).get('appearance', {}).get('bwmTheme') != 'plasma':
            raise ValueError('El ensayo requiere Breeze activo; no cambiará de skin automáticamente')
        if not args.binary.is_file() or not (args.package / 'metadata.json').is_file():
            raise ValueError('Falta binario o paquete de ensayo; revisar --binary/--package')
        if args.refresh_area_watcher:
            print('Actualizando el puente de Breeze y esperando su observador de área útil.',flush=True)
            report['areaObserverReload']=maximized.refresh_area_observer()
        if args.maximize:
            report['dynamicMaximizedContract'] = 'panel-appearance-and-withdrawal'
            target = by_description(before)[args.output]
            maximized.useful_area(target) # Reject unsupported scale/rotation before opening a fixture.
            fixture = maximized.Fixture(args.binary, args.output)
            fixture.start()
            report['maximizedBefore'] = fixture.measure(target)
        with tempfile.TemporaryFile(mode='w+') as log:
            argv = [sys.executable, str(ROOT / 'src/bwm-plasma-host/preview-isolated.py'),
                    '--binary', str(args.binary), '--package', str(args.package), '--native-panel', '--layer-panel',
                    '--follow-skin', '--native-policy', '--output', args.output]
            print('Midiendo la reserva antes/durante/después. El panel temporal se cerrará solo.', flush=True)
            try:
                # This opt-in session test requires real Wayland layer surfaces.
                # Do not inherit xcb/offscreen selection from a terminal's Qt env.
                child = subprocess.Popen(argv, stdout=log, stderr=log, start_new_session=True,
                                         env=dict(os.environ, QT_QPA_PLATFORM='wayland'))
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline and child.poll() is None:
                    snapshot = check.collect()
                    report['during'] = snapshot
                    runtime = snapshot.get('preview', {}).get('runtime', {})
                    if runtime.get('renderReady') is True and any(l.get('namespace') == 'bwm-r4-native-policy' for l in snapshot.get('nativeLayers', [])):
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
                if args.maximize:
                    target = by_description(report['during'])[args.output]
                    report['maximizedDuringWithoutRemaximize'] = fixture.measure(target, remaximize=False)
                    report['maximizedDuring'] = fixture.measure(target)
            finally:
                if child is not None: stop_child(child)
                if child is not None: report['previewExitCode'] = child.returncode
                # Preserve useful diagnostics even if startup raised an exception.
                log.seek(0)
                if report.get('previewExitCode') not in (0, 130) or not report.get('during', {}).get('preview', {}).get('runtime', {}).get('renderReady'):
                    report['previewError'] = log.read()[-2000:]
        deadline = time.monotonic() + 5
        while True:
            after = check.collect()
            report['after'] = after
            if after.get('status') == 'access-ok-no-native-preview' and not after.get('nativeLayers'): break
            if time.monotonic() >= deadline: break
            time.sleep(.15)
        report.update(evaluate(before, report['during'], report['after'], args.output))
        if fixture is not None:
            target = by_description(report['after'])[args.output]
            report['maximizedAfterWithoutRemaximize'] = fixture.measure(target, remaximize=False)
            report['dynamicMaximizedWindowVerified'] = (report['reservationDeltaVerified'] and
                report['maximizedBefore']['matches'] and report['maximizedDuringWithoutRemaximize']['matches'] and
                report['maximizedAfterWithoutRemaximize']['matches'])
            report['maximizedAfter'] = fixture.measure(target)
            verified = (report['reservationDeltaVerified'] and report['maximizedBefore']['matches'] and
                        report['maximizedDuring']['matches'] and report['maximizedAfter']['matches'])
            report['maximizedWindowVerified'] = verified
            report['realAreaVerified'] = verified
            if not verified: report['errors'].append('El marco maximizado no coincide con el área útil observada')
        if report.get('previewExitCode') not in (0, 130):
            report['reservationDeltaVerified'] = False
            report['maximizedWindowVerified'] = report['realAreaVerified'] = False
            report['dynamicMaximizedWindowVerified'] = False
            report['errors'].append('El auxiliar no terminó limpiamente')
    except (OSError, ValueError, TimeoutError, subprocess.SubprocessError, KeyboardInterrupt) as exc:
        report['errors'] = [str(exc) or 'Interrumpido por el usuario']
        report['reservationDeltaVerified'] = False
        report['maximizedWindowVerified'] = report['realAreaVerified'] = False
        report['dynamicMaximizedWindowVerified'] = False
        if child is not None and child.poll() is not None: report['after'] = check.collect()
        # A fixture failure must not erase an independently observed panel delta.
        if report.get('previewExitCode') in (0, 130) and 'during' in report and 'after' in report:
            reservation = evaluate(before, report['during'], report['after'], args.output)
            report['reservationDeltaVerified'] = reservation['reservationDeltaVerified']
            report['reservationCheckErrors'] = reservation['errors']
    finally:
        if fixture is not None:
            try:
                fixture.close()
                report['fixtureExitCode'] = fixture.child.returncode if fixture.child else None
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                report.setdefault('errors', []).append('Limpieza de ventana propia: ' + str(exc))
                report['maximizedWindowVerified'] = report['realAreaVerified'] = False
                report['dynamicMaximizedWindowVerified'] = False
        check.save_report(args.report, report)
    print(json.dumps({'reservationDeltaVerified': report['reservationDeltaVerified'],
                      'maximizedWindowVerified': report['maximizedWindowVerified'],
                      'dynamicMaximizedWindowVerified': report.get('dynamicMaximizedWindowVerified', False),
                      'errors': report.get('errors', []), 'report': str(args.report), 'r4Complete': False}, ensure_ascii=False, indent=2))
    return 0 if report['reservationDeltaVerified'] and (not args.maximize or report['maximizedWindowVerified']) else 2


if __name__ == '__main__': raise SystemExit(main())
