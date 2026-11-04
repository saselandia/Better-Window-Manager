#!/usr/bin/env bash

QUICKSHELL_CONFIG_NAME="ii"
XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"
XDG_STATE_HOME="${XDG_STATE_HOME:-$HOME/.local/state}"
CONFIG_DIR="$XDG_CONFIG_HOME/quickshell/$QUICKSHELL_CONFIG_NAME"
CACHE_DIR="$XDG_CACHE_HOME/quickshell"
STATE_DIR="$XDG_STATE_HOME/quickshell"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

term_alpha=100 #Set this to < 100 make all your terminals transparent
# sleep 0 # idk i wanted some delay or colors dont get applied properly
if [ ! -d "$STATE_DIR"/user/generated ]; then
  mkdir -p "$STATE_DIR"/user/generated
fi
cd "$CONFIG_DIR" || exit

colornames=''
colorstrings=''
colorlist=()
colorvalues=()

CONFIG_FILE="$XDG_CONFIG_HOME/illogical-impulse/config.json"
term_colors_file="$STATE_DIR/user/generated/material_colors.scss"

# BWM: terminal neutral mode. The terminal keeps end-4's base palette (terminal/scheme-base.json,
# dark) untouched, with pure greys for the extra slots: it never changes with the wallpaper or theme.
if [ -f "$CONFIG_FILE" ] && [ "$(jq -r '.appearance.wallpaperTheming.terminalGenerationProps.neutral' "$CONFIG_FILE")" = "true" ]; then
  neutral_file="$STATE_DIR/user/generated/terminal/neutral_colors.scss"
  if [ ! -s "$neutral_file" ]; then
    mkdir -p "$STATE_DIR/user/generated/terminal"
    bash "$XDG_CONFIG_HOME/hypr/skins/default/scripts/colors-python.sh" "$SCRIPT_DIR/generate_colors_material.py" \
      --color "#808080" --mode dark --scheme scheme-monochrome --harmony 0 --term_fg_boost 0 \
      --termscheme "$SCRIPT_DIR/terminal/scheme-base.json" > "$neutral_file.tmp" \
      && mv "$neutral_file.tmp" "$neutral_file"
  fi
  [ -s "$neutral_file" ] && term_colors_file="$neutral_file"
fi

colornames=$(cat "$term_colors_file" | cut -d: -f1)
colorstrings=$(cat "$term_colors_file" | cut -d: -f2 | cut -d ' ' -f2 | cut -d ";" -f1)
IFS=$'\n'
colorlist=($colornames)     # Array of color names
colorvalues=($colorstrings) # Array of color values

apply_kitty() {  
  # Check if terminal escape sequence template exists
  if [ ! -f "$SCRIPT_DIR/terminal/kitty-theme.conf" ]; then
    echo "Template file not found for Kitty theme. Skipping that."
    return
  fi
  # Copy template
  mkdir -p "$STATE_DIR"/user/generated/terminal
  cp "$SCRIPT_DIR/terminal/kitty-theme.conf" "$STATE_DIR"/user/generated/terminal/kitty-theme.conf
  # Apply colors
  for i in "${!colorlist[@]}"; do
    sed -i "s/${colorlist[$i]} #/${colorvalues[$i]#\#}/g" "$STATE_DIR"/user/generated/terminal/kitty-theme.conf
  done

  # BWM's Kitty includes this path; use end-4's generated palette there too.
  cp "$STATE_DIR/user/generated/terminal/kitty-theme.conf" "$XDG_CONFIG_HOME/kitty/kitty-colors.conf"
  "$XDG_CONFIG_HOME/hypr/scripts/kitty-recolor.sh"
}

apply_anyterm() {
  # Check if terminal escape sequence template exists
  if [ ! -f "$SCRIPT_DIR/terminal/sequences.txt" ]; then
    echo "Template file not found for Terminal. Skipping that."
    return
  fi
  # Copy template
  mkdir -p "$STATE_DIR"/user/generated/terminal
  cp "$SCRIPT_DIR/terminal/sequences.txt" "$STATE_DIR"/user/generated/terminal/sequences.txt
  # Apply colors
  for i in "${!colorlist[@]}"; do
    sed -i "s/${colorlist[$i]} #/${colorvalues[$i]#\#}/g" "$STATE_DIR"/user/generated/terminal/sequences.txt
  done

  sed -i "s/\$alpha/$term_alpha/g" "$STATE_DIR/user/generated/terminal/sequences.txt"

  for file in /dev/pts/*; do
    if [[ $file =~ ^/dev/pts/[0-9]+$ ]]; then
      {
      cat "$STATE_DIR"/user/generated/terminal/sequences.txt >"$file"
      } & disown || true
    fi
  done
}

apply_term() {
  apply_anyterm &
  apply_kitty &
}

# BWM: terminal theming is always on (end-4's enableTerminal was removed)
apply_term &

# apply_qt & # Qt theming is already handled by kde-material-colors
