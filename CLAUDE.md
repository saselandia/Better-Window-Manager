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
las mejoras de aspecto de cada original**: en la skin Breeze (Kde plasma) un tema de Plasma bajado de
internet debe aplicarse y funcionar; en Retro, un tema o plugin de Omarchy. BWM tiene pocas
interfaces propias (la bienvenida, Ajustes); casi todo es la interfaz del escritorio original.
**Pocas skins, fáciles y con lo mismo**: las tres actuales hacen lo esencial, se aprenden enseguida y
comparten casi las mismas funciones básicas; lo muy importante y propio de un escritorio se incluye en
su skin, la complejidad extra no se ofrece. **Un único compositor**: portar a Hyprland escritorios que no
corren sobre él (KDE Plasma en curso). Compatibilidad estimada y qué se conserva entre skins: README y
`docs/SKINS.md`.

## 0. Vocabulario

- **Estilo** (*skin*): default (end-4), Retro (Omarchy), Breeze (Kde plasma).
- **Tema**: lo de *dentro* de un estilo (temas de Omarchy incluidos/instalados en Retro o su paleta dinámica).
- Los nombres internos no cambian (`bwm-theme-manager.py get|set <estilo>`, `theme.lua`, `Appearance.isRetro`,
  `THEME_SPECIFIC_SECTIONS`…). En textos visibles, comentarios y documentación: «estilo/skin».

Los nombres visibles de las skins son **default (end-4)**, **Retro** y **Breeze (Kde plasma)**.
Los identificadores internos siguen siendo `default`, `retro` y `plasma`; KDE Plasma sigue
siendo el nombre del escritorio original que imita Breeze.

## 1. Qué es y dónde está

- Escritorio sobre **Hyprland ≥ 0.55 configurado en Lua** (sesión del 2026-10-28: 0.56.2; mira `hyprctl version -j`) + **Quickshell** (QML, config `ii`, derivada de
  end-4/illogical-impulse) en **Gentoo** (systemd), kernel cachyos, GPU **NVIDIA** + iGPU AMD (Ryzen 9 7900).
- Repo: `/mnt/HDD1TB/Projects/hyprland-de` (enlace `~/Projects/hyprland-de`). `~/.config/{hypr,quickshell,
  illogical-impulse,rofi,kitty,matugen,swaync,gtk-3.0,gtk-4.0,xdg-desktop-portal,nvim}` son **enlaces al repo**:
  editar el repo = editar lo que corre.
- Usuario: `sasel` (git `saselandia`). Habla **español**: responde en español.
- Remotos: `git push origin main` sube a GitLab y GitHub a la vez.
- Monitores (desde 2026-11-04): LG UltraFine 4K (arriba a la derecha, `2560x0`) y MSI MAG 274Q 1440p@240 (`0x720`, principal; antes un HP X24ih 1080p@144).
  **Se identifican por `desc:`**, nunca por `DP-N` (cambian con el orden de arranque de las GPU).

## 2. Reglas que NO se pueden romper

1. **Plugins C++ de Hyprland** (`src/breezebars`, `src/csd-minimize`): compilar con `-fno-gnu-unique` y desplegar
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
4. Campos `breezebars:*` de `hl.window_rule` (sólo existen con el plugin de Breeze cargado): dentro de
   `if hl.plugin and hl.plugin.breezebars then … end`, o sale «Your config has errors» en los otros estilos.
   **Dos plugins de barras, separados:** Breeze = `breezebars` (`src/breezebars`, `breezebars.so`: Breeze, CSD,
   snapping); Retro = el de Omarchy sin cambios (`src/omarchy-titlebars`, `omarchy-titlebars.so`, se registra como
   `hyprbars`). No mezcles funciones de uno en el otro sin que lo pida el usuario.
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
    temas/plugins de su escritorio original (formato de Omarchy en Retro, de Plasma en Breeze (Kde plasma), de
    matugen/end-4 en default (end-4)). Ante la duda, se adapta BWM al formato del original, no al revés. No
    introduzcas formatos de tema propios donde el original ya tiene uno.
12. **Requisitos declarados**: si una skin o el núcleo empieza a usar un programa, módulo QML/Qt, fuente o
    biblioteca nuevos, añádelo a `config/hypr/skins/requirements.json` (catálogo con paquetes por distro) y al
    `requires`/`recommends` de la skin; regenera la tabla de `docs/REQUIREMENTS.md`. El instalador, `bwm check` y
    la bienvenida salen de ahí.

13. **Configuración modular**: cada skin en sus carpetas/módulos propios y lo común en lo común, sin mezclar
    (tabla en `docs/SKINS.md`, «Estructura modular»). Código nuevo de una skin nace en su carpeta; no metas
    condiciones de una skin dentro de un módulo de otra si puede ser un módulo aparte.
14. **Se conserva entre skins** (no lo hagas propio de una skin): red/Bluetooth, cursor, Kelvin de la luz
    nocturna, apps predeterminadas (el gestor de archivos admite modo «Según la skin» —Dolphin en
    default/Breeze, Nautilus con extensiones de Omarchy en Retro— o fijar uno único; sus favoritos
    `gtk-3.0/bookmarks` ↔ `user-places.xbel` se sincronizan en común con `bwm-bookmarks-sync.py`), workspaces (los mismos
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
| BWMenu (rescate con + y - a la vez) | Galería autónoma `quickshell/bwmenu/` (mascota `BwmMascot.qml` y `mascot/{retro,default,plasma}/Character.qml`), paletas nativas en `scripts/bwm_menu_appearance.py`; `bwm-menu.py`/`bwm_versions.py`, `bwmenu`, `bwm menu`. Consola independiente de Qt/Quickshell con `--tui`, también en TTY. Atajos en helpers de `keybinds-manager.py`; guía `docs/BWMENU.md` |
| Catálogo «Añadir skins» de BWMenu | Repo independiente `saselandia/bwm-skins` (GitHub + GitLab), checkout `/mnt/HDD1TB/Projects/bwm-skins`; `catalog/skins.json` v2, generado con `scripts/bwm-skin-catalog.py build --catalog-root /ruta/bwm-skins` desde `skins/<id>/catalog.json` externos. Sólo default, Retro y Breeze van incluidos en BWM. Guía `docs/SKIN_CATALOG.md`; interfaz `quickshell/bwmenu/CatalogCard.qml` |
| Cambiar de estilo / ver qué hace al cambiar | `config/hypr/scripts/bwm-theme-manager.py` (`apply_theme`) |
| Algo que sólo cargue en un estilo | `quickshell/ii/panelFamilies/IllogicalImpulseFamily.qml` (`extraCondition`) |
| Colores/temas de Retro y sus apps | `scripts/bwm_omarchy.py` (`apply_retro_palette_colors`), `scripts/bwm_omarchy_apps.py`, `hypr/omarchy/themed/*.tpl` |
| Colores de apps en default (end-4)/Plasma | `config/matugen/config.toml` + `templates/` (Plasma los rellena con el esquema de color de Plasma activo: `skins/plasma/scripts/plasma_palette.py`) |
| Temas de Plasma en Breeze (esquemas, estilos, iconos, temas globales) | `skins/plasma/scripts/plasma-theme.py` (escribe kdeglobals/plasmarc/kwinrc con notificación; guarda y devuelve el kdeglobals de Breeze al cambiar de skin), `modules/plasma/theme/PlasmaTheme.qml` (lo lee el shell); plan del port en `docs/BREEZE_PLAN.md`, arquitectura en `docs/BREEZE_ARCH.md` |
| Preferencias del sistema (Breeze) | `plasmaSettings.qml` + `modules/plasma/settings` (barra lateral de systemsettings 6.7.5, `Catalog.js` de páginas, `ModuleView.qml`); KCM reales con el módulo QML `org.bwm.kcm` (`src/bwm-kcmhost`, `make install`; `open-settings.sh` pone `QML_IMPORT_PATH` y el estilo `org.kde.desktop`). Páginas propias en `pages/` escriben kwinrc/kdeglobals (puente F2); README de la carpeta; prueba `tests/test_plasma_settings.py` |
| Panel de Plasma (Breeze) | modules/plasma/panel (compactos nativos Kickoff/reloj/Mostrar escritorio, SVG, tareas, edición); bar.plasma; Loader por ruta sólo en Breeze en IllogicalImpulseFamily.qml. README de esa carpeta y docs/BREEZE_ARCH.md §10. Reinicio de mantenimiento para archivos nuevos. Bandeja/applets en modules/plasma/{tray,applets} (F5, ports y límites en sus README) |
| Kickoff de Plasma (Breeze) | `modules/plasma/kickoff` (QML original de Plasma 6.7.5 con los modelos de Kicker; `Plasmoid.qml` sustituye al attached, `KickoffWindow.qml` al diálogo, menús con `PC3.Menu` porque QMenu no abre desde layer-shell); config `bar.plasma.kickoff`; traducciones con `plasma-theme.py translations`; prueba `tests/test_plasma_kickoff_ui.py` |
| Decoraciones de KDE (Breeze) | `src/bwm-decorator` (auxiliar Qt/KDecoration3 fuera de Hyprland; `PROTOCOL.md`), supervisor `skins/plasma/scripts/decorator.py build|start|stop|status`; plugin `src/breezebars` (`DecoClient`, `barRemote`; README); pruebas `tests/test_bwm_decorator.py`, `tests/test_breezebars.py`; `hyprctl hyprbars-csd` |
| Minimizar/maximizar/restaurar en Breeze (KWin) | `skins/plasma/scripts/kwin-window.py` (modo en etiquetas `bwm-max-v/h`, restauración por ejes; minimizar con el formato común de `toggle-minimize.py`); atajos `"skins": ["plasma"]`; pruebas `tests/test_kwin_window.py` |
| Menús contextuales de Breeze (ventana, tareas, escritorio, panel) | `quickshell/ii/modules/plasma/menus/` (PC3.Menu, README), IPC `plasmaWindowMenu`; acciones en `kwin-window.py`; traducciones `menus/po` (`extract.py`); pruebas `tests/test_plasma_menus_ui.py` |
| Detección CSD/SSD de Breeze | `src/breezebars/CSDLogic.hpp` y `CSDDetect.cpp` (negociación aplicada, X11 asíncrono); `hyprctl -j breezebars-csd` / Lua `hl.plugin.breezebars.decoration(address,pid)` dan el marco real para Python y placement. Auditoría `skins/plasma/scripts/csd-audit.py`; matriz `docs/BREEZE_CSD_RESULTS.md`. Sólo probar plugin nuevo tras reiniciar sesión |
| Selector de skins de Breeze (Alt+T) | `modules/plasma/skinPicker`, diseño anterior recuperado; IPC plasmaThemePicker; paleta de PlasmaTheme y fuente Noto Sans 10. Los temas globales KDE se eligen en Preferencias |
| Interfaces de Plasma (F12) | `modules/plasma/{switcher,osd,lock,runtime}`; `interface-theme.py` lee LayoutName/LookAndFeelPackage y adapta QML en caché. ThemeHost en `src/bwm-kcmhost` (API 2, motores separados; Qt.quit de un tema no cierra el shell). Controlador MRU común intacto. KRunner nativo en Alt+Espacio sólo Breeze; agente polkit desde manifiesto vía `bwm_polkit.py` (KDE en Breeze, Omarchy embebido en Retro) |
| Cierre del port Breeze y pruebas de integración | `docs/BREEZE_F13_RESULTS.md` (limpieza, Sweet/KNS, cambios de skin y lista manual); `scripts/bwm-shell-conflicts.py` repara sólo reservas de bandeja rotas de kded sin módulos activos salvo ktimezoned |
| Reglas y encaje de KWin (Breeze, F10) | `skins/plasma/scripts/kwin_rules.py`, `kwin_tiles.py`, `kwin-tiles.py`; vigilante único F2 y Lua generado, `skins/plasma/hypr/{rules,kwinrules}.lua`; plugin `KWinSnap.hpp`/`SnapGeometry.hpp`; outline/editor `modules/plasma/tiling`. Ctrl+flechas conservado; Meta+T editor reducido. Cobertura y opt-out en `skins/plasma/scripts/KWIN_RULES.md`, lista tras reinicio en `docs/BREEZE_F10_CHECKLIST.md` |
| Configuración KDE ↔ BWM en Breeze | `skins/plasma/scripts/kde-config-bridge.py` (export/import/watch, ciclo enter/leave), `skins/plasma/hypr/kwin.lua`; inventario y autoridad en `docs/BREEZE_ARCH.md` §9. Gestores comunes avisan por `scripts/bwm_settings_hooks.py` (hook del manifiesto). Usuario Lua al final; nunca escribir `bwm/user/*` |
| GTK 3 / Qt / flatpaks | `scripts/gtk-theme.py`, `scripts/bwm_icons.py` (qt6ct, `kdeglobals`, overrides) |
| Barra Retro (la de Omarchy), sus paneles y plugins | `quickshell/ii/omarchyShell/` (copia de `shell/` de Omarchy: `OmarchyShell.qml` = su anfitrión, `plugins/{bar,panels,agents,services}`), `~/.config/omarchy/shell.json`, `omarchy-bar`/`omarchy-plugin-*`; `bwm-plugin.sh` traduce las órdenes de Ajustes → Barra/Plugins y del menú |
| Instalar/elegir temas y plugins | `modules/settings/{PluginsConfig,ThemesConfig}.qml`, `modules/settings/addons/`, `scripts/bwm-addons.py`, `scripts/bwm-plugin.sh`; detalle en `docs/OMARCHY_ADDONS.md` |
| About del menú Retro (Fastfetch) | `scripts/omarchy-shims/omarchy-launch-about`, `hypr/omarchy/about/`, `scripts/bwm-about-data.py`; no confundir con About de Settings |
| About de Ajustes / detección de distro | `modules/settings/About.qml`, `services/SystemInfo.qml` y `SystemInfoData.js` (os-release sin ejecutar shell); enlaces propios de BWM |
| Entrada del menú de Retro | `config/hypr/omarchy/bwm-menu.jsonc` (`when`/`checked` en bash) |
| Configuración del usuario en texto (manda sobre BWM) | `scripts/bwm-user-config` (`list/edit/apply/path`), `~/.config/bwm/user/{hyprland.lua,shell.jsonc}`, `~/.config/omarchy/shell.toml`, `~/.config/bwm/extensions/menu.jsonc`; `hyprland.lua` la carga al final con `pcall`; `bwm-theme-manager.py apply-user` y al cambiar de skin |
| Configuración integrada de Retro | `modules/ii/omarchyMenu/omarchy/settings/` (filas nativas y editor de pantallas dentro de `Menu.qml`) + `skins/retro/scripts/settings.py` (listas sobre los gestores comunes); `open-settings.sh [página]` → IPC `omarchyMenu.settings`. `retroSettings.qml` sólo redirige, sin ventana propia |
| Un comando `omarchy-*` que falta | `config/hypr/scripts/omarchy-shims/` (+ enlace en `~/.local/bin`, `bwm-plugin.sh catalog`) |
| Modo de cada workspace en Retro (mosaico, desplazamiento, flotante con barras) | `skins/retro/hypr/workspace-modes.lua` (port de Omarchy; modos en `~/.local/state/omarchy/workspace-layouts/`), shims `omarchy-hyprland-workspace-layout-*` y `bwm-workspace-layout-set`; barras con el plugin de Omarchy sin cambios (`src/omarchy-titlebars`), nada del de Breeze |
| Reglas de ventana / juegos | `hypr/modules/rules.lua`, reglas por app de Omarchy (`Commons/omarchy/default/hypr/apps/`, cargadas por `modules/app_rules.lua`), `scripts/window-guard.py` |
| Atajos | `keybinds.json` vía `keybinds-manager.py` |
| Bloqueo / pantalla de inicio de cada skin | `modules/ii/lock/Lock.qml` elige: `lock/LockSurface.qml` (end-4, el desenfoque lo pinta `background/Background.qml` y necesita `session_lock_xray` de `skins/default/hypr/lock.lua`), `omarchyLock/` (Omarchy 4, Retro), `modules/plasma/lock` (KScreenLocker/Breeze, con LockContext común); SDDM común entra solo (`install-boot-theme.sh`) |
| Apagar, reiniciar, cerrar sesión, suspender | `config/hypr/scripts/bwm-power <acción> [--dry-run]` (común a todas las skins); los menús de cada skin sólo lo llaman |
| Animaciones (ventanas, workspaces, menús/capas, fondo) | `config/hypr/skins/<id>/hypr/animations.lua` (copia de las del original); fondo: `modules/ii/background` (default (end-4)), `modules/ii/omarchyBackground` (Retro, vía `set-wallpaper.sh`) |
| Temas web de Stremio / barra de Steam | `scripts/stremio-theme.py`, `scripts/stremio-theme.cjs`, `scripts/steam-theme.sh`, `hypr/omarchy/overlays/steam.css`; alcance en `docs/STREMIO_THEMING.md` |
| Inactividad (salvapantallas, apagar monitores, bloqueo, suspender) | `modules/ii/idle/BwmIdle.qml` (común) con `idle.screensaver/screensaverTime/screen/lock/suspend` comunes a todas las skins; página Ajustes → Inactividad (`modules/settings/IdleConfig.qml`, también en el menú de Retro); salvapantallas sólo en Retro (`skins/retro/scripts/launch-screensaver.sh`: el nativo de Omarchy si se compiló con `install-screensaver.sh`, si no el de terminal); opciones de Hyprland propias de una skin en `skins/<id>/hypr/misc.lua` |
| Actualizaciones de Gentoo / Flatpak | `BWM_CONTEXT.md` §2.7; shims `omarchy-update` y `omarchy-update-available` |
| Reiniciar una app conservando sus ventanas | `bwm_omarchy.restart_app()` (Firefox, Vesktop, Steam, Stremio) + `scripts/bwm_windows.py` (`quiet_activation`: sin `focus_on_activate` mientras se reinicia, o te lleva a su workspace) |
| Dónde quedan las ventanas al cambiar de skin | `scripts/bwm_windows.py` (`remember_traditional` guarda geometría libre por sesión/skin y dirección+PID/inicio; `float_in_place`, `traditional_box`, `restored_box`, `hold_new_windows`), `bwm_transition.py`, `sync_floating_windows`; familia de la skin en `skins/<id>.json` → `windowing` (`tiling`/`stacking`) |

## 4. Estilos y piezas clave

- **Gestor**: `bwm-theme-manager.py get|set|toggle|list`. Perfil de Quickshell por estilo en
  `illogical-impulse/config-<estilo>.json` (secciones propias: appearance, background, bar, dock, panelFamily,
  waffles; dentro de `bar` se comparten `workspaces.shown`, `weather` y `topLeftIcon`); el resto se comparte.
- **default (end-4)**: Material You con matugen desde el fondo (`scripts/set-wallpaper.sh`).
- **Breeze (Kde plasma):** port KDE en `quickshell/ii/modules/plasma/` (panel, Kickoff,
  bandeja/applets, menús, temas, Preferencias, cambiador, OSD y bloqueo); no queda modules/ii/plasma*.
  Lee formatos reales KDE y kdedefaults; `bwm-decorator` renderiza KDecoration/Aurorae fuera de
  Hyprland y `breezebars` los compone. Cursor y servicios comunes siguen a BWM. Alt+T abre el selector anterior en `modules/plasma/skinPicker`;
  temas globales en Preferencias. Informe y límites: `docs/BREEZE_F13_RESULTS.md` (~50 %).
- **Retro = Omarchy 4** (repo `basecamp/omarchy`, rama `quattro`, MIT; investigación en `docs/OMARCHY_INVESTIGACION.md`):
  - Librerías de Omarchy en `quickshell/ii/Commons` y `Ui` (`qs.Commons`, `qs.Ui`; cambios BWM en `Commons/README.md`):
    `Color.qml` vigila `~/.local/state/bwm/omarchy/{colors,shell}.toml`, `I18n.qml` con cadenas incluidas (en, es-MX),
    `Style.qml` con `bwmScale`.
  - Barra = **la de Omarchy tal cual** (`omarchyShell/`, quattro `18ac93c`, BWM_CONTEXT §3.118): arrastrar widgets,
    mover la barra a cualquier borde, doble clic para el fondo, módulos propios; se configura en
    `~/.config/omarchy/shell.json` (formato de Omarchy) con `omarchy-bar`/`omarchy-plugin-*`. Plugins de terceros en
    `~/.config/omarchy/plugins` y los preinstalados de BWM en `omarchy-plugins/`. Parches «BWM» mínimos (workspaces
    con numeración global, servicios de BWM, menú y capas de `OmarchyPlugins`). Idioma en Ajustes → Idioma.
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
  (mosaico: default (end-4), Retro) o `"traditional"` (WM tradicional, todo flota con barra: Plasma) + bloque
  `traditional` (titlebar, panel, edgeMargin, gap). `theme.lua` lleva `windows` y `rules.lua` lo usa.
  `tests/test_skins.py` valida los manifiestos y que existan las rutas de `parts`.
- **Temas por defecto**: default (end-4) = Material You **dinámico** (matugen desde el fondo); Retro = paleta **dinámica**
  en formato Omarchy (o uno de los 23 temas **estáticos** con Alt+R); Plasma = el tema de Plasma activo (Breeze Oscuro de entrada), **estático**: lo cambian los temas de Plasma, no el fondo.
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
  Quickshell (Omarchy); Breeze usa polkit-kde-agent y default, `hyprpolkitagent`/BWM. Al tocar esto, revisa `bwm-theme-manager.py`
  (6.1/6.2) y `autostart.sh`.
- **Flatpak**: `--filesystem=xdg-config/x` se monta también en `~/.var/app/<id>/config/x`; los enlaces de
  `~/.config` apuntan al repo, que también hay que exponer.
- **Electron** reescribe su argv como una sola cadena: no lo relances con `/proc/<pid>/cmdline` tal cual
  (Vesktop flatpak: detecta `/app/` y usa `flatpak run`). Firefox: quita las URL con que se abrió.
- **Steam/Stremio no son Qt** en esta instalación: Steam usa CEF (Adwaita no cambia Tienda/Comunidad web); Stremio Linux usa GTK4/WebKit, con puente propio `stremio-theme.py`/`.cjs` para la web y CSS en vivo, activado sólo si está instalado (también desde `install.sh`). No confundir tema del marco con tema del contenido. Detalle y desactivación: `docs/STREMIO_THEMING.md`.
- **Steam en Retro:** `overlays/steam.css` hace que la barra superior use el fondo base del tema;
  default (end-4)/Plasma conservan la superficie elevada de la plantilla compartida.
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
- **Barra de Retro:** es el anfitrión de Omarchy (`omarchyShell/OmarchyShell.qml`); el único destino IPC `shell` es
  el de `OmarchyPlugins`, que le pasa las funciones de Omarchy (`ipc`) cuando existe. Lo que no es un plugin suyo
  (menú, portapapeles, emojis, selector de imágenes, recordatorios) vuelve a `OmarchyPlugins.summonLocal`. Su widget
  de workspaces da por hecho el modelo por monitor de Omarchy: está parcheado a la numeración global (§4.3 de
  `docs/OMARCHY_4_5.md`). Los comandos de monitores de Omarchy guardan con `omarchy-hyprland-monitor-persist` de BWM
  (`monitor-manager.py`, por `desc:`). Al actualizar desde Omarchy, conservar las marcas «BWM».
- **Inactividad:** cada fase respeta inhibidores y «mantener despierto»; un reproductor MPRIS sonando impide
  el salvapantallas y la suspensión, no el bloqueo. `loginctl lock-session` no bloquea en BWM (nadie lo
  escucha): bloquear es `bwm-power lock` / IPC `lock activate`.
- **Gentoo:** usa `sudo eselect news read`. Sin sudo puede listar los avisos pero fallar al guardar
  `news-gentoo.unread/skip` (root:portage) con «Cannot update list of news items». No cambies permisos.
  En `dispatch-conf`, compara el archivo actual con `._cfgNNNN_*` antes de recomendar `u` (aceptar),
  `z` (descartar) o `m` (fusionar); no aceptes cambios de configuración en bloque.
- **Plugin hyprbars y versión de Hyprland**: el `.so` guarda el commit de Hyprland para el que se compiló;
  `bwm-requirements.py` lo compara con el que corre. Tras actualizar Hyprland, Plasma sale en rojo hasta
  recompilar (`make && make install`, nunca `cp`). Si la API cambió (0.55→0.56: `State::monitorState()`,
  `Desktop::windowState()`, `CViewHitTester`, `Fullscreen::controller()`, `Animation::mgr()`), portéalo con el
  diff del hyprbars oficial entre los commits que fija `hyprpm.toml` de hyprwm/hyprland-plugins.
- **Pantalla completa**: `modules/fullscreen.lua` (cargado el último de las reglas) la deja sin bordes ni sombra, sin quitar la transparencia; un CSS nuevo para una app debe anular sus bordes/contornos en `:fullscreen` (Discord re-declara variables en `.theme-dark`: hay que ponerlas también ahí).
- **inotify (límite 128 instancias por usuario, por defecto en casi todas las distros)**: cada `FileView` con `watchChanges: true` (y cada `QFileSystemWatcher`) gasta una instancia, también si el archivo no existe. Llegar a 128 rompe otras apps (Obsidian: «EMFILE: too many open files, watch»). No crees un vigilante por elemento de una lista: uno sobre un archivo-marca que reescribe el productor (p. ej. `agents/usage/.updated`). Mide con `find /proc/<pid>/fd -lname 'anon_inode:inotify' | wc -l`.
- **swww/awww**: GURU publica swww con su nombre nuevo, `awww` (mismo uso). Los scripts usan el que exista.
- **Luz nocturna**: dos motores (servicio `Hyprsunset.qml` en default (end-4)/Plasma, `nightlight.py` en Retro) con un
  solo Kelvin: `nightlight.py --temperature` lo copia a `light.night.colorTemperature` y el servicio llama a
  `nightlight.py --remember K` (sólo guarda; no enciende ni apaga).
- **XWayland**: Hyprland no fija primary (Wine usa el primer monitor); coordenadas X distintas de las de Hyprland.
- **Quickshell**: un archivo con el mismo nombre que un tipo que usa dentro (p. ej. `PolkitAgent.qml`) lo ensombrece;
  tipos de una carpeta hermana cargada por `Loader` no se resuelven (usa `component` en línea o importa la carpeta).
  Dos módulos importados con un archivo del mismo nombre: gana el último import (pasó con `Dock.qml` de `dock` y
  `omarchyDock`); usa `import … as Nombre`.
- **Hyprland 0.55 Lua**: `hyprctl dispatch 'hl.dsp.…'`; inyectar atajos con
  `hyprctl eval 'return hl.dispatch(hl.dsp.send_shortcut({…}))'`.
- `pkill -f <patrón>` mata tu propia shell si el patrón está en el comando: mata por PID. Lo mismo `pgrep -f` en un
  bucle de espera (no termina nunca): usa `ps -eo args | grep "[b]wm_omarchy.py restart"`.
- Un demonio lanzado desde una terminal o una sesión de IA queda en su cgroup y puede morir con ella (pasó con la
  barra y `window-guard.py`, §3.105): lánzalos con `bwm_session.spawn()` (`hl.dsp.exec_cmd`), no con `Popen`.
  `window-guard.py` relanza el shell si falta: para pararlo de verdad, para antes el vigilante.
- **Entorno del shell al cambiar de skin:** arranque/recuperación/mantenimiento pasan por
  `bwm_session.start_shell` (proveedor Qt estable, KDE si está instalado). Las entradas de apps
  usan `AppSearch.launch` → `bwm-launch-app.py` → Hyprland para heredar el entorno actual,
  no el del arranque del shell. No forzar QIcon::setThemeName: desactiva el motor nativo KDE.
- **Anfitrión Plasma R4 (experimental):** cargar el archivo propietario con Corona.loadLayout
  antes de crear containments y guardar con saveLayout del mismo archivo + config.sync.
  AppletOrder del containment está en Containments/<id>/General, no Configuration/General.
  Exportar a otro nombre no sustituye ese ciclo. PanelSession sólo opera dentro del auxiliar;
  no activar el panel diario ni anunciar backends probados por descubrir un widget/acción.
  configUiModule/configUiComponent pueden ser páginas QML normales, no necesariamente KCM.
  Entregar title/cfg_ antes de Component.onCompleted y usar ConfigurationSession también en
  los probes; no certificar una opción por escribir el esquema desde una vía de prueba aparte.
  PanelViewHost carga Panel.qml instalado: length es preferencia, distinta de los límites de
  superficie. Sus setters son vista previa; applyViewSettings guarda explícitamente las seis
  claves admitidas en plasmashellrc nativo, respetando claves ajenas, kdedefaults e inmutabilidad.
  --native-policy añade panelVisibility 0–3 (1/2 sin reserva) con LayerShellQt; no confirma
  área útil real. Un panel por salida en ese ensayo; varios se bloquean hasta coordinar layout.
  Cambiar salida/orientación exige releer antes de guardar. Adaptive/efectos siguen
  sin backend; autoocultar/esquivar sólo con --native-policy y los puentes de R5.
  Vida QML y máscaras se validan al actualizar.
  Migración: conservar bar.plasma.edge o fallback bar.bottom (false→top), sin fijar BottomEdge/
  Horizontal; Corona serializa Location/FormFactor y el probe comprueba el orden por su eje.
  Alineación/longitud: placementContractVersion=1 sólo con outputSize lógico explícito por
  descripción; recalcular desde el archivo de origen y conservar formatos de staging anteriores.
  Es una captura para convertir preferencias, no certifica geometría física ni EDID (§315).
  El plasmashellrc de staging sólo contiene paneles preparados: no sustituir con él el archivo
  completo de sesión. Flags nativos migrados no certifican reservas/docking/Adaptive sin backend.
  PanelRuntime coordina vistas por descripción/skin; el hook común sólo controla una prueba
  registrada explícitamente con --follow-skin. No sustituye el panel diario. El llamador conserva
  Corona y bindings. Ambigüedad de salida deja el panel en
  espera; nunca usar el primer modelo parcial o un índice Qt como identidad persistente.
  Qt Wayland 6.11.2 no expone serie en QScreen: la descripción Hyprland puede añadirla al
  fabricante/modelo completo. Sólo admitir esa forma si la coincidencia es única; una serie
  conocida debe coincidir y dos salidas indistinguibles se rechazan. No certificar serie
  física cuando Qt no la aporta; status incluye qtPlatform/availableOutputs/serialAvailable.
  MSI real: Qt anuncia fabricante «Co., Ltd.» y descripción Hyprland «Co. Ltd.»; tolerar
  comas sólo en el prefijo completo del fabricante, sin alterar modelo/serie ni unicidad.
  Al cerrar la prueba, retirar registro y esperar a su transacción antes de borrar el ack.
  ProfileStore conserva archivos KDE completos y bindings separados en perfiles de ensayo;
  --serve-profile/--serve-selected-profile editan una copia privada y publican layout,
  preferencias y bindings juntos en otra generación tras cerrar todos los propietarios nativos.
  Una caída conserva la generación anterior; no checkpoint/restore/export con edición abierta.
  restaurar siempre a otra generación/ruta, sin sobrescribir el archivo de un KSharedConfig
  retenido. Mantener el lease durante la vida de Corona y hacer flush/cierre antes del checkpoint.
  --export-as conserva perfil/historial en la autoridad XDG de estado dedicada; no selecciona
  ni activa el panel. No ampliar esa autoridad a cualquier carpeta privada ni sobrescribir nombres.
  ProfileSelection (§267) guarda sólo la elección por nombre/procedencia bajo .selection
  en esa autoridad. No activa/autoinicia ni retira barras; revisión obligatoria para cambiarla.
  Abrir con openSelected y conservar el lease, nunca reutilizar una ruta de status como autorización.
  panel-session.py status exige respuesta nueva, no basta PID/ack viejo. renderReady sólo
  comprueba el marco Qt; replacementReady sigue false y no permite retirar el panel diario.
  widgetBackends informa instancias directas y dependencias/metadatos, no certifica servicios.
  Ni renderReady ni un inventario vacío habilitan sustitución. Revisar también hijos de bandeja
  y las autoridades/recuperación diarias antes de implementar takeover (§211).
  Adaptador KWindowSystem estático sólo en el auxiliar (§212): ABI privada V5 fijada a
  6.29.0 EXACT. No instalarlo globalmente ni dentro de Hyprland. --desktop-actions es opt-in
  de preview: usa el gestor común de minimizar/restaurar, no el efecto Peek de KWin/R7 ni
  el modelo TaskManager. Probes/export/KNS no habilitan acciones de escritorio.
  Binario de sesión R4: build/bwm-plasma-host/bwm-plasma-host dentro del repo (ignorado por
  Git); no asumir /tmp compartido/duradero entre ejecutores y terminales (§213).
  TaskManager experimental (§215): --task-actions sustituye sólo la fuente WindowTasksModel
  estándar dentro del auxiliar, usando APIs públicas Qt y LibTaskManager 6.7.5 EXACT.
  Conservar las fuentes personalizadas de terceros y mantener el panel diario.
  Transacciones nativas (§216): tareas y Mostrar escritorio comparten flock privado acotado;
  revalidar skin/PID/inicio tras adquirirlo. No cubre los llamadores diarios sin ese flag.
  Antes de confirmar retirada, suspender colas y esperar acciones en curso sin matarlas;
  RuntimeControl reintenta sin ack mientras quiescing. Conservar el fallo seguro del hook.
  VirtualDesktopInfo usa backend privado sin factoría pública; no intercambiar su puntero
  estático ni duplicar símbolos de la biblioteca. Menús/escritorios siguen sin certificar.
  No anunciar el widget entero operativo mientras falten esas capacidades y validaciones.
  Proveedor por protocolo (§218): src/bwm-plasma-desktops, extensión separada compilada
  pero NO instalada/cargada/autoiniciada. Empieza disabled. Núcleo y módulo deben llevar
  -fno-gnu-unique (verificar readelf), ABI Hyprland guardada y XML KDE privado fijado por hash.
  Fixture Wayland por socketpair prueba VirtualDesktopInfo/filtros/roles KDE originales;
  no acredita frontend real ni Task.qml pintado. Faltan barrera/conflictos y capacidades;
  no habilitar el proveedor sólo porque el fixture pase. Nunca bloquear el hilo compositor
  con flock/procesos: el propietario puede estar esperando su IPC. Despliegue futuro sólo
  make install atómico y carga al iniciar sesión, nunca hot load/unload.
  Barrera nativa (§219): bwm_plasma_desktop_control_v1 controla sólo el mismo wl_client.
  Todas las conexiones empiezan sólo lectura; propietario/resume habilita activaciones.
  Pause/destruir propietario cancela cola propia; otros clientes siguen. Cola en el núcleo,
  con recurso/serial de vida, y ack después del callback anterior. NativeDesktopControl
  correlaciona serial/estado con plazo 1 s; no admitir ack tardío como éxito ni bloquear la
  retirada porque el propio proveedor desapareció. Entrada/reanudación exigen confirmación.
  --native-desktops sólo consulta proveedor ya cargado/habilitado; nunca cargar desde el
  launcher. Qt generado init(nullptr) no es deinit: conservar regresión de pérdida/rebind.
  Menú nativo (§220): TaskMenuPolicy sólo opera dentro de raíces TaskManager registradas,
  con índices de capacidad BWM y ContextMenu.qml original revisado/fijado por SHA256.
  Máscara mediante QActionGroup público, no sobrescribir bindings enabled de QML ni copiar
  el menú. Un grupo no exclusivo por acción: removeAction solo no recalcula enabled;
  reactivar primero esa máscara conserva el estado explícito más reciente. Mantener encima,
  debajo y excluir captura siguen deshabilitados. Fuente desconocida bloquea el menú afectado.
  El test del menú carga KDE original pero Task.qml avisa de roles undefined en offscreen:
  prueba acciones/modelos, no el pintado de la barra ni su aceptación Wayland.
  Pantalla completa nativa (§221): snapshot fullscreenable opcional (ausente=false), sólo
  ventanas normales mapeadas/no ocultas/no fijadas/no minimizadas. El handler envía estado deseado, nunca
  toggle; kwin-window exige identidad/inicio y --state on|off bajo el bloqueo nativo.
  Revalidar también en Lua skin/PID/mapped/hidden/pinned/workspace. hyprctl repl devuelve recibo
  sólo con result.ok y modo interno leído igual al solicitado; exit=0 o «ok» no bastan. Lua sólo
  en BUILD_TESTING, sin compositor; no extender esta prueba a geometría/aceptación de sesión.
  Metadatos de tareas (§222): KSycoca::databaseChanged invalida la caché por fila tras 100 ms
  y se resuelve con TaskTools al leer roles de aplicación. No resetear filas/UUID ni agregar
  un watcher por ventana. El test reconstruye una base KDE real sólo con XDG temporales y
  KDESYCOCA eliminado; kbuildsycoca6 se requiere únicamente para BUILD_TESTING. No confundir
  esta actualización de aplicaciones .desktop con catálogo de plasmoides o prueba visual.
  Registro de escritorios (§223): el auxiliar exige control v2, inventario único visible y
  asociación desktop_global con el global KDE en la misma conexión. Enlace explícito por ID,
  no QWaylandClientExtension automático: Qt 6.11.2 trata la retirada por interfaz, no por ID.
  Duplicar el global KDE deja un bloqueo hasta reiniciar sólo el auxiliar; no resetear el
  backend privado de VirtualDesktopInfo. Permitir retirada/salir aun con conflicto. Controles
  retirados del servidor quedan inertes hasta destroy/desconexión para aceptar peticiones en
  vuelo. No habilitar/cargar el plugin por estas pruebas: aceptación de frontend/arranque
  en sesión sigue pendiente; ver el alcance limitado del arbitraje de §225.
  Arbitraje de servidor (§225): DesktopProvider inventaría el mismo display por socketpair
  asíncrono antes de publicar; inicialmente disabled sin globals. Claim elige entre BWM,
  sólo observa lo visible bajo el filtro; no impide globals ajenos/duplicación transitoria.
  Retirar con wl_global_remove conservando core/recursos/ofertas de UNA generación; no
  vaciar snapshot/resetear core ni reintentar cada 500 ms. providerRestartRequired pide
  futuro inicio de sesión del módulo, nunca hot unload. El latch cliente §223 sólo exige
  auxiliar nuevo. Launcher exige arbitraje v1 active además de barrera v2. Probado aislado
  normal/ASan y consumidor KDE, sin despliegue ni aceptación real del frontend/arranque.
  Vida del módulo (§226): Hyprland0.56.2 descarga plugins antes de destruir clientes.
  withdraw conserva core/recursos; destructor definitivo destruye TODOS los controles y
  recursos de claim antes de descargar .so. No dejar callbacks/interfaz del módulo en
  recursos con userdata=null tras destruir core. Retirados siguen asociados y niegan por
  withdrawn. Fixture retiene cores al retirar. DSO real de ensayo cubre orden de cierre,
  sin despachar requests después; NO autoriza hot unload ni certifica logout de sesión.
  Observer/peer/deadline nacen sólo en idle tras snapshot+opt-in, no durante constructor;
  cancelar antes del claim permite volver a pedirlo. Mantener filtro del compositor intacto.
  Launcher exige providerLifecycleVersion=1 e inicio diferido; rechazar módulos anteriores
  sin cargarlos/actualizarlos en caliente.
  Contador nativo (§227): CountMirror sólo copia en memoria; no volver a leer config.json
  en plugin/refresh. Puente existente resuelve opciones comunes+usuario y envía IPC fuera
  del compositor. No persistir otra preferencia ni cargar/habilitar módulo por estar instalado.
  Coordinación común §228 y reconcile usan bloqueo existente: auxiliar LOCK_NB, reconcile
  ya dentro; no adquirirlo recursivamente ni introducir espera/proceso en compositor. Rechazos/parcial
  conservan dato previo; primer valor desconocido bloquea publicación. Preflight sólo lee
  countMirrorVersion=1/copia conocida. Recibo no acredita frescura/panel operativo. Efectos
  sobre modelo probados en fixture; arranque/entrega reales pendientes. Puente en curso no
  reiniciado: necesita reinicio/inicio de sesión para adoptar nuevo módulo Python.
  Entrega entre skins (§228): SharedSettingsRuntime sólo en shell.qml y fuera de loaders,
  nunca en Config/Ajustes (evita duplicados). Dispatcher shared usa manifiestos incluidos,
  no scripts descargados. Prerequisito instala/arma sólo datos: jamás cargar/habilitar plugin.
  Auxiliar resuelve opciones de la skin actual, sin mantener/importar KDE bridge en Retro/
  default; no restaurar counts.tick del watch KDE. Process único + pending y retry, sin nuevo
  demonio/FileView/thread. FailedToStart de QS0.3.2 sólo runningChanged, manejar sin quedarse
  busy. sharedSettings status diagnostica, no valida panel. Fuente QML viva puede autorecargar;
  no afirmar carga/ausencia de cambios de sesión sin comprobar. IPC aquí sigue inaccesible.
  Delegado de tareas §229: test-taskdelegate exige backend Wayland original. TasksModel
  y WindowTasksModel consultan sus fuentes privadas al resolver roleNames; no sustituir
  símbolos/estado privado ni certificar Wayland con roles de fixture offscreen. Ensayo
  nativo normal aprobado por usuario (§233): ambos Task.qml dibujan en QImage, sin ventana
  ni superficie visible. Aquí wl_client_create sigue bloqueado; native ASan no ejecutado.
  No confundir QQuickRenderControl/QImage con entrada/superficies de sesión o widget entero.
  WAYLAND_SOCKET se consume al arrancar Qt/libwayland (§230): capturar identidad antes
  de QApplication y comprobar el wl_display activo; no exigir esa variable después.
  QQmlContext.baseUrl no identifica la fuente del objeto (§231): resolver recurso y
  verificar hash; la selección del delegado original se comprueba aparte por interfaz/raíz.
  Metadatos del test §232: usar .desktop/PNG y caché KDE temporales propios; un appId
  sin servicio puede resolverse por PID. Modelo conserva .desktop; Task.qml lo elimina.
  Grupo sin MRU (§234): TaskTools original requiere StackingOrder. clients sigue el orden
  inferior→superior de WindowState en0.56.2; focusHistoryID es MRU, no apilado. Conservar
  índices/UUID al cambiar el rol; fallback de snapshot legado no acredita orden físico.
  Registro del panel (§235): los applets pueden ser sólo hijos QQuickItem, no QObject.
  Recorrer ambos árboles sin reparentar ni forzar itemForApplet; probar PanelSession real,
  no sólo attach manual del widget. Startup de tareas exige fuente/snapshot, no basta PID.
  Filtro de escritorio (§236): showOnlyCurrentDesktop=true de KDE necesita VirtualDesktopInfo;
  probar geometría de QScreen coincidente y configuración nativa, no setters de TasksModel.
  Preview sin proveedor exige --all-desktops explícito, sólo XDG temporal y nunca --profile;
  no considerar boundModels/snapshot como prueba de ventanas visibles. Estado añade filas.
  special:minimized es almacén compartido entre monitores: regla común no_anim sólo allí
  suprime traslado animado; no prometer efecto KWin hacia el icono ni comprobación visual.
  Apariencia del preview (§238): --session-appearance sólo snapshot desechable, sin --profile.
  Preparar valores KDE permitidos con QCoreApplication antes de QApplication; no setThemeName,
  enlaces/copia completa de config ni layouts. KConfig SimpleConfig ignora addConfigSources:
  leer con NoGlobals/ruta absoluta, defaults explícitos y escribir destino nuevo SimpleConfig.
  Se respetan valores efectivos inmutables/borrados; no se migran sus restricciones al snapshot.
  Miniaturas del preview (§239): instalar kpipewire no aporta el protocolo KDE de captura.
  --task-thumbnails adapta sólo PipeWireThumbnail.qml original por URL/hash revisados en el
  motor compartido; no re-registrar tipos KDE ni manipular estado privado. Backend por
  handle extranjero estable + mapping64bits, sólo ventanas y snapshot iniciado tras vincular
  handle; UUID/PID/generación actuales. Nunca fallback a captura de salida/recorte de pantalla.
  Imágenes desacopladas de mmap, memfd CLOEXEC y límites; cerrar al ocultar/retirar/cambiar
  identidad. Captura posterior puede esperar daño en ventana estática: no timeout tras tener
  imagen. Prueba nativa compilada pero EPERM aquí no es pase ni aceptación de sesión.
  Captura R4 comparte ScreenshareSession del incidente BREEZE_RECOVERY: no reactivar sólo
  cambiando protocolo. Backend exige prueba de guarda de monitor del peer Wayland activo
  (SO_PEERCRED; ELF o informe IPC con PID coincidente); adoptar al próximo login. Parche
  0.56.2 en patches/hyprland guarda init/monitorChanged, probado por cuerpos aislados; no
  anunciar build completo de compositor, captura o resolución total del incidente. Sólo
  el binario de fixture autoriza su display sintético; no hay override CLI/env en el host.
  Parche local de Portage exige compilar fuente (--usepkg=n --getbinpkg=n), no reutilizar
  un binpkg. Ensayo native-task-thumbnail normal aprobado por usuario (§241): no repetir
  sin cambios; no equivale a native ASan, compositor parcheado o captura de sesión aceptada.
  Guarda del peer (§243): cap_sys_nice/filecaps de Gentoo puede impedir /proc/PID/exe.
  No confundir lectura denegada con marca ausente o sesión antigua; ejecutar diagnóstico
  check-thumbnail-compositor.py antes de pedir otra compilación/relogin. Preservar guarda,
  diagnosticar sin panel/capturas ni cambiar capacidades/permisos. wait_initial_ack debe
  detectar child muerto antes de register, conservando causa en vez de ENOENT de ack.json.
  Denegación confirmada por usuario (§244): no debilitar filecaps/ptrace/permisos. Parche
  ampliado informa bwmScreenshareMonitorGuard {version:1,pid:getpid()} en hyprctl -j version;
  getter implementado junto a guardas reales, sin E/S/esperas dentro del compositor. Auxiliar
  contrasta PID con SO_PEERCRED y UID propio, consulta fresca acotada; otra instancia falla.
  Subproceso usa runtime real BWM_R4_TASK_RUNTIME/BWM_R4_GUARD_RUNTIME, pues XDG propio es
  temporal. Esas rutas sólo seleccionan IPC, nunca autorizan. ELF directo sigue permitido.
  Extensión requiere sustituir user patch y recompilar desde fuente/reentrar por usuario;
  extensión adoptada y guarda IPC verificada por usuario (§245), PID/UID coincidentes.
  No pedir otro rebuild/relogin ni repetir CTest; siguiente paso es hover real del preview.
  Tooltips R4 (§246): ToolTipDialog6.7.5 deriva PopupPlasmaWindow, se crea desde C++ sin
  contexto QML. Resolver dueño por visualParent/árbol visual, no sólo Dialog/plasmoid. Rol
  LayerShellQt en SurfaceCreated antes de QWaylandWindow::setVisible/initWindow (Qt6.11.2),
  nunca cambiar rol mapeado. Un PopupAnchor, seguir dueño actual del tooltip compartido,
  conservar puntero y no pedir teclado/activación; al salir a ventana normal restaurar
  backend con hide/destroy. No ocultar PID propio en tareas para tapar un rol equivocado.
  Preview de tareas desechable ahora una instancia; --instances2 permite comparación sin
  tocar perfiles/probes. Local/ASan4/4 y ToolTipArea original pasan; miniaturas aceptadas
  por usuario en §247 (general, sin medición por caso). No repetir el ensayo aprobado.
  Lanzamientos de tareas (§248): fuera del host con entorno XDG/D-Bus/Qt original permitido,
  restaurado sólo para ese hijo. Sin contexto válido, rechazar; no filtrar todo el entorno
  del proceso al informe. KIO ApplicationLauncherJob/KService originales, no interpretar Exec
  ni ejecutar fallback de PID. Recibo CLOEXEC separado de stdout de apps, nueva sesión de
  proceso fuera del kill-group de acciones; no esperar su salida ni cerrar apps al retirar.
  CanLaunchNewInstance es visibilidad de menú, no veto de peticiones explícitas (KDE original).
  Su helper no exportado se adapta por KService público con créditos LGPL, no interposición.
  Cola/bloqueo y comprobación de skin/dirección/PID/inicio siguen obligatorios. Rutas de
  lanzadores puros/acciones específicas: §250 (abajo).
  Lanzadores anclados y Actions (§250): BwmLaunchRouter entre TaskFilterProxyModel y la
  concatenación de KDE; nunca sustituir LauncherTasksModel (TasksModel hace mapFromSource de
  su concatenación para el orden manual). Actions del menú original se identifican contra el
  .desktop (sin mnemónicos de KAcceleratorManager); no matching → enmascarar, nunca lanzar.
  El host desechable lleva KIOSK inmutable run_desktop_files/shell_access=false en su
  XDG_CONFIG_DIRS: ningún KIO job dentro del auxiliar; el handler KDE queda conectado y
  denegado. Lugares (§252): sólo desde la copia de solo lectura de user-places.xbel y casando
  título+icono con KFilePlacesModel; Recientes enmascarados. Acciones de ventana nativas
  (§252) siempre con estado deseado + recibo + relectura, nunca conmutar. «Sin borde» del menú
  KDE 6.7.5 está deshabilitado por la errata CanSetNoBoder de su QML: no parchearlo.
  Proveedor de escritorios en Hyprland real (§254): validar sólo con
  check-desktops-hyprland.py (Hyprland anidado desechable; el módulo nunca se carga en el
  compositor de la sesión). __hyprland_api_get_hash()/client_hash() devuelven const char*:
  comparar como std::string, nunca punteros (el módulo no cargaba por eso).
  Carga en sesión (§255): sólo native-desktops.py startup desde autostart.sh, con opt-in
  ~/.config/bwm/native-desktops.json y guarda contra bucles de fallo; nunca desde un cambio de
  skin ni en caliente. El contador común sólo se envía con la marca de sesión de esta instancia
  y el dispatcher compartido no reintenta entregas aplicadas o inactivas.
  Un `hyprctl reload` devuelve las opciones de plugin a su valor por defecto: `enabled` se
  mantiene en `modules/native_desktops.lua` (módulo cargado + opt-in), o la primera recarga
  (cambio de skin, atajos) retira el proveedor hasta otro inicio de sesión (§310).
  Activación entre salidas (§262): workspace ya activo → sólo Actions::focusMonitor;
  inactivo → sólo changeWorkspace por objeto. No encadenar ambos: con destino vacío
  y no_warps la segunda acción puede devolver el foco al puntero. Ruta v2 validada en
  sesión (§263, LG/10 → MSI/1): no repetir login/ciclo aceptado sin cambios nuevos.
  No confundir regresión con cuerpos nativos
  sobre andamiaje de datos con prueba de compositor/Wayland real.
  Vida de TaskThumbnail (§240): QQuickItem::~QQuickItem emite windowChanged después de
  destruir miembros derivados; QObject auto-disconnect llega tarde. Desconectar nuestras
  conexiones en el destructor derivado antes de liberar State, conservando destroyed/Qt/QML
  ajenos. Padre C++ puede haber emitido windowChanged durante construcción base: observar
  también window() inicial. Probar destrucción/reparentado/ventana padre, no sólo carga QML.
  «Obtener nuevos» sin diálogo (--kns-*, kns-cycle.py): sólo raíces XDG temporales, preguntas
  KNS siempre Cancelar; no cargar widgets que ejecutan órdenes sin revisarlos. Paquetes con
  KPlugin.ServiceTypes sin KPackageStructure no los lista KPackage 6.29 ni Plasma: no forzarlos.
  Páginas: sólo claves de main.xml y saveConfig() antes de Aplicar, como AppletConfiguration.qml.
  CLI de kwin-window: to-screen MONITOR [ADDRESS], con --pid antes del subcomando;
  no invertir los posicionales. Los fixtures deben probarse contra el parser real.
  kwin_area vive en el watch único de kde-config-bridge: sigue reserved real para ejes BWM
  maximizados, sin remaximizar ni escribir restauración/presnap. Respeta Force KDE, opt-outs,
  fullscreen/especiales/minimizadas y transición. Cambiar su Python exige reiniciar el puente
  existente (restart o --refresh-area-watcher del ensayo), no compositor/plugins/Quickshell.
  Ese observador queda activo y puede reajustar ventanas BWM ya maximizadas. El marcador
  privado sólo confirma baseline/proceso; la aceptación dinámica requiere medir al aparecer
  y retirar el panel sin remaximizar. Validado en sesión por el usuario para MSI inferior,
  escala 1/giro 0 y modo completo (§208); no extender a otras combinaciones ni takeover.
  R5: PanelViewHost guarda en plasmashellrc sólo con los Ajustes del panel abiertos
  (userConfiguring, como PanelView); fuera son vista previa. Longitud por defecto FillAvailable:
  una prueba con min/maxLength fijos debe pedir panelLengthMode=2 (Custom).
  Cambio de borde con el diálogo abierto: adoptLocation mueve la misma superficie (§304);
  sin diálogo el runtime recrea la vista (R4). Medir el diálogo en Hyprland con
  check-edit-mode-session.py (sin dispositivos de entrada), no con clics virtuales.
  Otras escalas/giros: probar en una salida headless temporal (r4-geometry-check.py, §302),
  nunca reconfigurando los monitores físicos. Un monitor sin descripción (sin EDID) no debe
  invalidar la instantánea de todas las salidas: la firma en memoria usa entonces el conector.
- Kitty recuerda también el estado maximizado: `remember_window_size no` evita restaurarlo. La regla global
  `suppress-maximize-events` bloquea peticiones de maximizado de apps (también botones CSD); el compositor
  conserva el control manual y las peticiones de fullscreen de juegos/vídeo siguen permitidas.
- **`OMARCHY_PATH`** = `~/.config/hypr/omarchy` (`environment.lua`): las piezas de Omarchy buscan ahí `bin/`,
  `default/i18n`, `themes/` y `shell/plugins/…` (enlaces a los shims y plugins vendidos). Sin ella fallan en silencio
  (agentes, recordatorios, Elsewhen). Un plugin nuevo que la use necesita su enlace bajo `shell/plugins/`.
- Omarchy usa `pacman`/AUR: al portar sus scripts, cámbialo por emerge/flatpak/`qlist` y avisa del paquete con
  `scripts/bwm-require.sh`.
- **Foco y puntero en Breeze (Hyprland 0.56):** `ClickToFocus` equivale a `input:follow_mouse = 2` (el puntero
  y el scroll siguen al ratón sin cambiar el foco activo hasta el clic); `follow_mouse = 0` bloquea
  `wl_pointer.enter` en ventanas inactivas y rompe el scroll sin clic. Además, los hooks de
  `m_events.input.mouse.button` (como `breezebars`) corren antes de `CInputManager::processMouseDownNormal`, que
  omite `setPointerFocus` si `focusState()->window()` ya es la ventana bajo el cursor: nunca llames a
  `fullWindowFocus` cuando el plugin deja pasar el clic (`!info.cancelled`).
- **Tooltips y foco de popups en Breeze (Quickshell):** `PlasmaCore.ToolTipArea` instancia
  `PlasmaQuick::ToolTipDialog` (`org_kde_plasma_shell`), que aparece centrado y rompe el primer clic del
  panel/bandeja; usar `PlasmaTheme.ToolTipArea` (`PopupWindow` pasivo). En `TrayPopup.qml`, activar
  `HyprlandFocusGrab` ~50 ms después de abrir para no congelar el puntero antes del mapeo del popup.
- **Capas *on demand* en Hyprland:** el puntero que solo pasa por encima de una capa con
  `KeyboardInteractivityOnDemand` le da el foco de teclado (`InputManager::mouseMoveUnified`), aunque
  `follow_mouse = 2`. Un `PlasmaCore.Dialog` con `hideOnWindowDeactivate` se oculta entonces sin clic
  (R5: barra «Añadir widgets…» frente al panel en edición): el cierre por clic fuera va por la captura de foco.

## 6. Cómo probar

- **Copias de prueba de QML con acciones reales** (bloquear, suspender, apagar, IPC al shell real): sustituye
  las llamadas y comprueba con `grep` que no quedó **ninguna** sin sustituir antes de ejecutar. Incidente
  2026-11-08: una línea sin `;` escapó al `sed` y la prueba suspendió el PC del usuario.
- Hyprland: `hyprctl reload`, `hyprctl configerrors`, `Hyprland --verify-config --config <archivo>`.
- Quickshell: `qs -c ii log` (errores de la instancia real; busca «failed to load», `ReferenceError`, `TypeError`,
  «is not a type»), `qs -c ii ipc show` (un panel que no carga **desaparece**), `qs -c ii ipc call <target> <función>`.
  «Handler was registered but will not be used» con dos monitores es esperado.
- Ajustes sin abrirlos a la vista: `SETTINGS_PAGE=<nombre|índice> timeout 8 qs -p ~/.config/quickshell/ii/settings.qml`
  con la regla temporal al workspace 9, y mira su salida.
- Capas visibles: `hyprctl layers -j` (namespaces `omarchy-*`). Capturas: `grim -g "x,y wxh"` (principal, MSI, en `0,720 2560x1440`).
- Python/bash: `python3 -m py_compile`, `bash -n`.
- Requisitos: `./install.sh --check` o `bwm check [--skin id] [--distro arch|fedora|…]` (sólo lee; `--distro`
  enseña los comandos de otra distribución). La bienvenida no se renderiza con `QT_QPA_PLATFORM=offscreen`
  (Quickshell necesita Wayland): para verla, ábrela flotando en un workspace visible y captura su recuadro.

## 7. Pendiente

Lista completa en `BWM_CONTEXT.md` §2.6 (menú Estilo de Omarchy, layouts de workspace, atajos de ventanas,
Install/Remove, web apps, compartir, Setup…; Qt sin recarga en vivo; entorno de pruebas con `$HOME`).

- Estado de Git: consulta `git status --short --branch` y `git log -1 --oneline`; no deduzcas el
  estado actual de un hash escrito en la documentación. Un commit local no implica push.
