# Stremio y Steam: alcance de los temas

## Stremio Linux (Flatpak)

La versión probada es `com.stremio.Stremio` 1.2.2, basada en GTK 4, libadwaita y
WebKitGTK. El antiguo `stremio-shell` sí utilizaba Qt. Los colores de qt6ct no
cambian ninguna de las dos interfaces web.

BWM genera `~/.local/state/bwm/stremio/theme.css` con la plantilla matugen
`stremio.css`. Default usa la paleta de matugen, Plasma la paleta Breeze y Retro
la paleta estática o dinámica más `omarchy/overlays/stremio.css`.

`stremio-theme.py`, como post_hook, configura sólo este Flatpak: permite leer
el directorio de scripts y el de la paleta, y añade `stremio-theme.cjs` a
`NODE_OPTIONS`. Conserva los argumentos NODE_OPTIONS definidos para la app.
Sólo se crean overrides si Flatpak y Stremio están instalados. `install.sh` llama
a `--setup-only` sin reiniciar ventanas; los cambios de tema vuelven a comprobar
la instalación, incluso al reaplicar una paleta estática sin cambios. Si se instala
Stremio después, reaplica el tema para activar la integración.

El módulo sólo se activa en `/app/libexec/stremio/server.js`. Añade un script
al HTML inicial que el servidor oficial ya sirve desde
`/proxy/d=https%3A%2F%2Fweb.stremio.com/`. Ese script lee los colores cada dos
segundos. Se mantiene el origen de la web, sus datos de sesión y sus API.
Los vídeos, imágenes, otros destinos del proxy y los archivos del Flatpak no
se modifican. No se instala otro servidor ni se abre otro puerto.

Al preparar la integración por primera vez, se reabre la ventana en su
workspace. No se reinicia si está en pantalla completa o MPRIS indica
reproducción; en ese caso se activa al próximo arranque. Después, los cambios
de colores y el estilo web son en vivo. El marco GTK sigue leyendo su CSS al
arrancar. La posición exacta en el mosaico puede variar tras ese primer reinicio.

### Límites y recuperación

Esta integración es específica del servidor y la ruta de inicio actuales de
Stremio Linux; no es una API oficial de temas. Una actualización que cambie
esa ruta puede dejar de aplicar el CSS. Ante respuestas desconocidas se
conserva el contenido original.

Para desactivarla, elimina únicamente el argumento
`--require="…/stremio-theme.cjs"` de NODE_OPTIONS del override de esta app.
Si no había otros argumentos (caso de esta instalación), basta:

```bash
flatpak override --user --unset-env=NODE_OPTIONS --unset-env=BWM_STREMIO_CSS com.stremio.Stremio
```

Después reinicia Stremio. El post_hook la volverá a preparar al cambiar el
tema; para desactivarla de forma permanente, quita también el post_hook de
`templates.stremio` en `config/matugen/config.toml`.

### Validación

Pruebas del puente HTTP (Node del propio Flatpak; no abre la interfaz):

```bash
flatpak run --command=node \
  --filesystem="$PWD/config/hypr/scripts:ro" com.stremio.Stremio \
  --test "$PWD/config/hypr/scripts/tests/stremio-theme.test.cjs"
```

Cubren HTML normal y comprimido (gzip, deflate, Brotli), conservación de
respuestas ajenas, errores, límite de tamaño y lectura de nuevas paletas.
La comprobación visual inicial y el cambio de paleta en vivo se hacen aparte.

## Steam

Steam usa CEF, no Qt. BWM aplica Adwaita-for-Steam a la barra del cliente,
biblioteca y diálogos, y reinicia Steam salvo que haya un juego abierto.
La Tienda y la Comunidad son páginas web y quedan fuera de este método.
No confundir su fondo sin cambios con un fallo de la paleta del cliente.

Verificado el 2026-10-26 con Ethereal: CSS generado y CSS instalado coinciden;
la barra del cliente muestra sus colores. La Tienda mantiene su propio diseño. Se comprobó también el cambio real de la
barra superior a Tokyo Night tras reiniciar Steam y se restauró Ethereal.
`steam-theme.sh` conserva los errores de instalación y reinicio en
`~/.local/state/bwm/steam/{install,restart}.log`; no reinicia si el instalador falla. El hook espera al reinicio, sin lanzar otro
proceso desligado que dé por terminado el trabajo antes de tiempo.

Fuentes: [Stremio Linux](https://github.com/Stremio/stremio-linux-shell),
[Stremio Web](https://github.com/Stremio/stremio-web),
[limitaciones de Adwaita-for-Steam](https://github.com/tkashkin/Adwaita-for-Steam#limitations).

En Retro, `omarchy/overlays/steam.css` hace que la barra superior use el fondo
base del tema, como el escritorio. El template compartido conserva la superficie
elevada para Default y Plasma. Esto corrige la diferencia entre `#131a3a` y
`#060b1e` que se veía en Ethereal.
