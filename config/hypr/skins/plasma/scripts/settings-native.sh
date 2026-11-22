#!/usr/bin/env bash
# Experimental R2 entry: real KDE System Settings with locally installed native BWM KCMs.
# Not the default launcher until all BWM pages have migrated.
set -euo pipefail
bwm_settings_prefix="${XDG_DATA_HOME:-$HOME/.local/share}/bwm/systemsettings"
export QT_PLUGIN_PATH="$bwm_settings_prefix/lib/qt6/plugins${QT_PLUGIN_PATH:+:$QT_PLUGIN_PATH}"
# Supported KAuthorized/Kiosk restrictions, scoped to this host process. No plugin deletion.
bwm_settings_profile="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../settings-profile" && pwd)"
export XDG_CONFIG_DIRS="$bwm_settings_profile:${XDG_CONFIG_DIRS:-/etc/xdg}"
# Opening a shared alias always selects its functional BWM replacement.
case "${1:-}" in
    effects|kcm_kwin_effects|kcm_kwin_effects_x11|kcm_animations|kcm_animations_x11) shift; set -- kcm_bwm_effects "$@" ;;
    kcm_kwinoptions) shift; set -- kcm_bwm_windows "$@" ;;
    kcm_kscreen) shift; set -- kcm_bwm_screens "$@" ;;
    kcm_kwin_virtualdesktops) shift; set -- kcm_bwm_workspaces "$@" ;;
    kcm_keys) shift; set -- kcm_bwm_shortcuts "$@" ;;
    kcm_cursortheme) shift; set -- kcm_bwm_cursor "$@" ;;
    kcm_powerdevilprofilesconfig) shift; set -- kcm_bwm_energy "$@" ;;
    kcm_nightcolor|kcm_nightlight) shift; set -- kcm_bwm_nightlight "$@" ;;
    kcm_componentchooser) shift; set -- kcm_bwm_apps "$@" ;;
    kcm_autostart) shift; set -- kcm_bwm_startup "$@" ;;
esac
exec systemsettings "$@"
