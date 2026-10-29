# Skins de BWM

Cada skin es **una carpeta con un `skin.json`**. Ese archivo es todo lo que BWM necesita saber de
ella: lo leen el gestor de skins, la colocación de ventanas, el comprobador de requisitos, el
instalador y la bienvenida (a través de `scripts/bwm_skins.py`). Para crear una skin no hay que
tocar el código del gestor.

```
config/hypr/skins/
├── README.md            ← esta guía
├── requirements.json    ← núcleo (lo que necesitan todas) + catálogo de requisitos por distro
├── _template/skin.json  ← plantilla comentada para empezar una skin nueva
├── default/skin.json    ← Default (end-4 / illogical-impulse)   · ventanas: tiling
├── retro/skin.json      ← Retro (Omarchy 4)                     · ventanas: tiling
└── plasma/skin.json     ← KDE Plasma 6                          · ventanas: traditional
```

Las skins de la comunidad van en `~/.local/share/bwm/skins/<id>/skin.json` (mismo formato). Las
carpetas que empiezan por `_` no son skins.

## La variable de ventanas: `windows`

Lo primero que decide una skin es cómo gestiona las ventanas:

| `"windows"` | Qué es | Ejemplos |
| :--- | :--- | :--- |
| `"tiling"` | **Mosaico**: las ventanas se reparten la pantalla sin solaparse | Default, Retro (Hyprland, i3, Sway, Omarchy) |
| `"traditional"` | **WM tradicional**: cada ventana flota con su barra de título y se solapan | KDE Plasma (Windows, macOS, GNOME) |

Una skin `"traditional"` añade su bloque `"traditional"`:

```json
"windows": "traditional",
"traditional": {
  "titlebar": 30,                              // alto de la barra de título que pone encima de cada ventana
  "panel": { "edge": "bottom", "size": 44 },   // su panel: borde (top/bottom/left/right) y grosor
  "edgeMargin": 10,                            // separación de las ventanas con los bordes del monitor
  "gap": 10                                    // hueco entre ventanas vecinas
}
```

Con eso BWM resuelve solo el paso entre familias, para cualquier skin: al entrar en una
tradicional, cada ventana flota **en el mismo sitio** que tenía en mosaico (con su barra, el margen
y el hueco); al volver a una de mosaico, se rehace el mosaico. Hyprland recibe la variable en
`modules/theme.lua` (`windows = "…"`) y `modules/rules.lua` hace flotar todo en las tradicionales.

## Campos de `skin.json`

| Campo | Para qué |
| :--- | :--- |
| `id`, `name`, `imitates`, `upstream`, `description`, `preview` | Identidad: qué escritorio reproduce, enlace al original y captura (`assets/skin-previews/`) |
| `windows` (+ `traditional`) | Mosaico o WM tradicional (arriba) |
| `palette` | Motor de colores: `matugen` (dinámico desde el fondo), `omarchy` (`colors.toml` de Omarchy) o `breeze` (paleta fija de KDE) |
| `defaultTheme`, `themes` | Tema por defecto (dinámico/estático), temas incluidos y qué temas del original acepta |
| `look` | Fondo por defecto (de `~/Pictures/Wallpapers`), redondeo, borde, huecos del mosaico, btop |
| `bar` | Alto, posición (`bottom`), esquinas y workspaces de la barra |
| `fonts` | Fuentes de la skin (las de cada tema de Retro mandan sobre éstas) |
| `parts` | **Mapa de archivos** de la skin: QML, Hyprland, colores y scripts (rutas desde la raíz del repo; un test comprueba que existen) |
| `requires`, `recommends`, `catalog` | Requisitos (ids del catálogo de `requirements.json`, o propios en `catalog`) |

## Crear una skin, paso a paso

1. Copia `_template/` a `<tu-id>/` y rellena `skin.json`. Empieza por `windows`.
2. Elige `palette` según el ecosistema de temas del escritorio que imitas: la finalidad de BWM es
   que los temas de ese escritorio funcionen tal cual.
3. Interfaz (Quickshell): crea sus módulos en su propia carpeta (`quickshell/ii/modules/ii/<tu-id>*`)
   y cárgalos sólo en tu skin desde `quickshell/ii/panelFamilies/IllogicalImpulseFamily.qml`
   (`extraCondition`). Añade esas rutas a `parts.quickshell`.
4. Colores de Hyprland y apps: reutiliza el motor de tu `palette` (plantillas en `matugen/templates`
   o `hypr/omarchy/themed`) y anota los archivos en `parts.colors`/`parts.hyprland`.
5. Atajos propios: `hypr/keybinds.json` vía `scripts/keybinds-manager.py`.
6. Captura en `assets/skin-previews/` y requisitos en `requires`.
7. Comprueba: `bwm skins` (aparece con su tipo de ventanas), `bwm check --skin <tu-id>` y
   `python3 -m unittest tests/test_skins.py`. Actívala con `bwm skin <tu-id>`.

Más contexto (qué se conserva entre skins, compatibilidad con temas, estructura modular):
`docs/SKINS.md`.
