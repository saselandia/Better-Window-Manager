# BWMenu

Menú de diagnóstico y recuperación común a todas las skins. Su ventana gráfica es una
instancia autónoma de Quickshell, separada de la barra y sus servicios. Presenta una
galería con vistas previas de las skins, sus requisitos y un botón para aplicarlas.
La consola de rescate sigue funcionando sin Quickshell ni Qt. Usa programas que ya son
requisitos del núcleo; no requiere paquetes nuevos.

El aspecto sigue en vivo la skin y el tema activos: colores, fuentes y formas de
default (end-4), Retro o Breeze. Lee los roles de Material You, `colors.toml` y
`shell.toml` de Omarchy (incluidos los ajustes del usuario) o los colores de
`kdeglobals`, sin escribirlos ni introducir un formato nuevo de temas. La tarjeta
activa muestra el fondo guardado y una muestra de su paleta; las demás usan las vistas
previas declaradas en sus manifiestos. Se conserva la selección al cambiar de tema.

Mantén pulsada **+** y pulsa **-**, o al revés, sin Super ni Alt. Sirven las teclas
normales, las del teclado numérico y sus combinaciones. Los signos por separado siguen
funcionando en las aplicaciones. El atajo se genera en los helpers de
`keybinds-manager.py`, por lo que sobrevive a regeneraciones y cambios de skin.

```bash
bwm menu                 # ventana gráfica; en una TTY, interfaz de consola
bwm menu --open          # ventana propia; si existe, le da el foco
bwm menu --tui           # interfaz de consola en esta terminal
bwm menu --open --tui    # consola de rescate en Kitty con configuración limpia
bwmenu                   # alias instalado por install.sh
bwm menu --report        # diagnóstico en texto
bwm menu --json          # diagnóstico estructurado, sin interfaz
bwm version              # revisión de BWM
bwm check --versions     # requisitos con versiones, mínimos y comandos de reparación
```

En la ventana gráfica se navega con ratón o Tab/Intro; Esc vuelve a Skins (allí cierra)
y Ctrl+R actualiza el diagnóstico. Las páginas son Skins, Estado, Dependencias,
Recuperación y Ayuda. Dependencias incluye buscador y comandos para resolver fallos.

Las luces de las dependencias y las tarjetas de skins usan la referencia declarada
por BWM: **verde / Correcta**, coincide o pasa su comprobación; **rojo / Falta**, ausente,
inferior a la referencia o incompatible; **naranja / Desactualizado**, la referencia de
BWM es anterior a la versión instalada.
`referenceVersion` registra las versiones del entorno de BWM; `check.min` conserva el
mínimo compatible para instalar/activar una skin. La fecha y la base de BWM del registro
están en `referenceEnvironment`, en `requirements.json`, y se muestran en Estado.
No se obtienen de la última build remota ni de los últimos commits de las dependencias.
Cuando no hay referencia de versión y sólo se comprueba presencia, pasarla da verde.
El gris indica que el diagnóstico aún no está disponible. No son consultas de
actualizaciones por Internet. La luz de una skin incluye el núcleo compartido y sus
dependencias opcionales; prevalece rojo sobre naranja y verde.

Las listas usan filas compactas de 34 px y las superficies del tema activo, con texto
negro en fondos claros y blanco en oscuros. Muestran dependencia, versión instalada y referencia BWM; pulsar una fila
abre los detalles. Los comandos de reparación se despliegan sólo cuando hay incidencias.
Los requisitos ausentes muestran «Falta» en la columna de versión instalada.

Los selectores Núcleo y de cada skin llevan también su luz de estado, con el mismo
resumen de versiones que las tarjetas. Las tarjetas de skins tienen esquinas rectas.
La mascota de BWM conserva la misma ventanita con antenas, pies y cuatro marcas en
las tres skins. Retro lleva gafas y patinete sobre fondo transparente, con una estela
que va hacia atrás para sugerir avance a la derecha; todos sus colores salen del tema.
Breeze mantiene la cabecera gris y default usa superficies tonales Material You/end-4.
Al pulsarla, se desplaza lateralmente y hacia arriba como una ventana y regresa a su
sitio, además de su gesto propio. También responde a Intro/Espacio y se pausa al ocultarse.

El botón **×** superior derecho cierra BWMenu; espera si se está aplicando una acción.
Para actualizar el diagnóstico usa Ctrl+R. En Añadir skins, **Actualizar** o Ctrl+R
consulta el catálogo remoto.

En la consola usa ↑/↓ y Intro; Esc vuelve (en Inicio sale), R actualiza y Q sale.
También sigue la paleta activa cuando la terminal admite color verdadero.

El menú incluye:

- **Estado y versiones:** revisión de BWM según Git, carpeta instalada, skin activa,
  Hyprland en ejecución e instalado, commit, bibliotecas y estado de Quickshell `ii`.
  `dirty` indica cambios locales en archivos versionados. Una copia sin Git ni archivo
  `VERSION` se identifica como una copia sin datos de revisión.
- **Dependencias:** requisitos obligatorios y opcionales del núcleo y de cada skin,
  versión instalada, mínimo declarado y versión probada cuando existe. Usa el mismo
  catálogo y comprobador que la bienvenida, el instalador y `bwm check`. Los paquetes
  se consultan localmente (Gentoo, Arch, Fedora/openSUSE o Debian/Ubuntu); algunas
  herramientas tienen una consulta de versión explícita en el catálogo.
- **Skins:** manifiestos instalados, requisitos y botón para aplicar cada una. «Lista»
  significa que cumple los requisitos obligatorios, incluido el núcleo. La acción
  vuelve a comprobarlos con `bwm skin ID` antes de aplicar; usa el gestor de BWM.
- **Añadir skins:** catálogo oficial desde GitHub con GitLab de respaldo, búsqueda,
  capturas y estado de instalación. «Actualizar» consulta nuevas publicaciones; sin conexión usa
  el catálogo guardado o el incluido. «Cómo publicar» abre la [guía del catálogo](SKIN_CATALOG.md).
  Las nuevas skins se publican por separado en `saselandia/bwm-skins`, sin incluirlas en
  builds de BWM; «Ver instalación» abre sus instrucciones. El instalador automático y
  la carga completa de módulos externos siguen pendientes. No se ejecuta código remoto ni se cambia de skin al consultar el catálogo.
- **Recuperación:** reinicio de mantenimiento de la barra y paneles de la skin actual
  (`set ID --restart-shell`), recarga de Hyprland, errores de configuración y últimas
  100 líneas del registro de Quickshell. No cierra sesión ni instala paquetes.
- **Ayuda:** comandos de recuperación y acceso desde una consola.

«OK» significa que pasa la comprobación del catálogo. Cuando no se declara una versión
mínima, se muestra **sin mínimo declarado**: la presencia del programa o módulo no
certifica su compatibilidad con todas las versiones. **Versión sin dato** indica que
no hay una versión consultable; no equivale a que falte el requisito. Los plugins de
Hyprland deben coincidir con el commit del compositor en ejecución. No se descargan ni
cargan plugins desde BWMenu y no se compilan automáticamente.

Si se actualizó Hyprland sin cerrar sesión, el requisito de Hyprland y los plugins se
comprueban con el compositor en ejecución; se muestra también el binario instalado
para la próxima sesión. Las versiones de paquetes son las instaladas, no una consulta
de actualizaciones por Internet.

Si cae **todo Hyprland**, sus atajos dejan de funcionar. Entra con Ctrl+Alt+F3, inicia
sesión y ejecuta:

```bash
~/.config/hypr/scripts/bwm menu --tui
```

En esa consola se pueden consultar versiones, requisitos y ayuda. Las acciones que
cambian el escritorio necesitan conexión con la sesión de Hyprland. No se intenta
arrancar un shell gráfico en una TTY ni se termina una transición por un tiempo límite
arbitrario. BWMenu evita instancias duplicadas del mismo modo.

Si la ventana gráfica falla al cargar o su proceso termina con error, el lanzador abre
la consola de rescate automáticamente. Una salida normal no abre otra ventana. Su
registro está en `$XDG_RUNTIME_DIR/bwm-menu.log`. Cerrar la ventana mientras aplica una
skin o reinicia paneles espera a que termine la acción.
