#!/usr/bin/env bash
# ==============================================================================
# bwm-require.sh <command> <package> [<command> <package>...] -- <action...>
# Runs the action if every command exists; otherwise says which package to install
# (Gentoo atom; also shown for other distros' usual names) instead of failing silently.
# Used by the Retro menu (hypr/omarchy/bwm-menu.jsonc) for tools that are optional.
# ==============================================================================
missing=()
while (($#)) && [[ $1 != -- ]]; do
  cmd=$1 pkg=${2:-$1}
  shift 2 || shift $#
  # "a|b" = any of them
  found=false
  IFS='|' read -ra alts <<<"$cmd"
  for c in "${alts[@]}"; do command -v "$c" >/dev/null 2>&1 && found=true && break; done
  $found || missing+=("$pkg")
done
[[ ${1:-} == -- ]] && shift

if ((${#missing[@]})); then
  notify-send -a BWM -u normal "Falta: ${missing[*]}" "Instálalo con: sudo emerge --ask ${missing[*]}"
  exit 1
fi
exec "$@"
