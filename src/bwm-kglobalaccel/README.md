# bwm-kglobalaccel — atajos globales de KDE en Breeze (Breeze III, T5)

Servicio `org.kde.kglobalaccel` de la skin Breeze sobre Hyprland. Hace que funcionen los atajos
globales de KDE (el atajo de un widget en su configuración, los de las apps KDE, los
`X-KDE-Shortcuts` de los `.desktop`, los que se editan en Preferencias → Atajos) **sin cambiar ni
sustituir ningún atajo de BWM**.

## Cómo funciona

- Incrusta la biblioteca **original** `libKGlobalAccelD` de kglobalacceld 6.7.5 (`KGlobalAccelD`,
  la misma que KWin carga en Wayland). El registro, el formato de `kglobalshortcutsrc`, la interfaz
  D-Bus y el lanzamiento de apps son los de KDE; no se copia ni se modifica su código.
- `platform.cpp` es el backend de plataforma `bwm` (`KGlobalAccelInterface`, plugin estático): la
  biblioteca le dice qué combinaciones capturar (`grabKey`) y él le devuelve las pulsaciones
  (`keyEvent`), como hace el filtro de entrada de KWin.
- `controller.cpp`:
  - lee los binds que BWM tiene en el Hyprland en marcha (`hyprctl -j binds`: `keybinds.json`, los
    fijos de `keybinds-manager.py`, el Lua del usuario) y los registra como componente **«bwm»**.
    Así KDE ve esas teclas como ocupadas; si una acción de KDE ya tenía una de ellas, se le quita
    (queda sin asignar, en conflicto) y se avisa. Un cambio a un atajo de «BWM» hecho desde
    Preferencias se deshace: los de BWM se cambian en Preferencias → BWM — Atajos;
  - convierte cada tecla de KDE que BWM no usa en dos binds de Hyprland (pulsar y soltar) que
    ejecutan `bwm-kglobalaccel --trigger press|release <tecla>`; los escribe en
    `~/.local/state/bwm/kde-shortcuts.lua` y los aplica en caliente con `hyprctl eval`;
  - se vuelve a sincronizar al cambiar las capturas, tras cada recarga de Hyprland
    (`configreloaded`) y tras cada escritura de `kglobalshortcutsrc` (kglobalacceld 6.7 permite dos
    acciones con la misma tecla, así que el registro de una app nueva sólo se nota ahí).
- `config/hypr/modules/kde_shortcuts.lua` vuelve a crear esos binds tras cada recarga, sólo en
  Breeze y antes del Lua del usuario. Fuera de Breeze el demonio no corre y no hay binds de KDE.
- Las acciones que BWM ya resuelve (Kickoff, Mostrar escritorio, KRunner, volumen…) no se duplican:
  su tecla es de BWM y la acción de KDE queda sin asignar.

## Uso

```
python3 config/hypr/skins/plasma/scripts/kde-shortcuts.py build|install|start|stop|status
~/.local/share/bwm/bin/bwm-kglobalaccel --status     # JSON: binds, conflictos, avisos
```

`autostart.sh` y `bwm-theme-manager.py` lo arrancan al entrar en Breeze (antes de
`bwm-plasma-host`, que registra los atajos de sus widgets) y lo paran al salir: el demonio retira
sus binds y su archivo de estado y kglobalacceld guarda `kglobalshortcutsrc`.

## Pruebas

- `ctest --test-dir build/bwm-kglobalaccel` (`BUILD_TESTING=ON`): `test-keymap` (conversión Qt ↔
  Hyprland) y `check-daemon.py` (D-Bus privado, `hyprctl` falso, cliente KDE real `test-client`).
- `python3 src/bwm-kglobalaccel/check-nested.py --binary … --client …`: contra un **Hyprland real
  desechable** sobre una salida headless temporal. Es obligatorio tras tocar el Lua generado.

## Trampa: objetos keybind de Hyprland 0.56.2

`:remove()` o `:set_enabled()` sobre un bind ya retirado tumba Hyprland: `LuaKeybind.cpp` comprueba
un `std::optional<SP<SKeybind>>` (siempre lleno) y desreferencia el puntero nulo. Quitar un bind quita
todos los de la misma tecla, también el de soltar. La primera versión llamaba `:remove()` a los dos y
dejó la sesión del usuario en modo seguro (§391). Ahora se retira con `hl.unbind("MODS + tecla")` y
sólo se desactivan referencias cuyo `tostring()` no es `HL.Keybind(expired)`.

## Límites

- Atajos de sólo modificadores (Meta solo) no se convierten: Super es de BWM.
- Secuencias de varias teclas: cada tecla se captura por separado (como en KWin), sin probar.
- Una tecla «desplazada» guardada sin Mayús (p. ej. `Meta+!`) no coincide con el bind de Hyprland.
- Tras una recarga en la que BWM empieza a usar una tecla de KDE, durante unos milisegundos (hasta
  que el demonio sincroniza) hay dos binds para esa tecla.

Licencia: GPL-2.0-or-later. Enlaza `libKGlobalAccelD` (LGPL-2.0-or-later, KDE) sin modificarla.
