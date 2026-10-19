------------------
---- MONITORS ----
------------------

-- Archivo gestionado automáticamente por Quickshell Display Settings
-- See https://wiki.hypr.land/Configuring/Basics/Monitors/

-- Monitor Principal: 4K (LG ULTRAFINE)
hl.monitor({
    output   = "desc:LG Electronics LG ULTRAFINE 405NTVS2J655",
    mode     = "3840x2160@60.0",
    position = "1920x0",
    scale    = "1.0",
})
hl.monitor({
    output   = "DP-1",
    mode     = "3840x2160@60.0",
    position = "1920x0",
    scale    = "1.0",
})

-- Monitor Secundario: 1080p (HP X24ih) - Abajo a la izquierda del 4K
hl.monitor({
    output   = "desc:HP Inc. HP X24ih 1CR1420TD4",
    mode     = "1920x1080@144.0",
    position = "0x1080",
    scale    = "1.0",
})
hl.monitor({
    output   = "DP-2",
    mode     = "1920x1080@144.0",
    position = "0x1080",
    scale    = "1.0",
})

-------------------------
---- WORKSPACE RULES ----
-------------------------

-- Monitor Secundario: Workspace 10 persistente
hl.workspace_rule({
    workspace  = "10",
    monitor    = "desc:HP Inc. HP X24ih 1CR1420TD4",
    default    = true,
    persistent = true,
})
hl.workspace_rule({
    workspace  = "10",
    monitor    = "DP-2",
    default    = true,
    persistent = true,
})

-- Monitor Principal: Workspaces 1 al 9 (Workspace 1 persistente)
for i = 1, 9 do
    hl.workspace_rule({
        workspace  = tostring(i),
        monitor    = "desc:LG Electronics LG ULTRAFINE 405NTVS2J655",
        default    = (i == 1),
        persistent = (i == 1),
    })
    hl.workspace_rule({
        workspace  = tostring(i),
        monitor    = "DP-1",
        default    = (i == 1),
        persistent = (i == 1),
    })
end
