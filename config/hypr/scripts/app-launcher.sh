#!/usr/bin/env bash
# ==============================================================================
# Script: app-launcher.sh
# Descripción: Lanza el menú de aplicaciones según el estilo activo:
#              - Plasma (KDE): Kickoff de Quickshell, con Rofi de respaldo.
#              - Retro (Omarchy): Menú y cuadrícula Apps de Omarchy.
#              - Default (Material You): Overview de Quickshell (Workspaces + Búsqueda).
# ==============================================================================

set -euo pipefail

CURRENT_THEME="$(python3 /home/sasel/.config/hypr/scripts/bwm-theme-manager.py get 2>/dev/null || echo "default")"

# app-launcher.sh apps: sólo las aplicaciones (en Retro la cuadrícula «Apps» de Omarchy,
# Alt+Espacio o Super+Espacio); sin argumento, el lanzador/menú de cada estilo (Super)
if [[ "${1:-}" == "apps" && "$CURRENT_THEME" == "retro" ]]; then
    # One shell entry point owns the menu/grid handoff and the optional dock.
    quickshell -c ii ipc call omarchyApps toggle 2>/dev/null \
        || rofi -show drun -theme "$HOME/.config/rofi/omarchy.rasi"
    exit 0
fi

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
