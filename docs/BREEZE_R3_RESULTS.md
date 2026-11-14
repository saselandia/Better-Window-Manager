# R3 — adaptadores nativos y autoridad de configuración

2026-11-12. **Implementación parcial; aceptación de sesión y equivalencia completa pendientes.**
Sólo R3. Se aprovechan los resultados R0–R2; no se migra el lanzador predeterminado de R2,
no se adelantan R4–R7 y no se reactivan sombras ni capturas. El usuario confirma que el reinicio
único del shell corrigió los iconos del incidente anterior.

## Cambios

- Ocho nuevos KCM QWidget reales, con factories y metadatos KDE, sobre los gestores comunes;
  nueve módulos con luz nocturna R2. `systemsettings` 6.7.5 descubre todos, no sólo un harness.
- `native-settings.py`: protocolo de vista sin almacenamiento paralelo. Validación de todo el
  lote, revisión optimista de página, candado entre instancias, Aplicar explícito y lectura
  posterior. Un resultado que no confirma los valores provoca error; los cambios pendientes
  no se descartan. Las acciones de varios gestores pueden aplicarse parcialmente si falla una;
  no se promete rollback distribuido. Restablecer relee, sin inventar valores de fábrica.
- `bwm-shared-settings.py`: transacción de los tres tiempos comunes de `Config.idle`; conserva
  claves ajenas, enlaces y permisos, comprueba concurrencia y respeta el overlay del usuario.
  La autoridad sigue siendo la misma configuración que consume BwmIdle en las tres skins.
- El puente conserva `pendingReload` cuando falla Hyprland y reintenta aunque los archivos
  generados ya no cambien. Vigila también todos los archivos relevantes de `kdedefaults` y
  `XDG_CONFIG_DIRS`. Eventos de directorios ajenos no posponen indefinidamente el debounce
  de 300 ms. No hay recarga por cada cambio del formulario antes de Aplicar.
- Inventario legible por máquina: `settings-capabilities.json`, accesible con
  `kde-config-bridge.py capabilities`. Documenta autoridad/dirección, consumidores, APIs
  ausentes y contrato de R7. No afirma que sus efectos estén implementados.
- `settings-native.sh` aplica un perfil **KAuthorized/Kiosk** mediante `XDG_CONFIG_DIRS`
  sólo al proceso. No cambia metadatos ni archivos KDE del sistema o preferencias del usuario.
  Retira módulos incompatibles y redirige alias a los adaptadores. Mecanismo contrastado con
  la cabecera pública `kauthorized.h` de KF6 Config 6.29 y con el anfitrión instalado.

## Control → archivo/API → efecto real → verificación

«Fixture» significa prueba aislada; no demuestra la sesión del usuario. «Consumidor existente»
identifica la ruta de aplicación inspeccionada, no una nueva aceptación visual.

| Control / módulo | Archivo o API y autoridad | Efecto real / equivalencia | Verificación y límite |
| :--- | :--- | :--- | :--- |
| Foco, `kcm_bwm_windows` | KDE `kwinrc [Windows] FocusPolicy` → puente → `input.follow_mouse` | Clic o seguimiento de ratón | Escritura → Lua → recarga simulada → lectura; vuelta de skin en fixture. Seguimiento es aproximación; no AutoRaise, ClickRaise ni retardo. Original kwinoptions restringido. |
| Colocación | KDE `kwinrc [Windows] Placement` → `placement.lua` | Smart, Centered, ZeroCornered, UnderMouse, Random, Maximizing, NoPlacement | Lectura/escritura nativa y consumidor existente; no nuevo ensayo visual. No se ofrece OnMainWindow como equivalencia garantizada. |
| Encaje magnético | KDE BorderSnapZone, WindowSnapZone, CenterSnapZone → `breezebars.snap_config` | Distancias del plugin BWM sobre marcos KDE | Sólo se ofrecen controles si el plugin se anuncia cargado; fixture cambia 13 → 29 y produce un reload. Ratón/ambos monitores pendientes. Otras opciones de encaje se conservan; no se añaden controles ignorados. |
| Doble clic de barra | KDE TitlebarDoubleClickCommand → breezebars → kwin-window.py | Maximizar normal/por eje, minimizar, cerrar, nada | Catálogo de acciones permitido; sólo con plugin. No equivale a controlar una barra CSD de la aplicación. |
| Decoración y botones | `kwinrc [org.kde.kdecoration2]` → bwm-decorator → KDecoration3 | Selección de biblioteca/tema, borde y bancos de botones nativos | Consumidor existente; pruebas nuevas de factory/config/render detalladas abajo. Acciones no existentes de KWin siguen siendo límite; no se certifican todos los botones. |
| Opciones de decoración instalada | `X-KDE-ConfigModule` → namespace `org.kde.kdecoration3.kcm`; archivo del plugin | Formulario original y opciones propias, sin lista fija BWM | Breeze `drawBackgroundGradient`: load → checkbox → save → nueva instancia → render distinto. Sin comprobar ventanas vivas. |
| Temas de terceros | `DecorationThemeProvider` de la factory; configurationName por tema | Descubre módulos de los cinco Sweet instalados | Provider Aurorae devuelve identificadores Sweet y `kcm_auroraedecoration`; no se añade una opción ficticia propia de Sweet. Configuración completa de todos los terceros no certificada. |
| Animación, duración | KDE `kdeglobals [KDE] AnimationDurationFactor` → kwin.lua y componentes KDE | Cero desactiva; factor cambia duración de las curvas actuales | Fixture escribe 0.5 y relee; no se cambia el motor ni se afirma fidelidad Plasma. kcm_animations y efectos KWin retirados del perfil. R7 implementará efectos/curvas y su KCM. |
| Pantalla/escala, `kcm_bwm_screens` | monitor-manager.py list/apply; descripciones persistentes | Escala, posición X/Y, giro, una aplicación por lote | Fixture de gestor con estado, lectura posterior y selector por descripción. Sin aplicar escala real. No incluye aún resolución/refresco, espejo, confirmación con reversión temporal. |
| Escritorios, `kcm_bwm_workspaces` | monitor-manager.py, asignaciones `workspaces` | Rangos por monitor sobre los workspaces comunes | Adaptador con validación de sintaxis y gestor existente. No emula org.kde.KWin.VirtualDesktopManager; no expone nombres, filas ni actividades KDE. El número de botones `bar.workspaces.shown` mantiene su autoridad actual. |
| Cursor, `kcm_bwm_cursor` | cursor-manager.py get/list/apply → cursor.lua, GTK, hyprctl | Tema instalado y tamaño común | Fixture comprueba aplicar tema+tamaño juntos, una llamada y relectura; sin mover el cursor real. El puente sigue exportando BWM → kcminputrc. |
| Atajos, `kcm_bwm_shortcuts` | keybinds-manager.py list/update → keybinds.json/generador | Editar combinaciones existentes de BWM, respetando filtro de skin | Fixture de gestor confirma delegación y lectura. Añadir/borrar/editar comandos no migrado a este KCM. No registra acciones en kglobalaccel ni inicia su servidor. |
| Apps, `kcm_bwm_apps` | default-apps.py list/set, XDG mimeapps.list y terminal BWM | Terminal, navegador, archivos, editor, monitor del sistema | Esquema usa candidatos del gestor; relectura obligatoria. Falta ensayo con aplicaciones reales. No se da TerminalService de Konsole por aplicado si se usa otra terminal. |
| Inicio, `kcm_bwm_startup` | autostart-manager.py → XDG autostart | Activar/desactivar entradas existentes | Fixture de gestor confirma guardar y releer. Añadir/borrar, scripts de sesión Plasma y unidades systemd no migrados a este KCM. |
| Energía/inactividad, `kcm_bwm_energy` | bwm-shared-settings.py → Config.idle → BwmIdle.qml/bwm-power | Tiempos de DPMS, bloqueo y suspensión compartidos | Almacén real aislado, reapertura, overlay protegido, tres identificadores de skin conservan valor. No se dispara bloqueo/suspensión/DPMS en pruebas. Sin perfiles AC/batería, tapa, carga ni equivalencia PowerDevil completa. |
| Luz nocturna R2 | nightlight.py; KCM BWM existente | Motor común; sin iniciar el de KWin | CTest R2 repetido; backend falso. Nativos kcm_nightlight/nighttime restringidos. |
| Fuentes, colores, iconos, estilo | kdeglobals/plasmarc, cascada KDE | Consumidores KDE/libplasma y sincronización BWM existentes | 12 pruebas de plasma-theme y 16 del puente; no nueva aceptación visual. Iconos de proceso persistente pueden requerir reinicio de mantenimiento, como el incidente resuelto. |

## Descubrimiento de complementos y demostración

`bwm-kcm-catalog` enumera metadatos sin cargar plugins por defecto. `--probe` acepta
explícitamente ejecutar las factories instaladas, instancia su KCModule cuando hay
`X-KDE-ConfigModule` y consulta `DecorationThemeProvider` cuando la metadata declara temas.
Se ha ejecutado y se conserva `BREEZE_R3_PLUGIN_DISCOVERY.json`:

- Breeze → `kcm_breezedecoration`, factory KCModule válida, cinco casillas descubiertas.
- Aurorae V2 → cinco variantes Sweet, con identificadores y módulo entregados por el provider.
- Aurorae QML → Plastik y su configurador nativo.

`test-decoration-option` descubre el configurador de **la biblioteca instalada**, localiza
`drawBackgroundGradient` en su propio formulario (ausente del catálogo fijo de BWM), guarda
false/true y reabre nuevas instancias. Para cada valor ejecuta el POC KDecoration ya existente,
que carga la misma biblioteca de decoración que usa BWM, y compara imágenes: **son distintas**.
El ensayo usa configuración temporal y QApplication offscreen; no crea servidor ni compositor.
Demuestra persistencia y consumo por el renderer del plugin; no certifica reconfiguración de
las ventanas abiertas, el transporte BWM de imágenes ni todas las opciones de terceros.
El catálogo de plasmoides/configuración por instancia se deja para R4.

## Contratos de servicios y R7

No se crea ningún proveedor D-Bus sustitutivo. KScreen necesita el backend/protocolo de salidas;
los escritorios, la API VirtualDesktopManager de KWin; el KCM de atajos, el registro de componentes
org.kde.kglobalaccel; PowerDevil, org.kde.Solid.PowerManagement/perfiles. Los módulos BWM usan
los controladores descritos en la tabla y no arrancan esos servicios.

R7 recibe contrato v1: duración en la clave KDE existente; solicitudes de efectos en
`kwinrc [Plugins] <id>Enabled`; parámetros en `[Effect-<id>]`, conservando desconocidas.
El catálogo de **capacidades** es distinto del de plugins instalados: `supported_effects=[]`
hasta implementar y verificar cada renderer. Un KCM futuro sólo ofrecerá capacidades reales,
con carga/guardar/defaults y lectura posterior. No se anuncia compatibilidad por instalar KWin.

## Pruebas ejecutadas

- **54 pruebas Python OK:** 10 de adaptadores R3, 16 del puente (incluye retry tras IPC fallido,
  kdedefaults, claves desconocidas, enlaces, no bucles y una recarga), 12 de temas, 9 de cambio
  de skin y 7 de sesión. Los cambios de skin en estos ensayos son fixtures, no transiciones reales.
- **3 ejecutables CTest OK:** luz nocturna R2, módulo nativo de gestores (guardar/reabrir,
  conflicto conserva cambios, descubrimiento y factories de las ocho páginas), opción de
  decoración instalada con comparación de render. Sin sockets de sesión.
- Build CMake correcto, instalación sólo en `/tmp/bwm-r3-prefix`, reemplazo atómico de los KCM.
  `systemsettings --list` real encuentra los nueve módulos de ese prefijo.
- KAuthorized probado en el anfitrión real: sin el perfil aparecen cursortheme,
  componentchooser y autostart; con el perfil desaparecen y permanecen los equivalentes BWM.
  En offscreen otros módulos KDE ya están ocultos por su plataforma declarada: no se atribuye
  esa ocultación al perfil. En Wayland debe comprobarse el resto de las restricciones.
- Sintaxis Python/bash y diff revisados. No se repite la matriz R1 ni se cambia de skin real.

## Pendiente para aceptar R3

1. Instalar los KCM en el prefijo real y abrirlos en el anfitrión de la sesión; todavía no se
   reemplaza Super+I. R2 no terminó la migración de todas las páginas/alias y sigue como gate.
2. Comprobar cambios reales de cada fila, reapertura y ciclo de skins con IPC; teclado/ratón,
   foco/colocación, encaje, pantalla y perfiles de energía son especialmente importantes.
3. Completar las equivalencias acotadas de la tabla si se exige toda la interfaz original:
   no son implementaciones completas de PowerDevil, KScreen, kglobalaccel ni Virtual Desktops.
   Páginas no adaptadas quedan restringidas en el lanzador experimental; no se habilitan para
   que sólo escriban archivos ignorados. El anfitrión antiguo queda fuera de esta migración.
4. Los botones de decoración cuyo dispatcher no existe y opciones propias adicionales de
   plugins necesitan revisión de capacidades/control individual. No se considera alcanzada
   la condición «ningún control activo ignorado» para todos los formularios de terceros.
5. Instalar y medir en sesión una decoración de terceros con una opción propia adicional,
   verificando su efecto después de cambiar de skin. La demostración de render actual usa
   Breeze instalado; el descubrimiento de Sweet está probado, su opción específica no.

## Uso y rollback

```bash
make -C src/bwm-systemsettings test
make -C src/bwm-systemsettings install
bash config/hypr/skins/plasma/scripts/settings-native.sh --list
bash config/hypr/skins/plasma/scripts/settings-native.sh kcm_bwm_windows
```

No hace falta reiniciar compositor ni plugins. La instalación real la debe ejecutar el usuario
porque el sandbox no permite escribir en su prefijo; tampoco permite validar sus sockets.
El informe no sustituye esa aceptación. No se ha ejecutado instalación real, commit ni push.

Rollback: dejar de usar `settings-native.sh`, conservar el lanzador anterior y retirar sólo los
KCM BWM del prefijo local con Preferencias cerrado. Revisar únicamente los hunks R3 del puente,
las páginas/adaptadores y el perfil; no hacer reset del resto del trabajo. Los archivos KDE del
usuario, sus metadatos de sistema y sus opciones de texto no se han usado como fixtures.

## Instalación confirmada por el usuario y comprobada (2026-11-12)

Tras ejecutar el usuario `make install`, se han encontrado los nueve KCM en el prefijo real
`~/.local/share/bwm/systemsettings`. Sus SHA-256 coinciden con la compilación local que acaba
de instalar. `settings-native.sh --list`, con systemsettings real y plataforma offscreen,
descubre los nueve; los siete módulos incompatibles enumerables en esta plataforma no aparecen.
Resultado estructurado: `BREEZE_R3_INSTALLATION.json`. Esto sustituye la instalación pendiente
del punto 1; la apertura gráfica, aplicación de controles y ciclo real de skins siguen pendientes.
No se ha reiniciado el compositor ni modificado ajustes para esta comprobación. El proceso
no conecta a D-Bus desde el sandbox; ese aviso no impide la enumeración offline.

Siguiente apertura, sin guardar cambios automáticamente:

```bash
bash ~/.config/hypr/skins/plasma/scripts/settings-native.sh kcm_bwm_windows
```

## Prueba de sesión confirmada por el usuario (2026-11-12)

El anfitrión se abrió pese al aviso del portal. El usuario confirma que Centered → Aplicar
centra una ventana nueva y que el valor sigue seleccionado al reabrir Preferencias.
Aceptación de **colocación centrada y persistencia** en la sesión real. No se amplía esta
confirmación a foco, encaje, pantallas, ciclo de skins ni al resto de controles R3.
