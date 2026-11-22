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
