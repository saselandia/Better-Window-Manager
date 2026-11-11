# OSD de Plasma (F12)

`OsdItem.qml` es `plasma-workspace v6.7.5/shell/qml/OsdItem.qml` (GPL-2.0-or-later,
Martin Klapetek y Kai Uwe Broulik). Cambio BWM: formato porcentual con Qt.locale, sin exigir
el contexto de traducción de plasmashell. `Osd.qml` sustituye OsdWindow por una capa Quickshell
sin entrada, SVG widgets/background, monitor enfocado y temporizador. El servicio común
OnScreenDisplay conserva Audio/Brightness, avisos e IPC osdVolume; sólo cambia la interfaz.
El timeout sigue el ajuste común de BWM. Pantallas: se agrupan cambios de monitors_layout.json
y se ofrece IPC `plasmaOsd displayText <texto> <icono>`; no se modifica la configuración del monitor.

Si el tema global incluye contents/osd/Osd.qml o main.qml se aloja con ThemeHost; los wrappers
OsdWindow/PlasmaCore.Dialog se adaptan dentro de la caché del paquete. Una raíz no visual o un
error de carga conserva el OsdItem nativo. No se ejecuta plasmashell ni se ocupa su nombre D-Bus.

Fuentes: https://invent.kde.org/plasma/plasma-workspace/-/tree/v6.7.5/shell/qml
