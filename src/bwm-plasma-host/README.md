# bwm-plasma-host — experimento R4

Auxiliar fuera de Hyprland con Corona/Applet/PlasmoidItem originales. **No es el nuevo panel**.
Arquitectura y límites en `docs/BREEZE_R4_ARCH.md`; resultados en `docs/BREEZE_R4_RESULTS.md`.
No tiene instalación ni autostart. No ejecutar sobre la configuración real como ensayo.

```bash
cmake -S src/bwm-plasma-host -B /tmp/bwm-r4-build
cmake --build /tmp/bwm-r4-build -j4
python3 src/bwm-plasma-host/check-isolated.py \
  --binary /tmp/bwm-r4-build/bwm-plasma-host \
  --upstream /ruta/libplasma-6.7.5 \
  --external /ruta/al/plasmoide-elegido \
  --report /tmp/bwm-r4-results.json
```

El driver instala y retira paquetes en un TemporaryDirectory, aísla XDG, deshabilita el bus de
sesión para los hijos y usa Qt offscreen/software. La prueba de terceros carga QML ejecutable;
seleccionar y revisar el paquete antes. No modifica las fuentes seleccionadas. `--exercise`
sólo prueba una propiedad booleana de una página, no todas las configuraciones posibles;
usa la transacción del diálogo real. `--probe` carga con esa misma fábrica e informa también
configurationError y loader/module/component, sin dar por operativa una configuración fallida.

## Diálogo, catálogo y vista interactiva (continuación R4)

`ConfigurationSession` aloja las páginas originales mediante ConfigView: categorías,
Aplicar/Cancelar/Predeterminados, cambios pendientes, claves inmutables y detección de
conflictos. Usa QPointer porque ConfigView se autodestruye al ocultarse. Los casos que aún
no tienen adaptador (callbacks, categorías KCM o propiedades sin escritura/notificación) bloquean Aplicar con
explicación. No se anuncia compatibilidad universal.

Las páginas pueden usar source o configUiModule/configUiComponent. La pareja completa se
resuelve con Qt y tiene prioridad sobre source, como KDE 6.7.5; un módulo QML normal no se
rechaza como si fuera un KCModule. Propiedades cfg_/title declaradas se entregan antes de
Component.onCompleted, incluidas las required, con el contexto/localización de ConfigView.
Módulo/tipo ausente, raíz no Item y required desconocido bloquean Aplicar con su error real.
Los KCM por pluginName y callbacks sin adaptador siguen bloqueados.

El driver copia un módulo QML de prueba a su ruta de importación aislada e instala nueve
paquetes desechables en sus raíces temporales. Prueba prioridad módulo/source, fallback de pareja incompleta, source absoluto,
transacciones/dos instancias/reapertura y errores. Son fixtures BWM; no certifican módulos
QML de terceros. Las fuentes originales KDE/Andromeda también pasan por la fábrica común.

Una clave del esquema puede aparecer en varias páginas: sus cambios se sincronizan entre
ellas en memoria, sin escritura por deslizador ni reconstrucción de los contenedores QML.
Se rechazan controles con límites incompatibles. El driver instala además un paquete BWM
desechable con dos categorías para probar esa sincronización, Cancelar/Predeterminados,
conflictos, efecto en la representación nativa y lectura de dos instancias desde otro proceso.
Este fixture amplía las regresiones; la prueba de un complemento externo sigue siendo Andromeda.

El paquete Plasma/Shell mínimo resuelve sus vistas con KPackage. AppletPopup recibe las
representaciones nativas; el marco de diálogo y la vista son adaptadores BWM, no el editor R5.
`Catalog` combina paquetes QML y applets compilados. Un solo watcher con debounce refresca
el catálogo. Obtener nuevos abre KNSWidgets::Dialog con el proveedor plasmoids.knsrc original;
la descarga remota todavía necesita aceptación, además de los jobs locales ya probados.

Prueba automática completa (seleccionar explícitamente las fuentes):

```bash
cmake -S src/bwm-plasma-host -B /tmp/bwm-r4-build \
  -DBWM_TEST_UPSTREAM=/ruta/libplasma-6.7.5 \
  -DBWM_TEST_EXTERNAL=/ruta/al/plasmoide-elegido
cmake --build /tmp/bwm-r4-build -j4
ctest --test-dir /tmp/bwm-r4-build --output-on-failure
```

Necesita KF6 NewStuffWidgets además de las dependencias anteriores; Qt Test para los ensayos.
En la prueba interactiva, el script crea un entorno temporal e instala allí una copia:

```bash
python3 src/bwm-plasma-host/preview-isolated.py \
  --binary /tmp/bwm-r4-build/bwm-plasma-host \
  --package ~/.local/share/plasma/plasmoids/AndromedaLauncher
```

Se prueba Configurar y abrir/cerrar el widget. No se abre automáticamente en la sesión.
El anclaje Wayland tiene un adaptador experimental descrito más abajo, pendiente de sesión.
Los Dialog propios tienen ahora un registro pre-superficie experimental; otros tipos siguen
pendientes. El panel activo no se modifica. Cerrar la vista termina
el auxiliar y retira el entorno temporal. Ctrl+C también detiene el hijo antes de limpiarlo.
Las raíces temporales no son un sandbox de código: las acciones de un widget pueden lanzar
programas; la comprobación se centra en la configuración, sin activar acciones de sesión.

## Actualizar desde upstream

1. Fijar versión de libplasma, Qt/KF6 y tarball/commit. Revisar las advertencias de API privada.
2. Contrastar paquetes en packages.cpp/plasma_applet_packagestructure.cpp y shellpackage.cpp;
   luego AppletQuickItem, ConfigView, ConfigModel y el shell/containment original de Plasma.
3. Actualizar la versión EXACT de CMake sólo después de compilar y revisar cambios de contrato.
4. Repetir representaciones, contextos/localización, todos los tipos de configuración,
   Apply/Cancel/Defaults, dos instancias, reinicio, instalación/retirada y paquetes externos.
   Revisar también notificaciones/aliases cfg_ y páginas con claves compartidas, límites y
   ausencia de escrituras/reconstrucciones durante cambios consecutivos de un deslizador.
5. Revisar los muebles/popup del shell y su integración layer-shell antes de activar en BWM.
6. Conservar licencias de cualquier código que se porte; el prototipo actual es propio y sólo
   llama las bibliotecas instaladas. Los ejemplos KDE y el paquete externo se leen de fuentes
   seleccionadas durante las pruebas y no se distribuyen aquí.
7. Revisar QScreen fabricante/modelo/serie y el contrato de retirada de Qt. Los fixtures QPA
   de Qt 6.11.2 sólo se ejecutan en offscreen; repetir hotplug, binding sustituido, ciclo de
   vistas por skin, ventanas propias y reapertura con enumeración/conectores cambiados.

## Superficies y migración (2026-11-13)

LayerShellQt >=6.7.5 es ahora dependencia explícita. `--layer-preview` y la opción
`preview-isolated.py --layer-panel` usan roles por ventana, no una variable global que altere
los diálogos. El popup conserva el contenido Plasma nativo y recibe anclaje en píxeles lógicos.
La negociación con Hyprland, foco y monitores reales todavía requieren aceptación de sesión.

`--stage-migration PLAN.json` y `--verify-stage DIRECTORIO` sólo funcionan con las cuatro
raíces XDG temporales existentes, como los otros ensayos. No usar el JSON real como fixture.
La carpeta nativa preparada contiene layout (Corona), plasmashellrc (vista), legacy.json y report.json. No sobrescribe
un destino existente ni activa el panel. Los bindings desconocidos se rechazan; el reloj
conserva showSeconds false→ToolTip(1), true→Always(2). Requiere plasma-desktop 6.7.5 instalado
para materializar org.kde.panel y sus widgets. La activación del panel sigue pendiente.
CTest cubre las superficies, la lectura del staging en un proceso nuevo y las rutas de error.

La migración conserva bar.plasma.edge y deriva el FormFactor nativo. Si falta el borde usa
bar.bottom, cuyo valor por defecto es false (arriba), como el panel heredado. C++ verifica
contra el origen archivado, sin confiar sólo en el campo de la propuesta. El probe comprueba
orden por x/y según la orientación. Los informes nuevos versionan este contrato; los antiguos
siguen leyéndose como el staging bottom/horizontal que realmente producían. No se corrigen
reescribiéndolos: se prepara otro staging desde el origen. Siete casos de dos paneles pasan
stage→lectura→QML original→lectura, con archivo de origen intacto.

Las propuestas incluyen nativeViewSettings para thickness/floating/panelOpacity. C++ vuelve
a derivarlos del origen: grosor con fallback/clamp de PanelLogic, flag original de flotación
y enum de opacidad, incluida la antigua combinación style=floating→Adaptive+floating.
El alfa numérico heredado no se transforma en ese enum. El archivo plasmashellrc preparado
usa grupos KDE y los IDs asignados por Corona; no es un reemplazo del archivo completo de
la sesión. La activación futura debe mezclar por panel con la política del destino.

viewSettingsContractVersion=1 exige origen/informe/archivo coherentes. deferredViewSettings
conserva valores y explica lo no adaptado: longitud relativa, alineación, visibilidad/reservas,
gap, docking y estilos adaptables. --probe-stage-frame DIRECTORIO carga Panel.qml con el
archivo preparado, comprueba render/valores/orden y falla explícitamente con Adaptive.
Los stages antiguos sin ese contrato siguen siendo legibles por --verify-stage; no pueden
presentarse como una prueba de migración de preferencias del marco. El driver prueba ocho
casos, dos paneles, lectura en otros procesos y alteraciones, sin cambiar la raíz de preferencias.
Evidencia: docs/BREEZE_R4_VIEW_MIGRATION_RESULTS.json. Revisión upstream: PanelView/Panel.qml
6.7.5 y semántica heredada de Config.qml/PanelLogic.js al cambiar el esquema de origen.

## Panel original (continuación tras instalar plasma-desktop)

`--probe-stage DIRECTORIO` carga el containment/QML original y verifica disposición de los
widgets mediante su LayoutManager. Es una prueba con ventanas; el driver fuerza offscreen.
El staging ya conserva AppletOrder y ajustes nativos de Kickoff/tareas/bandeja/reloj.
Los favoritos de Kickoff requieren importación al nuevo cliente KAStats, aún sin probar.

`PanelSession` conecta la acción Configurar del widget original con sus páginas, por ID.
QtTest prueba Aplicar/reapertura/dos instancias desde el panel original y la ventana de menú
creada por el propio Andromeda. No se confunde esa ventana con el AppletPopup del anfitrión.

Vista opcional de dos instancias en org.kde.panel:

```bash
python3 src/bwm-plasma-host/preview-isolated.py \
  --binary /tmp/bwm-r4-build/bwm-plasma-host \
  --package ~/.local/share/plasma/plasmoids/AndromedaLauncher --native-panel
```

Añadir `--layer-panel` selecciona el adaptador LayerShellQt sin reserva de área; su validación
Wayland está pendiente. Cerrar la ventana normal o Ctrl+C limpia el ensayo. El panel no ofrece
el editor R5. Los controles de un diálogo sin páginas quedan bloqueados con explicación.

El catálogo expone catalogVisible según filtros KDE, metadatos y evaluación runtime por paquete;
los desconocidos siguen visibles con evaluación pendiente. Tareas/pager/Mostrar escritorio
necesitan adaptadores de backend BWM; que sus datos se guarden no los hace operativos.
Al actualizar upstream revisar también LayoutManager/AppletOrder, el filtro WidgetExplorer y
los protocolos de libtaskmanager; repetir el clic real de ventanas propias de complementos.

PanelSession proporciona ahora panelInfo/widgets/order, addWidget/removeWidget, requestOrder,
widgetActions/triggerAction y configure. El catálogo se consulta por metadatos actuales, sin
tabla fija de widgets; la vista original se enlaza mediante bindPanelItem. El ejecutable deja
el QObject en la propiedad bwmPanelSession de la ventana del panel. Son contratos dentro del
auxiliar, sin IPC externo ni activación del panel diario. API completa en BREEZE_R4_ARCH.md.

La retirada es permanente y nativa; cierra Configurar antes de limpiar el esquema y respeta
inmutabilidad. Las acciones usan identidad de QAction y pertenencia por Applet: no se disparan
tokens obsoletos, ajenos, ocultos o deshabilitados. Preparar el menú una vez con widgetActions;
refrescar estados con prepare=false evita volver a ejecutar la fábrica del complemento.
requestOrder acepta una permutación exacta y delega el método original reorderApplets. Su
retorno acredita despacho; el consumidor verifica order y el resultado del LayoutManager.

Para conservar el panel, usar loadLayout sobre su archivo antes de crear containments y
saveLayout sobre el mismo propietario, con config()->sync(). AppletOrder del containment
está en General, no en Configuration/General. Exportar a otro nombre no sustituye este ciclo.
CTest añade/retira/recrea instancias, cambia su orden, verifica la serialización nativa y carga
el panel/posiciones/valores en otro proceso. No valida geometría o foco Wayland.
Al actualizar, revisar también Applet.destroy/destroyedChanged y Corona.loadLayout/saveLayout/
saveState, main.qml/reorderApplets, LayoutManager.js y menús dinámicos QAction/submenús.

`--theme-catalog` inventaría Plasma/LookAndFeel mediante KPackage: defaults nativos con KConfig,
referencias de componentes, archivos propios/heredados y scripts de layouts/setup con hash.
No aplica configuraciones ni ejecuta scripts; executeAllowed=false. El driver instala/retira un
tema desechable y comprueba claves desconocidas y rutas nativas. Al actualizar, revisar también
shell/packageplugins/lookandfeel/lookandfeel.cpp y su contrato de fallback.

## Dialogs del paquete y geometría de salida

PackageWindows enlaza el contexto nativo del Dialog con su Applet. En una vista layer-shell,
prepara sólo Dialog ocultos sin superficie, conserva ancla o posición solicitada y expone sus
capacidades. No toma ventanas ajenas ni sustituye roles ya creados. Los Dialog Tooltip/
outputOnly/OSD/notificaciones reciben ahora rol no interactivo (continuación Wayland de R4).
Window genérico y anclas externas siguen pendientes.
ViewCorona suministra geometría Qt real a los widgets del ejecutable; el staging usa fixtures.
Las reservas que Qt no comunique y la negociación Wayland requieren validación independiente.

Para la prueba manual preparada, añadir `--native-panel --layer-panel` al comando anterior.
CTest prueba tanto el Dialog propio de Andromeda como uno desconocido, los límites de adopción,
la posición solicitada y la geometría de la salida. No certifica foco o posición en Hyprland.
Al actualizar upstream revisar Dialog.componentComplete/setVisible, el contexto plasmoid y
la creación de roles LayerShellQt, además de las comprobaciones de memoria y lifecycle.

## Sesión Wayland (2026-11-13)

Probado en Hyprland con Andromeda: menú y avatar colocados sobre el panel en los dos monitores.
`--output "descripción"` elige la salida por su descripción (nunca DP-N). El auxiliar desactiva
las posiciones fijas de Qt Wayland al crear QApplication, como plasmashell; el panel no toma
el foco salvo que el containment lo pida. Diagnóstico de anclaje con
`QT_LOGGING_RULES="bwm.r4.anchor.debug=true"`. Resultados y límites en
`docs/BREEZE_R4_RESULTS.md`. Los menús se cierran al pulsar fuera con `hyprland_focus_grab_v1`
(necesita Qt6 WaylandClient y hyprland-protocols al compilar). El fondo original del panel se
aloja ahora en la vista descrita a continuación; su aceptación Wayland y el desenfoque siguen pendientes.

## Marco nativo de Panel.qml

--native-panel ya aloja el Panel.qml instalado mediante PanelViewHost/ContainmentView,
con su fondo SVG original y el containment org.kde.panel dentro. No copia ni parchea esa
vista. Dos temas SVG de prueba verifican en offscreen el cambio en vivo y prefijos de los
cuatro bordes, además de flotación/padding, dimensiones, máscara y NoBackground.
Configurar sólo abre una ConfigurationSession. KF6 Svg es dependencia explícita del build;
KSvg ya era requisito de la skin. La tabla de requisitos incluye el cambio.

--probe-panel-frame ID es una prueba de carga/render de la misma ruta; requiere las raíces
XDG temporales, como los otros probes. El driver la ejecuta con Qt offscreen. Expone
nativeViewLoaded, nativeContainmentAttached, frameReadbackAvailable y capacidades; no
certifica Wayland. Los layouts de panel y probes de widgets tienen propietarios distintos.

El adaptador admite políticas fijas Opaque/Translucent y flotación con vista previa y guardado
explícito. length sigue siendo tamaño natural; setLengthRange aplica los límites de superficie. Adaptive, autohide,
reservas, desenfoque y sombras externas siguen sin backend operativo en esta vista. No se
ofrecen como controles activos. UI e integración del ciclo por skin pendientes; no es el nuevo
editor R5 ni sustituye el panel diario.

viewSettings/reloadViewSettings/applyViewSettings usan PanelViewSettings y plasmashellrc,
en los grupos originales PlasmaViews/Panel <id>, Defaults y Horizontal<ancho>/Vertical<alto>.
Persisten floating, floatingApplets, panelOpacity, thickness, minLength y maxLength. Se
conservan claves ajenas y la cascada KConfig/kdedefaults; no se escribe por cada setter visual.
Aplicar es explícito, valida tipos/rangos/bloqueos/conflictos de todos los destinos y rechaza
opciones sin backend. Tras cambiar salida/orientación se debe recargar antes de guardar.
No hay copia de estas preferencias a un applet ni a ajustes compartidos de otra skin.

Reproducción de la vista optativa tras compilar en /tmp/bwm-r4-panel-view-build:

```bash
python3 src/bwm-plasma-host/preview-isolated.py \
  --binary /tmp/bwm-r4-panel-view-build/bwm-plasma-host \
  --package ~/.local/share/plasma/plasmoids/AndromedaLauncher --native-panel --layer-panel
```

Al actualizar revisar Panel.qml, panelview.h/.cpp, ContainmentView y SharedQmlEngine, los
enums Global y el contrato de máscaras/padding KSvg. Datos y límites:
docs/BREEZE_R4_PANEL_VIEW_RESULTS.json y docs/BREEZE_R4_RESULTS.md.

## Coordinación de paneles por salida y skin

PanelRuntime coordina vistas de los paneles ya cargados en ViewCorona. setAssignments
recibe IDs→descripciones del llamador; setSkin(plasma/retro/default) activa/retira vistas
sin destruir las instancias nativas. panels expone estados y motivos; view(id) permite
consumir PanelSession dentro del proceso. reconcile es idempotente, agrupa geometría y
relee el ámbito nativo tras un cambio de resolución lógica. Un borde distinto recrea sólo
su vista/rol. Sin reservas, autostart, IPC de editor ni altas/bajas de panel completo. El
envoltorio siguiente añade sólo la conexión explícita de prueba al gestor de skins.

El llamador conserva Corona viva y los bindings fuera de la configuración de los applets;
su autoridad/persistencia diaria sigue pendiente. El anfitrión duradero debe permanecer
vivo sin ventanas (quitOnLastWindowClosed=false), guardar el layout propietario con Corona
y conectar setSkin al gestor común. El JSON de bindings del test es sólo un fixture.

BwmOutput resuelve fabricante/modelo/serie de Qt con descripción completa, secuencia final
modelo+serie o modelo único. Rechaza conectores, subcadenas y ambigüedad; no mueve el panel
a otra salida si falta la solicitada. Este resolvedor también se usa con --output. Un monitor
idéntico sin identidad diferenciable queda pendiente de selección explícita, no se adivina.

--preview-stage DIR consume el informe verificado de una migración temporal y ofrece sus
paneles con layer-shell; falla con diagnóstico si ninguno tiene salida disponible.
--probe-stage-runtime DIR produce un snapshot de esa ruta con tiempo limitado. Ambos
requieren las raíces XDG temporales habituales. La previsualización puede escribir el
layout temporal mediante los applets originales; su informe conserva el contrato del staging
inicial y puede requerir prepararse de nuevo tras editarlo. No es la activación diaria.

QtTest usa dos pantallas QPA propias en offscreen y prueba retirada antes del fallback de
Qt, reconexión, duplicados, cierre de configuración pendiente/ventanas propias, cambios de
borde/resolución y reapertura. No equivale a una prueba de Hyprland, escala fraccionaria o
cambio de skins reales. Datos y límites: docs/BREEZE_R4_RUNTIME_RESULTS.json y arquitectura.

## Previsualización que sigue la skin

El hook skinChanged del manifiesto está conectado al gestor común, pero no actúa mientras
no haya una previsualización registrada explícitamente. No arranca el auxiliar ni sustituye
el panel diario. Para el ensayo opt-in, tras compilar:

```bash
python3 src/bwm-plasma-host/preview-isolated.py \
  --binary /tmp/bwm-r4-panel-view-build/bwm-plasma-host \
  --package ~/.local/share/plasma/plasmoids/AndromedaLauncher \
  --native-panel --layer-panel --follow-skin --output "MAG 274Q X24"
```

Usar la descripción/modelo exacto y único que Qt identifica en la salida elegida. El perfil
es temporal y su D-Bus no conecta a la sesión. En Breeze muestra el panel de prueba; al
salir lo retira y permanece vivo para volver. Sin coincidencia no mueve la vista a otro
monitor. Este comando no se ha ejecutado en la sesión Wayland durante esta continuación.

Ctrl+C envía stop y espera el guardado nativo. También se puede detener únicamente la prueba:

```bash
python3 config/hypr/skins/plasma/scripts/panel-session.py stop
```

Para consultar una prueba registrada desde otro terminal:

```bash
python3 config/hypr/skins/plasma/scripts/panel-session.py status
```

La consulta espera una respuesta nueva del auxiliar. No cambia de skin ni vuelve a cargar
el panel. Informa carga QML, exposición y fotograma enviado por Qt, errores y bloqueos por
salida. Sin registro devuelve active=false sin crear archivos; un auxiliar bloqueado agota
el timeout y termina con error, sin reutilizar un ack anterior. renderReady no acredita
presentación física ni servicios del widget. replacementReady sigue false: la prueba no
confirma reservas ni autoridad para retirar el panel diario. Este comando es también el
contrato de diagnóstico para el futuro controlador de activación; no lo activa.

El ensayo opcional de política nativa se activa añadiendo --native-policy al comando
--follow-skin anterior (también funciona con --profile). Consume panelVisibility=0/3 del
plasmashellrc del perfil; si falta, usa NormalPanel=0. Pide o retira espacio mediante
LayerShellQt con el grosor nativo y sin reservar dos veces el padding flotante. Al usarlo
en Wayland puede cambiar el área disponible para ventanas maximizadas: no reemplaza la
barra existente. Sus reservas/posiciones en coexistencia requieren validación real.

Es necesario conservar --native-policy al reabrir perfiles que guarden NormalPanel. Sin
la opción la previsualización habitual rechaza esa política; una variable de entorno
heredada no la habilita. AutoHide/Dodge, alineaciones/offset distintos de los admitidos
y varios paneles nativos en una misma salida se rechazan con diagnóstico. Dos salidas
distintas pueden tener sus políticas independientes. status informa reservationRequested/
exclusiveZoneRequested, mantiene reservedArea/waylandVerified/replacementReady=false y
explica la reserva sin verificar. Ctrl+C/stop o salir de Breeze retiran las vistas/peticiones.
La API applyViewSettings admite panelVisibility sólo en este modo, con transacción KDE,
inmutabilidad, concurrencia y readback. No se añade un selector ni el editor R5.

RuntimeControl y el publicador intercambian control/ack atómicos en un directorio privado,
con token, revisión creciente y bloqueos. El registro verifica PID+inicio, rechaza duplicados
y no modifica preferencias de usuario. Si el hook de salida no recibe confirmación, el
gestor aborta antes de mutar perfiles e intenta recuperar el auxiliar anterior. La limpieza
espera al lector del ack para evitar perder la confirmación de stop. No se ejecutan órdenes
de compositor mediante este canal ni se añade otro servidor D-Bus. La parada no activa una
sustitución diaria ni convierte el perfil temporal en un appletsrc alternativo.

Pruebas: hook común real→publicador→Qt, control ajeno/antiguo rechazado, no-op sin registro,
PID muerto/reutilizado, unicidad y CLI/envoltorio con parada/Ctrl+C. Revisar al actualizar
QFileSystemWatcher, QSaveFile, QLockFile y el orden before/after del gestor. Datos y alcance:
docs/BREEZE_R4_SKIN_CONTROL_RESULTS.json. Integración de producción/activación y aceptación
Hyprland/escala/skins siguen pendientes; no hay avance al editor R5.

## Perfil de ensayo conservado entre ejecuciones

Si falla el acceso a la sesión desde el asistente, ejecutar en una terminal normal:

```bash
python3 /mnt/HDD1TB/Projects/hyprland-de/config/hypr/skins/plasma/scripts/r4-session-check.py
```

El diagnóstico tiene tiempos límite y genera un informe privado en /tmp. Recoge sólo
monitores, capas del auxiliar y su status, sin abrir/mover ventanas ni reiniciar nada.
Confirmar acceso no confirma reservas ni completa R4; ver BREEZE_R4_ACCESS_RESULTS.json.

Para un ensayo temporal de reserva en Breeze, ejecutado desde esa terminal con acceso:

```bash
python3 /mnt/HDD1TB/Projects/hyprland-de/config/hypr/skins/plasma/scripts/r4-reservation-smoke.py \
  --run --output "DESCRIPCIÓN EXACTA DEL MONITOR"
```

El panel temporal se abre y cierra automáticamente. Mide reserva antes/durante/después,
exige restauración. Las órdenes directas del runner sólo operan sobre su fixture; el puente
de Breeze puede reajustar ventanas BWM ya maximizadas al cambiar reserved. Informe privado en /tmp.
Por defecto usa el binario normal de /tmp/bwm-r4-panel-view-build y el ejemplo original KDE
de /tmp/bwm-r4-config-pages-upstream; --binary/--package permiten indicar otras rutas.
Un delta verificado aún no certifica maximizado, posición, skins o cierre completo de R4.

Añadir --maximize realiza además la medición con una ventana propia temporal, usando el
gestor de maximizado BWM con PID/dirección verificados. Mide el marco completo y exige su
registro breezebars-csd; si falta, no certifica la decoración. Escala 1/giro 0 únicamente.
Maximiza su ventana antes de abrir el panel y mide el reajuste al aparecer y al retirarlo,
sin remaximizar en ambas observaciones automáticas. Conserva además medidas explícitas con
y sin panel. Ventana/panel se cierran solos; no cambia foco ni mueve directamente ventanas ajenas.
Los flags de área/maximizado pueden pasar para ese caso sin marcar r4Complete=true.

Tras actualizar kwin_area.py, el proceso antiguo del puente no carga Python de nuevo solo.
Para cargarlo y ensayar los dos sentidos en una misma ejecución local:

```bash
python3 /mnt/HDD1TB/Projects/hyprland-de/config/hypr/skins/plasma/scripts/r4-reservation-smoke.py \
  --run --maximize --refresh-area-watcher \
  --output "Micro-Star Int'l Co. Ltd. MAG 274Q X24 0x01010101"
```

El flag reinicia sólo kde-config-bridge por su ciclo existente y exige baseline nuevo con
PID/inicio/fecha privados. No reinicia compositor, shell ni plugins. El puente queda activo
para seguir cambios del área útil de máximos BWM, incluidos los que ya estén abiertos.
No cambia geometría de ventanas normales/fullscreen/especiales/minimizadas, ni escribe la
restauración. Respeta Force KDE y los opt-outs documentados. dynamicMaximizedWindowVerified
requiere ahora ambos sentidos; dynamicMaximizedContract lo identifica en el informe.
El marcador no prueba el reajuste. El usuario ya valida ambos sentidos en MSI inferior,
escala 1/giro 0 y modo completo: marco 1396→1348→1396 de alto, reserva 44→92→44 y limpieza
correcta. Evidencia real en docs/BREEZE_R4_AREA_SESSION_RESULTS.json y aislada en
docs/BREEZE_R4_AREA_TRACKING_RESULTS.json. Otras combinaciones e integración diaria siguen
pendientes; el éxito no habilita replacementReady ni completa R4.

ProfileStore conserva completos los archivos nativos de una migración verificada y sus
bindings por ID/descripción, con procedencia original separada. No genera un appletsrc
alternativo. El CLI mantiene las cuatro raíces XDG temporales obligatorias; el destino
inicial de importación debe ser privado y temporal, sin sobrescribir un perfil existente.
Puede exportarse después al almacenamiento XDG dedicado descrito a continuación.

Con ese entorno aislado preparado:

```bash
/tmp/bwm-r4-panel-view-build/bwm-plasma-host --import-profile "$XDG_CONFIG_HOME/bwm-native-staged"
/tmp/bwm-r4-panel-view-build/bwm-plasma-host --checkpoint-profile "$XDG_CONFIG_HOME/bwm-native-profile"
```

La primera orden crea bwm-native-profile dentro de XDG_CONFIG_HOME; la segunda devuelve la
ruta/ID de su snapshot. --profile-info DIR inspecciona el perfil y --restore-profile
RUTA_DEL_SNAPSHOT verifica sus hashes y selecciona una generación nueva, conservando la vieja.
Las operaciones rechazan un perfil ocupado. Los snapshots se toman tras guardar/sincronizar
y cerrar los propietarios de configuración nativos; no hay GC ni promesa de durabilidad
frente a un corte de energía. Conservar los directorios temporales es responsabilidad del
ensayo: /tmp puede borrarse al reiniciar el equipo.

Reabrirlo sin recrear widgets ni sustituir el panel activo:

```bash
python3 src/bwm-plasma-host/preview-isolated.py \
  --binary /tmp/bwm-r4-panel-view-build/bwm-plasma-host \
  --profile "$XDG_CONFIG_HOME/bwm-native-profile" --follow-skin
```

Las salidas vienen del perfil; --output no las sobreescribe. El envoltorio busca paquetes
instalados en los paths XDG del llamador y conserva config auxiliar/caché/runtime/D-Bus
desechables. El binario --serve-profile mantiene el lease, carga/guarda el mismo layout con
Corona y toma un checkpoint tras salir limpiamente. Detener con Ctrl+C o panel-session.py
stop. El envoltorio limpia su registro/control, y conserva el perfil seleccionado.

Al actualizar upstream revisar Corona.loadLayout/saveLayout/sync, jerarquía de preferencias,
IDs y ciclo de KSharedConfig. Repetir edición de widget/vista, dos instancias, skin, proceso
nuevo, desconocidos, perfil ocupado y restauración mientras un escritor antiguo retiene su
ruta. Esa restauración copia a otra ruta y no puede ser sobrescrita por el escritor viejo.
Evidencia: docs/BREEZE_R4_PROFILE_RESULTS.json. No es activación/rollback del panel diario;
su autoridad y aceptación Hyprland/escala siguen pendientes.

## Conservar el perfil fuera de /tmp

Con un perfil de ensayo existente, la exportación no necesita preparar variables XDG a mano:

```bash
python3 src/bwm-plasma-host/preview-isolated.py \
  --binary /tmp/bwm-r4-panel-view-build/bwm-plasma-host \
  --profile /ruta/al/perfil-de-ensayo --export-as breeze-test
```

Devuelve el destino en `$XDG_STATE_HOME/bwm/plasma/panel-profiles/breeze-test`, con fallback
a `~/.local/state/bwm/plasma/panel-profiles/breeze-test`. Copia el estado seleccionado y todo
el historial de snapshots, valida hashes/datos y termina sin abrir ni registrar un panel.
Conserva la fuente y sus generaciones no seleccionadas; no sobrescribe un nombre existente.
Las carpetas del almacenamiento dedicado deben ser propias, privadas y sin alias. Sólo
esta autoridad XDG amplía el límite de /tmp; no se habilitan carpetas arbitrarias.

Para la previsualización explícita, usar la ruta que devuelve la exportación:

```bash
python3 src/bwm-plasma-host/preview-isolated.py \
  --binary /tmp/bwm-r4-panel-view-build/bwm-plasma-host \
  --profile /ruta/devuelta/por/la/exportacion --follow-skin
```

No selecciona ni sustituye el panel diario y no añade autostart. El perfil queda en estado
persistente; los auxiliares/caché/runtime/D-Bus siguen siendo temporales. No se han escrito
perfiles en el estado real del usuario ni reiniciado el equipo en estas pruebas. Se usa
un fixture fuera de /tmp, se elimina la fuente y se verifica reapertura, guardado, restore,
historial e integridad. Evidencia: docs/BREEZE_R4_STATE_PROFILE_RESULTS.json.

## Obtener nuevos sin diálogo y puerta con widget desconocido (2026-11-14)

`--kns-search TÉRMINO [PÁGINA]`, `--kns-install ID` y `--kns-uninstall ID` usan KNSCore con el
proveedor nativo `plasmoids.knsrc` (mismos Entry/Transaction que el diálogo «Obtener nuevos»).
Sólo con XDG_CONFIG/DATA/CACHE temporales; toda pregunta de KNewStuff se responde Cancelar/No.
Instalar/quitar informa también del alta/baja en el catálogo vivo (su watcher único).

`kns-cycle.py --binary … --report …` (necesita red) elige candidatos por el orden de la tienda,
no por una lista del código; rechaza antes de cargar paquetes con binarios/scripts o fuentes de
datos `executable` (filtro estático, no sandbox), ejercita su opción booleana propia por su página
original, la relee en un proceso nuevo y retira cada paquete por KNS. Paquetes con metadatos
antiguos (`KPlugin.ServiceTypes` sin `KPackageStructure`) se clasifican: KPackage 6.29, y por tanto
el explorador de Plasma 6.7.5, tampoco los lista. Al actualizar KNewStuff revisar
`Transaction`/`Installation` (preguntas, `Uncompress=kpackage`) y el filtro de `packageloader.cpp`.

Las páginas siguen ahora `AppletConfiguration.qml` 6.7.5: se llama a `saveConfig()` antes de
guardar y se ignoran las `cfg_` que no están en `main.xml` (antes bloqueaban la página). El
diálogo y la vista de prueba pintan `Kirigami.Theme.backgroundColor`, como el original, porque el
auxiliar pide ya búferes con alfa igual que plasmashell.
