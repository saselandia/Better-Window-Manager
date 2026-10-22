-------------------
---- AUTOSTART ----
-------------------

-- Referencia: https://wiki.hypr.land/Configuring/Basics/Autostart/

local autostart_script = os.getenv("HOME") .. "/.config/hypr/scripts/autostart.sh"

-- 1. Arranque oficial al iniciar Hyprland (tras inicializar el servidor Wayland)
hl.on("hyprland.start", function()
    hl.exec_cmd(autostart_script)
end)

-- 2. Asegurar demonios si se recarga la configuración en caliente (idempotente)
hl.on("config.reloaded", function()
    hl.exec_cmd(autostart_script)
end)
