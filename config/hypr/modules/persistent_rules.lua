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

-- Chatgpt
hl.window_rule({
    name  = "persist_chatgpt",
    match = {
        class = "^Chatgpt$",
    },
    float = false,
})

-- com.mojang.minecraft
hl.window_rule({
    name  = "persist_com_mojang_minecraft",
    match = {
        class = "^com\\.mojang\\.minecraft$",
    },
    float = true,
})

-- dev.vencord.Vesktop
hl.window_rule({
    name  = "persist_dev_vencord_vesktop",
    match = {
        class = "^dev\\.vencord\\.Vesktop$",
    },
    float = true,
})

-- firefox-bin
hl.window_rule({
    name  = "persist_firefox_bin",
    match = {
        class = "^firefox\\-bin$",
    },
    float = true,
})

-- kitty
hl.window_rule({
    name  = "persist_kitty",
    match = {
        class = "^kitty$",
    },
    float = true,
})

-- md.obsidian.Obsidian
hl.window_rule({
    name  = "persist_md_obsidian_obsidian",
    match = {
        class = "^md\\.obsidian\\.Obsidian$",
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

-- org.bwm.menu
hl.window_rule({
    name  = "persist_org_bwm_menu",
    match = {
        class = "^org\\.bwm\\.menu$",
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

-- org.kde.dolphin
hl.window_rule({
    name  = "persist_org_kde_dolphin",
    match = {
        class = "^org\\.kde\\.dolphin$",
    },
    float = false,
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

-- steam_app_3951882152
hl.window_rule({
    name  = "persist_steam_app_3951882152",
    match = {
        class = "^steam_app_3951882152$",
    },
    float = true,
})

-- steam_app_960090
hl.window_rule({
    name  = "persist_steam_app_960090",
    match = {
        class = "^steam_app_960090$",
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

-- Steam (Grand Theft Auto: San Andreas - The Definitive Edition)
hl.window_rule({
    name  = "persist_steam_grand_theft_auto_san_andreas_the_definitive_edition",
    match = {
        class = "^steam$",
        title = "^Grand\\ Theft\\ Auto:\\ San\\ Andreas\\ \\-\\ The\\ Definitive\\ Edition$",
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

-- virt-manager
hl.window_rule({
    name  = "persist_virt_manager",
    match = {
        class = "^virt\\-manager$",
    },
    float = true,
})

return {}
