#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""T7 native KNS probes. Read-only host filesystem, writable disposable roots only.

KNS dependencies create their own engines: changing xcursor.knsrc in the parent
engine does not redirect them. Bind the legacy ~/.icons destination to private
data/icons too. HOME itself is never changed. This is filesystem containment,
not permission to execute an unreviewed widget or downloaded binary.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

PROVIDERS = ('lookandfeel', 'plasma-themes', 'colorschemes', 'aurorae',
             'window-decorations', 'icons', 'xcursor', 'plasmoids')


def private_root(path):
    path = Path(path).resolve(strict=True)
    if not path.is_relative_to(Path(tempfile.gettempdir()).resolve()) or path == Path(tempfile.gettempdir()):
        raise ValueError('Existing disposable directory under the temporary directory required')
    if path.stat().st_uid != os.getuid() or path.stat().st_mode & 0o077:
        raise ValueError('Disposable directory must be owned by this user, mode 0700')
    return path


def environment(item):
    item = private_root(item)
    env = {k: v for k, v in os.environ.items() if not k.startswith(('XDG_', 'QT_', 'DBUS_', 'BWM_'))
           and k not in ('WAYLAND_DISPLAY', 'WAYLAND_SOCKET', 'DISPLAY', 'HYPRLAND_INSTANCE_SIGNATURE')}
    for variable, directory in [('CONFIG_HOME', 'config'), ('DATA_HOME', 'data'), ('CACHE_HOME', 'cache'),
                                ('RUNTIME_DIR', 'runtime'), ('STATE_HOME', 'state'), ('CONFIG_DIRS', 'defaults')]:
        (item / directory).mkdir(mode=0o700, exist_ok=True)
        env['XDG_' + variable] = str(item / directory)
    (item / 'data/icons').mkdir(exist_ok=True)
    env.update(XDG_DATA_DIRS='/usr/local/share:/usr/share', QT_QPA_PLATFORM='offscreen',
               QT_QPA_PLATFORMTHEME='', QT_QUICK_BACKEND='software',
               DBUS_SESSION_BUS_ADDRESS='unix:path=' + str(item / 'no-bus'),
               DBUS_SYSTEM_BUS_ADDRESS='unix:path=' + str(item / 'no-system-bus'))
    return env


def sandbox(work, item, argv):
    work, item = private_root(work), private_root(item)
    if not item.is_relative_to(work):
        raise ValueError('Item must belong to the disposable work directory')
    return ['/usr/bin/bwrap', '--ro-bind', '/', '/', '--tmpfs', '/tmp',
            '--bind', str(work), str(work), '--bind', str(item / 'data/icons'), str(Path.home() / '.icons'),
            '--proc', '/proc', '--dev', '/dev', '--unshare-pid', '--die-with-parent', '--new-session', *map(str, argv)]


def invoke(work, item, binary, provider, command, value='', page=0):
    env = environment(item)
    argv = [Path(binary).resolve(), provider, command, value]
    if command == 'search':
        argv.append(str(page))
    reply = subprocess.run(sandbox(work, item, argv), env=env, capture_output=True, text=True, timeout=180)
    (item / (command + '.log')).write_text(reply.stderr)
    data = json.loads(reply.stdout)
    (item / (command + '.json')).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    return data, reply.returncode


def tree_hash(root):
    digest = hashlib.sha256()
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            digest.update(str(path.relative_to(root)).encode() + b'\0link\0' + os.readlink(path).encode())
        elif path.is_file():
            digest.update(str(path.relative_to(root)).encode() + b'\0file\0' + path.read_bytes())
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--provider', choices=PROVIDERS, required=True)
    parser.add_argument('--id', default='')
    parser.add_argument('--page', type=int, default=0)
    parser.add_argument('command', choices=('search', 'metadata', 'install', 'uninstall'))
    args = parser.parse_args()
    work = private_root(args.work)
    item = work / (args.provider + ('-' + args.id if args.id else ''))
    item.mkdir(mode=0o700, exist_ok=True)
    result, code = invoke(work, item, args.binary, args.provider, args.command, args.id, args.page)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
