# Mosaico y previsualización de Breeze (F10)

`Outline.qml` porta KWin **v6.7.5**, `src/qml/outline/plasma/outline.qml`: conserva avisos,
licencia, `widgets/translucentbackground` y la omisión de bordes pegados al área útil. BWM
sustituye `org.kde.kwin`, `Workspace` y el objeto `outline` por geometría lógica de Hyprland
recibida en IPC `plasmaOutline display <JSON>` / `hide <sequence>`. PanelWindow sin entrada, sólo en Breeze.
El color, textura y márgenes vienen del estilo de Plasma; no hay un rectángulo azul propio.
Los textos de licencia están en `licenses/KDE-GPL-2.0-only.txt`, `KDE-GPL-3.0-only.txt` y
`KDE-LicenseRef-KDE-Accepted-GPL.txt`.

`TileEditor.qml` es un editor BWM reducido (GPL-2.0-or-later) sobre el **mismo JSON de KWin**,
no una copia del efecto `tileseditor` (éste depende de la escena y API de efectos de KWin).
Meta/Super+T lo abre sólo en Breeze; Ctrl+flechas se conserva por decisión del usuario.
Permite dividir horizontal/vertical, unir una división, repartir zonas con una proporción,
cambiar la separación y elegir pantalla/distribución importada. Mayús+arrastre elige una hoja.
Guardar pasa por `skins/plasma/scripts/kwin-tiles.py`: conflicto de edición → se rechaza,
sin sobreescribir el cambio de KDE. Cancelar no escribe nada. El puente F2 agrupa la recarga.

Referencias de formato y geometría: KWin v6.7.5 `src/tiles/{tilemanager,customtile,tile,quicktile}.cpp`,
`src/plugins/tileseditor/qml/` y `src/workspace.cpp`. El adaptador Python/C++ es independiente,
sin copiar C++ de KWin ni cargar Qt dentro de Hyprland.

Los layouts viven en `kwinrc [Tiling][<desktop UUID>][<output UUID>]`, claves `tiles` y `padding`.
La lista de escritorios usa los Id_N originales de `[Desktops]`; si faltan al guardar, se crea
un UUID estable para ese workspace de BWM. Se leen también grupos antiguos `[Tiling][output]`.
KWin asigna UUIDs de pantalla aleatorios; Hyprland no los publica. Una asociación **sólo de máquina**
en `~/.local/state/bwm/plasma/tiling-outputs.json` enlaza la descripción del monitor con su UUID.
En el editor se puede elegir una distribución importada y guardarla para asociarla a esa pantalla.
No se identifica ninguna pantalla por DP-N. Sin asociación se usa un UUID estable derivado de
`desc:` y la disposición por defecto de KWin (tres columnas 25/50/25). Ese UUID nuevo no se
asocia automáticamente al mismo monitor si se vuelve a ejecutar KWin: se necesita la asociación.

Límites del editor: no es la superposición original de KWin, no hay arrastre libre de divisores,
zonas flotantes dibujables ni control de varios escritorios a la vez. El lector acepta el árbol
horizontal/vertical/flotante original y el editor puede subdividir/unir sus hojas. Guardar requiere
Breeze activa. Las pruebas de lectura/editor se ejecutan con configuración XDG temporal sin llamadas
reales que cambien ventanas; la carga QML se comprobó aparte con `qs -p`. F10 no se ha probado en
la sesión del compositor con el plugin nuevo: lista de ratón en `docs/BREEZE_F10_CHECKLIST.md`.
Los Loader nuevos requieren reiniciar el shell; el reinicio de sesión pendiente del plugin lo cubre.
