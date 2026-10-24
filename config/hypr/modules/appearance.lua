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
local ok_theme, active_theme = pcall(require, "modules.theme")
local ok_retro, retro_colors = pcall(require, "modules.retro_colors")
local ok_plasma, plasma_colors = pcall(require, "modules.plasma_colors")

local is_retro = ok_theme and (active_theme.name == "retro" or (active_theme.name and string.find(active_theme.name, "retro") ~= nil))
local is_plasma = ok_theme and (active_theme.name == "plasma" or (active_theme.name and string.find(active_theme.name, "plasma") ~= nil))
local win_rounding = (ok_theme and active_theme.rounding) or 0
local win_round_pwr = (ok_theme and active_theme.rounding_power) or 2
local border_sz = is_plasma and 0 or ((ok_theme and active_theme.border_size) or 2)
local g_in = (ok_theme and active_theme.gaps_in) or 3
local g_out = (ok_theme and active_theme.gaps_out) or 5

-- Configuración de colores de bordes:
-- En tema Retro (Omarchy): se sincroniza dinámicamente con el wallpaper pero potenciando la saturación (colores vivos y chillones).
-- En tema Default (Material You): mantiene la paleta tonal pastel original de Matugen.
local function boost_color(c_str, fallback)
    if not c_str then return fallback end
    local hex = string.match(c_str, "%x%x%x%x%x%x")
    if not hex then return fallback end
    local r = tonumber(string.sub(hex, 1, 2), 16) / 255
    local g = tonumber(string.sub(hex, 3, 4), 16) / 255
    local b = tonumber(string.sub(hex, 5, 6), 16) / 255
    local max_c = math.max(r, math.max(g, b))
    local min_c = math.min(r, math.min(g, b))
    local d = max_c - min_c
    if max_c > 0 and d > 0.05 then
        local factor = 1.7
        r = math.min(1.0, math.max(0.0, max_c - (max_c - r) * (1 / factor)))
        g = math.min(1.0, math.max(0.0, max_c - (max_c - g) * (1 / factor)))
        b = math.min(1.0, math.max(0.0, max_c - (max_c - b) * (1 / factor)))
        return string.format("rgba(%02x%02x%02xee)", math.floor(r * 255), math.floor(g * 255), math.floor(b * 255))
    end
    return fallback
end

local active_1
local active_2
local inactive

if is_plasma then
    -- En KDE Plasma Breeze Dark: sin estela ni borde gris alrededor de las ventanas
    active_1 = "rgba(00000000)"
    active_2 = "rgba(00000000)"
    inactive = "rgba(00000000)"
elseif is_retro then
    active_1 = (ok_retro and retro_colors and retro_colors.accent) or boost_color(ok and colors.primary, "rgba(33ccffee)")
    active_2 = (ok_retro and retro_colors and retro_colors.secondary) or boost_color(ok and colors.secondary, "rgba(00ff99ee)")
    inactive = (ok_retro and retro_colors and retro_colors.border_inactive) or "rgba(101520aa)"
else
    active_1 = ok and colors.primary or "rgba(33ccffee)"
    active_2 = ok and colors.primary_container or "rgba(00ff99ee)"
    inactive = ok and colors.outline or "rgba(595959aa)"
end

hl.config({
    general = {
        gaps_in  = g_in,
        gaps_out = g_out,
        border_size = border_sz,

        col = {
            -- Degradado dinámico según la paleta del wallpaper
            active_border   = { colors = { active_1, active_2 }, angle = 45 },
            inactive_border = inactive,
        },

        -- Permitir redimensionar arrastrando el borde de la ventana
        resize_on_border = true,
        allow_tearing    = false,
        layout           = "dwindle",

        -- Window Snapping magnético para ventanas flotantes (Hyprland 0.45+)
        snap = {
            enabled        = true,
            window_gap     = 10,
            monitor_gap    = 0,
            border_overlap = true,
            respect_gaps   = false,
        },
    },

    decoration = {
        rounding       = win_rounding,
        rounding_power = win_round_pwr,

        active_opacity   = 1.0,
        -- Retro, como Omarchy: apps opacas (sólo terminales/TUIs son translúcidos, ver omarchy_windows.lua)
        inactive_opacity = (is_plasma or is_retro) and 1.0 or 0.95,

        -- Sombra desactivada en retro y plasma para evitar estela/halo gris en los bordes
        shadow = {
            enabled      = not is_retro and not is_plasma,
            range        = 18,
            render_power = 3,
            color        = "rgba(00000035)",
        },

        -- Blur Dual-Kawase desactivado en plasma para evitar halo gris en márgenes CSD
        blur = {
            enabled           = not is_plasma and not is_retro,  -- Omarchy: sin blur salvo modo glass
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

------------------------------------
---- KDE PLASMA TITLEBAR & BARS ----
------------------------------------

hl.config({
    group = {
        auto_group = false,
        drag_into_group = 0,
        merge_groups_on_drag = false,
        merge_groups_on_groupbar = false,
        merge_floated_into_tiled_on_groupbar = false,
        groupbar = {
            enabled = false,
        }
    }
})

-- plugin.hyprbars: habilitar en Plasma y deshabilitar limpiamente en otros temas
if hl.plugin and hl.plugin.hyprbars then
    if is_plasma then
        hl.config({
            plugin = {
                hyprbars = {
                    enabled = true,
                    -- Paleta Breeze Dark (Plasma 6): cabecera activa / inactiva
                    bar_color = "0xff2a2e32",
                    inactive_bar_color = "0xff202326",
                    ["col.text"] = "0xfffcfcfc",
                    ["col.inactive_text"] = "0xffa1a9b1",
                    bar_height = 30,
                    bar_text_size = 10,
                    bar_text_font = "Google Sans Flex",
                    bar_text_align = "center",
                    bar_part_of_window = true,
                    bar_precedence_over_border = true,
                    bar_buttons_alignment = "right",
                    bar_padding = 6,
                    bar_button_padding = 4,
                    icon_on_hover = false,
                    on_double_click = "hyprctl dispatch \"hl.dsp.window.fullscreen({ mode = 1, action = 'toggle' })\"",
                }
            }
        })

        -- Botones con la decoración Breeze real (iconos vectoriales "breeze:*"):
        -- bg_color = círculo al pasar el ratón, fg_color = color del icono.
        -- La barra solo aparece en ventanas que piden decoración al compositor;
        -- las que traen sus propios botones (CSD) se detectan solas
        -- (comprobar con: hyprctl hyprbars-csd).
        if hl.plugin.hyprbars.add_button then
            -- Extremo derecho: Cerrar (círculo rojo Breeze #da4453 al pasar el ratón)
            hl.plugin.hyprbars.add_button({
                bg_color = "0xffda4453",
                fg_color = "0xfffcfcfc",
                size = 20,
                icon = "breeze:close",
                action = "hyprctl dispatch \"hl.dsp.window.close()\""
            })
            -- Centro: Maximizar / Restaurar
            hl.plugin.hyprbars.add_button({
                bg_color = "0xfffcfcfc",
                fg_color = "0xfffcfcfc",
                size = 20,
                icon = "breeze:maximize",
                action = "hyprctl dispatch \"hl.dsp.window.fullscreen({ mode = 1, action = 'toggle' })\""
            })
            -- Izquierda: Minimizar
            hl.plugin.hyprbars.add_button({
                bg_color = "0xfffcfcfc",
                fg_color = "0xfffcfcfc",
                size = 20,
                icon = "breeze:minimize",
                action = "/home/sasel/.config/hypr/scripts/toggle-minimize.py min"
            })
        end
    else
        hl.config({
            plugin = {
                hyprbars = {
                    enabled = false,
                }
            }
        })
    end
end
