#!/usr/bin/env bash
# ==============================================================================
# Script: bwm-plugin.sh
# Descripción: Plugins de la barra de Omarchy en el tema Retro de BWM. Equivalente a
# `omarchy plugin add/remove/update/list/enable/disable` (Omarchy, MIT): un plugin es un
# repositorio git con un manifest.json en la raíz (https://omarchy.org/manual/shell-plugins/).
# La barra Retro los carga con las librerías qs.Commons / qs.Ui de Omarchy
# (quickshell/ii/Commons, quickshell/ii/Ui) y modules/ii/bar/omarchy/.
#
# Uso:
#   bwm-plugin.sh add <url-git> [--section left|center|right] [--disabled] [--yes]
#   bwm-plugin.sh remove <id>        bwm-plugin.sh update [id]
#   bwm-plugin.sh enable <id> [--section S]   bwm-plugin.sh disable <id>
#   bwm-plugin.sh list               bwm-plugin.sh catalog   (JSON para la barra)
#   bwm-plugin.sh defaults           # instala los plugins por defecto de BWM
#
# Como en Omarchy, un plugin es código sin aislar que corre dentro de Quickshell: revisa
# lo que instalas. No se ejecutan hooks de instalación ni se pide sudo.
# ==============================================================================
set -euo pipefail

PLUGINS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/bwm/omarchy-plugins"
LAYOUT="${XDG_CONFIG_HOME:-$HOME/.config}/bwm/omarchy-plugins.json"
export GIT_TERMINAL_PROMPT=0

# Plugins por defecto: los más usados de Omarchy (estrellas en GitHub, 2026-10) que tienen
# sentido aquí y no necesitan cuentas: uso de IA (Claude...), monitor del sistema,
# multimedia con carátula y ventana activa con icono.
DEFAULT_PLUGINS=(
  "https://github.com/akitaonrails/ai-usagebar.git right"
  "https://github.com/crmne/omastats.git right"
  "https://github.com/crmne/omarchy-mpris.git center"
  "https://github.com/crmne/omarchy-active-window.git left"
)

fail() { echo "bwm-plugin: $*" >&2; exit 1; }
need() { command -v "$1" >/dev/null || fail "falta $1"; }
need jq
need git

mkdir -p "$PLUGINS_DIR" "${LAYOUT%/*}"
[[ -s $LAYOUT ]] || echo '{"bar": []}' >"$LAYOUT"

save_layout() {   # stdin: nuevo JSON
  local tmp
  tmp=$(mktemp "${LAYOUT}.XXXXXX")
  jq '.' >"$tmp" && mv -f "$tmp" "$LAYOUT"
  # La barra vigila el archivo; esto sólo acelera la recarga si Quickshell corre
  qs -c ii ipc call omarchyPlugins reload >/dev/null 2>&1 || true
}

plugin_dir() {    # id -> carpeta
  local id=$1 d
  for d in "$PLUGINS_DIR"/*/; do
    [[ -f $d/manifest.json ]] || continue
    [[ $(jq -r '.id // ""' "$d/manifest.json") == "$id" ]] && { echo "${d%/}"; return 0; }
  done
  return 1
}

# Secciones de Omarchy (left, centerBegin, center, centerEnd, tray, right) -> las de BWM
section_for() {
  case "$1" in
    left) echo left ;;
    center|centerBegin|centerEnd) echo center ;;
    *) echo right ;;
  esac
}

enable_plugin() { # id [section]
  local id=$1 section=${2:-} dir manifest
  dir=$(plugin_dir "$id") || fail "no está instalado: $id"
  manifest="$dir/manifest.json"
  if ! jq -e '(.kinds // []) | index("bar-widget")' "$manifest" >/dev/null; then
    echo "$id no es un widget de barra; sus servicios se cargan igualmente."
  fi
  [[ -n $section ]] || section=$(section_for "$(jq -r '.barWidget.defaultSection // "right"' "$manifest")")
  jq --arg id "$id" --arg s "$section" --argjson d "$(jq '.barWidget.defaults // {}' "$manifest")" '
    .bar |= ((map(select(.id != $id))) + [{id: $id, section: $s, settings: $d}])
    | .disabled = ((.disabled // []) - [$id])' "$LAYOUT" | save_layout
  echo "Activado $id en la sección $section."
}

cmd_add() {
  local url="" section="" enable=true yes=false name dest id
  while (($#)); do
    case "$1" in
      --section) section=$(section_for "${2:?}"); shift ;;
      --disabled) enable=false ;;
      --yes) yes=true ;;
      -*) fail "opción desconocida: $1" ;;
      *) url=$1 ;;
    esac
    shift
  done
  [[ $url =~ ^(https://|git@)[A-Za-z0-9._/:@-]+$ ]] || fail "URL git no válida: $url"
  name=$(basename "${url%.git}")
  [[ $name =~ ^[A-Za-z0-9._-]+$ && $name != .* ]] || fail "nombre de repositorio no válido: $name"
  dest="$PLUGINS_DIR/$name"
  if [[ -d $dest ]]; then
    echo "Ya estaba instalado: $dest"
  else
    if ! $yes && [[ -t 0 ]]; then
      read -r -p "Los plugins son código sin aislar dentro de la barra. ¿Instalar $url? [s/N] " reply
      [[ $reply == [sSyY]* ]] || exit 1
    fi
    git clone -q --depth 1 "$url" "$dest"
  fi
  [[ -f $dest/manifest.json ]] || { rm -rf "$dest"; fail "$url no tiene manifest.json en la raíz"; }
  id=$(jq -r '.id // ""' "$dest/manifest.json")
  [[ $id =~ ^[A-Za-z0-9._-]+$ && $id != omarchy.* ]] || { rm -rf "$dest"; fail "id de plugin no válido: $id"; }
  echo "Instalado $id ($(jq -r '.name // ""' "$dest/manifest.json")) en $dest"
  if $enable; then enable_plugin "$id" "$section"; fi
}

cmd_remove() {
  local id=${1:?id} dir
  dir=$(plugin_dir "$id") || fail "no está instalado: $id"
  jq --arg id "$id" '.bar |= map(select(.id != $id)) | .disabled = ((.disabled // []) - [$id])' "$LAYOUT" | save_layout
  rm -rf -- "$dir"
  echo "Eliminado $id."
}

cmd_update() {
  local d
  for d in "$PLUGINS_DIR"/*/; do
    [[ -d $d/.git ]] || continue
    if [[ -n ${1:-} && $(jq -r '.id // ""' "$d/manifest.json" 2>/dev/null) != "$1" ]]; then continue; fi
    echo "Actualizando $(basename "$d")..."
    git -C "$d" pull -q --ff-only || echo "  no se pudo actualizar (¿cambios locales?)" >&2
  done
  qs -c ii ipc call omarchyPlugins reload >/dev/null 2>&1 || true
}

cmd_disable() {
  local id=${1:?id}
  jq --arg id "$id" '.bar |= map(select(.id != $id)) | .disabled = (((.disabled // []) - [$id]) + [$id])' "$LAYOUT" | save_layout
  echo "Desactivado $id."
}

cmd_list() {
  local d id
  for d in "$PLUGINS_DIR"/*/; do
    [[ -f $d/manifest.json ]] || continue
    id=$(jq -r '.id' "$d/manifest.json")
    printf '%-32s %-8s %s\n' "$id" \
      "$(jq -r --arg id "$id" '(.bar[] | select(.id == $id) | .section) // (if ((.disabled // []) | index($id)) then "off" else "-" end)' "$LAYOUT")" \
      "$(jq -r '.name // ""' "$d/manifest.json")"
  done
}

# JSON para modules/ii/bar/omarchy/OmarchyPlugins.qml: plugins instalados y activos
cmd_catalog() {
  local d first=true
  printf '{"layout": %s, "plugins": [' "$(jq -c '.' "$LAYOUT")"
  for d in "$PLUGINS_DIR"/*/; do
    [[ -f $d/manifest.json ]] || continue
    $first || printf ','
    first=false
    jq -c --arg dir "${d%/}" '{
      id, name, version, kinds: (.kinds // []), dir: $dir,
      keepLoaded: (.keepLoaded // false),
      barWidget: (if .entryPoints.barWidget then ($dir + "/" + .entryPoints.barWidget) else null end),
      service: (if .entryPoints.service then ($dir + "/" + .entryPoints.service) else null end),
      defaults: (.barWidget.defaults // {})
    }' "$d/manifest.json"
  done
  printf ']}\n'
}

cmd_defaults() {
  local entry
  for entry in "${DEFAULT_PLUGINS[@]}"; do
    # shellcheck disable=SC2086 # url y sección
    set -- $entry
    cmd_add "$1" --section "$2" --yes || echo "  (falló $1)" >&2
  done
  # ai-usagebar es sólo la interfaz: el binario se compila con cargo si no está
  if ! command -v ai-usagebar >/dev/null && command -v cargo >/dev/null && [[ -d $PLUGINS_DIR/ai-usagebar ]]; then
    echo "Compilando ai-usagebar (cargo, unos minutos)..."
    cargo install --locked --root "$HOME/.local" --path "$PLUGINS_DIR/ai-usagebar" \
      --bin ai-usagebar --bin ai-usagebar-tui >/dev/null 2>&1 \
      && echo "ai-usagebar instalado en ~/.local/bin" \
      || echo "No se pudo compilar ai-usagebar; el widget mostrará que falta el programa." >&2
  fi
}

case "${1:-}" in
  add) shift; cmd_add "$@" ;;
  remove|rm) shift; cmd_remove "$@" ;;
  update) shift; cmd_update "$@" ;;
  enable) shift; id=${1:?id}; shift; s=""; [[ ${1:-} == --section ]] && s=$(section_for "${2:?}"); enable_plugin "$id" "$s" ;;
  disable) shift; cmd_disable "$@" ;;
  list|ls) cmd_list ;;
  catalog) cmd_catalog ;;
  defaults) cmd_defaults ;;
  *) sed -n '9,16p' "$0" | sed 's/^# \{0,1\}//'; exit 1 ;;
esac
