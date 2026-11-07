-- Pantalla completa limpia en todas las apps y skins: sin borde, sombra, redondeo ni atenuado
-- de ventana inactiva. La transparencia y el desenfoque de cada app se respetan.
-- Se carga después de omarchy_windows y glass.
hl.window_rule({
    name        = "bwm-fullscreen-clean",
    match       = { fullscreen = true },
    no_dim      = true,
    no_shadow   = true,
    border_size = 0,
    rounding    = 0,
})
