# Breeze III — T8: vista general y esquinas activas

Fecha: 2026-11-27. Plan: [BREEZE_PLAN_V3.md](BREEZE_PLAN_V3.md). Implementación instalada y activa
en la sesión diaria; aceptación física de los atajos y de las esquinas activas por el usuario
pendiente.

## Decisiones acordadas con el usuario

1. **Vista general / Rejilla / Ventanas expuestas:** port en el host nativo (`bwm-plasma-host`)
   reutilizando el algoritmo `ExpoLayout` / `ExpoCell` de KWin 6.7.5, `org.kde.milou` (KRunner real)
   y las miniaturas en vivo `TaskThumbnail` con la guarda `bwmScreenshareMonitorGuard`.
2. **Esquinas activas y «Bordes de la pantalla»:** desbloquear `kcm_kwinscreenedges` en Preferencias
   y ejecutar sensores `LayerShellQt` de 2 px en `bwm-plasma-host` sólo en esquinas/bordes
   exteriores configurados en `kwinrc`, sin tocar `breezebars.so` ni requerir reinicio de sesión.

## Implementación

### Vista general, Rejilla y Ventanas expuestas (`OverviewHost`)

- `src/bwm-plasma-host/expolayout.{h,cpp}`: algoritmo original `ExpoLayout` / `ExpoCell` de KWin
  6.7.5 (`GPL-2.0-or-later`), sin dependencias de KWin core.
- `src/bwm-plasma-host/overviewhost.{h,cpp}` y `src/bwm-plasma-host/qml/OverviewMain.qml`:
  - **4 modos:** `overview` (`Meta+W`), `grid` (`Meta+G`), `windowview` (`Ctrl+F9`) y
    `windowview-all` (`Ctrl+F10`).
  - **Aspecto y animaciones:** capa `LayerShellQt` (`LayerOverlay`) por monitor, rampa de entrada
    `Kirigami.Units.longDuration` (`Easing.OutCubic`) conectada a `ExpoCell.partialActivationFactor`,
    barra superior de escritorios (`DesktopBar`) con destino de arrastre, botón cerrar en hover y
    píldora de título al estilo `WindowHeapDelegate.qml` de Plasma 6.7.5.
  - **Miniaturas en vivo:** `TaskThumbnail` (`org.bwm.kwin.effects/WindowThumbnail`) conectado al
    `QUuid` de `BwmTaskSource::uuidForAddress`, respetando `bwmScreenshareMonitorGuard` y mostrando
    el icono `Kirigami.Icon` como respaldo en minimizadas o sin screencopy.
  - **Búsqueda KRunner:** `Milou.ResultsView` cargado perezosamente con `Loader` al escribir en el
    buscador de `Meta+W` (apertura instantánea sin bloquear el hilo GUI al inicializar runners).
  - **Multimonitor, escalas fraccionarias y Magic:** sustracción de geometría lógica por monitor,
    detección de `special:magic` abierto (`magicOpen`) e inclusión de sus ventanas con insignia
    propia.
  - **Acciones comunes:** activar/restaurar minimizadas vía `toggle-minimize.py` / `hyprctl`,
    cerrar vía `kwin-window.py close`, mover ventana a escritorio vía `movetoworkspacesilent`,
    cambiar/añadir escritorio vía `hyprctl`.
- **Respaldo sin host (`bar.plasma.nativeHost=false`):** `desktop-actions.py` envía
  `overview-toggle <modo>` a `$XDG_RUNTIME_DIR/bwm-plasma-host.sock` y cae automáticamente a
  `quickshell -c ii ipc call overview toggle` si el host no está activo.
- **Atajos (T5):** registrados sólo para Breeze (`skins: ["plasma"]`) mediante
  `keybinds-manager.py add` y añadidos a `DEFAULT_KEYBINDS`: `SUPER+W`, `SUPER+G`, `CTRL+F9`,
  `CTRL+F10` (sin afectar a `default` ni `retro`).

### Esquinas activas y `kcm_kwinscreenedges` (`ScreenEdges`)

- `kcm_kwinscreenedges` desbloqueado en `config/hypr/skins/plasma/settings-profile/kdeglobals`
  (manteniendo `kcm_kwinscreenedges_x11=false` y `kcm_kwintouchscreen=false`).
- `src/bwm-plasma-host/screenedges.{h,cpp}`:
  - Lee y vigila `~/.config/kwinrc` (`QFileSystemWatcher` con debounce de 150 ms) usando las
    claves exactas de `kwinscreenedgesettings.kcfg` (`ElectricBorderDelay`, `ElectricBorderCooldown`,
    `RemainActiveOnFullscreen`, `[Effect-overview]`, `[Effect-windowview]`, `[ElectricBorders]`,
    `[TabBox]`). Valor por defecto de Plasma 6: `TopLeft` → Vista general.
  - **Seguridad multimonitor:** `ScreenEdges::isExteriorEdge` comprueba si otro monitor es
    adyacente a cada esquina/borde y sólo crea sensores `LayerShellQt` de 2 px en bordes/esquinas
    exteriores (nunca en la unión entre pantallas).
  - **Seguridad con snapping (§17):** no dispara si `QGuiApplication::mouseButtons() != Qt::NoButton`
    (arrastre de ventana activo) ni sobre pantalla completa cuando `RemainActiveOnFullscreen=false`.
  - **Acciones soportadas:** Vista general, Rejilla, Ventanas expuestas (actual / todas), Mostrar
    escritorio, Bloquear pantalla y Alt+Tab.

## Comprobaciones

| Prueba | Resultado |
| :--- | :--- |
| `tests/test_breeze_t8.py` + regresiones Python (`t6`, `store`, `kde_shortcuts`) | **27/27 PASS** (enrutado al socket del host, fallback Quickshell, exclusión fuera de Breeze, desbloqueo de `kcm_kwinscreenedges`, atajos `skins: ["plasma"]`) |
| `ctest -R native-overview-screenedges` (`test-overview-screenedges`) | **7/7 PASS** (defaults `kwinrc`, bordes personalizados, geometría exterior de 2 monitores con escala 1,5, snapshot con minimizadas y `special:magic`, colocación `ExpoLayout` sin solapamiento) |
| `ctest --test-dir build/bwm-plasma-host-tests` (suite completa) | **17/17 PASS** (56,87 s) |
| `check-focus-safety.py --binary src/bwm-plasma-host/check-t8-session.py` (Hyprland anidado) | **PASS** (`passed: true`, `4/4` modos cargados sin errores QML, `screenedges` activo, `physicalOutputsUnchanged: true`, `cleanupVerified: true`; informe `build/bwm-plasma-host-tests/t8-session-results.json`) |
| Despliegue diario (`plasma-host.py install` + `stop`/`start`) | Binario `b32f1eb2ffd0785b…` activo (PID 87186, `ready: true`), `screenedges-status`: `TopLeft -> Overview`, **2 sensores exteriores** en los dos monitores, `overview-status` sin errores |

## Límites y pendiente

- **Límites de la Opción 1:** las acciones exclusivas de KWin dentro de `kcm_kwinscreenedges` (ej.
  efecto cubo o cambio de escritorio al arrastrar al borde) no tienen efecto; la barrera física de
  puntero (`EdgeBarrier` en píxeles) no se aplica desde sensores `LayerShellQt`.
- **Pendiente de comprobación física por el usuario:** probar `Meta+W` (incluida búsqueda Milou y
  arrastre de ventana a otro escritorio), `Meta+G`, `Ctrl+F9`, `Ctrl+F10`, la esquina superior
  izquierda en ambos monitores, el paso libre del ratón entre monitores / snapping (§17), y abrir
  **Preferencias → Bordes de la pantalla** (`kcm_kwinscreenedges`).
