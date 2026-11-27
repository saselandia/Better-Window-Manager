# Breeze III — T6: paquetes, bandeja, emojis, zoom y portal KDE

Fecha: 2026-11-27. Plan: [BREEZE_PLAN_V3.md](BREEZE_PLAN_V3.md). Cambios de T6 implementados;
aceptación de teclado y de las bandejas ya configuradas separada de las pruebas aisladas.

## Requisitos y energía

`ksystemstats`, `kdeplasma-addons`, `plasma-emojier` y `portal-kde` están declarados en el
catálogo y recomendados por el manifiesto de Breeze. Tabla de requisitos regenerada.
El comprobador de addons busca su plugin Qt instalado, incluido cuando el QML está embebido.

El usuario instaló y se comprobaron `kde-plasma/ksystemstats-6.7.5` y
`kde-plasma/kdeplasma-addons-6.7.5-r1`. Emoji Selector pertenece aquí a
`kde-plasma/plasma-desktop-6.7.5`; el portal KDE 6.7.5 ya estaba instalado. Los cuatro
requisitos nuevos aparecen **ok** en `bwm-requirements.py check --skin plasma --json`.

**PowerDevil se incorpora al catálogo, pero no se recomienda ni se arranca automáticamente.**
Se revisó el código original 6.7.5: `Core::loadProfile`, `SuspendSession::loadAction`,
`DPMSControl`, `DimDisplay` y `LidController` gestionan perfiles, tiempos de inactividad,
pantallas y tapa. `BwmIdle` y `bwm-power` ya son su autoridad común en BWM; ejecutar ambos
añadiría otro gestor de esas mismas acciones. No hay un modo general «sólo batería y brillo»
que permita recomendar el demonio sin coordinar esa autoridad. No se cambia su configuración
ni se oculta el conflicto con inhibidores permanentes. Su integración completa queda pendiente;
no se certifican los controles nativos que necesiten ese servicio. No se instaló ni probó energía.

Fuentes originales de [PowerDevil 6.7.5](https://invent.kde.org/plasma/powerdevil/-/tree/v6.7.5)
y plasma-workspace 6.7.5 descargadas de KDE y verificadas por SHA512 contra los Manifest de
Portage. Las fuentes se usan para revisión; no se incorporan al repo ni se modifican.

## Una bandeja predeterminada sin dos historiales

El historial común sigue siendo **cliphist**, con `Super+V` y las interfaces BWM existentes.
No se cambian sus datos, contenido del portapapeles ni procesos de captura al cambiar de skin.
La distribución del teclado sigue siendo la de Hyprland y su gestor común.

`BwmTrayDefaults` utiliza `General/knownItems`, clave original de Plasma. En una bandeja
**nueva**, marca conocidos `org.kde.plasma.clipboard` y `org.kde.plasma.keyboardlayout` sin
añadirlos a `extraItems`. El registro original no los autoactiva; los demás widgets conservan
su descubrimiento original. Esos dos applets siguen disponibles para quien los active.
No se parchea el QML de Plasma ni se inventa un formato de preferencias.

`ViewCorona` aplica esta política en `appletCreated`, señal original que sólo se emite para
instancias nuevas, y actualiza el KConfigLoader con su contrato save/read. El registro nativo
ya ha creado sus valores automáticos en ese punto; éstos se ajustan antes de la elección del
usuario. Al restaurar una bandeja o si sus claves son inmutables **no se reescribe su configuración**. Por ello una bandeja existente que tenga Klipper/teclado activados conserva
esa elección y puede seguir mostrando ambos historiales; para retirarlos se usa su configuración
original. No se anuncia una migración automática ni se han borrado applets del perfil diario.

## Atajos y zoom

La API/CLI de `keybinds-manager.py add|update` admite `--skins` y `--skins-except`, filtros
que el generador Lua ya entendía. Las entradas se registraron mediante ese gestor y el Lua
se regeneró con él. Las acciones y sus alternativas figuran también en los valores de fábrica:

| Atajo, sólo Breeze | Acción |
| :--- | :--- |
| Super+. | `plasma-emojier` original, como hijo de Hyprland |
| Meta con + o = | Aumentar `cursor:zoom_factor` por 1,2, hasta 8; incluye Mayús+0 para = en español |
| Meta+- | Reducir por 1,2, con mínimo 1 |
| Meta con + / − del teclado numérico | Ampliar / reducir con KP_Add y KP_Subtract |
| Meta+0 | Volver a 1 |

El atajo existente de emojis de Omarchy excluye Breeze. Retro y default conservan su acción.
`skins/plasma/scripts/desktop-actions.py` valida la skin y serializa los cambios de zoom con
flock, leyendo el factor real antes de cada pulsación. Al salir de Breeze devuelve el valor
anterior al primer cambio si el valor actual sigue siendo el último aplicado por el helper;
una modificación posterior ajena se conserva. No hay un demonio de zoom ni captura del escritorio.
Es zoom de Hyprland, sin prometer todas las opciones o animaciones del efecto KWin.

El backend T5 ha seguido activo durante las recargas: los binds de BWM permanecen registrados
como suyos. Verificada la presencia de una sola entrada activa para cada tecla nueva. No se ha
inyectado entrada en la sesión diaria. El usuario confirma Emoji Selector y detectó un fallo
al ampliar con `+`/`=`. Se corrigieron las combinaciones: Hyprland compara el símbolo sin
modificadores y la máscara por separado (en español `=` es Mayús+0; en US `+` es Mayús+=).
Se conservan `Super+=` sin Mayús, `Super++`, `Super+Mayús+=` y `Super+Mayús+0` como entradas
por skin del gestor. Ninguna cambia los atajos de las demás skins. El aplicador de zoom no
necesitó cambios. El usuario confirma que el zoom ya funciona tras la corrección y pide
también +/− del teclado numérico: añadidos KP_Add/KP_Subtract como alternativas de los mismos
controles, con el gestor y sus valores de fábrica.

## Portal de archivos

El manifiesto declara `portals.FileChooser = ["kde", "gtk"]`. El gestor común
`scripts/bwm_portals.py` prepara una copia efímera de la configuración seleccionada por
XDG en `$XDG_RUNTIME_DIR/bwm-portals/xdg-desktop-portal/portals.conf`, conserva las otras
interfaces y cambia sólo FileChooser. Un drop-in runtime de `xdg-desktop-portal.service`
limita **a ese servicio** el XDG_CONFIG_HOME de la copia. Las preferencias del usuario no
se sobrescriben, ni cambia XDG_CURRENT_DESKTOP de aplicaciones. Un FileChooser personalizado
distinto del GTK de base tiene prioridad y desactiva la sustitución de BWM.

Al iniciar/cambiar de skin se aplica el perfil; fuera de Breeze se retira el drop-in. Sólo si
cambia el perfil se recarga systemd y se reinicia el portal principal si estaba activo.
ScreenCast/Screenshot y el resto de preferencias conservan sus proveedores. No se cambia la
configuración global para forzar KDE en las demás skins. La selección sigue el
[contrato de portals.conf](https://flatpak.github.io/xdg-desktop-portal/docs/portals.conf.html).

`environment.lua` activa `GTK_USE_PORTAL=1` en Breeze para las apps GTK que usan el selector
nativo; conserva el valor del login fuera de Breeze y el Lua final del usuario puede
sobrescribirlo. Autostart y `bwm_session` lo propagan a la activación de nuevas apps. Un
diálogo implementado directamente por una aplicación no se convierte en portal por esta opción.

## Comprobaciones

| Prueba | Resultado |
| :--- | :--- |
| `tests/test_breeze_t6.py` | **10/10 PASS** con dobles de órdenes: incrementos de zoom, límites/restauración/cambio ajeno, Emoji Selector y skin, configuración del portal y preferencias ajenas, salida a las otras skins, idempotencia, persistencia de filtros de atajos y requisitos |
| CTest después de instalar los paquetes | **16/16 PASS**, 95,25 s; incluye los valores nativos de bandeja, conservación byte a byte de elecciones restauradas e inmutabilidad |
| Bandeja nativa nueva | Caso `nativeNewTrayUsesSharedClipboardDefaults`: su KConfigLoader contiene los dos plugins conocidos y ninguno activado. Se comprueba antes de crear representaciones visuales; las superficies se ensayan en Wayland anidado |
| Pulsaciones reales del atajo en Hyprland aislado | **6/6 recorridos PASS** (US =/+/numérico, español =/+/numérico): teclas y modificadores virtuales, binds del JSON y aplicador real; cada uno amplía una vez, reduce y restablece. Las pruebas anteriores del helper por sí solas no comprobaban este recorrido |
| Regresiones Python | T4 **9/9**, skins **7/7**, T5 **7/7**, arranque **4/4**, procesos de sesión **7/7**, atajos Retro **4/4** |
| Hyprland aislado + bus privado | Zoom in/out/reset y retirada; Emoji Selector original abre/cierra; OpenFile y GtkFileChooserNative de GTK 3 muestran la ventana del backend KDE y permiten cancelar |
| Sensores instalados | `org.kde.ksysguard.sensors/Sensor` recibe varias actualizaciones reales de CPU y memoria desde ksystemstats original, en bus privado |
| Widgets originales | CPU, memoria y calculadora cargan y se muestran sin módulos QML ausentes en el envoltorio de previsualización. Captura aislada de CPU revisada: porcentaje visible; captura borrada. No se certifica aún todo el catálogo de addons |
| Estado diario | Host nuevo ready, dos escritorios y dos paneles, avisos válidos; fondos originales conservados, Quickshell único, sin configerrors. Portal principal activo con drop-in runtime y backend FileChooser KDE introspectado. `GTK_USE_PORTAL=1` exportado a la activación |

Runner gráfico: `check-focus-safety.py --binary src/bwm-plasma-host/check-t6-session.py`, con
informe en `build/bwm-plasma-host-tests/t6-session-results.json`. El cliente valida PID y firma
del compositor desechable, usa D-Bus/XDG privados y retira sus procesos. La captura de CPU
se guarda dentro de su raíz temporal y se elimina con ella. No lee historiales de
portapapeles, selecciona archivos, toca dispositivos de entrada físicos ni aplica energía.
Gio (PyGObject), qml de Qt y grim se usan sólo en este arnés de prueba.

Para desactivar el perfil de portal de BWM sin cambiar de skin:
`python3 ~/.config/hypr/scripts/bwm_portals.py default`. Se retira sólo su drop-in y vuelve la
configuración normal del servicio. El zoom se puede restablecer con Meta+0; los widgets
excluidos por defecto se pueden habilitar en la configuración original de la bandeja.

## Despliegue y límites

Host instalado atómicamente SHA256
`8ab4c18d1da79fa0e6cca21393ae41436bab9cac09f7a3cb3c4be8c36e4a0515`, PID comprobado 121531.
No se recompiló/cargó un plugin dentro del compositor. T5 permanece como trabajo previo
sin commit en el checkout; no se ha descartado ni incluido en un commit de T6.

La nueva bienvenida de T4 ha sido confirmada por el usuario en este login: apareció y se
cerró correctamente. Sigue pendiente aplicar una disposición escogida por él. En T5 se
comprueba el nuevo arranque sin modo seguro; las pruebas de teclado siguen pendientes.

Pendientes de aceptación: ampliación al teclado numérico, elección de los applets en bandejas
existentes y cambio de skin diario con el portal. PowerDevil requiere una integración futura
con el gestor común antes de recomendarlo. No se ha iniciado T7 ni hecho commit/push en esta fase.

Regresión del atajo corregido (sólo en el compositor desechable):

```bash
cmake --build build/bwm-plasma-host-tests --target test-zoom-shortcuts -j6
python3 src/bwm-plasma-host/check-focus-safety.py \
  --binary build/bwm-plasma-host-tests/test-zoom-shortcuts \
  --report build/bwm-plasma-host-tests/zoom-shortcuts-results.json
```

`NestedInput` conserva la validación de UID/PID, socket Wayland y configuración del arnés.
libxkbcommon genera los mapas US/es instalados; sólo se añaden dispositivos al hijo verificado.
El estado del aplicador se desvía a la raíz temporal y su IPC sigue apuntando a ese compositor.
Fuente del comportamiento contrastado: [KeybindManager de Hyprland 0.56.2](https://github.com/hyprwm/Hyprland/blob/v0.56.2/src/managers/KeybindManager.cpp).
