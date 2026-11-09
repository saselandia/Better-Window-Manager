#!/usr/bin/env bash
# ==============================================================================
# Script: bwm-plugin.sh
# Descripción: plugins de la barra de Omarchy en el estilo Retro de BWM. La barra es la de Omarchy
# (quickshell/ii/omarchyShell, BWM_CONTEXT §3.118) y se configura como en Omarchy: en
# ~/.config/omarchy/shell.json, con `omarchy plugin add/remove/update/enable/disable`
# (omarchy-plugin-*, en hypr/scripts/omarchy-shims). Este script mantiene las órdenes que usan
# Ajustes → Barra, Ajustes → Plugins y el menú de Retro, y las pasa a esas de Omarchy.
#
# Uso:
#   bwm-plugin.sh add <url-git> [--section left|center|centerEnd|right] [--disabled] [--yes]
#   bwm-plugin.sh remove <id>        bwm-plugin.sh update [id]
#   bwm-plugin.sh enable <id> [--section S]   bwm-plugin.sh disable <id>
#   bwm-plugin.sh hide <id> | show <id>       (lo mismo que disable / enable)
#   bwm-plugin.sh list               bwm-plugin.sh catalog   (JSON para Ajustes y el menú)
#   bwm-plugin.sh build              # compila el binario de ai-usagebar (cargo)
#
# Plugins de terceros: los del usuario en ~/.config/omarchy/plugins (donde los instala Omarchy) y
# los que trae BWM preinstalados en quickshell/ii/omarchy-plugins (ai-usagebar, omastats,
# omarchy-mpris, omarchy-active-window). Como en Omarchy, un plugin es código sin aislar que corre
# dentro de Quickshell: revisa lo que instalas. No se ejecutan hooks de instalación ni se pide sudo.
# ==============================================================================
set -euo pipefail

SHIMS="$HOME/.config/hypr/scripts/omarchy-shims"
USER_PLUGINS="${XDG_CONFIG_HOME:-$HOME/.config}/omarchy/plugins"
BUNDLED_PLUGINS="${BWM_BUILTIN_PLUGINS:-$HOME/.config/quickshell/ii/omarchy-plugins}"
FIRST_PARTY="$HOME/.config/quickshell/ii/omarchyShell/plugins"
SHELL_JSON="${XDG_CONFIG_HOME:-$HOME/.config}/omarchy/shell.json"
DEFAULT_SHELL_JSON="$HOME/.config/hypr/omarchy/config/omarchy/shell.json"
# ai-usagebar: el plugin preinstalado es sólo la interfaz; su binario sale de este commit
AI_USAGEBAR_GIT="https://github.com/akitaonrails/ai-usagebar.git"
AI_USAGEBAR_REV="d1af986fe4bf8d05316bc8d6e1506881b5f4d265"
export GIT_TERMINAL_PROMPT=0
export PATH="$SHIMS:$PATH"

fail() { echo "bwm-plugin: $*" >&2; exit 1; }
need() { command -v "$1" >/dev/null || fail "falta $1"; }
need jq

# BWM llamaba «center» a la izquierda del reloj, que en Omarchy es centerBegin
omarchy_section() {
  case "$1" in
    center|centerBegin) echo centerBegin ;;
    left|centerEnd|right|tray) echo "$1" ;;
    *) echo right ;;
  esac
}

# ¿Está la barra de Omarchy en marcha (Retro)? Sin ella, las órdenes de Omarchy no tienen a quién
# pedírselo y se edita shell.json directamente, como haría Omarchy sin su shell
shell_running() {
  [[ $(qs -c ii ipc call shell listShellConfig 2>/dev/null) == "{"* ]] &&
    [[ $(qs -c ii ipc call shell listShellConfig 2>/dev/null) != "{}" ]]
}

ensure_shell_json() {
  [[ -s $SHELL_JSON ]] && return 0
  python3 -c 'import sys; sys.path.insert(0, sys.argv[1]); import bwm_omarchy; bwm_omarchy.ensure_omarchy_shell_json()' \
    "$HOME/.config/hypr/scripts" || true
  [[ -s $SHELL_JSON ]] || { mkdir -p "${SHELL_JSON%/*}"; cp "$DEFAULT_SHELL_JSON" "$SHELL_JSON"; }
}

edit_shell_json() {   # jq filter, args...
  local filter=$1 tmp
  shift
  ensure_shell_json
  tmp=$(mktemp "$SHELL_JSON.XXXXXX")
  jq "$@" "$filter" "$SHELL_JSON" >"$tmp" && mv -f "$tmp" "$SHELL_JSON"
}

cmd_enable() {   # id [section]
  local id=$1 section=${2:-}
  if shell_running; then
    if [[ -n $section ]]; then omarchy-plugin-enable "$id" --section "$section"
    else omarchy-plugin-enable "$id"; fi
    return
  fi
  edit_shell_json '
    .bar.layout = (.bar.layout // {})
    | if any(.bar.layout[]?[]?; .id == $id) and $section == "" then .
      else .bar.layout |= with_entries(.value |= map(select(.id != $id)))
        | .bar.layout[($section | if . == "" then "right" else . end)] += [{id: $id}] end' \
    --arg id "$id" --arg section "$section"
  echo "Activado $id."
}

cmd_disable() {
  local id=${1:?id}
  if shell_running; then omarchy-plugin-disable "$id"; return; fi
  edit_shell_json '.bar.layout |= with_entries(.value |= map(select(.id != $id)))' --arg id "$id"
  echo "Desactivado $id."
}

cmd_add() {
  local url="" section="" enable=true args=()
  while (($#)); do
    case "$1" in
      --section) section=$(omarchy_section "${2:?}"); shift ;;
      --disabled) enable=false ;;
      --yes) args+=(--yes) ;;
      -*) fail "opción desconocida: $1" ;;
      *) url=$1 ;;
    esac
    shift
  done
  [[ -n $url ]] || fail "falta la URL git"
  local before after id
  before=$(ls "$USER_PLUGINS" 2>/dev/null || true)
  omarchy-plugin-add "$url" "${args[@]}"
  after=$(ls "$USER_PLUGINS" 2>/dev/null || true)
  id=$(comm -13 <(sort <<<"$before") <(sort <<<"$after") | head -n 1)
  [[ -n $id && -f $USER_PLUGINS/$id/manifest.json ]] || return 0
  id=$(jq -r '.id' "$USER_PLUGINS/$id/manifest.json")
  if $enable; then cmd_enable "$id" "$section"; fi
}

cmd_remove() {
  local id=${1:?id}
  [[ -d $BUNDLED_PLUGINS ]] && grep -qs "\"id\": *\"$id\"" "$BUNDLED_PLUGINS"/*/manifest.json &&
    fail "$id viene preinstalado: desactívalo (bwm-plugin.sh disable $id)"
  omarchy-plugin-remove "$id" --yes
}

# Las órdenes omarchy-* que los plugins lanzan por su cuenta tienen que estar en el PATH de
# Quickshell: enlaces en ~/.local/bin a hypr/scripts/omarchy-shims, sin pisar nada propio
link_shims() {
  local bin="$HOME/.local/bin" f name
  [[ -d $SHIMS ]] || return 0
  mkdir -p "$bin"
  for f in "$SHIMS"/omarchy-*; do
    name=${f##*/}
    if [[ ! -e $bin/$name || ( -L $bin/$name && $(readlink "$bin/$name") == "$f" ) ]]; then
      ln -sfn "$f" "$bin/$name"
    fi
  done
}

# JSON para Ajustes → Barra / Plugins y el menú de Retro, con la forma de antes:
# {"layout": {"bar": [{id, section, settings}], "disabled": [...], "shown": [...]}, "plugins": [...]},
# sacado de shell.json (lo que está en la barra) y de los manifest.json de los plugins
cmd_catalog() {
  link_shims
  ensure_shell_json
  python3 - "$SHELL_JSON" "$FIRST_PARTY" "$BUNDLED_PLUGINS" "$USER_PLUGINS" <<'PY'
import json, sys
from pathlib import Path

shell_json, first_party, bundled, user = sys.argv[1:5]
try:
    layout = json.loads(Path(shell_json).read_text()).get("bar", {}).get("layout", {})
except (OSError, ValueError, AttributeError):
    layout = {}
to_bwm = {"left": "left", "centerBegin": "center", "center": "center", "centerEnd": "centerEnd", "right": "right", "tray": "right"}
placed = []
for section in ("left", "centerBegin", "center", "centerEnd", "tray", "right"):
    for entry in layout.get(section) or []:
        if isinstance(entry, dict) and entry.get("id"):
            settings = {k: v for k, v in entry.items() if k != "id"}
            placed.append({"id": entry["id"], "section": to_bwm[section], "settings": settings})

def manifests():
    for root, builtin in ((first_party, True), (bundled, True), (user, False)):
        base = Path(root)
        if not base.is_dir():
            continue
        found = list(base.glob("*/manifest.json")) + list(base.glob("*/*/manifest.json")) + list(base.glob("*/*/*.manifest.json"))
        for path in sorted(found):
            try:
                data = json.loads(path.read_text())
            except (OSError, ValueError):
                continue
            if isinstance(data, dict) and data.get("id"):
                yield path, data, builtin

plugins, seen = [], set()
for path, data, builtin in manifests():
    pid = data["id"]
    if pid in seen or "bar-widget" not in (data.get("kinds") or []):
        continue
    seen.add(pid)
    entry = data.get("entryPoints") or {}
    folder = path.parent
    section = (data.get("barWidget") or {}).get("defaultSection", "right")
    plugins.append({
        "builtin": builtin,
        "defaultSection": to_bwm.get(section, "right"),
        "description": data.get("description", ""),
        "id": pid, "name": data.get("name", pid), "version": data.get("version", ""),
        "kinds": data.get("kinds") or [], "dir": str(folder),
        "keepLoaded": bool(data.get("keepLoaded")),
        "barWidget": str(folder / entry["barWidget"]) if entry.get("barWidget") else None,
        "service": str(folder / entry["service"]) if entry.get("service") else None,
        "defaults": (data.get("barWidget") or {}).get("defaults") or {},
    })
on_bar = [e["id"] for e in placed]
print(json.dumps({
    "layout": {"bar": placed, "disabled": [p["id"] for p in plugins if p["id"] not in on_bar], "shown": on_bar},
    "plugins": plugins,
}))
PY
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
  update) shift; omarchy-plugin-update "$@" ;;
  enable|show)
    shift; id=${1:?id}; shift; s=""
    [[ ${1:-} == --section ]] && s=$(omarchy_section "${2:?}")
    cmd_enable "$id" "$s" ;;
  disable|hide) shift; cmd_disable "$@" ;;
  list|ls) omarchy-plugin-list ;;
  catalog) cmd_catalog ;;
  build|defaults) cmd_build ;;
  *) sed -n '/^# Uso:/,/^# Plugins de terceros/p' "$0" | sed 's/^# \{0,1\}//' | head -n -1; exit 1 ;;
esac
