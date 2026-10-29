# Third-party notices / Avisos de terceros

BWM reúne componentes con licencias diferentes. Los textos en `licenses/` y los avisos de cada
componente acompañan al código y a las distribuciones; ningún distintivo MIT cubre el conjunto.
Este inventario no sustituye las licencias originales ni autoriza a relicenciar código ajeno.
Los binarios existentes deben corresponder a su código fuente y avisos antes de una release.

| Componente y rutas | Procedencia y licencia | Distribución y cambios |
| :--- | :--- | :--- |
| Shell illogical-impulse, partes de `config/quickshell/ii/` | [end-4/dots-hyprland](https://github.com/end-4/dots-hyprland), GPL-3.0; [texto](licenses/GPL-3.0.txt) y `config/quickshell/ii/COPYING` | BWM adapta el shell, los servicios y la configuración para sus skins. Los cambios y fechas se detallan en el historial Git de cada archivo. El código derivado se distribuye bajo la GPL correspondiente; los subdirectorios vendorizados con licencia propia conservan sus avisos. La revisión exacta de origen aún debe fijarse. |
| hyprbars, `src/hyprbars/` y sus `.so` en `config/hypr/plugins/` | [hyprwm/hyprland-plugins](https://github.com/hyprwm/hyprland-plugins), Copyright (c) 2023 Hypr Development, BSD-3-Clause; [texto íntegro](licenses/hyprland-plugins-BSD-3-Clause.txt), también en `src/hyprbars/LICENSE` | BWM añade decoraciones Breeze, detección CSD y snapping, y adapta la API a Hyprland 0.56. No se implica patrocinio de Hypr Development. El `.so` antiguo `config/hypr/plugins/hyprbars.so` debe cotejarse con su revisión fuente antes de distribuir binarios. |
| Omarchy: `config/hypr/omarchy/`, librerías `config/quickshell/ii/Commons/`, `Ui/` y módulos identificados como Omarchy | [basecamp/omarchy, rama quattro](https://github.com/basecamp/omarchy/tree/quattro), Copyright (c) David Heinemeier Hansson, MIT; [texto íntegro](licenses/omarchy-MIT.txt) | BWM adapta shell, menús, temas, plantillas y pantallas de arranque. Los subdirectorios con avisos propios los conservan. Los fondos, marcas y recursos de terceros contenidos en temas requieren revisión independiente. |
| Plugins en `config/quickshell/ii/omarchy-plugins/` | Cada plugin conserva su `LICENSE` y manifiesto | Los iconos de `ai-usagebar/omarchy/icons/` tienen [créditos específicos](config/quickshell/ii/omarchy-plugins/ai-usagebar/omarchy/icons/README.md), incluida la licencia de Lobe Icons. Las marcas siguen perteneciendo a sus titulares. |
| Cursores `assets/cursors/Bibata-Modern-{Classic,Ice}` | [Bibata Cursor](https://github.com/ful1e5/Bibata_Cursor/tree/v2.0.6), GPL-3.0; `COPYING` junto a cada tema | Los `index.theme` indican v2.0.6; se incluyen XCursors y versiones Hyprcursor. Véase `SOURCE.md` en cada carpeta. La correspondencia de cada binario y la generación de Hyprcursor siguen pendientes de verificar. |
| Pywalfox, `config/firefox/extensions/pywalfox@frewacom.org.xpi` | [Frewacom/pywalfox](https://github.com/Frewacom/pywalfox/tree/v2.1.1), MPL-2.0; [texto](licenses/pywalfox-MPL-2.0.txt) | El manifiesto del XPI indica versión 2.1.1 (SHA-256 `b7a7a86d1d49a8309758ce1d38492975abe07a61e3788e2d913c70a4d07758b4`). El código publicado de esa versión está en la etiqueta enlazada; no se ha comprobado que el binario sea reproducible desde ella ni si contiene dependencias adicionales. |
| Fuentes `assets/fonts/` | Google Sans Flex, Readex Pro, Space Grotesk y JetBrains Mono Nerd Font: OFL-1.1. Material Symbols: fuente de la familia [Material Design Icons](https://github.com/google/material-design-icons), Apache-2.0 | Avisos por familia y licencias de Nerd Fonts 3.4.0 y 3.5.1 en `assets/fonts/licenses/`. Google Sans Flex: Copyright 2015 Google LLC según el TTF distribuido. JetBrains Mono: Copyright 2020 The JetBrains Mono Project Authors. La procedencia exacta de cada glifo añadido por Nerd Fonts y de la compilación de Material Symbols aún requiere cotejo. |
| Iconos Breeze en `config/quickshell/ii/assets/icons/breeze-dark/` | El proyecto [KDE/breeze-icons](https://github.com/KDE/breeze-icons), Copyright 2014 Uri Herrera y colaboradores, usa LGPL-3.0-or-later para sus iconos; [aviso de KDE](licenses/KDE-Breeze-COPYING-ICONS.txt), [LGPL](licenses/LGPL-3.0.txt) | Los archivos SVG distribuidos son su formato fuente. Debe confirmarse la procedencia y revisión exacta de cada icono incluido, así como cualquier excepción individual. |
| Iconos Fluent en `config/quickshell/ii/assets/icons/fluent/` | Joshua Oghenekaro Okwe, Windows 11 en Figma, CC BY 4.0 | [Aviso original](config/quickshell/ii/assets/icons/fluent/README.md) indica fuente y modificaciones. Verificar las condiciones de cada recurso descargado antes de distribuirlo. |
| Formas de `config/quickshell/ii/modules/common/widgets/shapes/` | Apache-2.0 | Texto en ese directorio; revisar procedencia y cualquier aviso `NOTICE` de la versión original. |

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
