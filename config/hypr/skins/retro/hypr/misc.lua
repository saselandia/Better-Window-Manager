-- -----------------------------------------------------
-- Opciones de Hyprland de Omarchy 4.5 para Retro (basecamp/omarchy, quattro d9cc361c, MIT,
-- default/hypr/looknfeel.lua). Las carga modules/appearance.lua sólo en esta skin.
-- Las que no existen en el Hyprland en marcha (bell_sound y no_donation_nag llegan después
-- de 0.56) se dejan sin poner, como hace Omarchy (#18047), para no dar error de configuración.
-- -----------------------------------------------------

local function has(option)
    return hl.get_config and hl.get_config(option) ~= nil
end

hl.config({
    misc = {
        -- Sin campanilla en cada BEL de la terminal (autocompletado sin resultados, avisos de TUIs)
        bell_sound = has("misc.bell_sound") and "none" or nil,
        -- Sin la ventana de donación de Hyprland
        no_donation_nag = has("misc.no_donation_nag") and true or nil,
    },
    render = {
        -- Una ventana a pantalla completa no pasa la pantalla a HDR: el contenido SDR se veía lavado
        cm_auto_hdr = has("render.cm_auto_hdr") and 0 or nil,
    },
})

-- Más de looknfeel.lua de Omarchy (quattro c18b00c5). modules/appearance.lua repone sus valores por
-- defecto antes, para que no se queden al pasar a otra skin.
hl.config({
    general = {
        -- Franja más estrecha para agarrar el borde y redimensionar
        extend_border_grab_area = 8,
    },
    misc = {
        -- Sin el texto de bienvenida sobre el fondo ni el aviso al cambiar la escala
        disable_splash_rendering   = true,
        disable_scale_notification = true,
        -- Aviso de «la app no responde» tras 3 pings perdidos
        anr_missed_pings           = 3,
        -- Una app se abre en el workspace en el que estás, no en el que estaba al lanzarla
        initial_workspace_tracking = 0,
    },
    cursor = {
        -- El puntero se oculta al escribir
        hide_on_key_press = true,
    },
    binds = {
        -- Cambiar de workspace cierra el workspace especial abierto
        hide_special_on_workspace_change = true,
    },
})

-- Interruptores de Hyprland de Omarchy (omarchy-hyprland-toggle): cada uno es un archivo en
-- ~/.local/state/omarchy/toggles/hypr/ que se copia de Commons/omarchy/default/hypr/toggles/ y recarga
-- Hyprland. Omarchy lee esa carpeta entera; aquí sólo los que BWM admite (los demás, como window-glassy,
-- necesitan piezas de Omarchy que BWM no tiene):
--   bar-glassy    fondo «vidrio» de la barra (doble clic en su centro, o `omarchy-bar background glassy`)
--   no-animations sin animaciones, desenfoque ni sombras (menú → Estilo → Animaciones)
--   corners-sharp / corners-rounded  esquinas de las ventanas, sea cual sea el tema (Estilo → Ventanas)
--   window-no-gaps  sin huecos ni bordes (Estilo → Ventanas)
-- Va después de animations.lua, así que gana.
local state_home = os.getenv("XDG_STATE_HOME") or ((os.getenv("HOME") or "") .. "/.local/state")

-- El hyprland.lua del tema de Omarchy activo (bordes con degradado, sombras de Lumon, borde de los
-- grupos…), que Omarchy carga después de sus valores por defecto y antes de los interruptores: lo trae
-- el tema estático (kanagawa, last-horizon, lumon, retro-82, solitude) y bwm_omarchy_apps lo copia a
-- ~/.local/state/bwm/omarchy/theme. Sin él, los colores de retro_colors.lua. Usa el `o.transparent_window`
-- de Omarchy (sólo kanagawa), que aquí es una regla de opacidad.
do
    local theme_file = state_home .. "/omarchy/current/theme/hyprland.lua"
    local file = io.open(theme_file, "r")
    if file then
        file:close()
        local o = {
            transparent_window = function(match, opacity)
                hl.window_rule({
                    match = type(match) == "string" and { class = match } or match,
                    opacity = opacity or "0.985 0.96",
                })
            end,
        }
        local chunk, err = loadfile(theme_file, "t", setmetatable({ o = o }, { __index = _G }))
        local ok = chunk ~= nil
        if ok then ok, err = pcall(chunk) end
        if not ok then
            print("BWM: hyprland.lua del tema: " .. tostring(err))
        end
    end
end

for _, name in ipairs({ "bar-glassy", "no-animations", "corners-sharp", "corners-rounded", "window-no-gaps" }) do
    local toggle = state_home .. "/omarchy/toggles/hypr/" .. name .. ".lua"
    local file = io.open(toggle, "r")
    if file then
        file:close()
        local ok, err = pcall(dofile, toggle)
        if not ok then
            print("BWM: " .. name .. ".lua: " .. tostring(err))
        end
    end
end
