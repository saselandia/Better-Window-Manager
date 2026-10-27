# Temas y plugins de Omarchy en BWM

Las páginas **Ajustes → Temas** y **Ajustes → Plugins** están separadas en las
dos aplicaciones de Ajustes. Temas muestra miniaturas, paletas y el tema elegido.
Plugins permite filtrar Todos/Activados/Desactivados, activar/desactivar y elegir
la posición de cada widget en la barra Retro. El indicador
«Elegido» muestra la paleta Retro guardada; si estás en otro estilo, Aplicar
cambia a Retro. Cada página tiene las vistas Instalados y Descubrir.

En **Descubrir**, dentro de la página correspondiente, escribe un nombre,
autor o palabra clave y pulsa Buscar. Cada resultado permite abrir su repositorio
o instalarlo. También puedes abrir el catálogo web o pegar directamente una URL
HTTPS de Git desde Instalar por URL. Descargar un tema no lo aplica: aparece en la lista para elegirlo.
Los plugins se activan después de instalarlos.

Las fuentes son la [galería de temas de Omarchy](https://omarchy.org/themes/) y
el [catálogo del marketplace de plugins](https://github.com/omacom/omarchy-plugin-marketplace).
El comportamiento de distribución por Git sigue el
[manual de plugins de Omarchy](https://omarchy.org/manual/shell-plugins/).
Los catálogos se guardan una hora en `~/.cache/bwm/addons`; Actualizar catálogo
fuerza su renovación. Si falla la conexión se usa la última copia disponible.
La búsqueda muestra los primeros 30 resultados e indica el total. **Mostrar más**
carga las páginas siguientes; también se puede acotar con más palabras.

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
- Los plugins descargados están en `~/.local/share/bwm/omarchy-plugins` y se
  validan en una carpeta temporal antes de publicarlos. Un id duplicado o un
  destino existente produce un error y conserva lo instalado.
- Activación, posición y ajustes se guardan en
  `~/.config/bwm/omarchy-plugins.json`. Mover un plugin conserva sus ajustes.
  Desactivar uno también deja de cargar su servicio. Los widgets fijos del sistema
  (bandeja, audio, red, etc.) se siguen ocultando en Ajustes → Barra.

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
