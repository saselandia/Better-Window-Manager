# Anfitrión libplasma — arquitectura R4 experimental

Estado: expansión, diálogo y catálogo probados en auxiliar aislado, **sin integración en el panel**. Objetivo de versión:
libplasma 6.7.5; las interfaces PlasmaQuick utilizadas contienen avisos de API privada.

## Componentes comprobados

`src/bwm-plasma-host/main.cpp` usa QApplication, una subclase mínima de Plasma::Corona,
Containment nativo, Applet nativo y PlasmaQuick::AppletQuickItem::itemForApplet. No ejecuta
plasmashell, KWin ni registra servidores D-Bus. QtTest muestra ventanas sólo sobre plataforma
offscreen; `--preview` es una apertura interactiva explícita con configuración temporal.
Los primeros ensayos usaban geometría 1024×768. Ahora el ejecutable enlaza ViewCorona a la
salida Qt de cada vista; los fixtures de staging/probePanel siguen separados de los monitores reales.

Corona carga y guarda `bwm-plasma-host-appletsrc` mediante **loadLayout/saveLayout**. No se genera
un INI propio: Corona conserva la jerarquía nativa de containments/applets/Configuration.
Dos Applet con el mismo plugin conservan IDs y configuración independientes. El nombre del
archivo separa el ensayo del escritorio Plasma; su contenido lo serializa libplasma.

`--catalog` usa `Catalog`/Plasma::PluginLoader::listAppletMetaData: combina KPackage con
bibliotecas de `plasma/applets`. La primera versión que sólo preguntaba a PackageLoader
omitía widgets compilados. No interpreta una lista fija de widgets. El orden de búsqueda lo decide KPackage/QStandardPaths, incluyendo
XDG_DATA_HOME y XDG_DATA_DIRS. Los plugins compilados/recursos qrc pueden resolver su QML
por una ruta distinta de la del paquete físico: no se sustituye ese comportamiento en Applet.

`--probe ID` carga el plasmoide y sus páginas originales. `--exercise ID` elige dinámicamente
una propiedad booleana `cfg_*` presente en una página y en su KConfigLoader; no conoce de
antemano la clave del plugin. Es un ensayo de configuración, no una interfaz de usuario final.
Exige raíces XDG temporales. El driver también aísla caché, runtime, defaults y D-Bus.

## Resolución confirmada en 6.7.5

Fuentes originales: `src/plasma/packagestructure/packages.cpp`,
`plasma_applet_packagestructure.cpp`, `shell/shellpackage.cpp`, `src/plasma/applet.cpp` y
`src/plasmaquick/{appletquickitem,configview,configmodel}.cpp`.

| Contrato | Resolución nativa |
| :--- | :--- |
| Entrada QML | `mainscript` → `contents/ui/main.qml`; Applet también contempla qrc |
| Esquema | `mainconfigxml` → `contents/config/main.xml` → KConfigLoader |
| Categorías | `configmodel` → `contents/config/config.qml` → ConfigModel |
| Página por archivo | ConfigModel resuelve SourceRole dentro de `ui`; se usa esa URL. Los paths absolutos preservados por KDE se convierten a URL local |
| Página por módulo | Pareja configUiModule/configUiComponent → QQmlComponent.loadFromModule con rutas de importación Qt; precede a source, como AppletConfiguration.qml 6.7.5 |
| Inicialización de página | beginCreate → setInitialProperties(title/cfg_ declarados/defaults/immutable) → completeCreate; los valores existen antes de Component.onCompleted |
| Localización | Applet.translationDomain y KLocalizedQmlContext de ConfigView |
| Form factor y borde | Containment.setFormFactor/setLocation, heredados por Applet |
| Representaciones | PlasmoidItem real, compactRepresentationItem/fullRepresentationItem |
| Expansión y muebles | Paquete Plasma/Shell: compactapplet, defaultcompactrepresentation, appletconfigurationui |

ConfigView crea el contexto del Applet y su ConfigModel. `ConfigurationSession` aloja las
páginas originales dentro del paquete de shell mínimo de BWM. El diálogo ofrece categorías,
Aplicar, Cancelar y Predeterminados. Conserva cambios en las páginas, convierte tipos según
KConfigLoader, respeta claves inmutables y relee antes de guardar para rechazar una edición
concurrente. Predeterminados prepara todos los valores conocidos del esquema, incluidos los
no expuestos por una página; no guarda hasta Aplicar. Claves ajenas se conservan por KConfig.
Se probaron bool, texto y enteros; no se certifican todos los tipos de todos los paquetes.

Las claves compartidas por varias páginas usan una preparación común por sesión. La señal
nativa de la propiedad identifica la página editada; se actualiza sólo esa clave en las demás,
con guarda de reentrada y sin guardar ni reconstruir páginas. Un límite incompatible entre
controles bloquea Aplicar. El notifier pagesChanged queda separado de dirty/error: mover un
deslizador no reconstruye los delegados que alojan las páginas. El esquema completo conserva
también los valores no expuestos, y sólo Predeterminados los prepara para un cambio explícito.

Una página con clave cfg_* sin esquema, sin escritura/notificación, callbacks personalizados
loadConfig/saveConfig o categoría pluginName que requiere KCM se marca sin adaptar y bloquea Aplicar con
explicación. No se ofrece como control operativo una escritura que se ignoraría.
El formulario del plugin es original; el marco de diálogo y los muebles son un adaptador BWM,
no una copia completa de la interfaz del shell Plasma ni el modo de edición R5.

Un módulo QML no equivale por sí solo a un KCM. Se admite su componente visual cuando sigue
el mismo contrato de esquema/propiedades cfg_ de las páginas por archivo; no se anuncia un
backend KCModule adicional por cargarlo. Si falta parte de la pareja módulo/componente y hay
source, se usa source como el shell original. Una pareja completa tiene prioridad: si falla,
se informa del error sin sustituirla silenciosamente por source. También se rechazan raíz
no Item y propiedades obligatorias que el contrato nativo no suministra.

La misma fábrica sirve al diálogo y a --probe/--exercise. --probe expone loader/module/component
y configurationError; --exercise aplica a través de ConfigurationSession en lugar de guardar
por una vía aparte. Su prueba booleana sigue siendo parcial; QtTest cubre además texto/entero,
propiedades obligatorias antes de completar, contexto plasmoid/localización, botones,
Defaults/Cancel sin escritura, dos instancias y lectura desde otro proceso. El módulo de
regresión y sus paquetes de error se instalan sólo en el XDG temporal; no son prueba de un
complemento tercero por módulo. Andromeda continúa como prueba externa por archivo.

Al actualizar upstream, revisar ConfigCategory/ConfigModel, la prioridad de open() en
AppletConfiguration.qml y la creación Qt (loadFromModule y beginCreate/setInitialProperties/
completeCreate), además del esquema y los callbacks. Repetir módulo ausente, tipo ausente,
raíz no visual, required desconocido, descriptor incompleto/fallback y source absoluto.
Evidencia: BREEZE_R4_CONFIG_PAGES_RESULTS.json.

ConfigView 6.7.5 hace deleteLater() desde hideEvent(). El auxiliar usa QPointer y verifica
su vida; no unique_ptr. El doble borrado de la primera implementación se encontró y corrigió
con AddressSanitizer. El paquete `shell/` usa AppletPopup nativo para alojar la representación
completa y proporciona el compacto de reserva. No se modifica libplasma para esconder el fallo.

## Vista original del panel

PanelViewHost deriva de PlasmaQuick::ContainmentView y carga mediante KPackage el
views/Panel.qml instalado de org.kde.plasma.desktop, sin copiarlo ni modificarlo. El
containment org.kde.panel conserva su QML/LayoutManager; la vista aporta fondo, prefijos,
márgenes, opacidad de las capas SVG y señalización de foco originales. Corona mantiene el
paquete de shell mínimo para popup/configuración: no se ejecuta plasmashell.

El módulo QML org.kde.plasma.shell.panel recibe sólo la metainformación Global de los enums
de PanelView 6.7.5. No registra un PanelView completo ni sustituye metadatos del sistema.
El adaptador ofrece las propiedades que usa esa vista. Configurar se enruta desde el método
virtual de ContainmentView hacia una única PanelSession, creada sin su conexión duplicada.

| Contrato | Adaptación comprobada |
| :--- | :--- |
| Fondo/tema | SVG originales de PlasmaCore/KSvg; cambio de tema sin reconstruir la vista; cuatro prefijos direccionales del QML original |
| Grosor/longitud | Grosor limitado por el mínimo de dibujo del tema; length es preferencia natural y setLengthRange define límites de la superficie, 640 fijo en la vista de ensayo |
| Flotación | Padding fijo leído del QML; floatingness animado hacia floatingnessTarget con duración Kirigami e InCubic/OutCubic como PanelView |
| Máscara | panelMask nativo, desplazado por floatingTranslucentItemOffset; NoBackground elimina el dibujo. QWindow.setMask prepara la petición; aplicación real Wayland pendiente |
| Opacidad | Opaque/Translucent con vista previa y guardado explícito; Adaptive se rechaza porque falta el backend común de ventanas. Se conserva el fallback original sin composición en offscreen |
| Visibilidad | WindowsGoBelow constante en el auxiliar: visible sin reserva. No ofrece autoocultado/dodge como operativos |

El cambio de orientación no debe tomar como longitud el máximo del eje anterior. Tampoco
debe confundir el preferredLength cero de un containment inicializándose con una petición de
encoger la superficie. Los tests verifican ambos casos, límites, grosor, padding del tema y
SVG por borde con dos temas desechables. Comparan píxeles con tolerancia 4/255 RGB; no hacen
una certificación colorimétrica ni de efectos del compositor.

La destrucción desconecta el containment, cierra configuración, detiene animación, separa el
AppletQuickItem y elimina el root QML antes de destruir las propiedades derivadas. Se revisó
SharedQmlEngine 6.7.5: guarda su root en QPointer; su destructor no vuelve a eliminarlo.

--panel-preview y --layer-panel-preview alojan ahora esta vista. --probe-panel-frame usa la
misma ruta y termina con JSON de carga/adjunción/readback/capacidades; no significa validación
Wayland. El layout nativo del panel se separa del de los probes de widgets para no envolver
por error un containment null. Evidencia: BREEZE_R4_PANEL_VIEW_RESULTS.json.

Pendientes: negociación/render de este marco en Wayland, escala fraccionaria, reservas,
controlador adaptable/autohide, desenfoque y sombras externas. Las preferencias admitidas del
marco usan ahora el formato nativo descrito abajo; UI y ciclo por skin requieren integración.
Al actualizar revisar Panel.qml, panelview.h/.cpp, ContainmentView/QuickViewSharedEngine/
SharedQmlEngine y los flags/máscaras KSvg; repetir las comprobaciones de vida con ASan.

### Preferencias nativas de la vista

PanelViewSettings usa plasmashellrc con KConfig, según panelview.cpp y applicationConfig de
ShellCorona 6.7.5. Mantiene el nombre relativo al abrir KConfig para respetar la cascada
XDG_CONFIG_DIRS/kdedefaults; sólo calcula el destino absoluto para identificar el bloqueo.
No copia estos datos a Configuration de un applet ni a preferencias comunes BWM.

| Claves KDE admitidas | Lectura y escritura nativa |
| :--- | :--- |
| floating / floatingApplets / panelOpacity | PlasmaViews / Panel <id>, enteros originales 0/1 y enum de opacidad |
| thickness | PlasmaViews / Panel <id> / Defaults |
| minLength / maxLength | Horizontal<ancho lógico Qt> o Vertical<alto lógico Qt>, con fallback a Defaults; al guardar se escriben ambos destinos como KDE |

viewSettings es la última instantánea cargada/guardada. Los setters visuales siguen siendo
vistas previas sin escritura. reloadViewSettings descarta esa vista previa, relee y aplica;
applyViewSettings(changes) valida el lote, guarda y relee antes de aplicarlo al marco.
Sólo se aceptan las seis claves declaradas y valores soportados; no se ignoran claves pedidas
desconocidas. Las claves ajenas ya almacenadas se conservan. Opacidad adaptable y políticas
explícitas de controlador que el auxiliar no implementa se rechazan sin reescribirlas ni
mostrar una vista que las ignore. La ausencia de esas políticas mantiene los defaults seguros
de la vista de ensayo, sin guardarlos de forma implícita.

El cambio de salida/orientación invalida el destino de guardado hasta reloadViewSettings.
El bloqueo por archivo serializa escritores BWM; las firmas de todos los destinos de cada
clave detectan cambios desde la carga, incluso un Defaults oculto por la resolución actual.
Los cambios ajenos en claves no tocadas se mantienen. KConfig conserva además su bloqueo y
mezcla de archivo; esto no es un compare-and-swap global frente a KCM ajenos. Una sincronización
fallida limpia el escritor privado para impedir que su destructor reintente una escritura
que se había informado como fallida. Las validaciones/conflictos/bloqueos se resuelven antes
de escribir cualquier clave del lote; no hay watcher ni reload por cada deslizador.

Se prueban grupos nativos, efecto visual, dos paneles, lectura en proceso nuevo, herencia
kdedefaults e inmutabilidad, conflictos, claves ajenas, escritor ocupado, orientación y un
Adaptive almacenado rechazado antes de cargar el frame. Evidencia: BREEZE_R4_VIEW_SETTINGS_RESULTS.json.
La migración de otras preferencias heredadas y la activación/ciclo por skin siguen pendientes.

## Interfaces para R5

| Interfaz | Disponible ahora | Requisito antes de consumirla en R5 |
| :--- | :--- | :--- |
| Catálogo de paquetes | `Catalog.entries/changed/refresh`, metadatos KDE nativos | Selección/altas del editor y ciclo por skin |
| Containments/widgets | PanelSession.panelInfo/widgets/order y altas/bajas; PanelRuntime coordina vistas de containments existentes por descripción de salida | Integración con el ciclo real BWM, alta/baja de paneles completos y aceptación Wayland |
| Representaciones | Clic compacto → AppletPopup, expansión/cierre repetidos | Adaptación de posición, foco y cierre en Wayland/Hyprland |
| Ventanas del paquete | PackageWindows.capabilities/refresh y adaptación pre-superficie de Dialog nativo | Validar negociación Wayland; adaptar Window genérico, tipos no interactivos y creación tardía |
| Acciones | PanelSession.widgetActions/triggerAction, tokens por identidad de QAction; submenús/estados/acciones dinámicas probados con fixtures inocuos | Integración del menú original del editor; servicios de cada acción se evalúan por paquete |
| Configuración | PanelSession.configure(id)/configurationOpened(id) enlaza configureRequested con ConfigurationSession; páginas, botones y persistencia probados | Adaptar explícitamente callbacks/KCM/casos bloqueados y aceptación en sesión |
| Obtener nuevos | KNSWidgets::Dialog(plasmoids.knsrc), refresco al terminar y watcher único | Verificar descarga real, errores de red y retirada desde KNS |
| Persistencia | loadLayout/saveLayout nativos; ciclo de vistas por skin y reapertura con conectores/índices distintos probados en Qt aislado | Autoridad/persistencia de bindings en la integración diaria y rollback de migración |
| Disposición | PanelSession.requestOrder usa el método nativo reorderApplets de org.kde.panel; AppletOrder, posiciones y lectura desde otro proceso probados | Geometría de panel, opciones no mapeadas, activación y rollback |

Las APIs QObject funcionan dentro del auxiliar y se prueban sobre el panel original. R5
puede alojar su UI en ese proceso; un editor externo necesitará además un IPC estable y el
ciclo de integración del panel. No se reutiliza la lista fija del panel como catálogo externo.

### Contrato PanelSession para el editor

| Operación | Semántica |
| :--- | :--- |
| panelInfo / widgets / order | ID nativo del containment, propiedades y widgets en orden nativo; changed coalescido. runtimeVerified=false no acredita sus backends |
| bindPanelItem(item) | C++: sólo acepta el AppletQuickItem del containment propietario; el ejecutable deja la sesión en la propiedad bwmPanelSession de su ventana |
| addWidget(pluginId) → ID o 0 | Descubre metadatos actuales con la misma política del catálogo; createApplet nativo, sin lista fija ni forzar un containment bloqueado. Crear no certifica servicios/funcionalidad |
| removeWidget(ID) → bool | Retirada permanente mediante Applet.destroy; respeta panel/widget inmutable y rechaza otro panel. Cierra Configurar al marcar transient, antes de limpiar su esquema. No simula la notificación de deshacer |
| requestOrder(IDs) → bool | Acepta sólo una permutación exacta de los widgets vivos, con IDs enteros únicos, vista propia y estado mutable. Delega reorderApplets al QML original; true confirma despacho, el consumidor confirma el orden observado |
| widgetActions(ID, prepare=true) | Al abrir el menú emite contextualActionsAboutToShow y descubre los QAction originales, incluidos submenús. Refrescar estado con prepare=false evita reconstrucción recursiva desde actionsChanged |
| triggerAction(ID, token) → bool | Verifica propietario por objeto, pertenencia actual y ruta visible/habilitada hasta el QAction. Rechaza tokens ajenos, retirados o destruidos y los encabezados de submenú |
| configure(ID) | Solicitud nativa por instancia; ConfigurationSession conserva el contrato de páginas/esquema, no añade controles fijos |

Los tokens de acciones son efímeros por sesión y no se guardan como preferencias; no usan
texto, objectName ni posición como identidad. Las acciones contextuales de los complementos
se descubren dinámicamente; las acciones internas del shell no se anuncian adaptadas mediante
este catálogo. Configurar y retirada tienen sus operaciones explícitas. Los servicios que
necesita una acción de un paquete siguen sujetos a su evaluación de capacidades.

requestOrder se llama al confirmar la disposición, no en cada movimiento del puntero. El
LayoutManager original realiza sus propias escrituras; BWM no replica su formato ni añade
recargas. Para persistir un panel, cargar primero su archivo propietario con loadLayout,
guardar sobre el mismo archivo y sincronizar Corona.config(). El esquema del containment
está en Containments/<id>/General/AppletOrder, a diferencia de la Configuration de un Applet.
La exportación saveLayout a otro archivo pasa por saveState/copyTo y no sustituye ese ciclo:
el ensayo detectó una copia de estado bajo Configuration que no se restauraba como orden.
No se corrige escribiendo a mano un INI alternativo.

El test nativo añade el paquete elegido, reordena y retira/recrea otra instancia; comprueba
el archivo, desaparición de la configuración retirada, valores por instancia y posiciones del
QML original en un proceso nuevo. La guía de actualización debe revisar main.qml/reorderApplets,
LayoutManager.js, Containment.createApplet, Applet.destroy/destroyedChanged y Corona.loadLayout/
saveLayout/saveState, además del contrato de menús QAction. Evidencia: BREEZE_R4_PANEL_API_RESULTS.json.

## Migración desde bar.plasma

`migration.py` produce una propuesta determinista con hash y **texto completo** del origen.
Reconoce los seis nombres heredados sólo para su migración; conserva duplicados, orden,
valores desconocidos y widgets sin correspondencia. No modifica el origen ni genera appletsrc.
Se crean propuestas independientes por descripción de monitor. Dieciocho tests prueban conservación,
idempotencia, mapeos de esquema, orientación y rechazo de identidades DP-/HDMI-.

El borde se conserva desde bar.plasma.edge; si está vacío/ausente se usa bar.bottom (false
por defecto en Config.qml), como PanelLogic.edge. Un valor inválido o un fallback no booleano
se rechaza. El stager C++ vuelve a derivarlo del archivo de origen autenticado y comprueba
que la propuesta coincide. Containment recibe la Location y el FormFactor nativos antes
de crear widgets; Corona serializa ambos. El probe de QML comprueba el orden por x o por y.

orientationContractVersion=1 pertenece al informe de staging: exige edge/location/formFactor
coherentes con el origen y layout, sin cambiar el formato nativo. Propuestas antiguas sin edge
se resuelven desde el origen. Los informes antiguos sin ese contrato conservan su semántica
bottom/horizontal: no se reinterpreta ni transforma un layout ya preparado. Para corregir un
staging antiguo se vuelve a preparar desde su origen. Siete casos prueban cuatro bordes,
fallbacks y valor por defecto en dos paneles con lectura/probe/lectura en procesos distintos.
Evidencia: BREEZE_R4_ORIENTATION_RESULTS.json.

El staging incluye ahora plasmashellrc separado del layout y del archivo de origen. Guarda
thickness en PlasmaViews/Panel <id>/Defaults y floating/panelOpacity en el grupo del panel,
con enteros originales. Se deriva dos veces (propuesta Python y C++ desde legacy.json):
thickness sigue el fallback 0→44 y clamp 24..128 de PanelLogic; style opaque/translucent/
adaptive usa 1/2/0; el antiguo style=floating equivale a floating=1 más Adaptive=0. No se
confunde bar.plasma.opacity, un alfa numérico heredado, con el enum panelOpacity.

viewSettingsContractVersion=1 identifica esos datos en el informe, no cambia el formato KDE.
verify compara origen, informe y archivo nativo; rechaza un artefacto sin contrato o ausente,
valores cambiados y omisión de pendientes. Conserva la lectura de stages antiguos realmente
sin preferencias de vista. El artefacto contiene los paneles preparados: nunca debe sustituir
el plasmashellrc completo de la sesión. Su futura activación requiere mezcla por IDs y
respeto de la cascada/inmutabilidad del destino, que aún no se implementa.

--probe-stage-frame usa PanelViewHost con ese archivo temporal y el Panel.qml original;
prueba render, valores efectivos y orden. El ctor acepta un destino antes de cargar, sin
cambiar el destino de una vista viva. La ruta normal sigue usando plasmashellrc relativo,
con kdedefaults. Adaptive se conserva pero ese probe lo rechaza por falta de backend;
--probe-stage sigue disponible para comprobar el containment original por separado.

El informe declara deferredViewSettings con valor/motivo y operationalVerified=false:
visibilidad/reservas, alineación, longitud proporcional sin geometría de salida, gap del tema,
comportamiento de docking para floating y Adaptive sin backend. Color/alfa y otros ajustes
heredados sin equivalencia establecida permanecen archivados. Ni guardar el flag ni cargar
un frame de ensayo valida el comportamiento completo de la barra anterior. Ocho casos con
dos paneles prueban tres modos fijos, límites/fallback de grosor y dos Adaptive rechazados,
archivo intacto, lectura posterior y alteraciones detectadas. Evidencia:
BREEZE_R4_VIEW_MIGRATION_RESULTS.json.

Antes de ejecutar la migración: resolver cada paquete nativo, crear Corona/Containment/Applet,
validar claves contra el esquema de destino y guardar mediante Corona. Archivar lo no mapeado;
no adivinar equivalencias de configuración. Comparar lectura posterior, mantener perfil antiguo
y marcar migración completada sólo después de confirmar el destino. Disposición y preferencias
comunes BWM no deben copiarse indiscriminadamente a Configuration de un widget. El programa
prepara un layout nativo aislado mediante Corona y verifica su reapertura; la activación y
rollback de una migración real siguen pendientes.

## Obtener nuevos y capacidades

Proveedor nativo instalado: `/usr/share/knsrcfiles/plasmoids.knsrc`, categoría
`Plasma 6 Extensions`, `KPackageStructure=Plasma/Applet`, `Uncompress=kpackage` y aviso
`ContentWarning=Executables`. Una futura acción del editor debe abrir el diálogo KNewStuff
con **ese** proveedor y refrescar el catálogo al terminar jobs/cambios. Esta conexión ya está
en `Catalog.getNewWidgets()` y la vista de prueba. Un único QFileSystemWatcher, con debounce,
observa directorios/metadatos; se probó el refresco con PackageJob sin reiniciar el catálogo.
La descarga por red desde el diálogo todavía no está verificada. La instalación/retirada local se prueba con kpackagetool6 y
raíces XDG desechables; no equivale a haber descargado contenido de la tienda.

Cada paquete debe declarar/mostrar capacidades comprobadas y fallos observados: imports QML,
APIs del shell, servicios de datos, KWin, entradas/salidas, acciones privilegiadas. Un import de
KWin no invalida todos los plasmoides; tampoco basta leer metadatos para certificar uno.
Andromeda carga en la prueba, pero consultar dispositivos/montajes/MPRIS sin bus produce avisos:
no se certifican sus lanzamientos, dispositivos ni acciones de sesión.

Temas globales: defaults se fusionan con kdedefaults; SVG los resuelve KSvg; decoraciones,
KDecoration; plasmoides, KPackage/Applet; fondos, su PackageStructure. `layout.js` es código:
no se evalúa al explorar o aplicar aspecto. Una disposición necesitará revisión/plan explícito,
API restringida y ensayo aislado; no ejecutar scripts nativos del escritorio a ciegas.

## Límite de la prueba offscreen y siguiente adaptador de Wayland

AppletPopup usa PopupPlasmaWindow. En las fuentes 6.7.5, updatePositionWayland() llama
PlasmaShellWaylandIntegration::setPosition: la prueba offscreen no verifica ese protocolo ni
anclaje en Hyprland. Antes de conectar al panel hay que adaptar la colocación a un protocolo
que ofrezca la sesión (por ejemplo layer-shell/xdg-popup), con monitor, escala, reservas y foco.
LayerShellQt es dependencia explícita del adaptador; su negociación Wayland sigue pendiente.
No se ejecuta KWin ni se registra un servidor Plasma parcial para satisfacerlo.

## Continuación 2026-11-13: superficies y staging nativo

`BwmSurface::configurePanel` inicializa una vista de prueba LayerShellQt; `PopupAnchor` enlaza
AppletPopup a esa salida y calcula márgenes/tamaño con `placePopup`. El modo normal no se
convierte a layer-shell. El adaptador usa Top/Overlay, OnDemand y zona -1, y recrea el rol al
cambiar de salida. La prueba lógica y de propiedades pasa; negociación/protocolo en Hyprland
pendiente. La inicialización de vista es para el ensayo, no una API de edición del panel R5.

`BwmMigration::stage/verify` materializa instancias mediante Corona en una carpeta nueva,
archiva el origen íntegro y relee en otro proceso. Ni `bar.plasma` ni el layout activo se tocan.
El informe conserva activationAllowed=false hasta completar disposición, fuentes de datos,
transición y rollback. El mapeo del reloj conserva el enum ToolTip/Always del port existente.

Los detalles, instalación de plasma-desktop confirmada, comandos y límites actualizados están
en las secciones de 2026-11-13 de BREEZE_R4_RESULTS.md; sustituyen los pendientes de implementación
de superficies/staging descritos en la primera versión de este documento.

### Panel original y capacidades (continuación tras instalar plasma-desktop)

El materializador crea **org.kde.panel**, aplica su esquema General/AppletOrder y deja que
Corona serialice. `--probe-stage` carga el QML original y verifica contenedores, orden y tamaño;
se vuelve a verificar el archivo tras ejecutar el LayoutManager original. Los ajustes con nombres
KDE se validan mediante el esquema de cada instancia. Los favoritos de Kickoff preparan una
importación al cliente KAStats del nuevo ID, cuyo efecto runtime todavía está pendiente.

`PanelSession` aloja un ConfigurationSession por ID; reutiliza un diálogo abierto y recrea
uno cerrado, liberándolo si desaparece el applet. Conecta la señal nativa configureRequested.
`--panel-preview ID` carga dos instancias en el panel original; `--layer-panel-preview ID`
selecciona el adaptador de superficie. Son modos temporales, sin arranque automático ni editor R5.
La configuración de un containment sin categorías explica el límite y bloquea guardar/defaults.

El catálogo conserva todas las entradas. `kind`/`containmentType` describen su naturaleza;
`catalogVisible` reproduce el filtro del explorador (NoDisplay, categoría y form factors).
Un containment también puede ofrecerse como widget: no se ocultan bandeja ni Folder View sólo
por tener ese tipo. Los metadatos provides/requiredExtensions se exponen sin inventar soporte.
`runtime` separa dependencias revisadas de paquetes unassessed y nunca marca operatividad por
mera instalación. La tabla de paquetes y fuentes está en BREEZE_R4_RESULTS.md.

Andromeda crea un PlasmaCore.Dialog aparte: se prueba su clic/apertura offscreen con el botón
original, además de sus páginas y configuración desde el panel. PopupAnchor sólo adapta los
AppletPopup del anfitrión en esa primera continuación; el registro descrito a continuación añade
Dialog del paquete sin acreditar todavía negociación/foco Wayland. El wrapper de compacta inicial no cubría
esa ventana. Las pruebas nuevas conservan esa distinción explícita.

`--theme-catalog` descubre Plasma/LookAndFeel con KPackage y lee defaults/layoutdefaults con
KConfig. Expone grupos y claves sin aplicar; distingue referencias SVG/decoración/fondo y los
archivos nativos de colores/vistas. Registra resolución propia/fallback y hashes de scripts
layouts/plasmoidsetupscripts con executeAllowed=false. No evalúa JS/QML de los temas para
inventariarlos ni infiere qué applets crearía un layout. Las opciones deben abrirse en el módulo
de cada componente; la tabla de rutas/gestores está en BREEZE_R4_RESULTS.md. Un tema desechable
con clave desconocida y script no ejecutable se instala, inventaría y retira en los ensayos.

### Ventanas propias: contrato pre-superficie

PackageWindows pertenece a PanelSession. Revisa QQuickWindow del proceso y asocia su contexto
`plasmoid` con un Applet del containment. No modifica ventanas sin esa asociación. AppletPopup
queda fuera de este registro porque tiene su adaptador declarativo. Un Dialog nativo oculto
y sin handle recibe un PopupAnchor independiente antes del primer show; un rol existente no
se sustituye en caliente. No se engancha a sockets ni se registra un compositor/servidor KDE.

Con visualParent se usa el ancla nativa del panel; sin ella se conservan x/y solicitadas por el
paquete y se limitan al área disponible. Ello mantiene las preferencias propias de Andromeda.
Los cambios de salida restauran la visibilidad de la ventana, sin tocar expanded de su applet.
capabilities informa status, placement y estado de preparación; waylandVerified permanece false.
No se anuncian como adaptados Window genérico, tipos no interactivos, anclas externas o ventanas
creadas/mostradas antes de registrarlas. Los tests incluyen estos límites y un Dialog sintético
de nombre desconocido. La lista de widgets no decide qué ventanas se aceptan.

ViewCorona enlaza containment→QQuickWindow→QScreen y suministra las APIs geométricas nativas.
Usa geometría lógica y QScreen.availableGeometry, notificando cambios; las reservas que Qt no
exponga requieren otra fuente del anfitrión. Los índices Qt son transitorios, no identidades para
persistir monitores. R5 debe consumir estos contratos sin confundirlos con un gestor de paneles
diario ni con aceptación real de foco/escala/negociación Wayland. El controlador añadido a
continuación cubre el ciclo de sus vistas en el auxiliar.

### Ciclo de vistas por salida y skin

PanelRuntime recibe una ViewCorona viva, el archivo nativo de preferencias y un mapa
containment-id→descripción de salida. El llamador carga primero el layout propietario y
conserva ese mapa fuera de la configuración de los applets; --preview-stage lo obtiene
del informe de migración ya verificado. No introduce otro appletsrc ni usa lastScreen/índice
Qt como identidad persistente. La persistencia/autoridad del mapa en la integración diaria
sigue pendiente; el JSON de bindings del test es sólo un fixture, no un nuevo estándar.

| API/estado | Contrato |
| :--- | :--- |
| setAssignments(map) | Debe cubrir exactamente los paneles vivos; rechaza conectores/entradas vacías antes de alterar vistas. Varios paneles pueden compartir salida |
| setSkin(plasma/retro/default) | Sólo plasma crea vistas; al salir retira vistas/configuración y ventanas propias, conservando containments/IDs/configuración. Otros valores se rechazan |
| reconcile / panels | Coalesce de eventos Qt, como mucho una vista por containment; informa visible, skin-inactive, output-unavailable, ambiguous-output-description o view-unavailable con motivo |
| view(id) | Acceso al PanelViewHost y su PanelSession dentro del proceso; no es IPC ni habilita servicios de plugins |
| Hotplug/cambio de borde | Retira la vista antes de que Qt la mueva a la salida primaria; recrea con el mismo containment al volver. Borde cambia el rol recreando sólo su vista |
| Resolución lógica | Relee el ámbito nativo Horizontal/Vertical correspondiente; no conserva preferencias de otra resolución como si fueran las actuales |

El resolvedor BwmOutput usa fabricante/modelo/serie de QScreen: descripción completa,
secuencia final modelo+serie (para diferencias en el prefijo del fabricante), o modelo único.
Normaliza espacios/caja y el prefijo desc:. No acepta subcadenas arbitrarias, ni la primera
coincidencia, ni nombres DP-/HDMI-. Duplicados o metadatos insuficientes dejan el panel en
espera; no se adivina otra salida. El mismo resolvedor reemplaza el de las vistas --output.

ViewCorona dispone de bind/unbind explícitos. Sustituir una ventana desconecta la relación
anterior: su destrucción no puede borrar la nueva. La retirada emite el índice anterior
screenRemoved de Corona y recalcula índices vigentes; las descripciones permanecen aparte.
PackageWindows.suspend colapsa applets y oculta sólo sus AppletPopup/ventanas con dueño
identificado; la retirada elimina ConfigurationSession sin Aplicar cambios pendientes.
Las ventanas se recorren con QPointer porque un callback de visibilidad puede destruir otra.

Corona debe vivir más que el controlador. El anfitrión diario deberá conservar el proceso
cuando no haya ventanas (quitOnLastWindowClosed=false) y llamar setSkin desde el gestor
común. PanelRuntime no instala autostart ni IPC de editor; la conexión explícita de prueba
se describe abajo. --preview-stage DIR ofrece
una vista layer-shell explícita, sin reservas, sólo con raíces XDG temporales; si ninguna
salida coincide termina con diagnóstico. --probe-stage-runtime usa el mismo coordinador y
produce un snapshot temporizado, sin acreditar negociación Wayland.

Las pruebas crean QScreen de fixture mediante QPlatformScreen/QWindowSystemInterface de
Qt 6.11.2, sólo con QPA offscreen y bus inaccesible. Comprueban dos salidas, conectores y
enumeración cambiados, hotplug/duplicados, ciclo de skins, borde, resolución lógica y
reapertura en proceso nuevo; no son monitores de Hyprland ni escala fraccionaria validada.
El widget de este ciclo es propio y desechable; la regresión de Andromeda conserva su
alcance previo. Evidencia: BREEZE_R4_RUNTIME_RESULTS.json. Pendientes producción/activación,
servicios y ventanas tardías no adaptados, reservas, escala, Wayland y aceptación con skins.

### Conexión explícita con el gestor de skins

El manifiesto Breeze declara hooks.skinChanged → scripts/panel-session.py. El módulo común
bwm_settings_hooks.skin_changed despacha los scripts confinados a las carpetas de ambas
skins, una vez por ID. El gestor llama before antes de modificar perfiles y after después
de la recarga del shell. Un fallo previo aborta las mutaciones e intenta after con la skin
anterior para recuperar el auxiliar; el descriptor del candado del gestor se cierra también
en esa salida. La política y los datos de Breeze permanecen en su script.

Sin registro explícito el script no crea archivos ni inicia procesos. Sólo una llamada
preview-isolated.py --native-panel --layer-panel --follow-skin --output DESCRIPCIÓN registra
la prueba en XDG_RUNTIME_DIR/bwm-plasma-host-preview/active.json. El registro privado 0600
identifica directorio temporal de control, token y PID+inicio de proceso. PID muerto/zombie/
reutilizado no autoriza órdenes. Registro duplicado rechazado: el nuevo auxiliar arranca
inactivo y sólo se activa después de registrarse, por lo que no aparece una segunda vista.

RuntimeControl usa un watcher de directorio y coalesce de 25 ms para control.json y ack.json
atómicos. Las órdenes versionadas son skin, stop y status, con token de sesión y revisión creciente
(entero representable exactamente en JSON). No ofrece dispatch arbitrario ni modifica las
preferencias nativas por este canal. El candado del lector y el del layout evitan dos dueños;
el publicador serializa transacciones, espera 1,5 s como máximo y verifica la confirmación.
Una revisión antigua o token ajeno no se aplica; el ack propio no provoca un bucle de escrituras.

Status obtiene una instantánea nueva sin setSkin, recargar preferencias ni recrear vistas.
El PID sólo permite localizar al auxiliar: la consulta exige un ack de su propia revisión,
con timeout y validación del contrato. El resultado incluye runtime (version 1,
scope isolated-preview), skin actual, panels, renderReady, replacementReady y blockers.
No se publica un archivo de salud que pueda seguir pareciendo válido tras un bloqueo.
Sin registro la consulta no crea archivos; un auxiliar antiguo sin contrato de estado
compatible se rechaza de forma explícita.

PanelViewHost.presentationState comprueba carga nativa, visibilidad/exposición, error de
scene graph y primer frameSwapped iniciado por beforeRendering de la misma generación de
superficie. Ocultación/reaparición, cambio de pantalla/tamaño, pérdida de exposición,
destrucción de superficie e invalidación de scene graph invalidan esa generación. Los
callbacks de render sólo retienen contadores atómicos compartidos; no acceden a objetos
QML ni a miembros derivados durante la destrucción. Un swap tardío del marco anterior
no confirma el nuevo. Un error de render exige recrear la vista para recuperarse.

PanelRuntime.readiness agrega las vistas y vuelve a comprobar la identidad de salida
al consultar, incluso antes de procesar el reconcile pendiente. renderReady sólo describe
el marco de Qt: no certifica presentación física del compositor, servicios del plasmoide,
posición correcta ni equivalencia visual. Los bloqueos incluyen salida no disponible,
vista oculta/no expuesta/sin frame y errores. replacementReady permanece false en este
anfitrión de ensayo, con isolated-preview-only/session-validation-pending y reservas ausentes
por defecto o no verificadas en el modo nativo explícito. No instala selección/autostart.
El futuro controlador de activación tendrá que comprobar además las capacidades de los
paquetes concretos y sus backends; este contrato no constituye un catálogo completo de ellos.

### Política nativa de visibilidad y petición de reservas

preview-isolated.py --native-policy --follow-skin activa explícitamente el adaptador para
un paquete/panel nativo o perfil existente. Sin esa opción el envoltorio elimina la variable
BWM_R4_NATIVE_PANEL_POLICY heredada. Sólo --serve-profile y --follow-panel-preview consumen
la capacidad; no se amplía a los probes/migraciones anteriores ni se instala autostart.

PanelViewSettings añade panelVisibility a las seis claves originales sólo en este modo.
Lee PlasmaViews/Panel <id>/panelVisibility y, cuando falta, el grupo de resolución heredado
de Plasma anterior a 5.9; escribe sólo la clave global, como PanelView 6.7.5. KConfig conserva
cascada XDG/kdedefaults, bloqueos y claves ajenas. El fallback también participa en la firma
optimista de concurrencia. Sólo se aceptan NormalPanel=0 y WindowsGoBelow=3; AutoHide/Dodge
se rechazan antes de guardar. El valor por defecto en este ensayo explícito es NormalPanel;
la previsualización común sigue con WindowsGoBelow y rechaza un NormalPanel almacenado,
incluido el fallback antiguo. Reabrir un perfil con NormalPanel requiere --native-policy.

BwmSurface pide la reserva mediante LayerShellQt::Window::setExclusiveZone(thickness).
La superficie conserva el espacio de flotación del SVG, pero la petición excluye ese padding,
como PanelView::updateExclusiveZone 6.7.5 fuera de edición. Con `zwlr_layer_shell_v1` v5 se
fijan los dos anclajes de la esquina, se pide el tamaño explícito sin margen final y se
designa el borde de reserva por separado. El anfitrión consulta la versión en el registro
de la conexión Qt activa. LayerShellQt 6.7.5 negocia hasta v5. Si la versión no está
disponible, se conservan los tres anclajes anteriores, con tamaño cero y margen final en
el eje estirado. §272 documenta por qué éstos acortaban un panel lateral con otra reserva
perpendicular en Hyprland 0.56.2. En v5 el mismo panel conserva su longitud solicitada.

La geometría de la salida/tamaño, visibilidad y reflow actualizan la petición. WindowsGoBelow,
ocultar/salir de skin o una superficie que no cabe retiran la reserva (-1). Longitudes fuera
de salida se rechazan antes de guardar. Los errores de política bloquean renderReady. El
anclaje nativo conserva su QScreen esperado: un screenChanged hacia el fallback de Qt retira
la reserva y oculta la vista antes de permitir un remapeo. PanelRuntime la recrea por la
descripción guardada; no se permite reservar transitoriamente la salida de respaldo. El
ámbito actual se limita a un panel nativo por salida: un binding con dos bloquea ambas vistas
con native-policy-output-conflict. El apilamiento/interacción con otros paneles existentes,
la posición global efectiva y el área útil real requieren aceptación Wayland; el adaptador
no deduce su éxito de las propiedades locales de LayerShellQt.

Capabilities/status distinguen nativeVisibilityPolicy, reservationRequested y
exclusiveZoneRequested de reservedArea/waylandVerified, que siguen false. Un pedido positivo
da reserved-area-unverified. replacementReady continúa false y no se retira el panel diario.
La migración sigue archivando la visibilidad diferida: habilitar este ensayo no certifica
su activación completa ni reescribe automáticamente staging o disposición.

El comprobador de reservas (§269) acepta varias descripciones de salida y un borde común.
Genera un perfil temporal mediante `--stage-migration` y `--import-profile`, con un panel
por salida. Lee el borde de cada containment en el estado del anfitrión y compara su
petición con el incremento correspondiente de `monitors.reserved` (izquierda, arriba,
derecha, abajo). Exige una capa de política nativa por salida solicitada, geometría e
identidad estables, y el retorno al estado original en todas las salidas. El informe
conserva los vectores antes, durante y después. Esto mide reservas en la sesión que
ejecuta la prueba. Las pruebas offscreen sólo verifican preparación y reapertura del
perfil, y las pruebas Python comparan observaciones simuladas.

Fuentes fijadas: distfiles de plasma-workspace 6.7.5 (PanelView::restore,
setVisibilityMode/updateLayerWindow/updateExclusiveZone) y layer-shell-qt 6.7.5
(QWaylandLayerSurface::setDesiredSize/setExclusiveEdge y XML incluido). Versiones/hashes y
ensayos en BREEZE_R4_RESERVATION_RESULTS.json. Al actualizar, repetir cuatro bordes,
longitud/flotación, ocultación, políticas/concurrencia/kdedefaults, dos salidas, conflicto
de múltiples paneles y lectura de otro proceso antes de verificar el compositor real.

Compatibilidad de identidad Qt Wayland 6.11.2: su QWaylandScreen aporta fabricante/modelo,
sin serialNumber. Si falta serie, OutputIdentity admite el prefijo exacto fabricante/modelo
de Qt más un único campo final de serie en la descripción Hyprland, exigiendo una única
coincidencia. No descarta series Qt conocidas ni escoge una salida entre duplicados. Esa
capacidad sólo identifica por fabricante/modelo únicos, no por serie física verificada.
Status expone qtPlatform/availableOutputs/serialAvailable para diagnosticar el caso real;
el nombre del conector es sólo diagnóstico y no reemplaza la identidad persistente.
La observación MSI de sesión añade una diferencia de fabricante: Co., Ltd. en Qt frente
a Co. Ltd. en la descripción Hyprland. Sólo las comas del prefijo completo del fabricante
se ignoran al comparar esa forma sin serie Qt. Modelo/serie conservan su puntuación y se
sigue rechazando cualquier selección ambigua. No se extiende la normalización a otros signos.

Aceptación local acotada (2026-11-14): el usuario observa en Hyprland reserva MSI inferior
44→92→44 px con una capa 640×48 y solicitud de 48 px; LG permanece en 44 px, registro/capas
retirados al finalizar. BREEZE_R4_RESERVATION_SESSION_RESULTS.json conserva ese ensayo real.
No cambia automáticamente waylandVerified/replacementReady ni certifica maximizado, coordenadas
Qt/popup o el resto de salidas/escalas/skins; se conserva el alcance de cada evidencia.

Before retira la vista al salir de Breeze; after permite su entrada con la configuración de
skin ya aplicada. La confirmación acredita el cambio de estado y retirada, no negociación
Wayland ni guardado final de disco. Stop retira vistas y cierra el bucle; el código de salida
comprueba después saveLayout/config.sync. El proceso permanece vivo aunque no tenga ventanas.
Ctrl+C lo gestiona el envoltorio mediante stop; el auxiliar ignora SIGINT y permanece en el
grupo del terminal, sin crear un demonio separado. Antes de limpiar el perfil temporal se
retira el registro y se espera que el publicador haya leído su ack: se corrigió una carrera
que borraba esa confirmación durante el cierre.

La previsualización conserva las raíces XDG y D-Bus desechables habituales. No sustituye
el panel de Quickshell ni se arranca automáticamente. Falta activar/recuperar un perfil diario,
persistencia/autoridad de bindings, cobertura de servicios y aceptación real de cambios de
skin en Hyprland. La prueba Qt invoca el hook Python común real con una salida QPA propia;
el smoke separado ejecuta el binario/envoltorio reales con salidas ausentes y comprueba
unicidad, vida sin ventanas, parada y Ctrl+C. Evidencia: BREEZE_R4_SKIN_CONTROL_RESULTS.json.

### Perfil nativo de ensayo y restauración por generaciones

ProfileStore importa una copia capturada de un staging verificado. Conserva completos
layout (serializado por Corona), plasmashellrc, legacy.json y report.json; añade bindings.json
con IDs nativos, descripciones de salida y hash del origen. El informe conserva la procedencia
inicial, no impone sus valores antiguos a un perfil editado. No serializa appletsrc a mano
ni transforma los ajustes de los plugins en preferencias BWM.

head.json selecciona una generación bajo generations/<id>. Es metadato de integración, no
un formato de configuración Plasma. Cada generación tiene nombres propios para los archivos
nativos. Un ProfileStore conserva el lease exclusivo durante toda la vida de Corona; otro
host/checkpoint rechaza ese perfil ocupado. Los bindings deben coincidir exactamente con
los containments de panel cargados mediante una Corona nativa sobre una copia de validación.
Inspeccionar el perfil no normaliza ni modifica sus archivos autorizados. El hash del origen
se contrasta con el archivo archivado y el informe; se conservan claves nativas y metadatos
desconocidos. Las versiones/rutas/IDs/symlinks inválidos se rechazan.

| Operación | Contrato |
| :--- | :--- |
| importStage | Copia a un directorio privado de preparación, verifica la copia y publica el perfil sin sobrescribir un destino existente |
| info / assignments / layoutFile / viewSettingsFile | Entrega metadatos y rutas nativas de la generación seleccionada; no certifica backends ni activa el panel diario |
| checkpoint | Tras flush y cierre de propietarios nativos, captura los cinco archivos, valida la copia e inventaría hashes; publica el directorio de snapshot completo |
| restore(snapshot-id) | Verifica inventario/hashes y datos nativos; copia a una generación nueva y cambia head.json atómicamente. No sobrescribe la generación anterior |
| recover(root, snapshot-id) | Toma el mismo lease sin abrir la generación actual; valida la copia explícita, conserva head anterior en recoveries y publica una generación nueva antes de cambiar head |
| serve-profile | Carga el archivo propietario con Corona y todos sus paneles con PanelRuntime; usa RuntimeControl y, al detenerse, sync/cierre de propietarios antes del checkpoint |

Conservar una ruta nueva al restaurar es necesario: un KSharedConfig antiguo puede retener
su nombre y escribir más tarde. El test mantiene uno vivo y demuestra que sólo altera la
generación anterior. Se retienen generaciones y snapshots; no hay limpieza automática.
Un restore interrumpido antes de seleccionar su head puede dejar una generación no elegida,
sin sustituir la vigente. El lease serializa escritores cooperantes; la comprobación
optimista de head detecta ediciones ajenas, no promete CAS global con escritores que ignoren
el bloqueo. Hashes son comprobación de integridad, no firma ni garantía ante corte de energía.

La recuperación explícita (§266) resuelve el caso que restore no puede abrir: head ausente,
JSON roto o generación actual incompleta. No elige «la última» copia: exige un snapshot ID
concreto. Usa el mismo lease antes de leer/verificar y conserva los bytes de head en
recoveries/<nueva-generación>/head.json (si existía), con un recovery.json que registra hash,
snapshot y nueva generación. Copia los cinco archivos a una ruta nueva y publica la
generación y el registro completos antes de seleccionar head con QSaveFile. Si falla antes
de ese último paso, no sustituye el head anterior; pueden quedar directorios no seleccionados.
Compara presencia/bytes de head antes de publicar para detectar escritores ajenos; no
promete exclusión frente a procesos que ignoren el lease. Conserva campos desconocidos de
un objeto legible y rechaza una versión explícita de head distinta de 1. No atraviesa aliases
ni reconstruye archivos faltantes de la copia. El CLI --recover-profile SNAPSHOT_DIR y el
envoltorio --profile DIR --recover-snapshot ID no arrancan paneles; el envoltorio usa QPA
offscreen sin acceso al compositor. Los registros de recuperación quedan en el perfil
original y no forman parte del historial de snapshots que copia exportToState.

preview-isolated.py --profile DIR --follow-skin reabre el perfil existente y conserva sus
bindings, IDs, widgets y opciones; no recrea dos widgets ni fuerza BottomEdge. Usa lookup XDG
de paquetes instalado, con las escrituras auxiliares/caché/runtime/D-Bus en raíces desechables.
El perfil seleccionado sobrevive al envoltorio, que sólo limpia esas raíces auxiliares. Los
paquetes/temas/activos externos siguen siendo recursos XDG, no se empaquetan en el snapshot.

La importación inicial conserva su raíz temporal y se puede exportar explícitamente al
estado XDG descrito abajo. Esto no constituye la selección/activación del panel diario.
Sustitución del panel/rollback de sesión,
autoridad diaria, servicios/controladores, reservas y aceptación Hyprland/escala siguen
pendientes. La prueba Qt añade/configura un widget propio mediante las APIs nativas, conserva
dos paneles y grosor/opciones independientes, restaura baseline/editado y relee en proceso
nuevo. El CLI/envoltorio reabre dos veces y rechaza perfil ocupado/copia alterada. Evidencia:
BREEZE_R4_PROFILE_RESULTS.json.

### Selección persistente y adquisición del perfil (§267)

ProfileSelection guarda intención en `panel-profiles/.selection/selection.json`, dentro de
la autoridad XDG existente, reservando un nombre que no puede exportarse como perfil.
Metadatos v1: revision entera 1–(2^53−1), profile (nombre simple o null) y sourceSha256 cuando
hay elección. Estado ausente equivale a revisión 0 sin perfil. Clear conserva el registro y
avanza la revisión para evitar reutilizar una revisión antigua tras vaciarlo. Campos ajenos
se conservan; metadata corrupta o futura se rechaza, sin reset ni elección automática.

Orden de leases no bloqueantes: selección → perfil anterior si difiere → perfil candidato.
Select verifica Corona/archivos nativos del candidato y exige la revisión esperada antes
de publicar con QSaveFile; repetir elección/procedencia no escribe ni avanza revisión.
Clear necesita sólo el lease del perfil anterior, por lo que admite head/generación rotos
o perfil ausente sin abrir Corona. Un anfitrión activo impide cambiar/vaciar la elección.
Las comparaciones optimistas de bytes detectan edición ajena; no son CAS global ni garantía
de durabilidad. Nombre+hash de procedencia no es identidad criptográfica de una instalación.

openSelected lee la intención y adquiere ProfileStore bajo el lease de selección; contrasta
procedencia y head antes de devolverlo. El llamador conserva el lease de ProfileStore toda
la vida de Corona. Así no hay una ventana entre consultar status y abrir una ruta obsoleta.
La elección no fija generación: restaurar/recuperar el mismo perfil conserva su nombre y
procedencia; la siguiente apertura toma sus archivos nuevos. Otro origen exige seleccionar
explícitamente otra vez. Info valida puntualmente si puede adquirir el perfil; ocupado/roto
se informa sin cambiar la elección. No confundir profileValidated con salud de proceso.

El CLI --serve-selected-profile reutiliza el ciclo nativo load/save/sync/cierre/checkpoint
de --serve-profile. preview-isolated.py --selected-profile --follow-skin pide ese modo sin
resolver previamente un nombre a una ruta. Sigue siendo preview registrado, no autostart.
profile-selection.py ejecuta consulta/select/clear offscreen sin sesión/compositor ni acciones.
No existe un controlador que retire la barra diaria a partir de esta elección; readiness
y los indicadores globales conservan sus bloqueos. Evidencia normal/ASan sobre fixtures y
CLI/envoltorios: BREEZE_R4_PROFILE_SELECTION_RESULTS.json. Logout/fallback diarios pendientes.

### Exportación a estado XDG persistente

exportToState(name) y --export-profile SOURCE NAME preparan el estado seleccionado y todos
los snapshots publicados bajo GenericStateLocation/bwm/plasma/panel-profiles/NAME. Qt respeta
XDG_STATE_HOME y usa ~/.local/state por defecto. Los nombres son componentes ASCII simples;
el destino existente no se sobrescribe. Se conservan IDs/descripciones/opciones y metadatos
desconocidos, con otra generación y rutas propias. La fuente permanece intacta; no se crean
hardlinks ni se mueven sus archivos. Las generaciones antiguas no seleccionadas permanecen
en la fuente, mientras el historial de snapshots completo permite restaurarlas por sus datos.

El directorio de publicación se prepara en el mismo filesystem del destino; tras validar
inventario/hashes/datos nativos de los snapshots, se publica por rename sin reemplazo. No
se publica un perfil si una copia del historial está alterada. Esto no es una firma ni
garantía de durabilidad ante corte de energía. La autoridad se limita a raíces temporales
o este subdirectorio XDG: no se habilita cualquier carpeta privada del sistema. Se rechazan
alias y directorios ajenos, y no se cambian permisos de directorios preexistentes; los
directorios de aplicación nuevos y el almacenamiento dedicado son privados.

preview-isolated.py --profile SOURCE --export-as NAME prepara el entorno auxiliar temporal,
exporta y termina sin registrar un preview ni crear vistas. Después puede reabrirse el
destino mediante --profile DEST --follow-skin, conservando caché/runtime/config auxiliar y
D-Bus desechables. La exportación no elige el perfil activo ni oculta el panel de Quickshell.

Las pruebas usan un XDG_STATE_HOME de fixture físicamente fuera de /tmp, en el directorio
tests permitido del repo. Eliminan la fuente temporal entera y reabren/guardan/restauran
el destino desde otro proceso. Verifican bytes nativos, historial, lease, nombres inválidos,
destino existente, carpeta fuera de autoridad y alias que intenta redirigir publicación.
No se escribe en el estado real del usuario ni se prueba un reboot. Evidencia:
BREEZE_R4_STATE_PROFILE_RESULTS.json. Pendientes selección/activación/fallback diarios,
servicios/controladores sin adaptar y aceptación Hyprland/escala/skins/KNS remoto.

### Sesión Wayland: posiciones, foco y ventanas no interactivas (2026-11-13)

Primera aceptación parcial en Hyprland (`BREEZE_R4_WAYLAND_SESSION_RESULTS.json`). Contratos:

- El auxiliar replica la preparación de plataforma de plasmashell 6.7.5 (`shell/main.cpp`):
  `QT_WAYLAND_DISABLE_FIXED_POSITIONS` sólo mientras se crea QApplication (no lo heredan los
  hijos) y `QQuickWindow::setDefaultAlphaBuffer(true)`. Sin ello Qt Wayland lleva cada ventana
  de primer nivel al origen de su salida y los paquetes calculan mal `mapToGlobal()`.
- La superficie de panel publica en QWindow la posición en la que el compositor la ancla
  (`bwmPanelRect`), es transparente y sin foco: `KeyboardInteractivityNone` y
  `WindowDoesNotAcceptFocus`, con OnDemand sólo mientras el containment está en
  `AcceptingInputStatus` (`setPanelAcceptsInput`), como `PanelView::refreshStatus`.
- PopupAnchor con posición pedida por el paquete: la limita al área disponible menos la franja
  del panel (`withoutPanelStrip`) y escribe la posición final en la QWindow, de forma que los
  Dialog compañeros que se colocan desde `root.x/y` la sigan. Con visualParent nada cambia.
- PackageWindows adapta también los Dialog solo salida/Notification/OSD/Tooltip del
  containment: capa Overlay sin teclado; no cambia su tipo, flags ni región de entrada.
- Cierre al pulsar fuera: `FocusGrab` (hyprland_focus_grab_v1) con el Dialog, el panel y los
  Dialog no interactivos visibles en la lista blanca; `cleared` oculta los Dialog con
  hideOnWindowDeactivate. Inerte sin el protocolo. Pendiente de contrato: desenfoque de fondos
  translúcidos y vista de fondo del panel. Al actualizar upstream revisar `shell/main.cpp`, `panelview.cpp` (refreshStatus,
  flags y capa), el tratamiento de posiciones de `qwaylandwindow.cpp` y la versión de
  `hyprland-focus-grab-v1.xml`.

### Área útil dinámica de ventanas BWM maximizadas (2026-11-14)

kwin_area.Runtime pertenece al watch único de kde-config-bridge, junto a kwin_rules.Runtime.
No ejecuta otro demonio, KWin, servidor ni compositor. El anfitrión nativo sigue siendo quien
pide la reserva; el puente observa el resultado real en monitors.reserved y ajusta sólo los
ejes de maximizado BWM. El estado de restauración, presnap y preferencias KDE no se escriben.

| Entrada/autoridad | Uso y límite |
| :--- | :--- |
| monitores por descripción + id efímero | monitor_box común calcula escala/giro lógico; se resta reserved real. El id sólo guarda el destino de esa operación, no identidad persistente |
| clients + bwm-max-v/h | Sólo flotantes mapeadas, workspace normal, sin fullscreen/minimización/snapping ni opt-outs |
| breezebars-csd v1 por dirección/PID | Bordes efectivos de marco/contenido; sin registro coherente se espera, no se inventa barra |
| kwin_rules.Runtime / resolve | Force (modo 2) de posición/tamaño/pantalla/escritorio tiene prioridad; cambios de reglas invalidan la firma |
| bloqueo del gestor de skins | Comprobación no bloqueante sin crear/modificar el archivo; Lua comprueba además skin/estado al ejecutar |
| Lua nativo 0.56.2 | PID, monitor, modo, etiquetas y elegibilidad se releen antes de resize/move; nunca foco, tags, fullscreen o traslado de workspace |

Se consulta como máximo cada 0,5 s mientras el puente no tiene reconciliación de archivos
pendiente. Las ventanas afectadas se agrupan hasta 16 en una petición con guardas individuales;
cada consulta/dispatch tiene límite de 2 s. Una firma identifica área/descripción, ejes,
workspace y revisión de reglas para cada dirección/PID. El éxito sólo se confirma al observar
la geometría esperada después. Hay tres intentos por firma y luego se detiene hasta cambiar
el área/elegibilidad/reglas; no se lucha indefinidamente contra restricciones ajenas. Errores
repetidos se limitan a una línea por 30 s. No se consulta decoración cuando no hay pendientes.
Los opt-outs son bwm-ignore-kwin-rules y bwm-ignore-maximized-area; usuario Lua sigue al final.

area-observer.json es estado privado de disponibilidad del proceso, no preferencias ni una
API de ejecución. Contiene versión, PID/inicio y fecha del baseline; se publica atómicamente
con 0600 tras una consulta válida. close sólo retira su propio marcador. restart usa stop/start
existentes del puente. El runner --refresh-area-watcher exige marcador nuevo y proceso vivo
antes de continuar; queda corriendo el mismo puente para las ventanas BWM maximizadas reales.

El fixture ahora existe/maximiza antes del panel. Mide primero el marco original, luego el
reajuste automático al añadir reserva, un maximizado explícito con panel, el reajuste al
retirar reserva y otro explícito sin panel. Las dos observaciones automáticas pasan
remaximize=False; la bandera dinámica exige ambas y la reserva/restauración correctas.
Se mantiene el éxito explícito separado y r4Complete=false. El runner sólo despacha órdenes
directas sobre su ventana; el observador puede reajustar otros máximos BWM como efecto previsto.

Revisar al actualizar Hyprland: contratos LuaWindow (pid, mapped, hidden, floating,
fullscreen/fullscreen_client, workspace, monitor, tags), LuaMonitor.id, resize/move y unidades
de monitors.reserved. Se consultó el código instalado 0.56.2; hashes y tests en
BREEZE_R4_AREA_TRACKING_RESULTS.json. Las pruebas ejecutan Lua con API simulada, no dentro
del compositor. Aceptación real de ambos sentidos todavía pendiente; no habilita takeover
del panel diario ni certifica escalas/bordes no medidos.

Aceptación posterior en sesión del usuario: BREEZE_R4_AREA_SESSION_RESULTS.json confirma
el contrato de aparición/retirada, ambos sin remax, para un fixture modo 3 en MSI inferior
escala 1/giro 0. Marco 1396→1348→1396 de alto y reserva 44→92→44, bordes autoritativos,
LG inalterado y limpieza correctas. No convierte el marcador en verificación, no cambia
replacementReady ni amplía la aceptación a ejes/otras salidas/bordes/escala/skins/hotplug.

### «Obtener nuevos» sin diálogo y contrato de páginas (2026-11-14)

- `BwmKns` (kns.cpp) usa `KNSCore::EngineBase` con `plasmoids.knsrc`, `SearchRequest`
  (Downloads/ExactEntryId) y `Transaction::installLatest/uninstall`: el mismo núcleo que
  `KNSWidgets::Dialog`. Un `QuestionListener` responde Cancelar/No. Instalación vía KPackage
  (`Uncompress=kpackage`) en XDG_DATA_HOME; sólo raíces temporales en el ejecutable.
- Visibilidad: un paquete instalado sólo aparece si su metadata declara `KPackageStructure`
  (KPackage 6.29 `readKPackageType`); igual que Plasma 6.7.5.
- ConfigurationSession sigue `AppletConfiguration.qml` 6.7.5: sólo claves del esquema; llama a
  `saveConfig()` de cada página antes de Aplicar; `loadConfig()` no lo llama Plasma y se ignora.
- Al actualizar upstream: revisar `installation.cpp` (preguntas), `transaction.cpp`, el filtro de
  `packageloader.cpp` y `AppletConfiguration.qml::saveConfig()`; repetir `kns-cycle.py`.

### Inventario de servicios antes de integración diaria (continuación §211)

PanelSession.widgetBackends (Q_PROPERTY, changed) consulta las instancias directas vivas en
orden nativo. Cada fila conserva id, package, failedToLaunch, launchError y runtime. La
evaluación procede de Catalog.runtimeAssessment(KPluginMetaData), la misma del catálogo:
version=1, status, operationalVerified=false, dependencies, declaredExtensions y evidence.
Las extensiones se conservan como las declara el paquete; no se interpretan como soporte.
La clasificación revisada de tareas/escritorios/Mostrar escritorio señala adaptadores
pendientes; los paquetes desconocidos siguen unassessed y visibles en el catálogo.

readiness/status añade widgetBackends, widgetBackendsVerified y
widgetInventoryScope=direct-panel-instances por panel. Sus blockers distinguen
widget-backend-adapter-required, widget-runtime-unverified, widget-launch-failed y
widget-inventory-unavailable-or-empty. Se consulta el estado vivo, sin ejecutar acciones,
alterar configuración ni crear servicios. Un inventario vacío o ausente no cuenta como
verificación.

Desde §274, la fila de `org.kde.plasma.systemtray` incluye `embeddedApplets` para sus
plasmoides nativos vivos. Plasma 6.7.5 los mantiene bajo el `CustomEmbedded` dentro del
panel. Cada hijo conserva su ID, paquete, estado de carga y servicio de activación declarado
por el paquete. Estos hijos quedan fuera del orden de applets directos. La lista tampoco
incluye iconos externos SNI, aplicaciones en segundo plano o plasmoides aún no activados.
Un checkpoint y un proceso nuevo comprueban que Corona conserva la configuración de un
hijo sin tratarlo como un panel independiente.

`r4-session-check.py --tray` consulta D-Bus para observar quién ofrece
`org.kde.StatusNotifierWatcher`. Lee las propiedades del nombre único, vuelve a comprobar
que conserva la propiedad y devuelve solo la clase de proceso y el número de iconos.
No autoactiva el watcher ni registra un host. El resultado confirma una lectura puntual
del servicio, sin acreditar menús, clics, iconos ni servicios de los plasmoides internos.

Este contrato es diagnóstico para el futuro controlador de selección/recuperación. No
instala dicho controlador ni autoridades diarias y no activa backends; replacementReady
sigue false incluso con renderReady=true. Para avanzar hace falta implementar y comprobar
los adaptadores concretos, servicios de hijos y ciclo de recuperación, con evidencia de
sesión. Test/evidencia: BREEZE_R4_BACKEND_INVENTORY_RESULTS.json.

### KWindowSystem: puente experimental de escritorio común (§212)

El controlador original compilado ShowDesktop de plasma-desktop 6.7.5 consulta org.kde.KWin
si existe; si no, llama a KWindowSystem. El ensayo conserva ese módulo original. La acción
Minimize All del mismo widget es otro controlador, basado en TaskManager, que sigue sin
adaptador. Tampoco se implementa aquí el movimiento visual de Peek (R7).

KWindowSystem 6.29.0 selecciona plugins estáticos antes que dinámicos (pluginwrapper.cpp).
El ejecutable enlaza un plugin estático propio por ese contrato; no instala módulos en Qt
ni entra en Hyprland. Delega createEffects/createWindowShadow/createWindowShadowTile y los
métodos de activación, tokens, export y etiquetas al plugin KDE original de la plataforma.
Sólo showingDesktop se adapta cuando el preview habilita expresamente las acciones. Los
headers private/V5 vienen del sistema; CMake exige 6.29.0 EXACT para no cargar otra ABI.
La capa estática y el controlador se prueban offscreen; la delegación de funciones gráficas
Wayland no está validada en sesión.

| Petición nativa | Adaptación dentro del auxiliar |
| :--- | :--- |
| showingDesktop() | Estado común bwm-show-desktop.json, no un estado por widget |
| setShowingDesktop(true) | Python kwin-window.py show-desktop enter (idempotente) |
| setShowingDesktop(false) | Mismo gestor con leave; conserva la implementación común |
| showingDesktopChanged | Notificación al KWindowSystem original tras leer el estado y terminar el gestor |

DesktopBridge limita a un QProcess y conserva la última petición pendiente; no lanza una
tarea por evento consecutivo. El gestor vive en un grupo propio y tiene timeout de 5 s;
timeout/cierre terminan sólo ese grupo y sus hijos. Desconecta callbacks antes de destruir
el puente. Poll de archivo cada 250 ms, sin nuevo inotify/servidor. Exige runtime privado
propio/canónico, estado regular propio ≤1 MiB y array de direcciones; JSON/alias inválidos
no pueden iniciar una acción. No publica fin mientras el gestor aún restaura ventanas.

preview-isolated.py --builtin ID descubre recursos instalados, incluidos applets compilados,
con datos/configuración temporales. --desktop-actions exige --follow-skin, Breeze activo,
runtime privado e IPC accesible, fuerza Wayland y autoriza explícitamente minimizar/restaurar
ventanas reales. Los probes/export/KNS eliminan los flags heredados; la entrada C++ sólo los
admite para follow-panel-preview/serve-profile. No se registra org.kde.KWin ni otro servicio.

Prueba: el plugin Plasma nativo se carga antes de instanciar dos ShowDesktop originales;
KWindowSystem conecta ambos con el gestor Python real y un hyprctl de fixture sin IPC. El
driver comprueba la restauración final de la ventana ficticia, setters repetidos y estado
compartido. Incluye rechazo de estado inválido y terminación de hijos de una acción que
excede el timeout. Root QML original y sus dos acciones se cargan, sin prometer una
fullRepresentation separada: este applet dibuja en su PlasmoidItem raíz.

operationalVerified/replacementReady siguen false. Faltan sesión real, modelo TaskManager,
efecto Peek y recuperación/autoridades diarias. BREEZE_R4_DESKTOP_ADAPTER_RESULTS.json guarda
procedencia, hashes y resultados. Al actualizar revisar showdesktop.cpp, ambos Controller,
pluginwrapper.cpp, kwindowsystem_p.h y métodos delegados; no basta cambiar la versión EXACT.

## 2026-11-14 — confirmación manual del botón nativo en Hyprland

El usuario confirma explícitamente que pulsar el botón del panel temporal minimiza las
ventanas y volver a pulsarlo las restaura. El log confirma registro del preview en MSI
por descripción. Evidencia: BREEZE_R4_DESKTOP_SESSION_RESULTS.json. Esto valida manualmente
el ciclo de clics del adaptador común, sin nuevas acciones del asistente ni telemetría de
geometría/foco/z-order. No se deducen ambas instancias, otros monitores o limpieza completa.

Persisten los avisos de D-Bus aislado, TaskManager sin protocolo, Toolbox y KWindowShadow
para tooltips; no se presentan como corregidos. La acción secundaria TaskManager, el efecto
Peek y las autoridades/recuperación diarias siguen pendientes. No se habilitan por esta
confirmación operationalVerified/replacementReady globales ni se da R4 por completada.

## Fuente de ventanas TaskManager opt-in (§215, 2026-11-15)

Se enlaza LibTaskManager 6.7.5 EXACT y KF6 Service. BwmTaskSource deriva de
AbstractWindowTasksModel; BwmTaskBridge recorre QAbstractProxyModel y
QConcatenateTablesProxyModel hasta WindowTasksModel y llama su setSourceModel heredado.
Sólo sustituye la fuente estándar TaskManager::WaylandTasksModel (o null en las pruebas);
conserva QPointers y restaura la fuente previa cuando la vista desaparece. Las fuentes de
terceros no se reemplazan. No se instala ningún plugin Qt global, servidor o parche de KDE.

native-tasks.py produce protocolo JSON versión 1 con ventanas/estados/identidad y delega
las cuatro acciones permitidas en kwin-window.py. Dirección, PID e inicio Linux identifican
la fila; la guarda final existente del compositor verifica dirección/PID. Metadatos de apps
proceden de TaskTools y KF6 Service. Los snapshots son validados íntegramente antes de
mutar filas; cambios parciales usan dataChanged por roles. Desaparición o cambio de identidad
invalida índices/UUID. No se reinicia la fuente en cada sondeo.

Un puente compartido por proceso, sondeo 750 ms, como máximo un snapshot y una acción en
paralelo, cola 64 y timeout 8 s. Cancelación mata sólo grupos de hijos propios. El diagnóstico
readiness.taskSource no acredita un widget: snapshotAvailable es la última respuesta válida,
pendingActions excluye el proceso en curso y lastError puede ser histórico. Faltan bloqueo
común entre llamadores de mutaciones y quiescencia verificada durante transiciones.

--task-actions es un experimento de preview, no una autoridad de selección diaria. Necesita
Breeze/Wayland/IPC y expone al helper las rutas reales de config/runtime; el proceso del
widget conserva config/data/cache/DBus aislados. Las otras herramientas limpian estos flags.
VirtualDesktopInfo, filtros/pager, menús completos, MinimizeAll secundario, lanzamientos y
acciones restantes siguen pendientes. No activar takeover ni prometer el widget completo.

Para actualizar upstream: revisar WindowTasksModel::roleNames (usa su backend original),
initSourceTasksModel y su propiedad compartida; AbstractTasksModel/AbstractTasksProxyModelIface
para roles y encaminamiento de acciones; proxies de agrupado/filtro/concatenación y
TaskTools para apps. Comparar también menús QML y VirtualDesktopInfo, no sólo headers.
No retirar EXACT sin recompilar y repetir la regresión nativa. El test offscreen proporciona
una tabla vacía de una columna sólo a StartupTasksModel sin backend; no usar ese fixture
como implementación ni evidencia de delegados Wayland. En Wayland todavía debe probarse la
cadena de roles/QML, fuentes de terceros, vida de vistas, acciones y recuperación con ventanas
propias. Hashes de fuentes consultadas y pruebas en BREEZE_R4_TASK_SOURCE_RESULTS.json;
matriz detallada en BREEZE_R4_RESULTS.md.

## Coordinación de acciones y control de retirada (§216)

native_guard.py aporta un único flock por runtime a las dos entradas experimentales del
auxiliar. kwin-window.py --native-serialized envuelve la ejecución existente y relee Breeze;
--expected-generation comprueba el inicio Linux después de adquirir el bloqueo. No se cambia
el comportamiento de las entradas diarias sin ese flag. Los datos de preferencias siguen
en sus formatos KDE/BWM existentes; el lock vacío no es una autoridad de configuración.

PanelRuntime.setSkin suspende ambos tipos de puente antes de retirar vistas. Si hay proceso
en curso, devuelve quiescing y RuntimeControl mantiene la revisión pendiente, releyendo a
los 25 ms sin ack. Las colas se descartan y se cancelan sólo snapshots; las mutaciones se
dejan terminar. Una nueva orden plasma puede reanudar el estado anterior si el publicador
agota su timeout y el gestor de skins cancela el cambio. No aumentar los timeouts del hook
ni publicar ack de retirada sólo porque la superficie se haya ocultado. readiness informa
nativeActionsQuiescing y el puente de tareas sus procesos en vuelo/quiescencia local.

La exclusión externa usa descriptor de directorio canónico/privado, O_NOFOLLOW/CLOEXEC,
archivo regular propio 0600 sin enlaces y espera máxima 1 s. Nunca unlink del lock: se
libera por cierre del descriptor. Probar con dos procesos y muerte del propietario, no sólo
con mocks de flock. Sólo sincroniza participantes nativos; las entradas diarias aún faltan.

VirtualDesktopInfo upstream mantiene un Private* estático sin setter/factoría pública;
currentDesktop/ids/names son READ y los métodos no son virtuales. TasksModel usa además ese
proveedor internamente para orden, y TaskFilterProxyModel para escritorios por pantalla.
Un reemplazo del objeto QML aislado no cubriría estos contratos. La integración futura
necesita una interfaz de proveedor coherente en esos consumidores, o el protocolo nativo
correspondiente, con alcance/ABI revisados. No modificar punteros privados ni interponer
símbolos duplicados de libtaskmanager. No declarar soporte por instalar el módulo QML.
Procedencia y pruebas en BREEZE_R4_NATIVE_TRANSACTIONS_RESULTS.json; límites y tabla completa
en BREEZE_R4_RESULTS.md. El proveedor y el widget completo siguen pendientes.

## Proveedor por protocolo nativo (§218)

La alternativa al backend privado de VirtualDesktopInfo es servir el protocolo que éste
consume. bwm-plasma-desktops separa DesktopProtocol (global v4 sobre wl_display existente),
workspaceSnapshot (proyección de datos sin configurar el sistema) y plugin.cpp (lectura/acción
Hyprland). El anfitrión de widgets no enlaza este servidor en producción: sólo su fixture de
BUILD_TESTING lo usa. La extensión opcional se construye aparte y empieza deshabilitada,
sin loader o hook de arranque. No se instala ni carga en esta entrega.

DesktopProtocol valida un snapshot completo antes de emitir cambios, conserva IDs y envía
propiedades/eventos done por las versiones pertinentes. Los recursos de escritorios retirados
reciben removed y se destruyen; un ID recreado obtiene recurso nuevo. Rechaza duplicados,
IDs inválidos, salidas ambiguas y límites de recursos. Las peticiones no fabrican estado:
el backend debe publicar su lectura autoritativa. Crear/quitar se deniegan y permanecen fuera
de capacidades; el protocolo no ofrece un flag universal para ocultar sus controles.

workspaceSnapshot une el contador BWM válido con workspaces vivos/activos, ordena por ID
normal y omite especiales/99. El plugin lee sólo config común y State/FocusState, coalesce
eventos y reconcilia a 500 ms sin inotify nuevo. Las activaciones usan Config::Actions en
el event loop. No trasladar workspaces ni saltarse asignaciones: por salida sólo se acepta
un desktop materializado ya en ese monitor y se enfoca el monitor mediante la acción común.
Faltan coordinación con la barrera del host, preflight de proveedores en conflicto, política
create/remove y aceptación real. Nunca bloquear el hilo compositor en el flock del gestor.

El núcleo y el frontend enlazado llevan -fno-gnu-unique; verificar readelf, no sólo el flag
del target final. ABI Hyprland guardada por hash al inicializar. XML KDE privado fijado por
SHA256, no sólo versión; revisar KWin plasmavirtualdesktop y consumidores de plasma-workspace
antes de actualizarlo. README del componente describe construcción/actualización y límites.

El test usa los originales VirtualDesktopInfo C++/QML, filtro por pantalla, orden inicial
TasksModel y nombre de rol display en un Instantiator de prueba. Se conecta por socketpair
Wayland heredado a un fixture data-only, sin conexión al usuario ni capacidad de dibujar
superficies. No usa el workaround StartupTasksModel offscreen de §215. Cubre retiro/recreación
sin parchear KDE. Es evidencia del protocolo/consumidores, no del frontend Hyprland ni de
Task.qml pintado. BREEZE_R4_NATIVE_DESKTOPS_RESULTS.json conserva fuentes y resultados.

## Barrera de activación por wl_client (§219)

El protocolo propio bwm_plasma_desktop_control_v1 comparte display/conexión con el protocolo
KDE; no es otra autoridad de preferencias. DesktopProtocol registra Peer mediante listener
de destrucción de wl_client y concentra la cola (32) en el núcleo real, eliminando la cola
duplicada del frontend. Una petición captura recurso + serial de vida + ID; recurso/peer
retirados cancelan su trabajo. No heredar permisos por dirección reutilizada de wl_client.

| Evento | Estado de esa conexión | Confirmación |
|---|---|---|
| Conectar/bind de control | Pausada; lectura continúa | availability informa backend, sin implicar operatividad |
| set_paused(serial,0) | Puede activar si el backend está disponible | Ack correlacionado, antes de mostrar el modo requerido |
| set_paused(serial,1) | Cola propia cancelada, nuevas activaciones rechazadas | Ack después de todo callback previo del mismo event loop |
| Destruir propietario | Pausada hasta rebind/resume | No resucitar permiso automáticamente |
| Desconectar | Peer y cola eliminados | Nuevo cliente empieza sin autoridad |

El idle de DesktopProtocol llama Config::Actions a través del frontend síncrono. No esperar
procesos/flock ni reentrar en el loop desde ese callback. Una pausa no puede intercalarse
con la ejecución síncrona; sólo se recibe después, y su ack no deja acciones propias futuras.
Las conexiones ajenas no se revocan. Esto no es exclusión global de acciones BWM.

NativeDesktopControl usa la extensión Qt generada con serial/estado y deadline de 1 s.
PanelRuntime lo crea como hijo, suspende también gestores locales y RuntimeControl espera
ambas barreras antes del ack de revisión. Pérdida/indisponibilidad retira vistas y suspende
colas; recuperación exige confirmación nueva. La entrada requerida falla si no hay control;
la ausencia del propio proveedor permite retirada/salida, evitando atrapar el cierre.
RuntimeControl conserva un arranque con revisión inicial pendiente. Status expone el control
sin convertirlo en certificación global; no se amplían deadlines del hook.

Qt generado init(nullptr) NO desinicializa: intenta instalar listener sobre null. Tras
retirada se destruye sólo el proxy local y se recuerda su liberación, sin acceso a miembros
privados; rebind restablece el recurso nuevo y evita doble destrucción. Mantener la prueba
ASan de pérdida/reaparición. La simulación de bloqueo está sólo en test-display por su pipe;
no bloquear ni enviar señales al compositor del usuario como prueba de este caso.

--native-desktops exige preflight de diagnóstico ya habilitado y contrato Wayland real;
no activa/configura/carga plugins. El código de producción nunca enlaza el servidor de
fixture en el host. Aceptación real/arranque/conflictos y menú/capacidades restantes quedan
pendientes. BREEZE_R4_DESKTOP_CONTROL_RESULTS.json conserva evidencia y límites.

## Capacidades del menú TaskManager original (§220)

BwmTaskSource expone un rol numérico propio Qt::UserRole+4096, mapa versionado con provider,
identity y capacidades keepAbove/keepBelow/excludeFromCapture. Las tres son false; no amplía
las cuatro operaciones admitidas. El rol atraviesa los proxies KDE por su API data(), sin
alterar roleNames del backend privado. Para un grupo, TaskMenuPolicy verifica recursivamente
cada hijo; no confía en la capacidad del primer miembro que devuelve el proxy agrupador.

TaskMenuPolicy se aloja en BwmTaskBridge. Su eventFilter sobre QEvent::Show reconoce QMenu,
QMenuProxy y el contexto original con backend/mpris2Source/modelIndex, comprueba pertenencia
a una raíz registrada por padres QObject/QQuickItem y exige el proveedor BWM. La resolución
QQmlContext::resolvedUrl de ContextMenu.qml permite leer tanto archivo como qrc. Su SHA256
revisado se declara en CMake; discrepancia/fuente ausente deshabilitan el menú afectado.
Esta dependencia privada requiere revisión al actualizar KDE, aunque Qt use APIs públicas.

Los tres controles no acotados por roles upstream se reconocen por el icono literal del
QMenuItem propietario. No se interpreta el texto traducido ni el icono de QAction de apps.
Una máscara QActionGroup pública, no exclusiva y por acción, deshabilita sin sobrescribir
bindings QML. Para retirarla se activa primero el grupo y después removeAction, pues Qt no
recalcula enabled sólo al quitarlo. Esto conserva el último estado explícito de la acción.
Un grupo previo ajeno no se reemplaza: bloquea el menú y deja diagnóstico. Los demás controles
conservan sus roles/handlers KDE; no se prometen operaciones sin implementación.

Suspender cierra menús y retira máscaras antes de confirmar retirada. Las señales estructurales
del modelo cierran menús con índices potencialmente obsoletos. Bindings y máscaras usan
QPointer, se desconectan antes de restaurar y evitan llamadas a propietarios QML parcialmente
destruidos. La recursión de submenús tiene guardia. menuPolicy en taskSource informa contadores,
suspensión y lastError, siempre operationalVerified=false. No es un certificado de widget.

Test-taskmenu usa el menú/QML instalados sobre modelos KDE y BWM originales en offscreen:
restricciones, petición individual/agrupada, acciones ajenas y restauración/cierre comprobados.
Task.qml avisa de roles undefined en offscreen y usa el fixture StartupTasksModel descrito en
§215: no afirmar rendering ni aceptación Wayland. Hashes y límites en
BREEZE_R4_TASK_MENU_RESULTS.json. Para actualizar: revisar ContextMenu.qml y QMenuProxy/
QMenuItem, su propiedad action/propietarios, roles y handlers; actualizar hash sólo tras esa
revisión, reconstruir y repetir normal/ASan. Después validar el menú real en Hyprland antes
de considerar soporte completo o sustitución diaria.

## Estado deseado y confirmación de pantalla completa (§221)

El snapshot interno versión 1 añade fullscreenable opcional booleano; ausencia es false y tipo
inválido rechaza el snapshot completo. La autoridad de elegibilidad es el gestor Python
existente: normales/mapeadas/no ocultas/no fijadas/no minimizadas. El helper reutiliza su
comprobación de minimizado al construir cada fila. IsFullScreenable refleja esa capacidad y
requestToggleFullScreen no emite si falta. Cuando está disponible emite action=fullscreen,
state=!fullscreen e identidad completa. Los proxies/handlers originales KDE se conservan.

El helper exige state de tipo bool, revalida contra clientes recientes y entrega
fullscreen --state on|off al gestor con --native-serialized, --expected-generation y --pid.
Dentro del bloqueo se releen skin/PID/inicio/capacidad. El setter nativo se diferencia de la
llamada diaria sin opciones, que conserva toggle. No se añade archivo de preferencias o estado
propio, ni se cambia el contrato de maximizado por ejes/restauración BWM.

native_fullscreen_lua ejecuta guardas de skin/PID/mapped/hidden/pinned/workspace y el setter
set/unset en un único paso del event loop. El Lua binding instalado devuelve result.ok y
w.fullscreen lee el modo interno síncrono. Sólo si ambos coinciden con lo pedido retorna el
recibo fijo. El proceso exige ese valor exacto mediante hyprctl repl con timeout 2 s; un ok
genérico, recibo mezclado con error, éxito sin cambio o excepción falla. No usar eval o el exit
status para inferir este resultado: repl expone el retorno, eval no. No esperar procesos o
bloqueos desde Lua/hilo del compositor. El recibo verifica modo interno, no frames/geometría.

Idempotencia y roles se prueban en BwmTaskSource, dos TasksModel y el menú instalado; el fixture
IPC ejecuta el Lua real en una tabla hl de prueba con estado, sin compositor. Lua se resuelve
en CMake únicamente dentro de BUILD_TESTING y se pasa al runner mediante --lua/BWM_R4_TEST_LUA.
No se usa ese intérprete desde el código de producción. El test offscreen no acredita el
pintado del Task.qml. Fuentes exactas/contrato/evidencia en BREEZE_R4_FULLSCREEN_RESULTS.json.

Al actualizar Hyprland revisar HyprCtl repl, ConfigManager::eval, hl.dispatch, resultado ok,
LuaWindow fullscreen/pinned y hl.window.fullscreen set/unset. Revisar también el controlador
para ventanas fijadas: por ahora quedan fuera de capacidad, aunque allow_pin_fullscreen se
habilite. Ampliar ese alcance requiere nueva prueba de estado/foco/restauración. Mantener
la aceptación real pendiente, no subir readiness por el recibo o por los tests aislados.

## Caché de aplicaciones de la fuente de tareas (§222)

AppData de cada fila procede de TaskTools/KService. El snapshot IPC sigue siendo autoridad
para identidad y estado de ventana; no es autoridad del nombre/icono/lanzador de la aplicación.
Anteriormente el cache sólo se recalculaba al cambiar appId, de modo que instalar/actualizar
un .desktop dejaba datos antiguos hasta recrear la ventana. El nuevo contrato separa ambos.

BwmTaskSource escucha KSycoca::databaseChanged y reinicia un singleShot de 100 ms, como la
fuente Wayland de Plasma 6.7.5. Al vencer marca AppData dirty en las filas existentes y emite
los seis roles que usa. La consulta data() resuelve de forma diferida sólo roles de aplicación;
los demás roles no fuerzan lecturas de servicios. Un cambio de appId del snapshot sí resuelve
su identidad nueva por la vía existente y limpia dirty. No se reemplazan filas ni UUID y no
se añaden capacidades de ejecución por descubrir un servicio. Fuente vacía no emite rango.

QObject/QTimer acotan las conexiones a la vida de la fuente. Se comparte la vigilancia del
singleton KSycoca del hilo GUI, sin QFileSystemWatcher propio ni uno por fila. La suspensión
puede vaciar filas sin convertir ese refresco de lectura en una acción de ventana o bloqueo
para la barrera. La lógica no crea procesos/servidores de escritorio ni preferencias nuevas.

El test instala/actualiza/retira/reinstala sólo una entrada .desktop propia en XDG temporal,
reconstruye la base KDE real y espera su notificación de archivo. Verifica dos fuentes,
colores de QIcon, fallback nativo, índices y vida durante cambios. No se inyecta la señal ni
se ejecuta Exec. El runner elimina KDESYCOCA y el test exige cache/data privados; CMake busca
kbuildsycoca6 sólo en BUILD_TESTING. Mantener estas guardas al ampliar la prueba.

La señal anuncia una base actualizada, no cualquier escritura de .desktop. El ensayo
reconstruye esa base explícitamente; no certifica la detección de todos los instaladores.
El preview usa su cache aislado. No se añade aquí un monitor de instalaciones ni se cambia
la autoridad del cache diario: separar ese ciclo del refresco de consumidores.

Al actualizar KF6 Service revisar databaseChanged, auto-rebuild y vida del cache; contrastar
la invalidación de AppData en WaylandTasksModel de la versión fijada. No llamar al reconstruidor
desde cada fila o snapshot ni convertirlo en otro demonio. BREEZE_R4_TASK_METADATA_RESULTS.json
conserva procedencia/evidencia y fallo previo. No equivale a render del Task.qml o catálogo KPackage.

## Inventario de globals y asociación del control (§223)

NativeDesktopRegistry crea wl_registry y wl_display_sync sobre el wl_display de Qt público;
la cola por defecto se despacha en GUI en Qt 6.11.2, contrastado con qwaylanddisplay.cpp.
No se crean conexiones/servidores ni se toca wl_display_set_global_filter. Se conservan sólo
los globals KDE management/control BWM (máximo 64); sync delimita inventario inicial y las
notificaciones posteriores lo mantienen. La guarda sólo conoce lo visible para ese cliente.

Control BWM v2 añade desktop_global al interface con nombre histórico _v1. Al bind, el núcleo
usa wl_global_get_name(global,client), API pública desde Wayland 1.22. El cliente exige un
management >=4 y un control >=2 y compara sus nombres de registry con ese evento. No envía
resume antes de esa prueba y de availability. Serial/deadline de la barrera continúan activos;
el plazo del inventario no se transforma en éxito por una respuesta tardía. Una revisión
nueva permite reintentar. El diagnóstico hyprctl y el launcher exigen barrierProtocolVersion=2.

NativeDesktopControl posee el proxy generado de control y lo enlaza explícitamente desde su
registro. Conserva su ID al aparecer/desaparecer otro control. No usa QWaylandClientExtension
para ese recurso: Qt 6.11.2 invalida por interfaz en globalRemoved, no por ID. Al quitar el
control realmente enlazado se destruye su recurso y se revalida cualquier reemplazo.

VirtualDesktopInfo original también usa esa extensión y conserva estado privado compartido.
Detectar dos management KDE marca un bloqueo de proceso: se permite retirar, pero reanudar
exige un auxiliar nuevo. Un objeto nuevo en el mismo Qt app no basta. La prueba observa lista
vieja de 0 tras el conflicto frente a 4 en un proceso nuevo, sin modificar KDE. No declarar
solucionado el backend nativo por restaurar solamente el proxy del control.

El runtime suspende gestores y oculta vistas/popups conocidos antes de volver al despacho
Wayland. El desmontaje sigue diferido. bwmControlWithdrawn identifica sólo esa ocultación;
si reconcile encuentra otra vez el control listo, vuelve a mostrar la misma vista y limpia
la marca. No se restauran ocultaciones manuales. Configuraciones no se aplican al retirar.
Sólo la rama de visibilidad Qt tiene prueba offscreen; no certifica foco/input/reservas reales.

El destructor del núcleo cancela colas y deja controles retirados con userdata=null. Sus
handlers de pausa no hacen nada; destroy sigue válido. El recurso vive hasta destroy o
wl_client disconnect, cubriendo peticiones en vuelo. Mantener el módulo cargado durante la
sesión: no se vuelve seguro hot unload por dejar recursos inertes. Clientes v1 siguen probados,
pero el host actual necesita v2. El XML propio cambia; el pin del XML privado KDE no cambia.

Revisar al actualizar Qt: default queue, NativeInterface y globalRemoved de consumidores;
Wayland: nombre visible por cliente y vida de controles; Plasma: backend compartido de
VirtualDesktopInfo. Repetir prueba de conflicto, timeout/ack tardío, proceso fresco y v1
normal/ASan. El arbitraje que evita publicar duplicados en el frontend Hyprland sigue siendo
otro contrato pendiente. Evidencia BREEZE_R4_REGISTRY_RESULTS.json. Sin despliegue/takeover.

## Arbitraje del proveedor sobre el display existente (§225)

DesktopProvider (provider.cpp) es la capa del frontend y del fixture arbitrado alrededor
de DesktopProtocol. Separa snapshot deseado, petición enabled y disponibilidad publicada.
El observador privado usa libwayland-client dentro del loop libwayland-server; no es otro
servidor ni otra autoridad de workspaces. Tres fences asíncronos separan inventario, elección
del claim y comprobación del par publicado. No se modifica el filtro global del compositor.
El cliente KDE sigue intacto y mantiene su propia guarda/handshake por conexión.

La retirada es monotónica durante esa vida del módulo: availability=false, cancelación de
trabajo, control inerte y wl_global_remove, conservando el único core y los recursos/ofertas.
No volver a publicar mientras sobreviven referencias; recuperación por nueva generación no
implementada. No desencadenar hot unload para recuperar. Configuración de bajo nivel disabled
por defecto y arranque/integración diarios pendientes, sin KCM que prometa reactivar en vivo.

El alcance es el inventario visible del observador. Claims cooperantes evitan la carrera
entre instancias BWM; módulos ajenos y filtros distintos pueden producir duplicación
transitoria. El diagnóstico lo declara; no se elimina la guarda independiente del auxiliar.
La tabla de efectos/pruebas/límites está en BREEZE_R4_RESULTS.md §225 y los resultados exactos
en BREEZE_R4_PROVIDER_ARBITRATION_RESULTS.json. Sin cambios de formatos KDE, layouts, R5 o R7.

## Vida del módulo y reloj de arranque (§226)

La inicialización del observador es diferida: snapshot+opt-in → idle del loop existente →
peer/registry/fence/plazo. Disabled no posee peer ni reloj. Cancelar ese idle no retira una
generación porque todavía no se creó el claim. Sigue un solo intento tras crearlo.

Retirada y destrucción definitiva son contratos distintos. withdraw conserva el core y
sus recursos; el destructor del core/proveedor destruye TODOS los recursos cuyos handlers
o wl_interface pertenecen al módulo, incluidos controles sin Peer::control y recursos del
claim. Retirados siguen asociados al core y niegan por withdrawn. No dejar recursos con
userdata=null esperando que desconecte el cliente después de descargar la biblioteca.
Hyprland 0.56.2 descarga plugins antes de wl_display_destroy_clients; el nuevo DSO fixture
verifica ese orden con biblioteca realmente descargada y con clientes aún conectados.

El filtro real se ha revisado en fuentes: permite el peer interno directo y mantiene
privilegiados nuestros globals para conexiones security-context. No se reemplaza/relaja.
Sin aceptación real de frontend/arranque/logout ni validación de otros plugins. El sondeo
JSON del contador y recuperación de generaciones siguen por resolver antes de uso diario.
Detalle y evidencia: BREEZE_R4_RESULTS.md §226 / BREEZE_R4_STARTUP_TEARDOWN_RESULTS.json.

El preflight de --native-desktops exige providerLifecycleVersion=1 (entero, no booleano)
y observerStartup=deferred-event-loop, además de las guardas anteriores. Diagnósticos de
un módulo antiguo se rechazan antes de lanzar el auxiliar; sin instalar/cargar/habilitar.

## Copia del contador compartido sin leer archivos en el compositor (§227)

Autoridad: opciones BWM efectivas, incluidos overrides comunes de texto → puente KDE ya
existente → native_workspaces.Runtime → comando bwm-plasma-desktops-count → CountMirror
memoria → workspaceSnapshot. El contador no se guarda por esta vía ni se convierte en una
preferencia de la skin. Los ajustes KDE siguen como proyección de la autoridad común.

El coordinador vive en watch existente (debounce previo y comprobación2s); reconcile lo
reutiliza y envía al reentrar. Sin watcher/thread/daemon propio. Lecturas y proceso IPC sólo
en ese auxiliar; frontend sin file_size/ifstream/JSONparse. Guarda de primer snapshot evita
publicar contador desconocido; errores posteriores conservan el último aceptado. Disponibilidad
de copia no significa frescura instantánea o certificación del panel. No hay creación/borrado
de workspaces; reducción conserva vivos/activos. Preflight continúa sólo lectura y exige
versión/copia confirmada. Interfaces, pruebas y límites en BREEZE_R4_RESULTS.md §227 y
BREEZE_R4_COUNT_MIRROR_RESULTS.json. Frontend/arranque reales y aceptación diaria pendientes.

## Entrega común entre skins sin otro demonio (§228)

SharedSettingsRuntime se instancia sólo en shell.qml y fuera de panelFamilies; usa Config
existente y un Timer Qt/Process asíncrono para debounce y retry. No vive en Config.qml para
no duplicarse en Ajustes/auxiliares. No nuevo FileView/inotify, demonio o thread. Un proceso
por turno; un cambio en vuelo conserva pendiente una entrega nueva, sin cancelar trabajo.

bwm_settings_hooks.py shared descubre sólo adaptadores incluidos/revisados mediante
hooks.sharedSettings {script,requiresConfigFile,intervalMs}. Script dentro de su skin,
prerequisito relativo XDG sin escape y recibo JSONv1/applied. No registro automático de
código descargado. Falta prerequisito: no IPC/adaptador, retry0; armado: reintento acotado.
Sólo activa entrega de datos, nunca carga/habilita un proveedor.

native_workspaces.py shared resuelve opciones comunes y overrides de la skin actual,
sin importar/arrancar el puente KDE. Usa CountMirror y su recibo existentes, con el mismo
bridge_lock. KDE watch pierde el sondeo periódico de contador y conserva reconcile; la
continuidad viene del shell común, incluso Retro/default. El contador sigue siendo común.
No preferencias nuevas ni escritura de texto del usuario o archivos KDE desde este auxiliar.

IPC sharedSettings status es sólo diagnóstico de coordinación, no aceptación gráfica.
Pruebas reales de componente Quickshell offscreen y cadena de procesos con backend C++ de
ensayo en BREEZE_R4_SHARED_DELIVERY_RESULTS.json; no compositor/IPC real. Fuente shell enlazada
puede recargarse automáticamente, pero carga no verificada: llamadas IPC de sesión fallan.
No activar panel nativo ni avanzar R5/R7 por estas pruebas. Marco completo/arranque diarios pendientes.


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
