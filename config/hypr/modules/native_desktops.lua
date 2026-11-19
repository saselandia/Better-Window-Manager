-- Native Plasma desktop provider (src/bwm-plasma-desktops), common to every skin.
-- native-desktops.py startup loads the module once per session and enables it with hl.config.
-- A config reload resets plugin options to their default (false) and the provider would then
-- withdraw for the rest of the session. Keep it enabled here while the module is loaded and
-- the opt-in (~/.config/bwm/native-desktops.json, managed by native-desktops.py) still holds.
-- This never loads the module: without it, get_config returns nil and nothing is set.
local function opted_in()
    local base = os.getenv("XDG_CONFIG_HOME")
    if not base or base == "" then base = (os.getenv("HOME") or "") .. "/.config" end
    local file = io.open(base .. "/bwm/native-desktops.json", "r")
    if not file then return false end
    local text = file:read(4096) or ""
    file:close()
    return text:find('"version"%s*:%s*1') ~= nil and text:find('"enabled"%s*:%s*true') ~= nil
end

if hl.get_config and hl.get_config("plugin.bwm_plasma_desktops.enabled") ~= nil and opted_in() then
    hl.config({ plugin = { bwm_plasma_desktops = { enabled = true } } })
end
