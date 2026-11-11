#pragma once
#include <cstdint>
// BWM: _NET_WM_MOVERESIZE move is a client request, never a guessed titlebar rectangle.
namespace BwmCsd {
constexpr bool acceptMoveRequest(uint32_t direction, uint32_t button, bool leftHeld,
                                 bool mapped, bool floating, bool fullscreen, bool underPointer) {
    return direction == 8 && button == 1 && leftHeld && mapped && floating && !fullscreen && underPointer;
}
}
