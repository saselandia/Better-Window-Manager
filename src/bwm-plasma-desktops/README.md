# Proveedor experimental de escritorios Plasma — R4

Este componente publica org_kde_plasma_virtual_desktop_management v4 en el display
Wayland existente de Hyprland. No inicia otro compositor, socket de sesión, plasmashell,
D-Bus KWin ni servidor de escritorio. Separa el núcleo de protocolo, la proyección de
workspaces BWM y una extensión opcional de Hyprland. Código propio GPL-2.0-or-later;
licencias de XML/generados y procedencia en ../../THIRD_PARTY_NOTICES.md.

Estado (§254–265): núcleo y consumidores KDE probados aislados y en Hyprland anidado;
extensión instalada y cargada mediante opt-in al iniciar la sesión real. El usuario confirma
ABI coincidente, arbitraje activo, contador común 10 y ausencia de errores. Filtro de tareas
aceptado por el usuario en MSI (§257); lectura medida LG/10 y MSI/1 aceptada en sesión (§259).
Ciclo de activación fallido en sesión (§261); doble acción de foco reproducida/corregida e
instalada atómicamente (§262, activationRoutingVersion=2). Ciclo real corregido LG/10 → MSI/1
validado por el usuario (§263): dos acciones aplicadas/observadas, sin fallo y pausa final.
Navegación real MSI/1 → MSI/3 → MSI/1 validada (§265), LG/10 conservado y sin fallos. Cierre
y autoridades/recuperación diarias siguen pendientes. No se selecciona el panel diario
ni se anuncia un pager o widget de tareas completo.

## Construcción y pruebas aisladas

```bash
cmake -S src/bwm-plasma-host -B build/bwm-plasma-host
cmake --build build/bwm-plasma-host -j4
ctest --test-dir build/bwm-plasma-host --output-on-failure
```

La regresión usa un socketpair heredado exclusivamente por los dos hijos de prueba,
WAYLAND_SOCKET soportado por Qt, raíces XDG temporales y D-Bus inexistente. El fixture
no escucha en una dirección ni puede representar superficies. Aloja los globals mínimos
compositor/shm/output/xdg_wm_base para inicializar Qt Wayland y el protocolo de escritorios.
No conecta al compositor del usuario. test-desktops usa VirtualDesktopInfo, TasksModel y
TaskFilterProxyModel instalados, más Instantiator/required display en QML. Comprueba roles
y objetos de delegado, sin dibujar ni certificar la barra. Las consultas cubren dos salidas
ficticias; no constituyen una matriz real de monitores.

El XML privado KDE se genera con wayland-scanner desde plasma-wayland-protocols 1.23.0
instalado; CMake fija su SHA256 porque admite cambios incompatibles sin cambiar versión.
El XML xdg-shell de wayland-protocols sólo se usa en el fixture. No se modifica KDE.

## Extensión de Hyprland: construcción y arranque opt-in

```bash
cmake -S src/bwm-plasma-desktops -B build/bwm-plasma-desktops -DBWM_BUILD_HYPRLAND_PLUGIN=ON
cmake --build build/bwm-plasma-desktops --target bwm-plasma-desktops -j3
```

El resultado queda en build/bwm-plasma-desktops/bwm-plasma-desktops.so. Tanto núcleo como
módulo se compilan con -fno-gnu-unique. No hay cambios del panel diario.
La guarda de inicialización compara el hash del Hyprland en ejecución con el de headers.
El opt-in plugin:bwm_plasma_desktops:enabled empieza en false. make install usa copia
temporal y rename atómico y se ejecutó antes del primer inicio real (§255).
No cargar/descargar en caliente ni sobrescribir un .so cargado. Revisar compatibilidad y
presencia de otro proveedor antes de una carga en un nuevo inicio de sesión.

autostart.sh carga/habilita sólo al iniciar Hyprland si se activó expresamente el opt-in:
`python3 ~/.config/hypr/skins/plasma/scripts/native-desktops.py enable` (siguiente login).
`disable` evita la carga en el siguiente login; `status` sólo consulta. La guarda contra
bucles desactiva el opt-in si el inicio anterior no alcanzó 60 segundos estables (§255).
El primer arranque real está confirmado; la barrera del auxiliar se probó aislada y anidada,
sin certificar todavía su frontend en la sesión del usuario. No habilitarla automáticamente
por el éxito de una prueba. El diagnóstico de hyprctl bwm-plasma-desktops, cuando esté cargada,
expone estado/contadores/capacidades; operationalVerified y liveSessionVerified siguen false.

## Autoridad y capacidades

- IDs normales BWM positivos en forma decimal, estables; fuera especiales y antiguo 99.
- Proyección de bar.workspaces.shown (1–100 válido) del config común, workspaces vivos y
  activos por salida. Nunca reduce/renumera workspaces reales al bajar el contador.
- Contador por copia en memoria desde el puente común, sin leer archivos en el frontend.
  Hasta recibir el primer valor válido no publica; ante errores conserva el último válido.
  No escribe archivos ni crea otra preferencia de layout (ver §227).
- Nombres vivos de Hyprland; índices son sólo posiciones de presentación. output_name es
  el nombre efímero del protocolo que ve QScreen, no una identidad persistida DP-N.
- Actualización por eventos coalescidos y un temporizador de reconciliación 500 ms; sin
  inotify adicional, hilos ni sondeos de procesos. Publica sólo cambios de snapshot.
- Activación diferida y validada por Config::Actions::changeWorkspace, la misma vía del
  dispatcher de Hyprland. No shell/exec. La cola tiene límite 32 y se descarta al desactivar.
- request_enter_output sólo usa un workspace ya materializado y asignado a esa salida;
  enfoca ese monitor mediante la acción estándar antes de activarlo. No mueve/swap de
  escritorios entre monitores ni invalida reglas comunes. Los demás casos se deniegan.
- Crear/quitar escritorios no está implementado: solicitudes denegadas y diagnóstico
  explícito. El protocolo no ofrece flags para ocultar esos controles en cualquier cliente;
  por ello no se certifican sus menús ni el pager completo. Falta la política/adaptación.
- La validación real de la barrera del auxiliar, navegación/wrapping por D-Bus, acciones de tareas restantes,
  especiales/filtros y negociación de ventanas permanecen pendientes de integración.

El test de protocolo permite activación entre salidas en su backend ficticio para verificar
el contrato v4. Eso NO acredita traslado entre salidas en la extensión real, que lo deniega.
Tampoco los contadores accepted/applied certifican resultado visual o un widget operativo.
No adquirir un flock ni esperar procesos desde el hilo del compositor: puede bloquear el
IPC que necesita el propietario del bloqueo. La retirada asíncrona se resuelve en §219;
la exclusión de todas las mutaciones entre gestores sigue fuera de ese contrato.

## Actualización de upstream

Comparar org-kde-plasma-virtual-desktop.xml completo, las fábricas/handlers de KWin y los
consumidores VirtualDesktopInfo, TaskFilterProxyModel y TasksModel del plasma-workspace
fijado. Revisar orden de eventos/done, versiones mínimas, vida de recursos, recreación de
IDs y semántica por salida antes de actualizar el hash. Repetir prueba nativa normal y
ASan. Para Hyprland revisar State::workspaceState/monitorState, FocusState, Config::Actions,
eventos, cleanup e identidad ABI. Compilar con el mismo compilador que el compositor.
Los efectos, scripts de layout y plugins de ventana son otros contratos; no se certifican
por descubrir el global. Arquitectura/evidencia en docs/BREEZE_R4_* del repositorio.

## Barrera por conexión (§219)

bwm-plasma-desktop-control-v1.xml es un contrato de integración propio, no un formato de
preferencias ni otro servidor. Usa el mismo wl_client de Qt y sólo controla activaciones
de esa conexión. Los eventos de lectura del protocolo KDE continúan. Las conexiones nacen
pausadas; para activar deben tener un propietario de control y enviar resume. Pausar o
destruir el propietario descarta su cola y mantiene esa conexión pausada. Una reconexión
no hereda autoridad de un wl_client con dirección reutilizada. Otros clientes no se pausan.

La cola (límite 32) vive ahora en DesktopProtocol, compartida por fixture y extensión real.
Una petición captura recurso + serial de vida + ID y se revalida antes de aplicar. Una
retirada de recurso o desconexión elimina su trabajo pendiente. Las acciones se ejecutan
en un idle del mismo event loop; pause sólo se confirma después de cancelar lo aún pendiente
y de terminar cualquier callback anterior. No flock, espera de proceso ni hilo bloqueado.
No se promete deshacer una acción que ya terminó antes de la pausa.

El auxiliar usa NativeDesktopControl y --native-desktops en un preview --follow-skin.
El launcher exige diagnóstico compatible del proveedor ya cargado/habilitado/disponible;
no lo habilita ni carga. El cliente requiere además confirmación Wayland real, con serial
correlacionado y plazo de 1 s. La revisión de control no se confirma mientras falte esa
respuesta o una acción local. Ante pérdida/indisponibilidad se suspenden colas locales y
se retiran vistas. Reanudar exige confirmación nueva. Un timeout no se convierte en éxito
por un ack tardío; una nueva revisión permite reintentar. La ausencia del proveedor no
impide retirar el auxiliar/salir de Breeze, pero impide entrar en el modo que lo requiere.

Pruebas: dos conexiones independientes, petición + pause en el mismo flush, conservación
del otro cliente, propietario destruido y rebind; RuntimeControl/PanelRuntime/cliente Qt con
pérdida, deshabilitación, reaparición y timeout. Sólo el fixture puede detener su event loop
mediante su pipe privado para simular un proveedor colgado; no es código de producción ni
se envían señales a procesos del usuario. Los controles no son una barrera de todos los
clientes ni serializan todas las operaciones de ventanas/workspaces de BWM. No certifican
menús, rendering, frontend real o takeover. Ver BREEZE_R4_DESKTOP_CONTROL_RESULTS.json.

## Asociación de registry: versión 2 del control (§223)

El interface bwm_plasma_desktop_control_v1 conserva su nombre y ofrece versión 2. Añade
el evento desktop_global con el nombre del management KDE visible para ese wl_client;
0 significa no visible. Requiere Wayland server >=1.22. El diagnóstico compilado anuncia
barrierProtocolVersion=2 y el launcher actual lo exige. Clientes v1 siguen recibiendo la
barrera anterior, sin el evento nuevo; no bastan para el auxiliar actual.

Los controles retirados quedan inertes hasta destroy/desconexión. Solicitudes que ya viajaban
son válidas pero no ejecutan trabajo ni reciben ack; no se envía invalid_object por esa
retirada. No autoriza unload del módulo: los handlers siguen perteneciendo a su código.

El cliente cuenta globals/asocia recursos en su conexión y evita usar proveedores ambiguos.
En §223 esta guarda aún no arbitraba en el servidor. §225 añade la coordinación descrita
abajo, con alcance limitado a los globals visibles; la aceptación del frontend/arranque
sigue pendiente. El módulo continúa compilado/desactivado, sin instalar/cargar/autoiniciar.

Las pruebas añaden controles duplicados, asociación falsa, inventario tardío y management KDE
duplicado. El SDK original pierde su lista después de retirar el duplicado; un proceso Qt
nuevo descubre los cuatro escritorios del fixture. El cliente bloquea hasta reiniciar sólo
el auxiliar. Se prueban también peticiones a controles retirados y compatibilidad v1 en dos
clientes. Fixture sin superficies, normal/ASan; evidencia BREEZE_R4_REGISTRY_RESULTS.json.

## Arbitraje previo en el servidor (§225)

DesktopProvider envuelve al core utilizado por plugin.cpp. Inicialmente disabled no publica
management, control ni claim. Un wl_client interno por socketpair observa el wl_display ya
existente mediante wl_registry/sync asíncronos. No usa WAYLAND_DISPLAY, no escucha en un
socket, no crea servidor/hilo y nunca hace wl_display_roundtrip en el hilo compositor.

Secuencia: inventario completo → sin proveedor previo → claim BWM → sync y elección del menor
ID visible → publicar el par inicialmente no disponible → sync y verificar globals propios →
available. Otro proveedor previo deja blocked y sin publicación propia; su retirada permite
intentar la elección si todavía no se había creado un claim. Dos proveedores BWM cooperantes
no deben publicar dos pares. El marcador bwm_plasma_desktop_provider_claim_v1 no tiene
peticiones/eventos; es sólo coordinación de registro, no configuración ni backend de Plasma.

Un proveedor ajeno posterior causa retirada propia al observar el conflicto. Ninguna API
pública utilizada impide a otro módulo ejecutar wl_global_create, y el filtro del compositor
puede ocultar globals al observador. Por eso el diagnóstico declara arbitrationScope:
observer-visible-globals. No sustituir wl_display_set_global_filter ni prometer exclusión
universal/autenticación. El auxiliar sigue verificando su propio registro y asociación.

Cada inventario/fence tiene plazo 1 s y sólo se guardan 128 globals relevantes. Fallo de E/S,
pérdida del peer, overflow o filtro que oculta el claim/par propio retiran la vía. Flush es
no bloqueante; WRITABLE se añade sólo ante EAGAIN. Sin llamadas a procesos, flock ni espera
sincrónica desde el módulo. Un estado de backend inválido nunca termina en available=true.

**Una generación por vida del módulo.** Después de crear un claim, desactivar/fallar/perder
la elección o detectar un conflicto retira para esa vida. providerRestartRequired=true pide
un FUTURO INICIO DE SESIÓN, nunca descarga/carga del módulo en caliente. No confundirlo con
el latch del consumidor de §223, que sólo pide un auxiliar nuevo. No hay reintento por cada
reconciliación de 500 ms. R4 no despliega todavía esta opción en los ajustes/arranque diarios.

DesktopProtocol::withdraw usa wl_global_remove y deja el core, globals y recursos KDE vivos
hasta teardown. Los controles retirados son inertes. Atiende binds ya ofrecidos y lecturas
pendientes del snapshot anterior, rechazando activaciones y sin ack de control. No publicar
un snapshot vacío para retirar: destruiría handles que aún pueden recibir requests. La vida
del módulo sigue importando: estos handlers impiden unload seguro con clientes conectados.

Regresión: native-desktop-provider-arbitration (14 escenarios C++ con servidor sólo de datos)
y native-desktop-arbitrated-kde-consumer (VirtualDesktopInfo C++/QML originales). Se añade a
los tests del host normal/ASan; sin conexión de sesión, superficies ni compositor alternativo.
Ver BREEZE_R4_PROVIDER_ARBITRATION_RESULTS.json. Al actualizar Wayland revisar get_name,
remove/destroy/late binds, propiedad de fds, cliente desconectado, flush/read/EAGAIN e integración
del event loop en sus fuentes primarias. Repetir elección simultánea, filtros, deadline,
solicitudes en vuelo, callback reentrante y consumidor KDE. No actualizar el protocolo privado
KDE ni quitar sus pins por una prueba del guard. Aceptación en Hyprland y más de una generación
siguen pendientes; esta compilación no autoriza instalar/cargar ni retirar el panel diario.

## Arranque y cierre del frontend (§226)

El constructor de DesktopProvider ya no crea el peer ni inicia el plazo: sólo snapshot
válido + opt-in programan un idle del loop existente. Estado waiting-for-event-loop hasta
ese momento, después inventory con plazo de 1 s. Si se cancela antes del idle, no arranca
ni consume la única generación. Esto evita un falso timeout durante inicialización lenta.
El diagnóstico añade observerStartup=deferred-event-loop; fallo al registrar el diagnóstico
aborta la inicialización antes de solicitar publicar. No añade hook de arranque automático.

La revisión primaria de Hyprland 0.56.2 confirma filterGlobals→SecurityContext: el peer
directo interno no está en la lista sandbox y puede ver los globals; las conexiones bajo
security-context mantienen el filtro de protocolos privilegiados (nuestros globals no están
en su whitelist). No tocar el filtro del compositor para cambiarlo. No es certificación de
sesión ni de todas las versiones/parches; repetir revisión al actualizar Hyprland.

Importante: cleanup de esa versión llama unloadAllPlugins ANTES de destruir clientes.
withdraw mantiene core/recursos vivos para peticiones en vuelo; el destructor definitivo
DEBE destruir todos los recursos del módulo. Controles retirados usan guarda withdrawn y
se registran aun sin propietario activo (límite 4096); recursos del claim registrados con
límite 256. Destruirlos antes de retornar de PLUGIN_EXIT impide callbacks o metadatos
apuntando a un .so descargado. La conservación con userdata=null después de destruir el
core no es suficiente. Los fixtures ahora retienen cores retirados hasta acabar los clientes.

Test-provider carga una biblioteca de ensayo del mismo proveedor/core con dlopen. Enlaza
los cuatro tipos de recursos y un control tardío, verifica que todos desaparecen al destruir
el proveedor, confirma dlclose real con RTLD_NOLOAD y sólo entonces destruye clientes. Dos
casos: activo/retirado. No despacha nuevas peticiones tras destruir el módulo: sigue prohibido
hot unload/load real. Sólo prueba este proveedor, no los otros plugins de Hyprland.

El test DSO es propio, no se instala ni se carga en Hyprland. libdl/CMAKE_DL_LIBS sólo en el
test, sin paquete de producción nuevo. CTest7/7 normal/ASan, 16 escenarios y Python R4 113;
BREEZE_R4_STARTUP_TEARDOWN_RESULTS.json. Sigue sin prueba física de arranque/logout o frontend.
Antes de integración diaria revisar además la lectura de config.json por refresh cada500ms,
la política de generaciones y las capacidades/resto de aceptación de R4. No seleccionar panel diario.

El preflight de --native-desktops exige providerLifecycleVersion=1 (entero, no booleano)
y observerStartup=deferred-event-loop, además de las guardas anteriores. Diagnósticos de
un módulo antiguo se rechazan antes de lanzar el auxiliar; sin instalar/cargar/habilitar.

## Contador común copiado por IPC (§227)

CountMirror recibe bwm-plasma-desktops-count N. No es una preferencia nueva ni un gestor de
workspaces; sólo el snapshot en memoria de bar.workspaces.shown. El puente existente resuelve
config + bwm/user/shell.jsonc con effective_options() y native_workspaces.py lo envía desde
ese proceso. El frontend ya no hace file_size/ifstream/parse JSON ni consulta HOME para ello.
Su timer de500ms sólo reconcilia estado del compositor y la copia aceptada.

El parser exige comando exacto y número canónico1–100 (no bool/float/argumentos extra). Recibo
JSON version1, accepted, configuredCount y revision. Valores idénticos no generan revisión
ni otro idle; inválidos no modifican cache. Cache aceptada se aplica en reconciliación; el
recibo no prueba cambio gráfico. Con enabled pero sin dato inicial no anuncia globals y el
diagnóstico expone awaiting-shared-workspace-count. Valores recibidos no crean workspaces.
Al reducir se conservan los vivos/activos, también fuera del rango; especiales/99 fuera.

El mismo watch de kde-config-bridge aporta debounce y reintento cada2s; reconcile reutiliza
ese Runtime, sin daemon/watcher/reload ni archivo adicional. Sólo intenta IPC con el .so
opcional instalado en la ruta estándar. No lo carga/habilita por estar instalado. El puente
lee fuera del compositor; errores/JSON parcial no envían cero ni borran estado. Efectivos sin
clave usan10 del modelo común; tipos/rangos inválidos se rechazan. Se conservan overrides y
claves desconocidas; reentrada en Breeze exporta el valor común otra vez. El watch en curso
necesita reiniciarse para cargar nuevo código; no se ha reiniciado como parte de esta fase.

Preflight --native-desktops exige countMirrorVersion=1/configuredCountAvailable=true. Sólo
lee, no envía el contador ni habilita el módulo. La cache conocida no certifica frescura
instantánea ni integridad del panel entero. La integración real de arranque/entrega, conexión
Hyprland y demás capacidades siguen pendientes; cero instalación/carga/autostart/takeover.

check-count-mirror.py conecta el emisor Python al parser/recibo C++ del core con transporte
privado; el cliente original VirtualDesktopInfo verifica cambios/reducción sin perder vivos
en los dos fixtures. Pruebas de puente real en XDG temporal verifican prioridad de texto,
reentrada, conservación y ausencia de reload. CTest7/7 normal/ASan y Python R4 122/puente20.
BREEZE_R4_COUNT_MIRROR_RESULTS.json. No añade paquetes de runtime ni modifica formatos KDE.

## Entrega del contador en las demás skins (§228)

La continuidad pasa del watch KDE a SharedSettingsRuntime en el shell común, una instancia
fuera de loaders de paneles. El dispatcher común descubre el adaptador por el manifiesto
incluido de Breeze, sin condiciones de skin en el núcleo. native_workspaces.py shared usa
las opciones comunes/usuario de la skin actual y el mismo lock/IPC, sin arrancar/importar
el puente KDE completo fuera de Breeze. KDE conserva el envío durante reconcile pero ya no
su sondeo periódico del contador. No nuevo demonio/watcher/thread; Timer Qt en el shell.

hooks.sharedSettings contiene script, requiresConfigFile e intervalMs. Sólo adaptadores
incluidos/revisados participan; paquetes descargados no registran código. Falta el .so:
no adaptador/IPC ni retry periódico. Instalado: arma datos y reintento2s, no carga/habilita
módulo ni promete backend operativo. Un cambio durante envío programa otra entrega, sin
solapar procesos. El prerequisito se reevalúa en inicio/disparos/reintentos armados, sin
FileView nuevo; instalar por primera vez sin suscripción requiere otro disparo o inicio.

Diagnóstico: qs -c ii ipc call sharedSettings status (sólo lectura). Pruebas Quickshell
reales offscreen y cadena QML→dispatcher→adaptador→recibo C++ de ensayo verifican default/
Retro/Breeze3/7/5 y prioridades del texto. No verifican IPC/visibilidad del plugin Hyprland
real. Fuente del shell integrada; autorecarga posible, no verificada: IPC sigue inaccesible
aquí. No reinicio forzado ni instalación/carga del módulo. BREEZE_R4_SHARED_DELIVERY_RESULTS.json.
Persisten arranque/entrega reales y autoridades/capacidades de R4 antes de seleccionar panel diario.

## Validación en Hyprland real anidado (§254)

`src/bwm-plasma-host/check-desktops-hyprland.py --module build/bwm-plasma-desktops/bwm-plasma-desktops.so
--test build/bwm-plasma-host/test-desktops-hyprland --report <json>` desde una terminal de la sesión
Hyprland. Arranca un Hyprland anidado desechable (ventana cliente en un workspace oculto), carga el
módulo sólo allí, lo habilita y ejecuta los consumidores KDE originales contra su frontend real;
termina el anidado y retira la regla temporal. Nunca carga, descarga ni habilita el módulo en el
compositor de la sesión. Corregida aquí la guarda de versión de PLUGIN_INIT (comparaba punteros).
Validado: activación en ambos sentidos, filtro de escritorio actual, contador en vivo, barrera de
pausa y rechazo de crear/quitar, con cliente normal y ASan. La carga al iniciar sesión sigue pendiente.

## Carga al iniciar sesión, opt-in (§255)

`config/hypr/skins/plasma/scripts/native-desktops.py enable|disable|status`. Con opt-in,
`autostart.sh` ejecuta `native-desktops.py startup` una vez al iniciar Hyprland: comprueba versión,
carga, habilita, deja la marca de sesión y publica el contador; guarda contra bucles de fallo
(si el inicio anterior no llegó a 60 s estables, se desactiva solo y avisa). Instalar con
`make install` mediante temporal + mv atómico: el inodo cargado queda intacto; el módulo
corregido se adopta al siguiente login, nunca recargándolo en caliente. Prueba de la ruta de inicio:
`check-desktops-hyprland.py --via-startup ...` en el Hyprland anidado.

## Diagnóstico de la sesión sin acciones (§258)

```bash
python3 /mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/check-desktops-session.py
```

Compara el inventario proyectado y los escritorios activos por salida con VirtualDesktopInfo
original, por nombre efímero y geometría. Asociación de proveedor verificada, sin reanudar
la conexión (serial 0), crear ventanas/paneles, activar escritorios ni cargar/habilitar el
módulo. Raíces XDG temporales; puede coexistir con el preview. Descripción única con BwmOutput,
geometría lógica del gestor común y lecturas antes/después coincidentes. Ante cambios durante
la medición o ambigüedad, repetir con pantallas/workspaces estables; no elegir una salida
arbitraria. No certifica activación ni navegación, cierre de sesión o panel diario.

## Ensayo explícito de activación por salida (§260)

```bash
python3 /mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/check-desktops-activation.py --focus-cycle
```

Pide enfocar los escritorios ya visibles de otras salidas y volver a la inicial mediante
VirtualDesktopInfo.requestActivateOnScreen. Cambia brevemente el foco. No crea escritorios ni
reubica/cambia qué escritorio muestra cada pantalla. Requiere Breeze y 2–8 salidas distintas;
bloqueos existentes de skin/acciones impiden solapar cambios. Rechaza especiales visibles
antes/después. Resume y pause de la misma
conexión, lectura por paso y deltas exactos del proveedor; si falla no aplica acciones de
respaldo para recuperar un foco que podría haberse quedado obsoleto. Sigue siendo un ensayo,
sin certificar navegación entre escritorios no visibles, foco de ventana o panel diario.

Primer intento real fallido (§261). Leer contadores/motivo actuales sin repetir el ciclo:

```bash
python3 /mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/check-desktops-activation.py --diagnose-last
```

El diagnóstico conserva datos del hijo/proveedor incluso al fallar. No interpretar
restoredInitialOutput=true como prueba de haber visitado otra salida: sólo es estado final.
El comando corto native-desktops.py no está en PATH; para consultar el arranque usar
`python3 ~/.config/hypr/skins/plasma/scripts/native-desktops.py status`.

Corrección §262: un workspace ya activo requiere sólo Actions::focusMonitor; añadir
changeWorkspace al mismo workspace puede devolver el foco al puntero con destino vacío
y no_warps=true. Para uno inactivo, changeWorkspace por objeto conserva su propio flujo
entre salidas. check-activation-routing.py ejecuta cuerpos originales 0.56.2 con andamiaje
de datos y el applyExact actual (48 casos normal/ASan); no certifica el compositor real.
El diagnóstico expone activationRoutingVersion=2 y el ciclo exige esa generación cargada.

## Ensayo de workspace no visible (§264)

```bash
python3 /mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/check-desktops-activation.py --workspace-cycle
```

Visita un ID configurado no materializado vinculado explícitamente al monitor actual y
vuelve al original. Descarta persistencia/comandos al crearlo, reglas ambiguas y workspaces
ya existentes, aunque estén vacíos. Usa requestActivate original, con lectura global y por
salida, manteniendo las demás salidas y comprobando recibos/pausa. Puede materializar un ID
ya anunciado; no añade preferencias ni usa requestCreateDesktop/remove. Un cambio externo
o fallo invalida el ensayo y no dispara recuperaciones de foco obsoletas. No requiere plugin
nuevo ni otro login. Aceptado en sesión (§265): MSI/1 → MSI/3 → MSI/1, LG/10 conservado,
dos acciones aplicadas/observadas sin fallos, asignaciones finales y pausa confirmadas.
No certifica relocalización entre salidas, escritorios ocupados, foco de app o panel diario.
