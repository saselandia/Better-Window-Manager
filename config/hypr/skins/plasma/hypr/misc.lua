-- -----------------------------------------------------
-- Opciones de Hyprland propias de Breeze (Kde plasma). Las carga modules/appearance.lua sólo en esta
-- skin; al cambiar de skin, modules/binds.lua vuelve a poner las comunes.
-- -----------------------------------------------------

-- Clic para enfocar, como KWin («Haga clic para activar» es su política predeterminada) y como los
-- workspaces flotantes de Omarchy 4.5: con las ventanas superpuestas, enfocar al pasar el ratón
-- cambiaba de ventana al cruzar por encima de otra camino de la que se quería usar.
hl.config({
    input = {
        follow_mouse = 0,
    },
})
