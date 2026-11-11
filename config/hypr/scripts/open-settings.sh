#!/usr/bin/env bash
# ==============================================================================
# Script: open-settings.sh
# Descripción: Abre la app de configuración del estilo activo:
#              - Breeze: plasmaSettings.qml (Preferencias del sistema de Plasma, KCMs reales)
#              - Retro (Omarchy): Configuración dentro del propio menú de Omarchy
#              - Default: settings.qml (Material You)
#              Página: SETTINGS_PAGE=<id> o primer argumento (p. ej. open-settings.sh bar).
# ==============================================================================

THEME="$(python3 "$HOME/.config/hypr/scripts/bwm-theme-manager.py" get 2>/dev/null || echo default)"

if [[ -n "${1:-}" && "$1" != -* ]]; then
    export SETTINGS_PAGE="$1"
    shift
fi

if [[ "$THEME" == "plasma" ]]; then
    # Preferencias del sistema de Breeze: KCMs reales incrustados con org.bwm.kcm (src/bwm-kcmhost)
    # y el estilo de controles de Plasma (qqc2-desktop-style), como systemsettings.
    export QML_IMPORT_PATH="${XDG_DATA_HOME:-$HOME/.local/share}/bwm/qml${QML_IMPORT_PATH:+:$QML_IMPORT_PATH}"
    export QT_QUICK_CONTROLS_STYLE=org.kde.desktop
    exec qs -p "$HOME/.config/quickshell/ii/plasmaSettings.qml" "$@"
elif [[ "$THEME" == "retro" ]]; then
    exec qs -c ii ipc call omarchyMenu settings "${SETTINGS_PAGE:-all}"
else
    exec qs -p "$HOME/.config/quickshell/ii/settings.qml" "$@"
fi
