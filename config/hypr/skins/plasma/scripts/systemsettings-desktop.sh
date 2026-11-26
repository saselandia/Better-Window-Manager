#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Desktop-entry wrapper for systemsettings.desktop.
# In Breeze (plasma), launches real KDE System Settings with BWM's local KCMs and KAuthorized profile.
# Outside Breeze, launches stock systemsettings untouched so other skins are never hijacked.
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cfg="${XDG_CONFIG_HOME:-$HOME/.config}/illogical-impulse/config.json"
skin=""
if [[ -f "$cfg" ]]; then
    skin="$(python3 -c 'import json,sys
try:
    print(json.load(open(sys.argv[1])).get("appearance",{}).get("bwmTheme",""))
except Exception:
    pass' "$cfg" 2>/dev/null || true)"
fi

native_kcm="${XDG_DATA_HOME:-$HOME/.local/share}/bwm/systemsettings/lib/qt6/plugins/plasma/kcms/systemsettings/kcm_bwm_windows.so"
if [[ "$skin" == "plasma" && -f "$native_kcm" && -x "$script_dir/settings-native.sh" ]]; then
    exec "$script_dir/settings-native.sh" "$@"
fi
exec "${BWM_SYSTEMSETTINGS_BIN:-systemsettings}" "$@"
