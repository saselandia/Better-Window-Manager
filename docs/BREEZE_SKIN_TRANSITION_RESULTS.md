# Retro → Breeze: auditoría del arranque y de la transición

2026-11-13. El usuario aporta una captura con iconos distintos de Breeze tras iniciar en Retro.
KDE y qt6ct seleccionaban breeze-dark, pero GTK 3/4 conservaba Adwaita. Compositor, D-Bus y
display siguen inaccesibles desde esta ejecución; no se afirma reparación visual en sesión.

| Área | Defecto encontrado | Corrección | Verificación |
| :--- | :--- | :--- | :--- |
| Barras de ventana | El arranque sólo cargaba breezebars si iniciaba en Plasma | Precarga al iniciar cualquier skin, desactivada fuera de Breeze; nunca cargar/descargar desde la transición | Cuatro pruebas del bloque real; corrección de §183 |
| Proveedor Qt del shell | Reconstruir paneles no cambia el proveedor GTK de un QApplication ya iniciado | bwm_session prepara KDE para el shell duradero, con qt6ct/portal como fallback y rutas estables de QML/kdedefaults | Selección independiente del entorno inicial y prueba nativa en un proceso |
| Arranque del shell | pidof quickshell confundía una ventana de ajustes con el escritorio ii | Usar bwm_session.ensure_shell y su guard por configuración | Pruebas de instancias, ausencia transitoria y recuperación; no duplicar ii |
| Iconos GTK | settings.ini conservaba Adwaita pese a gsettings/qt6ct | Actualizar sólo gtk-icon-theme-name y no reescribir si coincide | Temas de ida/vuelta, grupos/claves ajenos y mtime; archivos actuales corregidos a breeze-dark |
| Cachés Qt/KDE | Aplicar iconos comunes no notificaba a los cargadores KDE | Avisos de paleta, fuentes y estilo, más KIconLoader grupos 0–5; sin QIcon::setThemeName | Orden escritura→aviso y todos los grupos; iconos nuevos y retenidos cambian en el probe |
| Temas globales | El lector común de iconos sólo veía kdeglobals de usuario | Leer también XDG/kdedefaults conservando prioridad del usuario | Defaults personalizados y override probados; no se reescribe kdeglobals nativo |
| Trabajo diferido | Un trabajo de iconos de Retro podía terminar después de cambiar de skin | Comprobar skin antes de generar y antes de aplicar | Los trabajos obsoletos no escriben ni emiten cambios |
| Aplicaciones nuevas | La barra conserva su entorno inicial, que no debe imponerse a las apps | AppSearch.launch envía argv/cwd/terminal a bwm-launch-app.py; ejecución desde Hyprland con entorno actual y overrides Lua | Payload QML real, metacaracteres literales, cwd/terminal y rechazo del fallback obsoleto |
| Activación de servicios | D-Bus/systemd recibían el entorno sólo al arrancar y sin todas las rutas KDE | Completar las rutas al arrancar y solicitar exportación desde un hijo de Hyprland tras recargar, no desde el shell antiguo | Ruta/argumentos y ausencia de fallback probados; entrega por D-Bus/systemd pendiente |

El lanzamiento común se usa en buscador, menú Retro, dock, tareas y menús Breeze y grids/tareas
Waffle. Conserva el comando ya analizado por Quickshell, sin reconstruir Exec como una cadena
shell. Las acciones genéricas de búsqueda mantienen execute propio. Las apps de terminal usan
el gestor común de terminal predeterminada.

La política de las aplicaciones en modules/environment.lua sigue vigente; el proveedor KDE
estable es del shell. No se modifican bwm/user ni preferencias nativas, no se sustituye un
tema personalizado por Breeze fijo y no se reinician apps. Las paletas sólo emiten aviso
desde qt_sync si el kdeglobals generado realmente cambió.

## Prueba nativa del refresco

Qt 6.11.2, plasma-integration 6.7.5 y KIconThemes 6.29.0 instalados. Un QApplication offscreen
mantiene un QIcon y solicita otro nuevo en cada paso. Tres temas desechables de PNG permiten
verificar la selección e invalidación sin copiar recursos de terceros:

| Paso | Icono nuevo | Icono retenido |
| :--- | :--- | :--- |
| Inicial/Retro de prueba | #c44234 | #c44234 |
| Breeze de prueba | #3478c4 | #3478c4 |
| Vuelta al inicial | #c44234 | #c44234 |
| Tema personalizado de prueba | #7b34c4 | #7b34c4 |

Son fixtures para probar cachés, no una comparación visual de SVG Breeze reales. No se usa
QIcon::setThemeName ni forceThemeForTests. La prueba de bus privado fue bloqueada con
Operation not permitted; GTK tampoco puede abrir el display. No se eluden esas restricciones.
El ensayo final invoca localmente, sólo dentro del fixture, el receptor nativo _k_refreshIcons,
grupos 0–5. Ese contrato privado está fijado a la fuente KF6 6.29.0; producción emite señales
D-Bus normales. Se prueba render/caché, **no entrega por bus**. Un solo grupo no cubre todo
el orden de actualización de hints Qt y cargador KDE.

Fuentes locales revisadas: quickshell 0.3.2 src/launch/launch.cpp y src/io/processcore.cpp,
plasma-integration 6.7.5 qt6/src/platformtheme/khintssettings.cpp y KIconThemes 6.29.0
src/{kiconloader,kicontheme}.cpp. No se modifican esas implementaciones.

## Resultado y aceptación pendiente

54 pruebas pasan: runtime 12, panel 8, aplicador Plasma 12, sesión 7, colores Qt 4,
arranque Breeze 4 y manifiestos 7. Parser QML: nueve archivos cambiados válidos.
bash -n, py_compile y diff correctos. Evidencia en BREEZE_SKIN_TRANSITION_RUNTIME_RESULTS.json.

El shell actual necesita adoptar el nuevo arranque una vez. Cerrar y volver a entrar aplica
también la precarga de breezebars; reiniciar sólo el shell no carga un plugin ausente del
compositor. Para mantenimiento de una sesión cuyo plugin ya está cargado:

```bash
python3 ~/.config/hypr/scripts/bwm-theme-manager.py set plasma --restart-shell
```

Después, iniciar en Retro y pasar a Breeze debe conservar iconos/colores sin reiniciar el
shell en cada cambio. Falta comprobarlo en la sesión real, también para servicios activados
por D-Bus y aperturas desde menús. Las rutas de puente, decorador, notificaciones y polkit
siguen usando sus gestores actuales; no se duplican PowerDevil/KScreen/kglobalaccel.

Sin cargas/descargas de plugins en caliente, reinicio de compositor, segunda instancia ii,
cierre de apps, activación de sombras/miniaturas ni cambio de skin desde esta ejecución.
