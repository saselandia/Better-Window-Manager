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
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}${BOLD}==>${NC} ${BOLD}$1${NC}"
}

print_success() {
    echo -e "${GREEN}${BOLD}✓${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}${BOLD}!${NC} $1"
}

print_error() {
    echo -e "${RED}${BOLD}✗${NC} $1"
}

usage() {
    echo "Uso: $0 [OPCIONES]"
    echo ""
    echo "Opciones:"
    echo "  --symlink        Crea enlaces simbólicos a ~/.config (Recomendado: actualizaciones automáticas vía git pull)"
    echo "  --copy           Copia los archivos a ~/.config de forma independiente"
    echo "  --check-deps     Solo comprueba las dependencias instaladas en el sistema"
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
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ==============================================================================
# 1. Verificación de Dependencias del Sistema
# ==============================================================================
print_step "Comprobando componentes del sistema..."

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
    "python3:Intérprete Python para scripts de automatización"
)

MISSING_DEPS=()

for item in "${DEPENDENCIES[@]}"; do
    bin="${item%%:*}"
    desc="${item#*:}"
    if command -v "$bin" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} ${bin} (${desc})"
    else
        echo -e "  ${YELLOW}✗${NC} ${bin} ${YELLOW}[Falta]${NC} - ${desc}"
        MISSING_DEPS+=("$bin")
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo ""
    print_warn "Hay componentes no encontrados en tu sistema."
    echo "  Recomendamos instalarlos para que todas las funciones (temas dinámicos, audio, wallpapers) funcionen al 100%."
    echo ""
    echo "  Ejemplos según tu distribución:"
    echo "   • Arch / CachyOS: paru -S hyprland quickshell-git matugen-bin swww swaync rofi-wayland kitty playerctl wl-clipboard jq python"
    echo "   • Gentoo: emerge --ask gui-wm/hyprland gui-apps/quickshell gui-apps/swww gui-apps/swaync gui-apps/rofi-wayland x11-terms/kitty media-sound/playerctl gui-apps/wl-clipboard app-misc/jq"
    echo "   • Fedora: sudo dnf install hyprland kitty playerctl wl-clipboard jq python3"
    echo ""
fi

if [ "$INSTALL_MODE" = "check" ]; then
    exit 0
fi

# ==============================================================================
# 2. Permisos ejecutables en scripts
# ==============================================================================
print_step "Verificando permisos ejecutables en scripts..."
find "$CONFIG_SOURCE/hypr/scripts" -type f \( -name "*.sh" -o -name "*.py" \) -exec chmod +x {} +
print_success "Permisos de ejecución verificados."

# ==============================================================================
# 3. Preparación de carpetas de destino y Caché
# ==============================================================================
print_step "Preparando carpetas del usuario..."
mkdir -p "$TARGET_CONFIG"
mkdir -p "$HOME/Pictures/Wallpapers"
mkdir -p "$HOME/.cache"
mkdir -p "$HOME/.local/state/quickshell/user/generated"

# Copiar fondo de pantalla por defecto si no hay ninguno activo
if [ -d "$ASSETS_DIR/wallpapers" ]; then
    mkdir -p "$HOME/Pictures/Wallpapers"
    cp -n "$ASSETS_DIR/wallpapers/"* "$HOME/Pictures/Wallpapers/" 2>/dev/null || true
    if [ ! -f "$HOME/.cache/current_wallpaper" ]; then
        FIRST_WALLPAPER="$(find "$HOME/Pictures/Wallpapers" -type f | head -n 1 || true)"
        if [ -n "$FIRST_WALLPAPER" ]; then
            echo "$FIRST_WALLPAPER" > "$HOME/.cache/current_wallpaper"
            print_success "Fondo inicial configurado: $FIRST_WALLPAPER"
        fi
    fi
fi

# ==============================================================================
# 4. Instalación de Configuraciones (Symlink o Copy)
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
)

print_step "Instalando configuraciones (Modo: ${INSTALL_MODE})..."

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

if [ -d "$BACKUP_DIR" ]; then
    echo ""
    print_warn "Tus configuraciones previas se han respaldado de forma segura en:"
    echo "  $BACKUP_DIR"
fi

echo ""
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD} ¡Instalación completada con éxito!${NC}"
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Acciones siguientes:"
echo " 1. Si estás dentro de Hyprland, recarga la configuración:"
echo "    $ hyprctl reload"
echo " 2. Para generar la paleta de colores Material You con tu fondo:"
echo "    $ ~/.config/hypr/scripts/set-wallpaper.sh <ruta-al-fondo>"
echo "    O pulsa [ALT + W] para abrir el selector visual de fondos."
echo " 3. Atajos principales:"
echo "    • Super / Win: Menú de aplicaciones / Búsqueda Quickshell"
echo "    • Alt + Tab:   Selector de ventanas con vista previa visual"
echo "    • Super + A:   Panel lateral y ajustes rápidos de Quickshell"
echo "    • Ctrl + Enter: Terminal Kitty con colores dinámicos"
echo "    • Super + L:   Pantalla de bloqueo Material You"
echo ""
