#!/usr/bin/env bash
# ==============================================================================
# Script: glass.sh
# Descripción: Modo glass (ventanas translúcidas con desenfoque), port del de Omarchy
# (omarchy-theme-set-glass + toggles/window-glassy.lua, MIT). Global a los tres estilos.
#   - Hyprland: desenfoque esmerilado, apps GTK atenuadas y capas de Quickshell desenfocadas
#     (modules/glass.lua lee el estado)
#   - kitty: fondo al 65 % (glass.conf), el texto sigue nítido
# Uso: glass.sh on | off | toggle | status
# ==============================================================================

STATE="$HOME/.local/state/bwm/glass"
KITTY_GLASS="$HOME/.config/kitty/glass.conf"

apply() {
  if [[ -f $STATE ]]; then
    printf '%s\n%s\n' "# Generado por ~/.config/hypr/scripts/glass.sh (modo glass activado)" "background_opacity 0.65" >"$KITTY_GLASS"
  else
    printf '%s\n' "# Generado por ~/.config/hypr/scripts/glass.sh (modo glass desactivado)" >"$KITTY_GLASS"
  fi
  pkill -USR1 -x kitty
  hyprctl reload >/dev/null
}

case "$1" in
  on) mkdir -p "${STATE%/*}"; touch "$STATE"; apply ;;
  off) rm -f "$STATE"; apply ;;
  toggle) if [[ -f $STATE ]]; then rm -f "$STATE"; else mkdir -p "${STATE%/*}"; touch "$STATE"; fi; apply ;;
  status) [[ -f $STATE ]] && echo on || echo off ;;
  *) echo "Uso: glass.sh on | off | toggle | status" >&2; exit 1 ;;
esac
