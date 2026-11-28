# Breeze III — T9: respaldo sin duplicados, regresión completa y aceptación final

Fecha: 2026-11-28. Plan: [BREEZE_PLAN_V3.md](BREEZE_PLAN_V3.md).

## 1. Retirada del respaldo duplicado en Quickshell

Acordado con el usuario: retirar el port QML duplicado que sólo existía como respaldo de
`bwm-plasma-host` y, si el host nativo no arranca o se desactiva (`bar.plasma.nativeHost=false`),
caer a la barra común (`Bar`) y avisos comunes (`NotificationPopup`) de BWM.

### Retirado (180 archivos, ~15 090 líneas QML/JS + 5 pruebas obsoletas)

- `config/quickshell/ii/modules/plasma/applets/` (55 archivos, 7 699 líneas)
- `config/quickshell/ii/modules/plasma/kickoff/` (93 archivos, 4 287 líneas)
- `config/quickshell/ii/modules/plasma/panel/` (19 archivos, 2 225 líneas)
- `config/quickshell/ii/modules/plasma/tray/` (13 archivos, 836 líneas)
- `config/quickshell/ii/modules/plasma/menus/DesktopCatcher.qml`
- Pruebas obsoletas retiradas: `tests/test_plasma_kickoff_ui.py`, `tests/test_plasma_panel.py`,
  `tests/test_plasma_panel_native.py`, `tests/test_plasma_task_input.py`, `tests/test_plasma_tray.py`.
- Referencias limpiadas en `IllogicalImpulseFamily.qml`, `modules/plasma/menus/qmldir`,
  `skins/plasma/scripts/plasma-theme.py` y `skins/plasma/skin.json`.

### Conservado (piezas usadas con el host nativo activo o páginas sólo-BWM)

- `modules/plasma/theme/` (`PlasmaTheme`) y `modules/plasma/runtime/` (`InterfaceTheme`)
- `modules/plasma/lock/` (pantalla de bloqueo), `modules/plasma/osd/` (OSD),
  `modules/plasma/switcher/` (Alt+Tab), `modules/plasma/skinPicker/` (`Alt+T`),
  `modules/plasma/tiling/` (`Outline` + `TileEditor` `Meta+T`),
  `modules/plasma/session/` (proxy IPC `SessionScreen`),
  `modules/plasma/menus/` (`MenuHost` + `WindowMenu` para `Alt+F3` y barra de título de `breezebars`),
  `modules/plasma/settings/` + `plasmaSettings.qml` (usado por `open-settings.sh` para páginas
  exclusivas de BWM y respaldo si falta `systemsettings`).

## 2. Batería completa de regresión

| Suite | Resultado |
| :--- | :--- |
| Python Breeze / Plasma / decorador / `breezebars` / KCM / T2–T8 (22 archivos `tests/test_*.py`) | **149 tests ejecutados, 0 fallos** (16 omitidos por sesión/display; 51,66 s) |
| CTest `build/bwm-plasma-host-tests` (`BUILD_TESTING=ON`) | **17/17 PASS** (56,61 s) |
| CTest `build/bwm-kglobalaccel` (T5) | **2/2 PASS** (1,33 s) |
| CTest `src/bwm-systemsettings/build` (KCMs nativos y gestor) | **3/3 PASS** (4,48 s) |
| Hyprland anidado T8 (`check-focus-safety.py --binary check-t8-session.py`) | **PASS** (4/4 modos cargados sin errores QML, `screenedges` activo, limpieza verificada) |
| Matriz real entre skins (`check-skin-lifecycle.py --run`) | **PASS** (`retro` 4,02 s, `plasma` 5,22 s, `default` 5,07 s, `plasma` 4,17 s; `0` ventanas perdidas/movidas, reservas idénticas; corregido bloqueo por pipes heredados en `check-skin-lifecycle.py`; informe `build/bwm-plasma-host-tests/t9-skin-lifecycle.json`) |
| `docs/REQUIREMENTS.md` | Regenerado desde `requirements.json` y `skin.json` |

## 3. Límites conocidos que quedan fuera de Breeze III

- **PowerDevil:** catalogado en `requirements.json`, no recomendado ni activado automáticamente
  hasta coordinar su autoridad de DPMS/suspensión/tapa con `BwmIdle` y `bwm-power` (T6).
  Consecuencia medida en T7: widgets de la tienda que importan
  `org.kde.plasma.private.brightnesscontrolplugin` (como `KDE Control Station`) no cargan.
- **KWin exclusivo:** efectos del compositor KWin (blur personalizado, cubo, scripts de KWin) y
  barrera física de puntero (`EdgeBarrier` en píxeles) no corren sobre Hyprland.
- **Decoraciones C++ de la KDE Store:** al igual que en Plasma, KNS descarga código fuente y
  requiere compilar/instalar el plugin KDecoration3 por separado (`bwm-decorator` sí los carga
  una vez compilados, comprobado con BreezeChameleon y Klassy en T7).
- **Bandejas restauradas:** una bandeja preexistente con Klipper/teclado activados conserva la
  elección previa del usuario (T6).

## 4. Aceptación física final (pendiente del usuario)

Para dar por cerrada la aceptación física de T1–T8 con los binarios finales cargados:
- Notificaciones nativas (T1), Preferencias sin páginas rotas (T2), fondo por monitor (T3).
- Atajos KDE en `kcm_keys` y atajo de un widget (T5).
- Zoom numérico (`Meta+KP_Add`/`KP_Subtract`), `Super+.` y portal KDE en app GTK (T6).
- Vista general (`Meta+W` + búsqueda Milou + arrastrar ventana), Rejilla (`Meta+G`), Ventanas
  expuestas (`Ctrl+F9`/`F10`), esquina superior izquierda en ambos monitores y
  **Preferencias → Bordes de la pantalla** (T8).
