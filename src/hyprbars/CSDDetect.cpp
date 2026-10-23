// Autodetección de decoraciones: decide si una ventana dibuja sus propios
// botones (CSD) o espera que el compositor le ponga barra (SSD), leyendo lo que
// el cliente ha pedido por los protocolos Wayland, en vez de una lista de clases.
#include <any>
#include <sstream>
#include <fstream>
#include <iostream>
#include <functional>
#include <optional>
#include <variant>
#include <map>
#include <set>
#include <list>
#include <array>
#include <chrono>
#include <mutex>
#include <span>
#include <ranges>
#include <algorithm>
#include <expected>
#include <filesystem>
#include <regex>
#include <memory>
#include <vector>
#include <unordered_map>
#include <string>
#include <format>
#include <hyprutils/memory/SharedPtr.hpp>
#include <hyprutils/memory/UniquePtr.hpp>
#include <hyprutils/memory/WeakPtr.hpp>
#include <wayland-server.h>
#include <xcb/xcb.h>
#include <xcb/xcbext.h>
#include <poll.h>
#include <cstdlib>

// Las tablas de decoraciones de Hyprland son privadas: hay que leerlas directamente.
#define private public
#include <hyprland/src/protocols/XDGShell.hpp>
#include <hyprland/src/protocols/XDGDecoration.hpp>
#include <hyprland/src/protocols/ServerDecorationKDE.hpp>
#undef private

#include <hyprland/src/desktop/view/Window.hpp>
#include <hyprland/src/xwayland/XSurface.hpp>

#include "CSDDetect.hpp"

// _MOTIF_WM_HINTS: flags, functions, decorations, input_mode, status
static constexpr uint32_t MWM_HINTS_DECORATIONS = 1 << 1;

// Conexión propia a XWayland, solo para leer propiedades. Nunca se bloquea más de
// ~60 ms: si XWayland no contesta, se asume "sin datos" y se pone barra.
static xcb_connection_t* conn = nullptr;
static std::string       forDpy;

void closeDecorationDetection() {
    if (conn)
        xcb_disconnect(conn);
    conn = nullptr;
}

static xcb_connection_t* xconn() {
    const char*              dpy = getenv("DISPLAY");
    if (!dpy || !*dpy)
        return nullptr;
    if (conn && (xcb_connection_has_error(conn) || forDpy != dpy)) {
        xcb_disconnect(conn);
        conn = nullptr;
    }
    if (!conn) {
        conn = xcb_connect(dpy, nullptr);
        if (xcb_connection_has_error(conn)) {
            xcb_disconnect(conn);
            conn = nullptr;
            return nullptr;
        }
        forDpy = dpy;
    }
    return conn;
}

template <typename R>
static R* waitReply(xcb_connection_t* c, unsigned int sequence) {
    xcb_flush(c);
    for (int tries = 0; tries < 6; ++tries) {
        void*                rep = nullptr;
        xcb_generic_error_t* err = nullptr;
        if (xcb_poll_for_reply(c, sequence, &rep, &err)) {
            free(err);
            return (R*)rep;
        }
        pollfd pfd = {.fd = xcb_get_file_descriptor(c), .events = POLLIN, .revents = 0};
        ::poll(&pfd, 1, 10);
    }
    xcb_discard_reply(c, sequence);
    return nullptr;
}

// -1 = sin información, 0 = no quiere decoraciones del WM, 1 = sí las quiere
static int x11WantsDecorations(uint32_t xid) {
    auto c = xconn();
    if (!c || !xid)
        return -1;

    static xcb_atom_t motif = XCB_ATOM_NONE;
    if (motif == XCB_ATOM_NONE) {
        auto ck  = xcb_intern_atom(c, 1, 15, "_MOTIF_WM_HINTS");
        auto rep = waitReply<xcb_intern_atom_reply_t>(c, ck.sequence);
        if (!rep)
            return -1;
        motif = rep->atom;
        free(rep);
        if (motif == XCB_ATOM_NONE)
            return -1;
    }

    auto ck  = xcb_get_property(c, 0, xid, motif, XCB_ATOM_ANY, 0, 5);
    auto rep = waitReply<xcb_get_property_reply_t>(c, ck.sequence);
    if (!rep)
        return -1;

    int result = -1;
    if (xcb_get_property_value_length(rep) >= 12) {
        auto v = (uint32_t*)xcb_get_property_value(rep);
        if (v[0] & MWM_HINTS_DECORATIONS)
            result = v[2] != 0 ? 1 : 0;
    }
    free(rep);
    return result;
}

// Valores de los enums de ambos protocolos: 1 = cliente, 2 = servidor.
static constexpr uint32_t MODE_CLIENT = 1;
static constexpr uint32_t MODE_SERVER = 2;

static wl_resource* toplevelResource(PHLWINDOW w) {
    auto xdg = w->m_xdgSurface.lock();
    if (!xdg)
        return nullptr;
    auto top = xdg->m_toplevel.lock();
    if (!top || !top->m_resource)
        return nullptr;
    return top->m_resource->resource();
}

SDecoDetection detectDecorations(PHLWINDOW w) {
    SDecoDetection r;
    if (!w)
        return r;

    if (w->m_isX11) {
        // XWayland: _MOTIF_WM_HINTS sin decoraciones => la app dibuja la suya (Steam, juegos...)
        auto xs    = w->m_xwaylandSurface.lock();
        int  wants = xs ? x11WantsDecorations(xs->m_xID) : -1;
        if (w->m_X11DoesntWantBorders || wants == 0) {
            r.clientDraws = true;
            r.reason      = "x11 _MOTIF_WM_HINTS: sin decoraciones del WM";
        } else {
            r.clientDraws = false;
            r.reason      = wants == 1 ? "x11 _MOTIF_WM_HINTS: pide decoraciones" : "x11 sin hints (barra por defecto)";
        }
        return r;
    }

    if (PROTO::xdgDecoration) {
        if (auto res = toplevelResource(w)) {
            auto it = PROTO::xdgDecoration->m_decorations.find(res);
            if (it != PROTO::xdgDecoration->m_decorations.end() && it->second) {
                r.xdgRequested = it->second->mostRecentlyRequested;
                if (r.xdgRequested == MODE_CLIENT) {
                    r.clientDraws = true;
                    r.reason      = "xdg-decoration: pide client-side";
                    return r;
                }
                // pide server-side o no especifica (acepta lo que manda el compositor)
                r.clientDraws = false;
                r.reason      = r.xdgRequested == MODE_SERVER ? "xdg-decoration: pide server-side" : "xdg-decoration: sin preferencia";
                return r;
            }
        }
    }

    if (PROTO::serverDecorationKDE) {
        auto surf = w->resource();
        for (auto& d : PROTO::serverDecorationKDE->m_decos) {
            if (!d || d->m_surf != surf)
                continue;
            r.kdeRequested = d->m_mostRecentlyRequested;
            r.clientDraws  = r.kdeRequested == MODE_CLIENT;
            r.reason       = r.clientDraws ? "kde-server-decoration: pide client-side" : "kde-server-decoration: pide server-side";
            return r;
        }
    }

    // El cliente no negocia decoraciones: no sabe que el compositor puede
    // dibujarlas, así que trae las suyas (GTK con headerbar, Electron, Chromium...).
    r.clientDraws = true;
    r.reason      = "no negocia decoraciones (CSD propia)";
    return r;
}
