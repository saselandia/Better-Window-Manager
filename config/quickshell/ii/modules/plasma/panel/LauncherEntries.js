// BWM: pure helpers for LauncherEntries.qml (Unity LauncherEntry state, see
// plasma-desktop 6.7.5 smartlauncherbackend.cpp/smartlauncheritem.cpp, GPL-2.0-or-later).
.pragma library

function key(id) {
    return String(id || "").toLowerCase().replace(/^application:\/\//, "").replace(/\.desktop$/, "");
}

// The toplevel appId or its resolved desktop entry id, as Plasma's LauncherUrlWithoutIcon.
function lookup(entries, appId, desktopId) {
    return entries[key(desktopId)] ?? entries[key(appId)] ?? null;
}

// Backend::countVisible(): hidden while do-not-disturb is on.
function countVisible(entry, doNotDisturb) {
    return !!entry && !doNotDisturb && !!entry.countVisible && entry.count > 0;
}

function progressVisible(entry) {
    return !!entry && !!entry.progressVisible;
}

// One JSON line from launcher-entries.py; returns the new entries map (or the same object).
function handle(entries, line) {
    let msg;
    try { msg = JSON.parse(line); } catch (e) { return entries; }
    if (msg.reset) return {};
    if (!msg.id) return entries;
    const next = Object.assign({}, entries);
    if (msg.removed) delete next[msg.id];
    else next[msg.id] = msg;
    return next;
}
