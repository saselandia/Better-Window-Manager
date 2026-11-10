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

# Fondos de vídeo (Omarchy 4.5): swww, las paletas y el bloqueo usan su primer fotograma; el vídeo
# lo reproduce el motor de cada skin (bwm-video-wallpaper: OWE en Retro, mpvpaper en las demás)
VIDEO_WALLPAPER="$HOME/.config/hypr/scripts/bwm-video-wallpaper"
STILL="$WALLPAPER"
IS_VIDEO=0
if "$VIDEO_WALLPAPER" is-video "$WALLPAPER"; then
    IS_VIDEO=1
    STILL="$("$VIDEO_WALLPAPER" poster "$WALLPAPER")" || {
        echo "Error: no se pudo sacar el primer fotograma de '$WALLPAPER' (¿falta ffmpeg?)." >&2
        exit 1
    }
fi

# 1. Asegurar que el demonio swww-daemon esté en ejecución
# swww cambió de nombre a awww (mismo uso y opciones): vale cualquiera de los dos
WALL_BIN="$(command -v swww || command -v awww || echo swww)"
WALL_DAEMON="$(basename "$WALL_BIN")-daemon"
if ! pgrep -x "$WALL_DAEMON" > /dev/null 2>&1; then
    echo "Iniciando $WALL_DAEMON..."
    "$WALL_DAEMON" &
    # Esperar hasta que el demonio responda
    TIMEOUT=20
    COUNT=0
    until "$WALL_BIN" query > /dev/null 2>&1 || [ "$COUNT" -ge "$TIMEOUT" ]; do
        sleep 0.1
        COUNT=$((COUNT + 1))
    done
fi

# 2. Cambiar fondo (la animación es la de cada skin)
CURRENT_THEME="$(python3 /home/sasel/.config/hypr/scripts/bwm-theme-manager.py get 2>/dev/null || echo "default")"

echo "Aplicando wallpaper: $WALLPAPER"
# default (end-4) y Retro pintan el fondo en el shell, como sus originales (end-4: Background.qml;
# Omarchy: su plugin background con su transición): swww sólo queda debajo, sin animación.
# Breeze (Kde plasma) sigue con swww y su transición
if [[ "${BWM_SKIN_SWITCH:-0}" == "1" || "$CURRENT_THEME" != "plasma" ]]; then
    "$WALL_BIN" img "$STILL" --transition-type none
else
    "$WALL_BIN" img "$STILL" \
        --transition-type grow --transition-pos center --transition-step 90 \
        --transition-duration 2 --transition-fps 60
fi

# Retro: el fondo de Omarchy sigue ~/.local/state/omarchy/current/background y se le pide la
# transición por IPC, como omarchy-theme-bg-set
if [[ "$CURRENT_THEME" == "retro" ]]; then
    OMARCHY_BG_LINK="$HOME/.local/state/omarchy/current/background"
    mkdir -p "$(dirname "$OMARCHY_BG_LINK")"
    PREVIOUS_BG="$(readlink -f "$OMARCHY_BG_LINK" 2>/dev/null || true)"
    # Con OWE el enlace apunta al vídeo (owed lo reproduce y el fondo del shell se suspende);
    # sin OWE, a su primer fotograma
    SHELL_BG="$STILL"
    if [[ "$IS_VIDEO" == "1" && -x "${XDG_DATA_HOME:-$HOME/.local/share}/bwm/owe/bin/owed" ]]; then
        SHELL_BG="$WALLPAPER"
    fi
    # Sin el plugin WebP de Qt (dev-qt/qtimageformats) el shell no abre los .webp de los temas:
    # se le da una copia JPG en caché
    QT_WEBP=0
    for qt_plugins in /usr/lib64/qt6/plugins /usr/lib/qt6/plugins /usr/lib/x86_64-linux-gnu/qt6/plugins; do
        [[ -e "$qt_plugins/imageformats/libqwebp.so" ]] && QT_WEBP=1
    done
    if [[ "${SHELL_BG,,}" == *.webp && "$QT_WEBP" == "0" ]] && command -v magick >/dev/null 2>&1; then
        WEBP_CACHE="$HOME/.cache/bwm/omarchy-background"
        mkdir -p "$WEBP_CACHE"
        WEBP_SRC="$SHELL_BG"
        SHELL_BG="$WEBP_CACHE/$(printf '%s' "$WEBP_SRC" | md5sum | cut -d' ' -f1).jpg"
        if [[ ! -s "$SHELL_BG" || "$WEBP_SRC" -nt "$SHELL_BG" ]]; then
            magick "$WEBP_SRC" -quality 92 "$SHELL_BG.tmp.jpg" && mv "$SHELL_BG.tmp.jpg" "$SHELL_BG" || SHELL_BG="$WEBP_SRC"
        fi
    fi
    ln -sfn "$SHELL_BG" "$OMARCHY_BG_LINK"
    # Intro del fondo (Omarchy 4.5), si tiene y están activadas: sustituye a la transición. Corre
    # aparte para que los colores de las apps cambien mientras se ve, como en Omarchy
    INTRO=""
    if [[ "${BWM_SKIN_SWITCH:-0}" != "1" && "$IS_VIDEO" == "0" ]]; then
        INTRO="$("$VIDEO_WALLPAPER" intro-for "$WALLPAPER" 2>/dev/null || true)"
    fi
    if [[ "${BWM_SKIN_SWITCH:-0}" == "1" ]]; then
        quickshell -c ii ipc call background setInstant "$SHELL_BG" >/dev/null 2>&1 || true
    elif [[ -n "$INTRO" ]]; then
        setsid -f "$VIDEO_WALLPAPER" intro "$INTRO" "$SHELL_BG" >/dev/null 2>&1
    else
        quickshell -c ii ipc call background transition "$PREVIOUS_BG" "$SHELL_BG" >/dev/null 2>&1 || true
    fi
fi

# Motor de vídeo de la skin activa, o ninguno con una imagen
if [[ "$IS_VIDEO" == "1" ]]; then
    "$VIDEO_WALLPAPER" play "$WALLPAPER" || true
elif [[ -z "${INTRO:-}" ]]; then
    "$VIDEO_WALLPAPER" stop || true
fi

mkdir -p "$HOME/.cache"
echo "$WALLPAPER" > "$HOME/.cache/current_wallpaper"

echo "$WALLPAPER" > "$HOME/.cache/current_wallpaper_${CURRENT_THEME}"

# 2.2 Sincronizar ruta del wallpaper con Quickshell / Illogical Impulse
if [ -f "$HOME/.config/illogical-impulse/config.json" ] && command -v jq >/dev/null 2>&1; then
    jq --arg path "$WALLPAPER" --arg still "$STILL" '.background.wallpaperPath = $path | .background.thumbnailPath = $still' "$HOME/.config/illogical-impulse/config.json" > "$HOME/.config/illogical-impulse/config.json.tmp" && mv "$HOME/.config/illogical-impulse/config.json.tmp" "$HOME/.config/illogical-impulse/config.json"
fi

# 2.3 Sincronizar con el perfil aislado del estilo activo (config-retro.json / config-default.json)
PROFILE_JSON="$HOME/.config/illogical-impulse/config-${CURRENT_THEME}.json"
if [ -f "$PROFILE_JSON" ] && command -v jq >/dev/null 2>&1; then
    jq --arg path "$WALLPAPER" --arg still "$STILL" '.background.wallpaperPath = $path | .background.thumbnailPath = $still' "$PROFILE_JSON" > "$PROFILE_JSON.tmp" && mv "$PROFILE_JSON.tmp" "$PROFILE_JSON"
fi

# 3. Generar la paleta de colores según el estilo
if [[ "$CURRENT_THEME" == "plasma" ]]; then
    echo "Estilo Breeze (Kde plasma) activo: los colores son los del esquema de Plasma (sin Matugen); el fondo no los cambia."
    python3 /home/sasel/.config/hypr/scripts/bwm-theme-manager.py apply-plasma-colors 2>/dev/null || true
elif [[ "$CURRENT_THEME" == "retro" ]]; then
    # Sin matugen: bwm_omarchy.py genera desde el fondo una paleta estilo Omarchy y rellena
    # con ella todas las plantillas de apps (más la capa TUI y el tema Spicetify de Retro)
    echo "Sincronizando paleta Omarchy del wallpaper para todas las apps..."
    python3 /home/sasel/.config/hypr/scripts/bwm-theme-manager.py apply-wallpaper-colors "$WALLPAPER" 2>/dev/null || true
else
    echo "Extrayendo colores del wallpaper..."
    bash "$HOME/.config/quickshell/ii/scripts/colors/switchwall.sh" --colors-only --image "$STILL"
    # default (end-4) already published the shell palette and queued its app hooks.
    if [[ "${BWM_SKIN_SWITCH:-0}" != "1" ]]; then
        python3 "$HOME/.config/hypr/scripts/bwm_boot.py" render >/dev/null 2>&1 &
    fi
    exit 0
fi

# El gestor hace una sola recarga después de generar la paleta y ajustar las ventanas.
# Sus hooks heredan esta política aunque terminen en segundo plano.
if [[ "${BWM_SKIN_SWITCH:-0}" == "1" ]]; then
    exit 0
fi

# 3.1 Forzar recarga de colores en Quickshell (barra y widgets)
quickshell -c ii ipc call theme reload 2>/dev/null || true
quickshell -c ii ipc call retro reload 2>/dev/null || true

# 4. Actualizar colores en Firefox en caliente sin reiniciar
~/.local/share/pywalfox-venv/bin/pywalfox update 2>/dev/null || true

# 5. Sincronizar Nautilus / GNOME en caliente
~/.config/hypr/scripts/sync-nautilus.sh 2>/dev/null || true

# 6. Tema de arranque / inicio de sesión con los colores nuevos (lo instala el servicio
#    root de install-boot-theme.sh --auto, si está activado)
python3 ~/.config/hypr/scripts/bwm_boot.py render >/dev/null 2>&1 &

# 7. Recargar Hyprland para aplicar la nueva paleta en caliente
echo "Recargando configuración de Hyprland..."
hyprctl reload

echo "¡Fondo y tema Material You actualizados con éxito!"
