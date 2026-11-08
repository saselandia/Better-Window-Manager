-- Animaciones de Breeze (Kde plasma): las que BWM usaba antes en todas las skins (curvas de
-- Material Design 3). Lo carga modules/appearance.lua sólo con esta skin.

hl.curve("md3_standard", { type = "bezier", points = { {0.2, 0.0}, {0.0, 1.0} } })
hl.curve("md3_decel",    { type = "bezier", points = { {0.05, 0.7}, {0.1, 1.0} } })
hl.curve("md3_accel",    { type = "bezier", points = { {0.3, 0.0}, {0.8, 0.15} } })
hl.curve("menu_decel",   { type = "bezier", points = { {0.1, 1.0}, {0.0, 1.0} } })

hl.animation({ leaf = "windows",          enabled = true, speed = 3,  bezier = "md3_decel",  style = "popin 60%" })
hl.animation({ leaf = "windowsIn",        enabled = true, speed = 3,  bezier = "md3_decel",  style = "popin 60%" })
hl.animation({ leaf = "windowsOut",       enabled = true, speed = 3,  bezier = "md3_accel",  style = "popin 60%" })
hl.animation({ leaf = "border",           enabled = true, speed = 10, bezier = "default" })
hl.animation({ leaf = "fade",             enabled = true, speed = 3,  bezier = "md3_decel" })
hl.animation({ leaf = "fadeIn",           enabled = true, speed = 3,  bezier = "md3_decel" })
hl.animation({ leaf = "fadeOut",          enabled = true, speed = 3,  bezier = "md3_accel" })
hl.animation({ leaf = "workspaces",       enabled = true, speed = 4,  bezier = "menu_decel", style = "slide" })
hl.animation({ leaf = "workspacesIn",     enabled = true, speed = 4,  bezier = "menu_decel", style = "slide" })
hl.animation({ leaf = "workspacesOut",    enabled = true, speed = 4,  bezier = "menu_decel", style = "slide" })
hl.animation({ leaf = "specialWorkspace", enabled = true, speed = 3,  bezier = "md3_decel",  style = "slidevert" })
