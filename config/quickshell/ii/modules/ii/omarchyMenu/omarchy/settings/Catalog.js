// Retro exposes only options consumed by its own shell or shared services.
// Keep the existing managers and Omarchy's theme/plugin formats as the source of truth.
var pages = [
  ["interface", "setup.interface", "Interfaz", "󰕮", ""],
  ["general", "setup.general", "Batería", "󰁹", ""],
  ["services", "setup.services", "Servicios", "󰒋", ""],
  ["idle", "setup.idle", "Inactividad", "󰒲", ""],
  ["display", "setup.monitors", "Pantallas", "󰍹", "DisplaySettings.qml"],
  ["cursor", "setup.cursor", "Cursor", "󰇀", ""],
  ["defaultapps", "setup.default", "Apps predeterminadas", "󰀻", ""],
  ["keybinds", "setup.keybindings", "Atajos de teclado", "󰌌", ""],
  ["autostart", "setup.autostart", "Inicio automático", "󱓞", ""],
  ["plugins", "setup.plugin.manage", "Instalados", "󰐱", ""],
  ["plugin-catalog", "setup.plugin.catalog", "Catálogo", "󰐱", ""],
  ["themes", "appearance.retro-palette.catalog", "Catálogo", "󰏘", ""]
];
var groups = [
  {page:"interface", id:"overview", label:"Vista general", icon:"󰕰", prefix:"overview."},
  {page:"services", id:"weather", label:"Tiempo", icon:"󰖐", prefix:"bar.weather."}
];
// External open-settings callers retain their page names and numeric indices.
function page(key) {
  if (/^\d+$/.test(String(key))) key = ["general", "bar", "background", "interface", "keybinds", "services", "autostart", "display", "workspaces", "defaultapps", "plugins", "themes", "style", "cursor", "about", "idle"][Number(key)] || "all";
  var name = String(key || "").toLowerCase().replace(/[^a-z]/g, "");
  if (name === "defaultapplications") name = "defaultapps";
  if (name === "workspaces") name = "display";
  for (var i = 0; i < pages.length; i++) if (pages[i][0] === name || pages[i][1] === key) return pages[i];
  return null;
}
function route(key) {
  var p = page(key);
  if (p) return p[1];
  return ({bar:"appearance.top-bar", background:"appearance.background", style:"appearance", about:"about"})[key] || "setup";
}
// Old IPC routes and user menu links still reach the replacement section.
function resolve(id) {
  var aliases = {
    "setup.settings":"setup", "setup.settings.look":"appearance", "setup.settings.desktop":"setup", "setup.settings.system":"setup",
    "setup.settings.look.bar":"appearance.top-bar", "setup.settings.look.background":"appearance.background",
    "setup.settings.look.interface":"setup.interface", "setup.settings.look.themes":"appearance.retro-palette",
    "setup.settings.look.style":"appearance", "setup.settings.look.cursor":"setup.cursor",
    "setup.settings.desktop.display":"setup.monitors", "setup.settings.desktop.workspaces":"setup.monitors",
    "setup.settings.desktop.keybinds":"setup.keybindings", "setup.settings.system.general":"setup.general",
    "setup.settings.system.services":"setup.services", "setup.settings.system.autostart":"setup.autostart",
    "setup.settings.system.idle":"setup.idle", "setup.settings.system.defaultapps":"setup.default",
    "setup.settings.system.plugins":"setup.plugin.manage", "setup.settings.text":"setup.config", "setup.settings.about":"about"
  };
  return aliases[String(id).replace(/\.controls$/, "")] || id;
}
function choice(label, value) { return {label:label, value:value}; }
function field(pageId, key, label, type, extra) {
  var f = {id:route(pageId) + "." + key.replace(/\./g, "-"), parent:route(pageId), path:key, label:label, type:type, icon:""};
  for (var k in extra || {}) f[k] = extra[k];
  return f;
}
function fields() {
  var out = [];
  function add(p, path, label, type, extra) { out.push(field(p, path, label, type, extra)); }
  function bool(p, path, label) { add(p, path, label, "bool"); }
  function num(p, path, label, min, max, step, unit) { add(p, path, label, "number", {min:min, max:max, step:step || 1, unit:unit || ""}); }
  function text(p, path, label, hint) { add(p, path, label, "text", {hint:hint || ""}); }
  bool("interface", "overview.enable", "Activar");
  bool("interface", "overview.centerIcons", "Centrar iconos");
  num("interface", "overview.rows", "Filas", 1, 8);
  num("interface", "overview.columns", "Columnas", 1, 10);
  bool("interface", "overview.orderRightLeft", "Columnas de derecha a izquierda");
  bool("interface", "overview.orderBottomUp", "Filas de abajo arriba");
  bool("interface", "lock.launchOnStartup", "Bloquear al iniciar sesión");
  out.push({id:"appearance.dock.enabled", parent:"appearance.dock", path:"dock.omarchy", label:"Activar", type:"bool", icon:""});
  bool("idle", "idle.screensaver", "Salvapantallas");
  num("idle", "idle.screensaverTime", "Salvapantallas tras", 0, 7200, 30, "duration");
  num("idle", "idle.screen", "Apagar pantallas tras", 0, 7200, 30, "duration");
  num("idle", "idle.lock", "Bloquear tras", 0, 7200, 30, "duration");
  num("idle", "idle.suspend", "Suspender tras", 0, 14400, 60, "duration");
  bool("general", "sounds.battery", "Sonido de aviso");
  num("general", "battery.low", "Batería baja", 0, 100, 5, "%");
  num("general", "battery.critical", "Batería crítica", 0, 100, 5, "%");
  num("general", "battery.full", "Carga completa", 0, 100, 5, "%");
  bool("general", "battery.automaticSuspend", "Suspender con batería baja");
  num("general", "battery.suspend", "Suspender al", 0, 100, 1, "%");
  text("services", "bar.weather.city", "Ciudad", "Vacío: automática");
  bool("services", "bar.weather.useUSCS", "Unidades imperiales");
  text("services", "screenRecord.savePath", "Carpeta de grabaciones");
  text("services", "screenSnip.savePath", "Carpeta de capturas");
  for (var g = 0; g < groups.length; g++) {
    var group = groups[g];
    for (var n = 0; n < out.length; n++) {
      var f = out[n];
      if (f.parent === route(group.page) && f.path.startsWith(group.prefix)) {
        f.parent = route(group.page) + "." + group.id;
        f.id = f.parent + "." + f.path.slice(group.prefix.length).replace(/\./g, "-");
      }
    }
  }
  return out;
}
function fieldEntries(all) {
  var rows = [];
  for (var i = 0; i < all.length; i++) {
    var f = all[i];
    rows.push({id:f.id, parent:f.parent, label:f.label, icon:f.icon || "", searchTerms:f.searchTerms || [], action:f.type === "choice" ? "" : ":"});
    if (f.choices) for (var c = 0; c < f.choices.length; c++) rows.push({id:f.id + ".value" + c, parent:f.id, label:f.choices[c].label, icon:"", action:":"});
  }
  return rows;
}
function entries() {
  var rows = [];
  for (var p = 0; p < pages.length; p++) {
    var pg = pages[p];
    rows.push({id:pg[1], label:pg[2], icon:pg[3], action:pg[4] ? ":" : "", provider:!pg[4] && !["interface", "general", "services", "idle"].includes(pg[0]) ? "settings" : ""});
  }
  for (var g = 0; g < groups.length; g++) rows.push({id:route(groups[g].page) + "." + groups[g].id, label:groups[g].label, icon:groups[g].icon});
  return rows.concat(fieldEntries(fields()));
}
function read(options, path) {
  var obj = options;
  var keys = path.split(".");
  for (var i = 0; i < keys.length; i++) { if (obj === null || obj === undefined) return undefined; obj = obj[keys[i]]; }
  return obj;
}
function write(options, path, value) {
  var keys = path.split(".");
  var obj = options;
  for (var i = 0; i < keys.length - 1; i++) { if (obj[keys[i]] === undefined) return false; obj = obj[keys[i]]; }
  obj[keys[keys.length - 1]] = value;
  return true;
}
// Tiempos en segundos (unit "duration"): se muestran «5 min 30 s» y se escriben «5:30»; un número
// solo son minutos
function durationLabel(s) {
  s = Number(s) || 0;
  if (s <= 0) return "Nunca";
  var m = Math.floor(s / 60), r = s % 60;
  return (m ? m + " min" : "") + (m && r ? " " : "") + (r ? r + " s" : "");
}
function durationText(s) {
  s = Number(s) || 0;
  var r = s % 60;
  return Math.floor(s / 60) + ":" + (r < 10 ? "0" : "") + r;
}
function parseDuration(text) {
  var t = String(text).trim().toLowerCase();
  var m = t.match(/^(\d+):([0-5]?\d)$/);
  if (m) return Number(m[1]) * 60 + Number(m[2]);
  if (/^\d+$/.test(t)) return Number(t) * 60;
  m = t.match(/^(?:(\d+)\s*m(?:in)?)?\s*(?:(\d+)\s*s)?$/);
  if (m && (m[1] || m[2])) return Number(m[1] || 0) * 60 + Number(m[2] || 0);
  return NaN;
}
function editText(field, value) {
  return field && field.unit === "duration" ? durationText(value) : String(value === undefined ? "" : value);
}
function parseNumber(field, text) {
  return field && field.unit === "duration" ? parseDuration(text) : (String(text).trim() ? Number(text) : NaN);
}
function validate(field, text) {
  if (field.type !== "number") return {ok: true, value: text};
  if (field.unit === "duration") {
    var d = parseDuration(text);
    if (!isFinite(d)) return {ok: false, error: "Escribe minutos:segundos, p. ej. 5:00 (0 = nunca)"};
    if (d < field.min || d > field.max) return {ok: false, error: "Entre " + durationText(field.min) + " y " + durationText(field.max)};
    return {ok: true, value: d};
  }
  if (!String(text).trim()) return {ok: false, error: "Escribe un número"};
  var n = Number(text);
  if (!isFinite(n)) return {ok: false, error: "Escribe un número válido"};
  if (Math.round(n) !== n) return {ok: false, error: "Usa un número entero"};
  if (n < field.min || n > field.max) return {ok: false, error: "Entre " + field.min + " y " + field.max + (field.unit ? " " + field.unit : "")};
  return {ok: true, value: n};
}
function summary(field, value) {
  if (value === undefined) return "No disponible";
  if (field.type === "bool") return value ? "Sí" : "No";
  if (field.choices) for (var i = 0; i < field.choices.length; i++) if (field.choices[i].value === value) return field.choices[i].label;
  if (field.unit === "duration") return durationLabel(value);
  return (String(value) || "Sin definir") + (field.unit ? " " + field.unit : "");
}
