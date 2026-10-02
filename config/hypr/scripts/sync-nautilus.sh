#!/usr/bin/env bash
# ==============================================================================
# Script: sync-nautilus.sh
# Descripción: Sincroniza la paleta Material You con GNOME / Nautilus:
#              1. Actualiza el acento del sistema en GNOME (accent-color)
#              2. Si Nautilus está abierto, lo recarga de forma transparente
#                 para aplicar la nueva paleta de gtk.css sin intervención.
# ==============================================================================

set -euo pipefail

# 1. Calcular el color de acento más cercano para GNOME 47+ (Libadwaita)
WAL_COLORS="$HOME/.cache/wal/colors.json"

if [ -f "$WAL_COLORS" ]; then
    ACCENT=$(python3 -c "
import colorsys, json

gnome_accents = {
    'blue': (53, 132, 228),
    'teal': (33, 144, 164),
    'green': (58, 148, 74),
    'yellow': (200, 136, 0),
    'orange': (237, 91, 0),
    'red': (224, 27, 36),
    'pink': (213, 97, 153),
    'purple': (145, 65, 172),
    'slate': (98, 106, 118)
}

def hex_to_rgb(hex_str):
    h = hex_str.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hsl(rgb):
    r, g, b = [x/255.0 for x in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return (h * 360, s, l)

try:
    with open('$WAL_COLORS') as f:
        data = json.load(f)
    prim_hex = data.get('colors', {}).get('color4', '#a8c8ff')
    target_rgb = hex_to_rgb(prim_hex)
    target_h, target_s, target_l = rgb_to_hsl(target_rgb)
    if target_s < 0.15:
        closest = 'slate'
    else:
        def dist(name):
            rgb = gnome_accents[name]
            h, s, l = rgb_to_hsl(rgb)
            return min(abs(target_h - h), 360 - abs(target_h - h))
        closest = min(gnome_accents.keys(), key=dist)
    print(closest)
except Exception:
    print('blue')
" 2>/dev/null || echo "blue")

    gsettings set org.gnome.desktop.interface accent-color "$ACCENT" 2>/dev/null || true
    gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark' 2>/dev/null || true
fi

# 2. Si Nautilus está en ejecución con una ventana abierta, recargar de forma transparente
if pgrep -x "nautilus" > /dev/null 2>&1; then
    nautilus -q > /dev/null 2>&1 || true
    sleep 0.12
    hyprctl dispatch 'hl.dsp.exec_cmd("nautilus")' > /dev/null 2>&1 || true
fi
