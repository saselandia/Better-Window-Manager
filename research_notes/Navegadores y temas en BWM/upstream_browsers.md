# Navegadores de los originales de BWM

## Qué usa end 4 y qué parte de Firefox es propia de BWM

### Takeaway
end-4 no exige Firefox ni Chromium: su lanzador elige el primer navegador instalado de una lista que empieza por Chrome. La tematización Firefox/Pywalfox y la forma TUI que BWM añade a Firefox no son una obligación de compatibilidad con end-4 u Omarchy.

### Cited Findings
- Baseline consultado en vivo: `end-4/dots-hyprland`, rama `main`, commit `2f2a376fdb2ad738bf55f693dd0b474b64bb0ab8`. La API GitHub devolvió ese HEAD y `pushed_at=2026-10-11T02:48:36Z` durante esta investigación (fecha del usuario: 2026-11-08). Se mantiene el baseline documentado por BWM. — [Repositorio y árbol fijados](https://github.com/end-4/dots-hyprland/tree/2f2a376fdb2ad738bf55f693dd0b474b64bb0ab8)
- `dots/.config/hypr/hyprland/variables.lua:11` define el lanzador con este orden: `google-chrome-stable`, `zen-browser`, `firefox`, `brave`, `chromium`, `microsoft-edge-stable`, `opera`, `librewolf`. Es una selección del primero disponible, no una declaración de que todos se instalan ni un mandato de navegador único. — [variables.lua fijado](https://github.com/end-4/dots-hyprland/blob/2f2a376fdb2ad738bf55f693dd0b474b64bb0ab8/dots/.config/hypr/hyprland/variables.lua#L7-L12)
- El `matugen/config.toml` oficial tiene plantillas de colores del shell, Hyprland, hyprlock, fuzzel, GTK 3/4, KDE y fondo. No incluye plantilla Firefox, Chromium ni Pywalfox. — [matugen oficial](https://github.com/end-4/dots-hyprland/blob/2f2a376fdb2ad738bf55f693dd0b474b64bb0ab8/dots/.config/matugen/config.toml)
- `switchwall.sh` oficial llama a `kde-material-you-colors-wrapper.sh`, al aplicador de colores de código y al aplicador de terminales; establece tema GTK y preferencia claro/oscuro. Los archivos completos `switchwall.sh` y `applycolor.sh` consultados no añaden un mecanismo específico de Firefox ni reinician navegadores. — [switchwall.sh](https://github.com/end-4/dots-hyprland/blob/2f2a376fdb2ad738bf55f693dd0b474b64bb0ab8/dots/.config/quickshell/ii/scripts/colors/switchwall.sh), [applycolor.sh](https://github.com/end-4/dots-hyprland/blob/2f2a376fdb2ad738bf55f693dd0b474b64bb0ab8/dots/.config/quickshell/ii/scripts/colors/applycolor.sh)
- end-4 ofrece `plasma-browser-integration` como dependencia opcional de Arch. El instalador explica que sirve para mostrar el tiempo de reproducción de Firefox en el widget multimedia. No es Pywalfox ni tematización. — [install-deps.sh:127–145](https://github.com/end-4/dots-hyprland/blob/2f2a376fdb2ad738bf55f693dd0b474b64bb0ab8/sdata/dist-arch/install-deps.sh#L127-L145)
- BWM sí tiene plantilla Firefox y un hook Pywalfox, además de su propia capa TUI identificada explícitamente como BWM. — [config/matugen/config.toml local](/mnt/HDD1TB/Projects/hyprland-de/config/matugen/config.toml:33), [overlay Firefox local](/mnt/HDD1TB/Projects/hyprland-de/config/hypr/omarchy/overlays/firefox.css:2)

### Inferences
- Mantener Firefox no perjudica la compatibilidad esencial de default (end-4). Adoptar Chromium tampoco es un requisito de fidelidad de esa skin.
- La forma TUI de Firefox en Retro es un añadido BWM: renunciar a imponerla inmediatamente no supone perder una función de tematización que Omarchy original ofrezca para Firefox.

### Gaps
- No se ha demostrado que end-4 jamás utilizara Pywalfox en otras ramas o versiones históricas. La conclusión se limita al HEAD actual comprobado y a la cadena de generación de color examinada.
- No se han hecho pruebas visuales de Chrome o Firefox con GTK/Qt en el end-4 original. Su soporte real de colores del sistema debe distinguirse de una garantía de que todo el navegador tendrá colores exactos del fondo.

## Qué usa Omarchy quattro y qué significa su tema de Chromium

### Takeaway
Omarchy sí incluye Chromium como navegador base y por defecto, y cambia su color en vivo mediante políticas. Esto no equivale a la transformación TUI con fuentes monoespaciadas y esquinas de Firefox en BWM: su interfaz sigue siendo la de Chromium y recibe un color semilla más el esquema claro/oscuro del sistema.

### Cited Findings
- Baseline actual comprobado por API: `basecamp/omarchy`, rama por defecto `quattro`, commit `598e4ebc510b1cf69eb2b2188f938664f1feb1ec`, `pushed_at=2026-11-08T00:15:11Z`. — [árbol fijado](https://github.com/basecamp/omarchy/tree/598e4ebc510b1cf69eb2b2188f938664f1feb1ec)
- La documentación oficial dice que Chromium es el navegador por defecto y forma parte del sistema base; permite instalar Chrome, Edge, Brave, Brave Origin, Firefox y Zen. Instalar uno no lo hace predeterminado: se selecciona aparte. La misma página dice expresamente que Firefox y Zen no se tematizan por Omarchy y no reciben sus extensiones de Chromium. — [Manual oficial: Browsers](https://omarchy.org/manual/browsers/)
- El paquete `chromium` está en la lista base del instalador. — [omarchy-base.packages:16](https://github.com/basecamp/omarchy/blob/598e4ebc510b1cf69eb2b2188f938664f1feb1ec/install/omarchy-base.packages#L16)
- `default/themed/chromium.theme.tpl` contiene únicamente `{{ background_rgb }}`. Algunos temas llevan una sustitución explícita: `themes/retro-82/chromium.theme` contiene `0,23,46`. Son canales RGB, no una extensión de tema completa ni un descriptor de fuentes/esquinas. — [plantilla](https://github.com/basecamp/omarchy/blob/598e4ebc510b1cf69eb2b2188f938664f1feb1ec/default/themed/chromium.theme.tpl), [Retro-82](https://github.com/basecamp/omarchy/blob/598e4ebc510b1cf69eb2b2188f938664f1feb1ec/themes/retro-82/chromium.theme)
- `omarchy-theme-set-browser` lee ese archivo, prepara `BrowserThemeColor` y `BrowserColorScheme: device`, evita una escritura si el resultado ya coincide y, después de aplicar la política, envía `--refresh-platform-policy --no-startup-window` a los navegadores abiertos. No los mata/reinicia. Reconoce Chromium, Chrome, Edge y Brave, con manejo separado de Brave Origin. — [script oficial](https://github.com/basecamp/omarchy/blob/598e4ebc510b1cf69eb2b2188f938664f1feb1ec/bin/omarchy-theme-set-browser)
- La escritura es privilegiada: `omarchy-theme-set-browser-policy` exige un argumento de seis dígitos hexadecimales y escribe archivos `root:root`, modo 0644, en directorios de políticas existentes. Rutas separadas: `/etc/chromium/policies/managed`, `/etc/opt/chrome/policies/managed`, `/etc/opt/edge/policies/managed`, `/etc/brave/policies/managed`. Usa sudo o pkexec; una regla sudoers del paquete puede autorizar la operación limitada sin contraseña. — [escritor de políticas](https://github.com/basecamp/omarchy/blob/598e4ebc510b1cf69eb2b2188f938664f1feb1ec/bin/omarchy-theme-set-browser-policy)
- El instalador de navegadores crea directorios de políticas por producto y aplica el tema a la familia Chromium. Para Firefox/Zen instala políticas de preferencias y activa Wayland, sin ejecutar la tematización de Chromium. — [omarchy-install-browser](https://github.com/basecamp/omarchy/blob/598e4ebc510b1cf69eb2b2188f938664f1feb1ec/bin/omarchy-install-browser)
- Las políticas Firefox originales son preferencias de overscroll, VA-API/decodificación y escalado Wayland, no colores ni CSS TUI. — [policies.json Firefox](https://github.com/basecamp/omarchy/blob/598e4ebc510b1cf69eb2b2188f938664f1feb1ec/default/firefox/policies.json)
- BWM ya documenta que su soporte Chromium está pendiente por necesitar root. Su investigación previa describe correctamente la política de color; no la ha portado. — [docs/SKINS.md:56](/mnt/HDD1TB/Projects/hyprland-de/docs/SKINS.md:56), [investigación local:102](/mnt/HDD1TB/Projects/hyprland-de/docs/OMARCHY_INVESTIGACION.md:102)

### Inferences
- Chromium ofrece una ruta real y usada por el original para cambios de color sin cierre. Es una buena opción adicional para completar compatibilidad Retro y sus `chromium.theme` explícitos.
- Migrar sólo para resolver cierres de Firefox no elimina el problema conceptual: BWM debe definir si busca color en vivo o transformación profunda del navegador. La política original demuestra lo primero; no lo segundo.
- Portar el mecanismo requeriría adaptación al Gentoo real (rutas/política/paquete instalado), un ayudante privilegiado instalado por el usuario y respeto de las reglas del proyecto: el asistente no puede ejecutar sudo. No debe convertir directorios de políticas en escribibles por el usuario.
- Navegador predeterminado se mantiene común entre skins según AGENTS.md; no conviene reemplazarlo automáticamente al entrar en Retro sólo porque Chromium sea el predeterminado original.

### Gaps
- No se ejecutó Chromium ni se comprobó en esta máquina el efecto de `--refresh-platform-policy`. La evidencia de no cierre es el mecanismo fuente de Omarchy, no una prueba local.
- Las rutas anteriores son las de Omarchy/Arch; deben verificarse en el binario Gentoo antes de implementar. Chromium y Google Chrome no son el mismo paquete.

## Qué navegador exige KDE Plasma y qué aporta su integración

### Takeaway
Plasma es un escritorio, no una distribución que imponga un único navegador. Firefox y Chromium/Chrome son opciones compatibles; la integración de Plasma trata de multimedia, pestañas, descargas y enlaces, no de reescribir el aspecto del navegador para que imite Breeze.

### Cited Findings
- La página oficial identifica Plasma como escritorio y ofrece configuración visual y de aplicaciones. No declara Chromium como navegador obligatorio. — [Plasma oficial](https://kde.org/plasma-desktop/)
- El módulo oficial Default Applications permite elegir el navegador favorito o cualquier aplicación. La revisión de esa documentación es Plasma 5.24, 2022-01-12; respalda el modelo de selección, no un defecto actual concreto por distribución. — [Default Applications](https://docs.kde.org/trunk_kf6/en/plasma-workspace/kcontrol/componentchooser/index.html)
- KDE ofrece Falkon como navegador Qt propio, disponible como aplicación independiente; ello no lo convierte en el predeterminado universal de Plasma. — [Falkon oficial](https://apps.kde.org/falkon/)
- La extensión oficial KDE para Firefox gestiona audio/vídeo, notificaciones de descargas, KDE Connect y pestañas/KRunner. Requiere el paquete nativo `plasma-browser-integration`. — [Plasma Integration, publicada por KDE en Mozilla](https://addons.mozilla.org/en-US/firefox/addon/plasma-integration/)
- KDE Connect documenta integración de Firefox y Google Chrome para compartir enlaces y controlar multimedia. — [KDE Connect oficial](https://kdeconnect.kde.org/)
- El manifiesto actual de Plasma Browser Integration contiene nativeMessaging, downloads, tabs, scripting, contextMenus e history y módulos mpris/downloads/tabsrunner; no contiene API de tema que aplique Breeze al chrome del navegador. — [manifest.json oficial KDE](https://github.com/KDE/plasma-browser-integration/blob/master/extension/manifest.json)
- KDE anunció en octubre de 2026 mejoras de descargas Firefox y soporte Brave para su integración. Por tanto hay soporte activo de más de una familia; no un mandato Chromium. — [This Week in Plasma, 2026-10-24](https://blogs.kde.org/2026/10/24/this-week-in-plasma-fixing-all-the-bugs-pip-and-performance/)

### Inferences
- Breeze en BWM no obliga a migrar a Chromium ni a Falkon. La elección debe evaluarse por continuidad de navegación y alcance de tematización, no por una supuesta obligación del escritorio original.
- Un tema global de Plasma no implica necesariamente que Firefox o Chromium sustituyan su distribución interna por un diseño Breeze idéntico. Colores GTK/Qt, esquema oscuro y decoración del compositor son capas distintas de la interfaz interna del navegador.

### Gaps
- No se inventaría una lista de navegador por defecto de cada distribución KDE: depende de la distribución y versión. No es necesaria para responder qué exige Plasma como original de la skin.
- No se han probado aquí Firefox/Chromium sobre una sesión Plasma original ni se ha investigado en profundidad la recarga GTK/Qt interna de cada navegador (otro investigador cubre esa mecánica).
