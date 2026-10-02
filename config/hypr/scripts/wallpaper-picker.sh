#!/usr/bin/env bash
# ==============================================================================
# Script: wallpaper-picker.sh
# Descripción: Selector gráfico orgánico de fondos de pantalla estilo Material You.
#              Genera miniaturas en paralelo y muestra una cuadrícula visual interactiva.
# ==============================================================================

set -euo pipefail

WALLPAPER_DIR="$HOME/Pictures/Wallpapers"
CACHE_DIR="$HOME/.cache/wallpaper-thumbnails"
ROFI_THEME="$HOME/.config/rofi/wallpaper-picker.rasi"
SET_WALLPAPER="$HOME/.config/hypr/scripts/set-wallpaper.sh"

mkdir -p "$WALLPAPER_DIR" "$CACHE_DIR"

# Directorios de búsqueda de fondos
SEARCH_DIRS=(
    "$WALLPAPER_DIR"
    "$HOME/Pictures"
    "$HOME/Downloads"
    "/usr/share/backgrounds"
)

# Recopilar imágenes válidas
mapfile -t IMAGES < <(
    for dir in "${SEARCH_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            find "$dir" -maxdepth 2 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" \) 2>/dev/null
        fi
    done | sort -u
)

if [ ${#IMAGES[@]} -eq 0 ]; then
    notify-send "Wallpaper Picker" "No se encontraron imágenes en ~/Pictures o ~/Downloads"
    exit 1
fi

# Generar miniaturas faltantes en paralelo usando Python multihilo ultrarrápido
python3 - "${CACHE_DIR}" "${IMAGES[@]}" << 'EOF'
import sys, os, hashlib, subprocess
from concurrent.futures import ThreadPoolExecutor

cache_dir = sys.argv[1]
images = sys.argv[2:]

def gen(img):
    try:
        h = hashlib.md5(img.encode()).hexdigest()
        thumb = os.path.join(cache_dir, f"{h}.png")
        if not os.path.exists(thumb) or os.path.getmtime(img) > os.path.getmtime(thumb):
            subprocess.run(
                ["ffmpeg", "-v", "error", "-threads", "1", "-i", img,
                 "-vf", "scale=240:135:force_original_aspect_ratio=decrease,pad=240:135:(ow-iw)/2:(oh-ih)/2:black@0",
                 thumb, "-y"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
    except Exception:
        pass

with ThreadPoolExecutor(max_workers=8) as ex:
    list(ex.map(gen, images))
EOF

# Generar lista con miniaturas para Rofi
ROFI_INPUT=""
for img in "${IMAGES[@]}"; do
    hash=$(echo -n "$img" | md5sum | cut -d' ' -f1)
    thumb="$CACHE_DIR/${hash}.png"
    filename=$(basename "$img")

    if [ -f "$thumb" ]; then
        ROFI_INPUT+="${filename}\0icon\x1f${thumb}\x1finfo\x1f${img}\n"
    else
        ROFI_INPUT+="${filename}\0info\x1f${img}\n"
    fi
done

# Lanzar Rofi en modo selector visual (-format "i" devuelve el índice numérico exacto)
SELECTED_INDEX=$(echo -en "$ROFI_INPUT" | rofi -dmenu -theme "$ROFI_THEME" -p "󰸉 Fondo" -format "i" -hover-select -me-select-entry '' -me-accept-entry 'MousePrimary' || true)

if [ -z "$SELECTED_INDEX" ] || ! [[ "$SELECTED_INDEX" =~ ^[0-9]+$ ]]; then
    exit 0
fi

SELECTED_PATH="${IMAGES[$SELECTED_INDEX]:-}"

if [ -n "$SELECTED_PATH" ] && [ -f "$SELECTED_PATH" ]; then
    "$SET_WALLPAPER" "$SELECTED_PATH"
fi
