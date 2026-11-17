# SPDX-License-Identifier: GPL-2.0-or-later
"""Restore only launcher-relevant caller environment outside the disposable host."""
import json
import os
from pathlib import Path

KEYS = ('XDG_CONFIG_HOME', 'XDG_CONFIG_DIRS', 'XDG_DATA_HOME', 'XDG_DATA_DIRS',
        'XDG_CACHE_HOME', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS',
        'QT_QPA_PLATFORM', 'QT_QPA_PLATFORMTHEME', 'QT_QUICK_BACKEND', 'QT_PLUGIN_PATH',
        'QML_IMPORT_PATH', 'QML2_IMPORT_PATH', 'WAYLAND_DISPLAY', 'KDESYCOCA',
        'QT_WAYLAND_DISABLE_FIXED_POSITIONS')
VARIABLE = 'BWM_R4_LAUNCH_CONTEXT'


def capture(environment):
    return json.dumps({'version': 1, 'values': {key: environment.get(key) for key in KEYS}},
                      ensure_ascii=True, separators=(',', ':'))


def restore(environment):
    raw = environment.get(VARIABLE, '')
    if len(raw) > 131072:
        raise ValueError('Launch context exceeds limit')
    context = json.loads(raw)
    if (not isinstance(context, dict) or type(context.get('version')) is not int
            or context['version'] != 1 or not isinstance(context.get('values'), dict)
            or set(context['values']) != set(KEYS)):
        raise ValueError('Missing or invalid caller launch context')
    result = dict(environment)
    for key, value in context['values'].items():
        if value is None:
            result.pop(key, None)
        elif isinstance(value, str) and '\0' not in value:
            result[key] = value
        else:
            raise ValueError('Invalid launch environment value')
    for key in tuple(result):
        if key.startswith('BWM_R4_') or key in ('BWM_SKIN_SWITCH', 'WAYLAND_SOCKET'):
            result.pop(key, None)
    return result


HOST_POLICY = ('# Written by BWM for one disposable Plasma host; removed with its roots.\n'
               '# KDE KIOSK: KIO ApplicationLauncherJob/OpenUrlJob check run_desktop_files and\n'
               '# command launches check shell_access before spawning. Applications must\n'
               '# leave through the BWM launch helper with the restored caller environment.\n'
               '[KDE Action Restrictions][$i]\nrun_desktop_files=false\nshell_access=false\n')


def write_host_policy(config_dirs_root):
    """Deny in-process desktop launches for a host whose XDG_CONFIG_DIRS is this
    disposable directory. Immutable, so the host's own kdeglobals cannot lift it."""
    root = Path(config_dirs_root)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise ValueError('Host policy needs an existing private configuration directory')
    target = root/'kdeglobals'
    if target.exists() or target.is_symlink():
        raise ValueError('Host policy target already exists')
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    with os.fdopen(fd, 'w') as handle:
        handle.write(HOST_POLICY)


PLACES = 'user-places.xbel'


def snapshot_places(original_data_home, host_data_root, limit=1048576):
    """Read-only copy of the caller's KDE places (XBEL, KFilePlacesModel format) for
    the disposable host, so the task menu shows the user's own Places. Writes go to
    the copy and vanish with the host; the original is never opened for writing."""
    source = Path(original_data_home)/PLACES
    target = Path(host_data_root)/PLACES
    if not Path(host_data_root).is_dir() or target.exists() or target.is_symlink():
        raise ValueError('Places snapshot needs a fresh private data directory')
    try:
        fd = os.open(source, os.O_RDONLY | os.O_CLOEXEC)
    except FileNotFoundError:
        return False  # KDE creates its defaults in the disposable copy.
    with os.fdopen(fd, 'rb') as handle:
        if not os.path.isfile(f'/proc/self/fd/{handle.fileno()}'):
            raise ValueError('Places file is not a regular file')
        data = handle.read(limit+1)
    if len(data) > limit:
        raise ValueError('Places file exceeds limit')
    out = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    with os.fdopen(out, 'wb') as handle:
        handle.write(data)
    return True
