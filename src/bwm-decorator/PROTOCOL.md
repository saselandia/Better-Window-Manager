# Protocolo de bwm-decorator (versión 1)

Lo hablan el auxiliar `bwm-decorator`, el plugin `breezebars` de Hyprland (F6b) y el cliente de
pruebas `tests/bwm_decorator_client.py`, que es la referencia ejecutable. Constantes en
`protocol.h`; lectura y escritura en `wire.h`.

## Transporte

- Socket Unix **`SOCK_SEQPACKET`** en `$XDG_RUNTIME_DIR/bwm-decorator.sock`: cada paquete es un
  mensaje completo (no hay que trocear). Tamaño máximo 64 KiB.
- Varios clientes a la vez; cada uno tiene sus propias ventanas, que se destruyen al cerrar la
  conexión.
- Todo en **little-endian**. `u32`, `i32`, `f64`; **cadena** = `u32` longitud + bytes UTF-8.
- Los búferes viajan como descriptores de archivo (`SCM_RIGHTS`) en el mismo paquete que el mensaje
  que los anuncia. El auxiliar **nunca bloquea** al enviar (`MSG_DONTWAIT`): un cliente que no lee
  pierde mensajes, así que tiene que leer sin demora.
- Coordenadas **lógicas** de la decoración: el origen es la esquina superior izquierda del marco
  completo; el contenido de la ventana empieza en `(borde izquierdo, borde superior)`.

## Cabecera (16 bytes)

| Campo | Tipo | Valor |
| :--- | :--- | :--- |
| magic | u32 | `0x444D5742` («BWMD») |
| version | u16 | `1` (el auxiliar responde `Error` a otras) |
| type | u16 | tipo de mensaje |
| window | u32 | id de ventana elegido por el cliente; `0` en los globales |
| size | u32 | bytes de carga útil que siguen |

## Cliente → auxiliar

| Tipo | Nombre | Carga útil |
| ---: | :--- | :--- |
| 1 | Hello | `u32` versión. Es obligatorio antes que cualquier otro. |
| 2 | CreateWindow | *WindowState* |
| 3 | UpdateWindow | *WindowState* (estado completo; el auxiliar avisa a la decoración de lo que cambia) |
| 4 | DestroyWindow | — |
| 5 | Pointer | `u32 kind`, `f64 x`, `f64 y`, `u32 button`, `u32 buttons`, `f64 angleDeltaY` |
| 6 | Ping | — (responde `Pong`) |

**WindowState:** `f64 width`, `f64 height` (tamaño lógico del contenido, sin el marco), `f64 scale`
(escala del monitor), `u32 flags`, `u32 edges`, cadena `caption`, cadena `appClass` (clase o id de
la app), cadena `iconName` (vacía: el auxiliar busca el icono del `.desktop` por id o `StartupWMClass`).

`flags`: 1 activa, 2 maximizada en horizontal, 4 en vertical, 8 en todos los escritorios,
16 encima, 32 debajo, 64 enrollada, 128 se puede cerrar, 256 maximizar, 512 minimizar, 1024 mover,
2048 redimensionar, 4096 enrollar, 8192 modal, 16384 tiene ayuda contextual, 32768 excluida de
capturas.

`edges` (`Qt::Edges`, bordes de pantalla junto a la ventana): 1 arriba, 2 izquierda, 4 derecha, 8 abajo.

`Pointer.kind`: 1 movimiento (el primero hace de «entrar»), 2 salir, 3 pulsar, 4 soltar, 5 rueda.
`button`/`buttons` son los de Qt (1 izquierdo, 2 derecho, 4 central). La rueda va en
`angleDeltaY` (120 = un paso, como Qt). El doble clic en la barra **no** lo trata la decoración: es
del compositor (`kwinrc [Windows] TitlebarDoubleClickCommand`).

Como en KWin, la decoración recibe pulsar, soltar y rueda **sin aceptar**; si ningún botón suyo los
acepta, son del compositor. El auxiliar responde a cada uno con `PointerResult`: `accepted` = 1 si
la decoración lo usó (un botón), y `section` = la sección bajo el puntero en ese momento
(`Qt::WindowFrameSection`: 0 ninguna, 1 izquierda, 2 arriba-izquierda, 3 arriba, 4 arriba-derecha,
5 derecha, 6 abajo-derecha, 7 abajo, 8 abajo-izquierda, 9 barra de título). Con una pulsación no
aceptada el compositor mueve (barra), redimensiona (bordes), abre el menú (botón derecho) o aplica la
acción de doble clic o de rueda de `kwinrc`.

## Auxiliar → cliente

| Tipo | Nombre | Carga útil |
| ---: | :--- | :--- |
| 101 | HelloAck | `u32` versión, cadena plugin, cadena tema |
| 102 | Geometry | ver abajo |
| 103 | Frame | ver abajo (+ memfd si `hasFd`) |
| 104 | Shadow | ver abajo (+ memfd si `hasFd`) |
| 105 | Request | `u32 kind`, `u32 arg`, `f64 x, y, w, h`, cadena `text` |
| 106 | Error | cadena |
| 107 | Reconfigured | cadena plugin, cadena tema (otro plugin o tema: las decoraciones se recrean y llega Geometry y Frame nuevos) |
| 108 | Pong | — |
| 109 | SectionUnderMouse | `u32 Qt::WindowFrameSection` bajo el puntero (barra de título = mover, bordes = redimensionar) |
| 110 | PointerResult | `u32 kind`, `u32 accepted`, `u32 section`, `u32 button`: respuesta a cada pulsar, soltar y rueda |

**Geometry**, cada vez que cambia: `f64 left, top, right, bottom` (bordes del marco),
`f64 left, top, right, bottom` (bordes **sólo para redimensionar**, fuera del marco visible),
`f64 topLeft, topRight, bottomRight, bottomLeft` (radios de las esquinas), `f64 x, y, w, h` (barra de
título), `u32 opaque`, `f64` grosor del contorno, `u32` color del contorno (ARGB),
`f64 topLeft, topRight, bottomRight, bottomLeft` (radios del contorno). El contorno
(`KDecoration3::BorderOutline`) lo dibuja el compositor por fuera del marco, como KWin.

**Frame**: `u32 serial`, `u32 buffer` (0 o 1), `u32 hasFd`, `f64 scale`, `u32 width`, `u32 height`,
`u32 stride` (bytes), `u32 capacity` (tamaño del memfd); luego 4 piezas (arriba, abajo, izquierda,
derecha), cada una `u32 x, y, w, h` en píxeles dentro del búfer + `f64 x, y, w, h` rectángulo lógico
en la decoración; luego `u32 n` y `n` rectángulos dañados `f64 x, y, w, h` (lógicos).

- Píxeles **ARGB32 premultiplicados** en el orden de bytes de la máquina (BGRA en little-endian),
  como `DRM_FORMAT_ARGB8888` / `CAIRO_FORMAT_ARGB32`. Cada pieza está dibujada a `scale`.
- Las piezas van empaquetadas: arriba en `y = 0`, abajo debajo, e izquierda y derecha juntas debajo.
  El interior de la ventana no se envía.
- **Doble búfer**: hay dos memfd por ventana y se alternan. El descriptor llega una vez (con
  `hasFd`) cuando el búfer se crea o crece; después el cliente lo identifica por `buffer`. El cliente
  debe copiar o subir las piezas **al recibir** el Frame: el auxiliar sólo vuelve a escribir un búfer
  después de haber enviado un Frame del otro.
- Cada búfer está completo; los daños sólo indican qué cambió respecto al Frame anterior.

**Shadow**, cuando cambia la sombra del tema (normalmente una vez por ventana): `u32 serial`,
`u32 hasFd`, `u32 width`, `u32 height`, `u32 stride`, `f64 devicePixelRatio`,
`f64 left, top, right, bottom` (relleno alrededor del marco), `f64 x, y, w, h` (rectángulo interior
de la imagen, como `KDecoration3::DecorationShadow::innerShadowRect`). Con `hasFd = 0` y tamaño
cero: la decoración ya no tiene sombra. Misma codificación de píxeles que Frame.

**Request.kind**: 1 cerrar, 2 alternar maximizado (`arg` = botones), 3 minimizar, 4 menú de la
ventana (en el rectángulo), 5 mostrar tooltip (`text`), 6 ocultar tooltip, 7 encima, 8 debajo,
9 todos los escritorios, 10 enrollar, 11 ayuda contextual, 12 menú de la aplicación (rectángulo,
`arg` = acción), 13 excluir de capturas. El auxiliar no ejecuta nada: el compositor decide.

## Configuración

El auxiliar lee los archivos de Plasma y se recarga en vivo (KConfigWatcher, el archivo y
`KGlobalSettings.notifyChange`): `kwinrc [org.kde.kdecoration2] library, theme, ButtonsOnLeft,
ButtonsOnRight, BorderSize, BorderSizeAuto, CloseOnDoubleClickOnMenu`; el esquema de color de
`kdeglobals` (como `decorationpalette.cpp` de KWin); la fuente `[WM] activeFont`; el tema de iconos;
y `breezerc` (lo lee la propia decoración Breeze).
