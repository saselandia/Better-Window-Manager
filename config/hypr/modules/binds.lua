---------------------
---- MY PROGRAMS ----
---------------------

-- Set programs that you use
local terminal    = "kitty"
local fileManager = "nautilus"
local menu        = "quickshell -c ii ipc call search toggle || rofi -show drun"

---------------
---- INPUT ----
---------------

hl.config({
    input = {
        kb_layout  = "es",
        kb_variant = "",
        kb_model   = "",
        kb_options = "",
        kb_rules   = "",

        follow_mouse = 1,

        sensitivity = 0, -- -1.0 - 1.0, 0 means no modification.

        touchpad = {
            natural_scroll = false,
        },
    },
})

hl.gesture({
    fingers = 3,
    direction = "horizontal",
    action = "workspace"
})

-- Example per-device config
-- See https://wiki.hypr.land/Configuring/Advanced-and-Cool/Devices/ for more
hl.device({
    name        = "epic-mouse-v1",
    sensitivity = -0.5,
})


---------------------
---- KEYBINDINGS ----
---------------------

local mainMod = "ALT" -- Sets "Alt" key as main modifier

-- 1. General & Guía de atajos
hl.bind(mainMod .. " + A", hl.dsp.exec_cmd("quickshell -c ii ipc call cheatsheet toggle"), { description = "General: Guía de atajos (Cheatsheet)" })

-- 2. Lanzadores de aplicaciones
hl.bind("CTRL + RETURN", hl.dsp.exec_cmd(terminal), { description = "Lanzador: Abrir terminal (Kitty)" })
hl.bind("SUPER_L", hl.dsp.exec_cmd(menu), { description = "Lanzador: Menú de aplicaciones / Búsqueda" })
hl.bind(mainMod .. " + E", hl.dsp.exec_cmd(fileManager), { description = "Lanzador: Explorador de archivos (Nautilus)" })
hl.bind(mainMod .. " + W", hl.dsp.exec_cmd(os.getenv("HOME") .. "/.config/hypr/scripts/wallpaper-picker.sh"), { description = "Lanzador: Selector de fondos de pantalla" })

-- 3. Gestión de ventanas
hl.bind("ALT + X", hl.dsp.window.close(), { description = "Ventana: Cerrar ventana activa" })
hl.bind(mainMod .. " + Q", hl.dsp.exec_cmd(os.getenv("HOME") .. "/.config/hypr/scripts/toggle-float-persistent.py"), { description = "Ventana: Recordar regla flotante persistente" })
hl.bind(mainMod .. " + J", hl.dsp.layout("togglesplit"), { description = "Ventana: Alternar división horizontal/vertical" })
hl.bind(mainMod .. " + RETURN", hl.dsp.window.fullscreen({ mode = 0, action = "toggle" }), { description = "Ventana: Pantalla completa" })

-- Selector visual de ventanas Alt+Tab (Material You / Quickshell HUD)
hl.bind("ALT + TAB", hl.dsp.exec_cmd("quickshell -c ii ipc call altTab next"), { repeating = true, description = "Ventana: Selector visual de ventanas (Alt+Tab)" })
hl.bind("ALT + SHIFT + TAB", hl.dsp.exec_cmd("quickshell -c ii ipc call altTab prev"), { repeating = true })
hl.bind("Alt_L", hl.dsp.exec_cmd("quickshell -c ii ipc call altTab release"), { release = true })
hl.bind("Alt_R", hl.dsp.exec_cmd("quickshell -c ii ipc call altTab release"), { release = true })
hl.bind("ALT + Alt_L", hl.dsp.exec_cmd("quickshell -c ii ipc call altTab release"), { release = true })
hl.bind("ALT + Alt_R", hl.dsp.exec_cmd("quickshell -c ii ipc call altTab release"), { release = true })
hl.bind("ALT + Escape", hl.dsp.exec_cmd("quickshell -c ii ipc call altTab cancel"))

-- 4. Navegación de foco entre ventanas (Alt + Flechas)
hl.bind(mainMod .. " + left",  hl.dsp.focus({ direction = "left" }),  { description = "Navegación: Mover foco entre ventanas" })
hl.bind(mainMod .. " + right", hl.dsp.focus({ direction = "right" }))
hl.bind(mainMod .. " + up",    hl.dsp.focus({ direction = "up" }))
hl.bind(mainMod .. " + down",  hl.dsp.focus({ direction = "down" }))

-- 5. Mover ventanas (Control + Flechas en el layout y entre monitores)
hl.bind("CTRL + left",  hl.dsp.window.move({ direction = "left" }),  { repeating = true, description = "Navegación: Mover ventana (y entre monitores)" })
hl.bind("CTRL + right", hl.dsp.window.move({ direction = "right" }), { repeating = true })
hl.bind("CTRL + up",    hl.dsp.window.move({ direction = "up" }),    { repeating = true })
hl.bind("CTRL + down",  hl.dsp.window.move({ direction = "down" }),  { repeating = true })

-- 6. Espacios de trabajo (Workspaces 1 al 10)
for i = 1, 10 do
    local key = i % 10 -- 10 maps to key 0
    local desc_focus = (i == 1) and "Espacios de trabajo: Cambiar al espacio de trabajo" or nil
    local desc_move  = (i == 1) and "Espacios de trabajo: Mover ventana al espacio de trabajo" or nil
    hl.bind(mainMod .. " + " .. key, hl.dsp.focus({ workspace = i }), desc_focus and { description = desc_focus } or nil)
    hl.bind(mainMod .. " + SHIFT + " .. key, hl.dsp.window.move({ workspace = i }), desc_move and { description = desc_move } or nil)
end

-- Espacio de trabajo especial / Scratchpad (Magic)
hl.bind(mainMod .. " + S",         hl.dsp.workspace.toggle_special("magic"), { description = "Espacios de trabajo: Mostrar/Ocultar espacio especial (Magic)" })
hl.bind(mainMod .. " + SHIFT + S", hl.dsp.window.move({ workspace = "special:magic" }), { description = "Espacios de trabajo: Enviar ventana al espacio especial (Magic)" })

-- Scroll entre espacios de trabajo con Alt + rueda de ratón
hl.bind(mainMod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }), { description = "Espacios de trabajo: Espacio de trabajo siguiente" })
hl.bind(mainMod .. " + mouse_up",   hl.dsp.focus({ workspace = "e-1" }), { description = "Espacios de trabajo: Espacio de trabajo anterior" })

-- Arrastrar / Redimensionar ventanas con Alt + ratón
hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag(),   { mouse = true, description = "Ventana: Arrastrar ventana flotante" })
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true, description = "Ventana: Redimensionar ventana flotante" })

-- 7. Sistema y entorno Quickshell
hl.bind("SUPER + A", hl.dsp.exec_cmd("quickshell -c ii ipc call sidebarRight toggle"), { description = "Sistema: Panel lateral / Ajustes rápidos" })
hl.bind("SUPER + I", hl.dsp.exec_cmd("qs -p " .. os.getenv("HOME") .. "/.config/quickshell/ii/settings.qml"), { description = "Sistema: Configuración del sistema" })
hl.bind("SUPER + ALT + A", hl.dsp.exec_cmd(os.getenv("HOME") .. "/.config/hypr/scripts/open-autostart.sh"), { description = "Sistema: Gestor de inicio automático (Autostart)" })
hl.bind("SUPER + L", hl.dsp.exec_cmd("quickshell -c ii ipc call lock activate"), { description = "Sistema: Bloquear pantalla" })
hl.bind("Print", hl.dsp.exec_cmd("quickshell -c ii ipc call region screenshot"), { description = "Sistema: Captura de pantalla por región" })
hl.bind("SUPER + SHIFT + S", hl.dsp.exec_cmd("quickshell -c ii ipc call region screenshot"))
hl.bind(mainMod .. " + M", hl.dsp.exec_cmd("command -v hyprshutdown >/dev/null 2>&1 && hyprshutdown || hyprctl dispatch 'hl.dsp.exit()'"), { description = "Sistema: Menú de apagado / Salir" })

-- 8. Teclas multimedia y brillo
hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), { locked = true, repeating = true, description = "Multimedia: Subir volumen" })
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"),      { locked = true, repeating = true, description = "Multimedia: Bajar volumen" })
hl.bind("XF86AudioMute",        hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"),     { locked = true, repeating = true, description = "Multimedia: Silenciar audio" })
hl.bind("XF86AudioMicMute",     hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"),   { locked = true, repeating = true, description = "Multimedia: Silenciar micrófono" })
hl.bind("XF86MonBrightnessUp",  hl.dsp.exec_cmd("quickshell -c ii ipc call brightness increment"), { locked = true, repeating = true, description = "Multimedia: Subir brillo de pantalla" })
hl.bind("XF86MonBrightnessDown",hl.dsp.exec_cmd("quickshell -c ii ipc call brightness decrement"), { locked = true, repeating = true, description = "Multimedia: Bajar brillo de pantalla" })
hl.bind("XF86AudioNext",  hl.dsp.exec_cmd("playerctl next"),       { locked = true, description = "Multimedia: Pista siguiente" })
hl.bind("XF86AudioPause", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPlay",  hl.dsp.exec_cmd("playerctl play-pause"), { locked = true, description = "Multimedia: Reproducir / Pausar" })
hl.bind("XF86AudioPrev",  hl.dsp.exec_cmd("playerctl previous"),   { locked = true, description = "Multimedia: Pista anterior" })
hl.bind("XF86AudioStop",  hl.dsp.exec_cmd("playerctl stop"),       { locked = true, description = "Multimedia: Detener reproducción" })
