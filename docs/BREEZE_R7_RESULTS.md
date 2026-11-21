# R7 — Animaciones predeterminadas de Plasma 6.7.5 y sus ajustes

## Iteración 1: fuente única de verdad, curvas KWin 6.7.5, muelle nativo y `AnimationDurationFactor` (2026-11-21)

### Referencia (fuentes de KWin 6.7.5)

Efectos de animación habilitados por defecto (`EnabledByDefault: true`) en
`build/r6-upstream/kwin-6.7.5/src/plugins/`:

| Evento | Efecto original KWin 6.7.5 | Duración (`factor=1`) | Easing original | Transformación original | Implementación BWM (Hyprland 0.56.2 / QML) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Abrir ventana | `scale` (`package/contents/code/main.js`) | 200 ms × `factor` (`Duration`) | `QEasingCurve::OutCubic` | Escala `0.8 → 1.0` (`InScale`) + opacidad `0 → 1` | `windows`/`windowsIn`: `popin 80%`, `speed = 2.0 * factor`, `kwin_out_cubic`; `fade`/`fadeIn`: `2.0 * factor`, `kwin_out_cubic` |
| Cerrar ventana | `scale` | 200 ms × `factor` (`Duration`) | `QEasingCurve::InCubic` | Escala `1.0 → 0.8` (`OutScale`) + opacidad `1 → 0` | `windowsOut`: `popin 80%`, `speed = 2.0 * factor`, `kwin_in_cubic`; `fadeOut`: `2.0 * factor`, `kwin_in_cubic` |
| Maximizar / restaurar / mover / redimensionar | `maximize` / `fullscreen` (Stretch) | 250 ms × `factor` | `QEasingCurve::OutCubic` | Interpolación geométrica + cross-fade de instantánea | `windowsMove`: `speed = 2.5 * factor`, `kwin_out_cubic` (sin snapshot cross-fade en Hyprland) |
| Cambio de escritorio virtual | `slide` (`slide.cpp`, `springmotion.cpp`) | Muelle (`t95=318 ms`, `t99=465 ms`) | `SpringMotion(k=300/factor, ζ=1.1)` | Desplazamiento horizontal sin rebote (`slide`) | `workspaces`/`workspacesIn`/`workspacesOut`: curva nativa `spring = "kwin_slide"` (`stiffness=300/factor`, `dampening=2√k·1.1`, `mass=1`), `style = "slide"` |
| Popups / capas (panel, Kickoff, KRunner) | `slidingpopups` (`slidingpopups.cpp`) | 200 ms × `factor` (`Kirigami.Units.longDuration`) | `QEasingCurve::OutCubic` | Deslizamiento / aparición desde borde | `layers`/`layersIn`/`layersOut`: `speed = 2.0 * factor`, `kwin_out_cubic`, `style = "fade"` |
| Desvanecido de popups (menús, tooltips, diálogos) | `fadingpopups` (`package/contents/code/main.js`) | Entrada 150 ms / Salida 600 ms (`150×4`) × `factor` | Entrada `Linear` / Salida `OutQuart` | Opacidad `0 → 1` y `1 → 0` | `fadeLayersIn`: `1.5 * factor`, `kwin_linear`; `fadeLayersOut`: `6.0 * factor`, `kwin_out_quart` |
| Borde de ventana | Ninguno (Breeze no anima el borde de Hyprland) | — | — | — | `border`: `enabled = false` |
| Minimizar / restaurar hacia la tarea | `squash` (`package/contents/code/main.js`) | 250 ms × `factor` | `InCubic` / `OutCubic` | Encogimiento hacia geometría de icono en barra de tareas | Pendiente / límite de Hyprland (minimizado usa workspace especial `special:minimized`, sin geometría destino por tarea) |
| Workspace especial (Magic) | Extensión común de BWM (no existe en KDE) | 250 ms × `factor` | `kwin_out_cubic` | `slidevert` | `specialWorkspace*`: `speed = 2.5 * factor`, `kwin_out_cubic`, `slidevert` |
| Animaciones QML de Plasma | `Kirigami.Units.*Duration` | Escalado automático por Qt/Kirigami con `AnimationDurationFactor` | `OutCubic` / `InOutQuad` | Panel, Kickoff, menús, OSD | `PickerWindow.qml` pasado de 140/160 ms fijos a `Kirigami.Units.shortDuration` |

### Verificación empírica de `libhyprutils` (Hyprland 0.56.2)

Probado directamente enlazando contra `libhyprutils.so` instalado en el sistema:

* **Unidades de `speed`:** tras 100 ms reales, `speed = 2.0` devuelve `percent = 0.50` (200 ms) y
  `speed = 4.0` devuelve `percent = 0.25` (400 ms). `speed` es **duración en décimas de segundo**
  (`1.0 = 100 ms`), **directamente proporcional** a `AnimationDurationFactor`.
  * **Fallo corregido:** el bloque antiguo de `kwin.lua` asumía lo contrario (`speed = base / factor`),
    de modo que al subir `AnimationDurationFactor` a `2` (más lento) hacía las animaciones el doble
    de rápidas, y no se ejecutaba al volver a `factor = 1`.
* **Muelle nativo `SSpringCurve`:** `advanceSpring` con `{ stiffness = 300, damping = 2*sqrt(300)*1.1, mass = 1 }`
  produce `t=100ms → 0.4876`, `t=200ms → 0.8191`, `t=300ms → 0.9396`, `t=400ms → 0.9801`,
  `t=465ms → 0.9903`, idéntico a `KWin::SpringMotion(300, 1.1)` (`t99 = 465 ms`).
* **Bézier cúbicas exactas:** para $P_1=(1/3, y_1)$ y $P_2=(2/3, y_2)$, $B_x(u)=u$ exactamente, por lo
  que `(0.3333, 1, 0.6667, 1)` es matemáticamente idéntica a `QEasingCurve::OutCubic` y
  `(0.3333, 0, 0.6667, 0)` a `QEasingCurve::InCubic` (error 0).

### Cambios realizados

* **`config/hypr/skins/plasma/hypr/animations.lua`:** fuente única de verdad para las animaciones de
  Breeze. Eliminadas todas las curvas `md3_*` y `popin 60%`. Lee `$XDG_STATE_HOME/bwm/plasma/kwin.lua`,
  aplica `animations.enabled = factor > 0`, escala linealmente `ds(ms) = max(0.1, (ms/100)*factor)` y
  registra `kwin_slide` como `spring` nativo (`stiffness = 300/factor`, `dampening = 2√k·1.1`, `mass = 1`).
* **`config/hypr/skins/plasma/hypr/kwin.lua`:** eliminado el bloque duplicado e invertido de
  animaciones (`a[2] / factor` con `md3_*`).
* **`config/hypr/skins/plasma/scripts/kde-config-bridge.py`:** exporta los toggles reales de
  `kwinrc [Plugins]` (`scaleEnabled`, `maximizeEnabled`, `slideEnabled`, `fadingPopupsEnabled`,
  `slidingPopupsEnabled`) y `[Effect-scale]` (`Duration`, `InScale`, `OutScale`).
* **`config/quickshell/ii/modules/plasma/skinPicker/PickerWindow.qml`:** sustituidas duraciones fijas
  (140/160 ms) por `Kirigami.Units.shortDuration`.
* **No se han modificado las animaciones de `default` ni de `retro`.**

### Comprobado

* `hyprctl reload` y `hyprctl configerrors` vacío en la sesión real.
* `hyprctl animations` en la sesión real confirma `spring:kwin_slide` en `workspaces*`,
  `kwin_out_cubic` / `kwin_in_cubic` 2.0 (`popin 80%`) en `windows*` / `fade*`, `2.5` en
  `windowsMove`, `1.5` `kwin_linear` en `fadeLayersIn` y `6.0` `kwin_out_quart` en `fadeLayersOut`.
* `tests/test_kde_config_bridge.py` 22/22 (nueva prueba `test_kwin_default_animations_and_duration_factor`:
  `factor = 1`, `2`, `0`, retorno a `1`, toggles `[Plugins]`, `[Effect-scale]` y ausencia de `md3_*`
  / `popin 60%`).
* `tests/test_plasma_shadow_policy.py` 3/3.

### Límites / pendiente

* `squash` (minimizar hacia el rectángulo del icono en la barra de tareas) y cross-fade de instantánea
  en `maximize` no existen como estilos nativos en Hyprland; requerirían un complemento de compositor.
* Comparación por fotogramas/vídeo con marcas de tiempo frente a una sesión Plasma 6.7.5 real y
  página de efectos habilitados en Preferencias del sistema (solo los realmente soportados).
