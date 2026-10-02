#!/usr/bin/env bash
set -e

WAS_RUNNING=0
if pgrep -f "com.spotify.Client" > /dev/null 2>&1 || pgrep -x "spotify" > /dev/null 2>&1; then
    WAS_RUNNING=1
fi

if [ "$WAS_RUNNING" -eq 1 ]; then
    # Aplicar temas con Spicetify si Spotify está corriendo y relanzarlo
    spicetify -n apply >/dev/null 2>&1 || spicetify -n refresh >/dev/null 2>&1 || true
    pkill -9 -f "com.spotify.Client" 2>/dev/null || true
    pkill -9 -x "spotify" 2>/dev/null || true
    sleep 0.5
    hyprctl dispatch exec "flatpak run com.spotify.Client" >/dev/null 2>&1
else
    # Si Spotify no está activo, regenerar en segundo plano para no ralentizar el cambio de fondo
    (spicetify -n apply >/dev/null 2>&1 || true) & disown
fi
