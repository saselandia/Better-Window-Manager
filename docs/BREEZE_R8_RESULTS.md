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

## Lote 7: servidor de avisos en Breeze y respuesta en línea (2026-11-24)

* **Encontrado:** swaync tenía `org.freedesktop.Notifications` en Breeze (autostart lo arrancaba fuera
  de Retro), así que los toasts, el historial de la bandeja y las acciones de Plasma no recibían nada.
  Ahora `skin.json` declara `notifications` (`swaync` default, `shell` Breeze/Retro) y el gestor y
  `autostart.sh` cierran o arrancan swaync según la skin. `services/Notifications.qml` sólo crea su
  servidor en Breeze (o en default si falta swaync).
* **Respuesta en línea:** `ActionContainer.qml` vuelve a ser el original (botón Reply primero, campo
  por defecto si es la única acción) con `NotificationReplyField.qml` (sin `Globals.popupWidth`).
  `NotificationCard` lo conecta a `Notification.sendInlineReply()` de Quickshell y descarta el aviso
  al enviar. El servidor sólo anuncia `inline-reply` en Breeze, para que en default las apps no
  sustituyan su acción «Responder» por un campo que no se muestra. Los toasts toman el teclado
  (`OnDemand`) sólo mientras se escribe una respuesta y no caducan entonces.

### Comprobado

* `test_notification_inline_reply_like_plasma`: botón Reply, campo enfocado, «Hola» enviado por
  `sendInlineReply` sin invocar acciones. Bandeja, skins, sesión y cambio de skin: 45/45.
* Sesión real: `bwm-theme-manager.py set plasma` cerró swaync, el PID de Quickshell tomó el nombre
  y `GetCapabilities` incluye `inline-reply`; una notificación de prueba con `inline-reply` salió como
  toast de Plasma con los botones Reply y Abrir. Captura recortada y borrada; aviso cerrado.

### Límites

* No se ha escrito una respuesta real con el teclado en el toast, ni probado con Telegram/Vesktop.
* La etiqueta del botón es la de Plasma («Reply» en `en_US`); Quickshell no expone el texto que la
  app da a la acción `inline-reply`.
* Sin trabajos KIO ni No molestar programado.

## Lote 8: código QR y edición en el portapapeles (2026-11-24)

* **`applets/clipboard/DelegateToolButtons.qml`** (el de Klipper 6.7.5 sin «Invocar acción», que son
  las acciones de URL de Klipper, ni la estrella, que cliphist no guarda): en la fila bajo el puntero
  o con foco, «Mostrar código QR» y «Editar contenido» en texto y «Quitar del historial» en todas.
* **`BarcodePage.qml`** (Prison, copiar la imagen del QR con `KQuickControlsAddons.Clipboard`) y
  **`EditPage.qml`** originales. Klipper reescribe la entrada y la sube; con cliphist, guardar copia el
  texto nuevo (pasa a ser la primera entrada) y borra la anterior.
* `ClipboardApplet.qml` es ahora una `StackView` como `KlipperPopup` (la cabecera sigue a la página).
  Nuevo IPC `plasmaClipboard open|close|toggle`, como los demás applets de la bandeja.
* Requisitos nuevos declarados (ya instalados): módulos QML `org.kde.prison` y
  `org.kde.kquickcontrolsaddons`.

### Comprobado

* La prueba del portapapeles abre el QR (página 2, código válido) y la edición (texto original,
  guardar → texto nuevo copiado, entrada anterior borrada, vuelta a la lista). Bandeja, panel y skins:
  35/35. Captura del QR revisada y borrada.
* El IPC abre el portapapeles en la sesión real (es un `PopupWindow`, no aparece en `hyprctl layers`).

### Incidencia

* La primera versión, al guardar, usaba `Quickshell.clipboardText` también cuando el backend tenía su
  propio `setText` (`a?.()??b` ejecuta `b` si `a` devuelve `undefined`): las pruebas escribieron
  «Edited entry» en el portapapeles real. Se borró esa entrada de cliphist, se devolvió al portapapeles
  la entrada que estaba antes y se corrigió la condición; la prueba ya no toca el portapapeles.

### Límites

* Botones probados por código, no con el ratón en el panel diario. Sin vista de URL (miniaturas de
  archivos) ni acciones de Klipper.

## Lote 9: archivos copiados en el portapapeles (2026-11-24)

* **`applets/clipboard/UrlItemDelegate.qml`:** el de Klipper 6.7.5 (fila de miniaturas con el nombre
  del archivo debajo y «+N» si no caben). Klipper usa su proveedor `klipperpreview` (KIO
  `PreviewJob`: miniatura o icono MIME). Aquí la entrada de cliphist se decodifica una vez (el texto
  de la lista viene recortado) y `gio info` da, por cada URL local, la miniatura de la caché
  freedesktop (`~/.cache/thumbnails`, la que generan Dolphin y Nautilus) o su icono MIME. Las URL
  remotas no tienen vista previa, como en Klipper.
* `ClipboardApplet.qml` elige este delegado cuando todas las palabras de la entrada son `file://`
  (tolerando la última recortada). Sólo ofrece «Quitar del historial», como el tipo URL de Klipper.

### Comprobado

* La prueba del portapapeles añade una entrada de dos archivos (uno con espacio en el nombre) con un
  `cliphist` falso: lista completa tras decodificar e iconos `text-plain` e `image-png`. Bandeja,
  panel y skins: 35/35. Captura de una fila con un `.txt` (icono) y un fondo con miniatura de la
  caché revisada y borrada. El portapapeles real no se tocó.

### Límites

* Si un archivo no tiene miniatura en la caché se muestra su icono: BWM no genera miniaturas nuevas
  (Klipper sí, con `PreviewJob`). Sin arrastrar los archivos desde la fila.

## Lote 10: inhibición manual y perfiles de energía en `PowerApplet` (2026-11-24)

P2 de la auditoría (`applets/power`: «UPower/brillo compartidos, sin inhibiciones/perfiles PowerDevil»).
Se reaprovechan los proveedores comunes sin iniciar PowerDevil ni mostrar controles sin efecto:

* **`applets/PowerApplet.qml`:**
  * Cabecera `PlasmoidHeading` con el interruptor **«Manually block sleep and screen locking»**
    conectado al servicio común `Idle` (`Idle.inhibit` / `Idle.toggleInhibit()`), que mantiene el
    `IdleInhibitor` de Wayland y la pausa de `BwmIdle.qml`. Al activarlo se muestra el componente
    original `power/InhibitionHint.qml` («You have manually blocked sleep and screen locking.»).
  * Detecta una vez en el bus de sistema si existe `org.freedesktop.UPower.PowerProfiles` o
    `net.hadess.PowerProfiles` (`power-profiles-daemon`/`tuned-ppd`); si no está presente, oculta
    el selector de perfiles para no ofrecer controles sin efecto.
* **`applets/power/PowerProfileItem.qml`:** adaptado de PowerDevil 6.7.5 sobre
  `Quickshell.Services.UPower.PowerProfiles` (Power Save / Balanced / Performance según
  `hasPerformanceProfile`, más avisos `InhibitionHint` para `degradationReason` y `holds`).
* **`tray/SystemTray.qml`:** el applet `power` pasa a estar activo también cuando `Idle.inhibit`
  está activado (`Battery.available || Idle.inhibit`), como en Plasma, para que el icono aparezca
  en la bandeja en sobremesa mientras el reposo esté bloqueado manualmente.

### Comprobado

* `tests/test_plasma_tray.py`: `test_power_without_daemon` (interruptor de inhibición activa el
  mock `Idle` y muestra `InhibitionHint`, `PowerProfileItem` oculto) y
  `test_power_with_profiles_and_inhibition` (selector de perfiles visible, cambio a Performance,
  aviso de degradación por temperatura y `holds`).
* Bandeja, panel y skins: **37/37 OK** (`BWM_RUN_QML_TESTS=1`).

### Límites

* Sin inhibiciones de aplicaciones externas de PowerDevil ni perfiles automáticos al desconectar
  corriente. En el equipo actual no hay `power-profiles-daemon` instalado, así que `PowerProfileItem`
  permanece oculto en uso diario hasta que se instale.
* Archivo nuevo de módulo (`power/PowerProfileItem.qml`): requiere reinicio de mantenimiento del
  shell o próximo inicio de sesión para cargarse en el panel diario.

## Lote 11: agenda y opciones nativas del calendario (2026-11-24)

P2 de la auditoría (`panel/DigitalClock y applets/calendar`: «plugins de agenda»). `CalendarView.qml`
ya instanciaba `PlasmaCalendar.EventPluginsManager`, pero `CalendarApplet.qml` dejaba
`enabledCalendarPlugins: []`, `firstDayOfWeek: -1`, `showWeekNumbers: true` y `showSeconds: 0` fijos.

* **`applets/calendar/CalendarApplet.qml`:** lee ahora `enabledCalendarPlugins` (p. ej.
  `["holidaysevents"]` con el plugin instalado `/usr/lib64/qt6/plugins/plasmacalendarplugins/holidaysevents.so`),
  `firstDayOfWeek`, `showWeekNumbers` y `showSeconds` desde `Config.options.bar.plasma.clock` (las
  mismas claves de `digital-clock/main.xml` 6.7.5).

### Comprobado

* `tests/test_plasma_tray.py`: nueva `test_calendar_agenda_and_native_options` con
  `enabledCalendarPlugins: ["holidaysevents"]`, `firstDayOfWeek: 1`, `showWeekNumbers: false` y
  `showSeconds: 2`: `CalendarView.showAgenda` pasa a `true` y `MonthView` adopta las opciones.
* Bandeja, panel y skins: **37/37 OK** (`BWM_RUN_QML_TESTS=1`).

### Límites

* Sigue sin página gráfica en Ajustes para elegir zonas horarias o plugins de agenda (se configuran
  en `bar.plasma.clock` o en el texto del usuario). No comprobado visualmente en el panel diario.

## Lote 12: filtros, agrupación y rueda configurable en `TasksModel` (2026-11-25)

P2 de la auditoría (`panel/TasksModel, TaskToolTip`: «grupos y filtros de referencia»).

* **`panel/PanelLogic.js` (`filterTasks`):** lógica pura de los filtros nativos de
  `applets/taskmanager/package/contents/config/main.xml` 6.7.5:
  * `showOnlyCurrentScreen`: filtra por monitor del panel conservando los lanzadores fijados
    (`toplevels: []`), como `TaskManager::TasksModel`.
  * `showOnlyCurrentDesktop`: filtra por workspace activo del monitor respetando ventanas fijadas
    en todos los escritorios (`client.pinned`).
  * `showOnlyMinimized`: muestra sólo ventanas en `special:minimized`.
  * `groupingStrategy` (`0 = DoNotGroup`, `1 = ByProgramName` por defecto): en `0` separa cada
    ventana abierta con una `key` única (`appId:address`).
* **`panel/TasksModel.qml`, `panel/PanelContent.qml` y `panel/Task.qml`:** `TasksModel` recibe
  `panelMonitor` desde `PanelContent.qml`, lee `Config.options.bar.plasma.taskManager`, usa
  `objectProp: "key"` en `ScriptModel` y `Task.qml` respeta `wheelEnabled` (sin bloquear el ciclo
  al hacer clic).

### Comprobado

* `tests/test_plasma_panel.py`: nuevas `test_filter_tasks_screen_desktop_minimized_and_pinned` y
  `test_filter_tasks_ungrouped_keeps_distinct_keys` ejecutando `PanelLogic.js` en `qml6`.
* Panel, panel nativo, entrada de tareas y compilación: **22/22 OK** (`BWM_RUN_QML_TESTS=1`).

### Límites

* Las opciones se leen desde `bar.plasma.taskManager` (o texto del usuario); siguen sin página
  gráfica de configuración del gestor de tareas en el panel diario.

## Lote 13: internacionalización KDE y accesibilidad en `PanelEditor` (2026-11-25)

P2 de la auditoría (`Accesibilidad/idioma`: «PanelEditor contiene textos castellanos fijos»).

* **`panel/PanelEditor.qml`:** sustituidos todos los textos castellanos fijos por
  `KI18nContext` con el dominio original de Plasma (`plasma_shell_org.kde.plasma.desktop`),
  nombres legibles de widgets, `Accessible.name` en desplegables, deslizadores y botones de
  reordenación, tecla `Escape` para cerrar y encadenamiento seguro `anchor.item?.QsWindow?.window`.

### Comprobado

* `tests/test_plasma_panel.py`: nuevas `test_panel_editor_uses_kde_i18n_without_hardcoded_spanish`
  y `test_panel_editor_loads_with_english_labels_in_c_locale` (en `LC_ALL=C.UTF-8` devuelve
  «Panel Settings», «Task Manager», «Done» y cierra sin errores).
* Panel, panel nativo, entrada de tareas y compilación: **22/22 OK** (`BWM_RUN_QML_TESTS=1`).

### Límites

* No probado con lector de pantalla (Orca) ni en idioma RTL real.

## Lote 14: No molestar temporal en notificaciones (2026-11-25)

P2 de la auditoría (`applets/notifications`: «sin programación DND»).

* **`services/Notifications.qml`:** añadidos `silentUntil` (marca Unix en ms, `0` = indefinido),
  `setSilentFor(minutes)`, `clearSilentUntil()` y un `Timer` de expiración (cada 15 s mientras
  `silent && silentUntil > 0`) que apaga `silent` al cumplirse el plazo y limpia `silentUntil` al
  desactivar DND manualmente. Común a las skins que usan el servidor de Quickshell.
* **`applets/NotificationsApplet.qml`:** en el encabezado `PlasmoidHeading`, cuando DND está
  activo se muestra la hora de fin («Until HH:MM» / «Until turned off») y el selector de duración
  de Plasma 6.7.5 («Until turned off», «For 1 hour», «For 4 hours», «Until tomorrow»).

### Comprobado

* `tests/test_plasma_tray.py`: `test_notification_action_uses_existing_backend` verifica que
  activar DND muestra el selector, elegir «For 1 hour» fija `silentUntil > 0` y actualiza la
  etiqueta a «Until …»; `test_notification_inline_reply_like_plasma` sigue OK.

### Límites

* No persiste `silentUntil` entre reinicios del shell; sin trabajos KIO ni DND automático por
  pantalla duplicada.

## Lote 15: ownership de escaneo y acciones de dispositivo en `BluetoothApplet` (2026-11-25)

P2 de la auditoría (`applets/BluetoothApplet`: «Revisar ownership y parada de discovery iniciado aquí»).

* **`applets/BluetoothApplet.qml`:**
  * `stopOwnedDiscovery(force)` centraliza la parada de `scanTimeout`, `adapter.discovering` y
    el reinicio de `initiatedDiscovery = false` (antes `scanTimeout` y `onExpandedChanged` no
    limpiaban `initiatedDiscovery`, arriesgando parar un escaneo ajeno al destruirse el applet).
  * El botón `Find Devices` refleja `checked: root.scanning` y cambia a «Stop Searching» mientras
    escanea.
  * Durante el emparejamiento (`modelData.pairing`), el botón principal pasa a «Cancel»
    (`cancelPair()`); en la vista expandida se añaden casillas `Trusted` (`modelData.trusted`) y
    `Blocked` (`modelData.blocked`).

### Comprobado

* `tests/test_plasma_tray.py`: `test_bluetooth_uses_mock_and_does_not_discover_on_open` verifica
  que cerrar el popup NO apaga un escaneo iniciado fuera (`foreignKept: true`), y que un escaneo
  iniciado por `Find Devices` SÍ se detiene y limpia `initiatedDiscovery` al cerrar
  (`ownedStarted: true`, `ownedStopped: true`); `BluetoothAppletTests` sigue OK (4/4 en bloque).

### Límites

* Sin OBEX ni asistente avanzado de PIN de Bluedevil; no probado con radios/dispositivos físicos.

## Lote 16: controles gráficos de tareas y calendario en `PanelEditor` y cierre de regresión (2026-11-25)

* **`panel/PanelEditor.qml`:** envuelto el contenido en `PC3.ScrollView` (manteniendo «Done» fijo
  abajo) y añadidos los controles gráficos para las claves nativas de los lotes 11 y 12 cuando sus
  widgets están activos en el panel:
  * **Task Manager** (`bar.plasma.taskManager`): `showOnlyCurrentScreen`, `showOnlyCurrentDesktop`,
    `showOnlyMinimized`, `groupingStrategy` (agrupar por programa) y `wheelEnabled`.
  * **Digital Clock** (`bar.plasma.clock`): `showWeekNumbers` y «Show holidays» (activa/desactiva
    `"holidaysevents"` en `enabledCalendarPlugins`).

### Comprobado

* `tests/test_plasma_panel.py`: `test_panel_editor_loads_with_english_labels_in_c_locale` verifica
  también `setTaskOption("showOnlyCurrentScreen", true)`, `setTaskOption("groupingStrategy", 0)` y
  `toggleHolidayPlugin(true/false)`.
* Regresión completa tras lotes 10–16 (`BWM_RUN_QML_TESTS=1`):
  * `test_plasma_panel` + `test_plasma_panel_native` + `test_plasma_task_input` + `test_plasma_tray`
    + `test_plasma_menus_ui` + `test_skins`: **57/57 OK**.
  * `test_skin_switch` + `test_kwin_window` + `test_kwin_rules`: **42/42 OK**.
  * `test_r3_native_settings` + `test_launcher_entries`: **14/14 OK**.
  * `test_plasma_interfaces`: **8/8 OK**.
  * Total ejecutado: **121/121 OK**; `hyprctl configerrors` vacío; `bwm-requirements.py check --skin plasma`
    todo listo.

### Comprobado en la sesión reiniciada (2026-11-25)

* Tras reiniciar sesión en Breeze (`plasma`, Hyprland 0.56.2 con `bwmScreenshareMonitorGuard` v1):
  * `hyprctl configerrors` vacío; `breezebars-shadows` v2 (`shm: true`, XWayland `:0`) y
    `breezebars-scale` v1 activos; `bwm-decorator` escuchando (`installed: true`).
  * Instancia única de `quickshell -n -c ii`, dueño único de `org.freedesktop.Notifications`.
  * **0 avisos ni errores** en `/run/user/1000/quickshell-session.log` ni `qs -c ii log` para
    `modules/plasma/*` y `services/Notifications.qml` (con `PowerProfileItem.qml` ya cargado).

### Límites

* Sigue sin página gráfica de zonas horarias múltiples (se configuran en `bar.plasma.clock`).
* Comprobación visual física interactiva del usuario (abrir `PanelEditor`, `PowerApplet`,
  `NotificationsApplet` y `BluetoothApplet` en el panel diario) sigue en sus manos.





