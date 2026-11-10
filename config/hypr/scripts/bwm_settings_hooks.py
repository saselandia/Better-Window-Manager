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


if __name__ == "__main__":
    changed()
