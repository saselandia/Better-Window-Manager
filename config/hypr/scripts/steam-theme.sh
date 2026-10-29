#!/usr/bin/env bash
# ==============================================================================
# Script: steam-theme.sh
# Descripción: Aplica a Steam los colores del estilo BWM con Adwaita-for-Steam
# (https://github.com/tkashkin/Adwaita-for-Steam, MIT), como el módulo de Steam de
# omarchy-theme-hook. En Retro añade además esquinas rectas y la fuente monoespaciada
# del sistema (aspecto TUI). Sin Adwaita-for-Steam en ~/.local/share/steam-adwaita no
# hace nada. Steam sólo lo carga al arrancar; durante un cambio de skin permanece abierto.
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

if ! (cd "$ADW" && python3 install.py "${args[@]}") >"$HOME/.local/state/bwm/steam/install.log" 2>&1; then
  printf 'BWM: Steam theme installation failed; see %s\n' "$HOME/.local/state/bwm/steam/install.log" >&2
  exit 1
fi

# Steam only loads the skin at startup (this runs when its colours changed): restart it in
# place, unless a game is open (bwm_omarchy.restart_steam)
# The theme engine already runs this hook separately. Wait for the restart attempt
# here instead of detaching a second job, and retain errors for diagnosis.
[[ "${BWM_SKIN_SWITCH:-0}" == "1" ]] && exit 0
exec python3 "$HOME/.config/hypr/scripts/bwm_omarchy.py" restart-steam \
  >"$HOME/.local/state/bwm/steam/restart.log" 2>&1 </dev/null
