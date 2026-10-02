------------------
---- MONITORS ----
------------------

-- See https://wiki.hypr.land/Configuring/Basics/Monitors/
hl.monitor({
    output   = "DP-2",
    mode     = "1920x1080@144",
    position = "0x1080", -- Alineado abajo a la izquierda (borde inferior en Y=2160)
    scale    = "auto",
})
hl.monitor({
    output   = "DP-1",
    mode     = "preferred",
    position = "1920x0",
    scale    = "auto",
})

-------------------------
---- WORKSPACE RULES ----
-------------------------

-- Workspaces 1 al 9 vinculados al monitor principal (1080p / DP-2)
for i = 1, 9 do
    hl.workspace_rule({
        workspace = tostring(i),
        monitor   = "DP-2",
        default   = (i == 1),
    })
end

-- Workspace 10 vinculado al monitor secundario (4K / DP-1)
hl.workspace_rule({
    workspace = "10",
    monitor   = "DP-1",
    default   = true,
})

