-------------------------------
---- ENVIRONMENT VARIABLES ----
-------------------------------

-- See https://wiki.hypr.land/Configuring/Advanced-and-Cool/Environment-variables/



-----------------------
---- LOOK AND FEEL ----
-----------------------

-- Refer to https://wiki.hypr.land/Configuring/Basics/Variables/
-- 1. Importar los colores calculados por Matugen con valores de respaldo (fallback)
local ok, colors = pcall(require, "modules.colors")

local active_1 = ok and colors.primary or "rgba(33ccffee)"
local active_2 = ok and colors.primary_container or "rgba(00ff99ee)"
local inactive = ok and colors.outline or "rgba(595959aa)"

hl.config({
    general = {
        gaps_in  = 3,
        gaps_out = 5,
        border_size = 2,

        col = {
            -- Degradado dinámico según la paleta del wallpaper
            active_border   = { colors = { active_1, active_2 }, angle = 45 },
            inactive_border = inactive,
        },

        -- Permitir redimensionar arrastrando el borde de la ventana
        resize_on_border = true,
        allow_tearing    = false,
        layout           = "dwindle",
    },

    decoration = {
        rounding       = 0,
        rounding_power = 2,

        active_opacity   = 1.0,
        inactive_opacity = 0.95, -- Leve transparencia para ventanas en segundo plano

        -- Sombra amplia y suave estilo Material 3
        shadow = {
            enabled      = true,
            range        = 18,
            render_power = 3,
            color        = "rgba(00000035)",
        },

        -- Blur Dual-Kawase suave para Rofi, terminales translúcidas y paneles
        blur = {
            enabled           = true,
            size              = 6,
            passes            = 3,
            vibrancy          = 0.2,
            new_optimizations = true,
            ignore_opacity    = true,
        },
    },

    -- Animaciones fluidas características de End_4
    animations = {
        enabled = true,
    },
})

------------------------------------
---- MD3 BEZIERS & ANIMATIONS ------
------------------------------------

-- Curvas Bézier de Material Design 3 (End_4 / dots-hyprland)
hl.curve("md3_standard", { type = "bezier", points = { {0.2, 0.0}, {0.0, 1.0} } })
hl.curve("md3_decel",    { type = "bezier", points = { {0.05, 0.7}, {0.1, 1.0} } })
hl.curve("md3_accel",    { type = "bezier", points = { {0.3, 0.0}, {0.8, 0.15} } })
hl.curve("menu_decel",   { type = "bezier", points = { {0.1, 1.0}, {0.0, 1.0} } })

-- Animaciones dinámicas de ventanas y escritorio
hl.animation({ leaf = "windows",          enabled = true, speed = 3,  bezier = "md3_decel",  style = "popin 60%" })
hl.animation({ leaf = "windowsIn",        enabled = true, speed = 3,  bezier = "md3_decel",  style = "popin 60%" })
hl.animation({ leaf = "windowsOut",       enabled = true, speed = 3,  bezier = "md3_accel",  style = "popin 60%" })
hl.animation({ leaf = "border",           enabled = true, speed = 10, bezier = "default" })
hl.animation({ leaf = "fade",             enabled = true, speed = 3,  bezier = "md3_decel" })
hl.animation({ leaf = "fadeIn",           enabled = true, speed = 3,  bezier = "md3_decel" })
hl.animation({ leaf = "fadeOut",          enabled = true, speed = 3,  bezier = "md3_accel" })
hl.animation({ leaf = "workspaces",       enabled = true, speed = 4,  bezier = "menu_decel", style = "slide" })
hl.animation({ leaf = "workspacesIn",     enabled = true, speed = 4,  bezier = "menu_decel", style = "slide" })
hl.animation({ leaf = "workspacesOut",    enabled = true, speed = 4,  bezier = "menu_decel", style = "slide" })
hl.animation({ leaf = "specialWorkspace", enabled = true, speed = 3,  bezier = "md3_decel",  style = "slidevert" })

-- Ref https://wiki.hypr.land/Configuring/Basics/Workspace-Rules/
-- "Smart gaps" / "No gaps when only"
-- uncomment all if you wish to use that.
-- hl.workspace_rule({ workspace = "w[tv1]", gaps_out = 0, gaps_in = 0 })
-- hl.workspace_rule({ workspace = "f[1]",   gaps_out = 0, gaps_in = 0 })
-- hl.window_rule({
--     name  = "no-gaps-wtv1",
--     match = { float = false, workspace = "w[tv1]" },
--     border_size = 0,
--     rounding    = 0,
-- })
-- hl.window_rule({
--     name  = "no-gaps-f1",
--     match = { float = false, workspace = "f[1]" },
--     border_size = 0,
--     rounding    = 0,
-- })

-- See https://wiki.hypr.land/Configuring/Layouts/Dwindle-Layout/ for more
hl.config({
    dwindle = {
        preserve_split = true, -- You probably want this
    },
})

-- See https://wiki.hypr.land/Configuring/Layouts/Master-Layout/ for more
hl.config({
    master = {
        new_status = "master",
    },
})

-- See https://wiki.hypr.land/Configuring/Layouts/Scrolling-Layout/ for more
hl.config({
    scrolling = {
        fullscreen_on_one_column = true,
    },
})

----------------
----  MISC  ----
----------------

hl.config({
    misc = {
        force_default_wallpaper = -1,    -- Set to 0 or 1 to disable the anime mascot wallpapers
        disable_hyprland_logo   = false, -- If true disables the random hyprland logo / anime girl background. :(
    },
})
