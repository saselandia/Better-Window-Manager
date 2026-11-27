# Breeze III — T4: disposición, bienvenida y salida del tema global

Fecha: 2026-11-26. Plan: [BREEZE_PLAN_V3.md](BREEZE_PLAN_V3.md). Implementación instalada;
pruebas aisladas y apertura/cancelación diaria comprobadas según el inventario inferior.
La bienvenida del nuevo login queda confirmada por el usuario el 2026-11-27: apareció y se
cerró correctamente. La sustitución de una disposición en pantallas físicas sigue pendiente. No se ha aplicado un layout de prueba al escritorio diario.

## Disposición original y recuperación

`LookAndFeelLayout` publica `org.kde.plasmashell`, objeto `/PlasmaShell`, interfaz
`org.kde.PlasmaShell`, con **`immutable()` y `loadLookAndFeelDefaultLayout(string)`**. Es el
contrato que utiliza `KLookAndFeelManager` 6.7.5 al aplicar la disposición. No publica
`evaluateScript`, ni pretende ser el plasmashell completo; no desplaza un dueño existente.

La Corona guarda su estado antes de preparar el cambio. `ProfileStore::checkpointSession`
copia los cuatro archivos nativos (`appletsrc`, `plasmashellrc`, `assignments.json`,
`desktop-assignments.json`) a una generación privada en
`$XDG_STATE_HOME/bwm/plasma/session-profiles/<uuid>/`. Otra generación ejecuta el script
original en una Corona desechable, con escritorios por pantalla y paneles nativos. No se
sobrescribe el archivo abierto por la Corona diaria. Un error JS, script interrumpido o
configuración de panel inválida rechaza la operación antes de cerrar el host.

El supervisor finito `session-ui.py replace-layout` espera el cierre del proceso anterior,
valida inventario/hashes y selecciona la generación mediante
`$XDG_CONFIG_HOME/bwm-plasma-host/active-session.json`. Arranca el host y exige ready,
registro de la interfaz, escritorios, paneles visibles y ausencia de error de runtime.
Si falla, cierra ese host, selecciona el checkpoint anterior y lo vuelve a arrancar.
`last-layout.json` conserva fase, error y resultado de la recuperación. Las generaciones
activas son configuración nativa mutable: el manifiesto sella el checkpoint, no impide
guardar después cambios normales del usuario. Se conservan los checkpoints para recuperar.

Con edición del escritorio/panel o configuración de cualquier widget abierta, la petición
se rechaza. Las asignaciones persistentes usan descripción del monitor; una salida virtual
sin EDID no se convierte en una asignación permanente por nombre de conector.

### API de scripts medida

Se amplía el `LayoutTemplateRunner` existente, no se traduce el tema a un formato BWM:

- API 1 (`getApiVersion(1)`), `Panel`, `panelIds`, `panelById`, `screenGeometry`, `gridUnit`,
  `languageId`, `print`, `loadTemplate` y plantillas `Plasma/LayoutTemplate`.
- Escritorios de la única actividad de BWM: `currentActivity`, `activities`,
  `desktopsForActivity`, `desktopById`; `wallpaperPlugin`, `addWidget`,
  `currentConfigGroup`, `readConfig` y `writeConfig` en configuración nativa.
- Panel: borde, grosor, alineación, longitud, desplazamiento, ocultación, flotación,
  opacidad opaca/translúcida, orden y configuración de applets.
- `loadSerializedLayout`, formato **1** de Plasma, grupos codificados y medidas en `gridUnit`.

Límite de script 1.048.576 unidades UTF-16, interrupción JS a los 3 s y anidamiento máximo 16. Esto acota errores
como bucles infinitos; **no es un sandbox para código no confiable**. Las funciones ausentes
fallan. No se implementan `ConfigFile`, ejecución de programas, instalación de recursos,
gestión de Actividades, asignación arbitraria de pantalla, geometría libre de widgets de
escritorio ni opacidad adaptativa. No se garantiza un tema que dependa de esas operaciones;
la compatibilidad widget por widget corresponde a T7.

## Bienvenida

`autostart.sh` llama a `session-ui.py splash-start` una vez por inicio de Hyprland, sólo en
Breeze. Lee `ksplashrc` con la cascada KDE; `Engine=None` o `Theme=None` lo desactiva. Ejecuta
el **`ksplashqml --nofork <tema>` original**, con los recursos instalados sin copiarlos.
Al aparecer el host ready, completar un cambio de skin o agotar 20 s, completa las etapas
de KSplash, comprobando el token del proceso lanzado y que el dueño D-Bus conserve su PID. No termina un KSplash
ajeno. Cambiar de skin durante una sesión no vuelve a mostrar esta bienvenida.

## Salida

El greeter original requiere el backend de sesión de KDE y deja de arrancar si existe
`org.kde.Shutdown`; no resulta apropiado bajo Hyprland. `SessionUi` reutiliza el **ThemeHost**
de `src/bwm-kcmhost`: cada pantalla aloja el `contents/logout/Logout.qml` original del tema
en un motor separado, sobre layer-shell. Si el paquete no trae salida, utiliza la de Breeze.
Relee la elección de tema al abrir, incluida una modificación externa de `kdeglobals`.

El contrato de contexto/señales procede de `logout-greeter/shutdowndlg.cpp` 6.7.5. Cancelar,
Escape del QML y `Qt.quit()` cierran el diálogo; perder el foco fuera de sus ventanas también.
La cuenta atrás original llama **una sola vez** a `bwm-power <acción> --confirmed`, aunque
se muestre en dos monitores. Las capacidades de energía se consultan a logind. No se ofrecen
actualizaciones sin conexión ni opciones de firmware/cargador desde este diálogo.

El host reclama sin reemplazo los contratos originales `org.kde.LogoutPrompt` (cuatro
métodos prompt) y `org.kde.Shutdown` (logout/logoutAndShutdown/logoutAndReboot), utilizados
por los botones nativos. **`saveSession` no se implementa**: restaurar sesiones queda fuera
del plan. El menú del escritorio, la IPC `session`, los atajos existentes y las peticiones
de apagar/reiniciar/cerrar sesión de `bwm-power` abren esta interfaz en Breeze. La ejecución
sigue en el gestor común. Las otras skins conservan su interfaz.

Sin host nativo, el mismo binario ofrece `--logout-dialog` como auxiliar único con lock y
socket privados. Cierra al abandonar Breeze; no reclama los servicios D-Bus de sesión.
Un tema con QML inválido se rechaza; no se ejecuta por defecto una acción de energía.

## Evidencia

| Prueba | Entorno | Resultado |
| :--- | :--- | :--- |
| Python T4 + T3 + fallback de fondos + manifiestos | XDG temporal, dobles de procesos | **28/28 PASS**; incluye hashes/inventario, éxito y rollback del supervisor, cambio de skin, None y KSplash ajeno, también si aparece durante el arranque |
| Regresiones del gestor del host y cierre común | Dobles de procesos/órdenes | **15 PASS, 1 omitida** (prueba QML optativa del gestor); sin cierre de apps reales |
| CTest completo | `build/bwm-plasma-host-tests`, BUILD_TESTING=ON | **15/15 PASS**, 92,70 s |
| `test-t4-session` | D-Bus/XDG privados, Hyprland anidado, dos salidas a escala 1/1,25 | **8/8 PASS**: scripts Breeze/Sweet/Layan, error y bucle, dueño extranjero, llamada D-Bus original, edición abierta, logout original y Qt.quit separado |
| Cuenta atrás/señales | Sólo ejecutable ficticio de energía | Logout, reboot, shutdown y StandbyState llegan una vez al helper; cancelar no escribe ninguna acción. Ningún apagado/suspensión real |
| Auxiliar sin host | Mismo entorno aislado, BWM_POWER_DRY_RUN=1 | Diálogo Breeze original, segundo proceso no duplica ventanas, cancelación por socket, sin petición de energía |
| KSplash original | Breeze, Sweet, Layan en bus privado | Los tres cargan y terminan con código 0 al completar las etapas |
| Supervisor real | Procesos `--session` desechables | Candidato sin asignación persistente de salida rechazado, checkpoint anterior seleccionado y host ready recuperado. Éxito de activación cubierto con doble de estado, no con pantallas físicas |

Layan: [tienda KDE](https://store.kde.org/p/1325243),
[fuente](https://github.com/vinceliuice/Layan-kde), revisión
`a0b6a4956022276aee33309b2e07d1d0ef3db30c`. Se revisó y probó su script original
`contents/layouts/org.kde.plasma.desktop-layout.js` con `loadSerializedLayout`. No se instala
en el perfil diario ni se incluyen sus recursos en BWM. Su Splash.qml emite
`ReferenceError: bottomRect is not defined` (líneas 88–89 de esa revisión); es una limitación
del recurso original, no se considera validado visualmente. Sweet no trae disposición ni
salida propias: utiliza las rutas originales de respaldo de Breeze.

El runner `check-t4-session.py` retira su compositor, reglas y salida temporal. El gestor
del host comprueba también `XDG_RUNTIME_DIR` en `/proc/<pid>/environ`: una sesión de ensayo
no puede detener el host diario por compartir nombre de ejecutable. Informe generado:
`build/bwm-plasma-host-tests/t4-session-results.json` (no versionado).

## Sesión diaria y pendientes

Binario instalado atómicamente, SHA256
`6854b8b857ea73387ac359689fb16d90341db4ba70d60fc26133b42d372f11cb`. Host ready,
dos escritorios y dos paneles visibles, sin error de runtime; D-Bus introspectado con los
métodos anteriores y notificaciones válidas. Los registros de fondo de las dos pantallas
físicas coinciden con los anteriores al reinicio. No se aplicó ninguna disposición de prueba.
IPC `session open/close` del Quickshell único comprobada: dos ventanas del diálogo original,
cancelación y cero ventanas después; sin accionar botones de energía. Se corrigió el import
QtQuick del proxy y se verificó cargado tras reinicio de mantenimiento del shell.

Pendiente: aplicación elegida por el usuario
desde Preferencias de una disposición completa con sus monitores; revisión visual de los
temas y pruebas físicas de energía por el usuario. T4 no promete compatibilidad universal
de temas de tienda. La medición amplia sigue siendo T7; la aceptación de T5 se sigue en su informe.
