# R6 — sombras y efectos nativos de KDE

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
