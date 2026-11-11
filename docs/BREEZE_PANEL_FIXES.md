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
