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
