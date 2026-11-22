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
* Zonas horarias múltiples / agenda de `DigitalClock.qml` y respuesta inline de notificaciones
  quedan como P2 opcionales (no bloquean el uso diario ni la aceptación R9).
