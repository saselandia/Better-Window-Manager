-- BWM F10: traditional defaults and decoration states belong only to Breeze.
hl.window_rule({ name = "breeze-float-all", match = { class = ".*" },
    float = true, no_shadow = true, no_blur = true, border_size = 0 })
for _, state in ipairs({ { "fullscreen", { fullscreen = true } },
                         { "maximized", { tag = "bwm-maximized" } },
                         { "snapped", { tag = "snapped" } } }) do
    hl.window_rule({ name = "breeze-" .. state[1] .. "-square", match = state[2], rounding = 0 })
end
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
