-----------------------
----- PERMISSIONS -----
-----------------------

-- See https://wiki.hypr.land/Configuring/Advanced-and-Cool/Permissions/
-- Please note permission changes here require a Hyprland restart and are not applied on-the-fly
-- for security reasons

-- hl.config({
--   ecosystem = {
--     enforce_permissions = true,
--   },
-- })

-- hl.permission("/usr/(bin|local/bin)/grim", "screencopy", "allow")
-- hl.permission("/usr/(lib|libexec|lib64)/xdg-desktop-portal-hyprland", "screencopy", "allow")
-- hl.permission("/usr/(bin|local/bin)/hyprpm", "plugin", "allow")

--------------------------------
---- WINDOWS AND WORKSPACES ----
--------------------------------

-- See https://wiki.hypr.land/Configuring/Basics/Window-Rules/
-- and https://wiki.hypr.land/Configuring/Basics/Workspace-Rules/

-- Example window rules that are useful

-- local suppressMaximizeRule = hl.window_rule({
--     -- Ignore maximize requests from all apps. You'll probably like this.
--     name  = "suppress-maximize-events",
--     match = { class = ".*" },
-- 
--     suppress_event = "maximize",
-- })
-- -- suppressMaximizeRule:set_enabled(false)

hl.window_rule({
    -- Fix some dragging issues with XWayland
    name  = "fix-xwayland-drags",
    match = {
        class      = "^$",
        title      = "^$",
        xwayland   = true,
        float      = true,
        fullscreen = false,
        pin        = false,
    },

    no_focus = true,
})

-- Layer rules also return a handle.
-- local overlayLayerRule = hl.layer_rule({
--     name  = "no-anim-overlay",
--     match = { namespace = "^my-overlay$" },
--     no_anim = true,
-- })
-- overlayLayerRule:set_enabled(false)

-- Hyprland-run windowrule
hl.window_rule({
    name  = "move-hyprland-run",
    match = { class = "hyprland-run" },

    move  = "20 monitor_h-120",
    float = true,
})

-- Nautilus file chooser dialog windowrule
hl.window_rule({
    name   = "nautilus-file-chooser",
    match  = {
        class = "org.gnome.Nautilus",
        title = "^(Open|Save|Select|Abrir|Guardar).*",
    },
    float  = true,
    size   = "1100 700",
    center = true,
})

--------------------------------
---- PERSISTENT DYNAMIC RULES --
--------------------------------

-- Reglas persistentes de ventanas (alternadas con ALT + Q)
pcall(require, "modules.persistent_rules")


-- Forzar Fallout 3 y Gamescope al monitor principal (DP-2 / Workspace 1)
hl.window_rule({
    name      = "fallout3-main-monitor",
    match     = {
        class = "^(fallout3.exe|Fallout3.exe|steam_app_22370|gamescope)$",
    },
    workspace = "1",
})

--------------------------------
---- KDE PLASMA RULES ----------
--------------------------------

local ok_theme, active_theme = pcall(require, "modules.theme")
local is_plasma = ok_theme and (active_theme.name == "plasma" or (active_theme.name and string.find(active_theme.name, "plasma") ~= nil))

if is_plasma then
    -- 1. Todas las ventanas en modo flotante individual (sin mosaico ni estela gris)
    hl.window_rule({
        name        = "plasma-float-all",
        match       = { class = ".*" },
        float       = true,
        no_shadow   = true,
        no_blur     = true,
        border_size = 0,
    })

    -- 2. Aplicaciones con decoraciones CSD propias (Steam, Firefox, Discord, Antigravity, etc.):
    --    No ponerles barra superior adicional hyprbars.
    hl.window_rule({
        name  = "plasma-csd-no-hyprbars",
        match = {
            class = "^(steam|steamwebhelper|firefox|firefox-bin|google-chrome.*|chromium.*|brave-browser|zen.*|vesktop|discord|armcord|webcord|spotify|antigravity|antigravity-ide|code|Code|code-oss|vscodium|cursor|org.gnome..*|nautilus|pavucontrol|easyeffects|gamescope|signal|telegram-desktop|org.telegram.desktop|baobab|evince|loupe)$",
        },
        -- ["hyprbars:no_bar"] = true,
    })
end

--------------------------------
---- ELECTRON / BROWSER RULES --
--------------------------------

-- Evitar que Electron / Chromium / Vesktop / Discord congelen WebRTC, decodificadores de video o caigan a 2 FPS al minimizar/perder foco
hl.window_rule({
    name = "electron-render-unfocused",
    match = {
        class = "^(vesktop|discord|armcord|webcord|google-chrome.*|chromium.*|brave-browser|zen.*|firefox.*|code|Code|code-oss|vscodium|cursor|antigravity-ide|obsidian|spotify)$",
    },
    render_unfocused = true,
})

-- Bordes cuadrados al maximizar o snapear ventanas (Estilo KDE Plasma)
hl.window_rule({
    name     = "plasma-maximized-square",
    match    = { fullscreen = true },
    rounding = 0,
})

hl.window_rule({
    name     = "plasma-snapped-square",
    match    = { tag = "snapped" },
    rounding = 0,
})
