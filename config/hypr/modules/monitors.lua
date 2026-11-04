------------------
---- MONITORS ----
------------------

-- Archivo gestionado automáticamente por Quickshell Display Settings
-- See https://wiki.hypr.land/Configuring/Basics/Monitors/
-- Por descripción (desc:), no por conector: los nombres DP-N cambian si cambia el orden
-- en que arrancan las GPU (iGPU AMD / NVIDIA) y entonces las reglas caen en el monitor equivocado.

-- DP-1
hl.monitor({
    output   = "desc:LG Electronics LG ULTRAFINE 405NTVS2J655",
    mode     = "3840x2160@60",
    position = "2560x0",
    scale    = "1",
})

-- DP-2
hl.monitor({
    output   = "desc:Micro-Star Int'l Co. Ltd. MAG 274Q X24 0x01010101",
    mode     = "2560x1440@240",
    position = "0x720",
    scale    = "1",
})

-------------------------
---- WORKSPACE RULES ----
-------------------------

-- Monitor Secundario: Workspace 10 persistente
hl.workspace_rule({
    workspace = "10",
    monitor   = "desc:LG Electronics LG ULTRAFINE 405NTVS2J655",
    default   = true,
    persistent = true,
})

-- Monitor Principal (Workspaces 1 al 9)
for i = 1, 9 do
    hl.workspace_rule({
        workspace = tostring(i),
        monitor   = "desc:Micro-Star Int'l Co. Ltd. MAG 274Q X24 0x01010101",
        default   = (i == 1),
        persistent = (i == 1),
    })
end
