-- Bloqueo de default (end-4): su superficie de bloqueo es transparente y el fondo desenfocado lo
-- pinta Background.qml debajo. Sin session_lock_xray Hyprland no dibuja nada bajo el bloqueo y se
-- ve negro. Como en end-4/dots-hyprland 2f2a376 (hypr/hyprland/general.lua, misc)
hl.config({
    misc = {
        session_lock_xray = true,
    },
})
