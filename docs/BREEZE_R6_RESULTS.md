# R6 — sombras de decoración: primera iteración comprobada (2026-11-20)

Continúa desde R5 (§3.323). **R6 sigue abierta**. El candidato se ha probado fuera del
compositor diario; `breeze-float-all.no_shadow=true` sigue vigente. No se ha instalado el
candidato en `config/hypr/plugins`, reiniciado la sesión ni sustituido el auxiliar diario.
La skin observada al comenzar y terminar era `plasma`.

## Referencia y alcance

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

## Corregido

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

## Comprobaciones

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

## Paneles, diálogos y siguiente paso

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

## Reproducir

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
