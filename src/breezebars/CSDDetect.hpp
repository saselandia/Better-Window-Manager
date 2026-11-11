#pragma once
#include <cstdint>
#include <string>
#include "CSDLogic.hpp"
#include <hyprland/src/desktop/DesktopTypes.hpp>
struct SDecoDetection {
    BwmCsd::Input observed;
    bool clientDraws=true;
    bool ready=true;
    uint32_t xdgRequested=0, kdeRequested=0, sent=0, applied=0;
    std::string reason;
};
SDecoDetection detectDecorations(PHLWINDOW w);
void initDecorationDetection();
void refreshDecorationDetection();
void closeDecorationDetection();

// Standard X11 interactive move request, handled by the compositor side of Breeze.
void handleClientMoveResize(PHLWINDOW w, uint32_t direction, uint32_t button);
