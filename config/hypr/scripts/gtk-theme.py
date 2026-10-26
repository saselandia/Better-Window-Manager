#!/usr/bin/env python3
"""
Tema GTK 3 de BWM con recarga en vivo, en todos los estilos.

GTK 3 lee ~/.config/gtk-3.0/gtk.css una sola vez, al arrancar: las apps abiertas no cambiaban de
colores con el tema/fondo. En cambio sí releen los archivos de su tema cuando cambia el nombre
del tema GTK. Por eso los colores (bwm-colors.css, lo escriben matugen en Default, Breeze en
Plasma y bwm_omarchy en Retro) van dentro de un tema propio que importa adw-gtk3[-dark], y hay
dos copias, BWM-1 y BWM-2: cada recarga pasa a la otra y todas las apps GTK 3 se repintan.
~/.config/gtk-3.0/gtk.css queda vacío (si guardara colores, pisaría los nuevos hasta reiniciar).

GTK 4/libadwaita ignora el tema GTK: sigue con ~/.config/gtk-4.0/gtk.css (se aplica al abrir).

Uso: gtk-theme.py set <light|dark>   claro/oscuro (sólo recarga si cambia)
     gtk-theme.py reload             recarga los colores (tras escribir bwm-colors.css)
"""
import os
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
THEMES = HOME / ".local" / "share" / "themes"
GTK3 = HOME / ".config" / "gtk-3.0"
COLORS = GTK3 / "bwm-colors.css"
VARIANT = HOME / ".local" / "state" / "bwm" / "gtk-variant"
NAMES = ("BWM-1", "BWM-2")
STUB = ("/* BWM: los colores de GTK 3 están en el tema BWM-1/BWM-2 (hypr/scripts/gtk-theme.py),\n"
        "   que importa bwm-colors.css y se recarga en vivo. Lo que escribas aquí se aplica encima. */\n")


def gsetting(key, value=None):
    if value is None:
        return subprocess.run(["gsettings", "get", "org.gnome.desktop.interface", key],
                              capture_output=True, text=True).stdout.strip().strip("'")
    subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", key, value],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def write_theme(name: str, variant: str):
    base = THEMES / ("adw-gtk3" if variant == "light" else "adw-gtk3-dark")
    d = THEMES / name
    (d / "gtk-3.0").mkdir(parents=True, exist_ok=True)
    (d / "index.theme").write_text(
        "[Desktop Entry]\nType=X-GNOME-Metatheme\nName=" + name + "\n"
        "Comment=BWM: adw-gtk3 con los colores del estilo/tema activo\nEncoding=UTF-8\n", encoding="utf-8")
    (d / "gtk-3.0" / "gtk.css").write_text(
        f'@import url("file://{base}/gtk-3.0/gtk.css");\n'
        f'@import url("file://{COLORS}");\n', encoding="utf-8")
    # GTK 4 apps without libadwaita also follow the GTK theme
    if (base / "gtk-4.0" / "gtk.css").is_file():
        (d / "gtk-4.0").mkdir(exist_ok=True)
        (d / "gtk-4.0" / "gtk.css").write_text(
            f'@import url("file://{base}/gtk-4.0/gtk.css");\n'
            f'@import url("file://{HOME}/.config/gtk-4.0/gtk.css");\n', encoding="utf-8")


def ensure_stub():
    """The old ~/.config/gtk-3.0/gtk.css held the colours: move them to bwm-colors.css."""
    css = GTK3 / "gtk.css"
    try:
        text = css.read_text(encoding="utf-8")
    except Exception:
        text = ""
    if "@define-color" in text:
        if not COLORS.is_file():
            COLORS.write_text(text, encoding="utf-8")
        css.write_text(STUB, encoding="utf-8")
    elif not text.strip():
        css.write_text(STUB, encoding="utf-8")


def current_variant() -> str:
    try:
        v = VARIANT.read_text(encoding="utf-8").strip()
        if v in ("light", "dark"):
            return v
    except Exception:
        pass
    return "dark"


def switch(variant: str):
    ensure_stub()
    cur = gsetting("gtk-theme")
    new = NAMES[1] if cur == NAMES[0] else NAMES[0]
    write_theme(new, variant)
    VARIANT.parent.mkdir(parents=True, exist_ok=True)
    VARIANT.write_text(variant + "\n", encoding="utf-8")
    gsetting("gtk-theme", new)
    # settings.ini: GTK reads it when there is no gsettings (e.g. under some sandboxes)
    for ini in (GTK3 / "settings.ini", HOME / ".config" / "gtk-4.0" / "settings.ini"):
        try:
            lines = ini.read_text(encoding="utf-8").splitlines()
            lines = [f"gtk-theme-name={new}" if l.startswith("gtk-theme-name=") else l for l in lines]
            ini.write_text("\n".join(lines) + "\n", encoding="utf-8")
        except Exception:
            pass


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "reload"
    if cmd == "set" and len(sys.argv) > 2 and sys.argv[2] in ("light", "dark"):
        if sys.argv[2] != current_variant() or gsetting("gtk-theme") not in NAMES:
            switch(sys.argv[2])
    elif cmd == "reload":
        switch(current_variant())
    else:
        print(__doc__)
        sys.exit(1)
