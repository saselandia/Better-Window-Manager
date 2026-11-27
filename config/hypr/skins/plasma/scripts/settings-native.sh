#!/usr/bin/env bash
# Native KDE System Settings launcher with locally installed BWM KCMs.
set -euo pipefail
bwm_settings_prefix="${XDG_DATA_HOME:-$HOME/.local/share}/bwm/systemsettings"
export QT_PLUGIN_PATH="$bwm_settings_prefix/lib/qt6/plugins${QT_PLUGIN_PATH:+:$QT_PLUGIN_PATH}"
# Supported KAuthorized/Kiosk restrictions, scoped to this host process. No plugin deletion.
bwm_settings_profile="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../settings-profile" && pwd)"
export XDG_CONFIG_DIRS="$bwm_settings_profile:${XDG_CONFIG_DIRS:-/etc/xdg}"
# Opening a shared alias always selects its functional BWM or KDE replacement.
case "${1:-}" in
    effects|kcm_kwin_effects|kcm_kwin_effects_x11|kcm_animations|kcm_animations_x11) shift; set -- kcm_bwm_effects "$@" ;;
    windowbehavior|windows|kcm_kwinoptions) shift; set -- kcm_bwm_windows "$@" ;;
    display|screens|kcm_kscreen) shift; set -- kcm_bwm_screens "$@" ;;
    workspaces|kcm_kwin_virtualdesktops) shift; set -- kcm_bwm_workspaces "$@" ;;
    keybinds|shortcuts) shift; set -- kcm_bwm_shortcuts "$@" ;;
    globalshortcuts) shift; set -- kcm_keys "$@" ;;
    cursor|cursors|kcm_cursortheme) shift; set -- kcm_bwm_cursor "$@" ;;
    mouse|touchpad|input|kcm_mouse|kcm_touchpad) shift; set -- kcm_bwm_input "$@" ;;
    idle|energy|power|kcm_powerdevilprofilesconfig) shift; set -- kcm_bwm_energy "$@" ;;
    nightlight|kcm_nightcolor|kcm_nightlight) shift; set -- kcm_bwm_nightlight "$@" ;;
    defaultapps|apps|kcm_componentchooser) shift; set -- kcm_bwm_apps "$@" ;;
    autostart|startup|kcm_autostart) shift; set -- kcm_bwm_startup "$@" ;;
    sound|audio) shift; set -- kcm_pulseaudio "$@" ;;
    network|wifi) shift; set -- kcm_networkmanagement "$@" ;;
    globaltheme|themes) shift; set -- kcm_lookandfeel "$@" ;;
    colors) shift; set -- kcm_colors "$@" ;;
    plasmastyle) shift; set -- kcm_desktoptheme "$@" ;;
    decorations) shift; set -- kcm_kwindecoration "$@" ;;
    icons) shift; set -- kcm_icons "$@" ;;
    appstyle) shift; set -- kcm_style "$@" ;;
    fonts) shift; set -- kcm_fonts "$@" ;;
    behavior|interface) shift; set -- kcm_workspace "$@" ;;
esac
exec "${BWM_SYSTEMSETTINGS_BIN:-systemsettings}" "$@"
