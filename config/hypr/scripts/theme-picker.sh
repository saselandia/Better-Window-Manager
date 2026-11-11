#!/usr/bin/env bash
# ==============================================================================
# Script: theme-picker.sh
# Descripción: Selector interactivo de estilos (skins) de BWM (Default, Retro, KDE Plasma)
#              Cambia dinámicamente de aspecto según el estilo activo.
# ==============================================================================

set -euo pipefail

THEME_MANAGER="$HOME/.config/hypr/scripts/bwm-theme-manager.py"
CURRENT_THEME="$("$THEME_MANAGER" get 2>/dev/null || echo "default")"

# Breeze uses BWM's common skin gallery. Plasma global themes live in Preferences.
if [[ "$CURRENT_THEME" == "plasma" ]]; then
    exec "$HOME/.config/hypr/scripts/bwm-menu.py" --open
fi

# Retro: el carrusel 3D de los temas Retro, con los estilos (skin-switcher.sh)
if [[ "$CURRENT_THEME" == "retro" ]] && "$HOME/.config/hypr/scripts/skin-switcher.sh" >/dev/null 2>&1; then
    exit 0
fi

if [[ "$CURRENT_THEME" == "retro" ]]; then
    ROFI_THEME="$HOME/.config/rofi/theme-picker-retro.rasi"
elif [[ "$CURRENT_THEME" == "plasma" ]]; then
    ROFI_THEME="$HOME/.config/rofi/theme-picker-plasma.rasi"
else
    ROFI_THEME="$HOME/.config/rofi/theme-picker.rasi"
fi

OPTIONS="🎨 default (end-4)\n⚡ Retro (Omarchy)\n❄️ Breeze (Kde plasma)"

SELECTED_ROW=0
case "$CURRENT_THEME" in
    "default") SELECTED_ROW=0 ;;
    "retro")   SELECTED_ROW=1 ;;
    "plasma")  SELECTED_ROW=2 ;;
    *)         SELECTED_ROW=0 ;;
esac

CHOICE=$(echo -e "$OPTIONS" | rofi -dmenu \
    -theme "$ROFI_THEME" \
    -p "󰔎 Estilo BWM" \
    -selected-row "$SELECTED_ROW" \
    -format "i" \
    -hover-select \
    -me-select-entry '' \
    -me-accept-entry 'MousePrimary' || true)

if [ -z "$CHOICE" ] || ! [[ "$CHOICE" =~ ^[0-9]+$ ]]; then
    exit 0
fi

case "$CHOICE" in
    0) "$THEME_MANAGER" set default ;;
    1) "$THEME_MANAGER" set retro ;;
    2) "$THEME_MANAGER" set plasma ;;
    *) exit 0 ;;
esac
