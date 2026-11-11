-- Puente F2: opciones de kwinrc, convertidas por kde-config-bridge.py.
-- Se carga después de la configuración común y antes de ~/.config/bwm/user/hyprland.lua.
local state = (os.getenv("XDG_STATE_HOME") or (os.getenv("HOME") .. "/.local/state")) .. "/bwm/plasma/kwin.lua"
local ok, settings = pcall(dofile, state)
local k = ok and type(settings) == "table" and settings or {}
local follows = k.focus ~= nil and k.focus ~= "ClickToFocus"
local native_snap = not (hl.plugin and hl.plugin.breezebars and hl.plugin.breezebars.snap_config)
hl.config({
    input = { follow_mouse = follows and 1 or 0 },
    general = { snap = {
        enabled = native_snap and ((k.borderSnap or 10) > 0 or (k.windowSnap or 10) > 0),
        monitor_gap = k.borderSnap or 10,
        window_gap = k.windowSnap or 10,
    } },
    animations = { enabled = (k.animationFactor or 1) > 0 },
})
-- F10: KWin magnets use the complete KDE frame. Disable the competing native magnet above.
if not native_snap then
    hl.plugin.breezebars.snap_config({ border = k.borderSnap or 10, window = k.windowSnap or 10,
        center = k.centerSnap or 0, overlapOnly = k.snapOnlyOverlapping or false,
        quickTile = k.quickTile ~= false, maximize = k.edgeMaximize ~= false, cornerRatio = k.cornerRatio or 0.25 })
    local tiles = io.open((os.getenv("XDG_STATE_HOME") or os.getenv("HOME") .. "/.local/state") .. "/bwm/plasma/kwintiles.lua", "r")
    if tiles then
        tiles:close()
        dofile((os.getenv("XDG_STATE_HOME") or os.getenv("HOME") .. "/.local/state") .. "/bwm/plasma/kwintiles.lua")
    end
end

-- Hyprland expresa speed como inverso de duración. Conservamos las curvas de Breeze.
local factor = k.animationFactor or 1
if factor > 0 and factor ~= 1 then
    for _, a in ipairs({
        { "windows", 3, "md3_decel", "popin 60%" }, { "windowsIn", 3, "md3_decel", "popin 60%" },
        { "windowsOut", 3, "md3_accel", "popin 60%" }, { "border", 10, "default" },
        { "fade", 3, "md3_decel" }, { "fadeIn", 3, "md3_decel" }, { "fadeOut", 3, "md3_accel" },
        { "workspaces", 4, "menu_decel", "slide" }, { "workspacesIn", 4, "menu_decel", "slide" },
        { "workspacesOut", 4, "menu_decel", "slide" }, { "specialWorkspace", 3, "md3_decel", "slidevert" },
    }) do
        hl.animation({ leaf = a[1], enabled = true, speed = math.max(0.1, a[2] / factor), bezier = a[3], style = a[4] })
    end
end

-- El plugin actual sólo admite un banco de botones y los glifos I/A/X. El estado conserva ambos
-- bancos completos para F6a/F6b; no se finge que menú, ayuda o enrollar ya están portados.
if hl.plugin and hl.plugin.breezebars then
    -- Minimizar y maximizar: kwin-window.py (F8), con la semántica de KWin; el plugin añade la dirección
    local kw = "python3 " .. os.getenv("HOME") .. "/.config/hypr/skins/plasma/scripts/kwin-window.py "
    local actions = {
        Maximize = kw .. "maximize --mode toggle",
        ["Maximize (vertical only)"] = kw .. "maximize --mode vertical",
        ["Maximize (horizontal only)"] = kw .. "maximize --mode horizontal",
        Minimize = kw .. "minimize",
        Close = 'hyprctl dispatch "hl.dsp.window.close()"',
        Nothing = "",
    }
    local left, right = k.buttonsLeft or "M", k.buttonsRight or "IAX"
    local on_left = right == "" and left ~= ""
    local buttons = on_left and left or right
    hl.config({ plugin = { breezebars = {
        bar_buttons_alignment = on_left and "left" or "right",
        on_double_click = actions[k.doubleClick or "Maximize"] or "",
    } } })
    -- Rueda sobre la barra (kwinrc [MouseBindings] CommandTitlebarWheel); la interpreta el plugin.
    -- Sólo con un breezebars que la conozca (F6b): una opción desconocida daría error de configuración.
    if hl.plugin.breezebars.add_button and k.wheel then
        pcall(hl.config, { plugin = { breezebars = { on_wheel = k.wheel } } })
    end
    if hl.plugin.breezebars.add_button then
        local definitions = {
            X = { "close", actions.Close, "0xffda4453" },
            A = { "maximize", actions.Maximize, "0xfffcfcfc" },
            I = { "minimize", actions.Minimize, "0xfffcfcfc" },
        }
        -- En el banco derecho, add_button cuenta desde el extremo derecho hacia dentro.
        local first, last, step = #buttons, 1, -1
        if on_left then first, last, step = 1, #buttons, 1 end
        for i = first, last, step do
            local def = definitions[buttons:sub(i, i)]
            if def then
                hl.plugin.breezebars.add_button({
                    bg_color = def[3], fg_color = "0xfffcfcfc", size = 20,
                    icon = "breeze:" .. def[1], action = def[2],
                })
            end
        end
    end
end
return k
