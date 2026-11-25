"""Edición segura de ~/.config/gtk-{3,4}.0/settings.ini, compartida por los escritores de BWM.

Varios procesos lo actualizan casi a la vez al cambiar de skin (iconos, tema GTK alternado,
cursor). Con `open(..., "w")` uno truncaba el archivo mientras otro lo leía vacío y escribía
un único "\\n" en la posición 0, encima del "[" de la cabecera: quedaba "\\nSettings]" y GTK
ignoraba todo el archivo (§3.80, §373). Aquí se lee y escribe bajo un candado común y se
publica con un reemplazo atómico, de modo que nadie ve el archivo truncado.
"""

from __future__ import annotations

import fcntl
import os
import tempfile
from pathlib import Path
from typing import Callable

LOCK = Path(os.environ.get("XDG_RUNTIME_DIR") or tempfile.gettempdir()) / "bwm-gtk-settings.lock"


def update(path: Path, edit: Callable[[str], str]) -> bool:
    """Aplica `edit(texto_actual) -> texto_nuevo`; escribe sólo si cambia. Devuelve si escribió."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCK, "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        new = edit(text)
        if new == text:
            return False
        # Reemplazo en la misma carpeta (puede ser un enlace al repo: se resuelve el destino real)
        target = path.resolve() if path.is_symlink() else path
        fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=".settings.ini.")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(new)
            if target.exists():
                os.chmod(tmp, target.stat().st_mode & 0o7777)
            os.replace(tmp, target)
        except BaseException:
            try:
                os.unlink(tmp)
            except FileNotFoundError:
                pass
            raise
        return True
