// SPDX-FileCopyrightText: 2026 BWM
// SPDX-License-Identifier: GPL-2.0-or-later
//
// Protocolo de bwm-decorator (fase 6a de docs/BREEZE_PLAN.md). Lo usan el auxiliar, el plugin
// breezebars (F6b) y tests/bwm_decorator_client.py. Descripción completa en PROTOCOL.md.
//
// Socket Unix SOCK_SEQPACKET en $XDG_RUNTIME_DIR/bwm-decorator.sock: cada paquete es un mensaje
// completo. Enteros y reales little-endian; cadenas = u32 longitud + UTF-8. Los búferes (memfd)
// viajan como SCM_RIGHTS en el mismo paquete que el mensaje que los anuncia.
#pragma once

#include <cstdint>

namespace BwmDeco {

constexpr uint32_t Magic = 0x444D5742; // "BWMD"
constexpr uint16_t Version = 1;

struct Header {
    uint32_t magic;
    uint16_t version;
    uint16_t type;
    uint32_t window;  // id de ventana elegido por el cliente (0 = mensaje global)
    uint32_t size;    // bytes de carga útil tras la cabecera
};
static_assert(sizeof(Header) == 16);

enum ClientMessage : uint16_t {
    Hello = 1,          // u32 versión del cliente
    CreateWindow = 2,   // WindowState
    UpdateWindow = 3,   // WindowState
    DestroyWindow = 4,  // —
    Pointer = 5,        // u32 kind, f64 x, f64 y, u32 button, u32 buttons, f64 angleDeltaY
    Ping = 6,           // —
};

enum ServerMessage : uint16_t {
    HelloAck = 101,     // u32 versión, string plugin, string tema
    Geometry = 102,     // ver PROTOCOL.md
    Frame = 103,        // ver PROTOCOL.md (+ memfd si hasFd)
    Shadow = 104,       // ver PROTOCOL.md (+ memfd si hasFd)
    Request = 105,      // u32 kind, u32 arg, f64 x, f64 y, f64 w, f64 h, string text
    Error = 106,        // string
    Reconfigured = 107, // string plugin, string tema
    Pong = 108,
    SectionUnderMouse = 109, // u32 Qt::WindowFrameSection (para mover o redimensionar)
    PointerResult = 110,     // u32 kind, u32 accepted, u32 section, u32 button (respuesta a pulsar/soltar/rueda)
};

// Banderas de WindowState
enum WindowFlag : uint32_t {
    Active = 1u << 0,
    MaximizedHorizontally = 1u << 1,
    MaximizedVertically = 1u << 2,
    OnAllDesktops = 1u << 3,
    KeepAbove = 1u << 4,
    KeepBelow = 1u << 5,
    Shaded = 1u << 6,
    Closeable = 1u << 7,
    Maximizeable = 1u << 8,
    Minimizeable = 1u << 9,
    Moveable = 1u << 10,
    Resizeable = 1u << 11,
    Shadeable = 1u << 12,
    Modal = 1u << 13,
    ProvidesContextHelp = 1u << 14,
    ExcludedFromCapture = 1u << 15,
};

// Pointer.kind
enum PointerKind : uint32_t {
    Motion = 1,
    Leave = 2,
    Press = 3,
    Release = 4,
    Wheel = 5,
};

// Request.kind
enum RequestKind : uint32_t {
    Close = 1,
    ToggleMaximization = 2,   // arg = botones de Qt (1 izquierdo, 2 derecho, 4 central)
    Minimize = 3,
    ShowWindowMenu = 4,       // rect en coordenadas lógicas de la decoración
    ShowToolTip = 5,          // text
    HideToolTip = 6,
    ToggleKeepAbove = 7,
    ToggleKeepBelow = 8,
    ToggleOnAllDesktops = 9,
    ToggleShade = 10,
    ContextHelp = 11,
    ShowApplicationMenu = 12, // rect, arg = id de acción
    ToggleExcludeFromCapture = 13,
};

} // namespace BwmDeco
