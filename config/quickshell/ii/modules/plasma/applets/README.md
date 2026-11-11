# Applets de Plasma sobre Quickshell (F5)

Fuentes de KDE Plasma **v6.7.5**, con cambios señalados BWM. No se instancia PlasmoidItem real:
AppletHost proporciona el contrato de representaciones, configuración, acciones e idioma con
KI18nContext; la ventana/fondo del popup la ofrece ../tray/TrayPopup.qml (KSvg/PC3/Kirigami).
Las vistas comparten los colores y métricas de KDE y se actualizan con el motor de temas de F1.

| Carpeta / vista | Código de origen | Adaptación y licencia |
| --- | --- | --- |
| audio | plasma-pa/applet (main.qml y sus componentes) | QML original, datos org.kde.plasma.private.volume sobre el mismo servidor PipeWire/Pulse. Sin KDEDProxy, MicrophoneIndicator ni migración global. Acciones que cargarían kded van a Audio de BWM. PC3 sustituye QMenu; BwmListItemMenu adapta src/qml/listitemmenu.cpp para puertos/perfiles/rutas. GPL-2.0-only OR GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL; menú LGPL-2.1-only OR LGPL-3.0-only OR LicenseRef-KDE-Accepted-LGPL. |
| network | plasma-nm/applet | QML y modelos originales. Handler funciona con NM existente y su agente de secretos; no se inicia el de kded. Abrir no escanea: hay un botón explícito. El menú de copiar detalles usa PC3. LGPL-2.1-only OR LGPL-3.0-only OR LicenseRef-KDE-Accepted-LGPL. |
| BluetoothApplet | bluedevil/src/applet/qml/{FullRepresentation,DeviceItem}.qml | Port reducido del encabezado, lista y ExpandableListItem; datos/acciones del Bluetooth compartido de Quickshell. Emparejar, conectar/desconectar, batería, olvidar con confirmación y búsqueda explícita limitada a 30 s (se detiene sólo la iniciada aquí). Sin plugins privados de Bluedevil ni OBEX. Misma expresión LGPL que red. |
| media | plasma-workspace/applets/mediacontroller | QML original y Mpris2Model de Plasma; se reemplaza GlobalConfig local (paso de volumen), attached y menú de velocidad. No se inicia otro reproductor ni se cambian las teclas comunes. LGPL-2.0-or-later. |
| calendar | plasma-workspace/applets/digital-clock/CalendarView.qml | Vista original, calendario/MonthView y datos de KDE. Wrapper de hora local y configuración mínima; acción de configurar no disponible hasta F11. GPL-2.0-or-later. |
| notifications | plasma-workspace/applets/notifications/components | ModelInterface, Summary, Body y ActionContainer originales. NotificationCard adapta datos/acciones de services/Notifications; encabezado DND/historial reducido de FullRepresentation. Sin importar Globals ni crear NotificationManager.Server. Inline reply no se anuncia ni ofrece. GPL-2.0-only OR GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL. |
| clipboard | plasma-workspace/klipper/declarative/qml | TextItemDelegate original; base reducida de ClipboardItemDelegate y búsqueda con cliphist de BWM. Copia y borrado por entrada, sin arrancar Klipper. GPL-2.0-or-later. |
| power | powerdevil/applets/{batterymonitor,brightness} | BatteryItem, BrightnessItem e InhibitionHint originales. Wrapper UPower/Brightness común, enums de carga adaptados a UPower. No inicia PowerDevil ni usa su inhibición/perfiles. LGPL-2.0-or-later. |

Repositorios y fuentes correspondientes (etiqueta v6.7.5):
[plasma-workspace](https://invent.kde.org/plasma/plasma-workspace/-/tree/v6.7.5),
[plasma-pa](https://invent.kde.org/plasma/plasma-pa/-/tree/v6.7.5),
[plasma-nm](https://invent.kde.org/plasma/plasma-nm/-/tree/v6.7.5),
[bluedevil](https://invent.kde.org/plasma/bluedevil/-/tree/v6.7.5) y
[powerdevil](https://invent.kde.org/plasma/powerdevil/-/tree/v6.7.5). Licencias completas y referencias aceptadas en licenses/KDE-*.txt;
THIRD_PARTY_NOTICES.md registra los componentes.

## Notificaciones

NotificationPopups.qml aloja los mismos componentes en layer-shell con solid/dialogs/background.
Respeta el monitor preferido y el bloqueo comunes; muestra como máximo tres toasts simultáneos.
El historial, acciones, tiempo de expiración y No molestar siguen en services/Notifications.
Su servidor es el único dueño de org.freedesktop.Notifications en Breeze/default; Retro mantiene
su servidor Omarchy. No se inicia ni el servidor ni el gestor de trabajos de Plasma. Se corrigen
accesos a temporizadores/acciones que ya habían desaparecido del proveedor común.

## Alcance y pendientes

La interfaz de Bluetooth y los encabezados de notificaciones/portapapeles/energía son ports
reducidos: no se presenta toda la funcionalidad de Plasma como soportada. Faltan OBEX y asistente
avanzado de emparejamiento, respuestas en línea, trabajos KIO, DND programado, miniaturas/edición/QR
del portapapeles, plugins de agenda y selección multizona desde ajustes, perfiles e inhibiciones de
PowerDevil. Se conserva el control común de BWM para luz nocturna, inactividad y servicios.
Las acciones destructivas/reales de radios, rutas de audio y brillo no se ejecutan en las pruebas.

Los módulos de datos KDE ya estaban instalados desde F0; ahora plasma-nm/plasma-pa y los QML de
MPRIS/calendario/NotificationManager son requisitos declarados de Breeze. Bluedevil y PowerDevil
no se instalan ni se arrancan. Se conservan avisos de upstream en cada archivo derivado.
