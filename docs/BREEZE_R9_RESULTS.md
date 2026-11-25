# R9 — Aceptación final y regresión de las tres skins

> Estado actualizado: 2026-11-25. La batería de §2 corresponde al 2026-11-22.
> R4–R5 está activo en la sesión diaria; R9 sigue abierto por aceptación física/visual.

## 1. Binarios y servicios realmente cargados en la sesión diaria

Verificado directamente sobre la sesión Wayland activa (skin `plasma`, Hyprland 0.56.2,
Quickshell `ii`):

| Componente | Estado real observado | Evidencia |
| :--- | :--- | :--- |
| `config/hypr/plugins/breezebars.so` | **Cargado y activo** | SHA-256 `103fab72be07684be362d6124705e8d346cf9b716a3e63e0473ec09e928a383d`; `hyprctl eval 'assert(hl.plugin.breezebars.blur_on_request ~= nil)'` OK; `breezebars-shadows` v2 activo (`shm: true`, XWayland `:0`); `breezebars-scale` v1 activo (`enabled: true`, `starts: 60`, `resetOnClose: 1`, `tracked: 0`) |
| `~/.local/share/bwm/bin/bwm-decorator` | **Instalado y escuchando** | `decorator.py status`: `installed: true`, `listening: true`, supervisor único (`3491`) + auxiliar único (`3492`) |
| `src/bwm-systemsettings` (KCMs nativos) | **Instalados y descubiertos** | `QT_QPA_PLATFORM=offscreen settings-native.sh --list` descubre los 10 KCM BWM (`kcm_bwm_apps`, `cursor`, `effects`, `energy`, `nightlight`, `screens`, `shortcuts`, `startup`, `windows`, `workspaces`) y mantiene restringido `kcm_kwin_effects` |
| Quickshell (`qs -c ii`) | **Instancia única** | `pgrep -af "qs -c ii\|quickshell -c ii"` → **1** proceso |
| Servicios auxiliares Breeze | **Dueño único por servicio** | `polkit-kde-authentication-agent-1` (1), `kde-config-bridge.py watch` (1), `bwm-decorator` (1) |
| Configuración de Hyprland | **Sin errores** | `hyprctl configerrors` vacío |
| Requisitos (`bwm-requirements.py`) | **Todo listo** | `bwm-requirements.py check --skin plasma`: núcleo + Breeze completos |

---

## 2. Suite de regresión ejecutada en R9

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
| **R4–R5** | Anfitrión nativo `bwm-plasma-host`, edición original de panel/escritorio, plasmoides externos | **Activo en sesión diaria; aceptación parcial** | §364: activado por petición expresa con corrección de foco de §363 instalada. Arranque por defecto en Breeze desde Hyprland; panel/escritorio nativos en ambas pantallas sin duplicados de Quickshell. §365 valida editor/explorador originales, añadir widget, Escape y regreso del foco en Hyprland desechable; corregido propietario visual del editor. Pendientes aceptación visual física, escritura continuada en Firefox y backends incompletos de KWin. §367–368 corrigen arranque/cast de miniaturas y registro SNI de kded. §369 corrige panelMask: 32 casos UI, foco y edición nativa pasan; arranque sin bucles QML. §370 verifica 20 ciclos con entrada Wayland desde otra aplicación y corrige reintentos exponenciales del área útil (normal/ASan). Aceptación visual física pendiente; no implica compatibilidad completa |
| **R6** | Sombras KDE originales, esquinas del contenido y desenfoque KWin | **Verificado (con límites)** | `docs/BREEZE_R6_RESULTS.md`: `breezebars.so` y `bwm-decorator` cargados en la sesión diaria; sombras en los 4 bordes/esquinas medidas sobre fondo `#dcdcdc` (0 px de hueco, contorno 1 px, degradado 34/56/46/44 px); `blur_on_request` y `SquareTop` verificados en vivo; desenfoque en panel, Kickoff, bandeja, notificaciones, OSD, cambiador (y `ThemeHost`), menús, tooltips, `PanelEditor` y KRunner. Límite: sin `_KDE_NET_WM_SHADOW` X11 ni dmabuf; contorno de esquinas de Breeze a escala 2 limitado por el radio entero de Hyprland |
| **R7** | Animaciones predeterminadas de Plasma 6.7.5 y sus ajustes | **Verificado (con límites)** | `docs/BREEZE_R7_RESULTS.md`: fuente única `animations.lua`, curvas exactas `kwin_*`, muelle nativo `spring:kwin_slide` verificado frente a `KWin::SpringMotion` en ida y reversión, `AnimationDurationFactor` corregido y medido en `libhyprutils`, `KWinScale` cargado y validado en vivo (`resetOnClose: 0 → 1`), página `Efectos de escritorio` (`kcm_bwm_effects`), `breeze-static-layers`, `breeze-sliding-layers` y `PlasmaTheme.slidingPopups` en panel/Kickoff/bandeja. Límite: sin `squash` hacia la tarea ni cross-fade de instantánea en `maximize`; 3 residuos temporales >33 ms bajo captura virtual en iteración 4 |
| **R8** | Mejoras de uso diario y avisos QML | **Verificado (con límites)** | `docs/BREEZE_R8_RESULTS.md` (lotes 1–16): avisos QML en arranque a 0; `TaskToolTip` (icono, cerrar, miniaturas protegidas sobre `bwmScreenshareMonitorGuard` v1 y controles MPRIS); exclusión mutua `Overlay` y máscara al fijar Kickoff; insignias y progreso `Unity LauncherEntry`; servidor de avisos propio en Breeze con respuesta en línea y DND temporal; portapapeles Klipper (texto, imagen, URL/miniaturas `gio`, QR Prison y edición); rueda de zonas, relojes, plugins de agenda (`holidaysevents`) y claves nativas del calendario; `PowerApplet` (inhibición manual `Idle` + `InhibitionHint` y `PowerProfileItem` vía `UPower.PowerProfiles`); filtros/agrupación/`wheelEnabled` en `TasksModel`; `PanelEditor` con `KI18nContext`, accesibilidad y controles de tareas/festivos; y `BluetoothApplet` con ownership estricto de discovery, `cancelPair`, `Trusted`/`Blocked`. Límites: sin trabajos KIO, OBEX/Bluedevil, generación de miniaturas nuevas ni comprobación visual física completa en el panel diario |
| **Bloqueo/PAM y acciones de energía** | Pruebas físicas destructivas | **Requiere intervención del usuario** | No se ejecutan cierre de sesión, apagado ni desbloqueo PAM reales desde el arnés automatizado (`test_power_session` y `test_plasma_lock_ui` cubren el contrato aislado) |

---

## 4. Conclusión

**R9 sigue abierto; el plan no está completamente aceptado.** Las 364 pruebas de §2
son la batería histórica de 2026-11-22. Después se activó R4–R5 en la sesión diaria y se
corrigieron foco, propietario visual del editor, disponibilidad del host, miniaturas,
registro SNI, máscara del panel y reintentos del área útil (BWM_CONTEXT §362–370).

La validación de 2026-11-25 añade 20 ciclos con entrada Wayland en otra aplicación
(81 letras más una en la ventana elegida), 6/6 QtTest de edición/entrada, los 32 casos UI
anteriores y la regresión de consulta bloqueada/recuperación normal y ASan. El binario
instalado y activo coincide con el construido; la sesión tiene dos paneles y dos escritorios
nativos, una sola instancia de Quickshell y ningún error de configuración.

Siguiente: aceptación visual/física diaria de edición, escritura prolongada en Firefox y
miniaturas; matriz de cambios de skin/monitores y comparación final con Plasma. Los backends
KWin ausentes y las limitaciones de los informes no se consideran resueltos por estas pruebas.
El estado operativo y el orden de continuación están al principio de `BREEZE_PLAN_V2.md`.
