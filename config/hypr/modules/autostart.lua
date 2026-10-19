-------------------
---- AUTOSTART ----
-------------------

-- Referencia: https://wiki.hypr.land/Configuring/Basics/Autostart/

local autostart_script = os.getenv("HOME") .. "/.config/hypr/scripts/autostart.sh"

local function run_autostart()
    os.execute(autostart_script .. " >/dev/null 2>&1 &")
end

-- 1. Arranque oficial al iniciar Hyprland (tras inicializar el servidor Wayland)
hl.on("hyprland.start", function()
    run_autostart()
end)

-- 2. Asegurar demonios si se recarga la configuración en caliente (idempotente)
hl.on("config.reloaded", function()
    run_autostart()
end)

-- 3. Ejecutar inmediatamente al procesar la configuración
run_autostart()
