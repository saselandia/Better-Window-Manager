# Breeze III — T0: cierre de las comprobaciones de Breeze II

Fecha: 2026-11-26. Plan: [BREEZE_PLAN_V3.md](BREEZE_PLAN_V3.md). Base: `0b82db7` + plan v3.

## Estado de partida (comprobado por el asistente)

- Skin `plasma`; `bwm-plasma-host` activo y listo (PID 239653, binario `f2f9d08199060900…`, el de §384).
- En cada monitor (LG `DP-1`, MSI `DP-2`): `swww-daemon`, `bwm-r5-desktop`, `bwm-r4-native-policy`;
  ninguna capa del respaldo de Quickshell.
- Paneles: dos en el LG (contenedor 1, inferior) y MSI (contenedor 15, inferior, con reloj analógico).
  Escritorios sin widgets. Plasmoides de terceros instalados: AndromedaLauncher y KdeControlStation
  (ninguno en el panel).
- A petición del usuario («hazlo tú»), el asistente hizo las pruebas con un ratón/teclado virtual
  (uinput) en workspaces vacíos (MSI 9, LG 11) y una ventana kitty desechable. Se detuvo al ver que
  el usuario volvía a usar el MSI (un clic cayó en su ventana de Discord, sin efecto). Al terminar:
  ventana y regla temporal retiradas, host reiniciado sin depuración, LG en el workspace 10 y foco
  devuelto a la misma ventana (dirección comprobada).

## Comprobaciones

| # | Caso | Qué debe verse | Resultado |
| :--- | :--- | :--- | :--- |
| 1 | Desplegables de la bandeja (Bluetooth, volumen, red, notificaciones, portapapeles) | Pegados al panel sobre su icono, sin salir centrados ni como ventana; se cierran al pulsar fuera o Escape | Correcto: los cinco abren anclados sobre su icono (440×440 en `2077,1672` para la bandeja, 404×459 el calendario), icono resaltado; Escape y clic en el escritorio los cierran |
| 2 | Kickoff con Super y con clic, en los dos monitores | Se abre y queda abierto; bordes rectos del lado del panel y del borde de pantalla | **Fallo encontrado y corregido** (ver abajo). Tras la corrección: clic en el MSI 3/3 y en el LG, Super en ambos, se quedan abiertos y Escape/Super los cierran. Bordes ya comprobados en §384 |
| 3 | AndromedaLauncher añadido al panel | Su menú se abre anclado y no se cierra solo | Correcto (segunda tanda): cambiado desde «Alternativas» del lanzador; con clic y con Super se abre anclado en la esquina y sigue abierto, el clic en el escritorio y Escape lo cierran. Vuelto a Kickoff y restaurada la copia previa del panel (Kickoff conserva su identificador 42) |
| 4 | Widget en el escritorio (modo edición → Añadir widgets → arrastrar al escritorio) y su desplegable o configuración | Desplegable anclado al widget; un clic en el escritorio lo cierra | **Fallo encontrado y corregido** (ver abajo). Tras la corrección: widget Bluetooth en el escritorio con su icono, desplegable anclado encima con el resaltado, cerrado con clic en el escritorio y con Escape; menú del widget correcto y «Quitar» funciona. Widgets de prueba retirados |
| 5 | Modo edición con ventanas abiertas | Al entrar, las ventanas se minimizan y el escritorio se aleja; al salir vuelven en su sitio | Correcto: al entrar (desde el panel y desde el escritorio) la ventana de prueba pasa a `special:minimized` y el escritorio se aleja; al salir vuelve al workspace 9 en `960,1216 640×400`. Con los Ajustes del panel abiertos la vista alejada queda a la derecha del diálogo: es el cálculo de `editModeRect` del `Desktop.qml` original con un panel de ancho completo |
| 6 | Bordes con otro estilo de Plasma (p. ej. Sweet) | Las esquinas siguen el SVG del nuevo estilo y siguen rectas del lado del panel | Correcto: con Sweet, Kickoff, Bluetooth y calendario toman colores, acento y esquinas de Sweet, rectas del lado del panel y del borde de pantalla. Vuelto a `default` (`plasmarc` restaurado) |
| 7 | Miniaturas de un grupo de 2–3 ventanas al pasar el ratón | Tamaño como en Plasma (~300 px por ventana); al pasar a otra app se ajusta | Correcto: Firefox con 2 ventanas 602×316 (con controles multimedia), Steam con una 296×195; al volver al grupo, otra vez 602×316 |

## Fallos encontrados y correcciones

### Kickoff se cerraba al pulsar su icono (con Super no)

Al pulsar, el menú aparecía y desaparecía en menos de 0,3 s. Con la descripción emergente
«Application Launcher» visible (el puntero lleva un momento sobre el botón), `PopupAnchor::tryFocusGrab`
la metía en la captura de foco como acompañante pasivo del panel. Kickoff oculta esa descripción al
expandirse; `FocusGrab` suelta la captura entera cuando se oculta cualquier miembro (§363), así que el
teclado volvía a la ventana anterior y `PopupPlasmaWindow` cerraba el menú. Con Super no hay descripción
visible, por eso funcionaba. El registro de depuración (`bwm.r4.anchor`) mostraba `windows 3`.

Corrección: `FocusGrab::start(windows, transient)`. Las ventanas transitorias (descripciones sobre el
panel) entran en el segundo commit; al ocultarse o destruirse sólo se quitan de la captura
(`remove_surface` + commit), sin soltarla. Los miembros obligatorios (popup y panel) la siguen soltando
como antes. Prueba nueva `hidingTransientTooltipKeepsTheGrab` en `test-focus-safety`.

Comprobado: `test-focus-safety` 12/12 en Hyprland anidado, CTest del host 8/8 (`build/bwm-plasma-host-tests`),
host instalado (SHA256 `bb0c73db129c5757…`) y clic real en Kickoff 3/3.

### Widgets del escritorio con icono genérico y sin desplegable

En el escritorio (y en cualquier sitio que muestre un widget en forma compacta sin `CompactApplet`
propio) los widgets salían con el icono genérico de Plasma y al pulsarlos daba
«Cannot assign to non-existent property "expanded"». El paquete de shell del host tenía un
`DefaultCompactRepresentation.qml` mínimo propio de R4 que no recibe `plasmoidItem` ni usa `Plasmoid.icon`.
Ahora `shell/contents/applet/DefaultCompactRepresentation.qml` es el original de plasma-desktop 6.7.5, y se
añade también su `AppletError.qml`, que faltaba (vista de error de un widget que no carga). Basta con
reiniciar el host: el paquete se carga del repo.

### Comportamientos que parecen fallos y son los de Plasma

- Con los Ajustes del panel abiertos, el escritorio alejado queda a la derecha del diálogo
  (`editModeRect` en `Desktop.qml` con un panel de ancho completo).
- La descripción de un icono de la bandeja puede verse encima de su desplegable abierto:
  `PlasmoidItem.qml` de la bandeja la deja activa para los iconos de la parte visible.
- El explorador de widgets lista «Activity Bar» y «Activity Pager» aunque BWM no tiene actividades
  (se descartan en el plan; se ocultarían en T2).

## Resultado

Los siete casos están comprobados. Dos fallos corregidos. Sesión devuelta a su estado: workspaces 1 y 10,
foco en la misma ventana, estilo `default`, panel restaurado de la copia, ventana y regla de prueba
retiradas, host sin depuración.
