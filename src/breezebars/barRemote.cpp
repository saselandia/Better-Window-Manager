// La barra dibujada por bwm-decorator (F6b de docs/BREEZE_PLAN.md): el plugin es el pegamento entre
// Hyprland y la decoración de KDE que corre en el auxiliar. Coloca y reserva los bordes que dice la
// decoración, compone sus imágenes (sólo sube lo dañado), dibuja su sombra, le pasa el puntero y
// ejecuta lo que pide (cerrar, maximizar, minimizar, menú, tooltip). Como en KWin, una pulsación que
// ningún botón acepta es del compositor: mover, redimensionar, menú o doble clic.
#include "barDeco.hpp"
#include "barRemote.hpp"
#include "DecoClient.hpp"
#include "SnapHelper.hpp"

#include <hyprland/src/Compositor.hpp>
#include <hyprland/src/config/shared/actions/ConfigActions.hpp>
#include <hyprland/src/config/shared/complex/ComplexDataTypes.hpp>
#include <hyprland/src/config/supplementary/executor/Executor.hpp>
#include <hyprland/src/desktop/state/FocusState.hpp>
#include <hyprland/src/desktop/state/ViewHitTester.hpp>
#include <hyprland/src/desktop/state/ViewState.hpp>
#include <hyprland/src/desktop/state/WindowState.hpp>
#include <hyprland/src/desktop/view/Window.hpp>
#include <hyprland/src/layout/LayoutManager.hpp>
#include <hyprland/src/layout/target/Target.hpp>
#include <hyprland/src/managers/KeybindManager.hpp>
#include <hyprland/src/managers/SeatManager.hpp>
#include <hyprland/src/managers/fullscreen/FullscreenController.hpp>
#include <hyprland/src/managers/input/InputManager.hpp>
#include <hyprland/src/output/Monitor.hpp>
#include <hyprland/src/protocols/LayerShell.hpp>
#include <hyprland/src/render/OpenGL.hpp>
#include <hyprland/src/render/Renderer.hpp>
#include <hyprland/src/state/MonitorState.hpp>

#include <drm_fourcc.h>
#include <fstream>
#include <linux/input-event-codes.h>
#include <sstream>
#include <sys/mman.h>
#include <unistd.h>

using namespace BwmDeco;
using namespace Render::GL;

static std::string homeDir() {
    const char* h = getenv("HOME");
    return h ? h : "";
}

static std::string windowAddress(PHLWINDOW w) {
    return std::format("0x{:x}", reinterpret_cast<uintptr_t>(w.get()));
}

static void repositionShadow(PHLWINDOW w) {
    if (!w)
        return;
    for (auto& d : w->m_windowDecorations)
        if (d && d->getDisplayName() == "BreezeShadow")
            g_pDecorationPositioner->repositionDeco(d.get());
}

static CBox monitorLocal(const CBox& global, PHLMONITOR pMonitor) {
    CBox box = global;
    box.translate(-pMonitor->m_position).scale(pMonitor->m_scale).round();
    return box;
}

// ───────────────────────────────────────────────────────── estado y conexión

bool CHyprBar::remoteActive() {
    return !m_hidden && g_pGlobalState->config.enabled->value() && g_pDecoClient && g_pDecoClient->ready() && m_remote.created && m_remote.geometry &&
        m_remote.hasFrame && m_remote.width > 0 && m_remote.height > 0;
}

void CHyprBar::releaseRemoteBuffers() {
    for (auto& b : m_remote.buffers) {
        if (b.map)
            munmap(b.map, b.size);
        b = {};
    }
}

void CHyprBar::onRemoteReady() {
    m_remote.created  = false;
    m_remote.lastSent.reset();
    damageEntire();
}

// Vuelve al estado sin decoración remota conservando lo que hay que deshacer: el id, la colocación
// actual (para que updateRemotePositioning vea el cambio) y el redondeo que se forzó.
static void resetRemote(SRemoteState& r) {
    SRemoteState fresh;
    fresh.id                = r.id;
    fresh.positionedRemote  = r.positionedRemote;
    fresh.positionedBorders = r.positionedBorders;
    fresh.roundingOverride  = r.roundingOverride;
    r                       = std::move(fresh);
}

void CHyprBar::onRemoteLost() {
    releaseRemoteBuffers();
    resetRemote(m_remote);
    if (m_bResizing && g_layoutManager->dragController()->target())
        g_layoutManager->endDragTarget();
    m_bResizing = false;
    applyRoundingOverride(-1);
    hideDecorationToolTip();
    updateRemotePositioning();
    damageEntire();
}

void CHyprBar::onRemoteReconfigured() {
    // La decoración se recrea en el auxiliar: llegarán Geometry y Frame nuevos
    m_remote.lastSent.reset();
    damageEntire();
}

void CHyprBar::destroyRemote() {
    if (m_remote.created && g_pDecoClient)
        g_pDecoClient->send(destroyWindow(m_remote.id));
    releaseRemoteBuffers();
    resetRemote(m_remote);
    applyRoundingOverride(-1);
    updateRemotePositioning();
}

SWindowState CHyprBar::currentRemoteState() {
    SWindowState s;
    const auto   PW = m_pWindow.lock();
    if (!PW)
        return s;
    const auto size = PW->size(Desktop::View::IGeometric::GEOMETRIC_GOAL);
    s.width         = std::max(1.0, size.x);
    s.height        = std::max(1.0, size.y);
    const auto MON  = PW->m_monitor.lock();
    s.scale         = MON ? MON->m_scale : 1.0;

    uint32_t flags = Closeable | Maximizeable | Minimizeable | Moveable | Resizeable;
    if (PW == Desktop::focusState()->window())
        flags |= Active;
    // Modo de maximizado de kwin-window.py (F8), en etiquetas de la ventana; el de Hyprland cuenta como completo
    const bool FS   = Fullscreen::controller()->isFullscreen(PW);
    const auto TAGS = PW->m_ruleApplicator ? &PW->m_ruleApplicator->m_tagKeeper : nullptr;
    if (FS || (TAGS && TAGS->isTagged("bwm-max-h")))
        flags |= MaximizedHorizontally;
    if (FS || (TAGS && TAGS->isTagged("bwm-max-v")))
        flags |= MaximizedVertically;
    if (PW->m_pinned)
        flags |= OnAllDesktops;
    s.flags = flags;

    // Bordes de la pantalla junto a la ventana (Breeze quita bordes o esquinas ahí)
    if (MON && m_remote.geometry) {
        const auto& b    = m_remote.geometry->borders;
        const auto  pos  = PW->position(Desktop::View::IGeometric::GEOMETRIC_GOAL);
        const CBox  area = MON->m_reservedArea.apply(CBox{MON->m_position, MON->m_size});
        const CBox  fr{pos.x - b.left, pos.y - b.top, size.x + b.left + b.right, size.y + b.top + b.bottom};
        uint32_t    edges = 0;
        if (std::abs(fr.y - area.y) < 1)
            edges |= 1;
        if (std::abs(fr.x - area.x) < 1)
            edges |= 2;
        if (std::abs(fr.x + fr.w - (area.x + area.w)) < 1)
            edges |= 4;
        if (std::abs(fr.y + fr.h - (area.y + area.h)) < 1)
            edges |= 8;
        s.edges = edges;
    }
    s.caption  = PW->m_title;
    s.appClass = PW->m_class;
    return s;
}

// Lo llama draw() en cada fotograma: crea la ventana remota y envía el estado si cambió.
void CHyprBar::syncRemote() {
    if (!g_pDecoClient)
        return;
    if (m_hidden || !g_pGlobalState->config.enabled->value()) {
        if (m_remote.created || m_remote.geometry)
            destroyRemote();
        return;
    }
    if (!Desktop::View::validMapped(m_pWindow))
        return;
    g_pDecoClient->ensureConnected();
    if (!g_pDecoClient->ready())
        return;
    if (m_remote.id == 0)
        m_remote.id = g_pDecoClient->newId();
    const auto st = currentRemoteState();
    if (!m_remote.created) {
        if (g_pDecoClient->send(windowState(true, m_remote.id, st))) {
            m_remote.created  = true;
            m_remote.lastSent = st;
        }
    } else if (!m_remote.lastSent || *m_remote.lastSent != st) {
        if (g_pDecoClient->send(windowState(false, m_remote.id, st)))
            m_remote.lastSent = st;
    }
}

// Cambia la colocación entre la barra plana (STICKY arriba) y los bordes de la decoración (ABSOLUTE).
void CHyprBar::updateRemotePositioning() {
    const bool                       active  = remoteActive();
    std::optional<BwmDeco::SExtents> borders = active ? std::optional{m_remote.geometry->borders} : std::nullopt;
    if (active == m_remote.positionedRemote && borders == m_remote.positionedBorders)
        return;
    m_remote.positionedRemote  = active;
    m_remote.positionedBorders = borders;
    g_pDecorationPositioner->repositionDeco(this);
    if (auto PW = m_pWindow.lock(); PW && PW->layoutTarget())
        PW->layoutTarget()->recalc();
    repositionShadow(m_pWindow.lock());
}

// Redondeo del contenido = radio de abajo de la decoración (lo de arriba lo tapa la barra y lo cuadra
// SquareTop.cpp). Con la prioridad más baja: una regla de ventana del usuario sigue mandando.
void CHyprBar::applyRoundingOverride(int value) {
    if (value == m_remote.roundingOverride)
        return;
    auto PW = m_pWindow.lock();
    if (!PW || !PW->m_ruleApplicator)
        return;
    if (value < 0)
        PW->m_ruleApplicator->rounding().unset(Desktop::Types::PRIORITY_LAYOUT);
    else
        PW->m_ruleApplicator->rounding().set(value, Desktop::Types::PRIORITY_LAYOUT);
    m_remote.roundingOverride = value;
    g_pHyprRenderer->damageWindow(PW);
}

// ───────────────────────────────────────────────────────── mensajes del auxiliar

void CHyprBar::onRemoteMessage(const SMessage& msg, int fd) {
    auto closeFd = [&fd] {
        if (fd >= 0)
            close(fd);
        fd = -1;
    };

    if (msg.geometry) {
        const bool first = !m_remote.geometry;
        m_remote.geometry = *msg.geometry;
        const auto& g     = *msg.geometry;
        applyRoundingOverride(static_cast<int>(std::round(std::max(g.radius[2], g.radius[3]))));
        (void)first;
        updateRemotePositioning();
        damageEntire();
    } else if (msg.frame) {
        const SFrame& f = *msg.frame;
        if (f.buffer < 2 && f.hasFd && fd >= 0) {
            auto& buf = m_remote.buffers[f.buffer];
            if (buf.map)
                munmap(buf.map, buf.size);
            buf     = {};
            void* p = f.capacity ? mmap(nullptr, f.capacity, PROT_READ, MAP_SHARED, fd, 0) : MAP_FAILED;
            if (p != MAP_FAILED)
                buf = {p, f.capacity};
        }
        closeFd();
        if (!frameIsSane(f))
            return;
        const auto& buf = m_remote.buffers[f.buffer];
        if (!buf.map || f.capacity > buf.size)
            return;
        const bool resized = f.width != m_remote.width || f.height != m_remote.height || f.stride != m_remote.stride || !m_remote.hasFrame;
        m_remote.pixels.assign(static_cast<uint8_t*>(buf.map), static_cast<uint8_t*>(buf.map) + static_cast<size_t>(f.stride) * f.height);
        m_remote.width  = f.width;
        m_remote.height = f.height;
        m_remote.stride = f.stride;
        m_remote.parts  = f.parts;
        if (resized) {
            m_remote.texture.reset();
            m_remote.pendingDamage.clear();
        } else {
            auto dmg = damageInBuffer(f, false);
            m_remote.pendingDamage.insert(m_remote.pendingDamage.end(), dmg.begin(), dmg.end());
        }
        m_remote.hasFrame = true;
        updateRemotePositioning();
        damageEntire();
    } else if (msg.shadow) {
        const SShadow& s = *msg.shadow;
        if (s.hasFd && fd >= 0 && s.width && s.height) {
            const size_t size = static_cast<size_t>(s.stride) * s.height;
            void*        p    = mmap(nullptr, size, PROT_READ, MAP_SHARED, fd, 0);
            if (p != MAP_FAILED) {
                if (shadowIsSane(s, size)) {
                    m_remote.shadowPixels.assign(static_cast<uint8_t*>(p), static_cast<uint8_t*>(p) + size);
                    m_remote.shadow      = s;
                    m_remote.shadowDirty = true;
                }
                munmap(p, size);
            }
        } else if (!s.hasFd || !s.width || !s.height) {
            m_remote.shadow.reset();
            m_remote.shadowPixels.clear();
            m_remote.shadowTexture.reset();
        }
        closeFd();
        updateRemotePositioning();
        repositionShadow(m_pWindow.lock());
        damageEntire();
    } else if (msg.section) {
        m_remote.section = *msg.section;
    } else if (msg.pointerResult) {
        handlePointerResult(*msg.pointerResult);
    } else if (msg.request) {
        handleRequest(*msg.request);
    }
    closeFd();
}

// ───────────────────────────────────────────────────────── cajas

std::optional<CBox> CHyprBar::contentBoxGlobal(bool forRender) {
    const auto PW = m_pWindow.lock();
    if (!Desktop::View::validMapped(PW))
        return std::nullopt;
    CBox       box        = PW->getWindowMainSurfaceBox();
    const auto PWORKSPACE = PW->m_workspace;
    if (PWORKSPACE && !PW->m_pinned)
        box.translate(PWORKSPACE->m_renderOffset->value());
    if (forRender)
        box.translate(PW->m_floatingOffset);
    return box;
}

std::optional<CBox> CHyprBar::frameBoxGlobal(bool forRender) {
    auto content = contentBoxGlobal(forRender);
    if (!content || !m_remote.geometry)
        return content;
    const auto& b = m_remote.geometry->borders;
    return CBox{content->x - b.left, content->y - b.top, content->w + b.left + b.right, content->h + b.top + b.bottom};
}

// ───────────────────────────────────────────────────────── dibujo

void CHyprBar::uploadRemoteTexture() {
    if (m_remote.pixels.empty())
        return;
    const Vector2D size{static_cast<double>(m_remote.width), static_cast<double>(m_remote.height)};
    if (!m_remote.texture || m_remote.texture->m_size != size) {
        m_remote.texture = g_pHyprRenderer->createTexture(DRM_FORMAT_ARGB8888, m_remote.pixels.data(), m_remote.stride, size);
        m_remote.pendingDamage.clear();
    } else if (!m_remote.pendingDamage.empty()) {
        CRegion region;
        for (const auto& r : m_remote.pendingDamage)
            region.add(CBox{static_cast<double>(r.x), static_cast<double>(r.y), static_cast<double>(r.w), static_cast<double>(r.h)});
        m_remote.texture->update(DRM_FORMAT_ARGB8888, m_remote.pixels.data(), m_remote.stride, region);
        m_remote.pendingDamage.clear();
    }
}

void CHyprBar::renderRemote(PHLMONITOR pMonitor, float a) {
    uploadRemoteTexture();
    auto frame = frameBoxGlobal(true);
    if (!m_remote.texture || !frame || !m_remote.geometry)
        return;

    // La última imagen se estira al marco actual mientras llega la del tamaño nuevo (redimensionar)
    const auto targets = partTargets(SRectD{frame->x, frame->y, frame->w, frame->h}, m_remote.geometry->borders);
    const double W = m_remote.width, H = m_remote.height;
    for (size_t i = 0; i < 4; ++i) {
        const auto& p = m_remote.parts[i];
        const auto& t = targets[i];
        if (p.w == 0 || p.h == 0 || t.w <= 0 || t.h <= 0)
            continue;
        CBox box = monitorLocal(CBox{t.x, t.y, t.w, t.h}, pMonitor);
        if (box.w < 1 || box.h < 1)
            continue;
        CHyprOpenGLImpl::STextureRenderData data;
        data.a                           = a;
        data.allowCustomUV               = true;
        data.primarySurfaceUVTopLeft     = {p.x / W, p.y / H};
        data.primarySurfaceUVBottomRight = {(p.x + p.w) / W, (p.y + p.h) / H};
        g_pHyprOpenGL->renderTexture(m_remote.texture, box, data);
    }

    // Contorno de la decoración (KDecoration3::BorderOutline), por fuera del marco como KWin
    const auto& g = *m_remote.geometry;
    if (g.outlineThickness > 0 && (g.outlineColor >> 24) > 0) {
        double radius = 0;
        for (double r : g.outlineRadius)
            radius = std::max(radius, r);
        CBox box = monitorLocal(*frame, pMonitor);
        Config::CGradientValueData grad(CHyprColor{static_cast<uint64_t>(g.outlineColor)});
        g_pHyprOpenGL->renderBorder(box, grad,
                                    {.round = static_cast<int>(std::round(radius * pMonitor->m_scale)), .roundingPower = 2.F,
                                     .borderSize = std::max(1, static_cast<int>(std::round(g.outlineThickness * pMonitor->m_scale))), .a = a});
    }
}

void CHyprBar::renderShadow(PHLMONITOR pMonitor, float a) {
    if (!m_remote.shadow || m_remote.shadowPixels.empty())
        return;
    const auto& s = *m_remote.shadow;
    if (!m_remote.shadowTexture || m_remote.shadowDirty) {
        m_remote.shadowTexture = g_pHyprRenderer->createTexture(DRM_FORMAT_ARGB8888, m_remote.shadowPixels.data(), s.stride,
                                                                Vector2D{static_cast<double>(s.width), static_cast<double>(s.height)});
        m_remote.shadowDirty   = false;
    }
    auto frame = frameBoxGlobal(true);
    if (!frame || !m_remote.shadowTexture)
        return;
    const double W = s.width / s.dpr, H = s.height / s.dpr;
    for (const auto& q : shadowQuads(SRectD{frame->x, frame->y, frame->w, frame->h}, s)) {
        CBox box = monitorLocal(CBox{q.dst.x, q.dst.y, q.dst.w, q.dst.h}, pMonitor);
        if (box.w < 1 || box.h < 1)
            continue;
        CHyprOpenGLImpl::STextureRenderData data;
        data.a                           = a;
        data.allowCustomUV               = true;
        data.primarySurfaceUVTopLeft     = {q.src.x / W, q.src.y / H};
        data.primarySurfaceUVBottomRight = {(q.src.x + q.src.w) / W, (q.src.y + q.src.h) / H};
        g_pHyprOpenGL->renderTexture(m_remote.shadowTexture, box, data);
    }
}

// ───────────────────────────────────────────────────────── puntero

bool CHyprBar::remoteInputAllowed() {
    auto PW = m_pWindow.lock();
    if (!PW || !PW->m_workspace || !PW->m_workspace->isVisible() || !g_pInputManager->m_exclusiveLSes.empty())
        return false;
    if (g_pSeatManager->m_seatGrab && (!PW->wlSurface() || !g_pSeatManager->m_seatGrab->accepts(PW->wlSurface()->resource())))
        return false;
    return true;
}

bool CHyprBar::remoteHit(const Vector2D& mouse, Vector2D* local) {
    if (!remoteActive() || !remoteInputAllowed())
        return false;
    auto frame   = frameBoxGlobal(false);
    auto content = contentBoxGlobal(false);
    if (!frame || !content || !frame->containsPoint(mouse) || content->containsPoint(mouse))
        return false;
    auto       PW    = m_pWindow.lock();
    const auto AT    = Desktop::CViewHitTester{*Desktop::viewState()}.windowAt(mouse, Desktop::View::RESERVED_EXTENTS | Desktop::View::INPUT_EXTENTS |
                                                                                   Desktop::View::ALLOW_FLOATING);
    if (AT != PW)
        return false;
    // Una capa encima (panel, menú) se queda el puntero
    if (auto MON = PW->m_monitor.lock()) {
        PHLLS    found;
        Vector2D surfaceCoords;
        for (auto layer : {ZWLR_LAYER_SHELL_V1_LAYER_TOP, ZWLR_LAYER_SHELL_V1_LAYER_OVERLAY}) {
            Desktop::CViewHitTester{*Desktop::viewState()}.layerSurfaceAt(mouse, &MON->m_layerSurfaceLayers[layer], &surfaceCoords, &found);
            if (found)
                return false;
        }
    }
    if (local)
        *local = mouse - frame->pos();
    return true;
}

static uint32_t qtButton(uint32_t linuxButton) {
    switch (linuxButton) {
        case BTN_LEFT: return 1;
        case BTN_RIGHT: return 2;
        case BTN_MIDDLE: return 4;
        default: return 0;
    }
}

void CHyprBar::remoteMouseMove(const Vector2D& mouse) {
    if (m_bResizing || m_bDraggingThis || !g_pDecoClient)
        return;
    Vector2D local;
    if (remoteHit(mouse, &local)) {
        if (!m_remote.pointerInside || (local - m_remote.lastPointer).size() >= 0.5) {
            if (g_pDecoClient->send(pointer(m_remote.id, Motion, local.x, local.y, 0, m_remote.buttons, 0)))
                m_remote.lastPointer = local;
            m_remote.pointerInside = true;
        }
    } else if (m_remote.pointerInside) {
        g_pDecoClient->send(pointer(m_remote.id, Leave, -1, -1, 0, m_remote.buttons, 0));
        m_remote.pointerInside = false;
        m_remote.lastPointer   = {-1, -1};
        m_remote.section       = 0;
        hideDecorationToolTip();
    }
}

bool CHyprBar::remoteMouseButton(Event::SCallbackInfo& info, const IPointer::SButtonEvent& e) {
    const uint32_t button = qtButton(e.button);
    if (!button || !g_pDecoClient)
        return false;
    const auto mouse = g_pInputManager->getMouseCoordsInternal();
    auto       PW    = m_pWindow.lock();
    if (!PW)
        return false;

    if (e.state == WL_POINTER_BUTTON_STATE_PRESSED) {
        Vector2D local;
        if (!remoteHit(mouse, &local))
            return false;
        // Alt/Super + arrastre es de los atajos de Hyprland
        const auto MODS = g_pInputManager->getModsFromAllKBs();
        if ((MODS & (g_pKeybindManager->stringToModMask("ALT") | g_pKeybindManager->stringToModMask("SUPER"))) != 0)
            return false;

        if (Desktop::focusState()->window() != PW)
            Desktop::focusState()->fullWindowFocus(PW, Desktop::FOCUS_REASON_CLICK);
        if (PW->m_isFloating)
            Desktop::windowState()->raise(PW);

        info.cancelled   = true;
        m_bCancelledDown = true;
        m_remote.buttons |= button;
        m_remote.press = SRemoteState::SPress{button, false};
        hideDecorationToolTip();
        if (!g_pDecoClient->send(pointer(m_remote.id, Press, local.x, local.y, button, m_remote.buttons, 0))) {
            // Sin respuesta posible: como una pulsación que la decoración no quiso
            handlePointerResult(SPointerResult{Press, false, m_remote.section ? m_remote.section : TITLE_BAR_AREA, button});
        }
        return true;
    }

    if (!(m_remote.buttons & button))
        return false;
    m_remote.buttons &= ~button;
    if (auto frame = frameBoxGlobal(false)) {
        const auto local = mouse - frame->pos();
        g_pDecoClient->send(pointer(m_remote.id, Release, local.x, local.y, button, m_remote.buttons, 0));
    }
    if (m_remote.press && m_remote.press->button == button)
        m_remote.press->released = true;

    if (button == 1 && m_bResizing) {
        if (g_layoutManager->dragController()->target())
            g_layoutManager->endDragTarget();
        m_bResizing = false;
    }
    if (button == 1 && (m_bDraggingThis || m_bDragPending))
        handleUpEvent(info);
    else if (m_bCancelledDown) {
        info.cancelled   = true;
        m_bCancelledDown = false;
    }
    return true;
}

void CHyprBar::onAxis(Event::SCallbackInfo& info, const IPointer::SAxisEvent& e) {
    if (e.axis != WL_POINTER_AXIS_VERTICAL_SCROLL || e.delta == 0 || !g_pDecoClient)
        return;
    Vector2D local;
    if (!remoteHit(g_pInputManager->getMouseCoordsInternal(), &local))
        return;
    info.cancelled = true; // la rueda sobre la barra no llega a la app
    if (e.source != WL_POINTER_AXIS_SOURCE_WHEEL)
        return; // los paneles táctiles mandan muchos eventos: sólo rueda de verdad
    const double angle = e.delta < 0 ? 120 : -120; // Qt: positivo = hacia arriba
    m_remote.lastWheel = angle;
    g_pDecoClient->send(pointer(m_remote.id, Wheel, local.x, local.y, 0, m_remote.buttons, angle));
}

void CHyprBar::handlePointerResult(const SPointerResult& r) {
    auto PW = m_pWindow.lock();
    if (!PW)
        return;

    if (r.kind == Wheel) {
        if (r.accepted || r.section != TITLE_BAR_AREA)
            return;
        switch (wheelAction(g_pGlobalState->config.onWheel->value(), m_remote.lastWheel)) {
            case eWheelAction::RAISE: Desktop::windowState()->raise(PW); break;
            case eWheelAction::MAXIMIZE: runKWinWindow("maximize --mode full"); break;
            case eWheelAction::RESTORE: runKWinWindow("maximize --mode restore"); break;
            case eWheelAction::PREVIOUS_DESKTOP:
                Config::Supplementary::executor()->spawn(std::format("python3 {}/.config/hypr/scripts/cycle-workspace.py prev", homeDir()));
                break;
            case eWheelAction::NEXT_DESKTOP:
                Config::Supplementary::executor()->spawn(std::format("python3 {}/.config/hypr/scripts/cycle-workspace.py next", homeDir()));
                break;
            default: break;
        }
        return;
    }

    if (r.kind != Press || !m_remote.press || m_remote.press->button != r.button)
        return;
    const auto press = *m_remote.press;
    m_remote.press.reset();
    if (r.accepted)
        return; // un botón de la decoración: actúa al soltar (llega como Request)

    if (press.button == 1) {
        if (r.section == TITLE_BAR_AREA) {
            const auto now = Time::steadyNow();
            if (std::chrono::duration_cast<std::chrono::milliseconds>(now - m_lastTitleClick).count() < 400) {
                m_lastTitleClick = Time::steady_tp{};
                m_bDragPending   = false;
                runDoubleClickAction();
                return;
            }
            m_lastTitleClick = now;
            if (!press.released)
                m_bDragPending = true; // el primer movimiento empieza a mover (handleMovement)
        } else if (const uint8_t corner = cornerForSection(r.section); corner && !press.released && !Fullscreen::controller()->isFullscreen(PW)) {
            g_layoutManager->beginDragTarget(PW->layoutTarget(), MBIND_RESIZE, static_cast<Layout::eRectCorner>(corner));
            m_bResizing = true;
        }
    } else if (press.button == 2 && (r.section == TITLE_BAR_AREA || cornerForSection(r.section))) {
        // Botón derecho en la barra: menú de operaciones de la ventana (KWin)
        showWindowMenu(g_pInputManager->getMouseCoordsInternal());
    }
}

// ───────────────────────────────────────────────────────── peticiones de la decoración

// Minimizar y maximizar viven en kwin-window.py (F8): la misma lógica para botones, panel y atajos
void CHyprBar::runKWinWindow(const std::string& args) {
    if (auto PW = m_pWindow.lock())
        Config::Supplementary::executor()->spawn(
            std::format("python3 {}/.config/hypr/skins/plasma/scripts/kwin-window.py {} {}", homeDir(), args, windowAddress(PW)));
}

void CHyprBar::spawnMinimize() {
    runKWinWindow("minimize");
}

// Menú de operaciones de la ventana: lo dibuja Quickshell (F9) por IPC
void CHyprBar::showWindowMenu(const Vector2D& global) {
    if (auto PW = m_pWindow.lock())
        Config::Supplementary::executor()->spawn(
            std::format("qs -c ii ipc call plasmaWindowMenu open {} {} {}", windowAddress(PW), static_cast<int>(global.x), static_cast<int>(global.y)));
}

void CHyprBar::runDoubleClickAction() {
    auto PW = m_pWindow.lock();
    if (!Desktop::View::validMapped(PW))
        return;
    std::string cmd = g_pGlobalState->config.onDoubleClick->value();
    if (cmd.empty())
        return;
    if (cmd == "fullscreen 1" || cmd.find("window.fullscreen") != std::string::npos) {
        Fullscreen::controller()->setFullscreenMode(PW, Fullscreen::controller()->isFullscreen(PW) ? Fullscreen::FSMODE_NONE : Fullscreen::FSMODE_MAXIMIZED);
        return;
    }
    if (cmd.find("window.close") != std::string::npos) {
        Config::Actions::closeWindow(PW);
        return;
    }
    if ((cmd.find("toggle-minimize.py min") != std::string::npos || cmd.find("kwin-window.py") != std::string::npos) && cmd.find("0x") == std::string::npos)
        cmd += " " + windowAddress(PW);
    Config::Supplementary::executor()->spawn(cmd);
}

void CHyprBar::handleRequest(const SRequest& r) {
    auto PW = m_pWindow.lock();
    if (!Desktop::View::validMapped(PW))
        return;
    switch (r.kind) {
        case Close: Config::Actions::closeWindow(PW); break;
        case ToggleMaximization: {
            // Izquierdo: completo; central: vertical; derecho: horizontal (como KWin)
            const auto axis = maximizeAxis(r.arg);
            runKWinWindow(axis == eMaximizeAxis::VERTICAL ? "maximize --mode vertical" : axis == eMaximizeAxis::HORIZONTAL ? "maximize --mode horizontal" : "maximize --mode toggle");
            break;
        }
        case Minimize: spawnMinimize(); break;
        case ShowWindowMenu: {
            auto frame = frameBoxGlobal(false);
            showWindowMenu(frame ? Vector2D{frame->x + r.rect.x, frame->y + r.rect.y + r.rect.h} : g_pInputManager->getMouseCoordsInternal());
            break;
        }
        case ShowToolTip:
            if (m_remote.pointerInside)
                showDecorationToolTip(r.text, g_pInputManager->getMouseCoordsInternal());
            break;
        case HideToolTip: hideDecorationToolTip(); break;
        case ToggleOnAllDesktops: Config::Actions::pinWindow(Config::Actions::TOGGLE_ACTION_TOGGLE, PW); break;
        default: break; // encima/debajo, enrollar, ayuda, menú de la app: Hyprland no los tiene
    }
}

// ───────────────────────────────────────────────────────── sombra

CBreezeShadow::CBreezeShadow(PHLWINDOW window, WP<CHyprBar> bar) : IHyprWindowDecoration(window), m_window(window), m_bar(bar) {}

SDecorationPositioningInfo CBreezeShadow::getPositioningInfo() {
    SDecorationPositioningInfo info;
    info.policy   = DECORATION_POSITION_ABSOLUTE;
    info.edges    = DECORATION_EDGE_TOP | DECORATION_EDGE_BOTTOM | DECORATION_EDGE_LEFT | DECORATION_EDGE_RIGHT;
    info.reserved = false;
    m_positioned.reset();
    if (auto bar = m_bar.lock(); bar && bar->remoteActive() && bar->m_remote.shadow) {
        // Las extensiones se cuentan desde el contenido: bordes del marco + relleno de la sombra
        const auto& b = bar->m_remote.geometry->borders;
        const auto& p = bar->m_remote.shadow->padding;
        info.desiredExtents = {{b.left + p.left, b.top + p.top}, {b.right + p.right, b.bottom + p.bottom}};
        m_positioned        = BwmDeco::SExtents{p.left, p.top, p.right, p.bottom};
    }
    return info;
}

void CBreezeShadow::onPositioningReply(const SDecorationPositioningReply&) {}

std::optional<CBox> CBreezeShadow::outerBox() {
    auto bar = m_bar.lock();
    if (!bar || !bar->remoteActive() || !bar->m_remote.shadow)
        return std::nullopt;
    auto frame = bar->frameBoxGlobal(true);
    if (!frame)
        return std::nullopt;
    const auto& p = bar->m_remote.shadow->padding;
    return CBox{frame->x - p.left, frame->y - p.top, frame->w + p.left + p.right, frame->h + p.top + p.bottom};
}

void CBreezeShadow::draw(PHLMONITOR, float const& a) {
    auto bar = m_bar.lock();
    auto PW  = m_window.lock();
    if (!bar || !Desktop::View::validMapped(PW) || !bar->remoteActive() || !bar->m_remote.shadow)
        return;
    if (!PW->m_ruleApplicator->decorate().valueOrDefault() || PW->m_ruleApplicator->noShadow().valueOrDefault())
        return;
    g_pHyprRenderer->m_renderPass.add(makeUnique<CBreezeShadowPassElement>(this, a));
}

void CBreezeShadow::renderPass(PHLMONITOR pMonitor, float a) {
    if (auto bar = m_bar.lock())
        bar->renderShadow(pMonitor, a);
}

eDecorationType CBreezeShadow::getDecorationType() {
    return DECORATION_CUSTOM;
}

void CBreezeShadow::updateWindow(PHLWINDOW) {
    damageEntire();
}

void CBreezeShadow::damageEntire() {
    if (auto box = outerBox())
        g_pHyprRenderer->damageBox(*box);
}

eDecorationLayer CBreezeShadow::getDecorationLayer() {
    return DECORATION_LAYER_BOTTOM;
}

uint64_t CBreezeShadow::getDecorationFlags() {
    return DECORATION_NON_SOLID;
}

std::string CBreezeShadow::getDisplayName() {
    return "BreezeShadow";
}

std::vector<UP<IPassElement>> CBreezeShadowPassElement::draw() {
    m_deco->renderPass(g_pHyprRenderer->m_renderData.pMonitor.lock(), m_a);
    return {};
}

std::optional<CBox> CBreezeShadowPassElement::boundingBox() {
    auto box = m_deco->outerBox();
    if (!box)
        return std::nullopt;
    return box->translate(-g_pHyprRenderer->m_renderData.pMonitor->m_position);
}

// ───────────────────────────────────────────────────────── tooltip

namespace {
    struct SToolTip {
        std::string          text;
        Vector2D             pos;
        bool                 visible = false;
        SP<Render::ITexture> texture;
        std::string          textureText;
        float                textureScale = 0;
        BwmDeco::STooltipColors colors;
        CBox                 lastBox;
    };
    SToolTip g_toolTip;

    class CToolTipPassElement : public IPassElement {
      public:
        virtual std::vector<UP<IPassElement>> draw() override;
        virtual bool                          needsLiveBlur() override {
            return false;
        }
        virtual bool needsPrecomputeBlur() override {
            return false;
        }
        virtual bool undiscardable() override {
            return true;
        }
        virtual bool disableSimplification() override {
            return true;
        }
        virtual std::optional<CBox> boundingBox() override {
            return std::nullopt;
        }
        virtual const char* passName() override {
            return "CBreezeToolTipPassElement";
        }
        virtual ePassElementType type() override {
            return EK_CUSTOM;
        }
    };

    std::string readKdeGlobals() {
        const char*   xdg = getenv("XDG_CONFIG_HOME");
        std::string   dir = xdg && *xdg ? xdg : homeDir() + "/.config";
        std::ifstream in(dir + "/kdeglobals");
        std::stringstream ss;
        ss << in.rdbuf();
        return ss.str();
    }

    void damageToolTip() {
        if (g_toolTip.lastBox.w > 0)
            g_pHyprRenderer->damageBox(g_toolTip.lastBox.copy().expand(2));
    }
}

void showDecorationToolTip(const std::string& text, const Vector2D& globalPos) {
    damageToolTip();
    g_toolTip.text    = text;
    g_toolTip.pos     = globalPos;
    g_toolTip.visible = !text.empty();
    g_toolTip.colors  = BwmDeco::tooltipColors(readKdeGlobals());
    // Tamaño aproximado hasta dibujarlo: se daña una zona generosa bajo el puntero
    g_toolTip.lastBox = CBox{globalPos.x - 400, globalPos.y, 800, 80};
    damageToolTip();
}

void hideDecorationToolTip() {
    if (!g_toolTip.visible)
        return;
    g_toolTip.visible = false;
    damageToolTip();
}

void clearDecorationToolTip() {
    g_toolTip = SToolTip{};
}

void renderDecorationToolTip(eRenderStage stage) {
    if (stage != RENDER_LAST_MOMENT || !g_toolTip.visible)
        return;
    auto pMonitor = g_pHyprRenderer->m_renderData.pMonitor.lock();
    if (!pMonitor || !CBox{pMonitor->m_position, pMonitor->m_size}.containsPoint(g_toolTip.pos))
        return;
    g_pHyprRenderer->m_renderPass.add(makeUnique<CToolTipPassElement>());
}

std::vector<UP<IPassElement>> CToolTipPassElement::draw() {
    auto pMonitor = g_pHyprRenderer->m_renderData.pMonitor.lock();
    if (!pMonitor || !g_toolTip.visible)
        return {};
    const float scale = pMonitor->m_scale;
    if (!g_toolTip.texture || g_toolTip.textureText != g_toolTip.text || g_toolTip.textureScale != scale) {
        const auto fg = g_toolTip.colors.foreground;
        g_toolTip.texture =
            g_pHyprRenderer->renderText(g_toolTip.text, CHyprColor{static_cast<uint64_t>(fg)}, std::round(10 * scale), false, g_pGlobalState->config.barTextFont->value());
        g_toolTip.textureText  = g_toolTip.text;
        g_toolTip.textureScale = scale;
    }
    if (!g_toolTip.texture || g_toolTip.texture->m_texID == 0)
        return {};

    // Como QToolTip: debajo del puntero, dentro de la pantalla
    const Vector2D pad{6, 4};
    const Vector2D size = g_toolTip.texture->m_size / scale + pad * 2;
    Vector2D       pos  = g_toolTip.pos + Vector2D{-size.x / 2, 22.0};
    pos.x               = std::clamp(pos.x, pMonitor->m_position.x + 2, pMonitor->m_position.x + pMonitor->m_size.x - size.x - 2);
    if (pos.y + size.y > pMonitor->m_position.y + pMonitor->m_size.y)
        pos.y = g_toolTip.pos.y - size.y - 6;
    const CBox globalBox{pos, size};
    if (!(globalBox == g_toolTip.lastBox)) {
        damageToolTip();
        g_toolTip.lastBox = globalBox;
        damageToolTip();
    }

    CBox box = monitorLocal(globalBox, pMonitor);
    g_pHyprOpenGL->renderRect(box, CHyprColor{static_cast<uint64_t>(g_toolTip.colors.background)}, {.round = static_cast<int>(std::round(3 * scale)), .roundingPower = 2.F});
    Config::CGradientValueData border(CHyprColor{static_cast<uint64_t>((g_toolTip.colors.foreground & 0x00ffffff) | 0x33000000)});
    g_pHyprOpenGL->renderBorder(box, border, {.round = static_cast<int>(std::round(3 * scale)), .roundingPower = 2.F, .borderSize = 1, .a = 1.F});
    CBox textBox = monitorLocal(CBox{pos + pad, g_toolTip.texture->m_size / scale}, pMonitor);
    textBox.w    = g_toolTip.texture->m_size.x;
    textBox.h    = g_toolTip.texture->m_size.y;
    CHyprOpenGLImpl::STextureRenderData data;
    data.a = 1.F;
    g_pHyprOpenGL->renderTexture(g_toolTip.texture, textBox, data);
    return {};
}
