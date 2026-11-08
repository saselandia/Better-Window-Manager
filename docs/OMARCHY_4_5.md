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
5. **Cambio deslizante de fondo sin parpadeo negro** en todos los monitores: relacionado con el fallo de §3.81.
6. **Notificaciones**: comparar `omarchy-notification-send` y `Service.qml` con upstream (56 líneas de diferencia,
   sobre todo la acción sobre la última notificación, que sería un atajo) y traer sólo lo que no lo sea.

**Quizá más adelante**: panel Elsewhen/clima/Dropbox propios (BWM ya trae `omarchy-elsewhen` y `omarchy-weather`
como plugins; Dropbox sólo si lo usa el usuario), fondos con introducción, dictado (`voxtype` etc. necesitan
paquetes y micrófono), modelos locales (CUDA/container toolkit: coste alto), Jade Horse como tema extra.

**No**: todo lo de Arch/hardware (Apple, Snapdragon, ASUS, kernel `linux-omarchy`, módulos NVIDIA, keyring,
`pacman`, canales, migraciones, `omarchy update`): BWM actualiza con Portage (§2.7 de `BWM_CONTEXT.md`) y
mezclarlo rompería el arranque cifrado. Tampoco el panel de notificaciones retirado, ni el sshd/`sudo` de
Omarchy, ni instaladores de servicios (Slack, Microsoft) que BWM no gestiona.

**Atajos (anotado, sin implementar)**: ciclo de layout de workspace, Alt+Mayús+Tab, seleccionar todo universal,
Super+coma sobre notificaciones, dictado, gestos de touchpad.
