#!/usr/bin/env bash
# ==============================================================================
# Script: window-transparency.sh
# Descripción: Transparencia de ventanas al estilo Omarchy (estilo Retro).
#   Como en Omarchy (default/hypr/windows.lua + omarchy-hyprland-window-transparency*),
#   las apps son opacas y sólo los terminales/TUIs (y Nautilus) llevan la etiqueta
#   "transparent-window", que les da opacidad "0.985 0.96" (activa/inactiva).
# Uso:
#   window-transparency.sh status            # transparent | opaque
#   window-transparency.sh opaque            # todas opacas (quita la transparencia por defecto)
#   window-transparency.sh transparent       # restaura la transparencia por defecto
#   window-transparency.sh toggle-window     # alterna la transparencia de la ventana activa
# El modo glass (glass.sh) se combina con esto: lo translúcido se desenfoca.
# ==============================================================================

STATE="$HOME/.local/state/bwm/windows-opaque"

case "$1" in
  status) [[ -f $STATE ]] && echo opaque || echo transparent ;;
  opaque) mkdir -p "${STATE%/*}"; touch "$STATE"; hyprctl reload >/dev/null ;;
  transparent) rm -f "$STATE"; hyprctl reload >/dev/null ;;
  toggle-window)
    win=$(hyprctl activewindow -j 2>/dev/null)
    addr=$(jq -r '.address // empty' <<<"$win")
    [[ -n $addr ]] || exit 0
    if jq -e '.tags // [] | index("transparent-window")' <<<"$win" >/dev/null; then
      op="-transparent-window"
    else
      op="+transparent-window"
    fi
    hyprctl dispatch "hl.dsp.window.tag({ window = \"address:$addr\", tag = \"$op\" })" >/dev/null
    ;;
  *) echo "Uso: window-transparency.sh status | opaque | transparent | toggle-window" >&2; exit 1 ;;
esac
