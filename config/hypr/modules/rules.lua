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

local suppressMaximizeRule = hl.window_rule({
    -- Ignore maximize requests from all apps. You'll probably like this.
    name  = "suppress-maximize-events",
    match = { class = ".*" },

    suppress_event = "maximize",
})
-- suppressMaximizeRule:set_enabled(false)

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
    -- 1. Todas las ventanas en modo flotante individual (sin mosaico)
    hl.window_rule({
        name  = "plasma-float-all",
        match = { class = ".*" },
        float = true,
    })

    -- 2. Aplicaciones con decoraciones CSD propias (Steam, Firefox, Discord, Antigravity, etc.):
    --    No ponerles barra superior adicional hyprbars.
    hl.window_rule({
        name  = "plasma-csd-no-hyprbars",
        match = {
            class = "^(steam|firefox|firefox-bin|vesktop|discord|spotify|antigravity-ide|code|Code|org.gnome.Nautilus|nautilus|gamescope|signal)$",
        },
        ["hyprbars:no_bar"] = true,
    })
end
