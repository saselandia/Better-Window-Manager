#!/usr/bin/env bash
# ==============================================================================
# Script: autostart.sh
# Descripción: Inicialización segura de servicios y demonios en el arranque
#              de Hyprland (Gentoo / Illogical Impulse).
# ==============================================================================

set -euo pipefail

# Asegurar que las señales (SIGTERM, SIGHUP, etc.) no estén bloqueadas
# Hyprland usa signalfd en su hilo principal, lo que bloquea SIGTERM en procesos hijos.
if [ -z "${_SIG_UNMASKED:-}" ]; then
    export _SIG_UNMASKED=1
    exec python3 -c "import os, signal, sys; signal.pthread_sigmask(signal.SIG_SETMASK, []); os.execvp(sys.argv[1], sys.argv[1:])" "$0" "$@"
fi

# Asegurar entorno y PATH
export PATH="/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin:$PATH"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

# Evitar ejecuciones simultáneas de autostart.sh
LOCK_FILE="${XDG_RUNTIME_DIR:-/tmp}/hypr-autostart-script.pid"
if [ -f "$LOCK_FILE" ]; then
    OLD_PID="$(cat "$LOCK_FILE" 2>/dev/null || true)"
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null && [ "$OLD_PID" != "$$" ]; then
        exit 0
    fi
fi
echo "$$" > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT INT TERM

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
    dbus-update-activation-environment --systemd WAYLAND_DISPLAY DISPLAY XDG_CURRENT_DESKTOP XDG_SESSION_TYPE XDG_SESSION_DESKTOP QT_QPA_PLATFORMTHEME 2>/dev/null || true
fi

# 2. Agente de autenticación Polkit (Gentoo en /usr/libexec o PATH)
if ! pidof hyprpolkitagent >/dev/null 2>&1; then
    if command -v hyprpolkitagent >/dev/null 2>&1; then
        hyprpolkitagent >/dev/null 2>&1 &
    elif [ -x /usr/libexec/hyprpolkitagent ]; then
        /usr/libexec/hyprpolkitagent >/dev/null 2>&1 &
    fi
fi

# 3. Demonio de wallpapers (swww)
if ! pidof swww-daemon >/dev/null 2>&1; then
    swww-daemon >/dev/null 2>&1 &
fi

# 4. Restaurar el wallpaper guardado
(
    COUNT=0
    TIMEOUT=40
    until swww query >/dev/null 2>&1 || [ "$COUNT" -ge "$TIMEOUT" ]; do
        sleep 0.1
        COUNT=$((COUNT + 1))
    done

    WALLPAPER=""
    if [ -f "$HOME/.cache/current_wallpaper" ] && [ -s "$HOME/.cache/current_wallpaper" ]; then
        WALLPAPER="$(cat "$HOME/.cache/current_wallpaper")"
    fi

    if [ -z "$WALLPAPER" ] || [ ! -f "$WALLPAPER" ]; then
        if [ -f "$HOME/.config/illogical-impulse/config.json" ] && command -v jq >/dev/null 2>&1; then
            WALLPAPER="$(jq -r '.background.wallpaperPath // empty' "$HOME/.config/illogical-impulse/config.json" 2>/dev/null || true)"
        fi
    fi

    if [ -z "$WALLPAPER" ] || [ ! -f "$WALLPAPER" ]; then
        WALLPAPER="$(find "$HOME/Pictures" -maxdepth 2 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" \) 2>/dev/null | head -n 1 || true)"
    fi

    if [ -z "$WALLPAPER" ] || [ ! -f "$WALLPAPER" ]; then
        if [ -f "/usr/share/hypr/wall0.png" ]; then
            WALLPAPER="/usr/share/hypr/wall0.png"
        fi
    fi

    if [ -n "$WALLPAPER" ] && [ -f "$WALLPAPER" ]; then
        echo "$WALLPAPER" > "$HOME/.cache/current_wallpaper"
        # swww-daemon responde antes de tener todos los monitores (más aún al entrar desde
        # SDDM, con la GPU recién liberada por el saludo): reintentar hasta que todos
        # muestren la imagen, o quedan en negro.
        for _ in $(seq 1 30); do
            swww img "$WALLPAPER" --transition-type none 2>/dev/null || true
            sleep 0.5
            if swww query 2>/dev/null | grep -q . && ! swww query 2>/dev/null | grep -q "currently displaying: color"; then
                break
            fi
        done
    fi
) &

# 5. Barra y entorno de escritorio Quickshell (End_4 / Illogical Impulse)
if ! pidof quickshell >/dev/null 2>&1; then
    if command -v quickshell >/dev/null 2>&1; then
        quickshell -c ii >/run/user/$(id -u)/quickshell-session.log 2>&1 &
    fi
fi

# 5.1 Gestor de tareas de Retro (btop): existe sólo en Retro, también si se arranca ya en Retro
python3 -c "import sys; sys.path.insert(0, '$HOME/.config/hypr/scripts'); import bwm_omarchy as b; b.apply_task_manager('$(python3 "$HOME/.config/hypr/scripts/bwm-theme-manager.py" get 2>/dev/null)' == 'retro')" 2>/dev/null &

# 6. Centro de notificaciones (swaync). En Retro no: allí el demonio de notificaciones es el de
#    Omarchy dentro de Quickshell (modules/ii/omarchyNotifications) y sólo uno puede tener
#    org.freedesktop.Notifications. bwm-theme-manager.py lo cierra/arranca al cambiar de estilo.
if [[ "$(python3 "$HOME/.config/hypr/scripts/bwm-theme-manager.py" get 2>/dev/null)" != "retro" ]] && ! pidof swaync >/dev/null 2>&1; then
    if command -v swaync >/dev/null 2>&1; then
        swaync >/dev/null 2>&1 &
    fi
fi

# 7. Demonio de portapapeles (cliphist con wl-paste)
if ! pgrep -f '^wl-paste --type text' >/dev/null 2>&1; then
    wl-paste --type text --watch cliphist store >/dev/null 2>&1 &
fi
if ! pgrep -f '^wl-paste --type image' >/dev/null 2>&1; then
    wl-paste --type image --watch cliphist store >/dev/null 2>&1 &
fi

# 8. Aplicaciones de inicio automático del usuario (XDG Autostart / Quickshell Autostart)
if [ -f "$HOME/.config/hypr/scripts/autostart-manager.py" ]; then
    (
        sleep 2
        python3 "$HOME/.config/hypr/scripts/autostart-manager.py" run-all
    ) &
fi

# 9. Cargar plugins (soporte CSD minimize y hyprbars para KDE Plasma)
(
    sleep 1
    # hypr-csd retired in favor of native hyprbars
    if [ -f "/home/sasel/.config/hypr/modules/theme.lua" ] && grep -q 'name = "plasma"' "/home/sasel/.config/hypr/modules/theme.lua" 2>/dev/null; then
        if ! hyprctl plugin list 2>/dev/null | grep -q "Plugin hyprbars"; then
            hyprctl plugin load "/home/sasel/.config/hypr/plugins/hyprbars-plasma.so" 2>/dev/null || true
        fi
        hyprctl keyword windowrulev2 "plugin:hyprbars:nobar, class:^(steam|steamwebhelper|firefox|firefox-bin|google-chrome.*|chromium.*|brave-browser|zen.*|vesktop|discord|armcord|webcord|spotify|antigravity|antigravity-ide|code|Code|code-oss|vscodium|cursor|claude|claude-desktop|com.anthropic.Claude|org.gnome..*|nautilus|pavucontrol|easyeffects|gamescope|signal|telegram-desktop|org.telegram.desktop|baobab|evince|loupe)$" 2>/dev/null || true
    fi
) &

# 9b. Vigilante de ventanas: monitor principal de XWayland = el del workspace 1, ventanas fuera
#     de pantalla de vuelta a su monitor y juegos sin bordes del tamaño del monitor a pantalla completa
if ! pgrep -f 'window-guard.py watch' >/dev/null 2>&1; then
    python3 "$HOME/.config/hypr/scripts/window-guard.py" watch >/dev/null 2>&1 &
fi

# 10. Asegurar que las pantallas abran en Workspace 1 (Principal 1080p) y Workspace 10 (Secundario 4K)
(
    sleep 3.5
    # Pantalla secundaria 4K -> Workspace 10
    hyprctl dispatch 'hl.dsp.focus({ monitor = "desc:LG Electronics LG ULTRAFINE 405NTVS2J655" })' 2>/dev/null || hyprctl dispatch 'hl.dsp.focus({ monitor = "DP-1" })' 2>/dev/null || true
    hyprctl dispatch 'hl.dsp.focus({ workspace = 10 })' 2>/dev/null || true

    # Pantalla principal 1080p -> Workspace 1 y enfocar
    hyprctl dispatch 'hl.dsp.focus({ monitor = "desc:HP Inc. HP X24ih 1CR1420TD4" })' 2>/dev/null || hyprctl dispatch 'hl.dsp.focus({ monitor = "DP-2" })' 2>/dev/null || true
    hyprctl dispatch 'hl.dsp.focus({ workspace = 1 })' 2>/dev/null || true
) &

