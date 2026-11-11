# F13 — cierre del port Breeze y comprobaciones

Comprobado el 2026-11-11 en Gentoo: Hyprland 0.56.2, Plasma 6.7.5, Frameworks 6.29,
Qt 6.11.2 y Quickshell 0.3.2. El port funciona sobre Hyprland; no ejecuta KWin/plasmashell.
F13 cierra la limpieza del plan; las pruebas físicas y las limitaciones siguientes siguen abiertas.

## Limpieza y piezas conservadas

- Eliminados todos los `modules/ii/plasma*`: 13 archivos de plasmaCommon y el selector artesanal.
  F3–F12 ya habían sustituido panel, applets, menús, cambiador y bloqueo.
- Eliminados 152 SVG de assets/icons/breeze-dark sin consumidores. Se usa el tema de iconos
  instalado; breeze-icons sigue declarado como requisito.
- Eliminada la paleta fija de reserva de MaterialThemeLoader y la rama Breeze antigua del OSD.
  applyPlasmaColors conserva la conversión de roles para los widgets comunes de BWM.
- «Mostrar escritorio» vive en modules/plasma/panel/DesktopState.qml. Conserva el archivo y
  las acciones comunes de minimizado; desaparecen las heurísticas antiguas de panel flotante.
- Alt+T abre BWMenu en Breeze. Es el selector de skins de BWM; los temas globales originales
  se eligen en Preferencias → Tema global. Se retiran su antiguo IPC y estados sin consumidores.
- Geometría del panel sólo en modules/plasma/panel. Se eliminan sus tamaños especiales del
  Bar/Appearance comunes y las exclusiones redundantes de BarContent (sólo cargado en default).
- Reglas de Breeze en skins/plasma/hypr/rules.lua; incluida la supresión de barra del
  salvapantallas, con su guarda hl.plugin.breezebars. El rules.lua común no contiene campos
  breezebars ni una sección Plasma vacía.
- parts actualizado; catálogo y requisitos comprobados, tabla REQUIREMENTS regenerada.
  No se añaden paquetes nuevos.

Se mantienen quick-tile.py y toggle-minimize.py: los atajos de las tres skins, docks de
end-4/waffle, autostart-manager y el controlador kwin-window/kwin-tiles todavía los usan.
Incluyen tamaño previo al encaje, marco real, minimizar/restaurar y Mostrar escritorio.
No se elimina una operación pública compartida sólo por haberse sustituido una interfaz.

### Auditoría isPlasma

Se retiraron las ramas de OSD antiguo, tamaños de panel en Appearance/Bar y visibilidad
redundante de BarContent. Permanecen las selecciones necesarias de Loader en la familia,
OSD y bloqueo, el proveedor de paleta común, políticas de Alt+Tab y del agente polkit,
selección de skin/forma de widgets comunes y opciones compartidas de Ajustes. PanelState
sólo consulta la skin para suspender la actualización cuando está descargado. Estas ramas
no son interfaces de Breeze dibujadas dentro de módulos de otra skin.
BREEZE_DARK_M3, applyBreezeColors y plasmaCommon ya no tienen consumidores en producto.
Los valores por defecto de KColorScheme para esquemas incompletos siguen siendo necesarios.

## Cambio real de skins

Secuencia: **default → Breeze → Retro → Breeze**, con diez ventanas de apps existentes y
siete flujos PipeWire/PulseAudio (cinco no pausados al comienzo de la pasada final). Se compararon dirección,
PID y tiempo de inicio del proceso, workspaces, geometría, monitores y flujos/volumen/silencio.

| Resultado por cambio | default | Breeze | Retro | Breeze final |
| :--- | :---: | :---: | :---: | :---: |
| Ventanas conservadas | 10/10 | 10/10 | 10/10 | 10/10 |
| Ventanas enviadas a otro workspace | 0 | 0 | 0 | 0 |
| Workspaces visibles cambiados | 0 | 0 | 0 | 0 |
| Flujos de audio conservados y sin alterar | 7/7 | 7/7 | 7/7 | 7/7 |
| Instancias de shell ii | 1 | 1 | 1 | 1 |
| Errores de configuración Hyprland | 0 | 0 | 0 | 0 |

El mosaico reorganiza tamaños/posiciones durante default y Retro, como corresponde a esas skins.
Una repetición posterior detectó tres intercambios de posición entre ventanas del mismo
workspace por el orden de inserción en dwindle. Se corrigió guardando la geometría libre de
Breeze antes de salir: caché por sesión/skin en XDG_RUNTIME_DIR, dirección+PID+inicio del proceso,
workspace y descripción/geometría del monitor. Al volver se restaura el mismo marco con los
bordes de decoración actuales. Un cambio de workspace, monitor o modo especial descarta la
entrada; fullscreen, minimizadas, ancladas y maximizadas no se sobrescriben. No se guardan
reglas/configuración del usuario. Las ventanas nuevas siguen la colocación normal.
La pasada final con esta corrección recupera exactamente las diez geometrías iniciales.
Al salir también se eliminan sólo las etiquetas mutables de estado BWM; las del usuario y de
reglas se conservan. Cinco pruebas nuevas cubren identidad, prioridad, estados y etiquetas. Los procesos de apps conservan identidad; no se demuestra con ello que cada
reproductor produzca sonido audible sin interrupciones: se verifican sus flujos activos y estado.
La primera pasada incluyó un hyprland-dialog transitorio; no era una app cerrada por el gestor.

### Conflicto real encontrado y corregido

kded 6.29 src/kded.cpp registra **en cola** todos los X-KDE-DBus-ServiceName de sus plugins,
aunque autoload=false. Al liberar Quickshell la bandeja durante una recarga, kded podía tomar
org.kde.StatusNotifierWatcher sin ofrecer /StatusNotifierWatcher. Detenerlo una vez no bastaba.

bwm-shell-conflicts.py --repair-stale comprueba ese caso y sólo retira el PID si el objeto
no existe y sus únicos módulos cargados son ktimezoned o ninguno. No retira un watcher
funcional, otros módulos KDE, procesos de otro usuario ni todos los procesos del mismo nombre.
ConflictKiller lo comprueba al cargar. Los conflictos reales conservan el diálogo de decisión.
Pruebas unitarias cubren ambos casos y la repetición de la secuencia quedó sin el aviso.
Fuente estudiada: https://invent.kde.org/frameworks/kded/-/blob/v6.29.0/src/kded.cpp.

## Tema global de la KDE Store

**Sweet KDE**, de EliverLara, instalado desde la acción «Obtener nuevos…» del KCM original de
Tema global, dentro de una copia de Preferencias en qs -p y workspace 9 silent.
Se activaron las operaciones originales del KCM mediante una sonda; no fueron clics físicos.
Las descargas se hicieron a los datos reales del usuario y constan en los registros de KNewStuff.
Tema original: https://store.kde.org/p/1294729/ y https://github.com/EliverLara/Sweet.
Los recursos descargados permanecen instalados, fuera del repositorio.

El instalador también resolvió variantes Sweet-Mars/Ambar, candy-icons, estilos SVG, Aurorae,
cursores y fondos. Se omitieron dependencias SDDM cuyo knsrc no está instalado: no se tocó
el arranque. Ningún script de disposición o configuración de sesión del paquete fue ejecutado.

Aplicado **Sweet** desde el KCM de Preferencias, con selectedContents=31: colores,
estilo de aplicaciones, iconos, estilo de Plasma y decoraciones. Sin cursor, fuentes, fondo,
SDDM ni disposición; los ajustes comunes siguen bajo autoridad de BWM.

| Parte del tema | Evidencia y alcance |
| :--- | :--- |
| Esquema Sweet | Paleta generada scheme=Sweet, primary=#c50ed2, background=#181b28; QML lee #181b28 desde kdeglobals/kdedefaults. Plantillas de apps reciben esa paleta. No se certifica visualmente cada app. |
| Estilo de Plasma Sweet | plasmarc efectivo y PlasmaTheme.desktopTheme=Sweet; KSvg carga los SVG originales, panel en vivo y recorte propio revisado. Aviso upstream: metadata.desktop antiguo. |
| Aurorae Sweet-Dark | El auxiliar de sesión responde org.kde.kwin.aurorae / __aurorae__svg__Sweet-Dark; marco 4/28/4/4, imagen real revisada, sin errores. Es una ventana virtual de prueba del mismo auxiliar, no una matriz física de apps y botones. |
| Iconos candy-icons | Recursos instalados por KNS; KCM/kdeglobals y PlasmaTheme.iconTheme=candy-icons coinciden. No se certifican todos los iconos de todas las apps. |
| Cursor Sweet-cursors | Instalado por KNS en ~/.icons/Sweet-cursors; **no aplicado**. kcminputrc conserva miku-cursor-linux, tamaño 48, por la regla 14. |
| Estilo de aplicaciones | kdeglobals efectivo selecciona kvantum, instalado. No se ha certificado el aspecto completo de un tema Kvantum Sweet en cada app Qt. |
| Bloqueo, Alt+Tab y OSD de terceros | Este paquete Sweet trae defaults/previews/splash, sin esos componentes. Se conservan las vistas de reserva de F12. No es una prueba nueva de temas privados de bloqueo/cambiador. |
| Splash, efectos y disposición | No portados; no se aplican ni se ejecuta KWin. Plasmoides externos siguen sin anfitrión completo. |

La aplicación nativa descubrió lecturas incompletas de kdedefaults: PlasmaTheme y plasma_palette
ahora fusionan XDG_CONFIG_DIRS → kdedefaults → configuración local, con cambios en vivo.
La entrada local explícita manda. Una prueba QML cambia el esquema sin reiniciar y comprueba
que iconos locales ganan a los del tema global; otra prueba cubre el lector Python y .colors.
La configuración KDE previa se restauró después; el cursor y fondo comunes se conservaron.
Las imágenes de decoración/panel se borraron después de revisarlas.

### Estimación

Se conserva **~50 %** como estimación prudente de compatibilidad global en los tres documentos.
Cuatro capas de apariencia tienen evidencia de integración con Sweet, y el cursor permanece
común deliberadamente. No es un porcentaje medido de temas de la Store ni una promesa de
compatibilidad con la mitad de todos los paquetes. Un tema no prueba efectos, scripts,
plasmoides externos ni todas las APIs privadas de bloqueo/cambiador.

## Verificación automática y estado final

- Suite general final: 371 pruebas, 65 opcionales omitidas; sin fallos.
- Prueba QML de prioridad/cambio en vivo activada: pasa. ocho pruebas F12 activadas también pasan.
- qmllint de los archivos modificados ejecutado; avisos por imports qs/metadatos dinámicos,
  contrastados con la carga real. Hyprland --verify-config: config ok; configerrors vacío.
- Requisitos de Breeze comprobados. Una sola instancia ii; bandeja y agente polkit KDE en sesión.
- No se recompiló ni se cargó/descargó ningún plugin en caliente. Reinicio de mantenimiento
  del shell para cargar DesktopState, sin cerrar sesión ni reiniciar apps.
- Avisos previos: traducción en_US ausente, ToolbarTabBar, UPower no instalado y un objeto
  gráfico Omarchy sin escena. No se presentan como solucionados por F13.

## Reiniciar sesión y comprobaciones manuales

**F13 no cambia el binario del plugin:** el shell ya se reinició para la limpieza. No exige otra
salida de sesión para estos cambios. Tras actualizar Hyprland o instalar otro breezebars.so,
compilar e instalar con make install y cerrar sesión/entrar; nunca plugin unload/load en caliente.

1. En el siguiente inicio normal, comprobar acceso a Breeze sin crash, paneles en ambos
   monitores, bandeja sin conflicting programs y ausencia de Your config has errors.
2. Recorrer docs/BREEZE_CSD_RESULTS.md: apps Wayland/XWayland, una sola barra, negociación
   dinámica CSD/SSD y fullscreen. La matriz completa sigue pendiente de interacción real.
3. Recorrer docs/BREEZE_F10_CHECKLIST.md: arrastre por los dos monitores, esquinas, imanes,
   Mayús, vecinos y Meta+T. Ctrl+flechas se conserva.
4. Minimizar/restaurar, maximizado completo/por ejes y doble clic en la barra; geometría de
   Aurorae y menús con botones físicos, tanto en SSD como en CSD.
5. Alt+Tab rápido/sostenido, miniaturas de apps reales y foco al soltar Alt; OSD con teclas
   de volumen/brillo. Bloqueo real con contraseña/huella y autenticación polkit KDE.
6. Preferencias → Tema global → Obtener nuevos…: navegar, instalar y aplicar con ratón;
   comprobar cada app importante y después volver al tema preferido. Cursor/fondo comunes
   deben conservarse. Las operaciones por sonda no certifican esos clics físicos.

Estos pendientes impiden declarar equivalencia completa con KDE Plasma o una auditoría de release.
