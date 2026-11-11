# Tema de las interfaces Plasma (F12)

InterfaceTheme ejecuta el lector read-only skins/plasma/scripts/interface-theme.py al cargar y
cuando cambian kdeglobals/kwinrc o sus valores kdedefaults. Respeta XDG_CONFIG/DATA/CACHE y
prioridad de las claves explícitas. La configuración usa exclusivamente nombres y rutas de KDE:
LookAndFeelPackage, TabBox/LayoutName, plasma/look-and-feel y kwin/tabbox.

El adaptador copia paquetes a una caché versionada por contenido/fechas y publica la carpeta
atómicamente; nunca reescribe el tema instalado. Se preservan recursos y rutas relativas.
No carga plugins C++ de KWin. Los temas QML se alojan con ThemeHost (org.bwm.kcm, API 2), en
motores separados que no propagan Qt.quit() a Quickshell. Un fallo de carga deja la vista Breeze
portada. Las APIs privadas no implementadas se documentan en los README de cada interfaz.
