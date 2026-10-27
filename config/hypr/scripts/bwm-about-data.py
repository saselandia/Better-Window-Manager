#!/usr/bin/env python3
"""Real BWM metadata for the Omarchy-style Fastfetch presentation."""
from datetime import datetime
import json
import socket
from pathlib import Path
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[3]
STATE = Path.home() / '.local/state/bwm/omarchy'


def git(*args):
    try:
        return subprocess.check_output(['git', '-C', str(REPO), *args], text=True,
                                       stderr=subprocess.DEVNULL, timeout=2).strip()
    except (OSError, subprocess.SubprocessError):
        return ''


def read(path, fallback=''):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return fallback


def duration(seconds):
    minutes = max(0, int(seconds)) // 60
    days, minutes = divmod(minutes, 1440)
    hours, minutes = divmod(minutes, 60)
    return f'{days}d {hours}h' if days else (f'{hours}h {minutes}m' if hours else f'{minutes}m')


def value(field):
    if field == 'host':
        for name in ('product_name', 'product_family'):
            product = read('/sys/class/dmi/id/' + name)
            if product and product.lower() not in ('to be filled by o.e.m.', 'default string', 'system product name'):
                return product
        return socket.gethostname()
    if field == 'revision':
        branch, revision = git('branch', '--show-current'), git('rev-parse', '--short', 'HEAD')
        return ' · '.join(part for part in (branch, revision) if part) or 'BWM'
    if field == 'wm':
        try:
            running = json.loads(subprocess.check_output(['hyprctl', 'version', '-j'],
                                 text=True, stderr=subprocess.DEVNULL, timeout=2))
            version = running.get('version') or str(running.get('tag', '')).removeprefix('v')
            return 'Hyprland' + (f' {version}' if version else '') + ' (Wayland)'
        except (OSError, ValueError, subprocess.SubprocessError):
            return 'Hyprland (Wayland)'
    if field == 'skin':
        try:
            config = json.loads((Path.home() / '.config/illogical-impulse/config.json').read_text())
            skin = config.get('appearance', {}).get('bwmTheme', 'retro')
        except (OSError, ValueError):
            skin = 'retro'
        return {'retro': 'Retro (Omarchy)', 'default': 'Default (Material You)',
                'plasma': 'KDE Plasma'}.get(skin, skin)
    if field == 'theme':
        name = read(STATE / 'theme.name', 'dynamic')
        return 'Dynamic' if read(STATE / 'theme.mode') == 'dynamic' else name.replace('-', ' ').title()
    if field == 'uptime':
        return duration(float(read('/proc/uptime', '0').split()[0]))
    if field == 'age':
        try:
            birth = int(subprocess.check_output(['stat', '-c', '%W', '/'], text=True).strip())
            return f'{max(0, int((time.time() - birth) // 86400))} days' if birth > 0 else '—'
        except (OSError, ValueError, subprocess.SubprocessError):
            return '—'
    if field == 'update':
        # Gentoo's newest recorded package build/install, not an invented world-update date.
        timestamps = []
        for path in Path('/var/db/pkg').glob('*/*/BUILD_TIME'):
            try:
                timestamps.append(int(path.read_text().strip()))
            except (OSError, ValueError):
                pass
        if timestamps:
            return datetime.fromtimestamp(max(timestamps)).strftime('%Y-%m-%d %H:%M')
        return '—'
    raise ValueError(f'Unknown field: {field}')


if __name__ == '__main__':
    print(value(sys.argv[1]))
