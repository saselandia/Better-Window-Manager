# 🌌 Better Window Manager (BWM) - Material You Hyprland Desktop

Entorno de escritorio moderno, dinámico y estético basado en **Hyprland** (con configuración modular en **Lua**), widgets en **Quickshell** (Qt 6 / QML) y sincronización de paletas dinámicas en tiempo real con **Matugen** (Material You / M3).

---

## ✨ Características Principales

- 🎨 **Tematización Dinámica Material 3 (Material You):**
  - Generación instantánea de paletas tonales al cambiar de fondo de pantalla mediante `matugen`.
  - Sincronización en vivo de bordes de ventanas en Hyprland, widgets de Quickshell, terminal Kitty, Rofi, SwayNC y temas GTK 3 / GTK 4.
- 🚀 **Quickshell HUD y Widgets (Qt/QML):**
  - Barra superior y lateral personalizadas con monitoreo de rendimiento, tiempo, batería, red y audio MPRIS.
  - Selector visual interactivo de ventanas (**Alt + Tab**) con vistas previas en tiempo real.
  - Pantalla de bloqueo elegante y configurable con integración para autologin gráfico.
  - Búsqueda integrada y lanzador de aplicaciones con acceso directo a emojis y portapapeles.
- 🪟 **Hyprland Modular con Lua:**
  - Configuración limpia y dividida por responsabilidades en `modules/` (apariencia, atajos, monitores, reglas de ventanas y animaciones).
  - **Reglas persistentes inteligentes:** Script en Python para recordar qué ventanas deben ser flotantes o tiled entre sesiones (`ALT + Q`).
- 🖼️ **Selector Visual de Fondos de Pantalla:**
  - Selector interactivo con previsualización (`ALT + W`) que regenera automáticamente los colores de todo el sistema.
- ⚡ **Instalador Inteligente e Idempotente:**
  - Script `install.sh` con soporte para enlaces simbólicos (`--symlink`) para recibir actualizaciones automáticas vía `git pull`, o copia independiente (`--copy`) con respaldo de seguridad automático.

---

## 📦 Estructura del Repositorio

```text
Better-Window-Manager/
├── config/
│   ├── hypr/               # Configuración modular de Hyprland (Lua) y scripts de automatización
│   │   ├── modules/        # Binds, apariencia, monitores, reglas, colores
│   │   └── scripts/        # Wallpapers, persistencia de ventanas, autostart, etc.
│   ├── quickshell/         # Componentes y widgets Qt Quick / QML (Illogical Impulse)
│   ├── illogical-impulse/  # Preferencias de usuario, acciones y traducciones de la shell
│   ├── matugen/            # Plantillas de temas para exportar colores a todos los programas
│   ├── kitty/              # Configuración y temas de la terminal Kitty
│   ├── rofi/               # Temas de Rofi y selector de fondos
│   ├── swaync/             # Estilo CSS del centro de notificaciones
│   └── xdg-desktop-portal/ # Preferencias de portales Wayland (screencast, selector de archivos)
├── assets/
│   └── wallpapers/         # Fondos de pantalla incluidos listos para usar
├── install.sh              # Script instalador y verificador de dependencias
├── .gitignore              # Filtro de archivos temporales, cachés y logs
└── README.md
```

---

## 🛠️ Requisitos y Dependencias

Este entorno no incluye los paquetes binarios del sistema para que puedas instalar las versiones nativas u optimizadas de tu distribución Linux favorita.

### Componentes Clave:
| Paquete | Rol |
| :--- | :--- |
| **`hyprland`** | Compositor Wayland dinámico |
| **`quickshell`** | Framework de widgets y HUD de escritorio en QML |
| **`matugen`** | Generador de paletas Material You a partir de imágenes |
| **`swww`** | Demonio de fondos de pantalla de alto rendimiento con transiciones |
| **`swaync`** | Demonio y panel gráfico de notificaciones |
| **`rofi-wayland`** | Lanzador de aplicaciones y menú dinámico |
| **`kitty`** | Terminal acelerada por GPU |
| **`playerctl`** | Integración y control multimedia MPRIS |
| **`wl-clipboard`** | Gestión de portapapeles (`wl-copy` / `wl-paste`) |
| **`jq` & `python3`** | Procesamiento de configuraciones y automatizaciones |

### Instalación de dependencias según tu distribución:

#### Arch Linux / CachyOS:
```bash
paru -S hyprland quickshell-git matugen-bin swww swaync rofi-wayland kitty playerctl wl-clipboard jq python
```

#### Gentoo Linux:
```bash
emerge --ask gui-wm/hyprland gui-apps/quickshell gui-apps/swww gui-apps/swaync gui-apps/rofi-wayland x11-terms/kitty media-sound/playerctl gui-apps/wl-clipboard app-misc/jq
```

#### Fedora:
```bash
sudo dnf install hyprland kitty playerctl wl-clipboard jq python3
# Instala quickshell, matugen y swww desde COPR o compilados según tu configuración
```

---

## 🚀 Descarga e Instalación

### 1. Clonar el repositorio

Puedes descargarlo desde GitHub o GitLab según prefieras:

```bash
# Desde GitHub:
git clone https://github.com/saselandia/Better-Window-Manager.git ~/dotfiles/bwm
cd ~/dotfiles/bwm

# O desde GitLab:
git clone https://gitlab.com/saselandia/bwm.git ~/dotfiles/bwm
cd ~/dotfiles/bwm
```

### 2. Ejecutar el instalador

El instalador ofrece dos métodos de instalación:

- **Modo Enlace Simbólico (Recomendado):**
  Crea accesos directos desde `~/.config/` hacia la carpeta del repositorio. Esto permite que **cualquier actualización futura que descargues con `git pull` se aplique al instante** en tu sistema sin tener que volver a copiar archivos.
  ```bash
  ./install.sh --symlink
  ```

- **Modo Copia Directa:**
  Copia los archivos de configuración directamente a tu carpeta `~/.config/` de forma independiente.
  ```bash
  ./install.sh --copy
  ```

*(Nota: En ambos modos, el instalador creará una copia de seguridad automática de cualquier configuración previa que tengas en `~/.config/`)*.

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

Para descargar las últimas mejoras, correcciones y novedades publicadas en el proyecto:

```bash
# 1. Entra a la carpeta donde descargaste el repositorio:
cd ~/dotfiles/bwm   # o la ruta donde lo hayas clonado

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

> Nota: En esta configuración, la tecla principal modificadora está configurada en `ALT` (o `SUPER` según la función).

| Atajo | Acción |
| :--- | :--- |
| `SUPER_L` (Win) | Abrir Menú de Aplicaciones / Búsqueda en Quickshell |
| `CTRL + ENTER` | Abrir terminal Kitty con tema dinámico |
| `ALT + TAB` | Selector visual de ventanas con vista previa |
| `ALT + W` | Selector gráfico de fondos de pantalla con autotematización |
| `ALT + Q` | Alternar y recordar regla flotante persistente para la ventana activa |
| `ALT + X` | Cerrar ventana activa |
| `ALT + 1` .. `ALT + 0` | Cambiar a los espacios de trabajo (1 al 10) |
| `ALT + SHIFT + [1-0]` | Mover ventana activa al espacio de trabajo correspondiente |
| `SUPER + A` | Abrir / Cerrar panel lateral de ajustes rápidos |
| `SUPER + L` | Bloquear pantalla con Quickshell Lock |
| `SUPER + SHIFT + S` / `Print` | Captura de pantalla por región |
| `ALT + A` | Mostrar guía de atajos en pantalla (Cheatsheet) |

---

## 🤝 Contribuciones y Desarrollo

Si deseas proponer mejoras, corregir errores o colaborar:

1. Haz un **Fork** del proyecto en GitHub o GitLab.
2. Crea una rama para tu función (`git checkout -b feature/nueva-mejora`).
3. Realiza tus cambios y haz commit (`git commit -m "feat: añadir soporte para..."`).
4. Sube tu rama (`git push origin feature/nueva-mejora`) y abre un **Pull Request** / **Merge Request**.
