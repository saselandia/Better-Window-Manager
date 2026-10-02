#!/usr/bin/env bash
# ==============================================================================
#  Material You Hyprland Desktop Environment - Installer & Setup Script
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_SOURCE="$SCRIPT_DIR/config"
ASSETS_DIR="$SCRIPT_DIR/assets"
TARGET_CONFIG="$HOME/.config"
BACKUP_DIR="$HOME/.config/hyprland-de-backup-$(date +%Y%m%d_%H%M%S)"
INSTALL_MODE="symlink"

# Colors for terminal output
RED='[0;31m'
GREEN='[0;32m'
BLUE='[0;34m'
YELLOW='[1;33m'
CYAN='[0;36m'
MAGENTA='[0;35m'
BOLD='[1m'
NC='[0m' # No Color

print_step() {
    echo -e "
${BLUE}${BOLD}==>${NC} ${BOLD}$1${NC}"
}

print_success() {
    echo -e "  ${GREEN}${BOLD}✓${NC} $1"
}

print_warn() {
    echo -e "  ${YELLOW}${BOLD}!${NC} $1"
}

print_error() {
    echo -e "  ${RED}${BOLD}✗${NC} $1"
}

print_info() {
    echo -e "  ${CYAN}ℹ${NC} $1"
}

usage() {
    echo "Uso: $0 [OPCIONES]"
    echo ""
    echo "Opciones:"
    echo "  --symlink        Crea enlaces simbólicos a ~/.config (Recomendado: actualizaciones automáticas vía git pull)"
    echo "  --copy           Copia los archivos a ~/.config de forma independiente"
    echo "  --check-deps     Solo comprueba las dependencias y flatpaks instalados"
    echo "  -h, --help       Muestra esta ayuda"
    exit 0
}

# Parse options
while [[ $# -gt 0 ]]; do
    case "$1" in
        --symlink)
            INSTALL_MODE="symlink"
            shift
            ;;
        --copy)
            INSTALL_MODE="copy"
            shift
            ;;
        --check-deps)
            INSTALL_MODE="check"
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            print_error "Opción no reconocida: $1"
            usage
            ;;
    esac
done

echo -e "${CYAN}${BOLD}"
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║       Material You Hyprland Desktop Environment Installer        ║"
echo "║                 Nautilus • Firefox • Vesktop • Spotify            ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ==============================================================================
# 1. Verificación de Dependencias Nativas del Sistema
# ==============================================================================
print_step "1. Comprobando componentes y dependencias del sistema..."

DEPENDENCIES=(
    "hyprland:Compositor Wayland principal"
    "quickshell:Entorno de widgets, HUD y barra (Qt/QML)"
    "matugen:Generador de paletas Material You a partir del fondo de pantalla"
    "swww:Demonio de fondos de pantalla dinámicos para Wayland"
    "swaync:Centro de notificaciones gráfico"
    "rofi:Lanzador / selector de fondos (versión Wayland)"
    "kitty:Emulador de terminal GPU-accelerated"
    "playerctl:Controlador multimedia MPRIS"
    "wl-copy:Herramientas de portapapeles de Wayland (wl-clipboard)"
    "jq:Procesador JSON por línea de comandos"
    "python3:Intérprete Python para automatizaciones y persistencia"
    "nautilus:Gestor de archivos gráfico GNOME Files (tematizado con Material You)"
    "firefox:Navegador web principal nativo (tematizado con Material You)"
    "flatpak:Gestor de paquetes Flatpak (requerido para Vesktop y Spotify)"
)

MISSING_DEPS=()

for item in "${DEPENDENCIES[@]}"; do
    bin="${item%%:*}"
    desc="${item#*:}"
    if [ "$bin" = "firefox" ]; then
        if command -v firefox >/dev/null 2>&1 || command -v firefox-bin >/dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} ${BOLD}firefox${NC} - ${desc}"
        else
            echo -e "  ${YELLOW}✗${NC} ${YELLOW}[$bin]${NC} ${BOLD}[Falta]${NC} - ${desc}"
            MISSING_DEPS+=("$bin")
        fi
        continue
    fi

    if command -v "$bin" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} ${BOLD}${bin}${NC} - ${desc}"
    else
        echo -e "  ${YELLOW}✗${NC} ${YELLOW}[$bin]${NC} ${BOLD}[Falta]${NC} - ${desc}"
        MISSING_DEPS+=("$bin")
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo ""
    print_warn "Hay componentes del sistema no encontrados: ${MISSING_DEPS[*]}"
    echo "  Recomendamos instalarlos para que todas las funciones visuales y atajos operen al 100%."
    echo ""
    echo "  Comandos de instalación según tu distribución:"
    echo "   • Arch / CachyOS: paru -S hyprland quickshell-git matugen-bin swww swaync rofi-wayland kitty playerctl wl-clipboard jq python nautilus firefox flatpak"
    echo "   • Gentoo: emerge --ask gui-wm/hyprland gui-apps/quickshell gui-apps/swww gui-apps/swaync gui-apps/rofi-wayland x11-terms/kitty media-sound/playerctl gui-apps/wl-clipboard app-misc/jq gnome-base/nautilus www-client/firefox sys-apps/flatpak"
    echo "   • Fedora: sudo dnf install hyprland kitty playerctl wl-clipboard jq python3 nautilus firefox flatpak"
    echo ""
fi

# ==============================================================================
# 2. Verificación de Flatpaks Obligatorios (Vesktop & Spotify)
# ==============================================================================
print_step "2. Comprobando aplicaciones Flatpak obligatorias..."

FLATPAK_APPS=(
    "dev.vencord.Vesktop:Vesktop (Discord optimizado con Vencord y tema Material You)"
    "com.spotify.Client:Spotify Desktop (reproductor de música oficial)"
)

MISSING_FLATPAKS=()

if command -v flatpak >/dev/null 2>&1; then
    INSTALLED_FLATPAKS="$(flatpak list --app 2>/dev/null || true)"
    for app in "${FLATPAK_APPS[@]}"; do
        app_id="${app%%:*}"
        app_desc="${app#*:}"
        if echo "$INSTALLED_FLATPAKS" | grep -q "$app_id"; then
            echo -e "  ${GREEN}✓${NC} ${BOLD}${app_id}${NC} - ${app_desc}"
        else
            echo -e "  ${YELLOW}✗${NC} ${YELLOW}[$app_id]${NC} ${BOLD}[No instalado]${NC} - ${app_desc}"
            MISSING_FLATPAKS+=("$app_id")
        fi
    done

    if [ ${#MISSING_FLATPAKS[@]} -gt 0 ]; then
        echo ""
        print_warn "Puedes instalar los Flatpaks obligatorios con:"
        for m_app in "${MISSING_FLATPAKS[@]}"; do
            echo "  $ flatpak install -y flathub $m_app"
        done
        echo ""
    fi
else
    print_warn "Flatpak no está disponible. Instálalo para usar Vesktop y Spotify con temas Material You."
fi

# ==============================================================================
# 3. Verificación e Instalación de Spicetify
# ==============================================================================
print_step "3. Comprobando Spicetify (CLI para tematizar Spotify)..."

SPICETIFY_CMD=""
if command -v spicetify >/dev/null 2>&1; then
    SPICETIFY_CMD="spicetify"
elif [ -x "$HOME/.spicetify/spicetify" ]; then
    SPICETIFY_CMD="$HOME/.spicetify/spicetify"
fi

if [ -n "$SPICETIFY_CMD" ]; then
    SPICE_VER="$($SPICETIFY_CMD -v 2>/dev/null || echo 'instalado')"
    print_success "Spicetify detectado ($SPICE_VER)."
else
    print_warn "Spicetify no está instalado en el sistema."
    echo -e "  Instalando Spicetify automáticamente desde el repositorio oficial..."
    if curl -fsSL https://raw.githubusercontent.com/spicetify/cli/main/install.sh | sh; then
        SPICETIFY_CMD="$HOME/.spicetify/spicetify"
        export PATH="$HOME/.spicetify:$PATH"
        print_success "Spicetify instalado con éxito en ~/.spicetify/spicetify"
    else
        print_error "No se pudo descargar Spicetify automáticamente. Puedes instalarlo con:"
        echo "  curl -fsSL https://raw.githubusercontent.com/spicetify/cli/main/install.sh | sh"
    fi
fi

if [ "$INSTALL_MODE" = "check" ]; then
    echo ""
    print_info "Comprobación de dependencias completada."
    exit 0
fi

# ==============================================================================
# 4. Permisos ejecutables en scripts
# ==============================================================================
print_step "4. Verificando permisos ejecutables en scripts..."
find "$CONFIG_SOURCE/hypr/scripts" "$CONFIG_SOURCE/quickshell" -type f \( -name "*.sh" -o -name "*.py" \) -exec chmod +x {} + 2>/dev/null || true
print_success "Permisos de ejecución verificados en todos los scripts."

# ==============================================================================
# 5. Preparación de carpetas de destino y Caché
# ==============================================================================
print_step "5. Preparando carpetas del usuario y cachés..."
mkdir -p "$TARGET_CONFIG"
mkdir -p "$HOME/Pictures/Wallpapers"
mkdir -p "$HOME/.cache"
mkdir -p "$HOME/.local/state/quickshell/user/generated"
mkdir -p "$HOME/.var/app/dev.vencord.Vesktop/config/vesktop/themes"
mkdir -p "$HOME/.var/app/dev.vencord.Vesktop/config/vesktop/settings"
mkdir -p "$HOME/.config/spicetify/Themes/MaterialYou"

# Copiar e instalar fuentes requeridas
FONTS_DIR="$HOME/.local/share/fonts"
mkdir -p "$FONTS_DIR"
if [ -d "$ASSETS_DIR/fonts" ]; then
    echo -e "  ${BOLD}• Instalando tipografías en ~/.local/share/fonts...${NC}"
    cp -u "$ASSETS_DIR/fonts/"*.ttf "$FONTS_DIR/" 2>/dev/null || cp "$ASSETS_DIR/fonts/"*.ttf "$FONTS_DIR/" 2>/dev/null || true
    if command -v fc-cache >/dev/null 2>&1; then
        fc-cache -f "$FONTS_DIR" >/dev/null 2>&1 || true
    fi
    print_success "Fuentes requeridas instaladas y caché actualizada."
fi

# Copiar fondos incluidos si la carpeta Wallpapers está vacía
if [ -d "$ASSETS_DIR/wallpapers" ]; then
    cp -n "$ASSETS_DIR/wallpapers/"* "$HOME/Pictures/Wallpapers/" 2>/dev/null || true
    if [ ! -f "$HOME/.cache/current_wallpaper" ]; then
        FIRST_WALLPAPER="$(find "$HOME/Pictures/Wallpapers" -type f \( -name "*.jpg" -o -name "*.png" \) | head -n 1 || true)"
        if [ -n "$FIRST_WALLPAPER" ]; then
            echo "$FIRST_WALLPAPER" > "$HOME/.cache/current_wallpaper"
            print_success "Fondo inicial configurado: $FIRST_WALLPAPER"
        fi
    fi
fi

# ==============================================================================
# 6. Instalación de Configuraciones (Symlink o Copy)
# ==============================================================================
CONFIG_DIRS=(
    "hypr"
    "quickshell"
    "illogical-impulse"
    "matugen"
    "kitty"
    "rofi"
    "swaync"
    "xdg-desktop-portal"
    "gtk-3.0"
    "gtk-4.0"
)

print_step "6. Instalando configuraciones principales (Modo: ${INSTALL_MODE})..."

for cfg in "${CONFIG_DIRS[@]}"; do
    SRC="$CONFIG_SOURCE/$cfg"
    DEST="$TARGET_CONFIG/$cfg"

    if [ ! -e "$SRC" ]; then
        continue
    fi

    # Si el destino ya existe y NO es un symlink apuntando al origen
    if [ -e "$DEST" ] || [ -L "$DEST" ]; then
        CURRENT_LINK="$(readlink -f "$DEST" 2>/dev/null || true)"
        ACTUAL_SRC="$(readlink -f "$SRC" 2>/dev/null || true)"

        if [ "$CURRENT_LINK" = "$ACTUAL_SRC" ]; then
            echo -e "  ${GREEN}✓${NC} $cfg ya está enlazado correctamente."
            continue
        fi

        # Crear respaldo
        mkdir -p "$BACKUP_DIR"
        echo -e "  ${YELLOW}→${NC} Respaldando $DEST en $BACKUP_DIR/$cfg..."
        mv "$DEST" "$BACKUP_DIR/$cfg"
    fi

    if [ "$INSTALL_MODE" = "symlink" ]; then
        ln -s "$SRC" "$DEST"
        print_success "Enlazado simbólicamente: ~/.config/$cfg -> $SRC"
    else
        cp -r "$SRC" "$DEST"
        print_success "Copiado: ~/.config/$cfg"
    fi
done

# Corregir enlace de autostart en illogical-impulse
mkdir -p "$TARGET_CONFIG/illogical-impulse/actions"
ln -sf "$TARGET_CONFIG/hypr/scripts/open-autostart.sh" "$TARGET_CONFIG/illogical-impulse/actions/autostart"

# ==============================================================================
# 7. Configuración y Tematización Automatizada de Aplicaciones
# ==============================================================================
print_step "7. Aplicando temas Material You en aplicaciones..."

# ------------------------------------------------------------------------------
# 7.1 Nautilus y Entorno GTK 3/4
# ------------------------------------------------------------------------------
echo -e "
  ${BOLD}• Nautilus (GNOME Files) y Libadwaita / GTK:${NC}"
if command -v gsettings >/dev/null 2>&1; then
    gsettings set org.gnome.desktop.interface gtk-theme 'adw-gtk3-dark' 2>/dev/null || true
    gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark' 2>/dev/null || true
fi
if [ -x "$CONFIG_SOURCE/hypr/scripts/sync-nautilus.sh" ]; then
    "$CONFIG_SOURCE/hypr/scripts/sync-nautilus.sh" 2>/dev/null || true
fi
print_success "Nautilus configurado con acento dinámico y tema oscuro."

# ------------------------------------------------------------------------------
# 7.2 Vesktop (Discord con Vencord)
# ------------------------------------------------------------------------------
echo -e "
  ${BOLD}• Vesktop (Discord con Vencord):${NC}"
VESKTOP_DIR="$HOME/.var/app/dev.vencord.Vesktop/config/vesktop"
mkdir -p "$VESKTOP_DIR/themes" "$VESKTOP_DIR/settings"

# Copiar plantilla inicial de tema
if [ -f "$CONFIG_SOURCE/matugen/templates/vesktop.css" ]; then
    cp "$CONFIG_SOURCE/matugen/templates/vesktop.css" "$VESKTOP_DIR/themes/material-you.theme.css"
    cp "$CONFIG_SOURCE/matugen/templates/vesktop.css" "$VESKTOP_DIR/settings/quickCss.css"
fi

# Configurar automáticamente settings.json de Vesktop para activar el tema
python3 -c "
import json, os

settings_path = os.path.expanduser('~/.var/app/dev.vencord.Vesktop/config/vesktop/settings/settings.json')
data = {}
if os.path.isfile(settings_path):
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        data = {}

data['useQuickCss'] = True
themes = data.get('enabledThemes', [])
if 'material-you.theme.css' not in themes:
    themes.append('material-you.theme.css')
data['enabledThemes'] = themes

os.makedirs(os.path.dirname(settings_path), exist_ok=True)
with open(settings_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4)
" 2>/dev/null || true
print_success "Tema Material You y QuickCSS activados automáticamente en Vesktop."

# ------------------------------------------------------------------------------
# 7.3 Spotify y Spicetify
# ------------------------------------------------------------------------------
echo -e "
  ${BOLD}• Spotify y Spicetify:${NC}"
mkdir -p "$HOME/.config/spicetify/Themes/MaterialYou"
if [ -d "$CONFIG_SOURCE/spicetify/Themes/MaterialYou" ]; then
    cp -r "$CONFIG_SOURCE/spicetify/Themes/MaterialYou/"* "$HOME/.config/spicetify/Themes/MaterialYou/" 2>/dev/null || true
    print_success "Tema MaterialYou instalado en ~/.config/spicetify/Themes/MaterialYou"
fi

# Detectar ruta de Spotify Flatpak
SPOTIFY_USER_PATH="$HOME/.local/share/flatpak/app/com.spotify.Client/x86_64/stable/active/files/extra/share/spotify"
SPOTIFY_SYS_PATH="/var/lib/flatpak/app/com.spotify.Client/x86_64/stable/active/files/extra/share/spotify"
SPOTIFY_PREFS="$HOME/.var/app/com.spotify.Client/config/spotify/prefs"

ACTUAL_SPOTIFY_PATH=""
if [ -d "$SPOTIFY_USER_PATH" ]; then
    ACTUAL_SPOTIFY_PATH="$SPOTIFY_USER_PATH"
    chmod a+wr "$SPOTIFY_USER_PATH" "$SPOTIFY_USER_PATH/Apps" -R 2>/dev/null || true
elif [ -d "$SPOTIFY_SYS_PATH" ]; then
    ACTUAL_SPOTIFY_PATH="$SPOTIFY_SYS_PATH"
fi

if [ -n "$SPICETIFY_CMD" ]; then
    "$SPICETIFY_CMD" config current_theme MaterialYou color_scheme MaterialYou inject_css 1 replace_colors 1 2>/dev/null || true
    if [ -n "$ACTUAL_SPOTIFY_PATH" ]; then
        "$SPICETIFY_CMD" config spotify_path "$ACTUAL_SPOTIFY_PATH" prefs_path "$SPOTIFY_PREFS" 2>/dev/null || true
        # Intentar aplicar spicetify si los archivos tienen permisos
        "$SPICETIFY_CMD" backup apply 2>/dev/null || "$SPICETIFY_CMD" apply 2>/dev/null || true
    fi
    print_success "Spicetify configurado con el tema MaterialYou."
else
    print_warn "Spicetify no configurado completamente. Ejecuta 'spicetify apply' una vez instalado Spotify."
fi

# ------------------------------------------------------------------------------
# 7.4 Firefox (Binario Nativo)
# ------------------------------------------------------------------------------
echo -e "
  ${BOLD}• Firefox (userChrome.css y paleta dinámica):${NC}"
mkdir -p "$HOME/.cache"
touch "$HOME/.cache/material-you-firefox.css"

FF_PROFILES_DIR="$HOME/.mozilla/firefox"
FOUND_FF_PROFILES=0

if [ -d "$FF_PROFILES_DIR" ]; then
    for prof in "$FF_PROFILES_DIR"/*; do
        if [ -d "$prof" ] && [ -f "$prof/prefs.js" -o -f "$prof/user.js" -o "${prof##*.}" = "default-release" -o "${prof##*.}" = "default" ]; then
            FOUND_FF_PROFILES=$((FOUND_FF_PROFILES + 1))
            CHROME_DIR="$prof/chrome"
            mkdir -p "$CHROME_DIR"
            
            # Copiar userChrome.css
            cp "$CONFIG_SOURCE/firefox/userChrome.css" "$CHROME_DIR/userChrome.css"
            
            # Enlazar material-you.css dinámico a la caché de matugen
            ln -sf "$HOME/.cache/material-you-firefox.css" "$CHROME_DIR/material-you.css"

            # Instalar extensión Pywalfox en el perfil
            EXT_DIR="$prof/extensions"
            mkdir -p "$EXT_DIR"
            if [ -f "$CONFIG_SOURCE/firefox/extensions/pywalfox@frewacom.org.xpi" ]; then
                cp "$CONFIG_SOURCE/firefox/extensions/pywalfox@frewacom.org.xpi" "$EXT_DIR/pywalfox@frewacom.org.xpi"
            fi

            # Inyectar preferencia para activar hojas de estilo personalizadas
            USER_JS="$prof/user.js"
            if [ ! -f "$USER_JS" ] || ! grep -q "toolkit.legacyUserProfileCustomizations.stylesheets" "$USER_JS"; then
                echo 'user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);' >> "$USER_JS"
                echo 'user_pref("browser.zoom.full", true);' >> "$USER_JS"
            fi
            print_success "Perfil configurado: $(basename "$prof")"
        fi
    done
fi

# Configuración del host nativo de Pywalfox
mkdir -p "$HOME/.mozilla/native-messaging-hosts"
PYWALFOX_HOST_JSON="$HOME/.mozilla/native-messaging-hosts/pywalfox.json"
PYWALFOX_BIN="$HOME/.local/share/pywalfox-venv/bin/pywalfox"

if [ ! -x "$PYWALFOX_BIN" ] && ! command -v pywalfox >/dev/null 2>&1; then
    if command -v python3 >/dev/null 2>&1; then
        echo -e "    Instalando host nativo de Pywalfox en entorno virtual..."
        python3 -m venv "$HOME/.local/share/pywalfox-venv" 2>/dev/null || true
        if [ -x "$HOME/.local/share/pywalfox-venv/bin/pip" ]; then
            "$HOME/.local/share/pywalfox-venv/bin/pip" install --quiet pywalfox 2>/dev/null || true
        fi
    fi
fi

if command -v pywalfox >/dev/null 2>&1; then
    PYWALFOX_BIN="$(command -v pywalfox)"
fi

if [ -x "$PYWALFOX_BIN" ]; then
    cat > "$PYWALFOX_HOST_JSON" <<EOF
{
  "name": "pywalfox",
  "description": "Automatically theme your browser using the colors generated by Pywal",
  "path": "$PYWALFOX_BIN",
  "type": "stdio",
  "allowed_extensions": [ "pywalfox@frewacom.org" ]
}
EOF
    print_success "Host nativo de Pywalfox configurado en ~/.mozilla/native-messaging-hosts/pywalfox.json"
fi

if [ "$FOUND_FF_PROFILES" -eq 0 ]; then
    print_warn "No se encontraron perfiles de Firefox en ~/.mozilla/firefox/."
    echo "  Abre Firefox por primera vez y vuelve a ejecutar './install.sh' para tematizarlo."
else
    print_success "Firefox configurado con éxito con userChrome.css y soporte de estilos heredados."
fi

# ==============================================================================
# 8. Sincronización Inicial con Wallpaper Actual
# ==============================================================================
CURRENT_WALL="$(cat "$HOME/.cache/current_wallpaper" 2>/dev/null || true)"
if [ -n "$CURRENT_WALL" ] && [ -f "$CURRENT_WALL" ]; then
    print_step "8. Generando paleta inicial de colores Material You..."
    if [ -x "$TARGET_CONFIG/hypr/scripts/set-wallpaper.sh" ]; then
        "$TARGET_CONFIG/hypr/scripts/set-wallpaper.sh" "$CURRENT_WALL" >/dev/null 2>&1 || true
    elif command -v matugen >/dev/null 2>&1; then
        matugen image --source-color-index 0 "$CURRENT_WALL" 2>/dev/null || true
        if [ -x "$TARGET_CONFIG/hypr/scripts/sync-nautilus.sh" ]; then
            "$TARGET_CONFIG/hypr/scripts/sync-nautilus.sh" 2>/dev/null || true
        fi
    fi
    print_success "Esquema de colores Material You generado para todas las aplicaciones."
fi

if [ -d "$BACKUP_DIR" ]; then
    echo ""
    print_warn "Tus configuraciones previas se han respaldado de forma segura en:"
    echo "  $BACKUP_DIR"
fi

echo ""
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD} ¡Instalación y tematización completadas con éxito!${NC}"
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Acciones siguientes:"
echo " 1. Si estás dentro de Hyprland, recarga la configuración:"
echo "    $ hyprctl reload"
echo " 2. Para generar la paleta de colores Material You con cualquier fondo:"
echo "    $ ~/.config/hypr/scripts/set-wallpaper.sh <ruta-al-fondo>"
echo "    O pulsa [ALT + W] para abrir el selector visual interactivo."
echo " 3. Aplicaciones tematizadas:"
echo "    • Nautilus:    Gestor de archivos (Super + E) con colores GTK 3/4 dinámicos."
echo "    • Firefox:     userChrome.css activo. (Reinicia Firefox si estaba abierto)."
echo "    • Vesktop:     Vencord + QuickCSS con variables Material You sincronizadas."
echo "    • Spotify:     Tema MaterialYou inyectado mediante Spicetify."
echo " 4. Atajos principales:"
echo "    • Super / Win: Menú de aplicaciones / Búsqueda Quickshell"
echo "    • Alt + Tab:   Selector de ventanas con vista previa visual"
echo "    • Super + E:   Explorador de archivos Nautilus"
echo "    • Super + A:   Panel lateral y ajustes rápidos de Quickshell"
echo "    • Ctrl + Enter: Terminal Kitty con colores dinámicos"
echo "    • Super + L:   Pantalla de bloqueo Material You"
echo ""
