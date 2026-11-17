# Traspaso R4 para Claude

## Traspaso actualizado — 2026-11-17 (§252)

Hecho tras §251: Mover/Redimensionar, Ocultar de capturas y Sin borde del menú original por el
gestor común (estado deseado, recibo, relectura) y Lugares reales del usuario enrutados con la
URL. Pruebas locales completas y tags comprobados en sesión sobre una kitty desechable.
Aceptado por el usuario en sesión (§253): «todo revisado, funciona». No pedir repetirlo.
Encima/Debajo sin backend; geometría de delegados, proveedor de escritorios y panel diario
siguen pendientes. Evidencia docs/BREEZE_R4_WINDOW_ACTIONS_RESULTS.json, BWM_CONTEXT §3.252.

## Traspaso actualizado — 2026-11-17 (§250)

Prevalece sobre §249 en lo relativo a lanzadores. Hecho: lanzadores anclados sin ventana y
Actions del .desktop del menú original salen por el helper con el entorno original
(BwmLaunchRouter entre TaskFilterProxyModel y ConcatenateTasksProxyModel; TaskMenuPolicy
enruta las QAction del Backend que coinciden con el .desktop). El host desechable lleva KIOSK
inmutable run_desktop_files/shell_access=false: KIO no lanza nada dentro del auxiliar y el
arranque del preview lo exige. Lugares/Recientes enmascarados (datos del host temporal).

Pruebas locales: CTest 13/13 normal y ASan (detect_leaks=0; los fixtures Wayland nativos
sí corren en este ejecutor), Python R4 155, skins/puente 27. Ensayo de estado en sesión por
el asistente sin clics (1 ruta, 4 lanzadores, KIOSK activo) y parada limpia. Evidencia
`docs/BREEZE_R4_PINNED_LAUNCH_RESULTS.json`, BWM_CONTEXT §3.250.

Aceptado por el usuario en sesión (§251): lanzador anclado sin ventana, Action «New Window»
de Firefox y archivo soltado sobre Firefox anclado. La ventana nueva a la derecha es lo original
de KDE para org.kde.plasma.taskmanager (separateLaunchers). No pedir repetir §247–251. Siguen pendientes foco/activación de apps nuevas, Lugares/
Recientes, proveedor de escritorios y autoridades/fallback del panel diario. Sin commit/push.

## Traspaso actualizado — 2026-11-17 (§249)

Continuar sólo R4. Esta actualización prevalece sobre pendientes históricos de aceptación
que aparecen más abajo. No hay commit/push de este traspaso; existen numerosos cambios
anteriores, ajenos y generados: revisar git status/diff y conservarlos.

Aceptación manual del usuario después de §248:
- Miniaturas: «perfecto ya tiene miniaturas» (§247).
- Clic central abre otra ventana de Firefox; el usuario integra después su pestaña en la
  otra ventana y comprueba minimizar. Apertura de nueva instancia y minimizar aceptadas.
- Tras explicar que debía arrastrar una imagen local al icono de Firefox de la barra auxiliar,
  responde «se abre». Apertura de archivo desde el icono aceptada. No confundir con sólo
  arrastrar una pestaña entre ventanas. No se midió foco, actualización ni matriz de monitores.

No pedir repetir estas pruebas ni recompilar Hyprland: guarda IPC del compositor ya
verificada (§245, PID coincidente), fixture nativo de miniaturas aprobado (§241) y tooltip
corregido aceptado. La lectura /proc/PID/exe denegada con filecaps es esperada; conservar
verificación IPC ligada a SO_PEERCRED, nunca debilitar permisos/capacidades.

Último código: §248, nueva instancia/open-urls de tareas con ventana mediante
BwmTaskSource → cola BwmTaskBridge → native-tasks.py → --launch-task-application →
KIO::ApplicationLauncherJob. Entorno permitido de la sesión original restaurado para ese
proceso; contexto capturado por preview-isolated.py/native_launch.py. Recibo CLOEXEC,
proceso separado del grupo de acciones y arranque acotado; no terminar apps al retirar.
CanLaunchNewInstance es visibilidad de menú, no veto de peticiones explícitas; adaptación
LGPL de política .desktop porque helper KDE no exportado. Créditos/licencia preservados.
KIOGui declarado en CMake/requisito de build; tabla de requisitos regenerada.
Pruebas previas verificadas §248: CTest seleccionado5/5 normal y ASan, Python R4 152,
manifiestos7, Metadata QtTest5/5, Thumbnail13/13 (incluyen init/cleanup). No se han repetido
para este traspaso documental. Evidencia BREEZE_R4_TASK_LAUNCH_RESULTS.json.

Siguiente trabajo concreto: revisar lanzadores anclados SIN ventana abierta y acciones
específicas de aplicaciones (.desktop Actions), que aún siguen el camino KDE anterior y
pueden heredar entorno temporal del preview. Mantener formatos/handlers originales y
compatibilidad de terceros; investigar APIs públicas antes de adaptar. Probar con apps
propias y XDG temporales, sin lanzar/cerrar apps personales para ensayos automáticos.
También pendientes: foco/activación de nuevas apps, aceptación del proveedor nativo de
escritorios y autoridades/fallback del panel diario. No activar proveedor ni sustituir
panel sólo por estos pases. No avanzar a R5/R7 ni declarar R4 completa.

El usuario dejó el auxiliar abierto; su estado actual no se ha comprobado hoy. Antes de
actuar inspeccionar capacidades reales del ejecutor. Hubo pérdida temporal de acceso al
entorno en esta conversación, no un fallo demostrado del PC; no intentar eludir sandbox.
No arrancar Quickshell duplicado, ejecutar plasmashell ni hot load/unload de plugins.
Sudo lo ejecuta el usuario. No tocar configuración personal protegida. No commitear/pushear
salvo petición. Leer AGENTS.md/CLAUDE.md completos y BWM_CONTEXT.md §2.4/§3.239–249.

Comando conocido del auxiliar (sólo relanzarlo si hace falta adoptar cambios):
```sh
python3 /mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/preview-isolated.py \
  --binary /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host/bwm-plasma-host \
  --builtin org.kde.plasma.taskmanager --native-panel --layer-panel --instances 1 \
  --follow-skin --task-actions --all-desktops --session-appearance --task-thumbnails \
  --output "Micro-Star Int'l Co. Ltd. MAG 274Q X24 0x01010101"
```


Actualización tras e41c28d: la puerta original de widgets externos y el ciclo KNS ya están superados (§209). La integración diaria y aceptación restante siguen abiertas. Lee `CLAUDE.md` completo, `BWM_CONTEXT.md` §2.4 y §3.183–214, `docs/BREEZE_PLAN_V2.md` (reglas comunes y R4), `docs/BREEZE_R4_RESULTS.md`, `docs/BREEZE_R4_ARCH.md` y el README de `src/bwm-plasma-host`. Contrasta el código y el estado de Git antes de modificar nada: hay numerosos cambios y archivos sin seguimiento anteriores que deben conservarse.

## Estado comprobado

- El auxiliar libplasma experimental aloja widgets y sus páginas originales; la opción propia de un widget externo se ha probado con persistencia aislada. Hay interfaces experimentales para panel, containments, catálogo y configuración. Consulta los informes para el alcance exacto.
- El usuario confirmó en Hyprland la reserva del panel temporal y el reajuste automático de una ventana maximizada completa en MSI, borde inferior, escala 1 y giro 0: reserva 44→92→44 y altura del marco 1396→1348→1396. Informe: `docs/BREEZE_R4_AREA_SESSION_RESULTS.json`. No extrapolar a otras salidas, ejes, escalas o bordes.
- El panel diario de Quickshell aún no ha sido sustituido. `replacementReady=false`: no convertir una prueba aislada en aceptación de producción. El puente Breeze se recargó para el ensayo y su observador de área queda activo.
- Existen resultados aislados y limitaciones de backend, migración y KNS en `docs/BREEZE_R4_RESULTS.md` y `docs/BREEZE_R4_ARCH.md`. Claude validó la descarga/retirada real por KNS y tres widgets desconocidos; Modern Clock también guardó su opción en Hyprland. Véase BREEZE_R4_KNS_RESULTS.json. Quedan el diálogo KNS gráfico y la aceptación completa de sesión.

## Continuación

Completa sólo R4 conforme al prompt y puertas de salida originales. Prioriza integración/selección/fallback seguro del panel nativo, autoridades y backends de widgets, ciclo real de KNS y aceptación de sesión, según el estado efectivo del código. Conserva los formatos KDE, la configuración y las opciones desconocidas. Prueba persistencia y migración sin destruir el origen; clasifica las capacidades no soportadas por paquete. Valida ambas pantallas, bordes/escalas y cambios de skin cuando corresponda. No declares R4 completa si sus criterios no se cumplen; documenta cada bloqueo con evidencia y alternativa.

El usuario autorizó alterar su sesión cuando sea necesario para el proyecto. Sigue las reglas de seguridad de plugins de `CLAUDE.md`, nunca cargues/descargues `.so` en caliente ni arranques una segunda instancia de Quickshell. No ejecutes plasmashell ni cambies de compositor. No alteres archivos de configuración personal protegidos. Evita repetir pruebas ya documentadas salvo cambios o dudas concretas.

En la ejecución anterior el sandbox no podía acceder a los sockets Hyprland/Wayland/D-Bus y una elevación fue rechazada por política. Comprueba tus propias capacidades sin intentar eludir restricciones; si no puedes ejecutar una prueba de sesión, prepara un comando acotado y claro para que el usuario lo ejecute. No pidas confirmación para acciones ya autorizadas. Actualiza resultados, arquitectura, `BWM_CONTEXT.md` y, si corresponde, `AGENTS.md` y `CLAUDE.md` sincronizados. No hagas commits ni avances a R5/R7 sin indicación.

Continuación Codex (§210): build limpio y CTest local sin fuentes externas; defaults del runner ya no dependen de una extracción KDE antigua. Leer BREEZE_R4_REPRO_RESULTS.json y conservar los tres metadata.json propios aún sin seguimiento. El ejecutor Codex sigue sin IPC real.

Continuación §212: adaptador KWindowSystem estático/privado 6.29.0 en el auxiliar, con --desktop-actions y --builtin. Controlador ShowDesktop KDE original hacia gestor común minimizar/restaurar, probado con IPC ficticio normal/ASan; no efecto Peek ni TaskManager secundario. Leer BREEZE_R4_DESKTOP_ADAPTER_RESULTS.json. Sesión real/Wayland y capa diaria siguen pendientes; el opt-in puede minimizar/restaurar ventanas del usuario.

§213: binario compartido de sesión en build/bwm-plasma-host/bwm-plasma-host; usar esa ruta, no depender de /tmp entre sesiones. Preflight y errores de exec corregidos; BREEZE_R4_STABLE_BINARY_RESULTS.json.

§214: usuario confirma minimizar/restaurar al pulsar el botón nativo; BREEZE_R4_DESKTOP_SESSION_RESULTS.json (manual, sin telemetría ni matriz). Persisten TaskManager/Toolbox/sombras de tooltip y los pendientes de integración diaria.

§215: fuente experimental BwmTaskSource/BwmTaskBridge (LibTaskManager 6.7.5 EXACT + KF6
Service), activada sólo mediante --task-actions en preview. Reemplaza con APIs públicas Qt
la fuente estándar WaylandTasksModel y respeta fuentes personalizadas. Dos TasksModel
auténticos reciben la misma ventana y tramitan minimizar/restaurar/cerrar hacia el helper
native-tasks.py y el gestor común con IPC ficticio. Normal/ASan, índices persistentes y
retirada/restauración de fuente probados. BREEZE_R4_TASK_SOURCE_RESULTS.json contiene hashes,
logs y límites. No hay prueba nueva en sesión ni certificación del widget entero.

Continuar por VirtualDesktopInfo y gating de menús: no confundir los cuatro métodos de
acción con compatibilidad completa. En offscreen el test da una tabla vacía de una columna
al StartupTasksModel sin backend; no es código de producción ni prueba de delegados QML.
También faltan coordinación de mutaciones entre procesos/ShowDesktop y gestores diarios,
quiescencia durante transición, acciones restantes y aceptación Wayland antes de takeover.
taskSource.snapshotAvailable sólo confirma la última respuesta válida; pendingActions
cuenta la cola, sin incluir el proceso en curso, y lastError conserva el último fallo.

§216: serialización compartida para las dos entradas nativas (--native-serialized,
native_guard.py, flock privado con timeout 1 s) y comprobación de skin/generación tras esperar.
PanelRuntime suspende ambos puentes; RuntimeControl reintenta sin ack/revisión hasta finalizar
la acción. Colas descartadas, sólo snapshots cancelados y reanudación probada. No cambiar el
aborto seguro del hook ni ampliar sus timeouts. ASan/local/Python y hashes en
BREEZE_R4_NATIVE_TRANSACTIONS_RESULTS.json. Los llamadores diarios no participan todavía;
la quiescencia es local al auxiliar y no promete rollback de una terminación forzada.

VirtualDesktopInfo no tiene factoría pública: READ, métodos no virtuales y Private* estático.
No usar intercambio privado ni símbolos duplicados; revisar consumidores C++ de filtro/orden
además del QML antes de decidir la integración. Sigue pendiente, igual que menús/acciones,
aceptación Wayland y autoridades diarias. No avanzar R5/R7 ni certificar el widget completo.

§218: DesktopProtocol v4 y workspaceSnapshot en src/bwm-plasma-desktops, con frontend
Hyprland opcional separado/compilado/desactivado, sin instalar, cargar ni autoiniciar.
CTest incluye proveedor original VirtualDesktopInfo C++/QML, filtros por salida, orden inicial
y roles QML con socketpair Wayland privado (no user session ni rendering), 4/4 normal/ASan.
Ver BREEZE_R4_NATIVE_DESKTOPS_RESULTS.json y README del componente. El núcleo y el módulo
llevan -fno-gnu-unique: se corrigieron UNIQUE de las tablas estáticas del núcleo y se verificó
readelf del .so. XML privado fijado por hash. No usar make install ni hot load/unload como
prueba; hace falta revisión e inicio de sesión nuevo para una futura validación real.

Pendiente antes de activar: verificar conflictos de global, frontend y acciones en Hyprland,
coordinar la barrera/cola de activación con el host (sin flock bloqueante en compositor),
menús y create/remove/wrapping, especiales, matriz Wayland y autoridades de panel diario.
El fixture permite request_enter_output entre salidas; el plugin real sólo admite desktop
materializado/asignado a esa salida. No extender evidencia entre esos backends. Task.qml y
widget completo no certificados; no R5/R7 ni takeover.

§219: barrera por wl_client implementada en núcleo y cliente Qt del host. Cola real movida
a DesktopProtocol; conexiones nacen sólo lectura, exigen control/resume para activar. Pause,
destruir propietario o perder recurso/cliente cancelan trabajo propio; otro cliente no se
pausa. NativeDesktopControl exige ack con serial vigente/timeout 1 s; RuntimeControl espera
junto a los gestores locales, conserva revisión inicial pendiente, permite retirada sin el
propio proveedor y exige confirmación nueva al recuperarlo. --native-desktops sólo comprueba
proveedor ya cargado/habilitado y protocolo real; no carga/instala/habilita. Sin despliegue.

CTest 5/5 normal/ASan: dos clientes, same-flush cancel, propietario destruido/rebind,
pérdida/reconexión y timeout con ack tardío. Se corrigió init(nullptr) de Qt generado (no es
deinit); vida de proxy local/rebind cubierta. El fixture bloquea sólo su loop por pipe,
nunca el compositor/procesos del usuario. Ver BREEZE_R4_DESKTOP_CONTROL_RESULTS.json.

Antes de activar en sesión siguen pendientes frontend real/conflictos, arranque, menús y
create/remove/wrapping/especiales y autoridades diarias. Esta barrera no serializa todas las
acciones de ventanas/workspaces ni controla otras conexiones; no afirmar compatibilidad
completa por estos resultados. Sin R5/R7 ni takeover, sin hot load/unload.

§220: TaskMenuPolicy mantiene el ContextMenu.qml instalado; filtro QMenu público restringido
a raíces registradas + rol BWM versionado + hash exacto de la fuente original. Encima/debajo/
excluir captura sin backend quedan deshabilitados mediante un QActionGroup no exclusivo por
acción, sin tocar bindings QML. Para retirar: grupo enabled=true antes de removeAction (Qt
no recalcula enabled sólo al quitarlo), preservando el estado explícito reciente. No reutilizar
un grupo global: reactivarlo habilitaría otras acciones. Conservar propietarios de acciones
apps/menús ajenos. Cambio de fuente o grupo ajeno bloquea el menú afectado con diagnóstico.

Test-taskmenu carga icontasks/Task.qml/ContextMenu originales: minimizar individual y grupo2,
restricciones, restauración de enabled y cierre al quitar filas. CTest 5/5 normal/ASan,
Python R4 105 + skins7. Evidencia BREEZE_R4_TASK_MENU_RESULTS.json. Avisos undefined de
Task.qml en offscreen por roleNames del backend nativo ausente; StartupTasksModel fixture
sólo en test. NO acredita render del Task.qml, menú visual/entrada Wayland ni panel entero.
No se implementaron nuevas acciones; permanecen foco/minimizar/maximizar/cerrar. La errata
upstream CanSetNoBoder sigue sin convertir no-border en capacidad. Revisar source pin/QMenuItem
al actualizar, nunca parchear KDE para ocultar el problema. Falta aceptación real de menú/
frontend/proveedor y capacidades/autoridad/fallback del panel diario. Sin R5/R7 o takeover.

§221: fullscreen conectado al menú TaskManager original. Fuente usa fullscreenable opcional
(ausente=false; inválido rechaza snapshot) y estado deseado booleano. Helper/gestor común
exigen identidad/inicio y --native-serialized fullscreen --state on|off; llamada diaria sin
opciones conserva toggle. Capacidad sólo normales mapeadas/no ocultas/no fijadas/no minimizadas.
No ampliar a Magic, minimizadas o fijadas por un flag de UI. La Lua revalida skin/PID/estado y
usa set/unset; recibo por hyprctl repl sólo con result.ok y w.fullscreen igual al solicitado.
Exit=0/ok genérico/éxito sin cambio no bastan. Timeout 2 s; no esperar procesos en compositor.

Test original individual/grupo, checked al reabrir, modelo/capacidad y on/on/off desde dos
TasksModel con helper/gestor reales y Lua ejecutado en hl simulado. CTest normal/ASan 5/5;
TaskTest 8/8 y MenuTest 3/3 contando init/cleanup; Python R4 113, ventanas14/minimizar7/skins7.
BREEZE_R4_FULLSCREEN_RESULTS.json. Lua intérprete sólo BUILD_TESTING, resuelto por CMake;
no servidor ni dependencia nueva de runtime. Sigue sin acceso a socket de Hyprland y sin
prueba física de fullscreen/restauración/foco/monitores/skins o pintado de Task.qml. No R5/R7,
plugins o panel diario activados. Siguiente aceptación: frontend/proveedor y menú reales,
resto de capacidades y autoridades/fallback de sesión; no afirmar cierre por este recibo.

§222: corregido AppData obsoleto al actualizar una aplicación .desktop. Repro real guardado:
KSycoca notificaba pero la fuente conservaba First metadata tras cambiar a Updated metadata.
BwmTaskSource escucha databaseChanged, coalesce 100 ms e invalida los seis roles usados;
resuelve diferido mediante TaskTools. No reset de filas/UUID, watcher por ventana ni acción
nueva. Mantener refresh vacío seguro y conexiones QObject/QTimer acotadas a vida del modelo.

Test-taskmetadata usa kbuildsycoca6 real en XDG temporal, PNG/entrada propios y señal nativa:
actualización, retirada/reinstalación, dos fuentes e identidad estable; fuente destruida y otra
vaciada/reabierta durante cambios. No ejecuta Exec ni inyecta señales. El runner quita KDESYCOCA
y exige raíz privada; CMake requiere herramienta sólo en BUILD_TESTING. KF6 Service ya estaba
requerido. CTest 5/5 normal/ASan, test 3/3 contando init/cleanup, R4 Python113 y skins7.
BREEZE_R4_TASK_METADATA_RESULTS.json contiene fallo previo/hashes/salidas. No extrapolar a
catálogo de widgets, todos los temas de iconos o Task.qml pintado; sin nueva validación visual.
R4 abierta por integración/aceptación/capacidades/autoridades diarias. Sin R5/R7 ni takeover.

§223: guardas de registro y asociación implementadas. NativeDesktopRegistry observa globals
sobre el wl_display Qt existente y hace sync asíncrono. Exige management KDE >=4/control>=2,
únicos y asociados por desktop_global. El interface sigue llamándose _v1 pero su versión es 2;
server manda nombre visible por wl_client (Wayland >=1.22), diagnóstico/launcher actualizados.
No usar QWaylandClientExtension para el control: Qt 6.11.2 desactiva por interfaz al retirar
un duplicado. El control tiene proxy explícito por ID. Native KDE VDI sigue intacto.

Duplicar management KDE deja latch por proceso: sólo auxiliar nuevo recupera consumidores.
Prueba SDK original: viejo 0 escritorios, nuevo proceso 4; mismo proceso/objeto nuevo no evade
la guarda. Pausa/salida no se bloquean. Inventario tardío necesita revisión nueva. Runtime
oculta superficies/popups propios inmediatamente y reconcilia después; marca de ocultación
permite recuperar misma vista si confirmación llega antes. Sólo visibilidad offscreen probada.

Core conserva controles retirados inertes hasta destroy/disconnect: peticiones en vuelo no
matan conexión. Clientes v1 siguen probados. No hot unload: sus handlers pertenecen al módulo.
CTest normal/ASan 5/5, Qt Wayland 7/7 incl. init/cleanup, Python R4 113/skins7. ASan construido
en build/bwm-plasma-host-asan. Extensión compilada aparte, sin instalar/cargar y sin GNU UNIQUE.
Requisitos/guía actualizados; BREEZE_R4_REGISTRY_RESULTS.json conserva hashes/salidas/límites.

Esto verifica el cliente, no impide globals duplicados en servidor. No desplegar antes de
arbitraje/frontend/arranque y sesión real. Siguen capacidades/autoridad/fallback diarios y
render/entrada Wayland pendientes; operationalVerified/replacementReady false. Sólo R4.


§225: DesktopProvider ya arbitra antes de publicar el frontend y el fixture. Primero inventario
asíncrono en socketpair del mismo wl_display, después claim (menor ID visible), después par
KDE/control inicialmente no disponible y fence antes de habilitar. Inicialmente disabled no
anuncia globals vacíos. Snapshot inválido no reanuda; se ha quitado el fallback publish({}).

Al retirar conservar una única generación completa: wl_global_remove, controles inertes,
core/managers/desktops/globals/ofertas vivos hasta teardown; solicitudes en vuelo/late binds
no matan clientes. Nunca resetear ese core en caliente para reactivar. Claim creado implica
una publicación/intento por vida del módulo; providerRestartRequired pide futuro inicio de
sesión, NO hot unload/load. Esto sigue siendo restricción experimental, no KCM diario activo.

14 escenarios C++, consumidor VirtualDesktopInfo C++/QML original, CTest7/7 normal/ASan,
Python R4 113/skins7; BREEZE_R4_PROVIDER_ARBITRATION_RESULTS.json. Recompilada extensión con
cero GNU UNIQUE, sin instalar/cargar/autostart/takeover. Wayland client ya estaba declarado.
Launcher exige serverArbitrationVersion=1/active/restartRequired=false además de barrera v2.

No confundir este arbitraje con bloqueo de todos los módulos: sólo ve globals del peer bajo
el filtro existente, y un proveedor ajeno puede aparecer antes de observarlo/retirar el propio.
Claims no autentican. Mantener guardas del auxiliar §223; duplicado KDE pide auxiliar nuevo.
No afirmar pruebas físicas/visuales ni implementación completa de frontend/arranque.

Siguiente trabajo R4: revisar frontend/arranque/filtros de Hyprland y recuperación entre
generaciones antes de despliegue al inicio de sesión; conservar las prohibiciones de hot
load/unload. Después aceptación de consumidores/menús Wayland y capacidades/autoridad/fallback
diarias. No avanzar R5/R7 ni habilitar panel diario por estas pruebas. operationalVerified y
replacementReady siguen false. Preservar cambios ajenos de atajos/menús/bandeja de §224.

Pérdida del peer también después de retirado: no ignorar ese fallo por terminal=true;
marcar E/S fallida y quitar fd source para no iterar con HUP. Ambos estados están probados.


§226: corregidos arranque y cierre del proveedor tras revisar fuentes Hyprland 0.56.2.
El observer se crea en idle sólo después de snapshot+opt-in; antes de dispatch no corre
su deadline. Cancelar antes del claim sigue permitiendo reintentar. Fallar el registro del
diagnóstico aborta antes de publicar. Disabled no abre sockets/peer ni temporizador.

MUY IMPORTANTE: cleanup de Hyprland ejecuta unloadAllPlugins antes de destruir clientes.
La estrategia vieja de dejar controles con userdata=null tras destruir el core dejaba
handlers/interfaz en el .so descargado. Ahora withdraw retiene core+recursos; su destructor
definitivo destruye todos los controles registrados (incluidos retirados/late binds) y el
proveedor todos los recursos del claim. withdrawn hace inertes los controles retenidos,
con propietario para seguimiento. Límites controles4096/claim256. No revertir a la estrategia
antigua. Fixtures retienen cores retirados hasta terminar clientes; destruyen todo antes del display.

Prueba nueva: DSO sólo de test del core/proveedor, símbolos internos ocultos y sin GNU UNIQUE,
cliente enlaza los cuatro tipos de recurso + control tardío. Destruir proveedor → cero recursos
propios → dlclose → RTLD_NOLOAD negativo → destruir clientes. Activo/retirado, normal/ASan.
No despachar peticiones después del cierre definitivo ni deducir hot unload seguro. No es
el plugin Hyprland real, ni prueba logout físico o estabilidad de otros módulos.

16 escenarios, CTest7/7 normal/ASan detect_leaks=0/halt_on_error=1 y Python R4 113. Extensión
recompilada, no instalada/cargada/autostart, sin alterar sesión/panel. Evidencia exacta
BREEZE_R4_STARTUP_TEARDOWN_RESULTS.json. Test libdl/CMAKE_DL_LIBS sin dependencia nueva de producción.

Fuentes confirman filtro de esa versión permite peer directo interno no sandbox; nuevos
globals se consideran privilegiados para security-context. No cambiar filtros. Repetir
revisión sobre versiones/parches nuevos. Resta frontend/arranque/filtro real, futuras
generaciones y capacidades/aceptación/autoridad/fallback. Revisar E/S de count(): lee
config.json desde el hilo compositor cada500ms antes de despliegue diario. Mantener todas
las prohibiciones de hot load/unload y no activar panel diario; sólo R4.

El preflight de --native-desktops exige providerLifecycleVersion=1 (entero, no booleano)
y observerStartup=deferred-event-loop, además de las guardas anteriores. Diagnósticos de
un módulo antiguo se rechazan antes de lanzar el auxiliar; sin instalar/cargar/habilitar.


§227: resuelta E/S del contador del frontend. Eliminados count()/file_size/ifstream/JSONread
cada500ms. CountMirror conserva sólo un snapshot en memoria, alimentado por el puente KDE
existente desde effective_options() (opciones comunes + bwm/user). Sin preferencia/archivo
o watcher/daemon nuevo. Watch comparte Runtime con reconcile; debounce existente y reintento
cada2s si .so opcional instalado. Nunca cargar/habilitar por presencia del archivo.

Comando bwm-plasma-desktops-count N, parser canónico1–100, recibo JSONv1/valor/revisión.
Duplicados no aumentan revisión ni programan idle. No envía cero ante JSON parcial/error;
retiene último válido. Primera publicación espera dato; diagnostic countMirrorVersion=1 y
configuredCountSource=shared-bwm-bridge. Preflight sigue sólo lectura, requiere versión/copia
conocida, no envía ajustes. Recibo es aceptación de cache, no certificación visual o frescura.
Reducir contador conserva vivos/activos, aunque estén fuera de rango. Especiales/99 fuera.

Tests: emisor Python real→parser/recibo C++ real en transporte de ensayo, originales KDE
reciben3→7 y reducción conserva3/7 vivos; normal/arbitrado. Test de puente real con XDG temporal:
contador12, override9 intacto, reentrada y sin reload. CTest7/7 normal/ASan, Python R4 122 y
puente20; BREEZE_R4_COUNT_MIRROR_RESULTS.json. Módulo recompilado sin GNU UNIQUE, sin instalar/
cargar/autostart. Puente de sesión en ejecución no reiniciado, necesita reinicio/inicio de
sesión para adoptar fuente nueva. No ejecutar helper contra config real como parte de tests.

Ahora pendiente entrega/orden de arranque reales del frontend/puente en Hyprland, generaciones,
capacidades/entrada/render, autoridad/fallback diarios. No activar panel diario ni R5/R7.
La copia de count no autentica un escritor frente al mismo usuario con acceso al IPC. No
se presenta ese snapshot como otro ajuste, ni se amplía su propiedad a la skin. No hot load.

Límite entre skins: el watch KDE termina fuera de Breeze. El contador configurado del
proveedor puede conservar la última copia hasta reentrar, aunque su feed de workspaces
vivos continúe. Resolver esa entrega común entre skins antes de certificar integración
diaria; esta prueba acredita reentrada, no actualización continua de esa copia en Retro/default.


§228: implementada infraestructura de entrega entre skins. SharedSettingsRuntime.qml se
instancia UNA vez en shell.qml, fuera de panel loaders; no en Config.qml/Ajustes para evitar
copias. Requiere ready/count/skin/dispatcherCommand, sin importar Config por sí mismo.
Debounce200ms, Process asíncrono único, pending si cambia durante envío, retry validado de
recibo; errores/reintento5s, FailedToStart recuperado desde runningChanged (no exited).
IPC de sólo lectura sharedSettings status permite diagnóstico, no certificar operatividad.

Dispatcher común bwm_settings_hooks.py shared descubre hooks.sharedSettings sólo de skins
incluidas/revisadas. Manifiesto Breeze: native_workspaces.py, prerequisito hypr/plugins/
bwm-plasma-desktops.so, intervalo2s. No escribir rutas de Plasma en el lector/coordinador
común; no registrar scripts descargados al descubrir temas/widgets/skins. Instalar archivo
sólo arma entrega; no lo carga/habilita. Sin archivo no ejecuta adaptador/IPC ni mantiene
poll periódico. Instalación durante sesión inactiva requiere nuevo disparo/inicio; nunca hot load.

Auxiliar shared resuelve opciones/overrides según skin actual mediante API común; no
importa kde-config-bridge ni toca kwinrc fuera de Breeze. bridge_lock se comparte con KDE;
lock no bloqueante desde auxiliar, reconcile ya dentro. Retirado counts.tick del watch KDE:
no mantener ese watch al salir ni añadir demonio/watcher/thread. Sí hay un Timer Qt dentro
del shell para coordinación. Preferencia cuenta/usuario común conservada.

12 específicas (QML real offscreen, cinco escenarios + cadena real de procesos): default/
Retro/Breeze3/7/5 contra parser/recibo C++ de ensayo; también all9/Retro11. R4 134, puente20,
skins7; CTest7/7 normal/ASan. BREEZE_R4_SHARED_DELIVERY_RESULTS.json. C++ sin cambios/recompilación.
No instalar/cargar/autoiniciar módulo ni activar panel nativo. Fuente shell.qml ahora integrada;
puede recargarse automáticamente: no afirmar «sesión sin cambios» por no reiniciar manualmente.

Lectura de log posible, sin error de tipo del componente observado, pero no certifica carga.
Hyprctl version falla Couldn't open a socket(1); qs IPC UnsupportedSocketOperationError.
No eludir restricciones. Módulo sigue sin instalar y dispatcher real con config actual fue
noop/inactive/retry0 (sin IPC). Falta validar carga/entrega/arranque reales en Hyprland,
generaciones/capacidades/render/entrada y autoridad/fallback diarios. Sólo R4; no R5/R7.


R4 §229: test-taskdelegate/native-task-delegate-render prepara los dos widgets de tareas
KDE originales sobre Wayland privado + QQuickRenderControl/QImage sin superficie. No usar
proxies de roles offscreen como prueba nativa: TasksModel consulta WindowTasksModel estático.
Compila normal/ASan; ejecución nueva bloqueada ANTES de Qt por wl_client_create EPERM,
reproducido en suite anterior. Sólo3 suites sin esos clientes pasan normal/ASan; no afirmar
render validado ni CTest completo. Ver BREEZE_R4_TASK_DELEGATE_RESULTS.json y comando local en
BREEZE_R4_RESULTS.md §229. Sin producción/plugin/panel diario/reinicio/R5/R7.


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
