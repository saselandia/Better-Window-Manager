// BWM: pure geometry/visibility adapter for Plasma PanelView on layer-shell.
function clamp(v, low, high) { return Math.max(low, Math.min(high, v)); }
function edge(config, bottom) {
    return ["top", "bottom", "left", "right"].includes(config.edge) ? config.edge : (bottom ? "bottom" : "top");
}
function geometry(w, h, config, bottom, touching, revealed) {
    var e = edge(config, bottom), vertical = e === "left" || e === "right";
    var thickness = clamp(Number(config.thickness || 44), 24, 128);
    var floating = !!config.floating || config.style === "floating";
    var gap = floating && !touching ? clamp(Number(config.floatingGap ?? 8), 0, 32) : 0;
    var extent = vertical ? h : w;
    var length = Math.max(Math.min(160, extent), (extent - 2 * gap) * clamp(Number(config.length ?? 1), .1, 1));
    var align = config.alignment || "center";
    var start = align === "start" ? gap : align === "end" ? extent - gap - length : (extent - length) / 2;
    var visibility = config.visibility || "always";
    var wantsHide = visibility === "autoHide" || (visibility === "dodge" && touching);
    var hidden = wantsHide && !revealed;
    var reserve = visibility === "always" ? thickness : 0;
    var x = vertical ? (e === "left" ? gap : w - gap - thickness) : start;
    var y = vertical ? start : (e === "top" ? gap : h - gap - thickness);
    return {edge:e, vertical:vertical, thickness:thickness, gap:gap, length:length, start:start,
        x:x, y:y, width:vertical?thickness:length, height:vertical?length:thickness,
        visibility:visibility, hidden:hidden, reserve:reserve, distance:gap+thickness};
}
function intersects(a,b) {
    return a.x < b.x+b.width && a.x+a.width > b.x && a.y < b.y+b.height && a.y+a.height > b.y;
}
function touching(monitor, clients, rect) {
    if (!monitor) return false;
    var ws = [monitor.activeWorkspace?.id, monitor.specialWorkspace?.id];
    return clients.some(c => {
        if (c.hidden || c.mapped === false || !ws.includes(c.workspace?.id)) return false;
        if (c.monitor !== monitor.id) return false;
        if (c.fullscreen > 0) return true;
        return intersects(rect, {x:c.at[0]-monitor.x, y:c.at[1]-monitor.y, width:c.size[0], height:c.size[1]});
    });
}
function reorder(ids, source, target) {
    if(source===target) return ids.slice();
    var result = ids.filter(x=>x!==source), i = result.indexOf(target);
    if (i < 0) i = result.length;
    result.splice(i,0,source);
    return result;
}
