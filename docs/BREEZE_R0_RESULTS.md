# R0 — auditoría completada sobre el material disponible

2026-11-12. Se reutiliza la revisión nocturna y se amplía con lectura directa de contratos
libplasma, configuración/edición upstream, carga de módulos BWM y estado posterior al crash.
**No se implementa R1/R2 ni se cambia runtime en esta ejecución.**

## Entregables

- BREEZE_AUDIT_V2.md: inventario priorizado actualizado, contratos por área, dependencias,
  aceptación y orden corregido después del incidente.
- BREEZE_R0_REFERENCE.json: 26 archivos y sus SHA-256, commits desktop/workspace y estado
  verificable frente a desconocido. Incluye binario instalado, sin afirmar que esté cargado.
- BREEZE_R0_REFERENCE.md: entorno de referencia, baseline claro de fábrica y oscuro separado,
  12 escenarios, topología/escala propuestas, método de medición y gate de estabilidad.

## Conclusiones nuevas o afinadas

1. P0 de captura/recuperación antes de más apariencia. Mantener la contención; crash sin
   causa reproducida. Ni R0 ni la revisión del binding certifican que se haya resuelto.
2. R1 existente se aprovecha pero no se cierra: dock Retro restaura a normal actual, no al
   especial de origen, y la semántica del compositor no se ha verificado en sesión.
3. R2 tiene un KCM nativo real; faltan las demás páginas y el lanzador. No confundir la
   presencia en systemsettings --list con migración completa de Ajustes.
4. Libplasma ofrece Corona/Containment/Applet y un ejemplo CustomCorona. La falta de host es
   un trabajo arquitectónico concreto de R4, no una imposibilidad general de los plasmoides.
5. PanelState comparte configuración entre pantallas y Kickoff.configureAction está desactivada;
   un editor equivalente requiere identidad/configuración por instancia y acciones originales.
6. Las curvas MD3 y la duplicación son comprobadas. **No se demuestra el fallo al volver al
   factor 1**, porque appearance carga primero la base de animaciones y después kwin.lua;
   el puente provoca reload. Corregida la afirmación excesiva del inventario inicial.
7. El paquete original Breeze instalado declara BreezeLight de fábrica. La referencia oscura
   se debe medir como caso separado; no llamar al estado oscuro actual «default original».

## Qué se ha verificado ahora

Lecturas de código y fuentes locales, commits, existencia/huellas de 26 archivos, defaults de
fábrica y versiones systemsettings 6.7.5 / Quickshell 0.3.2. Los intentos de consulta read-only
hyprctl y busctl siguen rechazados por el sandbox: plugins vivos, propietario de servicios,
instancias del shell, monitores y atajos efectivos se registran como **no verificables**.
No se solicitó elevar permisos ni se sustituyó la sesión para conseguir esa información.

Se reutiliza la evidencia de la revisión inmediatamente anterior: 33 pruebas específicas OK,
compilación limpia y CTest del KCM OK, descubrimiento por System Settings real. No se vuelven
a ejecutar ni se presentan como pruebas de esta pasada documental. La suite histórica completa
había fallado en integraciones de sockets; la pasada offline excluyó esas integraciones y
omitió tests opcionales. No se transforma aquel resultado en certificación del escritorio.

## Cierre y pendientes

**R0 queda entregada según la alternativa que su prompt permite cuando no hay referencia
accesible:** procedimiento preparado y mediciones pendientes explícitas. No se considera
terminada la implementación de la skin ni comprobada su equivalencia con Plasma. Las pruebas
gráficas del protocolo se ejecutarán en las fases correspondientes, sin arrancar otro
escritorio sobre el del usuario.

Siguiente paso R1, con este prompt:

```text
Lee AGENTS.md, docs/BREEZE_PLAN_V2.md, BREEZE_AUDIT_V2.md, BREEZE_R0_RESULTS.md,
BREEZE_R0_REFERENCE.md, BREEZE_RECOVERY.md y los resultados R1 ya existentes.
Continúa R1 desde el código actual; no vuelvas a implementar lo que ya está probado.
Primero comprueba recuperación/estabilidad sin reactivar capturas ni sombras. No cierres
la sesión ni cambies de skin automáticamente para probar. Si no hay IPC, usa pruebas aisladas
y deja la validación de sesión explícitamente pendiente.
Cierra el hueco de restauración especial desde Retro conservando la semántica normal de
Omarchy; verifica Alt+S, foco, identidad PID, minimizadas, ambos monitores y tres skins.
No marques R1 completa sólo por pasar fixtures; documenta qué comprueba el compositor real.
No avances a R2 ni a cambios visuales hasta resolver o registrar sus gates de aceptación.
```

Sin cambios de código, compilación, instalación, recarga, reinicio, commit o push en R0 actual.
