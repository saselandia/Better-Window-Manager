# Compatibilidad medida de Breeze (Kde plasma) con la KDE Store

Fecha de medición: **2026-11-27**. Entorno: Gentoo Linux, Hyprland 0.56.2 (sesión anidada aislada),
Plasma Frameworks 6.29.0 / Plasma 6.7.5 (`ksystemstats` y `kdeplasma-addons` instalados; `powerdevil`
no instalado).

> **Alcance de la muestra:** esta tabla mide una muestra concreta de **18 paquetes** —los dos más
> descargados devueltos por KNewStuff (`KNSCore`) en cada categoría, separando decoraciones Aurorae
> de decoraciones C++— ejecutados en raíces XDG temporales aisladas con `bubblewrap`. Los
> porcentajes describen **esta muestra**, no la cobertura total de la KDE Store.

## Resumen de la muestra (2026-11-27)

| Bloque | Muestra | Funciona | Funciona con diferencias | No funciona |
| :--- | :---: | :---: | :---: | :---: |
| **Temas y recursos de aspecto** (globales, estilos Plasma, colores, Aurorae, C++, iconos, cursores) | 16 | **12 (75 %)** | **4 (25 %)** | 0 (0 %) |
| **Plasmoides / widgets** | 2 | **1 (50 %)** | 0 (0 %) | **1 (50 %)** |
| **Total de la muestra** | **18** | **13 (72 %)** | **4 (22 %)** | **1 (6 %)** |

- **Instalación y retirada KNS:** 18 / 18 instalados sin errores y 18 / 18 retirados limpiamente
  (`0` archivos residuales).
- **Renderizado en compositor anidado:** 41 / 42 casos visuales cargaron y generaron capturas válidas
  (el único fallo corresponde a KDE Control Station).

## Tabla detallada por categoría

| Categoría (proveedor KNS) | Paquete (ID Store) | Versión | Descargas (KNS) | Instala / Retira | Carga y aspecto (anidado) | Opciones propias | Estado | Causa / notas |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| Tema global (`lookandfeel`) | [Sweet KDE](https://store.kde.org/p/1294729) (`1294729`) | — | 123 012 | Sí / Sí | Sí (1 panel, `Splash.qml` propio, `Logout.qml` Breeze) | — | **Funciona con diferencias** | El paquete no incluye `layout.js` ni `Logout.qml` propios (usa los nativos, igual que Plasma); los efectos/reglas exclusivos de KWin no existen en Hyprland y BWM conserva el cursor común entre skins. |
| Tema global (`lookandfeel`) | [Apple MacOS \[WhiteSur-Dark\]](https://store.kde.org/p/1400424) (`1400424`) | — | 184 103 | Sí / Sí | Sí (2 paneles, `Splash.qml` y `Logout.qml` propios) | — | **Funciona con diferencias** | Disposición de barra superior + dock cargada tras corregir la conversión de arrays JS en `layouttemplate.cpp` (fallo pequeño de BWM corregido en T7). Sin efectos exclusivos de KWin (blur/Kvantum) y cursor común de BWM conservado. |
| Estilo de Plasma (`plasma-themes`) | [Sweet KDE](https://store.kde.org/p/1294174) (`1294174`) | — | 140 729 | Sí / Sí | Sí (SVG cargado y capturado) | — | **Funciona** | Aplicado con `plasma-apply-desktoptheme` sin errores. |
| Estilo de Plasma (`plasma-themes`) | [Sweet Mars KDE](https://store.kde.org/p/1393498) (`1393498`) | — | 88 678 | Sí / Sí | Sí (SVG cargado y capturado) | — | **Funciona** | Aplicado con `plasma-apply-desktoptheme` sin errores. |
| Esquema de color (`colorschemes`) | [Sweet KDE](https://store.kde.org/p/1294011) (`1294011`) | — | 721 990 | Sí / Sí | Sí (capturado) | — | **Funciona** | Aplicado con `plasma-apply-colorscheme` sin errores. |
| Esquema de color (`colorschemes`) | [WhiteSur Color](https://store.kde.org/p/1398831) (`1398831`) | — | 452 240 | Sí / Sí | Sí (3 variantes: `WhiteSur`, `WhiteSurDark`, `WhiteSurAlt`) | — | **Funciona** | Las tres variantes aplican y renderizan sin errores. |
| Decoración Aurorae (`aurorae`) | [Sweet Aurorae](https://store.kde.org/p/1286856) (`1286856`) | `1.1.0` | 126 501 | Sí / Sí | Sí (2 variantes, escala 1,0 y 1,5) | — | **Funciona** | `Sweet-Dark` y `Sweet-Dark-transparent` cargan en `bwm-decorator` sin errores. |
| Decoración Aurorae (`aurorae`) | [Sweet Mars KDE](https://store.kde.org/p/1393497) (`1393497`) | — | 568 255 | Sí / Sí | Sí (2 variantes, escala 1,0 y 1,5) | — | **Funciona** | `Sweet-Mars` y `Sweet-Mars-transparent` cargan en `bwm-decorator` sin errores. |
| Decoración Aurorae (`window-decorations`) | [Layan aurorae theme](https://store.kde.org/p/1325238) (`1325238`) | — | 296 867 | Sí / Sí | Sí (escala 1,0 y 1,5) | — | **Funciona** | Carga en `bwm-decorator` sin errores. |
| Decoración Aurorae (`window-decorations`) | [Edna](https://store.kde.org/p/1367056) (`1367056`) | `3.1` | 250 006 | Sí / Sí | Sí (escala 1,0 y 1,5) | — | **Funciona** | Carga en `bwm-decorator` sin errores. |
| Decoración C++ (`window-decorations`) | [BreezeChameleon](https://store.kde.org/p/2327206) (`2327206`) | `6.5` | 1 601 | Sí / Sí | Sí (escala 1,0 y 1,5) | Sí (`breezerc`: cambio real de píxeles) | **Funciona con diferencias** | La tienda distribuye código fuente C++/CMake, no un binario listo desde KNS; requiere compilación/instalación del plugin KDecoration3 (igual que en Plasma). Una vez compilado, `bwm-decorator` lo carga y respeta sus opciones nativas. |
| Decoración C++ (`window-decorations`) | [Klassy](https://store.kde.org/p/2349019) (`2349019`) | `6.7.3` | 5 747 | Sí / Sí | Sí (escala 1,0 y 1,5) | Sí (`klassy/klassyrc`: cambio real de píxeles) | **Funciona con diferencias** | Misma causa: distribución en código fuente que requiere compilar/instalar el plugin KDecoration3. En `bwm-decorator` renderiza a 1,0 y 1,5 y aplica opciones de `klassyrc`. No se activan generadores externos ni cambios de tema global desde KNS. |
| Iconos (`icons`) | [Papirus](https://store.kde.org/p/1166289) (`1166289`) | `20250501` | 478 941 | Sí / Sí | Sí (3 variantes: `Papirus`, `Papirus-Dark`, `Papirus-Light`) | — | **Funciona** | Todas las variantes resuelven iconos nativos sin errores. |
| Iconos (`icons`) | [Candy icons](https://store.kde.org/p/1305251) (`1305251`) | `0.24` | 759 | Sí / Sí | Sí (capturado) | — | **Funciona** | Resuelve iconos nativos sin errores. |
| Cursores (`xcursor`) | [WhiteSur cursors](https://store.kde.org/p/1411743) (`1411743`) | — | 1 225 872 | Sí / Sí | Sí (24 px y 48 px vía `libXcursor`) | — | **Funciona** | Aplicado con `plasma-apply-cursortheme` y decodificado correctamente. En sesión diaria, BWM conserva el cursor común entre skins. |
| Cursores (`xcursor`) | [Sweet cursors](https://store.kde.org/p/1393084) (`1393084`) | — | 848 319 | Sí / Sí | Sí (24 px y 48 px vía `libXcursor`) | — | **Funciona** | Aplicado con `plasma-apply-cursortheme` y decodificado correctamente. En sesión diaria, BWM conserva el cursor común entre skins. |
| Plasmoide (`plasmoids`) | [Andromeda Launcher Plasma 6](https://store.kde.org/p/2144212) (`2144212`) | — | 209 353 | Sí / Sí | Sí (capturado) | Sí (2 páginas; guardar/cancelar/recargar) | **Funciona** | Revisado antes de ejecutar (sin órdenes automáticas). Abre sin errores y persiste sus preferencias sin afectar a otras instancias. |
| Plasmoide (`plasmoids`) | [KDE Control Station](https://store.kde.org/p/2196105) (`2196105`) | `2.13.0` | 169 108 | Sí / Sí | **No** (fallo al cargar `NightLightPage.qml`) | Parcial (5 páginas de config cargan y guardan) | **No funciona** | **Paquete/servicio ausente:** importa `org.kde.plasma.private.brightnesscontrolplugin` (de PowerDevil, no instalado ni activado en Breeze por conflicto con `BwmIdle`, véase `docs/BREEZE_T6_RESULTS.md`). Revisado antes de cargar; sus acciones de órdenes/energía no se ejecutan. |

## Causas identificadas y trabajo futuro

1. **Corregido en T7 (fallo pequeño de BWM):** `LayoutTemplateWidget::writeConfig` recibía `QVariant`
   en vez de `QJSValue`, lo que descartaba listas pasadas como arrays de JavaScript por scripts
   `layout.js` originales (detectado con WhiteSur-Dark). Corregido siguiendo `scripting::Applet` de
   Plasma 6.7.5 y cubierto por regresión en `test-t4-session`.
2. **Paquete/servicio ausente (trabajo futuro):** widgets que importan módulos privados de
   **PowerDevil** (`org.kde.plasma.private.brightnesscontrolplugin`, como KDE Control Station) no
   cargan mientras PowerDevil siga sin integrarse ni coordinarse con `BwmIdle` / `bwm-power`.
3. **API de KWin ausente (límite estructural):** efectos de compositor exclusivos de KWin (blur
   personalizado, esquinas o scripts de KWin) que acompañan a algunos temas globales no corren sobre
   Hyprland.
4. **Decoraciones C++ desde la tienda:** al igual que en Plasma, KNS descarga el código fuente y no
   compila ni instala plugins nativos KDecoration3 automáticamente. `bwm-decorator` sí es compatible
   con ellos una vez compilados en una ruta de plugins Qt.
5. **Seguridad y aislamiento de KNS:** los proveedores de dependencias de temas globales en KNS
   crean motores propios que pueden escribir en `~/.icons` (`InstallPath=.icons` de `xcursor.knsrc`).
   El arnés de pruebas T7 lo contiene con `bubblewrap` y enlaza `~/.icons` a la carpeta temporal.
