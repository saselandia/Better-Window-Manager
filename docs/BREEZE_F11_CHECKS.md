# F11 — comprobaciones pendientes de Preferencias del sistema

Comprobado el 2026-11-11 con Plasma 6.7.5, Frameworks 6.29.0, Qt 6.11.2,
Quickshell 0.3.2 y la sesión de Breeze activa. Resultado de las pruebas que habían quedado
pendientes tras la implementación de Claude en BWM_CONTEXT.md §154.

## Método y alcance

Se cargó una copia temporal de **plasmaSettings.qml**, con su **ModuleView/KcmPage/KcmHost reales**,
en procesos `qs -p` aparte y ventanas al workspace 9 silent, sin foco inicial. Se eligió cada
página mediante SETTINGS_PAGE. Una sonda llamó a las propiedades y operaciones reales del KCM
que usa la interfaz; no se sustituyeron por dobles de prueba. No se pulsaron físicamente los controles.

Configuración, datos, caché y estado XDG en /tmp/bwm-f11-checks; HOME no se cambió.
Config.blockWrites activado en la copia para impedir escrituras de los módulos comunes.
Bus D-Bus privado para las notificaciones de apariencia: estas pruebas comprueban carga,
aplicación y persistencia del KCM, **no la propagación en vivo al escritorio principal**.
La prueba de sonido sí usa el servidor PipeWire/PulseAudio real, sólo con una salida virtual
temporal creada para la prueba. No se cerró sesión ni se modificó/cargó el plugin de Hyprland.

## Resultados

| Pendiente | Acción ejecutada | Resultado comprobado |
| :--- | :--- | :--- |
| Iconos | KCM kcm_icons: cambiar BWM-Papirus a breeze-dark y guardar | needsSave pasa a true y vuelve a false; kdeglobals [Icons] Theme=breeze-dark en la configuración temporal |
| Fuentes | KCM kcm_fonts: fuente general Noto Sans, 12 puntos; guardar | kdeglobals [General] font=Noto Sans,12,…; estado de cambios limpio tras guardar |
| Decoraciones | KCM kcm_kwindecoration: desactivar tamaño automático y elegir borde Large; guardar | kwinrc [org.kde.kdecoration2] BorderSize=Large y BorderSizeAuto=false; estado limpio |
| Estilo de aplicaciones | KCM kcm_style: alternar Breeze/Fusion y guardar | cambio real de modelo, needsSave true→false y widgetStyle=Fusion en kdeglobals; volver a Breeze elimina la clave cuando coincide con el valor predeterminado |
| Estilo de Plasma | KCM kcm_desktoptheme: elegir breeze-light; guardar | plasmarc [Theme] name=breeze-light y estado limpio |
| Tema global | KCM kcm_lookandfeel: elegir org.kde.breezedark.desktop y aplicar la selección de apariencia | LookAndFeelPackage cambia; kdedefaults/kdeglobals contiene BreezeDark, breeze-dark y widgetStyle=Breeze; kdedefaults/plasmarc selecciona default, kwinrc selecciona Breeze. Se aplicaron colores, estilo Qt, decoración, iconos y estilo Plasma; no cursor, fuentes, fondo, scripts ni disposición de escritorio |
| Sonido | KCM kcm_pulseaudio y su SinkModel: localizar por nombre exacto la salida virtual bwm_f11_check y cambiar volumen/silencio | pactl confirma 32768/65536 (50 %) en ambos canales y silencio activado. Comparación antes/después: volúmenes/silencio de todas las salidas y entradas físicas y dispositivos predeterminados iguales. Salida virtual eliminada; estado final idéntico al inicial |

Sonido aplica los cambios inmediatamente; su KCM anuncia sólo el botón Ayuda. No requiere
Aplicar ni expone save() como los módulos de apariencia. La sonda final respeta esa diferencia.

## «Obtener nuevos…» y descargas de la KDE Store

Se activó la **NewStuff.Action original del KCM**, sin crear un botón o un motor alternativo.
Los diálogos de iconos, decoraciones, estilo de Plasma y tema global se abren y sus motores
informan isValid=true con sus knsrc originales. También se abrió el de esquemas de color.

Dos descargas reales terminaron en el XDG_DATA_HOME temporal y en sus registros de KNewStuff:

- Esquema **Sweet Dark Blu**, KDE Store 1689224: color-schemes/SweetDarkBlu.colors.
  Archivo INI válido con 10 grupos, incluido Colors:Window; entrada en colorschemes.knsregistry.
- Estilo de Plasma **Sweet KDE**, KDE Store 1294174: plasma/desktoptheme/Sweet/,
  con metadata.desktop y recursos del tema; entrada en plasma-themes.knsregistry.

No se descargó ningún tema dentro del repositorio ni en las carpetas personales del usuario.
Se verifican dos descargas y la apertura de los otros diálogos; no se afirma haber instalado
por esta vía un paquete de iconos, una decoración ni un tema global.

Avisos observados del código KDE: KNewStuff solicita transientParent explícito y Kirigami
OverlayDrawer emite «Cannot read property width of null» al construir el diálogo. No impiden
las descargas comprobadas; no se presentan estas ventanas como libres de avisos. Al instalar
el .colors sin comprimir, KNewStuff registra primero que no reconoce un archivo comprimido
y después instala correctamente el fichero y actualiza su registro. El bus privado produce
avisos de servicios/portales ausentes que no prueban un fallo de la sesión normal.

## Limpieza y evidencia

- kdeglobals, kwinrc, plasmarc y kcminputrc reales comparados byte a byte con las copias
  iniciales de la prueba de sólo lectura: sin cambios.
- Comparación del sonido antes/después y tras descargar la salida virtual: idéntica.
- Sondas QML temporales eliminadas al acabar; sin segunda instancia qs -c ii ni capturas.
- Regla tmp-f11-probes retirada con hyprctl reload; configerrors vacío.
- test_plasma_settings.py: tres pruebas de catálogo pasan; las dos pruebas generales de
  interfaz se omiten en esa ejecución porque las páginas pendientes se ejercitaron con las
  sondas reales descritas arriba. No se volvió a ejecutar toda la suite del proyecto.
- Evidencia local temporal (no versionar registros privados ni enlaces de descarga firmados):
  /tmp/bwm-f11-checks/{icons,fonts,decorations,appstyle,plasmastyle,globaltheme}-apply/run.log,
  {icons,decorations,globaltheme,plasmastyle}-kns/run.log, colors-download/,
  plasmastyle-download/, sound-apply/run.log y audio-summary.log.

No se cambia la compatibilidad estimada por una prueba aislada. La pulsación física de Super+I,
el renderizado de una decoración distinta con el plugin y la propagación de estos cambios de
apariencia al escritorio real no se certifican aquí. El cambio de colores real ya estaba
comprobado en §154; se conserva ese resultado previo, sin repetirlo ni ampliarlo por inferencia.
