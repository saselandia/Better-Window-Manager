# F10 — comprobación después de reiniciar sesión en Breeze

**Pendiente:** el plugin nuevo está compilado e instalado para el siguiente inicio de sesión. No se ha
cargado ni descargado en caliente. Las pruebas automáticas no certifican interacción real con
el ratón. F6b–F9 tienen también sus comprobaciones pendientes; consultar sus documentos.

1. Guarda el trabajo y vuelve a iniciar sesión entrando en Breeze. No basta con reiniciar sólo
   Quickshell para cambiar el plugin. `hyprctl configerrors` debe estar vacío.
2. Comprueba un tema Breeze y otro estilo de Plasma: al arrastrar una ventana, la previsualización
   debe usar el SVG translúcido del tema. No debe quedar un rectángulo azul anterior ni capturar
   clics. El outline debe desaparecer al soltar, cancelar, cerrar la ventana o cambiar de skin.
3. Con kitty y una app CSD, arrastra a izquierda/derecha, las cuatro esquinas y arriba. Deben ser
   mitades, cuartos y maximizado con el panel visible. Suelta entre el MSI y el LG en ambos
   sentidos, también con el centro de la ventana ya en el otro monitor: se usa el monitor de la
   previsualización, con todo el marco dentro. Repite con escala fraccionaria y panel en otro borde.
4. Comprueba Ctrl+flechas y su secuencia de mitades/cuadrantes. Se conserva el atajo elegido;
   no se ha pasado a Super+flechas. Las etiquetas propias que uses en las ventanas deben conservarse.
5. Acerca dos ventanas por sus bordes y esquinas. En kwinrc `[Windows]`, probar BorderSnapZone,
   WindowSnapZone y CenterSnapZone con cero y valores distintos, y SnapOnlyWhenOverlapping.
   Deben tener efecto tras una única recarga agrupada. Las ventanas de otros workspaces no atraen.
6. Encaja dos ventanas contiguas y redimensiona el borde compartido: la vecina conserva su borde
   lejano y no aparecen huecos. Repite por arriba/abajo y con CSD/SSD mezcladas. Al alcanzar el
   mínimo de una app, debe detenerse el divisor. Las proporciones nuevas no se guardan como layout.
7. Meta/Super+T: abre el editor reducido. Divide, une y reparte zonas; cambia la separación y
   aplica. Mayús+arrastre selecciona una hoja del layout. El resultado debe coincidir con lo
   mostrado, incluso si sueltas Mayús justo antes de soltar el ratón. Cancelar no escribe nada.
8. Si importas una disposición de KWin, elige la distribución en el editor de la pantalla
   correspondiente y aplica para asociar su UUID. Repite en el otro monitor. No cambiará el
   layout de los workspaces de otras skins.
9. En el menú de una ventana → Más acciones → Configurar ajustes especiales, abrir el KCM de
   reglas original. Crear una regla sobre **una app de prueba**, no sobre todas las ventanas.
   Probar clase/título, NoBorder, tamaño/posición, opacidades, escritorio y maximizado por ejes.
   «Detectar propiedades» y preselección desde KWin no están disponibles: introducir criterios a mano.
10. Reordenar dos reglas coincidentes: por propiedad debe ganar la primera; «No afectar» bloquea
    la siguiente. Apply se ejecuta una sola vez en una ventana nueva; Force resiste modificaciones;
    Remember guarda al cerrar y se recupera al abrir otra ventana. Cambiar una propiedad desde el
    KCM mientras la app está abierta: no debe perderse ese cambio al cerrarla.
11. Probar una app XWayland con rol/tipo y una Wayland normal/diálogo. Revisar motivos y metadata
    en `hyprctl -j breezebars-csd`. Las condiciones sin soporte no deben aplicarse a todas las apps.
    Diagnóstico de omisiones: `~/.local/state/bwm/plasma/kwinrules-report.json`.
12. Volver a Retro/default y regresar a Breeze con ventanas abiertas: no se repiten las reglas
    iniciales ni se mueve su geometría por ellas. No debe quedar outline, magnetismo ni reglas
    exclusivas de Breeze en las otras skins. No deben aparecer KWin ni servicios nuevos de Plasma.

Límites y opt-out para el Lua del usuario: [KWIN_RULES.md](../config/hypr/skins/plasma/scripts/KWIN_RULES.md).
No hacen falta capturas del escritorio completo. Si se aporta una captura, limitarla a la ventana
implicada y borrarla tras revisar. No usar plugin unload/load para ejecutar esta lista.

## Comprobación previa del 2026-11-11

Breeze activo; requisitos y configuración correctos. IPC de menús, editor y outline presentes.
Hyprland todavía pertenece a la sesión anterior y no tiene plugins cargados: los puntos de
ratón siguen pendientes. Se corrigieron dos errores QML detectados en el registro (import de
GlobalStates en PanelState y listas de la bandeja aún sin inicializar), con prueba aislada real.
El usuario autorizó cerrar sesión; después deberá autenticarse en SDDM.


### Caída encontrada tras el reinicio del 2026-11-11

El primer diagnóstico vio el plugin sin ventanas, pero Hyprland abortó después al mapear una.
Los dos informes coinciden en `CBreezeShadow::getPositioningInfo`: `lock()` sobre una referencia
débil a una barra de propietario único. Corregidos los cuatro usos en la sombra; prueba de
regresión reproduce el aborto anterior y pasa con el arreglo. Cuatro pruebas del plugin correctas,
binario recompilado e instalado atómicamente. Las sesiones recuperadas están en modo seguro y sin
plugins. **El arranque completo con el arreglo y las comprobaciones de ratón siguen pendientes**;
no se da F10 por validada por aquel diagnóstico inicial. No se vuelve a cerrar la sesión ni se
carga el plugin en caliente para comprobarlo.

### Validación del arreglo en un Hyprland anidado (2026-11-11)

Sin cerrar la sesión recuperada ni cargar nada en ella: el plugin instalado se cargó en un Hyprland
anidado desechable con la configuración real de Breeze y su propio `bwm-decorator`. Decoraciones
KDE, maximizar/restaurar, cerrar, recargar, encajar, minimizar, «sin barra» y la caída del auxiliar
funcionan sin caídas; la versión anterior, compilada aparte, reproduce el aborto de los informes.
Detalle en `BWM_CONTEXT.md` §3.151. **Sigue pendiente** el inicio de sesión normal y esta lista
completa con el ratón.

### Pruebas con ratón y teclado virtuales en la sesión real (2026-11-11)

Sesión normal con `breezebars` corregido cargado; Breeze activado con el gestor y ratón/teclado
virtuales (uinput) mientras el usuario no tocaba el equipo. Detalle en `BWM_CONTEXT.md` §3.153.

* **Funciona:** decoración KDE y colocación (punto 1 y F7); contorno KSvg durante el arrastre y fuera
  al soltar (2); tras los arreglos de abajo, encaje a mitades, cuartos y maximizado en los dos
  monitores con el marco exacto del contorno (3); Ctrl+flechas con su ciclo (4); imán entre ventanas
  (5); la vecina conserva su borde lejano al redimensionar el borde compartido (6); Meta+T abre el
  editor con la distribución de KWin y Cancelar no escribe nada (7); regla de prueba con posición,
  tamaño forzado, sin borde y opacidad, «Recordar» al cerrar y abrir, y orden/«No afectar» (9–10);
  vuelta a Retro sin barras, auxiliar, puente, contorno, etiquetas ni opacidad de Breeze (12).
* **Corregido:** al soltar no encajaba nunca (`kwin-tiles.py` leía `int` en vez de `bool` y no
  aceptaba la descripción larga «… (DP-2)» que manda el plugin); Esc no cerraba el editor; bucle de
  enlace en el contorno; en el plugin (para el próximo inicio de sesión): zonas como KWin 6.7.5
  (sólo bordes laterales y superior, borde interior con 250 ms), primer paso perdido al redimensionar
  vecinas (hueco de 2–3 px) y descripción corta del monitor para Mayús+arrastre.
* **Pendiente:** con el plugin nuevo tras iniciar sesión: el hueco del borde compartido, bordes
  interiores y Mayús+arrastre (8); otro estilo de Plasma (2); escala fraccionaria; apps XWayland con
  rol/tipo (11); dividir/unir y aplicar en el editor (7); valores de las zonas en kwinrc (5).
