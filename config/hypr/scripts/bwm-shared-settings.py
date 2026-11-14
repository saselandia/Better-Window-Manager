#!/usr/bin/env python3
"""Small shared-settings transactions over Config's existing store; no skin-specific data.

Idle timers are consumed live by BwmIdle.qml in all skins. Never triggers a power action.
"""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile


def save_idle(changes):
    limits = {'screen': 7200, 'lock': 7200, 'suspend': 14400}
    if not isinstance(changes, dict) or not changes.keys() <= limits.keys():
        raise ValueError('Clave de inactividad no admitida')
    if any(type(v) is not int or not 0 <= v <= limits[k] for k, v in changes.items()):
        raise ValueError('Tiempo fuera de rango')
    config = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    path = (config / 'illogical-impulse/config.json').resolve()
    original = path.read_text()
    data = json.loads(original)
    data.setdefault('idle', {}).update(changes)
    # Respect the same final user overlay as all existing settings surfaces.
    loader = importlib.machinery.SourceFileLoader('shared_user', str(Path(__file__).with_name('bwm-user-config')))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    effective = json.loads(json.dumps(data))
    module.apply_shell(effective, data.get('appearance', {}).get('bwmTheme', 'default'))
    if any(effective.get('idle', {}).get(k) != v for k, v in changes.items()):
        raise ValueError('El ajuste está fijado en la configuración de texto del usuario')
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as f:
        tmp = Path(f.name)
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    try:
        tmp.chmod(path.stat().st_mode & 0o777)
        if path.read_text() != original:
            raise ValueError('La configuración cambió durante el guardado; reintenta')
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)
    return data['idle']


if __name__ == '__main__':
    try:
        if sys.argv[1] != 'idle':
            raise ValueError('Acción desconocida')
        print(json.dumps(save_idle(json.loads(sys.argv[2]))))
    except (ValueError, OSError, IndexError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
