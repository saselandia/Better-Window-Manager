#!/usr/bin/env python3
"""Read active bindings for Retro's Omarchy-style searchable keybindings menu.

The source is compositor state, not Omarchy's default shortcuts. Lua dispatchers
are resolved from BWM's generated source without executing configuration files.
"""
import json
from pathlib import Path
import re
import subprocess
import sys

MODIFIERS = [(64, 'SUPER'), (4, 'CTRL'), (8, 'ALT'), (1, 'SHIFT'), (2, 'CAPS'), (16, 'MOD2'), (32, 'MOD3'), (128, 'MOD5')]
KEY_NAMES = {'RETURN':'ENTER', 'SPACE':'SPACE', 'BACKSPACE':'BACKSPACE', 'GRAVE':'`',
             'LEFT':'←', 'RIGHT':'→', 'UP':'↑', 'DOWN':'↓', 'MOUSE:272':'LEFT MOUSE',
             'MOUSE:273':'RIGHT MOUSE', 'MOUSE:274':'MIDDLE MOUSE', 'SUPER_L':'SUPER', 'SUPER_R':'SUPER'}
STRING = r'"(?:\\.|[^"\\])*"'


def parse_plain(text):
    """Fallback for compositor versions whose JSON binds response is malformed."""
    rows, row = [], None
    for line in text.splitlines():
        if line.startswith('bind'):
            if row is not None:
                rows.append(row)
            row = {}
        elif row is not None and line.startswith('\t') and ': ' in line:
            key, value = line.strip().split(': ', 1)
            row[key] = int(value) if key in ('modmask', 'keycode') and value.isdigit() else (value == 'true') if value in ('true', 'false') else value
    if row is not None:
        rows.append(row)
    return rows


def active_bindings():
    try:
        data = json.loads(subprocess.check_output(['hyprctl', 'binds', '-j'], text=True))
        if isinstance(data, list):
            return data
    except (ValueError, subprocess.CalledProcessError):
        pass
    return parse_plain(subprocess.check_output(['hyprctl', 'binds'], text=True))


def lua_actions(source):
    """Only literal descriptions and single-line hl.dsp expressions; no Lua eval."""
    actions = {}
    for line in source.splitlines():
        match = re.search(r'hl\.bind\(.*?,\s*(hl\.dsp\..*),\s*\{\s*description\s*=\s*(' + STRING + r')', line)
        if not match:
            continue
        try:
            description = json.loads(match[2])
        except ValueError:
            continue
        expression = match[1].replace('mode = fullscreen_mode', 'mode = 0')
        # Different actions sharing a description must never dispatch arbitrarily.
        actions.setdefault(description, set()).add(expression)
    return {name: next(iter(values)) for name, values in actions.items() if len(values) == 1}


def records(bindings, actions):
    rows, seen = [], set()
    for bind in bindings:
        description = str(bind.get('description') or '').strip()
        if not description:
            continue  # helper releases and anonymous implementation bindings
        key = str(bind.get('key') or '').rsplit(' + ', 1)[-1].upper()
        if not key and bind.get('keycode'):
            key = 'code:' + str(bind['keycode'])
        if not key:
            continue
        mods = [name for bit, name in MODIFIERS if int(bind.get('modmask', 0)) & bit]
        display_key = KEY_NAMES.get(key, key)
        if display_key not in mods:
            mods.append(display_key)
        chord = ' + '.join(mods)
        submap = str(bind.get('submap') or '')
        action = description.split(': ', 1)[-1]
        label = f'{chord:<30} → {action}' + (f' [{submap}]' if submap else '')
        dispatcher, arg = bind.get('dispatcher', ''), str(bind.get('arg') or '')
        command = []
        if dispatcher == '__lua':
            expression = actions.get(description)
            if expression and not bind.get('mouse') and 'hl.dsp.window.drag(' not in expression and 'hl.dsp.window.resize(' not in expression:
                command = ['hyprctl', 'dispatch', expression]
        elif dispatcher and not bind.get('mouse'):
            command = ['hyprctl', 'dispatch', dispatcher, arg]
        identity = (label, dispatcher, arg)
        if identity in seen:
            continue
        seen.add(identity)
        # Keep shortcuts usable in the compositor but not dispatchable from a menu
        # (mouse gestures and user callbacks) available as reference too.
        rows.append({'label': label, 'command': command, 'description': description})
    rows.sort(key=lambda r: (0 if 'Cheatsheet' in r['description'] else 1 if r['description'].startswith('Lanzadores:') else 2, r['description'].casefold(), r['label']))
    return rows


def main():
    source = Path.home() / '.config/hypr/modules/user_binds.lua'
    actions = lua_actions(source.read_text()) if source.exists() else {}
    rows = records(active_bindings(), actions)
    if '--print' in sys.argv or '-p' in sys.argv:
        print('\n'.join(row['label'] for row in rows))
    else:
        print(json.dumps(rows, ensure_ascii=False))


if __name__ == '__main__':
    main()
