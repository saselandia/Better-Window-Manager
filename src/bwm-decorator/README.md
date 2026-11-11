# bwm-decorator

Auxiliar de la skin Breeze (fase 6a de `docs/BREEZE_PLAN.md`). Carga **cualquier decoración de
ventanas de KDE** (KDecoration3: Breeze, Aurorae y las C++ de terceros) fuera de KWin y la dibuja
para el plugin `breezebars` de Hyprland, que la compone (F6b). Es un proceso aparte con la
plataforma Qt «offscreen»: nada de Qt entra en Hyprland (regla 1).

## Piezas

- `decorator.{h,cpp}`: el anfitrión. `Bridge` (como `DecorationBridge` de KWin: plugin y tema de
  `kwinrc`, Aurorae SVG con el motor v2, recarga), `Settings` (como `SettingsImpl`: botones, tamaño
  de borde, fuente), `ClientImpl` (lo que la decoración ve de la ventana) y `Window` (estado de una
  ventana, eventos, confirmación del estado de KDecoration3 con `apply(nextState())`, dibujo de las
  cuatro piezas del marco a la escala del monitor y sombra).
- `palette.{h,cpp}`: `decorationpalette` de **kwin v6.7.5** (GPL-2.0-or-later) sin cambios de
  lógica. Colores del esquema de `kdeglobals` (grupo Header o, en esquemas antiguos, `[WM]`).
- `server.{h,cpp}`: socket, mensajes y vigilancia de la configuración.
- `protocol.h`, `wire.h`, **`PROTOCOL.md`**: el protocolo con el plugin.
- `poc-fase0.cpp`: la prueba de concepto de la fase 0 (`docs/BREEZE_ARCH.md` §2, prueba d).

Basado en el diseño de kwin v6.7.5 `src/decorations/{decorationbridge,decoratedwindow,settings,
decorationpalette}.cpp` y `src/kcms/decoration/declarative-plugin/preview*.cpp`.

## Compilar, instalar y ejecutar

```bash
make -C src/bwm-decorator install    # ~/.local/share/bwm/bin/bwm-decorator, con mv atómico
python3 config/hypr/skins/plasma/scripts/decorator.py build|start|stop|status
```

Lo lanza `decorator.py start` sólo en Breeze (inicio de sesión y `bwm-theme-manager.py`) como hijo
de Hyprland; `decorator.py run` lo relanza si cae (espera 30 s si cae cinco veces en un minuto) y
termina al salir de Breeze. Un candado por socket (`<socket>.lock`) impide dos instancias (código 3).

## Pruebas

`python3 -m unittest tests.test_bwm_decorator -v` compila y arranca el auxiliar con una
configuración aislada y le habla con `tests/bwm_decorator_client.py`: Breeze oscuro y claro, cambio
de esquema en vivo, botones de `kwinrc`, hover, clic → petición, escala 1,5, varias ventanas,
sombra, supervisor. `BWM_TEST_AURORAE_DIR=<datos con aurorae/themes>` añade un tema Aurorae y
`BWM_TEST_PNG_DIR` guarda las imágenes.

## Límites

- Los menús propios de una decoración (QMenu, `popup()`) no se muestran: el menú de la ventana se
  pide al compositor (`Request` 4).
- No hay barra de menú global (`ApplicationMenu`).
- La escala es la del monitor de la ventana (la envía el cliente); `nextScale` = `scale`.
