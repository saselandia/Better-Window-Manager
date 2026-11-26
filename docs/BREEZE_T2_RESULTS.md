# Breeze III — T2: Preferencias del sistema que funcionan o se ocultan

Fecha: 2026-11-26. Plan: [BREEZE_PLAN_V3.md](BREEZE_PLAN_V3.md). Base: T1 cerrada (§387).

## Qué se ha implementado

1. **`kcm_bwm_input` (Ratón y panel táctil sobre Hyprland):**
   - Gestor común a todas las skins: [`config/hypr/scripts/input-manager.py`](../config/hypr/scripts/input-manager.py), que descubre dispositivos reales de puntero desde `hyprctl -j devices` (filtrando interfaces auxiliares `consumer-control`/`system-control` de teclados), guarda `~/.config/hypr/input-devices.json` y genera `~/.config/hypr/modules/input_devices.lua` (cargado por [`hyprland.lua`](../config/hypr/hyprland.lua) después de `modules.binds` y antes de `~/.config/bwm/user/hyprland.lua`).
   - Opciones globales y por dispositivo: sensibilidad/velocidad (`-1.0` a `1.0`), perfil de aceleración (`""`, `adaptive`, `flat`), desplazamiento natural, modo zurdo y opciones de panel táctil (`natural_scroll`, `tap-to-click`, `disable_while_typing`).
   - Plugin KCM [`kcm_bwm_input`](../src/bwm-systemsettings/kcm_bwm_input.json) ([`plugin_input.cpp`](../src/bwm-systemsettings/plugin_input.cpp)) en categoría `pointing-devices`, conectado a [`native-settings.py`](../config/hypr/skins/plasma/scripts/native-settings.py) y alias `mouse|touchpad|input|kcm_mouse|kcm_touchpad` en [`settings-native.sh`](../config/hypr/skins/plasma/scripts/settings-native.sh).
2. **Región y formatos (`plasma-localerc` `LC_*` en todas las skins):**
   - [`config/hypr/modules/environment.lua`](../config/hypr/modules/environment.lua) lee `~/.config/plasma-localerc` (`[Formats]`) al cargar Hyprland y exporta mediante `hl.env` las categorías `LC_*` válidas (`LC_NUMERIC`, `LC_TIME`, `LC_MONETARY`, `LC_MEASUREMENT`, `LC_COLLATE`, `LC_ADDRESS`, `LC_NAME`, `LC_PAPER`, `LC_TELEPHONE`).
   - Respeta `useDetailed=false`, valida caracteres permitidos y **nunca pisa `LANG`** si el usuario o el sistema ya fijaron un `LANG` distinto de vacío/`C`/`POSIX`.
   - [`autostart.sh`](../config/hypr/scripts/autostart.sh) y [`bwm_session.py`](../config/hypr/scripts/bwm_session.py) (`sync_activation_environment`) propagan esos `LC_*` a D-Bus y `systemd --user`.
3. **Ocultación mediante perfil KAuthorized ([`settings-profile/kdeglobals`](../config/hypr/skins/plasma/settings-profile/kdeglobals)):**
   - Sin borrar plugins del sistema; sólo en el proceso de `settings-native.sh`: `kcm_mouse`, `kcm_touchpad`, `kcm_kwinscreenedges` (+ `_x11`), `kcm_kwintouchscreen` (+ `_x11`), `kcm_touchscreen`, `kcm_access`, `kcm_smserver` y `kcm_activities`.

## Inventario completo de páginas de `settings-native.sh`

### Páginas activas (43 módulos visibles en `systemsettings --list`)

| Módulo | Estado | Motivo / notas |
| :--- | :--- | :--- |
| `kcm_bwm_input` | **implementada** | Nuevo KCM común sobre `input-manager.py` + `modules/input_devices.lua` (ratón y touchpad globales y por dispositivo) |
| `kcm_regionandlang` | **implementada** | Guarda `plasma-localerc`; `environment.lua` + `autostart.sh` + `bwm_session.py` aplican `[Formats]` (`LC_*`) al iniciar sesión en todas las skins sin pisar `LANG` |
| `kcm_notifications` | **funciona** | Verificada en T1 (`bwm-plasma-host` + `NotificationHost` + `libnotificationmanager` en vivo sobre `plasmanotifyrc` y `*.notifyrc`) |
| `kcm_soundtheme` | **funciona** | Escribe `kdeglobals [Sounds] Theme`, consumido por `libcanberra` en `libnotificationmanager` y `KNotification` |
| `kcm_bwm_apps` | **funciona** | KCM BWM sobre `default-apps.py` (común) |
| `kcm_bwm_cursor` | **funciona** | KCM BWM sobre `cursor-manager.py` (común) |
| `kcm_bwm_effects` | **funciona** | KCM BWM sobre efectos soportados por Breeze (`kwinrc` / `kdeglobals`, R7) |
| `kcm_bwm_energy` | **funciona** | KCM BWM sobre `Config.idle` + `BwmIdle.qml` (común) |
| `kcm_bwm_nightlight` | **funciona** | KCM BWM sobre `nightlight.py` (común) |
| `kcm_bwm_screens` | **funciona** | KCM BWM sobre `monitor-manager.py` (común) |
| `kcm_bwm_shortcuts` | **funciona** | KCM BWM sobre `keybinds-manager.py` (común; T5 integrará atajos KDE) |
| `kcm_bwm_startup` | **funciona** | KCM BWM sobre `autostart-manager.py` (común) |
| `kcm_bwm_windows` | **funciona** | KCM BWM sobre opciones de foco, colocación, encaje y doble clic de barra traducidas a Hyprland/`breezebars` |
| `kcm_bwm_workspaces` | **funciona** | KCM BWM sobre `monitor-manager.py` / `bar.workspaces.shown` (común) |
| `kcm_bluetooth` | **funciona** | Habla directamente con BlueZ / `bluedevil` |
| `kcm_networkmanagement` | **funciona** | Habla directamente con NetworkManager |
| `kcm_pulseaudio` | **funciona** | Habla directamente con PipeWire / PulseAudio |
| `kcm_clock` | **funciona** | Habla con `systemd-timedated` |
| `kcm_users` | **funciona** | Habla con `accountsservice` / usuarios del sistema |
| `kcm_colors` | **funciona** | Escribe `kdeglobals`; sincronizado por `kde-config-bridge.py` + `plasma-theme.py sync` |
| `kcm_desktoptheme` | **funciona** | Escribe `plasmarc`; aplicado en vivo por `bwm-plasma-host` / `libplasma` |
| `kcm_icons` | **funciona** | Escribe `kdeglobals [Icons]`; sincronizado por `kde-config-bridge.py` + `plasma-theme.py` |
| `kcm_style` | **funciona** | Escribe `kdeglobals [KDE] widgetStyle` (apps Qt/KDE) |
| `kcm_fonts` | **funciona** | Escribe `kdeglobals`; sincronizado bidireccionalmente con `appearance.fonts` |
| `kcm_fontinst` | **funciona** | Instala y gestiona fuentes en fontconfig / `~/.local/share/fonts` |
| `kcm_kwindecoration` | **funciona** | Escribe `kwinrc [org.kde.kdecoration2]` y `breezerc`; consumido por `bwm-decorator` + `breezebars` |
| `kcm_lookandfeel` | **funciona** (parcial) | Colores, estilos, iconos y decoración funcionan (cursor protegido por BWM); la casilla de disposición del escritorio/panel se completa en T4 |
| `kcm_splashscreen` | **funciona** (guardado; T4) | Guarda `ksplashrc` correctamente; su ejecución al arranque se conecta en T4 |
| `kcm_kwintabbox` | **funciona** (parcial) | `LayoutName` de `kwinrc [TabBox]` se aplica en `modules/plasma/switcher` (`interface-theme.py`); filtros avanzados exclusivos de KWin no tienen efecto |
| `kcm_workspace` | **funciona** (parcial) | `SingleClick` y comportamiento general en apps KDE funcionan; la velocidad de animaciones se controla en `kcm_bwm_effects` |
| `kcm_plasmasearch` | **funciona** | Configura plugins de KRunner (`krunnerrc`), usado por KRunner nativo en `Alt+Espacio` |
| `kcm_filetypes` | **funciona** | Asociaciones de archivos XDG (`mimeapps.list`) |
| `kcm_desktoppaths` | **funciona** | Rutas personales XDG (`user-dirs.dirs`) |
| `kcm_recentFiles` | **funciona** | Historial de archivos recientes de apps KDE |
| `kcm_device_automounter` | **funciona** | Módulo `device_automounter` de `kded6` / Solid |
| `kcm_solid_actions` | **funciona** | Acciones de dispositivos de Solid (`devicenotifier`) |
| `kcm_kded` | **funciona** | Gestión D-Bus directa de módulos de `kded6` |
| `kcm_netpref` | **funciona** | Preferencias KIO (`kioslaverc`) |
| `kcm_proxy` | **funciona** | Proxy KIO (`kioslaverc`) |
| `kcm_webshortcuts` | **funciona** | Atajos web de KRunner/KIO (`kuriikwsfilterrc`) |
| `kcmspellchecking` | **funciona** | Diccionarios y corrector Sonnet (`sonnetrc`) |
| `kcm_qtquicksettings` | **funciona** | Backend de renderizado QtQuick (`kdeglobals`) |
| `kcm_landingpage` | **funciona** | Página inicial de `systemsettings`; respeta las restricciones KAuthorized |

### Páginas ocultadas en T2 (perfil KAuthorized)

| Módulo | Estado | Motivo |
| :--- | :--- | :--- |
| `kcm_mouse` | **oculta** | Pide dispositivos a KWin (`org.kde.KWin.InputDevice`, salía vacía); sustituida por `kcm_bwm_input` |
| `kcm_touchpad` | **oculta** | Pide dispositivos a KWin (`org.kde.KWin.InputDevice`, salía vacía); sustituida por `kcm_bwm_input` |
| `kcm_kwinscreenedges` (+ `_x11`) | **oculta** | Sin esquinas activas hasta T8 |
| `kcm_kwintouchscreen` (+ `_x11`) | **oculta** | Gestos táctiles de KWin sin equivalente en Hyprland |
| `kcm_touchscreen` | **oculta** | Calibración/dispositivos táctiles de KWin |
| `kcm_access` | **oculta** | Depende de KWin/`kaccess` (teclas lentas/rebotes/pantalla), sin efecto en Hyprland |
| `kcm_smserver` | **oculta** | Restauración de sesión de `ksmserver`, descartada en el plan |
| `kcm_activities` | **oculta** | Actividades de KWin/`kactivitymanagerd`, descartadas en el plan |

*(Se mantienen además las restricciones previas de R3 en `settings-profile/kdeglobals`: `kcm_kscreen`, `kcm_kwin_virtualdesktops`, `kcm_keys`, `kcm_powerdevilprofilesconfig`, `kcm_energyinfo`, `kcm_kwin_effects`, `kcm_kwin_scripts`, `kcm_kwinoptions`, `kcm_kwinrules`, `kcm_animations`, `kcm_cursortheme`, `kcm_nightcolor`, `kcm_keyboard`, `kcm_componentchooser`, `kcm_autostart`, `kcm_nightlight`, `kcm_nighttime`, `kcm_kwinxwayland`, `kcm_screenlocker`, `kcm_virtualkeyboard`, `kcm_wallpaper`.)*

## Comprobaciones realizadas

- `make -C src/bwm-systemsettings test install`: compilación e instalación atómica de `kcm_bwm_input.so`; CTest **3/3 PASS** (`native-kcm`, `manager-kcm`, `installed-decoration-option`).
- `python3 -m unittest -v tests/test_breeze_t2.py`: **4/4 PASS**:
  - Descubrimiento de dispositivos, filtrado de `consumer-control`, detección de touchpad, generación y ejecución sintáctica en `lua5.4` de `modules/input_devices.lua`, y rechazo de valores fuera de rango.
  - Carga de esquema de `native-settings.py input load` con `revision` y campos globales/por dispositivo.
  - Carga de `plasma-localerc` en `environment.lua` bajo `lua5.4`: exporta `LC_*` válidos, respeta `useDetailed=false`, rechaza inyecciones y **no pisa `LANG`** cuando ya está definido (sólo aplica `LANG` si era vacío/`C`/`POSIX`).
  - Visibilidad real en `systemsettings --list` con `settings-profile`: las 8 páginas ocultadas no aparecen; `kcm_bwm_input`, `kcm_notifications` y `kcm_regionandlang` sí aparecen.
- `hyprctl configerrors`: sin errores.
