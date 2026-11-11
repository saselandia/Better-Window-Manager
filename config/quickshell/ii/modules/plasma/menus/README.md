# Menús contextuales de Plasma en Breeze (F9)

Los mismos menús que KDE Plasma 6.7.5, con el estilo de Plasma activo (PlasmaComponents 3), en vez
de los QMenu originales: un QMenu (Qt Widgets) no puede abrirse desde layer-shell (ver F4). Sólo se
cargan en Breeze (`IllogicalImpulseFamily.qml`, por ruta).

| Menú | Original | Aquí |
| :--- | :--- | :--- |
| Ventana (botón derecho en la barra de título, botón de menú de la decoración, Alt+F3) | kwin `src/useractions.cpp` (`UserActionsMenu::init`, submenús de escritorios y pantallas) | `WindowMenu.qml` |
| Gestor de tareas | plasma-desktop `applets/taskmanager/qml/ContextMenu.qml` | `TaskMenu.qml` |
| Escritorio (botón derecho en el fondo) | plasma-workspace `containmentactions/contextmenu/menu.cpp` | `DesktopMenu.qml` + `DesktopCatcher.qml` |
| Panel (botón derecho en un hueco) | el mismo complemento, rama de paneles | `PanelMenu.qml` |

- `MenuHost.qml`: una capa transparente a pantalla completa en la pantalla donde se abre el menú
  (pulsar fuera o Escape lo cierran). IPC `plasmaWindowMenu open <dirección> <x> <y>` (la usan
  breezebars y `kwin-window.py menu`) y `plasmaMenus inspect|close`.
- `PlasmaMenus.qml`: estado (un menú a la vez) y `run()`, que manda las acciones de ventana a
  `config/hypr/skins/plasma/scripts/kwin-window.py` (F8/F9: un solo sitio).
- `DynamicItems.qml`: entradas generadas (escritorios, pantallas, acciones del .desktop, recientes).
- Recientes del gestor de tareas: `config/hypr/skins/plasma/scripts/task-recents.py` lee
  `~/.local/share/recently-used.xbel` (el backend del applet de Plasma no está instalado).

## Diferencias con Plasma (Hyprland o BWM no lo tienen)

- Ventana: «Mantener encima/debajo» salen desactivados (Hyprland no tiene capas por ventana); no hay
  «Atajo de la ventana», «Extensiones» ni actividades; «Añadir a un escritorio nuevo» desactivado
  (una ventana está en un solo workspace). Los escritorios son los workspaces 1…`bar.workspaces.shown`.
  «Configurar ajustes especiales…» llama a la IPC `plasmaWindowRules` del editor de reglas (F10) y,
  mientras no exista, abre `kcmshell6 kcm_kwinrules`.
- Tareas: sin «Lugares», actividades, «Enrollar» ni «Permitir agrupar»; «Configurar el gestor de
  tareas» no existe (el panel se configura en su modo de edición).
- Escritorio: «Abrir terminal», «Bloquear» y «Salir» (en Plasma desactivados de fábrica) están; no
  hay elementos gráficos de escritorio ni KRunner. «Escritorio y fondo» abre el selector de fondos de
  Breeze; «Configuración de la pantalla», la página de pantallas de los ajustes comunes.
- Panel: «Mostrar alternativas…» es de cada elemento gráfico con alternativas; los de BWM no tienen.

## Traducciones

Catálogo propio `bwm_plasma_menus` (`po/<idioma>.po`, 94 idiomas): sólo las cadenas que se usan,
con su contexto y traducción, sacadas de los `.po` de kwin, plasma-desktop, plasma-workspace y
libplasma 6.7.5 con `po/extract.py`. No se usan los dominios de KDE: un catálogo recortado con su
nombre taparía al completo si estuviera instalado. `plasma-theme.py translations` los compila en
`~/.local/share/locale` (también al entrar en Breeze).

## Licencia

Estructura y textos derivados de kwin, plasma-desktop, plasma-workspace y libplasma 6.7.5
(GPL-2.0-or-later / LGPL-2.1-or-later); cabeceras SPDX conservadas en los archivos derivados.

## Pruebas

`BWM_RUN_QML_TESTS=1 python3 -m unittest tests.test_plasma_menus_ui -v` (qs -p aparte, kitty de prueba
en el workspace 9): estructura de los cuatro menús, dentro de la pantalla, español, y maximizar desde
el menú.
