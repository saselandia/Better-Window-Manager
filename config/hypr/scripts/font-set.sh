#!/usr/bin/env bash
# ==============================================================================
# Script: font-set.sh
# Descripción: Fuente monoespaciada del sistema, compartida por los tres temas.
# Port de omarchy-font-set / omarchy-font-list / omarchy-font-current
# (https://github.com/basecamp/omarchy, MIT, Copyright (c) David Heinemeier Hansson).
# Uso: font-set.sh list | current | set "<familia>"
# Aplica a: kitty, fontconfig (alias "monospace": Qt, GTK, Quickshell...), la fuente
# monoespaciada de GNOME/GTK y la capa TUI del tema Retro (bwm_omarchy.py).
# ==============================================================================

STATE="$HOME/.local/state/bwm/font"

list_fonts() {
  # Monoespaciadas (y de ancho doble, como muchas Nerd Fonts) sin las de iconos/emoji
  fc-list ':spacing=100' family; fc-list ':spacing=90' family
} 2>/dev/null

case "$1" in
  list)
    list_fonts | sed 's/,.*//' | grep -viE "emoji|symbols|material|icons|awesome" | sort -u
    ;;
  current)
    if [[ -s $STATE ]]; then cat "$STATE"
    else sed -nE 's/^[[:space:]]*font_family[[:space:]]+(.*)$/\1/p' ~/.config/kitty/kitty.conf | head -1
    fi
    ;;
  set)
    font_name="$2"
    if [[ -z $font_name ]] || ! fc-list | grep -Fqi -- "$font_name"; then
      echo "Fuente '$font_name' no encontrada." >&2
      exit 1
    fi
    mkdir -p "${STATE%/*}"
    printf '%s\n' "$font_name" >"$STATE"

    # kitty
    if [[ -f ~/.config/kitty/kitty.conf ]]; then
      kitty_font_name=$(printf '%s' "$font_name" | sed 's/[\\&/]/\\&/g')
      if grep -qE '^[[:space:]]*font_family[[:space:]]+' ~/.config/kitty/kitty.conf; then
        sed --follow-symlinks -i -E "s/^[[:space:]]*font_family[[:space:]]+.*/font_family      $kitty_font_name/" ~/.config/kitty/kitty.conf
      else
        printf '\nfont_family %s\n' "$font_name" >>~/.config/kitty/kitty.conf
      fi
      pkill -USR1 -x kitty
    fi

    # fontconfig: el alias "monospace" apunta a la fuente elegida
    fontconfig_file="$HOME/.config/fontconfig/fonts.conf"
    mkdir -p "${fontconfig_file%/*}"
    cat >"$fontconfig_file" <<XML
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<!-- Generado por font-set.sh (BWM) -->
<fontconfig>
  <match target="pattern">
    <test name="family" qual="any">
      <string>monospace</string>
    </test>
    <edit name="family" mode="prepend_first" binding="strong">
      <string>$font_name</string>
    </edit>
  </match>
</fontconfig>
XML
    fc-cache -f >/dev/null 2>&1 &

    # GTK / GNOME
    gsettings set org.gnome.desktop.interface monospace-font-name "$font_name 11" 2>/dev/null

    # Retro: la capa TUI de las apps usa esta fuente
    if [[ $(python3 "$HOME/.config/hypr/scripts/bwm-theme-manager.py" get 2>/dev/null) == "retro" ]]; then
      python3 "$HOME/.config/hypr/scripts/bwm-theme-manager.py" apply-wallpaper-colors "$(cat ~/.cache/current_wallpaper 2>/dev/null)" >/dev/null 2>&1 &
    fi

    notify-send -a "BWM" "Fuente del sistema" "$font_name" 2>/dev/null
    ;;
  *)
    echo "Uso: font-set.sh list | current | set \"<familia>\"" >&2
    exit 1
    ;;
esac
