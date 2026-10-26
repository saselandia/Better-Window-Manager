#!/usr/bin/env bash
# ==============================================================================
# Script: bwm-plugin.sh
# Descripción: Plugins de la barra de Omarchy en el estilo Retro de BWM. Equivalente a
# `omarchy plugin add/remove/update/list/enable/disable` (Omarchy, MIT): un plugin es un
# repositorio git con un manifest.json en la raíz (https://omarchy.org/manual/shell-plugins/).
# La barra Retro los carga con las librerías qs.Commons / qs.Ui de Omarchy
# (quickshell/ii/Commons, quickshell/ii/Ui) y modules/ii/bar/omarchy/.
#
# Uso:
#   bwm-plugin.sh add <url-git> [--section left|center|centerEnd|right] [--disabled] [--yes]
#   bwm-plugin.sh remove <id>        bwm-plugin.sh update [id]
#   bwm-plugin.sh enable <id> [--section S]   bwm-plugin.sh disable <id>
#   bwm-plugin.sh list               bwm-plugin.sh catalog   (JSON para la barra)
#   bwm-plugin.sh build              # compila el binario de ai-usagebar (cargo)
#
# Preinstalados (quickshell/ii/omarchy-plugins, activos salvo que se desactiven en Ajustes →
# Barra): los plugins más usados de Omarchy que no necesitan cuentas: ai-usagebar, omastats,
# omarchy-mpris y omarchy-active-window. El reloj con calendario de Omarchy no es un plugin:
# forma parte de la barra Retro (quickshell/ii/modules/ii/bar/omarchy/clock).
#
# Como en Omarchy, un plugin es código sin aislar que corre dentro de Quickshell: revisa
# lo que instalas. No se ejecutan hooks de instalación ni se pide sudo.
# ==============================================================================
set -euo pipefail

PLUGINS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/bwm/omarchy-plugins"
BUILTIN_DIR="${BWM_BUILTIN_PLUGINS:-$HOME/.config/quickshell/ii/omarchy-plugins}"
# ai-usagebar: el plugin preinstalado es sólo la interfaz; su binario sale de este commit
AI_USAGEBAR_GIT="https://github.com/akitaonrails/ai-usagebar.git"
AI_USAGEBAR_REV="d1af986fe4bf8d05316bc8d6e1506881b5f4d265"
LAYOUT="${BWM_OMARCHY_LAYOUT:-${XDG_CONFIG_HOME:-$HOME/.config}/bwm/omarchy-plugins.json}"
export GIT_TERMINAL_PROMPT=0

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

plugin_dir() {    # id -> carpeta (instalados por el usuario o preinstalados)
  local id=$1 d
  for d in "$PLUGINS_DIR"/*/ "$BUILTIN_DIR"/*/; do
    [[ -f $d/manifest.json ]] || continue
    [[ $(jq -r '.id // ""' "$d/manifest.json") == "$id" ]] && { echo "${d%/}"; return 0; }
  done
  return 1
}

# Secciones de Omarchy (left, centerBegin, center, centerEnd, tray, right) -> las de BWM
section_for() {
  case "$1" in
    left) echo left ;;
    center|centerBegin) echo center ;;
    centerEnd|after-clock) echo centerEnd ;;
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
  if [[ -z $section ]]; then
    # Como en el shell.json de Omarchy: Elsewhen y el tiempo justo después del reloj
    if [[ $id == omarchy.elsewhen || $id == omarchy.weather ]]; then section=centerEnd
    elif [[ $id == crmne.mpris ]]; then section=center   # a la izquierda del reloj: a la derecha no cabe junto a omastats
    else section=$(section_for "$(jq -r '.barWidget.defaultSection // "right"' "$manifest")"); fi
  fi
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
  [[ $dir == "$BUILTIN_DIR"/* ]] && fail "$id viene preinstalado: desactívalo (bwm-plugin.sh disable $id)"
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
  for d in "$BUILTIN_DIR"/*/ "$PLUGINS_DIR"/*/; do
    [[ -f $d/manifest.json ]] || continue
    id=$(jq -r '.id' "$d/manifest.json")
    printf '%-32s %-8s %s\n' "$id" \
      "$(jq -r --arg id "$id" --argjson b "$([[ $d == "$BUILTIN_DIR"/* ]] && echo true || echo false)" '(.bar[] | select(.id == $id) | .section) // (if ((.disabled // []) | index($id)) then "off" elif $b then "default" else "-" end)' "$LAYOUT")" \
      "$(jq -r '.name // ""' "$d/manifest.json")"
  done
}

# JSON para modules/ii/bar/omarchy/OmarchyPlugins.qml: plugins instalados y activos
# Las órdenes omarchy-* que los plugins lanzan por su cuenta (sin bar.run) tienen que estar en el
# PATH de Quickshell: enlaces en ~/.local/bin a hypr/scripts/omarchy-shims, sin pisar nada propio
link_shims() {
  local shim_dir="$HOME/.config/hypr/scripts/omarchy-shims" bin="$HOME/.local/bin" f name
  [[ -d $shim_dir ]] || return 0
  mkdir -p "$bin"
  for f in "$shim_dir"/omarchy-*; do
    name=${f##*/}
    if [[ ! -e $bin/$name || ( -L $bin/$name && $(readlink "$bin/$name") == "$f" ) ]]; then
      ln -sfn "$f" "$bin/$name"
    fi
  done
}

cmd_catalog() {
  link_shims
  local d first=true builtin
  printf '{"layout": %s, "plugins": [' "$(jq -c '.' "$LAYOUT")"
  for d in "$BUILTIN_DIR"/*/ "$PLUGINS_DIR"/*/; do
    [[ -f $d/manifest.json ]] || continue
    $first || printf ','
    first=false
    builtin=false; [[ $d == "$BUILTIN_DIR"/* ]] && builtin=true
    jq -c --arg dir "${d%/}" --argjson builtin "$builtin" '{
      builtin: $builtin,
      defaultSection: (if (.id == "omarchy.elsewhen" or .id == "omarchy.weather") then "centerEnd" elif .id == "crmne.mpris" then "center" else (.barWidget.defaultSection // "right" | if . == "left" then "left" elif (. == "center" or . == "centerBegin") then "center" elif . == "centerEnd" then "centerEnd" else "right" end) end),
      description: (.description // ""),
      id, name, version, kinds: (.kinds // []), dir: $dir,
      keepLoaded: (.keepLoaded // false),
      barWidget: (if .entryPoints.barWidget then ($dir + "/" + .entryPoints.barWidget) else null end),
      service: (if .entryPoints.service then ($dir + "/" + .entryPoints.service) else null end),
      defaults: (.barWidget.defaults // {})
    }' "$d/manifest.json"
  done
  printf ']}\n'
}

# Binario de ai-usagebar (el plugin preinstalado es sólo su interfaz) en ~/.local/bin
cmd_build() {
  command -v ai-usagebar >/dev/null && { echo "ai-usagebar ya está instalado."; return 0; }
  need cargo
  echo "Compilando ai-usagebar ${AI_USAGEBAR_REV:0:8} con cargo (unos minutos)..."
  cargo install --locked --root "$HOME/.local" --git "$AI_USAGEBAR_GIT" --rev "$AI_USAGEBAR_REV" \
    --bin ai-usagebar --bin ai-usagebar-tui
  echo "ai-usagebar instalado en ~/.local/bin"
}

case "${1:-}" in
  add) shift; cmd_add "$@" ;;
  remove|rm) shift; cmd_remove "$@" ;;
  update) shift; cmd_update "$@" ;;
  enable) shift; id=${1:?id}; shift; s=""; [[ ${1:-} == --section ]] && s=$(section_for "${2:?}"); enable_plugin "$id" "$s" ;;
  disable) shift; cmd_disable "$@" ;;
  # Widgets fijos de la barra Retro (omarchy.tray, omarchy.audio…): sólo la lista `disabled`
  # (`shown` turns on the ones that are off by default, such as omarchy.media)
  hide) shift; jq --arg id "${1:?id}" '.disabled = (((.disabled // []) - [$id]) + [$id]) | .shown = ((.shown // []) - [$id])' "$LAYOUT" | save_layout ;;
  show) shift; jq --arg id "${1:?id}" '.disabled = ((.disabled // []) - [$id]) | .shown = (((.shown // []) - [$id]) + [$id])' "$LAYOUT" | save_layout ;;
  list|ls) cmd_list ;;
  catalog) cmd_catalog ;;
  build) cmd_build ;;
  defaults) cmd_build ;;   # nombre anterior: los plugins ya vienen preinstalados
  *) sed -n '9,16p' "$0" | sed 's/^# \{0,1\}//'; exit 1 ;;
esac
