# R6 — sombras y efectos nativos de KDE

## Iteración 9: menús contextuales, temas globales (`ThemeHost`) y KRunner (2026-11-21)

Continúa la iteración 8 en la sesión diaria (sin depender del plugin candidato):

* **Menús contextuales** (`menus/MenuHost.qml`): la capa `quickshell:plasmaMenu` entra en
  `breeze-blur-frames`. El menú abierto y sus submenús (incluidos submenús dinámicos de bandeja)
  enlazan `background.imagePath` a `BlurPath` (`widgets/background` → `translucent/widgets/background`
  con desenfoque) y publican sus marcos abiertos en `BackgroundEffect.blurRegion` (liberando las
  regiones previas al actualizar o cerrar).
* **Temas globales de terceros (`ThemeHost`)**: `switcher/compat/Dialog.qml` acepta
  `bwmDialogImagePath` y registra su `KSvg.FrameSvgItem` en `bwmBlurTarget.frame`. `osd/Osd.qml` y
  `switcher/Switcher.qml` + `ThemedSwitcher.qml` pasan la ruta resuelta por `BlurPath` y enlazan
  `BackgroundEffect.blurRegion` al marco del tema cargado en el otro motor QML (con reserva al
  propio `themed` en OSD si un tema no usa `Dialog`).
* **KRunner** (`skins/plasma/hypr/rules.lua`): `krunner` (`PlasmaQuick::PlasmaWindow` con
  `LayerShellQt::Window::setScope("krunner")`) ya pide `KWindowEffects::enableBlurBehind` y usa
  `translucent/dialogs/background` de `libplasma`; su capa `krunner` entra ahora en
  `breeze-blur-frames` (`ignore_alpha = 0.01`, `blur_popups = true`) para recortar esquinas y
  márgenes transparentes.

Comprobado: `hyprctl reload` sin errores de configuración, reinicio de mantenimiento del shell sin
errores (mismos workspaces y foco), `test_plasma_interfaces.py` 8/8 (incluye `BwmCompat.Dialog` en
`ThemeHost` recibiendo ruta translúcida y registrando su marco), `test_plasma_menus_ui.py` 5/5
(comprueba `background.imagePath` en menú y submenú y regiones de desenfoque al abrir y cerrar) y
`test_plasma_shadow_policy.py` 1/1 (actualizado con `layer_rule` y comprobación de
`breeze-blur-frames`). Pendiente: comprobación visual en vivo de Alt+Tab real, menús contextuales,
KRunner y un tema global de terceros.

---

## Iteración 8: OSD, cambiador y descripciones emergentes (2026-11-21)

Sigue la iteración 6 en la sesión diaria. En Plasma también son diálogos con desenfoque:

* **OSD** (`osd/Osd.qml`) y **cambiador de ventanas** (`switcher/ThumbnailGrid.qml`): piden
  desenfoque sobre su marco con `BackgroundEffect` y usan la variante translúcida
  (`widgets/background` y `dialogs/background`); sus capas (`bwm-plasma-osd`,
  `quickshell:altTab`) entran en la regla `breeze-blur-frames`. El aspecto de un tema global
  propio (`ThemeHost`, otro motor QML) no pide desenfoque todavía.
* **Descripciones emergentes** del panel (`theme/ToolTipArea.qml`) y de las tareas
  (`panel/TaskToolTip.qml`): ya las desenfocaba `blur_popups` de la capa del panel; ahora dibujan,
  como `ToolTipDialog`, `widgets/tooltip` en su variante translúcida. Sin desenfoque conservan
  la variante anterior.

Comprobado: reinicio de mantenimiento del shell sin errores (mismos workspaces y foco), OSD
por IPC dibujado en su capa con la variante nueva, pruebas QML de interfaces, bandeja, tareas,
panel y Kickoff (la de entrada de tareas recibe un sustituto de `BlurPath`). El cambiador no se
abre por IPC sin la tecla Alt pulsada (el controlador lo da por soltado y activa otra ventana):
en el intento cambió la ventana con foco, que se devolvió a la original; no se repitió. Falta
verlo con Alt+Tab real.

---

## Iteración 7: ventanas que piden desenfoque y franja superior doble (2026-11-21)

**Candidato en `build/r6-surface-plugin`, sin instalar**: con el plugin diario actual no cambia
nada (la regla sigue poniendo `no_blur` a todas las ventanas).

* **Ventanas que piden desenfoque:** KWin sólo desenfoca las que lo piden (`KWindowEffects`,
  `ext_background_effect_v1`); Hyprland, todas las translúcidas salvo `no_blur`. breezebars fija
  ahora `no_blur` con la prioridad más baja (`PRIORITY_LAYOUT`) en las ventanas que no lo piden y
  lo quita a las que lo piden, al confirmar su superficie; las reglas de ventana, también las del
  usuario, siguen mandando. Expone `hl.plugin.breezebars.blur_on_request`: `breeze-float-all`
  sólo pone `no_blur` cuando el plugin cargado no la tiene.
* **Franja superior pintada dos veces (fallo previo, también en la sesión diaria):**
  `SquareTop.cpp` cuadra las esquinas superiores del contenido dibujando encima una copia sin
  redondeo de la franja superior. En una ventana translúcida esa franja se mezclaba dos veces y
  salía más clara (216 en vez de 208 en el ensayo, 8 filas a escala 1). Ahora el original se
  recorta por debajo de la franja (conserva el redondeo inferior) y la copia la dibuja sola, con el
  desenfoque de la ventana.

Ensayo nuevo `check-r6-surfaces.py --kind decorated --effects`: ventana normal translúcida sobre
un tablero, en Hyprland anidado y en KWin 6.7.5. En los dos, sin petición la ventana no se
desenfoca; pidiendo la mitad izquierda se desenfoca sólo ésa (37 290 píxeles en ambos a escala
1; 83 819 y 83 824 a 1,5; 0 fuera); al retirarla vuelve exacta. `--user-no-blur` añade una regla
`no_blur` del usuario y Hyprland no desenfoca aunque la ventana lo pida. La franja superior mide
208 en los dos. Regresión: decoración en los tres temas a 1 y 1,5 igual que en la iteración 4,
desenfoque de capas y breezebars 4/4. Hace falta instalar el plugin y volver a iniciar sesión.

---

## Iteración 6: desenfoque de KWin en Breeze diario (2026-11-21)

Activado a petición del usuario tras el análisis de la iteración 5. **Afecta a la sesión diaria**
(no depende del plugin candidato).

* **Hyprland** (`skins/plasma/hypr/kwin.lua`): `decoration.blur` encendido salvo que `kwinrc`
  `[Plugins] blurEnabled=false`. La intensidad sale de `[Effect-blur] BlurStrength` con la tabla
  de iteraciones/desplazamiento de KWin (`initBlurStrengthValues`) y Hyprland recibe tres pasadas
  más con ese desplazamiento: `passes` 7, `size` 8 con la intensidad por defecto (15), la
  combinación medida en la iteración 5. Sin ruido, contraste, brillo ni viveza. Las otras 14
  intensidades siguen la misma regla sin medición propia. `kde-config-bridge.py` exporta
  `blur` y `blurStrength`; `appearance.lua` repone los valores por defecto de Hyprland
  (`noise`, `contrast`, `brightness`) en las demás skins, porque una recarga no los devuelve.
* **Qué se desenfoca:** como KWin, sólo lo que lo pide. El panel, Kickoff, la ventana de la
  bandeja (y las demás ventanas emergentes del panel) y las notificaciones piden desenfoque con
  `BackgroundEffect.blurRegion` de Quickshell (`ext_background_effect_v1`) sobre su marco. La
  regla de capa `breeze-blur-frames` (`ignore_alpha` 0,01, `blur_popups`) lo recorta donde el
  marco es transparente: esquinas redondeadas y huecos entre notificaciones, como la máscara
  KSvg que usa KWin.
* **Variantes del tema:** con el desenfoque, libplasma activa el selector `translucent` de KSvg.
  El nuevo `theme/BlurPath.qml` reproduce su orden de búsqueda (variante translúcida del tema
  actual, si no su variante normal, si no la translúcida del tema de reserva); `PlasmaTheme.blur`
  lee `kwinrc` del usuario. Sin desenfoque se conserva la variante anterior (sólida en los
  diálogos). En Breeze el diálogo translúcido tiene alfa 216/255 (el sólido, 255).

Comprobado en la sesión real: opciones de Hyprland leídas con `hyprctl getoption` tras la
recarga, sin errores de configuración ni del shell (un reinicio de mantenimiento, mismos
workspaces y foco). Kickoff abierto por IPC un momento: su fondo pasa del sólido (32, 35, 38) a
(33, 37, 38) con desviación ≤0,5 sobre una terminal con texto claro, es decir, marco translúcido
sobre fondo desenfocado. El panel del usuario está en modo «Opaco», así que se ve sólido como en
Plasma. Pruebas: puente KDE 21 (nueva: tabla de intensidad, efecto desactivado, límites), QML de
panel, bandeja, Kickoff y tareas 30.

Pendiente: las **ventanas** que piden desenfoque no lo reciben, porque la regla
`breeze-float-all` les pone `no_blur` (Hyprland desenfocaría si no todas las translúcidas); hará
falta que el plugin lo quite sólo a las que lo piden. Tampoco piden desenfoque todavía los menús
contextuales, la descripción emergente propia, el OSD, el cambiador ni KRunner. No se ha
probado el cambio a otra skin con estos valores ni la comparación visual con Plasma completo.

---

## Iteración 5: intensidad del desenfoque y contorno (análisis, 2026-11-21)

**R6 sigue abierta.** No cambia nada de la sesión diaria: en Breeze `decoration.blur` sigue
apagado y el panel/Kickoff usan las variantes sólidas del tema, como Plasma sin desenfoque.

**Contorno de Breeze en las esquinas (hasta 27/255).** Son 40–57 píxeles del suavizado diagonal:
`renderBorder` de Hyprland y el sombreador de borde de KWin (`sdf.glsl`, `fwidth`) calculan la
cobertura de otra forma. No hay parámetro que lo iguale; haría falta un sombreador propio. Se
deja como límite.

**Desenfoque.** Los dos usan *dual kawase* con los mismos núcleos de reducción y ampliación
(`downsample/upsample.frag` de KWin 6.7.5 y `blur1/blur2.glsl` de Hyprland 0.56.2), pero:

* KWin desplaza `offset` × medio téxel del nivel leído, igual al reducir que al ampliar, y
  recorta la captura a la región más `expandSize` (150 px con 4 iteraciones). Su intensidad por
  defecto (`BlurStrength=15`) son 4 iteraciones con `offset` 8; además satura al 150 % y añade
  ruido 5.
* Hyprland desplaza `size` téxeles al reducir y `size`/4 al ampliar, sobre búferes del tamaño del
  monitor, y aplica `contrast`, `brightness`, `vibrancy` y `noise` propios.

No hay una equivalencia exacta con un solo parámetro. Medido en el compositor anidado frente a
KWin (región de 90×120 px, fondo de tablero y fondo de cuadrantes con bordes nítidos, escala 1):

| Hyprland | Tablero | Cuadrantes |
| :--- | :--- | :--- |
| Por defecto (`size` 8, 1 pasada) | 32/255 | — |
| `passes` 4, `size` 8 | 6/255 | 16/255 |
| `passes` 6, `size` 6 | — | 5/255 |
| `passes` 7, `size` 8 (o 8 y 4), `noise` 0, `contrast`/`brightness` 1, `vibrancy` 0 | **4/255** | **2/255** |

Diferencia máxima dentro de la región. El fondo gris no mide la saturación del 150 % de KWin
(`vibrancy` de Hyprland es otra operación), y el resultado depende del tamaño de la región por
el recorte de KWin: el ajuste es para la intensidad por defecto, no una tabla para los 15
valores de `BlurStrength`.

**Semántica.** En capas (paneles, menús) Hyprland sólo desenfoca lo que lo pide por
`ext_background_effect_v1`, como KWin. En ventanas desenfoca todas las translúcidas salvo
`no_blur`, y Breeze pone `no_blur` a todas: una ventana que pida desenfoque no lo recibiría.
Igualar a KWin en Breeze diario supone activar el desenfoque, pedirlo desde Quickshell
(`BackgroundEffect.blurRegion`) en panel, Kickoff y menús, usar las variantes translúcidas del
tema y quitar `no_blur` sólo a las ventanas que lo piden. Es un cambio visible de la sesión
diaria: pendiente de la decisión del usuario.

Herramientas nuevas: `check-r6-surfaces.py --effects --blur-pattern edge` (cuadrantes con
bordes nítidos tras la región), `--hypr-blur "<campos Lua>"` y `--backends hyprland|kwin` para
barrer parámetros capturando KWin una sola vez.

---

## Iteración 4: radio de las esquinas del contenido (2026-11-21)

**R6 sigue abierta** y el veto diario `no_shadow=true` sigue vigente. La diferencia mayor de la
iteración 3 (Breeze hasta 73/255 oscuro y 109/255 claro) eran las esquinas inferiores del
contenido de la ventana. Medida píxel a píxel, no era el suavizado: el radio era menor.

* KWin 6.7.5 recorta la ventana con `round(radio × escala)` píxeles y un círculo exacto
  (`itemrenderer_opengl.cpp`, `sdf.glsl`).
* Hyprland 0.56.2 usa la regla de redondeo × escala × (potencia / 2) y resta 1 píxel antes de
  dibujar la superficie (`ElementRenderer.cpp`, «to fix a border issue»). Además breezebars
  redondeaba el radio lógico a entero antes de escalarlo. Breeze da 5 lógicos a escala 1 y
  5,33 a 1,5: Hyprland dibujaba 4 px en vez de 5 y 6,5 en vez de 8.
* Ahora la regla es el entero que deja el radio de Hyprland más cerca del de KWin
  (`contentRounding` en `DecoLogic.hpp`), con potencia de redondeo 2 en esas ventanas.

| Tema | 1 | 1,25 | 1,5 | 2 |
| :--- | :--- | :--- | :--- | :--- |
| Breeze oscuro | 12/255 | 16/255 | 14/255 | 52/255 |
| Breeze claro | 22/255 | 27/255 | 26/255 | 46/255 |
| Sweet (Aurorae) | 0/255 | 2/255 | 1/255 | 1/255 |

Máximos por par tema/escala (activa, inactiva y reactivada). Lo que queda en Breeze es el
suavizado del contorno en las esquinas (`renderBorder` de Hyprland frente al sombreador de
borde de KWin) y 1/255 de color del contorno. A escala 2 el objetivo son 10 px y la regla
entera sólo permite 9 u 11: no mejora (límite del tipo de la regla de Hyprland). La primera
imagen sigue siendo idéntica a la reactivada en los 24 casos. Matriz completa con la sesión
intacta (`build/r6-decorated-iter4.json`, `passed: true`); breezebars 4/4 con la prueba nueva de
redondeo (todas las escalas y radios frente a cualquier otro entero).

---

## Iteración 3: decoración completa frente a KWin real (2026-11-21)

**R6 sigue abierta** y el veto diario `no_shadow=true` sigue vigente. Las iteraciones 1 y 2
comparaban la sombra de la decoración con el método de KWin por CPU, y las sombras de cliente
por GPU. Ésta compara en GPU **la decoración completa** de una ventana normal con decoración
del servidor: marco, contorno, botones, icono y sombra KDecoration. Se usan Hyprland anidado
con `bwm-decorator` y el candidato de breezebars, frente a `kwin_wayland` 6.7.5 en raíces y
buses privados. Evidencia en
[BREEZE_R6_DECORATION_RESULTS.json](BREEZE_R6_DECORATION_RESULTS.json).

### Fallos encontrados y corregidos

* **Contorno a doble escala:** breezebars pasaba a `renderBorder` el grosor ya multiplicado por la
  escala, y Hyprland vuelve a aplicarla. A escala 2 el contorno de Breeze medía 4 px en vez de 2.
* **Icono a 1x en HiDPI:** el auxiliar pintaba con `painter.scale()`; ahora pinta sobre una imagen
  con la densidad de la salida, como `DecorationItem` de KWin, y `QIcon` elige el mapa nítido.
* **Iconos vacíos fuera de Breeze:** con la plataforma offscreen Qt sólo buscaba en `:/icons`. La
  decoración Breeze funcionaba por sus iconos incrustados; Aurorae y cualquier icono que sólo esté
  en hicolor (por ejemplo, Steam) salían vacíos. También pasaba en la sesión diaria. El auxiliar
  añade las carpetas XDG `icons` y `/usr/share/pixmaps`. Prueba de regresión que falla con el
  binario anterior.
* **Icono de reserva:** una ventana Wayland sin `.desktop` muestra el icono `wayland`, como
  `XdgToplevelWindow::updateIcon`. Nueva bandera `X11` (65536) en el protocolo para no aplicarlo
  a XWayland.
* **Sombra de Aurorae sin los bordes:** Aurorae crea su sombra en `init()`, antes de que se apliquen
  los bordes, y sólo la rehace al cambiar de activa/inactiva o al maximizar. KWin crea la
  decoración antes de mapear la ventana, aún inactiva, y la activa después: la sombra se rehace
  ya con bordes. El auxiliar la creaba activa y Sweet quedaba con una sombra de 380×260 en lugar
  de 388×292 (ventana 360×240), estirada: la primera imagen difería en las esquinas del lado
  derecho (hasta 44/255 a 1,5) hasta el siguiente cambio de foco. Ahora el auxiliar crea la
  decoración inactiva y le entrega después el estado real, como KWin. Prueba de regresión que
  falla con el binario anterior.
* **Referencia:** KWin arrancaba sin el tema de plataforma de KDE y usaba otra fuente de título
  (barra 8 px más alta). Ahora usa el de KDE, con dos escritorios para mostrar el botón
  «en todos los escritorios», como BWM.

### Resultado (activa, inactiva bajo otra ventana y reactivada)

| Tema | Escalas | Máx. | Dónde |
| :--- | :--- | :--- | :--- |
| Breeze oscuro | 1/1,25/1,5/2 | 73/255 | Antialiasing de las esquinas redondeadas del contenido; sombra ≤2/255 |
| Breeze claro | 1/1,25/1,5/2 | 109/255 | Igual: el contorno claro toca el azul en la esquina a 1,5 |
| Sweet (Aurorae) | 1/1,25/1,5/2 | 2/255 | Sólo el degradado de la sombra a escala fraccionaria |

Marco, barra de título, botones, icono y colores activos/inactivos coinciden. En los 12 pares
tema/escala la primera imagen ya es idéntica a la de después de reactivar, como en KWin (la
comprobación ahora es estricta). La sombra coincide en presencia y forma. La de Sweet es su
relleno de 10 px: queda dentro de la franja que excluye el recuento de presencia, en los dos
compositores. Regresión: decorador 15/15 (pruebas nuevas de hicolor y de la sombra de Aurorae),
breezebars 4/4, XWayland anidado (sombra KDE en 62 584 píxeles, sin segundo marco con
GTK/Motif), piezas a 1,5 y diálogo sin cambios. La matriz final (`build/r6-decorated-final.json`)
pasó todas las comparaciones de imagen; su `passed` es falso sólo porque el puntero se movió
durante los ~40 min de ensayo.

### Pendiente

* Esquinas del contenido: resuelto en la iteración 4 salvo a escala 2.
* Según el código de Aurorae 6.7.5, tampoco en KWin rehace Aurorae su sombra al redimensionar la
  ventana: se estira hasta el siguiente cambio de foco. Se conserva ese comportamiento original.
* No comparado: tamaño y maximizado pedidos por el cliente. Hyprland mantiene el tamaño flotante y
  BWM bloquea a propósito las peticiones de maximizado de las apps. Tampoco enrollar,
  encima/debajo ni píxeles X11 frente a KWin.
* El auxiliar y el plugin corregidos se usarán en la sesión diaria al instalarlos (auxiliar con
  `decorator.py build` y plugin con `make install`) y volver a iniciar sesión. No se ha hecho.

```bash
python3 src/breezebars/check-r6-surfaces.py --module build/r6-surface-plugin/installed/breezebars.so --kind decorated --report build/r6-decorated.json
```

---

## Iteración 2: superficies, paneles, diálogos y XWayland (2026-11-21)

Iniciada por Codex y terminada por Claude tras agotarse su uso. **R6 sigue abierta**: el
candidato sólo se ha probado en compositores desechables y `breeze-float-all.no_shadow=true`
sigue vigente. No se ha instalado nada en `config/hypr/plugins`, reiniciado la sesión ni
sustituido el panel diario. Evidencia resumida en
[BREEZE_R6_SURFACE_RESULTS.json](BREEZE_R6_SURFACE_RESULTS.json); informes completos en `build/r6-*.json`.

### Qué se añade

* **Protocolo `org_kde_kwin_shadow_manager` v2 en breezebars** (`KdeShadow.cpp`,
  `protocols/shadow.xml`). Los clientes KDE (`KWindowShadow`, `DialogShadows`,
  `PanelShadows`) envían sus ocho piezas originales; no hay tema, aproximación gaussiana ni
  segunda barra. Búferes SHM copiados con `pread` y límites (32 MiB), atlas como
  `NinePatchOpenGL` de KWin y geometría `ShadowItem::buildQuads` adaptada a las piezas del
  protocolo (`KdeShadowGeometry.hpp`). El estado se aplica con el commit real de la
  superficie (gancho de `CWLSurfaceResource::commitState`), como KWin. Una decoración
  KDecoration tiene prioridad sobre la sombra del cliente. Diagnóstico `hyprctl -j breezebars-shadows`.
  Sólo SHM: sin dmabuf ni `_KDE_NET_WM_SHADOW` de X11.
* **Panel:** `PanelViewHost::updateMask` sigue a `PanelView` 6.7.5 y publica desenfoque y
  contraste con `KWindowEffects` y sombras con `PanelShadows` de plasma-workspace (copia con
  cambios marcados). Máscara de entrada hasta el borde físico. Bordes activos calculados con
  la geometría del anclaje: con layer-shell Qt informa la posición (0,0) y se quitaba por
  error la sombra superior.
* **Diálogos:** `PlasmaQuick::Dialog` y su `DialogShadows` sin modificar. Una escena Qt Quick
  estática no enviaba fotograma tras recibir los efectos nativos y el diálogo perdía la
  sombra al recrearse; `BwmSurface::ensureNativeEffectsCommit` pide ese fotograma.
* **XWayland:** el plugin ya no conecta con X11 al cargarse. `xcb_connect` en la carga
  bloqueaba el bucle del compositor que debía arrancar el XWayland a demanda; ahora conecta
  tras mapearse una ventana X11.

### Fallos encontrados por el camino

* El estado de una superficie lo posee un puntero único; `weak.lock()` aborta en Hyprland.
  Se observa la referencia débil directamente. La caída se limitó al compositor de prueba.
* `SSurfaceState`/`CWLSHMBuffer` guardan el formato como enum de `wl_shm`, no fourcc DRM.
* Redondeo: KWin redondea la traslación y los vértices locales por separado; aplicarlo
  igualó el caso pequeño.
* **Esta sesión:** `PanelShadows::removeWindow` (auto-ocultar) desconectaba el aviso de
  destrucción pero dejaba la ventana marcada como observada; al volver a añadirla no se
  reconectaba y un cambio de SVG usaba un `QWindow` liberado (SIGSEGV reproducible 3/3 en
  `test-paneltasks`). Corregido; la prueba pasa en normal y ASan.
* **Esta sesión:** al retirar la salida headless temporal, Hyprland daba el foco a la última
  ventana de otro monitor. Los ensayos restauran ahora puntero y ventana (dirección y PID).

### Comprobaciones (KWin 6.7.5 frente a Hyprland 0.56.2, compositores privados)

| Prueba | Resultado |
| :--- | :--- |
| Geometría de las ocho piezas frente a `ShadowItem::buildQuads` | 192 casos, error 0 de color y alpha; con ASan/UBSan |
| Matriz de piezas: Breeze oscuro/claro y Sweet a 1/1,25/1,5/2 | 120 casos (sombra, recreación, pequeño, diminuto, acoplado, retirada, ocultar/mostrar, opacidad por `wp_alpha_modifier_v1`); **máx. 1/255**. 12 liberaciones de recursos y 12 cierres del compositor con sombras vivas |
| Diálogo `PlasmaQuick::Dialog` original, 3 temas a 1/1,25 | 42 casos, **máx. 3/255** (opacidad); recreación, ocultar/mostrar y opacidad restaurada idénticos a la imagen inicial en ambos compositores |
| Panel de BWM frente a plasmashell, ambos en KWin | Idéntico a 1/1,25/1,5; a 2, 2 píxeles con 1/255 |
| Desenfoque `ext_background_effect_v1` | Región correcta (8 960 píxeles dentro, 0 fuera) y retirada exacta en ambos; **intensidad distinta de KWin** (hasta 33/255): es el algoritmo de Hyprland |
| XWayland privado | Ventana X11 SSD con sombra KDE (62 584 píxeles); `_GTK_FRAME_EXTENTS` y Motif sin segundo marco. No probado: sombras X11 propias del cliente |
| Regresión | CTest 8/8, ASan 2/2, Python R4 262/262, breezebars/política 5/5, decorador 13/13, suite de sesión en el LG 54/54 |

La matriz de 40 minutos terminó con el puntero en otra posición (la sesión estaba en uso);
una repetición corta pasó con la sesión intacta. `KWindowEffects` no ofrece contraste en
ninguno de los dos compositores: KWin 6.7.5 lo integra en el desenfoque con parámetros globales.

### Pendiente

Instalar el candidato y retirar el veto `no_shadow` requiere volver a iniciar sesión y la
aceptación del usuario. Faltan: sombras de menús/tooltips de Quickshell, paridad de
intensidad del desenfoque, contraste, dmabuf y `_KDE_NET_WM_SHADOW`, y la comparación con
una sesión Plasma completa. R5 conserva su aceptación pendiente.

```bash
python3 src/breezebars/check-r6-surfaces.py --module build/r6-surface-plugin/installed/breezebars.so --report build/r6-tiles.json
python3 src/breezebars/check-r6-surfaces.py --module build/r6-surface-plugin/installed/breezebars.so --kind dialog --scales 1,1.25 --report build/r6-dialog.json
python3 src/breezebars/check-r6-surfaces.py --module build/r6-surface-plugin/installed/breezebars.so --effects --themes breeze-dark --scales 1 --report build/r6-blur.json
python3 src/breezebars/check-r6-nested.py --module build/r6-surface-plugin/installed/breezebars.so --helper src/bwm-decorator/bwm-decorator --xwayland --report build/r6-xwayland.json
```

Candidato compilado en una copia (`build/r6-surface-plugin`) y desplegado con
`make install PLUGIN_DIR=installed`; nunca sobre el `.so` cargado.

---

## Iteración 1: sombras de decoración (2026-11-20)

Continúa desde R5 (§3.323). **R6 sigue abierta**. El candidato se ha probado fuera del
compositor diario; `breeze-float-all.no_shadow=true` sigue vigente. No se ha instalado el
candidato en `config/hypr/plugins`, reiniciado la sesión ni sustituido el auxiliar diario.
La skin observada al comenzar y terminar era `plasma`.

### Referencia y alcance

Fuentes locales de las versiones instaladas, extraídas de los tarballs de Portage:
KWin, Breeze y KDecoration **6.7.5**; KWindowSystem **6.29.0**. Huellas y resultados en
[BREEZE_R6_SHADOW_RESULTS.json](BREEZE_R6_SHADOW_RESULTS.json). El comparador exige el
SHA256 revisado de `kwin/src/scene/shadowitem.cpp`: extrae sin modificar
`distributeHorizontally`, `distributeVertically` y `ShadowItem::buildQuads`, y los ejecuta
con geometría Qt, `DecorationShadow` real y un contenedor mínimo de vértices. No arranca
KWin ni constituye una comparación visual entre escritorios completos.

El diagnóstico de captura verifica en el peer Wayland actual la guarda
`bwmScreenshareMonitorGuard.version=1` por IPC (PID 3195). El incidente histórico no se
atribuye a las sombras: esta comprobación no reproduce el crash original. No se cambian
las fuentes de miniaturas del shell diario.

### Corregido

* **Geometría:** las esquinas pequeñas conservan una unión fraccionaria compartida, sin
  el hueco introducido por `floor/ceil`. Se acota primero el solape de esquinas asimétricas
  y se redistribuyen también los lados opuestos. Ventanas menores de 5 unidades no dibujan
  sombra, como KWin. Las geometrías de `DecorationShadow` usan las dimensiones de la
  imagen; no se dividen por la etiqueta DPR de `QImage`. La escala de salida se aplica
  después. El centro sigue sin dibujarse.
* **Vida y notificaciones:** `ShadowState` observa sustitución y cambios de imagen,
  `padding` e `innerShadowRect` sobre el mismo objeto, desconecta el anterior y tolera su
  destrucción. Al recrear la decoración se transmite también la retirada de la sombra,
  aunque la nueva decoración no tenga ninguna. No usa `weak.lock()` sobre la barra.
* **Transporte:** memfd de sombra sellado contra escritura y cambio de tamaño; un fallo
  de `mmap`, sellado o envío no se da por enviado. El compositor valida dimensiones,
  stride, DPR, valores finitos y rectángulo interior antes de reservar memoria; copia con
  `pread` y rechaza lecturas cortas. Así una sombra truncada no provoca SIGBUS por lectura
  de un mapeo. El transporte de los marcos de ventana queda fuera de este cambio.
* **Daños y visibilidad:** se daña el área anterior y la nueva al cambiar o retirar una
  sombra, perder el auxiliar o mover la ventana. Fullscreen y maximizado de ambos ejes
  la suprimen, como `Window::wantsShadowToBeRendered`; un único eje conserva la sombra.
  Las reglas explícitas de usuario siguen mandando; una CSD sin marco remoto no recibe
  esta segunda sombra.
* **Preferencias originales:** Breeze conecta su primera decoración antes que el proveedor
  común de ajustes. Se completa una notificación pública `reconfigured` encolada después
  de la lectura, para que una sola ventana adopte el primer cambio de `[Common]` en
  `breezerc`. Sin modificar el plugin de Breeze, su diálogo ni el formato KDE.

### Comprobaciones

| Prueba | Resultado y límite |
| :--- | :--- |
| Referencia KWin: 192 casos sintéticos | Geometrías/UV iguales; raster CPU sin diferencia de color ni alpha. Incluye esquinas asimétricas, tamaños mínimos, DPR 1/1,25/1,5/2 y las mismas escalas de salida |
| 18 muestras del auxiliar real | BreezeDark/BreezeLight activas e inactivas a 1/1,25/1,5/2, Sweet-Dark Aurorae activa/inactiva; error CPU máximo 0 de color y alpha |
| ASan + UBSan | Los 192 casos y las 18 muestras pasan con el comparador, `ShadowState` y lector de búfer instrumentados; el auxiliar que produce las muestras es la compilación normal |
| `test_bwm_decorator.py` | 13/13: incluye memfd sellado, preferencias nativas quitar/restaurar tamaño/color, reconexión, claro/oscuro y Aurorae |
| `test_breezebars.py` | 4/4: compilación del plugin en copia, símbolos resueltos, lógica/protocolo y propiedad única de la barra |
| Hyprland anidado, Wayland SSD | Sombra KDE externa medida: **62 586 píxeles** cambian al suprimirla, con PID/geometría iguales y sombra genérica apagada. No acredita igualdad con el render de KWin |
| Compilación del candidato | `-fno-gnu-unique`; 0 símbolos UNIQUE; instalación atómica mediante `make install` sólo en `build/r6-plugin/installed` |
| Regresión R5 tras compilar el estado actual | CTest normal 8/8 y Python R4 262/262 |
| Política diaria | `test_plasma_shadow_policy.py` pasa: conserva el veto de contención |

El anfitrión del ensayo anidado usa una salida **virtual del compositor padre**, que se
retira al terminar. Una ventana oculta no recibía fotogramas; una salida headless dentro
del hijo fallaba al asignar búferes GBM NVIDIA. Las primeras pruebas con XWayland a demanda
se bloquearon durante la carga inicial; al deshabilitar XWayland y retirar DISPLAY el
ensayo Wayland pudo avanzar. La causa exacta de ese bloqueo no se ha contrastado con una
pila; **XWayland no queda probado**. Los dos avisos propios de aplicación sin respuesta se
retiraron por PID. La prueba final comprueba foco, puntero, modos/posiciones/reservas y
workspaces físicos, y handles de plugins sin cambios; 0 compositores/salidas de ensayo
residuales, capturas borradas y `hyprctl configerrors` vacío.

### Paneles, diálogos y siguiente paso

_Superado por la iteración 2: el protocolo de sombras KDE ya está implementado en el candidato._

KWindowSystem 6.29 delega `KWindowShadow` en `org_kde_kwin_shadow_manager`; el SDK de
Hyprland 0.56.2 no incluye ese servidor ni la lectura de `_KDE_NET_WM_SHADOW` de X11.
No se anuncian esas sombras como operativas. `DialogShadows` de libplasma y `PanelShadows`
de plasma-workspace son las referencias que debe conservar la siguiente iteración.

El desenfoque necesita una distinción: Hyprland sí incluye `ext_background_effect_v1`,
que KWindowSystem sabe usar. Los diálogos de libplasma llaman a `KWindowEffects`; el
`PanelViewHost::updateMask` experimental aún no reproduce `PanelView::updateMask` para
blur/contraste. No se ha certificado su efecto real ni se introduce una segunda captura
de pantalla para simularlo.

Queda pendiente: sombras nativas de paneles/menús/popups, contraste/desenfoque del panel,
XWayland y CSD en sesión, cambios de foco/resize/cierre y pérdida del auxiliar en el
render real, matriz gráfica a escalas fraccionarias, maximizado/bordes/fullscreen y
comparación visual/perfiles de alpha con una sesión Plasma equivalente. **No retirar
todavía el veto diario ni pedir otro inicio de sesión por esta iteración.** R5 conserva
su aceptación visual pendiente; no se declara aceptada por el usuario.

### Reproducir

```bash
env -u QT_QPA_PLATFORMTHEME python3 src/breezebars/check-r6-shadows.py \
  --kwin build/r6-upstream/kwin-6.7.5 --native-samples --asan \
  --report build/r6-shadow-results.json

python3 src/breezebars/check-r6-nested.py \
  --module build/r6-plugin/installed/breezebars.so \
  --helper src/bwm-decorator/bwm-decorator \
  --report build/r6-shadow-nested-results.json
```

El segundo comando requiere el candidato compilado **en una copia** y desplegado en esa
carpeta con `make install PLUGIN_DIR=/ruta/absoluta/build/r6-plugin/installed`. Nunca
recompilar encima de un `.so` cargado, ni cargar/descargar el candidato en la sesión diaria.
No hay commit ni push de este trabajo.

---

## Antecedente histórico (2026-11-12, revertido)

Ver [BREEZE_RECOVERY.md](BREEZE_RECOVERY.md): la habilitación adelantada se revirtió.

### Corrección adelantada del veto de sombras (parcial, no vigente)

2026-11-12. R0 identificó una causa independiente del anfitrión/editor: `breeze-float-all`
impone no_shadow=true a todas las ventanas, y `CBreezeShadow::draw` omite el render si la
regla noShadow() es verdadera. Esto cancela la sombra original enviada por KDecoration.

Retirado **sólo ese veto global**. Las sombras genéricas de Hyprland siguen apagadas mediante
appearance.lua; la sombra KDE conserva sus datos originales y los overrides explícitos del
usuario. La regla de Sin marco mantiene no_shadow=true y decorate=false. No se cambia CSD,
protocolo, C++ ni ABI; no requiere recompilar plugin. No se forzó reload en la sesión.

Regresión `tests/test_plasma_shadow_policy.py`: ejecuta el Lua de reglas con un colector,
verifica que los defaults permiten sombra y Sin marco sigue sin ella. Pasa.

Esta corrección no certifica sombras idénticas: quedan DPR, alpha, foco, animación, orden,
CSD, bordes, fullscreen, comparación contra Plasma y prueba con el binario realmente cargado.
R6 continúa abierta; se adelantó sólo este fallo P1 porque no depende de R2–R5. La prueba
visual se deja para mañana. Rollback: reponer el hunk no_shadow en la regla default, sin
alterar el renderizador ni reemplazar el .so cargado.
