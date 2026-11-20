#!/usr/bin/env python3
"""Install upstream Yaru icon assets for legacy/community Omarchy icons.theme.

No root, GTK theme, cursor, or system package changes. Existing icon themes stay.
The upstream index generator is used with the same inheritance as its Meson build.
"""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

VERSION = "25.10.3"
COMMIT = "a35be2896824db2e738d3c88511375d7c7737985"
URL = f"https://codeload.github.com/ubuntu/yaru/tar.gz/{COMMIT}"
SHA256 = "25bbbb3236f28d6adf7b1c104a86ef9157acaf114c9eeff10619d36f1da5eec8"


def install(archive=None):
    home = Path.home()
    destination = Path(os.environ.get("XDG_DATA_HOME", home / ".local/share")) / "icons"
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bwm-yaru-") as tmp:
        work = Path(tmp)
        if archive is None:
            archive = work / "source.tar.gz"
            print(f"Downloading Yaru {VERSION} from ubuntu/yaru", flush=True)
            with urllib.request.urlopen(URL, timeout=60) as response, archive.open("wb") as output:
                shutil.copyfileobj(response, output)
        archive = Path(archive)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
            raise ValueError("Yaru archive checksum mismatch")
        with tarfile.open(archive) as source:
            source.extractall(work / "source", filter="data")
        root = work / "source" / f"yaru-{COMMIT}" / "icons"
        generator = root / "src/generate-index-theme.py"
        themes = sorted(path for path in root.glob("Yaru*") if path.is_dir() and path.name != "Yaru-mate")
        # Meson uses Yaru-dark's symbolic icons for each dark color variant.
        for base in list(themes):
            if base.name in ("Yaru", "Yaru-dark"):
                continue
            dark = root / (base.name + "-dark")
            if not dark.exists():
                shutil.copytree(root / "Yaru-dark", dark, symlinks=True)
                themes.append(dark)
        licenses = [root / name for name in ("COPYING", "LICENSE_CCBYSA", "LICENSE_GPL3", "AUTHORS")]
        for theme in themes:
            target = destination / theme.name
            if target.exists() or target.is_symlink():
                print(f"Keeping existing {theme.name}", flush=True)
                continue
            args = [sys.executable, str(generator), theme.name, "--source-dir", str(theme), "--output-dir", str(theme)]
            if theme.name == "Yaru-dark":
                args += ["--inherits", "Yaru"]
            elif theme.name.endswith("-dark"):
                args += ["--inherits", "Yaru-dark", "--inherits", theme.name[:-5]]
            elif theme.name != "Yaru":
                args += ["--inherits", "Yaru"]
            subprocess.run(args, check=True, stdout=subprocess.DEVNULL)
            staged = Path(tempfile.mkdtemp(prefix=".bwm-yaru-", dir=destination))
            try:
                shutil.copytree(theme, staged, symlinks=True, dirs_exist_ok=True)
                for license_file in licenses:
                    shutil.copy2(license_file, staged / license_file.name)
                (staged / ".bwm-yaru-source").write_text(f"{VERSION}\n{COMMIT}\n{URL}\n", encoding="utf-8")
                if not target.exists() and not target.is_symlink():
                    staged.rename(target)
                    print(f"Installed {theme.name}", flush=True)
            finally:
                if staged.exists():
                    shutil.rmtree(staged)
    print("Yaru icons installed; reapply the Retro theme to select them.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="use an already downloaded archive (same checksum required)")
    install(parser.parse_args().archive)
