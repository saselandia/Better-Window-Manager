# Adaptador de reglas y mosaico de KWin — F10

Fuentes consultadas: KWin **v6.7.5**, `src/rules.cpp`, `src/rules.h`, `src/rulesettings.kcfg`,
`src/rulebooksettings{,base}.*`, `src/kcms/rules/{kcmrules,rulebookmodel,rulesmodel}.cpp`,
`src/workspace.cpp`, `src/tiles/` y `src/plugins/tileseditor/`. Los adaptadores Python/Lua son
implementaciones BWM independientes; no contienen C++ de KWin ni cargan Qt en Hyprland.

## Archivos y ciclo

`kwin_rules.py` lee **kwinrulesrc original**: `[General] rules` ordena grupos UUID; si falta usa
`count` y grupos 1..N. Respeta Enabled y las coincidencias Exacta/Contiene/Expresión regular.
Cada propiedad se resuelve por orden: la primera con modo distinto de 0 bloquea las posteriores,
también «No afectar» (1). Una condición no representable nunca se convierte en «todas las apps».
Los modos no soportados bloquean esa propiedad y aparecen en el diagnóstico.

`kde-config-bridge.py` genera `~/.local/state/bwm/plasma/kwinrules.lua` y un informe
`kwinrules-report.json`. La skin carga ese Lua con `hl.window_rule` **antes** de
`~/.config/bwm/user/hyprland.lua`. Efectos dinámicos nativos: decoración, opacidad compuesta
activa/inactiva, foco, tamaños límite y exclusión de capturas. No hay scripts ni valores KDE
evaluados como código. Sólo se construyen nombres y campos de una lista admitida.

El **mismo** vigilante F2 observa kwinrulesrc y kwinrc, agrupa escrituras durante 300 ms y hace
como máximo una recarga por lote cuando cambian los archivos Lua generados. Mientras hay una
escritura pendiente no ejecuta las reglas. En reposo consulta ventanas cada 250 ms si hay reglas
(o etiquetas anteriores que limpiar). No consulta nada por reglas con la lista vacía. Si la
sesión agota la cuota inotify, mantiene vigilancia por firmas con el mismo intervalo.

Las ventanas nuevas reciben una marca al mapearse en Breeze; el puente consume la marca una
sola vez. Así Apply/Remember no recolocan las que ya estaban abiertas al cambiar de skin o al
reiniciar el vigilante. No se repite Apply en un reload. Esto también significa que no se aplica
inicialmente a ventanas que preceden a la instalación/carga del adaptador. El arranque compila
los archivos antes de la recarga inicial del plugin. Se comprueban dirección **y PID**, también
justo antes de los cambios y al reutilizar direcciones. Un cambio de skin cancela órdenes tardías.

## Cobertura

| Dato / propiedad | Soporte |
| --- | --- |
| Clase/appId y título | Exacta, contiene y regex (motor Python; se rechazan expresiones incompatibles con Python, no se relajan). Sin listas de apps. |
| Rol | `WM_WINDOW_ROLE` que expone XWayland; vacío para Wayland. Sin metadata del plugin no coincide. |
| Tipo / transient | Máscara NET de X11; normal/diálogo en toplevels Wayland según padre. No incluye superficies Plasma/layer-shell que no sean ventanas. |
| WM_CLASS completo (instancia+clase), clientmachine | No expuestos por Hyprland: se omite la regla completa y se informa. |
| Position / Size | Marco completo, no sólo contenido; se descuentan los bordes reales de F7. Apply (3), Force (2), Remember (4). No se fuerza geometría dentro de fullscreen. |
| Desktops | UUID de `[Desktops] Id_N` o número de workspace; una ventana sólo puede pertenecer a uno. Si la lista contiene varios se toma el de menor número resoluble. |
| Screen | Índice enlazado a descripción estable en `kwin-screens.json`, orden inicial de BWM; desconectado = no se mueve. Si también hay Desktops, manda éste: el workspace de Hyprland determina la pantalla. No se usan DP-N. |
| MaximizeVert / MaximizeHoriz | F8, modo por ejes, restauración conservada; Force mantiene el eje en el área útil aun al redimensionar. |
| Minimize / Fullscreen | Formato común de BWM y dispatchers explícitos; no se arrastran otros workspaces especiales. |
| NoBorder | Force → efecto nativo decorate=false (o true); Apply/Remember → estado de ventana modificable del menú. CSD sigue la negociación: nunca se fuerza otra barra. |
| OpacityActive / OpacityInactive | Force, como ForceRule de KWin; se combinan por propiedad antes de crear el efecto nativo. |
| AcceptFocus, MinSize, MaxSize | Force; usa no_focus y límites nativos. |
| ExcludeFromCapture | Force nativo; Apply/Remember usa el estado del menú. |
| Above / Below | Sin estado persistente equivalente en Hyprland; no se simula con subidas ocasionales de orden. |
| ApplyNow / ForceTemporarily | No implementados. No se consumen ni se eliminan entradas del usuario para fingirlo. |
| Actividades, reglas de efecto, sombreado, agrupar KWin, atajos por ventana, etc. | Sin equivalente; diagnóstico. Placement por regla no se traduce; Placement global de kwinrc sigue en placement.lua. |

Remember sólo escribe claves de estado soportadas, al cerrar una ventana o salir de Breeze,
con la última geometría normal observada (no el tamaño temporal de fullscreen/maximizado/encaje).
Conserva comentarios y claves ajenas. Si el KCM cambió la propiedad tras observarla, no la pisa.
Las escrituras son atómicas y verifican cambios concurrentes. No se escribe bwm/user.

Las propiedades mantenidas por seguimiento tienen una convergencia aproximada de 250 ms;
no son una sustitución interna del RuleBook de KWin. Un Force de geometría puede prevalecer sobre
un dispatcher puntual. Para que una regla en el Lua del usuario excluya esas ventanas del puente:

```lua
-- En tu hyprland.lua, cargado el último; BWM no crea ni edita este archivo.
hl.window_rule({ name = "mis-reglas", match = { class = "^mi-app$" },
                 tag = "bwm-ignore-kwin-rules" })
```

Ese opt-out desactiva **todo** el adaptador en las ventanas coincidentes, también las órdenes
ya encoladas. Los efectos nativos generados se cargan antes que las reglas de texto del usuario.
No hay un reemplazo de kwinrulesrc por un formato BWM.

## Editor y mosaico

Se usa `kcmshell6 kcm_kwinrules`, instalado y probado sin ejecutar KWin. El menú de F9 lo abre.
La selección automática de una ventana y «Detectar propiedades» del KCM dependen de D-Bus KWin:
no están disponibles; hay que escoger clase/título a mano. No se reclama `org.kde.KWin` para
simularlo. El KCM conserva opciones aún no soportadas, que aparecen en kwinrules-report.json.

Meta+T abre el editor de mosaico reducido; Ctrl+flechas se conserva por decisión del usuario.
El formato de mosaico y la asociación de UUID de pantalla se explican en el README de
`config/quickshell/ii/modules/plasma/tiling`. No hay editor del efecto original sin KWin.
El redimensionado conjunto ajusta vecinos encajados en vivo; no guarda proporciones nuevas
al mover un borde ni restaura todos los grupos de QuickRootTile de KWin.

Comprobaciones manuales tras reiniciar: `docs/BREEZE_F10_CHECKLIST.md`. Las pruebas automáticas
usan configuración XDG temporal y geometría/datos simulados; no mueven ventanas del usuario.
