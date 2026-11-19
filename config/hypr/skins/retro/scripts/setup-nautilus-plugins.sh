#!/usr/bin/env bash
# Instala (enlaza) las extensiones nautilus-python de Omarchy para la skin Retro
# sin pisar archivos propios que el usuario tenga en ~/.local/share/nautilus-python/extensions.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "$SCRIPT_DIR/../nautilus-python/extensions" && pwd)"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
DST_DIR="$DATA_HOME/nautilus-python/extensions"

mkdir -p "$DST_DIR"

for src in "$SRC_DIR"/*.py; do
    [ -f "$src" ] || continue
    name="$(basename "$src")"
    dst="$DST_DIR/$name"
    if [ -L "$dst" ]; then
        target="$(readlink -f "$dst" 2>/dev/null || true)"
        real_src="$(readlink -f "$src" 2>/dev/null || echo "$src")"
        # Actualizar sólo si ya apunta al propio paquete/repo o está roto
        if [ -z "$target" ] || [ ! -e "$dst" ] || [ "$target" = "$real_src" ] || [[ "$target" == *"/skins/retro/nautilus-python/extensions/$name" ]]; then
            ln -sfn "$src" "$dst"
        fi
    elif [ ! -e "$dst" ]; then
        ln -s "$src" "$dst"
    fi
done
