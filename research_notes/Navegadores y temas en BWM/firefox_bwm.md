# Firefox y temas sin reinicios en BWM

## Qué provoca hoy el cierre de Firefox

### Takeaway
El cierre automático es una decisión explícita de BWM para aplicar la forma de Retro, no una exigencia de cambiar colores en Firefox. Actualmente se programa al entrar o salir de Retro; cambiar un tema dentro de Retro, cambiar un fondo o pasar de default a Breeze no debería programarlo desde el código revisado.

### Cited Findings
- `bwm-theme-manager.py`, líneas 951–964, conserva un comentario antiguo que promete no cerrar el navegador, pero acto seguido, si `(theme_name == "retro") != (curr_theme == "retro")`, lanza `bwm_omarchy.py restart-firefox --after-switch` sin `BWM_SKIN_SWITCH`. No se trata de una caída del navegador: es cierre y relanzamiento deliberados. [Código local](/mnt/HDD1TB/Projects/hyprland-de/config/hypr/scripts/bwm-theme-manager.py:951)
- `restart_firefox(after_switch=True)` espera a que termine la transición, comprueba que Firefox ya existía y fuerza el reinicio. `restart_app` envía SIGTERM y lo relanza; intenta recuperar sesión, workspaces y posiciones, pero eso no preserva una llamada, reproducción o estado efímero de una página. El historial local reconoce además cambios de reparto del mosaico y una ventana emparejada por título equivocadamente. [Implementación](/mnt/HDD1TB/Projects/hyprland-de/config/hypr/scripts/bwm_omarchy.py:1409), [reinicio](/mnt/HDD1TB/Projects/hyprland-de/config/hypr/scripts/bwm_omarchy.py:1202), [historial §3.82–85](/mnt/HDD1TB/Projects/hyprland-de/BWM_CONTEXT.md:910)
- La búsqueda `rg restart-firefox|restart_firefox config` encontró como lanzador automático solamente ese bloque del gestor, además de la definición y la entrada CLI manual. Esto cubre el repositorio, no posibles hooks particulares del usuario; no se inspeccionaron datos privados. [Gestor](/mnt/HDD1TB/Projects/hyprland-de/config/hypr/scripts/bwm-theme-manager.py:957)
- La paleta se genera en `~/.cache/material-you-firefox.css`; `userChrome.css` la importa, y Retro añade al contenido generado la capa `overlays/firefox.css` con fuente monoespaciada, radios cero y otros cambios de geometría. BWM sustituye así reglas que Firefox ya cargó. El instalador copia `userChrome.css` a los perfiles y enlaza `material-you.css` a la paleta. [Aplicador](/mnt/HDD1TB/Projects/hyprland-de/config/hypr/scripts/bwm_omarchy.py:422), [CSS](/mnt/HDD1TB/Projects/hyprland-de/config/firefox/userChrome.css:10), [Retro](/mnt/HDD1TB/Projects/hyprland-de/config/hypr/omarchy/overlays/firefox.css:8), [instalador](/mnt/HDD1TB/Projects/hyprland-de/install.sh:312)
- Los colores principales sí utilizan las variables de tema que Pywalfox cambia en ejecución; `matugen/config.toml` llama `pywalfox update` después de generar `wal/colors.json`. Pywalfox declara que utiliza la API oficial de temas y ofrece actualización desde CLI. [Hook local](/mnt/HDD1TB/Projects/hyprland-de/config/matugen/config.toml:33), [Pywalfox original](https://github.com/Frewacom/pywalfox)
- El historial §3.83 documenta una prueba real: pestañas, URL y marcadores cambiaron de color al ejecutar Pywalfox, sin reiniciar Firefox. No se ha repetido durante esta investigación. [Prueba documentada](/mnt/HDD1TB/Projects/hyprland-de/BWM_CONTEXT.md:919)
- **Matiz importante:** el overlay Retro sigue usando numerosas `--mat-primary`, `--mat-outline` y `--mat-surface` como primera opción. Esas variables vienen del archivo leído al arrancar, de modo que no todos los acentos, bordes y detalles están garantizados en vivo aunque sí cambien el fondo y otras superficies. Conviene corregir esa dependencia al implementar una mejora. [Overlay, líneas 39–93](/mnt/HDD1TB/Projects/hyprland-de/config/hypr/omarchy/overlays/firefox.css:39)
- Se leyó la versión instalada mediante `firefox-bin --version`: **Mozilla Firefox 158.0.1**. No se abrió ninguna ventana ni se accedió al historial. [Binario instalado](/usr/bin/firefox-bin)

### Inferences
- Si Firefox también se cierra al cambiar únicamente de fondo o tema dentro de Retro, habría que registrar el disparador concreto: el repositorio revisado ya no contiene ese reinicio automático, retirado en §3.83. No conviene aceptar sin diagnóstico que cualquier tematización obliga a cerrar Firefox.
- El problema inmediato se puede eliminar conservando Firefox: quitar el relanzamiento posterior a la transición deja los colores vivos y la forma/fuente del arranque anterior hasta que el usuario decida cerrar el navegador. Es una solución pequeña y verificable, con una renuncia visual explícita.

### Gaps
- No se probó una transición completa ni se cambió el tema del usuario. No se confirmó que toda la paleta Retro responda en vivo, especialmente los detalles que aún leen `--mat-*`.
- No se inspeccionaron hooks de usuario ni procesos/URL abiertos, por privacidad y porque no eran necesarios para explicar el código.

## Puede Firefox cambiar también forma y fuente sin reiniciar

### Takeaway
Hay una vía técnica razonable: cargar todas las variantes CSS una sola vez y activar cada variante mediante un marcador del tema que Firefox ya actualiza en vivo. La API normal no permite enviar CSS arbitrario, fuentes o radios, pero eso no impide que una hoja precargada reaccione a cambios del DOM generados por esa API.

### Cited Findings
- `browser.theme.update()` cambia el tema en todas las ventanas si no se limita por ID y requiere permiso `theme`. El objeto sigue el esquema de `theme` del manifiesto: colores, imágenes y propiedades específicas; no incluye una propiedad general para fuente o CSS. [API update](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/theme/update), [tipo Theme](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/theme/Theme), [esquema](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/theme)
- `LightweightThemeConsumer.sys.mjs` actualiza en el elemento raíz `lwtheme-image` según exista `headerImage`; también escribe `--lwt-header-image` en el atributo `style`. El código instalado 158.0.1 coincide: líneas 428, 459 y 677. Esto ofrece una señal independiente de los colores. `theme-effective-id` existe, pero identifica el tema/extensión efectivo y no distingue payloads de skins de una misma extensión. [Fuente Firefox](https://searchfox.org/firefox-main/source/toolkit/modules/LightweightThemeConsumer.sys.mjs), [archivo instalado](/opt/firefox/omni.ja)
- El XPI **Pywalfox 2.1.1** que distribuye BWM llama, en `dist/background.js`, `browser.theme.update({colors:e,properties:{color_scheme:s,content_color_scheme:s}})`. No incluye imágenes. Añadir una clave al JSON de paleta o reescribir un CSS en disco no basta para que ese XPI emita un marcador. [XPI local](/mnt/HDD1TB/Projects/hyprland-de/config/firefox/extensions/pywalfox@frewacom.org.xpi), [proyecto upstream MPL-2.0](https://github.com/Frewacom/pywalfox)
- Firefox dispone de Native Messaging: una extensión puede mantener un puerto hacia un programa local e intercambiar JSON con él. BWM ya usa ese mecanismo con Pywalfox. [Mozilla Native Messaging](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Native_messaging), [registro local](/mnt/HDD1TB/Projects/hyprland-de/install.sh:337)
- Una extensión ordinaria no puede inyectar content scripts en la interfaz privilegiada del navegador como si fuese una página web. No serviría instalar Stylus y tratar la barra de Firefox como CSS de una página. [Límites de content scripts](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Content_scripts)
- Las versiones de publicación/beta exigen extensiones firmadas por Mozilla, también si se distribuyen fuera de AMO. Un fork no se resuelve editando silenciosamente el XPI firmado actual. [Distribución de extensiones](https://extensionworkshop.com/documentation/publish/signing-and-distribution-overview/)

### Inferences
- **Diseño candidato, todavía no probado:** hoja fija con el aspecto base y selectores de Retro, por ejemplo `:root[style*="bwm-skin-retro"] ...`; la extensión enviaría como `theme_frame` una imagen transparente empaquetada con ese nombre. Al cambiar a otra skin retira o sustituye esa imagen. Los radios y fuentes vendrían de reglas CSS ya cargadas, sin tocar la sesión. Para dos formas basta `lwtheme-image`, pero seleccionar el nombre preciso evita confundir cualquier tema con imagen con Retro y permite tres variantes futuras.
- Este marcador puede convivir con `color_scheme: light/dark/system` y con cualquier paleta de Omarchy: **no usar el modo claro/oscuro como señal de Retro**, puesto que Retro tiene temas claros y oscuros.
- Exigiría un pequeño fork del componente Firefox de Pywalfox y su comunicación nativa, una mejora aceptada upstream o un puente propio que sea el único dueño del tema. Dos extensiones llamando `theme.update` pueden sobrescribirse; una segunda extensión que simplemente reaccione y vuelva a emitir el tema añade posibles bucles y carreras.
- Se conservarían las paletas originales Omarchy, el generador matugen y los `.colors` de Plasma al adaptar sus datos al navegador. El marcador sería transporte interno de estado, no un nuevo formato de tema que la comunidad deba adoptar. Un fork debe conservar MPL-2.0, avisos y fuente correspondiente; BWM ya declara ese origen en `THIRD_PARTY_NOTICES.md`.
- El marcador se pierde o cambia si el usuario elige un tema del navegador o una extensión distinta toma control. El diseño debe respetar esa elección: detectar salida de control BWM y dejar aspecto base, o comunicar que el navegador está desacoplado del tema del sistema. No conviene secuestrar continuamente el tema del usuario.
- Incluso con un nombre preciso se depende de detalles internos del DOM de Firefox: `--lwt-header-image`, atributos y selectores. BWM ya depende de ellos para sus colores; se necesitan pruebas al actualizar Firefox y una degradación segura. No llamarlo una solución lista ni oficialmente garantizada por Mozilla.

### Gaps
- No se hizo una prueba visual de imagen transparente y cambio de variante CSS con la sesión real. El enlace API → marcador está confirmado en el código instalado; la integración completa BWM/Pywalfox es una propuesta.
- No se verificó recarga en todas las ventanas privadas; debe probarse si se implementa, respetando los permisos de extensión.
- Firefox permite temas experimentales con privilegios/restricciones adicionales, pero no se investigó como vía recomendada: el marcador y CSS precargado evitan basar el producto en desactivar restricciones del navegador.

## Alternativas sencillas y recomendación para BWM

### Takeaway
No recomendaría migrar de navegador únicamente para evitar este reinicio: BWM puede dejar de ordenar el cierre de Firefox ya mismo, y la forma viva tiene una vía plausible de implementación. La decisión de adoptar Chromium debería comparar también el nivel de personalización que se pretende conservar.

### Cited Findings
- Mozilla documenta que la fuente raíz del chrome viene de la fuente de interfaz del sistema (`font: message-box`); algunos menús la restablecen como `menu` u otras fuentes del sistema. [Guía CSS Firefox](https://firefox-source-docs.mozilla.org/code-quality/coding-style/css_guidelines.html)
- El backend GTK de Firefox observa `gtk-font-name`. Su callback notifica cambios de estilo y disposición a todas las ventanas; `NativeGetFont` toma las fuentes del tema de GTK. [Código GTK de Firefox](https://searchfox.org/firefox-main/source/widget/gtk/nsLookAndFeel.cpp)
- El overlay Retro actual fuerza una familia literal para todos los elementos del chrome (`JetBrainsMono Nerd Font`), anulando esa herencia. [CSS Retro](/mnt/HDD1TB/Projects/hyprland-de/config/hypr/omarchy/overlays/firefox.css:8)

### Inferences
- **Alternativa intermedia:** eliminar esa familia literal y dejar heredar la fuente GTK, junto con una geometría común para todas las skins. Puede permitir fuente y colores vivos sin mantener una extensión modificada. Hay base clara en el código de GTK; aún hay que verificar cómo llega la fuente de BWM a GtkSettings en esta sesión Wayland. No soluciona por sí sola los radios, marcos y disposiciones específicas de Retro.
- **Orden recomendado:** (1) priorizar continuidad y eliminar reinicios cosméticos; (2) decidir si la forma debe cambiar de inmediato o si basta color y fuente sistema; (3) si se exige fidelidad completa, prototipo aislado del marcador y CSS fijo; (4) sólo después evaluar migración con el mismo criterio de fidelidad, pues colorear Chromium no equivale a transformar su geometría libremente.
- Las pruebas de aceptación adecuadas son: alternar temas claros/oscuros en Retro y las tres skins mientras se reproduce vídeo o mantiene una llamada; comprobar mismo PID principal, ventanas/workspaces y reproducción; revisar fuente, radios y todas las superficies; probar elección manual de un tema de navegador y nueva ventana. No se han realizado en esta investigación.

### Gaps
- Esta investigación sólo analiza Firefox/BWM. La comparación con Chromium y los escritorios originales corresponde a las otras notas del informe.
- No se cambiaron archivos del producto, perfiles, preferencias, configuración de usuario ni estado del escritorio. Se creó únicamente esta nota de investigación.
