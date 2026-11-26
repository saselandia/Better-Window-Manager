#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Install or update ~/.local/share/applications/systemsettings.desktop for Breeze.

Copies the system systemsettings.desktop verbatim (preserving all translations, icons,
OnlyShowIn and Desktop Actions) and rewrites only Exec=systemsettings[...] lines to
invoke systemsettings-desktop.sh, which injects BWM's KCMs only when Breeze is active.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import tempfile

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE = Path("/usr/share/applications/systemsettings.desktop")
DEFAULT_WRAPPER = SCRIPT_DIR / "systemsettings-desktop.sh"
EXEC_RE = re.compile(r"^Exec=systemsettings(?=\s|$)(.*)$")


def render_desktop(source_text: str, wrapper: Path) -> str:
    wrapper_str = str(wrapper)
    out_lines = []
    for line in source_text.splitlines():
        m = EXEC_RE.match(line)
        if m:
            out_lines.append(f"Exec={wrapper_str}{m.group(1)}")
        else:
            out_lines.append(line)
    return "\n".join(out_lines) + ("\n" if source_text.endswith("\n") else "")


def sync_desktop(source: Path, dest: Path, wrapper: Path) -> bool:
    if not source.is_file():
        return False
    rendered = render_desktop(source.read_text(encoding="utf-8"), wrapper)
    if dest.is_file():
        try:
            if dest.read_text(encoding="utf-8") == rendered:
                return False
        except OSError:
            pass
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=dest.parent, prefix=".systemsettings-", suffix=".tmp", delete=False
    ) as tmp:
        tmp.write(rendered)
        tmp_path = Path(tmp.name)
    os.chmod(tmp_path, 0o644)
    os.replace(tmp_path, dest)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument(
        "--dest",
        type=Path,
        default=Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
        / "applications"
        / "systemsettings.desktop",
    )
    parser.add_argument("--wrapper", type=Path, default=DEFAULT_WRAPPER)
    args = parser.parse_args()
    sync_desktop(args.source, args.dest, args.wrapper)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
