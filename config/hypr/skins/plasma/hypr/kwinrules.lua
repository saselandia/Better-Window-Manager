-- BWM F10: the single F2 bridge compiles kwinrulesrc to native dynamic rules.
-- This module is loaded before bwm/user/hyprland.lua. Values are never evaluated as code.
local root = (os.getenv("XDG_STATE_HOME") or os.getenv("HOME") .. "/.local/state") .. "/bwm/plasma/"
local file = io.open(root .. "kwinrules.lua", "r")
if file then
    file:close()
    local enabled = dofile(root .. "kwinrules.lua")
    if enabled then
        -- Only windows mapped after loading Breeze get Apply/Remember initial values.
        -- Existing windows keep their geometry across skin changes and bridge restarts.
        hl.on("window.open", function(window)
            hl.dispatch(hl.dsp.window.tag({ tag = "+bwm-kwin-new", window = window }))
        end)
    end
end
