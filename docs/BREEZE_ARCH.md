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
| `kcminputrc` | `[Keyboard] RepeatDelay, RepeatRate` | **BWM** | De `modules/binds.lua` |
| `kxkbrc` | `[Layout]` | **BWM** | Distribución de teclado común |
| `mimeapps.list` | — | **BWM** | Apps predeterminadas comunes (`default-apps.py`) |
| `ksplashrc`, `kscreenlockerrc` | — | KDE | Tema global (sólo lo que Breeze use) |
| `kdedefaults/*` | — | KDE (lookandfeeltool) | Plasma añade `~/.config/kdedefaults` a `XDG_CONFIG_DIRS`: hay que hacerlo en el entorno de la sesión (`environment.lua`) para que los temas globales funcionen igual que en Plasma |
| `gtkrc`, `gtkrc-2.0`, `Trolltech.conf` | — | **BWM** | Los escribe lookandfeeltool: el puente debe volver a dejarlos como los quiere `gtk-theme.py` |
| `kded5rc` | `[Module-*] autoload` | **BWM** | Módulos de kded desactivados (§6) |

Al salir de Breeze, `kdeglobals` también lo leen default (plasma-integration) y Retro: la fase 2
debe coordinarlo con `bwm_icons.write_kdeglobals`.

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
fase 2 (`kde-config-bridge.py`) se encargará de crearlos y mantenerlos, y el instalador de crearlos
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
