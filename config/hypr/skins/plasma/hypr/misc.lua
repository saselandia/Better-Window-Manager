-- -----------------------------------------------------
-- Opciones de Hyprland propias de Breeze (Kde plasma). Las carga modules/appearance.lua sólo en esta
-- skin; al cambiar de skin, modules/binds.lua vuelve a poner las comunes.
-- -----------------------------------------------------

-- Clic para enfocar al estilo de KDE Plasma («Pulsar para enfocar» / ClickToFocus): el foco de
-- puntero sigue al cursor al pasar por encima (permite usar rueda o resaltado en ventanas sin
-- foco), mientras que el foco de teclado y activación sólo cambian al pulsar.
hl.config({
    input = {
        follow_mouse = 2,
    },
})
