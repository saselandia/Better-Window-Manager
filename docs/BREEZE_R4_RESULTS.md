# R4 — anfitrión nativo de plasmoides e integración en curso

> **Estado 2026-11-15 (§228): R4 sigue pendiente de integración y aceptación restante.** La puerta
> externa se superó con widgets elegidos por la tienda KDE y sus páginas propias (§209).
> El auxiliar conserva ahora el menú TaskManager original con capacidades BWM y bloquea tres
> acciones sin backend. Pantalla completa se conecta al gestor común con estado deseado y
> recibo explícito. Los metadatos de aplicaciones se actualizan desde la base nativa KDE sin
> reiniciar el auxiliar. El control de escritorios verifica registro único y asociación de
> proveedor; detecta duplicados y permite retirar la vista. El módulo opcional añade inventario
> previo, elección entre proveedores BWM y retirada ante conflictos visibles. El observador
> arranca bajo demanda desde el bucle y el cierre final destruye los recursos antes de descargar
> su biblioteca. El contador común llega del puente existente por IPC a una copia en memoria,
> sin leer config.json desde el frontend. Un coordinador común del shell mantiene la entrega
> entre skins sin mantener el puente KDE completo fuera de Breeze. Pruebas aisladas normal/ASan,
> sin certificar el pintado de Task.qml ni el
> comportamiento del panel completo en Wayland. Sustitución diaria y capacidades restantes
> siguen pendientes; operationalVerified/replacementReady permanecen false.

## Estado anterior (histórico)

Actualizado 2026-11-14. **R4 sigue pendiente de integración en Hyprland.** Tras la instalación
de plasma-desktop, carga también el panel original, su orden y configuración por instancia.
Faltan aceptación Wayland, adaptadores de datos, migración/activación completa y descarga KNS.
La configuración ya sincroniza claves compartidas entre categorías y mantiene las páginas
durante cambios de controles; pruebas normales/ASan y lectura desde otro proceso aprobadas.
PanelSession incorpora altas/bajas, orden nativo y acciones dinámicas/submenús para el futuro
editor, con persistencia y posiciones comprobadas en otro proceso. API dentro del auxiliar.
Las páginas por módulo QML y las propiedades required previas a Component.onCompleted ya
comparten fábrica/transacción con diálogo y CLI; regresión normal/ASan aprobada.
El auxiliar aloja ahora también el Panel.qml original instalado, con fondo/temas SVG,
bordes y flotación comprobados mediante render offscreen; su aceptación Wayland está pendiente.
Seis preferencias del marco se guardan en plasmashellrc nativo, con kdedefaults, conflictos,
inmutabilidad, efecto en la vista y lectura en otro proceso probados; guardar es explícito.
La migración prepara además grosor/flag de flotación/enum de opacidad en el archivo KDE
separado y los relee en el marco original; los comportamientos sin adaptador siguen pendientes.
PanelRuntime coordina ahora vistas por descripción de monitor y skin, con hotplug, rechazo
de ambigüedad, conservación de instancias y reapertura en proceso nuevo probados en Qt aislado.
El hook común del gestor puede controlar una previsualización registrada explícitamente,
con confirmación de retirada, unicidad y parada/Ctrl+C probadas. Sin sustitución diaria activada.
El perfil nativo de ensayo conserva archivos completos y bindings entre ejecuciones; snapshots
y restauración a otra generación/ruta probados con opciones de widget/vista y proceso nuevo.
La exportación explícita a estado XDG conserva ese estado y todo el historial de snapshots
fuera de /tmp; reapertura/restauración con la fuente temporal eliminada probadas en fixtures.
No se sustituye la barra fija ni se anuncia como soporte de plugins completado. No se avanza R5.

Antes de empezar, el usuario confirma la prueba R3 de colocación Centered, Aplicar, ventana
nueva centrada y valor conservado al reabrir. Esto valida esa opción en sesión; no cierra todos
los pendientes de R3. El aviso de registro del portal no impidió abrir el anfitrión real.

## Implementación

- `src/bwm-plasma-host`: ejecutable aislado con **libplasma/PlasmaQuick reales**, Corona,
  Containment, Applet, PlasmoidItem, ConfigView/ConfigModel y KConfigLoader. Catálogo KPackage.
- `check-isolated.py`: instala y retira tres paquetes con kpackagetool6 en raíces temporales;
  bus de sesión no disponible para hijos, Qt offscreen, sin compositor ni servidores.
- Configuración: páginas originales cargadas, propiedad booleana descubierta por reflexión
  `cfg_*` y esquema, preparación de cambios, cancelar sin escritura, defaults preparados,
  guardar/releer y prueba desde proceso nuevo. No hay formulario fijo para el paquete externo.
- `migration.py`: propuesta no destructiva, sin escribir un appletsrc propio. El layout del
  ensayo lo escribe/lee Corona con sus APIs; dos IDs del mismo plugin tienen datos separados.
- Arquitectura, contratos y guía de actualización en BREEZE_R4_ARCH.md y README del auxiliar.
  Dependencia experimental declarada; sin instalar/activar el auxiliar en la sesión.

## Pruebas ejecutadas y evidencia

`BREEZE_R4_PROBE_RESULTS.json` conserva el resultado del driver aprobado:

| Paquete | Comprobado |
| :--- | :--- |
| org.kde.example.compactrepresentation, original KDE | Item nativo, compacta y completa instanciadas, 48×48, localización/borde/form factor registrados, dos instancias, instalación/retirada nativa |
| org.kde.example.configuration, original KDE | Categorías y páginas originales; BoolTest descubierto dinámicamente, Cancel/Defaults no guardan, Aplicar cambia true→false; lectura desde proceso nuevo, segunda instancia intacta |
| AndromedaLauncher, paquete instalado de terceros | Item completo nativo; dos categorías y páginas ConfigGeneral/ListAndGrid; 23 claves del esquema; useCustomButtonImage descubierto sin tabla BWM, false→true guardado y releído en proceso nuevo; segunda instancia intacta; instalación/retirada nativa |

**No se modificó el Andromeda instalado:** se seleccionó su directorio como fuente para
instalarlo en el entorno desechable. Ninguna acción del launcher fue activada. Catálogo antes/
después confirma alta y baja; instalación local no equivale a probar descarga KNewStuff.

Tres tests Python de migración pasan. CMake compila el ejecutable con bibliotecas instaladas.
Pruebas con bus/Wayland de la sesión no se ejecutan. La prueba no demuestra render visual
idéntico ni disparo de QAction, sólo inspección de las acciones disponibles. ConfigView instala
el dominio de traducción, pero no se comparan traducciones renderizadas a varios idiomas.

## Pendientes de la primera iteración (actualización al final)

El widget externo **carga su página original y guarda una opción propia**, incluida lectura
desde proceso nuevo. Eso demuestra el núcleo requerido, pero no el flujo gráfico completo:

1. Falta paquete Plasma/Shell y muebles de expansión. libplasma emite Invalid home screen
   package; el ejemplo compacto no tiene un compactRepresentationExpander funcional. No se
   debe tratar compact/full instanciados como popup usable. Andromeda prefiere full y no
   crea su compacta en esta prueba; no se acredita su expansión interactiva.
2. El ciclo de configuración se ensaya programáticamente sobre página/esquema reales.
   Faltan diálogo navegable, botones pulsados, validación/callbacks especiales, tipos no booleanos,
   cambios entre categorías, concurrencia y destrucción/reapertura desde el panel real.
3. Corona usa geometría de fixture. Faltan view layer-shell, IDs de panel por monitor, input,
   reservas, popup/grabs y lifecycle al cambiar de skin. No se ejecuta plasmashell para suplirlo.
4. Migración: sólo propuesta probada y diseño; falta aplicación verificable mediante Corona,
   mapeo de todas las claves heredadas y rollback. bar.plasma permanece intacto.
5. Obtener nuevos: proveedor nativo identificado; diálogo KNS y actualización viva pendientes.
6. Interfaces R5 documentadas con estado, no anunciadas como IPC listo. Sin soporte universal
   ni conclusión «imposible» por dependencias KWin de un paquete particular.

Por estas diferencias **R4 permanece pendiente** y el panel actual sigue como estaba. No se
pide instalar/reiniciar nada para esta prueba. Sombras y miniaturas permanecen contenidas.

## Referencia y reproducción

libplasma 6.7.5, Qt 6.11.2/KF6 del equipo. Fuentes locales extraídas de los tarballs de Portage:

- libplasma-6.7.5.tar.xz SHA-256 `27b28823254aa489c094c40a314ce1575fd7906eeb521e636bb8fd2dc2981f2f`.
- plasma-workspace-6.7.5.tar.xz SHA-256 `94ab21e2243b7876f65c315f1e545081c6437f5bd0a041ca4fb6c2533ae874c9`.

Comando y actualización: src/bwm-plasma-host/README.md. Requiere elegir explícitamente fuente
upstream y paquete externo; los ejemplos no se copian al repositorio. Resultados registran
URLs temporales de las copias de prueba, ya retiradas al terminar; no son rutas instaladas.

Rollback: este auxiliar no está conectado al runtime. Retirar sólo su carpeta y referencias
R4 si se abandona el prototipo; preservar el trabajo R0–R3 y otros cambios concurrentes.
Sin instalación real, cambios de skin, reinicio de shell/compositor, commit ni push.

## Continuación: expansión, diálogo, acciones y catálogo vivo

Implementado después de la primera prueba:

- Paquete Plasma/Shell propio y mínimo, con contrato nativo `compactapplet`,
  `defaultcompactrepresentation` y `appletconfigurationui`. Usa **AppletPopup original**;
  no se ejecuta plasmashell. Muebles y marco de diálogo son adaptadores BWM, sin afirmar
  que sean el editor original de R5.
- `ConfigurationSession` + ConfigView: páginas originales, categorías, Aplicar/Cancelar/
  Predeterminados pulsados con QtTest; valores pendientes sin escribir, persistencia,
  bool/texto/entero y cambio de página. Predeterminados incluye claves conocidas sin control
  visible y respeta política inmutable. Guardado rechaza conflictos y tipos no convertibles.
- Páginas con cfg_* sin esquema, claves compartidas entre páginas, callbacks personalizados
  o KCM aún no adaptados explican el límite y bloquean Aplicar. No se silencian esas opciones.
- Corregida una liberación doble: ConfigView se autodestruye al ocultarse en 6.7.5; se usa
  QPointer. ASan identificó el problema durante el ensayo; no ocurrió en la sesión del usuario.
- Catálogo completo mediante PluginLoader: **27 widgets, 18 en bibliotecas nativas** en la
  lectura del equipo. El listado inicial sólo de PackageLoader los omitía. Reloj analógico
  nativo: qrc/configuración real, opción showSecondHand guardada/releída en otro proceso.
- Vista `--preview`: Configurar, acciones de QAction originales y Obtener nuevos.
  El menú se prueba con una acción inocua añadida al Applet de ensayo; no dispara acciones
  personales del launcher. El compacto se pulsa con ratón Qt, no sólo setExpanded por código.
- `Catalog.getNewWidgets()` abre KNSWidgets::Dialog con plasmoids.knsrc nativo; finalización
  refresca el catálogo. Watcher único con debounce detecta altas, bajas y metadatos. La prueba
  usa PackageJob para instalar/quitar un fixture con el catálogo ya abierto y comprueba señales.
  **No se ha probado una descarga desde la tienda ni se ha abierto KNS en la sesión real.**

### Evidencia de esta continuación

`BREEZE_R4_UI_RESULTS.json` conserva el resultado normal y
`BREEZE_R4_UI_ASAN_RESULTS.json` la repetición con AddressSanitizer. CTest coordina un driver
con raíces XDG temporales y bus de sesión deshabilitado para hijos:

1. Ejemplos originales y Andromeda: instalación/retirada nativa, dos instancias y lectura
   desde proceso nuevo. Se conserva también la prueba del reloj analógico compilado.
2. Dos ejecuciones de QtTest (ejemplo configurable y Andromeda), con grupos de pruebas de
   catálogo vivo, vista que abre ConfigView, botones, navegación, QAction inocua, popup y
   detección de edición concurrente. No se pulsa ninguna acción de sesión de los paquetes.
3. Repetición ASan del mismo escenario; detect_leaks=0: comprueba errores de memoria en el
   código instrumentado, **no** certifica ausencia de fugas ni instrumenta todas las bibliotecas.

Los mensajes sobre KWindowShadow y máscaras se producen porque Qt offscreen no proporciona
un compositor; no se usan para certificar sombras, posicionamiento real o equivalencia visual.
La operación de código QML de terceros sigue siendo ejecutable: raíces XDG temporales no son
un sandbox general. Los paquetes de las pruebas fueron seleccionados y revisados.

### Estado actual y siguiente aceptación

Se cierran los huecos aislados de popup/diálogo/acciones y de catálogo/KNS integrado. R4 sigue
pendiente por:

- PopupPlasmaWindow emplea PlasmaShellWaylandIntegration para posicionar en Wayland; faltan
  adaptación a Hyprland, pruebas de foco, escala, dos monitores y reservas. No basta mostrar
  una ventana offscreen para garantizar el anclaje.
- Migración de bar.plasma aplicada mediante Corona, transacción/rollback y ciclo entre skins.
- Categorías/callbacks de configuración bloqueados hasta adaptar su contrato; no compatibilidad
  universal. Descarga y retirada mediante el diálogo KNS real, además del PackageJob ya probado.
- Integración del auxiliar con el panel/editor; no se ha activado un segundo panel ni iniciado R5.

Vista de prueba explícita, con copia temporal del paquete y configuración desechable:

```bash
python3 /mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/preview-isolated.py \
  --binary /tmp/bwm-r4-build/bwm-plasma-host \
  --package ~/.local/share/plasma/plasmoids/AndromedaLauncher
```

Esta vista sirve para revisar configuración y apertura/cierre. No sustituye la barra. La posición
real del popup es precisamente parte pendiente; no se presenta como idéntica a Plasma.
No requiere instalar el auxiliar ni reiniciar el compositor. No se ejecutó esta apertura interactiva
desde el sandbox. No se instala nada en HOME, ni hay commit/push.

## 2026-11-13 — adaptador layer-shell y preparación nativa de migración

Se añaden `surfaces.{h,cpp}` y `migration.{h,cpp}`. No se sustituye el panel activo.

### Superficies sobre Hyprland: implementado, pendiente de aceptación real

El modo opt-in `--layer-preview` configura superficies concretas con LayerShellQt 6.7.5;
no cambia globalmente QT_WAYLAND_SHELL_INTEGRATION ni convierte los diálogos de ajustes en
paneles. La vista usa capa Top y el popup Overlay, teclado OnDemand y zona exclusiva -1:
no reserva espacio ni toma teclado exclusivo. El popup recibe pantalla, tamaño y márgenes
relativos a la pantalla, sin depender de org_kde_plasma_shell para su posición efectiva.

El cálculo trabaja en píxeles lógicos: cuatro bordes, orígenes negativos/desplazados, cambio
al lado contrario si falta espacio, límite de tamaño y rectángulo disponible explícito.
Usa mapRectToScene para transformaciones del widget, sin multiplicar por DPR. Se actualiza
con geometría de pantalla, tamaño y movimiento/animación; un cambio de salida recrea la
superficie porque la salida de layer-shell se elige al crear el rol.

`surface-geometry` pasa en offscreen: siete casos de geometría, entradas inválidas y
propiedades del adaptador, incluido widget escalado. **No demuestra el protocolo negociado,
foco, escalado real ni dos monitores en Hyprland.** El modo se mantiene explícito:

```bash
python3 /mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/preview-isolated.py \
  --binary /tmp/bwm-r4-build/bwm-plasma-host \
  --package ~/.local/share/plasma/plasmoids/AndromedaLauncher --layer-panel
```

Esta apertura gráfica no se ha ejecutado desde aquí. La vista temporal tiene una separación
inferior de 64 píxeles y no reemplaza ni modifica la barra real. R5 tendrá que proporcionar el
área útil/reservas y las identidades de monitor desde los gestores comunes para el panel final.

### Migración: instancia nativa preparada y releída, sin activación

`migration.py` añade bindings explícitos del reloj. La semántica existente de DigitalClock.qml
es `showSeconds ? 2 : 1`; se conserva **Always=2 / ToolTip=1**, no se convierte bool a int ni
se cambia false a Never=0. showDate mantiene su tipo booleano. Otras claves quedan archivadas
hasta disponer de una equivalencia contrastada.

`--stage-migration PLAN.json` valida el hash del origen y que estén todos los paquetes antes
de publicar nada. Crea containments/applets mediante Corona y aplica sólo claves presentes en
sus esquemas nativos. Fuerza el sync y destruye los propietarios KConfig antes de renombrar
atómicamente el directorio preparado. Dentro van `layout` escrito por Corona, `legacy.json`
con el texto íntegro del origen y `report.json` con identidades y estado; no es un formato
alternativo de appletsrc. Un destino existente no se sobrescribe.

`--verify-stage DIRECTORIO` vuelve a cargar el layout en **otro proceso** y verifica IDs,
paquetes, orientación y valores. La prueba crea dos monitores ficticios con dos relojes cada
uno, conserva las claves desconocidas y los ajustes comunes en el archivo original, y rechaza
paquete ausente, clave sin schema, hash incorrecto, archivo alterado y sobrescritura del destino.
No quedan directorios temporales parciales tras un error.

Esto materializa **datos de instancias** en un containment base nativo sin UI. No aplica todavía
toda la disposición/aspecto de bar.plasma ni hace la transición del panel real. Por eso el
resultado mantiene `activationAllowed=false`. El rollback de activación y el ciclo de skins
siguen pendientes; el origen nunca se modifica durante esta preparación.

### Bloqueo anterior por plasma-desktop (resuelto en la continuación siguiente)

`qlist -Iv kde-plasma/plasma-desktop` y la base instalada confirman que el paquete no está
instalado. El catálogo actual no contiene Kickoff, icontasks ni showdesktop. La migración del
panel completo se rechaza antes de publicar una copia parcial. Se declara
`plasma-desktop-widgets` como recomendación explícita; debe verificarse el catálogo tras instalar.
La instalación sólo aporta recursos: no hace operativo el modelo de tareas o las APIs KWin.

El ebuild local 6.7.5 ofrece semantic-desktop opcional. El pretend con ese flag desactivado
resolvió **cinco paquetes nuevos / 19071 KiB**: plasma-desktop, plasma-mimeapps-list,
knotifyconfig, xdg-user-dirs y setxkbmap. El comando terminó después con error de permisos
al actualizar `/var/lib/gentoo/news`; no instaló nada ni se corrigieron permisos.

Operación pendiente en la terminal del usuario (requiere sudo, regla 7 de AGENTS):

```bash
sudo env USE="-semantic-desktop" emerge --ask --oneshot =kde-plasma/plasma-desktop-6.7.5
```

El flag en ese comando es temporal; no se modifica package.use. No se ejecuta plasmashell
ni se habilita un servidor KDE para usar el anfitrión BWM.

### Verificación y estado

CTest normal y con AddressSanitizer pasan **surface-geometry + isolated-plasmoids**; se repiten
las pruebas de páginas, acciones, catálogo vivo, instalación/retirada y persistencia por instancia,
y se añade staging/lectura nativa. ASan con detect_leaks=0, sin acreditar fugas de bibliotecas.
Cinco tests Python de propuesta/mapeo y siete de manifiestos pasan. Sintaxis y diff correctos.
Evidencia nueva: `BREEZE_R4_SURFACE_MIGRATION_RESULTS.json`.

Fuente LayerShellQt: tarball local 6.7.5, SHA-256
`ccdcfec7081ca956f7a52c9113a4df3a226575bfbe98b56a2a9a4d7d7e19e8f0`.
Se revisaron Window::initializeShell y QWaylandLayerSurface: el rol es por ventana y la salida
se elige al crear la superficie. No se cambian plugins del compositor ni se añade otro escritorio.

R4 sigue pendiente de paquete desktop disponible, validación Wayland real, migración completa,
activación/rollback del panel y contratos de configuración aún bloqueados. KNS está conectado,
pero descarga remota y retirada desde su diálogo siguen sin comprobar. Sin instalación real,
reinicio, cambios de skin, capturas, sombras, commit ni push.

## 2026-11-13 — plasma-desktop instalado: panel original y configuración desde el panel

El usuario instaló el paquete. `qlist -Iv kde-plasma/plasma-desktop` confirma **6.7.5**;
el catálogo nativo devuelve **43 entradas**, incluidos org.kde.panel, Kickoff e icontasks.
No se ejecutó plasmashell ni se cambió el compositor. Los recursos se usan desde las
bibliotecas/paquetes instalados; no se copiaron los QML de Plasma al repositorio.

### Comprobado en esta continuación

| Contrato | Implementación y verificación |
| :--- | :--- |
| Containment original | Corona crea `org.kde.panel`; el root cargado procede de `qrc:/qt/qml/plasma/applet/org/kde/panel/main.qml` |
| Disposición nativa | `General/AppletOrder` se escribe con el KConfigLoader del panel; el LayoutManager original restaura dos relojes en orden, con contenedores y tamaños reales, en dos paneles |
| Reapertura | `--verify-stage` y `--probe-stage` corren en procesos nuevos; la carga del QML original no altera el orden previsto |
| Configuración desde el panel | `PanelSession` conecta `Containment::configureRequested` con ConfigView/ConfigurationSession; activar la QAction nativa abre las páginas originales |
| Cambios por instancia | QtTest pulsa Aplicar y Cancelar, reabre el diálogo y relee el esquema; la segunda instancia no cambia. Se prueba con el ejemplo KDE y Andromeda |
| Retirada de instancia | Quitar un applet con el diálogo abierto libera la sesión/configuración; las peticiones posteriores por ese ID se rechazan |
| Ventana propia del complemento | Clic sobre el botón original de Andromeda abre su **propio** PlasmaCore.Dialog; otra instancia conserva su ventana cerrada. Prueba offscreen, sin certificar posición Wayland |
| Panel sin páginas de applet | Se explica que el editor no pertenece a esta vista; Aplicar/Predeterminados quedan bloqueados. No se permite resetear AppletOrder desde un diálogo vacío |
| Datos del conjunto heredado | Staging y lectura de Kickoff, icontasks, bandeja, reloj y Mostrar escritorio: diez IDs en dos paneles; configuración de Kickoff/tareas/reloj y archivo íntegro preservados |
| Descubrimiento | Metadatos de tipo, provides, form factors y required extensions; visibilidad del explorador según NoDisplay/categoría/plataforma. Containments como Folder View y bandeja pueden ser widgets visibles |
| Temas globales | `--theme-catalog` usa Plasma/LookAndFeel y KConfig para separar defaults, referencias SVG/decoración/fondo, colores, vistas y scripts; conserva claves desconocidas e indica recursos heredados |

`migration.py` pasa las secciones que ya contienen nombres KDE (`kickoff`, `taskManager`,
`systemTray`, `clock`) al esquema nativo, sin una segunda lista fija de claves. Una clave que
no exista en destino bloquea la publicación del staging; el archivo original sigue íntegro.
Las claves superiores showDate/showSeconds mantienen la autoridad del port actual sobre clock.
Las listas de configuración se copian por instancia, sin compartir objetos entre propuestas.

**Favoritos de Kickoff:** el código upstream usa un cliente KAStats asociado al ID del applet.
Por ello se prepara `favoritesPortedToKAstats=false` si hay favoritos que importar: el true del
cliente BWM no acredita el nuevo cliente nativo. El valor original queda archivado. Se comprueba
la escritura/lectura del plan; **no** se certifica todavía la importación efectiva a KAStats.

### Capacidades y límites por paquete

El catálogo expone `runtime.status`, `dependencies` y `operationalVerified=false`. No convierte
una instalación en certificación operativa. Los paquetes desconocidos siguen descubriéndose,
con estado `unassessed`, sin quedar excluidos por una lista BWM.

| Paquete | Dependencia observada en upstream | Estado en este auxiliar |
| :--- | :--- | :--- |
| org.kde.panel | ContainmentItem, LayoutManager, view/superficie del anfitrión | QML y orden probados offscreen; Wayland/edición duradera pendientes |
| icontasks/taskmanager | org_kde_plasma_window_management y virtual desktop management en libtaskmanager | Datos/configuración persistidos; falta backend Hyprland para ventanas/acciones |
| pager | Modelo de ventanas/escritorios de libtaskmanager | Recurso disponible; falta adaptador de escritorios comunes BWM |
| showdesktop | org.kde.KWin /KWin o backend showingDesktop de KWindowSystem | Falta conectar al gestor común BWM; no se invocó ninguna acción |
| kickoff | KService, favoritos KAStats por instancia y proveedores de acciones de sesión | Instancia/esquema preparados; favoritos y acciones pendientes de integración |
| systemtray | StatusNotifierWatcher y servicios de cada applet hijo | Datos preparados; no se toma otra reserva del watcher ni se certifican los hijos |
| AndromedaLauncher | Kicker/servicios y PlasmaCore.Dialog creado por el propio paquete | Páginas, guardar, dos instancias y apertura real offscreen probadas; anclaje propio Wayland pendiente |

El adaptador PopupAnchor actual cubre **AppletPopup del anfitrión**. No intercepta todos los
Dialog/Window que un complemento cree por su cuenta. La prueba anterior que forzaba compacta
y envolvía la fullRepresentation de Andromeda sólo acreditaba ese wrapper: el paquete define
su fullRepresentation como un botón y crea el menú aparte. Esta continuación añade la prueba
de su ruta real; no atribuye a la prueba anterior una cobertura que no tenía.

### Temas globales: inventario sin ejecutar disposición

`themeinventory.cpp` resuelve defaults, layoutdefaults, colors, logout/splash/windowswitcher,
layouts y plasmoidsetupscripts mediante la PackageStructure instalada; registra si cada ruta
es propia o procede del fallback nativo. No asume que un tema global sea un SVG ni que declare
los widgets que sólo crearía su script. Los defaults se leen con KConfig, incluidos grupos y
claves desconocidas. El catálogo es de lectura, no un nuevo aplicador de temas.

| Componente | Cómo ofrecer sus opciones |
| :--- | :--- |
| Defaults/colores/estilo | Rutas nativas y gestores de aspecto existentes; mantener autoridad del usuario y kdedefaults de R3 |
| SVG Plasma | Resolver la referencia plasmarc/Theme; recursos y variantes del paquete de escritorio |
| Decoración | Resolver kwinrc/org.kde.kdecoration2; KCM/factory descubiertos en R3, incluidas opciones de terceros |
| Plasmoides | Catálogo KPackage y páginas originales por instancia; no extraer opciones fijas de layout.js |
| Fondo | Resolver su referencia y abrir el configurador del paquete de fondo; adaptación runtime pendiente |
| Vistas QML | Registrar rutas originales/fallback y validar cada capacidad del anfitrión; no prometer equivalencia por existencia |
| Layouts/setup scripts | Mostrar ruta, hash y explicación de capacidad pendiente; executeAllowed=false hasta tener adaptador revisado y transaccional |

La prueba instala/retira un tema global desechable con KPackage, lee una clave de proveedor
desconocida y referencias de SVG/decoración, comprueba el hash de un script que arrojaría error
si se ejecutase y conserva el origen. Este inventario no crea un motor de scripts ni aplica
defaults a la sesión. Los valores efectivos de kdedefaults no se sobrescriben al explorarlo.

### Uso de la nueva vista y evidencia

Vista explícita de dos instancias dentro del panel original, con copia y raíces temporales:

```bash
python3 /mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/preview-isolated.py \
  --binary /tmp/bwm-r4-build/bwm-plasma-host \
  --package ~/.local/share/plasma/plasmoids/AndromedaLauncher --native-panel
```

`--layer-panel` añade el modo LayerShellQt experimental sin reserva de área. La vista normal
se cierra como ventana; Ctrl+C termina el hijo y limpia el entorno. No se abrió en la sesión
desde esta ejecución, cuyo acceso a Wayland/Hyprland/D-Bus sigue restringido. No hay que
reiniciar el compositor para usar esta vista. El bus de sesión queda deshabilitado para los
hijos; las raíces XDG aisladas no son un sandbox para acciones arbitrarias del complemento.

Evidencia: `BREEZE_R4_NATIVE_PANEL_RESULTS.json`, con el catálogo, driver normal y ASan.
CTest pasa surface-geometry e isolated-plasmoids; incluye la nueva ruta del panel/diálogo.
Siete tests Python de migración y siete de manifiestos pasan. ASan usa detect_leaks=0;
no certifica fugas ni instrumentación de todas las bibliotecas KDE.

Se revisaron las fuentes 6.7.5: containments/panel/{main.qml,main.xml,LayoutManager.js},
applets/kickoff/main.qml, applets/showdesktop/showdesktop.cpp (plasma-desktop) y
libtaskmanager/{waylandtasksmodel,virtualdesktopinfo}.cpp, components/shellprivate/
plasmaappletitemmodel.cpp (plasma-workspace). Tarball plasma-desktop SHA-256:
`079fcf6b87d7bf65e3f2a4670d605fac9469344c279a285a98ad549332d7b53e`.

**R4 permanece pendiente.** Próximas puertas: contratos de ventanas propias de paquetes en
Wayland, backend de ventanas/escritorios, geometría/activación/rollback y cambio de skin,
casos de configuración aún bloqueados y descarga/retirada real KNS. El panel de uso diario
no se sustituye. Sombras y miniaturas continúan contenidas; no hay reinicios, commit ni push.

## 2026-11-13 — ventanas propias de los paquetes y geometría de la vista

El usuario responde «ya está, continúa» tras el comando de vista normal. Se conserva ese
feedback, sin deducir de él una matriz de dos monitores, escala/foco ni aceptación layer-shell.
La continuación implementa el siguiente contrato de R4; no inicia R5 ni sustituye la barra.

`PackageWindows` descubre ventanas QML del proceso y comprueba su propietario mediante el
contexto nativo `plasmoid`. Sólo considera applets del containment asociado. Para un
**PlasmaQuick::Dialog oculto y sin superficie**, prepara el adaptador por ventana antes de
mostrarlo. No modifica paquetes, metadatos instalados, ventanas externas ni servidores KDE.
Se usa desde PanelSession y se refresca explícitamente tras montar el panel, además de un
refresco coalescido por eventos de creación/visualización: no hay sondeo periódico.

| Ventana/caso | Decisión comprobada |
| :--- | :--- |
| Dialog nativo perteneciente al panel, todavía sin superficie | Rol Overlay, teclado OnDemand, zona exclusiva -1 y salida del panel preparados |
| Dialog con visualParent del mismo panel | Anclaje relativo al elemento nativo |
| Dialog sin visualParent, como el menú de Andromeda | Conservar su posición global solicitada; limitar tamaño/posición al área disponible, sin sustituir sus preferencias por centrado fijo |
| Ventana de otro contexto/aplicación | No intervenir |
| Dialog ya visible o con superficie creada | `requires-pre-surface-registration`; no recrear en caliente su rol |
| Tooltip, notificación, OSD o ventana outputOnly | `requires-noninteractive-role-adapter`; no imponer foco interactivo |
| Window genérico del paquete | `requires-explicit-window-type-adapter`; inventariado, sin anunciar soporte |
| Ancla en otra superficie | `unsupported-foreign-anchor` |
| Vista normal | `normal-window-preview`, sin conversión a layer-shell |

Cada registro expone appletId, package, status, placement, adapted y **waylandVerified=false**.
Un estado `layer-role-prepared` acredita preparación del cliente Qt, no negociación ni foco
en el compositor real. El AppletPopup del anfitrión conserva su vía independiente.

PopupAnchor admite ahora ventanas independientes: actualiza márgenes cuando el paquete cambia
x/y, mantiene la política de anclaje elegida y, al cambiar de salida, recuerda visibilidad sin
activar artificialmente `AppletQuickItem.expanded`. Los límites usan `QScreen.availableGeometry`
o un área explícita del anfitrión. Si Qt no proporciona reservas de Hyprland, no se inventan:
esa integración sigue pendiente de validar. Las pruebas cubren posiciones solicitadas, límites
con origen negativo y limpieza de los registros al desaparecer las ventanas.

`ViewCorona` reemplaza la geometría ficticia del ejecutable por las salidas Qt: numScreens,
geometría lógica, área disponible, región y containment→salida de su vista. Se enlaza antes de
cargar el QML del panel. Los cambios de pantalla/geometría notifican al containment; no se usa
el índice de Qt como identidad persistente de monitor. La asignación duradera seguirá usando
descripciones de monitor. Los fixtures de staging/probePanel conservan su geometría de ensayo.

### Pruebas y límites

- Dos suites CTest normales y con ASan pasan. El test del panel original abre el menú real de
  Andromeda, confirma el rol preparado **antes** del clic y comprueba que el popup recibe un
  rectángulo válido. La segunda instancia sigue independiente.
- Un Dialog de prueba ajeno a cualquier nombre conocido de widget se reconoce por su contexto.
  Los ensayos incluyen Dialog tardío, outputOnly, Window genérico y ventana sin propietario.
- ViewCorona se compara con la salida Qt de su ventana, incluidos índices inválidos y geometría
  virtual. Se comprueba también la destrucción: Corona destruye containments en su destructor
  base y las conexiones no deben acceder al mapa derivado ya liberado.
- Continúan pasando las páginas/configuración, instalación/retirada de complementos y tema
  desechable, staging nativo y lecturas posteriores. Siete tests Python de migración y siete
  de manifiestos pasan. ASan con detect_leaks=0; sin certificar fugas de todas las bibliotecas.

Evidencia nueva: `BREEZE_R4_PACKAGE_WINDOWS_RESULTS.json`. No se ha abierto una vista sobre
la sesión desde esta ejecución, ni se ha accedido a sockets restringidos. El código usa los
headers y fuentes locales de libplasma 6.7.5 ya fijadas, sin nuevas dependencias.

La siguiente vista manual ejercita esta vía; cerrar con Ctrl+C limpia el entorno temporal:

```bash
python3 /mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/preview-isolated.py \
  --binary /tmp/bwm-r4-build/bwm-plasma-host \
  --package ~/.local/share/plasma/plasmoids/AndromedaLauncher --native-panel --layer-panel
```

**R4 sigue pendiente** de aceptación Wayland real (foco, escala, dos monitores, reservas),
creación tardía y tipos de ventanas no adaptados, backend BWM de ventanas/escritorios,
favoritos KAStats, geometría/activación/rollback/ciclo de skins, callbacks/KCM bloqueados y
descarga/retirada real desde KNS. La vista anterior no valida automáticamente estos contratos.

## 2026-11-13 — opciones compartidas entre páginas y estabilidad del diálogo

El usuario confirma que el aspecto de Breeze vuelve a estar correcto tras la corrección de
arranque/cambio de skin. Esa confirmación se registra para la incidencia de iconos/barras;
no se convierte en aceptación de R4. El `pasted text.txt` mencionado no está disponible entre
los archivos de este entorno. No se supone su contenido ni el resultado de la vista Wayland.

Se elimina una limitación del anfitrión: una misma clave nativa del esquema puede aparecer en
varias categorías originales. `ConfigurationSession` mantiene un mapa de cambios pendientes
por instancia. Los notify de las propiedades/aliases `cfg_*` identifican qué valor cambió y lo
propagan a las otras páginas con guarda de reentrada. Ya no gana accidentalmente el último
valor leído de una página oculta. No se escribe en disco hasta Aplicar. Si los controles no
pueden representar el mismo valor —por ejemplo, rangos incompatibles— Aplicar se bloquea
con una explicación. Las propiedades sin escritura/notificación requieren adaptador explícito.

Además, el notifier de la lista de páginas queda separado del de cambios pendientes/errores.
Antes, cualquier cambio de configuración notificaba también el modelo del Repeater que
aloja las páginas. Ahora los cambios de un deslizador conservan esos contenedores y sus
formularios originales. Cancelar y Predeterminados actualizan la preparación sin guardar;
Aplicar conserva la comprobación de conflictos, la política de inmutabilidad y las claves ajenas.

| Contrato | Efecto comprobado en aislamiento |
| :--- | :--- |
| Dos categorías con la misma clave bool/int | Edición en ambos sentidos sincroniza la página visible y la oculta |
| 57 cambios consecutivos del entero | Misma página/contenedor, cero notificaciones de cambio de lista y mismos bytes en disco |
| Cancelar y volver a abrir | Se conservan los valores guardados, no los cambios cancelados |
| Aplicar | Cambia el esquema nativo y el Text enlazado a Plasmoid.configuration.caption |
| Predeterminados | Prepara también la clave oculta del esquema; no la guarda hasta Aplicar |
| Dos instancias | Sólo cambia la instancia editada; ambas páginas recuperan el valor al reabrir |
| Escritura ajena concurrente | Aplicar rechaza la edición obsoleta y no sobrescribe el cambio ajeno |
| Clave ajena al esquema | Se conserva en su grupo KConfig después de Aplicar/Predeterminados |
| Rango incompatible entre páginas | Error explícito; valor persistido intacto |
| Nuevo proceso | Corona carga el layout nativo y las páginas leen los valores esperados de las dos instancias |

El fixture `org.bwm.r4.shared-config` es código de prueba BWM desechable, instalado/retirado
con KPackage en el XDG temporal. No se presenta como prueba de terceros. El driver vuelve a
ejercitar también el ejemplo KDE original y Andromeda sin alterar sus fuentes instaladas.
Cada suite UI tiene 11 resultados aprobados y cero fallos; además ejecuta la lectura del
fixture en un proceso separado. Las dos suites CTest pasan tanto normales como con ASan
(detect_leaks=0; no certifica fugas ni instrumentación completa de las dependencias).
Pasan también siete tests Python de migración y siete de manifiestos, py_compile y diff.

Evidencia: `BREEZE_R4_SHARED_CONFIG_RESULTS.json`, con los dos drivers completos, logs CTest,
lecturas en procesos separados y hashes de las fuentes. Arquitectura/guía de actualización
incluyen el nuevo contrato; no hay dependencias adicionales ni instalación del anfitrión.

**R4 permanece pendiente** de negociación/foco/escala/dos monitores/reservas Wayland,
backend común de ventanas/escritorios, otros tipos/creación tardía de ventanas, favoritos
KAStats, migración/activación/rollback/ciclo de skins, callbacks/KCM sin adaptador y descarga
real KNS. No se modifica el panel activo ni se reinicia el shell/compositor. No se avanza R5.
Para revertir esta ampliación del ensayo basta con retirar el mapa pendiente/notifier separado
y su fixture/driver; ninguna configuración de usuario necesita restauración.

## 2026-11-13 — API nativa de instancias, disposición y acciones del panel

El usuario pide seguir con R4 y cita el aviso anterior de integración pendiente. No se toma
esa cita como una prueba de sesión ni se requiere otro TXT para continuar el trabajo aislado.
Se completa otro bloque del anfitrión, sin implementar la UI del editor R5 ni activar el panel.

PanelSession expone inventario del containment/widgets, ID nativo, orden, altas/bajas,
solicitud de reordenación, acciones y configuración. El ejecutable enlaza su AppletQuickItem
original y publica el QObject en la propiedad bwmPanelSession de la ventana. Catalog.discover
reutiliza la misma política de metadatos del catálogo vivo sin crear watchers por panel.

| Operación | API/formato original y efecto real | Verificación ejecutada |
| :--- | :--- | :--- |
| Añadir widget por ID de paquete | Metadatos KDE actuales → Containment.createApplet; nueva instancia nativa | Paquete elegido KDE/Andromeda más dos instancias de fixture; elementos dentro de contenedores QML originales |
| Retirar una instancia | Applet.destroy elimina configuración nativa; no borrado manual del appletsrc | ID retirado ausente del inventario y del archivo; las otras instancias permanecen |
| Retirar con Configurar abierto | destroyedChanged cierra su ConfigurationSession antes de que Plasma limpie el esquema | QPointer del diálogo/sesión liberado; retirada/recreación sin fallo normal/ASan |
| Reordenar | Permutación exacta → main.qml/reorderApplets → LayoutManager.js → General/AppletOrder del containment | Orden nativo, bytes serializados, lectura desde proceso nuevo y posiciones de los elementos originales |
| Bloqueos y pertenencia | Inmutabilidad nativa del panel/widget; consulta limitada al containment propietario | No añadir/retirar/reordenar bloqueados, retirar panel como widget ni operar sobre otro containment |
| Enumerar acciones | contextualActionsAboutToShow y QAction originales; árbol de submenús, estado y tokens por identidad | Acción creada al abrir el menú aparece sin tabla BWM; nombres/posiciones no son su identidad |
| Actualizar estados del menú | widgetActions(ID, false) lee sin volver a ejecutar la preparación del paquete | Cero avisos de preparación/cambios nuevos en esa lectura; evita el bucle fábrica→changed→fábrica |
| Ejecutar acción | Se comprueba el mismo Applet/QAction, pertenencia actual y ruta habilitada/visible | Acción inocua disparada y estado checked actualizado; token ajeno, retirado, borrado, oculto/deshabilitado o con submenú padre deshabilitado rechazado |

Los tokens son efímeros, no preferencias. Las acciones de servicios/sesión de Andromeda y
otros paquetes no se activan para probar esta API. Las acciones internas del shell siguen
fuera del inventario contextual: Configurar y retirada tienen operaciones explícitas. La
retirada es **permanente**; no se presenta como el flujo nativo de notificación/deshacer.
Crear un widget o descubrir sus acciones no certifica que sus servicios KWin/KDE funcionen.

requestOrder devuelve aceptación del despacho al QML original; el consumidor debe confirmar
order. No invoca una implementación propia de disposición. Valida IDs enteros, ausencia de
duplicados, conjunto exacto de instancias vivas, vista propia e inmutabilidad. Los avisos de
inventario están coalescidos. El futuro editor debe pedir la reordenación al confirmar la
disposición, sin enviar el array entero por cada movimiento del puntero.

### Persistencia: carga y guardado sobre el mismo propietario

La prueba detectó que usar saveLayout a otro archivo como si fuera el guardado corriente no
restauraba el orden. Se revisaron Corona.loadLayout/saveLayout y Applet.saveState de 6.7.5:
la exportación a otro nombre copia estado con copyTo bajo Configuration. El esquema de un
**containment** usa su grupo principal; AppletOrder está en Containments/<id>/General y no en
Configuration/General. Se corrigió el ensayo para usar el mismo ciclo que el ejecutable:
loadLayout del archivo antes de crear containments, saveLayout del mismo propietario y sync.
No se modifica libplasma ni se escribe un INI paralelo para ocultar el problema.

El test comprueba el grupo nativo correcto, ausencia de la instancia retirada, configuración
por instancia conservada y ausencia de un subárbol Applets duplicado bajo Configuration.
Otro proceso vuelve a cargar Corona y el QML original: recupera tres instancias en el orden
pedido, la opción propia guardada y posiciones crecientes del panel. Staging/probePanel ya
usaban loadLayout/saveLayout sobre su mismo archivo y siguen pasando.

Las dos suites CTest pasan normales y ASan, con **14 resultados UI aprobados por paquete**
en el ejemplo KDE y Andromeda; también pasan las invocaciones separadas de lectura de panel y
configuración. ASan usa detect_leaks=0; no certifica fugas ni todas las bibliotecas instaladas.
Pasan siete tests Python de migración y siete de manifiestos, py_compile y diff. Evidencia:
`BREEZE_R4_PANEL_API_RESULTS.json`, con drivers, logs, límites y hashes de fuentes.

Se restaura además el prompt R4 de BREEZE_PLAN_V2.md desde el encargo del usuario de esta
conversación: el bloque contenía sólo «ewe» y carecía de cierre. No se amplía el alcance a R5.
Arquitectura, guía upstream y avisos de procedencia actualizados; sin dependencias nuevas.

**R4 continúa pendiente de la integración de sesión:** superficies duraderas por monitor,
negociación/foco/escala/reservas Wayland, activación/rollback/ciclo de skins y descarga KNS.
Las dependencias por paquete —backends de ventanas/escritorios, favoritos KAStats, otras
ventanas y callbacks/KCM sin adaptador— mantienen sus capacidades pendientes, sin una promesa
de universalidad. La API está dentro del auxiliar: un editor fuera de él requiere transporte
IPC y ciclo de vida. No hay instalación, cambio de panel/skin, reinicio, plugin load/unload,
reactivación de sombras/miniaturas, commit ni push. Rollback: retirar la ampliación de
PanelSession y su enlace en la vista experimental; no hay estado de usuario que restaurar.

## 2026-11-13 — Primera prueba en la sesión Wayland real (Hyprland 0.56.2)

Las ejecuciones anteriores no podían abrir los sockets de la sesión. Esta sí: vista
`--native-panel --layer-panel` con Andromeda instalado en el entorno desechable, sin bus de
sesión, sin plasmashell/KWin y sin tocar el panel Breeze activo. Clics con un ratón virtual
uinput creado sólo durante cada comprobación; puntero y ventana con foco devueltos después.
Evidencia: `BREEZE_R4_WAYLAND_SESSION_RESULTS.json`.

| Hallazgo en sesión | Causa | Corrección |
| :--- | :--- | :--- |
| El menú de Andromeda salía en la esquina superior izquierda de la salida | Qt Wayland mueve toda ventana de primer nivel al origen de su salida: se perdían la posición del panel (mapToGlobal) y la x/y pedida por el paquete | `QT_WAYLAND_DISABLE_FIXED_POSITIONS` sólo al crear QApplication y fondo con alfa, igual que `shell/main.cpp` de plasma-workspace 6.7.5; el panel publica su posición anclada en QWindow |
| El avatar flotante (Dialog tipo Notification) aparecía como ventana normal de Hyprland en el centro de la LG | Los Dialog no interactivos quedaban sin adaptar | Capa Overlay sin teclado, posición pedida por el paquete; tipo, flags y región de entrada intactos |
| El segundo clic en el lanzador no lo cerraba | El panel tomaba el foco del teclado y `hideOnWindowDeactivate` cerraba el menú antes de que el clic lo volviera a abrir | Panel transparente, sin marco y sin foco (`KeyboardInteractivityNone`), con OnDemand sólo con `AcceptingInputStatus`, como `PanelView` 6.7.5 (que ya usa LayerShellQt) |
| El menú tapaba el propio icono | Andromeda supone el panel pegado al borde; la vista deja 64 px de hueco | La posición pedida se ajusta al área disponible sin la franja del panel y se devuelve a la QWindow, para que el avatar (que se calcula desde `root.x/y`) la siga |

Resultado comprobado en los dos monitores, elegidos por descripción (`--output`):

| Salida | Panel | Menú | Avatar | Ventanas sueltas |
| :--- | :--- | :--- | :--- | :--- |
| LG ULTRAFINE (origen 2560,0) | 2560,2048 640×48 | 2560,1532 680×516 | 2845,1477 110×110 | 0 |
| MAG 274Q X24 (origen 0,720) | 0,2048 640×48 | 0,1532 680×516 | 285,1477 110×110 | 0 |

Abrir con el icono, cerrar con un segundo clic, clic dentro sin cerrar y Escape funcionan.
**No cierra al pulsar en el escritorio vacío:** Hyprland deja el foco del teclado en una capa
OnDemand si el clic no cae en ninguna superficie, y `hideOnWindowDeactivate` no se dispara
(en Plasma, KWin enfoca la vista del escritorio). Hace falta un focus grab o una capa que
recoja el clic; pendiente. El fondo translúcido del diálogo se ve sin desenfoque
(KWindowEffects no existe en Hyprland: requeriría una regla de capa) y la vista de panel no
dibuja fondo porque el paquete Shell de prueba no tiene un `views/Panel.qml`.

CTest normal y ASan (`detect_leaks=0`, como en las ejecuciones previas) pasan: 13 casos de
superficies (franja del panel y política de foco nuevos) e isolated-plasmoids con el ejemplo
KDE y Andromeda; el test de ventanas propias exige ahora que Notification/solo salida se
adapten sin teclado. Tests de migración y manifiestos OK. Capturas recortadas, revisadas y
borradas; sin procesos ni capas de prueba restantes.

**R4 sigue pendiente**, ahora con evidencia de sesión: faltan escala fraccionaria, otros
bordes/autoocultado/reservas reales, cierre al pulsar fuera, desenfoque y fondo del panel,
otros paquetes y su creación tardía de ventanas, activación como panel diario, migración/
rollback/ciclo de skins y descarga KNS. No se avanza R5 ni se cambia el panel activo.

### Continuación: cerrar al pulsar fuera con `hyprland_focus_grab_v1`

El pendiente anterior queda resuelto con el protocolo de Hyprland que usa Quickshell para
sus menús. `FocusGrab` genera en la compilación el cliente de `hyprland-focus-grab-v1.xml`
(paquete hyprland-protocols del sistema) y PopupAnchor lo inicia cuando se muestra un Dialog
interactivo con `hideOnWindowDeactivate`. Lista blanca: el propio Dialog, el panel (su
lanzador puede seguir cerrándolo, como un panel de Plasma que no toma el foco) y los Dialog
no interactivos visibles del paquete. Un clic fuera anula el grab y eso equivale a la
desactivación que KWin provoca: el Dialog se oculta. Sin el protocolo (offscreen, otro
compositor) no hace nada y el Dialog conserva su comportamiento.

| Comprobación en sesión (LG) | Resultado |
| :--- | :--- |
| Clic en el escritorio vacío | Grab anulado (`cleared` en el registro) y menú cerrado |
| Clic dentro del menú | Sigue abierto |
| Segundo clic en el lanzador / Escape | Cierra |
| Clic en el avatar | Está en la lista blanca (sin `cleared`); cierra el menú su propio código (`root.toggle()`) y pide `kcm_users`, que no se lanzó por no haber bus de sesión |

CTest normal y ASan (`detect_leaks=0`) 2/2, con un caso nuevo que comprueba que sin el
protocolo el grab es inerte. Dependencias de compilación declaradas: Qt6 WaylandClient y
hyprland-protocols (`requirements.json`, `docs/REQUIREMENTS.md`); avisos en
THIRD_PARTY_NOTICES. Siguen pendientes desenfoque, fondo del panel, escala fraccionaria,
otros bordes y paquetes, activación, migración y KNS.

## 2026-11-13 — páginas por módulo QML e inicialización nativa

Se conserva la evidencia de sesión anterior (§187 del contexto, con dos monitores y focus
grab). En esta ejecución `hyprctl -j monitors` devuelve `Couldn't open a socket (1)`; no se
intenta otra vía de acceso. El trabajo amplía el contrato de configuración en aislamiento,
sin revertir superficies/foco/protocolos ni sustituir el panel activo.

Se corrige un rechazo excesivo: configUiModule/configUiComponent pueden describir un
componente QML normal. No equivalen por sí solos a una fábrica KCModule. Se revisaron los
ConfigCategory/ConfigModel de libplasma 6.7.5 y open() del AppletConfiguration.qml instalado.
ConfigurationSession usa QQmlComponent.loadFromModule con las rutas Qt originales; no busca
manualmente un archivo con el nombre del tipo ni crea una tabla de complementos admitidos.

| Descriptor/caso | Comportamiento implementado y probado |
| :--- | :--- |
| Pareja configUiModule/configUiComponent completa y source válido distinto | Se carga el componente del módulo, con prioridad nativa |
| Pareja completa cuyo módulo/tipo falta | Se conserva el error real y se bloquea Aplicar, aunque source sea válido |
| Pareja incompleta y source disponible | Se usa source, como el shell KDE |
| Pareja incompleta sin source | Error explícito; no control de guardado operativo |
| Source absoluto preservado por ConfigModel | Se convierte a URL local y se carga con el contexto nativo |
| Raíz no Item o required desconocido | Se rechaza con su diagnóstico; no se oculta con el aviso genérico de ausencia de páginas |
| pluginName/KCM sin adaptador | Continúa bloqueado; cargar módulos QML no anuncia soporte adicional de KCModule |

También se corrige la inicialización tardía de las páginas: beginCreate crea la jerarquía,
setInitialProperties entrega sólo las propiedades declaradas title/cfg_/Default/Immutable y
completeCreate completa el componente. Así las propiedades required quedan satisfechas y
Component.onCompleted ve los valores nativos actuales, incluidos los guardados al reabrir.
La localización y el Applet se mantienen en el contexto ConfigView original. Callbacks de
carga/guardado especiales y claves sin esquema/adaptador conservan sus bloqueos anteriores.

--probe y --exercise usan ahora esa misma fábrica. El primero expone loader/module/component
y configurationError; el segundo aplica mediante ConfigurationSession en lugar de guardar
el esquema por una vía distinta. Se comprueban un probe de módulo válido y otro con error;
la prueba booleana CLI sigue sin equivaler a toda la matriz de tipos/configuración.

### Pruebas y procedencia

Un módulo propio se copia a una ruta QML_IMPORT_PATH temporal y nueve paquetes propios se
instalan/retiran mediante KPackage. El fixture principal combina una página por archivo con
otra por módulo, ambas con propiedades obligatorias. Demuestra valores/título antes de
completar, contexto plasmoid/localización disponible, sincronización del texto entre páginas,
Aplicar con efecto en la representación Plasmoid.configuration, Cancelar/Predeterminados sin
escritura hasta Aplicar, clave oculta del esquema, dos instancias y lectura en proceso nuevo.
Los otros ocho casos cubren los descriptores y errores de la tabla.

Estos fixtures **no son un complemento tercero**. Las suites completas vuelven a cargar el
ejemplo KDE y Andromeda y a comprobar sus páginas/opciones reales con la fábrica común,
además de panel/acciones, superficies, focus grab inerte offscreen, instalación/retirada y
staging. Pasan dos suites CTest normales y dos ASan; cada ejecución de las suites UI tiene
**24 resultados aprobados**, sin fallos, y lecturas independientes en procesos nuevos.
ASan usa detect_leaks=0 y no certifica fugas ni instrumentación de todas las bibliotecas KDE.
Pasan también siete tests Python de migración y siete de manifiestos, py_compile y diff.

Evidencia: `BREEZE_R4_CONFIG_PAGES_RESULTS.json`, con ambos drivers/logs, probes, hashes de
fuentes y del AppletConfiguration.qml consultado. Builds de esta continuación en
/tmp/bwm-r4-config-pages-build y /tmp/bwm-r4-config-pages-asan; las fuentes libplasma se
reextraen del tarball 6.7.5 disponible en distfiles. No se altera el paquete externo instalado.
Arquitectura, guía upstream y procedencia actualizadas; no hay dependencias nuevas.

**R4 sigue pendiente** de integración/activación/migración/rollback/ciclo de skins, KNS remoto
y los pendientes Wayland/visuales ya enumerados, además de las capacidades de paquetes sin
adaptador. No se repite aquí la matriz de sesión ni se afirma aceptación de módulos QML de
terceros. Sin cambios de skin, reinicios, plugin load/unload, servicios duplicados, activación
de sombras/miniaturas, instalación de producción, commit o push. Rollback: revertir la fábrica
de páginas/uso común en el CLI y retirar sus fixtures; no se escribió configuración de usuario.

## 2026-11-13 — marco original Panel.qml sobre ContainmentView

Se resuelve el hueco visible del auxiliar: org.kde.panel sólo aporta el contenido. El fondo
vive en views/Panel.qml del paquete de shell. PanelViewHost deriva de ContainmentView y
carga ese QML mediante KPackage desde org.kde.plasma.desktop, sin copiarlo ni modificarlo.
El ejecutable lo usa en --panel-preview/--layer-panel-preview; la barra diaria no cambia.
Las configuraciones siguen usando el paquete mínimo y la fábrica ya probada de R4.

El adaptador registra sólo los enums Global que el PanelView original publica en su módulo
QML, con valores de 6.7.5. Aporta geometría, límites, política fija y conexión del containment,
sin anunciar una implementación completa del controlador PanelView. Configurar se enruta por
el método virtual de ContainmentView hacia una PanelSession que no conecta por segunda vez
configureRequested. El test acredita una única apertura y el cierre normal de configuración.

| Aspecto | Efecto/contrato real | Prueba ejecutada |
| :--- | :--- | :--- |
| Fondo y tema | FrameSvgItem del Panel.qml original; assets de PlasmaCore/KSvg | Dos paquetes Plasma/Theme propios instalados/retirados con KPackage; cambia el color renderizado al cambiar el tema en la misma vista |
| Bordes | Prefijos north/south/west/east del QML y flags KSvg del adaptador | Prefijo visible, color esperado y borde omitido comprobados en las cuatro orientaciones |
| Geometría | Longitud preferida del contenido separada de los límites de superficie; grosor y mínimo del SVG | 640×48, límites 320→640, error de rango inválido, cambio horizontal/vertical y grosor menor comprobados |
| Flotación | Márgenes fijos del tema y floatingnessTarget; animación Kirigami InCubic/OutCubic | Destino 0↔1 y dimensiones del contenido/marco; fixture con márgenes 2 px deja 636×48 dentro de 640×52 |
| NoBackground | El propio QML deja de dibujar los SVG | Píxel de fondo pasa de alfa no nula a cero |
| Máscara | panelMask y desplazamiento flotante originales → QWindow.setMask | Preparación del cliente; aplicación efectiva de la región en Wayland aún sin certificar |
| Opacidad | Políticas fijas Opaque/Translucent y flags nativos | Cambio de estado original probado. Offscreen conserva el fallback KDE sin composición; no certifica el resultado Opaque en Wayland |
| Adaptable/efectos | Adaptive rechazado con explicación; capacidades sin backend siguen false | No activa ventanas KWin, blur, sombras externas ni reservas como si fueran operativos |

La prueba encontró un fallo de geometría durante la inicialización: el tamaño natural vacío
podía encoger el marco. length conserva ahora su significado de preferencia y los límites
de superficie se aplican aparte; la vista de ensayo limita ambos a 640 por defecto. En los
cambios de orientación se evita consumir el máximo del eje anterior antes de publicar los
nuevos límites. No hay recarga del QML para cambiar tamaño, tema o política.

La destrucción detiene animación, desconecta el containment, cierra Configurar, separa el
AppletQuickItem y elimina el root QML mientras las propiedades derivadas aún existen.
Se revisaron ContainmentView/QuickViewSharedEngine/SharedQmlEngine de libplasma 6.7.5;
este último guarda el root en QPointer y no lo vuelve a destruir. ASan cubre la ruta.

### Comprobación del ejecutable y alcance

--probe-panel-frame usa la misma ruta de arranque del panel, muestra la vista sobre la
plataforma seleccionada y termina con JSON de fuente, adjunción, dimensiones, readback y
capacidades. El driver fuerza offscreen. Verifica que la vista contiene org.kde.panel y
que hay imagen renderizada. El layout propietario del panel queda separado del de probes
de widgets: una ejecución previa de --probe no debe hacer que el panel envuelva un
containment null. Se mantiene el formato nativo Corona; no se genera otro appletsrc a mano.

Pasan dos suites CTest normales y dos ASan, con **26 resultados UI aprobados por paquete**
en el ejemplo KDE y Andromeda, más las lecturas separadas y probes del ejecutable. Los
colores sintéticos se comparan con tolerancia 4/255 RGB y alfa superior a 250; no es una
calibración de color. NoBackground sí se comprueba con alfa cero. Los SVG son rectángulos
propios de prueba, no certificación universal de temas de terceros. ASan usa detect_leaks=0;
no certifica fugas ni instrumentación completa de las bibliotecas. Pasan siete tests Python
de migración y siete de manifiestos, py_compile y diff.

Evidencia: `BREEZE_R4_PANEL_VIEW_RESULTS.json`, con hash del QML original cargado, fuentes,
probes y ambos drivers/logs. Builds en /tmp/bwm-r4-panel-view-build y ...-asan. Se declara
KF6 Svg explícitamente en CMake y en el requisito del auxiliar; KSvg ya era obligatorio
para Breeze. Tabla REQUIREMENTS regenerada. Arquitectura, guía y procedencia actualizadas.

**R4 sigue pendiente:** este marco requiere aceptación en Wayland, escala fraccionaria,
bordes reales, máscaras, desenfoque y sombras externas. El control adaptable/autohide y
reservas, preferencias persistentes de la vista, activación/rollback/ciclo de skins,
migración y KNS remoto siguen pendientes. Las propiedades de la vista están en memoria;
no se ofrecen todavía como ajustes persistentes activos del usuario. La evidencia Wayland
de §187 permanece, pero no se transforma en aceptación de este nuevo marco. No se ejecuta
plasmashell ni KWin, ni se reinicia compositor/shell, cambia skin, carga plugins o reactiva
sombras/miniaturas. No hay instalación de producción, commit o push. Rollback: retirar el
enlace a PanelViewHost y volver a alojar el containment directamente en la vista experimental;
ningún estado de usuario necesita restaurarse.

## 2026-11-14 — revisión del alcance y corrección de migración de borde/orientación

El usuario pide hacer lo que falte de R4 y no introducir cambios si ya está cubierto. La
revisión detecta un defecto de migración: stage() fijaba BottomEdge/Horizontal y verify()
exigía ese resultado, aunque bar.plasma.edge indicara otro borde. El probe sólo comprobaba
orden horizontal. Conservar el JSON original archivado no hacía correcta esa disposición.

La propuesta conserva ahora el borde explícito. Si está vacío/ausente sigue bar.bottom,
cuyo valor de esquema es false (arriba), como PanelLogic.edge. No se convierten cadenas o
números en booleanos ni se adivina un borde inválido. C++ vuelve a obtener el borde desde
legacy.json autenticado y rechaza una propuesta que difiera. Se asignan Location/FormFactor
nativos antes de crear widgets y Corona conserva ambos en el layout original.

El informe lleva orientationContractVersion=1: edge/location/formFactor son obligatorios y
se contrastan con el origen y la lectura nativa. El verificador lee el archivo de origen una
vez y valida esos campos antes de cargar el layout. Los informes viejos sin ese contrato
siguen interpretándose según el bottom/horizontal que realmente producían; no se modifica
un staging existente para aparentar que ya conservaba el borde. Propuestas antiguas sin
edge sí pueden prepararse de nuevo: el stager lo deriva de su archivo de origen.

El probe dimensiona 640×48 o 48×640 según el FormFactor restaurado y comprueba el orden del
LayoutManager original por x o por y. Se ejecutan siete casos, cada uno con dos paneles:
top/bottom/left/right, bar.bottom true, bar.bottom false y valor de esquema sin borde. Todos
pasan stage→lectura en proceso nuevo→QML original→lectura posterior, con archivo fuente
idéntico. Se prueban propuesta incoherente, borde/fallback inválidos, informe actual al que
se quitan campos y lectura de un informe antiguo bottom/horizontal. Ningún caso activa el
panel diario ni publica una migración parcial tras los errores de preparación comprobados.

Pruebas: doce tests Python de migración y siete de manifiestos; CTest normal 2/2 y ASan 2/2,
incluida la matriz nueva y las 26 comprobaciones UI por paquete KDE/Andromeda de la regresión
previa. ASan detect_leaks=0, sin certificar fugas de todas las bibliotecas. py_compile/diff
correctos. Evidencia: `BREEZE_R4_ORIENTATION_RESULTS.json`; arquitectura/guía/plan actualizados.
Sin dependencias nuevas. Rollback: retirar el contrato de orientación de las propuestas y
staging nuevos; los layouts existentes no se han reescrito ni activado.

### Estado contra el encargo R4

| Criterio | Estado comprobado / límite |
| :--- | :--- |
| Corona/Containment/Applet/PlasmoidItem y páginas originales | Implementados en el auxiliar; originales KDE y opción propia de Andromeda pasan render/interacción/configuración en aislamiento |
| Compacta/completa, acciones, dos instancias y persistencia | Pruebas Qt/ASan y procesos nuevos; menús de Andromeda tienen además la evidencia Wayland anterior, sin extenderla a la matriz completa |
| Catálogo XDG/compilados y Obtener nuevos | Catálogo dinámico y diálogo con proveedor nativo conectados; jobs locales de instalar/quitar probados. Descarga remota desde KNS no verificada |
| Formatos KDE y migración | Serialización nativa, archivo completo del origen y claves desconocidas conservados; widgets/orden/borde/orientación releídos. Otras preferencias de vista y activación/rollback siguen declaradas pendientes |
| Interfaces para R5 | Contratos QObject de panel/widgets/acciones/configuración disponibles dentro del auxiliar; editor fuera del proceso necesitaría transporte |
| Temas globales y capacidades | Inventario separa defaults/SVG/decoraciones/plasmoides/fondos/scripts; scripts no ejecutados. Capacidades sin backend se explican, sin prometer compatibilidad universal |
| Puerta de salida en sesión | No se declara completa la aceptación real del nuevo marco, escala/bordes y ciclo de configuración/skins en Hyprland |

**R4 continúa pendiente de aceptación de sesión y de los límites de integración declarados.**
La comprobación actual de hyprctl devuelve `Couldn't open a socket (1)`; no se fuerza ni se
elude ese acceso. No se convierten todos los backends KWin sin adaptar en una promesa de
universalidad. El editor original completo corresponde a R5 y los efectos a R7: no se
implementan como ampliaciones de esta corrección. No hay cambios de skin, reinicios,
plugin load/unload, reactivación de sombras/miniaturas, instalación de producción, commit o push.

## 2026-11-14 — persistencia nativa de las preferencias del marco

PanelViewHost tenía propiedades visuales en memoria. Se añade PanelViewSettings para las
seis preferencias cuyo efecto ya implementa el marco experimental, usando KConfig y el
plasmashellrc original. Se ha contrastado el contrato con panelview.cpp y sus setters,
ShellCorona::applicationConfig y la identidad plasmashell de main.cpp, versión 6.7.5.
No se guarda configuración de la vista dentro de un applet ni se crea un formato BWM paralelo.

En esta tabla, B = PlasmaViews/Panel <containment-id>, D = B/Defaults y R =
B/Horizontal<ancho lógico Qt> o B/Vertical<alto lógico Qt>.

| Preferencia/API del auxiliar | Archivo/grupo nativo | Efecto real en el marco | Verificación |
| :--- | :--- | :--- | :--- |
| floating | plasmashellrc, B | Flotación y objetivo de la animación del Panel.qml original | Aplicar, objetivo 1, recarga y proceso nuevo |
| floatingApplets | plasmashellrc, B | Propiedad original que consume Panel.qml para sus applets | Cambio del estado de la vista y lectura nativa |
| panelOpacity | plasmashellrc, B | Modo original Opaque/Translucent en Panel.qml | Estado aplicado y persistido; Adaptive rechazado |
| thickness | plasmashellrc, D | Grosor efectivo, respetando el mínimo del tema | Aplicación de 40 px, recarga y proceso nuevo |
| minLength / maxLength | plasmashellrc, R y D | Límites de la superficie, separados del tamaño natural | Ancho efectivo 360 px, precedencia y fallback vertical |

El nombre relativo al abrir KConfig conserva XDG_CONFIG_DIRS/kdedefaults. Se escriben los
enteros nativos; minLength/maxLength se guardan en resolución y Defaults como los setters
originales. Se conservan claves ajenas y el segundo panel. viewSettings es la instantánea
cargada/guardada; los setters visuales sólo previsualizan. reloadViewSettings relee y aplica,
descartando la vista previa; applyViewSettings valida, guarda y verifica antes de aplicar.
La carga inicial aplica las preferencias antes de crear el marco QML. El cambio de ámbito
de salida/orientación obliga a releer antes de guardar.

Una transacción valida tipos, rangos y el estado combinado, comprueba inmutabilidad y firmas
de todos los destinos modificados, incluso Defaults oculto por la resolución actual. Un
QLockFile por archivo serializa los escritores BWM; KConfig mantiene su bloqueo/mezcla
nativos. No se promete compare-and-swap con KCM externos que no usan ese bloqueo BWM.
Cambios externos en claves no editadas se conservan. Un sync fallido marca limpio al
escritor privado para que su destructor no reintente una escritura ya informada como fallida.
No hay watcher ni escritura por cada movimiento de un deslizador.

Las claves pedidas desconocidas, Adaptive y valores inválidos se rechazan. Un archivo que
declare Adaptive o políticas incompatibles de visibilidad, alineación, longitud u offset
no abre una vista que las ignore: devuelve el motivo sin reescribirlas. Su ausencia conserva
los defaults seguros del ensayo; no escribe políticas nuevas implícitamente. Autohide,
reservas, adaptación a ventanas, blur y sombras externas siguen sin backend operativo.

Pruebas: CTest normal 2/2 y ASan 2/2, con **29 resultados QtTest por paquete** KDE/Andromeda;
lectura adicional de preferencias en otro proceso 3/3 en ambas ejecuciones. Se comprueban
grupos/precedencia, dos containments independientes, efecto en la vista, setters sin escritura,
claves ajenas, conflicto en Defaults oculto, edición externa no relacionada, escritor ocupado,
kdedefaults inmutable y lote mixto rechazado sin escritura parcial. Cambio de orientación
obsoleto y Adaptive almacenado se rechazan sin alterar bytes. Doce tests Python de migración,
siete de manifiestos y sintaxis correctos. ASan usa detect_leaks=0; no certifica fugas ni
instrumentación de todas las bibliotecas. Evidencia con logs y hashes de fuentes:
`BREEZE_R4_VIEW_SETTINGS_RESULTS.json`.

No hay dependencias nuevas ni instalación de producción. Las escrituras se prueban sólo
en raíces XDG temporales. Rollback de esta incorporación: retirar PanelViewSettings y su
integración en la vista experimental; ningún archivo de sesión del usuario se ha modificado.
**R4 sigue pendiente** de aceptación real del nuevo marco en Wayland/escala/bordes, ciclo
por skin, otras preferencias heredadas, migración/activación/rollback completos y KNS remoto.
La evidencia Wayland anterior conserva su alcance. No se cambia el panel diario ni se
reinicia el shell/compositor; sin plugins en caliente, efectos, commit/push ni trabajo de R5.

## 2026-11-14 — migración de preferencias de vista con lectura del marco original

Se conecta la preparación desde bar.plasma con las preferencias nativas del marco. Antes
sólo se archivaban esas opciones junto al layout. Ahora el directorio temporal contiene
plasmashellrc separado de layout (Corona), legacy.json y report.json. KConfig escribe los
grupos originales bajo los IDs que Corona asigna a cada panel. Es un artefacto con los
paneles preparados, **no un reemplazo del plasmashellrc completo de la sesión**; la futura
activación tendrá que mezclar por ID y respetar la cascada e inmutabilidad del destino.

| Origen heredado | Archivo/grupo/API | Efecto comprobado | Límite |
| :--- | :--- | :--- | :--- |
| thickness | plasmashellrc, PlasmaViews/Panel <id>/Defaults/thickness | Marco original con 38, 60 y 40 px; límites 24/128 y fallback 0→44 | El mínimo del tema puede elevar el grosor efectivo |
| floating y antiguo style=floating | plasmashellrc, PlasmaViews/Panel <id>/floating | Flag leído y floatingness 0/1 en Panel.qml | Docking según ventanas aún sin adaptar |
| style opaque/translucent/adaptive | plasmashellrc, PlasmaViews/Panel <id>/panelOpacity | Enum 1/2 aplicado y isOpaque correspondiente; enum 0 persistido | Adaptive se rechaza al abrir el marco, con motivo explícito |
| length/alignment/visibility/floatingGap y otros | Origen íntegro y deferredViewSettings del informe | Valores y motivos conservados, no anunciados como operativos | Pendientes controlador, geometría de salida o equivalencia nativa |

La propuesta Python y el stager C++ derivan los tres valores desde el mismo origen
archivado y rechazan diferencias. Se sigue PanelLogic.geometry para grosor: fallback de
cero a 44 y clamp 24..128, con validación estricta de tipo. El antiguo style=floating
equivale a Adaptive más el flag floating; no se transforma en Translucent para hacerlo
pasar. bar.plasma.opacity es un alfa numérico heredado y no se confunde con el enum KDE.

viewSettingsContractVersion=1 exige coincidencia entre origen, informe y archivo nativo.
Se detectan artefactos ausentes, valores alterados, omisión del contrato o de los pendientes.
Las propuestas antiguas pueden derivarse desde su archivo de origen; los stages antiguos
realmente sin preferencias de vista conservan su lectura. No pueden pasar por una prueba
de migración de preferencias del marco. Las claves nativas ajenas se conservan.

--probe-stage-frame abre PanelViewHost con el plasmashellrc preparado y el Panel.qml
instalado. Comprueba render, valores efectivos y disposición de los applets originales.
El destino se elige al construir la vista; la ruta habitual sigue usando plasmashellrc
relativo y kdedefaults. El probe separado --probe-stage mantiene el ensayo del containment.
Ni los informes de staging ni un probe offscreen certifican equivalencia de comportamiento
con el panel diario: visibilidad/reservas, alineación, longitud proporcional sin salida,
gap del tema y docking siguen declarados; Adaptive conserva su dependencia pendiente.

Pruebas normales y ASan: **CTest 2/2 en ambas**, ocho casos con dos paneles cada uno.
Seis casos de marco con modos fijos, incluidas ambas orientaciones, flotación y grosor
limitado/default; dos Adaptive rechazados sin reescribir el archivo. Cada caso pasa
preparación→lectura nueva→marco original/rechazo previsto→lectura posterior. El origen
permanece idéntico y la raíz aislada de preferencias ajena al staging no cambia. Se prueban
tipos de origen inválidos por la ruta C++, propuesta falsificada, informe/archivo alterados,
artefacto ausente, claves ajenas y compatibilidad antigua. Regresión de 29 resultados UI por
paquete KDE/Andromeda y lectura separada 3/3; 18 tests Python de migración y 7 manifiestos.
ASan con detect_leaks=0, sin certificar fugas ni instrumentación de bibliotecas del sistema.
Evidencia/logs/hashes: `BREEZE_R4_VIEW_MIGRATION_RESULTS.json`.

R4 sigue pendiente de los límites de integración y aceptación de sesión declarados: acceso
Hyprland continúa con `Couldn't open a socket (1)`. No se instala ni activa el auxiliar,
no se cambia skin/panel diario ni se reinicia compositor/shell. Sin efectos, plugins en
caliente, dependencias nuevas, commit/push o R5. Rollback: retirar el artefacto de vista de
staging y la ruta de su probe; los datos de la sesión no necesitan restaurarse.

## 2026-11-14 — ciclo de paneles por monitor y skin en el auxiliar

Se añade PanelRuntime sobre ViewCorona/PanelViewHost. Recibe un mapa de IDs nativos a
descripciones de salida que cubre exactamente los containments de panel existentes.
Mantiene como máximo una vista por containment y sólo las muestra con setSkin("plasma").
Retro/default retiran vistas y configuración sin borrar containments, IDs ni preferencias.
El llamador mantiene Corona viva, carga/guarda su layout propietario y proporciona los
bindings persistidos; el controlador no crea un formato alternativo de configuración KDE.

| Operación | Archivo/API | Efecto real comprobado | Alcance |
| :--- | :--- | :--- | :--- |
| Seleccionar salida | BwmOutput, QScreen fabricante/modelo/serie | Coincidencia completa, modelo+serie al final o modelo único; rechaza duplicados, serie errónea y subcadenas | Metadatos insuficientes dejan el panel en espera, sin fallback a DP-/índice/primario |
| Entrar/salir de skin | PanelRuntime.setSkin, PanelViewHost/PanelSession | Retira/recrea vistas manteniendo instancias y ajustes; configuración pendiente cancelada | API interna probada, sin hook de producción |
| Desconectar/reconectar monitor | Señales QGuiApplication, ViewCorona.bind/unbind | Retira antes del fallback Qt; recupera por descripción aunque cambien conector e índice | Dos QScreen de fixture, no monitores de Hyprland |
| Cerrar ventanas propias | PackageWindows.suspend | Colapsa applets y oculta sólo ventanas con dueño identificado; la ventana del otro panel permanece | Otros tipos/ventanas tardías no adaptados mantienen sus límites |
| Cambiar borde/resolución lógica | Location/FormFactor, PanelViewSettings | Recrea sólo la vista afectada y selecciona el ámbito nativo Vertical900 con longitud efectiva 400 | No certifica escala fraccionaria ni reservas |
| Reabrir en otro proceso | Corona.loadLayout y preferencias nativas, bindings del llamador | IDs, applets y grosor 38/60 conservados con enumeración y conectores cambiados | JSON de bindings del test es sólo fixture; autoridad diaria pendiente |

El resolvedor sustituye también la búsqueda parcial de --output: normaliza desc:, caja y
espacios, exige modelo identificable y no elige la primera coincidencia. El prefijo del
fabricante puede diferir si la secuencia final modelo+serie es la misma. Ante ambigüedad
la vista se retira y su snapshot lo explica; al desaparecer el duplicado se recupera.
Un panel con Adaptive sin backend falla con motivo sin impedir la vista del otro panel.

ViewCorona desconecta bindings reemplazados y ofrece unbind explícito: destruir la ventana
antigua no elimina su sustituta. Notifica screenRemoved con el índice anterior y recalcula
índices vigentes. PackageWindows usa QPointer al retirar ventanas, porque sus callbacks de
visibilidad pueden destruir otras. La configuración pendiente no se aplica al retirar una
vista. El controlador agrupa eventos de geometría con un timer; no escribe por cada evento.

--preview-stage DIR consume un staging verificado y ofrece una vista layer-shell explícita
sin reservas, sólo bajo raíces XDG temporales. Si ninguna descripción corresponde a una
salida, termina con diagnóstico. --probe-stage-runtime usa el mismo coordinador y devuelve
su snapshot tras 500 ms: el driver confirma que las salidas ausentes esperan y no crean
vistas en el monitor por defecto. No se ha ejecutado la previsualización en la sesión real.

Para integrar el ciclo diario faltan el hook común de skin, autoridad/persistencia de sus
bindings, activación/rollback y política de vida del proceso: el anfitrión persistente debe
mantenerse sin ventanas (quitOnLastWindowClosed=false) y conservar Corona más tiempo que
PanelRuntime. Tampoco implementa altas/bajas de paneles completos ni el editor R5.

Pruebas: **CTest normal 2/2 y ASan 2/2**, 33 resultados UI por paquete KDE/Andromeda, más
lectura específica del ciclo en otro proceso 3/3. Los cuatro tests nuevos cubren identidad,
vida del binding, ciclo/hotplug/ventanas/configuración/borde/resolución y reapertura. Para
ese ciclo se usa el widget propio desechable shared-config; la regresión de Andromeda no
se transforma en aceptación de todos sus servicios al cambiar de skin. Se crean/eliminan
pantallas sólo dentro del proceso Qt offscreen mediante QPlatformScreen y
QWindowSystemInterface 6.11.2. Se revisó su contrato de retirada/destrucción en el código
fuente instalado. No se simula ni se conecta un compositor. Dieciocho tests de migración,
siete de manifiestos y sintaxis aprobados. ASan detect_leaks=0, sin certificar fugas ni
instrumentación de todas las bibliotecas. Evidencia: `BREEZE_R4_RUNTIME_RESULTS.json`.

**R4 continúa pendiente de integración diaria y aceptación real en Hyprland**, escala y
otros límites registrados, además de KNS remoto. El intento actual de IPC sigue devolviendo
`Couldn't open a socket (1)`. No hay nuevas dependencias ni cambio del panel activo, skin,
compositor, plugins o efectos. Sin instalación en producción, commit/push ni avance a R5.
Rollback de este bloque: retirar el controlador y sus modos de preview; ningún archivo de
sesión del usuario ha cambiado. La evidencia Wayland de la continuación anterior se conserva.

## 2026-11-14 — conexión del hook de skins y parada de la previsualización

Se conecta hooks.skinChanged del manifiesto Breeze con el dispatcher común y el gestor
real. El script propio panel-session.py sólo actúa sobre una previsualización registrada
explícitamente: no arranca auxiliares ni sustituye el panel por defecto. La política de
Breeze queda en su carpeta; el dispatcher común confina las rutas y notifica las skins
involucradas sin añadir datos de una skin al módulo común.

| Paso | API/archivo | Efecto y verificación |
| :--- | :--- | :--- |
| Before | bwm-theme-manager → skin_changed → panel-session.py | Retira la vista antes de cambiar perfiles. Si falla la confirmación, aborta las mutaciones e intenta recuperar el auxiliar anterior; prueba sobre la función real con efectos externos sustituidos |
| After | Mismo hook, tras recargar el shell | Activa el estado de Breeze después de aplicar la skin; prueba Qt con dispatcher Python real y salida de fixture |
| Registro explícito | preview-isolated.py --follow-skin; active.json privado | Auxiliar arranca inactivo y sólo se activa tras registrarse. Un segundo registro no muestra otra vista ni borra el primero |
| Estado | RuntimeControl, control.json/ack.json temporales | Token, revisión creciente y confirmación. Rechaza revisiones antiguas y sesión ajena; watcher agrupado sin bucle por su propio ack |
| Parada | panel-session.py stop o Ctrl+C del envoltorio | Retira vistas, sale del bucle, guarda con Corona/config.sync y retira registro; CLI y envoltorio reales probados |
| Sin prueba activa | Ausencia de registro o PID terminado/reutilizado/zombie | No crea controles ni inicia procesos; casos Python aislados aprobados |

El registro vive bajo XDG_RUNTIME_DIR/bwm-plasma-host-preview, con directorio 0700 y datos
0600. Identifica el directorio temporal explícito, token y PID+inicio del auxiliar. Control
y ack son metadatos de integración, separados del layout y preferencias nativas; no se
crea un appletsrc alternativo. Lector/control y layout tienen dueños únicos; las órdenes
se serializan con bloqueo y esperan confirmación hasta 1,5 s (dispatcher: 3 s). Un token,
revisión o estado no reconocido no se aplica. El canal sólo ofrece skin/stop, no dispatch
de compositor ni servicios D-Bus. El descriptor del candado del gestor se cierra también
cuando el hook previo aborta: la prueba detectó y eliminó esa salida sin cierre explícito.

La confirmación acredita estado/retirada de vistas. El guardado final se comprueba con el
código de salida del proceso, sin convertir el ack en una promesa de disco/Wayland. El
auxiliar permanece vivo sin ventanas. Para Ctrl+C ignora SIGINT y deja que el envoltorio
envíe stop; ambos permanecen en el grupo del terminal. No se introduce un demonio separado.
La prueba encontró una carrera: al cerrar, el envoltorio podía borrar el ack antes de que
el publicador lo leyera. La limpieza ahora espera a esa transacción. Se prueban tanto
parada externa como interrupción del grupo de procesos propio del ensayo.

El comando de previsualización y parada está en README del auxiliar. Requiere paquete
seleccionado, panel nativo/layer-shell y descripción de monitor explícita; conserva datos,
configuración, caché, runtime y D-Bus desechables. No se ha registrado ni ejecutado en la
sesión real durante esta continuación. El panel diario permanece activo; retirar la prueba
no necesita restaurar ni sobrescribir su configuración.

Pruebas: **CTest normal 2/2 y ASan 2/2**, 34 resultados UI por paquete KDE/Andromeda. El nuevo
test usa el hook común real → publicador Python → RuntimeControl/PanelRuntime con widget y
salida Qt propios. El smoke ejecuta el binario independiente con cada paquete, sin salida
coincidente, y confirma vida sin ventanas, singleton y salida limpia. El envoltorio real se
prueba además con rechazo de duplicado, parada externa y Ctrl+C, registro eliminado y ack
consumido antes de limpiar. Estos smokes no validan el ciclo visual de Andromeda en Hyprland.
Dieciséis tests de publicación/errores/abort del gestor, 18 de migración, siete manifiestos,
cuatro de arranque y 16 del puente KDE aprobados, además de sintaxis/diff. ASan usa
detect_leaks=0; no certifica fugas ni instrumentación de bibliotecas del sistema. Evidencia
completa con logs/hashes: `BREEZE_R4_SKIN_CONTROL_RESULTS.json`.

**R4 sigue pendiente** de perfil/autoridad de bindings diarios, sustitución con activación/
rollback, servicios y controladores no adaptados, aceptación real Hyprland/escala/skins y
KNS remoto. El acceso IPC sigue denegado en este entorno. No se cambia skin/panel activo,
reinicia compositor/shell, carga plugins, activa efectos ni instala en producción. Sin
dependencias nuevas, commit/push o R5. Para retirar este bloque: quitar el hook del manifiesto
y el modo follow del auxiliar; no hay archivos de sesión que restaurar.

## 2026-11-14 — perfil nativo de ensayo, checkpoints y restauración

ProfileStore permite conservar y reabrir el perfil de prueba. Importa una copia capturada
de un staging, la verifica y publica un destino nuevo. Mantiene completos layout de Corona,
plasmashellrc, archivo fuente legacy.json e informe inicial report.json. bindings.json
guarda IDs nativos/descripciones/hash de origen y head.json selecciona una generación.
Son metadatos de integración separados de la configuración KDE; no se genera un appletsrc
alternativo ni se traduce el esquema de los plugins a otra lista de opciones BWM.

| Operación | Archivo/API | Efecto y verificación |
| :--- | :--- | :--- |
| Importar | --import-profile, copia validada por BwmMigration y Corona | Archivos nativos completos idénticos al origen; destino existente rechazado; desconocidos conservados |
| Reabrir | --serve-profile, Corona.loadLayout, PanelRuntime y bindings | Conserva paneles, monitores, widgets y opciones; no recrea dos instancias ni fuerza otro borde |
| Guardar | Archivo propietario de Corona + config.sync | Cierre de propietarios antes de crear checkpoint; dos reaperturas del CLI/envoltorio aprobadas |
| Punto de restauración | checkpoint, snapshots/<id>/snapshot.json | Copia los cinco archivos e inventaría hashes; publicación del directorio completo |
| Restaurar | restore, generation nueva y head.json atómico | Copia verificada a otra ruta; escritor KSharedConfig antiguo sólo puede alterar la generación anterior |
| Ocupar/validar perfil | Lease exclusivo, IDs/hash/rutas privadas | Host/checkpoint concurrente, binding incoherente, symlink o snapshot alterado rechazados sin seleccionar otro estado |

El informe migrado describe la procedencia inicial; sus antiguos valores no vuelven a
imponerse sobre widgets que el usuario haya editado. La validación usa una copia cargada
con Corona para no normalizar ni modificar los archivos del perfil inspeccionado. Los
bindings deben corresponder a sus containments de panel reales; las claves nativas y los
metadatos desconocidos se conservan. El hash del origen se comprueba contra el archivo
archivado y el informe.

La restauración usa una generación con ruta propia porque KSharedConfig puede retener el
nombre anterior. La prueba deja un propietario antiguo vivo y hace una escritura tardía:
no modifica el archivo restaurado. Se conservan generaciones anteriores y snapshots, sin
GC. Un fallo antes de seleccionar head puede dejar una generación no elegida; no sustituye
la vigente. El lease protege escritores cooperantes y la comparación optimista de head
detecta cambios externos; no promete CAS global con editores que ignoren el bloqueo. Los
hashes detectan inconsistencias, no son firmas ni garantía frente a un corte de energía.

preview-isolated.py --profile DIR --follow-skin usa el mismo hook/control y mantiene el
perfil elegido al cerrar. El auxiliar/caché/runtime/D-Bus siguen siendo desechables; busca
paquetes en las rutas XDG del llamador. Los paquetes, temas y activos externos no se
empaquetan en el snapshot. Al detener --serve-profile se retiran vistas, se sincroniza y
se cierran los propietarios de configuración antes del checkpoint automático.

Pruebas: **CTest normal 2/2 y ASan 2/2**, 36 resultados UI por paquete KDE/Andromeda, más
lectura específica del perfil en otro proceso 3/3. Dos tests nuevos importan dos paneles,
añaden un widget propio mediante PanelSession, cambian sus páginas originales con
ConfigurationSession y aplican grosor 52 frente a 44 desde PanelViewHost. Conservan sus
opciones tras el ciclo de skins, baseline/editado y proceso nuevo con otra enumeración.
Verifican bytes desconocidos, metadatos ajenos, hash alterado y escritura tardía del dueño
antiguo. El smoke usa CLI/envoltorio reales: dos reaperturas con los mismos bindings/IDs,
checkpoints automáticos al cerrar, perfil ocupado y restores inválidos rechazados. Estos
perfiles emplean reloj KDE y widget propio; la regresión de Andromeda no certifica todos
sus servicios en un perfil diario. Dieciséis tests del control, 18 de migración, siete de
manifiestos, cuatro de arranque y 16 del puente KDE, sintaxis/diff aprobados. ASan
detect_leaks=0, sin certificar fugas ni instrumentación de bibliotecas del sistema.
Evidencia/logs/hashes: `BREEZE_R4_PROFILE_RESULTS.json`.

**Alcance:** sólo directorios privados temporales; persiste entre ejecuciones del auxiliar,
no garantiza conservar /tmp tras reiniciar el equipo. R4 sigue pendiente de perfil/autoridad
diarios, sustitución del panel con activación/rollback de sesión, capacidades no adaptadas,
Hyprland/escala/skins y KNS remoto. No se ha activado ni registrado este perfil en la sesión
real. Sin cambios de skin/panel activo, reinicios, plugins/efectos, dependencias nuevas,
instalación de producción, commit/push o R5. Retirar este bloque sólo afecta a los perfiles
de ensayo; ningún archivo de sesión del usuario necesita restaurarse.

## 2026-11-14 — conservación del perfil en estado XDG fuera de /tmp

Se amplía el perfil anterior con exportToState y --export-profile SOURCE NAME. Conserva
el estado nativo seleccionado y todo el historial de snapshots publicados en
XDG_STATE_HOME/bwm/plasma/panel-profiles/NAME, con fallback Qt a ~/.local/state. El destino
usa otra generación/ruta propia y mantiene IDs, opciones, bindings y metadatos desconocidos.
La fuente no se mueve ni se modifica; sus generaciones no seleccionadas permanecen allí.
No se crea otro appletsrc ni se duplican esquemas de configuración KDE.

| Operación | Archivo/API | Efecto y verificación |
| :--- | :--- | :--- |
| Exportar sin abrir panel | preview-isolated.py --profile SOURCE --export-as NAME | Prepara auxiliares temporales, copia y termina sin registrar una previsualización |
| Almacenar fuera de /tmp | GenericStateLocation/bwm/plasma/panel-profiles | Autoridad dedicada, propia, privada y sin alias; no se admiten carpetas arbitrarias |
| Conservar historial | Snapshots completos e inventario de hashes | Archivos/manifiestos idénticos; un historial alterado no publica destino parcial |
| Publicar | Preparación en el filesystem de destino y rename | Destino existente/nombre con traversal rechazados; fuente conservada |
| Reabrir y guardar | --profile DEST --follow-skin, ProfileStore/Corona | Reabre desde otro proceso tras eliminar toda la fuente temporal; lease y checkpoint siguen funcionando |
| Restaurar copia exportada | --restore-profile | Recupera los bytes nativos del snapshot con otra generación, independiente del origen |

Los directorios nuevos de aplicación son privados. Se comprueban propiedad, rutas
canónicas, nombres y enlaces, sin cambiar permisos de directorios preexistentes. Sólo la
autoridad dedicada XDG amplía las raíces temporales permitidas. El proceso de visualización
mantiene configuración auxiliar/datos de escritura/caché/runtime/D-Bus temporales, y usa
las rutas XDG del llamador para localizar paquetes/activos. Éstos no se empaquetan en la
exportación y deben seguir instalados. No se añade selección activa ni autostart.

Pruebas: **CTest normal 2/2 y ASan 2/2**, 37 resultados UI por paquete KDE/Andromeda. El test
nuevo usa un XDG_STATE_HOME de fixture dentro de tests del repo, físicamente fuera de
/tmp; comprueba bytes, snapshots, metadatos, destino existente, nombres inválidos, carpeta
ajena a la autoridad y alias que intenta redirigir la publicación. El CLI/envoltorio real
exporta sin registro, elimina todo el perfil fuente y reabre/guarda/restaura la copia XDG
desde procesos nuevos. Verifica historial, bindings/IDs y rechazo de un segundo propietario.
Estos ensayos no escriben en el estado real del usuario y limpian sus carpetas de fixture.
La regresión sigue usando reloj KDE/widget propio para perfiles; no certifica servicios
de Andromeda ni cambios visuales en Hyprland. Dieciséis tests de control, 18 migración,
siete manifiestos, cuatro arranque y 16 puente KDE aprobados, sintaxis/diff correctos.
ASan detect_leaks=0, sin certificar fugas ni instrumentación de bibliotecas del sistema.
Evidencia con logs/hashes: `BREEZE_R4_STATE_PROFILE_RESULTS.json`.

**R4 sigue pendiente** de selección/activación/fallback del panel diario, autoridades de
producción, servicios/controladores sin adaptar, aceptación Hyprland/escala/skins y KNS
remoto. No se ha probado un reboot/corte de energía ni se promete conservación frente a
fallos de filesystem. El IPC de compositor sigue denegado aquí. No se ha creado un perfil
en el estado real del usuario, registrado vista ni cambiado panel/skin/compositor. Sin
reinicios, plugins/efectos, dependencias nuevas, instalación de producción, commit/push o R5.

## 2026-11-14 — disponibilidad del marco y consulta fresca del auxiliar

Se añade el diagnóstico necesario antes de diseñar la selección/activación diaria del
perfil. Hasta ahora un ack de skin sólo confirmaba que se había recibido/aplicado la orden;
no acreditaba que Qt hubiera enviado un fotograma. La nueva orden status obtiene una
instantánea de la revisión solicitada y no cambia skin, recarga preferencias ni recrea vistas.

| Control/estado | Archivo/API | Efecto real | Verificación |
| :--- | :--- | :--- | :--- |
| Consultar prueba registrada | panel-session.py status → RuntimeControl | Exige ack nuevo, token/revisión/contrato válidos y timeout | CLI real→Python→Qt y tests de ack antiguo/auxiliar sin respuesta |
| Carga y primer frame | PanelViewHost.presentationState, QQuickWindow | Distingue QML, visible/exposed, frameSubmitted, renderError | Marco original con Qt offscreen/software; espera al frame real |
| Generación de superficie | beforeRendering/frameSwapped/sceneGraphInvalidated | Un swap de una generación anterior no confirma la superficie nueva | Ocultar/mostrar y swap tardío inyectado por señales Qt |
| Disponibilidad agregada | PanelRuntime.readiness | Revalida identidad de salida, todas las vistas y errores al consultar | Pérdida de salida, vista oculta, error de scene graph inyectado y skin inactiva |
| Puerta de sustitución | runtime.replacementReady/blockers | Siempre false para este anfitrión de ensayo; explica reservas/validación pendientes | Incluso con renderReady=true no autoriza retirar el panel diario |

El comando disponible es:

```bash
python3 config/hypr/skins/plasma/scripts/panel-session.py status
```

Sin prueba registrada devuelve active=false y no crea archivos. Un PID vivo no basta para
dar el auxiliar por disponible; una respuesta anterior no satisface una revisión nueva.
Los auxiliares antiguos sin el contrato de diagnóstico compatible se rechazan. El canal
mantiene un solo vigilante de directorio y transacciones serializadas: no hay un watcher
por ventana ni escrituras por frame. Los callbacks del hilo de render sólo conservan
contadores atómicos compartidos; no acceden a QML ni a miembros derivados al destruirse.
Un error de render deja la vista no disponible hasta recrearla.

renderReady acredita un fotograma enviado por Qt para las vistas del panel. No acredita
presentación física, posición/foco/escala correctos, servicios de los plasmoides ni igualdad
visual con Plasma. Los bloqueos de este contrato no sustituyen el inventario por paquete.
La selección y activación/fallback de producción siguen pendientes: no se añade un selector
que prometa una sustitución antes de disponer de reservas y backends correspondientes.

La evidencia de esta continuación se conserva en BREEZE_R4_READINESS_RESULTS.json.
CTest normal **2/2** y ASan **2/2**: 38 resultados UI por paquete
KDE de configuración y Andromeda, sin fallos ni casos omitidos. La regresión incluye la
exportación/reapertura de perfiles fuera de /tmp y la retirada de sus fixtures. Veinte
pruebas Python de control, 18 de migración y siete de manifiestos aprobadas; sintaxis y
diff correctos. ASan usa detect_leaks=0: el primer intento con LeakSanitizer por defecto
falló por la restricción de ptrace del entorno; la ejecución final completa usa la opción
prevista para este harness. No certifica fugas ni instrumenta las bibliotecas del sistema.
No se ha registrado una prueba en la sesión real ni cambiado panel/skin/compositor.
El IPC de Hyprland sigue denegado (Couldn't open a socket (1)); R4 sigue pendiente de su
integración/aceptación de sesión, reservas/backends, autoridades de producción y KNS remoto.

## 2026-11-14 — política nativa de visibilidad y peticiones de reserva

Se conecta panelVisibility a un adaptador LayerShellQt explícito, activado con
preview-isolated.py --native-policy --follow-skin, tanto para paquete como para perfil.
El usuario autoriza alterar su sesión cuando sea necesario; la limitación de esta ejecución
sigue siendo el acceso denegado al socket del compositor. No se confunde esa limitación
técnica con falta de permiso del usuario ni con que la reserva sea inviable en Hyprland.

| Control/capacidad | Archivo/API | Efecto real | Verificación |
| :--- | :--- | :--- | :--- |
| NormalPanel=0 | plasmashellrc/PlasmaViews/Panel <id>/panelVisibility → LayerShellQt::setExclusiveZone | Solicita el grosor nativo, excluyendo padding flotante | QML original, propiedades reales LayerShellQt, cuatro bordes y flotación |
| WindowsGoBelow=3 | Misma clave/API | Retira la petición (-1), conservando vista/configuración | Escritura→reflow→lectura y reapertura desde otro proceso |
| Compatibilidad KDE | KConfig, clave global y fallback del grupo de resolución antiguo | Conserva claves ajenas, no escribe el fallback, respeta kdedefaults/inmutabilidad/concurrencia | Tests de precedencia, formulario obsoleto y lote bloqueado sin escritura parcial |
| Geometría de reserva | Tres anclajes, margen perpendicular final, exclusiveEdge | Pide longitud personalizada alineada al inicio sin depender del protocolo v5 | Propiedades Qt en los cuatro bordes; superficie que no cabe retira petición y da error |
| Vida de la vista | PanelRuntime y visibilidad/salida/skin | Ocultar/salir de Breeze retira la petición; volver relee política | Dos salidas/instancias independientes, Retro→Breeze y lectura nueva con conectores cambiados |
| Salida de respaldo Qt | QPointer de salida en BwmSurface | Retira/oculta antes de remapear a una salida distinta; runtime recrea por descripción | Cambio de QScreen inyectado: ninguna petición positiva en la salida ajena |
| Activación explícita | --native-policy → BWM_R4_NATIVE_PANEL_POLICY del hijo | La variable heredada se elimina si falta la opción | CLI/envoltorio real consulta nativePanelPolicy y se detiene limpiamente |
| Diagnóstico | reservationRequested/exclusiveZoneRequested | Expone lo solicitado, separado de reservedArea/waylandVerified=false | Status conserva replacementReady=false y muestra reserved-area-unverified |

NormalPanel es el valor por defecto sólo en este ensayo explícito. Sin la opción permanece
la política de previsualización habitual, sin reservas, y se rechaza un NormalPanel guardado,
incluido el fallback antiguo. Reabrir ese perfil exige --native-policy. AutoHide/Dodge,
alineación/offset no admitidos y longitudes fuera de salida se rechazan antes de escribir.
La capacidad no añade una pantalla de edición R5 ni un selector de producción.

Las fuentes 6.7.5 se han reextraído de los distfiles de Portage: plasma-workspace
SHA-256 94ab21e2243b7876f65c315f1e545081c6437f5bd0a041ca4fb6c2533ae874c9;
layer-shell-qt SHA-256 ccdcfec7081ca956f7a52c9113a4df3a226575bfbe98b56a2a9a4d7d7e19e8f0.
Se contrastan PanelView::restore/setVisibilityMode/updateExclusiveZone/updateLayerWindow,
el tamaño restringido de LayerShellQt y el XML de su protocolo. El código es propio; no
se redistribuyen esas implementaciones. No hay dependencias nuevas.

El alcance actual admite **un panel de política nativa por salida**. Si dos apuntan a la
misma, ambas vistas se bloquean con native-policy-output-conflict hasta disponer de un
controlador de disposición/apilamiento. El modo habitual de previsualización no cambia ese
comportamiento previo. La interacción con la barra diaria u otras superficies exclusivas,
la posición global real y el área útil aplicada por Hyprland siguen pendientes. El ensayo
puede modificar el área disponible cuando se ejecute en una sesión Wayland accesible;
las propiedades locales no certifican que el compositor haya aplicado la reserva.

Pruebas finales y hashes en BREEZE_R4_RESERVATION_RESULTS.json. **CTest normal 2/2 y
ASan 2/2**, 41 resultados UI por paquete KDE/Andromeda y 18 geométricos/de superficie en
cada compilación. El driver ejecuta lectura nueva de políticas, hijo/envoltorio con opción
explícita pese a variable heredada y parada limpia. Veinte pruebas Python de control,
18 de migración y siete de manifiestos aprobadas; sintaxis/diff/cmp correctos. ASan usa
detect_leaks=0; no certifica fugas ni instrumenta bibliotecas del sistema. Las comprobaciones
de tamaño esperan sus eventos Qt; no asumen redimensión o reserva física síncronas.

La migración mantiene la visibilidad diferida y archivada hasta validar activación completa;
no se reescribe staging
ni se retira automáticamente el panel diario. R4 sigue pendiente de esa integración,
backends/servicios, aceptación Wayland/escala y KNS remoto. No se cambia la sesión real ni
se reinicia compositor, se instala un plugin o se activan efectos R7 en esta continuación.

## 2026-11-14 — diagnóstico de acceso desde la sesión del usuario

Se comprueba UID 1000, variable de instancia presente y ambos sockets existentes, de tipo
socket y propiedad del usuario. hyprctl sigue devolviendo Couldn't open a socket (1).
La solicitud explícita de permisos ampliados para leer monitores se rechaza automáticamente:
la política Granular del ejecutor tiene sandbox_approval/rules/request_permissions=false.
No es una petición de nueva autorización al usuario; ésta ya consta. No se intenta sortear
esa restricción mediante otro intérprete, un terminal externo o un puente de ejecución.

Nuevo scripts/r4-session-check.py: consultas acotadas de monitores/capas y status fresco
del auxiliar registrado, sin dispatch, abrir ventanas, recargar o reiniciar. Si falla IPC
no prosigue con otras consultas. Cada hijo tiene timeout de tres segundos; no hay esperas
interactivas. Filtra los monitores y conserva sólo capas bwm-r4-*, sin títulos/direcciones
de clientes ni firma de instancia. Informe atómico privado 0600; rechaza destino enlazado
o ajeno. No añade paquetes/dependencias ni modifica la configuración de usuario.

Para ejecutar desde una terminal de la sesión:

```bash
python3 /mnt/HDD1TB/Projects/hyprland-de/config/hypr/skins/plasma/scripts/r4-session-check.py
```

Escribe /tmp/bwm-r4-access-1000.json para el UID actual y muestra su ruta. access-ok-no-native-preview
confirma consultas accesibles sin ensayo activo; observations-collected recoge observaciones
del ensayo. Ninguno certifica área útil, causalidad de reservas ni cierre de R4. Las reservas
totales podrían pertenecer a otras barras; hace falta prueba antes/durante/después y maximizado.
ipc-unavailable devuelve código 2 con informe, sin quedarse esperando.

Diez tests nuevos (timeout, respuestas inválidas, filtrado, ausencia de ensayo, reserva ajena,
permisos y enlaces) y 20 de control aprobados. Ejecución real aquí: ipc-unavailable, sockets
presentes/propios, realAreaVerified=false y r4Complete=false. Evidencia:
BREEZE_R4_ACCESS_RESULTS.json. Sin modificación del anfitrión C++ ni nuevas pruebas gráficas;
se conserva el alcance de la aceptación pendiente.

## 2026-11-14 — acceso local confirmado y ensayo temporal de reservas

El usuario ejecuta el diagnóstico en su terminal: access-ok-no-native-preview. Se lee el
informe /tmp/bwm-r4-access-1000.json: dos salidas, escala 1, reserva inferior de 44 px en
ambas, ninguna capa R4 ni auxiliar registrado. Es evidencia de acceso desde su terminal;
no cambia la restricción del ejecutor del asistente ni certifica reservas de R4.

Nuevo r4-reservation-smoke.py --run --output DESCRIPCIÓN_EXACTA. Usa el ejemplo original
KDE de configuración ya extraído y el binario normal compilado; permite rutas explícitas
--package/--binary. Exige Breeze activo, acceso y ausencia de otro ensayo. No cambia de
skin ni toca ventanas del usuario. Arranca el envoltorio aislado con --native-policy,
espera frame/capa, captura antes/durante/después y lo cierra automáticamente mediante su
parada/flush habitual. Los procesos tienen grupo propio; Ctrl+C también ejecuta la limpieza.
El plazo de inicio y consultas es acotado; si el grupo propio no responde se termina sólo
ese grupo. No añade un puente ni permite control remoto desde el asistente.

La comprobación exige incremento inferior exactamente igual a exclusiveZoneRequested,
reserva inicial restaurada, otras salidas/bordes iguales, geometría/escala estables y una
única capa nativa en la salida elegida. Salida ambigua/hotplug, delta distinto, ausencia de
frame/petición o limpieza sin confirmar no pasan. El informe diferencia reservationDeltaVerified
de maximizedWindowVerified/realAreaVerified/r4Complete: estos tres siguen false, porque no
se mueve ni crea todavía una ventana maximizada. Una coincidencia de reservas tampoco
demuestra equivalencia visual o atribución exclusiva frente a cambios externos concurrentes.

Diez tests nuevos de evaluación/limpieza con procesos simulados, además de regresión del
diagnóstico/publicador/manifiesto. No se ha ejecutado este nuevo ensayo gráfico desde el
asistente. Evidencia de preparación y acceso local: BREEZE_R4_RESERVATION_SMOKE_RESULTS.json.
El usuario sólo necesita ejecutar el comando documentado para obtener el siguiente informe
de sesión; no requiere dos terminales ni mantener manualmente abierto/cerrar el auxiliar.

## 2026-11-14 — ensayo local sin salida Qt y compatibilidad con serie ausente

El usuario ejecuta el ensayo: no alcanza frame/capa. El informe demuestra que el auxiliar
sí arrancó, se registró y respondió repetidamente con skin plasma/nativePanelPolicy=true,
pero su panel estaba en output-unavailable, sin vista ni petición de reserva. No es una
prueba de fallo del renderizador ni de reservas. Al terminar: código del envoltorio 130,
registro/capas retirados y 44 px inferiores en las dos salidas, iguales al inicio.

Se inspecciona qtbase-everywhere-src-6.11.2.tar.xz de Portage:
src/plugins/platforms/wayland/qwaylandscreen.cpp implementa manufacturer/model desde
wl_output, sin override de serialNumber. El contrato QScreen no ofrece aquí la serie EDID
que Hyprland añade a su descripción. El matcher anterior requería el sufijo modelo/serie
de Qt y rechazaba la descripción larga cuando Qt no aportaba serie. El backend/plataforma
del proceso real aún debe confirmarse con el nuevo inventario, no se presupone por el error.

OutputIdentity admite ahora la forma fabricante+modelo completos seguida de un único campo
de serie cuando Qt carece de ella y la coincidencia entre todas las salidas es única.
No usa substring, conector ni primer resultado. Fabricante/modelo distintos, campos extra,
duplicados y serie Qt conocida diferente se rechazan. Es una identidad por fabricante/modelo
únicos: no verifica una serie física ausente ni distingue sustituciones por otro equipo
idéntico. Resolver esa capacidad de EDID sigue pendiente si se exige identidad por serie.

Status añade qtPlatform y availableOutputs (fabricante/modelo/serie, serialAvailable,
descripción, nombre diagnóstico y geometría lógica). El conector no se persiste como binding.
El runner conserva ese inventario y da un error específico cuando no hay salida coincidente,
en lugar de atribuir todo a un timeout de frame. Se recompila el binario normal que usa el
comando del usuario; sin instalación de plugin o reinicio de sesión.
El runner de sesión selecciona explícitamente Qt Wayland para su hijo; no hereda xcb/offscreen
del terminal. Los ensayos automatizados separados siguen usando offscreen/software.

Regresión ampliada con los descriptores LG/MSI del ensayo y Qt sin serie, duplicados,
fabricante/modelo incorrectos y serie conocida diferente; inventario Qt/GUI comprobado.
Pruebas y hashes finales: BREEZE_R4_OUTPUT_MATCH_RESULTS.json. Se requiere repetir el ensayo
local para comprobar si esta compatibilidad resuelve el caso real y continuar las reservas.
Normal/ASan CTest 2/2, 41 resultados UI por paquete y 18 de superficie; 58 pruebas Python
R4 aprobadas. ASan detect_leaks=0, sin certificar fugas/bibliotecas del sistema. Sintaxis,
diff y sincronización AGENTS/CLAUDE correctos. No hay una nueva prueba Wayland real del
asistente ni se da por superado el delta de reserva.

## 2026-11-14 — fabricante Qt real distinto por una coma

El segundo informe local confirma plataforma wayland y los QScreen reales. MSI anuncia
fabricante «Micro-Star Int'l Co., Ltd.», modelo «MAG 274Q X24», serie vacía; Hyprland presenta
«Micro-Star Int'l Co. Ltd. MAG 274Q X24 0x01010101». La serie vacía ya estaba contemplada,
pero la coma del fabricante impedía la coincidencia completa. No era un fallo de capa/frame.
Al salir: auxiliar 130, sin registro/capas R4 y reservas originales de 44 px en ambas salidas.

Se corrige el caso comprobado: se localiza el modelo completo como campo y se comparan los
prefijos completos de fabricante ignorando únicamente comas en ambos. No se modifican
modelo o serie, no se eliminan guiones/apóstrofos/otros signos y se mantiene el requisito
de coincidencia única. Si Qt proporciona serie, no se descarta. Con dos pantallas iguales
la selección sigue ambigua; no se usa el conector ni el primer resultado.

La regresión usa los textos exactos del informe, en ambas direcciones de coma, y rechaza
duplicados, fabricante distinto, puntuación distinta en el modelo y series conocidas
incorrectas. Binario normal recompilado para el mismo comando del usuario; la prueba real
de reserva aún requiere repetirse. Resultados/hashes: BREEZE_R4_MAKER_MATCH_RESULTS.json.
CTest normal 2/2 y ASan 2/2, 41 resultados UI por paquete y 18 de superficie. ASan con
detect_leaks=0; sin certificar fugas ni bibliotecas del sistema. Diff y AGENTS/CLAUDE correctos.

## 2026-11-14 — reserva real confirmada en la sesión Hyprland del usuario

El usuario repite el ensayo con la corrección de fabricante y obtiene
reservationDeltaVerified=true/errors=[]. Se inspecciona y conserva el informe completo en
BREEZE_R4_RESERVATION_SESSION_RESULTS.json, con origen explícito de ejecución local del
usuario. No es una prueba ejecutada por el asistente ni levanta su restricción de acceso.

| Observación real | Antes | Durante | Después |
| :--- | :--- | :--- | :--- |
| Reserva inferior MSI (escala 1) | 44 px | 92 px | 44 px |
| Reserva inferior LG (escala 1) | 44 px | 44 px | 44 px |
| Capas R4 | Ninguna | Una bwm-r4-native-policy en MSI | Ninguna |
| Auxiliar registrado | No | Sí, Wayland y renderReady=true | No |

El panel solicita 48 px y Hyprland refleja exactamente ese incremento. La capa mide
640×48 y está en (0,2068), nivel 2; queda sobre la franja de la barra existente. Su borde
superior coincide con 2160−92=2068. Cierre del envoltorio 130 (parada automática por SIGINT
con flush/limpieza), sin errores ni reserva residual; ninguna salida ajena cambia.

Se da por validado **este delta de reserva y su retirada**: MSI, borde inferior, escala 1,
un panel temporal original KDE y coexistencia con la barra diaria de 44 px. No se amplía
esa aceptación a posiciones publicadas a Qt/popup, otros bordes, escala fraccionaria,
cambios de skin, servicios de paquetes o sustitución diaria. Las flags conservadoras del
auxiliar no se activan globalmente por una única prueba externa.

El informe mantiene maximizedWindowVerified=false, realAreaVerified=false y r4Complete=false:
todavía no se ha medido una ventana propia maximizada contra el límite útil. R4 sigue
pendiente de esa comprobación y del resto de integración/autoridades/backends/KNS descritos.
Esta continuación sólo registra evidencia de sesión; sin cambios de runtime ni repetición
innecesaria de tests de código.

## 2026-11-14 — ensayo opcional de ventana propia maximizada

El runner admite --maximize. Crea una única ventana Qt propia con app_id aleatorio y
temporizador de seguridad de 60 s, sin CSD de Qt y sin solicitar activación. No solicita
maximizado al cliente: usa kwin-window.py, el mismo gestor BWM de Breeze. Cada operación
comprueba proceso vivo, PID, clase aleatoria, dirección hexadecimal y cliente único antes
de pasar --pid/dirección al gestor. No opera sobre ventanas del usuario ni cambia de skin.
La ventana se coloca mediante to-screen en la descripción elegida, sin cambiar de workspace
al usuario; se restaura/cierra y retira su presnap por las APIs existentes al terminar.

Sólo se certifica escala 1/giro 0. El área esperada se calcula independientemente con
geometría/reserved de Hyprland; el marco observado procede del estado BWM y clientes reales.
Se exige modo completo y coincidencia de los cuatro valores (tolerancia 1 px), no sólo el
tamaño del contenido. La API breezebars-csd debe confirmar el registro propio por dirección/
PID y bordes coherentes: si falta, el resultado queda pendiente, sin inventar una barra.
No se activa ni recarga un plugin para obtener esa información.

maximizedDuring comprueba un maximizado nuevo con panel presente; tras cerrar el panel,
maximizedAfterWithoutRemaximize observa si se reajusta solo y lo refleja separadamente en
dynamicMaximizedWindowVerified. Después se restaura/maximiza de nuevo y mide maximizedAfter.
maximizedWindowVerified/realAreaVerified sólo son true si ambas mediciones explícitas, el
delta de reserva y la limpieza pasan. El reajuste automático no se da por hecho ni se
oculta tras volver a maximizar. r4Complete continúa false: no cubre el resto de aceptación.

Para ejecutar desde la terminal local con acceso:

```bash
python3 /mnt/HDD1TB/Projects/hyprland-de/config/hypr/skins/plasma/scripts/r4-reservation-smoke.py \
  --run --maximize --output "Micro-Star Int'l Co. Ltd. MAG 274Q X24 0x01010101"
```

La variante sin --maximize conserva el ensayo de reserva previo. Las raíces auxiliares Qt
son temporales, D-Bus aislado y Wayland explícito. El runner cierra su ventana aun cuando
falle una consulta/medición; los hijos y consultas tienen tiempos límite. No se expone una
vía de ejecución del asistente fuera de su política; el ensayo real lo lanza el usuario.

Regresión: CTest normal/ASan 2/2, 41 resultados UI por paquete, 18 de superficie y ciclo
del fixture nuevo offscreen con rechazo de identificador inválido. 67 pruebas Python R4
y siete de manifiestos aprobadas; incluye cálculo independiente, bordes/modo, identidad,
PID reutilizado, autoridad de decoración y limpieza del runner con excepción inyectada.
ASan detect_leaks=0, sin certificar fugas/bibliotecas del sistema. Evidencia de preparación:
BREEZE_R4_MAXIMIZED_PREP_RESULTS.json. No se ha ejecutado todavía esta medición en la sesión
del usuario ni se amplía la validación anterior de reserva a maximizado.

## 2026-11-14 — orden de argumentos corregido en el ensayo de maximizado

El usuario ejecuta --maximize: el panel vuelve a reservar 48 px en MSI (44→92→44), pero
el ensayo falla antes de medir la ventana. El error sin detalle procede de un código 1
sin stderr del gestor. Se identifica un error del runner: enviaba to-screen ADDRESS MONITOR,
cuando el parser real es to-screen MONITOR [ADDRESS]. El gestor no encontraba el supuesto
ADDRESS y rechazaba la operación; no ejecutaba la medida de maximizado. La ventana propia
se termina (-15), el panel se cierra (130), registro/capas retirados y reservas restauradas.

Se corrige start para usar el mismo constructor de órdenes guardadas por PID/dirección:
command('to-screen', 'desc:'+output). La prueba nueva ejecuta start y pasa los argumentos
generados por el argparse real de kwin-window.py, con sólo la consulta/movimiento sustituidos;
no se limita a verificar una lista fija de argumentos. Rechazos ahora incluyen acción,
código de salida y stderr/stdout o explicación explícita si ambos están vacíos.

Se separan además los resultados parciales: un fallo de la ventana ya no borra un delta
de reserva observado y restaurado. El runner lo reevalúa tras la limpieza y conserva
maximizedWindowVerified/realAreaVerified=false y salida de fallo para --maximize. Un test
de excepción de medida comprueba simultáneamente limpieza, delta conservado y fallo de
maximizado. No se disfraza una reserva correcta como medición de ventana completada.

69 pruebas Python R4, regresión del gestor de ventanas y manifiestos aprobadas; sintaxis,
diff y AGENTS/CLAUDE correctos. No cambia C++ ni necesita recompilar/reinstalar plugins.
Evidencia: BREEZE_R4_MAXIMIZED_CLI_RESULTS.json. Falta repetir el mismo comando local para
medir el marco; no se declara una nueva validación gráfica del asistente.

## 2026-11-14 — maximizado explícito real validado; reajuste automático pendiente

El usuario ejecuta el ensayo corregido: delta de reserva, maximizado y área real true;
reajuste automático false, errors=[]. Se conserva el informe en
BREEZE_R4_MAXIMIZED_SESSION_RESULTS.json, ejecutado desde la sesión local del usuario.

| Medición de la ventana propia | Esperado (x,y,w,h) | Observado | Resultado |
| :--- | :--- | :--- | :--- |
| Maximizar con panel | 0,720,2560,1348 | 0,720,2560,1348 | Correcto |
| Retirar panel sin maximizar de nuevo | 0,720,2560,1396 | 0,720,2560,1348 | No se reajusta |
| Maximizar de nuevo sin panel | 0,720,2560,1396 | 0,720,2560,1396 | Correcto |

Modo BWM 3 y autoridad de decoración propia confirmados, con barra superior de 28 px incluida
en el marco (otros bordes 0). Con el panel, el marco termina en y=2068, inicio de la capa
nativa. Sin panel, un nuevo maximizado termina en y=2116, límite de la barra diaria de 44 px.
Reservas MSI 44→92→44, LG inalterado, panel 130/ventana -15 al concluir, sin registro/capas
residuales. Validación limitada a MSI, borde inferior, escala 1/giro 0 y maximizado explícito.

Queda confirmado un hueco: al retirar el panel la ventana ya maximizada mantiene altura
1348 y deja 48 px sin usar hasta maximizar de nuevo. Añadir un panel sobre una ventana
previamente maximizada todavía no se ha ensayado. No se oculta esta falta de seguimiento
automático detrás del éxito explícito ni se habilita una capacidad global de producción.
R4 permanece abierta junto con el resto de integración/autoridades/backends/KNS. Esta
continuación sólo registra evidencia; sin cambios de runtime o tests de código repetidos.

## 2026-11-14 — seguimiento automático de máximos; nueva medición local pendiente

Se implementa la respuesta al hueco medido arriba: kwin_area.Runtime se integra en el
vigilante existente de kde-config-bridge. Sigue el área efectiva de Hyprland, no un grosor
fijo ni el estado solicitado por Qt. Reutiliza marco/contenido y reglas BWM y pide bordes
autoritativos por dirección/PID. No vuelve a maximizar, guarda geometría temporal como
restauración ni modifica presnap, etiquetas, foco o workspace.

| Comportamiento | Archivo/API | Efecto real previsto | Verificación de esta continuación |
| :--- | :--- | :--- | :--- |
| Añadir/retirar reserva | kwin_area.py → monitors.reserved → resize/move Lua | Reducir/ampliar los ejes BWM maximizados hasta el área útil | Ambos sentidos/ejes y otro monitor en fixtures; sesión pendiente |
| Decoración | breezebars-csd v1 por dirección/PID | Incluir los bordes reales al convertir marco/contenido | Identidad reutilizada, registro ausente y tamaño comprobados con IPC simulado |
| Autoridad de usuario | kwin_rules.resolve + tags opt-out | Respetar Force de geometría y exclusiones explícitas | Force/remoción de regla y opt-outs probados |
| Cambio de estado/skin | bloqueo de transición + guardas Lua actuales | No mover fullscreen, especiales, minimizadas o ventanas reemplazadas | Lua ejecutado con PID/monitor/skin/etiquetas mutados; sin compositor real |
| Aplicación agrupada | watch existente, 0,5 s, batch ≤16 | Un dispatch por tanda, sin recargas y con confirmación posterior | Batch Lua de dos ventanas ejecutado; tres reintentos máximos comprobados |
| Cargar el código nuevo | kde-config-bridge.py restart / --refresh-area-watcher | Recargar sólo el puente y conservarlo activo | Ciclo/orden y marcador privado fresco con PID/inicio probados de forma aislada |

El observador se activa al entrar/reiniciar el puente de Breeze. El proceso que ya corre
no recarga por editar su Python. El siguiente comando local carga la actualización y hace
un único ensayo automático con la ventana propia ya maximizada antes de abrir el panel:

```bash
python3 /mnt/HDD1TB/Projects/hyprland-de/config/hypr/skins/plasma/scripts/r4-reservation-smoke.py \
  --run --maximize --refresh-area-watcher \
  --output "Micro-Star Int'l Co. Ltd. MAG 274Q X24 0x01010101"
```

El puente permanece activo y puede ajustar las ventanas BWM que ya estén maximizadas cuando
cambie el área útil. No reinicia compositor, Quickshell ni plugins. Su marcador confirma
únicamente baseline/proceso; el runner mide el marco de la ventana contra el área observada.
maximizedDuringWithoutRemaximize y maximizedAfterWithoutRemaximize no ejecutan restore/full.
dynamicMaximizedWindowVerified exige ambas coincidencias, baseline correcto y delta restaurado;
dynamicMaximizedContract=panel-appearance-and-withdrawal identifica el alcance ampliado.
Las mediciones explícitas se conservan independientes. El runner sigue cerrando sus procesos
y guardando fallos parciales, sin invocar comandos directos sobre ventanas ajenas.

159 pruebas Python aprobadas: R4 89 (incluye 16 del observador), puente 18, reglas 18,
ventanas 13, manifiestos 7, arranque 4 y ajustes R3 10. Se ejecuta el intérprete Lua real
con API de compositor simulada, sin saltos por falta de Lua; esto valida los guardas y
sintaxis, no la interacción gráfica. No hay cambios C++ ni nuevas dependencias; no se repite
la matriz C++ anterior. Procedencia, hashes y logs: BREEZE_R4_AREA_TRACKING_RESULTS.json.

El asistente no ha reiniciado el puente ni ejecutado el nuevo ensayo gráfico: sigue sin
acceso IPC real. El último resultado de sesión continúa siendo el fallo dinámico de §206;
la corrección está implementada y probada aisladamente, pendiente de aceptación local.
R4 sigue abierta por esa aceptación y el resto de integración/backends/autoridades/KNS;
sin avanzar a R5/R7 ni sustituir el panel diario.

## 2026-11-14 — reajuste automático validado en la sesión Hyprland

El usuario ejecuta el comando con --refresh-area-watcher. El runner confirma el nuevo
baseline del puente y devuelve reserva/maximizado/dinámico/área real true y errors=[]. Se
conserva el informe íntegro con origen y SHA-256 en BREEZE_R4_AREA_SESSION_RESULTS.json;
no se sustituye la evidencia anterior del fallo. Las nueve fuentes coinciden con los hashes
de BREEZE_R4_AREA_TRACKING_RESULTS.json. El asistente no ejecuta órdenes gráficas nuevas.

| Medición de la ventana propia | Esperado (x,y,w,h) | Observado | Resultado |
| :--- | :--- | :--- | :--- |
| Maximizar antes del panel | 0,720,2560,1396 | 0,720,2560,1396 | Correcto |
| Aparecer panel sin remaximizar | 0,720,2560,1348 | 0,720,2560,1348 | Correcto automático |
| Maximizar explícitamente con panel | 0,720,2560,1348 | 0,720,2560,1348 | Correcto |
| Retirar panel sin remaximizar | 0,720,2560,1396 | 0,720,2560,1396 | Correcto automático |
| Maximizar explícitamente sin panel | 0,720,2560,1396 | 0,720,2560,1396 | Correcto |

Las cinco medidas confirman modo completo 3, registro de decoración y borde superior real
de 28 px incluido en el marco (otros bordes 0). La reserva se reevalúa con la función pura
del runner: MSI 44→92→44 y LG inalterado. Capa nativa 640×48 en (0,2068); al retirarla el
marco recupera el límite y=2116 automáticamente, sin el hueco anterior de 48 px. Panel sale
130 y fixture -15 según el cierre esperado; no quedan capas ni previsualización registrada.

Queda validado el seguimiento de área útil para ese fixture, MSI inferior, escala 1/giro 0.
No es comparación visual manual ni prueba de maximizado en LG, ejes parciales, otros bordes,
escala fraccionaria, hotplug o cambios de skin. El auxiliar conserva sus indicadores de
capacidad genéricos sin verificar y replacementReady=false: una evidencia de sesión acotada
no habilita sustitución global del panel. R4 sigue pendiente de integración diaria,
autoridades/backends, KNS remoto y el resto de aceptación documentada. Esta continuación
añade evidencia y estado; sin cambios de runtime ni repetir pruebas de código sin cambios.


## 2026-11-14 — ciclo real de «Obtener nuevos» y puerta con widgets desconocidos

Por primera vez el ejecutor tiene acceso a Hyprland y a la red desde la sesión del usuario.

**Implementado.** `kns.cpp`: búsqueda/instalación/retirada sin diálogo con KNSCore 6.29 y el
proveedor nativo `plasmoids.knsrc` (los mismos `Entry`/`Transaction` que el diálogo). Sólo en raíces
XDG temporales (regresión: fuera de ellas sale con 2). Preguntas de KNewStuff respondidas siempre
Cancelar/No. El catálogo vivo informa del alta/baja. `kns-cycle.py` elige candidatos por el orden
de descargas de la tienda (excluye sólo Andromeda, ya usado en todo R4), rechaza **antes de cargar**
paquetes con binarios/scripts o fuentes de datos `executable` (filtro estático, no sandbox; sin bus
de sesión), ejercita la opción booleana propia en su página original, la relee en un proceso nuevo
y retira el paquete por KNS.

**Corregido al probarlo.** Thermal Monitor declaraba `cfg_lastSeenVersion` sin esquema y su página
se bloqueaba. `AppletConfiguration.qml` 6.7.5 sólo recorre `config.keys()` y llama a `saveConfig()`
antes de guardar: ConfigurationSession hace ahora lo mismo (antes bloqueaba ambas cosas). Fixture
propio `tests/callback-config` en la regresión. El cambio a búferes con alfa dejaba transparentes el
diálogo y la vista de prueba: pintan `Kirigami.Theme.backgroundColor`, como el original.

| Resultado sobre los 12 primeros widgets de la tienda (sin Andromeda) | Nº | Detalle |
| :--- | :--- | :--- |
| Supera la puerta | 3 | Thermal Monitor `pinned`, KDE Modern Clock `show_day`, Simple Application Launcher `paneSwap`: página original, Aplicar, Cancelar/Predeterminados sin escribir, segunda instancia intacta y valor releído en proceso nuevo |
| Metadatos antiguos | 6 | Instalan, pero sólo `KPlugin.ServiceTypes` sin `KPackageStructure`: KPackage 6.29 (`packageloader.cpp`) y por tanto el explorador de Plasma 6.7.5 tampoco los listan. No es límite de BWM |
| Rechazados antes de cargar | 3 | KDE Control Station, Panel Colorizer y HTML Clock ejecutan órdenes o traen scripts |

Los 12 se retiraron por KNS (paquete borrado, baja en el catálogo, estado `deleted`).

**Validado en la sesión Hyprland.** Modern Clock descargado por KNS, vista `--layer-panel` en el LG
elegido por descripción: «Configure…» abre su diálogo original (xdg toplevel 800×600); con un
puntero uinput temporal se desmarca «Show Day» y Aplicar escribe `show_day=false` en el
`bwm-plasma-host-appletsrc` nativo de esa instancia. Tras corregir el fondo se repitió la apertura.
Vista cerrada, raíz temporal borrada, sin capas/clientes del auxiliar; puntero y foco devueltos.

**Pruebas.** CTest normal y ASan 2/2 (ASan `detect_leaks=0`), 96 tests Python (R4 + manifiestos).
Evidencia y hashes: `BREEZE_R4_KNS_RESULTS.json`. Sin dependencias nuevas (KNewStuff ya requerido).

### Balance frente al prompt original de R4

| Criterio | Estado |
| :--- | :--- |
| Prueba aislada: widget original simple y de terceros con configuración propia | Hecho (ejemplos KDE, Andromeda, y ahora 3 de la tienda) |
| Compacta/expandida, acciones, tamaño, localización, main.xml, config.qml, páginas, Aplicar/Cancelar/Predeterminados, persistencia por instancia, dos instancias | Hecho (QtTest/ASan, proceso nuevo) |
| Resolución de rutas por KPackage confirmada | Hecho (arquitectura) |
| Descubrir paquetes XDG y originales KDE | Hecho (catálogo vivo, también compilados) |
| Formato original y migración desde bar.plasma sin pérdida ni appletsrc inventado | Hecho como staging verificado (activación diaria no) |
| Separar metadatos, configuración por instancia, disposición y preferencias BWM | Hecho |
| Interfaces para R5 (panel, containments, widgets, acciones, catálogo, configuración) | Hecho dentro del auxiliar (PanelSession) |
| «Obtener nuevos» con proveedor nativo y actualización del catálogo; instalar/quitar en aislado | **Hecho hoy**, con la tienda real |
| Temas globales: defaults, SVG, decoraciones, plasmoides, fondos, scripts | Hecho (inventario sin ejecutar scripts) |
| Capacidades no soportadas registradas por paquete | Hecho (catálogo + clasificación KNS) |
| Puerta: widget externo no conocido de antemano muestra y guarda su opción | **Superada hoy**, también en sesión |
| Informe, arquitectura y guía upstream | Actualizados |

**Pendiente, fuera de esa puerta (no se declara hecho):** sustituir el panel diario de Quickshell
(`replacementReady=false`, autoridades/selección/fallback), backends BWM de tareas/escritorios/
Mostrar escritorio, aceptación en otras escalas/bordes/giros/hotplug y cambios de skin reales,
desenfoque de fondos translúcidos, widgets que ejecutan órdenes (no se cargan sin revisión) y la
interfaz gráfica del diálogo KNS en la sesión (el ciclo usa su núcleo sin diálogo).
Rollback: retirar `kns.*`, `kns-cycle.py`, el fixture y las dos excepciones de ConfigurationSession.

## 2026-11-14 — continuación sobre e41c28d: reproducción local

El commit de Claude supera la puerta original; se conservan sus resultados de tienda y
Hyprland. El ejecutor actual vuelve a carecer de IPC (diagnóstico ipc-unavailable), por lo
que no se anuncian nuevas pruebas gráficas ni se altera el panel diario.

Se añade check-local.py como prueba CTest siempre disponible con BUILD_TESTING: instala
los tres paquetes propios en XDG temporales, prueba callback/saveConfig, claves auxiliares,
dos instancias y lectura nueva, páginas por módulo y compartidas mediante cinco funciones
QtTest ejecutadas en procesos separados, catálogo y retirada. También carga org.kde.panel
con el fixture elegido por defecto para el próximo ensayo de sesión. Offscreen/software,
sin bus de sesión ni acceso a tienda. La prueba local no sustituye check-isolated.py ni
la puerta externa/KNS y no prueba backends de producción.

El runner de reservas deja de depender de la extracción KDE y build antiguos de /tmp:
por defecto usa /tmp/bwm-r4-build y tests/shared-config del repo. --binary/--package siguen
permitiendo seleccionar el ejemplo original; el informe identifica las rutas utilizadas.
No se reinterpreta la evidencia anterior de sesión como una prueba de estos defaults nuevos.

Detectados tres metadata.json fuera del commit en callback-config/module-config/shared-config;
son fuentes propias necesarias, no descartarlos. Permanecen en el árbol sin seguimiento;
.git es de sólo lectura para este ejecutor y no se ha podido añadirlos al índice.
La siguiente revisión/commit debe incluirlos junto a check-local.py y CMakeLists.txt.

Build nuevo correcto, CTest local 2/2 y Python R4 89 aprobados. Evidencia/hashes:
BREEZE_R4_REPRO_RESULTS.json. Sin cambio C++/plugins, sin repetir matriz externa/ASan.
Pendientes integración diaria, backends y aceptación restante de §209; no se avanza a R5/R7.

## 2026-11-14 — inventario de backends de las instancias del panel

La revisión de integración diaria confirma que faltan autoridades/selección/fallback y los
backends de ventanas/escritorios; un frame presentado no permite retirar la barra actual.
Se implementa el contrato de diagnóstico necesario: PanelSession.widgetBackends identifica
las instancias directas por ID y paquete, fallos de carga y evaluación de dependencias.
Catalog.runtimeAssessment comparte esa evaluación con el catálogo y conserva las extensiones
de metadatos de paquetes desconocidos. No es lista de widgets permitidos ni soporte universal.

El estado fresco del runtime incluye el inventario por panel y motivos específicos:
adaptador requerido, runtime sin verificar, carga fallida o inventario vacío/ausente. Todas
las evaluaciones siguen operationalVerified=false hasta tener adaptadores y evidencia real.
No se usa renderReady como comprobación de servicios, ni se marca vacío como éxito. El
alcance explícito es direct-panel-instances: los hijos de bandeja requieren trabajo adicional.

QtTest comprueba metadatos desconocidos con extensión propia, dependencias de APIs revisadas,
dos instancias independientes y retirada inmediata. El ensayo de RuntimeControl verifica
que una respuesta nueva puede tener renderReady=true mientras widgetBackendsVerified=false
y replacementReady=false. Ambos ensayos se ejecutan en CTest local junto con configuración
y lectura nueva; evidencia en BREEZE_R4_BACKEND_INVENTORY_RESULTS.json.

No se ha instalado arranque/selección/recuperación diarios ni activado backend alguno. Falta
su implementación y aceptación, además de la matriz restante. No se cambia el panel activo,
compositor ni plugins; sin R5/R7. Las pruebas actuales son offscreen, no nuevos ensayos de sesión.

## 2026-11-14 — adaptador KWindowSystem experimental hacia el escritorio común

Se implementa la primera conexión funcional de acciones de escritorio: el controlador KDE
ShowDesktop original puede llamar al gestor común BWM por un plugin estático KWindowSystem
dentro del auxiliar. No se modifica su QML/C++, no se emula org.kde.KWin ni se instala un
plugin global/Hyprland. Resto de activación/tokens/export/efectos/sombras delegado a KDE;
CMake fija la ABI privada V5 a KWindowSystem 6.29.0 EXACT y los requisitos se actualizan.

El puente serializa/coalesce peticiones, observa el estado compartido y espera el fin del
gestor antes de notificar. Timeout 5 s y cierre del grupo propio con hijos; JSON, direcciones,
dueño/directorio/alias se comprueban antes de actuar. El gestor común añade enter idempotente
sin alterar toggle/leave existentes. No se crea otro servidor ni vigilante inotify.

El ensayo QtTest carga el módulo compilado Plasma instalado e instancia dos ShowDesktop
originales: sus setters/getters/notificaciones pasan por KWindowSystem, ejecutan el gestor
Python real y un hyprctl de prueba que no puede contactar con el compositor. Se comprueba
minimización/restauración final ficticia, sincronización e idempotencia. El primer fallo de
restauración del fixture era su detector demasiado amplio de «special:minimized» (también
aparecía en un guarda de restore); se corrigió para reconocer la orden de destino real.
También se evita publicar finalización en medio del gestor y se prueba el timeout sin hijos
corriendo. El root del widget original y sus dos acciones cargan offscreen; no tiene una
fullRepresentation separada ni páginas propias de configuración y no se afirma lo contrario.

preview-isolated admite --builtin y --desktop-actions. El segundo sólo funciona con preview
registrado, Breeze, runtime privado e IPC accesible, y fuerza Wayland. Probes/export/KNS
suprimen esos flags. README contiene el comando local; puede minimizar/restaurar ventanas
reales sólo cuando se solicita ese opt-in. El ejecutor sigue sin IPC: no se ha lanzado la
vista ni una acción sobre la sesión del usuario.

Esto usa minimizar/restaurar común BWM: **no es el efecto visual Peek de KWin** (R7), y la
acción secundaria Minimize All basada en TaskManager continúa pendiente. Tampoco acredita
gráficos Wayland del delegado o integración diaria. operationalVerified/replacementReady
siguen false. Evidencia normal/ASan/Python/procedencia: BREEZE_R4_DESKTOP_ADAPTER_RESULTS.json.

Comprobación final de esta continuación: build normal y ASan, CTest 2/2 en cada uno
(incluye tres casos del controlador/estado/timeout más init/cleanup), 117 Python
(R4 89, ventanas 14, minimizar 7, manifiestos 7), sintaxis/diff y AGENTS=CLAUDE correctos.
ASan detect_leaks=0: no certifica fugas ni bibliotecas externas. La matriz externa KNS
anterior no se repite ni se amplía a partir de estos resultados.

## 2026-11-14 — corregido el arranque desde la terminal del usuario

Tras activar Breeze, el usuario no encuentra el binario de /tmp. El error ocurre antes de
crear la vista o ejecutar una acción, por lo que no se deduce ningún resultado de sesión.
Se construye el auxiliar en build/bwm-plasma-host dentro del árbol compartido; ese directorio
concreto se excluye de Git. Runner de reserva y README usan la ruta estable. No se cambia el
panel diario ni se ejecuta una acción real de escritorio desde el asistente.

preview-isolated comprueba archivo/permiso de ejecución antes de skin/IPC y da la orden de
compilación si falta. También captura OSError del exec (por ejemplo intérprete/loader ausente)
sin traceback. CTest local 2/2 en el build estable y dos pruebas nuevas de estos fallos pasan;
no se repite ASan por este cambio de Python/ruta. Evidencia BREEZE_R4_STABLE_BINARY_RESULTS.json.
La validación nativa en Hyprland y las limitaciones de §212 siguen pendientes.

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

## 2026-11-15 — fuente experimental para el TaskManager original

BwmTaskSource implementa AbstractWindowTasksModel de LibTaskManager 6.7.5 EXACT.
BwmTaskBridge descubre WindowTasksModel a través de proxies/concatenaciones Qt dentro
sólo del auxiliar y cambia su fuente con setSourceModel público. No modifica ni copia
libtaskmanager o sus formularios. Mantiene la fuente anterior y la restaura al retirar
el adaptador; una fuente personalizada de un complemento queda intacta. Dos modelos
TasksModel KDE comparten la misma fuente BWM en la regresión.

| Dato/acción | Archivo/API | Efecto implementado | Verificación actual |
|---|---|---|---|
| Ventanas, título, app, actividad, monitor | native-tasks.py → hyprctl clients/activewindow/monitors; BwmTaskSource | Filas nativas con geometría lógica, estados e identidad dirección/PID/inicio de proceso | Helper Python y modelos KDE con IPC ficticio |
| App/icono/launcher URL | TaskManager::windowUrlFromMetadata/appDataFromUrl, KF6 Service | Resolución KDE de metadatos; sin lista fija BWM | Flujo del modelo local; apariencia Wayland pendiente |
| Foco/minimizar/restaurar | requestActivate/requestToggleMinimized → native-tasks.py → kwin-window.py | Gestor BWM común; origen normal/especial y comprobación de identidad | Dos TasksModel nativos, IPC ficticio, cambio de estado y persistencia de índice |
| Maximizar | requestToggleMaximized → kwin-window.py maximize | Entrada al maximizador común, sin duplicarlo | Ruta de helper permitida/rechazo de identidad obsoleta; geometría real nueva pendiente |
| Cerrar | requestClose → kwin-window.py close | Cierre dirigido con guarda PID del gestor común | Fila desaparece e índice persistente se invalida con IPC ficticio |
| Índices e identidad | beginInsertRows/beginRemoveRows/dataChanged por roles | Cambios de título/estado conservan índices; nueva identidad obtiene UUID nuevo | QAbstractItemModelTester y regresión nativa |
| Diagnóstico | PanelRuntime.readiness.taskSource | Fuente habilitada, modelos, ventanas, última respuesta, cola y último error | Aserciones locales; operationalVerified=false |

El helper permite exclusivamente cuatro acciones, revalida Breeze y la identidad capturada
antes de invocar el gestor existente; éste vuelve a comprobar dirección/PID en Lua.
No se admite un comando arbitrario. Las ventanas minimizadas conservan el origen que
registró el gestor común; las especiales ocultas no se presentan como ventanas ordinarias.
Una ventana fijada a todos los escritorios normales lleva el rol nativo correspondiente.
No se inventan IDs de actividades ni se anuncia un proveedor de escritorios virtuales.

Los snapshots no reinician el modelo completo en cada sondeo: identidad estable y sólo
roles modificados. Un proveedor por proceso, sondeo de 750 ms mientras haya modelos
conectados, una acción simultánea y cola de hasta 64, timeout de 8 s y terminación acotada
de sus propios grupos de procesos. Snapshot y acción pueden coexistir. No hay servidor
nuevo. La cola sólo serializa las acciones de este puente: falta coordinar mutaciones con
ShowDesktop y otros llamadores del gestor común, y probar quiescencia al cambiar de skin.
No se afirma atomicidad entre la consulta del helper y la acción del compositor.

--task-actions requiere preview --follow-skin, Breeze, runtime privado e IPC accesible;
configuración/datos del widget y D-Bus permanecen aislados. Sólo el helper recibe las rutas
reales de configuración/runtime necesarias para el gestor común. Probes/export/KNS limpian
los flags. No se habilita automáticamente ni selecciona el panel diario.

Pruebas: CTest 2/2 normal y 2/2 ASan (detect_leaks=0), QtTest de tareas 5/5 contando
init/cleanup, 98 pruebas Python R4 y 7 de manifiestos. La cadena probada es TasksModel KDE
→ proxies nativos → fuente BWM → helper real → gestor común real → hyprctl ficticio.
En offscreen StartupTasksModel carece de backend y columnas; el test le proporciona sólo
una tabla vacía de una columna para no ocultar las otras fuentes concatenadas. Esa medida
no se aplica en producción. Las pruebas usan roles numéricos: no demuestran representación
de delegados QML ni resolución de sus roles en una sesión Wayland.

Evidencia completa: BREEZE_R4_TASK_SOURCE_RESULTS.json. Sin acceso nuevo al compositor,
sin cambio del panel diario, sin reinicio ni plugin de Hyprland. La puerta externa KNS ya
superada sigue respaldada por su informe anterior y no se repite en esta regresión.

Pendientes: proveedor VirtualDesktopInfo/pager y filtros de escritorio, acción secundaria
MinimizeAll, menús con acciones incondicionales que no tienen rol de capacidad, nuevas
instancias/URL-drop, mover/redimensionar/fullscreen y otras acciones, geometría de delegados,
coordinación entre procesos y aceptación Wayland. Los roles de capacidades sin implementar
quedan false donde KDE los ofrece; eso no desactiva por sí solo todos los menús originales.
El widget entero sigue sin certificar. snapshotAvailable indica la última respuesta válida,
pendingActions sólo la cola (no el proceso en curso) y lastError es histórico hasta sustituirse;
no son una certificación de salud o quiescencia. operationalVerified y replacementReady
siguen false. R4 permanece abierta; R5/R7 no se han iniciado.

## 2026-11-15 — transacciones nativas y retirada sin acciones tardías (§216)

Las dos entradas experimentales del auxiliar (tareas y Mostrar escritorio) coordinan sus
mutaciones con native_guard.py y el flag --native-serialized del gestor existente.
No se duplica su lógica: el bloqueo envuelve execute(args) en kwin-window.py. El helper de
tareas pasa --expected-generation además del PID, y la comprobación de inicio de proceso
se repite después de esperar. El gestor relee Breeze dentro de la transacción. El adaptador
de escritorio recibe el XDG_CONFIG_HOME real sólo para su proceso gestor; el widget conserva
sus archivos y D-Bus aislados.

| Control/límite | Archivo/API | Efecto real | Verificación |
|---|---|---|---|
| Tareas + Mostrar escritorio simultáneos | native_guard.action_lock → flock Linux; kwin-window --native-serialized | Exclusión entre ambas entradas nativas para el mismo runtime | Contención real entre procesos y rutas de ambos adaptadores en regresión nativa |
| Cambia skin mientras espera | require_breeze dentro del bloqueo | Rechazo antes de consultar/mutar el cliente | Proceso bloqueado, cambio de config y liberación; sin mutación |
| Cambia identidad mientras espera | --expected-generation + comprobación PID | Rechazo de inicio Linux obsoleto tras adquirir el bloqueo | Proceso bloqueado, generación modificada y liberación; sin mutación |
| Skin/stop del auxiliar | RuntimeControl → PanelRuntime → suspendAll de ambos puentes | Descarta cola, detiene consultas, permite acabar la mutación y confirma después | QtTest con hijos controlados por señales de archivos, sin IPC real |
| Cancelación del cambio | Nueva revisión con skin plasma | Reactiva sondeo/acciones y obtiene datos nuevos | QtTest: vuelta a plasma tras retirada y fuente disponible |
| Diagnóstico | readiness.nativeActionsQuiescing y taskSource | Expone espera, suspensión, procesos en vuelo y quiescencia local | Aserciones durante y después de la mutación |

El runtime del bloqueo debe ser canónico, privado y propio. Se abre por descriptor de
directorio; archivo regular propio 0600, sin enlaces, O_NOFOLLOW y CLOEXEC. Espera acotada
a 1 s, con error si continúa ocupado. No se cambia un permiso ajeno ni se borra el lock:
la exclusión pertenece al inodo y se libera al cerrar/morir el propietario. Una eliminación
para desbloquearlo permitiría dos transacciones independientes. Las pruebas cubren permisos,
symlink/hardlink, contención y muerte del propietario, conservando el mismo inodo.

La retirada no mata una operación de escritura para fingir que ha terminado. Ambos puentes
suspenden entradas y descartan lo aún en cola. Sólo la consulta de lectura se cancela;
RuntimeControl reintenta cada 25 ms sin aumentar revisión ni escribir ack hasta que terminen
sus procesos. No hay bucle Qt anidado ni espera bloqueante nueva de GUI. Si excede los
1,5 s del publicador de sesión, el hook falla y bwm-theme-manager aborta antes de cambiar
los perfiles, enviando después la skin anterior para reanudar. Los timeouts existentes no
se han ampliado. Una terminación forzada o el timeout del proceso no prometen rollback.

La barrera sólo cubre los puentes dentro de este auxiliar. El bloqueo cubre los llamadores
que optan por --native-serialized; las acciones diarias de Quickshell/atajos y otros gestores
aún no participan. Un snapshot sigue siendo varias consultas, no una transacción atómica del
compositor. quiescent significa ausencia de procesos/cola del puente de tareas, no ausencia
de actividad en todo BWM. Tampoco certifica geometría, foco o restauración visual.

VirtualDesktopInfo 6.7.5 se ha revisado en el código upstream: propiedades de sólo lectura,
métodos no virtuales y backend estático privado, sin factoría pública intercambiable.
La técnica de setSourceModel de WindowTasksModel no sirve para él. No se cambia su puntero
privado ni se interponen símbolos de la biblioteca instalada. El siguiente proveedor debe
integrarse mediante un contrato explícito, incluyendo los consumidores C++ de filtro/orden
y los QML de tareas/pager; reemplazar sólo un objeto QML no resolvería esos consumidores.
Esto clasifica una dependencia pendiente, sin excluir paquetes externos del catálogo ni
afirmar que todos los plasmoides sean inviables en Hyprland.

Validación: CTest normal 2/2 y ASan 2/2 (detect_leaks=0), tareas QtTest 7/7 incluyendo
init/cleanup; Python R4 103, ventanas 14, minimizar 7 y manifiestos 7. Evidencia/hashes en
BREEZE_R4_NATIVE_TRANSACTIONS_RESULTS.json. El binario estable está reconstruido. No hay
prueba nueva en sesión, ni ampliación de la puerta KNS previa, ni activación del panel diario.
R4 sigue pendiente por escritorios/menús/acciones, coordinación diaria y aceptación Wayland.

## 2026-11-15 — protocolo nativo de escritorios y consumidores KDE (§218)

Se implementa org_kde_plasma_virtual_desktop_management v4 en
src/bwm-plasma-desktops, separando protocolo, proyección de workspaces y extensión de
Hyprland opcional. Ésta añade un global al display existente: no inicia otro compositor,
socket de sesión, servidor KWin/D-Bus ni plasmashell. No reemplaza objetos QML o punteros
privados de libtaskmanager. El XML KDE privado 1.23.0 se genera con wayland-scanner y queda
fijado por hash; cambiarlo exige revisar el contrato completo.

| Capa | Implementación/efecto | Comprobación | Límite |
|---|---|---|---|
| Protocolo | IDs/nombres/posiciones/filas, activo global y por salida; eventos done y vida de recursos | VirtualDesktopInfo C++ y QML originales contra Wayland aislado; retiro/recreación del mismo ID | Versión 4 probada; no se certifica toda versión anterior |
| Filtro/orden | TaskFilterProxyModel por salida y TasksModel ordenado por escritorio usan el proveedor nativo | Datos BwmTaskSource, dos salidas ficticias, activación actualizada, orden inicial con fuente desordenada | Sin ventanas reales; reordenación automática del orden de tareas no certificada |
| Roles QML | TasksModel original y test Instantiator con required display | Objetos de delegado y título leído por nombre de rol | Es un delegado de prueba; no es Task.qml original ni una barra pintada |
| Proyección BWM | Contador compartido 1–N + workspaces vivos/activos, nombres reales, exclusión de especiales/99 | Test puro: IDs, orden, contador ausente/100, duplicados, desbordamiento, monitor sin foco | No configura ni renumera workspaces; sin nuevo archivo de preferencias |
| Extensión de Hyprland | Lectura State/FocusState, eventos coalescidos + reconciliación 500 ms; acciones Config::Actions | Compila contra headers 0.56.2 y guarda de hash; readelf sin STB_GNU_UNIQUE | No instalada, cargada ni validada en sesión; desactivada por defecto |
| Solicitudes | Activar; petición por salida existente con asignación compatible | Contrato de protocolo comprobado con backend ficticio | Backend real restringe cruces/no materializados; ejecución real pendiente |
| Crear/quitar | Denegación explícita, contadores y capacidades false | Solicitudes nativas no alteran el inventario en fixture | El protocolo no tiene flags para desactivar todos los controles de clientes; pager/menús completos sin certificar |

La extensión lee bar.workspaces.shown del config común; si falta o no es válido, informa
que el contador no está disponible y utiliza sólo los vivos/activos. Conserva escritorios
reales que exceden el contador. No modifica configuración ni carga layouts. output_name es
un nombre efímero del protocolo que coincide con QScreen, sin persistir conectores como
identidad de monitor. Especiales y antiguo 99 nunca se publican como escritorios normales.
Su política respecto a tareas de especiales todavía debe validarse con los filtros reales.

Las activaciones pasan por las acciones estándar de Hyprland, con cola limitada y aplicación
diferida al event loop. request_enter_output sólo admite workspace ya materializado/asignado
a esa salida y enfoca ese monitor antes de activarlo. No traslada ni intercambia workspaces,
no sobrescribe reglas comunes y no usa shell/exec. El fixture admite más movimientos para
probar el contrato v4: ese éxito no acredita tales movimientos en la extensión real.

El binario experimental está en build/bwm-plasma-desktops/bwm-plasma-desktops.so, separado
de breezebars. No se ha desplegado, cargado ni añadido al arranque. El opt-in empieza false.
Se compiló también el núcleo enlazado con -fno-gnu-unique y se comprobó ausencia de símbolos
UNIQUE en el .so. make install existe sólo como despliegue futuro atómico; no se ejecutó.
El funcionamiento en Hyprland, colisión con otro proveedor, coordinación asíncrona con la
barrera del auxiliar, creación/quita y navegación/wrapping siguen pendientes. Nunca esperar
un flock/proceso desde el hilo del compositor: podría bloquear el IPC del propio gestor.

La regresión usa socketpair heredado y WAYLAND_SOCKET de Qt, XDG temporal, D-Bus inexistente
y dos salidas de fixture. No conecta a Wayland/IPC del usuario ni abre un socket de escucha.
Un display mínimo inicializa Qt Wayland pero rechaza superficies; no es un compositor gráfico
ni una prueba visual. Se prueban propiedades C++/QML, activación, filtros, nombres/posiciones,
rechazo de snapshot duplicado, retiro y recreación. No se escribe el esquema del widget para
simular soporte: los consumidores instalados reciben el protocolo de verdad.

CTest 4/4 normal y 4/4 ASan (detect_leaks=0); QtTest nativo de escritorios 3/3 contando
init/cleanup. Regresión R4 Python 103 y manifiestos 7 pasan. Se declaran las dependencias
wayland/plasma-wayland-protocols/wayland-protocols y nlohmann_json para la extensión opcional.
Avisos esperados: D-Bus KWin ausente y protocolo de ventanas Plasma ausente en el fixture;
no se anuncian solucionados por este proveedor de escritorios.

Evidencia y hashes: BREEZE_R4_NATIVE_DESKTOPS_RESULTS.json. Esta prueba mejora el alcance de
§215/216: ahora hay consumidor nativo por Wayland y roles QML comprobados. No amplía las
confirmaciones manuales anteriores a este binario nuevo ni repite la puerta KNS externa.
operationalVerified/replacementReady permanecen false. R4 sigue abierta por aceptación en
Hyprland, coordinación, menú/acciones restantes y autoridades diarias; R5/R7 no se inician.

## 2026-11-15 — barrera de activación por conexión y retirada del host (§219)

Se conecta el proveedor de escritorios a RuntimeControl/PanelRuntime mediante el contrato
propio bwm_plasma_desktop_control_v1. Es un global en el mismo display y wl_client Qt,
no un servidor nuevo ni una sustitución del protocolo KDE. Los widgets conservan sus
VirtualDesktopInfo originales. El control afecta exclusivamente a las activaciones de esa
conexión; los eventos de lectura continúan y otros clientes conservan su estado/autoridad.

DesktopProtocol posee ahora la cola real de activaciones, común a fixture y extensión.
Toda conexión comienza pausada; activar exige propietario de control y resume explícito.
Pausar o destruir ese propietario cancela su trabajo pendiente y deja esa conexión pausada.
Desconectar borra su estado y cola, sin heredar autoridad por reutilización de punteros.
Cada petición captura recurso/serial de vida/ID y se valida antes de aplicar; retirar el
recurso también cancela su trabajo. Límite global de cola 32, ejecución en idle del mismo
event loop. Un pause sólo se confirma tras cancelar lo pendiente y terminar el callback
anterior: no espera un proceso ni toma flock desde el hilo del compositor.

| Caso | Aplicación/API real | Efecto | Verificación aislada |
|---|---|---|---|
| Activación seguida de pausa en el mismo flush | Protocolo KDE + control BWM por wl_client | Se cancela esa petición antes del ack | Cliente C real, inventario/activo sin cambio; cancelación contada |
| Segundo cliente | Dos conexiones Wayland independientes | Su activación sigue funcionando mientras el primero está pausado | Cliente C con dos endpoints privados |
| Sin propietario / propietario destruido | Estado de Peer + destructor del recurso | Sólo lectura; no hay activaciones hasta rebind/resume | Requests reales, rechazo y posterior reanudación |
| Cambio de skin / stop | NativeDesktopControl → PanelRuntime → RuntimeControl | Espera ack del serial vigente y mutaciones locales antes de confirmar revisión | Qt/KDE originales, transición y vuelta a Breeze |
| Proveedor deshabilitado o perdido | availability/activeChanged | Suspende colas locales y retira vistas; bloquea la entrada requerida | QtTest deshabilita/retira/restaura globals del fixture |
| Retirada sin proveedor | Estado ausente sin trabajo remoto propio | Permite retirar el auxiliar/salir de ese modo | QtTest; no se extiende al logout general del escritorio |
| Proveedor sin responder | Timer del cliente, plazo de 1 s | Error sin confirmar revisión; ack tardío ignorado | Sólo el fixture detiene su loop por pipe privado; nueva revisión recupera |

NativeDesktopControl correlaciona serial y estado, con confirmación asíncrona y timeout de
1 s. Un error no se convierte en éxito por una respuesta atrasada. Una revisión nueva puede
reintentar. Ante reaparición del global se exige confirmación nueva antes de reanudar. No se
usa un loop Qt anidado ni una espera bloqueante de GUI. RuntimeControl admite su primera
revisión pendiente sin soltar el propietario del canal, y sigue reintentando sólo mientras
haya espera válida. Los deadlines del publicador/hook no se han ampliado.

Se encontró y corrigió en la prueba un fallo de liberación del proxy al desaparecer el
global: el init(nullptr) generado por Qt instala un listener y no sirve para desinicializar.
Se libera localmente el proxy retirado y se sigue su vida sin volver a destruirlo; un bind
posterior crea el recurso nuevo. La regresión cubre desaparición, restauración y destrucción
bajo ASan. No se modifican miembros privados de Qt ni KDE.

--native-desktops es opt-in de preview --follow-skin. El launcher consulta únicamente el
diagnóstico del proveedor que ya esté cargado/habilitado/disponible y exige protocolo v4 /
barrera v1. Después el cliente comprueba el contrato Wayland real. No carga, habilita ni
instala un plugin. Probes/KNS/export y modos no interactivos limpian la variable; sin el
control una conexión sólo puede leer este proveedor experimental. Un diagnóstico compatible
no certifica que un KCM/widget/efecto completo sea operativo.

CTest 5/5 normal y 5/5 ASan (detect_leaks=0). QtTest Wayland 4/4 contando init/cleanup;
prueba C de dos clientes pasa; Python R4 105 y manifiestos 7, y repetición focal de los
4 tests del launcher tras ajustar su ayuda (incluidos en los 105). Evidencia BREEZE_R4_DESKTOP_CONTROL_RESULTS.json con hashes, logs y límites.
No se ha instalado/cargado la extensión ni cambiado el arranque o panel diario del usuario.

La barrera garantiza retirada de activaciones propias; no serializa todas las operaciones
normales de ventanas/workspaces ni revoca otros clientes. No promete rollback de acciones
ya aplicadas. La aceptación real del frontend, conflictos de proveedor, menús/create/remove,
wrapping/especiales y autoridades diarias siguen pendientes. No se certifica Task.qml pintado,
widget completo ni sustitución diaria; operationalVerified/replacementReady siguen false.
R4 permanece abierta. Sólo R4, sin R5/R7.

## 2026-11-15 — capacidades del menú de tareas original (§220)

TaskMenuPolicy protege las acciones de ventana del ContextMenu.qml instalado, sin copiarlo,
interceptar URLs ni modificar metadatos del sistema. Se integra en BwmTaskBridge y sigue su
suspensión. El filtro de eventos público de Qt sólo reconoce QMenu de QMenuProxy dentro de
una raíz TaskManager registrada, con QModelIndex procedente del proveedor de capacidades
org.bwm.window-actions versión 1. Las fuentes personalizadas ajenas siguen intactas.

Se revisó ContextMenu.qml de plasma-desktop 6.7.5: mantener encima y debajo carecen de rol
que permita deshabilitarlos; excluir de capturas sólo exige visualParent. Los tres handlers
existen en KDE, pero BwmTaskSource no implementa sus peticiones. Quedan deshabilitados con
una máscara QActionGroup no exclusiva por acción. No se sustituye enabled ni su binding
QML, ni se introducen implementaciones KWin ficticias. Los grupos comprueban todos sus hijos.
El icono se lee del QMenuItem propietario, no del QAction de una app: una acción de aplicación
con el mismo icono permanece intacta. No se aplica a menús ajenos.

| Control | Archivo/API | Efecto real | Verificación de esta continuación |
|---|---|---|---|
| Minimizar/restaurar individual | ContextMenu.qml original → TasksModel.requestToggleMinimized → BwmTaskSource | Petición toggle-minimize hacia el puente existente/gestor común | Handler original emite dirección/PID/generación; integración helper/gestor con IPC ficticio cubierta además por test-tasks; sin ventana real nueva |
| Minimizar grupo de dos | Mismo handler y agrupación nativa KDE | Una petición por ventana del grupo | Dos direcciones distintas y dos peticiones toggle-minimize comprobadas |
| Mantener encima/debajo | BwmTaskSource.ActionCapabilitiesRole + TaskMenuPolicy + QActionGroup | Deshabilitados; ninguna petición nueva implementada | Acciones originales deshabilitadas; trigger de encima no emite señal ni petición; checked independientes |
| Ocultar de capturas | Mismo rol/máscara sobre view-private original | Deshabilitado en la fuente nativa; ruta diaria no conectada aquí | Acción deshabilitada en menú individual y agrupado; no prueba física de captura |
| Acciones dinámicas de apps | QAction original, sin cambiar su propietario | Se conservan | Acción con icono coincidente queda habilitada y sin grupo impuesto |
| Retirar vista/cambiar skin | BwmTaskBridge.setSuspended → TaskMenuPolicy | Cierra menús y restaura el estado explícito vigente | Suspensión probada con enabled false/true; integración de retirada existente pasa CTest |
| Retirar/reordenar filas | Señales estructurales públicas del modelo | Cierra el menú antes de usar índices obsoletos | Retirada de filas individual/grupo comprobada; inserción/movimiento/reset/layout conectados, sin ensayo separado de cada señal |
| Menú KDE actualizado/no revisado | resolvedUrl + QFile/qrc + SHA256 del original | Deshabilita menú afectado y registra error | Coincidencia positiva del original probada; discrepancia y QActionGroup ajeno no inyectados en este ensayo |

Qt no recalcula enabled al llamar únicamente a removeAction. La retirada reactiva primero
la máscara individual y después la separa; así respeta el último estado explícito sin
reactivar otras acciones. Los grupos son no exclusivos para conservar checked independientes.
QPointer protege la vida de acciones/menús y una guardia evita recursión entre submenús.
El objeto se desvincula antes de restaurar acciones que pueden emitir señales.

El contrato privado se fija al SHA256 de ContextMenu.qml
ceefbecbc0daf6d4e9968a075b3e8c55a59815b79c89f7add6d7b88dc4cc4f81.
Una fuente distinta o no disponible bloquea ese menú y deja lastError, sin presumir compatibilidad.
La comprobación funciona también con el original compilado en recursos qrc. No se añade
ninguna dependencia: QtWidgets y LibTaskManager ya estaban declarados.

Validación: binario estable reconstruido; CTest 5/5 normal y 5/5 con AddressSanitizer
(detect_leaks=0, halt_on_error=1). El test nuevo es un caso QtTest con 3 pases contando
init/cleanup, integrado en isolated-local-configuration. Python R4 105 y manifiestos 7 pasan.
BREEZE_R4_TASK_MENU_RESULTS.json conserva hashes, referencias y salidas completas.

**Límite del ensayo:** carga org.kde.plasma.icontasks y abre su menú mediante la función
original de Task.qml con QApplication/QMenu reales en offscreen. El backend privado nativo de
WindowTasksModel está ausente en esa plataforma y roleNames() produce avisos undefined en
Task.qml; StartupTasksModel recibe sólo en test una tabla vacía de una columna. Los accesos
numéricos del menú al modelo y sus handlers sí se prueban. No es evidencia de un Task.qml
correctamente pintado, geometría/foco de menús, teclado/puntero Wayland ni barra completa.
La prueba previa Wayland de roles usa un delegado de ensayo diferente, no este Task.qml.

No se añadieron fullscreen, shade, no-border, asignación de escritorios ni nueva instancia
al adaptador. El original 6.7.5 consulta CanSetNoBoder (errata frente a CanSetNoBorder):
no se corrige copiando su menú ni se anuncia esa opción operativa. Restantes capacidades,
frontend/proveedor en Hyprland, conflictos/arranque y autoridad/fallback del panel diario siguen
pendientes. Sin nueva prueba de sesión, carga de plugins, cambio de panel activo ni R5/R7.

## 2026-11-15 — pantalla completa del menú nativo, con aplicación comprobada (§221)

Se conecta la acción original «Pantalla completa» de TaskManager con el gestor BWM existente.
BwmTaskSource implementa requestToggleFullScreen y publica el rol IsFullScreenable según la
capacidad fullscreenable del snapshot. Es un campo interno opcional booleano: si falta no
habilita la acción; un tipo incorrecto rechaza el snapshot atómicamente. Se notifica el cambio
del rol sin invalidar la identidad de la fila. No se copia ni modifica ContextMenu.qml.

El helper obtiene la capacidad de native_fullscreen_allowed del gestor: ventana normal,
mapeada, no oculta por Hyprland, no fijada, no minimizada ni en Magic/otro especial/antiguo 99.
No significa que esté actualmente en el monitor visible: puede pertenecer a otro escritorio
normal. La comprobación de minimizado ya calculada se reutiliza al producir snapshots, sin
cargar otra copia del gestor por cada fila. Las ventanas fijadas no se habilitan: Hyprland
condiciona su fullscreen a binds:allow_pin_fullscreen y no se inventa otra preferencia.

| Control/etapa | Archivo/API | Efecto real implementado | Verificación |
|---|---|---|---|
| Capacidad «Pantalla completa» | native-tasks.record → native_fullscreen_allowed → IsFullScreenable | Habilita sólo el alcance descrito; fuera de él no se envía petición | Python: normales/minimizadas/especiales/fijadas; C++: flag ausente/falso/inválido y notificación de cambio |
| Entrada/salida individual | ContextMenu.qml original → TasksModel.requestToggleFullScreen → BwmTaskSource | Envía estado booleano deseado true/false, identidad y generación | Handler original, checked tras reabrir y ambas direcciones probados |
| Acción agrupada | Handler/grupo originales KDE | Una petición de estado deseado por miembro | Dos peticiones true desde el menú de grupo comprobadas |
| Aplicación nativa | native-tasks → kwin-window --native-serialized fullscreen --state on/off | Bloqueo compartido, revalidación de skin/PID/inicio/capacidad, set/unset de Hyprland | Dos TasksModel originales ejercitan helper y gestor reales con IPC ficticio; secuencia on/on/off releída desde el modelo |
| Guarda en compositor | native_fullscreen_lua → hl.dispatch(hl.dsp.window.fullscreen) | Revalida skin/PID/mapped/hidden/pinned/workspace en el event loop antes del setter | Lua generado ejecutado: guards, rechazo del dispatcher y éxito sin cambio de modo se rechazan |
| Confirmación | result.ok + lectura w.fullscreen → hyprctl repl | Recibo exacto sólo si el modo interno leído coincide con el solicitado | Exit=0 sin recibo, error, modo no cambiado, salida adicional y timeout fallan; idempotencia set/set/unset comprobada |
| Entrada diaria existente | kwin-window fullscreen sin --state | Conserva su alternancia anterior | Prueba de compatibilidad de llamada y Lua guardado por PID |

La conversión a estado deseado sigue la semántica del consumidor KDE: dos solicitudes del
mismo snapshot no alternan dos veces. En el gestor nativo se exige --state on|off y PID/inicio;
no se admite toggle implícito. La exclusión y la barrera de retirada siguen siendo las de
§216; no se añade otro proceso duradero ni autoridad de preferencias.

Se revisaron las fuentes locales exactas de Hyprland 0.56.2: repl devuelve los valores de
Lua evaluados; hl.dispatch devuelve una tabla ok, y w.fullscreen expone el modo interno del
controlador. El script exige ambas cosas y su recibo bwm-r4-fullscreen-ok. No confunde
returncode=0 con aplicación, ni una tabla ok con un cambio de estado efectivo. Tiempo máximo
de esa consulta: 2 s. No añade esperas/hilos dentro del compositor. La comprobación interna
es síncrona; el frame físico y la geometría de restauración se aceptan por otra prueba.

Pruebas finales: CTest 5/5 normal y 5/5 AddressSanitizer (detect_leaks=0, halt_on_error=1).
QtTest TaskTest 8/8 y MenuTest 3/3, ambos contando init/cleanup. Python R4 113, gestor de
ventanas 14, minimizar 7 y manifiestos 7, sin omisiones. El fixture IPC ejecuta el Lua generado
contra un hl simulado con estado; no contacta ningún compositor. CMake resuelve explícitamente
lua5.4/lua sólo para BUILD_TESTING; el intérprete no es dependencia nueva de producción.
La nueva evidencia está en BREEZE_R4_FULLSCREEN_RESULTS.json; los informes previos conservan
sus hashes históricos. Binario estable reconstruido en build/bwm-plasma-host.

**Límites y siguiente aceptación:** hyprctl version sigue devolviendo Couldn't open a socket
(1) en este ejecutor. No hay nueva prueba física de entrada/salida de fullscreen, restauración
de geometría/maximizado, foco, reglas, monitores/escalas o cambios de skin con esa ventana.
Los avisos offscreen de roles de Task.qml y el fixture StartupTasksModel de §220 permanecen:
los tests no certifican el pintado de la barra ni el menú Wayland completo. Las tres acciones
sin backend siguen bloqueadas; no se añaden no-border, shade, asignación de escritorio ni
nueva instancia. La extensión de escritorios no se instala/carga y el panel diario sigue activo.
R4 abierta; operationalVerified/replacementReady false y sin R5/R7. Para retirar esta capacidad,
no emitir fullscreenable en el snapshot (ausente=false); no modificar paquetes KDE del sistema.

## 2026-11-15 — metadatos vivos de las tareas, sin reiniciar el auxiliar (§222)

Se reproduce un fallo de caché independiente del compositor: al actualizar una entrada de
aplicación .desktop, KSycoca notificaba el cambio, pero BwmTaskSource seguía devolviendo el
nombre anterior. La prueba falla antes del arreglo con First metadata frente a Updated
metadata. El identificador/PID de la ventana no cambian y no se entrega otro snapshot para
actualizar esa ficha: debe reaccionar a la base KDE, como el modelo original.

La fuente escucha KSycoca::databaseChanged mediante su API pública, compartiendo el singleton
KDE existente. Un QTimer singleShot de 100 ms agrupa notificaciones; invalida la caché AppData
y notifica sus roles. La resolución es diferida: sólo cuando un consumidor lee un rol de
aplicación vuelve a usar windowUrlFromMetadata/appDataFromUrl. Así no se resuelven de golpe
miles de filas ni se añade un vigilante por ventana. Un modelo vacío no emite rangos inválidos.

| Evento/dato | Archivo/API | Efecto | Verificación |
|---|---|---|---|
| Actualizar .desktop con la ventana abierta | KSycoca::databaseChanged → BwmTaskSource | Invalida datos de aplicación y emite AppId/AppName/GenericName/LauncherUrl/LauncherUrlWithoutIcon/DecorationRole | Reconstrucción real con kbuildsycoca6 y señal de archivo real; dos fuentes reciben el nombre actualizado |
| Cambiar el icono declarado | TaskTools + QIcon del paquete | Nueva imagen al leer DecorationRole | PNG rojo→azul comprobado por píxel del QIcon, sin capturas ni assets ajenos |
| Retirar/reinstalar aplicación | Mismos resolutores nativos | Elimina metadatos viejos, usa fallback KDE y descubre reinstalación | GenericName se vacía, LauncherUrl coincide con resolución fresca nativa y reaparece el nombre nuevo |
| Identidad de ventana | Row serial/UUID/QPersistentModelIndex | Conserva ventana, título e índices mientras cambia sólo AppData | UUID/título estables, cero modelReset; no nuevo snapshot para actualizar metadatos |
| Cerrar/vaciar una fuente durante aviso | Conexiones QObject/QTimer propias | Sin callbacks a fuente destruida ni rangos inválidos | Fuente temporal destruida y segunda fuente vaciada/reabierta, normal y ASan |

La prueba crea una entrada de aplicación con ID propio, Exec=/usr/bin/false e iconos PNG
propios. No ejecuta ese Exec. Lee los formatos estándar/KService reales, sin lista fija ni
señales databaseChanged simuladas. El runner conserva todas las escrituras en XDG temporal,
elimina KDESYCOCA heredado y el binario exige ese entorno antes de crear archivos. La base
se reconstruye en el cache privado. Los archivos de aplicaciones del sistema sólo se leen.

kbuildsycoca6 se busca explícitamente en CMake sólo para BUILD_TESTING; el runtime usa KF6
Service, que ya estaba declarado/enlazado. No se añaden programas de producción, preferencias,
servidores o cambios de sesión. El wrapper guarda salida y éxito del nuevo test en el informe.

Validación final: CTest 5/5 normal y 5/5 AddressSanitizer (detect_leaks=0, halt_on_error=1);
QtTest de metadatos 3/3 contando init/cleanup, integrado en la regresión local existente.
Python R4 113 y manifiestos 7 pasan. Evidencia BREEZE_R4_TASK_METADATA_RESULTS.json, incluido
el fallo previo. El binario estable y los tests se reconstruyeron desde las fuentes actuales.

El disparador es la notificación de la base KSycoca. El test la reconstruye explícitamente;
no acredita detección automática de cualquier instalador que sólo escriba un .desktop sin
actualizar esa base. El preview mantiene su cache aislado; esta corrección no añade un
monitor de instalaciones ni cambia la autoridad del cache diario.

Alcance: metadatos de aplicaciones .desktop del modelo experimental; no se certifica con esto
el catálogo de plasmoides, todas las actualizaciones de temas de iconos, ejecución de apps,
pintado de Task.qml o entrada/menús Wayland. No hay una nueva prueba visual en Hyprland. Las
capacidades pendientes, frontend de escritorios y autoridad/fallback del panel diario siguen
abiertos. operationalVerified/replacementReady siguen false; sólo R4, sin R5/R7 ni plugins
instalados/cargados o cambios del panel diario. Para revertir sólo este comportamiento,
retirar la conexión/invalidador de AppData; no borrar metadatos KDE del sistema.

## 2026-11-15 — registro único y asociación del proveedor de escritorios (§223)

Se cierra otro bloqueo previo a activar vistas nativas: existencia del control no bastaba
para saber qué proveedor de escritorios usaría Qt. NativeDesktopRegistry obtiene un registro
en la conexión Qt existente mediante QNativeInterface::QWaylandApplication/Wayland público.
Un sync asíncrono termina el inventario inicial; escucha altas/bajas posteriores. No abre
otra conexión ni socket, no altera filtros del compositor ni enumera estructuras privadas.
Sólo cuenta los dos protocolos pertinentes, con límite de 64 globals y fallo conservador.

El protocolo propio conserva el nombre bwm_plasma_desktop_control_v1 y pasa a versión 2.
Su evento desktop_global identifica el global KDE de ese proveedor para ese wl_client;
wl_global_get_name devuelve 0 si no es visible. El auxiliar exige exactamente un management
KDE >=4 y un control >=2, y verifica su asociación antes de pedir resume. Los eventos v1 y
la barrera siguen compatibles para clientes v1; el launcher del auxiliar rechaza proveedores
anteriores a v2 antes de abrirlo. No se anuncia por ello compatibilidad de widgets completos.

| Caso | Implementación | Resultado comprobado |
|---|---|---|
| Registro inicial/identidad | NativeDesktopRegistry + control v2 | Inventario completo, versiones y asociación válidas antes de resume |
| Dos controles | Enlace explícito al ID elegido | Deshabilita entrada, permite pausa/salida y recupera el control original con confirmación nueva al quitar el duplicado |
| Control disponible sin global asociado | Evento desktop_global=0 de proveedor de ensayo | Rechazado aunque availability y el inventario de versiones sean correctos |
| Registro/respuesta retenida | Deadline 1 s en el cliente | Inventario tardío no reanuda; revisión nueva permite otro handshake |
| Dos management KDE | Bloqueo por proceso del auxiliar | No reanuda al quitar el duplicado ni al crear otro controlador en ese proceso; salir sigue permitido |
| Recuperación de KDE original | VirtualDesktopInfo instalado, otro proceso Qt | El viejo queda con 0 escritorios; el proceso nuevo descubre los 4 publicados y confirma pausa/resume |
| Retirar servidor con peticiones en vuelo | Controles conservados inertes | Dos clientes v1 envían pausa/destroy tras global_remove sin invalid_object ni ack/trabajo del proveedor retirado |
| Pérdida breve de confirmación | PanelRuntime oculta antes de reconciliar | Prueba Qt offscreen restaura la misma vista si vuelve la confirmación antes del desmontaje; no altera una ocultación manual |

La prueba con duplicados detectó una trampa de Qt 6.11.2: QWaylandClientExtension desactiva
una extensión al retirarse cualquier global de su interfaz, sin comparar el ID enlazado.
El control usa ahora el binding generado directamente, con propiedad explícita del recurso.
Para los consumidores KDE originales no se intercambian punteros privados: la ambigüedad
KDE queda marcada durante ese proceso y exige reiniciar sólo el auxiliar. El ensayo real del
SDK confirma que su lista puede perderse. No se reinicia ni sustituye el compositor.

PanelRuntime suspende entradas locales y oculta inmediatamente paneles/popups propios al
perder confirmación; la destrucción continúa en reconcile diferido. Una marca transitoria de
vista evita dejarla oculta si el control vuelve antes de ese reconcile. Se comprueba la rama
con una vista Qt offscreen; la retirada de superficies/input reales por conflicto sigue sin
aceptación Wayland. Las ventanas arbitrarias de paquetes no se certifican por este mecanismo.

El núcleo retira los globals, cancela colas y deja los recursos de control retirados sin
owner hasta que el cliente los destruye o se desconecta. Peticiones de esos recursos se
ignoran, sin ack. Así una pausa o destroy que ya viajaba no mata la conexión. Esto no cambia
la semántica/lifetime de todos los recursos KDE ni permite hot unload del módulo.

Pruebas finales: CTest 5/5 normal y 5/5 AddressSanitizer, detect_leaks=0/halt_on_error=1;
Qt Wayland 7/7 contando init/cleanup, C++ de dos clientes v1 y un proceso Qt fresco sobre el
segundo socketpair de ensayo. Fixture sólo de datos: no puede representar superficies.
Python R4 113 y skins 7 pasan. Los tests exigen fixture privado antes de inicializar Qt;
KDESYCOCA se limpia también en ese runner. BREEZE_R4_REGISTRY_RESULTS.json guarda resultados,
fuentes exactas y hashes. Compilación ASan en build/bwm-plasma-host-asan; binario normal estable.

La extensión opcional se recompila contra los headers instalados y tiene cero símbolos GNU
UNIQUE (núcleo y módulo conservan -fno-gnu-unique). No se instala/carga ni cambia el arranque.
El mínimo Wayland server es 1.22; el cliente Wayland se enlaza explícitamente. Son paquetes
ya declarados; módulos/notas del inventario y docs/REQUIREMENTS.md se actualizan. No ejecutar
make install ni hot load/unload como parte de esta prueba.

**Pendiente:** esta guarda sólo verifica los globals visibles en la conexión actual y la
asociación declarada por el proveedor; no autentica ni certifica un backend arbitrario.
Tampoco impide que un servidor/módulo anuncie duplicados: el arbitraje previo del frontend
sigue pendiente antes de desplegarlo. Overflow/versiones antiguas y todas las políticas de
filtros no se inyectaron en Wayland; la prueba Python rechaza versiones antiguas del diagnóstico.
Siguen pendientes frontend/arbitraje/arranque, capacidades restantes, aceptación gráfica y
autoridad/fallback del panel diario. operationalVerified/replacementReady false. Sólo R4.

## Continuación R4 §225 — arbitraje del proveedor en el servidor (2026-11-15)

Se corrigen dos fallos del frontend experimental: anunciaba globals KDE/control aun con
`enabled=false` y podía terminar con disponibilidad activa después de fallar `publish`.
`DesktopProvider`, compartido entre extensión y fixture, ahora inventaría el display antes
de publicar. No añade otro servidor ni conecta al compositor de sesión desde el test.

| Caso | Vía y efecto real | Verificación |
| --- | --- | --- |
| Desactivado inicialmente | Sólo observador por socketpair en el mismo display; ningún global propio | Inventario de cliente independiente vacío |
| Proveedor previo | Registro asíncrono completo antes del claim; bloquea publicación propia | Sin duplicar el management; publica sólo después de su retirada |
| Dos BWM simultáneos | Claim propio versionado, menor ID visible y segundo sync antes de publicar | Un único par KDE/control durante la elección |
| Publicación | Snapshot validado, globals inicialmente no disponibles y tercer sync | Asociación v2 verificada por control y consumidores originales KDE C++/QML |
| Conflicto posterior | Al observarlo cancela cola, avisa disponibilidad falsa y retira globals propios | Queda sólo el proveedor ajeno; no reaparece automáticamente |
| Estado inválido | No publica vacío ni restaura disponibilidad después del rechazo | Generación retirada; auxiliares admiten salida/pausa |
| Solicitudes en vuelo | `wl_global_remove`, core/globals/recursos de una generación retenidos; controles inertes | Binds ofrecidos y get/activate/pause posteriores conservan conexión sin activar ni confirmar |
| Fallo de observador | Límite 128, plazo 1 s, error de E/S o pérdida de peer cierran la vía | Timeout, overflow y desconexión; filtros existentes conservados |

El observador usa APIs públicas Wayland client/server sobre socketpair privado; no crea
socket de escucha, hilo, proceso, bucle anidado, roundtrip bloqueante ni cambia el filtro
global del compositor. Maneja flush no bloqueante y escucha escritura sólo ante EAGAIN.
El diagnóstico añade serverArbitrationVersion=1, arbitrationState/arbitrationReason,
providerRestartRequired, arbitrationScope=observer-visible-globals y singlePublicationGeneration.
El launcher exige versión/estado activo y ausencia explícita de reinicio pendiente; no
instala, carga ni habilita el módulo. Se conservan la barrera por conexión y el XML KDE.

**Límites:** sólo observa globals visibles para su peer bajo el filtro del compositor. No
impide que un módulo ajeno anuncie duplicados: un conflicto posterior puede verse brevemente
antes de retirar los nuestros. Los claims son cooperación, no autenticación. El auxiliar
conserva además sus guardas por conexión de §223; una duplicación KDE sigue exigiendo auxiliar
nuevo. No hay prueba de todas las políticas de filtrado ni del frontend en sesión Hyprland.

Tras crear un claim se admite una sola generación por vida del módulo: desactivar, perder
la elección, fallar o detectar conflicto requiere un futuro inicio de sesión para publicar
de nuevo. No hacer hot unload/reload para recuperarlo. Es una restricción explícita del
experimento: se retienen recursos KDE y ofertas hasta el teardown, con límites existentes
del core, evitando generaciones/reintentos sin límite o destruir objetos aún utilizados.
No hay control KCM de activación diaria conectado a esta opción experimental.

Se corrigió también pérdida del peer después de la retirada: el descriptor deja de
vigilarse aunque la publicación ya sea terminal, evitando atender HUP repetidamente.

Pruebas: 14 escenarios C++ aislados, incluido cancelar el segundo trabajo desde el callback
del primero y 20 ciclos de display sin crecimiento de descriptores. El consumidor original
KDE C++/QML pasa activación, cambios y retirada por snapshot inválido. CTest normal y ASan
7/7; Python R4 113 y manifiestos de skins 7. ASan con detect_leaks=0/halt_on_error=1: no es
certificación de ausencia de fugas de memoria. Evidencia exacta, fuentes y hashes en
BREEZE_R4_PROVIDER_ARBITRATION_RESULTS.json. Extensión recompilada, cero símbolos GNU UNIQUE,
sin instalar/cargar/autoiniciar ni tocar el panel diario. Binario estable del auxiliar conservado.

**R4 sigue pendiente:** aceptación del frontend/arranque en Hyprland, ciclo seguro de futuras
generaciones, capacidades restantes, interfaz gráfica/entrada real y autoridad/fallback del
panel diario. operationalVerified/replacementReady continúan false. Sin R5/R7 ni takeover.

## Continuación R4 §226 — arranque diferido y cierre definitivo del módulo (2026-11-15)

La revisión de las fuentes Hyprland 0.56.2 detectó dos problemas del frontend antes de
cargarlo en una sesión: el reloj de inventario empezaba en el constructor aunque el loop
aún no atendiera eventos, y el cierre del módulo conservaba controles con callbacks a su
biblioteca después de que Hyprland pudiera descargarla.

### Arranque

DesktopProvider empieza disabled sin peer, socketpair ni plazo de inventario. Requiere
snapshot válido y petición explícita; espera un idle del loop existente para crear el
observador y empezar el plazo de 1 s. Deshabilitar antes del idle lo cancela y todavía
permite volver a solicitarlo porque no hay claim/generación. Un arranque detenido más de
1 s antes del primer dispatch ya no consume ese plazo. El diagnóstico informa
observerStartup=deferred-event-loop. El frontend aborta su inicialización si no consigue
registrar el comando de diagnóstico, antes de pedir publicar el proveedor.

Se revisaron filterGlobals, CProtocolManager::isGlobalPrivileged y SecurityContext. El
peer directo de este observador no figura en la lista de clientes sandbox y el filtro de
esa versión lo permite. Las conexiones creadas por security-context conservan la política
del compositor: nuestros globals no forman parte de su whitelist de protocolos permitidos.
No se cambia ese filtro ni se habilitan protocolos para clientes sandbox. Es una revisión
de fuentes; no una medición de visibilidad o seguridad en la sesión del usuario.

### Retirada frente a cierre

| Operación | Vida de los recursos | Prueba |
| --- | --- | --- |
| withdraw durante el uso | Globals retirados; core, ofertas y recursos conservados; controles ignoran pause/resume por withdrawn | Peticiones y binds en vuelo conservan conexión, sin acciones ni ack |
| Destrucción definitiva del core | Destruye también todos los controles registrados, activos/retirados/enlazados tarde | Ningún recurso con callbacks/interfaces del core queda al descargar |
| Destrucción definitiva del proveedor | Retira fuentes de eventos y peer; destruye core y recursos del claim | Cero recursos propios antes de dlclose |
| Cierre de Hyprland 0.56.2 | unloadAllPlugins precede a wl_display_destroy_clients | Fixture usa ese orden y verifica que el DSO se descargó realmente |

Los controles siguen asociados al core retenido para poder seguir su vida; withdrawn es la
guarda de inactividad. El registro de controles incluye los que Peer::control ya no referencia
y los binds posteriores a la retirada (límite total 4096). El claim también registra sus
recursos (límite 256): incluso un marcador sin peticiones contiene una referencia a metadatos
del módulo que debe desaparecer antes de descargarlo. No dejar punteros a funciones/interfaz
del .so después del destructor. Esto corrige y sustituye la estrategia antigua de conservar
controles con userdata=null tras destruir el core (§223).

El fixture anterior confundía retirada con destrucción: ahora retira y conserva los cores
de ensayo hasta terminar los clientes; los libera antes de destruir el display. El módulo
experimental conserva la única generación de §225 mientras vive, sin habilitar reintentos.

La nueva biblioteca desktop-provider-teardown-module es SÓLO de prueba: enlaza el mismo core
y proveedor con símbolos internos ocultos para impedir interposición con el ejecutable.
El test abre el DSO, enlaza management/desktop/control/claim, añade un control desde una
oferta retirada, destruye el proveedor, comprueba cero recursos propios, hace dlclose,
verifica RTLD_NOLOAD negativo y después destruye los clientes. Casos activo y retirado.
No procesa peticiones después del cierre definitivo: no autoriza hot unload en una sesión.
No carga el plugin Hyprland real ni otro compositor.

Pruebas: 16 escenarios del proveedor, incluyendo arranque lento/cancelación del idle y
teardown con DSO realmente descargado; CTest 7/7 normal y 7/7 ASan con detect_leaks=0 y
halt_on_error=1; Python R4 113. También se conserva la prueba original KDE C++/QML del
proveedor arbitrado. Extensión y bibliotecas de ensayo recompiladas y con cero GNU UNIQUE.
Fuentes exactas, hashes y salidas en BREEZE_R4_STARTUP_TEARDOWN_RESULTS.json. Sin instalación,
carga/autostart, reinicio del compositor, modificación de sesión ni activación del panel.

**Pendiente de R4:** frontend y arranque reales en Hyprland, recuperación de futuras
generaciones, capacidades/entrada/render restantes y autoridad/fallback diarios. El frontend
aún lee config.json en su reconciliación de 500 ms para el contador común; revisar esa E/S
antes de integración diaria. No se ha certificado un logout real ni el comportamiento de
otros plugins. operationalVerified/replacementReady/r4Complete siguen false. Sólo R4.

El preflight de --native-desktops exige providerLifecycleVersion=1 (entero, no booleano)
y observerStartup=deferred-event-loop, además de las guardas anteriores. Diagnósticos de
un módulo antiguo se rechazan antes de lanzar el auxiliar; sin instalar/cargar/habilitar.

## Continuación R4 §227 — contador compartido sin E/S en el frontend (2026-11-15)

Se elimina count() del plugin: ya no abre config.json, consulta su tamaño ni analiza JSON
en cada reconciliación de 500 ms o activación. La única fuente sigue siendo
bar.workspaces.shown y las opciones de texto del usuario. CountMirror es una copia en
memoria del último valor válido, no otra preferencia ni un archivo de KDE/BWM.

| Dato/operación | Archivo/API y efecto | Verificación |
| --- | --- | --- |
| Contador común efectivo | effective_options() del puente: config común + overrides existentes | Test del puente real con contador12, override9, reentrada en Breeze y archivos conservados |
| Transporte | hyprctl bwm-plasma-desktops-count N → CountMirror; entero canónico 1–100, recibo v1 con valor/revisión | Emisor Python real contra parser/recibo C++ real en transporte de ensayo |
| Aplicación | Cache aceptada programa reconciliación sólo si cambia; workspaceSnapshot consume esa copia | Consumidor original KDE cambia 3→7 y conserva escritorios vivos/activos al reducir a2 |
| Duplicados e inválidos | Repetir mismo valor no aumenta revisión; rechazar no cambia el último valor | C++ acepta/rechaza comandos y comprueba continuidad de valor/revisión |
| Escritura parcial | Lectura fallida en el puente no envía cero ni vacía escritorios | Python conserva último envío válido y recupera el valor final12 |
| Sin dato inicial | No publica el proveedor antes de contar con copia válida | Guarda explícita del frontend y preflight que exige countMirrorVersion=1/configuredCountAvailable |
| Actualización | Mismo watch del puente, debounce existente y comprobación de reintento cada2s | Sin daemon, thread, watcher o temporizador adicional; límites/reintento probados |

El puente importa native_workspaces.py. reconcile envía el snapshot después de sus cambios;
el mismo coordinador se comparte con watch y vuelve a intentarlo ante la carga posterior
del módulo. No añade reload ni escritura de preferencias. La lectura y los procesos IPC
ocurren en el auxiliar existente, no en el hilo del compositor. Sólo consulta IPC si existe
el módulo opcional en la ruta de instalación estándar; su presencia no lo carga/habilita.
Los errores se registran, no bloquean los otros ajustes ni convierten exit=0 en éxito.

El valor ausente en las opciones efectivas usa10, el default real del modelo común; valores
presentes con tipo/rango inválido se rechazan. La exportación KDE sigue usando su autoridad
común existente y conservando claves desconocidas. El nuevo adaptador respeta los overrides
sin escribir bwm/user. Cambios en otras skins se reflejan al reentrar y reconciliar Breeze;
no se hace propia de Breeze la preferencia compartida.

El comando no habilita el proveedor ni crea workspaces. Conserva los escritorios vivos y
activos fuera del rango configurado; especiales y antiguo99 continúan excluidos. Para la
primera publicación, enabled sin dato queda awaiting-shared-workspace-count. Un valor ya
válido se retiene ante errores transitorios. configuredCountAvailable confirma una copia
conocida, no certifica frescura instantánea de archivos/funcionamiento completo de Plasma.
El recibo reconoce cache aceptada; el cambio del modelo ocurre en reconciliación coalescida.

El launcher sigue haciendo sólo lectura. Exige countMirrorVersion=1 y contador confirmado,
además de barrera/asociación/arbitraje/ciclo de vida anteriores. No instala, carga, habilita
ni envía ajustes desde el preflight. Módulo sin adaptador/contador se rechaza antes del preview.

Pruebas: CTest7/7 normal y ASan (detect_leaks=0/halt_on_error=1); Python R4 122 y puente KDE20,
incluida nueva prueba de autoridad/reentrada/no-reload. Consumidor KDE C++ original verifica
los cambios en fixture normal y arbitrado; el consumidor QML y resto de regresión se mantienen.
check-count-mirror.py usa el emisor real y el mismo parser/recibo C++ con transporte privado,
no hyprctl ni socket real. La extensión está recompilada con cero GNU UNIQUE. Evidencia,
fuentes y salidas en BREEZE_R4_COUNT_MIRROR_RESULTS.json.

No se ha reiniciado el puente ya ejecutándose: adoptará el adaptador al reiniciarse/iniciar
sesión. No se ha instalado/cargado el plugin ni alterado la sesión/panel. Sigue pendiente
aceptación en Hyprland del frontend, orden de arranque y entrega efectiva del contador,
futuras generaciones y capacidades/render/entrada/autoridad/fallback diarios. La lectura
periódica del JSON en el frontend, pendiente en §226, queda resuelta por esta vía. R4 abierta;
operationalVerified/replacementReady/r4Complete false. Sin R5/R7 ni takeover.

Los envíos del contador se serializan con el bloqueo existente del puente. El tick usa
LOCK_NB y reintenta en0,25s ante contención; reconcile reutiliza su guardia ya adquirida.
Se evita reordenar escritores cooperantes o bloquear/entrar recursivamente en watch.

Límite entre skins: el watch KDE termina fuera de Breeze. El contador configurado del
proveedor puede conservar la última copia hasta reentrar, aunque su feed de workspaces
vivos continúe. Resolver esa entrega común entre skins antes de certificar integración
diaria; esta prueba acredita reentrada, no actualización continua de esa copia en Retro/default.

## Continuación R4 §228 — entrega común entre skins (2026-11-15)

Se resuelve en código el límite de §227: el contador configurado ya no depende de que el
watch KDE siga vivo en Breeze. SharedSettingsRuntime vive una vez en shell.qml, fuera de
los loaders de paneles/skins. Las ventanas de Ajustes no lo instancian y no se añade otro
demonio, thread o FileView/inotify. El watch KDE vuelve a ocuparse de sus reglas/área/KDE;
se retira de él el sondeo periódico del contador, conservando el envío durante reconcile.

| Paso | API/efecto | Verificación |
| --- | --- | --- |
| Disparo común | Config.ready, contador o skin cambian: debounce200ms en el shell principal | QML real sin compositor espera ready y agrupa ráfagas |
| Un proceso a la vez | Process asíncrono; cambio durante entrega deja pendiente una siguiente | Registro de procesos prueba start/end sin solapamiento |
| Descubrimiento | bwm_settings_hooks.py shared consulta hooks.sharedSettings de adaptadores incluidos | Validación de ruta/intervalo y rechazo de registro desde skins descargadas |
| Armado | requiresConfigFile relativo a XDG_CONFIG_HOME; falta archivo → inactivo/retry0 | Configuración real comprobada: .so ausente, sin ejecutar adaptador/IPC |
| Lectura efectiva | Auxiliar resuelve config + all + overrides de la skin actual | Default/Retro/Breeze con prioridad del texto, sin modificar archivos del usuario |
| Aplicación | native_workspaces.py shared envía contador por IPC al CountMirror existente | Cadena QML→dispatcher→adaptador→recibo C++ real en transporte de ensayo, valores3/7/5 |
| Continuidad | Mientras armado, retryMs del adaptador; contador2s, incluso sin nuevo cambio | Prueba de retry y carga tardía del auxiliar |
| Error | Recibo inválido/timeout no es aplicación; FailedToStart no deja busy permanente | Pruebas QML y Python; diagnóstico estructurado mantiene motivo acotado |

El hook de Breeze declara script, requiresConfigFile e intervalMs en su manifiesto. El
lector genérico no contiene condiciones de Plasma/Retro/default. Sólo las skins incluidas
registran estos adaptadores revisados; instalar un tema, plasmoide o skin descargada no
concede ejecución de fondo. Ruta del script dentro de su skin; prerequisito relativo sin
escape; intervalo1000–30000ms, timeout3s y recibo JSONv1 con applied booleano. La presencia
del .so sólo arma entrega: nunca lo instala, carga, habilita o declara operativo.

La entrega usa el contexto común actual, sin importar kde-config-bridge ni ejecutar su
enter/import/watch desde otras skins. effective_options() común respeta también overrides
específicos de la skin activa; la preferencia compartida y los archivos de texto conservan
su autoridad. El bloqueo existente del puente se comparte mediante bridge_lock; el auxiliar
usa LOCK_NB y reconcile aprovecha la guardia ya adquirida. No se hace trabajo de archivos,
proceso o bloqueo en el compositor, ni se recarga Hyprland por entregar el contador.

El coordinador usa un Timer Qt para debounce/reintento dentro del shell ya existente. Sin
adaptadores armados, retryMs=0 detiene el sondeo hasta otro disparo/inicio. Instalar el módulo
por primera vez durante una sesión sin suscripción exige nuevo disparo o inicio; no permite
cargarlo en caliente. El código mantiene el modelo conocido si hay un fallo; disponibilidad
de copia sigue sin certificar frescura instantánea ni funcionamiento del panel completo.

Diagnóstico nuevo de sólo lectura: qs -c ii ipc call sharedSettings status. Expone ready,
busy, número de entregas, skin y último informe de adaptadores. Quickshell0.3.2 llama
streamEnded antes de exited; FailedToStart sólo emite runningChanged. Esa diferencia se
maneja y se prueba con el binario instalado, sin quedarse esperando un exited inexistente.

Pruebas: 12 específicas, con cinco escenarios reales de Quickshell offscreen y cadena
completa de procesos sobre configuración/IPC de ensayo; dispatcher/adaptador reales, parser
y recibo C++ del núcleo. Default/Retro/Breeze envían3/7/5; otra prueba verifica all9/Retro11
sin tocar el texto del usuario, desconocidas ni kwinrc. Sin backend KDE completo fuera de
Breeze. Regresión R4 134, puente20, skins7; CTest7/7 normal y ASan (detect_leaks=0/halt_on_error=1).
No cambia código C++ ni instala/recompila el módulo en esta continuación. Evidencia en
BREEZE_R4_SHARED_DELIVERY_RESULTS.json.

**Sesión real:** el archivo shell.qml se ha integrado en el árbol enlazado a la configuración.
Puede recargarse automáticamente; no se ha forzado un reinicio ni se ha verificado su carga.
El log existente se pudo leer sin error de tipo SharedSettingsRuntime observado; eso no
prueba que el componente nuevo haya cargado. hyprctl -j version falla con Couldn't open a
socket (1) y la consulta IPC del shell con QLocalSocket::UnsupportedSocketOperationError.
No se cuenta como validación de sesión ni se han cambiado permisos/contextos para evitarlo.
El módulo opcional sigue sin instalar/cargar y el panel nativo no se activa.

R4 sigue abierta por frontend/arranque/entrega reales en Hyprland, futuras generaciones,
capacidades/entrada/render restantes y autoridad/fallback diarios. La infraestructura de
entrega entre skins queda implementada/probada aislada; falta medirla en sesión. Sin R5/R7.
operationalVerified/replacementReady/r4Complete false. No se afirma ausencia de cambios de
sesión: modificar QML vivo puede causar recarga aunque no se haya reiniciado por herramientas.

## Continuación R4 §229 — cobertura de dibujo del delegado original preparada (2026-11-16)

Los avisos de roles de §220 se explican por el entorno offscreen: WindowTasksModel.roleNames()
consulta su backend nativo privado y TasksModel.roleNames() consulta ese WindowTasksModel
estático. Cambiar sourceModel o concatenar otro proxy no demuestra que el QML reciba roles
Wayland. No se modifica KDE ni se sustituye ese estado privado.

Se añade test-taskdelegate y la prueba CTest native-task-delegate-render. Usa el mismo fixture
Wayland privado que rechaza superficies, los modelos KDE originales, el puente BWM real con
snapshots propios y los widgets instalados org.kde.plasma.icontasks/org.kde.plasma.taskmanager.
Prepara comprobaciones de roles/propiedades, activo→minimizado→restaurado, título, continuidad
del índice/delegado y retirada. QQuickRenderControl dibuja a QImage sin mostrar/crear ventana;
los avisos de binding de Task.qml/main.qml hacen fallar la prueba. No hay transporte de acciones
a Hyprland, compositor alternativo, IPC de sesión ni sustitutos de StartupTasksModel/roles.

**Cobertura preparada, pendiente de ejecución.** El fixture falla antes de iniciar Qt:
wl_client_create devuelve Operation not permitted (EPERM). La suite native-desktop-protocol
anterior falla igual. Ahora perror y el runner conservan el código/stderr del handshake.
No se intenta sortear la restricción. memoryRenderingVerified y renderingVerified siguen
false; el segundo campo se reserva para aceptación de superficies/sesión, distinta de memoria.

Compilación normal/ASan del test aprobada. Tres suites que no necesitan crear esos clientes
(proyección, geometría, configuración local) pasan3/3 en ambos builds; ASan detect_leaks=0/
halt_on_error=1. py_compile del runner aprobado. No es CTest8/8 ni aceptación de renderizado.
Fuentes, hashes, salidas y límites en BREEZE_R4_TASK_DELEGATE_RESULTS.json.

Ejecutar desde un terminal local para desbloquear esta cobertura (no abre ventanas ni toca
la sesión, instala o carga plugins):

```bash
ctest --test-dir /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host -R '^native-task-delegate-render$' --output-on-failure
```

No cambia código de producción ni configuración viva. R4 sigue abierta: cadena Wayland/
render de este test, entrada real, frontend/arranque/entrega y autoridades/fallback diarios.
operationalVerified/replacementReady/r4Complete false; sin R5/R7 ni takeover.


## Continuación R4 §230 — socket heredado consumido durante el arranque (2026-11-16)

El primer ensayo local del usuario ya inicia el fixture (exit0) y QtWayland. Falla una guarda
incorrecta del test que esperaba WAYLAND_SOCKET después de construir QApplication; no llega
a probar widgets ni dibujo. wl_display_connect de libwayland1.26.0 hace unsetenv al consumir
ese descriptor. No interpretar la variable ausente como falta de conexión.

Corregido con el hook QTest initMain previo a QApplication: captura fstat del socket heredado.
initTestCase consulta el wl_display activo de QNativeInterface::QWaylandApplication y compara
el dispositivo/inodo de su fd con la captura; permite duplicación del fd sin restablecer el
entorno, crear conexión nueva o relajar las guardas de aislamiento. No cambia producción.
La biblioteca instalada confirma consumo/identidad en reproducción con socketpair sin servidor.
Compilación normal/ASan aprobada. Aquí el ensayo completo sigue bloqueado antes de Qt por
wl_client_create EPERM; falta repetir el mismo comando CTest local. Informe anterior del
usuario preservado en userLocalAttempt, seguimiento en followUp230 de
BREEZE_R4_TASK_DELEGATE_RESULTS.json. Sin render aprobado ni aceptación diaria.


## Continuación R4 §231 — origen del QML sin suponer baseUrl (2026-11-16)

El siguiente ensayo del usuario pasa initTestCase, snapshots, roles nativos y creación de
fila/delegado. Se detiene en otra guarda incorrecta de la prueba: QQmlContext.baseUrl es una
base de resolución, no la ubicación del objeto. No se alcanzó el dibujo de Task.qml; los
avisos de servicios ausentes corresponden al fixture privado, sin D-Bus de sesión.

tests/task-qml-source.h resuelve Task.qml por QQmlContext.resolvedUrl y valida el recurso
contra el SHA256 original Plasma6.7.5 ya revisado. Se conserva la selección del delegado por
interfaz dentro del widget KDE instalado; la resolución por sí sola no prueba su tipo.
El fallo muestra baseUrl/resolvedUrl/hash. La misma guarda se ejecuta en test-taskmenu con
el delegado original: regresión local de configuración pasa normal y ASan. Ambos tests
recompilados en ambos builds; sin nuevas dependencias o APIs privadas.

Comprobación adicional Qt software: la misma secuencia QQuickRenderControl/QImage dibuja
rojo, actualiza a azul y mantiene ventana oculta sin handle nativo. Es un smoke de la API,
NO render aprobado de Task.qml ni aceptación Wayland. Propiedades/estados y semántica del
render software revisados en fuentes originales Plasma6.7.5/Qt6.11.2.

Informe del usuario conservado como userLocalAttemptAfter230 y resultados nuevos como
followUp231 en BREEZE_R4_TASK_DELEGATE_RESULTS.json. Pendiente repetir el mismo CTest nativo
corregido desde terminal. Sin código de producción, panel/plugin/reinicio ni cierre de R4.


## Continuación R4 §232 — metadatos independientes de aplicaciones instaladas (2026-11-16)

El siguiente ensayo del usuario ya supera conexión, origen QML y PID. Falla la expectativa
de AppId Konsole: TaskTools no resuelve ese servicio en el entorno aislado y usa el PID real
del ejecutable de prueba. Es un defecto de los datos del ensayo; no se modifica el resolver
KDE/BWM para hacerlo pasar. Informe conservado como userLocalAttemptAfter231.

La nueva preparación compartida tests/task-app-fixture.h instala únicamente en XDG temporal
una entrada .desktop y PNG propios, con ID ligado al PID del test, nombre fijo y Exec falso
que nunca se ejecuta. Reconstruye la caché privada con kbuildsycoca6 (ya requerido para tests)
y espera que KService reconozca el servicio. Rechaza raíces/configuración de caché ajenas.
El runner declara su raíz privada; el cliente nativo verifica primero los roles de modelo
(ID del servicio con .desktop, nombre) y luego el ID sin sufijo/nombre del Task.qml original.
No se sustituyen roles ni se altera la normalización de KDE.

La misma preparación y snapshot con PID real se comprueban en test-taskmetadata: ID/nombre/
icono rojo pasan. El caso anterior espera ahora su servicio inicial si KSycoca ya estaba
abierto por otra prueba; sus actualizaciones posteriores mantienen la comprobación de señal
nativa y fila/UUID estables. Ambas pruebas4/4 contando init/cleanup, regresión local completa
aprobada normal/ASan (detect_leaks=0/halt_on_error=1) y ambos ejecutables recompilados.
py_compile del runner aprobado. Evidencia followUp232 en BREEZE_R4_TASK_DELEGATE_RESULTS.json.

El CTest Wayland completo corregido y el dibujo original siguen pendientes de repetir en
terminal; no se dan por aprobados a partir de metadatos offscreen. Sin código de producción,
configuración de sesión, plugins/panel/reinicio ni cierre de R4. El comando local no cambia.


## Continuación R4 §233 — ensayo completo aprobado desde terminal (2026-11-16)

El usuario ejecutó el CTest corregido:1/1 aprobado en0,83s. El informe leído del workspace
confirma clientExit0, fixtureExit0, cleanupVerified=true y memoryRenderingVerified=true;
QtTest4/4 contando init/cleanup, sin fallos/omitidos, icons-only y text-and-icons aprobados.
La evidencia íntegra y hashes actuales están en currentValidation de
BREEZE_R4_TASK_DELEGATE_RESULTS.json. Este resultado supera los pendientes de §§229–232.

| Comprobado | Alcance |
| --- | --- |
| Modelo/delegado | Conexión privada QtWayland, roles/snapshots BWM y ambos widgets originales KDE |
| Identidad/procedencia | Socket heredado, recurso QML por hash, PID e ID/nombre propios |
| Actualizaciones | Activo→minimizado→restaurado, título, índice/delegado estables y retirada |
| Dibujo | Píxeles en QImage y cambio al minimizar, con QQuickRenderControl |
| Aislamiento/cierre | Ventana oculta sin handle nativo, fixture terminado y limpieza correcta |

Es dibujo EN MEMORIA sobre una conexión Wayland privada, sin ventana ni superficie visible.
renderingVerified permanece false para aceptación de superficies/sesión. Los avisos de
servicios, PlasmaWindowManagement, sombras y toolbox permanecen: sus backends no quedan
certificados por este pase. Sin compositor alternativo, IPC de sesión ni sustitutos de roles.

Pase nativo normal aportado por usuario; compilaciones/regresión local normal/ASan de §232
siguen comprobadas, pero no hay pase nativo ASan ni CTest8/8 completo. No se repiten ahora
ensayos aprobados ni se cambia producción, plugins, panel diario o sesión. R4 sigue abierta
por frontend/arranque/entrega reales, superficies/entrada, capacidades y autoridad/fallback
diarios. operationalVerified/replacementReady/r4Complete false; sin R5/R7 ni takeover.


## Continuación R4 §234 — grupos sin historial de activación (2026-11-16)

Se reproduce un fallo funcional del adaptador: el TaskTools.js original intenta usar
StackingOrder como fallback si ningún hijo tiene LastActivated. El modelo BWM no lo
entregaba y KDE acababa pasando undefined a requestActivate(QModelIndex), sin acción.
El test conserva el fallo previo0 acciones/TypeError y la corrección con el script instalado
sin copiarlo/parchearlo; su SHA256 se fija al original6.7.5.

native-tasks.snapshot entrega stackingOrder según la posición en clients. En las fuentes
Hyprland0.56.2, clientsRequest recorre WindowState.windows y las operaciones de subir/bajar
mueven las ventanas al final/principio. El orden es inferior→superior. No se confunde con
focusHistoryID/MRU ni se añaden consultas IPC. Se conserva el rango relativo al filtrar.
Revisar esta semántica al actualizar Hyprland; no se mide aquí oclusión/orden visual en sesión.

BwmTaskSource acepta stackingOrder opcional, entero0..INT_MAX, y lo expone como StackingOrder.
Cambios emiten el rol sin resetear/reordenar filas ni UUID. En snapshots v1 sin campo usa el
orden de presentación del snapshot: compatibilidad, no prueba de apilado físico. Invalidar
el campo rechaza todo el snapshot conservando el anterior. No cambia formatos de KDE.

| Prueba | Resultado |
| --- | --- |
| Grupo original sin MRU | Elige ventana rank9 frente a3 |
| Apilado actualizado | Elige la que subió a12, con índice persistente |
| MRU observado | Sigue la prioridad original LastActivated aunque el rank sea menor |
| Productor | Conserva orden inferior→superior tras filtrar; ignora focusHistoryID |
| Legado/inválidos | Orden del snapshot si falta campo; valores inválidos no mutan el modelo |

El test importa Native.TaskTools del módulo instalado cargado por Plasma::PluginLoader y
usa el TasksModel agrupado auténtico. El startup vacío de offscreen sólo facilita la prueba
numérica habitual; no prueba Task.qml pintado ni entrada física. Catálogo actualizado para
no seguir anunciando barrera1/ausencia de fullscreen o de adaptadores ya implementados;
conserva las limitaciones de sesión y operationalVerified=false.

Diez tests Python del helper pasan. TaskTest10/10 contando init/cleanup y CTest seleccionado
3/3 normal y3/3 ASan (detect_leaks=0/halt_on_error=1); builds completos y binario estable
recompilados. py_compile aprobado. Evidencia/salidas/hashes en BREEZE_R4_GROUP_ORDER_RESULTS.json.
Sin plugins instalados/cargados, reinicios, prueba nueva de sesión ni R5/R7. No se ha repetido
el render nativo después de este cambio; el resultado §233 conserva sus hashes/alcance.
Persisten frontend/arranque/entrega reales, superficies/entrada, capacidades y autoridad/
fallback diarios antes de sustituir panel. R4/operationalVerified/replacementReady false.


Próximo ensayo acotado: tareas nativas en la sesión, con el preview existente. No requiere
el proveedor de escritorios ni --native-desktops para las acciones básicas de ventana.
La vista temporal aloja dos instancias del gestor con texto; --native-policy se omite, por
lo que no pide reserva nueva. Con una ventana de prueba, comprobar minimizar/restaurar y
activar desde ambas instancias; Ctrl+C termina el auxiliar y retira su registro. No cerrar
apps desde el test automático ni sustituir el panel diario. La ejecución aún está pendiente.

```bash
python3 /mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/preview-isolated.py \
  --binary /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host/bwm-plasma-host \
  --builtin org.kde.plasma.taskmanager --native-panel --layer-panel \
  --follow-skin --task-actions \
  --output "Micro-Star Int'l Co. Ltd. MAG 274Q X24 0x01010101"
```

Preflight de este ejecutor: hyprctl -j version falla Couldn't set socket timeout (2).
No se eleva ni se elude; la aceptación necesita el terminal local. Config del repo indica
plasma, pero esa lectura no certifica el estado vivo del compositor. No se ha abierto el preview.


## Continuación R4 §235 — fuente de tareas ausente en la ruta del panel real (2026-11-16)

**Fallo comunicado por el usuario:** el preview se registra y muestra iconos, pero al pulsarlos
abre nuevas instancias en vez de activar aplicaciones abiertas. Su aspecto también se señala
incorrecto, sin captura/medición que permita atribuirlo a un tema. No es una aceptación de
entrada o tareas. Ctrl+C vuelve al terminal; no se midió la limpieza del registro en sesión.
Los avisos de D-Bus corresponden al aislamiento del ensayo; no se crea otra sesión de bus.

La regresión nueva usa PanelSession.bindPanelItem, como el anfitrión real, sin adjuntar el
applet manualmente al puente. Reproduce boundModels0: el containment no es el propietario
QObject de los AppletQuickItems que coloca en su árbol visual. QObject.findChildren no
alcanza sus modelos. El test de dibujo §233 no cubría esto porque adjuntaba el applet.

BwmTaskBridge recorre ambas relaciones (QObject.children y QQuickItem.childItems), deduplica
objetos y después sigue las fuentes/proxies como antes. No fuerza construcción de QML,
reparenta objetos ni reemplaza fuentes personalizadas. La prueba entra por el registro real,
configura un lanzador propio conocido y recibe una ventana desde el helper real/IPC ficticio:
quedan fusionados en una fila IsWindow/HasLauncher, IsLauncher=false; activar tramita focus.
Esto prueba la integración que antes fallaba, sin ejecutar programas de usuario ni conectar
al compositor real.

--task-actions ahora espera una respuesta status fresca con modelo conectado/snapshot válido
antes de anunciar la prueba preparada (plazo5s, cada orden limitada1,5s). Imprime conteos y
aborta si falta la fuente. No exporta títulos, IDs de apps ni la lista de ventanas. Un snapshot
con cero ventanas es válido; no es un certificado de todas las apps, aspectos, salud continua,
control de escritorios o sustitución del panel diario. Las demás previews conservan su ciclo.

Pruebas: test-paneltasks3/3 contando init/cleanup, incluida fusión/HasLauncher/focus; siete
Python del wrapper y check, py_compile; CTest seleccionado3/3 normal/ASan con
ASAN_OPTIONS=detect_leaks=0:halt_on_error=1. El fixture offscreen avisa de roles ausentes,
como §220: no es pintado de Task.qml ni input físico nuevo. Executables normal y ASan
recompilados. Evidencia con fallo previo, fuentes/salidas y observación manual en
BREEZE_R4_PANEL_TASK_REGISTRATION_RESULTS.json.

Pendiente repetir el MISMO comando de preview de §234. Debe imprimir
«Tareas R4 conectadas: N ventanas, M modelos» antes del mensaje de registro. Verificar
minimizar/restaurar/activar ventanas existentes desde ambas instancias y revisar los iconos.
Sin nuevo ensayo real aquí, sin desplegar plugins, reiniciar Quickshell o alterar el panel
existente. operationalVerified/replacementReady/r4Complete siguen false; sólo R4.

## Continuación R4 §236 — filtro nativo y almacén en otro monitor (2026-11-16)

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

Este comando sustituye al de §§234–235 para este preview sin proveedor nativo. Primero
cargar la regla común (no se ha ejecutado el reload desde este asistente):

```sh
hyprctl reload
python3 /mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/preview-isolated.py \
  --binary /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host/bwm-plasma-host \
  --builtin org.kde.plasma.taskmanager --native-panel --layer-panel \
  --follow-skin --task-actions --all-desktops \
  --output "Micro-Star Int'l Co. Ltd. MAG 274Q X24 0x01010101"
```

Pendiente medir en sesión clic sobre abierta, minimizar/restaurar sin otra instancia,
monitor de animación, aspecto y limpieza. operationalVerified/replacementReady/r4Complete
siguen false. Sin plugin desplegado/cargado, reinicio de Quickshell, nuevas dependencias,
configuración personal modificada, commits/push ni R5/R7.

§237 (2026-11-16): el usuario responde «ahora si» tras el ensayo de §236. Aceptación
funcional general del preview solicitado (activar/recuperar), comunicada por el usuario;
no medición directa ni desglose de apps/casos. No confirma individualmente animación,
iconos, limpieza o ejecución de reload. El fallo funcional de §§235–236 queda superado
para este preview con --all-desktops. Proveedor nativo/filtros e integración diaria de R4
siguen pendientes; operationalVerified/replacementReady/r4Complete false. Sin nuevo código
ni repetición de pruebas. Evidencia userFollowUp237 en BREEZE_R4_DESKTOP_FILTER_RESULTS.json.

## Continuación R4 §238 — apariencia nativa del preview (2026-11-16)

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

Comando actualizado para comprobar aspecto tras la aceptación funcional de §237:

```sh
python3 /mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/preview-isolated.py \
  --binary /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host/bwm-plasma-host \
  --builtin org.kde.plasma.taskmanager --native-panel --layer-panel \
  --follow-skin --task-actions --all-desktops --session-appearance \
  --output "Micro-Star Int'l Co. Ltd. MAG 274Q X24 0x01010101"
```

No se ha arrancado este nuevo ensayo en la sesión del usuario. La prueba verifica motores
nativos en offscreen, no aspecto físico, cobertura de todas las apps/temas ni aceptación
diaria. Pendientes proveedor nativo de escritorios/filtros, capacidades y autoridades/fallback
del panel diario. operationalVerified/replacementReady/r4Complete siguen false. Sin plugin
instalado/cargado, reinicio de shell, escritura en config personal, commit/push ni R5/R7.

## Continuación R4 §239 — aceptación de aspecto y captura de miniaturas preparada (2026-11-16)

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

Primero, desde terminal (el servidor sólo crea datos/píxeles propios en memoria):

```sh
ctest --test-dir /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host \
  -R '^native-task-thumbnail$' --output-on-failure
```

Después del pase, probar el auxiliar anterior añadiendo --task-thumbnails:

```sh
python3 /mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/preview-isolated.py \
  --binary /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host/bwm-plasma-host \
  --builtin org.kde.plasma.taskmanager --native-panel --layer-panel \
  --follow-skin --task-actions --all-desktops --session-appearance --task-thumbnails \
  --output "Micro-Star Int'l Co. Ltd. MAG 274Q X24 0x01010101"
```

Se espera «Miniaturas R4: protocolos de captura por ventana conectados; primeros fotogramas
pendientes del hover». No es confirmación de píxeles: mantener cursor sobre tarea no minimizada
para probar miniatura/actualización, cerrar tooltip y verificar acciones que ya funcionaban.
No se ha ejecutado este ensayo real desde el asistente. Avisos de sombra/D-Bus/WindowManagement
del entorno aislado siguen fuera de esta aceptación. No instalar kpipewire como supuesto arreglo
del protocolo. Rollback: omitir --task-thumbnails conserva la ruta anterior. Panel diario intacto;
operationalVerified/replacementReady/r4Complete false. Sin commit/push ni R5/R7.

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

## Continuación R4 §240 — cierre de la miniatura y señales de la base (2026-11-16)

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

Siguiente paso: repetir sólo el ensayo nativo corregido, antes del cambio de compositor:

```sh
ctest --test-dir /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host \
  -R '^native-task-thumbnail$' --output-on-failure
```

El fallo anterior ocurrió en el cliente de prueba y se reproduce sin capturar imágenes;
no modifica la guarda del incidente de Hyprland. No se infiere que los hitos nativos previos
al crash pasaran todos: los nuevos checkpoints permitirán separarlos de la limpieza.

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

### 249. R4: aceptación de nueva instancia/archivos y traspaso a Claude (2026-11-17)

Usuario confirma clic central → ventana nueva Firefox, combinación posterior de pestaña y
minimizar correcto; después de instrucciones de arrastrar imagen al icono auxiliar responde
«se abre». Ambas rutas de §248 aceptadas manualmente, sin inferir telemetría/foco/matriz.
Actualizado BREEZE_R4_HANDOFF_CLAUDE.md con prioridad sobre pendientes históricos y próximo
frente: lanzadores sin ventanas/acciones .desktop específicas y su entorno de lanzamiento.
Informes de aceptación actualizados; no nuevas pruebas/build, cambios de sesión, commit o
push. Auxiliar dejado abierto por usuario, estado actual no comprobado. R4 sigue abierta,
panel diario intacto. Pérdida temporal del ejecutor no demuestra un fallo del ordenador.

## Continuación R4 §250 — lanzadores anclados y Actions del .desktop (2026-11-17)

Antes de actuar: el auxiliar abierto en §249 ya no se ejecutaba (sin proceso, `status`
inactivo); Breeze activo; en esta ejecución hay IPC con Hyprland.

Problema (fuentes 6.7.5): LauncherTasksModel (runApp/requestOpenUrls) y las QAction de
Backend::jumpListActions/placesActions/recentDocumentActions inician
KIO::ApplicationLauncherJob dentro del auxiliar; KProcessRunner hereda XDG temporal y D-Bus
privado (DBusActivatable al bus privado). ApplicationLauncherJob no admite otro entorno.

Implementación:
- `launchrouter.{h,cpp}`: `BwmLaunchRouter` (QIdentityProxyModel + AbstractTasksProxyModelIface
  exportada) insertado por el puente entre TaskFilterProxyModel y ConcatenateTasksProxyModel.
  Peticiones sobre filas de LauncherTasksModel → `{action:launcher,launcherUrl,urls}`; resto
  sin cambios. No se sustituye LauncherTasksModel (TasksModel usa `mapFromSource` de su
  concatenación para el orden manual; comprobado mover/syncLaunchers).
- `taskmenupolicy.cpp`: identifica las QAction que el Backend original cuelga del
  ContextMenu.qml revisado y las compara con las Actions visibles del .desktop (misma
  resolución/filtro que jumpListActions; texto sin mnemónicos de KAcceleratorManager, elisión).
  Coincidentes → `{action:service-action,launcherUrl,serviceAction}`; handler KDE intacto.
  Lugares/Recientes (datos del host temporal) → enmascarados. Sin coincidencia exacta → todo
  enmascarado con error explicado.
- Host desechable: kdeglobals inmutable en XDG_CONFIG_DIRS con KIOSK
  `run_desktop_files=false`, `shell_access=false` (`native_launch.write_host_policy`). KIO deniega
  antes de crear procesos. El arranque del preview exige `inProcessLaunchDenied=true`.
- Helper: `native-tasks.py` acepta `launcher`/`service-action` sin identidad de ventana, con
  Breeze revalidado bajo el bloqueo; `--launch-task-application` resuelve como runApp
  (applications:, preferred:, .desktop local) sin respaldo OpenUrlJob/ejecutable, o la Action por
  nombre; ApplicationLauncherJob(KService|KServiceAction) con entorno original.

Pruebas locales (este ejecutor):
- CTest 13/13 normal y 13/13 ASan (`detect_leaks=0:halt_on_error=1`), incluidos los fixtures
  Wayland nativos (native-task-thumbnail/delegate-render también ASan).
- `isolated-task-application-launch`: lanzadores applications:/file:/preferred://terminal
  configurado, dos Actions (incluida una tras separador declarado), entorno original
  restaurado, rechazos (NoDisplay, desconocida, nombre inválido, URLs en Action, https:, campo
  pid, servicio inexistente, preferred sin terminal) y KIOSK del host denegando una petición
  válida sin crear proceso.
- PanelTaskTest 4/4 por PanelSession real: ventanas siguen por BwmTaskSource a través del
  router; tres peticiones de lanzador y ninguna por soltar vacío; menú original con
  «Compose & send», NoDisplay oculta, Lugares enmascarados; sin lanzamiento interno; orden
  manual preservado.
- Python R4 155 (+3 nuevas), skins/puente 27.

Sesión (ejecutado por el asistente, sin clics ni apps lanzadas): auxiliar real con
--task-actions/--all-desktops/--session-appearance en MSI: 1 ruta, 4 filas de lanzador,
10 ventanas, KIOSK activo, sin error. Parada con `panel-session.py stop`: sin proceso,
registro ni capas residuales; skin sigue en plasma.

Pendiente: aceptación manual (clic en lanzador anclado, Action del menú, soltar sobre
lanzador), foco/activación de apps nuevas, Lugares/Recientes, notifyAccessed de KActivities,
proveedor de escritorios, autoridades/fallback del panel diario. operationalVerified,
replacementReady y r4Complete siguen false. Evidencia `BREEZE_R4_PINNED_LAUNCH_RESULTS.json`.

### Aceptación manual §251 (2026-11-17)

Usuario confirma en sesión: lanzador anclado sin ventana abre la app; «New Window» de Firefox
desde el menú original; archivo de Descargas soltado sobre Firefox anclado se abre en Firefox;
Lugares aparece en el menú de Archivos. Auxiliar: 3 peticiones de lanzamiento, sin errores;
parada limpia. Ventana nueva a la derecha = separateLaunchers=true de org.kde.plasma.taskmanager
(KDE original). Foco/activación de la app nueva no medidos.

## Continuación R4 §252 — acciones de ventana restantes y Lugares (2026-11-17)

Mover/Redimensionar (breezebars-interactive con respuesta «ok»), Ocultar de capturas y Sin
borde (estado deseado + recibo Lua + relectura) desde el ContextMenu.qml original a través de
BwmTaskSource y del gestor común. Encima/Debajo siguen enmascarados (sin backend en Hyprland).
«Sin borde» queda deshabilitado por la errata `CanSetNoBoder` del QML de KDE 6.7.5, igual que en
Plasma. Lugares: copia de solo lectura de user-places.xbel en el host; cada QAction de Lugar se
casa con KFilePlacesModel y se envía como `launcher` (.desktop + URL). Recientes enmascarados.

Pruebas: CTest 13/13 normal y ASan; TaskTest 11/11, MenuTest 3/3, PanelTaskTest 4/4; Python R4
163; en sesión, etiquetas no-capture/no-border con recibo/relectura, `no_screen_share`
true→false y rechazos por PID/generación sobre una kitty desechable. Pendiente: clics manuales
(mover/redimensionar, capturas en wayland, Lugares propios). Evidencia
`BREEZE_R4_WINDOW_ACTIONS_RESULTS.json`.

### Aceptación manual §253 (2026-11-17)

Usuario confirma «todo revisado, funciona»: mover, redimensionar, ocultar de capturas,
encima/debajo y sin borde deshabilitados, y sus Lugares en el menú de Archivos. Sin desglose
medido por caso. Auxiliar: 16 acciones enrutadas, ninguna enmascarada, sin errores.

## Continuación R4 §254 — proveedor de escritorios en Hyprland real anidado (2026-11-17)

Corregida la guarda de versión de PLUGIN_INIT (comparaba punteros const char*; el módulo nunca
cargaba). Nuevo `check-desktops-hyprland.py` + `test-desktops-hyprland`: Hyprland 0.56.2 anidado y
desechable, módulo cargado sólo allí. Pasan con cliente normal y ASan: activación KDE→Hyprland y
Hyprland→KDE, filtro de escritorio actual con instantánea real, contador 4→6→4, barrera pausa/
reanudación, crear/quitar rechazados; limpieza completa, módulo nunca en el compositor de la sesión.
Pendiente: carga al iniciar sesión real, preview completo con --native-desktops, varias salidas.
Evidencia `BREEZE_R4_NESTED_PROVIDER_RESULTS.json`.

## Continuación R4 §255 — carga opt-in al iniciar sesión (2026-11-17)

`native-desktops.py` (enable/disable/status/startup) y bloque de `autostart.sh`: carga única al
iniciar Hyprland con comprobación de versión, habilitación verificada, marca de sesión, contador
inicial y guarda contra bucles de fallo. Contador común sin sondeo tras aplicar y sin IPC mientras
el módulo no está cargado. Ruta de inicio probada en Hyprland anidado (`--via-startup`) y 7 pruebas
unitarias. Instalado con make install; opt-in activado; pendiente el primer inicio de sesión real.
Evidencia `BREEZE_R4_PROVIDER_STARTUP_RESULTS.json`.

## Continuación R4 §256 — primer inicio real del proveedor (2026-11-17)

Salida del terminal del usuario: módulo instalado/cargado en esta sesión y compilado para
el Hyprland en ejecución; guarda vacía, proveedor habilitado/disponible, arbitraje activo,
sin petición de reinicio ni errores. Contador 10 desde shared-bwm-bridge, escritorio actual 1.
Registro de arranque leído por el asistente: loaded/stable true. Contadores de activación
cero: operationalVerified/liveSessionVerified siguen false. Falta probar el consumidor KDE
en la sesión, varias salidas y cierre; el panel diario sigue activo.

Siguiente prueba (desde terminal del usuario; el IPC está bloqueado para el ejecutor):

```sh
python3 /mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/preview-isolated.py \
  --binary /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host/bwm-plasma-host \
  --builtin org.kde.plasma.taskmanager --native-panel --layer-panel \
  --follow-skin --task-actions --native-desktops --session-appearance --task-thumbnails \
  --output "Micro-Star Int'l Co. Ltd. MAG 274Q X24 0x01010101"
```

Se omite --all-desktops para comprobar el filtro nativo. Cambiar entre dos workspaces del
MSI con ventanas distintas y comprobar que cada uno muestra sus tareas (los lanzadores
anclados pueden permanecer). Desde otro terminal, consultar estado fresco con
`python3 ~/.config/hypr/skins/plasma/scripts/panel-session.py status` y
`hyprctl -j bwm-plasma-desktops`. Ctrl+C en el terminal del preview cierra sólo el auxiliar.
Ensayo preparado, todavía no ejecutado/aceptado.

## Continuación R4 §257–258 — filtro aceptado y diagnóstico por salida (2026-11-17)

El usuario ejecuta el preview de §256 y confirma «correcto, funciona» para el filtro de
tareas del workspace actual en MSI. No se extiende esa aceptación a activación KDE,
mediciones por caso o el panel diario. Auxiliar no cerrado por el asistente.

Nuevo diagnóstico, compatible con dejar el preview abierto:

```sh
python3 /mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/check-desktops-session.py
```

El wrapper compara la proyección de IDs (contador común + workspaces vivos/activos) y todas
las salidas con VirtualDesktopInfo original en el anfitrión. Asociación de proveedor y
topología verificadas; conexión sin resume, serial 0 y ninguna ventana. Resuelve salidas
por descripción única usando BwmOutput; escritorio por nombre y geometría deben coincidir
con Hyprland y con el área lógica de monitor_box. Las lecturas antes/después deben coincidir;
cambio de salida/workspace, espejo con rectángulos idénticos, descripción ambigua, timeout
o error se rechazan. El consumidor usa XDG temporal y bus inexistente, no abre paneles,
captura ni registra otra prueba. Informe sin títulos/apps/PID o nombres de escritorios.

Compilaciones normal/ASan y rechazo real de offscreen correctos; Python R4 184/184,
CTest isolated-local-configuration pasa. Caso nativo nuevo compilado en test-desktops,
pero native-desktop-protocol bloqueado por wl_client_create EPERM antes de Qt. Wrapper
real bloqueado por IPC del ejecutor. No se declara ejecución Wayland/lectura real de las
dos salidas ni activación probada por este diagnóstico. No exige otro login ni cambia
plugins/requisitos/perfiles. Evidencia BREEZE_R4_DESKTOP_OUTPUTS_RESULTS.json.

## Continuación R4 §259–260 — lectura real por salida y ciclo de activación preparado

2026-11-17: el usuario ejecuta el diagnóstico de §258; passed/readOnly/bindingVerified true.
LG [2560,0,3840,2160] en escritorio 10, MSI [0,720,2560,1440] en 1; IDs 1–10, contador común
10, global 1. Cero peticiones de activación y ventanas. Evidencia de lectura real conservada
en BREEZE_R4_DESKTOP_OUTPUTS_RESULTS.json; no implica activación ni panel diario.

Siguiente ensayo explícito:

```sh
python3 /mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/check-desktops-activation.py --focus-cycle
```

En esta disposición pedirá enfocar LG/10 y volver a MSI/1 mediante requestActivateOnScreen
original. Sólo usa los escritorios ya visibles: no pide nuevos ni relocaliza/cambia asignaciones
de salida. Resume/pause correlacionados y lectura Qt en cada paso; debe volver al estado inicial
en Hyprland con deltas exactos de accepted/applied/observed/dispatched, sin fallo/no-op/rechazo/
cancelación. Cambios de salidas/asignaciones invalidan la medición y no disparan restauración
obsoleta. El ciclo sí cambia brevemente el foco, por eso requiere --focus-cycle; la consulta
check-desktops-session.py continúa siendo sólo lectura.

El wrapper mantiene bloqueo compartido en el inodo existente del gestor de skins (sin
truncar/borrar), bloqueo nativo de acciones y comprueba Breeze bajo ellos. Rechaza especiales
visibles antes/después para no ocultar Magic al volver al escritorio normal. El consumidor
temporal no abre superficies/capturas/paneles ni registra una prueba; al fallar pausa la
conexión y no lanza acciones alternativas. No demuestra foco de una app/puntero ni navegación
a escritorios no visibles. No se ha ejecutado en sesión desde el asistente.

Normal/ASan compilados, rechazo offscreen sin peticiones probado en ambos; Python R4 197,
isolated-local-configuration pasa. Prueba C++ nueva compilada, ejecución bloqueada antes de
Qt por wl_client_create EPERM. Evidencia BREEZE_R4_DESKTOP_ACTIVATION_RESULTS.json.

## Continuación R4 §261 — fallo real de activación, diagnóstico conservado

2026-11-17: primer ciclo real falla: destino no observado, paused/restoredInitialOutput true.
El estado final igual al inicial no acredita que llegara a enfocar otra salida. La causa aún
se desconoce; el informe anterior perdía la telemetría del hijo/servidor al salir con error.

Ahora conserva destino, observación fallida/final, estado de control, pasos y diagnóstico
del proveedor. Se puede leer el fallo ya registrado sin repetir acciones:

```sh
python3 /mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/check-desktops-activation.py --diagnose-last
```

No necesita binario Qt ni toma bloqueos de acciones; consulta sólo errores/contadores y
asignaciones. Un fallo de lectura parcial conserva los otros datos. El último error de
activación previo deja de vetar para siempre un futuro reintento explícito; al finalizar
se mantienen las comprobaciones estrictas de recibos y errores. No hay reintentos automáticos.
Ayuda/notificación/traspaso corrigen el nombre corto de native-desktops.py a su ruta completa.

Normal/ASan compilados; Python R4 201/201. Caso C++ nuevo de fallo/observaciones sin reintento
compilado, sin ejecución Wayland aquí por el bloqueo conocido. --diagnose-last no puede leer
el IPC desde este ejecutor. Falta su resultado desde terminal antes de atribuir la causa o
modificar el proveedor. Sin despliegue de plugin ni nuevo login solicitado.

## Continuación R4 §262 — una sola acción nativa de foco por activación

Diagnóstico del usuario: la primera petición se acepta/despacha, pero el backend devuelve
activation-readback-mismatch (0 applied/observed, 1 failed/rejected). Se reproduce con la
integración anterior y cuerpos exactos de Hyprland 0.56.2: focusMonitor seguido de
changeWorkspace en el workspace ya activo recalcula el puntero y puede volver al monitor
anterior con destino vacío y no_warps=true. No se ha medido si el destino real estaba vacío.

applyExact usa ahora sólo focusMonitor para workspaces ya activos; para inactivos usa sólo
changeWorkspace por objeto (absoluto). Respeta no_warps y conserva el rechazo si el backend
no confirma el resultado. activationRoutingVersion=2 permite comprobar la generación
cargada y el preflight impide repetir el ciclo sobre el módulo anterior.

Regresión con funciones upstream fijadas por SHA256 y andamiaje de datos: 48 combinaciones
normal/ASan, tres reproducciones del fallo anterior. Compila el applyExact actual y el
WorkspaceActivator real; no es prueba de compositor o superficies. CTest nuevo pasa en ambos
builds, Python R4 202/202, plugin compilado con commit correcto y sin símbolos UNIQUE.

Instalado mediante make install atómico; inodo anterior conservado sin cambios comprobando
un descriptor abierto. La sesión conserva el módulo anterior: cerrar sesión y volver a
entrar antes de ejecutar el ciclo. Sin emerge/sudo, hot load/unload ni reinicio de Quickshell.
La aceptación real corregida, navegación/resto R4 y panel diario siguen pendientes.
Evidencia ampliada en BREEZE_R4_DESKTOP_ACTIVATION_RESULTS.json.

## Aceptación real R4 §263 — activación por salida corregida

2026-11-17: el usuario ejecuta --focus-cycle con la ruta v2 y aporta passed true. KDE activa
LG/10 y vuelve a MSI/1: dos peticiones, deltas accepted/applied/observed/dispatched de 2,
sin fallo/rechazo/cancelación/no-op. Geometrías/asignaciones iniciales conservadas y barrera
final confirmada en pausa (serial 2, resumed false, asociación verificada, sin error).
El preflight exige activationRoutingVersion=2; este pase acredita su adopción en el ensayo.

Se cierra este fallo para los pares ya visibles de la disposición probada. No se extiende
a navegación a escritorios no visibles, foco de ventana/puntero, otras escalas/disposiciones,
teardown/logout ni panel diario. replacementReady/r4Complete siguen false. Evidencia
BREEZE_R4_DESKTOP_ACTIVATION_RESULTS.json; no se repiten pruebas o cambios de runtime.

## Continuación R4 §264 — navegación a un escritorio no visible del mismo monitor

Preparado, sin otro login ni cambio de plugin:

```sh
python3 /mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/check-desktops-activation.py --workspace-cycle
```

Selecciona un ID configurado que aún no tenga workspace materializado y que sus reglas
vinculen explícitamente al monitor enfocado, sin persistencia ni onCreatedEmpty. No reutiliza
workspaces existentes, aunque estén vacíos. Reglas de vínculo/creación no literales fuera
de alcance se rechazan; no se cambia configuración del usuario. La selección se revalida
antes de arrancar. WorkspaceState::create 0.56.2 puede obedecer vínculos y por eso no basta
con pasarle el monitor del foco; también se evita ejecutar comandos de creación del usuario.

Cliente KDE original: requestActivate(target) → lectura global y por salida → requestActivate
del ID inicial. Cada paso permite cambiar sólo el workspace del monitor original; todas
las otras salidas y geometrías/inventario deben conservarse. Puede materializar un ID que
ya estaba anunciado; no usa crear/quitar del protocolo ni añade un ajuste. Barrera/recibos
exactos y vuelta al estado inicial como en §260; un fallo no provoca acciones de respaldo
que recuperen un foco obsoleto. No garantiza exclusión de toda entrada/edición externa.

212 pruebas Python (10 nuevas), compilaciones normal/ASan, rechazo offscreen sin acciones
y regresión local pasan. Caso nativo Qt/Wayland sólo compilado: wl_client_create EPERM
impide iniciarlo aquí. Pendiente de ejecutar este comando en la sesión. El ensayo por
salidas de §263 no se repite; R4 y panel diario siguen abiertos. Evidencia
BREEZE_R4_WORKSPACE_NAVIGATION_RESULTS.json.

## Aceptación real R4 §265 — escritorio libre no visible en el mismo monitor

2026-11-17: el usuario aporta passed true, selectedDesktop 3 y dos pasos verificados de
requestActivate original: MSI/1 → MSI/3 → MSI/1. Deltas accepted/applied/observed/dispatched
de 2; cero fallos/rechazos/cancelaciones/noops. LG/10 se conserva en las comprobaciones por
salida y al final; geometrías y asignaciones originales coinciden, pausa final confirmada
(serial 2, resumed false, asociación verificada y sin error). Sin ventanas/paneles/capturas
ni cambios de configuración. No se midió foco de una app/puntero ni otras disposiciones.

Este caso de navegación queda aceptado. No se extiende a escritorios ocupados, relocalización
entre salidas, logout/teardown o panel diario. Persistencia/autoridad/recuperación diarias
y cierre de R4 siguen pendientes. Evidencia BREEZE_R4_WORKSPACE_NAVIGATION_RESULTS.json.
No se repiten las pruebas aceptadas.

## Recuperación explícita de perfil R4 §266 — estado actual ilegible

2026-11-17: restore requería una generación actual válida para poder abrir ProfileStore.
La nueva operación estática recover toma el mismo lease pero verifica directamente el
snapshot elegido. Conserva sus cinco archivos completos, crea otra generación y archiva
el head anterior byte por byte (o registra su ausencia), con hash y copia elegida. Publica
los directorios de generación/registro completos antes de reemplazar head atómicamente.
No selecciona automáticamente una copia y no cambia las rutas nativas de la generación vieja.

| Caso | Resultado comprobado |
| :--- | :--- |
| Generación actual incompleta | Constructor normal rechaza; recuperación desde copia íntegra pasa |
| Head roto, vacío, no objeto, generación inválida o archivo ausente | Recuperación pasa y registra bytes originales o ausencia |
| Campos nativos/metadata desconocidos | Archivos completos conservados; campos de head legible retenidos |
| KSharedConfig viejo escribe tarde | Sólo modifica su ruta vieja, no la recuperada |
| Datos de copia alterados o inventario incompleto | Rechazo con head/generaciones/registros intactos |
| Layout inválido con hash recalculado | Corona/bindings rechazan la copia; no basta con rehashear |
| Head de versión futura, aliases, ID/ruta inválidos | Rechazo sin redirigir ni sustituir datos |
| Otro proceso conserva el lease | CLI rechaza antes de recuperar y conserva el head roto |
| Autoridad XDG fuera de /tmp | Exportación a fixture, recuperación CLI real y reapertura en otro proceso pasan |
| CLI/envoltorio reales | CLI recupera JSON roto; wrapper evita preflight sobre head ausente y termina offscreen |
| Lectura nativa posterior | Otro proceso carga Corona y relee widget/opciones/desconocidos recuperados |

Tres casos Qt dedicados incorporados a isolated-local-configuration y tres pruebas Python
del envoltorio. Compilaciones/regresión local normal y ASan pasan; 215 pruebas Python R4
pasan. ASan usa detect_leaks=0, sin afirmar ausencia de fugas de Qt/KDE. No se depende del
fixture Wayland bloqueado por el ejecutor. Evidencia BREEZE_R4_PROFILE_RECOVERY_RESULTS.json.

CLI: --recover-profile SNAPSHOT_DIR. Envoltorio: --profile DIR --recover-snapshot ID,
con raíces/D-Bus auxiliares desechables y sin compositor ni registro de preview. Snapshots
y generaciones viejas se conservan. Registros recoveries permanecen en el perfil original;
exportToState copia estado elegido y snapshots, no esos archivos de diagnóstico. El lease
serializa escritores cooperantes; comparación de presencia/bytes no es CAS global. Una
interrupción anterior a seleccionar head puede dejar directorios completos no elegidos;
no se ha ensayado crash/corte de energía ni se promete durabilidad frente a ellos.

No se ejecutó recuperación sobre perfiles personales ni se seleccionó/retiró la barra
diaria. replacementReady, r4Complete y verificación global siguen false. Autoridades,
selección/activación/fallback diarios y logout siguen pendientes. No repetir §263/§265.

## Elección persistente del perfil R4 §267

2026-11-17: ProfileSelection añade intención persistente por nombre y procedencia, con
revisión esperada para cambiar/vaciar. Datos en la autoridad XDG existente, separados de
los archivos KDE. No fija generación ni duplica opciones. Consulta sin crear estado ausente;
publicación atómica y campos desconocidos conservados. Repetir la elección vigente no escribe.

| Caso | Resultado comprobado |
| :--- | :--- |
| Consulta inicial | Sin perfil/revisión 0, sin crear la autoridad XDG |
| Elección y consulta en proceso nuevo | Mismo nombre/procedencia/revisión; archivos KDE validados |
| Revisión antigua o candidato ausente | Rechazo sin cambiar el registro |
| Misma elección | Sin escritura ni incremento de revisión |
| Perfil ya abierto por otro host | Rechazo de nueva apertura, cambio y clear |
| Editar y recuperar el perfil elegido | Nueva generación, elección intacta y opción nativa releída |
| Head roto/perfil desaparecido | Consulta informa fallo; clear puede retirar la elección |
| Procedencia distinta | Apertura rechazada; reelección explícita renueva la elección |
| JSON/futuro esquema/revisión/tipo/ruta inválidos | Rechazo; sin reset automático ni elección alternativa |
| Contador agotado o lease de selección ocupado | Rechazo sin publicación |
| Metadata como enlace | Rechazo sin modificar el destino |
| Servidor seleccionado real, offscreen | Confirma control, conserva lease, recibe stop, guarda/sincroniza/cierra y publica checkpoint |
| Envoltorio de metadata real | select/status/clear con revisiones correctas y archivos auxiliares eliminados |
| Preview de selección | Pide --serve-selected-profile, sin capturar una ruta previa; conserva restricciones de perfiles guardados |

Prueba Qt usa XDG_STATE_HOME privado físicamente fuera de /tmp. El servidor hijo real
no tiene salidas visibles del perfil; prueba ciclo de vida y guardado, no pintado Wayland.
Cinco pruebas Python nuevas cubren entorno offscreen/D-Bus/acciones descartadas, revisión
obligatoria, conflictos sin reintento y modo de preview seleccionado. 220 pruebas Python R4
y regresión local normal/ASan pasan. ASan con detect_leaks=0; sin certificación de fugas de
Qt/KDE. Evidencia BREEZE_R4_PROFILE_SELECTION_RESULTS.json.

openSelected adquiere ProfileStore bajo el lease de selección y el host lo retiene hasta
cerrar/checkpoint; no autorizar con una ruta de status. profileValidated sólo indica una
inspección puntual, y puede ser false por propietario activo: no diagnostica salud de sesión.
Nombre/procedencia no firma una instalación; leases y comprobación optimista de bytes no
prometen CAS global/durabilidad ante corte de energía. Selección JSON corrupta no se repara
automáticamente. No hay autostart, autoridad de retirada o consumidor diario instalado.

Sólo fixtures; elecciones/perfiles personales y barra diaria intactos. R4, servicios,
activación/fallback diarios y logout siguen abiertos; indicadores globales false. Sin
repetir pruebas de sesión aceptadas, desplegar plugin, reiniciar, cambiar requisitos o
hacer commit/push. AGENTS/CLAUDE, estado, plan y traspaso actualizados.

## Cierre ordenado del preview R4 §268

`bwm-power` ejecuta `panel-session.py session-exit` antes del cierre de aplicaciones y
Hyprland. Selecciona el registro por instancia del compositor y comprueba el PID y su
inicio. Espera primero la retirada de vistas y luego el recibo del envoltorio, identificado
por token y revisión. El recibo sólo certifica éxito si el proceso sale con código cero.
En el caso de un perfil guardado eso requiere guardar el layout de Corona, sincronizar
su configuración, publicar un checkpoint y terminar liberando el bloqueo del perfil.
Se reutiliza la revisión de una parada que ya está en curso. La ejecución total queda
limitada a ocho segundos. Un error deja un diagnóstico y el cierre continúa.

La regresión local ejecutó el envoltorio y el servidor seleccionado reales con Qt offscreen.
Forzó la caída del anfitrión mientras esperaba órdenes y verificó que se retirara el registro
y que la caída no generara un checkpoint. Después reabrió el mismo perfil y verificó un
checkpoint nuevo de la generación vigente al parar con `session-exit`. Pasan la regresión
normal y con AddressSanitizer (`detect_leaks=0`), las 223 pruebas Python R4 y las cinco
pruebas de `bwm-power`. La prueba del orden de cierre usa operaciones Bash simuladas.
Quedan por verificar el logout real de Hyprland y la activación del panel de uso diario,
que requiere comprobar servicios de widgets y reservas en sesión.

## Ensayo de reservas en varias salidas R4 §269

`r4-reservation-smoke.py` permite comprobar el mismo borde en varios monitores con
`--edge` y `--output` repetido. El anfitrión crea un panel nativo temporal de 48 px
en cada salida solicitada. El informe distingue solicitud y reserva efectiva de
Hyprland, y verifica que todos los vectores vuelvan a su valor inicial al retirarlo.

Normal y AddressSanitizer (`detect_leaks=0`) pasan `isolated-local-configuration`.
El anfitrión crea perfiles de dos salidas para cada uno de los cuatro bordes y los
reabre en otro proceso. Las 224 pruebas Python R4 pasan. El comparador admite
grosores distintos por salida en los datos observados, y rechaza bordes ausentes o
incorrectos, salidas o capas duplicadas y una limpieza parcial.

El intento desde el ejecutor se detuvo antes de iniciar el panel porque la consulta a
Hyprland devolvió `Couldn't set socket timeout (2)`. La evidencia de la reserva inferior
del MSI sigue en `BREEZE_R4_AREA_SESSION_RESULTS.json`.

## Reserva superior real en dos salidas R4 §270

El usuario ejecutó `--edge top` en MSI MAG 274Q X24 y LG UltraFine. El informe
`/tmp/bwm-r4-reservation-session-1000.json` confirma `reservationDeltaVerified: true`
y cero errores, con escala 1 y giro 0 en ambos monitores.

| Salida | Antes | Durante | Después |
| :--- | :--- | :--- | :--- |
| MSI | `[0, 0, 0, 44]` | `[0, 48, 0, 44]` | `[0, 0, 0, 44]` |
| LG | `[0, 0, 0, 44]` | `[0, 48, 0, 44]` | `[0, 0, 0, 44]` |

Hyprland observó una capa superior de 640 × 48 por monitor. La retirada automática
terminó con código 130, sin capas ni registro de preview. El ensayo no incluía
maximizado. Sigue pendiente probar las reservas laterales, otras escalas y el panel diario.

## Secuencia lateral y salida confirmada R4 §271

`--edge left --edge right` recorre ambos bordes con un perfil temporal por ensayo. El
segundo exige la geometría y los vectores de reserva originales en todos los monitores.
Si el primero falla, el informe conserva su diagnóstico y el siguiente queda sin ejecutar.
Cada parada comprueba el parentesco del proceso registrado con el envoltorio, su identidad
y la instancia de Hyprland. Espera el recibo de salida y guardado antes de certificar el
resultado. Restaurar la reserva tras un cierre forzado no basta para que pase.

Pasan 227 pruebas Python de R4 y `isolated-local-configuration` normal y con AddressSanitizer
(`detect_leaks=0`). El caso offscreen usa el anfitrión real, espera el recibo y confirma
checkpoint y limpieza. El intento desde el ejecutor se detuvo en la primera consulta IPC,
antes de abrir un panel. La medición lateral real queda pendiente.

## Fallo lateral en sesión y corrección R4 §272

El ensayo real pidió 48 px a la izquierda en MSI y LG. En ambas salidas el vector
quedó en `[0, 0, 0, 44]`, frente a `[48, 0, 0, 44]` esperado. Se observaron capas de
48 × 24 px y la salida terminó con código cero y recibo confirmado. Después no quedó
ninguna capa de prueba. El borde derecho quedó sin ejecutar.

LayerShellQt 6.7.5 convierte el eje con dos anclajes opuestos en una dimensión cero.
Hyprland 0.56.2 calcula esa dimensión sobre el área útil y resta el margen final.
La barra inferior restaba 44 px a la altura cada vez que el anfitrión la recalculaba.
Hyprland descarta geometrías no positivas antes de aplicar su reserva. En la conexión
que ofrece layer-shell v5, el anfitrión pide ahora un tamaño explícito, con dos anclajes
adyacentes y `exclusive_edge`. Conserva los anclajes y el margen anteriores si la
versión no está disponible. La lectura del registro usa los headers privados de
Qt Wayland, dentro del auxiliar.

Se recompiló `bwm-plasma-host`. Pasan `surface-geometry` e
`isolated-local-configuration` tanto normal como con AddressSanitizer
(`detect_leaks=0`), y 227 pruebas Python de R4. Las pruebas locales comprueban
anclajes y márgenes para los cuatro bordes. Queda por medir en Hyprland la reserva
con el anfitrión corregido. La consulta IPC desde el ejecutor sigue fallando.

## Reservas laterales reales en dos salidas R4 §273

El usuario repitió `--edge left --edge right` tras recompilar el anfitrión. El informe
confirma ambas pruebas sin errores. MSI y LG conservaron escala 1 y giro 0, y Hyprland
observó una capa de 48 × 640 px en cada salida durante cada prueba.

| Ensayo en ambos monitores | Antes | Durante | Después |
| :--- | :--- | :--- | :--- |
| Izquierda | `[0, 0, 0, 44]` | `[48, 0, 0, 44]` | `[0, 0, 0, 44]` |
| Derecha | `[0, 0, 0, 44]` | `[0, 0, 48, 44]` | `[0, 0, 0, 44]` |

Cada cierre devolvió código 0 y recibo `exitConfirmed: true`. Después de cada borde,
el registro de prueba y las capas habían desaparecido. Esto confirma la corrección
de §272 para la disposición ensayada. Maximizado, escalas distintas y la integración
del panel de uso diario quedan fuera de estos resultados.

## Plasmoides de la bandeja y dueño de SNI R4 §274

El anfitrión inventaría ahora los plasmoides vivos dentro del `CustomEmbedded` de la
bandeja original de Plasma. Los muestra bajo `embeddedApplets`, con su estado de carga
y la declaración de activación D-Bus si existe. Las filas directas y su orden permanecen
como antes. Los iconos SNI externos y los hijos todavía inactivos quedan fuera de esa lista.

La prueba Qt usa la bandeja original con un plasmoide temporal reconocido por su registro.
La preferencia editada se guarda con Corona, pasa el checkpoint y se relee en otro proceso.
Al destruir el hijo deja de aparecer en el inventario. Pasan la regresión local normal y
con AddressSanitizer (`detect_leaks=0`) y las 230 pruebas Python R4. El primer intento ASan
se interrumpió por `EAGAIN` después de que pasaran los dos casos nuevos. La repetición aislada
completó toda la regresión.

`r4-session-check.py --tray` consulta el nombre único del dueño de StatusNotifierWatcher
y confirma que sigue vigente tras leer las dos propiedades del servicio. Devuelve la
clase de dueño, el contador de iconos y si hay host registrado. Las pruebas cubren un
servicio ausente, una lectura incoherente y un cambio de dueño. El ejecutor devolvió
`bus-unavailable`. Queda pendiente la lectura de la sesión y probar el uso del watcher
por el anfitrión nativo, además de menús y clics.

## Dueño real de la bandeja SNI R4 §275

La consulta del usuario confirma que Quickshell posee `org.kde.StatusNotifierWatcher`
y devuelve dos iconos registrados. La comprobación de dueño no detectó cambios durante
la lectura. `watcherVerified: true`, `sessionModified: false`, `replacementReady: false`.

El fuente de Quickshell 0.3.2 confirma que `RegisterStatusNotifierHost` admite varios
nombres de host válidos. Su propiedad `IsStatusNotifierHostRegistered` siempre devuelve
true. El `hostRegistered: true` observado no identifica al host de KDE. Las fuentes
de Plasma 6.7.5 muestran que el widget usa el watcher existente para enumerar iconos y
suscribirse a sus cambios. Falta validar esa conexión y el manejo de iconos desde el
auxiliar nativo en sesión.

## Ensayo de enumeración con el modelo nativo de la bandeja R4 §276

`check-native-tray.py` requiere que Quickshell posea el watcher y que haya iconos
registrados. Lanza un proceso offscreen con la bandeja original. La lista de referencia
sale de `RegisteredStatusNotifierItems` del watcher. El anfitrión lee su propio
modelo `systemTrayModel`, filtra `itemType == StatusNotifier` y compara `DataEngineSource`
con la lista inicial. La comparación exige coincidencia de identificadores y nombre temporal
de host registrado por esa conexión. El nombre del dueño y la lista deben coincidir también
al terminar. La salida pública contiene contadores y booleanos.

`xdg-dbus-proxy` concede exclusivamente un nombre de host basado en el PID y reglas
del watcher para consultar propiedades, registrar el host y recibir altas/bajas. No
autoriza llamadas a los servicios de cada icono. El proceso nativo espera que el proxy
esté listo antes de `exec`. Los procesos de prueba verifican el PID, las reglas y las
raíces desechables. La prueba local de Qt verifica los roles en el modelo original. El
binario rechaza un bus fuera de su ruta desechable y devuelve el fallo previsto si esa
ruta no tiene bus.

Pasaron 232 pruebas Python de R4 e `isolated-local-configuration` normal y con
AddressSanitizer (`detect_leaks=0`).

El ejecutor se detuvo en la consulta inicial al bus de sesión. Queda por comprobar
la coincidencia en la sesión del usuario. El ensayo de enumeración no verifica los
datos de cada icono, entradas/salidas de items en vivo, clics ni menús.

## Enumeración SNI confirmada en sesión R4 §277

El ensayo del usuario devolvió `passed: true`, `nativeModelMatches: true` y
`nativeHostNameOwned: true`. El modelo original de KDE recibió las dos filas SNI
con los mismos identificadores que publicó Quickshell. La comparación antes y después
confirmó que el dueño y la lista seguían iguales.

`panelShown: false` y `replacementReady: false`. La aceptación cubre la enumeración
de los iconos registrados. Quedan las propiedades, las altas/bajas durante el ensayo,
el pintado, los clics y los menús.

## Lectura de propiedades e iconos SNI R4 §278

La opción `--properties` conserva la comparación con el watcher de Quickshell y añade
reglas `GetAll` exactas por nombre y ruta de item. Se excluyen nombres activables.
Si un item usa nombre único, se confirma un alias adquirido por el mismo dueño.
Sin alias no hay permiso para ese objeto y la cobertura queda incompleta. El informe
exige los mismos dueños y la misma lista al principio y al final.

El anfitrión lee estado SNI y categoría del modelo original, y cuenta los iconos de los
que KDE obtiene un pixmap lógico de 22 px. Publica contadores agregados, sin títulos,
rutas ni contenido de iconos. El modo comprueba la carga fuera de pantalla. El pintado
del panel, los cambios en vivo y las acciones siguen pendientes.

Compilaciones normal y ASan, `isolated-local-configuration` en ambos modos y 234
pruebas Python de R4 pasan. Se comprobaron reglas por objeto, rechazo de alias con
otro dueño, exclusión de activables y resultados incompletos. La sonda nativa devuelve
`filtered-bus-unavailable` sin proxy. La consulta desde el ejecutor se detiene en el
bus de sesión y queda pendiente medir los iconos de la sesión del usuario.

## Cobertura del filtro SNI en sesión R4 §279

El intento del usuario conservó dos filas coincidentes y el mismo watcher, pero
`filterableItemCount`, `nativePropertiesCount` y `nativeUsableIconCount` fueron cero.
Ese resultado sólo localiza el fallo en la obtención de los permisos por objeto.

La actualización pregunta al daemon por nombres y dueños. Distingue un nombre único
sin alias, un nombre activable excluido y un dueño no disponible. Para los objetos
excluidos con dueño conocido consulta `Status`, `Category` e `IconName` directamente
al nombre único. Sólo devuelve contadores. La lectura directa queda separada de
`nativePropertiesVerified`, que exige las propiedades y el pixmap en el modelo KDE.

Pasan 235 pruebas Python R4, incluidas resolución de alias, cambio de dueño,
exclusión de activables, desaparición y lectura escalar directa. La repetición en
sesión queda pendiente. El ejecutor sigue sin acceso al bus de sesión.

## Lectura directa por nombre único en el proxy local R4 §280

La prueba del usuario confirmó dos iconos con nombre único, ambos sin alias y con
metadatos escalares accesibles. Uno anuncia icono por nombre. El watcher y los
identificadores KDE coincidieron. El proxy estándar dejó cero objetos autorizados.

La copia local de `xdg-dbus-proxy` añade una regla `GetAll` para el objeto exacto de
un nombre único. Conserva el filtro de método y ruta. La prueba C ejercita el
despacho real del proxy, y el parser rechaza activación, comodines y señales como
reglas por nombre único. `--properties` usa el binario ya compilado, verifica su
versión y contrasta también la identidad del bus antes y después. Se mantienen la
copia y el servicio del sistema.

Pasan la compilación, las pruebas del filtro y 237 pruebas Python. El ejecutor no
puede abrir un bus privado para una prueba integrada. Queda por verificar en la
sesión real que KDE obtenga las propiedades y los pixmaps de los dos iconos.

## Arranque del proxy con nombres únicos R4 §281

El usuario obtuvo dos reglas exactas y `native-tray-probe-timeout` sin contadores
del modelo KDE. La instantánea inicial mostró dos iconos registrados por Quickshell.

El código de inicio pedía al daemon el dueño de cada nombre filtrado. Para un nombre
único, la respuesta es el propio nombre. La variante anterior guardaba esa respuesta
como alias y la evaluación recorría el alias de forma recursiva. La versión
`0.1.8+bwm-sni-unique-2` evita esa consulta para nombres únicos y protege la tabla de
alias. Mantiene las suscripciones de dueño y las reglas exactas por método y ruta.

La regresión C falló antes de la corrección y pasa con el binario recompilado. Pasan
237 pruebas Python. El comprobador añade `timeoutStage` si se agota el plazo. Esta
ejecución encontró el bus de sesión inaccesible. La lectura de las propiedades y los
pixmaps de KDE queda pendiente de `--properties` en Breeze.

## Lectura del estado del modelo SNI R4 §282

El usuario obtuvo dos reglas por objeto y las dos filas nativas, con el watcher
de Quickshell y los objetos estables hasta el final. El informe anterior dio
`nativePropertiesCount: 0` y `nativeUsableIconCount: 0`.

En Plasma 6.7.5, `StatusNotifierModel::data` llama a `extractStatus` en ambos
roles de estado. Convierte el texto SNI del bus a `Plasma::Types::ItemStatus`. La
sonda comparaba el `QVariant` con las cadenas del bus y sólo probaba el pixmap si
pasaba esa condición. La corrección lee el valor del enum, exige categoría y
mide los pixmaps de 22 px por separado. El éxito sigue requiriendo ambas medidas
para todas las filas. La regresión cubre el retorno implícito del modelo, que
guarda el estado como entero en `QVariant`, además de los estados sin datos y
las categorías vacías. Pasan `isolated-local-configuration` y 237 pruebas Python.
Pendiente medir las dos filas en la sesión Breeze.

## Aceptación de propiedades y pixmaps SNI en Breeze R4 §283

El usuario ejecutó `check-native-tray.py --properties` y obtuvo `passed: true`.
El modelo de Plasma coincidió con los dos elementos que anunció Quickshell. El
proxy acotó las consultas a los dos objetos exactos. `nativePropertiesCount` y
`nativeUsableIconCount` fueron 2 y `nativePropertiesVerified` fue true. El dueño,
el inventario y los objetos seguían iguales al cerrar el ensayo.

El anfitrión poseyó su nombre temporal. `panelShown` y `replacementReady` fueron
false. Quedan por probar los cambios en vivo, la presentación y las acciones.

## Ciclo de un elemento SNI en bus privado R4 §284

El nuevo ensayo crea una bandeja original de Plasma fuera de pantalla. En un bus
privado sin servicios activables, registra un elemento de prueba con pixmap rojo,
emite `NewStatus` para pasar a pasivo y `NewIcon` para sustituir el pixmap por uno
azul. Cierra la conexión del elemento y exige su retirada del modelo. Cada fase
espera la observación correspondiente antes de pasar a la siguiente. El watcher
de prueba se retira con su bus y se borran las raíces XDG temporales.

Pasan compilación, firma D-Bus `a(iiay)` de los pixmaps del elemento y 237 pruebas
Python R4. El ciclo integrado quedó bloqueado antes de iniciar Qt por la denegación
al abrir el socket del bus privado en el ejecutor. Quedan por comprobar el ciclo
en terminal, los eventos bajo el proxy, la presentación y las acciones del panel.

## Aceptación del ciclo SNI original R4 §285

La ejecución del usuario en terminal obtuvo cuatro pases y cero fallos en 222 ms.
El modelo de KDE incorporó el elemento, cambió su estado e imagen y retiró la fila
al desaparecer el productor. El aviso de KWindowSystem sobre el plugin de
plataforma se produjo en Qt offscreen. El ciclo ejecutado fue el del bus privado.

## Ciclo SNI con filtro por objeto R4 §286

El modo `--filtered` conserva el bus privado y conecta el cliente KDE al proxy
local. El proxy permite el registro temporal del anfitrión, la lectura y las
señales de alta/baja del watcher, `Properties.GetAll` para el icono de prueba y
sus dos señales `NewStatus` y `NewIcon`. El test exige `AccessDenied` al consultar
otra ruta del productor y verifica después los cuatro cambios del modelo.

El proxy `0.1.8+bwm-sni-unique-3` valida los permisos por nombre único, ruta e
interfaz. Sus pruebas C comprueban el despacho de llamadas y broadcasts, y el
constructor rechaza reglas con comodines o miembros no previstos. La consulta de
propiedades en Breeze continúa usando sólo `GetAll`. Pasan la compilación del
ensayo, la firma de los pixmaps, el filtro C y 237 pruebas Python. La ejecución
integrada del modo filtrado queda pendiente en la terminal del usuario.

## Aceptación del ciclo SNI filtrado R4 §287

El usuario ejecutó `check-native-tray-events.py --filtered`. QtTest registró cuatro
pases, cero fallos y cero omisiones en 229 ms. El proxy rechazó la consulta a otra
ruta y el cliente KDE recibió el alta, los cambios y la retirada. El aviso de
KWindowSystem se produjo con Qt offscreen. El ensayo se limitó al bus privado.

## Peticiones SNI desde el plasmoide original R4 §288

`check-native-tray-events.py --actions` invoca los métodos del plasmoide con el
identificador que obtuvo el modelo. El icono de prueba devuelve cuatro recibos
con los argumentos exactos de `Activate`, `SecondaryActivate`, `Scroll` y
`ContextMenu`. Como no exporta un menú importable, KDE usa la solicitud SNI de
menú contextual. La activación usa el token vacío que ofrece KWindowSystem en
Qt offscreen. El modo filtrado conserva sus reglas y comprueba que el icono
de prueba no recibe `Activate`.

Pasan la compilación, la firma D-Bus de pixmaps, la prueba Qt del token vacío y
237 pruebas Python. El ejecutor no pudo abrir el socket del bus privado. Queda
pendiente la comprobación de los cuatro recibos en terminal, así como los tokens
de Wayland, la importación y la presentación del menú.

## Aceptación de peticiones SNI en bus privado R4 §289

El usuario ejecutó `--actions` y obtuvo cinco pases, cero fallos y cero omisiones
en 432 ms. El productor recibió los argumentos esperados para las cuatro peticiones.
El aviso de KWindowSystem se produjo con Qt offscreen. El de `ContextMenu` confirma
la ruta prevista para el productor sin menú D-Bus.

## Importación y acción de menú D-Bus R4 §290

El modo `--menu` ejecuta el importador del plasmoide original contra el menú
exportado por `KStatusNotifierItem`, con raíces XDG y bus privados. Comprueba
que se muestre el menú importado en Qt offscreen, que conserve las opciones y
su estado y que el evento de la opción habilitada llegue al productor.

Pasan la compilación del binario y 237 pruebas Python. La ejecución integrada del
menú queda pendiente en la terminal del usuario. El ensayo usa una acción Qt
programática y una ventana offscreen. La entrada y colocación reales bajo Wayland
siguen pendientes. `replacementReady` permanece false.

## Aceptación de la importación y acción D-Bus R4 §291

El usuario ejecutó `--menu` con cinco pases, cero fallos y cero omisiones en
223 ms. El menú importado de Plasma conservó ambas acciones y una selección
llegó al productor. Qt offscreen avisó sobre elevación y teclado. Al finalizar
la prueba, el daemon privado registró un `UnknownObject` del productor. El
ensayo siguió pasando y las dos comprobaciones se aceptaron fuera de pantalla.

## Menú importado con capa e input Wayland R4 §292

El modo `--menu-wayland` agrega un botón temporal en una capa superior sin
reserva de espacio. La apertura desde un clic comprueba el asiento y el serial
Wayland. La prueba exige que el menú quede expuesto, tenga rol `xdg_popup`,
conserve esa capa como padre transitorio y use los anclajes de borde superior.
Un clic en la acción habilitada debe llegar al productor del bus privado.

El importador original envía `Event("closed")` al ocultar el menú. El ensayo
cierra el menú y espera una lectura de su versión antes de destruir al productor,
de modo que el objeto permanezca publicado durante el cierre. Pendiente verificar
el resultado en terminal. Pasan la compilación y 237 pruebas Python. En el
ejecutor, el daemon se detuvo al abrir el socket del bus privado.

## Aceptación del menú Wayland y selección de monitor R4 §293

El usuario ejecutó `--menu-wayland` y completó los clics. QtTest informó cuatro
pases y cero fallos en 15,157 s. El ensayo confirmó el popup anclado a la capa
de prueba y que la acción llegó al productor. El aviso `UnknownObject` no apareció.
La capa se abrió en otro monitor, según el usuario.

El lanzador obtiene ahora la descripción de la salida enfocada en Hyprland al
inicio. `--output` permite elegir otra salida por descripción. El auxiliar usa
el resolver común y fija la pantalla antes de mapear la capa. Comprueba que la
capa y el popup correspondan en Qt a la pantalla elegida. Pasan la compilación,
la comprobación Qt de descripciones y las pruebas Python. Queda verificar la
ubicación física en la sesión con los dos monitores.

## Maximizado en los bordes superior y laterales R4 §294

Las reservas en esos bordes ya pasaron en dos salidas (§§270–273). El marco
maximizado y su reajuste automático estaban comprobados en MSI con reserva
inferior (§208). El comprobador permite ahora medir un marco propio en varios
bordes sucesivos de una salida. Cada ensayo conserva su informe y se exige la
línea base de la primera prueba antes de avanzar. El resumen distingue reserva,
marco explícito y reajuste automático por borde.

Las 241 pruebas Python incluyen la secuencia y la medida horizontal al añadir
una reserva izquierda. Qt offscreen importó perfiles nativos con los bordes
superior e izquierdo y derecho persistidos. El intento de sesión desde el
ejecutor se detuvo en el acceso a Hyprland. Las medidas reales siguen pendientes.

## Aceptación de maximizado en MSI R4 §295

El usuario confirmó la reserva, el marco y el reajuste automático en los tres
bordes. El informe de sesión confirmó los recibos de salida, una reserva de 48 px
por ensayo y la vuelta a `[0, 720, 2560, 1396]`. El LG conservó su reserva inferior
de 44 px en toda la secuencia.

| Borde en MSI | Marco observado con panel (`x, y, ancho, alto`) |
| :--- | :--- |
| Superior | `0, 768, 2560, 1348` |
| Izquierdo | `48, 720, 2512, 1396` |
| Derecho | `0, 720, 2512, 1396` |

El comprobador actualizado conserva el maximizado inicial si las observaciones
automáticas coinciden con el área útil. Registra `during` o `after` en
`remaximizedPhases` si tuvo que repetir el maximizado para medir el marco en
alguna fase. Las pruebas cubren las cuatro combinaciones de coincidencia entre
aparición y retirada. Pendiente aplicar el ensayo actualizado al LG.

## Maximizado en LG y retorno rápido del área R4 §296

El informe del usuario confirmó reservas, marco y salida limpia en los cuatro
bordes del LG. Superior e izquierdo y derecho completaron el reajuste con
`remaximizedPhases: []`. Abajo la reserva volvió de 92 a 44 px y el marco quedó
en `[2560, 0, 3840, 2068]` hasta remaximizar `after`, cuando volvió a 2116 px.

La prueba reproduce que la reducción se aplique y se retire el panel antes
del siguiente sondeo. El observador reutilizaba la confirmación del área previa
cuando reaparecía su firma. La corrección la invalida al detectar el cambio.
Cada transición descarta el presupuesto de intentos de la firma anterior. El
límite por firma sigue vigente. Pendiente confirmar el borde inferior del LG
con el puente recargado.

## Aceptación de la retirada inferior en LG R4 §297

El usuario repitió el borde inferior con el puente recargado. El informe de
sesión muestra la reserva `44 → 92 → 44`, el marco de altura
`2116 → 2068 → 2116` y `remaximizedPhases: []`. El proceso de prueba confirmó
su salida. El MSI conservó su reserva de 44 px. Reservas, marco y reajuste
automático del LG inferior pasaron.

## Ventanas maximizadas en ambas salidas R4 §298

El comprobador admite una ventana propia por monitor solicitado. Las maximiza
antes de crear los paneles y lee las transiciones automáticas de todas antes
de intervenir en una. El informe privado registra las medidas por descripción
en `maximizedByOutput`. La prueba de arranque parcial confirma la limpieza de
las dos ventanas de prueba si falla el inicio de la segunda.

Qt offscreen importó un perfil temporal con dos paneles y sus asociaciones
de salida. Las regresiones comprueban la independencia de las medidas y el
cierre. El intento simultáneo se detuvo en el acceso a Hyprland desde el
ejecutor. Pendiente la medida en sesión de los dos marcos simultáneos.

## Aceptación del maximizado inferior simultáneo R4 §299

El usuario obtuvo las tres verificaciones positivas en ambas pantallas con
`--maximize --edge bottom`. El informe confirma aumento y retirada de 48 px
por salida, `remaximizedPhases: []` en las dos ventanas y cierre del auxiliar.

| Salida | Altura inicial | Altura con panel | Altura tras retirarlo |
| :--- | ---: | ---: | ---: |
| MSI MAG 274Q X24 | 1396 | 1348 | 1396 |
| LG UltraFine | 2116 | 2068 | 2116 |

## Escala y transformaciones en la medición R4 §300

El comprobador calcula el marco esperado con la escala efectiva y la
transformación que publica Hyprland. Usa los píxeles físicos del modo para
obtener dimensiones lógicas redondeadas, y aplica las reservas ya lógicas.
La expectativa sigue siendo independiente del maximizador de BWM. Se conserva
la comprobación de marco completo y la tolerancia de un píxel lógico.

247 pruebas Python y 32 comparaciones con el redondeo de hyprutils 0.14.2 pasan.
La aceptación en sesión sigue acreditando sólo la escala y giro de §299.

## Redondeo de marco en el maximizador y el observador R4 §301

Las regresiones usaron un modo físico de 251 × 333, escala 2, giro 1 y reservas
de 2, 3, 4 y 5 px. Antes, ambos cálculos de Breeze daban un área de 160 × 117.
Con el redondeo de dimensiones de Hyprland, los dos devuelven 161 × 118.
El comprobador conserva su cálculo independiente. Las demás llamadas de
`monitor_box` conservan su semántica previa, incluida la lectura de estado.

Pasan 248 pruebas de R4, la suite de maximizado y las de selección de salida,
puente y cambio de skin. La comprobación de geometrías distintas en el
compositor sigue pendiente y el puente requiere recarga para adoptar el cambio.

## Escalas y giros en una salida headless temporal R4 §302

`r4-geometry-check.py --run` crea una salida headless con nombre único, aplica
modo, escala y giro con una regla `hl.monitor` y cambia su reserva con el campo
`reserved` de esa regla. Mide la ventana propia de R4 maximizada en esa salida
con `useful_area()` del comprobador y lee primero el reajuste automático. Los
monitores físicos no se reconfiguran.

El primer intento acertó el maximizado explícito pero no el reajuste: el
observador de `kwin_area.py` rechazaba toda la instantánea si un monitor tenía
descripción vacía. Las salidas sin EDID desactivaban el seguimiento en todos los
monitores. La firma en memoria usa ahora el conector cuando falta la descripción.

| Modo | Escala | Giro | Área lógica | Explícito | Automático |
| :--- | ---: | ---: | :--- | :--- | :--- |
| 1920x1200 | 1,25 | 1 | 960 × 1536 | Sí | Sí |
| 1920x1080 | 1,5 | 3 | 720 × 1280 | Sí | Sí |
| 2560x1600 | 1,6 | 2 | 1600 × 1000 | Sí | Sí |
| 1920x1200 | 1,25 | 5 | 960 × 1536 | Sí | Sí |

Reserva `[0, 0, 0, 44] → [0, 48, 0, 44] → [0, 0, 0, 44]`, sin remaximizar.
Limpieza verificada (salidas físicas, workspaces y foco iguales). Los medios
píxeles lógicos no se pueden producir: Hyprland 0.56 rechaza esas escalas. La
reserva no procede del panel nativo, que no admite salidas sin descripción.
Evidencia en `BREEZE_R4_GEOMETRY_SESSION_RESULTS.json`.
