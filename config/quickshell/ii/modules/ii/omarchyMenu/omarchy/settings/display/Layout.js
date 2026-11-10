// Monitor geometry is in Hyprland logical coordinates; modes are physical pixels.
function copy(value) { return JSON.parse(JSON.stringify(value)); }
function size(m) {
    var scale = Number(m.scale) || 1;
    var rotated = Number(m.transform || 0) % 2 !== 0;
    return {width: (rotated ? m.height : m.width) / scale, height: (rotated ? m.width : m.height) / scale};
}
// A screen that duplicates another (mirrorOf = description of the screen it copies) takes no room
// in the layout: it shows what its source shows and owns no workspaces.
function solid(monitors) { return monitors.filter(function(m) { return !m.mirrorOf; }); }
function mirrorSource(monitors, m) {
    if (!m || !m.mirrorOf || m.disabled) return null;
    for (var i = 0; i < monitors.length; i++) {
        var o = monitors[i];
        if (o === m || o.description !== m.mirrorOf) continue;
        return (o.disabled || o.mirrorOf) ? null : o;
    }
    return null;
}
function copiedBy(monitors, m) {
    return monitors.some(function(o) { return o !== m && o.mirrorOf && o.mirrorOf === m.description; });
}
// "" (own screen) followed by the screens this one could copy
function mirrorChoices(monitors, index) {
    var m = monitors[index], choices = [""];
    if (!m || m.disabled || copiedBy(monitors, m)) return choices;
    for (var i = 0; i < monitors.length; i++) {
        var o = monitors[i];
        if (i !== index && !o.disabled && !o.mirrorOf) choices.push(o.description);
    }
    return choices;
}
// Makes the screen at `index` a copy of the one with that description, or its own screen again with "".
// A copy owns no workspaces: when it held 1-9 they go to the screen it copies (as monitor-manager.py does).
function setMirror(monitors, index, description) {
    var list = copy(monitors), m = list[index];
    if (!m) return list;
    if (!description) {
        m.mirrorOf = "";
        if (!m.workspaces) m.workspaces = "10";
        return list;
    }
    var source = null;
    for (var i = 0; i < list.length; i++) if (list[i].description === description) source = list[i];
    if (!source || source === m || source.disabled || source.mirrorOf || m.disabled || copiedBy(list, m)) return list;
    if (m.is_primary || m.workspaces === "1-9") {
        for (var j = 0; j < list.length; j++) list[j].is_primary = list[j] === source;
        source.workspaces = "1-9";
    }
    m.mirrorOf = description; m.is_primary = false; m.workspaces = "";
    return list;
}
// Drops duplications that cannot work any more (its source was switched off, say)
function sanitize(monitors) {
    var list = copy(monitors);
    for (var i = 0; i < list.length; i++) {
        if (list[i].mirrorOf && !mirrorSource(list, list[i])) {
            list[i].mirrorOf = "";
            if (!list[i].workspaces) list[i].workspaces = "10";
        }
    }
    return list;
}
function bounds(allMonitors, padding) {
    var monitors = solid(allMonitors);
    var list = monitors.length ? monitors : [{x:0,y:0,width:1920,height:1080,scale:1}];
    var left = Infinity, top = Infinity, right = -Infinity, bottom = -Infinity;
    for (var i = 0; i < list.length; i++) {
        var m = list[i], s = size(m);
        left = Math.min(left, m.x); top = Math.min(top, m.y);
        right = Math.max(right, m.x + s.width); bottom = Math.max(bottom, m.y + s.height);
    }
    var p = padding || 0;
    return {x:left-p, y:top-p, width:Math.max(1,right-left+p*2), height:Math.max(1,bottom-top+p*2)};
}
function normalize(monitors) {
    var list = copy(monitors);
    var active = list.filter(function(m) { return !m.disabled && !m.mirrorOf; });
    if (!active.length) return list;
    var minX = Math.min.apply(null, active.map(function(m) { return m.x; }));
    var minY = Math.min.apply(null, active.map(function(m) { return m.y; }));
    for (var i = 0; i < list.length; i++) { list[i].x = Math.round(list[i].x - minX); list[i].y = Math.round(list[i].y - minY); }
    return list;
}
function move(monitors, index, dx, dy, frame) {
    var list = copy(monitors), m = list[index];
    if (!m || m.disabled || m.mirrorOf) return list;
    var s = size(m);
    m.x = Math.round(m.x + dx); m.y = Math.round(m.y + dy);
    if (frame) {
        m.x = Math.max(Math.ceil(frame.x), Math.min(Math.floor(frame.x + frame.width - s.width), m.x));
        m.y = Math.max(Math.ceil(frame.y), Math.min(Math.floor(frame.y + frame.height - s.height), m.y));
    }
    return list;
}
function snap(monitors, index, tolerance) {
    var list = copy(monitors), target = list[index];
    if (!target || target.disabled || target.mirrorOf) return list;
    var originalX = target.x, originalY = target.y;
    var s = size(target), bestX = tolerance + 1, bestY = tolerance + 1;
    for (var i = 0; i < list.length; i++) {
        if (i === index || list[i].disabled || list[i].mirrorOf) continue;
        var other = list[i], os = size(other);
        var xs = [other.x, other.x + os.width, other.x - s.width, other.x + os.width - s.width];
        var ys = [other.y, other.y + os.height, other.y - s.height, other.y + os.height - s.height];
        for (var x = 0; x < xs.length; x++) if (Math.abs(originalX - xs[x]) < bestX) { bestX = Math.abs(originalX - xs[x]); target.x = xs[x]; }
        for (var y = 0; y < ys.length; y++) if (Math.abs(originalY - ys[y]) < bestY) { bestY = Math.abs(originalY - ys[y]); target.y = ys[y]; }
    }
    return list;
}
function resolutions(m) {
    var values = (m.resolutions || []).slice();
    var current = m.width + "x" + m.height;
    if (values.indexOf(current) < 0) values.push(current);
    return values.filter(function(value, i) { return /^\d+x\d+$/.test(value) && values.indexOf(value) === i; }).sort(function(a,b) {
        var aa=a.split("x"), bb=b.split("x");
        return Number(aa[0])*Number(aa[1]) - Number(bb[0])*Number(bb[1]);
    });
}
function rates(m) {
    var list = ((m.modesMap || {})[m.width + "x" + m.height] || []).slice();
    if (!list.length) list.push(m.refreshRate || 60);
    return list.sort(function(a,b) { return a-b; });
}
function setResolution(monitors, index, value) {
    var list = copy(monitors), m = list[index];
    if (!m || resolutions(m).indexOf(value) < 0) return list;
    var originalX = m.x, originalY = m.y;
    var before = size(m), parts = value.split("x");
    m.width = Number(parts[0]); m.height = Number(parts[1]);
    var after = size(m), available = rates(m), current = Number(m.refreshRate);
    m.refreshRate = available.reduce(function(best,hz) { return Math.abs(hz-current) < Math.abs(best-current) ? hz : best; }, available[0]);
    // Keep an attached right/bottom edge attached when the selected screen shrinks.
    for (var i = 0; i < list.length; i++) {
        if (i === index || list[i].disabled || list[i].mirrorOf) continue;
        var other = list[i];
        if (Math.abs(originalX + before.width - other.x) < 1 && originalY < other.y + size(other).height && originalY + before.height > other.y) m.x = Math.round(other.x - after.width);
        if (Math.abs(originalY + before.height - other.y) < 1 && originalX < other.x + size(other).width && originalX + before.width > other.x) m.y = Math.round(other.y - after.height);
    }
    return list;
}
function resize(monitors, index, axis, direction) {
    var m = monitors[index];
    if (!m || m.disabled) return copy(monitors);
    var current = size(m), candidates = resolutions(m), best = null, score = Infinity;
    for (var i = 0; i < candidates.length; i++) {
        var parts = candidates[i].split("x"), candidate = copy(m);
        candidate.width = Number(parts[0]); candidate.height = Number(parts[1]);
        var s = size(candidate), change = axis === "x" ? s.width-current.width : s.height-current.height;
        if (change * direction <= 0.1) continue;
        var distance = Math.abs(s.width-current.width) + Math.abs(s.height-current.height);
        if (distance < score) { best = candidates[i]; score = distance; }
    }
    return best ? setResolution(monitors,index,best) : copy(monitors);
}
function cycle(values, current, delta) {
    if (!values.length) return current;
    var index = values.indexOf(current);
    if (index < 0) index = 0;
    return values[Math.max(0,Math.min(values.length-1,index+delta))];
}
function validate(monitors) {
    var active = monitors.filter(function(m) { return !m.disabled && !m.mirrorOf; });
    if (!active.length) return "Debe quedar al menos una pantalla activa";
    for (var c = 0; c < monitors.length; c++)
        if (monitors[c].mirrorOf && !mirrorSource(monitors, monitors[c])) return "La pantalla que se duplica debe estar activa y no ser a su vez una copia";
    var ids = [];
    for (var i = 0; i < monitors.length; i++) {
        var m = monitors[i], id = String(m.description || "").trim();
        if (!id || ids.indexOf(id) >= 0) return "No se puede identificar cada pantalla por su descripción";
        ids.push(id);
        if (!isFinite(m.x) || !isFinite(m.y) || m.scale <= 0) return "La posición o la escala no es válida";
        if (m.disabled) continue;
        if (m.width <= 0 || m.height <= 0 || (m.resolutions || []).indexOf(m.width + "x" + m.height) < 0) return "Selecciona una resolución disponible";
    }
    for (var a = 0; a < active.length; a++) for (var b = a+1; b < active.length; b++) {
        var sa=size(active[a]), sb=size(active[b]);
        if (active[a].x < active[b].x+sb.width-0.5 && active[a].x+sa.width > active[b].x+0.5 && active[a].y < active[b].y+sb.height-0.5 && active[a].y+sa.height > active[b].y+0.5) return "Las pantallas se superponen; sepáralas en el esquema";
    }
    return "";
}
