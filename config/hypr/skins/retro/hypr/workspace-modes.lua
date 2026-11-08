-- -----------------------------------------------------
-- Modo de cada workspace de Retro: mosaico (dwindle), desplazamiento (scrolling) o flotante, como en
-- Omarchy 4.5. Port de default/hypr/workspace-modes.lua y workspace-layouts.lua de basecamp/omarchy
-- (quattro 60bf28ee, MIT). Lo carga modules/appearance.lua sólo en Retro.
--
-- Cambios de BWM:
--  * `o` no existe en BWM: se crea aquí sólo con `o.workspace_mode`, el que llaman los archivos que
--    guarda omarchy-hyprland-workspace-layout-toggle en ~/.local/state/omarchy/workspace-layouts
--    (mismo formato que Omarchy, así que los de Omarchy valen tal cual).
--  * Barras de título con el hyprbars de BWM (hyprbars-plasma.so, el de Breeze) en vez de
--    omarchy-hyprland-titlebars: los dos se registran como «hyprbars» y no pueden convivir. El de BWM
--    tiene workspace_tag y %WINDOW% como el de Omarchy, y además no pone barra a las apps que traen
--    la suya (CSD). Se carga con `hyprctl plugin load` la primera vez que algo flota (nunca se descarga).
--  * Sin o.floating_apps: se excluyen de la regla de apertura las apps flotantes de BWM con tamaño
--    propio (rules.lua). El resto de reglas flotantes de BWM no fijan tamaño y toman el del modo.
--  * El modo vidrio de BWM (~/.local/state/bwm/glass) hace de «glassy».
--  * Minimizar de la barra: omarchy-hyprland-window-minimize de BWM (workspace 99; sólo con el dock).
-- -----------------------------------------------------

local HOME = os.getenv("HOME") or ""
local STATE_HOME = os.getenv("XDG_STATE_HOME")
if not STATE_HOME or STATE_HOME == "" then
    STATE_HOME = HOME .. "/.local/state"
end

local FLOATED_TAG = "omarchy-mode-floated"
local WORKSPACE_TAG = "omarchy-floating-workspace"
local OPENED_TAG = "omarchy-mode-opened"
local OPEN_RULE = "omarchy-floating-open-"
local LAST_WORKSPACE = 2147483647
local TITLEBARS = HOME .. "/.config/hypr/plugins/hyprbars-plasma.so"
local SHIMS = HOME .. "/.config/hypr/scripts/omarchy-shims"

-- Apps flotantes de BWM con tamaño propio (rules.lua): conservan el suyo
local OWN_SIZE = { class = { "^org\\.omarchy\\.terminal$", "^org\\.omarchy\\.about$", "hyprland-run" }, title = {} }

local M = {}

local modes = {}
local default_mode = nil
local watching = false
local floating_ready = false
local set_up_floating
local cascade = 0
local open_rules = 0
local window_rules = 0

local function file_exists(path)
    local file = io.open(path, "r")
    if file then
        file:close()
        return true
    end
    return false
end

-- o.window de Omarchy: una regla de ventana con nombre propio
local function window_rule(match, props)
    window_rules = window_rules + 1
    props.name = "bwm-floating-workspace-" .. window_rules
    props.match = match
    hl.window_rule(props)
end

local function set_floating(window, floating)
    hl.dispatch(hl.dsp.window.float({ action = floating and "on" or "off", window = window }))
end

local function set_claimed(window, claimed)
    hl.dispatch(hl.dsp.window.tag({ tag = (claimed and "+" or "-") .. FLOATED_TAG, window = window }))
end

local function set_on_floating_workspace(window, on)
    hl.dispatch(hl.dsp.window.tag({ tag = (on and "+" or "-") .. WORKSPACE_TAG, window = window }))
end

local function claimed()
    local addresses = {}
    for _, window in ipairs(hl.get_windows({ tag = FLOATED_TAG })) do
        addresses[window.address] = true
    end
    return addresses
end

-- Los workspaces especiales (scratchpad, minimizadas) y con nombre (id negativo) se dejan como estén,
-- igual que el 99 de las minimizadas de BWM.
local function floating_workspace(id)
    id = tonumber(id)
    if not id or id < 1 or id == 99 then
        return false
    end
    local mode = modes[tostring(id)]
    if mode then
        return mode == "floating"
    end
    return default_mode == "floating"
end

local function anything_floats()
    if default_mode == "floating" then
        return true
    end
    for _, mode in pairs(modes) do
        if mode == "floating" then
            return true
        end
    end
    return false
end

-- Tamaño cómodo, en el centro de su monitor y escalonada respecto a la anterior
local function place(window)
    local monitor = window.monitor
    if not monitor or not monitor.width then
        return
    end

    local width = math.floor(monitor.width / monitor.scale)
    local height = math.floor(monitor.height / monitor.scale)
    if (monitor.transform or 0) % 2 == 1 then
        width, height = height, width
    end

    local reserved = monitor.reserved or {}
    width = width - (reserved.left or 0) - (reserved.right or 0)
    height = height - (reserved.top or 0) - (reserved.bottom or 0)

    hl.dispatch(hl.dsp.window.resize({
        x = math.min(1100, math.floor(width * 0.64)),
        y = math.min(760, math.floor(height * 0.68)),
        relative = false,
        window = window,
    }))
    hl.dispatch(hl.dsp.window.center({ window = window }))

    cascade = (cascade + 1) % 5
    hl.dispatch(hl.dsp.window.move({ x = cascade * 24 - 48, y = cascade * 24 - 48, relative = true, window = window }))
end

-- Una ventana que ya flotaba por su cuenta queda sin reclamar (sigue flotando al salir del modo);
-- una a pantalla completa, como está. Se reclaman todas antes de hacer flotar ninguna: hacer flotar a
-- un miembro de un grupo hace flotar al resto.
-- La etiqueta de la regla de apertura (con «*» por ser de regla) dice que la hizo flotar el modo
local function opened_by_mode(window)
    for _, tag in ipairs(window.tags or {}) do
        if tag == OPENED_TAG or tag == OPENED_TAG .. "*" then
            return true
        end
    end
    return false
end

local function float_for_mode(windows)
    local claiming = {}
    local mine = claimed()
    for _, window in ipairs(windows) do
        set_on_floating_workspace(window, true)
        -- BWM: algunas apps (Firefox, Electron) reciben las etiquetas de regla después de abrirse, así que
        -- claim_opened no las ve; se reclaman aquí para que vuelvan al mosaico al acabar el modo
        if window.floating and opened_by_mode(window) and not mine[window.address] then
            set_claimed(window, true)
        end
        if not window.floating and (window.fullscreen or 0) == 0 then
            set_claimed(window, true)
            table.insert(claiming, window)
        end
    end
    for _, window in ipairs(claiming) do
        set_floating(window, true)
        place(window)
    end
end

-- Una fijada (pin) no se pasa a mosaico: también la desfijaría.
local function tile_for_mode(window, mine)
    set_on_floating_workspace(window, false)
    if not mine[window.address] or window.pinned then
        return
    end
    set_claimed(window, false)
    set_floating(window, false)
end

local function floating_ranges()
    local ranges = {}
    if default_mode == "floating" then
        local tiled = { 99 }
        for id, mode in pairs(modes) do
            local n = tonumber(id)
            if n and n >= 1 and mode ~= "floating" then
                table.insert(tiled, n)
            end
        end
        table.sort(tiled)
        local from = 1
        for _, n in ipairs(tiled) do
            if n > from then
                table.insert(ranges, { from, n - 1 })
            end
            from = math.max(from, n + 1)
        end
        table.insert(ranges, { from, LAST_WORKSPACE })
    else
        for id, mode in pairs(modes) do
            local n = tonumber(id)
            if n and n >= 1 and n ~= 99 and mode == "floating" then
                table.insert(ranges, { n, n })
            end
        end
        table.sort(ranges, function(a, b) return a[1] < b[1] end)
    end
    return ranges
end

local OPEN_WIDTH = "min(1100,monitor_w*0.64)"
local OPEN_HEIGHT = "min(760,monitor_h*0.68)"

local function open_position()
    local step = cascade * 24 - 48
    return string.format("(monitor_w-%s)/2+(%d) (monitor_h-%s)/2+(%d)", OPEN_WIDTH, step, OPEN_HEIGHT, step)
end

local function not_floating_on_their_own(match)
    for _, key in ipairs({ "class", "title" }) do
        local patterns = OWN_SIZE[key]
        if #patterns > 0 then
            local alternatives = {}
            for _, pattern in ipairs(patterns) do
                table.insert(alternatives, "(?:" .. pattern .. ")")
            end
            match[key] = "negative:" .. table.concat(alternatives, "|")
        end
    end
    return match
end

-- Una ventana que se abre en un workspace flotante flota desde su primer fotograma, al tamaño del
-- modo; los diálogos modales y las apps flotantes con tamaño propio se dejan a lo suyo.
local function sync_open_rules()
    local ranges = floating_ranges()
    for i, range in ipairs(ranges) do
        hl.window_rule({
            name = OPEN_RULE .. i,
            enabled = true,
            match = not_floating_on_their_own({ workspace = string.format("r[%d-%d]", range[1], range[2]), modal = false }),
            float = true,
            size = OPEN_WIDTH .. " " .. OPEN_HEIGHT,
            move = open_position(),
            tag = "+" .. OPENED_TAG,
        })
    end
    for i = #ranges + 1, open_rules do
        hl.window_rule({ name = OPEN_RULE .. i, enabled = false })
    end
    open_rules = math.max(open_rules, #ranges)
end

-- La etiqueta de una regla se va con la regla: la ventana que la regla hizo flotar se reclama al
-- abrirse, para volver a mosaico al acabar el modo.
local function claim_opened(window)
    if opened_by_mode(window) then
        set_claimed(window, true)
        cascade = (cascade + 1) % 5
        sync_open_rules()
    end
end

-- Una maximizada tiene el workspace para ella hasta que se abre otra: vuelve a su tamaño.
local function unmaximize_others(window)
    local id = window.workspace and window.workspace.id
    if not floating_workspace(id) then
        return
    end
    for _, other in ipairs(hl.get_workspace_windows(tostring(id))) do
        if other.address ~= window.address and (other.fullscreen or 0) == 1 then
            hl.dispatch(hl.dsp.window.fullscreen({ mode = "maximized", action = "unset", window = other }))
        end
    end
end

local function arrange(windows, workspace)
    local floating = {}
    local mine = claimed()
    for _, window in ipairs(windows) do
        local id = tonumber(workspace and workspace.id or (window.workspace and window.workspace.id))
        if id and id >= 1 and id ~= 99 then
            if floating_workspace(id) then
                table.insert(floating, window)
            else
                tile_for_mode(window, mine)
            end
        end
    end
    float_for_mode(floating)
end

-- Las ventanas se superponen y se colocan con el puntero: clic para enfocar en un workspace
-- flotante; el resto conserva el ajuste del usuario.
local input = {}

local function update_input()
    local workspace = hl.get_active_workspace()
    local active = workspace ~= nil and floating_workspace(workspace.id)
    if active == input.floating then
        return
    end
    input.floating = active
    hl.config({ input = { follow_mouse = active and 0 or input.follow_mouse } })
end

local function watch()
    if watching then
        return
    end
    watching = true
    input.follow_mouse = hl.get_config("input.follow_mouse")

    hl.on("window.open", function(window)
        claim_opened(window)
        unmaximize_others(window)
        arrange({ window })
    end)

    -- El movimiento aún se está aplicando cuando llega el evento: cambiar la flotación debajo lo pierde
    hl.on("window.move_to_workspace", function(window, workspace)
        hl.timer(function()
            arrange({ window }, workspace)
        end, { type = "oneshot", timeout = 1 })
    end)

    hl.on("window.fullscreen", function(window)
        hl.timer(function()
            arrange({ window })
        end, { type = "oneshot", timeout = 1 })
    end)

    hl.on("workspace.active", update_input)
    hl.on("monitor.focused", update_input)
end

o = o or {}

function o.workspace_mode(spec)
    watch()

    if spec.default then
        default_mode = spec.default
        if spec.default ~= "floating" then
            hl.config({ general = { layout = spec.default } })
        end
        sync_open_rules()
        if anything_floats() then
            set_up_floating()
        end
        return
    end

    local workspace = tostring(spec.workspace)
    -- Flotar conserva el layout en mosaico que tuviera el workspace
    if spec.mode ~= "floating" then
        hl.workspace_rule({ workspace = workspace, layout = spec.mode })
    end
    modes[workspace] = spec.mode

    if anything_floats() then
        set_up_floating()
    end

    arrange(hl.get_workspace_windows(workspace))
    sync_open_rules()
    update_input()
end

-- Colores de la barra: los del tema de Omarchy activo (lighter_background, o selection si coincide
-- con el fondo, como Omarchy)
local function theme_colors()
    local colors = {}
    local file = io.open(HOME .. "/.local/state/omarchy/current/theme/colors.toml", "r")
    if file then
        for line in file:lines() do
            local key, value = line:match('^%s*([%w_]+)%s*=%s*"#(%x%x%x%x%x%x)"')
            if key then
                colors[key] = "rgb(" .. value .. ")"
            end
        end
        file:close()
    end
    local background = colors.background or "rgb(1a1b26)"
    local titlebar = colors.lighter_background
    if not titlebar or titlebar == background then
        titlebar = colors.selection or background
    end
    return {
        background = background,
        foreground = colors.foreground or "rgb(c0caf5)",
        titlebar = titlebar,
    }
end

local function titlebars_loaded()
    for _, plugin in ipairs(hl.get_loaded_plugins and hl.get_loaded_plugins() or {}) do
        if plugin.name == "hyprbars" then
            return true
        end
    end
    return false
end

-- Sin el plugin cargado se carga una vez (fuera del proceso de la configuración, como autostart.sh);
-- al cargarse recarga la configuración y esta pasada pone sus opciones.
local function titlebars()
    if not file_exists(TITLEBARS) then
        return
    end
    if not titlebars_loaded() then
        -- Una sola carga aunque varias recargas seguidas lleguen aquí antes de que acabe
        os.execute("(sleep 0.3; flock -n \"${XDG_RUNTIME_DIR:-/tmp}/bwm-hyprbars-load.lock\" sh -c "
            .. "'hyprctl plugin list | grep -q \"Plugin hyprbars\" || hyprctl plugin load \"" .. TITLEBARS .. "\"') >/dev/null 2>&1 &")
        return
    end
    if not (hl.plugin and hl.plugin.hyprbars) then
        return
    end

    local colors = theme_colors()
    local window = [[window = "address:%WINDOW%"]]
    local maximize = "hyprctl dispatch 'hl.dsp.window.fullscreen({ mode = \"maximized\", action = \"toggle\", " .. window .. " })'"

    -- Opciones que sólo tiene el plugin nuevo (las del cargado antes de actualizarlo darían error)
    local function plugin_has(option)
        return hl.get_config and hl.get_config("plugin:hyprbars:" .. option) ~= nil
    end

    -- Un hyprbars cargado de antes de esta versión convertía en arrastre de la ventana cualquier
    -- pulsación arriba de una ventana sin barra (las pestañas de un navegador): mejor sin barras
    -- hasta volver a iniciar sesión, que es cuando se carga el nuevo (nunca se recarga en caliente).
    if not plugin_has("workspace_tag") or not plugin_has("button_rounding") then
        return
    end

    hl.config({
        plugin = {
            hyprbars = {
                enabled = true,
                bar_text_weight = plugin_has("bar_text_weight") and "normal" or nil,
                button_rounding = plugin_has("button_rounding") and 0 or nil,
                workspace_tag = WORKSPACE_TAG,
                snap = plugin_has("snap") and false or nil,
                bar_height = 30,
                bar_color = colors.titlebar,
                inactive_bar_color = colors.titlebar,
                ["col.text"] = colors.foreground,
                ["col.inactive_text"] = colors.foreground,
                bar_text_font = "monospace",
                bar_text_size = 12,
                bar_text_align = "left",
                bar_buttons_alignment = "right",
                bar_part_of_window = true,
                bar_precedence_over_border = true,
                bar_padding = 10,
                bar_button_padding = 8,
                icon_on_hover = false,
                inactive_button_color = colors.titlebar,
                on_double_click = maximize,
            },
        },
    })

    if hl.plugin.hyprbars.add_button then
        for _, button in ipairs({
            { icon = "×", action = "hyprctl dispatch 'hl.dsp.window.close({ " .. window .. " })'" },
            { icon = "□", action = maximize },
            -- Como en Omarchy, sólo con el dock encendido, que es quien las devuelve (workspace 99 de BWM)
            { icon = "−", action = "PATH=" .. SHIMS .. ":$PATH " .. SHIMS .. "/omarchy-hyprland-window-minimize %WINDOW%" },
        }) do
            hl.plugin.hyprbars.add_button({
                bg_color = colors.titlebar,
                fg_color = colors.foreground,
                size = 20,
                icon = button.icon,
                action = button.action,
            })
        end
    end
end

-- Con todos los modos guardados leídos, pone en orden las ventanas abiertas. Una recarga empieza de
-- cero aquí pero no para las ventanas: si el predeterminado deja de flotar hay que devolver lo que hizo
-- flotar aunque ya nada nombre esos workspaces.
function M.apply()
    local leftovers = #hl.get_windows({ tag = FLOATED_TAG }) > 0 or #hl.get_windows({ tag = WORKSPACE_TAG }) > 0
    if anything_floats() or leftovers then
        watch()
    end
    if watching then
        arrange(hl.get_windows())
        update_input()
    end
    if anything_floats() then
        set_up_floating()
    end
end

-- Lo que necesita un workspace flotante además del resto: sombras, ventanas opacas y barras.
set_up_floating = function()
    if floating_ready then
        return
    end
    floating_ready = true

    if not hl.get_config("decoration.shadow.enabled") then
        hl.config({ decoration = { shadow = { enabled = true, range = 16, render_power = 3, color = "rgba(00000035)" } } })
        window_rule({ class = ".*" }, { no_shadow = true })
        window_rule({ tag = WORKSPACE_TAG }, { no_shadow = false })
    end

    if not file_exists(STATE_HOME .. "/bwm/glass") then
        window_rule({ tag = WORKSPACE_TAG }, { opacity = "1.0 override 1.0 override" })
    end

    titlebars()
end

-- Modos guardados (omarchy-hyprland-workspace-layout-toggle/-default): default.lua primero y luego
-- uno por workspace, en el formato de Omarchy
local LAYOUTS = STATE_HOME .. "/omarchy/workspace-layouts"

local function load_saved(path)
    local chunk = loadfile(path, "t", setmetatable({ o = o }, { __index = _G }))
    if not chunk then
        return
    end
    local ok, err = pcall(chunk)
    if not ok then
        local msg = tostring(err):gsub("['\"`$\\]", "")
        os.execute("notify-send -a BWM 'Modo del workspace' '" .. msg .. "' &")
    end
end

load_saved(LAYOUTS .. "/default.lua")
local listing = io.popen("ls -1 '" .. LAYOUTS .. "' 2>/dev/null")
if listing then
    for name in listing:lines() do
        if name:match("^%d+%.lua$") then
            load_saved(LAYOUTS .. "/" .. name)
        end
    end
    listing:close()
end

M.apply()

return M
