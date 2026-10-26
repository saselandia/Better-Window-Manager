#!/usr/bin/env bash
# ==============================================================================
# Selector de estilos (skins: Default, Retro, KDE Plasma) con el carrusel 3D de los temas
# Retro (modules/ii/bar/omarchy/image-picker/ImagePicker.qml, source "skins").
#
#   skin-switcher.sh               abre el carrusel
#   skin-switcher.sh --print-rows  miniaturas (fondo de cada estilo, 1280x800 PNG) para el carrusel
#
# El nombre del archivo es la etiqueta del carrusel; ImagePicker lo traduce al estilo
# (Default -> default, Retro -> retro, KDE Plasma -> plasma).
# ==============================================================================
set -uo pipefail

CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/bwm/skin-switcher"
mkdir -p "$CACHE"

preview() {  # <skin> <etiqueta>
    local skin="$1" label="$2" wp out="$CACHE/$2.png"
    wp="$(tr -d '\n' < "$HOME/.cache/current_wallpaper_$skin" 2>/dev/null)"
    [[ -f "$wp" ]] || wp="$HOME/.config/hypr/omarchy/themes/$(ls "$HOME/.config/hypr/omarchy/themes" | head -1)/preview.png"
    # Se rehace si cambia el fondo del estilo (Qt de Quickshell no decodifica WebP: siempre PNG)
    if [[ ! -f "$out" || "$wp" -nt "$out" || "$(cat "$out.src" 2>/dev/null)" != "$wp" ]]; then
        if magick "$wp[0]" -resize 1280x800^ -gravity center -extent 1280x800 "$out.tmp.png" 2>/dev/null; then
            mv -f "$out.tmp.png" "$out"
            printf '%s' "$wp" > "$out.src"
        else
            rm -f "$out.tmp.png"
        fi
    fi
    [[ -f "$out" ]] && printf '%s\t%s\n' "$out" "$out"
}

if [[ "${1:-}" == "--print-rows" ]]; then
    preview default "Default"
    preview retro "Retro"
    preview plasma "KDE Plasma"
    exit 0
fi

exec qs -c ii ipc call omarchy.image-picker openPayload '{"source":"skins"}'
