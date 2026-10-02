# 🌌 Material You Hyprland Desktop Environment

Entorno de escritorio moderno, dinámico y estético basado en **Hyprland** (con configuración modular en **Lua**), widgets en **Quickshell** (Qt 6 / QML) y sincronización de paletas dinámicas en tiempo real con **Matugen** (Material You / M3).

---

## ✨ Características Principales

- 🎨 **Tematización Dinámica Material 3 (Material You):**
  - Generación instantánea de paletas tonales al cambiar de fondo de pantalla mediante `matugen`.
  - Sincronización en vivo de bordes de ventanas en Hyprland, widgets de Quickshell, terminal Kitty, Rofi, SwayNC y temas GTK 3 / GTK 4.
- 🚀 **Quickshell HUD y Widgets (Qt/QML):**
  - Barra superior y lateral personalizadas con monitoreo de rendimiento, tiempo, batería, red y audio MPRIS.
  - Selector visual interactivo de ventanas (**Alt + Tab**) con vistas previas.
  - Pantalla de bloqueo elegante y configurable con integración para autologin gráfico.
  - Búsqueda integrada y lanzador de aplicaciones con acceso directo a emojis y portapapeles.
- 🪟 **Hyprland Modular con Lua:**
  - Configuración limpia y dividida por responsabilidades en `modules/` (apariencia, atajos, monitores, reglas de ventanas y animaciones).
  - **Reglas persistentes inteligentes:** Script en Python para recordar qué ventanas deben ser flotantes o tiled entre sesiones (`ALT + Q`).
- 🖼️ **Selector Visual de Fondos de Pantalla:**
  - Selector interactivo con previsualización (`ALT + W`) que regenera automáticamente los colores de todo el sistema.
- ⚡ **Instalador Idempotente:**
  - Script `install.sh` con soporte para enlaces simbólicos (`--symlink`) para desarrollo activo o copia directa (`--copy`) con copias de seguridad automáticas.

---

## 📦 Estructura del Repositorio

```text
hyprland-de/
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

## 🚀 Instalación y Despliegue

1. **Clona el repositorio:**
   ```bash
   git clone <URL_DE_TU_REPOSITORIO> ~/Projects/hyprland-de
   cd ~/Projects/hyprland-de
   ```

2. **Ejecuta el instalador:**
   - **Modo Enlace Simbólico (Recomendado):** Enlaza `~/.config/*` directamente a este repositorio, de modo que cualquier ajuste que hagas en tu escritorio quede automáticamente registrado para subirlo a Git:
     ```bash
     ./install.sh --symlink
     ```
   - **Modo Copia Simple:**
     ```bash
     ./install.sh --copy
     ```

3. **Inicia o recarga Hyprland:**
   Si ya estás en una sesión de Hyprland:
   ```bash
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

## 🔄 Flujo de Trabajo y Actualizaciones en Git

Si instalaste con `--symlink`, cualquier cambio que hagas en tus archivos de `~/.config/` se reflejará directamente en el repositorio local.

Para guardar y subir tus cambios a GitLab / GitHub:

```bash
cd ~/Projects/hyprland-de

# Ver cambios realizados
git status

# Añadir cambios y crear commit
git add .
git commit -m "feat: actualizar ajustes de la barra y reglas de ventanas"

# Subir al repositorio
git push
```
