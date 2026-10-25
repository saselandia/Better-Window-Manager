# Investigación: cómo tematiza Omarchy sus aplicaciones

> Fuente: clon superficial del repositorio `github.com/basecamp/omarchy` (redirige a `omacom/omarchy`),
> rama **`quattro`**, versión `4.0.0.alpha`, leído el 2026-10-23/24. Licencia MIT.
> Solo se leyeron los scripts citados; no se ejecutó nada de Omarchy.
> Este documento describe **Omarchy**, y al final cómo se refleja en BWM (Retro).

---

## 1. Idea central

Un tema de Omarchy es una **carpeta con un `colors.toml`** (más extras opcionales). Todo lo demás
(configs de terminales, btop, Hyprland, VSCode…) se **genera por plantillas** a partir de esa paleta.
Cambiar de tema = regenerar los archivos y avisar a cada app para que recargue.

```
themes/<tema>/colors.toml  ─┐
default/themed/*.tpl        ├─►  omarchy-theme-set-templates  ─►  ~/.local/state/omarchy/current/theme/*
~/.config/omarchy/themed/*.tpl (plantillas del usuario) ─┘
                                         │
                                         ▼
             omarchy-theme-set lanza un omarchy-theme-set-<app> por app (en paralelo)
                                         │
                                         ▼
                        omarchy-hook theme-set   (scripts del usuario)
```

## 2. Estructura de un tema

Ejemplo `themes/tokyo-night/`:

| Archivo | Para qué |
| :--- | :--- |
| `colors.toml` | **La paleta** (ver abajo). Es el único archivo obligatorio. |
| `backgrounds/` | Fondos del tema |
| `icons.theme` | Nombre del tema de iconos GNOME (`Yaru-blue`… por defecto) |
| `vscode.json` | Descriptor de la extensión de VSCode a instalar |
| `neovim.lua` | Tema de Neovim |
| `keyboard.rgb` | Color de la retroiluminación del teclado |
| `preview.png`, `unlock.png`, `shell.lock.toml` | Vista previa y pantalla de bloqueo |

Temas incluidos: catppuccin, catppuccin-latte, ethereal, everforest, flexoki-light, gruvbox, hackerman,
kanagawa, last-horizon, lumon, lupine, matte-black, miasma, nord, osaka-jade, retro-82, ristretto,
rose-pine, solitude, starship, tokyo-night, vantablack, white.

### Formato de `colors.toml`

```toml
mode = "dark"                       # o "light"
accent = "#7aa2f7"
selection = "#292e42"
muted = "#414868"
background = "#1a1b26"             # + dark_background, darker_background, lighter_background
foreground = "#a9b1d6"             # + dark_foreground, light_foreground, bright_foreground
red / yellow / orange / green / cyan / blue / magenta / brown
bright_red / bright_yellow / bright_green / bright_cyan / bright_blue / bright_magenta
```

Las plantillas usan `{{ nombre }}` y funciones como `{{ mix a b 30% }}`, `{{ hypr_gradient ... }}`,
`{{ shell_gradient ... }}`. El generador (`omarchy-theme-set-templates`) calcula las mezclas y renderiza
todas las plantillas en **una sola pasada de awk** para que el cambio de tema sea rápido.
El usuario puede añadir plantillas propias en `~/.config/omarchy/themed/`.

## 3. Plantillas incluidas (`default/themed/`)

`alacritty.toml`, `foot.ini`, `ghostty.conf`, `kitty.conf`, `btop.theme`, `hyprland.lua` (bordes activo/inactivo),
`neovim.lua`, `helix.toml`, `vscode-theme.json`, `obsidian.css`, `chromium.theme`, `claude.json`, `pi.json`,
`hermes.yaml`, `t3code.json`, `fcitx5-theme.conf`, `keyboard.rgb`, `shell.toml`, `gum_env.lua`,
`hyprland-preview-share-picker.css`.

## 4. Qué hace `omarchy-theme-set <tema>`

1. Bloquea con `flock` (un cambio de tema a la vez) y prepara el tema en `.../current/next-theme`.
2. Los temas instalados desde git **no pueden traer** archivos que ejecuten código (`*.lua`, configs de
   terminal que nombran un programa, `vscode.json`): se filtran (`INSTALLED_THEME_DENIED`).
3. Renderiza las plantillas (`omarchy-theme-set-templates`).
4. Intercambia atómicamente `next-theme` → `current/theme` (`rm -rf` + `mv`) y guarda el nombre y una
   «generación» para que los reintentos diferidos sepan si otro cambio los reemplazó.
5. Avisa al *shell* (barra/menús, su propio Quickshell-like) con la paleta y cambia el fondo con transición.
6. Lanza **en paralelo** estas órdenes (esperando a todas; las que fallan se notifican, nunca rompen el cambio):

| Grupo | Órdenes |
| :--- | :--- |
| Lo que se ve primero | `restart-terminal`, `theme-set-foot`, `theme-set-tmux`, `restart-btop`, `restart-opencode`, `restart-helix`, `theme-set-hunk` |
| El resto | `theme-set-gnome`, `-pi`, `-claude`, `-hermes`, `-t3code`, `-browser`, `-vscode`, `-obsidian`, `-keyboard`, `-fcitx5` |

7. Ejecuta `omarchy-hook theme-set <nombre>`.

## 5. Cómo se aplica a cada aplicación

| App | Mecanismo | ¿Recarga en vivo? |
| :--- | :--- | :--- |
| **kitty** | Plantilla `kitty.conf` → `SIGUSR1` a kitty (`omarchy-restart-terminal`). Lleva `dynamic_background_opacity yes` para poder cambiar la opacidad (modo glass) al recargar. | Sí |
| **Alacritty** | Plantilla `alacritty.toml`; se hace `touch` al archivo (recarga automática). | Sí |
| **Ghostty** | Plantilla `ghostty.conf` → `SIGUSR2`. | Sí |
| **foot** | Plantilla `foot.ini` + `omarchy-theme-set-foot`. | Sí |
| **btop** | Plantilla `btop.theme` (`theme[main_bg]`, `hi_fg`, `selected_bg`…) → `SIGUSR2`. | Sí |
| **tmux, helix, opencode, hunk** | Su propio `omarchy-theme-set-*` / `omarchy-restart-*`. | Sí |
| **Neovim** | `neovim.lua` del tema, cargado al arrancar. | Al reiniciar |
| **Hyprland** | Plantilla `hyprland.lua` (solo los colores de borde) + `hyprctl reload`. | Sí |
| **GTK / Nautilus** | `gsettings`: `color-scheme prefer-dark/light`, `gtk-theme Adwaita-dark/Adwaita`, `icon-theme` desde `icons.theme`. **No** reescribe colores GTK. | Sí |
| **Chromium, Chrome, Edge, Brave** | `omarchy-theme-set-browser`: escribe una **política administrada** `{"BrowserThemeColor": "#hex", "BrowserColorScheme": "device"}` (necesita permisos de root; solo se reescribe si cambió) y refresca los navegadores abiertos. El color sale de `chromium.theme`. | Sí |
| **VSCode / VSCodium / Cursor** | Genera la extensión local `omarchy-theme` (`vscode-theme.json` + `vscode.json`) y la registra en `extensions.json`. | Al recargar la ventana |
| **Obsidian** | Plantilla `obsidian.css`. | Sí |
| **Claude Code, pi, hermes, t3code** | Plantillas `claude.json`, `pi.json`, `hermes.yaml`, `t3code.json`. | Según la herramienta |
| **Teclado RGB** | `keyboard.rgb` (ASUS ROG, F16…). | Sí |
| **fcitx5** | Plantilla `fcitx5-theme.conf`. | Sí |
| **Barra, menús, bloqueo, OSD** | El *shell* de Omarchy recibe `colors.toml` / `shell.toml` por IPC. | Sí |
| **Plymouth / SDDM** | `omarchy-plymouth-set-by-theme`, `omarchy-refresh-plymouth`, `omarchy-refresh-sddm`. | Al reiniciar |

> La columna «¿Recarga en vivo?» es orientativa: solo se leyeron los scripts de reinicio de kitty/Alacritty/Ghostty,
> btop y la política de los navegadores; el resto se deduce del nombre y los comentarios de cada `omarchy-theme-set-*`.

### Lo que Omarchy **no** tematiza

- **Discord**: es una *web app*: `applications/Discord.desktop` ejecuta `omarchy-launch-webapp https://discord.com/channels/@me`.
  Su único «tema» es el color de la política `BrowserThemeColor` del navegador.
- **Firefox**: solo trae `default/firefox/policies.json` con ajustes de rendimiento (VA-API, overscroll,
  escala fraccionaria). No hay tema de la interfaz.
- **Spotify, Steam, apps Qt, GTK con colores propios**: no los cubre. La comunidad lo resuelve con hooks
  (el proyecto *omarchy-theme-hook* —sin licencia publicada— se usó solo como idea, no se copió código).

## 6. Hooks (puerta para «todas las demás» apps)

`omarchy-hook <nombre>` ejecuta `~/.config/omarchy/hooks/<nombre>` y todo lo de `<nombre>.d/`.
Los nombres válidos son etiquetas fijas (`theme-set`, `post-update`, `font-set`…); se rechazan barras y
`.`/`..`. El hook de tema recibe el nombre del tema y puede leer `~/.local/state/omarchy/current/theme/`.
Es el mecanismo para tematizar cualquier app que Omarchy no conozca.

## 7. Transparencia, desenfoque y opciones visuales

### Transparencia por defecto (`default/hypr/windows.lua`)

- Las apps son **opacas**. Solo **optan por la transparencia**:
  - los terminales y TUIs (etiqueta `terminal`: Alacritty, kitty, ghostty, foot, wezterm, `org.omarchy.*`, `TUI.*`),
  - Nautilus y algunas apps (1Password, omawrite),
  - cualquier ventana con la etiqueta `transparent` (la pone el atajo).
- Opacidad estándar: **`0.985 0.96`** (activa / inactiva) mediante `o.transparent_window(...)`, que añade la
  etiqueta `transparent-window`.
- `SUPER + BACKSPACE` → `omarchy-hyprland-window-transparency-toggle`: alterna la transparencia de la
  ventana activa (etiqueta + `set_prop opaque`).

### Tres modos (`omarchy-hyprland-window-transparency [opaque|transparent|glassy]`)

| Modo | Archivo de estado (`~/.local/state/omarchy/toggles/hypr/`) | Efecto |
| :--- | :--- | :--- |
| transparent (por defecto) | ninguno | Reglas anteriores |
| opaque | `window-opaque.lua` | Todo a opacidad `1 1` |
| glassy | `window-glassy.lua` | Desenfoque esmerilado detrás de lo translúcido |

El modo **glassy** (`default/hypr/glass.lua`) activa `blur` con `size 4`, `passes 2`, `brightness 0.75`,
`noise 0.01`, `vibrancy 0.35`, `popups`/`special` y blur en las capas del shell. Como una regla de opacidad de
Hyprland también desvanece el **texto**, el cristal de los terminales se escribe **en su propio archivo de tema**
(`omarchy-theme-set-glass`, entre marcadores `omarchy-glass begin/end` que se retiran al salir de glassy), para que
el texto quede nítido. Nautilus (GTK, fondo sólido) se atenúa entero a `0.75`.

### Otros interruptores (`default/hypr/toggles/` + `omarchy-hyprland-*`)

| Interruptor | Qué hace |
| :--- | :--- |
| `corners-sharp` / `corners-rounded` | Esquinas cuadradas o redondeadas, sea cual sea el tema |
| `window-no-gaps` | Sin huecos ni bordes (`gaps_in/out = 0`, `border_size = 0`) |
| `single-window-aspect-ratio` | Una sola ventana con proporción cuadrada centrada |
| `no-animations` | Desactiva animaciones |
| `bar-glassy` | Barra translúcida con blur |
| `omarchy-hyprland-window-pop` / `-minimize` / `-close-all` / `-width` / `-tiled-fullscreen-toggle` | Utilidades de ventana |
| `omarchy-hyprland-workspace-layout-toggle` | Recorre los layouts dwindle, scrolling y flotante |

### Estética base (`default/hypr/looknfeel.lua`)

`rounding = 0`, sin sombra ni blur, `gaps_in 5`, `gaps_out 10`, `border_size 2`, borde activo en gradiente
`33ccff → 00ff99` a 45°, animaciones `easeOutQuint` (ventanas con `popin 87%`), cambio de workspace sin animación,
`groupbar` monoespaciada. Es decir: **cuadrado, plano, de terminal**.

### Reglas por aplicación (`default/hypr/apps/*.lua`)

Etiquetas `chromium-based-browser`/`firefox-based-browser`, apps flotantes (1Password, Bitwarden, Steam,
Telegram, LocalSend, Moonlight, JetBrains, DaVinci…), captive portal, PiP, ventanas de captura de pantalla
y de compartir pantalla enviadas a un workspace especial silencioso.

## 8. Cosas relacionadas que también cambian con el tema

- **Fuente del sistema** (`omarchy-font-set`), **iconos** (`icons.theme`), **fondo** con transición, **arranque**
  (Plymouth), **inicio de sesión** (SDDM), **bloqueo** (hyprlock/shell), **teclado RGB**.
- Chromium recibe solo el color del tema; el resto del navegador sigue la preferencia del sistema.

---

## 9. Reflejo en BWM (tema Retro)

| Omarchy | BWM |
| :--- | :--- |
| `colors.toml` | `~/.local/state/bwm/omarchy/colors.toml`, generado desde el **fondo de pantalla** (`bwm_omarchy.build_colors`) |
| Plantillas `kitty.conf` / `btop.theme` | Copiadas (MIT) en `config/hypr/omarchy/themed/` |
| Resto de plantillas | Las de **matugen** del proyecto rellenas con la paleta Omarchy (GTK 3/4, Vesktop, swaync, Firefox, Quickshell, rofi, Qt…) |
| Aspecto «de terminal» | Capas `config/hypr/omarchy/overlays/` (JetBrainsMono Nerd Font, esquinas rectas, sin sombras, marcos de 1 px) |
| Discord / Firefox (no tematizados por Omarchy) | Overlays TUI propios para Vesktop (se recarga solo) y la interfaz de Firefox (requiere reiniciar) |
| `omarchy-hook theme-set` | `~/.config/bwm/hooks/theme-set[.d]` (`BWM_THEME`, `BWM_COLORS`, `BWM_STATE`) |
| Transparencia (`terminal` → `0.985 0.96`, resto opaco) | `modules/omarchy_windows.lua` + `scripts/window-transparency.sh` (`SUPER+BACKSPACE`) |
| Modo glassy | `scripts/glass.sh` + `modules/glass.lua` |
| `corners-sharp`, `window-no-gaps`, `single-window-aspect-ratio`, cambio de layout | **No portados** (pendientes) |
| VSCode, Obsidian, tmux, helix, neovim, ghostty, alacritty, foot | VSCodium se tematiza con `workbench.colorCustomizations`; el resto no está instalado |
| Chromium (`BrowserThemeColor`) | No portado (no hay navegador Chromium en uso) |

Limitaciones conocidas: la interfaz de Firefox solo lee `userChrome.css` al arrancar (se reinicia al entrar o salir
de Retro; los colores sí cambian en vivo con Pywalfox), y GTK 3 solo lee `gtk.css` al abrir cada app.

---

## 10. Plugins del shell (Omarchy 4 «quattro»)

Desde Omarchy 4 toda la interfaz es **un solo proceso Quickshell** (`omarchy-shell`, carpeta `shell/`) y casi todo
son **plugins**: un repositorio git con un `manifest.json` (`id`, `kinds`: `bar-widget`, `service`, `panel`, `overlay`,
`menu`; `entryPoints`; `barWidget.defaultSection` y `defaults`). Se instalan con `omarchy plugin add <git> --enable`
en `~/.config/omarchy/plugins/` y su colocación en la barra vive en `~/.config/omarchy/shell.json`. Son código sin aislar.
Los widgets importan `qs.Commons` (singletons `Color`, `Style`, `Util`, `I18n`…: colores de `colors.toml` + `shell.toml`)
y `qs.Ui` (`BarWidget`, `PopupCard`, `Panel`, `PluginBarApi`…). El anfitrión les da `bar` (colores, tamaño, `run`,
popouts) y `bar.shell` (`serviceFor`, `updateEntryInline`, `pluginRegistry`, `barConfig`).

### Preinstalados (primera parte, `shell/plugins/`)

Barra, selector de imágenes, emojis, portapapeles, recordatorios, menú de Omarchy, notificaciones, audio, Bluetooth,
reloj, Elsewhen (zonas horarias), monitor, red, energía, Tailscale, agentes de IA, tiempo, multimedia, batería, inactividad,
luz nocturna, sesión remota, bloqueo, OSD, polkit y dock. Grupo de **indicadores** junto al reloj: sudo sin contraseña,
grabando pantalla, sesión remota, recordatorio, luz nocturna, no molestar y mantener despierto (glifos Nerd Font;
solo se ven los activos y al pasar el ratón los inactivos al 45 %). Reloj `dddd HH:mm` (alternativo `d MMMM 'W'ww yyyy`).

### Plugins de terceros más usados (estrellas en GitHub, 2026-10-25; todos MIT)

| ★ | Plugin | Qué hace |
| ---: | :--- | :--- |
| 721 | akitaonrails/ai-usagebar | Uso y límites de Claude, Codex, GLM, OpenRouter (binario Rust + widget) |
| 310 | huacnlee/omamail | Correo (Gmail, HEY, IMAP) |
| 239 | stappmus/Omarchy-Spotify | Spotify dentro del shell |
| 238 | thisisgm/omarchy-pods | Batería y modos de AirPods |
| 216 | SirJul1337/omarchy-lock-explorer | Diseños de pantalla de bloqueo |
| 171 | wesleygrimes/omastorm | Radar meteorológico NEXRAD (EE. UU.) |
| 144 | jankeesvw/omarchy-time-machine | Copias con restic |
| 136 | crmne/omarchy-hyprmoncfg | Perfiles de monitores |
| 125 | nixfred/infomarchy | Fondo de pantalla con información en vivo |
| 68 | brianblakely/omarchy-plugins | Tienda de plugins (Okomart) |
| 62 | robzolkos/omarchy-github | GitHub en la barra |
| 43 | crmne/omastats | Monitor del sistema estilo iStat Menus |
| 20 | crmne/omarchy-mpris | Multimedia con carátula |
| 10 | crmne/omarchy-active-window | Ventana activa con icono |

Fuentes: [omarchy.deepakness.com/plugins](https://omarchy.deepakness.com/plugins), [manual de Omarchy](https://omarchy.org/manual/shell-plugins/), API de GitHub.
El marketplace oficial (`plugins.omarchy.org`) carga la lista con JavaScript y no se pudo leer.

### Reflejo en BWM (Retro)

- `config/quickshell/ii/Commons` y `Ui`: copia de `shell/Commons` y `shell/Ui` (MIT). Cambios: `Color.qml` lee
  `~/.local/state/bwm/omarchy/{colors,shell}.toml`; `I18n.qml` usa las cadenas incluidas en `Commons/omarchy/`.
- `bwm_omarchy.py` renderiza `shell.toml` desde la plantilla de Omarchy (`{{ mix … }}`, `{{ shell_gradient … }}`).
- `modules/ii/bar/omarchy/`: `OmarchyPlugins.qml` (el `bar.shell`), `OmarchyPluginSlot.qml` (`PluginBarApi` por widget,
  secciones izquierda / junto al reloj / derecha) y `OmarchyIndicators.qml` (grabando, luz nocturna, no molestar,
  mantener despierto).
- `hypr/scripts/bwm-plugin.sh` = `omarchy plugin add/remove/update/list/enable/disable`; `defaults` instala ai-usagebar
  (compila el binario con cargo), omastats, omarchy-mpris y omarchy-active-window. Con glibc < 2.44 omastats usa su
  muestreador en Python.
- No portados: los widgets de primera parte de Omarchy (dependen de los servicios de `omarchy-shell`); BWM tiene sus
  equivalentes. Plugins que necesitan cuentas (correo, GitHub, Todoist) o hardware concreto (AirPods, MOZA) quedan
  para instalarlos a mano.
- Captura de pantalla: Omarchy usa **omasnap** (congela la pantalla, copia, vista previa flotante 10 s, fijar, editar,
  guardar en `~/Pictures/Screenshots`). BWM usa su selector de región; en Retro con marcos de acento, guarda y copia,
  y muestra la misma vista previa (`modules/ii/screenshotPreview/OmarchyScreenshotPreview.qml`).
