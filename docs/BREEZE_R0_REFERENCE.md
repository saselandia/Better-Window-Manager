# Referencia reproducible y protocolo de comparación — R0

Este procedimiento es el entregable alternativo previsto en R0 cuando no hay una sesión Plasma
comparable disponible. **No se ha ejecutado la referencia gráfica.** Los valores siguientes son
una especificación de ensayo, no el estado del escritorio del usuario.

## Entornos separados

- **Referencia:** VM o equipo/sesión desechable de Plasma 6.7.5 con KWin 6.7.5, Breeze 6.7.5,
  Frameworks 6.29.0 y Qt 6.11.2, si es posible reproducir esas versiones. Fijar revisiones de
  paquetes y commits. Si una versión difiere, registrarlo antes de comparar; no certificar
  pixel-perfect ni tiempos equivalentes entre builds distintos.
- **BWM:** Hyprland compatible con el plugin y las fuentes fijadas en BREEZE_R0_REFERENCE.json.
  Preferentemente compositor anidado desechable; documentar qué no reproduce ese backend.
  No usar una sesión recuperada en modo seguro como referencia visual del port.
- No arrancar plasmashell/KWin sobre el escritorio habitual. No cambiar HOME para probar los
  scripts BWM con rutas fijas. En VM usar su usuario normal; un entorno de datos temporal no
  sustituye aislamiento de compositor, D-Bus, servicios y dispositivos.
- Usar ventanas de prueba y datos sintéticos: título fijo, contenido neutro, mismas dimensiones.
  No capturar ventanas personales, contraseñas, portapapeles, lista de redes o notificaciones reales.

## Baseline de fábrica comprobable

El archivo instalado `/usr/share/plasma/look-and-feel/org.kde.breeze.desktop/contents/defaults`
(huella registrada) declara **BreezeLight**, widgetStyle Breeze, iconos breeze, desktoptheme
`default`, decoración library org.kde.breeze/theme Breeze y fondo Next. No es Breeze Dark.
Se define ese baseline explícito y otro oscuro, con esquema BreezeDark, como caso separado.
El baseline oscuro no se presenta como la configuración de fábrica del paquete claro.

| Parámetro | Valor del ensayo |
| :--- | :--- |
| Versión/paquete | Las versiones anteriores, con manifest de fuentes/build |
| Fuente | Noto Sans 10; monoespaciada Hack sólo donde la vista la use |
| Idioma base | es_ES.UTF-8; repetir inglés y RTL en casos de accesibilidad |
| Panel | Un panel inferior de 44 unidades lógicas; flotación según default original registrado |
| Configuración inicial | Perfil limpio en la VM, sin temas o efectos de terceros ni modo táctil forzado |
| Captura temporal | Frecuencia fija y documentada en ambos; 60 Hz como baseline propuesto, ensayo adicional a alta frecuencia |
| Pantalla A propuesta | 2560×1440 a escala 1 |
| Pantalla B propuesta | 3840×2160 a escala 1.5, posición lógica definida y registrada |
| Escalas adicionales | 1.25 y 2 en pasada separada, sin mezclar resultados |
| Fondo | Next para apariencia; color neutro uniforme en pasada separada para medir alpha de sombras |

Esta topología se propone para reproducibilidad; no se afirma que sean los modos actuales del
usuario ni que una VM permita todas las frecuencias. Toda sustitución se registra.

## Ficha por medición

Guardar por caso: id, versiones, fuente de configuración, escala/DPR, resolución lógica/física,
frecuencia real, compositor/backend, tema/colores/decoración, idioma/fuente y factor de animación.
Añadir pasos exactos, acción de entrada, imagen/vídeo recortados de la ventana sintética y
resultado esperado/observado. Registrar por separado pruebas automatizadas, visuales y físicas.
Guardar sólo la configuración sintética, nunca un volcado de la configuración personal.

## Casos de comparación

| ID | Acción reproducible | Medición / aceptación |
| :--- | :--- | :--- |
| REF-01 | Abrir Kickoff, reloj y bandeja de uno en uno | Marcos, márgenes, tipografía, azul de selección y anclaje. No se atenúa accidentalmente el panel |
| REF-02 | Entrar/salir de edición desde escritorio y panel | Controles, menús, teclado, asas y foco como original. No sustituir por seis casillas de widgets |
| REF-03 | Mover/cambiar grosor y longitud de panel en cuatro bordes | Área reservada lógica igual; alineación, flotación y ocultación persistentes |
| REF-04 | Dos paneles y dos instancias del mismo widget | Identidad y configuración independientes. Cancelar no modifica la instancia ni la otra |
| REF-05 | Instalar widget externo con una opción propia en entorno aislado | Opción descubierta sin editar BWM; Aplicar/Predeterminados/reapertura correctos |
| REF-06 | System Settings: módulo QML, QWidget y BWM | Mismo anfitrión real, categorías, búsqueda, subpáginas y aviso al navegar con cambios |
| REF-07 | Ventana SSD activa/inactiva, escala, resize y bordes | Frame y sombreado: padding y perfil alpha sobre fondo controlado, sin recorte ni doble sombra |
| REF-08 | CSD y XWayland, fullscreen/maximizado/restaurar | Una decoración adecuada, radios/marco correctos y retorno al mismo workspace/geometría |
| REF-09 | Abrir/cerrar/minimizar/maximizar, cambiar workspace, panel y popup | Duración, curva, posición, escala y opacidad por frame; distinguir efectos KWin de QML |
| REF-10 | Cambiar factor 0→1→2→1 y cancelar/revertir gesto | Cero sin movimiento, vuelta consistente; no sólo leer el valor escrito en KDE |
| REF-11 | Foco por teclado, menú, Esc, RTL y lector | Ningún control inaccesible, nombre/orden razonables y escape sin entrada residual |
| REF-12 | Tema alternativo SVG + decoración y sus opciones | Seguir métricas/opciones originales, sin colores/radios propios que oculten diferencias |

Magic no existe como tal en Plasma: sus casos se comparan **entre skins BWM**, sin inventar
una referencia KWin. Probar estado oculto/visible, dos monitores, Alt+S/Alt+Shift+S, tareas,
Alt+Tab y minimizado/restauración desde cada dock/controlador. Verificar dirección+PID/inicio,
workspace y monitor. La restauración del dock Retro es un hueco conocido de R1.

## Tolerancias y límites

- Geometría: comparar unidades lógicas primero, después píxeles físicos considerando DPR y
  redondeo. Diferencias de 1 px se registran; no se declaran equivalentes automáticamente.
- Tipografía: mismo motor, fuente y tamaño. Si el rasterizado/backend difiere, comparar también
  cajas y baselines; no ocultar la diferencia mediante escalado arbitrario de la captura.
- Sombras: medir grosor/padding y muestras de alpha por distancia en fondo uniforme; una foto
  del escritorio no distingue ausencia de sombra, color distinto y composición incorrecta.
- Animaciones: registrar timestamps, frames perdidos y tiempo de presentación; una tolerancia
  de un frame sólo tiene sentido con frecuencia y captura conocidas. Fijar umbrales por efecto
  en R7 antes de usar resultados para afirmar equivalencia.
- Un caso no ejecutado es pendiente. Una prueba con mocks valida un contrato local, no el
  resultado del compositor. Un paquete de terceros no prueba toda la KDE Store.

## Gate previo de estabilidad

No ejecutar REF-07/09 ni reactivar miniaturas/sombras en el escritorio real antes de investigar
el crash documentado en BREEZE_RECOVERY.md. Reproducción aislada: captura sobre una ventana
normal y luego oculta/minimizada/especial/cerrada, con y sin decoración/plugin; distinguir
crear sesión de captura y dibujar frames. Relacionar el monitor nulo con una ventana/cliente
concretos. No escribir un test que haga caer el compositor de uso diario.

R0 no incluye ejecutar estos ensayos ni instalar un escritorio adicional. Deja este procedimiento
listo para R1/R4–R9 cuando exista un entorno de prueba seguro.
