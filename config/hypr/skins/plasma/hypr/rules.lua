-- BWM F10 / R6: traditional defaults and decoration states belong only to Breeze.
-- The validated R6 breezebars plugin (blur_on_request) renders KDE decoration shadows and sets
-- no_blur at the lowest priority on windows that do not ask for blur; an older loaded plugin
-- keeps both vetoes until the next session.
local float_all = { name = "breeze-float-all", match = { class = ".*" },
    float = true, border_size = 0 }
if not (hl.plugin and hl.plugin.breezebars and hl.plugin.breezebars.blur_on_request) then
    float_all.no_shadow = true
    float_all.no_blur = true
end
hl.window_rule(float_all)
for _, state in ipairs({ { "fullscreen", { fullscreen = true } },
                         { "maximized", { tag = "bwm-maximized" } },
                         { "snapped", { tag = "snapped" } } }) do
    hl.window_rule({ name = "breeze-" .. state[1] .. "-square", match = state[2], rounding = 0 })
end
-- KWin blurs the shape of each Plasma frame (the KSvg mask). The shell asks for the frame minus
-- its shadow (BackgroundEffect); ignore_alpha drops the blur where the frame is transparent, so
-- the rounded corners keep their shape. Popups of the panel (tray, tooltips) are dialogs too.
hl.layer_rule({ name = "breeze-blur-frames",
    match = { namespace = "^(quickshell:(plasmaPanel|plasmaKickoff|plasmaNotifications|altTab|plasmaMenu)|bwm-plasma-osd|krunner)$" },
    ignore_alpha = 0.01, blur_popups = true })
hl.window_rule({ name = "breeze-no-capture", match = { tag = "bwm-no-capture" }, no_screen_share = true })
-- Native no-border also removes compositor borders/shadows; CSD negotiation stays automatic.
hl.window_rule({ name = "breeze-no-border", match = { tag = "bwm-no-border" },
    decorate = false, border_size = 0, no_shadow = true })

-- Sin barra de título; el campo sólo existe con el plugin breezebars cargado (Breeze)
if hl.plugin and hl.plugin.breezebars then
    hl.window_rule({
        name  = "bwm-screensaver-nobar",
        match = { class = "^org\\.bwm\\.screensaver$" },
        ["breezebars:no_bar"] = true,
    })
end
