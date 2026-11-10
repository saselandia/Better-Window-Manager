# Panel de Plasma sobre Quickshell (F3)

Panel de Breeze, cargado por ruta con PanelLoader únicamente cuando se activa esa skin.
Se necesita bwm-theme-manager.py set <skin-actual> --restart-shell al instalar el módulo nuevo:
reinicio de mantenimiento, sin una segunda instancia del shell.

## Origen y adaptación

Fuentes de KDE Plasma **v6.7.5**, en https://invent.kde.org/plasma/:

- plasma-desktop/desktoppackage/contents/views/Panel.qml: PanelBackground.qml conserva las capas
  SVG traslúcida/sólida, prefijos por borde, opacidad adaptable y márgenes. El anfitrión Panel.qml
  sustituye PanelView/PlasmaShell por layer-shell, con una superficie por pantalla.
- plasma-desktop/containments/panel/{main.qml,LayoutManager.js}: disposición y widgets adaptados a
  PanelContent.qml y la lista ordenada bar.plasma.widgets. No se carga el motor de plasmoides.
- plasma-workspace/shell/{panelview.cpp,panelshadows.cpp}: reserva del grosor (sin sumar el hueco
  flotante), flotación al tocar ventanas y selección de bordes. PanelLogic.js adapta su geometría
  en coordenadas lógicas; PanelBackground.qml compone las piezas shadow-* del SVG en vez del
  protocolo de sombras de KWin.
- plasma-desktop/applets/taskmanager/qml/Task.qml y code/TaskTools.js: port reducido del delegado
  sólo-iconos, estados/prefijos y marca de grupo. TaskPrefixes.js conserva los prefijos.
  TasksModel.qml sustituye TaskManager.TasksModel por toplevels de Quickshell y datos de Hyprland.
  TaskToolTip.qml reutiliza ScreencopyView, como el anterior plasmaTaskMenu.
- plasma-workspace/applets/digital-clock/DigitalClock.qml: representación compacta local,
  adaptada en DigitalClock.qml (Clock original de KDE, PC3, formato de fecha y disposición).
  Configuración y señales sustituyen al attached Plasmoid; el formato horario compartido sigue
  saliendo de Config.options.time.format.

Los archivos derivados conservan cabeceras SPDX y marcan la adaptación BWM.
Licencia **GPL-2.0-or-later**; texto en licenses/KDE-GPL-2.0-or-later.txt.
Fuentes originales sin modificar en el sistema; no se incorpora código de KWin al compositor.

## Configuración

En bar.plasma del perfil de Breeze (opción admitida por F3):

- edge: bottom/top/left/right; vacío migra el antiguo bar.bottom.
- thickness: 24–128 píxeles lógicos; floating, floatingGap.
- visibility: always/autoHide/dodge/windowsGoBelow.
- alignment: start/center/end; length: fracción del borde.
- style: adaptive/translucent/opaque; floating como estilo antiguo sigue siendo compatible.
- widgets: lista ordenada kickoff/pager/tasks/tray/clock/desktop.
- taskOrder: orden de grupos; las ancladas siguen en dock.pinnedApps, propio de cada skin.
- showDate y showSeconds.

Clic derecho en un espacio del panel activa la edición; Configurar abre los controles y permite
añadir/quitar/reordenar los widgets incluidos. Ajustes → Panel ofrece borde, visibilidad, opacidad
del tema, grosor, longitud y alineación. Los antiguos color/opacity/centerTasks quedan como datos
de migración; el fondo ahora lo dibuja el estilo de Plasma, sin una paleta propia superpuesta.

La zona exclusiva reserva el grosor sólo en always. Los demás modos reservan cero. El hueco
flotante se superpone al área útil, como PanelView::updateExclusiveZone; ventanas maximizadas
eliminan ese hueco. Una tira de 2 px permite revelar el panel oculto. Los popups actuales y
Kickoff se anclan al borde/posición nuevos hasta sus ports de F4/F5.

## Alcance y pendientes

- Agrupación, ancladas (menú existente), miniaturas de una o varias ventanas, clic central para
  nueva instancia, rueda y arrastre de grupos para reordenar. Resolución de IDs .desktop sin
  distinguir mayúsculas.
- Bandeja/applets: SysTray y applets BWM existentes hasta F5; Kickoff se porta en F4.
- No se hospedan plasmoides arbitrarios de la KDE Store: F0 comprobó sus dependencias de
  PlasmaShell y KWin. «Widgets incluidos» no es el catálogo de complementos de Plasma.
- Unity LauncherEntry (insignias/progreso), controles multimedia del tooltip y múltiples zonas
  horarias del reloj quedan pendientes; no se muestran datos falsos.
- El flujo completo de arrastre, clics de tareas y menú de edición requiere más validación de
  interacción; las pruebas cubren lógica y carga, sin acciones sobre apps del usuario.

## Verificación

tests/test_plasma_panel.py: cuatro bordes, longitud/alineación, flotación, ocultación,
intersecciones/filtrado de ventanas, orden y área útil con reserved real.

Sesión real: Breeze/default y Sweet de KDE Store, cuatro bordes por estilo, imágenes recortadas
al panel y reserva exacta de 44 px sólo en el borde elegido. AutoHide/Dodge/WindowsGoBelow
reservan cero; el último queda visible. Capturas borradas al finalizar.
