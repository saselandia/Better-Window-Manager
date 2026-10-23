-- -----------------------------------------------------
-- Entorno de las aplicaciones
-- -----------------------------------------------------

-- Qt 6 sigue la preferencia oscura/clara del sistema (org.gnome.desktop.interface
-- color-scheme) a través del portal, como GTK. Sin esto las apps Qt (KeePassXC,
-- diálogos de KDE...) salían siempre claras, sin importar el tema de BWM.
hl.env("QT_QPA_PLATFORMTHEME", "xdgdesktopportal")
