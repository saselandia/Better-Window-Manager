# Ajustes de Breeze después de F13

Comprobado el 2026-11-11. Cambios solicitados tras usar el panel portado.

| Problema | Corrección | Comprobado |
| :--- | :--- | :--- |
| Salida lenta a Retro | El manejador SIGTERM del supervisor ya no llama wait/poll de forma reentrante. La espera normal tiene plazo y comprueba el candado, no la existencia de un posible zombi en /proc. | Espera del auxiliar ~5,03 s → ~0,07 s. Cambio completo ~7,7 s → ~2,5–3 s en este equipo; tematizar fondo/apps aún cuesta tiempo. |
| Selector de skins | Recuperado el diseño anterior en modules/plasma/skinPicker, IPC plasmaThemePicker y Alt+T; sigue los colores/fuente y bordes del panel actuales. | Abre/cierra en el shell; miniaturas y aspecto revisados. |
| Panel redondeado pegado al borde | Se retiran todos los bordes que alcanzan los límites de pantalla, como Plasma PanelView::updateEnabledBorders. | Panel completo con laterales sin esquina SVG; recorte revisado. Un panel flotante sigue respetando el tema original. |
| Botones/iconos poco visibles | Complementary como grupo de color del panel, Kickoff 32 px, applets 22 px; SVG widgets/tasks original para las tareas. | Carga real y recorte del extremo izquierdo revisado. No se impone una forma propia por encima de los temas de KDE. |
| Tarea que no sube al frente | Nueva operación focus de kwin-window, con PID esperado; enfoca y eleva expresamente. | Mapeo 10/10 ventanas; la operación hace activa a ChatGPT. Foco anterior restaurado. Clic central sigue abriendo instancia; clic en la activa mantiene minimizar. |
| Applet que no se cierra | Mismo botón alterna, el grab permite el panel y Escape cierra desde contenido/atajo de aplicación. | QtTest pulsa el botón del fixture, vuelve a abrirlo y pulsa Escape; cierra ambos casos. Sin modificar red/Bluetooth/sonido reales. |
| Fuente incorrecta | Noto Sans 10 para interfaz y Hack para monoespaciada, según el KCM original; requisitos declarados. | KDE/Qt/Kirigami y perfil Breeze muestran Noto Sans 10; Retro mantiene JetBrains Mono NF. Configuración de usuario en bwm/user intacta. |

No se instalaron paquetes: las fuentes ya estaban disponibles. Se actualizaron los requisitos
y su tabla. Los cambios de preferencias de fuente sólo afectan a Breeze; los KCM/temas pueden
seguir cambiándola, y la configuración en texto del usuario conserva su prioridad.
Las dos imágenes del selector/panel se borraron después de revisarlas.

## Arrastre de ChatGPT y ventanas similares

ChatGPT se ejecuta como XWayland con _MOTIF_WM_HINTS sin decoración del servidor. No se debe
poner encima una segunda barra. En las fuentes de Hyprland 0.56.2, XWM.cpp anuncia
_NET_WM_MOVERESIZE en _NET_SUPPORTED pero handleClientMessage no implementa esa operación.

Breeze escucha ese mensaje de clientes en el root X11 mediante su conexión XCB existente.
Sólo comienza movimiento estándar (dirección 8, botón 1) para una ventana flotante mapeada
bajo el puntero, con el botón físico pulsado y fuera de fullscreen. No usa nombres de apps ni
supone que los primeros N píxeles sean una barra. La dirección 11 cancela sólo su propio gesto.
Las apps Wayland mantienen su protocolo nativo.

Referencias primarias:
- [EWMH, _NET_WM_MOVERESIZE](https://specifications.freedesktop.org/wm/latest/ar01s04.html).
- Hyprland 0.56.2, src/xwayland/XWM.cpp, handleClientMessage/initAtoms (fuente local cotejada).
- Plasma 6.7.5, plasma-workspace/shell/panelview.cpp y kcms/fonts/fontssettings.kcfg.

La política tiene pruebas puras de botón, foco bajo puntero, modo y estado. El plugin se
compiló con -fno-gnu-unique y se instaló con make install (reemplazo atómico). El proceso actual
sigue usando el binario anterior: **falta cerrar sesión/entrar para cargar esta parte**.
No se ha probado físicamente el arrastre de ChatGPT con el nuevo binario, ni se hizo carga en
caliente. Tras entrar, comprobar arrastre de ChatGPT/otras apps Electron XWayland, soltar el
botón, cancelación y snapping; no debe aparecer otra barra ni interferir con botones o pestañas.

## Pruebas

Suite general: 374 pruebas, 65 omitidas, sin fallos. Quince pruebas QML de applets con datos
controlados pasan; repetida la comprobación de toggle/Escape tras añadir el clic real al fixture.
Pruebas de foco/identidad y del manejador de parada pasan. qmllint ejecutado con avisos de
imports/metadatos dinámicos, complementado con carga real. Hyprland --verify-config y
configerrors se comprueban al cerrar este cambio; bwm check de Breeze correcto.

Los avisos previos de traducción en_US, UPower ausente y ToolbarTabBar no se presentan como
resueltos por este cambio.

## Corrección del clic directo y geometría (2026-11-12)

La comprobación anterior de focus verificaba el destino de la acción, pero no pulsaba
el icono del panel. El usuario confirmó que seguía fallando. Reproducido con el delegado
real dentro de un ListView: la versión anterior registra **0 clics izquierdos** y la
miniatura registra 1 activación. El DragHandler del icono interfiere con el MouseArea padre.

Task usa ahora Item + TapHandler/HoverHandler, como Task.qml de Plasma 6.7.5. La rueda
conserva un MouseArea exclusivo sin botones: WheelHandler no recibía ese evento en la
prueba dentro del ListView. Se mantienen las acciones del adaptador y su identidad por PID.

La disposición elimina los 2 px añadidos entre tareas y el margen del eje corto aplicado
a todo el panel. Los marcos llegan al borde exterior; las dimensiones de iconos/tareas
salen de los márgenes normales del SVG, con métricas estables al enfocar o pasar el ratón,
según Task.qml y code/LayoutMetrics.js de plasma-desktop 6.7.5. Se conserva el dibujo del
tema para normal/foco/minimizado; no se altera su color ni se ocultan sus estados.
Los fondos de las aplicaciones abiertas siguen siendo los del tema activo.

La prueba opcional tests/test_plasma_task_input.py pulsa centro y margen del botón,
botón central/derecho, rueda, arrastra y pulsa la miniatura real del PopupWindow.
Pasa en los cuatro bordes. Se sustituye sólo la captura de pantalla del fixture y el
adaptador de acciones: ninguna ventana/app real se modifica. La misma prueba contra
Task.qml anterior falla con cero clics izquierdos. Las pruebas de geometría (8) y acciones
de ventanas (13) pasan. Shell reiniciado por el gestor de mantenimiento, una instancia ii;
sin errores de configuración de Hyprland. Recortes del panel revisados y borrados.

Suite general: 375 pruebas, 66 opcionales omitidas, sin fallos. La prueba de entrada
opcional se ejecutó además expresamente; qmllint conserva avisos de imports/metadatos
dinámicos, complementados con la carga real del shell.

Esto comprueba el componente que usa la barra; no certifica equivalencia visual completa
con todas las versiones y temas de Plasma. No se modifica el plugin ni hace falta cerrar sesión.

## Port visual desde los originales (2026-11-12)

La comparación posterior del usuario mostró que las medidas corregidas de las tareas no
bastaban: reloj, lanzador, bandeja y Mostrar escritorio seguían siendo versiones reducidas.
Se clonaron plasma-desktop y plasma-workspace con la etiqueta v6.7.5 verificada y se portaron
sus representaciones compactas y métricas. Inventario y modificaciones en panel/README.md.

| Pieza | Implementación vigente |
| :--- | :--- |
| Kickoff | Compacto original; medidas según icono, etiqueta opcional, icono de reserva y arrastre. |
| Reloj | Estados y etiquetas originales, ajuste de fuente y formatos nativos; sin negrita fija. Las 216 líneas de estados se cotejaron iguales tras sustituir el attached. |
| Bandeja | AbstractItem para SNI/applets, flecha y animaciones originales; 22 px y celdas de 30 px por defecto, filas y escala según las fórmulas de Plasma. |
| Mostrar escritorio | Icono simbólico de 32 px e indicador tabbar original; controlador común BWM. |
| Contenedor | fixedMargins por applet y smallSpacing entre applets, con CanFillArea en tareas; sin margen exterior duplicado. |

Probado en el shell real y con fixtures seguros: reloj horizontal de varias alturas,
una línea y vertical; clic de lanzador, Mostrar escritorio y flecha; escala automática de
bandeja; se conservan las comprobaciones de tareas/miniaturas y popup/Escape. Capturas de
los componentes y extremos del panel revisadas y eliminadas. El módulo privado del reloj,
ya instalado, se declara en requisitos y manifiesto; no se instalaron paquetes.

En la referencia, el panel mide 44 px y el fondo es #202326: coinciden con el panel actual.
El logo turquesa de la referencia es distinto del start-here-kde-symbolic blanco instalado;
las aplicaciones, sus estados y el formato regional también difieren. Se conserva la
configuración elegida. No se afirma igualdad de todos los píxeles sin conocer los activos
y la configuración de la sesión de referencia. Se han sustituido las aproximaciones
identificadas por el código visual original; no se cambia la estimación general del port.

Verificación final: 379 pruebas generales, 70 opcionales omitidas, sin fallos; ejecutadas
además las cuatro pruebas de controles/medidas nativas, quince de bandeja y la de tareas en
cuatro bordes. Hyprland verifica config ok, configerrors vacío, requisitos de Breeze correctos
y una instancia ii. qmllint sin errores de sintaxis; conserva avisos de imports virtuales y
metadatos dinámicos, complementados con instanciación real. Avisos anteriores de UPower,
traducción en_US y ToolbarTabBar fuera del alcance de este ajuste.
