#!/usr/bin/env python3
"""Catálogo oficial de skins. Sólo metadatos; no instala ni ejecuta código remoto."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import bwm_skins

REPO = Path(__file__).resolve().parents[3]
INDEX = REPO / "catalog/skins.json"
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "bwm/extra-skin-catalog-v2.json"
GITHUB = "https://github.com/saselandia/bwm-skins"
GITLAB = "https://gitlab.com/saselandia/bwm-skins"
SOURCES = ["https://raw.githubusercontent.com/saselandia/bwm-skins/main/catalog/skins.json",
           GITLAB + "/-/raw/main/catalog/skins.json"]
MAX_BYTES = 1024 * 1024


def https_url(value):
    if not isinstance(value, str) or len(value) > 2048 or any(ord(c) < 32 for c in value):
        raise ValueError("Enlace no válido en el catálogo")
    url = urlsplit(value)
    if url.scheme != "https" or not url.hostname or url.username or url.password:
        raise ValueError("Los enlaces del catálogo deben ser HTTPS")
    return value


def validate(data):
    if not isinstance(data, dict) or (data.get("schemaVersion") != 2 or data.get("catalogId") != "bwm-extra-skins") or not isinstance(data.get("skins"), list):
        raise ValueError("Formato de catálogo no reconocido")
    if len(data["skins"]) > 300:
        raise ValueError("El catálogo contiene demasiadas entradas")
    ids, entries = set(), []
    for entry in data["skins"]:
        if not isinstance(entry, dict):
            raise ValueError("Entrada de catálogo no válida")
        sid = entry.get("id")
        if not isinstance(sid, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", sid) or sid in ids:
            raise ValueError("Id de skin inválido o duplicado")
        if sid in bwm_skins.ORDER:
            raise ValueError("Las tres skins incluidas en BWM no forman parte del catálogo externo")
        ids.add(sid)
        for key in ("name", "description", "imitates", "version", "compatibility"):
            if not isinstance(entry.get(key), str) or not entry[key].strip() or len(entry[key]) > 2048:
                raise ValueError(f"La skin {sid} necesita {key}")
        if entry.get("delivery") != "external-release":
            raise ValueError("El catálogo sólo admite releases de skins externas")
        entries.append({**{k: entry[k] for k in ("id", "name", "description", "imitates", "version", "compatibility", "delivery")},
                        **{k: https_url(entry.get(k)) for k in ("previewUrl", "sourceUrl", "installationUrl")}})
    return {"schemaVersion": 2, "catalogId": "bwm-extra-skins", "skins": entries}


def build(repo):
    """Genera el catálogo del repo externo a partir de skins/<id>/catalog.json."""
    if not (repo / "skins").is_dir():
        raise ValueError("La ruta debe ser el repositorio bwm-skins, con su carpeta skins/")
    entries = []
    for path in sorted((repo / "skins").glob("*/catalog.json")):
        if path.parent.name.startswith("_"):
            continue
        entry = json.loads(path.read_text(encoding="utf-8"))
        if entry.get("id") != path.parent.name:
            raise ValueError(f"El id no coincide con la carpeta: {path}")
        entries.append(entry)
    return validate({"schemaVersion": 2, "catalogId": "bwm-extra-skins", "skins": entries})


def read_index(path):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("El catálogo supera el tamaño permitido")
    return validate(json.loads(path.read_text(encoding="utf-8")))


def save_cache(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, prefix=".skins-", delete=False, encoding="utf-8") as stream:
        temporary = Path(stream.name)
        json.dump(data, stream, ensure_ascii=False)
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def fetch(url):
    request = Request(url, headers={"User-Agent": "BWM-Skin-Catalog/1.0", "Accept": "application/json"})
    with urlopen(request, timeout=6) as response:
        https_url(response.geturl())
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("El catálogo supera el tamaño permitido")
    return validate(json.loads(raw))


def catalog(refresh=False, local=False, cache=CACHE, index=INDEX):
    cached = None
    try:
        cached = read_index(cache)
        if not refresh and not local and time.time() - cache.stat().st_mtime < 3600:
            return cached, "cache", ""
    except (OSError, ValueError):
        pass
    if not local:
        for url in SOURCES:
            try:
                data = fetch(url)
                try:
                    save_cache(data, cache)
                except OSError:
                    pass  # Una caché no escribible no invalida un catálogo válido.
                return data, "remote", ""
            except (OSError, ValueError):
                continue
    if cached is not None and not local:
        return cached, "cache", "Sin conexión: catálogo guardado."
    return read_index(index), "bundled", "" if local else "Sin conexión: no se pudo consultar el catálogo de skins adicionales."


def discover(refresh=False, local=False):
    data, source, warning = catalog(refresh, local)
    installed = {skin["id"]: skin for skin in bwm_skins.all_skins()}
    entries = []
    for entry in data["skins"]:
        existing = installed.get(entry["id"])
        preview = ""
        if existing:
            path = Path(existing.get("preview", ""))
            if not path.is_absolute():
                path = REPO / path
            if path.is_file():
                preview = path.as_uri()
        entries.append({**entry, "installed": bool(existing), "preview": preview or entry["previewUrl"],
                        "status": "Instalada" if existing else "Disponible por separado"})
    entries.sort(key=lambda entry: entry["installed"])
    return {"skins": entries, "source": source, "warning": warning, "repository": GITHUB, "mirror": GITLAB,
            "publishingGuide": (REPO / "docs/SKIN_CATALOG.md").as_uri()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("discover", "build"))
    parser.add_argument("--catalog-root", type=Path, help="checkout del repositorio bwm-skins (para build)")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--local", action="store_true", help="sólo el catálogo incluido")
    parser.add_argument("--check", action="store_true", help="comprueba si el índice generado está actualizado")
    args = parser.parse_args()
    try:
        if args.action == "build":
            if args.catalog_root is None:
                raise ValueError("Indica --catalog-root con la ruta del repositorio bwm-skins")
            output = args.catalog_root.resolve() / "catalog/skins.json"
            data = build(args.catalog_root.resolve())
            if args.check:
                if read_index(output) != data:
                    raise ValueError("Regenera el índice con build --catalog-root /ruta/bwm-skins")
                print("Catálogo actualizado")
            else:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(f"Catálogo generado: {len(data['skins'])} skins")
        else:
            print(json.dumps(discover(args.refresh, args.local), ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"skins": [], "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
