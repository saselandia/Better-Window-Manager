# Omarchy 4.5: qué trae y qué hacemos con ello (estudio de 2026-11-08)

> Fuente: clon sin blobs de `github.com/basecamp/omarchy` (MIT), leído el 2026-11-08.
> `v4.5.0` es del 2026-11-04 (`ac2690cd`); `quattro` está en `d9cc361c` (2026-11-08). La versión del
> archivo `version` sigue siendo `4.0.0.alpha`. Las notas de la release no se pudieron leer
> (no hay `gh`): la lista sale de los 362 commits de `quattro` desde el 2026-10-23, que es de donde
> partió BWM, y de comparar lo vendido con el árbol de `quattro`. No se ejecutó nada de Omarchy.
> Alcance: sin atajos nuevos (petición del usuario). Lo marcado «(atajo)» queda sólo anotado.

## 1. Qué hay de nuevo

**Shell y barra (lo que más afecta a Retro)**
* Reglas de movimiento (`Style.duration`): los paneles «crecen» desde la barra, se transforman de uno a
  otro y cierran más rápido; botones e iconos de barra «ceden» bajo el puntero; el color de la barra
  se desvanece 250 ms al cambiar de tema; tooltips que aparecen al instante si ya hay uno. En BWM
  `Ui/` y `Commons/` van por detrás (todos los archivos de `Ui/` difieren y falta `PopupMenuRow.qml`).
* Pantallas: panel con una pantalla a la vez y mapa de distribución (girar con clic derecho),
  frecuencias de refresco, escala persistida por monitor, `monitors.lua` migrado sin solapes,
  `GDK_SCALE` de la pantalla de menor escala. BWM ya tiene su propio panel (§3.67) con 1908 líneas de diferencia.
* Notificaciones: control con teclado (atajo), botones de acción (`omarchy-notification-send --action/--exec`),
  Abrir/Editar en capturas, Abrir/Cortar en grabaciones, mazos apilados (Taildrop), animación de entrada/salida.
  Se retiraron el panel de notificaciones y el «posponer».
* Fondos: introducciones al cambiar de fondo, cambio deslizante en todos los monitores sin parpadeo negro,
  fondo de vídeo con fotograma fijo en el bloqueo.
* Salvapantallas **nativo de Wayland** (sustituye al de terminal), con gracia al lanzar y sin bloquear si
  volviste.
* Bloqueo: sigue usable tras el cambio de VT de una suspensión con NVIDIA; retroiluminación del teclado.
* Agentes: panel con todos los agentes y proveedores (≈25 colectores de uso), cuentas
  (añadir/usar/renombrar/`--reauth`), modelos locales con catálogo de recetas, consola Quake sembrada con el
  selector de agente, integración con herdr (app de escritorio). Instaladores `omarchy-install-ai-*`.
* Nuevos paneles propios: Elsewhen (globo con relojes), Dropbox, Tailscale rehecho (+448 líneas), servicio
  `remote-session`, clima como panel, dock como plugin.
* Dictado: backends Hex, Superwhisper y Voxtype (atajos: Alt+Espacio / Alt derecha).
* Ventanas y teclado (atajos, sólo anotado): ciclar el layout de workspace con la tecla de pantalla,
  Alt+Mayús+Tab hacia atrás, «seleccionar todo» universal, Super+coma que actúa sobre la última notificación,
  gestos de touchpad por defecto, teclas multimedia/fila superior, copiar/pegar universal.
* Hyprland por defecto: silenciar la campana del sistema, sin ventana de soporte, SDR en pantalla completa con
  HDR, animaciones apagadas con render por CPU, sin rtkit para Hyprland (rtkit sí para PipeWire).
* Temas: Jade Horse sustituye a Osaka Jade (éste se instala desde su repo), fondos nuevos de ethereal/hackerman,
  temas de Slack, Herdr, OpenCode 2, panel de diff de Claude Code, Hunk y `omarchy-theme-set-glass`,
  `omarchy-toggle-theme-sync`.

**Sistema (propio de Arch/Omarchy)**: Apple Silicon, Snapdragon, ASUS Zenbook, N1x, kernel `linux-omarchy`,
módulos NVIDIA precompilados, propiedad de paquetes, keyring, `pacman`, canales stable/rc/dev, migraciones
(105 nuevas desde 4.0.6), `omarchy update` con un solo `sudo`, sshd sólo con clave autorizada.

## 2. Seguridad

Revisado contra BWM:

| Cambio upstream | En BWM |
| :--- | :--- |
| Inyección Lua por nombre de dispositivo en `omarchy-toggle-input-device` (rama `fix/input-device-lua-injection`, nuevo `omarchy-lua-quote`) | No aplica: BWM no tiene ese script. Los nombres de monitor que van a `hyprctl eval` ya se validan con regex (`omarchy-hyprland-monitor-scaling/-clamshell`) y las reglas de `bwm_windows.py` usan `json.dumps` |
| Escapado del nombre de webapp (`security/backport-webapp-name`) | No aplica: `omarchy-launch-webapp` sólo hace `xdg-open` |
| sshd/asdcontrol, `sudo` ordinario, keyring, `pacman` | Propio de Arch, no aplica |
| `Security.js` de notificaciones (política de URLs y argv) | Idéntico al de upstream |
| Notificaciones `transient` no se guardaban en disco | **Corregido**: `omarchyNotifications/Service.qml` (`storePut`) las escribía en `~/.local/state/omarchy/notifications/live.json` y de ahí al historial (códigos de un solo uso, avisos de gestores de contraseñas) |
| `--reauth` sin cuenta añadía una cuenta | **Corregido** en `omarchy-agent-account-add` |

Revisado y sin cambios: `bwm-addons.py` (sólo https, sin hooks de git, ids por regex), `install-boot-theme.sh`
(solo archivos regulares con nombres de tema, campos validados) y `omarchy-tailscale-receive` (más
estricto que upstream: no decodifica miniaturas de archivos recibidos; se conserva).

Pendiente / observaciones: el historial que ya existe puede contener notificaciones transitorias antiguas
(no se ha tocado: es contenido privado); `json.dumps` con `ensure_ascii` produce `\uXXXX`, que Lua rechaza
(rompería una regla para una clase con caracteres no ASCII, no es inyección); `omarchy-launch-webapp`
pasa `$1` a `xdg-open` sin validar el esquema.

## 3. Qué añadir y qué no (sin atajos)

**Sí, por orden**
1. ~~Refrescar `Commons/` y `Ui/` de upstream~~ **Hecho el 2026-11-08** (§3.100 de `BWM_CONTEXT.md`). Las
   diferencias eran menores de lo que parecía: un solo líder de IPC por destino, lectura síncrona de catálogos,
   `PopupMenuRow`, desplegables que se cierran con un segundo clic y deslizadores que llegan al final. Las reglas
   de movimiento están en los plugins/paneles, no en `Ui/`: llegarán al traer cada panel.
2. ~~**Panel de agentes y Tailscale al día**~~ **Hecho el 2026-11-08** (§3.102 de `BWM_CONTEXT.md`): ambos de
   `quattro` `d9cc361c`, con los 23 colectores de uso y sin los modelos locales (necesitan `omarchy-local-ai`,
   podman y paquetes de Arch). El panel de agentes no funcionaba antes en BWM: faltaba `OMARCHY_PATH`.
3. ~~**Salvapantallas nativo de Wayland**~~ **Hecho el 2026-11-08** (§3.103): es un programa aparte en Rust
   (`omacom/omarchy-screensaver`, MIT); BWM lo compila con cargo (`skins/retro/scripts/install-screensaver.sh`) y
   lo usa con el logo de BWM. Sin él sigue el de terminal.
4. ~~**Hyprland de Retro**~~ **Hecho el 2026-11-08** (§3.103, `skins/retro/hypr/misc.lua`): SDR en pantalla
   completa (`cm_auto_hdr = 0`); campanilla y aviso de donación protegidos, porque Hyprland 0.56.2 aún no
   tiene esas opciones. Las animaciones apagadas con render por CPU no se portan: este equipo tiene NVIDIA.
5. ~~**Cambio deslizante de fondo sin parpadeo negro**~~ **Ya estaba** (§3.104): el fondo de Retro
   (`omarchyBackground`, §3.94) se copió de `598e4eb`, que ya incluye ese cambio (#17179), y no ha cambiado desde
   entonces. El negro tras reconectar un monitor lo resolvió §3.81.
6. ~~**Notificaciones**~~ **Hecho el 2026-11-08** (§3.104): `Service.qml` y `omarchy-notification-send` iguales a
   upstream (`--transient`, ventana de apps con nombres de varias palabras, IPC `notifications act`). Sin el atajo
   Super+coma.

**Quizá más adelante**: panel Elsewhen/clima/Dropbox propios (BWM ya trae `omarchy-elsewhen` y `omarchy-weather`
como plugins; Dropbox sólo si lo usa el usuario), dictado (`voxtype` etc. necesitan paquetes y micrófono), modelos
locales (CUDA/container toolkit: coste alto). Hechos después: fondos con introducción (§3.116 de `BWM_CONTEXT.md`)
y Jade Horse (§3.110).

**No**: todo lo de Arch/hardware (Apple, Snapdragon, ASUS, kernel `linux-omarchy`, módulos NVIDIA, keyring,
`pacman`, canales, migraciones, `omarchy update`): BWM actualiza con Portage (§2.7 de `BWM_CONTEXT.md`) y
mezclarlo rompería el arranque cifrado. Tampoco el panel de notificaciones retirado, ni el sshd/`sudo` de
Omarchy, ni instaladores de servicios (Slack, Microsoft) que BWM no gestiona.

## 4. Lo que faltaba en este estudio (revisión del 2026-11-08)

La primera pasada miró sobre todo lo vendido en BWM. Repasando los commits de funciones desde octubre
salen piezas que no estaban en la lista, algunas anteriores al 2026-10-23 pero nunca portadas.

### 4.1 Escritorio tradicional: workspaces flotantes con barras de título

Omarchy tiene desde el 2026-10-11 (#14482, ampliado hasta 4.5) un **modo por workspace**: cada workspace
es `dwindle` (mosaico), `scrolling` o `floating`, y `omarchy-hyprland-workspace-layout-toggle` (Super+L,
y desde 4.5 la tecla de pantalla) los recorre. `omarchy-hyprland-workspace-layout-default` fija el modo
de los workspaces sin uno propio; un workspace con ventanas conserva el suyo al cambiar el predeterminado.
El modo de cada workspace se guarda en `~/.local/state/omarchy/workspace-layouts/<n>.lua` y lo reponen
`default/hypr/workspace-layouts.lua` y `workspace-modes.lua` (573 líneas) al cargar la configuración.

Cómo funciona el modo flotante (Hyprland no tiene un layout flotante, así que se hace sobre las ventanas):
* Etiqueta `omarchy-mode-floated` en las ventanas que el modo hizo flotar (sólo esas vuelven a mosaico al
  salir) y `omarchy-floating-workspace` en todas las del workspace (barra, sombra y opacidad siguen a esa
  etiqueta, también en diálogos). Las etiquetas viven en la ventana: sobreviven a recargas y la siguen
  entre workspaces.
* Las ventanas nuevas flotan desde el primer fotograma por una regla `r[a-b]` con tamaño
  `min(1100, 64 %) × min(760, 68 %)`, centradas y en cascada de 24 px; los diálogos modales y las apps con
  regla flotante propia se respetan. Fullscreen y fijadas no se tocan.
* Clic para enfocar (`follow_mouse = 0`) sólo mientras el workspace activo flota; sombras y opacidad 1
  para distinguir ventanas superpuestas. Una ventana maximizada vuelve a su tamaño al abrirse otra.
* Barras de título con su plugin, **omarchy-hyprland-titlebars** (fork de hyprbars, BSD-3 + MIT, en
  `omacom/omarchy-hyprland-titlebars`): se registra como `hyprbars` con la misma API Lua
  (`hl.plugin.hyprbars.add_button`), y añade `workspace_tag` (barra sólo en ventanas con esa etiqueta),
  `bar_color_inactive`, `%WINDOW%` en las acciones de los botones y el título tomado del `.desktop` de la
  app. Colores del tema (`lighter_background`/`selection`), botones × □ − (− minimiza al dock), doble clic
  maximiza, arrastrar una maximizada la devuelve a su tamaño bajo el puntero.
* El dock de Omarchy aparece en los workspaces flotantes (#15263; BWM ya lo imita con un shim que llama
  «flotante» a un workspace sin ventanas en mosaico).

**Frente a Breeze (Kde plasma) de BWM:** BWM decide el modo por skin (`"windows": "traditional"` en
`skin.json`, todo flota en Plasma) y Omarchy por workspace dentro de la misma skin. El plugin de Omarchy y
el `hyprbars-plasma` de BWM son dos forks de hyprbars **con el mismo nombre de plugin**: no pueden estar
cargados a la vez. El de BWM ya tiene detección de CSD, iconos Breeze, snapping con previsualización y
minimizar; le faltan `workspace_tag` y `%WINDOW%` (que evita que un botón actúe sobre otra ventana si el
foco cambia antes de ejecutarse). Lo útil para Breeze: las etiquetas en la ventana en vez de estado
propio, abrir flotando desde el primer fotograma con tamaño y cascada, clic para enfocar sólo donde hay
superposición, y desmaximizar al abrirse otra ventana.

**Hecho (§3.106–3.108 de `BWM_CONTEXT.md`):** modo por workspace en Retro con el plugin de barras de Omarchy sin cambios (el de Breeze, renombrado `breezebars`, queda aparte), clic para enfocar en Breeze, cambio desde la barra y el menú (sin Super+L).

**Propuesta original:** portar el modo por workspace a Retro (estaba en §2.6 de `BWM_CONTEXT.md` como pendiente),
usando el `hyprbars-plasma` de BWM con `workspace_tag` y `%WINDOW%` añadidos, en vez de un segundo plugin;
y llevar a `bwm_windows.py`/Breeze las ideas de la lista anterior. Sin atajos nuevos mientras siga la
petición de no añadirlos (el recorrido de modos quedaría en el menú de Retro).

### 4.2 Temas que cambian las decoraciones

El README del plugin cita los temas **Omarchy 98** y **Windows XP**, que traen su propio fork de hyprbars
(`omacom/omarchy-98-theme`, no accesible sin cuenta el 2026-11-08). Es justo la finalidad de BWM (temas
del original que funcionan en su skin): hoy BWM no carga plugins que vengan con un tema de Omarchy.
Pendiente de estudiar cuando se pueda leer uno de esos temas.

### 4.3 Workspaces por monitor

`monitor-workspaces.lua` (#15655, 674 líneas, como Niri): cada monitor tiene sus workspaces 1-10 (bloques
de 10 por monitor físico, identificado por marca, modelo y número de serie), Super+3 va al tercero del
monitor con foco y los de un monitor desenchufado vuelven a él al reconectarlo. BWM numera los workspaces
de forma global y común a todas las skins (regla 14).

**Decidido (2026-11-09): no.** Lo de Omarchy son bloques de ids (11–20 para el segundo monitor), no un modelo
propio de Hyprland, y BWM depende de que un id sea único (modos de workspace, etiquetas de minimizado,
autoarranque, primario de XWayland, barra y dock). Los escritorios que imitan las skins (KDE, end-4, Omarchy)
son globales. El uso de este equipo (1–9 en el principal, el 10 fijo en el secundario por `desc:`) ya
recupera los workspaces de un monitor al reconectarlo.

### 4.4 Otras novedades sin portar

* ~~**Introducciones de fondo**~~ (#16875, #16877, #16884): **hecho** (§3.116), con OWE en Retro.
* **Panel de pantallas**: una pantalla cada vez con mapa de distribución, girar desde el mapa, Extender |
  Duplicar y frecuencias (#17159…#17232). Comparado (§3.116): el editor de BWM (§3.67) ya tiene mapa,
  giro, frecuencias, escala, principal y apagar. Falta **Duplicar** (espejo); pendiente.
* ~~**Motion rules**~~ (#16889): **revisado** (§3.116): curvas, animaciones y reglas de capa de Retro iguales a
  `quattro` `18ac93c`; lo que no está son las reglas de su modo vidrio, que BWM tiene propio.
* **Menú**: Apariencia como menú principal con las opciones de Estilo, Barra con Ocultar/Mostrar,
  transparencia de apps opcional (#14253), Setup > Teclado (#17270). Comparado (§3.116): añadidos Hibernar,
  Dock (ocultar/posición), Intros de fondo y Neovim. **Hechos después** (§3.128): Barra (ocultar, posición,
  fondo, formato del reloj), Animaciones sí/no, Marca (Acerca de y salvapantallas), Idioma y Entrada.
  Quedan Ventanas > Esquinas y Huecos, Setup > Teclado (distribuciones) y Seguridad (no aplican: pacman, PAM y
  sudo), Transcodificar, Compartir y Hardware.
* Avisos con botones: **hecho** (§3.116) en grabaciones (Abrir y, si está Omacut, Cortar) y batería baja como
  tarjeta normal. yt-dlp es la extensión de Chromium de Omarchy: no aplica.
* Instaladores de Arch (Notion, Slack, Microsoft, Amp, Herdr, dictado Hex/Voxtype/Superwhisper): no aplican
  tal cual en Gentoo.

## 5. Atajos

**Atajos (anotado, sin implementar)**: ciclo de layout de workspace, Alt+Mayús+Tab, seleccionar todo universal,
Super+coma sobre notificaciones, dictado, gestos de touchpad.
