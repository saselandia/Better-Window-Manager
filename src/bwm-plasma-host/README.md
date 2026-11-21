# bwm-plasma-host — experimento R4

Auxiliar fuera de Hyprland con Corona/Applet/PlasmoidItem originales. **No es el nuevo panel**.
Arquitectura y límites en `docs/BREEZE_R4_ARCH.md`; resultados en `docs/BREEZE_R4_RESULTS.md`.
No tiene instalación ni autostart. No ejecutar sobre la configuración real como ensayo.

```bash
cmake -S src/bwm-plasma-host -B /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host
cmake --build /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host -j4
python3 src/bwm-plasma-host/check-isolated.py \
  --binary /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host/bwm-plasma-host \
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
cmake -S src/bwm-plasma-host -B /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host \
  -DBWM_TEST_UPSTREAM=/ruta/libplasma-6.7.5 \
  -DBWM_TEST_EXTERNAL=/ruta/al/plasmoide-elegido
cmake --build /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host -j4
ctest --test-dir /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host --output-on-failure
```

Necesita KF6 NewStuffWidgets además de las dependencias anteriores; Qt Test para los ensayos.
En la prueba interactiva, el script crea un entorno temporal e instala allí una copia:

```bash
python3 src/bwm-plasma-host/preview-isolated.py \
  --binary /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host/bwm-plasma-host \
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
  --binary /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host/bwm-plasma-host \
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

`r4-session-check.py --tray` consulta al dueño actual del servicio de iconos SNI y devuelve
el número de iconos y si hay un host registrado. Es una lectura puntual de D-Bus, sin
arrancar el servicio ni registrar otro host. El estado del panel también enumera los
plasmoides vivos dentro de la bandeja KDE mediante `embeddedApplets`. Son dos inventarios
distintos. Véase §274 en `docs/BREEZE_R4_RESULTS.md`.

Con Quickshell como dueño y al menos un icono registrado, `check-native-tray.py` comprueba
que la bandeja original de KDE obtiene las mismas filas de ese watcher. Ejecuta el
anfitrión offscreen y utiliza `xdg-dbus-proxy` para limitarlo a ese servicio. Registra
un nombre de host temporal que desaparece al salir. Comprueba el dueño y la lista
antes y después. La salida sólo contiene contadores y resultados de comparación.
El ensayo cubre la enumeración SNI. Los datos de cada icono, clics y menús quedan
pendientes. Véase §276 en `docs/BREEZE_R4_RESULTS.md`.

`check-native-tray.py --properties` mide además si cada fila SNI presenta estado y
categoría tras la respuesta D-Bus y produce un pixmap de 22 px usando el icono de
KDE. El estado se lee como valor de `Plasma::Types::ItemStatus` y el informe cuenta
la disponibilidad del pixmap por separado. El permiso adicional es `Properties.GetAll`
en cada objeto registrado. Los nombres activables quedan excluidos. Para leer
servicios anunciados sólo por su nombre único, el proxy del sistema necesita un
alias del mismo dueño. El resultado indica cuántos elementos se pudieron autorizar,
cuántos aportaron propiedades y cuántos produjeron un pixmap. El ensayo se ejecuta
fuera de pantalla y cubre la lectura del modelo.

Si algún elemento queda fuera del filtro, el informe distingue alias ausente, nombre
activable o dueño no disponible. Una consulta directa al dueño único puede comprobar
estado y categoría y contar nombres de icono. Estos contadores son independientes
del modelo KDE y no incluyen imágenes ni convierten en éxito un resultado parcial.

Para nombres únicos sin alias, `build-tray-proxy.py` compila una variante local de
`xdg-dbus-proxy` 0.1.8 desde un archivo original verificado. En Gentoo busca el archivo
en `/var/cache/distfiles`; `--archive` admite otra ruta. `--properties` selecciona
esa copia si existe y añade un permiso `GetAll` para cada nombre único y objeto
exactos. El filtro se verifica durante la compilación. El comprobador muestra
`uniqueNameFilter: exact-object` cuando usa esa versión. El ensayo de enumeración
mantiene el proxy del sistema. Véase §280 en `docs/BREEZE_R4_RESULTS.md`.

Con `BUILD_TESTING`, el objetivo `test-plasma-tray-events` comprueba el alta, el
cambio de estado y pixmap, y la retirada de un elemento en el modelo original.
`check-native-tray-events.py` lo ejecuta fuera de pantalla en un D-Bus privado
creado por `dbus-run-session`. El ensayo usa un watcher y un elemento de prueba.
Véase §284 en `docs/BREEZE_R4_RESULTS.md`.

`check-native-tray-events.py --filtered` repite el ciclo con el proxy local
`0.1.8+bwm-sni-unique-3`. Permite `NewStatus` y `NewIcon` por nombre único y objeto
exactos y exige el rechazo de una lectura en otra ruta. Véase §286 en
`docs/BREEZE_R4_RESULTS.md`.

`check-native-tray-events.py --actions` usa las entradas originales del plasmoide
para comprobar la entrega de activación principal/secundaria, rueda y
`ContextMenu` al icono de prueba del bus privado. Véase §288 en
`docs/BREEZE_R4_RESULTS.md`.

`check-native-tray-events.py --menu` usa `KF6StatusNotifierItem`, dependencia
del objetivo de pruebas, para exportar un menú D-Bus real. Comprueba que el
plasmoide respete el estado de sus opciones y que una acción ejecutada en el
menú importado llegue al productor. Véase §290 en `docs/BREEZE_R4_RESULTS.md`.

`check-native-tray-events.py --menu-wayland` crea una capa de prueba sin reserva
en el monitor enfocado al lanzar el ensayo en Hyprland. `--output` selecciona
un monitor por descripción. El productor y el watcher usan el bus privado. Pulsa
«Abrir menú de prueba» y después «Test action». El ensayo verifica el rol y el
anclaje del popup, su pantalla y la recepción de la acción. La capa se retira
al salir. Véase §§292–293 en `docs/BREEZE_R4_RESULTS.md`.

Para un ensayo temporal de reserva en Breeze, ejecutado desde esa terminal con acceso:

```bash
python3 /mnt/HDD1TB/Projects/hyprland-de/config/hypr/skins/plasma/scripts/r4-reservation-smoke.py \
  --run --output "DESCRIPCIÓN EXACTA DEL MONITOR"
```

El panel temporal se abre y cierra automáticamente. Mide reserva antes/durante/después,
exige restauración. Las órdenes directas del runner sólo operan sobre su fixture; el puente
de Breeze puede reajustar ventanas BWM ya maximizadas al cambiar reserved. Informe privado en /tmp.
Por defecto usa /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host/bwm-plasma-host y el fixture propio
src/bwm-plasma-host/tests/shared-config; --binary/--package permiten seleccionar otras rutas.
El informe identifica ambos paths. No necesita conservar una extracción de ejemplos KDE en /tmp.
Un delta verificado aún no certifica maximizado, posición, skins o cierre completo de R4.

Para medir el mismo borde en varias salidas, repite `--output` y selecciona `--edge left`,
`top`, `right` o `bottom`. El comprobador usa un perfil nativo temporal con un panel por
salida y compara las cuatro reservas de cada monitor. Exige un fotograma por panel, una
capa por salida solicitada y la restauración de todos los valores originales. El perfil
contiene un widget de prueba. Con `--maximize`, el informe de varias salidas añade
`maximizedByOutput` con las medidas de cada ventana.

Repite `--edge` para recorrer varios bordes en orden, por ejemplo `--edge left --edge right`.
El informe conserva un resultado por borde. Antes de iniciar el siguiente, el comprobador
exige que las reservas y la geometría coincidan con las iniciales. También exige un recibo
de salida del anfitrión propio después de sincronizar la configuración y, si usa un perfil,
crear su checkpoint. Si no hay recibo, limpia sus procesos y da el ensayo por fallido.
Con `--maximize`, la secuencia también exige el marco esperado antes de avanzar y
`maximizedEdges` resume el resultado explícito y el automático por borde.

Añadir --maximize realiza además la medición con una ventana propia temporal por salida, usando el
gestor de maximizado BWM con PID/dirección verificados. Mide el marco completo y exige su
registro breezebars-csd. La expectativa usa la escala y el giro efectivos de Hyprland
y aplica las reservas lógicas. Los resultados reales de §299 corresponden a escala 1 y giro 0.
El maximizador y el observador usan el mismo criterio de redondeo (§301).
Maximiza su ventana antes de abrir el panel y mide el reajuste al aparecer y al retirarlo.
Si una observación automática difiere del área útil, vuelve a maximizar para medir esa fase
y la anota en `remaximizedPhases`. Ventana y panel se cierran solos.
Los flags de área/maximizado pueden pasar para ese caso sin marcar r4Complete=true.

Tras actualizar kwin_area.py, el proceso antiguo del puente no carga Python de nuevo solo.
Para cargarlo y ensayar los dos sentidos en una misma ejecución local:

```bash
python3 /mnt/HDD1TB/Projects/hyprland-de/config/hypr/skins/plasma/scripts/r4-reservation-smoke.py \
  --run --maximize --refresh-area-watcher \
  --output "Micro-Star Int'l Co. Ltd. MAG 274Q X24 0x01010101"
```

El flag reinicia sólo kde-config-bridge por su ciclo existente y exige baseline nuevo con
PID/inicio/fecha privados. Si se piden varios bordes, se ejecuta antes del primero.
El puente queda activo
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

Si `head.json` o su generación están dañados, `--restore-profile` no puede abrir el perfil.
La recuperación explícita usa el ID de una copia guardada, sin necesitar el estado actual:

```bash
python3 src/bwm-plasma-host/preview-isolated.py \
  --binary build/bwm-plasma-host/bwm-plasma-host \
  --profile /ruta/al/perfil --recover-snapshot ID_DEL_SNAPSHOT
```

El ID corresponde al nombre de una carpeta `snapshots/<32 caracteres hexadecimales>`.
No se elige automáticamente una copia. El envoltorio ejecuta `--recover-profile
RUTA_DEL_SNAPSHOT` offscreen y termina; usa raíces auxiliares/D-Bus desechables y no registra
un preview. También admite perfiles en la autoridad XDG persistente descrita abajo.
Rechaza perfiles ocupados, alias, archivos/copias alterados y versiones futuras de head.
Verifica los cinco archivos completos y el layout con Corona, prepara otra generación y
archiva los bytes exactos de head (si existía) en `recoveries/<nueva-generación>/head.json`,
junto a `recovery.json` con el hash y la copia elegida. Conserva claves desconocidas del
head si sigue siendo un objeto legible. Las generaciones anteriores permanecen intactas.
Tras publicar ambos directorios completos, sustituye head atómicamente; una interrupción
anterior puede dejar directorios no seleccionados. El lease y la comprobación de bytes
detectan conflictos cooperantes; no son un CAS global ni garantía frente a corte de energía.
Los registros de recuperación quedan en ese perfil; la exportación copia el estado elegido
y los snapshots, no esos archivos de diagnóstico. Esta operación no activa el panel diario.
Evidencia: `docs/BREEZE_R4_PROFILE_RECOVERY_RESULTS.json`.

Reabrirlo sin recrear widgets ni sustituir el panel activo:

```bash
python3 src/bwm-plasma-host/preview-isolated.py \
  --binary /tmp/bwm-r4-panel-view-build/bwm-plasma-host \
  --profile "$XDG_CONFIG_HOME/bwm-native-profile" --follow-skin
```

Las salidas vienen del perfil; --output no las sobreescribe. El envoltorio busca paquetes
instalados en los paths XDG del llamador y conserva config auxiliar/caché/runtime/D-Bus
desechables. El binario --serve-profile mantiene el lease y trabaja sobre una copia privada de
los archivos completos. Al salir, tras guardar/sincronizar y destruir Corona, publica juntos
el layout, las preferencias y los bindings como generación nueva; después toma el checkpoint.
Una caída descarta esa edición y conserva la generación anterior. Detener con Ctrl+C o panel-session.py
stop. El envoltorio limpia su registro/control, y conserva el perfil seleccionado.

Al actualizar upstream revisar Corona.loadLayout/saveLayout/sync, jerarquía de preferencias,
IDs y ciclo de KSharedConfig. Repetir edición de widget/vista, dos instancias, skin, proceso
nuevo, desconocidos, perfil ocupado y restauración mientras un escritor antiguo retiene su
ruta. Esa restauración copia a otra ruta y no puede ser sobrescrita por el escritor viejo.
Evidencia: docs/BREEZE_R4_PROFILE_RESULTS.json. No es activación/rollback del panel diario;
su autoridad y aceptación Hyprland/escala siguen pendientes.

## Elegir un perfil persistente (§267)

Un perfil previamente exportado puede elegirse por su nombre en la autoridad XDG de estado.
La selección se guarda en `panel-profiles/.selection/selection.json`: sólo nombre, hash del
origen archivado y revisión, separados de los archivos/preferencias nativos KDE. No fija
una generación vieja: ediciones y recuperaciones del mismo perfil siguen siendo visibles.

```bash
python3 src/bwm-plasma-host/profile-selection.py --binary build/bwm-plasma-host/bwm-plasma-host status
python3 src/bwm-plasma-host/profile-selection.py --binary build/bwm-plasma-host/bwm-plasma-host select breeze-test --revision 0
```

Usar la revisión que devuelve status; 0 sólo corresponde a una selección que aún no se ha
guardado. Los cambios requieren que siga coincidiendo: otro escritor no se sobrescribe con
una elección basada en una revisión antigua. Repetir la misma selección es una operación
sin cambios. `clear --revision N` deja la selección vacía y conserva el contador, sin borrar
perfiles. También permite retirar la elección de un perfil roto o ausente; no repara una
selección JSON corrupta ni elige otro perfil automáticamente. Versiones/aliases/rutas/revisiones
inválidas se rechazan. Los campos desconocidos legibles se conservan.

El envoltorio de selección ejecuta los comandos nativos --profile-selection-info,
--select-profile NAME REVISION y --clear-profile-selection REVISION offscreen, con raíces
auxiliares/D-Bus desechables. La elección sólo admite nombres de perfiles persistentes; un
perfil temporal primero debe exportarse. status no crea el almacenamiento si no existe.
profileValidated informa una inspección puntual; false con profileError puede significar
que otro anfitrión lo tiene ocupado. No es un diagnóstico de vida ni aceptación de backends.

Para abrir explícitamente la elección en el preview registrado:

```bash
python3 src/bwm-plasma-host/preview-isolated.py \
  --binary build/bwm-plasma-host/bwm-plasma-host --selected-profile --follow-skin
```

El binario --serve-selected-profile resuelve la selección actual y adquiere el lease del
perfil bajo el mismo bloqueo de selección. Conserva ese lease durante Corona y el guardado/
checkpoint de salida. Cambiar o vaciar la elección rechaza perfiles usados por otro host;
no mata ni sustituye procesos. No pasa al servidor una ruta capturada por status: si ya no
hay una selección válida, falla. No se reinterpretan índices Qt/conectores como identidad.
Los ajustes nativos, bindings por descripción y restricciones del preview siguen vigentes.

Esto prepara la elección duradera, sin autostart ni retirada de la barra diaria. Los
indicadores activationAllowed/replacementReady siguen false. Autoridades de sesión,
fallback automático, servicios y aceptación del panel diario/logout siguen pendientes.
Evidencia: `docs/BREEZE_R4_PROFILE_SELECTION_RESULTS.json`.

Al cerrar sesión, apagar o reiniciar desde `bwm-power`, el control de la misma instancia
Hyprland pide retirar el preview y espera su salida. En un perfil guardado, el anfitrión
guarda los archivos nativos y crea el checkpoint antes de salir. El envoltorio confirma
el resultado después de recoger el proceso. Si no se confirma a tiempo o el guardado falla,
`bwm-power` registra el motivo y sigue con el cierre. Véase §268 en `BWM_CONTEXT.md`.

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

## Reproducir el commit de continuación (2026-11-14)

Sin fuentes externas ni red, la configuración normal con BUILD_TESTING activa registra
surface-geometry e isolated-local-configuration. La segunda instala los tres fixtures
propios, valida saveConfig/claves auxiliares, representación del panel original con el
fixture de sesión, configuración compartida y módulos QML, lectura en procesos nuevos y
retirada. Usa sólo XDG temporales, Qt offscreen y ningún bus de sesión. No sustituye el
ensayo externo/KNS ni certifica uso diario o compositor real.

```bash
cmake -S src/bwm-plasma-host -B /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host -DBUILD_TESTING=ON
cmake --build /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host -j4
ctest --test-dir /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host --output-on-failure
```

check-isolated.py con las fuentes seleccionadas sigue añadiendo la matriz completa de
terceros; no interpretar 2/2 de esta configuración local como esa matriz. Los tres archivos
tests/{callback-config,module-config,shared-config}/metadata.json son fuentes necesarias:
el commit e41c28d los omitió y quedaron sin seguimiento. Incluirlos al versionar los cambios
pendientes; no son archivos generados para descartar. Evidencia: docs/BREEZE_R4_REPRO_RESULTS.json.

## Diagnóstico de backends por instancia

PanelSession.widgetBackends y readiness/status del panel exponen las instancias directas
con id/paquete, fallos de carga y evaluación del catálogo (dependencias, extensiones
originales, estado y procedencia). Desconocidos permanecen sin evaluar; no se certifica un
servicio por metadatos ni por haber presentado el frame. widgetBackendsVerified permanece
false; un inventario vacío/ausente tampoco sirve como comprobación. replacementReady sigue
false. No existe aún controlador de selección/arranque/fallback diario. El inventario no
incluye recursivamente los hijos de bandeja; ver docs/BREEZE_R4_BACKEND_INVENTORY_RESULTS.json.

## Prueba explícita del escritorio común con el controlador KDE original

Hay un adaptador KWindowSystem estático sólo dentro del auxiliar, fijado a ABI privada
6.29.0 V5. No se instala globalmente ni en el compositor. La operación de escritorio usa
minimizar/restaurar de BWM, con estado compartido por instancias; no implementa el efecto
visual Peek ni la acción secundaria TaskManager. El widget completo permanece sin certificar.

--builtin permite alojar un widget compilado instalado sin copiar/reinstalar su paquete.
Ejemplo desde una terminal de Breeze, tras construir /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host:

```bash
python3 /mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/preview-isolated.py \
  --binary /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host/bwm-plasma-host --builtin org.kde.plasma.showdesktop \
  --native-panel --layer-panel --follow-skin --desktop-actions \
  --output "Micro-Star Int'l Co. Ltd. MAG 274Q X24 0x01010101"
```

Este opt-in permite a los botones minimizar/restaurar las ventanas reales de los workspaces
visibles mediante el gestor común. Ctrl+C retira la vista; el modo de escritorio es compartido
con el botón diario de BWM, que también permite restaurar. Los datos del widget permanecen
temporales. Sin --desktop-actions no se habilita el puente; tampoco en probes/export/KNS.
El usuario confirmó el ciclo de clics de escritorio en Hyprland (§214; evidencia manual en
BREEZE_R4_DESKTOP_SESSION_RESULTS.json). Geometría/foco y matriz completa siguen pendientes.
Las pruebas automatizadas usan IPC sustituido. No sustituye el panel diario.

Evidencia y límites en docs/BREEZE_R4_DESKTOP_ADAPTER_RESULTS.json. Para otro KWindowSystem,
revisar la ABI y delegación antes de cambiar CMake; las otras funciones siguen en KDE.

El binario compartido del ensayo se construye dentro de build/bwm-plasma-host (ignorado
por Git): no se depende de que /tmp del ejecutor sobreviva o esté disponible en la terminal
del usuario. El lanzador comprueba el ejecutable antes de acceder a la sesión y explica
cómo reconstruirlo si falta; no compila ni cambia de skin automáticamente.

## Fuente experimental de ventanas nativas (§215)

El build enlaza ahora LibTaskManager 6.7.5 EXACT (plasma-workspace) y KF6 Service.
--task-actions permite investigar el modelo original de tareas en un preview explícito
--follow-skin con Breeze y Wayland/IPC. No es aún una barra de tareas operativa completa:
faltan VirtualDesktopInfo, acciones/menús, coordinación entre gestores y aceptación Wayland.
No usarlo para seleccionar el panel diario. El helper native-tasks.py deriva sólo foco,
minimizar/restaurar, maximizar y cerrar al gestor BWM existente, con identidad guardada.
Una fuente TaskManager personalizada por un widget queda intacta.

CTest local incluye test-tasks: dos TasksModel KDE auténticos, datos/índices y acciones con
helper/gestor reales e IPC ficticio; no prueba el pintado del QML en Wayland. El fixture
StartupTasksModel offscreen tiene una tabla vacía de una columna sólo en test. No hay nuevos
servidores ni parches de KDE. El diagnóstico taskSource conserva operationalVerified=false;
replacementReady sigue false. Límites, tabla de efectos y evidencia en
[los resultados R4](../../docs/BREEZE_R4_RESULTS.md) y
[BREEZE_R4_TASK_SOURCE_RESULTS.json](../../docs/BREEZE_R4_TASK_SOURCE_RESULTS.json).

## Transacciones de los adaptadores nativos (§216)

Los dos opt-in experimentales pasan ahora por --native-serialized del gestor común:
flock privado por runtime con espera máxima 1 s y nueva comprobación de Breeze dentro.
Las tareas pasan además el inicio Linux esperado, revalidado después de esperar.
El archivo de bloqueo nunca se elimina para desbloquearlo; se libera al cerrar el descriptor.
Las entradas diarias que no usan ese flag aún no participan en la exclusión.

Al salir de Breeze o parar mediante el canal de control, se suspenden las entradas, se
vacía la cola y se espera la operación en curso antes de confirmar. Se cancela únicamente
el snapshot de lectura. Si la confirmación tarda más que el publicador, el cambio de skin
falla antes de cambiar perfiles y se reanuda la skin anterior. No se garantiza rollback
ante terminación forzada/timeout. quiescent sólo describe los procesos/cola de este puente.

CTest incluye los casos de retirada con tareas y Mostrar escritorio, con helpers ficticios
que permiten comprobar el instante de finalización/ack y la reanudación. Las pruebas Python
cubren contención real, guardas posteriores a la espera y permisos/enlaces/muerte del dueño.
No sustituyen aceptación visual Wayland. Ver BREEZE_R4_NATIVE_TRANSACTIONS_RESULTS.json.

## Proveedor de escritorios por Wayland (§218)

BUILD_TESTING añade desktop-workspace-projection y native-desktop-protocol. Este último
inicia dos hijos con socketpair privado: fixture Wayland data-only y test del proveedor
VirtualDesktopInfo original, C++/QML, filtros/orden de TaskManager y roles de un delegado
de prueba. No dibuja superficies ni se conecta al compositor del usuario; no usa el
workaround StartupTasksModel offscreen. El XML KDE privado está fijado por hash y requiere
plasma-wayland-protocols y wayland-protocols además de wayland-server/client.

La extensión opcional de Hyprland vive en ../bwm-plasma-desktops, se compila aparte y está
desactivada por defecto. No se ha instalado/cargado ni cambiado el arranque. El éxito del
fixture no valida sus activaciones en Hyprland, coordinación o menús. Ver su README y
BREEZE_R4_NATIVE_DESKTOPS_RESULTS.json. El panel diario y flags de certificación siguen igual.

## Retirada del proveedor nativo (§219)

--native-desktops añade una barrera asíncrona de activación por conexión a un preview
--follow-skin. Requiere el proveedor experimental ya cargado, habilitado y compatible;
el launcher sólo consulta su diagnóstico, sin carga automática o cambio de configuración.
El cliente comprueba también el protocolo real por Wayland. Probes/KNS/export limpian la
variable del opt-in. No usar esta opción como certificado del widget o del panel diario.

NativeDesktopControl exige ack con serial vigente (timeout 1 s). RuntimeControl espera
esa confirmación y los gestores locales antes de confirmar retirada; las vistas se retiran
si el proveedor desaparece o deja de estar disponible. Su pérdida permite retirar/salir,
pero bloquea la entrada al modo requerido. Una nueva disponibilidad exige confirmación.
Los otros clientes conservan su autoridad; el propietario que se destruye deja pausada
su propia conexión. Las conexiones sin control sólo pueden leer el protocolo experimental.

CTest añade native-desktop-control-wire (dos conexiones) y amplía native-desktop-protocol
con RuntimeControl/PanelRuntime, pérdida/reconexión y ack tardío tras timeout. La cola usada
es el núcleo real del proveedor, no un duplicado Python. Se conserva fixture sin superficies
ni sesión del usuario. Evidencia y límites: BREEZE_R4_DESKTOP_CONTROL_RESULTS.json.

## Menú TaskManager original y capacidades (§220)

--task-actions integra TaskMenuPolicy en el puente experimental: conserva ContextMenu.qml
instalado y bloquea mantener encima/debajo y excluir captura, cuyas peticiones todavía no se
implementan. La máscara usa QActionGroup público y conserva enabled/checked nativos. Sólo
actúa sobre raíces registradas e índices BWM; acciones de apps y menús ajenos siguen intactos.
Los grupos validan todos sus miembros y retirar filas o suspender cierra sus menús.

El contenido original se fija por SHA256 en CMake. Si cambia/no puede leerse, el menú afectado
se deshabilita y taskSource.menuPolicy.lastError lo explica. No cambiar el hash sin revisar
handlers/roles/propietarios originales y repetir los tests normal/ASan. La retirada de una
máscara debe activar su grupo individual antes de removeAction, para recalcular enabled sin
perder el último estado explícito. No sobrescribir bindings QML ni copiar el menú al repo.

CTest local ejecuta test-taskmenu con el widget/menú originales instalados. Prueba minimizar
individual/grupo y las restricciones; Task.qml presenta roles undefined en offscreen por
backend nativo ausente. No certifica pintado, foco/teclado/posición Wayland ni widget completo.
El test de roles sobre Wayland aislado usa otro delegado, no Task.qml. Ver
BREEZE_R4_TASK_MENU_RESULTS.json. Sin nuevas dependencias, operaciones ni activación diaria.

## Pantalla completa nativa (§221)

--task-actions conecta el control original de fullscreen con kwin-window. El snapshot opcional
fullscreenable habilita IsFullScreenable sólo para ventanas normales mapeadas, no ocultas,
no fijadas/no minimizadas. Falta el campo → acción deshabilitada; no se parchea KDE. El handler
emite estado deseado, el gestor usa set/unset y verifica el recibo más el modo interno leído.
Dos peticiones del mismo snapshot no revierten la primera. Siguen las guardas PID/inicio,
bloqueo y retirada del puente. No ofrece fullscreen sobre Magic/almacenamiento de minimizadas.

CTest prueba menú individual/grupo y helper/gestor real con IPC y hl simulados: no certifica
frames, geometría, foco o Wayland real. BUILD_TESTING requiere lua5.4/lua para ejecutar el Lua
generado en ese fixture; CMake resuelve su ruta y check-local acepta --lua. Sin BUILD_TESTING
no se necesita el intérprete. Evidencia BREEZE_R4_FULLSCREEN_RESULTS.json. daily fullscreen
sin --state conserva toggle; las tres acciones no admitidas del menú siguen bloqueadas.
No activa el panel diario ni certifica TaskManager completo.

## Actualización de fichas de aplicaciones (§222)

La fuente experimental escucha la base KDE KSycoca: actualizar/quitar/reinstalar un .desktop
invalida el nombre/icono/lanzador sin recrear ventanas. Refresco agrupado de 100 ms y resolución
diferida con TaskTools; no hay watcher por ventana ni reset de UUID. KF6 Service ya requerido.

BUILD_TESTING requiere además kbuildsycoca6 del conjunto KF6 Service. Test-taskmetadata usa
una base KDE real con entradas/PNG propios, siempre en XDG temporales y sin KDESYCOCA heredado.
No ejecutar esa prueba apuntándola al cache del usuario; check-local.py proporciona su entorno
y guarda nativeTaskMetadataOutput. No ejecuta el Exec de las entradas. Evidencia y límites en
BREEZE_R4_TASK_METADATA_RESULTS.json. No acredita render, temas de iconos completos, catálogo
KPackage ni sustitución del panel diario.

## Registro del proveedor y control v2 (§223)

--native-desktops requiere ahora barrierProtocolVersion=2 y el evento desktop_global.
El auxiliar inspecciona su conexión Wayland existente, exige un único management KDE/control
BWM y comprueba la asociación antes de resume. Mantiene su proxy por ID, sin el enlace
automático de QWaylandClientExtension. Conflictos permiten retirar/salir; el diagnóstico
nativeDesktopControl incluye registry/bindingVerified/restartRequired.

Si se duplica el management KDE, reiniciar sólo el auxiliar es necesario antes de volver a
mostrar la vista: el consumidor original puede perder su lista aunque se quite el duplicado.
No parchear su backend privado ni reiniciar Hyprland para resolver ese estado del auxiliar.
El test prueba un proceso Qt nuevo con el segundo endpoint del fixture de datos; no abre
otra sesión/compositor ni dibuja superficies. La interfaz conserva el nombre _v1 y ofrece
versión 2; clientes v1 siguen en el test de barrera, pero no sirven para el host nuevo.

Dependencia cliente Wayland explícita, server >=1.22 para el componente opcional; paquetes
ya declarados. No instalar/cargar ese componente por pasar las pruebas: arbitraje de servidor,
frontend/arranque y aceptación real permanecen pendientes. BREEZE_R4_REGISTRY_RESULTS.json.


R4 §225: --native-desktops exige además serverArbitrationVersion=1, arbitrationState=active
y providerRestartRequired=false en el diagnóstico de sólo lectura. No activa/instala/carga
el módulo. El proveedor opcional inventaría/elige antes de publicar y conserva una única
generación al retirarla; ámbito visible y futuro inicio de sesión para recuperación, nunca
hot unload. CTest añade 14 escenarios del servidor y prueba original KDE C++/QML sobre el
fixture arbitrado. Detalle/límites: ../bwm-plasma-desktops/README.md y BREEZE_R4_RESULTS.md §225.
Aceptación del frontend/arranque real y panel diario siguen pendientes.


R4 §226: inicialización del proveedor diferida al loop tras opt-in y cierre definitivo
sin recursos/callbacks en una biblioteca descargada. CTest conserva 7 suites y añade dentro
del test del proveedor un arranque lento y DSO real descargado antes de destruir clientes,
activo/retirado. 16 escenarios; no prueba frontend/arranque/logout real ni autoriza hot unload.
Ver BREEZE_R4_STARTUP_TEARDOWN_RESULTS.json y README del proveedor. Sin activación diaria.

El preflight de --native-desktops exige providerLifecycleVersion=1 (entero, no booleano)
y observerStartup=deferred-event-loop, además de las guardas anteriores. Diagnósticos de
un módulo antiguo se rechazan antes de lanzar el auxiliar; sin instalar/cargar/habilitar.


R4 §227: preflight --native-desktops sigue sólo lectura y exige countMirrorVersion=1 con
contador común confirmado. El puente KDE existente resuelve las opciones comunes/usuario
y envía snapshot en memoria al módulo; no lee config.json en el frontend ni crea otra
preferencia. CTest combina emisor Python/recibo C++ y originales KDE; puente real se prueba
en XDG temporal. Ver BREEZE_R4_COUNT_MIRROR_RESULTS.json; aceptación de sesión sigue pendiente.


R4 §228: el shell principal coordina la entrega común del contador entre skins mediante
hooks.sharedSettings y native_workspaces.py shared. El puente KDE no se mantiene fuera de
Breeze. IPC sharedSettings status sólo diagnostica coordinación. QML/procesos probados sin
compositor, con recibos C++ de ensayo; sesión real no verificada (IPC inaccesible). Ver
BREEZE_R4_SHARED_DELIVERY_RESULTS.json. Fuente shell integrada/autorecarga posible; sin panel nativo.


R4 §229: test-taskdelegate/native-task-delegate-render prepara los dos widgets de tareas
KDE originales sobre Wayland privado + QQuickRenderControl/QImage sin superficie. No usar
proxies de roles offscreen como prueba nativa: TasksModel consulta WindowTasksModel estático.
Compila normal/ASan; ejecución nueva bloqueada ANTES de Qt por wl_client_create EPERM,
reproducido en suite anterior. Sólo3 suites sin esos clientes pasan normal/ASan; no afirmar
render validado ni CTest completo. Ver BREEZE_R4_TASK_DELEGATE_RESULTS.json y comando local en
BREEZE_R4_RESULTS.md §229. Sin producción/plugin/panel diario/reinicio/R5/R7.


§230 corrige la guarda del socket del test-taskdelegate: libwayland consume WAYLAND_SOCKET
al iniciar Qt. QTest initMain captura su identidad antes de QApplication; initTestCase
compara con el fd del wl_display activo por API Qt nativa. Compilado normal/ASan; el primer
ensayo local sólo probó arranque, falta repetir el CTest corregido para roles/render.


§231: la guarda de fuente de test-taskdelegate usa recurso resuelto + SHA256 original;
QQmlContext.baseUrl no identifica el archivo del objeto. Guarda compartida y aprobada con
el delegado original en test-taskmenu normal/ASan. Smoke de render Qt en memoria aprobado;
render Task.qml/ensayo Wayland completo sigue pendiente. Ver resultados §231.


§232: el test nativo usa su propia aplicación .desktop/PNG en XDG temporal y base KService
reconstruida; no depende de que Konsole esté registrado ni confunde su PID con otra app.
La preparación compartida pasa ID/nombre/icono en test-taskmetadata normal/ASan. AppId del
modelo conserva .desktop; Task.qml original lo elimina. Ensayo de dibujo completo pendiente.


§233: usuario supera native-task-delegate-render (CTest1/1, QtTest4/4). Ambos widgets
originales KDE, roles/metadatos/estados/título/índices/retirada y dibujo QImage comprobados
sobre conexión Wayland privada, ventana oculta/sin handle. Sustituye los pendientes de
§§229–232; no repetir sin motivo. Sólo native normal; ASan nativo no ejecutado. No acredita
superficies/entrada ni backends de sesión/panel diario. Evidencia currentValidation en
BREEZE_R4_TASK_DELEGATE_RESULTS.json. R4 sigue abierta por integración/aceptación diarias.


§234: grupos sin LastActivated reciben StackingOrder desde orden de clients de Hyprland0.56.2
(inferior→superior), sin usar focusHistoryID. Fuente conserva filas/UUID y notifica ese rol;
legado sin campo usa orden de snapshot, sin certificarlo físico. TaskTools.js original/pin
prueba selección superior, actualización y prioridad MRU. Helper Python10 y CTest3/3 normal/
ASan aprobados. Diagnósticos del catálogo corregidos; sin certificar frontend/panel de sesión.
Render nativo no repetido tras el cambio. Ver BREEZE_R4_GROUP_ORDER_RESULTS.json.


§235: usuario comunica clics que lanzan apps en vez de activar ventanas. Reproducido al
registrar sólo PanelSession: los applets son hijos visuales, fuera del árbol QObject del
containment. BwmTaskBridge recorre ambos árboles, sin reparentar/forzar creación. Test nuevo
por ruta real prueba lanzador+ventana fusionados/HasLauncher/focus (IPC ficticio); CTest3/3
normal/ASan y Python7 pasan. --task-actions espera fuente/snapshot y muestra conteos antes
del registro. No prueba entrada/aspecto en sesión: repetir mismo preview e iconos pendientes.
Evidencia BREEZE_R4_PANEL_TASK_REGISTRATION_RESULTS.json; sin takeover/plugin/reinicio diario.

§236: la repetición física sigue fallando tras §235: lanza instancias y no restaura;
animación de minimizado hacia otro monitor. Segunda causa reproducida: el filtro nativo
showOnlyCurrentDesktop=true rechaza ventanas sin VirtualDesktopInfo cuando ScreenGeometry
coincide con QScreen. El test anterior desactivaba el filtro directamente y no lo detectó.
El preview de tareas exige ahora --all-desktops explícito o --native-desktops con proveedor
ya cargado. El primero sólo guarda showOnlyCurrentDesktop=false por KConfigLoader en las
dos instancias temporales antes de crear el panel; se rechaza con --profile y fuera de XDG
temporal. No sustituye el backend. Diagnóstico v1 informa filas visibles/lanzadores/vistas y
rechaza inicio con filtro activo sin control nativo confirmado. Las cantidades suman vistas.
Test-paneltasks usa configuración original, geometría coincidente y dos applets por
PanelSession; prueba fusión/HasLauncher/focus y restauración desde almacén de otro monitor,
sin setters del modelo. Normal3/3 QtTest y local-config ASan1/1 tras ampliar restauración;
regresión seleccionada3/3 normal/ASan; Python10+10+7. Offscreen conserva avisos de roles y
no acredita pintado/input. Regla común no_anim al coincidir special:minimized, comprobada
con parser Lua/Hyprland aislado, suprime el traslado animado al almacén compartido; no es
el efecto KWin hacia el icono. Sin reload realizado ni aceptación visual/foco en sesión.
Comando anterior requiere añadir --all-desktops y cargar la regla con hyprctl reload.
Inicio nuevo: «Tareas R4 conectadas: N ventanas; filas visibles: V; lanzadores: L.»
Ver BREEZE_R4_DESKTOP_FILTER_RESULTS.json; R4 abierta y panel diario conservado.

§237 (2026-11-16): el usuario responde «ahora si» tras el ensayo de §236. Aceptación
funcional general del preview solicitado (activar/recuperar), comunicada por el usuario;
no medición directa ni desglose de apps/casos. No confirma individualmente animación,
iconos, limpieza o ejecución de reload. El fallo funcional de §§235–236 queda superado
para este preview con --all-desktops. Proveedor nativo/filtros e integración diaria de R4
siguen pendientes; operationalVerified/replacementReady/r4Complete false. Sin nuevo código
ni repetición de pruebas. Evidencia userFollowUp237 en BREEZE_R4_DESKTOP_FILTER_RESULTS.json.

§238 (2026-11-16): --session-appearance añade al preview desechable un snapshot inicial
nativo de iconos, colores/fuentes y tema SVG de Plasma. Rechazado con --profile. El wrapper
llama --stage-preview-appearance CONFIG_ROOT antes del proceso gráfico: QCoreApplication,
KConfig NoGlobals con ruta absoluta y defaults XDG/kdedefaults explícitos; lista limitada de
claves/grupos de apariencia, sin archivos completos o enlaces. No escribe en el origen ni
copia claves ajenas. Respeta los valores efectivos inmutables/borrados, sin afirmar migrar
restricciones al snapshot. SimpleConfig ignora addConfigSources en6.29; sólo para destino.
El gráfico usa QT_QPA_PLATFORMTHEME=kde y assets XDG originales (también con --package),
sin QIcon::setThemeName, conexión al D-Bus de sesión o layouts ejecutados. Snapshot de inicio,
no seguimiento vivo. No copia ajustes propios de QStyle/Kvantum ni configuración de apps.
La prueba isolated-preview-appearance usa motores originales QApplication/Plasma::Theme:
icono propio por tema XDG y píxel #39b574, paleta #112233, fuente15, SVG breeze-dark. Comprueba
precedencia/defaults/borrados/inmutabilidad efectiva, origen/sistema intactos, exclusión de
claves ajenas, independencia del snapshot y rechazo de sobrescritura/alias. CTest4/4 normal/
ASan seleccionados, Python wrapper11, py_compile OK. Sin prueba visual nueva de sesión ni
render Wayland repetido. Paquetes necesarios ya declarados. Ver BREEZE_R4_APPEARANCE_RESULTS.json.
Para ensayo visual, añadir --session-appearance al comando §236; R4 sigue abierta.

§239 (2026-11-16): usuario acepta aspecto/acciones de §238;7 ventanas de fuente,
12 filas ventana/grupo y6 lanzadores en dos vistas. Sólo falla miniatura hover; falta
org.kde.pipewire. PipeWireThumbnail/ScreencastingRequest original necesita además el
protocolo KDE zkde_screencast_unstable_v1; instalar el módulo por sí solo no resuelve esto.
--task-thumbnails prepara captura nativa de Hyprland sólo para preview desechable con tareas.
Interceptor público del QQmlEngine compartido cambia únicamente la URL qrc original de
PipeWireThumbnail.qml con SHA256 revisado; TaskThumbnail.qml LGPL conserva hasThumbnail/winId.
ToolTipDelegate/Instance, aspecto e interacción siguen originales. QQuickPaintedItem propio
consume ext-foreign-toplevel-list, mapping Hyprland64bits, ext-image-capture-source y
ext-image-copy-capture, en la conexión Qt existente. Sin KWin/PipeWire, copia/patch de KDE
instalado, tipos privados reemplazados o plugin de compositor. Fuente desconocida bloqueada.
Sólo captura ventanas: handle estable ligado antes de snapshot nuevo, UUID/identidad vigentes,
rechazo de minimizadas; cierre/ocultación/retirada/skin invalidan y liberan. memfd CLOEXEC,
8/10bits32bpp,8192 máx.,64MiB por buffer/128MiB total,8 sesiones,512px y4fps máx. Copia
independiente de mmap. Primer frame con timeout; posteriores esperan daño en ventanas
estáticas. Constraints nuevas reemplazan buffer; formatos no soportados fallan a icono.
Nunca salida/recorte, portales o imágenes en disco. Colorimetría HDR exacta no certificada.
Startup exige protocolos si flag activo, no declara primeros frames vistos. Diagnóstico
sólo agregado. Globals retirados/ambiguos bloquean hasta auxiliar nuevo. No daemon ni reload.
Local prueba píxeles/formato/transforms/límites/identidad y endpoint QML/cast en motor real
compartido con applet. CTest5/5 normal/ASan, Python13+10+7; no captura nativa aprobada.
Fixture sintético nuevo (sin superficies) prueba frame azul, estático, resize, pausa,
identidad, cierre y retirada; compila pero wl_client_create EPERM impide correrlo aquí.
Ejecutar native-task-thumbnail desde terminal antes del preview. Dependencias build
wayland-protocols/wayland-scanner explícitas, XML WLR original y licencias preservados.
Ver BREEZE_R4_THUMBNAIL_RESULTS.json. Sin integración diaria, R5/R7 o cierre de R4.

La continuación de §239 mantiene el veto del incidente BREEZE_RECOVERY: los protocolos
nuevos usan el mismo ScreenshareSession. Backend real bloqueado hasta que el peer Wayland
activo tenga BWM_SCREENSHARE_MONITOR_GUARD_V1 (SO_PEERCRED y /proc/PID/exe, no versión
instalada o archivo de configuración). Parche0.56.2 prepara monitor válido/referencia fuerte
en init y monitorChanged, sin cambiar ABI. Los cuerpos originales reproducen SIGSEGV con
monitor nulo y los siete casos corregidos pasan normal/ASan; no se compiló el compositor
completo ni se reprodujo el incidente real. CTest final6/6 local normal/ASan. Guía
BREEZE_R4_THUMBNAILS.md con prueba privada, parche Portage/emerge por el usuario y adopción
al próximo inicio de sesión. NO ejecutar el preview con capturas en el compositor antiguo;
no desactivar la guarda ni las contenciones diarias. Captura nativa pendiente por EPERM,
parche sin instalar y panel diario intacto.

§240 (2026-11-16): el CTest nativo del usuario falla con cliente SIGSEGV/acceso0x10,
fixture0. Repro mínimo local sin Wayland: destruir TaskThumbnail asociado a QQuickWindow.
ASan confirma callback windowChanged desde QQuickItem::~QQuickItem tras liberar State;
QObject todavía no ha desconectado. Destructor explícito desconecta conexiones propias
antes de liberar estado/captura; conserva destroyed y observadores ajenos. Se registra
window() inicial para padres C++ que ya emitieron la señal antes de conectar el callback.
Reparentado/desasociación, destrucción explícita y por ventana padre + destroyed/QPointer:
QtTest9/9 incluyendo init/cleanup, CTest seleccionado6/6 normal/ASan. Binarios recompilados.
El test nativo añade destrucción/recreación activa y checkpoints de etapa. Sigue EPERM aquí
al crear cliente privado; repetir native-task-thumbnail desde terminal. No se aceptan aún
píxeles/teardown nativos. Parche del compositor sin instalar y veto de sesión intacto.
No cambia backend, dependencias, panel diario o guardas; sin sudo/reinicio/commit/R5/R7.
Evidencia followUp240 en BREEZE_R4_THUMBNAIL_RESULTS.json.

§241 (2026-11-16): usuario aprueba native-task-thumbnail, CTest1/1 en4.30s. Informe leído:
cliente0/fixture0, QtTest3/3 incluyendo init/cleanup,4.116s, syntheticWindowCaptureVerified y
cleanupVerified true. Cinco checkpoints de píxeles sintéticos en QImage, estático/ocultación/
resize, destrucción/recreación con captura activa, identidad/cierre/retirada y teardown.
Supera el fallo §240 para ese ensayo normal privado; no native ASan o miniatura real de sesión.
No repetir ni recompilar sin cambio. Siguiente: user patch de Portage0.56.2 y emerge exacto
hyproverlay desde fuente (--usepkg=n --getbinpkg=n), por usuario, y próximo inicio de sesión.
Parche no instalado, capturas de sesión aún bloqueadas; panel diario intacto. Ver
BREEZE_R4_THUMBNAILS.md y userFollowUp241 de BREEZE_R4_THUMBNAIL_RESULTS.json. R4 abierta.

§242 (2026-11-16): usuario responde «listo» al paso de instalación/reentrada. Se verifican
patch /etc/portage idéntico al revisado y marca BWM_SCREENSHARE_MONITOR_GUARD_V1 en el
Hyprland instalado. El ejecutor no accede al IPC ni verifica proceso/peer activo; el auxiliar
exige esa validación automáticamente antes de capturar. No se infiere reinicio individual
por la respuesta ni se declara prueba visual. Config actual plasma; ejecutar preview con
--task-thumbnails --all-desktops --session-appearance y comprobar hover sobre no minimizada.
No repetir CTest aprobado. Sin código/build/tests/sudo/sesión cambiados desde el asistente.
Evidencia userFollowUp242; R4/panel diario/aceptación de captura real pendientes.

§243 (2026-11-16): preview del usuario bloquea en guarda y luego ENOENT de ack.json.
El antiguo bool no distinguía credenciales/permisos/lectura de una marca ausente. Marca en
archivo instalado y cap_sys_nice=ep de Gentoo verificados; causa del peer aún desconocida,
no asumir sesión antigua ni repetir emerge/relogin. Estado de guarda ahora tiene motivos
separados, peer PID/nombre/error/bytes, y mantiene el mismo requisito de marca real.
--check-thumbnail-compositor / runner check-thumbnail-compositor.py diagnostican usando
Qt Wayland, XDG/D-Bus privados, sin panel/capturas o cambios de permisos/capacidades.
wait_initial_ack detecta salida temprana/timeout antes de register y evita ENOENT secundario.
Regresión6/6 normal/ASan, wrapper16 y QtTest10/10 contando init/cleanup; binarios recompilados.
No repetir native§241 ni afirmar validación de guarda/hover en sesión. Pedir salida del runner;
userFollowUp243 conserva intento/hipótesis/límites. R4 abierta y panel diario intacto.

§244 (2026-11-16): el diagnóstico del usuario confirma Permission denied al leer el
executable de Hyprland PID5178/UID1000. La comprobación anterior por /proc no contemplaba esta
configuración Gentoo/filecaps; no prueba ausencia de guardas. Parche ampliado publica
bwmScreenshareMonitorGuard {version:1,pid:getpid()} en el JSON original de hyprctl -j version.
Getter junto a guardas reales, cabecera interna nueva; sin E/S/espera en compositor ni cambio
de estructuras/ABI. Auxiliar conserva prueba ELF y acepta informe fresco sólo con PID exacto
de SO_PEERCRED y UID propio. Runtime real para IPC desde XDG temporal; límite2s/64KiB,
rechazo de otra instancia/tipos inválidos/campo ausente/error/timeout. Sin override ni
cambios de permisos/capacidades. Diagnóstico conserva causa de /proc separada de la de IPC.
Aplicación del parche completo a dos originales0.56.2 + cabecera comprobada con git apply;
cuerpos originales/corregidos de guardas y getVersion compilados, JSON/PID real validados.
Build auxiliar normal/ASan, CTest seleccionado6/6 en ambos, wrapper16 y QtTest12/12 contando
init/cleanup pasan. No build completo de Hyprland ni prueba IPC/captura de sesión aquí;
ensayo nativo§241 no repetido. Guardas anteriores instaladas, parche instalado comparado:
carece del informe IPC. Extensión aún SIN instalar/adoptar: usuario debe reemplazar user
patch, recompilar desde fuente y entrar de nuevo; después ejecutar diagnóstico sin capturas.
Ver BREEZE_R4_THUMBNAILS.md y userFollowUp244. Panel diario intacto; R4 sigue abierta.

§245 (2026-11-16): usuario ejecuta diagnóstico corregido: clientExit0, verified=true,
verificationMethod=compositor-ipc, guarda version1 y PID496181 coincidente con SO_PEERCRED,
Hyprland/UID1000. /proc sigue denegado; alternativa IPC funciona manteniendo el requisito de
PID/UID. Runner sin cambios de sesión ni capturas (sessionModified/capturesStarted false).
Parche de Portage ampliado ahora idéntico al del repo (SHA256239aa61b67ca0f9d1ab536814027f3d18bbc74cb9f3aa008554e60b80ee9ff8c).
Informe activo comprobado por salida de terminal, sin inferir detalles del rebuild/relogin.
Siguiente: preview con --task-thumbnails --all-desktops --session-appearance y hover sobre
tarea no minimizada, comprobar imagen/actualización y cierre del tooltip/acciones. No repetir
CTest nativo aprobado ni pedir recompilar/reentrar otra vez. Miniatura física aún pendiente;
sin cambios de código/build/tests/sudo/sesión por el asistente. Panel diario intacto, R4 abierta.
Evidencia userFollowUp245 en BREEZE_R4_THUMBNAIL_RESULTS.json.

§246 (2026-11-16): usuario ve preview centrada/duplicada y listada como ventana en la
barra; deja auxiliar abierto. Ensayo visual NO aceptado. Lectura del último ack existente
confirma panel visible/protocolos preparados y dos applets taskmanager; no es un muestreo
actual de fotogramas. hyprctl directo sigue inaccesible aquí (Couldn't set socket timeout(2));
sin captura ni control visual de la superficie del usuario.
Causa de adaptación reproducida con tooltip original: ToolTipDialog6.7.5 se crea desde C++,
sin contexto QML propio, deriva PopupPlasmaWindow y no Dialog. PackageWindows sólo reconocía
Dialog/contexto plasmoid. Ahora resuelve propiedad visualParent por árbol visual de applet,
configura overlay/posición al SurfaceCreated antes de la selección de rol Wayland y sigue
visualParentChanged al reutilizar el tooltip. API pública LayerShellQt/PlasmaQuick; sin
parchear tooltip/QML KDE ni filtrar PID propio para ocultar el fallo. NonInteractive retiene
entrada de puntero, keyboardNone/activateOnShow=false; sin reserva de área. Una sola instancia
de PopupAnchor por ventana; conexiones de vida acotadas. Suspender sólo el dueño vigente.
Tooltip compartido que pasa a ventana normal recupera backend original tras hide/destroy;
al volver al panel se recrea su rol, nunca se cambia rol sobre superficie mapeada. Ventanas
ajenas quedan intactas. Diagnóstico packageWindows añade tipo/rol/geometría, sin contenido.
Preview desechable --task-actions --native-panel usa una instancia por defecto. --instances
1|2 permite comparación explícita sólo con --follow-skin y sin --profile; perfiles guardados
no cambian y probes/otros modos conservan las dos instancias. Env heredado se descarta.
Build normal/ASan; CTest seleccionado4/4 ambos (thumbnail, appearance, surfaces, local config),
QtTest13/13 contando init/cleanup y wrapper18 pasan. Prueba usa Core.ToolTipArea original:
creación perezosa C++, rol al crear superficie, posición/tamaño, cambio de applet/containment,
reutilización, ocultación, salida a ventana normal y vuelta; sin duplicar adaptador ni pedir
foco. Offscreen verifica política/orden de eventos, NO rol real del compositor o lista de
ventanas de sesión. Fuentes locales Qt6.11.2/LayerShellQt6.7.5 revisadas para ese límite.
Aviso LayerShellQt de ventana visible en SurfaceCreated se basa en flag Qt, que cambia antes
de crear su shell surface; se conserva en informes, no se usa como prueba de rol nativo.
Auxiliar abierto sigue con código anterior; siguiente Ctrl+C y mismo comando con --instances1,
comprobar hover anclado, sin ventana nueva en tareas, una sola vista y acciones/cierre.
Sin recompilar Hyprland/relogin, repetir ensayo nativo§241, nuevo requisito o tocar panel diario.
Evidencia userFollowUp246; captura/colocación física tras corrección pendientes y R4 abierta.

§247 (2026-11-16): usuario confirma «perfecto ya tiene miniaturas» tras §246 y pide continuar,
dejando el auxiliar abierto. Aceptación visual general del hover nativo registrada; no se
infiere medición individual de actualización/foco/geometría ni matriz completa de monitores.
No repetir el CTest nativo§241 ni el diagnóstico de guarda ya aprobados. El asistente no
cierra ni reinicia el auxiliar abierto. R4 sigue abierta por capacidades/aceptación restantes;
panel diario intacto. Evidencia userFollowUp247 en BREEZE_R4_THUMBNAIL_RESULTS.json.

§248 (2026-11-16): continúa R4 por Nueva ventana/abrir URL de una tarea con ventana. La
fuente BwmTaskSource antes heredaba los dos métodos vacíos de AbstractTasksModel. Añadidos
requestNewInstance/requestOpenUrls, índices/identidad vigentes y URL acotadas; TasksModel
original reenvía ambos. CanLaunchNewInstance se invalida con metadatos KSycoca. La política
del menú sigue datos .desktop originales (NoDisplay, SingleMainWindow, X-GNOME-SingleWindow,
acciones New Window). No confundir visibilidad del menú con permiso de ejecutar una petición
explícita: WaylandTasksModel original también permite clic central/modificadores aunque la
entrada genérica esté oculta. Helper canLauchNewInstance no está exportado; adaptación mínima
por KService público con licencia/créditos LGPL2.1 conservados, sin duplicar símbolos KDE.
Acciones pasan por cola/quiescencia del puente y bloqueo nativo común. native-tasks revalida
skin y dirección/PID/inicio dentro del bloqueo, resuelve appId de clients actual, y reejecuta
sólo el host conocido con --launch-task-application. Éste usa AppData/KService nativos y
KIO::ApplicationLauncherJob, sin interpretar Exec, comandos de PID o URL lanzadora arbitraria.
Se exige aplicación registrada; fallback a ejecutable sin .desktop no se ejecuta. Aceptación
del job confirma traspaso de arranque, nunca app lista/ventana/foco verificados.
El wrapper conserva sólo claves permitidas del entorno original en contexto de proceso;
auxiliar de lanzamiento restaura XDG/D-Bus/Qt/Wayland para que la app no use almacenes del
preview. Contexto ausente/malformado falla. No se restauran flags BWM_R4, BWM_SKIN_SWITCH ni
WAYLAND_SOCKET consumido. Host de lanzamiento sin panel/capturas, entrada/tiempo acotados y
sesión de proceso aparte: timeout/retirada no terminan apps lanzadas. Recibo por descriptor
CLOEXEC separado; stdout/stderr de apps no contaminan JSON ni retienen el canal abierto.
Prueba real de job KDE sólo con aplicación Python propia en XDG/D-Bus privados: args/espacios/
Unicode/metacaracteres y URL nativa, entorno, proceso que sigue vivo tras recibo, identidad
antigua, URL vacías y servicio retirado. Prueba C++ por TasksModel original verifica peticiones,
capacidad de menú y refresco KSycoca conservando índices. Política de visibilidad no bloquea
petición explícita; no promete que una app de ventana única abra otra ventana.
KIOGui declarado en CMake/requisito de build (Gentoo kio/Arch kio), tabla regenerada; skin ya
recomienda ese requisito experimental. Código/diagnósticos no certifican rutas restantes:
lanzadores puros/acciones específicas de aplicaciones mantienen su camino nativo anterior y
su entorno aún requiere revisión; activación/foco de apps nuevas y sesión real pendientes.
Sin nueva dependencia de captura, plugin, cambio de skin o panel diario. Auxiliar abierto
sigue con binario anterior; para probar el nuevo hay que cerrar sólo éste y relanzar wrapper.
No se instalan/recargan Hyprland/Quickshell ni se ejecutan aplicaciones del usuario desde aquí.
Ver BREEZE_R4_TASK_LAUNCH_RESULTS.json. R4/replacementReady/operationalVerified siguen false.

Validación §248: CTest seleccionado5/5 normal y ASan (launch/thumbnail/appearance/surface/local),
Python R4152 y manifiestos7. QtTest Metadata5/5 y Thumbnail13/13 (init/cleanup incluidos).
Job KDE ejecutado con fixture propio; stdout/stderr de app y vida tras recibo probados también
normal/ASan. No se repite native-task-thumbnail ni diagnóstico/hover aceptados. Alcance real
pendiente: peticiones de arranque/archivos desde el auxiliar actualizado en la sesión del usuario,
activación/foco, lanzadores puros y acciones específicas de aplicaciones; no prometer R4 cerrada.

## Lanzadores anclados y Actions del .desktop (§250)

Ningún lanzamiento de aplicaciones ocurre dentro del host desechable: heredaría su XDG
temporal y su D-Bus privado. Tres piezas:

1. **Política del host.** `preview-isolated.py` (y `check-local.py`) escriben con O_EXCL un
   kdeglobals inmutable en el XDG_CONFIG_DIRS desechable: `[KDE Action Restrictions][$i]
   run_desktop_files=false, shell_access=false`. KIO (ApplicationLauncherJob, OpenUrlJob,
   CommandLauncherJob) lo comprueba antes de crear procesos. El preview no se anuncia listo si
   `taskSource.applicationLauncher.inProcessLaunchDenied` no es `true`.
2. **Lanzadores anclados.** `BwmLaunchRouter` (QIdentityProxyModel +
   `TaskManager::AbstractTasksProxyModelIface`, ambas públicas) se inserta con el
   `setSourceModel` virtual entre `TaskFilterProxyModel` y `ConcatenateTasksProxyModel` de cada
   TasksModel registrado. Las peticiones activar/nueva instancia/abrir URLs sobre filas de
   `LauncherTasksModel` se encolan como `launcher`; lo demás pasa al iface original. No sustituir
   `LauncherTasksModel` en la concatenación: TasksModel usa `concatProxyModel->mapFromSource`
   con índices de su propio modelo de lanzadores (orden manual). Cadenas de terceros sin ese
   enlace no se tocan (sus lanzamientos internos quedan denegados por la política).
3. **Actions del menú original.** `TaskMenuPolicy` toma las QAction que `Backend` cuelga del
   ContextMenu.qml revisado (hash fijado) y compara las últimas con
   `nativeJumpListActions(launcherUrl)` (resolución/filtro de `Backend::jumpListActions`):
   separador, icono y texto sin mnemónicos (KAcceleratorManager) ni elisión. Coincidencia
   completa → `service-action` con el nombre de la Action; el handler de KDE queda conectado
   y KIOSK lo deniega. Sin coincidencia, y Lugares/Recientes (datos del host), → enmascarados
   con un QActionGroup deshabilitado.

Las tres peticiones van por la cola/bloqueo del puente a `native-tasks.py`, que revalida
Breeze bajo el bloqueo nativo y entrega a `--launch-task-application` con el entorno original
restaurado. La resolución replica `runApp` (applications:, preferred:, .desktop local) sin su
respaldo OpenUrlJob/ejecutable; la Action se busca por nombre entre las visibles. El recibo
acredita el traspaso a KIO, no la ventana ni el foco de la aplicación.

## Acciones de ventana restantes y Lugares (§252)

Campos opcionales v1 de la instantánea (`movable`, `windowTagsSettable`, `noBorder`,
`excludedFromCapture`) alimentan los roles KDE IsMovable/IsResizable/HasNoBorder/
CanSetNoBorder/IsExcludedFromCapture. Las peticiones van por la cola/bloqueo nativo a
`kwin-window.py --native-serialized`: `interactive move|resize` exige ventana flotante normal y
la respuesta «ok» de breezebars; `no-border|no-capture --state on|off` aplica el estado deseado
con guardas Lua, recibo y relectura (idempotente). Encima/Debajo no tienen backend.

Lugares: el wrapper copia de solo lectura `user-places.xbel` al host desechable
(`native_launch.snapshot_places`). TaskMenuPolicy casa cada QAction de Lugar con las filas
visibles de KFilePlacesModel (título sin mnemónicos/elisión + icono) y envía una coincidencia
única como `launcher` con el .desktop del gestor y la URL, equivalente al lambda de
Backend::placesActions. Ambigüedades y Recientes quedan enmascarados.

## Modo edición: Ajustes del panel originales (R5, §303)

`panelconfigview.{h,cpp}` adapta `PanelConfigView`/`PanelRulerView` de plasma-workspace 6.7.5
(LGPL-2.0-or-later) y carga el `PanelConfiguration.qml` instalado sin modificarlo. La acción
original del panel `configure` («Enter Edit Mode») lo abre y activa el modo edición de la Corona;
Escape o «Exit Edit Mode» lo cierran. `PanelViewHost` expone el contrato de `PanelView` que usa
(alineación, desplazamiento, modo de longitud, mín./máx., `minThickness`, `adaptiveOpacityEnabled`,
`userConfiguring`). Con el diálogo abierto cada cambio se guarda en `plasmashellrc`; fuera,
los setters son vista previa. Longitud por defecto `FillAvailable`, como Plasma.

Ensayo en la sesión, sólo con una vista desechable:

```
python3 preview-isolated.py --binary build/bwm-plasma-host/bwm-plasma-host \
  --builtin org.kde.plasma.analogclock --native-panel --layer-panel --follow-skin \
  --edit-mode --output "<descripción del monitor>"
```

«Siempre visible» necesita además `--native-policy` (reserva espacio real). «Set Position…»
mueve el panel de borde sin recrear la vista mientras el diálogo está abierto; en esta vista
desechable también a otro monitor (el runtime reabre los ajustes allí). Los perfiles también
admiten mover entre salidas y conservan la asignación por descripción al cerrar limpiamente.

Comprobación en la sesión, sin ratón ni teclado virtuales (acciona el QML original y mide con
`hyprctl layers`; panel desechable 64 px sobre el borde, retirado al final):

```
python3 src/bwm-plasma-host/check-edit-mode-session.py --output "<descripción del monitor>"
```

«Añadir widgets…» (o la acción interna «add widgets» del panel) abre el `WidgetExplorer.qml`
instalado en una capa lateral (`bwm-r5-widget-explorer`) mediante `widgetexplorerview.*` y
`qml/WidgetExplorerHost.qml`, que adapta la parte de `views/Desktop.qml` que el explorador
necesita. Al cerrarse vuelve a los Ajustes del panel, como upstream.

`shell/contents/defaults` lleva el grupo `[Panel]` del paquete de shell de Plasma: libplasma
carga con él la caja de herramientas `org.kde.paneltoolbox` (botón «Configurar» al final del panel
en modo edición, contra el que se mide el `ConfigOverlay.qml` original) y la acción del botón
derecho `org.kde.contextmenu` (menú del panel y de cada widget).

Con `--native-policy`, «Ocultar automáticamente» y «Esquivar ventanas» siguen la lógica de
`PanelView` 6.7.5. En vez del borde de KWin (`kde_auto_hide_screen_edge_v1`), el contenido se
desliza fuera y la máscara de entrada deja una franja de 2 px en el borde. Esquivar usa
`touchingWindow` del `Panel.qml` original, que necesita el puente de tareas y el proveedor de
escritorios.

«Clonar panel» usa las flechas del diálogo original y `panelclone.cpp`, adaptado de
`ShellCorona::clonePanelTo` 6.7.5. Copia opciones nativas de containment/widgets, orden con
IDs nuevos, hijos de la bandeja y todos los ámbitos de preferencias de la vista. Funciona
en la vista desechable y en perfiles, con paneles independientes, también con `--native-policy`
en la misma salida. Como en Plasma, sólo el panel normal más grueso de cada borde reserva
espacio (empate por ID menor). Los otros comparten la reserva y pueden solaparse: no se apilan
artificialmente. En edición se conservan las zonas positivas y los que no reservaban piden
su marco completo; al salir se restaura la selección por borde. El panel diario no forma
parte de ese inventario. `panel-session.py status` expone las capacidades vivas de
cada marco, incluidos `touchingWindow` y `autoHidden`.

Ensayo acotado de clonación, sobre el monitor que no esté usando el usuario:

```
python3 src/bwm-plasma-host/check-edit-mode-session.py --output "<descripción>" --case originalClonePanelInHyprland
```

Límites y pendientes en `docs/BREEZE_R5_RESULTS.md` (escritorio, esquinas/bordes adyacentes,
escala fraccionaria y comparación visual).
Al actualizar upstream, revisar `shell/panelconfigview.*`, los `Q_PROPERTY` de `panelview.h`,
`views/Desktop.qml` (contrato de la barra lateral), `explorer/WidgetExplorer.qml` y el grupo
`[Panel]` de `desktoppackage/contents/defaults`.


## R5: migrar alineación y longitud con tamaños lógicos capturados

`migration.proposal(legacy_json, descriptions, output_sizes=...)` admite un mapa explícito
por descripción, con `[ancho, alto]` en unidades lógicas de cada salida. No convierte píxeles
físicos ni presupone escala 1. Ejemplo con datos de ensayo:

```python
plan = proposal(legacy_json, ["Monitor A", "Monitor B"], output_sizes={
    "Monitor A": [1281, 800], "Monitor B": [1728, 960],
})
```

La propuesta sigue sin activar ni escribir el panel diario. Añade `placementContractVersion=1`,
`outputSize` y `nativePlacementSettings` al artefacto de staging; C++ recalcula desde el JSON
archivado y ese tamaño, y rechaza cambios incompatibles. Los valores terminan en las claves
KDE existentes de `plasmashellrc`: `alignment`, `panelLengthMode`, `minLength`, `maxLength` y
`offset`, con grupos `Defaults` y `HorizontalN`/`VerticalN` para las longitudes.

`start/center/end` se traduce a `AlignLeft/AlignCenter/AlignRight`. La longitud usa el eje del
borde, el clamp de fracción 0,1–1 y el mínimo de 160 del panel heredado, redondeando al entero
lógico más próximo (medios hacia arriba). Fracción 1 sin flotación conserva FillAvailable;
las demás usan Custom. Con flotación se captura el rectángulo mostrado sin ventana tocando,
incluido su `floatingGap` original; los márgenes y la pintura posteriores los decide el SVG
nativo. No se introduce una clave KDE inventada para ese hueco ni se promete equivalencia de
sus animaciones/adaptación. El desplazamiento nativo inicial es 0.

Si no se aporta el mapa, los planes/archivos anteriores mantienen su contrato y dejan
alineación/longitud diferidas. Un tamaño explícito permite convertir la preferencia, pero no
certifica el EDID ni la geometría de una sesión: `outputGeometryVerified` permanece false.
El llamador debe capturar y asociar las salidas, y volver a preparar la propuesta si cambian.


## R5: reservas compartidas de varios paneles (iteración 8)

`PanelRuntime::updateReservations` sigue `ShellCorona::shouldPanelReserveSpace` 6.7.5.
Los candidatos son sólo vistas visibles, normales y de containments no retirados, agrupadas
por QScreen resuelto desde su descripción y borde. El tamaño y los modos de visibilidad
siguen en `plasmashellrc`; elegir propietario no modifica la preferencia del usuario.
La selección se actualiza al cambiar grosor, visibilidad, salida, borde, edición o vida del
panel. Retira la petición del propietario anterior antes de habilitar la siguiente;
los commits de superficies Wayland independientes no constituyen una transacción atómica.

`reservationOwner` y `editModeReservation` en las capacidades del marco describen esa
selección/petición, no certifican que el compositor haya aplicado una reserva. Un cambio
sólo de zona exclusiva necesita `QQuickWindow::update()` para entregar el commit aunque
la escena sea estática: se encontró y reprodujo un fallo con `QWindow::requestUpdate()`.

Comprobación de reservas en el monitor que no tenga la vista del usuario:

```
python3 src/bwm-plasma-host/check-edit-mode-session.py --output "<descripción>" --case nativeMultiplePanelReservationsInHyprland
```

Mide máximo frente a suma en el mismo borde, traspasos, retirada de la última reserva,
reserva temporal en edición, eliminación del propietario, cambio a borde opuesto y limpieza.
No se infiere con ello equivalencia de esquinas/bordes adyacentes, anclaje de todos los
popups o escalas fraccionarias. R5 sigue abierta; no se reemplaza el panel diario.


## R5: alternativas de widgets, arrastre al panel, reordenado y desinstalación (iteración 9)

`alternativeshelper.{h,cpp}` y `PanelViewHost::showAlternativesForApplet` adaptan
`AlternativesHelper` y `ShellCorona::showAlternativesForApplet` de plasma-workspace 6.7.5
(LGPL-2.0-or-later). Registran `AlternativesHelper` en `org.kde.plasma.shell` (2.0 y 1.0),
conectan `Containment::appletAlternativesRequested` (acción interna `alternatives`) y cargan
sin modificar el `explorer/AppletAlternatives.qml` instalado. `loadAlternative` traslada el
atajo global, copia la configuración al nuevo widget, destruye el anterior y conserva su
posición en `AppletOrder`.

En una vista layer-shell, el `PlasmaCore.Dialog` de alternativas recibe un `PopupAnchor`
(`bwm-r4-popup`, `LayerOverlay`, teclado `OnDemand`) al crearse su superficie. `PopupAnchor`
calcula un tamaño inicial no nulo desde `mainItem` (+ `margins`) antes de `Dialog::showEvent`
y, como todas las instancias de `SharedQmlEngine` comparten el mismo `QQmlEngine`, tanto
`PanelConfigView` como el filtro de alternativas comprueban la jerarquía `rootContext()` de
su propio motor antes de adoptar un `Dialog` en `SurfaceCreated`.

El ensayo offscreen `originalAppletAlternativesDragAndUninstall` (`test-ui.cpp` /
`check-local.py`) prueba el diálogo de alternativas, el arrastre `text/x-plasmoidservicename`
sobre el `DropArea` de `org.kde.panel`, el reordenado con `ConfigOverlay.qml` y la retirada +
desinstalación de un widget local desde `WidgetExplorer.qml` (`removeAllInstances` y
`pendingUninstallTimer.uninstall()`). En sesión Hyprland, `panelOwnPopupsInHyprland`
(`check-edit-mode-session.py`) comprueba además que `AppletAlternatives.qml` se mapea como
capa `bwm-r4-popup` encima del widget (sin crear un `xdg_toplevel`) y sustituye el reloj en
el panel vivo.


## R5: bordes adyacentes, esquinas, popups y escalas fraccionarias (iteración 10)

Con `FillAvailable` (`lengthMode == 0`), `surfaces.cpp` ancla ambos bordes perpendiculares
(`AnchorLeft|AnchorRight` o `AnchorTop|AnchorBottom`, como `PanelView::updateLayerWindow` 6.7.5)
para que Hyprland ajuste la longitud al `usableArea` sin solapar paneles en bordes adyacentes.
`PanelRuntime::updateReservations()` calcula por orden de creación de superficie (`surfaceOrder()`)
el `bwmPanelBounds` de cada panel y el rectángulo disponible resultante, publicándolo en
`ViewCorona::setScreenAvailableRect` y `BwmSurface::setPanelLayoutContext`.

Los popups anclados a paneles que reservan espacio (`PopupAnchor`, cuando `!m_requestedPosition`)
usan `exclusiveZone = 0` y anclas alineadas al borde del panel con sólo el saliente flotante
(`max(0, panelCross - zone)`), respetando automáticamente tanto paneles adyacentes del anfitrión
como barras externas del compositor. `PanelRulerView` usa `KeyboardInteractivityNone` y
`activateOnShow = false` para no robar el foco de teclado (Escape) a `PanelConfigView`.

Verificación en Hyprland con bordes adyacentes/esquinas y con escalas fraccionarias (`1.25`, `1.5`,
`1.6`) sobre una salida headless temporal (`BWMR5-*`) sin modificar salidas físicas:

```
python3 src/bwm-plasma-host/check-edit-mode-session.py --output "<descripción>" --case nativeAdjacentEdgesAndCornerPopupsInHyprland
python3 src/bwm-plasma-host/check-edit-mode-session.py --fractional-scale
```


## R5: anfitrión de escritorio y `DesktopEditMode.qml` (iteración 11)

`desktopviewhost.{h,cpp}` adapta `DesktopView` de plasma-workspace 6.7.5 (GPL-2.0-or-later)
sobre `PlasmaQuick::ContainmentView` y carga sin modificar el `views/Desktop.qml` instalado
(junto con `views/DesktopEditMode.qml`) para un containment `org.kde.plasma.folder`.
`shell/contents/defaults` incluye ahora también `[Desktop]` y `[Desktop][ContainmentActions]`
de plasma-desktop 6.7.5.

`ViewCorona` expone `panelBeingConfigured`, `enteredEditModeViaDesktop()`, `showAddPanelContextMenu`
(Default/Empty Panel) y las acciones `"add panel"` / `"edit mode"`. `PanelViewHost` publica
`relativeConfigRect` y `PanelConfigView` conserva el modo edición abierto al cerrarse si se
entró desde el escritorio. En Hyprland, `DesktopViewHost` usa `LayerBackground` (`bwm-r5-desktop`,
`wantsToBeOnActiveScreen = false`), el `sidePanel` de `Desktop.qml` se ancla como `LayerTop`
(`bwm-r5-desktop-explorer`, `exclusiveZone = 0`, `FocusGrab`) y `AppletAlternatives.qml` como
`LayerOverlay` (`bwm-r5-desktop-popup`).

Comprobación en sesión Hyprland sobre una salida concreta:

```
python3 src/bwm-plasma-host/check-edit-mode-session.py --output "<descripción>" --case originalDesktopEditModeInHyprland
```

## R5: cierre — escritorio interactivo, configuración y «Add Panel» (iteración 12)

- **Vista desechable con escritorio:** `preview-isolated.py ... --native-panel --layer-panel --follow-skin
  --desktop --output "<descripción>"` añade el `Desktop.qml` original sobre la misma salida mientras la
  skin seguida sea Breeze. `desktop:/` apunta a una carpeta desechable (`XDG_DESKTOP_DIR` en el
  `user-dirs.dirs` temporal) y la plataforma Qt es `kde` (Breeze por defecto de la configuración vacía).
  `BWM_R5_DEBUG_MENUS=1` registra cada `QMenu` (acciones, ocultas, geometría) y
  `QT_LOGGING_RULES="bwm.r5.corona.info=true"` la asignación de pantalla del escritorio.
- **Folder View y menú del escritorio:** el `main.qml` original sólo activa la capa de iconos cuando
  `corona.isScreenUiReady(screen)` es verdadero al cambiar la pantalla del contenedor. `ViewCorona` sigue
  ahora el orden de `ShellCorona`: el escritorio no recibe pantalla hasta que su vista es visible y los
  paneles de esa salida están listos, y la conserva después (añadir un panel no la retira).
  `DesktopViewHost` registra la acción `desktop edit mode` de `DesktopView`; `edit mode` vuelve a ser la
  acción de libplasma (alternar). El menú de `org.kde.contextmenu` queda como en Plasma: Create New,
  Paste, Undo, Icons, Enter Edit Mode, Desktop and Wallpaper.
- **«Desktop and Wallpaper…»:** `ContainmentConfigView` (adaptado de plasma-workspace 6.7.5) carga el
  `ContainmentConfiguration.qml` instalado (Wallpaper, Mouse Actions, Location, Icons, Filter, About),
  aplica el fondo al contenedor y cambia el contenedor (Layout) con `DesktopViewHost::setContainmentType`,
  relanzando el diálogo como `DesktopView`. Tras cargar, el anfitrión llama una vez a la función original
  `settingValueChanged()`: la página del fondo marca cambios mientras se crea (normaliza `SlidePaths`)
  antes de que `AppletConfiguration.qml` conecte su aviso.
- **«Add Panel»:** `ViewCorona::showAddPanelContextMenu` reproduce `populateAddPanelsMenu` (plantillas con
  categoría `panel` y contenedores `Panel`); `PanelRuntime::addPanel` ejecuta sin modificar el `layout.js`
  de la plantilla en `LayoutTemplateRunner` (subconjunto de la API de scripts: `Panel`, `panelIds`,
  `panelById`, `screenGeometry`, `gridUnit`, `languageId`); cualquier otra llamada falla de forma visible.
- **Área útil real:** en Hyprland `strictAvailableScreenRect` cruza el área de los paneles propios con
  `reserved` del monitor (`hyprctl -j monitors` asíncrono con `BWM_R5_HYPR_RUNTIME`), como KWin con todos
  los struts; el explorador lateral y `DesktopEditMode.qml` respetan también barras externas.

Pruebas: `originalDesktopEditModeHost` y `originalDesktopContainmentConfiguration` (offscreen normal/ASan),
`originalDesktopEditModeInHyprland` (menú y área útil) y el paso `fractional-desktop-edit-mode` de
`--fractional-scale`. Ejecutar las pruebas offscreen sin `QT_QPA_PLATFORMTHEME` heredado de la sesión
(`gtk3` en Retro intenta abrir una pantalla GTK).


## R5, iteración 13: marco nativo, gestor de pantallas y referencia real

Las configuraciones interactivas de widgets usan ahora el `AppletConfiguration.qml` instalado
(barra lateral, Atajos, Acerca de y aviso de cambios). Los diagnósticos `--probe`/`--exercise`
conservan su arnés R4. `containmentmanagement` adapta los modelos de Plasma 6.7.5 y carga el
`ShellContainmentConfiguration.qml` original: mover paneles, intercambiar escritorios,
recuperar contenedores desconectados, previsualizar contenido propio y eliminar. Las asignaciones
de panel siguen usando descripciones físicas. No se sustituye el escritorio/panel diario.

«Add Panel» consulta la salida activa del compositor. Las preferencias de la plantilla preceden
la reserva inicial de edición. «Aplicar» empieza desactivado como en Plasma y responde al primer
cambio real del fondo. Al recrear una superficie, usar **`QWindow::destroy()`**, no el método
homónimo de `ContainmentView` (elimina el anfitrión).

Comparación reproducible con plasmashell/KWin 6.7.5 privados, escalas reales y botón central
sobre una selección primaria desechable:

```bash
python3 src/bwm-plasma-host/check-r5-reference.py --report /tmp/bwm-r5-reference-results.json
```

El resultado distingue paridad de las ventanas de configuración de la comparación completa
con efectos del compositor. Requisitos, resultados, diferencias y límites en
`docs/BREEZE_R5_RESULTS.md`, iteración 13; evidencia en `docs/BREEZE_R5_REFERENCE_RESULTS.json`.
