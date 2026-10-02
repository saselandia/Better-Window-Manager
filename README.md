# 🎨 Better Window Manager (BWM) - Material You Desktop Environment

<div align="center">

**Un entorno de escritorio moderno, fluido y completamente reactivo para Wayland basado en Hyprland, Quickshell (Qt/QML) y tematización dinámica Material Design 3 (Material You).**

[![GitLab](https://img.shields.io/badge/GitLab-bwm-orange?logo=gitlab)](https://gitlab.com/saselandia/bwm)
[![GitHub](https://img.shields.io/badge/GitHub-Better--Window--Manager-blue?logo=github)](https://github.com/saselandia/Better-Window-Manager)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hyprland](https://img.shields.io/badge/Hyprland-Wayland-brightgreen)](https://hyprland.org)
[![Quickshell](https://img.shields.io/badge/Quickshell-Qt%206%20%2F%20QML-purple)](https://quickshell.outfoxxed.me)

</div>

---

## ✨ Características Principales

- 🎨 **Tematización Dinámica Material 3 (Material You):**
  - Generación instantánea de paletas tonales al cambiar de fondo de pantalla mediante `matugen`.
  - Sincronización en vivo en: **Hyprland**, **Quickshell**, terminal **Kitty**, **Rofi**, **SwayNC**, **Nautilus (GNOME Files)**, **Firefox**, **Vesktop** y **Spotify (Spicetify)**.
- 📁 **Nautilus como Gestor de Archivos Clave:**
  - Integrado de forma nativa con temas dinámicos GTK 3 y GTK 4 (`gtk.css`).
  - Sincronización automática del color de acento de GNOME (`accent-color`) y modo oscuro según el fondo seleccionado.
  - Acceso directo instantáneo con **`Super + E`** o **`Alt + E`**.
- 🚀 **Quickshell HUD y Widgets (Qt/QML):**
  - Barra superior y lateral personalizadas con monitoreo de rendimiento, tiempo, batería, red y audio MPRIS.
  - Selector visual interactivo de ventanas (**Alt + Tab**) con vistas previas en tiempo real.
  - Pantalla de bloqueo elegante y configurable con integración para autologin gráfico.
  - Menú de aplicaciones accesible pulsando la tecla **Super** con buscador integrado.
- 🌐 **Navegador Firefox Tematizado:**
  - Integración visual con `userChrome.css` y variables Material You.
  - Activación automática de hojas de estilo heredadas en todos los perfiles detectados.
- 💬 **Vesktop (Discord) con Tema Dinámico:**
  - Plantilla CSS personalizada para Vencord y QuickCSS vinculada a las paletas de Matugen.
- 🎵 **Spotify + Spicetify:**
  - Tema Material You inyectado dinámicamente con recarga automática al cambiar de wallpaper.
- 🪟 **Hyprland Modular con Lua:**
  - Configuración limpia y dividida por responsabilidades en `modules/` (apariencia, atajos, monitores, reglas de ventanas y animaciones).
  - **Reglas persistentes inteligentes:** Script en Python para recordar qué ventanas deben ser flotantes o tiled entre sesiones (**`Alt + Q`**).
- 🖼️ **Selector Visual de Fondos de Pantalla:**
  - Selector interactivo con previsualización (**`Alt + W`**) que regenera automáticamente los colores de todo el sistema.
- ⚡ **Instalador Inteligente e Idempotente:**
  - Script `install.sh` con soporte para enlaces simbólicos (`--symlink`) para recibir actualizaciones automáticas vía `git pull`, o copia independiente (`--copy`) con respaldo de seguridad automático.

---

## 📸 Galería y Vistas Previas

> 💡 **Tematización Dinámica en Tiempo Real:** Al cambiar el fondo de pantalla, **todas las aplicaciones y widgets adaptan sus colores automáticamente** al esquema tonal generado por `matugen`.

| 🎨 Aplicaciones Tematizadas (Vesktop, Nautilus, Spotify) | 🌐 Firefox con userChrome.css y Terminal Kitty |
| :---: | :---: |
| [![Vesktop, Nautilus y Spotify](assets/screenshots/01-apps-material-you.png)](assets/screenshots/01-apps-material-you.png) | [![Firefox y Kitty](assets/screenshots/02-firefox-terminal.png)](assets/screenshots/02-firefox-terminal.png) |
| **❄️ Entorno Limpio con Barra y Widgets Quickshell** | **⚡ Tema Cyberpunk de Alto Contraste con Neofetch** |
| [![Gentoo Desktop](assets/screenshots/03-desktop-clean.jpg)](assets/screenshots/03-desktop-clean.jpg) | [![Cyberpunk Theme](assets/screenshots/04-cyberpunk-neofetch.png)](assets/screenshots/04-cyberpunk-neofetch.png) |

---

## 📦 Estructura del Repositorio

```text
Better-Window-Manager/
├── config/
│   ├── hypr/               # Configuración modular de Hyprland (Lua) y scripts de automatización
│   │   ├── modules/        # Binds, apariencia, monitores, reglas, colores
│   │   └── scripts/        # Wallpapers, persistencia de ventanas, nautilus, spotify, etc.
│   ├── quickshell/         # Componentes y widgets Qt Quick / QML (Illogical Impulse)
│   ├── illogical-impulse/  # Preferencias de usuario, acciones y traducciones de la shell
│   ├── matugen/            # Plantillas de temas para exportar colores a todos los programas
│   ├── kitty/              # Configuración y temas de la terminal Kitty
│   ├── rofi/               # Temas de Rofi y selector de fondos
│   ├── swaync/             # Estilo CSS del centro de notificaciones
│   ├── gtk-3.0/            # Estilos y configuración GTK 3 (Nautilus y apps tradicionales)
│   ├── gtk-4.0/            # Estilos y configuración GTK 4 / Libadwaita (Nautilus moderno)
│   ├── firefox/            # Hojas de estilo userChrome.css dinámicas para Firefox
│   ├── spicetify/          # Tema MaterialYou (color.ini y user.css) para Spotify
│   └── xdg-desktop-portal/ # Preferencias de portales Wayland (screencast, selector de archivos)
├── assets/
│   ├── screenshots/        # Capturas de pantalla de muestra del entorno
│   └── wallpapers/         # Fondos de pantalla incluidos listos para usar
├── install.sh              # Script instalador y verificador de dependencias
├── .gitignore              # Filtro de archivos temporales, cachés y logs
└── README.md
```

---

## 🛠️ Requisitos y Dependencias

Este entorno no incluye los binarios propietarios o pesados en el repositorio git para garantizar máxima ligereza y portabilidad entre distribuciones.

### Componentes Clave del Sistema:
| Paquete | Rol |
| :--- | :--- |
| **`hyprland`** | Compositor Wayland dinámico |
| **`quickshell`** | Framework de widgets y HUD de escritorio en QML |
| **`matugen`** | Generador de paletas Material You a partir de imágenes |
| **`swww`** | Demonio de fondos de pantalla de alto rendimiento con transiciones |
| **`swaync`** | Demonio y panel gráfico de notificaciones |
| **`rofi-wayland`** | Lanzador de aplicaciones y menú dinámico |
| **`kitty`** | Terminal acelerada por GPU |
| **`nautilus`** | Explorador de archivos (GNOME Files) con tema Material You dinámico |
| **`firefox`** | Navegador web principal con soporte de `userChrome.css` |
| **`flatpak`** | Gestor de aplicaciones Flatpak (necesario para Vesktop y Spotify) |
| **`playerctl`** | Integración y control multimedia MPRIS |
| **`wl-clipboard`** | Gestión de portapapeles (`wl-copy` / `wl-paste`) |
| **`jq` & `python3`** | Procesamiento de configuraciones y automatizaciones |

### Aplicaciones Flatpak Obligatorias:
| Aplicación | ID Flatpak | Rol |
| :--- | :--- | :--- |
| **Vesktop** | `dev.vencord.Vesktop` | Cliente de Discord con Vencord integrado y soporte de CSS |
| **Spotify** | `com.spotify.Client` | Reproductor oficial de música Spotify Desktop |

> ℹ️ **Nota sobre Spicetify:** Spicetify es la herramienta CLI que inyecta los temas en Spotify. No es un paquete Flatpak; el script `install.sh` lo descarga, instala y configura de forma 100% automática.

---

### Instalación de dependencias según tu distribución:

#### Arch Linux / CachyOS:
```bash
# Dependencias del sistema:
paru -S hyprland quickshell-git matugen-bin swww swaync rofi-wayland kitty playerctl wl-clipboard jq python nautilus firefox flatpak

# Flatpaks obligatorios:
flatpak install flathub dev.vencord.Vesktop com.spotify.Client
```

#### Gentoo Linux:
```bash
# Dependencias del sistema:
emerge --ask gui-wm/hyprland gui-apps/quickshell gui-apps/swww gui-apps/swaync gui-apps/rofi-wayland x11-terms/kitty media-sound/playerctl gui-apps/wl-clipboard app-misc/jq gnome-base/nautilus www-client/firefox sys-apps/flatpak

# Flatpaks obligatorios:
flatpak install flathub dev.vencord.Vesktop com.spotify.Client
```

#### Fedora:
```bash
# Dependencias del sistema:
sudo dnf install hyprland kitty playerctl wl-clipboard jq python3 nautilus firefox flatpak

# Flatpaks obligatorios:
flatpak install flathub dev.vencord.Vesktop com.spotify.Client
```

---

## 🎨 Tematización de Aplicaciones (Nautilus, Firefox, Vesktop, Spotify)

El instalador `./install.sh` automatiza la mayor parte de la configuración. A continuación se detalla cómo funciona cada una y qué pasos manuales de verificación puedes realizar:

### 1. 📁 Nautilus (GNOME Files)
- **Automatizado:** `install.sh` instala las hojas de estilo `gtk.css` en `~/.config/gtk-3.0/` y `~/.config/gtk-4.0/`, configura el tema oscuro en GNOME (`prefer-dark` y `adw-gtk3-dark`) y ejecuta el script `sync-nautilus.sh` para calcular y aplicar el acento de color Material You más cercano en tiempo real.
- **Lanzador:** Pulsa **`Super + E`** o **`Alt + E`** en cualquier momento para abrir el gestor de archivos.

### 2. 🌐 Firefox (Binario Nativo)
- **Automatizado por `install.sh`:**
  1. Detecta todos los perfiles de Firefox existentes en `~/.mozilla/firefox/`.
  2. Crea la carpeta `chrome/` en cada perfil y copia `userChrome.css`.
  3. Enlaza `material-you.css` a la caché dinámica generada por `matugen`.
  4. Habilita automáticamente `user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);` en `user.js`.
- **Verificación / Solución manual:**
  - Si los estilos no aparecen tras reiniciar Firefox:
    1. Escribe `about:config` en la barra de direcciones de Firefox.
    2. Busca `toolkit.legacyUserProfileCustomizations.stylesheets` y asegúrate de que esté establecido en **`true`**.
    3. Reinicia Firefox.
  - *(Opcional - Sincronización en vivo del Theme API)*: Para que la barra de pestañas y botones cambien de color al vuelo sin reiniciar la ventana, instala la extensión oficial [Pywalfox](https://addons.mozilla.org/firefox/addon/pywalfox/) y pulsa una vez en **"Fetch Pywal Colors"**.

### 3. 💬 Vesktop (Discord + Vencord)
- **Automatizado por `install.sh`:**
  1. Crea las carpetas `themes/` y `settings/` dentro de `~/.var/app/dev.vencord.Vesktop/config/vesktop/`.
  2. Genera y enlaza `material-you.theme.css` y `quickCss.css`.
  3. Actualiza el archivo `settings.json` de Vesktop para activar automáticamente QuickCSS y el tema Material You.
- **Verificación manual:**
  - En Vesktop, ve a **Ajustes de usuario** → **Vencord** → **Temas** y confirma que **Material You** está habilitado.

### 4. 🎵 Spotify Desktop y Spicetify
- **Automatizado por `install.sh`:**
  1. Comprueba si `spicetify` está instalado; si no lo está, lo descarga e instala automáticamente desde el script oficial.
  2. Instala la plantilla del tema en `~/.config/spicetify/Themes/MaterialYou/`.
  3. Ajusta los permisos de escritura del Flatpak de Spotify para permitir la inyección de temas.
  4. Configura Spicetify con el tema `MaterialYou` y aplica los cambios.
- **Solución manual si Spicetify pide permisos:**
  ```bash
  # Otorgar permisos de escritura al paquete Flatpak de Spotify:
  chmod a+wr "$HOME/.local/share/flatpak/app/com.spotify.Client/x86_64/stable/active/files/extra/share/spotify" "$HOME/.local/share/flatpak/app/com.spotify.Client/x86_64/stable/active/files/extra/share/spotify/Apps" -R
  
  # Aplicar el tema manualmente:
  spicetify backup apply
  ```

---

## 🚀 Descarga e Instalación

### 1. Clonar el repositorio

Puedes descargarlo desde GitHub o GitLab:

```bash
# Desde GitHub:
git clone https://github.com/saselandia/Better-Window-Manager.git ~/dotfiles/bwm
cd ~/dotfiles/bwm

# O desde GitLab:
git clone https://gitlab.com/saselandia/bwm.git ~/dotfiles/bwm
cd ~/dotfiles/bwm
```

### 2. Ejecutar el instalador

```bash
# Modo Enlace Simbólico (Recomendado para recibir actualizaciones continuas):
./install.sh --symlink

# O Modo Copia Directa:
./install.sh --copy
```

*(Nota: En ambos modos, el instalador creará una copia de seguridad automática de cualquier configuración previa en `~/.config/`)*.

### 3. Iniciar o recargar el entorno

Si ya te encuentras dentro de una sesión de Hyprland:
```bash
hyprctl reload
```

Para aplicar tu fondo de pantalla favorito y generar la paleta de colores Material You:
```bash
# Pulsa [ALT + W] o ejecuta:
~/.config/hypr/scripts/set-wallpaper.sh /ruta/a/tu/imagen.jpg
```

---

## 🔄 Cómo Actualizar a la Última Versión

```bash
# 1. Entra a la carpeta del repositorio:
cd ~/dotfiles/bwm

# 2. Descarga la versión más reciente:
git pull

# 3. Si instalaste con enlaces simbólicos (--symlink), los cambios ya están activos.
#    Si instalaste con copia independiente (--copy), vuelve a copiar los cambios:
#    ./install.sh --copy

# 4. Recarga Hyprland para aplicar los cambios en caliente:
hyprctl reload
```

---

## ⌨️ Atajos de Teclado Principales

> Nota: En esta configuración, las teclas modificadoras principales son **`ALT`** y **`SUPER`**.

| Atajo | Acción |
| :--- | :--- |
| **`SUPER_L`** (Win) | Abrir Menú de Aplicaciones / Búsqueda en Quickshell |
| **`SUPER + E`** / **`ALT + E`** | **Lanzador: Explorador de archivos (Nautilus)** |
| **`CTRL + ENTER`** | Abrir terminal Kitty con tema dinámico |
| **`ALT + TAB`** | Selector visual de ventanas con vista previa en tiempo real |
| **`ALT + W`** | Selector gráfico de fondos de pantalla con autotematización |
| **`ALT + Q`** | Alternar y recordar regla flotante persistente para la ventana activa |
| **`ALT + X`** | Cerrar ventana activa |
| **`ALT + 1` .. `ALT + 0`** | Cambiar a los espacios de trabajo (1 al 10) |
| **`ALT + SHIFT + [1-0]`** | Mover ventana activa al espacio de trabajo correspondiente |
| **`SUPER + A`** | Abrir / Cerrar panel lateral de ajustes rápidos |
| **`SUPER + L`** | Bloquear pantalla con Quickshell Lock |
| **`SUPER + SHIFT + S`** / **`Print`** | Captura de pantalla por región |
| **`ALT + A`** | Mostrar guía interactiva de atajos en pantalla (Cheatsheet) |

---

## 🤝 Contribuciones y Desarrollo

Si deseas proponer mejoras, corregir errores o colaborar:

1. Haz un **Fork** del proyecto en GitHub o GitLab.
2. Crea una rama para tu función (`git checkout -b feature/nueva-mejora`).
3. Realiza tus cambios y haz commit (`git commit -m "feat: añadir soporte para..."`).
4. Sube tu rama (`git push origin feature/nueva-mejora`) y abre un **Pull Request** / **Merge Request**.
