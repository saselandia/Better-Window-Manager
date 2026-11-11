#pragma once

#include <cstdint>
#include <string>
#include <hyprland/src/desktop/DesktopTypes.hpp>

struct SDecoDetection {
    bool        clientDraws  = false; // true => la ventana trae sus propios botones, no ponerle barra
    uint32_t    xdgRequested = 0;     // modo pedido por xdg-decoration (0 = sin objeto/sin pedir)
    uint32_t    kdeRequested = 0;     // modo pedido por org_kde_kwin_server_decoration
    std::string reason;
};

SDecoDetection detectDecorations(PHLWINDOW w);
void           closeDecorationDetection();
