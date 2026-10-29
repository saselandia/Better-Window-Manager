# Skins de BWM

> Esta página hace de wiki de skins: la enlaza la bienvenida (`bwm`, paso «Añadir skins»).

## Qué es una skin

BWM (Better Window Manager) es un gestor de ventanas que trata de encapsular todos los gestores de
ventanas y escritorios que existen como **skins**. Una skin reproduce otro escritorio entero sobre
Hyprland + Quickshell: su barra y paneles, sus menús, su lanzador, sus notificaciones, su bloqueo,
sus atajos, sus decoraciones de ventana y, sobre todo, **sus temas**. Al cambiar de skin
(`Alt + T`, `bwm skin <id>`) cambia todo el sistema: GTK, Qt, terminales, navegador y apps.

**Regla del proyecto: compatibilidad con el ecosistema de temas del original.** Una skin no está
terminada cuando se parece al escritorio que imita, sino cuando acepta lo que la gente ya usa para
cambiar su aspecto. Si estás en la skin KDE Plasma y pones un tema de Plasma de internet, debe
aplicarse y funcionar; en Retro, un tema o plugin de Omarchy. Cuando haya que elegir, se adapta BWM
al formato del original y no al revés.

**Pocas skins, fáciles y con lo mismo.** BWM ofrece muy pocas skins —las tres actuales— que hacen
lo esencial y se aprenden enseguida. Comparten casi las mismas funciones básicas, así que cambiar de
una a otra no obliga a reaprender. Si un escritorio tiene algo muy importante y propio, su skin lo
trae; el resto de complejidad la puede añadir quien la quiera, pero BWM no la ofrece de serie.

**Un único compositor.** BWM porta a Hyprland escritorios que no corren sobre él —KDE Plasma está en
curso— para tenerlo todo en un solo compositor. Cada escritorio porteado es una skin.

## Mosaico o WM tradicional: la variable `windows`

Toda skin declara en su `skin.json` cómo gestiona las ventanas:

* `"windows": "tiling"` — **mosaico** (Default, Retro): las ventanas se reparten la pantalla sin solaparse.
* `"windows": "traditional"` — **WM tradicional** (KDE Plasma; el modelo de Windows, macOS o GNOME):
  cada ventana flota con su barra de título y se solapan. Añade un bloque `"traditional"` con la barra
  de título, el panel, el margen con los bordes y el hueco entre ventanas.

El paso entre las dos familias lo resuelve BWM para cualquier skin (`scripts/bwm_windows.py`): al
entrar en una tradicional, cada ventana flota **en el mismo sitio** que tenía en mosaico; al volver a
una de mosaico, se rehace el mosaico. Detalle y ejemplo en
[`config/hypr/skins/README.md`](../config/hypr/skins/README.md).

## Skins incluidas

| id | Skin | Imita | Tema por defecto | Ecosistema de temas |
| :--- | :--- | :--- | :--- | :--- |
| `default` | Default | end-4 / illogical-impulse | Material You **dinámico** (matugen desde el fondo) | Plantillas de matugen, fondos |
| `retro` | Retro | Omarchy 4 (`quattro`) | Paleta **dinámica** con formato de Omarchy; 23 temas **estáticos** de Omarchy | `colors.toml` de Omarchy, plugins del shell de Omarchy (Ajustes → Temas / Plugins) |
| `plasma` | KDE Plasma | Plasma 6 Breeze Dark | Breeze Dark **estático** | Esquemas de color y temas globales de Plasma (objetivo, pendiente) |

*Dinámico* = la paleta se genera del fondo de pantalla y cambia con él. *Estático* = colores fijos
de un tema; cambiar el fondo no los toca.

## Compatibilidad actual (estimación)

| Skin | Temas del original | Plugins del original | Falta |
| :--- | :---: | :---: | :--- |
| Retro | ~90 % | ~80 % | `hyprland.lua` e `icons.theme` de los temas, tema de Chromium (root); plugins que sustituyen barra, bloqueo, overlays o paneles |
| Default | ~90 % | — | Plantillas de matugen de terceros: se añaden a mano en `matugen/config.toml` |
| KDE Plasma | ~5 % | 0 % | Esquemas de color (`.colors`), temas globales, estilos de Plasma, Aurorae, plasmoides. Sólo funcionan los cursores |

Actualiza esta tabla y la del README cuando cambie el soporte.

## Qué se conserva entre skins

Al cambiar de skin, todo esto sigue igual (es del usuario, no de la skin):

| Qué | Dónde vive |
| :--- | :--- |
| Red, Bluetooth, dispositivos de audio | El sistema (NetworkManager, BlueZ, PipeWire) |
| Cursor (tema y tamaño) | `hypr/modules/cursor.lua`, GTK `settings.ini` (`cursor-manager.py`) |
| Luz nocturna: temperatura en Kelvin | `~/.local/state/bwm/nightlight.json` y `light.night.colorTemperature`, sincronizados por `nightlight.py` |
| Aplicaciones predeterminadas | `~/.config/bwm/default-apps.json`, sección `apps`, `xdg-mime`. El gestor de archivos podría pasar a ser de cada skin (Dolphin en Plasma): pendiente de decidir |
| Workspaces: los mismos 1–N y sus monitores | Hyprland + `monitor-manager.py`; cuántos se muestran (`bar.workspaces.shown`) es común |
| Pantallas: resolución, Hz, posición, escala | `monitor-manager.py` (`monitors_layout.json`, `monitors.lua`); un cambio en una skin vale para todas |
| Inicio automático | `autostart-manager.py` (fuera de `config.json`) |
| Servicios: tiempo, IA, búsqueda, actualizaciones… | Secciones comunes de `config.json` y `bar.weather` |
| Interfaz: logo, vista general, OSD, bloqueo, ventanas, superposiciones | `cheatsheet`, `overview`, `osd`, `lock`, `windows`, `overlay`… y `bar.topLeftIcon` |
| General: idioma, hora, batería, políticas | Secciones comunes de `config.json` |
| Atajos | `hypr/keybinds.json` (salvo los propios de una skin, como Ctrl+flechas en Plasma) |

Propio de cada skin: el aspecto y las fuentes (las de la skin y, en Retro, las de su tema), el fondo,
la barra (salvo cuántos workspaces, el tiempo y el logo) y el dock (el de BWM o el de Omarchy).
Mecanismo: `bwm-theme-manager.py` (`THEME_SPECIFIC_SECTIONS`, `SHARED_KEYS_IN_SKIN_SECTIONS`) guarda
un perfil `config-<id>.json` por skin y, al cambiar, hereda las secciones comunes del perfil saliente.

## Estructura modular

Regla del proyecto: cada skin vive en sus propias carpetas/módulos y lo común en carpetas comunes,
sin mezclar. Así una skin nueva o un cambio en una no rompe las demás.

| | Común a todas | De una skin |
| :--- | :--- | :--- |
| Manifiesto, aspecto y requisitos | `hypr/skins/requirements.json` | `hypr/skins/<id>/skin.json` |
| Ajustes de Quickshell | Secciones comunes de `config.json` | `illogical-impulse/config-<id>.json` (secciones propias) |
| Interfaz QML | `quickshell/ii/modules/common`, `services`, `modules/settings` | Default: `modules/ii/*` de illogical-impulse; Retro: `modules/ii/omarchy*`, `modules/ii/bar/omarchy`, `Commons`, `Ui`, `omarchy-plugins`; Plasma: `modules/ii/plasma*`, `plasmaCommon` |
| Qué se carga en cada skin | `panelFamilies/IllogicalImpulseFamily.qml` (`extraCondition`) | — |
| Colores de Hyprland y apps | `hypr/modules/*.lua`, `matugen/` | `colors.lua` (Default), `retro_colors.lua` + `hypr/omarchy/` (Retro), `plasma_colors.lua` (Plasma) |
| Plugins de Hyprland | — | `src/hyprbars` (Plasma) |

En Retro, Configuración forma parte del menú de Omarchy: el catálogo y los editores viven en
`modules/ii/omarchyMenu/omarchy/settings/`. `SettingsPage.qml` aloja los controles compartidos
más complejos en la misma capa; `modules/settings/retro/SettingsStyle.qml` los adapta a la paleta.
`open-settings.sh` usa IPC y `retroSettings.qml` conserva compatibilidad con comandos antiguos,
sin crear una ventana de Ajustes.

Lo que aún está mezclado (por ejemplo, barras de varias skins bajo `modules/ii/bar/`) se irá
separando cuando se toque; el código nuevo ya debe nacer en la carpeta de su skin.

## Crear una skin

Cada skin es una carpeta `config/hypr/skins/<id>/` con un único `skin.json` (identidad, variable
`windows`, motor de colores, aspecto, barra, fuentes, mapa de archivos `parts` y requisitos). Las de
la comunidad irán en `~/.local/share/bwm/skins/<id>/skin.json`. La guía paso a paso, la tabla de
campos y la plantilla (`_template/skin.json`) están en
[`config/hypr/skins/README.md`](../config/hypr/skins/README.md).

* La skin aparece **en verde** en la bienvenida cuando el núcleo y todos sus `requires` están.
  `bwm skin <id>` se niega a activarla si falta algo.
* Requisitos: ids del catálogo de `config/hypr/skins/requirements.json` (paquetes por distribución y
  cómo se comprueba cada uno: `cmd`, `version`, `qml`, `qtplugin`, `python`, `pymodule`, `path`,
  `font`, `pkgconfig`, `hyprland-plugin`). Una skin puede añadir los suyos en `catalog`.
* `tests/test_skins.py` comprueba que cada `skin.json` está completo, que su variable `windows` es
  válida y que las rutas de `parts` existen.

Instalar skins de terceros sin tocar el repositorio (formato de paquete, firma, sandbox) está por
diseñar; cuando exista se documentará aquí y la bienvenida podrá activarlas.
