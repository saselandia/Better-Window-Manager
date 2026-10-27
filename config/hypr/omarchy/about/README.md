# About de Omarchy en el menú Retro

Fastfetch, no una recreación QML: logo ASCII de Omarchy, bloques Hardware,
Software y Age / Uptime / Update, colores ANSI del tema de terminal, tamaño
ajustado al contenido y brillo animado que recorre el logo. Cualquier tecla cierra
la ventana. Otra invocación enfoca la existente.

Sólo la entrada «Acerca de» del menú Retro usa esta presentación. About de
Settings conserva su diseño BWM, según la aclaración del usuario.

## Origen

Omarchy (MIT, David Heinemeier Hansson), commit
[`b8706a3f9eb185f56b61c6141561deba652beddf`](https://github.com/omacom/omarchy/tree/b8706a3f9eb185f56b61c6141561deba652beddf):

- `icon.txt`: copiado sin cambios.
- `bin/omarchy-branding-about-animation`: `about-animation.sh`, sin cambios.
- `etc/fastfetch/config.jsonc`: mismo orden, claves, cajas, padding y colores;
  datos de Omarchy/Arch adaptados a Gentoo y BWM.
- `bin/omarchy-launch-about`: adaptado en
  `scripts/omarchy-shims/omarchy-launch-about`.

La licencia original está en `LICENSE`.

## Adaptaciones BWM

No escribe `/etc/fastfetch` ni `~/.config/fastfetch`. Usa esta configuración
explícita y una copia bajo `$XDG_RUNTIME_DIR/bwm`; la medida de ventana queda en
`~/.local/state/bwm/omarchy/about.fit`. El lanzador usa la terminal predeterminada
mediante `bwm-terminal` y rutas absolutas de los helpers.

`bwm-about-data.py` proporciona rama/revisión del repo, estilo, tema, edad y
uptime. «Update» es la fecha del paquete más reciente registrado en Portage
(`BUILD_TIME`); no afirma que haya terminado una actualización completa.
OS, CPU, GPU, monitores, discos, memoria, kernel y terminal salen de Fastfetch.
WM consulta `hyprctl version -j`: muestra la versión de la sesión en ejecución,
que puede ser distinta del binario recién actualizado.
PC muestra DMI cuando está disponible y, si no, el hostname real.
La regla de `rules.lua` abre `org.omarchy.about` flotante y centrada; el lanzador
recuerda su tamaño ajustado y usa `relative = false` al redimensionar con Lua.

Comprobar la salida sin abrir una ventana:

```bash
~/.config/hypr/scripts/omarchy-shims/omarchy-launch-about --print
```

La comprobación visual se hace dentro de una terminal: en un pipe Fastfetch
puede detectar «codex» y omitir su fuente, que no representa la ventana final.
