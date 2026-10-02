#!/usr/bin/env bash
# ==============================================================================
# Script: open-autostart.sh
# Descripción: Abre la sección de aplicaciones de inicio automático en Quickshell
# ==============================================================================

export SETTINGS_PAGE="Autostart"
exec qs -p "$HOME/.config/quickshell/ii/settings.qml" "$@"
