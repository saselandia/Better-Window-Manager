# Arquitectura del port de KDE Plasma a Breeze

> Resultado de la **fase 0** de `docs/BREEZE_PLAN.md` (2026-11-10). Plasma 6.7.5 y KDE Frameworks
> 6.29.0 de Gentoo estable, Qt 6.11.2, Quickshell 0.3.2, Hyprland 0.56.2. Las pruebas se hicieron con
> archivos y configuraciones aisladas en el scratchpad, sin tocar la skin Breeze en uso.

## 1. Paquetes instalados

Instalados por el usuario:

```bash
printf '%s\n' 'kde-frameworks/kconfig qml' 'kde-frameworks/prison qml' 'dev-qt/qtmultimedia qml' 'kde-plasma/plasma-workspace -semantic-desktop' | sudo tee /etc/portage/package.use/bwm-plasma
```

```bash
sudo emerge --ask --noreplace kde-frameworks/ksvg kde-plasma/libplasma kde-plasma/plasma5support kde-plasma/kdecoration kde-plasma/breeze kde-plasma/aurorae kde-plasma/systemsettings kde-plasma/plasma-workspace kde-plasma/plasma-nm kde-plasma/plasma-pa kde-frameworks/bluez-qt
```

Son 75 paquetes. plasma-workspace arrastra **kwin**, kwin-x11, kscreenlocker y kglobalacceld; se
instalan pero BWM no los ejecuta. Con `-semantic-desktop` no se instala baloo.

**Descartados:**

- **kscreen:** su módulo de kded podría reconfigurar los monitores, que son de BWM.
- **plasma-desktop:** Kickoff y el gestor de tareas se leen de su código; no hace falta instalarlo.
- **bluedevil:** basta con `bluez-qt`.

Están declarados en `config/hypr/skins/requirements.json` y como `recommends` de
`skins/plasma/skin.json`. Pasarán a `requires` en la fase en que el código dependa de ellos.

## 2. Resultados de las pruebas

| Prueba | Resultado |
| :--- | :--- |
| **a. KSvg en Quickshell** | ✅ `import org.kde.ksvg` y `KSvg.FrameSvgItem` pintan `widgets/panel-background`, `dialogs/background` y `widgets/arrows` del estilo de Plasma activo. Con un tema de terceros (Layan, desde su repositorio de GitHub, montado en un `XDG_DATA_HOME` aislado) cambian el panel, los diálogos, los botones, los deslizadores y las flechas. Comprobado con imágenes en `qml6` sin pantalla. En `qs -p` las importaciones cargan sin errores; la captura de la ventana no se pudo hacer porque estaba en un workspace oculto. Con el desktoptheme `default` (Breeze), los colores siguen al esquema de color de `kdeglobals`. |
| **b. PlasmaComponents 3 y Kirigami** | ✅ Funcionan dentro de Quickshell `PC3.Button`, `ToolButton`, `Label`, `Slider`, `CheckBox` y `TextField`. `Kirigami.Theme` lee los colores de `kdeglobals` también en el proceso real, aunque el shell use `QT_QPA_PLATFORMTHEME=gtk3`. En Plasma 6 `PlasmaCore.Theme` ya no existe: los colores van por Kirigami. **Recarga en vivo:** reescribir `plasmarc` a mano **no** recarga; `kwriteconfig6 --notify` (o `plasma-apply-desktoptheme`) sí, porque libplasma escucha con `KConfigWatcher` la señal de D-Bus de KConfig. Todo lo que BWM escriba en archivos de KDE tiene que hacerse con notificación (KConfig `Notify` o `kwriteconfig6 --notify`). |
| **c. Plasmoides reales** | ❌ Como shell no sirven. `plasmawindowed` carga el reloj y la bandeja con errores (falta el paquete de shell y `compactRepresentationExpander`); libtaskmanager espera `PlasmaWindowManagement` de KWin, que Hyprland no tiene; la bandeja **intenta registrar `org.freedesktop.Notifications`** (falló porque ya había dueño); Kickoff y los iconos de tareas no están, porque son de plasma-desktop. En Plasma 6 los plasmoides vienen compilados dentro de `.so` (`/usr/lib64/qt6/plugins/plasma/applets/`). ✅ En cambio **sus módulos de datos sí funcionan fuera de Plasma**: `org.kde.plasma.private.volume` (4 salidas, 2 entradas, 3 flujos), `org.kde.plasma.networkmanagement` (`NetworkModel`, 5 redes), `org.kde.plasma.private.mpris` (4 reproductores) y `org.kde.bluezqt` (necesita esperar a que inicialice). `org.kde.plasma.private.kicker` carga (`RootModel` con sus 4 secciones), pero en la prueba las listas de apps salieron vacías aun con `XDG_MENU_PREFIX=plasma-` y `kbuildsycoca6`: queda pendiente para la fase 4. |
| **d. Decoraciones** | ✅ **Se pueden usar las decoraciones reales fuera de KWin.** Un programa de 150 líneas (`DecorationBridge` + `DecoratedWindowPrivateV4` + `DecorationSettingsPrivateV2`, cabeceras privadas instaladas por kdecoration) carga `org.kde.breeze` y `org.kde.kwin.aurorae` con `KPluginFactory` y los pinta en un `QImage`. Breeze tarda 15 ms en iniciarse y ~1 ms en pintarse. Salen bien Breeze Dark y Breeze Light (colores del grupo `[WM]` del esquema), el hover del botón de cerrar, el estado inactivo y el tema Aurorae Layan de terceros (66 ms en iniciarse, ~0,9 ms en pintarse). Los eventos de ratón llegan: el clic en cerrar produce `requestClose()` y el hover, `requestShowToolTip("Close")`. Trampa: KDecoration3 usa estado con doble búfer y el anfitrión debe llamar a `deco->apply(deco->nextState()->clone())`; si no, los bordes valen 0. `color()` del cliente hay que implementarlo leyendo el esquema (como `kwin/src/decorations/decorationpalette.cpp`). |
| **e. KCMs y herramientas de temas** | ✅ Cargan sin errores graves con `kcmshell6` (sin pantalla, sin KWin ni plasmashell): colors, desktoptheme, icons, cursortheme, fonts, style, kwinrules, kwinoptions, kwinscreenedges, kwin_virtualdesktops, animations, componentchooser, autostart, regionandlang, nightlight, wallpaper, soundtheme, networkmanagement y users. ⚠️ Avisos: `kcm_lookandfeel` busca `org.kde.plasmashell` (sólo para la disposición); `kcm_kwintabbox`, `kcm_notifications` y `kcm_screenlocker` buscan kglobalaccel (atajos); `kcm_kwindecoration` avisa de un `DecorationThemeProvider` de Breeze. **No se comprobó visualmente ninguno** ni se aplicó nada desde ellos. `plasma-apply-colorscheme`, `plasma-apply-desktoptheme` y `lookandfeeltool -l/-a` funcionan en una configuración aislada. Ojo: `lookandfeeltool -a` escribe `kdeglobals`, `plasmarc`, `gtkrc`, `gtkrc-2.0`, `Trolltech.conf` y `~/.config/kdedefaults/{kdeglobals,kwinrc,plasmarc,kcminputrc,ksplashrc,package}` (con **el cursor** incluido). |

## 3. Arquitectura elegida por pieza

| Pieza | Arquitectura | Por qué |
| :--- | :--- | :--- |
| **Tema (F1)** | Archivos reales de KDE (`kdeglobals`, `plasmarc`, `kwinrc`, `breezerc`, look-and-feel) escritos con `plasma-apply-*`/`lookandfeeltool` o KConfig con notificación. El shell los lee con Kirigami, KSvg y PC3. | Es el formato original; se recarga en vivo (prueba b). |
| **Panel, Kickoff, bandeja y applets (F3–F5)** | **Portar el QML** de plasma-desktop y plasma-workspace (v6.7.5) a `modules/plasma/…` dentro de Quickshell, usando KSvg, PC3 y Kirigami reales. El attached `Plasmoid` se sustituye por un objeto propio (`PlasmoidShim.qml`: `configuration`, `location`, `formFactor`, `expanded`, `status`, `title`, `icon`…) con el mínimo de cambios marcados `// BWM:`. **Datos:** los módulos de KDE que funcionan (volume, networkmanagement, mpris, bluezqt; kicker si la fase 4 lo hace funcionar) y, donde dependen de KWin o de plasmashell, los servicios de BWM y Quickshell (tareas y ventanas desde Hyprland, avisos con el servidor de BWM, bandeja con `SystemTray` de Quickshell). | Prueba c: los plasmoides no corren como shell, pero su QML y sus datos sí son reutilizables. |
| **Decoraciones (F6)** | Proceso auxiliar **`bwm-decorator`** (C++/Qt, en `src/bwm-decorator/`) que implementa `DecorationBridge` y carga **cualquier** decoración de KDecoration3 (Breeze, Aurorae y C++ de terceros como Klassy) según `kwinrc [org.kde.kdecoration2]`. Para cada ventana recibe el estado (tamaño, escala, activa, título, clase o icono, maximizada, bordes de pantalla, eventos de puntero) y devuelve bordes, zonas de redimensionado, la imagen de la decoración (memoria compartida memfd + daños), la sombra y las peticiones de los botones (cerrar, maximizar, minimizar, menú, tooltip, mantener encima o debajo, en todos los escritorios). El plugin **`breezebars`** se queda en pegamento del compositor: reserva el espacio, compone la textura, reenvía el puntero, ejecuta las peticiones y dibuja la sombra. Nada de Qt dentro de Hyprland (regla 1). Si el auxiliar no está, el plugin dibuja una barra plana con el título (el código cairo actual) y lo relanza con `bwm_session.spawn()`. Durante un redimensionado reutiliza la última imagen estirando el centro hasta que llega la nueva. | Prueba d: compatibilidad total con las decoraciones de la KDE Store; pintar cuesta ~1 ms. Reimplementar Breeze en cairo sólo cubriría Breeze y Aurorae. |
| **CSD (F7)** | En el plugin y el compositor, la misma decisión que KWin: preferir server-side en xdg-decoration y kde-server-decoration, client-side si la app lo pide o no habla el protocolo, `_MOTIF_WM_HINTS` y `_GTK_FRAME_EXTENTS` en XWayland, y reglas de `kwinrulesrc` («sin barra ni borde»). Una sola respuesta expuesta (`hyprctl breezebars-csd`) que usan también `placement.lua`, `quick-tile.py` y `bwm_windows`. | Sin cambios respecto al plan; no hay prueba propia en F0. |
| **Ventanas: min/max, menús, reglas, snapping (F8–F10)** | Módulo de la skin que traduce las acciones de KWin (`useractions.cpp`, `kwinbindings.cpp`, `rules.cpp`, quick tiling y tiles de Plasma 6) a Hyprland. El menú de ventana es QML con PC3 (se abre por IPC desde el plugin o el auxiliar). Las reglas de `kwinrulesrc` se traducen al cargar. | Sin cambios respecto al plan. |
| **Preferencias del sistema (F11)** | Nuestra ventana estilo systemsettings, con los **KCMs reales** de la tabla de la prueba e embebidos (KCMUtils o `kcmshell6`) para Apariencia y parte de Gestión de ventanas. Páginas comunes de BWM para lo compartido (pantallas, atajos, inicio automático, apps predeterminadas, inactividad, red, Bluetooth, sonido). Sin `kcm_kscreen`, `kcm_lookandfeel` con disposición de escritorio, actividades, efectos ni scripts de KWin, KWin X11, móvil ni teclado virtual. | Prueba e: cargan sin KWin; falta comprobarlos a la vista. |
| **Alt+Tab, OSD, bloqueo (F12)** | Port del QML de `kwin/src/tabbox/switchers` y del paquete look-and-feel Breeze (plasma-workspace `lookandfeel/`), con el que traiga el tema global si lo hay. | Paquetes look-and-feel instalados: `org.kde.breeze(dark,twilight).desktop`. |

## 4. Carpetas nuevas de la skin

```
config/quickshell/ii/modules/plasma/        QML de Breeze (sustituye a modules/ii/plasma*)
  theme/       PlasmaTheme (singleton), PlasmoidShim
  panel/       contenedor del panel y applets portados (taskmanager, digitalclock, systemtray…)
  kickoff/     Kickoff portado
  applets/     red, sonido, Bluetooth, avisos, multimedia, batería, portapapeles
  windowmenu/  menú de ventana de KWin
  tabbox/ osd/ lock/
config/hypr/skins/plasma/
  hypr/        animations, misc, placement, kwin.lua (generado), kwinrules.lua
  scripts/     plasma-theme.py, kde-config-bridge.py, kwin-window.py
src/breezebars/      plugin de Hyprland (antes src/hyprbars)
src/bwm-decorator/   auxiliar de decoraciones (Qt + KDecoration3)
```

Cada carpeta portada lleva un `README.md` con el origen (proyecto, etiqueta y rutas) y las líneas
`// BWM:`. Las licencias van en `THIRD_PARTY_NOTICES.md` (GPL-2.0-or-later y LGPL-2.1-or-later de KDE).

## 5. Archivos de configuración de KDE

**Quién manda:** «BWM» = lo escribe el puente (F2) desde la configuración común (regla 14);
«KDE» = lo escriben los KCMs y las herramientas de temas, y Breeze lo lee.

| Archivo | Grupo/clave | Manda | Uso |
| :--- | :--- | :--- | :--- |
| `kdeglobals` | `[Colors:*]`, `[WM]`, `[General] ColorScheme`, `AccentColor` | KDE | Esquema de color: apps Qt, Kirigami, panel y decoraciones |
| `kdeglobals` | `[Icons] Theme` | KDE | Iconos de Breeze |
| `kdeglobals` | `[General] font, fixed, smallestReadableFont…` | KDE | Fuentes de la skin |
| `kdeglobals` | `[KDE] widgetStyle`, `AnimationDurationFactor`, `SingleClick` | KDE | Estilo Qt y comportamiento |
| `plasmarc` | `[Theme] name` | KDE | Estilo de Plasma (desktoptheme) |
| `kwinrc` | `[org.kde.kdecoration2] library, theme, ButtonsOnLeft/Right, BorderSize` | KDE | `bwm-decorator` y plugin |
| `kwinrc` | `[Windows]` (FocusPolicy, Placement, TitlebarDoubleClickCommand, BorderSnapZone, WindowSnapZone…) | KDE | F2, F8 y F10 → opciones de Hyprland/breezebars |
| `kwinrc` | `[TabBox] LayoutName` | KDE | Cambiador de Alt+Tab (F12) |
| `kwinrc` | `[Desktops]` | **BWM** | Workspaces comunes: sólo se exportan |
| `kwinrc` | `[NightColor]` | **BWM** | Kelvin común (`nightlight.py`) |
| `breezerc` | todo | KDE | Opciones de la decoración Breeze |
| `kwinrulesrc` | todo | KDE | Reglas de ventana (F10) |
| `kcminputrc` | `[Mouse] cursorTheme, cursorSize` | **BWM** | Cursor común: se exporta y **pisa** a `kdedefaults/kcminputrc` |
| `kcminputrc` | `[Keyboard] RepeatDelay, RepeatRate` | **BWM** | Opciones efectivas del compositor (incluye la configuración del usuario); §9 |
| `kxkbrc` | `[Layout]` | **BWM** | Distribución de teclado común |
| `mimeapps.list` | — | **BWM** | Apps predeterminadas comunes (`default-apps.py`) |
| `ksplashrc`, `kscreenlockerrc` | — | KDE | Tema global (sólo lo que Breeze use) |
| `kdedefaults/*` | — | KDE (lookandfeeltool) | Plasma añade `~/.config/kdedefaults` a `XDG_CONFIG_DIRS`: hay que hacerlo en el entorno de la sesión (`environment.lua`) para que los temas globales funcionen igual que en Plasma |
| `gtkrc`, `gtkrc-2.0`, `Trolltech.conf` | — | **BWM** | Los escribe lookandfeeltool: el puente debe volver a dejarlos como los quiere `gtk-theme.py` |
| `kded5rc` | `[Module-*] autoload` | **BWM** | Módulos de kded desactivados (§6) |

Al salir de Breeze, `kdeglobals` también lo leen default (plasma-integration) y Retro: la fase 2
lo coordina con `bwm_icons.write_kdeglobals` (ciclo de salida en §9).

## 6. Servicios que no deben arrancar o chocar

| Servicio | Problema | Medida (comprobada) |
| :--- | :--- | :--- |
| Inicio automático de plasmashell, xembedsniproxy, gmenudbusmenuproxy y kaccess (`/etc/xdg/autostart`) | Llevan `OnlyShowIn=KDE` | No arrancan con `XDG_CURRENT_DESKTOP=Hyprland`. Mantenerlo así: no poner `KDE` en esa variable. |
| **kded6** (activado por D-Bus) | Al activarse carga sus módulos automáticos: `statusnotifierwatcher` (bandeja), `networkmanagement` (agente de secretos de NM, choca con nm-applet), `audioshortcutsservice` y `mprisservice` (teclas multimedia), `lookandfeelautoswitcher` (cambia el tema solo), `appmenu`, avisos de dispositivos o espacio… | `~/.config/kded5rc` con `autoload=false` en esos módulos (**en KF6 el archivo sigue llamándose `kded5rc`**: con `kded6rc` no tiene efecto). Comprobado: tras reiniciarse, kded6 sólo carga `ktimezoned`. Ojo: un cliente puede cargar un módulo bajo demanda (`loadModule`) y eso no se puede desactivar; el QML portado no debe usar módulos de kded. |
| `org.freedesktop.Notifications` | plasma-workspace añade `org.kde.plasma.Notifications.service` con el mismo nombre que el de notification-daemon; con dos archivos, dbus-daemon no garantiza cuál activa | `~/.local/share/dbus-1/services/org.freedesktop.Notifications.service` (tiene preferencia) con `plasma_waitforname --timeout 25`: si no hay dueño, espera a que el shell de BWM o swaync lo tome y nunca lanza otro demonio |
| kactivitymanagerd, kwalletd6 y ksecretd | Se activan por D-Bus al usar kicker, los KCMs o plasma-nm | Inofensivos (no reclaman nombres de BWM), pero `ksecretd` se convierte en el dueño de `org.freedesktop.secrets` al activarse; antes no había ninguno en marcha. Si la skin usa kicker, kactivitymanagerd será parte de Breeze (recientes y favoritos de Kickoff). |
| kglobalacceld | Instalado; sin KWin no puede capturar teclas | No se usa; los atajos son de `keybinds-manager.py` |
| polkit-kde-agent | No arranca solo | Un solo agente por sesión (§5 de `CLAUDE.md`) |
| KWin, kscreenlocker, ksmserver, `plasma-login-sessions` (sesión «Plasma» en SDDM) | Instalados | No se ejecutan; el autologin sigue entrando en `hyprland.desktop` |

`~/.config/kded5rc` y el servicio de D-Bus de usuario los creó la fase 0 a mano en este equipo. La
fase 2 (`kde-config-bridge.py guards`) los mantiene, y el instalador los prepara
si se instala plasma-workspace.

## 7. Cambios en `BREEZE_PLAN.md`

- **F1:** el aplicador debe usar KConfig con notificación; `lookandfeeltool` pisa
  GTK/Trolltech/cursor: envolverlo y reparar después; añadir `~/.config/kdedefaults` a
  `XDG_CONFIG_DIRS` en Breeze.
- **F2:** el puente es dueño de `kded5rc`, del servicio de D-Bus de avisos y de la tabla de §5.
- **F3–F5:** port del QML con `PlasmoidShim`; datos de los módulos de KDE probados; nunca módulos de
  kded ni el servidor de avisos de Plasma.
- **F4:** investigar por qué `Kicker.RootModel` sale vacío; si no se resuelve, usar AppSearch con
  categorías del menú `plasma-applications.menu`.
- **F6:** pasa a ser `bwm-decorator` (auxiliar con KDecoration3) + `breezebars` como pegamento,
  en lugar de reimplementar Breeze en cairo. Es la fase más grande: conviene partirla en F6a
  (auxiliar y protocolo, probados sin Hyprland) y F6b (plugin, con reinicio de sesión).
- **F11:** KCMs reales para Apariencia; probarlos a la vista antes de decidir cuáles se embeben.

## 8. Sin probar

- Captura de los controles de Plasma dentro de una ventana real de Quickshell (sólo carga y
  valores). La imagen se comprobó con `qml6` sin pantalla.
- Ver los KCMs abiertos y aplicar cambios desde ellos.
- `Kicker.RootModel` con apps (vacío en la prueba) y `RunnerModel`.
- `bluezqt` tras inicializarse del todo.
- Escala fraccionaria y HiDPI en `bwm-decorator`, decoraciones C++ de terceros (Klassy…) y sombras.
- Rendimiento del envío de la imagen de la decoración (memfd) al plugin durante un redimensionado.

## 9. Fase 2: autoridad y sincronización de configuración

Implementado el 2026-11-11. El código original sigue en KDE (`kwinrc`, `kdeglobals`, etc.);
`~/.local/state/bwm/plasma/bridge-state.json` sólo guarda lo necesario para resolver cambios y
retirar exportaciones. No es un formato de temas. El archivo Lua generado en ese directorio
es una caché de traducción; `skins/plasma/hypr/kwin.lua` lo aplica antes de la configuración del
usuario. Nunca se escribe `~/.config/bwm/user/*`.

| Ajuste | Fuente BWM / equivalente KDE | Autoridad y dirección | Alcance real en F2 |
| :--- | :--- | :--- | :--- |
| Cursor y tamaño | `hypr/modules/cursor.lua` → `kcminputrc [Mouse] cursorTheme,cursorSize` | BWM → KDE; corrige cambios de un KCM/tema global | El valor local prevalece sobre `kdedefaults/kcminputrc`. Hook de `cursor-manager.py` antes de su recarga. No se aplica un cursor recibido de KDE. |
| Kelvin y luz nocturna | `~/.local/state/bwm/nightlight.json`, `light.night.colorTemperature` → `kwinrc [NightColor] Active,Mode,NightTemperature,DayTemperature` | BWM → KDE | `Mode=0` (constante en Plasma 6.7.5), día a 6500 K. La programación y el motor siguen siendo de BWM: no arrancar el de KWin. Hook de `nightlight.py`; el archivo de usuario tiene prioridad sobre el Kelvin exportado. |
| Distribuciones y opciones XKB | Opciones efectivas de Hyprland (`input:kb_layout,kb_variant,kb_model,kb_options`) → `kxkbrc [Layout] Use,LayoutList,VariantList,Model,Options,SwitchMode` | BWM → KDE | Se consulta el compositor, por lo que se ven los ajustes de `user/hyprland.lua`. No se ejecuta `setxkbmap` ni el KCM de teclado para aplicarlos. |
| Repetición / Bloq Num | `input:repeat_rate,repeat_delay,numlock_by_default` → `kcminputrc [Keyboard] RepeatRate,RepeatDelay,KeyRepeat,NumLock` | BWM → KDE | `NumLock=0` activado, `1` desactivado; `KeyRepeat=repeat/none`. Valores de los `.kcfg` de plasma-desktop 6.7.5. Los cambios del archivo Lua común se observan con inotify. |
| Apps predeterminadas | `mimeapps.list`, `default-apps.py`, `apps.terminal` → el mismo `mimeapps.list`, `kdeglobals [General] TerminalApplication,TerminalService` | Fuente XDG común; terminal BWM → KDE | Para navegador, archivos y editor KDE ya lee el mismo archivo XDG: no se crea una copia. Un KCM que edite `mimeapps.list` edita directamente la fuente común. No se importa `apps.*` desde un tema de KDE. Gestor de tareas sin equivalente KDE genérico. |
| Pantallas, escala, giro, posición y duplicación | `monitor-manager.py`, `monitors.lua`, compositor → KScreen | BWM | KScreen Wayland necesita el protocolo de gestión de salidas de KWin; no tiene un archivo que represente fielmente esta sesión Hyprland. No se escribe un falso `kscreen/*` ni `kwinoutputconfig.json`, ni se inicia kded-kscreen. La página Pantallas de F11 usa el gestor común. Identidades persistentes `desc:`. |
| Workspaces | `bar.workspaces.shown` → `kwinrc [Desktops] Number,Rows` | BWM → KDE | Numeración global; no se importan escritorios/actividades de KWin. `Rows=1` sólo describe la presentación. |
| Idioma de interfaz | `language.ui` → `plasma-localerc [Translations] LANGUAGE` | BWM → KDE | `auto` quita la sobrescritura y deja el idioma del sistema. No cambia `LANG`, los formatos regionales ni `/etc/locale*`. El idioma del menú Omarchy sigue en su proveedor propio y no se importa a Breeze. |
| Fuente general y mono | `appearance.fonts.main,monospace` ↔ `kdeglobals [General] font,fixed` | Bidireccional, propia de Breeze | Se conservan tamaño, estilo y resto de QFont al cambiar la familia desde BWM. Si cambian ambos a la vez gana KDE; `user/shell.jsonc` siempre gana al final y se refleja también en KDE. |
| Fuente de lectura/título | `appearance.fonts.reading,title` ↔ `kdeglobals [General] menuFont`, `[WM] activeFont` | Igual que las anteriores | El título real está en `[WM] activeFont`, según `fontssettings.kcfg`. Otras fuentes de KDE (`toolBarFont`, `smallestReadableFont`) se conservan y las leen los componentes KDE. |
| Iconos, esquema de color, acento, estilo Qt y tema global | `kdeglobals [Icons] Theme`, `[Colors:*]`, `[General] ColorScheme,AccentColor`, `[KDE] widgetStyle,LookAndFeelPackage` | KDE → Breeze | El vigilante llama a `plasma-theme.py sync` sólo cuando cambia la paleta/aspecto; las apps se recolorean sin reiniciarse. `bwm_icons.write_kdeglobals` sigue sin escribir en Breeze. |
| Estilo de Plasma | `plasmarc [Theme] name` | KDE → Breeze | libplasma recibe `ConfigChanged`; `PlasmaTheme` también vigila el archivo. No se inventa una paleta de panel. |
| Clic simple/doble para abrir archivos | `kdeglobals [KDE] SingleClick` | KDE, propio del aspecto/comportamiento Breeze | Las apps KDE lo leen directamente. No cambia el comportamiento de Nautilus ni las otras skins. Los lanzadores portados lo podrán consumir. |
| Intervalo de doble clic | `kdeglobals [KDE] DoubleClickInterval` | KDE | Qt lo lee; el plugin actual tiene un intervalo fijo. El intervalo de la barra se completa en F6b/F8; no se presenta como soportado. |
| Animaciones | `kdeglobals [KDE] AnimationDurationFactor` → `hl.config animations.enabled`, velocidades de las curvas Breeze | KDE → Hyprland | Cero desactiva; el factor escala duración, inverso de `speed`. Las animaciones de QML que no usan aún KDE se portan en F3–F5/F12. |
| Política de foco | `kwinrc [Windows] FocusPolicy` → `input.follow_mouse` | KDE → Hyprland; usuario Lua al final | `ClickToFocus=0`; las políticas de seguimiento se aproximan con `1`. `AutoRaise`, `ClickRaise`, `DelayFocusInterval` y diferencias entre las tres políticas de seguimiento no tienen traducción exacta en F2 y se conservan. |
| Colocación | `kwinrc [Windows] Placement` → `placement.lua` | KDE → Hyprland | Smart/mínimo solapamiento, Centered, ZeroCornered, UnderMouse, Random, Maximizing y NoPlacement. Diálogos de la misma app y ventanas con regla propia se conservan. OnMainWindow se delega a Hyprland. |
| Encaje magnético | `kwinrc [Windows] BorderSnapZone,WindowSnapZone` → `general.snap.monitor_gap,window_gap` | KDE → Hyprland | Distancias enteras (la API Lua rechaza `19.0`). Ambos cero desactivan. `CenterSnapZone`, `SnapOnlyWhenOverlapping`, esquinas/zonas de mosaico y ElectricBorders quedan para F10. |
| Doble clic de barra | `kwinrc [Windows] TitlebarDoubleClickCommand` → `plugin.breezebars.on_double_click` | KDE → plugin | Maximize, Minimize, Close y Nothing en barras del servidor. Acciones restantes y CSD se completan en F6/F8/F9. Las cadenas de KDE nunca se ejecutan como órdenes. |
| Botones de barra | `kwinrc [org.kde.kdecoration2] ButtonsOnLeft,ButtonsOnRight` | KDE → plugin / auxiliar F6 | El plugin actual permite I/A/X en un solo banco (izquierdo si el derecho está vacío); orden y lado se traducen. Ambos bancos completos, menú, ayuda y demás botones permanecen en KDE y en la caché para F6a/F6b. No se recompila ni recarga el plugin en caliente. |
| Decoración y reglas | `kwinrc [org.kde.kdecoration2] library,theme,BorderSize`, `breezerc`, `kwinrulesrc` | KDE | Se conservan: interpretación de decoraciones en F6 y reglas por ventana en F10. |
| Red/Bluetooth, servicios, bloqueo/OSD, inicio automático y atajos | Gestores comunes y servicios BWM | BWM | No se importan desde temas KDE; F11 usa páginas comunes. No se usan KWin, kglobalacceld, ksmserver ni agentes duplicados para aplicarlos. |

### Ciclo de vida y conflictos

- `kde-config-bridge.py enter` inicia la sesión del puente después de que F1 devuelva el
  `kdeglobals` de Breeze. `export` vuelca lo compartido; `import` sólo sincroniza fuentes propias
  y traduce opciones de ventanas. Ambos son inocuos fuera de Breeze.
- `watch` se lanza con `bwm_session.spawn()`, como hijo de Hyprland. Un candado evita duplicados.
  inotify observa las carpetas reales, incluidos padres de carpetas aún inexistentes, para detectar
  guardados con renombrado atómico. Agrupa cambios durante 300 ms y compara huellas: las escrituras
  propias no vuelven a disparar trabajo. Un JSON incompleto se reintenta sin sobrescribirlo.
- Las escrituras conservan comentarios, grupos anidados y claves desconocidas. Se preparan en un
  archivo temporal, se sincronizan y se renombran sobre el destino real (conservando enlaces).
  Si cambia el archivo durante la preparación, se aborta y reintenta; las operaciones del puente
  tienen candado. Una carrera de otro proceso exactamente entre la última comprobación y el
  `rename` no puede excluirse sin cooperación de ese escritor.
- Cada archivo de KDE modificado emite la señal original de KConfig 6.29:
  `org.kde.kconfig.notify.ConfigChanged(a{saay})`. Sólo una traducción distinta de `kwinrc` provoca
  `hyprctl reload`; los gestores comunes ya tienen su recarga y usan `--no-reload` en el hook.
- Al salir: se detiene el vigilante y se espera a que termine su escritura; se retiran sólo las
  claves exportadas que todavía coinciden con lo escrito por el puente. No se deshace una edición
  ajena posterior. Después F1 guarda el `kdeglobals` de Breeze y la skin entrante genera el suyo.
  Pueden quedar cabeceras de grupos vacíos, sin efecto sobre KDE. Las protecciones de servicios
  permanecen, porque los paquetes de KDE siguen instalados fuera de Breeze.
- El hook genérico de los gestores comunes (`bwm_settings_hooks.py`) se obtiene del manifiesto
  de la skin: `hooks.settingsChanged`. En Breeze apunta al puente. No hay lógica KDE en otras skins.
- `guards` mantiene sólo las claves conocidas de `kded5rc` y el servicio de avisos que BWM creó
  en F0; respeta un servicio propio del usuario. El instalador también lo llama. No descarga ni
  arranca módulos kded; los módulos ya cargados se revisan aparte.

`gtkrc`, `gtkrc-2.0` y `Trolltech.conf` son formatos heredados que krdb/`lookandfeeltool` pueden
escribir. El puente guarda sus valores anteriores al entrar: en GTK1/2 repara sólo el bloque
autogenerado que identifica a KDE Plasma y conserva líneas ajenas añadidas; en Trolltech restaura
sólo las claves Qt4 de krdb (`font`, `GUIEffects`, `Palette`, `KWinPalette`, contraste), conservando
las demás. Se prueba con archivos simulados. Las apps Qt 6 leen `kdeglobals` y GTK sigue las
plantillas comunes. El aplicador de F1 ya evita esas exportaciones; F11 debe usarlo para temas
globales. El puente no ejecuta scripts arbitrarios de paquetes.

### Verificación de F2

Pruebas aisladas en `tests/test_kde_config_bridge.py`: ida/vuelta, archivos y comentarios ajenos,
conflictos entre fuentes, prioridad del usuario, JSON incompleto, enlaces, guardas, números Lua,
inotify con renombrados y carpetas nuevas, ausencia de bucles y recarga sólo al cambiar ventanas.
`tests/test_plasma_placement.py` prueba también Centered, ZeroCornered y NoPlacement.

Prueba real: Retro → Breeze; cursor Miku de 48 a 40 mediante `cursor-manager.py` →
`kcminputrc` mostró `miku-cursor-linux`, `40`. Una escritura KDE de otro cursor se corrigió sola.
Un lote con política de foco y encaje provocó **una** recarga (evento `configreloaded`), el foco
pasó a seguimiento y el encaje se comprobó en 19 después de corregir la conversión a entero.
Después: tamaño 48, archivo `cursor.lua` original y vuelta a Retro; `kdeglobals` idéntico al
inicial, vigilante parado, 11 ventanas con los mismos PID y foco conservado. No hubo capturas.

Pendiente de validación visual: todas las opciones de colocación, botones con el plugin cargado
en la próxima sesión, KCMs embebidos (F11), ajustes de Qt 6 con apps abiertas y un tema global
aplicado directamente por un KCM en vez del aplicador BWM.
