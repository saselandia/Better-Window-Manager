#!/usr/bin/env bash
# ==============================================================================
# Script: launch-screensaver.sh
# Descripción: salvapantallas de la skin Retro en todos los monitores, como omarchy-launch-screensaver
# (https://github.com/basecamp/omarchy, MIT, Copyright (c) David Heinemeier Hansson).
#  * Con el salvapantallas nativo de Omarchy 4.5 compilado (install-screensaver.sh): una capa
#    Wayland por monitor con efectos ttfx sobre el logo de BWM (skins/retro/screensaver.txt) o,
#    si existe, el del usuario (~/.config/omarchy/branding/screensaver.txt, como en Omarchy).
#  * Si no: el de terminal de antes, una kitty a pantalla completa por monitor, en su propio
#    workspace especial, ejecutando bwm-screensaver.py.
# Uso: launch-screensaver.sh [force]   (force: aunque esté desactivado en ajustes)
# Lo lanza modules/ii/idle/BwmIdle.qml tras idle.screensaverTime s, si idle.screensaver (Ajustes → Inactividad)
# ==============================================================================

CLASS="org.bwm.screensaver"
SKIN_DIR="$HOME/.config/hypr/skins/retro"
SCRIPT="$SKIN_DIR/scripts/bwm-screensaver.py"
NATIVE="${XDG_DATA_HOME:-$HOME/.local/share}/bwm/omarchy-screensaver/bin/omarchy-launch-screensaver"

if [[ $1 != "force" ]] && [[ -f "$HOME/.config/illogical-impulse/config.json" ]] &&
   [[ $(jq -r '.idle.screensaver // true' "$HOME/.config/illogical-impulse/config.json") == "false" ]]; then
  exit 1
fi

if [[ -x $NATIVE ]]; then
  # Él mismo evita una segunda instancia y no arranca con la sesión bloqueada (omarchy-shell lock isLocked)
  args=()
  [[ $1 == "force" ]] && args+=(force)
  [[ -f $HOME/.config/omarchy/branding/screensaver.txt ]] || args+=(--input "$SKIN_DIR/screensaver.txt")
  export PATH="$HOME/.config/hypr/scripts/omarchy-shims:$PATH"
  exec "$NATIVE" "${args[@]}"
fi

# Ya en marcha
pgrep -f "[o]rg\.bwm\.screensaver" >/dev/null && exit 0

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
