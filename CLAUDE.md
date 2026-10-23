# BWM (Better Window Manager)

Contexto maestro del proyecto (arquitectura, historial, estado de Git y puntos críticos):

@BWM_CONTEXT.md

## Notas para Claude Code
- Responder en español.
- El repo vive en `/mnt/HDD1TB/Projects/hyprland-de` (symlink `~/Projects/hyprland-de`); el usuario ejecuta desde `~/.config/`, así que los cambios deben reflejarse en ambos sitios.
- Plugins C++ de Hyprland: compilar siempre con `-fno-gnu-unique`.
- Desplegar plugins SOLO con `make install` (tmp + mv atómico). Nunca `cp` sobre un `.so` cargado ni `hyprctl plugin unload/load` en caliente: crashea Hyprland (SIGBUS → safe mode).
- Nunca arrancar Quickshell dos veces; usar `bwm-theme-manager.py` para reinicios.
- Push: `git push origin main` (sube a GitLab y GitHub).
- Si se cambia algo relevante (nuevas features, commits importantes), actualizar `BWM_CONTEXT.md`.
