#!/usr/bin/env bash
# ==============================================================================
# Script: open-settings.sh
# Descripción: Abre la app de configuración del estilo activo:
#              - Breeze: Preferencias del sistema reales de KDE (settings-native.sh)
#                con los KCM nativos de BWM; plasmaSettings.qml para páginas sólo-BWM,
#                BWM_SETTINGS_HOST=legacy o respaldo si falta systemsettings.
#              - Retro (Omarchy): Configuración dentro del propio menú de Omarchy
#              - Default: settings.qml (Material You)
#              Página: SETTINGS_PAGE=<id> o primer argumento (p. ej. open-settings.sh display).
# ==============================================================================

THEME="${BWM_SETTINGS_THEME_OVERRIDE:-$(python3 "$HOME/.config/hypr/scripts/bwm-theme-manager.py" get 2>/dev/null || echo default)}"

if [[ -n "${1:-}" && "$1" != -* ]]; then
    export SETTINGS_PAGE="$1"
    shift
fi

if [[ "$THEME" == "plasma" ]]; then
    native_launcher="$HOME/.config/hypr/skins/plasma/scripts/settings-native.sh"
    native_kcm="${XDG_DATA_HOME:-$HOME/.local/share}/bwm/systemsettings/lib/qt6/plugins/plasma/kcms/systemsettings/kcm_bwm_windows.so"
    sys_bin="${BWM_SYSTEMSETTINGS_BIN:-systemsettings}"
    use_legacy=0
    case "${SETTINGS_PAGE:-}" in
        background|wallpaper|bar|panel|plugins|services|general|style|about|windowrules)
            use_legacy=1
            ;;
    esac
    if [[ "${BWM_SETTINGS_HOST:-native}" != "legacy" && "$use_legacy" -eq 0 \
          && -f "$native_launcher" && -f "$native_kcm" ]] \
       && command -v "$sys_bin" >/dev/null 2>&1; then
        if [[ -n "${SETTINGS_PAGE:-}" ]]; then
            exec bash "$native_launcher" "$SETTINGS_PAGE" "$@"
        fi
        exec bash "$native_launcher" "$@"
    fi
    # Respaldo o páginas exclusivas de BWM: plasmaSettings.qml (org.bwm.kcm + qqc2-desktop-style)
    export QML_IMPORT_PATH="${XDG_DATA_HOME:-$HOME/.local/share}/bwm/qml${QML_IMPORT_PATH:+:$QML_IMPORT_PATH}"
    export QT_QUICK_CONTROLS_STYLE=org.kde.desktop
    exec "${BWM_QS_BIN:-qs}" -p "$HOME/.config/quickshell/ii/plasmaSettings.qml" "$@"
elif [[ "$THEME" == "retro" ]]; then
    exec "${BWM_QS_BIN:-qs}" -c ii ipc call omarchyMenu settings "${SETTINGS_PAGE:-all}"
else
    exec "${BWM_QS_BIN:-qs}" -p "$HOME/.config/quickshell/ii/settings.qml" "$@"
fi
