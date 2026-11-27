-- -----------------------------------------------------
-- Entorno de las aplicaciones
-- -----------------------------------------------------

local function exists(path)
    local f = io.open(path, "r")
    if f then f:close() end
    return f ~= nil
end

-- Como Omarchy (default/uwsm/env): la raíz de Omarchy, donde sus piezas buscan bin/, default/i18n,
-- themes/ y shell/plugins/. En BWM es config/hypr/omarchy, con enlaces a los shims y a los
-- plugins vendidos (panel de agentes, recordatorios, Elsewhen, idioma del menú).
hl.env("OMARCHY_PATH", os.getenv("HOME") .. "/.config/hypr/omarchy")

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

-- GTK native file choosers use the selected portal in Breeze. Preserve the
-- login environment outside Breeze; the user's final Lua still has precedence.
local gtk_portal = os.getenv("BWM_ORIGINAL_GTK_USE_PORTAL")
if gtk_portal == nil then
    gtk_portal = os.getenv("GTK_USE_PORTAL") or ""
    hl.env("BWM_ORIGINAL_GTK_USE_PORTAL", gtk_portal)
end
hl.env("GTK_USE_PORTAL", skin == "plasma" and "1" or gtk_portal)

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

-- Breeze (Kde plasma): como en Plasma, el plugin de KDE lee el esquema de color, los iconos y el
-- estilo de kdeglobals (skins/plasma/scripts/plasma-theme.py) y repinta las apps en vivo
local breeze_qt = skin == "plasma" and qt_plugin("platformthemes/KDEPlasmaPlatformTheme6.so")

if end4_qt() or breeze_qt then
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

-- Breeze: como startplasma, ~/.config/kdedefaults va delante en XDG_CONFIG_DIRS para que los
-- valores por defecto de un tema global (lookandfeeltool, plasma-theme.py) se apliquen. En las
-- demás skins se quita.
do
    local kdedefaults = os.getenv("HOME") .. "/.config/kdedefaults"
    local dirs = {}
    for dir in (os.getenv("XDG_CONFIG_DIRS") or "/etc/xdg"):gmatch("[^:]+") do
        if dir ~= kdedefaults then table.insert(dirs, dir) end
    end
    if skin == "plasma" then table.insert(dirs, 1, kdedefaults) end
    hl.env("XDG_CONFIG_DIRS", table.concat(dirs, ":"))
end

-- Como startplasma: el menú de aplicaciones de Plasma (plasma-applications.menu, de plasma-workspace).
-- Sin él, Kickoff (modelos de Kicker) no tiene categorías. Va en todas las skins si existe: KService
-- guarda la caché (ksycoca) en el mismo archivo sea cual sea el prefijo, así que un proceso de otra
-- skin sin él la reconstruiría sin categorías. Las otras skins no usan menús XDG.
if exists("/etc/xdg/menus/plasma-applications.menu") then
    hl.env("XDG_MENU_PREFIX", "plasma-")
end

-- Formatos regionales de Plasma (kcm_regionandlang → ~/.config/plasma-localerc [Formats]):
-- se aplican en todas las skins al entrar, sin pisar el locale del sistema ni el LANG elegido
-- por el usuario. Sólo se exportan las categorías LC_* escritas explícitamente en [Formats].
do
    local cfg_home = os.getenv("XDG_CONFIG_HOME") or (os.getenv("HOME") .. "/.config")
    local f = io.open(cfg_home .. "/plasma-localerc", "r")
    if f then
        local allowed = {
            LC_NUMERIC = true, LC_TIME = true, LC_MONETARY = true,
            LC_MEASUREMENT = true, LC_COLLATE = true, LC_ADDRESS = true,
            LC_NAME = true, LC_PAPER = true, LC_TELEPHONE = true,
        }
        local in_formats = false
        local use_detailed = true
        local pending = {}
        local fmt_lang = nil
        for line in f:lines() do
            local trimmed = line:match("^%s*(.-)%s*$")
            if trimmed:match("^%[.+%]$") then
                in_formats = (trimmed == "[Formats]")
            elseif in_formats and trimmed ~= "" and not trimmed:match("^#") then
                local k, v = trimmed:match("^([%w_]+)%s*=%s*(.-)%s*$")
                if k == "useDetailed" then
                    use_detailed = (v:lower() ~= "false")
                elseif k == "LANG" and v ~= "" and v:match("^[%w_.@%-]+$") then
                    fmt_lang = v
                elseif k and allowed[k] and v ~= "" and v:match("^[%w_.@%-]+$") then
                    pending[k] = v
                end
            end
        end
        f:close()
        local cur_lang = os.getenv("LANG") or ""
        if fmt_lang and (cur_lang == "" or cur_lang == "C" or cur_lang == "POSIX") then
            hl.env("LANG", fmt_lang)
        end
        if use_detailed then
            for k, v in pairs(pending) do
                hl.env(k, v)
            end
        end
    end
end
