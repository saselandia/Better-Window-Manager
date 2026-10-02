#!/usr/bin/env bash
# ==============================================================================
# Script: autostart.sh
# Descripción: Inicialización segura de servicios y demonios en el arranque
#              de Hyprland (Gentoo / Illogical Impulse).
# ==============================================================================

set -euo pipefail

# Asegurar entorno y PATH
export PATH="/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin:$PATH"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

# Evitar ejecuciones simultáneas de autostart.sh
LOCK_FILE="${XDG_RUNTIME_DIR:-/tmp}/hypr-autostart-script.lock"
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
    exit 0
fi

# 1. Esperar activamente a que el socket de Wayland esté completamente disponible
COUNT=0
TIMEOUT=100
until [ -n "${WAYLAND_DISPLAY:-}" ] && [ -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" ]; do
    for sock in "$XDG_RUNTIME_DIR"/wayland-[0-9]*; do
        if [ -S "$sock" ]; then
            export WAYLAND_DISPLAY="$(basename "$sock")"
            break
        fi
    done

    if [ -n "${WAYLAND_DISPLAY:-}" ] && [ -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" ]; then
        break
    fi

    sleep 0.1
    COUNT=$((COUNT + 1))
    if [ "$COUNT" -ge "$TIMEOUT" ]; then
        break
    fi
done

export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
export DISPLAY="${DISPLAY:-:0}"
export XDG_CURRENT_DESKTOP="Hyprland"
export XDG_SESSION_TYPE="wayland"
export XDG_SESSION_DESKTOP="Hyprland"

# Actualizar entorno en systemd y dbus (vital para Flatpak, Signal, Steam, Polkit)
if command -v dbus-update-activation-environment >/dev/null 2>&1; then
    dbus-update-activation-environment --systemd WAYLAND_DISPLAY DISPLAY XDG_CURRENT_DESKTOP XDG_SESSION_TYPE XDG_SESSION_DESKTOP 2>/dev/null || true
fi

# 2. Agente de autenticación Polkit (Gentoo en /usr/libexec o PATH)
if ! pidof hyprpolkitagent >/dev/null 2>&1; then
    if command -v hyprpolkitagent >/dev/null 2>&1; then
        hyprpolkitagent &
    elif [ -x /usr/libexec/hyprpolkitagent ]; then
        /usr/libexec/hyprpolkitagent &
    fi
fi

# 3. Demonio de wallpapers (swww)
if ! pidof swww-daemon >/dev/null 2>&1; then
    swww-daemon &
fi

# 4. Restaurar el wallpaper guardado (solo si swww no está mostrando uno ya)
(
    COUNT=0
    TIMEOUT=40
    until swww query >/dev/null 2>&1 || [ "$COUNT" -ge "$TIMEOUT" ]; do
        sleep 0.1
        COUNT=$((COUNT + 1))
    done

    # Solo restaurar si no hay una imagen activa mostrándose actualmente
    if ! swww query 2>/dev/null | grep -q "currently displaying: image:"; then
        WALLPAPER=""
        # Prioridad 1: archivo de caché
        if [ -f "$HOME/.cache/current_wallpaper" ] && [ -s "$HOME/.cache/current_wallpaper" ]; then
            WALLPAPER="$(cat "$HOME/.cache/current_wallpaper")"
        fi

        # Prioridad 2: configuración de Illogical Impulse / Quickshell
        if [ -z "$WALLPAPER" ] || [ ! -f "$WALLPAPER" ]; then
            if [ -f "$HOME/.config/illogical-impulse/config.json" ] && command -v jq >/dev/null 2>&1; then
                WALLPAPER="$(jq -r '.background.wallpaperPath // empty' "$HOME/.config/illogical-impulse/config.json" 2>/dev/null || true)"
            fi
        fi

        # Prioridad 3: primera imagen en Pictures/Wallpapers o ~/Pictures
        if [ -z "$WALLPAPER" ] || [ ! -f "$WALLPAPER" ]; then
            WALLPAPER="$(find "$HOME/Pictures" -maxdepth 2 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" \) 2>/dev/null | head -n 1 || true)"
        fi

        # Prioridad 4: wallpaper por defecto del sistema
        if [ -z "$WALLPAPER" ] || [ ! -f "$WALLPAPER" ]; then
            if [ -f "/usr/share/hypr/wall0.png" ]; then
                WALLPAPER="/usr/share/hypr/wall0.png"
            fi
        fi

        if [ -n "$WALLPAPER" ] && [ -f "$WALLPAPER" ]; then
            echo "$WALLPAPER" > "$HOME/.cache/current_wallpaper"
            swww img "$WALLPAPER" --transition-type none 2>/dev/null || true
        fi
    fi
) &

# 5. Barra y entorno de escritorio Quickshell (End_4 / Illogical Impulse)
if ! pidof quickshell >/dev/null 2>&1; then
    if command -v quickshell >/dev/null 2>&1; then
        quickshell -c ii &
    fi
fi

# 6. Centro de notificaciones (swaync)
if ! pidof swaync >/dev/null 2>&1; then
    if command -v swaync >/dev/null 2>&1; then
        swaync &
    fi
fi

# 7. Demonio de portapapeles (cliphist con wl-paste)
if ! pgrep -f '^wl-paste --type text' >/dev/null 2>&1; then
    wl-paste --type text --watch cliphist store &
fi
if ! pgrep -f '^wl-paste --type image' >/dev/null 2>&1; then
    wl-paste --type image --watch cliphist store &
fi

# 8. Aplicaciones de inicio automático del usuario (XDG Autostart / Quickshell Autostart)
if [ -f "$HOME/.config/hypr/scripts/autostart-manager.py" ]; then
    (
        # Esperar 2 segundos para dar tiempo a que Hyprland, los monitores y Xwayland estén listos
        sleep 2
        python3 "$HOME/.config/hypr/scripts/autostart-manager.py" run-all
    ) &
fi

