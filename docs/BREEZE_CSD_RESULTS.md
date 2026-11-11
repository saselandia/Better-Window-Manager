# Verificación de decoraciones CSD/SSD — F7

**Pendiente de reiniciar sesión entrando en Breeze.** F6b y F7 se preparan juntos; no se ha cargado el plugin nuevo en caliente ni se ha validado su resultado visual en apps reales.

| App / caso | Esperado nominal (manda el protocolo/hint real) | Obtenido con F7 |
| --- | --- | --- |
| kitty | SSD (decoraciones habilitadas) | Pendiente tras reinicio |
| Firefox | CSD; SSD si se activa barra del sistema | Pendiente tras reinicio |
| Nautilus | CSD (libadwaita, sin negociación) | Pendiente tras reinicio |
| Dolphin | SSD (Qt) | Pendiente tras reinicio |
| Steam | CSD si Motif decorations=0 | Pendiente tras reinicio |
| Vesktop | CSD; probar también barra del sistema | Pendiente tras reinicio |
| Stremio | CSD (GTK4 en este equipo) | Pendiente tras reinicio |
| Signal | CSD; probar también barra del sistema | Pendiente tras reinicio |
| Krita | SSD (Qt Widgets) | Pendiente tras reinicio |
| Claude | CSD (Electron) | Pendiente tras reinicio |
| VS Code / Codium | CSD; probar también barra del sistema | Pendiente tras reinicio |
| Kate flatpak | SSD (verificar instancia flatpak) | Pendiente tras reinicio |
| Qt Widgets (qt6ct/designer) | SSD | Pendiente tras reinicio |
| xterm / xeyes XWayland | SSD, sin hints CSD | Pendiente tras reinicio |

Después de iniciar sesión, abrir las apps instaladas y ejecutar:

    python3 ~/.config/hypr/skins/plasma/scripts/csd-audit.py --output /mnt/HDD1TB/Projects/hyprland-de/docs/BREEZE_CSD_RESULTS.md

El informe no lanza ni modifica apps, no cambia preferencias y no guarda títulos de ventanas.
«No observada» significa que no hay una ventana coincidente, no que se haya probado ni que no esté instalada.
La clasificación por app sólo etiqueta la tabla de pruebas: no decide CSD/SSD.

Casos adicionales que hay que comprobar visualmente:

1. En Firefox/Chromium/Electron, activar/desactivar la barra del sistema sin cerrar la app; no debe aparecer una segunda barra.
2. Alternar CSD/SSD varias veces (más de cuatro con el protocolo KDE antiguo), maximizar, entrar y salir de fullscreen.
3. En una ventana X11 de prueba, cambiar/borrar Motif y GTK_FRAME_EXTENTS (incluido un hint válido con ceros) y volver a consultar.
4. Probar breezebars:no_bar=true/false; false vuelve a automático, no fuerza una barra sobre un CSD. F10 traducirá las reglas NoBorder de KWin.
5. Encajar/colocar CSD y SSD en ambos monitores: el panel reservado y todo el marco KDE deben quedar dentro del área útil; cambiar de tema de decoración (Breeze/Aurorae) y repetir.

No hay que reiniciar la sesión desde una prueba automática, ni usar plugin unload/load para validar estos cambios.
