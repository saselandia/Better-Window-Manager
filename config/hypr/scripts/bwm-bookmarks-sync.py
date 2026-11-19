#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sincronizador común de favoritos/lugares entre Nautilus (GTK 3/4) y Dolphin (KDE).

Pieza común a todas las skins de BWM:
  - Al iniciar sesión (`startup` o `start`), reúne los favoritos existentes de
    ~/.config/gtk-3.0/bookmarks y ~/.local/share/user-places.xbel sin borrar ninguno.
  - Después (`watch` / `sync`), sincroniza altas, cambios de nombre y eliminaciones
    en ambos sentidos usando un estado previo (~/.local/state/bwm/bookmarks-sync.json)
    para distinguir una eliminación de un marcador nuevo y evitar que reaparezcan
    los borrados.
  - Vigila las carpetas padre con una única instancia inotify (con fallback a polling
    si se agota la cuota del kernel) para sobrevivir a sustituciones atómicas al guardar,
    y agrupa los avisos próximos (debounce) en una sola sincronización.
  - Conserva todas las entradas especiales de KDE (isSystemItem, remote:/, trash:/,
    timeline:/, UDI, isHidden, onlyInApp, <info> raíz, iconos, IDs y metadatos extra).
  - Si detecta un archivo a medias o cambios simultáneos no conciliables con seguridad,
    conserva la información sin sobrescribirla y vuelve a intentar la sincronización.

Uso:
  bwm-bookmarks-sync.py startup
  bwm-bookmarks-sync.py sync
  bwm-bookmarks-sync.py watch [--no-startup]
  bwm-bookmarks-sync.py start
  bwm-bookmarks-sync.py stop
  bwm-bookmarks-sync.py status
"""

from __future__ import annotations

import argparse
import ctypes
import errno
import fcntl
import hashlib
import json
import os
import re
import select
import signal
import struct
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import quote, unquote, urlsplit, urlunsplit

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

NS_BOOKMARK = "http://www.freedesktop.org/standards/desktop-bookmarks"
NS_KDEPRIV = "http://www.kde.org/kdepriv"
NS_MIME = "http://www.freedesktop.org/standards/shared-mime-info"
OWNER_FDO = "http://freedesktop.org"
OWNER_KDE = "http://www.kde.org"

ET.register_namespace("bookmark", NS_BOOKMARK)
ET.register_namespace("kdepriv", NS_KDEPRIV)
ET.register_namespace("mime", NS_MIME)

SYNCABLE_SCHEMES = frozenset({
    "file", "sftp", "smb", "ftp", "ftps", "dav", "davs", "nfs", "afp", "ssh",
})

# inotify masks (Linux <sys/inotify.h>)
IN_MODIFY = 0x00000002
IN_ATTRIB = 0x00000004
IN_CLOSE_WRITE = 0x00000008
IN_MOVED_FROM = 0x00000040
IN_MOVED_TO = 0x00000080
IN_CREATE = 0x00000100
IN_DELETE = 0x00000200
IN_DELETE_SELF = 0x00000400
IN_MOVE_SELF = 0x00000800
IN_Q_OVERFLOW = 0x00004000
WATCH_MASK = (
    IN_CLOSE_WRITE | IN_MOVED_FROM | IN_MOVED_TO | IN_CREATE
    | IN_DELETE | IN_DELETE_SELF | IN_MOVE_SELF | IN_ATTRIB
)

DEFAULT_DEBOUNCE_SECS = 0.35
DEFAULT_MAX_DEBOUNCE_SECS = 2.0
DEFAULT_RETRY_DELAYS = (0.75, 1.5, 3.0, 6.0)


class IncompleteFileError(Exception):
    """Raised when a bookmark file appears truncated or malformed mid-write."""


def default_gtk_path() -> Path:
    cfg = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return cfg / "gtk-3.0" / "bookmarks"


def default_kde_path() -> Path:
    data = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return data / "user-places.xbel"


def default_state_dir() -> Path:
    state = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return state / "bwm"


def default_state_path() -> Path:
    return default_state_dir() / "bookmarks-sync.json"


def default_lock_path() -> Path:
    return default_state_dir() / "bookmarks-sync.lock"


def sha256_bytes(data: Optional[bytes]) -> str:
    if data is None:
        return ""
    return hashlib.sha256(data).hexdigest()


def is_syncable_uri(uri: str) -> bool:
    uri = uri.strip()
    if not uri:
        return False
    try:
        parts = urlsplit(uri)
    except ValueError:
        return False
    scheme = parts.scheme.lower()
    if scheme not in SYNCABLE_SCHEMES:
        return False
    if scheme == "file":
        return bool(parts.path)
    return bool(parts.netloc or parts.path)


def normalize_uri(uri: str) -> str:
    """Canonical URI for stable matching between GTK bookmarks and KDE XBEL."""
    parts = urlsplit(uri.strip())
    scheme = parts.scheme.lower()
    netloc = parts.netloc
    if scheme == "file" and netloc.lower() in ("", "localhost"):
        netloc = ""
    raw_path = unquote(parts.path)
    if len(raw_path) > 1:
        raw_path = raw_path.rstrip("/") or "/"
    encoded_path = quote(raw_path, safe="/:@!$&'()*+,;=-._~")
    if scheme == "file":
        return f"file://{netloc}{encoded_path}"
    return urlunsplit((scheme, netloc, encoded_path, parts.query, parts.fragment))


def default_label(uri: str) -> str:
    parts = urlsplit(uri)
    path = unquote(parts.path).rstrip("/")
    if path:
        base = os.path.basename(path)
        if base:
            return base
    if parts.scheme.lower() == "file":
        return "/"
    return parts.netloc or uri


def effective_label(uri: str, label: str) -> str:
    cleaned = label.strip()
    return cleaned if cleaned else default_label(uri)


# ── GTK bookmarks (~/.config/gtk-3.0/bookmarks) ──────────────────────────────

@dataclass
class GtkEntry:
    canon: str
    raw_uri: str
    label: str
    explicit_label: bool = True


@dataclass
class GtkDocument:
    entries: List[GtkEntry]
    extra_lines: List[str]
    existed: bool

    def by_canon(self) -> Dict[str, GtkEntry]:
        return {e.canon: e for e in self.entries}


def parse_gtk_bookmarks(raw: Optional[bytes]) -> GtkDocument:
    if raw is None:
        return GtkDocument(entries=[], extra_lines=[], existed=False)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise IncompleteFileError(f"GTK bookmarks UTF-8 inválido: {exc}") from exc

    entries: List[GtkEntry] = []
    extra_lines: List[str] = []
    seen: Set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        uri_part, sep, rest = line.rstrip("\r\n").partition(" ")
        uri_part = uri_part.strip()
        if not is_syncable_uri(uri_part):
            extra_lines.append(line.rstrip("\r\n"))
            continue
        canon = normalize_uri(uri_part)
        if canon in seen:
            continue
        seen.add(canon)
        raw_label = rest.strip() if sep else ""
        entries.append(GtkEntry(
            canon=canon,
            raw_uri=canon,
            label=effective_label(canon, raw_label),
            explicit_label=bool(raw_label),
        ))
    return GtkDocument(entries=entries, extra_lines=extra_lines, existed=True)


def render_gtk_bookmarks(doc: GtkDocument) -> bytes:
    lines: List[str] = []
    for entry in doc.entries:
        uri = entry.raw_uri or entry.canon
        lbl = entry.label.strip()
        if lbl:
            lines.append(f"{uri} {lbl}")
        else:
            lines.append(uri)
    lines.extend(doc.extra_lines)
    content = ("\n".join(lines) + "\n") if lines else ""
    return content.encode("utf-8")


# ── KDE places (~/.local/share/user-places.xbel) ─────────────────────────────

@dataclass
class KdeEntry:
    canon: str
    href: str
    label: str
    element: ET.Element


@dataclass
class KdeDocument:
    root: ET.Element
    user_entries: List[KdeEntry]
    system_uris: Set[str]
    all_ids: Set[str]
    extra_xmlns: Dict[str, str]
    existed: bool

    def by_canon(self) -> Dict[str, KdeEntry]:
        return {e.canon: e for e in self.user_entries}


def _kde_metadata(elem: ET.Element) -> Optional[ET.Element]:
    info = elem.find("info")
    if info is None:
        return None
    for meta in info.findall("metadata"):
        if meta.attrib.get("owner") == OWNER_KDE:
            return meta
    return None


def _kde_meta_text(meta: Optional[ET.Element], tag: str) -> str:
    if meta is None:
        return ""
    child = meta.find(tag)
    return (child.text or "").strip() if child is not None else ""


def _extract_root_xmlns(text: str) -> Dict[str, str]:
    match = re.search(r"<xbel\b([^>]*)>", text, flags=re.DOTALL)
    if not match:
        return {}
    attrs = match.group(1)
    return dict(re.findall(r'xmlns:([A-Za-z_][\w.-]*)\s*=\s*"([^"]*)"', attrs))


def _create_empty_kde_root() -> ET.Element:
    root = ET.Element("xbel")
    info = ET.SubElement(root, "info")
    meta = ET.SubElement(info, "metadata", {"owner": OWNER_KDE})
    ver = ET.SubElement(meta, "kde_places_version")
    ver.text = "4"
    return root


def parse_kde_places(raw: Optional[bytes]) -> KdeDocument:
    if raw is None:
        return KdeDocument(
            root=_create_empty_kde_root(),
            user_entries=[],
            system_uris=set(),
            all_ids=set(),
            extra_xmlns={},
            existed=False,
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise IncompleteFileError(f"user-places.xbel UTF-8 inválido: {exc}") from exc

    if not text.strip():
        raise IncompleteFileError("user-places.xbel vacío durante lectura")

    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise IncompleteFileError(f"user-places.xbel XML incompleto: {exc}") from exc

    if root.tag != "xbel":
        raise IncompleteFileError(f"Raíz inesperada en user-places.xbel: {root.tag}")

    extra_xmlns = _extract_root_xmlns(text)
    user_entries: List[KdeEntry] = []
    system_uris: Set[str] = set()
    all_ids: Set[str] = set()
    seen_user: Set[str] = set()

    for child in list(root):
        if child.tag != "bookmark":
            continue
        meta = _kde_metadata(child)
        bid = _kde_meta_text(meta, "ID")
        if bid:
            all_ids.add(bid)

        href = (child.attrib.get("href") or "").strip()
        is_system = _kde_meta_text(meta, "isSystemItem").lower() == "true"
        is_hidden = _kde_meta_text(meta, "isHidden").lower() == "true"
        only_in_app = _kde_meta_text(meta, "onlyInApp")
        udi = _kde_meta_text(meta, "UDI")

        if is_system and not is_hidden and is_syncable_uri(href):
            system_uris.add(normalize_uri(href))

        if is_system or is_hidden or only_in_app or udi or not is_syncable_uri(href):
            continue

        canon = normalize_uri(href)
        if canon in seen_user:
            continue
        seen_user.add(canon)
        title = (child.findtext("title") or "").strip()
        user_entries.append(KdeEntry(
            canon=canon,
            href=href,
            label=effective_label(canon, title),
            element=child,
        ))

    return KdeDocument(
        root=root,
        user_entries=user_entries,
        system_uris=system_uris,
        all_ids=all_ids,
        extra_xmlns=extra_xmlns,
        existed=True,
    )


def _next_kde_id(doc: KdeDocument) -> str:
    stamp = int(time.time())
    seq = 0
    while True:
        candidate = f"{stamp}/{seq}"
        if candidate not in doc.all_ids:
            doc.all_ids.add(candidate)
            return candidate
        seq += 1


def kde_add_bookmark(doc: KdeDocument, canon_uri: str, label: str) -> KdeEntry:
    bm = ET.SubElement(doc.root, "bookmark", {"href": canon_uri})
    title = ET.SubElement(bm, "title")
    title.text = effective_label(canon_uri, label)
    info = ET.SubElement(bm, "info")

    fdo = ET.SubElement(info, "metadata", {"owner": OWNER_FDO})
    scheme = urlsplit(canon_uri).scheme.lower()
    icon_name = "folder" if scheme == "file" else "folder-remote"
    ET.SubElement(fdo, f"{{{NS_BOOKMARK}}}icon", {"name": icon_name})

    kde = ET.SubElement(info, "metadata", {"owner": OWNER_KDE})
    bid = ET.SubElement(kde, "ID")
    bid.text = _next_kde_id(doc)

    entry = KdeEntry(canon=canon_uri, href=canon_uri, label=title.text, element=bm)
    doc.user_entries.append(entry)
    return entry


def kde_set_title(entry: KdeEntry, new_label: str) -> None:
    title = entry.element.find("title")
    if title is None:
        title = ET.Element("title")
        entry.element.insert(0, title)
    title.text = effective_label(entry.canon, new_label)
    entry.label = title.text


def kde_remove_bookmark(doc: KdeDocument, entry: KdeEntry) -> None:
    doc.root.remove(entry.element)
    doc.user_entries = [e for e in doc.user_entries if e is not entry]


def render_kde_places(doc: KdeDocument) -> bytes:
    ET.indent(doc.root, space=" ")
    xml_body = ET.tostring(doc.root, encoding="unicode")
    # Preserve the standard KDE XBEL namespace declarations on <xbel ...>
    required_ns = {
        "bookmark": NS_BOOKMARK,
        "kdepriv": NS_KDEPRIV,
        "mime": NS_MIME,
    }
    merged_ns = {**required_ns, **doc.extra_xmlns}
    match = re.match(r"<xbel\b([^>]*)>", xml_body)
    if match:
        existing_attrs = match.group(1)
        present = set(re.findall(r'xmlns:([A-Za-z_][\w.-]*)\s*=', existing_attrs))
        missing = "".join(
            f' xmlns:{prefix}="{uri}"'
            for prefix, uri in merged_ns.items()
            if prefix not in present
        )
        if missing:
            xml_body = f"<xbel{existing_attrs}{missing}>" + xml_body[match.end():]
    full = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xbel>\n' + xml_body + "\n"
    return full.encode("utf-8")


# ── Atomic I/O ───────────────────────────────────────────────────────────────

def read_bytes_or_none(path: Path) -> Optional[bytes]:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def file_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = None
    try:
        mode = path.stat().st_mode & 0o777
    except OSError:
        pass
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        if mode is not None:
            os.chmod(tmp, mode)
        os.replace(tmp, path)
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise


# ── 3-way synchronization engine ─────────────────────────────────────────────

class BookmarksSync:
    def __init__(
        self,
        gtk_path: Optional[Path] = None,
        kde_path: Optional[Path] = None,
        state_path: Optional[Path] = None,
    ):
        self.gtk_path = Path(gtk_path) if gtk_path else default_gtk_path()
        self.kde_path = Path(kde_path) if kde_path else default_kde_path()
        self.state_path = Path(state_path) if state_path else default_state_path()

    def load_state(self) -> Optional[dict]:
        raw = read_bytes_or_none(self.state_path)
        if raw is None:
            return None
        try:
            data = json.loads(raw.decode("utf-8"))
            if isinstance(data, dict) and isinstance(data.get("entries"), dict):
                return data
        except (ValueError, UnicodeDecodeError):
            pass
        return None

    def save_state(
        self,
        entries: Dict[str, dict],
        order: List[str],
        gtk_hash: str,
        kde_hash: str,
        last_conflict: Optional[dict] = None,
    ) -> None:
        payload = {
            "version": 1,
            "entries": entries,
            "order": order,
            "gtk_hash": gtk_hash,
            "kde_hash": kde_hash,
            "updated_at": round(time.time(), 3),
        }
        if last_conflict:
            payload["last_conflict"] = last_conflict
        atomic_write(
            self.state_path,
            (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8"),
        )

    def _build_state_entries(
        self, gtk_doc: GtkDocument, kde_doc: KdeDocument
    ) -> Tuple[Dict[str, dict], List[str]]:
        entries: Dict[str, dict] = {}
        order: List[str] = []
        gtk_map = gtk_doc.by_canon()
        kde_map = kde_doc.by_canon()
        for canon in list(gtk_map.keys()) + [u for u in kde_map.keys() if u not in gtk_map]:
            g = gtk_map.get(canon)
            k = kde_map.get(canon)
            label = g.label if g else k.label
            entries[canon] = {
                "label": label,
                "kde_system": (canon in kde_doc.system_uris and k is None),
            }
            order.append(canon)
        return entries, order

    def _pick_startup_label(
        self,
        canon: str,
        gtk_entry: GtkEntry,
        kde_entry: KdeEntry,
        prev_entries: Dict[str, dict],
        gtk_mtime: float,
        kde_mtime: float,
    ) -> str:
        if gtk_entry.label == kde_entry.label:
            return gtk_entry.label
        prev = prev_entries.get(canon)
        if prev:
            prev_lbl = prev.get("label", "")
            if gtk_entry.label != prev_lbl and kde_entry.label == prev_lbl:
                return gtk_entry.label
            if kde_entry.label != prev_lbl and gtk_entry.label == prev_lbl:
                return kde_entry.label
        dflt = default_label(canon)
        gtk_custom = gtk_entry.label != dflt
        kde_custom = kde_entry.label != dflt
        if gtk_custom and not kde_custom:
            return gtk_entry.label
        if kde_custom and not gtk_custom:
            return kde_entry.label
        return kde_entry.label if kde_mtime > gtk_mtime else gtk_entry.label

    def startup(self) -> dict:
        """Session-start union: merges bookmarks from both managers without deleting any."""
        gtk_raw = read_bytes_or_none(self.gtk_path)
        kde_raw = read_bytes_or_none(self.kde_path)
        try:
            gtk_doc = parse_gtk_bookmarks(gtk_raw)
            kde_doc = parse_kde_places(kde_raw)
        except IncompleteFileError as exc:
            return {"status": "retry", "reason": str(exc), "retry": True}

        prev = self.load_state() or {}
        prev_entries = prev.get("entries", {}) if isinstance(prev.get("entries"), dict) else {}
        gtk_mtime = file_mtime(self.gtk_path)
        kde_mtime = file_mtime(self.kde_path)

        gtk_map = gtk_doc.by_canon()
        kde_map = kde_doc.by_canon()
        union_uris = list(gtk_map.keys()) + [u for u in kde_map.keys() if u not in gtk_map]

        gtk_dirty = False
        kde_dirty = False
        added_to_gtk = 0
        added_to_kde = 0
        renamed = 0

        for canon in union_uris:
            g = gtk_map.get(canon)
            k = kde_map.get(canon)
            if g and k:
                chosen = self._pick_startup_label(canon, g, k, prev_entries, gtk_mtime, kde_mtime)
                if g.label != chosen:
                    g.label = chosen
                    gtk_dirty = True
                    renamed += 1
                if k.label != chosen:
                    kde_set_title(k, chosen)
                    kde_dirty = True
                    renamed += 1
            elif g and not k:
                if canon not in kde_doc.system_uris:
                    kde_add_bookmark(kde_doc, canon, g.label)
                    kde_dirty = True
                    added_to_kde += 1
            elif k and not g:
                gtk_doc.entries.append(GtkEntry(canon=canon, raw_uri=canon, label=k.label))
                gtk_dirty = True
                added_to_gtk += 1

        new_gtk_raw = gtk_raw
        new_kde_raw = kde_raw
        gtk_written = False
        kde_written = False

        if gtk_dirty:
            rendered = render_gtk_bookmarks(gtk_doc)
            if rendered != gtk_raw:
                atomic_write(self.gtk_path, rendered)
                new_gtk_raw = rendered
                gtk_written = True

        if kde_dirty:
            rendered = render_kde_places(kde_doc)
            if rendered != kde_raw:
                atomic_write(self.kde_path, rendered)
                new_kde_raw = rendered
                kde_written = True

        state_entries, order = self._build_state_entries(gtk_doc, kde_doc)
        self.save_state(
            state_entries,
            order,
            sha256_bytes(new_gtk_raw),
            sha256_bytes(new_kde_raw),
        )
        return {
            "status": "synced" if (gtk_written or kde_written) else "noop",
            "mode": "startup",
            "gtk_written": gtk_written,
            "kde_written": kde_written,
            "added_to_gtk": added_to_gtk,
            "added_to_kde": added_to_kde,
            "renamed": renamed,
            "total": len(state_entries),
        }

    def sync_once(self) -> dict:
        """Bidirectional 3-way reconciliation using the last saved snapshot."""
        state = self.load_state()
        if state is None:
            return self.startup()

        gtk_raw = read_bytes_or_none(self.gtk_path)
        kde_raw = read_bytes_or_none(self.kde_path)
        gtk_hash = sha256_bytes(gtk_raw)
        kde_hash = sha256_bytes(kde_raw)

        if gtk_hash == state.get("gtk_hash", "") and kde_hash == state.get("kde_hash", ""):
            return {"status": "noop", "gtk_written": False, "kde_written": False}

        try:
            gtk_doc = parse_gtk_bookmarks(gtk_raw)
            kde_doc = parse_kde_places(kde_raw)
        except IncompleteFileError as exc:
            return {"status": "retry", "reason": str(exc), "retry": True}

        base: Dict[str, dict] = state.get("entries", {})
        gtk_map = gtk_doc.by_canon()
        kde_map = kde_doc.by_canon()

        # Logical label views for 3-way diffing.
        # If a URI is covered by a visible KDE isSystemItem, KDE did NOT delete it.
        gtk_view: Dict[str, str] = {u: e.label for u, e in gtk_map.items()}
        kde_view: Dict[str, str] = {u: e.label for u, e in kde_map.items()}
        for u, info in base.items():
            if u not in kde_view and info.get("kde_system") and u in kde_doc.system_uris:
                kde_view[u] = info["label"]

        # Preserve stable ordering: base order, then GTK additions, then KDE additions.
        all_uris: List[str] = []
        seen: Set[str] = set()
        for seq in (state.get("order", []), list(base.keys()), list(gtk_map.keys()), list(kde_map.keys())):
            for u in seq:
                if u not in seen:
                    seen.add(u)
                    all_uris.append(u)

        def op_for(view: Dict[str, str], uri: str) -> Tuple[str, Optional[str]]:
            in_base = uri in base
            in_now = uri in view
            if not in_base and not in_now:
                return ("same", None)
            if not in_base and in_now:
                return ("add", view[uri])
            if in_base and not in_now:
                return ("del", None)
            if view[uri] == base[uri]["label"]:
                return ("same", view[uri])
            return ("ren", view[uri])

        conflicts: List[dict] = []
        decisions: Dict[str, Tuple[str, Optional[str]]] = {}  # uri -> ("keep"|"set"|"del", label)

        for u in all_uris:
            gop = op_for(gtk_view, u)
            kop = op_for(kde_view, u)

            if gop == kop:
                if gop[0] == "del":
                    decisions[u] = ("del", None)
                elif gop[0] in ("add", "ren"):
                    decisions[u] = ("set", gop[1])
                else:
                    decisions[u] = ("keep", gop[1])
            elif gop[0] == "same":
                if kop[0] == "del":
                    decisions[u] = ("del", None)
                else:
                    decisions[u] = ("set", kop[1])
            elif kop[0] == "same":
                if gop[0] == "del":
                    decisions[u] = ("del", None)
                else:
                    decisions[u] = ("set", gop[1])
            else:
                # Both sides changed the same URI incompatibly (add vs add with different names,
                # rename vs rename to different names, or delete vs rename).
                conflicts.append({
                    "uri": u,
                    "gtk": {"op": gop[0], "label": gop[1]},
                    "kde": {"op": kop[0], "label": kop[1]},
                })

        if conflicts:
            # Preserve both files untouched and keep previous base state so we can safely retry.
            return {
                "status": "conflict",
                "retry": True,
                "conflicts": conflicts,
                "gtk_written": False,
                "kde_written": False,
            }

        gtk_dirty = False
        kde_dirty = False
        summary = {"added": 0, "renamed": 0, "deleted": 0}

        for u in all_uris:
            action, target_label = decisions[u]
            g = gtk_map.get(u)
            k = kde_map.get(u)

            if action == "del":
                if g is not None:
                    gtk_doc.entries = [e for e in gtk_doc.entries if e.canon != u]
                    gtk_dirty = True
                    summary["deleted"] += 1
                if k is not None:
                    kde_remove_bookmark(kde_doc, k)
                    kde_dirty = True
                    summary["deleted"] += 1
            elif action == "set":
                assert target_label is not None
                if g is None:
                    gtk_doc.entries.append(GtkEntry(canon=u, raw_uri=u, label=target_label))
                    gtk_dirty = True
                    summary["added"] += 1
                elif g.label != target_label:
                    g.label = target_label
                    gtk_dirty = True
                    summary["renamed"] += 1

                if k is None:
                    if u not in kde_doc.system_uris:
                        kde_add_bookmark(kde_doc, u, target_label)
                        kde_dirty = True
                        summary["added"] += 1
                elif k.label != target_label:
                    kde_set_title(k, target_label)
                    kde_dirty = True
                    summary["renamed"] += 1

        new_gtk_raw = gtk_raw
        new_kde_raw = kde_raw
        gtk_written = False
        kde_written = False

        if gtk_dirty:
            rendered = render_gtk_bookmarks(gtk_doc)
            if rendered != gtk_raw:
                atomic_write(self.gtk_path, rendered)
                new_gtk_raw = rendered
                gtk_written = True

        if kde_dirty:
            rendered = render_kde_places(kde_doc)
            if rendered != kde_raw:
                atomic_write(self.kde_path, rendered)
                new_kde_raw = rendered
                kde_written = True

        state_entries, order = self._build_state_entries(gtk_doc, kde_doc)
        self.save_state(
            state_entries,
            order,
            sha256_bytes(new_gtk_raw),
            sha256_bytes(new_kde_raw),
        )
        return {
            "status": "synced" if (gtk_written or kde_written) else "noop",
            "gtk_written": gtk_written,
            "kde_written": kde_written,
            "changes": summary,
            "total": len(state_entries),
        }


# ── Directory watcher (single inotify instance + polling fallback) ───────────

class DirectoryWatcher:
    """Watches parent directories of both bookmark files so atomic renames are caught.

    Uses a single Linux inotify instance via libc (zero extra dependencies) and falls
    back to hash polling if the session exhausts its inotify instance quota.
    """

    EVENT_HDR = struct.Struct("iIII")

    def __init__(self, target_files: List[Path]):
        self.targets = [Path(p) for p in target_files]
        self.lib = ctypes.CDLL(None, use_errno=True)
        self.fd = self.lib.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
        if self.fd < 0 and ctypes.get_errno() not in (errno.EMFILE, errno.ENOSPC):
            raise OSError(ctypes.get_errno(), "inotify_init1")
        self.wd_to_dir: Dict[int, Path] = {}
        self.dir_to_wd: Dict[Path, int] = {}
        self.expected_names: Dict[Path, Set[str]] = {}
        self.poll_hashes = self._snapshot_hashes()
        self.refresh()

    def _snapshot_hashes(self) -> Dict[str, str]:
        return {str(p): sha256_bytes(read_bytes_or_none(p)) for p in self.targets}

    def refresh(self) -> None:
        wanted: Dict[Path, Set[str]] = {}
        for target in self.targets:
            parent = target.parent
            expected = target.name
            cur = parent
            while not cur.exists() and cur != cur.parent:
                expected = cur.name
                cur = cur.parent
            resolved = cur.resolve() if cur.exists() else cur
            wanted.setdefault(resolved, set()).add(expected)

        self.expected_names = wanted
        if self.fd < 0:
            return

        # Drop watches for directories we no longer need (e.g. ancestor once child exists)
        for folder in list(self.dir_to_wd.keys()):
            if folder not in wanted:
                wd = self.dir_to_wd.pop(folder)
                self.wd_to_dir.pop(wd, None)
                self.lib.inotify_rm_watch(self.fd, wd)

        for folder in wanted:
            if folder in self.dir_to_wd:
                continue
            wd = self.lib.inotify_add_watch(self.fd, os.fsencode(folder), WATCH_MASK)
            if wd < 0:
                err = ctypes.get_errno()
                if err in (errno.EMFILE, errno.ENOSPC):
                    self._fallback_to_polling()
                    return
                continue
            self.dir_to_wd[folder] = wd
            self.wd_to_dir[wd] = folder

    def _fallback_to_polling(self) -> None:
        if self.fd >= 0:
            try:
                os.close(self.fd)
            except OSError:
                pass
            self.fd = -1
        self.wd_to_dir.clear()
        self.dir_to_wd.clear()
        self.poll_hashes = self._snapshot_hashes()

    def wait_relevant(self, timeout: float) -> bool:
        """Wait up to `timeout` seconds; return True if a relevant filesystem event occurred."""
        if self.fd < 0:
            time.sleep(max(0.0, timeout))
            now_hashes = self._snapshot_hashes()
            changed = now_hashes != self.poll_hashes
            self.poll_hashes = now_hashes
            self.refresh()
            return changed

        try:
            ready = bool(select.select([self.fd], [], [], max(0.0, timeout))[0])
        except InterruptedError:
            return False
        if not ready:
            return False

        relevant = False
        needs_refresh = False
        while True:
            try:
                buf = os.read(self.fd, 65536)
            except BlockingIOError:
                break
            if not buf:
                break
            offset = 0
            hdr_size = self.EVENT_HDR.size
            while offset + hdr_size <= len(buf):
                wd, mask, _cookie, name_len = self.EVENT_HDR.unpack_from(buf, offset)
                offset += hdr_size
                raw_name = buf[offset:offset + name_len]
                offset += name_len
                name = raw_name.split(b"\x00", 1)[0].decode("utf-8", errors="surrogateescape")

                if mask & (IN_Q_OVERFLOW | IN_DELETE_SELF | IN_MOVE_SELF):
                    relevant = True
                    needs_refresh = True
                    continue

                folder = self.wd_to_dir.get(wd)
                if folder is None:
                    continue
                expected = self.expected_names.get(folder, set())
                if name in expected:
                    relevant = True
                    # If an ancestor directory saw the missing child directory created, refresh watches
                    if any(t.parent.name == name for t in self.targets):
                        needs_refresh = True

        if needs_refresh:
            self.refresh()
        return relevant

    def close(self) -> None:
        if self.fd >= 0:
            try:
                os.close(self.fd)
            except OSError:
                pass
            self.fd = -1


# ── Daemon loop & lifecycle ──────────────────────────────────────────────────

def run_watch_loop(
    syncer: BookmarksSync,
    *,
    do_startup: bool = True,
    debounce_secs: float = DEFAULT_DEBOUNCE_SECS,
    max_debounce_secs: float = DEFAULT_MAX_DEBOUNCE_SECS,
    retry_delays: Tuple[float, ...] = DEFAULT_RETRY_DELAYS,
    stop_check=None,
    on_result=None,
) -> None:
    if do_startup:
        res = syncer.startup()
        if on_result:
            on_result(res)

    watcher = DirectoryWatcher([syncer.gtk_path, syncer.kde_path])
    pending_since: Optional[float] = None
    debounce_until: Optional[float] = None
    retry_at: Optional[float] = None
    retry_index = 0

    try:
        while not (stop_check and stop_check()):
            now = time.monotonic()
            timeout = 1.0
            if debounce_until is not None:
                timeout = min(timeout, max(0.0, debounce_until - now))
            if retry_at is not None:
                timeout = min(timeout, max(0.0, retry_at - now))

            if watcher.wait_relevant(timeout):
                ev_now = time.monotonic()
                if pending_since is None:
                    pending_since = ev_now
                debounce_until = min(ev_now + debounce_secs, pending_since + max_debounce_secs)
                # Fresh filesystem activity resets retry backoff
                retry_index = 0
                retry_at = None

            now = time.monotonic()
            due_debounce = debounce_until is not None and now >= debounce_until
            due_retry = retry_at is not None and now >= retry_at
            if due_debounce or due_retry:
                pending_since = None
                debounce_until = None
                retry_at = None
                watcher.refresh()
                res = syncer.sync_once()
                if on_result:
                    on_result(res)
                if res.get("retry"):
                    if retry_index < len(retry_delays):
                        retry_at = time.monotonic() + retry_delays[retry_index]
                        retry_index += 1
                else:
                    retry_index = 0
    finally:
        watcher.close()


def _running_pid(lock_path: Path) -> Optional[int]:
    if not lock_path.exists():
        return None
    try:
        fd = os.open(lock_path, os.O_RDWR)
    except OSError:
        return None
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(fd, fcntl.LOCK_UN)
            return None
        except BlockingIOError:
            text = os.read(fd, 32).decode("ascii", errors="ignore").strip()
            pid = int(text) if text.isdigit() else None
            if pid and Path(f"/proc/{pid}/cmdline").exists():
                args = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
                if str(Path(__file__).resolve()).encode() in args and b"watch" in args:
                    return pid
            return None
    except OSError:
        return None
    finally:
        os.close(fd)


def cmd_watch(no_startup: bool = False) -> int:
    lock_path = default_lock_path()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a+") as guard:
        try:
            fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0
        guard.seek(0)
        guard.truncate()
        guard.write(f"{os.getpid()}\n")
        guard.flush()

        stopping = False

        def handle_signal(_signum, _frame):
            nonlocal stopping
            stopping = True

        signal.signal(signal.SIGTERM, handle_signal)
        signal.signal(signal.SIGINT, handle_signal)

        def log_result(res: dict):
            if res.get("status") != "noop":
                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{ts}] {json.dumps(res, ensure_ascii=False)}", flush=True)

        run_watch_loop(
            BookmarksSync(),
            do_startup=not no_startup,
            stop_check=lambda: stopping,
            on_result=log_result,
        )
    return 0


def cmd_start() -> int:
    lock_path = default_lock_path()
    pid = _running_pid(lock_path)
    if pid is not None:
        print(json.dumps({"status": "already-running", "pid": pid}))
        return 0
    import bwm_session
    log_path = str(default_state_dir() / "bookmarks-sync.log")
    default_state_dir().mkdir(parents=True, exist_ok=True)
    launched = bwm_session.spawn([sys.executable, str(Path(__file__).resolve()), "watch"], log=log_path)
    print(json.dumps({"status": "started" if launched else "failed", "log": log_path}))
    return 0 if launched else 1


def cmd_stop() -> int:
    lock_path = default_lock_path()
    pid = _running_pid(lock_path)
    if pid is None:
        print(json.dumps({"status": "not-running"}))
        return 0
    try:
        os.kill(pid, signal.SIGTERM)
        for _ in range(100):
            if _running_pid(lock_path) is None:
                break
            time.sleep(0.05)
    except OSError:
        pass
    print(json.dumps({"status": "stopped", "pid": pid}))
    return 0


def cmd_status() -> int:
    lock_path = default_lock_path()
    pid = _running_pid(lock_path)
    syncer = BookmarksSync()
    state = syncer.load_state()
    print(json.dumps({
        "running": pid is not None,
        "pid": pid,
        "gtk_path": str(syncer.gtk_path),
        "kde_path": str(syncer.kde_path),
        "state_path": str(syncer.state_path),
        "tracked_count": len(state.get("entries", {})) if state else 0,
        "updated_at": state.get("updated_at") if state else None,
    }, ensure_ascii=False, indent=2))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Sincronizador de favoritos entre Nautilus y Dolphin")
    sub = parser.add_subparsers(dest="action")
    sub.add_parser("startup", help="Reúne los favoritos existentes de ambos gestores sin borrar ninguno")
    sub.add_parser("sync", help="Ejecuta una conciliación bidireccional puntual")
    watch_p = sub.add_parser("watch", help="Vigila ambas carpetas y sincroniza en segundo plano")
    watch_p.add_argument("--no-startup", action="store_true", help="Omitir la unión inicial al arrancar")
    sub.add_parser("start", help="Arranca el vigilante como proceso de sesión")
    sub.add_parser("stop", help="Detiene el vigilante")
    sub.add_parser("status", help="Muestra el estado del vigilante y del último guardado")

    args = parser.parse_args(argv)
    if args.action == "startup":
        print(json.dumps(BookmarksSync().startup(), ensure_ascii=False))
        return 0
    if args.action == "sync":
        print(json.dumps(BookmarksSync().sync_once(), ensure_ascii=False))
        return 0
    if args.action == "watch":
        return cmd_watch(no_startup=args.no_startup)
    if args.action == "start":
        return cmd_start()
    if args.action == "stop":
        return cmd_stop()
    if args.action == "status":
        return cmd_status()
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
