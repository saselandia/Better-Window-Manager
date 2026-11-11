#!/usr/bin/env python3
"""Read-only F7 audit. App-name patterns label test rows; they NEVER decide decorations."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

APPS = [
    ('kitty', r'^kitty$', 'SSD (decoraciones habilitadas)'),
    ('Firefox', r'firefox', 'CSD; SSD si se activa barra del sistema'),
    ('Nautilus', r'nautilus', 'CSD (libadwaita, sin negociación)'),
    ('Dolphin', r'dolphin', 'SSD (Qt)'),
    ('Steam', r'^steam', 'CSD si Motif decorations=0'),
    ('Vesktop', r'vesktop', 'CSD; probar también barra del sistema'),
    ('Stremio', r'stremio', 'CSD (GTK4 en este equipo)'),
    ('Signal', r'signal', 'CSD; probar también barra del sistema'),
    ('Krita', r'krita', 'SSD (Qt Widgets)'),
    ('Claude', r'claude', 'CSD (Electron)'),
    ('VS Code / Codium', r'(^code$|codium|visual.studio.code)', 'CSD; probar también barra del sistema'),
    ('Kate flatpak', r'(^kate$|org.kde.kate)', 'SSD (verificar instancia flatpak)'),
    ('Qt Widgets (qt6ct/designer)', r'(qt6ct|designer|qdbusviewer|assistant)', 'SSD'),
    ('xterm / xeyes XWayland', r'^(xterm|xeyes)$', 'SSD, sin hints CSD'),
]

def assess(record):
    o = record.get('observed', {})
    if not record.get('ready'):
        return 'En transición / sin confirmar'
    suppressed = o.get('noBar') or not o.get('decorate', True) or o.get('fullscreen')
    requested = record.get('xdgRequested') if o.get('xdg') else record.get('kdeRequested')
    if o.get('x11'):
        expected = not (suppressed or o.get('special') or o.get('gtkFrameExtents') or o.get('motifNoBorder'))
    elif o.get('xdg'):
        mode = 2 if suppressed or requested != 1 else 1
        if record.get('sent') != mode:
            return 'FALLO: respuesta xdg incoherente'
        if record.get('applied') != mode:
            return 'En transición / falta ack+commit'
        expected = not suppressed and mode == 2
    elif o.get('kde'):
        mode = 0 if suppressed else requested if o.get('kdeExplicit') else 2
        if record.get('sent') != mode:
            return 'FALLO: respuesta KDE incoherente'
        if record.get('applied') != mode:
            return 'En transición / falta commit'
        expected = not suppressed and mode == 2
    else:
        expected = False
    return 'OK (datos; comprobar visualmente)' if record.get('visible') is expected else 'FALLO: barra distinta de lo negociado'

def clean(text):
    return str(text).replace('|', '/').replace('\n', ' ').replace('\r', ' ')

def report(snapshot):
    lines = ['# Matriz CSD de Breeze — F7', '',
             'Lectura del plugin activo. «OK» comprueba los datos; la inspección visual sigue siendo necesaria.',
             'Las preferencias de cada app, fullscreen y overrides tienen prioridad sobre el caso nominal.', '',
             '| App / caso | Esperado nominal | PID / protocolo / barra / bordes | Resultado |',
             '| --- | --- | --- | --- |']
    for name, pattern, expected in APPS:
        matches = [w for w in snapshot['windows'] if re.search(pattern, w.get('class', ''), re.I)]
        if not matches:
            lines.append(f'| {name} | {expected} | — | No observada |')
            continue
        for window in matches:
            o = window.get('observed', {})
            protocol = 'XWayland' if o.get('x11') else 'xdg' if o.get('xdg') else 'KDE' if o.get('kde') else 'sin protocolo'
            borders = window.get('borders', {})
            frame = ','.join(str(borders.get(e, 0)) for e in ['left', 'top', 'right', 'bottom'])
            value = f'{window["pid"]} / {protocol} / {"SSD" if window.get("visible") else "sin barra"} / {frame}'
            lines.append(f'| {name} | {expected} | {clean(value)} | {clean(assess(window))} |')
    lines += ['', 'Repetir tras cambiar CSD/SSD en Firefox/Chromium/Electron, salir de fullscreen,',
              'y crear/quitar hints Motif/GTK en ventanas X11 de prueba. No ejecutar cargas/descargas del plugin en caliente.', '']
    return '\n'.join(lines)

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, help='JSON guardado del diagnóstico F7 (no toca Hyprland)')
    parser.add_argument('--output', type=Path, help='Guardar la tabla Markdown en esta ruta')
    args = parser.parse_args(argv)
    try:
        if args.snapshot:
            raw = args.snapshot.read_text()
        else:
            result = subprocess.run(['hyprctl', '-j', 'breezebars-csd'], capture_output=True, text=True, timeout=3)
            raw = result.stdout
        data = json.loads(raw)
        if data.get('api') != 'breezebars-csd' or data.get('version') != 1 or not isinstance(data.get('windows'), list):
            raise ValueError('API F7 ausente')
        if not data.get('enabled'):
            raise ValueError('Breeze está inactiva')
    except (OSError, ValueError, AttributeError, subprocess.SubprocessError) as error:
        print(f'F7 aún no verificable: {error}. Reinicia sesión entrando en Breeze; no cargues el plugin en caliente.', file=sys.stderr)
        return 2
    text = report(data)
    if args.output:
        args.output.write_text(text)
    else:
        print(text, end='')
    return int(any(assess(w).startswith('FALLO') for w in data['windows']))

if __name__ == '__main__':
    raise SystemExit(main())
