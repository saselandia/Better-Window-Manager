# Temas y plugins de Omarchy en BWM

En **Retro**, todo se hace dentro del menú de Omarchy:

- **Estilo → Temas → Elegir tema** abre el carrusel nativo, con todos los temas
  incluidos e instalados y la paleta dinámica del fondo.
- **Ajustes → Plugins → Instalados** permite activar cada plugin y colocar sus
  widgets en las seis zonas de la barra de Omarchy. **Estilo → Barra → Widgets**
  lleva a la misma lista. Clonar y quitar conservan los selectores originales.
- **Catálogo**, dentro de Temas o Plugins, muestra una lista con buscador de
  teclado. Cada entrada permite ver el repositorio o instalar; las ya instaladas
  llevan una marca. También se puede pegar una **URL de Git**.

Intro abre o guarda, Espacio cambia un interruptor, Esc vuelve conservando la
fila y la búsqueda. Los campos de un atajo o comando nuevo quedan en borrador
hasta pulsar **Añadir**. Los errores de lectura o guardado se muestran en el menú.
Pantallas conserva un esquema visual y sólo cambia la configuración al aplicar.
Las páginas de catálogo con miniaturas siguen disponibles en Ajustes de Breeze;
default (end-4) conserva sus ajustes propios.

Las fuentes son la [galería de temas de Omarchy](https://omarchy.org/themes/) y
el [catálogo del marketplace de plugins](https://github.com/omacom/omarchy-plugin-marketplace).
Se comparten el motor de descarga, validación y caché de una hora de BWM
(`~/.cache/bwm/addons`), con la última copia disponible si falla la conexión.
En Retro la búsqueda consulta el catálogo completo guardado, también por autor
y descripción, y muestra lotes de 60 entradas con **Mostrar más**. En Breeze
la búsqueda conserva su paginación de 30 resultados.
Descargar un tema no lo aplica: aparece en el carrusel para elegirlo. Los plugins
se activan al instalarlos.

## Compatibilidad y archivos

- Temas: formato actual de Omarchy, con `colors.toml` en la raíz y las claves
  `background`, `foreground` y `accent` en hexadecimal. Se instalan en
  `${XDG_DATA_HOME:-~/.local/share}/bwm/omarchy-themes`. No se ejecutan instaladores
  ni hooks del repositorio. Los archivos de apps que un tema aporta (por ejemplo,
  `neovim.lua`) se consumen como en los temas incluidos al aplicarlo.
- Los 23 temas incluidos siguen en `config/hypr/omarchy/themes`.
  `~/.config/omarchy/themes` también se reconoce para instalaciones anteriores;
  en este equipo es un enlace a los incluidos, así que no es el destino de las
  descargas. El catálogo evita contar ese enlace como temas de la comunidad.
- Plugins: `manifest.json`, `schemaVersion: 1`, id propio y tipos `bar-widget`
  y/o `service`. Se comprueba que los archivos de entrada existan, que no salgan
  del repositorio ni sean enlaces y que los imports `qs.*` estén disponibles.
  No se admiten reemplazos completos de barra, bloqueo, overlays o paneles que
  el anfitrión de BWM no carga. Esto comprueba el formato y los módulos, no todas
  las dependencias de aplicaciones ni cada llamada de un plugin ajeno.
- Los plugins descargados están en `~/.config/omarchy/plugins` y se
  validan en una carpeta temporal antes de publicarlos. Un id duplicado o un
  destino existente produce un error y conserva lo instalado.
- Activación, posición y ajustes se guardan en
  `~/.config/omarchy/shell.json`. Mover un plugin conserva sus ajustes.
  Desactivar uno también deja de cargar su servicio. Los widgets del sistema
  (bandeja, audio, red, etc.) se gestionan en la misma lista de plugins.

La lista de Ajustes, `omarchy-theme-list`, `omarchy-theme-dir`, el carrusel y el
motor de colores usan el mismo catálogo de temas. Un tema sin `preview.png`
recibe una miniatura de su fondo o de su paleta.

## Barra

Los widgets que no se ven liberan su anchura: por ejemplo, el teclado con una
sola distribución y las actualizaciones sin paquetes pendientes. Al ocultar
widgets, la bandeja se mantiene junto a los que quedan. Los plugins que no caben
siguen siendo medibles sin crear un bucle entre visibilidad y anchura.

El plugin multimedia `crmne.mpris` se coloca por defecto en `centerEnd`, a la
derecha de la hora. Su anchura se adapta al espacio disponible antes de los
indicadores del extremo derecho. La página Plugins permite cambiar esa posición.

## Validación

```bash
python3 -m unittest discover -s config/hypr/scripts/tests -p test_bwm_addons.py
python3 -m py_compile config/hypr/scripts/bwm-addons.py config/hypr/scripts/bwm_omarchy.py
bash -n config/hypr/scripts/bwm-plugin.sh
```

Las pruebas aíslan los directorios con constantes/env de la función probada;
no cambian `$HOME` ni aplican paletas o plugins de prueba a la sesión real.
