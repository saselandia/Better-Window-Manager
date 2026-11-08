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
