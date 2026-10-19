------------------
---- MONITORS ----
------------------

-- Archivo gestionado automáticamente por Quickshell Display Settings
-- See https://wiki.hypr.land/Configuring/Basics/Monitors/
hl.monitor({
    output   = "DP-2",
    mode     = "3840x2160@60.0",
    position = "1920x0",
    scale    = "1.0",
})
hl.monitor({
    output   = "DP-3",
    mode     = "1920x1080@144.0",
    position = "0x1080",
    scale    = "1.0",
})

-------------------------
---- WORKSPACE RULES ----
-------------------------

-- Workspace 10 vinculado al monitor (DP-2) [Secundario]
hl.workspace_rule({
    workspace = "10",
    monitor   = "DP-2",
    default   = true,
})

-- Workspaces 1 al 9 vinculados al monitor (DP-3) [Principal]
for i = 1, 9 do
    hl.workspace_rule({
        workspace = tostring(i),
        monitor   = "DP-3",
        default   = (i == 1),
    })
end
