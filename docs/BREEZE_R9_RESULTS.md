# R9 — Aceptación final y regresión de las tres skins

> Estado actualizado: **2026-11-26 — R9 cerrado (con límites técnicos explícitos).**
> El usuario inició nueva sesión con los binarios finales cargados (`breezebars.so` §376,
> `omarchy-titlebars.so` §377, `bwm-plasma-host` §362–370), sin coredumps nuevos, y confirmó las
> pruebas físicas/visuales diarias.

## 1. Binarios y servicios realmente cargados en la sesión diaria

Verificado directamente sobre la nueva sesión Wayland activa (2026-11-26, skin `plasma`,
Hyprland 0.56.2, Quickshell `ii`, 0 coredumps):

| Componente | Estado real observado | Evidencia |
| :--- | :--- | :--- |
| `config/hypr/plugins/breezebars.so` | **Cargado y activo** (incluye parche de salida limpia §376) | SHA-256 `6c750f1a5859a1fd6419c0335a3722399f8b6a608572fee66771729ef5fc5183`; `hyprctl -j plugin list` activo; `breezebars-shadows` v2 activo (`shm: true`, `applied: 6`, XWayland `:0`); `breezebars-scale` v1 activo (`enabled: true`, `starts: 12`, `observedFrames: 458`) |
| `config/hypr/plugins/omarchy-titlebars.so` | **Instalado** (§377, se carga bajo demanda en workspaces flotantes de Retro) | SHA-256 `36d0e4f4892b2d1d79bd966815186cdac72f1d4425e01e8524dd7680fa125800` |
| `~/.local/share/bwm/bin/bwm-plasma-host` | **Instalado y activo (`ready: true`)** | SHA-256 `96cb79414481d07418a1f345fa4b05ea1889ee811bb801bb88bbd511c4accb06`; `plasma-host.py status` → `running: true`, `ready: true`; 2 `bwm-r4-native-policy` + 2 `bwm-r5-desktop`, reservas `[0,0,0,48]` en LG 4K y MSI 1440p; `bwm-plasma-desktops` cargado en Hyprland |
| `~/.local/share/bwm/bin/bwm-decorator` | **Instalado y escuchando** | SHA-256 `083d3ddd3dea7969aa0e1c08ed60ba70348528867c48f2f9ce3fdc24779826ea`; proceso único activo |
| `src/bwm-systemsettings` (KCMs nativos) | **Instalados y descubiertos** | `QT_QPA_PLATFORM=offscreen settings-native.sh --list` descubre los 10 KCM BWM (`kcm_bwm_apps`, `cursor`, `effects`, `energy`, `nightlight`, `screens`, `shortcuts`, `startup`, `windows`, `workspaces`) + `kcm_colors`/`kcm_desktoptheme`/`kcm_lookandfeel`, y mantiene restringido `kcm_kwin_effects` |
| Quickshell (`qs -c ii`) | **Instancia única** | `quickshell -n -c ii` único proceso activo, sin paneles duplicados |
| Servicios auxiliares Breeze | **Dueño único por servicio** | `polkit-kde-authentication-agent-1` (1), `kde-config-bridge.py watch` (1), `bwm-decorator` (1), `launcher-entries.py` (1) |
| Configuración de Hyprland y estabilidad | **Sin errores ni coredumps** | `hyprctl configerrors` vacío; `coredumpctl list` sin caídas nuevas tras el reinicio de sesión |
| Requisitos (`bwm-requirements.py`) | **Todo listo** | `bwm-requirements.py check --skin plasma`: núcleo + Breeze completos; `docs/REQUIREMENTS.md` regenerado |

---

## 2. Suite de regresión ejecutada en R9

### 2.1 Repetición del 2026-11-25 (host nativo activo)

| Bloque | Resultado | Notas |
| :--- | :--- | :--- |
| Python completo (`unittest discover -s tests`) | **794 OK**, 85 omitidas (QML sin activar) | Corregidas dos pruebas: `test_breeze_startup` no contemplaba `native-desktops.py startup` (§255) ni `plasma-host.py start` (§362); `test_gtk_settings_ini` dejaba `XDG_RUNTIME_DIR` apuntando a una carpeta borrada |
| QML + C++ Breeze (17 módulos, `BWM_RUN_QML_TESTS=1`) | **119 OK**, 2 omitidas (pasada final) | Caída de Kicker 6.7.5 en el arnés de Kickoff localizada y esquivada (§375): 14/14 ejecuciones sin caída ni reintento |
| CTest `src/bwm-systemsettings` | **3/3 OK** | `installed-decoration-option` fallaba con `QT_QPA_PLATFORMTHEME=kde` heredado y escribía el `~/.config/breezerc` real; corregido (§374) |
| CTest `build/bwm-plasma-host` (sin `native-*`) | **8/8 OK** | |
| Matriz de skins en la sesión real | **PASS** | `check-skin-lifecycle.py` (§372) |
| Aislamiento de configuración | **Corregido** | `Config.blockWrites` no frenaba `writeAdapter()` en Quickshell 0.3.2: las pruebas QML escribían el `config.json` real (§374) |

### 2.2 Ampliación R9 del 2026-11-25 (escalas fraccionarias, matriz de temas y documentación)

| Bloque | Resultado | Notas |
| :--- | :--- | :--- |
| Escalas fraccionarias + bordes + modo edición nativo en Hyprland (`src/bwm-plasma-host/check-edit-mode-session.py --fractional-scale`) | **24/24 pasos PASS** | Salida headless temporal `BWMR5-*` (monitores físicos inalterados) a **1.25×**, **1.5×** y **1.6×**: panel inferior, `PanelConfiguration`, flechas Set Position, traslado a borde izquierdo con reserva lateral, popup de alternativas, `WidgetExplorer`, `DesktopEditMode` y limpieza |
| Matriz de temas/estilos/temas globales en XDG aislado (`plasma-theme.py`) | **6/6 pasos OK** | `BreezeLight` → `BreezeDark` → estilo SVG `Sweet` → `default` → tema global `Sweet` (esquema + SVG + `candy-icons` + `kvantum` + Aurorae `__aurorae__svg__Sweet-Dark`) → rollback a `org.kde.breezedark.desktop`, sin tocar `~/.config` real |
| Decoraciones (`test_bwm_decorator.py`) + KCMs (`ctest src/bwm-systemsettings/build`) | **15/15 OK** + **3/3 OK** | Breeze claro/oscuro, Aurorae de terceros, sombras, escala, cambios en vivo y KCM nativos |
| R1/R3/host (`test_r3_native_settings`, `test_r1_local_validation`, `test_special_workspace_restore`, `test_native_plasma_host`, `bwm-r1-validate.py` sólo lectura) | **40 OK** (1 omitida opcional) + preflight OK | Contratos de Magic, KCM nativos, readiness por PID vivo y acceso IPC |
| Documentación R9 | **Actualizada** | `docs/REQUIREMENTS.md` regenerado, `docs/BREEZE_ARCH.md` §18 y `modules/plasma/{panel,kickoff,tray,settings}/README.md` actualizados con el estado de Breeze II |


| Bloque | Tipo | Resultado | Alcance |
| :--- | :--- | :--- | :--- |
| Regresión Python multi-skin (34 archivos) | Unitaria / API / Lua | **293/293 OK** (1 omitido sin QML) | R1/Magic Alt+S (`test_r1_local_validation`, `test_special_workspace_restore`), cambio de skin (`test_skin_switch`, `test_skin_runtime`, `test_skins`), KWin/Breeze (`test_kwin_window`, `test_kwin_rules`, `test_kwin_tiles`, `test_quick_tile`, `test_minimize`, `test_csd_detection`, `test_plasma_placement`, `test_plasma_theme`, `test_plasma_panel`, `test_plasma_shadow_policy`, `test_kde_config_bridge`, `test_r3_native_settings`, `test_r7_animation_measurement`, `test_r7_effects`), default (`test_default_colors`, `test_default_palette_apply`), Retro (`test_retro_keybindings`, `test_retro_menu_catalog`, `test_retro_settings`, `test_retro_wallpapers`, `test_nautilus_appearance`, `test_nautilus_plugins`), común (`test_autostart`, `test_bookmarks_sync`, `test_file_manager`, `test_user_config`, `test_power_session`, `test_shell_conflicts`, `test_steam_restart`) |
| Suite QML + C++ de Breeze (8 archivos, `BWM_RUN_QML_TESTS=1`) | Interfaz aislada `qs -p` + compilación C++ + protocolo | **68/68 OK** | `test_r7_effects` (8), `test_plasma_interfaces` (8), `test_plasma_menus_ui` (5), `test_plasma_panel_native` (4), `test_plasma_task_input` (1), `test_plasma_tray` (20), `test_breezebars` (4), `test_bwm_decorator` (15, claro/oscuro/Aurorae/hicolor/sombras) |
| CTest (`src/bwm-systemsettings/build`) | C++ / KCM real | **3/3 OK** | `native-kcm`, `manager-kcm`, `installed-decoration-option` |

**Total ejecutado en R9: 364 pruebas, 0 fallos.** Sin archivos temporales (`zz_*`) residuales ni cambios en las preferencias del usuario.

---

## 3. Estado por objetivo del plan (`docs/BREEZE_PLAN_V2.md`, R0–R8)

| Fase | Objetivo | Estado | Evidencia / límite explícito |
| :--- | :--- | :--- | :--- |
| **R0** | Auditoría, línea base y contención de captura | **Verificado** | `docs/BREEZE_R0_RESULTS.md`, `BREEZE_R0_REFERENCE.md/.json`, `BREEZE_RECOVERY.md` |
| **R1** | Magic (Alt+S) común y restauración especial en las 3 skins | **Verificado** | `docs/BREEZE_R1_RESULTS.md`, `test_r1_local_validation`, `test_special_workspace_restore`, `test_skin_switch` en verde |
| **R2–R3** | `systemsettings` real con KCMs BWM, opciones nativas de terceros y transacciones | **Verificado (con límites)** | `open-settings.sh` (Super+I y menús) lanza ahora `systemsettings` real vía `settings-native.sh` con los 10 KCM BWM (`kcm_bwm_*`), `kcm_kwindecoration` y alias cortos (`display`, `effects`, `autostart`, etc.); `plasmaSettings.qml` queda para páginas sólo-BWM (`background`, `bar`, `services`, `general`, `style`, `about`, `windowrules`), `BWM_SETTINGS_HOST=legacy` o respaldo sin `systemsettings`. CTest 3/3, `test_r3_native_settings` 11/11, `test_r7_effects` 8/8 |
| **R4–R5** | Anfitrión nativo `bwm-plasma-host`, edición original de panel/escritorio, plasmoides externos | **Verificado (con límites)** | `bwm-plasma-host --session` activo por defecto en Breeze en ambas salidas (LG 4K + MSI 1440p, reservas `[0,0,0,48]`, sin duplicados de Quickshell). Validado en compositor desechable (edición, explorador, 20 ciclos con entrada Wayland, 6/6 QtTest, 32 casos UI, área útil normal/ASan), en Hyprland real a escalas fraccionarias 1.25/1.5/1.6 con traslado a borde izquierdo (24/24 pasos PASS) y matriz de skins real (§372). El usuario ha completado la verificación física diaria en la nueva sesión (2026-11-26, 0 coredumps). Límite: backends KWin no implementados sobre Hyprland no están certificados para todos los plasmoides externos |
| **R6** | Sombras KDE originales, esquinas del contenido y desenfoque KWin | **Verificado (con límites)** | `docs/BREEZE_R6_RESULTS.md`: `breezebars.so` (§376) y `bwm-decorator` cargados en la sesión diaria; sombras en los 4 bordes/esquinas medidas sobre fondo `#dcdcdc` (0 px de hueco, contorno 1 px, degradado 34/56/46/44 px); `blur_on_request` y `SquareTop` verificados en vivo; desenfoque en panel, Kickoff, bandeja, notificaciones, OSD, cambiador (y `ThemeHost`), menús, tooltips, `PanelEditor` y KRunner. Límite: sin `_KDE_NET_WM_SHADOW` X11 ni dmabuf; contorno de esquinas de Breeze a escala 2 limitado por el radio entero de Hyprland |
| **R7** | Animaciones predeterminadas de Plasma 6.7.5 y sus ajustes | **Verificado (con límites)** | `docs/BREEZE_R7_RESULTS.md`: fuente única `animations.lua`, curvas exactas `kwin_*`, muelle nativo `spring:kwin_slide` verificado frente a `KWin::SpringMotion` en ida y reversión, `AnimationDurationFactor` corregido y medido en `libhyprutils`, `KWinScale` cargado y validado en vivo (`resetOnClose: 0 → 1`), página `Efectos de escritorio` (`kcm_bwm_effects`), `breeze-static-layers`, `breeze-sliding-layers` y `PlasmaTheme.slidingPopups` en panel/Kickoff/bandeja. Límite: sin `squash` hacia la tarea ni cross-fade de instantánea en `maximize`; 3 residuos temporales >33 ms bajo captura virtual en iteración 4 |
| **R8** | Mejoras de uso diario y avisos QML | **Verificado (con límites)** | `docs/BREEZE_R8_RESULTS.md` (lotes 1–16): avisos QML en arranque a 0; `TaskToolTip` (icono, cerrar, miniaturas protegidas sobre `bwmScreenshareMonitorGuard` v1 y controles MPRIS); exclusión mutua `Overlay` y máscara al fijar Kickoff; insignias y progreso `Unity LauncherEntry`; servidor de avisos propio en Breeze con respuesta en línea y DND temporal; portapapeles Klipper (texto, imagen, URL/miniaturas `gio`, QR Prison y edición); rueda de zonas, relojes, plugins de agenda (`holidaysevents`) y claves nativas del calendario; `PowerApplet` (inhibición manual `Idle` + `InhibitionHint` y `PowerProfileItem` vía `UPower.PowerProfiles`); filtros/agrupación/`wheelEnabled` en `TasksModel`; `PanelEditor` con `KI18nContext`, accesibilidad y controles de tareas/festivos; y `BluetoothApplet` con ownership estricto de discovery, `cancelPair`, `Trusted`/`Blocked`. Límites: sin trabajos KIO, OBEX/Bluedevil ni generación de miniaturas nuevas |
| **Bloqueo/PAM y acciones de energía** | Pruebas físicas en sesión real | **Confirmado por el usuario** | El usuario confirmó las pruebas físicas y el reinicio de sesión (2026-11-26, 0 coredumps); `test_power_session` y `test_plasma_lock_ui` cubren el contrato aislado |

---

## 4. Conclusión

**R9 cerrado (2026-11-26) — plan `BREEZE_PLAN_V2.md` completado con límites técnicos explícitos.**

Todas las fases R0–R9 están integradas y comprobadas con los binarios finales cargados en la nueva
sesión del usuario (`breezebars.so` `6c750f1a…`, `omarchy-titlebars.so` `36d0e4f4…`,
`bwm-plasma-host` `96cb7941…`, `bwm-decorator` `083d3ddd…`, 10 KCM nativos en `systemsettings`),
con dos paneles y dos escritorios nativos, una sola instancia de Quickshell, dueños únicos por
servicio, `hyprctl configerrors` vacío y 0 coredumps.

**Límites técnicos explícitos que se conservan abiertos (no se declara 100 % ni equivalencia total):**
- Sin sesión Plasma 6.7.5 separada para comparación visual píxel a píxel de referencia externa.
- Sombras: sin `_KDE_NET_WM_SHADOW` X11 ni dmabuf; contorno de esquinas de Breeze a escala 2 acotado por el radio entero de Hyprland.
- Animaciones: sin `squash` hacia la tarea ni cross-fade de instantánea en maximizado.
- Applets: sin trabajos KIO, OBEX/Bluedevil ni backends KWin ausentes en Hyprland para plasmoides arbitrarios que los exijan.
- Páginas exclusivas de BWM (`background`, `bar`, `services`, `general`, `style`, `about`, `windowrules`) siguen abriendo `plasmaSettings.qml` como complemento/respaldo de `systemsettings`.
