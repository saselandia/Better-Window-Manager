-------------------------------------
---- REGLAS DE VENTANA POR APP ------
-------------------------------------

-- Las de Omarchy (basecamp/omarchy quattro c18b00c5, default/hypr/apps/*.lua, MIT), sin cambios, en
-- quickshell/ii/Commons/omarchy/default/hypr/apps/ (README allí). Valen en todas las skins: imagen en
-- imagen, gestores de contraseñas fuera de las capturas de pantalla, Steam, Telegram, RetroArch,
-- Moonlight, la superposición de webcam de las grabaciones, diálogos del portal… Se cargan después de
-- rules.lua y antes de los modos de workspace de Retro (appearance.lua), en el mismo orden que Omarchy.
--
-- Cada archivo usa el `o.window(match, reglas)` de Omarchy (default/hypr/helpers.lua); aquí lo da este
-- adaptador, con su propio entorno para no tocar el `o` global de skins/retro/hypr/workspace-modes.lua.
-- Adaptaciones BWM:
--   * En una skin de WM tradicional (Breeze) todo flota: la regla `tile` de los navegadores Chromium se
--     ignora allí.
--   * `o.transparent_window` no hace nada: la transparencia de Omarchy en BWM es sólo de Retro y la
--     lleva modules/omarchy_windows.lua.
--   * Fuera: terminals.lua (lo hace omarchy_windows.lua), omarchy-shell.lua y screenshot-selection.lua
--     (capas de Omarchy: skins/retro/hypr/animations.lua), battlenet.lua (necesita el lanzador de Omarchy).

local ok_theme, active_theme = pcall(require, "modules.theme")
local is_traditional = ok_theme and (active_theme.windows == "traditional" or active_theme.name == "plasma")

local o = {}

function o.window(match, rules)
    rules.match = rules.match or {}
    if type(match) == "string" then
        rules.match.class = match
    else
        for key, value in pairs(match) do
            rules.match[key] = value
        end
    end
    if is_traditional and rules.tile ~= nil then
        rules.tile = nil
        if next(rules, nil) == "match" and next(rules, "match") == nil then return end
    end
    hl.window_rule(rules)
end

function o.transparent_window() end

local dir = (os.getenv("HOME") or "") .. "/.config/quickshell/ii/Commons/omarchy/default/hypr/apps/"
local env = setmetatable({ o = o }, { __index = _G })
for _, name in ipairs({ "system", "1password", "bitwarden", "browser", "captive-portal", "davinci-resolve",
                        "geforce", "hermes", "inkscape", "jetbrains", "localsend", "moonlight", "pip",
                        "retroarch", "steam", "telegram", "webcam-overlay" }) do
    local chunk, err = loadfile(dir .. name .. ".lua", "t", env)
    local ok = chunk ~= nil
    if ok then ok, err = pcall(chunk) end
    if not ok then
        print("BWM: reglas de " .. name .. ": " .. tostring(err))
    end
end
