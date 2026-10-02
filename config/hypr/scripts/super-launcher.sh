#!/usr/bin/env bash
# ==============================================================================
# Script: super-launcher.sh
# Descripción: Abre el menú/búsqueda de Quickshell únicamente cuando la tecla
#              SUPER se pulsa y se suelta en solitario (tap), evitando abrirse
#              si se utilizó en una combinación (como SUPER + A, SUPER + I, etc.).
# ==============================================================================

FLAG="/tmp/.super_interrupted"

# Si se presionó cualquier combinación con SUPER, el flag existe: cancelamos y salimos.
if [ -f "$FLAG" ]; then
    rm -f "$FLAG"
    exit 0
fi

# Ejecutar el menú principal de Quickshell (o fallback a Rofi)
quickshell -c ii ipc call search toggle || rofi -show drun
