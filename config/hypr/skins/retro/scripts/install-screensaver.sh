#!/usr/bin/env bash
# ==============================================================================
# Script: install-screensaver.sh
# Descripción: compila el salvapantallas nativo de Omarchy 4.5 (omacom/omarchy-screensaver,
# MIT, Copyright (c) 2026 Tobias Lütke): una capa Wayland por monitor con efectos ttfx, que
# se cierra con cualquier tecla, clic, rueda o movimiento del ratón. Omarchy lo instala como
# paquete de Arch; aquí se compila con cargo desde un commit fijo, sin sudo.
# Uso: install-screensaver.sh [--force]   (--force: recompilar aunque ya esté)
# Lo usa launch-screensaver.sh; sin él, el salvapantallas de terminal de antes.
# ==============================================================================
set -euo pipefail

GIT="https://github.com/omacom/omarchy-screensaver"
REV="b3026b63999908bf424eae62194aa95df5e4d24c"   # v1.3.1 + block-elements, 2026-10-28
ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/bwm/omarchy-screensaver"
BIN="$ROOT/bin/omarchy-launch-screensaver"
export GIT_TERMINAL_PROMPT=0

if [[ -x $BIN && ${1:-} != "--force" ]]; then
  echo "El salvapantallas nativo ya está en $BIN"
  exit 0
fi
command -v cargo >/dev/null || { echo "Falta cargo (Rust): sudo emerge --ask dev-lang/rust-bin" >&2; exit 1; }
command -v pkg-config >/dev/null || { echo "Falta pkg-config" >&2; exit 1; }

echo "Compilando omarchy-screensaver ${REV:0:8} con cargo (menos de un minuto)..."
cargo install --locked --force --root "$ROOT" --git "$GIT" --rev "$REV" omarchy-launch-screensaver
echo "Instalado en $BIN"
