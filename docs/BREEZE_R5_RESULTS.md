# Breeze II — R5: modo edición de Plasma (resultados)

R5 sustituye el editor reducido por las interfaces originales de Plasma 6.7.5. Este informe
recoge cada iteración; R5 sigue **abierta**.

## Punto de partida

Los criterios del prompt de R4 se cumplieron en §209 (widget de terceros desconocido que muestra
y guarda su opción). Lo que quedó abierto de R4 (sustituir el panel diario, bandeja nativa en la
vista) está fuera de ese prompt. R5 se construye sobre el anfitrión aislado de R4
(`src/bwm-plasma-host`, `PanelViewHost`, `PanelSession`, `PanelViewSettings`).

Fuentes de referencia (Portage, `/var/cache/distfiles`): `plasma-workspace-6.7.5.tar.xz`
(`shell/panelconfigview.*`, `shell/panelview.*`), `libplasma-6.7.5.tar.xz` y el paquete
instalado `org.kde.plasma.desktop` de plasma-desktop 6.7.5 (`configuration/PanelConfiguration.qml`,
`configuration/panelconfiguration/{Ruler,SliderHandle,PanelRepresentation}.qml`, `views/Panel.qml`).

## Iteración 1 (2026-11-18) — «Ajustes del panel» originales

### Qué hay

- **`PanelConfigView`/`PanelRulerView`** (`panelconfigview.{h,cpp}`): adaptación LGPL-2.0-or-later
  de `shell/panelconfigview.*`. Carga **sin modificar** el `PanelConfiguration.qml` instalado con
  los mismos objetos de contexto (`plasmoid`, `panel`, `configDialog`) y la propiedad inicial
  `panelConfiguration`. Cambios BWM: sin ShellCorona/KWayland/X11; la ventana se coloca como capa
  con el `PopupAnchor` de R4 (encima del panel, teclado OnDemand); el espaciador y el separador de
  márgenes se añaden con `Containment::createApplet` como el `panel.addWidget()` del script de
  Plasma (son widgets ocultos al catálogo). La regla (`Ruler.qml`) usa la capa `dock` de upstream.
- **Entrada**: la acción original del contenedor `configure` («Enter Edit Mode») abre/cierra el
  diálogo y el modo edición de la Corona, como `PanelView::showConfigurationInterface`. Escape y
  «Exit Edit Mode» lo cierran. `ViewCorona::enteredEditModeViaDesktop()` (false: no hay escritorio).
- **Contrato `PanelView` en `PanelViewHost`**: `alignment`, `offset`, `lengthMode` (lectura y
  escritura), `minimumLength`/`maximumLength`, `minThickness`, `screenToFollow`,
  `adaptiveOpacityEnabled` (del estilo de Plasma, `Plasma::Theme::adaptiveTransparencyEnabled()`),
  `unsupportedConfiguration*`, `userConfiguring`, `fixUnsupportedConfiguration()`, `clonePanelTo()`.
- **Tamaño y posición como upstream**: `preferredSize()` (Rellenar / Ajustar al contenido /
  Personalizado con mín./máx. y desplazamiento) y el anclaje de `updateLayerWindow()` (lado de la
  alineación con el desplazamiento como margen; centrado sin ancla lateral). En layer-shell v5 se
  conserva el tamaño explícito de §272 (sin anclas opuestas). El modo predeterminado pasa a ser el
  de Plasma, **FillAvailable**, cuando `plasmashellrc` no dice otra cosa.
- **Preferencias**: `alignment`, `panelLengthMode` (grupo del panel) y `offset` (resolución +
  `Defaults`) se leen y guardan en el `plasmashellrc` original con las mismas reglas de
  inmutabilidad, concurrencia y claves ajenas de R4. Antes se rechazaban.
- **Escritura**: mientras el diálogo está abierto (`userConfiguring`) cada cambio se guarda al
  momento, como `PanelView`. Fuera de él los setters siguen siendo vista previa (contrato R4).
- **Ensayo**: `preview-isolated.py --edit-mode` (sólo con `--native-panel --follow-skin`
  desechable) abre el diálogo cuando el panel aparece, mediante la misma acción `configure`.

### Pruebas

| Prueba | Resultado |
| :--- | :--- |
| `originalPanelSettingsEditMode` (QtTest, nueva): acción `configure` → diálogo cargado desde `PanelConfiguration.qml`; combos reales Alineación→Derecha, Anchura→Personalizada (regla visible), altura 52, Flotante, Opacidad (si el estilo la ofrece); Autoocultar rechazado; valores en `plasmashellrc`; «Add New > Spacer»; Escape sale del modo edición; lectura en un anfitrión nuevo; setters fuera del diálogo sin escribir | Pasa (local y en las dos pasadas de `check-isolated.py`) |
| `nativeAnchoringFollowsPanelViewPlacement` (`test-surfaces`, nueva): anclas y márgenes para derecha/centro/rellenar/ajustar, v5 y anterior | Pasa (20/20) |
| CTest `isolated-local-configuration` y `surface-geometry` | Pasan |
| `check-isolated.py` completo (ejemplo KDE + AndromedaLauncher, dos pasadas de toda la UI) | Pasa |
| Python R4 (`tests/test_r4_*`, con la prueba nueva de `--edit-mode`) | 255 OK |
| Sesión Hyprland, LG, `--edit-mode` con el reloj analógico original | El diálogo «Panel Settings» se abrió como capa `bwm-r4-popup` centrada encima del panel (3840×48, «Fill width»), con Opacidad habilitada; cierre limpio por `panel-session.py stop`, sin capas residuales |

Correcciones en el arnés encontradas al ejecutar `check-isolated.py` (anteriores a R5): no
instalaba el fixture `org.bwm.r4.tray-child`; ejecuta la UI una vez por paquete en las mismas
raíces (ahora cada pasada usa su copia de config/estado/runtime) y la suite completa necesita más
de 25 s (300 s sólo para esa orden). Las pruebas que esperaban 640 px piden ahora `Custom`
explícitamente, como haría un `plasmashellrc` con longitudes.

### Límites y diferencias con upstream

- **Sin pulsación física** en sesión: el diálogo se vio en Hyprland; los controles se probaron con
  los combos reales del QML en Qt offscreen. Falta que el usuario lo use con el ratón.
- **Autoocultar / Esquivar ventanas** y **Adaptativa** siguen sin controlador: el combo vuelve al
  valor guardado y el anfitrión registra el error (no se ocultan las opciones del original).
- **Mover a otro monitor** (`screenToFollow`, indicadores «Set Position…» en otras pantallas) y
  **Clonar panel** no tienen backend todavía: fallan de forma visible (`error`), sin efecto.
- Los indicadores de posición son `PlasmaCore.Dialog` del motor del diálogo, sin adaptación a capa.
- El diálogo no se cierra al pulsar fuera (upstream: `focusVisibilityCheck`); sí con Escape o
  «Exit Edit Mode».
- Centrado con desplazamiento: como el camino layer de upstream, el desplazamiento no se aplica.
- «Add New > Add Widgets…» dispara la acción original `add widgets`; el `WidgetExplorer` original
  aún no está portado (siguiente iteración).
- Migración desde `bar.plasma`: alineación y longitud siguen diferidas; ya existe controlador para
  ellas, pero la conversión no se ha implementado.
- Sin ASan en esta iteración.

### Pendiente de R5

`WidgetExplorer` original, modo edición del escritorio (`DesktopEditMode.qml`, sin contenedor de
escritorio en el anfitrión), mover/clonar paneles con el runtime, superposiciones de edición de
widgets en el panel, autohide/esquivar, varios paneles, escala fraccionaria, comparación de
imágenes con Plasma real y aceptación del usuario.

### Rollback

Retirar `panelconfigview.*`, las propiedades nuevas de `PanelViewHost`, las tres claves de
`PanelViewSettings` (vuelve a rechazar `alignment`/`panelLengthMode`/`offset`), el anclaje por
alineación en `surfaces.cpp`, `enteredEditModeViaDesktop`, `--edit-mode` y las pruebas nuevas.
