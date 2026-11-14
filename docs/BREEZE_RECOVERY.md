# Incidente: captura de ventanas y modo seguro, 2026-11-12

El usuario comunica modo seguro después de la sesión nocturna. Informe más reciente leído:
`hyprlandCrashReport32.txt`, mtime 2026-11-12 11:24 (hora local del sistema). SIGSEGV,
Hyprland 0.56.2 efb5099…, plugin breezebars cargado. Pila:
Screenshare::CScreenshareSession::init+0xad7 → constructor de sesión por ventana →
CToplevelExportClient::captureToplevel. No es una prueba de fallo de sintaxis Lua.

El binario instalado tiene init en 0xbaf6a0. La instrucción de 0xbb0177 (offset +0xad7)
lee una dirección absoluta 0x94, seguida de CBox::scale. Es evidencia de acceso nulo al
calcular la escala, **no evidencia suficiente de que lo provoque la sombra o el plugin**.
No se identificó aún el cliente/ventana exactos ni se reprodujo. El entorno actual tampoco
permite conectar hyprctl a la sesión; versión viva y estado final no se verificaron.

## Contención aplicada

- Restaurado no_shadow=true en breeze-float-all; se revierte la habilitación adelantada de R6.
  Su relación causal con este crash no se ha demostrado. La prueba de política ahora exige
  mantener el veto hasta validar render y captura.
- Desactivadas temporalmente fuentes de ScreencopyView en TaskToolTip, ThumbnailGrid y
  compat/WindowThumbnail de Breeze. `live:false` solo no basta: se deja captureSource:null.
  Se mantienen etiquetas/selección de ventanas, pero no sus imágenes en estas vistas.
- No se cambió C++, instaló plugin, descargó/cargó plugin, reinició shell ni cerró sesión.
  No se cambiaron archivos de configuración de usuario o recoverycfg.lua.

Las referencias anteriores a R6 eliminado/verificado quedan supersedidas por este informe.
Falta comprobar en sesión normal el arranque y apertura del panel/Alt+Tab sin capturas.
No afirmar «solucionado» hasta hacerlo. Revisar además las restantes capturas comunes si se
repite: esta contención sólo cubre las vistas Breeze identificadas, no todos los clientes
posibles del protocolo. Investigar upstream o corregir compositor antes de reactivar capturas
sobre ventanas sin monitor, ocultas, cerradas o en workspaces especiales.

## Recuperación por el usuario

Guardar el trabajo desde la sesión de recuperación. Cerrar sesión y entrar normalmente para
que arranque la configuración del repo con la contención; esto termina las apps de esa sesión,
por lo que no se hizo automáticamente. No usar plugin unload/load ni matar Hyprland.
Si vuelve a fallar, conservar la recuperación y consultar el nuevo informe antes de otro intento.
No necesita recompilar ni instalar paquetes para estos cambios.


Revisión posterior de R0–R2: la vista común de Alt+Tab también podía capturar estando oculta
en Breeze. Se corrigió el binding de captureSource/live para depender de panelWindow.visible,
con regresión QtTest offscreen. Ver BREEZE_R0_R1_R2_REVIEW.md. La causa del SIGSEGV original
sigue sin reproducir; esta corrección no certifica recuperación de la sesión.
