#!/usr/bin/env bash
# ==============================================================================
# Script: app-launcher.sh
# Descripción: Lanza el menú de aplicaciones según el estilo activo:
#              - Plasma (KDE): Rofi Kickoff launcher en esquina inferior izquierda.
#              - Retro (Omarchy): Menú estilo Omarchy / Rofi en modo drun.
#              - Default (Material You): Overview de Quickshell (Workspaces + Búsqueda).
# ==============================================================================

set -euo pipefail

CURRENT_THEME="$(python3 /home/sasel/.config/hypr/scripts/bwm-theme-manager.py get 2>/dev/null || echo "default")"

if [[ "$CURRENT_THEME" == "plasma" ]]; then
    pkill -x "rofi" 2>/dev/null || true
    quickshell -c ii ipc call omarchyMenu close 2>/dev/null || true
    quickshell -c ii ipc call plasmaKickoff toggle 2>/dev/null || rofi -show drun -theme "$HOME/.config/rofi/plasma-kickoff.rasi"
elif [[ "$CURRENT_THEME" == "retro" ]]; then
    pkill -x "rofi" 2>/dev/null || true
    quickshell -c ii ipc call plasmaKickoff close 2>/dev/null || true
    quickshell -c ii ipc call omarchyMenu toggle 2>/dev/null || rofi -show drun -theme "$HOME/.config/rofi/omarchy.rasi"
else
    pkill -x "rofi" 2>/dev/null || true
    quickshell -c ii ipc call omarchyMenu close 2>/dev/null || true
    quickshell -c ii ipc call plasmaKickoff close 2>/dev/null || true
    quickshell -c ii ipc call search toggle || rofi -show drun
fi
