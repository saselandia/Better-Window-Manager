# Breeze III — T1: notificaciones nativas de Plasma en Breeze

Fecha: 2026-11-26. Plan: [BREEZE_PLAN_V3.md](BREEZE_PLAN_V3.md). Base: T0 cerrada (§386).

## Decisión de arquitectura

- **Servidor elegido:** `NotificationManager::Server` original de `plasma-workspace` 6.7.5 (`PW::LibNotificationManager`) dentro de `bwm-plasma-host --session`, coordinado por el nuevo componente [`NotificationHost`](../src/bwm-plasma-host/notificationhost.h).
- **Por qué:** el applet `org.kde.plasma.notifications` cargado por la bandeja nativa de `bwm-plasma-host` comparte en proceso el singleton `NotificationManager::Server::self()`, por lo que popups, historial, agrupación, progreso de trabajos KIO (`org.kde.JobViewServer` / `org.kde.kuiserver`), sonidos con `libcanberra`, acciones, respuesta en línea y `kcm_notifications` (`plasmanotifyrc`) funcionan sin parchear el applet ni `libnotificationmanager`.
- **Sin colas en D-Bus:** `bwm-plasma-host` no fija `_plasma_dbus_master=true`, así que `ServerPrivate::init()` registra `org.freedesktop.Notifications` con `DontQueueService | AllowReplacement`. Si el nombre aún está ocupado al arrancar, `NotificationHost` no bloquea ni hace cola: un `QDBusServiceWatcher` (`WatchForUnregistration`) reclama el servicio en cuanto el dueño anterior lo suelta.

## Cambios realizados

1. **`src/bwm-plasma-host/notificationhost.{h,cpp}` y `main.cpp`:**
   - Reclama `org.freedesktop.Notifications` con `NotificationManager::Server::self().init()` al arrancar `--session` (y reintenta automáticamente al liberarse vía `QDBusServiceWatcher`).
   - Adapta las ventanas `NotificationWindow` (`PlasmaQuick::PlasmaWindow`) creadas por el applet nativo de Plasma a `LayerShellQt::Window` en `QPlatformSurfaceEvent::SurfaceCreated` (namespace `bwm-plasma-notification`, `LayerTop` o `LayerOverlay` si `isCritical`, `exclusiveZone = -1`, `KeyboardInteractivityNone` por defecto y `KeyboardInteractivityOnDemand` cuando `takeFocus` pasa a `true` para respuesta en línea o copia al portapapeles).
   - Preserva la posición solicitada por `Globals.qml` frente al reset `(0, 0)` de `QWaylandWindow::handleGeometryChange` al recibir `zwlr_layer_surface_v1.configure`, y calcula márgenes locales por monitor (`popupMarginsForScreen`).
   - Expone en `bwm-plasma-host.sock`: `dnd-status`, `dnd-toggle`, `dnd-set true|false`, `notifications-status` y `notifications-claim`.
   - Publica atómicamente el estado real de «No molestar» (`Server::inhibited()`, cubriendo tanto el modo manual en `plasmanotifyrc` como inhibiciones de aplicaciones/pantalla completa) en `$XDG_RUNTIME_DIR/bwm-plasma-dnd`.

2. **Relevo de dueño (`services/Notifications.qml`, `IllogicalImpulseFamily.qml`, `plasma-host.py`, `bwm-theme-manager.py`):**
   - `Notifications.qml` comprueba `plasma-host.py ready` antes de activar su `NotificationServer` de respaldo y vigila `$XDG_RUNTIME_DIR/bwm-plasma-dnd` con `FileView` para mantener `Notifications.silent` y `bwmNotifications` IPC (`isDnd` / `toggleDnd`) sincronizados bidireccionalmente con el host nativo.
   - `IllogicalImpulseFamily.qml` propaga el estado de `nativeHostProbe` a `Notifications.updateNativeHostReady()` y desactiva el respaldo `modules/plasma/applets/NotificationPopups.qml` mientras el host nativo está activo.
   - **Hallazgo comprobado sobre Quickshell:** `Quickshell.Services.Notifications.NotificationServer` registra `org.freedesktop.Notifications` sin `ALLOW_REPLACEMENT` y no libera el nombre en D-Bus al destruir el componente QML (`LazyLoader` ni `Loader`). Por ello, `bwm-theme-manager.py` y `plasma-host.py` comprueban el PID dueño real de `org.freedesktop.Notifications`: **sólo** cuando `quickshell` posee el nombre y el nuevo dueño es externo (`bwm-plasma-host` o `swaync`), reinician Quickshell limpiamente antes/tras arrancar el nuevo servidor. Las transiciones que no parten de un `NotificationServer` de Quickshell (`plasma ↔ default`, `default → retro`, `plasma → retro`) no reinician el shell.
   - Durante los milisegundos del relevo, `~/.local/share/dbus-1/services/org.freedesktop.Notifications.service` (`plasma_waitforname`) retiene llamadas entrantes en D-Bus sin perder avisos.

3. **Autoridad del monitor de popups (documentada):**
   - **Breeze con host nativo activo:** manda **Plasma** (`plasmanotifyrc` para esquina/posición `PopupPosition`, duración `PopupTimeout`, comportamiento por aplicación, historial y sonidos; pantalla elegida por `Globals.qml` del applet nativo según el panel principal con bandeja).
   - **Respaldo sin host (`bar.plasma.nativeHost=false` o caída del host), Retro y default sin `swaync`:** aplica `Config.options.notifications.forceMonitor` de BWM.
   - Motivo: `org.kde.plasma.notifications` calcula `screenRect`, `availableWidth`, `CloseToWidget` y `obstructingDialog` sobre el containment de su panel; forzar otro monitor externo desajustaría el apilado y `CloseToWidget` en configuraciones multimonitor de distinta resolución.

## Comprobaciones realizadas

| Prueba | Entorno | Resultado |
| :--- | :--- | :--- |
| `notification-host` (`test-notifications.cpp`) | CTest en `dbus-run-session` privado + `QT_QPA_PLATFORM=offscreen` | **PASS** (4/4): clamping multimonitor 1440p/4K, rechazo sin colas ante propietario extranjero, reclamo automático al liberarse, `Notify()` por D-Bus y `notify-send` real, DND bidireccional + propiedad D-Bus `Inhibited` + `bwm-plasma-dnd`, lectura en vivo de `plasmanotifyrc` |
| `check-notifications-session.py` (`test-notifications-session`) | Hyprland anidado (`1280x800`) + `dbus-daemon` privado + `XDG_CONFIG_HOME` aislado | **PASS**: `org.freedesktop.Notifications`, `org.kde.JobViewServer` y `org.kde.kuiserver` en el host; popup real vía `notify-send` en capa `bwm-plasma-notification` (`x=36, y=665, w=332, h=71`, `0` ventanas `xdg_toplevel`); cambio en vivo `PopupPosition=TopLeft` en `plasmanotifyrc` + señal KConfig `ConfigChanged` recoloca el siguiente popup en `x=36, y=125`; DND por socket + archivo `bwm-plasma-dnd`; liberación limpia al parar |
| Batería completa CTest (`build/bwm-plasma-host-tests`) | `BUILD_TESTING=ON` | **15/15 PASS** (0 fallos, 92,8 s) |
| Relevo DND y caída/recuperación del host en sesión real | Sesión Breeze (`bwm-plasma-host` instalado, SHA256 `260a191aac3295a5…`) | **PASS**: `bwmNotifications toggleDnd` ↔ `plasma-host.py dnd-toggle` sincronizados (`false → true → false`); `plasma-host.py stop` devuelve `org.freedesktop.Notifications` a `quickshell`; `plasma-host.py start` lo devuelve a `bwm-plasma-host` (`valid: true`, `owner: "Plasma"`) |
| Relevo completo entre skins | `plasma → retro → default → plasma` en sesión | **PASS**: `bwm-plasma-host` → `quickshell` (Omarchy) → `swaync` → `bwm-plasma-host` (`valid: true`), sesión devuelta a Breeze |

## Pendiente de comprobación visual / uso diario

- Confirmación visual por el usuario de popups con acciones interactivas, respuesta en línea, progreso de una copia KIO real (Dolphin) y ajustes desde `systemsettings` → Notificaciones (`kcm_notifications`).
