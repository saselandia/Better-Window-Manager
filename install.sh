#!/usr/bin/env bash
# ==============================================================================
#  BWM (Better Window Manager) - instalador
#
#  BWM es un gestor de ventanas que reúne a los demás como skins (Default = end-4 /
#  illogical-impulse, Retro = Omarchy, KDE Plasma). Lo primero que hace este instalador es
#  comprobar que el equipo tiene todo lo que necesitan el núcleo y cada skin para pintar la
#  pantalla (config/hypr/skins/*.json, scripts/bwm-requirements.py). Si falta algo, lo dice,
#  da los comandos para tu distribución y sale sin tocar nada.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_SOURCE="$SCRIPT_DIR/config"
ASSETS_DIR="$SCRIPT_DIR/assets"
SCRIPTS_SOURCE="$CONFIG_SOURCE/hypr/scripts"
REQUIREMENTS="$SCRIPTS_SOURCE/bwm-requirements.py"
TARGET_CONFIG="$HOME/.config"
BACKUP_DIR="$HOME/.config/hyprland-de-backup-$(date +%Y%m%d_%H%M%S)"
INSTALL_MODE="symlink"
LOGIN_SETUP="ask"    # ask | yes | no: pantalla de inicio de sesión SDDM estilo Omarchy
PLUGINS_SETUP="yes"  # yes | no: compilar ai-usagebar para el plugin preinstalado de uso de IA
SPICETIFY_SETUP="ask" # ask | yes | no: descargar Spicetify si Spotify está instalado
SKINS=()             # vacío = las tres skins de la release

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

print_step() { echo -e "\n${BLUE}${BOLD}==>${NC} ${BOLD}$1${NC}"; }
print_success() { echo -e "  ${GREEN}${BOLD}✓${NC} $1"; }
print_warn() { echo -e "  ${YELLOW}${BOLD}!${NC} $1"; }
print_error() { echo -e "  ${RED}${BOLD}✗${NC} $1"; }
print_info() { echo -e "  ${CYAN}ℹ${NC} $1"; }

usage() {
    cat <<EOF
Uso: $0 [OPCIONES]

Opciones:
  --symlink          Enlaza ~/.config al repositorio (recomendado: git pull actualiza BWM)
  --copy             Copia los archivos a ~/.config
  --check            Sólo comprueba los requisitos y dice cómo instalar lo que falta
  --skins A,B        Instala sólo estas skins (default, retro, plasma). Por defecto, las tres
  --login            Configura sin preguntar el inicio de sesión SDDM estilo Omarchy (pide sudo)
  --no-login         No toca el inicio de sesión ni el arranque
  --no-plugins       No compila ai-usagebar (plugin de uso de IA de la skin Retro)
  --spicetify        Descarga Spicetify sin preguntar si Spotify está instalado
  --no-spicetify     No descarga Spicetify
  -h, --help         Muestra esta ayuda

Después de instalar, \`bwm\` abre la bienvenida (skins y sus requisitos) y \`bwm check\`
vuelve a comprobar los requisitos.
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --symlink) INSTALL_MODE="symlink" ;;
        --copy) INSTALL_MODE="copy" ;;
        --check|--check-deps) INSTALL_MODE="check" ;;
        --skins) shift; IFS=',' read -r -a SKINS <<< "${1:-}" ;;
        --skins=*) IFS=',' read -r -a SKINS <<< "${1#--skins=}" ;;
        --login) LOGIN_SETUP="yes" ;;
        --no-login) LOGIN_SETUP="no" ;;
        --plugins) PLUGINS_SETUP="yes" ;;
        --no-plugins) PLUGINS_SETUP="no" ;;
        --spicetify) SPICETIFY_SETUP="yes" ;;
        --no-spicetify) SPICETIFY_SETUP="no" ;;
        -h|--help) usage ;;
        *) print_error "Opción no reconocida: $1"; usage ;;
    esac
    shift
done

echo -e "${CYAN}${BOLD}"
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                 BWM · Better Window Manager                       ║"
echo "║   Un gestor de ventanas que reúne a los demás como skins          ║"
echo "║          Default (end-4) · Retro (Omarchy) · KDE Plasma           ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ==============================================================================
# 1. Requisitos del núcleo y de cada skin (sale si falta alguno)
# ==============================================================================
print_step "1. Comprobando los requisitos de BWM y de sus skins..."

if ! command -v python3 >/dev/null 2>&1; then
    print_error "Falta Python 3 (≥ 3.11): lo necesita el propio comprobador de requisitos."
    echo "  Gentoo: sudo emerge --ask dev-lang/python    Arch: sudo pacman -S python"
    echo "  Fedora: sudo dnf install python3             Debian/Ubuntu: sudo apt install python3"
    exit 1
fi

SKIN_ARGS=()
for skin in "${SKINS[@]}"; do
    [[ -n "$skin" ]] && SKIN_ARGS+=(--skin "$skin")
done

CHECK_ARGS=(check "${SKIN_ARGS[@]}")
[[ "$INSTALL_MODE" == "check" ]] || CHECK_ARGS+=(--pre-install)
set +e
python3 "$REQUIREMENTS" "${CHECK_ARGS[@]}"
CHECK_STATUS=$?
set -e

if [[ "$INSTALL_MODE" == "check" ]]; then
    exit "$CHECK_STATUS"
fi
if [[ $CHECK_STATUS -eq 2 ]]; then
    exit 2
fi
if [[ $CHECK_STATUS -ne 0 ]]; then
    echo ""
    print_error "Faltan requisitos: instala lo de arriba y vuelve a ejecutar ./install.sh"
    print_info "Si sólo quieres algunas skins: ./install.sh --skins default,retro"
    exit 1
fi
print_success "Requisitos completos (lo marcado como opcional se puede instalar después)."

# ==============================================================================
# 2. Permisos ejecutables en scripts
# ==============================================================================
print_step "2. Permisos de ejecución de los scripts..."
find "$SCRIPTS_SOURCE" "$CONFIG_SOURCE/quickshell" -type f \( -name "*.sh" -o -name "*.py" \) -exec chmod +x {} + 2>/dev/null || true
chmod +x "$SCRIPTS_SOURCE/bwm" "$SCRIPTS_SOURCE/bwm-terminal" "$SCRIPTS_SOURCE"/omarchy-shims/* 2>/dev/null || true
print_success "Listo."

# ==============================================================================
# 3. Carpetas del usuario, cursores, fuentes y fondos
# ==============================================================================
print_step "3. Carpetas del usuario, cursores, fuentes y fondos..."
mkdir -p "$TARGET_CONFIG" "$HOME/Pictures/Wallpapers" "$HOME/.cache" "$HOME/.local/bin" \
    "$HOME/.local/state/quickshell/user/generated" "$HOME/.config/bwm"

ICONS_DIR="$HOME/.local/share/icons"
mkdir -p "$ICONS_DIR" "$HOME/.icons"
if [ -d "$ASSETS_DIR/cursors" ]; then
    cp -r "$ASSETS_DIR/cursors/"* "$ICONS_DIR/" 2>/dev/null || true
    cp -r "$ASSETS_DIR/cursors/"* "$HOME/.icons/" 2>/dev/null || true
    if command -v flatpak >/dev/null 2>&1; then
        flatpak override --filesystem=~/.icons:ro --filesystem=~/.local/share/icons:ro --user 2>/dev/null || true
    fi
    print_success "Cursores instalados (Bibata-Modern-Classic, Bibata-Modern-Ice)."
fi

FONTS_DIR="$HOME/.local/share/fonts"
mkdir -p "$FONTS_DIR"
if [ -d "$ASSETS_DIR/fonts" ]; then
    cp -u "$ASSETS_DIR/fonts/"*.ttf "$FONTS_DIR/" 2>/dev/null || true
    fc-cache -f "$FONTS_DIR" >/dev/null 2>&1 || true
    print_success "Fuentes de BWM instaladas (Material Symbols, Google Sans Flex, JetBrainsMono Nerd Font)."
fi

if [ -d "$ASSETS_DIR/wallpapers" ]; then
    cp -n "$ASSETS_DIR/wallpapers/"* "$HOME/Pictures/Wallpapers/" 2>/dev/null || true
    if [ ! -f "$HOME/.cache/current_wallpaper" ]; then
        FIRST_WALLPAPER="$(find "$HOME/Pictures/Wallpapers" -type f \( -name "*.jpg" -o -name "*.png" \) | head -n 1 || true)"
        if [ -n "$FIRST_WALLPAPER" ]; then
            echo "$FIRST_WALLPAPER" > "$HOME/.cache/current_wallpaper"
            print_success "Fondo inicial: $FIRST_WALLPAPER"
        fi
    fi
fi

# ==============================================================================
# 4. Configuraciones (enlaces o copia)
# ==============================================================================
CONFIG_DIRS=(hypr quickshell illogical-impulse matugen kitty rofi swaync xdg-desktop-portal gtk-3.0 gtk-4.0 btop)

print_step "4. Instalando las configuraciones (modo: ${INSTALL_MODE})..."
for cfg in "${CONFIG_DIRS[@]}"; do
    SRC="$CONFIG_SOURCE/$cfg"
    DEST="$TARGET_CONFIG/$cfg"
    [ -e "$SRC" ] || continue

    if [ -e "$DEST" ] || [ -L "$DEST" ]; then
        if [ "$(readlink -f "$DEST" 2>/dev/null || true)" = "$(readlink -f "$SRC" 2>/dev/null || true)" ]; then
            echo -e "  ${GREEN}✓${NC} $cfg ya está enlazado."
            continue
        fi
        mkdir -p "$BACKUP_DIR"
        echo -e "  ${YELLOW}→${NC} Respaldando $DEST en $BACKUP_DIR/$cfg..."
        mv "$DEST" "$BACKUP_DIR/$cfg"
    fi

    if [ "$INSTALL_MODE" = "symlink" ]; then
        ln -s "$SRC" "$DEST"
        print_success "~/.config/$cfg -> $SRC"
    else
        cp -r "$SRC" "$DEST"
        print_success "Copiado: ~/.config/$cfg"
    fi
done

mkdir -p "$TARGET_CONFIG/illogical-impulse/actions"
ln -sf "$TARGET_CONFIG/hypr/scripts/open-autostart.sh" "$TARGET_CONFIG/illogical-impulse/actions/autostart"

# ==============================================================================
# 5. Comando bwm, comandos de Omarchy y bienvenida
# ==============================================================================
print_step "5. Comando bwm y bienvenida..."
# El comando apunta al repositorio: así funciona también con --copy y con la instalación a medias
ln -sfn "$SCRIPTS_SOURCE/bwm" "$HOME/.local/bin/bwm"
print_success "Comando bwm en ~/.local/bin (abre la bienvenida; bwm help para más)."
case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) print_warn "~/.local/bin no está en tu PATH: añádelo para poder escribir bwm en la terminal." ;;
esac

# Sustitutos de los comandos omarchy-* que usan los paneles y plugins de Retro (enlaces en ~/.local/bin)
"$SCRIPTS_SOURCE/bwm-plugin.sh" catalog >/dev/null 2>&1 \
    && print_success "Comandos omarchy-* de la skin Retro enlazados." \
    || print_warn "No se pudieron enlazar los comandos omarchy-* (repítelo con: bwm-plugin.sh catalog)."

# La bienvenida sale en cada inicio de sesión hasta que se desactive desde ella (o bwm startup off)
if [ ! -f "$HOME/.config/bwm/welcome.json" ]; then
    "$SCRIPTS_SOURCE/bwm" startup on >/dev/null
fi
print_success "Bienvenida activada al iniciar sesión."

# ==============================================================================
# 6. Plugin hyprbars de la skin KDE Plasma (compilado para tu Hyprland)
# ==============================================================================
if [[ ${#SKINS[@]} -eq 0 || " ${SKINS[*]} " == *" plasma "* ]]; then
    PLUGIN_STATE="$(python3 "$REQUIREMENTS" check --skin plasma --json 2>/dev/null \
        | python3 -c 'import json,sys; d=json.load(sys.stdin); print(next((r["status"] for s in d["skins"] for r in s["requires"] if r["id"]=="hyprbars-plasma"), ""))' 2>/dev/null || true)"
    if [[ "$PLUGIN_STATE" == "build" ]]; then
        print_step "6. Compilando el plugin hyprbars para tu versión de Hyprland..."
        # make install instala con un renombrado atómico: nunca sobrescribe el .so cargado
        if (cd "$SCRIPT_DIR/src/hyprbars" && make clean >/dev/null && make >/dev/null && make install >/dev/null); then
            print_success "Plugin compilado. Se carga al volver a iniciar sesión en la skin KDE Plasma."
        else
            print_warn "No se pudo compilar. Repítelo con: cd $SCRIPT_DIR/src/hyprbars && make && make install"
        fi
    fi
fi

# ==============================================================================
# 7. Temas de las aplicaciones
# ==============================================================================
print_step "7. Temas de las aplicaciones..."

# GTK / Nautilus: el tema BWM-1/BWM-2 sigue a la skin activa (gtk-theme.py)
python3 "$SCRIPTS_SOURCE/gtk-theme.py" set dark >/dev/null 2>&1 || true
gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark' 2>/dev/null || true
"$SCRIPTS_SOURCE/sync-nautilus.sh" >/dev/null 2>&1 || true
print_success "GTK y Nautilus siguen a la skin."

# Vesktop: activa bwm.theme.css (lo escribe la paleta de cada skin y Vencord lo recarga en vivo)
if [ -d "$HOME/.var/app/dev.vencord.Vesktop" ] || [ -d "$HOME/.config/vesktop" ]; then
    (cd "$SCRIPTS_SOURCE" && python3 -c 'import bwm_omarchy; bwm_omarchy.vesktop_enable_theme()') >/dev/null 2>&1 \
        && print_success "Vesktop: tema BWM activado." \
        || print_warn "Vesktop: no se pudo activar el tema BWM."
fi

# Spotify + Spicetify (sólo si Spotify está instalado)
SPOTIFY_USER_PATH="$HOME/.local/share/flatpak/app/com.spotify.Client/x86_64/stable/active/files/extra/share/spotify"
SPOTIFY_SYS_PATH="/var/lib/flatpak/app/com.spotify.Client/x86_64/stable/active/files/extra/share/spotify"
SPOTIFY_PREFS="$HOME/.var/app/com.spotify.Client/config/spotify/prefs"
SPOTIFY_PATH=""
[ -d "$SPOTIFY_USER_PATH" ] && SPOTIFY_PATH="$SPOTIFY_USER_PATH"
[ -z "$SPOTIFY_PATH" ] && [ -d "$SPOTIFY_SYS_PATH" ] && SPOTIFY_PATH="$SPOTIFY_SYS_PATH"
if [ -n "$SPOTIFY_PATH" ]; then
    SPICETIFY_CMD="$(command -v spicetify || true)"
    [ -z "$SPICETIFY_CMD" ] && [ -x "$HOME/.spicetify/spicetify" ] && SPICETIFY_CMD="$HOME/.spicetify/spicetify"
    if [ -z "$SPICETIFY_CMD" ] && [ "$SPICETIFY_SETUP" = "ask" ] && [ -t 0 ]; then
        read -r -p "  Spotify está instalado. ¿Descargar Spicetify (github.com/spicetify) para tematizarlo? [s/N] " reply
        case "$reply" in [sSyY]*) SPICETIFY_SETUP="yes" ;; *) SPICETIFY_SETUP="no" ;; esac
    fi
    if [ -z "$SPICETIFY_CMD" ] && [ "$SPICETIFY_SETUP" = "yes" ]; then
        if curl -fsSL https://raw.githubusercontent.com/spicetify/cli/main/install.sh | sh; then
            SPICETIFY_CMD="$HOME/.spicetify/spicetify"
        else
            print_warn "No se pudo descargar Spicetify."
        fi
    fi
    if [ -n "$SPICETIFY_CMD" ]; then
        mkdir -p "$HOME/.config/spicetify/Themes"
        cp -r "$CONFIG_SOURCE/spicetify/Themes/"* "$HOME/.config/spicetify/Themes/" 2>/dev/null || true
        [ "$SPOTIFY_PATH" = "$SPOTIFY_USER_PATH" ] && chmod a+wr "$SPOTIFY_PATH" "$SPOTIFY_PATH/Apps" -R 2>/dev/null || true
        "$SPICETIFY_CMD" config current_theme MaterialYou color_scheme MaterialYou inject_css 1 replace_colors 1 \
            spotify_path "$SPOTIFY_PATH" prefs_path "$SPOTIFY_PREFS" >/dev/null 2>&1 || true
        "$SPICETIFY_CMD" backup apply >/dev/null 2>&1 || "$SPICETIFY_CMD" apply >/dev/null 2>&1 || true
        print_success "Spotify: tema de Spicetify configurado (cambia con la skin)."
    else
        print_info "Spotify sin Spicetify: no seguirá a la skin. Instálalo cuando quieras y repite ./install.sh"
    fi
fi

# Firefox: userChrome.css con la paleta + Pywalfox
FOUND_FF_PROFILES=0
touch "$HOME/.cache/material-you-firefox.css"
if [ -d "$HOME/.mozilla/firefox" ]; then
    for prof in "$HOME/.mozilla/firefox"/*; do
        [ -d "$prof" ] || continue
        if [ -f "$prof/prefs.js" ] || [ -f "$prof/user.js" ]; then
            FOUND_FF_PROFILES=$((FOUND_FF_PROFILES + 1))
            mkdir -p "$prof/chrome" "$prof/extensions"
            cp "$CONFIG_SOURCE/firefox/userChrome.css" "$prof/chrome/userChrome.css"
            ln -sf "$HOME/.cache/material-you-firefox.css" "$prof/chrome/material-you.css"
            if [ -f "$CONFIG_SOURCE/firefox/extensions/pywalfox@frewacom.org.xpi" ]; then
                cp "$CONFIG_SOURCE/firefox/extensions/pywalfox@frewacom.org.xpi" "$prof/extensions/"
            fi
            if ! grep -q "toolkit.legacyUserProfileCustomizations.stylesheets" "$prof/user.js" 2>/dev/null; then
                echo 'user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);' >> "$prof/user.js"
            fi
        fi
    done
fi
PYWALFOX_BIN="$(command -v pywalfox || echo "$HOME/.local/share/pywalfox-venv/bin/pywalfox")"
if [ "$FOUND_FF_PROFILES" -gt 0 ] && [ ! -x "$PYWALFOX_BIN" ]; then
    python3 -m venv "$HOME/.local/share/pywalfox-venv" 2>/dev/null \
        && "$HOME/.local/share/pywalfox-venv/bin/pip" install --quiet pywalfox 2>/dev/null || true
fi
if [ -x "$PYWALFOX_BIN" ]; then
    mkdir -p "$HOME/.mozilla/native-messaging-hosts"
    cat > "$HOME/.mozilla/native-messaging-hosts/pywalfox.json" <<EOF
{
  "name": "pywalfox",
  "description": "Automatically theme your browser using the colors generated by Pywal",
  "path": "$PYWALFOX_BIN",
  "type": "stdio",
  "allowed_extensions": [ "pywalfox@frewacom.org" ]
}
EOF
fi
if [ "$FOUND_FF_PROFILES" -gt 0 ]; then
    print_success "Firefox: $FOUND_FF_PROFILES perfil(es) con userChrome.css y Pywalfox."
elif command -v firefox >/dev/null 2>&1 || command -v firefox-bin >/dev/null 2>&1; then
    print_info "Firefox no tiene perfil todavía: ábrelo una vez y repite ./install.sh para tematizarlo."
fi

if [ -x "$SCRIPTS_SOURCE/cursor-manager.py" ]; then
    "$SCRIPTS_SOURCE/cursor-manager.py" apply Bibata-Modern-Classic 24 >/dev/null 2>&1 || true
fi

# ==============================================================================
# 8. Paleta inicial
# ==============================================================================
CURRENT_WALL="$(cat "$HOME/.cache/current_wallpaper" 2>/dev/null || true)"
if [ -n "$CURRENT_WALL" ] && [ -f "$CURRENT_WALL" ]; then
    print_step "8. Generando la paleta de la skin activa..."
    "$TARGET_CONFIG/hypr/scripts/set-wallpaper.sh" "$CURRENT_WALL" >/dev/null 2>&1 || true
    print_success "Colores generados para el escritorio y las apps."
fi

# Stremio es opcional: prepara el Flatpak instalado sin reiniciarlo
python3 "$SCRIPTS_SOURCE/stremio-theme.py" --setup-only 2>/dev/null ||
    print_warn "No se pudo preparar el tema de Stremio. Se reintentará al cambiar de skin."

# ==============================================================================
# 9. Inicio de sesión estilo Omarchy (SDDM) con los colores de la skin
# ==============================================================================
# SDDM con su tema dentro de un Hyprland mínimo, como el instalador de Omarchy. Plymouth (pantalla
# de arranque) no se activa solo: toca el initramfs y el grub.cfg.
BOOT_SCRIPT="$SCRIPTS_SOURCE/install-boot-theme.sh"
if [ "$LOGIN_SETUP" != "no" ] && command -v sddm >/dev/null 2>&1 && [ -x "$BOOT_SCRIPT" ]; then
    if [ "$LOGIN_SETUP" = "ask" ] && [ -t 0 ]; then
        echo ""
        read -r -p "¿Usar la pantalla de inicio de sesión estilo Omarchy (SDDM)? Pide sudo. [S/n] " reply
        case "$reply" in [nN]*) LOGIN_SETUP="no" ;; *) LOGIN_SETUP="yes" ;; esac
    fi
    if [ "$LOGIN_SETUP" = "yes" ]; then
        print_step "9. Inicio de sesión (SDDM estilo Omarchy)..."
        python3 "$SCRIPTS_SOURCE/bwm_boot.py" render >/dev/null 2>&1 || true
        if sudo "$BOOT_SCRIPT" --all; then
            print_success "SDDM listo: se verá en el próximo arranque y seguirá los colores de la skin."
        else
            print_warn "No se pudo configurar SDDM. Repítelo con: sudo $BOOT_SCRIPT --all"
        fi
    fi
elif [ "$LOGIN_SETUP" = "yes" ]; then
    print_warn "SDDM no está instalado: instálalo y ejecuta sudo $BOOT_SCRIPT --all"
fi

# ==============================================================================
# 10. Plugin de uso de IA de la barra Retro (ai-usagebar, se compila con cargo)
# ==============================================================================
PLUGIN_SCRIPT="$SCRIPTS_SOURCE/bwm-plugin.sh"
if [ "$PLUGINS_SETUP" != "no" ] && ! command -v ai-usagebar >/dev/null 2>&1; then
    if command -v cargo >/dev/null 2>&1; then
        print_step "10. Compilando ai-usagebar (plugin de uso de IA de Retro)..."
        "$PLUGIN_SCRIPT" build >/dev/null 2>&1 \
            && print_success "ai-usagebar instalado en ~/.local/bin." \
            || print_warn "No se pudo compilar ai-usagebar; repítelo con: $PLUGIN_SCRIPT build"
    else
        print_info "Sin cargo no se compila ai-usagebar (opcional). Instala Rust y ejecuta: $PLUGIN_SCRIPT build"
    fi
fi

if [ -d "$BACKUP_DIR" ]; then
    echo ""
    print_warn "Tus configuraciones anteriores están en: $BACKUP_DIR"
fi

# ==============================================================================
# Resumen
# ==============================================================================
echo ""
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD} BWM instalado. ¡Gracias!${NC}"
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════════════════════${NC}"
python3 "$REQUIREMENTS" skins "${SKIN_ARGS[@]}" || true
cat <<EOF

Siguientes pasos:
  • Inicia sesión en Hyprland (o, si ya estás dentro: hyprctl reload).
  • Al entrar se abre la bienvenida: skins instaladas, sus requisitos y la wiki para añadir más.
    Ábrela cuando quieras con:  bwm
  • Alt+T cambia de skin · Alt+R temas de Retro · Alt+W fondo · Super+I ajustes
  • bwm check vuelve a comprobar los requisitos.
EOF
