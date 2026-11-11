-- -----------------------------------------------------
-- Colocación de ventanas nuevas de Breeze (Kde plasma), como «Mínimo solapamiento» (Smart), la
-- política de KWin: una ventana nueva va al hueco libre del escritorio en vez de encima de otra.
-- La carga modules/appearance.lua sólo en esta skin.
--
-- Hyprland centra las ventanas flotantes; aquí, al abrirse, se busca la posición que menos tape a
-- las demás del mismo workspace. Si el centro está libre se queda en el centro (lo que haría
-- Hyprland); si no, la posición libre más arriba y a la izquierda, como KWin; sin hueco libre, la
-- que menos se solapa. Se respeta su tamaño (como KWin) y la barra de título Breeze (breezebars),
-- el margen y el hueco del bloque «traditional» de skins/plasma/skin.json.
-- -----------------------------------------------------

local EDGE_MARGIN = 10
local GAP = 10
local kwin = package.loaded["skins.plasma.hypr.kwin"] or {}

-- Ventanas con su sitio propio (reglas de modules/rules.lua) o colocadas por otro mecanismo
local KEEP_CLASSES = {
    "^org%.omarchy%.", "^omacalc$", "^hyprland%-run$", "^bwm%-", "^xdg%-desktop%-portal",
}
local KEEP_TITLES = { "^Open", "^Save", "^Select", "^Abrir", "^Guardar", "^Seleccionar" }

local function matches(value, patterns)
    value = value or ""
    for _, pattern in ipairs(patterns) do
        if value:find(pattern) then
            return true
        end
    end
    return false
end

-- Área útil del monitor en unidades lógicas, sin paneles ni el margen de la skin
local function work_area(monitor)
    local width = monitor.width / monitor.scale
    local height = monitor.height / monitor.scale
    if (monitor.transform or 0) % 2 == 1 then
        width, height = height, width
    end
    local reserved = monitor.reserved or {}
    local x = monitor.x + (reserved.left or 0) + EDGE_MARGIN
    local y = monitor.y + (reserved.top or 0) + EDGE_MARGIN
    return {
        x = x,
        y = y,
        w = width - (reserved.left or 0) - (reserved.right or 0) - 2 * EDGE_MARGIN,
        h = height - (reserved.top or 0) - (reserved.bottom or 0) - 2 * EDGE_MARGIN,
    }
end

-- F7: same committed frame as IPC/quick-tile, queried in-process without class heuristics.
local function borders(window)
    local zero = { left = 0, top = 0, right = 0, bottom = 0 }
    local query = hl.plugin and hl.plugin.breezebars and hl.plugin.breezebars.decoration
    if not query then return zero end
    local ok, state = pcall(query, window.address, window.pid)
    if not ok or not state then return zero end
    if state.ready == false then return nil end
    if not state.visible then return zero end
    for side in pairs(zero) do
        local n = state.borders and state.borders[side]
        if type(n) == "number" and n == n and n < math.huge then zero[side] = math.max(0, n) end
    end
    return zero
end
local function clamp(value, low, high) return math.max(low, math.min(value, high)) end
local function frame(window, border)
    return { x = window.at.x - border.left, y = window.at.y - border.top,
             w = window.size.x + border.left + border.right, h = window.size.y + border.top + border.bottom }
end

local function overlap(a, b)
    local w = math.min(a.x + a.w, b.x + b.w + GAP) - math.max(a.x, b.x - GAP)
    local h = math.min(a.y + a.h, b.y + b.h + GAP) - math.max(a.y, b.y - GAP)
    if w <= 0 or h <= 0 then
        return 0
    end
    return w * h
end

local function total_overlap(rect, others)
    local sum = 0
    for _, other in ipairs(others) do
        sum = sum + overlap(rect, other)
    end
    return sum
end

local function best_position(size, area, others)
    local function clamp(value, low, high)
        return math.max(low, math.min(value, high))
    end
    local max_x, max_y = area.x + area.w - size.w, area.y + area.h - size.h

    local center = {
        x = math.floor(area.x + (area.w - size.w) / 2),
        y = math.floor(area.y + (area.h - size.h) / 2),
        w = size.w,
        h = size.h,
    }
    if total_overlap(center, others) == 0 then
        return center
    end

    -- Candidatas como KWin: los bordes del área y los de cada ventana (a su lado, con el hueco)
    local xs, ys = { area.x, max_x }, { area.y, max_y }
    for _, other in ipairs(others) do
        table.insert(xs, other.x + other.w + GAP)
        table.insert(xs, other.x - GAP - size.w)
        table.insert(ys, other.y + other.h + GAP)
        table.insert(ys, other.y - GAP - size.h)
    end

    local best, best_score
    for _, x in ipairs(xs) do
        for _, y in ipairs(ys) do
            local rect = { x = clamp(x, area.x, max_x), y = clamp(y, area.y, max_y), w = size.w, h = size.h }
            local score = total_overlap(rect, others)
            if not best
                or score < best_score
                or (score == best_score and (rect.y < best.y or (rect.y == best.y and rect.x < best.x))) then
                best, best_score = rect, score
            end
        end
    end
    return best
end

local function place(window)
    if not window.floating or (window.fullscreen or 0) ~= 0 or window.pinned then
        return
    end
    local own_border = borders(window)
    if not own_border then return false end -- wait for the initial X11 reply / xdg commit
    local workspace, monitor = window.workspace, window.monitor
    if not workspace or not workspace.id or workspace.id < 1 or not monitor or not monitor.width then
        return
    end
    if matches(window.class, KEEP_CLASSES) or matches(window.title, KEEP_TITLES) then
        return
    end

    local others = {}
    for _, other in ipairs(hl.get_workspace_windows(workspace.id) or {}) do
        if other.address ~= window.address and other.mapped and not other.hidden then
            -- Otra ventana de la misma app: es un diálogo o una ventana secundaria, que Hyprland
            -- coloca sobre la suya (KWin también centra los diálogos sobre su ventana)
            if other.pid == window.pid then
                return
            end
            local other_border = borders(other)
            if not other_border then return false end
            table.insert(others, frame(other, other_border))
        end
    end
    local policy = kwin.placement or "Smart"
    if policy == "NoPlacement" or policy == "OnMainWindow" then return end
    if #others == 0 and (policy == "Smart" or policy == "Default") then return end

    local area = work_area(monitor)
    local size = { w = window.size.x + own_border.left + own_border.right, h = window.size.y + own_border.top + own_border.bottom }
    if size.w > area.w or size.h > area.h then
        return
    end
    local rect
    if policy == "Centered" then
        rect = { x = area.x + (area.w - size.w) / 2, y = area.y + (area.h - size.h) / 2 }
    elseif policy == "Random" then
        rect = { x = area.x + math.random(0, math.floor(area.w - size.w)),
                 y = area.y + math.random(0, math.floor(area.h - size.h)) }
    elseif policy == "ZeroCornered" then
        rect = { x = area.x, y = area.y }
    elseif policy == "UnderMouse" then
        local pos = hl.get_cursor_pos()
        rect = { x = clamp(pos.x - size.w / 2, area.x, area.x + area.w - size.w),
                 y = clamp(pos.y - size.h / 2, area.y, area.y + area.h - size.h) }
    elseif policy == "Maximizing" then
        hl.dispatch(hl.dsp.window.fullscreen({ window = window, mode = 1, action = "set" }))
        return
    else
        -- Smart, Default y valores desconocidos: mínimo solapamiento.
        rect = best_position(size, area, others)
    end
    hl.dispatch(hl.dsp.window.move({
        x = math.floor(rect.x + own_border.left),
        y = math.floor(rect.y + own_border.top),
        relative = false,
        window = window,
    }))
end

local function on_open(window, attempt, address, pid)
    if not window or window.address ~= address or window.pid ~= pid or window.mapped == false then return end
    local ok, result = pcall(place, window)
    if not ok then print("BWM placement: " .. tostring(result))
    elseif result == false and attempt < 10 and hl.timer then
        hl.timer(function() on_open(window, attempt + 1, address, pid) end, { type = "oneshot", timeout = 30 })
    end
end
hl.on("window.open", function(window) on_open(window, 0, window.address, window.pid) end)
