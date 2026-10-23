#!/usr/bin/env bash
# ==============================================================================
# Script: theme-picker.sh
# Descripción: Selector interactivo de temas para BWM (Default, Retro, KDE Plasma)
#              Cambia dinámicamente de aspecto según el tema activo.
# ==============================================================================

set -euo pipefail

THEME_MANAGER="$HOME/.config/hypr/scripts/bwm-theme-manager.py"
CURRENT_THEME="$("$THEME_MANAGER" get 2>/dev/null || echo "default")"

# Tema Plasma: selector nativo de Quickshell (estilo "Tema global" de KDE)
if [[ "$CURRENT_THEME" == "plasma" ]] && qs -c ii ipc call plasmaThemePicker toggle >/dev/null 2>&1; then
    exit 0
fi

if [[ "$CURRENT_THEME" == "retro" ]]; then
    ROFI_THEME="$HOME/.config/rofi/theme-picker-retro.rasi"
elif [[ "$CURRENT_THEME" == "plasma" ]]; then
    ROFI_THEME="$HOME/.config/rofi/theme-picker-plasma.rasi"
else
    ROFI_THEME="$HOME/.config/rofi/theme-picker.rasi"
fi

OPTIONS="🎨 Default (Material You)\n⚡ Retro (Omarchy)\n❄️ KDE Plasma (Breeze Dark)"

SELECTED_ROW=0
case "$CURRENT_THEME" in
    "default") SELECTED_ROW=0 ;;
    "retro")   SELECTED_ROW=1 ;;
    "plasma")  SELECTED_ROW=2 ;;
    *)         SELECTED_ROW=0 ;;
esac

CHOICE=$(echo -e "$OPTIONS" | rofi -dmenu \
    -theme "$ROFI_THEME" \
    -p "󰔎 Tema BWM" \
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
