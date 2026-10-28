# 🪟 Better Window Manager (BWM)

<div align="center">

**Un gestor de ventanas que reúne a todos los demás como _skins_.**
Default (end-4 / illogical-impulse), Retro (Omarchy) y KDE Plasma sobre Hyprland y Quickshell: cambia de uno a otro sin cerrar nada y las aplicaciones cambian con él.

<p align="center">
  <a href="README.md">English</a> • <b>Español</b>
</p>

[![GitLab](https://img.shields.io/badge/GitLab-bwm-orange?logo=gitlab)](https://gitlab.com/saselandia/bwm)
[![GitHub](https://img.shields.io/badge/GitHub-Better--Window--Manager-blue?logo=github)](https://github.com/saselandia/Better-Window-Manager)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hyprland](https://img.shields.io/badge/Hyprland-Wayland-brightgreen)](https://hyprland.org)
[![Quickshell](https://img.shields.io/badge/Quickshell-Qt%206%20%2F%20QML-purple)](https://quickshell.outfoxxed.me)

</div>

---

## 🧭 Qué es BWM

**BWM (Better Window Manager) es un gestor de ventanas que trata de encapsular todos los gestores de ventanas y escritorios que existen como _skins_.** Cada skin reproduce otro escritorio —su barra, sus menús, sus paneles, sus atajos y sus temas— sobre el mismo compositor (Hyprland) y el mismo shell (Quickshell), y todo el sistema le sigue: GTK, Qt, terminales, Firefox, Vesktop, Spotify, Steam, la pantalla de bloqueo y la de inicio de sesión. Se cambia de skin en caliente con **`Alt + T`**.

**La meta es la compatibilidad.** Cada skin debe aceptar los temas y mejoras de aspecto de su escritorio original: si estás en la skin KDE Plasma y te bajas un tema de Plasma de internet, debe aplicarse y funcionar; si estás en Retro y añades un tema o un plugin de Omarchy, igual. BWM tiene pocas interfaces propias; casi todo es la interfaz de cada escritorio original.

### Skins incluidas

| Skin | Imita | Tema por defecto | Otros temas | Compatibilidad buscada |
| :--- | :--- | :--- | :--- | :--- |
| **Default** | [end-4 / illogical-impulse](https://github.com/end-4/dots-hyprland) (Material You) | **Dinámico**: matugen saca la paleta del fondo cada vez que lo cambias | — (claro u oscuro según el fondo) | Plantillas y fondos de matugen / end-4 |
| **Retro** | [Omarchy 4](https://github.com/basecamp/omarchy) (rama `quattro`) | **Dinámico**: paleta con el formato de Omarchy sacada del fondo | 23 temas estáticos de Omarchy (Tokyo Night, Catppuccin, Nord, Gruvbox…) con `Alt + R`; al fijar uno, el fondo ya no cambia los colores | Temas y plugins de la comunidad de Omarchy (Ajustes → Temas / Plugins) |
| **KDE Plasma** | KDE Plasma 6 (Breeze Dark) | **Estático**: Breeze Dark, no cambia con el fondo | — | Esquemas de color y temas globales de Plasma de la KDE Store (pendiente) |

Más skins: [docs/SKINS.md](docs/SKINS.md) explica qué es una skin y cómo se añade.

## 👋 Bienvenida y comando `bwm`

Tras instalar, cada inicio de sesión abre una ventana de bienvenida estilo asistente (como Calamares) que te da las gracias, enseña las skins instaladas —**en verde** las que tienen todos sus requisitos—, despliega los requisitos de cada una con los comandos para instalar lo que falte, permite activarlas y enlaza la wiki para añadir skins. Se desactiva con el interruptor «Mostrar al iniciar sesión».

```bash
bwm                 # abre la bienvenida (también sin haber terminado de instalar)
bwm check           # requisitos del núcleo y de cada skin, con los comandos para tu distro
bwm skins           # skins instaladas
bwm skin retro      # cambia de skin (comprueba antes sus requisitos)
bwm startup off     # que la bienvenida no se abra al iniciar sesión
```

## ✨ Características Principales

- 🎨 **Tematización Dinámica en Tiempo Real:** Cambia tu fondo de pantalla y todo el escritorio (ventanas, paneles, terminal y aplicaciones) adapta sus colores al instante.
- 🖥️ **Gestor Interactivo de Pantallas y Monitores:** Configura resolución, tasa de refresco (Hz), escala y organiza monitores visualmente con **arrastre con ratón (drag & drop)** y acoplamiento magnético.
- 🖱️ **Gestor de Temas de Cursor y Hyprcursor:** Cambia fácilmente de tema de cursor (compatible con Hyprcursor y XCursor) y personaliza el tamaño (de 20px a 48px) mediante interfaz gráfica, con zona de pruebas interactiva y temas Bibata Material Design incluidos.
- 📁 **Explorador Nautilus Integrado:** Abre tu gestor de archivos con **`Super + E`** o **`Alt + E`**, con modo oscuro y colores de acento sincronizados.
- 🚀 **Panel y Widgets Quickshell:** Barra superior con métricas de sistema, panel lateral de ajustes rápidos y selector de ventanas (**`Alt + Tab`**) con vista previa en directo.
- 🔍 **Menú de Aplicaciones:** Acceso rápido a tus apps y buscador integrado pulsando la tecla **`Super`**.
- 🌐 **Firefox, Vesktop y Spotify Tematizados:** Integración visual completa en tus aplicaciones diarias con colores dinámicos.
- 🪟 **Ventanas Flotantes Persistentes:** Recuerda qué aplicaciones prefieres en modo flotante o en mosaico entre sesiones con **`Alt + Q`**.
- 🖼️ **Selector de Fondos Visual:** Elige fondos de pantalla cómodamente con vista previa pulsando **`Alt + W`**.
- ⚡ **Instalador Rápido:** Configuración automatizada con un solo comando vía `install.sh`.

---

## 📸 Galería y Vistas Previas

> 💡 **Tematización Dinámica en Tiempo Real:** Al cambiar el fondo de pantalla, **todas las aplicaciones y widgets adaptan sus colores automáticamente** al esquema tonal generado por `matugen`.

| 🎨 Aplicaciones Tematizadas (Vesktop, Nautilus, Spotify) | 🌐 Firefox con userChrome.css y Terminal Kitty |
| :---: | :---: |
| [![Vesktop, Nautilus y Spotify](assets/screenshots/01-apps-material-you.png)](assets/screenshots/01-apps-material-you.png) | [![Firefox y Kitty](assets/screenshots/02-firefox-terminal.png)](assets/screenshots/02-firefox-terminal.png) |
| **❄️ Entorno Limpio con Barra y Widgets Quickshell** | **⚡ Tema Cyberpunk de Alto Contraste con Neofetch** |
| [![Gentoo Desktop](assets/screenshots/03-desktop-clean.jpg)](assets/screenshots/03-desktop-clean.jpg) | [![Cyberpunk Theme](assets/screenshots/04-cyberpunk-neofetch.png)](assets/screenshots/04-cyberpunk-neofetch.png) |

---

## 🛠️ Requisitos

El instalador **comprueba todo antes de tocar nada**: si falta algo, te dice qué, para qué sirve y te da los comandos de tu distribución (Gentoo, Arch/CachyOS, Fedora, openSUSE, Debian/Ubuntu; en las demás, la guía), y sale. Puedes comprobarlo cuando quieras:

```bash
./install.sh --check       # o, ya instalado: bwm check
```

La lista completa, con los paquetes de cada distribución, está en [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) y sale de `config/hypr/skins/*.json`. En resumen:

| | Necesita |
| :--- | :--- |
| **Núcleo** (todas las skins) | Hyprland ≥ 0.55 (configuración en Lua), Quickshell (probado con 0.3.1), Qt ≥ 6.10 con 5Compat y SVG, Python ≥ 3.11 con Pillow, jq, swww, wl-clipboard, cliphist, kitty, grim, slurp, libnotify, GLib, fontconfig, PipeWire/WirePlumber, adw-gtk3. Las fuentes (Material Symbols, Google Sans Flex, JetBrainsMono Nerd Font) las instala BWM |
| **Default** | matugen, rofi (Wayland), hyprpolkitagent |
| **Retro** | ImageMagick 7 (`magick`). Polkit, notificaciones y OSD los dibuja Quickshell |
| **KDE Plasma** | hyprpolkitagent, iconos Breeze y el plugin hyprbars de BWM **compilado para tu versión de Hyprland** (el instalador lo compila si tienes las cabeceras de Hyprland, `make` y un compilador de C++) |

Opcional: portales de escritorio (hyprland, gtk), NetworkManager, BlueZ, qt6ct, socat, git, Nautilus, Firefox, Flatpak (Vesktop, Spotify, Stremio), btop, fastfetch, Papirus, hyprsunset, SDDM y Plymouth.

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
./install.sh            # comprueba requisitos, enlaza ~/.config al repo y aplica los temas
./install.sh --check    # sólo comprueba los requisitos
./install.sh --skins default,retro   # sólo algunas skins
./install.sh --copy     # copia en vez de enlazar
```

Si falta un requisito, el instalador se detiene **sin cambiar nada** y te da los comandos para instalarlo. Si todo está, respalda tu configuración previa de `~/.config`, enlaza las configuraciones, instala fuentes y cursores, crea el comando `bwm`, compila el plugin de Plasma si tu Hyprland es otra versión, tematiza las apps que tengas y activa la bienvenida.

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

### 4. Inicio de sesión y pantalla de arranque (estilo Omarchy)

`install.sh` ofrece configurarlo (o usa `--login` / `--no-login`). Hace lo mismo que el instalador de Omarchy: SDDM con el tema de inicio de sesión de Omarchy (logo de BWM, colores del estilo activo) dentro de un Hyprland mínimo con tu teclado y tus monitores, recordando el último usuario y la última sesión. Después un servicio root actualiza los colores en cada cambio de fondo o de tema. A mano:

```bash
sudo ~/.config/hypr/scripts/install-boot-theme.sh --all            # SDDM + actualización automática
sudo ~/.config/hypr/scripts/install-boot-theme.sh --sddm --autologin   # sin contraseña (disco cifrado, como Omarchy)
sudo ~/.config/hypr/scripts/install-boot-theme.sh --disable-sddm   # volver al inicio anterior (autologin en tty1)
sudo ~/.config/hypr/scripts/install-boot-theme.sh --plymouth       # pantalla de arranque (rehace el initramfs)
sudo ~/.config/hypr/scripts/install-boot-theme.sh --revert         # quitar la pantalla de arranque
```

La pantalla de arranque es opcional: rehace el initramfs con dracut (con los mismos drivers de GPU y descartándolo si crece más de un 50 %) y añade `splash` al `grub.cfg` existente sin regenerarlo. Guarda copias y `--revert` las restaura.

### 5. Plugins de la barra de Omarchy (estilo Retro)

La barra Retro ejecuta **plugins del shell de Omarchy** sin cambios: las librerías `qs.Commons` / `qs.Ui` de Omarchy (MIT) van incluidas en `config/quickshell/ii/Commons` y `Ui` y leen la paleta Omarchy de BWM. El reloj de Omarchy con su calendario desplegable forma parte de la barra Retro. Estos plugins vienen **preinstalados y activos** (`config/quickshell/ii/omarchy-plugins`, todos MIT): el tiempo y Elsewhen (relojes del mundo) de Omarchy tras el reloj, uso de IA (`ai-usagebar`, cuyo programa compila `install.sh` con cargo), OmaStats, controles multimedia con carátula del disco y ventana activa. Cada uno se desactiva en **Ajustes → Barra** (Retro). Más plugins, como con `omarchy plugin add`:

```bash
~/.config/hypr/scripts/bwm-plugin.sh add https://github.com/<usuario>/<plugin>.git [--section left|center|centerEnd|right]
~/.config/hypr/scripts/bwm-plugin.sh list | update | enable <id> | disable <id> | remove <id> | build
```

Los plugins son código sin aislar que corre dentro de la barra (igual que en Omarchy): revisa los que añadas.

---

## 🎨 Verificaciones Manuales de Aplicaciones

El instalador `./install.sh` se encarga de configurar y vincular los temas de todas las aplicaciones automáticamente. Si necesitas realizar alguna comprobación puntual o ajuste manual:

### 1. 📁 Nautilus (Explorador de Archivos)
- **Lanzador:** Pulsa **`Super + E`** o **`Alt + E`** en cualquier momento para abrir el gestor de archivos con el tema y acento activos.

### 2. 🌐 Firefox
- **Habilitar Pywalfox y estilos de usuario:**
  - El instalador despliega automáticamente `userChrome.css`, la extensión `pywalfox.xpi` en tu perfil de Firefox y configura el host nativo en el sistema.
  - Al abrir Firefox, si aparece una notificación indicando que se ha añadido la extensión Pywalfox, haz clic en **"Habilitar"** (Enable).
  - En la barra de herramientas de Firefox, haz clic en el icono de **Pywalfox** y pulsa una vez en **"Fetch Pywal Colors"** para sincronizar la barra de pestañas en vivo.
  - *(Comprobación opcional)*: Si por algún motivo los estilos personalizados no cargan, entra en `about:config` y confirma que `toolkit.legacyUserProfileCustomizations.stylesheets` esté en **`true`**.

### 3. 💬 Vesktop (Discord)
- **Verificación de tema:** En Vesktop, abre **Ajustes de usuario** → **Vencord** → **Temas** y confirma que el tema **bwm.theme.css** está habilitado (cambia de nombre y colores con la skin).

### 4. 🎵 Spotify Desktop y Spicetify
- **Permisos de escritura para Flatpak:** Si Spicetify solicita permisos para inyectar el tema en el Flatpak de Spotify, ejecuta:
  ```bash
  chmod a+wr "$HOME/.local/share/flatpak/app/com.spotify.Client/x86_64/stable/active/files/extra/share/spotify" "$HOME/.local/share/flatpak/app/com.spotify.Client/x86_64/stable/active/files/extra/share/spotify/Apps" -R
  spicetify backup apply
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

## 💖 Créditos y Agradecimientos

Este proyecto se inspira y construye sobre el excelente trabajo de la comunidad:

- **[end-4 / dots-hyprland](https://github.com/end-4/dots-hyprland)**: Base fundamental e inspiración para los widgets de Quickshell (Illogical Impulse), animaciones y sistema de temas Material You.
- **[Hyprland](https://hyprland.org)**: Compositor Wayland fluido, dinámico y extensible.
- **[Quickshell](https://quickshell.outfoxxed.me)**: Framework flexible para widgets y barras de escritorio en Qt 6 / QML.
- **[Matugen](https://github.com/InioX/matugen)**: Generador dinámico de paletas de color Material Design 3.
- **[Omarchy](https://github.com/basecamp/omarchy)** (MIT): plantillas de apps del estilo Retro, temas de Plymouth y SDDM, el saludo de SDDM en Hyprland, bloqueo estilo hyprlock, salvapantallas, modo glass y selector de fuente.

---

## 🤝 Contribuciones y Desarrollo

Si deseas proponer mejoras, corregir errores o colaborar:

1. Haz un **Fork** del proyecto en GitHub o GitLab.
2. Crea una rama para tu función (`git checkout -b feature/nueva-mejora`).
3. Realiza tus cambios y haz commit (`git commit -m "feat: añadir soporte para..."`).
4. Sube tu rama (`git push origin feature/nueva-mejora`) y abre un **Pull Request** / **Merge Request**.
