"""Avisos de los gestores comunes a la skin activa (sin datos de ninguna skin aquí)."""
import json
import os
from pathlib import Path
import subprocess
import sys


def changed():
    """Exportar después de guardar un ajuste; el gestor conserva la única recarga necesaria."""
    try:
        config = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        active = json.loads((config / "illogical-impulse/config.json").read_text()).get("appearance", {}).get("bwmTheme", "default")
        import bwm_skins
        skin = bwm_skins.skin(active)
        hook = skin.get("hooks", {}).get("settingsChanged")
        if not hook:
            return
        script = (Path(skin["dir"]) / hook).resolve()
        if Path(skin["dir"]).resolve() not in script.parents:
            raise ValueError("El hook de ajustes debe estar dentro de su skin")
        subprocess.run([sys.executable, str(script), "export", "--no-reload"],
                       stdout=subprocess.DEVNULL, timeout=20, check=False)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"BWM: no se pudo sincronizar el ajuste con la skin: {exc}", file=sys.stderr)


def skin_changed(phase, previous, current):
    """Notify hooks of both involved skins; no skin-specific policy in this module.

    Before is called before changing profiles; after is called after shell reload.
    A hook may only act on an explicitly registered/opted-in helper of its own.
    """
    if phase not in ('before', 'after'): raise ValueError('Fase de cambio de skin inválida')
    import bwm_skins
    ok = True
    for sid in dict.fromkeys((previous, current)):
        skin = bwm_skins.skin(sid)
        hook = skin.get('hooks', {}).get('skinChanged')
        if not hook: continue
        try:
            directory = Path(skin['dir']).resolve()
            script = (directory / hook).resolve()
            if directory not in script.parents: raise ValueError('El hook debe estar dentro de su skin')
            result = subprocess.run([sys.executable, str(script), 'event', phase, previous, current],
                                    capture_output=True, text=True, timeout=3, check=False)
            if result.returncode: raise RuntimeError(result.stderr.strip() or 'El hook no confirmó el cambio')
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            print(f'BWM: hook de cambio de {sid}: {exc}', file=sys.stderr);ok = False
    return ok


if __name__ == "__main__":
    if sys.argv[1:2] == ['skin']:
        if len(sys.argv) != 5: raise SystemExit('Uso: bwm_settings_hooks.py skin before|after ANTERIOR ACTUAL')
        raise SystemExit(0 if skin_changed(*sys.argv[2:]) else 1)
    changed()
