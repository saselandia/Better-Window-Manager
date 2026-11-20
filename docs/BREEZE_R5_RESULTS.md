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
  Autoocultar y esquivar tienen controlador desde la iteración 5 (con `--native-policy`).
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

### Pendiente de R5 (tras la iteración 1)

`WidgetExplorer` original, modo edición del escritorio (`DesktopEditMode.qml`, sin contenedor de
escritorio en el anfitrión), mover/clonar paneles con el runtime, superposiciones de edición de
widgets en el panel, autohide/esquivar, varios paneles, escala fraccionaria, comparación de
imágenes con Plasma real y aceptación del usuario.

### Rollback

Retirar `panelconfigview.*`, las propiedades nuevas de `PanelViewHost`, las tres claves de
`PanelViewSettings` (vuelve a rechazar `alignment`/`panelLengthMode`/`offset`), el anclaje por
alineación en `surfaces.cpp`, `enteredEditModeViaDesktop`, `--edit-mode` y las pruebas nuevas.

## Iteración 2 (2026-11-19) — Posición, alineación y flotante en Hyprland

### Informe del usuario

Con el ratón, sobre la vista de la iteración 1: «Set Position…», alineación, visibilidad y
flotante no funcionaban; el resto sí. El `plasmashellrc` de esa vista tenía `alignment=132`
(centrado) con `panelLengthMode=0` (rellenar), sin clave `floating`, y el panel seguía abajo.

### Causas y cambios

- **Posición.** Dos fallos: (1) las flechas de «Set Position…» son `PlasmaCore.Dialog` del
  motor del diálogo, colocadas por coordenadas globales en cada pantalla; nada les daba un
  rol layer y salían como ventanas normales. Ahora `PanelConfigView` les asigna, al crearse la
  superficie (`SurfaceCreated`, como R4), una capa `overlay` sin teclado (`bwm-r5-edit-indicator`)
  en la pantalla de esas coordenadas; `screenFromWindow()` devuelve esa pantalla. (2) Cambiar el
  borde recreaba la vista en el runtime y cerraba el diálogo. Ahora, **mientras el diálogo está
  abierto**, el anfitrión hace lo de `PanelView` 6.7.5: fija el factor de forma, relee las
  preferencias del nuevo ámbito y mueve la misma superficie layer al nuevo borde
  (`BwmSurface::setPanelEdge`). Fuera del diálogo se mantiene el contrato de R4 (recrear y releer).
- **Otro monitor.** `screenToFollow` hacia otra salida lo atiende el runtime: cambia la
  asignación por descripción, recrea la vista allí y vuelve a abrir los ajustes. Sólo en la vista
  desechable con `--output` (`setOutputMovesAllowed`); los perfiles guardados no reescriben sus
  bindings y siguen rechazándolo con un error visible.
- **Alineación.** Funcionaba: con «Rellenar anchura» no cambia nada visible, igual que en Plasma.
  Con «Personalizada» o «Ajustar al contenido» se mueve a izquierda, centro o derecha (medido).
- **Flotante.** El camino funciona en Hyprland (medido abajo): el marco original flota y la
  ventana crece 16 px. En la vista de ensayo el panel ya está 64 px por encima del borde (para no
  tapar la barra diaria), así que el efecto es pequeño. No se reprodujo un fallo de escritura; la
  ausencia de `floating` en el archivo del usuario es compatible con haber elegido sólo
  «Applets only»/«Disabled».
- **Visibilidad.** Sin cambios: «Siempre visible» sólo existe con `--native-policy` (reserva
  espacio real); sin ella la vista de ensayo no reserva y lo rechaza. «Ocultar automáticamente»
  y «Esquivar ventanas» siguen sin controlador (los tienen desde la iteración 5).

### Pruebas

| Prueba | Resultado |
| :--- | :--- |
| `check-edit-mode-session.py` (nuevo, Hyprland real, MSI; raíces XDG temporales, sin dispositivos de entrada): acciona los combos del QML original y lee `hyprctl layers` | 11/11 pasos: rellenar 0,2048 2560×48; personalizado izquierda/derecha/centro 640×48 en x=0/1920/960; flotante 640×64; 7 flechas como capas dentro de su pantalla; arriba/izquierda/derecha/abajo sin cerrar el diálogo ni recrear la vista; paso al LG (4160,2048) con los ajustes reabiertos; `plasmashellrc` con `alignment=132`, `floating=1`, `panelLengthMode=2`; capas retiradas al final |
| `originalPanelSettingsEditMode` (ampliada): `moveTo(Izquierda)` y vuelta abajo con el diálogo abierto, ámbito `Vertical<alto>` | Pasa (CTest `isolated-local-configuration`) |
| `surface-geometry`, `check-isolated.py` completo (ejemplo KDE + AndromedaLauncher instalado del usuario, copiado a raíces temporales) | Pasan |
| Python R4 | 255 OK |

No probado: el clic físico en las flechas y combos (la prueba usa los manejadores del QML, no el
ratón), escalas fraccionarias y `--native-policy` con el diálogo.

### Límites

Autoocultar/esquivar, persistencia del cambio de monitor en perfiles, el resto de la lista de
pendientes y la aceptación del usuario.

## Iteración 3 (2026-11-19) — «Añadir widgets…» con el WidgetExplorer original

### Qué hay

- `widgetexplorerview.{h,cpp}` (propio) y `qml/WidgetExplorerHost.qml` (adapta la parte de
  `views/Desktop.qml` de plasma-desktop 6.7.5 que el explorador espera de su vista: el `id: root`
  con `widgetExplorer`, el `pendingUninstallTimer` y el `PlasmaCore.Dialog` lateral con su
  `Loader`). Carga sin modificar el `explorer/WidgetExplorer.qml` instalado y el tipo C++
  `WidgetExplorer` de `org.kde.plasma.private.shell`: lista, búsqueda, categorías, «Obtener
  widgets nuevos», arrastrar y `addApplet()` son los originales.
- La acción interna de libplasma «add widgets» emite `showAddWidgetsInterface`; `PanelViewHost`
  la atiende como `ShellCorona::toggleWidgetExplorer`: entra en modo edición y abre/cierra la
  barra lateral de ese panel. «Añadir widgets…» de los Ajustes del panel pasa por la misma acción.
  Los Ajustes se ocultan al abrirla y `WidgetExplorer.qml` los vuelve a abrir al cerrarla
  (`onClosed`), como upstream.
- La barra lateral es una capa `top` (`bwm-r5-widget-explorer`) anclada al borde izquierdo
  (derecho si el panel está a la derecha o el idioma es RTL), de arriba abajo, con teclado
  «a demanda». Zona exclusiva 0: Hyprland le deja fuera las reservas de los paneles; si el panel
  editado no reserva (vista de ensayo), se separa de él con un margen. Un `hyprland_focus_grab_v1`
  sobre la barra y el panel hace de la desactivación de ventana de KWin (`hideOnWindowDeactivate`);
  no cierra mientras el explorador lo impide (`preventWindowHide`, p. ej. al arrastrar).
- Sin modo edición del escritorio: al cerrarse la barra sin reabrir los Ajustes, se sale del
  modo edición.

### Pruebas

| Prueba | Resultado |
| :--- | :--- |
| `originalWidgetExplorerAddsToPanel` (offscreen, CTest `isolated-local-configuration`): «Añadir widgets…» desde el QML original, QML del explorador instalado, modelo y búsqueda, `addApplet('org.kde.plasma.analogclock')` en el panel, cierre que reabre los Ajustes, Escape sale del modo edición; la acción «add widgets» directa y su cierre por desactivación | Pasa (normal, tres repeticiones; también con ASan) |
| `check-edit-mode-session.py` en Hyprland (LG, panel desechable): paso nuevo con la capa medida en `hyprctl layers` frente a `monitors.reserved` | 16/16 pasos; capa 498×2004 en 2560,0 (alto de pantalla − 44 px de la barra diaria − panel de prueba con su hueco); Ajustes ocultos con la barra abierta; reloj digital añadido; al cerrar, Ajustes reabiertos; capas retiradas y foco devuelto |
| CTest normal (8 pruebas sin las `native-`) | Pasa |

Encontrado durante las pruebas: `fileUrl("explorer")` del paquete de shell es una carpeta; se
usa `explorer/WidgetExplorer.qml` como hace `Desktop.qml`. La prueba leía el `PanelConfigView`
después de que éste se borrara al ocultarse (como upstream): ahora usa un `QPointer`.

Con ASan, `isolated-local-configuration` falla después de todas las pruebas de interfaz, en el
ensayo de salida de sesión de §268: `panel-session.py stop` pide `transaction.lock` sin esperar
(`LOCK_NB`) mientras el anfitrión, más lento con ASan, aún lo tiene. No está relacionado con el
explorador. Corregido después (ver «Bloqueo de transacción del ensayo de salida»).

### Corrección tras la prueba del usuario

Con el ratón, la barra lateral se cerraba al poco de abrirse. El registro `bwm.r5.explorer`
(desactivado por defecto: `QT_LOGGING_RULES="bwm.r5.explorer.debug=true"`) mostró que el foco pasaba
de la barra al panel editado y que, a continuación, la barra se ocultaba. Hyprland 0.56.2 da el foco
de teclado a una capa con interactividad *on demand* cuando el puntero solo pasa por encima
(`InputManager::mouseMoveUnified`), y en modo edición el panel acepta entrada.
`Dialog::focusOutEvent` toma ese foco como un clic en la vista («viewClicked») y oculta la barra. En
KWin pasar el ratón no mueve el foco. `WidgetExplorerView` ya no deja que esa pérdida de foco oculte
la barra cuando el foco pasa al panel editado; un clic fuera de ambos sigue liberando la captura de
foco y la cierra. La prueba offscreen activa la barra y después el panel: falla sin la corrección y
pasa con ella.

En la siguiente prueba, la Vista de carpeta (`org.kde.desktopcontainment`, que el explorador
ofrece como widget) añadida al panel avisaba de que `isScreenUiReady` no existía. Es un método de
`ShellCorona`. `ViewCorona` lo implementa sin vista de escritorio: una pantalla está lista cuando
todos los paneles enlazados en ella son visibles y su containment informa `uiReady`. La prueba
offscreen comprueba la función.

**Aceptado por el usuario (2026-11-19):** con el ratón en el MSI, la barra «Añadir widgets…» se
queda abierta y añade widgets al panel («Sí, funciona»). Es una respuesta general, sin
desglose por caso (arrastre, doble clic, clic fuera). La corrección de `isScreenUiReady` es
posterior a esa prueba y no se ha vuelto a ver en sesión.

### Límites

Sin clic físico (la prueba llama a los manejadores del QML), ni arrastre de un widget al panel
en Hyprland, ni «Obtener widgets nuevos» desde aquí (KNS ya probado en R4). Desinstalar widgets
del usuario no se ha ejecutado. Alternativas de widgets (`AppletAlternatives.qml`) sin probar.

## Iteración 4 (2026-11-19) — Caja de herramientas del panel y menú del botón derecho

### Causa

Cada entrada en modo edición dejaba en el registro `kf.plasma.quick: Toolbox not loading…` y
`org/kde/panel/main.qml:135: TypeError: Cannot read property 'height' of null`. libplasma 6.7.5
(`ContainmentItem`, `Containment::restore`) lee el archivo `defaults` del paquete de shell de la
Corona: con él carga la caja de herramientas del panel (`[Panel] ToolBox`) y las acciones del ratón
de un panel sin acciones propias (`[Panel][ContainmentActions]`). El paquete de shell mínimo del
anfitrión no tenía ese archivo. Sin caja de herramientas, el `ConfigOverlay.qml` original (asas de
mover y quitar widgets en modo edición) se creaba con `toolBox` nulo; sin acción del botón derecho,
el clic derecho sobre el panel no abría ningún menú.

### Cambio

`src/bwm-plasma-host/shell/contents/defaults` con el grupo `[Panel]` de
`desktoppackage/contents/defaults` de plasma-desktop 6.7.5: `ToolBox=org.kde.paneltoolbox` y
`RightButton;NoModifier=org.kde.contextmenu`. Sin `[Desktop]`: el anfitrión no tiene escritorio.
No se toca código; los paquetes nombrados (`org.kde.paneltoolbox`, `org.kde.contextmenu`) se
cargan instalados y sin cambios.

### Pruebas

| Prueba | Resultado |
| :--- | :--- |
| `originalPanelToolBoxOverlayAndContextMenu` (offscreen): acción `RightButton;NoModifier` en el containment, caja de herramientas del paquete original, oculta fuera de edición; con «Enter Edit Mode» se crea el `ConfigOverlay` y aparece la caja; Escape los retira; clic derecho en el panel abre el `QMenu` de `org.kde.contextmenu` con «Enter Edit Mode» y «Añadir widgets…»; esta última abre el explorador | Pasa; sin el archivo `defaults` falla |
| CTest normal (8 pruebas sin las `native-`) y 255 pruebas Python de R4 | Pasan |

### Límites

Sin probar en Hyprland: el menú del botón derecho es un `QMenu` que se abre como `xdg_popup` del
panel (capa) y necesita el clic real del usuario. Tampoco se han probado con el ratón las asas del
`ConfigOverlay` (mover, cambiar de sitio y quitar widgets en el panel).

### Emergentes del panel en el centro de la pantalla

El usuario lo encuentra perfecto con el ratón, salvo que «algunos desplegables se abren en el centro
de la pantalla». `PackageWindows` sólo daba rol de capa anclada al panel a las ventanas emergentes
cuyo dueño era un widget del panel. El recuadro de cada widget en modo edición (`PopupPlasmaWindow`
de `ConfigOverlay.qml`: Configurar, Alternativas, Quitar) y el tooltip del botón de la caja de
herramientas pertenecen al propio containment del panel: quedaban como ventanas normales y la
colocación de Breeze las centraba. Ahora también reciben la capa las `PopupPlasmaWindow` cuyo ancla
visual está en el panel y cuyo dueño es el containment. Las ventanas que sólo nombran el containment
en su contexto QML (los Ajustes del panel, con sus flechas de «Set Position…») conservan su
tratamiento propio.

`check-edit-mode-session.py` añade `panelOwnPopupsInHyprland`: con los Ajustes abiertos muestra el
recuadro de un reloj analógico y el tooltip del botón ⚙, y comprueba en `hyprctl` que son capas y que
el proceso no crea ninguna ventana normal. El recuadro queda justo encima del widget (150×134 en
2560,1918; el widget empieza en y=2052, dentro del margen del panel, como en Plasma). Sin la
corrección el recuadro aparece como ventana normal (`ownClients: 1`). Ensayo completo en el LG 20/20;
CTest normal 8/8. El menú del botón derecho (`QMenu`) no se ha medido aquí: necesita un clic real.

El usuario lo vuelve a probar con el ratón tras la corrección: «ya va bien parece» (sin desglose por
desplegable).

## Bloqueo de transacción del ensayo de salida (2026-11-19)

El fallo con ASan de §268 venía del envoltorio, no del anfitrión. Tras el acuse de la skin
inicial, `command()` del envoltorio sigue en su último sondeo de 10 ms con `transaction.lock`
tomado. La prueba ya ve el acuse y lanza `session-exit`, que pedía el bloqueo con `LOCK_NB` y
fallaba con `BlockingIOError`. Con ASan el reparto de tiempos lo hacía frecuente.

`panel-session.py` espera ahora hasta 0,5 s (`LOCK_WAIT`) por el bloqueo en `command()`. Si
pasa ese tiempo sigue dando `BlockingIOError`. Así una salida de sesión que espera al guardado
sigue detectándose. Los límites de tiempo de los llamadores se mantienen: hook de cambio de
skin 3 s, `bwm-power` 8 s (2 + 5 + 0,5).

| Prueba | Resultado |
| :--- | :--- |
| Regresión nueva `test_short_lived_transaction_holder_is_waited_for_not_reported_busy` (otro hilo retiene el bloqueo 0,1 s) | Pasa; falla con `LOCK_WAIT = 0` |
| CTest `isolated-local-configuration` con ASan (`detect_leaks=0`) | Pasa tres veces seguidas |
| CTest normal sin `native-` | 8/8 |
| Python R4 | 256 |

## Iteración 5 (2026-11-19) — Autoocultar y esquivar ventanas

### Cómo lo hace Plasma 6.7.5

`PanelView` decide cuándo ocultarse (`restoreAutoHide`): no si el puntero o un arrastre están
sobre el panel, en modo edición, con el contenedor en estado de atención, o con una ventana
transitoria suya visible. Al salir el puntero espera 500 ms. `showTemporarily` lo enseña 3 s
(activación del contenedor, entrada de teclado, entrar en los ajustes). Ocultar lo hace KWin con
`kde_auto_hide_screen_edge_v1`: retira la superficie y la vuelve a mostrar al tocar el borde.
«Esquivar ventanas» sólo oculta mientras `touchingWindow` del `Panel.qml` es cierto. Ese valor
sale de un `TasksModel` con filtro por región, escritorio actual y actividad. Ninguno de los dos
modos reserva espacio.

### Cambio

- `panelviewhost.cpp` porta esa lógica (procedencia en un comentario). El ocultado es propio:
  el contenido se desliza fuera de la pantalla en 200 ms y la máscara de entrada se reduce a una
  franja de 2 px en el borde. Al entrar el puntero o un arrastre en ella, el panel vuelve, como
  con el borde de KWin.
- Sólo con `--native-policy`, donde la superficie toca el borde. La vista de ensayo sin política
  conserva su hueco y sigue rechazando estos modos.
- `surfaces.cpp`: los modos 1 y 2 no piden reserva. `panelviewsettings.cpp` admite
  `panelVisibility` 0–3 con la política nativa.
- El puente de tareas BWM se engancha también a la raíz de `Panel.qml`, cuyo `TasksModel` decide
  `touchingWindow`.
- El proveedor nativo de escritorios se retiraba con cualquier `hyprctl reload`. La opción se
  ponía en caliente y la recarga la devolvía a `false`. Lo corrige `modules/native_desktops.lua`.
  Sin el proveedor, el filtro por escritorio de `Panel.qml` no deja ventanas, y esquivar no
  ocultaría nunca.

### Pruebas

| Prueba | Resultado |
| :--- | :--- |
| `nativePanelAutoHideAndDodge` (QtTest offscreen): sin reserva; contenido desplazado y franja de 2 px; entrada que lo muestra y salida que lo oculta tras 500 ms; modo edición; ventana transitoria; estado de atención; `touchingWindow` en «Esquivar»; vuelta a «Siempre visible»; vista sin política rechaza los modos; `panelVisibility=1` en `plasmashellrc` | Pasa (normal y ASan) |
| `surface-geometry`: modos 1 y 2 sin reserva; 4 rechazado; vista de ensayo rechaza 1 y 2 | Pasa |
| CTest normal sin `native-` | 8/8 |
| `check-isolated.py` (ejemplos de libplasma y Andromeda, incluye toda la suite de interfaz) | Pasa |
| `autoHideEdgeStripInHyprland` (sesión real, LG, borde superior, `check-edit-mode-session.py`): capa de 640×48 pegada al borde sin cambiar `reserved`; puntero llevado al borde → aparece (eventos de entrada recibidos); alejado → se oculta; puntero y foco devueltos | Pasa (23/23 con el resto del ensayo, más 3/3 sólo este caso) |
| Python R4, con la prueba Lua de `native_desktops.lua` | 257 |
| Sesión: `hyprctl reload` con el módulo cargado y el opt-in activo | La opción sigue en `true`; sin errores de configuración |

En la primera ejecución en sesión el puntero llegó antes de que la nueva región de entrada
llegara al compositor y no apareció. El ensayo espera ahora 250 ms antes de moverlo.

### Límites

- Esquivar con ventanas reales no está medido. En esta sesión el proveedor ya estaba retirado
  por una recarga anterior, y sólo vuelve al iniciar sesión.
- La franja usa el borde de la superficie. Un panel en un borde compartido con otro monitor
  recibe la entrada al cruzar el puntero hacia el otro monitor (KWin tiene el mismo caso).
- Sin la animación propia de KWin: el desplazamiento es del contenido dentro de la superficie.
- Falta la prueba del usuario con el ratón.

El usuario lo prueba con el ratón en el MSI: «todo funciona menos el esquivar ventanas». Esquivar
no se ocultaba porque en esa sesión el proveedor de escritorios estaba retirado; no se ha
confirmado después de volver a iniciar sesión.

### Diagnóstico posterior y regresión de geometría (2026-11-19, §312)

Al retomar, `native-desktops.py status` sigue dando `enabled=true`,
`providerAvailable=false`, `arbitrationState=retired` en la misma instancia de Hyprland.
No se lanza el preview con `--native-desktops` mientras falte ese requisito. La retirada
explica la ausencia de escritorios del filtro, pero aún no demuestra que sea la única
causa del fallo observado con el ratón.

Nueva prueba `originalPanelDetectsWindowOverlapFromTaskSnapshots` en `test-paneltasks`:
carga el `Panel.qml` instalado con `PanelViewHost` y un widget sin modelo de tareas propio.
Sólo el registro del marco puede conectar entonces su `TasksModel` al puente BWM.
Un IPC ficticio entrega una ventana inicialmente alejada, después solapada, minimizada,
restaurada y alejada de nuevo. Se comprueban la región y el rol `Geometry`, las filas del
modelo original, `touchingWindow` y el ocultado/reaparición del panel, sin escribir esa
propiedad desde la prueba.

El filtro de actividad permanece activo, sin bus de sesión ni `kactivitymanagerd`:
no elimina la ventana. En **offscreen se desactiva sólo el filtro por escritorio actual**,
porque ese backend no dispone del proveedor Wayland. No valida ese filtro ni sustituye
la prueba en la sesión real tras volver a entrar.

Comprobado: compilación de `test-paneltasks`; CTest `isolated-local-configuration`
1/1 (42,50 s), con QtTest de tareas del panel 5/5, sin fallos ni omisiones.
No se ha cambiado código del controlador, reiniciado la sesión ni hecho una nueva prueba
visual. Sigue pendiente la prueba real de «Esquivar ventanas»; el resto de R5 permanece abierto.


### Aceptación de esquivar tras volver a iniciar sesión (2026-11-19, §313)

El usuario comunica que ha vuelto a iniciar sesión. `native-desktops.py status` confirma
una instancia nueva de Hyprland, `enabled=true`, `providerAvailable=true` y arbitraje
`active`. Se abre en segundo plano, como hijo de Hyprland, el preview desechable del reloj
analógico en el MSI con `--native-policy --edit-mode --task-actions --native-desktops`.
El control nativo confirma enlace y reanudación; el modelo recibe ventanas con el filtro
por escritorio activo.

El usuario elige «Esquivar ventanas», sale del modo edición y prueba solapar y retirar una
ventana. Confirma **«Sí, funciona en ambos sentidos»**. Aceptación funcional con el ratón
en el MSI; no es una medición de tiempos, escalas o todos los bordes. El preview se detiene
por `panel-session.py stop`, con acuse, y el registro queda inactivo. No se repite el ensayo
aprobado ni se reinicia Quickshell o el compositor.

## Iteración 6 (2026-11-19) — Mover y clonar paneles, con edición transaccional de perfiles

### Cambio

- Los perfiles de ensayo permiten «Set Position…» hacia otra salida y «Clonar panel» desde
  el `PanelConfiguration.qml` instalado. El runtime conserva IDs de containments independientes
  y asignaciones por descripción; reabre los Ajustes tras mover como en la vista desechable.
- `panelclone.cpp` adapta `ShellCorona::clonePanelTo` 6.7.5: copia configuración nativa del
  containment, applets y applets embebidos de bandeja, remapea `General/AppletOrder` a IDs
  nuevos y conserva subgrupos desconocidos. También copia todo el grupo `PlasmaViews/Panel N`
  de `plasmashellrc`, incluidos ámbitos por resolución. No hay un formato nuevo de tema.
- Los applets internos de la bandeja pueden haber inicializado ya su `KConfigLoader`. La
  copia se sincroniza antes de recargar su esquema nativo y notificar a QML. `Applet::config()`
  apunta al subgrupo Configuration de un applet, pero al grupo raíz de un containment:
  se copia el grupo completo correcto, incluidos atajos y claves desconocidas. El ensayo
  de bandeja prepara su propia opción: la prueba de ciclo anterior elimina su widget hijo.
- `ProfileStore::beginEditing/commitEditing`: los procesos `--serve-profile` y
  `--serve-selected-profile` retienen su lease y editan una copia privada. Al salir, guardan,
  sincronizan y destruyen Corona; después validan layout completo, preferencias, bindings y
  procedencia, publican una generación nueva y cambian `head.json` atómicamente. Sólo entonces
  toman el checkpoint. Una caída pierde la edición en curso y conserva la generación previa.
  No se permite checkpoint/restauración/exportación mientras esa edición está abierta.
- Sin `--native-policy`, varios paneles independientes pueden estar en la misma salida. Con
  la política nativa se mantiene el límite de uno por salida: mover o clonar hacia una salida
  ya ocupada se rechaza **antes** de cambiar bindings o crear containments. Falta coordinar
  las reservas. Las opciones originales siguen visibles.
- `panel-session.py status` incluye `runtime.panels[].capabilities` actualizado al consultar,
  con `autoHidden` y `touchingWindow`; antes esas propiedades existían sólo en el marco C++.

### Pruebas

- `profileEditingMovesAndClonesNativePanels`: dos widgets de la misma clase con opciones
  distintas y orden invertido, claves desconocidas de containment/vista, IDs nuevos,
  movimiento de salida y cambio de skin; rechazo de destino inválido y clonación desactivada;
  guardado incompleto rechazado sin cambiar el head, nueva generación completa, abandono de
  una edición posterior y fuente original intacta.
- `profileEditingFreshProcessReadback`: otro proceso, enumeración de pantallas invertida,
  dos paneles en la misma salida por descripción, opciones/IDs/orden y grosor conservados.
- `clonedNativeTrayKeepsEmbeddedOptionsAndNewIds`: opciones del widget hijo de bandeja e ID
  propio, también tras guardar y volver a cargar el layout.
- Hyprland real, LG: `check-edit-mode-session.py --case originalClonePanelInHyprland` pulsa
  mediante señal el manejador del indicador original «Clonar panel». Dos capas 640×48 en
  `(4160,2048)` y `(4160,64)`, widgets distintos; sin ventanas normales, reservas conservadas,
  capas retiradas y foco/puntero devueltos. **2/2 pasos**. No es un clic físico.

Verificación final: compilaciones normal y ASan completas; CTest normal sin pruebas
`native-` **8/8** (configuración local 45,00 s), `isolated-local-configuration` con
ASan (`detect_leaks=0`) **1/1** (50,35 s), incluidos los tres casos nuevos. Python R4: **257/257**. El ensayo de
clonación en Hyprland se repite tras los cambios del copiador y vuelve a pasar 2/2.

### Límites

R5 sigue abierta: `DesktopEditMode.qml` necesita todavía un anfitrión de escritorio;
coordinación de varios paneles con reservas en una salida, escala fraccionaria del editor,
migración de alineación/longitud de `bar.plasma`, comparación con Plasma real, arrastre al
panel y desinstalar/alternativas. No se sustituye
el panel diario ni se instala un perfil de producción. Los cambios del perfil se publican
al salir limpiamente; no se promete conservar una edición interrumpida o durabilidad ante
un corte de energía.


**Aceptación del usuario (2026-11-19):** con el ratón en el MSI, en la vista desechable sin
política de reservas, «Sí, clona y mueve bien». Confirma clonación y movimiento en general;
no se deduce una prueba del perfil persistente, de todos los destinos/bordes o de bandeja.
Preview detenido con acuse y registro inactivo; proveedor de escritorios sigue activo,
sin errores de configuración de Hyprland.


## Iteración 7 (2026-11-19) — Migración de alineación y longitud

### Cambio

`migration.proposal` acepta `output_sizes`, un mapa completo por descripción con tamaños
**lógicos** explícitos. Genera un contrato opcional `placementContractVersion=1`; C++
recalcula la conversión desde el origen archivado, sin confiar en las claves nativas
propuestas. No se toca la configuración del usuario ni se activa un perfil.

- `start/center/end` → alineaciones Qt 1/132/2 de `PanelView`.
- Longitud según el eje del borde, fracción limitada a 0,1–1 y mínimo de 160 (o el eje si es
  menor), como `PanelLogic.geometry`; redondeo lógico al entero más próximo, medios arriba.
- Fracción 1 sin flotación → FillAvailable; el resto → Custom con mínimo/máximo iguales.
- La flotación toma la longitud nominal sin ventana tocando, descontando el hueco archivado.
  La pintura/márgenes posteriores siguen al SVG de Plasma. El hueco sigue como dato diferido;
  no se inventa una opción nativa `floatingGap`. Desplazamiento inicial 0.
- Escritura en `PlasmaViews/Panel N` y sus grupos nativos `Defaults` y
  `Horizontal<ancho>`/`Vertical<alto>`. La verificación relee los dos destinos de longitud y
  detecta valores alterados, tamaños inválidos y propuestas inconsistentes.
- Los planes sin tamaños y todos los formatos de staging anteriores conservan su contrato;
  no se reinterpretan sus archivos. Un tamaño capturado no certifica la salida física:
  `outputGeometryVerified=false`, `activationAllowed=false`.

### Pruebas y límites

`migratedPlacementReadsOriginalPanelFrames`: cuatro bordes × tres alineaciones, dos salidas
lógicas de 1281×800 y 1728×960, lectura del `Panel.qml` instalado por `PanelRuntime`; longitudes,
alineación y modo reales de la vista, archivo de origen intacto y rechazo de longitud/tamaño
forjados. Pruebas Python de clamps, flotación, redondeo y tipos inválidos. La matriz de
`check-isolated.py` añade siete propuestas Python→C++→lectura nativa (dos salidas cada una).

Al ejecutar la matriz completa se encontró una expectativa anterior a la iteración 6:
exigía que `--serve-profile` conservara la generación. El ensayo ahora comprueba dos
generaciones nuevas tras dos cierres limpios, conserva intacto el layout original y exige
los mismos bindings/preferencias. No se cambia el nuevo contrato transaccional para acomodar
la prueba antigua.

Sin nueva prueba visual ni cambio de pantallas físicas. No se certifica comportamiento del
editor a escala fraccionaria por usar tamaños lógicos impares en un fixture. Siguen pendientes
el anfitrión de escritorio, reservas coordinadas de varios paneles, escala del editor,
comparación con Plasma real y arrastre/desinstalar/alternativas. La captura automática de
tamaños en una migración de producción tampoco está activada.


Verificación final de la iteración 7: CTest `isolated-local-configuration` **1/1 normal**
(49,27 s) y **1/1 ASan** con `detect_leaks=0` (55,02 s), incluida la posición lógica real del
marco para las 12 combinaciones. Python R4 **262/262** (23 de migración). Matriz
`check-isolated.py` completa con tres paquetes (dos ejemplos KDE y Andromeda), siete casos
nuevos de dos salidas y dos generaciones transaccionales tras cierres limpios: pasa.


## Iteración 8 (2026-11-19) — Varios paneles con reservas nativas

### Regla de Plasma y cambio

Se revisaron `ShellCorona::shouldPanelReserveSpace` y `PanelView::updateExclusiveZone` de
plasma-workspace 6.7.5. En cada salida y borde, sólo reserva el panel **normal más grueso**;
los demás no suman otra reserva ni se apilan artificialmente. Pueden solaparse. BWM desempata
por el menor ID de containment para que el propietario no dependa del orden de un hash.

`PanelRuntime::updateReservations` aplica esa selección a las vistas visibles/no retiradas.
Se reevalúa al cambiar grosor, visibilidad, borde, salida, vida de una vista o modo edición.
Ya no se rechaza un perfil, movimiento o clonación por tener otra vista en la misma salida.
Los modos y tamaños guardados no se cambian para seleccionar al propietario.

En edición se mantiene una zona positiva anterior; los paneles que no reservaban piden
el tamaño completo del marco. Ese valor se congela mientras se configura, como upstream;
al salir vuelven las reglas por borde y los modos AutoHide/Dodge/WindowsGoBelow sin reserva.
Las capacidades añaden `reservationOwner` y `editModeReservation`; son decisiones/peticiones,
no una certificación de área útil. Los commits de distintas superficies Wayland no son atómicos.

### Fallo real encontrado

La primera prueba con Hyprland dejó una reserva vieja o no activó la del nuevo propietario,
aunque `exclusiveZoneRequested` y el propietario calculado eran correctos. El cambio podía
no producir ninguna diferencia visual: `QWindow::requestUpdate()` dejaba el estado layer-shell
pendiente. `updatePanelPolicy` usa ahora `QQuickWindow::update()` para forzar el repintado/commit.
El mismo ensayo que fallaba pasa después, sin cargar/descargar plugins ni reiniciar el shell.

El ejecutable del ensayo también registra los tipos `org.bwm.plasma.host` antes de cargar
la representación compacta del reloj. Antes, al ejecutar sólo ese caso, el import faltaba;
no se ocultaron esos errores para aprobar la prueba.

### Pruebas

- `nativePanelsShareReservationsPerScreenAndEdge`: cuatro paneles, empate y cambio de grosor,
  cambio de modos, ocultar/mostrar, retirar propietario, cambiar borde/salida, clonar hacia
  una salida ocupada, cambio de skin y reservas temporales de edición. Incluye un propietario
  flotante que conserva su zona de grosor en vez de sumar otra vez sus márgenes.
- `nativePanelPolicyPersistsAndWithdrawsReservations` pasa ahora con dos paneles en bordes
  opuestos de la misma salida, en vez de exigir el antiguo rechazo.
- Hyprland real: `nativeMultiplePanelReservationsInHyprland`, MSI (el usuario tenía la vista
  activa en el LG). **10/10 pasos**: máximo 56, traspaso a 64, vuelta a 56 al autoocultar,
  retirada de la última reserva (0), restauración (64), edición (120), salida de edición
  (64), retirada del propietario (56), traslado al borde opuesto y limpieza. Se comprobaron
  capas, ausencia de ventanas normales del ensayo, reservas iniciales restauradas y devolución
  del puntero/foco, validando dirección y PID antes de restaurar el foco.

**Aceptación del usuario:** preview con `--native-policy` en el LG, clonación arriba y ventana
maximizada; confirma «Sí, se ajusta bien» al respetar ambas reservas y reajustar al quitar o
cambiar un panel. Aceptación funcional general; no se deducen todos los bordes, esquinas,
escalas o popups de esa respuesta. Preview detenido con acuse y registro inactivo;
`hyprctl configerrors` vacío.

### Límites

Sin sustitución del panel diario. Los paneles externos al anfitrión conservan sus reservas;
no participan en la elección interna de propietario. Falta certificar combinaciones de bordes
adyacentes/esquinas, anclaje de sus popups y editor a escala fraccionaria. R5 sigue abierta:
anfitrión de escritorio (`DesktopEditMode.qml`), comparación con Plasma real y flujos de
arrastre/desinstalar/alternativas. No se anuncia compatibilidad universal por estos ensayos.


Verificación final de la iteración 8: compilación normal completa, CTest normal sin
`native-` **8/8** (58,48 s), pruebas `surface-geometry` y `isolated-local-configuration`
con ASan (`detect_leaks=0`) **2/2** (52,37 s). La prueba real fue normal, no ASan nativo.
No quedan capas `bwm-r4-*` después de cerrar el preview.

## Iteración 9 (2026-11-19) — Alternativas de widgets, arrastre al panel, reordenado y desinstalación

### Qué hay

- **`AlternativesHelper` y `AppletAlternatives.qml`** (`alternativeshelper.{h,cpp}`,
  `PanelViewHost::showAlternativesForApplet`): adapta `shell/alternativeshelper.{h,cpp}` y
  `ShellCorona::showAlternativesForApplet` de plasma-workspace 6.7.5 (LGPL-2.0-or-later, Marco
  Martin). Registra `AlternativesHelper` en `org.kde.plasma.shell` (2.0 y 1.0) y conecta la señal
  `Plasma::Containment::appletAlternativesRequested` de la acción interna `alternatives` («Show
  Alternatives…»). Carga sin modificar el `explorer/AppletAlternatives.qml` instalado del paquete
  de shell. `loadAlternative` traslada el atajo global, sincroniza y copia el `config()` del
  widget saliente al nuevo, recarga su `configScheme()`, destruye el anterior y reconcilia
  `AppletOrder` si un layout offscreen sin pulir no colocó el nuevo en la ranura original.
- **Anclaje layer-shell del diálogo de alternativas**: `PopupAnchor` instala el filtro de eventos
  sobre `m_popup` para `QEvent::PlatformSurface` (`SurfaceCreated`) y deriva un tamaño inicial no
  nulo desde `mainItem` (+ `margins`) antes de `Dialog::showEvent`, porque una superficie
  `Top|Left` de LayerShellQt no admite `desiredSize` `0×0` al crearse. Además, tanto
  `PanelConfigView::eventFilter` como `AlternativesSurfaceFilter` filtran los `PlasmaQuick::Dialog`
  por la jerarquía `rootContext()` de su propio `SharedQmlEngine`, ya que todas las instancias de
  `SharedQmlEngine` comparten el mismo `QQmlEngine` del proceso (antes `PanelConfigView` tomaba el
  diálogo de alternativas como un indicador `bwm-r5-edit-indicator`). Tampoco se cierra cuando el
  puntero pasa por encima del panel editado, su `PopupPlasmaWindow` o los Ajustes del panel
  (foco *on demand* de Hyprland en hover).
- **Arrastre (`text/x-plasmoidservicename`), reordenado (`ConfigOverlay`) y desinstalación
  (`pendingUninstallTimer`)**: el `DropArea` original de `org.kde.panel`, el arrastre de
  `ConfigOverlay.qml` (`currentApplet` + `item.x` + `LayoutManager.insertAtCoordinates`) y el
  botón de desinstalar de `WidgetExplorer.qml` (`removeAllInstances` +
  `pendingUninstallTimer.uninstall()`) funcionan sin parches sobre los QML instalados.

### Pruebas

| Prueba | Resultado |
| :--- | :--- |
| `originalAppletAlternativesDragAndUninstall` (`test-ui.cpp`, registrada en `check-local.py`): (1) acción `alternatives` del reloj analógico → `AppletAlternatives.qml` con modelo poblado, Escape cierra sin cambiar, reapertura + `loadAlternative('org.kde.plasma.digitalclock')` conserva el slot en `AppletOrder`; (2) `QDragEnterEvent`/`QDropEvent` con `text/x-plasmoidservicename` sobre el `DropArea` de `org.kde.panel` inserta el widget en las coordenadas soltadas; (3) `ConfigOverlay` mueve un widget de la primera a la última posición y actualiza `AppletOrder`; (4) paquete local desechable instalado en `XDG_DATA_HOME`, añadido al panel, marcado `pendingUninstall` en el explorador (`removeAllInstances` lo retira del panel) y desinstalado de disco al disparar `pendingUninstallTimer` | Pasa (CTest `isolated-local-configuration`, normal y ASan) |
| `panelOwnPopupsInHyprland` (`check-edit-mode-session.py`, LG, sesión Hyprland real): paso `applet-alternatives-popup-and-switch` añadido: dispara `alternatives`, verifica la capa `bwm-r4-popup` (`368×251` en `2560,1801`, justo encima del widget en `2568,2052 40×40`, `0` toplevels propios), cambia el reloj analógico por `org.kde.plasma.digitalclock`, cierra la capa y restituye puntero y foco verificando dirección + PID | Pasa (suite completa `check-edit-mode-session.py` en LG, 38 pasos, todos `passed: true`, sin capas residuales) |
| Compilación y CTest normal (`-E "^native-"`) | **8/8** (59,67 s) |
| Compilación y CTest ASan (`detect_leaks=0`, `surface-geometry` + `isolated-local-configuration`) | **2/2** (54,56 s) |
| Suite Python R4 (`test_r4_*.py`) | Pasa |

### Verificación interactiva con ratón en sesión real (2026-11-20)

Con autorización explícita del usuario y sin alterar su skin activa (`retro`), se lanzó
`bwm-plasma-host --follow-panel-preview` en raíces XDG temporales sobre el monitor LG (`DP-1`,
`2560,0 3840×2160`) y se ejecutaron los 6 escenarios con eventos reales de ratón y teclado
(`/dev/uinput`), verificando capas con `hyprctl layers`, estado en disco y recortes visuales
(borrados al terminar):

1. **Alternativas de widgets**: hover sobre el reloj analógico → popup de asa de `ConfigOverlay`
   (`bwm-r4-popup`, `0` clientes propios) → clic real en «Show Alternatives…» → `AppletAlternatives.qml`
   (`368×254` en `2560,1798`, `0` clientes propios); sobrevive al pasar el puntero por el panel, se
   cierra con Escape, se cierra al pulsar fuera en el escritorio vacío del LG (`FocusGrab`), y al hacer
   clic en `Calendar` se cierra y sustituye el 1.er reloj en su posición.
2. **Arrastre desde el explorador**: clics reales en `Add New` → `Widgets…` abren `bwm-r5-widget-explorer`
   (`2560,26 498×2022`) ocultando Ajustes del panel; arrastre Wayland `wl_data_device` (`BTN_LEFT` +
   movimiento continuo) del widget local desechable `org.bwm.r5.disposable` hasta el panel (el explorador
   permanece abierto durante el arrastre y el widget queda soltado y guardado en `appletsrc`).
3. **Reordenado en modo edición**: arrastre físico del 1.er widget por delante de los otros dos en el panel;
   `AppletOrder` pasó de `2;3;4` a `3;4;2` y se guardó.
4. **Retirar todas las instancias y desinstalar**: clics reales en `Remove all instances`, `Mark for
   Uninstallation` y el pie `Uninstall (1 Widget)`; retirado del panel y borrado del `XDG_DATA_HOME` temporal.
5. **Set Position… y Clone Panel**: clics reales en `Set Position…` → 3 flechas `bwm-r5-edit-indicator` en el
   LG → clic en la flecha superior movió el panel a `2560,64 3840×48`; clic real en `Clone Panel` → 3 flechas
   → clic en la flecha lateral creó un 2.º `bwm-r4-preview` (`6288,0 48×2160`, `AppletOrder=7;8;6`, `0`
   clientes propios).
6. **Limpieza**: 0 capas `bwm-r4-*`/`bwm-r5-*` residuales; cursor y ventana activa restaurados.

## Iteración 10 (2026-11-20) — Bordes adyacentes, esquinas, popups y escalas fraccionarias

### Qué hay

- **Anclaje bilateral para `FillAvailable` en layer-shell** (`surfaces.{h,cpp}`): igual que
  `PanelView::updateLayerWindow` (plasma-workspace 6.7.5), un panel con longitud «Rellenar anchura/altura»
  (`lengthMode == 0`) ancla ambos bordes perpendiculares (`AnchorLeft|AnchorRight` en horizontal,
  `AnchorTop|AnchorBottom` en vertical) para que Hyprland (`IHyprRenderer::arrangeLayerArray`) lo ajuste
  dentro del `usableArea` cuando otro panel reserva un borde adyacente, sin desbordar ni solapar la esquina.
  `Custom` y `FitContent` conservan un único ancla lateral y tamaño explícito, acotados a `bwmPanelBounds`.
  `updatePanelPolicy` evita rebotes redundantes de `setExclusiveZone(-1)` cuando sólo cambia el eje estirado
  por un `configure` del compositor; `PanelViewHost::resizeEvent` sincroniza el tamaño del `rootObject()`
  y la máscara en los redimensionados del compositor.
- **Rectángulo disponible y contexto de bordes por salida** (`panelruntime.cpp`, `panelviewhost.{h,cpp}`,
  `viewcorona.{h,cpp}`): `PanelViewHost` mantiene un orden monótono de creación de superficie (`surfaceOrder()`)
  en `QEvent::Show` que refleja el orden de `CLayerSurface` en Hyprland. `PanelRuntime::updateReservations()`
  calcula por pantalla el `usableArea` de cada panel y el rectángulo disponible final tras todas las reservas
  activas, publicándolos en `ViewCorona::setScreenAvailableRect` (adaptando `ShellCorona::_availableScreenRect`)
  y en `BwmSurface::setPanelLayoutContext` (`bwmPanelBounds`, `bwmAvailableRect`). `dropAll()` limpia los
  rectángulos publicados al desactivar la skin.
- **Popups de paneles con reserva en esquinas** (`surfaces.cpp`): cuando `PopupAnchor` ancla un popup
  (`PanelConfigView`, `AppletAlternatives`, popups de widgets) a un panel que reserva espacio
  (`bwmExclusiveZoneRequested > 0 && !m_requestedPosition`), usa `exclusiveZone = 0` y anclas alineadas al
  borde del panel (`Bottom|Left`, `Top|Left`, `Left|Top`, `Right|Top`), añadiendo sólo el saliente flotante
  `max(0, panelCross - zone)` en el eje del panel y la alineación respecto a `area` en el eje perpendicular.
  Así respeta automáticamente tanto otros paneles adyacentes del anfitrión como barras externas del compositor
  (p. ej. `omarchy-bar` o la barra diaria).
- **Corrección de foco de `PanelRulerView` y refresco de indicadores/explorador** (`panelconfigview.cpp`,
  `widgetexplorerview.cpp`): `PanelRulerView` pasa a `KeyboardInteractivityNone` + `setActivateOnShow(false)`
  (`Ruler.qml` sólo usa puntero), evitando que al activar «Personalizada» le robe el foco de teclado (Escape)
  a `PanelConfigView` en sesiones de un solo monitor. `placeIndicator` deriva tamaño inicial no nulo desde
  `mainItem` + `margins` y llama a `quick->update()` si ya es visible; `WidgetExplorerView::place()` llama a
  `m_sidePanel->update()` cuando es visible.
- **Verificación de escala fraccionaria en salida headless temporal** (`check-edit-mode-session.py
  --fractional-scale`, `test-editmode-session.cpp`): crea una salida `BWMR5-*` temporal con Hyprland
  (`1920×1080@60`) a escalas `1.25` (`1536×864`), `1.5` (`1280×720`) y `1.6` (`1200×675`), verifica el
  `devicePixelRatio()` de ventana vía `wp_fractional_scale_v1`, panel inferior, Ajustes del panel, 3 flechas
  de `Set Position…`, cambio a borde izquierdo respetando la reserva superior, `AppletAlternatives`,
  `WidgetExplorer` y retirada completa sin alterar ningún monitor físico (`physicalOutputsUnchanged: true`).

### Pruebas

| Prueba | Resultado |
| :--- | :--- |
| `surface-geometry` (`test-surfaces.cpp`): anclaje bilateral `FillAvailable` y caso nuevo `adjacentEdgeLayoutAndCornerPopups` | Pasa (normal y ASan) |
| `adjacentEdgesCornersAndAvailableRect` (`test-ui.cpp`, registrada en `check-local.py`): 3 paneles simultáneos (arriba 48 + izquierda 56 + derecha 44 personalizado) en salida lógica `1536×864`, `availableScreenRect` (`56,48 1436×816`), `bwmPanelBounds` por orden de superficie, `PanelConfigView` y `AppletAlternatives` contenidos en `expectedAvail` sin solapar ningún panel, retirada al pasar izquierda a AutoHide y restauración al salir de `plasma` | Pasa (CTest `isolated-local-configuration`, normal y ASan) |
| `check-edit-mode-session.py --output "LG Electronics LG ULTRAFINE 405NTVS2J655"` (Hyprland real, suite completa): incluye `nativeAdjacentEdgesAndCornerPopupsInHyprland` (arriba `2560,26 3840×48` + izquierda `2560,74 56×2086`, Ajustes `2616,846 420×542`, Alternativas `2616,74 368×251`, Explorador `2616,74 498×2086`, 3 bordes simultáneos arriba+izquierda+abajo disjuntos, limpieza completa) y todos los casos anteriores | Pasa (exit 0, todos los pasos `passed: true`, 0 capas residuales) |
| `check-edit-mode-session.py --fractional-scale` (Hyprland real en salida headless temporal `BWMR5-*`): escalas `1.25` (`1536×864`), `1.5` (`1280×720`) y `1.6` (`1200×675`), `windowDpr` exacto en las tres, todos los pasos (panel, Ajustes, 3 flechas, borde izquierdo, Alternativas, Explorador, limpieza) | Pasa (21/21 pasos `passed: true`, `physicalOutputsUnchanged: true`, salida `BWMR5-*` eliminada) |
| Compilación y CTest normal (`-E "^native-"`) | **8/8** (61,92 s) |
| Compilación y CTest ASan (`detect_leaks=0`, `surface-geometry` + `isolated-local-configuration`) | **2/2** (56,42 s) |
| Suite Python R4 (`test_r4_*.py`) | **262/262 OK** |
| Estado de Hyprland al terminar (`hyprctl layers`, `hyprctl configerrors`) | 0 capas `bwm-r4-*`/`bwm-r5-*`, 0 errores |

### Límites y pendiente de R5

- La prueba de escalas fraccionarias se ha ejecutado en una salida headless temporal (`BWMR5-*`) con los
  manejadores del QML original (no con ratón físico sobre un monitor físico escalado, ni comprobación visual
  subpíxel de texto/bordes a `1.25`/`1.5`/`1.6`).

## Iteración 11 (2026-11-20) — Anfitrión de escritorio y `DesktopEditMode.qml`

### Qué hay

- **`DesktopViewHost`** (`desktopviewhost.{h,cpp}`): adapta `shell/desktopview.{h,cpp}` de
  plasma-workspace 6.7.5 (GPL-2.0-or-later) sobre `PlasmaQuick::ContainmentView` y `LayerShellQt`.
  Carga sin modificar el `views/Desktop.qml` instalado (que instancia `views/DesktopEditMode.qml` sin
  modificar cuando `corona.editMode == true`) con el containment real `org.kde.plasma.folder`.
- **Contrato de escritorio y acoplamiento con paneles** (`viewcorona.{h,cpp}`, `panelviewhost.{h,cpp}`,
  `panelconfigview.cpp`, `panelruntime.cpp`, `shell/contents/defaults`):
  - `shell/contents/defaults` añade los grupos `[Desktop]` y `[Desktop][ContainmentActions]` de
    plasma-desktop 6.7.5 (`org.kde.plasma.folder`, `org.kde.contextmenu`, `org.kde.paste`).
  - `ViewCorona` expone `panelBeingConfigured`, `enteredEditModeViaDesktop()`, `showAddPanelContextMenu`
    (con «Default Panel» y «Empty Panel» emitiendo `addPanelRequested`) y las acciones de Corona
    `"add panel"` y `"edit mode"` (texto dinámico Enter/Exit Edit Mode).
  - `PanelViewHost` expone `relativeConfigRect` y sincroniza `ViewCorona::setPanelBeingConfigured`;
    `PanelConfigView::hideEvent` respeta `enteredEditModeViaDesktop()` de modo que cerrar Ajustes del
    panel mantiene abierto `DesktopEditMode.qml` cuando la edición se inició desde el escritorio (y
    sigue saliendo de edición cuando se inició desde un panel).
  - `PanelRuntime::setAssignments` permite coexistir containments de escritorio en la misma `ViewCorona`
    junto a los paneles gestionados por el runtime.
- **Superficies layer-shell en Hyprland**:
  - `bwm-r5-desktop` en `LayerBackground` (`AnchorTop|AnchorBottom|AnchorLeft|AnchorRight`,
    `exclusiveZone = -1`, `wantsToBeOnActiveScreen = false`, ligado explícitamente a `m_targetScreen`
    para no saltar al monitor enfocado al crear/redimensionar).
  - El `sidePanel` original de `Desktop.qml` (`explorer/WidgetExplorer.qml`) se intercepta en
    `SurfaceCreated` filtrando por `rootContext()` y recibe capa `bwm-r5-desktop-explorer` (`LayerTop`,
    `exclusiveZone = 0`, `FocusGrab`, tolerando hover sobre el escritorio/paneles); `AppletAlternatives.qml`
    sobre widgets del escritorio se mapea como `bwm-r5-desktop-popup` (`LayerOverlay`, `exclusiveZone = 0`).

### Pruebas

| Prueba | Resultado |
| :--- | :--- |
| `originalDesktopEditModeHost` (`test-ui.cpp`, registrada en `check-local.py`): `Desktop.qml` + `DesktopEditMode.qml` con `org.kde.plasma.folder` + panel inferior 48 px en salida `(2000,0 1536×864)`; `strictAvailableScreenRect` local `(0,0 1536×816)`; entrada por acción `"edit mode"`, `open === true`, `scale < 1.0`; apertura/cierre de `PanelConfigView` preservando `DesktopEditMode`; «Add Widgets…» abre el `sidePanel` original de `Desktop.qml` y añade `org.kde.plasma.analogclock`; `AppletAlternatives` cambia a `org.kde.plasma.digitalclock`; menú «Add Panel» («Default Panel» / «Empty Panel»); salida con Escape y persistencia en `appletsrc` | Pasa (CTest `isolated-local-configuration`, normal y ASan) |
| `originalDesktopEditModeInHyprland` (`check-edit-mode-session.py`, LG, sesión Hyprland real): `bwm-r5-desktop` `2560,0 3840×2160` (`0` toplevels), `DesktopEditMode.qml` activo (`scale: 0.88`, `strictAvail: 0,0 3840×2112`), traspaso de `PanelConfigView` (`4270,1570 420×542`, mantiene edición al cerrarse), `bwm-r5-desktop-explorer` (`2560,26 498×2086` despejando barra superior 26 px + panel inferior 48 px, `0` toplevels, añade reloj), `bwm-r5-desktop-popup` (`4361,1224 368×251`, `0` toplevels, cambia a `digitalclock`), limpieza completa | Pasa (6/6 pasos `passed: true`, 0 capas residuales) |
| Compilación y CTest normal (`-E "^native-"`) | **8/8** |
| Compilación y CTest ASan (`detect_leaks=0`, `surface-geometry` + `isolated-local-configuration`) | **2/2** (58,91 s) |
| Suite Python R4 (`test_r4_*.py`) | **262/262 OK** |
| Escalas fraccionarias (`check-edit-mode-session.py --fractional-scale`, `1.25`/`1.5`/`1.6`) | **21/21 pasos `passed: true`**, `physicalOutputsUnchanged: true` |
| Estado de Hyprland al terminar (`hyprctl layers`, `hyprctl configerrors`) | 0 capas `bwm-r4-*`/`bwm-r5-*`, 0 errores |

### Límites y pendiente de R5

- `DesktopViewHost` está implementado y verificado en pruebas aisladas (offscreen normal/ASan y Hyprland
  real en capa `background`), sin sustituir el fondo ni el panel diario de Breeze y sin verificación
  visual directa ni interacción física con ratón sobre `DesktopEditMode.qml` todavía.
- Pendiente para cerrar R5: comparación visual con Plasma real (incl. `DesktopEditMode.qml`, paneles y
  escalas fraccionarias) y aceptación final del usuario. No se sustituye el panel diario.



