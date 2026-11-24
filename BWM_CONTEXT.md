# 📘 BWM (Better Window Manager) — documento de contexto

> **Para qué sirve:** memoria completa del proyecto para retomarlo en cualquier sesión de IA o
> terminal: qué hay ahora (§2), cómo se llegó ahí (§3), dónde está cada cosa (§4), qué se tocó
> fuera del repo (§5), git (§6) y cómo trabajar (§7). `AGENTS.md` y `CLAUDE.md` son el resumen corto
> con las mismas reglas; este archivo es el detalle. Los tres están versionados.
>
> **Cómo leerlo:** §2 es la verdad actual. El historial de §3 es cronológico y conserva lo que se
> hizo en cada momento: cuando algo quedó superado lo indica con **⚠️ Superado en parte por §3.N**.
> Fechas en formato AAAA-MM-DD. Última revisión: 2026-11-10. Estado de Git: consulta §6; no uses los hashes históricos como estado actual.
> Registra las pruebas realizadas y sus límites; una instrucción dada al usuario no confirma su ejecución.

**Vocabulario:** **estilo** (*skin*) = default (end-4), Retro, KDE Plasma. **Tema** = lo que hay dentro de
un estilo (los 23 temas de Omarchy en Retro o su paleta dinámica). Los nombres internos siguen con
«theme» (`bwm-theme-manager.py`, `theme.lua`, `Appearance.isRetro`…).

---

## 1. 🖥️ Qué es, máquina y rutas

**BWM** es un gestor de ventanas que trata de encapsular todos los gestores de ventanas y escritorios
como **skins**: cada una reproduce otro escritorio (barra, menús, paneles, atajos, decoraciones y temas)
y todo el sistema la sigue. **Finalidad: compatibilidad con las mejoras de aspecto de cada original**
(un tema de Plasma de internet debe funcionar en la skin Breeze (Kde plasma); uno de Omarchy, en Retro). Pocas
interfaces propias (bienvenida, Ajustes); el resto es la del original. Detalle: `docs/SKINS.md`.

Corre sobre **Hyprland ≥ 0.55 configurado en Lua** (desarrollado en `v0.55.4`/`a0136d8c`; la sesión
del 2026-10-28 ya corre `v0.56.2`/`efb50993`, comprobado con `hyprctl version -j`) y **Quickshell** (Qt 6/QML; config `ii`, derivada de
end-4/illogical-impulse), con tres estilos que cambian todo el escritorio y las apps.

| | |
| :--- | :--- |
| Usuario | `sasel` (git `saselandia`, habla español) |
| Sistema | Gentoo `x86_64`, kernel `7.2.5-cachyos`, systemd (sesión de usuario) |
| Hardware | Ryzen 9 7900 (iGPU AMD) + GPU NVIDIA |
| Monitores | LG UltraFine 4K arriba a la derecha (`2560x0`, 60 Hz) y MSI MAG 274Q 1440p@240 principal (`0x720`), desde 2026-11-04 (antes HP X24ih 1080p@144 en `0x1080`; las secciones antiguas de §3 hablan del HP). **Siempre por `desc:`**, nunca `DP-N` |
| Terminal | kitty (control remoto `listen_on unix:@kitty`) |
| Inicio de sesión | SDDM con tema de Omarchy en un Hyprland mínimo, entra solo en todas las skins; la contraseña la pide el bloqueo de la skin activa (§3.97) |
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
* **Nombres visibles (§3.70):** `default (end-4)`, `Retro`, `Breeze (Kde plasma)`; ids y rutas siguen siendo `default`, `retro`, `plasma`. Los nombres de los escritorios originales se conservan al hablar de su procedencia.
* **Cambio de fondo de default (end-4) (§3.70):** `matugen-fast.py` publica la paleta sin hooks bloqueantes y después ejecuta los hooks de apps en un trabajador separado, sin reiniciar apps. Peticiones serializadas, se descartan las intermedias pendientes; Kitty sólo recibe la paleta del motor original. Última medición del aplicador completo: 1,08 s al reaplicar el fondo actual (no es una medida de todas las apps ni de una transición visual entre dos fondos diferentes).
* Gestor: `config/hypr/scripts/bwm-theme-manager.py get|set|toggle|list <estilo>`. Al cambiar: perfil de Quickshell por estilo (`illogical-impulse/config-<estilo>.json`, secciones propias en `THEME_SPECIFIC_SECTIONS`), colores de Hyprland, plugins (hyprbars sólo en Plasma), iconos, GTK/Qt, apps, recarga de paneles por IPC `bwmSkin.reload` conservando Quickshell (candado `/tmp/bwm-theme-manager.lock`), swaync sólo en default (`notifications` de `skin.json`; §351), `hyprpolkitagent` fuera de Retro, las apps permanecen abiertas durante el cambio de skin (§3.57).
* Selector de estilos: Alt+T (Retro: carrusel 3D con capturas de lo que imita cada estilo, `skin-switcher.sh`; default (end-4): rofi; Plasma: «Estilo global»). Temas de Retro: Alt+R (carrusel, sólo existe en Retro: campo `skins` de `keybinds.json`; caché estable de miniaturas JPG como Omarchy, §3.71), menú → Estilo → Temas → Elegir tema; catálogo en Estilo → Temas → Catálogo.
* **Temas y Plugins:** Retro los integra como listas del menú (§3.136): carrusel nativo de temas y Catálogo; Plugins → Instalados, Catálogo, Clonar y Quitar. Breeze conserva las páginas `ThemesConfig.qml`/`PluginsConfig.qml` con miniaturas, filtros, búsqueda remota y Git/URL; default (end-4) no las muestra. Comparten el motor `bwm-addons.py` y los formatos originales. Guía: `docs/OMARCHY_ADDONS.md`.
* Temas de comunidad en `~/.local/share/bwm/omarchy-themes` (`XDG_DATA_HOME`); también se reconoce `~/.config/omarchy/themes`, que aquí enlaza al repo y no se usa como destino de instalación. `theme_directory()` y `list_omarchy_themes()` comparten precedencia, igual que la CLI y el carrusel.
* **Animaciones por skin (§3.94):** `config/hypr/skins/<id>/hypr/animations.lua` (default (end-4) = dots-hyprland, Retro = Omarchy, Breeze = las MD3 anteriores). El fondo lo pinta el shell como en el original: `Background.qml` de end-4 en default (cambio directo, sin la transición «grow» de swww) y el plugin background de Omarchy en Retro (`modules/ii/omarchyBackground`, revelación diagonal de 840 ms); swww queda debajo sin animación. Breeze sigue con swww.
* **Intros de fondo (Retro, §3.116):** un fondo fijo con `backgrounds/intros/<nombre>.<ext>` la reproduce con OWE al elegirlo (también al cambiar de tema) y al entrar, una vez por sesión tras desbloquear; se apaga en el menú → Estilo → Intros de fondo (`omarchy-theme-bg-intro`) o con las animaciones apagadas.
* **Selectores de fondos:** todas las skins sólo toman `~/Pictures/Wallpapers` (§311). default (end-4) (§3.93): el de end-4 (`modules/ii/wallpaperSelector`, confinado a esa carpeta) con Alt+W, Ctrl+Super+T y Ctrl+Super+Alt+T (aleatorio de la carpeta); aplica con `switchwall.sh`. Retro (§3.111): carrusel original de Omarchy con Alt+W; backend `skins/retro/scripts/wallpaper-picker.py`. Breeze conserva el rofi de `wallpaper-picker.sh`.
* **default (end-4): selección de colores de end-4 (§3.69)**: `set-wallpaper.sh` llama a `switchwall.sh --colors-only`; respeta `appearance.palette.type`, preferencia claro/oscuro de GSettings y `enableAppsAndShell`. El clasificador automático y el generador de terminal son los originales; dependencias aisladas en `~/.local/share/bwm/default-colors-venv`, preparadas por el instalador.
* **Tema por defecto de cada skin:** default (end-4) = Material You **dinámico** (matugen desde el fondo); Retro = paleta **dinámica** en formato Omarchy (23 temas **estáticos** con Alt+R); Plasma = el tema de Plasma activo, **estático** (Breeze Oscuro de entrada; §3.139). Cada skin en su carpeta `config/hypr/skins/<id>/skin.json` (§2.9, §3.59).
* Retro estático/dinámico: `~/.local/state/bwm/omarchy/{theme.mode,theme.name,colors.toml,shell.toml}`; en estático cambiar el fondo no toca la paleta. Temas claros (White, Catppuccin Latte…) ponen las apps en claro.

### 2.2 Apps tematizadas
| App | default (end-4) | Plasma | Retro | ¿En vivo? |
| :--- | :--- | :--- | :--- | :--- |
| GTK 3 | matugen → `gtk-3.0/bwm-colors.css` | Breeze | Omarchy + capa TUI | Sí: tema `BWM-1/BWM-2` alternado (`gtk-theme.py`) |
| GTK 4 / libadwaita | `gtk-4.0/gtk.css` | Breeze | Libadwaita nativo como Omarchy; admite `gtk.css` del tema (§3.319) | Al abrir; no se reinició Nautilus en §3.319 |
| Qt nativo | qt6ct `colors/bwm.conf`; con plasma-integration, kdeglobals de kde-material-you-colors como end-4 (§3.79) | Breeze | con `qtbase[gtk]`, paleta del tema GTK como Omarchy (`gtk3`, §3.80); si no, qt6ct + fuente mono | default con KDE y Retro con gtk3: sí; qt6ct: al abrir |
| KDE / Qt en flatpak | `~/.config/kdeglobals` (de bwm.conf) + overrides flatpak | igual | igual | Al abrir |
| kitty | matugen | Breeze | plantilla de Omarchy | Sí (`kitty-recolor.sh`, control remoto) |
| foot, alacritty, ghostty, helix, neovim, tmux, VS Code/VSCodium/Cursor, Claude Code, pi, Hermes, T3, fcitx5, Obsidian | — | — | plantillas de Omarchy (`bwm_omarchy_apps.py`), también sin instalar | foot/ghostty/helix/neovim/tmux sí |
| Neovim | — | — | LazyVim de BWM (`config/nvim`), todos los temas instalados | Sí (`bwm-theme-hotreload.lua`) |
| Vesktop | `themes/bwm.theme.css` «BWM Material You» | «BWM Breeze Dark» | «BWM Omarchy TUI» | Sí (escrito en el mismo inodo) |
| Firefox | userChrome + Pywalfox | igual | + capa TUI | Colores en vivo, sin reiniciar (Pywalfox, variables de Firefox 13x+, §3.82–3.83); la forma de la capa TUI (fuente mono, esquinas) con un reinicio automático al entrar o salir de Retro (§3.85) |
| Spotify | Spicetify MaterialYou | Breeze | `BWM-Omarchy` | Reinicio automático en su sitio |
| Steam (cliente/biblioteca, no Tienda/Comunidad web) | Adwaita-for-Steam `bwm` + barra inferior (`steam-custom.css`) | igual | + esquinas rectas, mono y barra con fondo base (`overlays/steam.css`) | Reinicio automático al acabar el cambio de tema (no en cambios de skin ni con un juego abierto; vuelve a la bandeja si estaba ahí), §3.82, §3.339 |
| btop, swaync, rofi, Pywalfox, iconos (`icons.theme` o Adwaita en Retro, §3.319) | sí | sí | sí | — |
| Stremio Linux Flatpak | paleta matugen | Breeze | paleta Omarchy + TUI | Web en vivo mediante `stremio-theme.cjs`; marco GTK al abrir |
| Omacalc (§3.112) | paleta dinámica matugen/end-4 | Breeze | colores nativos del tema estático o dinámico | Sí, sin reiniciar ni perder el cálculo (`matugen/templates/omacalc-colors.toml`) |

### 2.3 Retro = Omarchy (Quickshell)
* **Nautilus (§3.308, §3.318):** extensiones originales de Omarchy LocalSend y Transcode enlazadas por el instalador y al activar Retro. LocalSend admite binario nativo o Flatpak sin excepción si falta la app; Transcode entrega el PATH de los shims a sus hijos incluso con activación D-Bus. En este equipo están instalados nautilus-python, Sushi, ffmpegthumbnailer y LocalSend Flatpak 1.18.2; comprobadas las entradas con las APIs GI reales, pendiente la interacción visual/envío. `bwm check` reconoce también LocalSend Flatpak.
* **Aspecto/apertura de Nautilus (§3.319):** GTK4 conserva Libadwaita nativo, sin Material You ni la capa TUI de BWM. `icons.theme` se respeta si está instalado, con Adwaita de respaldo como quattro actual; Yaru 25.10.3 instalado sin root para los temas incluidos antiguos (ahora `Yaru-yellow`). Plantillas `.txt`/`.md` de BWM habilitan Nuevo documento usando XDG y se añaden una sola vez sin pisar las propias. La regla flotante guardada de Nautilus tiene `excludeSkins: ["retro"]` por elección del usuario: sigue el modo del workspace sólo en Retro, conserva su regla en las demás skins. Apertura real silenciosa en workspace 9 comprobada en mosaico; no se reinició el Nautilus existente ni se verificó el nuevo aspecto en pantalla.
* **Nuevo documento confirmado en sesión (§3.320):** el Nautilus antiguo conservaba desactivada la ruta Templates. Reiniciado el proceso desde Hyprland, recuperadas las dos ventanas/carpetas y confirmado su modelo de menú real con «Archivo de texto.txt» y «Documento Markdown.md». La configuración XDG y las plantillas ya eran correctas; no forzar reinicios al cambiar de skin. El menú de creación requiere una carpeta escribible, no una vista virtual como Recientes.
* **Barra = la de Omarchy (§3.118):** `quickshell/ii/omarchyShell/` es `shell/` de Omarchy quattro `18ac93c` (su anfitrión de plugins como `OmarchyShell.qml`, `plugins/bar`, paneles, agentes, servicios de multimedia y sesión remota), cargado sólo en Retro en lugar de la barra de BWM. Arrastrar widgets para reordenarlos, arrastrar un hueco vacío (o mantener pulsado) para llevar la barra a cualquier borde, doble clic en el centro para el fondo (transparente, vidrio, opaco; el vidrio con `skins/retro/hypr/misc.lua`), módulos propios (`type: command`/`qml`). Configuración en `~/.config/omarchy/shell.json` (formato de Omarchy; se creó una vez desde `~/.config/bwm/omarchy-plugins.json`, que ya no se usa), `omarchy-bar` y `omarchy-plugin-*`. Plugins de terceros en `~/.config/omarchy/plugins` y los preinstalados de BWM (`omarchy-plugins/`).
* Adaptaciones «BWM»: workspaces con numeración global (Omarchy numera por monitor, §4.3 de `docs/OMARCHY_4_5.md`); indicadores de mantener despierto, luz nocturna y no molestar sobre los servicios de BWM; el menú y las capas de BWM (portapapeles, emojis, selector de imágenes, recordatorios) por `OmarchyPlugins`, que tiene el único destino IPC `shell`; panel de pantallas que guarda con `monitor-manager.py`. `bwm-plugin.sh` mantiene sus órdenes para Ajustes → Barra/Plugins y el menú, pasadas a las de Omarchy. `bar.workspaces.shown` ya no afecta a Retro (Omarchy enseña 1-5 y los que existan).
* **About del menú Retro:** `omarchy-launch-about` ejecuta Fastfetch con logo ASCII, marcos Hardware/Software/Age, autoajuste y brillo originales de Omarchy (`hypr/omarchy/about/`, MIT, `b8706a3f`). Datos de Gentoo/BWM mediante `bwm-about-data.py`; WM muestra la versión en ejecución de `hyprctl`, no la del binario recién actualizado. About de Settings no cambia.
* **Guía de atajos** (§3.68): Alt+A y Aprender → Atajos abren el selector de Omarchy en `omarchy-menu` (800×500), con buscador Qt, combinaciones y acciones en columnas, colores del tema y sin pie de ayudas. Lee los atajos activos de Hyprland; Intro ejecuta la acción resoluble después de cerrar la capa. Los gestos de ratón y callbacks Lua no resolubles quedan como referencia. IPC `cheatsheet open|toggle|close|inspect`; `omarchy-menu-keybindings --print` lista los atajos. default (end-4)/Plasma conservan su guía anterior.
* **Configuración integrada en Omarchy (§3.136):** Super+I, el menú y la cuadrícula abren Ajustes (`setup`) en la capa `omarchy-menu`. Listas nativas con buscador y valores: Interfaz/Vista general, Batería (sólo con batería), Servicios e Inactividad usan `Config.options`; cursor, apps predeterminadas, atajos, inicio automático y plugins pasan a sus gestores mediante `skins/retro/scripts/settings.py`. Los formularios nuevos se guardan con Añadir; la edición de campos con Intro/Guardar y Esc cancela. No hay árbol duplicado Configuración ni «Más opciones» que cargue páginas de otra skin. Pantallas es la única vista gráfica: distribución, modos, escala, giro, activar, duplicar y workspaces, con borrador hasta Aplicar. Esc/← devuelve búsqueda, fila y desplazamiento. Los enlaces IPC antiguos de páginas se redirigen; la extensión del usuario se fusiona al final.
* **Configuración en texto** (§3.61): `bwm-user-config list|edit|apply|path` para `hyprland` (`~/.config/bwm/user/hyprland.lua`, cargado al final de `hyprland.lua` con `pcall`), `shell` (`~/.config/bwm/user/shell.jsonc`: `all` y `skins.<id>`, aplicado por `bwm-theme-manager.py apply-user` y en cada cambio de skin), `omarchy` (`~/.config/omarchy/shell.toml`, que Omarchy ya vigila) y `menu`. Menú → Ajustes → Editar configuración.
* **Menú** (Super): `modules/ii/omarchyMenu` + `hypr/omarchy/bwm-menu.jsonc`. ↑↓, Tab/Shift+Tab, Ctrl+J/K/N/P, Inicio/Fin; Esc/← vuelve al submenú anterior conservando fila y búsqueda, Borrar vuelve con el buscador vacío. Sin pie de navegación ni descripciones redundantes (§3.136). Estilo → Ventanas conserva Glass, esquinas y huecos, sin los controles genéricos transparente/opaco; Dock incluye Activar. Estilo → Barra → Widgets enlaza a Ajustes → Plugins → Instalados. Temas: un carrusel con todos los incluidos/instalados y la paleta dinámica; Catálogo de Temas/Plugins como listas con buscador sobre caché local, 60 entradas por lote y Mostrar más. Guards de hardware/programas se conservan al mezclar ajustes y ocultan también sus descendientes en búsquedas. IPC `state`, `selected`, `back`, `inspect`, `settings <página>`. **Apps** (Alt+Espacio/Super+Espacio): cuadrícula nativa con buscador Qt, navegación por teclado y menú contextual (§3.63).
* **Dock** (opcional, Estilo → Dock → Activar, apagado): `modules/ii/omarchyDock`, sólo en workspaces flotantes; Super+M y el botón − de la barra minimizan como Omarchy (`special:minimized` + `omarchy-minimized-from-<n>`; el dock las devuelve al workspace que tienes delante). Las otras skins usan el mismo sitio y la misma etiqueta (§3.114): al cambiar de skin no se mueve nada.
* **Notificaciones** (`omarchyNotifications`), **OSD** (`omarchyOsd`), **polkit** (`omarchyPolkit`), **recordatorios** (`omarchy-reminder`), bloqueo estilo hyprlock, captura omasnap, portapapeles (Super+V), emojis (Super+.), salvapantallas nativo de Omarchy 4.5 (compilado con `install-screensaver.sh`; si no, el de terminal, §3.103), glass, transparencia de ventanas (Super+Backspace).
* Librerías de Omarchy vendidas: `quickshell/ii/Commons`, `quickshell/ii/Ui` (MIT). Comandos `omarchy-*` sustituidos en `config/hypr/scripts/omarchy-shims/` (enlazados en `~/.local/bin`).
* **Fuentes del shell (§3.109):** `Commons/Style.qml` resuelve `monospace,<appearance.fonts.monospace>` y entrega a Qt la familia concreta. Sin la regla global `50-omarchy.conf` de Omarchy, aquí `monospace` solo elegía Liberation Mono aunque el perfil indicara JetBrains Mono. Se respetan las preferencias explícitas de Fontconfig, `omarchy-font-set` y `OMARCHY_MENU_FONT`; no se modifica Fontconfig del usuario ni el aspecto de las otras skins.
* **`OMARCHY_PATH` = `~/.config/hypr/omarchy` (§3.102):** raíz de Omarchy para sus piezas (`bin` → shims, `default/i18n`, `themes`, `shell/plugins/{agents,panels/elsewhen}` como enlaces). Panel de agentes con los colectores de upstream; sin modelos locales.
* **Modo de cada workspace (§3.106):** mosaico, desplazamiento o flotante como en Omarchy 4.5 (`skins/retro/hypr/workspace-modes.lua`, modos guardados en `~/.local/state/omarchy/workspace-layouts/` con su formato). Un workspace flotante es un escritorio tradicional: ventanas que flotan al abrirse a 1100×760 como máximo, en cascada, con barra de título en todas (también las que traen la suya, con el nombre de la app; el plugin de Omarchy sin cambios, `src/omarchy-titlebars`, cargado la primera vez que algo flota, §3.108), clic para enfocar y sombras. Se cambia pulsando el glifo del workspace activo en la barra o en el menú → Estilo → Layout de workspace (sin Super+L). El dock de Omarchy sale sólo en workspaces flotantes, como en Omarchy.
* Idioma del shell de Omarchy: menú → Ajustes → Idioma, con el proveedor original de Omarchy; no hay segundo selector de idioma en ajustes generales.

### 2.4 Breeze (Kde plasma): port sobre Hyprland

* **R6, primera iteración (2026-11-20, §324):** sombra KDecoration contrastada contra
  `ShadowItem::buildQuads` de KWin 6.7.5: uniones fraccionarias/asimétricas, coordenadas de
  imagen, observación de cambios internos, memfd sellado/lectura `pread` acotada, daños
  anteriores y preferencias originales de Breeze. 192 casos + 18 muestras claro/oscuro/
  Sweet sin diferencias CPU de alpha/color; comparador ASan/UBSan. Plugin candidato
  renderizado en Hyprland anidado, con salida anfitriona virtual retirada y sesión
  restituida. Sólo instalado mediante `make install` en `build/`, no en la sesión diaria.
  **R6 abierta; `no_shadow=true` sigue vigente.** Pendientes paneles/menús/popups,
  XWayland/CSD y comparación visual completa; `docs/BREEZE_R6_RESULTS.md`.
* **R6, iteración 2 (2026-11-21, §326):** breezebars sirve `org_kde_kwin_shadow_manager` v2
  (`KdeShadow.cpp`): `KWindowShadow`, `DialogShadows` y `PanelShadows` originales envían sus
  piezas. El panel publica desenfoque/contraste/sombras como `PanelView`; el plugin ya no
  bloquea el XWayland a demanda. Frente a KWin 6.7.5 en compositores privados: 120 casos de
  piezas (3 temas, 4 escalas) máx. 1/255, diálogo original máx. 3/255 con ciclo de vida
  exacto, panel idéntico salvo 1/255 a escala 2, desenfoque con región correcta pero
  intensidad distinta. Candidato sólo en `build/r6-surface-plugin`; **veto diario intacto**.
* **R6, iteración 3 (2026-11-21, §327):** decoración completa (marco, contorno, icono y sombra
  KDecoration) de una ventana normal frente a KWin 6.7.5 en GPU: Breeze oscuro/claro y Sweet
  Aurorae × 1/1,25/1,5/2. Corregidos contorno a doble escala, icono a 1x en HiDPI e iconos vacíos
  del auxiliar offscreen (sólo `:/icons`; afectaba también a la sesión diaria) y sombra de Aurorae
  sin bordes en ventanas creadas activas (Sweet 2/255). Quedan esquinas del contenido. Sin instalar.
* **R6, iteración 4 (2026-11-21, §328):** radio de las esquinas del contenido como KWin: Hyprland
  dibuja regla × escala − 1 px y breezebars redondeaba antes de escalar. Ahora la regla es el
  entero más cercano a `round(radio × escala)` de KWin, potencia 2. Breeze oscuro 73→16/255 y
  claro 109→27/255 a 1–1,5; a escala 2 la regla entera no llega (9 u 11 px frente a 10). Queda el
  suavizado del contorno en las esquinas. Sin instalar.
* **R6, iteración 5 (2026-11-21, §329, análisis):** contorno en esquinas = cobertura distinta de
  `renderBorder` y el sombreador de KWin, sin parámetro. Desenfoque: mismo *dual kawase*, distinto
  desplazamiento por pasada; `passes` 7/`size` 8 sin ruido/contraste/brillo/viveza queda a 4/255 de
  KWin con su intensidad por defecto (los valores de Hyprland por defecto, 32/255). Activarlo en
  Breeze diario (Quickshell `BackgroundEffect`, variantes translúcidas, `no_blur` sólo a quien no lo
  pide) queda pendiente del usuario; en Breeze sigue apagado.
* **R6, iteración 6 (2026-11-21, §330):** desenfoque de KWin activo en Breeze diario (lo pidió el
  usuario): `kwin.lua` lo enciende según `blurEnabled`/`BlurStrength` de `kwinrc` (7 pasadas,
  `size` 8 por defecto, sin modulaciones); panel, Kickoff, bandeja y notificaciones lo piden con
  `BackgroundEffect` y usan las variantes `translucent` del tema (`theme/BlurPath.qml`); regla
  `breeze-blur-frames` con `ignore_alpha`. Ventanas que lo piden: pendiente (llevan `no_blur`).
* **R6, iteración 7 (2026-11-21, §331, candidato sin instalar):** breezebars pone `no_blur` con
  prioridad mínima sólo a las ventanas que no piden desenfoque (`blur_on_request` para las reglas);
  `SquareTop` ya no mezcla dos veces la franja superior de ventanas translúcidas (fallo también
  diario). Mismo resultado que KWin con ventana normal translúcida a 1 y 1,5; regla del usuario manda.
* **R6, iteración 8 (2026-11-21, §332):** OSD y cambiador piden desenfoque y usan variantes
  translúcidas (capas en `breeze-blur-frames`); descripciones emergentes con `widgets/tooltip`
  translúcido. Temas globales propios (`ThemeHost`) sin desenfoque; Alt+Tab real sin ver.
* **R6, iteración 9 (2026-11-21, §333):** menús contextuales (`MenuHost`, incluidos submenús),
  diálogos de temas globales en `ThemeHost` (`compat/Dialog.qml` en OSD y cambiador), editor del
  panel (`PanelEditor`) y KRunner (capa `krunner` en `breeze-blur-frames`) ya piden desenfoque y
  usan variantes translúcidas. Pruebas QML, puente KDE, cambio de skin y política Lua en verde.
* **R6, despliegue (2026-11-21, §334):** `breezebars.so` (0 UNIQUE) y `bwm-decorator` instalados
  atómicamente; `breeze-float-all` retira `no_shadow` y `no_blur` cuando el plugin expone
  `blur_on_request` (verificado en vivo tras reiniciar: 4 bordes/esquinas KDE, `blur_on_request` y
  `SquareTop` sin doble mezcla).
* **R7, iteración 1 (2026-11-21, §335):** animaciones de Breeze consolidadas en
  `skins/plasma/hypr/animations.lua` con las curvas y duraciones de KWin 6.7.5 (`scale` 200 ms
  `popin 80%` `OutCubic`/`InCubic`, `maximize` 250 ms, `fadingpopups` 150/600 ms, `slide` con muelle
  nativo `spring:kwin_slide` `k=300/factor, ζ=1.1`); corregido el bug invertido de `AnimationDurationFactor`
  (`speed` medido en `libhyprutils`: 1.0 = 100 ms, proporcional al factor) y eliminados `md3_*` y
  `popin 60%`. Ver `docs/BREEZE_R7_RESULTS.md`.
* **R7, iteración 2 (2026-11-21, §336):** Efectos de escritorio en Preferencias (`effects`) y
  `kcm_bwm_effects` instalado en systemsettings nativo experimental. Mismo backend R3: seis
  toggles implementados, intensidad del desenfoque, duración/escalas y factor; Aplicar,
  Restablecer y Predeterminados, revisión/relectura y errores con borrador conservado.
  `slidingpopups` controla por ahora capas con `fade`, no desplazamiento KDE; límites explícitos
  en capacidades/informe. Pruebas en XDG temporal y carga Wayland; sin cambiar efectos diarios.
  R7 sigue abierta por comparación temporal y transformaciones pendientes.
* **R7, iteración 3 (2026-11-21, §337):** comparación temporal real KWin 6.7.5/Hyprland 0.56.2:
  2.719 frames (factor 1/2/0), abrir/cerrar/maximizar/restaurar y cierre durante apertura. Factor 0
  sin estados intermedios de opacidad observados; diferencia de color inicialmente atribuida a
  escala/alfa (rectificada en §338: dim inicial del arnés) y cancelación de cierre distinta. OutQuart mejorada con cota matemática
  <1/255, sin certificar aún popups. JSON/lámina en `docs/BREEZE_R7_*`; R7 sigue abierta. Sólo la
  curva se recargó en diario, sin plugins ni preferencias cambiadas.
* **R7, iteración 4 (2026-11-21, §338):** eliminado el dim inicial de Breeze con `fadeDim=false`,
  activo en diario. `KWinScale.cpp` restaura escala/alfa completas al cerrar durante entrada,
  sin reemplazar relojes. Candidato probado: 2.701 frames sin decoración + 1.401 con KDecoration,
  ocho guardas y 46 pruebas. Quedan residuos (3,0625 px > 3 px y tres ajustes temporales fuera
  de margen), sin paridad exacta. Plugin instalado atómicamente; **C++ pendiente de próximo
  inicio de sesión**, antiguo aún cargado. Sin hot load/reinicio/commit/push. Informe R7.
* **R7, iteración 5–6 (2026-11-22, §340):** validado `breezebars-scale` en la sesión diaria tras
  reiniciar (`resetOnClose: 0 → 1`, `tracked: 0`); comparación numérica de ida y reversión (120 ms)
  de `KWin::SpringMotion` frente a `SSpringCurve`; clasificación de capas (`breeze-static-layers`,
  `breeze-sliding-layers`), `PlasmaTheme.slidingPopups` en `Panel.qml`, `KickoffWindow.qml` y
  `TrayPopup.qml`, y contrato `r7_contract` actualizado. 71/71 pruebas en verde.
* **R8, lote 1 (2026-11-22, §341):** cerrados los 8 avisos QML reales de `modules/plasma/*` en el
  log en vivo (`Task.qml`, `ToolTipArea.qml`, `SystemTray.qml`, `TrayPopup.qml` → **0 avisos** tras
  reiniciar el shell); añadido botón «Clear History» (`Cliphist.wipe`) y copia con `Return` en
  `ClipboardApplet.qml`, e icono + botón de cierre en cada tarjeta de `TaskToolTip.qml`. 25/25
  pruebas QML en verde (`docs/BREEZE_R8_RESULTS.md`).
* **R8, lote 2 (2026-11-22, §342):** rueda del reloj que cambia de zona horaria (`onWheel` original,
  guarda `lastSelectedTimezone` en `bar.plasma.clock`) y relojes del calendario con
  `selectedTimeZones` (antes `["Local"]` fijo). Rectificado el lote 1: los avisos QML de
  `modules/plasma` sólo salen al destruir la generación anterior en una recarga en caliente.
* **R9, aceptación final (2026-11-22, §343):** verificados binarios cargados en la sesión diaria
  (`breezebars.so` `103fab72…`, `bwm-decorator`, 10 KCM BWM descubiertos por `settings-native.sh`,
  dueño único de `qs -c ii`/polkit/bridge, `hyprctl configerrors` vacío y `bwm-requirements.py`
  completo) y **364 pruebas ejecutadas con 0 fallos** (293 Python multi-skin, 68 QML + C++ Breeze,
  3 CTest). Informe completo con límites explícitos en `docs/BREEZE_R9_RESULTS.md`.
* **R8, lote 3 (2026-11-22, §344):** levantada la contención de capturas (`BREEZE_RECOVERY.md`)
  tras confirmar `bwmScreenshareMonitorGuard` v1 en Hyprland 0.56.2: `TaskToolTip.qml`,
  `ThumbnailGrid.qml`, `ThemedSwitcher.qml` y `WindowThumbnail.qml` vuelven a capturar con doble
  guarda QML (visible + no minimizada); `TaskToolTip.qml` añade icono de respaldo para minimizadas
  y controles multimedia MPRIS (`previous`/`togglePlaying`/`next` + título de pista). 17/17 OK.
* **R8, lote 4 (2026-11-22, §345):** exclusión mutua entre capas `Overlay` de Breeze
  (`KickoffWindow.qml`, `MenuHost.qml`, `TrayState`), máscara de entrada restringida a `frame` y
  `keyboardFocus: OnDemand` cuando Kickoff está fijado (`pin`), y cierre con cualquier botón.
  `test_plasma_menus_ui` 5/5 OK, 0 errores en `qs -c ii`.
* **R8, lote 5 (2026-11-24, §349):** insignias y barra de progreso Unity LauncherEntry en las
  tareas del panel (`launcher-entries.py` en el bus de sesión, `LauncherEntries.qml`,
  `TaskBadgeOverlay.qml` original); vistas en sesión con un emisor de prueba.
* **Preferencias nativas en Breeze (2026-11-22, §346):** `open-settings.sh` (Super+I y menús)
  usa ahora por defecto el `systemsettings` real de KDE vía `settings-native.sh` (con alias cortos
  `display`, `effects`, `autostart`, etc. y los 10 `kcm_bwm_*` + `kcm_kwindecoration`).
  `plasmaSettings.qml` queda para páginas exclusivas de BWM (`background`, `bar`, `services`,
  `general`, `style`, `about`, `windowrules`), `BWM_SETTINGS_HOST=legacy` o respaldo. 19/19 OK.
* **R5 (2026-11-18, §303):** «Ajustes del panel» originales de Plasma en el anfitrión aislado, abiertos
  con «Enter Edit Mode»; alineación/desplazamiento/modo de longitud guardados en `plasmashellrc`.
  Probado offscreen y visto en Hyprland; evolución hasta la iteración 13 (§325) en
  `docs/BREEZE_R5_RESULTS.md`.
  Iteración 2 (§304): «Set Position…» (flechas como capas, borde cambiado sin recrear la vista,
  paso a otro monitor en la vista desechable), medido en Hyprland con `check-edit-mode-session.py`.
  Iteración 3 (§305): «Añadir widgets…» con el `WidgetExplorer.qml` original en una capa lateral;
  añade al panel y vuelve a los Ajustes, probado offscreen y medido en Hyprland.
  Iteración 4 (§306): caja de herramientas del panel y menú del botón derecho originales
  (archivo `defaults` del paquete de shell), probados offscreen.
  Iteración 5 (§310): autoocultar y esquivar ventanas con una franja de borde en lugar del
  protocolo de KWin (sólo `--native-policy`); autoocultar medido en Hyprland, esquivar aceptado
  por el usuario en ambos sentidos tras volver a entrar (§313). Iteración 6 (§314): mover/clonar
  paneles y edición transaccional de perfiles. Iteración 7 (§315): alineación/longitud de
  bar.plasma migradas con tamaño lógico explícito por salida; formatos anteriores conservados.
  Iteración 8 (§316): varios paneles con política nativa; reserva el normal más grueso por borde,
  con reservas temporales en edición. Medido en Hyprland y aceptado con el ratón. Iteración 9
  (§317): alternativas de widgets (`AppletAlternatives.qml` + `AlternativesHelper`), arrastre
  `text/x-plasmoidservicename` al panel, reordenado con `ConfigOverlay` y desinstalación de widgets
  locales desde `WidgetExplorer`; probado offscreen normal/ASan, medido en Hyprland y verificados
  los 6 flujos con ratón real (`/dev/uinput`) en el LG (§321). Iteración 10 (§321): bordes
  adyacentes/esquinas con anclaje bilateral `FillAvailable`, `availableScreenRect` y `bwmPanelBounds`
  por orden de superficie, popups en esquinas con `exclusiveZone=0` respetando paneles y barras
  externas, corrección de foco de `PanelRulerView` y verificación del editor a escalas fraccionarias
  (`1.25`, `1.5`, `1.6`) en salida headless temporal (`BWMR5-*`). Iteración 11 (§322): anfitrión de
  escritorio `DesktopViewHost` cargando `Desktop.qml` y `DesktopEditMode.qml` instalados sobre
  `LayerBackground` (`org.kde.plasma.folder`, `[Desktop]` en `shell/contents/defaults`, traspaso de
  `PanelConfigView`, `sidePanel` WidgetExplorer en `LayerTop`, `AppletAlternatives` y menú «Add Panel»);
  probado offscreen normal/ASan y medido en Hyprland real. Iteración 12 (§323, cierre): escritorio
  probado con ratón real en el LG (`preview-isolated.py --desktop`): Folder View y menú del escritorio
  originales (corregido el orden de `isScreenUiReady`), «Desktop and Wallpaper…» con
  `ContainmentConfigView` (fondo y Layout), «Add Panel» ejecutando las plantillas `layout.js` originales
  y área útil del compositor en `strictAvailableScreenRect`. Iteración 13 (§325): configuración de
  widgets con `AppletConfiguration.qml` instalado, gestor original de escritorios/paneles y modelos
  (mover/intercambiar/recuperar conservando widgets), reserva de plantilla correcta desde su creación,
  «Add Panel» en la salida activa y Aplicar inicialmente desactivado. Comparación con plasmashell y
  KWin 6.7.5 privados: 12 ventanas de configuración a escala 1/1,25/1,5/1,6 (idénticas a 1; error
  máximo de 1/255 por canal en fraccionaria), 4 capturas de modo edición con diferencias registradas,
  botón central con selección primaria desechable. Quedan los efectos de R6 y la integración diaria,
  sin atribuir aceptación al usuario; `docs/BREEZE_R5_RESULTS.md` y su JSON de referencia.
* **Breeze II (2026-11-12):** `docs/BREEZE_PLAN_V2.md`, R0 entregada con referencia y límites documentados;
  R1 corrige origen de especiales al minimizar, activación común y filtro de Alt+Tab (pruebas
  aisladas; fallo visual original pendiente). R2 tiene primer KCM QWidget real, descubierto por
  `systemsettings --list`, aún sin migrar el lanzador. Dock Retro ya usa restauración común con
  origen especial preservado (R1, pendiente de sesión). Veto no_shadow restaurado como contención
  y miniaturas Breeze suspendidas tras el crash; recuperación/comparación visual pendientes. Informes `BREEZE_R0/R1/R2/R6_RESULTS.md`.
  R3 añade ocho KCM nativos/adaptadores, perfil KAuthorized del lanzador experimental y
  descubrimiento de configuradores por factories; pruebas aisladas aprobadas, aceptación
  real y cobertura completa pendientes (`docs/BREEZE_R3_RESULTS.md`). Sin migrar Super+I.
  R4: auxiliar aislado libplasma/PlasmaQuick en src/bwm-plasma-host, opción externa Andromeda
  guardada/releída en proceso nuevo y dos instancias. Ya tiene popup/diálogo con botones y
  catálogo vivo (también applets compilados), conexión KNS nativa y vista temporal explícita.
  Pruebas QtTest/ASan; adaptador LayerShellQt y staging nativo añadidos (2026-11-13).
  plasma-desktop instalado: org.kde.panel/QML original, AppletOrder y configuración por
  QAction probados; staging de cinco widgets/dos paneles. Dialog propios ocultos sin superficie
  reciben adaptador layer-shell por contexto; ViewCorona usa salida Qt (offscreen/ASan OK).
  Claves compartidas entre categorías sincronizadas en memoria y páginas estables durante
  cambios de controles; Aplicar/Cancelar/Predeterminados y lectura en otro proceso probados (§185).
  API PanelSession de instancias/altas/bajas/orden/acciones para R5 probada sobre org.kde.panel:
  lectura de archivo, posiciones y opciones en proceso nuevo (§186), sin activar el panel diario.
  Páginas por módulo QML y required/title/cfg_ antes de completar admitidas (§188), con fábrica
  común diálogo/probe/ejercicio y errores explícitos. Regresión normal/ASan y proceso nuevo OK.
  Marco original Panel.qml alojado por PanelViewHost/ContainmentView (§189): SVG/temas, bordes,
  flotación, tamaño, NoBackground y ruta del ejecutable probados con readback offscreen/ASan.
  Migración de borde/orientación corregida (§190): cuatro bordes y fallback bar.bottom,
  lectura nativa/QML por ambos ejes y fuente intacta, normal/ASan. R4 no se declara cerrado.
  Seis preferencias del marco guardadas en plasmashellrc nativo (§191), con efecto en la vista,
  kdedefaults/inmutabilidad, conflictos y lectura de dos paneles desde otro proceso probados.
  Los setters siguen siendo vista previa; guardar es explícito. Sin activar el panel diario.
  Staging migra grosor/flag de flotación/enum de opacidad (§192) al archivo KDE separado;
  ocho casos/dos paneles, marco original, lectura nueva y rechazos Adaptive normal/ASan OK.
  Geometría/controladores restantes se archivan con motivos; no hay activación de sesión.
  PanelRuntime coordina vistas por salida/skin (§193): hotplug, duplicados, borde/resolución,
  cierre de configuración pendiente/ventanas propias y reapertura Qt aislada normal/ASan OK.
  Hook común before/after controla ahora una prueba registrada explícitamente (§194), con
  confirmación, unicidad y cierre/Ctrl+C probados. Perfil diario/autoridad de bindings y
  aceptación de cambios de skin en Hyprland pendientes; no sustituye el panel activo.
  ProfileStore conserva un perfil de ensayo entre procesos (§195): archivos KDE completos,
  bindings, checkpoints e IDs/opciones propios; restore a otra ruta evita escrituras tardías
  del propietario viejo. Qt/CLI/envoltorio normal/ASan OK; raíces temporales, sin activación diaria.
  Exportación explícita a XDG de estado (§196): conserva estado seleccionado e historial de
  snapshots fuera de /tmp; fuente eliminada y destino reabierto/guardado/restaurado en fixtures.
  Estado real del usuario intacto; selección/activación/fallback del panel diario pendientes.
  Recuperación explícita desde snapshot (§266) incluso con head ausente/roto o generación
  actual incompleta: lease exclusivo, nueva generación, archivo exacto del head anterior y
  validación de hashes/layout nativo. CLI/envoltorio offscreen, Qt/procesos separados,
  autoridad XDG fuera de /tmp y rechazos normal/ASan comprobados. No es fallback de sesión.
  Elección persistente de perfil (§267): ProfileSelection guarda nombre/procedencia/revisión
  en la autoridad XDG, exige revisión vigente y bloquea cambios si un host conserva el lease.
  --selected-profile --follow-skin abre la elección bajo ese lease, siguiendo generaciones
  recuperadas sin tomar una ruta vieja de status. CLI/envoltorios y ciclo nativo de cierre
  probados offscreen normal/ASan; sin autostart ni sustitución del panel de uso diario.
  Cierre ordenado del preview (§268): bwm-power pide retirada al registro de su instancia
  Hyprland y espera el resultado del proceso tras sincronizar y guardar su checkpoint. Si
  falla, registra el motivo y sigue con el cierre. Caída/reapertura y cierre comprobados
  con anfitrión real offscreen. Pendientes logout real y activación del panel diario.
  Comprobador de reservas por borde y varias salidas (§269), con perfil desechable,
  comparación de las cuatro reservas por salida y retirada verificada. Perfiles probados
  en Qt aislado. Borde superior simultáneo en MSI y LG validado en sesión (§270).
  La prueba lateral recorre ambos bordes en una ejecución y exige la restauración de la
  geometría y las reservas, además del recibo de salida del propio anfitrión (§271).
  El ensayo izquierdo encontró que la reserva inferior acortaba ambos paneles; el
  anfitrión usa ahora tamaño explícito y `exclusive_edge` en layer-shell v5 (§272).
  Izquierda y derecha ya validadas en MSI y LG, con 48 px de reserva por salida,
  longitud de 640 px conservada y salida limpia confirmada en ambos ensayos (§273).
  El ensayo con una ventana propia maximizada admite ahora recorrer varios bordes
  en una salida (§294). En MSI se confirmaron el marco y el reajuste arriba y en
  los dos laterales (§295), además del inferior (§208). El ensayo sólo remaximiza
  una fase si falla la observación automática. En LG se verificaron las cuatro
  reservas y todos los marcos. El reajuste sin remaximizar pasó arriba y en los
  laterales. Falló al retirar el panel inferior. Carrera reproducida y corregida
  en el observador (§296). El LG recuperó su área al retirar el panel inferior
  con un único maximizado inicial (§297). El ensayo inferior simultáneo pasó
  con un marco por salida (§§298–299). La expectativa del comprobador admite
  escala y giro (§300). El maximizador y el observador aplican también el
  redondeo de Hyprland en geometrías fraccionarias (§301). Una salida headless
  temporal confirmó maximizado y reajuste con escalas 1,25/1,5/1,6 y giros
  1/2/3/5. El observador ya no se detiene con salidas sin EDID (§302).
  Inventario de plasmoides internos de la bandeja nativa y comprobación de su guardado
  en otro proceso (§274). `r4-session-check.py --tray` lee el dueño y los contadores SNI
  de la sesión sin activar servicios.
  Quickshell observado como dueño del watcher SNI, con dos iconos registrados (§275).
  Ensayo offscreen de enumeración con el modelo nativo y proxy D-Bus acotado (§276).
  Plasma recibió las mismas dos filas que el watcher de Quickshell en sesión (§277).
  Ensayo de estado e icono SNI con `--properties`, limitado a leer los objetos
  registrados y con comprobación de dueño al final (§278). Pendiente sesión real.
  El ensayo de sesión recibió dos filas y ningún permiso por objeto. Nueva resolución
  por `ListNames`/`GetNameOwner` y contadores de rechazo y lectura directa (§279).
  Sesión confirma dos nombres únicos sin alias. Variante local del proxy permite
  el `GetAll` exacto para esos objetos (§280). Corregido el alias recursivo al arrancar
  el proxy (§281), la sesión volvió a enumerar las dos filas. El comprobador ahora
  lee el enum de estado que publica Plasma y cuenta los pixmaps por separado (§282).
  En sesión, el anfitrión actualizado obtuvo estado, categoría y pixmaps para los
  dos iconos sin cambios de dueño, inventario ni objetos (§283).
  Ciclo SNI original aprobado en D-Bus privado (§285) y a través del proxy con dos
  señales exactas por objeto (§§286–287). Confirmadas la activación principal y
  secundaria, la rueda y la solicitud `ContextMenu` (§289). El menú D-Bus se
  importó fuera de pantalla y su acción llegó al productor (§§290–291). El
  anclaje y los clics pasaron con una capa sin reserva en Wayland (§§292–293).
  El ensayo ya selecciona el monitor enfocado al lanzarlo. Falta confirmar
  la corrección de monitor en sesión (§293).
  Consulta fresca de disponibilidad (§197): status no recarga ni cambia skin; renderReady
  requiere QML/exposición y frame Qt de la misma generación. Bloqueos explícitos y timeout;
  replacementReady false conserva el panel diario. Qt/software y CLI aislados comprobados.
  --native-policy (§198) conecta panelVisibility 0/3 con peticiones LayerShellQt de grosor
  nativo; flotación, retirada/skins y lectura nueva probadas. Un panel por salida en ese modo;
  reserva real/posicionamiento Wayland pendientes, sin sustituir el panel diario.
  Diagnóstico local r4-session-check.py (§199) con informe privado, filtros y timeout; aquí
  sockets presentes/propios e IPC inaccesible. Elevación denegada por política del ejecutor.
  Acceso del terminal local confirmado (§200): dos salidas a escala 1 con 44 px inferiores,
  sin ensayo R4. Runner temporal de reserva/cierre automático preparado, sin ejecución gráfica
  nueva del asistente; maximizado/aceptación siguen pendientes.
  Primer ensayo local (§201): auxiliar activo pero output-unavailable, cierre/44 px restaurados.
  Compatibilidad de descripción Hyprland con Qt sin serie e inventario diagnóstico añadidos;
  falta repetir la prueba real, sin certificar identidad física por serie ausente.
  Segundo intento (§202) confirma Qt Wayland y fabricante MSI con coma sólo en Qt;
  normalización limitada al fabricante completo corregida. Datos exactos cubiertos por
  regresión, limpieza/44 px originales confirmados; delta de reserva real aún pendiente.
  Reserva local MSI validada (§203): 44→92→44 px, capa original 640×48, LG inalterado y
  registro/capas retirados. Evidencia de usuario conservada; maximizado/resto R4 pendientes.
  Ensayo --maximize preparado (§204): ventana propia y maximizador BWM guardado por identidad,
  autoridad de decoración y medición independiente con/sin panel; reajuste automático separado.
  Pendiente de nueva ejecución local; no se ha certificado aún el marco maximizado real.
  --maximize local falla por to-screen invertido en runner (§205), corregido con prueba
  contra parser real. Reserva/limpieza correctas; marco todavía sin medición real.
  Maximizado explícito real validado (§206): marco 0,720,2560,1348 con panel y 0,720,2560,1396
  al maximizar de nuevo sin panel; barra de 28 px incluida. Reajuste automático al retirarlo
  falla (48 px sin usar); adición sobre ventana ya maximizada/resto R4 pendientes.
  Seguimiento de área implementado en el puente existente (§207), con autoridad de bordes,
  ejes parciales, Force KDE y guardas PID/skin/estado; sin tocar restauración/presnap/foco.
  159 tests Python pasan, incluidos Lua ejecutado y runner de aparición/retirada sin remax.
  Usuario carga el puente actualizado y valida ambos sentidos en sesión (§208): reserva
  44→92→44 y altura de marco 1396→1348→1396 sin remax, MSI inferior escala 1/giro 0. LG
  inalterado, limpieza correcta; otros casos y resto R4 pendientes. Evidencia conservada.
  El puente permanece activo para reajustar máximos BWM; no reinicia compositor.
  Build del auxiliar compartido en build/bwm-plasma-host (§213); /tmp no se asume
  duradero/compartido. Preflight del ejecutable con error accionable, sin traceback.
  Primer adaptador de escritorio nativo (§212): KWindowSystem estático en el auxiliar hacia
  minimizar/restaurar común, con opt-in de preview y controlador original probado contra
  IPC ficticio normal/ASan. Usuario confirma ciclo de minimizar/restaurar en sesión (§214);
  sin medir geometría/foco ni certificar TaskManager/Peek o integración diaria.
  Fuente de ventanas TaskManager añadida (§215), opt-in del auxiliar: snapshots e identidades
  BWM por APIs públicas, acciones comunes y dos modelos KDE probados con IPC ficticio/ASan.
  No acredita delegados Wayland, VirtualDesktopInfo, todos los menús ni sustitución diaria.
  Transacciones nativas coordinadas (§216): bloqueo entre los dos adaptadores, revalidación
  tras esperar y barrera de retirada con descarte de colas/ack sólo al terminar la acción.
  Aislado normal/ASan; no sincroniza todavía los otros llamadores del gestor común.
  Protocolo nativo de escritorios (§218) probado con VirtualDesktopInfo C++/QML, filtros,
  orden inicial y roles nativos sobre Wayland aislado. Extensión Hyprland aparte compilada,
  sin desplegar/cargar y desactivada; faltan frontend en sesión y capacidades.
  Barrera por conexión integrada (§219): control propio sobre el mismo Wayland, cola nativa
  cancelable y ack correlacionado antes de retirar; pérdida/reconexión/timeout aislados pasan.
  --native-desktops hace preflight de sólo lectura y exige handshake; sin cargar el plugin.
  Menú original de tareas protegido por capacidades (§220): tres acciones sin backend
  deshabilitadas con QActionGroup público; raíz/índices BWM y fuente KDE fijada por hash.
  Minimizar individual/grupo y cierre ante índice retirado probados normal/ASan aislados;
  Task.qml tiene avisos de roles offscreen, sin certificar pintado o aceptación Wayland.
  Pantalla completa del menú nativo conectada (§221): estado deseado idempotente, capacidad
  por ventana y guardas Python/Lua; recibo explícito del dispatcher antes de aceptar.
  Pruebas original individual/grupo + gestor/IPC ficticio/Lua pasan; sin medición visual real.
  Metadatos vivos de aplicaciones (§222): notificación KSycoca nativa, invalidación agrupada
  y lectura diferida actualizan nombre/icono/lanzador sin cambiar filas/UUID. Actualización,
  retirada/reinstalación y vida de dos fuentes probadas con base KDE real temporal normal/ASan.
  Guardas del registro Wayland (§223): control v2 declara su global KDE, cliente comprueba
  unicidad/versión/asociación antes de reanudar. Duplicar KDE exige auxiliar nuevo (modelo
  original pierde su lista); comprobado proceso nuevo con 4 escritorios frente a 0 del viejo.
  Salida permitida, controles retirados inertes y vistas ocultas al perder confirmación.
  Arbitraje de servidor experimental (§225): inicialmente disabled no publica globals;
  inventario/claim/confirmación asíncronos, elección entre BWM y retirada ante conflicto visible.
  Una generación retenida por vida del módulo; al retirar pide futuro inicio de sesión,
  nunca hot unload. Globals bajo filtro pueden ocultarse; módulos ajenos aún pueden duplicar
  brevemente. CTest7/7 normal/ASan, 14 escenarios y consumidor KDE original; no desplegado.
  Arranque/cierre del proveedor revisados (§226): peer/deadline sólo desde idle tras opt-in;
  inicialmente disabled sin sockets ni reloj. withdraw retiene; destructor final destruye
  todos los recursos/callbacks de core y claim antes de dlclose. Hyprland descarga plugins
  antes de destruir clientes: prueba con DSO realmente descargado pasa activo/retirado.
  CTest7/7 normal/ASan y 16 escenarios. Sin sesión real, despliegue ni panel diario.
  Contador común sin E/S del frontend (§227): puente existente resuelve opciones/overrides
  y envía por IPC a CountMirror en memoria. Sin fichero/preferencia nueva ni reload. Watch
  comparte coordinador/bloqueo existente (intento no bloqueante, sin recursión); parcial o
  fallo conserva último válido. Primera publicación espera dato; preflight sólo consulta
  countMirrorVersion=1/copia conocida. CTest7/7 normal/ASan, R4 Python122 y puente20.
  Entrega común entre skins implementada (§228): SharedSettingsRuntime una vez en shell.qml,
  fuera de panel loaders; Config existente + Process/Timer Qt, sin otro daemon/FileView.
  Dispatcher genérico sólo adaptadores incluidos, con prerequisito/intervalo; auxiliar usa
  opciones/overrides de skin actual sin puente KDE completo. Retirado sondeo counts de watch
  KDE. Pruebas QML/cadena de procesos aisladas pasan; carga real no verificada por IPC.
  Ensayo del Task.qml original aprobado en terminal del usuario (§233): CTest1/1,
  QtTest4/4 con icontasks/taskmanager. Conexión Wayland privada, roles/snapshots, identidad/
  metadatos propios, estados/título/índices/retirada y píxeles en QImage comprobados. Ventana
  oculta/sin handle: no aceptación de superficies/entrada ni panel diario. Avisos de servicios
  del fixture conservados; backends no certificados. Sólo pase nativo normal; compilación/
  regresión local normal/ASan sí comprobadas. No afirmar native ASan ni CTest8/8 completo.
  Correcciones previas del test: socket consumido (§230), origen por recurso/hash (§231) y
  aplicación .desktop propia sin fallback PID (§232). Aquí wl_client_create sigue bloqueado;
  no repetir prueba aprobada sin motivo. operationalVerified/replacementReady false.
  Activación de grupos sin MRU corregida (§234): StackingOrder desde clients de Hyprland,
  índices estables y fallback legado por orden de snapshot. TaskTools.js original pasa
  elección superior/actualización/prioridad MRU, sin parchear KDE. Helper Python10 y
  CTest3/3 normal/ASan; render nativo no repetido tras cambio. Diagnósticos del catálogo
  actualizados a capacidades/versiones implementadas, nunca operationalVerified=true.
  Ensayo físico de tareas FALLA (§235): clic en iconos lanza otras instancias. Causa
  reproducida: PanelSession registra el panel, y los applets sólo son hijos visuales, no
  QObject; faltaban modelos. BwmTaskBridge recorre ambos árboles. Registro real/pinned+
  ventana/focus pasan en fixture; startup espera fuente válida y muestra conteos. CTest3/3
  normal/ASan y Python7. Pendiente repetir sesión y aspecto de iconos; no aceptación diaria.
  Repetición física FALLA también tras §235 (§236): filtro showOnlyCurrentDesktop=true
  de KDE oculta ventanas sin VirtualDesktopInfo. Reproducido con QScreen coincidente.
  Preview exige --all-desktops explícito (config KDE temporal de ambas instancias) o
  --native-desktops con proveedor cargado. Test por PanelSession sin setters del modelo
  prueba dos vistas/fusión/focus y restauración de minimizada en otra pantalla. Startup
  muestra filas visibles/lanzadores. Regla común no_anim sólo en special:minimized evita
  traslado animado al monitor del almacén; sintaxis verificada, sin reload/visual real.
  CTest seleccionado3/3 normal/ASan; extensión restore ASan1/1; Python10+10+7. Pendiente
  ensayo con --all-desktops y hyprctl reload; no aceptación de sesión ni de iconos.
  Confirmación posterior del usuario (§237): «ahora si» tras el ensayo solicitado; aceptación
  funcional general del preview de tareas/recuperación. Sin desglose por app, medición de foco
  o confirmación específica de animación/iconos/limpieza; no se infiere ejecución de reload.
  No equivale a aceptar proveedor de escritorios, integración diaria ni cierre de R4.
  Apariencia del preview (§238): --session-appearance opt-in copia sólo valores KDE de
  iconos/paleta/fuentes/SVG a XDG temporal antes de QApplication, con defaults nativos.
  Proveedor Qt KDE y assets XDG del usuario legibles; no setThemeName ni layouts. Snapshot
  de inicio, sin seguimiento vivo ni perfil persistido. Motor KDE/protección de origen
  probados normal/ASan; aceptación visual real pendiente. No cambia el panel diario.
  Usuario acepta aspecto/acciones tras §238 (§239); queda hover sin miniatura y falta
  org.kde.pipewire. Backend original requiere también protocolo de captura KDE. Opt-in
  --task-thumbnails preparado: adapta sólo PipeWireThumbnail.qml revisado, conserva tooltip
  original y captura por handle estable mediante ext-image-copy-capture/Hyprland mapping,
  snapshot fresco y UUID/PID/generación; píxeles sólo memoria, cierre al ocultar/retirar.
  Local5/5 normal/ASan y Python13+10+7; prueba nativa de píxeles compilada, BLOQUEADA aquí
  por wl_client_create EPERM, pendiente terminal y después ensayo real. No captura aceptada.
  Backend BLOQUEADO para sesión sin guarda del monitor en Hyprland activo: mismo núcleo
  del crash documentado. Parche0.56.2 preparado/probado por cuerpos aislados, sin instalar.
  Peer ELF por SO_PEERCRED + /proc/PID/exe debe incluir marca de guardas antes de capturar;
  guía BREEZE_R4_THUMBNAILS.md. Próximo login necesario tras recompilar, sin hot load.
  Ensayo nativo de usuario FALLA cliente-11/fixture0 (§240). Repro sin Wayland y ASan:
  windowChanged de destructor QQuickItem accede State ya liberado. Destructor del auxiliar
  desconecta conexiones propias antes de liberar estado; conserva destroyed de Qt/QML y
  observa ventana padre inicial. Local QtTest9/9 (init/cleanup incluidos), CTest6/6 normal/
  ASan. Native corregido sigue bloqueado aquí por EPERM; repetir CTest antes de instalar
  parche/core o activar captura. No hay nueva aceptación de miniaturas ni cambios de sesión.
  Repetición nativa APROBADA por usuario (§241): CTest1/1, QtTest3/3 (init/cleanup incluidos),
  cinco checkpoints de píxeles/estático/resize/vida activa/identidad/cierre/retirada/teardown
  y cliente0/fixture0 verificados en informe. Sólo normal, entorno Wayland privado; no ASan
  nativo ni captura de escritorio real. Siguiente: instalar user patch y recompilar0.56.2
  desde fuente por usuario, adoptar al próximo login. Sin instalación/reinicio hechos aún.
  Usuario comunica «listo» (§242): parche de Portage idéntico al revisado y marcador en
  /usr/bin/Hyprland verificados. ELF de proceso activo/relogin no verificados aquí por IPC
  inaccesible; auxiliar verifica peer antes de capturar. Config skin=plasma. Siguiente:
  preview con --task-thumbnails para medir hover real; sin repetir CTest o cambiar sesión.
  Preview real bloquea en guarda (§243). Error antiguo confundía permisos con marca ausente;
  instalado marcado + cap_sys_nice=ep verificados. Causa de sesión aún desconocida. Gate
  conserva requisito, ahora informa motivos distintos y runner check-thumbnail-compositor.py
  sólo diagnóstico. ack.json ausente por child muerto ya no produce ENOENT secundario.
  Siguiente: diagnóstico de peer/lectura desde terminal; no reinstalar/reiniciar por suposición.
  Diagnóstico del usuario confirma Permission denied al leer /proc/5178/exe (§244), UID1000,
  peer Hyprland. Parche ampliado añade informe IPC de versión de guarda/PID real, implementado
  en la unidad de guardas. Auxiliar acepta informe fresco sólo con PID de SO_PEERCRED/UID
  propio; consulta limitada2s/64KiB y runtime real, no XDG temporal del preview. Conserva ELF
  directo, sin archivos instalados como prueba ni cambios de capacidades/permisos. Guardas
  previas instaladas; extensión IPC adoptada y verificada por usuario en §245: informe
  version1/PID496181 coincide con peer Wayland/UID1000, clientExit0 y verified=true.
  /proc sigue denegado, IPC funciona; siguiente preview/hover real, sin repetir rebuild/CTest.
  Ensayo visual falla (§246): tooltip centrado/listado como ventana y dos vistas. ToolTipDialog
  actual es PopupPlasmaWindow C++ sin contexto QML, ignorado por adaptador Dialog anterior.
  Adaptación pública añadida al crear superficie antes del rol, dueño por visualParent,
  reuso/movimiento/suspensión y restauración al pasar a ventana normal. Preview de tareas
  ahora una instancia; --instances2 sólo comparación explícita desechable. CTest4/4 normal/
  ASan y wrapper18. Usuario acepta miniaturas en §247; no se repite ensayo aprobado.
  Continúa §248: Nueva ventana/abrir URL de tareas pasan por cola/bloqueo e identidad vigente,
  ApplicationLauncherJob en proceso aparte con entorno original restaurado (XDG/D-Bus/Qt).
  Fuente/TasksModel original y job KDE con app propia probados; selección .desktop nativa,
  sin interpretar Exec ni lanzar fallback de PID. KIOGui explícito en build/requisitos.
  Usuario acepta nueva instancia y apertura de archivos desde icono en §249; no repetir.
  §250: lanzadores anclados sin ventana y Actions del .desktop salen también por el helper
  con el entorno original (proxy BwmLaunchRouter entre filtro y concatenación de KDE; menú
  original identificado contra el .desktop). KIOSK run_desktop_files/shell_access=false en
  el host desechable deniega sus lanzamientos internos; Lugares/Recientes enmascarados.
  CTest 13/13 normal y ASan, Python R4 155. Usuario acepta en sesión (§251) lanzador anclado
  sin ventana, Action «New Window» y archivo soltado sobre lanzador; foco sin medir.
  §252: Mover/Redimensionar, ocultar de capturas y sin borde del menú original por el gestor
  común (estado deseado + recibo + relectura); Lugares reales (copia de user-places.xbel)
  enrutados. Encima/debajo siguen sin backend. Usuario acepta todo en sesión (§253).
  §254: primera validación del proveedor de escritorios en Hyprland real (anidado desechable):
  encontrado y corregido un fallo que impedía cargar el módulo; KDE VirtualDesktopInfo,
  activación, filtro, contador y barrera pasan.
  §255: carga opt-in al iniciar Hyprland (native-desktops.py, guarda contra bucles de fallo);
  instalado con make install y opt-in activado. Primer inicio real confirmado por usuario
  en §256: cargado, ABI coincidente, arbitraje activo, contador común 10 y sin errores;
  filtro nativo de tareas por workspace aceptado por usuario en §257. Diagnóstico de sólo
  lectura para todas las salidas de §258 validado en sesión por usuario en §259: LG10 y
  MSI1, geometrías/IDs/asociación coinciden, sin acciones. Ciclo de activación por salida
  de §260 falla en sesión (§261): lectura de activación no coincide. §262 reproduce la
  secuencia focusMonitor + changeWorkspace redundante con cuerpos Hyprland 0.56.2; ruta
  corregida/instalada atómicamente (activationRoutingVersion=2). §263: ciclo real LG/10 →
  MSI/1 validado por usuario, dos peticiones aplicadas/observadas y cero fallos/rechazos,
  asignaciones conservadas y pausa final confirmada. §264 prepara --workspace-cycle para
  un ID no visible/libre, vinculado al monitor actual y sin comandos de creación. §265:
  navegación real MSI/1 → MSI/3 → MSI/1 validada, LG/10 conservado, dos acciones aplicadas/
  observadas, cero fallos/rechazos y pausa final. Logout/recuperación y autoridades del
  panel diario siguen pendientes.

  Inventario vivo de backends por instancia añadido (§211), compartido con el catálogo;
  readiness distingue render de servicios. Todos sin certificar; integración diaria pendiente.
  Reproducción local sobre e41c28d (§210): build nuevo, CTest sin fuentes externas 2/2,
  runner con fixture del repo; conservar los tres metadata.json omitidos del commit.
  Criterios originales de R4 cumplidos (§209): ciclo real de «Obtener nuevos» con la tienda
  KDE (KNSCore + plasmoids.knsrc, raíces temporales), tres widgets elegidos por la tienda guardan
  su opción propia por su página original y en proceso nuevo; Modern Clock también en Hyprland.
  saveConfig()/cfg_ sin esquema como AppletConfiguration.qml 6.7.5. Panel diario/backends fuera.
  Primera prueba en la sesión Wayland (§187): posiciones de Qt Wayland, foco del panel y Dialog
  no interactivos corregidos; menú/avatar de Andromeda bien colocados en los dos monitores.
  Cierre al pulsar fuera con hyprland_focus_grab_v1. Pendientes de sesión: desenfoque, aceptación
  del nuevo marco, escala fraccionaria y bordes. No se deduce validación del marco de §187.
  Pendientes backend de ventanas/escritorios, negociación Wayland, otros tipos/creación tardía
  de ventanas y migración/activación completa. Detalles
  BREEZE_R4_RESULTS.md / BREEZE_R4_ARCH.md. Centered de R3 confirmado por usuario en sesión.
  Autostart precarga breezebars aunque la skin inicial sea Retro/default; barras desactivadas
  fuera de Breeze. Usuario confirma el resultado visual tras las correcciones Retro→Breeze;
  no equivale a validar la matriz de R4. Nunca cargar/descargar el plugin en caliente (§183).
  Auditoría Retro→Breeze (§184): arranque/recuperación del shell con proveedor Qt estable,
  iconos GTK/Qt/KDE coherentes y avisos nativos; apps por AppSearch.launch/Hyprland y entorno
  de activación actualizado. Pruebas aisladas aprobadas y usuario confirma «está perfecto
  ahora» para el aspecto de la barra; entrega por bus y matriz completa no se deducen de ello.
  F0–F13 se conserva como historial en `docs/BREEZE_PLAN.md`.

* **Estado F0–F13 (§3.139–158):** interfaces en `modules/plasma/`, scripts/Lua en
  `skins/plasma/`. Retirados todos los `modules/ii/plasma*`, su selector artesanal, 152 SVG
  locales sin uso y la paleta fija de reserva. Informe final: `docs/BREEZE_F13_RESULTS.md`.
* **Tema original:** `PlasmaTheme` y `plasma_palette.py` leen la cascada KDE
  XDG_CONFIG_DIRS → kdedefaults → archivos locales; cambios en vivo. `plasma-theme.py`
  aplica esquemas/estilos/iconos/temas globales y sincroniza las plantillas comunes de apps.
  Cursor, Kelvin, pantallas y demás configuración común siguen bajo autoridad de BWM. La fuente general predeterminada es Noto Sans 10 y la monoespaciada Hack; fuentes propias de Breeze, no compartidas.
* **Panel/Kickoff/applets:** `modules/plasma/{panel,kickoff,tray,applets}` usan KSvg/PC3 y
  fuentes de datos KDE o servicios comunes. Panel en bar.plasma, cuatro bordes/reserva real,
  seis widgets incluidos. Clic de tareas con TapHandler, probado con eventos en cuatro bordes (§3.160);
  marcos adyacentes y medidas del SVG. Representaciones compactas nativas de Kickoff/reloj/
  Mostrar escritorio y flecha de bandeja, con márgenes originales por applet (§3.161). DesktopState gestiona Mostrar escritorio sobre el minimizado común.
  `TrayPopup` difiere `HyprlandFocusGrab` 50 ms al abrirse y el panel/bandeja usan `PlasmaTheme.ToolTipArea` (`PopupWindow` pasivo) en lugar de `PlasmaCore.ToolTipArea`.
  No hay anfitrión completo de plasmoides externos; límites de applets en sus README.
* **Ventanas:** `breezebars` compone las imágenes de KDecoration/Aurorae de `bwm-decorator`
  fuera de Hyprland; CSD negociado sin listas de clases y marco real por dirección+PID.
  `ClickToFocus` mapea a `input:follow_mouse = 2` (scroll al pasar el ratón; foco activo al pulsar) y `breezebars` ya no llama a `fullWindowFocus` en clics CSD pasantes (`m_hidden`).
  `kwin-window.py` proporciona minimizar/maximizar/restaurar; `modules/plasma/menus` los menús.
  Reglas originales kwinrulesrc y Tiling de kwinrc vía puente F2/F10, Ctrl+flechas conservado,
  Meta+T editor reducido. Comprobaciones físicas pendientes en las listas F7/F10.
* **Interfaces de sesión F12:** rejilla Alt+Tab original con controlador MRU común, OSD y
  bloqueo KDE sobre LockContext. ThemeHost (API 2) aloja QML de temas en motores separados;
  no emula todas las APIs privadas. KRunner nativo en Alt+Espacio sólo Breeze.
* **Preferencias F11:** `plasmaSettings.qml`/`modules/plasma/settings` con KCM reales mediante
  org.bwm.kcm. Páginas comunes de BWM para lo compartido. Alt+T abre el selector anterior de skins de Breeze (`modules/plasma/skinPicker`);
  los temas globales de Plasma se eligen dentro de Preferencias. KNS descarga a rutas estándar.
* **Servicios:** único servidor de avisos de BWM, agente polkit KDE en Breeze/Omarchy en Retro.
  bwm-shell-conflicts comprueba al dueño D-Bus. Kded reserva nombres en cola aun con módulos
  desactivados; sólo se retira automáticamente su reserva de bandeja rota si no tiene objeto
  y sus módulos son ninguno/ktimezoned. No se detienen otros módulos o un watcher funcional.
* **Comprobado F13:** diez ventanas y siete flujos de audio conservados en default → Breeze →
  Retro → Breeze, sin saltos de workspace ni errores de config, una instancia ii y geometría
  final conservada. Sweet instalado por KNS desde el KCM y aplicado desde Preferencias:
  colores, SVG, candy-icons y Aurorae; cursor BWM intacto. Restituida la configuración anterior.
  Estimación prudente ~50 %, no compatibilidad universal. Pendientes: sesión inicial completa,
  ratón/CSD/snapping, PAM/huella/polkit reales y más temas privados. F13 no modifica el plugin.

### 2.5 Ventanas, juegos y sistema
* `window-guard.py watch` (autostart): primary de XWayland = monitor del workspace 1, ventanas fuera de pantalla de vuelta, juegos sin bordes a pantalla completa, y fondo repuesto en los monitores que swww/awww deja en negro al reconectarse (§3.81; `window-guard.py wallpaper` lo hace a mano). También relanza Quickshell si desaparece (~20 s, §3.105). Los demonios de sesión se lanzan con `bwm_session.spawn()` (hijos de Hyprland, no de quien llama). Regla `games-main-monitor` (HP, foco al activarse, inhibir reposo).
* Dock de default (end-4) (§3.91): el de end-4 (`modules/ii/dock`), apagado por defecto; las ventanas minimizadas se restauran desde él. Retro usa el de Omarchy (`dock.omarchy`).
* **Minimizado (§3.113, §3.114):** todas las skins guardan las minimizadas en `special:minimized` con la etiqueta de Omarchy `omarchy-minimized-from-<n>`. Retro usa el script y el dock de Omarchy (sólo workspaces flotantes, vuelve al workspace que tienes delante). default y Breeze usan `toggle-minimize.py`: también en mosaico y sin dock, vuelve a su workspace de origen con la geometría exacta, y «Mostrar escritorio». Las del workspace 99 con `from_ws_<n>` de versiones anteriores se siguen reconociendo.
* Pantalla completa (§3.90): `modules/fullscreen.lua` la deja sin borde/sombra/redondeo/atenuado en todas las skins (la transparencia se respeta); el CSS de apps (Vesktop, Firefox, Stremio) anula sus bordes en `:fullscreen`.
* `focus_on_activate = true`, `xwayland.force_zero_scaling = true`, `on_focus_under_fullscreen` por defecto (2), `allow_session_lock_restore` y encender pantallas con teclado/ratón (§3.134). Reglas por app de Omarchy en todas las skins con `modules/app_rules.lua` (§3.134).
* Las apps no pueden solicitar maximizado (`suppress-maximize-events`, global); incluye botones CSD. El maximizado/pantalla completa se controla con Alt+Enter (Plasma: maximizado, otros estilos: fullscreen), y fullscreen solicitado por juegos/vídeo sigue permitido. Kitty tiene `remember_window_size no` para no restaurar tamaño/estado maximizado de su caché. Véase §3.48.
* Atajos en `config/hypr/keybinds.json` → `keybinds-manager.py` → `modules/user_binds.lua`.
* **Pantalla de inicio y bloqueo (§3.97):** SDDM (común, de BWM) entra solo en todas las skins y el bloqueo de la skin activa pide la contraseña al arrancar y al bloquear: default (end-4) el de end-4 con el fondo desenfocado de `Background.qml`, Retro el de Omarchy 4 (`modules/ii/omarchyLock`, su `LockView.qml` sin cambios) y Breeze uno como el de KDE (`modules/plasma/lock`). Tras cambiar `install-boot-theme.sh` hay que repetir `sudo …/install-boot-theme.sh --sddm --auto`.
* **Apagado común (§3.95):** `scripts/bwm-power shutdown|reboot|firmware|logout|suspend|hibernate|lock [--dry-run]`. Lo llaman el menú de sesión y el bloqueo de end-4 (`Session.qml`), Kickoff de Breeze, el menú Sistema de Retro y Alt+M. Avisa, cierra las ventanas y espera hasta 5 s a que sus procesos terminen antes de apagar, desde un servicio `systemd-run --user`.
* **Inactividad (§3.96, §3.98):** `modules/ii/idle/BwmIdle.qml`, común, con página propia Ajustes → Inactividad (`modules/settings/IdleConfig.qml`; en el menú de Retro, Ajustes → Inactividad). Tiempos independientes y comunes a todas las skins: salvapantallas `idle.screensaverTime` 150 s (sólo skins que lo traen: Retro; `idle.screensaver` lo activa), apagar monitores `idle.screen` 300 (DPMS; también cierra el salvapantallas), bloqueo `idle.lock` 600 y suspensión `idle.suspend` 0 = nunca. Respeta inhibidores y «mantener despierto»; un reproductor MPRIS sonando impide salvapantallas y suspensión.
* Kelvin común a todas las skins: `nightlight.py --temperature` lo copia a `light.night.colorTemperature` (servicio `Hyprsunset.qml` de default (end-4)/Plasma) y este llama a `nightlight.py --remember K` al cambiarlo.
* Luz nocturna (panel de pantallas de Retro, menú, indicador junto al reloj): un solo estado `~/.local/state/bwm/nightlight.json` vía `nightlight.py`/`omarchy-toggle-nightlight [--on|--off|<K>]`. Usa hyprsunset si está instalado (como Omarchy; no tiñe capturas) y si no un `screen_shader` que `modules/nightlight.lua` conserva tras `hyprctl reload`; `autostart.sh` lo reaplica (`--apply`). Véase §3.49.
* **Firefox al salir (§3.137):** `bwm-power` solicita el cierre de la aplicación con un SIGTERM por PID verificado, sin cerrar sus ventanas una por una (eso dejaba sólo la última en la sesión restaurada). No cambia las preferencias de Firefox. Validado con acciones simuladas; pendiente comprobar tras un cierre real.
* **Autoarranque (§3.76):** `autostart-manager.py run-all` empieza en el workspace 1 y, durante 3 min, manda todas las ventanas de cada app de inicio (también la principal que llega tras una de carga, como en Steam) a su `X-Hyprland-Workspace`, sin quitarte el foco. Reglas temporales por clase + ventanas que descienden del proceso lanzado.
* Regla `electron-render-unfocused`: incluye `codex`, `codex-desktop`, `chatgpt` y `ChatGPT`. Regla persistente de virt-manager: flotante (`float = true`), según el estado guardado actual.

* **Cambio de skin sin interrumpir apps (§3.57):** una sola generación de paleta/recarga de Hyprland;
  `bwm_transition.py` propaga política a hooks separados. No reinicia Firefox, Steam, Spotify, Nautilus,
  Stremio ni Vesktop durante el cambio. Recarga paneles con `bwmSkin.reload` sin matar Quickshell;
  `set <skin> --restart-shell` conserva el reinicio de mantenimiento. La geometría se captura antes de
  cambiar reglas, flotación explícita enable/disable; fullscreen/minimizadas/especiales/pinned no se recolocan.
  Los colores que no recargan en vivo esperan al siguiente inicio/aplicador (Spotify: Spicetify).

### 2.6 Pendiente / ideas
* De Omarchy sin portar (Estilo, vidrio, consola, compartir y hora ya se portaron, §3.135): Super+L para los layouts de workspace (los modos ya están, §3.106), atajos de ventanas (Super+Ctrl+F, Super+Alt+F, Super+O, scratchpad Super+S, consola Quake Super+`, copiar/pegar universal), Install/Remove adaptado a emerge/flatpak, web apps y TUIs, Setup (DNS, teclado y seguridad; Idioma y Entrada ya están, §3.128), interruptores rápidos y actualizaciones de firmware/hora.
* Qt sin recarga en vivo sólo con qt6ct (Breeze (Kde plasma) y el respaldo sin plugins); default con el plugin de KDE y Retro con el de GTK sí repintan (§3.79, §3.80). Chromium sin tema (necesita política root).
* Entorno de pruebas aparte (Hyprland anidado + usuario + rama `dev`), antes cambiar `/home/sasel` fijos por `$HOME`.
* El actualizador Retro no sincroniza los repositorios ni gestiona noticias, `dispatch-conf` o `@preserved-rebuild`; los perfiles default (end-4)/Plasma aún conservan un `apps.update` heredado con `pacman`. Adaptar ese acceso a Gentoo.
* Compatibilidad con temas del original (finalidad del proyecto): Breeze admite esquemas, SVG, Aurorae, iconos y temas globales; faltan plasmoides externos, efectos y las comprobaciones físicas de F13. default (end-4): plantillas de matugen de terceros sin probar.
* Skins de la comunidad: el comprobador ya lee `~/.local/share/bwm/skins/*.json`, pero falta definir paquete, instalación y cómo cargan su QML/Lua sin tocar el repo.
* `hyprbars-plasma.so` porteado y compilado para Hyprland 0.56.2, cargado y probado en sesión real (§3.52). Pendientes pruebas de botones, snapping y arrastre con ratón.
* Al volver de Plasma, los workspaces con 3+ ventanas pueden cambiar el reparto del mosaico (§3.53).
* Gestor de archivos por skin (posible Dolphin en Plasma); el resto de apps predeterminadas sigue común. Sin decidir.
* `xdg-desktop-portal-gtk` no está instalado (FileChooser=gtk): `sudo emerge --ask sys-apps/xdg-desktop-portal-gtk` (lo ejecuta el usuario).
* `QuickConfig.qml` vuelve a Ajustes de default (end-4) (§3.73); Retro y Breeze (Kde plasma) no lo muestran.


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
* **Dos About distintos:** el del menú Retro es Fastfetch con presentación Omarchy (§3.47). El de Ajustes de default (end-4)/Breeze mantiene las tarjetas y enlaces BWM; el usuario pidió expresamente cambiar sólo el primero.
* Navegación (§3.73): `settings.qml` (default (end-4)) sigue a end-4: Quick, General, Bar, Background, Interface, Services, Advanced y después las de BWM (Keybinds, Autostart, Display, Workspaces, Default apps, Style, Cursor, About); sin Temas ni Plugins (son de Omarchy: siguen en Retro y en `plasmaSettings.qml`). Modo glass: `settings/shared/GlassModeSection.qml` (módulo `qs.modules.settings.shared`), en General para default (end-4) y en Estilo para Breeze; Retro lo ofrece en su menú → Estilo → Ventanas → Glass. Estilo conserva fuentes y arranque en las páginas compartidas. Retro ya no carga estas páginas (§3.136).
* About: tarjeta Distro con nombre/versión/logo detectados de os-release y enlace de inicio; tarjeta WM con BWM, logo del arranque y accesos a GitLab/GitHub. Documentation abre README.es.md en GitLab; Issues abre los de GitHub; Star tiene un GIF local de 32 fotogramas y abre GitHub. Sin botones de ayuda/documentación/bugs/privacidad de la distro ni Donate. Discussions omitido: GitHub API `has_discussions=false`, comprobado el 2026-10-27.
* `SystemInfoData.js` parsea comillas simples/dobles y valores sin comillas como datos, sin ejecutar shell. `SystemInfo.qml` aplica al cargar FileView, vigila cambios y recurre a `/usr/lib/os-release` si falta `/etc/os-release`. El lector anterior no reconocía el formato con comillas simples de Gentoo. Logo simbólico con fallback incluido y ColorOverlay para que sea visible sobre fondos oscuros.

### Licencias y avisos de terceros
* `THIRD_PARTY_NOTICES.md` identifica componentes, fuentes y cuestiones pendientes; textos en `licenses/`,
  fuentes en `assets/fonts/licenses/`, Bibata en cada carpeta, GPL del shell en `config/quickshell/ii/COPYING`
  y BSD de hyprbars en `src/breezebars/LICENSE`. El instalador copia avisos a `~/.local/share/doc/bwm`
  (o `$XDG_DATA_HOME/doc/bwm`) y los de fuentes a `~/.local/share/fonts/bwm-licenses`.
* No anunciar todo el repo como MIT: shell derivado de end-4 GPL-3.0, hyprbars BSD-3-Clause,
  Omarchy MIT, Pywalfox MPL-2.0, fuentes OFL y otros. La procedencia exacta de imágenes, iconos,
  fuentes correspondientes a algunos binarios y licencia de código independiente siguen pendientes.

### 2.9 Instalador, requisitos y bienvenida
* **BWMenu en el lanzador (§3.307, §3.309):** la entrada común `org.bwm.menu.desktop` permite buscar **BWMenu** en las tres skins. El instalador y el inicio de sesión la registran en `${XDG_DATA_HOME:-$HOME/.local/share}/applications`. Instalada también en esta sesión; apertura desde la entrada de aplicación comprobada.
* **Añadir skins en BWMenu (§3.126–127):** catálogo independiente `saselandia/bwm-skins` creado y publicado en GitHub/GitLab, checkout `/mnt/HDD1TB/Projects/bwm-skins`. Sólo las tres actuales se incluyen en BWM; las adicionales tendrán releases propias. Índice v2 `catalog/skins.json` con id `bwm-extra-skins`, inicialmente vacío; generador `scripts/bwm-skin-catalog.py build --catalog-root /ruta/bwm-skins`. BWMenu lo consulta online con respaldo GitLab, caché separada de una hora y fallback vacío. El instalador automático y la carga completa de módulos externos siguen pendientes; «Ver instalación» abre las instrucciones publicadas.
* **Semáforos de BWMenu (§3.123–125):** `bwm_versions.version_state()` compara con `referenceVersion` (registro local versionado en `skins/requirements.json`; fecha/base BWM en `referenceEnvironment`), con fallback a `check.tested`/`check.min`. Verde / Correcta si coincide o pasa una comprobación sin referencia; rojo / Falta si falta/es inferior a la referencia/incompatible; naranja / Desactualizado si la referencia queda por debajo de la instalada. Los mínimos `check.min` siguen controlando la instalación y activación de skins; el semáforo no los eleva. No consulta versiones remotas. La luz de cada skin agrega núcleo + obligatorios + opcionales (rojo > naranja > verde). Tabla compacta `DependencyTable.qml` con las superficies del tema, letras negras en fondos claros y blancas en oscuros; detalles al pulsar una fila. Registro actualizado el 2026-11-10: 54 referencias, incluidas Hyprland 0.56.2, Quickshell 0.3.2, Qt 6.11.2 y Python 3.14.7.
* **Skins = carpetas** en `config/hypr/skins/`: `requirements.json` (núcleo `requires`/`recommends` + catálogo: etiqueta, para qué, comprobación y paquete por familia de distro, con `guru:`/`hyproverlay:` en Gentoo, `aur:` en Arch, `copr:` en Fedora) y una carpeta por skin con su `skin.json` (`default/`, `retro/`, `plasma/`: identidad, variable de ventanas `windows` = `tiling`/`traditional` + bloque `traditional`, `palette` matugen/omarchy/breeze, `defaultTheme`, temas, `look`, `bar`, `fonts`, mapa de archivos `parts`, requisitos). Plantilla `_template/skin.json` y guía `skins/README.md`. `scripts/bwm_skins.py` los carga para el gestor (que ya no tiene datos de skin en Python), `bwm_windows.py`, el comprobador y la bienvenida. Tabla generada en `docs/REQUIREMENTS.md`; qué es una skin y cómo se añade en `docs/SKINS.md` (la «wiki»).
* **`scripts/bwm-requirements.py check [--skin] [--json] [--pre-install] [--distro]` / `skins`**: sólo lee el sistema (comandos, versiones mínimas de Hyprland/Quickshell, módulos QML y plugins de Qt, Python/Pillow, fuentes, pkg-config, commit de Hyprland embebido en `breezebars.so`) y genera los comandos de instalación de la distro detectada por os-release. `--pre-install` no cuenta lo que pone el instalador (fuentes) ni el plugin si se puede compilar.
* **`install.sh`**: paso 1 = comprobación; si falta algo imprime los comandos y sale con 1 **sin tocar nada**. `--check`, `--skins default,retro`, `--spicetify/--no-spicetify` (antes descargaba Spicetify sin preguntar; ahora sólo si Spotify está y con confirmación). Enlaza `~/.local/bin/bwm` al repo, enlaza los shims de Omarchy (`bwm-plugin.sh catalog`), activa la bienvenida, compila hyprbars si no coincide con el Hyprland en uso y activa `bwm.theme.css` en Vesktop con `bwm_omarchy.vesktop_enable_theme()` (antes copiaba `material-you.theme.css` y lo ponía en Quick CSS, contrario a §3.35).
* **Comando `bwm`** (`config/hypr/scripts/bwm`): sin argumentos abre la bienvenida (o, sin Wayland/Quickshell, los requisitos en texto); `check`, `skins`, `skin [id]` (se niega si faltan requisitos), `startup on|off|status`, `welcome --startup`.
* **BWMenu (§3.119, §3.122):** galería visual de skins y diagnóstico con `+` y `-` a la vez (cualquier orden, teclado normal o numérico). `bwm menu`/`bwmenu` abre la ventana autónoma `quickshell/bwmenu/` (instancia aparte de `ii`); colores, fuentes y formas siguen los temas originales en vivo mediante `bwm_menu_appearance.py`, sin guardar otro formato de tema. Vistas previas de manifiestos, tarjeta activa con su fondo/paleta, aplicación de skins, versiones/requisitos, buscador, recuperación y registros. La consola original sigue independiente de Qt/Quickshell con `bwm menu --tui`, o `--open --tui` para Kitty limpio; también se abre automáticamente si la ventana gráfica falla. Revisión `bwm version`, requisitos `bwm check --versions`; guía `docs/BWMENU.md`. Si cae todo Hyprland, Ctrl+Alt+F3 y `bwm menu --tui`. Sin requisitos nuevos. Mascota original animada en `bwmenu/BwmMascot.qml`, con variantes en `mascot/{retro,default,plasma}/Character.qml`; sigue la paleta y pausa al ocultarse (§3.129, §3.132–133). Retro: patinete, fondo transparente y estela hacia atrás, todo con colores del tema; Breeze: cabecera gris; default: superficies Material You/end-4. Las tres comparten silueta y cuatro marcas; clic/Intro/Espacio las desplaza lateralmente y hacia arriba, además de su gesto propio. El botón × superior derecho cierra; diagnóstico con Ctrl+R y catálogo con Actualizar/Ctrl+R. Esquinas rectas en tarjetas y semáforos también en los selectores de Dependencias.
* **Qué se conserva entre skins** (tabla en `docs/SKINS.md`): red/Bluetooth, cursor, Kelvin, apps predeterminadas, workspaces (los mismos 1–N; `bar.workspaces.shown` común y la barra Retro muestra 1..shown, ya no 1-5 fijos), pantallas y escala, autoarranque, servicios (`bar.weather`), interfaz (logo, `overview`, `osd`, `lock`, `windows`, `wallpaperSelector`) y General. Propio de cada skin: `appearance` (fuentes incluidas), `background`, `bar` (salvo `workspaces.shown`, `weather`, `topLeftIcon`), `dock`, `panelFamily`, `waffles`. Sin protección de volumen («earbang»).
* **Bienvenida** `quickshell/ii/bwmWelcome.qml`: ventana `qs -p` aparte con pasos a la izquierda (Bienvenida, Skins, Añadir skins, Listo) como Calamares. Agradece, explica el propósito, muestra sistema/Hyprland/skin activa; tarjetas desplegables por skin con punto/etiqueta verde si tiene sus requisitos, tema por defecto, requisitos con ✓/✗, comandos copiables (`wl-copy`), «Activar esta skin» (`bwm-theme-manager.py set`, relee a los 14 s) y enlace al original; «Añadir skins» con la wiki. Interruptor «Mostrar al iniciar sesión» → `~/.config/bwm/welcome.json` (`showAtStartup`; sin archivo = activada). `autostart.sh` la lanza 4 s después de Quickshell. `FirstRunExperience.qml` ya no abre la bienvenida de illogical-impulse ni pone su fondo por defecto.

---

## 3. 📋 Historial (cronológico)

Peticiones del usuario y cómo se resolvieron, en el orden en que se hicieron (sesiones con Antigravity, Gemini y Claude Code). Los números de sección se citan como §3.N.

### 1. Sincronización y Configuración del Proyecto en Antigravity
* Integración del repositorio en Antigravity (`hyprland-de`).
* Configuración de la sincronización de avances y commits hacia ambos repositorios remotos (GitLab y GitHub).

### 2. Comportamiento de Pantalla Completa en KDE Plasma (`Alt + Enter`)
* **Petición:** Al pulsar `Alt + Enter` en el estilo Breeze (Kde plasma), la ventana debe maximizarse ocupando todo el espacio de trabajo pero **manteniendo la barra de tareas de Quickshell siempre a la vista** (estilo maximizado nativo de KDE), mientras que en los temas `default` y `retro` debe conservar la pantalla completa tradicional (ocultando barras).
* **Solución:** Ajuste en `config/hypr/scripts/quick-tile.py` y `config/hypr/modules/user_binds.lua` para verificar el estilo activo y despachar `quick-tile.py maximize` en lugar de `fullscreen 0` cuando el tema es Plasma.

### 3. Reasignación de Atajos de Quick Tiling / Snapping en KDE Plasma
* **Petición:** Los atajos de snapping a bordes (`Super + flechas`) debían convertirse en `Ctrl + flechas` (`Ctrl + Up / Down / Left / Right`), exclusivo para el estilo Breeze (Kde plasma).
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

### 12. Applet Bluetooth estilo Breeze (Kde plasma) (Bluedevil) en Breeze Dark
* **Petición:** GUI de Bluetooth idéntica a la de Plasma 6, abierta desde el botón Bluetooth de la barra Plasma.
* **Solución:** `config/quickshell/ii/modules/ii/plasmaBluetooth/PlasmaBluetooth.qml` (registrado en `panelFamilies/IllogicalImpulseFamily.qml`):
  - Cabecera con interruptor, "Emparejar dispositivo…" (escaneo 60 s con barra indeterminada) y botón Configurar (`Config.options.apps.bluetooth` → `blueman-manager`).
  - Secciones *Conectados / Disponibles / Dispositivos encontrados*, filas desplegables con acción por defecto (Conectar / Desconectar / Emparejar), detalles (nombre, dirección, tipo, batería, confianza, adaptador) y botones Confiar / Olvidar.
  - Placeholders para sin adaptador, Bluetooth desactivado y sin dispositivos.
  - Iconos Breeze Dark empaquetados en `config/quickshell/ii/assets/icons/breeze-dark/bluetooth/`.
  - Botón de la barra: clic izquierdo abre el applet (anclado encima del botón), clic central activa/desactiva Bluetooth. Estado en `GlobalStates.plasmaBluetooth*`. IPC: `qs -c ii ipc call plasmaBluetooth toggle|open|close`.
  - Requisitos nuevos: `bluez` (+ `bluez-utils` en Arch) y `blueman`.

### 13. Applet de Redes estilo Breeze (Kde plasma) (plasma-nm) en Breeze Dark
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
* **Lanzador único:** `config/hypr/scripts/open-settings.sh` abre `plasmaSettings.qml` en Plasma y `settings.qml` en default (end-4)/Retro (Super+I, botón de la barra lateral, `open-autostart.sh`; respeta `SETTINGS_PAGE`).
* ⚠️ **Superado en parte por §3.52** (lock, osd, overview, wallpaperSelector y windows pasan a ser comunes).
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
* **Iconos por estilo:** `scripts/bwm_icons.py` (Plasma `breeze-dark`, Retro `BWM-Papirus` = Papirus-Dark con carpetas del color más cercano al acento, default (end-4) Adwaita) + `~/.config/qt6ct/qt6ct.conf` (en Retro también la fuente mono del sistema para las apps Qt).
* **Qt con la paleta:** plantilla `matugen/templates/qt6ct-colors.conf` → `~/.config/qt6ct/colors/bwm.conf` (la rellenan matugen, Breeze y Omarchy); `environment.lua` usa `QT_QPA_PLATFORMTHEME=qt6ct` si `/usr/bin/qt6ct` existe.
* **Steam:** Adwaita-for-Steam (MIT) clonado en `~/.local/share/steam-adwaita`; plantilla `steam-adwaita.css` (formato actual `--adw-*-bg-dark`, no los `-rgb` del hook) → `scripts/steam-theme.sh` lo instala con `--color-theme bwm --color-scheme dark` y, en Retro, `general/no-rounded-corners` + `--custom-css` con la fuente mono. Steam lo aplica al reiniciarse.
* **Arranque/inicio de sesión:** temas Plymouth y SDDM de Omarchy (MIT) en `config/hypr/omarchy/boot` con logo BWM; `scripts/bwm_boot.py render` los recolorea con el estilo activo en `~/.local/state/bwm/boot`; `sudo scripts/install-boot-theme.sh --plymouth | --sddm [--enable-sddm] | --revert | --auto | --no-auto` los instala o deshace Plymouth. **Automático:** `bwm_boot.py render` se lanza tras cada cambio de fondo (`set-wallpaper.sh`) y de tema (`bwm-theme-manager.py`) y sólo reescribe `~/.local/state/bwm/boot/.stamp` si el resultado cambia; `--auto` instala una copia root del script en `/usr/local/sbin/bwm-boot-theme` y `bwm-boot-theme.path/.service` (vigila el `.stamp`, espera 20 s sin cambios, copia sólo archivos de tema válidos y, si Plymouth está instalado —marcas en `/var/lib/bwm-boot-theme`—, rehace el initramfs con las comprobaciones, a prioridad mínima). Tras cambiar el script en el repo hay que repetir `--auto`. **Ojo:** aquí `grub.cfg` no se puede regenerar con `grub-mkconfig` (la línea `rd.luks…`/`root=` no está en `/etc/default/grub`); el script añade `splash` (sin `quiet`) a las líneas `linux` del `grub.cfg` existente (copia `.bwm-backup`) y rehace el initramfs con los mismos argumentos de dracut que tenía + plymouth (copia `.bwm-backup`). El initramfs incluye la llave LUKS (`/etc/dracut.conf.d`). No hay gestor de sesión: autologin en tty1 + `~/.bash_profile`.
* **SDDM como en Omarchy (`--sddm`, `--all`):** mismo `Main.qml` que Omarchy; el saludo corre en un Hyprland mínimo (`/usr/share/sddm/bwm-hyprland.lua`, copia de `default/sddm/hyprland.lua` de Omarchy) que el script root escribe validando `greeter.conf` (teclado y monitores `desc:` que genera `bwm_boot.py`), `/etc/sddm.conf.d/10-bwm-theme.conf`, `10-bwm-wayland.conf` (`DisplayServer=wayland`, `CompositorCommand=start-hyprland -- --config …`), `99-bwm-login.conf` (recordar usuario/sesión) y `/var/lib/sddm/state.conf` (sesión `hyprland.desktop`). `--enable-sddm` aparca el autologin de getty en `/var/lib/bwm-boot-theme/`; `--disable-sddm` lo devuelve; `--autologin` = autologin de SDDM (lo que hace Omarchy con disco cifrado). `--all` = `--sddm --enable-sddm --auto`. `install.sh` lo ofrece al final (`--login`/`--no-login`). `~/.bash_profile` sólo lanza Hyprland en un login de texto en tty1 (SDDM también lo lee). Probado: el tema en `sddm-greeter-qt6 --test-mode` y el Lua con `Hyprland --verify-config`.
* ⚠️ **Superado por §3.97** (SDDM entra solo en todas las skins). **Inicio de sesión por estilo (2026-10-24):** Retro → contraseña en SDDM (Omarchy) y `LockScreen.qml` no vuelve a bloquear si `Appearance.isRetro` y la sesión viene de SDDM (`XDG_SESSION_PATH` `/org/freedesktop/DisplayManager…`); default (end-4)/Plasma → autologin de SDDM y el bloqueo de Quickshell (`lock.launchOnStartup`) hace de inicio de sesión. `bwm_boot.py` escribe `theme=` en `greeter.conf` y `apply_login_mode()` (en `--sddm` y en el servicio `--sync`) pone o quita `/etc/sddm.conf.d/autologin.conf`; `--autologin` lo fija siempre (`/var/lib/bwm-boot-theme/autologin-always`).
* **Arranque lento (25 s) de Quickshell y del bloqueo:** `xdg-desktop-portal` tenía `FileChooser=nautilus` con un `~/.local/share/xdg-desktop-portal/portals/nautilus.portal` hecho a mano, pero Nautilus no implementa ese portal: al arrancar lo activaba y esperaba 25 s (`Settings.ReadAll` de Quickshell daba `NoReply`). `config/xdg-desktop-portal/*.conf` usa `FileChooser=gtk`. Además `autostart.sh` reintenta `swww img` hasta que ningún monitor quede en negro (entrando desde SDDM el fondo no se ponía).
* **Incidente 2026-10-23 (Plymouth):** la primera versión rehízo el initramfs con el módulo plymouth de dracut, que metió `amdgpu` (iGPU del Ryzen): 182 → 526 MB (GRUB lo lee del disco cifrado: ~27 s de cargador) y la iGPU arrancó antes que la NVIDIA, así que los conectores pasaron de DP-1/DP-2 a DP-2/DP-3 y las reglas de monitor por nombre cayeron en el monitor equivocado (los dos a 1080p en 0x1080, superpuestos). Arreglo: `monitors.lua` y `monitor-manager.py` usan sólo `desc:`; `--plymouth` conserva los drivers de GPU del initramfs original (`--omit-drivers`) y descarta el nuevo si crece más de un 50 %; `--revert` restaura las copias.
* ⚠️ **Superado por §3.97** (bloqueo de Omarchy 4 en `modules/ii/omarchyLock`). **Bloqueo de pantalla en Retro:** `modules/ii/lock/OmarchyLockSurface.qml`, copia del `hyprlock.conf` de Omarchy (fondo desenfocado, una caja cuadrada de 650×100 con borde de 4 px, monoespaciada de 32 px, «Enter password», borde de acento al comprobar, «(N)» intentos fallidos). `Lock.qml` la usa si `Appearance.isRetro`; los otros estilos siguen con el bloqueo Material You.
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
* **Aplicaciones predeterminadas** (Ajustes → default (end-4) apps / Aplicaciones predeterminadas, en las dos apps de ajustes): `modules/settings/DefaultAppsConfig.qml` + `hypr/scripts/default-apps.py list|set` (terminal → `~/.config/bwm/default-apps.json`, `apps.terminal`, `xdg-terminals.list`; navegador `xdg-settings`; archivos/editor `xdg-mime`; gestor de tareas → `apps.taskManager`, btop/htop en la terminal). `hypr/scripts/bwm-terminal [--class X] [--title T] -- cmd` abre la terminal predeterminada con los flags de cada una (kitty, foot, alacritty, ghostty, wezterm…); lo usan el Gestor de tareas de Retro y los shims de Omarchy. Regla de ventana `omarchy-floating-terminal` (flota, 875×600, centrada).
* **Audio, red y Bluetooth de Omarchy en Retro (2026-10-25):** `modules/ii/bar/omarchy/{audio,network,bluetooth}/` = los paneles de primera parte de Omarchy (MIT), fijos en la barra Retro (`omarchyStatus`, sustituyen a los botones de BWM, que quedan de respaldo). Sus scripts (`omarchy-audio-*`, `omarchy-bluetooth-*`, `omarchy-network-band/-status/-captive-portal`) van copiados en `omarchy-shims`, más sustitutos `omarchy-cmd-present`, `omarchy-launch-webapp`, `omarchy-audio-tuning` y un `omarchy-dns` de sólo lectura (el de Omarchy cambia el DNS del sistema como root). IPC `omarchy.audio|network|bluetooth open|close|toggle`. `OmarchyPlugins.summon()` es un stub (el test de velocidad es un overlay de omarchy-shell).
* **Ajustes rápidos centrados en Retro:** `sidebarRight` en Retro es una ventana centrada (ancho `sidebarWidth`+60, alto el del contenido, clic fuera/Esc cierra) sin notificaciones (`CenterWidgetGroup`) ni pestaña Calendario (`BottomWidgetGroup.tabs` filtra); se abre desde el menú (Ajustes → Ajustes rápidos) o la app «Quick Settings / Ajustes rápidos» (`hypr/omarchy/applications/bwm-quick-settings.desktop`, sólo en Retro como el Gestor de tareas: `bwm_omarchy.RETRO_APPS`). Ningún botón de la barra Retro la abre. El menú de Retro abre las apps `Terminal=true` (btop++) en la terminal predeterminada (`bwm-terminal`); `autostart.sh` crea/quita las apps de Retro al arrancar según el estilo.
* **Revisión de los commits 7e1273f/5e334e7 (otra sesión, 2026-10-25):** panel de pantallas (`bar/omarchy/monitor/Panel.qml`) rehecho en lo roto: pestañas propias (el `Button` de `qs.Ui` sólo mide su `text`, los hijos se salían), todo lo de debajo (brillo, escalado, resolución, refresco, orientación, principal, apagar) es de la pantalla seleccionada; brillo en un mapa `brightness` reactivo (antes mutaba `modelData`), varios cambios seguidos se aplican todos (un `Process` sólo corre uno), seleccionar ya no enfoca (usaba `hyprctl dispatch focusmonitor`, sintaxis antigua); luz nocturna y tamaño de texto como ajustes de todas las pantallas. Energía: título roto (`power.power` no existe), perfiles ocultos sin `powerprofilesctl` (el shim inventaba tres que no aplicaba). `RegionSelection.qml` tolera que el detector de imágenes no devuelva JSON.
* **Menú / paleta de comandos de Omarchy en Retro (2026-10-25):** `modules/ii/omarchyMenu/omarchy/{Menu.qml,MenuModel.js}` = el plugin `omarchy.menu` de Omarchy (MIT), con el catálogo de BWM `hypr/omarchy/bwm-menu.jsonc` (formato omarchy-menu.jsonc: ids con puntos = jerarquía, `action`/`target`/`provider`, `when`/`checked`/`disabled` en bash evaluados en lote, alias) + extensión del usuario `~/.config/bwm/extensions/menu.jsonc`; se recargan solos. Cambios: rutas de catálogo, ancho 360, paquetes con `qlist` (Gentoo) en vez de pacman. `OmarchyMenu.qml` es ahora el anfitrión (`AppLibrary.qml` = `shell.appLibrary` sobre AppSearch, apps de terminal con `bwm-terminal`; `summon` de overlays vía `OmarchyPlugins`). IPC `omarchyMenu toggle|open|close|summon <ruta>|refresh`; comando `omarchy-menu [ruta]` en los shims; proveedor `fonts` con `omarchy-font-current/list/set` → `font-set.sh`. Estado para los ✓: IPC `bwmIdle isInhibited|toggle` y `bwmNotifications isDnd|toggleDnd`.
* **Capturas de Omarchy en el menú de Retro (2026-10-25):** Acciones → Capturar (`trigger.capture.*` en `bwm-menu.jsonc`) con los scripts de Omarchy copiados en `omarchy-shims`: `omarchy-capture-text` (OCR con tesseract, todos los idiomas instalados), `omarchy-capture-qr` (zbarimg, al portapapeles con `--sensitive`), `omarchy-capture-screenrecording` (+`-process`, `-with-webcam`, `webcam-list/-resize`, `omarchy-capture-region`; gpu-screen-recorder o wf-recorder, audio de escritorio/micro, webcam con mpv+v4l2-ctl), `omarchy-menu-select` (usa el modo select del menú: `omarchy-shell shell summon omarchy.menu <json>` → IPC `omarchyMenu openPayload`), `omarchy-i18n` (+`plural.jq`, `cli.json` en/es-MX en `Commons/omarchy`) y el `omarchy-notification-send` real (las acciones de sus avisos son indicaciones propias de Omarchy: aquí salen sin botón). `scripts/bwm-require.sh <cmd> <paquete> … -- acción` avisa del paquete de Gentoo que falta. El indicador de grabación detecta también gpu-screen-recorder y lo detiene. `omarchy-shell` ignora `omarchy.indicators refresh`.
* **Notificaciones de Omarchy en Retro (2026-10-25):** `modules/ii/omarchyNotifications/` = el servicio `omarchy.notifications` de Omarchy (MIT: tarjetas agrupadas bajo la barra, glifos, acciones `--action` de `omarchy-notification-send` como «Abrir» al terminar una grabación, códigos copiables, No molestar, historial en `~/.local/state/omarchy/notifications`), cargado sólo en Retro (`IllogicalImpulseFamily.qml`, `Config.ready && Appearance.isRetro`). El `NotificationServer` de BWM (`services/Notifications.qml`) va en un `LazyLoader` con `Config.ready && !Appearance.isRetro`: sólo uno tiene `org.freedesktop.Notifications`; al cambiar de estilo Quickshell se reinicia y, si no, Quickshell reintenta el registro cuando el otro suelta el nombre. `OmarchyNotifications.qml` le da al servicio la posición/grosor de la barra Retro y sincroniza su No molestar con `Notifications.silent` (indicador, menú, IPC `bwmNotifications`). `omarchy-hyprland-focus-app` en los shims (clic en un aviso enfoca la app). **swaync** también reclama ese nombre (antes lo tenía siempre): `autostart.sh` no lo arranca en Retro y `bwm-theme-manager.py` lo cierra al entrar en Retro y lo vuelve a lanzar al salir.
* **Indicadores de Omarchy** junto al reloj (`OmarchyIndicators.qml`): grabando (rojo, `wf-recorder`), luz nocturna, no molestar, mantener despierto; sólo los activos, los inactivos al 45 % al pasar el ratón por el grupo o el reloj. Reloj con el formato de Omarchy `dddd HH:mm` (fecha larga al pasar el ratón).
* **Workspace mágico (Alt+S):** en `RetroBarContent.qml` los números se atenúan y aparece `[ 󰜗 magic ]` enmarcado en el acento (como la píldora del estilo default (end-4)); clic lo oculta. Usa `WorkspaceModel.specialWorkspace*`.
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
  - Se inicializó `OmarchyPlugins` en `shell.qml` (`Component.onCompleted`), garantizando que la captura en segundo plano del portapapeles (`capture.sh`) y los atajos globales `Super + V` y `Super + .` funcionen de inmediato en default (end-4), Plasma, Retro o Waffle.
* **Solución Definitiva al Pegado en Hyprland 0.55+ Lua:**
  - **Ejecución de Dispatchers:** En Hyprland 0.55+, llamar a `hl.dsp.send_shortcut(...)` en Lua sólo construye el descriptor; para despacharlo debe evaluarse con `hl.dispatch(...)` (`hyprctl eval 'return hl.dispatch(hl.dsp.send_shortcut({ mods = "...", key = "..." }))'`).
  - **Detección inteligente de Ventana Destino:** Se consulta la clase de la app activa con `hyprctl activewindow -j`. Si es una terminal (`kitty`, `alacritty`, `foot`, `wezterm`, etc.) se despacha `Shift + Insert`; si es una app gráfica, navegador o Electron (`Telegram`, `Discord`, `Chrome`, `Firefox`, `Slack`, etc.) se despacha `Ctrl + V`.
  - **Persistencia de `wl-copy`:** Se eliminó la destrucción prematura con `kill` tras 200 ms que cortaba la negociación Wayland (`wl_data_device.data_offer`) antes de que apps pesadas leyeran el buffer.
  - **Temporizado de foco tras dismiss:** Se ajustó la espera a 220 ms para garantizar que el compositor ha desenfocado la capa layer-shell (`OverlayWindow`) y devuelto el foco de teclado a la app previa antes de inyectar las teclas.

### 27. Verificación y Optimización del Doble Sistema de Notificaciones (KDE/default (end-4) vs Retro)
* **Petición / Preocupación:** Verificar si tener dos servicios de notificaciones distintos (el servidor estándar de BWM/KDE junto al de Retro) causa conflictos en el sistema o penalizaciones de rendimiento en segundo plano.
* **Diagnóstico y Arquitectura:**
  - Se inspeccionó `config/quickshell/ii/panelFamilies/IllogicalImpulseFamily.qml` y `services/Notifications.qml`.
  - Se comprobó que ambos servicios implementan el protocolo estándar D-Bus `org.freedesktop.Notifications`.
  - La carga está gobernada por `extraCondition` en los Loaders de Quickshell:
    - Servidor Retro (`omarchyNotifications`): únicamente activo cuando `Config.ready && Appearance.isRetro`.
    - Servidor default (end-4)/Plasma (`Notifications.qml`): únicamente activo cuando `Config.ready && !Appearance.isRetro`.
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
* **Vocabulario:** lo que antes se llamaba «tema» (default (end-4), Retro, KDE Plasma) es ahora **estilo** (*skin* en inglés); **tema** es lo de dentro de un estilo (los temas de Omarchy en Retro). Cambiado en textos visibles (menú de Retro «Estilo» / «Selector de estilos…» / «Temas Retro (Omarchy)», atajo Alt+T «Selector de estilos», ayuda de `bwm-theme-manager.py`, Ajustes → Estilo, «Estilo global» en Plasma), comentarios y documentación. Nombres de archivos, comandos e identificadores sin cambiar; atajos iguales.
* **Vesktop:** Omarchy no tematiza Discord y omarchy-theme-hook sólo cambia colores cargando un CSS remoto (base16-discord), así que hay tema propio: `hypr/omarchy/themed/vesktop.theme.css.tpl` («BWM Omarchy TUI»: colores de `colors.toml`, monoespaciada, sin redondeos, paneles enmarcados, selección invertida con el acento, caja de mensaje con prompt `❯`). `bwm_omarchy.apply_vesktop()` lo escribe en cada tema Retro (estático o dinámico). Un único archivo para todos los estilos, `themes/bwm.theme.css` (matugen lo escribe en default (end-4) como «BWM Material You», Plasma como «BWM Breeze Dark»), más `settings/quickCss.css`: Vencord los recarga en vivo. `vesktop_enable_theme()` cambia una vez `enabledThemes` de `material-you.theme.css` a `bwm.theme.css` (Vencord guarda sus ajustes al salir: cierra Vesktop, edita y lo reabre en su sitio).
* **Firefox:** la capa TUI (`overlays/firefox.css`) añade pestaña activa invertida (como tmux) y prompt `❯` en la barra de direcciones. Firefox sólo lee el CSS al arrancar: `restart_firefox()` lo reinicia si `~/.cache/material-you-firefox.css` es más nuevo que el proceso (espera a que el CSS deje de cambiar y usa un candado para que el cambio de estilo y el de paleta no reinicien dos veces); lo piden `bwm-theme-manager.py` en cada cambio de estilo y Retro en cada cambio de tema. Relanza sin las URL con las que se abrió (antes reabría la de inicio de sesión de Claude).
* **`restart_app()`** (bwm_omarchy): cierre con SIGTERM, edición opcional, relanzar y devolver cada ventana a su workspace (también especiales) y, si flota, posición y tamaño; casa ventanas por título y luego por orden, distinguiendo las viejas por PID.
* **Selector de estilos en Retro:** Alt+T en Retro abre el mismo carrusel 3D que los temas (`ImagePicker.qml`, `source: "skins"`, `skinMode`), con miniaturas del fondo de cada estilo (`hypr/scripts/skin-switcher.sh --print-rows`, PNG 1280×800 en `~/.cache/bwm/skin-switcher/`, la etiqueta es el nombre del archivo). default (end-4) sigue con rofi y Plasma con su «Estilo global».

### 34. Todas las apps de Omarchy en Retro, Vesktop más limpio y capturas en el selector de estilos (2026-10-26)
* **Plantillas de Omarchy:** las 16 de `default/themed` que faltaban (alacritty, chromium, claude, fcitx5, foot, ghostty, gum_env, helix, hermes, hyprland, hyprland-preview-share-picker, keyboard.rgb, neovim, obsidian, pi, t3code, vscode-theme) en `hypr/omarchy/themed/` (README con origen). `complete_colors()` añade `theme_type` y los alias `purple`/`magenta` que esas plantillas usan.
* **`hypr/scripts/bwm_omarchy_apps.py`** (lo llama `apply_retro_palette_colors` en cada tema Retro): `render_theme_dir()` escribe `~/.local/state/bwm/omarchy/theme` (archivos propios del tema estático primero —neovim.lua, vscode.json, btop.theme…— y plantillas para lo demás; borra lo que dejó el tema anterior) y `~/.local/state/omarchy/current/theme` apunta ahí (antes apuntaba a la carpeta del tema en el repo). `apply_apps()`, aunque la app no esté instalada: alacritty/ghostty/foot incluyen el tema desde su config (creada si falta), Helix `theme = "omarchy"`, Neovim `lua/plugins/theme.lua` si hay LazyVim, VS Code/VSCodium/Cursor extensión generada «Omarchy» (o la del tema estático si ya está instalada; si no, se intenta instalar en segundo plano y sólo se selecciona si funciona: Open VSX no tiene, p. ej., la de Lumon), Obsidian por bóveda, Claude Code `custom:omarchy`, pi/Hermes/T3 Code si existen, fcitx5, share-picker, tmux si hay sesiones. Chromium (política root), gum, teclado RGB y hyprland.lua quedan generados. `restore_apps()` al salir de Retro devuelve los temas de Helix, Claude Code, pi y los editores (`app-restore.json`). btop usa el `btop.theme` del tema si lo trae. El viejo `workbench.colorCustomizations` de BWM se quita (pisaba el tema).
* **Vesktop:** fuentes de reserva para símbolos (Noto, DejaVu, FreeSerif, emoji); botones de icono (micrófono, auriculares, ajustes, barras) planos sin marco, marco de acento sólo en botones de diálogos/formularios; panel de cuenta plano sin imagen de fondo; menús con el elemento activo invertido.
* **Selector de estilos:** capturas de lo que imita cada estilo en `assets/skin-previews/` (README con origen): end-4/illogical-impulse (default (end-4)) y Plasma 6.8 de kde.org (KDE Plasma); Retro usa la `preview.png` oficial del tema de Omarchy activo (Tokyo Night con paleta dinámica). Miniaturas en `~/.cache/bwm/skin-switcher/<hash>/` (la ruta cambia con la imagen para que Quickshell no muestre la de caché).

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
* **Stremio:** nueva plantilla `config/matugen/templates/stremio.css`, post_hook `scripts/stremio-theme.py` y overlay Retro `omarchy/overlays/stremio.css`. default (end-4), Plasma y Retro (estático/dinámico) usan sus renderizadores existentes. El hook configura sólo `com.stremio.Stremio` cuando está instalado (véase §3.41): NODE_OPTIONS carga `stremio-theme.cjs`, BWM_STREMIO_CSS señala `~/.local/state/bwm/stremio/theme.css`, dos accesos de sólo lectura al directorio de scripts y de paleta.
* **Puente específico de Stremio Linux:** sólo en el Node del servidor oficial, añade un script al HTML de inicio de `web.stremio.com` que éste sirve por su proxy local; lee el CSS cada 2 s sin recargar la página. Conserva origen/sesión; no modifica el Flatpak, los vídeos, las API ni otros destinos del proxy. La primera vez reabre Stremio en su workspace salvo fullscreen/reproducción MPRIS; después no reinicia. El marco GTK cambia al abrir. El primer reinicio puede cambiar la posición en el mosaico (se observó en workspace 10).
* **Pruebas:** 7 tests HTTP en `scripts/tests/stremio-theme.test.cjs` (HTML normal/gzip/deflate/Brotli, errores, límite de tamaño, tráfico no afectado, CSS en vivo); compilación Python; 23 paletas Retro y Breeze renderizadas sin placeholders pendientes. Capturas recortadas verifican Ethereal → Tokyo Night → Ethereal con el mismo PID y sesión. Se restauró Ethereal. No se hizo un cambio global de estilo ni de wallpaper durante esta prueba.
* **Mantenimiento:** la ruta de inicio es específica de Stremio Linux actual; una actualización puede requerir adaptarla. Alcance, pruebas y desactivación en `docs/STREMIO_THEMING.md`. No presentar el tema GTK como soporte del contenido web ni afirmar que toda la Tienda de Steam está tematizada.


### 41. Integración opcional de Stremio en el instalador y prueba de la barra de Steam (2026-10-26)
* `stremio-theme.py` comprueba Flatpak y `flatpak info com.stremio.Stremio` antes de crear estado/overrides. `install.sh` ejecuta `--setup-only` tras generar la paleta, sin reiniciar apps. Al reaplicar Retro o Plasma se ejecuta el hook de Stremio aunque el CSS no cambie, para detectar una instalación posterior. Sin Stremio no se toca su configuración.
* 3 tests Python comprueban ausencia de Flatpak, ausencia de Stremio y setup sin reinicios; se mantienen los 7 tests HTTP del puente. Tema de Steam: se cambió sólo su CSS a Tokyo Night y se verificó visualmente el cambio de la barra superior tras reiniciar; después se restauró Ethereal. No confundir esta barra CEF con Qt.
* `steam-theme.sh` deja de reiniciar si falla el instalador y guarda los errores del reinicio en `~/.local/state/bwm/steam/restart.log` en vez de descartarlos; además espera al reinicio en el propio hook, sin un segundo lanzamiento desligado. No se afirma haber identificado la causa original del aviso del usuario.

### 42. Barra de Steam con el fondo base de Retro (2026-10-26)
* La captura del usuario mostró una diferencia real: el template compartido usaba `surface_container_high` (Ethereal `#131a3a`) mientras la barra del escritorio usa `background` (`#060b1e`). Las pruebas anteriores demostraban cambio de color, no coincidencia con el escritorio.
* Nuevo `omarchy/overlays/steam.css`, registrado en `MATUGEN_OVERLAYS`: `--adw-headerbar-bg` y su backdrop referencian `--adw-window-bg`. Sigue cualquier tema Retro estático/dinámico; default (end-4) y Plasma conservan su template compartido. Se aplicó a Steam y se reinició para cargarlo. Captura recortada verificada: color dominante de la barra `(6, 11, 30)` = `#060b1e`; captura temporal borrada.


### 43. Salvapantallas, ventanas y perfiles de la sesión (2026-10-26)
* `ScreensaverIdle.qml` importa `Quickshell.Services.Mpris` y calcula `mediaPlaying` con `Mpris.players.values.some(p => p.isPlaying)`: bloquea el temporizador automático durante la reproducción. Conserva el inicio manual y el cierre por actividad.
* La regla de renderizado sin foco incorpora las clases de Codex y ChatGPT. Virt-manager pasa de flotante a mosaico en JSON y Lua persistentes.
* Perfiles default (end-4)/Plasma: gestor de tareas btop mediante `bwm-terminal` y salvapantallas habilitado a los 5 min. El perfil activo incorpora `notifications.forceMonitor`. Se conserva también el estado generado de colores Ethereal, tema GTK `BWM-2` y bordes sin degradado inventado.
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
* **Verificado:** con el backend shader (hyprsunset ausente), muestreo de 4×4 px con grim: encendido 4000 K y 3000 K reducen el azul, sigue tras `hyprctl reload`, apagado y apagado+reload vuelven al color sin tinte; `configerrors` vacío; reinicio de Quickshell con el gestor y sin errores del panel/indicador en el log. **No probado:** clic real en el interruptor/deslizador del panel ni el indicador a la vista; backend hyprsunset (instalable con `sudo emerge gui-apps/hyprsunset`, overlay hyproverlay). default (end-4) sigue con su servicio `Hyprsunset` propio.

---

### 50. Consolidación de todos los cambios y publicación solicitada (2026-10-27)
* El usuario pide commitear todo y subirlo a los remotos. Se incluyen deliberadamente cambios de esta conversación y concurrentes: About BWM/Fastfetch, separación de Temas/Plugins y catálogo, barra adaptable, maximizado, luz nocturna, perfiles generados y virt-manager flotante. No se descartan cambios ajenos.
* Verificación previa: 20 pruebas de About/complementos correctas; sintaxis de 6 Python, 8 Bash y 4 Lua; 3 JSON válidos; AGENTS/CLAUDE idénticos, `git diff --check` y `hyprctl configerrors` sin errores. Esta tarea no repite pruebas gráficas ni prueba juegos reales. Publicación mediante `git push origin main` y comprobación de `refs/heads/main` de GitLab/GitHub; el resultado se informa tras ejecutarlo.

### 51. Instalador con requisitos por skin, bienvenida y propósito del proyecto (2026-10-28)
* **Petición:** instalador que analice el equipo y, si falta un requisito, lo diga, dé los comandos para la distro y salga; requisitos basados en lo que necesita BWM para pintar y en las tres skins; bienvenida al iniciar sesión (agradecer, skins en verde con requisitos, añadir skins con la wiki, desactivable, tipo Calamares) que se abra también con `bwm`; documentar el propósito (gestor de ventanas que encapsula a los demás como skins) y la norma de compatibilidad con los temas de cada original; temas por defecto de cada skin.
* **Hecho:** §2.9. Requisitos deducidos del código (imports QML, comandos de scripts, `qfile` de los binarios instalados en Gentoo y ebuilds de GURU/hyproverlay). Propósito y reglas 11-12 en `AGENTS.md`/`CLAUDE.md`, README en/es reescritos en cabecera, requisitos e instalador, `docs/SKINS.md`, `docs/REQUIREMENTS.md`.
* **Encontrado:** la sesión corre Hyprland 0.56.2 (`efb50993`) y `hyprbars-plasma.so` es de 0.55.4 (`a0136d8c`): el comprobador marca Plasma «faltan requisitos» con el comando de recompilación. No se recompiló. `xdg-desktop-portal-gtk` (FileChooser=gtk de §3.22) no está instalado aquí: sale como recomendado.
* **Verificado:** `py_compile`, `bash -n` de `install.sh`/`bwm`/`autostart.sh`, JSON válidos; `./install.sh --check` (sale 1 por el plugin), `--skins default,retro` (0), skin desconocida (2); planes de instalación simulados para Gentoo, Arch, Fedora, openSUSE, Debian y desconocida; `bwm help|startup status|skins|skin`, `bwm skin plasma` rechazado. Bienvenida cargada con `qs -p` sin errores de QML (sólo avisos WebP/portal) y revisada visualmente en las cuatro páginas (ventana flotante unos segundos en el workspace 10, capturas recortadas y borradas); corregido el botón «Activar» invisible cuando falta algo. La barra real recargó `FirstRunExperience.qml` sin errores.
* **No probado:** una instalación completa en un `$HOME` limpio u otra distro (se ejecutó sólo `--check`), el autoarranque real de la bienvenida en un inicio de sesión, «Activar esta skin» desde la ventana y la compilación del plugin por el instalador.

### 52. Fallos de §3.51 corregidos, ajustes comunes entre skins y propósito ampliado (2026-10-28)
* **Petición:** corregir los fallos encontrados; documentar que BWM facilita usarlos todos (pocas skins, lo esencial, casi las mismas funciones, lo muy importante de cada escritorio incluido, sin complejidad extra), el porcentaje estimado de compatibilidad con temas y plugins de cada original, el porteo de escritorios a un único compositor (Hyprland); configuración modular por skin; qué se conserva entre skins (cursor, Kelvin, apps predeterminadas, workspaces, pantallas y escala, autoarranque, servicios, interfaz, General; fuentes por skin y tema); quitar la protección de volumen en todas.
* **hyprbars → Hyprland 0.56:** cambios de API tomados del diff del hyprbars oficial entre `3aa21f2` (0.55.4) y `7644cec` (0.56.x) de hyprwm/hyprland-plugins: `Animation::mgr()`, `State::monitorState()->query().vec/name()`, `Desktop::windowState()->windows()/raise()`, `Desktop::CViewHitTester{*Desktop::viewState()}.windowAt/layerSurfaceAt`, `Fullscreen::controller()->setFullscreenMode/isFullscreen`, `position/size(GEOMETRIC_CURRENT)`, `Desktop::View::validMapped`, `Pointer::Cursor::overrideController`, includes `animation/`, `output/Monitor.hpp`, `pointer/cursor/`. Compila sin avisos, el `.so` lleva el commit `efb50993` y se instaló con `make install`. **No cargado** (Retro activo; carga en caliente prohibida).
* **swww/awww:** `autostart.sh`, `set-wallpaper.sh` y `switchwall.sh` usan el binario que exista; el comprobador acepta cualquiera de los dos grupos (`cmd` con `groups`).
* **Ajustes comunes:** `THEME_SPECIFIC_SECTIONS` = appearance, background, bar, dock, panelFamily, waffles; `SHARED_KEYS_IN_SKIN_SECTIONS` = `bar.workspaces.shown`, `bar.weather`, `bar.topLeftIcon`. Antes de compartir overview/osd/lock/windows/wallpaperSelector se comprobó que eran idénticos en los tres perfiles (el dock no: queda propio). La barra Retro muestra 1..`bar.workspaces.shown`. Kelvin sincronizado (Retro estaba en 3350 K y default (end-4) en 5000 K: se igualó a 3350). Protección de volumen quitada de Ajustes → General y de `services/Audio.qml`.
* **Docs:** README en/es (pocas skins, qué se conserva, tabla de compatibilidad, porteo a Hyprland), `docs/SKINS.md` (compatibilidad, qué se conserva y dónde vive, estructura modular), reglas 13–14 en AGENTS/CLAUDE, `todo.md`. `bwm-requirements.py docs` regenera `docs/REQUIREMENTS.md`. Compatibilidad estimada: Retro ~90 % temas / ~80 % plugins, default (end-4) ~90 %, Plasma ~5 % / 0 % (basada en qué archivos y tipos se admiten, no medida tema a tema).
* **Verificado:** `py_compile`/`bash -n` de los scripts tocados, JSON válidos, `git diff --check`; `./install.sh --check` sale 0 (las tres skins completas); prueba unitaria de `merge_shared_sections` (comunes copiadas, estilo de la barra intacto); `nightlight.py --temperature/--remember`; reinicio de Quickshell con `bwm-theme-manager.py set retro` sin errores en el log y captura recortada de la barra del HP con los workspaces 1–10 (borrada); Ajustes → General cargado en el workspace 9 sin errores; la barra real recargó `Audio.qml`, `Hyprsunset.qml` y `GeneralConfig.qml` sin errores.
* **Probado después (2026-10-28, sin cerrar Stremio, que ya tenía el puente cargado y no se reinicia al cambiar de skin):** Retro→default (end-4)→Retro con valores de prueba: `bar.weather`, `bar.workspaces.shown`, `bar.topLeftIcon`, `overview` y `osd` pasaron a default (end-4) y `bar.height` siguió siendo el propio (40). Kelvin cambiado en la config de default (end-4) (4200 K) llegó a `nightlight.json` y a hyprsunset; restaurado a 3350 K y los valores de prueba revertidos. Plugin: `nm -D` no deja símbolos de Hyprland sin resolver (sólo cairo/GL/lua que Hyprland ya enlaza) y el comprobador lo da por bueno; un Hyprland anidado para cargarlo no arrancó (el sistema lo mata a los segundos), así que no se cargó.
* **Plugin en sesión real (2026-10-28, a petición del usuario):** `bwm skin plasma` cargó hyprbars-plasma.so (`hyprctl plugin list`), Hyprland siguió vivo (mismo PID), sin errores de configuración y Stremio abierto; `hyprctl hyprbars-csd` decide bien (kitty, Signal y Krita con barra; Firefox, Steam, Stremio, Vesktop, Claude y Antigravity sin ella); captura recortada de un kitty de prueba con la barra Breeze (título centrado y tres botones). Vuelta a Retro (`plugin:hyprbars:enabled` false) sin errores.
* **Sigue sin probar:** pulsar los botones de la barra y arrastrar/encajar ventanas (sin herramienta para inyectar ratón en este equipo).
* **Pendiente del usuario:** `sudo emerge --ask sys-apps/xdg-desktop-portal-gtk`.

### 53. Cambiar a Plasma sin que las ventanas se descoloquen (2026-10-28)
* **Petición:** al pasar a Plasma las apps reiniciadas (Steam…) se reabrían en el workspace del ratón y las ventanas en mosaico saltaban a cualquier sitio. Que todo se reabra donde estaba, que las ventanas en mosaico floten en su mismo sitio con un margen sutil respecto a los bordes, y que cambiar de skin sea cómodo.
* **Causas:** `sync_floating_windows` sólo hacía flotar (Hyprland usa entonces su geometría flotante por defecto). `restart_app` sólo restauraba la geometría de ventanas que ya flotaban, colocaba una vez cada hueco (la ventana de carga de Steam lo gastaba y la principal quedaba donde el ratón) y esperaba 40 s.
* **Hecho:** nuevo `scripts/bwm_windows.py` (común): `plasma_box()` mantiene el rectángulo de la ventana —bajando el contenido los 30 px de la barra Breeze si hyprbars le pone barra (`hyprctl hyprbars-csd`)— dentro del área útil de Plasma (panel 44 px) con `EDGE_MARGIN` = 10 px; `float_for_plasma()` lo aplica a todas las ventanas en mosaico al entrar en Plasma; `restored_box()` decide la geometría de una ventana que vuelve tras reiniciar su app. `restart_app` guarda siempre geometría, devuelve el hueco si la ventana colocada se cierra (ventana de carga), sigue 8 s tras la última colocación y acepta `place_secs` (Steam 180 s). `reload-spotify.py` usa lo mismo. Al volver al mosaico se ordenan las ventanas por posición y se fuerza `dwindle:force_split = 2` mientras se rehace (luego se restaura).
* **Verificado (sesión real, Stremio abierto todo el rato, mismo PID):** tres idas y vueltas Retro↔Plasma. En Plasma todas las ventanas flotan en su workspace y su sitio, a 10 px de los bordes y por encima del panel; Firefox y Steam se reiniciaron y volvieron a su workspace y posición (Steam al 4). Al volver a Retro, todas en mosaico en su workspace; en la última prueba los workspaces de 1–2 ventanas quedaron idénticos. `configerrors` vacío, Hyprland con el mismo PID.
* **Limitación:** en workspaces de 3+ ventanas el reparto del mosaico (árbol de dwindle) puede cambiar al volver de Plasma. Reproducirlo exactamente exigiría reconstruir el árbol con mensajes de layout (en `todo.md`).

### 54. Foco y reproducción al cambiar de skin; mención de NVIDIA en el README (2026-10-28)
* **Problema:** al pasar a Plasma el usuario vio un cambio de workspace y Stremio pausado. Causa más probable (no medida antes de arreglarlo): las apps que se reabren (Firefox, Steam) toman el foco por `focus_on_activate` y te llevan a su workspace; Stremio, oculto, se pausa.
* **Hecho:** `bwm_windows.snapshot_focus()/restore_focus()` guardan y restauran el workspace visible de cada monitor, el monitor y la ventana con foco, y reanudan por MPRIS (`Play`) los reproductores que sonaban y se pausaron. Se usan en `restart_app` y alrededor del cambio de skin.
* **Verificado:** con Stremio reproduciendo, Retro→Plasma→Retro: workspaces (10 y 1), ventana con foco y reproducción idénticos antes y después, mismo PID de Hyprland. No se pudo comprobar el fallo original en el estado anterior.
* **README:** mención «Diseñado con tarjetas NVIDIA en mente» (texto, bajo la introducción) y nota pequeña de que AMD e Intel también sirven pero están menos probados. **Sin logo de NVIDIA**: sus normas exigen permiso escrito para usarlo y dicen que implica patrocinio; sólo se usa el nombre, con aviso de marca y de que no hay relación con NVIDIA. Equipo: RTX 4070 Ti SUPER, driver oficial (módulo abierto).

### 55. Cambio de skin más cómodo; familias mosaico/apiladas (2026-10-28)
* **Petición:** que cambiar de skin sea rápido y, sobre todo, cómodo: la ventana de carga de Steam salía en medio del workspace que estabas mirando; más hueco entre ventanas al flotar en Plasma; distinguir skins de mosaico y de ventanas apiladas (escritorio tradicional) para reutilizarlo en skins futuras.
* **Medido:** el gestor tarda ~1,7–2,2 s (0,5 s es la espera a hyprbars) y la barra de Quickshell vuelve a los ~2,2 s. Lo lento/incómodo eran los reinicios de apps (Steam, Firefox) y sus ventanas emergentes.
* **Hecho:** `bwm_windows.hold_new_windows()/release_new_windows()`: mientras `restart_app` reinicia una app, una regla temporal (`bwm-restart-<clase>`, `workspace = "<ws> silent"`) manda sus ventanas nuevas a su workspace sin foco; se retira redefiniéndola con el mismo nombre y un patrón que no casa (comprobado que redefinir sustituye). Manifiestos con `"windowing"`: default (end-4)/Retro `tiling`, Plasma `stacking` con `titlebar` 30, `panel` abajo 44, `edgeMargin` 10 y `gap` 10. `float_for_plasma`/`plasma_box` → `float_in_place(skin)`/`stacking_box(…, windowing)`; `sync_floating_windows(skin)` decide por el manifiesto (hyprbars sólo en Plasma); `theme.lua` lleva `windowing` y `rules.lua` hace flotar todo si es `stacking`.
* **Verificado (Stremio sonando todo el rato):** Retro→Plasma→Retro. «Sign in to Steam» (su ventana de carga) apareció en el workspace 4 de Steam en las dos idas, la principal volvió a su sitio, workspaces visibles (10 y 1) sin cambios, Stremio «Playing». En Plasma, 10 px entre ventanas vecinas. `Hyprland --verify-config` ok, `configerrors` vacío. La ventana con foco al final de la vuelta a Retro era kitty y no Claude: no se pudo distinguir si fue un clic del usuario o la restauración.
* **No hecho:** acelerar el reinicio de Quickshell o evitar el de Steam/Firefox (ambos sólo cargan su tema al arrancar).

---

### 56. Auditoría y correcciones iniciales de licencias (2026-10-28)
* El usuario pidió revisar licencias y aplicar correcciones. Los README ya no afirman que todo BWM sea MIT.
  Se incorporaron avisos y textos originales GPL, BSD, MIT, MPL, LGPL y OFL para componentes identificados,
  inventario `THIRD_PARTY_NOTICES.md` y copia de avisos para recursos instalados. No se eligió una licencia
  para el código propio no identificado ni se afirmó que las capturas, fondos o binarios sean conformes.
* Pendiente: procedencia y permisos de recursos gráficos, reproducción de fuentes correspondientes de los
  binarios y alcance preciso de los derivados. Consulte el inventario y `todo.md` antes de una release.

---

### 57. Cambios de skin ligeros, sin saltos de workspace ni reinicios de apps (2026-10-28)
* Petición: default (end-4)→Plasma provocaba múltiples cambios de workspace y desplazaba el vídeo.
* Causas observadas en el código: paleta de Plasma/Retro aplicada dos veces (set-wallpaper + gestor),
  recargas repetidas de Hyprland y hooks que cerraban Firefox, Steam, Spotify y Nautilus. Cada reinicio
  separado restauraba posteriormente su propio snapshot de foco. La geometría se consultaba después de
  modificar reglas, y `window.float` alternaba el estado en lugar de fijarlo.
* Hecho: política común `bwm_transition.py` heredada por hooks; mantiene apps y reproducción. Una sola
  generación y recarga del compositor. IPC `bwmSkin.reload` reconstruye sólo paneles, conservando servicios,
  PID y cachés; fallback de compatibilidad reinicia sólo la instancia ii, sin `pkill -9` global. Flag
  `--restart-shell` para mantenimiento, sin heredar BWM_SKIN_SWITCH. Config activa escrita atómicamente y una
  sola vez aunque las rutas de repo y ~/.config coincidan. Captura previa de clientes, flotación idempotente,
  exclusión de fullscreen/pinned/minimizadas/especiales, una restauración final sin volver a enfocar monitores
  que no cambiaron y validando PID. No se carga un plugin que falta en caliente.
* QML: `Config.reload`, `bwmSkin` en shell, Breeze reactivo a `Appearance.isPlasma`, qmldir explícito de
  `bar/omarchy` para corregir un fallo de resolución al recargar módulos.
* Verificado en la sesión real con socket2 de Hyprland y Stremio reproduciendo: Plasma→default (end-4) (1,14 s)
  →Plasma (0,68 s), y Plasma→Retro (0,88 s)→default (end-4) (1,18 s)→Plasma (0,74 s). Cero eventos de workspace o
  monitor enfocado en ambas secuencias; mismos PID de apps y shell, workspaces visibles e individuales
  conservados, Stremio Playing. Conteo flotantes 1 en mosaico y 12 en Plasma; sin nuevos errores QML en la
  segunda secuencia y configerrors vacío. Se dejó Plasma, la skin inicial.
* Cuatro regresiones automatizadas en `tests/test_skin_switch.py`: hooks no reinician durante transición,
  sesión sin cambios no vuelve a enfocar monitores, dirección reutilizada no roba foco y fullscreen/espacios
  ocultos no se recolocan; además py_compile, bash -n, TOML y diff --check. Fallback de shell antiguo y
  --restart-shell no ejercitados en sesión real.
* Límite deliberado: apps sin recarga de estilos en vivo no reciben el marco completo instantáneamente;
  los archivos quedan preparados para su próximo inicio, y Spotify puede necesitar `spicetify apply`.
  No se ha afirmado una comprobación visual de cada panel ni de todos los servicios al cambiar de dueño.

---

### 58. Snapping al monitor correcto y previsualización más discreta de Plasma (2026-10-28)
* Petición: soltar una ventana en la derecha del monitor principal la llevaba a la derecha del monitor
  vecino; vista previa demasiado redondeada y opaca.
* Causas: el plugin calcula el monitor del puntero, pero Python volvía a elegir el monitor de la ventana
  (su centro puede cruzar la unión antes que el cursor). Se ignoraba escala/rotación y se restaban 44 px
  incluso sin panel abajo. También se detectó que asignar workspace después de fijar el rectángulo lo
  desplaza de nuevo al transferir entre monitores.
* Se corrigió además la implementación anterior de flotación (§3.57): `window.float` exige
  `enable/disable`; `set/unset` desconocidos se interpretaban como toggle. En ventanas de prueba, repetir
  snap alternaba mosaico y tamaño de pantalla completa. Corregido en quick-tile, bwm_windows y gestor.
* Hecho: `quick-tile.py --monitor desc:… --edge --pid …`; modo arrastre sin ciclos/restauración; compatibilidad
  con plugin cargado antiguo eligiendo borde bajo el cursor; no actuar sobre ventana activa si desaparece
  la explícita; validar PID si se suministra. Geometría lógica, reserved real, barra de título incluida,
  workspace primero y dimensiones/posición después. Teclado mantiene sus ciclos y el monitor de la ventana.
* C++: `SnapHelper.hpp` pasa monitor de previsualización, modo edge y PID, usa HOME sin ruta de usuario fija,
  área reservada real y umbral de borde 16 px/corner 64 px. `BarPassElement.cpp`: relleno 0,12 (antes 0,35),
  borde 1 px/0,65 (antes 3 px/0,95), radio 2 px (antes 8), inset 1 px (antes 6). Aproximación propia de
  Breeze; se consultó el outline de KWin como referencia, no se copió su QML.
* Makefile depende también de headers y compila sólo fuentes .cpp. Compilado para Hyprland 0.56.2 e
  instalado sólo mediante make install (rename atómico). Aviso de compilación preexistente por
  addConfigKeyword deprecado; sin errores. NO unload/load en caliente: el preview nuevo requiere otra sesión.
* Verificado: diez regresiones en tests/test_quick_tile.py y las cuatro de cambio de skin; py_compile y
  diff --check. Ocho snaps reales (right dos veces, top-right, bottom-left) en dos terminales invisibles
  de prueba en workspaces temporales: geometría exacta, flotación true, monitor/workspace correctos y
  workspaces visibles conservados. Caso cruzado: ventana real de prueba en LG + lectura del puntero
  simulada en (1919,1500) -> HP, contenido (960,1110,960,1006), sin cambio de workspaces visibles.
* Límite: sin arrastre manual de ratón ni revisión visual del plugin nuevo cargado. El plugin anterior sigue
  cargado hasta reiniciar sesión; el script compatible ya corrige el destino con ese plugin.

### 59. Skins en carpetas y variable de ventanas `windows` (2026-10-29)
* **Petición:** reestructurar para que sea más compacto y entendible, con las skins bien seccionadas para que quien quiera crear una lo entienda, y una variable de ventanas tiling o WM tradicional.
* **Hecho:** cada skin es `config/hypr/skins/<id>/skin.json` y reúne lo que antes estaba repartido entre el manifiesto plano (`skins/<id>.json`, borrado) y el diccionario `THEMES` de `bwm-theme-manager.py` (redondeo, borde, huecos, barra, fuentes, fondo, btop). Nuevo `scripts/bwm_skins.py` (`all_skins`, `skin`, `windows`, `is_traditional`, `traditional`, `theme_table`), del que salen `THEMES`, `bwm_windows.windowing/is_traditional`, `bwm-requirements.load_data` y, vía `--json`, la bienvenida. Variable **`"windows": "tiling" | "traditional"`** (sustituye a `windowing.mode` `tiling`/`stacking`); `traditional` lleva titlebar, panel, edgeMargin y gap. `theme.lua` escribe `windows = "…"` y `rules.lua` hace flotar todo si es `traditional` (o Plasma). `palette` (`matugen`/`omarchy`/`breeze`) sustituye a `is_retro`/`is_plasma` como dato (las claves se derivan para el código existente). `parts` enumera los QML/Lua/colores/scripts de cada skin. Plantilla `_template/` (excluida al listar) y guía `skins/README.md`; `docs/SKINS.md` resume y enlaza. El comprobador, la tabla de `docs/REQUIREMENTS.md` y la bienvenida muestran el tipo de ventanas.
* **No movido:** QML, Lua y scripts de cada skin siguen donde estaban (enlazados a la sesión en vivo y con rutas fijas); `parts` documenta dónde está cada pieza. Una skin nueva aún necesita condiciones de carga en `IllogicalImpulseFamily.qml`.
* **Verificado:** `THEMES` derivado de los manifiestos coincide con el anterior en todos los valores (sólo cambian título y descripción); 7 tests nuevos en `tests/test_skins.py` (campos, carpeta = id, variable `windows` y bloque, rutas de `parts`, requisitos en el catálogo, tabla del gestor, plantilla) + los 14 de cambio de skin y snapping: 21 OK. Retro→Plasma→Retro real: `theme.lua` con `windows = "traditional"`/`"tiling"`, 9/9 ventanas flotan en Plasma, mismos PID y workspaces visibles, `configerrors` vacío; al volver, Steam sigue flotando por su regla persistente `float=true` (comportamiento esperado).

### 60. Ajustes de Retro como ventanas de Omarchy (2026-10-29)
* **Petición:** en Retro, que Configuración abra las mismas opciones de Ajustes pero en ventanitas flotantes de Hyprland con el aspecto de Omarchy, con la misma funcionalidad y siguiendo los colores del tema; sólo en Retro.
* **Hecho:** `quickshell/ii/retroSettings.qml` (como `plasmaSettings.qml`: otro marco, las mismas páginas de `modules/settings/`, mismo `config.json`). Marco: cabecera `󰒓 Configuración › Página` y atajos, lista con glifos Nerd, fila elegida con fondo `menu.selected-background`, texto `menu.selected-text` y barra de acento, buscador con `❯`; colores de `qs.Commons.Color` (popups/menú de `shell.toml`), fuente `Style.font.menuFamily`, `Style.bwmScale` 1,25. Con `SETTINGS_PAGE` (o `open-settings.sh <página>`) es una ventanita de una página; sin ella, la ventana completa. `open-settings.sh` acepta la página como argumento y en Retro abre esta app (default (end-4) `settings.qml`, Plasma `plasmaSettings.qml`). Menú: `setup.settings` pasa a submenú con «Todas las páginas» + 15 páginas; `setup.plugins` abre Plugins (antes Barra). Reglas sólo-Retro en `omarchy_windows.lua` (antes del corte de opacidad): `omarchy-settings-page` (título `Configuración · …`, flotante 1000×680 centrada) y `omarchy-settings` (1150×760). `parts.quickshell` de Retro incluye la app.
* **Verificado:** `Hyprland --verify-config` ok, `configerrors` vacío; ventanita «Barra» y ventana completa abiertas en el workspace 10 (sin quitar el foco: workspaces 10/1 intactos), flotantes, centradas, con el tamaño de la regla y sin errores de QML; capturas recortadas revisadas y borradas. Paleta en vivo por diseño: `Commons/Color.qml` y `MaterialThemeLoader` vigilan sus archivos (`watchChanges`); no se cambió de tema durante la prueba para no tocar las apps del usuario.
* **Límite:** las páginas siguen siendo los widgets Material de BWM (con los colores y la fuente de Retro); algunas píldoras calculan su propio radio y siguen redondeadas. El menú no se probó con clic (se recarga solo al cambiar el `.jsonc`).

### 61. Ajustes navegables con teclado desde el menú y configuración en texto del usuario (2026-10-29)
* **Petición:** navegar la configuración desde el lanzador por completo con el teclado (Escape/Borrar = atrás, ir y volver) y, al final de Configuración, una zona en texto como la de Omarchy donde el usuario escriba reglas u opciones que sobrescriban las de BWM, bien explicada («en esta zona puedes escribir tú»).
* **Menú:** ya tenía Escape (sale del submenú; cierra en la raíz) y Borrar con el buscador vacío (atrás). Las entradas `setup.settings.*` y los accesos `setup.default/keybindings/plugins` pasan `BWM_SETTINGS_FROM_MENU`, así la ventana de Ajustes, al salir, reabre el menú en esa ruta (`omarchyMenu summon`). Etiquetas acortadas para el ancho del menú («Apps predeterminadas», «Editar en texto»).
* **`retroSettings.qml`:** ↑/↓ elige página (contorno de acento cuando el teclado está en la lista), Intro/→/Tab entra (foco al primer control; Tab/Shift+Tab recorren), Esc o Borrar vuelve a la lista, y desde la lista sale y vuelve al menú; en la ventanita, Esc vuelve directamente. Ctrl+F y ↓ desde el buscador. Ayuda de teclas en la cabecera según dónde esté el foco. Borrar en un campo de texto sigue borrando (el campo se queda la tecla).
* **Configuración en texto:** `scripts/bwm-user-config` con plantillas comentadas (cabecera «EN ESTA ZONA PUEDES ESCRIBIR TÚ», ejemplos) creadas sólo si faltan, edición en `$VISUAL/$EDITOR` dentro de una terminal flotante de Omarchy (`org.omarchy.terminal`) y aplicación al cerrar: `hyprctl reload` + aviso de `configerrors`, o `apply-user`. `hyprland.lua` carga el archivo del usuario el último con `pcall` (un error se notifica sin romper la config de BWM). `shell.jsonc` (JSON con comentarios): `all` y luego `skins.<id>`, fusionados sobre el perfil en `load_theme_config` y con `apply-user`. Regla 18 en AGENTS/CLAUDE.
* **Verificado:** en la sesión real, ventana completa abierta desde «menú» en el LG con foco prestado y teclas enviadas por `send_shortcut`: ↓↓ eligió «Fondo», Intro entró (ayuda «tab moverse · esc volver a la lista»), Borrar volvió a la lista, Escape cerró y abrió `omarchy-menu` en Configuración con «Editar en texto» al final (captura borrada); foco devuelto a la ventana previa, regla temporal retirada. Zona de Hyprland: una regla en un archivo temporal mandó una ventana de prueba al workspace 9; con el archivo roto `configerrors` siguió vacío; archivo y carpeta borrados. 4 tests nuevos (`tests/test_user_config.py`: precedencia all/skin, JSONC, plantillas que no pisan lo del usuario, plantilla de opciones vacía) + 21 previos: 25 OK. `Hyprland --verify-config` ok.
* **No probado:** que la notificación de error se vea, editar de verdad en la terminal flotante y `apply-user` sobre la config real (sólo con datos de prueba). Quitar una línea de `shell.jsonc` no devuelve el valor de BWM (queda guardado): documentado en el README.

### 62. Menú y Ajustes de Retro más ergonómicos con teclado (2026-10-29)
* **⚠️ Ajustes y edición de texto superados en parte por §3.63.**
* **Petición:** el aviso «Tu hyprland.lua tiene un error»; al volver con Escape el cursor saltaba arriba del todo; mejorar visuales y navegación; no obligar a pulsar Tab cientos de veces (categorías); buscar más mejoras de ergonomía.
* **Aviso:** era la notificación crítica (no caduca) de la prueba de §3.61 con un archivo roto, ya borrado; `hyprctl configerrors` vacío. Retirada con IPC `notifications dismiss`. El mensaje ahora conserva el texto de Lua («línea 1: } expected near no…») y dice cómo corregirlo; sólo quita comillas y caracteres de shell.
* **Menú (`omarchyMenu/omarchy/Menu.qml`):** `rebuildDisplay` conserva la fila por id (también en las reconstrucciones asíncronas de `when/checked`); `goBack` marca el submenú del que se sale; `lastSelection` por menú (la raíz empieza arriba al abrir, los submenús donde se dejaron); `setActiveMenu(…, focusItemId)`; `open` acepta `select`. Teclas: Tab/Shift+Tab, Ctrl+J/K/N/P, Inicio/Fin. Pie (`footerHeight`, contado en el alto de la tarjeta y en `availableRowsHeight`) con la ruta (`pathFor`) y las teclas según el contexto. IPC nuevas en `OmarchyMenu.qml`: `summonSelect(route, item)` y `selected()`.
* **Catálogo:** `setup.settings` de 17 filas a 6: Todas, Apariencia (Barra, Fondo, Interfaz, Temas, Estilo, Cursor), Escritorio (Pantallas, Workspaces, Atajos), Sistema (General, Servicios, Inicio automático, Apps predeterminadas, Plugins), Editar en texto y Acerca de. Cada página lleva `BWM_SETTINGS_FROM_MENU=<su id>`.
* **`retroSettings.qml`:** dentro de una página se navega por **secciones** (`ContentSection` de `contentData`): ↑↓/Tab/Inicio/Fin/AvPág eligen sección (marco de acento con barra, la página se desplaza a ella), Intro/→ entra (foco al primer control de la sección), Esc/Borrar/← vuelve a las secciones y luego a la lista (o al menú en la ventanita). Recuadro de acento que sigue al control con el foco y lo mantiene a la vista (los widgets Material no muestran foco de teclado). Escribir en la lista de páginas busca. Al salir, `summonSelect` del padre con la entrada marcada.
* **Verificado (sesión real):** por IPC: abrir Configuración (marca «Todas»), entrar en Apariencia y `back` → marcada Apariencia; `summonSelect` Sistema › Plugins, `back` → Sistema, `back` → Ajustes con Configuración, volver a Sistema → recuerda Plugins. Captura del menú: 6 filas, pie «Ajustes › Configuración» y teclas. Ventanita General con foco prestado y teclas por `send_shortcut`: ↓↓ marcó la sección Policies y desplazó la página, Intro + Tab mostró el recuadro en «Yes», Esc volvió a las secciones y Esc cerró y abrió el menú en Sistema con General marcada. Capturas borradas, menú cerrado, foco devuelto, regla temporal retirada; log de la barra sin errores tras recargar `Menu.qml`; 25 tests OK; `Hyprland --verify-config` ok.
* **No probado:** las teclas del menú enviadas de verdad (el menú es una capa: se probó con su IPC, no con teclado); Ctrl+J/K y escribir para buscar en la lista de páginas.


### 63. Rediseño de Configuración y del lanzador de Retro; edición de texto normal (2026-10-29)
* **⚠️ La ventana independiente y su navegación se sustituyen por la integración de §3.65.** Las correcciones de los campos y la cuadrícula se conservan.
* **Petición:** rehacer ambos partiendo de los últimos commits: desentonaban, navegación incómoda y fallos al escribir.
* **Causas corregidas:** los `Shortcut` globales de Borrar/Escape de Ajustes se adelantaban a los campos; el lanzador de apps construía una cadena desde `Keys.onPressed`; el menú usaba un `FilterInput` que impedía mover el cursor y seleccionar. Los campos Material bajo el estilo Qt Basic no fijaban el color del texto. `StyledSpinBox` guardaba `parseFloat(text)` en cada pulsación, impidiendo vaciar y reemplazar un número.
* **Ajustes:** marco y controles coherentes con Omarchy, navegación agrupada, búsqueda sin distinguir tildes, ancho lateral fijo y contenido adaptable, barra de secciones con botones anterior/siguiente, contorno de foco y ayuda contextual. F6/Mayús+F6 recorre zonas, Alt+↑↓ salta secciones, Intro entra y Esc vuelve después de que el control/popup haya podido atender la tecla. No hay atajo global de Borrar. Se mantiene el retorno al menú con la entrada marcada, ahora también desde «Todas las páginas». La skin aporta el adaptador `modules/settings/retro/SettingsStyle.qml`; lo común sólo añade la opción genérica `Appearance.outlinedControls` y correcciones de campos/botones. Las paletas se derivan de `qs.Commons.Color` y admiten temas claros y `shell.toml`; los `Binding` de los roles usan `RestoreNone` para que una paleta vieja no se restaure al reemplazar sus delegados.
* **Apps y menú:** `TextInput` real con selección, cursor, edición por palabras y pegado de Qt; las teclas durante composición se dejan al método de entrada. Supr deja de ofrecer desinstalar por accidente (esa acción usa Ctrl+Mayús+Supr). Apps muestra cuadrícula más compacta, nombres con más ancho, celda seleccionada completa, contador, ayuda, barra de desplazamiento, Tab/Mayús+Tab, AvPág/RePág y menú contextual con teclado. El puntero quieto no reemplaza la selección al filtrar. Se conserva el catálogo, ranking, temas de Omarchy y las acciones existentes.
* **Verificado:** pruebas con eventos Qt reales en un `qs -p` separado y ventana al workspace 9: editar/borrar a mitad de texto, Ctrl+A, reemplazar selecciones, números que se guardan al terminar, navegación de secciones, Escape, navegación/lanzamiento de apps (capturado por un stub, no se abren apps), menú contextual y buscador del menú. Las 15 páginas cargan; paleta clara/oscura simulada sólo en ese proceso. Suite completa: **35 pruebas OK**, incluidas 10 de interfaz; `Hyprland --verify-config` correcto y `hyprctl configerrors` vacío. Capturas recortadas de la ventana completa y Apps revisadas; se borraron al terminar. `tests/test_retro_ui.py` queda como suite optativa (`BWM_RUN_QML_TESTS=1 python3 -m unittest discover -s tests -p test_retro_ui.py -v`); requiere QtTest y una sesión Wayland, crea copias temporales de los QML y no arranca la barra otra vez.
* **Límites:** no se ha probado composición con fcitx5/IME real, pegar desde el portapapeles de la sesión ni arrastrar apps al dock; no se ha cambiado la configuración en texto del usuario, instalado paquetes ni hecho commit/push. Las correcciones de campos comunes benefician a default (end-4)/Plasma, sin prueba visual completa de esas dos apps en esta sesión.

---


### 3.64. Ventanas existentes en el gestor de inicio (2026-10-29)

* Vesktop seguía funcionando en el workspace 10 del monitor 4K, con Steam superpuesto. Se enfocó su ventana sin cerrar la aplicación; una segunda ejecución terminó sin crear otra ventana. No se ha establecido por qué estaba en el workspace 10 ni que todos los lanzadores eleven una instancia existente.
* `autostart-manager.py run-one` reconoce el identificador completo de escritorio de las aplicaciones Wayland/Flatpak y enfoca la ventana concreta; restaura las minimizadas. Con workspace explícito conserva la asignación y enfoca la ventana. Esto sólo afecta a la acción del gestor de inicio, no cambia la semántica de los lanzadores generales ni garantiza solucionar cualquier fallo de aplicación.
* Verificado: compilación Python, coincidencia con Vesktop real y pruebas aisladas de foco/restauración. No se ha probado un inicio de sesión nuevo ni una restauración real de ventana minimizada.


### 65. Configuración dentro del propio lanzador de Omarchy (2026-10-29)
* **Petición:** el diseño anterior seguía desintegrado y resultaba incómodo; Configuración debía formar parte del lanzador de Omarchy en Retro.
* **Cambio de arquitectura:** `OmarchyMenu.qml` posee un `SettingsController` y lo entrega a `Menu.qml`. `omarchy/settings/Catalog.js` añade opciones con el mismo formato de menú existente, antes de `menu.jsonc` del usuario. Los controles escriben los mismos `Config.options` que las páginas comunes; no hay otro almacén de opciones ni un formato de temas nuevo. Idioma y widgets de barra usan el archivo y los comandos de Omarchy que ya utilizaba `BarConfig.qml`.
* **Interacción nativa:** valores visibles en las filas; Intro/Espacio activa o desactiva sin cerrar, elecciones en submenús y editor en la misma tarjeta con validación, Guardar/Cancelar y botones ±/↑↓ para números. Batería, Tiempo y Vista general se agrupan. ← y Esc conservan la navegación de Omarchy. El historial guarda menú, fila, búsqueda y desplazamiento, también al seguir enlaces; elegir un valor tras buscar devuelve a los mismos resultados. La petición de apertura se conserva si aún no se han leído los archivos del menú (fallo observado en la primera prueba tras recarga y corregido).
* **Todas las páginas disponibles:** `SettingsPage.qml` carga los controles más complejos (Atajos, Temas, Plugins, Inicio, apps predeterminadas, etc.) dentro de la misma tarjeta/capa, con altura acotada, secciones, desplazamiento al control enfocado y contorno. `SettingsStyle.qml` adapta sólo esa vista; al salir se reaplica la paleta del shell. No hay barra lateral ni ventana flotante adicional. `retroSettings.qml` se reduce a un puente de IPC para comandos antiguos, y se retiran sus dos reglas de ventana. `open-settings.sh`, Super+I, los enlaces del menú y el botón/Ctrl+, de Apps (también con dock) llevan a esa misma configuración.
* **Verificado:** **43 pruebas OK**, incluidas 18 de interfaz con eventos Qt en una instancia `qs -p` de prueba, escrituras de Config bloqueadas y datos aislados para cambios de opciones. Las 15 páginas cargan dentro del menú sin crear ventanas; se prueban edición/validación/cancelación, ajuste numérico con ↑, elecciones, interruptores, búsqueda y vuelta por enlaces, foco al cambiar de sección y apertura antes de cargar fuentes. En la sesión real `open-settings.sh general` mostró la lista nativa y Atajos se abrió como vista de la misma capa, con el mismo conjunto de ventanas Quickshell. Capturas recortadas revisadas y borradas. No se necesitó reiniciar la barra ni las apps.
* **Límites:** las escrituras reales de idioma/widgets y cambios de opciones no se ejecutaron para probar (se conserva la configuración del usuario); la cuadrícula del dock no se ha probado visualmente. No se ha probado un IME real. Sin commit/push.


### 66. Menús sin pie y Apps con apertura nativa; Alt+Espacio (2026-10-29)
* **Petición:** quitar de todos los menús la franja inferior de ruta y recordatorio de teclas; Apps no abría desde el menú ni con Alt+Espacio.
* **Reproducido:** `omarchyMenu summon apps` cerraba el menú sin mostrar la cuadrícula; abrir `omarchyApps open` directamente sí creaba su capa. Alt+Espacio no estaba en `keybinds.json` ni entre los atajos activos (sólo Super+Espacio).
* **Menús:** eliminado el pie de `Menu.qml` (afecta a todos sus submenús y vistas) y de `AppGrid.qml`, incluyendo sus márgenes/altura. El editor de ajustes sólo muestra el mensaje de validación cuando hay un error, sin leyenda permanente de teclas. Se conservan navegación, botones y atajos.
* **Apertura:** Apps usa la acción estándar `omarchy-shell shell summon bwm.apps`, atendida dentro de `OmarchyMenu.qml`; no necesita lanzar bash y otra llamada IPC desde el menú. `omarchyApps open|toggle|close` y `app-launcher.sh apps` comparten la misma gestión del traspaso entre menú/cuadrícula. El dock opcional se consulta dentro del proceso con `Commons.IpcRegistry` y expone `openApps`, `closeApps`, `inspectApps`, manteniendo su cuadrícula con anclaje/arrastre; sin dock se usa la cuadrícula del menú. `omarchyApps inspect` devuelve geometría, apertura, visibilidad, preparación y número de apps.
* **Atajo:** Alt+Espacio añadido con `keybinds-manager.py add` a `keybinds.json`, que regenera `user_binds.lua` y recarga Hyprland. Super+Espacio se conserva. El comando usa la ruta absoluta de `app-launcher.sh apps`.
* **Verificado:** 45 pruebas OK, incluidas 20 de interfaz (dos regresiones nuevas: acción Apps entregada al shell nativo y ausencia de leyendas inferiores). En la sesión real, la entrada Apps y el comando del atajo mostraron 50 aplicaciones, con `opened`, `visible` y `ready` verdaderos. Alt+Espacio figura activo con modificador 8; se ejecutó su comando, no se simuló una pulsación física. Capturas recortadas de Apps y Estilo revisadas y borradas. Sin errores QML de estos componentes ni errores de configuración de Hyprland.
* **No probado:** el camino del dock con éste activado (está desactivado en la sesión). No se reinició Quickshell ni ninguna app, no se instalaron paquetes y no se hizo commit/push.

### 67. Pantallas de Retro con teclado y distribución visual (2026-10-29)
* **Petición:** navegar por Pantallas con ↑↓ y cambiar valores con ←→; entrar con Intro/Espacio al esquema, mover con flechas, cambiar resolución con Ctrl+flechas y salir con Esc/Borrar. Mostrar las ayudas sólo durante la edición por teclado.
* **Implementación:** `omarchyMenu/omarchy/settings/DisplaySettings.qml` y `display/Layout.js`, propios de Retro. `SettingsPage.qml` los carga en la misma tarjeta/capa del menú, sin el formulario Material ni su recorrido por Tab. default (end-4)/Plasma conservan `DisplayConfig.qml`. Se mantienen resolución, frecuencia, escala, giro, activación, pantalla principal, espacios de trabajo y posición. Aplicar/Restablecer siempre visibles; la fila seleccionada se desplaza automáticamente al navegar.
* **Distribución:** ←→ elige monitor fuera de la edición; Intro/Espacio entra; flechas mueven 40 unidades lógicas (Mayús: 10), Ctrl+flechas elige el modo anunciado más próximo en esa dirección; Tab cambia de monitor dentro del esquema. El dibujo usa resolución, escala y giro. Ajuste a bordes al terminar; Intro/Espacio/Esc/Borrar termina sin salir de Pantallas y oculta las ayudas. Un segundo Esc/Borrar vuelve al menú. El ratón también permite seleccionar/arrastrar; las ayudas se muestran al usar el teclado.
* **Aplicación:** los cambios son un borrador hasta «Aplicar cambios». Normalización del origen y validación de descripción única, resolución y pantallas superpuestas/última activa; se llama al `monitor-manager.py` existente y se conserva la identificación por descripción. La resolución ajusta la frecuencia al modo disponible más cercano y conserva los bordes contiguos al redimensionar. No hay nuevos requisitos ni formato de tema.
* **Incidente durante pruebas y recuperación verificada:** una llamada IPC con JSON y espacios fue rechazada con salida textual y código 0; una prueba continuó sin instalar su backend ficticio y cambió los modos reales. Se restauraron `monitors.lua` y `monitors_layout.json` a su estado previo limpio y se recargó Hyprland: LG 3840×2160@60 en 1920,0 y HP 1920×1080@144 en 0,1080. Se informó al usuario. El fixture ahora viaja codificado, se comprueban su instalación y la ruta del backend antes de pulsar teclas, y las pruebas comparan los archivos reales al terminar.
* **Verificado:** 51 pruebas OK (26 Qt/QML, seis nuevas de Pantallas: navegación/valores, escala/giro, modo de edición y salida, Borrar/Intro, aplicación ficticia y rechazo de superposición). Capturas recortadas revisadas en instancia aislada y panel real; sin leyenda en reposo, ayudas durante edición y acciones fijas. Instancia real abre la nueva página por `open-settings.sh display`, sin reiniciar el shell. Sin errores QML de estos componentes ni errores de configuración de Hyprland. Capturas temporales borradas. Sin commit/push.
* **Pendiente de prueba manual:** arrastre continuado con ratón y nueva aplicación voluntaria de una distribución física; las pruebas finales de aplicar utilizan exclusivamente el backend ficticio.

### 68. Cheatsheet de Retro como el selector de Omarchy (2026-10-29)
* **Petición:** hacer la guía de atajos de Retro como la de Omarchy.
* **Referencia:** `basecamp/omarchy`, rama `quattro`, `bin/omarchy-menu-keybindings`: guía buscable mediante `omarchy-menu-select`, anchura 800, altura de filas 500, combinación → acción y ejecución de la selección. Se reutiliza el `Menu.qml` de Omarchy ya vendorizado (MIT); no se ha copiado el script upstream ni actualizado esa versión vendorizada.
* **Interfaz:** `omarchyMenu/Keybindings.qml` abre la misma tarjeta/capa en modo `select`, con tipografía, colores y buscador de Retro. `Menu.qml` añade `requestTag` y `selectionAccepted` para devolver la selección dentro del proceso sin archivos temporales. Mantiene ↑↓, Tab, Inicio/Fin, búsqueda/edición Qt, Intro y Esc; sin pie de ayudas ni tabla periódica en Retro. La búsqueda se conserva si llega una actualización de los datos mientras se escribe.
* **Datos y acciones:** `hypr/skins/retro/scripts/keybindings.py` consulta `hyprctl binds -j` (fallback al texto), elimina duplicados exactos y helpers sin descripción, formatea modificadores y ratón, ordena los lanzadores al principio e incluye atajos personalizados con descripción. Las acciones Lua generadas se resuelven leyendo expresiones `hl.dsp.*` de `user_binds.lua`, sin ejecutar el archivo de configuración; fullscreen usa el modo 0 de Retro. Los gestos de ratón, callbacks no resolubles y descripciones con varias acciones diferentes se muestran sólo como consulta. La acción seleccionada se despacha 100 ms después de ocultar la capa; las órdenes se pasan como argv.
* **Entradas:** el host de Omarchy carga el componente sólo en Retro y posee ahí `cheatsheet open|toggle|close|inspect` y los GlobalShortcut anteriores. `IllogicalImpulseFamily` deja la guía Material a default (end-4)/Plasma. La entrada Aprender usa `bwm.keybindings` dentro del shell. El shim `omarchy-menu-keybindings` abre la guía o imprime los atajos con `--print`/`-p`. Su enlace en `~/.local/bin` ya existía. El directorio de scripts se declara en `retro/skin.json`; sin dependencias nuevas.
* **Verificado:** 58 pruebas OK, incluidas cuatro pruebas Python nuevas (formato, Lua, ambigüedad/ratón y fallback) y tres Qt nuevas (host compila, búsqueda/Esc y selección capturada sin ejecutar apps). Reinicio de mantenimiento mediante `set retro --restart-shell`, confirmado por el IPC nuevo. En la sesión real, IPC y la ruta Aprender abren 79 atajos (77 acciones resolubles); `hyprctl layers` muestra `omarchy-menu`, sin `quickshell:cheatsheet`. Captura recortada revisada y borrada, shim `--print` comprobado, `bash -n`, `py_compile`, `git diff --check` y `hyprctl configerrors` limpios. Recarga QML posterior confirmada en el log. No se pulsó físicamente Alt+A ni se ejecutó una acción real desde la guía durante la prueba. Sin commit/push.

### 69. default (end-4) usa la selección de colores original de end-4 (2026-10-29)
* **Petición:** igualar la selección del color, la paleta y el resto del flujo con end-4 para comprobar el acento salmón del fondo naranja de Goku.
* **Referencia:** `end-4/dots-hyprland` `2f2a376fdb2ad738bf55f693dd0b474b64bb0ab8` (HEAD consultado). `scheme_for_image.py`, `generate_colors_material.py` y la plantilla Matugen `colors.json` se cotejaron sin diferencias. El original usa Matugen con `--source-color-index 0`; automático = neutral si colorfulness <40, tonal-spot en las demás imágenes; modo según GSettings, tipo según `appearance.palette.type`, acento personalizado en recoloreado y borrado de ese acento al elegir un fondo nuevo. No se ha forzado una paleta naranja.
* **Cambio:** el aplicador directo de fondos ya no invoca Matugen con sus valores por defecto; usa `switchwall.sh --colors-only --image`, compartiendo el parser y la selección originales con el selector de Quickshell. Este modo evita gestionar otra vez el fondo, mpvpaper, diálogos de reescalado y hooks externos de KDE/Code; conserva los hooks Matugen de BWM y su política de transición. Los errores de generación se propagan. `applycolor.sh` coloca el tema de terminal original en el archivo que incluye Kitty y lo recarga mediante el helper existente.
* **Dependencias:** runner propio en `hypr/skins/default/scripts/colors-python.sh`; usa Python del sistema si tiene la API necesaria o el entorno aislado bajo XDG_DATA_HOME. `--install` instala OpenCV headless, NumPy, Pillow y materialyoucolor. Se fija materialyoucolor **2.0.10**, como upstream; 3.x cambia los nombres de roles y falló con `primary_paletteKeyColor` durante la primera aplicación (corregido y aplicación repetida con éxito). OpenCV 5.0.0.93, NumPy 2.5.4 y Pillow 13.0.0 permiten Python 3.14; sus versiones difieren de las antiguas del lockfile de upstream. El código de selección se conserva idéntico, sin afirmar identidad binaria del entorno. Catálogo, manifiesto, instalador y tabla de requisitos actualizados. No se instala nada con sudo ni se cambia el Python del sistema.
* **Resultado comprobado en sesión:** el clasificador original elige `scheme-tonal-spot` para el fondo actual; regeneración real completada usando `BWM_SKIN_SWITCH=1` para conservar apps abiertas, seguida de `hyprctl reload` y `theme reload` por IPC. Los **49 roles** son idénticos a los previos: primary `#ffb599`, background `#1a110e`, secondary `#e7beaf`. Sigue saliendo salmón. Kitty coincide con el archivo generado por el motor de terminal original. Recorte de la barra del LG revisado; la del HP estaba cubierta por un juego a pantalla completa. Capturas temporales eliminadas.
* **Validación:** siete pruebas nuevas aisladas (automático, tipo configurado, claro, recoloreado desactivado, acento nuevo frente a `--noswitch`, fallo Matugen), siete de skins y cuatro de transición OK. `bash -n`, requisitos de default (end-4) y `hyprctl configerrors` OK. Log del shell con avisos anteriores de miniaturas/iconos; no se ha reiniciado Quickshell. Aviso de deprecación `Pillow.getdata` en el generador upstream, aún funcional. No se ha reproducido el entorno/fondo exactos de la captura del autor ni probado todos los esquemas visualmente. Sin commit/push.

### 70. Recoloreado rápido de default (end-4) y nuevos nombres de skins (2026-10-29)
* **Petición:** corregir el cambio lento/irregular de colores al elegir fondo y usar en todas las interfaces `default (end-4)` y `Breeze (Kde plasma)`; Retro no cambia de nombre. Los ids `default`/`plasma`, rutas, IPC y formatos siguen iguales.
* **Causas en el código:** Matugen ejecutaba hooks de aplicaciones dentro del recorrido que debía publicar la paleta (Spotify puede esperar decenas de segundos, Steam instala/reinicia), Kitty recibía primero colores Matugen y después los originales de end-4, el aplicador directo repetía recargas/GTK/Firefox al terminar, y `sync-nautilus.sh` podía volver a forzar oscuro después de elegir claro. El runner también importaba OpenCV/NumPy varias veces sólo para comprobar dependencias.
* **Implementación:** `hypr/skins/default/scripts/matugen-fast.py` lee el TOML original, crea un config temporal sin post_hooks y sin el segundo dueño de Kitty, conserva opciones/plantillas ajenas, ejecuta Matugen y publica inmediatamente por IPC `theme reload`; Hyprland se recarga una vez salvo transición. Los hooks de apps van a un trabajador separado con la política existente `BWM_SKIN_SWITCH=1` (sin cierres/restauración de foco ni recargas adicionales); log en `~/.local/state/bwm/default-colors/hooks.log`. El clasificador, los colores elegidos y el generador de terminal de end-4 no cambian. No se propaga la política al proceso duradero del shell.
* **Peticiones consecutivas:** el coordinador de `switchwall.sh` usa fcntl y tokens atómicos; serializa las aplicaciones y descarta solicitudes intermedias que aún esperaban al llegar una posterior. Los hooks comprueban token y skin antes de cada acción y no continúan cuando quedan obsoletos. Un hook ya iniciado puede terminar; cada uno tiene límite de 30 s. No bloquea la publicación de la siguiente paleta.
* **Otros ajustes:** comprobación de módulos Python sin importar OpenCV/NumPy repetidamente; `set-wallpaper.sh` no repite los hooks ni recargas de default (end-4); `sync-nautilus.sh` sólo sincroniza el acento y no modifica la preferencia claro/oscuro. No hay dependencias nuevas (Python estándar).
* **Nombres:** manifiestos, selector rofi, carrusel y su mapa de ids (acepta etiquetas antiguas de caché), selector Breeze, menú Retro, bienvenida, About/CLI, READMEs, guía de skins/requisitos y reglas AGENTS/CLAUDE. Se conserva KDE Plasma al referirse al escritorio original, y Material You/Breeze Dark como nombres de los temas/esquemas de color.
* **Verificado:** 22 pruebas OK (11 de colores/aplicación, siete de manifiestos y cuatro de transición). Incluyen publicación antes de hooks separados, TOML con opciones/plantillas ajenas y hooks multilínea, único dueño de Kitty, hooks obsoletos y tres peticiones concurrentes que ejecutan primera/última descartando la intermedia. `bash -n`, `py_compile`, requisitos de default (end-4), `git diff --check` e ids/nombres del listado y filas del carrusel comprobados. Aplicación real sobre el fondo actual `anime_1.jpg`: recoloreado 0,92 s y aplicador completo 1,08 s, sin cerrar apps. No se midió el tiempo anterior mediante una ejecución que reiniciara aplicaciones. Reinicio de mantenimiento con `set default --restart-shell` completado; IPC de shell, tema y selectores disponible después, sin errores de configuración de Hyprland. Los 49 roles del fondo actual siguen coincidiendo con Matugen y el clasificador de end-4.
* **Límites:** las apps que no admiten recarga en vivo conservan los colores hasta su siguiente inicio. No se afirma una prueba visual de todas las apps, de todas las skins ni de todas las animaciones entre fondos. El generador original sigue emitiendo el aviso de deprecación de Pillow.getdata. No se ha hecho commit/push.

### 71. Carrusel de temas (Alt+R) sin miniaturas grises y sólo en Retro (2026-10-31)
* **Petición:** Alt+R abría casi siempre el carrusel con todas las miniaturas en gris; hacerlo como Omarchy y exclusivo de Retro.
* **Causa:** el carrusel abre con las filas que ya tiene y a la vez ejecuta `omarchy-theme-switcher --print-rows`; nuestra versión borraba y recreaba todas las previsualizaciones (y `dynamic.png`) en cada ejecución. Las imágenes que se estaban decodificando en ese momento acababan en `Image.Error` (`cache: false`, misma URL) y quedaban grises. Además cargaba las `preview.png` de 2560×1440.
* **Como Omarchy** (`bin/omarchy-theme-switcher` + `omarchy-menu-images`, `quattro` `bda3aaf`): caché estable en `~/.cache/omarchy/theme-selector/{previews,thumbnails}`; las entradas (enlaces con el nombre del tema) y las miniaturas JPG 1536×864 (calidad 82, el tamaño de Omarchy; con `magick` porque `vipsthumbnail` no está) sólo cambian si cambia su origen, siempre por `rename`; candado `flock`; se borra sólo lo que ya no usa ningún tema. Filas `entrada\tminiatura`, paleta dinámica primero (miniatura del fondo actual, también WebP). Primera generación 0,7 s, después 0,06 s. `ImagePicker.qml` reintenta hasta 3 veces una miniatura que falla.
* **Sólo en Retro:** `keybinds-manager.py` admite `"skins": [...]` en una entrada y la genera dentro de `if active_skin == "…" then … end` (en las demás skins la tecla llega a las apps). Alt+R lo usa, con ruta absoluta; el shim sin argumentos tampoco abre nada fuera de Retro.
* **Verificado:** reinicio de mantenimiento con `set retro --restart-shell`; tres aperturas seguidas con el shim y capturas recortadas del HP: todas las tarjetas con imagen; capturas borradas. `hyprctl binds` muestra Alt+R cargado, `configerrors` vacío. **No probado:** pulsar físicamente Alt+R ni comprobar en default (end-4)/Plasma que el atajo desaparece (sólo revisado el Lua generado).

### 72. Cambiar de tema en Retro sin que te cambie de workspace (2026-10-31)
* **Petición:** el cambiador de temas de Retro cambiaba de workspace mientras se reabrían otras apps.
* **Causa (en el código):** al cambiar de tema se reinician las apps que sólo cargan su tema al arrancar (Firefox, Steam, Spotify, Vesktop la primera vez). `restart_app` hacía una foto del foco al empezar y la restauraba al terminar, que con Steam puede ser hasta 3 min después (`place_secs=180`), y cada app en su propio proceso: si cambiabas de workspace entretanto, te devolvía al de la foto. Spotify se reabría sin la regla temporal de `hold_new_windows`, en el workspace visible y con foco.
* **Arreglo:** `bwm_windows.FocusKeeper`: la foto se renueva en cada comprobación y sólo se deshace un robo de foco (la ventana nueva de la app enfocada, o su workspace mostrado, en los 2,5 s siguientes a aparecer). Lo que hagas tú mientras tanto se respeta, también ir a esa app a propósito. Lo usan `restart_app` y `reload-spotify.py`, que ahora también abre Spotify con `hold_new_windows` en su workspace. `snapshot_focus(media=False)` evita consultar MPRIS en cada comprobación; el cambio de skin (`bwm-theme-manager.py`) sigue con su foto y restauración en un único paso.
* **Verificado:** 3 pruebas nuevas en `tests/test_focus_keeper.py` (cambio del usuario respetado, robo inmediato deshecho, enfocar la app después respetado) y las 14 de cambio de skin/snapping: 17 OK. Reinicio real con `restart_app` de una kitty de prueba en el workspace 9: workspaces visibles (10 y 1) y ventana con foco iguales antes y después; ventana y regla temporal retiradas. **No probado:** un cambio de tema real reiniciando Firefox/Steam/Spotify (no se interrumpieron las apps del usuario).

### 73. Ajustes de default (end-4) como los de end-4 (2026-10-31)
* **Petición:** en la skin default (end-4), pasar el modo glass de Estilo a General, quitar Temas y Plugins y poner lo que tiene illogical-impulse, copiando casi todo de end-4/dots-hyprland sin cambiar la configuración esencial.
* **Comparado con end-4** (`dots-hyprland` `2f2a376`): sus páginas son Quick, General, Bar, Background, Interface, Services, Advanced y About. Quick, Background y Services eran idénticas; Bar e Interface sólo añaden secciones visibles en Retro; General sólo difiere por la protección de volumen (quitada a petición en §3.52, se mantiene quitada). Faltaban Quick (retirada en §3.39) y Advanced (retirada en §3.46).
* **Hecho:** `settings.qml` = orden de end-4 (Quick, General, Bar, Background, Interface, Services, Advanced) y luego las páginas de BWM (Keybinds, Autostart, Display, Workspaces, Default apps, Style, Cursor, About). `AdvancedConfig.qml` copiado sin cambios de end-4 (GPL, como el resto del shell); sus opciones (`wallpaperTheming.*`) las sigue usando `switchwall.sh`/`applycolor.sh`. Temas y Plugins fuera de `settings.qml` (Omarchy: siguen en el menú de Retro y en `plasmaSettings.qml`). Nuevo `modules/settings/GlassModeSection.qml`: en General sólo con default (end-4), en Estilo sólo con Retro/Breeze. Traducciones es_ES/es_MX del modo glass. About sigue siendo el de BWM (§3.46) y los widgets comunes conservan las correcciones de §3.63.
* **Verificado:** las páginas 0 (Quick), 1 (General), 6 (Advanced) y 12 (Style) cargan con `qs -p settings.qml` en el workspace 9 sin errores (sólo los avisos de `Revealer` ya conocidos); `configerrors` vacío. Con la skin default (end-4) activa, así que General cargó con la sección glass. **No probado:** revisión visual ni pulsar el interruptor.

### 74. Estilo vacío arreglado y overlay de widgets de end-4 (2026-10-31)
* **Fallo de §3.73:** Estilo salía vacío y General también fallaba: «GlassModeSection is not a type». Las páginas se cargan por ruta y Quickshell no resuelve un tipo de su misma carpeta (como en §3.46 con `addons/`). Movido a `modules/settings/shared/` con `qmldir` (`qs.modules.settings.shared`) e importado en General y Estilo (y `qs.services` para `Translation`). Comprobado: las páginas 1 y 12 cargan sin errores y capturas recortadas de General (modo glass arriba) y Estilo (fuente, salvapantallas, arranque); capturas borradas. La instancia principal (menú de Retro) cargará el módulo nuevo al reiniciar el shell.
* **Widgets de end-4:** su overlay de widgets (`modules/ii/overlay`: grabadora, mezclador de volumen, recursos, notas, imagen flotante, mira y limitador de FPS, con la barra superior para elegirlos y fijarlos) ya estaba en BWM, idéntico al de `dots-hyprland` `2f2a376`, pero sin atajo. Se añade **Super+G** (como end-4) con `keybinds-manager.py`, sólo en default (end-4) (`"skins": ["default"]`), lanzando `quickshell -c ii ipc call overlay toggle`. Los widgets de fondo de end-4 (`modules/ii/background/widgets`) también son idénticos. end-4 no tiene buscador de widgets: su selector es esa barra.
* **Verificado:** `hyprctl binds` muestra Super+G, `configerrors` vacío; abierto por IPC en la sesión real: capa `quickshell:overlay` en el monitor enfocado con grabadora, mezclador y recursos; cerrado de nuevo y captura borrada. **No probado:** pulsar físicamente Super+G ni cada widget.

### 75. Bordes, redondeo y barra flotante de default (end-4) como en end-4 (2026-11-02)
* **Petición:** con una captura de dots-hyprland real: sin bordes que se iluminan, mismo redondeo de ventanas y la barra en modo redondeado igual que end-4.
* **Comparado con end-4** (`dots-hyprland` `2f2a376`, `hypr/hyprland/general.lua`, plantilla matugen `hyprland/colors.lua`): `border_size = 1`, `rounding = 18`, `rounding_power = 2.5`, `gaps_out = 5`; borde activo `outline_variant` al `0x77` e inactivo `surface_container_low` al `0x33`, sin degradado. BWM tenía 2 px con degradado `primary`→`primary_container`, redondeo 14 y `gaps_out` 8.
* **Hecho:** `skins/default/skin.json` (`look`) y `theme.lua` con los valores de end-4; `appearance.lua` usa los colores de end-4 en default (end-4) (Retro y Breeze sin cambios). Barra: el modo flotante (`cornerStyle` 1) separa la barra `hyprlandGapsOut` = 5 px y la redondea con `windowRounding` = 18, así que ahora coincide con las ventanas; `BarContent.qml` vuelve a dibujar el fondo como end-4 cuando `showBackground` está apagado (transparente con su borde de 1 px en flotante, antes se ocultaba).
* **Verificado:** `hyprctl reload` sin errores; `getoption` da borde 1, redondeo 18, potencia 2,5, huecos 5 y degradado `77484648`; captura recortada de una ventana sin borde iluminado (borrada); la barra recargó `BarContent.qml` (sólo el aviso previo de la línea 137); 11 tests de skins/cambio de skin OK. Después, a petición del usuario, `bar.cornerStyle = 1` en `config.json` y `config-default.json`: captura recortada con la barra separada 5 px, redondeada y alineada con el borde y las esquinas de la ventana de debajo (borrada). Después, también a petición, sombra y oscurecido de end-4 en default (end-4): `shadow` range 20, offset 0 2, render_power 10, `rgba(00000020)`; `dim_inactive` con `dim_strength` 0,05 y `dim_special` 0,2; `inactive_opacity` 1 (antes 0,95). Comprobado con `getoption` tras `hyprctl reload` sin errores; sin captura (el oscurecido del 5 % apenas se aprecia en una imagen recortada).

### 76. Autoarranque: cada app en su workspace, también tras una ventana de carga (2026-11-03)
* **Petición:** al encender, empezar en el workspace 1 y que las apps de inicio se abran en el suyo aunque antes enseñen una ventana pequeña (Steam acababa en el 4, el de Signal). Para todas las apps, no sólo Steam.
* **Causa:** `run-all` lanzaba cada app con la regla de exec `[workspace N silent]` de Hyprland, que sólo cubre la primera ventana del proceso lanzado; la ventana de carga de Steam la gastaba y la principal caía en otro sitio. Además nada fijaba el workspace inicial.
* **Hecho (`autostart-manager.py`):** enfoca `HOME_WORKSPACE` (1) al empezar; por cada entrada con workspace, regla temporal `bwm-autostart-<archivo>` (`bwm_windows.hold_new_windows`: `workspace "N silent"`, sin foco inicial ni `focus_on_activate`) por las clases posibles (`StartupWMClass`, id del `.desktop` y su última parte, binario sin envoltorios como `flatpak`, nombre; tal cual y en minúsculas). Lanza con `Popen` y guarda el PID. `settle_windows()` escucha socket2 durante `SETTLE_SECS` (180 s) y mueve sin seguir (`follow = false`) cualquier ventana nueva que sea de la app por clase o por descender de su PID y no esté en su workspace (sólo la primera vez que la ve: después, lo que hagas tú se respeta); `bwm_windows.FocusKeeper` deshace un robo de foco. Al acabar se retiran las reglas. `run-one` (botón «Probar» de Ajustes) no cambia.
* **Verificado:** prueba real con una entrada falsa al workspace 9 que abría una kitty «de carga» y, 3 s después, otra con otra clase: las dos acabaron en el 9 (la segunda por PID), sin cambiar workspaces visibles ni la ventana con foco (se usó el workspace visible como inicial para no moverte); ventanas cerradas. 4 tests nuevos en `tests/test_autostart.py` (clases sin envoltorio, mayúsculas/minúsculas, workspaces válidos, descendencia de PID) + focus keeper y cambio de skin: 11 OK. `configerrors` vacío. **No probado:** un arranque real del equipo con Vesktop, Signal y Steam.

### 77. Ajustes → Atajos más compacto, agrupado y ordenado (2026-11-03)
* **Petición:** filas de atajos un poco más compactas; las cuatro flechas de una misma combinación en una fila «flechas» desplegable; una acción con dos combinaciones en la misma fila; lo más importante primero. La guía de atajos (cheatsheet) se deja como está.
* **Hecho:** nuevo `modules/settings/KeybindGroups.js` (lógica pura, `.pragma library`), usado por `KeybindsConfig.qml` (la página común: default (end-4), Breeze y la vista de Atajos del menú de Retro). Agrupa las flechas con los mismos modificadores y categoría (≥2) en «Alt ← ↑ ↓ → Mover foco» (título = palabras comunes de las descripciones o la del ← sin la dirección), los números (≥3, «Alt 1…0 Cambiar al espacio de trabajo»), las teclas multimedia XF86 (≥3) y las combinaciones de una misma acción (misma orden o dispatcher+argumento: «ImprPant o Super+Shift+S», «Super+Espacio o Alt+Espacio»). Cada grupo es una cabecera con su número de atajos y desplegable; dentro, una fila sangrada por atajo con editar/eliminar/restaurar como antes. Al buscar se despliegan solos; la pestaña «Eliminados» no agrupa. Los contadores de las pestañas cuentan cada grupo como uno (Todos 74 → 33; Espacios de trabajo 22 → 4, Multimedia 10 → 1), comprobado con los atajos reales. Orden: lista `PRIORITY` (menú, Apps, terminal, cerrar, pantalla completa, Alt+Tab, foco, workspaces, mover/ajustar ventanas, guía, ajustes, bloqueo, captura, portapapeles…) y después por categoría. Teclas legibles (`←`, `Enter`, `Espacio`, `.`, `ImprPant`, `Vol +`…) y Super_L sin el «SUPER+» repetido (`visibleMods`). Filas de 70 → 48 px, botones de 36 → 30, separación 8 → 4, columna de teclas ajustada a su contenido.
* **Verificado:** agrupación sobre los 74 atajos reales (42 filas de nivel superior antes del grupo multimedia) con un `qs -p` aparte; página cargada sin avisos nuevos; capturas recortadas de la página plegada y, con copias temporales `zz_…` que abrían los grupos, desplegada (borradas, igual que las copias y la regla temporal). Durante la prueba se enfocó por error un momento tu ventana de Ajustes ya abierta y el workspace 9; se volvió al 2. `configerrors` vacío. **No probado:** clic real en el desplegable ni la vista dentro del menú de Retro; sin test automático (no hay node y las pruebas QML necesitan la sesión).

### 78. Advanced: «Terminal neutra» en vez de «Forzar modo oscuro» (2026-11-03)
* **Petición:** explicar las opciones de Ajustes → Advanced → Generación de color y cambiar «Forzar modo oscuro en la terminal» por un modo neutro que no cambie con el tema.
* **Qué hace cada opción en BWM** (sólo en default (end-4); las usa `switchwall.sh`/`applycolor.sh`): «Shell y utilidades» apagado = al cambiar de fondo no se genera ninguna paleta (shell, GTK, apps y terminal se quedan como estaban). «Apps Qt» = el paso `kde-material-you-colors` de end-4, que va en `post_process`; BWM llama con `--colors-only` y nunca lo ejecuta, así que **no hace nada**: Qt sigue la paleta por `qt6ct`/`kdeglobals` de matugen. «Terminal» apagado = no se regenera la paleta de Kitty ni de las demás terminales (se quedan con la última). Armonía (0,6), Umbral de armonización (100°) e Impulso de primer plano (0,35) son parámetros de `generate_colors_material.py` para los 16 colores ANSI: cuánto girar su tono hacia el acento, máximo de grados de ese giro y cuánto aclarar (oscuro) u oscurecer (claro) los colores para el contraste.
* **Hecho:** clave nueva `appearance.wallpaperTheming.terminalGenerationProps.neutral` (Config.qml, por defecto `false`); `forceDarkMode` se conserva y se sigue leyendo (formato de end-4), pero sale de la interfaz. Con `neutral`, `applycolor.sh` usa para Kitty y las secuencias de terminal `~/.local/state/quickshell/user/generated/terminal/neutral_colors.scss`, generado una vez con el mismo `generate_colors_material.py` (gris, `scheme-monochrome`, armonía 0, impulso 0, sin mezclar fondo/texto): la paleta base de end-4 (`terminal/scheme-base.json`, oscura, Gruvbox: fondo #282828) intacta y grises puros en los huecos 232–255. Al cambiar el interruptor se reaplica al momento (`applycolor.sh`, sólo fuera de Retro/Breeze); Armonía e Impulso se desactivan mientras está encendido. Traducciones es_ES/es_MX/en_US. Después, a petición, se quita de la página «Umbral de armonización» (`harmonizeThreshold` se sigue leyendo con su valor, 100). También a petición se eliminan «Shell y utilidades» y «Terminal»: fuera de la página, de `Config.qml` y de los cuatro `config*.json` (`enableAppsAndShell`, `enableTerminal`); `switchwall.sh` y `applycolor.sh` ya no los consultan y siempre generan la paleta y tematizan la terminal. Queda «Apps Qt» (desde §3.79, el generador Qt de end-4).
* **Verificado:** paleta neutra generada a mano (valores = `scheme-base.json`), `bash -n`, JSON de traducciones válidos, página Advanced cargada con `qs -p` en el workspace 9 sin avisos. **No probado:** activarlo en la sesión real (recolorearía las terminales abiertas) ni el clic en el interruptor.

### 79. «Apps Qt» como en end-4, sólo en default (end-4) (2026-11-03)
* **Petición:** clonar «Apps Qt» de dots-hyprland; el usuario eligió hacerlo sólo en default (end-4).
* **Cómo es en end-4** (`2f2a376`): al cambiar de fondo `switchwall.sh` (`post_process`) llama a `matugen/templates/kde/kde-material-you-colors-wrapper.sh`, que ejecuta `kde-material-you-colors` 1.10.1 (pip) con el color, el modo de GSettings y la variante del esquema; genera `~/.local/share/color-schemes/MaterialYou{Dark,Light}.colors` y los aplica con `plasma-apply-colorscheme` a `~/.config/kdeglobals`. Las apps Qt los leen con `QT_QPA_PLATFORMTHEME=kde` (plasma-integration) y estilo Darkly (`kwriteconfig6 … widgetStyle Darkly` en su instalador); iconos breeze-plus con `plasma-changeicons`, configuración en `~/.config/kde-material-you-colors/config.conf`. Sin KWin el programa termina tras aplicar, al intentar recargar KWin (`org.kde.KWin` no existe en Hyprland): pasa igual en end-4, por eso no queda proceso en segundo plano.
* **Hecho:** `skins/default/scripts/kde-material-you-colors-wrapper.sh` (el de end-4, llamado desde `switchwall.sh` también con `--colors-only`), `colors-python.sh --install-qt|--check-qt|--qt` y `requirements-qt.txt` (mismo entorno de colores, `materialyoucolor` 2.0.10 intacto), `config/kde-material-you-colors/config.conf` copiado de end-4 (el script lo enlaza en `~/.config` si falta; `install.sh` lo enlaza e instala el módulo). Sin plasma-workspace, `kde-shims/plasma-apply-colorscheme` (propio de BWM, sólo se pone delante en el PATH de ese programa si falta el original) copia los grupos de color a kdeglobals conservando lo demás y emite `KGlobalSettings.notifyChange`, como el original. `bwm_icons.write_kdeglobals` conserva el esquema de end-4 (y Darkly si está) cuando la skin es default y «Apps Qt» no está apagado; en Retro/Breeze sigue con la paleta de qt6ct. `environment.lua`: en default, con «Apps Qt» y el plugin `KDEPlasmaPlatformTheme6.so`, `QT_QPA_PLATFORMTHEME=kde`; sin él, qt6ct como antes. Requisitos recomendados de default: `default-qt-colors`, `plasma-integration`, `darkly` (Darkly no está en Gentoo/GURU: en end-4 sale de su overlay). No se usa breeze-plus ni `plasma-changeicons` (no instalados; BWM mantiene sus iconos por skin).
* **Verificado:** instalación de `kde-material-you-colors` 1.10.1 y dbus-python 1.5.1 en `~/.local/share/bwm/default-colors-venv` sin cambiar las demás versiones; ejecución en un HOME aparte y después real: kdeglobals con `ColorScheme=MaterialYouDark`, grupos de color nuevos y `[BWM]`, fuentes e iconos conservados; reescritura de `bwm_icons` conserva los colores de end-4. Reaplicar el fondo actual con `set-wallpaper.sh`: 1,04 s, el log del programa se actualiza, `configerrors` vacío. 6 pruebas nuevas (`tests/test_qt_colors.py`) + skins, colores y cambio de skin: OK; actualizada la prueba de la opción «Shell y utilidades» retirada en §3.78. Copia previa de kdeglobals sólo en el scratchpad de la sesión.
* **No probado / pendiente del usuario:** `sudo emerge --ask kde-plasma/plasma-integration` (sin él las apps Qt nativas siguen con qt6ct; los flatpaks KDE ya leen kdeglobals) y Darkly; tras instalarlo, el cambio de `QT_QPA_PLATFORMTHEME` llega a las apps abiertas después de reiniciarlas, y a todo tras volver a iniciar sesión. Sin prueba visual de una app Qt con el plugin. kde-material-you-colors también escribe, como en end-4, perfiles de Konsole (`~/.local/share/konsole`, `~/.config/konsolerc`) y temas de resaltado de KDE.
* **Actualización de Gentoo para instalar plasma-integration (2026-11-04):** hizo falta `@world` (Qt 6.11.1→6.11.2, KF 6.27→6.29, Quickshell 0.3.2, NVIDIA 615.78.08). Trampas: `/usr/src/linux` apuntaba al 7.3.0 sin compilar (se volvió al 7.2.5 con `eselect kernel set`) y el `objtool` del 7.2.5 enlazaba un `libopcodes` de binutils ya sustituido (`make -C /usr/src/linux-7.2.5-cachyos tools/objtool`). La actualización **desinstaló `dev-qt/qtpositioning`** (no estaba en world) y Quickshell no cargó la configuración tras reiniciar («module "QtPositioning" is not installed», `services/Weather.qml`): ahora es requisito del núcleo (`qtpositioning` en `requirements.json`). 26 `._cfg` revisados: libvirt y SDDM sólo cosméticos, descartados.
* **Tras reiniciar (2026-11-04):** `dev-qt/qtpositioning` reinstalado y Quickshell lanzado una vez: carga, con `QT_QPA_PLATFORMTHEME=kde`; módulo NVIDIA 615.78.08 cargado. Protegidos dos errores del arranque: `WorkspaceModel.qml` (`monitor?.id`, el monitor aún es nulo) y `agents/Panel.qml` (`Qt.callLater` cuando el panel ya se recreó). Demostración con una app Qt Widgets compilada aparte en el workspace 10, sin foco: con qt6ct sigue la paleta de matugen; con el plugin de KDE, la de kde-material-you-colors, y al aplicar otro color (`#3b82f6`) se repintó **en vivo** sin reabrirla (qt6ct no). Restaurado el color del fondo; ventanas y reglas temporales retiradas. Estilo de widgets aún Fusion (Darkly sin instalar).

### 80. Apps Qt de Retro como en Omarchy: plugin GTK (2026-11-04)
* **Petición:** que las apps Qt de Retro cambien con el tema como en default.
* **Cómo es en Omarchy** (`quattro` `84b3f28`): `default/hypr/envs.lua` pone `QT_QPA_PLATFORMTHEME=gtk3`; Fusion con la paleta del tema GTK (la migración `1785351479` retiró Kvantum porque no seguía el tema). Nada de kde-material-you-colors.
* **Hecho:** `environment.lua` en Retro usa `gtk3` si existe `platformthemes/libqgtk3.so`; si no, qt6ct como antes. Requisito recomendado de Retro `qt-gtk3` (Gentoo `dev-qt/qtbase[gtk]`; el usuario lo activó en `/etc/portage/package.use/bwm-qt-gtk` y recompiló qtbase). En el resto de skins no cambia.
* **Encontrado con el plugin GTK:** dos errores que afectaban a todas las apps GTK: `config/gtk-3.0/settings.ini` empezaba por `Settings]` (faltaba el `[`; ya estaba así en el repo, causa desconocida, GTK ignoraba el archivo) y la plantilla `matugen/templates/gtk.css` usaba `!important`, que GTK no admite (descartaba el color de la fila seleccionada de `navigation-sidebar`). Corregidos la cabecera, la plantilla y los dos CSS generados; `gtk-theme.py reload` aplicado.
* **Verificado:** la ventanita Qt Widgets de demostración con `QT_QPA_PLATFORMTHEME=gtk3` (workspace 10, sin foco) sale con la paleta del tema GTK actual y, al poner un momento `gtk-theme` Adwaita, se repintó **en vivo** a claro; al volver a `BWM-1`, de nuevo con la paleta. Tras corregir, sin avisos de GTK al arrancar (sólo el del portal por app ID, inofensivo). Durante la limpieza, una tercera prueba de 3 s se abrió en el workspace visible porque ya se había retirado la regla temporal. **No probado:** la skin Retro activa de verdad (no se cambió de skin) ni con un tema de Omarchy claro/estático.

### 81. El fondo no desaparece al reconectarse un monitor (2026-11-04)
* **Petición:** se quitó el fondo del monitor principal; que no vuelva a pasar.
* **Causa (log de Hyprland):** el MSI (`DP-2`) se desconectó y volvió a conectarse (`Connector DP-2 disconnected` / `connected`), p. ej. al entrar en reposo. swww-daemon recrea la salida pero la deja en un color (`swww query`: `currently displaying: color: 000000`); el LG seguía con la imagen. `autostart.sh` sólo reintenta al iniciar sesión.
* **Hecho:** `window-guard.py` (ya escuchaba `monitoradded/monitorremoved/configreloaded`) llama a `restore_wallpapers()`: busca en `swww query` las salidas que muestran un color y les pone el fondo actual (`~/.cache/current_wallpaper`, si no `background.wallpaperPath`) con `--outputs`, sin transición, hasta 10 intentos. No hace nada con un fondo de vídeo (`mpvpaper`) ni sin swww/awww. También al arrancar el vigilante y con `window-guard.py wallpaper`.
* **Verificado:** `window-guard.py wallpaper` devolvió el fondo al MSI; vigilante reiniciado (PID nuevo); `swww clear` del `DP-2` + `hyprctl reload` → el vigilante lo repuso solo en <4 s; `configerrors` vacío; 3 pruebas en `tests/test_window_guard_wallpaper.py`. **No probado:** una desconexión física real del monitor (el evento es `monitoradded`, el mismo camino).

### 82. Steam y Firefox siguen a la skin (2026-11-04)
* **Petición:** al pasar a Retro, Steam no cambiaba de tema; que se reinicie sin cerrar la bandeja ni un juego, y ver si se puede sin reiniciar. Firefox: la fila de pestañas cambiaba, pero la de URL y marcadores seguía con los colores de default.
* **Steam, causa:** el tema se instalaba (21:22) pero `steam-theme.sh` salía antes de reiniciar con `BWM_SKIN_SWITCH=1` (§3.57: el cambio de skin no reinicia apps) y Steam (abierto desde las 19:14) sólo carga el tema al arrancar. **Hecho:** durante un cambio de skin el hook lanza aparte `bwm_omarchy.py restart-steam --after-switch` sin la variable: espera a que el gestor suelte `/tmp/bwm-theme-manager.lock` y reinicia sólo si `install.log` es posterior al arranque de Steam (`_steam_started_at`, de `/proc`). Mantiene lo de antes: nada con un juego abierto (`steam_app_*`, gamescope, `SteamLaunch AppId`; aviso), ventana en su sitio o vuelta a la bandeja con `-silent`. Probado en real: reiniciado 21:30:44, ventana de nuevo en el workspace 2 y workspaces visibles sin cambios. 4 pruebas en `tests/test_steam_restart.py`.
* **Steam sin reiniciar:** Adwaita-for-Steam por su instalador (el método de BWM) modifica los archivos de `steamui`, que Steam sólo lee al arrancar. Aplicarlo en vivo exige un inyector (Millennium, CSSLoader o SFP, los que admite Adwaita-for-Steam) que se conecta al CEF de Steam con su depuración remota (`~/.local/share/Steam/.cef-enable-remote-debugging`, puerto local que cualquier proceso del equipo podría usar para controlar la sesión de Steam). No activado; pendiente de decisión del usuario.
* **Firefox, causa:** Firefox 158 renombró las variables del tema (`LightweightThemeConsumer`/`ThemeVariableMap` del `omni.ja`): `--toolbar-bgcolor` → `--toolbar-background-color`, `--toolbar-field-focus-background-color` → `--toolbar-field-background-color-focus`, `--tab-selected-bgcolor` → `--tab-background-color-selected`… La barra de URL además ponía primero `--mat-*`, que sólo se lee al arrancar. Pywalfox ya cambiaba en vivo (la fila de pestañas sí cambiaba). **Hecho:** `config/firefox/userChrome.css` usa primero las variables nuevas, después las antiguas y por último `--mat-*`; la capa TUI de Retro (`overlays/firefox.css`, y la copia generada en `~/.cache/material-you-firefox.css`) pone `--toolbar-background-color` en la barra. Copiado a los dos perfiles (el instalador lo copia, no lo enlaza). Firefox reiniciado una vez (`restart-firefox --force`, 21:39) con sus tres ventanas de vuelta en sus workspaces: captura recortada con pestañas, URL y marcadores en el color del tema Retro activo (Retro-82, fondo `#05182e`) y la capa TUI. **No probado:** un cambio de skin o de fondo posterior con Firefox abierto (debería cambiar en vivo por Pywalfox).
* **Después (2026-11-04):** con Retro-82, Firefox salía más claro que el resto. Pywalfox (`dist/background.js`) da al marco (`frame` → `--lwt-accent-color`) el fondo exacto (`color0`) y a las barras tonos derivados (`backgroundLight` = color0 ×1,25, `backgroundExtra` ×1,85). La capa TUI de Retro usa ahora `--lwt-accent-color` en el marco, las barras y el fondo de la URL (un solo fondo, el exacto del tema, en vivo). default (end-4) conserva los tonos de Pywalfox. Necesita un reinicio de Firefox para cargarse. **Steam no se reinició al cambiar a Retro-82 porque había un juego abierto** (`SteamLaunch AppId=960090`); antes sólo avisaba. Ahora `restart_steam` espera (hasta 12 h, comprobando cada 15 s) a que se cierre el juego y reinicia entonces, si Steam sigue con el tema viejo; un solo proceso esperando (`/tmp/bwm-steam-restart-<uid>.lock`). `steam-theme.sh` lo lanza siempre aparte (los ejecutores de hooks cortan a los pocos segundos). 2 pruebas más (6 en total). Lanzado en la sesión real: esperando a que se cierre el juego. Firefox reiniciado otra vez (21:54): pestañas, barra de URL y marcadores miden exactamente `#05182e` (Retro-82). Una ventana volvió al workspace 1 en vez del 10 (se emparejan por título y el de YouTube había cambiado); se devolvió a mano. Añadida también la regla del campo de URL con foco (sale en el siguiente reinicio de Firefox).


### 83. Firefox ya no se reinicia al cambiar de tema en Retro (2026-11-04)
* **Petición:** cambiar los temas de Steam y Firefox sin cerrarlos, y ver cómo lo hace Omarchy.
* **Omarchy** (`quattro` `84b3f28`, `bin/omarchy-theme-set-browser`): sólo tematiza navegadores Chromium (Chromium, Chrome, Edge, Brave), con la política de empresa `BrowserThemeColor` en `/etc/…/policies/managed/color.json` (escrita como root mediante una regla de sudo propia) y `--refresh-platform-policy`, que la aplica sin reiniciar. No tematiza Firefox ni Steam.
* **Hecho:** quitado el reinicio de Firefox de `apply_retro_palette_colors` (era el único sitio que lo pedía automáticamente). Con §3.82 sus colores llegan en vivo por Pywalfox; la CSS de `material-you-firefox.css` sólo aporta la forma de la capa TUI, igual en todos los temas de Retro, que carga en el siguiente arranque. `bwm_omarchy.py restart-firefox [--force]` sigue disponible a mano.
* **Verificado:** paleta de prueba en `~/.cache/wal/colors.json` (fondo `#3a0a0a`) + `pywalfox update`: pestañas, URL y marcadores pasaron a `#3a0a0a` sin reiniciar Firefox; devuelta la paleta original, otra vez `#05182e`. **Steam en vivo** sigue sin hacerse: exigiría un inyector (CSSLoader/Millennium) y abrir la depuración remota de Steam; el usuario no lo ha pedido.

### 84. Stremio sin barra de título GTK (2026-11-04)
* **Petición:** al cambiar de tema (Retro-82 → Osaka Jade) Stremio «no cambiaba».
* **Causa:** la web sí cambió en vivo (captura: acento verde y texto crema de Osaka Jade); lo que seguía con Retro-82 era la barra de título, que dibuja GTK 4/libadwaita y sólo lee `gtk.css` al arrancar Stremio (abierto a las 22:07, tema cambiado a las 22:09). El puente `stremio-theme.cjs` sólo llega a la web.
* **Hecho:** Stremio Linux tiene `-n, --no-window-decorations` (visto en `--help`). `stremio-theme.py` escribe `~/.local/share/applications/com.stremio.Stremio.desktop` (copia del exportado por Flatpak con esa opción tras el id, marcada `X-BWM-Generated=stremio-theme.py`; no pisa un lanzador propio del usuario y se actualiza si cambia el de Flatpak) y su reinicio de adjuntar el puente también pasa la opción. Las skins en mosaico no usan barras de título, como Omarchy. Arreglado de paso el import de `bwm_transition` en `stremio-theme.py` cuando se carga por ruta (la prueba `test_stremio_setup.py` ya fallaba antes). 2 pruebas en `tests/test_stremio_launcher.py`.
* **Verificado:** Stremio reabierto (en pausa) con `--no-window-decorations` en su línea de órdenes; captura recortada de la franja superior: sin barra y con los colores de Osaka Jade. Al reabrirlo, la ventana volvió en el workspace 10 en vez del 1 y se devolvió a mano. **No probado:** Breeze (Kde plasma), donde hyprbars debería ponerle su barra Breeze.

### 85. Firefox cambia de fuente al entrar o salir de Retro (2026-11-05)
* **Petición:** al pasar de Retro a default (end-4) la fuente de las letras no cambiaba.
* **Causa:** era Firefox (abierto en Retro el 2026-11-04 a las 21:54): los colores cambian en vivo por Pywalfox, pero la capa TUI de Retro (JetBrains Mono, esquinas rectas) va en el CSS del chrome, que sólo se lee al arrancar, y desde §3.83 nada lo reiniciaba. GTK, Qt, kitty, Vesktop y la config de Quickshell ya estaban con las fuentes de default; Steam se había reiniciado tras el cambio.
* **Hecho (elegido por el usuario):** `bwm-theme-manager.py`, cuando el cambio de skin entra o sale de Retro, lanza aparte y sin `BWM_SKIN_SWITCH` `bwm_omarchy.py restart-firefox --after-switch`: espera a que el gestor suelte su candado y reinicia una vez un Firefox que ya estuviera abierto antes del cambio (sesión y ventanas en su sitio, como Steam en §3.82). Los cambios de tema dentro de Retro y default ↔ Breeze no lo reinician. 4 pruebas en `tests/test_firefox_restart.py`.
* **Verificado:** ese mismo camino reinició el Firefox real; captura recortada con la fuente y la URL redondeada de default. Las tres ventanas volvieron a su workspace (2, 10, 10); en el 10 quedaron una encima de otra y se devolvieron lado a lado con `togglesplit`, con el foco devuelto. En el workspace 2 (Firefox, ChatGPT, Steam) cambió el reparto del mosaico y no se pudo reconstruir el anterior (limitación de §3.53). **No probado:** un cambio de skin completo Retro ↔ default con Firefox abierto.

### 86. Barra, ajustes rápidos y Ajustes con la fuente de Retro en default (end-4) (2026-11-05)
* **Petición:** tras volver de Retro, la barra, el menú de ajustes rápidos y Ajustes seguían con la fuente de Retro.
* **Causas:** (1) el perfil `config-default.json` pedía `Rubik` y `Gabarito` (valores antiguos de end-4, conservados porque el gestor respeta las fuentes ya guardadas en el perfil) y no están instaladas (`fc-match` → Liberation Sans); el manifiesto de la skin dice `Google Sans Flex`. (2) La instancia de Quickshell llevaba desde el 2026-11-04 19:17: con la fuente ya corregida en `config.json`, ni el vigilante ni `bwmSkin.reload` la cambiaron (la misma config en un `qs -p` aparte daba Google Sans Flex). No se pudo averiguar por qué esa instancia dejó de aplicarla (trampa ya conocida de instancias de muchas horas, regla 2).
* **Hecho:** `bwm-theme-manager.py` `replace_missing_fonts()`: al cargar el perfil de una skin, una fuente que fontconfig no conoce (`fc-list : family`) se sustituye por la de su `skin.json`, si ésa sí está; las del usuario instaladas se respetan. Aplicado a `config-default.json`/`config.json` (Rubik y Gabarito → Google Sans Flex) y reinicio de mantenimiento con `set default --restart-shell`. 3 pruebas en `tests/test_profile_fonts.py`.
* **Verificado:** captura recortada de la barra con Google Sans Flex; con la instancia nueva, cambiar `fonts.main` en `config.json` cambia la barra en vivo (probado y deshecho). **No probado:** un cambio de skin Retro → default con esta instancia nueva.

### 87. Contraseña tres veces al iniciar sesión: reintento de SDDM (2026-11-06)
* **Petición:** tras reiniciar en default (end-4) pidió la contraseña dos veces en el saludo de SDDM (que siempre tiene el aspecto de Omarchy) y otra en el bloqueo de default.
* **Causa (journal del arranque de las 13:26):** el autologin de SDDM entró bien, pero Hyprland 0.56.2 murió con SIGSEGV a los 0,3 s dentro de `libaquamarine.so.0.15.1` (`segfault at 1c8`, misma dirección en los dos intentos, log de Hyprland vacío: antes de leer la configuración). SDDM mostró entonces el saludo; el primer intento con contraseña volvió a caerse igual y el segundo arrancó; después vino el bloqueo de default, que es el inicio de sesión normal de esa skin. Intermitente: el arranque de las 10:12 del mismo día entró solo, sin cambios de configuración ni paquetes desde el 2026-11-04 y con el mismo orden de GPU; hubo caídas parecidas el 2026-10-31 y el 2026-11-02. Sin backtrace: systemd-coredump no guardó los volcados de Hyprland y no hay gdb.
* **Hecho:** `install-boot-theme.sh` escribe `Relogin=true` en `/etc/sddm.conf.d/autologin.conf` (sólo cuando hay autologin: default, Breeze o `--autologin`): si la sesión termina, SDDM vuelve a entrar solo. Efecto secundario: cerrar sesión también vuelve a entrar. Lo aplica el usuario con `sudo …/install-boot-theme.sh --sddm --auto` (reescribe la configuración de SDDM y la copia root del script que usa el servicio).
* **Verificado:** `bash -n` y el texto generado. El usuario ejecutó `--sddm --auto` (2026-11-07): `/etc/sddm.conf.d/autologin.conf` lleva `Relogin=true`, la copia de `/usr/local/sbin/bwm-boot-theme` está al día y `bwm-boot-theme.path` sigue activo. **No probado:** un arranque con la caída real.

### 88. Ajustes → Services: sólo lo que se usa en cada skin (2026-11-07)
* **Petición:** comparar Services con la de end-4, quitar opciones inútiles, el prompt de IA plegado y menos invasivo, arreglar las diferencias importantes, quitar del menú de Retro lo que no use y instalar lo que falte.
* **Comparación:** `ServicesConfig.qml` era idéntico al de `end-4/dots-hyprland` (`main`, `2f2a376`).
* **Hecho:** fuera «Networking → User agent» (sólo cambia cómo se identifican las descargas de favicons/imágenes) y el interruptor de GPS del tiempo (necesita geoclue, que no está y un sobremesa sin Wi-Fi no puede localizar; con la ciudad vacía `wttr.in` ya usa la IP, también en los plugins de Retro); el campo de ciudad lo dice. Cada sección se muestra sólo en la skin que la usa: IA (con `policies.ai` ≠ 0), prefijos y buscador web sólo en default (barra lateral y vista general de end-4); recursos, búsqueda aproximada e intervalo del tiempo fuera de Retro; reconocimiento de música fuera de Breeze. El prompt de IA queda plegado en una fila con su primera línea y, al abrirlo, un editor de 150 px con desplazamiento. Menú de Retro (`Catalog.js`): fuera tiempo en la barra/servicio/GPS, búsqueda aproximada, buscador web e intervalo de recursos (la barra y el lanzador de Omarchy no los leen). `omarchy-capture-screenrecording` respeta `screenRecord.savePath` (antes Retro siempre grababa en `~/Videos` aunque se pusiera otra carpeta). `songrec` (GURU, `~amd64`) declarado como recomendado de default y Retro; tabla de requisitos regenerada. Traducción en/es del nuevo texto de la ciudad.
* **Verificado:** página cargada con `qs -p` sin errores y captura recortada en default (IA plegada, sin user agent ni GPS); suite de pruebas OK; `bash -n` del shim y la carpeta resuelta (`~/Videos`). Después el usuario instaló `media-sound/songrec-0.7.3` (GURU, con `~amd64` en `package.accept_keywords/songrec`); `songrec listen` acepta las opciones de `recognize-music.sh` y ve el monitor de la salida por defecto. **No probado:** abrir el editor del prompt con clic, la página en Retro/Breeze, una grabación real y un reconocimiento real (envía la huella del audio a Shazam).

* **Después (2026-11-07):** la sección IA pasa al final de la página. Bajo cada carpeta de «Save paths» se ve la que está en uso: la escrita o, vacía, `~/Videos` (en Retro la carpeta XDG de vídeos) y «sólo se copia al portapapeles» (en Retro `~/Pictures/Screenshots`). Captura recortada comprobada; traducciones en/es.
### 89. Vesktop: sin línea a la izquierda en pantalla completa (2026-11-07)
* **Petición:** al poner a pantalla completa una emisión de Discord quedaba una barra a la izquierda.
* **Causa:** Hyprland daba a Vesktop el monitor entero (`fullscreen 2`, 2560×1440) y no era el borde de ventana (con `border_size = 0` seguía). Era una columna de 1 px dibujada por Discord con `--border-subtle`, que los temas de BWM ponen opaca (`outline_variant`, aquí `#5b4137`); el tema la vuelve a declarar en cada `.theme-dark`, así que no basta con cambiarla en `:root`. Las barras negras anchas a los lados son de la emisión, no de BWM.
* **Hecho:** plantillas `matugen/templates/vesktop.css` (default (end-4)/Breeze) y `omarchy/themed/vesktop.theme.css.tpl` (Retro): dentro de `:fullscreen` `--border-subtle` transparente y `border-left-width`/`border-top-width: 0` (también había una línea gris de 1 px arriba). Aplicado también al `bwm.theme.css` en uso, escrito en el mismo inodo. La regla `electron-render-unfocused` no reconocía Vesktop (su clase es `dev.vencord.Vesktop`): añadida.
* **Verificado:** con la emisión a pantalla completa, la columna `x=0` pasó de `#5b4137` a negro sin reabrir Vesktop; `configerrors` vacío. **No probado:** Retro (la plantilla se aplica al siguiente tema) ni otros vídeos a pantalla completa en Discord.

### 90. Pantalla completa limpia en todas las apps (2026-11-07)
* **Petición:** que lo de §3.89 (líneas o franjas a pantalla completa) no pase en ninguna otra app.
* **Hecho:** `modules/fullscreen.lua`, cargado tras `omarchy_windows` y `glass` para ganar a sus reglas: toda ventana a pantalla completa va sin borde, sombra, redondeo ni atenuado. **Se conserva la transparencia** (Omarchy/glass/la propia app): la primera versión la forzaba opaca y el usuario lo rechazó. En el CSS que BWM pone a apps: Firefox (`userChrome.css`, sin la línea inferior del marco en `inFullscreen`/`inDOMFullscreen`, copiado a los perfiles) y Stremio (`--outer-glow` nulo en `:fullscreen`; también en el CSS en uso). Lo que dibuja una app por su cuenta sin tema de BWM no se puede corregir desde fuera.
* **Verificado:** `Hyprland --verify-config` y `configerrors` limpios; `hyprctl getprop` de Vesktop a pantalla completa: `opaque` false, `no_dim` true, `border_size` 0, `rounding` 0; Firefox en ventana sigue con borde 1 y redondeo 18. Firefox carga el CSS nuevo al reiniciarse (no se reinició). **No probado:** pantalla completa de Firefox/Stremio ni un terminal translúcido de Retro a pantalla completa.

### 91. Dock de default (end-4) igual al de end-4 (2026-11-07)
* **Petición:** comparar el dock de default (end-4) con el de `end-4/dots-hyprland` (HEAD = `2f2a376`, el mismo de §3.69/§3.73) e igualarlo: aspecto, posición, ratón/autoocultado, apps ancladas, previsualizaciones, menús y Ajustes → Interfaz → Dock.
* **Comparación:** los cinco QML de `modules/ii/dock/` son idénticos salvo el minimizado de BWM (clic en la app activa con una ventana → `toggle-minimize.py toggle-app`). Opciones `dock.*` de `Config.qml` y `TaskbarApps.qml` idénticas (BWM añade `dock.omarchy`); la sección Dock de `InterfaceConfig.qml` igual salvo el interruptor del dock de Omarchy, visible sólo en Retro. Lo demás que usa el dock (`Appearance`, `AppSearch`) sólo cambia en Retro/Breeze o en la búsqueda por palabras clave.
* **Fallo principal (BWM):** `IllogicalImpulseFamily.qml` importaba `qs.modules.ii.dock` y después `qs.modules.ii.omarchyDock`, que también tiene un `Dock.qml`: el segundo import gana y `Dock {}` creaba el Dock de **Omarchy** (capa `omarchy-dock`, invisible sin su anfitrión, con su IPC `omarchy.dock`). Con `dock.enable` el dock de end-4 no salía nunca en default ni en Breeze. Arreglo: `import qs.modules.ii.omarchyDock as OmarchyDockModule` y `OmarchyDockModule.OmarchyDock {}`; los archivos de `omarchyDock` no se tocan (su `Dock {}` interno sigue resolviendo al suyo).
* **Diferencias corregidas:** reglas de capa de end-4 para `quickshell:dock` (`rules.lua`, `bwm-ii-dock`: `animation = "slide bottom"`, blur, `blur_popups`, `ignore_alpha = 0.79`; BWM no tenía ninguna de las reglas `quickshell:.*` de end-4 y sólo se añaden las del dock). Ventanas minimizadas: el ciclo de ventanas al pulsar la app y el clic en una miniatura hacían `activate()`, que llevaba al workspace 99; ahora `DockApps.activateToplevel()` restaura con `toggle-minimize.py restore <dirección>` las del 99 y activa las demás.
* **Diferencias justificadas:** minimizado con un clic en la app activa (función común de BWM, como en la barra de Breeze y Waffle); `pinnedApps` del perfil default `org.kde.dolphin` → `org.gnome.Nautilus` (Dolphin no está instalado y el gestor de archivos de BWM es Nautilus, como en el perfil de Breeze; el formato y el valor por defecto de `Config.qml` siguen siendo los de end-4); `dock.enable` sigue apagado por defecto, como en end-4; sin requisitos nuevos.
* **Verificado:** `Hyprland --verify-config` y `configerrors` limpios. Con `dock.enable` y `pinnedOnStartup` puestos un momento en `config.json`, la instancia real creó `quickshell:dock` en los dos monitores (75 px abajo) sin errores en `qs -c ii log` (sólo avisos previos); captura recortada del dock (fijar, Nautilus y kitty anclados, separador, apps abiertas con sus puntos y botón de la cuadrícula), borrada. Después se dejaron `enable`/`pinnedOnStartup` en `false` en `config.json` y `config-default.json`. Hizo falta un reinicio de mantenimiento (`set default --restart-shell`) antes de encontrar la causa; cargó del perfil `bar.cornerStyle` 2 sobre el 0 que había en `config.json`, que se devolvió a 0. **No probado:** clic real en el dock, menús contextuales, miniaturas, autoocultado al pasar el ratón ni restaurar una ventana minimizada desde él; no se cambió a Retro para ver el dock de Omarchy tras el import con nombre.

### 92. Steam ya no te cambia de workspace al reiniciarse por un cambio de fondo (2026-11-08)
* **Petición:** al cambiar de fondo Steam se reinicia (para cargar su tema) y te llevaba a su ventana, cambiándote de workspace.
* **Causa (eventos de socket2 durante `restart_app` real):** con `misc:focus_on_activate = true`, Steam activa su ventana nada más pedirle `steam -shutdown` (salto al workspace 2 antes de que hubiera ninguna protección: `hold_new_windows` y `FocusKeeper` empezaban después del cierre) y vuelve a pedir activación varias veces al arrancar. La regla temporal deja las ventanas nuevas en su workspace sin foco, pero no frena esas peticiones, y `FocusKeeper` sólo deshacía la primera de cada ventana en sus 2,5 s, así que el salto se repetía.
* **Hecho:** `bwm_windows.quiet_activation` (bloque `with`): apaga `misc:focus_on_activate` con `hyprctl eval` y lo devuelve a su valor original al terminar; con reinicios solapados (Steam y Firefox) lo devuelve el último, gracias a un archivo por proceso en `$XDG_RUNTIME_DIR/bwm-quiet-activation` con candado (los de procesos muertos no cuentan). `restart_app` lo usa desde antes de cerrar la app hasta colocar sus ventanas, y `reload-spotify.py` desde antes de matar Spotify. Las activaciones quedan como `urgent`. `restart_app` sondea cada 0,2 s los primeros 30 s para que `FocusKeeper` deshaga antes lo que se escape. Un `hyprctl reload` durante un reinicio devuelve también el valor de la configuración. 4 pruebas en `tests/test_quiet_activation.py`.
* **Verificado (Steam real, sin juego):** antes, salto al workspace 2 al cerrarse y otros tres al volver. Con el cambio, dos reinicios por `bwm_omarchy.py restart-steam`: en uno no hubo ningún cambio de workspace (sólo `urgent`); en el otro, un salto de 0,6 s a un workspace 2 recién creado justo antes de mapearse una ventana de Steam, deshecho por `FocusKeeper` (después se acortó el sondeo). `focus_on_activate` vuelve a `true` y Steam a su workspace. **Límites:** mientras Steam se reinicia (normalmente unos segundos; hasta `place_secs` si una ventana no vuelve), ninguna app toma el foco al activarse; no se probó el cambio de fondo completo ni Spotify.

### 93. Selector de fondos de end-4 en default (end-4) (2026-11-08)
* **Petición:** que el cambiador de fondos sea como el de dots-hyprland, copiado para la skin default.
* **Comparado** con `end-4/dots-hyprland` `2f2a376` (HEAD consultado): `modules/ii/wallpaperSelector/*.qml` y `services/Wallpapers.qml` ya eran idénticos en BWM y el panel se cargaba, pero nada lo abría: Alt+W lanzaba el rofi propio de `wallpaper-picker.sh`. end-4 lo abre con Ctrl+Super+T (`quickshell:wallpaperSelectorToggle`), Ctrl+Super+Alt+T elige uno al azar de la carpeta, y su capa baja desde arriba (`slide top`).
* **Hecho:** `wallpaper-picker.sh` en default llama a `qs -c ii ipc call wallpaperSelector toggle` (rofi de respaldo si Quickshell no responde; `qs` devuelve 0 también con «Target not found.», así que se exige salida vacía). Ctrl+Super+T y Ctrl+Super+Alt+T con `keybinds-manager.py`, sólo en default (`"skins": ["default"]`). Regla de capa `bwm-ii-wallpaper-selector` (`slide top`). Al elegir, el servicio usa `switchwall.sh` sin `--colors-only` (como end-4: fondo, perfil, paleta y aviso de reescalado); se le añade `bwm_boot.py render` para que el tema de arranque siga los colores como con `set-wallpaper.sh`. Retro y Breeze no cambian.
* **Verificado:** el script abre la capa `quickshell:wallpaperSelector` en el monitor enfocado (1200×690, carpeta `~/Pictures/Wallpapers`), sin rofi; captura recortada revisada y borrada; cerrado por IPC. `hyprctl binds` muestra los tres atajos, `configerrors` vacío, `bash -n` correcto. **No probado:** elegir un fondo desde el selector (no se cambió el fondo del usuario), la pulsación física de las teclas ni la animación de la capa.

### 94. Animaciones de default (end-4) y Retro clonadas de sus originales (2026-11-08)
* **Petición:** todas las animaciones (cambiar de workspace, abrir menús, cambiar de fondo…) iguales a las del original: las de end-4 en default (end-4) y las de Omarchy en Retro.
* **Antes:** las tres skins compartían en `appearance.lua` unas curvas MD3 «al estilo end-4» que no eran las de end-4 (popin 60 %, workspaces velocidad 4, sin `windowsMove`, `layers*`, `zoomFactor`…) ni se parecían a las de Omarchy (que no anima los workspaces y abre las capas con fundido). Los fondos se cambiaban con swww «grow» de 2 s en todas; end-4 y Omarchy pintan el fondo en su shell.
* **Comparado con:** `end-4/dots-hyprland` `2f2a376` (`hypr/hyprland/general.lua`, `rules.lua`) y `basecamp/omarchy` `quattro` `598e4eb` (`default/hypr/looknfeel.lua`, `qconsole.lua`, `apps/omarchy-shell.lua`, `apps/screenshot-selection.lua`, `shell/plugins/background/Background.qml`). Las animaciones internas de Quickshell ya eran las suyas: `Appearance.qml` (curvas y duraciones) idéntico al de end-4 y `Commons/Style.qml` al de Omarchy salvo `bwmScale`.
* **Hecho:** `config/hypr/skins/<id>/hypr/animations.lua`, que `appearance.lua` carga según la skin activa (con `pcall` y aviso si falla). default: curvas, animaciones y reglas de capa de animación de end-4 tal cual (barra «slide», cheatsheet/dock/osk «slide bottom», paneles laterales, popin 93 %/94 % para el resto, sin animación en vista general, sesión, polkit, selector de región…). Retro: curvas y animaciones de Omarchy (workspaces sin animación, capas con fundido, especiales tipo consola Quake) y sus capas sin animación (`omarchy-menu`, OSD, emojis, portapapeles, dock…; la barra Retro `quickshell:bar` y el selector de región estilo omasnap igual que `omarchy-bar`/`omasnap`). Breeze conserva las anteriores en su carpeta. Fondo: en default se carga el `Background.qml` de end-4 (estaba tras `background.enable`, nunca activo); en Retro, nuevo `modules/ii/omarchyBackground/OmarchyBackground.qml` = plugin background de Omarchy (sólo cambian los dobles clics del escritorio: `wallpaper-picker.sh` y `omarchy-theme-switcher`). `set-wallpaper.sh` en Retro apunta `~/.local/state/omarchy/current/background` y llama a la IPC `background transition` (o `setInstant` en un cambio de skin), como `omarchy-theme-bg-set`; swww queda debajo sin animación en default/Retro (en Breeze conserva «grow»). Sin el plugin WebP de Qt (no instalado aquí) el shell no abre los `.webp` de los temas: `set-wallpaper.sh` le pasa una copia JPG en caché (`~/.cache/bwm/omarchy-background`); requisito recomendado nuevo `qt-imageformats` (`dev-qt/qtimageformats`).
* **Verificado:** las tres `animations.lua` cargan con `Hyprland --verify-config` (sólo fallaba una línea errónea puesta a propósito para ver que se informa); `hyprctl reload` sin errores y `hyprctl animations` con los valores de end-4 en la sesión (default). La barra real recargó: capa `quickshell:background` en los dos monitores, sin errores en el log. `OmarchyBackground` en una instancia `qs -p` aparte: la IPC `transition` recorrió `revealProgress` 0→1 en ~0,85 s y terminó mostrando el fondo nuevo; `setInstant` cambia sin transición; reveló que Qt no decodifica WebP (de ahí el respaldo). Tests OK.
* **Probado en Retro (después, a petición):** el usuario instaló `dev-qt/qtimageformats` 6.11.2 (`libqwebp.so`); `set retro --restart-shell` para que el shell cargue el plugin. En Retro, `hyprctl animations` con los valores de Omarchy (workspaces desactivado, capas `fade`, especiales `slide top/bottom`), capa `omarchy-background` en los dos monitores, sin errores de configuración ni de decodificación WebP. Con el workspace 9 vacío a la vista un momento, la IPC `transition` mostró la franja diagonal abriéndose desde el centro y terminó en el fondo nuevo; vuelta al original. Capturas reducidas, revisadas y borradas. Vuelta a default por el camino normal (`set default`, sin reiniciar el shell): workspaces visibles y ventana con foco iguales, animaciones de end-4 y `quickshell:background` de vuelta.
* **Encontrado:** con `--restart-shell` el monitor principal pasó del workspace 2 al 1 (se devolvió a mano). El cambio normal no lo hace; `restore_focus` se ejecuta justo tras lanzar el nuevo Quickshell, antes de que arranque, así que algo del arranque cambia de workspace. Causa no identificada.
* **No probado:** un cambio de fondo real con `set-wallpaper.sh` en Retro (recolorea las apps) y en default, el fondo de end-4 visto en pantalla; Breeze sin cambios visuales. Las animaciones propias de cada QML portado de Omarchy son las de la versión vendida, no se compararon una a una con `598e4eb`.

### 95. Apagado, reinicio y cierre de sesión comunes: `bwm-power` (2026-11-08)
* **Petición:** encendido y apagado como parte de BWM, iguales en todas las skins (tras revisar cómo estaban).
* **Antes:** cada skin apagaba a su manera. El menú de sesión de end-4 (default y el bloqueo de pantalla) mataba los procesos con `kill` y apagaba sin esperar a que guardaran. El menú Sistema de Retro y Kickoff de Breeze llamaban a `systemctl poweroff/reboot` con todas las apps abiertas. Cerrar sesión era `hyprshutdown` (no instalado) o `hl.dsp.exit()`, y en end-4 `pkill Hyprland`.
* **Hecho:** `config/hypr/scripts/bwm-power`, basado en `omarchy-system` y `omarchy-hyprland-window-close-all` (Omarchy quattro, MIT). Avisa con `notify-send`, cierra cada ventana con `hl.dsp.window.close`, espera a que sus procesos terminen (`pidwait`, máximo `BWM_POWER_CLOSE_TIMEOUT`, 5 s; Omarchy usa 2 s, BWM da algo más para que Firefox/Steam guarden su sesión; sin `pidwait`, sondea con `kill -0`) y ejecuta la acción. Corre en un servicio `systemd-run --user`, así no muere con el panel o la terminal que lo pidió. Al apagar bloquea la tapa y el reposo con `systemd-inhibit`. Cerrar sesión usa `hyprshutdown` si existe; si no, `hl.dsp.exit()`. Suspender, hibernar y bloquear no cierran nada. `--dry-run` (o `BWM_POWER_DRY_RUN=1`) dice qué haría. Conectado en `Session.qml` (end-4: menú de sesión, bloqueo, waffle), `PlasmaKickoff.qml`, `bwm-menu.jsonc` (Sistema de Retro) y Alt+M (`keybinds-manager.py`, también el valor por defecto). Las pantallas siguen siendo de cada skin. Requisito recomendado del núcleo `procps` (`pidwait`); regenerada `docs/REQUIREMENTS.md` (incluye también `qt-imageformats`, que faltaba).
* **Verificado:** `--dry-run` de todas las acciones (13 ventanas y sus procesos detectados, orden final correcta; una acción desconocida sale con 2). El mismo cierre y espera con dos kitty de prueba en el workspace 9: las dos se cerraron y la espera terminó en 0,07 s. `systemd-run --user` con las mismas propiedades y variables llega a `hyprctl` y `notify-send`. Atajo Alt+M regenerado sin marcarse como modificado, `configerrors` vacío, QML recargado sin errores, tests OK.
* **No probado:** un apagado, reinicio o cierre de sesión real (cerraría tus apps); suspender e hibernar reales. Durante la prueba el foco acabó en el workspace 1 con Claude; no se pudo saber si fue el usuario y no se tocó.

### 96. Inactividad común y salvapantallas sólo en Retro (2026-11-08)
* **Petición:** salvapantallas de cada skin en su carpeta; y la nota del usuario en `todo.md`: sólo Retro con salvapantallas, las demás apagan la pantalla, opciones de suspensión conectadas entre skins y, en Retro, opción de apagar el monitor en vez del salvapantallas.
* **Antes:** las tres skins lanzaban el salvapantallas de terminal de Omarchy a los 5 min (`ScreensaverIdle.qml`, `scripts/launch-screensaver.sh`) y nada bloqueaba, apagaba las pantallas ni suspendía por inactividad. Además `loginctl lock-session` (botón «Bloquear» del menú de sesión de end-4) no hacía nada: en end-4 lo atiende hypridle, que BWM no usa.
* **Referencias:** end-4 `hypridle.conf` (2f2a376): bloqueo 300 s, DPMS 600, suspensión 900, bloquear antes de dormir. Omarchy quattro (598e4eb, `shell/plugins/services/idle/Service.qml`, `lock/Service.qml`): salvapantallas 150 s, bloqueo 300, pantallas apagadas 5 s después de bloquear; no suspende. KDE: sin salvapantallas.
* **Hecho:** nuevo `modules/ii/idle/BwmIdle.qml` (sustituye a `screensaver/ScreensaverIdle.qml`), con la sección común `idle` de `Config.qml` (`screen` 300, `screensaver` true, `lock` 600, `suspend` 0). A los `screen` s: si la skin trae `skins/<skin>/scripts/launch-screensaver.sh` (sólo Retro: movidos ahí `launch-screensaver.sh` y `bwm-screensaver.py`) y `screensaver` es true, lo lanza; si no, apaga las pantallas (`hl.dsp.dpms`), que se encienden con cualquier entrada. Bloqueo con la IPC `lock activate`; en modo salvapantallas, pantallas apagadas a `lock + 5` s. Suspensión con `bwm-power suspend`. `bwm-power lock` usa la IPC (no `loginctl`) y `suspend`/`hibernate` bloquean antes, como end-4; `Session.lock()` pasa por `bwm-power`. Ajustes → Estilo → «Inactividad» (interruptor del salvapantallas y botón de prueba sólo en Retro) y el menú de Retro con las mismas opciones. Los tiempos por defecto conservan los 5 min que tenía el salvapantallas; bloqueo a los 10 y sin suspensión para no cambiar de golpe un sobremesa que antes no se bloqueaba ni suspendía.
* **Verificado:** la barra real recargó `BwmIdle` sin errores y la IPC `screensaver` sigue. Copia aislada con `IdleMonitor` simulado, tiempos 4/7/11 s y todas las acciones sustituidas por un registro (comprobado con `grep` que no quedaba ninguna real): default apaga las pantallas a los 4 s, bloquea a los 7, suspende a los 11 y enciende al volver; Retro pone el salvapantallas a los 4, lo cierra y bloquea a los 7, apaga las pantallas a los 12 (bloqueo + 5) y enciende al volver. Ajustes → Estilo carga sin errores. Con el `IdleMonitor` real no hubo 2 s sin entrada en la sesión (uso activo), así que la detección real no se comprobó.
* **Incidentes:** (1) una primera copia de prueba sustituía las acciones con un `sed` por línea y la de suspender (sin `;`) escapó: ejecutó `bwm-power suspend` real, que bloqueó la sesión y suspendió el PC a las 02:30:19 unos 20 s; despertó con los monitores en sus workspaces. Se avisó al usuario; trampa añadida a §6 de AGENTS/CLAUDE. (2) Con una primera versión (tiempos propios de cada skin) cargada, Quickshell escribió en `config.json` y `config-default.json` su sección `idle` (incluido `suspend: 900`); se reescribió `config.json` con los valores nuevos y se quitó del perfil. Un `Config.qml` cargado escribe sus propiedades al archivo: al cambiar el formato de una sección, revisa los JSON.
* **No probado:** la inactividad real en ninguna skin, el salvapantallas en Retro tras moverlo y el encendido tras DPMS con la NVIDIA.

### 97. Pantalla de inicio y bloqueo de cada skin; SDDM común que entra solo (2026-11-08)
* **Petición:** la tercera parte de la revisión de encendido, inicio, salvapantallas y apagado: la pantalla de inicio (inicio de sesión y bloqueo) de cada skin en su carpeta, con SDDM como parte común de BWM; y la nota de `todo.md`: el inicio de sesión de default debería mostrar el fondo desenfocado como en dots-4.
* **Antes:** Retro pedía la contraseña en SDDM y su bloqueo era una copia del `hyprlock.conf` de Omarchy 3 (`lock/OmarchyLockSurface.qml`); default y Breeze entraban solos y pedían la contraseña con el bloqueo de end-4, también en Breeze. En end-4 el desenfoque del bloqueo lo pinta `Background.qml` (sube a la capa Overlay y se desenfoca al bloquear); BWM no cargaba ese fondo hasta §3.94, así que el bloqueo de default no mostraba el fondo desenfocado. Retro decidía «entré por SDDM» con `XDG_SESSION_PATH`, que también vale para el autologin, así que dejarlo entrar solo lo habría dejado sin contraseña.
* **Hecho:** `Lock.qml` elige el bloqueo de la skin. default: el de end-4 (`lock/LockSurface.qml`, sin cambios), con el fondo desenfocado de `Background.qml`, que ya se carga desde §3.94 (`lock.blur` activado como en end-4). Retro: `modules/ii/omarchyLock/LockView.qml` = la vista de bloqueo de Omarchy 4 (`shell/plugins/lock/LockView.qml`, quattro 598e4eb, MIT, sin cambios) y `OmarchyLockSurface.qml` la conecta a `LockContext` (PAM, huella, llavero). Breeze: `modules/ii/plasmaLock/PlasmaLockSurface.qml`, diseño propio que imita la pantalla de bloqueo Breeze de Plasma 6: fondo con el reloj grande; al mover el ratón o teclear, fondo desenfocado y oscurecido, reloj arriba, avatar (`~/.face.icon`, `~/.face` o la inicial), nombre, contraseña y botón de desbloquear (`go-next` de breeze-icons); vuelve al reloj a los 10 s sin actividad. `install-boot-theme.sh`: `apply_login_mode` pone el autologin de SDDM siempre (`--autologin` queda por compatibilidad). `LockScreen.qml` bloquea al arrancar en todas las skins (`lock.launchOnStartup`).
* **Verificado:** las vistas de Breeze (reposo y despierta) y de Omarchy 4 en ventanas aparte del workspace 9 con un `LockContext` real, sin bloquear la sesión: capturas recortadas revisadas y borradas; sin errores de QML. El workspace 9 mostró el fondo de end-4 pintado por `Background.qml`. `bash -n` del script. La barra real recargó sin errores.
* **Pendiente del usuario:** `sudo ~/.config/hypr/scripts/install-boot-theme.sh --sddm --auto`. Hasta entonces la copia root del servicio quita el autologin al arrancar en Retro, y Retro pediría la contraseña dos veces (SDDM y su bloqueo).
* **Después (2026-11-08):** el desenfoque de default comprobado sin bloquear: una copia de `Background.qml` con «bloqueado» forzado, en la capa Overlay del LG unos segundos, mostró el fondo desenfocado (radio 100, zoom 1,1, como end-4). La sesión en curso empezó (2026-11-07 23:04) antes de que default cargara `Background.qml` (§3.94), por eso su bloqueo de inicio no lo tenía.
* **Fondo negro al bloquear en default (2026-11-08):** con un bloqueo real se veía negro. end-4 pone `misc.session_lock_xray = true` (`general.lua`): sin esa opción Hyprland no dibuja nada bajo la superficie de bloqueo, que en end-4 es transparente. Nuevo `skins/default/hypr/lock.lua` con esa opción, cargado por `appearance.lua` sólo si la skin tiene ese archivo (Retro y Breeze pintan su propio fondo). Comprobado: `--verify-config`, `configerrors` vacío y `getoption` = true tras recargar. **No probado:** volver a bloquear para verlo.
* **No probado:** bloquear de verdad en cada skin (desbloquear con PAM, huella), el desenfoque visto en un bloqueo real y un arranque real con el autologin en Retro. Durante la prueba un `pgrep -f` con el patrón dentro del propio comando mató la shell de la herramienta (trampa conocida, §5 de AGENTS); la instancia de prueba se cerró después por PID.


### 98. Página propia de Inactividad: salvapantallas y apagar los monitores por separado (2026-11-08)
* **Petición:** una opción separada en Ajustes para el salvapantallas y para apagar el monitor al cabo de un rato.
* **Hecho:** nueva página `modules/settings/IdleConfig.qml` («Inactividad»/«Idle») en `settings.qml`, `plasmaSettings.qml` (id `idle`) y el menú de Retro (`Catalog.js`, ruta `setup.settings.system.idle`; el índice numérico se añade al final para no mover los demás). Secciones: Salvapantallas (sólo Retro: interruptor, «Mostrar tras», probar), Pantallas («Apagar los monitores tras») y Bloqueo y suspensión. Sale de Ajustes → Estilo. Tiempos independientes: clave nueva `idle.screensaverTime` (150 s, como Omarchy) para el salvapantallas y `idle.screen` sólo para apagar los monitores; se quita el apagado a `lock + 5` s de §3.96. Al apagarse los monitores se cierra el salvapantallas. Arreglado de paso el ✓ de «Salvapantallas» del menú de Retro, que leía la clave antigua `screensaver.enable`.
* **Verificado:** página cargada con `qs -p settings.qml` en una ventana flotante del workspace 10 sin errores y captura revisada (en default (end-4) sin la sección del salvapantallas); traducciones JSON válidas; `configerrors` vacío. **No probado:** la página en Retro y en el menú de Retro, ni los tiempos reales de inactividad.
* **Después (2026-11-08):** los tiempos en minutos y segundos. En Ajustes, cada fila tiene dos casillas (min y s, de 5 en 5) y pone «Nunca» con 0; se siguen guardando en segundos. En el menú de Retro, unidad `duration` de `Catalog.js`: la fila dice «5 min 30 s» o «Nunca» y el editor acepta «5:30», «5» (minutos) o «5m 30s». Cada sección explica qué hace: apagar los monitores sólo apaga las pantallas (el equipo sigue con música, descargas y juegos); suspender duerme el equipo entero y lo para todo, por eso está apagado por defecto. Comprobado: las funciones de `Catalog.js` en un `qs -p` aparte (formatos, validación y límites) y captura de la página en default (end-4). **No probado:** cambiar un valor con clic ni el editor dentro del menú de Retro.

### 99. Estudio de Omarchy 4.5 y dos correcciones de seguridad (2026-11-08)
* **Petición:** revisar a fondo la actualización grande de Omarchy, listar sus novedades, aplicar seguridad si hace falta y estudiar qué añadir y qué no, sin añadir atajos.
* **Hecho:** `docs/OMARCHY_4_5.md` (novedades, tabla de seguridad, qué sí/quizá/no). Comparado `quattro` `d9cc361c` (v4.5.0 = `ac2690cd`, 2026-11-04) con lo vendido: 362 commits desde el 2026-10-23, shims de `omarchy-shims`, `Commons/`, `Ui/` y los plugins copiados. Las notas oficiales de la release no se leyeron (sin `gh`).
* **Seguridad aplicada:** `omarchyNotifications/Service.qml` ya no guarda en disco (`live.json`/historial) las notificaciones con la pista `transient`; `omarchy-agent-account-add --reauth` sin cuenta falla en vez de añadir una. Nada más lo necesitaba: los fallos de inyección Lua/webapp de upstream no existen en BWM, `Security.js` es idéntico y `bwm-addons.py`/`install-boot-theme.sh` ya validan.
* **Verificado:** `bash -n`; el log de `qs -c ii` tras editar `Service.qml` sólo trae los avisos conocidos de `ShellIpc`. **No probado:** que una notificación transitoria real deje de persistir; el historial anterior no se ha limpiado ni leído.
* **No hecho (por decisión del usuario):** ningún atajo. Pendiente según el estudio: refrescar `Commons/`/`Ui/`, agentes/Tailscale, salvapantallas nativo.

### 100. `Commons/` y `Ui/` de Omarchy al día (2026-11-08)
* **Petición:** primer punto del estudio de §3.99: refrescar las librerías de Omarchy vendidas.
* **Hecho:** `Commons/` y `Ui/` copiados de `quattro` `d9cc361c` y vueltos a aplicar los parches de BWM (`Color.qml` ruta y vigilancia, `Style.bwmScale`, `I18n.omarchyPath`, línea de `ScreenMoveRemap` en `Ui/qmldir`); lo demás queda idéntico a upstream (anotado en `Commons/README.md`). Cambios que llegan: `ShellIpc` sólo habilita el primer manejador vivo de cada destino y el siguiente toma el relevo (`IpcRegistry.leads`), catálogos de traducción leídos siempre de forma síncrona (`preload: false`, `blockAllReads`), `PopupMenuRow` nuevo, `WidgetButton.held` pasa a `heldButtons`/`pressFeedbackButtons` (nadie en BWM usaba `held` fuera de `Ui/`), desplegables que se cierran con un segundo clic, `PanelSlider` que llega al final, glifos medidos sin el píxel de más, `PopupCard` sin tragarse clics al cerrarse, h/j/l en diálogos y desplegables.
* **Verificado:** en una copia aislada (`qs -p`), los 40 tipos de `Ui` compilan, dos `ShellIpc` con el mismo destino dejan uno activo y el otro toma el relevo al destruir el primero, sin avisos. Compilación de los 101 QML de Retro con la copia actual y con la actualizada: mismo resultado (69 compilan; los 32 restantes fallan igual en ambas por cómo resuelve tipos hermanos esta prueba). Shell real (skin default) recargado sin errores nuevos; desaparecen los 26 avisos «Handler was registered but will not be used» de los `ShellIpc` de los paneles de Omarchy y siguen los 57 destinos IPC.
* **Probado en Retro (después, a petición):** `set retro` → `set default` sin reiniciar Quickshell. En Retro, sin errores nuevos en el log ni ningún aviso de `ShellIpc` duplicado (sólo los de `IpcHandler` simples de `RetroBarContent`/`Keybindings`, ya conocidos), 61 destinos IPC, barra correcta (captura recortada) y panel de audio dibujado bien con los deslizadores al 100 % hasta el final de la pista; capturas borradas. Al volver, workspaces 1 y 10 iguales y `configerrors` vacío; la ventana con foco pasó de Claude a Vesktop (mismo workspace), sin saber si por el cambio o por el usuario.
* **Encontrado:** con dos monitores, abrir un panel por IPC (`qs -c ii ipc call omarchy.audio open`, que usa el menú de Retro, o `omarchy-shell`) lo abre en la barra del LG aunque el foco esté en el MSI. `omarchy-shell` resuelve con `IpcRegistry.handlerFor`, que no cambió, y da el mismo resultado: casi seguro ya pasaba antes; no se comprobó con la versión anterior. Pendiente: que el panel se abra en el monitor con foco.

### 101. Los paneles de Omarchy se abren en el monitor con foco (2026-11-08)
* **Petición:** arreglar lo encontrado en §3.100: abrir un panel por IPC (menú de Retro, `omarchy-shell`) lo abría en la barra del LG aunque el foco estuviera en el MSI.
* **Causa:** cada barra tiene su copia de cada panel y responde la copia que se registró primero, sin mirar el monitor.
* **Hecho (parche BWM a lo vendido, anotado en `Commons/README.md`):** `Ui/Panel.qml` expone `ipcScreenName` (pantalla de su ventana) y ancla sus manejadores en `Commons/IpcRegistry.qml`; `leaderFor()` prefiere la copia del `Hyprland.focusedMonitor` (sin ella, la primera). `reconcile()` (al registrar, cambiar de destino o de pantalla, y al cambiar el foco de monitor) apaga primero el líder viejo y enciende el nuevo en el ciclo siguiente: con un binding los dos coincidían un instante y Quickshell avisaba «will not be used» en cada cambio de foco. `ShellIpc` empieza con `enabled: false`. Vale para todos los paneles (los que declaran su propio `ShellIpc` también heredan de `Panel`); los plugins de terceros que no heredan de `Panel` siguen con la primera copia.
* **Verificado:** en una copia aislada (`qs -p`), dos manejadores anclados a «DP-1»/«DP-2»: responde el del monitor con foco, y al intercambiar las pantallas la llamada cambia de copia, sin avisos; los 40 tipos de `Ui` compilan y el relevo al destruir una copia sigue. Shell real (default) recargado sin errores nuevos, mismos 57 destinos IPC.
* **Probado en Retro (después):** seguía abriéndose en el LG. Causa: `Hyprland.focusedMonitor` de Quickshell queda vacío (o con un valor viejo) hasta que el foco cambia de monitor, y sin él gana la primera copia. `IpcRegistry` lee ahora el monitor con foco de `hyprctl -j activeworkspace` al arrancar y sigue los eventos `focusedmon`/`focusedmonv2` (`focusedScreen`). Con el foco en el LG, `omarchy.audio open` abrió el panel en el LG; con el foco pasado un momento al MSI, en el MSI (capa `omarchy-keyboard-panel` en DP-2 y la de cierre en DP-1); foco devuelto a la misma ventana y workspaces sin cambios. Sin errores nuevos; el aviso «will not be used» de `omarchy.system-update` (un `ShellIpc` sin `Panel`) sale una vez por recarga y ya salía antes. Vuelta a default por el camino normal, misma ventana con foco, `configerrors` vacío.
* **No probado:** abrirlo desde el menú de Retro con el teclado ni con `omarchy-shell` (usa el mismo manejador activo).

### 102. Paneles de agentes y Tailscale al día; `OMARCHY_PATH` en la sesión (2026-11-08)
* **Petición:** seguir con el estudio de §3.99: punto 2, los paneles de agentes y Tailscale de Omarchy al día.
* **Encontrado:** el panel de agentes de BWM nunca había mostrado datos: sus scripts buscan los colectores y sus módulos en `$OMARCHY_PATH/bin` y `$OMARCHY_PATH/shell/plugins/agents`, y esa variable no existía en la sesión (`~/.local/state/omarchy/agents/usage/` vacío desde el 2026-10-25). Lo mismo rompía, en silencio, los recordatorios (`ReminderFlow.qml` ejecutaba `undefined/bin/omarchy-reminder`), el globo de Elsewhen (`world.json`) y las traducciones del menú de Retro (`menu.json`). `omarchy-agent-account-add` llamaba además a `omarchy-default-agent` y `omarchy-cmd-missing`, que no existían.
* **Hecho:** `OMARCHY_PATH=~/.config/hypr/omarchy` en `modules/environment.lua` (y exportada a D-Bus/systemd en `autostart.sh`), como en Omarchy. En `config/hypr/omarchy/` enlaces relativos a lo que espera Omarchy: `bin` → `scripts/omarchy-shims`, `default` → `Commons/omarchy/default`, `shell/plugins/agents` y `shell/plugins/panels/elsewhen`; `themes/` ya estaba (el selector de temas ya usaba esa ruta por defecto). Paneles de `quattro` `d9cc361c` fusionados a tres vías desde su base (`84cfb939`) conservando los parches de BWM (`import "."`, `Qt.callLater` protegido, Tailscale oculto sin `tailscale`): Tailscale (lista virtualizada, avisos de Taildrop), agentes (todos los proveedores, `collectors.py`, 41 logos, secciones sólo para suscripciones). El agents Panel importa el `Model.js` de Elsewhen desde `omarchy-plugins/omarchy-elsewhen`. Scripts `omarchy-agent-*` de upstream sin cambios (23 colectores de uso), salvo los de modelos locales, herdr y crash. Sustitutos de BWM: `omarchy-agent-local` (sin modelos locales: `refresh/status/list` no hacen nada, el resto avisa), `omarchy-default-agent` (lee/escribe `~/.config/omarchy/defaults/agent`; no instala con mise, avisa si falta), `omarchy-launch-browser` (navegador de `xdg-settings`, `--private` según el navegador), `omarchy-launch-tui` (`bwm-terminal`), `omarchy-cmd-missing`, `omarchy-pkg-present` (qlist/flatpak). Logos de proveedores anotados en `THIRD_PARTY_NOTICES.md`.
* **IPC en el monitor con foco (§3.101), afinado:** al arrancar, `Hyprland.focusedMonitor` puede nombrar el monitor equivocado; ya no pisa a `hyprctl`/eventos. Y ninguna copia se enciende hasta conocer el monitor con foco (`focusKnown`, respaldo de 2 s): encender la del LG y pasar a la del MSI al cargar hacía avisar «will not be used» una vez por panel (7 avisos al arrancar Retro). Tras el cambio, una recarga sólo deja el aviso ya conocido de `RetroBarContent`.
* **Verificado:** compilación aislada de los 101 QML de Retro igual que antes (69, mismos fallos de la prueba). `omarchy-agent-usage-update` con la variable: 23 registros en 1,4 s; Claude y Codex con datos locales y Codex con sus 2 límites (sólo se miraron claves y banderas). `hyprctl reload` + `set retro --restart-shell` con la variable: el shell la tiene, 61 destinos IPC, el propio panel regeneró los registros. Panel de agentes abierto por IPC en el MSI (monitor con foco): Codex con sesión/semana, Claude Code «Sign-in required» (la CLI `claude` no está en el PATH); captura recortada y borrada. Audio, pantallas y red se abren en el MSI; con el foco pasado un momento al LG, en el LG; foco devuelto a la misma ventana. Vuelta a default normal, misma ventana con foco, `configerrors` vacío.
* **No probado:** pulsar en el panel (añadir cuenta, «Make something cool», elegir agente), Tailscale (no instalado: el widget sigue oculto), un recordatorio real, el menú de Retro en es-MX (ahora con `menu.json`; en inglés no cambia) y una sesión nueva desde el inicio (la variable llega a las apps lanzadas tras la recarga y al shell reiniciado; el resto la tendrá al volver a iniciar sesión).

### 103. Salvapantallas nativo de Omarchy y opciones de Hyprland de Retro (2026-11-08)
* **Petición:** seguir con el estudio de §3.99: puntos 3 (salvapantallas nativo) y 4 (opciones de Hyprland).
* **Salvapantallas:** en Omarchy 4.5 es un programa aparte, [omacom/omarchy-screensaver](https://github.com/omacom/omarchy-screensaver) (Rust, MIT): una capa Wayland `org.omarchy.screensaver` por monitor con efectos ttfx, que se cierra con cualquier tecla, clic, rueda o movimiento, oculta el cursor y lo devuelve al salir. `skins/retro/scripts/install-screensaver.sh` lo compila con cargo desde `b3026b63` en `~/.local/share/bwm/omarchy-screensaver` (≈35 s, sin sudo); también `install.sh` (paso 10b, con cargo). `launch-screensaver.sh` lo usa si está, con el logo de BWM (`skins/retro/screensaver.txt`) salvo que exista el del usuario (`~/.config/omarchy/branding/screensaver.txt`, como en Omarchy); si no, el de terminal de antes. `BwmIdle.stop()` también lo cierra (SIGTERM). Nueva función IPC `lock isLocked` (`LockScreen.qml`), que el programa consulta con `omarchy-shell lock isLocked` para no arrancar con la sesión bloqueada. Requisito recomendado de Retro `omarchy-screensaver` (lo trae BWM); tabla regenerada.
* **Opciones de Hyprland:** `skins/retro/hypr/misc.lua` (cargado por `appearance.lua` junto a `lock.lua`, sólo en la skin que lo tenga): `render.cm_auto_hdr = 0` (una ventana a pantalla completa no pasa la pantalla a HDR), y `misc.bell_sound = "none"` y `misc.no_donation_nag = true` sólo si existen (Hyprland 0.56.2 no las tiene; protegidas con `hl.get_config`, como Omarchy #18047). `appearance.lua` repone antes `cm_auto_hdr = 1`, porque `hyprctl reload` no devuelve a su valor por defecto lo que nadie vuelve a poner. No se porta el apagado de animaciones con render por CPU (equipo con NVIDIA).
* **Verificado:** compilación e instalación (`cargo install --locked`), render sin pantalla con el logo, `lock isLocked` → `false`; ejecución real con `force`: dos capas `org.omarchy.screensaver`, cursor oculto, captura recortada del MSI con «BWM» animado (borrada); al cerrarlo, sin proceso ni capas, cursor visible y mismos workspaces y ventana con foco. `hyprctl reload` en Retro: `cm_auto_hdr` 0, sin errores; `Hyprland --verify-config` ok; 102 pruebas OK. Durante la prueba un `pkill -f` con el patrón dentro del propio comando mató la shell de la herramienta (trampa conocida); el salvapantallas ya se había cerrado y el cursor estaba restaurado.
* **No probado:** que lo lance la inactividad real ni que se cierre moviendo el ratón (se cerró con SIGTERM), la vuelta a default con `cm_auto_hdr` repuesto a 1 (no se cambió de skin) y un juego HDR a pantalla completa.

### 104. Fin del estudio de Omarchy 4.5: fondo y notificaciones (2026-11-08)
* **Petición:** seguir con los puntos 5 y 6 del estudio de §3.99.
* **Fondo sin parpadeo negro (5):** ya estaba. `omarchyBackground/OmarchyBackground.qml` (§3.94) viene de `598e4eb`, posterior a «Slide background changes on every monitor without a black flash» (#17179); el `Background.qml` de `d9cc361c` sólo difiere en los dobles clics que BWM cambió. Las introducciones de fondo (#16875…) siguen en «quizá».
* **Notificaciones (6):** de `omarchyNotifications/` sólo diferían `Service.qml` y el shim `omarchy-notification-send`, sin parches de BWM pendientes (el de `transient` de §3.99 ya es el de upstream). Copiados de `d9cc361c`: `--transient` en el envío (no se guarda ni se repone tras reiniciar), la ventana de la app se encuentra también con nombres de varias palabras («Telegram Desktop» → `org.telegram.desktop`) y la IPC `notifications act` (cierra, pulsa su único botón o toma el teclado sobre la última tarjeta). El atajo de Omarchy que la llama (Super+coma) no se añade.
* **Verificado (en Retro, recarga en caliente):** `act` aparece en la IPC; una notificación con `--transient` no llegó a `~/.local/state/omarchy/notifications` y otra normal sí; dos `act` cerraron las dos y el tercero devolvió `none`. La entrada de prueba se quitó del historial y el servicio se recargó para que no la volviera a escribir. Sin errores nuevos en el log.
* **No probado:** `act` sobre una tarjeta con botones o que abre una app, y el enfoque de una app de nombre compuesto.

### 105. La barra desaparecía: demonios fuera del proceso que los lanza y vigilante del shell (2026-11-08)
* **Petición:** en Retro no se veía la barra.
* **Encontrado:** no había ninguna instancia de Quickshell (sólo el fondo). La anterior, relanzada a las 14:06 con `--restart-shell` desde otra sesión de Claude, dejó de escribir su log a las 16:54:23 sin fallo registrado (ni coredump, ni informe de Quickshell, ni OOM); `window-guard.py`, relanzado también desde una sesión de IA (§3.81), tampoco estaba. Lo lanzado por `autostart.sh` seguía vivo. Al relanzarlo desde la app de Claude, el shell quedó en el cgroup `app-com.anthropic.Claude-….scope`: vive y muere con quien lo lanza. No se pudo demostrar qué los mató; en ese mismo segundo el panel de agentes recargaba sus 23 registros, pero un estrés aislado de 60 s con 23 `FileView` reemplazados por `mv` no reprodujo un fallo. Además `set <skin> --restart-shell` fallaba con `JSONDecodeError` si no había ningún shell (`list -j` no imprime nada).
* **Hecho:** nuevo `scripts/bwm_session.py`: `spawn()` lanza un demonio con `hl.dsp.exec_cmd` (hijo de Hyprland, en `session-1.scope`, con el entorno de la sesión; si no hay compositor, proceso aparte sin `BWM_SKIN_SWITCH`), `shell_instances()` (vacío sin JSON), `ensure_shell()` (nunca un segundo shell) y `bwm_session.py ensure-shell`. El gestor lo usa para Quickshell, swaync y hyprpolkitagent. `window-guard.py watch` comprueba cada 10 s si hay un shell `ii` y, tras dos comprobaciones sin él y sin un cambio de skin en curso (candado del gestor), lo relanza. 7 pruebas en `tests/test_session.py`.
* **Verificado (sesión real):** shell y `window-guard.py` relanzados así: los dos en `session-1.scope`, colgando de Hyprland, barra en los dos monitores. Matado el shell por PID: volvió solo a los 17 s, una sola instancia, sin errores de carga. `configerrors` vacío.
* **Efecto:** un `pkill quickshell` deliberado también se deshace a los ~20 s; para pararlo de verdad, para antes `window-guard.py`. **No probado:** la causa original de la muerte.

### 106. Escritorio tradicional por workspace en Retro (Omarchy 4.5) y clic para enfocar en Breeze (2026-11-08)
* **Petición:** añadir todo lo del punto 4.1 de `docs/OMARCHY_4_5.md`: los workspaces flotantes con barras de título de Omarchy, con nuestro plugin en vez del suyo, y lo útil para Breeze; sin atajos.
* **Plugin (`src/hyprbars`):** `plugin:hyprbars:workspace_tag` (barra sólo en ventanas flotantes con esa etiqueta; vacío = todas, Breeze), `%WINDOW%` en las acciones de botones y doble clic (dirección de la ventana de esa barra), ambos de omarchy-hyprland-titlebars `b351b14`, y `plugin:hyprbars:snap` (Breeze, por defecto sí; Retro no). El manejador de Alt/Super + arrastre de Breeze (salía de pantalla completa y **borraba todas las etiquetas** de la ventana) sólo actúa con el snapping activo. Las barras se recalculan al recargar. Compilado e instalado con `make install`; la detección de CSD se conserva (Firefox, Steam… sin barra doble).
* **Retro:** `skins/retro/hypr/workspace-modes.lua` = `workspace-modes.lua` + `workspace-layouts.lua` de Omarchy `60bf28ee`, cargado al final de `appearance.lua` (lo de la skin gana a lo común). Mismo mecanismo: etiquetas `omarchy-mode-floated`/`omarchy-floating-workspace`, regla de apertura por rangos, colocación con cascada, clic para enfocar sólo en el workspace flotante activo, desmaximizar al abrir otra, sombras y opacidad (salvo modo vidrio de BWM, su «glassy»). Adaptado: global `o` sólo con `workspace_mode` (los archivos guardados son los de Omarchy), workspace 99 de minimizadas excluido, apps flotantes de BWM con tamaño propio excluidas de la regla de apertura, plugin cargado con `hyprctl plugin load` (con candado, nunca descargado) la primera vez que algo flota, colores del tema activo, minimizar con el shim de BWM (sólo con dock). Shims `omarchy-hyprland-workspace-layout-{toggle,default,current}` de Omarchy (minimizadas por `from_ws_<n>`, sólo en Retro) y `bwm-workspace-layout-set <modo>` para el menú. Barra: el glifo del workspace activo lee su modo y lo cambia al pulsarlo (IPC `omarchy.workspaces refresh`). Menú → Estilo → Layout de workspace (este workspace y predeterminado). `bwm-theme-manager.py` ya no apaga hyprbars al entrar en Retro. El dock de Omarchy pasa a salir sólo en workspaces flotantes (antes, en cualquiera sin ventanas en mosaico).
* **Breeze:** `skins/plasma/hypr/misc.lua` con clic para enfocar (`follow_mouse = 0`, política predeterminada de KWin). Lo demás de la lista ya estaba o no aplica: flota desde el primer fotograma por `plasma-float-all`, los botones de la barra ya actúan sobre su ventana (cerrar/maximizar nativos, minimizar con su dirección) y al abrir otra ventana Hyprland ya desmaximiza (`on_focus_under_fullscreen` 2). No se añadieron sombras (se quitaron a propósito en §3.7).
* **Verificado (sesión real, Retro):** `--verify-config` y `configerrors` limpios; con el modo flotante guardado en el workspace 9, el plugin se cargó solo y dos kitty de prueba abrieron flotando a 1100×760, escalonadas 48 px, con las etiquetas y barra (`hyprbars-csd`); captura recortada con título a la izquierda y − □ × (borrada). `follow_mouse` 0 en el 9 y 1 al volver. Pasar a mosaico quitó etiquetas, flotación y barras; volver a flotante las recolocó; mover una ventana al 8 la devolvió al mosaico; una maximizada se desmaximizó al abrir otra; las órdenes de cerrar y maximizar con `%WINDOW%` sustituido funcionan; `toggle` y `bwm-workspace-layout-set` en el 9 guardan/borran el archivo. Sin el modo guardado, una recarga devolvió las ventanas al mosaico y las opciones del plugin a su valor por defecto. 109 pruebas OK. Ventanas, regla y archivos de prueba retirados; el plugin queda cargado (desactivado) hasta cerrar sesión.
* **No probado:** pulsar los botones y arrastrar por la barra con el ratón, el glifo de la barra con clic, el menú, el modo `scrolling` visto en pantalla, Breeze con el clic para enfocar (no se cambió de skin) y cambiar de skin con un workspace flotante.

### 107. Pestañas que se pueden arrastrar y barras más fieles a Omarchy (2026-11-08)
* **Petición:** en un workspace flotante, arrastrar una pestaña de Firefox movía la ventana; ver cómo lo resuelve Omarchy y acercar el modo al suyo («prácticamente clonado aunque adaptado»).
* **Causa:** `hyprbars-plasma` convertía en arrastre de la ventana cualquier pulsación en los 50 px de arriba de una ventana sin barra (pensado para encajar en Breeze las apps con barra propia). Con `workspace_tag` (§3.106) eso alcanzaba además a todas las ventanas sin barra de Retro, también en mosaico. El usuario tenía el workspace 1 flotante desde las 22:45. **Omarchy no intercepta nada:** la app pide moverse (`xdg_toplevel.move`) y su plugin pone barra a todas las ventanas flotantes con la etiqueta, también a las que traen la suya.
* **Plugin:** sin intercepción en ninguna skin (en Breeze se conserva el doble clic para maximizar; el snapping sigue a los movimientos que pide la app, `s_pNativeDraggedWindow`). Con `workspace_tag`, barra en todas las ventanas etiquetadas aunque traigan la suya, y título con el nombre de la app de su `.desktop` (`appName.cpp` de omarchy-hyprland-titlebars, sin cambios); Breeze sigue con el título de la ventana. También de Omarchy: resaltado del botón bajo el puntero (color de su icono al 18 %), `button_rounding` (Retro 0, como Omarchy; -1 = círculo de antes), `bar_text_weight`, y redimensionar desde el borde de encima de la barra. Compilado e instalado con `make install`.
* **Retro:** las barras sólo se activan si el hyprbars cargado es esta versión (tiene `button_rounding`): el de la sesión, cargado antes, tenía el arrastre defectuoso; hasta volver a iniciar sesión los workspaces flotantes van sin barras. `float_for_mode` reclama también las ventanas que la regla de apertura hizo flotar y cuyas etiquetas de regla llegaron después del evento de apertura (Firefox, Claude): antes no habrían vuelto al mosaico al acabar el modo.
* **Verificado (sesión real, Retro):** `--verify-config` y `configerrors` limpios; con el plugin viejo cargado, un workspace flotante de prueba hizo flotar su kitty a 1100×760 con `enabled = false`; en el workspace 1 del usuario las seis ventanas quedaron reclamadas sin moverse. El plugin compila sin errores.
* **Tras volver a iniciar sesión (2026-11-08):** seguía sin barras: el plugin no se había cargado (ni rastro en el log de Hyprland). La carga se lanzaba mientras Hyprland leía su configuración al arrancar, cuando `hyprctl` aún no responde, y fallaba en silencio. Ahora espera a que `hyprctl` responda (hasta 30 s). Con `hyprctl reload` en la sesión se cargó y las ventanas del workspace 1 recibieron barra (kitty y también Claude, que trae la suya). **No probado:** el arranque con la espera nueva (requiere otro inicio de sesión).
* **Después (2026-11-09):** las barras desaparecían al arrastrar una ventana: `handleMovement` (arrastre por la barra) y el Alt/Super + arrastre de Breeze llamaban a `clearTags`, que borraba **todas** las etiquetas de la ventana (pensado para quitar las `snapped*` de quick-tile), también `omarchy-floating-workspace`. Ahora `clearSnapTags()` quita sólo `snapped` y `snapped_<borde>`. Compilado e instalado con `make install`; en la sesión sigue el plugin anterior hasta volver a iniciar sesión. Una recarga devolvió las etiquetas y las barras a las ventanas del workspace 1.
* **No probado:** el plugin nuevo (no se puede recargar en caliente; un Hyprland anidado con el aislamiento del verificador de Omarchy —`XDG_RUNTIME_DIR` propio, puntero virtual del anidado— muere con SIGKILL al arrancar, también lanzado con `setsid`, sin poder ver quién lo mata: no hay strace). Pendiente tras volver a iniciar sesión: arrastrar pestañas, barras en Firefox, título de la app, resaltado, redimensionar por arriba y snapping de Breeze con apps de barra propia.

### 108. Retro con el plugin de barras de Omarchy tal cual; el de Breeze, aparte (2026-11-09)
* **Petición:** al pulsar una barra para mover una ventana en un workspace flotante de Retro, la barra desaparecía y salían las previsualizaciones de encaje de Breeze. El modo flotante de Retro debe ser exactamente el de Omarchy y no tener nada que ver con Breeze; si algún día se lleva algo de uno al otro, se hará a propósito.
* **Causa:** §3.106/§3.107 usaban en Retro el plugin de Breeze ampliado, con su snapping y el borrado de etiquetas al arrastrar. Además la sesión seguía con una versión anterior cargada.
* **Hecho:** Retro usa **omarchy-hyprland-titlebars sin cambios** (`src/omarchy-titlebars`, `379ff91`, el último que compila con Hyprland 0.56; BWM sólo añade un `Makefile` con instalación atómica → `config/hypr/plugins/omarchy-titlebars.so`). `workspace-modes.lua` lo configura con las mismas opciones y botones que el `titlebars()` de Omarchy; sólo cambian la carga (`hyprctl plugin load` la primera vez que algo flota, esperando a que Hyprland responda, sin descargarlo nunca) y la ruta del shim de minimizar. El plugin de Breeze vuelve a su estado anterior a §3.106 (fuera `workspace_tag`, `%WINDOW%`, título de la app, resaltado, redondeo, grosor, borde superior y `snap`) con dos correcciones que se conservan: no roba el arrastre de las pestañas de las apps con barra propia y sólo quita las etiquetas `snapped*`. Se registra como **`breezebars`** (opciones `plugin:breezebars:*`, `hl.plugin.breezebars`, reglas `breezebars:*`; `hyprctl hyprbars-csd` sigue igual), así que puede convivir con el de Omarchy, que conserva su nombre `hyprbars` como en Omarchy. Cambiados `appearance.lua`, `rules.lua`, `autostart.sh`, `quick-tile.py`, `bwm-theme-manager.py`, requisitos (`omarchy-titlebars` recomendado de Retro; `install.sh` lo compila en el paso 6b), regla 4 de AGENTS/CLAUDE y avisos de terceros. `bwm-requirements.py` reconoce el commit de Hyprland aunque el compilador lo guarde fundido con otra cadena (le bastan 16 caracteres).
* **Verificado:** los dos plugins compilan sin errores para Hyprland 0.56.2 (`bwm check`: los dos «compilado para Hyprland efb50993»); `--verify-config`, `configerrors` tras recargar y 109 pruebas OK.
* **No probado:** nada del comportamiento nuevo en pantalla: en la sesión sigue cargado el plugin anterior (no se recarga en caliente) y un Hyprland anidado no arranca aquí (§3.107). Tras volver a iniciar sesión: barras de Omarchy en el workspace 1 sin previsualizaciones de encaje y sin perderlas al arrastrar; Breeze con `breezebars` (barras, botones y snapping).

### 109. Fuente del menú y la barra de Retro: alternativa del perfil sin cambiar Fontconfig global (2026-11-09)
* **Petición:** investigar y corregir la forma extraña de la «l» en el menú y la barra de Retro sin romper el resto del escritorio.
* **Causa comprobada:** ambos usan `Commons.Style` y pedían `monospace`; `fc-match` y `QtQuick.FontInfo` resolvían Liberation Mono. El perfil de Retro tenía JetBrains Mono instalada, pero Omarchy presupone su regla de sistema `default/fontconfig/conf.avail/50-omarchy.conf` (`monospace` → JetBrainsMono Nerd Font), que BWM no instala.
* **Cambio:** `Commons/Style.qml` consulta `fc-match` con `monospace,<fuente monospace del perfil>` (nombre escapado para Fontconfig) y entrega a los componentes la familia concreta. La fuente del perfil queda antes de las alternativas genéricas de la distribución, pero una preferencia explícita de Fontconfig sigue ganando. `OMARCHY_MENU_FONT` se conserva. Los cambios del perfil y de `fonts.conf` vuelven a resolver; un temporizador agrupa peticiones y espera si sigue corriendo la anterior. Sin escribir configuración del usuario ni instalar reglas globales. Adaptación documentada en `Commons/README.md` y avisos de terceros.
* **Verificado:** pruebas aisladas de Quickshell/Qt con Fontconfig temporal: JetBrains por defecto, preferencia explícita Liberation Mono respetada, `OMARCHY_MENU_FONT=Liberation Sans` respetada y cambio en vivo a una fuente ausente con alternativa válida. Sonda separada `qs -p`, sin ventanas ni acciones: con la configuración real, perfil `JetBrains Mono NF`, fuente solicitada y efectiva de Qt `JetBrainsMono Nerd Font`, también en el menú. El shell real recargó en caliente con «Configuration Loaded», sigue con sus objetivos IPC, sin errores nuevos de fuente/carga; `hyprctl configerrors` vacío. 3 pruebas de fuentes de perfil y 7 de manifiestos OK. Sondas temporales eliminadas.
* **Límite:** no se ha hecho una comprobación visual del menú ni de la «l» en la barra real; sí se ha verificado la familia efectiva de Qt. No se ha cambiado de skin para probar visualmente default/Breeze.

### 110. Jade Horse y fondos de vídeo en todas las skins (2026-11-09)
* **Petición:** temas que cambian las decoraciones (Omarchy 98/Windows XP), los temas de Omarchy que faltan (Jade Horse) y los fondos de vídeo de Omarchy 4.5, también en las demás skins y en Alt+W.
* **Omarchy 98 / Windows XP:** sus repositorios (omacom/omarchy-98-theme…) piden credenciales y no están en el catálogo de la comunidad: pendiente.
* **Jade Horse:** copiado de `quattro` `60bf28ee` (upstream sustituyó Osaka Jade, #16594); Osaka Jade se conserva. Entrada en el menú de Retro. No se aplicó (tema activo: Gruvbox).
* **Vídeos:** nuevo `scripts/bwm-video-wallpaper` (`is-video|poster|still|play|stop|sync|thumbnails`). Retro: OWE (omacom/owe `56e7659`, MIT) compilado por `skins/retro/scripts/install-owe.sh` en `~/.local/share/bwm/owe` (también `install.sh` 10c), `owed` lanzado con `bwm_session.spawn` sólo en Retro y apagado fuera; sin unidad systemd. default/Breeze: mpvpaper con las opciones de end-4 (no instalado: `sudo emerge --ask gui-apps/mpvpaper`, GURU). swww, paletas, plantillas, bloqueo y carrusel usan el primer fotograma (`~/.cache/bwm/video-posters`); `background.thumbnailPath` lo lleva. `set-wallpaper.sh`, `switchwall.sh` (sin escribir el script de restauración en el repo), `autostart.sh` (`sync` al entrar), `window-guard.py`, `bwm_omarchy.py`, `omarchy-theme-switcher`, `OmarchyLockSurface.qml`. Selectores: rofi de Retro/Breeze y el de end-4 (`Wallpapers.qml`, miniaturas freedesktop con ffmpeg, hash igual al de `ThumbnailImage.qml`). Requisitos `owe`, `mpvpaper`, `ffmpeg`.
* **Verificado:** en Retro, `set-wallpaper.sh` con el intro de Osaka Jade: `owed` en `session-*.scope`, capas `owe-background`, fotogramas distintos en dos capturas (borradas); vuelta a Gruvbox: «engine: shell», la imagen se ve. Miniaturas y QML del selector (`qs -p` aparte) con un vídeo; 109 pruebas OK. Durante la prueba el MSI pasó del workspace 1 al 4 (Signal/Steam); repetir `set-wallpaper.sh` escuchando socket2 no produjo ningún cambio de workspace.
* **No probado:** mpvpaper (no instalado), default/Breeze con vídeo, el inicio de sesión con un vídeo, introducciones de tema de Omarchy (no portadas) y monitores conectados después (mpvpaper no se relanza).

### 111. Selector original de fondos de Omarchy en Retro, con la colección compartida de BWM (2026-11-09)
* **Petición:** copiar por completo el selector de fondos de Omarchy, conservar Alt+W y sus fondos por tema, añadiendo los de `~/Pictures/Wallpapers` que usan las demás skins.
* **Hecho:** se reutiliza el `ImagePicker.qml` original ya vendorizado (mismo carrusel, aspecto, navegación con ratón/teclado y conservación de miniaturas; no se modifica su interfaz). `OmarchyPlugins.qml` añade el protocolo `omarchy.image-selector` de `shell/shell.qml` de Omarchy `cbd0029f` (`open/preload/cancel/ping`) y `inspect` de diagnóstico. Se retira la inyección de `shell`/`manifest` del Loader del selector: el componente original no tiene esas propiedades. Nuevo shim `omarchy-menu-images`, port de ese mismo commit: miniaturas JPEG 1536×864, imágenes/vídeos, caché por firma, publicación atómica y selección por archivos temporales. BWM usa ImageMagick y FFmpeg, ya declarados, en lugar de añadir libvips/ffmpegthumbnailer; conserva las funciones originales y evita abrir una capa vacía si no hay archivos válidos.
* **Colección:** `skins/retro/scripts/wallpaper-picker.py` resuelve el tema estático con el catálogo existente (también los instalados en `~/.local/share/bwm/omarchy-themes`), sus `backgrounds`, los extras personales `~/.config/omarchy/backgrounds/<tema>` y la carpeta compartida. En modo dinámico ofrece extras de `dynamic` y la carpeta compartida. Deduplica directorios equivalentes por enlace. Como Omarchy, lee un nivel por carpeta. Preselecciona el medio original, incluidos vídeos con póster. Shims `omarchy-theme-bg-switcher` (devuelve ruta, como upstream) y `omarchy-theme-bg-set` (delegación al aplicador común de BWM).
* **Integración:** sólo la rama Retro de `wallpaper-picker.sh` delega en el backend nuevo; Alt+W y el menú mantienen su entrada existente. Al confirmar pasa por `set-wallpaper.sh`, conservando perfiles, paleta estática/dinámica y motor de vídeo. Si se cambió de skin mientras estaba abierto, no aplica a la nueva skin. Enlaces de los shims creados con `bwm-plugin.sh catalog`. Procedencia y modificaciones en `image-picker/README.md` y `THIRD_PARTY_NOTICES.md`.
* **Verificado:** 10 pruebas nuevas (colecciones estática/dinámica/comunidad, tema eliminado, selección/cancelación, vacío, UTF-8, invalidación al sobrescribir imagen, miniatura de vídeo, aplicador común y guardia al cambiar de skin). `qs -p` separado, con acciones de cambio/eliminación sustituidas y revisión de que no quedaban llamadas reales: carrusel renderizado y revisado, flecha derecha e Intro reales de QtTest, selección con acento y señal de finalización correctas; archivos de prueba retirados. Protocolo real UTF-8 y entrada real de `wallpaper-picker.sh`: 22 fondos válidos (6 Gruvbox + 16 compartidos), preselección y cancelación OK; fondo actual intacto. La imagen compartida `plasma-breeze.png` tiene cabecera PNG inválida y se omite, sin modificarla. Recarga real de Quickshell correcta, una sola instancia, sin errores de carga del selector; `hyprctl configerrors` vacío. Bash y Python válidos.
* **Límite:** no se cambió deliberadamente el fondo real desde el nuevo selector durante la prueba; la confirmación se verificó con archivos aislados y la delegación al aplicador común con pruebas. No se cambió de skin para probar visualmente los otros selectores.

### 112. Omacalc instalada, con colores en vivo de Retro, default y Breeze (2026-11-09)
* **Petición:** instalar Omacalc, declararla como dependencia y hacer que siga todos los temas, incluidos los fondos dinámicos de Retro y default, como en Omarchy.
* **Instalación comprobada:** original [omacom/omacalc](https://github.com/omacom/omacalc), commit `573d7106f5c6c0225864eb8634ae37ddcb657f63` (MIT; iA Writer Mono S incluida, OFL). Nuevo `scripts/install-omacalc.sh`: Qt 6/qmake, compilación sin sudo desde revisión fija y exportación limpia, instalación atómica en `~/.local/share/bwm/omacalc/bin/omacalc`, caché de fuentes Git, parche y licencias junto al binario; lanzador `~/.local/bin/omacalc` → `scripts/bwm-omacalc`, `.desktop` e icono originales. Rechaza sobrescribir un lanzador ajeno. Semilla inicial desde los colores del shell actual, sin reaplicar fondo. `install.sh` lo ejecuta antes del paso 8. `omacalc` y las herramientas de compilación están en `requirements.json` y como recomendados de las tres skins; tabla regenerada. `bwm check` los da OK.
* **Colores:** la aplicación original sólo leía la paleta de Omarchy. Parche mínimo `hypr/omacalc/theme-path.patch`: acepta `OMACALC_THEME_FILE` (si no se pasa, mantiene el comportamiento original) y vigila archivo/directorio, incluyendo la creación inicial y los reemplazos atómicos. El lanzador usa `~/.local/state/bwm/omacalc/colors.toml`, salvo preferencia explícita del usuario. Nueva plantilla compartida `matugen/templates/omacalc-colors.toml`, formato **nativo de Omarchy** (`background/foreground/accent/selection`): los aplicadores existentes de Retro y Breeze y Matugen de default la rellenan automáticamente; sin hooks de reinicio ni cambios en los formatos de los temas. Retro conserva exactamente esos cuatro colores del tema estático o dinámico. Sin campo `mode`, Omacalc infiere claro/oscuro por el fondo, como permite upstream.
* **Acceso:** Apps en todas las skins y Acciones → Calculadora en Retro. Regla común de ventana: flotante y centrada, sin fijar tamaño para conservar la escala de texto original. Sin atajo nuevo. Conservados interfaz, icono, fuente y motor de cálculo originales. Procedencia/licencias y reproducción en `hypr/omacalc/README.md`, `THIRD_PARTY_NOTICES.md` y `licenses/omacalc-*`.
* **Verificado:** 24 pruebas originales de Omacalc OK; 6 comprobaciones QtTest del adaptador (incluyen inicialización/finalización), con cambio claro/oscuro, escritura en sitio, varias sustituciones atómicas, paleta creada después de arrancar y cálculo `2 + 3 = 5` conservado. 4 pruebas de integración: temas Gruvbox/Tokyo Night/Catppuccin Latte exactos, Breeze, fondos sintéticos rojo/azul de Retro dinámico y Matugen real en default oscuro/claro con archivos aislados. 7 pruebas de manifiestos y 4 del motor de paletas default OK. Binario instalado carga QML sin errores (también sin pantalla); abierto en el workspace 9 silencioso: clase `omacalc`, flotante 400×568, después cerrado por su PID. `.desktop` válido, reinstalación idempotente desde la ruta enlazada, verificación/recarga de Hyprland sin errores; regla temporal retirada. Paleta inicial real igual al tema Retro activo (Everforest); no se cambió el tema del usuario para probar. No hay procesos de prueba abiertos.
* **Límite:** se verificaron los cambios de color con el backend real y los renderizadores en pruebas aisladas; no se recorrieron visualmente temas reales ni se cambió de skin en el escritorio del usuario durante esta prueba.

### 113. Minimizado de Retro igual que el de Omarchy (2026-11-09)
> ⚠️ **Superado en parte por §3.114:** ya no hay paso al workspace 99 al salir de Retro; todas las skins usan `special:minimized`.
* **Petición:** que el minimizado de Retro sea igual al de Omarchy (en el dock no se distinguía la ventana minimizada; Omarchy tampoco la marca).
* **Cómo es en Omarchy** (`quattro` `b99593e`): `omarchy-hyprland-window-minimize` sólo en workspaces flotantes; mueve la ventana a `special:minimized` con la etiqueta `omarchy-minimized-from-<n>` y enfoca ese workspace. El dock la devuelve sin animación al workspace que tienes delante (`bringForward`); con varias ventanas, primero las del workspace actual, después las minimizadas.
* **Hecho:** shim `omarchy-hyprland-window-minimize` = el de Omarchy sin cambios salvo una guarda de BWM (sólo con el dock encendido: es opcional y sin él la ventana no tendría vuelta). `omarchyDock/Dock.qml` recupera el `bringForward` de Omarchy en vez de `toggle-minimize.py restore`. `DockModel.js` sigue reconociendo además el workspace 99 (ventanas minimizadas en otras skins). `omarchy-hyprland-workspace-layout-default` cuenta las minimizadas de los dos sistemas. Al salir de Retro, `bwm_windows.omarchy_minimized_to_bwm()` (desde `bwm-theme-manager.py`) pasa las de `special:minimized` al 99 con `from_ws_<n>`, para que el dock de end-4 y la barra de Breeze las devuelvan. default y Breeze siguen con `toggle-minimize.py`.
* **Verificado (Retro, workspace 9 flotante de prueba):** el shim manda una kitty a `special:minimized` con `omarchy-minimized-from-9`; los pasos de `bringForward` la devuelven flotante; la conversión la deja en el 99 con `from_ws_9` y `toggle-minimize.py restore` la devuelve al 9. Ventana, modo y regla retirados; `configerrors` vacío; 123 pruebas OK; reinicio de mantenimiento del shell sin errores del dock. Ojo de la prueba: minimizar una ventana de un workspace no visible enfoca ese workspace (lo hace también Omarchy); se volvió al 1.
* **No probado:** pulsar el dock ni el botón − de la barra con el ratón, ni un cambio de skin real con ventanas minimizadas.

### 114. Minimizado común en `special:minimized` (2026-11-09)
* **Petición:** de la comparación entre los dos sistemas, quedarse con el sitio de Omarchy (workspace especial) en default y Breeze, conservando lo de BWM: geometría, vuelta al workspace de origen, funcionar sin dock y en mosaico.
* **Hecho:** `toggle-minimize.py` mueve a `special:minimized` con la etiqueta `omarchy-minimized-from-<n>` (la de Omarchy, quitando antes otra vieja), y como Omarchy devuelve el foco al workspace de origen sólo si es el que está delante (si no, la ventana siguiente se abriría en el workspace oculto; minimizar desde el dock o una lista no cambia de workspace). Restaurar lee esa etiqueta o la antigua `from_ws_<n>`, quita sólo las de minimizar (las `snapped*` de quick-tile se conservan) y repone la geometría guardada. Retro y las demás skins comparten ventanas minimizadas sin conversión: fuera `bwm_windows.omarchy_minimized_to_bwm()` y su llamada en el gestor. Comprobaciones del 99 cambiadas por el nombre del workspace en Alt+Tab (antes también excluía las minimizadas en id negativo), el selector de Breeze, el menú de tareas de Breeze y el dock de end-4; quitadas las del vigilante de ventanas, `float_in_place`, el gestor, la barra de workspaces de Retro y `workspace-modes.lua`. Siguen reconociendo el 99 (ventanas de versiones anteriores) `toggle-minimize.py`, el dock de Omarchy, `cycle-workspace.py` y `omarchy-hyprland-workspace-layout-default`. La razón antigua del 99 (docstring: que el workspace especial colgara retransmisiones de Electron/WebRTC) no se pudo comprobar; Omarchy lo usa así.
* **Verificado (sesión real, Retro):** una kitty de prueba en el workspace 9 en mosaico: `min` → `special:minimized` con `omarchy-minimized-from-9`, ningún workspace especial a la vista; `restore` → de vuelta en el 9, en mosaico, sin la etiqueta. Flotante a 700×500 en 300,900: misma posición y tamaño al volver. Restaurar enfoca la ventana y muestra su workspace (como antes); se volvió al 1 con Firefox enfocado. Ventana y regla temporal retiradas, `configerrors` vacío, log del shell sin errores nuevos. 3 pruebas nuevas en `tests/test_minimize.py` y la de `float_in_place` actualizada: 126 OK.
* **No probado:** «Mostrar escritorio» de Breeze, Alt+Tab y el dock de end-4 con ventanas minimizadas, una retransmisión de Vesktop minimizada y el cambio de skin con minimizadas.

### 115. Breeze coloca las ventanas nuevas donde no tapan a las demás (2026-11-09)
* **Petición:** lo equivalente en Breeze a la cascada de los workspaces flotantes de Omarchy (§3.106): que las ventanas nuevas no se abran unas encima de otras.
* **Cómo es en el original:** KWin usa por defecto la colocación «Mínimo solapamiento» (Smart): la ventana nueva va a la posición libre más arriba y a la izquierda, o a la que menos tapa si no hay hueco; los diálogos van sobre su ventana. No redimensiona. (La cascada de 48 px es de Omarchy y se queda en Retro.)
* **Hecho:** `skins/plasma/hypr/placement.lua`, cargado por `appearance.lua` sólo en Breeze (junto a `lock`/`misc`/`workspace-modes`) y declarado en `parts` de `skin.json`. En `window.open`: si el centro (lo que haría Hyprland) está libre, se queda ahí; si no, prueba como KWin los bordes del área útil y los de cada ventana del workspace (a su lado con el hueco de 10 px) y elige la de menor solapamiento, la más alta y luego la más a la izquierda. Cuenta la barra Breeze (30 px), el margen de 10 px y las reservas reales del monitor; respeta el tamaño de la app. No toca: la primera ventana del workspace, flotantes que no caben, pantalla completa, fijadas, workspaces especiales, otra ventana de la misma app (diálogos y secundarias: Hyprland ya las pone sobre la suya), diálogos de abrir/guardar y las clases con sitio propio en `rules.lua` (terminal flotante y About de Omarchy, Omacalc, hyprland-run).
* **Verificado:** 5 pruebas en `tests/test_plasma_placement.py` (ejecutan el Lua con `lua` y un `hl` falso: sola, centro libre, al lado de otra, diálogo de la misma app, diálogo de archivo); 131 OK. En la sesión real (Retro) se cargó el archivo un momento y se colocaron cuatro kitty flotantes de 900×600 en el workspace 9 del MSI: la primera en el centro, las otras abajo a la izquierda, abajo a la derecha y arriba a la izquierda, solapándose lo mínimo. Ventanas cerradas y `hyprctl reload` para quitar el manejador; `configerrors` vacío. `Hyprland --verify-config` con una copia en modo Breeze: ok. La ventana con foco pasó de Firefox a Vesktop durante la prueba; no se supo si fue el usuario.
* **No probado:** en una sesión real de Breeze (no se cambió de skin): apps con barra propia (la barra Breeze se cuenta siempre, así que quedan 30 px más separadas), apps que cambian de tamaño después de abrirse y el cambio de skin a Breeze con ventanas abiertas (lo coloca `float_in_place`, no esto).

### 116. Punto 4.4 del estudio de Omarchy 4.5: intros de fondo, avisos, animaciones y menú (2026-11-09)
* **Petición:** seguir con el punto 4 de `docs/OMARCHY_4_5.md` (§4.4, novedades sin portar). Antes se discutió el 4.3 (workspaces por monitor) y se descartó: queda anotado en el estudio.
* **Intros de fondo (#16875…):** las 19 intros de upstream ya venían en los temas copiados. `bwm-video-wallpaper` gana `intro-for` (clip de `intros/<nombre>.<ext>` junto a un fondo fijo, sólo en Retro con OWE, intros activadas y animaciones encendidas, como `omarchy-theme-bg-boot-intro`), `intro` y `boot-intro`. `intro` arranca owed, pide `owe intro --start first-frame --refresh` y, cuando OWE ya pinta la intro (motor `renderer`), pasa el shell al fondo nuevo por debajo sin transición; OWE termina fundiéndose en él y owed se para si el fondo no es un vídeo. `set-wallpaper.sh` la usa en Retro en lugar de la transición (en un proceso aparte, mientras cambian los colores; también al cambiar de tema), salvo en un cambio de skin. `autostart.sh` lanza `boot-intro`: una vez por sesión (marcador de Omarchy), **después de desbloquear**, porque OWE no reproduce intros con la sesión bloqueada y BWM bloquea al entrar. Interruptor `omarchy-theme-bg-intro` de Omarchy sin cambios (mismo archivo de estado) y entrada en el menú → Estilo.
* **Avisos:** `omarchy-capture-screenrecording` como upstream: no avisa al parar una grabación que no empezó él y el botón Cortar lleva su texto traducido (`capture.recordingCut`, en/es-MX); en BWM sólo aparece si está `omacut`. `omarchy-battery-low` como tarjeta normal (#16562); en BWM el aviso de batería lo da el servicio común `services/Battery.qml` en todas las skins. yt-dlp (#16843) es una extensión de Chromium: no aplica.
* **Animaciones (#16889):** las curvas, animaciones y reglas de capa de `skins/retro/hypr/animations.lua` coinciden con `quattro` `18ac93c`; sólo faltan las reglas de su modo vidrio, que BWM tiene propio. Sin cambios.
* **Menú:** comparado con `omarchy-menu.jsonc` de `18ac93c`. Añadidos: Sistema → Hibernar (con el shim `omarchy-hibernation-available`, que en vez del archivo de mkinitcpio de Omarchy exige `resume=` en la línea del kernel: aquí no hay, así que no sale), Estilo → Dock (ocultar automáticamente y posición, con el `omarchy-dock` de BWM; sólo con el dock encendido y en un workspace flotante), Estilo → Intros de fondo y Aprender → Neovim (atajos de LazyVim). Pendientes en el estudio: Barra (ocultar, posición, fondo, formatos del reloj), Animaciones sí/no, Branding, Setup de teclado/entrada/idioma/seguridad, Transcodificar, Compartir y Hardware.
* **Panel de pantallas:** el editor de BWM (§3.67) ya tiene mapa, giro, frecuencias, escala, principal y apagar; falta Duplicar (espejo), anotado como pendiente.
* **Verificado (sesión real, Retro):** con el workspace 9 vacío a la vista, `bwm-video-wallpaper intro` con la intro de Matte Black: captura a los 3 s con la intro, al acabar el fondo de siempre, owed parado y sólo las capas `omarchy-background`; 9 s en total. `set-wallpaper.sh` con el fondo actual (sin intro): sin cambios de comportamiento. `intro-for` encuentra el clip; el comprobador de hibernación sale «no» aquí y «sí» con un `resume=` de prueba. Menú abierto por IPC: «Intros de fondo ✓» en Estilo; Dock e Hibernar ocultos, como corresponde. JSON del menú y traducciones válidos, `bash -n` de los scripts, 131 pruebas OK, `configerrors` vacío. Capturas borradas. Tras `set-wallpaper.sh` el MSI estaba en el workspace 2 (antes en el 1); no se movió y no se sabe si fue el usuario.
* **No probado:** una intro al elegir un fondo desde el selector o al cambiar de tema (no se cambió el fondo ni el tema del usuario), la de inicio de sesión tras desbloquear, el aviso de una grabación real y Hibernar.

### 117. Nautilus se abría solo al cambiar de fondo o de tema (2026-11-09)
* **Petición:** cada cambio de fondo o de tema abría una ventana de Nautilus.
* **Causa:** `sync-nautilus.sh` (hook de matugen y final de `set-wallpaper.sh`) cierra Nautilus para que GTK 4 relea `gtk.css` y lo vuelve a abrir. Decía «si tiene una ventana abierta», pero sólo miraba si había proceso: Nautilus suele seguir en segundo plano sin ventanas (`--gapplication-service`, activado por D-Bus o el portal de archivos), así que lo «reabría» con una ventana nueva.
* **Hecho:** se sigue cerrando para que tome la paleta, y sólo se reabre si `hyprctl clients` tenía una ventana `org.gnome.Nautilus`.
* **Verificado:** Nautilus como servicio sin ventana → tras el script, cerrado y sin ventanas; con una ventana (regla temporal al workspace 9) → cerrado y reabierto con una ventana. Acento de GNOME sin cambios; regla retirada y Nautilus cerrado. **No probado:** un cambio de fondo completo con el selector.

### 118. La barra de Retro es la de Omarchy, idéntica (2026-11-09)
* **Petición:** en Omarchy se mantienen pulsados los widgets de la barra para moverlos; BWM no podía. Que la barra de Retro sea idéntica a la de Omarchy.
* **Encontrado:** la barra de Retro no era la de Omarchy: `RetroBarContent.qml` (317 líneas) era una reconstrucción hecha en octubre (§3.32) con Omarchy 4.0, widgets en posiciones fijas y un formato propio (`~/.config/bwm/omarchy-plugins.json`), contra la regla 11. La de Omarchy (`shell/plugins/bar/Bar.qml`, 3231 líneas) depende de su anfitrión de plugins (`shell/shell.qml` y `services/`): registro de plugins por manifiestos, `shell.json`, API por plugin, paneles y servicios.
* **Hecho:** `config/quickshell/ii/omarchyShell/` = `shell/` de Omarchy quattro `18ac93c`: `OmarchyShell.qml` (su `shell.qml`), `services/` (registro y API de plugins), `plugins/bar` (barra, widgets, indicadores), `plugins/panels/*`, `plugins/agents`, `plugins/services/{media,remote-session}` y `plugins/menu` (sólo el botón). `IllogicalImpulseFamily.qml` lo carga en Retro en lugar de la barra de BWM. Cambios marcados «BWM»: raíz `Scope`; fuera la biblioteca de apps, teclas de brillo, intros/cambio de fondo, atajos globales, socket e IPC del selector de imágenes (BWM los tiene aparte); `bwmHosted()` manda el menú y las capas de BWM a `OmarchyPlugins.summonLocal/hideLocal/toggleLocal`; `bwmServices` da los servicios `omarchy.idle` (inhibidor de BWM), `omarchy.nightlight` (`nightlight.json`) y `omarchy.notifications` (no molestar de BWM); el registro lee también `quickshell/ii/omarchy-plugins` (los preinstalados) y los plugins desde la carpeta del shell (`Quickshell.shellDir`, para que resuelvan `qs.*`); el widget de workspaces usa la numeración global y `hl.dsp.focus`. `OmarchyPlugins` conserva el único destino IPC `shell` y, con el anfitrión, le pasa sus funciones (`putBarWidget`, `enablePlugin`, `listPlugins`…), sus `summon/hide/toggle` y los servicios; su copia vieja del servicio de multimedia y de los paneles de velocidad/QR se quitó. `$OMARCHY_PATH/shell` es ahora un enlace a `omarchyShell/` y `$OMARCHY_PATH/config/omarchy/shell.json` el `shell.json` por defecto de Omarchy. Comandos de Omarchy copiados sin cambios: `omarchy-bar`, `omarchy-shell-config`, `omarchy-plugin-*`, `omarchy-restart-hyprctl`, `omarchy-git-url-check`, los de monitores (`layout`, `resolution`, `rotate`, `scaling`, `laptop`, `omarchy-monitor-state`) y `omarchy-hyprland-toggle-enabled`; de BWM con su interfaz: `omarchy-hyprland-monitor-persist` (guarda con `monitor-manager.py`; la ida y vuelta con tus monitores sólo cambia `60` por `60.0`) y `omarchy-sudo-passwordless` (nunca activo: BWM no toca sudo). Fondo vidrio: `Commons/omarchy/default/hypr/toggles/bar-glassy.lua` (sin el modo vidrio de Omarchy) leído por `skins/retro/hypr/misc.lua`. Fuente de iconos `assets/fonts/omarchy.ttf` (logo del menú y agentes). `bwm-plugin.sh` reescrito sobre `omarchy-plugin-*` y `shell.json` (sin barra en marcha, edita `shell.json`), con el mismo `catalog` para Ajustes y el menú. `bwm_omarchy.ensure_omarchy_shell_json()` crea una vez `~/.config/omarchy/shell.json` desde el de Omarchy y lo elegido en la barra vieja (fuera Elsewhen, el tiempo y energía; mpris tras el reloj con sus ajustes; fondo opaco); nunca toca uno existente. Borrados: `RetroBarContent.qml`, `OmarchyPluginSlot.qml`, `OmarchyIndicators.qml`, los paneles viejos de `bar/omarchy/` y los preinstalados `omarchy-weather`/`omarchy-elsewhen` (ahora de Omarchy). Requisitos recomendados de Retro: `font-omarchy`, `inotify-tools`.
* **Verificado (sesión real, Retro):** primero en una instancia `qs -p` aparte unos segundos (salió una segunda barra bajo la tuya); después en el shell real, en los dos monitores, con tu disposición; dos reinicios de mantenimiento sin errores de carga y con los mismos workspaces y ventana con foco. `omarchy-plugin list` enumera los 29 plugins; `bwm-plugin.sh enable/disable omarchy.power` y `catalog` funcionan; `omarchy-bar background glassy` crea el interruptor y recarga Hyprland, `omarchy-bar position bottom` lleva la barra abajo (captura) y todo volvió a como estaba (mismo `shell.json`). Logo de Omarchy y workspaces 1-5 (+ los del monitor) en capturas recortadas y borradas. 131 pruebas OK, `Hyprland --verify-config` correcto.
* **Incidentes:** la instancia de prueba creó `~/.config/omarchy/shell.json` con los valores de Omarchy (el widget de Elsewhen guardó sus ciudades); se sustituyó por el de la migración. Al limpiar `OmarchyPlugins.qml` una sustitución automática lo dejó con un error de sintaxis unos segundos: el shell siguió con la configuración anterior hasta corregirlo.
* **No probado:** arrastrar widgets o la barra con el ratón, el doble clic, cambiar algo desde el panel de pantallas de Omarchy, añadir un plugin de terceros, los interruptores de Ajustes → Barra/Plugins y del menú con la interfaz, y las otras skins tras el cambio (allí sigue la barra de BWM; `OmarchyShell` no se carga). `inotify-tools` no está instalado (sin él no se recarga sola un plugin en desarrollo).

### 119. BWMenu: diagnóstico y recuperación sin Quickshell (2026-11-10)
* **Interfaz ampliada en §3.122:** galería gráfica autónoma con temas en vivo; esta consola se conserva como rescate.
* **Petición:** un menú BWMenu para usar si crashea el escritorio, con versión de BWM, versiones y compatibilidad de dependencias, skins instaladas, cómo aplicarlas y recuperación. El usuario aclaró que el atajo es pulsar `+` y `-` a la vez, sin Super ni Alt.
* **Hecho:** `scripts/bwm-menu.py` es una interfaz de terminal con Python estándar (sin Qt/QML/curses): flechas, Intro, Esc, R para actualizar y Q para salir. `bwm menu --open` usa Kitty con `--config NONE`, ventana `org.bwm.menu` flotante/centrada, y reutiliza la existente; candado de instancia única. `bwm menu`/`bwmenu` usan la terminal actual; `--tui` funciona también sin sesión gráfica, `--report` y `--json` permiten diagnóstico sin interfaz. No arranca un shell gráfico desde TTY. Revisión local por Git (incluye `dirty`; copia sin metadatos explícitamente sin dato), Hyprland instalado/en ejecución, bibliotecas, instancia `ii` y errores. `bwm_versions.py` consulta paquetes instalados y las sondas `versionProbes` declaradas en el catálogo (swww/awww, matugen, cliphist y playerctl); no consulta Internet. `bwm-requirements.py --versions` añade versiones, mínimos y referencia probada; la comprobación de Hyprland usa el de la sesión cuando existe, evitando aceptar un binario actualizado con un compositor viejo aún en ejecución. Si no hay mínimo o versión consultable se dice, sin inventar compatibilidad.
* **Acciones:** requisitos obligatorios/opcionales y comandos para resolver fallos; skins instaladas y aplicación por `bwm skin ID` (revalida requisitos); reinicio de mantenimiento por `bwm-theme-manager.py set <actual> --restart-shell`, recarga de Hyprland, errores y últimas 100 líneas del registro de Quickshell. Sin instalación automática ni descarga/carga de plugins. Helpers de `keybinds-manager.py`: ocho combos (ambos órdenes, normal, numérico y mezclados), regenerados con `reload`; no se interceptan signos por separado. `install.sh` instala el alias `bwmenu` (enlazado también en este equipo). README en ambos idiomas, `docs/BWMENU.md`, AGENTS/CLAUDE sincronizados. Tabla de requisitos regenerada, sin cambios (no hay dependencias nuevas).
* **Verificado:** ventana real de BWMenu, navegación a las dependencias y a la ficha de una skin, versiones/mínimos visibles; capturas sólo de su ventana, borradas. Inyección de teclas con dispositivo temporal uinput mientras BWMenu tenía foco: normal y numérico, en ambos órdenes; callbacks temporales comprobaron cada combo, una sola ventana después de repetir; dispositivo/reglas/archivos de prueba retirados con recarga. `Hyprland --verify-config` correcto y `configerrors` vacío. 146 pruebas (12 nuevas de BWMenu), OK con 29 omitidas; Python compila y `bash -n` correcto. Las nuevas pruebas cubren ausencia de compositor/shell y catálogo corrupto, slots de paquetes, mínimos, sondas, compositor viejo con binario nuevo y rutas de recuperación sin ejecutar sus efectos. Skin activa sigue siendo Retro.
* **No probado:** un crash real, el cambio de skin o el reinicio de barra desde este menú (rutas comprobadas con mocks, sin provocar interrupciones), ni una TTY física; la interfaz se ejecutó también en una pseudoterminal. Consultas de versiones de paquetes sólo probadas en Gentoo; las otras distribuciones quedan pendientes. Una instancia `ii` detectada no certifica que todos sus paneles funcionen: para eso están el registro y el diagnóstico de errores.

---

### 120. Dos recomendaciones ausentes en BWMenu: Darkly y editor de red (2026-11-10)
* **Petición:** instalar los dos paquetes que BWMenu marcaba como ausentes y corregirlo.
* **Comprobado:** los dos faltan realmente: `darkly` (opcional de default) y `nm-connection-editor` (opcional de Breeze). Núcleo y requisitos obligatorios de las tres skins completos. En Gentoo el editor viene en `gnome-extra/nm-applet`; simulación de Portage correcta, instala `libnma-1.10.6-r2` y `nm-applet-1.36.0`, sin cambios de USE ni conflictos en la simulación.
* **Preparado:** Darkly oficial `v0.5.43`, commit `3f69ff222e3ad7dcb901a41be691020f70112ea6`, en `~/.cache/bwm/build/Darkly-v0.5.43`. Compilado Qt6 (sin Qt5 ni decoraciones de KWin), `build-bwm/`, prefijo `/usr/local` y plugins en `/usr/lib64/qt6/plugins`. Instalación de prueba bajo `stage/` con DESTDIR; prueba Qt Widgets offscreen crea `Darkly::Style` correctamente, sin dependencias dinámicas ausentes. Código y licencia originales conservados. No se ha instalado aún en el sistema.
* **Corregido:** `bwm_versions.py` y el catálogo permiten leer la versión de una instalación manual desde el `DarklyConfigVersion.cmake` original; no se toma una mera compilación como instalación. Prueba específica con metadatos presentes y plugin ausente: sigue sin versión/ausente. 13 pruebas de BWMenu OK.
* **Paso con sudo:** se facilitaron al usuario `sudo emerge --ask --noreplace gnome-extra/nm-applet`, `sudo cmake --install /home/sasel/.cache/bwm/build/Darkly-v0.5.43/build-bwm` y `sudo install -Dm644 /home/sasel/.cache/bwm/build/Darkly-v0.5.43/COPYING /usr/local/share/licenses/darkly/COPYING`. **Instalación verificada después en §3.121.**

### 121. Verificada la instalación de las dos recomendaciones (2026-11-10)
* **Petición:** comprobar si ya estaban instalados tras ejecutar los comandos.
* **Verificado:** BWMenu (`--json`) marca `darkly` **ok**, versión **0.5.43**, y `nm-connection-editor` **ok**, paquete **nm-applet 1.36.0**. También instalado `libnma 1.10.6-r2`. Todos los requisitos obligatorios y recomendados que enumera el diagnóstico están satisfechos; las tres skins listas.
* **Pruebas reales:** una aplicación Qt Widgets offscreen encuentra el plugin en su ubicación instalada, sin usar `QT_PLUGIN_PATH` de la compilación, y crea `Darkly::Style`; licencia en `/usr/local/share/licenses/darkly/COPYING`. El editor ejecuta su ayuda correctamente (no admite `--version`; se usa la versión de Portage). `ldd` de ambos sin bibliotecas ausentes; `hyprctl configerrors` vacío. No se cambió de skin ni se abrió el editor gráfico de red.

---

### 122. BWMenu visual con galería y temas sincronizados (2026-11-10)
* **Petición:** analizar las skins, hacer BWMenu mucho más visual y que cambie con sus temas.
* **Análisis y aplicación:** manifiestos `skin.json`, superficies de Material You/end-4, colores/superficies de Omarchy (`colors.toml`/`shell.toml`) y paleta KDE (`kdeglobals`). Galería con capturas ya incluidas (sin recursos gráficos nuevos), formas/fuentes de cada skin y tarjeta activa con su fondo guardado, tema y muestras de color. El marco, los botones y la tipografía siguen la skin activa: radios Material, geometría recta/monoespaciada de Retro y superficies Breeze. Conserva selección y navegación al cambiar de tema. Sin formatos propios de tema ni escrituras en configuración del usuario.
* **Piezas:** `config/quickshell/bwmenu/{shell,SkinCard,MenuButton}.qml`, una ventana `org.bwm.menu` en una instancia `qs -n -p` aparte, sin importar `ii` ni sus servicios. Navegación Skins/Estado/Dependencias/Recuperación/Ayuda, buscador de dependencias, aplicación mediante `bwm skin` (revalida requisitos), comandos de reparación y registro. `bwm_menu_appearance.py` normaliza las paletas originales, lee los manifiestos/perfiles y vigila cambios por sondeo de 250 ms, con margen de escritura y espera del candado de transición. Soporta colores claros/oscuros, aliases/gradientes de Omarchy y la precedencia de `~/.config/omarchy/shell.toml`. La misma paleta se aplica a la consola cuando admite color verdadero.
* **Rescate conservado:** `bwm menu`/`bwmenu` abre la galería en Wayland; `--tui` conserva la terminal/TTY y `--open --tui` abre Kitty limpio (`org.bwm.menu.console`). Supervisor Python con candado: un error de carga/salida anómala de la galería abre la consola; cerrar normalmente no la abre. Registro `$XDG_RUNTIME_DIR/bwm-menu.log`. Cerrar la galería durante una acción espera a que termine. `bwm_session.spawn()` lanza el supervisor como hijo de Hyprland; sin segunda instancia de `ii`. La regla común admite ambas clases. Sin dependencias nuevas. Guía, README y AGENTS/CLAUDE actualizados.
* **Verificado:** misma ventana de prueba con las tres skins y Retro White claro mediante fixtures fuera de la configuración real; IPC comprueba cambio de fondo/acento/fuente/radio, capturas recortadas de cada variante. Navegación por las cinco páginas; visor gráfico sin errores QML de carga/tipos, consola en pseudoterminal y pruebas de caída/cierre normal del lanzador. Prueba con sustitución real de un archivo de paleta en un entorno temporal: el mismo vigilante emite el color nuevo y no duplica emisiones sin cambios. 155 pruebas OK, 29 omitidas; compilación Python y `bash -n` correctos. Campos opcionales mal formados del perfil no rompen el aspecto del rescate; un fondo de vídeo usa la captura de referencia en la tarjeta.
* **Sesión real:** galería lanzada mediante `bwm menu`, Retro/Nord, su estado IPC coincide con la paleta y fuente originales, diagnóstico cargado y una única ventana tras volver a abrir. Una sola instancia de `ii` (PID 3276), sin reiniciarla; `configerrors` vacío. `Hyprland --verify-config`: `config ok` con aviso de inotify del proceso de verificación. Capturas/datos de prueba y regla temporal retirados; galería real abierta.
* **Límites:** no se cambió la skin ni el tema del escritorio del usuario para probar (las variantes se comprobaron en la ventana aislada); no se ejecutó una recuperación/cambio de skin desde los botones ni se provocó un crash real de Qt. Las rutas de esas acciones y del rescate se comprueban con mocks. Sigue apareciendo el aviso de registro del portal de Qt («Connection already associated with an application ID»), sin impedir cargar la ventana. La consola física no cambia su fuente con el tema.

---

### 123. BWMenu más limpio, semáforos y dependencias compactas (2026-11-10)
* **Petición:** reducir texto y ruido visual, mejorar la estética, luces junto a dependencias y skins (verde correcta, rojo antigua, naranja más nueva que la pedida por BWM), y listas más compactas con letras negras en cualquier skin.
* **Interfaz:** se quitan lemas, subtítulos repetidos, muestras globales de paleta, pie de sesión y descripciones extensas; tarjetas y ficha seleccionada más pequeñas. Se conserva la identidad de cada skin. `StatusLight.qml`: luz con halo verde/rojo/naranja y descripción al pasar el puntero; gris mientras no hay diagnóstico. `DependencyTable.qml`: filas de 34 px, columnas Dependencia/Instalada/BWM pide, blanco/negro fijo aunque la skin sea oscura, y detalles desplegables al pulsar una fila. Comandos de reparación ocultos salvo incidencias y despliegue explícito. Buscador y navegación por skin conservados.
* **Versiones:** `bwm_versions.py` añade `versionState` y `versionReason`, con comparación numérica y normalización de ceros finales. El fallo de una comprobación tiene prioridad; los plugins de Hyprland siguen exigiendo el commit exacto. Sin mínimo declarado se comprueba presencia, no se inventa una versión. `bwm-requirements.py --versions` agrega `versionHealth` por núcleo y por skin, incluidos opcionales y núcleo compartido, deduplicando requisitos. No se altera la elegibilidad para activar una skin. En este equipo las tres tarjetas salen naranja por Hyprland 0.56.2 > 0.55.0, Quickshell 0.3.2 > 0.2.0 y Python 3.14.7 > 3.11.
* **Verificado:** galería y tablas reales de default (13 filas) y Retro (18) en la misma ventana, capturas recortadas; luces visibles y texto negro en la lista sobre blanco bajo Retro/Nord. IPC muestra los tres resúmenes `newer`. 159 pruebas OK, 29 omitidas; cuatro pruebas nuevas cubren comparaciones numéricas, versiones iguales con ceros finales, errores prioritarios, plugins, ausencia de mínimo, herencia del núcleo/opcionales y deduplicación. Python compila; `configerrors` vacío. Capturas retiradas; ventana dejada en Skins. Sin cambio de skin, tema ni reinicio de la barra.
* **Incidencia corregida:** una recarga parcial al renombrar `SkinCard.ready` a `health` detectó el consumidor antiguo; al actualizarlo cargó correctamente. El log conserva ese error de recarga anterior, sin fallo actual.

---

### 124. Referencias de versiones actualizadas y separadas del mínimo (2026-11-10)
* **Petición:** aclarar si los semáforos se basaban en la última build/Git de las dependencias y actualizar las dependencias. El usuario precisó **actualizar las referencias de BWMenu**, no los programas instalados.
* **Hecho:** 54 `referenceVersion` en `skins/requirements.json`, tomadas de las versiones instaladas consultables del entorno local comprobado con BWM el 2026-11-10. `referenceEnvironment` documenta fecha, origen local y commit base `f0b1ce757189dab0c104abb4b53eda62ec0a51bd`; no se presenta como última release remota ni como el commit de una build publicada. No se inventan referencias para fuentes/recursos sin versión, grupos con varios paquetes ni hashes de plugins. Versiones numéricas de programa sin revisiones de empaquetado de la distro.
* **Comparación:** referencia del catálogo → `check.tested` → `check.min`. `check.min` sigue siendo el mínimo compatible y no se elevó a Python 3.14 ni a las versiones del equipo. Quickshell `check.tested` pasa a 0.3.2, que sí se ejercitó con BWMenu. Referencias principales: Hyprland 0.56.2, Quickshell 0.3.2, Qt 6.11.2, Python 3.14.7, Darkly 0.5.43. Los nombres de paquetes (como `qt6ct`) no se interpretan como números de versión. Se mantiene el requisito de commit exacto para los plugins.
* **Interfaz y documentación:** columna «Referencia BWM», mínimos compatibles en el detalle y fecha del registro en Estado. `docs/REQUIREMENTS.md` regenerado con tabla de referencias y mínimos. Las tres skins quedan verdes en el diagnóstico actual. Referencias locales en un archivo versionado de BWM, sin consulta automática a Git de los proyectos ni modificación de programas.
* **Verificado:** prueba del mínimo compatible conservado con una referencia más nueva (elegible aunque semáforo rojo por referencia antigua), misma versión verde, más nueva naranja y paquete con dígitos en el nombre. Suite completa: 161 pruebas OK, 29 omitidas. IPC de la galería con las tres skins `ok`.

### 125. Dependencias del tema con contraste automático y etiquetas breves (2026-11-10)
* **Petición:** retirar el blanco fijo de Dependencias; usar de nuevo el tema, con letras negras en temas claros y blancas en oscuros. Cambiar «Revisar» por «Falta» y «Más nueva» por «Desactualizado».
* **Hecho:** `ThemeUtils.js` calcula tinta negra/blanca según luminancia lineal, también en cabeceras, filas alternas, selección, buscador y detalles. `DependencyTable.qml` usa las superficies/bordes de la skin activa; `shell.qml` deja de forzar fondo blanco. Filas de 34 px y comportamiento compacto conservados. Leyenda «Correcta / Falta / Desactualizado»; una dependencia `missing`/`pending` muestra «Falta» donde iría la versión. Naranja conserva la comparación solicitada: instalada más reciente, con explicación «Referencia de BWM desactualizada» para no afirmar que el programa más nuevo sea antiguo.
* **Verificado:** componente real de tabla en una instancia Qt aislada sin acciones del escritorio: fondo Nord → `#ffffff`, fondo claro → `#000000`, sin errores QML. Captura recortada de la ventana real con Nord, letras blancas, referencias actualizadas y las nuevas etiquetas; borrada. 161 pruebas OK, 29 omitidas, Python compila y `configerrors` vacío. Sin cambio de tema/skin del usuario, instalación de paquetes ni reinicio de la barra.

---

### 126. Catálogo visual para añadir y publicar skins (2026-11-10)
* **Petición:** añadir una opción para descubrir más skins y elegir dónde publicarlas.
* **Hecho:** botón «+ Añadir skins» en BWMenu, búsqueda, tarjetas con capturas y estado instalada/disponible, acceso a la ficha instalada o a las instrucciones de instalación, actualización manual y guía «Cómo publicar». Sigue la apariencia activa de BWMenu. El índice `catalog/skins.json` se genera desde los manifiestos integrados mediante `scripts/bwm-skin-catalog.py build`; excluye la plantilla y las skins privadas del usuario, comprueba vistas previas y piezas. Nombre/descripción/captura siguen viniendo de `skin.json`.
* **Publicación:** repositorios existentes `saselandia/Better-Window-Manager` (GitHub, principal) y `saselandia/bwm` (GitLab, respaldo), rama main. Publicar código, recursos e índice juntos. `docs/SKIN_CATALOG.md` explica el proceso. No se ha hecho commit ni push: la URL remota del índice todavía no está disponible; el menú usa las tres skins reales del catálogo incluido.
* **Lectura:** HTTPS, límites de tamaño/entradas, metadatos validados, caché de una hora, refresco explícito y fallback a caché/copia incluida. No ejecuta instaladores remotos ni modifica la skin activa. La distribución actual es `bwm-update`: las skins completas se integran en BWM; carga e instalación autónomas de paquetes externos quedan pendientes y no se simulan copiando manifiestos.
* **Verificado:** catálogo generado coincide con manifiestos; ventana real con tema Nord, buscador y tres tarjetas, IPC con `catalogCount:3`, origen `bundled`, carga terminada y las tres skins listas. Captura sólo de BWMenu revisada y borrada. Pruebas de publicación, caché/refresco/fallback, metadatos inválidos/incompletos, error de escritura de caché y detección de nuevas entradas sin instalarlas. Suite completa: 169 pruebas OK (29 omitidas); tras añadir el caso de catálogo incompleto, las 9 pruebas específicas OK. Python compila, `git diff --check` limpio y configuración QML cargada sin errores (sólo aviso existente del portal de aplicaciones).

---

### 127. Repositorio independiente de skins en GitHub/GitLab (2026-11-10)
* **Cambio de criterio del usuario:** BWM debe incluir sólo las tres skins actuales; las futuras se distribuyen aparte. Petición explícita de crear `bwm-skins` en GitHub/GitLab y conectarlo a Añadir skins.
* **Publicado:** repos públicos `https://github.com/saselandia/bwm-skins` y `https://gitlab.com/saselandia/bwm-skins`, rama `main`, commit inicial `10c8c9b05b5d5aadf6f5f3a38d4b64bd8cd2655f` (coautoría Codex). Checkout `/mnt/HDD1TB/Projects/bwm-skins`; `origin` lee GitHub y hace push a ambos, más remotos `github`/`gitlab`. README, licencia MIT sólo para metadatos/documentación nuevos, plantilla fuera del catálogo, carpeta `skins/` y catálogo vacío; ninguna skin ficticia ni copia de las tres integradas. Las skins futuras conservarán sus propias licencias.
* **Conexión:** `bwm-skin-catalog.py` consulta raw GitHub del repo nuevo y GitLab de respaldo. Índice schemaVersion 2/catalogId bwm-extra-skins, delivery external-release, versión y compatibilidad descriptiva por publicación. Rechaza los tres ids integrados y el catálogo v1 anterior. Caché nueva `extra-skin-catalog-v2.json`; la copia incluida en BWM queda vacía. `build --catalog-root` genera desde `skins/<id>/catalog.json` del checkout externo; exige carpeta `skins/`, no escanea manifiestos de BWM ni plantillas.
* **Interfaz/documentación:** botón Repositorio, estado vacío explícito, versión en tarjetas y recarga manual. Abrir un catálogo vacío ya consultado no vuelve a descargarlo continuamente. Guías y reglas sincronizadas con la distribución separada. No se ha hecho commit/push del checkout de BWM en esta tarea.
* **Límite:** catálogo conectado y publicación separada preparados. Instalador automático y carga completa de módulos externos aún pendientes; no se presentan como hechos. El campo compatibility informa de la revisión probada, no aplica restricciones de instalación todavía.
* **Verificado:** hashes de main en GitHub y GitLab iguales al commit inicial; ambos endpoints HTTPS devuelven el catálogo v2 vacío y válido. BWMenu real: Añadir skins, origen remote, cero entradas y carga terminada; botones Repositorio/Cómo publicar visibles con Nord, las tres instaladas siguen listas. Captura recortada revisada y borrada. 171 pruebas OK (29 omitidas), incluidas 10 de catálogo; Python compila, índice externo actualizado, `git diff --check` limpio y AGENTS/CLAUDE iguales. QML recargado sin errores; aviso de portal existente. Checkout bwm-skins limpio tras el push.

### 128. Menú de Retro: Barra, Marca, Animaciones, Idioma y Entrada (2026-11-10)
* **Petición:** «Menú Barra/Setup» de lo que quedaba del estudio de Omarchy 4.5 (§4.4 de `docs/OMARCHY_4_5.md`), sin atajos nuevos. Comparado con `omarchy-menu.jsonc` de `quattro` `ec62d379` (HEAD del 2026-11-10); el resto de lo vendido sigue en `18ac93c`/`d9cc361c` y no se ha vuelto a comparar con upstream.
* **Estilo → Barra** (`appearance.top-bar`, los mismos ids que Omarchy: las traducciones es-MX de su `menu.json` se aplican solas; sustituye al enlace `appearance.bar`): Ocultar/Mostrar (`omarchy-toggle-bar`, la marca `bar-off` que ya vigilaba `Bar.qml`), Posición (✓ en la actual), Fondo (opaco, cristalino, transparente), Indicadores (% de batería sólo con batería: `omarchy-battery-present` en lugar de `omarchy-hw-laptop`; reloj con 10 formatos horizontales y 4 apilados, según la posición) y «Más ajustes…» (Ajustes → Barra).
* **Estilo → Marca** (Acerca de y Salvapantallas: editar texto, desde imagen, restablecer): `omarchy-branding-about|screensaver` adaptados. El logo por defecto es el del repo; `~/.config/omarchy/branding/{about,screensaver}.txt` sólo existe si lo personalizas y «restablecer» lo borra. `omarchy-launch-about` usa el tuyo si existe; `launch-screensaver.sh` ya lo leía (el salvapantallas sólo con el nativo instalado). Editar texto abre `$VISUAL`, `$EDITOR`, nvim o nano en una terminal flotante y vuelve a mostrar el resultado. Desde imagen: `omarchy-file-select` (portal GTK, ya instalado) + `omarchy-transcode-ascii` (ImageMagick), de upstream sin cambios.
* **Estilo → Animaciones** (con ✓): `omarchy-toggle-animations` → `omarchy-hyprland-toggle no-animations` copia `no-animations.lua` a `~/.local/state/omarchy/toggles/hypr/` y recarga Hyprland. `skins/retro/hypr/misc.lua` lee ahora `bar-glassy` y `no-animations` (lista fija: Omarchy lee la carpeta entera, pero sus otros interruptores, como `window-glassy`, necesitan piezas que BWM no tiene). Con el modo glass encendido el desenfoque sigue (`glass.lua` se carga después), como en Omarchy con `window-glassy`.
* **Ajustes → Idioma** (proveedor `languages` del menú) con `omarchy-language` de BWM: sólo escribe `~/.config/omarchy/language` (el mismo archivo que Ajustes → Barra) y sólo lista lo que BWM trae traducido (en, es-MX); no toca el locale del sistema ni usa sudo. **Ajustes → Entrada** abre tu `hyprland.lua` (Editar en texto); la plantilla de ese archivo trae ahora un ejemplo de `input` (sólo para archivos que se creen después: el tuyo no se toca).
* **Scripts:** 8 de upstream sin cambios en `omarchy-shims` (`omarchy-toggle`, `-toggle-enabled`, `-toggle-bar`, `-hyprland-toggle`, `-toggle-animations`, `-hyprland-animations-off`, `-transcode-ascii`, `-file-select`), 3 adaptados (`omarchy-language`, `omarchy-branding-about`, `omarchy-branding-screensaver`), todos enlazados en `~/.local/bin` con `bwm-plugin.sh catalog`.
* **No portado a propósito:** Seguridad (huella, FIDO2, sshd, sudo sin contraseña: pacman, PAM y sudo, que BWM no toca), DNS (cambiarlo es de root), Git/XCompose/Hyprsunset, Direct boot, Reset, y las distribuciones de teclado (la de BWM es `kb_layout` de `modules/binds.lua`; no hay ajuste propio).
* **Verificado:** `tests/test_retro_menu_catalog.py` (14 pruebas: catálogo sin ids repetidos ni huérfanos ni enlaces rotos, comandos `omarchy-*` que existen, entradas de la barra, shims en un HOME aparte con `hyprctl` simulado, `misc.lua` ejecutado con `lua`); suite de 185 pruebas OK (29 omitidas). En la sesión real: `omarchy-toggle-animations` off/on (`animations:enabled` true→false→true, sin marca al final, `configerrors` vacío), `omarchy-toggle-bar` (la barra sale de pantalla, y=-2160, y vuelve), `omarchy-bar get/set` del reloj con vuelta a `dddd HH:mm` y `shell.json` igual byte a byte, y los menús abiertos por IPC con capturas (Barra, Reloj con ✓, Estilo, Marca, Ajustes con Idioma y Entrada, Idioma con English ✓). `Hyprland --verify-config` correcto.
* **No probado:** pulsar las entradas con teclado o ratón (sólo IPC y los scripts), cambiar la posición de la barra desde el menú (probado por script en §3.118), los formatos apilados (barra vertical), «editar texto» y «desde imagen» de Marca (no se abrió la terminal ni el selector de archivos), cambiar de idioma desde el menú ni las otras skins (el menú es sólo de Retro).
* **Encontrado, anterior a este cambio:** en `tests/test_retro_ui.py` (opcional, con `BWM_RUN_QML_TESTS=1`) falla `test_native_complex_pages_use_the_existing_layer` en la página `style` y, por consecuencia, `test_z_no_runtime_errors`: desde §3.98 la página Estilo no tiene filas nativas, así que no hay «Más opciones…» y la entrada «Más estilo (Ajustes)» no se muestra (un enlace sólo se ve si su destino tiene filas). Fallan igual con el catálogo anterior. Las dos pruebas de enlaces que seguían `appearance.bar` ahora usan `appearance.top-bar.settings`.

---

### 129. Semáforos de grupos, tarjetas rectas y mascota animada de BWMenu (2026-11-10)
* **Petición:** luces junto a los nombres Núcleo/default/Retro/Breeze de Dependencias; recuadros de skins con esquinas cuadradas; mascota pequeña animada en la esquina inferior izquierda, con apariencia propia de cada skin.
* **Hecho:** `MenuButton.statusHealth` es opcional y reutiliza `StatusLight` con `core.versionHealth`/`skin.versionHealth`; misma comparación y semáforos existentes (verde/rojo/naranja/gris), sin alterar comprobaciones. `SkinCard` y `CatalogCard` tienen borde/vista previa de esquinas rectas, independiente del redondeo del tema; se conserva la miniatura del aspecto de la skin.
* **Mascota:** diseño original como pequeña ventana con antenas, pies y cara, dibujado con QML nativo; sin imágenes/recursos externos ni requisitos nuevos. `BwmMascot.qml` comparte movimiento, pausa, parpadeo y saludo accesible con ratón/teclado. Variantes separadas en `mascot/retro/Character.qml` (bloques, gafas y pasos de 2 px), `mascot/default/Character.qml` (formas blandas y flotación suave) y `mascot/plasma/Character.qml` (acabado Breeze biselado/brillo). Usa la paleta activa en vivo, sin modificar los formatos de temas originales. IPC inspect añade variante/ready/moving.
* **Verificado:** ventana real Retro/Nord, luces verdes junto a los cuatro selectores, tarjetas rectas y mascota visible. Vista aislada Qt sin acciones del escritorio con las tres variantes, muestras de movimiento distintas, cambio Retro→Plasma con Loader listo y pausa comprobada (SWITCH_OK/PAUSE_OK). `qmllint` limpio para mascota, variantes y MenuButton; QML real cargado sin errores, salvo aviso conocido del portal. `git diff --check` limpio. Capturas recortadas y pruebas temporales retiradas. Se reabrió sólo BWMenu para registrar el tipo QML nuevo; no se reinició ii ni se cambió el tema/skin del usuario. No se repitió la suite Python: el cambio es visual y se comprobó en Qt.

### 130. Duplicar pantalla (espejo) en el editor de pantallas (2026-11-10)
* **Petición:** lo que faltaba del panel de pantallas de Omarchy 4.5 (`docs/OMARCHY_4_5.md` §4.4): Duplicar.
* **Backend (`monitor-manager.py`, común a todas las skins):** cada pantalla lleva `mirrorOf` (la descripción de la que copia, `""` si es independiente); `get_monitors()` lo lee de `hyprctl monitors all` (el campo trae el nombre o el id) y `write_monitors_lua()` escribe `mirror = "desc:…"` en su `hl.monitor`. Una copia no ocupa sitio en el esquema, no tiene reglas de workspace y no puede ser la principal: si lo era, el 1-9 pasa a la pantalla que copia. Una copia cuyo origen se apaga, falta o es a su vez otra copia se descarta al guardar (`sanitize_mirrors`). Nuevo `set-mirror <pantalla> <origen|none>` y `set-primary` rechaza una copia.
* **Retro:** fila «Duplicar» tras «Pantalla activa» en `omarchyMenu/omarchy/settings/DisplaySettings.qml` (←→ recorre «No» y las demás pantallas activas), la copia se dibuja sobre la pantalla que copia con ⧉, no se puede mover en el esquema y su fila de workspaces dice «Ninguno (copia)»; la lógica está en `display/Layout.js` (`setMirror`, `mirrorChoices`, `sanitize`, y `bounds`/`normalize`/`snap`/`validate` ignoran las copias). **default y Breeze:** selector «Duplicar pantalla» en `modules/settings/DisplayConfig.qml` con la misma lógica (importa `Layout.js`) y traducciones es_ES/es_MX. El panel de pantallas de la barra de Omarchy ya tenía su propio Duplicar, pero sólo con pantalla interna (portátil).
* **Verificado:** `tests/test_monitor_mirror.py` (6 pruebas del backend: `mirror` escrito, sin reglas de workspace para la copia, relevo de la principal, volver a independiente, duplicaciones imposibles, lectura de `mirrorOf` desde `hyprctl`) y dos pruebas Qt nuevas del editor (`BWM_RUN_QML_TESTS=1`: duplicar y aplicar con el backend ficticio, y no mover una copia); las 8 pruebas Qt de pantallas pasan y la suite normal da 193 OK. En la sesión real: el `monitors.lua` generado por el backend (en una carpeta temporal) cargado con `hyprctl eval dofile` duplicó el LG sobre el MSI con `desc:` (`mirrorOf` = id del MSI, que el gestor devuelve como su descripción), y `hyprctl reload` lo restauró; la página de Ajustes → Pantallas común carga sin errores. Los archivos reales de monitores no se tocaron.
* **Efecto de la prueba:** mientras duplicaba, el workspace 10 pasó al MSI; tras restaurar volví a poner el 2 en el MSI y el foco en Firefox.
* **No probado:** aplicar un espejo desde el editor con clic (sólo la edición con teclado y el backend ficticio), la copia con resoluciones o escalas distintas a las del origen (Hyprland ajusta la imagen) y el selector de la página común más allá de que carga.

### 131. Revisión completa de BWM frente a Omarchy (2026-11-10)
* **Petición:** una gran comprobación del proyecto y de Omarchy para ver qué queda por meter.
* **Hecho:** comparación con un clon de `quattro` `c18b00c5` (shell, `bin/`, `default/`, temas, menú); resultado completo en `docs/OMARCHY_4_5.md` §6: sincronizaciones pendientes (notificaciones, Dropbox, colectores de agentes), opciones de Hyprland sin portar (la más importante `allow_session_lock_restore`, ahora `false`), reglas de ventana por app, entradas de menú aplicables, el `hyprland.lua` propio de cinco temas y diferencias de vidrio y Qt. No se cambió nada del sistema ni del repo salvo esa documentación.
* **Verificado:** 193 pruebas OK (31 omitidas), `hyprctl configerrors` vacío, `bwm check --skin retro` correcto, 60 destinos IPC y una sola instancia de Quickshell. En el log queda un aviso de `services/Notifications.qml` (código original de end-4: el temporizador de un aviso ya retirado), que no afecta a Retro.
* **No hecho:** ninguna de las incorporaciones listadas; la lista está ordenada por riesgo y valor para decidir cuáles se hacen.

---

### 132. Mascotas con animaciones propias: vaporwave, Breeze y Material You (2026-11-10)
* **Petición:** Retro con patinete y fondo vaporwave, surfeando; Breeze con barra gris KDE sobre la cabeza y flotación/balanceo suave al pulsar; default más Material You/end-4 y una animación pequeña elegida por BWM.
* **Hecho:** las tres variantes son escenas QML de 136×108 px. Retro incluye sol a franjas, estrellas, horizonte/cuadrícula de neón que avanza, gafas magenta/cian y patinete con ruedas y mástil; inclina el conjunto como al surfear y hace un giro al pulsar. Breeze tiene cabecera gris con minimizar/maximizar/cerrar dibujados, flotación lenta y un balanceo amortiguado al pulsar. default respira, conserva la forma blanda y los cuatro puntos de la frente se abren y giran 90° con una ligera deformación del cuerpo.
* **Estructura:** cada `mascot/<skin>/Character.qml` implementa `activate()`, `motionEnabled` y su animación. `BwmMascot.qml` sólo aloja, propaga paleta/visibilidad, parpadeo y activa por clic/Intro/Espacio/accesibilidad; no fuerza el antiguo salto común. Sin recursos externos ni dependencias nuevas. La paleta vaporwave de la escena es propia de esa ilustración; el cuerpo conserva el acento del tema.
* **Verificado:** `qmllint` limpio en los cuatro archivos. Prueba aislada Qt sin acciones del escritorio: las tres cargadas, movimiento en reposo, reacción a la misma función del clic con valores no nulos, pausa tanto de reposo como de reacción y cambio Retro→Breeze, todo OK (IDLE_MOTION_OK/ACTION/PAUSE_OK/SWITCH_OK). Capturas de reposo y clic revisadas. BWMenu real con Retro/Jade Horse: variante lista y en movimiento, escena visible y QML cargado sin errores salvo aviso conocido del portal. Capturas recortadas y archivos de prueba retirados. No se cambió la skin/tema ni se reinició ii; se abrió BWMenu. `git diff --check` limpio. Verificación centrada en Qt, sin repetir la suite Python para este cambio visual.

---

### 133. Mascota coherente entre skins, Retro transparente y botón de cierre (2026-11-10)
* **Petición:** animación de clic como una ventana que se mueve de lado y hacia arriba; Retro sin paisaje/suelo, menos vaporwave y más Omarchy, colores del tema y avance claro hacia la derecha; mejorar end-4 y reforzar la identidad compartida. Sustituir actualizar de la esquina superior derecha por cerrar.
* **Mascota:** `BwmMascot.qml` añade un desplazamiento compartido (derecha/arriba → izquierda/más arriba → regreso suave), sin mover la ventana real de BWMenu. Conserva gesto propio, accesibilidad y pausa completa al ocultarse. Las tres variantes comparten cuerpo tipo ventana de 56×43, antenas, pies y marca de cuatro puntos/píxeles. default tiene cabecera y superficies tonales, cuerpo más parecido a las otras y sus puntos animados; Breeze conserva la cabecera con marca común y usa colores derivados del tema, sin sombra de suelo.
* **Retro:** se retiraron sol, paisaje, cuadrícula y fondo; no hay suelo. Paleta íntegra del tema (accent/foreground/onAccent/surface), sin magenta/cian fijos. Patinete, ruedas que giran, postura inclinada hacia la derecha y estelas que se desplazan a la izquierda; ya no oscila horizontalmente de lado a lado en reposo. El clic refuerza la marcha además del desplazamiento común.
* **Cierre/actualización:** botón × con nombre accesible Cerrar BWMenu y `root.close()`, conservando el bloqueo durante acciones. Ctrl+R actualiza diagnóstico o catálogo según la página. Añadir skins conserva un botón Actualizar dentro de su buscador. IPC `closeMenu` activa el mismo manejador del botón.
* **Verificado:** Qt aislado, las tres cargadas y animadas; desplazamiento positivo en X y negativo en Y al clic en las tres, retorno exacto, pausa de reposo/reacción y cambio de paleta de Retro en vivo, OK (WINDOW_GLIDE_OK/LIVE_PALETTE_OK/RETURN_AND_PAUSE_OK). Capturas de reposo, clic y paleta alternativa revisadas. `qmllint` limpio en los cuatro componentes, `git diff --check` limpio. BWMenu real con default/Material You: mascota y × visibles, sin errores QML, salvo aviso del portal. Se invocó por IPC el mismo manejador del cierre: desapareció BWMenu sin abrir consola de rescate; reabierto después. No se cambiaron skin/tema ni se reinició ii. Capturas y prueba temporal retiradas; no se repitió la suite Python para este cambio visual.

### 134. Opciones de Hyprland, reglas por app y notificaciones de Omarchy al día (2026-11-10)
* **Petición:** los puntos 1–3 de la revisión de §3.131 (Dropbox aparte), sin romper BWM.
* **Comunes a todas las skins:** `misc.allow_session_lock_restore` (un shell relanzado por `window-guard.py` retoma el bloqueo en vez de dejar la pantalla roja), `key_press_enables_dpms` y `mouse_move_enables_dpms` (una tecla o el ratón encienden las pantallas apagadas por inactividad) en `modules/appearance.lua`; repetición de teclas 40/250 y bloqueo numérico al arrancar en `modules/binds.lua`.
* **Sólo Retro** (`skins/retro/hypr/misc.lua`, de `looknfeel.lua` de Omarchy `c18b00c5`): `extend_border_grab_area` 8, sin texto de bienvenida ni aviso de escala, `anr_missed_pings` 3, `initial_workspace_tracking` 0, puntero oculto al escribir y el workspace especial se cierra al cambiar de workspace. `appearance.lua` repone antes los valores por defecto para que no se queden al cambiar de skin.
* **Reglas por app:** 17 archivos de `default/hypr/apps/` de Omarchy copiados sin cambios en `Commons/omarchy/default/hypr/apps/` y cargados por el adaptador nuevo `modules/app_rules.lua` (da `o.window`, entorno propio para no pisar el `o` de Retro), justo después de `rules.lua`: imagen en imagen (flota, fija, 600×338), 1Password/Bitwarden fuera de las capturas, «is sharing» a `special silent`, Steam, Telegram sin robar foco, RetroArch/Moonlight a pantalla completa, DaVinci, LocalSend, superposición de webcam de las grabaciones, diálogos del portal y Papers/visor de Nautilus/imv/mpv flotantes (etiqueta `floating-window`). En Breeze se ignora el `tile` de los navegadores Chromium (todo flota); `transparent_window` no hace nada (la transparencia de Retro la lleva `omarchy_windows.lua`). Fuera: terminales, capas del shell y Battle.net.
* **Sincronizado con `c18b00c5`:** notificaciones (`Store.js`, `Service.qml`, `Icons.js`: avisos idénticos en una tarjeta, glifo del remitente) y colectores de uso `deepseek`, `fireworks`, `openrouter`, `kimchi`, `ollama` (antes quedaban por detrás del `collectors.py` ya actualizado).
* **Verificado:** `Hyprland --verify-config` y `configerrors` limpios; en la sesión (Breeze) las seis opciones comunes con sus valores nuevos y las de Retro en su valor por defecto; una kitty de prueba titulada «Picture-in-Picture» quedó flotante, fijada y a 600×338 en el workspace 9 (cerrada por PID, regla temporal retirada). `tests/test_app_rules.py` (4 pruebas: todos los archivos cargan, imagen en imagen, sin `tile` en Breeze, gestores de contraseñas); suite 197 OK (31 omitidas). Colectores ejecutados con `omarchy-agent-usage-update` (0,9 s, JSON válidos). El `Service.qml` nuevo compila hasta el mismo punto que el anterior en un `qs -p` aparte («Toast is not a type» en los dos, por cargarlo suelto).
* **Incidente de la prueba:** un `hyprctl eval dofile(misc.lua)` para comprobar las opciones de Retro las aplicó un momento en la sesión de Breeze; `hyprctl reload` las devolvió. Y un `pkill -f` con el patrón en el propio comando mató la shell de la herramienta (trampa conocida); la ventana de prueba se cerró después por PID.
* **No probado:** las opciones de Retro y las notificaciones nuevas en una sesión Retro real (la skin activa es Breeze), las demás reglas por app con sus apps reales y el despertar de las pantallas tras DPMS.

* **Validación previa al commit/push solicitado:** suite completa de 197 pruebas OK (31 omitidas), `qmllint` de mascota/variantes/MenuButton limpio y `git diff --check` limpio. Se incluyen sólo BWMenu, referencias, catálogo y documentación de este trabajo; se dejan fuera colores/perfiles generados y reglas persistentes ajenas.

### 135. Más de Omarchy en Retro: menú, `hyprland.lua` de los temas, vidrio y consola desplegable (2026-11-10)
* **Petición:** aplicar en Retro lo que quedaba de la revisión de §3.131 (menú, `hyprland.lua` de los temas, y las diferencias de vidrio y consola; Qt no).
* **`hyprland.lua` de cada tema:** `skins/retro/hypr/misc.lua` carga ahora `~/.local/state/omarchy/current/theme/hyprland.lua` (kanagawa, last-horizon, lumon, retro-82 y solitude lo traen y `bwm_omarchy_apps` ya lo copiaba) antes de los interruptores, como Omarchy: degradados de borde, sombras de Lumon y borde de grupos. Con el `o.transparent_window` de Omarchy como regla de opacidad (sólo lo usa kanagawa).
* **Menú de Retro** (`bwm-menu.jsonc`): Estilo → Ventanas → Esquinas (tema, rectas, redondeadas) y Huecos y bordes, con los interruptores `corners-*.lua` y `window-no-gaps.lua` de Omarchy (misma carpeta de interruptores que Animaciones); Ajustes → Plugins (activar, desactivar, añadir, clonar y quitar: `omarchy-menu-plugin`; el enlace anterior pasa a «Gestor de plugins»); Acciones → Transcodificar (`omarchy-transcode`, con `omarchy-menu-file`) y Compartir con LocalSend (sólo si está instalado: nuevo recomendado `localsend`, sin paquete en Gentoo); Actualizar → Temas extra (`omarchy-theme-extras` adaptado: mira también `~/.local/share/bwm/omarchy-themes`), Hora y Zona horaria (el selector real de Omarchy con `timedatectl` por polkit, en vez del aviso de antes).
* **Vidrio de Omarchy 4.5 en Retro** (`modules/glass.lua`, sólo con el modo glass encendido y la skin Retro): toda ventana al 75 % y desenfoque en las capas `omarchy-*`, como su `window-glassy.lua`; las otras skins no cambian.
* **Consola desplegable:** `skins/retro/hypr/qconsole.lua` de Omarchy (panel que baja desde arriba como workspace especial `qconsole`, centrado si hay una sola ventana), cargado por `appearance.lua`. Cambio de BWM: se abre con el agente predeterminado si lo hay y, si no, con la terminal predeterminada (`org.bwm.console`), para que nunca salga vacía. **Sin atajo** (no se añaden): menú → Acciones → Consola desplegable.
* **No portado:** `qtengine` (BWM sigue con el tema `gtk3` de Qt, que funciona y no necesita un paquete que no está en Gentoo) y las entradas de Instalar/Quitar, hardware, firmware, claves, Direct Boot y Aprender de tmux/herdr.
* **Verificado:** `Hyprland --verify-config` y `configerrors` limpios; 198 pruebas OK (nueva: carga del `hyprland.lua` del tema antes de los interruptores y los tres interruptores nuevos); la regla de vidrio ejecutada con un `hl` falso (Retro: `bwm-glass-all` y 2 capas; Breeze: sin cambios); menús Ventanas, Esquinas, Plugins, Acciones y Actualizar abiertos por IPC y capturados; la consola cargada un momento en tu sesión (Breeze): se abrió a media pantalla con la terminal y se cerró. `omarchy-theme-extras` y `omarchy-hyprland-corners` ejecutados en lectura.
* **Incidente de la prueba:** la consola abrió dos terminales (cargué su archivo dos veces con `hyprctl eval`, así que el evento corría duplicado) y una tercera reapareció tras cerrarla; las cerré por dirección y `hyprctl reload` quitó los manejadores. Un `Edit` mal hecho dejó `misc.lua` con un error de sintaxis un par de minutos (sólo afecta a Retro; no estaba activa): corregido.
* **No probado:** nada de lo de Retro en una sesión Retro real (ahora estás en Breeze): el `hyprland.lua` de un tema, el vidrio, las esquinas y los huecos aplicados, la consola con el agente, y Transcodificar, Compartir, Plugins y Zona horaria con clic.

### 136. Limpieza del menú y ajustes nativos de Retro (2026-11-10)
* **Petición:** revisar los últimos commits de Omarchy en Retro, retirar opciones sin efecto o repetidas y hacer coherentes los ajustes BWM con el menú, la estética sencilla y el teclado de Omarchy.
* **Menú:** un solo árbol Ajustes, sin la segunda Configuración y sin páginas genéricas de «Más opciones». Se retiran la barra/fondo/idioma heredados de end-4, el grabador de región duplicado, la lista parcial de temas, los enlaces duplicados y transparente/opaco (Glass permanece). Barra → Widgets comparte Plugins → Instalados. Temas conserva el carrusel original, también para la paleta dinámica, y su catálogo. Energía sólo se ofrece con batería o powerprofilesctl; los guards y aliases no se pierden al extender una fila desde ajustes y sus descendientes quedan ocultos también en búsquedas. Las rutas antiguas de páginas IPC se redirigen.
* **Ajustes:** `omarchy/settings/Catalog.js` ofrece sólo opciones usadas por Retro o servicios comunes; `skins/retro/scripts/settings.py` aporta listas de cursor, apps predeterminadas, atajos, inicio automático, plugins y catálogos, guardadas por los gestores existentes. Atajos nuevos admiten comandos/dispatchers, campos en borrador, activación, edición, restablecer los originales y eliminar los propios. Inicio automático añade apps/comandos, activa/desactiva, asigna workspace y quita entradas, sin ejecutarlas al editar. Plugins usa las seis zonas reales de Omarchy y conserva sus shims. Catálogos buscan en la caché completa y muestran lotes de 60 con Mostrar más; no se cargan miles de filas de golpe. Errores de JSON con `success:false` también se tratan como fallo; no se cambia el formato de preferencias ni se edita la zona de texto del usuario.
* **Pantallas:** sigue siendo una vista de Omarchy dentro de la capa, con esquema y borrador antes de Aplicar. Se eliminan las coordenadas duplicadas con el esquema y la segunda opción de principal (se asigna con workspaces); una pantalla duplicada no ofrece workspaces propios. Se acortan etiquetas y ayudas de edición. Se retira el adaptador de páginas compartidas de `SettingsPage.qml`: no altera la paleta global para mostrarlas.
* **Otros arreglos:** se cita correctamente `'gpu-screen-recorder|wf-recorder'` en las órdenes de grabación (antes Bash lo interpretaba como una tubería) y Reiniciar barra fuerza `--restart-shell`. No se ejecutan esas acciones durante las pruebas.
* **Validación:** `BWM_RUN_QML_TESTS=1 python3 -m unittest discover -s tests -v`: 217 pruebas OK, incluidas 36 de Qt con teclas reales en un `qs -p` aislado y 12 del adaptador con mutaciones simuladas. Validados JSONC, comandos Bash y `git diff --check`. Revisadas visualmente cuatro tarjetas recortadas en el arnés (Ajustes, Pantallas, Añadir atajo y Cursor), y Cursor en la sesión real; abiertas por IPC también apps predeterminadas, inicio automático, atajos, plugins y catálogo de temas. Quickshell recargó la configuración sin reinicio y conserva los destinos IPC; `hyprctl configerrors` vacío. El registro de sesión muestra avisos de ToolbarTabBar, Revealer, la traducción en_US ausente y el registro MPRIS, en módulos no modificados. El arnés bloquea acciones externas y guarda sólo en gestores simulados; los archivos reales de pantallas se mantuvieron intactos. Capturas y copias temporales eliminadas.
* **Límites:** las mutaciones se verifican con gestores simulados; no se cambian cursor, apps, atajos, inicio automático ni plugins del usuario, ni se instala ningún complemento. Tampoco se cambia la configuración de las otras skins.

### 137. Conservar todas las ventanas de Firefox al apagar (2026-11-10)
* **Problema:** Firefox recuperaba sólo una ventana. El perfil activo ya tiene `browser.startup.page = 3`; `bwm-power` cerraba cada ventana mediante el compositor, lo que Firefox considera ventanas descartadas antes de salir. Mozilla documenta que ese cierre sólo restaura la última ventana, frente a salir de la aplicación completa.
* **Corrección:** antes del cierre genérico, `bwm-power` identifica los PID de ventanas Firefox, comprueba su ejecutable en `/proc` y envía un único SIGTERM por proceso, como el reinicio existente de Firefox. Excluye esas ventanas del cierre individual si la señal se entregó; mantiene la espera de procesos y el cierre de las demás apps. El modo `--dry-run` no manda señales.
* **Sesiones privadas:** inspeccionadas sólo cantidades, sin volcar títulos ni URL. La sesión anterior contiene una ventana abierta y cuatro cerradas; la actual contiene dos abiertas y cuatro cerradas. Copia preventiva local bajo `~/.local/state/bwm/firefox-session-backups/`, fuera del repo. No se restauran automáticamente ventanas cerradas porque no sabemos cuál busca el usuario; se indica Historial → Ventanas cerradas recientemente.
* **Validación:** cuatro pruebas de `tests/test_power_session.py` con comandos de compositor, señales y espera sustituidos: dos ventanas del mismo proceso, otros ejecutables, fallo al señalar y simulación sin efectos. `bash -n` correcto y `bwm-power logout --dry-run` sin acciones reales. No se cierra ni reinicia Firefox, no se modifica su perfil y no se apaga ni cierra la sesión real; pendiente verificar la restauración después del siguiente cierre normal.

### 138. Plan de Breeze como KDE Plasma porteado: fase 0, viabilidad y arquitectura (2026-11-10)
* **Petición:** rehacer Breeze como un port real de KDE Plasma 6 compatible con sus temas (panel, Kickoff, reglas, barras, detección de CSD, min/max, menús de clic derecho, Preferencias, snapping), con un plan de prompts por fases para Opus 5.5. Plan en `docs/BREEZE_PLAN.md` (F0–F13); la fase 0 está hecha y su resultado está en `docs/BREEZE_ARCH.md`. La skin Breeze en uso no ha cambiado.
* **Paquetes** (instalados por el usuario, Plasma 6.7.5 / KF 6.29): ksvg, libplasma, plasma5support, kdecoration, breeze, aurorae, systemsettings, plasma-workspace (con `-semantic-desktop`; arrastra kwin, que no se ejecuta), plasma-nm, plasma-pa, bluez-qt; USE `qml` en kconfig, prison y qtmultimedia (`/etc/portage/package.use/bwm-plasma`). Declarados en `requirements.json` y como `recommends` de Breeze; `docs/REQUIREMENTS.md` regenerado. Descartados kscreen (podría reconfigurar monitores), plasma-desktop y bluedevil.
* **Comprobado:** KSvg, PlasmaComponents 3 y Kirigami cargan en Quickshell y pintan el estilo de Plasma activo, también un tema de terceros (Layan); la recarga en vivo necesita escribir con notificación de KConfig (`kwriteconfig6 --notify`), no reescribir el archivo. Los plasmoides reales no sirven como shell (sin KWin ni plasmashell; la bandeja intenta quedarse con los avisos), pero sus módulos de datos sí (volumen, red, MPRIS; bluezqt sin terminar de comprobar). Las decoraciones reales de KDecoration3 (Breeze y Aurorae de terceros) se cargan y pintan fuera de KWin con un `DecorationBridge` propio (prueba en `src/bwm-decorator/poc-fase0.cpp`; hay que llamar a `apply(nextState())`). Los KCMs de Apariencia y Gestión de ventanas cargan con `kcmshell6` sin KWin (no vistos ni usados); `plasma-apply-*` y `lookandfeeltool` funcionan, y este último también escribe gtkrc, Trolltech.conf y el cursor en `kdedefaults`.
* **Arquitectura decidida:** QML de Plasma portado a Quickshell con KSvg/PC3/Kirigami y un `PlasmoidShim`; decoraciones con un auxiliar `bwm-decorator` (Qt + KDecoration3) y `breezebars` como pegamento (F6 se divide en F6a/F6b); KCMs reales en Preferencias.
* **Conflictos encontrados y corregidos en este equipo:** al activarse por D-Bus durante las pruebas, `kded6` cargó todos sus módulos (bandeja, agente de NetworkManager, teclas multimedia, cambio automático de tema). En KF6 el archivo de configuración **sigue siendo `kded5rc`**; el primer intento con `kded6rc` no tuvo efecto. Creado `~/.config/kded5rc` con esos módulos en `autoload=false`; tras reiniciarse, kded6 sólo carga `ktimezoned`. plasma-workspace añade un segundo servicio de D-Bus para `org.freedesktop.Notifications`: se creó `~/.local/share/dbus-1/services/org.freedesktop.Notifications.service` con `plasma_waitforname --timeout 25` para que nunca arranque otro demonio. Las pruebas activaron kactivitymanagerd, kwalletd6 y ksecretd (dueño de `org.freedesktop.secrets` mientras corre); se pararon por PID. La bandeja y los avisos siguieron siendo de Quickshell en todo momento. Reglas temporales retiradas con `hyprctl reload`, `configerrors` vacío.
* **No probado:** captura de los controles de Plasma dentro de una ventana real de Quickshell (sólo en `qml6` sin pantalla), los KCMs a la vista, las listas de apps de `Kicker.RootModel` (salieron vacías), escala fraccionaria en las decoraciones y el envío de la imagen al plugin. `tests/test_skins.py` OK y `bwm check --skin plasma` correcto.

### 139. Fase 1 de Breeze: motor de temas de Plasma (2026-11-10)
* **Petición:** fase 1 de `docs/BREEZE_PLAN.md`: un servicio único con el tema de Plasma activo, leído de los archivos reales de KDE y en vivo, sustituyendo la paleta fija Breeze Dark (repetida en `bwm-theme-manager.py` como `BREEZE_DARK_M3`, en `MaterialThemeLoader.applyBreezeColors` y en `plasmaCommon/Breeze.qml`).
* **Hecho:** `skins/plasma/scripts/plasma_palette.py` (esquema de KDE → roles Material 3, kitty con el ANSI de Konsole «Breeze» sobre el fondo View, `plasma_colors.lua`, rofi; color de acento de `[General] AccentColor` si no viene del fondo). `plasma-theme.py`: `colors` (plasma-apply-colorscheme real o el shim de default; si el de Plasma dice «already set», fusiona igual), `desktoptheme`, `icons`, `lookandfeel` (lee `contents/defaults` del paquete y escribe cada clave con `kwriteconfig6 --notify`, sin cursor, fondo ni disposición, y sin gtkrc/Trolltech.conf que escribiría `lookandfeeltool`), `cursor` se niega (regla 14), `list`, `current`, `save`/`restore` del kdeglobals de Breeze, `sync`. El gestor llama a `save` al salir de Breeze y a `restore` al entrar (la primera vez aplica Breeze Oscuro conservando fuentes y demás claves que no son de BWM). `apply_plasma_colors` y `apply_plasma_app_themes` usan la paleta del esquema y ponen GTK y `color-scheme` en claro u oscuro según el esquema. `bwm_icons`: en Breeze no reescribe kdeglobals y el tema de iconos es `[Icons] Theme`. `MaterialThemeLoader` lee `~/.local/state/bwm/plasma/colors.json` (Breeze Dark sólo si aún no existe). Nuevo singleton `modules/plasma/theme/PlasmaTheme.qml` (todos los grupos de KColorScheme, WM, acento, estilo de Plasma, iconos, fuentes; vigila kdeglobals y plasmarc) y `Breeze.qml` como fachada. Barra y Kickoff actuales toman sus colores principales de `Breeze` (se sustituyen en F3/F4; `bar.plasma.color` sólo manda si no es el antiguo `#24292e`). `environment.lua`: en Breeze `QT_QPA_PLATFORMTHEME=kde` (con plasma-integration) y `~/.config/kdedefaults` delante en `XDG_CONFIG_DIRS`. Kvantum declarado como recomendado (lo piden muchos temas globales).
* **Comprobado:** 8 pruebas nuevas (`tests/test_plasma_theme.py`, HOME temporal, esquemas y tema global falsos, sin herramientas de KDE): paleta clara/oscura, acento, fusión de grupos conservando el resto, tema global sin cursor ni fondo, listados, primera entrada con kdeglobals de BWM, guardar/devolver, `sync` sólo reaplica dentro de Breeze. Plantillas reales renderizadas con Breeze Claro en un HOME temporal sin ejecutar hooks: GTK 3/4, Vesktop, Firefox, Pywalfox, Steam, Stremio, Omacalc, qt6ct, btop, rofi, swaync, Spicetify y Quickshell sin marcadores sin rellenar; GTK pasa a `light`. `PlasmaTheme` en `qs -p` con una configuración aislada cambió en vivo de Breeze Oscuro a Breeze y de estilo `default` a `breeze-light`. «Obtener nuevos…» (KNewStuff, sin pantalla, en un `XDG_DATA_HOME` aislado) descargó de la KDE Store el esquema, el estilo de Plasma, la decoración Aurorae y el tema global Sweet a sus carpetas estándar; `plasma-theme.py lookandfeel Sweet` aplicó esquema, estilo, iconos (candy-icons) y decoración Aurorae, y KSvg pintó el estilo Sweet. Sin errores nuevos en el log del shell real (Retro) tras recargar `MaterialThemeLoader`; `Hyprland --verify-config` correcto; pruebas de skins OK.
* **No probado:** `QT_QPA_PLATFORMTHEME=kde` y `kdedefaults` con una app Qt abierta. Sweet pide el estilo `kvantum` (instalado después: `x11-themes/kvantum`, sólo en `~amd64`). Con `QT_QPA_PLATFORMTHEME=kde`, que Breeze pone, Kirigami toma los colores del esquema de Sweet (comprobado en `qml6`); sin el plugin de KDE cae a una paleta genérica. Los iconos incluidos de los applets actuales siguen siendo Breeze oscuro.
* **Prueba en la sesión real (2026-11-10, a petición del usuario):** Retro → Breeze en 1,3 s. La primera entrada aplicó el tema global Breeze Oscuro (kdeglobals sin la marca de BWM, `colors.json`, kitty con el fondo View `#141618`, `plasma_colors.lua`, GTK oscuro, iconos `breeze-dark`); sin errores nuevos en el log del shell. `plasma-theme.py colors BreezeLight` (0,5 s) puso en vivo kitty, GTK (`prefer-light`) y Kickoff en claro, sin reiniciar el shell; vuelta a Breeze Oscuro igual. El panel conserva el color propio del usuario (`bar.plasma.color` `#000000`), así que con un esquema claro el texto oscuro apenas se lee: se resolverá con el panel portado (F3). Breeze → Retro: el kdeglobals de Breeze quedó guardado en `~/.local/state/bwm/plasma/kdeglobals` y el de Retro quedó idéntico al de antes; las 12 ventanas y los workspaces visibles (1 y 10) se conservaron; Firefox y Steam se reiniciaron como ya hacían (§3.82, §3.85). El foco no se restauró solo (pasó de Vesktop a Kate) y se devolvió a mano. Corregido: sin `ColorScheme` en kdeglobals, el nombre es Breeze Claro (KConfig no escribe el valor por defecto). Capturas recortadas y borradas.

### 140. Fase 2 de Breeze: puente de configuración KDE ↔ BWM (2026-11-11)
* **Petición:** sincronizar KCMs y BWM respetando la autoridad de los ajustes comunes (regla 14), el usuario al final (18), el formato de KDE y el aislamiento entre skins.
* **Hecho:** inventario por clave y límites en `docs/BREEZE_ARCH.md` §9. Nuevo `skins/plasma/scripts/kde-config-bridge.py`: export/import, ciclo enter/leave, vigilante inotify con candado, debounce, huellas y escrituras atómicas conservando enlaces/comentarios/claves ajenas; reintenta archivos incompletos o modificados concurrentemente. KConfig recibe su señal original `ConfigChanged(a{saay})`. Exporta cursor/tamaño, teclado efectivo del compositor, Kelvin/estado nocturno, workspaces, idioma y terminal; MIME usa su archivo XDG común. Sólo importa fuentes de Breeze; si cambian ambos lados gana KDE en aspecto, con `user/shell.jsonc` aplicado al final. Emite una caché Lua de opciones de ventanas. `skins/plasma/hypr/kwin.lua` aplica foco, duración de animaciones, distancias enteras de encaje y acciones/botones soportados por el plugin actual; `placement.lua` atiende las políticas de KWin. Todo se carga antes del Lua del usuario. No se toca ni recompila el plugin.
* **Ciclo y servicios:** el gestor devuelve el kdeglobals de Breeze, llama a enter antes de su recarga única y lanza watch con `bwm_session.spawn`. Al salir detiene el vigilante, retira sólo las claves que siguen teniendo el valor exportado y guarda el kdeglobals de Breeze antes del entrante. Nuevos hooks genéricos de cursor, pantallas, luz nocturna, apps predeterminadas y apply-user, declarados en `hooks.settingsChanged` del manifiesto (sin código KDE en las otras skins). Autostart restablece el puente sólo en Breeze. `guards` mantiene kded5rc y el servicio de avisos de BWM; también lo llama el instalador. Se conserva un servicio de avisos propio del usuario. Para las escrituras heredadas de krdb se guarda el estado previo de GTK1/2 y claves Qt4 de Trolltech, se repara sólo lo conocido y se conserva lo ajeno.
* **Cambio de skin sin interrupción:** eliminados los reinicios diferidos antiguos de Firefox en `bwm-theme-manager.py` y Steam en `steam-theme.sh` durante una transición; las apps que requieren reinicio toman el aspecto al abrirse de nuevo. Necesario para probar el puente cumpliendo la regla 16.
* **Comprobado:** 14 pruebas del puente con rutas XDG temporales (sin cambiar HOME), ida/vuelta, prioridad, conflictos, metadatos ajenos, cambios atómicos, enlaces, protección de bwm/user, inotify, guardas y reparación GTK/Qt4; se amplían también las pruebas Lua de colocación. En sesión real: Retro → Breeze, cursor Miku 48 → 40 desde el gestor BWM; `kcminputrc` mostró el tema correcto y 40. Un cambio KDE de cursor se corrigió automáticamente. Lote de foco/encaje: un evento configreloaded y follow_mouse pasó a 1. Se detectó que Hyprland rechaza distancias flotantes como 19.0: corregido a int y el compositor aplicó 19. Después, cursor 48 y cursor.lua original, vuelta a Retro: kdeglobals idéntico, 11 ventanas con los mismos PID, foco conservado, vigilante terminado; no hubo capturas. Config de Hyprland verificada también cargando los módulos Breeze en un archivo aislado. No se añadieron paquetes: inotify usa libc y las señales GLib, ya declarados. El log contiene los avisos previos de imágenes de notificaciones, BarContent y registro polkit durante la transición; terminó con «omarchy polkit agent registered».
* **Validación final:** 245 pruebas OK (36 de interfaz optativas omitidas), Python y Bash verificados; `Hyprland --verify-config` con la configuración real y un archivo aislado de Breeze correctos, `hyprctl configerrors` vacío, `bwm check --skin plasma` correcto. La tabla de requisitos coincide con su generador; no hay QML nuevo que requiera qmllint. El perfil generado `config-plasma.json` conserva las fuentes recibidas de KDE y se excluye del commit según la regla 5.
* **Límites pendientes:** política exacta de auto-raise/demora, intervalo doble clic de la barra, bancos simultáneos y botones distintos de I/A/X (F6/F8/F9); zonas de mosaico y encaje central (F10); KCMs abiertos visualmente (F11). Las políticas de colocación adicionales y botones se prueban de forma aislada; la configuración de los botones con el plugin cargado se verifica en el próximo inicio de sesión. KScreen no tiene equivalente funcional en Hyprland: pantallas siempre por el gestor común.

### 141. Fase 3 de Breeze: panel de Plasma y tareas/reloj portados (2026-11-11)
* **Petición:** sustituir el panel hecho a mano por un port con los SVG y comportamiento de Plasma, cuatro bordes y reserva de espacio correcta.
* **Hecho:** módulos propios en modules/plasma/panel; PanelBackground deriva de plasma-desktop v6.7.5 desktoppackage/contents/views/Panel.qml, Task y TaskPrefixes de applets/taskmanager, reloj compacto de plasma-workspace applets/digital-clock. Se conservan avisos SPDX y GPL-2.0-or-later (texto añadido en licenses). El anfitrión de Quickshell adapta PanelView/PanelShadows: sombras SVG, prefijos por borde, capas traslúcida/sólida y opacidad adaptable. Geometría pura en PanelLogic.js, estado en PanelState; cuatro bordes, flotación, alineación/longitud/grosor y modos siempre/ocultar/esquivar/ventanas por debajo. Loader por ruta vacía fuera de Breeze para mantener sus requisitos KDE aislados.
* **Tareas y ajustes:** TasksModel usa TaskbarApps/HyprlandData (sin PlasmaWindowManagement), resuelve IDs .desktop sin distinguir mayúsculas, mantiene grupos/ancladas, clic central para nueva instancia, rueda, orden por arrastre y miniaturas ScreencopyView. Clock de KDE y PC3 con time.format compartido. Editor de seis widgets incluidos (añadir/quitar/ordenar) y página PlasmaBarConfig actualizada; la configuración es bar.plasma (lo permite F3), sin un falso appletsrc. Retirado el fondo de color plano; el estilo de Plasma manda. Kickoff, bandeja y applets anteriores se conservan hasta F4/F5, con sus anclajes actualizados. bwm_windows.traditional_box consume reserved real; quick-tile y placement ya lo usaban.
* **Requisitos y documentación:** KSvg/libplasma/plasma-workspace pasan a requires de Breeze; Kirigami y el módulo plasma-clock declarados en catálogo/skin y tabla regenerada. README de procedencia y límites, THIRD_PARTY_NOTICES, arquitectura §10 y plan actualizados. Sin paquetes nuevos que instalar: estaban presentes desde F0. Estimación de compatibilidad de temas ~35 % (README/SKINS), con limitaciones explícitas.
* **Probado:** ocho combinaciones en la sesión real (Breeze/default y Sweet de KDE Store, cada uno en cuatro bordes), con captura limitada al panel y reserva exacta de 44 px sólo en el borde elegido. El host usa el grosor configurado, no un valor fijo. AutoHide/Dodge/WindowsGoBelow reservan cero; el último permanece visible. Dos reinicios de mantenimiento del shell para cargar el módulo y las correcciones; nunca una segunda instancia ii. Una animación de posición causaba desplazamientos al cambiar de orientación y se retiró. Se verificó también el Loader por ruta y se corrigieron accesos nulos de tareas durante destrucción de la skin.
* **Validación final:** 253 pruebas OK (36 opcionales omitidas), incluidas ocho nuevas de geometría/orden/área útil; Python y configuración de Hyprland verificados, configerrors vacío. qmllint ejecutado con avisos de imports virtuales/metadatos, complementado con carga real del módulo y compilación aislada del editor.
* **Sesión y límites:** devuelto a Retro con ajustes del panel y estilo de Plasma restaurados; los 17 PID de ventanas del último lote se conservaron. Se encontró kded6 con sólo ktimezoned pero reteniendo org.kde.StatusNotifierWatcher sin objeto de bandeja; se cerró ese PID y Quickshell tomó el nombre, mostrando los iconos de bandeja. Pendientes: validar interacción completa de arrastre/miniaturas/edición, Unity LauncherEntry (insignias/progreso), reloj multizona y plasmoides externos (F0 no proporciona anfitrión compatible). Se ofrecen sólo widgets incluidos, no el catálogo general de Plasma. Los logs conservan avisos de Notifications y otros módulos anteriores; sin errores nuevos de modules/plasma/panel tras corregir accesos de destrucción. Capturas borradas al terminar.

### 142. Fase 4 de Breeze: Kickoff de Plasma portado (2026-11-11)
* **Petición:** fase 4 de `docs/BREEZE_PLAN.md`: sustituir el Kickoff hecho a mano (`modules/ii/plasmaKickoff`, 925 líneas) por el de Plasma 6.7.5.
* **Hecho:** `config/quickshell/ii/modules/plasma/kickoff` = `applets/kickoff` de plasma-desktop v6.7.5 (GPL-2.0-or-later) y sus 62 catálogos `po/` del paquete publicado. Los modelos son los reales de `org.kde.plasma.private.kicker` (plasma-workspace): el «RootModel vacío» de F0 era que faltaba `refresh()`, que el original llama al crear la vista. Favoritos y recientes en KActivities (cliente `org.kde.plasma.kickoff.favorites.instance-bwm`, primera vez desde `bar.plasma.kickoff.favorites`). Adaptado con `// BWM:` (detalle en el README de la carpeta): `main.qml` → `Kickoff.qml` (`Item` con `expanded`/`hideOnWindowDeactivate` sincronizados en los dos sentidos con `GlobalStates.plasmaKickoffOpen`, sin representación compacta), singleton `Plasmoid.qml` en lugar del attached (configuración = claves de `main.xml` en `bar.plasma.kickoff` de `Config.qml`), `KickoffI18n.qml` (KI18nContext con el dominio original; `plasma-theme.py translations` compila los `.mo` en `~/.local/share/locale`, también al entrar en Breeze), menús con `PC3.Menu`, sesión con `bwm-power`, y `KickoffWindow.qml` como diálogo (fondo `solid/dialogs/background`, sin el borde del lado del panel, alineado con el botón, cierra al pulsar fuera salvo fijado y con Escape). Botón del panel (`PanelContent.qml`) ancla y abre Kickoff; Alt+F1 nuevo sólo en Breeze; `IllogicalImpulseFamily.qml` lo carga sólo en Breeze (antes el Kickoff antiguo se cargaba en todas las skins). `kactivitymanagerd` declarado como recomendado.
* **Encontrado:** `PlasmaExtras.Menu` es un QMenu: sin QApplication tira Quickshell; con ella (la del shell) Qt no crea su ventana emergente desde una capa de layer-shell. Kicker resuelve `preferred://filemanager` al navegador (el Kickoff de Plasma pone Dolphin explícito): los favoritos por defecto llevan `org.gnome.Nautilus.desktop`. Al lanzar algo, el QML de Plasma asigna `kickoff.expanded = false` y rompía un enlace simple con el estado global: al reabrir, Kickoff seguía «cerrado» (Escape y el vaciado de la búsqueda dejaban de funcionar); se sincroniza en los dos sentidos. Escape lo recoge un atajo a nivel de aplicación, como el diálogo de Plasma, porque la búsqueda reenvía las teclas a la vista. Sin kmenuedit se oculta «Editar aplicación…»; sin Discover Kicker no ofrece «Desinstalar».
* **Comprobado:** `tests/test_plasma_kickoff_ui.py` (opcional, `BWM_RUN_QML_TESTS=1`): 5 pruebas con teclas reales de QtTest en una instancia `qs -p` aparte, con la configuración bloqueada, otro cliente de favoritos (vaciado al terminar) y una app de prueba en `XDG_DATA_DIRS` temporal: 13 secciones y 57 apps, 4 favoritos, búsqueda que encuentra la app de prueba e Intro que la lanza (crea su archivo) y cierra; ↓ desde la búsqueda al contenido, → / ← en la rejilla, ← a la barra lateral, ↓↓ cambia de categoría, → vuelve; tecla Menú abre el menú contextual («Add to Favorites», sin separadores sobrantes ni kmenuedit); Escape cierra tras reabrir. Capturas recortadas del Kickoff revisadas y borradas. Reinicio de mantenimiento del shell real (Retro): una instancia, sin errores nuevos, mismos workspaces y foco. Pruebas de skins y del motor de temas OK.
* **Incidentes:** una primera prueba sin `Config.blockWrites` guardó `favoritesPortedToKAstats` en `config.json` y los favoritos en el cliente real de KActivities: se deshizo. Un `pkill -f` con el patrón en la propia orden mató la shell de la herramienta (trampa conocida).
* **Prueba en la sesión real (2026-11-11, a petición del usuario):** al entrar en Breeze **Quickshell se cayó dos veces** (se reinicia solo): `KickoffListDelegate` de medida en `Kickoff.qml` no da la propiedad requerida `isMultilineText` (el original tampoco); creado de forma síncrona sólo avisa, pero en la carga asíncrona del `PanelLoader` aborta la creación y, al destruir lo ya creado, KSvg cae en `QObject::disconnect`. Corregido (`isMultilineText: false`) y la prueba de interfaz ahora crea Kickoff con un `Loader` asíncrono: sin la corrección falla, con ella pasa. Dos causas más, también corregidas: `XDG_MENU_PREFIX=plasma-` (sin él KService no carga `plasma-applications.menu` y Kickoff no tiene categorías; se pone en todas las skins si existe el menú, porque la caché `ksycoca` es el mismo archivo con cualquier prefijo y otra skin la reconstruiría sin categorías; se reconstruyó con el prefijo) y el primer volcado de favoritos a KActivities, hecho en la instancia que se cayó (marcado como hecho pero vacío: se repitió). Tras un reinicio de mantenimiento en Breeze (el shell hereda `XDG_MENU_PREFIX`, `QT_QPA_PLATFORMTHEME=kde` y `kdedefaults`), Kickoff abierto por IPC en el monitor principal: pegado al panel, colores y fuente del tema, favoritos (Firefox, Archivos, kitty, Preferencias), todas las categorías con su marca de «nueva»; los botones de apagado salen al lado de «Session» cuando hay sitio y se recogen en él cuando no, como el original. Vuelta a Retro sin caídas, mismos workspaces; el foco pasó de Claude a ChatGPT y se devolvió a mano. Capturas recortadas y borradas; informes de las dos caídas borrados.
* **No probado:** botón del panel con el ratón, Super y Alt+F1 pulsados, posición con el panel en otro borde, arrastrar a favoritos y los botones de apagado reales. La sesión está en `en_US`, así que se ve en inglés como en Plasma; el español no se ha visto. La página de configuración de Kickoff llega con F11.


### 143. Fase 5 de Breeze: bandeja y applets de Plasma (2026-11-11)
* **Petición:** portar systemtray y las interfaces de red, Bluetooth, audio, notificaciones/toasts, reproductor, batería/brillo, portapapeles y calendario sin tocar radios reales al probar.
* **Hecho:** modules/plasma/tray usa el delegado AbstractItem/PulseAnimation de Plasma 6.7.5 y SNI de Quickshell, rejilla de ocultos, modos Auto/Shown/Hidden por ID (bar.plasma.trayItems), PC3 para menús DBus y un popup por sesión/monitor. modules/plasma/applets aloja AppletHost, vistas de plasma-pa/plasma-nm/mediacontroller/CalendarView y componentes de notificaciones, delegados Klipper/PowerDevil; Bluetooth y varias representaciones son ports reducidos. El panel queda revelado al abrir la bandeja. El reloj abre CalendarView; IPC anteriores conservados. Retiradas plasmaNetwork/Bluetooth/Audio/Notifications/Calendar y parts actualizadas. Loader por ruta sólo en Breeze.
* **Servicios:** las acciones de GlobalService de plasma-pa cargaban audioshortcutsservice: se sustituyen por Audio común; sin KDEDProxy, MicrophoneIndicator, migración de ajustes globales ni Globals/Server de notificaciones de Plasma. Radio/secretos de NM siguen en el NM existente; Bluetooth usa el proveedor común. No se inicia Bluedevil, PowerDevil ni Klipper. Toasts de KDE sobre services/Notifications (monitor preferido, bloqueo y DND comunes); tres simultáneos. Corregidos accesos a temporizador/acción inexistente al descartarse un aviso. Paquetes ya instalados desde F0; nuevos módulos QML requeridos declarados y tabla regenerada.
* **Procedencia:** fuentes de plasma-workspace, plasma-pa, plasma-nm, bluedevil y powerdevil comprobadas en v6.7.5. Cabeceras y licencias GPL/LGPL con alternativas/ref de KDE conservadas, textos en licenses, THIRD_PARTY_NOTICES y README por carpeta. Compatibilidad estimada ~45 % con límites explícitos.
* **Pruebas y límites:** pruebas de carga aisladas y QtTest con Bluetooth/notificaciones simulados, SNI, popup, calendario y toast. Red/audio con controles deshabilitados; ninguna conexión/desconexión ni cambio de radio real. Las ventanas ocultas no terminaban de dibujar las transformaciones del StackView: pruebas de clic con pequeña capa visible sin foco de teclado. Pendientes OBEX, jobs/inline reply/DND programado, edición/QR e imágenes del portapapeles, agenda/multizona configurable, perfiles/inhibición de PowerDevil y validación de acciones reales/menús de terceros. No se presenta equivalencia completa con cada applet.

* **Validación final:** 273 pruebas OK (52 de interfaz opcionales omitidas) y 15 pruebas F5 con BWM_RUN_QML_TESTS=1 OK (11 de interfaz, cuatro de visibilidad). Python, bwm check y verificación de Hyprland correctos; configerrors vacío. qmllint de todos los QML nuevos ejecutado con avisos de imports/metadatos y accesos dinámicos, sin errores de sintaxis; carga real de cada página y compilación de panel/controlador comprobadas. Se revisaron capturas sólo de las vistas (audio, Bluetooth simulado, calendario, bandeja y toast simulado) y se borraron. La captura detectó un fondo SVG transparente en el toast aislado: faltaba importar PlasmaCore para inicializar su ImageSet, corregido y verificado. Notifications y StatusNotifierWatcher conservan los mismos dueños D-Bus antes y después de las pruebas; se mantiene Retro y los diez PID de ventanas comprobados. La configuración real del shell recargó con sus avisos anteriores, sin errores nuevos de estos módulos. No se hizo un cambio real a Breeze ni un reinicio de mantenimiento: al cargar los nuevos Loader se recomienda set plasma --restart-shell.

### 144. Fase 6a de Breeze: auxiliar de decoraciones de KDE `bwm-decorator` (2026-11-11)
* **Petición:** fase 6a de `docs/BREEZE_PLAN.md`: un proceso que dibuje las decoraciones reales de KDE para el plugin de Hyprland, probado sin Hyprland.
* **Hecho:** `src/bwm-decorator` (C++20, Qt 6, KDecoration3; `Makefile` con `make install` atómico a `~/.local/share/bwm/bin/bwm-decorator`). Sigue kwin v6.7.5: `Bridge` (plugin y tema de `kwinrc [org.kde.kdecoration2]`, recarga, Aurorae SVG con el motor v2 como `migrateAuroraeTheme`), `Settings` (`ButtonsOnLeft/Right` con las letras de KWin, `BorderSize`/`BorderSizeAuto` con el tamaño recomendado del plugin, `CloseOnDoubleClickOnMenu`, fuente `[WM] activeFont`), `palette.cpp` = `decorationpalette.cpp` de KWin (GPL-2.0-or-later) sin cambios de lógica, `ClientImpl` (estado de la ventana y peticiones) y `Window` (confirma `apply(nextState())`, dibuja las cuatro piezas del marco a la escala del monitor en dos memfd alternos y envía la sombra aparte). Iconos por id del `.desktop` o `StartupWMClass`. Recarga en vivo con KConfigWatcher, el archivo y `KGlobalSettings.notifyChange`. Protocolo binario versionado sobre `SOCK_SEQPACKET` (`PROTOCOL.md`, `protocol.h`): ventanas, estado, puntero, geometría, marcos, sombra, peticiones y sección bajo el puntero; varias ventanas y clientes a la vez. Supervisor `skins/plasma/scripts/decorator.py` (`start` con `bwm_session.spawn()` al entrar en Breeze y al iniciar sesión, `run` lo relanza si cae, `stop` al salir de Breeze, `build`, `status`); candado por socket (segunda instancia: código 3). Declarado en `requirements.json` (tipo build) y en Breeze.
* **Encontrado:** la paleta de KWin lee la configuración principal del proceso (que incluye `kdeglobals` en cascada) y la refresca con `sync()`, que no relee el archivo; en KWin lo relee su KConfigWatcher. Aquí se relee antes de actualizar, o un cambio de esquema repintaba con los colores viejos. La ruta de un socket Unix no puede pasar de 108 caracteres (las pruebas usan un directorio corto en `$XDG_RUNTIME_DIR`).
* **Comprobado:** `tests/test_bwm_decorator.py` (9 pruebas, compila el auxiliar, configuración aislada, cliente `tests/bwm_decorator_client.py`): Breeze oscuro y claro, cambio a claro en vivo al reemplazar `kdeglobals`, botones de `kwinrc` (`XIA` a la izquierda), hover sobre cerrar (se dibuja distinto) con tooltip, clic → `close` y `toggleMaximization` con el botón izquierdo, escala 1,5 (1200 px de ancho, barra de 42 px), dos ventanas activa/inactiva, sombra, destruir una, el auxiliar no cae; supervisor que relanza tras una caída y no hace nada fuera de Breeze. Con `BWM_TEST_AURORAE_DIR` apuntando a los temas Sweet descargados en F1, el tema Aurorae Sweet-Dark se dibuja (plugin `org.kde.kwin.aurorae`). Imágenes revisadas y borradas. Candado: la segunda instancia sale con 3. `decorator.py build` instaló el binario; `status` correcto.
* **No probado:** con Hyprland (lo conecta F6b), decoraciones C++ de terceros (Klassy…), HiDPI real con monitores de escala distinta, el relanzado automático en la sesión real y el rendimiento al redimensionar (cada marco se dibuja entero en ~1 ms).

---

### 145. Fase 6b de Breeze: el plugin `breezebars` compone las decoraciones de KDE (2026-11-11)
* **Petición:** fase 6b de `docs/BREEZE_PLAN.md`: barras de título idénticas a KWin con el tema activo, dibujadas por `bwm-decorator`, con el plugin como pegamento.
* **Movido:** `src/hyprbars` → `src/breezebars`; se instala como `config/hypr/plugins/breezebars.so` (sigue registrándose como `breezebars`). Requisito `hyprbars-plasma` → `breezebars` en `requirements.json`, `skin.json`, `install.sh`, `autostart.sh` y documentos; `hyprbars-plasma.so` fuera del repo. `src/omarchy-titlebars` no se toca.
* **Plugin (detalle en `src/breezebars/README.md`):** `DecoClient` (socket no bloqueante en el bucle de eventos de Wayland, `MSG_DONTWAIT`, reintentos y `decorator.py start` como mucho cada 15 s si no hay auxiliar), `barRemote` (estado por ventana enviado sólo si cambia; bordes reservados en los cuatro lados con `DECORATION_POSITION_ABSOLUTE`; textura copiada al recibir y subida sólo en lo dañado; la última imagen se estira mientras llega la nueva; contorno del tema; sombra de nueve trozos como KWin en la decoración aparte `CBreezeShadow`; redondeo del contenido = radio inferior de la decoración con la prioridad más baja). Puntero como KWin: la decoración recibe pulsar/soltar/rueda sin aceptar y lo no aceptado es del compositor (mover con el snapping de siempre, redimensionar desde la sección del borde con `beginDragTarget` y esquina forzada, doble clic `on_double_click`, rueda `on_wheel`, botón derecho = menú). Peticiones: cerrar, maximizar por ejes (izquierdo ambos, central vertical, derecho horizontal), minimizar con `toggle-minimize.py`, menú de la ventana por IPC `plasmaWindowMenu open <dirección> <x> <y>` (aún no existe: F9), tooltip con `[Colors:Tooltip]` de `kdeglobals`, fijar. Sin auxiliar: la barra plana de siempre. `hyprctl hyprbars-csd` dice el estado de la conexión y si cada barra es `kde` o `plana`.
* **Auxiliar y protocolo:** nuevo mensaje `PointerResult` (110: aceptado y sección bajo el puntero tras pulsar, soltar o rueda) y radios del contorno al final de `Geometry`. El puente F2 exporta `CommandTitlebarWheel` y `kwin.lua` lo pasa a `plugin:breezebars:on_wheel`.
* **Comprobado:** plugin compilado con `-fno-gnu-unique` sin errores (sólo el aviso previo de `addConfigKeyword`), sin símbolos sin resolver contra Hyprland 0.56.2, instalado con `make install`; `bwm check --skin plasma` lo da por bueno. `tests/test_breezebars.py`: lógica del plugin sin Hyprland (secciones, piezas, daños a escala 1,5, sombra con esquinas solapadas, rueda, ejes, colores, mensajes truncados o falsos) y el código C++ del plugin hablando con el auxiliar real (estado, imagen, sombra, pulsación en la barra → sección 9 sin aceptar, rueda, cambio de tamaño). Prueba nueva del auxiliar con `PointerResult` (barra 9, botón aceptado, franja inferior 7). 286 pruebas OK; `Hyprland --verify-config` correcto, `configerrors` vacío.
* **No probado:** nada dentro de Hyprland. El plugin no se carga en caliente (regla 1) y la sesión está en Retro: hay que volver a iniciar sesión en Breeze. Límites conocidos: el redimensionado desde un borde lateral usa el de Hyprland por esquina (un borde sólo mueve un eje si el ratón sólo se mueve en ese eje); el intervalo de doble clic es fijo (400 ms), no `DoubleClickInterval`; el menú de la ventana espera a F9; el tooltip lo dibuja el plugin (no el estilo de Qt).

### 146. Fase 7 de Breeze: negociación CSD/SSD y marco único (2026-11-11)

* **Fuentes:** KWin v6.7.5 (xdgshellwindow, xdgdecoration_v1, server_decoration, x11window) y Hyprland 0.56.2 `efb50993780079460b0cbed1363e2166a2de1d9f` (XDGDecoration/ServerDecorationKDE/XDGShell). Hyprland respondía Server a Client; el detector antiguo miraba la petición y podía ocultar la única barra. Se reescribe la política de forma propia, sin copiar C++ de KWin; procedencia en README/THIRD_PARTY_NOTICES.
* **Plugin:** CSDLogic puro y CSDDetect integran callbacks de creación y peticiones, ack+commit xdg (primer configure tras commit vacío), KDE antiguo None/Client/Server sin límite de cuatro peticiones y prioridad xdg si hay ambos. Hooks sobre setters generados verificados en símbolos y llamadas del binario; falla la inicialización si no se pueden instalar. Política original fuera de Breeze. XCB independiente/asíncrono, PropertyNotify y cache por ventana/PID; sin esperar respuestas en render/IPC. Motif decorations=0 o GTK_FRAME_EXTENTS válido → CSD; por requisito cuenta también GTK con ceros (KWin comprueba valores no nulos). Sin protocolo Wayland → CSD; sin preferencia → SSD. Reacciona a cambios/destrucción de protocolos y overrides, fullscreen sin marco. no_bar=false devuelve el automático; no fuerza barra sobre CSD. F10 traducirá NoBorder.
* **Marco compartido:** JSON API 1 `hyprctl -j breezebars-csd`, alias hyprbars-csd, y Lua `hl.plugin.breezebars.decoration(address,pid)`: petición, respuesta, aplicado, motivos, pendiente, visibilidad y cuatro bordes reales (F6). bwm_windows usa dirección+PID, traditional_box/quick-tile/placement cuentan el marco real y no 30 px por defecto; placement reintenta brevemente el estado inicial pendiente. quick-tile comprueba PID otra vez al mover para no actuar sobre una dirección reutilizada. Nombre propio Breezebar para no confundirlo con las barras de Omarchy. Ninguna lista de clases decide CSD.
* **Auditoría:** `skins/plasma/scripts/csd-audit.py` de sólo lectura, declarado en parts, genera tabla sin títulos; distingue datos OK de inspección visual y apps no observadas de probadas. Pruebas de política, seriales/ack/commit, hints, cambios KDE repetidos, ABI, identidad y cuatro bordes. No hay requisitos nuevos: Python/hyprctl/XCB ya usados y libdl del sistema. No se toca Retro ni bwm/user.
* **Comprobado:** 297 pruebas generales, 53 opcionales omitidas, y nueve específicas CSD/auditoría pasan; compilación con -fno-gnu-unique e instalación atómica mediante make install, Python/Lua válidos, Hyprland --verify-config correcto, configerrors vacío, bwm check --skin plasma correcto. Log de Quickshell existente con avisos previos de Lock.qml (pantalla nula), sin cambios QML de F7.
* **Estado:** plugin F7 compilado e instalado. No se carga/descarga el plugin en caliente. La sesión continúa en Retro; la tabla de apps reales sigue pendiente de reiniciar entrando en Breeze en `docs/BREEZE_CSD_RESULTS.md`. Sin capturas. Arquitectura §12; no elevar compatibilidad por pruebas simuladas.

### 146. Fase 8 de Breeze: minimizar, maximizar y restaurar como KWin (2026-11-11)
* **Petición:** fase 8 de `docs/BREEZE_PLAN.md`: la semántica de KWin para minimizar, maximizar y restaurar, en un solo sitio, usado por el panel, el plugin, Alt+Tab y Alt+Enter.
* **KWin v6.7.5 leído** (código local de `distfiles`): `XdgToplevelWindow::maximize` (`src/xdgshellwindow.cpp`): modo con dos ejes; el marco ocupa el área útil en los ejes maximizados; `geometryRestore` sólo se actualiza en los ejes que no estaban maximizados y no se toca desde un mosaico rápido; al dejar un eje se vuelve a su tamaño y centro; maximizar sale del mosaico. Botón de maximizar: izquierdo completo, central `^ Vertical`, derecho `^ Horizontal`. Atajos de `src/useractions.cpp`: Meta+RePág maximizar, Meta+AvPág minimizar, Meta+D vistazo al escritorio, Alt+F4 cerrar, Alt+F3 menú (F9), Meta+Retroceso restaurar (no se usa: en BWM es la transparencia, común).
* **Hecho:** `skins/plasma/scripts/kwin-window.py` (`maximize --mode toggle|full|vertical|horizontal|restore`, `minimize`, `unminimize`, `activate`, `toggle-minimize`, `show-desktop [leave]`, `state`). Cuentas con el marco (barra de la decoración dentro del área útil, panel visible). El modo vive en etiquetas que lee el plugin (`bwm-max-v`, `bwm-max-h`, `bwm-maximized`; regla `plasma-kwin-maximized-square` de redondeo cero) y la restauración en `$XDG_RUNTIME_DIR/bwm-kwin-windows.json` por dirección y PID. Desde un mosaico rápido, la restauración es el tamaño de antes del mosaico (`quick-tile.py`). Minimizar, restaurar y «Mostrar escritorio» llaman a las funciones de `toggle-minimize.py`: formato común (`special:minimized`, `omarchy-minimized-from-<n>`) sin cambios. Conectado: botones y doble clic/rueda del plugin (los flags de maximizado de la decoración salen de las etiquetas; arrastrar una ventana maximizada la restaura, como el mosaico), acciones de `kwin.lua`, tareas del panel, menú de tareas, «Mostrar escritorio», Alt+Tab en Breeze. Atajos de Breeze en `keybinds.json` con `"skins": ["plasma"]` (Alt+Intro, Meta+RePág, Meta+AvPág, Meta+D, Alt+F4) y `keybinds-manager.py` admite `"skins_except"` (el Alt+Intro común ya no existe en Breeze).
* **No hecho:** animación de minimizar hacia el icono del panel: Hyprland no tiene una animación por ventana hacia un punto (sólo la del workspace especial). Restaurar con Meta+Retroceso.
* **Comprobado:** 11 pruebas del cálculo (`tests/test_kwin_window.py`). En la sesión real (Retro), dos kitty de prueba en los workspaces 9 (MSI) y 8 (LG, reglas temporales): maximizar = área útil exacta con las tres etiquetas, restaurar a la geometría exacta, vertical, vertical+horizontal = completo, sólo horizontal, restaurar, minimizar a `special:minimized` con `omarchy-minimized-from-<n>` y volver a su workspace con la geometría exacta; en los dos monitores. Workspaces visibles y foco devueltos, reglas retiradas con `hyprctl reload`. Plugin recompilado e instalado con `make install`; 297 pruebas OK, `configerrors` vacío.
* **No probado:** en Breeze con decoración (bordes reales, botones del plugin, doble clic, arrastrar una maximizada), «Mostrar escritorio» real (minimizaría tus ventanas), Alt+Tab y panel con clic, la regla de redondeo; el plugin nuevo se carga al volver a iniciar sesión en Breeze.

### 147. Fase 9 de Breeze: menús contextuales de Plasma (2026-11-11)
* **Petición:** fase 9 de `docs/BREEZE_PLAN.md`: los mismos menús contextuales que Plasma, con su estilo: ventana (KWin), gestor de tareas, escritorio y panel.
* **Leído en las fuentes 6.7.5** (kwin y plasma-workspace de `distfiles`, plasma-desktop bajado de download.kde.org): `UserActionsMenu::init()` y sus submenús de escritorios/pantallas, `applets/taskmanager/qml/ContextMenu.qml`, `containmentactions/contextmenu/menu.cpp` (orden y acciones de escritorio y panel).
* **Hecho:** `modules/plasma/menus/` (README): `MenuHost` (capa a pantalla completa en la pantalla donde se abre; IPC `plasmaWindowMenu open <dirección> <x> <y>` que ya usaba breezebars, y `plasmaMenus inspect`), `WindowMenu`, `TaskMenu` (recientes de `recently-used.xbel` con `skins/plasma/scripts/task-recents.py`, acciones del .desktop, multimedia, mover al escritorio, anclar, Más, modo de edición, cerrar), `DesktopMenu` + `DesktopCatcher` (capa transparente en `bottom` que recoge el botón derecho sobre el fondo), `PanelMenu` (añadir elementos → editor del panel, modo de edición). PC3.Menu con el tema de Plasma (QMenu no abre desde layer-shell). Sustituye a `modules/ii/plasmaTaskMenu` (borrado, y sus `GlobalStates`). Acciones de ventana en `kwin-window.py` (nuevas: `menu`, `interactive move|resize`, `fullscreen`, `no-border`, `no-capture`, `pin`, `to-desktop`, `to-screen`, `rules`, `close`). breezebars: `hyprctl breezebars-interactive move|resize <dirección>` (la ventana sigue al puntero hasta el siguiente clic, como KWin) y la etiqueta `bwm-no-border` quita la barra; regla `plasma-kwin-no-capture` (`no_screen_share`). Alt+F3 en Breeze. Catálogo de traducciones propio `bwm_plasma_menus` (94 idiomas) con las cadenas originales recortadas (`po/extract.py`). Requisitos recomendados nuevos: `gio`, `xdg-open`.
* **No hay en Hyprland/BWM:** mantener encima/debajo (desactivados), atajo de ventana, actividades, lugares, enrollar, «Mostrar alternativas…» (ningún elemento de BWM tiene alternativas). «Configurar ajustes especiales…» espera al editor de reglas de F10 (por ahora `kcmshell6 kcm_kwinrules`).
* **Comprobado:** `tests/test_plasma_menus_ui.py` (5 pruebas, `qs -p` aparte con una kitty de prueba en el workspace 9): estructura y orden de los cuatro menús, dentro de la pantalla, en español, y «Maximizar» desde el menú de la ventana. Acciones reales con otra kitty de prueba: sin barra, ocultar de capturas (`getprop no_screen_share` = true), mover al escritorio 8, a la pantalla LG y de vuelta, fijar/quitar, cerrar; workspaces y foco devueltos. Captura recortada del menú de la ventana con el estilo de Plasma (borrada). Tu shell (Retro) recargó sin errores. Plugin compilado e instalado con `make install`.
* **No probado:** dentro de Breeze: botón derecho en la barra de título y en el botón de menú (necesita el plugin nuevo: volver a iniciar sesión), clic real en tareas, panel y escritorio, Mover/Redimensionar interactivos, y el editor de elementos al pedir «Añadir o gestionar elementos gráficos…».

### 148. Fase 10 de Breeze: reglas de KWin y encaje (2026-11-11)

* **Fuentes:** KWin v6.7.5 desde distfiles: rules.cpp/h, rulesettings.kcfg, rulebooksettings*, KCM de reglas, workspace.cpp, window.cpp, tiles/{quicktile,customtile,tile,tilemanager}, tileseditor y qml/outline/plasma/outline.qml. Adaptadores propios Python/Lua y geometría C++ independiente; port del outline con sus avisos y licencia. Sin Qt dentro de Hyprland.
* **Reglas:** kwin_rules.py, generado kwinrules.lua y loader de la skin. El mismo puente F2 observa kwinrulesrc y aplica estados; orden por propiedad, DontAffect, Apply/Force/Remember. Marca de mapa inicial para no recolocar ventanas existentes al volver a Breeze; dirección+PID y guarda contra órdenes tardías tras cambiar de skin. Remember al cerrar/salir con escritura atómica y conservación de texto ajeno/conflictos. Reglas nativas antes del Lua del usuario; opt-out bwm-ignore-kwin-rules para seguimiento forzado. Diagnóstico de omisiones. Rol/tipo desde metadata nativa del plugin; sin WM_CLASS completo/clientmachine ni todos los tipos Wayland, Above/Below, ApplyNow/ForceTemporarily o actividades. Limitaciones completas en scripts/KWIN_RULES.md y arquitectura §13.
* **Separación:** flotación/estados visuales de Breeze pasan de modules/rules.lua a skins/plasma/hypr/rules.lua; appearance carga rules/kwinrules antes de placement y de bwm/user. KCM original kcm_kwinrules con kcmshell6: carga sin KWin; detección y preselección por D-Bus KWin no funcionan. Catálogo/recomendaciones y REQUIREMENTS actualizados, paquetes ya instalados. No se ejecuta KWin ni otro servicio KDE.
* **Encaje:** KWinSnap.hpp sustituye SnapHelper.hpp; SnapGeometry.hpp puro. Border/Window/CenterSnapZone, SnapOnlyWhenOverlapping, ElectricBorderTiling/Maximize/CornerRatio. Imanes por marco real, mitades/cuartos y arriba maximizado F8; se aplica el rectángulo mostrado y el monitor de esa previsualización con PID, workspace antes de geometría. Vecinas encajadas comparten redimensión de borde con límites nativos; no se guardan proporciones del grupo. Ctrl+flechas conservado por decisión expresa del usuario. quick-tile deja de borrar etiquetas ajenas.
* **Mosaico/outline:** kwin_tiles.py lee/escribe JSON original en kwinrc [Tiling][desktop UUID][output UUID], padding de KWin; asociación de UUID de KWin a descripción de monitor en estado de máquina (sin DP-N). Mayús+arrastre elige hojas. Meta+T abre editor reducido (dividir/unir/repartir/separación), sin el efecto original ni arrastre libre de divisores. Outline KSvg del tema activo sustituye el GL azul; Loader sólo Breeze y sin entrada. README y licencias. autostart genera archivos antes de la recarga inicial del plugin; fuera el override CSD antiguo por clases. No se toca el plugin de Retro ni archivos bwm/user.
* **Validación:** 339 pruebas generales correctas (60 opcionales omitidas); dos pruebas QML F10 activadas pasan, incluidas órdenes IPC antiguas del outline descartadas por secuencia (método display para evitar show, reservado por el CLI). Plugin compilado con -fno-gnu-unique e instalado con make install, fuente/binario coinciden. Parser real de Hyprland acepta las reglas generadas; configuración actual válida, configerrors vacío y bwm check correcto. qmllint con avisos de metadatos/imports, complementado con carga real. Pruebas de orden/modos, conflictos y PID, geometría/reservas, imanes, vecinos y formato original de mosaico; carga QML aparte (incluidos delegados y lectura real de tres zonas), KCM con XDG temporal en workspace 9 y sin guardar. Sin capturas. La sesión permanece en Retro y el plugin nuevo sólo se valida tras reiniciar: lista en docs/BREEZE_F10_CHECKLIST.md. Compatibilidad no aumentada por simulaciones.

### 149. Comprobaciones previas al reinicio de Breeze y errores de QML (2026-11-11)

* **Sesión observada:** skin plasma activa, Loader/IPC de menús, mosaico y outline presentes, requisitos correctos y configerrors vacío; Hyprland sigue siendo el proceso de la sesión anterior (iniciado el 2026-11-10), sin plugins cargados. Cambiar de skin no validó el plugin F6–F10: sigue haciendo falta volver a iniciar sesión. El usuario autoriza que BWM cierre la sesión para ello; la autenticación en SDDM la hace el usuario.
* **Errores encontrados/corregidos:** PanelState.anchor usaba GlobalStates sin importar qs; añadido el import. La etiqueta de bandeja vacía evaluaba length antes de inicializar hiddenItems/hiddenApplets; protegida esa transición. Prueba qs -p aislada sin ventana visible: anclaje real de un Item (ANCHOR_OK) y TrayPopup con listas aún no disponibles, sin ReferenceError/TypeError. Ocho pruebas de panel y cuatro de bandeja pasan (11 QML opcionales omitidas). Sin tocar la configuración en texto del usuario, sin capturas y sin cargar el plugin en caliente.
* **Pendiente:** comprobar el arranque con el plugin y después las acciones con ratón de docs/BREEZE_F10_CHECKLIST.md. El diagnóstico de requisitos sólo valida instalación/compatibilidad, no que el plugin esté cargado.

### 150. Caída al iniciar Breeze: referencia de la sombra a una barra de propietario único (2026-11-11)

* **Incidente real:** tras el cierre autorizado, Hyprland cae dos veces al mapear una ventana con breezebars cargado (informes locales hyprlandCrashReport77911.txt y hyprlandCrashReport782833.txt). Ambos abortos señalan CBreezeShadow::getPositioningInfo+0x1a5. SDDM autentica y lanza la sesión correctamente en el registro consultado; estos informes no prueban un fallo de SDDM. El usuario recupera el escritorio desde tty3 con start-hyprland.
* **Causa/corrección:** Hyprland posee CHyprBar con CUniquePointer; la sombra guardaba CWeakPointer e intentaba lock(), que aborta deliberadamente en Hyprutils para propietarios únicos. Sustituidas las cuatro conversiones en posicionamiento, caja, dibujo y render de CBreezeShadow por referencias débiles comprobadas, como la lista global de barras; no se cambia la propiedad ni se usa un puntero sin comprobación. Las referencias a ventanas/monitores de propietario compartido conservan lock().
* **Validación:** nueva prueba ejecuta el método real de posicionamiento con los tipos de memoria reales de Hyprutils: sin auxiliar, marco/sombra disponibles y barra destruida. Con el código anterior reproduce SIGABRT y el mensaje «tried to lock a CWeakPointer over a CUniquePointer»; con el corregido pasa. Las cuatro pruebas de test_breezebars.py pasan (protocolo, auxiliar real, compilación/símbolos y regresión). Compilado con -fno-gnu-unique, sin símbolos UNIQUE, instalado únicamente con make install; SHA256 fuente/binario instalado 60db26a97493418235136474c1d6b0aed74203f472b65444375f3058c0f55ffa.
* **Estado y límites:** se observan dos Hyprland vivos, ambos con --safe-mode y sin plugins: uno lanzado por SDDM en tty1 y el recuperado en tty3. Esto explica la configuración incompleta; no se cierran ni se sale del modo seguro automáticamente. No se ha cargado/descargado el plugin en caliente. El diagnóstico de un solo uso alcanzó a ver el plugin antes de que hubiera ventanas y luego se produjo el aborto: no cuenta como validación de arranque. El nuevo binario queda preparado para el siguiente inicio; arranque completo, acciones con ratón y resto de F10 siguen pendientes. Ningún cambio en SDDM, /boot o configuración en texto del usuario.

* **Traspaso a Claude solicitado por el usuario:** estado operativo, archivos sin commit, pruebas y siguiente paso en `docs/BREEZE_F10_HANDOFF.md`.

### 151. Arreglo de la sombra validado en un Hyprland anidado, sin tocar la sesión recuperada (2026-11-11)

* **Petición:** continuar F10 desde `docs/BREEZE_F10_HANDOFF.md`, preservando la sesión recuperada: sin cerrar sesión ni cargar el plugin en caliente en ella.
* **Comprobado antes:** siguen dos Hyprland 0.56.2 en modo seguro y sin plugins (tty1 de SDDM y tty3 recuperado); el binario instalado y el compilado coinciden (SHA256 `60db26a9…`). Revisadas las demás llamadas `lock()` del plugin: sólo quedan sobre ventanas, superficies y recursos (propietario compartido); ninguna sobre `CHyprBar`.
* **Prueba anidada:** esta vez un Hyprland anidado sí arranca dentro de la sesión (wayland-3) con el `XDG_RUNTIME_DIR` normal. Configuración de prueba en el scratchpad con `modules/rules`, `app_rules` y `appearance` reales (skin plasma: `kwin.lua`, `kwinrules.lua`, `placement.lua`), sin autostart, binds ni Quickshell; un `bwm-decorator` propio en `$XDG_RUNTIME_DIR/bwm-f10-nested.sock` (`BWM_DECORATOR_SOCKET`). El plugin instalado se cargó **sólo en esa instancia desechable**. Mientras su ventana está en un workspace oculto no dibuja y el plugin no llega a conectarse al auxiliar: se mostró unos segundos en una esquina del LG (workspace 10), sin cambiar foco ni workspaces.
* **Resultado con el arreglo:** dos kitty y pavucontrol con la decoración Breeze real (`kde`; botones menú, fijar, minimizar, maximizar, cerrar; título centrado), colocación «mínimo solapamiento», maximizar/restaurar por `kwin-window.py` (etiquetas y geometría de F8), cerrar una ventana, `hyprctl reload` sin errores, encaje a mitades con `quick-tile.py`, minimizar/restaurar, «sin barra», y caída/vuelta del auxiliar (barra plana y de nuevo `kde`). Sin ninguna caída; salida 0 al cerrar.
* **Reproducción:** la versión anterior de `barRemote.cpp` (HEAD) compilada aparte en el scratchpad, sin instalar, y cargada en otro Hyprland anidado aborta al mapear la primera kitty con el mismo marco `CBreezeShadow::getPositioningInfo+0x1a5` que los dos informes del arranque. Informe de esa prueba borrado; copia y capturas también.
* **Observado, sin investigar:** pavucontrol (GTK 4) negocia la decoración KDE `server-side` y su contenido queda recortado por la derecha a 500 y a 800 px de ancho. Revisar en la sesión real si pasa también sin el plugin.
* **No probado:** el arranque normal completo (dos monitores, puente F2, Quickshell, autostart) y todo lo de ratón de `docs/BREEZE_F10_CHECKLIST.md`. La sesión recuperada sigue en modo seguro: hace falta que el usuario vuelva a iniciar sesión (o reinicie) por su cuenta.

### 155. F11: aplicación de KCM, descargas KNewStuff y sonido (2026-11-11)

* **Petición:** ejecutar las pruebas que Claude dejó pendientes de F11. Informe y límites en `docs/BREEZE_F11_CHECKS.md`.
* **Comprobado:** copias temporales de plasmaSettings.qml con ModuleView/KcmPage/KcmHost reales, qs -p en workspace 9 sin foco, XDG temporal (sin cambiar HOME), Config.blockWrites y D-Bus privado para apariencia. KCM de iconos (breeze-dark), fuentes (Noto Sans 12), decoración (borde Large no automático), estilo Qt (Breeze/Fusion), estilo de Plasma (breeze-light) y tema global (Breeze Dark, sólo piezas de apariencia seleccionadas) aplican y guardan los archivos KDE esperados. El tema global escribe también kdedefaults, como KDE; no basta con buscar las claves explícitas de kdeglobals.
* **KNewStuff:** acciones originales de los KCM abren diálogos válidos de iconos, decoraciones, estilo de Plasma y tema global; descarga real desde el KCM de colores de Sweet Dark Blu (1689224), y desde el de estilo de Plasma de Sweet KDE (1294174), a XDG_DATA_HOME temporal con sus registros KNewStuff. Sin instalar recursos en el repo ni en los datos personales. Avisos upstream de transientParent/OverlayDrawer al construir los diálogos, sin impedir esas descargas; no se ocultan en el informe.
* **Sonido:** KCM real y su SinkModel sobre PipeWire/PulseAudio real; salida virtual temporal bwm_f11_check, seleccionada únicamente por nombre exacto. Volumen al 50 % y silencio comprobados externamente con pactl. Volúmenes/silencio físicos y dispositivos predeterminados intactos; salida eliminada y estado completo restaurado. Es un KCM de aplicación inmediata, sin save()/Aplicar.
* **Limpieza/límites:** archivos KDE reales iguales byte a byte a sus copias iniciales; sondas borradas, regla temporal retirada, configerrors vacío. Tres pruebas de catálogo pasan (dos pruebas generales opcionales omitidas); sin cambios de código de producto ni suite completa repetida, sin capturas ni reinicios. Esto prueba aplicación/persistencia en configuración aislada y sonido real sobre dispositivo de prueba, no propagación en vivo de toda la apariencia ni pulsación física de Super+I. F11 §154 conserva sus pruebas reales de colores y sus restantes límites.

### 156. F12: cambiador, OSD, bloqueo, KRunner y polkit de Plasma (2026-11-11)

* **Implementación:** modules/plasma/{switcher,osd,lock,runtime}. Rejilla de miniaturas portada de KWin 6.7.5, conservando el controlador MRU común (snapshot propio, pendingSteps, releasedEarly, foco al soltar Alt); borrado PlasmaSwitcher.qml antiguo. OsdItem original de plasma-workspace, con capa sin entrada, SVG, Audio/Brightness y timeout comunes, y aviso agrupado del gestor de pantallas/IPC plasmaOsd. Se deja la lógica común y no se modifica el plugin C++ de Hyprland.
* **Bloqueo:** el paquete Breeze 6.7.5 comprobado no tiene contents/lockscreen; se portan controles del Greeter de KScreenLocker 6.7.5 y se usan Clock, SessionManagementScreen/avatar y ActionButton reales de Breeze. Sustituye plasmaLock. LockContext conserva PAM, huella y desbloqueo; el adaptador sólo ofrece operaciones de autenticación, no el contexto completo al tema. Un error de carga conserva el formulario de reserva. Se corrigieron dos problemas durante las pruebas: referencia remanente a PasswordSync y solapamiento reloj/avatar; la captura del propio elemento fue revisada y borrada.
* **Temas globales:** interface-theme.py lee LayoutName/LookAndFeelPackage con prioridad KDE/kdedefaults; respeta rutas XDG de paquetes. Adapta QML y recursos en una caché atómica, sin tocar el tema instalado. ThemeHost (org.bwm.kcm API 2) aloja QML original en motores separados: Qt.quit del tema no sale de Quickshell ni desbloquea. Shim de TabBoxSwitcher/WindowThumbnail/Dialog para los cambiadores; fuentes lockscreen y osd del tema global si existen. No se emulan todas las APIs privadas de KWin/KScreenLocker. Código fuente, avisos y límites en README y BREEZE_ARCH §14.
* **KRunner/atajo:** el original instalado con Milou carga y acepta consulta calculator 1+1 sin plasmashell, con plataforma offscreen/bus privado, sin ejecutar resultados. Alt+Espacio estaba ocupado: el usuario autorizó KRunner sólo en Breeze; registro skins=[plasma] mediante keybinds-manager y binding anterior limitado a default/Retro. Requisitos declarados (incluido KI18n y API 2 de bwm-kcmhost), tabla regenerada; no hizo falta instalar paquetes.
* **Polkit:** manifiesto Breeze selecciona polkit-kde-agent; bwm_polkit comprueba la skin activa, retira sólo agentes externos conocidos de otra skin, espera su salida y serializa/reintenta el arranque inicial. Desbloquea señales heredadas al lanzar el agente. BWM no registra su agente en Breeze y Retro conserva Omarchy. La sesión actual está en Retro: un intento de iniciar KDE fue rechazado porque Omarchy ya posee el registro; no hubo sustitución. Se añadió guarda contra hooks de una skin ya abandonada. No se ejecutó ninguna operación privilegiada.
* **Pruebas:** ocho pruebas F12 activadas pasan, incluidas UI con contextos simulados, Qt.quit interceptado, Alt+Tab acumulado/rápido/sostenido sin foco real, prioridad/paquetes/caché, guarda y reintento serial de polkit. El QML original completo de thumbnail_grid carga con el adaptador. Suite general final: 358 pruebas correctas, 65 opcionales omitidas. qmllint ejecutado (avisos de imports/metadatos dinámicos, complementados con carga real). Módulo Qt compilado e instalado atómicamente; requisitos y configuración comprobados. Sin reinicio del shell/sesión y sin plugin unload/load.
* **Pendiente real:** hace falta reinicio de mantenimiento del shell para Loader/módulo nuevos; prueba física de Alt+Tab/miniaturas y OSD, PAM/huella/bloqueo real, autenticación polkit KDE al entrar en Breeze y temas externos adicionales. Las pruebas simuladas no certifican estos puntos. Se mantiene Ctrl+flechas y la configuración protegida del usuario.

### 157. F12 cargada: conflicto de bandeja y resolución del OSD (2026-11-11)

* **Causa comprobada:** kded6 conservaba `org.kde.StatusNotifierWatcher` sin el objeto `/StatusNotifierWatcher`, pese a tener sólo ktimezoned cargado. Quickshell no podía leer los elementos. El detector heredado usaba pidof y avisaba incluso de un kded6 inofensivo.
* **Corrección:** `scripts/bwm-shell-conflicts.py` consulta el PID dueño del nombre D-Bus, verifica ejecutable/usuario y comparte el diagnóstico con ConflictKiller y killDialog. Resolver vuelve a comprobar el dueño y envía SIGTERM sólo a ese PID; desaparecen los killall generales. Se conserva la detección de mako/dunst cuando realmente poseen Notifications.
* **Sesión:** retirado el kded6 con registro obsoleto. Quickshell recuperó la bandeja y devolvió el elemento de Steam. Activado otra vez kded6 por D-Bus: sólo ktimezoned, sin conflicto ni pérdida del dueño Quickshell. Polkit KDE registró correctamente su agente en esta sesión; no se probó ninguna autenticación privilegiada.
* **OSD:** importación local explícita de OsdItem, necesaria al cargar Osd.qml desde otro módulo. Reinicio de mantenimiento con el gestor en plasma, una única instancia de shell; desapareció «OsdItem is not a type» y la llamada IPC de texto al OSD respondió correctamente. No se cerró sesión ni se recargaron plugins.
* **Pruebas:** cuatro pruebas unitarias de propiedad D-Bus/resolución dirigida pasan. La carga real del shell confirma ausencia de errores del detector y disponibilidad de la bandeja/OSD. Siguen pendientes las pruebas físicas de F12 descritas en §156.

### 158. F13: limpieza, tema real y prueba de cambio de skins (2026-11-11)

* Retirados modules/ii/plasmaCommon, plasmaThemePicker y sus 152 iconos sin consumidores;
  rama antigua del OSD y paleta fija del cargador. DesktopState vive en el panel; Alt+T usa
  BWMenu. parts actualizado y regla de barra del salvapantallas movida a la skin con guarda.
  quick-tile/toggle-minimize se conservan porque default/Retro/controladores aún los usan.
* La prueba de cambios descubrió que kded registra servicios en cola independientemente de
  autoload (fuente frameworks/kded v6.29.0). Reparación limitada de la reserva rota de bandeja:
  objeto ausente, mismo PID/usuario y sólo ktimezoned/ningún módulo. Se conserva el diálogo
  para conflictos funcionales. Seis pruebas específicas pasan; no hay killall general.
* Una repetición detectó tres intercambios de posición por dwindle. El gestor ahora recuerda
  geometría libre tradicional antes de salir, en caché de sesión/skin (XDG_RUNTIME_DIR), y
  restaura el marco al volver sólo para dirección+PID+inicio, workspace y monitor coincidentes.
  Cambios de salida y modos especiales invalidan la entrada; no se toca configuración del usuario.
  Se preservan etiquetas ajenas al retirar estado BWM. Cinco regresiones nuevas pasan.
* Secuencia repetida default → Breeze → Retro → Breeze: diez ventanas con el mismo PID/inicio,
  cero saltos de workspace, siete flujos de audio intactos, una instancia ii, configerrors vacío
  y geometría final conservada. No se cerró sesión ni se cargaron/descargaron plugins.
* Sweet instalado desde Obtener nuevos del KCM real, con dependencias a rutas del usuario,
  y aplicado desde Preferencias mediante sonda (no clics físicos). Colores/SVG/candy-icons y
  Aurorae efectivos; imagen del auxiliar y recorte del panel revisados y borrados. Cursor
  miku 48 intacto aunque Sweet-cursors queda instalado. Configuración KDE anterior restaurada.
* La aplicación nativa expuso lecturas incompletas de kdedefaults: corregida la cascada en QML
  y Python. Pruebas de prioridad y cambio en vivo pasan. Suite final 371 pruebas, 65 omitidas;
  qmllint con avisos de metadatos/imports, verificación Hyprland correcta. Detalle, limitaciones
  de licencia y lista manual en docs/BREEZE_F13_RESULTS.md. Requisitos/docs actualizados;
  estimación conservadora ~50 % en SKINS y ambos README. No se declara equivalencia total.

### 159. Ajustes tras F13: selector anterior, panel, foco, fuentes y arrastre CSD (2026-11-11)

* **Rapidez:** Breeze → Retro tardaba ~7,7 s. decorator.py esperaba dentro de su manejador
  SIGTERM, reentrando en Popen.wait con su lock de waitpid tomado: agotaba 5 s aunque el
  auxiliar ya saliera. El manejador sólo señala y el bucle normal espera con plazo; se limpian
  señales bloqueadas heredadas. Stop medido ~0,07 s y cambio completo ~2,5–3 s (resta tematizar
  fondo/apps). Regresión específica y pruebas del supervisor pasan.
* **Selector pedido por el usuario:** restaurado el aspecto anterior de Alt+T, miniaturas y
  navegación en modules/plasma/skinPicker, con paleta PlasmaTheme actual y offsets del panel.
  Sólo se carga en Breeze; conserva IPC plasmaThemePicker. No se recupera plasmaCommon entero.
  Añadido qmldir explícito al tema; alias Local.Palette evita la colisión con Palette de QtQuick.
* **Panel:** PanelBackground elimina todos los bordes que tocan pantalla, como PanelView
  6.7.5 (incluidos laterales en panel completo, no sólo el borde inferior). Los flotantes siguen
  admitiendo la forma del SVG. Controles en el grupo Complementary y tamaños explícitos 32 px
  para Kickoff / 22 px para bandeja: iconos visibles con la paleta del panel. Se conservan widgets/tasks
  y sus prefijos originales. Recortes del selector/panel revisados y eliminados.
* **Tareas:** TasksModel usa focus de kwin-window.py con dirección+PID; la acción enfoca y eleva
  explícitamente, sin depender de las peticiones de activación del cliente. Nueva opción --pid
  impide operar sobre una dirección reutilizada; el foco Lua también comprueba el PID.
  Mapeadas 10/10 toplevels reales; activar ChatGPT comprobado, foco anterior restaurado.
* **Menús:** abrir el mismo applet alterna su estado; el grab incluye su panel para que un
  clic en el botón no lo cierre antes de procesar el toggle. Escape a nivel de aplicación y
  contenido enfocado. QtTest con el botón real del fixture y Escape cierra, sin cambiar audio/red.
* **Fuentes:** Noto Sans 10 para interfaz/menú/barra/títulos y Hack para monoespaciada, como
  fontssettings.kcfg de Plasma 6.7.5. Manifiesto y requisitos actualizados; ambas instaladas.
  Aplicado sólo a kdeglobals/perfil Breeze, sin tocar bwm/user ni perfiles de otras skins.
  Verificado Noto Sans 10 en Qt/Kirigami con QApplication+kde; Retro conserva JetBrains Mono NF.
* **Arrastre de ChatGPT y equivalentes:** es XWayland con Motif sin marco. Hyprland 0.56.2
  anuncia _NET_WM_MOVERESIZE pero handleClientMessage no lo procesa. CSDDetect escucha el
  mensaje estándar en el root X11 por su conexión XCB y pide movimiento al compositor sólo
  con botón izquierdo físicamente pulsado, ventana flotante mapeada bajo el puntero y fuera
  de fullscreen; cancela sólo su propio gesto. Sin listas de clases ni barra duplicada.
  Política pura probada; plugin compilado con -fno-gnu-unique e instalado con make install.
  **Pendiente reiniciar sesión para activar este cambio C++; no se hizo unload/load ni logout.**
* **Validación:** 374 pruebas generales, 65 opcionales omitidas, sin fallos; 15 pruebas QML de
  applets activadas, repetida la del toggle/Escape. Verificación de Hyprland, requisitos y logs.
  Más detalle en docs/BREEZE_PANEL_FIXES.md; las pruebas de CSD no sustituyen el arrastre físico.

### 160. Clic directo de tareas y medidas del panel de Breeze (2026-11-12)

* El usuario detectó que §3.159 no resolvía el clic: se había probado focus, no la entrada
  del icono. Reproducido con Task real en ListView: clic izquierdo 0, miniatura 1.
  MouseArea padre interfería con DragHandler hijo; sustituido por Item+TapHandler/HoverHandler
  como Plasma 6.7.5. Área sin botones para rueda, comprobada dentro del ListView.
* Marcos sin separación artificial de 2 px, sin margen en el eje corto del panel; geometría
  de iconos/tareas con las métricas normales estables de widgets/tasks (Task.qml/LayoutMetrics.js).
  SVG y estados originales conservados. Recorte real revisado y borrado; sin prometer paridad visual total.
* Prueba opcional test_plasma_task_input.py: centro, margen, central, derecho, rueda,
  arrastre sin activar y miniatura, en cuatro bordes. Mock sólo de captura/datos/acciones.
  Pasa con la corrección y falla con Task anterior (0 clics). Ocho pruebas de geometría y
  trece de acciones de ventanas pasan. Reinicio de mantenimiento del shell; sin cambio C++
  ni cierre de sesión. Suite general: 375 pruebas, 66 omitidas, sin fallos; la entrada QML
  opcional se ejecutó expresamente. Informe actualizado en docs/BREEZE_PANEL_FIXES.md.

### 161. Panel de Breeze: representaciones y medidas originales de Plasma (2026-11-12)

* El usuario pidió igualdad visual precisa. Clonadas y verificadas etiquetas v6.7.5 de
  plasma-desktop/plasma-workspace. KickoffButton, ShowDesktopButton y ExpanderArrow portan
  sus representaciones originales; las acciones se delegan al host/servicios BWM.
* DigitalClock conserva etiquetas, fuentes ajustables, estados y formato original (216
  líneas de disposición cotejadas iguales tras adaptar nombres). Se retira fuente fija
  pequeña/negrita. Configuración nativa en bar.plasma.clock y formato común conservado.
* PanelContent aplica fixedMargins por applet, límite spacingAtMinSize y smallSpacing;
  tareas llenan el área. Bandeja con AbstractItem también para applets, celdas/filas nativas,
  22/30 px por defecto y scaleIconsToFit/iconSpacing en bar.plasma.systemTray.
* Dependencia QML privada digitalclock declarada (ya instalada). Cuatro pruebas QML de
  reloj/medidas/controles pasan, quince de bandeja y tareas con eventos en cuatro bordes.
  Recortes reales revisados y eliminados. Shell reiniciado por el gestor, sin cerrar sesión.
* Referencia adjunta: fondo #202326 y panel 44 px coinciden. Logo y configuración regional
  distintos; no se afirma igualdad de todos los píxeles ni se eleva compatibilidad estimada.
  Límites y fuentes en docs/BREEZE_PANEL_FIXES.md y README de panel/tray. Suite general:
  379 pruebas, 70 opcionales omitidas, sin fallos; config/requirements correctos y una instancia ii.


### 162. Segundo plan de Breeze: fidelidad y correcciones del port (2026-11-12)

* **Petición:** nuevo plan con prompts y esfuerzo medium/high para modo edición original,
  opciones de temas/complementos, sombras, animaciones y ajustes KDE auténticos, auditoría
  profunda y arreglo de Magic/Alt+S y ventanas especiales que aparecen detrás de las normales.
* **Hecho:** `docs/BREEZE_PLAN_V2.md`, diez fases R0–R9 secuenciales con objetivos, rutas,
  pruebas de aceptación, dependencias y límites. Enlace desde el plan histórico F0–F13.
  Revisión inicial de código y documentación: editor reducido, animaciones MD3, Ajustes
  mediante `qs -p`, sombras KDE ya implementadas y ruta de activación de tareas sin tratamiento
  explícito de especiales. `systemsettings` existe; no se abrió ni se probó en esta sesión.
* **Comprobado:** estructura de los diez prompts, vallas Markdown y `git diff --check`.
  `AGENTS.md`/`CLAUDE.md` siguen idénticos. Sólo cambios documentales, sin commit ni push.
* **Pendiente:** toda la ejecución R0–R9. La causa de Alt+S sigue sin reproducir; se documenta
  como hipótesis, no se afirma que existan dos workspaces distintos ni que se haya corregido.
  No se cambiaron skins, configuración de usuario, procesos ni plugins.

### 163. Primera ejecución Breeze II: auditoría, especiales y prueba de KCM nativo (2026-11-12)

* **Petición:** ejecutar R0 y continuar autónomamente mientras el usuario descansa, dejando
  sudo/pruebas físicas/reinicio para mañana. No se promete haber consumido cinco horas.
* **Entorno:** IPC Hyprland/Wayland/D-Bus bloqueado por sandbox; systemsettings 6.7.5 y
  referencias locales desktop/workspace v6.7.5 confirmadas. No se pudo inspeccionar plugin vivo.
* **R0:** `docs/BREEZE_AUDIT_V2.md`, inventario priorizado y referencia reproducible. Identificados
  origen especial perdido al minimizar y veto global de sombras como causas de código; no se
  atribuye con certeza el síntoma Alt+S sin reproducirlo.
* **R1:** política común de activación, PID en foco diferido de Alt+Tab, Magic visible incluido,
  nombre especial conservado en etiqueta al minimizar y caché geométrica con identidad. Pruebas
  Lua/QtTest offscreen/Python pasan. Dock nativo opcional Retro y matriz de sesión siguen pendientes.
* **R2 parcial:** `src/bwm-systemsettings`, primer KCModule QWidget real de luz nocturna con
  controlador común, pruebas aisladas y detección por systemsettings real. Instalado sólo en
  `/tmp` para probar. Lanzador experimental `settings-native.sh`; Super+I sigue intacto hasta
  migrar las demás opciones BWM. Recomendación experimental declarada y requisitos regenerados.
* **R6 parcial adelantada:** quitado no_shadow=true de la regla global Breeze, manteniendo
  sombra genérica apagada y overrides de Sin marco. Regresión de Lua pasa; no cambia plugin.
* **Límites:** no se cambió skin, reinició shell/sesión, instaló con sudo ni tocó texto de usuario.
  No hay prueba visual ni equivalencia nueva. Resultados por fase y pasos para mañana en docs.
  Sin commit ni push. Las suites con sockets de decorador fallan por permisos del sandbox,
  no se presentan como aprobadas; resultado offline final en el informe de continuación.

### 164. Incidente de modo seguro tras Breeze II: contención (2026-11-12)

* Usuario comunica modo seguro. Informe reciente SIGSEGV en ScreenshareSession::init+0xad7,
  capturando una ventana; objdump confirma lectura nula 0x94 en cálculo de escala. No se
  demuestra causalidad con sombra/plugin ni se identificó ventana/cliente exactos.
* Restaurado no_shadow=true global de Breeze como contención, y captureSource:null/live:false
  en miniaturas TaskToolTip/ThumbnailGrid/compat WindowThumbnail. Sombras R6 siguen pendientes.
* No se reinició ni cerró sesión; IPC sigue bloqueado. Reentrada normal y verificación pendientes.
  Detalle en docs/BREEZE_RECOVERY.md; informes anteriores R6 quedan supersedidos.

### 165. Revisión R0–R2: estados parciales y captura en fallback oculto (2026-11-12)

* Repetidas 33 pruebas específicas y reconstrucción limpia de KCM/CTest; KDE descubre el módulo.
* R0 documental con referencia gráfica pendiente, R1 parcial y R2 sólo prototipo. No se cierran.
* Detectada y corregida captura del Alt+Tab común oculto en Breeze: ahora la fuente depende
  de panelWindow.visible, con prueba de binding en QtTest sin capturar ventanas reales.
* Restauración del dock Retro aún ignora el origen especial; integración/validación pendientes.
  No se cambió sesión ni archivos generados ajenos. Informe docs/BREEZE_R0_R1_R2_REVIEW.md.

### 166. R0 completada como auditoría sobre el trabajo existente (2026-11-12)

* Petición: hacer R0 aprovechando lo ya hecho. Se actualiza inventario al árbol actual,
  incluyendo R1 parcial, prototipo R2 y contención posterior; no se cambia código/runtime.
* Leídos contratos Corona/Containment/Applet/AppletQuickItem, ejemplo CustomCorona,
  configuración de applet/panel y edición upstream de la versión local; auditadas rutas de
  servicios, tareas, reloj, menús y carga del puente. Fuentes ausentes se marcan sin cotejo.
* Corregida afirmación anterior: kwin.lua no escala factor 1, pero appearance carga la base
  antes; el fallo de retorno a 1 no está demostrado. Kickoff aún tiene Configurar desactivado;
  panel comparte configuración entre monitores. Breeze de fábrica declara BreezeLight.
* Entregados protocolo de referencia con 12 casos y manifiesto SHA-256 de 26 archivos.
  Se cumple la alternativa de R0 para sesión de referencia inaccesible. IPC/servicios vivos y
  mediciones visuales siguen sin verificar; no se certifica equivalencia ni resolución del crash.
* BREEZE_R0_RESULTS.md incluye cierre con límites y siguiente prompt R1. Sin instalación,
  reinicios, cambios de skin, commit o push. Documentación actual corrige el estado del veto de sombras.

### 167. Continuación R1: restaurar especiales desde dock Retro sin extraerlos (2026-11-12)

* Dock Retro delega al controlador común con PID de lastIpcObject. Opción restore-on-current
  conserva destino actual para normales (Omarchy) y nombre/geométrica de origen para especiales.
  No cambia la restricción nativa de minimizar sólo en workspaces normales flotantes de Retro.
* Cleanup no_anim del dock pasa de shell diferido a timer con PID fresco en el compositor.
  min/toggle con dirección cerrada ya no usan como alternativa la ventana activa.
* Diez pruebas nuevas de Lua con estado, CLI y método real del dock en QtTest pasan; también
  las específicas de activación/minimizado/KWin/transición. Sin capturas ni acciones en sesión.
* IPC sigue rechazado: R1 no se cierra visualmente. No se cambió skin, reinició shell,
  reactivó sombras/miniaturas ni instaló plugin. Informe ampliado BREEZE_R1_RESULTS.md.

### 168. Intento de validación real R1 y límite de permisos (2026-11-12)

* Usuario autoriza probar todo y reactivar compositor con cuidado. Consulta IPC falla y
  escalación read-only de hyprctl -j version rechazada por sandbox_approval=false antes de ejecutar.
  No se reinicia compositor: no se puede comprobar estado/ventanas ni cambia el permiso al reiniciar.
* Preparado bwm-r1-validate.py para ejecutar desde una terminal real de la sesión, con fixtures
  desechables y limpieza/restauración; rechaza Magic ocupado y no usa capturas ni reinicia nada.
* Aquí sólo preflight bloqueado; 3 tests de seguridad aislados pasan. Cero pruebas gráficas nuevas
  aprobadas. Instrucciones/alcance en BREEZE_R1_RESULTS.md. R1 sigue sin aceptación de sesión.

### 169. R1: prueba principal aprobada en la sesión real del usuario (2026-11-12)

* Usuario ejecuta bwm-r1-validate.py --run y comparte resultado; se comprueba el mismo JSON
  en /tmp y se conserva en docs/BREEZE_R1_SESSION_RESULTS.json, sin títulos/datos privados.
* Hyprland 0.56.2: IPC, Magic canónico, dispatcher mostrar/ocultar, activación repetida/foco,
  minimizar/restaurar con política de dock y rechazo de PID incorrecto aprobados. Limpieza
  sin errores reportados; compositor no reiniciado y visual_verified=false.
* Esta es evidencia real por ejecución del usuario; el sandbox no obtuvo acceso. No cubre
  pulsación física, clic QML del dock, matriz de monitores/skins, fullscreen o Mostrar escritorio.
  R1 tiene smoke principal aprobado pero aceptación completa pendiente. Sombras/capturas siguen
  contenidas; no se declara resuelto el crash. Sin cambios de runtime en este registro.

### 170. R1: matriz de monitores/skins y registro de observaciones preparado (2026-11-12)

* bwm-r1-validate.py añade --matrix/--interactive. Recorre monitores por desc y tres skins,
  verifica identidad/workspace de apps preexistentes, estado Magic y restaura skin original.
  Bloques manuales por skin registran s/n/pendiente; no se confunden con medición de render.
* Rechaza matriz sin plugin cargado; no carga plugins ni reinicia compositor. Alt+Tab físico
  sólo se ofrece en Breeze mientras no se resuelva el crash; otras skins quedan pendientes.
* 9 pruebas aisladas del validador y 10 de restauración pasan. Matriz nueva aún no ejecutada
  en sesión; smoke real anterior se conserva. Instrucción y alcance en BREEZE_R1_RESULTS.md.

### 171. Primer intento de matriz R1 y preparación del puntero (2026-11-12)

* Usuario sólo ve Comprobando skin: default. Informe encontrado: error de monitor enfocado,
  matrix vacío y cleanup sin errores; se conserva en BREEZE_R1_MATRIX_ATTEMPT_01.json.
* Se coloca puntero en centro lógico del monitor antes de enfocarlo y se espera convergencia;
  se guarda/restaura cursor y se añade diagnóstico si falla. Sin cambiar política de foco.
* Simulador reproduce vuelta de foco al monitor del puntero y prueba con/sin movimiento.
  9 pruebas pasan. Falta repetir en sesión; causa real aún no confirmada. Sin nuevo crash report
  observado. Detalle en BREEZE_R1_RESULTS.md.

### 172. Iconos de Breeze tras la matriz: restauración sin aviso a KIconLoader (2026-11-12)

* Usuario ve iconos de Retro (sonido, entre otros) en la barra Breeze. kdeglobals y qt6ct
  inspeccionados seleccionan breeze-dark; no se ha visto el render de la sesión desde aquí.
* Hallazgo: plasma-theme.py restore devolvía kdeglobals guardado y enviaba sólo cambio de
  paleta, sin invalidar iconos. Se añade notify_icons para grupos KDE Desktop..Dialog (0..5)
  tras ambas ramas de restore, y se reutiliza al aplicar iconos explícitamente. Es un defecto
  comprobado de notificación, candidato al síntoma; falta verificar visualmente el resultado.
* Orden refresh-icons sólo emite avisos de iconos, sin reescribir preferencias, cambiar skin,
  reiniciar apps/shell/compositor ni forzar Breeze en lugar del tema KDE elegido por el usuario.
* 12 pruebas del aplicador pasan, incluidas restauración del tema personalizado antes del
  aviso, grupos panel/pequeños y refresco sin escritura. Bus real no usado en las pruebas.
  Sintaxis/diff correctos. Recuperación de la barra actual requiere ejecutar refresh-icons en
  terminal real por la restricción de IPC/D-Bus del sandbox. No se afirma icono ya reparado.

### 173. Iconos de Breeze: el aviso no basta; comprobación en proceso nuevo (2026-11-12)

* El usuario confirma que refresh-icons no corrigió sonido y ahora ve el logo de GNOME.
  No se considera resuelto el incidente de §172.
* Comprobación aislada con QApplication y KIconLoader, plataforma offscreen, tanto con
  QT_QPA_PLATFORMTHEME=qt6ct como kde: Qt y KDE seleccionan breeze-dark; audio-volume-high
  resuelve a /usr/share/icons/breeze-dark/status/24/audio-volume-high.svg y
  start-here-kde-symbolic a /usr/share/icons/breeze-dark/places/22/start-here-kde-symbolic.svg.
  La configuración activa de Kickoff también conserva start-here-kde-symbolic. Esto verifica
  los recursos y su resolución en un proceso nuevo, no el render de la barra existente.
* Siguiente recuperación: bwm-theme-manager.py set plasma --restart-shell, reinicio único
  de mantenimiento del shell; no volver a ejecutar la matriz de skins. No realizado desde
  el sandbox por el bloqueo de acceso a la sesión. Pendiente confirmar ambos iconos después.
  No se fuerza otro tema de iconos ni se modifican preferencias del usuario.

### 174. Kickoff de Breeze se abre con el buscador enfocado (2026-11-12)

* **Petición:** como en Plasma, al abrir el menú con Super (o Alt+F1) lo que se teclee a continuación debe buscar aplicaciones.
* **Causa:** `KickoffWindow.qml` hacía `kickoff.forceActiveFocus()` al mostrarse la capa; `Kickoff` es un `Item` normal (no un `FocusScope`), así que el foco se quedaba en él y no descendía al `searchField`, y las letras se perdían.
* **Hecho:** `focusSearch()` en `KickoffWindow.qml` enfoca `kickoff.searchField` con `Qt.ShortcutFocusReason` al hacerse visible la capa, con reintentos cada 25 ms (máx. 20) mientras la vista aún no ha creado el campo.
* **Verificado (sesión real, Breeze, tras reinicio de mantenimiento del shell, necesario porque la capa se carga por ruta):** con teclado virtual uinput, abrir por IPC y pulsar «f», «i» sin tocar nada → el campo muestra «fi» y la lista filtra aplicaciones; cerrado después, sin capas residuales. Capturas borradas.
* **No probado:** pulsar físicamente Super y escribir de inmediato. Las teclas que llegan antes de que el compositor dé el foco de teclado a la capa (unas decenas de ms tras soltar Super: lanza `app-launcher.sh`, que llama a `qs ipc`) las recibe la app que tenía el foco; es una limitación de layer-shell.

### 174. R3 parcial: preferencias nativas efectivas y catálogo de decoraciones (2026-11-12)

* Iconos: el usuario confirma resueltos tras el reinicio de shell de §173.
* Ocho KCModule QWidget sobre gestores comunes y puente KDE (ventanas, cursor, pantallas,
  escritorios por monitor, apps, inicio, atajos, inactividad). Nueve con luz nocturna R2.
  Aplicar explícito, revisión de página, validación, candado y relectura; errores conservan dirty.
* Puente: pendingReload durable ante error IPC; vigila cascada KDE completa y eventos ajenos
  no aplazan el debounce. Conserva formatos/claves/kdedefaults y precedencia del usuario.
* Perfil KAuthorized sólo para settings-native.sh: retira KCM incompatibles sin borrar plugins.
  Systemsettings real descubre los nueve y confirma filtrado de cursor/apps/autostart.
* bwm-kcm-catalog sigue X-KDE-ConfigModule y DecorationThemeProvider. Descubre Sweet (5 temas)
  y sus configuradores. Ensayo instalado Breeze: drawBackgroundGradient guarda, reabre y cambia
  el render del plugin; no se certifica su efecto en las ventanas vivas ni una opción propia Sweet.
* settings-capabilities.json: autoridad por clave, APIs ausentes y contrato R7; efectos
  soportados vacío, sin anunciar KWin como motor operativo. Plasmoides quedan en R4.
* 54 pruebas Python y 3 ejecutables CTest pasan. Build/install sólo /tmp/bwm-r3-prefix;
  sin instalar en HOME, sin IPC de sesión, sin cambios de skin, capturas ni sombras.
  R3 sigue parcial: aceptación real, controles avanzados y terceros por completar. Informe
  BREEZE_R3_RESULTS.md con tabla/control y rollback. No cambia Super+I ni cierra R2.

### 175. R3: instalación real comprobada tras confirmación del usuario (2026-11-12)

* Usuario ejecuta make install. Los nueve KCM del prefijo real coinciden por SHA-256 con
  src/bwm-systemsettings/build. Systemsettings real los descubre mediante settings-native.sh;
  siete módulos incompatibles enumerables en offscreen quedan retirados por el perfil.
* Evidencia BREEZE_R3_INSTALLATION.json; informe R3 actualizado. Instalar ya no es pendiente;
  apertura gráfica y aplicación real siguen sin verificar. Sin reinicios ni ajustes cambiados.

### 176. R3 Centered confirmado y R4: primer anfitrión nativo aislado (2026-11-12)

* Usuario confirma apertura de systemsettings real, Centered aplica a ventana nueva y persiste
  al reabrir. No valida por extensión toda R3 ni el ciclo de skins.
* src/bwm-plasma-host: Corona/Containment/Applet/PlasmoidItem, ConfigView/Model, KConfigLoader
  y KPackage reales. Tres paquetes instalados/retirados en XDG temporal con kpackagetool6.
  Ejemplo compacto original tiene ambas representaciones; ejemplo configurable y Andromeda
  cargan páginas, guardan bool descubierto dinámicamente y releen desde proceso nuevo.
  Segunda instancia intacta. Pruebas no muestran ventanas ni usan bus de sesión.
* Migración: propuesta sin escritura con origen íntegro, tres tests OK. Contratos R5, formatos,
  capacidades, proveedor plasmoids.knsrc y actualización upstream documentados.
* R4 sigue pendiente: falta shell package/muebles de expansión, diálogo interactivo completo,
  integración layer-shell/panel, migración aplicada y KNS vivo. No se presenta lista fija como
  host universal. Sin cambios en panel, servicios, sombras, capturas, skin ni compositor.
* BREEZE_R4_RESULTS.md, BREEZE_R4_ARCH.md y BREEZE_R4_PROBE_RESULTS.json. No instalación real,
  commit ni push; auxiliar experimental declarado como recomendación de compilación.

### 177. Tareas del panel de Breeze: el segundo clic no devolvía la ventana minimizada (2026-11-12)

* **Petición:** clic en una app de la barra la minimiza; un segundo clic sin mover el ratón no la traía al frente; alejando el cursor y volviendo, sí.
* **Causa (reproducida):** al minimizar una ventana sola en su workspace (o sin otra ventana que tome el foco, con el puntero sobre el panel), Hyprland la mantiene como ventana activa aunque esté en `special:minimized`; `activewindow` la sigue dando y su toplevel conserva `activated`. `TasksModel.click()` veía «una ventana activa» y la volvía a minimizar (no hacía nada). Al mover el puntero sobre el escritorio u otra ventana cambiaba el foco y el siguiente clic sí la activaba. Con otra ventana en el workspace el foco pasa a ésa y no ocurría.
* **Hecho:** `modules/plasma/panel/TasksModel.qml` con `isActive(top)` = `activated` y no en `special:minimized` (KWin nunca da por activa una ventana minimizada); lo usan `click()`, `cycle()` y el estado visual de `Task.qml`.
* **Verificado (sesión real, Breeze, tras reinicio de mantenimiento del shell):** kitty de prueba sola en el workspace 9 y ratón virtual uinput sobre su icono: primer clic → `special:minimized` (y sigue siendo la activa, confirmando la causa), segundo clic sin mover → de vuelta al 9. Ventana cerrada, workspace 1 y foco en Vesktop devueltos, `configerrors` vacío.
* **No probado:** con el ratón físico; grupos de varias ventanas (usan el mismo `isActive`).

### 179. Minimizadas de Breeze sin salida al cambiar de skin (2026-11-12)

* **Petición:** las apps minimizadas en Breeze quedaban en un limbo difícil de sacar al cambiar de skin.
* **Causa:** desde §3.114 todas las skins comparten `special:minimized` y al cambiar de skin «no se mueve nada». Pero sólo Breeze tiene algo visible que las devuelva (el panel); en default el dock de end-4 está apagado por defecto y en Retro el dock de Omarchy sólo sale en workspaces flotantes. Sólo quedaba Alt+Tab.
* **Hecho:** `toggle-minimize.py release-all` devuelve todas las minimizadas a su workspace de origen (geometría y etiquetas como `restore`, sin foco ni cambio de workspace; `restore_win(focus=False)`) y vacía el estado de «Mostrar escritorio». `bwm-theme-manager.py` lo llama al cambiar a una skin sin forma de verlas (`shows_minimized()`: Breeze sí; default sólo con `dock.enable` en su perfil; Retro no), antes de capturar las ventanas, para que la skin destino las coloque en mosaico o flotantes como a las demás. Matiza §3.114.
* **Verificado (sesión real, Breeze):** kitty de prueba en el workspace 9, minimizada con `kwin-window.py` → `special:minimized`; `release-all` → de vuelta al 9 sin etiquetas, misma ventana activa y mismos workspaces visibles (10 y 1). Regla temporal retirada, `configerrors` vacío, `py_compile` correcto.
* **Cambios de skin reales (a petición):** con una kitty de prueba minimizada desde el workspace 9: Breeze → default tres veces y default → Retro una: en las cuatro volvió al 9 sin etiquetas. Un primer intento Breeze → default **no** la devolvió (siguió en `special:minimized` con su etiqueta) y no se pudo reproducir ni explicar después (en ese intento no se registró la salida de `release-all`). El resto de ventanas conservó PID y workspace, una sola instancia del shell, `configerrors` vacío; se volvió a Breeze con los workspaces 10/1 y el foco en Vesktop.
* **Breeze → Retro con varias (a petición):** tres kitty de prueba minimizadas desde Breeze (dos del workspace 9, una del 8, flotantes): al entrar en Retro (2,7 s) las tres volvieron a su workspace, en mosaico y sin etiquetas, sin ningún evento de cambio de workspace o monitor y con la misma ventana activa. De vuelta en Breeze flotan en su workspace. Una sola instancia del shell, `configerrors` vacío.
* **Observado durante esa prueba:** una ventana del usuario en el workspace 10 (PID 18138) ya no existía al terminar; sin coredump ni rastro en el journal ni en el log de Hyprland, y el usuario usaba el ratón en ese momento. Los comandos de prueba sólo tocaron las clases `bwm-mt*`; no se ha establecido qué la cerró. Investigado después: era casi con seguridad Firefox (hay uno nuevo, PID 100566, en el workspace 10, arrancado a las 21:06:08 como `app-firefox-bin@….service` desde `firefox-bin.desktop`, el patrón de los lanzadores de KDE como Kickoff/KRunner). El anterior seguía vivo a las ~21:04 y murió de golpe: no escribió `sessionstore.jsonlz4` (último cierre limpio a las 03:58), sin informe de fallo de Firefox ni coredump, sin OOM ni kill en el kernel, sin salida suya en el journal y con un log de Hyprland que sólo tiene el arranque. Firefox 158.0.1 no se había actualizado. En BWM nada envía señales a Firefox durante un cambio de skin (`restart_firefox` no tiene llamadas; los `pkill` sólo afectan a apps GTK 4 fuera de transición, swaync y Spotify). Causa sin determinar; candidatas: un error de protocolo Wayland que desconecta al cliente o un fallo sin informe. **Reproducción (a petición):** con el Firefox nuevo (su salida va al journal por ser unidad) y vigilando su PID cada 0,2 s y los `closewindow` de socket2: el mismo escenario (tres kitty minimizadas, Breeze → Retro → Breeze, cierre de las kitty y `hyprctl reload`) y dos ciclos completos default → Retro → Breeze: siete cambios de skin sin que Firefox muriera ni escribiera nada en el journal; resto de ventanas con el mismo PID y workspace. No reproducido; si vuelve a pasar, mirar `journalctl --user` del Firefox lanzado como unidad.
* Las que ya estuvieran en el limbo salen en el próximo cambio de skin o con `toggle-minimize.py release-all`.

### 178. R4: popup, diálogo nativo y catálogo vivo en auxiliar aislado (2026-11-12)

* Paquete Plasma/Shell mínimo de BWM sobre AppletPopup y ConfigView reales. Compacto pulsado,
  expansión/cierre repetidos, botones Aplicar/Cancelar/Predeterminados y navegación probados.
  Bool/texto/enteros, defaults del esquema no expuestos y conflicto concurrente cubiertos.
* ConfigView se autodestruye al ocultarse: corregido doble borrado con QPointer. ASan encontró
  el fallo en el auxiliar de prueba; corrección y regresión pasan, sin afectar la sesión real.
* Catalog usa PluginLoader (KPackage + bibliotecas/qrc): lectura local de 27 widgets, 18 nativos.
  Reloj analógico nativo probado. Watcher único y PackageJob prueban alta/baja con catálogo vivo.
  Obtener nuevos conecta KNSWidgets::Dialog(plasmoids.knsrc); descarga remota aún no probada.
* Vista --preview y script preview-isolated.py opt-in con copia/config temporal; menú QAction
  probado con acción inocua, sin acciones de sesión. No se abrió en el escritorio del usuario.
* CTest aislado normal y AddressSanitizer pasan con ejemplos KDE y Andromeda; resultados en
  BREEZE_R4_UI_RESULTS.json y BREEZE_R4_UI_ASAN_RESULTS.json (leaks deshabilitados).
* R4 pendiente: Wayland/Hyprland (posición nativa usa PlasmaShellWaylandIntegration), migración
  aplicada y ciclo del panel, casos de configuración bloqueados, descarga KNS e integración R5.
  Sin cambios en barra activa, compositor, sombras, capturas, servicios, instalación o push.

### 180. R4: adaptador layer-shell y staging nativo, pendiente de sesión (2026-11-13)

* BwmSurface/PopupAnchor usan LayerShellQt por ventana: geometría lógica, cuatro bordes,
  clipping/flip, pantalla/DPR de Qt, área útil explícita, OnDemand, Top/Overlay y zona -1.
  Cambio de salida recrea rol. Vista --layer-preview opt-in, sin reserva ni sustitución de barra.
* BwmMigration stage/verify crea datos de instancias con Corona, guarda archivo original íntegro,
  hace sync/libera propietarios antes de publicar directorio y relee desde otro proceso.
  Dos paneles ficticios/dos relojes, IDs y settings persistidos; errores no publican parciales.
  showSeconds conserva false→ToolTip(1), true→Always(2), contrastado con DigitalClock actual.
  activationAllowed=false: disposición completa, activación y rollback siguen pendientes.
* CTest normal/ASan pasa surface-geometry + isolated-plasmoids; 5 tests de propuesta/mapeo y
  7 de manifiestos OK. BREEZE_R4_SURFACE_MIGRATION_RESULTS.json conserva evidencia.
* plasma-desktop no instalado (qlist/base local); faltan widgets originales del panel. Pretend
  con USE=-semantic-desktop resuelve 5 nuevos/19071 KiB, luego falla al actualizar news por
  filesystem read-only. Sin instalación. Comando sudo preparado en BREEZE_R4_RESULTS.md.
* LayerShellQt declarado en build y plasma-desktop-widgets como recomendación de recursos;
  presencia de paquete no certifica APIs KWin/modelo de tareas ni inicia esos servicios.
* R4 pendiente de paquete desktop y pruebas Wayland reales, migración completa/activación,
  callbacks bloqueados y descarga KNS. No se abrió preview en la sesión ni cambió el panel.

### 181. R4: plasma-desktop instalado, panel/QML original y configuración por instancia (2026-11-13)

* Verificado kde-plasma/plasma-desktop-6.7.5 instalado por el usuario; catálogo43 entradas.
  kind/containmentType son metadatos; catalogVisible sigue NoDisplay/categoría/form factors
  del explorador. Folder View/bandeja pueden ser containments y widgets visibles a la vez.
* El staging usa org.kde.panel, General/AppletOrder mediante schema y Corona. --probe-stage
  carga qrc original, verifica contenedores/tamaños/orden en dos paneles y relee después.
  Diez instancias/cinco widgets en dos paneles conservan datos de fixture y archivo original.
* PanelSession conecta configureRequested nativo a ConfigurationSession por ID. QtTest pulsa
  Aplicar, cierra/reabre, verifica persistencia y segunda instancia intacta con ejemplo KDE y
  Andromeda. Diálogo sin categorías explica el límite y bloquea Defaults/Apply.
* Andromeda define fullRepresentation como botón y abre PlasmaCore.Dialog propio: clic real
  de esa ruta probado offscreen. El wrapper compacto de la primera prueba no cubría su menú.
  PopupAnchor aún sólo adapta AppletPopup del anfitrión, no ventanas arbitrarias del paquete.
* --native-panel en preview-isolated ofrece dos instancias en org.kde.panel; --layer-panel
  selecciona la superficie experimental. Sin instalación/autostart, apertura de sesión ni
  sustitución de barra. El auxiliar sigue fuera del runtime de producción.
* Esquemas heredados con nombres KDE pasan a validación nativa, sin lista fija de claves.
  Kickoff prepara favoritesPortedToKAstats=false para el nuevo cliente por ID; importación
  efectiva aún pendiente. Listas copiadas independientemente entre propuestas de monitor.
* CTest normal/ASan (leaks off) pasa dos suites, siete tests Python de migración y siete de
  manifiestos OK. Evidencia BREEZE_R4_NATIVE_PANEL_RESULTS.json; arquitectura y README al día.
* --theme-catalog usa Plasma/LookAndFeel/KConfig: defaults y referencias de componentes,
  recursos propios/fallback y scripts con hash/executeAllowed=false. Tema desechable instalado,
  inventariado con claves desconocidas y retirado. No aplica defaults ni evalúa layouts/QML.
  Retirada de widget con configuración abierta probada también en el panel original.
* R4 pendiente: negociación/foco/posición Wayland, backend BWM de tareas/escritorios/Mostrar
  escritorio, favoritos KAStats, geometría/activación/rollback/skins y descarga KNS. Catálogo
  expone dependencias y operationalVerified=false; desconocidos unassessed. Sin R5, reinicios,
  cambios de sombras/miniaturas, commit ni push.

### 182. R4: Dialog propios, registro pre-superficie y geometría Qt de la vista (2026-11-13)

* Usuario indica «ya está, continúa» tras la vista normal. Sin informe de matriz no se da por
  validado layer-shell, foco, dos monitores o escalas. No se inicia R5 ni se sustituye la barra.
* PackageWindows registra QQuickWindow del proceso por contexto nativo plasmoid y pertenencia
  al containment. Dialog oculto/sin handle: rol preparado antes de show, Overlay/OnDemand/-1.
  PopupAnchor independiente conserva visualParent o x/y solicitados, límites y visibilidad al
  cambiar de salida, sin activar expanded. No modifica paquetes, metadatos ni servidores KDE.
* Tipos pendientes explícitos: Window genérico, no interactivos, rol ya creado/ventana visible,
  ancla externa. Sin tocar ventanas sin propietario del panel ni AppletPopup ya alojado.
  Registro coalescido por eventos y refresh explícito; sin sondeo periódico. waylandVerified=false.
* ViewCorona reemplaza fixture 1024×768 en ejecutable por QQuickWindow/QScreen: geometría lógica,
  área Qt disponible, región y asignación de salida; índices no persistentes. Staging conserva
  fixtures. Reservas que Qt no comunique necesitan fuente del anfitrión y aceptación real.
* CTest normal/ASan pasa dos suites, incluido menú real de Andromeda con rol preparado antes del
  clic, Dialog desconocido, límites/limpieza, x/y y geometría de salida. Siete tests Python de
  migración y siete de manifiestos OK. ASan leaks off. Resultado PACKAGE_WINDOWS_RESULTS.json.
* R4 sigue pendiente: negociación/foco/escala/salidas Wayland, tipos/creación tardía no adaptados,
  backend BWM, KAStats, geometría/activación/rollback/skins, callbacks/KCM y KNS remoto.
  Vista manual --native-panel --layer-panel preparada; no se abrió desde el sandbox ni se
  accedió a sockets restringidos. Sin reinicios, sombras/miniaturas, instalación, commit o push.

### 183. Terminal sin barra tras Retro→Breeze: precarga de breezebars al iniciar (2026-11-13)

* Usuario abre terminal tras Retro→Breeze sin barra; hyprctl -j breezebars-csd devuelve
  unknown request. La terminal configurada es Kitty y hide_window_decorations=no. El comando
  no está registrado en su sesión; no se obtuvo plugin list ni snapshot CSD vivo desde sandbox.
* Causa encontrada en código: autostart sólo cargaba breezebars si arrancaba en Plasma.
  sync_floating_windows activaba su opción al cambiar a Breeze, pero no podía crear un plugin
  ausente. Las barras de Retro son otro plugin y no resuelven esta ausencia.
* Bloque 9 de autostart ahora precarga el .so existente en cualquier skin inicial, sólo al
  arrancar Hyprland. appearance.lua mantiene enabled=false fuera de Breeze. Bridge enter
  precede a la carga sólo si inicia en Breeze; bridge/decorator tampoco arrancan en Retro/default.
  Evita duplicar plugin load, no hace unload ni añade carga desde la transición. Fallo de carga
  se informa por stderr; binario ausente no interrumpe arranque de otras skins.
* El aviso del gestor de skins identifica breezebars ausente y explica reentrada de sesión,
  en lugar de nombrar hyprbars o sugerir que sólo se preparará iniciando en Plasma.
* Cuatro pruebas funcionales sobre bloque real con comandos simulados: las tres skins, orden
  enter→load, servicios por skin, carga única, binario ausente/fallo y Lua de enabled. Pasan;
  bash -n, py_compile y diff OK. No se ejecuta autostart real durante las pruebas.
* Aplicación efectiva pendiente de cerrar/abrir sesión por el usuario. Sin plugin load/unload,
  modificación/reinstalación de .so, reinicio de compositor, cambios de skin, sombras o miniaturas
  desde esta ejecución. No se afirma todavía verificación visual de la terminal reparada.

### 184. Auditoría Retro→Breeze: Qt del shell, iconos y entorno de las apps (2026-11-13)

* Captura del usuario muestra otros iconos en Breeze tras iniciar en Retro. KDE/qt6ct seleccionan
  breeze-dark, GTK3/4 settings.ini conservaba Adwaita; corregido sólo ese campo a la selección
  actual. Proveedor Qt del proceso queda fijado al construir QApplication: bwmSkin.reload
  reconstruía paneles pero conservaba GTK si el shell nacía en Retro.
* bwm_session.shell_command usa KDE cuando está instalado, qt6ct/portal como fallback y rutas
  coherentes QML/kdedefaults para el shell duradero. Autostart usa ensure_shell (config ii),
  en vez de pidof de cualquier Quickshell. Cambios normales conservan proceso/servicios.
* bwm_icons actualiza respaldo GTK sin perder datos ajenos ni reescribir si coincide. Avisos
  nativos de paleta/fuentes/estilo y seis grupos de iconos; qt_sync sólo avisa si cambió su
  kdeglobals generado. Mantiene autoridad KDE en Breeze y temas personalizados/kdedefaults.
  Trabajos de iconos obsoletos se omiten antes de generar y antes de aplicar.
* AppSearch.launch → bwm-launch-app.py → bwm_session.spawn(allow_fallback=False) usa el entorno
  actual de Hyprland para DesktopEntry/acciones, cwd y terminal común. Actualizados buscador,
  Retro, dock, tareas/menús Breeze y grids/tareas Waffle. Así el proveedor estable del shell
  no se impone a las apps. Se preserva argv analizado, sin construir un Exec shell nuevo.
* Autostart exporta XDG_CONFIG_DIRS/XDG_MENU_PREFIX/QML_IMPORT_PATH a activación. Gestor solicita
  nueva exportación desde un hijo de Hyprland tras recarga, respetando overrides Lua; nunca
  exporta el entorno antiguo del llamante como fallback. Entrega real por bus aún no probada.
* 54 pruebas OK (runtime 12, panel 8, Plasma 12, sesión 7, Qt 4, arranque 4, manifiestos 7);
  parser acepta nueve QML modificados. bash -n, py_compile y diff correctos.
* QApplication aislado conserva QIcon: A→B→A→custom cambia icono nuevo/retenido, sin setThemeName
  ni forceThemeForTests. Bus privado/display fueron bloqueados; el probe final sólo invoca el
  receptor nativo local KF6 6.29.0 (contrato privado exclusivo del test), no entrega D-Bus.
  BREEZE_SKIN_TRANSITION_RESULTS.md y BREEZE_SKIN_TRANSITION_RUNTIME_RESULTS.json.
* Proceso actual necesita adoptar el nuevo arranque una vez. Reentrada de sesión aplica también
  precarga de breezebars; mantenimiento sólo de shell no carga un plugin ausente. Sin cambios
  de skin, reinicio de compositor/shell, cierre de apps, plugin load/unload o sombras/capturas
  desde aquí. IPC continúa bloqueado; aceptación visual Retro→Breeze pendiente en sesión.

### 185. R4: claves compartidas entre categorías y páginas estables durante edición (2026-11-13)

* Usuario confirma el aspecto tras la corrección Retro→Breeze y pide retomar R4. El TXT
  mencionado no está disponible en el entorno; no se inventa su salida ni aceptación Wayland.
* ConfigurationSession permite la misma clave nativa en varias categorías: mapa pendiente
  por instancia, notify original de cfg_ y propagación de la clave editada con guarda de
  reentrada. Controles con rangos incompatibles bloquean Aplicar con explicación. Propiedades
  sin escritura/notificación siguen sin adaptar; callbacks/KCM tampoco se anuncian operativos.
* pagesChanged queda separado del notifier dirty/error: editar no reconstruye los delegados
  de las páginas. Cancelar/Predeterminados no guardan; se mantienen inmutabilidad, detección
  de edición concurrente y conservación de claves ajenas mediante KConfig.
* Fixture propio desechable con dos categorías prueba ambos sentidos, 57 cambios sin alterar
  bytes/contenedor, Apply con efecto en binding Plasmoid.configuration, Defaults sobre clave
  oculta, Cancel, dos instancias, lectura en proceso nuevo, conflicto y rango incompatible.
  No se usa este fixture como certificado de terceros: driver también repite ejemplo KDE
  original y Andromeda con instalación/retirada temporal y sus páginas originales.
* Dos suites CTest normales y ASan pasan, 11 resultados UI por paquete más lectura en proceso
  nuevo; ASan con detect_leaks=0. Siete tests Python de migración y siete de manifiestos OK.
  Evidencia BREEZE_R4_SHARED_CONFIG_RESULTS.json; informes/arquitectura/guía/plan actualizados.
* R4 sigue pendiente de Wayland real, backends y activación/migración completa, tipos/creación
  tardía de ventanas, favoritos KAStats, callbacks/KCM y descarga real KNS. Sin nuevas
  dependencias, instalación, acceso a sockets restringidos, cambios de skin, reinicios de
  shell/compositor, plugins, sombras/miniaturas, commit o push. No se avanza R5.

### 186. R4: API nativa de instancias, orden persistente y acciones dinámicas (2026-11-13)

* Usuario pide seguir R4 y cita el aviso previo de pendiente; no es salida nueva de sesión.
  Se continúa sin exigir TXT. No se implementa el editor visual R5.
* PanelSession expone panelInfo/widgets/order, addWidget/removeWidget/requestOrder,
  widgetActions/triggerAction y configure. Main enlaza AppletQuickItem propietario y deja
  el QObject bwmPanelSession en su ventana. Catalog.discover comparte descubrimiento/política
  de metadatos con el catálogo vivo, sin otro watcher por panel ni lista fija de widgets.
* Altas por createApplet, bajas permanentes por Applet.destroy e inmutabilidad respetada.
  Al marcar destroyedChanged se cierra Configurar antes de limpiar el esquema. Se rechazan
  IDs de otro panel, raíz como widget, órdenes incompletos/duplicados/fraccionarios y bloqueos.
* Orden mediante reorderApplets/LayoutManager original; true acredita despacho, consumidor
  verifica order. Inventario coalescido. Menús con QAction originales y tokens efímeros por
  QObject; submenús/estados dinámicos, pertenencia actual y ruta habilitada/visible. prepare=false
  refresca sin reejecutar la fábrica del menú. No se simulan acciones internas/undo/servicios.
* Prueba de exportación detecta que saveLayout a otro nombre copia estado del containment
  bajo Configuration. Persistencia correcta: loadLayout del propietario antes de crear,
  saveLayout del mismo archivo + config.sync. AppletOrder vive en Containments/<id>/General.
  Ejecutable y staging ya usan mismo propietario; se alinea el test y verifica archivo/posiciones
  del QML original/valores al reabrir en otro proceso. No se escribe un appletsrc alternativo.
* Dos suites CTest normales/ASan pasan: 14 resultados UI por paquete original KDE/Andromeda,
  además de lecturas de panel/configuración en procesos separados. Siete tests migración y
  siete manifiestos OK; py_compile/diff correctos. ASan detect_leaks=0, no certificado de fugas.
  BREEZE_R4_PANEL_API_RESULTS.json con drivers, logs y hashes; arquitectura/guía/resultados
  y procedencia actualizados. Prompt R4 restaurado desde el encargo del usuario: sólo tenía
  «ewe» y no cerraba el bloque. No cambia alcance a R5 ni añade dependencias.
* R4 pendiente de sesión Wayland real, superficies duraderas desc:, activación/rollback/skins,
  descarga KNS y capacidades por paquete aún sin adaptar. API en proceso; editor externo
  necesitará IPC/ciclo de vida. No se activa el panel ni se cambia skin, shell/compositor,
  plugins, sombras/miniaturas o servicios reales. Sin instalación, commit ni push.

### 187. R4 en la sesión Wayland real: posiciones, foco del panel y ventanas no interactivas (2026-11-13)

* Usuario pide continuar R4 donde lo dejó la sesión de ChatGPT. Esta vez sí hay acceso a
  Hyprland: vista --native-panel --layer-panel con Andromeda en entorno desechable, sin bus
  de sesión ni plasmashell/KWin, ratón virtual uinput sólo durante cada prueba; puntero y
  foco devueltos, panel Breeze activo intacto.
* Hallazgos: Qt Wayland llevaba cada ventana al origen de su salida (panel en 2560,0 para Qt,
  menú de Andromeda en la esquina superior); el avatar (Dialog Notification) salía como
  ventana normal; el panel tomaba el foco y el segundo clic no cerraba el menú; el menú tapaba
  el icono por el hueco de 64 px de la vista.
* Corrección como upstream: QT_WAYLAND_DISABLE_FIXED_POSITIONS sólo al crear QApplication y
  fondo con alfa (plasma-workspace 6.7.5 shell/main.cpp); panel transparente, sin foco y
  KeyboardInteractivityNone salvo AcceptingInputStatus (PanelView::refreshStatus, que ya usa
  LayerShellQt). Propio: posición del panel publicada en QWindow, posición pedida limitada al
  área sin la franja del panel y devuelta a la QWindow; Dialog solo salida/Notification/OSD/
  Tooltip como capa Overlay sin teclado. preview-isolated.py --output elige salida por desc.
* Comprobado en LG y MSI: menú 680×516 sobre el panel, avatar centrado en su borde, cero
  ventanas sueltas; abrir/cerrar con el icono, clic dentro y Escape. CTest normal y ASan
  (detect_leaks=0) 2/2, migración y manifiestos OK. Evidencia BREEZE_R4_WAYLAND_SESSION_RESULTS.json.
* Clic fuera (segunda iteración): Hyprland deja el foco en una capa si el clic no cae en una
  superficie. FocusGrab usa hyprland_focus_grab_v1 (cliente generado del XML de hyprland-protocols
  del sistema); lista blanca Dialog + panel + Dialog no interactivos; cleared oculta Dialogs con
  hideOnWindowDeactivate; inerte sin protocolo. Probado: escritorio vacío cierra, clic dentro
  no, avatar en lista blanca. Qt6 WaylandClient y hyprland-protocols declarados (regla 12).
* Pendiente: fondo translúcido sin desenfoque, vista sin fondo de panel, escala fraccionaria,
  otros bordes, otros paquetes, activación/migración/skins y KNS. R4 sigue pendiente; sin commit ni push.

### 188. R4: páginas por módulo QML, propiedades iniciales y CLI común (2026-11-13)

* Se conserva §187 y su evidencia Wayland real; desde esta ejecución hyprctl -j monitors
  vuelve a fallar con Couldn't open a socket (1). Sin bypass ni nuevas pruebas de sesión.
* ConfigurationSession deja de confundir configUiModule/configUiComponent con KCModule.
  Usa QQmlComponent.loadFromModule y prioridad de AppletConfiguration.qml 6.7.5: pareja completa
  precede source, sin fallback silencioso al fallar; pareja incompleta admite source.
  Source absoluto preservado por ConfigModel se convierte a URL local. pluginName/KCM,
  callbacks y contratos no adaptados siguen bloqueados, con diagnósticos reales conservados.
* beginCreate/setInitialProperties/completeCreate entrega title y cfg_/Default/Immutable
  declaradas antes de Component.onCompleted, incluidas required. Contexto/localización
  nativos. --probe/--exercise usan la misma fábrica; ejercicio aplica por ConfigurationSession.
* Módulo propio en ruta QML aislada y nueve paquetes desechables prueban prioridad, fuente
  absoluta, required/contexto/localización, Apply/Cancel/Defaults, dos instancias y proceso
  nuevo; módulo/tipo ausentes, raíz no Item, required desconocido, descriptores parciales y
  KCM bloqueado. Fixtures propios no se presentan como terceros; KDE/Andromeda repiten sus
  páginas reales en la regresión común. No se alteran sus fuentes ni importaciones de sesión.
* Dos suites CTest normales y dos ASan pasan; 24 resultados UI por paquete, más lecturas en
  procesos separados. Siete migración y siete manifiestos OK, py_compile/diff. ASan con
  detect_leaks=0. BREEZE_R4_CONFIG_PAGES_RESULTS.json contiene drivers/probes/logs/hashes;
  arquitectura, guía, plan y procedencia al día. Sin dependencias nuevas.
* R4 pendiente de integración/activación/migración/rollback/skins, KNS remoto, pendientes
  visuales/Wayland y capacidades sin adaptar. No se activa el panel diario, reinicia shell/
  compositor, cambia skin, carga plugins, reactiva sombras/miniaturas ni instala en producción.
  Sin commit/push ni avance a R5.

### 189. R4: marco original Panel.qml, SVG/temas y geometría de la vista (2026-11-13)

* PanelViewHost deriva de ContainmentView y carga Panel.qml instalado con KPackage, sin copia
  ni parche. Global registra sólo los enums de PanelView 6.7.5. Contenido org.kde.panel nativo;
  Configurar virtual → PanelSession sin conexión duplicada. No se implementa UI de R5.
* --panel-preview/--layer-panel-preview usan el marco original; --probe-panel-frame verifica
  esa ruta en Qt offscreen. Layout de panel separado del de probes de widgets para no alojar
  por error un containment null. Fuente/readback/dimensiones/capacidades en el JSON del probe.
* Geometría separa preferred length y límites de superficie; evita encoger al inicializar o
  tomar el máximo del eje anterior. Grosor, padding, floatingness y máscara originales;
  duración Kirigami e InCubic/OutCubic. Configurar abre una sola sesión. Destrucción separa
  el item y destruye QML antes de los miembros; SharedQmlEngine guarda el root en QPointer.
* Dos temas SVG propios, instalados/retirados con KPackage, prueban cambio en vivo, colores y
  prefijos de cuatro bordes. Píxeles con tolerancia 4/255 RGB, alfa >250; NoBackground alfa0.
  Flotación 0↔1 y contenido/marco comprobados; límites 320→640 y cambio de orientación OK.
* Adaptive rechazado con explicación. Políticas fijas en memoria; fallback KDE sin composición
  conservado en offscreen. Autohide/dodge, reservas, blur, sombras externas y aceptación de
  máscaras/render del nuevo marco en Wayland sin certificar. No se ofrecen como ajustes
  persistentes activos; no confundir con el PanelView completo ni activar efectos por él.
* CTest normales y ASan 2/2, 26 resultados UI por paquete KDE/Andromeda, probes del ejecutable,
  lecturas separadas y regresiones de staging. ASan detect_leaks=0. Siete migración y siete
  manifiestos OK, sintaxis/diff. BREEZE_R4_PANEL_VIEW_RESULTS.json incluye logs/drivers/hashes.
  KF6 Svg explícito en CMake/requisito del auxiliar; KSvg ya requerido por Breeze. Tabla,
  arquitectura, guía y procedencia actualizadas.
* R4 pendiente de este marco en sesión, escala/bordes/reservas, controlador adaptable y efectos,
  persistencia de vista, integración/activación/migración/rollback/skins y KNS remoto. Se conserva
  §187 sin deducir nueva aceptación. Sin cambiar panel diario/skin, reiniciar shell/compositor,
  cargar plugins, reactivar sombras/miniaturas, instalar en producción, commit/push ni R5.

### 190. R4: revisión del alcance y migración de borde/orientación (2026-11-14)

* Usuario pide hacer lo que falte de R4, sin cambios si ya estuviera cubierto. Se detecta
  migración forzada BottomEdge/Horizontal y probe sólo por x, aunque origen indique otro borde.
* Propuesta conserva bar.plasma.edge; vacío/ausente usa bar.bottom (false de esquema→top),
  como PanelLogic.edge. Valores inválidos/fallback no booleano rechazados. C++ deriva del
  archivo autenticado y rechaza propuesta discrepante. Corona serializa Location/FormFactor
  nativos; verificador y probe respetan orientación y orden por x/y.
* orientationContractVersion=1 del informe exige campos coherentes con el origen/layout.
  Fuente leída una vez; validación antes de cargar. Informes antiguos siguen bottom/horizontal
  sin reescritura; propuestas antiguas sin edge se preparan desde la fuente. No se activa nada.
* Siete casos con dos paneles: cuatro bordes, fallbacks true/false y defecto de esquema.
  Stage→lectura nueva→QML original→lectura pasa; fuente exacta. Errores de propuesta/origen/
  campos ausentes y compatibilidad de informe antiguo comprobados. Doce tests migración y
  siete manifiestos OK; CTest normal/ASan 2/2, regresión UI 26 por paquete, sintaxis/diff.
  ASan detect_leaks=0. BREEZE_R4_ORIENTATION_RESULTS.json; informe/arquitectura/guía/plan al día.
* R4 sigue pendiente de aceptación de sesión/integración declarada y KNS remoto; hyprctl
  vuelve a fallar Couldn't open a socket (1). Auditoría distingue capacidades no adaptadas
  de promesas universales y evita invadir editor R5/efectos R7. Sin nuevas dependencias,
  cambio de panel/skin, reinicio, plugins, sombras/miniaturas, instalación, commit o push.

### 191. R4: persistencia nativa de preferencias del marco (2026-11-14)

* PanelViewSettings usa KConfig privado y el plasmashellrc original. Contrato contrastado
  con panelview.cpp, ShellCorona::applicationConfig y la identidad plasmashell de 6.7.5.
  floating/floatingApplets/panelOpacity en PlasmaViews/Panel <id>; thickness en Defaults;
  minLength/maxLength en Horizontal<ancho> o Vertical<alto> y Defaults, como el original.
* Nombre relativo conserva cascada XDG/kdedefaults. Sólo seis claves admitidas; conserva
  claves ajenas y otros paneles. Rechaza Adaptive y políticas explícitas sin controlador
  antes de abrir una vista que las ignore. No ofrece backends nuevos ni controles de R5.
* PanelViewHost carga valores antes del QML y los aplica al tamaño/flotación/opacidad reales
  del marco de ensayo. viewSettings/reloadViewSettings/applyViewSettings distinguen instantánea,
  vista previa y guardado explícito. Cambio de salida/orientación obliga a releer el ámbito.
* Lote validado antes de escribir, bloqueo por archivo para escritores BWM, firmas de todos
  los destinos (también Defaults oculto), inmutabilidad y mezcla KConfig. Sin watcher ni
  escritura por deslizador. No promete CAS entre aplicaciones; al fallar sync limpia el
  escritor privado para impedir reintento del destructor tras informar el error.
* Pruebas de grupos nativos, precedencia, claves ajenas, conflicto, escritor ocupado,
  kdedefaults inmutable y lote sin escritura parcial. Dos containments independientes,
  efecto del marco y lectura desde otro proceso; orientación obsoleta y Adaptive rechazados.
  CTest normal/ASan 2/2, 29 resultados UI por paquete y lectura separada 3/3. ASan sin
  detectar fugas (detect_leaks=0); doce tests migración y siete manifiestos aprobados.
  Evidencia BREEZE_R4_VIEW_SETTINGS_RESULTS.json; informe/arquitectura/guía/plan actualizados.
* Pendientes aceptación real de este marco/escala/bordes, ciclo por skin, otras preferencias
  heredadas, integración/activación/rollback y KNS remoto. Sin dependencias nuevas, cambios de
  panel/skin, reinicios, plugins, sombras/miniaturas, instalación de producción, commit o push.

### 192. R4: migración de preferencias de vista y probe del marco original (2026-11-14)

* migration.py/C++ derivan thickness/floating/panelOpacity desde el origen archivado. Grosor
  con fallback 0→44 y clamp 24..128 de PanelLogic; estilos con enums KDE 0/1/2. El antiguo
  style=floating es Adaptive más flag floating; el alfa numérico no se confunde con el enum.
* KConfig prepara plasmashellrc junto a layout/legacy.json/report.json. Grupos originales por
  ID Corona y Defaults, sin formato BWM ni reemplazo del archivo completo de la sesión. La
  futura activación requiere mezcla por panel con política/cascada del destino, aún pendiente.
* viewSettingsContractVersion=1 contrasta origen/informe/archivo. Detecta datos/contrato/
  pendientes omitidos o alterados. Propuestas antiguas derivadas desde el origen, stages
  antiguos realmente sin artefacto siguen legibles. Ningún stage certifica runtime.
* PanelViewHost acepta archivo al construir; ruta normal conserva plasmashellrc relativo/
  kdedefaults. --probe-stage-frame lee el artefacto con Panel.qml instalado y comprueba render,
  tamaño, modos/flotación y orden. --probe-stage conserva el ensayo de containment original.
* deferredViewSettings archiva valores/motivos: visibilidad/reservas, alineación, longitud
  proporcional sin salida, gap, docking y Adaptive sin backend; otros valores sin equivalencia
  no se aplican a ciegas. Adaptive se conserva pero el frame lo rechaza, no se degrada el modo.
* CTest normal/ASan 2/2, ocho casos con dos paneles (seis de marco y dos Adaptive rechazados),
  lectura posterior y fuente idéntica. Pruebas de alteraciones, claves ajenas, tipos inválidos,
  legado y raíz de preferencias intacta. Regresión UI 29 por paquete más lectura separada 3/3;
  18 tests migración y siete manifiestos. ASan detect_leaks=0. Evidencia completa y hashes en
  BREEZE_R4_VIEW_MIGRATION_RESULTS.json; informe/arquitectura/guía/plan/procedencia al día.
* Hyprctl sigue sin acceso (Couldn't open a socket (1)); R4 no cierra sesión/escala/bordes,
  activación/migración/rollback/skins ni KNS remoto. Sin nuevas dependencias, instalación,
  cambios de panel/skin, reinicios, plugins/efectos, commit/push o avance a R5.

### 193. R4: ciclo de vistas por monitor/skin e identidad de salidas (2026-11-14)

* PanelRuntime recibe Corona viva, archivo nativo de preferencias y bindings ID→descripción
  del llamador; exige cobertura exacta de paneles. Sólo plasma crea vistas, como máximo una
  por containment. Retro/default retiran vistas sin borrar containments/IDs/configuración.
  Invalidar skin/bindings no altera las vistas vigentes; snapshots explican estados/errores.
* BwmOutput sustituye también la búsqueda parcial de --output: fabricante/modelo/serie,
  normalización de desc:/espacios/caja, descripción completa/secuencia modelo+serie/modelo
  único. Rechaza conectores, serie distinta, subcadenas y duplicados; no fallback al primario.
* Hotplug retira antes de que Qt reasigne ventanas; reconexión restaura el mismo panel con
  conector/índice distintos. Cambio de borde recrea sólo esa vista/rol; resolución lógica
  relee su ámbito nativo. Adaptive no disponible bloquea sólo el panel afectado con motivo.
* ViewCorona.bind/unbind desconecta relaciones anteriores; destruir ventana sustituida no
  borra la vigente. screenRemoved notifica índice previo y recalcula vigentes. Suspender
  colapsa applets y oculta sus ventanas identificadas, con QPointer ante callbacks destructivos;
  eliminar la vista cierra ConfigurationSession sin aplicar controles pendientes.
* --preview-stage y --probe-stage-runtime consumen staging verificado bajo raíces temporales;
  el primero es opt-in layer-shell sin reservas, el segundo snapshot temporizado. CLI con
  salidas ausentes deja espera sin crear vistas. No se ejecutó preview en la sesión real.
* Cuatro tests nuevos con QScreen de fixture QPA offscreen prueban identidad, bindings,
  dos paneles, ciclos/ventanas/configuración, hotplug/duplicado, borde/resolución y proceso
  nuevo con enumeración/conectores cambiados. Widget del ciclo propio, no aceptación general
  Andromeda. CTest normal/ASan 2/2; 33 resultados UI por paquete y lectura específica 3/3;
  18 migración/siete manifiestos y sintaxis/diff OK. ASan detect_leaks=0. Evidencia completa
  BREEZE_R4_RUNTIME_RESULTS.json con logs/hashes; contratos/procedencia/guía/plan actualizados.
* Corona debe sobrevivir al controlador; anfitrión persistente requiere vida sin ventanas y
  llamada setSkin del gestor común. Hook diario, autoridad/persistencia de bindings y alta/
  baja de paneles completos pendientes; no inventa appletsrc ni un estándar de bindings.
  Aceptación Hyprland/escala/skins, servicios/ventanas sin adaptar, activación/rollback y KNS
  remoto siguen pendientes. IPC denegado; sin cambios de panel/skin, reinicios, instalaciones,
  plugins/efectos, dependencias nuevas, commit/push ni R5.

### 194. R4: hook de skins conectado a previsualización explícita y parada limpia (2026-11-14)

* hooks.skinChanged Breeze → panel-session.py mediante dispatcher común, confinado a ambas
  skins involucradas. Before antes de mutar perfiles; si falla aborta e intenta recuperar
  el auxiliar anterior. After tras recarga del shell. Contexto del lock del gestor cierra
  su descriptor también al abortar; prueba con la función real y efectos externos sustituidos.
* --follow-skin del envoltorio exige panel nativo/layer/output y registra explícitamente el
  auxiliar en XDG_RUNTIME_DIR/bwm-plasma-host-preview. Inicialmente inactivo, sólo se activa
  tras registro. Token+PID/inicio; muerto/zombie/reutilizado no autoriza comandos. Duplicado
  no crea otra vista ni retira registro ajeno. Sin registro no inicia procesos ni crea controles.
* RuntimeControl: watcher agrupado 25 ms, control/ack atómicos, revisión creciente, token y
  dueños únicos de control/layout; publicador serializa y espera hasta 1,5 s (dispatcher 3).
  Sólo skin/stop, sin dispatch de compositor ni D-Bus. Son metadatos privados temporales,
  separados del layout/preferencias KDE; no hay un appletsrc alternativo ni autoridad diaria.
* Stop confirma retirada, después salida principal guarda Corona/config.sync y comprueba
  resultado. Proceso vive sin ventanas. Ctrl+C del envoltorio envía stop, auxiliar ignora
  SIGINT y sigue en grupo del terminal. Registro retirado y transacción drenada antes de
  limpiar: se corrige carrera que borraba el ack antes de que lo consumiera el publicador.
* QtTest hook común real→Python→Qt con widget/salida propios; revisión antigua/token ajeno,
  singleton y no-op sin registro. CLI con cada paquete/salida ausente verifica vida/parada;
  envoltorio real prueba duplicado, parada externa y Ctrl+C del grupo privado del ensayo.
  CTest normal/ASan 2/2, UI 34 por paquete; 16 tests publicación/abort, 18 migración, siete
  manifiestos, cuatro arranque y 16 puente KDE aprobados, sintaxis/diff. ASan detect_leaks=0.
  Evidencia BREEZE_R4_SKIN_CONTROL_RESULTS.json con logs/hashes; guía/arquitectura/plan al día.
* Código de hook conectado, sin registro/ejecución en la sesión real ni sustitución diaria.
  IPC sigue denegado. Pendientes perfil/autoridad de bindings, activación/rollback real,
  servicios/controladores sin adaptar, Hyprland/escala/skins y KNS remoto. Sin dependencias
  nuevas, cambios de panel/skin, reinicios, instalación en producción, plugins/efectos,
  commit/push o avance a R5. Retirar la conexión no exige restaurar archivos de sesión.

### 195. R4: perfil nativo de ensayo y restauración por generaciones (2026-11-14)

* ProfileStore importa copia capturada/validada del staging a destino nuevo. Conserva layout
  completo de Corona, plasmashellrc, origen e informe; bindings.json separa IDs/descripciones/
  procedencia, head.json selecciona generación. No inventa appletsrc ni impone valores viejos
  del informe a los widgets editados. Validación nativa sobre copia, sin modificar lo inspeccionado.
* Lease del perfil durante toda la vida de Corona; guarda/sync/cierra propietarios antes
  de checkpoint con cinco archivos y hashes. Snapshot alterado, bindings/rutas/symlinks,
  destino existente o perfil ocupado se rechazan. Desconocidos nativos/head se conservan.
* Restore copia a una generación/ruta nueva y cambia head atómicamente; conserva la vieja.
  Escritura tardía de KSharedConfig retenido sólo afecta a su ruta anterior, probada. Sin GC;
  generaciones no elegidas pueden permanecer tras fallo de preparación. Lease cooperante
  y comprobación optimista de head; sin prometer CAS ajeno, firma ni durabilidad por corte.
* CLI import/profile-info/checkpoint/restore/serve-profile y preview-isolated --profile
  --follow-skin: reabre sin recrear widgets/IDs/bindings ni fijar BottomEdge. Lookup XDG del
  llamador, auxiliares/caché/runtime/D-Bus desechables. Dos arranques/cierres del envoltorio
  y checkpoints automáticos pasan; el perfil sobrevive a éste, bajo raíz temporal privada.
* Dos tests Qt nuevos con dos paneles/reloj KDE y widget propio añadido/configurado por
  PanelSession/ConfigurationSession; grosor 52/44 con efecto de vista, ciclo de skin,
  baseline/editado y lectura desde otro proceso con nueva enumeración. Archivos completos,
  desconocidos, escritor antiguo y errores comprobados. CTest normal/ASan 2/2, UI 36 por
  paquete y lectura específica 3/3; 16 control, 18 migración, siete manifiestos, cuatro arranque,
  16 puente KDE y sintaxis/diff OK. ASan detect_leaks=0. BREEZE_R4_PROFILE_RESULTS.json con
  logs/hashes; informe/arquitectura/guía/plan/procedencia actualizados.
* No es perfil diario ni garantía de conservar /tmp después de reiniciar el equipo. Pendientes
  autoridad/activación/rollback de sustitución, servicios/controladores no adaptados, aceptación
  Hyprland/escala/skins y KNS remoto. Sin registro en sesión, cambios de panel/skin, reinicios,
  instalación de producción, plugins/efectos, dependencias nuevas, commit/push o avance R5.

### 196. R4: exportación persistente XDG y reapertura fuera de /tmp (2026-11-14)

* ProfileStore.exportToState/--export-profile SOURCE NAME y envoltorio --profile SOURCE
  --export-as NAME conservan estado nativo seleccionado y todo historial de snapshots en
  GenericStateLocation/bwm/plasma/panel-profiles/NAME (XDG_STATE_HOME o ~/.local/state).
  Nueva generación/rutas con IDs/opciones/bindings/desconocidos; fuente y sus generaciones
  no seleccionadas intactas. No se duplican esquemas ni se fabrica otro appletsrc.
* Copia preparada en filesystem de destino, valida archivos/hashes/identidad nativa y publica
  sin reemplazo. Historial alterado no publica destino parcial. Nombres/rutas/propiedad/
  enlaces controlados; sólo autoridad XDG dedicada o temporal, no cualquier carpeta privada.
  No chmod de directorios preexistentes; aplicación/almacenamiento nuevos privados.
* Exportación no arranca ni registra preview, no selecciona perfil diario/autostart. Reabre
  después por --profile DEST --follow-skin; auxiliares/config de escritura/caché/runtime/
  D-Bus desechables y recursos/paquetes por lookup XDG. El snapshot no empaqueta esos activos.
* Fixture XDG_STATE_HOME en tests del repo fuera de /tmp, sin tocar estado real del usuario.
  Prueba de bytes/manifiestos, desconocidos, restore, origen intacto, alias y carpeta fuera de
  autoridad. CLI/envoltorio exporta, elimina fuente temporal, reabre/guarda/restaura destino;
  lease y copias conservados. Destino existente/nombre inválido rechazados. CLI también
  acepta slash final del directorio de snapshot y no confunde nombre inválido con --catalog.
* CTest normal/ASan 2/2, UI 37 por paquete; 16 control, 18 migración, siete manifiestos,
  cuatro arranque y 16 puente KDE, sintaxis/diff OK. ASan detect_leaks=0. Evidencia completa
  BREEZE_R4_STATE_PROFILE_RESULTS.json con logs/hashes; informe/guía/arquitectura/plan al día.
* Sin reboot/corte de energía ni garantía de filesystem. R4 pendiente de autoridades/selección/
  activación/fallback diarios, servicios/controladores sin adaptar, Hyprland/escala/skins y
  KNS remoto. IPC denegado; sin perfil ni registro en estado/sesión real, cambios de skin/panel,
  reinicios, instalación productiva, plugins/efectos, dependencias nuevas, commit/push o R5.

### 197. R4: consulta fresca y disponibilidad del marco antes de activación (2026-11-14)

* Se identifica que el ack de skin sólo acredita aplicación de la orden, no un primer
  fotograma. Se prepara ese requisito previo sin seleccionar/activar un perfil diario.
* PanelViewHost.presentationState comprueba carga QML, visible/exposed, frame Qt y error
  de scene graph. beforeRendering/frameSwapped usan generaciones atómicas compartidas:
  ocultación/reaparición, tamaño/salida, superficie o invalidación retiran disponibilidad;
  un swap tardío de una generación anterior no confirma la nueva. Los callbacks de render
  no acceden a miembros derivados/QML al destruir la vista. Error requiere recrearla.
* PanelRuntime.readiness agrega vistas y vuelve a comprobar salidas al consultar. Distingue
  renderReady de replacementReady (false); lista los bloqueos, incluidas reservas ausentes
  y validación de sesión. Un frame Qt no acredita presentación física, servicios ni aspecto.
* RuntimeControl añade status sin setSkin/relectura/recreación. panel-session.py status exige
  ack de revisión nueva con token/contrato/timeout; PID vivo/ack antiguo no bastan. Sin registro
  devuelve active=false sin crear archivos; contrato antiguo rechazado. No se añade watcher
  por panel ni escrituras por frame, selector sin consumidor o control del compositor.
* Test nuevo Qt usa marco nativo/software: primer frame real, vista oculta, swap tardío y
  error de render inyectados, salida retirada y skin inactiva. CLI/publicador reales consultan
  Qt conservando la vista/skin; driver comprueba respuesta en hijo/envoltorio sin salida.
* CTest normal 2/2, ASan 2/2, 38 resultados UI por paquete; control Python
  20, migración 18 y manifiestos 7 OK, sintaxis/diff/cmp OK. Primera ejecución ASan con LSan
  por defecto falla por ptrace; final completa con detect_leaks=0 como en las anteriores.
  BREEZE_R4_READINESS_RESULTS.json conserva drivers/logs/hashes; guía/arquitectura/plan e
  instrucciones/procedencia actualizados. Fixtures fuera de /tmp retirados.
* Hyprctl sigue denegado (Couldn't open a socket (1)). R4 pendiente de selección/activación/
  fallback y autoridades diarios, reservas/backends, Wayland/escala/skins y KNS remoto. No se
  registra prueba real ni se cambia panel/skin, compositor, sombras, plugins ni servicios;
  sin dependencias nuevas, instalación, reinicios, commit/push o R5/R7.

### 198. R4: política nativa de visibilidad y peticiones de reserva LayerShellQt (2026-11-14)

* Usuario autoriza explícitamente alterar su sesión cuando sea necesario en este proyecto.
  No pedir otra confirmación por ese motivo; sockets siguen denegados en este entorno.
* --native-policy del envoltorio activa sólo el ensayo registrado --follow-skin (paquete o
  perfil). Limpia BWM_R4_NATIVE_PANEL_POLICY heredada cuando falta la opción. No hay selector,
  autostart ni retirada de la barra diaria; modo común conserva política sin reservas.
* PanelViewSettings añade panelVisibility 0/3 sólo con esa capacidad. Lee la clave global
  y fallback antiguo por resolución; escribe sólo global, conserva desconocidas y verifica
  concurrencia/fallback, kdedefaults/inmutabilidad. AutoHide/Dodge y longitud excesiva se
  rechazan sin escribir. Un perfil NormalPanel necesita la opción también al reabrirlo.
* BwmSurface conecta NormalPanel con setExclusiveZone(grosor), excluyendo padding flotante
  como Plasma 6.7.5; WindowsGoBelow/ocultación/skin retiran la petición. Usa borde + ambos
  anclajes perpendiculares/margen final para preservar longitud sin requerir protocolo v5.
  Superficie que no cabe marca error y retira petición. Un panel nativo por salida;
  duplicados bloqueados explícitamente hasta coordinar disposición/apilamiento.
* Capability/status distingue petición y zona solicitada de reserva/Wayland verificados
  (false); error de política bloquea renderReady. replacementReady sigue false, reservado
  positivo pendiente de aceptación real no implica retirar la barra existente.
  Guard de QScreen esperado retira/oculta antes del remapeo de respaldo de Qt; el runtime
  recrea por descripción. Test de cambio de salida comprueba que no reserva la ajena.
* Fuentes plasma-workspace/layer-shell-qt 6.7.5 reextraídas de /var/cache/distfiles y hashes
  registrados. No copia de implementaciones/dependencias nuevas. Guía de actualización,
  arquitectura/resultados/plan/procedencia e instrucciones sincronizados.
* Qt/software prueba cuatro bordes, flotación, retiro, clave/formato nativo, dos instancias/
  salidas, conflicto, ciclo de skins y nuevo proceso con conectores cambiados; wrapper real
  comprueba opción explícita pese a variable heredada y parada limpia. Resultados finales
  en BREEZE_R4_RESERVATION_RESULTS.json. No certifica protocolo enviado/compositor real.
  Final normal/ASan 2/2, 41 resultados UI por paquete y 18 de superficie por compilación;
  Python control 20, migración 18 y manifiestos 7 OK. ASan detect_leaks=0; sintaxis/diff/cmp
  correctos y fixtures de estado fuera de /tmp retirados.
* R4 pendiente de reserva/posición/área útil y coexistencia de paneles en Hyprland, autoridades/
  activación/fallback diarios, backends, escala/skins y KNS remoto. No prueba registrada real,
  cambios de panel/skin, plugins, efectos, servicios, reinicios, instalación, commit/push o R5/R7.

### 199. R4: diagnóstico acotado de acceso a la sesión (2026-11-14)

* Usuario pide continuar e intentar conseguir acceso al sistema. UID/entorno/metadata
  confirman firma presente y sockets existentes/propios; hyprctl no abre la conexión.
  Intento documentado de elevación de lectura rechazado automáticamente por política
  Granular (sandbox_approval/rules/request_permissions=false). No es falta de permiso
  del usuario; no sortearlo mediante otros runtimes/terminales/puentes.
* Nuevo skins/plasma/scripts/r4-session-check.py para ejecutar en terminal normal del
  usuario: consultas hyprctl monitors/layers y status del auxiliar, timeout 3 s por hijo,
  salida inmediata cuando falla IPC, informe privado atómico con datos filtrados.
  Sin dispatch, lanzadores de ventanas, reinicios ni configuraciones de usuario.
* No guarda títulos/direcciones de clientes, firma de instancia ni capas ajenas al auxiliar.
  Sockets se inspeccionan como metadata; sólo hyprctl intenta la conexión normal. Reporta
  acceso/observaciones separadamente de área útil/cierre R4 (siempre no certificados).
* Diez tests nuevos y 20 del publicador OK. Diagnóstico real aquí ipc-unavailable y sockets
  presentes/propios; evidencia BREEZE_R4_ACCESS_RESULTS.json. README/resultados/plan al día.
  No se modifica C++ ni se repite su matriz, no hay nueva prueba gráfica ni cambio de sesión.
* Próximo paso dependiente: usuario ejecuta el único comando documentado en su terminal
  para observar acceso fuera de este ejecutor restringido. No hay bypass/autorización nueva
  ni cierre de R4, instalación, R5/R7, commit/push o cambio de compositor.

### 200. R4: acceso local confirmado y runner temporal de reservas (2026-11-14)

* Usuario aporta access-ok-no-native-preview. Lectura del JSON local confirma dos salidas
  a escala 1 y reserva inferior 44 px en ambas; ninguna capa/prueba R4 activa. No implica
  acceso desde el ejecutor restringido ni aceptación del anfitrión nuevo.
* Nuevo r4-reservation-smoke.py --run --output descripción exacta: un comando en terminal
  local ejecuta envoltorio/ejemplo KDE aislado con política nativa, espera frame/capa y mide
  antes/durante/después. Cierre automático por parada/flush/Ctrl+C; plazo acotado y escalado
  de señales sólo al grupo creado por este runner si no responde. No toca ventanas/skins.
* Evalúa delta inferior exacto, salida/capa/petición, resto de bordes/salidas sin cambios,
  geometría/escala iguales y recuperación completa. No certifica maximizado/área real/R4
  completos; cambios externos concurrentes y equivalencia visual no quedan resueltos.
* Diez tests nuevos con procesos simulados y regresiones Python; parts/guía/resultados/plan
  y procedencia actualizados. BREEZE_R4_RESERVATION_SMOKE_RESULTS.json. El ensayo real aún
  lo debe lanzar el usuario desde su terminal; no se ha lanzado desde otra herramienta para
  saltar las restricciones. Sin cambios C++, reinicios, instalación, R5/R7 o commit/push.

### 201. R4: ensayo local sin salida coincidente y Qt Wayland sin serie (2026-11-14)

* Usuario aporta timeout de frame/capa. JSON local confirma auxiliar registrado/respondiente,
  skin plasma/política nativa, pero output-unavailable y ninguna petición/capa. Cierre 130,
  registro retirado y reservas inferiores 44 px en ambas salidas, iguales al inicio.
* Fuente qtbase 6.11.2 de Portage: QWaylandScreen implementa fabricante/modelo desde
  wl_output y no serialNumber. Matcher anterior de descripción larga exigía sufijo con
  serie Qt; ahora admite fabricante/modelo completos + un campo de serie añadido si Qt
  carece de ella y sólo hay una coincidencia. Duplicados/fabricante/modelo distintos/serie
  conocida diferente se rechazan. No verifica serie ausente ni sustituciones de equipo idéntico.
* Readiness añade qtPlatform/availableOutputs/serialAvailable y geometría; conector sólo
  diagnóstico. Runner distingue falta de salida de timeout genérico; conserva inventario.
  Recompilado el binario normal para el siguiente ensayo local, sin plugin/reinicio.
  El runner de sesión fija QT_QPA_PLATFORM=wayland sólo en su hijo; no hereda selección
  xcb/offscreen del terminal. Los tests aislados de Qt siguen usando offscreen/software.
* Tests ampliados de identidad con descriptores LG/MSI y serie Qt vacía; inventario GUI y
  matriz normal/ASan, regresión Python y hashes en BREEZE_R4_OUTPUT_MATCH_RESULTS.json.
  Falta repetir prueba real: plataforma/identidades Qt reales y reserva aplicada pendientes.
  Sin ejecución gráfica nueva desde el asistente, R5/R7, instalaciones, commit/push.

### 202. R4: coma en fabricante MSI confirmada por inventario Qt real (2026-11-14)

* Usuario repite ensayo; nuevo JSON confirma qtPlatform=wayland, fabricante Qt MSI
  «Micro-Star Int'l Co., Ltd.» vs descripción Hyprland «Micro-Star Int'l Co. Ltd.».
  Modelo igual y serie Qt vacía. La coma que sólo tiene Qt explica la selección rechazada
  tras corregir el sufijo de serie. Cierre 130, registro/capas retirados y 44 px originales.
* OutputIdentity compara el prefijo completo del fabricante ignorando sólo comas, con
  modelo completo literal y sufijo de un campo cuando falta serie Qt. No cambia otros
  signos, modelo/serie, conectores ni rechazo de ambigüedad o series Qt conocidas distintas.
* Tests con el fabricante real exacto, ambas direcciones, duplicados y negativos de modelo/
  fabricante. Matriz normal/ASan y hashes en BREEZE_R4_MAKER_MATCH_RESULTS.json; binario normal
  recompilado para repetir el mismo comando local. Documentación e instrucciones sincronizadas.
* No se afirma reserva aplicada: falta nuevo ensayo real. Sin prueba Wayland lanzada por el
  asistente, cambios de compositor/panel diario, plugin/reinicio, R5/R7, commit/push.

### 203. R4: reserva real del panel temporal confirmada por usuario en Hyprland (2026-11-14)

* Usuario repite ensayo: reservationDeltaVerified=true, errors=[]. Informe leído y conservado
  en BREEZE_R4_RESERVATION_SESSION_RESULTS.json con origen de ejecución local del usuario.
* MSI escala 1: reserva inferior 44→92→44 px; petición del panel 48 px, capa nativa 640×48
  en (0,2068), sobre la barra existente. LG conserva 44 px. Frame/exposición/QML confirmados
  por auxiliar Wayland, envoltorio termina 130 tras su parada automática, sin registro/capas
  ni reserva residual. Se verifica la limpieza completa a partir del informe.
* Aceptación limitada a MSI/borde inferior/escala 1/ejemplo KDE/coexistencia. No se certifican
  posiciones publicadas Qt/popup, otros bordes/escalas/skins/paquetes ni sustitución diaria.
  Flags globales del auxiliar conservadas; el ejecutor del asistente sigue restringido.
* MaximizedWindowVerified/realAreaVerified/r4Complete siguen false porque falta medir una
  ventana propia maximizada. Resto de integración/autoridades/backends/KNS pendiente.
* Sólo evidencia/documentación, sin cambios de runtime, pruebas de código repetidas, plugin,
  reinicio, instalación, R5/R7, commit/push.

### 204. R4: preparación del ensayo de maximizado con ventana propia (2026-11-14)

* --maximize añade fixture Qt normal al runner de reserva, app_id aleatorio, timer 60 s y
  raíces auxiliares privadas. C++ --maximize-fixture exige identidad válida/raíces temporales;
  no ejecuta QML de paquetes ni maximiza desde el cliente (Hyprland suprime esas solicitudes).
* r4-maximized-check.py selecciona sólo PID vivo/clase/dirección propios y llama a
  kwin-window.py --pid para colocar/restaurar/maximizar. Esperado calculado independientemente
  desde geometría/reserved; escala 1/giro 0, marco observado completo, 1 px de tolerancia.
  Exige registro breezebars-csd propio con bordes coherentes; sin autoridad no certifica.
* Compara maximizado explícito con panel y después sin panel. Observa el reajuste automático
  antes de volver a maximizar y lo registra separado; no promete que funcione. Flags área/
  maximizado sólo pasan con medidas explícitas/reserva/limpieza; r4Complete sigue false.
* Cleanup restaura/cierra sólo fixture y retira su presnap con API común; excepciones guardan
  fallo y ejecutan cleanup. Sin cambios de ventanas ajenas/skin/plugin/compositor ni servicios.
* Normal/ASan CTest 2/2, 41 UI por paquete, 18 superficie y ciclo fixture offscreen; Python
  R4 67 y manifiestos 7 OK, sintaxis/diff/cmp. ASan detect_leaks=0. Evidencia de preparación
  BREEZE_R4_MAXIMIZED_PREP_RESULTS.json; no hay nueva validación Wayland del asistente.
* Usuario debe lanzar el mismo runner con --maximize en su terminal; no se sortea el sandbox.
  Sigue pendiente maximizado real/resto R4. Sin instalaciones, reinicios, R5/R7 o commit/push.

### 205. R4: contrato CLI de to-screen corregido y fallos parciales separados (2026-11-14)

* Usuario ejecuta --maximize y obtiene error vacío. Informe confirma panel/reserva MSI
  44→92→44, pero ninguna medición del marco. Runner enviaba ADDRESS MONITOR; el parser real
  de kwin-window exige MONITOR [ADDRESS] y devolvía 1 sin stderr al buscar esa dirección.
  Fixture termina -15, panel 130, registro/capas retirados y reservas originales recuperadas.
* Fixture.start pasa ahora por command('to-screen', 'desc:'+output), conservando PID/clase/
  dirección verificados. Regresión usa start + argparse real + PID guard, sustituyendo sólo
  operaciones externas; antes habría fallado con los argumentos invertidos.
* Errores incluyen acción/exit code y stdout/stderr o texto si no hay salida. Si falla la
  medición, runner reevalúa reserva antes/durante/después tras limpiar y no borra un delta
  válido; maximizado/área real siguen false y --maximize devuelve fallo.
* Python R4 69 y tests del gestor/manifiestos OK; sintaxis/diff/cmp correctos. Evidencia
  BREEZE_R4_MAXIMIZED_CLI_RESULTS.json. Sin cambios C++ ni repetición de su matriz.
* Falta repetir mismo comando local: no se afirma marco real verificado, reinicio/plugin,
  servicios, R5/R7, instalación, commit/push o acceso ampliado del ejecutor.

### 206. R4: marco maximizado real correcto; reajuste automático pendiente (2026-11-14)

* Usuario ejecuta --maximize corregido: delta/maximizado/área real true, dinámico false y
  sin errores. Informe leído/conservado en BREEZE_R4_MAXIMIZED_SESSION_RESULTS.json, con
  origen de ejecución local del usuario; no supone acceso del asistente al compositor.
* MSI escala 1/giro 0: con panel marco esperado/observado (0,720,2560,1348); tras retirar
  y maximizar de nuevo (0,720,2560,1396). Modo 3 y decoración propia 28 px confirmados.
  Límite inferior coincide con capa/panel real. Reserva 44→92→44, LG inalterado, cierre
  panel 130/fixture -15 y sin registro/capas residuales.
* Sin nuevo maximizado conserva 1348 en vez de 1396: deja 48 px sin usar. Seguimiento
  automático de área útil pendiente; añadir panel sobre ventana ya maximizada no probado.
  No certificar lo dinámico con el éxito explícito ni ampliar aceptación a otras escalas/
  bordes/skins/backends o a sustitución diaria. R4 sigue abierta.
* Sólo evidencia/documentación; sin runtime, tests de código repetidos, reinicio/plugin,
  instalación, R5/R7, commit/push.

### 207. R4: seguimiento de área útil en el puente existente; ensayo dinámico preparado (2026-11-14)

* Responde al fallo real de §206: kwin_area.py observa monitores/clientes desde el watch
  único de kde-config-bridge, no crea otro demonio/servidor. Usa reserved real y matemáticas
  BWM de marco/contenido con bordes propios de breezebars-csd por dirección/PID.
* Sólo ejes bwm-max-v/h de ventanas flotantes normales; excluye fullscreen, especiales,
  minimizadas, snapping y opt-outs. Respeta Force KDE de geometría y bloqueo de transición.
  Lua vuelve a validar PID/monitor/skin/estado/etiquetas antes de resize/move. No modifica
  restore, presnap, etiquetas, foco ni workspace. Escala/giro calculados en unidades lógicas.
* Poll agrupado 0,5 s, consultas/dispatch 2 s, hasta 16 ventanas en una petición, tres
  intentos por firma con confirmación de geometría. Sin recargas por cada evento ni lucha
  ilimitada contra reglas. El baseline privado incluye PID/inicio y fecha; no certifica efecto.
* restart recarga sólo el puente por su ciclo existente; --refresh-area-watcher exige
  marcador fresco/privado y proceso vivo antes del ensayo. Queda activo para máximos BWM
  existentes. El runner crea/maximiza primero su fixture, mide al aparecer/retirar el panel
  sin remax, y conserva por separado las medidas explícitas. Limpieza en todos los fallos.
* 159 tests Python: R4 89, puente 18, reglas 18, ventanas 13, manifiestos 7, arranque 4,
  ajustes R3 10. Incluye Lua real con API simulada, batches, PID reutilizado, ambos sentidos,
  ejes, Force/opt-outs/transición, confirmación/reintentos y orden refresh→fixture→panel.
  Evidencia/hashes: BREEZE_R4_AREA_TRACKING_RESULTS.json. No cambios C++ ni repetir su matriz.
* El ejecutor sigue sin IPC real: no ha recargado el puente ni validado el nuevo comportamiento
  en sesión. Repetir comando local con --refresh-area-watcher. R4 permanece pendiente junto
  con aceptación restante/autoridades/backend/KNS; sin R5/R7, instalación, commit o push.

### 208. R4: reajuste automático real al aparecer y retirar el panel validado (2026-11-14)

* Usuario ejecuta --run --maximize --refresh-area-watcher en su terminal Hyprland. El
  runner confirma baseline fresco del puente y devuelve reserva/maximizado/dinámico/área
  real true, errors=[] y r4Complete=false. Informe completo guardado con hash/origen en
  BREEZE_R4_AREA_SESSION_RESULTS.json; hashes de las nueve fuentes de §207 aún coinciden.
* Se reevalúa reserva con la función pura del runner y se contrastan las cinco medidas:
  antes marco (0,720,2560,1396), al aparecer panel sin remax (0,720,2560,1348), explícito
  con panel igual, al retirarlo sin remax (0,720,2560,1396), explícito final igual. En
  todas modo 3, decoración autoritativa y borde superior 28 px confirmados.
* MSI inferior escala 1/giro 0: reserva 44→92→44, capa nativa 640×48 en (0,2068). LG
  mantiene 44 px; no equivale a maximizado probado en LG. Panel termina 130 y fixture -15,
  sin capas/registro residuales. Resuelve el fallo dinámico observado en §206 para este caso.
* Sin nuevas órdenes gráficas del asistente ni cambios de runtime/repetición de tests.
  R4 sigue abierta por integración diaria/backends/autoridades/KNS y aceptación restante:
  ejes parciales, otros bordes/escala/salidas, hotplug y cambios de skin no se deducen del
  ensayo. Sin avance a R5/R7, sustitución del panel, instalación, commit o push.

### 209. R4: «Obtener nuevos» real y puerta con widgets no conocidos de antemano (2026-11-14)

* Usuario pide continuar R4 desde el traspaso a Claude. Esta ejecución tiene acceso a Hyprland y
  red. Build anterior en /tmp perdido: recompilado en scratchpad con libplasma 6.7.5 de Portage.
* kns.cpp: búsqueda/instalación/retirada sin diálogo con KNSCore 6.29 y plasmoids.knsrc (mismos
  Entry/Transaction que el diálogo), sólo raíces XDG temporales, preguntas siempre Cancelar/No,
  alta/baja en el catálogo vivo. kns-cycle.py elige por orden de descargas de la tienda (excluye
  Andromeda), rechaza antes de cargar binarios/scripts/fuentes executable (filtro estático),
  ejercita la opción booleana propia, relee en proceso nuevo y retira por KNS.
* Corregido: páginas con cfg_ sin esquema (Thermal Monitor) se bloqueaban y saveConfig() también;
  ahora como AppletConfiguration.qml 6.7.5 (sólo config.keys(), saveConfig() antes de Aplicar).
  Fixture tests/callback-config y regresión KNS fuera de raíces temporales en check-isolated.
  Diálogo/vista con Kirigami.Theme.backgroundColor (el alfa de §187 los dejaba transparentes).
* Tienda (12 primeros sin Andromeda): 3 superan (Thermal Monitor pinned, Modern Clock show_day,
  Simple Application Launcher paneSwap), 6 con metadatos antiguos que KPackage 6.29/Plasma 6.7.5
  tampoco listan, 3 rechazados por ejecutar órdenes. Todos retirados por KNS.
* Sesión Hyprland (LG por descripción): Modern Clock descargado, «Configure…» abre su página
  original, uinput desmarca Show Day, Aplicar escribe show_day=false en el appletsrc nativo.
  Limpieza completa, puntero/foco devueltos. CTest normal/ASan 2/2 (detect_leaks=0), 96 Python.
  Evidencia BREEZE_R4_KNS_RESULTS.json; resultados/arquitectura/plan/README/procedencia al día.
* Criterios originales de R4 cumplidos. Fuera de su puerta y pendientes: panel diario
  (replacementReady=false), backends tareas/escritorios, otras escalas/bordes/skins, desenfoque,
  widgets que ejecutan órdenes, diálogo KNS gráfico en sesión. Sin R5/R7, commit ni push.

### 210. R4: reproducción del commit de Claude sin fuentes temporales externas (2026-11-14)

* Revisado e41c28d: conserva la puerta KNS de §209. En este ejecutor IPC continúa
  inaccesible (r4-session-check), sin nuevas pruebas gráficas ni recargas.
* Build nuevo /tmp/bwm-r4-build. CTest registra siempre isolated-local-configuration,
  además de superficies: tres fixtures propios, callbacks/saveConfig, dos instancias,
  páginas compartidas/módulo, lectura en otro proceso, catálogo y retirada. El fixture
  de sesión se prueba también con org.kde.panel original offscreen. Sin red/bus/sesión.
* Runner de sesión usa ahora ese build convencional y shared-config del repo por defecto,
  sin extracción upstream antigua en /tmp. Paths en el informe; overrides conservados.
* Tres metadata.json necesarios no se incluyeron en e41c28d: siguen presentes sin seguimiento
  en tests/{callback-config,module-config,shared-config}. Conservarlos e incluirlos al
  versionar. No se pudo añadir al índice: .git es de sólo lectura aquí; sin commit/push.
* Evidencia BREEZE_R4_REPRO_RESULTS.json: CTest local 2/2, Python R4 89. No son la matriz
  externa/ASan previa. Restan integración diaria/backends y aceptación de sesión descritos
  en §209; sin R5/R7 ni sustitución del panel activo.

### 211. R4: inventario de backends por instancia para preparar integración diaria (2026-11-14)

* PanelSession.widgetBackends usa instancias vivas en orden nativo, conserva id/paquete,
  fallo de carga y evaluación del catálogo. Dos copias se distinguen; la retirada desaparece
  al consultar. Catalog.runtimeAssessment comparte metadatos y extensiones declaradas con
  el catálogo, mantiene desconocidos unassessed y todos operationalVerified=false.
* readiness/status incluye por panel widgetBackends, widgetBackendsVerified y alcance
  direct-panel-instances. Explica adaptador requerido, runtime sin verificar, fallo de carga
  o inventario ausente/vacío. No evalúa recursivamente bandeja ni acredita servicios por frame.
* Se preparan diagnósticos para autoridades/selección/fallback, pero esas piezas diarias y
  los backends aún no están implementados. replacementReady=false; sin retirar barra actual.
* Test real QtTest de metadatos de paquete desconocido, dos instancias/retirada, APIs conocidas
  pendientes y respuesta fresca RuntimeControl con renderReady=true pero backend sin validar.
  Incluido en CTest local. Evidencia BREEZE_R4_BACKEND_INVENTORY_RESULTS.json. Sin plugin,
  compositor, IPC de sesión, instalación, nuevas dependencias, commit/push ni R5/R7.

### 212. R4: adaptador nativo KWindowSystem hacia escritorio común BWM (2026-11-14)

* Estudiados ShowDesktop/PeekController/MinimizeAllController de plasma-desktop 6.7.5 y
  cargador/plataforma privada V5 de KWindowSystem 6.29.0 desde fuentes de Portage. El
  controlador nativo usa KWin D-Bus si existe, o KWindowSystem como fallback. Minimize All
  secundario depende de TaskManager; no se dan ambos por implementados.
* windowsystemplugin es estático dentro del auxiliar, nunca plugin Hyprland/global. Delega
  activación/tokens/exports/efectos/sombras al plugin KDE instalado; sólo showingDesktop
  tiene puente BWM opt-in. DesktopBridge serializa/coalesce peticiones asíncronas, espera
  fin del gestor, timeout 5 s y lee estado común validado con poll 250 ms sin otro watcher.
* Gestor común admite enter idempotente sin alterar toggle/leave anteriores. No se duplica
  servidor D-Bus ni compositor. La acción usa minimizar/restaurar existente: no implementa
  efectos Peek/R7 ni modelo de tareas. Evaluación del widget sigue sin certificar.
* preview-isolated acepta --builtin para paquetes compilados y --desktop-actions sólo con
  --follow-skin/Breeze/IPC accesible/runtime privado; fuerza Wayland. Probes normales,
  export y drivers KNS/offscreen eliminan esos flags. Panel diario intacto.
* QtTest carga plugin/controlador ShowDesktop originales instalados: dos instancias cambian
  estado por KWindowSystem y ejecutan el gestor Python real contra un hyprctl de fixture sin
  IPC. Comprueba restauración y estado común finales; JSON/entradas/alias inválidos rechazados.
  Evidencia BREEZE_R4_DESKTOP_ADAPTER_RESULTS.json. No equivale a ventana real de sesión.
* CMake exige KWindowSystem 6.29.0 EXACT/headers privados; requisitos/tablas actualizados.
  Activación/gráficos Wayland del delegado, TaskManager/secundario, Peek, integración diaria
  y resto de aceptación siguen pendientes. No hay instalación, plugin en caliente o commit.

### 213. R4: ejecutable de sesión en ruta estable y preflight de arranque (2026-11-14)

* Usuario activa Breeze, pero el siguiente ensayo falla con FileNotFoundError del binario
  /tmp/bwm-r4-build. No llegó a crear el auxiliar ni ejecutar acciones de escritorio.
* Build completo nuevo en build/bwm-plasma-host dentro del repo, con exclusión específica
  en .gitignore. Runner de reserva y ejemplos README usan esa ruta; --binary explícito se
  conserva. No se asume disponibilidad de /tmp entre ejecutores/terminales.
* Preview normaliza y comprueba archivo ejecutable antes de leer skin/acceder a IPC; si
  falta, explica cmake/configurar/compilar y --binary. Captura además errores de exec/loader.
* CTest local 2/2 y dos pruebas nuevas de arranque pasan (ausente/no ejecutable e intérprete
  de ejecutable inexistente), sin acceder a la sesión. Evidencia BREEZE_R4_STABLE_BINARY_RESULTS.json.
  Sin recompilar plugins Hyprland, reinicios, acciones nativas reales, commit/push o R5/R7.
* Repetir ensayo con --binary /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host/bwm-plasma-host.
  Adapter sigue pendiente de sesión; perfil diario/backends/Peek continúan según §212.

### 214. R4: botón nativo minimiza y restaura en sesión, confirmado por usuario (2026-11-14)

* Usuario ejecuta preview estable con builtin showdesktop/desktop-actions, MSI por descripción.
  El log confirma registro. Preguntado expresamente por pulsar y volver a pulsar el botón,
  confirma «si»: ventanas minimizadas/escritorio visible y luego restauradas.
* Evidencia manual, no telemetría de ventanas: BREEZE_R4_DESKTOP_SESSION_RESULTS.json. No se
  deducen geometría/foco/z-order exactos, ambas instancias, matriz de monitores ni limpieza
  instrumentada. No hubo acciones gráficas nuevas del asistente ni cambios de runtime.
* Avisos pegados: bus aislado, TaskManager sin protocolo, Toolbox y sombras de ToolTipDialog.
  Sombras/TaskManager/Peek y la integración diaria siguen pendientes. No se cambian los
  flags generales operationalVerified/replacementReady ni se declara R4 completa.

### 215. R4: fuente de ventanas BWM dentro del modelo nativo TaskManager (2026-11-15)

* BwmTaskSource hereda AbstractWindowTasksModel de LibTaskManager 6.7.5 EXACT, sin copiar
  bibliotecas ni su QML. BwmTaskBridge recorre proxies Qt/concatenación y usa setSourceModel
  público sobre WindowTasksModel nativo; conserva agrupado/filtros/orden y restaura fuente
  previa al retirarse. Fuentes personalizadas de terceros se dejan intactas.
* native-tasks.py aporta snapshot acotado clients/activewindow/monitors y acciones por gestor
  BWM existente: foco, minimizar/restaurar, maximizar, cerrar. Revalida dirección/PID/inicio,
  mapeo/origen y Breeze antes de llamar; no acepta exec arbitrario. Origen especial/normal y
  estados minimizados usan las funciones comunes. Apps/iconos/launch URLs por TaskManager.
* Índices/UUID estables en cambios de datos; se invalidan al desaparecer o cambiar identidad.
  Sólo roles cambiados se notifican para conservar índices persistentes y activeTaskChanged.
  Unsupported capabilities false donde existen roles; menús sin tales roles aún deben adaptarse.
* Un proveedor por host, poll 750 ms mientras hay modelos enlazados, un snapshot y una acción
  simultáneos, colas limitadas/timeout 8 s/grupos propios. No hay nuevos servidores/watcher.
  --task-actions es opt-in de preview/Breeze/Wayland/IPC; resto de probes/KNS limpian flags.
* status incluye taskSource (contadores, snapshotAvailable, lastError, scope window-model-only).
  operatividad global sigue false. VirtualDesktopInfo/pager, minimizar-todo secundario, menús,
  new-instance/URL-drop/move/resize/otras acciones y geometría de delegados pendientes.
* QtTest prueba dos TasksModel auténticos con datos/acciones comunes e IPC falso, índices
  persistentes, cierre/reaparición, retirada de vistas, restauración de fuente y terceros.
  En offscreen StartupTasksModel carece de backend/columnas: el test le suministra una tabla
  vacía de una columna; esto no se hace en producción ni prueba delegados QML Wayland.
* Evidencia BREEZE_R4_TASK_SOURCE_RESULTS.json, compilación normal/ASan y regresión Python.
  Sin pruebas nuevas en sesión ni cambios en la barra diaria, plugins Hyprland o compositor.
  R4 sigue abierta por backend de escritorios/menús y las autoridades diarias; sin R5/R7.

### 216. R4: transacciones de los adaptadores nativos y barrera de retirada (2026-11-15)

* Revisión del contrato VirtualDesktopInfo 6.7.5: datos de sólo lectura, métodos no virtuales,
  backend estático privado y sin factoría pública de proveedores. A diferencia de la fuente
  WindowTasksModel, no se puede usar setSourceModel. No se toca ese puntero ni se interponen
  símbolos KDE; proveedor de escritorios/filtros/menús sigue pendiente, no imposibilidad universal.
* native_guard.py (propio, stdlib) añade flock compartido por tareas/Mostrar escritorio del
  auxiliar: runtime canónico privado, descriptor de directorio, O_NOFOLLOW/CLOEXEC, archivo
  regular propio 0600 sin enlaces, espera máxima 1 s. Nunca borrar el lock para desbloquearlo;
  la muerte del propietario libera el descriptor. No crea demonio ni formato de preferencias.
* kwin-window --native-serialized envuelve sólo las entradas experimentales permitidas.
  Relee Breeze y cliente después de esperar; --expected-generation comprueba inicio Linux
  además del PID. El helper de tareas pasa ambos; el adaptador de escritorio recibe también
  el XDG_CONFIG_HOME real. Las entradas diarias sin flag conservan su comportamiento.
* PanelRuntime suspende ambos puentes antes de salir de Breeze/parar. Descarta lo aún en
  cola, cancela sólo consultas de lectura y deja terminar la mutación en curso. RuntimeControl
  reintenta sin ack/revisión nueva hasta quedar inactivo; no bloquea GUI ni usa loop anidado.
  Si tarda más que el publicador/hook, el gestor común aborta antes de cambiar perfiles y
  su hook after vuelve a habilitar la skin anterior. No se amplían sus timeouts.
* Estado: nativeActionsQuiescing; tareas añaden suspended/actionInFlight/snapshotInFlight/
  quiescent. Este último sólo describe sus procesos/cola, no el compositor o todos los gestores.
  No afirma rollback si se agota un timeout o se termina a la fuerza el auxiliar.
* QtTest nuevo ejercita RuntimeControl→PanelRuntime→ambos puentes: falta de ack mientras
  mutan, cola descartada, finalización antes de ack y reanudación. Regresión Python prueba
  contención entre procesos, skin/generación cambiadas mientras esperan, permisos/enlaces
  rechazados y liberación tras muerte sin reemplazar el inodo.
* Evidencia BREEZE_R4_NATIVE_TRANSACTIONS_RESULTS.json: CTest normal/ASan y suites Python.
  No hay prueba nueva de sesión ni sustitución diaria. Falta proveedor de escritorios,
  menús/acciones, coordinación con llamadores diarios, Wayland y autoridades diarias; sólo R4.

### 217. Breeze: congelación de popups de la bandeja, tooltips `ToolTipDialog`, `follow_mouse = 2` y primer clic en CSD (2026-11-15)

* **Popups de bandeja/reloj congelados tras abrir (`TrayPopup.qml`, `AppletItem.qml`, `StatusNotifierItem.qml`, `Panel.qml`, `PanelState.qml`):** `TrayPopup.qml` activaba `HyprlandFocusGrab` en el mismo ciclo al abrir antes de mapearse la superficie `xdg_popup`, bloqueando el puntero/clics dentro del desplegable. Diferido 50 ms con `grabReady` + `grabTimer`; `AppletItem.qml` (`active: !tray.expanded`) y `StatusNotifierItem.qml` (`active: !tray.expanded && inVisibleLayout`) desactivan áreas de hover mientras la bandeja está expandida, y `Panel.qml`/`PanelState.qml` extraen `forceShown` con guarda no-op en `update()`.
* **Tooltip centrado y fallo del primer clic en iconos del panel/bandeja (`PlasmaCore.ToolTipArea`):** `AbstractItem.qml`, `ExpanderArrow.qml` y `ShowDesktopButton.qml` instanciaban `PlasmaQuick::ToolTipDialog` (`org_kde_plasma_shell`), que sin protocolo Plasma en Hyprland aparecía centrado en pantalla y estorbaba al primer clic sobre los iconos del panel/bandeja. Creado `config/quickshell/ii/modules/plasma/theme/ToolTipArea.qml` (exportado en `qmldir`) basado en `HoverHandler { acceptedButtons: Qt.NoButton }`, retardo `Kirigami.Units.toolTipDelay` y `PopupWindow` no enfocable con estilo `KSvg.FrameSvgItem` (`solid/dialogs/background`); `ShowDesktopButton.qml` oculta además el tooltip al pulsar. Comprobado con grep cero usos restantes de `PlasmaCore.ToolTipArea` en `modules/plasma/`.
* **Scroll sin clic previo en ventanas inactivas (`misc.lua`, `kwin.lua`, `settings-capabilities.json`, `docs/BREEZE_ARCH.md`):** `input:follow_mouse = 0` impedía que Hyprland enviara `wl_pointer.enter` al pasar el ratón por ventanas sin foco (Firefox no recibía scroll hasta hacer clic). En Hyprland 0.56 `ClickToFocus` debe mapear a `follow_mouse = 2` (el cursor/scroll sigue al ratón sin robar foco activo hasta el clic; `FollowsMouse` conserva `1`).
* **Primer clic/arrastre ignorado en CSD oculto (`src/breezebars/barDeco.cpp`):** al hacer clic en los 50 px superiores fuera de los últimos 140 px (`if (m_hidden)`), el hook `mouse.button` llamaba a `fullWindowFocus` y `raise` antes de `CInputManager::processMouseDownNormal`; al ver que `focusState()->window()` ya coincidía con la ventana bajo el cursor, Hyprland omitía `setPointerFocus` y entregaba el primer `BTN_LEFT` a la ventana previa. Eliminadas ambas llamadas en ese paso pasante y reinstalado `config/hypr/plugins/breezebars.so` de forma atómica con `make install`.
* **Comprobado:** 45 pruebas en verde (`BWM_RUN_QML_TESTS=1 python3 -m unittest tests.test_kde_config_bridge tests.test_plasma_tray tests.test_plasma_panel_native tests.test_plasma_task_input tests.test_breezebars -v`, incluidos los nuevos regresivos de `follow_mouse` en `lua5.4` y `ToolTipAreaTests`); `hyprctl reload` + `bwm-theme-manager.py set plasma --restart-shell` sin errores de configuración ni errores QML en `/run/user/1000/quickshell-session.log`, y `hyprctl getoption input:follow_mouse` devuelve `int: 2`.
* **Pendiente manual del usuario:** el cambio C++ de `breezebars.so` está instalado atómicamente pero no recargado en caliente (regla de Hyprland); entra en vigor en el compositor tras reiniciar la sesión de Hyprland. Faltan pruebas manuales interactivas del usuario sobre popups de bandeja, tooltips, scroll sobre Firefox sin clic y arrastre inmediato entre ventanas tras dicho reinicio.

### 218. R4: protocolo nativo de escritorios para consumidores originales KDE (2026-11-15)

* DesktopProtocol v4 en src/bwm-plasma-desktops, sobre el display existente del compositor,
  sin servidor de sesión/D-Bus nuevo, plasmashell ni cambios privados a VirtualDesktopInfo.
  XML plasma-wayland-protocols 1.23.0 fijado por SHA256 y generado con wayland-scanner.
* Proyección de contador común válido + escritorios vivos/activos, con nombres e IDs BWM
  estables; excluye especiales y antiguo 99, conserva los reales que superan el contador.
  Si el config no es legible, no inventa el contador. No escribe preferencias ni layouts.
* Núcleo valida antes de publicar, agrupa con done, envía estado por salida y retira recursos
  de IDs eliminados. Qt/KDE original prueba activación, nombres, filas, posiciones, retirada
  y recreación. Solicitudes create/remove denegadas con diagnóstico y capacidades false.
* Test Wayland por socketpair heredado/raíces XDG temporales/no bus. Fixture sin socket de
  escucha ni representación de superficies. VirtualDesktopInfo C++/QML, filtro por salida,
  orden inicial TasksModel y rol display de Instantiator (delegado de prueba) pasan; sin
  workaround offscreen StartupTasksModel ni parches KDE. No acredita Task.qml pintado.
* Frontend Hyprland opcional separado, compila con headers 0.56.2 y guarda de hash; empieza
  desactivado, no se instala/carga ni añade al arranque. Eventos coalescidos + timer 500 ms,
  acciones Config::Actions, cola acotada. Por salida sólo admite escritorio ya materializado
  y asignado al monitor, que enfoca antes de activar; no traslados/swap ni overrides de reglas.
* Ambos targets del plugin (incluido núcleo estático) usan -fno-gnu-unique. readelf confirmó
  cero UNIQUE en build/bwm-plasma-desktops/bwm-plasma-desktops.so. Makefile ofrece únicamente
  despliegue atómico futuro; no ejecutar carga/descarga en caliente. Ningún .so activo tocado.
* Dependencias declaradas, licencias XML/generados conservadas y guía de actualización en
  README/ARCH. Evidencia BREEZE_R4_NATIVE_DESKTOPS_RESULTS.json: CTest 4/4 normal y ASan,
  Python R4 103/manifiestos 7. ASan sin fugas habilitadas; no prueba de sesión nueva.
* Pendientes: frontend real/conflictos de proveedor, coordinación asíncrona con retirada
  del host (nunca flock bloqueante en hilo compositor), create/remove y gating/wrapping,
  otros menús/acciones, especiales, matriz visual/autoridades diarias. Fixture de activación
  entre salidas no demuestra traslado soportado en plugin real. R4 abierta; sólo R4.

### 219. R4: retirada coordinada del proveedor por conexión Wayland (2026-11-15)

* bwm_plasma_desktop_control_v1, contrato propio de integración sobre la conexión Qt existente.
  No altera KDE ni añade servidor/configuración de usuario. Cada conexión nace pausada y
  debe poseer control + resume para activar; lectura continúa. Otras conexiones no se pausan.
* Cola real (32) movida a DesktopProtocol y compartida por fixture/frontend. Captura recurso,
  serial de vida e ID; retirar recurso/cliente cancela trabajo, sin heredar autoridad al
  reutilizar punteros. Pause/destruir propietario cancela sólo cola propia; ack después de
  callbacks anteriores en el mismo event loop. No procesos/flock ni loop anidado en compositor.
* NativeDesktopControl Qt valida serial/estado, plazo 1 s y no acepta ack tardío tras timeout.
  Nueva revisión permite retry; reaparición exige confirmación nueva. PanelRuntime suspende
  también gestores locales y retira vistas ante pérdida; RuntimeControl espera ambas barreras
  y admite revisión inicial pendiente sin liberar el propietario. Ausencia del propio proveedor
  permite retirada/salida, bloquea entrada requerida; no se cambian deadlines del hook.
* Error encontrado por prueba al retirar global: Qt generado init(nullptr) instala listener,
  no desinicializa. Liberación local y seguimiento del proxy retirado corregidos, sin miembros
  privados, con pérdida/rebind/destrucción probados por ASan.
* --native-desktops sólo para preview --follow-skin; preflight de diagnóstico ya cargado /
  habilitado / disponible / barrera v1 y handshake real posterior. No carga ni habilita plugin.
  Probes/export/KNS limpian flag. Status informa el control sin certificar widget completo.
* Prueba C de dos clientes: sin propietario denegado, same-flush cancel, otro cliente sigue,
  destruir propietario mantiene pausa y rebind/resume funciona. Prueba Qt original añade
  RuntimeControl, pérdida/deshabilitación/reconexión y timeout con ack tardío. Sólo el fixture
  bloquea su propio loop por pipe; no se señalan ni afectan procesos/compositor del usuario.
* Evidencia BREEZE_R4_DESKTOP_CONTROL_RESULTS.json: CTest 5/5 normal/ASan, Qt Wayland 4/4
  contando init/cleanup, Python R4 105/manifiestos 7 y launcher 4. Extensión compilada aparte,
  sin instalar/cargar, sin autoinicio ni cambio del panel diario. readelf sin UNIQUE.
* Falta validar frontend/conflictos/arranque en sesión, menús/create-remove/wrapping/especiales
  y autoridades diarias. La barrera es de retirada propia, no exclusión global de todas las
  acciones BWM ni rollback de lo ya aplicado. R4 sigue abierta; sólo R4, sin R5/R7.

### 220. R4: capacidades del menú TaskManager original sin parchear KDE (2026-11-15)

* TaskMenuPolicy conserva ContextMenu.qml instalado y sus handlers. Limita el filtro Qt
  a menús de raíces registradas y modelos con marcador org.bwm.window-actions versión 1.
  Comprueba el contenido original por SHA256, incluso desde qrc; fuente no revisada o grupo
  QAction ajeno en una acción sin capacidad deshabilitan el menú afectado y registran error.
* Mantener encima/debajo y excluir captura no tienen capacidad operativa en la fuente nativa:
  se enmascaran con un QActionGroup público no exclusivo por acción. No se reemplazan los
  bindings enabled ni se parchean metadatos/QML KDE. Qt removeAction no recalcula enabled:
  reactivar la máscara propia antes de retirarla conserva el último estado explícito.
* Índices agrupados se comprueban por todos sus hijos; cambios estructurales cierran el
  menú antes de invalidar índices. Suspensión cierra menús/restaura máscaras, vida con
  QPointer y guardia de recursión; acciones de apps/menús ajenos conservadas.
* Nuevo test carga org.kde.plasma.icontasks, Task.qml y su menú originales. Minimizar
  individual y grupo de dos ventanas emiten las peticiones correctas a BwmTaskSource;
  captura/encima/debajo bloqueados, estado explícito y cierre tras retirar filas probados.
  No se añadieron operaciones de ventana: permanecen foco/minimizar/maximizar/cerrar.
* Evidencia BREEZE_R4_TASK_MENU_RESULTS.json: CTest 5/5 normal/ASan (fugas deshabilitadas),
  QtTest menú 3/3 contando init/cleanup, Python R4 105 y skins 7. Task.qml emite roles
  undefined en offscreen por backend nativo ausente; prueba del menú, no render certificado.
  El fixture StartupTasksModel sólo existe en test. Sin nueva aceptación de sesión.
* R4 pendiente: frontend/proveedor real, conflictos/arranque, restantes capacidades y
  autoridades/recuperación del panel diario. operationalVerified/replacementReady false.
  Sin activar panel diario, instalar/cargar extensión ni avanzar R5/R7.

### 221. R4: pantalla completa nativa con estado deseado y recibo del dispatcher (2026-11-15)

* BwmTaskSource publica IsFullScreenable sólo con fullscreenable booleano del snapshot:
  ausente deshabilita, tipo inválido rechaza snapshot sin cambios. El helper deriva esa
  capacidad del gestor existente para ventanas normales mapeadas/no ocultas/no fijadas, fuera de
  special:minimized, Magic/especiales y antiguo 99. No activa controles sobre almacenamiento.
* requestToggleFullScreen convierte el estado de la fila en estado deseado true/false,
  como el consumidor KDE; duplicados del mismo snapshot no invierten el resultado. Se
  transmite a kwin-window fullscreen --state on|off con PID/inicio y bloqueo nativo. La
  invocación diaria fullscreen sin opciones sigue alternando como antes.
* Después de adquirir el bloqueo se revalida identidad/skin/capacidad. El Lua de Hyprland
  vuelve a comprobar skin/PID/mapped/hidden/pinned/workspace en el event loop y usa set/unset.
  Se consulta result.ok y se relee el modo interno; sólo si coincide se devuelve recibo exacto
  por hyprctl repl, no sólo exit status. Error/recibo incorrecto/timeout falla; ninguna autoridad nueva.
* El menú KDE original individual comprueba entrada/salida y checked al reabrir; el grupo
  emite dos estados deseados. Dos TasksModel instalados ejercitan helper/gestor reales
  con IPC ficticio y el Lua generado ejecutado contra hl simulado: on/on/off termina off.
  Modelo prueba flag ausente/inválido, notificación de capacidad y rechazo sin capacidad.
* CTest 5/5 normal y ASan (fugas deshabilitadas), Python R4 113, ventanas 14, minimizar 7
  y skins 7. Lua es dependencia exclusiva BUILD_TESTING, ya resuelta explícitamente por
  CMake; no nuevo intérprete/servidor de producción. BREEZE_R4_FULLSCREEN_RESULTS.json
  conserva hashes, fuentes primarias locales, salidas/avisos y límites del ensayo.
* hyprctl version sigue sin acceso al socket en este ejecutor. Sin nueva medición física
  de fullscreen/restauración, pintado Task.qml, monitores/escalas ni aceptación Wayland.
  No cambia el panel activo ni carga plugins. R4 abierta, flags globales false, sin R5/R7.

### 222. R4: metadatos vivos del modelo nativo de tareas (2026-11-15)

* Reproducido con una base KSycoca real en XDG temporal: KDE notificaba un cambio de
  .desktop, pero BwmTaskSource retenía AppData y devolvía «First metadata» tras actualizar
  a «Updated metadata». No faltaba un snapshot: el identificador de la ventana era el mismo.
* Fuente conectada a KSycoca::databaseChanged, igual que la fuente KDE. Timer único por
  fuente de 100 ms agrupa notificaciones, invalida AppData y emite sus seis roles; resolución
  diferida por TaskTools al consultar datos. Reutiliza singleton/vigilancia KDE, sin watcher
  por ventana, reset del modelo, nuevo servidor o cambios en acciones/configuración.
* Prueba nueva con aplicación .desktop y PNG propios: dos fuentes actualizan nombre/icono,
  vacían metadatos al retirar, descubren reinstalación y conservan títulos/UUID/índices.
  Fuente destruida durante notificación y fuente vacía/reabierta seguras. Base nativa y
  señal real por archivo, sin inyectar databaseChanged ni ejecutar el Exec de la aplicación.
* kbuildsycoca6 se resuelve sólo en BUILD_TESTING; el runner elimina KDESYCOCA heredado y
  el test exige XDG/cache privados antes de crear archivos. KF6 Service ya estaba requerido.
* CTest normal/ASan 5/5, nuevo QtTest 3/3 contando init/cleanup, Python R4 113 y skins 7.
  Evidencia con fallo previo, hashes y límites en BREEZE_R4_TASK_METADATA_RESULTS.json.
  Binario estable reconstruido; AGENTS/CLAUDE y guías actualizados. Sin commit/push.
* No es catálogo KPackage, render de Task.qml, cambio de tema de iconos o aceptación real
  de Hyprland. Panel diario intacto, sin plugins nuevos cargados ni R5/R7. R4 sigue abierta
  por frontend/proveedor/capacidades y autoridades/aceptación de sesión pendientes.

### 223. R4: registro único, asociación de proveedor y recuperación del auxiliar (2026-11-15)

* NativeDesktopRegistry observa un wl_registry sobre la conexión Qt existente, con sync
  asíncrono; no crea conexión/socket/servidor. Exige un global KDE v4 y un control BWM v2.
  Control v2 añade desktop_global (nombre visible por wl_client, API Wayland >=1.22) y el
  cliente verifica que se corresponde con ese único proveedor antes de enviar resume.
* Sustituida la extensión automática del control por enlace explícito con bindings Qt
  generados y API pública Wayland. La prueba detectó que Qt desactiva por interfaz al
  retirar un duplicado, perdiendo un recurso aún válido. Ahora conserva su ID y no reenlaza
  el control al retirar otro global. Conflicto/ausencia/asociación inválida bloquean entrada.
* Si se duplica KDE, los consumidores originales pueden perder su backend privado: bloqueo
  de proceso requiere reiniciar sólo el auxiliar. Repro con VirtualDesktopInfo instalado:
  tras retirar duplicado ve 0; otro proceso Qt en el mismo fixture ve los 4 publicados.
  Un objeto nuevo en el mismo proceso no evita la guarda. No se parchea el backend KDE.
* Inventario y barrera con plazo 1 s; respuesta tardía no reanuda sin revisión nueva.
  Conflictos no atrapan retirada. PanelRuntime oculta vistas/popups propios al perder
  confirmación, difiere su destrucción y restaura una vista ocultada si se confirma antes.
* El servidor conserva controles retirados inertes (userdata null) hasta destroy/desconexión:
  pausa/destrucción en vuelo no provoca invalid_object ni ejecuta trabajo. Clientes v1
  siguen probados; el auxiliar requiere v2. Launcher y diagnóstico compilado actualizados.
* CTest normal/ASan 5/5; Qt Wayland 7/7 contando init/cleanup, dos clientes v1 y proceso
  fresco; Python R4 113/skins 7. Extensión compilada, readelf sin GNU UNIQUE, sin instalar/
  cargar. Requisitos Wayland declarados/guía regenerada. BREEZE_R4_REGISTRY_RESULTS.json.
* Esto es una guarda del cliente, no arbitraje que impida anunciar globals duplicados en
  el servidor. Frontend real/arranque/arbitraje/capacidades y autoridad diaria pendientes.
  Sin render Wayland nuevo ni plugin/panel diario activado; R4 abierta, sin R5/R7.

### 224. Breeze: cierre de la ventana bajo el cursor (`Alt+X`) y menús desplegables de iconos SNI en la bandeja (2026-11-15)

* **Cerrar la ventana bajo el cursor en Breeze (`keybinds-manager.py`, `modules/user_binds.lua`):** con `input:follow_mouse = 2` (§3.217), el puntero y la rueda llegan a la ventana bajo el cursor pero el foco activo de teclado (`activewindow`) permanece en la última ventana clicada hasta hacer clic. Por eso `hl.dsp.window.close()` sin argumentos cerraba la ventana clicada anteriormente en vez de aquella sobre la que estaba el cursor al pulsar `Alt+X` o `Alt+F4`. Añadida `close_window_target()` en `keybinds-manager.py` (y mapeado el dispatcher `window.close` a `(is_plasma and close_window_target or hl.dsp.window.close)()`): en Breeze consulta `hl.get_cursor_pos()`, el monitor del cursor y su workspace activo (especial o normal), busca la ventana mapeada visible superior bajo el cursor (incluyendo los márgenes de decoración de `hl.plugin.breezebars.decoration(w.address, w.pid)` y priorizando flotantes y menor `focus_history_id`) y llama a `hl.dsp.window.close({ window = best })` (o `hl.dsp.window.close()` si el cursor no está sobre ninguna ventana). En default y Retro sigue llamando a `hl.dsp.window.close()`.
* **Menús contextuales de iconos SNI en la bandeja (`TrayMenu.qml`, `SystemTray.qml`, `PlasmaMenus.qml`, `MenuHost.qml`):** `SystemTray.qml` abría un `TrayMenu` (`PC3.Menu`) instanciado dentro de la propia ventana de la barra (`PanelWindow` de 44 px de alto, `WlrLayer.Top`, `WlrKeyboardFocus.None` y máscara limitada a `hitArea`). En QtQuick Controls un `Popup` es un overlay interno de su `QQuickWindow`, por lo que el desplegable quedaba recortado a los 44 px de la barra y carecía de captura de clics fuera de la barra para cerrarse. Además, `TrayMenu.qml` envolvía los elementos de `QsMenuOpener` en un `Loader` dentro de `Instantiator` y el `delegate` por defecto de `PC3.Menu` (`width: parent.width`) provocaba `TypeError` al insertar submenús. Ahora `SystemTray.openMenu` delega en `PlasmaMenus.openFor("tray", button, root.edge, { trayMenu })` (soportando tanto iconos directos del panel como iconos dentro de `TrayPopup`), `MenuHost.qml` aloja `TrayMenu` en su capa `WlrLayer.Overlay` a pantalla completa (posicionándolo junto al borde del panel, reajustando al cambiar el ancho asíncrono de D-Bus y cerrándolo al hacer clic fuera o pulsar `Escape`), y `TrayMenu.qml` inserta directamente `PC3.MenuItem`, `PC3.MenuSeparator` y submenús recursivos sobre `PC3.Menu` cerrando `PlasmaMenus` al disparar una opción.
* **Comprobado:** 32 pruebas en verde (`BWM_RUN_QML_TESTS=1 python3 -m unittest tests.test_plasma_tray tests.test_retro_settings -v`, incluyendo `TrayMenuAndCursorCloseTests`: apertura de menú SNI con submenús por encima de un panel de 44 px con `height > 80` y cierre al hacer clic fuera, y prueba en vivo en el workspace 9 con dos ventanas kitty donde `close_window_target()` cierra la ventana bajo el cursor dejando intacta la clicada). Regenerado `user_binds.lua` con `keybinds-manager.py reload`, reiniciado Quickshell con `bwm-theme-manager.py set plasma --restart-shell` y verificado `Hyprland --verify-config` y `qs -c ii ipc call plasmaMenus inspect` sin errores.

### 225. R4: arbitraje previo y retirada del proveedor de escritorios (2026-11-15)

* DesktopProvider integra en el frontend/fixture inventario de globals sobre el display
  existente, claim de elección entre proveedores BWM y confirmación asíncrona del par antes
  de availability. Inicialmente disabled no anuncia interfaces vacías. Se corrige el frontend
  que reactivaba disponibilidad tras fallar publish; no se vacía el snapshot para retirar.
* Un socketpair privado con libwayland-client/server, sin escuchar, hilo, proceso, roundtrip
  bloqueante o sustitución del filtro global. Inventario relevante límite 128 y fences 1 s;
  EAGAIN activa sólo escritura necesaria, fallos/peer perdido retiran y eliminan el fd source.
* wl_global_remove conserva una generación de core/globals/manager/desktop/ofertas durante
  esa vida. Controles retirados inertes; binds/get/activate/pause en vuelo no invalidan la
  conexión ni hacen trabajo/ack. Una vez creado el claim, fallo/desactivación/conflicto pide
  futuro inicio de sesión; no reintentos de generaciones ni hot unload/load. No hay KCM
  diario prometiendo esa activación. La recuperación de generaciones queda pendiente.
* Diagnóstico serverArbitrationVersion=1/estado/motivo/restartRequired/alcance visible y
  singlePublicationGeneration; launcher exige active y reinicio explícitamente falso sin
  instalar/cargar/habilitar. Conserva control v2/guardas del auxiliar y XML KDE originales.
* Pruebas C++14 escenarios: desactivado, proveedor previo, elección simultánea, conflicto
  posterior, snapshot inválido, recursos/binds en vuelo, retirada dentro de callback,
  filtros que ocultan claim/control, overflow, peer perdido activo/retirado (sin polling de
  HUP tras terminal), timeout y 20 ciclos sin aumentar
  fds. Prueba aparte de VirtualDesktopInfo C++/QML KDE original: activación/cambios/retirada.
  CTest7/7 normal y ASan (detect_leaks=0/halt_on_error=1), Python R4 113 y skins7. No mide
  fugas de memoria ni superficies/entrada reales. BREEZE_R4_PROVIDER_ARBITRATION_RESULTS.json.
* Extensión recompilada con cero GNU UNIQUE; no instalación/carga/autostart, reinicios ni
  sustitución del panel diario. Requisitos/noticias/arquitectura/handoff actualizados.
  Código propio GPL-2.0-or-later y APIs públicas, fuentes Wayland primarias sin copiar.
* Alcance: globals visibles para el observador bajo el filtro existente, claims cooperantes
  no auténticos. Un módulo ajeno puede anunciar duplicación antes de observarla/retirarnos.
  Mantener §223: su consumidor KDE puede exigir auxiliar nuevo. Frontend/arranque/filtros
  y aceptación Hyprland, generaciones, capacidades/autoridad/fallback diarios pendientes;
  operationalVerified/replacementReady false. Sólo R4, sin R5/R7 ni takeover. Conservar §224.

### 226. R4: inicialización diferida y cierre antes de descargar el módulo (2026-11-15)

* Fuente primaria Hyprland 0.56.2: filterGlobals permite el peer interno directo (no figura
  en SecurityContext::m_sandboxedClients); su whitelist mantiene privilegiados los globals
  propios para conexiones sandbox. No modificar ese filtro. PluginSystem programa reload
  después de init, y cleanup llama unloadAllPlugins ANTES de wl_display_destroy_clients.
* DesktopProvider difiere peer/registry/plazo hasta idle del loop con snapshot+opt-in.
  Disabled no crea sockets/peer/reloj; waiting-for-event-loop no consume deadline. Cancelar
  antes del claim permite nueva solicitud. Diagnóstico observerStartup=deferred-event-loop;
  fallo de registro hyprctl aborta antes de solicitar publicar.
  Preflight exige providerLifecycleVersion=1 e inicio diferido; rechaza módulos antiguos
  antes de lanzar, sin instalar/cargar/habilitar ni certificar operatividad por el diagnóstico.
* El cierre anterior dejaba controles inertes con callbacks/interfaz del módulo descargado.
  withdraw mantiene core y recursos para peticiones en vuelo; destructor definitivo destruye
  todos los controles registrados (límite4096) y proveedor todos los recursos del claim
  (límite256), incluidos controles retirados/late binds no referenciados por Peer::control.
  Inactividad por withdrawn, con core vivo para seguir la vida. No volver a userdata=null
  esperando desconexión después de destruir core/descargar .so. Cambia contrato viejo §223.
* Fixture ahora retiene cores retirados hasta terminar clientes, los libera antes del display.
  Nuevo DSO de prueba del mismo proveedor/core, símbolos internos ocultos y -fno-gnu-unique:
  enlaza management/desktop/control/claim y control tardío, destruye proveedor, exige cero
  recursos propios, dlclose, RTLD_NOLOAD negativo, después destruye clientes. Activo/retirado.
  No despacha peticiones después del cierre, por lo que no autoriza hot unload en vivo.
* CTest7/7 normal/ASan (detect_leaks=0/halt_on_error=1), 16 escenarios del proveedor, Python
  R4 113. Prueba arranque lento (>1s antes del primer dispatch), cancelación de idle y mismos
  consumidores KDE originales conservados. Extensión y DSO de prueba sin símbolos GNU UNIQUE.
  BREEZE_R4_STARTUP_TEARDOWN_RESULTS.json conserva fuentes/hash/resultados; código propio GPL.
* No instalar/cargar/autoiniciar plugin, reiniciar compositor o sustituir panel diario.
  Aceptación de frontend/arranque/logout/filtro real, futuras generaciones, capacidades,
  render/entrada y autoridades/fallback siguen pendientes. Revisar también E/S de count()
  que lee JSON desde el hilo compositor cada500ms. operationalVerified/replacementReady false.
  Sólo R4, no otros plugins ni R5/R7. No se ha probado logout físico del usuario.

### 227. R4: contador compartido enviado al frontend sin lectura de JSON (2026-11-15)

* Eliminada E/S count()/file_size/ifstream/JSON del frontend cada500ms. CountMirror guarda
  sólo copia del último contador válido, sin archivo/preferencia nueva. Comando propio
  bwm-plasma-desktops-count N, parser canónico1–100, recibo version1/valor/revisión; iguales
  no aumentan revisión ni programan idle. No habilita proveedor ni crea/borra workspaces.
* Puente existente resuelve effective_options() y prioridad bwm/user; native_workspaces.py
  transmite desde ese proceso. Reconcile/watch comparten Runtime, debounce previo y tick2s
  sólo si instalado el módulo opcional. No lo carga/habilita por presencia del .so. Sin
  daemon/thread/watcher/timer propio. Usa bloqueo existente: LOCK_NB en tick/reintento0,25s,
  guardia ya adquirida en reconcile; evita escrituras cooperantes reordenadas y recursión.
  El bloqueo y el proceso IPC nunca están en el compositor.
* Default10 es el del modelo común si falta clave; inválidos/JSON parcial no envían cero.
  Cache previa se conserva y primer estado desconocido impide publicar. Diagnostic
  countMirrorVersion=1/configuredCountSource=shared-bwm-bridge y countRevision; preflight
  sólo lee y exige versión/copia conocida. Recibo es cache aceptada, no frescura instantánea
  ni efecto gráfico confirmado. Rango menor conserva escritorios vivos/activos y excluye99/especiales.
* Pruebas combinan emisor Python real con parser/recibo C++ real sobre transporte de ensayo;
  originales KDE prueban3→7/reducir2 conserva3 y7 activos, normal/arbitrado. Puente real en XDG
  temporal: contador12, override9, reentrada, archivos ajenos/usuario conservados y sin reload.
  Python R4 122, puente20; CTest7/7 normal/ASan detect_leaks=0/halt_on_error=1. Módulo recompilado
  sin GNU UNIQUE. BREEZE_R4_COUNT_MIRROR_RESULTS.json con fuentes/hash/resultados.
* Requisitos/arquitectura/handoff/procedencia actualizados, sin nuevos paquetes runtime.
  No reiniciado puente en curso ni instalado/cargado/autoiniciado módulo, compositor/sesión
  o panel diario. El puente adoptará código al reiniciarse/iniciar sesión. Entrega/arranque
  real en Hyprland, generaciones/capacidades/render/entrada/autoridad/fallback pendientes.
  E/S del contador pendiente en§226 queda resuelta. operationalVerified/replacementReady
  false; sólo R4, sin R5/R7 ni takeover. Preservar cambios ajenos de atajos/bandeja.

### 228. R4: coordinador común del contador entre skins (2026-11-15)

* SharedSettingsRuntime.qml se instancia una vez en shell.qml, fuera de panel/skin loaders;
  no vive en Config/Ajustes. Usa Config.ready/contador/skin, Timer Qt debounce200ms y Process
  asíncrono. Si cambia durante envío deja pending para otra entrega, sin solapar procesos.
  Retry sólo si adaptador armado; sin prerequisito no hay sondeo periódico. FailedToStart
  no emite exited en QS0.3.2: runningChanged recupera estado, cubierto por prueba real.
* bwm_settings_hooks.py shared descubre hooks.sharedSettings sólo de skins incluidas/revisadas,
  con script relativo dentro de skin, prerequisito XDG relativo sin escape, intervalo1–30s,
  timeout3s y recibo JSONv1/applied bool. No ejecuta skins/temas/widgets descargados por declarar
  un hook. El .so sólo arma entrega de datos, nunca carga/habilita o certifica proveedor.
* Manifiesto Breeze registra native_workspaces.py shared cada2s. Auxiliar resuelve opciones
  comunes + texto all/skin ACTUAL mediante API común, sin importar/arrancar KDE bridge fuera
  de Breeze ni escribir archivos KDE/usuario. bridge_lock compartido con KDE, LOCK_NB fuera
  de reconcile. Se retira counts.tick periódico del watch KDE; sigue envío durante reconcile.
  No daemon/thread/FileView/inotify nuevo; hay Timer Qt en shell. No mover preferencia común.
* IPC de sólo lectura sharedSettings status devuelve ready/busy/entregas/skin/último informe.
  Recibos inválidos/timeouts no son éxito; motivos acotados en diagnóstico y retry armado.
  Nuevas instalaciones sin suscripción requieren otro disparo/inicio; nunca hot load/load.
* 12 pruebas específicas, incluidos QML real offscreen y cadena real de procesos a recibo C++
  de ensayo default/Retro/Breeze3/7/5. También all9/Retro11, texto ajeno/usuario intacto y sin
  kwinrc/KDE bridge. R4 134, puente20, skins7; CTest7/7 normal/ASan detect_leaks=0/halt_on_error=1.
  Sin cambios/recompilación C++; BREEZE_R4_SHARED_DELIVERY_RESULTS.json. Requisitos/guías/licencias actualizados.
* El dispatcher contra configuración actual fue inactive/retry0 porque módulo no instalado,
  sin IPC. Log existente legible sin error de tipo observado, NO prueba de carga. Hyprctl
  version falla Couldn't open a socket(1), qs IPC UnsupportedSocketOperationError. No eludir.
  shell.qml enlazado modificado puede recargarse solo; no reinicio forzado/carga verificada.
  No afirmar sesión sin cambios por no reiniciar manualmente. Sin instalación/carga de plugin
  o activación de panel nativo. Falta entrega/arranque reales, generaciones/capacidades/render/
  entrada/autoridad/fallback diarios. operationalVerified/replacementReady false; sólo R4.

### 229. R4: prueba del Task.qml original con roles Wayland preparada; ejecución bloqueada (2026-11-16)

* Revisadas fuentes instaladas de plasma-workspace/plasma-desktop6.7.5: los avisos
  undefined de §220 no prueban un fallo de BwmTaskSource. WindowTasksModel.roleNames
  consulta su backend nativo privado, ausente en offscreen; TasksModel.roleNames consulta
  ese WindowTasksModel estático, aunque se cambien fuentes por APIs públicas. No introducir
  sustitución de símbolos/punteros privados ni dar un proxy de prueba por aceptación Wayland.
* Nuevo test-taskdelegate.cpp y CTest native-task-delegate-render: usa la conexión Wayland
  privada del fixture existente, modelos originales y BwmTaskBridge real con snapshots
  propios. Prepara los widgets KDE icontasks/taskmanager, roles/identidad, activo→minimizado→
  restaurado, título, índice estable y retirada; QQuickRenderControl/QImage para dibujo en
  memoria sin show/create ni superficie. Errores de binding del QML original son fallos.
  No se han ejecutado esas aserciones: son cobertura preparada, NO resultados aprobados.
* El fixture falla ANTES de Qt: wl_client_create devuelve EPERM/Operation not permitted.
  Se reproduce también con native-desktop-protocol anterior. Añadidos perror y diagnóstico
  de handshake con código/stderr para no ocultar el motivo. Sin elevar ni eludir permisos.
  memoryRenderingVerified/renderingVerified false; no prueba física ni render aprobado.
* Compilación del test normal/ASan completada. Regresión seleccionada que no necesita
  wl_client_create: proyección de workspaces, geometría y configuración local3/3 normal y
  3/3 ASan (detect_leaks=0/halt_on_error=1). No afirmar CTest completo8/8: Wayland bloqueado.
  py_compile del runner OK. Evidencia BREEZE_R4_TASK_DELEGATE_RESULTS.json.
* No cambia código de producción, bibliotecas requeridas, configuración viva, plugin,
  panel diario ni binario del anfitrión. Sin instalación/carga/reinicio/commit/push/R5/R7.
  Comando local acotado para ejecutar la cobertura nueva: ctest --test-dir
  /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host -R '^native-task-delegate-render$'
  --output-on-failure. No usa compositor/IPC de sesión, no abre ventanas; depende del SDK KDE
  instalado y de poder crear los clientes Wayland privados. R4/aceptación diaria pendientes.

### 230. R4: corregida la guarda del socket heredado de la prueba nativa (2026-11-16)

* El usuario ejecuta native-task-delegate-render: fixtureExit0, QtWayland inicia, pero ambas
  filas fallan por exigir WAYLAND_SOCKET después de QApplication. Era un error del test,
  no prueba de fallo del widget ni de conexión ausente. Conservado el informe local anterior
  en userLocalAttempt de BREEZE_R4_TASK_DELEGATE_RESULTS.json; no se llegó al render.
* Revisado wl_display_connect en Wayland1.26.0: consume/unsetenv WAYLAND_SOCKET al conectar.
  QTest initMain captura fstat del socket ANTES de QApplication. initTestCase obtiene el
  wl_display real por QNativeInterface::QWaylandApplication y compara dispositivo/inodo del
  fd activo con el heredado. Admite dup, sin reponer variable ni crear otra conexión.
  Conserva guardas sin WAYLAND_DISPLAY/Hyprland de sesión. Sin cambio de producción.
* Reproducción con libwayland instalada/socketpair sin servidor confirma variable consumida
  e identidad preservada. Test recompilado normal/ASan; ejecución completa aquí sigue
  bloqueada por wl_client_create EPERM antes de Qt. No afirmar que pase/renderice: pendiente
  repetir desde terminal el mismo CTest. No plugin/panel/reinicio/commit/push ni R5/R7.

### 231. R4: procedencia del QML resuelta por recurso/hash, no por baseUrl (2026-11-16)

* Segundo ensayo del usuario: identidad de conexión, snapshots/roles nativos y creación de
  fila/delegado pasan; ambas filas se detienen por exigir que QQmlContext.baseUrl contenga
  /taskmanager/Task.qml. Otra suposición errónea del test: baseUrl es base de resolución,
  no la ubicación de fuente del objeto. Informe conservado como userLocalAttemptAfter230.
* tests/task-qml-source.h resuelve Task.qml con QQmlContext.resolvedUrl y verifica SHA256
  del recurso original Plasma6.7.5 ya revisado. No afirma que baseUrl identifique el objeto;
  la selección del delegado sigue su interfaz dentro del widget original instalado. Diagnóstico
  incluye base/resuelto/hash si falla. No APIs privadas ni cambios de producción/KDE.
* La misma guarda se añade a test-taskmenu: pasa con el delegado original en la regresión
  local de configuración, normal y ASan (detect_leaks=0/halt_on_error=1). Ambos ejecutables
  recompilados en los dos builds. Evita depender del terminal del usuario para probar esta
  corrección concreta. Prueba Qt aislada de la secuencia QQuickRenderControl/QImage confirma
  píxeles rojo→azul y ventana oculta/sin handle; NO acredita Task.qml pintado ni Wayland.
* Revisadas propiedades/estados del Task.qml original y render software Qt6.11.2. El ensayo
  completo corregido sigue pendiente del terminal local; no se extiende lo ya aprobado a
  render/entrada/aceptación diaria. Sin plugins/panel/reinicio/commit/push/R5/R7. Evidencia en
  followUp231 de BREEZE_R4_TASK_DELEGATE_RESULTS.json.

### 232. R4: aplicación de prueba propia para evitar el fallback de metadatos por PID (2026-11-16)

* Nuevo ensayo del usuario supera conexión, origen QML y PID, pero AppId es test-taskdelegate
  en vez de org.kde.konsole. El fixture no garantizaba un servicio Konsole en su base KDE:
  TaskTools.windowUrlFromMetadata cae al PID al no encontrar servicio. Error del ensayo,
  no del resolver de producción. Informe preservado como userLocalAttemptAfter231.
* tests/task-app-fixture.h crea aplicación .desktop/icono propios en XDG temporal y usa
  kbuildsycoca6 ya requerido sólo por BUILD_TESTING. Comprueba raíz/cache/servicio y espera
  notificación nativa; Exec=/usr/bin/false nunca se ejecuta. El runner entrega su raíz privada
  al cliente. Native test verifica primero AppId/nombre del modelo y después los de Task.qml.
  AppId del servicio conserva .desktop; Task.qml original quita el sufijo. Sin normalizar
  artificialmente el modelo ni cambiar el resolver, PID real conservado y ningún archivo
  de usuario/KDE de sesión modificado.
* La misma preparación/snapshot se ejecuta en test-taskmetadata con PID del propio test:
  ID/nombre/icono rojo correctos antes del fallback. Pasan ambas pruebas de metadatos4/4
  contando init/cleanup. Inicialización de la anterior ahora espera su servicio inicial,
  evitando caché retenida al ejecutar varios casos; actualizaciones posteriores siguen
  exigiendo notificación real, sin inyectar señales ni resetear caché privada.
* Compilación de ambos tests normal/ASan completada; isolated-local-configuration pasa
  normal y ASan detect_leaks=0/halt_on_error=1. py_compile del runner OK. Ensayo Wayland
  corregido/render de Task.qml sigue pendiente de nuevo CTest local; no certificarlo por
  la regresión offscreen de metadatos. Sin código de producción, plugins/panel/reinicio/
  commit/push/R5/R7. Evidencia followUp232 en BREEZE_R4_TASK_DELEGATE_RESULTS.json.

### 233. R4: ambos delegados originales KDE dibujados en memoria, ensayo local aprobado (2026-11-16)

* Usuario ejecuta native-task-delegate-render en terminal: CTest1/1 aprobado0,83s;
  QtTest4/4 contando init/cleanup, sin fallos/omitidos, ambos casos icons-only/text-and-icons.
  Informe workspace leído: clientExit0, fixtureExit0, cleanupVerified y memoryRenderingVerified
  true. Evidencia completa preservada en currentValidation de BREEZE_R4_TASK_DELEGATE_RESULTS.json.
* Pasa la cadena original KDE sobre socket Wayland privado: identidad de conexión, roles/
  snapshots BWM, recurso QML revisado, PID/ID/nombre, activo→minimizado→restaurado, título,
  continuidad del índice/delegado y retirada. Ambos widgets originales pintan píxeles con
  QQuickRenderControl/QImage y cambian al minimizar. Ventana oculta y sin handle nativo.
  Sin sustitutos de roleNames/StartupTasksModel, no se modifica el QML KDE.
* Alcance: render EN MEMORIA sobre conexión Wayland aislada, no superficie Wayland visible
  ni aceptación del panel de sesión/entrada/acciones Hyprland. Los avisos de servicios,
  protocolo PlasmaWindowManagement, sombras/toolbox del fixture permanecen; no certifican
  esos backends. renderingVerified/operationalVerified/replacementReady/r4Complete false.
* Este pase nativo es normal (usuario). Compilación y regresión local normal/ASan de §232
  siguen comprobadas; no afirmar ejecución nativa ASan ni CTest8/8 completo. Sin repetir
  ensayos aprobados, instalar/cargar plugins, panel diario, reinicio, commit/push ni R5/R7.
  Próximos bloqueos R4: frontend/arranque/entrega reales, entrada/superficies, capacidades
  restantes y autoridad/fallback diarios. Este resultado cierra el ensayo de §§229–232.

### 234. R4: activar grupos sin historial usa el apilado real del snapshot (2026-11-16)

* Reproducido con TaskTools.js instalado original6.7.5 y TasksModel agrupado real: dos
  ventanas sin LastActivated no recibían activación. StackOrder ausente dejaba undefined;
  activateTask línea172 intentaba pasarlo a QModelIndex, TypeError y cero acciones.
  Prueba anterior al arreglo y posterior preservadas en BREEZE_R4_GROUP_ORDER_RESULTS.json.
* native-tasks.snapshot conserva el índice de la lista clients como stackingOrder. Fuentes
  Hyprland0.56.2: clientsRequest recorre WindowState.windows; moveToTop lo mueve al final,
  moveToBottom al principio. No usar focusHistoryID, que es MRU. Excluir filas no invierte
  el orden relativo. Sin consulta extra, archivos, daemon o cambios de protocolo KDE.
* BwmTaskSource entrega StackingOrder y emite dataChanged al cambiarlo, sin reordenar sus
  filas/UUID. Campo opcional v1: si falta usa orden del snapshot como fallback de compatibilidad,
  no lo anuncia como apilado físico. Entero no negativo/int32; inválidos rechazan snapshot
  completo sin alterar el anterior. LastActivated sigue teniendo prioridad en KDE.
* Test original JS fijado por SHA256, importado desde el módulo KDE tras cargar su applet,
  sin copiar/parchear sus handlers. Grupo elige rank9 frente a3; tras actualizar elige12;
  tras observar activación vuelve a preferir MRU aunque tenga rank menor. También índices
  persistentes, cambio de rol, legado/inválidos, y productor ignora focusHistoryID probados.
  Offscreen usa startup vacío habitual; no es entrada física ni render Task.qml nuevo.
* Catálogo corrige diagnóstico obsoleto: fullscreen incluido, orden declarado, barrera2
  y arbitraje/ciclo/contador/readback1. Mantiene operationalVerified false y los pendientes
  de aceptación de frontend/menú de sesión; no convierte implementación en certificación.
* Diez Python del helper pasan; TaskTest10/10 contando init/cleanup. Regresión seleccionada
  CTest3/3 normal y3/3 ASan detect_leaks=0/halt_on_error=1; ambos builds completos y binario
  estable recompilados, py_compile OK. No CTest completo ni render nativo repetido tras este
  cambio; el pase previo §233 conserva su alcance. Sin instalar/cargar plugins, reinicios,
  aceptación de sesión, commits/push/R5/R7. Sin nuevas dependencias ni cambios de formatos KDE.

### 235. R4: el registro del panel debe recorrer la propiedad visual de los applets (2026-11-16)

* Ensayo real del usuario con --task-actions: los iconos abrían otra instancia en vez de
  enfocar ventanas existentes. También señala iconos incorrectos; no hay captura ni medición
  de aspecto. Se registra como FALLO, no como aceptación de tareas/entrada. Ctrl+C devuelve
  el prompt; limpieza del registro no medida en sesión. Avisos D-Bus/sombras permanecen.
* Reproducido por la ruta real PanelSession.bindPanelItem: boundModels0 aunque el applet
  tenía TasksModel. AppletQuickItem conserva propietarios QObject fuera del containment,
  pero pertenece visualmente al panel. findChildren sólo recorría QObject. El ensayo §233
  adjuntaba el applet directamente y por eso no cubría este fallo de integración.
* BwmTaskBridge.tick recorre children de QObject y childItems de QQuickItem con conjunto
  de visitados. No cambia padres, no crea items ni altera fuentes personalizadas. Descubre
  modelos visuales tardíos y conserva guardas, suspensión/quiescencia e identidad existentes.
* Nuevo test-paneltasks entra sólo por PanelSession (sin attach manual del applet): servicio
  propio fijado + ventana real del modelo sobre IPC ficticio se fusionan en una fila IsWindow,
  HasLauncher=true/IsLauncher=false. requestActivate produce focus y no lanzamiento. Antes:
  boundModels0; después3/3 QtTest contando init/cleanup. QML offscreen conserva sus avisos de
  roles nativos ausentes: esta prueba valida registro/modelo/ruta de acción, no pintado/entrada.
* previewchecks.py añade confirmación inicial de --task-actions, antes de anunciar registro:
  status fresco, modelo conectado y snapshot válido; plazo5s. Imprime sólo cantidades de
  ventanas/modelos; sin fuente aborta el ensayo con motivo en vez de anunciarlo preparado.
  No certifica aspecto, conexión de todas las apps ni salud continua; cero ventanas es válido.
  No se añade daemon/IPC de escritorio. Siete tests Python del wrapper/check pasan.
* Regresión CTest seleccionada3/3 normal y3/3 ASan detect_leaks=0/halt_on_error=1; focused
  HasLauncher/focus pasa, ejecutables normal/ASan recompilados y py_compile OK. Evidencia
  BREEZE_R4_PANEL_TASK_REGISTRATION_RESULTS.json. Sin Hyprland plugins/Quickshell reiniciados
  o configuración personal escrita. El nuevo ensayo real (incluidos iconos) sigue pendiente;
  mismo comando, ahora debe mostrar «Tareas R4 conectadas: N ventanas, M modelos».
  Sin nueva dependencia runtime, sin commit/push/R5/R7 ni sustitución diaria del panel.

### 236. R4: filtro nativo de escritorio ocultaba tareas; minimización entre monitores (2026-11-16)

* Usuario repite el ensayo de §235: sigue lanzando instancias y no puede recuperar las
  minimizadas; además observa la animación hacia el otro monitor. Se registra FALLO de
  sesión, sin aceptar tareas/entrada/iconos ni dar por resuelto §235 en el escritorio.
* Segunda causa reproducida: showOnlyCurrentDesktop viene true en main.xml de Plasma6.7.5.
  TaskFilterProxyModel compara ScreenGeometry con QScreen y exige VirtualDesktopInfo para
  esa salida. Sin proveedor nativo activo rechaza las ventanas, aunque boundModels y snapshot
  sean válidos. El test anterior forzaba el filtro a false y otra geometría, enmascarándolo.
  Nueva reproducción con geometría coincidente falla IsWindow antes del cambio.
* --task-actions exige ahora --all-desktops o --native-desktops con proveedor ya activo.
  --all-desktops es una opción explícita sólo del preview desechable: escribe el campo KDE
  showOnlyCurrentDesktop=false mediante KConfigLoader en ambas instancias antes de crear
  el panel. Sin parche QML, setters del modelo, escritorios inventados ni formato nuevo.
  Wrapper rechaza --profile; binario exige modo/acciones y raíces XDG temporales canónicas.
  No modifica configuración personal/persistida ni sustituye el backend de escritorios.
* Diagnóstico taskViewDiagnosticsVersion1 añade modelos de vista, filtros activos y filas
  visibles de ventana/grupo/lanzador; cuenta ambas instancias, no ventanas físicas únicas.
  Inicio exige vistas y proveedor confirmado si el filtro sigue activo; imprime cantidades,
  sin títulos/IDs. No es validación de entrada, aspecto o salud continua.
* Test-paneltasks usa dos applets y su configuración nativa, nunca setters de TasksModel:
  geometría QScreen real, lanzador+ventana fusionados/HasLauncher/focus, almacén minimizado
  en otra pantalla sin perder filas, y secuencia toggle-minimize/focus/restauración. Normal
  QtTest3/3; isolated-local-configuration ASan1/1 tras la extensión. Regresión seleccionada
  anterior3/3 normal/ASan; Python preview10, tareas10 y minimización7; py_compile OK.
  QML offscreen mantiene avisos de roles: no acredita nuevo render Wayland ni clic físico.
* Regla común bwm-minimized-storage-no-animation con match workspace=special:minimized y
  no_anim=true: evita animar el traslado al almacén compartido que puede estar asignado al
  otro monitor. Deja de coincidir al restaurar y no escribe override por ventana. Respeta
  Lua del usuario al final. Lua parse y Hyprland --verify-config aislado pasan (config ok).
  No implementa el efecto KWin de minimizar hacia el icono; efecto visual pendiente.
* Binarios normal/ASan recompilados. Sin reload en sesión desde este ejecutor (IPC
  inaccesible), sin plugins instalados/cargados ni Quickshell reiniciado. Para el ensayo:
  hyprctl reload y comando anterior añadiendo --all-desktops. Nueva línea esperada:
  «Tareas R4 conectadas: N ventanas; filas visibles: V; lanzadores: L.»
  Evidencia BREEZE_R4_DESKTOP_FILTER_RESULTS.json. operationalVerified/replacementReady/
  r4Complete false; pendientes foco/restauración físicos, regla cargada/animación e iconos.
  Sin nuevas dependencias, commit/push/R5/R7 ni sustitución del panel diario.

### 237. R4: usuario confirma funcionamiento del preview de tareas (2026-11-16)

* Tras el comando de §236 con --all-desktops y la indicación de cargar la regla, usuario
  responde literalmente «ahora si». Se registra aceptación funcional general del ensayo
  solicitado de activación/restauración, comunicada por el usuario, sin afirmar observación
  directa del asistente ni mediciones independientes de foco, geometría o monitor.
* Supera el fallo funcional comunicado en §§235–236 para este preview. No hay desglose de
  apps/casos, conteos de arranque, captura, confirmación individual del efecto animado,
  iconos o limpieza. No se da por ejecutado hyprctl reload sólo por esa respuesta.
* El alcance sigue siendo auxiliar desechable con todos los escritorios; el proveedor nativo
  de escritorio/filtros y la aceptación diaria de R4 permanecen pendientes. Sin nuevo código,
  compilación o tests repetidos. Evidencia userFollowUp237 en
  BREEZE_R4_DESKTOP_FILTER_RESULTS.json; operationalVerified/replacementReady/r4Complete false.

### 238. R4: apariencia KDE nativa en el preview desechable (2026-11-16)

* Continuación tras la confirmación funcional §237. Se atiende el aspecto de iconos que el
  usuario había señalado en §235: la configuración XDG vacía del preview no contenía su
  selección de iconos, paleta, fuentes o SVG. La reproducción aislada lee breeze/default,
  fondo #eff0f1 y ningún icono propio; no se afirma medir los iconos de su sesión.
* Nueva opción --session-appearance del wrapper, sólo con --follow-skin desechable y nunca
  --profile. Antes de QApplication ejecuta --stage-preview-appearance con QCoreApplication:
  lee ajustes de aspecto permitidos de kdeglobals/plasmarc, fusiona rutas XDG seleccionadas y
  kdedefaults mediante KConfig, y publica archivos nativos nuevos en XDG temporal. No copia
  archivos enteros/enlaces ni ejecuta layouts; origen y claves ajenas quedan intactos.
* KConfig::NoGlobals con archivo absoluto + addConfigSources aplica prioridad local y
  valores inmutables/borrados. SimpleConfig ignora fuentes adicionales en KConfig6.29:
  usarlo sólo al escribir el destino. Snapshot contiene valores efectivos; no se afirma
  trasladar restricciones [$i] a la nueva configuración ni migrar un perfil completo.
* Permite leer assets desde XDG_DATA_HOME/DIRS originales también con --package. El preview
  selecciona QT_QPA_PLATFORMTHEME=kde; el motor nativo crea QIcon/paleta/fuentes sin llamar
  setThemeName. D-Bus y todas las escrituras siguen aislados. Snapshot de inicio, sin watcher
  nuevo ni seguimiento de cambios posteriores. No copia ajustes específicos de QStyle/Kvantum,
  cursor, fondo, servicios, configuración de apps o scripts de tema.
* Prueba nueva isolated-preview-appearance usa QApplication, Plasma::Theme y motor KDE real:
  icono/PNG propios en árbol XDG estándar, píxel #39b574, icon theme propio, paleta #112233,
  fuente15 y SVG breeze-dark. Comprueba defaults local/sistema, borrado/inmutabilidad efectiva,
  claves privadas excluidas, fuente/sistema sin cambios, independencia tras editar el origen,
  rechazo de sobrescritura y alias origen/destino. Wrapper rechaza perfiles sin tocarlos.
* Regresión seleccionada CTest4/4 normal/ASan (detect_leaks=0/halt_on_error=1), wrapper Python11,
  py_compile y diff-check propios pasan. Binarios normal/ASan recompilados. No se repite el
  render Wayland aprobado ni se arranca preview en la sesión desde este ejecutor.
  Dependencias KDE ya declaradas (plasma-integration/KConfig/libplasma), sin paquetes nuevos.
* Evidencia BREEZE_R4_APPEARANCE_RESULTS.json. Ensayo físico opcional: comando §236 añadiendo
  --session-appearance; revisar iconos/paleta/SVG. Sin nueva aceptación visual, instalación/
  carga de plugins, reinicio de shell, commit/push/R5/R7 o sustitución del panel diario.
  operationalVerified/replacementReady/r4Complete siguen false.

### 239. R4: aspecto/acciones aceptados; miniaturas de tareas por captura nativa preparadas (2026-11-16)

* Usuario ejecuta --session-appearance y confirma «todo lo que me pediste que comprobara va
  bien ... lo demas todo perfecto», salvo miniatura al pasar cursor. Se acepta aspecto y
  comportamiento solicitado a nivel de su reporte, no una matriz medida. Inicio:7 ventanas,
  12 filas ventana/grupo y6 lanzadores sumando ambas vistas. Ctrl+C devuelve prompt; sin
  medición independiente de limpieza. userFollowUp239 en BREEZE_R4_APPEARANCE_RESULTS.json.
* Log: falta org.kde.pipewire al cargar PipeWireThumbnail.qml. Fuentes originales6.7.5 muestran
  además ScreencastingRequest → zkde_screencast_unstable_v1 de KDE. Instalar sólo el módulo
  no conecta ese backend con Hyprland ni convierte los UUID BWM en UUID de KWin.
* Nueva opción --task-thumbnails, sólo preview desechable con --task-actions. Mantiene
  ToolTipDelegate/Instance originales, su disposición, acciones y estilo. Interceptor público
  del QQmlEngine compartido cambia únicamente la URL qrc exacta de PipeWireThumbnail.qml,
  revisada por SHA256. Adaptación LGPL pequeña en qml/TaskThumbnail.qml: conserva contrato
  hasThumbnail/winId, sustituye el endpoint KWin/PipeWire por un QQuickPaintedItem propio.
  Fuente desconocida bloquea el opt-in. Sin parche del KDE instalado, símbolos privados
  duplicados, registros de tipos KDE sustituidos o plugin de compositor.
* Backend asíncrono en la conexión Wayland Qt existente: ext-foreign-toplevel-list + mapping
  Hyprland de64 bits + ext-foreign-toplevel-image-capture-source/ext-image-copy-capture + shm.
  Sólo handles de ventana; no captura salidas, recorta pantalla, abre portales o escribe
  imágenes. Vincula handle estable ANTES de exigir snapshot iniciado después; comprueba
  UUID/identidad actual BWM. PID/generación nuevos invalidan UUID anterior. No se admiten
  minimizadas; cierre de handle, ocultación, retirada de fuente/skin/global borran la imagen.
* memfd CLOEXEC, buffers8/10bits de32bpp, dimensiones8192 máx.,64MiB por buffer/128MiB total,
 8 sesiones máx., texturas hasta512px y peticiones máx.4fps por sesión. Copia desacoplada antes
  de liberar memoria. Sólo primer frame/negociación tienen timeout: uno posterior puede
  esperar daño indefinidamente en ventana estática. Cambios de constraints reemplazan buffer;
  formatos ajenos fallan a icono, sin inventar una captura. Sin prometer HDR/colorimetría exactos.
* Startup exige protocolos conectados si se pidió el flag; informa que los primeros frames
  dependen del hover. Diagnóstico agregado de capturas/bytes/frames/error, sin imágenes/IDs.
  Globals retirados/duplicados bloquean hasta reiniciar sólo el auxiliar. Sin roundtrips
  bloqueantes, daemon nuevo, carga de .so, scripts externos o escrituras de config personal.
* Prueba local nueva en XDG/D-Bus privados: formato de píxeles8/10bits, límites/transforms,
  identidad UUID/minimizada y QML original redirigido/cast, mismo motor del AppletQuickItem.
  Fixture nativo propio genera píxeles #3684c9 y prueba pausa/estático/resize/identidad/cierre/
  retirada en memoria, sin wl_surface. Compilado, pero su ejecución aquí bloquea antes del
  cliente con wl_client_create: Operation not permitted. NO se da por aprobado ese ensayo.
* Regresión seleccionada5/5 normal/ASan, Python wrapper13/tareas10/skins7, py_compile y
  diff-check propios pasan. ASan detect_leaks=0/halt_on_error=1. Binarios/fixtures compilados;
  sin repetir render Wayland §233 ni afirmar captura real. Evidencia
  BREEZE_R4_THUMBNAIL_RESULTS.json; ejecutar native-task-thumbnail desde terminal antes del
  nuevo preview con --task-thumbnails. R4/operationalVerified/replacementReady/r4Complete false.
* Requisitos build hacen explícitos wayland-protocols/wayland-scanner ya empaquetados;
  tabla regenerada. XML WLR original vendorizado de Hyprland0.56.2 sólo para tipos referidos
  por mapping (no se vincula su manager). Avisos/licencias conservados. Sin commit/push,
  reinicio de shell, plugin instalado/cargado, panel diario sustituido ni R5/R7.

* Bloqueo de seguridad encontrado al contrastar BREEZE_RECOVERY.md: la nueva captura
  también llega a ScreenshareSession::init0.56.2. Se mantiene el veto de sesión hasta tener
  el monitor protegido, no se supone seguro por cambiar protocolo. Parche versionado propio
  en patches/hyprland valida/retiene monitor en init y monitorChanged; marca ELF retenida,
  sin ABI/cabeceras nuevas. Dos cuerpos originales producen SIGSEGV con monitor nulo en
  prueba aislada; siete casos parcheados pasan normal/ASan. No es build completo de Hyprland
  ni prueba del crash original. Fuente BSD original conservada como fixture y licenciada.
* Anfitrión exige marca del EJECUTABLE ACTIVO del peer Wayland (SO_PEERCRED + /proc/PID/exe),
  no archivo de config/env, versión instalada ni .so. Sin parche activo rechaza opt-in antes
  de crear capturas; sólo el ejecutable de fixture tiene autorización sintética explícita.
  Guía BREEZE_R4_THUMBNAILS.md: CTest privado primero; instalación user patch de Portage y
  emerge exacto0.56.2::hyproverlay por el usuario, después próximo inicio de sesión. Sin
  sudo/instalación/reinicio realizados aquí; contenciones diarias no reactivadas. Regresión
  final6/6 normal/ASan, no5/5; mantiene captura nativa pendiente por EPERM.

### 240. R4: SIGSEGV del cliente de miniaturas al destruir el item (2026-11-16)

* Usuario ejecuta native-task-thumbnail: fixture arranca/termina0, cliente sale-11 a4.165s,
  acceso0x10; CTest falla1/1. Se registra fallo, no captura aceptada ni crash de Hyprland.
  No hay core guardado para ese cliente. No se instalan parche/paquetes ni se cambia sesión.
* Reproducción mínima local: TaskThumbnail asociado a un QQuickWindow y destruido. Falla
  en0ms con acceso0x10, también sin Wayland/captura/IPC. ASan sitúa QWeakPointer::isNull ←
  QPointer<QQuickWindow> ← callback windowChanged ← QQuickItem::~QQuickItem. El destructor
  de la base emite la señal después de liberar State; QObject desconecta demasiado tarde.
  Esto identifica el defecto del auxiliar; no acredita los demás hitos del ensayo nativo.
* Destructor explícito desconecta sólo nuestras conexiones guardadas antes de liberar
  State/captura. No desconecta indiscriminadamente destroyed ni callbacks ajenos de Qt/QML.
  Watch de ventana separado registra también el padre C++ inicial, cuya windowChanged se
  emitió en la base antes de conectar el callback. Sin cambios de backend/capacidades/guardas.
* Test local amplía destrucción con ventana, reparentado/desasociación, destrucción del
  padre y entrega normal de destroyed/QPointer. QtTest9/9 contando init/cleanup normal/ASan.
  Ensayo nativo añade destrucción/recreación con captura activa y cinco checkpoints de
  etapa sin IDs/píxeles privados. Runner local desactiva core dumps; todo XDG sigue temporal.
* Binarios/fixtures normal/ASan recompilados; regresión seleccionada6/6 ambos, py_compile
  y diff-check propios pasan. Native-task-thumbnail corregido no se puede ejecutar aquí:
  sigue wl_client_create EPERM antes del cliente; repetir el mismo CTest desde terminal.
  No se repite el render §233 ni se da por validada miniatura/teardown nativos en sesión.
* Evidencia followUp240 en BREEZE_R4_THUMBNAIL_RESULTS.json conserva fallo de usuario,
  repro/ASan anteriores, código/hash y resultados nuevos. Parche de monitor de Hyprland
  y su instalación siguen pendientes; veto de capturas reales intacto. Sin nuevas
  dependencias, sudo, plugins/reinicios, panel diario sustituido, commit/push/R5/R7.

### 241. R4: ensayo nativo de miniaturas aprobado desde terminal (2026-11-16)

* Usuario repite native-task-thumbnail tras §240: CTest1/1 aprobado en4.30s. Informe local
  leído y verificado: cliente0/fixture0, syntheticWindowCaptureVerified=true, cleanupVerified
  true, QtTest3/3 contando init/cleanup,4.116s. Conserva avisos del backend WindowManagement
  KDE original del fixture; no hubo diagnósticos adicionales del cliente/servidor.
* Los cinco checkpoints confirman: píxeles sintéticos #3684c9 por captura Wayland hasta
  QImage; estático/ocultación/resize; destruir/recrear durante captura activa; identidad,
  cierre y retirada; teardown completo. Supersede el fallo del cliente de §240 y el bloqueo
  de ejecución nativa para este ensayo normal. No es native ASan ni miniatura en escritorio.
* Evidencia userFollowUp241/currentValidation en BREEZE_R4_THUMBNAIL_RESULTS.json. No se
  repite el ensayo aprobado ni se recompila por esta actualización documental. Cero sudo,
  cambios de sesión, plugins, shell reiniciado, commits/push/R5/R7 o sustitución diaria.
* Siguiente paso concreto: parche de monitor de Hyprland0.56.2 en Portage y recompilación
  por el usuario; fuerza build desde fuente (--usepkg=n --getbinpkg=n). Ruta de parche
  destino sigue ausente; ebuild0.56.2::hyproverlay disponible. Después de instalar, guardar
  trabajo y próximo inicio de sesión para adoptar el binario. Todavía no instalado/cargado;
  guardas/contenciones reales intactas. Guía BREEZE_R4_THUMBNAILS.md actualizada.
  operationalVerified/replacementReady/r4Complete false; ensayo visual de hover pendiente.

### 242. R4: parche instalado y marca del ejecutable comprobados; hover real pendiente (2026-11-16)

* Tras instrucciones de §241, usuario responde «listo». Se registra reporte de finalización;
  no hay log de emerge ni confirmación separada del reinicio de sesión. Comprobación directa:
  patch de /etc/portage coincide byte a byte con el revisado; /usr/bin/Hyprland contiene
  BWM_SCREENSHARE_MONITOR_GUARD_V1. Instalación del artefacto protegida comprobada, no se
  afirma recompilación ejecutada por el asistente ni adopción en proceso activo.
* IPC sigue inaccesible en este ejecutor (hyprctl version devuelve2, socket timeout). No se
  identificó proceso Hyprland de la sesión visible al ejecutor; no implica que no esté
  ejecutándose. Asociación de peer Wayland/ELF activo pendiente: la verifica el auxiliar
  automáticamente antes de permitir --task-thumbnails. Config actual de skin=plasma.
* Siguiente ensayo: comando de guía con --task-thumbnails, conservar --all-desktops y
  --session-appearance. Mantener cursor sobre tarea no minimizada, comprobar imagen y
  actualización/cierre del tooltip. No se arranca preview o cambia sesión desde aquí ni
  se repiten pruebas ya aprobadas. Captura visual real y cierre R4 pendientes.
* Evidencia userFollowUp242/currentValidation en BREEZE_R4_THUMBNAIL_RESULTS.json. Sin cambios
  de código, compilación/tests nuevos, sudo ejecutado por asistente, hot load/unload,
  Quickshell reiniciado, panel diario sustituido, commit/push/R5/R7. Las contenciones de
  recuperación de la barra diaria siguen intactas. operationalVerified/replacementReady/
  r4Complete false.

### 243. R4: diagnóstico de guarda no distingue permisos de marca ausente; corregido (2026-11-16)

* Usuario ejecuta preview con --task-thumbnails: auxiliar bloquea diciendo que falta marca;
  wrapper añade ENOENT de ack.json. No miniatura ni aceptación visual. La comprobación de
  §242 sólo acreditaba archivo instalado, no proceso activo. No se infiere que haya que
  reinstalar/reiniciar: el antiguo bool agrupaba todos los motivos de fallo bajo ese texto.
* Confirmado localmente: /usr/bin/Hyprland contiene marca y tiene cap_sys_nice=ep; USE
  filecaps activo en Gentoo. Esto puede impedir acceso a /proc/PID/exe. Hipótesis pendiente
  de diagnóstico en sesión: no se afirma que sea la causa ni que el proceso sea antiguo.
  El ejecutor sigue sin ver ese proceso/IPC. No se toca filecaps, núcleo, permisos o guarda.
* thumbnailCompositorGuardStatus distingue conexión/credenciales/PID/UID, apertura/lectura/
  tamaño de ELF y marca realmente ausente/presente; informa peer PID/nombre, error y bytes,
  sin cmdline/env/datos de ventanas. El gate sigue exigiendo lectura real de la marca;
  no fallback al archivo instalado ni permiso/capacidad adicional. Mensaje ya no afirma
  ausencia de marca cuando no se pudo leer.
* Nuevo --check-thumbnail-compositor en binario, antes de perfiles/vistas. Runner
  check-thumbnail-compositor.py usa XDG/D-Bus temporales y la conexión Qt Wayland del usuario,
  imprime JSON y no crea panel/captura ni lanza tareas. Siguiente comando: python3
  /mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/check-thumbnail-compositor.py.
  La salida decidirá entre imagen antigua, permiso u otro fallo; no recompilar a ciegas.
* wait_initial_ack separa child muerto/timeout antes de register. Si aborta guarda, preserva
  motivo original y código de salida, sin ENOENT engañoso. Tests de muerte/ack viejo/timeout,
  y runner diagnóstico sólo modo lectura/conexión correcta/raíces privadas. Binarios normal/
  ASan recompilados; seleccionados6/6 ambos, wrapper16, py_compile/diff-check pasan.
  QtTest thumbnail10/10 incluyendo init/cleanup; no captura nueva ni repetición native§241.
* Evidencia userFollowUp243 en BREEZE_R4_THUMBNAIL_RESULTS.json. Sin dependencia nueva,
  sudo/sistema/reinicio de sesión, plugins/shell/panel diario o commit/push/R5/R7. R4 y
  captura visual pendientes. operationalVerified/replacementReady/r4Complete false.

### 244. R4: denegación de /proc confirmada; informe de guarda por IPC y PID (2026-11-16)

§244 (2026-11-16): el diagnóstico del usuario confirma Permission denied al leer el
executable de Hyprland PID5178/UID1000. La comprobación anterior por /proc no contemplaba esta
configuración Gentoo/filecaps; no prueba ausencia de guardas. Parche ampliado publica
bwmScreenshareMonitorGuard {version:1,pid:getpid()} en el JSON original de hyprctl -j version.
Getter junto a guardas reales, cabecera interna nueva; sin E/S/espera en compositor ni cambio
de estructuras/ABI. Auxiliar conserva prueba ELF y acepta informe fresco sólo con PID exacto
de SO_PEERCRED y UID propio. Runtime real para IPC desde XDG temporal; límite2s/64KiB,
rechazo de otra instancia/tipos inválidos/campo ausente/error/timeout. Sin override ni
cambios de permisos/capacidades. Diagnóstico conserva causa de /proc separada de la de IPC.
Aplicación del parche completo a dos originales0.56.2 + cabecera comprobada con git apply;
cuerpos originales/corregidos de guardas y getVersion compilados, JSON/PID real validados.
Build auxiliar normal/ASan, CTest seleccionado6/6 en ambos, wrapper16 y QtTest12/12 contando
init/cleanup pasan. No build completo de Hyprland ni prueba IPC/captura de sesión aquí;
ensayo nativo§241 no repetido. Guardas anteriores instaladas, parche instalado comparado:
carece del informe IPC. Extensión aún SIN instalar/adoptar: usuario debe reemplazar user
patch, recompilar desde fuente y entrar de nuevo; después ejecutar diagnóstico sin capturas.
Ver BREEZE_R4_THUMBNAILS.md y userFollowUp244. Panel diario intacto; R4 sigue abierta.

### 245. R4: guarda del compositor activo verificada por IPC (2026-11-16)

§245 (2026-11-16): usuario ejecuta diagnóstico corregido: clientExit0, verified=true,
verificationMethod=compositor-ipc, guarda version1 y PID496181 coincidente con SO_PEERCRED,
Hyprland/UID1000. /proc sigue denegado; alternativa IPC funciona manteniendo el requisito de
PID/UID. Runner sin cambios de sesión ni capturas (sessionModified/capturesStarted false).
Parche de Portage ampliado ahora idéntico al del repo (SHA256239aa61b67ca0f9d1ab536814027f3d18bbc74cb9f3aa008554e60b80ee9ff8c).
Informe activo comprobado por salida de terminal, sin inferir detalles del rebuild/relogin.
Siguiente: preview con --task-thumbnails --all-desktops --session-appearance y hover sobre
tarea no minimizada, comprobar imagen/actualización y cierre del tooltip/acciones. No repetir
CTest nativo aprobado ni pedir recompilar/reentrar otra vez. Miniatura física aún pendiente;
sin cambios de código/build/tests/sudo/sesión por el asistente. Panel diario intacto, R4 abierta.
Evidencia userFollowUp245 en BREEZE_R4_THUMBNAIL_RESULTS.json.

### 246. R4: tooltip moderno sin rol adaptado y preview de tareas duplicada (2026-11-16)

§246 (2026-11-16): usuario ve preview centrada/duplicada y listada como ventana en la
barra; deja auxiliar abierto. Ensayo visual NO aceptado. Lectura del último ack existente
confirma panel visible/protocolos preparados y dos applets taskmanager; no es un muestreo
actual de fotogramas. hyprctl directo sigue inaccesible aquí (Couldn't set socket timeout(2));
sin captura ni control visual de la superficie del usuario.
Causa de adaptación reproducida con tooltip original: ToolTipDialog6.7.5 se crea desde C++,
sin contexto QML propio, deriva PopupPlasmaWindow y no Dialog. PackageWindows sólo reconocía
Dialog/contexto plasmoid. Ahora resuelve propiedad visualParent por árbol visual de applet,
configura overlay/posición al SurfaceCreated antes de la selección de rol Wayland y sigue
visualParentChanged al reutilizar el tooltip. API pública LayerShellQt/PlasmaQuick; sin
parchear tooltip/QML KDE ni filtrar PID propio para ocultar el fallo. NonInteractive retiene
entrada de puntero, keyboardNone/activateOnShow=false; sin reserva de área. Una sola instancia
de PopupAnchor por ventana; conexiones de vida acotadas. Suspender sólo el dueño vigente.
Tooltip compartido que pasa a ventana normal recupera backend original tras hide/destroy;
al volver al panel se recrea su rol, nunca se cambia rol sobre superficie mapeada. Ventanas
ajenas quedan intactas. Diagnóstico packageWindows añade tipo/rol/geometría, sin contenido.
Preview desechable --task-actions --native-panel usa una instancia por defecto. --instances
1|2 permite comparación explícita sólo con --follow-skin y sin --profile; perfiles guardados
no cambian y probes/otros modos conservan las dos instancias. Env heredado se descarta.
Build normal/ASan; CTest seleccionado4/4 ambos (thumbnail, appearance, surfaces, local config),
QtTest13/13 contando init/cleanup y wrapper18 pasan. Prueba usa Core.ToolTipArea original:
creación perezosa C++, rol al crear superficie, posición/tamaño, cambio de applet/containment,
reutilización, ocultación, salida a ventana normal y vuelta; sin duplicar adaptador ni pedir
foco. Offscreen verifica política/orden de eventos, NO rol real del compositor o lista de
ventanas de sesión. Fuentes locales Qt6.11.2/LayerShellQt6.7.5 revisadas para ese límite.
Aviso LayerShellQt de ventana visible en SurfaceCreated se basa en flag Qt, que cambia antes
de crear su shell surface; se conserva en informes, no se usa como prueba de rol nativo.
Auxiliar abierto sigue con código anterior; siguiente Ctrl+C y mismo comando con --instances1,
comprobar hover anclado, sin ventana nueva en tareas, una sola vista y acciones/cierre.
Sin recompilar Hyprland/relogin, repetir ensayo nativo§241, nuevo requisito o tocar panel diario.
Evidencia userFollowUp246; captura/colocación física tras corrección pendientes y R4 abierta.

### 247. R4: miniaturas aceptadas por el usuario (2026-11-16)

§247 (2026-11-16): usuario confirma «perfecto ya tiene miniaturas» tras §246 y pide continuar,
dejando el auxiliar abierto. Aceptación visual general del hover nativo registrada; no se
infiere medición individual de actualización/foco/geometría ni matriz completa de monitores.
No repetir el CTest nativo§241 ni el diagnóstico de guarda ya aprobados. El asistente no
cierra ni reinicia el auxiliar abierto. R4 sigue abierta por capacidades/aceptación restantes;
panel diario intacto. Evidencia userFollowUp247 en BREEZE_R4_THUMBNAIL_RESULTS.json.

### 248. R4: nueva instancia y apertura de archivos mediante lanzador KDE (2026-11-16)

§248 (2026-11-16): continúa R4 por Nueva ventana/abrir URL de una tarea con ventana. La
fuente BwmTaskSource antes heredaba los dos métodos vacíos de AbstractTasksModel. Añadidos
requestNewInstance/requestOpenUrls, índices/identidad vigentes y URL acotadas; TasksModel
original reenvía ambos. CanLaunchNewInstance se invalida con metadatos KSycoca. La política
del menú sigue datos .desktop originales (NoDisplay, SingleMainWindow, X-GNOME-SingleWindow,
acciones New Window). No confundir visibilidad del menú con permiso de ejecutar una petición
explícita: WaylandTasksModel original también permite clic central/modificadores aunque la
entrada genérica esté oculta. Helper canLauchNewInstance no está exportado; adaptación mínima
por KService público con licencia/créditos LGPL2.1 conservados, sin duplicar símbolos KDE.
Acciones pasan por cola/quiescencia del puente y bloqueo nativo común. native-tasks revalida
skin y dirección/PID/inicio dentro del bloqueo, resuelve appId de clients actual, y reejecuta
sólo el host conocido con --launch-task-application. Éste usa AppData/KService nativos y
KIO::ApplicationLauncherJob, sin interpretar Exec, comandos de PID o URL lanzadora arbitraria.
Se exige aplicación registrada; fallback a ejecutable sin .desktop no se ejecuta. Aceptación
del job confirma traspaso de arranque, nunca app lista/ventana/foco verificados.
El wrapper conserva sólo claves permitidas del entorno original en contexto de proceso;
auxiliar de lanzamiento restaura XDG/D-Bus/Qt/Wayland para que la app no use almacenes del
preview. Contexto ausente/malformado falla. No se restauran flags BWM_R4, BWM_SKIN_SWITCH ni
WAYLAND_SOCKET consumido. Host de lanzamiento sin panel/capturas, entrada/tiempo acotados y
sesión de proceso aparte: timeout/retirada no terminan apps lanzadas. Recibo por descriptor
CLOEXEC separado; stdout/stderr de apps no contaminan JSON ni retienen el canal abierto.
Prueba real de job KDE sólo con aplicación Python propia en XDG/D-Bus privados: args/espacios/
Unicode/metacaracteres y URL nativa, entorno, proceso que sigue vivo tras recibo, identidad
antigua, URL vacías y servicio retirado. Prueba C++ por TasksModel original verifica peticiones,
capacidad de menú y refresco KSycoca conservando índices. Política de visibilidad no bloquea
petición explícita; no promete que una app de ventana única abra otra ventana.
KIOGui declarado en CMake/requisito de build (Gentoo kio/Arch kio), tabla regenerada; skin ya
recomienda ese requisito experimental. Código/diagnósticos no certifican rutas restantes:
lanzadores puros/acciones específicas de aplicaciones mantienen su camino nativo anterior y
su entorno aún requiere revisión; activación/foco de apps nuevas y sesión real pendientes.
Sin nueva dependencia de captura, plugin, cambio de skin o panel diario. Auxiliar abierto
sigue con binario anterior; para probar el nuevo hay que cerrar sólo éste y relanzar wrapper.
No se instalan/recargan Hyprland/Quickshell ni se ejecutan aplicaciones del usuario desde aquí.
Ver BREEZE_R4_TASK_LAUNCH_RESULTS.json. R4/replacementReady/operationalVerified siguen false.

Validación §248: CTest seleccionado5/5 normal y ASan (launch/thumbnail/appearance/surface/local),
Python R4152 y manifiestos7. QtTest Metadata5/5 y Thumbnail13/13 (init/cleanup incluidos).
Job KDE ejecutado con fixture propio; stdout/stderr de app y vida tras recibo probados también
normal/ASan. No se repite native-task-thumbnail ni diagnóstico/hover aceptados. Alcance real
pendiente: peticiones de arranque/archivos desde el auxiliar actualizado en la sesión del usuario,
activación/foco, lanzadores puros y acciones específicas de aplicaciones; no prometer R4 cerrada.

### 249. R4: aceptación de nueva instancia/archivos y traspaso a Claude (2026-11-17)

Usuario confirma clic central → ventana nueva Firefox, combinación posterior de pestaña y
minimizar correcto; después de instrucciones de arrastrar imagen al icono auxiliar responde
«se abre». Ambas rutas de §248 aceptadas manualmente, sin inferir telemetría/foco/matriz.
Actualizado BREEZE_R4_HANDOFF_CLAUDE.md con prioridad sobre pendientes históricos y próximo
frente: lanzadores sin ventanas/acciones .desktop específicas y su entorno de lanzamiento.
Informes de aceptación actualizados; no nuevas pruebas/build, cambios de sesión, commit o
push. Auxiliar dejado abierto por usuario, estado actual no comprobado. R4 sigue abierta,
panel diario intacto. Pérdida temporal del ejecutor no demuestra un fallo del ordenador.

### 250. R4: lanzadores anclados y Actions del .desktop fuera del host desechable (2026-11-17)

* **Petición:** seguir R4 por los lanzadores anclados sin ventana y las acciones específicas
  (.desktop Actions), sin heredar carpetas ni D-Bus temporales del preview y conservando los
  formatos/handlers de KDE. Las aceptaciones manuales de §247–249 no se repiten.
* **Estado inicial:** el auxiliar ya no estaba abierto (sin proceso, `panel-session.py status`
  inactivo); Breeze activo. En esta ejecución sí hay IPC con Hyprland.
* **Causa leída en fuentes 6.7.5:** LauncherTasksModel::requestActivate/NewInstance/OpenUrls
  (runApp) y las QAction de Backend::jumpListActions/placesActions/recentDocumentActions crean
  KIO::ApplicationLauncherJob dentro del auxiliar; KProcessRunner hereda su entorno (XDG
  temporal, D-Bus privado; DBusActivatable iría al bus privado). KIO no ofrece una API de entorno
  para ApplicationLauncherJob.
* **Lanzadores:** `BwmLaunchRouter` (QIdentityProxyModel + `AbstractTasksProxyModelIface`
  exportada) se inserta con `setSourceModel` entre TaskFilterProxyModel y
  ConcatenateTasksProxyModel. Filas de LauncherTasksModel → petición `launcher` (URL sin icono +
  URLs soltadas); lo demás pasa sin cambios. Concatenación y LauncherTasksModel intactos
  (orden manual comprobado). No se sustituye LauncherTasksModel: TasksModel usa
  `mapFromSource` de su concatenación.
* **Actions:** TaskMenuPolicy identifica las QAction que el Backend original cuelga del
  ContextMenu.qml revisado (hash sin cambios) y compara las últimas con las Actions visibles del
  .desktop (separador/icono/texto sin mnemónicos de KAcceleratorManager y con elisión). Las que
  coinciden encolan `service-action` (nombre de la Action); el handler de KDE sigue conectado.
  Lugares/Recientes salen de datos del host desechable: se enmascaran deshabilitados. «Abrir
  nueva ventana» no aparece en lanzadores puros (KDE: CanLaunchNewInstance=false).
* **Host:** kdeglobals inmutable en el XDG_CONFIG_DIRS desechable con
  `[KDE Action Restrictions][$i] run_desktop_files=false, shell_access=false`
  (`native_launch.write_host_policy`, O_EXCL, en preview-isolated.py y check-local.py). KIO
  deniega antes de crear procesos; el arranque del preview exige `inProcessLaunchDenied=true`.
* **Helper:** native-tasks.py `launcher`/`service-action` sin identidad de ventana, Breeze
  revalidado bajo el bloqueo nativo, entorno original restaurado → `--launch-task-application`
  → ApplicationLauncherJob(KService|KServiceAction). Resolución como runApp (applications:,
  preferred:, .desktop local) sin su respaldo OpenUrlJob/ejecutable; otros esquemas rechazados.
  La reconstrucción de jumpListActions (GPL-2.0-or-later en KDE) vive en launchrouter.cpp, no
  en el archivo LGPL de §248.
* **Pruebas locales:** CTest 13/13 normal y 13/13 ASan (detect_leaks=0), incluidos aquí los
  fixtures Wayland nativos (native-task-thumbnail y delegate-render también con ASan, por
  primera vez en este ejecutor). Lanzamiento KDE real con app propia en XDG temporal: lanzadores
  applications:/file:/preferred://terminal configurado, dos Actions, entorno original
  restaurado, rechazos (oculta/desconocida/esquema/campos extra/sin terminal) y KIOSK del host
  denegando una petición válida. PanelTaskTest 4/4 por PanelSession: ventanas siguen por
  BwmTaskSource, tres peticiones de lanzador, menú original con «Compose & send», NoDisplay
  oculta, Lugares enmascarados, ningún lanzamiento interno, orden manual preservado. Python R4 155
  (+3), skins/puente 27. Evidencia `docs/BREEZE_R4_PINNED_LAUNCH_RESULTS.json`.
* **Sesión (asistente, sin clics):** auxiliar real con --task-actions en MSI: 1 ruta, 4 filas
  de lanzador, 10 ventanas, KIOSK activo, sin error; parada limpia (sin proceso/capas/registro,
  skin plasma). No se pulsó ningún lanzador ni Action.
* **Pendiente:** aceptación manual de un clic en lanzador anclado/Action, foco/activación de
  apps nuevas, Lugares/Recientes, notifyAccessed de KActivities (no reproducido), proveedor de
  escritorios y autoridades del panel diario. Sin commit/push; panel diario intacto.

### 251. R4: aceptación manual de lanzadores anclados y Actions (2026-11-17)

* El asistente lanzó el auxiliar (comando del traspaso con --task-thumbnails) a petición del
  usuario: 3 lanzadores, 1 ruta, KIOSK activo, sin error.
* Usuario confirma: el lanzador anclado sin ventana abre la app; Firefox → clic derecho →
  «New Window» crea una ventana; tras anclar Firefox en la barra auxiliar y cerrarlo, soltar
  una imagen de Descargas sobre el icono abre Firefox con ese archivo; Lugares aparece en el
  menú de Archivos. Telemetría del auxiliar: 3 peticiones de lanzamiento, sin errores.
* La ventana nueva aparece a la derecha y no en el sitio del lanzador: es lo original de KDE
  para org.kde.plasma.taskmanager (separateLaunchers=true; launchInPlace sólo con iconsOnly y
  orden manual, main.qml/main.xml 6.7.5). Con icontasks ocupa el sitio del lanzador.
* No medido: foco/activación de la app nueva ni que esté deshabilitada cada entrada de Lugares
  (el usuario confirmó que aparecen). Parada con panel-session.py stop: sin proceso, registro
  ni capas; skin plasma. Sin commit/push; panel diario intacto.

### 252. R4: acciones de ventana restantes y Lugares del menú de tareas (2026-11-17)

* **Petición:** seguir con lo que falte de R4. Se eligen las entradas del menú original que
  tienen backend BWM y estaban vacías o enmascaradas: Mover, Redimensionar, Ocultar de
  capturas, Sin borde, y la sección Lugares de los gestores de archivos.
* **Acciones:** la instantánea añade campos opcionales v1 (`movable`, `windowTagsSettable`,
  `noBorder`, `excludedFromCapture`; ausentes = sin capacidad, tipo erróneo rechaza la
  instantánea entera). BwmTaskSource publica IsMovable/IsResizable/HasNoBorder/CanSetNoBorder/
  IsExcludedFromCapture y la capacidad excludeFromCapture (TaskMenuPolicy levanta la máscara).
  Mover/Redimensionar → `kwin-window.py --native-serialized interactive` (breezebars-interactive
  debe responder «ok»). Borde/capturas → estado deseado `--state on|off` con guardas Lua,
  recibo y relectura de `hyprctl clients`; idempotente. Los llamadores diarios conservan el
  conmutador (`--state toggle` por defecto). Encima/Debajo siguen enmascarados (sin backend).
* **Errata de KDE:** ContextMenu.qml 6.7.5 enlaza «Sin barra de título ni marco» a
  `CanSetNoBoder` (inexistente): sale deshabilitado también en Plasma. No se modifica el QML.
* **Lugares:** con --task-actions, preview-isolated.py copia de solo lectura el
  `user-places.xbel` del usuario (O_EXCL, 1 MiB) al XDG_DATA_HOME desechable. TaskMenuPolicy
  compara cada QAction de Lugar del Backend (título sin mnemónicos/elisión + icono) con las filas
  visibles del mismo KFilePlacesModel y, si es única, la envía como `launcher` (.desktop del
  gestor + URL del lugar), igual que el lambda de KDE. «N lugares más…» y los submenús siguen
  activos; Recientes sigue enmascarado. KIOFileWidgets (paquete kio ya requerido) enlazado.
* **Pruebas locales:** CTest 13/13 normal y ASan; TaskTest 11/11, MenuTest 3/3 (mover/
  redimensionar desde el menú original; en offscreen KDE oculta «Ocultar de capturas»),
  PanelTaskTest 4/4 (Lugares enrutados con URL, ninguno enmascarado); Python R4 163 (8 nuevas,
  con las guardas Lua ejecutadas), skins/puente/kwin 41. Evidencia
  `docs/BREEZE_R4_WINDOW_ACTIONS_RESULTS.json`.
* **Sesión (asistente, kitty desechable en el workspace 9, sin clics):** no-capture on/on/off/off
  y no-border on/off con recibo y relectura correctos; `no_screen_share` true→false; PID ajeno y
  generación caducada rechazados. Ventana cerrada, reload sin errores, foco y workspace intactos.
* **Pendiente:** clic manual de Mover/Redimensionar (mueven el puntero), «Ocultar de capturas»
  en wayland y Lugares propios en la barra auxiliar; Encima/Debajo, geometría de delegados,
  proveedor de escritorios y autoridades del panel diario. Sin commit/push.

### 253. R4: aceptación manual de acciones de ventana y Lugares (2026-11-17)

* El asistente lanzó el auxiliar a petición del usuario (13 ventanas, 4 lanzadores, KIOSK
  activo, `user-places.xbel` copiado). Usuario: «todo revisado, funciona» para Move, Resize,
  Hide from Screencast, Keep Above/Below y Sin borde deshabilitados, y Lugares de Archivos.
  Respuesta general, sin desglose medido por caso. Auxiliar: 16 acciones enrutadas, ninguna
  enmascarada, sin errores; parada limpia (sin proceso, registro ni capas; skin plasma).
* El usuario pide commit y push de este trabajo.

### 254. R4: proveedor de escritorios validado en un Hyprland anidado (2026-11-17)

* **Petición:** seguir con R4. Frente elegido: el proveedor nativo de escritorios, compilado
  desde §218 pero nunca ejecutado en un Hyprland real.
* **Fallo encontrado:** `PLUGIN_INIT` comparaba `__hyprland_api_get_hash()` y
  `__hyprland_api_get_client_hash()` como punteros `const char*`: el módulo lanzaba siempre
  «headers/runtime mismatch» y no podía cargarse nunca. Corregido comparando el texto
  (`std::string`, como breezebars). Ninguna prueba anterior cargaba el módulo real.
* **Método:** `src/bwm-plasma-host/check-desktops-hyprland.py` arranca Hyprland 0.56.2 (el
  mismo binario parcheado) como ventana cliente enviada en silencio al workspace 9 de la sesión,
  carga el módulo SÓLO en esa instancia, fija contador 4 y lo habilita, abre dos kitty propias
  (escritorios 1 y 2) y ejecuta `test-desktops-hyprland`: VirtualDesktopInfo y
  TaskFilterProxyModel originales de KDE, BwmTaskSource alimentada por el `native-tasks.py`
  real y la barrera NativeDesktopControl. Después SIGTERM al grupo del anidado y se retira la
  regla temporal (redefinida sin coincidencias). No es una prueba de CTest: necesita sesión.
* **Resultado (cliente normal y ASan):** arbitraje activo, 4 escritorios; requestActivate de KDE
  aplicado por el dispatcher de Hyprland y cambios de Hyprland reflejados en KDE; el filtro de
  escritorio actual muestra sólo la ventana del workspace activo y sigue la activación;
  contador 4→6→4 en vivo; conexión en pausa ignora peticiones y reanuda; crear/quitar
  rechazados. 6 activaciones aplicadas/observadas, 3 rechazadas, sin error. Módulo nunca
  cargado en tu compositor; foco y workspace intactos; sin instancias residuales.
  Evidencia `docs/BREEZE_R4_NESTED_PROVIDER_RESULTS.json`.
* **Pendiente:** cargarlo al iniciar sesión en tu sesión (make install + arranque + volver a
  entrar; decisión del usuario), preview completo con --native-desktops (la salida anidada no
  tiene descripción para --output), varias salidas reales, estabilidad y cierre de sesión;
  sustitución del panel diario. Sin commit.

### 255. R4: carga opt-in del proveedor de escritorios al iniciar sesión (2026-11-17)

* **Petición:** preparar la carga del proveedor al iniciar sesión (aceptado volver a entrar).
* **Opt-in:** `skins/plasma/scripts/native-desktops.py enable|disable|status` escribe
  `~/.config/bwm/native-desktops.json` (zona gestionada por BWM, no la configuración de texto del
  usuario). Efecto en el siguiente inicio de sesión; nunca carga ni descarga en caliente.
* **Arranque:** `autostart.sh` (bloque 9, sólo al iniciar Hyprland) lanza en segundo plano
  `native-desktops.py startup`: comprueba opt-in, módulo instalado y compilado para el commit en
  ejecución, escribe una guarda pendiente, `hyprctl plugin load`, habilita
  `plugin:bwm_plasma_desktops:enabled`, verifica el diagnóstico, deja la marca
  `$XDG_RUNTIME_DIR/bwm-native-desktops.json` con la instancia y publica el contador una vez;
  a los 60 s estables borra la guarda. Habilitado en todas las skins (una generación por vida
  del módulo; el contador ya se entrega en todas, §228).
* **Guarda contra bucles:** si al arrancar encuentra la guarda pendiente de otra instancia (el
  inicio anterior no se estabilizó: cierre o fallo en los primeros 60 s), desactiva el opt-in,
  avisa y no carga. Un cierre de sesión normal en ese minuto también lo desactiva: se reactiva
  con `enable`.
* **Contador sin sondeo:** el prerrequisito de `hooks.sharedSettings` pasa a ser el opt-in;
  `native_workspaces.py` sólo envía con el módulo cargado en esta instancia (marca de sesión) y
  si no responde `inactive`. El dispatcher reintenta sólo entregas pendientes (no aplicadas ni
  inactivas): fuera el lanzamiento de Python cada 2 s tras aplicar (diseño anterior de §228).
* **Instalación:** `make install` (temporal + mv atómico) con el módulo NO cargado en la sesión;
  idéntico al validado, sin símbolos UNIQUE. Opt-in activado por el asistente a petición.
* **Pruebas:** Python R4 172 (startup 7 nuevas: no opt-in, carga+marca, guarda tras inicio
  inestable, ventana interrumpida, módulo de otra versión/carga fallida/habilitación fallida,
  ya cargado, desactivar), puente/skins/kwin 41; `check-desktops-hyprland.py --via-startup`
  ejecuta la ruta de inicio real en el Hyprland anidado (carga, habilita, contador 4, estable) y
  después pasan los consumidores KDE; sin marca residual ni módulo en el compositor de la sesión.
  Evidencia `docs/BREEZE_R4_PROVIDER_STARTUP_RESULTS.json`.
* **Pendiente:** primer inicio de sesión real con el módulo (status/diagnóstico), preview con
  `--native-desktops` en la sesión, varias salidas; panel diario. Sin commit.

### 256. R4: primer inicio real del proveedor confirmado (2026-11-17)

* **Evidencia del usuario:** `python3 ~/.config/hypr/skins/plasma/scripts/native-desktops.py
  status` confirma optedIn/installed/builtForRunningHyprland/loadedInThisSession true y
  startupGuard vacío. `hyprctl -j bwm-plasma-desktops`: enabled/providerAvailable true,
  arbitrationState active, providerRestartRequired false, 10 escritorios, actual 1,
  configuredCountSource shared-bwm-bridge y lastError vacío. Protocolos/barrera/arbitraje/
  ciclo de vida compatibles con el preflight del auxiliar.
* **Comprobación del asistente:** registro de arranque loaded/stable true; ejecutable
  build/bwm-plasma-host/bwm-plasma-host disponible y panel-session.py status inactive.
  IPC del compositor inaccesible desde el ejecutor; el diagnóstico actual anterior viene
  del terminal del usuario. El nombre corto native-desktops.py no está en PATH: usar la
  ruta completa, sin necesidad de instalar otro comando.
* **Alcance:** todos los contadores de activación están a cero; operationalVerified y
  liveSessionVerified siguen false. El inicio correcto no certifica filtro de tareas,
  activación KDE, varias salidas, cierre de sesión ni sustitución del panel diario.
* **Siguiente:** preview desechable de tareas en MSI con --native-desktops (sin
  --all-desktops), aspecto/miniaturas ya aceptados. Comprobar filtro al cambiar de workspace
  con ventanas distintas y obtener estado fresco del auxiliar. No arrancado aquí; sin
  cambios de código, compilación, carga/descarga de plugins, commit ni push.

### 257. R4: filtro nativo de tareas aceptado en la sesión (2026-11-17)

* El usuario ejecuta el comando de §256 con --native-desktops (sin --all-desktops) en el
  MSI y confirma «correcto, funciona» al cambiar entre workspaces con ventanas distintas.
  Se acepta ese comportamiento del filtro original de KDE; sin mediciones independientes
  por ventana/salida ni certificación de activación solicitada por el proveedor.
* No se repiten miniaturas/lanzadores/acciones ya aceptados. No se ha ordenado cerrar el
  auxiliar. El ejecutor sigue sin acceso al IPC y no puede confirmar el estado vivo de la
  prueba del terminal; su panel-session.py status devuelve inactive.

### 258. R4: diagnóstico nativo de escritorios por salida, sólo lectura (2026-11-17)

* **Implementado:** `src/bwm-plasma-host/check-desktops-session.py`, modo del anfitrión
  --check-native-desktops-session y desktopsessioncheck.{cpp,h}. VirtualDesktopInfo original
  en la conexión Qt, inventario/pareja de proveedor verificados con NativeDesktopControl,
  sin resume ni peticiones de activación (serial 0). No crea ventanas/paneles/capturas,
  registra prueba ni cambia perfiles/configuración del usuario.
* **Comparación:** descripción única con BwmOutput; todas las salidas Qt y Hyprland deben
  coincidir, incluida geometría lógica (monitor_box común), escritorio por nombre efímero
  y por geometría. Proyección de IDs = contador común + vivos/activos, excluidos especiales
  y 99. Lecturas antes/después deben coincidir; cambios, espejo con rectángulos idénticos,
  descripción ambigua, timeout o error de protocolo rechazan el informe. No persiste DP-N.
* **Aislamiento:** raíces XDG temporales y bus inexistente, sin flags BWM_R4 de acciones;
  conserva sólo la conexión Wayland seleccionada para el consumidor. Informe sin ventanas,
  títulos/apps/PID, nombres de workspaces ni entorno. Es una instantánea, no una prueba de
  navegación/activación, captura, logout o sustitución diaria.
* **Comprobado:** compilaciones normal/ASan del anfitrión y test-desktops; Python R4 184/184
  (12 pruebas nuevas); CTest isolated-local-configuration pasa. Modo nuevo rechaza offscreen
  con JSON de error, normal/ASan (detect_leaks=0). El caso nuevo en test-desktops comprueba
  lectura por dos salidas, serial 0/sin ventanas, rechazo de duplicados/salida desconocida
  y conexión sin reanudar; compilado, **no ejecutado**: native-desktop-protocol bloqueado en
  wl_client_create EPERM antes de Qt. No es un pase Wayland. Ejecución real del wrapper
  también bloqueada por IPC; se deja para el terminal del usuario, sin pedir otro login.
* **Evidencia:** docs/BREEZE_R4_DESKTOP_OUTPUTS_RESULTS.json. Sin nuevos requisitos,
  cambios/despliegue de plugin, reinicio de shell, commit ni push. Activación real desde
  KDE, lectura de todas las salidas en sesión, logout y autoridades diarias pendientes.

### 259. R4: lectura nativa de los dos monitores validada en sesión (2026-11-17)

* **Evidencia del usuario:** salida de check-desktops-session.py con passed/readOnly true,
  bindingVerified true, IDs 1–10 y contador común 10. LG ULTRAFINE: geometría lógica
  [2560,0,3840,2160], escritorio 10; MSI MAG 274Q X24: [0,720,2560,1440], escritorio 1.
  Ambas salidas verified true; escritorio global 1, cero peticiones de activación y ventanas.
* **Alcance:** snapshot coincidente de VirtualDesktopInfo original y Hyprland por descripción,
  geometría y escritorio por nombre/geometría. No certifica navegación, activación solicitada
  por KDE, otras disposiciones/escalas ni logout/panel diario. El usuario interrumpe el preview
  con Ctrl+C antes del diagnóstico; sin telemetría independiente de limpieza desde el ejecutor.
  Evidencia conservada en docs/BREEZE_R4_DESKTOP_OUTPUTS_RESULTS.json.

### 260. R4: ciclo explícito de activación sobre los escritorios ya visibles (2026-11-17)

* **Implementado:** check-desktops-activation.py --focus-cycle y modo del anfitrión
  --check-native-desktops-focus-cycle. VirtualDesktopInfo.requestActivateOnScreen original
  visita los pares escritorio/salida ya activos y vuelve a la salida inicialmente enfocada;
  nunca llama requestActivate sin salida, crear/quitar ni cambia el escritorio mostrado por
  cada salida. IDs, geometrías y asignaciones deben permanecer iguales durante cada paso.
* **Guardas:** bloqueo compartido del mismo inodo /tmp/bwm-theme-manager.lock (sin truncar/
  borrar) excluye cambios de skin durante el ensayo; bloqueo común native_guard para otras
  acciones experimentales y Breeze comprobada bajo bloqueo. Rechaza workspaces especiales
  visibles antes/después (no ocultar Magic al volver). Consumidor con XDG temporal,
  bus inexistente, sin panel/superficie/captura. Barrera resume antes de actuar y pause al
  terminar o fallar; plazos acotados. Si cambian asignaciones/falla un paso, no restaurar foco
  obsoleto con acciones posteriores. El informe dice si volvió realmente a la salida inicial.
* **Recibos:** Qt debe observar el escritorio global esperado en cada paso conservando los
  escritorios por salida. Wrapper exige estado Hyprland final igual al inicial y deltas exactos
  de accepted/applied/observed/dispatched; ningún rechazo, fallo, cancelación o no-op nuevo.
  Otro consumidor activando a la vez invalida la medición. No certifica foco de una ventana
  concreta/puntero ni navegar a escritorios no visibles.
* **Comprobado:** normal/ASan compilan anfitrión y test-desktops; rechazo offscreen sin emitir
  peticiones, normal/ASan. Python R4 197/197 (13 nuevas, incluidos bloqueos/rechazos/recibos/
  ruta/salida y error sin fallback); isolated-local-configuration pasa. El caso C++ nuevo
  nativeFocusCycleVisitsExistingOutputsAndReturns compila, no ejecutado: prueba nativa
  bloqueada en wl_client_create EPERM antes de Qt. El asistente no ejecuta el ciclo en sesión
  (IPC sigue inaccesible). Ejecutar desde terminal, opt-in explícito, sin otro login.
* **Evidencia:** docs/BREEZE_R4_DESKTOP_ACTIVATION_RESULTS.json. Sin plugin nuevo/despliegue,
  requisitos, reinicio de shell, cambio de configuración personal, commit ni push. Pendientes:
  ejecución del ciclo real, navegación entre escritorios de la misma salida y autoridades/
  cierre/recuperación del panel diario.

### 261. R4: ciclo real fallido y conservación del diagnóstico (2026-11-17)

* **Evidencia del usuario:** check-desktops-activation.py --focus-cycle devuelve passed false,
  activationAttempted true, restoredInitialOutput/paused true y «Native activation was not
  observed with unchanged output assignments». Sólo confirma que el estado final seguía
  igual al inicial; no prueba que visitara el otro monitor ni identifica la causa. El wrapper
  anterior descartaba los pasos/observaciones y el motivo del servidor al devolver error.
* **Corrección del diagnóstico:** conserva nativeDiagnostic y providerAfter aun si el hijo
  falla; C++ añade destino solicitado, lectura fallida/final, geometrías, IDs y estado de la
  conexión. Nuevo --diagnose-last sólo lee los contadores/errores existentes y asignaciones
  actuales: no repite el ciclo, adquiere bloqueos de acciones, abre paneles ni necesita binario.
  Conserva la causa del proveedor aunque la instantánea de sesión no pueda estabilizarse.
* **Reintentos:** el último error histórico de activación no bloquea permanentemente un
  futuro ensayo explícito. Inicial admite ese dato previo; al concluir con éxito se siguen
  exigiendo recibos exactos y ausencia de errores nuevos. No se reintenta automáticamente.
* **PATH:** nombre corto native-desktops.py no instalado en PATH. Ayuda/notificación y
  docs/BREEZE_R4_HANDOFF_CLAUDE.md indican ahora
  `python3 ~/.config/hypr/skins/plasma/scripts/native-desktops.py status` (o enable/disable).
  No se crean enlaces/comandos ni se escribe configuración de usuario.
* **Comprobado:** anfitrión/test-desktops normal y ASan compilan; Python R4 201/201 (4 nuevas,
  17 de activación). Caso C++ nuevo de fallo simulado conserva observación, una petición,
  pausa y estado inicial, sin reintento; sólo compilado, fixture Wayland bloqueado en este
  ejecutor como antes (EPERM). --diagnose-last local devuelve error de IPC, sin acciones.
  Ejecución de diagnóstico real pendiente en el terminal del usuario. No se ha corregido
  todavía un fallo del proveedor ni pedido rebuild/login; sin cambios del plugin, commit/push.

### 262. R4: corregida la doble acción de foco del proveedor (2026-11-17)

* **Diagnóstico real del usuario:** 1 accepted/dispatched, 0 applied/observed, 1 failed/rejected;
  activation-readback-mismatch / activation-application-denied. Proveedor activo/disponible,
  sin error general ni cola; LG/10 y MSI/1 conservados. La petición sí llegó al backend: no
  es fallo de PATH, asociación Wayland ni módulo ausente.
* **Causa reproducida:** applyExact llamaba focusMonitor(target) y después changeWorkspace
  al workspace ya activo. Los cuerpos originales Hyprland 0.56.2 muestran que la segunda
  llamada puede simular movimiento de puntero y devolver el foco al monitor anterior si el
  destino está vacío y cursor:no_warps impide llevar allí el puntero. La configuración común
  declara no_warps=true; este escenario reproduce el recibo observado, sin afirmar que se
  midiera el contenido del workspace real. No se modifica esa preferencia del usuario.
* **Corrección:** workspace ya activo → sólo Actions::focusMonitor(owner); inactivo → sólo
  Actions::changeWorkspace(workspace), sin prefoco que omita su rama nativa entre salidas.
  Se conservan IDs absolutos, validación de pertenencia a salida, barrera y lectura estricta:
  casos nativos aún divergentes siguen rechazados. Diagnóstico activationRoutingVersion=2;
  --focus-cycle rechaza el módulo antiguo antes de iniciar acciones. --diagnose-last sigue
  leyendo versiones antiguas.
* **Pruebas:** check-activation-routing.py compila el applyExact real y WorkspaceActivator
  con tres cuerpos upstream exactos, fijados por SHA256, sobre andamiaje de foco/puntero de
  datos (BSD conservada, THIRD_PARTY_NOTICES actualizado). 48 combinaciones normal y ASan,
  tres reproducciones del fallo anterior; contador de errores/lectura estricta conservados
  para destinos inactivos que el upstream no confirma. CTest nuevo pasa en ambos builds;
  Python R4 202/202, plugin real compilado para efb5099..., cero símbolos UNIQUE. Esto no es
  un Hyprland anidado ni prueba Wayland/foco real; esa aceptación corregida queda pendiente.
* **Instalación verificada:** make install (temporal + mv atómico), binario instalado igual
  al build, inodo distinto y descriptor abierto al anterior conserva exactamente sus bytes.
  SHA256 213f2885... → 4304230d892209cc1919f28542c7f6528f4ec7c21d58efc07dda52532b91fd9f.
  Nunca se carga/descarga ni se escribe sobre el inodo cargado. La sesión actual sigue en
  generación anterior; **adopción al próximo login**, sin otro emerge/sudo ni restart-shell.
* **Evidencia:** docs/BREEZE_R4_DESKTOP_ACTIVATION_RESULTS.json. Próximo paso del usuario:
  cerrar sesión, volver a entrar y ejecutar check-desktops-activation.py --focus-cycle.
  La marca de versión impide repetir accidentalmente sobre el módulo anterior. Sin commit/
  push; R4/panel diario no se declaran terminados.

### 263. R4: activación por salida corregida y validada en sesión (2026-11-17)

* **Evidencia del usuario:** check-desktops-activation.py --focus-cycle devuelve passed true,
  dos peticiones y dos pasos verified: LG/escritorio 10 y vuelta a MSI/1. Deltas exactos de
  accepted/applied/observed/dispatched = 2; failed/rejected/cancelled/noops = 0. Estado final
  igual al inicial: escritorio global 1, asignaciones y geometrías LG/10 y MSI/1 conservadas.
* **Barrera:** misma conexión, asociación verificada y un global de gestión/control visible;
  serial final 2, confirmed/confirmedPaused true, resumed false y lastError vacío. Sin
  ventanas/paneles/capturas ni cambios de configuración. El preflight del script exige
  activationRoutingVersion=2: el pase acredita la adopción de esa ruta en esta ejecución,
  sin consulta IPC independiente del ejecutor.
* **Alcance:** queda resuelto y aceptado el bloqueo de activación entre los escritorios ya
  visibles en estas dos salidas. No certifica foco de una app/puntero, navegar a escritorios
  no visibles, otras disposiciones/escalas, teardown/logout o panel diario. Los indicadores
  generales operationalVerified/replacementReady/r4Complete no se elevan por este caso.
* **Registro:** evidencia en docs/BREEZE_R4_DESKTOP_ACTIVATION_RESULTS.json; actualizados
  estado, plan y traspaso. Sólo documentación/evidencia, sin repetir pruebas aceptadas,
  cambiar código/runtime, compilar, reinstalar, reiniciar ni hacer commit/push.

### 264. R4: navegación segura a un escritorio no visible preparada (2026-11-17)

* **Implementado:** check-desktops-activation.py --workspace-cycle, modo del anfitrión
  --check-native-desktops-workspace-cycle y API nativeDesktopWorkspaceCycle. Reutiliza el
  ciclo/barrera existente: VirtualDesktopInfo.requestActivate hacia un ID ya anunciado,
  verifica el nuevo workspace en el monitor original (por nombre y geometría) conservando
  todas las otras salidas, y vuelve al ID inicial. Dos recibos estrictos y pausa final.
* **Selección:** sólo ID configurado 1–N/1–100, no 99, ausente del inventario de workspaces
  vivos (no se reutiliza uno personal aunque tenga cero ventanas). Lee workspacerules y
  requiere vínculo explícito único al monitor actual, no persistente y sin onCreatedEmpty.
  Declara fuera de alcance reglas de vínculo/creación no literales que no pueda auditar.
  No edita las reglas ni la configuración del usuario. Repite selección antes de arrancar;
  si cambia, no envía acciones. Nombres de conectores sólo se comparan con el dato efímero
  actual para leer reglas existentes; identidad/informes por descripción.
* **Motivo:** WorkspaceState::create de Hyprland 0.56.2 consulta vínculos de workspace aun
  si recibe un monitor explícito. No asumir que un ID no materializado aparecerá donde
  está el foco. Puede materializar un ID proyectado; no usa requestCreateDesktop/remove ni
  añade preferencias. Hyprland conserva/reclama después ese workspace según su ciclo normal.
* **Guardas:** Breeze/bloqueos/ausencia de especiales como §260; destino ordinario no visible
  en ninguna salida e incluido en inventario KDE; geometrías/IDs estables y asignaciones
  esperadas por paso. Fallo/cambio externo pausa y no dispara restauración obsoleta. Estado
  final compara contra el original incluso si el intento fallido esperaba otro workspace.
  No certifica una instantánea atómica frente a entrada/edición externa concurrente.
* **Comprobado:** anfitrión y test-desktops normal/ASan compilan; Python R4 212/212 (10 nuevas),
  isolated-local-configuration pasa. Modo nuevo rechaza offscreen sin peticiones en ambos
  builds. Caso Qt/Wayland de ida/vuelta, otros monitores intactos, destinos inválidos y fallo
  sin reintento añadido, sólo compilado: fixture bloqueado en wl_client_create EPERM antes
  de Qt. No ejecutado el nuevo ciclo en sesión desde el asistente; aceptación real pendiente.
* **Evidencia:** docs/BREEZE_R4_WORKSPACE_NAVIGATION_RESULTS.json. Sin cambios de plugin,
  despliegue, login/reinicio de shell, requisitos, configuración personal, commit ni push.
  El ciclo por salidas de §263 ya está aceptado; no se pide repetirlo. R4/panel diario abiertos.

### 265. R4: navegación al escritorio no visible validada en sesión (2026-11-17)

* **Evidencia del usuario:** --workspace-cycle devuelve passed true y selectedDesktop 3.
  VirtualDesktopInfo.requestActivate verifica MSI/1 → MSI/3 → MSI/1: ambos pasos verified,
  deltas accepted/applied/observed/dispatched = 2, failed/rejected/cancelled/noops = 0.
  No se infiere por qué no eligió el ID 2: no se aportó el inventario usado por la selección.
* **Estado final:** global 1, asignaciones iniciales conservadas, LG/10 y MSI/1 con sus
  geometrías previas. Asociación verificada y globals de gestión/control únicos visibles;
  serial 2, pausa final confirmada, resumed false, lastError vacío. Cero ventanas/paneles/
  capturas y configurationChanged false. Lectura por nombre y geometría coincidente.
* **Alcance:** aceptado este recorrido a un ID libre no visible del mismo monitor. No
  certifica relocalización entre salidas, navegación a workspaces personales ocupados,
  foco de una ventana/puntero, otras disposiciones/escalas o teardown/logout. Panel diario,
  autoridades, selección/persistencia y recuperación siguen pendientes; no se elevan los
  indicadores generales operationalVerified/replacementReady/r4Complete.
* **Registro:** BREEZE_R4_WORKSPACE_NAVIGATION_RESULTS.json y estado/plan/traspaso actualizados.
  Sólo evidencia/documentación, sin repetir ensayos aceptados ni tocar código/runtime,
  compilar, reinstalar, reiniciar o hacer commit/push.

### 266. R4: recuperación de perfiles cuyo estado actual no se puede abrir (2026-11-17)

* **Problema:** restore exigía construir ProfileStore, que valida head y la generación
  actual antes de leer la copia elegida. Un head ausente/roto o archivo nativo perdido
  impedía recuperar incluso con un snapshot íntegro.
* **Cambio:** recover(root, snapshot-id) toma el mismo lease exclusivo antes de inspeccionar,
  valida inventario/hashes y layout con Corona sobre copia, prepara otra generación y
  registra el head anterior byte por byte (o su ausencia), hash y snapshot bajo recoveries.
  Publica ambos directorios completos antes de sustituir head con QSaveFile; conserva
  generaciones y claves desconocidas legibles, detecta cambios de presencia/bytes y rechaza
  versiones futuras. Sin autoelección de copia, GC, CAS global ni promesa ante corte de luz.
* **Entrada:** --recover-profile SNAPSHOT_DIR y preview-isolated.py --profile DIR
  --recover-snapshot ID. El envoltorio evita el preflight que exigía head sano; ejecuta
  offscreen sin compositor, bus de sesión ni registro de preview, y termina.
* **Comprobado:** fixture propio de widget con opciones/valores nativos y desconocidos;
  head roto/vacío/no objeto/generación inválida/ausente, generación incompleta, reapertura
  desde proceso nuevo, escritura tardía de KSharedConfig sólo en la ruta vieja; rechazo
  de copia alterada/inventario cambiado/layout rehasheado con bindings distintos, IDs/rutas
  inválidos, aliases y versión futura sin cambiar head. Autoridad XDG físicamente fuera de
  /tmp, lease rechazado por otro proceso y recuperación/reapertura con CLI real. Wrapper
  real sobre head ausente y CLI real sobre JSON roto. Regresión local normal/ASan pasa;
  215 pruebas Python R4 (tres nuevas) pasan. ASan con detect_leaks=0 por bibliotecas Qt/KDE.
* **Límites:** sólo perfiles de fixtures. Sin activar, seleccionar, retirar o reemplazar
  la barra diaria; sin prueba de logout/crash/corte de energía. Recoveries quedan en el
  perfil original y no se exportan con los snapshots. Sin dependencias, cambios de plugin,
  reinicio/login, configuración personal, commit ni push. §263/§265 no se repiten.
  R4/replacementReady/r4Complete/autoridades y fallback diarios siguen abiertos.
* **Evidencia:** docs/BREEZE_R4_PROFILE_RECOVERY_RESULTS.json; arquitectura, resultados,
  README, plan y traspaso actualizados.

### 267. R4: elección persistente y apertura del perfil seleccionado (2026-11-17)

* **Cambio:** ProfileSelection conserva nombre, procedencia y revisión bajo
  panel-profiles/.selection/selection.json en la autoridad XDG existente. Sólo metadatos de
  integración, no opciones de widgets/vistas ni formato de tema. Consulta sin crear estado
  ausente, cambios con revisión esperada, guardado atómico, claves ajenas conservadas y
  misma elección sin escritura. Vaciar conserva contador; no elimina perfiles ni elige otro.
* **Coordinación:** lease de selección antes de los perfiles, siempre no bloqueante.
  Select valida candidato con ProfileStore/Corona; clear permite head/generación rotos o
  perfil desaparecido sin construirlos. Rechaza cambiar/vaciar si el host usa el perfil.
  openSelected resuelve el nombre/procedencia y adquiere ProfileStore bajo el mismo lease;
  el host lo conserva durante Corona, guardado y checkpoint. No usar una ruta de status
  como autorización. Edición/restauración/recuperación cambian generación, no la elección.
* **Entradas:** profile-selection.py --binary BIN status | select NAME --revision N |
  clear --revision N, con raíces auxiliares y bus desechables/offscreen, sin acciones.
  --serve-selected-profile reutiliza ciclo nativo; preview-isolated.py --selected-profile
  --follow-skin pide esa apertura en lugar de capturar una ruta antes de lanzar el host.
  Restricciones de perfiles guardados y bindings por descripción intactas.
* **Comprobado:** fixture XDG físicamente fuera de /tmp: revisión vieja, candidato ausente,
  elección repetida sin escritura, propietario activo, edición y recuperación con lectura
  nativa de opciones, consulta desde proceso nuevo, clear con head roto/perfil desaparecido,
  procedencia distinta y reelección explícita. Rechazo de metadata/versiones/aliases/revisiones
  inválidas, contador agotado y lease de selección ocupado. Proceso real seleccionado sin
  salidas visibles: confirma control, retiene lease, se detiene, sincroniza y hace checkpoint.
  CLI/envoltorio reales select/status/clear y limpieza; cinco tests Python nuevos del entorno,
  restricciones y modo seleccionado. Regresión local normal/ASan y 220 pruebas Python R4 OK.
  ASan con detect_leaks=0; no certifica ausencia de fugas de Qt/KDE.
* **Límites:** intención persistente y preview explícito, no activación/autostart/takeover ni
  recuperación automática de la barra diaria. profileValidated es inspección puntual y puede
  ser false por lease ocupado; no es salud de sesión. JSON de selección corrupto se rechaza,
  no se reinicia automáticamente. Nombre/procedencia no firma la instalación; sin CAS global
  ni ensayo de corte de energía/logout. No se escribieron elecciones/perfiles personales ni
  configuración del usuario, ni se reinició shell/plugin/sesión. §263/§265 no se repiten.
  replacementReady/activationAllowed/r4Complete globales false; R4 sigue abierta, sin R5/R7.
* **Registro:** docs/BREEZE_R4_PROFILE_SELECTION_RESULTS.json, arquitectura, README,
  resultados, plan y traspaso. AGENTS/CLAUDE sincronizados; sin requisitos nuevos/commit/push.

### 268. R4: guardado del panel de prueba durante el cierre de sesión (2026-11-18)

* `bwm-power` pide la parada antes de cerrar las aplicaciones y el compositor. El registro
  debe corresponder a la misma instancia de Hyprland y al PID e inicio del anfitrión. La
  parada espera su confirmación de retirada y luego un recibo de la misma revisión, escrito
  por el envoltorio tras recoger el código de salida del proceso. En un perfil guardado,
  el código cero llega tras guardar con Corona, sincronizar, crear el checkpoint y liberar
  el bloqueo del perfil. Una parada ya solicitada conserva su revisión.
* El cierre sigue si el guardado no se confirma. Conserva el diagnóstico en el registro de
  `bwm-power` y tiene un límite de ocho segundos. Una invocación sin instancia, sin registro
  propio o con `--dry-run` no modifica el control de prueba.
* `isolated-local-configuration` ejecuta el envoltorio y anfitrión seleccionado reales con
  un perfil desechable. Fuerza la caída del anfitrión antes del cierre, verifica que no hay
  un checkpoint nuevo, reabre el mismo perfil y comprueba el recibo y el checkpoint en la
  siguiente parada. También comprueba que se retiran registro y control. Python prueba
  instancia ajena, recibo ausente/incorrecto y salida con error. La prueba de `bwm-power`
  sustituye el cierre de aplicaciones y del compositor por funciones Bash.
* La barra de uso diario sigue bajo Quickshell. El arranque automático del panel nativo
  depende de comprobar servicios de widgets y reservas en sesión. También queda por
  verificar el cierre físico de Hyprland. Pruebas y límites en `docs/BREEZE_R4_RESULTS.md`.

### 269. R4: ensayo de reservas para cuatro bordes y varias salidas (2026-11-18)

* `r4-reservation-smoke.py --run` admite `--edge` y varias descripciones con `--output`.
  Para esos ensayos prepara un perfil desechable mediante la migración y el importador
  nativos. Un panel de 48 px con el widget de prueba por salida, con el mismo borde en
  todas ellas. La invocación anterior de una salida y el ensayo de maximizado inferior
  siguen disponibles.
* El informe contrasta fotograma, borde del containment, petición y capa por salida con
  la reserva efectiva de Hyprland. Comprueba geometría estable, cambios limitados al
  borde elegido y vuelta al valor original en todas las salidas. Guarda valores
  observados y esperados por descripción de monitor.
* La regresión offscreen prepara y reabre en otro proceso perfiles de dos salidas para
  cada borde. Python prueba incrementos distintos por monitor y rechazos por borde
  ausente o incorrecto, capas duplicadas y restauración parcial. La lectura IPC del
  ejecutor falló antes de abrir el ensayo. Queda pendiente medir los casos nuevos en
  Hyprland. Se conserva la evidencia anterior del borde inferior del MSI (§208).

### 270. R4: reserva superior simultánea validada en MSI y LG (2026-11-18)

* El usuario ejecutó el ensayo `--edge top` en ambas salidas y devolvió
  `reservationDeltaVerified: true` sin errores. Informe local revisado. Los dos monitores
  mantuvieron escala 1 y giro 0. En ambos, `monitors.reserved` pasó de `[0, 0, 0, 44]`
  a `[0, 48, 0, 44]` y volvió a `[0, 0, 0, 44]`. Cada panel creó una capa superior
  de 640 × 48 px en su salida. Tras cerrar, no quedaron capas del ensayo ni registro activo.
* El ensayo midió reservas. No se solicitó `--maximize`. Los falsos de maximizado y
  área útil del marco son valores de capacidad no ensayada. Quedan pendientes reservas
  laterales, otras escalas y la integración del panel diario. Evidencia en
  `docs/BREEZE_R4_RESULTS.md`.

### 271. R4: secuencia lateral con salida confirmada (2026-11-18)

* `r4-reservation-smoke.py` admite `--edge left --edge right` con una o varias salidas.
  Conserva una medición por borde, compara la segunda línea base con la primera y se
  detiene si el primer ensayo falla. El informe de una sola prueba conserva su formato.
* Cada prueba comprueba que el proceso registrado pertenece al envoltorio que lanzó y a
  la misma instancia de Hyprland. Envía la parada y espera el recibo del guardado, además
  de confirmar que el envoltorio salió correctamente. Si falta, limpia el grupo que creó
  y marca el ensayo como fallido aunque las reservas se hayan restaurado.
* El ensayo offscreen usa el control real para detener el anfitrión de un perfil, confirma
  checkpoint y limpieza. Python cubre la línea base entre bordes, el aborto antes de
  continuar, un anfitrión ajeno y la falta de recibo. El ejecutor sigue sin acceso IPC.
  Pendiente la medición lateral real. La aceptación superior de §270 se conserva.

### 272. R4: corrección de la reserva lateral en Hyprland (2026-11-18)

* El usuario ejecutó izquierda/derecha. La izquierda solicitó 48 px en ambas salidas,
  pero Hyprland mantuvo `[0, 0, 0, 44]` y registró capas de 48 × 24. La retirada quedó
  confirmada, con código 0 y ninguna capa remanente. El derecho no se ejecutó.
* LayerShellQt 6.7.5 enviaba longitud cero al detectar anclajes opuestos. Hyprland 0.56.2
  calcula la longitud sobre el área ya reservada y resta el margen del panel. La reserva
  inferior de 44 px acortaba el panel lateral cada vez que Qt ajustaba la longitud y
  el anfitrión recalculaba el margen. Hyprland omite la reserva si la altura resultante
  es cero o negativa. Con layer-shell v5, el anfitrión fija tamaño explícito, dos
  anclajes, margen cero y `exclusive_edge`. Conserva el comportamiento anterior para
  versiones inferiores. Usa los headers privados del mismo paquete Qt Wayland para
  consultar el registro ya disponible de la conexión.
* Prueba de geometría comprueba los cuatro bordes y la política previa para versiones
  inferiores. La aceptación de sesión izquierda/derecha con el binario corregido sigue
  pendiente. El ensayo superior §270 pertenece al binario anterior.

### 273. R4: reservas laterales confirmadas en MSI y LG (2026-11-18)

* El usuario repitió `--edge left --edge right` con el anfitrión corregido. En ambas
  salidas, a escala 1 y giro 0, la izquierda presentó `[48, 0, 0, 44]` y la derecha
  `[0, 0, 48, 44]`. Ambas pruebas partieron de `[0, 0, 0, 44]` y lo restauraron.
  Hyprland midió una capa vertical de 48 × 640 px por monitor en cada ensayo.
* Ambos envoltorios terminaron con código 0 y recibo de salida confirmado. Sin capas
  ni registro de prueba al terminar cada borde. El ensayo no incluyó maximizado ni
  cambio de escala. Sigue pendiente la integración del panel diario. Resultados
  en `docs/BREEZE_R4_RESULTS.md`.

### 274. R4: inventario interno de bandeja y diagnóstico de su servicio (2026-11-18)

* Plasma 6.7.5 mantiene sus plasmoides de bandeja en el `CustomEmbedded` de
  `org.kde.plasma.systemtray`. El estado añade una lista de hijos vivos por bandeja, con
  ID, paquete, fallo de carga y servicio de activación declarado. Conserva la lista y
  el orden de los widgets directos. No enumera iconos SNI ni hijos no activados.
* Prueba Qt aislada con el tray original y un hijo desechable. Verifica inventario, cambio
  de preferencia, guardado con Corona, checkpoint y lectura en otro proceso. Al retirar
  el hijo deja de aparecer. No cambió el formato de perfil ni sus bindings.
* `r4-session-check.py --tray` comprueba `NameHasOwner`, consulta las propiedades del
  dueño único con autoarranque desactivado y comprueba de nuevo la propiedad. Devuelve
  categoría de dueño, contador de iconos y host registrado, sin PID, nombres de iconos
  ni nombres únicos de bus. La sesión real del ejecutor devuelve `bus-unavailable` y
  crear un bus privado también está bloqueado. La lectura real queda por confirmar.
* Pendientes la integración de la bandeja nativa con el servicio existente y sus
  menús/clics, los servicios de los hijos y la activación del panel diario.

### 275. R4: Quickshell identificado como dueño de la bandeja SNI (2026-11-18)

* El usuario ejecutó `r4-session-check.py --tray`. El mismo dueño respondió a la
  consulta de propiedades y conservó el nombre de bus. `ownerKind: quickshell`,
  `registeredItemCount: 2`, `watcherVerified: true`, `sessionModified: false`.
* Fuentes locales de Quickshell 0.3.2 (`services/status_notifier/watcher.cpp`): acepta
  varios nombres de host que ya son propiedad de un cliente. Su getter
  `IsStatusNotifierHostRegistered` devuelve siempre true. El valor observado no
  verifica el registro de un host concreto. KDE 6.7.5 registra un nombre de host
  propio y consulta el watcher existente para recibir y enumerar los iconos.
* Sigue pendiente probar ese consumo desde el auxiliar nativo, que normalmente usa
  un bus aislado, y verificar alta/baja, menú y clics. No es necesario reemplazar el
  watcher para ensayar esa conexión. `replacementReady` sigue false.

### 276. R4: ensayo de enumeración SNI con el modelo de Plasma (2026-11-18)

* `check-native-tray.py` captura dueño e inventario de Quickshell, usa la bandeja
  original de Plasma y compara las filas SNI identificadas por `DataEngineSource`.
  La salida publica contadores y coincidencia. El digest y los identificadores no
  se publican en el informe. El dueño y el inventario deben seguir iguales al terminar.
* El anfitrión arranca offscreen en un proceso nuevo y con raíces XDG desechables.
  `xdg-dbus-proxy` autoriza su nombre exacto `org.kde.StatusNotifierHost-<PID>`, la
  lectura del watcher, el registro de host y las dos señales de alta/baja de items.
  La sonda comprobó el PID mediante `exec`. El anfitrión no toma el nombre del watcher.
  El proxy y su conexión se retiran al terminar. Proxy opcional declarado en requisitos.
* `--probe-native-tray-model` comprueba pertenencia al bus de su nombre temporal. La
  prueba aislada confirma los roles de la bandeja original y el lanzador usa dobles
  de los procesos para validar el orden de arranque y los permisos. El ejecutor no pudo
  consultar D-Bus real. Quedan pendientes enumeración de sesión y las propiedades,
  clics, menús y cambios de iconos.

### 277. R4: enumeración SNI nativa confirmada con Quickshell (2026-11-18)

* `check-native-tray.py` devolvió `passed: true` en la sesión del usuario. Quickshell
  conservó la propiedad del watcher con dos iconos. El modelo original de Plasma
  recibió dos filas con los mismos identificadores y el anfitrión confirmó la propiedad
  de su nombre temporal. La lista y el dueño coincidieron antes y después del ensayo.
* El ensayo se ejecutó fuera de pantalla. Quedan por comprobar las propiedades de cada
  icono, las altas/bajas durante la ejecución, el pintado, los clics y los menús.
  `replacementReady` sigue false. Evidencia en `docs/BREEZE_R4_RESULTS.md`.

### 278. R4: ensayo de estado e iconos SNI con permisos por objeto (2026-11-18)

* `check-native-tray.py --properties` concede `Properties.GetAll` al servicio y la
  ruta de cada objeto anunciado. xdg-dbus-proxy 0.1.8 deriva filtros para nombres
  únicos de sus alias. El comprobador busca un alias adquirido del mismo dueño y
  comprueba el dueño con `GetNameOwner`. Nombres activables, el bus y el watcher
  quedan excluidos de las reglas de lectura de items. Sin alias, el resultado
  indica cobertura parcial. La elección y los dueños se comparan al terminar.
* El modelo original de KDE debe exponer estado SNI y categoría, y su `QIcon`
  debe producir un pixmap lógico de 22 px. La interpretación del estado se corrige
  en §282. El informe sólo incluye
  contadores y confirmación. Obtener un pixmap no prueba presentación, clic ni
  menú en Wayland. El ensayo anterior de enumeración conserva su alcance.
* Pruebas de reglas exactas, alias que cambian de dueño, nombres activables y
  contadores incompletos. Compilación normal/ASan y rechazo de bus ausente
  comprobados. El ejecutor sigue sin acceder al bus real.

### 279. R4: diagnóstico de cobertura del filtro SNI (2026-11-18)

* El usuario ejecutó `--properties`. KDE conservó la coincidencia de sus dos filas
  y el watcher no cambió. `filterableItemCount`, `nativePropertiesCount` y
  `nativeUsableIconCount` fueron 0. El informe anterior no distinguía por qué.
* La resolución usa `ListNames` y `GetNameOwner` del bus, sin depender de la tabla de
  credenciales de `busctl list`. Informa cuentas de nombres únicos sin alias, nombres
  activables y dueños desaparecidos. Para los dos primeros supuestos puede consultar
  tres propiedades escalares, con destino al dueño único y autoarranque desactivado.
  No autoriza ese destino en el proxy ni sustituye lo leído por el modelo de KDE.
* Pruebas Python de alias, dueño cambiado, nombre activable, desaparición y consulta
  directa sin publicar nombres. La causa exacta del 0/2 queda por confirmar en sesión.
  Sin cambios C++ o del filtro por método/objeto.

### 280. R4: lectura SNI por nombre único sin alias (2026-11-18)

* El usuario confirmó dos nombres únicos sin alias y dos lecturas escalares directas.
  Un elemento anunció un icono por nombre. El filtro estándar dejó las dos filas KDE
  sin propiedades. Enumeración y dueño de Quickshell se mantuvieron.
* `build-tray-proxy.py` valida el archivo original de `xdg-dbus-proxy` 0.1.8 y aplica
  un parche local. Las reglas nuevas aceptan sólo `Properties.GetAll` en una ruta
  exacta de un nombre único. El ensayo `--properties` usa ese binario si está presente
  y declara `uniqueNameFilter: exact-object`. Compara identidad del bus, watcher,
  objetos y dueños. La enumeración ordinaria sigue con el proxy del sistema.
* Variante compilada en `build/bwm-plasma-host/tray-proxy`, con versión identificable.
  El ensayo C del filtro acepta la llamada exacta y rechaza otro objeto, nombre o
  método. El parser rechaza comodines y señales para nombres únicos. 237 pruebas
  Python R4 pasan. El ejecutor tampoco puede crear un bus temporal. Pendiente
  validar propiedades y pixmaps con el modelo nativo en la sesión real.

### 281. R4: arranque del proxy con reglas para nombres únicos (2026-11-18)

* La sesión preparó las dos reglas exactas y devolvió `native-tray-probe-timeout`
  antes de observar el modelo nativo. Quickshell seguía siendo el dueño en la
  lectura inicial. La comparación final quedó pendiente.
* El arranque del proxy consultaba `GetNameOwner` para cada nombre del filtro.
  Para un nombre único, el bus devuelve el mismo nombre. Guardarlo como alias
  hacía recursiva la consulta de su política. La variante local omite esa consulta
  para nombres únicos y excluye esos nombres de la tabla de alias. Conserva las
  reglas `GetAll` por objeto y la suscripción al cambio de dueño.
* La regresión C falla con la variante anterior y pasa con `0.1.8+bwm-sni-unique-2`,
  publicada en el directorio `build/` del repositorio. Pasan 237 pruebas Python R4.
  El informe identifica la etapa si se agota el plazo y distingue una salida del
  proxy durante el ensayo. Pendiente repetir `--properties` en la sesión Breeze.

### 282. R4: lectura del estado real del modelo SNI (2026-11-18)

* La sesión volvió a enumerar las dos filas de KDE con el proxy corregido y dos
  reglas exactas. Quickshell y los objetos conservaron su identidad. El comprobador
  informó cero propiedades y cero pixmaps.
* En Plasma 6.7.5, los roles `Status` y `status` convierten el estado recibido a
  `Plasma::Types::ItemStatus`. El comprobador había esperado las cadenas del bus.
  Ahora acepta los valores de estado SNI mediante su representación en `QVariant`,
  exige categoría y cuenta los pixmaps de 22 px de forma independiente.
* La regresión reproduce el retorno implícito de `StatusNotifierModel::data` y
  rechaza estados desconocidos, categorías vacías y cadenas del bus. El caso
  falló con la lectura limitada al tipo enum y pasa al aceptar el entero que
  devuelve el modelo. Pasan `isolated-local-configuration` y 237 pruebas Python R4.
  Pendiente repetir `--properties` en Breeze con el anfitrión recompilado.

### 283. R4: propiedades y pixmaps SNI confirmados en Breeze (2026-11-18)

* `check-native-tray.py --properties` pasó en la sesión. El watcher de Quickshell
  conservó los dos iconos y sus objetos. El modelo nativo de KDE coincidió con el
  inventario y poseyó su nombre temporal. Las dos reglas exactas dieron dos filas
  con propiedades y dos pixmaps de 22 px.
* La aceptación cubre la lectura fuera de pantalla y conserva `replacementReady: false`.
  Quedan pendientes los cambios en vivo, la presentación en el panel y las acciones.

### 284. R4: ensayo aislado de cambios SNI en el modelo original (2026-11-18)

* `check-native-tray-events.py` lanza `test-plasma-tray-events` en Qt offscreen y
  un D-Bus privado sin directorios de activación. Un watcher de prueba y un icono
  propio tienen conexiones distintas. El modelo es el plasmoide KDE instalado.
* Tras leer un inventario vacío, el modelo debe incorporar la fila de la conexión
  de prueba, mostrar estado activo y un pixmap rojo, pasar a pasivo con `NewStatus`,
  mostrar un pixmap azul con `NewIcon` y retirar la fila al caer su dueño. El
  ensayo cubre la reacción del modelo al protocolo en el bus privado. La prueba
  de sesión §283 cubre por separado la lectura filtrada de propiedades.
* Binario compilado y formato de pixmaps `a(iiay)` comprobado. El ejecutor recibe
  `Operation not permitted` al abrir el socket del bus. El ciclo integrado sigue
  pendiente en la terminal del usuario. Se mantienen pendientes los eventos bajo
  el proxy y las acciones y presentación del panel.

### 285. R4: ciclo SNI del modelo original confirmado en D-Bus privado (2026-11-18)

* La terminal del usuario ejecutó `check-native-tray-events.py`. QtTest informó
  cuatro pases, incluido `originalTrayTracksItemLifecycle`. Se verificaron alta,
  estado pasivo, cambio de pixmap y retirada tras desconectar al productor.
* El aviso de KWindowSystem sobre el plugin de plataforma apareció en Qt
  offscreen. El ensayo acreditó la reacción del modelo en el bus privado.

### 286. R4: ensayo del ciclo SNI con señales por objeto en el proxy (2026-11-18)

* La variante local `0.1.8+bwm-sni-unique-3` admite permisos explícitos de
  `NewStatus` y `NewIcon` por nombre único y ruta exactos. Comprueba miembro,
  interfaz, ruta y origen con el filtro de broadcasts. `--properties` en sesión
  sigue pidiendo sólo `GetAll` para cada icono.
* `check-native-tray-events.py --filtered` dirige la conexión por defecto de Qt
  al proxy. Watcher y productor abren sus conexiones al bus privado. Antes del
  ciclo, el ensayo exige `AccessDenied` al pedir propiedades de otra ruta del
  mismo productor. El ciclo positivo sigue comprobando alta, cambios y retirada.
* Pasan la compilación del proxy y del ensayo, el filtro C y 237 pruebas Python.
  La prueba C incluye rechazos por ruta, origen, miembro y dirección incorrectos.
  Pendiente `--filtered` en terminal. La presentación y las acciones siguen abiertas.

### 287. R4: ciclo SNI filtrado confirmado en D-Bus privado (2026-11-18)

* `check-native-tray-events.py --filtered` pasó en terminal. QtTest informó cuatro
  pases y cero fallos en 229 ms. El cliente KDE recibió el alta, los cambios de
  estado y pixmap y la retirada del icono. La consulta a otra ruta fue denegada.
* El aviso de KWindowSystem corresponde a Qt offscreen. Esta prueba cubre los
  eventos a través del proxy en el bus privado. Los clics y menús en Wayland
  siguen pendientes.

### 288. R4: ensayo privado de peticiones SNI desde el plasmoide original (2026-11-18)

* `check-native-tray-events.py --actions` invoca `activate`, `secondaryActivate`,
  `scroll` y `openContextMenu` en el plasmoide de Plasma. El productor de prueba
  debe recibir cuatro llamadas con coordenadas, giro y orientación exactos.
  El productor no anuncia un menú importable. KDE debe recurrir a `ContextMenu`.
* `--filtered` conserva la política de lectura y señales. El caso añade una
  petición `Activate` sobre el objeto de prueba ya registrado y exige
  `AccessDenied` y cero acciones recibidas. Las dos modalidades son excluyentes.
* Compilación, comprobación Qt del token vacío en offscreen, firma de los
  pixmaps y 237 pruebas Python aprobadas. La apertura del bus privado sigue
  bloqueada en el ejecutor. Pendiente `--actions` en terminal. Los tokens de
  Wayland y la apertura visual de menús siguen pendientes.

### 289. R4: peticiones de activación, rueda y menú SNI confirmadas (2026-11-18)

* `check-native-tray-events.py --actions` pasó en terminal. QtTest informó cinco
  pases y cero fallos en 432 ms. El icono de prueba recibió las cuatro peticiones
  enviadas por el plasmoide, con los argumentos esperados.
* KDE avisó que usaría `ContextMenu` al faltar un menú D-Bus. Era el caso de
  prueba previsto. La importación de un menú y su acción quedan para §290.

### 290. R4: ensayo privado de importación y acción de un menú D-Bus (2026-11-18)

* `check-native-tray-events.py --menu` levanta un `KStatusNotifierItem` con su
  exportador D-Bus en el bus privado y espera a que el modelo de Plasma lo
  registre. El watcher responde a `ProtocolVersion` para el productor nativo.
* La entrada original `openContextMenu` debe abrir fuera de pantalla un `QMenu`
  importado con una acción habilitada y otra deshabilitada. El ensayo activa la
  primera y espera el recibo en el `QAction` del productor.
* Compilación y pruebas Python comprobadas. `KF6StatusNotifierItem` se enlaza
  en el objetivo de prueba. El ejecutor sigue sin poder abrir el socket del
  bus privado. Pendiente el resultado de `--menu` en terminal y la presentación
  del menú con entrada real en Wayland.

### 291. R4: importación y acción del menú D-Bus confirmadas (2026-11-18)

* `check-native-tray-events.py --menu` pasó en terminal con cinco pases, cero
  fallos y cero omisiones en 223 ms. Plasma importó las dos opciones, conservó
  la opción deshabilitada y devolvió al productor el evento de la habilitada.
* Qt offscreen informó que no podía elevar la ventana ni capturar el teclado.
  El daemon del bus privado también registró un `UnknownObject` del productor
  al terminar. La comprobación de las opciones y la acción pasó.

### 292. R4: ensayo de menú SNI anclado y clic real en Wayland (2026-11-18)

* `check-native-tray-events.py --menu-wayland` usa el socket Wayland del usuario
  y conserva el watcher, el productor y las raíces XDG en el ensayo privado.
  Crea una capa propia sin reserva en la pantalla primaria que elige Qt. El
  clic en el botón abre el menú con un asiento y serial reales. El menú debe
  adquirir el rol `xdg_popup`, quedar expuesto y usar la capa como padre
  transitorio, con el anclaje superior esperado. Un clic en «Test action» debe
  llegar al productor. El ensayo retira la capa al salir.
* En ambos modos de menú, se cierra el `QMenu` y se espera una lectura de
  `com.canonical.dbusmenu.Version` antes de destruir al productor. La lectura
  se encola después de `Event("closed")`, para que el exportador siga vivo al
  despachar el cierre. Se mantiene la política del bus privado.
* Compilación y 237 pruebas Python aprobadas. El ejecutor sigue sin poder abrir
  el socket del bus privado. Pendiente `--menu-wayland` en terminal y confirmar
  si el nuevo cierre evita el aviso al repetir el ensayo. Los resultados de
  §291 acreditan sólo Qt offscreen. `replacementReady` sigue false.

### 293. R4: menú Wayland confirmado y selección del monitor enfocado (2026-11-18)

* `--menu-wayland` obtuvo cuatro pases y cero fallos en 15,157 s. El usuario abrió
  el menú y eligió la acción. Se confirmaron el rol `xdg_popup`, el padre y el
  anclaje dentro de la capa de prueba. No apareció el aviso D-Bus de §291.
  El usuario indicó que la capa se abrió en el monitor equivocado.
* El lanzador consulta ahora `hyprctl -j monitors` antes de crear la capa. Usa
  la descripción del monitor que tiene el foco. `--output` permite indicar otra
  descripción. El auxiliar emplea el resolver común de Qt, asigna la pantalla
  antes de crear la superficie y comprueba que Qt atribuya la capa y el popup
  a esa pantalla. Una salida no identificable detiene el ensayo.
* Compilación, resolución Qt de descripciones y pruebas Python de selección por
  foco verificadas. La ubicación física del ensayo actualizado queda por observar
  en sesión. El panel diario sigue fuera del ensayo.

### 294. R4: comprobación de maximizado en varios bordes (2026-11-18)

* `r4-reservation-smoke.py --maximize` admite cualquiera de los cuatro bordes
  y secuencias en una sola salida. Cada prueba crea su propia ventana y panel,
  compara el marco con el área útil real y exige restauración de las reservas
  y confirmación de salida. Se conserva el límite de escala 1 y giro 0.
* La secuencia compara con la primera línea base, se detiene si falla la reserva
  o el marco explícito y muestra `maximizedEdges` con el resultado por borde.
  El resultado automático se informa por separado. Si se solicita refrescar
  el puente, se hace una vez antes del primer ensayo.
* 241 pruebas Python R4 pasan. Los perfiles nativos de arriba, izquierda y
  derecha se importaron en Qt offscreen con su borde persistido. El ejecutor
  se detuvo antes de crear ventanas por falta de acceso a Hyprland. Pendiente
  ejecutar la secuencia en sesión. El panel diario queda fuera del ensayo.

### 295. R4: maximizado en tres bordes validado en MSI (2026-11-18)

* El usuario completó superior, izquierdo y derecho con `--maximize` y tres
  resultados dinámicos positivos. El informe de sesión confirma reserva de
  48 px por borde, salida limpia y retorno del marco a `[0,720,2560,1396]` en
  los tres casos. La reserva inferior de 44 px en el LG se mantuvo.
* El comprobador usa ahora la observación automática cuando el marco coincide
  con el área útil. Sólo remaximiza tras una discrepancia y anota la fase en
  `remaximizedPhases`. Un ciclo con éxito dinámico conserva el mismo maximizado
  desde antes de abrir el panel hasta después de retirarlo. Las observaciones
  explícitas de respaldo siguen disponibles y su éxito conserva el resultado
  independiente de marco. La evidencia del MSI precede este ajuste del ensayo.
* Las cuatro combinaciones de lectura automática pasan en pruebas Python. El
  IPC de Hyprland sigue inaccesible en el ejecutor. Pendiente medir en el LG
  con el comprobador actualizado. El panel diario queda fuera de la prueba.

### 296. R4: restitución de maximizado al retirar rápidamente una reserva (2026-11-18)

* En LG, el ensayo confirmó los deltas de los cuatro bordes, el marco de los
  cuatro y la salida limpia. Superior y laterales se ajustaron en ambos sentidos
  con un único maximizado inicial. Abajo, la reserva volvió de 92 a 44 px pero
  el marco conservó 2068 px de alto. El maximizado explícito devolvió los 2116 px.
* Se reprodujo la transición `44 → 92 → 44` entre confirmaciones: el observador
  aplicaba la reducción, conservaba en caché la primera confirmación e ignoraba
  la vuelta al área anterior. Ahora invalida esa confirmación al observar el
  cambio de firma, aunque aún falte confirmar o despachar el ajuste. Los
  reintentos se conservan sólo mientras se mantenga la misma firma.
* La regresión falla antes y pasa después. Las guardas de elegibilidad, identidad,
  reglas, decoración y recuento de reintentos se mantienen. Pendiente ejecutar
  sólo el borde inferior en LG con `--refresh-area-watcher` para recargar el
  puente que contiene el observador. El ejecutor carece de IPC de Hyprland.

### 297. R4: retirada inferior en LG validada con el puente actualizado (2026-11-18)

* El usuario ejecutó `--maximize --refresh-area-watcher --edge bottom` en LG.
  El puente confirmó su arranque y el ensayo pasó. El informe privado confirma
  reserva `44 → 92 → 44`, altura de marco `2116 → 2068 → 2116`, ningún
  remaximizado durante las transiciones y salida limpia del panel.
* La reserva del MSI se mantuvo. Quedan verificados los cuatro bordes por
  separado en ambas salidas, con la escala y giro actuales. Este resultado
  completa la comprobación pendiente del fallo de §296.

### 298. R4: ensayo de maximizado simultáneo en varias salidas (2026-11-18)

* `--maximize` crea una ventana de prueba por cada `--output`, con identidad
  propia. Maximiza todas antes de abrir un panel temporal por salida. Lee
  todos los marcos automáticos antes de aplicar un respaldo explícito.
  `maximizedByOutput` conserva las observaciones y el cierre por salida en
  pruebas de varias salidas. El informe de una salida conserva sus campos.
* La preparación comprueba escala y giro para todas las salidas antes de
  abrir ventanas. El cierre alcanza a cada ventana iniciada aunque falle una
  posterior. Pruebas Python de medición independiente y arranque parcial, y
  perfil de dos paneles importado en Qt offscreen. IPC inaccesible en el
  ejecutor. Pendiente medir ambas ventanas en la sesión al mismo tiempo.

### 299. R4: maximizado inferior simultáneo confirmado en MSI y LG (2026-11-18)

* El usuario pasó `--maximize --edge bottom` con las dos salidas. El informe
  privado confirmó reserva `44 → 92 → 44` en ambas, alturas de marco
  `1396 → 1348 → 1396` en MSI y `2116 → 2068 → 2116` en LG. El anfitrión
  confirmó su salida y las dos ventanas temporales terminaron.
* Ninguna ventana necesitó un maximizado adicional. La prueba acredita la
  configuración de ambas pantallas a escala 1 y giro 0.

### 300. R4: expectativa de marco para escala y giro (2026-11-18)

* `r4-maximized-check.py` admite la escala efectiva y las ocho transformaciones
  Wayland. Hyprland 0.56.2 informa las dimensiones del modo en píxeles físicos
  y la posición y reservas en unidades lógicas. El comprobador intercambia ejes
  para las transformaciones impares, divide por la escala, redondea como el
  compositor y aplica las reservas lógicas. La geometría inválida se rechaza.
* Pasan 247 pruebas Python. 32 geometrías contrastadas con el redondeo de
  hyprutils 0.14.2, incluidos medios píxeles y transformaciones reflejadas.
  Cambio del comprobador. Entrada de sesión e integración a escalas o giros
  distintos de los de §299 pendientes de una disposición que los use.

### 301. R4: redondeo del compositor en maximizado y reajuste (2026-11-18)

* Dos regresiones reprodujeron una diferencia de un píxel en ancho y alto
  al dividir y girar dimensiones que producen medios píxeles lógicos.
  `kwin-window.py` y el observador `kwin_area.py` ahora piden a `monitor_box`
  redondear las dimensiones como Hyprland antes de aplicar las reservas.
* El argumento es opcional y la llamada común conserva el comportamiento
  anterior, incluido el cotejo de geometrías guardadas de las transiciones.
  La expectativa del comprobador de §300 se calcula de forma independiente.
* Pasan las dos regresiones, las 248 pruebas R4 y las suites de ventanas,
  selección de monitor, puente y cambio de skin. La medición en una nueva
  escala o giro sigue pendiente. El puente en ejecución adoptará la corrección
  Python al recargarse por su mecanismo existente.

### 302. R4: maximizado con otras escalas y giros en una salida temporal (2026-11-18)

* Esta sesión tiene acceso IPC a Hyprland. Para no reconfigurar los monitores
  físicos, `r4-geometry-check.py --run` crea una salida headless con nombre
  único y le aplica modo, escala y giro con `hl.monitor`. Cambia la reserva con
  el campo `reserved` de la misma regla, que Hyprland suma a las capas. La ventana
  de prueba de R4 se abre en esa salida sin foco y se maximiza con el gestor común.
  La salida, la regla temporal de ventana y la ventana se retiran al terminar.
* Primer intento: el maximizado explícito coincidió en las cuatro geometrías y
  el reajuste automático falló en todas. `kwin_area.py` rechazaba la instantánea
  entera si un monitor tenía descripción vacía. Con un monitor sin EDID (headless,
  virtual o real sin EDID) el observador dejaba de actuar en todas las salidas.
  La descripción sólo se usa en la firma en memoria. Ahora, si falta, usa el
  nombre del conector. Una salida sin descripción ni nombre sigue rechazada.
* Tras recargar el puente pasaron explícito y automático, sin remaximizar, en
  `1920x1200` escala 1,25 giro 1 y 5, `1920x1080` 1,5 giro 3 y `2560x1600` 1,6
  giro 2. La reserva superior de 48 px se añadió y retiró con el panel diario
  de 44 px en esa salida. Limpieza verificada: salidas físicas, workspaces y
  ventana con foco iguales. Evidencia `docs/BREEZE_R4_GEOMETRY_SESSION_RESULTS.json`.
* Límites: Hyprland 0.56 rechaza escalas que dejan medios píxeles lógicos. El
  redondeo de §301 queda cubierto por pruebas unitarias. La reserva no la crea
  el panel nativo: su identidad exige descripción y no se ejecuta en headless.
* Regresión del observador (falla antes, pasa después) y cinco pruebas del
  comprobador; 254 pruebas R4 y 42 de ventanas/puente/skins pasan. `Fixture`
  admite un selector opcional; por defecto sigue usando `desc:`.

### 303. R5, iteración 1: los «Ajustes del panel» originales de Plasma (2026-11-18)

* **Petición:** continuar lo que quedara de R4 y, si no quedaba, empezar R5. Los criterios del
  prompt de R4 se cumplieron en §209. El panel diario y la bandeja nativa en la vista se quedan
  fuera de ese prompt, así que se empieza R5 sobre el anfitrión aislado.
* **Hecho:** `src/bwm-plasma-host/panelconfigview.{h,cpp}` adapta `PanelConfigView`/`PanelRulerView`
  de plasma-workspace 6.7.5 (LGPL, autoría conservada). Carga sin cambios el `PanelConfiguration.qml`
  instalado con sus objetos `plasmoid`/`panel`/`configDialog`. Lo abre la acción original del panel
  «Enter Edit Mode» (`configure`), que activa el modo edición de la Corona. `PanelViewHost` cumple
  ahora el contrato de `PanelView` que usa ese QML: alineación, desplazamiento, modo de longitud,
  mín./máx., `minThickness`, `adaptiveOpacityEnabled` según el estilo de Plasma y `userConfiguring`.
  Tamaño y anclaje siguen `preferredSize`/`updateLayerWindow`. El modo predeterminado es el de
  Plasma, rellenar el ancho. `alignment`, `panelLengthMode` y `offset` se guardan en `plasmashellrc`.
  Antes se rechazaban.
* Con el diálogo abierto cada cambio se guarda al momento, como en Plasma. Fuera, los setters
  siguen siendo vista previa. Autoocultar, esquivar ventanas y opacidad adaptativa siguen sin
  controlador: se rechazan sin ocultar la opción. Mover a otro monitor y clonar fallan de forma
  visible. `preview-isolated.py --edit-mode` abre el diálogo en la vista desechable.
* **Comprobado:** QtTest nuevo con los combos reales del QML (alineación, anchura personalizada con
  regla, altura, flotante, opacidad, añadir espaciador, Escape) y lectura en un anfitrión nuevo.
  Prueba de anclaje por alineación. CTest local y de superficies, `check-isolated.py` completo
  (KDE y Andromeda) y 255 pruebas Python R4 pasan. En Hyprland (LG) el diálogo se abrió como
  capa encima del panel y se cerró sin capas residuales. El foco de teclado se devolvió a la
  ventana que lo tenía. Arreglado de paso en `check-isolated.py` (anterior a R5): fixture de
  bandeja ausente, pasadas repetidas en las mismas raíces y límite de 25 s para la suite.
* **Pendiente:** usarlo con el ratón (usuario), WidgetExplorer original, modo edición del
  escritorio, mover/clonar paneles, autoocultar, varios paneles, escala fraccionaria y la
  conversión de alineación/longitud de `bar.plasma`. Sin ASan esta vez. Informe en
  `docs/BREEZE_R5_RESULTS.md`.

## 4. 📂 Estructura del repositorio

```
hyprland-de/
├── assets/
│   ├── fonts/ cursors/ wallpapers/ screenshots/
│   └── skin-previews/                 # Capturas de lo que imita cada estilo (end-4, KDE Plasma 6.8) + README
├── config/                            # Enlazado desde ~/.config
│   ├── hypr/
│   │   ├── hyprland.lua               # Raíz: importa modules/*
│   │   ├── skins/                     # Una carpeta por skin: <id>/skin.json (windows, aspecto, colores, parts, requisitos),
│   │   │                              # _template/, README.md (crear una skin), requirements.json (núcleo + catálogo)
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
│   │       ├── bwm                    # Comando bwm (bienvenida, check, skins, skin, startup)
│   │       ├── bwm-requirements.py    # Comprobador de requisitos + comandos por distro
│   │       ├── bwm_skins.py           # Carga las skins (skins/<id>/skin.json) para todo lo demás
│   │       ├── bwm-user-config        # Configuración en texto del usuario (manda sobre la de BWM)
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
│   │   ├── shell.qml, settings.qml, plasmaSettings.qml, retroSettings.qml, bwmWelcome.qml (bienvenida)
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
│   ├── quickshell/bwmenu/              # Galería autónoma de skins y diagnóstico; consola de rescate en scripts/bwm-menu.py
│   ├── matugen/                       # config.toml + plantillas (GTK, Vesktop, Qt, Steam, kitty…)
│   ├── gtk-3.0/ gtk-4.0/ kitty/ rofi/ swaync/ btop/ firefox/ spicetify/ xdg-desktop-portal/
│   └── illogical-impulse/             # config.json activo + perfiles por estilo
├── src/breezebars/ src/omarchy-titlebars/ src/csd-minimize/  # Plugins C++ (breezebars de Breeze, barras de Omarchy para Retro; -fno-gnu-unique, make install)
├── docs/                            # SKINS.md (wiki de skins), REQUIREMENTS.md, OMARCHY_*.md, STREMIO_THEMING.md
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
* **KDE Plasma 6.7.5 instalado como bibliotecas** (§3.138): `/etc/portage/package.use/bwm-plasma`, `~/.config/kded5rc` (módulos de kded6 desactivados) y `~/.local/share/dbus-1/services/org.freedesktop.Notifications.service` (sin demonio de avisos alternativo). KWin está instalado y no se ejecuta.
* **Procesos de sesión**: `window-guard.py watch`, `hyprpolkitagent` (sólo fuera de Retro), swaync (sólo en default), recordatorios como temporizadores `systemd --user` (`omarchy-reminder-*`).

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
python3 ~/.config/hypr/scripts/bwm-theme-manager.py set retro   # cambia de skin sin reiniciar apps
qs -c ii log | tail -50                                    # log de la instancia real
qs -c ii ipc show                                          # objetivos IPC (un panel que no carga desaparece)
omarchy-theme-list; omarchy-theme-set tokyo-night; omarchy-theme-current   # temas de Retro
~/.config/hypr/scripts/bwm-plugin.sh list                  # plugins de la barra Retro
hyprctl hyprbars-csd                                       # qué ventanas llevan barra (Plasma)
~/.config/hypr/scripts/xwayland-primary.py status          # primary de XWayland
cd src/breezebars && make clean && make && make install      # plugin (cargará al reiniciar sesión)
git status; git log --oneline -5; git push origin main
```

**Puntos críticos:**
* Plugins C++: `-fno-gnu-unique` y sólo `make install`; nunca `cp` sobre un `.so` cargado ni `hyprctl plugin unload/load` (SIGBUS, safe mode).
* Quickshell una sola vez (`qs -c ii`); reinicios de mantenimiento con `bwm-theme-manager.py set <estilo> --restart-shell`. Los widgets cargados por `Loader` desde `bar/omarchy/*`, overlays y archivos nuevos de un módulo no se recargan en caliente: reinicia.
* Hyprland 0.55 en Lua: `hyprctl dispatch 'hl.dsp.…'`; para inyectar atajos `hyprctl eval 'return hl.dispatch(hl.dsp.send_shortcut({…}))'`.
* Archivos que otras apps vigilan por inodo (Vesktop) se escriben en el sitio; los que se vigilan por carpeta (qt6ct) o se reemplazan (resto) con `os.replace`.
* Polkit y `org.freedesktop.Notifications` admiten un solo dueño: en Retro los tiene Quickshell (Omarchy), fuera `hyprpolkitagent`/swaync o BWM.
* Retro estático: cambiar el fondo no cambia la paleta.
* Puede haber otra sesión de IA en el repo: commits sólo con tus archivos, salvo petición explícita de incluir todo; revisa cada diff.
* Mantenimiento de Gentoo: §2.7. Usar `sudo eselect news read`, revisar cada configuración y no dar por terminada la actualización sin evidencia.

### 152. Bloqueo de Breeze: el campo de contraseña perdía el foco en cada letra (2026-11-11)

* **Petición:** al iniciar sesión en Breeze, tras pulsar el campo y escribir una letra se deseleccionaba y había que volver a pulsarlo para cada letra.
* **Causa:** `plasmaLock/PlasmaLockSurface.qml` daba el foco con `password.forceActiveFocus()`, pero `password` es el `Rectangle` de `BreezeTextField`, no su `TextInput`. Cada letra llama a `wake()` (para mostrar el formulario y alargar el reposo), que pasaba el foco al rectángulo y dejaba el campo sin teclado.
* **Hecho:** el foco va siempre a `password.input` (al cargar, en `wake()` sólo si no lo tiene y en `shouldReFocus`). El formulario ya no se oculta en reposo (sólo opacidad 0): un elemento invisible no puede tener el foco. Quitado el `Keys.onPressed` del rectángulo (no recibía nada).
* **Comprobado:** `tests/test_plasma_lock_ui.py` (opcional, `BWM_RUN_QML_TESTS=1 BWM_LOCK_TEST_WORKSPACE=<visible>`): `qs -p` aparte con la superficie y un `LockContext` real (sin llamar a PAM) en una ventana pequeña del workspace visible unos segundos, mover el ratón y teclas reales de QtTest: escribe «abc1» entero con el arreglo y nada con el código anterior; después devuelve el foco a la ventana que lo tenía.
* **No probado:** un bloqueo real de la sesión ni escribir en reposo sin mover antes el ratón (en la ventana de prueba nadie tiene el foco al cargar).

### 153. F10 en la sesión real: el encaje no se aplicaba al soltar; zonas como KWin (2026-11-11)

* **Petición:** continuar las pruebas de F10. El usuario dejó el equipo unos minutos; se probó con ratón y teclado virtuales (uinput, `hl.dsp.cursor.move` para colocar el puntero) en Breeze, con dos kitty de prueba en el workspace 9 (una primera prueba se estropeó porque el usuario cambió de workspace a la vez y el arrastre movió su ventana de Claude). Resultados punto por punto en `docs/BREEZE_F10_CHECKLIST.md`.
* **Fallos encontrados y corregidos en Python (efecto inmediato):** soltar una ventana en un borde nunca la encajaba aunque el contorno era correcto. `kwin-tiles.py apply` exigía `int` en `hyprctl getoption plugin:breezebars:enabled`, que en Hyprland 0.56 es `{"bool": true}`; y el plugin pasa `m_description`, con el conector al final («… 0x01010101 (DP-2)»), mientras `hyprctl monitors` da `m_shortDescription`. Nuevo `bwm_windows.monitor_matches()` (corta, larga o nombre) en `kwin-tiles.py`, `quick-tile.py` y `kwin-window.py`. Después: mitades, cuartos y maximizado en los dos monitores con el marco exacto del contorno.
* **QML:** el editor de mosaico (Meta+T) no se cerraba con Esc (atajo `StandardKey.Cancel`); `Outline.qml` tenía un bucle de enlace en `visible` (usaba el tamaño de su propia ventana; ahora el de la pantalla). Comprobados tras un reinicio de mantenimiento del shell.
* **Plugin (compilado e instalado con `make install`, se carga al próximo inicio de sesión):** `SnapGeometry::edge` sigue `Window::checkQuickTilingMaximizationZones` de KWin 6.7.5: sólo los bordes laterales (20 px) encajan, con cuartos por la proporción de esquina sobre la altura del área útil; el superior (5 px) maximiza; el inferior no hace nada; un borde compartido con otro monitor encaja tras 250 ms quieto (temporizador del bucle de Hyprland). Antes: 10 px en los cuatro bordes, mitad inferior, cuartos desde arriba/abajo y nada en bordes interiores. Al redimensionar una ventana encajada se perdía el primer paso para la vecina (hueco de 2–3 px): se guardan los marcos al pulsar. Mayús+arrastre y la orden de encaje usan `m_shortDescription` (con la larga, las zonas de mosaico no casaban nunca con su monitor). Prueba de geometría actualizada con los casos de KWin; pruebas del plugin y de quick-tile correctas.
* **Comprobado en la sesión:** decoración KDE y colocación, Ctrl+flechas (al restaurar vuelve centrada, no a su posición previa como en KWin), imán entre ventanas, vecina que conserva su borde lejano, editor con la distribución de KWin y Cancelar sin escribir, regla de prueba en `kwinrulesrc` (posición, tamaño forzado, sin borde, opacidad, «Recordar», orden y «No afectar»; al forzar tamaño Hyprland recoloca desde el centro), y vuelta a Retro sin restos de Breeze. `kwinrulesrc` de prueba borrado (no existía), ventanas de prueba cerradas, workspaces 1/10 y foco devueltos. Suite completa OK; `Hyprland --verify-config` correcto.
* **No probado:** el plugin nuevo (bordes interiores, hueco del borde compartido, Mayús+arrastre), otro estilo de Plasma, escala fraccionaria, apps XWayland con rol/tipo, dividir/unir/aplicar en el editor y valores de las zonas en kwinrc. El cambio a Retro tardó 7,3 s (a Breeze 1,2 s), sin investigar.

### 154. Fase 11 de Breeze: Preferencias del sistema con los KCM reales (2026-11-11)

* **Petición:** fase 11 de `docs/BREEZE_PLAN.md`: «Preferencias del sistema» como systemsettings de Plasma 6.7.5, con los KCM reales donde funcionen, las páginas comunes de BWM para lo compartido y sin páginas inútiles.
* **Estructura (`modules/plasma/settings`):** `Main.qml`, `SideBarItem.qml`, `CategoriesPage.qml`, `SubCategoryPage.qml`, `CategoryItem.qml` y `HamburgerMenuButton.qml` son los de systemsettings `app/qml/` v6.7.5 (LGPL-2.0-only), con los modelos de C++ cambiados por `SettingsState.qml` (`// BWM:`) y el catálogo de traducciones instalado `systemsettings` (`SettingsI18n`, `KI18nContext`). Categorías, orden y nombres de `categories/settings-*.desktop`; búsqueda sin tildes; dos columnas en ventana ancha; menú ⋮ con «Resaltar las preferencias modificadas» (se pasa a `defaultsIndicatorsVisible` del KCM abierto). `ModuleView.qml` hace en QML lo de `app/ModuleView.cpp`: Ayuda/Predeterminados/Restablecer/Aplicar según `buttons`, `needsSave` y `representsDefaults`, y el aviso de cambios sin aplicar al cambiar de página. `plasmaSettings.qml` sigue siendo la entrada (Super+I, `open-settings.sh`).
* **KCM reales:** nuevo módulo QML `org.bwm.kcm` en C++ (`src/bwm-kcmhost`, `make install` → `~/.local/share/bwm/qml`): `KcmHost` carga el KCM con `KQuickConfigModuleLoader::loadModule` en el motor de la ventana (como systemsettings) y `KcmPage.qml` porta el `ApplicationItem` con `pageStack` de `KCModuleQml` (kcmutils 6.29.0, LGPL-2.0-only) para la página y sus subpáginas. `mainUi()` va antes de `load()`: `kcm_fonts` usa en `load()` el motor que sólo existe después y tumbaba el proceso en el orden inverso. Incrustados: tema global, colores, estilo de Plasma, decoraciones, iconos, estilo de aplicaciones, fuentes, reglas de ventana (F10) y sonido (`kcm_pulseaudio`). Los cambios que hacen en `kdeglobals`/`kwinrc`/`kwinrulesrc` los recoge el puente F2 (p. ej. `ColorScheme` → `plasma-theme.py sync` a kitty, GTK y demás). `open-settings.sh` pone `QML_IMPORT_PATH` y `QT_QUICK_CONTROLS_STYLE=org.kde.desktop`. Requisito recomendado `bwm-kcmhost` (tipo build) y tabla regenerada. Sólo la ventana de Preferencias (proceso `qs -p` aparte) lo carga; nunca la barra.
* **Páginas:** comunes de BWM, sin duplicar lógica: cursores, pantalla y monitor, escritorios virtuales, atajos, inicio automático, apps predeterminadas, energía e inactividad (`IdleConfig`), General de BWM, servicios, arranque e inicio de sesión (`StyleConfig`) y Acerca de. Propias de Breeze (`pages/`, escriben con `kwriteconfig6 --notify` lo que lee el puente; leen con la nueva orden `kde-config-bridge.py kwin-settings`): **Comportamiento general** (clic simple/doble y velocidad de animaciones, como `kcm_workspace`, que no está instalado), **Comportamiento de las ventanas** (foco, colocación, doble clic y rueda en la barra, encaje en bordes, zonas de imán; `kcm_kwinoptions` es QWidget y no se puede incrustar; sólo se ofrecen los valores que BWM aplica) y **Fondo de escritorio** (fondo actual y el selector de Breeze). Red (`kcm_networkmanagement`, QWidget) y Bluetooth (bluedevil, no instalado) abren su app de `Config.options.apps`. Los ids anteriores de `SETTINGS_PAGE` siguen valiendo (alias: interface → comportamiento general, themes → tema global, plugins → panel).
* **Quitado y por qué:** Interfaz (opciones de end-4: guía de atajos, dock, barras laterales, superposiciones y selector de regiones de end-4; Breeze no las usa), Plugins y Temas (formato de Omarchy; en Breeze los temas son de Plasma, con sus KCM y «Obtener nuevos…»), la página de fondo común (widgets de fondo de end-4) y, al no existir en BWM, Actividades, efectos y scripts de KWin, Plasma Vault, KDE Connect, pantalla táctil, teclado virtual y KScreen.
* **Arreglos de paso:** `StyledSpinBox` con márgenes propios (con el estilo de Plasma el «−» tapaba el número; con Basic no cambia nada); `ConfigSlider` con `stepSize` y `moved()`, que la página del panel (F3) usaba y la dejaban sin cargar.
* **Comprobado:** las 26 páginas cargan en `qs -p` en el workspace 9 sin errores de QML y `SETTINGS_PAGE` acepta ids, alias y nombres (`tests/test_plasma_settings.py`, opcional con `BWM_RUN_QML_TESTS=1`; los avisos de Kirigami al destruir la ventana tras salir y los internos del QML de un KCM no cuentan). Capturas recortadas de Colores, Decoraciones de ventana, Comportamiento de las ventanas y seis páginas comunes, revisadas y borradas. Cambio de esquema desde la página del KCM de colores en una configuración aislada (`XDG_CONFIG_HOME` temporal con el `kdeglobals` de Breeze): la ventana pasó en vivo de Breeze Oscuro a Breeze Claro sin reabrirla y el `kdeglobals` real no se tocó. Ajustes de default con estilo Basic siguen cargando. Suite completa, `qmllint`, `Hyprland --verify-config` y `configerrors` correctos.
* **Probado después con Breeze activo (a petición):** `open-settings.sh colors` (lo que hace Super+I) abre la ventana con la paleta de Breeze Oscuro y, en ventana estrecha, la vista de una columna con «Back», como Plasma. Aplicar Breeze Claro desde el KCM de colores: `kdeglobals`, kitty (`#ffffff`), GTK (`prefer-light`), la paleta del shell y el panel cambiaron en vivo, y la ventana de Preferencias abierta (otro proceso) se repintó sola. Volver a Breeze Oscuro igual. Captura recortada de la ventana y del panel, borradas.
* **Fallo encontrado y corregido:** `bwm-theme-manager.py set plasma` estando ya en Breeze (reinicio de mantenimiento `--restart-shell` o volver a elegirla) ejecutaba `plasma-theme.py restore` y devolvía el `kdeglobals` guardado al salir de Breeze, deshaciendo lo aplicado desde las Preferencias (el esquema volvió a Breeze Oscuro). Ahora sólo restaura al entrar desde otra skin; comprobado que tras el reinicio sigue Breeze Claro. El inicio de sesión no restaura.
* **No probado:** «Obtener nuevos…», aplicar en los KCM de iconos, decoraciones, fuentes, estilo y tema global, la página de sonido con cambios, y la pulsación física de Super+I. Kickoff conserva `systemsettings.desktop` como favorito por defecto, que abre las Preferencias de KDE y no éstas. Sin insignias de cambios en la barra lateral (sólo en el KCM abierto).

### 160. Panel de Breeze: tareas con la medida de Plasma y comparación con una referencia (2026-11-12)

* **Petición:** igualar «al milímetro» el panel con un panel de Plasma de referencia (captura del usuario: un fotograma de vídeo encima y el panel de BWM debajo, a la misma escala).
* **Encontrado:** la captura era de antes del port de Codex (§3.159 y commits `7f42636`/`7851ea6`, reloj/Kickoff/bandeja/«Mostrar escritorio»). Con el panel actual quedaban las tareas: 42 px (paso 44) porque `PanelContent` usaba el ancho mínimo de `LayoutMetrics` en vez de `preferredMaxWidth()`.
* **Hecho:** ancho de tarea = alto + márgenes horizontales del marco × `iconSpacing` (vertical: ancho + verticales), icono como el `iconBox` «standalone» de Task.qml 6.7.5; nuevo `bar.plasma.taskManager.iconSpacing` (0/1/3, por defecto 1). Con Breeze por defecto y panel de 44: 52 px e icono de 32. Márgenes de `widgets/tasks` medidos con KSvg: `normal` 4/4/4/4, `north-*` 4/3/4/3, sin `south-*`.
* **La referencia:** sus medidas cuadran con un panel de 68 px, tareas con espaciado Grande y bandeja escalada con espaciado Grande (los ajustes del modo táctil de Plasma). Aplicados un momento y comparados a escala 0,5: tareas, bandeja, flecha y ancho del reloj coinciden; `config.json` devuelto byte a byte. Sólo «Mostrar escritorio» (fijo a 32 en 6.7.5, ~39 allí) y un reloj algo menor no salen de Plasma 6.7.5. Detalle en `docs/BREEZE_PANEL_FIXES.md`.
* **Comprobado:** 379 pruebas (70 omitidas), 19 de interfaz del panel/bandeja y la de entrada de tareas con `BWM_RUN_QML_TESTS=1`; recarga en caliente sin errores nuevos (los avisos de `Task.qml:22` ya estaban desde el arranque del shell). Capturas recortadas y borradas.
* **No probado:** paneles verticales a la vista con el ancho nuevo (la fórmula vertical sigue a `preferredMaxHeight()`).
* **Después (2026-11-12):** el usuario pidió el panel por defecto de Plasma: vuelto a 44 px, espaciado de tareas Normal y bandeja sin escalar (se retiraron los valores de la referencia de los perfiles). Plasma no cambia el grosor según la resolución: lo escala con el factor de escala de la pantalla, y en Hyprland el panel ya va en unidades lógicas. El icono de Bluetooth no salía: BWM sólo lo mostraba con un dispositivo conectado; bluedevil 6.7.5 (`applet/qml/main.qml`) lo activa mientras `bluetoothOperational` (adaptador presente y encendido), con los iconos `network-bluetooth{,-activated,-inactive}-symbolic`. Corregido en `tray/SystemTray.qml`; comprobado en el panel real y 27 pruebas de bandeja y panel con `BWM_RUN_QML_TESTS=1`.

### 161b. Bandeja, Kickoff y resaltado del botón como en Plasma (2026-11-12)

* **Petición:** los iconos de la bandeja salían estirados, Kickoff se mezclaba con el panel y el botón de Kickoff no se resaltaba en azul al abrirlo.
* **Iconos:** las apps de la bandeja (SNI) medían 12×18 o 14×20. Plasma pasa un `QIcon` a `Kirigami.Icon`, que lo mantiene cuadrado; Quickshell da una URL de imagen, que `Kirigami.Icon` estiraba a la caja de la celda (22 × alto del panel). `tray/StatusNotifierItem.qml` lo dibuja cuadrado y centrado: ahora 18–20 px por lado.
* **Kickoff sobre el panel:** las pestañas del pie de Kickoff se estiran a propósito hacia el margen inferior del diálogo (`anchors.bottomMargin: -root.bottomPadding`). En Plasma el diálogo es su propia ventana y su borde las recorta; aquí la capa de Kickoff ocupa toda la pantalla y cubrían, al 75 %, las 3 primeras filas del panel, atenuando también las líneas de las tareas. `KickoffWindow.qml` recorta en el borde del diálogo (`clip`), y añade la línea `widgets/line` entre el menú y el panel, con el píxel extra, como `CompactApplet.qml` de plasma-desktop 6.7.5.
* **Resaltado:** `ExpandedHighlight` en `PanelContent.qml` porta el `expandedItem` de `CompactApplet.qml`: `widgets/tabbar` `<borde>-active-tab` estirado sobre los márgenes del contenedor hasta el borde del panel, con su fundido. Se usa en Kickoff y en el reloj (calendario). El prefijo va como lista porque `hasElementPrefix()` no es notificable.
* **Comprobado:** con Kickoff abierto, la línea azul del botón sale a `#3daee9` pleno y las tareas conservan su línea; 32 pruebas de bandeja, panel y Kickoff con `BWM_RUN_QML_TESTS=1`. Capturas recortadas y borradas; cinco reinicios de mantenimiento del shell para cargar el panel (Loader) y las pruebas temporales, con el foco devuelto.
* **Después:** resaltado de la bandeja portado de `CurrentItemHighLight.qml` (systemtray 6.7.5) en `tray/SystemTray.qml`: tras el icono del applet abierto, o toda la bandeja hasta el borde del panel con la lista de ocultos; el calendario es del reloj. No se veía porque las ventanas emergentes de la bandeja y del calendario se anclaban al borde del icono, 4 px dentro del panel, y lo tapaban: `TrayPopup.qml` se apoya ahora en el borde del panel (como `PlasmaQuick::Dialog`), sin su borde en ese lado y con la línea `widgets/line`; en panel flotante deja `largeSpacing`. La prueba de Kickoff dependía de que la configuración real no hubiera importado ya los favoritos a KActivities (`favoritesPortedToKAstats`); ahora lo pone a falso con escrituras bloqueadas antes de crear Kickoff. 32 pruebas OK.

### 170. Obsidian: tema en la versión Flatpak y límite de inotify (2026-11-12)

* **Tema:** `bwm_omarchy_apps.apply_obsidian()` sólo leía `~/.config/obsidian/obsidian.json`; el Obsidian Flatpak la guarda en `~/.var/app/md.obsidian.Obsidian/config/obsidian`. Ahora lee las dos y, si una bóveda no tiene tema elegido (`cssTheme` vacío), activa «Omarchy»; un tema elegido por el usuario se respeta. Aplicado a las dos bóvedas del usuario.
* **«EMFILE: too many open files, watch» al abrir una bóveda:** no eran descriptores sino instancias de inotify: 127 de 128 por usuario, 86 de ellas de Quickshell. Cada `FileView` con `watchChanges` es un `QFileSystemWatcher` y una instancia. El panel de agentes de Omarchy creaba una por registro de uso (23 proveedores). Ahora `Agent.qml` no vigila y `Main.qml` vigila un único marcador `agents/usage/.updated`, que `omarchy-agent-usage-update` reescribe al final de cada ejecución (también lanzada desde fuera del panel); se siguen recargando todos los registros tras cada actualización del propio panel. Fuera también los dos vigilantes de `agent-local` (BWM no tiene modelos locales). Parches marcados «BWM».
* **Comprobado:** tras reinicio de mantenimiento, Quickshell 86 → 42 instancias y el usuario 127 → 85; destinos IPC `shell`/`omarchy.agents` presentes, sin errores nuevos en el log; el script escribe el marcador. No se cambió `fs.inotify.max_user_instances` (sigue 128), así que vale para cualquier instalación.
* **No probado:** abrir la bóveda en Obsidian tras el arreglo y que el panel de agentes muestre datos nuevos en vivo tras una actualización lanzada desde terminal. Quedan 11 instancias de Quickshell sin ningún archivo vigilado (FileView sobre archivos inexistentes) sin identificar.

### 304. R5, iteración 2: posición, alineación y flotante medidos en Hyprland (2026-11-19)

* **Petición:** el usuario probó el diálogo con el ratón: posición, alineación, visibilidad y
  flotante no funcionaban; los clics y el resto sí.
* **Causas:** las flechas de «Set Position…» (`PlasmaCore.Dialog` del QML original, por
  coordenadas globales) no tenían rol layer; cambiar el borde recreaba la vista desde el runtime
  y cerraba el diálogo. La alineación no se ve con «Rellenar anchura» (igual que en Plasma). El
  flotante funciona; en la vista de ensayo el panel ya está 64 px sobre el borde y el cambio es
  pequeño. Visibilidad: «Siempre visible» necesita `--native-policy`; autoocultar/esquivar sin
  controlador.
* **Hecho:** `PanelConfigView` coloca las flechas como capas `overlay` en su pantalla
  (`bwm-r5-edit-indicator`). Con el diálogo abierto, `PanelViewHost::adoptLocation` sigue a
  `PanelView` 6.7.5 (factor de forma, relectura del ámbito, `BwmSurface::setPanelEdge` sobre la
  misma superficie); fuera del diálogo sigue el contrato de R4. `screenToFollow` hacia otra
  salida: el runtime cambia la asignación por descripción y reabre los ajustes (sólo la vista
  desechable con `--output`; los perfiles no reescriben bindings).
* **Comprobado:** nuevo `check-edit-mode-session.py` + `test-editmode-session` (fuera de CTest):
  panel desechable en el MSI, combos del QML original y geometría leída con `hyprctl layers`; 11/11
  pasos (alineaciones, flotante, flechas en ambos monitores, cuatro bordes, paso al LG). CTest
  local/superficies, `check-isolated.py` completo y 255 pruebas Python OK. No se tocó la barra
  diaria; la vista de prueba del usuario se detuvo para medir.
* **Pendiente:** clic físico del usuario, autoocultar/esquivar, persistencia del cambio de monitor
  en perfiles y el resto de R5 (`docs/BREEZE_R5_RESULTS.md`).

### 305. R5, iteración 3: «Añadir widgets…» con el WidgetExplorer original (2026-11-19)

* **Petición:** seguir con R5 tras confirmar el usuario que los clics del diálogo funcionan.
* **Hecho:** `widgetexplorerview.{h,cpp}` y `qml/WidgetExplorerHost.qml` (adapta de `views/Desktop.qml`
  6.7.5 sólo el contrato que espera el explorador: `root.widgetExplorer`, `pendingUninstallTimer`, el
  Dialog lateral y su Loader). Cargan sin cambios `explorer/WidgetExplorer.qml` y el tipo C++
  `WidgetExplorer`. `PanelViewHost` atiende `showAddWidgetsInterface` (acción interna «add widgets»)
  como `ShellCorona::toggleWidgetExplorer`: modo edición, Ajustes ocultos y reabiertos por el
  `onClosed` original. Barra lateral como capa `top` `bwm-r5-widget-explorer` de arriba abajo, zona
  exclusiva 0 (margen sólo si el panel editado no reserva), teclado a demanda, focus grab con la barra
  y el panel. Sin escritorio: al cerrarse sin reabrir los Ajustes se sale del modo edición.
* **Comprobado:** prueba Qt nueva en `isolated-local-configuration` (normal ×3 y ASan): QML instalado,
  modelo/búsqueda, `addApplet` en el panel, cierre que reabre los Ajustes, acción directa y cierre por
  desactivación. En Hyprland (LG) `check-edit-mode-session.py` 16/16: capa 498×2004 dentro del área
  libre según `monitors.reserved`, widget añadido, Ajustes reabiertos, sin restos y foco devuelto.
  No se tocó la vista `--native-policy` que el usuario tenía abierta en el MSI.
* **Pendiente:** clic físico, arrastrar un widget al panel, desinstalar, alternativas de widgets. Con
  ASan falla después el ensayo de salida de §268 (`transaction.lock` con `LOCK_NB` mientras el anfitrión
  lento aún lo tiene), ajeno a este cambio.
* **Después (2026-11-19):** con el ratón la barra se cerraba al poco de abrirse. Hyprland da el foco a
  una capa *on demand* cuando el puntero solo pasa por encima, y el panel en edición lo es.
  `Dialog::focusOutEvent` lo tomaba como un clic en la vista y ocultaba la barra. Ahora esa pérdida de
  foco hacia el panel editado no la oculta; un clic fuera sigue cerrándola mediante la captura de foco.
  Registro `bwm.r5.explorer`, prueba offscreen que falla sin la corrección; CTest normal 8/8.
  `ViewCorona::isScreenUiReady` (de `ShellCorona`), que pide la Vista de carpeta añadida al panel desde el
  explorador: lista si los paneles visibles de esa pantalla tienen `uiReady`.
  El usuario confirma con el ratón en el MSI que la barra se queda abierta y añade widgets (sin
  desglose por caso); `isScreenUiReady` no se ha vuelto a ver en sesión.

### 306. R5, iteración 4: caja de herramientas del panel y menú del botón derecho (2026-11-19)

* **Encontrado:** cada entrada en modo edición registraba «Toolbox not loading» y un `TypeError`
  en `org/kde/panel/main.qml:135`. libplasma lee el `defaults` del paquete de shell de la Corona para
  la caja de herramientas del panel y sus acciones de ratón; el paquete mínimo del anfitrión no lo
  tenía. Sin él, `ConfigOverlay.qml` (asas de mover/quitar widgets) se creaba con `toolBox` nulo y
  el clic derecho sobre el panel no abría ningún menú.
* **Hecho:** `src/bwm-plasma-host/shell/contents/defaults` con el `[Panel]` de plasma-desktop 6.7.5
  (`ToolBox=org.kde.paneltoolbox`, `RightButton;NoModifier=org.kde.contextmenu`). Sin código nuevo.
* **Comprobado:** prueba offscreen nueva (caja de herramientas, `ConfigOverlay`, Escape, menú del
  botón derecho con «Enter Edit Mode» y «Añadir widgets…», que abre el explorador); falla sin el
  archivo. CTest normal 8/8 y 255 pruebas Python R4.
* **No probado:** el menú del botón derecho y las asas del `ConfigOverlay` con el ratón en Hyprland.

* **Después (2026-11-19):** el fallo con ASan del ensayo de salida de §268 era del envoltorio.
  Su `command()` aún retenía `transaction.lock` en el último sondeo tras el acuse inicial, y
  `session-exit` lo pedía con `LOCK_NB`. `panel-session.py` espera hasta 0,5 s por el bloqueo
  antes de dar `BlockingIOError`. Regresión nueva (falla sin la espera); ASan
  `isolated-local-configuration` pasa 3/3; Python R4 256.

### 307. BWMenu en el lanzador de aplicaciones de las tres skins (2026-11-19)

* **Hecho:** entrada común en `config/hypr/applications/org.bwm.menu.desktop`. Abre
  `bwmenu --open` desde su ruta de instalación, también si el lanzador carece de
  `~/.local/bin` en el PATH. `install-bwmenu-launcher.sh` la registra desde el instalador
  y al iniciar sesión, antes de Quickshell, y respeta una entrada existente.
* **Comprobado:** `desktop-file-validate`, detección en `DesktopEntries` de Quickshell y
  `KService` de KDE, y entrega de `--open` a un ejecutable de prueba desde Quickshell, KDE y
  GIO. Se probaron XDG explícito y por defecto, repetición y una entrada personalizada.
  Pasaron las 27 pruebas de BWMenu. Queda pendiente comprobar los lanzadores en sesión:
  el entorno de trabajo tiene el directorio de aplicaciones del usuario en sólo lectura.
* **Después (2026-11-19):** el usuario lo da por bueno con el ratón salvo emergentes en el centro de la
  pantalla. El recuadro de cada widget en modo edición (`ConfigOverlay.qml`) y el tooltip del botón ⚙
  pertenecen al containment del panel y `PackageWindows` sólo adaptaba los de los widgets: salían
  como ventanas normales y Breeze los centraba. Ahora reciben capa si su ancla visual está en el
  panel. Ensayo de sesión nuevo `panelOwnPopupsInHyprland` (falla sin la corrección); 20/20 en el LG.

### 308. Gestor de archivos por skin (Dolphin / Nautilus en Retro), plugins de Omarchy y sincronización de favoritos (2026-11-19)

* **Hecho:**
  * Cada skin declara `"fileManager"` en `config/hypr/skins/<id>/skin.json` (`org.kde.dolphin.desktop`
    en `default` y `plasma`; `org.gnome.Nautilus.desktop` en `retro`), expuesto por `bwm_skins.file_manager()`.
  * `default-apps.py` incorpora modo `"per-skin"` (por defecto: «Según la skin (Dolphin / Nautilus en Retro)»)
    o `"fixed"` (un único gestor elegido para todas las skins), compatible con `DefaultAppsConfig.qml`,
    `skins/retro/scripts/settings.py` y `skins/plasma/scripts/native-settings.py`. `apply-skin` actualiza
    `inode/directory` al cambiar de skin sólo en modo `"per-skin"` y respeta la elección fija.
  * Lanzador común `config/hypr/scripts/bwm-file-manager` (enlazado en `~/.local/bin` y desde los shims
    `omarchy-launch-files` / `omarchy-launch-nautilus`); `Alt+E` y `Super+E` en `keybinds.json` y
    `keybinds-manager.py` apuntan a él (recargado con `keybinds-manager.py reload`).
  * Extensiones `nautilus-python` de Omarchy (`localsend.py` y `transcode.py`, MIT, `quattro` `05344eb6`
    y `ec4a3d02`) en `config/hypr/skins/retro/nautilus-python/extensions/` con instalador idempotente
    `skins/retro/scripts/setup-nautilus-plugins.sh` (enlaza en `~/.local/share/nautilus-python/extensions/`
    sin pisar extensiones propias del usuario). Requisitos `dolphin`, `ffmpegthumbs`, `nautilus-python`,
    `sushi` y `ffmpegthumbnailer` añadidos a `requirements.json` y `docs/REQUIREMENTS.md`.
  * Sincronizador común `config/hypr/scripts/bwm-bookmarks-sync.py` (arrancado en `autostart.sh` vía
    `bwm_session.spawn`): unión aditiva sin borrados en `startup`, conciliación bidireccional de 3 vías
    con estado previo (`~/.local/state/bwm/bookmarks-sync.json`) para distinguir eliminaciones de altas
    nuevas, vigilancia de carpetas padre con una sola instancia `inotify` + debouncing (y fallback a
    polling), preservación de entradas especiales y metadatos KDE (`isSystemItem`, `remote:/`, `trash:/`,
    `timeline:/`, `UDI`, `isHidden`, `onlyInApp`, `<info>`, iconos e `ID`), y conservación + reintento
    ante XML incompleto o cambios simultáneos en conflicto.
  * Miniaturas de vídeo en Dolphin: instalado `kde-apps/ffmpegthumbs` y limpiada la lista `Plugins=` de
    `~/.config/dolphinrc` (quitando `ffmpegthumbnailer` y `ffmpeg` que bloqueaban `KIO::PreviewJob`) más
    caché `~/.cache/thumbnails/fail/*`.
* **Comprobado:** 65/65 pruebas unitarias (`test_bookmarks_sync.py`, `test_file_manager.py`,
  `test_skins.py`, `test_retro_settings.py`, `test_r3_native_settings.py`, `test_kde_config_bridge.py`,
  incluido inotify real con sustituciones atómicas y debounce), `py_compile`, `bash -n`,
  `hyprctl configerrors` vacío, `bwm-requirements.py check`, `default-apps.py apply-skin` (Breeze pasó
  a `org.kde.dolphin.desktop`), `bwm-file-manager --print` por skin, unión real inicial (5 favoritos de
  Nautilus incorporados a `user-places.xbel` preservando los 5 `isSystemItem` de KDE), vigilante
  activo como hijo de Hyprland con 1 descriptor inotify y generación de miniaturas de vídeo en Dolphin
  verificada con la configuración real del usuario (6/6 en muestra `.mkv`/`.mp4`/`.webm`/`.mov`).
* **Pendiente entonces (resuelto en parte en §3.318):** instalar `dev-python/nautilus-python` (y opcionalmente
  LocalSend) para que Nautilus cargue las extensiones Python ya enlazadas, y prueba visual interactiva
  abriendo `Alt+E` en Breeze/default (Dolphin) y Retro (Nautilus).

### 309. BWMenu: registro en la instalación actual y apertura comprobada (2026-11-19)

* **Petición:** continuar §307 y asegurar que instalar BWM registre BWMenu como aplicación
  para el lanzador de cualquier skin.
* **Comprobado:** `install.sh` llama al registro común tras enlazar `~/.local/bin/bwmenu`;
  `autostart.sh` cubre instalaciones existentes antes de iniciar Quickshell. Ejecutado
  `install-bwmenu-launcher.sh` en esta sesión: creada
  `~/.local/share/applications/org.bwm.menu.desktop`, validada con `desktop-file-validate`.
  Quickshell enumera BWMenu en `DesktopEntries.applications` y KDE lo encuentra visible
  mediante `KService::serviceByDesktopName`, tras actualizar su caché con `kbuildsycoca6`.
  `gio launch` de esa entrada abre una ventana mapeada `org.bwm.menu`, título BWMenu.
  Pasan las 27 pruebas existentes de BWMenu y la sintaxis Bash de los scripts implicados.
* **Alcance:** sin cambio de skin ni reinicio del shell; no se ha recorrido visualmente
  la búsqueda en los tres lanzadores. Queda resuelta la instalación local pendiente de §307.
  El usuario lo vuelve a probar con el ratón: «ya va bien parece».

### 310. R5, iteración 5: autoocultar y esquivar ventanas; proveedor de escritorios tras recargar (2026-11-19)

* **Hecho:** `PanelViewHost` admite «Ocultar automáticamente» (1) y «Esquivar ventanas» (2) con
  `--native-policy`, donde el panel toca el borde. La lógica de cuándo ocultarse se porta de
  `PanelView` 6.7.5: `restoreAutoHide`, `showTemporarily` (3 s), temporizador de 500 ms al salir,
  modo edición, estado de atención y ventanas transitorias visibles. El ocultado sustituye al protocolo
  `kde_auto_hide_screen_edge_v1` de KWin. El contenido se desliza fuera de la pantalla en 200 ms y la
  máscara de entrada deja una franja de 2 px en el borde. Al entrar el puntero, el panel vuelve.
  Esquivar sigue la propiedad `touchingWindow` del `Panel.qml` original. Su `TasksModel` recibe ahora
  el puente de tareas BWM (`attachEnabled` también en la raíz del marco). No hay reserva en ninguno
  de los dos modos, como en Plasma. `plasmashellrc` admite `panelVisibility` 0–3.
* **Proveedor de escritorios:** `native-desktops.py startup` lo activaba con `hl.config` en caliente.
  Cualquier `hyprctl reload` (cambio de skin, atajos) devolvía la opción a `false` y el proveedor quedaba
  retirado hasta otro inicio de sesión: en esta sesión estaba `disabled-after-claim`. Nuevo
  `modules/native_desktops.lua` (común): mantiene `enabled = true` si el módulo está cargado
  (`hl.get_config` no nulo) y el opt-in sigue activo. Nunca carga el módulo.
* **Comprobado:** QtTest `nativePanelAutoHideAndDodge` (sin reserva, desplazamiento y franja, entrada y
  salida, modo edición, ventana transitoria, atención, `touchingWindow`, vuelta a normal, vista sin
  política rechaza los modos); `surface-geometry`; CTest normal 8/8; matriz `check-isolated.py` con KDE y
  Andromeda; Python R4 257 (Lua del proveedor: cargado/no cargado/opt-in apagado/ausente). En Hyprland
  (LG, borde superior) `check-edit-mode-session.py` 23/23. Se movió el puntero al borde: el panel
  apareció; al alejarlo se ocultó. No se reservó espacio, y el puntero y el foco se devolvieron.
  Ensayo repetido 3/3. Tras `hyprctl reload` la opción del proveedor sigue en `true` y no hay errores
  de configuración.
* **Pendiente:** esquivar con ventanas reales necesita el proveedor activo (`Panel.qml` filtra por
  escritorio actual): volver a iniciar sesión. Falta también la prueba con el ratón del usuario.
* **Después:** el usuario confirma con el ratón que todo funciona salvo esquivar ventanas. Era lo
  esperado sin el proveedor; queda probarlo tras volver a iniciar sesión.

### 311. Selectores de fondo: sólo `~/Pictures/Wallpapers` en todas las skins (2026-11-19)

* **Petición:** que el selector de fondos de todas las skins tome en cuenta únicamente `~/Pictures/Wallpapers/`.
* **Hecho:** default: `services/Wallpapers.qml` fija `rootPath` y confina la navegación (normaliza `..`, redirige a la raíz toda
  ruta de fuera —pegada, barra de direcciones—, `navigateUp` no sale de ella); el panel lateral de `WallpaperSelectorContent.qml` queda con
  el único acceso «Wallpapers» (sin Home/Documentos/Descargas/Imágenes/Vídeos/homework). Se permiten subcarpetas de dentro.
  Se corrigió de paso la validación de `validateDirProc` (asignaba el directorio antes de comprobarlo y una ruta inexistente se ignoraba).
  Respaldo `switchwall.sh` (kdialog): arranca en Wallpapers y descarta lo elegido fuera. Breeze y respaldo rofi: `wallpaper-picker.sh`
  sólo busca en `~/Pictures/Wallpapers` (antes también `~/Pictures`, `~/Downloads`, `/usr/share/backgrounds`). Retro:
  `skins/retro/scripts/wallpaper-picker.py` ya no mezcla los fondos del tema de Omarchy ni `~/.config/omarchy/backgrounds/<tema>`.
* **No cambia:** `set-wallpaper.sh`/`switchwall.sh --image` y la IPC `wallpapers apply` siguen aceptando cualquier ruta (los usan
  scripts, el fondo aleatorio —que ya descarga a Wallpapers— y los temas de Omarchy); sólo los selectores están restringidos.
* **Comprobado:** `test_retro_wallpapers.py` (10, con las colecciones reescritas), `bash -n` de ambos scripts, `--print-dirs` de Retro
  = `~/Pictures/Wallpapers`, recarga de Quickshell sin errores en el log. **No probado:** abrir el selector de end-4 y navegar fuera de
  la raíz a mano, ni el kdialog de respaldo.


### 312. R5: regresión de esquivar desde el modelo original y proveedor aún retirado (2026-11-19)

* **Estado al retomar:** los cambios del traspaso ya estaban commiteados en `f6243bb`;
  la carga `require("modules.native_desktops")` ya estaba en `4c22038`. No se duplican.
  `native-desktops.py status` confirma en la misma instancia `enabled=true`,
  `providerAvailable=false` y arbitraje `retired`. Para la prueba real falta volver a entrar
  en la sesión; no se carga/descarga el módulo en caliente ni se arranca un preview condenado
  a fallar su preflight. No se ha hecho push desde esta continuación.
* **Regresión añadida:** `originalPanelDetectsWindowOverlapFromTaskSnapshots`, en
  `test-paneltasks.cpp`, usa `PanelViewHost` y el `Panel.qml` instalado, con un widget sin
  modelo de tareas. El puente tiene que descubrir el modelo del propio marco. IPC ficticio
  mueve una ventana sobre el panel, la minimiza/restaura y la aleja: se observan región,
  rol `Geometry`, filas, `touchingWindow` y ocultado/reaparición, sin forzar touchingWindow.
* **Comprobado:** compilación del objetivo; CTest `isolated-local-configuration` 1/1
  (42,50 s), QtTest de tareas del panel 5/5. El filtro de actividad permanece activo sin
  kactivitymanagerd y no descarta esa ventana. AGENTS.md y CLAUDE.md siguen idénticos.
* **Límites:** en offscreen sólo se desactiva el filtro de escritorio actual por ausencia
  del proveedor Wayland; no se valida ese filtro ni esquivar en la sesión real. Sin cambio
  del controlador o nueva aceptación visual. La retirada del proveedor es un bloqueo
  confirmado, no una demostración de que sea la única causa. Resto de R5 pendiente hasta
  resolver la prueba real, como pide el orden del traspaso. Informe: BREEZE_R5_RESULTS.md.


### 313. R5: esquivar ventanas aceptado tras volver a iniciar sesión (2026-11-19)

* **Comprobado:** instancia nueva de Hyprland; proveedor `enabled=true`, `providerAvailable=true`,
  arbitraje `active`. Preview del reloj en MSI, con `--native-policy --edit-mode --task-actions
  --native-desktops`, lanzado como hijo de Hyprland. Control enlazado/reanudado, modelo con
  ventanas y filtro por escritorio activo. No se carga/descarga ningún plugin en caliente.
* **Aceptación del usuario:** elige «Esquivar ventanas», sale del modo edición y prueba
  solapamiento/retirada de ventana: «Sí, funciona en ambos sentidos». Sólo aceptación funcional
  en MSI, sin medición de tiempos ni todos los bordes/escalas. Preview detenido con acuse;
  `panel-session.py status` queda inactivo. No repetir ese ensayo sin cambios relevantes.

### 314. R5, iteración 6: mover/clonar paneles y transacción completa de perfiles (2026-11-19)

* **Hecho:** `PanelRuntime` atiende el `cloneRequested` del diálogo original y admite movimientos
  de salida también en perfiles. `panelclone.cpp` adapta `ShellCorona::clonePanelTo` 6.7.5
  (LGPL, avisos originales): opciones nativas, widgets de la misma clase independientes,
  orden con IDs nuevos, hijos de bandeja y preferencias completas de la vista. Las opciones de
  los hijos con esquema ya inicializado exigen `KConfigLoader::load()` además de configChanged.
* **Perfiles:** `beginEditing` crea copia privada; `--serve-profile/--serve-selected-profile`
  guardan/sincronizan/cierran propietarios nativos antes de `commitEditing`. Layout completo,
  preferencias, bindings y procedencia se validan y publican en generación nueva, con head
  atómico y checkpoint posterior. Caída/edición abandonada conserva la generación previa.
  Checkpoint/restore/export rechazan una edición abierta. No es activación del panel diario.
* **Sesión:** clonación desde el manejador QML original, LG, dos capas 640×48 en 4160,2048 y
  4160,64, sin ventanas normales ni cambios de reservas; retirada y foco/puntero restituidos,
  2/2 pasos (`check-edit-mode-session.py --case originalClonePanelInHyprland`). Sin clic físico.
* **Pruebas:** compilaciones normal/ASan; CTest normal sin `native-` 8/8, configuración local
  con ASan (`detect_leaks=0`) 1/1; Python R4 257/257. Nuevos casos de edición/transacción, lectura en otro proceso
  con pantallas reordenadas y copia de hijos de bandeja con opciones propias; todos pasan.
* **Límites:** varios paneles sin reserva admitidos en una salida; con política nativa se
  conserva uno por salida y se rechaza un destino ocupado antes de mutar. Aún sin anfitrión
  de escritorio, escala fraccionaria del editor, migración de alineación/longitud, comparación
  con Plasma y arrastre/desinstalar/alternativas. Informe
  completo en `docs/BREEZE_R5_RESULTS.md`. `status` incluye capacidades vivas por panel.
* **Aceptación del usuario:** con el ratón en MSI, «Sí, clona y mueve bien» en el preview sin
  política de reservas. No acredita el perfil persistente, todos los bordes/destinos o bandeja.
  Ensayo detenido con acuse y registro inactivo; proveedor sigue activo y configerrors vacío.


### 315. R5, iteración 7: migrar alineación/longitud por salida lógica (2026-11-19)

* **Git antes de continuar:** `91afe29` y `74d3850` subidos a GitLab y GitHub por petición
  explícita; `ls-remote` confirmó `74d3850` en ambos. Cambios ajenos pendientes excluidos.
* **Hecho:** `migration.proposal(..., output_sizes=...)` exige tamaños lógicos completos por
  descripción, valida datos y genera placementContractVersion=1 opcional. C++ recalcula desde
  el JSON archivado: alineaciones 1/132/2, longitud por el eje del borde con clamp/mínimo de
  PanelLogic y redondeo al entero lógico (medios arriba), FillAvailable para fracción 1 sin
  flotación y Custom para las demás. Escribe claves/grupos KDE originales; offset inicial 0.
  Flotación captura la longitud nominal sin tocar, descontando el gap archivado; pintura y
  márgenes posteriores siguen al SVG nativo. No se inventa una clave de tema para floatingGap.
* **Compatibilidad:** planes sin captura mantienen el contrato anterior. Se verifica el
  plasmashellrc separado, el informe y el archivo de origen; claves inconsistentes o tamaños
  inválidos se rechazan. outputGeometryVerified/activationAllowed false: no prueba EDID ni
  habilita el panel diario. La captura automática en producción sigue sin activarse.
* **Ensayos:** QtTest de 4 bordes × 3 alineaciones con dos salidas lógicas, vista Panel.qml
  original, longitudes/mode/alineación y rechazos; Python de clamps/redondeo/flotación/tipos;
  siete propuestas Python→C++ y lectura nativa en la matriz con ejemplos KDE y Andromeda.
  Ajustada una expectativa vieja de check-isolated: al cerrar el perfil ahora debe crear
  otra generación (iteración 6), manteniendo archivo previo y bindings, no conservar su ID.
* **Pendiente:** escritorio, varias reservas en una salida, editor a escala fraccionaria,
  comparación visual y arrastre/desinstalar/alternativas. No se cambiaron monitores físicos
  ni se repitieron ensayos con ratón ya aceptados. Informe: BREEZE_R5_RESULTS.md.
* **Verificación final:** configuración local CTest 1/1 normal (49,27 s) y 1/1 ASan
  (`detect_leaks=0`, 55,02 s); el test comprueba también coordenadas del marco, no sólo
  propiedades. Python R4 262/262 (23 migración). Matriz completa con dos ejemplos KDE y
  Andromeda, siete casos nuevos por dos salidas y dos generaciones tras cierres limpios: pasa.


### 316. R5, iteración 8: reservas de varios paneles por salida y borde (2026-11-19)

* **Hecho:** `PanelRuntime::updateReservations` sigue `ShellCorona::shouldPanelReserveSpace`
  6.7.5: sólo el NormalPanel visible más grueso de cada salida/borde reserva (empate por ID
  menor). Los otros comparten reserva y pueden solaparse; no se suman/apilan artificialmente.
  Retirados/ocultos no son candidatos. Ya no se bloquean perfiles, clonaciones o movimientos
  hacia una salida ocupada. Se recalcula con tamaño, modo, borde/salida, vida y edición.
* **Edición:** como `PanelView::updateExclusiveZone`, conserva zonas positivas anteriores
  y da el marco completo a los que no reservaban; las congela hasta salir. Restaura después
  la selección normal y los modos sin reserva. No escribe otra preferencia para ello.
  Capacidades: reservationOwner y editModeReservation; replacementReady sigue false.
* **Fallo real corregido:** sólo cambiaba el estado layer-shell, sin escena visual nueva;
  QWindow::requestUpdate no entregaba siempre el commit. updatePanelPolicy usa ahora
  QQuickWindow::update. El ensayo que fallaba al retirar/traspasar la reserva pasa tras ello.
  El ejecutable del ensayo registra además PopupAnchor antes de cargar CompactApplet.
* **Comprobado en Hyprland:** MSI, sin la vista activa del usuario (estaba en LG), 10/10 pasos:
  top delta 56→64→56→0→64→120 (edición)→64→56, paso al borde opuesto y retirada. Capas,
  ausencia de toplevels propios, reservas restauradas y puntero/foco devueltos (dirección+PID).
* **Aceptación del usuario:** preview nativo en LG, clona arriba, sale de edición y maximiza;
  «Sí, se ajusta bien» con ambas reservas y al quitar/cambiar panel. No se infieren todas las
  esquinas/escalas/popups. Ensayo detenido con acuse, registro inactivo y configerrors vacío.
* **Límites:** elección sólo dentro del anfitrión, sin retirar el panel diario o reservas
  externas. Faltan bordes adyacentes/esquinas y sus popups, escala fraccionaria del editor,
  escritorio, comparación con Plasma y arrastre/desinstalar/alternativas. Informe R5 actualizado.
* **Verificación final:** compilación normal completa; CTest sin `native-` 8/8 (58,48 s),
  superficies/configuración local con ASan (`detect_leaks=0`) 2/2 (52,37 s). Sólo normal
  en sesión, no ASan nativo. Cero capas de ensayo tras el cierre; AGENTS/CLAUDE idénticos.


### 317. R5, iteración 9: alternativas de widgets, arrastre al panel, reordenado y desinstalación (2026-11-19)

* **Hecho:** `alternativeshelper.{h,cpp}` y `PanelViewHost::showAlternativesForApplet` adaptan
  `AlternativesHelper` y `ShellCorona::showAlternativesForApplet` de plasma-workspace 6.7.5
  (LGPL-2.0-or-later, Marco Martin). Registran `AlternativesHelper` en `org.kde.plasma.shell`
  (2.0 y 1.0), conectan `Containment::appletAlternativesRequested` (acción interna `alternatives`)
  y cargan sin modificar el `explorer/AppletAlternatives.qml` instalado. `loadAlternative`
  traslada el atajo global, sincroniza y copia el `config()` del widget saliente al nuevo,
  recarga su `configScheme()`, destruye el anterior y reconcilia `AppletOrder` en la ranura
  original.
* **Anclaje layer-shell y `SharedQmlEngine`:** `PopupAnchor` instala filtro de eventos sobre
  `m_popup` para `SurfaceCreated` y deriva un tamaño inicial no nulo desde `mainItem` (+ `margins`)
  antes de `Dialog::showEvent`. Como todas las instancias de `SharedQmlEngine` comparten el mismo
  `QQmlEngine` del proceso, tanto `PanelConfigView::eventFilter` como `AlternativesSurfaceFilter`
  filtran los `PlasmaQuick::Dialog` por la jerarquía `rootContext()` de su propio motor (antes
  `PanelConfigView` interceptaba `AppletAlternatives.qml` como un indicador `bwm-r5-edit-indicator`).
  El diálogo ignora además la pérdida de foco por hover hacia el panel, su popup de asa o los
  Ajustes del panel.
* **Ensayos offscreen y en Hyprland:** `originalAppletAlternativesDragAndUninstall` (`test-ui.cpp`,
  registrada en `check-local.py`) verifica el diálogo `AppletAlternatives.qml` (Escape + cambio de
  reloj analógico a digital conservando `AppletOrder`), el arrastre `text/x-plasmoidservicename`
  sobre el `DropArea` de `org.kde.panel`, el reordenado con `ConfigOverlay.qml` y la retirada +
  desinstalación de un widget local desde `WidgetExplorer.qml` (`removeAllInstances` +
  `pendingUninstallTimer.uninstall()`). En sesión Hyprland real (LG), `panelOwnPopupsInHyprland`
  (`check-edit-mode-session.py`) comprueba que `AppletAlternatives.qml` se mapea como capa
  `bwm-r4-popup` (`368×251` en `2560,1801`, justo encima del widget en `2568,2052 40×40`, `0`
  toplevels propios), sustituye el reloj en el panel vivo y se retira limpiamente restituyendo
  puntero y foco (verificando dirección y PID).
* **Verificación:** compilación normal y ASan completas; CTest normal sin `native-` **8/8**
  (59,67 s); CTest ASan (`detect_leaks=0`, `surface-geometry` + `isolated-local-configuration`)
  **2/2** (54,56 s); suite completa `check-edit-mode-session.py` en LG **38/38 pasos** OK sin
  capas residuales; Python R4 **262/262** OK.
* **Límites:** sin arrastre físico con ratón en la sesión del usuario. Siguen pendientes en R5
  bordes adyacentes/esquinas y sus popups, escala fraccionaria del editor, anfitrión de escritorio
  (`DesktopEditMode.qml`), comparación visual con Plasma real y aceptación final del usuario. No
  se sustituye el panel diario. Documentación actualizada en `docs/BREEZE_R5_RESULTS.md`,
  `src/bwm-plasma-host/README.md` y `THIRD_PARTY_NOTICES.md`.

### 318. Retro: extensiones de Nautilus operativas y LocalSend instalado (2026-11-20)

* **Origen comprobado:** Omarchy quattro `b20d7876f5ec6a45d18b9e4383dc4b6d9e8492ab`
  sigue incluyendo sólo `localsend.py` y `transcode.py` en `default/nautilus-python/extensions/`;
  BWM ya vendía ambas y las enlazaba al instalar/activar Retro (§3.308).
* **Corregido:** `Gio.Subprocess.wait_check()` lanza `GLib.Error` cuando `flatpak info`
  no encuentra LocalSend; la extensión ahora oculta esa acción sin excepción. Transcode
  propaga el PATH ampliado al terminal y al conversor, que llama a otros shims por nombre.
  Se conservan las acciones, filtros y escape de rutas de Omarchy.
* **Equipo:** nautilus-python ya estaba instalado y el Nautilus abierto tenía su biblioteca
  cargada. Se reaplicaron los enlaces sin cerrar ventanas y se instaló LocalSend **1.18.2**
  mediante `flatpak install --user --assumeyes --noninteractive flathub org.localsend.localsend_app`.
  Sin sudo. Sushi y ffmpegthumbnailer ya estaban disponibles.
* **Requisitos:** comprobación opcional de app Flatpak en requisitos de tipo `cmd`, utilizada
  por LocalSend; salida no cero/timeout/error no se consideran instalado. Catálogo con comando
  manual para Flathub y tabla `docs/REQUIREMENTS.md` regenerada. El menú Compartir de Retro
  sigue usando LocalSend nativo; la compatibilidad Flatpak comprobada aquí es la de Nautilus.
* **Verificado:** 17/17 pruebas (`test_nautilus_plugins`, `test_file_manager`, `test_skins`),
  compilación Python y `bash -n` del instalador. Proveedores reales GI/Nautilus 4.1 generan
  `Send via LocalSend` y `Transcode` para una selección local de imagen; `bwm check` da `ok`
  para Nautilus, nautilus-python, Sushi, ffmpegthumbnailer y LocalSend (Flatpak).
* **Límites:** no se enviaron archivos, no se lanzó conversión desde el menú ni se realizó
  prueba visual. No se reinició Nautilus, Quickshell o Hyprland; un Nautilus ya abierto puede
  necesitar cerrarse y abrirse para adoptar los cambios Python. Sin commit ni push.

### 319. Retro: Nautilus nativo, Nuevo documento, iconos originales y apertura por workspace (2026-11-20)

* **Alcance pedido:** además de las extensiones, crear archivos con clic derecho, distribución,
  aspecto/apertura de ventana e iconos. El usuario elige expresamente seguir el modo del
  workspace en Retro, conservando la regla flotante guardada para las demás skins.
* **Plantillas:** `skins/retro/scripts/setup-nautilus.py`, llamado con `--templates` desde
  el instalador y el cambio de skin. Usa XDG TEMPLATES (activa sólo esa ruta si estaba
  deshabilitada), añade `Archivo de texto.txt` y `Documento Markdown.md` de
  `skins/retro/nautilus-templates/` sin sobrescribir nada. Marca de una sola aplicación
  `~/.local/state/bwm/retro/nautilus-templates-v1`: respeta cambios/borrados posteriores.
  En este equipo quedó `~/Templates`. Esto es una adición BWM solicitada: quattro actual
  desactiva Templates, no distribuye ese menú como extensión propia.
* **Distribución/aspecto:** Omarchy no fija una vista ni un tamaño especial de Nautilus:
  usa sus valores nativos y la geometría del workspace. BWM mezclaba el CSS Material You
  del template compartido con su capa TUI. Retro ahora publica su `gtk/gtk4.css` nativo
  (sin esas dos capas); admite el `gtk.css` propio del tema original. Cambia el GTK4 de
  Retro en conjunto; default/Breeze y el GTK3 de Retro conservan sus recorridos previos.
  Se conserva la preferencia de vista del usuario y los favoritos comunes sincronizados.
* **Iconos:** el gestor común deja de sustituir el `icons.theme` original por BWM-Papirus.
  Usa el tema indicado si está instalado y Adwaita si falta/no se especifica (quattro
  `b20d7876f5ec6a45d18b9e4383dc4b6d9e8492ab` actual usa Adwaita). Se añadió instalador
  sin root de Yaru **25.10.3** para los temas incluidos antiguos: fuente oficial fijada por
  commit/SHA256, índices con generador original, variantes oscuras con herencia original,
  avisos/autores/licencias conservados y temas preexistentes intactos. Instalado en
  `~/.local/share/icons`; el tema actual declara y selecciona **Yaru-yellow**. Dependencias
  `xdg-user-dirs`, `adwaita-icons`, `yaru-icons` declaradas y tabla regenerada.
* **Apertura:** `toggle-float-persistent.py` genera exclusiones opcionales `excludeSkins`.
  Sólo la entrada guardada de Nautilus añade `retro`, preservando las demás reglas y su
  comportamiento fuera de Retro. Corregido también `workspace-modes.lua`: Hyprland 0.56
  exige `enable/disable`, no `on/off` (que alternaban silenciosamente).
* **Comprobado:** 35/35 pruebas (Nautilus apariencia/extensiones, gestor de archivos,
  manifiestos y runtime/iconos Qt), compilación Python, sintaxis Bash y CSS aceptado por
  el proveedor Gtk real. Gtk.IconTheme resuelve `folder`, `user-home`, `text-x-generic`
  a los archivos originales Yaru; sin enlaces rotos en Yaru/Yaru-yellow/Yaru-yellow-dark.
  `bwm check` da ok para los requisitos relacionados. Nautilus real abierto temporalmente
  sobre carpeta de ensayo en workspace 9 silent, sin foco: **floating=false, fullscreen=0**.
  Se cerró sólo esa ventana por dirección+PID, no quedan ventanas de ensayo y se retiró
  su regla con `hyprctl reload`; `configerrors` vacío.
* **Límites:** el proceso Nautilus previo (PID 25818) y sus ventanas se conservaron; requiere
  salir por completo y abrir otra vez para adoptar el CSS y la ruta XDG de plantillas.
  Sin comprobación visual del aspecto/menú ni envío/conversión desde ellos. No se probó
  físicamente la alternancia de modos del workspace; su acción idempotente pasa en fixture
  Lua. Sin reinicio de shell/compositor, sin commit ni push. Avisos de terceros actualizados.

### 320. Nautilus: Nuevo documento confirmado tras sustituir el proceso antiguo (2026-11-20)

* **Reporte:** sólo aparecía Nueva carpeta. XDG TEMPLATES apuntaba correctamente a
  `~/Templates`, con las dos plantillas vacías y legibles; GLib en un proceso nuevo lo
  resolvía bien. Nautilus seguía siendo el PID **25818** de antes de habilitar Templates.
* **Resuelto en sesión:** comprobado el estado no ocupado y las dos ubicaciones por
  `org.freedesktop.FileManager1.OpenWindowsWithLocations` (una pestaña por ventana).
  Se solicitó cierre normal y se verificó que el PID anterior había desaparecido. La CLI
  devolvió 255 durante el cierre/inicialización de display: no se tomó su retorno como
  prueba de éxito. Relanzado desde Hyprland mediante `bwm_session.spawn`, con activación
  silenciada, PID nuevo **210726**; dos ventanas y las mismas ubicaciones comprobadas por
  D-Bus. Ventanas resultantes en workspaces 1 y 3; no se acredita su geometría anterior.
* **Verificación real del menú:** sonda Python temporal cargada por nautilus-python,
  sólo de lectura del árbol GTK y propiedad nativa `templates-menu` de NautilusFilesView.
  En el segundo sondeo devolvió exactamente `Archivo de texto.txt` y
  `Documento Markdown.md`. No es una simulación del proveedor de extensiones ni una
  captura visual. Se retiraron la sonda, su bytecode y el informe; sin temporizadores
  pendientes de la sonda. Regla temporal de relanzamiento retirada con recarga.
* **Alcance:** configuración/plantillas ya eran correctas; no se añadió un reinicio a
  los cambios de skin. `Nuevo documento` sólo corresponde a carpetas escribibles, no
  a ubicaciones virtuales como Recientes. No se creó ningún archivo desde ese menú ni
  se verificó el clic físicamente. Sin commit ni push.

### 321. Breeze R5: ratón real de iteración 9 e iteración 10 (bordes adyacentes, esquinas, popups y escalas fraccionarias) (2026-11-20)

* **Verificación real con ratón de la iteración 9 (LG, `/dev/uinput`, autorizado por el usuario):**
  sin tocar la skin activa (`retro`), se lanzó `bwm-plasma-host --follow-panel-preview` en raíces
  XDG temporales sobre el LG (`DP-1`) y se comprobaron los 6 escenarios con eventos reales de
  ratón/teclado: (1) hover reloj → asa `ConfigOverlay` → clic «Show Alternatives…» →
  `AppletAlternatives.qml` (`368×254`, `0` clientes propios), sobrevive al hover del panel, cierra
  con Escape y clic fuera (`FocusGrab`), clic en `Calendar` sustituye en sitio; (2) `Add New` →
  `Widgets…` + arrastre Wayland `wl_data_device` de un widget local desechable al panel (explorador
  abierto durante el arrastre, guardado en `appletsrc`); (3) arrastre de reordenado en el panel
  (`AppletOrder` `2;3;4` → `3;4;2`); (4) `Remove all instances`, `Mark for Uninstallation` y
  `Uninstall (1 Widget)` (borrado de panel y del `XDG_DATA_HOME` temporal); (5) `Set Position…`
  (3 flechas → arriba `2560,64 3840×48`) y `Clone Panel` (2.º panel `6288,0 48×2160`, `0` clientes);
  (6) 0 capas residuales, cursor y foco restaurados, recortes temporales eliminados.
* **Iteración 10 — bordes adyacentes, esquinas y popups (`src/bwm-plasma-host/`):**
  - `surfaces.{h,cpp}`: `nativePanelAnchoring` ancla ambos bordes perpendiculares en `FillAvailable`
    (como `PanelView::updateLayerWindow` 6.7.5) para que Hyprland ajuste la longitud al `usableArea`
    sin solapar paneles en bordes adyacentes; `updatePanelPolicy` evita rebotes redundantes de
    `setExclusiveZone(-1)` en `configure`; `BwmSurface::setPanelLayoutContext` publica `bwmPanelBounds`
    y `bwmAvailableRect`. `PopupAnchor::update()` usa `exclusiveZone=0` y anclas alineadas al borde
    con sólo el saliente flotante `max(0, panelCross - zone)` para paneles que reservan, respetando
    tanto otros paneles del anfitrión como barras externas del compositor.
  - `viewcorona.{h,cpp}`, `panelviewhost.{h,cpp}`, `panelruntime.cpp`: `ViewCorona::setScreenAvailableRect`
    (semántica `ShellCorona::_availableScreenRect`), `surfaceOrder()` monótono en `QEvent::Show` y
    cálculo por salida en `PanelRuntime::updateReservations()`; `PanelViewHost::resizeEvent` sincroniza
    `rootObject()` y máscara; `reflow()` respeta longitudes estiradas configuradas por Wayland y acota
    `Custom`/`FitContent` a `bwmPanelBounds`.
  - `panelconfigview.cpp`, `widgetexplorerview.cpp`: `PanelRulerView` cambia a
    `KeyboardInteractivityNone` + `activateOnShow=false` (`Ruler.qml` es sólo puntero), corrigiendo el
    robo de foco a `PanelConfigView` (Escape) en sesiones de un solo monitor; `placeIndicator` deriva
    tamaño inicial no nulo y llama a `update()`, igual que `WidgetExplorerView::place()`.
* **Verificado:**
  - Compilación y CTest normal (`-E "^native-"`): **8/8** (incluidos `surface-geometry` con
    `adjacentEdgeLayoutAndCornerPopups` e `isolated-local-configuration` con
    `adjacentEdgesCornersAndAvailableRect`).
  - Compilación y CTest ASan (`detect_leaks=0`, `surface-geometry` + `isolated-local-configuration`):
    **2/2** (tras limpiar el hover `QEvent::Leave` antes de abrir el explorador en `offscreen`).
  - Suite Python R4 (`test_r4_*.py`): **262/262 OK**.
  - Hyprland real (`check-edit-mode-session.py --output "LG Electronics LG ULTRAFINE 405NTVS2J655"`):
    exit 0 (todos los pasos `passed: true`, incluido `nativeAdjacentEdgesAndCornerPopupsInHyprland`
    con arriba+izquierda, Ajustes/Alternativas/Explorador en esquina y 3 bordes simultáneos disjuntos).
  - Escalas fraccionarias (`check-edit-mode-session.py --fractional-scale`, salida headless temporal
    `BWMR5-*`): **21/21 pasos** en `1.25` (`1536×864`), `1.5` (`1280×720`) y `1.6` (`1200×675`),
    `windowDpr` exacto vía `wp_fractional_scale_v1`, `physicalOutputsUnchanged: true`, salida temporal
    eliminada. 0 capas `bwm-r4-*`/`bwm-r5-*` residuales y `hyprctl configerrors` vacío.
* **Pendiente en R5:** anfitrión de escritorio (`DesktopEditMode.qml`), comparación visual con Plasma
  real (incl. comprobación visual subpíxel en escalas fraccionarias) y aceptación final del usuario.
  No se sustituye el panel diario. Documentación actualizada en `docs/BREEZE_R5_RESULTS.md`,
  `src/bwm-plasma-host/README.md` y `THIRD_PARTY_NOTICES.md`. Sin commit ni push todavía.

### 322. Breeze R5: iteración 11 — anfitrión de escritorio (`DesktopViewHost`) y `DesktopEditMode.qml` (2026-11-20)

* **Anfitrión de escritorio (`src/bwm-plasma-host/desktopviewhost.{h,cpp}`, `CMakeLists.txt`):**
  adapta `shell/desktopview.{h,cpp}` de plasma-workspace 6.7.5 (GPL-2.0-or-later) sobre
  `PlasmaQuick::ContainmentView` y `LayerShellQt`. Carga sin modificar el `views/Desktop.qml`
  instalado (y `views/DesktopEditMode.qml`) con el containment real `org.kde.plasma.folder`.
  `shell/contents/defaults` añade `[Desktop]` y `[Desktop][ContainmentActions]` de plasma-desktop
  6.7.5 (`org.kde.plasma.folder`, `org.kde.contextmenu`, `org.kde.paste`).
* **Contrato compartido Corona/panel/escritorio (`viewcorona.{h,cpp}`, `panelviewhost.{h,cpp}`,
  `panelconfigview.cpp`, `panelruntime.cpp`):**
  - `ViewCorona` añade `panelBeingConfigured`, `enteredEditModeViaDesktop()`,
    `showAddPanelContextMenu` («Default Panel» / «Empty Panel» → `addPanelRequested`) y las
    acciones `"add panel"` y `"edit mode"` (texto dinámico Enter/Exit Edit Mode).
  - `PanelViewHost` expone `relativeConfigRect` y sincroniza `panelBeingConfigured`;
    `PanelConfigView::hideEvent` respeta `enteredEditModeViaDesktop()` de modo que cerrar
    Ajustes de un panel mantiene `DesktopEditMode.qml` abierto cuando se entró desde el escritorio.
  - `PanelRuntime::setAssignments` ignora containments no-panel para que escritorios y paneles
    coexistan en la misma `ViewCorona`.
* **Layer-shell en Hyprland:** `bwm-r5-desktop` en `LayerBackground` (`wantsToBeOnActiveScreen=false`,
  ligado explícitamente a `m_targetScreen` y `setGeometry(target->geometry())` para no saltar al
  monitor enfocado), `sidePanel` original de `Desktop.qml` interceptado en `SurfaceCreated` como
  `bwm-r5-desktop-explorer` (`LayerTop`, `exclusiveZone=0`, `FocusGrab`, tolerando hover en el
  escritorio/paneles) y `AppletAlternatives.qml` del escritorio como `bwm-r5-desktop-popup`
  (`LayerOverlay`, `exclusiveZone=0`).
* **Verificado:**
  - `originalDesktopEditModeHost` (`test-ui.cpp` / `check-local.py`): offscreen normal (**8/8**
    CTest `-E "^native-"`) y ASan (**2/2**, 58,91 s, 0 errores ASan).
  - Suite Python R4 (`test_r4_*.py`): **262/262 OK**.
  - Hyprland real (`originalDesktopEditModeInHyprland` en LG): **6/6 pasos** (`bwm-r5-desktop`
    `2560,0 3840×2160`, `scale: 0.88`, `strictAvail: 0,0 3840×2112`, traspaso `PanelConfigView`
    `4270,1570 420×542`, `bwm-r5-desktop-explorer` `2560,26 498×2086`, `bwm-r5-desktop-popup`
    `4361,1224 368×251`, todos con `0` clientes toplevel y limpieza total).
  - Escalas fraccionarias (`--fractional-scale`): **21/21 pasos** (`1.25`/`1.5`/`1.6`,
    `physicalOutputsUnchanged: true`). 0 capas residuales `bwm-r4-*`/`bwm-r5-*` y
    `hyprctl configerrors` vacío.
* **Pendiente para cerrar R5:** verificación interactiva/visual de `DesktopEditMode.qml`,
  comparación visual con Plasma real (incl. escalas fraccionarias) y aceptación final del usuario.
  Sin sustituir el fondo ni el panel diario. Documentación actualizada en `docs/BREEZE_R5_RESULTS.md`,
  `src/bwm-plasma-host/README.md` y `THIRD_PARTY_NOTICES.md`. Sin commit ni push.

### 323. Breeze R5: cierre — escritorio interactivo, configuración del escritorio y «Add Panel» (2026-11-20)

* **Petición:** cerrar R5 desde `d24d896`: interacción real y comparación visual del escritorio y del
  modo edición, corregir desajustes, verificación completa y documentación para la aceptación.
* **Vista desechable con escritorio:** `preview-isolated.py --desktop` (con `--native-panel --layer-panel
  --follow-skin`) añade el `Desktop.qml` original en la misma salida mientras la skin seguida sea Breeze;
  `desktop:/` a una carpeta desechable, plataforma Qt `kde`. Diagnóstico opcional `BWM_R5_DEBUG_MENUS=1`
  y categoría `bwm.r5.corona`.
* **Corregido (encontrado con ratón real en el LG):** Folder View nunca se cargaba (el `main.qml`
  original evalúa `corona.isScreenUiReady(screen)` sólo al cambiar la pantalla; `ViewCorona` ahora la
  asigna al escritorio cuando su vista y los paneles están listos, y la conserva); faltaba la acción
  `desktop edit mode` de `DesktopView` y `edit mode` volvía a ser la de libplasma; «Desktop and
  Wallpaper…» abre `ContainmentConfigView` (adaptado, LGPL) con `ContainmentConfiguration.qml` y cambia
  el contenedor con `setContainmentType`; «Aplicar» se recalcula una vez con la función original
  `settingValueChanged()` tras cargar; «Add Panel» ejecuta sin cambios las plantillas `layout.js`
  (`LayoutTemplateRunner`, subconjunto LGPL de la API de scripts) desde `PanelRuntime::addPanel`;
  `strictAvailableScreenRect` cruza el área de los paneles propios con `reserved` de Hyprland (barras
  externas); textos con el catálogo `plasmashell`.
* **Comprobado con ratón real (LG, skin `retro` intacta, raíces temporales):** menú del escritorio,
  entrar/salir del modo edición (botón, Escape, clic fuera), «Default/Empty Panel», explorador y arrastre
  de un widget al escritorio, mover/configurar el widget, Ajustes del panel a la vez (Escape sólo los
  cierra), fondo aplicado y Layout Folder View → Desktop. LG devuelto al workspace 10 con el mismo foco
  y puntero; capturas borradas. No se probó el botón central (pegaría el portapapeles real).
* **Pruebas:** CTest normal 8/8, ASan 2/2, Python R4 262/262, sesión LG completa (51 pasos) y
  `--fractional-scale` 24/24 con el escritorio a 1,25/1,5/1,6; 0 capas residuales, `configerrors`
  vacío. Pruebas offscreen sin `QT_QPA_PLATFORMTHEME` heredado (`gtk3` de Retro las rompe). La
  plantilla «Default Panel» no se prueba offscreen: Klipper cae en XCB sin X11.
* **Pendiente / diferencias:** marco de configuración de widgets de R4 (no el `AppletConfiguration.qml`
  de Plasma), sin sombras ni desenfoque de KWin (R6), `manage-containments` sin portar, reserva congelada
  en edición con el grosor de creación, sin revisión visual subpíxel a escala fraccionaria ni capturas
  de un Plasma real. Aceptación del usuario pendiente; no sustituye el panel diario ni el fondo de Breeze.
  Sin commit.

### 324. Breeze R6: primera iteración de sombras KDecoration, comparador KWin y ensayo anidado (2026-11-20)

* **Petición:** continuar desde el cierre técnico de R5 de Claude (§323). Se revisaron los
  cambios pendientes sin mezclarlos ni commitearlos; R5 conserva su aceptación visual pendiente.
  La skin real observada al comenzar/terminar era `plasma` (no se cambió de skin).
* **Sombra de decoración:** `DecoLogic.hpp` corrige los huecos de `floor/ceil`, acota y
  redistribuye solapes asimétricos y lados opuestos, respeta el umbral mínimo de 5 y usa las
  dimensiones de imagen de `DecorationShadow` como KWin 6.7.5 (DPR no divide sus geometrías).
  `barRemote.cpp` invalida áreas anterior/nueva al cambiar/retirar/perder sombras y suprime
  el dibujo en fullscreen/maximizado completo. No fuerza sombras sobre CSD sin marco remoto.
* **Vida/transporte:** `shadowstate.h` sigue imagen/padding/innerShadowRect del mismo objeto
  y desconecta sombras anteriores. Retirada explícita al recrear una decoración sin sombra.
  Memfd sellado contra escritura/redimensionado; no se da por enviado un fallo de memoria,
  sellado o socket. `ShadowBuffer.hpp` valida layout/valores finitos y copia con `pread` para
  rechazar un fd corto sin SIGBUS de un mapeo. Sólo afecta al transporte de sombras, no Frame.
* **Preferencias nativas:** prueba real del auxiliar con `[Common] ShadowSize/Strength/Color`
  encontró que la primera decoración de Breeze recibía `reconfigured` antes que su proveedor
  compartido. Una notificación pública encolada completa la lectura y aplica el primer cambio
  sin reescribir el formato/diálogo KDE. Probada retirada/restauración y reconexión del cliente.
* **Comparación reproducible:** `check-r6-shadows.py` exige SHA256 de `shadowitem.cpp` de KWin
  6.7.5 y ejecuta sus métodos sin modificar con geometría Qt/KDecoration real en un contenedor
  mínimo. **192 casos + 18 muestras** (BreezeDark/Light activas/inactivas a 1/1,25/1,5/2;
  Aurorae Sweet-Dark activa/inactiva): geometrías/UV iguales y error CPU máximo de color/alpha
  **0**. Pasa normal y ASan/UBSan del comparador/lector/observador; las muestras del auxiliar
  se producen con la compilación normal. No es una captura de una sesión Plasma equivalente.
* **Render real aislado:** candidato compilado en copia con `-fno-gnu-unique`, 0 símbolos
  UNIQUE y `make install` atómico **sólo en `build/r6-plugin/installed`**. El ensayo
  `check-r6-nested.py` carga ese candidato al inicio de un Hyprland nuevo, antes de clientes.
  Wayland SSD con marco KDE: **62 586 píxeles externos** cambian al suprimir la sombra,
  PID/geometría iguales, sombra genérica apagada. La ventana del hijo necesita una salida
  virtual del padre (retirada al cerrar): oculta no recibe frames y el headless del hijo
  falló con GBM NVIDIA. XWayland a demanda bloqueó los primeros intentos de carga; se apagó
  sólo en el fixture y se retiró DISPLAY, sin atribuir causa exacta sin pila. XWayland no
  probado. Dos avisos propios de no respuesta retirados por PID; primera prueba gráfica
  detectó puntero desplazado, corregida su restitución. Ensayo final: foco/puntero, salidas,
  workspaces físicos y handles de plugins iguales; limpieza total y configerrors vacío.
* **Regresión:** compilación del host R5 actual y CTest **8/8**, Python R4 **262/262**;
  decorador **13/13**, breezebars **4/4**, política diaria de sombras **1/1**. Guarda de captura
  actual verificada por peer Wayland/IPC, PID 3195; no reproduce el incidente original.
* **Pendiente:** R6 sigue abierta: paneles/menús/popups (protocolo KDE de sombras y hints X11
  sin backend en Hyprland), blur/contraste del panel (existe ext-background-effect y KDE sabe
  usarlo, no falta todo desenfoque por protocolo), matriz GPU de escalas/foco/resize/cierre/
  pérdida del auxiliar/CSD/XWayland y comparación visual con Plasma real. **Veto diario
  `no_shadow=true` conservado**, sin instalar candidato/auxiliar diarios ni reiniciar shell/
  sesión. Detalle y evidencias en `docs/BREEZE_R6_RESULTS.md` y
  `docs/BREEZE_R6_SHADOW_RESULTS.json`. AGENTS/CLAUDE sincronizados. Sin commit ni push.


### 325. Breeze R5: pendientes de la iteración 12, marco/gestor originales y referencia Plasma real (2026-11-20)

* **Petición:** comprobar si quedaba trabajo de R5 y hacerlo antes de continuar R6. La iteración
  anterior sí dejaba funciones y pruebas pendientes; se retoma R5. Se conserva el candidato R6 de
  §324 sin instalarlo ni ampliar sus cambios.
* **Configuración de widgets:** vistas interactivas con `AppletConfiguration.qml` instalado, barra
  lateral, Atajos, Acerca de y aviso original de cambios. Aplicar/Descartar originales probados.
  El marco reducido y las transacciones R4 quedan sólo en su arnés de diagnóstico, no en esas vistas.
* **Gestor:** `containmentmanagement.{h,cpp}` adapta los modelos de `shell/shellcontainmentconfig`
  6.7.5, LGPL-2.0-or-later (Cyril Rossi 2021). Carga el gestor/delegados originales sin modificar,
  publica tarjetas/previsualizaciones propias y mueve paneles por descripción física. Intercambia
  escritorios y recupera contenedores desconectados conservando widgets. Sale del modo edición.
  En las vistas Qt se cualifica `QWindow::destroy()`; el método de `ContainmentView` elimina el host.
* **Otros pendientes corregidos:** preferencias de plantilla antes de congelar la reserva de edición
  (ya no 48 px hasta salir); «Add Panel» consulta asíncronamente la salida enfocada del compositor;
  captura por valor de la función local del sincronizador de escritorio. La comparación real confirma
  Aplicar inicialmente desactivado: se descarta el aviso inicial de normalización de `SlidePaths`
  para que el primer cambio real emita su aviso. Guardar fondo sigue confirmado por configuración KDE.
* **Referencia real aislada:** `check-r5-reference.py` + `tests/r5_reference_client.cpp` arrancan KWin
  y plasmashell 6.7.5 con D-Bus, actividad y raíces XDG privados, sin cambiar `$HOME`. OpenGL,
  Breeze Oscuro, 1600×1000 lógicos; escalas 1/1,25/1,5/1,6 aplicadas/verificadas con kscreen-doctor
  privado y metadatos de captura. `QScreen` puede dar DPR entero superior: no prueba la escala real.
  Tres ventanas por escala (widget/color/imagen): a 1 idénticas; en fraccionaria 9–124 píxeles
  distintos, diferencia máxima de 1/255 por canal. Modo edición comparado y revisado con diferencias
  de efectos del compositor y visibilidad inicial de «Gestionar…» documentadas; no paridad total.
* **Botón central:** entrada Wayland y selección primaria privadas; nativo y BWM crean un widget
  `org.kde.plasma.icon` con la URL local desechable comprobada, no una copia del archivo a Desktop.
  No se leyó ni sustituyó el portapapeles del usuario. Los procesos/raíces privados se retiran;
  capturas de fixture borradas tras inspección, hashes/métricas en `docs/BREEZE_R5_REFERENCE_RESULTS.json`.
* **Pruebas:** CTest normal 8/8, ASan 2/2 (`detect_leaks=0`), Python R4 262/262. Casos nuevos del
  marco original y gestor (incl. recuperación desconectados), reserva de plantilla y estado de Aplicar.
  LG: 8 pasos con escritorio, explorador, ajustes, alternativas, salida activa para panel y limpieza.
  Headless Hyprland 1,25/1,5/1,6: 24/24, salidas físicas sin cambios. Offscreen sin plataforma gtk3.
* **Alcance:** R5 técnica en el anfitrión aislado; queda la aceptación propia del usuario y la
  integración diaria de R4. Efectos del compositor, producción y demás límites en los informes R5/R6.
  Recuperación de contenedores sin vista probada offscreen; intercambio y recuperación de
  superficies Wayland en LG/MSI (3/3, foco y reservas intactos), sin desconexión física. Skin diaria conservada
  (`plasma` en esta sesión); no reinicio de Quickshell/sesión ni instalación de .so diario.
  Codex no ejecutó commits/push. Durante el trabajo aparecieron `7315921` y `a761afb` (incluyen
  parte de los archivos aún en progreso); se conserva ese historial. Los últimos ajustes y la
  evidencia JSON siguen en el árbol de trabajo.

### 326. Breeze R6, iteración 2: sombras nativas KDE de superficies, panel, diálogos y XWayland (2026-11-21)

* **Origen:** iniciada por Codex (ChatGPT) y terminada por Claude cuando a Codex se le agotó
  el uso. Se revisó lo que dejó en el árbol, se repitieron sus ensayos con el estado final y
  se corrigieron dos fallos.
* **Hecho (Codex):** servidor `org_kde_kwin_shadow_manager` v2 en `src/breezebars/KdeShadow.cpp`
  con `protocols/shadow.xml` (LGPL-2.1, generado con `wayland-scanner`; Makefile/CMake/meson
  actualizados, requisito `breezebars-build`). Copia SHM acotada (`KdeShadowPixels.hpp`), atlas
  `NinePatchOpenGL` y geometría `ShadowItem::buildQuads` para ocho piezas
  (`KdeShadowGeometry.hpp`), estado aplicado en el commit real de la superficie, prioridad de
  KDecoration, `hyprctl -j breezebars-shadows`. Panel: `PanelShadows` de plasma-workspace 6.7.5
  (`panelshadows.cpp`) y `KWindowEffects` desde `PanelViewHost::updateMask`; bordes con la
  geometría del anclaje (Qt da (0,0) en layer-shell). Diálogos: `ensureNativeEffectsCommit`
  pide un fotograma para que una escena estática envíe los efectos. CSDDetect ya no llama a
  `xcb_connect` al cargar. Arneses `check-r6-surfaces.py`, `test-r6-native.cpp`,
  `tests/r6_x11_client.cpp` y `--xwayland` en `check-r6-nested.py`.
* **Corregido en esta continuación:** `PanelShadows::removeWindow` dejaba la ventana como
  observada tras desconectar su aviso de destrucción; después de auto-ocultar no se
  reconectaba y un cambio de SVG usaba un `QWindow` liberado (SIGSEGV 3/3 en
  `test-paneltasks`). Los ensayos restauran ahora puntero y ventana enfocada (dirección+PID):
  retirar la salida headless temporal daba el foco a la última ventana de otro monitor.
* **Comprobado:** matriz de piezas Breeze oscuro/claro/Sweet × 1/1,25/1,5/2, 120 casos con
  opacidad por `wp_alpha_modifier_v1`, máx. 1/255; 12 liberaciones y 12 cierres con sombras
  vivas. Ese ensayo de 40 min terminó con el puntero movido (sesión en uso); repetición corta
  con la sesión intacta. Diálogo `PlasmaQuick::Dialog` original, 3 temas × 1/1,25: 42 casos,
  máx. 3/255, recreación/ocultar/opacidad exactos, sesión intacta. Panel BWM frente a
  plasmashell en KWin: idéntico a 1/1,25/1,5, 1/255 en 2 píxeles a 2 (informe de Codex).
  Desenfoque: región exacta y retirada limpia; intensidad hasta 33/255 distinta (algoritmo de
  Hyprland). XWayland privado: sombra KDE en ventana SSD, sin segundo marco con GTK/Motif.
  Regresión: CTest 8/8, ASan 2/2, Python R4 262/262, breezebars/política 5/5, decorador 13/13,
  suite de sesión en el LG 54/54 sin capas residuales y `configerrors` vacío.
* **Límites:** sólo SHM; sin `_KDE_NET_WM_SHADOW` ni dmabuf; contraste no disponible (KWin 6.7.5
  tampoco lo ofrece por separado); sin sombras de menús/tooltips de Quickshell; sin comparación
  con una sesión Plasma completa. Candidato `build/r6-surface-plugin/installed/breezebars.so`,
  0 símbolos UNIQUE, no instalado en `config/hypr/plugins`; `no_shadow=true` sigue vigente y
  activarlo exige volver a iniciar sesión. Evidencia `docs/BREEZE_R6_SURFACE_RESULTS.json`.

### 327. Breeze R6, iteración 3: decoración completa frente a KWin real (2026-11-21)

* **Petición:** «continúa» tras el commit de la iteración 2. Faltaba comparar en GPU la decoración de
  las ventanas normales (lo más visible de R6) con KWin real.
* **Hecho:** `test-r6-native` añade el tipo `decorated` (xdg_toplevel con decoración del servidor y
  una segunda ventana para volverla inactiva). `check-r6-surfaces.py --kind decorated` arranca
  `bwm-decorator` para el Hyprland anidado, da a ambos compositores el mismo `kwinrc` (Breeze o
  Aurorae Sweet-Dark copiada a la raíz privada) y alinea por el color del contenido (erosión para
  ignorar el puntero).
* **Corregido:** grosor del contorno escalado dos veces en `barRemote.cpp` (`renderBorder` ya
  escala); el auxiliar pinta sobre una imagen con `devicePixelRatio` (iconos nítidos en HiDPI);
  `Bridge::readIconTheme` añade las carpetas XDG `icons` y `/usr/share/pixmaps` (offscreen sólo
  buscaba `:/icons`: Aurorae y los iconos hicolor salían vacíos, también en la sesión diaria);
  icono `wayland` de reserva como KWin y bandera `X11` (65536) en el protocolo. La referencia KWin
  usa ahora el tema de plataforma de KDE y dos escritorios. Sombra de Aurorae: se crea en `init()`
  antes de los bordes y sólo se rehace al cambiar de activa; KWin crea la decoración inactiva y la
  activa al mapear. El auxiliar la creaba activa (Sweet: 380×260 en vez de 388×292) y ahora sigue
  ese ciclo: decoración inactiva y estado real después.
* **Comprobado:** 36 casos. Breeze oscuro máx. 73/255 y claro 109/255, sólo en el antialiasing de
  las esquinas del contenido; sombra ≤2/255. Sweet máx. 2/255. La primera imagen es idéntica a la
  reactivada en los 12 pares (comprobación estricta). Decorador 15/15 (regresiones de hicolor y de
  la sombra de Aurorae, que fallan con el binario anterior), breezebars 4/4, XWayland anidado y
  piezas sin cambios. Las imágenes pasan; la matriz y XWayland sólo vieron moverse el puntero
  (uso del equipo durante el ensayo).
* **Límites:** sin comparar tamaño/maximizado pedidos por el cliente (Hyprland conserva el tamaño
  flotante; BWM bloquea el maximizado de apps), enrollar ni X11 frente a KWin. Auxiliar y plugin
  corregidos sin instalar en la sesión diaria. Evidencia `docs/BREEZE_R6_DECORATION_RESULTS.json`.

### 328. Breeze R6, iteración 4: radio de las esquinas del contenido (2026-11-21)

* **Petición:** «continúa» tras el commit de la iteración 3. Quedaba la mayor diferencia de la
  decoración Breeze frente a KWin: las esquinas inferiores del contenido.
* **Causa medida:** no era el suavizado sino el radio. KWin recorta con `round(radio × escala)` y
  círculo exacto (`itemrenderer_opengl.cpp`, `sdf.glsl` 6.7.5); Hyprland 0.56.2 usa regla × escala ×
  (potencia/2) − 1 px (`ElementRenderer.cpp`), y `barRemote.cpp` redondeaba el radio lógico a
  entero: 4 px en vez de 5 a escala 1, 6,5 en vez de 8 a 1,5.
* **Hecho:** `contentRounding()` en `DecoLogic.hpp` elige el entero que deja el radio de Hyprland
  más cerca del de KWin con la escala del monitor; `applyRoundingOverride` fija también potencia 2.
  Prueba en `tests/breezebars_wire_test.cpp` («ok redondeo»): todas las escalas/radios frente a
  cualquier otro entero.
* **Comprobado:** matriz completa (`build/r6-decorated-iter4.json`, `passed: true`, sesión intacta):
  Breeze oscuro 12/16/14/52 y claro 22/27/26/46 a 1/1,25/1,5/2; Sweet ≤2. Primera imagen idéntica a la
  reactivada en los 24 casos. Breezebars 4/4. Candidato en `build/r6-surface-plugin`, 0 UNIQUE.
* **Límites:** a escala 2 la regla entera da 9 u 11 px frente a 10; queda el suavizado del contorno
  (`renderBorder` frente al sombreador de borde de KWin). Sin instalar en la sesión diaria; veto
  `no_shadow=true` intacto.

### 329. Breeze R6, iteración 5: desenfoque y contorno (análisis, 2026-11-21)

* **Petición:** «haz commit y continúa» tras la iteración 4.
* **Contorno:** las 40–57 diferencias diagonales de las esquinas vienen de la cobertura de
  `renderBorder` de Hyprland frente al borde SDF de KWin (`fwidth`); no hay parámetro: límite.
* **Desenfoque:** KWin 6.7.5 (`downsample/upsample.frag`, `initBlurStrengthValues`) y Hyprland
  0.56.2 (`blur1/blur2.glsl`) comparten núcleos *dual kawase*; KWin desplaza `offset`/2 téxeles del
  nivel leído y recorta a región + 150 px, Hyprland `size` al reducir y `size`/4 al ampliar sobre
  búferes de monitor. Barrido en el anidado frente a KWin (intensidad 15 por defecto): Hyprland por
  defecto 32/255, `passes` 7/`size` 8 (o 8/4) con `noise` 0 y `contrast`/`brightness` 1, `vibrancy`
  0 → 4/255 en tablero y 2/255 en cuadrantes. No mide la saturación 150 %; depende del tamaño de la
  región.
* **Semántica:** capas sólo si lo piden (como KWin); ventanas todas salvo `no_blur`, que Breeze pone
  a todas. Activarlo en Breeze diario es un cambio visible: pendiente de decisión del usuario.
* **Herramientas:** `check-r6-surfaces.py --blur-pattern edge`, `--hypr-blur`, `--backends`;
  `test-r6-native` con `BWM_R6_EFFECTS_PATTERN=edge`. Sin cambios en la sesión diaria.

### 330. Breeze R6, iteración 6: desenfoque de KWin en Breeze diario (2026-11-21)

* **Petición:** «Sí, actívalo», tras el análisis de §329.
* **Hecho:** `skins/plasma/hypr/kwin.lua` enciende `decoration.blur` salvo `[Plugins]
  blurEnabled=false` y traduce `[Effect-blur] BlurStrength` con la tabla de KWin (iteraciones + 3
  pasadas, desplazamiento como `size`; 7/8 por defecto) sin ruido/contraste/brillo/viveza;
  `kde-config-bridge.py` exporta `blur`/`blurStrength`; `appearance.lua` repone en las otras skins
  los valores por defecto de Hyprland. Regla de capa `breeze-blur-frames` (`ignore_alpha` 0,01,
  `blur_popups`) para panel, Kickoff y notificaciones. `BackgroundEffect.blurRegion` en
  `Panel.qml`, `KickoffWindow.qml`, `TrayPopup.qml` y `NotificationPopups.qml`; nuevo
  `theme/BlurPath.qml` (orden de búsqueda de KSvg con el selector `translucent`) y
  `PlasmaTheme.blur` (lee `kwinrc` del usuario: un vigilante más; inotify medido en 106/128).
* **Comprobado:** `hyprctl getoption` tras recarga, `configerrors` vacío, reinicio de
  mantenimiento del shell sin errores (mismos workspaces y foco); Kickoff por IPC con marco
  translúcido sobre fondo desenfocado; puente KDE 21 y QML 30 pruebas. El panel del usuario está en
  «Opaco».
* **Límites:** ventanas que piden desenfoque siguen con `no_blur` (requiere el plugin); menús,
  descripción emergente, OSD, cambiador y KRunner aún no lo piden; no probado el cambio de skin con
  estos valores ni comparado con Plasma completo.
* **Incidencia:** un comando de esta sesión extrajo `quickshell-0.3.2/` en la raíz del repo por no
  cambiar de carpeta; se borró (no estaba en Git).

### 331. Breeze R6, iteración 7: ventanas que piden desenfoque y franja doble (2026-11-21)

* **Petición:** «continúa» tras activar el desenfoque en Breeze diario (§330).
* **Hecho:** `barDeco.cpp` (`updateRules`, en cada commit de la superficie) fija `noBlur` con
  `PRIORITY_LAYOUT`: verdadero salvo que la superficie tenga `m_hasBackgroundEffect` con región no
  vacía; nada fuera de Breeze. `main.cpp` registra `blur_on_request`; `skins/plasma/hypr/rules.lua`
  sólo pone `no_blur` en `breeze-float-all` si el plugin cargado no la tiene (plugin diario actual:
  sin cambios). `SquareTop.cpp`: el original se recorta con `clipBox` bajo la franja superior y la
  copia sin redondeo dibuja sólo la franja (antes se superponía: +8/255 en las 8 primeras filas de
  una ventana translúcida, fallo también diario) y conserva el desenfoque.
* **Ensayo:** `check-r6-surfaces.py --kind decorated --effects` (ventana translúcida sobre tablero;
  `test-r6-native` con formato con alfa), `--user-no-blur`; captura guardada antes de procesarla.
  KWin y Hyprland: sin petición nada, con petición sólo la mitad pedida (37 290 = 37 290 a 1; 83 819
  / 83 824 a 1,5), retirada exacta; regla del usuario gana. Decoración 1/1,5 igual que §328, capas y
  breezebars 4/4. Candidato 0 UNIQUE.
* **Límites:** sin instalar en la sesión diaria (plugin + volver a iniciar sesión).

### 332. Breeze R6, iteración 8: OSD, cambiador y descripciones emergentes (2026-11-21)

* **Petición:** «CONTINUA» tras §331.
* **Hecho:** `osd/Osd.qml` y `switcher/ThumbnailGrid.qml` con `BackgroundEffect.blurRegion` sobre su
  marco y `BlurPath` (variantes translúcidas de `widgets/background` y `dialogs/background`);
  `breeze-blur-frames` añade `quickshell:altTab` y `bwm-plasma-osd`. `theme/ToolTipArea.qml` y
  `panel/TaskToolTip.qml` usan `widgets/tooltip` translúcido con desenfoque (como `ToolTipDialog`);
  sin desenfoque, lo de antes. `tests/test_plasma_task_input.py` da un sustituto de `BlurPath`.
* **Comprobado:** shell reiniciado sin errores, OSD por IPC, pruebas QML (interfaces, bandeja, tareas,
  panel, Kickoff), puente KDE y `--verify-config`.
* **Incidencia:** abrir el cambiador por IPC sin Alt lo cerró activando otra ventana; se devolvió el
  foco a la original (Firefox) y se borraron las capturas. No abrir Alt+Tab por IPC en la sesión real.
* **Pendiente:** Alt+Tab real, temas globales con `ThemeHost`, menús contextuales y KRunner.

### 333. Breeze R6, iteración 9: menús contextuales, temas globales (`ThemeHost`) y KRunner (2026-11-21)

* **Petición:** continuar por lo pendiente de §332 (desenfoque en temas globales con `ThemeHost`,
  menús contextuales y KRunner).
* **Hecho:**
  * `config/hypr/skins/plasma/hypr/rules.lua`: `breeze-blur-frames` incluye `quickshell:plasmaMenu`
    y `krunner` (`krunner` usa `PlasmaQuick::PlasmaWindow` con `LayerShellQt::setScope("krunner")`,
    que ya llama a `KWindowEffects::enableBlurBehind` y usa `translucent/dialogs/background`).
  * `config/quickshell/ii/modules/plasma/menus/MenuHost.qml`: aplica `BlurPath`
    (`widgets/background`) al menú abierto y sus submenús (incluidos dinámicos) y actualiza
    `BackgroundEffect.blurRegion` con sus marcos abiertos (destruyendo regiones previas).
  * `config/quickshell/ii/modules/plasma/switcher/compat/Dialog.qml`, `osd/Osd.qml`,
    `switcher/Switcher.qml` y `switcher/ThemedSwitcher.qml`: pasan `bwmDialogImagePath` y
    `bwmBlurTarget` al motor QML de `ThemeHost` para que `BwmCompat.Dialog` use la variante
    translúcida y registre su `FrameSvgItem` en `BackgroundEffect.blurRegion`.
  * `config/quickshell/ii/modules/plasma/panel/PanelEditor.qml`: pasa también a `BlurPath`
    (`dialogs/background`).
  * Pruebas actualizadas: `tests/test_plasma_interfaces.py` (contrato `BwmCompat.Dialog` en
    `ThemeHost`), `tests/test_plasma_menus_ui.py` (fondo translúcido en menú/submenú y conteo de
    regiones al abrir y cerrar) y `tests/test_plasma_shadow_policy.py` (`layer_rule` de
    `breeze-blur-frames`, `blur_on_request` y transición Lua `plasma` ↔ `default` ↔ `retro`
    restaurando todos los parámetros de `decoration.blur`).
* **Comprobado:** `hyprctl reload` sin errores, reinicio de mantenimiento del shell sin errores
  (mismos workspaces y foco), `test_plasma_interfaces.py` 8/8, `test_plasma_menus_ui.py` 5/5,
  `test_plasma_shadow_policy.py` 3/3, `test_plasma_panel_native.py` 4/4, `test_kde_config_bridge.py`
  21/21, `test_breezebars.py` 4/4 y `test_bwm_decorator.py` 15/15.
* **Pendiente:** comprobación visual en vivo de Alt+Tab real, menús contextuales, KRunner y un tema
  global de terceros; e instalar el plugin candidato de §331 + `bwm-decorator` y reiniciar sesión
  cuando proceda.

### 334. Breeze R6, despliegue atómico de `breezebars` y `bwm-decorator` (2026-11-21)

* **Petición:** desplegar el candidato de R6 (`make install` + `decorator.py build` + retirar
  `no_shadow` para la próxima sesión).
* **Hecho:**
  * `make -C src/breezebars clean && make -C src/breezebars -j$(nproc) && make -C src/breezebars install`:
    instalado atómicamente en `config/hypr/plugins/breezebars.so` con `-fno-gnu-unique` y **0**
    símbolos `UNIQUE`.
  * `python3 config/hypr/skins/plasma/scripts/decorator.py build`: instalado atómicamente en
    `~/.local/share/bwm/bin/bwm-decorator` (supervisor en marcha sin interrupciones).
  * `config/hypr/skins/plasma/hypr/rules.lua`: `breeze-float-all` mueve `no_shadow = true` al
    bloque del plugin anterior (`not hl.plugin.breezebars.blur_on_request`), de modo que la sesión
    actual conserva ambos vetos hasta reiniciar y la próxima sesión activa sombras KDE y desenfoque
    bajo demanda automáticamente; `breeze-no-border` mantiene siempre `no_shadow = true`.
  * `tests/test_plasma_shadow_policy.py`: verifica ambos casos (`no_shadow` con plugin anterior y
    retirado con plugin R6).
* **Comprobado (post-reinicio, con los binarios R6 cargados):**
  * `hyprctl configerrors` vacío, `hl.plugin.breezebars.blur_on_request` presente,
    `breezebars-shadows` v2 activo (`shm: true`, XWayland `:0`), `breezebars-csd` correcto y
    `bwm-decorator` escuchando; `test_plasma_shadow_policy.py` 3/3.
  * Sombras KDE medidas sobre fondo `#dcdcdc` en ventana SSD real (`kind: kde`): 0 px de hueco y
    contorno de 1 px (`143/255`) en los 4 lados, degradado arriba 34 px / abajo 56 px / izquierda
    46 px / derecha 44 px y 4 esquinas continuas (19/18/30/29 px). Ventana `bwm-no-border`: 0 px
    de sombra.
  * `blur_on_request` + `SquareTop` sobre tablero en ventana translúcida: sin petición, contraste
    120 en cuerpo y franja superior; con petición, contraste 8 en cuerpo y 6 en franja superior.
  * `bwm-plasma-osd` y `quickshell:plasmaMenu` verificados en vivo sin errores QML; capturas
    borradas y foco/workspaces intactos.
* **Estado R6:** desplegado y verificado en la sesión diaria. Listo para `git push` o pasar a R7.

### 335. Breeze R7, iteración 1: animaciones predeterminadas de KWin 6.7.5 y `AnimationDurationFactor` (2026-11-21)

* **Petición:** `git push` de R6 y continuar con R7 (`docs/BREEZE_PLAN_V2.md`).
* **Hecho:**
  * `git push origin main` (`5cadd75..43cffbd`).
  * Medición empírica contra `libhyprutils.so`: `speed = 2.0` → 50 % a 100 ms (200 ms), `speed = 4.0`
    → 25 % a 100 ms (400 ms); `SSpringCurve{300, 2√300·1.1, 1}` coincide con `KWin::SpringMotion(300, 1.1)`
    (`t99 = 465 ms`). Corregido el bug previo de `kwin.lua` que dividía `speed / factor` (al revés).
  * `config/hypr/skins/plasma/hypr/animations.lua` consolidado como fuente única de verdad (eliminado
    el bloque duplicado de `kwin.lua` y todas las curvas `md3_*` y `popin 60%`): `scale` 200 ms
    `popin 80%` (`kwin_out_cubic`/`kwin_in_cubic`), `maximize` 250 ms (`windowsMove`), `slidingpopups`
    200 ms, `fadingpopups` 150 ms `kwin_linear` / 600 ms `kwin_out_quart`, `slide` con curva nativa
    `spring = "kwin_slide"` (`stiffness = 300/factor`, `dampening = 2√k·1.1`, `mass = 1`), y Magic
    (`specialWorkspace*`) 250 ms `kwin_out_cubic` `slidevert`.
  * `config/hypr/skins/plasma/scripts/kde-config-bridge.py`: exporta `scaleEnabled`, `scaleDuration`,
    `scaleIn`, `scaleOut`, `maximizeEnabled`, `slideEnabled`, `fadingPopupsEnabled` y
    `slidingPopupsEnabled`.
  * `config/quickshell/ii/modules/plasma/skinPicker/PickerWindow.qml`: 140/160 ms fijos →
    `Kirigami.Units.shortDuration`.
  * Documentado en `docs/BREEZE_R7_RESULTS.md`.
* **Comprobado:** `hyprctl reload` sin errores, `hyprctl animations` con `spring:kwin_slide` y
  curvas `kwin_*` activas en la sesión real, `tests/test_kde_config_bridge.py` 22/22 y
  `tests/test_plasma_shadow_policy.py` 3/3.
* **Pendiente:** comparación temporal por fotogramas frente a Plasma 6.7.5, evaluar `squash` /
  minimizado hacia tarea y página de efectos habilitados en Preferencias (sólo los soportados).

### 336. Breeze R7, iteración 2: preferencias de efectos y KCM nativo (2026-11-21)

* **Petición:** continuar donde lo dejó Gemini, con la página de Efectos de escritorio.
* **Hecho:** `native-settings.py effects` comparte el contrato R3 con la página activa
  `DesktopEffects.qml`/`EffectsStore.qml` y el nuevo `kcm_bwm_effects`. Once controles: seis
  interruptores (`blur`, `scale`, `maximize`, `slide`, `fadingpopups`, `slidingpopups`), intensidad,
  duración/escalas y factor global. Claves KDE reales, validación de lote/revisión, escritura
  conservadora/notificación, reconciliación y lectura posterior. Default nativo de escala
  `Duration=0` conservado como «automático», distinto del 200 ms efectivo.
* **Interfaz:** Aplicar/Restablecer/Predeterminados; defaults sólo en esquemas que los declaran.
  Factor con cuatro decimales en QWidget. `ModuleView` espera guardado asíncrono antes de navegar
  y conserva borrador/página tras error; `plasmaSettings.qml` protege también el cierre pendiente.
  Alias `effects`/`kcm_kwin_effects`/`kcm_bwm_effects`/`kcm_animations`; el lanzador diario no cambia.
* **Capacidades:** seis adaptadores con límites en `settings-capabilities.json`; no se expone
  ruido/saturación, minimizado hacia tarea ni catálogo KWin completo. Capas de `slidingpopups`
  usan todavía `fade`, maximizar usa `windowsMove` sin cross-fade y popups no tienen clasificación
  individual KWin. No se cambian curvas ni otras skins. Sin nuevas dependencias.
* **Comprobado:** R7 8/8 (QML offscreen, backend real con IPC sustituido en XDG temporal,
  guardar/releer/defaults/restablecer/error y navegación), R3 10/10, puente KDE 22/22, política de
  sombras 3/3, catálogo 3/3 y CTest 3/3. Carga Wayland de effects/alias/behavior en `qs -p` aparte
  en workspace 9 sin foco inicial; regla retirada con reload y configerrors vacío. Lectura real
  del backend: once controles. Instalación KCM atómica con `cmake --install`; SHA-256 del módulo
  instalado igual al build y `settings-native.sh --list` lo descubre.
* **Límites:** sin guardar valores de efectos del usuario en las pruebas ni reiniciar shell,
  compositor o sesión. Comparación temporal, geometría de capas, `kwin_out_quart`, `squash` y
  cross-fade siguen pendientes; R7 abierta. Informe `docs/BREEZE_R7_RESULTS.md`. Sin commit/push.
  Los dos config*.json ya estaban modificados al empezar y se conservaron.

### 337. Breeze R7, iteración 3: muestreo temporal real y corrección de OutQuart (2026-11-21)

* **Petición:** continuar tras la página de efectos, con la comparación temporal pendiente.
* **Hecho:** `tests/r7_animation_client.cpp` y `src/breezebars/check-r7-animations.py`: escena Qt
  idéntica sin decoración (300×200 en 800×600), clientes con raíces/bus privados y comprobación
  del peer compositor por PID/UID; Hyprland anidado en salida temporal y KWin virtual. Mismo
  animations.lua de producción, sin cargar plugins. Screencopy SHM persistente con tiempo
  ready comprobado; KWin ScreenShot2 con bracket de petición/respuesta y punto medio. Cadencia
  de muestreo no equivale a FPS presentados; duración y fase ajustadas por separado.
* **Comprobado:** 2.719 muestras, KWin 6.7.5 / Hyprland 0.56.2 × factores 1/2/0: abrir, maximizar,
  restaurar, cerrar y cerrar tras 50 ms de apertura. Factor 0 sin opacidad intermedia observada.
  Maximizado/restauración BWM ~249/499–501 ms; KWin ~262–264/526–535 ms bajo esta captura virtual.
  Tolerancia temporal declarada ~33,3 ms (dos intervalos), sin prometer equivalencia exacta.
* **Diferencias:** escala/alfa del mismo frame, tolerancia 3 px: KWin ≤1,41 px, BWM hasta 10,56 px.
  Cierre durante apertura: KWin vuelve a opacidad/escala completas, BWM continúa el estado parcial
  (primeros 30 ms: alfa máxima 0,242/0,078 con factores 1/2, frente a 1 en KWin). No se falsea
  igualdad cambiando speed para compensar planificación. Capturas/JSON en
  `docs/BREEZE_R7_ANIMATION_RESULTS.json` y `docs/BREEZE_R7_OPEN_FRAMES.png`.
* **Corregido:** Bézier OutQuart `(0.25,1)/(0.5,1)` tenía error matemático 0,00561944; nueva
  `(0.258146,1)/(0.488205,1)` ~0,003167, cota entre muestras <0,003396 <1/255. Sigue siendo
  aproximación, sin certificar renderer de popups ni interpolación interna de libhyprutils.
  `hyprctl reload`/configerrors vacío en diario. Sin tocar otras skins ni valores KDE del usuario.
* **Pruebas:** nuevas numéricas/análisis 3/3 (incluye cota de derivada y cuantización), puente
  KDE 22/22, política de sombras 3/3, efectos R7 8/8 QML incluido y adaptadores R3 10/10.
  Sin cambios C++ de KCM, por lo que no se repitió CTest. Sin nuevas dependencias de escritorio.
* **Sesión:** matriz final sólo difería en puntero tras restaurar foco; foco/PID, plugins,
  workspaces, salidas físicas y reservas iguales. Restauración adicional de puntero después
  del foco; ensayo posterior Hyprland/factor 0, 404 frames, sesión íntegra. No extrapolar ese
  resultado retrospectivamente a la matriz. Sin procesos/salidas residuales ni reinicio diario.
* **Pendiente:** sincronización/cancelación con solución de compositor aislada; muelle y gestos
  de escritorios, popups/desplazamiento, minimizado hacia tarea, cross-fade, foco/sombra y QML
  de las interfaces. Informe `docs/BREEZE_R7_RESULTS.md`; no se certifica Plasma completo ni
  coste/FPS diarios. Sin commit/push. Se conservaron todos los cambios de §336 y los generados
  ajenos (`config*.json`, `persistent_rules.*`).


### 338. Breeze R7, iteración 4: dim inicial y cierre durante entrada (2026-11-21)

* **Rectificación de §337:** `mapWindow` de Hyprland 0.56.2 aplica `dim_strength` al inicio
  incluso con `dim_inactive=false`; contraste RGB bajo dim no equivale a alfa. El arnés anterior
  heredaba 0,5 frente a 0,05 de BWM. No demuestra por sí solo un fallo de relojes de animación.
* **Hecho:** Breeze `fadeDim=false` (recarga diaria verificada). `KWinScale.cpp` sigue entradas
  por referencia débil/PID, monitor/workspace y objetivos; restaura escala/alfa completas sólo
  al cerrar durante la entrada, antes del snapshot nativo. No reemplaza relojes/callbacks ni
  escribe geometría por frame. Reglas propias, no_anim, efectos off, resize/fullscreen,
  cambio de workspace/monitor y reload conservan su autoridad. Documentación AGENTS/CLAUDE igual.
* **Comprobado:** matriz final 2.701 frames sin marco y 1.401 con KDecoration, KWin 6.7.5 /
  Hyprland 0.56.2. Cierre precoz alcanza alfa 1 en ambos. Ocho guardas sin reset indebido ni
  entradas cerradas retenidas. 46/46 pruebas (numéricas, efectos/QML, R3, puente y sombras).
  Plugin completo `-fno-gnu-unique`, sin UNIQUE, cargado sólo en compositores aislados.
* **Límites:** máximo BWM factor 2 sin marco 3,0625 px > tolerancia conservada 3 px; tres
  ajustes temporales fuera de los márgenes declarados. Temporizador pedido 5 ms mide realmente
  15,031529 ms con un render intermedio: no afirmar cierre antes del primer render. Matrices y
  ensayo corto conservan sesión; guarda reload sólo difiere en cursor. Sin certificar paridad,
  placement, coste/FPS diario ni todo Plasma. Evidencias `docs/BREEZE_R7_SCALE_*.json/png`.
* **Despliegue:** `make install` atómico; SHA-256 del candidato/archivo diario
  `103fab72be07684be362d6124705e8d346cf9b716a3e63e0473ec09e928a383d`.
  El plugin antiguo sigue cargado (`breezebars-scale`: unknown request). Nuevo C++ sólo tras
  salir/entrar; no se hizo hot unload/load ni logout/reinicio de shell/compositor. Lua sí activa.
* **Pendiente:** validar próximo inicio diario, residuos temporales, slide/gestos, popups,
  minimizado hacia tarea, cross-fade, foco/sombras y QML de interfaces. R7 abierta. Sin nuevas
  dependencias, commit ni push. Cambios anteriores/config*.json/persistent_rules.* conservados.


### 339. Steam (Adwaita-for-Steam): restaurar barra inferior y botón «Añadir un producto» (2026-11-22)

* **Petición:** el usuario planteó quitar la personalización de Steam porque no veía la opción
  de agregar un juego con clave; al revisar `~/.local/share/steam-adwaita/adwaita/css/main/headerbar/`
  (`headerbar.css` y `menu.css`) se vio que Adwaita-for-Steam oculta `div._2foCkpRXhqq0UGVE50BWqj`
  («Añadir un producto») y colapsa la barra inferior `div._3vCzSrrXZzZjVJFZNg9SGu` a altura 0,
  replegando «Productos → Activar un producto» dentro del botón hamburguesa. El usuario eligió
  conservar Adwaita-for-Steam y volver a mostrar la barra inferior / botón por CSS.
* **Hecho:** nuevo `config/hypr/scripts/steam-custom.css` con mayor especificidad que
  `headerbar.css` (`html body.DesktopUI ...`, dado que `gamerecording.css` importa `main.min.css`
  sin `config.css`): usa `display: contents` en `div._1_yS5UP7el0aN4vntx3dx` para mantener el
  banner de actualización en `order: 2` y colocar `div._3vCzSrrXZzZjVJFZNg9SGu` en `order: 4`
  (36 px de alto, fondo `--adw-headerbar-bg`, borde `--adw-headerbar-shade`), restaurando
  `div._2foCkpRXhqq0UGVE50BWqj` con el estilo y radios/fuentes del tema.
* **Despliegue:** `config/hypr/scripts/steam-theme.sh` genera `~/.local/state/bwm/steam/custom.css`
  y pasa `--custom-css` en todas las skins (en `retro` añade al final la fuente monoespaciada del
  sistema). Documentación actualizada en `docs/STREMIO_THEMING.md`, `AGENTS.md`, `CLAUDE.md` y
  §2.2.
* **Comprobado:** `steam-theme.sh` ejecutado sobre la sesión en `plasma`: `install.log` sin errores,
  `~/.local/share/Steam/steamui/adwaita/{config,custom}.css` con la importación y reglas nuevas, y
  Steam reiniciado en el workspace 2 (`[373, 837]`, `1728×1229`); pruebas `tests/test_steam_restart.py`
  (6/6 OK). **Pendiente:** confirmación visual del usuario en Steam al pasar al workspace 2.

### 340. Breeze R7, iteración 5: validación en vivo de `breezebars-scale`, muelle/reversión de `slide`, clasificación de capas y QML (2026-11-22)

* **Petición:** continuar con R7 tras las iteraciones 2–4 y el reinicio de sesión.
* **Hecho:**
  * Validado en vivo `hyprctl -j breezebars-scale` en la sesión diaria (`version: 1, enabled: true`):
    al cerrar una ventana de prueba en el workspace 10 a los ~20 ms de mapearse, `resetOnClose`
    pasa de `0` a `1` y `tracked` vuelve a `0`.
  * Comparado `KWin::SpringMotion::integrate` (RK4 a 100 Hz con `.dp = state.velocity`, que añade
    un retardo Euler de ~`dt/2 = 5 ms` en posición) frente a la EDO continua de `SSpringCurve`
    (`stiffness = 300/factor, dampening = 2√k·1.1, mass = 1`) en ida y reversión a mitad de trayecto
    (120 ms) para factores 0,5/1/2 (`test_r7_animation_measurement.py`).
  * `config/hypr/skins/plasma/hypr/rules.lua`: `breeze-static-layers` (`no_anim = true` en
    `quickshell:(plasmaDesktop|plasmaOutline)`) evita que la guía de snapping tarde 600 ms en
    desvanecerse al soltar una ventana.
  * `config/hypr/skins/plasma/hypr/animations.lua`: `breeze-sliding-layers` aplica
    `animation = "slide"` a `quickshell:plasmaNotifications` y `krunner` cuando
    `slidingPopupsEnabled` está activo (con caída a `"fade"` o `no_anim = true`).
  * `config/quickshell/ii/modules/plasma/theme/PlasmaTheme.qml`,
    `config/quickshell/ii/modules/plasma/panel/Panel.qml`,
    `config/quickshell/ii/modules/plasma/kickoff/KickoffWindow.qml`,
    `config/quickshell/ii/modules/plasma/tray/TrayPopup.qml` y
    `config/hypr/skins/plasma/scripts/settings-capabilities.json`: `PlasmaTheme.slidingPopups` lee
    en vivo `kwinrc [Plugins] slidingpopupsEnabled` y `AnimationDurationFactor > 0`; activa las
    transiciones de 200 ms `OutCubic` (`Kirigami.Units.longDuration`) en el cambio flotante ↔
    acoplado del panel y el deslizamiento de entrada `Translate` desde el borde del panel en
    Kickoff y en el popup de la bandeja. Actualizado `r7_contract.limitations`.
* **Comprobado:** `hyprctl reload` y `hyprctl configerrors` vacío; **71/71** pruebas en verde
  (`test_r7_animation_measurement` 4/4, `test_r7_effects` 8/8, `test_r3_native_settings` 10/10,
  `test_kde_config_bridge` 22/22, `test_plasma_shadow_policy` 3/3, `test_plasma_panel_native` 4/4,
  `test_plasma_tray` 20/20).

### 341. Breeze R8, lote 1: cierre de avisos QML reales, portapapeles y vista previa de tareas (2026-11-22)

* **Petición:** continuar con R8 (`docs/BREEZE_PLAN_V2.md`).
* **Hecho:**
  * Cerrados los 8 avisos `Unable to assign [undefined]` registrados en `qs -c ii log` sobre
    `modules/plasma/*`: `panel/Task.qml` (`isActive`/`isMinimized`), `theme/ToolTipArea.qml`
    (`root.QsWindow?.window`, `HoverHandler.enabled`), `tray/SystemTray.qml`
    (`QsWindow?.window`, `expander?.visible`, `Math.max(1, lanes)`) y `tray/TrayPopup.qml`
    (`anchorItem?.QsWindow?.window`).
  * `applets/ClipboardApplet.qml`: botón «Clear History» (`edit-clear-history` → `Cliphist.wipe()`)
    en la cabecera, foco en el buscador al abrir y `Return`/`Enter` para copiar la primera
    coincidencia.
  * `panel/TaskToolTip.qml`: cabecera con icono de la aplicación, título elidido y botón
    `window-close` por ventana (como `ToolTipInstance.qml` de Plasma 6.7.5).
  * Informe `docs/BREEZE_R8_RESULTS.md`.
* **Comprobado:** `tests/test_plasma_task_input.py` 1/1, `tests/test_plasma_panel_native.py` 4/4,
  `tests/test_plasma_tray.py` 20/20; reinicio de mantenimiento del shell con **0 avisos** en
  `modules/plasma/*`.
* **Pendiente:** P2 aplazados en `docs/BREEZE_R8_RESULTS.md` o pasar a R9 (aceptación final y
  regresión entre las tres skins).

### 342. Breeze R8, lote 2: zonas horarias del reloj y del calendario (2026-11-22)

* **Petición:** continuar donde lo dejó Gemini (R8) y hacer commit y push.
* **Rectificación del lote 1:** el registro del shell real no tiene avisos de `modules/plasma/*` al
  arrancar; los 72 «Unable to assign [undefined]» aparecen sólo entre «Reloading configuration…» y la
  nueva generación (destrucción de la anterior). El «0 avisos» de §341 vale para el arranque.
* **Hecho:** `panel/DigitalClock.qml` porta el `onWheel` de plasma-workspace 6.7.5 (adaptado: emite
  `timeZoneSelected`; `PanelContent.qml` guarda `lastSelectedTimezone` en `bar.plasma.clock`).
  `applets/calendar/CalendarApplet.qml` lee `selectedTimeZones` con la deduplicación y orden
  originales (`TimeZoneUtils`), `currentTimeZone`, `displayTimezoneFormat`, `formatTime` y
  `formatOffset` de `digital-clock/main.qml`.
* **Comprobado:** panel nativo 6/6 y bandeja 21/21 con `BWM_RUN_QML_TESTS=1` (tres pruebas nuevas);
  recarga en caliente sin errores nuevos. **No probado:** rueda física en el panel diario; no hay
  página para editar la lista de zonas. Detalle en `docs/BREEZE_R8_RESULTS.md`.

### 343. Breeze R9: aceptación final y regresión de las tres skins (2026-11-22)

* **Petición:** continuar con R9 (`docs/BREEZE_PLAN_V2.md`).
* **Comprobado en la sesión diaria real:**
  * `config/hypr/plugins/breezebars.so` (SHA-256 `103fab72be07684be362d6124705e8d346cf9b716a3e63e0473ec09e928a383d`)
    cargado con `breezebars-shadows` v2 (`shm: true`, XWayland `:0`), `breezebars-scale` v1
    (`enabled: true`, `resetOnClose: 1`, `tracked: 0`) y `blur_on_request` OK.
  * `bwm-decorator` instalado y escuchando; `settings-native.sh --list` descubre los 10 KCM BWM
    (`kcm_bwm_*`) y restringe `kcm_kwin_effects`; dueño único de `qs -c ii` (1),
    `polkit-kde-authentication-agent-1` (1) y `kde-config-bridge.py watch` (1);
    `hyprctl configerrors` vacío; `bwm-requirements.py check --skin plasma` todo listo.
* **Suite de regresión ejecutada (364 pruebas, 0 fallos):**
  * 293/293 Python multi-skin (`default`, `retro`, `plasma`, R1/Magic Alt+S, R3, R6, R7, Steam, común).
  * 68/68 QML + C++ Breeze (`test_r7_effects`, `test_plasma_interfaces`, `test_plasma_menus_ui`,
    `test_plasma_panel_native`, `test_plasma_task_input`, `test_plasma_tray`, `test_breezebars`,
    `test_bwm_decorator`).
  * 3/3 CTest (`src/bwm-systemsettings/build`).
* **Entregado:** `docs/BREEZE_R9_RESULTS.md` con tabla de estado por fase (R0–R8) y límites
  explícitos (R4–R5 experimental, contención de miniaturas en `TaskToolTip`, pruebas físicas de
  bloqueo/PAM y energía reservadas al usuario).

### 344. Breeze R8, lote 3: miniaturas en vivo con guardas y controles MPRIS en `TaskToolTip` (2026-11-22)

* **Petición:** «continua».
* **Hecho:**
  * Verificado `hyprctl -j version` → `"bwmScreenshareMonitorGuard": {"version": 1, "pid": 3191}` en
    la sesión diaria, levantando la contención temporal de `docs/BREEZE_RECOVERY.md` con doble
    defensa en QML (sólo capturar cuando la vista está visible y la ventana no está en
    `special:minimized`/workspace 99).
  * `config/quickshell/ii/modules/plasma/panel/TaskToolTip.qml`: `ScreencopyView` protegido por
    `popup.visible && !card.isMinimized && (card.modelData != null)` con icono 48×48 de respaldo
    para minimizadas, y fila MPRIS (`Quickshell.Services.Mpris`, emparejamiento por
    `desktopEntry`/`dbusName`/`identity`, título de pista y botones `previous`/`togglePlaying`/`next`).
  * `config/quickshell/ii/modules/plasma/switcher/{ThumbnailGrid,ThemedSwitcher,compat/WindowThumbnail}.qml`:
    miniaturas protegidas por visibilidad + exclusión de minimizadas.
  * `tests/test_plasma_task_input.py`: nueva prueba `test_tooltip_thumbnail_guards_and_mpris_controls`.
* **Comprobado:** `test_plasma_task_input` (2/2), `test_plasma_interfaces` (8/8) y
  `test_window_activation` (7/7) = **17/17 OK** (`BWM_RUN_QML_TESTS=1`); recarga en caliente de
  `qs -c ii` sin errores de estos archivos. **Pendiente del usuario:** comprobación visual física
  al pasar el ratón por tareas y pulsar `Alt+Tab` con ventanas reales y un reproductor MPRIS.

### 345. Breeze R8, lote 4: exclusión mutua de capas `Overlay` y máscara al fijar Kickoff (2026-11-22)

* **Contexto:** en una sesión previa con dos monitores aparecieron simultáneamente `plasmaMenu`
  (DP-1) y `plasmaKickoff` (DP-2) en `Layer 3 (Overlay)` con `WlrKeyboardFocus.Exclusive`.
* **Hecho:**
  * `config/quickshell/ii/modules/plasma/kickoff/KickoffWindow.qml`: al abrir cierra `PlasmaMenus`
    y `TrayState`; si está fijado (`!kickoff.hideOnWindowDeactivate`), restringe `mask` a `frame` y
    usa `WlrKeyboardFocus.OnDemand` para no capturar clics fuera; fondo de cierre con
    `acceptedButtons: Qt.AllButtons` en `onPressed`.
  * `config/quickshell/ii/modules/plasma/menus/MenuHost.qml`: al abrir cierra `plasmaKickoffOpen`
    (y `TrayState` salvo `kind === "tray"`); al expandirse `TrayState` cierra menús no-tray.
* **Comprobado:** `test_plasma_menus_ui.py` **5/5 OK** (`BWM_RUN_QML_TESTS=1`) y recarga en
  caliente de `qs -c ii` sin avisos ni errores nuevos. Detalle en `docs/BREEZE_R8_RESULTS.md`.

### 346. Breeze R2–R3: `systemsettings` real como lanzador predeterminado de Preferencias (2026-11-22)

* **Petición:** «continua».
* **Hecho:**
  * `config/hypr/skins/plasma/scripts/settings-native.sh` (`chmod +x`): añadidos los alias cortos
    de BWM (`display`, `windowbehavior`, `workspaces`, `keybinds`, `cursor`, `idle`, `nightlight`,
    `defaultapps`, `autostart`, `sound`, `network`, `globaltheme`, `colors`, `plasmastyle`,
    `decorations`, `icons`, `appstyle`, `fonts`, `behavior`) hacia sus KCM reales (`kcm_bwm_*` y
    KDE).
  * `config/hypr/scripts/open-settings.sh`: en Breeze (`plasma`) lanza ahora `settings-native.sh`
    cuando están instalados `systemsettings` y `kcm_bwm_windows.so` en `plasma/kcms/systemsettings/`;
    enruta páginas sólo-BWM (`background`, `bar`, `services`, `general`, `style`, `about`,
    `windowrules`), `BWM_SETTINGS_HOST=legacy` o instalaciones sin `systemsettings` a
    `plasmaSettings.qml`.
  * `tests/test_r3_native_settings.py`: nueva prueba
    `test_open_settings_routes_plasma_to_native_with_aliases_and_fallback`.
* **Comprobado:** `test_r3_native_settings` (11/11) + `test_r7_effects` (8/8) = **19/19 OK**;
  `open-settings.sh --list` en la sesión Wayland real descubre los 10 `kcm_bwm_*` y
  `kcm_kwindecoration`. **Pendiente del usuario:** abrir Preferencias con `Super+I` y probar
  visualmente los módulos en su uso diario.

### 349. Breeze R8, lote 5: insignias y progreso Unity LauncherEntry en las tareas (2026-11-24)

* **Petición:** continuar el plan Breeze v2 (R0–R9 ya cerrados; quedan P2).
* **Hecho:** `skins/plasma/scripts/launcher-entries.py` escucha `com.canonical.Unity.LauncherEntry.Update`
  y sanea como `smartlauncherbackend.cpp` 6.7.5; anuncia `com.canonical.Unity` sin desplazar a otro
  dueño y olvida la entrada al salir el emisor; sale con su padre (`PR_SET_PDEATHSIG`).
  `panel/LauncherEntries.qml`/`.js` (un `Process`, sólo en Breeze), `panel/TaskBadgeOverlay.qml`
  (el original con `BadgeEffect`) y en `Task.qml` la barra de `TaskProgressOverlay.qml` y `urgent`
  como atención. Insignias ocultas con No molestar.
* **Comprobado:** pruebas nuevas (bus D-Bus privado y QML de insignia/progreso/No molestar); panel,
  bandeja y skins 40/40. En sesión, un emisor de prueba mostró insignia «5» y 60 % en Signal y se
  retiraron al salir. Una primera prueba dejó un listener huérfano del shell anterior (causa del
  `PR_SET_PDEATHSIG`); se mató por PID. El reinicio de mantenimiento movió el foco (devuelto a mano).
* **No probado:** apps reales que emitan el protocolo. Detalle en `docs/BREEZE_R8_RESULTS.md`.

### 350. Breeze R8, lote 6: imágenes en el portapapeles (2026-11-24)

* **Hecho:** `applets/clipboard/ImageItemDelegate.qml` (el original de Klipper 6.7.5) para las
  entradas de imagen de cliphist: decodificadas una vez a `$XDG_RUNTIME_DIR/bwm-plasma-clipboard`
  (0700, borradas con la fila); `ClipboardApplet.qml` elige texto o imagen por entrada.
* **Comprobado:** prueba QML con un `cliphist` falso (imagen 40×20, copia, carpeta 0700); panel,
  bandeja y skins 34/34. **Pendiente:** verlo en el panel diario (archivo nuevo: hace falta reinicio
  de mantenimiento del shell o volver a iniciar sesión). Sin edición/QR/URL.

### 351. Breeze R8, lote 7: avisos de Plasma como servidor en Breeze y respuesta en línea (2026-11-24)

* **Encontrado:** en Breeze, swaync (arrancado por autostart en todas las skins menos Retro) tenía
  `org.freedesktop.Notifications`: los avisos, el historial y las acciones de Plasma portados en F5
  nunca se usaban. El usuario eligió los avisos de Plasma.
* **Hecho:** campo `notifications` en `skin.json` (`swaync` en default, `shell` en Breeze y Retro) y
  `bwm_skins.notifications()`; el gestor (6.1) y `autostart.sh` cierran o arrancan swaync según él.
  `services/Notifications.qml` crea su servidor en Breeze, y en default sólo si swaync no está
  instalado. Respuesta en línea: `inlineReplySupported` sólo en Breeze (las otras skins conservan
  las acciones «Responder» de las apps), `ActionContainer.qml` original y `NotificationReplyField.qml`,
  `Notifications.sendInlineReply()`; los toasts piden teclado sólo mientras se escribe.
* **Comprobado:** prueba QML (botón Reply, campo enfocado, texto enviado por el servidor); 45 pruebas
  de bandeja, skins, sesión y cambio de skin. En sesión: `set plasma` cerró swaync, Quickshell tomó el
  nombre (anuncia `inline-reply`) y una notificación de prueba salió como toast de Plasma con Reply.
  **No probado:** escribir una respuesta real con el teclado en el toast ni con una app real.

### 352. Breeze R8, lote 8: código QR y edición en el portapapeles (2026-11-24)

* **Hecho:** `DelegateToolButtons.qml`, `BarcodePage.qml` y `EditPage.qml` de Klipper 6.7.5 en
  `applets/clipboard` (sin acciones de Klipper ni estrella); `ClipboardApplet.qml` como `StackView`;
  editar copia el texto nuevo y borra la entrada anterior. IPC `plasmaClipboard`. Requisitos
  `prison-qml` y `kquickcontrolsaddons` (instalados).
* **Comprobado:** prueba QML de QR y edición; bandeja, panel y skins 35/35; IPC abre el portapapeles.
* **Incidencia:** una primera versión escribió «Edited entry» en el portapapeles real durante la
  prueba (`a?.()??b`); entrada borrada de cliphist, portapapeles devuelto y condición corregida.
* **No probado:** los botones con el ratón en el panel diario.

