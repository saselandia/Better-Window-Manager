# Third-party notices / Avisos de terceros

BWM reúne componentes con licencias diferentes. Los textos en `licenses/` y los avisos de cada
componente acompañan al código y a las distribuciones; ningún distintivo MIT cubre el conjunto.
Este inventario no sustituye las licencias originales ni autoriza a relicenciar código ajeno.
Los binarios existentes deben corresponder a su código fuente y avisos antes de una release.

| Componente y rutas | Procedencia y licencia | Distribución y cambios |
| :--- | :--- | :--- |
| Shell illogical-impulse, partes de `config/quickshell/ii/` | [end-4/dots-hyprland](https://github.com/end-4/dots-hyprland), GPL-3.0; [texto](licenses/GPL-3.0.txt) y `config/quickshell/ii/COPYING` | BWM adapta el shell, los servicios y la configuración para sus skins. Los cambios y fechas se detallan en el historial Git de cada archivo. El código derivado se distribuye bajo la GPL correspondiente; los subdirectorios vendorizados con licencia propia conservan sus avisos. La revisión exacta de origen aún debe fijarse. |
| Outline de KWin en `config/quickshell/ii/modules/plasma/tiling/Outline.qml` | [KWin v6.7.5](https://invent.kde.org/plasma/kwin/-/tree/v6.7.5), `src/qml/outline/plasma/outline.qml`; Martin Gräßlin (2014), Kai Uwe Broulik (2017); GPL-2.0-only OR GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL (textos KDE en `licenses/`) | BWM sustituye Workspace/outline y la ventana de KWin por geometría IPC y layer-shell de Quickshell; conserva KSvg y bordes del estilo de Plasma. `TileEditor.qml` y los adaptadores Python/Lua de reglas/mosaico son implementaciones propias; referencias de formato KWin `rules.cpp`, `rulesettings.kcfg`, `rulebooksettings*`, `tiles/*` y `workspace.cpp`; el C++ independiente de geometría/magnetismo de breezebars conserva BSD-3-Clause. |
| hyprbars, `src/breezebars/` (plugin `breezebars`, el de Breeze) y su `.so` en `config/hypr/plugins/breezebars.so` | [hyprwm/hyprland-plugins](https://github.com/hyprwm/hyprland-plugins), Copyright (c) 2023 Hypr Development, BSD-3-Clause; [texto íntegro](licenses/hyprland-plugins-BSD-3-Clause.txt), también en `src/breezebars/LICENSE` | BWM añade decoraciones Breeze, detección CSD, snapping y la composición de las decoraciones de KDE que dibuja `bwm-decorator` (la sombra sigue el algoritmo de `shadowitem.cpp` de KWin, reescrito sin copiar código), adapta la API a Hyprland 0.56 y lo registra como `breezebars`. F7 implementa de forma propia la política de negociación CSD/SSD estudiada en KWin v6.7.5 (`src/xdgshellwindow.cpp`, `src/wayland/{xdgdecoration_v1,server_decoration}.cpp`, `src/x11window.cpp`), sin copiar C++ de KWin; integración sobre las fuentes/SDK de Hyprland 0.56.2 (`XDGDecoration`, `ServerDecorationKDE`, `XDGShell`). No se implica patrocinio de Hypr Development. El `.so` antiguo `config/hypr/plugins/hyprbars.so` debe cotejarse con su revisión fuente antes de distribuir binarios. |
| omarchy-hyprland-titlebars, `src/omarchy-titlebars/` y `config/hypr/plugins/omarchy-titlebars.so` | [omacom/omarchy-hyprland-titlebars](https://github.com/omacom/omarchy-hyprland-titlebars) `379ff91` (2026-10-13, el último que compila con Hyprland 0.56): fork de hyprbars (BSD-3-Clause, `src/omarchy-titlebars/LICENSE`) con cambios de Omarchy bajo MIT (`src/omarchy-titlebars/LICENSE.MIT`) | Sin cambios en el código; BWM sólo añade un `Makefile` que compila e instala de forma atómica. Barras de los workspaces flotantes de Retro. |
| Omarchy: `config/hypr/omarchy/`, librerías `config/quickshell/ii/Commons/`, `Ui/` y módulos identificados como Omarchy | [basecamp/omarchy, rama quattro](https://github.com/basecamp/omarchy/tree/quattro), Copyright (c) David Heinemeier Hansson, MIT; [texto íntegro](licenses/omarchy-MIT.txt) | BWM adapta shell, menús, temas, plantillas y pantallas de arranque. Los subdirectorios con avisos propios los conservan. Los fondos, marcas y recursos de terceros contenidos en temas requieren revisión independiente. Los logos de `modules/ii/bar/omarchy/agents/assets/` (Claude, Codex, Copilot, Cursor, NVIDIA y otros proveedores) vienen tal cual de Omarchy y siguen siendo marcas de sus titulares; no implican relación ni patrocinio. |
| Plugins en `config/quickshell/ii/omarchy-plugins/` | Cada plugin conserva su `LICENSE` y manifiesto | Los iconos de `ai-usagebar/omarchy/icons/` tienen [créditos específicos](config/quickshell/ii/omarchy-plugins/ai-usagebar/omarchy/icons/README.md), incluida la licencia de Lobe Icons. Las marcas siguen perteneciendo a sus titulares. |
| Omacalc (instalado por `config/hypr/scripts/install-omacalc.sh`) | [omacom/omacalc, `573d7106`](https://github.com/omacom/omacalc/tree/573d7106f5c6c0225864eb8634ae37ddcb657f63), Copyright (c) 2026 David Heinemeier Hansson, [MIT](licenses/omacalc-MIT.txt); fuente iA Writer Mono S incluida: Information Architects Inc. / IBM Plex (IBM Corp.), [OFL-1.1](licenses/omacalc-iA-Writer-OFL.txt) | Se conserva la interfaz, fuentes, aritmética e icono originales. `config/hypr/omacalc/theme-path.patch` añade una ruta opcional de paleta nativa (`OMACALC_THEME_FILE`) y su vigilancia; BWM genera sus colores con los motores existentes de cada skin. Fuentes correspondientes en `~/.local/share/bwm/omacalc/source`, parche y avisos junto al binario; el instalador conserva MIT y OFL. Detalle y reproducción en `config/hypr/omacalc/README.md`. |
| Cursores `assets/cursors/Bibata-Modern-{Classic,Ice}` | [Bibata Cursor](https://github.com/ful1e5/Bibata_Cursor/tree/v2.0.6), GPL-3.0; `COPYING` junto a cada tema | Los `index.theme` indican v2.0.6; se incluyen XCursors y versiones Hyprcursor. Véase `SOURCE.md` en cada carpeta. La correspondencia de cada binario y la generación de Hyprcursor siguen pendientes de verificar. |
| Pywalfox, `config/firefox/extensions/pywalfox@frewacom.org.xpi` | [Frewacom/pywalfox](https://github.com/Frewacom/pywalfox/tree/v2.1.1), MPL-2.0; [texto](licenses/pywalfox-MPL-2.0.txt) | El manifiesto del XPI indica versión 2.1.1 (SHA-256 `b7a7a86d1d49a8309758ce1d38492975abe07a61e3788e2d913c70a4d07758b4`). El código publicado de esa versión está en la etiqueta enlazada; no se ha comprobado que el binario sea reproducible desde ella ni si contiene dependencias adicionales. |
| Fuentes `assets/fonts/` | Google Sans Flex, Readex Pro, Space Grotesk y JetBrains Mono Nerd Font: OFL-1.1. Material Symbols: fuente de la familia [Material Design Icons](https://github.com/google/material-design-icons), Apache-2.0 | Avisos por familia y licencias de Nerd Fonts 3.4.0 y 3.5.1 en `assets/fonts/licenses/`. Google Sans Flex: Copyright 2015 Google LLC según el TTF distribuido. JetBrains Mono: Copyright 2020 The JetBrains Mono Project Authors. La procedencia exacta de cada glifo añadido por Nerd Fonts y de la compilación de Material Symbols aún requiere cotejo. |
| Iconos Fluent en `config/quickshell/ii/assets/icons/fluent/` | Joshua Oghenekaro Okwe, Windows 11 en Figma, CC BY 4.0 | [Aviso original](config/quickshell/ii/assets/icons/fluent/README.md) indica fuente y modificaciones. Verificar las condiciones de cada recurso descargado antes de distribuirlo. |
| Formas de `config/quickshell/ii/modules/common/widgets/shapes/` | Apache-2.0 | Texto en ese directorio; revisar procedencia y cualquier aviso `NOTICE` de la versión original. |

Adaptaciones de interfaz (2026-10-29): `modules/ii/omarchyMenu/omarchy/{Menu,AppGrid}.qml`
conservan la procedencia y licencia MIT del menú y la cuadrícula de Omarchy quattro ya
vendorizados. BWM sustituye la entrada de texto limitada por editores Qt, ajusta la cuadrícula
y añade navegación de teclado. La apertura de Apps pasa al shell nativo y se retiran los
pies de ruta/atajos del menú y la cuadrícula. La extensión de BWM en `omarchyMenu/omarchy/settings/`
añade configuración dentro del menú mediante sus componentes originales `qs.Ui`.
Desde 2026-11-10, Retro usa filas nativas y `hypr/skins/retro/scripts/settings.py`
(código de BWM) sobre los gestores existentes; `SettingsPage.qml` sólo aloja el
esquema de monitores. No carga las páginas de illogical-impulse ni cambia su paleta
para mostrarlas. `modules/settings/retro/SettingsStyle.qml` se conserva para los
consumidores anteriores y las pruebas de sus controles, con la GPL de ese componente.
La versión vendorizada previa y estas modificaciones se pueden consultar en el historial Git
de cada archivo; no se ha actualizado el código de terceros a otra revisión upstream.

Guía de atajos de Retro (2026-10-29): `omarchyMenu/Keybindings.qml` reutiliza el selector
del menú de Omarchy ya vendorizado, siguiendo el flujo de
[`bin/omarchy-menu-keybindings`](https://github.com/basecamp/omarchy/blob/quattro/bin/omarchy-menu-keybindings)
(Quattro, MIT). El selector recibe una señal de selección dentro del proceso. El adaptador y
`hypr/skins/retro/scripts/keybindings.py` son código de BWM para presentar los atajos activos
del compositor; el script upstream no se ha incorporado ni se han sustituido sus fuentes
vendorizadas. La licencia y el aviso del menú original se conservan.

Fuentes del shell de Retro (2026-11-09): `Commons/Style.qml`, derivado de Omarchy
quattro `d9cc361c` (MIT), resuelve `monospace` con la fuente del perfil de BWM como
alternativa anterior a las fuentes genéricas de la distribución, conservando las preferencias
explícitas de Fontconfig. Detalle de las adaptaciones en `Commons/README.md`.

Selector de fondos de Retro (2026-11-09): el carrusel vendorizado de Omarchy en
`modules/ii/bar/omarchy/image-picker/` conserva su interfaz. El nuevo
`hypr/scripts/omarchy-shims/omarchy-menu-images` y el protocolo añadido a `OmarchyPlugins.qml`
proceden de `bin/omarchy-menu-images` y `shell/shell.qml` de Omarchy quattro
[`cbd0029f`](https://github.com/basecamp/omarchy/tree/cbd0029fddcfcae0b73cf1c01a1c6031eae98f99)
(MIT, Copyright (c) David Heinemeier Hansson). BWM adapta los conversores de miniaturas a
ImageMagick/FFmpeg, el IPC al shell existente y la aplicación a sus perfiles/motores; añade
`~/Pictures/Wallpapers` a los fondos del tema y los extras personales de Omarchy. Detalle en
`modules/ii/bar/omarchy/image-picker/README.md`.

Animaciones y fondo (2026-11-08): `hypr/skins/retro/hypr/animations.lua` copia las curvas,
animaciones y reglas de capa de Omarchy quattro `598e4eb` (`default/hypr/looknfeel.lua`,
`qconsole.lua`, `apps/omarchy-shell.lua`, `apps/screenshot-selection.lua`; MIT) y
`modules/ii/omarchyBackground/OmarchyBackground.qml` su `shell/plugins/background/Background.qml`
(MIT), con los dobles clics del escritorio cambiados a los selectores de BWM.
`hypr/skins/default/hypr/animations.lua` copia las de end-4/dots-hyprland `2f2a376`
(`hypr/hyprland/general.lua` y `rules.lua`, GPL-3.0, como el resto del shell derivado).

Bloqueo de Retro (2026-11-08): `modules/ii/omarchyLock/LockView.qml` es `shell/plugins/lock/LockView.qml` de
Omarchy quattro `598e4eb` (MIT) sin cambios. El bloqueo artesanal de Breeze fue sustituido
por el port de KScreenLocker descrito en F12 al final de este archivo.

Modos de workspace de Retro (2026-11-08): `hypr/skins/retro/hypr/workspace-modes.lua` y los shims
`omarchy-hyprland-workspace-layout-{toggle,default,current}` portan `default/hypr/workspace-modes.lua`,
`workspace-layouts.lua` y `bin/omarchy-hyprland-workspace-layout-*` de basecamp/omarchy `quattro`
`60bf28ee` (MIT); cambios de BWM anotados en sus cabeceras.

Salvapantallas nativo de Retro (2026-11-08): `hypr/skins/retro/scripts/install-screensaver.sh`
compila [omacom/omarchy-screensaver](https://github.com/omacom/omarchy-screensaver) `b3026b63`
(MIT, Copyright (c) 2026 Tobias Lütke) con cargo en `~/.local/share/bwm/omarchy-screensaver`; sus
dependencias (ttfx, Smithay Client Toolkit, fontdue…) las descarga cargo con sus licencias. No se
incluye ni el código ni el binario en el repositorio. `hypr/skins/retro/screensaver.txt` es el logo de BWM.

Apagado común (2026-11-08): `hypr/scripts/bwm-power` sigue `bin/omarchy-system` y
`bin/omarchy-hyprland-window-close-all` de Omarchy quattro `598e4eb` (MIT), reescrito para BWM.

Barra de Retro (2026-11-09): `config/quickshell/ii/omarchyShell/` es una copia de `shell/` de Omarchy
quattro [`18ac93c`](https://github.com/basecamp/omarchy/tree/18ac93c) (MIT, Copyright (c) David
Heinemeier Hansson): la barra (`plugins/bar`), sus paneles (`plugins/panels`), el de agentes
(`plugins/agents`), los servicios de multimedia y sesión remota (`plugins/services`), el registro de
plugins y sus API (`services/`) y el anfitrión `shell/shell.qml` como `OmarchyShell.qml`. Cambios de BWM,
marcados «BWM» en el código: el anfitrión es un `Scope` dentro del shell de BWM, sin biblioteca de apps,
teclas de brillo, introducciones de fondo, atajos globales, socket IPC ni el IPC del selector de imágenes
(BWM los tiene en otra parte); el menú y las capas que aloja BWM se piden a `OmarchyPlugins`; los
servicios de inactividad, luz nocturna y no molestar son adaptadores sobre los de BWM; el registro lee
además los plugins preinstalados de BWM; el widget de workspaces usa la numeración global de BWM; y el
botón del menú se declara sólo como widget de barra. También de `18ac93c`, sin cambios: `omarchy-bar`,
`omarchy-shell-config`, `omarchy-plugin-*`, `omarchy-restart-hyprctl`, `omarchy-git-url-check`,
`omarchy-hyprland-monitor-{layout,resolution,rotate,scaling,laptop}`, `omarchy-monitor-state` y
`omarchy-hyprland-toggle-enabled`, `omarchy-toggle{,-enabled,-bar,-animations}`, `omarchy-hyprland-toggle`,
`omarchy-hyprland-animations-off`, `omarchy-transcode-ascii` y `omarchy-file-select` (quattro `ec62d379`) en
`hypr/scripts/omarchy-shims`, adaptados `omarchy-language` y `omarchy-branding-{about,screensaver}`; reglas de ventana `default/hypr/apps/*.lua` (quattro `c18b00c5`, sin cambios) en `Commons/omarchy/default/hypr/apps/`; propios de BWM con su interfaz:
`omarchy-hyprland-monitor-persist` (guarda con `monitor-manager.py`) y `omarchy-sudo-passwordless`
(nunca activo). `Commons/omarchy/default/hypr/toggles/bar-glassy.lua` procede de
`default/hypr/toggles/bar-glassy.lua` sin la llamada a su modo vidrio.
Extensiones de Nautilus para Retro (2026-11-19): `config/hypr/skins/retro/nautilus-python/extensions/{localsend,transcode}.py`
proceden de `default/nautilus-python/extensions/` de Omarchy quattro (`05344eb6` y `ec4a3d02`, MIT),
adaptadas mínimamente para buscar también en `~/.local/bin` y `~/.config/hypr/scripts/omarchy-shims`
cuando Nautilus se activa por D-Bus sin `~/.local/bin` en `PATH`.

Fuente de iconos de Omarchy (2026-11-09): `assets/fonts/omarchy.ttf`, de
`default/fonts/omarchy/omarchy.ttf` de Omarchy quattro `18ac93c` (repositorio MIT), con su descripción en
`assets/fonts/licenses/omarchy-font-README.md`. Además del logo de Omarchy contiene marcas de terceros
(Claude, Codex, Cursor, Tailscale…) redibujadas desde sus logos: son marcas de sus dueños y su uso no
queda cubierto por la licencia MIT; pendiente de revisar antes de una release, como el resto de
recursos de la lista siguiente.

## Recursos pendientes de procedencia

No se declara que los siguientes recursos estén cubiertos por MIT ni por una licencia común:

* `assets/wallpapers/{default,cyberpunk,gentoo-penguins}.jpg`: no se ha localizado autor,
  fuente ni autorización de redistribución.
* `assets/skin-previews/kde-plasma-6.png` y `end4-illogical-impulse.png`: su origen figura en
  `assets/skin-previews/README.md`, pero la licencia específica de las capturas debe verificarse.
  Las imágenes de temas de Omarchy también pueden tener autores o condiciones distintas del código.
* Los binarios `config/hypr/plugins/hypr-csd.so`, `src/csd-minimize/hypr-csd.so` y
  `config/hypr/plugins/hyprbars.so`: identificar versión, fuentes exactas y licencias de cualquier
  código incorporado, o dejar de distribuirlos como binarios.
* Determinar la licencia y titulares del código original de BWM no derivado, y fijar revisiones de
  terceros. Los términos de cada licencia de terceros siguen aplicándose independientemente de esa decisión.

Hasta completar estas verificaciones, no debe presentarse una release como íntegramente auditada.

Colores de Default (2026-10-29): los scripts `scheme_for_image.py` y
`generate_colors_material.py`, y la plantilla Matugen `colors.json`, se cotejaron con
[end-4/dots-hyprland, 2f2a376fdb2a](https://github.com/end-4/dots-hyprland/tree/2f2a376fdb2ad738bf55f693dd0b474b64bb0ab8)
sin diferencias (GPL-3.0 del proyecto). BWM adapta `switchwall.sh` con una entrada
`--colors-only` y un runner de dependencias aisladas; `applycolor.sh` escribe el tema
de terminal original en la ruta usada por Kitty en BWM. Las fuentes correspondientes
están en `config/quickshell/ii/scripts/colors/` y su historial Git. Las bibliotecas de
Python se descargan al instalar el entorno, con sus propios avisos/licencias; no se
incorporan sus binarios al repositorio.

Aplicación rápida de colores (2026-10-29): BWM añade el coordinador
`config/hypr/skins/default/scripts/matugen-fast.py` y adapta las llamadas de
`switchwall.sh` para publicar los mismos colores antes de ejecutar los hooks de apps.
El clasificador y el generador de colores de end-4 conservan el código cotejado con
`2f2a376fdb2a`; no se modifica su selección de colores. Los cambios de nombres visibles
de skins tampoco alteran los avisos de procedencia de KDE Plasma/end-4.

Apps Qt de Default (2026-11-03): `config/hypr/skins/default/scripts/kde-material-you-colors-wrapper.sh`
y `config/kde-material-you-colors/config.conf` proceden de end-4/dots-hyprland `2f2a376fdb2a`
(GPL-3.0); el primero se adapta al entorno de colores de BWM. `kde-material-you-colors`
(GPL-3.0, de luisbocanegra) y `dbus-python` (MIT y GPL-2.0-or-later o AFL-2.1) se descargan con pip al instalar, con sus avisos;
no se incluyen en el repositorio. `kde-shims/plasma-apply-colorscheme` es propio de BWM.

Puente de configuración de Breeze (F2, 2026-11-11): `kde-config-bridge.py` y `hypr/kwin.lua`
son código propio; los nombres de claves y señales se verificaron con los `.kcfg` de KDE Plasma
v6.7.5 y KConfig v6.29.0. No se copió implementación KDE. Rutas y procedencia en
`config/hypr/skins/plasma/scripts/README.md` y decisiones en `docs/BREEZE_ARCH.md` §9.

Panel de Breeze (F3, 2026-11-11): componentes derivados de KDE Plasma **v6.7.5** en
config/quickshell/ii/modules/plasma/panel, GPL-2.0-or-later. Origen:
[plasma-desktop](https://invent.kde.org/plasma/plasma-desktop/-/tree/v6.7.5)
(desktoppackage/contents/views/Panel.qml, containments/panel, applets/taskmanager/qml/Task.qml y
code/TaskTools.js y qml/code/LayoutMetrics.js; manejadores y medidas cotejados de nuevo
el 2026-11-12) y
[plasma-workspace](https://invent.kde.org/plasma/plasma-workspace/-/tree/v6.7.5)
(applets/digital-clock/DigitalClock.qml, shell/panelview.cpp y panelshadows.cpp).
Se conservan las cabeceras SPDX de Marco Martin, Eike Hein, Nate Graham, Heena Mahour,
Sebastian Kügler, Martin Klapetek y David Edmundson en los archivos derivados. BWM adapta
anfitrión, datos y acciones a Quickshell/Hyprland, reduce las representaciones compactas y
sustituye la configuración attached de Plasma. Fuente correspondiente incluida y adaptación en
el README de la carpeta; [texto de licencia](licenses/KDE-GPL-2.0-or-later.txt).

Kickoff de Breeze (F4, 2026-11-11): config/quickshell/ii/modules/plasma/kickoff es el Kickoff de
[plasma-desktop](https://invent.kde.org/plasma/plasma-desktop/-/tree/v6.7.5/applets/kickoff)
**v6.7.5** (GPL-2.0-or-later) y sus traducciones originales (`po/`, del paquete publicado
plasma-desktop-6.7.5.tar.xz). Se conservan las cabeceras SPDX de Martin Gräßlin, Gregor Taetzner,
Marco Martin, David Edmundson, Eike Hein, Mikel Johnson, Noah Davis, ivan tkachenko y demás
autores. BWM sustituye el anfitrión de Plasma (PlasmoidItem, attached Plasmoid, Dialog e i18n),
los menús QMenu y las acciones de sesión, sin cambiar los modelos de Kicker. `Plasmoid.qml`,
`KickoffI18n.qml` y `KickoffWindow.qml` son propios de BWM (GPL-2.0-or-later). Adaptación en el
README de la carpeta; [texto de licencia](licenses/KDE-GPL-2.0-or-later.txt).

Preferencias del sistema de Breeze (F11, 2026-11-11): `config/quickshell/ii/modules/plasma/settings`
porta la barra lateral de [systemsettings](https://invent.kde.org/plasma/systemsettings/-/tree/v6.7.5/app/qml)
**v6.7.5** (`Main.qml`, `SideBarItem.qml`, `CategoriesPage.qml`, `SubCategoryPage.qml`,
`CategoryItem.qml`, `HamburgerMenuButton.qml`; LGPL-2.0-only, © Marco Martin, ivan tkachenko,
Jan Blackquill) con sus cabeceras SPDX; los cambios llevan `// BWM:` (modelos de C++ sustituidos por
`SettingsState.qml`). Las categorías y su orden siguen `categories/settings-*.desktop`. Las cadenas
usan el catálogo instalado `systemsettings`. `ModuleView.qml` reescribe en QML la parte de
`app/ModuleView.cpp` (botones y aviso de cambios sin aplicar); el resto de la carpeta, las páginas y
`src/bwm-kcmhost` (módulo QML que carga los KCM con KCMUtils) son propios de BWM
(GPL-2.0-or-later). Los KCM son los instalados de Plasma, no se copian.
[Texto de licencia](licenses/KDE-LGPL-2.0-only.txt).

Menús contextuales de Breeze (F9, 2026-11-11): `config/quickshell/ii/modules/plasma/menus` porta la
estructura y los textos de `src/useractions.cpp` de [KWin](https://invent.kde.org/plasma/kwin/-/tree/v6.7.5),
`applets/taskmanager/qml/ContextMenu.qml` de [plasma-desktop](https://invent.kde.org/plasma/plasma-desktop/-/tree/v6.7.5)
y `containmentactions/contextmenu/menu.cpp` de [plasma-workspace](https://invent.kde.org/plasma/plasma-workspace/-/tree/v6.7.5),
todos **v6.7.5** (GPL-2.0-or-later; Matthias Ettrich, Lubos Lunak, Eike Hein, Kai Uwe Broulik, Chani
Armitage y demás autores, cabeceras conservadas). El catálogo `po/<idioma>.po` (dominio propio
`bwm_plasma_menus`) recoge las traducciones originales de esas cadenas de kwin, plasma-desktop,
plasma-workspace y libplasma 6.7.5 (GPL-2.0-or-later / LGPL-2.1-or-later), extraídas con `po/extract.py`.
Anfitrión, ayudantes y acciones (`MenuHost.qml`, `PlasmaMenus.qml`, `DynamicItems.qml`,
`DesktopCatcher.qml`, `kwin-window.py`, `task-recents.py`) son propios de BWM (GPL-2.0-or-later).
Detalle en el README de la carpeta; [texto de licencia](licenses/KDE-GPL-2.0-or-later.txt).

Auxiliar de decoraciones de Breeze (F6a, 2026-11-11): `src/bwm-decorator/palette.{h,cpp}` es
`src/decorations/decorationpalette.{h,cpp}` de [KWin](https://invent.kde.org/plasma/kwin/-/tree/v6.7.5)
**v6.7.5** (GPL-2.0-or-later; Martin Gräßlin, Hugo Pereira Da Costa, Mika Allan Rauhala, Carson
Black), sin cambios de lógica. La lectura de ajustes y la carga de plugins de `decorator.cpp` siguen
`settings.cpp` y `decorationbridge.cpp` de la misma versión (Martin Gräßlin). El resto es propio de
BWM (GPL-2.0-or-later). Enlaza con KDecoration3 (LGPL) y carga en tiempo de ejecución los plugins de
decoración instalados (Breeze, Aurorae y los del usuario), con sus licencias. Detalle en
`src/bwm-decorator/README.md`; [texto de licencia](licenses/KDE-GPL-2.0-or-later.txt).

### KDE Plasma: bandeja y applets F5 (2026-11-11)

Fuentes v6.7.5 de invent.kde.org/plasma: plasma-workspace (applets/systemtray, mediacontroller,
digital-clock, notifications/components y klipper/declarative/qml), plasma-pa (applet y
src/qml/listitemmenu.cpp), plasma-nm (applet), bluedevil (src/applet/qml) y powerdevil
(applets/batterymonitor, brightness). Destinos: config/quickshell/ii/modules/plasma/{tray,applets}.
Los README de esas carpetas identifican cada archivo/grupo, procedencia y cambios BWM; sus
cabeceras SPDX conservan autores y expresiones completas de licencia. El host se adapta a
Quickshell, modelos KDE compatibles y servicios comunes BWM, con ports reducidos explícitos.
No se copian binarios ni se incorporan los demonios de Plasma.

Licencias: systemtray/mediacontroller/PowerDevil LGPL-2.0-or-later; calendario/portapapeles
GPL-2.0-or-later; plasma-pa y componentes de avisos GPL-2.0-only OR GPL-3.0-only OR
LicenseRef-KDE-Accepted-GPL; plasma-nm/bluedevil y el menú de dispositivos de audio LGPL-2.1-only
OR LGPL-3.0-only OR LicenseRef-KDE-Accepted-LGPL. Textos originales y referencias aceptadas
copiados en licenses/KDE-*.txt. Cada cabecera de archivo prevalece sobre este resumen.
La fuente correspondiente está incluida en QML adaptado y disponible en los repositorios citados,
etiqueta v6.7.5; las bibliotecas enlazadas las proporciona la distribución.


### Interfaces de Plasma (F12)

- `modules/plasma/switcher/ThumbnailGrid.qml`: port de KWin v6.7.5
  `src/tabbox/switchers/thumbnail_grid/contents/ui/main.qml`, Chris Holland (2020) y
  Nate Graham (2023), GPL-2.0-or-later. BWM sustituye la ventana/modelo de KWin por
  layer-shell, su controlador MRU y ScreencopyView; conserva disposición y controles.
- `modules/plasma/osd/OsdItem.qml`: plasma-workspace v6.7.5 `shell/qml/OsdItem.qml`,
  Martin Klapetek (2014) y Kai Uwe Broulik (2019), GPL-2.0-or-later. Formato porcentual
  adaptado a Qt.locale; el anfitrión BWM sustituye OsdWindow, sin copiar el C++ de plasmashell.
- `modules/plasma/lock/Greeter.qml`: KScreenLocker v6.7.5
  `greeter/fallbacktheme/Greeter.qml`, Martin Gräßlin (2011) y Nate Graham (2023),
  GPL-2.0-or-later. BWM conecta controles/mensajes a LockContext mediante un adaptador,
  retira cambio de usuario y terminación del proceso. Clock, avatar, SessionManagementScreen
  y ActionButton son los componentes Breeze instalados, con sus avisos LGPL-2.0-or-later.
- Adaptadores, resolución de paquetes, wrappers y ThemeHost de BWM: GPL-2.0-or-later.
  Los temas de terceros permanecen fuera del repo: sólo se adaptan copias de caché local,
  conservando las cabeceras originales; no se redistribuyen en este cambio.

Fuentes correspondientes: https://invent.kde.org/plasma/kwin/-/tree/v6.7.5/src/tabbox/switchers,
https://invent.kde.org/plasma/plasma-workspace/-/tree/v6.7.5/shell/qml y
https://invent.kde.org/plasma/kscreenlocker/-/tree/v6.7.5/greeter/fallbacktheme.
Los README de `modules/plasma/{switcher,osd,lock,runtime}` detallan versiones, adaptaciones y
límites. El QML portado y la fuente de los adaptadores están incluidos; KRunner, Milou y el
agente polkit de KDE se usan desde los paquetes de la distribución, sin incorporar sus binarios.

### Limpieza F13 y recursos de prueba

Se retiran los 152 SVG Breeze locales y los módulos artesanales sustituidos; los iconos actuales
proceden del paquete de la distribución o del tema del usuario y no se incorporan aquí.
DesktopState y la reparación D-Bus son implementación propia de BWM (GPL-2.0-or-later);
la política de registro en cola se estudió en frameworks/kded v6.29.0 src/kded.cpp, sin copiarlo.

Sweet/variantes, candy-icons, Aurorae y Sweet-cursors descargados para F13 permanecen fuera del
repositorio, con sus avisos originales. No se redistribuyen ni se añaden como requisitos de BWM.
Los metadatos del tema global Sweet declaran GPL 3+; no se extiende esa declaración a todos los
recursos de sus dependencias. Las fuentes/copias portadas de F3–F12 y sus textos de licencia
siguen identificadas arriba y en cada README. La lista de auditoría de release de este archivo
continúa abierta para los recursos y binarios ajenos a este cierre; F13 no la declara resuelta.


Selector y ajustes posteriores a F13: modules/plasma/skinPicker recupera el diseño propio
anterior de BWM desde cab72f8 y adapta paleta/geometría, sin código KDE nuevo. La corrección
de bordes del panel sigue la política de plasma-workspace 6.7.5 PanelView::updateEnabledBorders;
se mantienen cabeceras y origen del port. CsdMove.hpp y la recepción XCB de _NET_WM_MOVERESIZE
son implementación propia sobre EWMH, sin copiar C++ de KWin/Hyprland ni añadir Qt al plugin.
Noto Sans y Hack proceden de los paquetes del sistema, no se añaden sus binarios al repo.


Panel Breeze, ampliación del port visual (2026-11-12): fuentes de **v6.7.5**, etiquetas
verificadas en clones de [plasma-desktop](https://invent.kde.org/plasma/plasma-desktop/-/tree/v6.7.5)
y [plasma-workspace](https://invent.kde.org/plasma/plasma-workspace/-/tree/v6.7.5).
KickoffButton.qml extrae kickoff/main.qml y ShowDesktopButton.qml deriva de showdesktop/main.qml
(GPL-2.0-or-later). DigitalClock.qml conserva ahora la representación compacta completa
(GPL-2.0-or-later). Se conservan sus cabeceras SPDX y autores. PanelContent adapta los márgenes
de containments/panel/main.qml; las señales de expansión/acciones y la configuración las aporta BWM.
ExpanderArrow.qml y AppletItem.qml proceden de systemtray/qml/{ExpanderArrow,PlasmoidItem}.qml
(LGPL-2.0-or-later); la cuadrícula sigue systemtray/qml/main.qml. Cabeceras y modificaciones
marcadas BWM en los archivos; explicaciones en los README de panel y tray. Textos de licencia
ya incluidos en licenses. No se copia el logotipo de la captura de referencia.


### KCM nativo experimental de BWM (Breeze II R2, 2026-11-12)

`src/bwm-systemsettings` es código propio BWM bajo GPL-2.0-or-later, indicado en sus fuentes;
[texto de licencia](licenses/KDE-GPL-2.0-or-later.txt). Utiliza las APIs públicas de Qt Widgets
6.11.2 y KF6 KCMUtils/CoreAddons/I18n 6.29.0 instaladas por la distribución. No incluye fuentes
copiadas de KDE ni distribuye esas bibliotecas. Conserva los avisos de sus paquetes originales.
Factory y metadata siguen el contrato documentado en las cabeceras KCMUtils instaladas.
Alcance, compilación, pruebas aisladas y límites en `src/bwm-systemsettings/README.md`.

R3 añade `ManagerModule`, el adaptador `native-settings.py`, el contrato de capacidades y
`bwm-kcm-catalog`: código propio GPL-2.0-or-later. Descubrimiento mediante KPluginMetaData,
KPluginFactory y KDecoration3::DecorationThemeProvider; no se copian los formularios de terceros.
La prueba `test-decoration-option` carga el KCM Breeze instalado y reutiliza el POC de render
ya incluido en `src/bwm-decorator/poc-fase0.cpp`; no distribuye binarios KDE adicionales.
El perfil local utiliza las restricciones KAuthorized documentadas en KF6 Config 6.29.

### Anfitrión experimental libplasma R4 (2026-11-12)

El protocolo bwm-plasma-desktop-control-v1.xml, su cola/barrera por wl_client, NativeDesktopControl
y las pruebas de retirada/reconexión son propios GPL-2.0-or-later. Las interfaces C y Qt se
generan desde ese XML propio con wayland-scanner/qtwaylandscanner instalados. No sustituyen
el protocolo KDE ni lo presentan como API KDE; comparten su conexión sólo para integración
BWM. Procedencia/hashes y límites en BREEZE_R4_DESKTOP_CONTROL_RESULTS.json.

`src/bwm-plasma-desktops/{desktops,workspaces,plugin,test-*}` y la nueva regresión del
anfitrión son propios GPL-2.0-or-later (texto completo en licenses/KDE-GPL-2.0-or-later.txt).
El protocolo KDE org-kde-plasma-virtual-desktop.xml, de plasma-wayland-protocols 1.23.0,
atribuye copyright 2018 Marco Martin y LGPL-2.1-or-later; wayland-scanner genera interfaces
sin modificar el XML instalado y conserva ese aviso. Su texto de licencia se conserva en
licenses/plasma-wayland-protocols-LGPL-2.1-or-later.txt, copiado sin cambios del tarball.
El fixture usa además xdg-shell.xml de wayland-protocols 1.49, licencia MIT y avisos
conservados en licenses/wayland-protocols-xdg-shell-MIT.txt. Los generados quedan en build,
no se venden como implementación original BWM del protocolo KDE. La extensión utiliza las
APIs/headers Hyprland 0.56.2 instaladas y su guarda de hash, sin copiar el compositor.
La lectura JSON del frontend utiliza nlohmann_json 3.12.0 instalado (MIT), con su licencia
conservada en licenses/nlohmann-json-MIT.txt (del tarball original). Se revisaron KWin plasmavirtualdesktop y plasma-workspace 6.7.5
para contrato/vida de recursos y consumidores, sin copiar su implementación. Hashes/versiones
y límites en BREEZE_R4_NATIVE_DESKTOPS_RESULTS.json; núcleo/fixture no certifican sesión real.

native_guard.py y test_r4_native_guard.py y las modificaciones de transacción/retirada
son propios GPL-2.0-or-later, usando stdlib Python (fcntl/flock Linux) y Qt instalados.
Se revisan también VirtualDesktopInfo y TaskFilterProxyModel de plasma-workspace 6.7.5;
no se copia ni modifica su backend privado. Procedencia y hashes adicionales en
BREEZE_R4_NATIVE_TRANSACTIONS_RESULTS.json.

tasksource.*, taskbridge.*, test-tasks.cpp y native-tasks.py son propios GPL-2.0-or-later.
Enlazan LibTaskManager 6.7.5 y KF6 Service instalados, usando sus headers públicos y APIs de
modelos Qt; no redistribuyen ni modifican libtaskmanager o el QML original. Se consultan
tasksmodel/windowtasksmodel/concatenatetasksproxymodel/abstracttasksmodel y VirtualDesktopInfo
de plasma-workspace 6.7.5. TaskManager::windowUrlFromMetadata/appDataFromUrl resuelven apps e
iconos con la lógica KDE existente. Hashes/procedencia en BREEZE_R4_TASK_SOURCE_RESULTS.json.

desktopbridge.*, windowsystemplugin.* y test-desktop.cpp son propios GPL-2.0-or-later.
Usan headers privados instalados de KWindowSystem 6.29.0 (ABI V5, versión EXACT en CMake)
y su contrato de plugins estáticos, sin copiar headers ni implementación. El plugin es parte
del ejecutable auxiliar: delega al backend KDE instalado y no se instala globalmente. Se
consultaron los tarballs plasma-desktop 6.7.5 y kwindowsystem 6.29.0 de Portage para contrastar
el controlador original y la carga de plugins. La prueba carga el módulo original ShowDesktop
instalado sin redistribuirlo ni modificar su QML/C++; el hyprctl sustituto es fixture propio
sin acceso al compositor. Procedencia/hashes en BREEZE_R4_DESKTOP_ADAPTER_RESULTS.json.

La ampliación de inventario de backends en Catalog/PanelSession/PanelRuntime es propia
GPL-2.0-or-later y consulta KPluginMetaData y las instancias Plasma existentes. No copia
implementaciones de servicios ni añade dependencias; los metadatos sintéticos son fixtures BWM.

check-local.py es propio GPL-2.0-or-later y usa los fixtures BWM de configuración ya incluidos,
QtTest y las herramientas KDE instaladas. No añade paquetes de terceros ni dependencias.
El nuevo ensayo local no descarga ni redistribuye widgets externos.

`src/bwm-plasma-host` es código propio BWM GPL-2.0-or-later que utiliza las APIs instaladas
libplasma/PlasmaQuick 6.7.5, KF6 Config/KPackage y Qt. Se estudió CustomCorona y los contratos
de la distribución upstream fijada en BREEZE_R4_RESULTS.md; no se incluyen esos ejemplos ni
código de AndromedaLauncher. Las pruebas leen fuentes elegidas explícitamente y las instalan
en un prefijo temporal. AndromedaLauncher conserva sus avisos GPL y autoría originales en
la copia de prueba; no se redistribuye en este repositorio. Las APIs privadas requieren la
revisión de actualización descrita en el README del auxiliar.

La continuación R4 añade un paquete Plasma/Shell mínimo propio (muebles sobre AppletPopup,
marco ConfigView y vista temporal), `ConfigurationSession` y `Catalog`, todos GPL-2.0-or-later.
No copia AppletConfiguration.qml ni CompactApplet.qml de plasma-desktop; carga formularios de
los paquetes originales. Usa además KF6 NewStuffWidgets y el proveedor plasmoids.knsrc de la
distribución, manteniendo sus licencias. QtTest/ASan prueban el adaptador sin redistribuir los
widgets ni ejecutar un shell Plasma. Estado y diferencias en BREEZE_R4_RESULTS.md.

La continuación R4 del 2026-11-13 utiliza también LayerShellQt 6.7.5 instalado, mediante su
API pública Window, sin copiar su implementación. `surfaces.*`, `migration.*` y sus pruebas
son código propio GPL-2.0-or-later; geometría y publicación de la migración quedan fuera del
compositor. La fuente de referencia y SHA-256 del tarball LayerShellQt se registran en
BREEZE_R4_RESULTS.md. No se redistribuye el paquete plasma-desktop ni se ejecuta plasmashell.

Tras instalar plasma-desktop 6.7.5, el ensayo carga org.kde.panel y su LayoutManager desde
los recursos originales instalados. `panelsession.*` y `panelprobe.*` son adaptadores/pruebas
propios GPL-2.0-or-later. No se copian los QML del panel ni del menú de Andromeda. El filtro
de visibilidad se contrasta con PlasmaAppletItemModel de plasma-workspace 6.7.5 mediante sus
metadatos públicos. Procedencia y SHA-256 de las fuentes en BREEZE_R4_RESULTS.md.
`themeinventory.*` es código propio GPL-2.0-or-later que consulta Plasma/LookAndFeel/KConfig;
no copia ni evalúa layouts o vistas de temas. Conserva las rutas y procedencia de los recursos.
`packagewindows.*` y `viewcorona.*` son adaptadores propios GPL-2.0-or-later. Consultan las
APIs/contextos nativos de libplasma/PlasmaQuick 6.7.5, Qt y LayerShellQt sin copiar Dialog ni
alterar las bibliotecas/paquetes instalados. Pruebas y límites en BREEZE_R4_RESULTS.md.

R5: `src/bwm-plasma-host/panelconfigview.{h,cpp}` adapta `shell/panelconfigview.{h,cpp}` de
plasma-workspace 6.7.5 (Marco Martin, LGPL-2.0-or-later), con la cabecera SPDX y la autoría
originales y una nota de cambios BWM. Cargan sin modificar el `PanelConfiguration.qml` y sus
`panelconfiguration/*.qml` instalados de plasma-desktop 6.7.5 (no se copian al repositorio).
`src/bwm-plasma-host/qml/WidgetExplorerHost.qml` adapta parte de `desktoppackage/contents/views/Desktop.qml`
de plasma-desktop 6.7.5 (Marco Martin, David Edmundson; GPL-2.0-or-later), con su cabecera SPDX
y una nota de cambios BWM; carga sin modificar el `explorer/WidgetExplorer.qml` instalado.
`src/bwm-plasma-host/shell/contents/defaults` copia el grupo `[Panel]` de `desktoppackage/contents/defaults`
de plasma-desktop 6.7.5 (caja de herramientas `org.kde.paneltoolbox` y acción `org.kde.contextmenu`), con
un comentario de procedencia; los paquetes que nombra se cargan instalados, sin copiarlos.
La colocación del panel en `panelviewhost.cpp`/`surfaces.cpp` sigue `PanelView::preferredSize`,
`geometryByDistance` y `updateLayerWindow` de la misma versión, reescrita sin copiar el código.
`restoreAutoHide`, `setAutoHideEnabled`, `showTemporarily`, `updateTouchingWindow` y el manejo de
Enter/Leave/arrastre de `PanelView` 6.7.5 (`shell/panelview.cpp`, GPL-2.0-or-later) se portan a
`panelviewhost.cpp` con su procedencia en un comentario; el ocultado con franja de borde que sustituye
a `kde_auto_hide_screen_edge_v1` de KWin es propio de BWM.

La API de instancias/acciones de PanelSession y sus pruebas son propias GPL-2.0-or-later.
Utilizan Containment.createApplet, Applet.destroy, QAction/QMenu y el método reorderApplets
del panel original cargado desde sus recursos. Se revisan Corona.loadLayout/saveLayout y
Applet.saveState de libplasma 6.7.5; no se copian sus implementaciones ni LayoutManager.js.

La resolución de categorías por módulo QML de ConfigurationSession utiliza QQmlComponent
de Qt y ConfigCategory/ConfigModel de libplasma 6.7.5. Se estudia la prioridad de open() en
AppletConfiguration.qml del shell original; no se copia esa vista. La fábrica, la adaptación
de propiedades iniciales y los fixtures tests/{module-config,config-pages-module} son propios
GPL-2.0-or-later, instalados sólo en raíces temporales por las pruebas.

`panelviewhost.*` es un adaptador propio GPL-2.0-or-later sobre ContainmentView y KF6 Svg.
Carga sin modificar el views/Panel.qml instalado de org.kde.plasma.desktop (GPL-2.0-or-later,
© 2012 Marco Martin). Su registro de enums sigue los valores de PanelView 6.7.5; se revisan
su política de flotación/geometría y SharedQmlEngine para la destrucción segura del root.
No se copia Panel.qml, panelview.cpp ni sus sombras/efectos de compositor. Los SVG usados
como fixtures son rectángulos propios generados en raíces temporales, GPL-2.0-or-later.

`panelviewsettings.*` es propio GPL-2.0-or-later. Usa KConfig/QLockFile y la jerarquía de
plasmashellrc de PanelView 6.7.5 (panelConfig, configDefaults, restore y setters), sin copiar
sus implementaciones. Se contrasta applicationConfig de ShellCorona y la identidad de
plasmashell para el archivo nativo. Las políticas/fixtures de configuración se prueban sólo
en raíces XDG temporales; no se redistribuye código ni configuración de usuario de KDE.
La preparación de preferencias de vista de migration.* deriva los valores heredados del
Config.qml/PanelLogic.js propios y los serializa con KConfig en los grupos originales de
PanelView 6.7.5. panelprobe.* carga el Panel.qml instalado para verificar esa lectura, sin
copiarlo. Código nuevo GPL-2.0-or-later, sin recursos de terceros añadidos ni efectos portados.

`outputidentity.*` y `panelruntime.*` son propios GPL-2.0-or-later. Coordinan QScreen,
ViewCorona y las vistas nativas sin copiar ScreenPool/ShellCorona de Plasma. Los fixtures
de pantallas en test-ui.cpp usan las APIs QPA ya requeridas de Qt 6.11.2; se revisa el
contrato handleScreenRemoved/QPlatformScreen del tarball qtbase-everywhere-src-6.11.2,
sin copiar sus implementaciones. Sólo se añaden/eliminan pantallas dentro del proceso
offscreen de pruebas, no se redistribuyen módulos de plataforma ni código del compositor.

`runtimecontrol.*`, el publicador `skins/plasma/scripts/panel-session.py` y las ampliaciones
del dispatcher/gestor y envoltorio son código propio GPL-2.0-or-later. Usan Qt Core y la
biblioteca estándar Python para metadatos privados de integración, sin copiar servidores,
formatos de preferencias o servicios de Plasma. La configuración/layout siguen bajo las
APIs KDE originales. Las pruebas del protocolo/hook se ejecutan sólo en raíces desechables;
no se redistribuye un módulo de plataforma nuevo ni código de terceros adicional.

`profilestore.*` y las ampliaciones del CLI/envoltorio son propios GPL-2.0-or-later. Copian
archivos completos ya producidos por Corona/KConfig y llaman las APIs nativas para validar
copias, sin copiar la implementación de Plasma ni inventar otro formato appletsrc. Los
metadatos de bindings/generaciones/hashes son integración BWM separada. Fixtures y ensayos
se limitan a directorios temporales; no se añaden recursos de terceros ni dependencias.
La ampliación de almacenamiento persistente de ProfileStore usa GenericStateLocation de
Qt Core y un namespace propio de estado para copias/índices, conservando archivos KDE
completos. Código propio GPL-2.0-or-later; sin copiar implementaciones ni incorporar recursos
nuevos. El ensayo fuera de /tmp usa un XDG_STATE_HOME de fixture en el repo y lo elimina,
sin escribir perfiles en el estado real del usuario.

El diagnóstico de disponibilidad del anfitrión usa señales públicas de QQuickWindow de
Qt 6.11.2 (beforeRendering, frameSwapped y sceneGraphInvalidated), sin copiar implementaciones.
Las generaciones/contadores atómicos, agregación de bloqueos y ampliación status del
protocolo de ensayo son código propio GPL-2.0-or-later. No incorporan nuevas dependencias
ni certifican presentación física del compositor o funcionamiento de servicios KDE.

La ampliación de política de panel/reservas es propia GPL-2.0-or-later. Contrasta las APIs
instaladas y los tarballs plasma-workspace/layer-shell-qt 6.7.5 de Portage, en particular
PanelView::restore/setVisibilityMode/updateExclusiveZone/updateLayerWindow y
QWaylandLayerSurface::setDesiredSize/setExclusiveEdge. No copia sus implementaciones ni el
XML de protocolo al repo. Hashes, contrato y límites en BREEZE_R4_RESERVATION_RESULTS.json;
no añade dependencias. La petición LayerShellQt no se presenta como reserva física validada.

El diagnóstico R4 r4-session-check.py y sus tests son propios GPL-2.0-or-later; utilizan
Python estándar y la interfaz JSON del hyprctl instalado. No incorporan código de terceros,
dependencias nuevas ni un puente de ejecución fuera de las restricciones del asistente.

El runner temporal r4-reservation-smoke.py y sus tests son propios GPL-2.0-or-later.
Reutiliza el envoltorio existente y el ejemplo KDE de configuración de libplasma 6.7.5
ya seleccionado/extraído para ensayos; no redistribuye ese ejemplo ni añade dependencias.

La continuación de identidad de salidas consulta qtbase-everywhere-src 6.11.2 de Portage
(QWaylandScreen manufacturer/model y QPlatformScreen::serialNumber) sin copiar su código.
El matcher y el inventario Qt son propios GPL-2.0-or-later; hashes en
BREEZE_R4_OUTPUT_MATCH_RESULTS.json. No añade dependencias ni certifica serie EDID ausente.

El fixture Qt de maximizado, r4-maximized-check.py y pruebas son propios GPL-2.0-or-later.
Usan QQuickWindow público y los gestores BWM existentes; no copian interfaces ni algoritmos
KDE, no incorporan dependencias y no cambian plugins/compositor.

`kwin_area.py` y las ampliaciones de puente/runner/tests son propias GPL-2.0-or-later.
Reutilizan las matemáticas y reglas BWM existentes. Para los guardas Lua se consultan
LuaWindow.cpp y LuaMonitor.cpp del tarball Hyprland 0.56.2 de Portage, sin copiar sus
implementaciones. No añaden bibliotecas, protocolos ni servicios; hashes/procedencia en
BREEZE_R4_AREA_TRACKING_RESULTS.json. El código de API simulado para tests es propio y
no sustituye la aceptación en el compositor real.

`kns.*` y `kns-cycle.py` son propios GPL-2.0-or-later; enlazan KNewStuffCore 6.29 instalado
(LGPL) y usan el proveedor `plasmoids.knsrc` del sistema. Los widgets que descarga el ensayo se
instalan sólo en raíces temporales y se retiran; no se redistribuyen. El fixture
`tests/callback-config` es propio. El comportamiento de `saveConfig()`/claves del esquema sigue
`AppletConfiguration.qml` de plasma-desktop 6.7.5 sin copiar su código.

`focusgrab.*` es propio GPL-2.0-or-later. En la compilación, qtwaylandscanner/wayland-scanner
generan los enlaces cliente de `hyprland-focus-grab-v1.xml`, leído del paquete del sistema
hyprland-protocols (BSD-3-Clause, © 2024 outfoxxed; aviso completo en el propio XML); el XML
no se copia al repositorio, pero el binario incluye código generado a partir de él.
La preparación de plataforma de `main.cpp` (QT_WAYLAND_DISABLE_FIXED_POSITIONS alrededor de
QApplication, alfa por defecto) y la política de foco del panel siguen el comportamiento de
plasma-workspace 6.7.5 (`shell/main.cpp`, `PanelView::refreshStatus`) sin copiar su código.

La auditoría de transición de skins utiliza el código propio GPL-2.0-or-later
`bwm-launch-app.py` y el probe `tests/qt_skin_icon_probe.cpp`. Consulta Qt 6.11.2,
plasma-integration 6.7.5 y KIconThemes 6.29.0 instalados; sus implementaciones no se copian.
Los iconos PNG de prueba se generan en directorios temporales. El contrato privado del
receptor KF6 se usa sólo en el test local, no en los componentes desplegados.

TaskMenuPolicy y test-taskmenu.cpp son propios GPL-2.0-or-later. Usan APIs públicas de Qt
(QMenu/QAction/QActionGroup) ya enlazadas, y cargan el widget/menú original instalado sin
copiar ni redistribuir su QML. Se consultaron ContextMenu.qml, Task.qml y main.qml de
plasma-desktop 6.7.5; QMenuProxy/QMenuItem de libplasma 6.7.5, y el proxy agrupador de
plasma-workspace 6.7.5. El contrato privado se fija al hash del ContextMenu.qml original;
no se copian sus implementaciones ni se modifican metadatos del sistema. Archivos consultados,
hashes y resultados en BREEZE_R4_TASK_MENU_RESULTS.json. El fixture no certifica render ni
entrada real de la barra. No añade bibliotecas/protocolos o recursos de terceros.

La continuación de fullscreen nativo en tasksource/native-tasks/kwin-window y sus tests es
propia GPL-2.0-or-later; no copia el menú o los bindings de KDE/Hyprland. Se consultaron
WaylandTasksModel/ContextMenu de Plasma 6.7.5 y las fuentes Hyprland 0.56.2 de HyprCtl,
ConfigManager Lua, bindings dispatch/result/window y FullscreenController para comprobar
set/unset, repl y lectura de modo interno. El intérprete Lua se usa sólo en BUILD_TESTING
para ejecutar el Lua generado contra un hl simulado; no se incorpora código Lua de terceros
ni otro compositor/servidor. Referencias exactas, hashes y límites en BREEZE_R4_FULLSCREEN_RESULTS.json.

La invalidación de AppData de BwmTaskSource y test-taskmetadata.cpp son propios GPL-2.0-or-later.
Usan la API pública KSycoca/TaskTools de las bibliotecas ya enlazadas; contrastan la estrategia
de invalidación de WaylandTasksModel (plasma-workspace 6.7.5) y la notificación de archivo de
KService 6.29.0 sin copiar sus implementaciones. kbuildsycoca6 instalado sólo se ejecuta en el
test con cache XDG privado. Las entradas .desktop y PNG del test son propios y desechables,
no ejecutan aplicaciones y no incorporan assets de terceros. Procedencia/hashes/evidencia en
BREEZE_R4_TASK_METADATA_RESULTS.json. No se añaden dependencias de producción.

NativeDesktopRegistry, la ampliación v2 del protocolo BWM y las modificaciones de control,
runtime y fixtures son propias GPL-2.0-or-later. Usan APIs públicas de Qt/Wayland y bindings
generados del XML propio, sin copiar ni parchear el consumidor KDE. Se consultaron Qt 6.11.2
(qwaylanddisplay, QWaylandClientExtension, NativeInterface), VirtualDesktopInfo de
plasma-workspace 6.7.5 y wl_global_get_name/recursos de Wayland 1.26.0. Esa API de nombre está
disponible desde 1.22. No se copian esas implementaciones. El fixture crea globals alternativos
propios y un proceso Qt adicional sobre un endpoint privado ya existente; no redistribuye
componentes ni inicia otro compositor. Procedencia/hashes: BREEZE_R4_REGISTRY_RESULTS.json.


DesktopProvider, el marcador de elección y test-provider.cpp (§225) son propios GPL-2.0-or-later.
Enlazan las bibliotecas Wayland client/server ya declaradas, usando APIs públicas sin copiar
implementaciones. Se consultaron wayland-server.c, wayland-client.c y connection.c de Wayland
1.26.0 para global_remove, ofertas/binds en vuelo, get_name/filtros, propiedad de fds y E/S
no bloqueante. El consumidor de prueba carga VirtualDesktopInfo original de plasma-workspace
6.7.5, sin modificarlo/copiarlo. El XML privado KDE y sus avisos/pins siguen iguales. No hay
nuevo recurso de terceros ni daemon/compositor incorporado. Fuentes exactas, hashes y límites
en BREEZE_R4_PROVIDER_ARBITRATION_RESULTS.json.


La continuación §226 de arranque/cierre, el DSO test-teardown-module.cpp y su test son propios
GPL-2.0-or-later. Se consultaron Compositor.cpp (filterGlobals/cleanup), ProtocolManager.cpp,
SecurityContext.cpp y PluginSystem.cpp de Hyprland 0.56.2 para orden de cierre, filtro y
recarga posterior a init; no se copian sus implementaciones. dlopen/dlclose/libdl sólo en
la prueba aislada, enlazada mediante CMAKE_DL_LIBS, no en el proveedor de producción.
No se introduce dependencia nueva de producción ni se incorpora otro compositor/servidor.
Wayland y XML originales mantienen avisos y contratos. Hashes/referencias/evidencia en
BREEZE_R4_STARTUP_TEARDOWN_RESULTS.json.


CountMirror, native_workspaces.py, check-count-mirror.py y las extensiones de tests/puente
§227 son propios GPL-2.0-or-later. Usan C++/Python estándar y el IPC existente HyprCtl; se
consultó src/debug/HyprCtl.cpp de Hyprland0.56.2 para orden exact/prefix y entrega del request
completo, y el Config.qml común ya incluido para su default del contador. No se copian
implementaciones nuevas de terceros ni se añaden dependencias de producción, protocolos de
preferencias o servidores. El consumidor original KDE sigue instalado/intacto. Fuentes,
hashes y límites de prueba: BREEZE_R4_COUNT_MIRROR_RESULTS.json.


SharedSettingsRuntime.qml, shared dispatcher/effective_options, el auxiliar shared y sus tests
§228 son propios GPL-2.0-or-later. Se consultaron process.cpp/process.hpp y datastream.cpp de
Quickshell0.3.2 para orden streamEnded/exited y FailedToStart sin señal exited; no se copian
sus implementaciones. Se usan QtQuick/Quickshell.Io y Python estándar ya declarados. El QML
de prueba no representa superficies ni accede al compositor; transporte de recibos hacia
el mismo núcleo C++ de BWM. No dependencias/activos nuevos de terceros ni scripts descargados
ejecutados. Procedencia/hashes/evidencia: BREEZE_R4_SHARED_DELIVERY_RESULTS.json.


El test-taskdelegate y las mejoras de diagnóstico del fixture/runner (§229) son propios
GPL-2.0-or-later. Consultan WindowTasksModel::roleNames, TasksModel::roleNames, fuentes QML
Task.qml/main.qml originales de Plasma6.7.5 y usan las APIs Qt6 QQuickRenderControl/
QQuickRenderTarget/QImage ya enlazadas. Cargan los widgets instalados sin copiarlos o
modificarlos; sin activos o dependencias nuevos de terceros. No se incorpora otro compositor
ni servidor de sesión. Prueba nativa preparada, ejecución bloqueada por EPERM del cliente
Wayland privado; no resultado de render aprobado. Referencias/hashes y alcance exacto en
BREEZE_R4_TASK_DELEGATE_RESULTS.json.


La guarda compartida de pruebas tests/task-qml-source.h (§231) es propia GPL-2.0-or-later.
Lee/verifica el recurso Task.qml instalado sin copiarlo; SHA256 fijado al original Plasma6.7.5.
Se consultaron QQmlContext, QQuickRenderControl y QSGSoftwareRenderer de Qt6.11.2 para
resolución y secuencia de dibujo en memoria. Sin implementación/activo/dependencia nuevos
de terceros. La prueba de API Qt no certifica el render del widget KDE. Evidencia §231.


La preparación tests/task-app-fixture.h (§232), su .desktop/PNG generados y las comprobaciones
son propios GPL-2.0-or-later. Usan KService/KSycoca/TaskTools instalados sin copiar su código;
se consultó windowUrlFromMetadata/appDataFromUrl de Plasma6.7.5 para fallback por PID y sufijo
de AppId. kbuildsycoca6 sigue sólo en BUILD_TESTING, ya declarado. Sin dependencia/activo nuevo
de producción; datos sólo en XDG temporal. Resultados y límites en evidencia §232.


La proyección stackingOrder, el rol BWM y pruebas de §234 son propios GPL-2.0-or-later.
El ensayo importa TaskTools.js original instalado de Plasma6.7.5 (GPL-2.0-or-later), fijado
por SHA256, sin copiar/parchear sus handlers. Se consultaron clientsRequest de HyprCtl.cpp
y WindowState.cpp de Hyprland0.56.2 para orden inferior/superior; no se copian implementaciones.
Sin activos/dependencias nuevos ni formatos de temas propios. Referencias/evidencia en
BREEZE_R4_GROUP_ORDER_RESULTS.json.


El recorrido visual/propietario de BwmTaskBridge, test-paneltasks y previewchecks (§235)
son propios GPL-2.0-or-later. Usan QObject/QQuickItem y modelos KDE originales mediante APIs
públicas, sin copiar/parchear applets. Datos .desktop/PNG propios y helper/IPC ficticio dentro
de XDG temporal; sin nuevos activos/dependencias. Alcance y evidencia en
BREEZE_R4_PANEL_TASK_REGISTRATION_RESULTS.json.

La preparación explícita del preview de todos los escritorios (§236, taskpreview.*),
diagnósticos/tests y regla del almacén minimizado son propios GPL-2.0-or-later. Configuran
el campo original showOnlyCurrentDesktop con APIs públicas Plasma/KConfigLoader, sin copiar
ni parchear QML. Fuentes consultadas: plasma-desktop/plasma-workspace6.7.5 (main.xml,
main.qml y TaskFilterProxyModel) e Hyprland0.56.2 (GlobalWindowController, Window,
AnimationManager, WindowRuleApplicator). Licencias de esos originales conservadas; sin
nuevos recursos o dependencias. Referencias/hashes en BREEZE_R4_DESKTOP_FILTER_RESULTS.json.

La preparación de apariencia del preview (§238, previewappearance.*, check-preview-appearance.py
 y test-previewappearance.cpp) es propia GPL-2.0-or-later, usando KConfig/libplasma y Qt públicos.
Consulta de fuentes plasma-integration6.7.5 (proveedor Qt6 KDE), KConfig6.29 (cascada y fuentes
adicionales); sin copia/parche del motor de iconos o QML. El PNG/index.theme de prueba son
datos originales mínimos, sin imágenes externas. plasma-integration ya figura en requisitos;
sin dependencias nuevas. Referencias/hashes en BREEZE_R4_APPEARANCE_RESULTS.json.

Miniaturas de R4 (§239): taskthumbnail.*, fixtures y runners nuevos son propios
GPL-2.0-or-later. qml/TaskThumbnail.qml adapta únicamente PipeWireThumbnail.qml de
plasma-desktop6.7.5, Copyright2020 Aleix Pol Gonzalez, LGPL-2.0-or-later (avisos conservados).
Se mantiene todo el tooltip upstream instalado; la URL/hash revisados seleccionan el endpoint.
No se copia ni sustituye código privado de LibTaskManager o el proveedor PipeWire de KDE.

protocols/wlr-foreign-toplevel-management-unstable-v1.xml es copia íntegra sin cambios de
Hyprland0.56.2, Copyright2018 Ilia Bozhinov, con su licencia permisiva íntegra en el XML.
Sólo se necesitan sus descriptores de tipo referidos por el XML mapping; no se vincula el
manager WLR. Los XML ext-foreign-toplevel-list/ext-image-capture-source/ext-image-copy-capture
se usan desde wayland-protocols instalado; MIT y créditos completos en
licenses/wayland-protocols-image-capture-MIT.txt. hyprland-toplevel-mapping-v1.xml se usa desde
hyprland-protocols instalado; BSD-3-Clause, Copyright2025 WhySoBad, en
licenses/hyprland-toplevel-mapping-BSD-3-Clause.txt. Generación con wayland-scanner; sin cambios
a los protocolos. Fuentes/versión/hash y límites en BREEZE_R4_THUMBNAIL_RESULTS.json.

El parche patches/hyprland/0.56.2-screenshare-monitor-guard.patch sigue BSD-3-Clause de
Hyprland0.56.2; no cambia la licencia del compositor. Fixture tests/upstream/Hyprland-0.56.2-
ScreenshareSession.cpp copiado sin cambios del archivo original para aplicar/revisar el
parche y compilar sus dos cuerpos con scaffolding de prueba propio GPL-2.0-or-later.
Texto original en licenses/Hyprland-BSD-3-Clause.txt. check-screenshare-guard.py y la guarda
de ELF del auxiliar son propios GPL-2.0-or-later. Sin binario de compositor distribuido,
recompilación/instalación de sistema o capturas reactivadas por este cambio.

La corrección de conexiones/destructor de TaskThumbnail y sus regresiones de vida (§240)
son propias GPL-2.0-or-later, mediante QObject/QQuickItem públicos. Sin cambios a Qt/KDE,
QML upstream, XML, licencias o dependencias del backend descrito en §239.

El diagnóstico estructurado de peer/guarda, runner privado y espera de ack inicial (§243)
son propios GPL-2.0-or-later, usando Qt/Linux/Python públicos. Sin copiar/parchear KDE,
retirar guardas, cambiar permisos/capacidades del compositor o añadir dependencias.

La ampliación §244 del parche BSD-3-Clause añade una cabecera interna propia y el informe
JSON de guarda/PID en SystemInfo.cpp, sin cambiar formatos KDE ni estructuras de plugins.
tests/upstream/Hyprland-0.56.2-SystemInfo.cpp es copia íntegra sin cambios de
hyprland-0.56.2.gh.tar.gz, src/helpers/SystemInfo.cpp (misma licencia Hyprland incluida).
El test compila su getVersion original/corregido con scaffolding propio. Consulta IPC,
validación de PID/UID y pruebas del auxiliar son propias GPL-2.0-or-later mediante Qt/Linux.
Sin recursos externos o dependencias nuevas; hashes y evidencia en userFollowUp244 de
BREEZE_R4_THUMBNAIL_RESULTS.json. La extensión no está instalada ni activa por este trabajo.

La adaptación de PopupPlasmaWindow/ToolTipDialog en el auxiliar (§246) es propia
GPL-2.0-or-later, mediante APIs públicas PlasmaQuick/Qt/LayerShellQt; no copia ni sustituye
el tooltip o código privado de KDE/Qt. Prueba instancia Core.ToolTipArea original instalado.
Fuentes primarias locales consultadas: libplasma6.7.5 tooltiparea/tooltipdialog/
popupplasmawindow, QtBase6.11.2 QWindow/QWaylandWindow y LayerShellQt6.7.5 Window, conservando
sus licencias originales existentes. Sin dependencias o recursos de terceros nuevos.

Lanzamiento de aplicaciones de tareas (§248): tasklauncher.cpp adapta la política de
canLauchNewInstance de plasma-workspace6.7.5/libtaskmanager/tasktools.cpp, copyright2016 Eike
Hein y2023 Harald Sitter. El original permite LGPL-2.1-only OR LGPL-3.0-only OR
LicenseRef-KDE-Accepted-LGPL; esta adaptación y la supervisión añadida eligen LGPL-2.1-only.
Avisos en el archivo y texto íntegro original en licenses/plasma-tasktools-LGPL-2.1-only.txt.
Sólo se adapta esa política de datos .desktop; no se reimplementa el ejecutor ni se copian
privados KDE. AppData/KService, ApplicationLauncherJob/KJob públicos realizan resolución y
arranque. tasklauncher.h, native_launch.py, peticiones/puente y fixtures propios son
GPL-2.0-or-later. Origen/versiones/hashes en BREEZE_R4_TASK_LAUNCH_RESULTS.json; sin binarios
externos o recursos gráficos nuevos. KIOGui ahora es dependencia explícita de build.
Lanzadores anclados y Actions (§250): launchrouter.cpp reconstruye con APIs públicas de
KService/KDesktopFile la resolución y el filtro de Backend::jumpListActions y
tryDecodeApplicationsUrl de plasma-desktop 6.7.5 (applets/taskmanager/backend.cpp,
copyright 2012–2016 Eike Hein, GPL-2.0-or-later); el archivo es GPL-2.0-or-later. La
resolución de lanzadores de tasklauncher.cpp sigue runApp de plasma-workspace 6.7.5
(libtaskmanager/tasktools.cpp, mismos términos LGPL que §248). No se copia ni modifica QML ni
C++ de KDE; la política KIOSK usa el formato kdeglobals estándar.

## Regresión de foco por salida — Hyprland 0.56.2 (R4 §262)

`src/bwm-plasma-desktops/tests/upstream/Hyprland-0.56.2-WorkspaceActions.cpp` contiene
extractos sin modificar de `src/config/shared/actions/ConfigActions.cpp` de Hyprland
v0.56.2 (`efb50993780079460b0cbed1363e2166a2de1d9f`), desde el tarball de Portage
`hyprland-0.56.2.gh.tar.gz`: `tryMoveFocusToMonitor`, `Actions::focusMonitor` y la
sobrecarga por objeto de `Actions::changeWorkspace`. Copyright 2022–2026 vaxerski,
BSD-3-Clause; texto íntegro en `licenses/Hyprland-BSD-3-Clause.txt`. El archivo lleva
su aviso y una huella fijada por el ensayo. Fuente correspondiente:
<https://github.com/hyprwm/Hyprland/tree/v0.56.2>.

`check-activation-routing.py` y su andamiaje de datos son código BWM propio GPL-2.0-or-later;
compilan esos cuerpos junto al `applyExact` actual de BWM para reproducir la interacción
de foco/puntero, sin iniciar un compositor. No se copian esas implementaciones al plugin
de producción ni se presenta el andamiaje como una implementación completa de Hyprland.
### xdg-dbus-proxy 0.1.8 (ensayo R4)

Copyright © 2015 Red Hat, Inc. y autores indicados en el código original. LGPL-2.1-or-later.
Fuente correspondiente: `xdg-dbus-proxy-0.1.8.tar.xz`, publicado por el proyecto Flatpak.
El archivo se valida por SHA-256 en `src/bwm-plasma-host/build-tray-proxy.py`.
`patches/xdg-dbus-proxy/0.1.8-sni-unique-getall.patch` añade reglas de lectura de
propiedades y de las señales SNI `NewStatus` y `NewIcon` para un objeto exacto de
un nombre único D-Bus. La compilación es local.
Texto original: `licenses/xdg-dbus-proxy-LGPL-2.1-or-later.txt`.

### Clonación de paneles de Plasma 6.7.5 (R5)

`src/bwm-plasma-host/panelclone.cpp` adapta `ShellCorona::clonePanelTo` de
`plasma-workspace-6.7.5/shell/shellcorona.cpp` (tarball de Portage). Conserva los avisos
originales de Aaron Seigo (2008), Sebastian Kügler, Ivan Cukic y Marco Martin (2013),
LGPL-2.0-or-later. Fuente correspondiente:
<https://invent.kde.org/plasma/plasma-workspace/-/blob/v6.7.5/shell/shellcorona.cpp>.
Cambios BWM: copia recursiva de containments embebidos, remapeo de IDs desde la configuración
fuente sin dejar grupos de los IDs antiguos, y ciclo de vistas/salidas separado en
`PanelRuntime`. El QML de edición instalado se sigue cargando sin cambios. La API auxiliar,
las transacciones de perfiles y los ensayos nuevos son código BWM GPL-2.0-or-later.


### Reservas de varios paneles — Plasma 6.7.5 (R5)

`PanelRuntime::updateReservations` adapta la selección de
`ShellCorona::shouldPanelReserveSpace`, de `shell/shellcorona.cpp`, LGPL-2.0-or-later
(Aaron Seigo, Sebastian Kügler, Ivan Cukic y Marco Martin, avisos indicados arriba).
`BwmSurface::setPanelReservationPolicy` sigue `PanelView::updateExclusiveZone`, de
`shell/panelview.cpp`, copyright 2013 Marco Martin, GPL-2.0-or-later. Fuente correspondiente:
<https://invent.kde.org/plasma/plasma-workspace/-/tree/v6.7.5/shell> (tarball de Portage).
Adaptaciones BWM: desempate estable por ID, coordinador de vistas ligado a las salidas por
su descripción, conservación de zonas al entrar en edición y entrega por LayerShellQt/QtQuick
al compositor Hyprland. No se copia ni modifica el QML de Plasma; las reservas se entregan
mediante layer-shell en Hyprland.
