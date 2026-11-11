# Preferencias del sistema de Breeze (F11)

Ventana `plasmaSettings.qml` (proceso `qs -p` aparte, lo lanza `open-settings.sh [página]` y Super+I).

| Pieza | Origen |
| :--- | :--- |
| `Main.qml`, `SideBarItem.qml`, `CategoriesPage.qml`, `SubCategoryPage.qml`, `CategoryItem.qml`, `HamburgerMenuButton.qml` | systemsettings **v6.7.5** `app/qml/` (LGPL-2.0-only). Cambios marcados `// BWM:` |
| `SettingsState.qml` | BWM: lo que en systemsettings da el objeto C++ `systemsettings` (modelos de categorías, subcategorías y búsqueda, módulo activo) |
| `Catalog.js` | BWM: páginas y categorías (orden y nombres de `categories/settings-*.desktop`) |
| `ModuleView.qml` | BWM: zona del módulo de `app/ModuleView.cpp` (cabecera, Ayuda/Predeterminados/Restablecer/Aplicar, cambios sin aplicar) |
| `KcmPage.qml` | BWM: un KCM real de Plasma con `KcmHost` de `org.bwm.kcm` (`src/bwm-kcmhost`, `make install`) |
| `KdeSettingsStore.qml`, `pages/` | BWM: páginas propias que escriben los archivos de KDE con `kwriteconfig6 --notify`; las aplica el puente F2 |

Tipos de página (`kind` en `Catalog.js`): `kcm` (KCM QML incrustado), `bwm` (página común de
`modules/settings/`, sin duplicar su lógica), `page` (propia de Breeze) y `launch` (abre la app de
`Config.options.apps.*`, para módulos sólo QWidget o no instalados).

Actualizar desde upstream: comparar los seis archivos portados con `app/qml/` de la nueva etiqueta
y volver a aplicar los cambios `// BWM:`. Las cadenas usan el catálogo instalado `systemsettings`.

Límites: los KCM de QWidget (`kcm_kwinoptions`, `kcm_networkmanagement`) no se incrustan; el de
Bluetooth (bluedevil) no está instalado. Sin insignias de «cambios resaltados» en la barra lateral
(sólo en el KCM abierto). Sin Ayuda local (abre docs.kde.org).
