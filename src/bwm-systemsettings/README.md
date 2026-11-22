# KCM nativos de BWM para System Settings — R2 parcial

El anfitrión es **systemsettings real**, sin una copia de su interfaz en Quickshell. Primer
módulo de prueba funcional: `kcm_bwm_nightlight`, un `KCModule` QWidget de KDE. No sustituye
las páginas actuales ni el lanzador de Super+I hasta completar la migración R2/R3.

## Contrato comprobado

- Factory `K_PLUGIN_CLASS_WITH_JSON`, metadata embebida, namespace
  `plasma/kcms/systemsettings` y categoría nativa `display`.
- `systemsettings --list` de KDE 6.7.5 descubre el módulo con `QT_PLUGIN_PATH` del prefijo.
- KPluginFactory lo instancia como `KCModule` real; Widgets conserva estilo/foco nativos.
- Lectura, cambio pendiente, Predeterminados sin guardar, Restablecer, Aplicar y error de
  backend cubiertos con QtTest offscreen. Datos/controlador **falsos y aislados** en las pruebas.
- La configuración real se delega a `nightlight.py --status` y a una única transacción
  `--temperature K --on|--off`. No duplica el servicio ni escribe JSON de Quickshell desde C++.
- `save()` concluye la transacción antes de devolver el control: el host puede destruir la
  página al navegar. Timeout limitado, errores visibles y cambios pendientes conservados.
- El backend real no se ejecutó para probar: incluso `nightlight.py --status` puede migrar
  datos antiguos. No usar la configuración del usuario como fixture.

## Compilar, probar e instalar

Desde el repo:

```bash
make -C src/bwm-systemsettings test
make -C src/bwm-systemsettings install
bash config/hypr/skins/plasma/scripts/settings-native.sh --list
bash config/hypr/skins/plasma/scripts/settings-native.sh kcm_bwm_nightlight
```

La instalación reemplaza el módulo mediante temporal + rename atómico, sin truncar un .so
que pueda estar cargado en Preferencias.

Sin sudo. Prefijo por defecto `~/.local/share/bwm/systemsettings`; `PREFIX` lo cambia. Si se usa
`XDG_DATA_HOME`, instalar con `PREFIX="$XDG_DATA_HOME/bwm/systemsettings"`. La ruta de plugins se
aplica sólo al proceso de prueba, sin alterar variables globales o archivos de KDE.

Paquetes de desarrollo usados: Qt6 Widgets, KF6 KCMUtils/CoreAddons/I18n y CMake; Qt6 Test sólo
para tests. Ya disponibles en la máquina inspeccionada. Declarado como recomendación experimental
en el catálogo BWM. No inicia KWin, plasmashell, PowerDevil ni un nuevo dueño D-Bus.

La instalación se probó **sólo bajo /tmp**, no en el prefijo del usuario. Para revertir una
instalación manual de este prototipo basta retirar ese `.so` del prefijo BWM cuando System
Settings esté cerrado. No borrar plugins del sistema. `open-settings.sh` sigue intacto.

## Pendiente antes de activar el nuevo lanzador

Inventario de páginas en `docs/BREEZE_R2_RESULTS.md`. Faltan los demás KCM BWM, autoridad del
puente, todos los alias, traducciones completas, cambios sin guardar entre páginas y validación
visual en la sesión real. El módulo de luz nocturna es prueba de la arquitectura y puede
reemplazarse por el KCM KDE original si R3 aporta el adaptador necesario. No ofrecer dos
configuradores contradictorios al cerrar la migración.

Código propio BWM, GPL-2.0-or-later. Uso de APIs públicas KF6 6.29.0 y Qt 6.11.2; sin copiar
fuentes de KDE. No se carga este módulo en Hyprland ni en la barra Quickshell.

## R3: adaptadores y perfil de compatibilidad

Se añaden ocho `KCModule` QWidget (`kcm_bwm_cursor`, `screens`, `workspaces`, `apps`,
`startup`, `shortcuts`, `energy`, `windows`). Usan `scripts/native-settings.py` de Breeze;
los ajustes comunes se delegan a los gestores comunes. La energía usa la misma sección
`idle` que `BwmIdle.qml`, mediante `bwm-shared-settings.py`; no arranca PowerDevil.

Los controles se generan desde valores/opciones devueltos por los gestores. Es un protocolo
entre la vista y el controlador, no un formato nuevo de temas. Aplicar envía sólo cambios,
con revisión de la página, valida el lote entero, guarda y relee. Un error conserva el estado
pendiente. Varias operaciones de gestores no forman una transacción distribuida: un fallo
puede haber aplicado algunas; Restablecer relee el estado. No se inventan Predeterminados
para la selección de aplicaciones, monitores ni atajos personales. Los procesos tienen plazos.

`settings-native.sh` usa el perfil KAuthorized de `settings-profile/kdeglobals` sólo para ese
proceso con `XDG_CONFIG_DIRS`. Sus restricciones inmutables retiran los KCM que requieren
servicios no portados o contienen controles sin aplicación. El anfitrión y los formularios KDE
siguen siendo originales; no se eliminan plugins del sistema. Los alias compartidos abren
su KCM BWM equivalente. El lanzador predeterminado de R2 sigue pendiente de migración.

`bwm-kcm-catalog` descubre metadatos KDecoration3 y `X-KDE-ConfigModule`; `--probe` carga
explícitamente las fábricas y proveedores nativos, incluidos Aurorae/temas de terceros. Sin
`--probe` no ejecuta código de los plugins. El KCM de decoraciones original sigue siendo
quien presenta sus formularios, sin copiar una lista de opciones a BWM.

Informe y diferencias por control: `docs/BREEZE_R3_RESULTS.md`. Nueve módulos contando la luz
nocturna de R2. Compilación/instalación aislada y pruebas pasadas; sin instalación en el prefijo
real ni cambios de sesión. Los KCM de ventanas fallan con mensaje si no hay Breeze o IPC.

## R7: Efectos de escritorio

Décimo KCM contando luz nocturna: `kcm_bwm_effects`, categoría nativa `desktopbehavior`.
`settings-native.sh effects` (o `kcm_kwin_effects` / `kcm_animations`) abre este adaptador.
Mismo controlador `native-settings.py effects` que la página de las Preferencias actuales;
seis toggles, intensidad de desenfoque, duración/escalas y factor global. Sólo esta página de
gestores aporta defaults KDE explícitos. Restablecer relee; Predeterminados deja un borrador.

Instalado atómicamente en el prefijo local y descubierto por `systemsettings --list` el
2026-11-21. Pruebas de persistencia en XDG temporal, sin guardar ajustes de efectos diarios.
No cambia el lanzador habitual. Límites y verificaciones: `docs/BREEZE_R7_RESULTS.md`.
