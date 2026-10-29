# BWM (Better Window Manager) — traspaso para cualquier asistente (Codex, Claude, Gemini…)

Este archivo es autocontenido: léelo entero antes de tocar nada. El detalle está en `BWM_CONTEXT.md`
(mismo directorio): **§2 = estado actual por áreas**, §3 = historial numerado
(§3.N), §4 = árbol del repo, §5 = cambios hechos fuera del repo, §7 = comandos.
Si tu herramienta no expande `@archivo`, abre `BWM_CONTEXT.md` a mano.

`AGENTS.md` y `CLAUDE.md` contienen las mismas reglas y se mantienen sincronizados. Los tres
archivos de contexto están versionados; no incluyas contraseñas, tokens ni volcados de datos privados.

@BWM_CONTEXT.md

---

## Propósito (lo más importante)

**BWM es un gestor de ventanas que trata de encapsular todos los gestores de ventanas y escritorios
como skins.** Cada skin reproduce otro escritorio (barra, menús, paneles, atajos, decoraciones y
temas) sobre Hyprland + Quickshell, y el sistema entero la sigue. **Finalidad: compatibilidad con
las mejoras de aspecto de cada original**: en la skin KDE Plasma un tema de Plasma bajado de
internet debe aplicarse y funcionar; en Retro, un tema o plugin de Omarchy. BWM tiene pocas
interfaces propias (la bienvenida, Ajustes); casi todo es la interfaz del escritorio original.
**Pocas skins, fáciles y con lo mismo**: las tres actuales hacen lo esencial, se aprenden enseguida y
comparten casi las mismas funciones básicas; lo muy importante y propio de un escritorio se incluye en
su skin, la complejidad extra no se ofrece. **Un único compositor**: portar a Hyprland escritorios que no
corren sobre él (KDE Plasma en curso). Compatibilidad estimada y qué se conserva entre skins: README y
`docs/SKINS.md`.

## 0. Vocabulario

- **Estilo** (*skin*): Default (Material You), Retro (Omarchy), KDE Plasma (Breeze Dark).
- **Tema**: lo de *dentro* de un estilo (temas de Omarchy incluidos/instalados en Retro o su paleta dinámica).
- Los nombres internos no cambian (`bwm-theme-manager.py get|set <estilo>`, `theme.lua`, `Appearance.isRetro`,
  `THEME_SPECIFIC_SECTIONS`…). En textos visibles, comentarios y documentación: «estilo/skin».

## 1. Qué es y dónde está

- Escritorio sobre **Hyprland ≥ 0.55 configurado en Lua** (sesión del 2026-10-28: 0.56.2; mira `hyprctl version -j`) + **Quickshell** (QML, config `ii`, derivada de
  end-4/illogical-impulse) en **Gentoo** (systemd), kernel cachyos, GPU **NVIDIA** + iGPU AMD (Ryzen 9 7900).
- Repo: `/mnt/HDD1TB/Projects/hyprland-de` (enlace `~/Projects/hyprland-de`). `~/.config/{hypr,quickshell,
  illogical-impulse,rofi,kitty,matugen,swaync,gtk-3.0,gtk-4.0,xdg-desktop-portal,nvim}` son **enlaces al repo**:
  editar el repo = editar lo que corre.
- Usuario: `sasel` (git `saselandia`). Habla **español**: responde en español.
- Remotos: `git push origin main` sube a GitLab y GitHub a la vez.
- Monitores: LG UltraFine 4K (arriba a la derecha, `1920x0`) y HP X24ih 1080p@144 (`0x1080`, principal).
  **Se identifican por `desc:`**, nunca por `DP-N` (cambian con el orden de arranque de las GPU).

## 2. Reglas que NO se pueden romper

1. **Plugins C++ de Hyprland** (`src/hyprbars`, `src/csd-minimize`): compilar con `-fno-gnu-unique` y desplegar
   SOLO con `make install` (copia temporal + `mv` atómico). Nunca `cp` sobre un `.so` cargado ni
   `hyprctl plugin unload/load` en caliente → SIGBUS, crash, safe mode.
2. **Nunca arrancar Quickshell (`qs -c ii`) dos veces.** Reinicios de mantenimiento con `bwm-theme-manager.py set <estilo-actual> --restart-shell`
   (~10 s, las barras parpadean). Editar un QML del repo recarga en caliente la barra real del usuario: no metas
   cambios temporales de prueba en archivos que esté usando; prueba en un archivo aparte
   (`qs -p ~/.config/quickshell/ii/zz_prueba.qml`) y bórralo. **No se recargan en caliente** (hay que reiniciar):
   lo cargado por `Loader` desde `bar/omarchy/*`, overlays, archivos nuevos de un módulo, y una instancia con
   muchas horas puede dejar de recargar (el log no dice «Reloading configuration»).
3. **Arranque**: `/boot` está en el disco cifrado (LUKS con llave en el initramfs, dracut `--hostonly`).
   **NUNCA `grub-mkconfig`** (la línea `rd.luks…`/`root=` no está en `/etc/default/grub`). Plymouth/SDDM sólo con
   `config/hypr/scripts/install-boot-theme.sh` (copias `.bwm-backup`, conserva los drivers de GPU; `--revert`).
   Incidente 2026-10-23: un initramfs con `amdgpu` cambió los conectores y superpuso los monitores.
4. Campos `hyprbars:*` de `hl.window_rule` (sólo existen con el plugin, estilo Plasma): dentro de
   `if hl.plugin and hl.plugin.hyprbars then … end`, o sale «Your config has errors» en los otros estilos.
5. Puede haber **otra sesión de IA trabajando a la vez**: en los commits añade sólo tus archivos (revisa el
   `git diff` de cada uno). Archivos generados que cambian solos con el estilo/tema/fondo — no los incluyas salvo
   a propósito: `colors.lua`, `retro_colors.lua`, `plasma_colors.lua`, `gtk-3.0/bwm-colors.css`, `gtk-4.0/gtk.css`,
   `config*.json`, `kitty-colors.conf`, `rofi/*.rasi`, `swaync/style.css`, `btop.conf`, `persistent_rules.*`.
6. **Atajos**: `config/hypr/keybinds.json` + `scripts/keybinds-manager.py add|update|purge|reload` (regenera
   `modules/user_binds.lua`; uno añadido sólo al `.lua` se pierde). Fijos (Alt+Tab, Alt+`, Super+Backspace…) en
   el bloque «helpers» de `generate_lua()`. Usa rutas absolutas en `exec` (el PATH de Hyprland no tiene `~/.local/bin`).
7. Acciones con sudo (emerge, install-boot-theme.sh…) las ejecuta el usuario: dale el comando exacto.
8. **Ventanas de Hyprland**: una ventana nueva puede reutilizar la dirección de la anterior (pasó con Spotify):
   distingue una ventana reiniciada por **PID**, no por `address`.
9. Rutas fijas `/home/sasel/...` en muchos scripts: no los pruebes con otro `$HOME`. Capturas con `grim`: pueden
   mostrar contenido privado; recorta a lo necesario y bórralas al terminar. Para probar ventanas sin molestar,
   regla temporal `hyprctl eval 'hl.window_rule({ name = "tmp-…", match = {…}, workspace = "9 silent" })'` y
   `hyprctl reload` después.
10. Commits con la línea de coautoría de tu herramienta. Tras cambios relevantes actualiza `BWM_CONTEXT.md`:
    una sección nueva al final de §3 y, si cambia lo actual, §2 (y aquí, si es una pieza clave o una trampa).
    Mantén `AGENTS.md` y `CLAUDE.md` iguales. Separa lo comprobado de lo pendiente; no afirmes que se
    completó una actualización, reinicio, prueba visual o push sin haberlo verificado. Si el usuario pide
    «commitear todo», incluye también los cambios ajenos y generados tras revisarlos; no los descartes.
11. **Compatibilidad con los temas del original**: al tocar una skin, hazlo de forma que siga aceptando los
    temas/plugins de su escritorio original (formato de Omarchy en Retro, de Plasma en KDE Plasma, de
    matugen/end-4 en Default). Ante la duda, se adapta BWM al formato del original, no al revés. No
    introduzcas formatos de tema propios donde el original ya tiene uno.
12. **Requisitos declarados**: si una skin o el núcleo empieza a usar un programa, módulo QML/Qt, fuente o
    biblioteca nuevos, añádelo a `config/hypr/skins/requirements.json` (catálogo con paquetes por distro) y al
    `requires`/`recommends` de la skin; regenera la tabla de `docs/REQUIREMENTS.md`. El instalador, `bwm check` y
    la bienvenida salen de ahí.

13. **Configuración modular**: cada skin en sus carpetas/módulos propios y lo común en lo común, sin mezclar
    (tabla en `docs/SKINS.md`, «Estructura modular»). Código nuevo de una skin nace en su carpeta; no metas
    condiciones de una skin dentro de un módulo de otra si puede ser un módulo aparte.
14. **Se conserva entre skins** (no lo hagas propio de una skin): red/Bluetooth, cursor, Kelvin de la luz
    nocturna, apps predeterminadas (quizá salvo el gestor de archivos en el futuro), workspaces (los mismos
    1–N y `bar.workspaces.shown`), pantallas y escala, inicio automático, servicios (`bar.weather`…),
    interfaz (logo, vista general, OSD, bloqueo) y General. **Propio de cada skin**: aspecto y fuentes (de la
    skin y su tema), fondo, barra y dock. Mecanismo: `THEME_SPECIFIC_SECTIONS` y
    `SHARED_KEYS_IN_SKIN_SECTIONS` de `bwm-theme-manager.py`. La protección de volumen («earbang») se quitó.

15. **Licencias y procedencia**: conserva los avisos y textos de cada componente de terceros; BWM
    incluye GPL, BSD, MIT, MPL, OFL y otros términos, no se presenta todo como MIT. Documenta origen,
    versión, modificaciones y fuente correspondiente en `THIRD_PARTY_NOTICES.md`; revisa las imágenes,
    marcas y binarios pendientes antes de una release. El instalador conserva los avisos al copiar recursos.

16. **Cambio de skin sin interrupciones**: `bwm_transition.skin_change()` propaga `BWM_SKIN_SWITCH=1`
    a los hooks: no cerrar apps, no recargar Hyprland desde cada hook ni restaurar focos antiguos desde
    tareas separadas. Capturar geometría antes de modificar reglas; usar acciones de flotación explícitas
    (`enable`/`disable`), respetar fullscreen, minimizadas y especiales. Quickshell se actualiza con `bwmSkin.reload`;
    `set <skin> --restart-shell` fuerza sólo su reinicio para mantenimiento. No propagar la variable de
    transición al proceso duradero de Quickshell.

17. **Snapping de Plasma**: el monitor al soltar es el de la previsualización/puntero, no el que
    tenga asignado la ventana al cruzar una unión. Pasarlo por `--monitor desc:… --edge --pid …` a
    `quick-tile.py`; el workspace se asigna antes de fijar geometría (hacerlo después la desplaza).
    Área útil en unidades lógicas con `reserved` real, sin restar un panel fijo de 44 px; incluir la
    barra hyprbars dentro del marco. En Hyprland 0.56 `window.float` usa `enable/disable`, mientras
    `window.fullscreen` usa `set/unset`: las cadenas desconocidas alternan flotación silenciosamente.
18. **La configuración en texto del usuario manda**: `~/.config/bwm/user/*`, `~/.config/omarchy/shell.toml` y
    `~/.config/bwm/extensions/menu.jsonc` son del usuario: no los edites ni los crees por él (sólo `bwm-user-config`
    con su plantilla, si no existen). Todo lo nuevo de BWM debe cargarse antes que ellos para que puedan sobrescribirlo.

## 3. Dónde tocar para…

| Quiero… | Dónde |
| :--- | :--- |
| Crear o cambiar una skin (datos, aspecto, ventanas) | `config/hypr/skins/<id>/skin.json` (plantilla `_template/`, guía `skins/README.md`), cargado por `scripts/bwm_skins.py`; nada de datos de skin en el Python del gestor |
| Requisitos (instalador, `bwm check`, bienvenida) | `config/hypr/skins/requirements.json` + `requires` de cada `skin.json`, `scripts/bwm-requirements.py`; tabla en `docs/REQUIREMENTS.md` |
| Instalador | `install.sh` (sale con los comandos de la distro si falta un requisito) |
| Bienvenida / comando `bwm` | `quickshell/ii/bwmWelcome.qml` (qs -p aparte), `scripts/bwm`, `~/.config/bwm/welcome.json`, `autostart.sh` |
| Cambiar de estilo / ver qué hace al cambiar | `config/hypr/scripts/bwm-theme-manager.py` (`apply_theme`) |
| Algo que sólo cargue en un estilo | `quickshell/ii/panelFamilies/IllogicalImpulseFamily.qml` (`extraCondition`) |
| Colores/temas de Retro y sus apps | `scripts/bwm_omarchy.py` (`apply_retro_palette_colors`), `scripts/bwm_omarchy_apps.py`, `hypr/omarchy/themed/*.tpl` |
| Colores de apps en Default/Plasma | `config/matugen/config.toml` + `templates/` (Plasma los rellena con Breeze en `bwm-theme-manager.py`) |
| GTK 3 / Qt / flatpaks | `scripts/gtk-theme.py`, `scripts/bwm_icons.py` (qt6ct, `kdeglobals`, overrides) |
| Barra Retro y su derecha | `modules/ii/bar/RetroBarContent.qml`, `bar/omarchy/*`, Ajustes → Barra (`BarConfig.qml`) |
| Instalar/elegir temas y plugins | `modules/settings/{PluginsConfig,ThemesConfig}.qml`, `modules/settings/addons/`, `scripts/bwm-addons.py`, `scripts/bwm-plugin.sh`; detalle en `docs/OMARCHY_ADDONS.md` |
| About del menú Retro (Fastfetch) | `scripts/omarchy-shims/omarchy-launch-about`, `hypr/omarchy/about/`, `scripts/bwm-about-data.py`; no confundir con About de Settings |
| About de Ajustes / detección de distro | `modules/settings/About.qml`, `services/SystemInfo.qml` y `SystemInfoData.js` (os-release sin ejecutar shell); enlaces propios de BWM |
| Entrada del menú de Retro | `config/hypr/omarchy/bwm-menu.jsonc` (`when`/`checked` en bash) |
| Configuración del usuario en texto (manda sobre BWM) | `scripts/bwm-user-config` (`list/edit/apply/path`), `~/.config/bwm/user/{hyprland.lua,shell.jsonc}`, `~/.config/omarchy/shell.toml`, `~/.config/bwm/extensions/menu.jsonc`; `hyprland.lua` la carga al final con `pcall`; `bwm-theme-manager.py apply-user` y al cambiar de skin |
| Configuración integrada de Retro | `modules/ii/omarchyMenu/omarchy/settings/` (catálogo, controlador y editores dentro de `Menu.qml`); `open-settings.sh [página]` → IPC `omarchyMenu.settings`. `retroSettings.qml` sólo redirige, sin ventana propia |
| Un comando `omarchy-*` que falta | `config/hypr/scripts/omarchy-shims/` (+ enlace en `~/.local/bin`, `bwm-plugin.sh catalog`) |
| Reglas de ventana / juegos | `hypr/modules/rules.lua`, `scripts/window-guard.py` |
| Atajos | `keybinds.json` vía `keybinds-manager.py` |
| Temas web de Stremio / barra de Steam | `scripts/stremio-theme.py`, `scripts/stremio-theme.cjs`, `scripts/steam-theme.sh`, `hypr/omarchy/overlays/steam.css`; alcance en `docs/STREMIO_THEMING.md` |
| Salvapantallas e inhibición por multimedia | `modules/ii/screensaver/ScreensaverIdle.qml`, `scripts/launch-screensaver.sh` |
| Actualizaciones de Gentoo / Flatpak | `BWM_CONTEXT.md` §2.7; shims `omarchy-update` y `omarchy-update-available` |
| Reiniciar una app conservando sus ventanas | `bwm_omarchy.restart_app()` (Firefox, Vesktop, Steam, Stremio) + `scripts/bwm_windows.py` |
| Dónde quedan las ventanas al cambiar de skin | `scripts/bwm_windows.py` (`float_in_place`, `traditional_box`, `restored_box`, `hold_new_windows`), `bwm_transition.py`, `sync_floating_windows`; familia de la skin en `skins/<id>.json` → `windowing` (`tiling`/`stacking`) |

## 4. Estilos y piezas clave

- **Gestor**: `bwm-theme-manager.py get|set|toggle|list`. Perfil de Quickshell por estilo en
  `illogical-impulse/config-<estilo>.json` (secciones propias: appearance, background, bar, dock, panelFamily,
  waffles; dentro de `bar` se comparten `workspaces.shown`, `weather` y `topLeftIcon`); el resto se comparte.
- **Default**: Material You con matugen desde el fondo (`scripts/set-wallpaper.sh`).
- **Plasma** (`quickshell/ii/modules/ii/plasma*`, comunes en `plasmaCommon/`: `Breeze.qml`, `BreezePopupWindow` —se
  desliza con un offset y respeta `bar.bottom`, `passBarClicks`—, `BreezeSlider`…): panel flotante, Kickoff
  (Super), applets Bluetooth/red/audio/calendario/notificaciones, menú de tareas con miniaturas y «peek»,
  selector «Estilo global» (Alt+T), Alt+Tab de KDE (el foco cambia al soltar Alt), OSD Breeze, hyprbars con
  barras Breeze y snapping. Redondeo 12 px.
- **Retro = Omarchy 4** (repo `basecamp/omarchy`, rama `quattro`, MIT; investigación en `docs/OMARCHY_INVESTIGACION.md`):
  - Librerías de Omarchy en `quickshell/ii/Commons` y `Ui` (`qs.Commons`, `qs.Ui`; cambios BWM en `Commons/README.md`):
    `Color.qml` vigila `~/.local/state/bwm/omarchy/{colors,shell}.toml`, `I18n.qml` con cadenas incluidas (en, es-MX),
    `Style.qml` con `bwmScale`.
  - Barra `RetroBarContent.qml` (clon de la de Omarchy) con widgets fijos de `bar/omarchy/` y plugins
    (`omarchy-plugins/`, `~/.config/bwm/omarchy-plugins.json`, `bwm-plugin.sh`); cada widget de la derecha se oculta
    en Ajustes → Barra (`disabled`/`shown`). Idioma del shell de Omarchy en Ajustes → Barra (ahora inglés).
  - Menú (Super) `omarchyMenu` + `bwm-menu.jsonc`; cuadrícula Apps (Alt+Espacio o Super+Espacio, `AppGrid.qml`); dock opcional
    (`omarchyDock`, `dock.omarchy`, apagado; Super+M); notificaciones, OSD, polkit, recordatorios, bloqueo
    hyprlock, captura omasnap, portapapeles (Super+V), emojis (Super+.), salvapantallas, glass, transparencia.
  - Temas: 23 incluidos (`hypr/omarchy/themes`), temas instalados en `~/.local/share/bwm/omarchy-themes`
    o paleta dinámica del fondo; Alt+R carrusel; `omarchy-theme-set`. Ajustes → Plugins y Ajustes → Temas permiten
    buscar en los catálogos de Omarchy, instalar por Git, aplicar temas y activar/colocar plugins.
    Multimedia (`crmne.mpris`) va por defecto a la derecha de la hora (`centerEnd`).
  - Apps: todas las plantillas de Omarchy (`bwm_omarchy_apps.py`, también para apps sin instalar; LazyVim propio
    en `config/nvim`), Vesktop/Firefox con capa TUI propia, Spotify `BWM-Omarchy`, Steam con Adwaita-for-Steam.
- **Skins = carpetas**: `config/hypr/skins/<id>/skin.json` es la única fuente de datos de una skin (identidad,
  `windows`, `palette`, `look`, `bar`, `fonts`, mapa `parts`, requisitos); `bwm_skins.py` lo carga y
  `bwm-theme-manager.py` construye `THEMES` desde ahí. Variable de ventanas **`"windows"`**: `"tiling"`
  (mosaico: Default, Retro) o `"traditional"` (WM tradicional, todo flota con barra: Plasma) + bloque
  `traditional` (titlebar, panel, edgeMargin, gap). `theme.lua` lleva `windows` y `rules.lua` lo usa.
  `tests/test_skins.py` valida los manifiestos y que existan las rutas de `parts`.
- **Temas por defecto**: Default = Material You **dinámico** (matugen desde el fondo); Retro = paleta **dinámica**
  en formato Omarchy (o uno de los 23 temas **estáticos** con Alt+R); Plasma = Breeze Dark **estático**.
- **Bienvenida** (`bwm`): asistente tipo Calamares que se abre en cada inicio de sesión hasta desactivarlo
  (`bwm startup off`): gracias, skins instaladas en verde si tienen sus requisitos (desplegables, con comandos y
  «Activar»), «Añadir skins» → `docs/SKINS.md`. Ventana `qs -p` aparte: `pkill -x quickshell` no la cierra.
- **Todos los estilos**: GTK 3 en vivo (tema `BWM-1|BWM-2`), qt6ct + `kdeglobals`, flatpaks con overrides, kitty en
  vivo, Vesktop (`themes/bwm.theme.css`), iconos por estilo. Al cambiar de skin no se reinician apps: se conserva
  reproducción y workspaces; los colores que requieren reinicio quedan pendientes (Spotify puede requerir Spicetify).
  SDDM/Plymouth que siguen los colores, `window-guard.py` para juegos, aplicaciones predeterminadas
  (`default-apps.py`, `bwm-terminal`), hooks del usuario en `~/.config/bwm/hooks/theme-set[.d]`.

## 5. Trampas aprendidas

- **Vigilancia de archivos**: Vesktop vigila por inodo (fs.watch) → escribe en el sitio (`_write_in_place`); un
  rename atómico lo deja sordo. qt6ct vigila la carpeta y aun así no repinta apps abiertas. GTK 3 lee
  `~/.config/gtk-3.0/gtk.css` sólo al arrancar → los colores van en un tema que se alterna.
- **Un solo dueño**: polkit (un agente por sesión) y `org.freedesktop.Notifications`: en Retro los tiene
  Quickshell (Omarchy); fuera, `hyprpolkitagent`/swaync o BWM. Al tocar esto, revisa `bwm-theme-manager.py`
  (6.1/6.2) y `autostart.sh`.
- **Flatpak**: `--filesystem=xdg-config/x` se monta también en `~/.var/app/<id>/config/x`; los enlaces de
  `~/.config` apuntan al repo, que también hay que exponer.
- **Electron** reescribe su argv como una sola cadena: no lo relances con `/proc/<pid>/cmdline` tal cual
  (Vesktop flatpak: detecta `/app/` y usa `flatpak run`). Firefox: quita las URL con que se abrió.
- **Steam/Stremio no son Qt** en esta instalación: Steam usa CEF (Adwaita no cambia Tienda/Comunidad web); Stremio Linux usa GTK4/WebKit, con puente propio `stremio-theme.py`/`.cjs` para la web y CSS en vivo, activado sólo si está instalado (también desde `install.sh`). No confundir tema del marco con tema del contenido. Detalle y desactivación: `docs/STREMIO_THEMING.md`.
- **Steam en Retro:** `overlays/steam.css` hace que la barra superior use el fondo base del tema;
  Default/Plasma conservan la superficie elevada de la plantilla compartida.
- **Ajustes:** Plugins y Temas son páginas independientes en ambas apps; Advanced se eliminó.
  Tipos compartidos en `modules/settings/addons/` necesitan su `qmldir` explícito. About usa el logo
  BWM del arranque, GitLab/GitHub del proyecto y `assets/bwm-star.gif`.
- **About del menú Retro:** es Fastfetch con la configuración/logo/animación de Omarchy,
  `omarchy-launch-about`; About de Settings conserva las tarjetas BWM. El lanzador ajusta una ventana
  `org.omarchy.about` flotante y deshace su maximizado inicial antes de medir (si no, Hyprland rechaza
  el resize). WM consulta `hyprctl version -j`, no el binario que puede haberse actualizado sin reiniciar.
- **os-release:** puede usar comillas simples, dobles o valores sin comillas. Parsear como datos
  (`SystemInfoData.js`), aplicar en `FileView.onLoaded` y recurrir a `/usr/lib/os-release` si falta `/etc`.
  Los SVG simbólicos negros se tiñen con ColorOverlay; MultiEffect.colorization deja negro el negro.
- **Temas de la comunidad:** `~/.config/omarchy/themes` es un enlace al repo en este equipo. No instalar
  ahí: usar `~/.local/share/bwm/omarchy-themes` (respeta `XDG_DATA_HOME`). Listado, resolución y carrusel
  comparten el catálogo; no volver a limitar las búsquedas a `THEMES_DIR`.
- **Anchura de widgets:** `OmarchyPluginSlot` reserva cero si el widget está invisible. Los que no caben
  se ocultan con opacidad/recorte, manteniendo su medida; `visible: false` en el padre produce un bucle
  al medir `loader.item.visible`. Los servicios ajenos sólo cargan con el plugin activado.
- **Salvapantallas:** el disparo automático respeta inhibidores, «mantener despierto» y cualquier reproductor
  MPRIS en reproducción; el inicio manual por IPC sigue disponible.
- **Gentoo:** usa `sudo eselect news read`. Sin sudo puede listar los avisos pero fallar al guardar
  `news-gentoo.unread/skip` (root:portage) con «Cannot update list of news items». No cambies permisos.
  En `dispatch-conf`, compara el archivo actual con `._cfgNNNN_*` antes de recomendar `u` (aceptar),
  `z` (descartar) o `m` (fusionar); no aceptes cambios de configuración en bloque.
- **Plugin hyprbars y versión de Hyprland**: el `.so` guarda el commit de Hyprland para el que se compiló;
  `bwm-requirements.py` lo compara con el que corre. Tras actualizar Hyprland, Plasma sale en rojo hasta
  recompilar (`make && make install`, nunca `cp`). Si la API cambió (0.55→0.56: `State::monitorState()`,
  `Desktop::windowState()`, `CViewHitTester`, `Fullscreen::controller()`, `Animation::mgr()`), portéalo con el
  diff del hyprbars oficial entre los commits que fija `hyprpm.toml` de hyprwm/hyprland-plugins.
- **swww/awww**: GURU publica swww con su nombre nuevo, `awww` (mismo uso). Los scripts usan el que exista.
- **Luz nocturna**: dos motores (servicio `Hyprsunset.qml` en Default/Plasma, `nightlight.py` en Retro) con un
  solo Kelvin: `nightlight.py --temperature` lo copia a `light.night.colorTemperature` y el servicio llama a
  `nightlight.py --remember K` (sólo guarda; no enciende ni apaga).
- **XWayland**: Hyprland no fija primary (Wine usa el primer monitor); coordenadas X distintas de las de Hyprland.
- **Quickshell**: un archivo con el mismo nombre que un tipo que usa dentro (p. ej. `PolkitAgent.qml`) lo ensombrece;
  tipos de una carpeta hermana cargada por `Loader` no se resuelven (usa `component` en línea o importa la carpeta).
- **Hyprland 0.55 Lua**: `hyprctl dispatch 'hl.dsp.…'`; inyectar atajos con
  `hyprctl eval 'return hl.dispatch(hl.dsp.send_shortcut({…}))'`.
- `pkill -f <patrón>` mata tu propia shell si el patrón está en el comando: mata por PID. Lo mismo `pgrep -f` en un
  bucle de espera (no termina nunca): usa `ps -eo args | grep "[b]wm_omarchy.py restart"`.
- Kitty recuerda también el estado maximizado: `remember_window_size no` evita restaurarlo. La regla global
  `suppress-maximize-events` bloquea peticiones de maximizado de apps (también botones CSD); el compositor
  conserva el control manual y las peticiones de fullscreen de juegos/vídeo siguen permitidas.
- Omarchy usa `pacman`/AUR: al portar sus scripts, cámbialo por emerge/flatpak/`qlist` y avisa del paquete con
  `scripts/bwm-require.sh`.

## 6. Cómo probar

- Hyprland: `hyprctl reload`, `hyprctl configerrors`, `Hyprland --verify-config --config <archivo>`.
- Quickshell: `qs -c ii log` (errores de la instancia real; busca «failed to load», `ReferenceError`, `TypeError`,
  «is not a type»), `qs -c ii ipc show` (un panel que no carga **desaparece**), `qs -c ii ipc call <target> <función>`.
  «Handler was registered but will not be used» con dos monitores es esperado.
- Ajustes sin abrirlos a la vista: `SETTINGS_PAGE=<nombre|índice> timeout 8 qs -p ~/.config/quickshell/ii/settings.qml`
  con la regla temporal al workspace 9, y mira su salida.
- Capas visibles: `hyprctl layers -j` (namespaces `omarchy-*`). Capturas: `grim -g "x,y wxh"` (HP en `0,1080 1920x1080`).
- Python/bash: `python3 -m py_compile`, `bash -n`.
- Requisitos: `./install.sh --check` o `bwm check [--skin id] [--distro arch|fedora|…]` (sólo lee; `--distro`
  enseña los comandos de otra distribución). La bienvenida no se renderiza con `QT_QPA_PLATFORM=offscreen`
  (Quickshell necesita Wayland): para verla, ábrela flotando en un workspace visible y captura su recuadro.

## 7. Pendiente

Lista completa en `BWM_CONTEXT.md` §2.6 (menú Estilo de Omarchy, layouts de workspace, atajos de ventanas,
Install/Remove, web apps, compartir, Setup…; Qt sin recarga en vivo; entorno de pruebas con `$HOME`).

- Estado de Git: consulta `git status --short --branch` y `git log -1 --oneline`; no deduzcas el
  estado actual de un hash escrito en la documentación. Un commit local no implica push.
