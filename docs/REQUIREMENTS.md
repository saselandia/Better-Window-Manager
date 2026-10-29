# Requisitos de BWM

> Generado con `config/hypr/scripts/bwm-requirements.py docs > docs/REQUIREMENTS.md` a partir de
> `config/hypr/skins/requirements.json` y de los manifiestos de cada skin. Esos archivos son la
> fuente de verdad: los leen `install.sh`, `bwm check` y la bienvenida. Cambia los requisitos allí.

Comprueba tu equipo con `./install.sh --check` o, ya instalado, `bwm check`: dice qué falta y te
da los comandos exactos para tu distribución. Notación de paquetes:

* **Gentoo:** `repo:categoría/paquete` = paquete de un overlay que hay que activar
  (`sudo eselect repository enable guru hyproverlay && sudo emaint sync -r guru -r hyproverlay`).
  Hyprland y sus herramientas están en [hyproverlay](https://codeberg.org/hyproverlay/hyproverlay);
  Quickshell, matugen, adw-gtk3, cliphist, awww… en [GURU](https://wiki.gentoo.org/wiki/Project:GURU).
* **Arch:** `aur:paquete` = AUR (`paru` o `yay`).
* **Fedora:** `copr:usuario/proyecto:paquete` = repositorio COPR (`sudo dnf copr enable usuario/proyecto`).
* **—** = la distribución no lo empaqueta: `bwm check` muestra cómo instalarlo a mano o la guía
  ([Hyprland](https://wiki.hypr.land/Getting-Started/Installation/),
  [Quickshell](https://quickshell.outfoxxed.me/docs/guide/install-setup/)).

Debian/Ubuntu no empaquetan un Hyprland con configuración en Lua (≥ 0.55) ni Quickshell: hay que
compilarlos o usar sus repositorios de terceros.

## Núcleo: lo que necesita cualquier skin para pintar la pantalla

| Requisito | Para qué | Gentoo | Arch / CachyOS | Fedora | openSUSE | Debian / Ubuntu |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Hyprland ≥ 0.55 | Compositor. BWM se configura en Lua, que llegó con Hyprland 0.55 | `hyproverlay:gui-wm/hyprland` | `hyprland` | `copr:solopasha/hyprland:hyprland` | `hyprland` | — |
| Quickshell | Pinta barras, paneles, menús, bloqueo y OSD de todas las skins (Qt 6 / QML) | `guru:gui-apps/quickshell` | `aur:quickshell` | `copr:errornointernet/quickshell:quickshell` | — | — |
| Qt 6 5Compat (GraphicalEffects) | Sombras, máscaras y tintes de los iconos en Quickshell | `dev-qt/qt5compat` | `qt6-5compat` | `qt6-qt5compat` | `qt6-qt5compat-imports` | `qml6-module-qt5compat-graphicaleffects` |
| Qt 6 SVG | Iconos SVG de las barras y applets | `dev-qt/qtsvg` | `qt6-svg` | `qt6-qtsvg` | `qt6-svg` | `qt6-svg-plugins` |
| Qt ≥ 6.10 (Qt.labs.synchronizer) | Controles de Ajustes y paneles sincronizados con la configuración | `dev-qt/qtdeclarative` | `qt6-declarative` | `qt6-qtdeclarative` | `qt6-declarative-imports` | — |
| Python ≥ 3.11 | Gestor de skins, motor de temas y scripts (usa tomllib) | `dev-lang/python` | `python` | `python3` | `python3` | `python3` |
| Pillow (Python) | Lee el fondo para sacar paletas y miniaturas | `dev-python/pillow` | `python-pillow` | `python3-pillow` | `python3-Pillow` | `python3-pil` |
| jq | Perfiles JSON de cada skin y scripts | `app-misc/jq` | `jq` | `jq` | `jq` | `jq` |
| swww o awww | Pinta el fondo de pantalla con transiciones (awww es el nombre nuevo de swww; vale cualquiera) | `guru:gui-apps/awww` | `swww` | — | `swww` | — |
| wl-clipboard | Portapapeles de Wayland (copiar, pegar, capturas) | `gui-apps/wl-clipboard` | `wl-clipboard` | `wl-clipboard` | `wl-clipboard` | `wl-clipboard` |
| cliphist | Historial del portapapeles | `guru:app-misc/cliphist` | `cliphist` | `cliphist` | `cliphist` | `cliphist` |
| kitty | Terminal por defecto; se recolorea en vivo con cada skin y tema | `x11-terms/kitty` | `kitty` | `kitty` | `kitty` | `kitty` |
| grim | Capturas de pantalla y miniaturas | `gui-apps/grim` | `grim` | `grim` | `grim` | `grim` |
| slurp | Seleccionar una región para capturas | `gui-apps/slurp` | `slurp` | `slurp` | `slurp` | `slurp` |
| libnotify (notify-send) | Avisos de los scripts | `x11-libs/libnotify` | `libnotify` | `libnotify` | `libnotify-tools` | `libnotify-bin` |
| GLib (gsettings) | Tema GTK, modo claro/oscuro e iconos de cada skin | `dev-libs/glib` | `glib2` | `glib2` | `glib2-tools` | `libglib2.0-bin` |
| fontconfig | Registrar las fuentes que trae BWM | `media-libs/fontconfig` | `fontconfig` | `fontconfig` | `fontconfig` | `fontconfig` |
| PipeWire + WirePlumber | Volumen, OSD y applets de audio | `media-video/wireplumber` | `wireplumber` | `wireplumber` | `wireplumber` | `wireplumber` |
| adw-gtk3 | Base de los temas GTK 3 BWM-1/BWM-2 que siguen a la skin en vivo | `guru:x11-themes/adw-gtk3` | `adw-gtk-theme` | `adw-gtk3-theme` | — | — |
| Fuentes de BWM (Material Symbols, Google Sans Flex) | Iconos y textos de Quickshell | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* |

### Recomendado (opcional)

| Requisito | Para qué | Gentoo | Arch / CachyOS | Fedora | openSUSE | Debian / Ubuntu |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| xdg-desktop-portal-hyprland | Compartir pantalla y capturas desde apps | `hyproverlay:gui-libs/xdg-desktop-portal-hyprland` | `xdg-desktop-portal-hyprland` | `xdg-desktop-portal-hyprland` | `xdg-desktop-portal-hyprland` | — |
| xdg-desktop-portal-gtk | Diálogo de abrir/guardar archivos (FileChooser=gtk) | `sys-apps/xdg-desktop-portal-gtk` | `xdg-desktop-portal-gtk` | `xdg-desktop-portal-gtk` | `xdg-desktop-portal-gtk` | `xdg-desktop-portal-gtk` |
| playerctl | Teclas multimedia | `media-sound/playerctl` | `playerctl` | `playerctl` | `playerctl` | `playerctl` |
| NetworkManager | Applets y paneles de red | `net-misc/networkmanager` | `networkmanager` | `NetworkManager` | `NetworkManager` | `network-manager` |
| BlueZ | Applets y paneles de Bluetooth | `net-wireless/bluez` | `bluez-utils` | `bluez` | `bluez` | `bluez` |
| qt6ct | Paleta de la skin en las apps Qt | `gui-apps/qt6ct` | `qt6ct` | `qt6ct` | `qt6ct` | `qt6ct` |
| socat | Salvapantallas de terminal (eventos de Hyprland) | `net-misc/socat` | `socat` | `socat` | `socat` | `socat` |
| git | Instalar temas y plugins de la comunidad y actualizar BWM | `dev-vcs/git` | `git` | `git` | `git` | `git` |
| Nautilus | Gestor de archivos tematizado (Super+E) | `gnome-base/nautilus` | `nautilus` | `nautilus` | `nautilus` | `nautilus` |
| Firefox | Navegador tematizado (userChrome + Pywalfox) | `www-client/firefox-bin` | `firefox` | `firefox` | `MozillaFirefox` | `firefox-esr` |
| Flatpak | Vesktop, Spotify, Stremio… tematizados con overrides | `sys-apps/flatpak` | `flatpak` | `flatpak` | `flatpak` | `flatpak` |

## Skin Default

Imita **end-4 / illogical-impulse (Material You)**. Material Design 3: barra, panel lateral, vista general y Alt+Tab de illogical-impulse. Todo el escritorio y las apps toman los colores del fondo de pantalla.

* **Ventanas:** mosaico (*tiling*)
* **Tema por defecto:** Material You desde el fondo (dinámico). Dinámico: matugen genera la paleta del fondo cada vez que lo cambias (Alt+W).
* **Temas:** Paleta dinámica de matugen (claro u oscuro según el fondo).
* **Compatibilidad:** Objetivo: plantillas y fondos de la comunidad de matugen / end-4 funcionan tal cual.

| Requisito | Para qué | Gentoo | Arch / CachyOS | Fedora | openSUSE | Debian / Ubuntu |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| matugen | Genera la paleta Material You desde el fondo (tema dinámico de Default) | `guru:x11-misc/matugen` | `aur:matugen-bin` | — | — | — |
| rofi (con Wayland) | Selector de estilos y de fondos de Default | `guru:gui-apps/rofi-wayland` | `rofi` | `rofi-wayland` | `rofi` | `rofi` |
| hyprpolkitagent | Diálogo de contraseña (polkit). En Retro lo dibuja Quickshell y no hace falta | `hyproverlay:sys-auth/hyprpolkitagent` | `hyprpolkitagent` | `copr:solopasha/hyprland:hyprpolkitagent` | `hyprpolkitagent` | — |

**Recomendado:**

| Requisito | Para qué | Gentoo | Arch / CachyOS | Fedora | openSUSE | Debian / Ubuntu |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| SwayNotificationCenter | Centro de notificaciones fuera de Retro | `guru:gui-apps/swaync` | `swaync` | `SwayNotificationCenter` | `SwayNotificationCenter` | `sway-notification-center` |
| hyprsunset | Luz nocturna que no tiñe las capturas (sin él se usa un shader) | `hyproverlay:gui-apps/hyprsunset` | `hyprsunset` | `copr:solopasha/hyprland:hyprsunset` | `hyprsunset` | — |

## Skin Retro

Imita **Omarchy 4 (basecamp/omarchy, rama quattro)**. El shell de Omarchy: su barra con plugins, menú, cuadrícula de apps, notificaciones, OSD, polkit, bloqueo y el tema de todas sus apps con capa TUI.

* **Ventanas:** mosaico (*tiling*)
* **Tema por defecto:** Paleta dinámica (formato Omarchy) (dinámico). Dinámico por defecto: genera un colors.toml de Omarchy desde el fondo. Se puede fijar cualquiera de los 23 temas estáticos de Omarchy (Alt+R) y entonces el fondo no cambia la paleta.
* **Temas:** Paleta dinámica + 23 temas de Omarchy (Tokyo Night, Catppuccin, Nord, Gruvbox, Kanagawa, Rose Pine, Everforest, Ethereal, White…).
* **Compatibilidad:** Temas y plugins de la comunidad de Omarchy (colors.toml, plugins de barra) se instalan desde Ajustes → Temas / Plugins o por Git.

| Requisito | Para qué | Gentoo | Arch / CachyOS | Fedora | openSUSE | Debian / Ubuntu |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| ImageMagick 7 (magick) | Miniaturas de temas y del selector de estilos, fondos WebP y color de texto de la barra | `media-gfx/imagemagick` | `imagemagick` | `ImageMagick` | `ImageMagick` | `imagemagick` |
| JetBrainsMono Nerd Font (todos los pesos) | Fuente del shell de Omarchy y su capa TUI | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* |

**Recomendado:**

| Requisito | Para qué | Gentoo | Arch / CachyOS | Fedora | openSUSE | Debian / Ubuntu |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| btop | Gestor de tareas de Retro (y tema btop de Omarchy) | `sys-process/btop` | `btop` | `btop` | `btop` | `btop` |
| fastfetch | «Acerca de» del menú de Retro, como en Omarchy | `app-misc/fastfetch` | `fastfetch` | `fastfetch` | `fastfetch` | `fastfetch` |
| Papirus | Iconos de Retro con las carpetas del color del tema (sin él, Adwaita) | `x11-themes/papirus-icon-theme` | `papirus-icon-theme` | `papirus-icon-theme` | `papirus-icon-theme` | `papirus-icon-theme` |
| git | Instalar temas y plugins de la comunidad y actualizar BWM | `dev-vcs/git` | `git` | `git` | `git` | `git` |
| socat | Salvapantallas de terminal (eventos de Hyprland) | `net-misc/socat` | `socat` | `socat` | `socat` | `socat` |
| hyprsunset | Luz nocturna que no tiñe las capturas (sin él se usa un shader) | `hyproverlay:gui-apps/hyprsunset` | `hyprsunset` | `copr:solopasha/hyprland:hyprsunset` | `hyprsunset` | — |

## Skin KDE Plasma

Imita **KDE Plasma 6 (Breeze Dark)**. Panel flotante, Kickoff, applets de red/Bluetooth/audio/calendario/notificaciones, Alt+Tab de KWin, OSD Breeze y barras de título Breeze con snapping.

* **Ventanas:** WM tradicional (ventanas flotantes)
* **Tema por defecto:** Breeze Dark (estático). Estático: la paleta Breeze Dark no cambia con el fondo.
* **Temas:** Breeze Dark (escritorio, GTK, Qt, kitty y apps).
* **Compatibilidad:** Objetivo: esquemas de color y temas globales de Plasma de la KDE Store aplicados al panel, applets y apps (pendiente).

| Requisito | Para qué | Gentoo | Arch / CachyOS | Fedora | openSUSE | Debian / Ubuntu |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| hyprpolkitagent | Diálogo de contraseña (polkit). En Retro lo dibuja Quickshell y no hace falta | `hyproverlay:sys-auth/hyprpolkitagent` | `hyprpolkitagent` | `copr:solopasha/hyprland:hyprpolkitagent` | `hyprpolkitagent` | — |
| Iconos Breeze | Iconos breeze-dark de las apps y applets de la skin Plasma | `kde-frameworks/breeze-icons` | `breeze-icons` | `breeze-icon-theme` | `breeze6-icons` | `breeze-icon-theme` |
| Plugin hyprbars de BWM (barras de título Breeze) | Barras de título Breeze y snapping con previsualización; debe estar compilado para el Hyprland que usas | *se compila* | *se compila* | *se compila* | *se compila* | *se compila* |

**Recomendado:**

| Requisito | Para qué | Gentoo | Arch / CachyOS | Fedora | openSUSE | Debian / Ubuntu |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| qt6ct | Paleta de la skin en las apps Qt | `gui-apps/qt6ct` | `qt6ct` | `qt6ct` | `qt6ct` | `qt6ct` |
| NetworkManager | Applets y paneles de red | `net-misc/networkmanager` | `networkmanager` | `NetworkManager` | `NetworkManager` | `network-manager` |
| nm-connection-editor | Botón «Configurar» del applet de red | `gnome-extra/nm-applet` | `nm-connection-editor` | `nm-connection-editor` | `NetworkManager-connection-editor` | `network-manager-gnome` |
| BlueZ | Applets y paneles de Bluetooth | `net-wireless/bluez` | `bluez-utils` | `bluez` | `bluez` | `bluez` |
| blueman | Botón «Configurar» del applet Bluetooth | `net-wireless/blueman` | `blueman` | `blueman` | `blueman` | `blueman` |
| SwayNotificationCenter | Centro de notificaciones fuera de Retro | `guru:gui-apps/swaync` | `swaync` | `SwayNotificationCenter` | `SwayNotificationCenter` | `sway-notification-center` |

## Plugin hyprbars (skin KDE Plasma)

Los plugins de Hyprland sólo cargan en la versión exacta para la que se compilaron (el `.so`
guarda el commit de Hyprland). `bwm check` compara ese commit con el del Hyprland que usas; si
no coinciden, `install.sh` lo recompila (`cd src/hyprbars && make && make install`, que instala con
un renombrado atómico). El plugin nuevo se carga al volver a iniciar sesión. Nunca copies el `.so`
a mano encima del cargado ni lo descargues/cargues en caliente: Hyprland cae (SIGBUS). Cuando
cambia la API interna de Hyprland hay que portearlo (referencia: el hyprbars oficial de
hyprwm/hyprland-plugins fijado a esa versión en su `hyprpm.toml`).
