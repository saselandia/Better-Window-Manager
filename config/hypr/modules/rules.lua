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

-- El compositor controla el maximizado, no el estado guardado por las apps.
-- Afecta también a sus botones CSD; usar el atajo de BWM para maximizar.
-- No suprime fullscreen (juegos/vídeo), ni los dispatchers manuales de Hyprland.
hl.window_rule({
    name  = "suppress-maximize-events",
    match = { class = ".*" },
    suppress_event = "maximize",
})

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


-- Juegos (Steam/Proton, Wine, gamescope) al monitor principal, en todos los estilos.
-- Va junto con scripts/xwayland-primary.py (autostart.sh), que marca ese mismo monitor como
-- principal en XWayland: sin él Wine toma el LG 4K y el juego sale diminuto o fuera de pantalla.
-- De Omarchy (misc.focus_on_activate, apps/steam.lua): el juego toma el foco y sube al frente
-- cuando Wine activa su ventana (con focus_on_activate global en false se ignoraba y quedaba
-- debajo de otras), y la pantalla no se apaga mientras está a pantalla completa.
-- Las ventanas sin bordes del tamaño del monitor las pone a pantalla completa window-guard.py.
hl.window_rule({
    name              = "games-main-monitor",
    match             = {
        class = "^(steam_app_[0-9]+|gamescope|.*\\.exe|.*\\.EXE)$",
    },
    monitor           = "desc:HP Inc. HP X24ih 1CR1420TD4",
    focus_on_activate = true,
    idle_inhibit      = "fullscreen",
})

-- Steam (Big Picture) tampoco deja que se apague la pantalla a pantalla completa
hl.window_rule({
    name         = "steam-idle-inhibit",
    match        = { class = "^steam$" },
    idle_inhibit = "fullscreen",
})

--------------------------------
---- KDE PLASMA RULES ----------
--------------------------------

local ok_theme, active_theme = pcall(require, "modules.theme")
local is_plasma = ok_theme and (active_theme.name == "plasma" or (active_theme.name and string.find(active_theme.name, "plasma") ~= nil))
-- Skins de WM tradicional ("windows": "traditional" en config/hypr/skins/<id>/skin.json): todo flota
local is_traditional = ok_theme and (active_theme.windows == "traditional" or is_plasma)

if is_traditional then
    -- 1. Todas las ventanas en modo flotante individual (sin mosaico ni estela gris)
    hl.window_rule({
        name        = "plasma-float-all",
        match       = { class = ".*" },
        float       = true,
        no_shadow   = true,
        no_blur     = true,
        border_size = 0,
    })

    -- 2. Barras de título: hyprbars detecta solo qué ventanas traen sus propios
    --    botones (xdg-decoration / kde-server-decoration / _MOTIF_WM_HINTS).
    --    Forzar a mano solo si hiciera falta:
    --      ["hyprbars:no_bar"] = true   -> quitar barra
    --      ["hyprbars:no_bar"] = false  -> forzar barra
end

--------------------------------
---- ELECTRON / BROWSER RULES --
--------------------------------

-- Evitar que Electron / Chromium / Vesktop / Discord congelen WebRTC, decodificadores de video o caigan a 2 FPS al minimizar/perder foco
hl.window_rule({
    name = "electron-render-unfocused",
    match = {
        class = "^(vesktop|discord|armcord|webcord|google-chrome.*|chromium.*|brave-browser|zen.*|firefox.*|code|Code|code-oss|vscodium|cursor|antigravity-ide|obsidian|spotify|claude|claude-desktop|com.anthropic.Claude|codex|codex-desktop|chatgpt|ChatGPT)$",
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

-- Terminal flotante de los plugins de Omarchy (omarchy-shims/omarchy-launch-floating-terminal-
-- with-presentation), como su etiqueta "floating-window": flota centrada
hl.window_rule({
    name   = "omarchy-floating-terminal",
    match  = { class = "^org\\.omarchy\\.terminal$" },
    float  = true,
    size   = "875 600",
    center = true,
})

-- Omarchy About: Fastfetch with its upstream ASCII layout, fitted by the launcher.
hl.window_rule({
    name   = "omarchy-about",
    match  = { class = "^org\\.omarchy\\.about$" },
    float  = true,
    fullscreen = false,
    size   = "1100 740",
    center = true,
})

-- Salvapantallas de terminal (launch-screensaver.sh), como el de Omarchy:
-- pantalla completa, sin barra de título y en su workspace especial si se reabre
hl.window_rule({
    name       = "bwm-screensaver",
    match      = { class = "^org\\.bwm\\.screensaver$" },
    fullscreen = true,
    float      = true,
    animation  = "slide",
})
-- Sin barra de título; el campo sólo existe con hyprbars cargado (estilo Plasma)
if hl.plugin and hl.plugin.hyprbars then
    hl.window_rule({
        name  = "bwm-screensaver-nobar",
        match = { class = "^org\\.bwm\\.screensaver$" },
        ["hyprbars:no_bar"] = true,
    })
end
