# Bandeja de Plasma sobre Quickshell (F5)

Port de plasma-workspace v6.7.5, applets/systemtray/qml. AbstractItem.qml y PulseAnimation.qml
conservan el QML original; StatusNotifierItem.qml adapta sus iconos, clics, menú y rueda a
Quickshell.Services.SystemTray. SystemTray.qml y TrayPopup.qml adaptan el contenedor, el encabezado
de ExpandedRepresentation y la rejilla de HiddenItemsView a una lista explícita de applets BWM.

Origen: https://invent.kde.org/plasma/plasma-workspace/-/tree/v6.7.5/applets/systemtray
LGPL-2.0-or-later; cabeceras conservadas y cambios marcados BWM. Texto en licenses/KDE-LGPL-2.0-or-later.txt.
El README de ../applets describe los applets y sus licencias distintas.

## Datos y comportamiento

- Un solo SystemTray de Quickshell por proceso; no se crea un segundo watcher de SNI ni se usa
  el motor de bandeja/servidor de avisos de Plasma. Un popup expandido por sesión, anclado al monitor
  y borde de su panel; Escape, pulsar fuera y cerrar lo recogen. El panel autooculto sigue visible
  mientras su bandeja está abierta. Abrir Kickoff cierra la bandeja, y viceversa.
- Auto: los SNI Passive y applets inactivos quedan en la rejilla; Shown/Hidden fuerzan cada caso.
  Se guarda por ID estable en bar.plasma.trayItems; no cambia las preferencias comunes de la
  bandeja de otras skins. «Configurar» ofrece los tres modos para todos los elementos presentes.
- SNI: clic izquierdo (o menú si onlyMenu), central, derecho, rueda horizontal/vertical y atención.
  TrayMenu usa QsMenuOpener y PC3, incluidos submenús, porque QMenu no abre desde layer-shell.
- Los applets se crean sólo al abrir su página. La configuración del usuario en texto sigue
  prevaleciendo; Config.blockWrites protege las pruebas. appletProperties permite inyectar un
  proveedor al embeber/probar una página sin acceder a dispositivos o datos reales.
- Se conservan los IPC plasmaNetwork/plasmaBluetooth/plasmaAudio/plasmaCalendar/plasmaNotifications.
  Sólo existen con el controlador cargado en Breeze. No se usan los antiguos módulos modules/ii/plasma*.

## Verificación y límites

Tests de semántica de visibilidad en tests/test_plasma_tray.py y pruebas opcionales con QtTest:
BWM_RUN_QML_TESTS=1 python3 -m unittest tests.test_plasma_tray -v.
Las acciones de Bluetooth y notificaciones usan objetos simulados; red/audio se cargan con controles
inhabilitados. No se conecta/desconecta ni se cambia el radio real para probarlas.

Las páginas originales de ajustes de cada plasmoide y los plasmoides de terceros no se alojan aquí.
La disposición/configuración es la opción bar.plasma aceptada en F3, no un appletsrc parcial.
Nuevos archivos/Loader: reinicio de mantenimiento con bwm-theme-manager.py set <skin-actual> --restart-shell.


Seguimiento visual 2026-11-12: ExpanderArrow.qml procede de plasma-workspace v6.7.5 sin
redibujar su flecha ni sus animaciones. AppletItem.qml adapta PlasmoidItem.qml a los modelos
BWM usando AbstractItem; sustituye ToolButton en el panel. SystemTray usa las fórmulas de
qml/main.qml: smallMedium (22 px), smallSpacing*iconSpacing (8 px de entrada), celdas de
30 px, filas/columnas según grosor y opción scaleIconsToFit. Claves nativas de apariencia
en bar.plasma.systemTray; visibilidad por ID sigue en trayItems. Sin cambios de servicios.
