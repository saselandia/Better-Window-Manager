# Third-party notices / Avisos de terceros

BWM reúne componentes con licencias diferentes. Los textos en `licenses/` y los avisos de cada
componente acompañan al código y a las distribuciones; ningún distintivo MIT cubre el conjunto.
Este inventario no sustituye las licencias originales ni autoriza a relicenciar código ajeno.
Los binarios existentes deben corresponder a su código fuente y avisos antes de una release.

| Componente y rutas | Procedencia y licencia | Distribución y cambios |
| :--- | :--- | :--- |
| Shell illogical-impulse, partes de `config/quickshell/ii/` | [end-4/dots-hyprland](https://github.com/end-4/dots-hyprland), GPL-3.0; [texto](licenses/GPL-3.0.txt) y `config/quickshell/ii/COPYING` | BWM adapta el shell, los servicios y la configuración para sus skins. Los cambios y fechas se detallan en el historial Git de cada archivo. El código derivado se distribuye bajo la GPL correspondiente; los subdirectorios vendorizados con licencia propia conservan sus avisos. La revisión exacta de origen aún debe fijarse. |
| hyprbars, `src/breezebars/` (plugin `breezebars`, el de Breeze) y su `.so` en `config/hypr/plugins/breezebars.so` | [hyprwm/hyprland-plugins](https://github.com/hyprwm/hyprland-plugins), Copyright (c) 2023 Hypr Development, BSD-3-Clause; [texto íntegro](licenses/hyprland-plugins-BSD-3-Clause.txt), también en `src/breezebars/LICENSE` | BWM añade decoraciones Breeze, detección CSD, snapping y la composición de las decoraciones de KDE que dibuja `bwm-decorator` (la sombra sigue el algoritmo de `shadowitem.cpp` de KWin, reescrito sin copiar código), adapta la API a Hyprland 0.56 y lo registra como `breezebars`. No se implica patrocinio de Hypr Development. El `.so` antiguo `config/hypr/plugins/hyprbars.so` debe cotejarse con su revisión fuente antes de distribuir binarios. |
| omarchy-hyprland-titlebars, `src/omarchy-titlebars/` y `config/hypr/plugins/omarchy-titlebars.so` | [omacom/omarchy-hyprland-titlebars](https://github.com/omacom/omarchy-hyprland-titlebars) `379ff91` (2026-10-13, el último que compila con Hyprland 0.56): fork de hyprbars (BSD-3-Clause, `src/omarchy-titlebars/LICENSE`) con cambios de Omarchy bajo MIT (`src/omarchy-titlebars/LICENSE.MIT`) | Sin cambios en el código; BWM sólo añade un `Makefile` que compila e instala de forma atómica. Barras de los workspaces flotantes de Retro. |
| Omarchy: `config/hypr/omarchy/`, librerías `config/quickshell/ii/Commons/`, `Ui/` y módulos identificados como Omarchy | [basecamp/omarchy, rama quattro](https://github.com/basecamp/omarchy/tree/quattro), Copyright (c) David Heinemeier Hansson, MIT; [texto íntegro](licenses/omarchy-MIT.txt) | BWM adapta shell, menús, temas, plantillas y pantallas de arranque. Los subdirectorios con avisos propios los conservan. Los fondos, marcas y recursos de terceros contenidos en temas requieren revisión independiente. Los logos de `modules/ii/bar/omarchy/agents/assets/` (Claude, Codex, Copilot, Cursor, NVIDIA y otros proveedores) vienen tal cual de Omarchy y siguen siendo marcas de sus titulares; no implican relación ni patrocinio. |
| Plugins en `config/quickshell/ii/omarchy-plugins/` | Cada plugin conserva su `LICENSE` y manifiesto | Los iconos de `ai-usagebar/omarchy/icons/` tienen [créditos específicos](config/quickshell/ii/omarchy-plugins/ai-usagebar/omarchy/icons/README.md), incluida la licencia de Lobe Icons. Las marcas siguen perteneciendo a sus titulares. |
| Omacalc (instalado por `config/hypr/scripts/install-omacalc.sh`) | [omacom/omacalc, `573d7106`](https://github.com/omacom/omacalc/tree/573d7106f5c6c0225864eb8634ae37ddcb657f63), Copyright (c) 2026 David Heinemeier Hansson, [MIT](licenses/omacalc-MIT.txt); fuente iA Writer Mono S incluida: Information Architects Inc. / IBM Plex (IBM Corp.), [OFL-1.1](licenses/omacalc-iA-Writer-OFL.txt) | Se conserva la interfaz, fuentes, aritmética e icono originales. `config/hypr/omacalc/theme-path.patch` añade una ruta opcional de paleta nativa (`OMACALC_THEME_FILE`) y su vigilancia; BWM genera sus colores con los motores existentes de cada skin. Fuentes correspondientes en `~/.local/share/bwm/omacalc/source`, parche y avisos junto al binario; el instalador conserva MIT y OFL. Detalle y reproducción en `config/hypr/omacalc/README.md`. |
| Cursores `assets/cursors/Bibata-Modern-{Classic,Ice}` | [Bibata Cursor](https://github.com/ful1e5/Bibata_Cursor/tree/v2.0.6), GPL-3.0; `COPYING` junto a cada tema | Los `index.theme` indican v2.0.6; se incluyen XCursors y versiones Hyprcursor. Véase `SOURCE.md` en cada carpeta. La correspondencia de cada binario y la generación de Hyprcursor siguen pendientes de verificar. |
| Pywalfox, `config/firefox/extensions/pywalfox@frewacom.org.xpi` | [Frewacom/pywalfox](https://github.com/Frewacom/pywalfox/tree/v2.1.1), MPL-2.0; [texto](licenses/pywalfox-MPL-2.0.txt) | El manifiesto del XPI indica versión 2.1.1 (SHA-256 `b7a7a86d1d49a8309758ce1d38492975abe07a61e3788e2d913c70a4d07758b4`). El código publicado de esa versión está en la etiqueta enlazada; no se ha comprobado que el binario sea reproducible desde ella ni si contiene dependencias adicionales. |
| Fuentes `assets/fonts/` | Google Sans Flex, Readex Pro, Space Grotesk y JetBrains Mono Nerd Font: OFL-1.1. Material Symbols: fuente de la familia [Material Design Icons](https://github.com/google/material-design-icons), Apache-2.0 | Avisos por familia y licencias de Nerd Fonts 3.4.0 y 3.5.1 en `assets/fonts/licenses/`. Google Sans Flex: Copyright 2015 Google LLC según el TTF distribuido. JetBrains Mono: Copyright 2020 The JetBrains Mono Project Authors. La procedencia exacta de cada glifo añadido por Nerd Fonts y de la compilación de Material Symbols aún requiere cotejo. |
| Iconos Breeze en `config/quickshell/ii/assets/icons/breeze-dark/` | El proyecto [KDE/breeze-icons](https://github.com/KDE/breeze-icons), Copyright 2014 Uri Herrera y colaboradores, usa LGPL-3.0-or-later para sus iconos; [aviso de KDE](licenses/KDE-Breeze-COPYING-ICONS.txt), [LGPL](licenses/LGPL-3.0.txt) | Los archivos SVG distribuidos son su formato fuente. Debe confirmarse la procedencia y revisión exacta de cada icono incluido, así como cualquier excepción individual. |
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
Omarchy quattro `598e4eb` (MIT) sin cambios. `modules/ii/plasmaLock/` es diseño propio que imita la
pantalla de bloqueo Breeze de Plasma 6, sin código de KDE; usa el icono `go-next` de breeze-icons.

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
* Iconos Breeze incluidos en `config/quickshell/ii/assets/icons/breeze-dark/`: verificar versión,
  autores y licencias de los archivos concretos; no basta el nombre del tema.
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
code/TaskTools.js) y
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
