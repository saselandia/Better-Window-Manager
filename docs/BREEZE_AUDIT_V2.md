# Auditoría R0 de Breeze II

2026-11-12. Base `2a4ae3c` **más el árbol de trabajo actual**, incluidas las correcciones R1,
el prototipo R2 y la contención del crash. Revisión R0 completada sobre el material disponible;
no es una certificación gráfica. Fuentes y binario instalado fijados mediante 26 huellas SHA-256
en `BREEZE_R0_REFERENCE.json`. No se guardan configuraciones privadas ni capturas del usuario.

## Entorno comprobado

- `QT_QPA_PLATFORM=offscreen systemsettings --version`: **6.7.5**. El intento sin offscreen
  falló al no poder conectar con Wayland/X11; no implica una instalación rota.
- Quickshell **0.3.2**, revisión `4f508be500dea6e5732cc3d50382a0048b17e7b1`.
- Base de paquetes Gentoo: KConfig/KCMUtils/KSvg **6.29.0**, Kirigami **6.29.0-r1**;
  Breeze, libplasma, KDecoration, Aurorae, KWin y System Settings **6.7.5** (revisiones Gentoo aparte).
- Fuentes locales verificadas: plasma-desktop `v6.7.5`, commit
  `43f55fff3480c6eb5f60133f045bfc74b9c67d84`; plasma-workspace `v6.7.5`,
  `cc1ab7963f94a9b76836412855caed6b94066188`.
- Headers Hyprland instalados. La variable de entorno apunta a la revisión `efb5099…`,
  pero **no demuestra la versión del proceso vivo**. `hyprctl` no accede al socket.
- Sin acceso a Wayland, X11, D-Bus ni IPC Hyprland desde el sandbox de esta sesión.
  No se pueden inventariar propietarios D-Bus, plugin cargado, atajos efectivos o ventanas.
  Los comandos fallidos no son pruebas gráficas aprobadas. No se pidió elevar permisos.

## Inventario priorizado

`C`: comprobado en código; `H`: hipótesis pendiente de reproducción; `M`: comparación manual pendiente.
Todas las rutas QML de la tabla parten de `config/quickshell/ii/`; scripts de
`config/hypr/`. Un P0 es un fallo de integridad/visibilidad, P1 una función principal incompleta,
P2 una mejora de paridad secundaria. No implica que cada función de KDE deba añadirse a BWM.

| Prioridad/estado | Ruta y símbolo | Hallazgo y referencia original | Corrección y aceptación |
| :--- | :--- | :--- | :--- |
| P0/C crash, causa pendiente | ScreenshareSession::init (binario Hyprland), fuentes de captura del cambiador y tareas | SIGSEGV por acceso nulo documentado; contención aplicada, sin reproducción aislada ni recuperación certificada | Gate de estabilidad antes de R1 gráfico y de R6; mantener miniaturas desactivadas |
| P0/H | scripts/keybinds-manager.py, `ws_toggle_special`; modules/user_binds.lua | Alt+S apunta a magic; mover a special:magic. No hay dos identidades por skin en estos datos | Ver atajos/reglas efectivos mañana; no migrar otros especiales |
| P0/C, parcial corregido | scripts/toggle-minimize.py, `origin_workspace`, `minimize_win`, `restore_win` | El defecto inicial del ID negativo ya tiene corrección por nombre y pruebas aisladas; falta integración de sesión y dock Retro | R1: verificar ida/vuelta sin extraer de Magic en las tres skins |
| P0/H, parcial corregido | modules/plasma/panel/TasksModel.qml `activate`; skins/plasma/scripts/kwin-window.py `focus` | Ahora delega en activación común del workspace especial; no se ha comprobado que elimine el síntoma reportado | R1: verificar semántica real de focus, elevación e identidad, sin extraer ventanas |
| P1/C, parcial corregido | modules/ii/altTab/AltTab.qml `getVisibleWindows` y `focusTarget` | Filtro y PID corregidos y probados aisladamente; no validados con compositor | R1: comprobar Magic visible/oculto, dos monitores y timer con ventana cerrada |
| P1/C, contención vigente | skins/plasma/hypr/rules.lua `breeze-float-all`; src/breezebars/barRemote.cpp `CBreezeShadow::draw` | no_shadow=true suprime la sombra KDE. Su retirada se revirtió tras el crash; no hay causalidad probada entre sombra y crash | R6: validar captura/render de forma aislada antes de levantar el veto; no reactivarlo como simple ajuste Lua |
| P1/C | skins/plasma/hypr/animations.lua; kwin.lua | Curvas MD3 y tabla duplicada. kwin.lua sólo escala factor !=1, pero appearance carga primero la base: no se demuestra un fallo al volver a 1 | Una fuente; medir KWin (efectos de fábrica) y comprobar 0/1/2 y vuelta a 1 |
| P1/C | scripts/open-settings.sh; modules/plasma/settings/Catalog.js | App qs -p con catálogo propio y seis QML upstream; no es systemsettings | Anfitrión real y KCM BWM descubiertos por KDE; conservar alias |
| P1/C | src/bwm-kcmhost/KcmHost; settings/ModuleView.qml | Host sólo KQuickConfigModule; QWidget se abre como app externa o se sustituye | KCMUtils real en systemsettings; comprobar QWidget y QML, cambios sin guardar |
| P1/C | panel/PanelEditor.qml | Casillas de seis widgets; no PanelConfiguration original | Port upstream desktoppackage/contents/configuration/PanelConfiguration.qml y panelconfiguration/* |
| P1/C | panel/PanelState.qml y Panel.qml | Estado de panel por pantalla pero configuración compartida, sin identidades de panel persistentes independientes | Modelo de containments/instancias antes de varios paneles; migración sin pérdida |
| P1/C | applets/AppletHost.qml; tray/SystemTray.qml | Contrato manual y lista explícita, no Plasma::Applet/PlasmoidItem | Corona/Containment/Applet; demostrar paquete externo y configuración original |
| P1/C | settings/Catalog.js `bar`, panel README | Opciones clock/systemTray existen en datos pero no interfaz completa | Configuración de applet upstream por instancia, no lista de opciones hardcode |
| P1/C | applets y tray/TrayPopup.qml | Popups portados, no anfitrión de páginas config.qml/main.xml | AppletConfiguration upstream usa configModel y cfg_*; probar Aplicar/Cancelar/Predeterminados |
| P1/M | src/bwm-decorator y breezebars | Sombras/decoration usan Qt externo y memfd; hubo crash de propietario único | Mantener modelo; prueba de destrucción/reconexión y geometría/alpha/DPR |
| P1/M | skins/plasma/scripts/kwin-tiles.py; KWinSnap.hpp | Bordes interiores, Mayús y vecinas pendientes en plugin final según F10 | Comprobar binario cargado y matriz física de dos monitores |
| P1/M | CSDDetect.cpp, CSDLogic.hpp | Negociación comprometida y hints, matriz real incompleta | Una barra, marco exacto, Wayland/X11, cambios dinámicos, fullscreen |
| P1/H histórico | kwin-window.py `maximize` y quick-tile | Ctrl+flechas restauraba centrada según §3.153; no se reprodujo en esta auditoría | Comparación de ida/vuelta con marco y workspace correctos |
| P1/M | modules/plasma/lock; runtime/ThemeHost | Reserva y temas privados con API parcial; PAM/huella no validados | Prueba con usuario mañana; jamás disparar bloqueo desde fixture |
| P2/C, parcial corregido (R8 lotes 3 y 5) | panel/TasksModel, TaskToolTip | Modelo reducido; insignias/progreso Unity y controles multimedia ya portados | Proveedores reales LauncherEntry/MPRIS, grupos y filtros de referencia |
| P2/C, parcial corregido (R8 lote 2) | panel/DigitalClock y applets/calendar | Rueda de zonas y lista de relojes del calendario portadas; falta página de zonas y agenda | Configuración original y plugins de agenda disponibles sin inventar datos |
| P2/C | applets/BluetoothApplet | Port reducido; OBEX/asistente avanzado ausentes | Evaluar Bluedevil existente/proveedor común; no iniciar otro dueño |
| P2/C | applets/notifications | Sin respuesta en línea, jobs KIO ni programación DND | Ver capacidades del servidor BWM y mapear vista original sólo si efectivas |
| P2/C | applets/clipboard | cliphist con delegados originales, sin edición/QR/miniaturas | Reutilizar proveedor común, sin lanzar Klipper adicional |
| P2/C | applets/power | UPower/brillo compartidos, sin inhibiciones/perfiles PowerDevil | Evaluar API compatible sin duplicar inhibidores/servicios |
| P2/M | kickoff/KickoffWindow y menus | Menús PC3 sustituyen QMenu por layer-shell; correcciones visuales recientes | Mantener anclaje/clip/highlights; teclado, accesibilidad y RTL |
| P2/M | switcher/OSD/runtime | Ports F12 con API de temas privada parcial | Verificar selección del tema, escala, modo oscuro/claro y cancelación |
| P1/M | transición skins; bwm_windows.float_in_place | Excluye especiales/minimizadas, pero no matriz real de Magic | Ciclo tres skins, conservar dirección+PID, geometría y reproducción |

## Contratos de extensiones

Una página config de plasmoide no se obtiene de un estilo SVG. La fuente original
`desktoppackage/contents/configuration/AppletConfiguration.qml` usa `configDialog.configModel`,
`Plasmoid.configuration` (KConfigPropertyMap), propiedades `cfg_*`, `configurationChanged` y
`unsavedChangesChanged`. `PanelConfiguration.qml` exige `panelConfiguration` y el objeto panel,
con offset/min/max length y `org.kde.plasma.shell.panel`. Copiar sólo los controles no implementa
esas APIs. R4 debe demostrar esos contratos antes de R5.

KCMUtils instalado documenta KCModule (QWidget) y KQuickConfigModule con metadata y factory
K_PLUGIN_CLASS_WITH_JSON; namespace `plasma/kcms/systemsettings`. El host real admite ambos;
la limitación QWidget del port actual no es una limitación de System Settings.

## Referencia reproducible y aceptación visual

No hay sesión Plasma de referencia accesible. Preparar en sesión/VM aislada Plasma **6.7.5**,
Breeze predeterminado, Noto Sans 10, mismo desktoptheme y esquema, idioma, tamaño del panel y
escala lógica. Guardar configuración de referencia y versiones (sin datos privados). No
iniciar KWin ni plasmashell sobre la sesión del usuario para obtenerla.

Escenarios: cuatro bordes/panel flotante o pegado, tarea activa/inactiva, popup, modo edición,
ventana SSD/CSD, maximizar/minimizar, escritorios y transiciones. Medir geometría lógica y DPR;
comparar imágenes sobre fondo controlado y perfiles alpha para sombras. Animaciones: vídeo
con timestamps, escala/opacidad/posición por frame, misma frecuencia, factor 0/1/2, cancelación.
Tolerancias explícitas por frame y por píxel; sin referencia, estado **pendiente**, no igualdad.

## Orden confirmado

R1 puede corregir fallos puros y dejar validación gráfica pendiente; R2 puede construir/probar
KCM en plataforma offscreen y bus privado. No activar globalmente el nuevo lanzador hasta
preservar opciones BWM y validar descubrimiento. R3–R5 requieren cerrar esos contratos.
La recuperación y estabilidad del compositor pasan delante de todo port nuevo. R6 tiene un
veto de sombras identificado, **que se mantiene como contención**. No repetir su retirada sin
validación aislada de captura/render. Las miniaturas Breeze permanecen desactivadas temporalmente.


## Profundización de R0: contratos contrastados y ruta de implementación

Las referencias `D` y `W` siguientes son los commits desktop/workspace de §Entorno; `L` es
la fuente libplasma 6.7.5 extraída localmente, sin commit Git verificado. Su huella está en el
manifiesto. Se han leído las declaraciones y rutas señaladas; las referencias KWin sin fuente
local disponible se marcan como pendientes de cotejo. No se usa documentación de master para
atribuir comportamiento a 6.7.5.

| Área / hueco | Fuente original concreta y contrato | Diferencia observada en BWM | Fase, dependencias y aceptación |
| :--- | :--- | :--- | :--- |
| Edición general | D `desktoppackage/contents/views/DesktopEditMode.qml`; D `configuration/PanelConfiguration.qml`, propiedad requerida panelConfiguration | DesktopMenu omite edición del escritorio; PanelEditor es formulario propio | R4→R5: anfitrión y estado de edición por containment; abrir/cerrar desde escritorio y panel, teclado, foco y región de entrada restituidos |
| Containments/varios paneles | L `plasma/corona.h`: createContainment, loadLayout/saveLayout y screenGeometry; `plasma/containment.h`: createApplet | PanelState.configuration es único Config.options.bar.plasma; panels[screen] sólo guarda geometría | R4: identidad persistente por panel, migración y reservas reales; dos paneles editables de forma independiente y reapertura intacta |
| Anfitrión externo | L `plasmaquick/appletquickitem.h`: representaciones compact/full, expanded, badgeText, plasmoid; L `examples/shell/customcorona.cpp` | AppletHost.qml emula propiedades, no crea Plasma::Applet. Hay un ejemplo upstream de anfitrión propio: no hay base para declarar imposible toda extensión | R4: evaluar Corona propia/auxiliar fuera del compositor. Gate: widget externo no conocido de antemano con representaciones y acciones correctas |
| Opciones por instancia | L `plasma/applet.h`: configScheme/configuration; D `configuration/AppletConfiguration.qml`: configDialog.configModel, cfg_*, writeConfig y unsavedChanges | AppletHost.configuration es un QtObject reducido, internalActions manuales; sin esquema cargado por paquete | R4: backend nativo de configuración, Aplicar/Cancelar/Predeterminados y dos instancias con valores distintos |
| Explorador de widgets | D `explorer/WidgetExplorer.qml` y AppletDelegate.qml; paquetes KPackage | Editor enumera seis ids internos fijos | R4→R5: descubrimiento por rutas XDG y KPackage, catálogo y proveedor KNS correctos; instalar complemento de prueba aislado y mostrar sus opciones sin editar BWM |
| Kickoff | D `applets/kickoff/main.xml` y `main.qml`; BWM `kickoff/Plasmoid.qml` configureAction | Acción Configurar desactivada explícitamente; favoritos usan id BWM común en KActivities, no identidad de instancia de containment | R4/R8: activar configuración original y evaluar migración de identidad sin perder favoritos; dos Kickoff independientes con configuración persistente |
| Preferencias | KCMUtils instalado `kcmodule.h`/`kquickconfigmodule.h`: factory y metadatos; D/W no sustituyen el host de systemsettings | Host actual qs -p, catálogo manual; prototipo R2 sólo aporta luz nocturna nativa | R2: migrar cada página común a KCM o adaptador original, alias y entradas .desktop; host real sin perder opciones |
| Aplicación efectiva | BWM bridge reconcile → hyprctl reload; authority de cada clave, no basta KCM visible | KCM que depende de KWin puede escribir ajustes sin efecto. No se ha validado todo el puente | R3: inventario control→archivo→API→efecto y pruebas de ida/vuelta. No asumir org.kde.KWin ni duplicar servicios |
| Animaciones | W/D QML usa métricas/Units de KDE; KWin effects y defaults de fábrica: fuente exacta pendiente de cotejo | MD3/pop-in en animations.lua; kwin.lua replica valores. appearance carga base antes que kwin | R7: medir efecto, duración y curva; probar 0→1→2→1 y QML/compositor. No marcar retorno a 1 roto sólo por la condición de kwin.lua |
| Sombras | KDecoration3 DecorationShadow e innerShadowRect; protocolo BWM Shadow con DPR/stride/padding. Algoritmo KWin scene/shadowitem citado en port, no cotejado de nuevo | CBreezeShadow respeta noShadow; veto restaurado tras incidente. El crash real está en captura, no en una pila de Shadow | R6: fuente KWin/Breeze fijada antes de portar; captura, ciclo de vida, alpha/DPR, focos y CSD sin sombra duplicada |
| Tareas | D `applets/taskmanager/qml/Task.qml` y modelos libtaskmanager de W | TasksModel agrupa toplevels comunes; no adapta LauncherEntry. TaskToolTip sin MPRIS y capturas suspendidas | R8 tras estabilidad: progreso/insignias y multimedia con datos reales; grupos, filtros, foco y arrastre. Restituir miniaturas sólo después del gate de captura |
| Reloj/calendario | W `applets/digital-clock/DigitalClock.qml`: onWheel y wheelChangesTimezone; CalendarView y plugin de configuración | BWM conserva clockConfig.wheelChangesTimezone, pero su representación compacta no tiene onWheel; ajustes y agenda incompletos | R4/R8: páginas originales, rueda y zonas horarias disponibles; distinguir UTC/locale/12h de configuración compartida de hora BWM |
| Bandeja | W `applets/systemtray/qml/` y L contratos de applet | TrayState mantiene popup único y SystemTray incluye ids propios; representación correcta no equivale a host de cualquier applet | R4/R8: acciones SNI, atención, ocultos y configuración original; un solo watcher, popup correcto por panel |
| Avisos | W `applets/notifications/components/ActionContainer.qml`; BWM conserva señales de reply/jobs pero el proveedor no anuncia ese soporte | ActionContainer adaptado declara explícitamente que no ofrece inline reply; señales sin proveedor no cuentan como funcionalidad | R8: ampliar proveedor común antes que UI; reply real/KIO si implementables, sin segundo NotificationManager.Server |
| Bluetooth | Fuente Bluedevil 6.7.5 citada por port; el árbol completo no se revalidó en esta pasada | BluetoothApplet usa backend común y Timer 30 s; faltan OBEX/asistente nativo | R8: fijar fuente antes de completar; emparejamiento/transferencia bajo intervención, no encender radios para auditar. Revisar ownership y parada de discovery iniciado aquí |
| Red/audio | QML original plasma-nm/plasma-pa adaptado, fuentes completas no revalidadas ahora | Modelo original más sustituciones de agente/menú; abrir vista no demuestra secretos y cambio de perfil/ruta | R8: verificar proveedor existente antes de KCM; autenticación, perfil y menús con fixture primero; sin duplicar agente de secretos |
| Energía | Fuente PowerDevil 6.7.5 referenciada por port; BWM PowerApplet BatteryItem/BrightnessItem | Wrapper sólo batería y brillo; no perfiles/inhibiciones del servicio original | R3/R8: conservar BwmIdle y proveedores comunes, mapear capacidades reales. Deshabilitar controles sin efecto, no iniciar PowerDevil por semejanza visual |
| Portapapeles | W `klipper/declarative/qml` | ClipboardApplet usa cliphist; no Klipper ni capacidades de imágenes/QR equivalentes | R8: extender proveedor común si procede; historial, selección y privacidad verificables sin leer el portapapeles real durante pruebas |
| Menús/salida | W `containmentactions/contextmenu/root.cpp`; D acciones de containments. BWM DesktopMenu/PanelMenu/WindowMenu | DesktopMenu excluye explícitamente widgets/edición. Salida llama BWM, no una sesión Plasma completa | R5/R8: mismas acciones cuando backend exista. Recuperación/logout debe funcionar sin depender de servicios Plasma; no probar cierre de sesión durante auditoría |
| OSD/temas privados | W OSD y BWM InterfaceTheme → interface-theme.py; ThemeHost con motor separado | Contrato adaptado sólo cubre APIs seleccionadas; cache/loader no certifican todos los temas descargados | R8: matriz de capacidades y fallback explícito, volumen/brillo y monitor/escala. No certificar un tema global a partir de sólo colores/SVG |
| Bloqueo | KScreenLocker/temas y BWM LockTheme → ThemeHost; contexto PAM común | Authenticator aislado del tema, Qt.quit no desbloquea; UI sola no verifica PAM/huella | R9 con usuario: foco, contraseña, cancelación y bloqueo real. Ninguna llamada PAM/bloqueo en R0 |
| Accesibilidad/idioma | D QML de configuración, catálogos KDE; BWM SettingsI18n/MenuI18n | Parte usa KI18n, PanelEditor contiene textos castellanos fijos y KCM prototipo aún sin traducción completa; no ensayo lector/RTL | R5/R8: dominios originales, orden Tab/nombres accesibles, RTL y lector. Exigir interacción, no sólo presencia de strings |
| Transición/estados | BWM bwm_windows/transition, kwin_rules live updater | Exclusiones de especiales presentes; dock Retro aún restaura minimizadas en normal actual | R1 antes de otros ports: captura de estado por PID/generación, matrices visible/oculto y tres skins; no cerrar apps ni alterar reproducción |

Las rutas dentro de D en la tabla son relativas a plasma-desktop: configuration/explorer son
subcarpetas de `desktoppackage/contents/`. Las rutas de taskmanager/kickoff se comprobaron en la etiqueta local; no coinciden con las
rutas package/contents citadas en documentación de otras versiones.
Los contratos libplasma dan una vía arquitectónica; **no constituyen una prueba de concepto
funcional del host externo**. Esa demostración pertenece a R4.

## Servicios, instalación y estado vivo

| Recurso | Instalado/configurado inspeccionable | Estado vivo en esta auditoría |
| :--- | :--- | :--- |
| Hyprland/breezebars | Binario del plugin fijado por SHA en manifiesto; fuentes y reglas inspeccionadas | No verificable: socket rechazado. No confundir archivo con plugin cargado |
| System Settings | 6.7.5, KCM original y prototipo BWM detectados en revisión previa | No se abre la ventana ni se escribe configuración en R0 |
| Quickshell | 0.3.2; rutas de panel/servicios inspeccionadas | Número de instancias y logs actuales no verificados |
| Notifications/SNI/polkit | Autoridad prevista en código y manifiestos | Propietarios D-Bus no verificables; busctl denegado |
| Red/Bluetooth/audio/energía | Adaptadores/proveedores identificados en código | No se afirma conexión, reproducción, inhibición o autenticación probadas |
| Configuración/atajos del usuario | No se edita ni se incorpora al informe | Atajos efectivos y overrides activos sin inspección por IPC |

No instalar paquetes para terminar R0. Para las fuentes que faltan, obtener versión/commit en
scratch en la fase que las use, sin mezclar una rama nueva con 6.7.5. Los paquetes y ejemplos
instalados se han leído, no ejecutado como escritorios o agentes.

## Prioridades revisadas después del incidente

1. **P0 estabilidad/recuperación:** crash de captura de ventana con acceso nulo. Mantener
   contención; reproducir en compositor aislado y comprobar cliente/ventana/monitor, estados
   oculto/minimizado/especial/cierre y capturas del fallback. No atribuirlo a sombras sin evidencia.
2. **P0 semántica común:** terminar R1 con el material existente, especialmente restauración
   especial desde Retro, Alt+S y activación por tareas/Alt+Tab en ambos monitores.
3. **P1 host nativo:** completar R2 por módulos antes de tocar el lanzador global; R3 cobertura
   de ajustes. El prototipo existente se reutiliza, no es prueba de migración completa.
4. **P1 extensibilidad antes de UI:** R4 demuestra contratos reales por instancia; R5 porta
   editor/menús/explorador originales. No copiar controles antes de disponer del backend.
5. **P1 profundidad/movimiento:** R6 sólo tras gate de estabilidad de captura/render. R7 con
   fuentes de efectos y referencia temporal; conservar las prioridades anteriores.
6. **P2 paridad cotidiana:** R8 sobre proveedores compartidos; R9 integración y pruebas físicas.

## Criterio de salida de R0

Inventario, fuentes disponibles, limitaciones vivas, procedimiento de referencia y siguientes
prompts quedan entregados. Se usa la alternativa prevista en el propio prompt R0 cuando no
hay sesión de referencia: **preparar procedimiento y marcar mediciones pendientes**. No se
exige ejecutar una sesión Plasma encima de la sesión actual para llamar concluida la auditoría.
La implementación R1/R2, una comparación visual y la resolución del crash no forman parte
completada de R0. No se cambia runtime, activa skin ni ejecuta nuevo port en esta pasada.


Actualización posterior R1 (mismo día): el hueco de restauración especial desde el dock Retro
ya tiene integración con el controlador común y regresiones aisladas. No se ha validado en
sesión. El inventario anterior conserva el diagnóstico de R0; estado operativo y límites en
BREEZE_R1_RESULTS.md. Las huellas de R0 permanecen congeladas como evidencia de aquella revisión.
