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
| Qt 6 Positioning | Servicio del tiempo de Quickshell (ubicación); sin él no carga la configuración del shell | `dev-qt/qtpositioning` | `qt6-positioning` | `qt6-qtpositioning` | `qt6-positioning-imports` | `qml6-module-qtpositioning` |
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
| procps-ng (pidwait) | bwm-power espera a que las apps terminen de guardar antes de apagar (sin él, sondea) | `sys-process/procps` | `procps-ng` | `procps-ng` | `procps` | `procps` |
| git | Instalar temas y plugins de la comunidad y actualizar BWM | `dev-vcs/git` | `git` | `git` | `git` | `git` |
| Nautilus | Gestor de archivos tematizado (Super+E) | `gnome-base/nautilus` | `nautilus` | `nautilus` | `nautilus` | `nautilus` |
| Firefox | Navegador tematizado (userChrome + Pywalfox) | `www-client/firefox-bin` | `firefox` | `firefox` | `MozillaFirefox` | `firefox-esr` |
| Flatpak | Vesktop, Spotify, Stremio… tematizados con overrides | `sys-apps/flatpak` | `flatpak` | `flatpak` | `flatpak` | `flatpak` |
| FFmpeg | Primer fotograma y miniaturas de los fondos de vídeo; miniaturas del selector de fondos rofi | `media-video/ffmpeg` | `ffmpeg` | `ffmpeg-free` | `ffmpeg` | `ffmpeg` |

## Skin default (end-4)

Imita **end-4 / illogical-impulse (Material You)**. Material Design 3: barra, panel lateral, vista general y Alt+Tab de illogical-impulse. Todo el escritorio y las apps toman los colores del fondo de pantalla.

* **Ventanas:** mosaico (*tiling*)
* **Tema por defecto:** Material You desde el fondo (dinámico). Dinámico: matugen genera la paleta del fondo cada vez que lo cambias (Alt+W).
* **Temas:** Paleta dinámica de matugen (claro u oscuro según el fondo).
* **Compatibilidad:** Objetivo: plantillas y fondos de la comunidad de matugen / end-4 funcionan tal cual.

| Requisito | Para qué | Gentoo | Arch / CachyOS | Fedora | openSUSE | Debian / Ubuntu |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Colores end-4 (OpenCV, NumPy, Pillow, materialyoucolor) | Selección automática de paleta y colores de terminal originales de illogical-impulse | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* |
| matugen | Genera la paleta Material You desde el fondo (tema dinámico de default (end-4)) | `guru:x11-misc/matugen` | `aur:matugen-bin` | — | — | — |
| rofi (con Wayland) | Selector de estilos y de fondos de default (end-4) | `guru:gui-apps/rofi-wayland` | `rofi` | `rofi-wayland` | `rofi` | `rofi` |
| hyprpolkitagent | Diálogo de contraseña (polkit). En Retro lo dibuja Quickshell y no hace falta | `hyproverlay:sys-auth/hyprpolkitagent` | `hyprpolkitagent` | `copr:solopasha/hyprland:hyprpolkitagent` | `hyprpolkitagent` | — |

**Recomendado:**

| Requisito | Para qué | Gentoo | Arch / CachyOS | Fedora | openSUSE | Debian / Ubuntu |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Omacalc (calculadora de Omarchy) | Calculadora con los colores de cada skin, recarga en vivo y fuente iA Writer Mono incluida | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* |
| Compilar Omacalc (Qt 6) | Sólo durante la instalación: BWM compila la calculadora original con soporte para sus paletas | `dev-qt/qtbase` `dev-qt/qtdeclarative` `dev-vcs/git` `sys-devel/patch` | `base-devel` `qt6-base` `qt6-declarative` `git` | `gcc-c++` `make` `qt6-qtbase-devel` `qt6-qtdeclarative-devel` `git` `patch` | `gcc-c++` `make` `qt6-base-devel` `qt6-declarative-devel` `git` `patch` | `build-essential` `qt6-base-dev` `qt6-declarative-dev` `qmake6` `git` `patch` |
| SwayNotificationCenter | Centro de notificaciones fuera de Retro | `guru:gui-apps/swaync` | `swaync` | `SwayNotificationCenter` | `SwayNotificationCenter` | `sway-notification-center` |
| SongRec | Reconocer la música que suena (botón de los ajustes rápidos) | `guru:media-sound/songrec` | `songrec` | — | — | — |
| hyprsunset | Luz nocturna que no tiñe las capturas (sin él se usa un shader) | `hyproverlay:gui-apps/hyprsunset` | `hyprsunset` | `copr:solopasha/hyprland:hyprsunset` | `hyprsunset` | — |
| Colores Qt de end-4 (kde-material-you-colors) | Apps Qt de default (end-4) con la paleta del fondo, como en illogical-impulse | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* |
| Plugin de plataforma de KDE para Qt | Las apps Qt de default (end-4) leen kdeglobals (QT_QPA_PLATFORMTHEME=kde), como en end-4 | `kde-plasma/plasma-integration` | `plasma-integration` | `plasma-integration` | `plasma6-integration-plugin` | `plasma-integration` |
| Darkly (estilo de widgets Qt) | Estilo de las apps Qt de end-4 en default (end-4) | — | `aur:darkly-bin` | `copr:deltacopy/darkly:darkly` | — | — |
| mpvpaper | Fondos de vídeo en default (end-4) y Breeze (Kde plasma), como switchwall.sh de end-4; sin él se queda el primer fotograma | `guru:gui-apps/mpvpaper` | `aur:mpvpaper` | — | — | — |

## Skin Retro

Imita **Omarchy 4 (basecamp/omarchy, rama quattro)**. El shell de Omarchy: su barra con plugins, menú con configuración integrada, cuadrícula de apps, notificaciones, OSD, polkit, bloqueo y el tema de todas sus apps con capa TUI.

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
| Omacalc (calculadora de Omarchy) | Calculadora con los colores de cada skin, recarga en vivo y fuente iA Writer Mono incluida | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* |
| Compilar Omacalc (Qt 6) | Sólo durante la instalación: BWM compila la calculadora original con soporte para sus paletas | `dev-qt/qtbase` `dev-qt/qtdeclarative` `dev-vcs/git` `sys-devel/patch` | `base-devel` `qt6-base` `qt6-declarative` `git` | `gcc-c++` `make` `qt6-qtbase-devel` `qt6-qtdeclarative-devel` `git` `patch` | `gcc-c++` `make` `qt6-base-devel` `qt6-declarative-devel` `git` `patch` | `build-essential` `qt6-base-dev` `qt6-declarative-dev` `qmake6` `git` `patch` |
| btop | Gestor de tareas de Retro (y tema btop de Omarchy) | `sys-process/btop` | `btop` | `btop` | `btop` | `btop` |
| SongRec | Reconocer la música que suena (botón de los ajustes rápidos) | `guru:media-sound/songrec` | `songrec` | — | — | — |
| fastfetch | «Acerca de» del menú de Retro, como en Omarchy | `app-misc/fastfetch` | `fastfetch` | `fastfetch` | `fastfetch` | `fastfetch` |
| Papirus | Iconos de Retro con las carpetas del color del tema (sin él, Adwaita) | `x11-themes/papirus-icon-theme` | `papirus-icon-theme` | `papirus-icon-theme` | `papirus-icon-theme` | `papirus-icon-theme` |
| git | Instalar temas y plugins de la comunidad y actualizar BWM | `dev-vcs/git` | `git` | `git` | `git` | `git` |
| socat | Salvapantallas de terminal (eventos de Hyprland) | `net-misc/socat` | `socat` | `socat` | `socat` | `socat` |
| hyprsunset | Luz nocturna que no tiñe las capturas (sin él se usa un shader) | `hyproverlay:gui-apps/hyprsunset` | `hyprsunset` | `copr:solopasha/hyprland:hyprsunset` | `hyprsunset` | — |
| Salvapantallas nativo de Omarchy | Salvapantallas de Retro como capa Wayland (sin él, el de terminal en kitty); se compila con cargo | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* |
| Barras de título de Omarchy (omarchy-hyprland-titlebars) | Barras de las ventanas en los workspaces flotantes de Retro, el plugin de Omarchy sin cambios; debe estar compilado para el Hyprland que usas | *se compila* | *se compila* | *se compila* | *se compila* | *se compila* |
| Plugin GTK de Qt (gtk3) | Las apps Qt de Retro toman los colores del tema GTK, como en Omarchy (QT_QPA_PLATFORMTHEME=gtk3) | `dev-qt/qtbase[gtk]` | `qt6-base` | `qt6-qtbase-gui` | `qt6-platformtheme-gtk3` | `qt6-gtk-platformtheme` |
| Plugin WebP de Qt (qtimageformats) | El fondo de Omarchy en Retro dibuja los fondos WebP de muchos temas con su transición (sin él, BWM los convierte a JPG) | `dev-qt/qtimageformats` | `qt6-imageformats` | `qt6-qtimageformats` | `qt6-imageformats` | `qt6-image-formats-plugins` |
| OWE (fondos de vídeo de Omarchy) | Fondos de vídeo en Retro, como Omarchy 4.5 (omacom/owe; sin él se queda el primer fotograma); se compila con meson y necesita libmpv | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* |

## Skin Breeze (Kde plasma)

Imita **KDE Plasma 6 (Breeze Dark)**. Panel flotante, Kickoff, applets de red/Bluetooth/audio/calendario/notificaciones, Alt+Tab de KWin, OSD Breeze y barras de título Breeze con snapping.

* **Ventanas:** WM tradicional (ventanas flotantes)
* **Tema por defecto:** Breeze Dark (estático). Estático: la paleta Breeze Dark no cambia con el fondo.
* **Temas:** Breeze Dark (escritorio, GTK, Qt, kitty y apps).
* **Compatibilidad:** Objetivo: esquemas de color y temas globales de Plasma de la KDE Store aplicados al panel, applets y apps (pendiente).

| Requisito | Para qué | Gentoo | Arch / CachyOS | Fedora | openSUSE | Debian / Ubuntu |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| hyprpolkitagent | Diálogo de contraseña (polkit). En Retro lo dibuja Quickshell y no hace falta | `hyproverlay:sys-auth/hyprpolkitagent` | `hyprpolkitagent` | `copr:solopasha/hyprland:hyprpolkitagent` | `hyprpolkitagent` | — |
| Iconos Breeze | Iconos breeze-dark de las apps y applets de la skin Plasma | `kde-frameworks/breeze-icons` | `breeze-icons` | `breeze-icon-theme` | `breeze6-icons` | `breeze-icon-theme` |
| Plugin breezebars de BWM (barras de título Breeze) | Barras de título Breeze y snapping con previsualización; debe estar compilado para el Hyprland que usas | *se compila* | *se compila* | *se compila* | *se compila* | *se compila* |

**Recomendado:**

| Requisito | Para qué | Gentoo | Arch / CachyOS | Fedora | openSUSE | Debian / Ubuntu |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Omacalc (calculadora de Omarchy) | Calculadora con los colores de cada skin, recarga en vivo y fuente iA Writer Mono incluida | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* |
| Compilar Omacalc (Qt 6) | Sólo durante la instalación: BWM compila la calculadora original con soporte para sus paletas | `dev-qt/qtbase` `dev-qt/qtdeclarative` `dev-vcs/git` `sys-devel/patch` | `base-devel` `qt6-base` `qt6-declarative` `git` | `gcc-c++` `make` `qt6-qtbase-devel` `qt6-qtdeclarative-devel` `git` `patch` | `gcc-c++` `make` `qt6-base-devel` `qt6-declarative-devel` `git` `patch` | `build-essential` `qt6-base-dev` `qt6-declarative-dev` `qmake6` `git` `patch` |
| qt6ct | Paleta de la skin en las apps Qt | `gui-apps/qt6ct` | `qt6ct` | `qt6ct` | `qt6ct` | `qt6ct` |
| NetworkManager | Applets y paneles de red | `net-misc/networkmanager` | `networkmanager` | `NetworkManager` | `NetworkManager` | `network-manager` |
| nm-connection-editor | Botón «Configurar» del applet de red | `gnome-extra/nm-applet` | `nm-connection-editor` | `nm-connection-editor` | `NetworkManager-connection-editor` | `network-manager-gnome` |
| BlueZ | Applets y paneles de Bluetooth | `net-wireless/bluez` | `bluez-utils` | `bluez` | `bluez` | `bluez` |
| blueman | Botón «Configurar» del applet Bluetooth | `net-wireless/blueman` | `blueman` | `blueman` | `blueman` | `blueman` |
| SwayNotificationCenter | Centro de notificaciones fuera de Retro | `guru:gui-apps/swaync` | `swaync` | `SwayNotificationCenter` | `SwayNotificationCenter` | `sway-notification-center` |
| mpvpaper | Fondos de vídeo en default (end-4) y Breeze (Kde plasma), como switchwall.sh de end-4; sin él se queda el primer fotograma | `guru:gui-apps/mpvpaper` | `aur:mpvpaper` | — | — | — |

## Plugins de barras de título (Breeze (Kde plasma) y Retro)

Breeze usa `breezebars` (`src/hyprbars`, fork de hyprbars con decoraciones Breeze, detección de las
apps que traen su propia barra y snapping). Retro usa en sus workspaces flotantes el plugin de
Omarchy sin cambios, omarchy-hyprland-titlebars (`src/omarchy-titlebars`), que se registra como
`hyprbars` igual que en Omarchy. Tienen nombres distintos, así que pueden estar cargados a la vez.

Los plugins de Hyprland sólo cargan en la versión exacta para la que se compilaron (el `.so`
guarda el commit de Hyprland). `bwm check` compara ese commit con el del Hyprland que usas; si
no coinciden, `install.sh` los recompila (`make && make install` en su carpeta, que instala con
un renombrado atómico). El plugin nuevo se carga al volver a iniciar sesión. Nunca copies el `.so`
a mano encima del cargado ni lo descargues/cargues en caliente: Hyprland cae (SIGBUS). Cuando
cambia la API interna de Hyprland hay que portearlos (referencias: el hyprbars oficial de
hyprwm/hyprland-plugins fijado a esa versión en su `hyprpm.toml`, y el commit de
omarchy-hyprland-titlebars que compile con ella).
