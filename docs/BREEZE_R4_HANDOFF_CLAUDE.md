# Traspaso R4 para Claude

R4 sigue abierta. Lee `CLAUDE.md` completo, `BWM_CONTEXT.md` §2.4 y §3.183–208, `docs/BREEZE_PLAN_V2.md` (reglas comunes y R4), `docs/BREEZE_R4_RESULTS.md`, `docs/BREEZE_R4_ARCH.md` y el README de `src/bwm-plasma-host`. Contrasta el código y el estado de Git antes de modificar nada: hay numerosos cambios y archivos sin seguimiento anteriores que deben conservarse.

## Estado comprobado

- El auxiliar libplasma experimental aloja widgets y sus páginas originales; la opción propia de un widget externo se ha probado con persistencia aislada. Hay interfaces experimentales para panel, containments, catálogo y configuración. Consulta los informes para el alcance exacto.
- El usuario confirmó en Hyprland la reserva del panel temporal y el reajuste automático de una ventana maximizada completa en MSI, borde inferior, escala 1 y giro 0: reserva 44→92→44 y altura del marco 1396→1348→1396. Informe: `docs/BREEZE_R4_AREA_SESSION_RESULTS.json`. No extrapolar a otras salidas, ejes, escalas o bordes.
- El panel diario de Quickshell aún no ha sido sustituido. `replacementReady=false`: no convertir una prueba aislada en aceptación de producción. El puente Breeze se recargó para el ensayo y su observador de área queda activo.
- Existen resultados aislados y limitaciones de backend, migración y KNS en `docs/BREEZE_R4_RESULTS.md` y `docs/BREEZE_R4_ARCH.md`. La descarga remota KNS y la aceptación completa de sesión siguen pendientes. No confundir la conexión de KNS con una instalación remota validada.

## Continuación

Completa sólo R4 conforme al prompt y puertas de salida originales. Prioriza integración/selección/fallback seguro del panel nativo, autoridades y backends de widgets, ciclo real de KNS y aceptación de sesión, según el estado efectivo del código. Conserva los formatos KDE, la configuración y las opciones desconocidas. Prueba persistencia y migración sin destruir el origen; clasifica las capacidades no soportadas por paquete. Valida ambas pantallas, bordes/escalas y cambios de skin cuando corresponda. No declares R4 completa si sus criterios no se cumplen; documenta cada bloqueo con evidencia y alternativa.

El usuario autorizó alterar su sesión cuando sea necesario para el proyecto. Sigue las reglas de seguridad de plugins de `CLAUDE.md`, nunca cargues/descargues `.so` en caliente ni arranques una segunda instancia de Quickshell. No ejecutes plasmashell ni cambies de compositor. No alteres archivos de configuración personal protegidos. Evita repetir pruebas ya documentadas salvo cambios o dudas concretas.

En la ejecución anterior el sandbox no podía acceder a los sockets Hyprland/Wayland/D-Bus y una elevación fue rechazada por política. Comprueba tus propias capacidades sin intentar eludir restricciones; si no puedes ejecutar una prueba de sesión, prepara un comando acotado y claro para que el usuario lo ejecute. No pidas confirmación para acciones ya autorizadas. Actualiza resultados, arquitectura, `BWM_CONTEXT.md` y, si corresponde, `AGENTS.md` y `CLAUDE.md` sincronizados. No hagas commits ni avances a R5/R7 sin indicación.
