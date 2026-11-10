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

-- Interruptores de Hyprland de Omarchy (omarchy-hyprland-toggle): cada uno es un archivo en
-- ~/.local/state/omarchy/toggles/hypr/ que se copia de Commons/omarchy/default/hypr/toggles/ y recarga
-- Hyprland. Omarchy lee esa carpeta entera; aquí sólo los que BWM admite (los demás, como window-glassy,
-- necesitan piezas de Omarchy que BWM no tiene):
--   bar-glassy    fondo «vidrio» de la barra (doble clic en su centro, o `omarchy-bar background glassy`)
--   no-animations sin animaciones, desenfoque ni sombras (menú → Estilo → Animaciones)
-- Va después de animations.lua, así que gana.
local state_home = os.getenv("XDG_STATE_HOME") or ((os.getenv("HOME") or "") .. "/.local/state")
for _, name in ipairs({ "bar-glassy", "no-animations" }) do
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
