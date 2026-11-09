#!/usr/bin/env bash
# ==============================================================================
# Script: install-owe.sh
# Descripción: compila OWE (omacom/owe, MIT), el motor de fondos de vídeo de Omarchy 4.5: el
# demonio `owed` vigila ~/.local/state/omarchy/current/background y, cuando apunta a un vídeo,
# `owe-render` lo reproduce (libmpv, decodificación por hardware) en una capa de fondo por
# monitor y suspende el fondo del shell (`omarchy-shell background setSuspended`). Omarchy lo
# instala como paquete de Arch; aquí se compila con meson desde un commit fijo, sin sudo.
# Uso: install-owe.sh [--force]   (--force: recompilar aunque ya esté)
# Lo arranca bwm-video-wallpaper sólo en Retro (las otras skins usan mpvpaper, como end-4).
# ==============================================================================
set -euo pipefail

GIT="https://github.com/omacom/owe"
REV="56e7659fb46fbd48ec3e1c8b187d0186d97da866"   # OWE 0.2.13, 2026-10-30
DATA="${XDG_DATA_HOME:-$HOME/.local/share}/bwm"
ROOT="$DATA/owe"
SRC="$DATA/owe-src"
BIN="$ROOT/bin/owed"
export GIT_TERMINAL_PROMPT=0

if [[ -x $BIN && ${1:-} != "--force" ]]; then
  echo "OWE ya está en $ROOT/bin"
  exit 0
fi

missing=()
for command in git meson ninja gcc pkg-config ffmpeg; do
  command -v "$command" >/dev/null 2>&1 || missing+=("$command")
done
if ((${#missing[@]})); then
  echo "Faltan: ${missing[*]}" >&2
  exit 1
fi
if ! pkg-config --print-errors --exists wayland-client wayland-egl egl glesv2 gl epoxy \
    'mpv >= 0.35' libavformat libavcodec libavutil libswscale libsystemd; then
  echo "Faltan bibliotecas (Gentoo: media-video/mpv[libmpv], dev-libs/libepoxy, media-video/ffmpeg)" >&2
  exit 1
fi

if [[ -d $SRC/.git ]]; then
  git -C "$SRC" fetch --quiet origin "$REV" 2>/dev/null || git -C "$SRC" fetch --quiet origin
else
  rm -rf "$SRC"
  git clone --quiet "$GIT" "$SRC"
fi
git -C "$SRC" -c advice.detachedHead=false checkout --quiet "$REV"

echo "Compilando OWE ${REV:0:8} con meson..."
meson setup --reconfigure -Dbuildtype=release "$SRC/build" "$SRC" >/dev/null 2>&1 || \
  meson setup -Dbuildtype=release "$SRC/build" "$SRC"
ninja -C "$SRC/build"

# Instalación atómica: owed puede estar en marcha con los binarios anteriores
install_binary() {
  install -Dm755 "$1" "$ROOT/bin/$2.new.$$"
  mv -f "$ROOT/bin/$2.new.$$" "$ROOT/bin/$2"
}
install_binary "$SRC/build/src/cli/owe" owe
install_binary "$SRC/build/src/daemon/owed" owed
install_binary "$SRC/build/src/render/owe-render" owe-render
install -Dm644 "$SRC/config/config.toml" "$ROOT/share/config.toml.example"
echo "Instalado en $ROOT/bin (owed busca owe-render en su misma carpeta)"
