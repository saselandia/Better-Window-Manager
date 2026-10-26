#!/usr/bin/env bash
# ==============================================================================
# Script: steam-theme.sh
# Descripción: Aplica a Steam los colores del tema BWM con Adwaita-for-Steam
# (https://github.com/tkashkin/Adwaita-for-Steam, MIT), como el módulo de Steam de
# omarchy-theme-hook. En Retro añade además esquinas rectas y la fuente monoespaciada
# del sistema (aspecto TUI). Sin Adwaita-for-Steam en ~/.local/share/steam-adwaita no
# hace nada. Steam aplica el cambio la próxima vez que se abra.
# ==============================================================================

ADW="$HOME/.local/share/steam-adwaita"
CSS="$HOME/.local/state/bwm/steam/bwm.css"
[[ -f $ADW/install.py && -f $CSS ]] || exit 0

mkdir -p "$ADW/adwaita/colorthemes/bwm"
cp -f "$CSS" "$ADW/adwaita/colorthemes/bwm/bwm.css"

# Retro follows the Omarchy palette's mode (light themes such as White or Catppuccin Latte)
scheme=dark
theme=$(python3 "$HOME/.config/hypr/scripts/bwm-theme-manager.py" get 2>/dev/null)
if [[ $theme == "retro" ]] && grep -Eq '^mode *= *"light"' "$HOME/.local/state/bwm/omarchy/colors.toml" 2>/dev/null; then
  scheme=light
fi

args=(--color-theme bwm --color-scheme "$scheme" --accent-color theme --extras library/hide-whats-new)
if [[ $theme == "retro" ]]; then
  font=$("$HOME/.config/hypr/scripts/font-set.sh" current 2>/dev/null)
  tui="$HOME/.local/state/bwm/steam/tui.css"
  printf '* { font-family: "%s", monospace !important; }\n' "${font:-JetBrainsMono Nerd Font}" >"$tui"
  args=(--color-theme bwm --color-scheme "$scheme" --accent-color theme
        --extras library/hide-whats-new general/no-rounded-corners --custom-css "$tui")
fi

cd "$ADW" && python3 install.py "${args[@]}" >"$HOME/.local/state/bwm/steam/install.log" 2>&1

if pgrep -x steam >/dev/null; then
  notify-send -a "BWM" "Steam" "El tema de Steam se aplicará al reiniciarlo." 2>/dev/null
fi
