#!/usr/bin/env bash
# ==============================================================================
# Script: theme-picker.sh
# Descripción: Selector interactivo de temas para BWM (Default vs Retro)
# ==============================================================================

set -euo pipefail

ROFI_THEME="$HOME/.config/rofi/theme-picker.rasi"
THEME_MANAGER="$HOME/.config/hypr/scripts/bwm-theme-manager.py"

OPTIONS="🎨 Default (Material You)\n📼 Retro (Omarchy Minimalist)"

# Obtener tema actual para preseleccionar
CURRENT_THEME="$("$THEME_MANAGER" get 2>/dev/null || echo "default")"
SELECTED_ROW=0
if [ "$CURRENT_THEME" = "retro" ]; then
    SELECTED_ROW=1
fi

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
    0)
        "$THEME_MANAGER" set default
        ;;
    1)
        "$THEME_MANAGER" set retro
        ;;
    *)
        exit 0
        ;;
esac
