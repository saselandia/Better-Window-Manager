# Breeze III — T3: fondo único BWM ↔ Plasma

Fecha: 2026-11-26. Plan: [BREEZE_PLAN_V3.md](BREEZE_PLAN_V3.md). T3 implementada y activada.

## Resultado y autoridad

En Breeze con host nativo manda la configuración original de Plasma de cada containment.
Alt+W, `set-wallpaper.sh` y la IPC `wallpapers apply` llegan al mismo aplicador que
«Escritorio y fondo…», mediante `KConfigPropertyMap` y el esquema del paquete, compartiendo
la adaptación de `ShellCorona::setWallpaper` 6.7.5. No se edita appletsrc como texto.

| Entrada o medio | Comportamiento |
| :--- | :--- |
| Elección BWM | Aplica a todos los escritorios conectados; respeta claves inmutables y comprueba todos los destinos antes de escribir |
| «Escritorio y fondo…» | Aplica sólo al containment elegido; el botón Aplicar notifica el puente. `PreviewImage` no se publica |
| Fondos distintos | Plasma los conserva por pantalla. El fondo de `QGuiApplication::primaryScreen()` alimenta el fondo único de BWM; sin esa pantalla disponible, el containment conectado de menor ID |
| Imagen | Se publica el archivo local; un paquete de imágenes sin archivo directo exporta una imagen del item del fondo |
| Presentación | El plugin original sigue funcionando; BWM recibe la diapositiva actual al cambiar `configuration.Image` |
| Color / plugin sin imagen local | Captura del subárbol del wallpaper, sin iconos, widgets ni ventanas, después de cargar/aplicar; no una captura del escritorio ni un flujo continuo |
| Vídeo elegido desde BWM | Paquete Plasma/Wallpaper `org.bwm.video`, QtMultimedia, mudo y en bucle. Primer fotograma para bloqueo/respaldo; no mpvpaper detrás del escritorio |
| Host ausente o desactivado | Camino existente swww/mpvpaper. La elección BWM se guarda también como petición para el próximo arranque del host |
| Caída del host | `window-guard.py` comprueba el proceso cada 2 s y recupera el fondo representativo. Una marca ready obsoleta no evita la recuperación |
| Cambio de skin | Conserva la disposición nativa y los fondos por pantalla; no aplana todo al fondo representativo. Una petición BWM explícita pendiente se consume al arrancar |

Las asignaciones de escritorios se guardan aparte del appletsrc, por descripción de monitor,
en `bwm-plasma-host/desktop-assignments.json`; siguen los cambios de containment y pantalla.
Los conectores de salidas virtuales sin EDID sólo se usan en memoria.

`bwm_wallpaper.publish` es la publicación común de ambos caminos: actualiza
`current_wallpaper{,_plasma}` y `background.wallpaperPath`/`thumbnailPath` en config.json y el
perfil de la skin. El bloqueo de Breeze usa `thumbnailPath` para no intentar abrir un vídeo
como imagen. El exportador comprueba skin y PID para rechazar generaciones antiguas. No hay
nuevo demonio ni nuevo vigilante inotify. Las instantáneas tienen nombre por contenido para
evitar la caché de Qt; se conservan ocho recientes más las referenciadas por pantallas activas.

El renderizador habitual de arranque se ejecuta sin recolorear desde el fondo. SDDM/Plymouth
siguen usando los colores estáticos de Breeze: sus temas existentes no usan una fotografía
del wallpaper. No se han cambiado temas root ni initramfs. `bwm_boot.py` respeta XDG de
estado/configuración para poder probar su staging en aislamiento.

Los selectores de BWM siguen limitados a `~/Pictures/Wallpapers` (§311); la ventana original
de Plasma conserva su selector y sus plugins nativos. La API de aplicación acepta rutas
externas igual que antes. Las otras skins conservan sus motores y paletas.

## Cambios

- `src/bwm-plasma-host/wallpaperbridge.{h,cpp}`, integración en `main.cpp` y `ViewCorona`, y
  aplicador compartido con `containmentconfigview.cpp`.
- Socket `QLocalServer` privado: `wallpaper-status`, `wallpaper-set <JSON>`; lectura asíncrona
  acotada a 64 KiB y 2 s, con peticiones fragmentadas y rutas largas/Unicode.
- `skins/plasma/scripts/wallpaper-sync.py`, instalación/arranque desde `plasma-host.py` y
  paquete estándar `skins/plasma/share/plasma/wallpapers/org.bwm.video`.
- Publicación común `scripts/bwm_wallpaper.py`; rutas de `set-wallpaper.sh` y `Wallpapers.qml`;
  respaldo en `window-guard.py`, supresión del reproductor externo en `bwm-video-wallpaper`.
- QtMultimedia QML declarado como recomendado en catálogo/manifiesto, tabla de requisitos
  regenerada. Si falta, el host rechaza el vídeo y se mantiene el camino de respaldo.
- Procedencia, arquitectura, README del host y AGENTS/CLAUDE sincronizados.

## Comprobado

| Prueba | Entorno | Resultado |
| :--- | :--- | :--- |
| `test_breeze_t3.py`, `test_window_guard_wallpaper.py`, `test_skins.py` | XDG temporal y dobles de procesos externos | **19/19 PASS**: publicación común, skin de catálogo, selección de principal, rechazo de generación obsoleta, elección sin host y reanudación, skin entry sin aplanar, fallback, manifiestos |
| CTest completo del host | `build/bwm-plasma-host-tests`, `BUILD_TESTING=ON` | **15/15 PASS**, 92,97 s |
| `test-wallpapers-session` + `check-wallpapers-session.py` | Hyprland anidado, D-Bus/XDG privados, dos salidas Wayland 1280×800 a escala **1 y 1,25**, OpenGL | **PASS**: Aplicar de `ContainmentConfigView` real, imagen por pantalla y global, color con comprobación del píxel central exportado, presentación con cambio de diapositiva, vídeo H.264 con dos imágenes de fotogramas distintas y vuelta a imagen |
| Host de producción `--session` | Mismo entorno aislado | **PASS**: migración inicial de fondo, ruta BWM → Plasma → perfiles, rutas Unicode de más de 512 bytes, petición fragmentada sin bloquear otro cliente, selección pendiente/reanudación, caída con marca ready obsoleta, paleta intacta y staging de arranque |
| Compilación/instalación | `plasma-host.py build`, instalación atómica | SHA256 **`1c01b5c4a67ca84506e0a30c5d3c59c7a343e8df74da21b25b35affaf45239d6`** |
| Sesión diaria, autorización explícita del usuario en este chat | Host nuevo PID **1466015**, dos escritorios reales | **PASS**: fondo temporal por `set-wallpaper.sh` en ambas pantallas; restauración por API de los fondos originales; publicación del principal a BWM; hashes de kdeglobals y plasma_colors.lua iguales; swww/mpvpaper parados; host ready y vigilante relanzado como hijo de Hyprland |
| Comprobaciones finales | Sesión diaria | `hyprctl configerrors` vacío; Quickshell cargado, una instancia `ii`, sin errores nuevos de carga de Wallpapers.qml |

El arnés sustituye swww/awww/pgrep para no parar motores de la sesión diaria durante los
ensayos privados. Plasma, su configuración, presentación y el vídeo sí se ejecutan y
renderizan realmente. La retirada de swww/mpvpaper también se comprobó en la sesión diaria.
No se inyectó entrada en esa sesión ni se cambiaron los monitores físicos.

La primera ejecución completa de CTest coincidió con un reenlazado y falló al ejecutar
`test-plasma-ui` (EACCES transitorio); la ejecución secuencial final pasó entera. Un segundo
headless del compositor hijo no dio modo válido en NVIDIA: el arnés final usa dos salidas
Wayland sobre una salida virtual del anfitrión, retirada al terminar.

## Límites y comprobaciones pendientes

- La restauración diaria se verificó por el estado nativo y la publicación BWM, sin
  confirmación visual del usuario de cada pantalla. La ventana original Aplicar se ejercitó
  en el compositor anidado; en la sesión diaria se utilizó la misma API por socket.
- El principal es el de **Qt**, no la pantalla enfocada ni una elección que siga el puntero.
  El respaldo swww es el único fondo representativo de BWM; los fondos diferentes reaparecen
  al volver el host.
- Un plugin de terceros que cambia internamente sin notificar `loading`, `accentColor`,
  `Image` ni Aplicar no promete una instantánea del nuevo contenido. Se conserva el plugin;
  su última instantánea válida alimenta el bloqueo. No se instalaron plugins de vídeo o
  imagen del día de terceros para esta fase; su matriz de compatibilidad corresponde a T7.
- No se hizo un ciclo completo de skins en la sesión diaria ni un corte físico de monitores.
  Se probaron las guardas de cambio de skin y las dos pantallas aisladas; no se afirma esa
  aceptación física adicional.
- No se añadieron fotografías a los temas de SDDM/Plymouth ni se ejecutó sudo.

## Recuperación

Copia privada previa en `~/.local/state/bwm/t3-session-backup/`: binario anterior, layout y
asignaciones previos, estado original de fondos y resultado de la prueba. No está en Git.
Para volver al respaldo puede desactivarse el host nativo desde la configuración de BWM y
pararlo con `plasma-host.py stop`; el vigilante repone el fondo representativo. No cargar ni
descargar plugins de Hyprland, no arrancar otra instancia `qs -c ii` y no reescribir un
appletsrc mientras su Corona lo tiene abierto.

T4 no se había empezado al cerrar esta fase.
