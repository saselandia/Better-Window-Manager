# R2 — System Settings real: primera integración nativa (parcial)

2026-11-12. **R2 no está terminada.** Super+I/open-settings.sh siguen con el host anterior para
conservar las opciones BWM hasta completar su migración. No se instaló nada en el prefijo del usuario.

## Comprobado

- Nuevo `src/bwm-systemsettings`: plugin `KCModule` QWidget real, factory/metadata KDE y
  categoría display. Primer módulo: luz nocturna compartida, con el controlador común BWM.
- Compilación CMake con Qt 6.11.2 / KF6 KCMUtils 6.29.0 correcta.
- Pruebas C++ offscreen de lectura, cambios, Aplicar, Restablecer, Predeterminados sin escritura,
  fallo del controlador conservando cambios y descubrimiento/instanciación KPluginFactory.
- **La aplicación `/usr/bin/systemsettings` 6.7.5**, ejecutada con `--list` y el prefijo de
  plugins temporal, devuelve `kcm_bwm_nightlight - Night Light shared by all BWM skins`.
  No es sólo el host Quickshell ni sólo el harness quien lo descubre.
- Instalación de prueba en `/tmp/bwm-r2-prefix`. No se ejecutó el backend real de luz nocturna:
  tests usan script/estado falsos. El estado real y el texto del usuario siguen intactos.
- Entrada experimental `skins/plasma/scripts/settings-native.sh`: QT_PLUGIN_PATH sólo para
  systemsettings, sin cambiar entorno global ni servicios KDE. No se añade a Super+I aún.
- Nuevo módulo declarado como recomendación experimental y en parts; tabla de requisitos
  regenerada. Dependencias de desarrollo ya presentes; no se necesita sudo para compilarlo.

## Antes de sustituir el lanzador

| Páginas actuales / alias | Destino | Estado |
| :--- | :--- | :--- |
| colores, temas globales, estilo, decoraciones, iconos, fuentes, sonido, reglas | KCM KDE ya instalados | Anfitrión real disponible; verificar aplicación y puente en R3 |
| Comportamiento de ventanas | kcm_kwinoptions QWidget real | Puede cargar en host nativo; falta cobertura efectiva del puente |
| cursor, pantallas, workspaces, atajos, autostart, apps predeterminadas | KCM nativos con gestores comunes BWM | Migración pendiente; no duplicar controladores |
| red/Bluetooth | KCM originales y servicios compartidos | Inventariar proveedor, módulos instalados y acciones sin duplicar agentes |
| General, servicios, energía/inactividad, arranque, About | KCM BWM con controles KDE | Pendientes; conservar alcance de acciones sudo/arranque |
| panel, widgets, fondo | Interfaces de configuración originales y anfitrión R4–R5 | Contratos todavía pendientes |
| Luz nocturna | Primer KCM BWM real | Pruebas aisladas aprobadas; prueba visual y controlador real pendientes |
| SETTINGS_PAGE y alias | Mapa a módulos/destinos reales | Pendiente; no perder páginas al hacer la transición |

## Probar mañana (opcional, sin sudo)

Desde el repo, `make -C src/bwm-systemsettings test` y
`make -C src/bwm-systemsettings install`. Después:

```bash
bash config/hypr/skins/plasma/scripts/settings-native.sh --list
bash config/hypr/skins/plasma/scripts/settings-native.sh kcm_bwm_nightlight
```

Abrir no debería modificar ajustes salvo la migración antigua que pueda realizar nightlight.py;
Aplicar sí actúa sobre la luz nocturna común. Leer antes README del módulo. No hay reinicio de
sesión necesario para el KCM. No cambiar globalmente variables KDE ni arrancar plasmashell/KWin.
La prueba visual, traducciones completas, callbacks del host al salir con cambios, otros KCM
BWM y migración final siguen pendientes. R3–R5 no se dan por ejecutadas.
