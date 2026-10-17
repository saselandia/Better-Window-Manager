#!/usr/bin/env bash
# ==============================================================================
# Script: theme-picker.sh
# Descripción: Selector interactivo de temas para BWM
# ==============================================================================

set -euo pipefail

ROFI_THEME="$HOME/.config/rofi/theme-picker.rasi"
THEME_MANAGER="$HOME/.config/hypr/scripts/bwm-theme-manager.py"

OPTIONS="🎨 Default (Material You)\n❄️ Retro Frost (Omarchy Cyan)\n🌹 Retro Ash (Omarchy Dark Rose)\n⚡ Retro Cyberpunk (Omarchy Neon)"

# Obtener tema actual para preseleccionar
CURRENT_THEME="$("$THEME_MANAGER" get 2>/dev/null || echo "default")"
SELECTED_ROW=0
case "$CURRENT_THEME" in
    "default") SELECTED_ROW=0 ;;
    "retro") SELECTED_ROW=1 ;;
    "retro-ash") SELECTED_ROW=2 ;;
    "retro-cyberpunk") SELECTED_ROW=3 ;;
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
    2) "$THEME_MANAGER" set retro-ash ;;
    3) "$THEME_MANAGER" set retro-cyberpunk ;;
    *) exit 0 ;;
esac
