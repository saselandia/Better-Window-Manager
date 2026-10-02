-- =============================================================================
-- REGLAS PERSISTENTES DE VENTANAS (Generadas dinámicamente con ALT + Q)
-- Archivo gestionado automáticamente por toggle-float-persistent.py
-- =============================================================================

-- firefox-bin
hl.window_rule({
    name  = "persist_firefox_bin",
    match = {
        class = "^firefox\\-bin$",
    },
    float = false,
})

-- kitty
hl.window_rule({
    name  = "persist_kitty",
    match = {
        class = "^kitty$",
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

-- spotify
hl.window_rule({
    name  = "persist_spotify",
    match = {
        class = "^spotify$",
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

-- Steam (Amigos / Chat)
hl.window_rule({
    name  = "persist_steam_friends",
    match = {
        class = "^steam$",
        title = "(?i).*(friends|amigos|chat).*",
    },
    float = true,
})

return {}
