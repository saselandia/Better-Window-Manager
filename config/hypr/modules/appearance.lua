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
-- En estilo Retro (Omarchy): se sincroniza dinámicamente con el wallpaper pero potenciando la saturación (colores vivos y chillones).
-- En estilo Default (Material You): mantiene la paleta tonal pastel original de Matugen.
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
    -- default (end-4): como dots-hyprland (matugen templates/hyprland/colors.lua), borde casi
    -- invisible sin degradado: outline_variant al 0x77 activo, surface_container_low al 0x33 inactivo
    local function with_alpha(c_str, alpha, fallback)
        local hex = c_str and string.match(c_str, "%x%x%x%x%x%x")
        return hex and ("rgba(" .. hex .. alpha .. ")") or fallback
    end
    active_1 = with_alpha(ok and colors.outline_variant, "77", "rgba(44464f77)")
    active_2 = active_1
    inactive = with_alpha(ok and colors.surface_container_low, "33", "rgba(1a1b2033)")
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
        -- Todas opacas: Retro, como Omarchy (sólo terminales/TUIs son translúcidos, ver omarchy_windows.lua);
        -- default (end-4), como dots-hyprland, distingue las inactivas oscureciéndolas (dim_*), no con opacidad
        inactive_opacity = 1.0,

        -- default (end-4): oscurecido de dots-hyprland (general.lua)
        dim_inactive = not is_retro and not is_plasma,
        dim_strength = 0.05,
        dim_special  = 0.2,

        -- Sombra de dots-hyprland en default (end-4); desactivada en retro y plasma para evitar
        -- estela/halo gris en los bordes
        shadow = {
            enabled      = not is_retro and not is_plasma,
            range        = 20,
            offset       = { 0, 2 },
            render_power = 10,
            color        = "rgba(00000020)",
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

    -- Las curvas y animaciones son de cada skin: skins/<id>/hypr/animations.lua
    animations = {
        enabled = true,
    },
})

------------------------------------
---- ANIMACIONES DE LA SKIN ---------
------------------------------------

-- Cada skin copia las de su escritorio original: default (end-4) las de dots-hyprland,
-- Retro las de Omarchy y Breeze (Kde plasma) las suyas
local anim_skin = (ok_theme and active_theme.name) or "default"
local ok_anim, anim_err = pcall(require, "skins." .. anim_skin .. ".hypr.animations")
if not ok_anim then
    local msg = tostring(anim_err):gsub("['\"`$\\]", "")
    os.execute("notify-send -a BWM 'Animaciones de la skin " .. anim_skin .. "' '" .. msg .. "' &")
end

-- Un hyprctl reload no devuelve a su valor por defecto lo que no se vuelve a poner: lo que una
-- skin cambia en su misc.lua se repone aquí antes, para que no se quede al cambiar de skin
hl.config({
    render = { cm_auto_hdr = (hl.get_config and hl.get_config("render.cm_auto_hdr") ~= nil) and 1 or nil },
})


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

-- Proporción de ventana única (Super + Enter / toggle-single-window-aspect.sh)
local aspect_state = io.open(os.getenv("HOME") .. "/.local/state/bwm/single-window-aspect", "r")
if aspect_state then
    aspect_state:close()
    hl.config({
        layout = {
            single_window_aspect_ratio = { 1, 1 },
        },
    })
else
    hl.config({
        layout = {
            single_window_aspect_ratio = { 0, 0 },
        },
    })
end


----------------
----  MISC  ----
----------------

hl.config({
    misc = {
        force_default_wallpaper = -1,    -- Set to 0 or 1 to disable the anime mascot wallpapers
        disable_hyprland_logo   = false, -- If true disables the random hyprland logo / anime girl background. :(
        -- Como Omarchy: una app que pide activarse (enlace abierto desde Discord, etc.) toma el foco
        -- y te lleva a su workspace, en vez de quedar sólo marcada como urgente
        focus_on_activate       = true,
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

-- plugin.breezebars (barras de título Breeze, src/hyprbars): habilitar en Plasma y deshabilitar en las
-- demás skins. Las barras de los workspaces flotantes de Retro son otro plugin, el de Omarchy
-- (hyprbars), que configura skins/retro/hypr/workspace-modes.lua.
if hl.plugin and hl.plugin.breezebars then
    if is_plasma then
        hl.config({
            plugin = {
                breezebars = {
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
        if hl.plugin.breezebars.add_button then
            -- Extremo derecho: Cerrar (círculo rojo Breeze #da4453 al pasar el ratón)
            hl.plugin.breezebars.add_button({
                bg_color = "0xffda4453",
                fg_color = "0xfffcfcfc",
                size = 20,
                icon = "breeze:close",
                action = "hyprctl dispatch \"hl.dsp.window.close()\""
            })
            -- Centro: Maximizar / Restaurar
            hl.plugin.breezebars.add_button({
                bg_color = "0xfffcfcfc",
                fg_color = "0xfffcfcfc",
                size = 20,
                icon = "breeze:maximize",
                action = "hyprctl dispatch \"hl.dsp.window.fullscreen({ mode = 1, action = 'toggle' })\""
            })
            -- Izquierda: Minimizar
            hl.plugin.breezebars.add_button({
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
                breezebars = {
                    enabled = false,
                }
            }
        })
    end
end

-- XWayland sin escalado (como Omarchy): los juegos y apps X11 dibujan a la resolución nativa
-- del monitor en vez de reescalarse borrosos si algún monitor usa escala distinta de 1
hl.config({
    xwayland = {
        force_zero_scaling = true,
    },
})

-- Ajustes de la skin, si los tiene: bloqueo (skins/<id>/hypr/lock.lua), otras opciones de
-- Hyprland de su escritorio original (skins/<id>/hypr/misc.lua), colocación de ventanas nuevas
-- (skins/<id>/hypr/placement.lua, Breeze) y modos de workspace
-- (skins/<id>/hypr/workspace-modes.lua, Retro). Al final, para que lo suyo gane a lo común de arriba
-- (p. ej. las barras de título de los workspaces flotantes de Retro).
for _, part in ipairs({ { "lock", "Bloqueo" }, { "misc", "Opciones" }, { "placement", "Colocación de ventanas" },
                       { "workspace-modes", "Modos de workspace" } }) do
    local mod = "skins." .. anim_skin .. ".hypr." .. part[1]
    if package.searchpath and package.searchpath(mod, package.path) then
        local ok_part, part_err = pcall(require, mod)
        if not ok_part then
            local msg = tostring(part_err):gsub("['\"`$\\]", "")
            os.execute("notify-send -a BWM '" .. part[2] .. " de la skin " .. anim_skin .. "' '" .. msg .. "' &")
        end
    end
end
