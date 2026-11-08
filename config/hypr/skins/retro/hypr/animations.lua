-- Animaciones de Retro: copia de Omarchy (basecamp/omarchy, rama quattro, 598e4eb, MIT)
-- default/hypr/looknfeel.lua (curvas y animaciones), qconsole.lua (workspaces especiales)
-- y apps/omarchy-shell.lua + apps/screenshot-selection.lua (capas sin animación).
-- Lo carga modules/appearance.lua sólo con esta skin.

-- Default animations, see https://wiki.hypr.land/Configuring/Advanced-and-Cool/Animations/
hl.curve("easeOutQuint", { type = "bezier", points = { { 0.23, 1 }, { 0.32, 1 } } })
hl.curve("easeInOutCubic", { type = "bezier", points = { { 0.65, 0.05 }, { 0.36, 1 } } })
hl.curve("linear", { type = "bezier", points = { { 0, 0 }, { 1, 1 } } })
hl.curve("almostLinear", { type = "bezier", points = { { 0.5, 0.5 }, { 0.75, 1.0 } } })
hl.curve("quick", { type = "bezier", points = { { 0.15, 0 }, { 0.1, 1 } } })

-- Speed is in tenths of a second. These are the animations from before #16889 with every
-- duration cut by a fifth: the 250ms motion-rules timings felt rushed, the originals a touch slow.
hl.animation({ leaf = "global", enabled = true, speed = 8, bezier = "default" })
hl.animation({ leaf = "border", enabled = true, speed = 4.31, bezier = "easeOutQuint" })
hl.animation({ leaf = "windows", enabled = true, speed = 3.03, bezier = "easeOutQuint" })
hl.animation({ leaf = "windowsIn", enabled = true, speed = 3.28, bezier = "easeOutQuint", style = "popin 87%" })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 1.19, bezier = "linear", style = "popin 87%" })
hl.animation({ leaf = "fadeIn", enabled = true, speed = 1.38, bezier = "almostLinear" })
hl.animation({ leaf = "fadeOut", enabled = true, speed = 1.17, bezier = "almostLinear" })
hl.animation({ leaf = "fade", enabled = true, speed = 2.42, bezier = "quick" })
hl.animation({ leaf = "fadeSwitch", enabled = false })
hl.animation({ leaf = "layers", enabled = true, speed = 3.05, bezier = "easeOutQuint" })
hl.animation({ leaf = "layersIn", enabled = true, speed = 3.2, bezier = "easeOutQuint", style = "fade" })
hl.animation({ leaf = "layersOut", enabled = true, speed = 1.2, bezier = "linear", style = "fade" })
hl.animation({ leaf = "fadeLayersIn", enabled = true, speed = 1.43, bezier = "almostLinear" })
hl.animation({ leaf = "fadeLayersOut", enabled = true, speed = 1.11, bezier = "almostLinear" })
hl.animation({ leaf = "workspaces", enabled = false })

-- qconsole.lua: "slide top" drops a special workspace down into view, and "slide bottom"
-- retracts it back up the way a Quake console does.
hl.animation({ leaf = "specialWorkspaceIn", enabled = true, speed = 3, bezier = "easeOutQuint", style = "slide top" })
hl.animation({ leaf = "specialWorkspaceOut", enabled = true, speed = 2, bezier = "easeOutQuint", style = "slide bottom" })

-- Keep the bar instant: no layer-shell fade/slide animation. (La barra Retro de BWM vive en
-- la capa quickshell:bar; omarchy-bar se deja por si se carga la de Omarchy tal cual.)
hl.layer_rule({ match = { namespace = "^(omarchy-bar|quickshell:bar)$" }, no_anim = true, animation = "none" })

-- Launcher, image selector, emojis, clipboard overlays, the OSD, reminders, the
-- Wi-Fi QR code and keyboard-driven panels should pop without compositor layer
-- animations.
hl.layer_rule({ match = { namespace = "^(omarchy-menu|omarchy-image-selector|omarchy-emojis|omarchy-clipboard|omarchy-keyboard-panel|omarchy-osd|omarchy-reminders|omarchy-network-qr|omarchy-dock|omarchy-dock-apps)$" }, no_anim = true, animation = "none" })

-- The media fades itself, so a compositor fade on the background layer only dips the
-- screen toward the empty desktop during the handoff.
hl.layer_rule({ match = { namespace = "^(omarchy-background|owe-background)$" }, no_anim = true, animation = "none" })

-- Remove the 1px border around the slurp region selection used by recordings, OCR, and QR capture.
hl.layer_rule({ match = { namespace = "selection" }, no_anim = true, animation = "none" })

-- Keep the Omasnap overlay immediate. (En BWM la selección de región estilo omasnap es
-- quickshell:regionSelector.)
hl.layer_rule({ match = { namespace = "^(omasnap|quickshell:regionSelector)$" }, no_anim = true, animation = "none" })
