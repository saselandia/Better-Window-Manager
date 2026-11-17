# Breeze II: fidelidad a Plasma y corrección del port existente

Fecha: 2026-11-12. Base revisada: `2a4ae3c`.

Este es el **nuevo plan activo de mejoras de Breeze (Kde plasma)**. No vuelve a implementar
F0–F13: parte de lo que ya funciona. El plan histórico sigue en `BREEZE_PLAN.md`, porque hay
código y documentación que citan sus fases. Las nuevas fases se llaman **R0–R9**.

Cada bloque es un prompt para una sesión nueva. Ejecutarlos en orden; el objetivo de cada
sesión es implementar y comprobar su fase, salvo R0, que es una auditoría. No ejecutar todas
las fases con un único prompt ni confundir «compila» con «es igual a Plasma».

## 1. Resultado que se busca

1. El mismo workspace especial de BWM en las tres skins: Alt+S, enviar ventanas, activarlas,
   ocultarlas y volver; sin ventanas fantasma detrás del escritorio normal.
2. **La aplicación real de Preferencias del sistema de KDE**, con sus KCM reales y las opciones
   de BWM integradas como módulos. La aplicación actual es una adaptación y no cumple este objetivo.
3. El modo de edición original de Plasma: escritorio, panel, controles de geometría, asas,
   acciones de widgets y sus ventanas de configuración; aspecto e interacción del original.
4. Compatibilidad con las opciones que realmente aporten paquetes de Plasma instalados,
   descubiertas desde sus metadatos, esquemas y páginas QML, no una lista fija de BWM.
5. Sombras de la decoración activa y animaciones iguales a Plasma predeterminado donde sea
   técnicamente posible sobre Hyprland, con preferencias que tengan efecto real.
6. Revisar a fondo el resto de la skin y cerrar los huecos de uso diario y las pruebas pendientes.

**Qué significa «idéntico».** Usar el código/interfaz original cuando exista; comparar con una
referencia de la misma versión, configuración y escala. Una aproximación no se declara idéntica.
Hyprland sigue siendo el único compositor: no ejecutar KWin ni un segundo escritorio para
ocultar límites del port. Si un efecto exige capacidades ausentes, investigar una implementación
segura antes de descartarlo y documentar exactamente la diferencia que quede.

## 2. Revisión inicial: hechos, carencias e hipótesis

Esta revisión es de código y documentación, **no una nueva prueba de la sesión gráfica**.
Las versiones Plasma 6.7.5 / Frameworks 6.29.0 proceden de la referencia del repo; R0 debe
confirmar las instaladas y fijar los commits exactos. No usar `master` como referencia visual.

| Área | Evidencia revisada | Mejora necesaria |
| :--- | :--- | :--- |
| Edición del panel | `modules/plasma/panel/PanelEditor.qml`: popup propio, seis widgets fijos, casillas y flechas | Portar el modo de edición completo y sus contratos; no retocar este formulario para que se parezca |
| Motor de widgets | README de `panel`, `tray` y `applets`: no se instancia un anfitrión real de plasmoides arbitrarios | Resolver Corona/Containment/Applet/PlasmoidItem, configuración y acciones antes de prometer complementos externos |
| Opciones de complementos | Bandeja con lista explícita; páginas originales de cada plasmoide sin alojar | Descubrimiento por paquete, configuración por instancia y páginas nativas; incluir opciones aportadas por terceros |
| Ajustes | `open-settings.sh` ejecuta `qs -p plasmaSettings.qml`; `Catalog.js` mantiene un catálogo propio | Migrar a `systemsettings` real; el ejecutable existe en el equipo inspeccionado, pendiente probarlo e integrar módulos BWM |
| Páginas de Ajustes | Páginas compartidas BWM y sustitutos reducidos de comportamiento; QWidget no incrustado en el host actual | KCM nativos, incluidos QWidget, con adaptadores efectivos a BWM; páginas BWM con estilo KDE |
| Animaciones | `skins/plasma/hypr/animations.lua` declara curvas `md3_*`, `popin 60%`; `kwin.lua` repite esa tabla | Sustituir por semántica, tiempos y curvas de Plasma; eliminar las dos fuentes de verdad |
| Control de animación | Puente exporta `AnimationDurationFactor`; `kwin.lua` sólo reaplica velocidades si factor != 1 | Probar 1 → otro valor → 1, cero y reinicio; configuración completa de los efectos implementados |
| Sombras SSD | `bwm-decorator` ya transmite `DecorationShadow`; `barRemote.cpp` compone nueve trozos con `CBreezeShadow` | Auditar render, activación, escala, geometría, daños y orden; conservar el origen KDE en vez de añadir una sombra genérica |
| Sombras CSD | `modules/appearance.lua` apaga la sombra genérica en Breeze para evitar halos; negociación CSD/SSD ya existe | Identificar quién aporta cada sombra; evitar tanto ventanas sin profundidad como doble sombra y recortes |
| Alt+S | `keybinds.json` y generador apuntan a `magic`; mover usa `special:magic` | No hay evidencia estática de un atajo distinto por skin: verificar estado efectivo, reglas, activación y cambios de skin |
| Activación de tareas | `TasksModel.activate()` → `kwin-window.py focus`: focus, bring_to_top y alter_zorder; sin rama explícita para especiales | Hipótesis para investigar, no causa confirmada del fallo reportado; resolver estado del workspace antes de elevar |
| Modelos de escritorios | `HyprlandData.qml` limita su lista de workspaces a 1–100; minimizar usa `special:minimized` | Separar escritorios normales, Magic y almacenamiento de minimizadas sin romper consumidores comunes |
| Panel/tareas | Ports y medidas corregidos recientemente; sigue pendiente funcionalidad del task manager | Progreso/insignias, multimedia en miniaturas, filtros, rueda, grupos, menús y configuración original |
| Reloj y bandeja | Opciones nativas presentes en datos pero no todas en interfaz | Configuración nativa, zonas horarias, agenda y acciones; conservar las correcciones visuales recientes |
| Applets | Bluetooth, avisos, portapapeles y energía documentan ports reducidos | Evaluar OBEX, respuestas en línea, trabajos KIO, agenda, portapapeles y perfiles; priorizar sin duplicar servicios |
| Ventanas | F10 y CSD conservan pruebas manuales pendientes; hubo crash de propiedad de la sombra (§3.150–151) | Validación del plugin realmente cargado, escalas, bordes interiores, CSD/SSD y restauración completa |
| Sesión | F12/F13 tienen límites de bloqueo, temas privados, OSD y servicios | Pruebas funcionales y de cambio de skin, no sólo carga de QML |

Un **estilo de Plasma SVG** normalmente aporta aspecto y métricas; no se deben inventar opciones
que no declare. Un **plasmoide**, decoración o plugin sí puede aportar configuración propia.
Un **tema global** puede incluir componentes y disposición. Hay que descubrir cada contrato
real: no todos los paquetes tienen opciones ni todos son el mismo tipo de complemento.

## 3. Reglas comunes de ejecución

Todos los prompts incorporan esta sección al pedir leer el plan.

- Leer `AGENTS.md` entero y el estado vigente en `BWM_CONTEXT.md`, `BREEZE_ARCH.md`,
  `BREEZE_F13_RESULTS.md`, `BREEZE_PANEL_FIXES.md` y las comprobaciones específicas del área.
  Inspeccionar Git antes de editar y respetar cambios de otras sesiones.
- Trabajo modular en `config/quickshell/ii/modules/plasma/`, `config/hypr/skins/plasma/` y
  auxiliares `src/`. El workspace especial es común: su corrección debe servir a las tres skins.
- Código original antes que réplicas artesanales. Leer fuentes de la versión instalada,
  fijar etiqueta/commit por componente, conservar licencias y registrar parches BWM y procedencia.
  Las copias upstream de `/tmp` son reutilizables sólo después de verificar su versión.
- No ejecutar KWin, plasmashell, una sesión Plasma ni servidores duplicados de notificaciones,
  SNI, polkit, energía o atajos en la sesión real. No apropiarse de nombres D-Bus de KDE con
  implementaciones parciales que engañen a otras aplicaciones.
- El usuario permite instalar dependencias necesarias: investigar y preparar los cambios;
  las operaciones con sudo las ejecuta él, con comando exacto basado en Portage. No instalar
  todo Plasma sin determinar el conjunto requerido. Declarar dependencias y regenerar su tabla.
- No escribir `~/.config/bwm/user/*` ni modificar texto de configuración del usuario.
  Respetar claves comunes, ajustes por skin, precedencia local/kdedefaults y preferencias ajenas.
- Plugins: `-fno-gnu-unique`, instalar sólo con `make install`, sin unload/load en caliente.
  Probar en compositor anidado desechable si está disponible. Instalar no demuestra que la
  sesión use ese binario: anotar versión cargada y qué exige próximo inicio de sesión.
- Nunca un segundo `qs -c ii`. Ensayos en archivos separados, sin acciones peligrosas;
  reinicios de mantenimiento con el gestor. No cambiar de skin, mover ventanas del usuario ni
  cerrar su sesión sólo para obtener una captura. Usar ventanas desechables y restaurar estado.
- No ejecutar scripts de disposición de temas para «ver qué hacen» sobre la sesión del usuario:
  son código. Estudiar el contrato real y ensayar en entorno aislado antes de soportarlos.
- Pruebas específicas de comportamiento y regresión según el cambio. Las pruebas opcionales
  omitidas no cuentan como aprobadas. QML: prueba de carga e interacción; C++: protocolo,
  tiempos de vida, compositor anidado y después prueba de sesión cuando corresponda.
- Validar sintaxis/configuración y logs cuando se modifique runtime y las herramientas estén
  disponibles. No exigir una prueba gráfica o Hyprland para una fase sólo documental.
- Cada fase termina con un informe `docs/BREEZE_R<n>_RESULTS.md`: archivos, pruebas ejecutadas,
  límites, diferencias con upstream, tareas pendientes y rollback. Actualizar §2 y añadir sección
  a §3 de `BWM_CONTEXT.md` cuando cambie el estado; AGENTS/CLAUDE idénticos si se modifican.
  Actualizar estado de este plan. No hacer commit/push salvo petición explícita; si se pide commit,
  revisar sólo los archivos propios y añadir coautoría. No subir compatibilidad estimada sin evidencia.

## 4. Orden y nivel de razonamiento

Usar **high** para arquitectura, C++, protocolos, estado de ventanas y sincronización. **medium**
para portar interfaces sobre contratos ya probados y pulir funciones delimitadas. No hace falta
poner high a toda la sesión por incluir una comparación visual.

| Fase | Trabajo | Esfuerzo | Dependencia | Reinicio de sesión |
| :--- | :--- | :--- | :--- | :--- |
| R0 | Auditoría y referencia reproducible | **high** | Ninguna | No |
| R1 | Magic/Alt+S y activación común | **high** | R0 | Sólo si cambia plugin |
| R2 | System Settings real y KCM BWM | **high** | R1 | No previsto |
| R3 | Ajustes KDE efectivos y opciones de plugins | **high** | R2 | Sólo si cambia plugin |
| R4 | Anfitrión de plasmoides/configuración/extensiones | **high** | R3 | Sólo si cambia plugin |
| R5 | Modo de edición original completo | **medium** | R4; si falta contrato, volver a R4 | No previsto |
| R6 | Sombras y profundidad nativas | **high** | R5 | Si cambia `breezebars` |
| R7 | Animaciones Plasma y sus preferencias | **high** | R6 y KCM de R2–R3 | Si exige plugin |
| R8 | Cerrar mejoras de uso diario de la auditoría | **medium** | R7 | Según corrección |
| R9 | Comparación e integración final | **high** | R8 | Probar tras cargar binarios finales |

Si una fase crece demasiado, dividirla por entregables manteniendo sus puertas de aceptación.
Las fases se ejecutan de forma secuencial; no trabajar simultáneamente en el plugin o el puente.
Estado al 2026-11-12 tras la primera ejecución:

- **R0 entregada:** auditoría actualizada, contratos upstream y 26 huellas en
  BREEZE_R0_REFERENCE.json. Protocolo BREEZE_R0_REFERENCE.md preparado según la alternativa
  del prompt para referencia inaccesible; mediciones gráficas y estado vivo siguen pendientes.
  Resultado y siguiente prompt en BREEZE_R0_RESULTS.md.
- **R1:** controlador común, origen especial y dock Retro integrados con pruebas aisladas;
  destino explícito cerrado ya no actúa sobre otra ventana. Smoke real ejecutado por el usuario
  en Hyprland 0.56.2 aprobado (Magic, foco, restauración y PID). Falta aceptación visual,
  modelo completo del dock y matriz en sesión de las tres skins. Ver BREEZE_R1_RESULTS.md.
- **R2:** primer KCM real compilado, probado y descubierto por systemsettings; migración parcial.
- **Incidente posterior:** modo seguro por SIGSEGV en captura de ventanas. Contención y límites
  en BREEZE_RECOVERY.md; miniaturas Breeze desactivadas, veto de sombras restaurado.
- **R6 (revertida por contención):** se había adelantado la eliminación del veto global identificado por R0,
  independiente del anfitrión de R4/R5; resto de la fase pendiente.
- **R3 parcial:** ocho adaptadores KCModule nativos, perfil KAuthorized del anfitrión,
  contrato por clave/APIs y R7, retry del puente y descubrimiento de decoraciones/terceros.
  Pruebas aisladas y opción Breeze instalada con render comprobadas. Falta sesión real,
  equivalencias completas y opción específica de tercero; ver BREEZE_R3_RESULTS.md.
- **R4: criterios originales cumplidos (2026-11-14).** Puerta superada con widgets elegidos por la
  tienda KDE, instalados/retirados con el proveedor nativo y una opción propia guardada también en
  la sesión Hyprland (BREEZE_R4_KNS_RESULTS.json). Pendiente fuera de la puerta: panel diario,
  backends, otras escalas/bordes/skins. Historial:
- **R4 (historial):** auxiliar con popup, diálogo, acciones y catálogo vivo probado
  en QtTest/ASan. Adaptador LayerShellQt y staging de datos nativos con lectura en otro
  proceso añadidos (2026-11-13). plasma-desktop instalado: org.kde.panel/QML original,
  AppletOrder y configuración desde su QAction probados; datos de cinco widgets en dos paneles.
  Registro pre-superficie de Dialog propios y geometría Qt añadidos, probados offscreen/ASan.
  Configuración con claves compartidas entre categorías sincronizada en memoria; páginas
  estables durante cambios de controles, conflicto/límites y lectura en otro proceso probados.
  Páginas por módulo QML y propiedades required antes de completar admitidas; fábrica común
  para diálogo/probe/ejercicio, errores explícitos y reapertura probados en QtTest/ASan.
  Marco Panel.qml original instalado alojado por ContainmentView; SVG/temas, bordes, flotación,
  dimensiones y NoBackground probados con readback offscreen. Falta su aceptación Wayland.
  Migración de borde/orientación corregida: cuatro bordes y fallback bar.bottom comprobados
  con staging, QML original y lectura posterior; archivo fuente preservado (2026-11-14).
  Seis preferencias del marco persisten ahora en plasmashellrc nativo, con kdedefaults,
  bloqueos/conflictos, efecto en la vista y lectura de dos paneles en otro proceso probados.
  Staging migra ahora grosor/flag de flotación/enum de opacidad al archivo KDE separado,
  con lectura/render del marco original; políticas sin adaptador quedan explícitas en el informe.
  PanelRuntime coordina vistas por descripción de salida/skin, conserva instancias ante
  retirada/hotplug y rechaza ambigüedad. Pruebas Qt offscreen y reapertura con otros índices/
  conectores pasan; hook diario, autoridad de bindings y aceptación real siguen pendientes.
  Hook común before/after conectado a una previsualización registrada explícitamente;
  dispatcher→publicador→Qt y CLI/envoltorio con unicidad, parada y Ctrl+C probados. Sin
  registro no actúa; sustitución diaria, perfil persistente y aceptación Hyprland pendientes.
  Perfil nativo de ensayo conservado entre procesos añadido: bindings separados, archivos
  completos, checkpoints con hashes y restauración en otra generación/ruta. Dos reaperturas
  del CLI/envoltorio y edición/lectura nueva normal/ASan pasan; limitado a raíces temporales.
  Exportación explícita a la autoridad XDG de estado añadida: conserva estado seleccionado e
  historial, sin sobrescribir fuente/destino existente. Fixture fuera de /tmp eliminado origen
  y reapertura/restore del destino pasan; sin perfil real ni activación diaria del usuario.
  Consulta status del auxiliar exige confirmación nueva y distingue carga/exposición/frame
  de Qt de sustitución diaria. Errores/pérdida de salida invalidan disponibilidad; el contrato
  de diagnóstico no autoriza retirar el panel existente ni selecciona un perfil diario.
  Modo de ensayo --native-policy añadido: panelVisibility 0/3 consume formatos KDE y pide/
  retira reservas mediante LayerShellQt; un panel por salida, cuatro bordes y persistencia
  probados aislados. La reserva aplicada por Hyprland y la coexistencia/disposición de varios
  paneles siguen pendientes; no se declara sustitución del panel diario.
  Diagnóstico r4-session-check.py disponible para ejecutar desde terminal local: consultas
  acotadas y filtradas, sin reinicios/dispatch. Aquí confirma sockets presentes/propios e IPC
  denegado; elevación rechazada por política del ejecutor. No declara validación gráfica.
  Usuario confirma acceso desde terminal local: dos salidas con reserva inferior 44 px y
  sin ensayo activo. r4-reservation-smoke.py prepara medición temporal antes/durante/después,
  con cierre automático; pendiente de ejecución local y posterior prueba de maximizado.
  Primer ensayo local falla por output-unavailable, con auxiliar activo y limpieza/44 px
  originales confirmados. Matcher ampliado para descripción completa con serie añadida
  cuando Qt Wayland no aporta serie, sólo fabricante/modelo únicos; inventario Qt añadido.
  Pendiente repetir localmente: no se presenta esta corrección como reservas ya validadas.
  Segundo informe local confirma Qt Wayland/MSI con fabricante «Co., Ltd.» frente a
  «Co. Ltd.» en Hyprland. Matcher corrige comas sólo en fabricante con regresión exacta;
  resto de identidad/unicidad conservados. Reservas 44 px originales y limpieza confirmadas;
  delta real sigue pendiente de repetir el ensayo.
  Ensayo local posterior supera el delta: MSI inferior 44→92→44 px, capa nativa 640×48,
  LG inalterado y cierre/registro restaurados. Evidencia de sesión conservada; aceptación
  limitada a ese monitor/borde/escala 1. Maximizado y cierre completo de R4 siguen pendientes.
  Preparado --maximize: ventana Qt propia, gestor BWM con PID/clase/dirección verificados,
  marco con autoridad de decoración, medición con/sin panel y reajuste automático separado.
  Regresiones aisladas pasan; nueva medición real todavía pendiente de ejecución local.
  Primera ejecución de --maximize encuentra error de orden de argumentos to-screen en el
  runner; corregido y probado contra argparse real. Panel/limpieza vuelven a pasar; ventana
  aún sin medir. Errores detallados y resultados parciales independientes añadidos.
  Ensayo posterior valida marco explícito con/sin panel en MSI escala 1, barra de 28 px
  incluida. Reajuste automático al retirar panel falla: conserva altura menor y deja 48 px
  sin usar. Adición previa aún no ensayada; R4 no se cierra por el éxito del maximizado nuevo.
  Seguimiento automático implementado en el puente existente, sin restaurar/maximizar de
  nuevo ni alterar el estado de restauración: bordes reales, ejes BWM, Force KDE y opt-outs.
  159 tests Python pasan. Ensayo ampliado a aparición/retirada sobre ventana ya maximizada;
  --refresh-area-watcher carga el código nuevo y espera baseline fresco. Usuario ejecuta
  el ensayo y valida ambos sentidos en MSI inferior escala 1/giro 0: altura 1396→1348→1396,
  reserva 44→92→44 y limpieza correctas. BREEZE_R4_AREA_SESSION_RESULTS.json conserva el
  informe. El fallo dinámico queda resuelto para ese caso; otros casos e integración diaria
  siguen pendientes y no se habilita sustitución del panel diario.
  API nativa de altas/bajas/reordenación y acciones dinámicas/submenús probada con persistencia
  y posiciones en otro proceso; QObject disponible dentro del auxiliar, sin activar el panel diario.
  Primera prueba en la sesión Hyprland (2026-11-13): posiciones de Qt Wayland, foco del
  panel y Dialog no interactivos corregidos; menú y avatar de Andromeda bien colocados en los
  dos monitores; cierre al pulsar fuera con hyprland_focus_grab_v1. Pendientes de sesión:
  escala fraccionaria, otros bordes en Wayland, desenfoque y aceptación del marco nativo.
  Faltan backend, otros tipos/creación tardía de ventanas, resto de aceptación Wayland,
  migración completa/activación del panel, descarga KNS y casos bloqueados de configuración.
  Ver BREEZE_R4_RESULTS.md/BREEZE_R4_ARCH.md; no se sustituye el panel activo.
- **R5 y R7–R9:** pendientes. No se declara ninguna equivalencia visual nueva.

Informes individuales BREEZE_R0/R1/R2/R6_RESULTS.md. El sandbox de esta ejecución no permite
acceso a los sockets Hyprland/Wayland/D-Bus; las verificaciones de sesión quedan para mañana.

Inventario por instancia para la integración diaria añadido (§211): estado fresco del
panel expone dependencias y bloqueos, sin certificar backends ni activar takeover.
Evidencia: BREEZE_R4_BACKEND_INVENTORY_RESULTS.json.

Adaptador KWindowSystem experimental implementado (§212), sólo en el auxiliar y con opt-in:
controlador KDE original → gestor común BWM, probado con IPC ficticio normal/ASan. Faltan
sesión real, acción secundaria TaskManager, efectos Peek e integración diaria. No aumenta
operationalVerified ni replacementReady. BREEZE_R4_DESKTOP_ADAPTER_RESULTS.json.

Usuario confirma ciclo de clics nativo minimizar/restaurar en Hyprland (§214), con evidencia
manual en BREEZE_R4_DESKTOP_SESSION_RESULTS.json. No mide geometría/foco ni certifica sombras,
TaskManager/Peek o sustitución diaria.

Continuación R4 §216: las dos entradas nativas comparten bloqueo acotado con revalidación
tras la espera; retirada confirmada sólo después de la mutación en curso, colas descartadas
y reanudación probadas. Ver BREEZE_R4_NATIVE_TRANSACTIONS_RESULTS.json. No sincroniza aún
los llamadores diarios. VirtualDesktopInfo carece de factoría pública; queda pendiente una
integración coherente de sus consumidores C++/QML, igual que menús y aceptación Wayland.

Continuación R4 §218: protocolo nativo de escritorios implementado y probado con los
consumidores KDE C++/QML originales en Wayland aislado, incluidos filtro, orden inicial y
roles de modelo. Frontend Hyprland separado compilado/desactivado y sin despliegue/carga.
BREEZE_R4_NATIVE_DESKTOPS_RESULTS.json: 4/4 CTest normal/ASan. Falta validar frontend,
coordinar retirada, menús/acciones/capacidades y sesión real antes de activar el panel.

Continuación R4 §219: barrera por conexión Wayland entre proveedor/auxiliar, cola compartida
real y confirmación asíncrona antes de retirar, con pérdida/reconexión/timeout probados.
Preflight --native-desktops sólo de lectura y handshake real, sin carga/despliegue de plugin.
BREEZE_R4_DESKTOP_CONTROL_RESULTS.json: 5/5 CTest normal/ASan. Falta aceptación del frontend
en sesión, menús/capacidades y autoridades diarias; sin certificar widget entero/takeover.

Continuación R4 §220: el menú TaskManager original conserva sus handlers/bindings; capacidades
BWM deshabilitan encima/debajo/excluir captura sin backend. Individual/grupo y retirada pasan
normal/ASan; CTest 5/5 y Python R4 105/manifiestos7. BREEZE_R4_TASK_MENU_RESULTS.json conserva
avisos de roles offscreen: no acredita Task.qml pintado o menú Wayland. Siguen pendientes
aceptación del frontend/proveedor, resto de capacidades y autoridad/fallback del panel diario.

Continuación R4 §221: pantalla completa del TaskManager original conectada al gestor BWM
con estado deseado, capacidad por ventana y recibo con lectura de modo interno. Individual/
grupo y on/on/off pasan con IPC/Lua simulados normal/ASan; CTest 5/5, Python R4 113 y
regresión ventanas14/minimizar7/skins7. BREEZE_R4_FULLSCREEN_RESULTS.json. Sin prueba física
de fullscreen/restauración o pintado de Task.qml; R4 sigue abierta por integración/aceptación.

Continuación R4 §222: las fichas de aplicaciones del modelo nativo siguen la base KSycoca
real, con invalidación agrupada y resolución diferida. Actualizar/quitar/reinstalar .desktop
refresca dos fuentes conservando identidad; prueba aislada normal/ASan y regresión 5/5,
Python R4 113/skins7. BREEZE_R4_TASK_METADATA_RESULTS.json incluye el fallo previo. No equivale
a render de Task.qml o catálogo de plasmoides; integración/aceptación de sesión siguen pendientes.

Continuación R4 §223: registro Wayland único y asociación declarada del proveedor antes de
resume; control BWM v2 y binding explícito por ID. Conflictos permiten retirar; duplicar KDE
exige proceso nuevo del auxiliar (VDI viejo pierde lista, nuevo ve cuatro). Controles retirados
inertes, timeout/revisión y visibilidad Qt probados. CTest 5/5 normal/ASan, Qt Wayland7/7,
Python R4 113/skins7. BREEZE_R4_REGISTRY_RESULTS.json. Arbitraje de servidor, frontend/arranque,
capacidades y aceptación de sesión siguen pendientes; no despliegue o takeover.

Continuación R4 §225: frontend sin globals cuando está inicialmente desactivado. Inventario,
elección entre proveedores BWM y publicación comprobada son asíncronos; conflictos visibles
y snapshots inválidos retiran sin destruir recursos en vuelo. CTest7/7 normal/ASan, 14 casos
C++, consumidor KDE original y Python R4 113/skins7. BREEZE_R4_PROVIDER_ARBITRATION_RESULTS.json.
Alcance de observador visible, una generación por vida del módulo; futura sesión para recuperar,
nunca hot unload. Sin despliegue: frontend/arranque real, capacidades y autoridades siguen pendientes.

Continuación R4 §226: el observer/deadline nace en idle bajo demanda, sin falso timeout antes
del primer dispatch. Cierre definitivo destruye controles/claim antes de descargar el módulo;
Hyprland descarga plugins antes de destruir clientes. Un DSO de prueba del proveedor confirma
descarga real y cero recursos propios, activo/retirado. CTest7/7 normal/ASan, 16 escenarios y
Python R4 113. BREEZE_R4_STARTUP_TEARDOWN_RESULTS.json. No certifica arranque/logout real ni
permite hot unload. Frontend, E/S del contador, generaciones y aceptación diaria pendientes.

Continuación R4 §227: contador común efectivo enviado por el puente existente a CountMirror
en memoria; sin leer JSON desde el frontend, nueva preferencia, daemon o reload. Primera
publicación espera dato y preflight sólo lee versión/copia conocida. Reducción conserva vivos/
activos. CTest7/7 normal/ASan, Python R4 122/puente20; BREEZE_R4_COUNT_MIRROR_RESULTS.json.
Pendientes entrega/arranque y aceptación reales, generaciones/capacidades/autoridad diarias.

Continuación R4 §228: entrega común desde una instancia en shell.qml, fuera de loaders de
skins/paneles. Manifiesto de adaptador incluido + dispatcher común; opciones actuales/usuario
sin mantener watch KDE fuera de Breeze. Un proceso, debounce/retry, sin daemon/watcher nuevo.
Pruebas Quickshell offscreen y cadena real de procesos default/Retro/Breeze3/7/5 con recibo
C++ de ensayo. R4 134/puente20/skins7 y CTest7/7 normal/ASan. BREEZE_R4_SHARED_DELIVERY_RESULTS.json.
Fuente shell integrada/autorecarga posible; carga no verificada por IPC inaccesible. Sin
plugin instalado/cargado ni panel nativo. Persisten validación real y aceptación diaria.



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

## 5. Prompts listos para pegar

Continuación R4 §215 (2026-11-15): fuente BWM opt-in dentro de WindowTasksModel original,
sin parchear KDE; acciones comunes, índices persistentes y dos modelos nativos probados con
IPC simulado normal/ASan. Ver BREEZE_R4_TASK_SOURCE_RESULTS.json. Faltan VirtualDesktopInfo,
menús/acciones restantes, delegados Wayland y coordinación diaria. No se habilita takeover.

Continuación sobre e41c28d: CTest local reproducible sin fuentes externas añadido
(BREEZE_R4_REPRO_RESULTS.json); runner de sesión usa build convencional y fixture del repo.
Conservar los tres metadata.json propios omitidos por el commit. La puerta KNS de Claude
sigue superada; integración diaria/backends y aceptación restante siguen pendientes.

### R0 — Auditoría profunda y referencia — HIGH

```text
Trabaja en /mnt/HDD1TB/Projects/hyprland-de. Lee AGENTS.md y docs/BREEZE_PLAN_V2.md entero,
incluidas sus reglas comunes. Ejecuta únicamente R0: auditoría profunda, sin cambiar el runtime.

Revisa la skin completa y contrasta cada pieza con las fuentes originales de la versión KDE
instalada. Confirma versiones, commits, servicios, plugins instalados frente a cargados y estado
de Git. Usa el plan anterior sólo como historial: comprueba lo que realmente hay hoy.

Prioriza: Magic/Alt+S y activación desde tareas/Alt+Tab; modo edición del escritorio/panel;
descubrimiento y configuración de plasmoides y componentes de temas; systemsettings real;
sombras activas/inactivas y CSD/SSD; animaciones y sus KCM. Revisa además Kickoff, tareas,
bandeja, reloj, avisos, portapapeles, Bluetooth/red/audio/energía, menús, decoraciones,
snapping, escritorios, OSD, bloqueo, accesibilidad, traducciones y cambios de skin.

Para cada hueco da: ruta y símbolo, upstream exacto, síntoma, prioridad, causa comprobada o
hipótesis, propuesta mínima, dependencias y prueba de aceptación. No basta listar READMEs.
Inspecciona contratos y rutas de ejecución y marca lo que no pudiste reproducir.

Establece una referencia de Plasma predeterminado de igual versión, fuente, escala y ajustes.
Si no hay sesión de referencia aislada disponible, prepara su procedimiento y marca pendientes
las comparaciones visuales/temporales: no presentes capturas de internet como igualdad medida.
No abras otro escritorio sobre la sesión del usuario.

Entrega docs/BREEZE_AUDIT_V2.md y BREEZE_R0_RESULTS.md con matriz P0/P1/P2 y procedimiento
de medición. Ajusta las fases restantes del plan según lo encontrado, sin rebajar los objetivos.
R0 no ejecuta R1 ni arregla los fallos; deja el siguiente prompt listo y explica los bloqueos reales.
```

### R1 — Un solo Magic y ventanas especiales correctas — HIGH

```text
Lee AGENTS.md, docs/BREEZE_PLAN_V2.md y la auditoría R0. Implementa sólo R1.

Arregla el fallo reportado: Breeze debe usar el mismo special:magic de las otras skins.
Alt+S debe mostrar/ocultar sus ventanas encima del workspace normal; no puede haber ventanas
de Magic visibles detrás de ventanas normales ni una segunda identidad especial según la skin.

Antes de cambiar nada, traza atajos efectivos, reglas de usuario sólo en lectura, workspace
asignado y activeSpecialWorkspace por monitor. Distingue magic, special sin nombre,
special:minimized y otros especiales legítimos. No migres ni borres otros especiales por suponer
que están duplicados. Comprueba con ventanas desechables si hay dos destinos o un fallo de
visibilidad/foco/orden; documenta la causa real.

Revisa keybinds-manager.py/keybinds.json, HyprlandData, TaskbarApps, Alt+Tab, TasksModel,
kwin-window.py focus, toggle-minimize.py, bwm_windows.py y transiciones. Una activación debe
resolver primero el estado especial correcto y después foco/orden; no sacar una ventana de
Magic, fijarla en todos los escritorios ni «arreglarlo» sólo con alter_zorder. Unifica la política
común sin introducir código Breeze en Retro. El generador de atajos es la fuente persistente.

Cubre: vacío, varias ventanas, Alt+Shift+S, pulsaciones repetidas, cambio de workspace/monitor,
activar desde tareas y Alt+Tab con Magic oculto/visible, minimizar/restaurar, Mostrar escritorio,
fullscreen y cambios default→Breeze→Retro→Breeze con Magic abierto y cerrado. Separar siempre
minimizadas. Identidad por dirección+PID y, para estado duradero, inicio del proceso.

Pruebas de transiciones y una reproducción aislada antes/después; comprueba además que no
hay ventanas ocultas interceptando entrada. Conserva ventanas, geometría y datos del usuario.
Si la causa está en Hyprland/plugin, presenta evidencia y corrige en la capa apropiada.
Entrega BREEZE_R1_RESULTS.md, con lo verificado en las tres skins y lo pendiente explícito.
```

### R2 — La aplicación real de Preferencias del sistema — HIGH

```text
Lee AGENTS.md, docs/BREEZE_PLAN_V2.md y resultados R0–R1. Implementa sólo R2.

Objetivo estricto: Super+I, Kickoff, KRunner, menús y open-settings.sh deben abrir la aplicación
real systemsettings de KDE en Breeze. No otra copia de su sidebar ni otro qs -p que se le parezca.
El binario existía al redactar el plan: confirma paquete/versión y prueba su funcionamiento antes
de recomendar descargarlo. Si falta una dependencia, prepara el comando Gentoo exacto.

Investiga el descubrimiento de KCM y categorías de esa versión y construye módulos BWM reales
con KCMUtils/KConfig/Kirigami (QML o QWidget según contrato), instalables bajo el prefijo local
de BWM sin sobrescribir archivos del sistema. Primero prueba un KCM BWM mínimo cargado por
systemsettings real y su apertura directa; después integra las páginas BWM necesarias.

Conserva los controladores comunes de BWM y su autoridad. Las páginas deben verse como KCM
KDE: no incrustes sin adaptar los controles Material de end-4. Usa las categorías naturales y
una sección BWM para lo exclusivo; no dupliques opciones KDE equivalentes. Soporta QWidget,
búsqueda, traducciones, subpáginas, Aplicar/Restablecer/Predeterminados, avisos de cambios y
resaltado de modificados. Mantén SETTINGS_PAGE y alias con un mapa al módulo real.

Verifica resolución desde favoritos .desktop y menús sin secuestrar globalmente systemsettings
en otras skins. No falsifiques KDE_SESSION_VERSION/XDG_CURRENT_DESKTOP de toda la sesión para
mostrar módulos. Evalúa el descubrimiento real y posibles variables sólo del lanzador.

No retires el host anterior hasta demostrar navegación, persistencia y reapertura del flujo real.
R3 completará adaptadores de KCM que escriben ajustes sin efecto en Hyprland; deja ese inventario
explícito. Declara dependencias, instalación/rollback y licencias. Entrega BREEZE_R2_RESULTS.md.
```

### R3 — KCM nativos que funcionan y configuración de terceros — HIGH

```text
Lee AGENTS.md, docs/BREEZE_PLAN_V2.md y resultados R0–R2. Implementa sólo R3.

Con systemsettings real como anfitrión, conecta las preferencias KDE al comportamiento real de
BWM. Revisa kde-config-bridge.py y su inventario de autoridad por clave. Incluye comportamiento
de ventanas, decoraciones, foco, encaje, animaciones, pantalla/escala, escritorios, cursor,
atajos, apps predeterminadas, inicio y energía. Para lo común usa los gestores BWM existentes;
para lo propio de Breeze lee formatos KDE y conserva claves desconocidas y kdedefaults.

No confundas que un KCM abra con que su opción funcione. Prueba escritura→aplicación→lectura
tras reabrir y tras cambiar de skin. Evita bucles, carreras y recargas por cada deslizador.
No dupliques PowerDevil, KScreen, kglobalaccel ni servidores: inventaría qué API necesita cada
módulo. Donde no sea viable reutilizar el KCM, implementa el adaptador o un KCM BWM nativo con
equivalencia documentada; no dejes un control activo que sólo escriba un archivo ignorado.

Descubre módulos de configuración de decoraciones y plugins mediante sus metadatos/fábricas
reales, incluidos los de terceros. Demuestra una opción específica de un complemento instalado
que no existía en la lista fija BWM: aparece en el módulo correcto, se aplica y persiste.
El catálogo completo de plasmoides y sus páginas se resuelve en R4, no con opciones a mano.

R7 implementará los efectos: acuerda ahora claves/capacidades y el contrato de su KCM, sin
anunciar efectos KWin como operativos sólo porque estén instalados. Si hace falta filtrar
módulos del anfitrión, usa mecanismos soportados; no borres metadatos del sistema.
Entrega BREEZE_R3_RESULTS.md y tabla control→archivo/API→efecto real→verificación.
```

### R4 — Plasmoides, paquetes y páginas de configuración originales — HIGH

```text
Lee AGENTS.md, docs/BREEZE_PLAN_V2.md y resultados R0–R3. Implementa sólo R4.

Resuelve el anfitrión que falta para alojar plasmoides y su configuración real sobre Hyprland.
Estudia libplasma/PlasmaQuick, Corona, Containment, Applet, PlasmoidItem, KPackage y los
contratos usados por el modo edición original. Usa auxiliares KDE fuera de Hyprland si hacen
falta. No ejecutar plasmashell ni sustituir el compositor. No declares imposible cargar todo
plasmoide sólo porque un caso dependa de KWin: clasifica dependencias por capacidades.

Haz primero una prueba aislada: plasmoide original simple y uno de terceros con configuración
propia. Demuestra representación compacta/expandida, acciones, tamaño, localización, esquema
contents/config/main.xml, categorías contents/config/config.qml, páginas config*.qml y ciclo
Aplicar/Cancelar/Predeterminados, persistencia por instancia y dos instancias independientes.
Los paths son contratos habituales: confirma cómo los resuelve KPackage en esta versión.

Descubre paquetes en rutas XDG estándar y originales KDE. Para datos que Plasma ya define,
usa su formato original; diseña y prueba la migración desde bar.plasma sin perder configuración
ni inventar un appletsrc incompleto como nuevo estándar. Separa metadatos de paquetes,
configuración por instancia, disposición y preferencias compartidas BWM.

Proporciona al editor R5 las interfaces de panel, containments, widgets, acciones, catálogo
y configuración. Integra Obtener nuevos… con el proveedor nativo correspondiente y actualización
del catálogo. Prueba instalar/quitar un complemento desechable en entorno aislado.

Para temas globales: distinguir defaults, SVG, decoraciones, plasmoides, fondos y scripts de
disposición. Determinar cómo ofrecer sus opciones reales sin ejecutar layouts a ciegas. Registrar
las capacidades no soportadas con explicación por paquete, sin prometer universalidad.
Puerta de salida: un widget externo no conocido de antemano muestra y guarda su opción propia.
Si no la supera, deja R4 pendiente y no disfraces la lista fija como soporte de plugins.
Entrega BREEZE_R4_RESULTS.md, arquitectura y guía para actualizar desde upstream.
```

Continuación R4 §§237–238 (2026-11-16): usuario confirma funcionamiento del preview de
activación/restauración con --all-desktops. Nueva opción --session-appearance prepara sólo
apariencia KDE nativa en XDG temporal antes de QApplication; motores nativos de iconos,
paleta/fuentes/SVG y protección de origen pasan aislados normal/ASan. Snapshot inicial,
sin seguimiento vivo, migración de perfil o aceptación visual de sesión. Evidencia
BREEZE_R4_DESKTOP_FILTER_RESULTS.json y BREEZE_R4_APPEARANCE_RESULTS.json. R4/integración
diaria siguen abiertas; no se avanza a R5/R7.

Continuación R4 §239: aspecto/acciones del auxiliar aceptados por usuario; falta miniatura
hover. Adaptación opt-in del endpoint revisado de Plasma hacia captura por ventana nativa
Hyprland preparada, sin compositor/plugin nuevo ni módulo PipeWire requerido por esa vía.
Pruebas locales pasan; captura nativa sintética compilada pero bloqueada por EPERM del
ejecutor. Ejecución terminal y miniatura en sesión pendientes; R4 sigue abierta.

### R5 — Modo edición de Plasma, escritorio y panel — MEDIUM

```text
Lee AGENTS.md, docs/BREEZE_PLAN_V2.md y resultados R0–R4. Implementa sólo R5.
Usa medium si R4 dejó contratos probados; si falta arquitectura, resuélvela en R4 con high.

Sustituye PanelEditor.qml y el flujo reducido por las interfaces originales de la versión KDE
fijada: desktoppackage/contents/views/DesktopEditMode.qml, configuration/PanelConfiguration.qml,
panelconfiguration/*, explorer/WidgetExplorer.qml, configuración de applets/containments y
overlays de containments/panel. Confirma rutas y dependencias en esa etiqueta.

Porta el QML original, conservando estructura, métricas, iconos, textos, accesibilidad,
foco, animaciones y comportamiento. Adapta sólo los contratos del anfitrión. No hagas otro
popup propio con los mismos nombres de controles. Añade módulos en la carpeta Breeze.

Debe incluir el flujo de edición del escritorio y panel, terminar/Esc, asas de movimiento y
tamaño, borde y monitor, alineación, longitud y modos disponibles en upstream, grosor,
flotación, opacidad, visibilidad, añadir/quitar/reordenar widgets, espaciadores, configuración
individual y acciones del panel. Replica múltiples paneles cuando lo permita el contrato de
la referencia: una sola lista clonada en todos los monitores no es equivalencia.

Añadir widgets debe mostrar el catálogo descubierto en R4. Configurar un widget/tema/plugin
debe mostrar sus páginas originales si las trae, también tras instalarlo y sin editar una lista
BWM. No inventar menús por tema ni esconder acciones del original para evitar implementar su backend.

Prueba interacción real en fixture: cuatro bordes, dos monitores, escala fraccionaria, arrastre,
teclado, Escape, autohide, eliminar/deshacer si lo ofrece la referencia y persistencia tras
reinicio. Comprueba que al terminar se recuperan foco, región de entrada y reserved reales.
Compara imágenes recortadas con Plasma de igual versión; registra diferencias que queden.
Entrega BREEZE_R5_RESULTS.md; no certifiques «perfecto» por pasar qmllint.
```

### R6 — Las sombras originales, sin halos ni duplicados — HIGH

```text
Lee AGENTS.md, docs/BREEZE_PLAN_V2.md y resultados R0–R5; revisa el incidente de sombra en
BWM_CONTEXT.md §3.150–151. Implementa sólo R6.

Objetivo: profundidad de ventanas como Plasma, con las sombras de la decoración/tema real.
Ya existen DecorationShadow, transporte memfd y CBreezeShadow: audita y corrige esa ruta.
No reemplazarla por ajustar range/render_power de una sombra genérica de Hyprland.

Contrasta con KWin/Breeze de la versión fijada: imagen, padding, innerShadowRect, nueve trozos,
alpha premultiplicado, UV, escala/DPR, activo/inactivo, transición al cambiar foco, recorte,
daños y orden respecto al contenido/decoración/otras ventanas. Verifica vida de los recursos,
destrucción, reconexión del auxiliar, cambio de decoración y resize; no reintroducir weak.lock()
sobre propietario único. Revisa también sombras del panel, menús y popups.

CSD/SSD requieren clasificación: sombra propia del cliente, sombra KDecoration o ausencia.
Investiga soporte real de protocolos de sombras KDE y hints X11 antes de ofrecer compatibilidad
con apps que los usan. No fuerces una segunda barra/sombra sobre una CSD. Sin decoración o
fullscreen y bordes pegados/maximizados deben seguir la referencia, no una regla universal inventada.

Configuración: usar el diálogo propio de Breeze/decoración nativa y sus parámetros, incluidos
complementos Aurorae/terceros; cambios visibles sin perder preferencias al cambiar de skin.
Prueba claro/oscuro, activa/inactiva, ventanas pequeñas, bordes de pantalla, escalas 1/1.25/1.5/2
cuando estén disponibles, Wayland/XWayland, CSD/SSD, maximizado y tema alternativo.

Entrega comparación medible (márgenes y perfiles de alpha sobre fondo controlado) y revisión
visual con referencia equivalente. Instala plugin sólo por make install; pruebas anidadas y
anota qué queda pendiente hasta reiniciar sesión. Entrega BREEZE_R6_RESULTS.md.
```

### R7 — Animaciones de Plasma predeterminado y sus ajustes — HIGH

```text
Lee AGENTS.md, docs/BREEZE_PLAN_V2.md y resultados R0–R6. Implementa sólo R7.

Objetivo: clonar las animaciones predeterminadas de la versión Plasma de referencia, no elegir
unas curvas «parecidas». Inspecciona efectos habilitados de fábrica y fuentes de KWin y QML:
abrir/cerrar, minimizar/restaurar hacia la tarea, maximizar/restaurar, cambio de escritorio,
foco/opacidad/sombra, panel/autohide, popups, Kickoff, tooltips, edición y OSD. Magic es una
extensión BWM: debe conservar su semántica común, sin atribuirle una animación inexistente en KDE.

Construye tabla evento→efecto original→duración→easing→transformación→implementación BWM.
Separa efectos del compositor y animaciones QML. Determina qué soporta Hyprland y qué requiere
un complemento seguro; evalúa snapshots, shaders, geometría destino y cancelación antes de
descartar un efecto. No ejecutar scripts/efectos KWin como si Hyprland tuviera su ABI.

Elimina md3_* y popin 60% de la ruta Breeze donde no correspondan a la referencia; consolida
animations.lua y kwin.lua en una fuente de verdad. AnimationDurationFactor debe aplicarse
coherentemente, incluido 0, retorno a 1 y cambios repetidos; no asumir unidades de speed sin medir.
Incluye cancelación/reversión de gestos, ventana destruida, foco rápido, fps y reduced motion.

Integra preferencias en systemsettings real usando el KCM original donde sea viable y el
contrato de R3. Configuración por efecto y páginas de plugins sólo para capacidades que estén
implementadas; controles operativos, predeterminados correctos y persistencia. No muestres un
catálogo completo de efectos KWin que no pueden ejecutarse con BWM.

Compara vídeos o secuencias con timestamps de Plasma/BWM en escenario idéntico: duración,
trayectoria y escala/opacidad en puntos de la línea temporal. Define tolerancias justificadas
por frame y registra diferencias; no certifiques clon exacto con una captura estática.
Mide coste y evita bloquear el render de Hyprland. Entrega BREEZE_R7_RESULTS.md y pendientes
de carga del plugin. No modificar las animaciones de las otras skins.
```

### R8 — Mejoras de uso diario detectadas — MEDIUM

```text
Lee AGENTS.md, docs/BREEZE_PLAN_V2.md, auditoría R0 y resultados R1–R7. Implementa R8.

Resuelve primero los P0/P1 pendientes del inventario. Trabaja por lotes pequeños con validación
al terminar cada uno. Si un lote necesita arquitectura/protocolos/C++, sepáralo con high; medium
se reserva para ports y correcciones delimitadas sobre proveedores ya probados.

Revisa especialmente tareas (grupos, filtros, progreso/insignias, rueda, miniaturas y multimedia),
reloj (zonas horarias, calendario/agenda, configuración), bandeja (visibilidad/menús/configuración),
notificaciones (acciones/respuesta, historial), portapapeles y Bluetooth. Prioriza comportamiento
habitual y componentes originales frente a funciones nuevas ajenas a Plasma. Conserva las
correcciones recientes de medidas, iconos cuadrados, anclajes y resaltado del panel.

Completa las opciones nativas de los widgets incluidos y su acceso desde modo edición. No
dupliques notificaciones, klipper, energía, red ni Bluetooth para conseguir una interfaz.
Si una prestación necesita otro proveedor, documenta propiedad del servicio, lifecycle y
dependencias antes de habilitarla. Conserva el estado común de BWM entre skins.

Revisa accesibilidad, teclado/lector de pantalla, foco, traducciones, colores claros/oscuros,
escala fraccionaria y múltiples paneles. Cierra los fallos de QML reales: no silenciar avisos
generales para que el informe quede limpio. Actualiza la auditoría por evidencia, no por intención.
Entrega BREEZE_R8_RESULTS.md y lista precisa de P2 aplazados, si los hay.
```

### R9 — Aceptación final y regresiones de las tres skins — HIGH

```text
Lee AGENTS.md, docs/BREEZE_PLAN_V2.md, auditoría y todos los informes R0–R8. Ejecuta R9.

Verifica qué binarios están realmente cargados. Una compilación o make install pendiente del
próximo inicio de sesión no cierra una prueba. Prepara lo necesario antes de pedir al usuario
guardar trabajo y volver a entrar; no cierres su sesión por tu cuenta.

Prueba la matriz final: Breeze predeterminado claro/oscuro, un estilo SVG distinto, una
decoración Aurorae o C++ alternativa disponible, tema global y plasmoide externo con opción
propia. Confirma que la aplicación es systemsettings real, KCM BWM descubiertos, opciones
nativas de terceros, Aplicar/Cancelar/Predeterminados, persistencia y rollback.

Recorre edición de escritorio/panel, cuatro bordes, múltiples paneles/monitores, escala
fraccionaria, autohide y reserved; sombras y animaciones contra referencia; CSD/SSD, snapping,
menús, maximizado por ejes, minimizar/restaurar, fullscreen, OSD y bloqueo. El bloqueo/PAM y
acciones de energía se prueban con intervención del usuario, no en copias con llamadas reales.

Reproduce el fallo original de Alt+S y verifica su ausencia: Magic oculto/visible, activar
ventanas desde tareas/Alt+Tab, moverlas y cambiar normal/especial/monitor; ninguna aparece
detrás ni sale de su especial por enfocar. Repite default→Breeze→Retro→Breeze, sin reiniciar
apps ni alterar audio, ventanas o workspaces del usuario, usando un entorno de prueba adecuado.

Ejecuta pruebas apropiadas y la suite de regresión disponible; separa tests omitidos, sondeos
de API, interacción automatizada y verificación física. Registra una sola instancia ii y un
solo dueño por servicio. Limpia fixtures, reglas y capturas privadas y conserva las preferencias.

Entrega BREEZE_R9_RESULTS.md y actualiza BREEZE_ARCH, READMEs de módulos, requisitos/licencias
y contexto. Marca cada objetivo de este plan como verificado, parcial o bloqueado con motivo.
No declarar 100 %, «idéntico» o «perfecto» si quedan diferencias medidas o pruebas esenciales
sin realizar. Si queda un P0/P1 de esta petición, el plan sigue abierto con su siguiente prompt.
```

## 6. Fuentes y aceptación

Fuentes primarias para los contratos (cotejar siempre con la etiqueta instalada):

- [KCM y System Settings](https://develop.kde.org/docs/features/configuration/kcm/).
- [Configuración de plasmoides](https://develop.kde.org/docs/plasma/widget/configuration/).
- [plasma-desktop](https://invent.kde.org/plasma/plasma-desktop): desktoppackage, containments,
  taskmanager y sus ventanas de configuración.
- [plasma-workspace](https://invent.kde.org/plasma/plasma-workspace): shell, panelview,
  systemtray, reloj y applets.
- [systemsettings](https://invent.kde.org/plasma/systemsettings),
  [libplasma](https://invent.kde.org/plasma/libplasma),
  [KCMUtils](https://invent.kde.org/frameworks/kcmutils).
- [KWin](https://invent.kde.org/plasma/kwin), [Breeze](https://invent.kde.org/plasma/breeze),
  [KDecoration](https://invent.kde.org/plasma/kdecoration) y
  [Aurorae](https://invent.kde.org/plasma/aurorae).

No se considera cerrado este plan sin: Magic común sin el fallo reportado; systemsettings real
con módulos BWM; edición con los controles originales; opción propia de un complemento externo
descubierta y persistente; sombras verificadas; animaciones comparadas y configurables; y
regresión entre las tres skins. El inventario final debe hacer visibles las diferencias restantes.

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
