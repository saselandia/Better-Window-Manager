




agregar el las kde plasma settings y hacer que coincidan con las settings que tenemos y las respeten, para la skin breeze










4. Otras novedades sin portar:

animaciones de introducción al cambiar de fondo;
el panel de pantallas con mapa de distribución y opción de Extender o Duplicar;
las reglas de movimiento aplicadas a las animaciones de Hyprland;
cambios en el menú: Apariencia como menú principal, la transparencia de apps opcional y una sección de Teclado;
botones Abrir/Cortar en los avisos de descargas y grabaciones.

Los instaladores de apps (Notion, Slack, dictado…) dependen de Arch y no sirven tal cual en Gentoo.

Te propongo empezar por el punto 1: portar el modo por workspace a Retro sin cargar un segundo plugin, ampliando nuestro hyprbars-plasma con las dos cosas que le faltan. Como no quieres atajos nuevos, el cambio de modo iría en el menú de Retro en vez de en Super+L.




MEJORAR ALT TAB EN TODOS



cambiar de nautilus a dolphin, dejar nautilus en omarchy y añadirle los plugins que ellos le añaden, hacer que funcione uno en cada skin y que compartan bookmarks y demas, que alt + e abra el que sea de cada skin, añadir la opcion de solo usar uno de los dos o usar los dos para depende de cada skin. Lo integraría como una pieza común a todas las skins, con este comportamiento:
- Al iniciar sesión, reúne los favoritos existentes de ambos gestores sin borrar ninguno.
- Después, sincroniza altas, cambios de nombre y eliminaciones en ambos sentidos.
- Guarda un pequeño estado anterior para distinguir una eliminación de un marcador nuevo y evitar que reaparezcan los borrados.
- Vigila las carpetas que contienen los archivos, porque las aplicaciones pueden sustituirlos al guardar; agrupa los avisos próximos para no trabajar varias veces por una sola edición.
- Conserva las entradas especiales de KDE y los datos que no tengan equivalente en GTK. Si detecta cambios simultáneos que no pueda conciliar con seguridad, conserva la información y vuelve a intentar la sincronización.


hacer que bwmenu salga como app para buscarla en el lanzador
