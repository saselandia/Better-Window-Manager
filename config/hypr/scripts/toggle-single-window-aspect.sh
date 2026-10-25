#!/usr/bin/env bash
# ==============================================================================
# Script: toggle-single-window-aspect.sh
# Descripción: Conmuta la proporción cuadrada (1:1) para ventana única en Hyprland.
#              Port de omarchy-hyprland-window-single-square-aspect-toggle (MIT).
#              Evita que una única ventana se estire en exceso en monitores panorámicos.
# Uso: toggle-single-window-aspect.sh [on|off|toggle|status]
# ==============================================================================

set -euo pipefail

STATE="${XDG_STATE_HOME:-$HOME/.local/state}/bwm/single-window-aspect"

apply_state() {
    local mode="$1"
    if [[ "$mode" == "on" ]]; then
        mkdir -p "$(dirname "$STATE")"
        touch "$STATE"
        hyprctl eval 'hl.config({ layout = { single_window_aspect_ratio = { 1, 1 } } })' >/dev/null 2>&1 || true
        command -v notify-send >/dev/null 2>&1 && notify-send -a "BWM" -i "window" "Proporción de ventana única" "Proporción cuadrada activada (1:1)" || true
        echo "on"
    else
        rm -f "$STATE"
        hyprctl eval 'hl.config({ layout = { single_window_aspect_ratio = { 0, 0 } } })' >/dev/null 2>&1 || true
        command -v notify-send >/dev/null 2>&1 && notify-send -a "BWM" -i "window" "Proporción de ventana única" "Proporción estándar restaurada" || true
        echo "off"
    fi
}

ACTION="${1:-toggle}"

case "$ACTION" in
    on)
        apply_state "on"
        ;;
    off)
        apply_state "off"
        ;;
    status)
        if [[ -f "$STATE" ]]; then
            echo "on"
        else
            echo "off"
        fi
        ;;
    toggle)
        if [[ -f "$STATE" ]]; then
            apply_state "off"
        else
            apply_state "on"
        fi
        ;;
    *)
        echo "Uso: $0 [on|off|toggle|status]" >&2
        exit 1
        ;;
esac
