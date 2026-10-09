-- =============================================================================
-- REGLAS PERSISTENTES DE VENTANAS (Generadas dinámicamente con ALT + Q)
-- Archivo gestionado automáticamente por toggle-float-persistent.py
-- =============================================================================

-- kitty
hl.window_rule({
    name  = "persist_kitty",
    match = {
        class = "^kitty$",
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

return {}
