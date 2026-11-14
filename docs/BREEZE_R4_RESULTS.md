# R4 — anfitrión nativo de plasmoides: criterios originales cumplidos

> **Estado 2026-11-14 (última sección):** la puerta de salida original —un widget externo no
> conocido de antemano muestra y guarda su opción propia— se supera con widgets elegidos por el
> orden de la tienda KDE, instalados y retirados con el proveedor nativo de «Obtener nuevos», y
> se comprueba también en la sesión Hyprland. El resto del prompt R4 estaba ya cubierto (secciones
> siguientes). La sustitución del panel diario, backends de tareas/escritorios y aceptación en
> otras escalas/bordes no forman parte de esa puerta y siguen pendientes, sin declararse hechas.

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
