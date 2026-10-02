#!/usr/bin/env bash
# ==============================================================================
# Script: set-wallpaper.sh
# Descripción: Cambia el wallpaper con swww usando animación 'grow',
#              extrae la paleta Material You con Matugen y recarga Hyprland.
# ==============================================================================

set -euo pipefail

# Validar argumento de imagen
if [ $# -lt 1 ] || [ -z "$1" ]; then
    echo "Error: Debe especificar la ruta a una imagen de fondo." >&2
    echo "Uso: $0 /ruta/al/wallpaper.jpg" >&2
    exit 1
fi

WALLPAPER="$(realpath "$1")"

if [ ! -f "$WALLPAPER" ]; then
    echo "Error: El archivo '$WALLPAPER' no existe o no es accesible." >&2
    exit 1
fi

# 1. Asegurar que el demonio swww-daemon esté en ejecución
if ! pgrep -x "swww-daemon" > /dev/null 2>&1; then
    echo "Iniciando swww-daemon..."
    swww-daemon &
    # Esperar hasta que el demonio responda
    TIMEOUT=20
    COUNT=0
    until swww query > /dev/null 2>&1 || [ "$COUNT" -ge "$TIMEOUT" ]; do
        sleep 0.1
        COUNT=$((COUNT + 1))
    done
fi

# 2. Cambiar fondo con animación fluida estilo End_4 ('grow')
echo "Aplicando wallpaper: $WALLPAPER"
swww img "$WALLPAPER" \
    --transition-type grow \
    --transition-pos center \
    --transition-step 90 \
    --transition-duration 2 \
    --transition-fps 60

# 2.1 Guardar en caché para recuperación instantánea al encender el PC
mkdir -p "$HOME/.cache"
echo "$WALLPAPER" > "$HOME/.cache/current_wallpaper"

# 2.2 Sincronizar ruta del wallpaper con Quickshell / Illogical Impulse
if [ -f "$HOME/.config/illogical-impulse/config.json" ] && command -v jq >/dev/null 2>&1; then
    jq --arg path "$WALLPAPER" '.background.wallpaperPath = $path' "$HOME/.config/illogical-impulse/config.json" > "$HOME/.config/illogical-impulse/config.json.tmp" && mv "$HOME/.config/illogical-impulse/config.json.tmp" "$HOME/.config/illogical-impulse/config.json"
fi

# 3. Generar la paleta de colores con Matugen (Material You / MD3)
echo "Generando esquema de colores con Matugen..."
timeout 10 matugen image --source-color-index 0 "$WALLPAPER" || true

# 3.1 Forzar recarga de colores en Quickshell (barra y widgets)
quickshell -c ii ipc call theme reload 2>/dev/null || true

# 4. Actualizar colores en Firefox en caliente sin reiniciar
~/.local/share/pywalfox-venv/bin/pywalfox update 2>/dev/null || true

# 5. Sincronizar Nautilus / GNOME en caliente
~/.config/hypr/scripts/sync-nautilus.sh 2>/dev/null || true

# 6. Recargar Hyprland para aplicar la nueva paleta en caliente
echo "Recargando configuración de Hyprland..."
hyprctl reload

echo "¡Fondo y tema Material You actualizados con éxito!"
