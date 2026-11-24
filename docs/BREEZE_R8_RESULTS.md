# R8 — Mejoras de uso diario en Breeze (Plasma 6.7.5)

## Lote 1: cierre de avisos QML reales, portapapeles y vista previa de tareas (2026-11-22)

### Auditoría en vivo del shell (`qs -c ii log`)

Al iniciar R8 se recogieron **8 avisos QML reales** en `modules/plasma/`:

| Archivo y línea | Aviso original | Causa real | Corrección |
| :--- | :--- | :--- | :--- |
| `panel/Task.qml:21–22` | `Unable to assign [undefined] to bool` | `tasksModel?.isActive(t)` / `minimized(t)` sin comprobación de función ni coerción booleana al desmontar o con adaptadores reducidos | Coerción booleana estricta y guarda `typeof tasksModel?.isActive === "function"` |
| `theme/ToolTipArea.qml:31,73` | `Unable to assign [undefined] to QString / bool` | `root.QsWindow.window` sin `?.` lanzaba `TypeError` al desmontarse, devolviendo `undefined` | `root.QsWindow?.window` y `enabled: !!(root.visible && root.active)` |
| `tray/SystemTray.qml:51,57` | `Unable to assign [undefined] to QString / double` | `QsWindow.window` sin `?.` y `expander.visible` cuando `expander` se destruía antes de `root` | `QsWindow?.window?.screen?.name \|\| ""`, `Math.max(1, lanes)` y `(expander?.visible ? itemSize : 0)` |
| `tray/TrayPopup.qml:25,38` | `Unable to assign [undefined] to QString` | `anchorItem.QsWindow.window` sin `?.` al desmontarse | `anchorItem?.QsWindow?.window?.screen?.name \|\| ""` y guarda en `HyprlandFocusGrab` |

Tras el reinicio de mantenimiento del shell (`bwm-theme-manager.py set plasma --restart-shell`),
`qs -c ii log | rg "modules/plasma"` devuelve **0 avisos**.

### Mejoras de uso diario sobre componentes de Plasma 6.7.5

* **Portapapeles (`modules/plasma/applets/ClipboardApplet.qml`):**
  * Añadido botón **«Clear History»** (`edit-clear-history`) en la cabecera `PlasmoidHeading`,
    conectado a `Cliphist.wipe()` (mismo proveedor común `cliphist` de BWM, sin duplicar servicio).
  * Al abrir el applet, se limpia y enfoca el campo de búsqueda; pulsar `Return`/`Enter` copia la
    primera entrada filtrada.
* **Vista previa de tareas (`modules/plasma/panel/TaskToolTip.qml`):**
  * Cada tarjeta de ventana muestra ahora en su cabecera el icono de la aplicación
    (`Kirigami.Icon`), el título elidido y un botón `window-close` para cerrar esa ventana
    directamente desde el tooltip, como `ToolTipInstance.qml` de Plasma 6.7.5.

### Comprobado

* `tests/test_plasma_task_input.py`: 1/1 (todos los bordes, clics, arrastre, rueda y clic en la
  vista previa de `TaskToolTip`).
* `tests/test_plasma_panel_native.py`: 4/4.
* `tests/test_plasma_tray.py`: 20/20 (incluye `ClipboardApplet`, `BluetoothApplet`,
  `NotificationsApplet`, `CalendarApplet`, `TrayPopup` y menús SNI).
* Reinicio de mantenimiento del shell real: **0 avisos** en `modules/plasma/*`.

### P2 aplazados / límites explícitos

* Miniaturas en vivo de `TaskToolTip.qml` (`ScreencopyView`): mantienen la contención de
  `docs/BREEZE_RECOVERY.md` hasta habilitar la captura segura de ventanas en el panel diario.
* ~~Zonas horarias múltiples de `DigitalClock.qml`~~ (resuelto en el lote 2). Agenda y
  respuesta inline de notificaciones quedan como P2 opcionales (no bloquean R9).

## Lote 2: zonas horarias del reloj y del calendario (2026-11-22)

### Rectificación del lote 1

El registro del shell real (`quickshell -n -c ii`, iniciado 18:30:03, después de la edición de
`Task.qml` a las 18:27) no tiene avisos de `modules/plasma/*` desde el arranque hasta la primera
recarga en caliente. Los 72 avisos `Unable to assign [undefined]` de `Task.qml`, `ToolTipArea.qml`,
`TrayPopup.qml` y `SystemTray.qml` aparecen **sólo** entre «Reloading configuration…» y la carga de
la nueva generación: son evaluaciones de enlaces durante la destrucción de los objetos anteriores
(el `!!(...)` de `Task.qml:21` no puede devolver `undefined` en un contexto válido). El «0 avisos»
del lote 1 vale para el arranque, no para cada recarga en caliente. No se silencian.

### Rueda del reloj (`panel/DigitalClock.qml`)

* Portado sin cambios de lógica el `onWheel` de `applets/digital-clock/DigitalClock.qml` de
  plasma-workspace 6.7.5 (SHA256 `b3dfe4b4…c988e7`): con `wheelChangesTimezone`, cada clic de
  120 unidades avanza (abajo) o retrocede (arriba) en `selectedTimeZones`, da la vuelta y acumula
  medios clics. Lo único adaptado: en lugar de escribir `Plasmoid.configuration`, emite
  `timeZoneSelected` y `PanelContent.qml` guarda `lastSelectedTimezone` en `bar.plasma.clock`
  (las mismas claves de `main.xml`). `tzIndex` se recalcula al cambiar la configuración.
* Con una sola zona no hace nada, igual que el original.

### Calendario (`applets/calendar/CalendarApplet.qml`)

* `selectedTimeZonesDeduplicatingExplicitLocalTimeZone()` devolvía `["Local"]` fijo: la lista de
  relojes del calendario nunca salía. Ahora sigue `digital-clock/main.qml` 6.7.5: lee
  `selectedTimeZones`, quita la entrada explícita que coincide con la zona del sistema y ordena con
  `TimeZoneUtils.sortedTimeZones`. `currentTimeZone` sigue a `lastSelectedTimezone`,
  `displayTimezoneFormat` a la clave nativa, y `formatTime`/`formatOffset` son los originales
  (día de la semana si cambia de día, « • N horas antes/después» con el catálogo de Plasma).

### Comprobado

* `tests/test_plasma_panel_native.py` 6/6 (dos nuevos: rueda abajo×3 + arriba con vuelta y
  medio clic acumulado; rueda ignorada sin `wheelChangesTimezone`).
* `tests/test_plasma_tray.py` 21/21 (nuevo: calendario con tres zonas, lista visible, desplazamiento
  «2 hours later», sin desplazamiento para la zona actual). El primer intento con
  `Europe/Madrid` confirmó la deduplicación original (es la zona del sistema).
* Recarga en caliente del shell real sin errores nuevos de estos archivos.

### Límites

* No hay página para editar la lista de zonas (la del original es `configTimeZones.qml`, un KCM
  de applet): se configuran en `bar.plasma.clock` o en el texto del usuario. No probado con la
  rueda física en el panel diario ni a la vista.

## Lote 3: miniaturas en vivo con guardas y controles MPRIS en `TaskToolTip` (2026-11-22)

### Levantamiento de la contención de capturas (`BREEZE_RECOVERY.md`)

Verificado en la sesión activa que Hyprland 0.56.2 ejecuta el parche de usuario de Portage
(`hyprctl -j version` → `"bwmScreenshareMonitorGuard": {"version": 1, "pid": 3191}`). Además de la
guarda en el compositor, se añade doble defensa en QML (sólo capturar cuando la superficie está
visible y la ventana **no** está minimizada en `special:minimized`/workspace 99):

* **`modules/plasma/panel/TaskToolTip.qml`:**
  * `ScreencopyView` vuelve a capturar `card.modelData` sólo con
    `card.canCapture = popup.visible && !card.isMinimized && (card.modelData != null)` (`live` y
    `visible` ligados a `canCapture`). Las ventanas minimizadas muestran el icono centrado de la
    aplicación (48×48) en lugar de un recuadro vacío.
  * **Controles multimedia MPRIS** (como `ToolTipInstance.qml` de Plasma 6.7.5): empareja
    `Mpris.players` con `group.appId` por `desktopEntry`, `dbusName` o `identity` y muestra título
    de pista + botones `media-skip-backward`, `media-playback-pause`/`start` y
    `media-skip-forward`.
* **`modules/plasma/switcher/ThumbnailGrid.qml`:**
  * `ScreencopyView` ligado a `tabBox.visible && !isMinimized && (modelData.toplevel != null)`.
* **`modules/plasma/switcher/ThemedSwitcher.qml` y `compat/WindowThumbnail.qml`:**
  * `bwmToplevels` filtra a `null` las ventanas minimizadas y `WindowThumbnail` sólo enlaza
    `captureSource` cuando `visible && bwmController.isOpen`.

### Comprobado

* `tests/test_plasma_task_input.py`: **2/2** (nuevo `test_tooltip_thumbnail_guards_and_mpris_controls`
  comprueba `captureSource: null` cerrado/minimizado, captura activa abierto en ventana visible,
  vuelta a `null` al cerrar y botones MPRIS `previous`/`togglePlaying`/`next`).
* `tests/test_plasma_interfaces.py` (8/8) y `tests/test_window_activation.py` (7/7): **17/17 OK**.
* Recarga en caliente de `qs -c ii` sin errores de los cuatro archivos modificados.

### Pendiente / límites

* Comprobación visual física del usuario al pasar el ratón por tareas y pulsar `Alt+Tab` con
  ventanas reales y un reproductor MPRIS activo.
* Agenda y respuesta en línea de notificaciones siguen como P2 opcionales.

## Lote 4: exclusión mutua de capas `Overlay` y máscara al fijar Kickoff (2026-11-22)

Al diagnosticar una sesión con dos capas `WlrLayer.Overlay` abiertas a la vez (un menú contextual
en DP-1 y Kickoff en DP-2), se detectaron y corrigieron dos fallos de interacción:

* **`modules/plasma/kickoff/KickoffWindow.qml`:**
  * Abrir Kickoff cierra ahora `PlasmaMenus` y `TrayState`.
  * Cuando Kickoff está fijado (`!kickoff.hideOnWindowDeactivate`), `mask` se restringe a `frame`
    y `keyboardFocus` pasa a `OnDemand` (antes su `MouseArea` a pantalla completa capturaba todos
    los clics del monitor).
  * El fondo de cierre acepta `Qt.AllButtons` en `onPressed` (antes sólo `onClicked` izquierdo).
* **`modules/plasma/menus/MenuHost.qml`:**
  * Abrir un menú contextual cierra `GlobalStates.plasmaKickoffOpen` (y `TrayState` salvo cuando
    `kind === "tray"`, para permitir menús contextuales desde `TrayPopup`).
  * Expandir `TrayState` cierra cualquier `PlasmaMenus` que no sea de bandeja.

### Comprobado

* `tests/test_plasma_menus_ui.py`: **5/5 OK** (`BWM_RUN_QML_TESTS=1`).
* Recarga en caliente de `qs -c ii`: 0 errores ni advertencias de `KickoffWindow.qml` / `MenuHost.qml`.

## Lote 5: insignias y progreso Unity LauncherEntry en las tareas (2026-11-24)

P2 de la auditoría (`panel/TasksModel, TaskToolTip`: «Unity progress/badges»). El
`SmartLauncherItem` de Plasma vive en el módulo privado compilado dentro del applet
(`org.kde.plasma.taskmanager.so`) y no se puede importar desde Quickshell, así que:

* **`skins/plasma/scripts/launcher-entries.py`:** escucha en el bus de sesión
  `com.canonical.Unity.LauncherEntry.Update` (`sa{sv}`), sanea como
  `smartlauncherbackend.cpp` 6.7.5 (`count` < 2³¹, `progress` 0–1 → 0–100 redondeado, NaN = 0),
  anuncia `com.canonical.Unity` con `DO_NOT_QUEUE` (si otro dock lo tiene, sólo escucha) y olvida
  la entrada cuando el emisor sale del bus (`NameOwnerChanged`, como `onServiceUnregistered`).
  Sale con su proceso padre (`PR_SET_PDEATHSIG` + comprobación cada 5 s): una primera prueba en
  sesión dejó un huérfano reteniendo el nombre tras el reinicio de mantenimiento.
* **`panel/LauncherEntries.qml` + `LauncherEntries.js`:** singleton con un único `Process`
  (sólo mientras la skin es Breeze, relanzado a los 5 s si cae) y lógica pura compartida con las
  pruebas. Busca por el id del `.desktop` resuelto y, si no, por el `appId` de la ventana.
* **`panel/TaskBadgeOverlay.qml`:** el original con `BadgeEffect` (recorte del icono bajo la
  insignia), `Kirigami.Badge` y sufijos «k»/«9k+» del catálogo del applet. **`Task.qml`:** barra de
  progreso de `TaskProgressOverlay.qml` (`widgets/tasks` `progress` + `hover` por borde) y
  `urgent` cuenta como atención, como el `when:` original. Insignias ocultas con No molestar
  (`Notifications.silent`), como `Backend::count()`/`countVisible()`.

### Comprobado

* `tests/test_launcher_entries.py` 3/3: normalización, saneado y una prueba en un **bus D-Bus
  privado** (`dbus-run-session`): señal real → JSON esperado, `com.canonical.Unity` propio y
  retirada al salir el emisor.
* `tests/test_plasma_task_input.py` 3/3 (nueva `test_unity_badge_progress_and_urgent_like_plasma`:
  insignia «12», relleno 40 %, atención, oculta con No molestar, «9k+», retirada). Repetida 3 veces.
  Panel nativo, bandeja y skins: 40/40 en conjunto.
* Sesión real (Breeze, tras un reinicio de mantenimiento del shell): un emisor de prueba de
  4 s para `signal.desktop` mostró la insignia «5» recortando el icono y el 60 % de progreso en el
  panel del MSI, y ambos desaparecieron al salir el emisor. Capturas recortadas y borradas.

### Límites

* Sin `taskmanagerrulesrc` [Unity Launcher Mapping], sin `[Badges] InTaskManager` ni lista de
  apps excluidas de `plasmanotifyrc`; el No molestar programado de Plasma no aplica (se usa el
  de BWM).
* No probado con apps reales que envíen el protocolo (Telegram, Vesktop, descargas de Firefox).
* El reinicio de mantenimiento movió el foco al MSI (workspace 2), como ya se vio en §3.94;
  se devolvió a mano a la ventana anterior.

## Lote 6: imágenes en el portapapeles (2026-11-24)

P2 de la auditoría (`applets/clipboard`: «sin miniaturas»). Klipper usa `ImageItemDelegate.qml`
para las entradas de imagen; BWM mostraba su texto de cliphist («[[ binary data … ]]»).

* **`applets/clipboard/ImageItemDelegate.qml`:** el original de plasma-workspace 6.7.5 con la
  disposición, tamaño (4 unidades de rejilla) y alineación de Klipper. En lugar de `decoration` del
  `HistoryModel`, decodifica la entrada con `cliphist decode <id>` una sola vez a
  `$XDG_RUNTIME_DIR/bwm-plasma-clipboard/<id>` (umask 077, escritura en `.part` y renombrado) y lo
  borra al destruirse la fila. No toca el portapapeles al mostrarla.
* **`ClipboardApplet.qml`:** elige texto o imagen por entrada con `Cliphist.entryIsImage`, como el
  `DelegateChooser` de Klipper; copiar y borrar siguen igual.

### Comprobado

* `tests/test_plasma_tray.py` (ahora 21 pruebas): nueva `test_clipboard_text_and_image_entries`
  con un `cliphist` falso y un PNG de 40×20: una fila de imagen, imagen cargada a 40×20, clic que
  copia y carpeta privada 0700. Panel nativo, bandeja y skins: 34/34.

### Límites

* No se ha visto en el panel diario: un archivo nuevo de un módulo necesita un reinicio de
  mantenimiento del shell o el próximo inicio de sesión.
* Sin edición, QR ni vista de URL (`EditPage`, `BarcodePage`, `UrlItemDelegate`).

