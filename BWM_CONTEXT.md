# 📘 BWM (Better Window Manager) — documento de contexto

> **Para qué sirve:** memoria completa del proyecto para retomarlo en cualquier sesión de IA o
> terminal: qué hay ahora (§2), cómo se llegó ahí (§3), dónde está cada cosa (§4), qué se tocó
> fuera del repo (§5), git (§6) y cómo trabajar (§7). `AGENTS.md` y `CLAUDE.md` son el resumen corto
> con las mismas reglas; este archivo es el detalle. Los tres están versionados.
>
> **Cómo leerlo:** §2 es la verdad actual. El historial de §3 es cronológico y conserva lo que se
> hizo en cada momento: cuando algo quedó superado lo indica con **⚠️ Superado en parte por §3.N**.
> Fechas en formato AAAA-MM-DD. Última revisión: 2026-10-27. Estado de Git: consulta §6; no uses los hashes históricos como estado actual.
> Registra las pruebas realizadas y sus límites; una instrucción dada al usuario no confirma su ejecución.

**Vocabulario:** **estilo** (*skin*) = Default, Retro, KDE Plasma. **Tema** = lo que hay dentro de
un estilo (los 23 temas de Omarchy en Retro o su paleta dinámica). Los nombres internos siguen con
«theme» (`bwm-theme-manager.py`, `theme.lua`, `Appearance.isRetro`…).

---

## 1. 🖥️ Qué es, máquina y rutas

**BWM** es un entorno de escritorio para Wayland sobre **Hyprland 0.55.4 configurado en Lua**
(tag `v0.55.4`, commit `a0136d8c`) y **Quickshell** (Qt 6/QML; config `ii`, derivada de
end-4/illogical-impulse), con tres estilos que cambian todo el escritorio y las apps.

| | |
| :--- | :--- |
| Usuario | `sasel` (git `saselandia`, habla español) |
| Sistema | Gentoo `x86_64`, kernel `7.2.5-cachyos`, systemd (sesión de usuario) |
| Hardware | Ryzen 9 7900 (iGPU AMD) + GPU NVIDIA |
| Monitores | LG UltraFine 4K arriba a la derecha (`1920x0`, 60 Hz) y HP X24ih 1080p@144 principal (`0x1080`). **Siempre por `desc:`**, nunca `DP-N` |
| Terminal | kitty (control remoto `listen_on unix:@kitty`) |
| Inicio de sesión | SDDM con tema de Omarchy en un Hyprland mínimo (Retro pide contraseña; Default/Plasma autologin + bloqueo de Quickshell) |
| Flatpaks | Vesktop, Spotify, Stremio, Kate, ProtonUp-Qt, Modrinth, Sober |

**Estilos:**
1. `default` — Material You (matugen) que sigue al fondo; barra y paneles de end-4.
2. `plasma` — clon de KDE Plasma 6 Breeze Dark: panel, Kickoff, applets, Alt+Tab, OSD, barras de título Breeze con hyprbars propio y snapping con previsualización.
3. `retro` — clon de **Omarchy 4** (basecamp/omarchy, rama `quattro`, MIT): su barra, menú, lanzador, paneles, notificaciones, OSD, polkit, bloqueo, 23 temas estáticos o paleta dinámica del fondo, y el tema de todas sus apps.

**Rutas:**
* Repo: `/mnt/HDD1TB/Projects/hyprland-de` (enlace `~/Projects/hyprland-de`).
* Enlaces de `~/.config` al repo (editar el repo = editar lo que corre): `hypr`, `quickshell`, `illogical-impulse`, `rofi`, `kitty`, `matugen`, `swaync`, `gtk-3.0`, `gtk-4.0`, `xdg-desktop-portal`, `nvim`.
* Estado generado (no en el repo): `~/.local/state/bwm/` (paleta y tema de Omarchy en `omarchy/`, Steam, iconos, arranque…), `~/.local/state/omarchy/current/theme` → `~/.local/state/bwm/omarchy/theme`, `~/.config/bwm/` (plugins de la barra, dock, apps predeterminadas, hooks), `~/.config/omarchy/language`.
* Remotos: `origin` (GitLab + GitHub a la vez con `git push origin main`), `gitlab`, `github`.

---

## 2. 🧭 Estado actual (resumen por áreas)

### 2.1 Estilos y temas
* Gestor: `config/hypr/scripts/bwm-theme-manager.py get|set|toggle|list <estilo>`. Al cambiar: perfil de Quickshell por estilo (`illogical-impulse/config-<estilo>.json`, secciones propias en `THEME_SPECIFIC_SECTIONS`), colores de Hyprland, plugins (hyprbars sólo en Plasma), iconos, GTK/Qt, apps, reinicio limpio de Quickshell (candado `/tmp/bwm-theme-manager.lock`), swaync fuera de Retro, `hyprpolkitagent` fuera de Retro, Firefox reiniciado si cambió su CSS.
* Selector de estilos: Alt+T (Retro: carrusel 3D con capturas de lo que imita cada estilo, `skin-switcher.sh`; Default: rofi; Plasma: «Estilo global»). Temas de Retro: Alt+R (carrusel), menú → Estilo → Temas Retro, Ajustes → Temas.
* **Ajustes → Temas / Plugins** (dos páginas, en ambas apps): Temas muestra galería con miniaturas/paletas/tema elegido; Plugins muestra tarjetas, activación, posición y filtros Todos/Activados/Desactivados. Cada página tiene Instalados/Descubrir, búsqueda remota, Mostrar más, enlaces y Git/URL. `ThemesConfig.qml`, `PluginsConfig.qml` y módulo `addons/` con `qmldir`; backend `bwm-addons.py`, detalle en `docs/OMARCHY_ADDONS.md`.
* Temas de comunidad en `~/.local/share/bwm/omarchy-themes` (`XDG_DATA_HOME`); también se reconoce `~/.config/omarchy/themes`, que aquí enlaza al repo y no se usa como destino de instalación. `theme_directory()` y `list_omarchy_themes()` comparten precedencia, igual que la CLI y el carrusel.
* Retro estático/dinámico: `~/.local/state/bwm/omarchy/{theme.mode,theme.name,colors.toml,shell.toml}`; en estático cambiar el fondo no toca la paleta. Temas claros (White, Catppuccin Latte…) ponen las apps en claro.

### 2.2 Apps tematizadas
| App | Default | Plasma | Retro | ¿En vivo? |
| :--- | :--- | :--- | :--- | :--- |
| GTK 3 | matugen → `gtk-3.0/bwm-colors.css` | Breeze | Omarchy + capa TUI | Sí: tema `BWM-1/BWM-2` alternado (`gtk-theme.py`) |
| GTK 4 / libadwaita | `gtk-4.0/gtk.css` | Breeze | Omarchy + TUI | Al abrir (Nautilus y pavucontrol se reabren) |
| Qt nativo | qt6ct `colors/bwm.conf` | Breeze | Omarchy + fuente mono | Al abrir |
| KDE / Qt en flatpak | `~/.config/kdeglobals` (de bwm.conf) + overrides flatpak | igual | igual | Al abrir |
| kitty | matugen | Breeze | plantilla de Omarchy | Sí (`kitty-recolor.sh`, control remoto) |
| foot, alacritty, ghostty, helix, neovim, tmux, VS Code/VSCodium/Cursor, Claude Code, pi, Hermes, T3, fcitx5, Obsidian | — | — | plantillas de Omarchy (`bwm_omarchy_apps.py`), también sin instalar | foot/ghostty/helix/neovim/tmux sí |
| Neovim | — | — | LazyVim de BWM (`config/nvim`), todos los temas instalados | Sí (`bwm-theme-hotreload.lua`) |
| Vesktop | `themes/bwm.theme.css` «BWM Material You» | «BWM Breeze Dark» | «BWM Omarchy TUI» | Sí (escrito en el mismo inodo) |
| Firefox | userChrome + Pywalfox | igual | + capa TUI | Reinicio automático con sesión |
| Spotify | Spicetify MaterialYou | Breeze | `BWM-Omarchy` | Reinicio automático en su sitio |
| Steam (cliente/biblioteca, no Tienda/Comunidad web) | Adwaita-for-Steam `bwm` | igual | + esquinas rectas, mono y barra con fondo base (`overlays/steam.css`) | Reinicio automático (no con un juego abierto) |
| btop, swaync, rofi, Pywalfox, iconos (Papirus por acento en Retro) | sí | sí | sí | — |
| Stremio Linux Flatpak | paleta matugen | Breeze | paleta Omarchy + TUI | Web en vivo mediante `stremio-theme.cjs`; marco GTK al abrir |

### 2.3 Retro = Omarchy (Quickshell)
* **Barra** `modules/ii/bar/RetroBarContent.qml`: disposición y colores de Omarchy; menú, workspaces, reloj + indicadores (grabando, luz nocturna, no molestar, mantener despierto, recordatorios), plugins (`omarchy-plugins/`, `~/.config/bwm/omarchy-plugins.json`) y a la derecha actualizaciones, multimedia (apagado), bandeja, distribución de teclado, agentes, Tailscale, Bluetooth, red, audio, pantallas, energía — cada uno se oculta en Ajustes → Barra.
* Los widgets invisibles liberan su anchura en `OmarchyPluginSlot`; los que no caben se recortan/atenúan sin anular su medida. La bandeja se desplaza al ocultar widgets. El plugin multimedia `crmne.mpris` vuelve a `centerEnd` (derecha de la hora), con presupuesto de ancho antes de los indicadores. Activación y posición de plugins pasan de Ajustes → Barra a Plugins; los widgets fijos y el idioma siguen en Barra.
* **About del menú Retro:** `omarchy-launch-about` ejecuta Fastfetch con logo ASCII, marcos Hardware/Software/Age, autoajuste y brillo originales de Omarchy (`hypr/omarchy/about/`, MIT, `b8706a3f`). Datos de Gentoo/BWM mediante `bwm-about-data.py`; WM muestra la versión en ejecución de `hyprctl`, no la del binario recién actualizado. About de Settings no cambia.
* **Menú** (Super): `modules/ii/omarchyMenu` + catálogo `config/hypr/omarchy/bwm-menu.jsonc`. **Apps** (Super+Espacio): cuadrícula `AppGrid.qml`.
* **Dock** (opcional, Ajustes → Interfaz → Dock, apagado): `modules/ii/omarchyDock`, en workspaces sin ventanas en mosaico; Super+M minimiza a él.
* **Notificaciones** (`omarchyNotifications`), **OSD** (`omarchyOsd`), **polkit** (`omarchyPolkit`), **recordatorios** (`omarchy-reminder`), bloqueo estilo hyprlock, captura omasnap, portapapeles (Super+V), emojis (Super+.), salvapantallas de terminal, glass, transparencia de ventanas (Super+Backspace).
* Librerías de Omarchy vendidas: `quickshell/ii/Commons`, `quickshell/ii/Ui` (MIT). Comandos `omarchy-*` sustituidos en `config/hypr/scripts/omarchy-shims/` (enlazados en `~/.local/bin`).
* Idioma del shell de Omarchy: Ajustes → Barra (English / Español es-MX), ahora inglés.

### 2.4 Plasma (Quickshell + hyprbars)
Panel flotante/pegado, Kickoff, applets Bluetooth/red/audio/calendario/notificaciones, menú de tareas con miniaturas y «peek», Alt+Tab de KWin, OSD Breeze, «Mostrar escritorio», snapping con Ctrl+flechas y cuartos de pantalla, barras de título Breeze sólo donde la app no trae las suyas (`hyprctl hyprbars-csd`).

### 2.5 Ventanas, juegos y sistema
* `window-guard.py watch` (autostart): primary de XWayland = monitor del workspace 1, ventanas fuera de pantalla de vuelta, juegos sin bordes a pantalla completa. Regla `games-main-monitor` (HP, foco al activarse, inhibir reposo).
* `focus_on_activate = true`, `xwayland.force_zero_scaling = true`, `on_focus_under_fullscreen` por defecto (2).
* Las apps no pueden solicitar maximizado (`suppress-maximize-events`, global); incluye botones CSD. El maximizado/pantalla completa se controla con Alt+Enter (Plasma: maximizado, otros estilos: fullscreen), y fullscreen solicitado por juegos/vídeo sigue permitido. Kitty tiene `remember_window_size no` para no restaurar tamaño/estado maximizado de su caché. Véase §3.48.
* Atajos en `config/hypr/keybinds.json` → `keybinds-manager.py` → `modules/user_binds.lua`.
* Salvapantallas: `ScreensaverIdle.qml` inhibe el disparo automático si cualquier reproductor MPRIS está reproduciendo, además de respetar `Idle.inhibit` y los inhibidores Wayland; el inicio manual por IPC sigue disponible.
* Luz nocturna (panel de pantallas de Retro, menú, indicador junto al reloj): un solo estado `~/.local/state/bwm/nightlight.json` vía `nightlight.py`/`omarchy-toggle-nightlight [--on|--off|<K>]`. Usa hyprsunset si está instalado (como Omarchy; no tiñe capturas) y si no un `screen_shader` que `modules/nightlight.lua` conserva tras `hyprctl reload`; `autostart.sh` lo reaplica (`--apply`). Véase §3.49.
* Regla `electron-render-unfocused`: incluye `codex`, `codex-desktop`, `chatgpt` y `ChatGPT`. Regla persistente de virt-manager: flotante (`float = true`), según el estado guardado actual.

### 2.6 Pendiente / ideas
* De Omarchy sin portar: menú Estilo completo (barra opaca/transparente, reloj 12/24 h, esquinas, huecos, animaciones, branding), layouts de workspace (dwindle/scrolling/flotante, Super+L), atajos de ventanas (Super+Ctrl+F, Super+Alt+F, Super+O, scratchpad Super+S, consola Quake Super+`, copiar/pegar universal), Install/Remove adaptado a emerge/flatpak, web apps y TUIs, compartir (LocalSend), Setup (DNS, idioma, teclado, seguridad), interruptores rápidos y actualizaciones de firmware/hora.
* Qt sin recarga en vivo (qt6ct no repinta apps abiertas); Chromium sin tema (necesita política root).
* Entorno de pruebas aparte (Hyprland anidado + usuario + rama `dev`), antes cambiar `/home/sasel` fijos por `$HOME`.
* El actualizador Retro no sincroniza los repositorios ni gestiona noticias, `dispatch-conf` o `@preserved-rebuild`; los perfiles Default/Plasma aún conservan un `apps.update` heredado con `pacman`. Adaptar ese acceso a Gentoo.
* `QuickConfig.qml` ya no está en Ajustes (fondo aleatorio de Konachan y claro/oscuro de Default sólo estaban ahí).


### 2.7 Actualizar este equipo (Gentoo + Flatpak)
Las operaciones con sudo las ejecuta el usuario. Dar los comandos por pasos y revisar los avisos/errores antes de continuar:

```bash
sudo emerge --sync
sudo eselect news read
sudo emerge --ask --verbose --update --deep --newuse @world
# Tras una actualización correcta, si hay bibliotecas preservadas:
sudo emerge --ask @preserved-rebuild
# Si Portage avisa de configuraciones pendientes, revisarlas:
sudo dispatch-conf
flatpak update
```

* `eselect news` sin sudo pudo listar los avisos pero falló al guardar su estado con «Cannot update list of news items for repository "gentoo"». Verificado: `/var/lib/gentoo/news` y sus archivos son `root:portage`; `sasel` no pertenece al grupo `portage`. Usar sudo, sin cambiar permisos.
* `dispatch-conf`: comparar el archivo instalado con `._cfgNNNN_<nombre>`. `u` acepta el nuevo, `z` lo descarta, `m` permite fusionar, `q` sale. En esta sesión, `._cfg0001_virt-manager` conservaba todo y añadía `>=media-video/ffmpeg-8.1.2 x264` para `wf-recorder`; se recomendó `u` tras ver el diff. No convertir esa decisión concreta en una regla general.
* `omarchy-update` actualiza Flatpak y ejecuta `sudo emerge -avuDN @world`, pero **no hace sync**, no gestiona los pasos posteriores ni actualiza el checkout de BWM. El indicador sólo consulta lo disponible en los repositorios locales y `origin/main` (intenta un `git fetch origin`, con límite de 15 s).
* Si cambia Hyprland, revisar compatibilidad y recompilar los plugins antes de usarlos con la nueva versión (`-fno-gnu-unique`, `make install`, sin descarga/carga en caliente). Kernel/arranque: respetar §2 de `AGENTS.md`; nunca `grub-mkconfig`.
* No se ha confirmado que la actualización del sistema haya terminado. Tampoco se ha confirmado en esta sesión la aceptación del cambio en `dispatch-conf`.


### 2.8 Ajustes y About
* **Dos About distintos:** el del menú Retro es Fastfetch con presentación Omarchy (§3.47). El de Settings mantiene las tarjetas y enlaces BWM; el usuario pidió expresamente cambiar sólo el primero.
* Navegación: Plugins y Temas separados en ambas apps, Cursor conservado y Advanced eliminado (también su QML). Estilo conserva fuentes, glass, salvapantallas y arranque.
* About: tarjeta Distro con nombre/versión/logo detectados de os-release y enlace de inicio; tarjeta WM con BWM, logo del arranque y accesos a GitLab/GitHub. Documentation abre README.es.md en GitLab; Issues abre los de GitHub; Star tiene un GIF local de 32 fotogramas y abre GitHub. Sin botones de ayuda/documentación/bugs/privacidad de la distro ni Donate. Discussions omitido: GitHub API `has_discussions=false`, comprobado el 2026-10-27.
* `SystemInfoData.js` parsea comillas simples/dobles y valores sin comillas como datos, sin ejecutar shell. `SystemInfo.qml` aplica al cargar FileView, vigila cambios y recurre a `/usr/lib/os-release` si falta `/etc/os-release`. El lector anterior no reconocía el formato con comillas simples de Gentoo. Logo simbólico con fallback incluido y ColorOverlay para que sea visible sobre fondos oscuros.

---

## 3. 📋 Historial (cronológico)

Peticiones del usuario y cómo se resolvieron, en el orden en que se hicieron (sesiones con Antigravity, Gemini y Claude Code). Los números de sección se citan como §3.N.

### 1. Sincronización y Configuración del Proyecto en Antigravity
* Integración del repositorio en Antigravity (`hyprland-de`).
* Configuración de la sincronización de avances y commits hacia ambos repositorios remotos (GitLab y GitHub).

### 2. Comportamiento de Pantalla Completa en KDE Plasma (`Alt + Enter`)
* **Petición:** Al pulsar `Alt + Enter` en el estilo KDE Plasma, la ventana debe maximizarse ocupando todo el espacio de trabajo pero **manteniendo la barra de tareas de Quickshell siempre a la vista** (estilo maximizado nativo de KDE), mientras que en los temas `default` y `retro` debe conservar la pantalla completa tradicional (ocultando barras).
* **Solución:** Ajuste en `config/hypr/scripts/quick-tile.py` y `config/hypr/modules/user_binds.lua` para verificar el estilo activo y despachar `quick-tile.py maximize` en lugar de `fullscreen 0` cuando el tema es Plasma.

### 3. Reasignación de Atajos de Quick Tiling / Snapping en KDE Plasma
* **Petición:** Los atajos de snapping a bordes (`Super + flechas`) debían convertirse en `Ctrl + flechas` (`Ctrl + Up / Down / Left / Right`), exclusivo para el estilo KDE Plasma.
* **Solución:** `keybinds-manager.py` y `config/hypr/modules/user_binds.lua` se adaptaron para condicionar los atajos según el estilo activo:
  - Estilo Plasma: `Ctrl + Left/Right/Up/Down`.
  - Otros temas: `Super + Left/Right/Up/Down`.

### 4. Snapping en Cuartos de Pantalla (Esquinas) con Teclado
* **Petición:** Si una ventana ya está encajada a la izquierda o derecha (sea por teclado o arrastre con ratón), pulsar `Ctrl + Abajo` debe moverla al cuarto inferior correspondiente (abajo-izquierda o abajo-derecha), y `Ctrl + Arriba` al cuarto superior.
* **Solución:** Se implementó una máquina de estados contextual en `config/hypr/scripts/quick-tile.py`, detectando la posición actual de la ventana activa mediante llamadas a `hyprctl activewindow -j` y calculando el nuevo recuadro relativo al monitor.

### 5. Lanzador de Aplicaciones KDE Plasma Kickoff en Quickshell
* **Petición:** Crear un menú de aplicaciones nativo idéntico al lanzador Kickoff de KDE Plasma que se abra al pulsar `Super`, sustituyendo los menús genéricos en el estilo Plasma.
* **Solución:**
  - Se desarrolló `config/quickshell/ii/modules/ii/plasmaKickoff/PlasmaKickoff.qml` en Quickshell/QML.
  - Se estructuró en dos columnas: barra lateral con avatares, categorías y accesos rápidos de sesión (bloqueo, reinicio, apagado), y área principal con lista de aplicaciones.
  - Se corrigió el motor de búsqueda en vivo para filtrar ejecutables y nombres en tiempo real.
  - Se añadió la sección de **"Aplicaciones recientes"** usando el historial de escritorio.
  - Se refinaron proporciones (diseño más fino y estilizado) y se extrajeron los iconos oficiales **Breeze Dark SVG** a `config/quickshell/ii/assets/icons/breeze-dark/`.

### 6. Corrección del Cuelgue del PC al Apagar / Cerrar Sesión
* **Petición:** Al apagar el ordenador se quedaba bloqueado en "cerrando sesión" durante minutos por culpa de procesos huérfanos.
* **Diagnóstico & Solución:** Se inspeccionaron logs de systemd (`journalctl`). Se detectó que procesos auxiliares arrancados en `autostart.sh` con combinaciones de `nohup` y `disown` ignoraban señales de terminación o mantenían descriptores abiertos. Se limpió `config/hypr/modules/autostart.lua` y `config/hypr/scripts/autostart.sh` garantizando un manejo adecuado de `SIGTERM` y desvinculación limpia.

### 7. Estilo Visual y Bordes de Ventana en KDE Plasma
* **Petición:** Eliminar la estela/halo gris residual que quedaba en los bordes de ventana y aumentar ligeramente el radio de redondeo de las esquinas.
* **Solución:** Se ajustaron los colores de borde inactivo en `plasma_colors.lua`, se eliminó el halo residual y se elevó el valor de `rounding` de `5px` a `8px` (después `12px`) en `config/hypr/modules/theme.lua` y `config/hypr/scripts/bwm-theme-manager.py`.

### 8. Window Snapping Interactivo con Ratón y Previsualización Traslúcida (KDE Style)
* **Petición:** Al arrastrar una ventana con el ratón por su barra de título hacia los bordes de la pantalla, debía aparecer un área resaltada traslúcida (*snap highlight preview*) indicando exactamente cómo y dónde se va a posicionar la ventana antes de soltar el botón del ratón.
* **Solución:**
  - Se modificó a bajo nivel el código fuente en C++ del plugin `hyprbars` (`src/hyprbars/`).
  - Se creó `SnapHelper.hpp` y `BarPassElement.cpp` integrados con `CRenderPass` de Hyprland para pintar la geometría proyectada en el buffer gráfico de Wayland.
  - Se recompiló `hyprbars-plasma.so` con la bandera crítica `-fno-gnu-unique` (necesaria en Gentoo para evitar colisiones de símbolos ELF al descargar y recargar plugins en tiempo de ejecución de Hyprland).
  - Se implementó la persistencia y restauración del tamaño previo (`pre-snap size`) para que al des-snappear una ventana recupere su geometría flotante original.
  - Se solucionó el problema de clics "tragados" tras soltar la barra CSD.

### 9. Corrección de Barras Duplicadas y Sincronización Flotante / Tiling al Cambiar Temas
* **Petición:** Al cambiar al estilo Retro y regresar al estilo Plasma, la barra de Quickshell se duplicaba en pantalla y varias ventanas que debían ser flotantes aparecían en modo tiling.
* **Solución:**
  - En `config/hypr/scripts/bwm-theme-manager.py` se robusteció la función de reinicio de Quickshell (`killall quickshell`, espera y comprobación con bloqueo `/tmp/bwm-theme-manager.lock`).
  - Se sincronizaron las reglas de flotabilidad en `config/hypr/modules/persistent_rules.lua` y `config/hypr/persistent_rules.json`.

### 10. Autodetección de Barras de Título y Decoración Breeze Real (KDE Plasma)
* **Petición:** No poner barra a las ventanas que ya traen sus propios botones (Claude, VSCodium, Firefox, Steam...) sin depender de listas de clases, y que la barra que se ponga sea la de Breeze Dark de KDE, no una inventada.
* **Solución:**
  - Nuevo `src/hyprbars/CSDDetect.cpp`: decide por ventana leyendo lo que la app negocia con el compositor: `xdg-decoration` (client-side → sin barra, server-side → barra), `org_kde_kwin_server_decoration` (Qt/Firefox), y en XWayland `_MOTIF_WM_HINTS` leído por xcb con timeout de ~60 ms (Steam). Si no negocia nada, se asume CSD propia. Se eliminó la lista fija `isKnownCSD` y la regla de clases de `rules.lua`.
  - Diagnóstico: `hyprctl hyprbars-csd` lista cada ventana, si lleva barra y el motivo.
  - Override manual (rara vez necesario): regla `["hyprbars:no_bar"] = true/false`.
  - Botones `icon = "breeze:close|maximize|minimize"`: iconos vectoriales con la geometría de Breeze (cairo), círculo solo al pasar el ratón (rojo `#da4453` en cerrar), rombo de restaurar al estar maximizada.
  - Nuevas opciones `inactive_bar_color` y `col.inactive_text`: cabecera Breeze Dark `#2a2e32` / `#202326`, texto `#fcfcfc` / `#a1a9b1`, título centrado (`appearance.lua`).
  - `kitty.conf`: `hide_window_decorations no` para que kitty pida barra al compositor (antes quedaba sin marco ni botones).

### 11. Crash de Hyprland (SIGBUS → safe mode) al desplegar plugins
* **Problema:** Al recompilar `hyprbars` se hacía `cp hyprbars.so config/hypr/plugins/hyprbars-plasma.so` con Hyprland en marcha. `cp` trunca el `.so` que Hyprland tiene mapeado en memoria → **SIGBUS**, crash y arranque en *safe mode*.
* **Solución:** Objetivo `make install` en `src/hyprbars/Makefile` y `src/csd-minimize/Makefile` que instala a un temporal y hace `mv` (rename atómico, no toca el inodo en uso). `csd-minimize` ahora también compila con `-fno-gnu-unique`. El plugin nuevo se carga al reiniciar la sesión.

### 12. Applet Bluetooth estilo KDE Plasma (Bluedevil) en Breeze Dark
* **Petición:** GUI de Bluetooth idéntica a la de Plasma 6, abierta desde el botón Bluetooth de la barra Plasma.
* **Solución:** `config/quickshell/ii/modules/ii/plasmaBluetooth/PlasmaBluetooth.qml` (registrado en `panelFamilies/IllogicalImpulseFamily.qml`):
  - Cabecera con interruptor, "Emparejar dispositivo…" (escaneo 60 s con barra indeterminada) y botón Configurar (`Config.options.apps.bluetooth` → `blueman-manager`).
  - Secciones *Conectados / Disponibles / Dispositivos encontrados*, filas desplegables con acción por defecto (Conectar / Desconectar / Emparejar), detalles (nombre, dirección, tipo, batería, confianza, adaptador) y botones Confiar / Olvidar.
  - Placeholders para sin adaptador, Bluetooth desactivado y sin dispositivos.
  - Iconos Breeze Dark empaquetados en `config/quickshell/ii/assets/icons/breeze-dark/bluetooth/`.
  - Botón de la barra: clic izquierdo abre el applet (anclado encima del botón), clic central activa/desactiva Bluetooth. Estado en `GlobalStates.plasmaBluetooth*`. IPC: `qs -c ii ipc call plasmaBluetooth toggle|open|close`.
  - Requisitos nuevos: `bluez` (+ `bluez-utils` en Arch) y `blueman`.

### 13. Applet de Redes estilo KDE Plasma (plasma-nm) en Breeze Dark
* **Petición:** GUI de red como la de Plasma 6 en el botón de red de la barra Plasma.
* **Solución:** `config/quickshell/ii/modules/ii/plasmaNetwork/PlasmaNetwork.qml`:
  - Cabecera: interruptor Wi-Fi, modo avión (apaga radios y Bluetooth, recuerda el estado previo), búsqueda y Configurar (KCM de plasma-nm si existe → `nm-connection-editor` → `nmtui` en kitty).
  - Secciones *Conectadas / Disponibles* con conexiones cableadas y Wi-Fi: icono de señal Breeze (con candado si es segura), estado con velocidad ⬇/⬆ en vivo, Conectar / Desconectar, campo de contraseña en línea para redes nuevas, Olvidar para redes guardadas.
  - Conexión activa desplegada: pestañas *Velocidad* (gráfica de 60 s en Canvas) y *Detalles* (interfaz, IPv4/IPv6, puerta de enlace, DNS, MAC, BSSID, frecuencia, seguridad, señal).
  - Backend: servicio `Network` + `nmcli` (dispositivos, conexiones guardadas, `/sys/class/net/*/statistics`). Estado en `GlobalStates.plasmaNetwork*`. IPC: `qs -c ii ipc call plasmaNetwork toggle|open|close`.
* **Componentes Breeze comunes:** `modules/ii/plasmaCommon/` (singleton `Breeze` con paleta + iconos, `BreezePopupWindow`, `BreezeHeader`, `BreezeSwitch`, `BreezeButton`, `BreezeToolButton`, `BreezeTextField`, `BreezeSectionHeader`, `BreezePlaceholder`, `BreezeDetailKey/Value`). El applet Bluetooth se reescribió sobre ellos.
* Requisitos: `networkmanager` y `network-manager-applet` / `nm-connection-editor`.

### 14. Calendario, app de ajustes Plasma y opciones del panel
* **Calendario:** clic en el reloj de la barra Plasma → `modules/ii/plasmaCalendar/PlasmaCalendar.qml` (popup del reloj digital de Plasma: fecha larga + hora, mes con anterior/Hoy/siguiente, semanas ISO, lunes primero, rueda para cambiar de mes). IPC `plasmaCalendar`. Sólo un popup de la barra abierto a la vez (`togglePopup` en `PlasmaBarContent.qml`).
* **Panel Plasma** (`bar.plasma` en config): `style` = `translucent` (por defecto) / `opaque` / `floating` (separado `floatingGap` px de los bordes y redondeado; Kickoff y applets flotan igual), `centerTasks` (iconos centrados en el panel). `Appearance.sizes.plasmaFloating/plasmaFloatingGap/plasmaPanelHeight`; en flotante `baseBarHeight` = panel + hueco.
* **Mostrar escritorio:** franja cuadrada a toda la altura del panel en el borde derecho.
* **Kickoff** más estrecho: 460 px (barra lateral 140).
* **App de ajustes Plasma:** `config/quickshell/ii/plasmaSettings.qml`, estilo Preferencias del sistema de Plasma 6 (barra lateral con buscador e iconos Breeze, cabecera con título). Carga las mismas páginas que `settings.qml` salvo *Barra de tareas* → `modules/settings/PlasmaBarConfig.qml`. Activa `MaterialThemeLoader.forceBreeze` y redondeos/fuentes Breeze sólo en su proceso.
* **Lanzador único:** `config/hypr/scripts/open-settings.sh` abre `plasmaSettings.qml` en Plasma y `settings.qml` en Default/Retro (Super+I, botón de la barra lateral, `open-autostart.sh`; respeta `SETTINGS_PAGE`).
* **Ajustes compartidos vs por estilo:** `bwm-theme-manager.py` (`THEME_SPECIFIC_SECTIONS`): `appearance, background, bar, dock, lock, osd, overview, panelFamily, waffles, wallpaperSelector, windows` son de cada estilo; el resto de `config.json` se hereda del tema saliente al cambiar. Autostart y atajos viven fuera de `config.json` y siguen siendo comunes.

### 15. Menú contextual y lista de ventanas en la barra de tareas Plasma
* **Petición:** Clic derecho en una app de la barra → menú estilo Plasma (abrir otra ventana, anclar, cerrar); con 2+ ventanas, desplegable con las ventanas y resaltado al pasar el ratón.
* **Solución:** `config/quickshell/ii/modules/ii/plasmaTaskMenu/PlasmaTaskMenu.qml` (registrado en `IllogicalImpulseFamily.qml`, estado en `GlobalStates.plasmaTask*`):
  - Menú: "Abrir nueva ventana", acciones del `.desktop`, Anclar/Desanclar, Cerrar (o "Cerrar todas (N)").
  - Lista al pasar el ratón (apps con 2+ ventanas): miniaturas en vivo (`ScreencopyView`); clic activa/restaura la ventana (la sube al frente), clic central o ✕ la cierra.
  - Peek: al pasar sobre una miniatura se dibuja una copia en vivo de la ventana en una capa Overlay click-through con el resto atenuado; no se toca el orden real de apilado, así que al quitar el ratón no hay nada que restaurar.

### 16. Panel flotante al estilo Plasma 6, color del panel y applet de notificaciones
* **Flotante combinable:** `bar.plasma.floating` (bool) independiente de `style` (`translucent`/`opaque`; el antiguo `style: "floating"` se lee como traslúcido + flotante).
* **Desacople al maximizar:** `modules/ii/plasmaCommon/PlasmaPanelState.qml` (singleton) marca por monitor si hay una ventana maximizada (ocupa el área útil, p. ej. Alt+Enter/quick-tile o botón de la barra de título) o en pantalla completa en su workspace activo; el panel se pega al borde (animado) y vuelve a flotar al restaurar. Kickoff y applets usan `PlasmaPanelState.gapFor(pantalla)` / `panelEdgeOffset(pantalla)`. El panel conserva su grosor al pegarse (sólo desaparecen los huecos laterales e inferior) y la zona reservada es sólo el grosor (`plasmaPanelHeight`), como en Plasma: el hueco flotante se solapa con el área de trabajo y una ventana maximizada llega justo al panel pegado. Radio flotante 18 px (Plasma real usa ~6 px; elegido por el usuario). Eventos de Hyprland + sondeo cada 700 ms (los redimensionados no emiten eventos).
* **Color y opacidad:** `bar.plasma.color` (por defecto `#24292e`) y `bar.plasma.opacity` (traslúcido). En Ajustes → Barra de tareas: muestras Breeze, campo hex y Restablecer.
* **Notificaciones:** campana en la bandeja de la barra Plasma (`notification-active/inactive`, tachada con No molestar). Con "Indicador de no leídas: mostrar número" muestra el contador; si no, un punto azul. Clic → `modules/ii/plasmaNotifications/PlasmaNotifications.qml` (historial, acciones, cerrar, Borrar todo, interruptor No molestar; al abrirse marca como leídas y oculta los popups). Clic central → No molestar. IPC `plasmaNotifications`.

### 17. Applet de Audio (plasma-pa) y selector de estilo Plasma
* **Audio:** `modules/ii/plasmaAudio/PlasmaAudio.qml` + `plasmaCommon/BreezeSlider.qml`. Cabecera con interruptor de mute y "Configurar…" (`apps.volumeMixer`); secciones Salida / Entrada (deslizador del dispositivo por defecto + lista para cambiarlo) y Aplicaciones (volumen por app). Iconos Breeze Dark en `config/quickshell/ii/assets/icons/breeze-dark/audio/`. Botón de volumen: clic izquierdo abre el applet, central silencia, rueda cambia volumen. IPC: `qs -c ii ipc call plasmaAudio toggle|open|close`.
* **Selector de tema:** `modules/ii/plasmaThemePicker/PlasmaThemePicker.qml` (estilo "Estilo global"); `theme-picker.sh` lo usa en el estilo Plasma (Alt+T, en el monitor enfocado).
* **OSD de volumen/brillo:** en el estilo Plasma `OsdValueIndicator.qml` dibuja una tarjeta Breeze (icono 32px, barra azul, porcentaje) abajo al centro; el botón de volumen de la barra ya no muestra el porcentaje (rueda sobre él → sale el OSD).
* **Alt+Tab clon de KDE Plasma:** `modules/ii/altTab/PlasmaSwitcher.qml` (solo en el estilo Plasma; los otros estilos conservan el HUD Material You). Cuadrícula de miniaturas en vivo con icono encima y título debajo, ventana seleccionada resaltada en el escritorio con el resto atenuado (efecto "Resaltar ventanas" de KWin), solo ventanas de los escritorios visibles + minimizadas (se restauran al elegirlas), Alt+` / Alt+Shift+` para ciclar entre ventanas de la misma app, flechas/Enter/Esc, hover selecciona, clic activa, clic central o ✕ cierra.
* `BreezePopupWindow`: el deslizado usa un offset (no la `y`) y respeta `bar.bottom`; `passBarClicks` deja libre la barra.

### 18. Mostrar escritorio y revisión del minimizado
* **Botón «Mostrar escritorio»** (franja derecha de la barra Plasma): recortado con la misma curva que el panel flotante (no sobresale de las esquinas), resaltado en azul mientras está activo. Clic → `toggle-minimize.py show-desktop`: minimiza todas las ventanas de los workspaces visibles de todos los monitores; otro clic las restaura en su orden. Estado en `$XDG_RUNTIME_DIR/bwm-show-desktop.json`.
* Mientras se muestra el escritorio el panel flotante se pega abajo (`PlasmaPanelState.showingDesktop`). Si aparece una ventana (abrir una app, restaurar una), se sale del modo como en KWin: `show-desktop leave` devuelve las ventanas ocultas y deja la nueva delante.
* **Fallos corregidos en el minimizado (`toggle-minimize.py`):**
  - Restaurar borraba todas las etiquetas de la ventana (incluidas `snapped_*` de quick-tile): ahora sólo quita `from_ws_*`.
  - Restaurar con un workspace especial abierto (scratchpad) abría `special:minimized`: eliminado.
  - La etiqueta `from_ws_*` se ponía con un conmutador; ahora con `+`.
  - Ventanas del monitor 4K minimizadas al workspace 99 (que vive en un solo monitor) volvían desplazadas: la geometría exacta se guarda en `$XDG_RUNTIME_DIR/bwm-minimized-geometry.json` y se reaplica al restaurar.
  - Alt + rueda (`e+1`/`e-1`) podía llevar al workspace 99 y enseñar las ventanas minimizadas: ahora usa `scripts/cycle-workspace.py`, que lo salta.
* El plugin `hypr-csd.so` está retirado: el botón de minimizar propio de las apps (CSD) lo atiende hyprbars (`requestsMinimize` → `toggle-minimize.py min <dirección>`).

### 19. Apps con un único tema oscuro en KDE Plasma (GTK, Qt y apps tematizadas)
> ⚠️ **Superado en parte por §3.36:** GTK 3 lleva los colores en el tema `BWM-1/BWM-2`, no en `gtk-3.0/gtk.css`.
* **Problema:** en Plasma `set-wallpaper.sh` no ejecuta matugen, así que GTK, Vesktop, Spotify (Spicetify), Firefox/Pywalfox, swaync, btop, los selectores de rofi y la propia Quickshell se quedaban con los colores Material You del último fondo de *otro* tema. Las apps Qt no tenían tema de plataforma y salían claras.
* **Solución:** `apply_plasma_colors()` llama a `apply_plasma_app_themes()` (`bwm-theme-manager.py`), que renderiza las mismas plantillas de `matugen/config.toml` con la paleta Breeze Dark (`BREEZE_DARK_M3`, igual que `MaterialThemeLoader.applyBreezeColors`), salvo `hyprland_colors` y `kitty` (ya tienen su paleta Breeze). Fija `gtk-theme=adw-gtk3-dark` y `color-scheme=prefer-dark`, y sólo reescribe/relanza hooks si el archivo cambia (cambiar de fondo en Plasma no reinicia Spotify).
* **Qt:** `config/hypr/modules/environment.lua` → `QT_QPA_PLATFORMTHEME=xdgdesktopportal` (Qt 6 sigue el modo oscuro del sistema; también exportado a D-Bus/systemd en `autostart.sh`). Verificado que no cambia el aspecto de Quickshell.

### 20. Spicetify/Blueman en oscuro y Alt+Tab
> ⚠️ **Superado en parte por §3.36:** las apps GTK 3 ya no se reabren: cambian en vivo (sólo pavucontrol, GTK 4, se reabre).
* **Apps tematizadas en Plasma (revisión):** GTK 3/4, Qt 6, kitty, Vesktop, Spotify (Spicetify), Firefox (Pywalfox/userChrome), swaync, btop, rofi y Quickshell quedan en Breeze oscuro. GTK 3 sólo lee `gtk.css` al arrancar: `apply_plasma_app_themes()` reabre `blueman-manager`, `pavucontrol` y `nm-connection-editor` si estaban abiertos y `gtk.css` cambió (`GTK_RELAUNCH_APPS`).
* **`reload-spotify.sh`** usaba `hyprctl dispatch exec ...` (sintaxis antigua, no funciona con la config Lua): cerraba Spotify y no lo volvía a abrir. Ahora `hl.dsp.exec_cmd(...)`.
* **Alt+Tab** (`modules/ii/altTab/AltTab.qml`, con el selector Plasma `PlasmaSwitcher.qml`): al abrirse pide una instantánea propia de `hyprctl clients/monitors`. Antes usaba `HyprlandData`, que descarta refrescos mientras hay uno en curso, así que el orden de última ventana enfocada (`focusHistoryID`) solía estar desfasado y una sola pulsación no cambiaba de ventana o elegía otra. Las pulsaciones de Tab que llegan mientras se abre se acumulan (`pendingSteps`) y soltar Alt antes de tiempo cambia directamente (`releasedEarly`). Verificado también con una ventana a pantalla completa en el mismo workspace (la otra ventana se ve encima y la de pantalla completa la conserva).

### 21. Retro: apps con estilo Omarchy reactivo al fondo
> ⚠️ **Superado en parte por §3.34:** VSCodium ya no usa `colorCustomizations`: lleva la extensión de tema de Omarchy.
* **Investigación:** Omarchy (MIT) describe cada estilo con `colors.toml` (16 colores ANSI + fondos/textos/acento) y genera por plantillas los archivos de cada app (`default/themed/*.tpl`: kitty, alacritty, ghostty, btop, hyprland, neovim, vscode, obsidian, chromium...); GTK sólo con `Adwaita-dark` + tema de iconos. Spotify, GTK con colores, Discord/Vesktop, Steam, Qt... los cubre la comunidad con **omarchy-theme-hook** (sin licencia publicada: no se copió código, sólo la idea; su tema de Discord además carga CSS remoto).
* **Implementación:** `config/hypr/scripts/bwm_omarchy.py`, llamado desde `apply_retro_wallpaper_colors()` (cambio de fondo en Retro y al entrar en Retro). En Retro ya **no se ejecuta matugen**:
  - Genera desde el fondo una paleta en formato Omarchy → `~/.local/state/bwm/omarchy/colors.toml` (acento aclarado para que se lea como texto, ANSI armonizados un 6 % hacia el acento).
  - kitty y btop con las plantillas oficiales de Omarchy (`config/hypr/omarchy/themed/`, MIT con atribución); btop pasa a `color_theme = "omarchy"`.
  - Todas las plantillas de matugen (GTK 3/4, Vesktop, swaync, Firefox, Pywalfox, Quickshell, rofi, btop, Hyprland) rellenas con la paleta Omarchy + capa TUI (`config/hypr/omarchy/overlays/`: JetBrainsMono Nerd Font, esquinas rectas, sin sombras, bordes finos de acento) y sus mismos hooks de recarga.
  - Spotify: tema Spicetify propio `BWM-Omarchy` (estilo terminal: monoespaciada, paneles enmarcados, sin degradados, títulos `> `), sólo se reaplica si cambió.
  - VSCodium: `workbench.colorCustomizations` en vivo, guardando y devolviendo las del usuario.
  - Al salir de Retro `restore_non_retro()` devuelve Spicetify a `MaterialYou`, btop a `matugen` y VSCodium a lo que hubiera.
* **Pendiente de Omarchy (para decidir):** ver la lista en la conversación del 2026-10-23 (iconos por estilo, Qt con qt6ct, Steam, web apps / TUI apps como lanzadores, launch-or-focus, toggles de ventana (gaps, transparencia, pop/pin, aspecto cuadrado, escritorio completo), cambio de layout dwindle/scrolling, salvapantallas TUI, modo glass, dictado, fuentes del sistema, tema de arranque Plymouth/SDDM, instalar temas desde git).

### 22. Funciones de Omarchy portadas (Estilo)
> ⚠️ **Superado en parte por §3.33:** Firefox se reinicia en cualquier cambio de estilo o tema Retro si cambió su CSS (`restart_firefox`).
* **Firefox al entrar/salir de Retro:** `bwm_omarchy.py restart-firefox` (lanzado por `apply_theme`) lo cierra con SIGTERM (guarda la sesión), lo relanza con el mismo comando y devuelve cada ventana a su workspace/tamaño por título. La capa TUI de Firefox anula también las variables `--border-radius-*` de Firefox reciente.
* **Salvapantallas de terminal:** `scripts/launch-screensaver.sh` (port de `omarchy-launch-screensaver`, kitty a pantalla completa en `special:screensaver-<monitor>`, tamaño de letra según el alto del monitor) + `scripts/bwm-screensaver.py` (efectos propios estilo TTE —descifrado, lluvia, haces, expansión, matrix— sobre el logo BWM con la paleta Omarchy; `ttfx` no está en Gentoo). Python va dentro de `sh -c` (como proceso directo de kitty terminaba al instante). Disparo: `modules/ii/screensaver/ScreensaverIdle.qml` (`IdleMonitor`, respeta inhibidores, «mantener despierto» y cualquier reproductor MPRIS en reproducción —`mediaPlaying`—; lo cierra con cualquier entrada). Config `screensaver.enable/timeoutMinutes`. IPC `screensaver start|stop`. Regla de ventana en `rules.lua`.
* **Spotify recuerda su workspace (2026-10-25):** `scripts/reload-spotify.sh` delega en `reload-spotify.py`, que guarda workspace (incluido `special:magic`), monitor y, si es flotante, geometría antes de reiniciar Spotify con el nuevo tema Spicetify y los restaura al aparecer la ventana nueva (distingue la ventana vieja por PID porque Hyprland reutiliza direcciones).
* **Fuente del sistema:** `scripts/font-set.sh list|current|set` (port de `omarchy-font-set`): kitty, alias `monospace` de fontconfig, fuente mono de GNOME y capa TUI de Retro (`bwm_omarchy.system_font()`).
* **Modo glass:** `scripts/glass.sh on|off|toggle` + `modules/glass.lua` (blur esmerilado de Omarchy, apps GTK al 80 %, capas `quickshell*` con blur) + `kitty/glass.conf` (fondo 0,65, `dynamic_background_opacity`).
* **Iconos por estilo:** `scripts/bwm_icons.py` (Plasma `breeze-dark`, Retro `BWM-Papirus` = Papirus-Dark con carpetas del color más cercano al acento, Default Adwaita) + `~/.config/qt6ct/qt6ct.conf` (en Retro también la fuente mono del sistema para las apps Qt).
* **Qt con la paleta:** plantilla `matugen/templates/qt6ct-colors.conf` → `~/.config/qt6ct/colors/bwm.conf` (la rellenan matugen, Breeze y Omarchy); `environment.lua` usa `QT_QPA_PLATFORMTHEME=qt6ct` si `/usr/bin/qt6ct` existe.
* **Steam:** Adwaita-for-Steam (MIT) clonado en `~/.local/share/steam-adwaita`; plantilla `steam-adwaita.css` (formato actual `--adw-*-bg-dark`, no los `-rgb` del hook) → `scripts/steam-theme.sh` lo instala con `--color-theme bwm --color-scheme dark` y, en Retro, `general/no-rounded-corners` + `--custom-css` con la fuente mono. Steam lo aplica al reiniciarse.
* **Arranque/inicio de sesión:** temas Plymouth y SDDM de Omarchy (MIT) en `config/hypr/omarchy/boot` con logo BWM; `scripts/bwm_boot.py render` los recolorea con el estilo activo en `~/.local/state/bwm/boot`; `sudo scripts/install-boot-theme.sh --plymouth | --sddm [--enable-sddm] | --revert | --auto | --no-auto` los instala o deshace Plymouth. **Automático:** `bwm_boot.py render` se lanza tras cada cambio de fondo (`set-wallpaper.sh`) y de tema (`bwm-theme-manager.py`) y sólo reescribe `~/.local/state/bwm/boot/.stamp` si el resultado cambia; `--auto` instala una copia root del script en `/usr/local/sbin/bwm-boot-theme` y `bwm-boot-theme.path/.service` (vigila el `.stamp`, espera 20 s sin cambios, copia sólo archivos de tema válidos y, si Plymouth está instalado —marcas en `/var/lib/bwm-boot-theme`—, rehace el initramfs con las comprobaciones, a prioridad mínima). Tras cambiar el script en el repo hay que repetir `--auto`. **Ojo:** aquí `grub.cfg` no se puede regenerar con `grub-mkconfig` (la línea `rd.luks…`/`root=` no está en `/etc/default/grub`); el script añade `splash` (sin `quiet`) a las líneas `linux` del `grub.cfg` existente (copia `.bwm-backup`) y rehace el initramfs con los mismos argumentos de dracut que tenía + plymouth (copia `.bwm-backup`). El initramfs incluye la llave LUKS (`/etc/dracut.conf.d`). No hay gestor de sesión: autologin en tty1 + `~/.bash_profile`.
* **SDDM como en Omarchy (`--sddm`, `--all`):** mismo `Main.qml` que Omarchy; el saludo corre en un Hyprland mínimo (`/usr/share/sddm/bwm-hyprland.lua`, copia de `default/sddm/hyprland.lua` de Omarchy) que el script root escribe validando `greeter.conf` (teclado y monitores `desc:` que genera `bwm_boot.py`), `/etc/sddm.conf.d/10-bwm-theme.conf`, `10-bwm-wayland.conf` (`DisplayServer=wayland`, `CompositorCommand=start-hyprland -- --config …`), `99-bwm-login.conf` (recordar usuario/sesión) y `/var/lib/sddm/state.conf` (sesión `hyprland.desktop`). `--enable-sddm` aparca el autologin de getty en `/var/lib/bwm-boot-theme/`; `--disable-sddm` lo devuelve; `--autologin` = autologin de SDDM (lo que hace Omarchy con disco cifrado). `--all` = `--sddm --enable-sddm --auto`. `install.sh` lo ofrece al final (`--login`/`--no-login`). `~/.bash_profile` sólo lanza Hyprland en un login de texto en tty1 (SDDM también lo lee). Probado: el tema en `sddm-greeter-qt6 --test-mode` y el Lua con `Hyprland --verify-config`.
* **Inicio de sesión por estilo (2026-10-24):** Retro → contraseña en SDDM (Omarchy) y `LockScreen.qml` no vuelve a bloquear si `Appearance.isRetro` y la sesión viene de SDDM (`XDG_SESSION_PATH` `/org/freedesktop/DisplayManager…`); Default/Plasma → autologin de SDDM y el bloqueo de Quickshell (`lock.launchOnStartup`) hace de inicio de sesión. `bwm_boot.py` escribe `theme=` en `greeter.conf` y `apply_login_mode()` (en `--sddm` y en el servicio `--sync`) pone o quita `/etc/sddm.conf.d/autologin.conf`; `--autologin` lo fija siempre (`/var/lib/bwm-boot-theme/autologin-always`).
* **Arranque lento (25 s) de Quickshell y del bloqueo:** `xdg-desktop-portal` tenía `FileChooser=nautilus` con un `~/.local/share/xdg-desktop-portal/portals/nautilus.portal` hecho a mano, pero Nautilus no implementa ese portal: al arrancar lo activaba y esperaba 25 s (`Settings.ReadAll` de Quickshell daba `NoReply`). `config/xdg-desktop-portal/*.conf` usa `FileChooser=gtk`. Además `autostart.sh` reintenta `swww img` hasta que ningún monitor quede en negro (entrando desde SDDM el fondo no se ponía).
* **Incidente 2026-10-23 (Plymouth):** la primera versión rehízo el initramfs con el módulo plymouth de dracut, que metió `amdgpu` (iGPU del Ryzen): 182 → 526 MB (GRUB lo lee del disco cifrado: ~27 s de cargador) y la iGPU arrancó antes que la NVIDIA, así que los conectores pasaron de DP-1/DP-2 a DP-2/DP-3 y las reglas de monitor por nombre cayeron en el monitor equivocado (los dos a 1080p en 0x1080, superpuestos). Arreglo: `monitors.lua` y `monitor-manager.py` usan sólo `desc:`; `--plymouth` conserva los drivers de GPU del initramfs original (`--omit-drivers`) y descarta el nuevo si crece más de un 50 %; `--revert` restaura las copias.
* **Bloqueo de pantalla en Retro:** `modules/ii/lock/OmarchyLockSurface.qml`, copia del `hyprlock.conf` de Omarchy (fondo desenfocado, una caja cuadrada de 650×100 con borde de 4 px, monoespaciada de 32 px, «Enter password», borde de acento al comprobar, «(N)» intentos fallidos). `Lock.qml` la usa si `Appearance.isRetro`; los otros estilos siguen con el bloqueo Material You.
* **Error de config en temas sin hyprbars:** los campos `hyprbars:*` de `hl.window_rule` sólo existen con el plugin cargado (Plasma); fuera de él dan «Your config has errors», y el aviso además reserva espacio arriba (la barra se separaba del borde). Van dentro de `if hl.plugin and hl.plugin.hyprbars then`.
* **Ajustes → Estilo** (`modules/settings/StyleConfig.qml`, en las dos apps de ajustes): fuente, glass, salvapantallas y arranque.
* Requisitos nuevos: `socat`, `qt6ct`, `papirus-icon-theme`; opcionales `plymouth`, `sddm`.

### 23. Ventanas y hotswap al estilo Omarchy (investigación del repo `basecamp/omarchy`, rama `quattro`)
* **Cómo lo hace Omarchy:** `colors.toml` → plantillas `default/themed/*.tpl` → `~/.local/state/omarchy/current/theme/` → `omarchy-theme-set` lanza en paralelo un `omarchy-theme-set-<app>` por app (terminales, btop, GTK vía `gsettings`, Chromium vía política `BrowserThemeColor`, VSCode, Obsidian, etc.) y al final `omarchy-hook theme-set` (scripts del usuario). **Omarchy no tematiza Discord ni la UI de Firefox**: Discord es una web app y Firefox sólo lleva `policies.json`; eso lo cubren hooks de la comunidad. Transparencia: sólo los terminales/TUIs (etiqueta `terminal`) y Nautilus llevan opacidad `0.985 0.96` (`o.transparent_window`); el resto de apps son opacas; tres modos (opaque/transparent/glassy) y `SUPER+BACKSPACE` alterna la ventana activa.
* **Implementado:** `modules/omarchy_windows.lua` (Retro: etiqueta `terminal`, opacidad Omarchy, estado `~/.local/state/bwm/windows-opaque`), `scripts/window-transparency.sh` (`status|opaque|transparent|toggle-window`, `SUPER+BACKSPACE`), Retro con `inactive_opacity = 1` y blur sólo en modo glass (antes 0,90 para todo). Hooks de hotswap: `~/.config/bwm/hooks/theme-set[.d]` (`bwm_omarchy.py hook <tema>`, variables `BWM_THEME`, `BWM_COLORS`, `BWM_STATE`) tras cada cambio de estilo y de fondo en Retro. Overlays TUI de Vesktop y Firefox ampliados (`hypr/omarchy/overlays`). Los atajos `Alt+\``/`Super+Backspace` están también en el generador de `keybinds-manager.py`.

### 24. Plugins de Omarchy, captura y workspace mágico en Retro (2026-10-25)
> ⚠️ **Superado en parte por §3.32:** la disposición de la barra, la bandeja y el reloj se rehicieron como en Omarchy.
* **Plugins del shell de Omarchy en la barra Retro:** `config/quickshell/ii/Commons` + `Ui` = `shell/Commons` y `shell/Ui` de Omarchy (MIT, `Commons/README.md`), así los plugins (`import qs.Commons`/`qs.Ui`) corren sin cambios. `Color.qml` lee `~/.local/state/bwm/omarchy/` (`colors.toml` + `shell.toml`, este último renderizado por `bwm_omarchy.apply_shell_toml` desde `hypr/omarchy/themed/shell.toml.tpl`). Anfitrión: `modules/ii/bar/omarchy/OmarchyPlugins.qml` (singleton = `bar.shell`: `serviceFor`, `updateEntryInline`, `pluginRegistry`, `barConfig`; crea los `service`; IPC `omarchyPlugins reload`) y `OmarchyPluginSlot.qml` (un `PluginBarApi` por widget; secciones `left`, `center` = junto al reloj, `right`). Gestor: `hypr/scripts/bwm-plugin.sh add|remove|update|list|enable|disable|catalog|defaults` (plugins en `~/.local/share/bwm/omarchy-plugins`, colocación en `~/.config/bwm/omarchy-plugins.json`). `defaults` = ai-usagebar (+ `cargo install` del binario en `~/.local`), omastats, omarchy-mpris, omarchy-active-window. `install.sh` lo ofrece (`--plugins`/`--no-plugins`). Ranking y detalles en `docs/OMARCHY_INVESTIGACION.md` §10. Probado con un plugin de prueba local (widget + servicio + `PopupCard`).
* **Plugins preinstalados (2026-10-25):** `config/quickshell/ii/omarchy-plugins/` (README con commits): `omarchy-clock` (el `omarchy.clock` de Omarchy: formatos, clic = calendario desplegable con progreso del año y semanas, clic derecho cambia formato), `ai-usagebar` (sólo `manifest.json` + `omarchy/`; el binario lo compila `bwm-plugin.sh build` = `cargo install --git … --rev d1af986f` en `~/.local/bin`, también `install.sh`), `omastats` (sin los binarios `bin/`: muestreador en Python), `omarchy-mpris`, `omarchy-active-window`. Activos salvo que estén en `disabled` de `~/.config/bwm/omarchy-plugins.json` (`OmarchyPlugins.effectiveEntries()`); secciones: active-window `left`, reloj `clock` (sustituye al reloj de BWM, que vuelve si se desactiva), omastats `centerEnd` (tras el reloj, para no pisarlo), ai-usagebar y mpris `right`. **Ajustes → Barra** (sólo Retro) tiene un interruptor por plugin (`BarConfig.qml`, lee `bwm-plugin.sh catalog` con su propio `Process` para no cargar plugins en la app de ajustes). `hypr/scripts/omarchy-shims/` sustituye los comandos de Omarchy que lanzan los plugins (`omarchy-launch-floating-terminal-with-presentation`, `omarchy-launch-or-focus-tui`, `omarchy-menu-timezone`); `OmarchyPluginSlot` los pone primero en el `PATH` de `bar.run`.
* **Revisión (2026-10-25):** el reloj/calendario de Omarchy ya no es plugin: `modules/ii/bar/omarchy/clock/` fijo en la barra Retro (`OmarchyPluginSlot.fixedEntries`; sus ajustes de formato se guardan como entrada `builtin` del layout). Nuevos preinstalados de Omarchy (primera parte): `omarchy-weather` y `omarchy-elsewhen` en `centerEnd` (como su `shell.json`); los scripts `omarchy-weather-*` de Omarchy van en `omarchy-shims` con la ciudad y unidades de `bar.weather`, y `bwm-plugin.sh catalog` enlaza los shims en `~/.local/bin` (los plugins los lanzan directamente, no por `bar.run`). omarchy-mpris no se veía: mide el hueco libre con los slots de Omarchy (`activeItem`/`region`, `BarGeometry.js`); `OmarchyPluginSlot` los expone y un slot invisible representa los iconos propios de la derecha; la sección derecha de plugins se limita al espacio libre (`Layout.maximumWidth`, recorte). omastats pasa a `right`.
* **Gestor de tareas en Retro:** `hypr/omarchy/applications/bwm-task-manager.desktop` (Task Manager / Gestor de tareas / … con palabras clave en inglés y español) → btop vía `omarchy-launch-or-focus-tui`; `bwm_omarchy.apply_task_manager()` lo instala en `~/.local/share/applications` al entrar en Retro y lo quita al salir. `services/AppSearch.qml` busca también en nombre genérico y palabras clave (después de los nombres), así «gestor de tareas» lo encuentra en una sesión en inglés.
* **Barra Retro, ajustes (2026-10-25):** omarchy-mpris por defecto en `center` (izquierda del reloj; `widthBudget` = hueco hasta la parte izquierda) con desplegable propio `NowPlayingPanel.qml` (clic izquierdo; carátula, progreso con seek, aleatorio/repetir, reproductores, «open player»; IPC `bwm.nowPlaying`). Los plugins de la derecha que no caben enteros se ocultan (`OmarchyPluginSlot.maxWidth`/`fittedCount`). Bandeja: `SysTray.itemSize` (Retro = 62 % de la altura). Escalado: `Commons/Style.qml` tiene `bwmScale` (Retro = altura/24) para que reloj, plugins y paneles de Omarchy escalen con la barra.
* **Aplicaciones predeterminadas** (Ajustes → Default apps / Aplicaciones predeterminadas, en las dos apps de ajustes): `modules/settings/DefaultAppsConfig.qml` + `hypr/scripts/default-apps.py list|set` (terminal → `~/.config/bwm/default-apps.json`, `apps.terminal`, `xdg-terminals.list`; navegador `xdg-settings`; archivos/editor `xdg-mime`; gestor de tareas → `apps.taskManager`, btop/htop en la terminal). `hypr/scripts/bwm-terminal [--class X] [--title T] -- cmd` abre la terminal predeterminada con los flags de cada una (kitty, foot, alacritty, ghostty, wezterm…); lo usan el Gestor de tareas de Retro y los shims de Omarchy. Regla de ventana `omarchy-floating-terminal` (flota, 875×600, centrada).
* **Audio, red y Bluetooth de Omarchy en Retro (2026-10-25):** `modules/ii/bar/omarchy/{audio,network,bluetooth}/` = los paneles de primera parte de Omarchy (MIT), fijos en la barra Retro (`omarchyStatus`, sustituyen a los botones de BWM, que quedan de respaldo). Sus scripts (`omarchy-audio-*`, `omarchy-bluetooth-*`, `omarchy-network-band/-status/-captive-portal`) van copiados en `omarchy-shims`, más sustitutos `omarchy-cmd-present`, `omarchy-launch-webapp`, `omarchy-audio-tuning` y un `omarchy-dns` de sólo lectura (el de Omarchy cambia el DNS del sistema como root). IPC `omarchy.audio|network|bluetooth open|close|toggle`. `OmarchyPlugins.summon()` es un stub (el test de velocidad es un overlay de omarchy-shell).
* **Ajustes rápidos centrados en Retro:** `sidebarRight` en Retro es una ventana centrada (ancho `sidebarWidth`+60, alto el del contenido, clic fuera/Esc cierra) sin notificaciones (`CenterWidgetGroup`) ni pestaña Calendario (`BottomWidgetGroup.tabs` filtra); se abre desde el menú (Ajustes → Ajustes rápidos) o la app «Quick Settings / Ajustes rápidos» (`hypr/omarchy/applications/bwm-quick-settings.desktop`, sólo en Retro como el Gestor de tareas: `bwm_omarchy.RETRO_APPS`). Ningún botón de la barra Retro la abre. El menú de Retro abre las apps `Terminal=true` (btop++) en la terminal predeterminada (`bwm-terminal`); `autostart.sh` crea/quita las apps de Retro al arrancar según el estilo.
* **Revisión de los commits 7e1273f/5e334e7 (otra sesión, 2026-10-25):** panel de pantallas (`bar/omarchy/monitor/Panel.qml`) rehecho en lo roto: pestañas propias (el `Button` de `qs.Ui` sólo mide su `text`, los hijos se salían), todo lo de debajo (brillo, escalado, resolución, refresco, orientación, principal, apagar) es de la pantalla seleccionada; brillo en un mapa `brightness` reactivo (antes mutaba `modelData`), varios cambios seguidos se aplican todos (un `Process` sólo corre uno), seleccionar ya no enfoca (usaba `hyprctl dispatch focusmonitor`, sintaxis antigua); luz nocturna y tamaño de texto como ajustes de todas las pantallas. Energía: título roto (`power.power` no existe), perfiles ocultos sin `powerprofilesctl` (el shim inventaba tres que no aplicaba). `RegionSelection.qml` tolera que el detector de imágenes no devuelva JSON.
* **Menú / paleta de comandos de Omarchy en Retro (2026-10-25):** `modules/ii/omarchyMenu/omarchy/{Menu.qml,MenuModel.js}` = el plugin `omarchy.menu` de Omarchy (MIT), con el catálogo de BWM `hypr/omarchy/bwm-menu.jsonc` (formato omarchy-menu.jsonc: ids con puntos = jerarquía, `action`/`target`/`provider`, `when`/`checked`/`disabled` en bash evaluados en lote, alias) + extensión del usuario `~/.config/bwm/extensions/menu.jsonc`; se recargan solos. Cambios: rutas de catálogo, ancho 360, paquetes con `qlist` (Gentoo) en vez de pacman. `OmarchyMenu.qml` es ahora el anfitrión (`AppLibrary.qml` = `shell.appLibrary` sobre AppSearch, apps de terminal con `bwm-terminal`; `summon` de overlays vía `OmarchyPlugins`). IPC `omarchyMenu toggle|open|close|summon <ruta>|refresh`; comando `omarchy-menu [ruta]` en los shims; proveedor `fonts` con `omarchy-font-current/list/set` → `font-set.sh`. Estado para los ✓: IPC `bwmIdle isInhibited|toggle` y `bwmNotifications isDnd|toggleDnd`.
* **Capturas de Omarchy en el menú de Retro (2026-10-25):** Acciones → Capturar (`trigger.capture.*` en `bwm-menu.jsonc`) con los scripts de Omarchy copiados en `omarchy-shims`: `omarchy-capture-text` (OCR con tesseract, todos los idiomas instalados), `omarchy-capture-qr` (zbarimg, al portapapeles con `--sensitive`), `omarchy-capture-screenrecording` (+`-process`, `-with-webcam`, `webcam-list/-resize`, `omarchy-capture-region`; gpu-screen-recorder o wf-recorder, audio de escritorio/micro, webcam con mpv+v4l2-ctl), `omarchy-menu-select` (usa el modo select del menú: `omarchy-shell shell summon omarchy.menu <json>` → IPC `omarchyMenu openPayload`), `omarchy-i18n` (+`plural.jq`, `cli.json` en/es-MX en `Commons/omarchy`) y el `omarchy-notification-send` real (las acciones de sus avisos son indicaciones propias de Omarchy: aquí salen sin botón). `scripts/bwm-require.sh <cmd> <paquete> … -- acción` avisa del paquete de Gentoo que falta. El indicador de grabación detecta también gpu-screen-recorder y lo detiene. `omarchy-shell` ignora `omarchy.indicators refresh`.
* **Notificaciones de Omarchy en Retro (2026-10-25):** `modules/ii/omarchyNotifications/` = el servicio `omarchy.notifications` de Omarchy (MIT: tarjetas agrupadas bajo la barra, glifos, acciones `--action` de `omarchy-notification-send` como «Abrir» al terminar una grabación, códigos copiables, No molestar, historial en `~/.local/state/omarchy/notifications`), cargado sólo en Retro (`IllogicalImpulseFamily.qml`, `Config.ready && Appearance.isRetro`). El `NotificationServer` de BWM (`services/Notifications.qml`) va en un `LazyLoader` con `Config.ready && !Appearance.isRetro`: sólo uno tiene `org.freedesktop.Notifications`; al cambiar de estilo Quickshell se reinicia y, si no, Quickshell reintenta el registro cuando el otro suelta el nombre. `OmarchyNotifications.qml` le da al servicio la posición/grosor de la barra Retro y sincroniza su No molestar con `Notifications.silent` (indicador, menú, IPC `bwmNotifications`). `omarchy-hyprland-focus-app` en los shims (clic en un aviso enfoca la app). **swaync** también reclama ese nombre (antes lo tenía siempre): `autostart.sh` no lo arranca en Retro y `bwm-theme-manager.py` lo cierra al entrar en Retro y lo vuelve a lanzar al salir.
* **Indicadores de Omarchy** junto al reloj (`OmarchyIndicators.qml`): grabando (rojo, `wf-recorder`), luz nocturna, no molestar, mantener despierto; sólo los activos, los inactivos al 45 % al pasar el ratón por el grupo o el reloj. Reloj con el formato de Omarchy `dddd HH:mm` (fecha larga al pasar el ratón).
* **Workspace mágico (Alt+S):** en `RetroBarContent.qml` los números se atenúan y aparece `[ 󰜗 magic ]` enmarcado en el acento (como la píldora del estilo Default); clic lo oculta. Usa `WorkspaceModel.specialWorkspace*`.
* **Captura estilo omasnap:** el selector de región en Retro usa marcos del acento, guarda en `~/Pictures/Screenshots` además de copiar y llama a `qs -c ii ipc call omarchyScreenshot show <png>` → `modules/ii/screenshotPreview/OmarchyScreenshotPreview.qml` (tarjeta en la esquina, 10 s salvo fijada o con el ratón encima; edit = satty/swappy, folder, pin, close). Sólo se carga en Retro.
* **Proporción cuadrada para ventana única (Super + Enter, port de Omarchy):** `scripts/toggle-single-window-aspect.sh` conmuta en caliente la opción nativa de Hyprland `layout:single_window_aspect_ratio` entre `1, 1` (cuadrada 1:1, centrada en pantalla para evitar que una única app se estire a todo lo ancho en pantallas ultra-anchas/4K) y `0, 0` (libre / estándar). Persiste el estado en `~/.local/state/bwm/single-window-aspect` y `modules/appearance.lua` lo restaura al recargar Hyprland o iniciar sesión. Atajo registrado en `keybinds.json` y `keybinds-manager.py` (`SUPER + RETURN`). Notificación informativa mediante `notify-send`.
* **Paneles de primera parte de Omarchy portados a la barra Retro (2026-10-25):**
  - **Monitor / Pantallas (`modules/ii/bar/omarchy/monitor/Panel.qml`):** Brillo independiente por pantalla (soporta ddcutil en pantallas externas como DP-1/DP-2 y backlight en portátiles), interruptor de luz nocturna (Night Light) con control deslizante Kelvin (3000K-6500K) integrado con `omarchy-toggle-nightlight` y `hyprsunset`, conmutador dinámico de resolución, tasa de refresco (Hz), orientación y escalado fraccionario por monitor.
  - **Energía y Batería (`modules/ii/bar/omarchy/power/Panel.qml`):** Conmutador de perfiles de rendimiento (`Performance`, `Balanced`, `Power Saver`) con persistencia en `~/.local/state/omarchy/powerprofiles/ac` y compatibilidad transparente con o sin `power-profiles-daemon`; interruptor de inhibición de reposo / Stay Awake (Caffeine) bidireccional conectado con `qs.services.Idle` y `omarchy-toggle-idle`; soporte desktop completo (icono de AC plug/perfil cuando no hay batería presente).
  - **Test de Velocidad de Red y Disco (`modules/ii/bar/omarchy/speedtest/`, `disk-speedtest/` y `Ui/SpeedTestOverlay.qml`):** Overlays de reloj interactivo con medición en streaming de latencia ping, bajada y subida (fast.com/speedtest) y benchmark de lectura y escritura en disco MB/s (`omarchy-disk-speedtest`).
  - **Wi-Fi QR (`modules/ii/bar/omarchy/wifiqr/Panel.qml`):** Generador instantáneo de código QR para compartir la red Wi-Fi activa con móviles mediante `omarchy-network-qr` (`qrencode`), con revelación segura de contraseña bajo demanda.
  - **Tailscale Mesh VPN (`modules/ii/bar/omarchy/tailscale/Panel.qml`):** Estado de conexión, listado de nodos de la red, selección de Exit Node (incluyendo Mullvad) y transferencia de archivos Taildrop (`omarchy-tailscale-send`). Visibilidad dinámica condicionada a `tailscale.installed`.
  - **Panel de Agentes IA (`modules/ii/bar/omarchy/agents/Panel.qml`):** Visualizador de límites de tokens (sesión y semanal), saldo de créditos prepagados, cambio rápido de cuentas y cuentas secundarias para Claude Code, Codex y Grok con starter prompts interactivos.
  - **Integración de Overlays y CLI (`OmarchyPlugins.qml` y `omarchy-shell`):** `OmarchyPlugins.summon(id, args)` y `hide(id)` enlazados con Loaders e `IpcHandler` dedicados para invocar overlays desde los paneles internos (como los botones de Speedtest y QR dentro de `network/Panel.qml`) o mediante el CLI unificado `omarchy-shell <target> [method]`.

### 25. Rediseño del Panel de Monitores y Gestión Segura de Pantallas (2026-10-25)
* **Incidente:** Al hacer clic en un monitor en la lista de pantallas del panel portado de Omarchy (`monitor/Panel.qml`), Hyprland apagó la pantalla secundaria (DP-1, LG Ultrafine 4K) y migró los workspaces bruscamente, provocando que pareciera que Hyprland había caído en modo seguro.
* **Causa Raíz:** En el código original de Omarchy, hacer clic en una fila de la lista de pantallas ejecutaba `toggleDisplay(name, enabled)` llamando a `hl.monitor({ output = name, disabled = true })`. El usuario hizo clic para seleccionar y configurar la pantalla, pero el código lo interpretó como una orden de apagado instantáneo de la salida física. Además, al reencender usaba `position = "auto"`, lo que descuadraba la disposición de pantallas.
* **Solución Implementada:**
  1. **Persistencia de Coordenadas (`monitors_layout.json`):** `config/hypr/scripts/monitor-manager.py` ahora almacena y respeta estrictamente las coordenadas físicas (`1920x0` para LG 4K y `0x1080` para HP 1080p), resolución, refresco, escalado y rotación, garantizando que un monitor jamás pierda su posición ni use `position = "auto"`.
  2. **Comandos CLI de Gestión en `monitor-manager.py`:**
     - `get-state`: Devuelve JSON con todas las pantallas, brillo individual (DDC/backlight), modos disponibles (resoluciones y Hz), escalado, rotación y estado de luz nocturna.
     - `set-mode`, `set-scale`, `set-transform`, `set-primary`, `toggle-enable`, `set-brightness`, `get-brightness`.
     - Protección activa: Rechaza apagar la única pantalla activa si solo queda una encendida.
  3. **Luz Nocturna Nativa (`config/hypr/scripts/nightlight.py`):** ⚠️ Superado en parte por §3.49 (hyprsunset preferido, estado en `~/.local/state/bwm`).
     - Basada en `decoration:screen_shader` nativo de Hyprland con cálculo de coeficientes RGB por fórmula física de Kelvin (2700K - 6500K). Cero daemons externos, 144Hz fluidos, instantáneo. Enlazada a `omarchy-toggle-nightlight`.
  4. **Rediseño Completo de `monitor/Panel.qml`:**
     - **Pestañas de selección de pantalla:** Ahora hacer clic en una pantalla la **selecciona** para configuración y la enfoca en Hyprland, **NUNCA** la apaga.
     - **Brillo individual:** Sliders dedicados e independientes para cada pantalla conectada (vía `ddcutil`).
     - **Luz nocturna:** Interruptor + deslizador Kelvin en vivo.
     - **Ajustes de la pantalla seleccionada:** Selector de escalado fraccionario (1x, 1.25x, 1.5x, 1.6x, 2x), resolución, tasa de refresco (Hz), orientación (0°, 90°, 180°, 270°), botón de monitor principal y botón de encendido/apagado protegido con etiqueta clara.

### 26. Portapapeles y Selector de Emojis Gráficos en Quickshell (2026-10-25)
* **Petición:** Reemplazar los selectores externos de Rofi por las ventanas superpuestas de primera parte de Omarchy (`clipboard/Clipboard.qml` y `emojis/Emojis.qml`) integradas nativamente en Quickshell, con máxima ergonomía, búsqueda difusa, previsualización rica y soporte global en todos los temas.
* **Historial de Portapapeles Gráfico (`modules/ii/bar/omarchy/clipboard/Clipboard.qml`):**
  - Overlay de Quickshell invocado con `Super + V` (`omarchy-shell clipboard toggle`).
  - Motor de búsqueda difusa en vivo (`fzf`/FTS) y almacenamiento local en `~/.local/state/omarchy/clipboard/`.
  - **Detección rica de tipos (`ClipboardHistory.js`):**
    - **Colores HEX:** Detecta `#RRGGBB` / `#RGB` y muestra un chip de color real en la lista junto a un panel de previsualización con caja destacada (140x70px), código HEX formateado y descripción.
    - **Enlaces Web:** Icono distintivo `󰌹`, texto subrayado en acento y soporte para apertura directa en el navegador con `Alt + Enter`.
    - **Imágenes / Capturas:** Miniatura con esquinas redondeadas en la lista, visualizador adaptativo a escala completa en el panel derecho y metadatos de captura (`capturedAt`, resolución).
    - **Archivos:** Icono `󰈔` y conteo de ficheros copiados.
    - **Texto y Código:** Previsualización en fuente monoespaciada con recuento en vivo de líneas y caracteres.
  - **Barra inferior de atajos rápidos:** `↵ Pegar`, `⇧↵ / Ctrl+C Copiar`, `⎇↵ Abrir`, `Supr Borrar`, `⇧Supr Vaciar`, `Esc Cerrar`.
* **Buscador de Emojis (`modules/ii/bar/omarchy/emojis/Emojis.qml`):**
  - Overlay de Quickshell con catálogo offline `emojis.json` invocado con `Super + .` (`omarchy-shell emojis toggle`).
  - Cabecera con buscador en vivo e icono `󰍉` con contador dinámico de resultados.
  - Pie interactivo con previsualización ampliada (26px), nombre formal y etiquetas/palabras clave asociadas al navegar o hacer hover.
  - Al pulsar `Enter` o hacer clic pega el emoji seleccionado en la app previa; con `Shift + Enter` o `Ctrl + C` sólo lo copia al portapapeles sin pegar.
* **Disponibilidad Global en Todos los Temas (`shell.qml`):**
  - Se inicializó `OmarchyPlugins` en `shell.qml` (`Component.onCompleted`), garantizando que la captura en segundo plano del portapapeles (`capture.sh`) y los atajos globales `Super + V` y `Super + .` funcionen de inmediato en Default, Plasma, Retro o Waffle.
* **Solución Definitiva al Pegado en Hyprland 0.55+ Lua:**
  - **Ejecución de Dispatchers:** En Hyprland 0.55+, llamar a `hl.dsp.send_shortcut(...)` en Lua sólo construye el descriptor; para despacharlo debe evaluarse con `hl.dispatch(...)` (`hyprctl eval 'return hl.dispatch(hl.dsp.send_shortcut({ mods = "...", key = "..." }))'`).
  - **Detección inteligente de Ventana Destino:** Se consulta la clase de la app activa con `hyprctl activewindow -j`. Si es una terminal (`kitty`, `alacritty`, `foot`, `wezterm`, etc.) se despacha `Shift + Insert`; si es una app gráfica, navegador o Electron (`Telegram`, `Discord`, `Chrome`, `Firefox`, `Slack`, etc.) se despacha `Ctrl + V`.
  - **Persistencia de `wl-copy`:** Se eliminó la destrucción prematura con `kill` tras 200 ms que cortaba la negociación Wayland (`wl_data_device.data_offer`) antes de que apps pesadas leyeran el buffer.
  - **Temporizado de foco tras dismiss:** Se ajustó la espera a 220 ms para garantizar que el compositor ha desenfocado la capa layer-shell (`OverlayWindow`) y devuelto el foco de teclado a la app previa antes de inyectar las teclas.

### 27. Verificación y Optimización del Doble Sistema de Notificaciones (KDE/Default vs Retro)
* **Petición / Preocupación:** Verificar si tener dos servicios de notificaciones distintos (el servidor estándar de BWM/KDE junto al de Retro) causa conflictos en el sistema o penalizaciones de rendimiento en segundo plano.
* **Diagnóstico y Arquitectura:**
  - Se inspeccionó `config/quickshell/ii/panelFamilies/IllogicalImpulseFamily.qml` y `services/Notifications.qml`.
  - Se comprobó que ambos servicios implementan el protocolo estándar D-Bus `org.freedesktop.Notifications`.
  - La carga está gobernada por `extraCondition` en los Loaders de Quickshell:
    - Servidor Retro (`omarchyNotifications`): únicamente activo cuando `Config.ready && Appearance.isRetro`.
    - Servidor Default/Plasma (`Notifications.qml`): únicamente activo cuando `Config.ready && !Appearance.isRetro`.
  - **Resultado en Bus D-Bus:** Sólo un servidor reclama la interfaz `org.freedesktop.Notifications` a la vez. Cuando se cambia de tema, Quickshell descarga el componente anterior y monta el nuevo, liberando y reclamando el nombre del bus de manera atómica sin colisiones ni consumo duplicado de recursos o CPU.

### 28. Biblioteca de 23 Temas Estáticos Curados de Omarchy y Modo Dual en Retro (2026-10-25)
> ⚠️ **Superado en parte por §3.34:** VSCodium usa la extensión «Omarchy», no `colorCustomizations`.
* **Petición:** Retro generaba los colores únicamente a partir del fondo de pantalla. Se requería incorporar los 23+ temas estáticos oficiales calibrados a mano de Omarchy (Tokyo Night, Catppuccin Mocha/Latte, Nord, Gruvbox, Kanagawa, Rose Pine, Everforest, Osaka Jade, Solitude, Starship, Lumon, Miasma, Retro-82, etc.) con sus correspondientes `colors.toml`, fondos y estilos, añadiendo un conmutador para elegir entre paleta dinámica y tema estático oficial.
* **Implementación:**
  1. **Vendoring Completo de los 23 Temas:** Se alojaron en `config/hypr/omarchy/themes/` estructurados con sus archivos `colors.toml`, subcarpetas `backgrounds/` (o imágenes de fondo) y miniaturas visuales `preview.png`.
  2. **Modo Dual en Retro (`dynamic` vs `static`):**
     - Almacenado en `~/.local/state/bwm/omarchy/mode` y `current_theme`.
     - En modo `"dynamic"`, el cambio de fondo genera la paleta reactiva al vuelo.
     - En modo `"static"`, se utiliza la paleta oficial curada del tema seleccionado.
  3. **Protección de Paleta al Cambiar Fondo:** En modo estático, cambiar el fondo de pantalla mediante `set-wallpaper.sh` actualiza el fondo de escritorio y la pantalla de bloqueo, pero **preserva intacta la paleta de colores del tema estático**, evitando que Matugen o el extractor sobrescriban los colores de las aplicaciones.
  4. **Propagación Integral al Ecosistema:** Al activar un tema estático, `bwm_omarchy.py` renderiza y aplica en caliente los estilos a:
     - Terminal Kitty (`kitty-colors.conf`), monitor de sistema btop (`omarchy.theme`), editor VSCodium (`workbench.colorCustomizations`), Spotify/Spicetify (`BWM-Omarchy`), GTK 3 y GTK 4 (`gtk.css`), cliente Discord/Vesktop, centro de notificaciones swaync, navegador Firefox/Pywalfox, bordes y decoraciones de Hyprland (`retro_colors.lua`), Quickshell QML y selectores Rofi (`omarchy-colors.rasi`), además de sintonizar los iconos de carpetas Papirus con el acento del tema.
  5. **Compatibilidad WebP en Gentoo:** Se solventó la falta de soporte WebP nativo en la compilación de `PIL` canalizando la extracción a través de ImageMagick (`magick ... ppm:-`), evitando cualquier aviso de error en segundo plano.

### 29. Galería Visual 3D / Carrusel en Quickshell (`ImagePicker.qml`) (2026-10-25)
* **Implementación:** Se portó y adaptó el carrusel de selección tridimensional `config/quickshell/ii/modules/ii/bar/omarchy/image-picker/ImagePicker.qml`.
* **Características:**
  - Perspectiva 3D con proyección angular, escalado dinámico de elementos según su distancia al centro y reflejo visual suave.
  - Navegación por teclado (`Flecha Izquierda` / `Flecha Derecha`, `Enter` para aplicar, `Esc` para cancelar), desplazamiento por rueda de ratón y selección por clic directo.
  - Campo de búsqueda en vivo para filtrar rápidamente temas por nombre.
  - Ficha flotante con detalles del tema enfocado, miniatura ampliada y colores de acento.
  - Integración en `OmarchyPlugins.qml` mediante `imagePickerLoader` y handlers IPC registrados en `omarchy.image-picker` y `shell`.

### 30. Atajo de Teclado `Alt + R` y Puntos de Acceso al Selector de Temas (2026-10-25)
* **Atajo Global:** Se asignó `Alt + R` para abrir directamente el conmutador de temas de Retro (`omarchy-theme-switcher`). Registrado en `config/hypr/keybinds.json` y compilado en `config/hypr/modules/user_binds.lua` (`hl.bind("ALT + R", hl.dsp.exec_cmd("omarchy-theme-switcher"), ...)`).
* **Colección de Shims CLI (`config/hypr/scripts/omarchy-shims/` enlazados a `~/.local/bin/`):**
  - `omarchy-theme-set <tema> [--no-wallpaper]`: Aplica un tema estático y actualiza todo el sistema.
  - `omarchy-theme-list`: Lista todos los temas curados disponibles.
  - `omarchy-theme-current`: Muestra el modo activo (`dynamic` o `static`) y el tema actual.
  - `omarchy-theme-dir`: Devuelve la ruta a la biblioteca de temas.
  - `omarchy-theme-switcher`: Invoca el carrusel 3D de Quickshell.
* **Paleta de Comandos de Retro (`bwm-menu.jsonc`):**
  - Añadida la categoría `appearance.retro-palette` con accesos rápidos para abrir la galería visual, alternar entre paleta dinámica y estática, y seleccionar directamente cualquiera de los 23 temas oficiales.
* **Preferencias del Sistema (`StyleConfig.qml`):**
  - Sección "Paleta Retro (Omarchy)" con selector dinámico/estático, botón de apertura del carrusel 3D y chips interactivos con feedback visual del tema en uso.
* **Arreglos (2026-10-25, revisión de bdfbf9b):**
  - **Alt + R no abría nada:** `ImagePicker.qml` no cargaba («PreviewHold is not a type»). Quickshell no resuelve tipos de un archivo hermano cuando el componente se carga por `Loader` desde una carpeta que ningún módulo `qs.…` importa (ni con `import "."`): `PreviewHold` es ahora un `component` en línea. Quitado el precalentado `omarchy-theme-bg-boot-intro` (no existe en BWM).
  - Miniatura «Dynamic»: el Qt de Quickshell no decodifica WebP; `omarchy-theme-switcher` genera un PNG 1280×800 del fondo con `magick` (se rehace si cambia el fondo) en vez de enlazar el original.
  - `omarchy-theme-set` → `bwm_omarchy.set_theme()`: fuera de Retro guarda la elección (y el fondo del tema en `current_wallpaper_retro`) y cambia a Retro, en vez de recolorear las apps del estilo activo. Un tema estático con fondo pasa por `set-wallpaper.sh` (bloqueo y perfil al día, una sola pasada de paleta).
  - Avisos «Estilo Retro» sólo al elegir tema, no en cada cambio de fondo.
  - El color secundario del borde/rofi/Quickshell vuelve a salir del fondo en modo dinámico (`_secondary()` lo lee de `hyprland_active_border`; antes era siempre `bright_magenta`).

### 31. Juegos en pantalla completa en el monitor equivocado / diminutos (2026-10-25, todos los temas)
* **Problema:** Fallout 3 (y otros juegos de Wine/Proton) se abrían diminutos o por debajo de las pantallas.
* **Causa:** Hyprland no fija ningún monitor principal (RandR primary) en XWayland, así que Wine toma el primer output (el LG 4K, `DP-1`) y crea la ventana con su tamaño/posición, mientras la regla de Hyprland la mandaba al workspace 1 del HP. XWayland usa su propio espacio de coordenadas (los monitores van uno al lado del otro: LG en 0,0 y HP en 3840,0), distinto del de Hyprland.
* **Arreglo:** `config/hypr/scripts/xwayland-primary.py` (ctypes sobre libXrandr, sin `xrandr`) marca como primary el monitor del workspace 1; `status` lo muestra.
* **Segunda causa (ventana tapada / fuera de pantalla):** Fallout 3 está en modo ventana sin bordes (`bFull Screen=0` en `FalloutPrefs.ini`) a 1920×1080 y Wine la puso en 0,2160, justo debajo del HP: flotante, sin pantalla completa y fuera de todas las pantallas. Ninguna regla estática lo cubre (los juegos se colocan después de mapearse y Hyprland no emite eventos por eso).
* **`config/hypr/scripts/window-guard.py watch`** (lanzado por `autostart.sh`, sustituye al `watch` de xwayland-primary): mantiene el primary en `monitoradded/monitorremoved/configreloaded/moveworkspace`; revisa cada ventana nueva a los 0,3/1/2/4/7/12/20 s y al cambiar de título (como mucho cada 3 s): una flotante fuera de todas las pantallas vuelve centrada al monitor de su workspace; una XWayland flotante del tamaño exacto de un monitor pasa a pantalla completa en él (una vez por dirección+PID: si la sacas, no se vuelve a forzar; sólo enfoca si su workspace está a la vista). Ignora minimizadas (ws 99) y workspaces especiales. Probado con ventanas X11 falsas hechas con ctypes.
* **Revisado en Omarchy (`quattro`, 2fca7fe):** no tiene nada específico para juegos fuera de pantalla (sólo `xwayland.force_zero_scaling`, sin efecto a escala 1). Se toma lo útil, sólo para juegos: `focus_on_activate = true` en la regla `games-main-monitor` (Omarchy lo pone global; después también global en `appearance.lua` a petición del usuario, como Omarchy; además `xwayland.force_zero_scaling = true` para cuando algún monitor no esté a escala 1) e `idle_inhibit = "fullscreen"` en juegos y en Steam (`apps/steam.lua`). No se copia su `misc.on_focus_under_fullscreen = 1` (la ventana nueva se queda la pantalla completa y taparía el juego); BWM sigue con el valor por defecto (2). La regla `games-main-monitor` de `rules.lua` (clases `steam_app_N`, `gamescope`, `*.exe`) los lleva al HP por `desc:` (sustituye a la regla fija de Fallout 3 al workspace 1).

### 32. Barra Retro clonada de la de Omarchy y modo claro/oscuro de las apps (2026-10-26)
* **Problema:** con temas claros (White, Catppuccin Latte…) la barra Retro tenía el texto casi blanco (colores fijos `#f8fafc` en `RetroBarContent.qml`), una línea gris debajo, separadores, botones propios de BWM (captura, modo oscuro, teclado, micro, selector de tema) y workspaces `[ 2 ]`; las apps seguían en oscuro.
* **Barra** (`modules/ii/bar/RetroBarContent.qml`, reescrita): misma disposición que el `shell.json` por defecto de Omarchy y colores de su sección `[bar]` (`Commons/Color.qml` → `bar.text/background/active`), márgenes `Style.space(8)`, sin línea ni separadores. Widgets de Omarchy (MIT) como entradas fijas de `OmarchyPluginSlot`: `bar/omarchy/menu/` (logo de `cheatsheet.superKey`, abre `omarchyMenu`; clic derecho `bwm-terminal`), `bar/omarchy/workspaces/` (1-5 + los que existan, el activo con el glifo del layout 󱓻, los vacíos al 50 %; numeración global de BWM, sin el 99 de minimizadas) y `bar/omarchy/tray/` (su bandeja con cajón al pasar el ratón; fijar/ocultar con clic derecho en la flecha, se guarda como entrada `builtin`). Sin fondo (`bar.showBackground = false`) el texto lo elige `omarchy-shims/omarchy-bar-text-color` (copia de Omarchy) muestreando el fondo de pantalla bajo la barra; se repite al cambiar el fondo (`~/.cache/current_wallpaper`) o el tema.
* **Menú:** ancho 300 como Omarchy, orden de la raíz como el suyo (Apps, Aprender, Acciones, Estilo…) y 39 iconos vacíos de `bwm-menu.jsonc` rellenados (los de Omarchy o glifos Nerd equivalentes).
* **Modo claro/oscuro:** `bwm_omarchy.theme_mode()` lo resuelve como `omarchy-theme-color` (clave `mode`/`theme_type`, `light.mode`, brillo del fondo > 382). `apply_color_scheme()` pone `gtk-theme` `adw-gtk3`/`adw-gtk3-dark`, `color-scheme` `prefer-light`/`prefer-dark` y `pywalfox light|dark`; marca `~/.local/state/bwm/omarchy/light-scheme` para que `sync-nautilus.sh` no lo devuelva a oscuro y `restore_non_retro()` vuelva a oscuro al salir de Retro. Iconos `BWM-Papirus` heredan de Papirus-Light en temas claros (`bwm_icons.py`), Steam usa `--color-scheme light` (`steam-theme.sh`). Quickshell ya calculaba `darkmode` por el brillo del fondo.
* **Revisión (2026-10-26):** los temas estáticos sin `hyprland_active_border` ya no reciben un degradado inventado: como en Omarchy, el borde de ventana es el acento y el del menú/lanzador el color de texto (`active-border-foreground`). Workspaces: 1-5 y los demás sólo si están en el monitor de esa barra (el 10 del 4K no sale en la del HP). Bandeja: iconos al 68 % de la barra. `sync-nautilus.sh` no toca `color-scheme` en Retro (una ejecución atrasada devolvía `prefer-dark` tras elegir Lupine). Los widgets cargados por `Loader` desde `bar/omarchy/*` no se recargan en caliente: reinicia con `bwm-theme-manager.py set retro`. El menú de Omarchy pinta las filas en peso Medium: hace falta JetBrainsMono Nerd Font Medium (aquí sólo había Regular/Bold; instalados todos los pesos de nerd-fonts v3.4.0 en `~/.local/share/fonts`, Medium y SemiBold también en `assets/fonts` con la OFL, que `install.sh` copia).

### 33. Estilos vs temas, Vesktop/Firefox TUI y selector de estilos en Retro (2026-10-26)
> ⚠️ **Superado en parte por §3.35:** Quick CSS ya no copia el tema y Vesktop se escribe en el mismo inodo; las miniaturas del selector son capturas (§34).
* **Vocabulario:** lo que antes se llamaba «tema» (Default, Retro, KDE Plasma) es ahora **estilo** (*skin* en inglés); **tema** es lo de dentro de un estilo (los temas de Omarchy en Retro). Cambiado en textos visibles (menú de Retro «Estilo» / «Selector de estilos…» / «Temas Retro (Omarchy)», atajo Alt+T «Selector de estilos», ayuda de `bwm-theme-manager.py`, Ajustes → Estilo, «Estilo global» en Plasma), comentarios y documentación. Nombres de archivos, comandos e identificadores sin cambiar; atajos iguales.
* **Vesktop:** Omarchy no tematiza Discord y omarchy-theme-hook sólo cambia colores cargando un CSS remoto (base16-discord), así que hay tema propio: `hypr/omarchy/themed/vesktop.theme.css.tpl` («BWM Omarchy TUI»: colores de `colors.toml`, monoespaciada, sin redondeos, paneles enmarcados, selección invertida con el acento, caja de mensaje con prompt `❯`). `bwm_omarchy.apply_vesktop()` lo escribe en cada tema Retro (estático o dinámico). Un único archivo para todos los estilos, `themes/bwm.theme.css` (matugen lo escribe en Default como «BWM Material You», Plasma como «BWM Breeze Dark»), más `settings/quickCss.css`: Vencord los recarga en vivo. `vesktop_enable_theme()` cambia una vez `enabledThemes` de `material-you.theme.css` a `bwm.theme.css` (Vencord guarda sus ajustes al salir: cierra Vesktop, edita y lo reabre en su sitio).
* **Firefox:** la capa TUI (`overlays/firefox.css`) añade pestaña activa invertida (como tmux) y prompt `❯` en la barra de direcciones. Firefox sólo lee el CSS al arrancar: `restart_firefox()` lo reinicia si `~/.cache/material-you-firefox.css` es más nuevo que el proceso (espera a que el CSS deje de cambiar y usa un candado para que el cambio de estilo y el de paleta no reinicien dos veces); lo piden `bwm-theme-manager.py` en cada cambio de estilo y Retro en cada cambio de tema. Relanza sin las URL con las que se abrió (antes reabría la de inicio de sesión de Claude).
* **`restart_app()`** (bwm_omarchy): cierre con SIGTERM, edición opcional, relanzar y devolver cada ventana a su workspace (también especiales) y, si flota, posición y tamaño; casa ventanas por título y luego por orden, distinguiendo las viejas por PID.
* **Selector de estilos en Retro:** Alt+T en Retro abre el mismo carrusel 3D que los temas (`ImagePicker.qml`, `source: "skins"`, `skinMode`), con miniaturas del fondo de cada estilo (`hypr/scripts/skin-switcher.sh --print-rows`, PNG 1280×800 en `~/.cache/bwm/skin-switcher/`, la etiqueta es el nombre del archivo). Default sigue con rofi y Plasma con su «Estilo global».

### 34. Todas las apps de Omarchy en Retro, Vesktop más limpio y capturas en el selector de estilos (2026-10-26)
* **Plantillas de Omarchy:** las 16 de `default/themed` que faltaban (alacritty, chromium, claude, fcitx5, foot, ghostty, gum_env, helix, hermes, hyprland, hyprland-preview-share-picker, keyboard.rgb, neovim, obsidian, pi, t3code, vscode-theme) en `hypr/omarchy/themed/` (README con origen). `complete_colors()` añade `theme_type` y los alias `purple`/`magenta` que esas plantillas usan.
* **`hypr/scripts/bwm_omarchy_apps.py`** (lo llama `apply_retro_palette_colors` en cada tema Retro): `render_theme_dir()` escribe `~/.local/state/bwm/omarchy/theme` (archivos propios del tema estático primero —neovim.lua, vscode.json, btop.theme…— y plantillas para lo demás; borra lo que dejó el tema anterior) y `~/.local/state/omarchy/current/theme` apunta ahí (antes apuntaba a la carpeta del tema en el repo). `apply_apps()`, aunque la app no esté instalada: alacritty/ghostty/foot incluyen el tema desde su config (creada si falta), Helix `theme = "omarchy"`, Neovim `lua/plugins/theme.lua` si hay LazyVim, VS Code/VSCodium/Cursor extensión generada «Omarchy» (o la del tema estático si ya está instalada; si no, se intenta instalar en segundo plano y sólo se selecciona si funciona: Open VSX no tiene, p. ej., la de Lumon), Obsidian por bóveda, Claude Code `custom:omarchy`, pi/Hermes/T3 Code si existen, fcitx5, share-picker, tmux si hay sesiones. Chromium (política root), gum, teclado RGB y hyprland.lua quedan generados. `restore_apps()` al salir de Retro devuelve los temas de Helix, Claude Code, pi y los editores (`app-restore.json`). btop usa el `btop.theme` del tema si lo trae. El viejo `workbench.colorCustomizations` de BWM se quita (pisaba el tema).
* **Vesktop:** fuentes de reserva para símbolos (Noto, DejaVu, FreeSerif, emoji); botones de icono (micrófono, auriculares, ajustes, barras) planos sin marco, marco de acento sólo en botones de diálogos/formularios; panel de cuenta plano sin imagen de fondo; menús con el elemento activo invertido.
* **Selector de estilos:** capturas de lo que imita cada estilo en `assets/skin-previews/` (README con origen): end-4/illogical-impulse (Default) y Plasma 6.8 de kde.org (KDE Plasma); Retro usa la `preview.png` oficial del tema de Omarchy activo (Tokyo Night con paleta dinámica). Miniaturas en `~/.cache/bwm/skin-switcher/<hash>/` (la ruta cambia con la imagen para que Quickshell no muestre la de caché).

### 35. Neovim, apps no instaladas, kitty en vivo y Vesktop que se quedaba en un color (2026-10-26)
* **Neovim:** el `neovim.lua` de Omarchy es un plugin de LazyVim (Omarchy trae LazyVim); sin config no hacía nada. `config/nvim/` = LazyVim starter + `plugins/bwm-all-themes.lua` (todos los plugins de color de los temas de `hypr/omarchy/themes` y aether.nvim v3, instalados con `lazy = true`: lazy.nvim los carga al pedir su `:colorscheme`) + `plugins/bwm-theme-hotreload.lua` (vigila `~/.local/state/omarchy/current/theme` y aplica el `colorscheme` del `neovim.lua` nuevo; con aether, `setup(opts)` antes; `background` según `mode` de colors.toml) + `plugins/theme.lua` → `current/theme/neovim.lua` (enlace, en `.gitignore` con `lazy-lock.json`). `apply_neovim()` enlaza `~/.config/nvim` → `config/nvim` si no existe (si el usuario tiene la suya con `lua/plugins`, sólo pone `theme.lua`) e instala los plugins sin abrir ventana (`nvim --headless "+Lazy! sync"`). Probado: carga el tema activo y vuelve a él al reescribir el archivo con otro esquema puesto.
* **Apps no instaladas:** `apply_apps()` deja listo su tema para que salgan tematizadas al instalarlas: VS Code y Cursor (settings + extensión «Omarchy»), Claude Code, pi (`settings.json` con `omarchy-system`), Hermes, T3 Code, fcitx5 (`classicui.conf`), tmux (`~/.config/tmux/tmux.conf` con `source-file -q …/current/theme/tmux.conf` si no hay config), alacritty/ghostty/foot/helix (ya estaban). Obsidian sólo por bóveda; Chromium necesita la política root.
* **Kitty en vivo:** `hypr/scripts/kitty-recolor.sh` = `kitty @ --to unix:@kitty-<pid> set-colors --all --configured kitty-colors.conf` por cada kitty (control remoto de `kitty.conf`; SIGUSR1 si falla): también pisa colores cambiados por programas. Lo usan Retro (`apply_kitty`, siempre), matugen (`post_hook`) y Plasma. foot: secuencias OSC a cada shell (`recolor_foot`, port de omarchy-theme-set-foot/-osc).
* **Vesktop atascado:** Vesktop vigila `quickCss.css` por inodo (fs.watch); BWM lo reemplazaba con rename atómico → tras el primer cambio dejaba de enterarse, y Quick CSS (copia completa del tema, cargada después) mantenía el color viejo. Ahora el tema se escribe en el mismo archivo (`_write_in_place`), Quick CSS vuelve a un comentario (salvo CSS propio del usuario) y matugen ya no lo escribe (fuera `templates.vesktop_quickcss`). Un reinicio único de Vesktop (`~/.local/state/bwm/vesktop-watch-v2`). Corregido el relanzado de Vesktop en flatpak (Electron reescribe su argv como una sola cadena: se detecta `/app/` o `/proc/<pid>/root/.flatpak-info`).

### 36. GTK y Qt con el tema del estilo activo, también en flatpaks y en vivo (2026-10-26)
> ⚠️ **Superado en parte por §3.40:** Stremio ya tiene integración de su interfaz web; la Tienda/Comunidad de Steam siguen fuera de Adwaita-for-Steam.
* **Comprobado:** GTK 3/4 nativos ya tenían la paleta del tema Retro + capa TUI y Qt nativo la de qt6ct (`colors/bwm.conf`), pero sólo al abrir la app: GTK 3 lee `~/.config/gtk-3.0/gtk.css` una vez (alternar `gtk-theme` no lo relee: probado con blueman) y qt6ct no recarga la paleta de una app abierta (probado: su vigilante sólo mira la carpeta y no repinta). Los flatpaks (Kate y ProtonUp-Qt en runtime KDE; Modrinth, Stremio, Sober en GNOME) no veían nada.
* **GTK 3 en vivo:** `hypr/scripts/gtk-theme.py` (`set light|dark`, `reload`). Los colores van a `~/.config/gtk-3.0/bwm-colors.css` (matugen `templates.gtk3`, también Breeze y Omarchy, con `post_hook = gtk-theme.py reload`) dentro de un tema propio en `~/.local/share/themes/BWM-1|BWM-2` que importa `adw-gtk3[-dark]` + ese archivo; cada recarga alterna BWM-1/BWM-2 y GTK relee su tema (probado: blueman abierto cambia al momento). `~/.config/gtk-3.0/gtk.css` queda con un comentario (con colores pisaría los nuevos). Sustituye a fijar `adw-gtk3[-dark]` en `bwm_omarchy.apply_color_scheme`, `bwm-theme-manager.py` (Plasma) y `switchwall.sh`. GTK 4/libadwaita ignora el tema GTK: sigue con `gtk-4.0/gtk.css` al abrir (se reabre pavucontrol, `GTK_RELAUNCH_APPS`; Nautilus lo reabre `sync-nautilus.sh`).
* **Qt / KDE:** `bwm_icons.py write_kdeglobals()` genera `~/.config/kdeglobals` (marcado `[BWM]`; uno ajeno se guarda en `kdeglobals.bwm-backup`) con la paleta de `bwm.conf` (grupos Window/View/Button/Selection/Tooltip/Header, iconos y, en Retro, la fuente mono). Lo llaman `bwm_icons.apply` y `bwm_icons.py qt-sync` (`post_hook` de `templates.qt6ct`).
* **Flatpaks** (`bwm_icons.flatpak_overrides()`, en `qt-sync`): override global de usuario con acceso de sólo lectura a `xdg-config/gtk-3.0`, `gtk-4.0`, `kdeglobals`, `qt6ct`, `~/.local/share/themes`, `~/.local/share/icons`, `~/.themes` (enlace a `~/.local/share/themes`, GTK 3 en flatpak busca ahí) y `~/Projects/hyprland-de/config` (las carpetas de config son enlaces al repo), y `QT_QPA_PLATFORMTHEME=kde` (el plugin de KDE del runtime lee kdeglobals). Probado: Kate en flatpak sale con la paleta del tema. Vale para flatpaks instalados después.
* Qt nativo y flatpaks: el tema se aplica al abrir la app (no hay recarga en vivo fiable para Qt).
* **Steam y Stremio no son Qt.** Steam pinta su interfaz con su propio Chromium (CEF): se tematiza con Adwaita-for-Steam (`steam-theme.sh`, colores en `~/.local/state/bwm/steam/bwm.css`), que Steam sólo carga al arrancar; antes sólo avisaba. Ahora `steam-theme.sh` (post_hook de matugen cuando cambian sus colores) lanza `bwm_omarchy.py restart-steam`: `steam -shutdown` y vuelve a abrirlo con la ventana en su sitio (`restart_app(quit_cmd=…)`), o en la bandeja (`-silent`) si estaba ahí; con un juego abierto (`steam_app_*`, gamescope, `SteamLaunch AppId`) no lo toca y avisa. La Tienda y la Comunidad son la web de Steam y no cambian. Stremio (flatpak) es GTK 4 + libadwaita + WebKitGTK: recibe `gtk-4.0/gtk.css` (flatpak lo monta en `~/.var/app/<id>/config`), pero sólo afecta al marco y diálogos; el contenido es la web de Stremio, sin tematizar.

### 37. Lanzador «Apps» de Omarchy y parte derecha de la barra configurable (2026-10-26)
> ⚠️ **Superado en parte por §3.38:** Super+Espacio abre la cuadrícula y Super+Alt+Espacio no hace nada.
* **Lanzador:** el de Omarchy 4 es la cuadrícula «Apps» de su dock (`shell/plugins/dock/AppGrid.qml`, MIT): copiada en `modules/ii/omarchyMenu/omarchy/AppGrid.qml` sin el dock (`dock` nulo: sin «mantener en el dock»), anfitrión `OmarchyMenu.qml`, IPC `omarchyApps toggle|open|close`. Buscador de Omarchy (`services/AppSearch.js` → `omarchyMenu/AppSearchModel.js`: nombre, id, nombre genérico, palabras clave, siglas) ahora también en `AppLibrary.sortedEntries(query)` (antes ignoraba la búsqueda). Atajos como en Omarchy: **Super+Espacio** = menú/lanzador del estilo (igual que Super), **Super+Alt+Espacio** = Apps (`app-launcher.sh apps`; en los otros estilos su lanzador). La entrada «Apps» del menú de Retro abre la cuadrícula (`action` en `bwm-menu.jsonc`, como `omarchy-shell omarchy.dock apps`). Desinstalar desde ella sólo avisa (Gentoo).
* **Parte derecha de la barra Retro:** Ajustes → Barra → «Parte derecha de la barra» (sólo Retro) con un interruptor por widget fijo de Omarchy (bandeja, agentes, Tailscale, Bluetooth, red, audio, pantallas, energía). Se guardan en `disabled` de `~/.config/bwm/omarchy-plugins.json` (`bwm-plugin.sh hide|show <id>`) y `RetroBarContent.qml` los filtra en vivo.
* **Pendiente de Omarchy** (comparado con `quattro` 58858ae): lo que queda está en §2.6 (dock, OSD, polkit, recordatorios, actualizaciones e idioma ya se hicieron en §3.38).

### 38. Dock, OSD, polkit, recordatorios, widgets e idioma de Omarchy en Retro (2026-10-26, Omarchy `quattro` 58858ae)
> ⚠️ **Superado en parte por §3.39:** el dock es opcional y está apagado; el shell de Omarchy está en inglés con selector de idioma.
* **Atajos:** Super+Espacio = cuadrícula «Apps» (`app-launcher.sh apps`: la del dock, o la del menú si el dock no está); Super+Alt+Espacio quitado (Super ya abre el menú). Super+M = minimizar al dock.
* **Idioma:** `es-MX` de Omarchy (`shell.json`, `menu.json`, `keybindings.json`, `cli.json`) en `quickshell/ii/Commons/omarchy/default/i18n/es-MX/`; `~/.config/omarchy/language` = `es-MX` (lo crea `bwm_omarchy.ensure_omarchy_language()` según `LANG` si falta). Paneles, menú, dock, OSD, polkit y recordatorios de Omarchy salen en español.
* **OSD:** `modules/ii/omarchyOsd/` (Osd.qml + OsdModel.js de Omarchy). `onScreenDisplay/OnScreenDisplay.qml` en Retro llama a `showOmarchyOsd()` con las mismas señales (volumen, silencio, brillo, protección de volumen); el aviso de gamma sigue con el de BWM. IPC `osd show <json>`.
* **Polkit:** `modules/ii/omarchyPolkit/OmarchyPolkit.qml` (PolkitAgent.qml de Omarchy) sólo en Retro. Polkit admite un agente por sesión: `services/PolkitService.qml` crea el suyo con un `LazyLoader` fuera de Retro, `bwm-theme-manager.py` para `hyprpolkitagent` al entrar en Retro (antes de reiniciar Quickshell) y lo arranca al salir, y `autostart.sh` no lo lanza en Retro. Probado con `pkexec true`: diálogo de Omarchy en español.
* **Recordatorios:** `omarchy-reminder` de Omarchy en `omarchy-shims` (temporizadores `systemd-run --user`, avisos con `omarchy-notification-send`), overlay `bar/omarchy/reminders/ReminderFlow.qml` (`OmarchyPlugins.summon("omarchy.reminders")`, `omarchy-reminder -i`), menú Acciones → Recordatorio (poner/ver/borrar) e indicador 󰢌 en `OmarchyIndicators.qml` (cada 15 s `omarchy-reminder show --json`).
* **Widgets de la barra Retro** (a la derecha, en Ajustes → Barra): `bar/omarchy/system-update` (SystemUpdate.qml; sólo se ve con algo pendiente; shims `omarchy-update-available` = paquetes de @world con `emerge --pretend`, flatpaks y commits nuevos de BWM; `omarchy-update` = terminal con `flatpak update` y `sudo emerge -avuDN @world`), `bar/omarchy/keyboard-layout` (KeyboardLayout.qml; sólo con varias distribuciones) y `bar/omarchy/media` (BarWidget + Service.qml de Omarchy, servicio en `OmarchyPlugins.firstPartyServiceFor("omarchy.media")`, IPC `media`; apagado por defecto porque ya está el plugin mpris: `shown` de `omarchy-plugins.json`, `bwm-plugin.sh show|hide`).
* **Dock:** `modules/ii/omarchyDock/` (Dock.qml, DockWindow.qml, DockModel.js de Omarchy; la cuadrícula es la de `omarchyMenu/omarchy/AppGrid.qml`) con anfitrión `OmarchyDock.qml` (biblioteca de apps de BWM, ajustes en `~/.config/bwm/dock.json`, ancladas por defecto Nautilus, Firefox, kitty, Vesktop, Spotify, Steam), sólo en Retro. Adaptado: BWM no tiene workspaces «flotantes», así que el shim `omarchy-hyprland-workspace-layout-current` dice `floating` si el workspace no tiene ventanas en mosaico y el dock relee los modos al abrir/cerrar/mover ventanas; los minimizados son los del workspace 99 de BWM y vuelven con `toggle-minimize.py restore`; `omarchy-dock` (shim) escribe `dock.json` (posición, autoocultar, anclar). `omarchy-hyprland-window-minimize` (Super+M) minimiza con `toggle-minimize.py` sólo donde se ve el dock, como Omarchy. Probado en un workspace vacío.

### 39. Dock de Omarchy opcional, idioma de Omarchy en Ajustes y fuera la página «Quick» (2026-10-26)
* **Dock duplicado:** el interruptor de Ajustes → Interfaz → Dock era el del dock propio de BWM (`dock.enable`), que salía además del de Omarchy. Ahora en Retro el de BWM no se carga (`IllogicalImpulseFamily.qml`: `dock.enable && !isRetro`) y ese apartado muestra sólo «Dock de Omarchy» (`dock.omarchy`, nuevo en `Config.qml`, **apagado por defecto**; `dock` es sección propia de cada estilo). Con el dock apagado, Super+Espacio y «Apps» usan la cuadrícula del menú y Super+M no hace nada (`omarchy-hyprland-window-minimize` mira si existe el IPC `omarchy.dock`).
* **Idioma de Omarchy:** Ajustes → Barra → «Idioma de los paneles de Omarchy» (sólo Retro): English / Español (México), escribe `~/.config/omarchy/language` (lo vigila `Commons/I18n.qml`, cambio en vivo). Puesto en inglés a petición del usuario.
* **Página «Quick» quitada** de `settings.qml` y `plasmaSettings.qml` («Ajustes rápidos»); `modules/settings/QuickConfig.qml` sigue en el repo sin usarse (fondo y colores, posición/estilo de la barra y esquinas de pantalla: también en sus páginas o en el selector de fondos).


### 40. Stremio Web sigue la paleta; diagnóstico visual de Steam (2026-10-26)
* **Problema real:** Stremio 1.2.2 Flatpak usa GTK4/libadwaita/WebKitGTK, no Qt; sólo se tematizaba el marco. Steam usa CEF: su barra ya mostraba Ethereal y el CSS instalado coincidía con el generado; lo que el usuario veía sin cambiar era la **Tienda web**, que Adwaita-for-Steam no cubre (tampoco Comunidad).
* **Stremio:** nueva plantilla `config/matugen/templates/stremio.css`, post_hook `scripts/stremio-theme.py` y overlay Retro `omarchy/overlays/stremio.css`. Default, Plasma y Retro (estático/dinámico) usan sus renderizadores existentes. El hook configura sólo `com.stremio.Stremio` cuando está instalado (véase §3.41): NODE_OPTIONS carga `stremio-theme.cjs`, BWM_STREMIO_CSS señala `~/.local/state/bwm/stremio/theme.css`, dos accesos de sólo lectura al directorio de scripts y de paleta.
* **Puente específico de Stremio Linux:** sólo en el Node del servidor oficial, añade un script al HTML de inicio de `web.stremio.com` que éste sirve por su proxy local; lee el CSS cada 2 s sin recargar la página. Conserva origen/sesión; no modifica el Flatpak, los vídeos, las API ni otros destinos del proxy. La primera vez reabre Stremio en su workspace salvo fullscreen/reproducción MPRIS; después no reinicia. El marco GTK cambia al abrir. El primer reinicio puede cambiar la posición en el mosaico (se observó en workspace 10).
* **Pruebas:** 7 tests HTTP en `scripts/tests/stremio-theme.test.cjs` (HTML normal/gzip/deflate/Brotli, errores, límite de tamaño, tráfico no afectado, CSS en vivo); compilación Python; 23 paletas Retro y Breeze renderizadas sin placeholders pendientes. Capturas recortadas verifican Ethereal → Tokyo Night → Ethereal con el mismo PID y sesión. Se restauró Ethereal. No se hizo un cambio global de estilo ni de wallpaper durante esta prueba.
* **Mantenimiento:** la ruta de inicio es específica de Stremio Linux actual; una actualización puede requerir adaptarla. Alcance, pruebas y desactivación en `docs/STREMIO_THEMING.md`. No presentar el tema GTK como soporte del contenido web ni afirmar que toda la Tienda de Steam está tematizada.


### 41. Integración opcional de Stremio en el instalador y prueba de la barra de Steam (2026-10-26)
* `stremio-theme.py` comprueba Flatpak y `flatpak info com.stremio.Stremio` antes de crear estado/overrides. `install.sh` ejecuta `--setup-only` tras generar la paleta, sin reiniciar apps. Al reaplicar Retro o Plasma se ejecuta el hook de Stremio aunque el CSS no cambie, para detectar una instalación posterior. Sin Stremio no se toca su configuración.
* 3 tests Python comprueban ausencia de Flatpak, ausencia de Stremio y setup sin reinicios; se mantienen los 7 tests HTTP del puente. Tema de Steam: se cambió sólo su CSS a Tokyo Night y se verificó visualmente el cambio de la barra superior tras reiniciar; después se restauró Ethereal. No confundir esta barra CEF con Qt.
* `steam-theme.sh` deja de reiniciar si falla el instalador y guarda los errores del reinicio en `~/.local/state/bwm/steam/restart.log` en vez de descartarlos; además espera al reinicio en el propio hook, sin un segundo lanzamiento desligado. No se afirma haber identificado la causa original del aviso del usuario.

### 42. Barra de Steam con el fondo base de Retro (2026-10-26)
* La captura del usuario mostró una diferencia real: el template compartido usaba `surface_container_high` (Ethereal `#131a3a`) mientras la barra del escritorio usa `background` (`#060b1e`). Las pruebas anteriores demostraban cambio de color, no coincidencia con el escritorio.
* Nuevo `omarchy/overlays/steam.css`, registrado en `MATUGEN_OVERLAYS`: `--adw-headerbar-bg` y su backdrop referencian `--adw-window-bg`. Sigue cualquier tema Retro estático/dinámico; Default y Plasma conservan su template compartido. Se aplicó a Steam y se reinició para cargarlo. Captura recortada verificada: color dominante de la barra `(6, 11, 30)` = `#060b1e`; captura temporal borrada.


### 43. Salvapantallas, ventanas y perfiles de la sesión (2026-10-26)
* `ScreensaverIdle.qml` importa `Quickshell.Services.Mpris` y calcula `mediaPlaying` con `Mpris.players.values.some(p => p.isPlaying)`: bloquea el temporizador automático durante la reproducción. Conserva el inicio manual y el cierre por actividad.
* La regla de renderizado sin foco incorpora las clases de Codex y ChatGPT. Virt-manager pasa de flotante a mosaico en JSON y Lua persistentes.
* Perfiles Default/Plasma: gestor de tareas btop mediante `bwm-terminal` y salvapantallas habilitado a los 5 min. El perfil activo incorpora `notifications.forceMonitor`. Se conserva también el estado generado de colores Ethereal, tema GTK `BWM-2` y bordes sin degradado inventado.
* Estos cambios ya estaban pendientes al pedir el usuario «commitea todo». Se revisan e incluyen expresamente, sin atribuir esta implementación a la sesión de mantenimiento ni afirmar una prueba funcional nueva.

### 44. Actualización de Gentoo y consolidación del contexto (2026-10-26)
* Diagnosticado el error de noticias mediante `eselect news list`, permisos de `/var/lib/gentoo/news` y el módulo local `/usr/share/eselect/modules/news.eselect`: fallaba al escribir el estado como usuario. Corregida la instrucción a `sudo eselect news read`.
* Revisado el diff de `/etc/portage/package.use/virt-manager` frente a `._cfg0001_virt-manager`: sólo añade `ffmpeg[x264]` requerido por `wf-recorder`; se indicó `u`. La ejecución y el final de la actualización siguen sin confirmar.
* `AGENTS.md` y `CLAUDE.md` sincronizados; ambos y `BWM_CONTEXT.md` pasan a Git por petición del usuario. Se actualizan estado actual, rutas, mantenimiento de Gentoo, limitaciones del actualizador y pendientes de `todo.md`. Los hashes del historial se conservan como referencias; para el estado actual se consulta Git.
* Validación previa al commit: compilación Python de `bwm_omarchy.py`; sintaxis Lua de `rules.lua`, `persistent_rules.lua` y `retro_colors.lua`; parseo de las 5 configuraciones JSON; renderizado de la plantilla Steam + overlay con las 23 paletas, sin placeholders pendientes y sin escribir ni reiniciar apps; `hyprctl configerrors` vacío. El log de Quickshell contiene recarga y no muestra `ReferenceError`, `TypeError`, tipos desconocidos ni errores de `ScreensaverIdle`; sí avisos de imágenes WebP y otros servicios. `qmllint` pasa la comprobación de sintaxis con avisos de imports `qs.*` no resueltos y accesos sin cualificar (se permitió su recuento de warnings); no acredita la resolución completa de tipos del proyecto. No se realizó una nueva prueba visual o de reproducción MPRIS.


### 45. Bandeja adaptable, multimedia tras la hora y gestor de temas/plugins (2026-10-27)
* **Petición:** eliminar el hueco de la bandeja al ocultar widgets, devolver multimedia a la derecha de la hora y gestionar temas/plugins de Omarchy desde Ajustes con buscador e instalación.
* **Barra:** `OmarchyPluginSlot` toma anchura cero cuando el widget está invisible (antes el teclado de una sola distribución, por ejemplo, mantenía su hueco). El ajuste por espacio disponible conserva las medidas y usa opacidad/recorte para no realimentar `item.visible` desde el padre. `centerEnd` limita el ancho de multimedia antes de los indicadores. `crmne.mpris` predeterminado y disposición del usuario migrados a `centerEnd`, conservando sus opciones; `enable --section` ya no las reinicia.
* **Página única:** `PluginsThemesConfig.qml` en `settings.qml` y `plasmaSettings.qml` (`SETTINGS_PAGE=plugins`): temas instalados con paleta y elección actual, filtros, plugins con activación/posición y retirada de los añadidos, búsqueda remota con Ver/Instalar, catálogo web e instalación por URL. Las listas antiguas salen de Estilo/Barra; los widgets fijos y el idioma permanecen en Barra. Navegación de Ajustes ampliada para que quepa el nombre.
* **Backend `bwm-addons.py`:** galería oficial de temas y JSON del marketplace, caché de una hora/fallback sin conexión, búsqueda por palabras y primeros 30 resultados. Instalación de temas en `~/.local/share/bwm/omarchy-themes`; plugins mediante `bwm-plugin.sh` con staging, validación de manifest/entradas/imports y detección de id duplicado. Formatos admitidos: temas con colors.toml y plugins de barra/servicios; no reemplazos de otras partes del shell. Sin hooks de instalación ni sudo. La validación no certifica cada dependencia o comportamiento de un plugin externo.
* **Trampa encontrada:** `~/.config/omarchy/themes` es un symlink al repo. El catálogo lo deduplica, mantiene los incluidos como tales y reconoce las carpetas de usuario en `theme_directory()`, motor de colores, shims y carrusel. Los temas sin preview reciben miniatura del fondo o paleta. No se instaló ningún tema/plugin externo elegido al azar en la sesión real.
* **Servicios:** `syncServices()` sólo carga servicios ajenos activados, además de los preinstalados no deshabilitados.
* **Verificado:** 13 pruebas unitarias (formato, rutas, imports, caché, listado/resolución con symlink, instalación y posición sin perder opciones); compilación Python y sintaxis bash; carga real de la página en workspace 9 y prueba QML aislada sin ventana: búsqueda de temas «tokyo» = 2 resultados, plugins «mpris» = 46, posición de multimedia = centerEnd. Carrusel con 24 filas (23 incluidos + dinámica). Reinicio único de la barra mediante el gestor, captura recortada con bandeja compacta y multimedia tras la hora. No se inició otra instancia `qs -c ii`. Documentación en `docs/OMARCHY_ADDONS.md`.


### 46. About de BWM, eliminación de Advanced y separación de Temas/Plugins (2026-10-27)
* **Petición:** autodetectar distro y su imagen/nombre; quitar sus cuatro botones de ayuda; sustituir Dotfiles/illogical-impulse por WM/BWM, logo y remotos propios; enlazar documentación/issues/discusiones reales, retirar Donate, añadir Star con GIF; eliminar Advanced y separar/mejorar Plugins y Temas.
* **About:** tarjetas Distro/WM, logo BWM existente (`hypr/omarchy/boot/logo.png`) y GIF local `assets/bwm-star.gif` (32 fotogramas, bucle). GitLab/GitHub coinciden con los remotos del repo. Documentation → GitLab README.es.md; Issues → GitHub /issues (API has_issues=true). Sin Discussions, comprobado has_discussions=false mediante API pública; no se activaron funciones remotas ni se dio ninguna estrella.
* **Distro:** Gentoo usa NAME/ID/PRETTY_NAME entre comillas simples; el lector antiguo sólo reconocía comillas dobles. Nuevo `SystemInfoData.js` puro, sin evaluar shell, con parser de variantes y selección por ID/ID_LIKE. Servicio actualizado en FileView.onLoaded, fallback /usr/lib/os-release y icono incluido; `ColorOverlay` tiñe SVG negros (MultiEffect.colorization no los aclaraba). About muestra «Gentoo Linux», versión, Hyprland y Wayland.
* **Navegación:** `AdvancedConfig.qml` retirado con todas sus entradas. `PluginsConfig.qml` y `ThemesConfig.qml` abren páginas independientes en las dos apps; el antiguo combinado deja de existir. `addons/AddonPage.qml` comparte estructura, `AddonManager.qml` el transporte/estado, `AddonBrowser.qml` la búsqueda. **Necesario:** un `qmldir` con exports explícitos para importar esta carpeta nueva; sin él Quickshell dice que el módulo no está instalado.
* **Mejoras:** Temas con cuadrícula de miniaturas, paletas, elección activa y paleta del fondo; Plugins con tarjetas, versión/origen, interruptor, posición y filtros Todos/Activados/Desactivados; nombres/descripciones de los preinstalados en español, conservando el texto original en el catálogo. Ambas páginas con Instalados/Descubrir, instalación por URL y feedback. Backend discover añade --offset y nextOffset para Mostrar más, sin perder resultados tras los primeros 30.
* **Verificado:** 14 tests Python incluidos límites de paginación 30/30/5; sintaxis Python/QML; prueba aislada Quickshell de parser (comillas simples/dobles, sin comillas e ID_LIKE), detección real Gentoo Linux/id=gentoo y 32 frames del GIF. Carga de las 3 páginas: 23 temas, 6 plugins/1 activo, 2 resultados «tokyo» y 46 «mpris», cargados de 30 a 46 sin duplicados; filtro de activos = 1. Carga de Temas en plasmaSettings con regla temporal al workspace 9. Revisión visual de About, Temas y Plugins; corregidos icono negro y contraste de selección. Se conservan avisos previos de WebP/portal/traducción y Revealer. Sin segunda instancia qs -c ii, sin cambios de estilo y sin aplicar temas/plugins durante estas pruebas.


### 47. About de Omarchy con Fastfetch real, sólo en el menú Retro (2026-10-27)
* **Petición y alcance aclarado:** About idéntico al de Omarchy, basado en Fastfetch. A la pregunta de si también en Settings, el usuario respondió «Solo en el menú Retro». No se modificó `modules/settings/About.qml` en esta tarea.
* **Origen:** Omarchy `b8706a3f9eb185f56b61c6141561deba652beddf` (MIT): `icon.txt` y `bin/omarchy-branding-about-animation` copiados sin cambios; configuración de `/etc/fastfetch/config.jsonc` y lanzador portados a `hypr/omarchy/about/` y `omarchy-shims/omarchy-launch-about`. README y licencia incluidos. Conserva ASCII de 54×26, padding, cajas/orden/colores, glint animado, autoajuste por celdas y cierre con una tecla. La segunda invocación enfoca la ventana existente.
* **Integración:** «Acerca de» de `bwm-menu.jsonc` usa el nuevo shim, enlazado en `~/.local/bin` por catalog. Nueva regla `omarchy-about` para `org.omarchy.about`, flotante y centrada. El tamaño ajustado se guarda en `~/.local/state/bwm/omarchy/about.fit`; configuración sólo en repo y `$XDG_RUNTIME_DIR/bwm`, sin tocar /etc/fastfetch ni la configuración personal de Fastfetch.
* **Gentoo/BWM:** `bwm-about-data.py` da host (DMI o hostname), rama/revisión, estilo, tema, edad/uptime y fecha del último BUILD_TIME de Portage. El resto sale de Fastfetch. No inventa versión de Omarchy ni fecha de actualización completa. Fastfetch detectaba el binario instalado de Hyprland como 0.56.2, pero `hyprctl version -j` confirma sesión 0.55.4/a0136d8c: el campo WM se consulta por IPC para reflejar lo que corre realmente. No se reinició el compositor ni se tocaron plugins.
* **Trampa de tamaño (causa identificada y corregida en §3.48: caché de Kitty):** el terminal de About se mapeaba maximizado (fullscreen=1); la regla fullscreen=false no bastaba y Hyprland rechazaba redimensionarlo. El lanzador deshace los modos 1/0 sólo de su ventana antes de medir y usa `relative=false` en resize. Eliminado fallback que habría centrado la ventana activa en vez de la dirección de About. Se comprobó el tamaño 877×640, fullscreen=0 y un solo PID tras reabrir.
* **Verificado:** 6 tests de metadatos (duración, fecha desconocida, checkout ausente, WM en ejecución, host sin DMI, tema dinámico); Python compilado, bash -n de lanzador/animación, Lua y JSONC válidos, configerrors vacío. Fastfetch 2.65.2 procesa el diseño. Prueba gráfica con logo, las tres cajas y fuente Kitty; cierre por tecla y reapertura ajustada/enfoque sin duplicar. Capturas temporales recortadas a About y eliminadas después.

---

### 48. Terminales y otras apps sin maximizado automático (2026-10-27)
* **Causa comprobada:** `~/.cache/kitty/main.json` guardaba `window-state: maximized`. Kitty recuerda por defecto tanto tamaño como estado de ventana. En la versión instalada, `--start-as normal` también consulta la caché; no basta como solución. Era maximizado (Hyprland `fullscreen=1`), no fullscreen real (`2`).
* **Corrección:** `config/kitty/kitty.conf` establece `remember_window_size no`; `modules/rules.lua` activa la regla global recomendada `suppress_event = "maximize"`. Evita que cualquier app restaure/pida maximizado, incluidos sus botones CSD; se usan los dispatchers/atajos del compositor para maximizar. No suprime fullscreen, para conservar juegos/vídeo, ni bloquea maximizado manual del compositor. No se borró la caché ni se alteraron ventanas existentes.
* **Aplicación y pruebas reales:** recarga de Hyprland sin errores. Tres Kitty nuevas en workspace 9 silent: inicio normal → 0, petición explícita maximizado → 0, fullscreen explícito → 2. Sobre la segunda, dispatcher manual mode=1 → 1. App Qt independiente con `showMaximized()` → 0. Ventanas identificadas por PID; procesos, archivo QML y reglas temporales eliminados. Configuración recargada también en Kitty existente. Sin reiniciar compositor/Quickshell ni tocar plugins.

### 49. Luz nocturna del panel de pantallas que sí funciona (2026-10-27)
* **Causa comprobada:** `ToggleSwitch` emite `toggled()` sin argumento; `toggleNightlight(on)` asignaba `undefined` a un `bool`, QML lanzaba «Cannot assign [undefined] to bool» (en `qs -c ii log`) y el comando nunca se ejecutaba. Además el indicador 󰔎 de la barra Retro miraba el servicio `Hyprsunset` de end-4 (hyprsunset no está instalado), el estado y el shader se escribían en `~/.config/hypr` (el repo) y cualquier `hyprctl reload` o inicio de sesión perdía el shader.
* **Arreglo:** el panel invierte su estado y llama a `omarchy-toggle-nightlight --on|--off`. `nightlight.py`: estado en `~/.local/state/bwm/nightlight.json` (migra y borra el antiguo del repo), backend hyprsunset si existe (`hyprctl hyprsunset temperature N` / `identity`, arrancando el daemon, como Omarchy) y si no shader GLSL 300 es en `~/.local/state/bwm/nightlight.frag`, que sólo existe encendido; `--status` incluye `backend`; `--apply` en `autostart.sh`. `modules/nightlight.lua` pone el shader si existe el archivo. El indicador lee el JSON con `FileView` y usa el mismo shim, igual que el menú.
* **Verificado:** con el backend shader (hyprsunset ausente), muestreo de 4×4 px con grim: encendido 4000 K y 3000 K reducen el azul, sigue tras `hyprctl reload`, apagado y apagado+reload vuelven al color sin tinte; `configerrors` vacío; reinicio de Quickshell con el gestor y sin errores del panel/indicador en el log. **No probado:** clic real en el interruptor/deslizador del panel ni el indicador a la vista; backend hyprsunset (instalable con `sudo emerge gui-apps/hyprsunset`, overlay hyproverlay). Default sigue con su servicio `Hyprsunset` propio.

---

### 50. Consolidación de todos los cambios y publicación solicitada (2026-10-27)
* El usuario pide commitear todo y subirlo a los remotos. Se incluyen deliberadamente cambios de esta conversación y concurrentes: About BWM/Fastfetch, separación de Temas/Plugins y catálogo, barra adaptable, maximizado, luz nocturna, perfiles generados y virt-manager flotante. No se descartan cambios ajenos.
* Verificación previa: 20 pruebas de About/complementos correctas; sintaxis de 6 Python, 8 Bash y 4 Lua; 3 JSON válidos; AGENTS/CLAUDE idénticos, `git diff --check` y `hyprctl configerrors` sin errores. Esta tarea no repite pruebas gráficas ni prueba juegos reales. Publicación mediante `git push origin main` y comprobación de `refs/heads/main` de GitLab/GitHub; el resultado se informa tras ejecutarlo.

---

## 4. 📂 Estructura del repositorio

```
hyprland-de/
├── assets/
│   ├── fonts/ cursors/ wallpapers/ screenshots/
│   └── skin-previews/                 # Capturas de lo que imita cada estilo (end-4, KDE Plasma 6.8) + README
├── config/                            # Enlazado desde ~/.config
│   ├── hypr/
│   │   ├── hyprland.lua               # Raíz: importa modules/*
│   │   ├── keybinds.json              # Atajos (fuente de verdad) → keybinds-manager.py → modules/user_binds.lua
│   │   ├── modules/                   # appearance, autostart, binds, colors (generado), monitors (desc:),
│   │   │                              # omarchy_windows, plasma_colors/retro_colors (generados), rules,
│   │   │                              # persistent_rules (Alt+Q), theme, user_binds (generado), glass…
│   │   ├── omarchy/
│   │   │   ├── bwm-menu.jsonc         # Catálogo del menú de Retro
│   │   │   ├── themes/                # 23 temas de Omarchy (colors.toml, fondos, preview.png, neovim.lua…)
│   │   │   ├── themed/                # Plantillas de apps de Omarchy (+ vesktop propia) + README
│   │   │   ├── overlays/              # Capas TUI (GTK, Firefox, swaync, Stremio, Steam…)
│   │   │   ├── applications/          # Apps sólo-Retro (.desktop)
│   │   │   └── boot/                  # Temas Plymouth/SDDM de Omarchy con logo BWM
│   │   ├── plugins/                   # hyprbars(-plasma).so — desplegar SÓLO con make install
│   │   └── scripts/
│   │       ├── bwm-theme-manager.py   # Gestor de estilos
│   │       ├── bwm_omarchy.py         # Motor de Retro: paletas, apps, Vesktop, Firefox/Steam (restart_app)
│   │       ├── bwm-addons.py          # Catálogos e instalación de temas/plugins de Omarchy
│   │       ├── bwm_omarchy_apps.py    # Plantillas de apps de Omarchy y su aplicación/restauración
│   │       ├── bwm_icons.py           # Iconos por estilo, qt6ct, kdeglobals, overrides de flatpak
│   │       ├── gtk-theme.py           # Tema GTK 3 BWM-1/BWM-2 con recarga en vivo
│   │       ├── stremio-theme.py/.cjs  # Tema de la web Stremio Linux Flatpak (opcional)
│   │       ├── steam-theme.sh         # Instala Adwaita-for-Steam y espera al reinicio
│   │       ├── kitty-recolor.sh       # Recolorea kitty en vivo
│   │       ├── window-guard.py        # Juegos/ventanas fuera de pantalla + primary de XWayland
│   │       ├── xwayland-primary.py    # RandR primary por ctypes
│   │       ├── skin-switcher.sh       # Filas del carrusel de estilos
│   │       ├── app-launcher.sh        # Lanzador según estilo (`apps` = cuadrícula)
│   │       ├── set-wallpaper.sh, theme-picker.sh, quick-tile.py, toggle-minimize.py, keybinds-manager.py,
│   │       │   monitor-manager.py, nightlight.py, reload-spotify.py, install-boot-theme.sh,
│   │       │   bwm_boot.py, bwm-plugin.sh, default-apps.py, bwm-terminal, font-set.sh, glass.sh…
│   │       └── omarchy-shims/         # Sustitutos de comandos omarchy-* (→ ~/.local/bin)
│   ├── quickshell/ii/
│   │   ├── shell.qml, settings.qml, plasmaSettings.qml
│   │   ├── Commons/ Ui/               # Librerías de Omarchy (qs.Commons, qs.Ui), i18n en/es-MX
│   │   ├── omarchy-plugins/           # Plugins de barra de Omarchy preinstalados
│   │   ├── panelFamilies/IllogicalImpulseFamily.qml   # Qué se carga en cada estilo
│   │   ├── services/                  # Audio, Notifications, PolkitService, AppSearch…
│   │   └── modules/
│   │       ├── ii/bar/RetroBarContent.qml, bar/omarchy/*   # Barra Retro y sus widgets/paneles
│   │       ├── ii/omarchyMenu/ omarchyDock/ omarchyOsd/ omarchyPolkit/ omarchyNotifications/
│   │       ├── ii/plasma*/            # Kickoff, applets, menú de tareas, selector, calendario…
│   │       ├── ii/altTab/ lock/ onScreenDisplay/ screensaver/ screenshotPreview/ sidebarRight/…
│   │       └── settings/              # Páginas de Ajustes (BarConfig, InterfaceConfig, StyleConfig…)
│   ├── nvim/                          # LazyVim de BWM (Retro), temas y recarga en vivo
│   ├── matugen/                       # config.toml + plantillas (GTK, Vesktop, Qt, Steam, kitty…)
│   ├── gtk-3.0/ gtk-4.0/ kitty/ rofi/ swaync/ btop/ firefox/ spicetify/ xdg-desktop-portal/
│   └── illogical-impulse/             # config.json activo + perfiles por estilo
├── src/hyprbars/ src/csd-minimize/    # Plugins C++ (-fno-gnu-unique, make install)
├── docs/OMARCHY_INVESTIGACION.md      # Investigación de Omarchy
├── install.sh, README.md, README.es.md
└── AGENTS.md, CLAUDE.md, BWM_CONTEXT.md # Reglas sincronizadas y contexto versionados
```

---

## 5. ⚙️ Cambios hechos en el sistema (fuera del repo)

* **Plugins de Hyprland** compilados con `-fno-gnu-unique` (pixman, libdrm, hyprland, libinput, udev, wayland-server, xkbcommon, lua5.4) e instalados en `config/hypr/plugins/` con `make install`.
* **Arranque/login** (con sudo, por el usuario): `install-boot-theme.sh --all` (SDDM con Hyprland mínimo, servicio `bwm-boot-theme.path`, `/usr/local/sbin/bwm-boot-theme`), Plymouth opcional. `grub.cfg` sólo parcheado, nunca regenerado.
* **`~/.local/bin`**: enlaces a `omarchy-shims/*` (`bwm-plugin.sh catalog`), binario `ai-usagebar` (cargo).
* **Flatpak**: overrides globales de usuario (sólo lectura a temas GTK, `kdeglobals`, `qt6ct`, iconos, `~/.themes`, `~/Projects/hyprland-de/config`; `QT_QPA_PLATFORMTHEME=kde`); Vesktop con `enabledThemes = ["bwm.theme.css"]`.
* **Enlaces**: `~/.config/nvim` → `config/nvim`, `~/.themes` → `~/.local/share/themes`, `~/.local/state/omarchy/current/theme` → `~/.local/state/bwm/omarchy/theme`.
* **Generados en `$HOME`**: temas GTK `~/.local/share/themes/BWM-1|BWM-2`, `~/.config/kdeglobals` (marcado `[BWM]`), configs creadas para apps no instaladas (alacritty, ghostty, foot, helix, tmux, VS Code, Cursor, pi, Hermes, T3, fcitx5), `~/.claude/themes/omarchy.json` y `settings.json` con `custom:omarchy` en Retro (se restaura al salir: `~/.local/state/bwm/omarchy/app-restore.json`), extensión «Omarchy» en `~/.vscode-oss/extensions`.
* **Fuentes**: JetBrainsMono Nerd Font en todos los pesos (`~/.local/share/fonts`).
* **Stremio Flatpak:** override por app NODE_OPTIONS/BWM_STREMIO_CSS y acceso de sólo lectura a los scripts y `~/.local/state/bwm/stremio` (véase §3.40).
* **Adwaita-for-Steam** en `~/.local/share/steam-adwaita` (parchea `steamui`).
* **Procesos de sesión**: `window-guard.py watch`, `hyprpolkitagent` (sólo fuera de Retro), swaync (sólo fuera de Retro), recordatorios como temporizadores `systemd --user` (`omarchy-reminder-*`).

---

## 6. 🔀 Git

* Rama `main`; `git push origin main` sube a GitLab y GitHub. El estado del árbol de trabajo cambia solo (archivos generados): consúltalo con `git status`, no lo apuntes aquí.
* Consultar `git status --short --branch` y `git log -1 --oneline` para saber el commit y los cambios actuales. El usuario pidió el 2026-10-27 commitear todos los cambios y subirlos a ambos remotos. Comprobar el resultado del push mediante los hashes remotos; no inferirlo de un commit local.
* `AGENTS.md` y `CLAUDE.md` deben ser idénticos; ambos y este contexto están versionados. No añadir secretos ni volcados privados. Los archivos generados sólo se incluyen de forma deliberada (como en esta petición de «todo»).

| Commit | Qué |
| :--- | :--- |
| `f02eeb6` | Stremio web opcional, integración en instalador y espera del reinicio de Steam |
| `90df2d9` | Retro: cuadrícula Apps, dock, OSD, polkit, recordatorios y widgets de Omarchy; idioma; fuera «Quick» |
| `62b9bdd` | Steam se reinicia en su sitio al cambiar sus colores |
| `d26dc97` | GTK y Qt siguen al estilo/tema, GTK 3 en vivo, flatpaks |
| `0007d16` | Todas las plantillas de apps de Omarchy, LazyVim, kitty/Vesktop en vivo, capturas del selector |
| `e11135a` | Juegos a pantalla completa, Vesktop/Firefox TUI, estilos vs temas |
| `fc06051` | Barra de Omarchy, temas claros en apps, aspecto del menú |
| `7d5aa03` | Alt+R abre y aplica temas |
| `bdfbf9b` | 23 temas estáticos, carrusel 3D, portapapeles y emojis |
| `77acb80` | Notificaciones de Omarchy en Retro |
| `380746a` | Capturas de Omarchy (texto, QR, grabación) en el menú |
| `fd1c1fa` | Menú / paleta de comandos de Omarchy |
| `7e1273f` | Paneles de Omarchy, luz nocturna nativa, proporción de ventana única |
| `4aa7d42` | Plugins del shell de Omarchy, indicadores, workspace mágico, capturas omasnap |
| `0a177b2` | SDDM de Omarchy |
| `9d1a436` | Monitores por descripción, Plymouth opcional y reversible |
| `f5e46a4` | Salvapantallas, glass, fuentes, iconos, Qt, tema de arranque |
| `cb15a89` | Apps con estilo Omarchy que siguen al fondo |
| `9105abc` | Plasma: un tema oscuro Breeze para GTK, Qt y apps |

---

## 7. 🚀 Guía rápida

**Arranque de una sesión nueva:** lee `AGENTS.md` o `CLAUDE.md` (mismas reglas) y §2 de este documento; para un área
concreta, busca su sección en §3.

```bash
hyprctl reload; hyprctl configerrors                       # Hyprland
python3 ~/.config/hypr/scripts/bwm-theme-manager.py get    # estilo activo
python3 ~/.config/hypr/scripts/bwm-theme-manager.py set retro   # reinicia Quickshell (~10 s)
qs -c ii log | tail -50                                    # log de la instancia real
qs -c ii ipc show                                          # objetivos IPC (un panel que no carga desaparece)
omarchy-theme-list; omarchy-theme-set tokyo-night; omarchy-theme-current   # temas de Retro
~/.config/hypr/scripts/bwm-plugin.sh list                  # plugins de la barra Retro
hyprctl hyprbars-csd                                       # qué ventanas llevan barra (Plasma)
~/.config/hypr/scripts/xwayland-primary.py status          # primary de XWayland
cd src/hyprbars && make clean && make && make install      # plugin (cargará al reiniciar sesión)
git status; git log --oneline -5; git push origin main
```

**Puntos críticos:**
* Plugins C++: `-fno-gnu-unique` y sólo `make install`; nunca `cp` sobre un `.so` cargado ni `hyprctl plugin unload/load` (SIGBUS, safe mode).
* Quickshell una sola vez (`qs -c ii`); reinicios con `bwm-theme-manager.py set <estilo>`. Los widgets cargados por `Loader` desde `bar/omarchy/*`, overlays y archivos nuevos de un módulo no se recargan en caliente: reinicia.
* Hyprland 0.55 en Lua: `hyprctl dispatch 'hl.dsp.…'`; para inyectar atajos `hyprctl eval 'return hl.dispatch(hl.dsp.send_shortcut({…}))'`.
* Archivos que otras apps vigilan por inodo (Vesktop) se escriben en el sitio; los que se vigilan por carpeta (qt6ct) o se reemplazan (resto) con `os.replace`.
* Polkit y `org.freedesktop.Notifications` admiten un solo dueño: en Retro los tiene Quickshell (Omarchy), fuera `hyprpolkitagent`/swaync o BWM.
* Retro estático: cambiar el fondo no cambia la paleta.
* Puede haber otra sesión de IA en el repo: commits sólo con tus archivos, salvo petición explícita de incluir todo; revisa cada diff.
* Mantenimiento de Gentoo: §2.7. Usar `sudo eselect news read`, revisar cada configuración y no dar por terminada la actualización sin evidencia.
