#!/usr/bin/env bash
set -euo pipefail

source_dir="$(dirname -- "${BASH_SOURCE[0]}")/../applications"
data_dir="${XDG_DATA_HOME:-}"
[[ "$data_dir" == /* ]] || data_dir="$HOME/.local/share"
applications="$data_dir/applications"
entry="$applications/org.bwm.menu.desktop"

# Respetar una entrada existente, incluida una que el usuario haya ocultado.
if [[ -e "$entry" || -L "$entry" ]]; then
    exit 0
fi

mkdir -p -- "$applications"
staging="$(mktemp --tmpdir="$applications" .bwmenu.XXXXXXXX)"
trap 'rm -f -- "$staging"' EXIT
install -m644 -- "$source_dir/org.bwm.menu.desktop" "$staging"
mv -nT -- "$staging" "$entry"
