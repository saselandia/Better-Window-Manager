#!/usr/bin/env python3
"""R4 exit gate with a widget nobody chose in advance, through the native KDE Store provider.

The store listing decides the candidate: results of plasmoids.knsrc (sorted by downloads) are
tried in order, skipping only ids already used by BWM tests. Each candidate is installed with
KNSCore (the same Entry/Transaction objects as the "Get New Widgets" dialog) into disposable XDG
roots, inspected before any of its QML runs, then hosted offscreen: its own option is changed
through its original configuration page, applied, read back from a new process, and finally the
package is removed again through KNSCore. Needs network access to store.kde.org.

Safety: a candidate is rejected before loading if it ships compiled code or asks Plasma to run
commands (executable data engine, Process/QProcess, P5Support/Plasma5Support executable source).
This is a static filter, not a sandbox; the session D-Bus is not reachable from the children.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

KNOWN = {'2144212'}  # Andromeda: already used as the external fixture of every other R4 test.
RISKY = [re.compile(p) for p in (
    r'engine\s*:\s*["\']executable["\']', r'\bexecutable\b\s*\.\s*connectSource', r'\bQProcess\b',
    r'\bProcess\s*\{', r'Plasma5Support\.DataSource[\s\S]{0,200}executable', r'P5Support\.DataSource[\s\S]{0,200}executable')]

p = argparse.ArgumentParser()
p.add_argument('--binary', type=Path, required=True)
p.add_argument('--report', type=Path, required=True)
p.add_argument('--term', default='', help='Store search term; empty lists the most downloaded widgets')
p.add_argument('--max-candidates', type=int, default=12)
a = p.parse_args()


def run(env, *argv, timeout=180, check=True):
    r = subprocess.run([str(a.binary), *map(str, argv)], env=env, capture_output=True, text=True, timeout=timeout)
    try:
        data = json.loads(r.stdout) if r.stdout.strip().startswith('{') else None
    except json.JSONDecodeError:
        data = None
    if check and (r.returncode or data is None):
        raise RuntimeError(f'{argv[0]} {argv[1] if len(argv) > 1 else ""}: exit {r.returncode}\n{r.stderr[-1500:]}\n{r.stdout[-1500:]}')
    return data, r.returncode


def inspect(package: Path):
    """Reasons to refuse loading a package; empty when acceptable."""
    reasons, bools = [], []
    for f in package.rglob('*'):
        if not f.is_file():
            continue
        head = f.read_bytes()[:4]
        if head == b'\x7fELF' or f.suffix in ('.so', '.py', '.sh'):
            reasons.append('ships executable/compiled file ' + str(f.relative_to(package)))
        if f.suffix in ('.qml', '.js'):
            text = f.read_text(errors='replace')
            for rx in RISKY:
                if rx.search(text):
                    reasons.append(f'{f.relative_to(package)} runs commands ({rx.pattern})')
                    break
    main = package / 'contents/config/main.xml'
    if not main.exists() or not (package / 'contents/config/config.qml').exists():
        reasons.append('no own configuration (contents/config/main.xml + config.qml)')
    else:
        bools = re.findall(r'<entry\s+name="([^"]+)"\s+type="Bool"', main.read_text(errors='replace'))
        if not bools:
            reasons.append('no boolean option to exercise without guessing values')
    return reasons, bools


def digest(package: Path):
    h = hashlib.sha256()
    for f in sorted(x for x in package.rglob('*') if x.is_file()):
        h.update(str(f.relative_to(package)).encode()); h.update(f.read_bytes())
    return h.hexdigest()


report = {'provider': None, 'sessionModified': False, 'liveHyprlandUsed': False, 'candidates': [], 'gate': None}
try:
    with tempfile.TemporaryDirectory(prefix='bwm-r4-kns-') as tmp:
        root = Path(tmp)
        for d in ('config', 'data', 'cache', 'runtime', 'defaults'):
            (root / d).mkdir(mode=0o700)
        env = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                   XDG_CONFIG_HOME=str(root / 'config'), XDG_DATA_HOME=str(root / 'data'),
                   XDG_CACHE_HOME=str(root / 'cache'), XDG_RUNTIME_DIR=str(root / 'runtime'),
                   XDG_CONFIG_DIRS=str(root / 'defaults'), XDG_DATA_DIRS='/usr/local/share:/usr/share',
                   DBUS_SESSION_BUS_ADDRESS='unix:path=' + str(root / 'no-bus'))
        env.pop('WAYLAND_DISPLAY', None); env.pop('DISPLAY', None); env.pop('HYPRLAND_INSTANCE_SIGNATURE', None)
        env.pop('BWM_R4_DESKTOP_ACTIONS',None);env.pop('BWM_R4_DESKTOP_RUNTIME',None);env.pop('BWM_R4_DESKTOP_CONFIG',None)
        for key in ('BWM_R4_TASK_ACTIONS','BWM_R4_TASK_RUNTIME','BWM_R4_TASK_CONFIG','BWM_R4_NATIVE_DESKTOPS'):env.pop(key,None)
        search, _ = run(env, '--kns-search', a.term, 0, timeout=90)
        report['provider'] = search['provider']
        report['searchCount'] = len(search['results'])
        assert search['results'], 'The store returned no widgets'
        for entry in search['results']:
            if len(report['candidates']) >= a.max_candidates:
                break
            if entry['uniqueId'] in KNOWN:
                continue
            item = {'uniqueId': entry['uniqueId'], 'name': entry['name'], 'version': entry['version'],
                    'downloadCount': entry['downloadCount']}
            report['candidates'].append(item)
            installed, code = run(env, '--kns-install', entry['uniqueId'], check=False)
            item['install'] = {'exit': code, 'errors': (installed or {}).get('errors'), 'questions': (installed or {}).get('questions'),
                               'status': ((installed or {}).get('installed') or {}).get('status'),
                               'catalogAdded': (installed or {}).get('catalogAdded')}
            added = (installed or {}).get('catalogAdded') or []
            if code or len(added) != 1:
                item['result'] = 'install-not-usable'
                files = ((installed or {}).get('installed') or {}).get('installedFiles') or []
                meta = next((Path(f) / 'metadata.json' for f in files if (Path(f) / 'metadata.json').exists()), None)
                if meta:
                    data = json.loads(meta.read_text())
                    if data.get('KPackageStructure') != 'Plasma/Applet':
                        # KPackage 6.29 (and Plasma 6.7.5's widget explorer) only lists metadata with
                        # KPackageStructure; legacy KPlugin.ServiceTypes packages are skipped there too.
                        item['result'] = 'legacy-metadata-not-listed-by-kpackage'
                        item['legacyServiceTypes'] = data.get('KPlugin', {}).get('ServiceTypes')
                if installed and (installed.get('installed') or {}).get('status') == 'installed':
                    removed, code = run(env, '--kns-uninstall', entry['uniqueId'], check=False)
                    item['uninstall'] = {'exit': code, 'errors': (removed or {}).get('errors'),
                                         'status': ((removed or {}).get('after') or {}).get('status'),
                                         'packageGone': all(not Path(f).exists() for f in files)}
                continue
            plugin = added[0]
            package = root / 'data/plasma/plasmoids' / plugin
            item['plugin'] = plugin
            item['packageInXdgDataHome'] = package.is_dir()
            reasons, bools = inspect(package) if package.is_dir() else (['package not found under XDG_DATA_HOME'], [])
            item['rejected'] = reasons
            item['booleanOptions'] = bools
            if not reasons:
                item['sha256'] = digest(package)
                exercised, code = run(env, '--exercise', plugin, check=False)
                item['exercise'] = None if exercised is None else {
                    k: exercised.get(k) for k in ('itemLoaded', 'compact', 'full', 'exercise', 'exercisePassed', 'categories', 'pages', 'error', 'translationDomain')}
                if exercised and exercised.get('exercisePassed'):
                    key = exercised['exercise']['key']
                    reopened, _ = run(env, '--probe', plugin, check=False)
                    value = ((reopened or {}).get('valuesBeforeExercise') or {}).get(key)
                    item['newProcessValue'] = value
                    item['newProcessMatches'] = value == exercised['exercise']['expectedValue']
                    if item['newProcessMatches'] and key in bools:
                        report.setdefault('passed', []).append({'uniqueId': entry['uniqueId'], 'plugin': plugin, 'key': key, 'savedValue': value})
                    if item['newProcessMatches'] and key in bools and not report['gate']:
                        report['gate'] = {'uniqueId': entry['uniqueId'], 'plugin': plugin, 'key': key,
                                          'savedValue': value, 'chosenBy': 'store order (downloads), first candidate passing the static safety filter'}
                elif exercised is None:
                    item['exerciseExit'] = code
                else:
                    item['notPassedReason'] = exercised.get('configurationError') or 'no writable boolean cfg_ property on its pages'
                    item['exerciseExit'] = code
            removed, code = run(env, '--kns-uninstall', entry['uniqueId'], check=False)
            item['uninstall'] = {'exit': code, 'errors': (removed or {}).get('errors'),
                                 'catalogRemoved': (removed or {}).get('catalogRemoved'),
                                 'status': ((removed or {}).get('after') or {}).get('status'),
                                 'packageGone': not package.exists()}
            item['result'] = 'gate-passed' if any(x['plugin'] == plugin for x in report.get('passed', [])) else ('rejected' if reasons else 'not-passed')
        report['summary'] = {r: sum(1 for c in report['candidates'] if c.get('result') == r)
                             for r in sorted({c.get('result') for c in report['candidates']})}
        report['ok'] = bool(report['gate']) and all(
            c.get('uninstall', {}).get('packageGone', True) and c.get('uninstall', {}).get('exit', 0) == 0
            for c in report['candidates'] if 'uninstall' in c)
finally:
    report['finishedAt'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')
    a.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
print(json.dumps({'ok': report.get('ok'), 'gate': report.get('gate')}, ensure_ascii=False))
raise SystemExit(0 if report.get('ok') else 1)
