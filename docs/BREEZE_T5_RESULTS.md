# Breeze III — T5: atajos globales de KDE coherentes con BWM

Fecha: 2026-11-26/27. Plan: [BREEZE_PLAN_V3.md](BREEZE_PLAN_V3.md) §T5. Contexto: `BWM_CONTEXT.md` §391.

## Qué se ha hecho

| Pieza | Dónde |
| :--- | :--- |
| Servicio `org.kde.kglobalaccel` con la biblioteca original kglobalacceld 6.7.5 y un backend «bwm» | `src/bwm-kglobalaccel` (README) |
| Supervisor (compilar, instalar, arrancar sólo en Breeze, parar) | `config/hypr/skins/plasma/scripts/kde-shortcuts.py` |
| Binds de KDE tras cada recarga, sólo en Breeze, antes del Lua del usuario | `config/hypr/modules/kde_shortcuts.lua` (estado en `~/.local/state/bwm/kde-shortcuts.lua`) |
| Arranque al iniciar sesión en Breeze y al entrar; parada al salir | `autostart.sh`, `bwm-theme-manager.py` |
| Preferencias → Atajos (`kcm_keys`) habilitado; «BWM — Atajos» sigue siendo el editor de BWM | `settings-profile/kdeglobals`, `settings-native.sh` (`globalshortcuts`) |
| Requisitos | `bwm-kglobalaccel`, `bwm-kglobalaccel-build` en `requirements.json`; tabla regenerada |

Por qué el demonio propio y no `kglobalacceld`: el binario original sale sin hacer nada en Wayland
(«los atajos los ejecuta kwin_wayland») y su único backend es X11. KWin incrusta la biblioteca
`libKGlobalAccelD` con un backend propio; BWM hace lo mismo con uno que habla con Hyprland.

## Reglas de convivencia y cómo se cumplen

| Regla del plan | Implementación |
| :--- | :--- |
| `keybinds.json` y los helpers siguen siendo la fuente | El demonio lee los binds del Hyprland en marcha y no escribe `keybinds.json`, `user_binds.lua` ni el Lua del usuario |
| Una combinación de BWM no se asigna a KDE: queda en conflicto | Cada bind de BWM es una acción del componente «BWM» con esa tecla. Si una acción de KDE la tenía o la registra después, se le quita (`setForeignShortcutKeys`), queda sin asignar y se avisa. `--status` la lista en `conflicts` |
| Asignar en Preferencias una tecla de BWM se rechaza | `kcm_keys` muestra el conflicto con «BWM» como con cualquier componente. Si aun así se reasigna, el demonio devuelve la tecla a BWM y avisa: «Los atajos de BWM se cambian en Preferencias → BWM — Atajos» |
| Módulo Lua propio, sólo en Breeze | `modules/kde_shortcuts.lua`; sin binds de KDE fuera de Breeze (comprobado con las tres skins) |
| No duplicar lo que BWM ya resuelve | Kickoff (Alt+F1), KRunner, volumen, Mostrar escritorio…: la tecla es de BWM, la acción de KDE queda sin asignar. Nunca dos binds activos para la misma tecla (si BWM empieza a usarla, el nuestro se desactiva) |
| `kcm_keys`: KDE editables, BWM sólo lectura o con enlace | Componente «BWM» visible; sus cambios se deshacen con aviso que remite a «BWM — Atajos» |

## Pruebas

| Prueba | Resultado |
| :--- | :--- |
| `test-keymap` (Qt ↔ Hyprland, 21 casos: letras con Mayús, Print, F1, Espacio, `=`/`.`, multimedia, flechas, Backtab, solo-modificador, vuelta Hyprland→Qt→Hyprland) | 21/21 |
| `check-daemon.py` (CTest, D-Bus privado, `hyprctl` falso, cliente con el framework KGlobalAccel real) | Pasa: atajo libre enlazado (pulsar+soltar) y disparado; Alt+F1 de BWM retirado a KDE y en conflicto; edición de «bwm» deshecha con aviso; tecla que BWM empieza a usar: KDE la pierde y el bind sólo se desactiva; parada borra estado; `kglobalshortcutsrc` escrito |
| `check-nested.py` (Hyprland 0.56.2 real, desechable, salida headless temporal) | 5/5: binds creados y disparados por `exec`, recreados tras `reload` por el módulo, retirada pulsar+soltar **sin caída**, tecla tomada por BWM conserva el bind de BWM, parada limpia |
| `tests/test_kde_shortcuts.py` (módulo Lua con `hl` simulado en las tres skins, supervisor) | 7/7 |
| Suites de skins, arranque de Breeze, cambio de skin, Preferencias R3/T2 | OK (una expectativa de arranque actualizada con el nuevo servicio) |
| `Hyprland --verify-config` | `config ok` |
| Preferencias (`settings-native.sh --list`) | Lista `kcm_keys` y `kcm_bwm_shortcuts` |

## Incidente durante la prueba en la sesión

Con el demonio arrancado en la sesión diaria, un cliente de prueba registró un atajo y Hyprland cayó
(SIGSEGV, `~/.cache/hyprland/hyprlandCrashReport3197.txt`, pila en el `hyprctl eval` del demonio). La
sesión volvió en **modo seguro**. Causa, reproducida en un Hyprland anidado:

- `hl.bind` devuelve un objeto `HL.Keybind`. En `LuaKeybind.cpp` de 0.56.2, `getKeybindFromUserdata`
  devuelve `std::optional<SP<SKeybind>>`, siempre lleno, y los métodos lo desreferencian aunque el bind
  ya no exista.
- `:remove()` borra todos los binds de esa tecla: el de pulsar se llevó el de soltar, y llamar
  `:remove()` al de soltar desreferenció un puntero nulo.

Corrección: retirar con `hl.unbind("MODS + tecla")` y llamar métodos sólo a referencias cuyo `tostring()`
(seguro) no sea `HL.Keybind(expired)`. Comprobado en anidado: el script viejo lo tumba, el nuevo no.
La prueba con `hyprctl` falso no podía ver el fallo; por eso existe `check-nested.py`. Trampa añadida a
AGENTS/CLAUDE. Se borraron el archivo de estado y el componente de prueba.

Antes de la caída, en la sesión: 100 capturas, 96 teclas de BWM registradas, 6 binds de KDE (Touchpad y
Dolphin con Meta+E, libre porque el Meta+E de BWM está desactivado en `keybinds.json`). El host nativo
registró sus componentes (`bwm-plasma-host`, `plasmashell`, `kmix`) al aparecer el servicio.

## Pendiente

- Nuevo login comprobado el 2026-11-27: Hyprland 0.56.2 con breezebars y bwm-plasma-desktops cargados, sin configerrors; bwm-kglobalaccel PID 3532 es el dueño único y no informa error. Esto cierra el reinicio pendiente; no sustituye la aceptación con teclado de los puntos siguientes.
- Aceptación en la sesión: atajo de un widget del panel nativo, apps KDE reales (Spectacle, Konsole)
  pulsados con el teclado, conflicto visto en `kcm_keys`, cambio de skin sin binds de KDE residuales.
- Límites (README): sin atajos de sólo modificadores, secuencias de varias teclas sin probar, teclas
  desplazadas guardadas sin Mayús.
