// SPDX-License-Identifier: GPL-2.0-or-later
// BWM F11: catalogue of Breeze's «System Settings». Categories and their order/names follow the
// category .desktop files of systemsettings 6.7.5 (categories/settings-*.desktop, X-KDE-Weight).
// kind: "kcm" = a real Plasma KCM embedded with org.bwm.kcm (KQuickConfigModule, shared engine);
//       "bwm" = a common BWM page (modules/settings/*.qml), never duplicated here;
//       "page" = a Breeze page of this folder that writes the KDE files the F2 bridge reads;
//       "launch" = an app configured in BWM (Config.options.apps.*) for QWidget-only modules.
// `aliases` keep the SETTINGS_PAGE ids of the previous plasmaSettings.qml working.
.pragma library

const BWM = "modules/settings/";
const PAGES = "modules/plasma/settings/pages/";

var sections = [
    { id: "input", name: ["Input & Output", "Entrada y salida"], items: [
        { id: "sound", kind: "kcm", module: "kcm_pulseaudio", icon: "preferences-desktop-sound",
          name: ["Sound", "Sonido"], keywords: "audio sonido volumen altavoz micro pulseaudio pipewire" },
        { id: "display", kind: "bwm", component: BWM + "DisplayConfig.qml", icon: "preferences-desktop-display-randr",
          name: ["Display & Monitor", "Pantalla y monitor"], keywords: "pantalla monitor resolucion escala display" },
    ] },
    { id: "hardware", name: ["Connected Devices", "Dispositivos conectados"], items: [
        { id: "bluetooth", kind: "launch", app: "bluetooth", icon: "preferences-system-bluetooth",
          name: ["Bluetooth", "Bluetooth"], keywords: "bluetooth dispositivos emparejar" },
    ] },
    { id: "network", name: ["Networking", "Redes"], items: [
        { id: "network", kind: "launch", app: "network", icon: "preferences-system-network",
          name: ["Wi-Fi & Internet", "Wifi e internet"], keywords: "red wifi internet ethernet vpn conexiones" },
    ] },
    { id: "appearance", name: ["Appearance & Style", "Aspecto y estilo"], items: [
        { id: "themes", name: ["Colors & Themes", "Colores y temas"], icon: "preferences-desktop-theme-global", items: [
            { id: "globaltheme", kind: "kcm", module: "kcm_lookandfeel", icon: "preferences-desktop-theme-global",
              aliases: ["themes"], keywords: "tema global look and feel" },
            { id: "colors", kind: "kcm", module: "kcm_colors", icon: "preferences-desktop-color", keywords: "colores esquema" },
            { id: "plasmastyle", kind: "kcm", module: "kcm_desktoptheme", icon: "preferences-desktop-plasma-theme",
              keywords: "estilo de plasma tema del escritorio" },
            { id: "decorations", kind: "kcm", module: "kcm_kwindecoration", icon: "preferences-desktop-theme-windowdecorations",
              keywords: "decoraciones barras de titulo botones aurorae" },
            { id: "icons", kind: "kcm", module: "kcm_icons", icon: "preferences-desktop-icons", keywords: "iconos" },
            { id: "cursor", kind: "bwm", component: BWM + "CursorConfig.qml", icon: "preferences-cursors",
              name: ["Cursors", "Cursores"], keywords: "cursor puntero raton" },
            { id: "appstyle", kind: "kcm", module: "kcm_style", icon: "preferences-desktop-theme-applications",
              keywords: "estilo de aplicaciones gtk qt widgets" },
        ] },
        { id: "fonts", kind: "kcm", module: "kcm_fonts", icon: "preferences-desktop-font", keywords: "fuentes tipografia letra" },
        { id: "background", kind: "page", component: PAGES + "WallpaperPage.qml", icon: "preferences-desktop-wallpaper",
          name: ["Wallpaper", "Fondo de escritorio"], keywords: "fondo wallpaper" },
        { id: "bar", kind: "bwm", component: BWM + "PlasmaBarConfig.qml", icon: "preferences-desktop-plasma",
          aliases: ["plugins"], name: ["Panel", "Panel"], keywords: "panel barra de tareas flotante" },
    ] },
    { id: "applications", name: ["Apps & Windows", "Aplicaciones y ventanas"], items: [
        { id: "defaultapps", kind: "bwm", component: BWM + "DefaultAppsConfig.qml", icon: "preferences-desktop-default-applications",
          name: ["Default Applications", "Aplicaciones predeterminadas"], keywords: "predeterminadas navegador terminal archivos editor" },
        { id: "windowmanagement", name: ["Window Management", "Gestión de ventanas"], icon: "preferences-system-windows", items: [
            { id: "windowbehavior", kind: "page", component: PAGES + "WindowBehavior.qml", icon: "preferences-system-windows-actions",
              name: ["Window Behavior", "Comportamiento de las ventanas"], keywords: "foco colocacion barra de titulo doble clic encajar imanes" },
            { id: "windowrules", kind: "kcm", module: "kcm_kwinrules", icon: "preferences-system-windows-actions",
              keywords: "reglas de ventana kwin" },
            { id: "workspaces", kind: "bwm", component: BWM + "WorkspaceConfig.qml", icon: "preferences-desktop-virtual",
              name: ["Virtual Desktops", "Escritorios virtuales"], keywords: "escritorios virtuales workspaces" },
        ] },
        { id: "keybinds", kind: "bwm", component: BWM + "KeybindsConfig.qml", icon: "preferences-desktop-keyboard-shortcut",
          name: ["Shortcuts", "Atajos"], keywords: "atajos teclado shortcuts" },
    ] },
    { id: "workspace", name: ["Workspace", "Espacio de trabajo"], items: [
        { id: "behavior", kind: "page", component: PAGES + "GeneralBehavior.qml", icon: "preferences-desktop",
          aliases: ["interface"], name: ["General Behavior", "Comportamiento general"], keywords: "clic doble clic animaciones velocidad" },
        { id: "autostart", kind: "bwm", component: BWM + "AutostartConfig.qml", icon: "preferences-system-login",
          name: ["Autostart", "Inicio automático"], keywords: "inicio automatico arranque autostart" },
        { id: "services", kind: "bwm", component: BWM + "ServicesConfig.qml", icon: "preferences-system-services",
          name: ["Services", "Servicios"], keywords: "servicios tiempo weather ia recursos" },
    ] },
    { id: "system", name: ["System", "Sistema"], items: [
        { id: "idle", kind: "bwm", component: BWM + "IdleConfig.qml", icon: "preferences-system-power-management",
          name: ["Power & Idle", "Energía e inactividad"], keywords: "energia inactividad suspender bloquear apagar pantallas" },
        { id: "general", kind: "bwm", component: BWM + "GeneralConfig.qml", icon: "preferences-system",
          name: ["BWM General", "General de BWM"], keywords: "general bateria idioma hora sonidos" },
        { id: "style", kind: "bwm", component: BWM + "StyleConfig.qml", icon: "preferences-system-login",
          name: ["Boot & Login", "Arranque e inicio de sesión"], keywords: "arranque sddm plymouth inicio de sesion glass fuente del sistema" },
        { id: "about", kind: "bwm", component: BWM + "About.qml", icon: "hwinfo",
          name: ["About this System", "Acerca de este sistema"], keywords: "acerca de informacion sistema" },
    ] },
];

// Every module (leaf) with its section and parent subcategory
function leaves() {
    const out = [];
    for (const s of sections)
        for (const item of s.items) {
            if (item.items) for (const child of item.items) out.push({ entry: child, section: s, parent: item });
            else out.push({ entry: item, section: s, parent: null });
        }
    return out;
}

// SETTINGS_PAGE: an id, an alias of the previous app, or a page name (any language, any case)
function find(page, label) {
    const p = String(page || "").trim().toLowerCase();
    if (!p) return null;
    return leaves().find(l => l.entry.id === p || (l.entry.aliases || []).includes(p)
                         || (label && label(l.entry).toLowerCase() === p)
                         || (l.entry.name || []).some(n => n.toLowerCase() === p)) || null;
}
