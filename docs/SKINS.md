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

## Skins incluidas

| id | Skin | Imita | Tema por defecto | Ecosistema de temas |
| :--- | :--- | :--- | :--- | :--- |
| `default` | Default | end-4 / illogical-impulse | Material You **dinámico** (matugen desde el fondo) | Plantillas de matugen, fondos |
| `retro` | Retro | Omarchy 4 (`quattro`) | Paleta **dinámica** con formato de Omarchy; 23 temas **estáticos** de Omarchy | `colors.toml` de Omarchy, plugins del shell de Omarchy (Ajustes → Temas / Plugins) |
| `plasma` | KDE Plasma | Plasma 6 Breeze Dark | Breeze Dark **estático** | Esquemas de color y temas globales de Plasma (objetivo, pendiente) |

*Dinámico* = la paleta se genera del fondo de pantalla y cambia con él. *Estático* = colores fijos
de un tema; cambiar el fondo no los toca.

## Qué declara una skin

Cada skin tiene un manifiesto JSON. Las de la release viven en `config/hypr/skins/<id>.json`; las
de la comunidad se buscarán en `~/.local/share/bwm/skins/<id>.json`. El comprobador
(`config/hypr/scripts/bwm-requirements.py`), el instalador y la bienvenida los leen:

```json
{
  "id": "plasma",
  "name": "KDE Plasma",
  "imitates": "KDE Plasma 6 (Breeze Dark)",
  "upstream": "https://kde.org/plasma-desktop/",
  "description": "Qué reproduce de su escritorio original.",
  "preview": "assets/skin-previews/kde-plasma-6.png",
  "defaultTheme": { "mode": "static", "name": "Breeze Dark", "description": "…" },
  "themes": { "builtIn": "Temas incluidos.", "compatibility": "Qué temas externos acepta." },
  "requires": ["hyprpolkitagent", "breeze-icons", "hyprbars-plasma"],
  "recommends": ["qt6ct", "networkmanager"],
  "catalog": { }
}
```

* `requires` / `recommends`: ids del catálogo de `config/hypr/skins/requirements.json` (paquetes por
  distribución y cómo se comprueba cada uno). Una skin puede añadir los suyos en `catalog`.
* La skin aparece **en verde** en la bienvenida cuando el núcleo y todos sus `requires` están.
  `bwm skin <id>` se niega a activarla si falta algo.
* Tipos de comprobación: `cmd` (`any`/`all`), `version` (`cmd`, `regex`, `min`, `tested`), `qml`,
  `qtplugin`, `python`, `pymodule`, `path`, `font`, `pkgconfig`, `hyprland-plugin`.

## Cómo se construye una skin hoy

Una skin toca varias piezas; las tres actuales sirven de ejemplo:

1. **Gestor de skins:** `config/hypr/scripts/bwm-theme-manager.py` (`THEMES`, `apply_theme`), perfil
   de Quickshell `config/illogical-impulse/config-<id>.json`.
2. **Qué carga Quickshell en esa skin:** `config/quickshell/ii/panelFamilies/IllogicalImpulseFamily.qml`
   (`extraCondition`).
3. **Colores de Hyprland y de las apps:** `config/hypr/modules/theme.lua`, plantillas de
   `config/matugen/templates/` (o las de Omarchy en Retro).
4. **Atajos propios:** `config/hypr/keybinds.json` vía `keybinds-manager.py`.
5. **Manifiesto** en `config/hypr/skins/<id>.json` y captura en `assets/skin-previews/`.

Instalar skins de terceros sin tocar el repositorio (formato de paquete, firma, sandbox) está por
diseñar; cuando exista se documentará aquí y la bienvenida podrá activarlas.
