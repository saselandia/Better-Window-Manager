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

## Referencias de versiones de BWMenu

Registro local: **2026-11-10**. Base de BWM: `f0b1ce757189`.

Son las versiones registradas en el entorno local de BWM, no las últimas publicadas por cada proyecto. Se usan para los semáforos; los mínimos compatibles siguen controlando la instalación y la activación de skins.

| Dependencia | Referencia BWM | Mínimo compatible |
| :--- | :--- | :--- |
| Omacalc (calculadora de Omarchy) | 1 | 1 |
| Colores end-4 (OpenCV, NumPy, Pillow, materialyoucolor) | 1 | 1 |
| Colores Qt de end-4 (kde-material-you-colors) | 1 | 1 |
| Plugin de plataforma de KDE para Qt | 6.7.5 | — |
| Plugin GTK de Qt (gtk3) | 6.11.2 | — |
| Plugin WebP de Qt (qtimageformats) | 6.11.2 | — |
| Darkly (estilo de widgets Qt) | 0.5.43 | — |
| Hyprland ≥ 0.55 | 0.56.2 | 0.55.0 |
| Quickshell | 0.3.2 | 0.2.0 |
| Qt 6 5Compat (GraphicalEffects) | 6.11.2 | — |
| Qt 6 Positioning | 6.11.2 | — |
| Qt 6 SVG | 6.11.2 | — |
| Qt ≥ 6.10 (Qt.labs.synchronizer) | 6.11.2 | — |
| Python ≥ 3.11 | 3.14.7 | 3.11 |
| Pillow (Python) | 12.3.0 | — |
| jq | 1.8.2 | — |
| swww o awww | 0.11.2 | — |
| wl-clipboard | 2.2.1 | — |
| cliphist | 0.7.0 | — |
| kitty | 0.49.2 | — |
| grim | 1.5.0 | — |
| slurp | 1.5.0 | — |
| SongRec | 0.7.3 | — |
| procps-ng (pidwait) | 4.0.6 | — |
| libnotify (notify-send) | 0.8.8 | — |
| GLib (gsettings) | 2.88.2 | — |
| fontconfig | 2.18.3 | — |
| PipeWire + WirePlumber | 0.5.18 | — |
| inotify-tools | 4.25.9.0 | — |
| matugen | 4.2.0 | — |
| rofi (con Wayland) | 1.7.8 | — |
| hyprpolkitagent | 0.2.0 | — |
| Iconos Breeze | 6.29.0 | — |
| ImageMagick 7 (magick) | 7.1.2.32 | — |
| btop | 1.4.7 | — |
| fastfetch | 2.65.2 | — |
| Papirus | 20250501 | — |
| hyprsunset | 0.4.0 | — |
| mpvpaper | 1.8 | — |
| FFmpeg | 8.1.3 | — |
| SwayNotificationCenter | 0.12.6 | — |
| blueman | 2.4.6 | — |
| nm-connection-editor | 1.36.0 | — |
| xdg-desktop-portal-hyprland | 1.4.1 | — |
| xdg-desktop-portal-gtk | 1.15.3 | — |
| playerctl | 2.4.1 | — |
| NetworkManager | 1.58.1 | — |
| BlueZ | 5.87 | — |
| qt6ct | 0.11 | — |
| socat | 1.8.1.3 | — |
| git | 2.55.0 | — |
| Nautilus | 49.6 | — |
| Firefox | 158.0.1 | — |
| Flatpak | 1.18.1 | — |
| KSvg (SVG de temas de Plasma) | 6.29.0 | — |
| libplasma (PlasmaComponents 3) | 6.7.5 | — |
| Plasma5Support | 6.7.5 | — |
| KDecoration3 | 6.7.5 | — |
| Decoración y estilo Breeze | 6.7.5 | — |
| Aurorae (decoraciones SVG) | 6.7.5 | — |
| plasma-workspace (herramientas de temas y KCMs) | 6.7.5 | — |
| Anfitrión de módulos de configuración KDE 6 | 6.29.0 | — |
| Editor original de reglas de KWin | 6.7.5 | — |
| Preferencias del sistema de KDE | 6.7.5 | — |
| plasma-nm (applet de red) | 6.7.5 | — |
| plasma-pa (applet de sonido) | 6.7.5 | — |
| BluezQt | 6.29.0 | — |
| Kirigami (componentes KDE) | 6.29.0 | — |
| Reloj de Plasma | 6.7.5 | — |
| Interfaz del reloj digital de Plasma | 6.7.5 | — |
| Gestor de actividades de KDE | 6.7.5 | — |
| Modelo MPRIS de Plasma | 6.7.5 | — |
| Calendario de Plasma | 6.7.5 | — |
| Componentes de notificaciones KDE (sin servidor) | 6.7.5 | — |
| Módulo QML org.bwm.kcm (bwm-kcmhost) | 2 | 2 |
| Agente polkit de KDE | 6.7.5 | — |
| KRunner | 6.7.5 | — |
| Resultados de KRunner | 6.7.5 | — |
| Componentes de sesión de Breeze | 6.7.5 | — |
| Traducciones de KDE (KI18n) | 6.29.0 | — |

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
| Fuente de iconos de Omarchy (omarchy.ttf) | Logo del menú y marcas de los agentes en la barra de Omarchy (Retro) | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* |
| inotify-tools | La barra de Omarchy recarga sola un plugin de ~/.config/omarchy/plugins al editarlo (inotifywait) | `sys-fs/inotify-tools` | `inotify-tools` | `inotify-tools` | `inotify-tools` | `inotify-tools` |
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
| LocalSend | Compartir portapapeles, archivos y carpetas desde el menú de Retro (Acciones → Compartir) | — | `localsend` | — | — | — |

## Skin Breeze (Kde plasma)

Imita **KDE Plasma 6 (Breeze)**. Panel flotante, Kickoff, applets de red/Bluetooth/audio/calendario/notificaciones, Alt+Tab de KWin, OSD Breeze y barras de título Breeze con snapping. Sigue el tema de Plasma activo.

* **Ventanas:** WM tradicional (ventanas flotantes)
* **Tema por defecto:** Breeze Dark (estático). Tema global Breeze Oscuro de Plasma; se cambia con los temas de Plasma (no con el fondo).
* **Temas:** Temas globales Breeze, Breeze Oscuro y Breeze Crepúsculo de Plasma; esquemas de color, estilos de Plasma e iconos instalados.
* **Compatibilidad:** Formatos originales de Plasma: esquemas, estilos SVG, iconos, decoraciones KDecoration/Aurorae y temas globales. Cursor común controlado por BWM. Límites y comprobaciones: docs/BREEZE_F13_RESULTS.md.

| Requisito | Para qué | Gentoo | Arch / CachyOS | Fedora | openSUSE | Debian / Ubuntu |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Iconos Breeze | Iconos breeze-dark de las apps y applets de la skin Plasma | `kde-frameworks/breeze-icons` | `breeze-icons` | `breeze-icon-theme` | `breeze6-icons` | `breeze-icon-theme` |
| Plugin breezebars de BWM (barras de título Breeze) | Barras de título Breeze y snapping con previsualización; debe estar compilado para el Hyprland que usas | *se compila* | *se compila* | *se compila* | *se compila* | *se compila* |
| KSvg (SVG de temas de Plasma) | Pinta el panel, los popups y los controles de Breeze con el estilo de Plasma activo (desktoptheme) | `kde-frameworks/ksvg` | `ksvg` | `kf6-ksvg` | — | — |
| libplasma (PlasmaComponents 3) | Controles de Plasma (botones, menús, deslizadores) con el tema de Plasma en el shell de Breeze | `kde-plasma/libplasma` | `libplasma` | `libplasma` | — | — |
| Kirigami (componentes KDE) | Iconos, fuentes y métricas de los componentes portados del panel Plasma | `kde-frameworks/kirigami` | `kirigami` | `kf6-kirigami` | — | `qml6-module-org-kde-kirigami` |
| plasma-workspace (herramientas de temas y KCMs) | plasma-apply-*, lookandfeeltool, módulos de Preferencias (colores, estilo de Plasma, iconos, cursores, fuentes, tema global) y modelos de Kickoff/bandeja. Instala KWin, pero BWM no lo ejecuta | `kde-plasma/plasma-workspace` | `plasma-workspace` | `plasma-workspace` | — | `plasma-workspace` |
| Reloj de Plasma | Fuente de hora del reloj digital portado de Plasma | `kde-plasma/plasma-workspace` | `plasma-workspace` | `plasma-workspace` | — | `plasma-workspace` |
| Interfaz del reloj digital de Plasma | Formato y traducciones de zonas horarias del reloj nativo de Plasma | `kde-plasma/plasma-workspace` | `plasma-workspace` | `plasma-workspace` | — | `plasma-workspace` |
| plasma-nm (applet de red) | Modelos de red del applet de Plasma (org.kde.plasma.networkmanagement) | `kde-plasma/plasma-nm` | `plasma-nm` | `plasma-nm` | — | `plasma-nm` |
| plasma-pa (applet de sonido) | Modelos de sonido del applet de Plasma (org.kde.plasma.private.volume) | `kde-plasma/plasma-pa` | `plasma-pa` | `plasma-pa` | — | `plasma-pa` |
| Modelo MPRIS de Plasma | Interfaz de los applets portados de Breeze, sin arrancar plasmashell ni sus servidores | `kde-plasma/plasma-workspace` | `plasma-workspace` | `plasma-workspace` | — | `plasma-workspace` |
| Calendario de Plasma | Interfaz de los applets portados de Breeze, sin arrancar plasmashell ni sus servidores | `kde-plasma/plasma-workspace` | `plasma-workspace` | `plasma-workspace` | — | `plasma-workspace` |
| Componentes de notificaciones KDE (sin servidor) | Interfaz de los applets portados de Breeze, sin arrancar plasmashell ni sus servidores | `kde-plasma/plasma-workspace` | `plasma-workspace` | `plasma-workspace` | — | `plasma-workspace` |
| Agente polkit de KDE | Un único diálogo de autenticación nativo de KDE en Breeze | `kde-plasma/polkit-kde-agent` | `polkit-kde-agent` | `polkit-kde` | `polkit-kde-agent-6` | `polkit-kde-agent-1` |
| KRunner | Alt+Espacio nativo de Plasma, aplicaciones, cálculo y comandos, sin plasmashell | `kde-plasma/plasma-workspace` | `plasma-workspace` | `plasma-workspace` | `plasma6-workspace` | `plasma-workspace` |
| Resultados de KRunner | Interfaz nativa de Plasma en Breeze (F12) | `kde-plasma/milou` | `milou` | `milou` | `milou6` | `milou` |
| Componentes de sesión de Breeze | Interfaz nativa de Plasma en Breeze (F12) | `kde-plasma/plasma-workspace` | `plasma-workspace` | `plasma-workspace` | `plasma6-workspace` | `plasma-workspace` |
| Noto Sans | Fuente general original de KDE Plasma (10 pt) | `media-fonts/noto` | `noto-fonts` | `google-noto-sans-fonts` | `google-noto-sans-fonts` | `fonts-noto-core` |
| Hack | Fuente monoespaciada predeterminada de KDE Plasma | `media-fonts/hack` | `ttf-hack` | `source-foundry-hack-fonts` | `hack-fonts` | `fonts-hack` |

**Recomendado:**

| Requisito | Para qué | Gentoo | Arch / CachyOS | Fedora | openSUSE | Debian / Ubuntu |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| gio (GLib) | Abrir un archivo reciente con su aplicación desde el menú del gestor de tareas de Breeze | `dev-libs/glib` | `glib2` | `glib2` | `glib2-tools` | `libglib2.0-bin` |
| xdg-open (xdg-utils) | Abrir la imagen de fondo desde el menú del escritorio de Breeze | `x11-misc/xdg-utils` | `xdg-utils` | `xdg-utils` | `xdg-utils` | `xdg-utils` |
| Omacalc (calculadora de Omarchy) | Calculadora con los colores de cada skin, recarga en vivo y fuente iA Writer Mono incluida | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* | *lo trae BWM* |
| Compilar Omacalc (Qt 6) | Sólo durante la instalación: BWM compila la calculadora original con soporte para sus paletas | `dev-qt/qtbase` `dev-qt/qtdeclarative` `dev-vcs/git` `sys-devel/patch` | `base-devel` `qt6-base` `qt6-declarative` `git` | `gcc-c++` `make` `qt6-qtbase-devel` `qt6-qtdeclarative-devel` `git` `patch` | `gcc-c++` `make` `qt6-base-devel` `qt6-declarative-devel` `git` `patch` | `build-essential` `qt6-base-dev` `qt6-declarative-dev` `qmake6` `git` `patch` |
| qt6ct | Paleta de la skin en las apps Qt | `gui-apps/qt6ct` | `qt6ct` | `qt6ct` | `qt6ct` | `qt6ct` |
| NetworkManager | Applets y paneles de red | `net-misc/networkmanager` | `networkmanager` | `NetworkManager` | `NetworkManager` | `network-manager` |
| nm-connection-editor | Botón «Configurar» del applet de red | `gnome-extra/nm-applet` | `nm-connection-editor` | `nm-connection-editor` | `NetworkManager-connection-editor` | `network-manager-gnome` |
| BlueZ | Applets y paneles de Bluetooth | `net-wireless/bluez` | `bluez-utils` | `bluez` | `bluez` | `bluez` |
| blueman | Botón «Configurar» del applet Bluetooth | `net-wireless/blueman` | `blueman` | `blueman` | `blueman` | `blueman` |
| SwayNotificationCenter | Centro de notificaciones fuera de Retro | `guru:gui-apps/swaync` | `swaync` | `SwayNotificationCenter` | `SwayNotificationCenter` | `sway-notification-center` |
| mpvpaper | Fondos de vídeo en default (end-4) y Breeze (Kde plasma), como switchwall.sh de end-4; sin él se queda el primer fotograma | `guru:gui-apps/mpvpaper` | `aur:mpvpaper` | — | — | — |
| Plasma5Support | Fuentes de datos que usan los plasmoides portados (reloj, energía) | `kde-plasma/plasma5support` | `plasma5support` | — | — | — |
| KDecoration3 | Biblioteca de decoraciones de KWin: BWM la usa para dibujar las barras de título del tema de Plasma activo | `kde-plasma/kdecoration` | `kdecoration` | `kdecoration` | — | — |
| Decoración y estilo Breeze | Barras de título Breeze reales y estilo de widgets Breeze | `kde-plasma/breeze` | `breeze` | `plasma-breeze` | — | `breeze` |
| Aurorae (decoraciones SVG) | Decoraciones de ventana de la KDE Store en formato Aurorae | `kde-plasma/aurorae` | `aurorae` | `aurorae` | — | — |
| Preferencias del sistema de KDE | Base de las Preferencias del sistema de Breeze (KCMs con kcmshell6) | `kde-plasma/systemsettings` | `systemsettings` | `plasma-systemsettings` | — | `systemsettings` |
| BluezQt | Modelos de Bluetooth del applet de Plasma (org.kde.bluezqt) | `kde-frameworks/bluez-qt` | `bluez-qt` | `kf6-bluez-qt` | — | — |
| Kvantum (estilo de widgets Qt) | Muchos temas globales de la KDE Store (Sweet, Layan…) piden el estilo de aplicaciones Kvantum; sin él las apps Qt vuelven a Breeze/Fusion | `x11-themes/kvantum` | `kvantum` | `kvantum` | — | — |
| Gestor de actividades de KDE | Favoritos y recientes del Kickoff de Breeze (KActivities, el formato de Plasma) | `kde-plasma/kactivitymanagerd` | `kactivitymanagerd` | `kactivitymanagerd` | — | `kactivitymanagerd` |
| Auxiliar de decoraciones de BWM (bwm-decorator) | Dibuja las decoraciones reales de KDE (Breeze, Aurorae, de terceros) para las barras de título de Breeze | — | — | — | — | — |
| Módulo QML org.bwm.kcm (bwm-kcmhost) | Incrusta los KCM reales de Plasma (colores, estilo, decoraciones, tema global, iconos, fuentes…) en las Preferencias del sistema de Breeze | — | — | — | — | — |
| Anfitrión de módulos de configuración KDE 6 | Abrir el editor original de reglas de KWin desde los menús de Breeze | `kde-frameworks/kcmutils` | `kcmutils` | `kf6-kcmutils` | `kf6-kcmutils` | `libkf6kcmutils-bin` |
| Editor original de reglas de KWin | Editar kwinrulesrc con kcm_kwinrules; el compositor KWin no se ejecuta | `kde-plasma/kwin` | `kwin` | `kwin` | — | `kwin-common` |
| Traducciones de KDE (KI18n) | Contexto de traducción de los temas Plasma cargados con ThemeHost | `kde-frameworks/ki18n` | `ki18n` | `kf6-ki18n-devel` | `kf6-ki18n-devel` | `libkf6i18n-dev` |

## Plugins de barras de título (Breeze (Kde plasma) y Retro)

Breeze usa `breezebars` (`src/breezebars`, fork de hyprbars con decoraciones Breeze, detección de las
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
