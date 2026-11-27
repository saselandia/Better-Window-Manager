-- Atajos globales de KDE en Breeze (Breeze III, T5). bwm-kglobalaccel escribe en
-- ~/.local/state/bwm/kde-shortcuts.lua los binds de los atajos de KDE que BWM no usa y los
-- aplica en caliente; este módulo los vuelve a crear tras cada recarga de Hyprland.
-- Se carga después de los atajos de BWM y antes del Lua del usuario. Fuera de Breeze no hay
-- binds de KDE: el demonio no corre y este archivo no carga nada.
local ok_theme, theme = pcall(require, "modules.theme")
if not ok_theme or theme.name ~= "plasma" then
    return
end
local base = os.getenv("XDG_STATE_HOME")
if not base or base == "" then base = (os.getenv("HOME") or "") .. "/.local/state" end
local state = base .. "/bwm/kde-shortcuts.lua"
local file = io.open(state, "r")
if not file then return end
file:close()
_G.bwm_kde_binds = {}
local ok, err = pcall(dofile, state)
if not ok then
    local msg = tostring(err):gsub("['\"`$\\]", "")
    os.execute("notify-send -a BWM 'Atajos de KDE sin cargar' '" .. msg .. "' &")
end
