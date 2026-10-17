-- =============================================================================
-- REGLAS PERSISTENTES DE VENTANAS (Generadas dinámicamente con ALT + Q)
-- Archivo gestionado automáticamente por toggle-float-persistent.py
-- =============================================================================

-- com.mojang.minecraft
hl.window_rule({
    name  = "persist_com_mojang_minecraft",
    match = {
        class = "^com\\.mojang\\.minecraft$",
    },
    float = true,
})

-- firefox-bin
hl.window_rule({
    name  = "persist_firefox_bin",
    match = {
        class = "^firefox\\-bin$",
    },
    float = false,
})

-- Minecraft* 26.2
hl.window_rule({
    name  = "persist_minecraft_26_2",
    match = {
        class = "^Minecraft\\*\\ 26\\.2$",
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

return {}
