# Temas y configuración KDE de Breeze

Código propio de BWM. `plasma-theme.py` aplica los formatos originales de temas; `plasma_palette.py`
lee el esquema de KDE. `kde-config-bridge.py` sincroniza ajustes y gestiona su vigilante de sesión.
La autoridad de cada ajuste y las limitaciones están en `docs/BREEZE_ARCH.md` §9.

Fuentes consultadas para F2 (sin copiar código):

- KDE Plasma **v6.7.5**, `plasma-desktop/kcms/keyboard/{keyboardsettings,keyboardmiscsettings}.kcfg`.
- `kwin/src/kwin.kcfg`, `kwin/src/plugins/nightlight/nightlightsettings.kcfg`.
- `plasma-workspace/kcms/fonts/fontssettings.kcfg` y `kcms/krdb/krdb.cpp`.
- KDE Frameworks **v6.29.0**, `kconfig/src/core/{kconfig,kconfigwatcher}.cpp`:
  señal `org.kde.kconfig.notify.ConfigChanged(a{saay})`.

Repositorios correspondientes en `https://invent.kde.org/plasma/` y
`https://invent.kde.org/frameworks/kconfig`. Se respetan los grupos/claves originales; no hay un
formato de tema nuevo. Los Lua generados y el estado de resolución de conflictos son cachés locales.

`enter` → `export/import` → `watch` (sólo en Breeze), `leave` al salir. `start` lanza watch a través
de `bwm_session.spawn`; `stop` verifica PID/argv y espera a que termine la escritura. `guards` se
puede ejecutar sin Breeze para preparar las protecciones contra servicios duplicados de KDE.
