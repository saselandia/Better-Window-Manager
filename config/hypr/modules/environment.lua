-- -----------------------------------------------------
-- Entorno de las aplicaciones
-- -----------------------------------------------------

local function exists(path)
    local f = io.open(path, "r")
    if f then f:close() end
    return f ~= nil
end

-- Apps Qt 6 (KeePassXC, diálogos de KDE...):
--  * default (end-4) con «Apps Qt» y el plugin de KDE (kde-plasma/plasma-integration): como end-4,
--    QT_QPA_PLATFORMTHEME=kde lee ~/.config/kdeglobals, con los colores de kde-material-you-colors
--    y el estilo Darkly si está (skins/default/scripts/kde-material-you-colors-wrapper.sh)
--  * con qt6ct instalado: la paleta del estilo BWM activo (~/.config/qt6ct/colors/bwm.conf, que
--    rellenan matugen / Breeze / la paleta Omarchy de Retro) y sus iconos (bwm_icons.py)
--  * sin qt6ct: siguen el modo oscuro/claro del sistema a través del portal, como GTK
local function end4_qt()
    local ok, theme = pcall(require, "modules.theme")
    if not ok or theme.name ~= "default" then return false end
    local f = io.open(os.getenv("HOME") .. "/.config/illogical-impulse/config.json", "r")
    if f then
        local text = f:read("a")
        f:close()
        if text:find('"enableQtApps"%s*:%s*false') then return false end
    end
    return exists("/usr/lib64/qt6/plugins/platformthemes/KDEPlasmaPlatformTheme6.so")
        or exists("/usr/lib/qt6/plugins/platformthemes/KDEPlasmaPlatformTheme6.so")
end

if end4_qt() then
    hl.env("QT_QPA_PLATFORMTHEME", "kde")
elseif exists("/usr/bin/qt6ct") then
    hl.env("QT_QPA_PLATFORMTHEME", "qt6ct")
else
    hl.env("QT_QPA_PLATFORMTHEME", "xdgdesktopportal")
end
