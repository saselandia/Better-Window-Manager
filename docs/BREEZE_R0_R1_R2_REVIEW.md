> Revisión histórica anterior a la finalización documental de R0. Estado actualizado de R0 en
> [BREEZE_R0_RESULTS.md](BREEZE_R0_RESULTS.md); los límites de R1/R2 siguen vigentes.

# Revisión de lo ejecutado durante la noche — 2026-11-12

## Veredicto

| Fase | Estado comprobado | Qué impide cerrarla |
| :--- | :--- | :--- |
| R0 | Inventario de código, versiones y plan de referencia presentes | Sin comparación gráfica reproducible ni comprobación de la sesión viva |
| R1 | Correcciones parciales, pruebas Python/Lua/JavaScript aprobadas | Alt+S real sin reproducir/verificar, matriz entre skins ausente y restauración especial del dock Retro sin integrar |
| R2 | Prototipo KCModule real compilable y descubierto por KDE | Sólo luz nocturna; no se migraron las páginas BWM, alias ni el lanzador de Super+I |

**No son tres fases completas.** R0 es una auditoría documental con pendientes; R1 y R2 son
implementaciones parciales. Los informes nocturnos lo indican, pero no deben usarse como
certificación de integración. El crash posterior tampoco ha quedado reproducido/resuelto.

## Hallazgos

1. **Contención incompleta de capturas (corregida en esta revisión).** El PanelWindow del
   Alt+Tab común tiene visible=false en Breeze, pero sus delegados pueden seguir existiendo.
   La condición captureSource dependía únicamente de root.isOpen; al abrir el cambiador Breeze
   podía pedir capturas desde la vista común oculta. Desactivar las tres vistas Breeze no
   cubría esa ruta. Ahora captureSource/live/visible respetan panelWindow.visible. Se añadió
   prueba QtTest offscreen que ejecuta el binding real: oculto→sin fuente, visible→fuente,
   cerrado→sin fuente, oculto de nuevo→sin fuente. No se activa ningún protocolo de captura.
   Esto cierra un hueco de contención, **no demuestra la causa original ni evita peticiones
   de captura de otros clientes**.
2. **R1 no cubre el origen especial al restaurar desde el dock Retro.** Dock.qml bringForward
   mueve una minimizada al workspace normal actual. Las nuevas etiquetas de origen especial
   no intervienen allí. El controlador común sí guarda/recupera el nombre, pero el objetivo
   de consistencia en todas las skins sigue incompleto. No se alteró el dock en esta revisión.
3. **Las pruebas de activación no validan la API del compositor.** Ejecutan Lua con dispatchers
   simulados, y el filtro real QML en QtTest. Prueban orden/identidad/filtro, no la semántica
   efectiva de focus(workspace especial), elevación ni persistencia visual en Hyprland.
4. **R2 aún no es la nueva aplicación de Ajustes activa.** open-settings.sh sigue ejecutando
   qs -p plasmaSettings.qml. La prueba con systemsettings --list es real pero sólo demuestra
   descubrimiento del módulo nativo. No demuestra las 26 páginas migradas ni equivalencia visual.
5. **El KCM sigue experimental.** save() puede esperar hasta 10 s al backend; no hay prueba con
   el controlador real ni traducciones completas. --status de nightlight.py ejecuta la migración
   heredada antes de leer, por lo que abrir esa página no debe probarse contra datos del usuario
   como si fuera una operación sin efectos. No se ejecutó dicho backend en esta revisión.

## Repetición de pruebas

- Activación: 7 pruebas OK (incluye nueva regresión de captura de fallback oculto).
- Minimizado: 6 OK. Ventanas KWin/geometría/activación: 13 OK. Manifiestos: 7 OK.
  Total **33 pruebas específicas**, sin omitidas en estas ejecuciones.
- R2 reconstruido desde cero en /tmp/bwm-review-r2, CMake y compilación correctos.
- CTest native-kcm: OK (dos métodos de prueba y preparación/limpieza QtTest).
- systemsettings real con plataforma offscreen y QT_PLUGIN_PATH de la compilación nueva:
  encuentra kcm_bwm_nightlight. No instalado en el prefijo del usuario.
- hyprctl sigue sin acceso al socket. No se verificó estado vivo, recargó shell, movió ventanas,
  cambió skin ni cerró sesión. No se modificaron archivos generados de temas que cambiaron
  desde la última sesión. git diff --check correcto.

Siguiente prioridad: verificar recuperación y Alt+S en sesión real antes de continuar nuevos
ports. Después cerrar restauración de especiales desde Retro y la migración completa de R2.
