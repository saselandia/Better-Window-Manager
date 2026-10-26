-- -----------------------------------------------------
-- Entorno de las aplicaciones
-- -----------------------------------------------------

-- Apps Qt 6 (KeePassXC, diálogos de KDE...):
--  * con qt6ct instalado: la paleta del estilo BWM activo (~/.config/qt6ct/colors/bwm.conf, que
--    rellenan matugen / Breeze / la paleta Omarchy de Retro) y sus iconos (bwm_icons.py)
--  * sin qt6ct: siguen el modo oscuro/claro del sistema a través del portal, como GTK
local qt6ct = io.open("/usr/bin/qt6ct", "r")
if qt6ct then
    qt6ct:close()
    hl.env("QT_QPA_PLATFORMTHEME", "qt6ct")
else
    hl.env("QT_QPA_PLATFORMTHEME", "xdgdesktopportal")
end
