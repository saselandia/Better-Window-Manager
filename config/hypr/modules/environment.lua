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
--  * Retro con el plugin GTK de Qt (dev-qt/qtbase[gtk]): como Omarchy, QT_QPA_PLATFORMTHEME=gtk3
--  * con qt6ct instalado: la paleta del estilo BWM activo (~/.config/qt6ct/colors/bwm.conf, que
--    rellenan matugen / Breeze / la paleta Omarchy de Retro) y sus iconos (bwm_icons.py)
--  * sin qt6ct: siguen el modo oscuro/claro del sistema a través del portal, como GTK
local ok_theme, active_theme = pcall(require, "modules.theme")
local skin = ok_theme and active_theme.name or "default"

local function qt_plugin(path)
    return exists("/usr/lib64/qt6/plugins/" .. path) or exists("/usr/lib/qt6/plugins/" .. path)
end

local function end4_qt()
    if skin ~= "default" then return false end
    local f = io.open(os.getenv("HOME") .. "/.config/illogical-impulse/config.json", "r")
    if f then
        local text = f:read("a")
        f:close()
        if text:find('"enableQtApps"%s*:%s*false') then return false end
    end
    return qt_plugin("platformthemes/KDEPlasmaPlatformTheme6.so")
end

if end4_qt() then
    hl.env("QT_QPA_PLATFORMTHEME", "kde")
elseif skin == "retro" and qt_plugin("platformthemes/libqgtk3.so") then
    -- Como Omarchy (default/hypr/envs.lua): Fusion con la paleta del tema GTK, que BWM pinta con
    -- el tema de Omarchy y alterna en vivo (BWM-1/BWM-2)
    hl.env("QT_QPA_PLATFORMTHEME", "gtk3")
elseif exists("/usr/bin/qt6ct") then
    hl.env("QT_QPA_PLATFORMTHEME", "qt6ct")
else
    hl.env("QT_QPA_PLATFORMTHEME", "xdgdesktopportal")
end
