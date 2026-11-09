#!/usr/bin/env bash
# Compile Omacalc (MIT) for BWM without sudo. Source and licenses stay installed.
# Usage: install-omacalc.sh [--force]
set -euo pipefail
repo="https://github.com/omacom/omacalc.git"
revision="573d7106f5c6c0225864eb8634ae37ddcb657f63"
scripts=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
data="${XDG_DATA_HOME:-$HOME/.local/share}"
root="$data/bwm/omacalc"
bin_dir="$HOME/.local/bin"
export GIT_TERMINAL_PROMPT=0

if [[ -x $root/bin/omacalc && -f $root/build-info && ${1:-} != --force ]] &&
   grep -qx "bwm-omacalc 1 $revision" "$root/build-info"; then
    echo "Omacalc ya está instalado ($revision)."
    exit 0
fi
for tool in git make c++ qmake6 pkg-config patch; do
    if ! command -v "$tool" >/dev/null; then
        echo "Falta $tool para compilar Omacalc. Consulta docs/REQUIREMENTS.md (omacalc-build)." >&2
        exit 1
    fi
done
pkg-config --print-errors --exists Qt6Core Qt6Gui Qt6Qml Qt6Quick Qt6QuickControls2 Qt6DBus
if [[ -e $bin_dir/omacalc && ! ( -L $bin_dir/omacalc && $(readlink "$bin_dir/omacalc") == "$scripts/bwm-omacalc" ) ]]; then
    echo "$bin_dir/omacalc ya existe y no pertenece a BWM; no se sobrescribe." >&2
    exit 1
fi
mkdir -p "$root" "$bin_dir"
if [[ ! -d $root/source/.git ]]; then
    git clone --quiet --no-checkout "$repo" "$root/source"
fi
git -C "$root/source" fetch --quiet --depth 1 origin "$revision"
# Build a clean export; never reset a developer's source checkout.
work=$(mktemp -d "$root/build.XXXXXX")
trap 'rm -r "$work"' EXIT
git -C "$root/source" archive "$revision" | tar -x -C "$work"
patch --batch --forward -d "$work" -p1 < "$scripts/../omacalc/theme-path.patch"
mkdir "$work/build"
jobs=$(nproc)
(( jobs <= 8 )) || jobs=8
(
    cd "$work/build"
    qmake6 "$work/omacalc.pro"
    make -j"$jobs"
)
install -Dm755 "$work/build/omacalc" "$root/bin/omacalc.new.$$"
mv "$root/bin/omacalc.new.$$" "$root/bin/omacalc"
install -Dm644 "$work/LICENSE" "$root/share/licenses/MIT.txt"
install -Dm644 "$work/fonts/OFL.txt" "$root/share/licenses/iA-Writer-Mono-OFL.txt"
install -Dm644 "$scripts/../omacalc/theme-path.patch" "$root/share/theme-path.patch"
install -Dm644 "$work/pkgbuild/omacalc.svg" "$data/icons/hicolor/scalable/apps/omacalc.svg"
mkdir -p "$data/applications"
sed "s|^Exec=.*|Exec=$bin_dir/omacalc|" "$work/pkgbuild/omacalc.desktop" > "$data/applications/omacalc.desktop"
ln -sfn "$scripts/bwm-omacalc" "$bin_dir/omacalc"
printf 'bwm-omacalc 1 %s\n' "$revision" > "$root/build-info"
# Seed from the active shell's common M3 roles without reapplying a wallpaper
# or restarting any app. Later theme changes render the same Matugen template.
python3 - "$scripts" <<'PY'
import json, os, sys
from pathlib import Path
scripts = Path(sys.argv[1])
state = Path.home() / ".local/state"
try:
    roles = json.loads((state / "quickshell/user/generated/colors.json").read_text())
    content = (scripts.parent.parent / "matugen/templates/omacalc-colors.toml").read_text()
    for key, value in roles.items():
        content = content.replace("{{colors." + key + ".default.hex}}", value)
    if "{{" not in content:
        target = state / "bwm/omacalc/colors.toml"
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_text() != content:
            temporary = target.with_name(target.name + f".{os.getpid()}.tmp")
            temporary.write_text(content)
            temporary.replace(target)
except (OSError, ValueError):
    pass  # A first-ever palette will arrive on the next wallpaper/theme change.
PY
if command -v update-desktop-database >/dev/null; then
    update-desktop-database "$data/applications"
fi
echo "Omacalc instalado en $root/bin, disponible como omacalc y en Apps."
