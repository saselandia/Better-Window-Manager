#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Compare KDE's native tray model with the current Quickshell watcher, offscreen."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import select
import shlex
import socket
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT/'config/hypr/skins/plasma/scripts'
WATCHER = 'org.kde.StatusNotifierWatcher'
HOST_PREFIX = 'org.kde.StatusNotifierHost-'
WATCHER_PATH = '/StatusNotifierWatcher'
WELL_KNOWN = r'[A-Za-z_-][A-Za-z0-9_-]*(?:\.[A-Za-z_-][A-Za-z0-9_-]*)+'
UNIQUE = r':[0-9]+\.[0-9]+'
ITEM = re.compile(rf'(?:{UNIQUE}|{WELL_KNOWN})/(?:[A-Za-z0-9_]+(?:/[A-Za-z0-9_]+)*)?\Z')
BUS = ['busctl', '--user', '--auto-start=no', '--timeout=1']
DAEMON = ['call', 'org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus']
SNI = 'org.kde.StatusNotifierItem'
LOCAL_PROXY = ROOT/'build/bwm-plasma-host/tray-proxy/xdg-dbus-proxy'


def session_bus_id(run=subprocess.run):
    reply = run(BUS+DAEMON+['GetId'], capture_output=True, text=True, check=True, timeout=2)
    fields = shlex.split(reply.stdout)
    if len(fields) != 2 or fields[0] != 's' or not re.fullmatch(r'[a-f0-9]{32}', fields[1]):
        raise ValueError('invalid-session-bus-id')
    return fields[1]


def choose_proxy(properties):
    if not properties or not LOCAL_PROXY.is_file():
        return 'xdg-dbus-proxy', False
    reply = subprocess.run([LOCAL_PROXY,'--version'], capture_output=True, text=True, check=True, timeout=2)
    if reply.stdout.strip() not in ('xdg-dbus-proxy 0.1.8+bwm-sni-unique-2', 'xdg-dbus-proxy 0.1.8+bwm-sni-unique-3'):
        raise ValueError('unexpected-local-tray-proxy-version')
    return str(LOCAL_PROXY), True


def bus_array(run, method):
    result = run(BUS+DAEMON+[method], capture_output=True, text=True, check=True, timeout=2)
    values = shlex.split(result.stdout)
    if len(values) < 2 or values[0] != 'as' or not values[1].isdigit() or int(values[1]) != len(values)-2:
        raise ValueError('invalid-bus-name-list')
    return set(values[2:])


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS/f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def property_endpoints(items, run=subprocess.run, *, exact_unique=False):
    """Ask the daemon about names and owners, independent of busctl's credentials table."""
    deadline = time.monotonic() + 8
    activatable = bus_array(run, 'ListActivatableNames')
    service_names = {item.partition('/')[0] for item in items}
    unique_services = {name for name in service_names if name.startswith(':')}
    owners = {}

    def owner(name):
        if name not in owners:
            remaining = deadline-time.monotonic()
            if remaining <= 0:
                raise ValueError('watcher-item-owner-check-timeout')
            reply = run(BUS+DAEMON+['GetNameOwner','s',name], capture_output=True, text=True, timeout=min(2,remaining))
            fields = shlex.split(reply.stdout) if reply.returncode == 0 else []
            owners[name] = fields[1] if len(fields)==2 and fields[0]=='s' and re.fullmatch(UNIQUE, fields[1]) else None
        return owners[name]

    reserved = {WATCHER, 'org.freedesktop.DBus'}
    aliases = {}
    if unique_services and not exact_unique:
        candidates = sorted(name for name in bus_array(run, 'ListNames') if re.fullmatch(WELL_KNOWN, name))
        for name in candidates:
            if name in reserved or name.startswith(HOST_PREFIX): continue
            current = owner(name)
            if current in unique_services:
                aliases.setdefault(current, []).append(name)

    endpoints = {}
    unfiltered = {}
    reasons = {'uniqueNameItemCount':0, 'uniqueWithoutAliasCount':0, 'onlyActivatableNameCount':0, 'ownerUnavailableCount':0}
    if exact_unique: reasons['uniqueExactRuleCount'] = 0
    for item in items:
        service, path = item.split('/', 1)
        if service in reserved or service.startswith(HOST_PREFIX): continue
        unique = service in unique_services
        current = owner(service)
        reasons['uniqueNameItemCount'] += int(unique)
        if not current or (unique and current != service):
            reasons['ownerUnavailableCount'] += 1
            continue
        if unique and exact_unique:
            endpoints[item] = (current, '/'+path, current)
            reasons['uniqueExactRuleCount'] += 1
            continue
        names = aliases.get(service, ()) if unique else (service,)
        usable = sorted(set(names)-activatable, key=lambda name: (not name.startswith('org.kde.StatusNotifierItem'), name))
        if usable:
            endpoints[item] = (usable[0], '/'+path, current)
        else:
            reasons['onlyActivatableNameCount' if names else 'uniqueWithoutAliasCount'] += 1
            unfiltered[item] = (current, '/'+path)
    return endpoints, unfiltered, reasons


def direct_metadata(endpoints, run=subprocess.run):
    """Read only small scalar SNI properties from exact unique owners not usable by the proxy."""
    count = icons = 0
    deadline = time.monotonic()+6
    for service, path in endpoints.values():
        values = {}
        for prop in ('Status','Category','IconName'):
            remaining = deadline-time.monotonic()
            if remaining <= 0:
                return {'directMetadataCount':count, 'directNamedIconCount':icons, 'directMetadataTimedOut':True}
            try:
                reply = run(BUS+['get-property',service,path,SNI,prop], capture_output=True, text=True, timeout=min(2,remaining))
                fields = shlex.split(reply.stdout) if reply.returncode == 0 else []
            except (ValueError, subprocess.TimeoutExpired):
                fields = []
            if len(fields)==2 and fields[0]=='s': values[prop] = fields[1]
        if values.get('Status') in ('Active','Passive','NeedsAttention') and values.get('Category'):
            count += 1
            icons += int(bool(values.get('IconName')))
    return {'directMetadataCount':count, 'directNamedIconCount':icons, 'directMetadataTimedOut':False}


def proxy_rules(pid, endpoints=()):
    rules = ['--filter', f'--own={HOST_PREFIX}{pid}', f'--see={WATCHER}',
            f'--call={WATCHER}=org.freedesktop.DBus.Properties.Get@{WATCHER_PATH}',
            f'--call={WATCHER}={WATCHER}.RegisterStatusNotifierHost@{WATCHER_PATH}',
            f'--broadcast={WATCHER}={WATCHER}.StatusNotifierItemRegistered@{WATCHER_PATH}',
            f'--broadcast={WATCHER}={WATCHER}.StatusNotifierItemUnregistered@{WATCHER_PATH}']
    rules.extend(f'--call={name}=org.freedesktop.DBus.Properties.GetAll@{path}'
                 for name, path in sorted({endpoint[:2] for endpoint in endpoints}))
    return rules


def item_digest(items):
    return hashlib.sha256('\0'.join(sorted(items)).encode('ascii')).hexdigest()


def complete_observation(report, native, before, after, endpoints=None, endpoints_unchanged=True):
    unchanged = before == after
    rows = native.get('nativeRows', 0)
    matches = (native.get('modelReady') is True and native.get('hostNameOwned') is True and
               type(rows) is int and rows == len(before[1]) and native.get('itemDigest') == item_digest(before[1]))
    report.update(watcherSnapshotUnchanged=unchanged, nativeModelMatches=matches,
                  nativeItemCount=rows if type(rows) is int else None, nativeHostNameOwned=native.get('hostNameOwned') is True)
    if endpoints is not None:
        loaded = native.get('nativePropertiesCount', 0)
        icons = native.get('nativeUsableIconCount', 0)
        complete = (type(loaded) is int and type(icons) is int and loaded == icons == len(before[1]) == len(endpoints))
        report.update(propertyEndpointsUnchanged=endpoints_unchanged, filterableItemCount=len(endpoints),
                      nativePropertiesCount=loaded, nativeUsableIconCount=icons,
                      nativePropertiesVerified=unchanged and matches and endpoints_unchanged and complete)
    if not unchanged:
        report['status'] = 'watcher-snapshot-changed'
    elif not matches:
        report['status'] = 'native-model-unverified'
    elif endpoints is not None:
        report['passed'] = report['nativePropertiesVerified']
        report['status'] = 'native-item-properties-verified' if report['passed'] else 'native-item-properties-incomplete'
    else:
        report['status'] = 'native-model-matches-watcher'
        report['passed'] = True


def run_native(binary, root, address, count, endpoints=None, proxy_binary='xdg-dbus-proxy'):
    for name in ('config', 'data', 'cache', 'runtime', 'defaults'):
        (root/name).mkdir(mode=0o700)
    load_script('native_launch').write_host_policy(root/'defaults')
    path = root/'runtime/tray-bus'
    env = {key: value for key, value in os.environ.items() if not key.startswith('BWM_R4_') and key not in
           ('DISPLAY', 'WAYLAND_DISPLAY', 'WAYLAND_SOCKET', 'HYPRLAND_INSTANCE_SIGNATURE', 'DBUS_STARTER_ADDRESS', 'DBUS_STARTER_BUS_TYPE')}
    env.update(QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software', XDG_CONFIG_HOME=str(root/'config'),
               XDG_DATA_HOME=str(root/'data'), XDG_CACHE_HOME=str(root/'cache'), XDG_RUNTIME_DIR=str(root/'runtime'),
               XDG_CONFIG_DIRS=str(root/'defaults'), XDG_DATA_DIRS='/usr/local/share:/usr/share',
               DBUS_SESSION_BUS_ADDRESS=f'unix:path={path}')

    # exec preserves the child's PID, so the filter grants only that one host name.
    gate = 'import os,sys; fd=int(sys.argv[1]); ready=os.read(fd,1); os.close(fd); os.execv(sys.argv[2],sys.argv[2:]) if ready else sys.exit(2)'
    read_gate, write_gate = os.pipe()
    controller, peer = socket.socketpair()
    host = proxy = None
    try:
        mode = '--probe-native-tray-model' if endpoints is None else '--probe-native-tray-properties'
        host = subprocess.Popen([sys.executable, '-c', gate, str(read_gate), str(binary), mode, str(count)],
                                env=env, pass_fds=(read_gate,), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        proxy = subprocess.Popen([proxy_binary, f'--fd={peer.fileno()}', address, str(path), *proxy_rules(host.pid, endpoints or ())],
                                 pass_fds=(peer.fileno(),), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        peer.close()
        if not select.select([controller], [], [], 3)[0] or not controller.recv(1) or proxy.poll() is not None:
            raise ValueError('filtered-proxy-unavailable')
        os.write(write_gate, b'1')
        try:
            output, _ = host.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            if proxy.poll() is not None:
                raise ValueError('tray-proxy-exited-during-native-probe') from None
            raise
        try:
            native = json.loads(output)
        except ValueError as exc:
            raise ValueError('native-tray-probe-failed') from exc
        if not isinstance(native, dict) or native.get('version') != 1:
            raise ValueError('invalid-native-tray-reply')
        if host.returncode != 0:
            native['modelReady'] = False
        return native
    finally:
        os.close(read_gate)
        os.close(write_gate)
        controller.close()
        peer.close()
        if host is not None and host.poll() is None:
            host.kill()
            host.communicate()
        if proxy is not None:
            try:
                proxy.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proxy.kill()
                proxy.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, default=ROOT/'build/bwm-plasma-host/bwm-plasma-host')
    parser.add_argument('--properties', action='store_true', help='Allow GetAll at the registered item endpoints and check status and icons')
    args = parser.parse_args()
    report = {'version': 1, 'passed': False, 'replacementReady': False, 'panelShown': False,
              'scope': 'native-tray-item-properties' if args.properties else 'native-tray-watcher-enumeration'}
    stage = 'watcher-preflight'
    try:
        check = load_script('r4-session-check')
        watcher, before = check.tray_observation()
        report['watcher'] = watcher
        if before is None or watcher.get('ownerKind') != 'quickshell':
            raise ValueError('quickshell-watcher-unavailable')
        if not 0 < len(before[1]) <= 256 or len(set(before[1])) != len(before[1]) or not all(ITEM.fullmatch(i) for i in before[1]):
            raise ValueError('watcher-items-empty-or-invalid')
        address = os.environ.get('DBUS_SESSION_BUS_ADDRESS')
        if not address:
            raise ValueError('session-bus-address-unavailable')
        stage = 'proxy-selection'
        proxy_binary, exact_unique = choose_proxy(args.properties)
        if args.properties:
            stage = 'item-endpoints'
            bus_id = session_bus_id()
            report['uniqueNameFilter'] = 'exact-object' if exact_unique else 'well-known-alias'
            endpoints, unresolved, resolution = property_endpoints(before[1], exact_unique=exact_unique)
            report['endpointResolution'] = resolution
            report.update(direct_metadata(unresolved))
        else:
            endpoints = None
        stage = 'native-probe'
        with tempfile.TemporaryDirectory(prefix='bwm-r4-tray-') as temporary:
            native = run_native(args.binary.expanduser().resolve(), Path(temporary), address, len(before[1]),
                                list(endpoints.values()) if endpoints is not None else None, proxy_binary)
        stage = 'watcher-recheck'
        _, after = check.tray_observation()
        endpoints_unchanged = endpoints is None or (bus_id == session_bus_id() and before == after and
            (endpoints, unresolved, resolution) == property_endpoints(after[1], exact_unique=exact_unique))
        complete_observation(report, native, before, after, endpoints, endpoints_unchanged)
    except FileNotFoundError:
        report['status'] = 'native-host-or-xdg-dbus-proxy-missing'
    except subprocess.TimeoutExpired:
        report['status'] = 'native-tray-probe-timeout'
        report['timeoutStage'] = stage
    except subprocess.SubprocessError:
        report['status'] = 'watcher-item-owners-unavailable'
    except OSError:
        report['status'] = 'native-tray-probe-unavailable'
    except ValueError as exc:
        report['status'] = str(exc)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['passed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
