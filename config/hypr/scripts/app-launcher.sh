#!/usr/bin/env bash
# ==============================================================================
# Script: app-launcher.sh
# Descripción: Lanza el menú de aplicaciones según el tema activo:
#              - Retro (Omarchy): Rofi en modo drun con tema y colores Omarchy (con toggle).
#              - Default (Material You): Overview de Quickshell (Workspaces + Búsqueda).
# ==============================================================================

set -euo pipefail

CURRENT_THEME="$(python3 /home/sasel/.config/hypr/scripts/bwm-theme-manager.py get 2>/dev/null || echo "default")"

if [[ "$CURRENT_THEME" == "retro" ]]; then
    # Menú estilo Omarchy nativo en Quickshell (toggle); Rofi como respaldo
    quickshell -c ii ipc call omarchyMenu toggle 2>/dev/null || rofi -show drun -theme "$HOME/.config/rofi/omarchy.rasi"
else
    quickshell -c ii ipc call omarchyMenu close 2>/dev/null || true
    # Overview de Quickshell (Material You)
    quickshell -c ii ipc call search toggle || rofi -show drun
fi
