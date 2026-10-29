#!/usr/bin/env bash
# ==============================================================================
# Script: open-settings.sh
# Descripción: Abre la app de configuración del estilo activo:
#              - Plasma (KDE): plasmaSettings.qml (estilo Preferencias del sistema)
#              - Retro (Omarchy): retroSettings.qml (mismas páginas, marco de Omarchy);
#                con una página concreta, en una ventanita flotante sólo con esa página
#              - Default: settings.qml (Material You)
#              Página: SETTINGS_PAGE=<id> o primer argumento (p. ej. open-settings.sh bar).
# ==============================================================================

THEME="$(python3 "$HOME/.config/hypr/scripts/bwm-theme-manager.py" get 2>/dev/null || echo default)"

if [[ -n "${1:-}" && "$1" != -* ]]; then
    export SETTINGS_PAGE="$1"
    shift
fi

if [[ "$THEME" == "plasma" ]]; then
    exec qs -p "$HOME/.config/quickshell/ii/plasmaSettings.qml" "$@"
elif [[ "$THEME" == "retro" ]]; then
    exec qs -p "$HOME/.config/quickshell/ii/retroSettings.qml" "$@"
else
    exec qs -p "$HOME/.config/quickshell/ii/settings.qml" "$@"
fi
