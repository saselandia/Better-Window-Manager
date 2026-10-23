#!/usr/bin/env bash
# ==============================================================================
# Script: launch-screensaver.sh
# Descripción: Salvapantallas de terminal en todos los monitores.
# Port de omarchy-launch-screensaver (https://github.com/basecamp/omarchy, MIT,
# Copyright (c) David Heinemeier Hansson): una kitty a pantalla completa por monitor,
# en su propio workspace especial, ejecutando bwm-screensaver.py.
# Uso: launch-screensaver.sh [force]   (force: aunque esté desactivado en ajustes)
# ==============================================================================

CLASS="org.bwm.screensaver"
SCRIPT="$HOME/.config/hypr/scripts/bwm-screensaver.py"

# Ya en marcha
pgrep -f "[o]rg\.bwm\.screensaver" >/dev/null && exit 0

if [[ $1 != "force" ]] && [[ -f "$HOME/.config/illogical-impulse/config.json" ]] &&
   [[ $(jq -r '.screensaver.enable // true' "$HOME/.config/illogical-impulse/config.json") == "false" ]]; then
  exit 1
fi

focused=$(hyprctl monitors -j | jq -r '.[] | select(.focused) | .name')

hypr_focus_monitor() {
  hyprctl dispatch "hl.dsp.focus({ monitor = \"$1\" })" >/dev/null 2>&1
}

SOCKET="$XDG_RUNTIME_DIR/hypr/$HYPRLAND_INSTANCE_SIGNATURE/.socket2.sock"
# Abrir el flujo de eventos antes de lanzar nada, para no perder el openwindow
exec {events}< <(socat -U - "UNIX-CONNECT:$SOCKET")

# Cada ventana nueva aparece en el monitor enfocado: esperar a que abra antes de pasar al siguiente
wait_for_screensaver_window() {
  local line deadline=$((SECONDS + 5))
  while ((SECONDS < deadline)) && IFS= read -r -t $((deadline - SECONDS)) -u "$events" line; do
    [[ $line == openwindow\>\>*,$CLASS,* ]] && return 0
  done
}

while read -r m height special; do
  hypr_focus_monitor "$m"
  workspace=${special:-special:screensaver-$m}
  # Same logo size on every screen: 16 pt at 1080 px of (logical) height
  font_size=$(( 16 * height / 1080 ))
  hyprctl dispatch "hl.dsp.exec_cmd([[[workspace $workspace] kitty --class=$CLASS --override font_size=$font_size --override window_padding_width=0 --override background_opacity=1 -e sh -c 'python3 \"\$0\"' $SCRIPT]])" >/dev/null 2>&1
  wait_for_screensaver_window
done < <(hyprctl monitors -j | jq -r '.[] | "\(.name) \((.height / .scale) | floor) \(.specialWorkspace.name)"')

hypr_focus_monitor "$focused"

# Al cerrarse el último, devolver el foco al monitor que lo tenía
(
  while hyprctl clients -j | SCREENSAVER=$CLASS jq -e 'any(.[]; .mapped and .class == env.SCREENSAVER)' >/dev/null; do
    IFS= read -r -u "$events" line || exit
  done
  hypr_focus_monitor "$focused"
) >/dev/null 2>&1 &
