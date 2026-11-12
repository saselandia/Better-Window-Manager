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
| **CSD (F7)** | Política de KWin por negociación Wayland/hints X11, con la excepción GTK de F7 (§12). JSON `hyprctl -j breezebars-csd` y API Lua comparten el marco aplicado con `placement.lua`, `quick-tile.py` y `bwm_windows`. Overrides no_bar/decorate; traducción de NoBorder en F10. | Implementado, compilado e instalado; pruebas de lógica/geometría pasan. Pendiente de sesión nueva y matriz visual (§12). |
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

El detector de conflictos comprueba el dueño D-Bus con `bwm-shell-conflicts.py`, no la
presencia de kded6: ktimezoned puede seguir activo sin interferir. Un kded6 que conserve el
nombre StatusNotifierWatcher sin su objeto sigue bloqueando la bandeja; se comprobó en F12.
Retirar ese proceso liberó el nombre y Quickshell recuperó sus elementos. La acción de resolver
revalida el dueño y termina sólo su PID; no utiliza killall.

## 7. Cambios en `BREEZE_PLAN.md`

- **F1:** el aplicador debe usar KConfig con notificación; `lookandfeeltool` pisa
  GTK/Trolltech/cursor: envolverlo y reparar después; añadir `~/.config/kdedefaults` a
  `XDG_CONFIG_DIRS` en Breeze.
- **F2:** el puente es dueño de `kded5rc`, del servicio de D-Bus de avisos y de la tabla de §5.
- **F3–F5:** port del QML con `PlasmoidShim`; datos de los módulos de KDE probados; nunca módulos de
  kded ni el servidor de avisos de Plasma.
- **F4 (hecha):** `Kicker.RootModel` funciona: hay que llamar a `refresh()`, como Kickoff. Se usan
  los modelos reales de Kicker; los menús `PlasmaExtras.Menu` (QMenu) no sirven desde layer-shell.
- **F6:** pasa a ser `bwm-decorator` (auxiliar con KDecoration3) + `breezebars` como pegamento,
  en lugar de reimplementar Breeze en cairo. Es la fase más grande: conviene partirla en F6a
  (auxiliar y protocolo, probados sin Hyprland) y F6b (plugin, con reinicio de sesión).
- **F11:** KCMs reales para Apariencia; probarlos a la vista antes de decidir cuáles se embeben.

## 8. Sin probar

- Captura de los controles de Plasma dentro de una ventana real de Quickshell (sólo carga y
  valores). La imagen se comprobó con `qml6` sin pantalla.
- Ver los KCMs abiertos y aplicar cambios desde ellos.
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
| Botones de barra | `kwinrc [org.kde.kdecoration2] ButtonsOnLeft,ButtonsOnRight` | KDE → auxiliar (F6b) | Desde F6b los lee `bwm-decorator` y los dibuja la decoración de KDE: ambos bancos y todos sus botones. El plugin sólo traduce I/A/X a un banco para la barra plana de respaldo (sin auxiliar). Enrollar, encima/debajo, ayuda y menú de aplicación no existen en Hyprland: el botón se ve pero no hace nada. |
| Rueda en la barra | `kwinrc [MouseBindings] CommandTitlebarWheel` → `plugin.breezebars.on_wheel` | KDE → plugin | F6b: Raise/Lower (sólo subir), Maximize/Restore y Previous/Next Desktop; el resto no hace nada. |
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

## 10. Fase 3: panel de Plasma (2026-11-11)

modules/plasma/panel sustituye modules/ii/bar/PlasmaBarContent.qml. Se ha adaptado el fondo de
desktoppackage/contents/views/Panel.qml, las representaciones compactas de Task/DigitalClock y
los prefijos originales del gestor de tareas (Plasma v6.7.5). Fuentes, modificaciones y límites en
el README de la carpeta; GPL-2.0-or-later conservada. Quickshell aloja el panel mediante un Loader
con ruta vacía fuera de Breeze: sus dependencias KDE permanecen propias de esta skin.

**Configuración:** bar.plasma, admitida por F3. No se escribe un archivo appletsrc parcial que
pueda confundirse con un anfitrión completo de plasmoides. Workspaces, time.format y servicios
siguen siendo comunes. Las ancladas usan dock.pinnedApps del perfil y el orden de grupos se guarda
en bar.plasma.taskOrder. El editor elige/reordena los seis widgets incluidos; no instala widgets
externos incompatibles.

**Panel:** cuatro bordes, alineación/longitud/grosor, flotación eliminada al tocar una ventana,
SVG de fondo/sombra del estilo activo y opacidad adaptable/opaca/traslúcida. AutoHide, Dodge y
WindowsGoBelow reservan cero; el último permanece visible. Siempre visible reserva sólo el
grosor, como PanelView::updateExclusiveZone en Wayland. La superficie incluye las sombras del SVG;
el hueco flotante se superpone al área útil. Geometría aislada en PanelLogic.js; IPC de diagnóstico:
qs -c ii ipc call plasmaPanel inspect.

**Área útil:** bwm_windows.traditional_box usa reserved real del compositor (lista/diccionario),
incluidos ceros para panel oculto; sólo usa el manifiesto si ese dato no existe. quick-tile.py y
placement.lua ya consumían esa reserva. Popups y Kickoff existentes se adaptan al borde y posición.

**Datos:** TaskbarApps/Quickshell reemplazan el protocolo PlasmaWindowManagement de KWin.
Grupos por app, SVG widgets/tasks, miniaturas ScreencopyView, ancladas, clic central, rueda y
orden por arrastre. El reloj usa org.kde.plasma.clock y PC3 con formato horario común. Bandeja y
applets existentes hasta F5.

**Probado:** ocho casos reales (dos estilos × cuatro bordes), reserva exacta sólo en su borde.
Se retiró una animación de posición que desplazaba el panel al cambiar de orientación; los bordes
se aplican directamente. AutoHide/Dodge reservan cero y pueden ocultarse; WindowsGoBelow reserva
cero y queda visible. Capturas recortadas y borradas. El reinicio de mantenimiento carga el módulo
nuevo. Al volver a Retro se restauran el estilo de Plasma y los ajustes del panel.

**Pendiente:** interacción completa de arrastre/menú/miniaturas, insignias/progreso Unity, zonas
horarias múltiples, applets portados (F5) y alojamiento de plasmoides de terceros. qmllint se
ejecuta con avisos por imports virtuales qs.* y metadatos incompletos de Quickshell/KSvg; la carga
real complementa esta comprobación.

## 11. Fase 5: bandeja y applets (2026-11-11)

Bandeja nueva en modules/plasma/tray y páginas en modules/plasma/applets. Las cinco vistas
anteriores plasmaNetwork/Bluetooth/Audio/Notifications/Calendar se retiran; sus nombres IPC se
conservan en TrayController. Lo cargan los Loader por ruta de Breeze; el panel usa esta bandeja y
el reloj abre su calendario. La ventana expandida sigue el borde/monitor y conserva visible el
panel autooculto. No se instala un anfitrión de plasmoides externos.

**Código original y adaptadores:** AbstractItem/PulseAnimation y eventos SNI de systemtray;
main.qml y componentes de plasma-pa y plasma-nm; main/ExpandedRepresentation de mediacontroller;
CalendarView del reloj; ModelInterface/Summary/Body/ActionContainer de notificaciones;
TextItemDelegate de Klipper; BatteryItem/BrightnessItem de PowerDevil. Bluetooth, encabezados de
historial y base de portapapeles son ports reducidos. Tabla de procedencia/licencias y cambios en
los README de ambas carpetas; fuentes v6.7.5 y textos/expresiones SPDX conservados.

**Autoridad:** Quickshell SystemTray alimenta SNI; Auto/Shown/Hidden por ID estable se guardan en
bar.plasma.trayItems, propios de Breeze. Los applets se crean sólo al abrirlos. Red usa los modelos
originales y Handler de plasma-nm; audio, los de plasma-pa sobre PipeWire/Pulse existente. Bluetooth,
brillo, batería, portapapeles y avisos usan los proveedores comunes de BWM. Se cambia la interfaz,
no la configuración común ni los archivos de texto del usuario.

**Servicios:** nunca KDEDProxy, MicrophoneIndicator.init, GlobalService de plasma-pa ni Globals o
NotificationManager.Server de Plasma. GlobalService.ensureKDEDModule habría activado
audioshortcutsservice y kglobalaccel al pulsar volumen: se reemplaza por Audio de BWM.
Los QMenu de audio/red/velocidad se adaptan a PC3; la bandeja abre sus menús DBus con QsMenuOpener.
No se inicia Klipper, PowerDevil ni Bluedevil. No hace falta instalar paquetes nuevos: los módulos
estaban desde F0 y ahora se declaran requires. El servidor de avisos sigue en services/Notifications
(Breeze/default), y Retro conserva Omarchy; un único dueño. Los toasts nativos respetan el monitor
común, el bloqueo, la expiración y DND; máximo tres simultáneos. El historial sigue siendo común.

**Pruebas:** carga de todas las páginas en qs -p, acciones QtTest de Bluetooth y notificaciones
con datos simulados, modelo SNI y popup expandido simulado, calendario y toast sin servidor adicional.
Las vistas ocultas en workspace 9 no completaban algunas transformaciones antes de los clics:
las comprobaciones de interacción usan una pequeña capa de prueba visible sin foco de teclado.
Red/audio se cargan con controles inhabilitados; nunca se conecta/desconecta ni se cambia un radio
real para probar. Capturas limitadas al contenido de las vistas, revisadas y borradas al terminar.

**Pendiente:** OBEX y asistente avanzado de emparejamiento; KIO/jobs y respuestas en línea;
DND programado; edición/QR y miniaturas del portapapeles; plugins de agenda y ajustes multizona;
perfiles/inhibición de PowerDevil; pruebas de acciones reales de red, audio y brillo y de todos los
menús SNI de terceros. Se ofrecen controles básicos funcionales, no equivalencia completa de todos
los applets. Sus opciones avanzadas y los KCMs se completan en F11.

Validación final F5: 273 pruebas generales OK (52 opcionales omitidas), y 15 pruebas F5 con QtTest
activado OK; verificación de Hyprland y requisitos correctos. qmllint conserva avisos por imports
virtuales y tipos dinámicos; la carga real complementa el análisis. El host de toasts importa
PlasmaCore explícitamente para inicializar el ImageSet de KSvg también en qs -p aislado. Se mantiene
Retro; no se cambió a Breeze ni se reinició el shell. Para incorporar los Loader nuevos, usar
bwm-theme-manager.py set plasma --restart-shell al activar Breeze.

## 12. Fase 7: negociación y fuente única del marco (2026-11-11)

F6b/F7 ya se cargan en la sesión de Breeze y la decoración de sesión responde; sigue pendiente
la matriz física completa de negociación CSD/SSD. El cierre y las correcciones están en §15.

**Hallazgo en las fuentes:** KWin 6.7.5 decide por negociación Wayland o hints X11, mientras
Hyprland 0.56.2 responde Server incluso a Client y limita a cuatro peticiones KDE. El detector
anterior leía lo pedido, no lo aplicado: podía ocultar la barra cuando el cliente ya había
renunciado a la suya. `src/breezebars/CSDDetect.cpp` ahora envuelve los callbacks de creación de
decoraciones y negocia Client/Server; `CSDLogic.hpp` separa la política y el estado puro.
Sin protocolo Wayland no hay barra; sin preferencia se ofrece Server. El modo xdg se aplica
tras ack+commit, incluido el commit vacío inicial; KDE antiguo conserva None y aplica tras
commit sin el límite de cuatro cambios. Si hay ambos, manda xdg. Callbacks originales fuera de
Breeze; hooks específicos de la ABI comprobada del binario 0.56.2, restaurados al finalizar.
Detalles y rutas de las fuentes en `src/breezebars/README.md`.

**XWayland:** Motif decorations=0 o presencia de GTK_FRAME_EXTENTS válido → CSD. Por requisito
F7 cuenta un hint GTK con cuatro ceros; KWin literalmente comprueba valores no nulos: esta
excepción está declarada, no se presenta como igualdad exacta. Conexión XCB separada y asíncrona,
eventos de cambio de propiedades, sin esperas de respuestas dentro del render o IPC. Datos
incompletos → pendiente/sin barra hasta resolverlos. Cache ligada a ventana y PID.

**Overrides:** no_bar=true, decorate=false y fullscreen suprimen el marco; false restaura el
automático, nunca fuerza doble barra. F10 sigue pendiente para traducir NoBorder de kwinrulesrc.
No se crea una lista de clases. Las expresiones de apps de csd-audit.py sólo etiquetan pruebas.

**Consumidores:** `hyprctl -j breezebars-csd` (alias hyprbars-csd, API 1) y
`hl.plugin.breezebars.decoration(address,pid)` comparten visibilidad, motivo, estado y los cuatro
bordes efectivos de F6. Python enlaza dirección+PID; placement consulta dentro del proceso y
espera brevemente si el modo inicial aún no está aplicado. traditional_box y quick-tile dejan de
inventar 30 px y cuentan todos los bordes, también Aurorae. Sin plugin: marco cero.

**Requisitos y límites:** no se añaden programas ni bibliotecas ajenas al sistema (XCB ya usado,
libdl del sistema); el script de auditoría se declara en parts del manifiesto. No se ejecuta Qt
en Hyprland, no cambia el plugin de Retro ni se escriben archivos bwm/user. No se arrancan
servicios KDE adicionales ni se cambia la sesión para probar. El auxiliar F6 sigue siendo el
único proceso Qt de decoraciones. La negociación con clientes reales, hooks en ejecución,
fullscreens y geometría con ambos temas/monitores sólo podrán validarse tras reiniciar sesión.

Pruebas de política/estado, hints X11, ABI exportada, JSON, identidad, cuatro bordes y colocación
con datos simulados pasan. La suite general incluye las comprobaciones de compilación de F6.
Estado y pasos de prueba real: `docs/BREEZE_CSD_RESULTS.md`; herramienta de lectura:
`config/hypr/skins/plasma/scripts/csd-audit.py`. No se tomaron capturas en F7.

Validación automática F7: suite general de 297 pruebas, 53 opcionales omitidas; nueve pruebas
específicas de detección/auditoría pasan. Compilación e instalación con `make install` y
`-fno-gnu-unique`; Python y Lua válidos, `Hyprland --verify-config` correcto, `configerrors`
vacío y `bwm check --skin plasma` correcto. El log del shell existente en Retro conserva avisos
previos (entre ellos propiedades de pantalla nula en Lock.qml); F7 no cambia QML. Ninguna de
estas comprobaciones equivale a cargar el plugin F7 en el compositor.


## 13. Fase 10: reglas de KWin y snapping (2026-11-11)

**Implementado y cargado; pendiente de la lista física de ratón.** No se aumenta
la estimación de compatibilidad por compilación o pruebas con datos simulados.

El puente F2 incorpora `skins/plasma/scripts/kwin_rules.py` y `kwin_tiles.py`. kwinrulesrc se
lee en su formato original (lista ordenada UUID, grupos numéricos antiguos y Enabled). La primera
regla fija cada propiedad; DontAffect bloquea las posteriores. Se generan reglas nativas por
etiqueta en `~/.local/state/bwm/plasma/kwinrules.lua`, cargadas por la skin antes del Lua del
usuario. El mismo vigilante F2 resuelve clase/título/rol/tipo y aplica estados iniciales o forzados,
con identidad dirección+PID. La marca de mapa inicial evita recolocar ventanas preexistentes al
cambiar de skin o reiniciar el puente. Remember escribe sólo claves conocidas al cerrar/salir,
conservando texto ajeno y comprobando conflictos. Las escrituras se agrupan con las de F2;
mientras hay un lote pendiente se suspende la aplicación de reglas. Sin cuota inotify se usan
firmas, sin un segundo servicio. El estado vigilado converge aproximadamente en 250 ms.

**Cobertura y límites:** posición/tamaño del marco, workspace, pantalla por descripción estable,
NoBorder, opacidades activa/inactiva, foco, min/maxsize, minimizado, maximizado por ejes,
fullscreen y ocultar de capturas. Modos Apply/Force/Remember. X11 tiene rol y máscara NET;
Wayland normal/diálogo según padre. Expresiones regulares compatibles con Python. Las condiciones
no representables se omiten sin ampliar la coincidencia. Sin WM_CLASS completo, clientmachine,
Above/Below persistentes, ApplyNow, ForceTemporarily, actividades ni todos los tipos de KWin.
Desktop+Screen se reduce al workspace; no se simulan varios escritorios por ventana. Diagnóstico:
kwinrules-report.json. Matriz completa, prioridad y opt-out para reglas del usuario en
`config/hypr/skins/plasma/scripts/KWIN_RULES.md`. Force de geometría requiere excluir la ventana
con bwm-ignore-kwin-rules si se quiere controlarla desde el Lua del usuario; no se edita ese Lua.

Las reglas de flotación/estados visuales de Breeze salen del rules.lua común y viven en
`skins/plasma/hypr/rules.lua`. El Loader opcional de reglas está en appearance.lua antes de
placement y antes de bwm/user. Placement global sigue leyendo kwinrc; no se porta Placement por
regla. El KCM original `kcmshell6 kcm_kwinrules` está instalado y carga sin KWin (se probó con
configuración XDG aparte en workspace 9). No funciona su detección de ventanas por D-Bus KWin;
el menú abre el editor general. No se reclama org.kde.KWin. kcmshell6/KCM declarados como
recomendaciones y en el catálogo; no fue necesario instalar paquetes.

**Snapping:** `KWinSnap.hpp` sustituye SnapHelper.hpp; `SnapGeometry.hpp` separa cálculos puros.
Imanes de KWin por marco completo y reservas reales: BorderSnapZone, WindowSnapZone,
CenterSnapZone y SnapOnlyWhenOverlapping. Se desactiva el imán nativo de Hyprland sólo en Breeze
cuando existe el API nuevo. ElectricBorderTiling/Maximize/CornerRatio controlan bordes y esquinas.
Laterales → mitades; esquinas → cuartos; arriba → F8 maximizado. Se consume el destino que se
mostró, incluido su monitor y la elección Mayús, y `kwin-tiles.py` recibe descripción, PID y
marco exacto. Workspace primero, PID otra vez y geometría después. Redimensión de bordes
compartidos entre vecinas encajadas con límites nativos; no persiste las proporciones del grupo.
Ctrl+flechas se conserva por decisión expresa del usuario. Se preservan etiquetas ajenas.

**Mosaico y aspecto:** Mayús+arrastre sobre las hojas del JSON Tiling de KWin. Editor reducido
Meta+T para dividir/unir/repartir, padding y pantalla. Árbol original horizontal/vertical/flotante,
grupo `[Tiling][desktop UUID][output UUID]`. Los UUID de pantalla de KWin no se publican en
Hyprland: asociación en estado de máquina tiling-outputs.json por descripción; se elige al
importar una distribución. No hay un formato de layout propio ni identificadores DP-N. Sin datos,
las tres columnas originales 25/50/25. El editor no es el efecto original (requiere KWin), ni
permite dibujar zonas flotantes o arrastrar divisores. README en modules/plasma/tiling.

El outline GL azul desaparece. `Outline.qml` porta el QML de KWin v6.7.5 con su licencia, KSvg
widgets/translucentbackground y bordes según el área útil; capas sin entrada y sólo en Breeze.
Los dos Loader nuevos requieren reinicio del shell; el reinicio de sesión necesario del plugin
lo incorpora. autostart genera los archivos antes de cargar el plugin: su reload inicial ya los
encuentra. Se retira el override CSD antiguo por lista de clases. Sin Qt dentro de Hyprland,
sin cambios en el plugin de Retro, sin servicios KDE nuevos ni escrituras en bwm/user.

**Comprobado:** política/orden/modos, conflictos, identidad, árboles de KWin, aplicación exacta
al monitor de previsualización, geometría lógica/reservas, imanes y vecinos con datos simulados;
carga de los dos QML y de sus delegados en qs -p, e inspección de tres zonas a través del proceso
real de lectura. KCM con XDG temporal, sin guardar. Sin capturas. El resto sigue pendiente de
la lista de ratón `docs/BREEZE_F10_CHECKLIST.md`; no se ha cambiado a Breeze ni cargado el plugin
nuevo en caliente para declararlo probado.

Verificación final F10: **339 pruebas generales, 60 opcionales omitidas**, y las **dos pruebas
QML de F10 activadas pasan** (lector real del editor y orden del IPC del outline, sin capas visibles).
El IPC usa display/hide con una secuencia: las órdenes antiguas no reviven una previsualización.
Se evitó el nombre show, reservado por el CLI de Quickshell. Plugin compilado con
-fno-gnu-unique e instalado con make install; fuente/binario instalado coinciden. Parser real de
Hyprland acepta las reglas generadas (incluyendo opacidad compuesta y límites); configuración
actual válida, configerrors vacío y bwm check de Plasma correcto. qmllint ejecutado con avisos por
imports qs, metadatos de Quickshell/KSvg y tipos dinámicos; se complementa con carga real.


## 14. Interfaces de sesión de Plasma (F12)

- **Alt+Tab:** rejilla QML de KWin 6.7.5, con el controlador MRU común conservado (pulsaciones
  acumuladas y foco al soltar Alt). `[TabBox] LayoutName` selecciona paquetes de `kwin/tabbox`.
  Adaptación de TabBoxSwitcher, Dialog y WindowThumbnail, sobre los Toplevel de Quickshell.
  Los paquetes originales y sus recursos se conservan; se trabaja en caché publicada atómicamente.
- **OSD:** OsdItem original de plasma-workspace 6.7.5, PC3/Kirigami y SVG del tema activo;
  layer-shell sin entrada. Audio/brillo y timeout siguen siendo comunes. Avisos de cambios de
  pantallas mediante el archivo del gestor común y `plasmaOsd displayText`.
- **Bloqueo:** KScreenLocker 6.7.5 Greeter y componentes de sesión reales de Breeze.
  Las fuentes de Breeze 6.7.5 comprobadas ya no llevan `contents/lockscreen`. El tema global
  puede proporcionar LockScreenUi.qml/main.qml; si no carga se conserva el formulario de reserva.
  LockContext conserva PAM/huella y la decisión de desbloquear. El tema recibe sólo el adaptador,
  no el contexto de seguridad completo. Cambiar de usuario no se ofrece.
- **Temas QML:** ThemeHost (org.bwm.kcm, API 2) utiliza un QQmlEngine separado por componente;
  Qt.quit no sale del shell. Las APIs de KWin/KScreenLocker fuera del contrato implementado no se
  emulan; no se promete compatibilidad universal con efectos o temas privados de terceros.
  KcmHost sigue instanciando KCM únicamente dentro de Preferencias; no se carga Qt en Hyprland.
- **KRunner:** original instalado, con Milou y sus runners. Verificado sin plasmashell en un bus
  privado y plataforma offscreen: carga y consulta de calculadora, sin ejecutar resultados.
  Alt+Espacio se reserva a KRunner sólo en Breeze, autorizado por el usuario; la función anterior
  queda en default/Retro. No se inicia otro compositor ni un servidor de notificaciones.
- **Polkit:** manifiesto de Breeze selecciona el agente KDE instalado. bwm_polkit verifica la
  skin activa, detiene agentes externos conocidos de otras skins, espera su salida y serializa
  el arranque; reintenta fallos iniciales mientras se desmonta el agente embebido anterior.
  Retro mantiene Omarchy; el servicio BWM no registra otro agente en Breeze/Retro.

**Pruebas:** ocho pruebas F12 con la interfaz activada: prioridad KDE/kdedefaults, paquetes,
caché/recursos y selección, guardas/reintento serial de polkit, vistas nativas con autenticación
simulada, Qt.quit interceptado y Alt+Tab rápido/acumulado/sostenido sin foco real. Además, carga
del QML original completo de thumbnail_grid a través del adaptador. Vista de bloqueo revisada
mediante grabToImage del propio elemento (sin capturar otras ventanas), corregido un solapamiento
del reloj/avatar y eliminada la imagen. Suite general final: 358 pruebas, 65 omitidas. qmllint ejecutado con avisos por metadatos/imports dinámicos, complementado con carga QML real.

**Estado actualizado en F13:** el shell ya carga las interfaces; OSD y bandeja se corrigieron
tras el primer uso. Polkit KDE registró su agente. Faltan las pruebas físicas de Alt+Tab/OSD,
PAM/huella y autenticación privilegiada; el fallo histórico bajo Retro no describe el estado actual.

## 15. Cierre F13 y límites actuales

Código QML de Breeze únicamente en modules/plasma; eliminados los controles plasmaCommon,
el selector artesanal y los iconos locales sin consumidores. DesktopState mantiene Mostrar
escritorio en el panel. Alt+T usa BWMenu, sin confundir skin con tema global de KDE.
Se retira la paleta fija de reserva del cargador Material y su OSD antiguo. Se mantiene la
conversión desde el esquema activo para los widgets comunes y las ramas de selección necesarias.
Requisitos y parts revisados; quick-tile/toggle-minimize conservan consumidores en otras skins.

PlasmaTheme y plasma_palette fusionan la cascada XDG_CONFIG_DIRS → kdedefaults → archivos
locales: la aplicación nativa de Sweet probó que no bastaba con leer el archivo local.
Cambios en vivo y prioridad del usuario comprobados en pruebas Python/QML.

kded registra en cola los nombres de servicios de todos sus plugins, independientemente de
autoload=false. Al recargar el shell podía tomar StatusNotifierWatcher sin crear su objeto.
bwm-shell-conflicts --repair-stale sólo retira esa reserva rota con mismo PID/usuario y ningún
módulo cargado salvo ktimezoned. Conflictos funcionales siguen requiriendo la decisión del diálogo.
No se detienen módulos ajenos ni se reclama un nombre falso con otro demonio.

Integración: diez ventanas y siete flujos de audio conservados en la secuencia completa de skins,
sin saltos de workspace/configerrors, una instancia ii y geometría final conservada. Sweet
instalado con KNS y aplicado desde el KCM: colores, SVG, iconos y Aurorae efectivos; cursor
común intacto. Datos instalados fuera del repo; configuración anterior restaurada.
Evidencia y alcance, licencias, estimación prudente ~50 % y lista manual definitiva en
[BREEZE_F13_RESULTS.md](BREEZE_F13_RESULTS.md). La compilación o las pruebas simuladas no
sustituyen la matriz física CSD, snapping o autenticación. No se promete equivalencia completa.

La repetición final detectó un intercambio de posiciones en el orden de inserción de dwindle:
bwm_windows recuerda las ventanas libres al salir de una skin tradicional y recupera su marco
al volver. La caché es de sesión/skin en XDG_RUNTIME_DIR (no un archivo de tema): valida dirección,
PID/inicio, workspace y descripción/geometría de monitor. Descarta modos especiales y cambios
de workspace/salida. Las etiquetas del usuario y de reglas se preservan al salir de Breeze.
La secuencia final recupera las diez geometrías y conserva siete flujos de audio.

## 16. Ajustes después de F13

El usuario pidió recuperar el selector anterior: Alt+T vuelve a modules/plasma/skinPicker,
con su diseño BWM original y PlasmaTheme. Las menciones de BWMenu en el cierre F13 describen
ese commit, no el comportamiento actual. Noto Sans 10 y Hack son los valores predeterminados
de Breeze, declarados como fuentes requeridas; el puente mantiene su aislamiento entre skins.

PanelBackground sigue también la eliminación de bordes laterales de PanelView cuando el panel
llega a los extremos de pantalla. Se mantienen el SVG y los botones originales del tema, con
grupo Complementary e iconos dimensionados. Las tareas usan enfoque/elevación explícitos y PID;
la bandeja alterna el mismo botón y admite Escape incluyendo el panel en su grab.

El supervisor de decoraciones no espera dentro de un manejador de señal: evita reentrar en el
lock de Popen.wait y elimina la espera fija de cinco segundos al salir de Breeze.

El plugin recibe _NET_WM_MOVERESIZE por XCB para el arrastre CSD XWayland que Hyprland 0.56.2
no maneja. Usa la ventana real bajo el puntero y el botón físico, sin adivinar una zona superior
ni una lista de clases. No altera el protocolo Wayland ni la decisión CSD/SSD. Binario instalado
atómicamente; la parte C++ sólo se activa al reiniciar sesión. Evidencia y límites en
[BREEZE_PANEL_FIXES.md](BREEZE_PANEL_FIXES.md).

Seguimiento 2026-11-12: la acción de enfoque funcionaba pero el MouseArea del delegado
perdía el clic izquierdo por su DragHandler hijo. Task utiliza TapHandler como upstream;
prueba de entrada real en ListView, incluyendo miniatura, en los cuatro bordes. Sin margen
artificial entre tareas ni en el eje corto del panel; dimensiones basadas en las métricas
normales del SVG, como Task.qml/LayoutMetrics.js. Detalle en BREEZE_PANEL_FIXES.md.

Port visual posterior del mismo día: representaciones compactas originales de Kickoff,
DigitalClock, Mostrar escritorio y ExpanderArrow; cuadrícula nativa de bandeja sobre
AbstractItem y márgenes del contenedor por applet. Servicios y acciones permanecen en BWM.
bar.plasma.clock y systemTray admiten claves originales de apariencia; requisitos incluyen
el módulo QML privado de digital-clock. Estado y límites en BREEZE_PANEL_FIXES.md.
