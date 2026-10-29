-- -----------------------------------------------------
-- Ventanas al estilo Omarchy (estilo Retro), port de default/hypr/windows.lua,
-- apps/terminals.lua y glass.lua (MIT):
--   * las apps son opacas; los terminales y TUIs (y Nautilus) optan por la
--     transparencia con la etiqueta "transparent-window" (opacidad 0.985 / 0.96)
--   * Super+Backspace (window-transparency.sh) la alterna en la ventana activa
--   * window-transparency.sh opaque la quita para todas
-- -----------------------------------------------------
local ok_theme, active_theme = pcall(require, "modules.theme")
if not (ok_theme and active_theme.name == "retro") then
    return
end

-- Etiqueta "terminal" para distinguir terminales y TUIs lanzadas con app-id propio
hl.window_rule({
    name  = "omarchy-terminals",
    match = { class = "^(Alacritty|kitty|com\\.mitchellh\\.ghostty|foot|org\\.codeberg\\.dnkl\\.foot|wezterm|org\\.omarchy\\..*|TUI\\..*)$" },
    tag   = "+terminal",
})

-- Ajustes de Retro (retroSettings.qml) como ventanas flotantes de Omarchy: una página suelta es una
-- ventanita centrada; la ventana completa (Super+I), un poco mayor. Marco: el borde de acento de Retro.
hl.window_rule({
    name   = "omarchy-settings-page",
    match  = { class = "^org\\.quickshell$", title = "^Configuración · .+$" },
    float  = true,
    size   = "1000 680",
    center = true,
})
hl.window_rule({
    name   = "omarchy-settings",
    match  = { class = "^org\\.quickshell$", title = "^Configuración$" },
    float  = true,
    size   = "1150 760",
    center = true,
})

local opaque = io.open(os.getenv("HOME") .. "/.local/state/bwm/windows-opaque", "r")
if opaque then
    opaque:close()
    return
end

-- Terminales/TUIs y apps GTK que Omarchy hace transparentes por defecto
hl.window_rule({ name = "omarchy-transparent-terminals", match = { tag = "terminal" }, tag = "+transparent-window" })
hl.window_rule({ name = "omarchy-transparent-nautilus", match = { class = "^org\\.gnome\\.Nautilus$" }, tag = "+transparent-window" })

-- Cualquier ventana con la etiqueta (también la que se marca con Super+Backspace)
hl.window_rule({ name = "omarchy-transparent-window", match = { tag = "transparent-window" }, opacity = "0.985 0.96" })
