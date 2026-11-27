# Breeze III — T7: compatibilidad medida con la tienda KDE

Fecha: 2026-11-27. Plan: [BREEZE_PLAN_V3.md](BREEZE_PLAN_V3.md). Tabla publicada en
[BREEZE_STORE_COMPAT.md](BREEZE_STORE_COMPAT.md).

## Objetivo y metodología

Sustituir la estimación previa (~50 % de temas, 0 % de plugins) por una medición reproducible con
`KNSCore` y raíces XDG desechables en todas las categorías de la tienda KDE: temas globales, estilos
de Plasma, esquemas de color, decoraciones (separando Aurorae y C++), iconos, cursores y plasmoides.

Para aislar por completo la sesión diaria del usuario:
- `src/bwm-plasma-host/kns-store.cpp` y `src/bwm-plasma-host/store-compat.py` ejecutan `KNSCore`
  sólo sobre raíces temporales privadas (`0700`) bajo `/tmp`, dentro de `bubblewrap` con el sistema
  de archivos del anfitrión en sólo lectura y red desactivada al renderizar (`--unshare-net`).
- Al probar dependencias de un tema global se detectó que `KNSCore` instancia motores propios para
  `xcursor.knsrc` (`InstallPath=.icons`), escribiendo en `~/.icons`. Se corrigió el aislamiento
  enlazando `~/.icons` dentro del sandbox a la carpeta temporal `data/icons` del elemento y
  verificándolo con `tests/test_breeze_store.py`. El cursor temporal que llegó a crearse (`WhiteSur`)
  se retiró y los archivos diarios quedaron intactos.
- Todo widget o código externo (plasmoides, `layout.js`/`Splash.qml`/`Logout.qml` de temas globales
  y fuentes C++ de decoraciones) se revisó manualmente y se selló por hash SHA-256 en `review.json`
  antes de ejecutarse en `check-store-session.py` / `prepare-store-fixtures.py`. No se ejecutó ningún
  binario descargado ni acciones de órdenes/energía de widgets.

## Resultados de la muestra (18 paquetes)

- **Temas y recursos de aspecto (16 paquetes):** **12 / 16 (75 %)** funcionan sin cambios y
  **4 / 16 (25 %)** funcionan con diferencias (los 2 temas globales por ausencia de efectos KWin y
  política común de cursor; las 2 decoraciones C++ por distribuirse como código fuente que requiere
  compilación del plugin KDecoration3). **0 / 16** fallan.
- **Plasmoides (2 paquetes):** **1 / 2 (50 %)** funciona completo (`Andromeda Launcher Plasma 6`,
  incluyendo persistencia de opciones y segunda instancia intacta) y **1 / 2 (50 %)** no carga
  (`KDE Control Station`, por ausencia de `org.kde.plasma.private.brightnesscontrolplugin` de
  PowerDevil; sus 5 páginas de configuración sí cargan y guardan).
- **Total de la muestra:** **13 / 18 (72 %)** funcionan, **4 / 18 (22 %)** funcionan con diferencias,
  **1 / 18 (6 %)** no funciona.
- **Ciclo KNS completo:** **18 / 18** instalados sin errores y **18 / 18** retirados limpiamente sin
  archivos residuales (`build/breeze-t7/uninstall.json`).
- **Compositor anidado (`check-focus-safety.py` + `check-store-session.py`):** **41 / 42** casos
  visuales cargados con capturas no uniformes comprobadas; `dailyHostStarted=false`,
  `physicalOutputsUnchanged=true`, `cleanupVerified=true`.
- **Opciones propias comprobadas:**
  - `Andromeda Launcher Plasma 6`: guardar, cancelar sin escribir, recargar y aislar segunda instancia (`exercisePassed=true`).
  - `BreezeChameleon` (`breezerc`) y `Klassy` (`klassy/klassyrc`): cambios de configuración nativa
    reflejados en los píxeles renderizados por `bwm-decorator` (`changedPixels=true`), además de
    escala `1.5`.

## Fallo de BWM encontrado y corregido

Al ejecutar el script `layout.js` original de **WhiteSur-Dark** (`1400424`), su lista de lanzadores
del dock se pasaba a `writeConfig` como un array de JavaScript. `LayoutTemplateWidget::writeConfig`
aceptaba `QVariant` directamente, dejando un `QJSValue` sin convertir que `KConfig` descartaba en
silencio.

- **Corrección:** `src/bwm-plasma-host/layouttemplate.{h,cpp}` acepta ahora `QJSValue`, lo convierte
  con `toVariant()`, actualiza el esquema `KConfigLoader` original (`setProperty` / `save` / `read`)
  y escribe en el grupo, replicando el contrato de `scripting::Applet` de Plasma 6.7.5.
- **Regresión:** `originalScriptArrayUpdatesSchemaAndSurvivesReload` añadida a
  `src/bwm-plasma-host/test-t4-session.cpp` (`3 passed, 0 failed`).

## Pruebas ejecutadas

| Prueba | Resultado |
| :--- | :--- |
| `tests/test_breeze_store.py` | **5/5 PASS** (guardas de raíz temporal, aislamiento `bwrap` de `~/.icons` y host sólo lectura, hash de revisión, rechazo previo a Qt en `kns-store`) |
| `tests/test_breeze_t6.py`, `test_breeze_startup.py`, `test_kde_shortcuts.py` | **21/21 PASS** (26/26 junto con `test_breeze_store.py`) |
| `test-t4-session originalScriptArrayUpdatesSchemaAndSurvivesReload` | **3/3 PASS** (`build/breeze-t7/array-regression.log`) |
| `ctest --test-dir build/bwm-plasma-host-tests --output-on-failure` | **16/16 PASS** (57,46 s) |
| `check-focus-safety.py --binary src/bwm-plasma-host/check-store-session.py` | **PASS** (`41/42` cargados; único fallo esperado: KDE Control Station; `build/breeze-t7/nested.json`) |
| Retirada KNS (`store-compat.py` / `kns-store uninstall`) | **18/18 PASS** (`0` errores, `0` archivos restantes; `build/breeze-t7/uninstall.json`) |

## Requisitos, documentación y límites

- `bwm-plasma-store-tests` añadido a `config/hypr/skins/requirements.json` y a `recommends` de
  Breeze (`bubblewrap`, `libXcursor`, `kcolorscheme`, `kiconthemes` sólo para repetir el arnés T7);
  `docs/REQUIREMENTS.md` regenerado.
- Porcentajes actualizados con el dato medido y fecha `2026-11-27` en `README.md`, `README.es.md` y
  `docs/SKINS.md`.
- **Límites:** los resultados corresponden a la muestra de 18 paquetes más descargados, no a toda la
  KDE Store. Las capturas visuales se tomaron en Hyprland anidado con vistas directas porque la
  salida virtual carece de EDID para la disposición multi-monitor completa. El binario de producción
  en `build/bwm-plasma-host` se recompila con el arreglo de `layouttemplate.cpp` sin reiniciar la
  sesión diaria.
