-- Animaciones de Breeze (Kde plasma) — fuente única de verdad (R7, KWin 6.7.5).
-- Lo carga modules/appearance.lua sólo con la skin plasma.
-- Unidades verificadas en libhyprutils 0.56.2: speed = duración en décimas de segundo (1.0 = 100 ms),
-- directamente proporcional a AnimationDurationFactor (factor = 0 desactiva las animaciones).

local state_path = (os.getenv("XDG_STATE_HOME") or (os.getenv("HOME") .. "/.local/state")) .. "/bwm/plasma/kwin.lua"
local ok, settings = pcall(dofile, state_path)
local k = ok and type(settings) == "table" and settings or {}

local factor = k.animationFactor
if factor == nil then factor = 1 end

hl.config({
    animations = { enabled = factor > 0 },
})

if factor <= 0 then
    return k
end

local function ds(ms)
    return math.max(0.1, (ms / 100.0) * factor)
end

-- Curvas exactas de KWin 6.7.5:
-- OutCubic: 1 - (1-t)^3  <-> bezier(1/3, 1, 2/3, 1) (idéntica, error 0)
-- InCubic:  t^3          <-> bezier(1/3, 0, 2/3, 0) (idéntica, error 0)
-- Linear:   t            <-> bezier(0, 0, 1, 1)
-- OutQuart: 1 - (1-t)^4  <-> bezier(0.25, 1, 0.5, 1)
-- Slide:    SpringMotion(300 / factor, dampingRatio=1.1) -> muelle nativo de Hyprland
local slide_stiffness = math.max(1.0, 300.0 / factor)
local slide_dampening = 2.0 * math.sqrt(slide_stiffness) * 1.1

hl.curve("kwin_out_cubic", { type = "bezier", points = { { 0.3333, 1.0 }, { 0.6667, 1.0 } } })
hl.curve("kwin_in_cubic",  { type = "bezier", points = { { 0.3333, 0.0 }, { 0.6667, 0.0 } } })
hl.curve("kwin_linear",    { type = "bezier", points = { { 0.0, 0.0 },    { 1.0, 1.0 } } })
hl.curve("kwin_out_quart", { type = "bezier", points = { { 0.25, 1.0 },   { 0.5, 1.0 } } })
hl.curve("kwin_slide",     { type = "spring", stiffness = slide_stiffness, dampening = slide_dampening, mass = 1 })

-- Abrir / cerrar ventana: plugin «scale» de KWin 6.7.5 (200 ms, InScale/OutScale = 0.8, OutCubic / InCubic)
local scale_on = k.scaleEnabled ~= false
local scale_ms = (k.scaleDuration and k.scaleDuration > 0) and k.scaleDuration or 200
local in_pct   = math.max(10, math.min(100, math.floor(((k.scaleIn or 0.8) * 100) + 0.5)))
local out_pct  = math.max(10, math.min(100, math.floor(((k.scaleOut or 0.8) * 100) + 0.5)))
local in_style  = string.format("popin %d%%", in_pct)
local out_style = string.format("popin %d%%", out_pct)

hl.animation({ leaf = "windows",       enabled = scale_on, speed = ds(scale_ms), bezier = "kwin_out_cubic", style = in_style })
hl.animation({ leaf = "windowsIn",     enabled = scale_on, speed = ds(scale_ms), bezier = "kwin_out_cubic", style = in_style })
hl.animation({ leaf = "windowsOut",    enabled = scale_on, speed = ds(scale_ms), bezier = "kwin_in_cubic",  style = out_style })
hl.animation({ leaf = "fade",          enabled = scale_on, speed = ds(scale_ms), bezier = "kwin_out_cubic" })
hl.animation({ leaf = "fadeIn",        enabled = scale_on, speed = ds(scale_ms), bezier = "kwin_out_cubic" })
hl.animation({ leaf = "fadeOut",       enabled = scale_on, speed = ds(scale_ms), bezier = "kwin_in_cubic" })

-- Maximizar / restaurar / mover / redimensionar: plugin «maximize» / «fullscreen» Stretch (250 ms, OutCubic)
local move_on = k.maximizeEnabled ~= false
hl.animation({ leaf = "windowsMove",   enabled = move_on,  speed = ds(250),      bezier = "kwin_out_cubic" })
hl.animation({ leaf = "border",        enabled = false,    speed = 1,            bezier = "kwin_linear" })

-- Capas y ventanas emergentes: «slidingpopups» (200 ms, OutCubic) y «fadingpopups» (150 ms Linear / 600 ms OutQuart)
local layers_on = k.slidingPopupsEnabled ~= false
local fade_popups_on = k.fadingPopupsEnabled ~= false
hl.animation({ leaf = "layers",        enabled = layers_on,      speed = ds(200), bezier = "kwin_out_cubic", style = "fade" })
hl.animation({ leaf = "layersIn",      enabled = layers_on,      speed = ds(200), bezier = "kwin_out_cubic", style = "fade" })
hl.animation({ leaf = "layersOut",     enabled = layers_on,      speed = ds(200), bezier = "kwin_out_cubic", style = "fade" })
hl.animation({ leaf = "fadeLayersIn",  enabled = fade_popups_on, speed = ds(150), bezier = "kwin_linear" })
hl.animation({ leaf = "fadeLayersOut", enabled = fade_popups_on, speed = ds(600), bezier = "kwin_out_quart" })

-- Cambio de escritorio virtual: plugin «slide» de KWin 6.7.5 (SpringMotion nativo, estilo slide)
local slide_on = k.slideEnabled ~= false
hl.animation({ leaf = "workspaces",    enabled = slide_on, speed = 1, spring = "kwin_slide", style = "slide" })
hl.animation({ leaf = "workspacesIn",  enabled = slide_on, speed = 1, spring = "kwin_slide", style = "slide" })
hl.animation({ leaf = "workspacesOut", enabled = slide_on, speed = 1, spring = "kwin_slide", style = "slide" })

-- Workspace especial (Magic, extensión común de BWM; no tiene efecto propio en KWin)
hl.animation({ leaf = "specialWorkspace",    enabled = true, speed = ds(250), bezier = "kwin_out_cubic", style = "slidevert" })
hl.animation({ leaf = "specialWorkspaceIn",  enabled = true, speed = ds(250), bezier = "kwin_out_cubic", style = "slidevert" })
hl.animation({ leaf = "specialWorkspaceOut", enabled = true, speed = ds(250), bezier = "kwin_out_cubic", style = "slidevert" })

return k
