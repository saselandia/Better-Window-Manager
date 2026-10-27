#!/usr/bin/env python3
"""Themes and shell plugins for BWM; catalog metadata is never executed."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from html.parser import HTMLParser
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import time
import tomllib
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

SCRIPTS = Path(__file__).resolve().parent
USER_THEMES = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'bwm/omarchy-themes'
CACHE = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')) / 'bwm/addons'
PLUGIN_CATALOG = 'https://raw.githubusercontent.com/omacom/omarchy-plugin-marketplace/main/site/catalog.json'
THEME_CATALOG = 'https://omarchy.org/themes/'
PLUGIN_SCRIPT = SCRIPTS / 'bwm-plugin.sh'
SUPPORTED_KINDS = {'bar-widget', 'service'}


def repository_url(value: str) -> str:
    value = value.strip().rstrip('/')
    url = urlsplit(value)
    if (url.scheme != 'https' or not url.hostname or url.username or url.password
            or url.query or url.fragment or not re.fullmatch(r'/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+', url.path)
            or any(p in ('.', '..') for p in url.path.split('/'))):
        raise ValueError('Introduce la URL HTTPS del repositorio Git, sin /tree/ ni /blob/.')
    if url.hostname == 'github.com' and len(url.path.strip('/').split('/')) != 2:
        raise ValueError('Usa la URL del repositorio de GitHub, no la de un archivo o una rama.')
    return value.removesuffix('.git')


def run(command: list[str], timeout: int = 120) -> str:
    proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout,
                          env={**os.environ, 'GIT_TERMINAL_PROMPT': '0'})
    if proc.returncode:
        raise ValueError((proc.stderr.strip() or proc.stdout.strip() or 'La operación falló.')[-2500:])
    return proc.stdout


def check_tree(directory: Path):
    # Git metadata is not theme/plugin input. Files installed by a repo must stay in it.
    for base, dirs, files in os.walk(directory):
        if Path(base) == directory:
            dirs[:] = [d for d in dirs if d != '.git']
        for name in dirs + files:
            if (Path(base) / name).is_symlink():
                raise ValueError('El repositorio contiene enlaces simbólicos; no se ha instalado.')


def validate_plugin(directory: Path) -> dict:
    check_tree(directory)
    manifest = json.loads((directory / 'manifest.json').read_text())
    if not isinstance(manifest, dict) or not isinstance(manifest.get('name'), str) or not manifest['name'].strip():
        raise ValueError('El manifest necesita un nombre de plugin.')
    plugin_id = manifest.get('id', '')
    if (not isinstance(plugin_id, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', plugin_id)
            or plugin_id.startswith('omarchy.')):
        raise ValueError('El plugin necesita un id propio, fuera del espacio reservado omarchy.*.')
    kinds = manifest.get('kinds', [])
    if (manifest.get('schemaVersion') != 1 or not isinstance(kinds, list) or not kinds
            or any(not isinstance(k, str) or k not in SUPPORTED_KINDS for k in kinds)):
        raise ValueError('BWM admite widgets de barra y sus servicios de Omarchy (schemaVersion 1). '
                         'Este plugin reemplaza otras partes del shell que BWM no carga.')
    entries = manifest.get('entryPoints', {})
    if not isinstance(entries, dict):
        raise ValueError('entryPoints debe ser un objeto.')
    for kind in kinds:
        key = 'barWidget' if kind == 'bar-widget' else kind
        name = entries.get(key, '')
        if not isinstance(name, str) or not name:
            raise ValueError(f'Falta el archivo de entrada {key}.')
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or not (directory / name).is_file() or path.suffix != '.qml':
            raise ValueError(f'Archivo de entrada no válido: {name}')
    # The upstream shell has modules BWM may not ship. Reject those imports
    # before an incompatible plugin can disappear silently from the user's bar.
    qml_root = SCRIPTS.parents[1] / 'quickshell/ii'
    for source in directory.rglob('*.qml'):
        if '.git' in source.relative_to(directory).parts:
            continue
        imports = re.findall(r'^\s*import\s+qs\.([A-Za-z0-9_.]+)\b', source.read_text(), re.M)
        for module in imports:
            if not qml_root.joinpath(*module.split('.')).is_dir():
                raise ValueError(f'El plugin requiere qs.{module}, un módulo de Omarchy no disponible en BWM.')
    return manifest


def validate_theme(directory: Path) -> dict:
    check_tree(directory)
    colors = tomllib.loads((directory / 'colors.toml').read_text())
    for key in ('background', 'foreground', 'accent'):
        if not isinstance(colors.get(key), str) or not re.fullmatch(r'#[0-9A-Fa-f]{6}', colors[key]):
            raise ValueError(f'colors.toml necesita {key} en formato #RRGGBB (temas Omarchy actuales).')
    return colors


@contextmanager
def cloned(url: str, parent: Path):
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.bwm-install-', dir=parent) as temporary:
        checkout = Path(temporary) / 'checkout'
        run(['git', '-c', 'core.hooksPath=/dev/null', 'clone', '--depth', '1', '--', url, str(checkout)])
        yield checkout


def install_theme(url: str) -> dict:
    import bwm_omarchy as bwm
    url = repository_url(url)
    name = urlsplit(url).path.rstrip('/').split('/')[-1].lower()
    name = re.sub(r'^omarchy-', '', name)
    name = re.sub(r'-(?:omarchy-)?theme$', '', name)
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', name) or name == 'dynamic':
        raise ValueError('Nombre de tema no válido.')
    if any(t['id'] == name for t in bwm.list_omarchy_themes()):
        raise ValueError(f'El tema {name} ya está instalado; no se sobrescribe.')
    with cloned(url, USER_THEMES) as checkout:
        validate_theme(checkout)
        (checkout / '.bwm-source.json').write_text(json.dumps({'url': url}) + '\n')
        checkout.rename(USER_THEMES / name)
    return {'ok': True, 'id': name, 'message': f'Tema instalado: {name}. Ya puedes seleccionarlo.'}


def installed() -> dict:
    import bwm_omarchy as bwm
    plugins = json.loads(run([str(PLUGIN_SCRIPT), 'catalog'], timeout=20))
    mode, theme = bwm.get_retro_mode()
    return {**plugins, 'themes': bwm.list_omarchy_themes(), 'themeMode': mode, 'theme': theme,
            'skin': bwm._bwm_theme()}


class ThemeLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.link = ''
        self.label = []
        self.themes = []

    def handle_starttag(self, tag, attrs):
        if tag == 'li':
            self.depth += 1
        if tag == 'a' and self.depth:
            url = dict(attrs).get('href', '')
            if url.startswith('https://github.com/'):
                self.link, self.label = url, []

    def handle_data(self, value):
        if self.link:
            self.label.append(value)

    def handle_endtag(self, tag):
        if tag == 'a' and self.link:
            try:
                url = repository_url(self.link)
                self.themes.append({'id': url, 'name': ''.join(self.label).strip(), 'url': url,
                                    'description': 'Tema de la comunidad de Omarchy', 'kind': 'theme'})
            except ValueError:
                pass
            self.link = ''
        if tag == 'li':
            self.depth = max(0, self.depth - 1)


def download(url: str) -> bytes:
    with urlopen(Request(url, headers={'User-Agent': 'BWM-Addons/1.0'}), timeout=25) as response:
        data = response.read(32 * 1024 * 1024 + 1)
    if len(data) > 32 * 1024 * 1024:
        raise ValueError('El catálogo supera el tamaño permitido.')
    return data


def remote_catalog(kind: str, refresh: bool = False) -> tuple[list, str]:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f'{kind}.json'
    cached = None
    try:
        cached = json.loads(path.read_text())
        if not refresh and time.time() - path.stat().st_mtime < 3600:
            return cached, ''
    except (OSError, ValueError):
        pass
    try:
        if kind == 'themes':
            parser = ThemeLinks()
            parser.feed(download(THEME_CATALOG).decode('utf-8'))
            entries = parser.themes
        else:
            data = json.loads(download(PLUGIN_CATALOG))
            entries = [{'id': p['id'], 'name': p['name'], 'url': repository_url(p['repo']),
                        'description': p.get('description', ''), 'kind': p.get('kind', ''),
                        'author': p.get('author', '')}
                       for p in data['plugins']
                       if p.get('installAvailable') and p.get('repositoryLayout') == 'root-plugin'
                       and p.get('kind') in ('Bar widget', 'Service + Bar widget', 'Service')]
        if not entries:
            raise ValueError('El catálogo no contiene resultados compatibles con BWM.')
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(entries, ensure_ascii=False))
        temporary.replace(path)
        return entries, ''
    except Exception as error:
        if cached is not None:
            return cached, 'Sin conexión: se muestra el último catálogo guardado.'
        raise ValueError(f'No se pudo consultar el catálogo: {error}') from error


def discover(kind: str, query: str, refresh: bool = False, offset: int = 0) -> dict:
    entries, warning = remote_catalog(kind, refresh)
    words = query.casefold().split()
    matches = [e for e in entries if all(w in ' '.join(str(v) for v in e.values()).casefold() for w in words)]
    offset = max(0, offset)
    return {'results': matches[offset:offset + 30], 'total': len(matches),
            'nextOffset': min(offset + 30, len(matches)), 'message': warning}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('list')
    search = sub.add_parser('discover')
    search.add_argument('kind', choices=('themes', 'plugins'))
    search.add_argument('query', nargs='?', default='')
    search.add_argument('--refresh', action='store_true')
    search.add_argument('--offset', type=int, default=0)
    for action in ('install-theme', 'install-plugin'):
        sub.add_parser(action).add_argument('url')
    sub.add_parser('validate-plugin').add_argument('directory', type=Path)
    apply = sub.add_parser('apply-theme')
    apply.add_argument('name')
    args = parser.parse_args()
    try:
        if args.action == 'list':
            result = installed()
        elif args.action == 'discover':
            result = discover(args.kind, args.query, args.refresh, args.offset)
        elif args.action == 'validate-plugin':
            result = {'ok': True, 'id': validate_plugin(args.directory)['id']}
        elif args.action == 'install-theme':
            result = install_theme(args.url)
        elif args.action == 'install-plugin':
            run([str(PLUGIN_SCRIPT), 'add', repository_url(args.url), '--yes'])
            result = {'ok': True, 'message': 'Plugin instalado y activado. Puedes elegir su posición en la lista de instalados.'}
        else:
            # Keep the result JSON separate from hooks' diagnostic output.
            run([sys.executable, str(SCRIPTS / 'bwm_omarchy.py'), 'set-theme', args.name], timeout=180)
            result = {'ok': True, 'message': 'Tema aplicado: ' + args.name}
        print(json.dumps(result, ensure_ascii=False))
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        print(json.dumps({'ok': False, 'message': str(error)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == '__main__':
    main()
