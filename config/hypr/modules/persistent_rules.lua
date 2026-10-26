-- =============================================================================
-- REGLAS PERSISTENTES DE VENTANAS (Generadas dinámicamente con ALT + Q)
-- Archivo gestionado automáticamente por toggle-float-persistent.py
-- =============================================================================

-- antigravity-ide
hl.window_rule({
    name  = "persist_antigravity_ide",
    match = {
        class = "^antigravity\\-ide$",
    },
    float = true,
})

-- com.mojang.minecraft
hl.window_rule({
    name  = "persist_com_mojang_minecraft",
    match = {
        class = "^com\\.mojang\\.minecraft$",
    },
    float = true,
})

-- Minecraft* 26.2
hl.window_rule({
    name  = "persist_minecraft_26_2",
    match = {
        class = "^Minecraft\\*\\ 26\\.2$",
    },
    float = true,
})

-- org.gnome.Nautilus
hl.window_rule({
    name  = "persist_org_gnome_nautilus",
    match = {
        class = "^org\\.gnome\\.Nautilus$",
    },
    float = true,
})

-- org.quickshell
hl.window_rule({
    name  = "persist_org_quickshell",
    match = {
        class = "^org\\.quickshell$",
    },
    float = true,
})

-- steam_app_22370
hl.window_rule({
    name  = "persist_steam_app_22370",
    match = {
        class = "^steam_app_22370$",
    },
    float = false,
})

-- steam_app_413150
hl.window_rule({
    name  = "persist_steam_app_413150",
    match = {
        class = "^steam_app_413150$",
    },
    float = false,
})

-- Steam (Amigos / Chat)
hl.window_rule({
    name  = "persist_steam_friends",
    match = {
        class = "^steam$",
        title = "(?i).*(friends|amigos|chat).*",
    },
    float = true,
})

-- Steam (Ventana Principal)
hl.window_rule({
    name  = "persist_steam_main",
    match = {
        class = "^steam$",
        title = "^Steam$",
    },
    float = false,
})

-- Steam (Sign in to Steam)
hl.window_rule({
    name  = "persist_steam_sign_in_to_steam",
    match = {
        class = "^steam$",
        title = "^Sign\\ in\\ to\\ Steam$",
    },
    float = false,
})

-- Steam (Steam - Browser)
hl.window_rule({
    name  = "persist_steam_steam_browser",
    match = {
        class = "^steam$",
        title = "^Steam\\ \\-\\ Browser$",
    },
    float = true,
})

-- virt-manager
hl.window_rule({
    name  = "persist_virt_manager",
    match = {
        class = "^virt\\-manager$",
    },
    float = false,
})

return {}
