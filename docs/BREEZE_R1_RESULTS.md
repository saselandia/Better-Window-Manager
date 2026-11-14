# R1 — Magic, activación y minimizado (implementación parcial validada sin compositor)

2026-11-12. No se da por reproducido ni cerrado el fallo visual original de Alt+S.

## Cambios

- Atajos fuente y generados ya usan magic/special:magic: no se cambiaron ni se regeneraron.
- Activación común en `bwm_windows.focus_body_lua`: consulta el workspace vivo de la ventana,
  enfoca primero el especial y después ventana/orden. Usa focus idempotente, no toggle, y no
  mueve la ventana a un escritorio normal. No activa el almacenamiento de minimizadas.
- `kwin-window.py focus`, usado por las tareas Breeze, delega a esa política común.
- `bwm-focus.py` restaura minimizadas antes de enfocar y comprueba dirección+PID al consultar
  y de nuevo en Lua. Alt+Tab guarda PID además de dirección para su reenfoque retardado.
- Alt+Tab admite Magic si está visible en algún monitor y lo excluye si está oculto. Se
  conservan sus políticas por skin para escritorios normales y minimizadas.
- Minimizar desde un especial conserva **su nombre**, no un ID negativo efímero. Se usa una
  etiqueta interna específica para origen especial, UTF-8 codificado en hex; las etiquetas
  numéricas de Omarchy y las heredadas normales siguen interpretándose igual. Sólo se borran
  etiquetas de minimizado. Restaurar devuelve la ventana al especial original, incluso si
  quedó vacío y fue destruido por el compositor.
- La caché de geometría comprueba PID/inicio del proceso para evitar aplicar la geometría de
  una ventana anterior que reutilizó la dirección. Registros antiguos sin identidad no se usan.
- `toggle_win` y `toggle-app` del controlador común usan la misma activación, conservando cursor.

## Evidencia

- 6 pruebas `test_minimize.py`: destinos normales/heredados, Magic y especial sin nombre,
  nombres Unicode, etiqueta corrupta, almacenamiento reservado, limpieza y caché con PID antiguo.
- 6 pruebas `test_window_activation.py`: ejecución del Lua real en fixture de dispatchers,
  orden especial→foco→elevación, repetición idempotente, rechazo de PID, almacenamiento invisible,
  CLI y **JavaScript original de Alt+Tab ejecutado en QtTest offscreen**, visible/oculto en dos skins.
- 13 pruebas `test_kwin_window.py` pasan. Sintaxis Python correcta. qmllint ejecutado con
  avisos de imports virtuales qs/tipos dinámicos; no sustituye una carga de shell real.
- La prueba Qt detectó que `flatMap` no existe en este motor QML; se usa map+concat y pasa.

## Límites y pendientes para mañana

1. En ventanas desechables, Alt+Shift+S → Alt+S; varias pulsaciones, ambos monitores y foco.
2. Activar Magic oculto desde una tarea Breeze y comprobar que aparece delante y conserva
   workspace. Alt+Tab incluye Magic visible, no el oculto; el cursor se conserva al activar.
3. Minimizar/restaurar una ventana **nueva** desde Magic; no debe salir al escritorio normal.
   No es posible reconstruir con certeza el origen de minimizadas antiguas cuya etiqueta sólo
   guardaba el ID negativo y cuyo workspace ya desapareció. No se migraron ventanas existentes.
4. Mostrar escritorio, fullscreen y cambio default→Breeze→Retro→Breeze con Magic visible/oculto.
5. La integración del dock Retro ya está implementada en la continuación siguiente. Falta
   verificar en sesión real el modelo completo del dock y las dos políticas de restauración.
6. Inspeccionar atajos/reglas efectivos y plugin vivo. No se pudo leer configuración de usuario
   en ejecución ni ver si interviene otra regla/atajo. No se modificó texto de usuario.

No se cerró sesión, cambió de skin, movió ventanas del usuario ni reinició Quickshell.
Rollback de código: revisar diff de los cuatro scripts comunes/kwin-window y AltTab, y revertir
sólo esos hunks, no otros cambios de la rama. No hace falta tocar ni descargar ningún plugin.


## Continuación R1: dock Retro y protección del destino (2026-11-12)

### Cambios implementados

- Dock.qml toma el PID de lastIpcObject y llama al controlador común con argumentos separados;
  no usa comandos de shell concatenados ni foco sin identidad cuando faltan datos IPC.
- Nueva opción `bwm-focus.py --restore-on-current`, explícita para la política del dock:
  una minimizada de origen normal vuelve al workspace actual (Omarchy), una de origen
  especial vuelve a su **nombre original**, incluso si no es Magic. No renombra otros especiales.
- `restore_win(..., on_current_workspace=True)` conserva geometría de especiales con su
  identidad; para normales restauradas en otro escritorio no reaplica coordenadas del monitor
  anterior. La política común por defecto conserva destino/geometría de origen como antes.
- La restauración normal del dock conserva no_anim temporal. Su limpieza pasa por un timer
  del compositor, con comprobación fresca de dirección+PID, en vez de un shell que duerme.
- CLI rechaza PID/dirección inválidos y respuestas IPC que no sean una lista de clientes.
- `min DIRECCIÓN` y `toggle DIRECCIÓN` ya no usan la ventana activa como alternativa si la
  dirección explícita desapareció. Sin argumento siguen usando la activa.
- No se cambiaron Alt+S ni Alt+Shift+S: los datos/generador siguen apuntando al mismo Magic.
  El Lua de usuario en ~/.config/bwm/user/hyprland.lua no existe en la inspección actual.
  No se escribió configuración de usuario ni se modificaron archivos de paleta generados.

### Evidencia nueva

`tests/test_special_workspace_restore.py`: 10 pruebas. Ejecutan el Lua generado con un
simulador de dispatchers con estado (movimiento cambia el workspace vivo) y la función QML
bringForward original en QtTest offscreen, sustituyendo sólo execDetached por registro.
Cubren destino normal actual/original, Magic/otro especial/sin nombre, geometría, PID antiguo,
limpieza diferida, delegación de CLI, IPC inválido y destino cerrado sin fallback a otra ventana.
No ejecutan protocolo de captura ni crean ventanas en la sesión del usuario.

Se repiten 7 pruebas de activación/filtro, 6 de minimizado, 13 de ventanas KWin y 9 de
transición de skins. Todas pasan. Sintaxis Python y diff correctos; qmllint del dock sin errores
de sintaxis, con avisos de imports virtuales/tipos dinámicos que no sustituyen carga real.
Pasada general offline final: **388 casos, 70 omitidos, sin fallos** (318 ejecutados).
Se excluyeron explícitamente 12 integraciones del decorador que requieren sockets rechazados
por el sandbox; no se presentan como aprobadas.

### Contrato contrastado y límites

Se consultó la implementación de Hyprland 0.56.2 distribuida en el espejo de código:
[LuaBindingsDispatchers.cpp](https://codegraph.jelmer.uk/hyprland/0.56.2%2Bds-2/src/config/lua/bindings/LuaBindingsDispatchers.cpp)
y [ConfigActions.cpp](https://codegraph.jelmer.uk/hyprland/0.56.2%2Bds-2/src/config/shared/actions/ConfigActions.cpp).
La ruta focus(workspace) delega a changeWorkspace; la rama especial usa setSpecialWorkspace.
Esto apoya la separación entre revelar y toggle. No demuestra la geometría/foco efectivos del
proceso vivo ni que el binario Gentoo sea idéntico al paquete del espejo. Los símbolos del
binario instalado y la propiedad lastIpcObject de Quickshell también se inspeccionaron.

hyprctl sigue rechazado por sandbox. Se ven tres archivos de log y no hay un crash report
más reciente que hyprlandCrashReport32.txt; esos archivos **no demuestran recuperación o
estabilidad actual**. No se intentó otro compositor o una captura para provocarlo.

**R1 sigue pendiente de aceptación en sesión real**, no de la implementación del antiguo
hueco del dock. Falta Alt+S visible/oculto, dos monitores, foco/entrada, fullscreen, Mostrar
escritorio y ciclo de skins. La ruta de minimizar nativa de Retro sigue restringida a workspaces
normales flotantes según Omarchy: esta continuación no amplía ese comportamiento; sí restaura
correctamente desde el dock una minimizada con origen especial guardado por el controlador común.
No se pueden reconstruir nombres de especiales perdidos por versiones antiguas.

El dock empleará el cambio cuando se cargue el QML actualizado; no se ha forzado recarga,
reinicio de shell ni cambio de skin. No se han reactivado capturas/sombras ni tocado plugins.
Sin instalación, commit o push. Las huellas R0 son una referencia histórica: los scripts/dock
modificados por esta fase naturalmente difieren de aquel snapshot.

Rollback de esta continuación: revisar únicamente el diff del dock, la opción restore-on-current
y sus ramas de restauración común. No hacer git reset ni descartar el resto del trabajo previo.


## Intento de validación real autorizado por el usuario (2026-11-12)

El usuario autoriza pruebas completas y reactivar el compositor si hace falta. Se intentaron
consultas IPC y una escalación **sólo de lectura** (`hyprctl -j version`) antes de modificar
la sesión. La política de esta tarea rechazó require_escalated porque sandbox_approval=false;
no llegó a ejecutarse la consulta fuera del sandbox. No es evidencia de que Hyprland esté en
modo seguro ni de que haya que reiniciarlo. Reiniciar el compositor no cambia esta política.
No se usó un segundo intérprete, terminal o proceso persistente para eludir la restricción.

Preparado `config/hypr/scripts/bwm-r1-validate.py`, ejecutable por el usuario en una terminal
de la sesión. Sin --run sólo consulta acceso. Con --run crea dos kitty desechables en un
workspace libre, prueba el dispatcher usado por Alt+S (no inyecta la tecla física), activación
repetida, minimizar/restaurar desde Magic con política del dock y rechazo de PID. Limpia
ventanas por identidad y restaura foco/workspaces iniciales. Rechaza Magic ocupado o cualquier
especial abierto para no usar ventanas personales como fixtures. No activa capturas, cambia
skin ni reinicia compositor. No prueba la matriz visual completa ni hace clic en el dock real.

```bash
python3 /mnt/HDD1TB/Projects/hyprland-de/config/hypr/scripts/bwm-r1-validate.py --run
```

No usar el teclado/ratón durante el ensayo. Informe en `/tmp/bwm-r1-session-results.json`.
Si se rechaza por Magic ocupado, el ensayo se detiene sin trasladar esas ventanas. El informe
siempre distingue prueba de estado y verificación visual; nunca marca visual_verified=true.

**Ejecutado aquí sólo el preflight:** IPC denegado, cero checks de sesión aprobados, cero
acciones de fixture y compositor no reiniciado. Tres pruebas de seguridad pasan con mocks:
IPC denegado no lanza/mueve nada, Magic ocupado no se usa y preflight read-only no crea fixtures.
No presentar el script preparado ni esos tests como una prueba visual ejecutada.


## Validación real ejecutada por el usuario: aprobada (2026-11-12)

El usuario ejecutó bwm-r1-validate.py --run desde su terminal y compartió la salida.
Se leyó además el mismo informe en /tmp/bwm-r1-session-results.json; se conserva sin datos
personales en BREEZE_R1_SESSION_RESULTS.json. Hyprland informa **0.56.2**.

| Comprobación de sesión | Resultado |
| :--- | :--- |
| Acceso IPC desde la terminal del usuario | OK |
| Enviar fixture al special:magic canónico | OK |
| Mostrar/ocultar Magic mediante dispatcher de Alt+S | OK |
| Dos activaciones comunes conservan Magic abierto y enfocan el fixture | OK |
| Minimizar y restaurar con política de dock conserva origen especial | OK |
| PID incorrecto rechazado sin mover el fixture | OK |
| Limpieza | Sin errores reportados |

Esta evidencia reemplaza «cero checks de sesión aprobados» del intento anterior: aquella
frase describe sólo la ejecución bloqueada del asistente. No se ha obtenido acceso directo
al compositor desde el sandbox. No se reinició el compositor para esta prueba.

**Pasa el bloque principal de R1 en el compositor real.** No equivale a cerrar toda la fase:
visual_verified sigue false. Faltan pulsación física de Alt+S, clic real del dock/panel, ambos
monitores, fullscreen, Mostrar escritorio y ciclo de las tres skins. La prueba usó la política
de backend del dock, no el modelo QML completo del dock ni un clic en él. La ausencia de errores
de cleanup no mide por sí sola toda la geometría/foco anterior y posterior de las apps del usuario.
No se reactivan sombras/miniaturas a partir de este resultado ni se declara resuelto el crash.


## Continuación: matriz e interacción por etapas (preparada, no ejecutada en sesión)

El smoke real anterior se conserva intacto en BREEZE_R1_SESSION_RESULTS.json. Se amplía el
validador con dos opciones explícitas: --matrix cambia de skin y recorre cada monitor por
descripción; --interactive pide observaciones reales y guarda respuestas por skin.

```bash
python3 /mnt/HDD1TB/Projects/hyprland-de/config/hypr/scripts/bwm-r1-validate.py --run --matrix --interactive --report /tmp/bwm-r1-matrix-results.json
```

La prueba cambia entre default/Breeze/Retro, activa Magic en cada monitor, verifica foco y
transiciones con el especial abierto/cerrado, y devuelve la skin original. Compara identidad
(dirección/PID/generación de proceso) y workspace de las ventanas preexistentes. Se detiene
si desaparece una o cambia de workspace. No certifica geometría exacta, audio o repintado.
Se niega a hacer la matriz si breezebars no está cargado: no hace plugin load/unload ni reinicia
compositor. Sigue rechazando Magic ocupado/especial abierto al inicio. Los fixtures duran
hasta 30 minutos para permitir las observaciones; la limpieza cierra sólo las identidades propias.

En modo interactivo se restaura el foco de la terminal antes de cada bloque de una skin.
Responder s/n/Enter registra confirmado por usuario/fallo/pendiente; ningún Enter cuenta como
éxito. No se cambia de skin manualmente durante cada bloque; si cambia, la observación queda
pendiente. Usar sólo las ventanas BWM R1 test. Mostrar escritorio afecta temporalmente a las
apps abiertas, como avisa la pregunta; se puede omitir con Enter. La captura del render no se
activa para estas observaciones. Las respuestas no son comparaciones automáticas de píxeles.

**Alt+Tab físico está limitado a Breeze mientras siga abierto el incidente de capturas.** En
las otras skins su observación se marca pendiente sin sugerir activar esa ruta de riesgo. Por
eso una matriz automatizada aprobada no cierra R1 completa ni el incidente. visual_verified
sólo puede ser true si están confirmadas todas las observaciones de las tres skins; una sola
skin confirmada se etiqueta por separado. Las capturas y sombras siguen contenidas.

Pruebas aisladas actuales del validador: 9 OK. Incluyen IPC bloqueado, Magic ocupado, plugin
no cargado, generación/PID reutilizados, cambios de workspace, respuestas manuales omitidas
y un simulador con estado que recorre tres skins/dos monitores y devuelve la original. También
pasan las 10 pruebas de restauración especial. Sintaxis y diff correctos. La matriz nueva no
se ha podido ejecutar aquí y no se presenta como aprobada; el acceso directo sigue restringido.
No se forzó ninguna transición del escritorio del usuario desde esta ejecución.


## Primer intento real de matriz: fallo al seleccionar monitor (2026-11-12)

El usuario sólo vio «Comprobando skin: default». Se encontró el informe escrito por el
validador: checks iniciales aprobados, matrix vacío, error «Matrix activation focused the wrong
monitor» y cleanup_errors vacío. Conservado en BREEZE_R1_MATRIX_ATTEMPT_01.json. No hay un
crash report nuevo respecto a hyprlandCrashReport32.txt. No se puede concluir un crash a partir
de la ausencia del JSON en la salida visible de la terminal.

Se corrige la preparación del ensayo, no la política de foco del escritorio: antes de enfocar
cada monitor se coloca el puntero en su centro lógico (escala/transformación incluidas) y se
espera la convergencia del foco. Antes sólo se seleccionaba el monitor por software, lo que
puede competir con seguimiento del ratón/activación y vuelta del cursor a su posición previa.
Es una hipótesis compatible con el fallo, **no su causa confirmada en el equipo real**.

El cursor original se guarda antes de empezar y se restaura en cleanup. Si vuelve a fallar,
el reporte incluye monitor solicitado, monitores enfocados/especial activo y monitor del
fixture, sin títulos de ventanas personales. Añadido aviso final de error por stderr con ruta
al reporte, además del JSON.

Las 9 pruebas aisladas del validador pasan. El simulador ahora devuelve el foco al monitor
del puntero durante activación: con movimiento explícito recorre 3 skins/2 monitores; al
suprimir ese movimiento como control negativo reproduce el fallo de foco y guarda diagnóstico.
Esto valida el ajuste de preparación, no acredita que el intento real corregido haya pasado.
El usuario puede repetir el mismo comando --run --matrix --interactive con el reporte separado.
No se cambió compositor, plugin, política de ratón, skin, miniaturas ni sombras desde aquí.
