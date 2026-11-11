# breezebars (BWM)

Plugin de Hyprland de la skin Breeze de BWM, fork de hyprbars (hyprwm/hyprland-plugins,
BSD-3-Clause, ver `LICENSE`). Se registra como `breezebars` (`plugin:breezebars:*`, reglas
`breezebars:*`) para poder convivir con el de Omarchy de Retro, que se llama `hyprbars`.

## Decoraciones de KDE (F6b de `docs/BREEZE_PLAN.md`)

Las barras las dibuja **bwm-decorator** (`src/bwm-decorator`, protocolo en su `PROTOCOL.md`) con la
decoración de KWin activa (Breeze, Aurorae, de terceros). El plugin es el pegamento:

- `DecoClient.{hpp,cpp}`: socket `SOCK_SEQPACKET` no bloqueante, leído desde el bucle de eventos de
  Wayland; envíos con `MSG_DONTWAIT` (nunca bloquea a Hyprland). Si el auxiliar no está, lo lanza
  (`decorator.py start`, como mucho cada 15 s) y reintenta; mientras tanto, la barra plana de siempre.
- `barRemote.{hpp,cpp}`: por ventana, estado (tamaño, escala, activa, maximizada, fijada, bordes de
  pantalla, título, app) enviado sólo si cambia; bordes reservados en los cuatro lados
  (`DECORATION_POSITION_ABSOLUTE`); una textura con el búfer del auxiliar copiado al recibirlo y
  subida sólo en los rectángulos dañados; la última imagen se estira mientras llega la del tamaño
  nuevo; contorno del tema; sombra de nueve trozos como KWin en una decoración aparte
  (`CBreezeShadow`, sin reservar espacio); redondeo del contenido = radio inferior de la decoración
  (prioridad mínima, las reglas del usuario mandan; arriba lo cuadra `SquareTop.cpp`).
- Puntero como KWin: movimiento, pulsar, soltar y rueda van a la decoración sin aceptar; lo que
  ningún botón acepta (`PointerResult`) es del compositor: mover desde la barra (con el snapping de
  siempre), redimensionar desde los bordes que diga la decoración, doble clic (`on_double_click`,
  de `kwinrc [Windows] TitlebarDoubleClickCommand`), rueda (`on_wheel`, de `kwinrc [MouseBindings]
  CommandTitlebarWheel`) y menú de la ventana con el botón derecho.
- Peticiones: cerrar, maximizar (izquierdo: ambos ejes; central: vertical; derecho: horizontal) y
  minimizar con `skins/plasma/scripts/kwin-window.py` (F8; el modo de maximizado de la decoración sale
  de las etiquetas `bwm-max-v`/`bwm-max-h`), menú de la ventana por IPC a Quickshell
  (`qs -c ii ipc call plasmaWindowMenu open <dirección> <x> <y>`, lo dibuja F9), tooltip (con los
  colores `[Colors:Tooltip]` de `kdeglobals`) y fijar en todos los escritorios. Encima/debajo,
  enrollar, ayuda contextual y menú de aplicación no existen en Hyprland: no hacen nada.
- `DecoWire.hpp` y `DecoLogic.hpp` no dependen de Hyprland: los prueba
  `tests/breezebars_wire_test.cpp` (vía `tests/test_breezebars.py`), también contra el auxiliar real.
  La sombra sigue el algoritmo de `generateShadowQuads` de KWin v6.7.5 (`src/scene/shadowitem.cpp`),
  reescrito, sin copiar su código.

`hyprctl breezebars-interactive move|resize <dirección>` (F9, «Mover»/«Redimensionar» del menú de la
ventana): la ventana sigue al puntero hasta el siguiente clic, como KWin. La etiqueta `bwm-no-border`
(«Sin barra de título ni marco») quita la barra.

`hyprctl hyprbars-csd` dice si hay conexión con el auxiliar y, por ventana, si lleva barra de KDE
(`kde`), la plana (`plana`) o ninguna.

Compilar e instalar: `make && make install` (copia temporal + `mv` atómico a
`config/hypr/plugins/breezebars.so`). Nunca `cp` sobre el `.so` cargado ni cargarlo/descargarlo en
caliente: se carga al iniciar sesión en Breeze (`autostart.sh`).

## Detección y negociación CSD/SSD (F7)

`CSDLogic.hpp` contiene la política y el estado comprobables sin compositor. `CSDDetect.cpp`
integra esa política con los protocolos de Hyprland **0.56.2**, commit
`efb50993780079460b0cbed1363e2166a2de1d9f`. Referencias leídas de KWin **v6.7.5**:
`src/xdgshellwindow.cpp`, `src/wayland/xdgdecoration_v1.cpp`,
`src/wayland/server_decoration.cpp` y `src/x11window.cpp`. Es una implementación propia de la
política, sin copiar C++ de KWin. El auxiliar Qt de F6 sigue fuera de Hyprland.

- Wayland sin protocolo de decoración: CSD. Con xdg-decoration: petición client-side → CSD;
  server-side o sin preferencia → SSD. El modo visible cambia tras **ack_configure y commit**,
  asociando el primer configure al commit vacío inicial; no se reserva la barra por la petición
  antes de que el cliente haya aplicado el modo. Si existen ambos protocolos, manda xdg.
- El protocolo KDE antiguo respeta None/Client/Server; sin petición explícita prefiere Server.
  Aplica al siguiente commit (no tiene ack) y admite más de cuatro cambios consecutivos.
- Hyprland responde siempre Server de origen y limita las peticiones KDE antiguas. Dos hooks
  sobre los setters de callbacks de las fábricas generadas sustituyen esa política sólo con
  Breeze habilitado. Se verificaron sus símbolos exportados y llamadas en el binario 0.56.2;
  no se interceptan funciones pequeñas que el compilador integra en sus llamadores. Si falla
  un hook, la inicialización falla y restaura los callbacks; no continúa con negociación falsa.
  Esta integración es específica de la ABI de Hyprland: recompilar y revisar al actualizarlo.
- XWayland: `_MOTIF_WM_HINTS` con flag decorations y decorations=0, o un
  `_GTK_FRAME_EXTENTS` válido de cuatro CARDINAL, implica CSD. **También cuenta el hint GTK con
  ceros**, como exige F7; KWin 6.7.5 comprueba valores no nulos. Ventanas override-redirect o
  especiales no llevan barra. XCB usa otra conexión, respuestas asíncronas y PropertyNotify;
  no espera respuestas en el render ni en las consultas IPC. Mientras faltan hints: pendiente.
- `breezebars:no_bar=true`, `decorate=false` y fullscreen suprimen el marco. `no_bar=false`
  vuelve al automático: no fuerza otra barra sobre un CSD. La traducción de NoBorder desde
  `kwinrulesrc` sigue siendo F10. Destruir/recrear protocolos y cambiar sus modos recalcula el marco.

Diagnóstico humano: `hyprctl breezebars-csd`; el alias `hyprbars-csd` se conserva.
`hyprctl -j breezebars-csd` devuelve API versión 1 con dirección **y PID**, petición, respuesta,
modo aplicado, hints/overrides, motivo, estado pendiente y los cuatro bordes visibles. La API Lua
`hl.plugin.breezebars.decoration(address, pid)` devuelve el mismo marco para `placement.lua`.
`bwm_windows.py` y `quick-tile.py` consumen el JSON; nunca adivinan por clase/título ni añaden
30 px si falta el plugin. Se cuentan todos los bordes reales de F6, también con Aurorae.

Pruebas: `tests/csd_logic_test.cpp`, `tests/test_csd_detection.py`,
`tests/test_plasma_placement.py` y las de F6. Incluyen ack/commit, seriales que desbordan,
cambios de modo, propiedades X11, identidad reutilizada y geometría del marco en cuatro lados.
`skins/plasma/scripts/csd-audit.py` prepara una tabla de sólo lectura sin guardar títulos.
**Pendiente de ejecutar dentro de Hyprland tras reiniciar sesión entrando en Breeze**:
ver `docs/BREEZE_CSD_RESULTS.md`. No cargar/descargar el plugin en caliente.

---

Texto original de hyprbars:

# hyprbars

Adds simple title bars to windows.

![image](https://github.com/user-attachments/assets/184a66b9-eb91-4f6f-8953-b265a2735939)

## Config

All config options are in `plugin:hyprbars`:

```
plugin {
    hyprbars {
        # example config
        bar_height = 20

        # example buttons (R -> L)
        # hyprbars-button = color, size, on-click
        hyprbars-button = rgb(ff4040), 10, 󰖭, hyprctl dispatch killactive
        hyprbars-button = rgb(eeee11), 10, , hyprctl dispatch fullscreen 1

        # cmd to run on double click of the bar
        on_double_click = hyprctl dispatch fullscreen 1
    }
}
```

| property | type | description | default |
| --- | --- | --- | --- |
`enabled` | bool | whether to enable the bars |
`bar_color` | color | bar's background color
`bar_height` | int | bar's height | `15`
`bar_blur` | bool | whether to blur the bar. Also requires the global blur to be enabled.
`col.text` | color | bar's title text color
`bar_title_enabled` | bool | whether to render the title | `true`
`bar_text_size` | int | bar's title text font size | `10`
`bar_text_font` | str | bar's title text font | `Sans`
`bar_text_align` | left, center | bar's title text alignment | `center`
`bar_buttons_alignment` | right, left | bar's buttons alignment | `right`
`bar_part_of_window` | bool | whether the bar is a part of the main window (if it is, stuff like shadows render around it)
`bar_precedence_over_border` | bool | whether the bar should have a higher priority than the border (border will be around the bar)
`bar_padding` | int | left / right edge padding | `7`
`bar_button_padding` | int | padding between the buttons | `5`
`icon_on_hover` | bool | whether the icons show on mouse hovering over the buttons | `false`
`inactive_button_color` | col | buttons bg color when window isn't focused
`on_double_click` | str | command to run on double click of the bar (not on a button)

## Buttons Config

Use the `hyprbars-button` keyword.

```ini
hyprbars-button = bgcolor, size, icon, on-click, fgcolor
```

Please note it _has_ to be inside `plugin { hyprbars { } }`.

For Lua config, use `hl.config` for plugin options and
`hl.plugin.hyprbars.add_button` for buttons:

```lua
hl.config({
    plugin = {
        hyprbars = {
            bar_height = 20,
            on_double_click = "hyprctl dispatch fullscreen 1",
        },
    },
})

hl.plugin.hyprbars.add_button({
    bg_color = "rgb(ff4040)",
    fg_color = "rgb(ffffff)",
    size = 10,
    icon = "X",
    action = "hyprctl dispatch killactive",
})

hl.plugin.hyprbars.add_button({
    bg_color = "rgb(eeee11)",
    fg_color = "rgb(000000)",
    size = 10,
    icon = "_",
    action = "hyprctl dispatch fullscreen 1",
})
```

## Window rules

Hyprbars supports the following _dynamic_ [window rules](https://wiki.hypr.land/Configuring/Window-Rules/):

`hyprbars:no_bar` -> disables the bar on matching windows.  
`hyprbars:bar_color` -> sets the bar background color on matching windows.  
`hyprbars:title_color` -> sets the bar title color on matching windows.  

Example:
```bash
# Sets the bar color in red for all windows that have 'myClass' as a class
windowrule {
    name = myClass-red-bars
    match:class = ^(myClass)$
    hyprbars:bar_color = rgb(ff0000)
}
```
