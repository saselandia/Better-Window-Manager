-- Luz nocturna sin hyprsunset (scripts/nightlight.py): el shader existe sólo mientras está
-- encendida. `hyprctl reload` vuelve a leer este archivo y lo conserva; con hyprsunset no hay shader.
local nightlight_shader = os.getenv("HOME") .. "/.local/state/bwm/nightlight.frag"
local shader_file = io.open(nightlight_shader, "r")
if shader_file then
    shader_file:close()
    hl.config({ decoration = { screen_shader = nightlight_shader } })
end
