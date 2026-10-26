#!/usr/bin/env bash
# Recolorea al momento todas las ventanas de kitty con ~/.config/kitty/kitty-colors.conf (lo escriben
# matugen en Default, Breeze en Plasma y bwm_omarchy en Retro), como hace Omarchy con foot por OSC.
# Con el control remoto de kitty.conf (listen_on unix:@kitty -> @kitty-<pid>), --all y --configured
# pisan también los colores que un programa hubiera cambiado por secuencias de escape; sin él, la
# recarga normal de la config (SIGUSR1).
COLORS="${1:-$HOME/.config/kitty/kitty-colors.conf}"
for pid in $(pgrep -x kitty); do
    kitty @ --to "unix:@kitty-$pid" set-colors --all --configured "$COLORS" >/dev/null 2>&1 \
        || kill -USR1 "$pid" 2>/dev/null
done
exit 0
