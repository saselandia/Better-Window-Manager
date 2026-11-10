# Chromium y temas sin reiniciar en BWM

## ¿Puede Chromium cambiar de tema en vivo y qué usa realmente Omarchy?

### Takeaway
Sí, Chromium moderno puede recibir un nuevo color de tema sin cerrar ventanas, pestañas o procesos. La vía estándar de Omarchy usa una política de color y un refresco de políticas; reproduce un color base, no la transformación completa de fuentes y formas que BWM añade a Firefox.

### Cited Findings
- La política **BrowserThemeColor** admite una cadena `#RRGGBB`, genera y aplica un tema a partir de ese color y está soportada desde Chrome 91. Su definición declara `dynamic_refresh: true` y `per_profile: true`; mientras esté impuesta el usuario no puede elegir otro tema. Es evidencia oficial de actualización sin reiniciar, no una conjetura sobre GTK. — [Definición upstream](https://raw.githubusercontent.com/chromium/chromium/main/components/policy/resources/templates/policy_definitions/Miscellaneous/BrowserThemeColor.yaml); [documentación de Google](https://chromeenterprise.google/policies/browser-theme-color/).
- El código `ThemeService` de Chromium 151 observa `themes::kPolicyThemeColor`; `HandlePolicyColorUpdate()` construye el tema de política y `NotifyThemeChanged()` avisa a observadores para repintar. No contiene un cierre/reapertura del navegador en ese camino. La fuente 151 se eligió porque los ebuilds del equipo incluyen esa versión; **no significa que esté instalada**. — [ThemeService 151](https://raw.githubusercontent.com/chromium/chromium/151.0.7922.169/chrome/browser/themes/theme_service.cc).
- Omarchy quattro lee `~/.local/state/omarchy/current/theme/chromium.theme`, convierte su RGB en hex y llama al escritor de política. Para navegadores abiertos ejecuta `--refresh-platform-policy --no-startup-window`; contempla Chromium, Chrome, Edge y Brave. — [Aplicador Omarchy](https://github.com/omacom/omarchy/blob/quattro/bin/omarchy-theme-set-browser).
- En upstream actual, `StartupBrowserCreator::ProcessCommandLineAlreadyRunning()` detecta `kRefreshPlatformPolicy`, llama a `RefreshPlatformPolicies()` y vuelve antes de abrir otra ventana. — [Mecanismo Chromium](https://github.com/chromium/chromium/blob/main/chrome/browser/ui/startup/startup_browser_creator.cc).
- La plantilla original de Omarchy para `chromium.theme` sólo contiene `{{ background_rgb }}`. Un tema puede proporcionar su propio archivo; la estructura esperada es una tripleta RGB, no CSS, fuente ni un tema de extensión Chrome. — [Plantilla original](https://github.com/omacom/omarchy/blob/quattro/default/themed/chromium.theme.tpl); [validador de RGB](https://github.com/omacom/omarchy/blob/quattro/install/helpers/browser-policy.sh).
- El antiguo microfork **omarchy-chromium fue archivado el 7 de mayo de 2026**; su README explica que dejó de ser necesario cuando upstream mejoró el refresco de políticas. No hay que mantener aquel fork ni copiar sus opciones privadas `--set-theme-color`, `--set-user-color`, etc. como si fueran una API estable de Chromium normal. — [Repositorio y explicación de sus autores](https://github.com/omacom/omarchy-chromium).
- La política no garantiza conservar exactamente cada tono del tema: hay un informe actual de Omarchy/Chromium 151 donde un fondo crema produce amarillo fuerte por la derivación del color semilla. Es un reporte concreto, no una prueba de que falle para todos los temas. — [Issue de Omarchy #7624](https://github.com/omacom/omarchy/issues/7624).

### Inferences
- BWM podría implementar un adaptador Chromium de colores sin cierres usando la vía original de Omarchy, mantener `chromium.theme` cuando venga en un tema Retro y generar la tripleta sólo como respaldo. Esto encaja mejor con la regla de compatibilidad que inventar otro formato.
- Para default (end-4) y Breeze sería posible usar una semilla de su paleta por el mismo mecanismo común, pero **un tema generado a partir de una semilla no equivale a aplicar todos los colores Material You/Breeze**. Mantener un navegador visualmente Chromium, coloreado por cada skin, sería un objetivo razonable y verificable.

### Gaps
- No se ha hecho prueba real en este equipo: `command -v chromium chromium-browser google-chrome google-chrome-stable firefox firefox-bin` sólo encontró `/usr/bin/firefox-bin`. No se instaló ni inició Chromium.
- Omarchy escribe también `"BrowserColorScheme": "device"`; se comprobó su presencia en el script, pero no se encontró esa clave como política en el catálogo upstream consultado. No atribuirle soporte oficial ni prometer su efecto: habría que comprobar `chrome://policy` y usar el modo «dispositivo/sistema» soportado por el navegador. `BrowserColorScheme` como enum interno de C++ **sí existe**, lo que no prueba que exista como política JSON.

## ¿Cambian también las fuentes, las esquinas y las páginas?

### Takeaway
Chromium no ofrece un equivalente de `userChrome.css` para reescribir arbitrariamente sus pestañas, barra de URL y menús. La integración GTK/Qt puede seguir ajustes nativos, pero no convierte el navegador en la capa TUI mono/cuadrada que BWM dibuja en Firefox.

### Cited Findings
- Los temas oficiales Chrome son extensiones sin HTML ni JavaScript. Su manifiesto configura **images, colors, tints y properties**; estas últimas incluyen alineación/repetición del fondo y logo de nueva pestaña. La API de temas documentada no expone familia de fuente, radios de las pestañas, padding arbitrario ni CSS para el navegador. — [Documentación oficial de temas Chrome](https://developer.chrome.com/docs/extensions/develop/ui/themes).
- Instalar o habilitar una extensión de tema sí puede actualizar el tema en vivo: `ThemeObserver::OnExtensionLoaded()` llama a `DoSetTheme()`. Un tema forzado por política tiene precedencia sobre el de extensión. Por tanto, «Chrome tiene temas estáticos» **no significa que haya que cerrar Chrome para seleccionar otro**, sino que su contenido es declarativo y hay que instalar/actualizar el paquete para cambiarlo. — [ThemeService](https://raw.githubusercontent.com/chromium/chromium/main/chrome/browser/themes/theme_service.cc).
- La actualización de extensiones usa un ciclo de comprobación periódico y espera que la extensión esté inactiva; `requestUpdateCheck()` puede ser limitado por frecuencia. No es un buen sustituto de un canal inmediato de paleta para cada fondo. — [Ciclo oficial de actualizaciones](https://developer.chrome.com/docs/extensions/develop/concepts/extensions-update-lifecycle).
- En Chromium 151, `GtkUi` escucha cambios de nombre de tema, iconos y preferencia oscuro; `OnThemeChanged()` vacía cachés, llama `LoadGtkValues()` y notifica el tema nativo. `InitializeFontSettings()` obtiene la fuente GTK/Pango para las fuentes nativas. Esto demuestra un camino de integración, **no** que todos los widgets existentes regeneren su fuente en vivo. — [GTK de Chromium 151](https://raw.githubusercontent.com/chromium/chromium/151.0.7922.169/ui/gtk/gtk_ui.cc).
- `QtUi::FontChanged()` invalida los ajustes de fuente y `ThemeChanged()` actualiza el tema Qt nativo. Los datos Qt se usan para colores, fuentes y algunos diálogos, pero la UI de pestañas y barra continúa siendo Chromium. — [Qt de Chromium 151](https://raw.githubusercontent.com/chromium/chromium/151.0.7922.169/ui/qt/qt_ui.cc).
- `LinuxUi::GetDefaultFontDescription()` mantiene una caché; `PlatformFontSkia` también tiene una fuente predeterminada cacheada que puede recargarse. Esto es otra razón para no inferir de una señal GTK/Qt que toda la interfaz abierta cambia instantáneamente de fuente. — [LinuxUi](https://github.com/chromium/chromium/blob/main/ui/linux/linux_ui.cc); [fuentes Skia 151](https://github.com/chromium/chromium/blob/151.0.7922.169/ui/gfx/platform_font_skia.cc).
- Los content scripts de Chrome corren en páginas web. `chrome.fontSettings` configura familias genéricas por idioma/script del contenido; no es un mecanismo para cambiar la tipografía de los controles de pestañas. — [Content scripts](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts); [fontSettings](https://developer.chrome.com/docs/extensions/reference/api/fontSettings).
- La integración Linux se elige según toolkit/entorno y bibliotecas compiladas; no basta con que haya kdeglobals. El factory puede escoger GTK, Qt o fallback, y respeta `--ui-toolkit`. — [Factory upstream](https://github.com/chromium/chromium/blob/main/ui/linux/linux_ui_factory.cc).
- En el equipo, el ebuild Chromium 151.0.7922.169-r1 usa GTK y habilita Qt6 sólo si el USE `qt6` está activo. Es configuración de compilación disponible, no confirmación de un binario Chromium ni de que BWM gestione su toolkit. — [Ebuild local](/var/db/repos/gentoo/www-client/chromium/chromium-151.0.7922.169-r1.ebuild:1350).

### Inferences
| Parte que debe seguir a la skin | Chromium estándar sin cerrar | Alcance real |
| --- | --- | --- |
| Color general del navegador | Sí, vía BrowserThemeColor | Paleta derivada por Chromium; no todos los hex exactos de la skin. |
| Claro/oscuro | Diseñado para seguir sistema/portal o preferencia interna | Hay que validar configuración activa; no confiar en `BrowserColorScheme` sin comprobar. |
| Familia tipográfica de todos los controles | Sin garantía demostrada | GTK/Qt aportan fuente nativa; falta verificar en ventanas ya abiertas y toolkit usado. |
| Pestañas y URL cuadradas/mono tipo TUI | No con la política o manifiesto estándar estudiados | Requeriría parche/fork del navegador o renunciar a esa transformación. |
| Borde exterior/redondeo/sombra de la ventana | Sí, compositor BWM/Hyprland | Es independiente del navegador y no cambia formas internas. |
| Nueva pestaña | El tema puede colorear y aportar imagen | No convierte todas las páginas web al tema; políticas y extensiones tienen prioridades distintas. |
| Webs normales | Sólo preferencias como claro/oscuro que cada web respete | Recolorear arbitrariamente páginas exige extensiones de contenido; es otro problema. |
| Diálogos de archivos/impresión | Posible integración GTK/Qt/portal | La política de color del navegador no los tematiza por sí misma. |

La tabla sintetiza las fuentes anteriores y distingue capacidades documentadas de garantías todavía no probadas.

### Gaps
- No se ha probado en vivo un cambio Google Sans Flex ↔ JetBrains Mono ni Breeze ↔ GTK en Chromium. No afirmar que se necesitan reinicios para toda fuente; tampoco prometer ausencia de ellos si se exige esa transformación completa.
- No se auditó cada fork Chromium. Las conclusiones se refieren al estándar, no a Vivaldi u otros que añaden interfaces y APIs propias.

## ¿Qué implica para BWM y qué opción conviene?

### Takeaway
No recomendaría una migración obligatoria sólo para arreglar el reinicio. Chromium tiene una solución estándar simple si aceptamos su propia forma y sólo lo coloreamos; Firefox ya tiene colores vivos en BWM y permite conservar mayor control de la forma con una mejora del puente, pendiente de implementar y probar.

### Cited Findings
- El writer actual de Omarchy usa rutas fijas bajo `/etc/.../policies/managed`, escritura como root con `sudo`/`pkexec`, validación estricta de seis hex y fichero `root:root` modo 0644. Los directorios de política se mantienen `root:root` 0755. **No copiar el antiguo `chmod a+rw`** que aparece en algunas búsquedas/documentación histórica. — [Writer privilegiado original](https://github.com/omacom/omarchy/blob/quattro/bin/omarchy-theme-set-browser-policy); [instalación y endurecimiento](https://github.com/omacom/omarchy/blob/quattro/install/helpers/browser-policy.sh).
- BWM declara explícitamente Chromium como aún no portado, porque su política necesita root, y el navegador tematizado recomendado hoy es Firefox. — [Plantillas de apps BWM](/mnt/HDD1TB/Projects/hyprland-de/config/hypr/scripts/bwm_omarchy_apps.py:19); [requisitos actuales](/mnt/HDD1TB/Projects/hyprland-de/config/hypr/skins/requirements.json:348).
- Omarchy actual usa Chromium por defecto, permite instalar Chrome/Edge/Brave/Firefox/Zen y advierte que Firefox/Zen no reciben su tematización ni extensiones Chromium. Por tanto BWM ya ofrece una capa Firefox adicional a lo que hace el original. — [Manual original de navegadores](https://github.com/omacom/omarchy/blob/quattro/manual/23-browsers.md).
- La forma TUI de Firefox en BWM es código propio: fuerza fuente JetBrains Mono, radios cero, tab/URL/paneles cuadrados y contornos. Eso excede lo que describe `chromium.theme` de Omarchy. — [Overlay Firefox BWM](/mnt/HDD1TB/Projects/hyprland-de/config/hypr/omarchy/overlays/firefox.css:1).

### Inferences
- Si el requisito principal es **que el navegador nunca se cierre por cambiar skin**, BWM debería empezar por suprimir el reinicio automático del navegador y preservar lo que ya puede cambiar vivo. La decisión del navegador predeterminado puede mantenerse independiente y compartida entre skins.
- Si se quiere seguir fielmente el comportamiento original de Omarchy, añadir soporte opcional Chromium aporta valor: colores vivos y compatibilidad `chromium.theme`, sin forzar migración. Se necesita instalación de helper privilegiado por el usuario; nunca escribir root desde un checkout editable sin validar.
- Si además se exige la tipografía y geometría Retro cambiando en vivo, migrar a Chromium **no resuelve ese requisito** con las vías estándar investigadas. El puente Firefox propuesto por el investigador hermano (CSS precargado condicionado por un marcador dinámico de Theme API) merece una prueba acotada antes de cambiar de navegador. Su coste es mantenimiento específico de Firefox; Chromium evitaría ese coste sólo aceptando menos cambios internos.
- Prueba de aceptación futura: dos perfiles desechables, PID de navegador constante, audio/vídeo continuo, ninguna pérdida de foco/workspace al pasar default ↔ Retro ↔ Breeze, comprobar colores exactos, fuentes, radios internos, NTP y diálogos por separado. No se ejecutó durante esta investigación.

### Gaps
- Esta investigación no instala ni cambia el navegador predeterminado ni demuestra la solución Firefox. La conclusión técnica Chromium se basa en código y documentación primaria, no en una prueba visual local.
