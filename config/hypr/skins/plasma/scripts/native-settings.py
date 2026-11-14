#!/usr/bin/env python3
"""R3 native KCM adapter. Schema is UI transport, never another settings store.

Only allowlisted fields are accepted. Apply compares the reopened page before calling the
shared controllers. Partial controller failures are errors, never successful saves.
"""
import hashlib
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

SCRIPTS = Path(__file__).resolve().parents[3] / 'scripts'
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))


def command(script, *args):
    result = subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)],
                            capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise ValueError(result.stderr.strip() or result.stdout.strip() or 'Falló el gestor BWM')
    # Some managers include diagnostics before their final JSON response.
    try:
        data = json.loads(result.stdout)
    except ValueError:
        data = None
        for line in reversed(result.stdout.splitlines()):
            try:
                data = json.loads(line)
                break
            except ValueError:
                pass
    if isinstance(data, dict) and (data.get('success') is False or data.get('status') == 'error'):
        raise ValueError(data.get('message', 'Falló el gestor BWM'))
    return data


def bridge():
    spec = importlib.util.spec_from_file_location('native_bridge', Path(__file__).with_name('kde-config-bridge.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


WINDOW_FIELDS = [
    ('kwinrc', 'Windows', 'FocusPolicy', 'Foco', 'focus', 'choice', {'choices': [dict(label='Clic para enfocar', value='ClickToFocus'), dict(label='Seguir ratón (aproximación Hyprland)', value='FocusFollowsMouse')]}),
    ('kwinrc', 'Windows', 'Placement', 'Colocación', 'placement', 'choice', {'choices': [dict(label=x, value=x) for x in ['Smart', 'Centered', 'ZeroCornered', 'UnderMouse', 'Random', 'Maximizing', 'NoPlacement']]}),
    ('kdeglobals', 'KDE', 'AnimationDurationFactor', 'Factor de duración (0 = desactivadas; efectos en R7)', 'animationFactor', 'real', dict(min=0, max=20)),
]
DECOR_FIELDS = [
    ('kwinrc', 'Windows', 'TitlebarDoubleClickCommand', 'Doble clic en barra del servidor', 'doubleClick', 'choice', {'choices': [dict(label=x, value=x) for x in ['Maximize', 'Maximize (vertical only)', 'Maximize (horizontal only)', 'Minimize', 'Close', 'Nothing']]}),
]
SNAP_FIELDS = [
    ('kwinrc', 'Windows', key, label, setting, 'int', dict(min=0, max=1000))
    for key, label, setting in [('BorderSnapZone', 'Encaje con pantalla (px)', 'borderSnap'), ('WindowSnapZone', 'Encaje con ventanas (px)', 'windowSnap'), ('CenterSnapZone', 'Encaje con centro (px)', 'centerSnap')]
]


def field(key, label, value, kind='text', **extra):
    return dict(key=key, label=label, value=value, type=kind, **extra)


def page(category):
    fields = []
    if category == 'windows':
        b = bridge()
        if not b.active():
            raise ValueError('El comportamiento propio de Breeze sólo se edita con Breeze activo')
        version = b.run(['hyprctl', '-j', 'version'])
        if version.returncode:
            raise ValueError('No hay acceso al compositor; no se ofrecen controles de ventanas sin aplicación')
        settings = b.kwin_settings()
        plugins = b.run(['hyprctl', '-j', 'plugins'])
        definitions = WINDOW_FIELDS + (SNAP_FIELDS + DECOR_FIELDS if plugins.returncode == 0 and 'breezebars' in plugins.stdout else [])
        for file, group, key, label, setting, kind, extra in definitions:
            value = settings[setting]
            extra = dict(extra)
            if kind == 'choice' and value not in [c['value'] for c in extra['choices']]:
                extra['choices'] = extra['choices'] + [dict(label='Actual (sin equivalencia exacta): ' + str(value), value=value)]
            fields.append(field(file + '\x1f' + group + '\x1f' + key, label, value, kind, **extra))
    elif category == 'cursor':
        current = command('cursor-manager.py', 'get')
        themes = command('cursor-manager.py', 'list')
        choices = [dict(label=t['name'], value=t['id']) for t in themes]
        if current['theme'] not in [c['value'] for c in choices]:
            choices.append(dict(label=current['theme'], value=current['theme']))
        fields = [field('theme', 'Tema', current['theme'], 'choice', choices=choices),
                  field('size', 'Tamaño (px)', current['size'], 'int', min=16, max=96)]
    elif category == 'apps':
        data = command('default-apps.py', 'list')
        for key, label in [('terminal', 'Terminal'), ('browser', 'Navegador'), ('files', 'Archivos'),
                           ('editor', 'Editor'), ('taskmanager', 'Monitor del sistema')]:
            info = data[key]
            choices = [dict(label=o['name'], value=o['id']) for o in info['options']]
            if info['current'] not in [c['value'] for c in choices]:
                choices.append(dict(label=info['current'], value=info['current']))
            fields.append(field(key, label, info['current'], 'choice', choices=choices))
    elif category in ('screens', 'workspaces'):
        monitors = command('monitor-manager.py', 'list')
        if not monitors:
            raise ValueError('No se pudieron consultar las pantallas; no se ofrecen valores ficticios')
        for m in monitors:
            desc = m['description']
            if not desc:
                continue  # Never persist connector identities.
            prefix = desc + '\x1f'
            if category == 'screens':
                for key, label, kind, extra in [('scale', 'Escala', 'real', dict(min=0.5, max=4)),
                        ('x', 'Posición X', 'int', dict(min=-32768, max=32768)),
                        ('y', 'Posición Y', 'int', dict(min=-32768, max=32768)),
                        ('transform', 'Giro (0–3)', 'int', dict(min=0, max=3))]:
                    fields.append(field(prefix + key, desc + ' — ' + label, m[key], kind, **extra))
            else:
                fields.append(field(prefix + 'workspaces', desc + ' — escritorios (ej. 1-9)', m['workspaces']))
    elif category == 'startup':
        for entry in command('autostart-manager.py', 'list'):
            fields.append(field(entry['file'], entry['name'], entry['enabled'], 'bool'))
    elif category == 'shortcuts':
        for entry in command('keybinds-manager.py', 'list'):
            if entry.get('skins') and 'plasma' not in entry['skins']:
                continue
            fields.append(field(entry['id'], entry['description'],
                                ' + '.join(entry.get('mods', []) + [entry['key']])))
    elif category == 'energy':
        data = json.loads((CONFIG / 'illogical-impulse/config.json').read_text())
        for key, label, default, maximum in [('screen', 'Apagar pantallas (s; 0 = nunca)', 300, 7200),
                ('lock', 'Bloquear (s; 0 = nunca)', 600, 7200),
                ('suspend', 'Suspender (s; 0 = nunca)', 0, 14400)]:
            fields.append(field(key, label, data.get('idle', {}).get(key, default), 'int', min=0, max=maximum))
    else:
        raise ValueError('Módulo desconocido')
    revision = hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest()
    return dict(fields=fields, revision=revision)


def combination(value):
    parts = [s.strip() for s in value.split('+')]
    aliases = {'SUPER': 'SUPER', 'CTRL': 'CTRL', 'CONTROL': 'CTRL', 'ALT': 'ALT', 'SHIFT': 'SHIFT'}
    if not parts[-1] or any(p.upper() not in aliases for p in parts[:-1]):
        raise ValueError('Atajo no válido')
    return ','.join(dict.fromkeys(aliases[p.upper()] for p in parts[:-1])), parts[-1]


def apply(category, request):
    current = page(category)
    if current['revision'] != request.get('revision'):
        raise ValueError('La configuración cambió desde que se abrió; pulsa Restablecer y revisa los cambios')
    specs = {f['key']: f for f in current['fields']}
    changes = request.get('changes')
    if not isinstance(changes, dict) or not changes.keys() <= specs.keys():
        raise ValueError('Claves no admitidas')
    # Validate the entire batch before any write.
    for key, value in changes.items():
        spec = specs[key]
        kind = spec['type']
        if kind in ('int', 'real'):
            if type(value) not in ((int,) if kind == 'int' else (int, float)) or not spec['min'] <= value <= spec['max']:
                raise ValueError('Número fuera de rango')
        elif kind == 'bool':
            if type(value) is not bool:
                raise ValueError('Se esperaba un booleano')
        elif not isinstance(value, str) or '\n' in value or '\0' in value:
            raise ValueError('Texto no válido')
        if kind == 'choice' and value not in [c['value'] for c in spec['choices']]:
            raise ValueError('Opción no disponible')
        if category == 'shortcuts':
            combination(value)
        if category == 'workspaces':
            # Same parser as monitor-manager, before applying any monitor.
            import re
            if not re.fullmatch(r'\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*', value):
                raise ValueError('Lista de escritorios no válida')
    changes = {k: v for k, v in changes.items() if specs[k]['value'] != v}
    if category == 'windows' and changes:
        b = bridge()
        for file in ('kwinrc', 'kdeglobals'):
            updates = {}
            for ident, value in changes.items():
                target, group, key = ident.split('\x1f')
                if target == file:
                    updates[group, key] = str(value)
            if updates:
                path = CONFIG / file
                text = b.read(path)
                if b.atomic(path, b.patch_ini(text, updates), text):
                    b.notify(file, updates)
        b.reconcile()
    elif category == 'cursor' and changes:
        values = {k: f['value'] for k, f in specs.items()} | changes
        command('cursor-manager.py', 'apply', values['theme'], values['size'])
    elif category in ('screens', 'workspaces') and changes:
        monitors = command('monitor-manager.py', 'list')
        for m in monitors:
            for k in ('scale', 'x', 'y', 'transform', 'workspaces'):
                key = m['description'] + '\x1f' + k
                if key in changes:
                    m[k] = changes[key]
        command('monitor-manager.py', 'apply', json.dumps(monitors))
    elif category == 'apps':
        for key, value in changes.items():
            command('default-apps.py', 'set', key, value)
    elif category == 'startup':
        for key, value in changes.items():
            command('autostart-manager.py', 'toggle', key, str(value).lower())
    elif category == 'shortcuts':
        for key, value in changes.items():
            mods, bind_key = combination(value)
            command('keybinds-manager.py', 'update', '--id', key, '--mods', mods, '--key', bind_key)
    elif category == 'energy' and changes:
        command('bwm-shared-settings.py', 'idle', json.dumps(changes))
    reopened = page(category)
    values = {f['key']: f['value'] for f in reopened['fields']}
    if any(values.get(k) != v for k, v in changes.items()):
        raise ValueError('El gestor no confirmó la lectura posterior. Puede haber cambios parciales; pulsa Restablecer')
    return reopened


def main():
    try:
        category, action = sys.argv[1:3]
        if action == 'load':
            result = page(category)
        elif action == 'save':
            state = Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state')) / 'bwm/plasma'
            state.mkdir(parents=True, exist_ok=True)
            with open(state / 'native-settings.lock', 'a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                result = apply(category, json.load(sys.stdin))
        else:
            result = None
        if result is None:
            raise ValueError('Acción desconocida')
        print(json.dumps(result, ensure_ascii=False))
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(json.dumps(dict(error=str(exc)), ensure_ascii=False))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
