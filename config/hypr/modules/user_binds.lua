-- =============================================================================
-- ATAJOS DE TECLADO CONFIGURADOS (HYPRLAND LUA)
-- Archivo gestionado automáticamente por keybinds-manager.py
-- =============================================================================

local terminal    = "kitty"
local fileManager = "nautilus --new-window"
local menu        = "quickshell -c ii ipc call search toggle || rofi -show drun"

local ok_theme, active_theme = pcall(require, "modules.theme")
local is_plasma = ok_theme and (active_theme.name == "plasma" or (active_theme.name and string.find(active_theme.name, "plasma") ~= nil))
local fullscreen_mode = is_plasma and 1 or 0
local active_skin = ok_theme and active_theme.name or ""

-- [General]
hl.bind("ALT + A", hl.dsp.exec_cmd("quickshell -c ii ipc call cheatsheet toggle"), { description = "General: Guía de atajos (Cheatsheet)" })
-- [Lanzadores]
hl.bind("CTRL + RETURN", hl.dsp.exec_cmd("kitty"), { description = "Lanzadores: Abrir terminal (Kitty)" })
hl.bind("SUPER + SUPER_L", hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/app-launcher.sh"), { description = "Lanzadores: Menú de aplicaciones / Búsqueda", release = true })
hl.bind("ALT + E", hl.dsp.exec_cmd("nautilus --new-window"), { description = "Lanzadores: Explorador de archivos alternativo (Alt+E)" })
hl.bind("ALT + W", hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/wallpaper-picker.sh"), { description = "Lanzadores: Selector de fondos de pantalla" })
-- [Ventanas]
hl.bind("ALT + X", hl.dsp.window.close(), { description = "Ventanas: Cerrar ventana activa" })
hl.bind("ALT + Q", hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/toggle-float-persistent.py"), { description = "Ventanas: Recordar regla flotante persistente" })
hl.bind("ALT + J", hl.dsp.layout("togglesplit"), { description = "Ventanas: Alternar división horizontal/vertical (Split)" })
hl.bind("ALT + RETURN", hl.dsp.window.fullscreen({ mode = fullscreen_mode, action = "toggle" }), { description = "Ventanas: Alternar pantalla completa" })
hl.bind("SUPER + RETURN", hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/toggle-single-window-aspect.sh"), { description = "Ventanas: Alternar proporción cuadrada para ventana única (Omarchy)" })
hl.bind("ALT + TAB", hl.dsp.exec_cmd("quickshell -c ii ipc call altTab next"), { description = "Ventanas: Selector visual de ventanas (Alt+Tab)", repeating = true })
-- [Navegación]
hl.bind("ALT + left", hl.dsp.focus({ direction = "left" }), { description = "Navegación: Mover foco a la izquierda" })
hl.bind("ALT + right", hl.dsp.focus({ direction = "right" }), { description = "Navegación: Mover foco a la derecha" })
hl.bind("ALT + up", hl.dsp.focus({ direction = "up" }), { description = "Navegación: Mover foco hacia arriba" })
hl.bind("ALT + down", hl.dsp.focus({ direction = "down" }), { description = "Navegación: Mover foco hacia abajo" })
hl.bind((is_plasma and "SUPER + left" or "CTRL + left"), hl.dsp.window.move({ direction = "left" }), { description = "Navegación: Mover ventana a la izquierda", repeating = true })
hl.bind((is_plasma and "SUPER + right" or "CTRL + right"), hl.dsp.window.move({ direction = "right" }), { description = "Navegación: Mover ventana a la derecha", repeating = true })
hl.bind((is_plasma and "SUPER + up" or "CTRL + up"), hl.dsp.window.move({ direction = "up" }), { description = "Navegación: Mover ventana hacia arriba", repeating = true })
hl.bind((is_plasma and "SUPER + down" or "CTRL + down"), hl.dsp.window.move({ direction = "down" }), { description = "Navegación: Mover ventana hacia abajo", repeating = true })
-- [Espacios de trabajo]
hl.bind("ALT + S", hl.dsp.workspace.toggle_special("magic"), { description = "Espacios de trabajo: Mostrar / Ocultar espacio especial (Magic)" })
hl.bind("ALT + SHIFT + S", hl.dsp.window.move({ workspace = "special:magic" }), { description = "Espacios de trabajo: Enviar ventana al espacio especial (Magic)" })
-- [Sistema]
hl.bind("SUPER + A", hl.dsp.exec_cmd("quickshell -c ii ipc call sidebarRight toggle"), { description = "Sistema: Panel lateral / Ajustes rápidos" })
hl.bind("SUPER + I", hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/open-settings.sh"), { description = "Sistema: Configuración del sistema (Settings)" })
hl.bind("SUPER + ALT + A", hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/open-autostart.sh"), { description = "Sistema: Gestor de inicio automático (Autostart)" })
hl.bind("SUPER + L", hl.dsp.exec_cmd("quickshell -c ii ipc call lock activate"), { description = "Sistema: Bloquear pantalla" })
hl.bind("Print", hl.dsp.exec_cmd("quickshell -c ii ipc call region screenshot"), { description = "Sistema: Captura de pantalla por región (Print)" })
hl.bind("SUPER + SHIFT + S", hl.dsp.exec_cmd("quickshell -c ii ipc call region screenshot"), { description = "Sistema: Captura de pantalla alternativa (Super+Shift+S)" })
hl.bind("ALT + M", hl.dsp.exec_cmd("command -v hyprshutdown >/dev/null 2>&1 && hyprshutdown || hyprctl dispatch 'hl.dsp.exit()'"), { description = "Sistema: Menú de apagado / Salir de sesión" })
-- [Multimedia]
hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), { description = "Multimedia: Subir volumen", locked = true, repeating = true })
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"), { description = "Multimedia: Bajar volumen", locked = true, repeating = true })
hl.bind("XF86AudioMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"), { description = "Multimedia: Silenciar audio", locked = true })
hl.bind("XF86AudioMicMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"), { description = "Multimedia: Silenciar micrófono", locked = true })
hl.bind("XF86MonBrightnessUp", hl.dsp.exec_cmd("quickshell -c ii ipc call brightness increment"), { description = "Multimedia: Subir brillo de pantalla", locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("quickshell -c ii ipc call brightness decrement"), { description = "Multimedia: Bajar brillo de pantalla", locked = true, repeating = true })
hl.bind("XF86AudioPlay", hl.dsp.exec_cmd("playerctl play-pause"), { description = "Multimedia: Reproducir / Pausar", locked = true })
hl.bind("XF86AudioNext", hl.dsp.exec_cmd("playerctl next"), { description = "Multimedia: Pista siguiente", locked = true })
hl.bind("XF86AudioPrev", hl.dsp.exec_cmd("playerctl previous"), { description = "Multimedia: Pista anterior", locked = true })
hl.bind("XF86AudioStop", hl.dsp.exec_cmd("playerctl stop"), { description = "Multimedia: Detener reproducción", locked = true })
-- [Espacios de trabajo]
hl.bind("ALT + 1", hl.dsp.focus({ workspace = 1 }), { description = "Espacios de trabajo: Cambiar al espacio de trabajo 1" })
hl.bind("ALT + SHIFT + 1", hl.dsp.window.move({ workspace = 1 }), { description = "Espacios de trabajo: Mover ventana al espacio de trabajo 1" })
hl.bind("ALT + 2", hl.dsp.focus({ workspace = 2 }), { description = "Espacios de trabajo: Cambiar al espacio de trabajo 2" })
hl.bind("ALT + SHIFT + 2", hl.dsp.window.move({ workspace = 2 }), { description = "Espacios de trabajo: Mover ventana al espacio de trabajo 2" })
hl.bind("ALT + 3", hl.dsp.focus({ workspace = 3 }), { description = "Espacios de trabajo: Cambiar al espacio de trabajo 3" })
hl.bind("ALT + SHIFT + 3", hl.dsp.window.move({ workspace = 3 }), { description = "Espacios de trabajo: Mover ventana al espacio de trabajo 3" })
hl.bind("ALT + 4", hl.dsp.focus({ workspace = 4 }), { description = "Espacios de trabajo: Cambiar al espacio de trabajo 4" })
hl.bind("ALT + SHIFT + 4", hl.dsp.window.move({ workspace = 4 }), { description = "Espacios de trabajo: Mover ventana al espacio de trabajo 4" })
hl.bind("ALT + 5", hl.dsp.focus({ workspace = 5 }), { description = "Espacios de trabajo: Cambiar al espacio de trabajo 5" })
hl.bind("ALT + SHIFT + 5", hl.dsp.window.move({ workspace = 5 }), { description = "Espacios de trabajo: Mover ventana al espacio de trabajo 5" })
hl.bind("ALT + 6", hl.dsp.focus({ workspace = 6 }), { description = "Espacios de trabajo: Cambiar al espacio de trabajo 6" })
hl.bind("ALT + SHIFT + 6", hl.dsp.window.move({ workspace = 6 }), { description = "Espacios de trabajo: Mover ventana al espacio de trabajo 6" })
hl.bind("ALT + 7", hl.dsp.focus({ workspace = 7 }), { description = "Espacios de trabajo: Cambiar al espacio de trabajo 7" })
hl.bind("ALT + SHIFT + 7", hl.dsp.window.move({ workspace = 7 }), { description = "Espacios de trabajo: Mover ventana al espacio de trabajo 7" })
hl.bind("ALT + 8", hl.dsp.focus({ workspace = 8 }), { description = "Espacios de trabajo: Cambiar al espacio de trabajo 8" })
hl.bind("ALT + SHIFT + 8", hl.dsp.window.move({ workspace = 8 }), { description = "Espacios de trabajo: Mover ventana al espacio de trabajo 8" })
hl.bind("ALT + 9", hl.dsp.focus({ workspace = 9 }), { description = "Espacios de trabajo: Cambiar al espacio de trabajo 9" })
hl.bind("ALT + SHIFT + 9", hl.dsp.window.move({ workspace = 9 }), { description = "Espacios de trabajo: Mover ventana al espacio de trabajo 9" })
hl.bind("ALT + 0", hl.dsp.focus({ workspace = 10 }), { description = "Espacios de trabajo: Cambiar al espacio de trabajo 10" })
hl.bind("ALT + SHIFT + 0", hl.dsp.window.move({ workspace = 10 }), { description = "Espacios de trabajo: Mover ventana al espacio de trabajo 10" })
-- [Lanzadores]
hl.bind("ALT + T", hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/theme-picker.sh"), { description = "Lanzadores: Selector de estilos (BWM)" })
if active_skin == "retro" then hl.bind("ALT + R", hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/omarchy-shims/omarchy-theme-switcher"), { description = "Lanzadores: Galería 3D de temas Retro (Omarchy)" }) end
-- [Ventanas]
hl.bind((is_plasma and "CTRL + left" or "SUPER + left"), hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/quick-tile.py left"), { description = "Ventanas: Ajustar ventana a la izquierda (Quick Tile Left)" })
hl.bind((is_plasma and "CTRL + right" or "SUPER + right"), hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/quick-tile.py right"), { description = "Ventanas: Ajustar ventana a la derecha (Quick Tile Right)" })
hl.bind((is_plasma and "CTRL + up" or "SUPER + up"), hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/quick-tile.py top"), { description = "Ventanas: Maximizar ventana (Quick Tile Top)" })
hl.bind((is_plasma and "CTRL + down" or "SUPER + down"), hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/quick-tile.py bottom"), { description = "Ventanas: Restaurar / Ajustar abajo (Quick Tile Bottom)" })
hl.bind((is_plasma and "CTRL + ALT + left" or "SUPER + ALT + left"), hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/quick-tile.py top-left"), { description = "Ventanas: Ajustar esquina superior izquierda (Quick Tile)" })
hl.bind((is_plasma and "CTRL + ALT + right" or "SUPER + ALT + right"), hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/quick-tile.py top-right"), { description = "Ventanas: Ajustar esquina superior derecha (Quick Tile)" })
hl.bind((is_plasma and "CTRL + ALT + down" or "SUPER + ALT + down"), hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/quick-tile.py bottom-right"), { description = "Ventanas: Ajustar esquina inferior derecha (Quick Tile)" })
hl.bind((is_plasma and "CTRL + ALT + up" or "SUPER + ALT + up"), hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/quick-tile.py bottom-left"), { description = "Ventanas: Ajustar esquina inferior izquierda (Quick Tile)" })
-- [Lanzadores]
hl.bind("SUPER + V", hl.dsp.exec_cmd("omarchy-shell clipboard toggle"), { description = "Lanzadores: Historial del portapapeles" })
hl.bind("SUPER + period", hl.dsp.exec_cmd("omarchy-shell emojis toggle"), { description = "Lanzadores: Selector de emojis" })
hl.bind("SUPER + SPACE", hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/app-launcher.sh apps"), { description = "Lanzadores: Aplicaciones (cuadrícula Apps de Omarchy en Retro)" })
-- [Ventanas]
hl.bind("SUPER + M", hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/omarchy-shims/omarchy-hyprland-window-minimize"), { description = "Ventanas: Minimizar al dock (Omarchy, en workspaces sin mosaico)" })
-- [Lanzadores]
hl.bind("ALT + SPACE", hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/app-launcher.sh apps"), { description = "Lanzadores: Aplicaciones (Apps de Omarchy en Retro)" })
-- [General]
if active_skin == "default" then hl.bind("SUPER + G", hl.dsp.exec_cmd("quickshell -c ii ipc call overlay toggle"), { description = "General: Overlay de widgets (end-4)" }) end

-- Helper binds: allow Super+Alt for corner snaps in Plasma as well
if is_plasma then
    hl.bind("SUPER + ALT + left", hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/quick-tile.py top-left"), { description = "Ventanas: Ajustar esquina superior izquierda (Quick Tile)" })
    hl.bind("SUPER + ALT + right", hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/quick-tile.py top-right"), { description = "Ventanas: Ajustar esquina superior derecha (Quick Tile)" })
    hl.bind("SUPER + ALT + down", hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/quick-tile.py bottom-right"), { description = "Ventanas: Ajustar esquina inferior derecha (Quick Tile)" })
    hl.bind("SUPER + ALT + up", hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/quick-tile.py bottom-left"), { description = "Ventanas: Ajustar esquina inferior izquierda (Quick Tile)" })
end

-- Alt+Tab Helper Releases
hl.bind("ALT + SHIFT + TAB", hl.dsp.exec_cmd("quickshell -c ii ipc call altTab prev"), { repeating = true })
hl.bind("Alt_L", hl.dsp.exec_cmd("quickshell -c ii ipc call altTab release"), { release = true })
hl.bind("Alt_R", hl.dsp.exec_cmd("quickshell -c ii ipc call altTab release"), { release = true })
hl.bind("ALT + Alt_L", hl.dsp.exec_cmd("quickshell -c ii ipc call altTab release"), { release = true })
hl.bind("ALT + Alt_R", hl.dsp.exec_cmd("quickshell -c ii ipc call altTab release"), { release = true })
hl.bind("ALT + Escape", hl.dsp.exec_cmd("quickshell -c ii ipc call altTab cancel"))
hl.bind("ALT + grave", hl.dsp.exec_cmd("quickshell -c ii ipc call altTab nextApp"), { description = "Ventanas: Alternar entre ventanas de la misma aplicación (Alt+`)", repeating = true })
hl.bind("ALT + SHIFT + grave", hl.dsp.exec_cmd("quickshell -c ii ipc call altTab prevApp"), { repeating = true })
hl.bind("SUPER + BACKSPACE", hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/window-transparency.sh toggle-window"), { description = "Ventanas: Alternar transparencia de la ventana activa (Omarchy)" })

-- Mouse Window Gestures
hl.bind("ALT + mouse:272", hl.dsp.window.drag(), { mouse = true, description = "Ventanas: Arrastrar ventana flotante" })
hl.bind("ALT + mouse:273", hl.dsp.window.resize(), { mouse = true, description = "Ventanas: Redimensionar ventana flotante" })
hl.bind("ALT + mouse_down", hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/cycle-workspace.py next"), { description = "Espacios de trabajo: Espacio de trabajo siguiente" })
hl.bind("ALT + mouse_up",   hl.dsp.exec_cmd("/home/sasel/.config/hypr/scripts/cycle-workspace.py prev"), { description = "Espacios de trabajo: Espacio de trabajo anterior" })

return {}
