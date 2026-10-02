#!/usr/bin/env bash
# ==============================================================================
# Script: super-launcher.sh
# Descripción: Abre el menú/búsqueda de Quickshell únicamente cuando la tecla
#              SUPER se pulsa y se suelta en solitario (tap), evitando abrirse
#              si se utilizó en una combinación (como SUPER + A, SUPER + I, etc.).
# ==============================================================================

FLAG="/tmp/.super_interrupted"

# 1. Si se utilizó alguna combinación con Super (Super+A, etc.), cancelar
if [ -f "$FLAG" ]; then
    rm -f "$FLAG"
    exit 0
fi

# 2. Antirrebote (Debounce) para evitar ejecuciones dobles en microsegundos
LOCKFILE="/tmp/.super_launcher_last"
NOW=$(date +%s%3N)
if [ -f "$LOCKFILE" ]; then
    LAST=$(cat "$LOCKFILE" 2>/dev/null || echo 0)
    DIFF=$(( NOW - LAST ))
    if [ "$DIFF" -ge 0 ] && [ "$DIFF" -lt 350 ]; then
        exit 0
    fi
fi
echo "$NOW" > "$LOCKFILE"

# 3. Lanzar menú de Quickshell (o fallback a Rofi)
quickshell -c ii ipc call search toggle || rofi -show drun
