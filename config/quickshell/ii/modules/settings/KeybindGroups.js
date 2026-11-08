.pragma library

// Agrupa y ordena los atajos de Ajustes → Atajos de teclado:
// - las cuatro flechas con los mismos modificadores son una fila «←↑↓→» desplegable,
// - los números (Alt+1…0) igual,
// - las teclas multimedia (volumen, brillo, reproducción) en otra,
// - una acción con varias combinaciones (Print o Super+Shift+S) sale en una sola fila con ambas,
// - lo más usado primero.

var DIRECTIONS = ["left", "up", "down", "right"];
var KEY_LABELS = {
    left: "←", right: "→", up: "↑", down: "↓",
    RETURN: "Enter", SPACE: "Espacio", TAB: "Tab", Escape: "Esc",
    SUPER_L: "Super", period: ".", comma: ",", Print: "ImprPant",
    XF86AudioRaiseVolume: "Vol +", XF86AudioLowerVolume: "Vol −", XF86AudioMute: "Silencio",
    XF86AudioMicMute: "Micro", XF86MonBrightnessUp: "Brillo +", XF86MonBrightnessDown: "Brillo −",
    XF86AudioPlay: "Play", XF86AudioNext: "Siguiente", XF86AudioPrev: "Anterior", XF86AudioStop: "Stop"
};
// Lo que más se usa, en este orden; lo demás va después, por categoría
var PRIORITY = [
    /app-launcher\.sh(?! apps)/, /app-launcher\.sh apps/, /^terminal /, /window\.close/,
    /window\.fullscreen/, /altTab/, /focus_direction/, /workspace_focus/, /workspace_window_move \d/,
    /window_move_direction/, /quick-tile/, /cheatsheet/, /open-settings/, /lock activate/,
    /region screenshot/, /clipboard/, /emojis/, /nautilus/, /sidebarRight/, /hyprshutdown/, /bwm-power/,
    /theme-picker/, /omarchy-theme/, /wallpaper-picker/, /toggle_special|special:magic/
];
var CATEGORY_ORDER = ["Lanzadores", "Ventanas", "Navegación", "Espacios de trabajo", "Sistema",
                      "General", "Multimedia", "Personalizados"];

function keyLabel(key) {
    return KEY_LABELS[key] !== undefined ? KEY_LABELS[key] : (key || "");
}

function signature(b) {
    return (b.id || "") + " " + (b.exec || "") + " " + (b.dispatcher || "") + " " + (b.dispatcher_arg || "");
}

function action(b) {
    return b.action_type === "exec" ? "exec:" + (b.exec || "").trim()
                                    : "disp:" + (b.dispatcher || "") + ":" + (b.dispatcher_arg || "");
}

function rank(b, index) {
    var sig = signature(b);
    for (var i = 0; i < PRIORITY.length; i++)
        if (PRIORITY[i].test(sig)) return i * 1000 + index;
    var cat = CATEGORY_ORDER.indexOf(b.category || "");
    return (PRIORITY.length + (cat < 0 ? CATEGORY_ORDER.length : cat)) * 1000 + index;
}

function modsKey(b) {
    return (b.mods || []).slice().sort().join("+");
}

function words(text) {
    return (text || "").split(/\s+/).filter(function (w) { return w.length > 0; });
}

// Palabras iniciales comunes («Mover foco a la izquierda», «… hacia arriba» → «Mover foco»)
function commonPrefix(texts) {
    var lists = texts.map(words);
    var out = [];
    for (var i = 0; lists.length && i < lists[0].length; i++) {
        var w = lists[0][i];
        if (!lists.every(function (l) { return l[i] === w; })) break;
        out.push(w);
    }
    while (out.length && /^(a|al|la|el|hacia|de|del|en|y)$/i.test(out[out.length - 1])) out.pop();
    return out.join(" ");
}

function stripDirection(text) {
    return (text || "").replace(/\s*(a la |hacia |al )?(izquierda|derecha|arriba|abajo)\b.*$/i, "").trim();
}

// Quita «(Print)», «(Super+Shift+S)»… que repiten la combinación en la descripción
function stripKeysNote(text) {
    return (text || "").replace(/\s*\(([^)]*\+[^)]*|print|alt\+\w+)\)\s*$/i, "").trim();
}

// Super_L con el modificador Super es sólo «Super»
function visibleMods(mods, key) {
    var k = String(key || "").toLowerCase();
    return (mods || []).filter(function (m) {
        var mod = m.toLowerCase();
        return mod !== k && k.indexOf(mod + "_") !== 0;
    });
}

function combo(mods, key) {
    return { mods: visibleMods(mods, key), key: key };
}

function makeGroup(kind, binds) {
    var title, combos;
    var descs = binds.map(function (b) { return b.description || b.id; });
    if (kind === "arrows") {
        var byDir = {};
        binds.forEach(function (b) { byDir[b.key] = b; });
        binds = DIRECTIONS.filter(function (d) { return byDir[d]; }).map(function (d) { return byDir[d]; });
        title = commonPrefix(descs);
        if (words(title).length < 2) title = stripDirection(binds[0].description || binds[0].id);
        combos = [combo(binds[0].mods, binds.map(function (b) { return keyLabel(b.key); }).join(" "))];
    } else if (kind === "digits") {
        binds = binds.slice().sort(function (a, b) {
            return (a.key === "0" ? 10 : +a.key) - (b.key === "0" ? 10 : +b.key);
        });
        title = commonPrefix(descs) || descs[0];
        combos = [combo(binds[0].mods, binds[0].key + "…" + binds[binds.length - 1].key)];
    } else if (kind === "media") {
        title = "Teclas multimedia (volumen, brillo y reproducción)";
        combos = [combo([], binds.slice(0, 3).map(function (b) { return keyLabel(b.key); }).join(" ") + " …")];
    } else {
        title = stripKeysNote(descs[0]);
        combos = binds.map(function (b) { return { mods: visibleMods(b.mods, b.key), key: keyLabel(b.key) }; });
    }
    return {
        key: kind + ":" + binds.map(function (b) { return b.id; }).join(","),
        kind: kind, title: title, category: binds[0].category || "", combos: combos, binds: binds
    };
}

function single(b) {
    return { key: "one:" + b.id, kind: "single", title: b.description || b.id, category: b.category || "",
             combos: [{ mods: visibleMods(b.mods, b.key), key: keyLabel(b.key) }], binds: [b] };
}

// list: atajos ya filtrados. group = false deja una fila por atajo (pestaña «Eliminados»).
function build(list, group) {
    var items = (list || []).map(function (b, i) { return { b: b, r: rank(b, i) }; });
    items.sort(function (x, y) { return x.r - y.r; });
    var binds = items.map(function (x) { return x.b; });
    if (!group) return binds.map(single);

    var used = {};
    var buckets = {};
    var order = [];
    function add(bucketKey, kind, b) {
        if (!buckets[bucketKey]) { buckets[bucketKey] = { kind: kind, binds: [] }; order.push(bucketKey); }
        buckets[bucketKey].binds.push(b);
    }
    binds.forEach(function (b) {
        if (DIRECTIONS.indexOf(b.key) >= 0) add("arrows|" + modsKey(b) + "|" + (b.category || ""), "arrows", b);
        else if (/^[0-9]$/.test(b.key || "")) add("digits|" + modsKey(b) + "|" + (b.dispatcher || b.exec || ""), "digits", b);
        else if (/^XF86/.test(b.key || "")) add("media", "media", b);
    });
    var groupOf = {};
    order.forEach(function (k) {
        var bucket = buckets[k];
        var min = bucket.kind === "arrows" ? 2 : 3;  // números y teclas multimedia: 3 o más
        if (bucket.binds.length < min) return;
        var g = makeGroup(bucket.kind, bucket.binds);
        bucket.binds.forEach(function (b) { used[b.id] = true; groupOf[b.id] = g; });
    });

    var byAction = {};
    binds.forEach(function (b) {
        if (used[b.id]) return;
        var a = action(b);
        (byAction[a] = byAction[a] || []).push(b);
    });

    var out = [];
    var emitted = {};
    binds.forEach(function (b) {
        var g = groupOf[b.id];
        if (g) {
            if (!emitted[g.key]) { emitted[g.key] = true; out.push(g); }
            return;
        }
        var same = byAction[action(b)];
        if (same.length > 1) {
            var alt = makeGroup("alternatives", same);
            if (!emitted[alt.key]) { emitted[alt.key] = true; out.push(alt); }
            return;
        }
        out.push(single(b));
    });
    return out;
}
