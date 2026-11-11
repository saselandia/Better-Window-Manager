#!/usr/bin/env python3
"""Genera los catálogos bwm_plasma_menus/<idioma>.po de los menús portados (F9).

Toma sólo las cadenas que usan los menús (con su contexto) de los .po originales de KDE 6.7.5:
kwin, plasma-desktop (taskmanager, desktopcontainment), plasma-workspace (containmentactions/
contextmenu, wallpaper image) y libplasma. Uso, con los po/ de esos tarballs ya extraídos:

  extract.py <carpeta con */po/<idioma>/<dominio>.po> <carpeta de salida>
"""
import sys
from pathlib import Path

# (dominio, contexto o None, msgid)
WANTED = [
    ("kwin", None, s) for s in [
        "&Desktops", "&All Desktops", "Desktop %1", "Move to %1", "Move to &Screen", "Ma&ximize", "Mi&nimize",
        "Keep &Above Others", "&More Actions", "&Move", "&Resize", "Keep &Below Others", "&Fullscreen",
        "&No Titlebar and Frame", "&Hide from Screenshots and Screen Recordings",
        "Configure Special &Window Settings…", "Configure S&pecial Application Settings…", "&Close"]
] + [
    ("kwin", "Create a new desktop and add the window to that desktop", "Add to &New Desktop"),
    ("kwin", "Create a new desktop and move the window to that desktop", "Move to New Desktop"),
    ("kwin", "@item:inmenu List of all Screens to send a window to. First argument is a number, second the output identifier. E.g. Screen 1 (HDMI1)", "Screen &%1 (%2)"),
] + [
    ("plasma_applet_org.kde.plasma.taskmanager", c, s) for c, s in [
        ("@title:group for section of menu items", "Recent Files"), ("@title:group for section of menu items", "Actions"),
        ("Play previous track", "Previous Track"), ("Pause playback", "Pause"), ("Start playback", "Play"),
        ("Play next track", "Next Track"), ("Stop playback", "Stop"), ("action:inmenu", "Open New Window"),
        ("action:inmenu", "Move to &Desktop"), ("action:inmenu", "Move &To Current Desktop"), ("action:inmenu", "&All Desktops"),
        ("action:inmenu", "&New Desktop"), ("action:inmenu", "&Pin to Task Manager"), ("action:inmenu", "Unpin from Task Manager"),
        ("item:inmenu opens submenu", "More"), ("action:inmenu", "&Move"), ("action:inmenu", "Re&size"),
        ("action:inmenu", "Ma&ximize"), ("action:inmenu", "Mi&nimize"), ("action:inmenu", "&Fullscreen"),
        ("@action:inmenu", "&No Titlebar and Frame"), ("@action:inmenu", "&Hide from Screencast"),
        ("@action:inmenu", "&Close All"), ("@action:inmenu", "&Close")]
] + [
    ("plasma_containmentactions_contextmenu", None, "Open Terminal"),
    ("plasma_containmentactions_contextmenu", "plasma_containmentactions_contextmenu", "Lock Screen"),
    ("plasma_containmentactions_contextmenu", "plasma_containmentactions_contextmenu", "Show Logout Screen"),
    ("plasma_containmentactions_contextmenu", "plasma_containmentactions_contextmenu", "Display Configuration"),
    ("plasma_applet_org.kde.desktopcontainment", "@action:inmenu opens config dialog", "Desktop and Wallpaper"),
    ("plasma_wallpaper_org.kde.image", None, "Open Wallpaper Image"),
    ("libplasma6", None, "Enter Edit Mode"), ("libplasma6", None, "Exit Edit Mode"),
    ("libplasma6", None, "Add or Manage Widgets…"),
]


def unquote(s):
    return s[1:-1].encode("utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8")


def parse(path):
    """Entradas {(ctx, msgid): (msgstr)} de un .po (sin plurales: no se usan aquí)."""
    entries, cur, field = {}, {}, None
    def flush():
        if "msgid" in cur and "msgstr" in cur and not cur.get("obsolete"):
            entries[(cur.get("msgctxt"), cur["msgid"])] = cur["msgstr"]
        cur.clear()
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            flush(); field = None; continue
        if line.startswith("#~"):
            cur["obsolete"] = True; continue
        if line.startswith("#"):
            continue
        for key in ("msgctxt", "msgid_plural", "msgid", "msgstr[0]", "msgstr"):
            if line.startswith(key + " "):
                if key == "msgctxt" and "msgid" in cur:
                    flush()
                field = key; cur[key] = unquote(line[len(key) + 1:]); break
        else:
            if line.startswith('"') and field:
                cur[field] += unquote(line)
    flush()
    return entries


def quote(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def main(src, out):
    src, out = Path(src), Path(out)
    langs = sorted({p.parent.name for p in src.glob("*/po/*/*.po")})
    out.mkdir(parents=True, exist_ok=True)
    for lang in langs:
        cache, lines = {}, []
        for domain, ctx, msgid in WANTED:
            if domain not in cache:
                files = list(src.glob(f"*/po/{lang}/{domain}.po"))
                cache[domain] = parse(files[0]) if files else {}
            msgstr = cache[domain].get((ctx, msgid), "")
            if not msgstr:
                continue
            lines.append("")
            if ctx is not None:
                lines.append("msgctxt " + quote(ctx))
            lines += ["msgid " + quote(msgid), "msgstr " + quote(msgstr)]
        if not lines:
            continue
        header = ['# Catálogo de los menús portados de Breeze (BWM, F9). Cadenas y traducciones de KDE 6.7.5:',
                  '# kwin, plasma-desktop, plasma-workspace y libplasma (GPL-2.0-or-later / LGPL); generado por extract.py.',
                  'msgid ""', 'msgstr ""', '"Content-Type: text/plain; charset=UTF-8\\n"', f'"Language: {lang}\\n"']
        (out / f"{lang}.po").write_text("\n".join(header + lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
