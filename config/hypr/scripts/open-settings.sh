#!/usr/bin/env bash
# ==============================================================================
# Script: open-settings.sh
# Descripción: Abre la app de configuración del tema activo:
#              - Plasma (KDE): plasmaSettings.qml (estilo Preferencias del sistema)
#              - Default / Retro: settings.qml (Material You)
#              Respeta SETTINGS_PAGE para abrir una página concreta (p. ej. Autostart).
# ==============================================================================

THEME="$(python3 "$HOME/.config/hypr/scripts/bwm-theme-manager.py" get 2>/dev/null || echo default)"

if [[ "$THEME" == "plasma" ]]; then
    exec qs -p "$HOME/.config/quickshell/ii/plasmaSettings.qml" "$@"
else
    exec qs -p "$HOME/.config/quickshell/ii/settings.qml" "$@"
fi
