# Plan: Breeze = KDE Plasma porteado a BWM

> Plan de acción para rehacer la skin **Breeze (Kde plasma)** (id `plasma`) como un port real de
> KDE Plasma 6 sobre Hyprland + Quickshell, compatible con los temas de Plasma. Cada fase es un
> prompt listo para pegar en una sesión nueva. Pensado para **Opus 5.5, esfuerzo medium**; las
> fases marcadas **[HIGH]** conviene lanzarlas con esfuerzo **high**.
>
> Redactado el 2026-11-10 a partir del estado del repo en `e54367d`.

## 1. Por qué rehacerla

Hoy Breeze es una imitación hecha a mano: QML propio que *se parece* a Plasma
(`modules/ii/plasma*`, `PlasmaBarContent.qml`), colores Breeze Dark fijos, un plugin de barras
(`breezebars`, `src/hyprbars`) que dibuja botones aproximados con cairo, detección de CSD con
heurísticas, y minimizado/maximizado/snapping repartidos entre `quick-tile.py`,
`toggle-minimize.py`, `placement.lua` y reglas de `rules.lua`. Nada de eso lee un tema de Plasma:
un tema bajado de la KDE Store no cambia nada (compatibilidad estimada en `docs/SKINS.md`: ~5 %).

El objetivo (regla 11 de `AGENTS.md`/`CLAUDE.md`): **que funcionen los formatos del original**.
En Plasma 6 eso es:

| Formato de Plasma | Dónde vive | Qué cambia |
| :--- | :--- | :--- |
| Esquema de color `.colors` | `~/.local/share/color-schemes`, `/usr/share/color-schemes` → `kdeglobals` | Colores de apps Qt, panel, decoraciones |
| Estilo de Plasma (*desktoptheme*, SVG) | `~/.local/share/plasma/desktoptheme/<tema>`, `plasmarc [Theme]` | Panel, popups, botones, iconos del panel |
| Decoración de ventanas (Breeze C++ o **Aurorae** SVG) | `kwinrc [org.kde.kdecoration2]`, `breezerc`, `~/.local/share/aurorae/themes` | Barras de título y botones |
| Tema global (*look-and-feel*) | `~/.local/share/plasma/look-and-feel/<id>` | Paquete con todo lo anterior + cambiador de tareas, OSD, bloqueo, splash, disposición |
| Iconos, cursores, fuentes | `kdeglobals [Icons]`, `kcminputrc`, `kdeglobals [General]` | — |
| Reglas de ventana | `kwinrulesrc` | Comportamiento por app |

La clave técnica: **usar las bibliotecas reales de KDE dentro de Quickshell** (KSvg, libplasma,
Kirigami, KConfig) para pintar con los SVG y colores del tema, y portar el QML original de los
plasmoides (Kickoff, gestor de tareas, bandeja, reloj…) sustituyendo sólo sus fuentes de datos
(que dependen de KWin) por las de Hyprland/BWM.

## 2. Reglas para todas las fases

Estas líneas van incluidas en cada prompt; no hace falta repetirlas a mano.

- Leer entero `CLAUDE.md` (o `AGENTS.md`) y las secciones de `BWM_CONTEXT.md` que cite el prompt.
- **Código de KDE:** clonar en el scratchpad (no en el repo) la rama/etiqueta `v6.7.5` (la versión
  estable de Plasma en Gentoo) de `https://invent.kde.org/plasma/<proyecto>` (KDE Frameworks:
  `https://invent.kde.org/frameworks/<proyecto>`, `v6.29.0`). Copiar el QML/C++ con sus cabeceras de
  licencia (GPL-2.0-or-later / LGPL-2.1-or-later), anotar origen, versión y cambios en
  `THIRD_PARTY_NOTICES.md` y un `README.md` en la carpeta portada (regla 15). Marcar cada cambio
  con un comentario `// BWM:` para poder actualizar desde upstream.
- **Modularidad (regla 13):** todo lo nuevo de Breeze vive en carpetas de la skin
  (`config/quickshell/ii/modules/plasma/…` para QML, `config/hypr/skins/plasma/…` para Lua/scripts,
  `src/breezebars/` para el plugin). Nada de `if (isPlasma)` nuevo en módulos comunes si puede ser
  un módulo aparte. Actualizar `parts` de `skins/plasma/skin.json` y `tests/test_skins.py`.
- **Paquetes:** si hace falta uno, comprobarlo con `emerge -p` y dar al usuario el comando exacto
  con sudo (regla 7: el usuario lo ejecuta; esperar a que confirme). Declararlo en
  `config/hypr/skins/requirements.json` (con paquetes de Arch/Fedora/Debian/openSUSE si existen),
  en `requires`/`recommends` de `skins/plasma/skin.json`, y regenerar `docs/REQUIREMENTS.md`
  (`bwm-requirements.py docs`) (regla 12). Añadir `referenceVersion` en el catálogo.
- **Se conserva entre skins (regla 14):** red/Bluetooth, cursor, Kelvin, apps predeterminadas,
  workspaces, pantallas/escala, inicio automático, servicios, interfaz y General. Lo que Plasma
  guarda en sus propios archivos para esas cosas debe **seguir a la configuración de BWM**, no al
  revés. Propio de Breeze: aspecto, fuentes, fondo, panel.
- **Configuración del usuario (regla 18):** `~/.config/bwm/user/*` manda; no editarla.
- **Cambio de skin sin interrupciones (regla 16)** y **snapping (regla 17)**: respetarlas.
- **Plugin de Hyprland (regla 1):** compilar con `-fno-gnu-unique`, desplegar sólo con
  `make install`, nunca cargar/descargar en caliente. Un plugin nuevo sólo se prueba tras volver a
  iniciar sesión: agrupar los cambios del plugin y pedir al usuario un reinicio de sesión cuando
  estén listos; mientras, probar la lógica con pruebas unitarias.
- **Quickshell (regla 2):** nunca un segundo `qs -c ii`; probar QML nuevo con `qs -p` en un archivo
  aparte y ventanas en el workspace 9 con regla temporal; `bwm-theme-manager.py set plasma
  --restart-shell` para reinicios de mantenimiento. Copias de prueba con acciones reales: sustituir
  todas y comprobar con `grep` (§6 de `CLAUDE.md`).
- Terminar cada fase con: pruebas (`python3 -m unittest discover -s tests`, `qmllint` de lo nuevo,
  `Hyprland --verify-config`, `hyprctl configerrors`, `qs -c ii log` sin errores nuevos), nueva
  sección al final de §3 de `BWM_CONTEXT.md`, §2.4 actualizado, `docs/SKINS.md` (compatibilidad)
  y commit **sólo de tus archivos** con la línea de coautoría. Sin push salvo que se pida. Separar
  lo comprobado de lo no probado.

## 3. Orden y dependencias

```
F0 Viabilidad [HIGH] ─┬─ F1 Motor de temas ─┬─ F3 Panel ──── F4 Kickoff ── F5 Bandeja y applets
                      │                     ├─ F6a/F6b Decoraciones [HIGH] ── F7 CSD [HIGH] ── F8 Min/Max
                      │                     │                                   └── F9 Menús de clic derecho
                      │                     └─ F12 Alt+Tab, OSD, bloqueo, KRunner
                      ├─ F2 Puente de configuración [HIGH] ── F11 Ajustes de Plasma
                      └─ F10 Reglas de ventana y snapping [HIGH] (tras F6–F8)
F13 Limpieza final
```

F3–F5 y F6–F8 pueden ir en paralelo (archivos distintos). Las fases del plugin (F6b, F7, F8 parte
C++, F10 parte C++) comparten `src/breezebars/`: **nunca dos a la vez**.

| Fase                                                      | Esfuerzo | Necesita reiniciar sesión       |
| :-------------------------------------------------------- | :------- | :------------------------------ |
| F0 Viabilidad y arquitectura                              | **high** | No                              |
| F1 Motor de temas de Plasma                               | medium   | No                              |
| F2 Puente de configuración BWM ↔ KDE                      | **high** | No                              |
| F3 Panel                                                  | medium   | No                              |
| F4 Kickoff                                                | medium   | No                              |
| F5 Bandeja del sistema y applets                          | medium   | No                              |
| F6a Auxiliar de decoraciones `bwm-decorator`              | **high** | No                              |
| F6b Plugin `breezebars` con las decoraciones del auxiliar | **high** | Sí                              |
| F7 Detección de CSD                                       | **high** | Sí                              |
| F8 Minimizar y maximizar como KWin                        | medium   | Sí (si toca el plugin)          |
| F9 Menús de clic derecho                                  | medium   | Sí (menú de la barra de título) |
| F10 Reglas de ventana y snapping                          | **high** | Sí                              |
| F11 Preferencias del sistema                              | medium   | No                              |
| F12 Alt+Tab, OSD, bloqueo, KRunner                        | medium   | No                              |
| F13 Limpieza, documentación y prueba completa             | medium   | No: no cambia el plugin; lista manual pendiente |
|                                                           |          |                                 |

---

## 4. Prompts

> **F0–F13 implementadas y limpieza final ejecutada.** El resultado comprobado y lo que aún
> necesita interacción física están en `docs/BREEZE_F13_RESULTS.md`; la arquitectura vigente
> está en `docs/BREEZE_ARCH.md`. Los prompts siguientes conservan el objetivo original, no son
> una certificación de equivalencia completa ni del cumplimiento de todas las pruebas manuales.

### F0 · Viabilidad y arquitectura — **[HIGH]**

```text
Fase 0 del plan docs/BREEZE_PLAN.md (léelo entero primero, incluida la sección 2 de reglas, y
también CLAUDE.md y BWM_CONTEXT.md §2.1, §2.4 y §3.10, §3.58, §3.106–3.108, §3.114–3.115).

Objetivo: decidir con pruebas la arquitectura del port de KDE Plasma 6 a BWM, antes de escribir
nada de la skin. No toques todavía la skin Breeze en uso.

1. Paquetes. Gentoo estable tiene Plasma 6.7.5 / Frameworks 6.29. Comprueba con `emerge -p` qué
   arrastran: kde-frameworks/ksvg, kde-plasma/libplasma, kde-plasma/plasma5support,
   kde-plasma/breeze, kde-plasma/kdecoration, kde-plasma/aurorae, kde-plasma/systemsettings,
   kde-plasma/plasma-workspace, kde-plasma/plasma-desktop, kde-plasma/kscreen,
   kde-plasma/plasma-nm, kde-plasma/bluedevil, kde-plasma/plasma-pa, kde-plasma/polkit-kde-agent,
   kde-plasma/kwin (sólo para saber qué trae; NO debe acabar ejecutándose). Ya se sabe que
   libplasma pide `kde-frameworks/kconfig[qml]`. Dime el conjunto mínimo y el comando exacto
   (`/etc/portage/package.use/bwm-plasma` + emerge) para que yo lo ejecute; espera mi
   confirmación. Avisa si alguno instala servicios que se arrancan solos (kded módulos, kwalletd,
   ksmserver, plasmashell autostart en /etc/xdg/autostart) y cómo evitar que choquen con BWM
   (un dueño para Notifications, polkit, StatusNotifierWatcher; ver §5 de CLAUDE.md).

2. Pruebas de concepto en archivos aparte (`qs -p` en el scratchpad o `zz_prueba.qml`, ventanas al
   workspace 9 con regla temporal), con Qt 6.11.2 y Quickshell 0.3.2:
   a. ¿Quickshell puede `import org.kde.ksvg` y pintar un `KSvg.FrameSvgItem` con
      `widgets/panel-background` del desktoptheme `default`/`breeze-dark` y de un tema de terceros
      descargado de la KDE Store (bájalo con knewstuff o a mano al scratchpad)?
   b. ¿`import org.kde.plasma.core` / `org.kde.plasma.components 3.0` / `org.kde.kirigami`
      funcionan dentro de Quickshell (Theme colors de PlasmaCore, PC3.Button, ToolTip, Menu)?
      ¿Cómo se fija el tema (plasmarc) y se recarga en vivo al cambiarlo?
   c. ¿Se puede cargar el QML de un plasmoide real (p. ej. org.kde.plasma.digitalclock) con un
      `Plasmoid` simulado, o hay que portar el QML quitando el attached `Plasmoid`? ¿Sirve
      `plasmawindowed`? (Ojo: el gestor de tareas y el pager dependen de
      org_kde_plasma_window_management de KWin, que Hyprland no tiene; Hyprland ofrece
      wlr-foreign-toplevel y su IPC.)
   d. Decoraciones: ¿se puede reutilizar kdecoration3 + el plugin Breeze fuera de KWin (bridge
      propio que renderice a un QImage en un proceso aparte y lo entregue al plugin de Hyprland),
      o es mejor reimplementar en C++/cairo la geometría de breezedecoration/breezebutton leyendo
      breezerc/kwinrc/kdeglobals, más un renderizador de temas Aurorae (SVG con librsvg)? Mide
      coste y riesgo (nunca Qt dentro del proceso de Hyprland).
   e. KCMs: ¿qué módulos de systemsettings funcionan con `kcmshell6` sin KWin ni plasmashell
      (kcm_colors, kcm_lookandfeel, kcm_desktoptheme, kcm_icons, kcm_cursortheme, kcm_fonts,
      kcm_kwindecoration, kcm_style, kcm_kwinrules, kcm_kscreen…)? ¿Qué archivos escriben y qué
      D-Bus esperan? `lookandfeeltool`/`plasma-apply-*` sin plasmashell.
   Clona en el scratchpad lo que necesites leer: invent.kde.org/plasma/{libplasma,plasma-desktop,
   plasma-workspace,kwin,breeze,aurorae,kdecoration,systemsettings} (tag v6.7.5) y
   frameworks/{ksvg,kirigami,knewstuff} (v6.29.0).

3. Resultado: `docs/BREEZE_ARCH.md` con lo comprobado (y lo no probado), la arquitectura elegida
   por pieza (panel, plasmoides, applets, decoraciones, CSD, ajustes, temas), las carpetas nuevas
   de la skin, el mapa de archivos de configuración de KDE que leeremos/escribiremos, los
   servicios que hay que impedir que arranquen, y cualquier cambio necesario en las fases
   siguientes de BREEZE_PLAN.md (edítalo si algo no es viable). Declara los paquetes elegidos en
   requirements.json y skin.json (regla 12). Capturas recortadas y borradas al acabar.
```

### F1 · Motor de temas de Plasma

```text
Fase 1 de docs/BREEZE_PLAN.md (lee el plan, la sección 2 y docs/BREEZE_ARCH.md de la fase 0).

Objetivo: un servicio único que dé a todo Breeze el tema de Plasma activo, leído de los archivos
reales de KDE, y que cambie en vivo. Sustituye la paleta fija Breeze Dark (`BREEZE_DARK_M3`,
`MaterialThemeLoader.applyBreezeColors`, `plasmaCommon/Breeze.qml` con colores a mano).

1. `modules/plasma/theme/PlasmaTheme.qml` (singleton, según la arquitectura de F0): esquema de
   color de `kdeglobals` (todos los grupos: Window, View, Button, Selection, Tooltip, Complementary,
   Header, WM) con KColFase 13 (última) de docs/BREEZE_PLAN.md (lee el plan y los commits de las fases anteriores).

2. Elimina lo que quede de la Breeze hecha a mano: `modules/ii/plasma*` sustituidos, colores fijos
   BREEZE_DARK_M3, `isPlasma` en módulos comunes que ya no hagan falta (`grep -rn isPlasma`),
   reglas de `rules.lua` movidas a la skin, partes de `quick-tile.py`/`toggle-minimize.py` que ya
   no use nadie (comprueba que default/Retro no las usan). Actualiza `parts`, requisitos y tests.
3. Cambio de skin (regla 16): default → Breeze → Retro → Breeze con apps abiertas y algo sonando;
   ventanas en su sitio, sin saltos de workspace, sin reinicios de apps, sin «Your config has
   errors» en las otras skins (regla 4).
4. Prueba con temas reales: un tema global completo de la KDE Store (colores + estilo de Plasma +
   Aurorae + iconos + cursor) instalado con «Obtener nuevos…» y aplicado desde Preferencias; mide
   qué parte del escritorio cambia y actualiza la compatibilidad estimada en `docs/SKINS.md`,
   README.md y README.es.md (sólo lo comprobado).
5. Documentación: §2.4 de BWM_CONTEXT reescrito, sección nueva en §3, `docs/BREEZE_ARCH.md` al día,
   tabla «Dónde tocar» de AGENTS.md/CLAUDE.md (iguales), THIRD_PARTY_NOTICES.md completo.
6. Lista final para mí de lo que requiere reiniciar sesión y qué comprobar a mano.orScheme/KConfig QML si F0 lo validó; desktoptheme de `plasmarc`; iconos;
   fuentes de `kdeglobals [General]`; vigilancia de cambios (KConfigWatcher o FileView).
   `Breeze.qml` pasa a ser una fachada sobre él para no romper los applets actuales.
7. Aplicador `config/hypr/skins/plasma/scripts/plasma-theme.py` con el formato de Plasma:
   `colors <esquema>` (equivalente a plasma-apply-colorscheme: copia grupos a kdeglobals, notifica
   `KGlobalSettings.notifyChange`; reutiliza o sustituye `skins/default/scripts/kde-shims/
   plasma-apply-colorscheme`), `desktoptheme <tema>`, `icons`, `cursor` (ojo regla 14: el cursor es
   común; lo manda BWM), `lookandfeel <id>` (lee `contents/defaults` del paquete y aplica cada
   parte, como lookandfeeltool), `list`. Si `plasma-apply-*` reales están instalados, úsalos.
8. Que el resto del escritorio siga el esquema activo: colores de Hyprland (`plasma_colors.lua`),
   GTK (`gtk-theme.py`, plantillas de matugen rellenadas desde el esquema en vez de BREEZE_DARK_M3
   en `bwm-theme-manager.py`), Qt (`QT_QPA_PLATFORMTHEME=kde` en Breeze si plasma-integration está,
   como default), kitty, Vesktop, Firefox/Pywalfox, Steam, Stremio, Omacalc: la misma tubería que hoy
   usa la paleta fija. Temas claros (Breeze Light) deben poner las apps en claro.
9. KNewStuff: comprobar que «Obtener nuevos…» (knewstuff, ya instalado) descarga esquemas,
   estilos de Plasma, decoraciones Aurorae y temas globales a las carpetas estándar.
10. Pruebas: Breeze Dark, Breeze Light y al menos un esquema y un estilo de Plasma de la KDE Store
   (en el scratchpad o vía knewstuff), cambiados en vivo sin reiniciar el shell. Pruebas unitarias
   del aplicador con un HOME temporal. Actualiza `defaultTheme`/`themes` de skin.json.
```

### F2 · Puente de configuración BWM ↔ KDE — **[HIGH]**

> Implementada: `docs/BREEZE_ARCH.md` §9 contiene el inventario, la autoridad por clave,
> el ciclo de vida y los límites del plugin actual. F6 completa ambos bancos y todos los botones;
> F10 completa las zonas de mosaico. F11 usa páginas comunes para pantallas/teclado/cursor.

```text
Fase 2 de docs/BREEZE_PLAN.md (lee el plan, su sección 2 y docs/BREEZE_ARCH.md).

Objetivo: que las herramientas de KDE (KCMs, apps KDE, temas globales) y BWM vean la misma
configuración, respetando la regla 14 (lo común manda desde BWM) y la 18 (lo del usuario manda).

1. Inventario de claves: para cada ajuste común de BWM (cursor y tamaño, Kelvin/luz nocturna,
   apps predeterminadas, distribución de teclado y repetición, pantallas/escala, fuentes si son de
   la skin, iconos, idioma, doble clic, animaciones, focus policy…) su equivalente en KDE
   (kcminputrc, kdeglobals, kwinrc, kxkbrc, mimeapps.list, kscreen, plasmarc…), quién manda y en
   qué dirección se sincroniza. Tabla en docs/BREEZE_ARCH.md.
2. `config/hypr/skins/plasma/scripts/kde-config-bridge.py`: `export` (BWM → archivos KDE, al
   entrar en Breeze y cuando cambie un ajuste común: hook en `bwm-theme-manager.py` y en los
   gestores comunes), `import` (KDE → BWM sólo para lo propio de Breeze), `watch` (demonio lanzado
   con `bwm_session.spawn()` sólo en Breeze: vigila carpetas con inotify, agrupa avisos, ignora
   sus propias escrituras, no hace bucles). Escrituras atómicas y conservando las claves que no
   conoce. Nunca toca `~/.config/bwm/user/*`.
3. Lo que KWin aplicaría en vivo (kwinrc: botones de la barra, acciones de doble clic, focus
   policy, placement, snap zones) se traduce a opciones de Hyprland/breezebars en un
   `skins/plasma/hypr/kwin.lua` generado o leído al cargar (`hyprctl reload` sólo una vez por
   cambio).
4. Al salir de Breeze, nada de lo exportado debe cambiar las otras skins (kdeglobals lo usan
   también default con plasma-integration y Retro: revisa `bwm_icons.write_kdeglobals`).
5. Pruebas unitarias con HOME temporal (ida, vuelta, conflictos, archivos ajenos conservados) y
   una prueba real cambiando el cursor desde BWM y comprobando kcminputrc.
```

### F3 · Panel de Plasma

> Implementada como port reducido de panel, tareas sólo-iconos y reloj: BREEZE_ARCH.md §10.
> Se eligió bar.plasma. Edición de widgets incluidos; alojar plasmoides externos y el catálogo
> completo «Añadir widgets» queda pendiente por las dependencias del anfitrión de F0.
> Insignias/progreso Unity y múltiples zonas horarias necesitan trabajo adicional.
> F4/F5 ya sustituyen Kickoff y applets; sus límites se detallan en la arquitectura y sus README.

```text
Fase 3 de docs/BREEZE_PLAN.md (lee el plan, su sección 2, docs/BREEZE_ARCH.md y el resultado de F1).

Objetivo: sustituir `modules/ii/bar/PlasmaBarContent.qml` por un port del panel de Plasma 6
pintado con el estilo de Plasma activo (KSvg `widgets/panel-background`, márgenes y sombras del
tema), con su comportamiento.

1. Lee en invent.kde.org/plasma/plasma-desktop (v6.7.5) `containments/panel/` y en
   plasma-workspace/libplasma la PanelView y `shell/contents/views/Panel.qml` del shell
   org.kde.plasma.desktop: grosor, flotante (desacople al maximizar, que hoy hace
   `PlasmaPanelState.qml`), visibilidad (siempre, ocultar auto, esquivar ventanas), alineación,
   longitud, borde (abajo/arriba/izquierda/derecha), opacidad adaptable.
2. Disposición de plasmoides como la predeterminada de Plasma 6: Kickoff, pager (opcional),
   gestor de tareas solo-iconos (org.kde.plasma.icontasks), bandeja, reloj digital, mostrar
   escritorio. Porta el QML de `applets/taskmanager` (plasma-desktop) y `applets/digital-clock`
   (plasma-workspace) sustituyendo `TaskManager.TasksModel` por un modelo sobre Hyprland
   (`HyprlandData`/toplevels de Quickshell): agrupación por app, ancladas, miniaturas al pasar el
   ratón (reutiliza ScreencopyView de `plasmaTaskMenu`), progreso/insignias si se puede (Unity
   LauncherEntry por D-Bus), arrastrar para reordenar, clic central = nueva instancia, rueda.
3. Configuración del panel en el formato de Plasma si F0 lo decidió (`plasma-org.kde.plasma.
   desktop-appletsrc`) o en `bar.plasma` de BWM; mantener `bar.workspaces.shown` y lo común (regla
   14). Modo edición del panel (añadir/quitar/mover plasmoides, «Añadir widgets») si es viable; si
   no, deja anotado en el plan qué falta.
4. Se carga con un `Loader` desde `IllogicalImpulseFamily.qml` sólo en Breeze; el QML nuevo vive en
   `modules/plasma/panel/`. La reserva de espacio del panel (exclusive zone) debe coincidir con lo
   que usan `quick-tile.py`, `placement.lua` y `bwm_windows.traditional_box`.
5. Pruebas con dos estilos de Plasma distintos y con el panel en los cuatro bordes; capturas
   recortadas y borradas. Avisa de que hace falta `--restart-shell` para cargar el Loader.
```

### F4 · Kickoff

```text
Fase 4 de docs/BREEZE_PLAN.md (lee el plan, su sección 2, docs/BREEZE_ARCH.md y F1/F3).

Objetivo: sustituir `modules/ii/plasmaKickoff/PlasmaKickoff.qml` (925 líneas hechas a mano) por un
port de Kickoff de Plasma 6.7.5 (invent.kde.org/plasma/plasma-desktop, `applets/kickoff/`), con el
estilo de Plasma activo.

1. Copia su QML (Header, LeaveButtons, ApplicationsPage, FavoritesPage, PlacesPage, búsqueda,
   KickoffGridView/ListView, rejilla/lista configurables) y cambia sólo los modelos que dependen de
   `org.kde.plasma.private.kicker` y KRunner: aplicaciones por categorías de los `.desktop`
   (AppSearch de BWM o KService si F0 lo permite), favoritos (formato de Plasma si es posible),
   recientes (archivos y apps), lugares, y la búsqueda (AppSearch + archivos + acciones). Avatar y
   nombre de usuario como en Plasma.
2. Botones de sesión: todos a `config/hypr/scripts/bwm-power` (regla común, §3.95). Bloquear =
   `bwm-power lock`.
3. Se abre con Super (como hoy, keybinds-manager), clic en el botón del panel y Alt+F1. Menú
   contextual de las apps (Añadir a favoritos, Editar aplicación si existe kmenuedit, Desinstalar
   no: avisa como en Retro).
4. Pruebas en `qs -p` aparte: búsqueda, navegación completa con teclado (como en Plasma), lanzar una
   app con un stub. Captura recortada.
```

### F5 · Bandeja del sistema y applets

> Implementada con vistas originales y adaptadores (BREEZE_ARCH.md §11). Bluetooth, historial y
> portapapeles son ports reducidos; se conserva un único servidor BWM. Quedan las opciones avanzadas
> indicadas en la arquitectura (OBEX, jobs, inline reply, DND programado, edición/QR, agenda y perfiles).
> No se ejecutaron acciones sobre redes/dispositivos reales; interacción probada con datos simulados.

```text
Fase 5 de docs/BREEZE_PLAN.md (lee el plan, su sección 2, docs/BREEZE_ARCH.md, F1 y F3).

Objetivo: portar la bandeja del sistema de Plasma (plasma-workspace `applets/systemtray/`) y sus
applets, con el estilo de Plasma, sustituyendo los applets hechos a mano de `modules/ii/plasma*`.

1. Bandeja: elementos StatusNotifierItem (Quickshell SystemTray), popup expandido con la lista de
   applets ocultos/visibles, configuración de visibilidad por elemento.
2. Applets, portando el QML original y cambiando sólo la capa de datos:
   - Red: plasma-nm (`applet/`) sobre el servicio `Network` + nmcli de BWM (o el plugin QML de
     plasma-nm si se instala y funciona sin KDE, según F0).
   - Bluetooth: bluedevil (`src/applet/`) sobre bluez de Quickshell.
   - Audio: plasma-pa (`applet/`) sobre PipeWire de Quickshell (o el plugin QML de plasma-pa).
   - Notificaciones: plasma-workspace `applets/notifications/` y los popups de notificación del
     shell; servidor `org.freedesktop.Notifications` = el de BWM (un solo dueño, §5 de CLAUDE.md).
   - Reproductor (mediacontroller), batería y brillo (si hay), portapapeles (Klipper → cliphist de
     BWM), calendario del reloj digital, «No molestar».
   Red/Bluetooth/audio son comunes entre skins (regla 14): sólo cambia la interfaz.
3. Elimina los módulos antiguos cuando cada sustituto funcione (plasmaNetwork, plasmaBluetooth,
   plasmaAudio, plasmaNotifications, plasmaCalendar) y actualiza `parts`.
4. Pruebas en `qs -p`, capturas recortadas, sin cambiar la red/Bluetooth reales del usuario.
```

### F6a · Auxiliar de decoraciones `bwm-decorator` — **[HIGH]**

```text
Fase 6a de docs/BREEZE_PLAN.md (lee el plan, su sección 2 y docs/BREEZE_ARCH.md entero, sobre todo
la prueba d y la fila «Decoraciones» de §3; reglas 1, 4 y 15 de CLAUDE.md).

Objetivo: un proceso auxiliar que dibuje las decoraciones reales de KDE para el plugin de Hyprland,
probado sin Hyprland.

1. `src/bwm-decorator/` (C++20, Qt 6, KDecoration3; CMake o Makefile con instalación atómica a
   ~/.local/share/bwm/bin o al repo, como decidas y documentes). Parte de la prueba de la fase 0
   (`src/bwm-decorator/poc-fase0.cpp`) y sigue kwin v6.7.5
   `src/kcms/decoration/declarative-plugin/preview{bridge,client,settings}.cpp` y
   `src/decorations/{decorationbridge,decoratedwindow,settings,decorationpalette}.cpp`).
   Recuerda `deco->apply(deco->nextState()->clone())` tras cada cambio de estado.
2. Lee `kwinrc [org.kde.kdecoration2]` (library, theme, ButtonsOnLeft/Right, BorderSize,
   CloseOnDoubleClickOnMenu) y el esquema de color (paleta como `decorationpalette.cpp`, con caché);
   recarga en vivo con KConfigWatcher / `KGlobalSettings.notifyChange`.
3. Protocolo con el plugin por un socket Unix en `$XDG_RUNTIME_DIR/bwm-decorator.sock` (binario y
   versionado): el plugin envía alta/baja de ventana, tamaño, escala, activa, título, clase, icono,
   maximizada (H/V), bordes de pantalla adyacentes, todos los escritorios, encima/debajo,
   y eventos de puntero sobre la decoración; el auxiliar responde bordes, `resizeOnlyBorders`,
   radios, la imagen (memfd compartido + rectángulos dañados), la sombra (imagen + padding una vez
   por tema) y las peticiones (cerrar, maximizar con botón, minimizar, menú en un rect, tooltip,
   encima/debajo, todos los escritorios, enrollar). Diséñalo para varias ventanas a la vez y para
   la escala de cada monitor.
4. Iconos de ventana: `QIcon::fromTheme` a partir de la clase/`.desktop` (como hace hoy Breeze).
5. Lanzado con `bwm_session.spawn()` sólo en Breeze (autostart y `bwm-theme-manager.py`), una
   instancia (candado), reinicio si muere.
6. Pruebas: cliente de prueba en Python que habla el protocolo y guarda PNG (Breeze Dark/Light,
   Aurorae de terceros, botones en otra disposición, hover, clic → petición, cambio de esquema en
   vivo, escala 1,5). Declara el auxiliar en requirements.json (tipo build, como hyprbars-plasma).
```

### F6b · Plugin `breezebars` con las decoraciones del auxiliar — **[HIGH]**

```text
Fase 6b de docs/BREEZE_PLAN.md (lee el plan, su sección 2, docs/BREEZE_ARCH.md, el protocolo de
F6a, y BWM_CONTEXT §3.8, §3.10, §3.11, §3.52, §3.58, §3.107, §3.108; reglas 1, 4 y 17 de CLAUDE.md).

Objetivo: barras de título idénticas a KWin con el tema activo, dibujadas por `bwm-decorator`.

1. Mueve el plugin de `src/hyprbars` a `src/breezebars` (Makefile con -fno-gnu-unique y `make
   install` atómico a `config/hypr/plugins/breezebars.so`; actualiza requirements.json,
   `bwm-requirements.py`, `appearance.lua`, `install.sh`, skin.json). Sigue registrándose como
   `breezebars` (`plugin:breezebars:*`, regla 4). No toques `src/omarchy-titlebars`.
2. El plugin pasa a ser pegamento: conexión no bloqueante al socket (nunca bloquear el hilo de
   Hyprland), reserva de bordes, textura desde el memfd sólo en los rectángulos dañados, sombra,
   reenvío de puntero, ejecución de peticiones (cerrar, maximizar/restaurar con el botón usado,
   minimizar con el módulo de F8 o `toggle-minimize.py` hasta entonces, menú de ventana por IPC
   a Quickshell para F9), redimensionar desde los bordes que diga la decoración. Durante un
   redimensionado, estira la última imagen hasta que llegue la nueva. Sin auxiliar: barra plana
   con título (código cairo actual) y relanzarlo.
3. Acciones de doble clic/rueda de la barra de `kwinrc [Windows]` y el snapping actual siguen
   funcionando (regla 17).
4. Pruebas unitarias de lo que se pueda fuera de Hyprland. El plugin sólo se prueba tras volver a
   iniciar sesión: cuando esté compilado e instalado, pídemelo con la lista exacta de qué comprobar
   (Breeze claro/oscuro, un Aurorae de la KDE Store, botones en otra disposición, doble clic,
   hover, tooltip, redimensionar, dos monitores con escala distinta).
```

### F7 · Detección de apps con botones propios (CSD) — **[HIGH]**

Implementación en §12 de la arquitectura: negociación real, ack/commit y hints X11 asíncronos;
JSON/Lua comparten marco y dirección+PID con geometría. `no_bar=false` vuelve al automático.
La traducción de NoBorder se conserva para F10. Matriz pendiente en `BREEZE_CSD_RESULTS.md`:
no dar F7 por validada visualmente antes de reiniciar sesión en Breeze.

```text
Fase 7 de docs/BREEZE_PLAN.md (lee el plan, su sección 2, BWM_CONTEXT §3.10 y el estado de F6).

Objetivo: que `breezebars` ponga barra exactamente donde la pondría KWin y nunca dos barras, sin
listas de clases.

1. Estudia cómo decide KWin (invent.kde.org/plasma/kwin v6.7.5: `src/xdgshellwindow.cpp`,
   `xdgdecorationv1`, `serverdecorationmanager`/org_kde_kwin_server_decoration, `x11window.cpp`
   con _MOTIF_WM_HINTS y _GTK_FRAME_EXTENTS) y cómo lo resuelve Hyprland (su implementación de
   xdg-decoration en el código de Hyprland 0.56.2 y en `src/breezebars/CSDDetect.cpp`).
2. Reglas: Wayland — si la app no habla xdg-decoration ni kde-server-decoration → CSD (libadwaita,
   Firefox con CSD); si pide client-side → CSD; si pide server-side o acepta el modo preferido →
   barra. Prefiere server-side como KWin (responder `server_side` a quien no impone modo).
   XWayland — _MOTIF_WM_HINTS decorations=0 o _GTK_FRAME_EXTENTS → CSD. Reaccionar a cambios de
   modo durante la vida de la ventana (apps que cambian de CSD a SSD al salir de pantalla
   completa, Chromium/Electron con su opción de «usar barra del sistema»).
3. Overrides: reglas de KWin («Sin barra de título ni marco» en kwinrulesrc, que F10 traducirá) y
   `breezebars:no_bar`. Mantén `hyprctl hyprbars-csd` (o renómbralo `breezebars-csd`) con el motivo
   de cada decisión.
4. Que el resto de BWM use la misma respuesta: `bwm_windows.traditional_box`, `placement.lua` y
   `quick-tile.py` deben contar la barra sólo si de verdad la hay (hoy `placement.lua` la cuenta
   siempre, §3.115).
5. Pruebas: tabla de apps reales (kitty, Firefox, Nautilus/Dolphin, Steam, Vesktop, Stremio,
   Signal, Krita, Claude, VS Code/Codium, Kate en flatpak, una app Qt Widgets, xterm/xeyes en
   XWayland) con lo esperado y lo obtenido, tras reiniciar sesión.
```

### F8 · Minimizar y maximizar como KWin

```text
Fase 8 de docs/BREEZE_PLAN.md (lee el plan, su sección 2, BWM_CONTEXT §3.2, §3.18, §3.113–3.114).

Objetivo: minimizar, maximizar y restaurar con la semántica de KWin, en un solo sitio.

1. Lee en kwin v6.7.5 `src/window.cpp` (maximize, MaximizeMode vertical/horizontal/full, restore
   geometry, quick tile vs maximize), `src/useractions.cpp` y los atajos por defecto de
   `src/kwinbindings.cpp` (Meta+PgUp maximizar, Meta+PgDown minimizar, Alt+F3 menú, Alt+F4…).
2. Un módulo de la skin (`config/hypr/skins/plasma/scripts/kwin-window.py` o Lua en
   `skins/plasma/hypr/`, lo que encaje con F0) que sustituya las partes de `quick-tile.py
   maximize` y `toggle-minimize.py` usadas por Breeze: maximizado real al área útil (con la barra
   de título dentro, el panel visible, sin bordes redondeados, como hoy `plasma-maximized-square`),
   maximizado vertical/horizontal (clic central/derecho en el botón maximizar, como KWin),
   restaurar a la geometría exacta, minimizar a `special:minimized` con la etiqueta común
   `omarchy-minimized-from-<n>` (formato común, §3.114: no lo cambies), animación de minimizar
   hacia el icono del panel si Hyprland lo permite, «Mostrar escritorio».
3. Que el panel (F3), el plugin (botones de F6), Alt+Tab y Alt+Enter usen ese módulo. Atajos sólo
   con `keybinds-manager.py` y `"skins": ["plasma"]`.
4. Pruebas con ventanas de prueba en el workspace 9 (minimizar/restaurar con geometría, maximizar
   y restaurar, vertical/horizontal, dos monitores), pruebas unitarias del cálculo.
```

### F9 · Menús de clic derecho

```text
Fase 9 de docs/BREEZE_PLAN.md (lee el plan, su sección 2 y lo hecho en F3–F8).

Objetivo: los mismos menús contextuales que Plasma, con su estilo.

1. Menú de ventana de KWin (barra de título clic derecho, botón de menú, Alt+F3): porta la
   estructura de `src/useractions.cpp` de kwin v6.7.5 — Mover, Redimensionar, Mantener encima,
   Mantener debajo, Pantalla completa, Enrollar (si se implementa), Sin borde, Mover al escritorio
   (workspaces), Mover a la pantalla, Más acciones → Configurar ajustes especiales de la ventana/
   de la aplicación (abre el editor de reglas de F10), Cerrar. Quickshell lo pinta (PlasmaComponents
   Menu con el tema activo); el plugin lo pide por IPC (`qs -c ii ipc call plasmaWindowMenu open
   <address> <x> <y>`).
2. Menú del gestor de tareas: sustituye `plasmaTaskMenu` por el de `applets/taskmanager/
   ContextMenu.qml` (acciones del .desktop, recientes, Anclar, Mover a, Más, Cerrar).
3. Menú del escritorio (clic derecho en el fondo) de la containment folder/desktop de Plasma:
   Añadir widgets (si existe), Cambiar fondo, Configurar el escritorio y el fondo, Abrir terminal,
   Bloquear, Salir… adaptado a BWM. Menú del panel: Añadir widgets, Modo de edición, Mostrar
   alternativas.
4. Pruebas en `qs -p` y, para el de la barra de título, tras reiniciar sesión.
```

### F10 · Reglas de ventana y snapping — **[HIGH]**

Implementación F10 en arquitectura §13. Ctrl+flechas se conserva por decisión del usuario;
Meta+T abre un editor de mosaico reducido con el formato de KWin. Cobertura/omisiones de reglas
en `skins/plasma/scripts/KWIN_RULES.md`. No equivalencia completa del RuleBook ni del efecto
editor de KWin. Plugin compilado e instalado; validación con ratón pendiente de reiniciar sesión:
`docs/BREEZE_F10_CHECKLIST.md`.

```text
Fase 10 de docs/BREEZE_PLAN.md (lee el plan, su sección 2, reglas 4 y 17 de CLAUDE.md, BWM_CONTEXT
§3.4, §3.8, §3.58, §3.115; y lo hecho en F6–F8).

Objetivo: reglas de ventana y snapping como KWin.

A. Reglas:
1. Lee kwin v6.7.5 `src/rules.cpp`, `src/rulebooksettings*` y `kcms/rules/` (formato de
   kwinrulesrc). Traduce kwinrulesrc a `hl.window_rule` al cargar Hyprland en Breeze (módulo
   `skins/plasma/hypr/kwinrules.lua` o generado por el puente de F2): coincidencia por clase,
   título, rol y tipo; propiedades posición, tamaño, escritorio, pantalla, encima/debajo, sin
   barra, opacidad, minimizado, maximizado, pantalla completa, foco… con «aplicar inicialmente»,
   «forzar», «recordar». Lo que no tenga equivalente, documentado.
2. Sustituye `plasma-float-all`, `plasma-maximized-square`/`plasma-snapped-square` de `rules.lua`
   por reglas de la skin; `placement.lua` sigue la política de colocación de kwinrc (Smart por
   defecto) leyendo `[Windows] Placement`.
3. Editor de reglas: si kcm_kwinrules funciona con kcmshell6 (F0), úsalo; si no, una página propia
   con su misma estructura.

B. Snapping:
4. Lee kwin `src/quicktiling`, `src/tiles/` (Plasma 6: tiling personalizado con Meta+T y Shift al
   arrastrar), `src/workspace.cpp` (snap zones: bordes de pantalla, de ventanas y centro,
   `BorderSnapZone`, `WindowSnapZone`, `CenterSnapZone` de kwinrc) y el efecto `outline`.
5. Reescribe el snapping de Breeze: quick tiling a mitades y cuartos (arrastre y Meta+flechas;
   hoy son Ctrl+flechas, §3.3: pregúntame si se pasan a los de KWin), mosaico personalizado de
   Plasma 6 con su editor si es viable, imán a bordes de pantalla y de otras ventanas al mover,
   previsualización con el estilo del outline de KWin (sustituye a `SnapHelper.hpp` y el aspecto
   de §3.58), redimensionar juntas las ventanas en mosaico adyacentes. Respeta la regla 17 (monitor
   del puntero, workspace antes de la geometría, `window.float enable/disable`).
6. Pruebas unitarias de geometría (amplía `tests/test_quick_tile.py`) y, tras reiniciar sesión,
   una lista concreta de comprobaciones con ratón para mí.
```

### F11 · Preferencias del sistema

```text
Fase 11 de docs/BREEZE_PLAN.md (lee el plan, su sección 2, docs/BREEZE_ARCH.md, F2 y
BWM_CONTEXT §3.14, §3.39, §3.73, §3.98).

Objetivo: que Breeze tenga «Preferencias del sistema» como Plasma, que respete la configuración de
BWM y sin páginas inútiles.

1. Estructura y aspecto de systemsettings de Plasma 6.7.5 (invent.kde.org/plasma/systemsettings:
   barra lateral por categorías, búsqueda, cabecera, «Cambios resaltados»), pintado con el estilo
   de Plasma activo, sustituyendo `plasmaSettings.qml`.
2. Páginas:
   - Apariencia y estilo: Colores, Estilo de Plasma, Decoraciones de ventana, Tema global, Iconos,
     Cursores (común: escribe en BWM), Fuentes, Estilo de aplicaciones. Usar los KCMs reales con
     kcmshell6/KCMUtils embebidos donde F0 comprobó que funcionan (incluido «Obtener nuevos…»);
     si no, una página propia que use `plasma-theme.py` de F1.
   - Espacio de trabajo: Comportamiento (doble clic, animaciones), Gestión de ventanas (reglas de
     F10, comportamiento: foco, colocación, barras de título), Atajos, Inicio automático,
     Pantallas, Escritorios virtuales = workspaces de BWM.
   - Sistema, red, Bluetooth, sonido, energía/inactividad (IdleConfig común), apps predeterminadas,
     Acerca de: las páginas comunes de BWM (no duplicar su lógica).
   Quitar lo que no aplica en BWM (Actividades, efectos de KWin, Plasma Vault, KDE Connect si no
   está, etc.) y lo que hoy sobra en Breeze (revisa cada página actual de plasmaSettings.qml y
   explica en el commit qué se quita y por qué).
3. Todo cambio pasa por el puente de F2 para que BWM y los archivos de KDE coincidan. Super+I y
   `open-settings.sh [página]` siguen funcionando (`SETTINGS_PAGE`).
4. Pruebas: cada página carga en `qs -p`/kcmshell6 en el workspace 9 sin errores; captura recortada
   de dos páginas; un cambio de esquema de color desde la página se ve en vivo.
```

### F12 · Alt+Tab, OSD, bloqueo y KRunner

```text
Fase 12 de docs/BREEZE_PLAN.md (lee el plan, su sección 2, F1 y BWM_CONTEXT §3.17, §3.20, §3.97).

Objetivo: el resto de interfaces de Plasma, con el tema global activo.

1. Alt+Tab: porta el cambiador «Rejilla de miniaturas» (el predeterminado de Plasma 6) y, si es
   barato, los otros de kwin `src/tabbox/switchers/`; que el tema global elija el cambiador
   (`kwinrc [TabBox] LayoutName`). Conserva el comportamiento correcto de §3.20 (foco al soltar
   Alt, pulsaciones acumuladas) y sustituye `altTab/PlasmaSwitcher.qml` dentro de la carpeta de la
   skin.
2. OSD de volumen/brillo/cambio de pantalla: el de plasma-workspace (`osd/`) con el tema.
3. Bloqueo: porta el `lockscreen/` del paquete look-and-feel Breeze (plasma-workspace
   `lookandfeel/`) y usa el del tema global si trae uno; mantiene `LockContext` de BWM (PAM,
   huella). Sustituye `plasmaLock/`.
4. KRunner (Alt+Espacio en Plasma): sólo si F0 vio que krunner/milou funcionan sin plasmashell; si
   no, un port de la interfaz sobre AppSearch + calculadora + comandos. Atajo con
   keybinds-manager y `"skins": ["plasma"]`; pregúntame antes si choca con uno existente.
5. Polkit: polkit-kde-agent si se instaló (un solo agente por sesión, §5 de CLAUDE.md) o el de BWM
   con aspecto Breeze.
6. Pruebas en `qs -p` con copias cuyas acciones reales estén sustituidas (comprueba con grep).
```

### F13 · Limpieza, documentación y prueba completa

> Limpieza y pruebas de integración terminadas: véase `docs/BREEZE_F13_RESULTS.md`.
> No se modifica el plugin en F13; el reinicio de mantenimiento del shell ya se hizo.
> Pendientes de comprobación física detallados al final del informe, sin cerrar sesión automáticamente.

```text
Fase 13 (última) de docs/BREEZE_PLAN.md (lee el plan y los commits de las fases anteriores).

1. Elimina lo que quede de la Breeze hecha a mano: `modules/ii/plasma*` sustituidos, colores fijos
   BREEZE_DARK_M3, `isPlasma` en módulos comunes que ya no hagan falta (`grep -rn isPlasma`),
   reglas de `rules.lua` movidas a la skin, partes de `quick-tile.py`/`toggle-minimize.py` que ya
   no use nadie (comprueba que default/Retro no las usan). Actualiza `parts`, requisitos y tests.
2. Cambio de skin (regla 16): default → Breeze → Retro → Breeze con apps abiertas y algo sonando;
   ventanas en su sitio, sin saltos de workspace, sin reinicios de apps, sin «Your config has
   errors» en las otras skins (regla 4).
3. Prueba con temas reales: un tema global completo de la KDE Store (colores + estilo de Plasma +
   Aurorae + iconos + cursor) instalado con «Obtener nuevos…» y aplicado desde Preferencias; mide
   qué parte del escritorio cambia y actualiza la compatibilidad estimada en `docs/SKINS.md`,
   README.md y README.es.md (sólo lo comprobado).
4. Documentación: §2.4 de BWM_CONTEXT reescrito, sección nueva en §3, `docs/BREEZE_ARCH.md` al día,
   tabla «Dónde tocar» de AGENTS.md/CLAUDE.md (iguales), THIRD_PARTY_NOTICES.md completo.
5. Lista final para mí de lo que requiere reiniciar sesión y qué comprobar a mano.
```

---

## 5. Notas

- **Atajos:** el plan no añade ninguno salvo los de KWin que sustituyen a los actuales de Breeze; cada
  fase debe preguntar antes de cambiar uno (p. ej. Ctrl+flechas → Meta+flechas).
- **Dolphin:** `todo.md` tiene una idea aparte (Dolphin en Breeze con favoritos sincronizados con
  Nautilus). No forma parte de este plan; puede hacerse después de F11.
- **Si F0 descubre que algo no es viable** (p. ej. libplasma no carga en Quickshell), la fase 0 debe
  reescribir las fases afectadas de este documento antes de seguir.
