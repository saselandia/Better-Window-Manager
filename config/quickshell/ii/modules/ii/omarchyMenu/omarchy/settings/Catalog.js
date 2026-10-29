// BWM's Retro settings use Omarchy's existing menu format and Config.options.
// No second settings store: these paths are the same ones used by the shared pages.
var pages = [
  ["bar", "setup.settings.look.bar", "Barra", "󰍜", "BarConfig.qml"],
  ["background", "setup.settings.look.background", "Fondo", "󰋩", "BackgroundConfig.qml"],
  ["interface", "setup.settings.look.interface", "Interfaz", "󰕮", "InterfaceConfig.qml"],
  ["themes", "setup.settings.look.themes", "Temas", "󰏘", "ThemesConfig.qml"],
  ["style", "setup.settings.look.style", "Estilo", "󰛖", "StyleConfig.qml"],
  ["cursor", "setup.settings.look.cursor", "Cursor", "󰇀", "CursorConfig.qml"],
  ["display", "setup.settings.desktop.display", "Pantallas", "󰍹", "DisplayConfig.qml"],
  ["workspaces", "setup.settings.desktop.workspaces", "Workspaces", "󰕰", "WorkspaceConfig.qml"],
  ["keybinds", "setup.settings.desktop.keybinds", "Atajos de teclado", "󰌌", "KeybindsConfig.qml"],
  ["general", "setup.settings.system.general", "General", "󰒓", "GeneralConfig.qml"],
  ["services", "setup.settings.system.services", "Servicios", "󰒋", "ServicesConfig.qml"],
  ["autostart", "setup.settings.system.autostart", "Inicio automático", "󱓞", "AutostartConfig.qml"],
  ["defaultapps", "setup.settings.system.defaultapps", "Apps predeterminadas", "󰀻", "DefaultAppsConfig.qml"],
  ["plugins", "setup.settings.system.plugins", "Plugins", "󰐱", "PluginsConfig.qml"],
  ["about", "setup.settings.about", "Acerca de", "󰋼", "About.qml"]
];
var groups = [
  {page:"general", id:"battery", label:"Batería", icon:"󰁹", prefix:"battery."},
  {page:"interface", id:"overview", label:"Vista general", icon:"󰕰", prefix:"overview."},
  {page:"services", id:"weather", label:"Tiempo", icon:"󰖐", prefix:"bar.weather."}
];
function page(key) {
  if (/^\d+$/.test(String(key))) key = ["general", "bar", "background", "interface", "keybinds", "services", "autostart", "display", "workspaces", "defaultapps", "plugins", "themes", "style", "cursor", "about"][Number(key)] || "all";
  var name = String(key || "").toLowerCase().replace(/[^a-z]/g, "");
  if (name === "defaultapps" || name === "defaultapplications") name = "defaultapps";
  for (var i = 0; i < pages.length; i++) if (pages[i][0] === name || pages[i][1] === key) return pages[i];
  return null;
}
function route(key) { var p = page(key); return p ? p[1] : "setup.settings"; }
function choice(label, value) { return {label: label, value: value}; }
function field(pageId, key, label, type, extra) {
  var f = {id: route(pageId) + "." + key.replace(/\./g, "-"), parent: route(pageId), path: key, label: label, type: type, icon: key.startsWith("time.") ? "󰥔" : key.startsWith("battery.") ? "󰁹" : key.includes("weather") ? "󰖐" : key.includes("fonts.") ? "󰛖" : key.startsWith("search.") ? "󰍉" : key.includes("dock") ? "󰀻" : "󰒓"};
  for (var k in extra || {}) f[k] = extra[k];
  return f;
}
function fields() {
  var out = [];
  function add(p, path, label, type, extra) { out.push(field(p, path, label, type, extra)); }
  function bool(p, path, label) { add(p, path, label, "bool"); }
  function num(p, path, label, min, max, step, unit) { add(p, path, label, "number", {min:min, max:max, step:step || 1, unit:unit || ""}); }
  function text(p, path, label, hint) { add(p, path, label, "text", {hint:hint || ""}); }
  function select(p, path, label, values) { add(p, path, label, "choice", {choices:values.map(function(v) { return choice(v[0], v[1]); })}); }
  bool("bar", "bar.bottom", "Barra en la parte inferior");
  bool("bar", "bar.autoHide.enable", "Ocultar automáticamente la barra");
  bool("bar", "bar.indicators.notifications.showUnreadCount", "Contador de notificaciones");
  num("bar", "bar.workspaces.shown", "Número de workspaces", 1, 20, 1);
  bool("bar", "bar.weather.enable", "Tiempo en la barra");
  bool("bar", "tray.showItemId", "Identificador de iconos de bandeja");
  select("bar", "bar.topLeftIcon", "Icono del lanzador", [["BWM", "spark"], ["Distribución", "distro"]]);
  bool("background", "background.widgets.clock.enable", "Reloj en el fondo");
  bool("background", "background.widgets.weather.enable", "Tiempo en el fondo");
  bool("background", "background.widgets.clock.quote.enable", "Frase bajo el reloj");
  text("background", "background.widgets.clock.quote.text", "Texto de la frase");
  bool("interface", "dock.omarchy", "Dock de Omarchy");
  bool("interface", "overview.enable", "Vista general");
  bool("interface", "overview.centerIcons", "Centrar iconos de la vista general");
  num("interface", "overview.rows", "Filas de la vista general", 1, 8);
  num("interface", "overview.columns", "Columnas de la vista general", 1, 10);
  bool("interface", "sidebar.translator.enable", "Traductor de pantalla");
  bool("interface", "sidebar.cornerOpen.enable", "Abrir paneles desde las esquinas");
  bool("interface", "sidebar.cornerOpen.clickless", "Abrir las esquinas al pasar el puntero");
  bool("style", "screensaver.enable", "Salvapantallas automático");
  num("style", "screensaver.timeoutMinutes", "Espera del salvapantallas", 1, 120, 1, "min");
  bool("workspaces", "overview.orderRightLeft", "Orden inverso de las columnas");
  bool("workspaces", "overview.orderBottomUp", "Orden inverso de las filas");
  num("workspaces", "bar.workspaces.shown", "Workspaces en la barra", 1, 20);
  num("workspaces", "overview.rows", "Filas en la vista general", 1, 8);
  num("workspaces", "overview.columns", "Columnas en la vista general", 1, 10);
  select("general", "time.format", "Formato de la hora", [["24 horas", "hh:mm"], ["12 horas", "h:mm AP"]]);
  bool("general", "time.secondPrecision", "Reloj con segundos");
  text("general", "time.dateFormat", "Formato de la fecha", "Por ejemplo: ddd, dd/MM o dddd d MMMM.");
  select("general", "language.ui", "Idioma de los ajustes", [["Automático", "auto"], ["English", "en_US"], ["Español", "es_ES"]]);
  bool("general", "sounds.battery", "Avisos de batería con sonido");
  bool("general", "sounds.pomodoro", "Avisos del temporizador con sonido");
  num("general", "battery.low", "Aviso de batería baja", 0, 100, 5, "%");
  num("general", "battery.critical", "Aviso de batería crítica", 0, 100, 5, "%");
  bool("general", "battery.automaticSuspend", "Suspender con batería baja");
  num("general", "battery.suspend", "Nivel de batería para suspender", 0, 100, 1, "%");
  select("general", "policies.ai", "Funciones de inteligencia artificial", [["Desactivadas", 0], ["Activadas", 1], ["Sólo locales", 2]]);
  bool("services", "bar.weather.enable", "Servicio del tiempo");
  bool("services", "bar.weather.enableGPS", "Localización automática para el tiempo");
  text("services", "bar.weather.city", "Ciudad del tiempo", "Nombre de la ciudad; vacío para detección automática.");
  bool("services", "bar.weather.useUSCS", "Unidades imperiales");
  bool("services", "search.sloppy", "Búsqueda aproximada");
  text("services", "search.engineBaseUrl", "Buscador web", "URL base que se antepone a la consulta.");
  text("services", "screenRecord.savePath", "Carpeta de grabaciones");
  text("services", "screenSnip.savePath", "Carpeta de capturas");
  num("services", "resources.updateInterval", "Intervalo del monitor de recursos", 100, 10000, 100, "ms");
  num("services", "musicRecognition.timeout", "Tiempo para reconocer música", 1, 120, 1, "s");
  add("bar", "shell-language", "Idioma del menú y los paneles", "choice", {backend:"language", choices:[choice("English", "en"), choice("Español (México)", "es-MX")]});
  var widgets = [
    ["omarchy.media", "Multimedia", true], ["omarchy.system-update", "Actualizaciones"],
    ["omarchy.tray", "Bandeja del sistema"], ["omarchy.keyboard-layout", "Distribución del teclado"],
    ["omarchy.agents", "Agentes de IA"], ["omarchy.tailscale", "Tailscale"],
    ["omarchy.bluetooth", "Bluetooth"], ["omarchy.network", "Red"], ["omarchy.audio", "Audio"],
    ["omarchy.monitor", "Pantallas"], ["omarchy.power", "Energía"]
  ];
  for (var w = 0; w < widgets.length; w++) {
    var widget = widgets[w];
    out.push({id:route("bar") + ".widgets." + widget[0].slice(8), parent:route("bar") + ".widgets", label:widget[1], type:"bool", backend:"widget", widget:widget[0], hiddenByDefault:!!widget[2], icon:"󰒓"});
  }
  for (var g = 0; g < groups.length; g++) {
    var group = groups[g];
    for (var n = 0; n < out.length; n++) {
      var f = out[n];
      if (f.parent === route(group.page) && !f.backend && f.path.startsWith(group.prefix)) {
        f.parent = route(group.page) + "." + group.id;
        f.id = f.parent + "." + f.path.slice(group.prefix.length).replace(/\./g, "-");
      }
    }
  }
  return out;
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
function validate(field, text) {
  if (field.type !== "number") return {ok: true, value: text};
  if (!String(text).trim()) return {ok: false, error: "Escribe un número"};
  var n = Number(text);
  if (!isFinite(n)) return {ok: false, error: "Escribe un número válido"};
  if (Math.round(n) !== n) return {ok: false, error: "Usa un número entero"};
  if (n < field.min || n > field.max) return {ok: false, error: "Entre " + field.min + " y " + field.max + (field.unit ? " " + field.unit : "")};
  return {ok: true, value: n};
}
function summary(field, value) {
  if (value === undefined) return "No disponible";
  if (field.type === "bool") return value ? "Activado" : "Desactivado";
  if (field.choices) for (var i = 0; i < field.choices.length; i++) if (field.choices[i].value === value) return field.choices[i].label;
  return (String(value) || "Sin definir") + (field.unit ? " " + field.unit : "");
}
function entries() {
  var rows = [];
  var all = fields();
  for (var p = 0; p < pages.length; p++) {
    var pg = pages[p];
    var hasFields = all.some(function(f) { return f.parent === pg[1]; });
    rows.push({id:pg[1], label:pg[2], icon:pg[3], action:hasFields ? "" : ":"});
    if (pg[0] === "bar") rows.push({id:pg[1] + ".widgets", label:"Widgets de la barra", icon:"󰐱"});
    for (var i = 0; i < all.length; i++) {
      var f = all[i];
      if (f.parent !== pg[1] && !f.parent.startsWith(pg[1] + ".")) continue;
      rows.push({id:f.id, label:f.label, icon:f.icon, action:f.type === "choice" ? "" : ":", parent:f.parent, aliases:[f.label.normalize("NFD").replace(/[\u0300-\u036f]/g, "")]});
      if (f.choices) for (var c = 0; c < f.choices.length; c++) rows.push({id:f.id + ".value" + c, label:f.choices[c].label, icon:"", action:":"});
    }
    for (var g = 0; g < groups.length; g++) if (groups[g].page === pg[0]) rows.push({id:pg[1] + "." + groups[g].id, label:groups[g].label, icon:groups[g].icon});
    if (pg[0] === "style") rows.push({id:pg[1] + ".font", label:"Fuente del sistema", icon:"󰛖", target:"appearance.font"});
    if (hasFields) rows.push({id:pg[1] + ".controls", label:"Más opciones…", icon:"󰒓", action:":"});
  }
  return rows;
}
