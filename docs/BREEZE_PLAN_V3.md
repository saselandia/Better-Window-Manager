# Breeze III: lo que Plasma hace y Breeze aún no

Fecha: 2026-11-26. Base revisada: `0b82db7` (Breeze II cerrado, §381–384 de `BWM_CONTEXT.md`).

Este es el **plan activo de Breeze (Kde plasma)** tras cerrar `BREEZE_PLAN_V2.md` (R0–R9). No
repite lo hecho: el panel y el escritorio diarios ya son `bwm-plasma-host --session` con las
interfaces originales de Plasma 6.7.5, Preferencias es el `systemsettings` real y las ventanas
usan KDecoration, sombras y animaciones de KWin. Las fases nuevas se llaman **T0–T9**.

Cada bloque de §5 es un prompt para una sesión nueva. Ejecutarlos en orden; una fase por sesión.
No confundir «compila» o «carga» con «funciona como en Plasma».

## 1. De dónde sale esta lista

Se recorrió Plasma 6.7.5 desde su código (applets, KCM de `systemsettings`, efectos de KWin,
programas de sesión, runners y contenido de los temas globales) y se comparó con lo que corre en
la sesión Breeze actual. Sólo entran huecos comprobados, no ideas sueltas.

| Área de Plasma | Qué pasa hoy en Breeze (comprobado) | Fase |
| :--- | :--- | :--- |
| Notificaciones | `org.freedesktop.Notifications` lo tiene Quickshell; el applet `org.kde.plasma.notifications` de la bandeja nativa no puede registrarse («Failed to register Notification service on DBus»): no ve los avisos, su historial ni su «no molestar». Nadie lee `plasmanotifyrc`, así que la página de Notificaciones de Preferencias no hace nada | T1 |
| Páginas de Preferencias | Ratón y Touchpad piden los dispositivos a KWin y salen vacías; Región se guarda pero no se aplica al entrar; Accesibilidad, Pantalla táctil, Sesión y Actividades dependen de KWin o de servicios que no existen | T2 |
| Fondo | Hay dos fondos: el del escritorio nativo de Plasma (`org.kde.image` en el appletsrc del host) y el de BWM (`set-wallpaper.sh`, swww, bloqueo, SDDM). Cambiar uno no cambia el otro (nota del usuario en `todo.md`) | T3 |
| Temas globales | «Disposición del escritorio y ventanas» pide a `org.kde.PlasmaShell` cargar la disposición del tema; el host no ofrece ese servicio. Pantalla de bienvenida (`contents/splash`) y de salida (`contents/logout`) no se usan; Breeze y Sweet las traen y `ksplashqml`/`ksmserver-logout-greeter` están instalados | T4 |
| Atajos globales | `kglobalacceld` está instalado pero no corre («Couldn't start kglobalaccel»). No funcionan el atajo que se pone a un widget en su configuración ni los atajos globales de apps de KDE (Spectacle, Konsole…). `kcm_keys` está restringido | T5 |
| Paquetes | Faltan `ksystemstats` (los widgets de Monitor del sistema no tienen datos), `kdeplasma-addons` (widgets estándar) y `powerdevil` (batería y brillo en portátiles) | T6 |
| Bandeja nativa | El applet de portapapeles de Plasma (Klipper) convive con cliphist y Super+V; el de distribución de teclado depende de KWin | T6 |
| Pequeños | Super+. abre los emojis de BWM y no `plasma-emojier` (instalado); sin zoom de pantalla con Meta+= / Meta+-; el portal de archivos es el de GTK aunque `xdg-desktop-portal-kde` está instalado | T6 |
| Tienda KDE | La compatibilidad estimada (~50 %) no está medida tema a tema ni widget a widget | T7 |
| Vista general | Meta+W (vista general), Meta+G (rejilla de escritorios), Ctrl+F9/F10 (ventanas expuestas) y la esquina superior izquierda vienen activas por defecto en Plasma; Breeze no tiene nada equivalente. Bordes de la pantalla tampoco | T8 |
| Respaldo duplicado | `modules/plasma` sigue entero como respaldo del host nativo; se mantiene dos veces cada interfaz | T9 |

**Se descarta** (y no se vuelve a proponer sin una razón nueva): Actividades; scripts y efectos de
terceros de KWin (Krohnkite y similares: Hyprland ya hace mosaico); menú global (necesita un
protocolo de KWin que Hyprland no tiene); minimizar hacia la tarea, `squash` y cross-fade de
maximizado; sombras X11 `_KDE_NET_WM_SHADOW`; Discover; «Restaurar sesión» (si se hace algún día,
es común a todas las skins, no de Breeze).

## 2. Resultado que se busca

1. Los avisos son los de Plasma en Breeze (popups, historial, progreso de copias, sonidos,
   «no molestar»), y su página de Preferencias tiene efecto.
2. Ninguna página de Preferencias se muestra sin hacer nada: o funciona sobre Hyprland/BWM o se
   oculta con el perfil KAuthorized que ya existe.
3. Un solo fondo: se cambia desde el selector de BWM o desde «Escritorio y fondo…» de Plasma y
   llega a todo (escritorio, bloqueo, SDDM, paleta de las apps cuando corresponda).
4. Un tema global de la tienda aplica todo lo que trae: colores, estilos, decoración, iconos,
   **disposición del panel, pantalla de bienvenida y pantalla de salida**.
5. Los atajos globales de KDE funcionan **sin pisar los de BWM** (§3).
6. Lo que Plasma trae de serie y aquí falta está declarado como requisito, sin duplicados en la
   bandeja.
7. La compatibilidad con la tienda KDE se mide y se publica con datos.
8. Vista general y esquinas activas como las de Plasma 6, si el coste se confirma asumible.

## 3. Reglas comunes

Valen las reglas de `BREEZE_PLAN_V2.md` §3 (leerlas): código original antes que réplicas,
procedencia y licencias, ningún KWin/plasmashell en la sesión, sudo lo ejecuta el usuario, no
escribir `~/.config/bwm/user/*`, plugins sólo con `make install` y sin carga en caliente, nunca
otro `qs -c ii`, pruebas en compositor anidado y ventanas desechables, informe por fase. Además:

- **Los atajos de BWM mandan.** `config/hypr/keybinds.json` (y los fijos de «helpers» de
  `keybinds-manager.py`) siguen siendo la fuente de los atajos de BWM en todas las skins. Un atajo
  global de KDE nunca sustituye ni desactiva uno de BWM: si la combinación ya la usa BWM, el de
  KDE queda sin asignar y Preferencias → Atajos lo muestra como en conflicto. Las acciones que hoy
  resuelve BWM (Kickoff con Super/Alt+F1, Meta+D, Alt+F3, Meta+RePág/AvPág, Alt+Tab, KRunner…)
  siguen yendo por BWM aunque KDE registre las suyas.
- **Un solo dueño por servicio.** Notificaciones, SNI, polkit y atajos: un dueño a la vez, con
  relevo explícito al entrar y salir de Breeze, y vuelta al respaldo si el host nativo cae.
  Retro y default no cambian de dueño por este plan.
- **Probar con el host nativo y sin él.** Cada cambio en Breeze debe funcionar con
  `bwm-plasma-host` activo y con el respaldo de Quickshell (`bar.plasma.nativeHost=false`).
- **Pruebas del host:** compilar con `BUILD_TESTING=ON` en `build/bwm-plasma-host-tests`; el CTest
  de `build/bwm-plasma-host` ejecuta binarios viejos (§383).
- Cada fase entrega `docs/BREEZE_T<n>_RESULTS.md`, actualiza §2 y añade sección a §3 de
  `BWM_CONTEXT.md` y el estado de este plan. Sin commit/push salvo petición expresa.

## 4. Orden y esfuerzo

**high** para servicios D-Bus, protocolos, C++ del host, relevos entre skins y la vista general.
**medium** para páginas, requisitos y medición.

| Fase | Trabajo | Esfuerzo | Depende de | Reinicio de sesión |
| :--- | :--- | :--- | :--- | :--- |
| T0 | Cerrar las comprobaciones pendientes de Breeze II — **hecha** (§386) | **medium** | — | No |
| T1 | Notificaciones de Plasma en Breeze — **hecha** (§387) | **high** | T0 | No |
| T2 | Preferencias que funcionan u ocultan — **hecha** (§388) | **medium** | T1 (página de Notificaciones) | No |
| T3 | Fondo único BWM ↔ Plasma — **hecha** (§389) | **high** | T0 | No |
| T4 | Temas globales: disposición, bienvenida y salida — **implementada**, aceptación física parcial (§390; BREEZE_T4_RESULTS.md) | **high** | T3 | No previsto |
| T5 | Atajos globales de KDE coherentes con BWM — **implementada**, aceptación en sesión pendiente (§391; BREEZE_T5_RESULTS.md) | **high** | T2 (página de Atajos) | No previsto |
| T6 | Paquetes, bandeja nueva y detalles — **implementada**, límites de PowerDevil/bandejas existentes en §392 y BREEZE_T6_RESULTS.md | **medium** | T5 (Meta+=, Super+.) | No |
| T7 | Compatibilidad medida con la tienda KDE — **hecha** (§394; BREEZE_STORE_COMPAT.md, BREEZE_T7_RESULTS.md) | **medium** | T4 | No |
| T8 | Vista general y esquinas activas — **implementada**, aceptación física pendiente (§395; BREEZE_T8_RESULTS.md) | **high** | T5 | No (sin cambios en `breezebars`) |
| T9 | Respaldo sin duplicados y aceptación final — **implementada**, regresión completa en verde, aceptación física final pendiente (§396; BREEZE_T9_RESULTS.md) | **high** | T8 | No (binarios finales ya cargados) |

T1, T3 y T5 tocan piezas distintas; aun así se ejecutan en orden para no tener dos sesiones
trabajando sobre el host a la vez.

## 5. Prompts listos para pegar

### T0 — Cerrar Breeze II — MEDIUM

```text
Trabaja en /mnt/HDD1TB/Projects/hyprland-de. Lee AGENTS.md, docs/BREEZE_PLAN_V3.md entero y
BWM_CONTEXT.md §383–384. Ejecuta sólo T0.

Quedan comprobaciones de uso real de §383–384 que el usuario aún no ha visto: desplegables de la
bandeja nativa (Bluetooth, audio, red…) anclados al panel, desplegables de widgets del escritorio,
modo edición con ventanas abiertas (se minimizan y vuelven), bordes de los desplegables con otro
tema y con un lanzador de terceros (AndromedaLauncher usa su propio Dialog) y el tamaño de las
miniaturas de grupos. No inyectes entrada en la sesión diaria: prepara para cada caso qué tiene
que hacer el usuario y qué debe ver, pídele que lo haga y registra lo que diga.

Si algo falla, reprodúcelo en Hyprland anidado (check-focus-safety.py, check-edit-mode-session.py)
y corrígelo con prueba de regresión. Entrega docs/BREEZE_T0_RESULTS.md con lo confirmado, lo
corregido y lo que siga pendiente. No empieces T1.
```

### T1 — Notificaciones de Plasma en Breeze — HIGH

```text
Lee AGENTS.md, docs/BREEZE_PLAN_V3.md y BREEZE_T0_RESULTS.md. Implementa sólo T1.

Objetivo: en Breeze los avisos son los de Plasma 6.7.5. Estudia en plasma-workspace 6.7.5
libnotificationmanager (Server, Notifications, Settings, jobs) y el applet
org.kde.plasma.notifications (popups, historial, «no molestar», progreso de trabajos KIO, sonidos
con canberra, acciones y respuesta en línea). Decide quién debe ser el servidor: lo preferible es
que bwm-plasma-host use el Server original, para que el applet de la bandeja nativa funcione sin
parches; justifica la alternativa si no es viable.

Relevo de dueño: hoy services/Notifications.qml de Quickshell tiene org.freedesktop.Notifications
en Breeze (campo notifications de skin.json, §3.351) y swaync lo tiene en default. Al entrar en
Breeze con el host activo, el host toma el nombre; al salir o si el host cae, Quickshell vuelve
a tenerlo sin perder avisos en vuelo más de lo inevitable. Nunca dos servidores a la vez ni
una cola de nombres que deje a un cliente esperando. Revisa bwm-theme-manager.py (6.1/6.2),
autostart.sh, plasma-host.py y la marca ready.

Conserva lo común: «no molestar» e indicadores de BWM (bwmNotifications IPC, los que usa el
menú de Retro y la inactividad) deben seguir el estado real del servidor activo. Monitor de los
popups según la configuración de Plasma (plasmanotifyrc) y la de BWM (notifications.forceMonitor):
decide la autoridad y documéntala. La página Notificaciones de Preferencias (kcm_notifications)
debe tener efecto real: posición, duración, por aplicación, historial, sonidos.

Pruebas: servidor en D-Bus privado con clientes reales (notify-send, una app KDE si hay), popups
y applet de la bandeja en Hyprland anidado, relevo Breeze ↔ Retro ↔ default sin avisos perdidos,
caída del host con respaldo, «no molestar» desde BWM y desde la bandeja. Entrega BREEZE_T1_RESULTS.md.
```

### T2 — Preferencias que funcionan u ocultan — MEDIUM

```text
Lee AGENTS.md, docs/BREEZE_PLAN_V3.md y resultados T0–T1. Implementa sólo T2.

Recorre todas las páginas que muestra settings-native.sh (systemsettings real con el perfil
KAuthorized de BWM). Para cada una, comprueba si su cambio tiene efecto en Hyprland/BWM o si
depende de KWin o de un servicio que no existe. Mínimo conocido:

| Página | Hoy | Hacer |
| Ratón y Touchpad | Piden dispositivos a KWin (InputDevice D-Bus): vacías | KCM propio (kcm_bwm_input, en src/bwm-systemsettings) con las opciones de entrada de Hyprland por dispositivo: aceleración, perfil, natural scroll, tap, velocidad, zurdo. Común a las skins en lo que sea común |
| Bordes de la pantalla | Sin esquinas activas | Ocultar hasta T8 |
| Accesibilidad, Pantalla táctil | Dependen de KWin | Ocultar, salvo opciones que BWM sí pueda aplicar |
| Sesión (restaurar), Actividades | Sin equivalente | Ocultar |
| Región (formatos) | Se guarda, no se aplica al entrar | Aplicar plasma-localerc (LC_*) al iniciar sesión en todas las skins sin pisar locale del sistema ni LANG elegido por el usuario |
| Notificaciones | Resuelta en T1 | Verificar |

Ocultar = el perfil KAuthorized existente, no borrar plugins del sistema. Una opción que BWM
aplique debe seguir las reglas de configuración común entre skins (§14 de AGENTS) y el puente
kde-config-bridge.py (regla de autoridad, BREEZE_ARCH §9). Revisa también las páginas que ya
funcionan por si alguna opción concreta no tiene efecto, y márcala o ocúltala.

Entrega BREEZE_T2_RESULTS.md con una tabla de todas las páginas: funciona / implementada /
oculta, y por qué.
```

### T3 — Fondo único BWM ↔ Plasma — HIGH

```text
Lee AGENTS.md, docs/BREEZE_PLAN_V3.md y resultados T0–T2. Implementa sólo T3.

Petición del usuario (todo.md): el selector de fondo de Breeze bien integrado con el de Plasma,
para cambiarlo desde los dos sitios. Hoy hay dos fondos: el del containment de escritorio nativo
(plugin org.kde.image y otros, en el appletsrc del host) y el de BWM (set-wallpaper.sh, swww,
~/.cache/current_wallpaper, background.wallpaperPath, bloqueo, SDDM, tema de arranque).

Diseña una sola autoridad en Breeze con el host activo y que ambas entradas la cambien:
- desde BWM (selector Alt+W, IPC, bwm, cambio de skin): el host aplica el fondo en el
  containment de cada pantalla con su API original, sin reescribir el appletsrc a mano;
- desde «Escritorio y fondo…» de Plasma (ContainmentConfigView): BWM se entera y actualiza lo
  suyo (bloqueo, SDDM/arranque, background.wallpaperPath) por el camino normal.
Resuelve: fondos distintos por pantalla en Plasma frente a uno en BWM; plugins que no son una
imagen (presentación, color, imagen del día, vídeo): qué recibe el bloqueo; fondos de vídeo de
BWM (§3.110); qué hace swww debajo del escritorio nativo (no trabajar dos veces) y cómo sigue
siendo el respaldo si el host cae. Breeze tiene paleta estática: cambiar el fondo no recolorea.

Conserva el formato de Plasma y la regla de selectores (§311: los selectores de BWM sólo
~/Pictures/Wallpapers). Pruebas en XDG aislado y en Hyprland anidado; en la sesión sólo con el
permiso del usuario y devolviendo su fondo. Entrega BREEZE_T3_RESULTS.md.
```

### T4 — Temas globales completos — HIGH

```text
Lee AGENTS.md, docs/BREEZE_PLAN_V3.md y resultados T0–T3. Implementa sólo T4.

Tres piezas de los temas globales (look-and-feel) que hoy no llegan:

1. Disposición: kcm_lookandfeel con «Disposición del escritorio y ventanas» llama por D-Bus a
   org.kde.PlasmaShell (loadLookAndFeelDefaultLayout y lo que use plasma-apply-lookandfeel).
   Ofrece en bwm-plasma-host la parte de esa interfaz que el tema necesita, ejecutando su
   layout.js con el LayoutTemplateRunner existente (§323), con copia previa del perfil
   (ProfileStore) y vuelta atrás si falla. No tomar el nombre si plasmashell real existiera.
   Estudia la API de scripts que usan los temas de la tienda y declara la que no se soporta.
2. Bienvenida (contents/splash, ksplashqml instalado): decide cuándo se muestra en BWM (SDDM
   entra solo y Breeze pide la contraseña en su bloqueo, §3.97) y qué la cierra (host listo).
   Sólo en Breeze. Respeta «Ninguna» en kcm_splashscreen.
3. Salida (contents/logout, ksmserver-logout-greeter instalado): el diálogo de Apagar/Reiniciar/
   Cerrar sesión con cuenta atrás de Plasma para los botones de sesión de Breeze (Kickoff,
   menús), con las acciones por bwm-power. Usa el greeter original si su contrato se puede
   cubrir sin ksmserver; si no, alójalo con ThemeHost como el bloqueo y el OSD (§3.156).

Los scripts de temas son código: ensáyalos en raíces aisladas antes de soportarlos. Pruebas con
Breeze, Sweet y al menos un tema de la tienda con disposición propia. Entrega BREEZE_T4_RESULTS.md.
```

### T5 — Atajos globales de KDE coherentes con BWM — HIGH

```text
Lee AGENTS.md, docs/BREEZE_PLAN_V3.md (sobre todo §3, «Los atajos de BWM mandan») y resultados
T0–T4. Implementa sólo T5.

Objetivo: que funcionen los atajos globales de KDE (el atajo de un widget en su configuración,
los de apps KDE como Spectacle o Konsole, los de kcm_keys) sin cambiar ningún atajo de BWM.

Estudia kglobalaccel 6.29 y kglobalacceld 6.7.5 (instalado, no corre): su interfaz D-Bus
org.kde.KGlobalAccel, el formato de kglobalshortcutsrc y sus plugins de plataforma
(KGlobalAccelInterface). Preferible: kglobalacceld original con un backend BWM que convierta
cada atajo activo en un bind de Hyprland y le devuelva la pulsación; justifica otra vía si no.

Reglas de convivencia, obligatorias:
- keybinds.json y los helpers de keybinds-manager.py siguen siendo la fuente de los atajos de
  BWM; lo que hoy usa un atajo de BWM lo sigue usando.
- Al registrar KDE una combinación ya usada por BWM (en la skin activa), no se asigna: queda en
  conflicto, visible en Preferencias → Atajos, y el usuario puede darle otra libre.
- Asignar en Preferencias una combinación de BWM se rechaza con el aviso de conflicto de KDE,
  indicando que se cambia en los atajos de BWM.
- Los atajos de KDE se generan en un módulo Lua propio, cargado antes del Lua del usuario y
  regenerado sin tocar user_binds.lua ni keybinds.json. Sólo en Breeze; fuera de Breeze no
  hay binds de KDE.
- Las acciones de KDE que BWM ya resuelve (Kickoff, Mostrar escritorio, menú de ventana,
  maximizar/minimizar, Alt+Tab, KRunner…) no se duplican: el atajo de KDE queda apuntando al
  de BWM o oculto, no dos binds para la misma tecla.
Decide qué muestra kcm_keys (hoy restringido): los atajos de KDE editables y los de BWM como
sólo lectura o con enlace a la página de atajos de BWM.

Pruebas: registro y pulsación desde un cliente propio en D-Bus privado; conflicto con un atajo de
BWM; widget con atajo en el host anidado; cambio de skin sin binds residuales; keybinds-manager
reload sin perder los de KDE. Entrega BREEZE_T5_RESULTS.md.
```

### T6 — Paquetes, bandeja sin duplicados y detalles — MEDIUM

```text
Lee AGENTS.md, docs/BREEZE_PLAN_V3.md y resultados T0–T5. Implementa sólo T6.

1. Requisitos: declara en config/hypr/skins/requirements.json y en recommends de Breeze
   ksystemstats (datos de los widgets de Monitor del sistema), kdeplasma-addons (widgets estándar)
   y powerdevil (batería y brillo; comprueba que no choca con el servicio de energía común ni con
   la inactividad de BWM antes de recomendarlo). Comandos de Portage para el usuario; regenera
   docs/REQUIREMENTS.md. Verifica tras instalarlos que los widgets muestran datos.
2. Bandeja nativa sin duplicados: el applet de portapapeles de Plasma (Klipper) frente a cliphist
   y Super+V; el de distribución de teclado (KWin org.kde.keyboard) frente a las distribuciones de
   Hyprland. Para cada uno elige una sola fuente: conectarlo a lo de BWM o retirarlo de la
   bandeja por defecto, sin borrar la elección del usuario.
3. Detalles: en Breeze, Super+. abre plasma-emojier; zoom de pantalla con Meta+= y Meta+- y
   Meta+0 (cursor:zoom_factor de Hyprland), como el efecto Zoom de KWin; el portal de archivos de
   KDE (xdg-desktop-portal-kde, ya instalado) en Breeze para las apps GTK, sin cambiar las otras
   skins. Los atajos nuevos con keybinds-manager.py y skins: ["plasma"], respetando T5.

Entrega BREEZE_T6_RESULTS.md.
```

### T7 — Compatibilidad medida con la tienda KDE — MEDIUM

```text
Lee AGENTS.md, docs/BREEZE_PLAN_V3.md y resultados T0–T6. Implementa sólo T7.

Sustituye la estimación (~50 %, README y docs/SKINS.md) por una medición. Con KNSCore y raíces
XDG temporales (kns-cycle.py, §209), toma los elementos más descargados de cada categoría:
temas globales, estilos de Plasma, esquemas de color, decoraciones (Aurorae y C++), iconos,
cursores y plasmoides. Para cada uno: instala, aplica o añade, comprueba carga sin errores,
aspecto (captura en el compositor anidado), opciones propias y retirada. No cargues widgets que
ejecuten órdenes sin revisarlos (regla de §209).

Clasifica: funciona / funciona con diferencias / no funciona, con la causa (API de KWin ausente,
servicio, paquete que falta, fallo de BWM). Corrige los fallos de BWM que sean pequeños; anota
los grandes como trabajo futuro. Publica la tabla en docs/BREEZE_STORE_COMPAT.md y actualiza el
porcentaje de README.md, README.es.md y docs/SKINS.md con el dato medido y su fecha.
Entrega BREEZE_T7_RESULTS.md.
```

### T8 — Vista general y esquinas activas — HIGH

```text
Lee AGENTS.md, docs/BREEZE_PLAN_V3.md y resultados T0–T7. Implementa sólo T8.

Objetivo: la vista general de Plasma 6 en Breeze: Meta+W (vista general con escritorios y
búsqueda de KRunner), Meta+G (rejilla de escritorios), Ctrl+F9/F10 (ventanas expuestas) y
la esquina superior izquierda, con el aspecto y las animaciones de KWin 6.7.5.

Estudia kwin/src/plugins/overview y windowview (QML y su contrato con el efecto). Antes de
implementar, mide el coste y decide con el usuario: un port del QML sobre Quickshell o el host,
con miniaturas en vivo (screencopy con la guarda bwmScreenshareMonitorGuard), como el Alt+Tab
(§3.156); o una alternativa más pequeña. Lo mismo para la página Bordes de la pantalla
(kcm_kwinscreenedges): esquinas activas sobre Hyprland sin romper el snapping de §17 ni el
arrastre entre monitores.

Las acciones sobre ventanas y escritorios usan lo común (kwin-window.py, toggle-minimize.py,
proveedor de escritorios nativo). Atajos según T5. Pruebas en compositor anidado, dos monitores,
escalas fraccionarias y Magic abierto. Entrega BREEZE_T8_RESULTS.md.
```

### T9 — Respaldo sin duplicados y aceptación final — HIGH

```text
Lee AGENTS.md, docs/BREEZE_PLAN_V3.md y resultados T0–T8. Implementa sólo T9.

1. Respaldo: config/quickshell/ii/modules/plasma mantiene panel, Kickoff, bandeja, menús y
   applets como respaldo del host nativo. Decide con el usuario qué se conserva (lo mínimo para
   que Breeze siga usable si el host no arranca) y retira el resto, con sus pruebas y READMEs.
   No retires nada que use Breeze con el host activo (avisos si T1 no los movió, OSD, bloqueo,
   Alt+Tab, menús de ventana, selector de skins).
2. Regresión: batería completa (Python, QML, CTest del host con BUILD_TESTING=ON, decorador,
   KCM), matriz de skins check-skin-lifecycle.py, escalas fraccionarias y temas en XDG aislado.
3. Aceptación física del usuario de T1–T8 en una sesión nueva, con los binarios finales cargados.

Actualiza BREEZE_ARCH, READMEs, REQUIREMENTS.md, THIRD_PARTY_NOTICES y el estado de este plan.
Entrega BREEZE_T9_RESULTS.md con lo cerrado y los límites que queden.
```

## 6. Fuentes

Cotejar siempre con la etiqueta instalada (Plasma 6.7.5, Frameworks 6.29.0):

- [plasma-workspace](https://invent.kde.org/plasma/plasma-workspace): libnotificationmanager,
  applets/notifications, shell (PlasmaShell D-Bus, layout scripts), ksplash, ksmserver
  (logout-greeter).
- [kglobalaccel](https://invent.kde.org/frameworks/kglobalaccel) y
  [kglobalacceld](https://invent.kde.org/plasma/kglobalacceld).
- [plasma-desktop](https://invent.kde.org/plasma/plasma-desktop): kcms (input, keys, notifications,
  lookandfeel, region), wallpaper de containments.
- [KWin](https://invent.kde.org/plasma/kwin): plugins/overview, windowview, screenedge, zoom.
- [kdeplasma-addons](https://invent.kde.org/plasma/kdeplasma-addons),
  [ksystemstats](https://invent.kde.org/plasma/ksystemstats),
  [powerdevil](https://invent.kde.org/plasma/powerdevil),
  [xdg-desktop-portal-kde](https://invent.kde.org/plasma/xdg-desktop-portal-kde).

Este plan se da por cerrado cuando los avisos, Preferencias, fondo, temas globales y atajos
cumplen §2 en una sesión real, la compatibilidad con la tienda está medida y publicada, y T8 está
hecho o descartado con el usuario.
