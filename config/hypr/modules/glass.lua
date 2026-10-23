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
