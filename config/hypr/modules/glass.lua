-- -----------------------------------------------------
-- Modo glass (ventanas translúcidas), port de Omarchy
-- (default/hypr/glass.lua y toggles/window-glassy.lua, MIT)
-- Se activa con scripts/glass.sh, que crea ~/.local/state/bwm/glass
-- -----------------------------------------------------
local state = io.open(os.getenv("HOME") .. "/.local/state/bwm/glass", "r")
if state then
    state:close()

    -- Vidrio esmerilado: lo que hay detrás de una superficie translúcida se desenfoca
    hl.config({
        decoration = {
            blur = {
                enabled           = true,
                size              = 4,
                passes            = 2,
                new_optimizations = true,
                xray              = false,
                contrast          = 1.0,
                brightness        = 0.75,
                noise             = 0.01,
                vibrancy          = 0.35,
                vibrancy_darkness = 0.35,
                popups            = true,
                special           = true,
            },
        },
    })

    -- Retro, como Omarchy 4.5 (toggles/window-glassy.lua, quattro e56f833): cada ventana se desvanece
    -- entera al 75 % (la mayoría de apps pintan su fondo opaco) y las capas de su shell desenfocan lo
    -- que tienen detrás. Va antes de la regla de GTK de abajo, que se queda con su 80 % en esas apps.
    local ok_theme, active_theme = pcall(require, "modules.theme")
    if ok_theme and active_theme.name == "retro" then
        hl.window_rule({
            name    = "bwm-glass-all",
            match   = { class = ".*" },
            opacity = "0.75 0.75",
        })
        hl.layer_rule({
            name         = "bwm-glass-omarchy-layers",
            match        = { namespace = "^(omarchy-bar|omarchy-menu|omarchy-notifications|omarchy-osd|omarchy-polkit|omarchy-reminders|omarchy-clipboard|omarchy-emojis|omarchy-image-selector|omarchy-keyboard-panel|omarchy-network-qr)$" },
            blur         = true,
            ignore_alpha = 0.3,
        })
    end

    -- Las apps GTK pintan su fondo opaco: se atenúan enteras (los terminales tienen su
    -- propio fondo translúcido desde glass.sh, que deja el texto nítido)
    hl.window_rule({
        name    = "bwm-glass-gtk",
        match   = { class = "^(org\\.gnome\\.Nautilus|blueman-manager|\\.?blueman-manager-wrapped|pavucontrol|org\\.pulseaudio\\.pavucontrol|nm-connection-editor)$" },
        opacity = "0.80 0.80",
    })

    -- Barra, menús y paneles de Quickshell con desenfoque detrás
    hl.layer_rule({
        name         = "bwm-glass-shell",
        match        = { namespace = "^quickshell" },
        blur         = true,
        ignore_alpha = 0.3,
    })
end
