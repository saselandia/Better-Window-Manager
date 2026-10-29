# BWM (Better Window Manager) — Resumen de Contexto para PLM

Documento sintético para traspaso y continuidad entre agentes de IA.
Última actualización: 2026-10-27.

---

## 1. Objetivo del Proyecto, Alcance y Resultado Esperado

* **Objetivo:** Entorno de escritorio Wayland completo, modular y de alto rendimiento basado en **Hyprland 0.55.4 (configurado en Lua)** y **Quickshell (Qt 6 / QML)** sobre **Gentoo Linux**.
* **Alcance:** Tres estilos (*skins*) intercambiables en caliente mediante un único comando:
  1. `default`: Material You dinámico generado desde el fondo con `matugen` y barra/paneles de illogical-impulse.
  2. `plasma`: Clon fidedigno de KDE Plasma 6 Breeze Dark con panel flotante/pegado, Kickoff, applets Breeze (Bluetooth, Red, Audio, Calendario, Notificaciones), Alt+Tab tipo KWin y barras de título CSD con snapping interactivo.
  3. `retro`: Clon completo de Omarchy 4 (*quattro*, MIT) con 23 temas estáticos o paleta dinámica, barra con plugins modulares, cuadrícula de apps, lanzador, OSD, polkit propio y tematización profunda de apps.
* **Resultado Esperado:** Experiencia de escritorio sólida para uso diario con monitor dual (4K + 1080p@144) sobre hardware híbrido AMD/NVIDIA, con sincronización de temas en apps nativas, Flatpak y navegadores.

---

## 2. Requisitos, Preferencias y Restricciones Críticas

* **Idioma:** Español en toda comunicación, comentarios y documentación.
* **Monitores:** LG UltraFine 4K (`1920x0`, 60 Hz) y HP X24ih 1080p@144 (`0x1080`, principal). **Identificar SIEMPRE por `desc:`**, jamás por `DP-N` (el orden de inicialización de GPU NVIDIA / AMD iGPU altera los conectores).
* **Arranque y Kernel:** `/boot` en disco cifrado con LUKS y llave en initramfs (`dracut --hostonly`). **NUNCA ejecutar `grub-mkconfig`** (la línea `rd.luks...` no está en `/etc/default/grub`). Temas SDDM/Plymouth solo mediante `config/hypr/scripts/install-boot-theme.sh`.
* **Plugins C++ de Hyprland (`src/hyprbars`, `src/csd-minimize`):**
  - Compilar con `-fno-gnu-unique`.
  - Desplegar **ÚNICAMENTE con `make install`** (copia temporal + `mv` atómico).
  - **NUNCA `cp` directo sobre un `.so` cargado** ni `hyprctl plugin unload/load` en caliente (provoca SIGBUS, cuelgue y *safe mode*).
* **Quickshell:** **NUNCA arrancar dos instancias (`qs -c ii`)**. Reiniciar mediante `bwm-theme-manager.py set <estilo>` (~10 s). Probar cambios aislados en archivos temporales con `qs -p`.
* **Dueño Único:** Polkit y `org.freedesktop.Notifications` solo admiten un proveedor a la vez: en Retro los gestiona Quickshell; fuera de Retro, `hyprpolkitagent` y `swaync`.
* **Gestión de Ventanas:** Identificar ventanas reiniciadas por **PID**, no por `address` de Hyprland (se reutilizan direcciones).
* **Maximizaciones Automáticas Prohibidas:** Regla global `suppress_event = "maximize"` en Hyprland y `remember_window_size no` en Kitty para evitar que apps recuerden o fuercen maximizado al arrancar. Alt+Enter controla el tamaño (maximizado en Plasma; fullscreen en Default/Retro).
* **Sudo y Sistema:** Operaciones con `sudo` (Portage, dispatch-conf, etc.) las ejecuta el usuario; proporcionar el comando exacto.
* **Reglas de Agentes y Git:** `AGENTS.md` y `CLAUDE.md` deben mantenerse idénticos. Añadir nueva sección en §3 y actualizar §2 de `BWM_CONTEXT.md` tras cambios relevantes. No incluir archivos generados en commits salvo orden expresa del usuario ("commitear todo").

---

## 3. Arquitectura y Tecnologías

* **Compositor:** Hyprland 0.55.4 (`v0.55.4`, commit `a0136d8c`), configurado enteramente en Lua (`config/hypr/hyprland.lua` y `modules/*.lua`).
* **Shell Gráfico:** Quickshell (Qt 6 / QML / C++), configuración `ii` (derivada de illogical-impulse de end-4).
* **Plugins C++ Propios:**
  - `hyprbars-plasma`: Soporte de barras de ventana Breeze con detección de CSD nativa (`CSDDetect.cpp` vía `xdg-decoration` y `_MOTIF_WM_HINTS`), y renderizado de previsualización traslúcida de snapping (`SnapHelper.hpp`, `CRenderPass`).
  - `csd-minimize`: Minimizado de ventanas para integración con paneles.
* **Motor de Tematización:**
  - `bwm-theme-manager.py`: Orquestador de estilos, perfiles de Quickshell (`config-<estilo>.json`) y recargas.
  - `bwm_omarchy.py` y `bwm_omarchy_apps.py`: Motor Retro, paletas TOML, 23 temas estáticos y plantillas.
  - `gtk-theme.py`: Alterna temas `BWM-1` y `BWM-2` en GTK 3 para forzar recarga en vivo sin reiniciar aplicaciones.
  - `matugen`: Generación de paletas Material You desde fondos de pantalla.
  - `stremio-theme.py/.cjs`: Inyección en vivo de temas CSS en la interfaz web de Stremio Flatpak.
  - `nightlight.py`: Luz nocturna con backend `hyprsunset` o shader GLSL 300 es (`nightlight.frag`).
* **Sistema:** Gentoo Linux x86_64, systemd (sesión usuario), kernel `7.2.5-cachyos`, hardware híbrido AMD Ryzen 9 7900 + NVIDIA.

---

## 4. Archivos y Rutas Relevantes (Relativas al Repo)

* `BWM_CONTEXT.md`: Memoria completa del proyecto (§2 estado actual, §3 historial cronológico).
* `AGENTS.md` / `CLAUDE.md`: Reglas operativas estrictas para asistentes.
* `todo.md`: Tareas completadas y pendientes priorizadas.
* `config/hypr/hyprland.lua`: Punto de entrada de Hyprland (importa `modules/*`).
* `config/hypr/keybinds.json`: Fuente de verdad de atajos de teclado.
* `config/hypr/modules/`:
  - `rules.lua`: Reglas de ventanas, flotabilidad, render y supresión de maximizado.
  - `nightlight.lua`: Persistencia del shader de luz nocturna tras recargas.
  - `user_binds.lua`: Atajos generados por `keybinds-manager.py`.
* `config/hypr/scripts/`:
  - `bwm-theme-manager.py`: Gestor CLI de estilos (`get|set|toggle|list`).
  - `bwm-addons.py`: Backend de búsqueda, descarga e instalación Git de temas y plugins.
  - `nightlight.py`: Control de luz nocturna unificado.
  - `window-guard.py`: Daemon de monitorización de juegos, primary XWayland y ventanas perdidas.
  - `omarchy-shims/`: Comandos CLI emulados de Omarchy (`omarchy-launch-about`, `omarchy-toggle-nightlight`, etc.).
* `config/quickshell/ii/`:
  - `shell.qml`, `settings.qml`, `plasmaSettings.qml`: Entradas de la interfaz.
  - `modules/settings/`: Páginas de configuración (`ThemesConfig.qml`, `PluginsConfig.qml`, `About.qml`, `addons/`).
  - `modules/ii/bar/RetroBarContent.qml`: Barra Retro con widgets fijos y plugins dinámicos.
  - `modules/ii/plasma*/`: Componentes visuales y applets del estilo Plasma.
* `src/hyprbars/`: Código C++ del plugin de barras Breeze y snapping.
* Enlaces externos en `~/.config`: `hypr`, `quickshell`, `illogical-impulse`, `rofi`, `kitty`, `matugen`, `swaync`, `gtk-3.0`, `gtk-4.0`, `xdg-desktop-portal`, `nvim` apuntan directamente a este repositorio.

---

## 5. Estado Actual: Hechos Comprobados vs Pendientes

### Hechos Comprobados y Verificados
* **Ajustes (Temas y Plugins):** Páginas separadas operativas con catálogos remotos, filtros (Todos/Activados/Desactivados), miniaturas y soporte de clonación por Git (`bwm-addons.py`).
* **Ventana About:** Diferenciación completada: About del menú Retro ejecuta Fastfetch en ventana flotante con tamaño y posición corregidos (`omarchy-launch-about`); About de Ajustes muestra tarjeta del sistema autodetectada (`SystemInfoData.js`) y enlaces del proyecto.
* **Supresión de Maximizado Espurio:** Bloqueo verificado mediante `suppress_event = "maximize"` y `remember_window_size no` en Kitty; ventanas respetan modo flotante/tiling sin expandirse indebidamente.
* **Luz Nocturna:** Corregido error en QML (`ToggleSwitch`); `nightlight.py` conmuta limpiamente aplicando shader GLSL y persistiendo tras `hyprctl reload`.
* **Git:** Repositorio en rama `main` limpio y sincronizado con remotos en el commit `ffc33e1`.

### Supuestos y Operaciones No Verificadas
* **Actualización del Sistema Gentoo:** No se ha confirmado si el usuario completó la actualización `@world` ni si resolvió las configuraciones de `dispatch-conf` en su terminal.
* **Daemon `hyprsunset`:** No comprobado en vivo porque el paquete no está instalado (el sistema usa correctamente el fallback GLSL).

### Tareas Pendientes
1. Portar el menú Estilo completo de Omarchy (barra opaca/transparente, 12/24 h, esquinas, huecos, animaciones, branding).
2. Layouts por workspace (dwindle/scrolling/flotante) y ciclado con `Super+L`.
3. Atajos de ventanas pendientes (Super+Ctrl+F, Super+Alt+F, Super+O, scratchpad Super+S, consola Quake Super+`).
4. Adaptar instaladores de software (`omarchy-install/remove`, Web Apps, TUIs) a Portage y Flatpak.
5. Completar el actualizador de Gentoo en BWM (sync, sudo eselect news, dispatch-conf, preserved-rebuild).
6. Solucionar recarga en caliente de temas Qt en aplicaciones abiertas sin reiniciar.

---

## 6. Decisiones Tomadas y Alternativas Descartadas

* **Despliegue atómico de plugins C++:** Se descartó el `cp` simple porque truncaba el archivo `.so` en memoria, causando crash por SIGBUS en Hyprland. Se adoptó `make install` (copia temporal + `mv` atómico).
* **Detección CSD en tiempo de ejecución:** Descartadas las listas estáticas de ventanas en Lua; `CSDDetect.cpp` consulta directamente los protocolos Wayland (`xdg-decoration`) y X11 (`_MOTIF_WM_HINTS`).
* **Monitores por descripción:** Descartada la nomenclatura `DP-1` / `DP-2`; se usa `desc:` para evitar intercambios de posición causados por el orden de carga de los controladores de GPU.
* **Temas GTK 3 alternados:** GTK 3 no relee `gtk.css` sin reiniciar; alternar entre nombres `BWM-1` y `BWM-2` en `settings.ini` fuerza la relectura inmediata.
* **Vesktop edit in-place:** Descartado el reemplazo atómico de archivo en `themes/bwm.theme.css`; Electron vigila por inodo (`fs.watch`), por lo que se sobrescribe el archivo existente directamente.
* **Maximizaciones en el compositor:** Descartado intentar anular el maximizado solo con flags de Kitty; la regla `suppress_event = "maximize"` a nivel de Hyprland erradica el problema en todas las aplicaciones preservando el fullscreen para juegos.
* **Fastfetch en About Retro:** Se mantuvo Fastfetch original de Omarchy en terminal dedicado en vez de duplicar la interfaz QML, respetando la identidad del estilo Retro.

---

## 7. Comandos de Instalación, Ejecución y Pruebas

```bash
# Hyprland: recargar configuración y verificar errores de sintaxis
hyprctl reload && hyprctl configerrors

# Gestor de estilos BWM
python3 config/hypr/scripts/bwm-theme-manager.py get
python3 config/hypr/scripts/bwm-theme-manager.py set retro   # reinicia Quickshell (~10s)

# Quickshell: inspección y depuración
qs -c ii log | tail -50     # comprobar errores de carga en la instancia real
qs -c ii ipc show           # comprobar paneles cargados en IPC

# Gestión de temas Retro
omarchy-theme-list
omarchy-theme-set tokyo-night
omarchy-theme-current

# Compilación segura de plugins C++ (aplican al reiniciar sesión)
cd src/hyprbars && make clean && make && make install

# Diagnóstico de decoraciones CSD en Plasma
hyprctl hyprbars-csd

# Pruebas unitarias y de sintaxis
python3 -m unittest discover config/hypr/scripts/tests/
python3 -m py_compile config/hypr/scripts/*.py
bash -n config/hypr/scripts/*.sh
```

---

## 8. Errores Conocidos, Riesgos y Bloqueos

* **Cifrado LUKS y GRUB:** Riesgo de rotura del arranque si se ejecuta `grub-mkconfig`. Seguir exclusivamente `install-boot-theme.sh`.
* **Colisión de Quickshell:** Si se invoca `qs -c ii` manualmente con una instancia corriendo, se crean paneles duplicados y cuelgues.
* **Permisos en Portage:** `eselect news` y `dispatch-conf` fallan si no se ejecutan con `sudo`.
* **Recarga de Qt:** `qt6ct` no refresca paletas en aplicaciones Qt ya abiertas; requieren reinicio manual de la aplicación.
* **Pkill accidental:** Evitar `pkill -f` con patrones genéricos que puedan coincidir con la shell del asistente.

---

## 9. Próximos Pasos Priorizados para el Siguiente Agente

1. **Menú Estilo Retro (`bwm-menu.jsonc`):** Implementar conmutadores para opacidad de barra, formato de reloj 12/24 h, visualización de batería y redondeos/huecos.
2. **Layouts de Espacios de Trabajo:** Desarrollar el conmutador dinámico de layouts (dwindle / scrolling / flotante) y vincularlo al atajo `Super+L`.
3. **Atajos de Teclado Faltantes:** Registrar en `keybinds.json` y regenerar con `keybinds-manager.py` los atajos pendientes (`Super+Ctrl+F`, `Super+Alt+F`, `Super+O`, `Super+S`, `Super+\``).
4. **Instaladores de Aplicaciones:** Adaptar las rutinas de instalación de Web Apps y terminales TUI para usar `emerge` / `flatpak` en vez del `pacman` original de Omarchy.

---

## 10. Información de Repositorios y Estado de Git

* **Ruta Local:** `/mnt/HDD1TB/Projects/hyprland-de` (enlace simbólico `~/Projects/hyprland-de`).
* **Rama Actual:** `main`.
* **Remotos Configurados:**
  - `origin`:
    - Fetch: `git@gitlab.com:saselandia/bwm.git`
    - Push: `git@gitlab.com:saselandia/bwm.git` Y `git@github.com:saselandia/Better-Window-Manager.git` (push simultáneo).
  - `gitlab`: `git@gitlab.com:saselandia/bwm.git`
  - `github`: `git@github.com:saselandia/Better-Window-Manager.git`
* **Commits Clave Recientes:**
  - `ffc33e1`: `feat(bwm): improve settings, Omarchy addons and window behavior` (HEAD -> main, origin/main).
  - `0bcdbd4`: `feat: addons manager, About, nightlight fix, maximize suppression, bar tweaks`.
  - `d2462ac`: `chore(bwm): consolidate context and pending desktop changes`.
* **Estado de Trabajo:** Árbol de trabajo completamente limpio (`working tree clean`), sin cambios locales pendientes ni desvíos con `origin/main`.
