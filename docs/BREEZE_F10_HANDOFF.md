# Traspaso a Claude — continuar F10 de Breeze

Fecha: 2026-11-11. Petición del usuario: continuar las comprobaciones de F10 y resolver el fallo
que encontró al volver a iniciar sesión. Este documento registra observaciones; vuelve a consultar
el estado real antes de actuar. No asumir que la sesión actual conserva los PID o el entorno citados.

## Leer primero

1. AGENTS.md / CLAUDE.md completos, docs/BREEZE_PLAN.md (incluida sección 2), docs/BREEZE_ARCH.md.
2. BWM_CONTEXT.md §2.4 y §148–150: implementación F10, comprobaciones previas y crash.
3. docs/BREEZE_F10_CHECKLIST.md y config/hypr/skins/plasma/scripts/KWIN_RULES.md.

## Prioridad: recuperación y arranque

El usuario autorizó que Codex cerrase sesión para probar el plugin. Se ejecutó bwm-power logout.
Hyprland cayó después de iniciar la nueva sesión; el usuario tuvo que ir a Ctrl+Alt+F3 y ejecutar
start-hyprland. **No repetir automáticamente el cierre ni salir del modo seguro para probar.**
En este incidente la prioridad pasó a investigar el fallo, preservar la sesión recuperada y preparar
la corrección. No se ha probado el arranque completo con la corrección instalada.

Último estado observado:

- Dos Hyprland vivos, **ambos en modo seguro y sin plugins**. PID 780614 en tty1 (SDDM),
  comando Hyprland --watchdog-fd 4 --safe-mode --locked; PID 783349 en tty3 (recuperado),
  comando Hyprland --watchdog-fd 4 --safe-mode.
- Instancias: efb50993780079460b0cbed1363e2166a2de1d9f_1794401421_1820146378 (wayland-1),
  efb50993780079460b0cbed1363e2166a2de1d9f_1794401514_617469003 (wayland-2).
- Ambos son Hyprland 0.56.2, commit efb50993780079460b0cbed1363e2166a2de1d9f.
- El escritorio incompleto es compatible con el modo seguro. Los registros de SDDM consultados
  muestran autenticación y lanzamiento correctos; no demuestran un fallo propio de SDDM.
- Consultar hyprctl instances -j y los comandos de cada PID antes de usar IPC. El entorno de
  una terminal/IA puede apuntar a otra instancia. Fijar HYPRLAND_INSTANCE_SIGNATURE sólo con un
  identificador observado y vivo. No matar una sesión porque parezca duplicada.

### Causa comprobada y arreglo YA instalado

Informes privados locales: ~/.cache/hyprland/hyprlandCrashReport77911.txt y
hyprlandCrashReport782833.txt. Ambos: SIGABRT, plugin breezebars, marco
CBreezeShadow::getPositioningInfo()+0x1a5 al mapear una ventana.

Hyprland posee CHyprBar con Hyprutils CUniquePointer. CBreezeShadow conserva una CWeakPointer,
pero llamaba m_bar.lock(): Hyprutils aborta deliberadamente al intentar crear un propietario
compartido desde una referencia débil a un propietario único.

**Arreglo en src/breezebars/barRemote.cpp:** cuatro m_bar.lock() pasan a referencias débiles
comprobadas (getPositioningInfo, outerBox, draw, renderPass), como la lista global de barras.
No quitar lock() a las referencias de ventanas/monitores: ésas sí tienen propietario compartido.

Compilado y desplegado con make -C src/breezebars y make -C src/breezebars install.
-fno-gnu-unique presente; readelf no encuentra símbolos UNIQUE. SHA256 de fuente compilada
src/breezebars/breezebars.so y binario instalado config/hypr/plugins/breezebars.so:
60db26a97493418235136474c1d6b0aed74203f472b65444375f3058c0f55ffa.
No se ha cargado ni descargado en caliente. El nuevo binario se usará al siguiente inicio normal.

### Prueba de regresión real

Nueva test_shadow_positioning_with_unique_owned_bar en tests/test_breezebars.py: compila el
método real de posicionamiento con los tipos de memoria reales de Hyprutils y simula únicamente
el estado del marco. Comprueba sin auxiliar, con marco/sombra y tras destruir la barra.

- Con el código anterior recuperado de HEAD en una copia temporal, reproduce retorno -6 y
  «tried to lock a CWeakPointer over a CUniquePointer». No se alteró el código vivo para reproducir.
- Con el arreglo pasa. Las cuatro pruebas de test_breezebars.py pasan en 29,368 s, incluidas
  compilación/símbolos y comunicación con el auxiliar real.
- Registros locales: /tmp/bwm-f10/crash-fix-build.log y crash-fix-tests.log.
- Comando: python3 -m unittest discover -s tests -p test_breezebars.py

### Diagnóstico anterior: límite importante

Se preparó una entrada XDG de diagnóstico de un solo uso, que **ya se eliminó al ejecutarse**.
La ruta guardada en /tmp/bwm-f10/probe-entry.txt ya no existe. No recrearla sin necesidad.
Script residual: /tmp/bwm-f10/after-login-probe.py.
Resultados privados: ~/.local/state/bwm/plasma/f10-checks/latest.json y csd-audit.md.
El JSON vio plugin e IPC, pero aún no había ventanas: **Hyprland cayó después**. Ese resultado
NO valida el arranque ni la matriz CSD. No publicar esos informes privados ni volcados de ventanas.

## Implementación F10 existente

Commit 2c0ad9f: reglas KWin, snapping y mosaico; commit posterior 5510b3e: dos arreglos QML
(import qs en PanelState y listas de bandeja aún no inicializadas en TrayPopup).
Último HEAD observado: 5510b3e. No se ha hecho push en estas comprobaciones.

- Reglas: skins/plasma/scripts/kwin_rules.py integrado en el vigilante único F2
  kde-config-bridge.py. Lee kwinrulesrc, orden por propiedad, DontAffect, Apply/Force/Remember;
  Lua generado antes del usuario. Ventanas nuevas marcadas, identidad dirección+PID, conflicto
  por clave al guardar Remember, guarda contra órdenes tardías al cambiar de skin.
- Carga en skins/plasma/hypr/{rules,kwinrules,kwin}.lua. Defaults de Breeze sacados de reglas comunes.
  KCM original kcmshell6 kcm_kwinrules funciona; detección/preselección D-Bus KWin no disponible.
- Encaje: src/breezebars/KWinSnap.hpp y SnapGeometry.hpp. Border/Window/CenterSnapZone,
  solapamiento, mitades/cuartos y arriba maximizado F8. Área útil lógica con reserved real,
  marco CSD/SSD real, monitor de la previsualización/puntero, workspace antes de geometría.
  Vecinas encajadas comparten redimensión; no persiste la proporción del grupo.
- **Decisión expresa del usuario: conservar Ctrl+flechas**, no cambiar a Super+flechas.
- Mosaico: kwin_tiles.py / kwin-tiles.py, JSON original kwinrc [Tiling][desktop UUID][output UUID].
  Asociación de UUID con descripción de monitor en estado local. Meta+T editor reducido,
  Mayús+arrastre hojas. Límites y cobertura documentados en arquitectura y KWIN_RULES.md.
- Outline/editor QML: modules/plasma/tiling, Loader sólo Breeze. Outline KSvg del tema activo,
  capa sin entrada. IPC plasmaOutline **display** (no show: CLI lo reserva), hide, inspect;
  plasmaTiles open/close/inspect. No inyectar secuencias de prueba en el outline real: se puede
  dejar rechazando secuencias del plugin. Para pruebas de secuencia usar qs -p aparte.
- CSD autoritativo: hyprctl -j breezebars-csd y Lua hl.plugin.breezebars.decoration(address,pid).
  Incluye metadata nativa para reglas. Ver docs/BREEZE_CSD_RESULTS.md.
- autostart.sh genera configuración del puente antes de cargar el plugin al inicio normal;
  éste recarga una vez y después se inician puente/decorador. No ejecutar autostart.sh a mano
  sobre la sesión recuperada: podría intentar cargar el plugin en caliente.

## Validaciones anteriores y lo que falta

Antes del crash: suite general 339 pruebas correctas, 60 omitidas; dos pruebas QML F10 activadas
correctas, parser real acepta reglas generadas, requisitos instalados correctos. Logs en
/tmp/bwm-f10/all-tests-release.log y qml-tests.log. No repetir toda la suite sin cambios que lo justifiquen.
Los arreglos QML de 5510b3e tienen pruebas aisladas reales sin ventana visible.

Pendiente, por orden:

1. Revisar el diff del arreglo y el estado de las instancias recuperadas. Confirmar binario/fuente.
2. Organizar una validación segura del arranque corregido sin cerrar a ciegas la sesión actual ni
   cargar el plugin en caliente. Si se necesita otro inicio completo, explicar al usuario el estado
   y coordinarlo; no presentar la autorización anterior como prueba de que el reinicio funcionó.
3. Abrir al menos una ventana de prueba y confirmar estabilidad, plugin cargado, decoración/API
   y shell. Un plugin presente sin ventanas ya dio un falso positivo.
4. Ejecutar la lista docs/BREEZE_F10_CHECKLIST.md: CSD/SSD, bordes y cruce de monitores, outline
   con dos temas, Ctrl+flechas, imanes, redimensión vecina, Meta+T/Mayús, reglas reales y cambio de skin.
5. Separar lo comprobado de lo pendiente en checklist/contexto. No dar F10 por terminada sólo
   por las pruebas unitarias. F6–F9 también conservan pruebas reales pendientes.

## Cambios SIN COMMIT que pertenecen a este arreglo

- src/breezebars/barRemote.cpp
- tests/test_breezebars.py
- config/hypr/plugins/breezebars.so (desplegado atómicamente, versionado)
- BWM_CONTEXT.md (§150)
- docs/BREEZE_F10_CHECKLIST.md (incidente posterior al reinicio)
- docs/BREEZE_F10_HANDOFF.md (este archivo)

Revisar git diff antes de un eventual commit. No hay commit ni push del arreglo del crash todavía.
El resto de modificaciones ya existía, generado por cambios de skin o ajeno: btop, GTK, theme.lua,
persistent_rules.*, perfiles config*.json, kitty, rofi, swaync y todo.md. No descartarlas ni incluirlas
por accidente en un commit de este arreglo. La autorización histórica de «sube todo» no significa
que se haya hecho un push de estos cambios.

## Restricciones que importan especialmente ahora

- Nunca plugin unload/load en caliente ni cp sobre un .so cargado. make install atómico solamente.
- Nunca una segunda instancia qs -c ii; qs -p separado para pruebas y limpieza posterior.
- No tocar ~/.config/bwm/user/* ni SDDM, /boot o autologin para sortear este crash.
- Ventanas de prueba al workspace 9 silent, reglas temporales y limpieza; dirección más PID.
- No cambiar red/Bluetooth reales. Capturas sólo recortadas y borradas al acabar.
- No mezclar funcionalidades del plugin de Retro con breezebars. Mantener Ctrl+flechas.

## Actualización (Claude, 2026-11-11)

El arreglo de la sombra está validado en un Hyprland anidado (`BWM_CONTEXT.md` §3.151): sin caída con
el binario instalado; la versión anterior reproduce el aborto. Para repetirlo sin tocar la sesión:
config mínima que haga `require` de `modules.rules`, `modules.app_rules` y `modules.appearance`,
`BWM_DECORATOR_SOCKET` con un socket propio, `Hyprland --config …` con `WAYLAND_DISPLAY` de la sesión,
`hyprctl plugin load` **con la firma de la instancia anidada**, y la ventana anidada visible (si no,
no dibuja ni conecta con el auxiliar). Lo pendiente sigue siendo los pasos 2–5 de arriba en un inicio
de sesión normal, que decide el usuario.
