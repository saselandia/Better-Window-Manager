# R4: miniaturas experimentales y protección del compositor

Plasma 6.7.5 usa `PipeWireThumbnail.qml` → `ScreencastingRequest` → el protocolo KDE
`zkde_screencast_unstable_v1`. Instalar `org.kde.pipewire` sólo aporta el consumidor de vídeo;
no implementa ese protocolo en Hyprland ni relaciona los UUID de BWM con los de KWin.

El opt-in `--task-thumbnails` conserva el tooltip original de Plasma y adapta únicamente
su endpoint revisado hacia captura nativa por handle de ventana. No captura pantallas ni
guarda imágenes: usa `ext-foreign-toplevel-list`, mapping de Hyprland de 64 bits,
`ext-image-capture-source` y `ext-image-copy-capture`, con buffers memfd privados.

## Bloqueo por el incidente de captura anterior

[BREEZE_RECOVERY.md](BREEZE_RECOVERY.md) documenta un SIGSEGV en
`Screenshare::CScreenshareSession::init` de Hyprland 0.56.2. Tanto el protocolo antiguo como
el nuevo usan esa rutina. El código original desreferencia `monitor()` sin comprobarlo en
`init()` y en el callback de cambio de monitor. Cambiar de protocolo no elimina ese problema.

El parche [0.56.2-screenshare-monitor-guard.patch](../patches/hyprland/0.56.2-screenshare-monitor-guard.patch)
valida y conserva una referencia fuerte al monitor antes de acceder a él en ambos lugares.
Si falta, detiene la sesión de captura. No cambia estructuras ni la ABI de plugins. Incluye una
marca retenida en el ELF y un informe IPC de la guarda/PID real del compositor activo.

El auxiliar **rechaza activar capturas reales** hasta verificar las guardas del proceso que
sirve su socket Wayland. Obtiene PID/UID con `SO_PEERCRED`, exige UID propio y comprueba la
marca en `/proc/PID/exe` cuando es legible. Si no puede verificarla allí, consulta de nuevo
`hyprctl -j version` y exige `bwmScreenshareMonitorGuard: {"version": 1, "pid": PID}` con el
PID exacto del peer Wayland. La función que informa la versión está en la misma unidad de
compilación que las guardas de monitor; el compositor sólo añade ese valor y `getpid()` al
JSON, sin procesos auxiliares, E/S o esperas. El auxiliar limita la consulta a unos 2 segundos
y 64 KiB; rechaza errores, JSON/tipos inválidos, ausencia del campo y otras instancias.

No acepta archivos instalados, una marca de configuración o un flag de entorno como prueba.
`BWM_R4_TASK_RUNTIME`/`BWM_R4_GUARD_RUNTIME` permiten seleccionar el IPC de la sesión real desde
los almacenes XDG temporales del preview/diagnóstico; el PID sigue siendo obligatorio. No
cambia filecaps, ptrace ni permisos. El ejecutable separado de prueba autoriza sólo su fixture
sintético; la entrada normal del anfitrión no ofrece ese override.

Se han compilado los cuerpos originales y corregidos de ambas rutinas con un monitor/eventos
de prueba: los dos casos nulos originales terminan con SIGSEGV y los siete casos corregidos
pasan (monitor ausente, válido, referencia que desaparece y callback tras stop). Se compila también el cuerpo original/corregido de getVersion y se valida su JSON/PID real.
Se comprueba que el parche aplica a los dos archivos originales 0.56.2 y añade su cabecera
interna, sin cambiar el sistema. Esto no equivale
a compilar todo Hyprland ni demuestra que todos los posibles fallos de captura/GPU estén
resueltos. Las capturas de la barra diaria y del selector siguen contenidas.

## Probar primero sin tocar la sesión

```sh
ctest --test-dir /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host \
  -R '^native-task-thumbnail$' --output-on-failure
```

El fixture sólo usa un display privado y píxeles propios #3684c9. Comprueba captura, espera
sin daño en imagen estática, resize, ocultación, identidad reutilizada, cierre y retirada,
sin crear una superficie visible. Aquí ese ensayo está bloqueado por `wl_client_create:
Operation not permitted`; no se registra como aprobado. La compilación y las pruebas
locales de QML, identidad, formatos, límites y guardas sí se han ejecutado.

Actualización §240: el primer ensayo del usuario llegó al cliente pero terminó en SIGSEGV.
Se reprodujo sin Wayland al destruir un item asociado a ventana: la señal windowChanged de
la base llegaba tras liberar State. La corrección ya está compilada; las pruebas locales de
vida del item pasan normal/ASan. Repetir el mismo CTest antes de aplicar el parche del sistema.
La captura nativa corregida y sus hitos siguen pendientes; el bloqueo del compositor permanece.

Actualización §241: ensayo nativo aprobado por el usuario, CTest1/1 en4.30s; informe con
cliente0/fixture0, QtTest3/3 y los cinco checkpoints completados. Captura de píxeles, estático,
resize, destrucción/recreación activa, identidad/cierre/retirada y teardown comprobados en
su display privado. Supersede el fallo §240 para este ensayo normal. No repetirlo sin motivo;
no acredita native ASan ni miniatura física del escritorio. La siguiente etapa es la preparación
del compositor descrita abajo.

## Preparar Hyprland 0.56.2 en este Gentoo

Paquete instalado comprobado: `gui-wm/hyprland-0.56.2`, repositorio `hyproverlay`. Su ebuild
llama `cmake_src_prepare`/`default_src_prepare`, que aplica los parches de usuario de Portage.
La ruta de destino siguiente no existía al preparar estas instrucciones. Son comandos para
el usuario; no se han ejecutado con sudo desde el asistente:

```sh
sudo install -Dm644 \
  /mnt/HDD1TB/Projects/hyprland-de/patches/hyprland/0.56.2-screenshare-monitor-guard.patch \
  /etc/portage/patches/gui-wm/hyprland-0.56.2/9000-bwm-screenshare-monitor-guard.patch
sudo emerge --ask --oneshot --usepkg=n --getbinpkg=n =gui-wm/hyprland-0.56.2::hyproverlay
```

Se fuerza compilación desde fuente para que el parche local no quede fuera por reutilizar
un paquete binario. Comprobar que Portage aplica el parche y termina de compilar/instalar. Guardar el trabajo,
cerrar sesión y entrar normalmente para usar el nuevo ejecutable. `hyprctl reload` no cambia
el binario del compositor. No cargar/descargar plugins en caliente ni matar Hyprland para
adoptar la actualización. En §244 se comparó el parche instalado: contiene las guardas previas pero no el informe IPC.
Los comandos anteriores sustituyen ese parche por la ampliación revisada; después hace falta
una nueva compilación e inicio de sesión para incorporar el informe.

## Diagnosticar una guarda que bloquea

Actualización §244: el diagnóstico del usuario confirma `cannot-read-peer-executable`,
`Permission denied`, peer Hyprland PID5178/UID1000. El ejecutable instalado ya tiene las guardas
anteriores y cap_sys_nice=ep; la restricción de lectura impide esa forma de verificarlas.
La comprobación anterior no contemplaba esta configuración. La ampliación IPC descrita arriba
está compilada en el auxiliar y comprobada con rutinas originales, pero **todavía debe instalarse
el parche ampliado, recompilar Hyprland y entrar de nuevo**. No se ha compilado todo el compositor
desde el asistente ni se ha verificado su informe en la sesión real.

```sh
python3 /mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/check-thumbnail-compositor.py
```

El runner abre sólo la conexión Qt Wayland, con configuración/cache/D-Bus temporales; no
crea panel ni solicita imágenes. Informa si faltan credenciales, no se puede leer el peer,
la imagen es antigua/sin marca, o la guarda pasa. La comprobación no cambia capacidades,
permisos o el gate, y nunca acepta el archivo instalado como sustituto del proceso activo.
Si un auxiliar termina antes del ack, el wrapper ahora informa esa salida y no un ENOENT.

## Ensayo visual posterior

Actualización §247: usuario confirma «perfecto ya tiene miniaturas». Aceptación visual general
del tooltip corregido, sin inferir mediciones separadas de cada caso. No repetir ensayo
nativo ni diagnóstico de guarda; auxiliar queda abierto mientras continúa el trabajo.
Historial de los intentos anteriores abajo; no exige repetirlos. R4 sigue abierta por sus
otras capacidades y aceptación diaria.

Actualización §245: diagnóstico del usuario aprobado, clientExit0/verified=true por
compositor-ipc. PID496181 del informe version1 coincide con peer Wayland/UID1000. La lectura
de /proc sigue denegada y la comprobación IPC funciona. El parche instalado coincide con el
ampliado. No repetir compilación/reentrada ni CTest nativo: procede el preview siguiente.
Aún no se ha aceptado una miniatura física; este diagnóstico no solicita imágenes.

Actualización §242: usuario comunica finalización. Parche instalado idéntico y marca en
/usr/bin/Hyprland comprobados; proceso activo/reinicio no verificables desde este ejecutor.
El auxiliar comprueba el peer real antes de capturar. Tras §244, el siguiente paso es adoptar la ampliación IPC y pasar el diagnóstico anterior;
después procede el ensayo visual. No hay que repetir el CTest nativo ya aprobado.

Actualización §246: el primer hover real mostró un popup centrado/listado en tareas y vistas
duplicadas. El auxiliar no adaptaba el ToolTipDialog moderno (PopupPlasmaWindow creado desde
C++). Corregido por API pública, con capa overlay antes del rol Wayland y ancla visual vigente;
conserva el tooltip original y su interacción. La prueba desechable de tareas usa ahora una
sola instancia; --instances 2 permite comparar expresamente dos widgets. El auxiliar abierto
sigue usando el código anterior: cerrar sólo éste con Ctrl+C y repetir el comando siguiente.
Pruebas locales normal/ASan aprobadas; posición/rol y ausencia de tarea nueva aún deben
comprobarse en sesión. No hay nuevo parche de compositor ni inicio de sesión que repetir.

Después de pasar el fixture y entrar con el compositor protegido, cerrar el auxiliar anterior
con Ctrl+C y ejecutar:

```sh
python3 /mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/preview-isolated.py \
  --binary /mnt/HDD1TB/Projects/hyprland-de/build/bwm-plasma-host/bwm-plasma-host \
  --builtin org.kde.plasma.taskmanager --native-panel --layer-panel --instances 1 \
  --follow-skin --task-actions --all-desktops --session-appearance --task-thumbnails \
  --output "Micro-Star Int'l Co. Ltd. MAG 274Q X24 0x01010101"
```

La línea de protocolos conectados aún no prueba píxeles. Mantener el cursor sobre una tarea
no minimizada, comprobar la imagen y una actualización, salir del tooltip y conservar las
acciones que el usuario ya validó. Los límites son 8 sesiones, 64 MiB/buffer y 128 MiB totales,
32 bits por píxel de formatos habituales de 8/10 bits, hasta 8192 por dimensión, imágenes de
hasta 512 píxeles y solicitudes hasta 4 fps. No se certifica colorimetría HDR exacta.

Miniaturas del preview aceptadas en §247; R4 todavía no está cerrada. Omitir `--task-thumbnails` conserva la prueba
anterior ya aceptada. La barra diaria y las contenciones de recuperación siguen intactas.
