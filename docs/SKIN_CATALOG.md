# Catálogo de skins adicionales de BWM

BWMenu → **Skins → Añadir skins** consulta un repositorio independiente:

- [GitHub: saselandia/bwm-skins](https://github.com/saselandia/bwm-skins).
- [GitLab: saselandia/bwm-skins](https://gitlab.com/saselandia/bwm-skins).
- Índice: `catalog/skins.json`, rama `main` en ambos.
- Checkout local: `/mnt/HDD1TB/Projects/bwm-skins`.

BWM incluye sólo default (end-4), Retro y Breeze (Kde plasma). Las demás skins se
publican en `bwm-skins`, con sus propias versiones y descargas. No hace falta añadirlas
a cada build de BWM. El catálogo comienza vacío hasta publicar la primera skin adicional.

## Publicar una skin

1. Trabaja en el repositorio `bwm-skins`. Crea `skins/<id>/` con la implementación,
   recursos, captura, licencia, avisos de terceros e instrucciones de instalación y
   desinstalación. Conserva los formatos de temas del escritorio original.
2. Prueba la instalación y activación con una revisión concreta de BWM y documenta
   sus dependencias. El manifiesto `skin.json` por sí solo no carga todos los módulos.
3. Publica una versión propia de la skin, por ejemplo `<id>-v1.0.0`.
4. Copia `templates/catalog-entry.json` a `skins/<id>/catalog.json` y completa nombre,
   descripción, escritorio original, versión, compatibilidad probada y enlaces HTTPS
   públicos a captura, código e instrucciones de esa versión.
5. Desde el checkout de BWM, genera y valida el índice del repositorio independiente:

   ```bash
   python3 config/hypr/scripts/bwm-skin-catalog.py build --catalog-root ../bwm-skins
   python3 config/hypr/scripts/bwm-skin-catalog.py build --catalog-root ../bwm-skins --check
   ```

6. Revisa y commitea los archivos en `bwm-skins`. Su `origin` tiene ambos destinos:

   ```bash
   git push origin main
   git push origin <id>-v1.0.0
   ```

Las descargas adjuntas a releases se publican aparte en cada plataforma; Git replica
archivos y etiquetas. El [README del catálogo](https://github.com/saselandia/bwm-skins#readme)
contiene también estas instrucciones.

## Consultar e instalar

Pulsa Actualizar o Ctrl+R en Añadir skins para consultar lo recién publicado. BWMenu muestra versión y
estado de instalación, permite buscar y abre «Ver instalación» en la página de la skin.
«Repositorio» abre GitHub; GitLab se usa como respaldo para leer el índice.
La caché dura una hora; sin conexión se conserva la última copia válida. BWM incluye
únicamente un índice vacío de respaldo, nunca copias del código de las skins externas.
Una caché del catálogo anterior de skins integradas no se reutiliza.

**Pendiente:** instalador automático y carga completa de módulos externos. El motor
actual detecta manifiestos en `~/.local/share/bwm/skins`, pero todavía requiere integrar
la carga de sus módulos para admitir un escritorio externo completo. Las instrucciones
de cada publicación deben reflejar su soporte real. Consultar el catálogo no instala ni
ejecuta código, no actualiza BWM y no cambia la skin activa. `compatibility` es información
publicada de las pruebas; todavía no es una restricción aplicada por un instalador.
