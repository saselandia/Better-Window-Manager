#!/usr/bin/env bash
# ==============================================================================
# Selector de estilos (skins: Default, Retro, KDE Plasma) con el carrusel 3D de los temas
# Retro (modules/ii/bar/omarchy/image-picker/ImagePicker.qml, source "skins").
#
#   skin-switcher.sh               abre el carrusel
#   skin-switcher.sh --print-rows  miniaturas (captura de lo que imita cada estilo, 1280x800 PNG)
#
# El nombre del archivo es la etiqueta del carrusel; ImagePicker lo traduce al estilo
# (Default -> default, Retro -> retro, KDE Plasma -> plasma).
# ==============================================================================
set -uo pipefail

CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/bwm/skin-switcher"
mkdir -p "$CACHE"

REPO="$(cd "$(dirname "$(readlink -f "$0")")/../../.." && pwd)"
SHOTS="$REPO/assets/skin-previews"   # capturas de lo que imita cada estilo (README.md ahí)

# Retro: la captura oficial de Omarchy del tema Retro activo (su escritorio con ventanas);
# con la paleta dinámica, la de Tokyo Night, el tema por defecto de Omarchy
retro_shot() {
    local name themes="$HOME/.config/hypr/omarchy/themes"
    name="$(tr -d '\n' < "$HOME/.local/state/bwm/omarchy/theme.name" 2>/dev/null)"
    if [[ -n "$name" && -f "$themes/$name/preview.png" ]]; then
        printf '%s' "$themes/$name/preview.png"
    else
        printf '%s' "$themes/tokyo-night/preview.png"
    fi
}

preview() {  # <imagen> <etiqueta>
    local src="$1" label="$2" key out
    [[ -f "$src" ]] || return 0
    # Miniatura 1280x800 en una carpeta por imagen de origen: si cambia, cambia la ruta y
    # Quickshell no enseña la que tenía en caché
    key="$(printf '%s %s' "$src" "$(stat -c %Y "$src")" | md5sum | cut -c1-12)"
    out="$CACHE/$key/$label.png"
    if [[ ! -f "$out" ]]; then
        mkdir -p "$CACHE/$key"
        magick "$src[0]" -resize 1280x800^ -gravity center -extent 1280x800 "$out.tmp.png" 2>/dev/null \
            && mv -f "$out.tmp.png" "$out" || rm -f "$out.tmp.png"
    fi
    [[ -f "$out" ]] && printf '%s\t%s\n' "$out" "$out"
}

if [[ "${1:-}" == "--print-rows" ]]; then
    preview "$SHOTS/end4-illogical-impulse.png" "Default"
    preview "$(retro_shot)" "Retro"
    preview "$SHOTS/kde-plasma-6.png" "KDE Plasma"
    exit 0
fi

exec qs -c ii ipc call omarchy.image-picker openPayload '{"source":"skins"}'
