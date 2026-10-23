#!/usr/bin/env bash
# ==============================================================================
# Script: steam-theme.sh
# Descripción: Aplica a Steam los colores del tema BWM con Adwaita-for-Steam
# (https://github.com/tkashkin/Adwaita-for-Steam), como el módulo de Steam de
# omarchy-theme-hook. No hace nada si Adwaita-for-Steam no está en
# ~/.local/share/steam-adwaita. Steam aplica el cambio la próxima vez que se abra.
# ==============================================================================

ADW="$HOME/.local/share/steam-adwaita"
CSS="$HOME/.local/state/bwm/steam/bwm.css"
[[ -f $ADW/install.py && -f $CSS ]] || exit 0

# Las --adw-*-rgb de Adwaita-for-Steam son tripletes "r, g, b": convertir los #rrggbb
mkdir -p "$ADW/adwaita/colorthemes/bwm"
python3 - "$CSS" "$ADW/adwaita/colorthemes/bwm/bwm.css" <<'PY'
import re, sys
text = open(sys.argv[1]).read()
text = re.sub(r"#([0-9a-fA-F]{6})", lambda m: ", ".join(str(int(m.group(1)[i:i + 2], 16)) for i in (0, 2, 4)), text)
open(sys.argv[2], "w").write(text)
PY

cd "$ADW" && python3 install.py --color-theme bwm >/dev/null 2>&1

if pgrep -x steam >/dev/null; then
  notify-send -a "BWM" "Steam" "El tema de Steam se aplicará al reiniciarlo." 2>/dev/null
fi
