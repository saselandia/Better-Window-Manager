#!/usr/bin/env bash
# ==============================================================================
# Script: app-launcher.sh
# Descripción: Lanza el menú de aplicaciones según el tema activo:
#              - Plasma (KDE): Rofi Kickoff launcher en esquina inferior izquierda.
#              - Retro (Omarchy): Menú estilo Omarchy / Rofi en modo drun.
#              - Default (Material You): Overview de Quickshell (Workspaces + Búsqueda).
# ==============================================================================

set -euo pipefail

CURRENT_THEME="$(python3 /home/sasel/.config/hypr/scripts/bwm-theme-manager.py get 2>/dev/null || echo "default")"

if [[ "$CURRENT_THEME" == "plasma" ]]; then
    # Toggle Rofi Kickoff
    if pgrep -x "rofi" > /dev/null 2>&1; then
        pkill -x "rofi"
    else
        rofi -show drun -theme "$HOME/.config/rofi/plasma-kickoff.rasi"
    fi
elif [[ "$CURRENT_THEME" == "retro" ]]; then
    quickshell -c ii ipc call omarchyMenu toggle 2>/dev/null || rofi -show drun -theme "$HOME/.config/rofi/omarchy.rasi"
else
    quickshell -c ii ipc call omarchyMenu close 2>/dev/null || true
    quickshell -c ii ipc call search toggle || rofi -show drun
fi
