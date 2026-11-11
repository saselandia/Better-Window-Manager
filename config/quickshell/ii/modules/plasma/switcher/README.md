# Cambiador de ventanas de Plasma (F12)

`ThumbnailGrid.qml` porta `kwin v6.7.5/src/tabbox/switchers/thumbnail_grid/contents/ui/main.qml`
(GPL-2.0-or-later; Chris Holland y Nate Graham). Conserva el algoritmo de columnas, tamaños,
miniaturas, iconos, títulos, resaltado SVG, cierre y navegación. Cambios BWM: TabBox/Dialog
se alojan en layer-shell y los datos/acciones vienen del controlador existente `AltTab.qml`.
No se cambia su instantánea MRU, pendingSteps, releasedEarly ni el foco al soltar Alt.

`Switcher.qml` lee `[TabBox] LayoutName` mediante InterfaceTheme (incluye kdedefaults).
Paquetes en las rutas estándar `kwin/tabbox/<id>`: `interface-theme.py` conserva una copia en
caché del paquete con sus recursos y adapta los imports de KWin y PlasmaCore.Dialog. El original
instalado no se modifica. `compat/` expone TabBoxSwitcher, el modelo de ventanas y activate/close,
WindowThumbnail sobre ScreencopyView, y Dialog dentro de la capa de BWM. Los datos JS se
convierten a variantes al cruzar motores QML; las capturas mantienen objetos Toplevel nativos.

El QML de cada paquete usa ThemeHost, nunca el proceso de Hyprland. Si no existe un paquete o
no carga, se usa la rejilla portada. APIs adicionales de KWin (efectos, escritorios 3D y shaders
privados) no se emulan. No se afirma compatibilidad universal con cambiadores externos: se
comprobó el QML original de la rejilla con el adaptador y el port integrado con datos simulados.
La versión de KWin usada sólo incluye thumbnail_grid aquí; no se inventan otros cambiadores.

Fuentes correspondientes: https://invent.kde.org/plasma/kwin/-/tree/v6.7.5/src/tabbox/switchers
