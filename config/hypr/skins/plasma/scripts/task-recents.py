#!/usr/bin/env python3
"""Archivos recientes de una aplicación para el menú del gestor de tareas de Breeze (F9).

  task-recents.py list <id del .desktop> [--limit N]    JSON [{name, uri, path}] más recientes primero
  task-recents.py open <id del .desktop> <uri>          abre el archivo con esa aplicación

En Plasma la sección «Archivos recientes» la da el backend del applet taskmanager (KActivities) con
recentDocumentActions(). Sin ese backend (plasma-desktop no se instala) se usa el registro común de
freedesktop, ~/.local/share/recently-used.xbel, que escriben GTK, Qt/KDE (KRecentDocument) y las
apps: cada archivo lista las aplicaciones que lo abrieron (bookmark:application, con su Exec).
Sólo lee; no escribe nada.
"""
from __future__ import annotations

import argparse
import configparser
import json
import os
import shlex
import subprocess
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

DATA = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
XBEL = DATA / "recently-used.xbel"
NS = {"bookmark": "http://www.freedesktop.org/standards/desktop-bookmarks",
      "mime": "http://www.freedesktop.org/standards/shared-mime-info"}


def desktop_file(app_id: str) -> Path | None:
    name = app_id if app_id.endswith(".desktop") else app_id + ".desktop"
    dirs = [DATA] + [Path(d) for d in (os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":") if d]
    for d in dirs:
        candidate = d / "applications" / name
        if candidate.is_file():
            return candidate
    # Sin distinguir mayúsculas (los app_id de Wayland a veces no coinciden en caja)
    for d in dirs:
        folder = d / "applications"
        if folder.is_dir():
            for f in folder.glob("*.desktop"):
                if f.name.lower() == name.lower():
                    return f
    return None


def app_keys(app_id: str) -> set[str]:
    """Nombres con que la app aparece en el registro: id, nombre, binario del Exec."""
    keys = {app_id.lower().removesuffix(".desktop")}
    path = desktop_file(app_id)
    if path:
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        try:
            parser.read(path, encoding="utf-8")
            entry = parser["Desktop Entry"]
            if entry.get("Name"):
                keys.add(entry["Name"].lower())
            exec_line = entry.get("Exec", "")
            argv = [a for a in shlex.split(exec_line) if not a.startswith("%")] if exec_line else []
            # flatpak run <id>, env FOO=1 prog…: el programa real
            while argv and (argv[0] in ("env", "flatpak") or "=" in argv[0] or argv[0] == "run" or argv[0].startswith("--")):
                argv.pop(0)
            if argv:
                keys.add(Path(argv[0]).name.lower())
        except (configparser.Error, KeyError, ValueError):
            pass
    return {k for k in keys if k}


def recents(app_id: str, limit: int = 5) -> list[dict]:
    try:
        root = ET.parse(XBEL).getroot()
    except (OSError, ET.ParseError):
        return []
    keys = app_keys(app_id)
    found = []
    for bm in root.findall("bookmark"):
        uri = bm.get("href", "")
        apps = bm.findall("info/metadata/bookmark:applications/bookmark:application", NS)
        stamp = ""
        match = False
        for app in apps:
            name = (app.get("name") or "").lower()
            exec_bin = Path(shlex.split(app.get("exec", "'x'"))[0].strip("'\"")).name.lower() if app.get("exec") else ""
            if name in keys or exec_bin in keys:
                match = True
                stamp = max(stamp, app.get("modified", ""))
        if not match:
            continue
        path = urllib.parse.unquote(urllib.parse.urlparse(uri).path) if uri.startswith("file://") else ""
        if path and not Path(path).exists():
            continue  # como KActivities: no se ofrecen archivos que ya no existen
        name = (bm.findtext("title") or Path(path).name or uri).strip()
        found.append({"name": name, "uri": uri, "path": path, "stamp": stamp or bm.get("modified", "")})
    found.sort(key=lambda r: r["stamp"], reverse=True)
    return [{k: r[k] for k in ("name", "uri", "path")} for r in found[:limit]]


def open_with(app_id: str, uri: str) -> int:
    path = desktop_file(app_id)
    if path:
        return subprocess.Popen(["gio", "launch", str(path), uri], start_new_session=True,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) and 0
    return subprocess.Popen(["xdg-open", uri], start_new_session=True,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) and 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list")
    p.add_argument("app")
    p.add_argument("--limit", type=int, default=5)
    p = sub.add_parser("open")
    p.add_argument("app")
    p.add_argument("uri")
    args = parser.parse_args(argv)
    if args.cmd == "list":
        print(json.dumps(recents(args.app, args.limit), ensure_ascii=False))
        return 0
    return open_with(args.app, args.uri)


if __name__ == "__main__":
    sys.exit(main())
