# Kickoff de Plasma sobre Quickshell (F4)

Lanzador de aplicaciones de la skin Breeze. Es el **Kickoff de KDE Plasma v6.7.5**
([plasma-desktop/applets/kickoff](https://invent.kde.org/plasma/plasma-desktop/-/tree/v6.7.5/applets/kickoff),
GPL-2.0-or-later) con su QML casi sin cambios. Todo lo adaptado lleva un comentario `// BWM:`.
Lo carga `panelFamilies/IllogicalImpulseFamily.qml` sólo en Breeze (`KickoffWindow`). Al instalar o
cambiar archivos nuevos del módulo hace falta un reinicio de mantenimiento del shell
(`bwm-theme-manager.py set <skin-actual> --restart-shell`).

## Datos: los de Plasma

No se sustituye ningún modelo: son los de `org.kde.plasma.private.kicker` (plasma-workspace),
que funcionan fuera de Plasma una vez que se llama a `rootModel.refresh()`, como hace el original.

- Aplicaciones y categorías: `Kicker.RootModel` sobre KService y el menú `plasma-applications.menu`
  (necesita `XDG_MENU_PREFIX=plasma-`, que pone `hypr/modules/environment.lua` como startplasma).
- Búsqueda: `Kicker.RunnerModel` (KRunner con los runners instalados: aplicaciones, ajustes,
  archivos recientes, lugares, calculadora, órdenes…).
- Favoritos y recientes: KActivities (`kactivitymanagerd`), en el formato de Plasma, cliente
  `org.kde.plasma.kickoff.favorites.instance-bwm`. La primera vez se pasan los de
  `bar.plasma.kickoff.favorites`, como `portOldFavorites` en Plasma.
- Lugares: `Kicker.ComputerModel` y `RecentUsageModel`.
- Avatar y nombre: `KUser`; el avatar abre `kcm_users`.
- Las apps se lanzan con KIO (`ApplicationLauncherJob`), cada una en su propio scope de systemd.

## Qué cambia respecto al original

- `main.qml` → `Kickoff.qml`: un `Item` normal en vez de `PlasmoidItem`. Ofrece `expanded`,
  `hideOnWindowDeactivate` y `fullRepresentationItem`, sincronizados con `GlobalStates.plasmaKickoffOpen`,
  y no tiene la representación compacta (el botón es el del panel, `modules/plasma/panel`).
- `Plasmoid.qml`: singleton que sustituye al attached `Plasmoid` de libplasma (configuración, borde,
  forma, icono). La configuración son las claves de `main.xml`, guardadas en `bar.plasma.kickoff`
  de `Config.qml` en vez de en `plasma-org.kde.plasma.desktop-appletsrc`.
- `KickoffI18n.qml`: `i18n()`/`i18nc()` con el dominio `plasma_applet_org.kde.plasma.kickoff`.
  Los catálogos son los originales (`po/`, del paquete publicado plasma-desktop-6.7.5) y los compila
  `plasma-theme.py translations` (también al entrar en Breeze) en `~/.local/share/locale`.
- `ActionMenu.qml` y el menú de `LeaveButtons.qml`: `PC3.Menu` en vez de `PlasmaExtras.Menu`, que es
  un QMenu y no puede abrir su ventana emergente desde una capa de layer-shell. Se omiten los
  separadores sobrantes (QMenu lo hace solo) y «Editar aplicación…» si no está kmenuedit.
- `LeaveButtons.qml`: las acciones de sesión van a `config/hypr/scripts/bwm-power` (bloquear,
  cerrar sesión, suspender, hibernar, reiniciar, apagar). `SystemModel` sigue decidiendo cuáles hay;
  «Cambiar de usuario» y «Guardar sesión» no se ofrecen (no hay ksmserver).
- `KickoffWindow.qml` (propio): hace de PlasmaQuick::Dialog. Es una capa con el fondo
  `solid/dialogs/background` del estilo de Plasma activo, porque Breeze no desenfoca y Plasma usa
  la variante sólida sin desenfoque. No dibuja el borde que toca al panel pegado y se alinea con el
  botón. Se cierra al pulsar fuera salvo que esté fijado, y con Escape (primero vacía la búsqueda),
  como el diálogo de Plasma.
- Sin la página de configuración de Kickoff (`ConfigGeneral.qml`, `config.qml`): llegará con las
  Preferencias de F11. «Editar aplicaciones…» del menú del plasmoide tampoco está.

## Apertura

Botón del panel (anclado a él), Super y Alt+F1 (`keybinds.json`, sólo en Breeze), y la IPC de
siempre: `qs -c ii ipc call plasmaKickoff toggle|open|close`.

## Pruebas

`BWM_RUN_QML_TESTS=1 python3 -m unittest tests.test_plasma_kickoff_ui -v`: teclas reales de QtTest
en una instancia aparte. Comprueba los modelos, la búsqueda y el lanzamiento con Intro de una app de
prueba, la navegación como en Plasma, el menú contextual, Escape y los botones de sesión. No
escribe la configuración y usa otro cliente de favoritos, que vacía al terminar.
