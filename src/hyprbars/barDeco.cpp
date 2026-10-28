
#include "barDeco.hpp"
#include "CSDDetect.hpp"
#include "SnapHelper.hpp"

#include <hyprland/src/desktop/state/WindowState.hpp>
#include <hyprland/src/desktop/state/ViewState.hpp>
#include <hyprland/src/desktop/state/ViewHitTester.hpp>
#include <hyprland/src/state/MonitorState.hpp>
#include <hyprland/src/managers/fullscreen/FullscreenController.hpp>
#include <hyprland/src/Compositor.hpp>
#include <hyprland/src/desktop/state/FocusState.hpp>
#include <hyprland/src/desktop/view/Window.hpp>
#include <hyprland/src/helpers/MiscFunctions.hpp>
#include <hyprland/src/managers/SeatManager.hpp>
#include <hyprland/src/managers/input/InputManager.hpp>
#include <hyprland/src/render/Renderer.hpp>
#include <hyprland/src/config/ConfigManager.hpp>
#include <hyprland/src/config/shared/animation/AnimationTree.hpp>
#include <hyprland/src/config/shared/parserUtils/ParserUtils.hpp>
#include <hyprland/src/config/supplementary/executor/Executor.hpp>
#include <hyprland/src/config/shared/actions/ConfigActions.hpp>
#include <hyprland/src/animation/AnimationManager.hpp>
#include <hyprland/src/protocols/LayerShell.hpp>
#include <hyprland/src/event/EventBus.hpp>
#include <hyprland/src/layout/LayoutManager.hpp>
#include <hyprland/src/layout/space/Space.hpp>
#include <hyprland/src/layout/target/Target.hpp>
#include <hyprland/src/pointer/cursor/CursorShapeOverrideController.hpp>
#include <hyprland/src/render/OpenGL.hpp>

#include "globals.hpp"
#include "BarPassElement.hpp"
#include <hyprland/src/protocols/XDGShell.hpp>
#include <hyprland/src/xwayland/XSurface.hpp>

#include <climits>
#include <linux/input-event-codes.h>

using namespace Render::GL;

static CHyprColor configColor(Config::INTEGER color) {
    return CHyprColor{static_cast<uint64_t>(color)};
}

// La ventana trae sus propios botones: no se le dibuja barra (pero se sigue
// gestionando su arrastre CSD para el snapping).
static bool isKnownCSD(PHLWINDOW window) {
    return detectDecorations(window).clientDraws;
}

// Iconos de la decoración Breeze (KDE Plasma), con la misma geometría que
// breeze/kdecoration: rejilla de 18x18, trazo de ~1px y extremos redondeados.
static SP<Render::ITexture> breezeIcon(SHyprButton& button, bool maximized, const CHyprColor& col, int px) {
    const std::string kind = button.breezeKind == "maximize" && maximized ? "restore" : button.breezeKind;
    const auto        key  = std::format("{}:{}:{:x}", kind, px, col.getAsHex());
    if (auto it = button.breezeTex.find(key); it != button.breezeTex.end() && it->second && it->second->m_texID != 0)
        return it->second;

    auto surf = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, px, px);
    auto cr   = cairo_create(surf);
    cairo_scale(cr, px / 18.0, px / 18.0);
    cairo_set_source_rgba(cr, col.r, col.g, col.b, col.a);
    cairo_set_line_width(cr, std::max(1.01, 18.0 / px));
    cairo_set_line_cap(cr, CAIRO_LINE_CAP_ROUND);
    cairo_set_line_join(cr, CAIRO_LINE_JOIN_ROUND);

    if (kind == "close") {
        cairo_move_to(cr, 5, 5);
        cairo_line_to(cr, 13, 13);
        cairo_move_to(cr, 13, 5);
        cairo_line_to(cr, 5, 13);
    } else if (kind == "maximize") {
        cairo_move_to(cr, 3.5, 11.5);
        cairo_line_to(cr, 9, 6);
        cairo_line_to(cr, 14.5, 11.5);
    } else if (kind == "restore") {
        cairo_move_to(cr, 4.5, 9);
        cairo_line_to(cr, 9, 4.5);
        cairo_line_to(cr, 13.5, 9);
        cairo_line_to(cr, 9, 13.5);
        cairo_close_path(cr);
    } else if (kind == "minimize") {
        cairo_move_to(cr, 3.5, 6.5);
        cairo_line_to(cr, 9, 12);
        cairo_line_to(cr, 14.5, 6.5);
    }
    cairo_stroke(cr);
    cairo_surface_flush(surf);

    auto tex = g_pHyprRenderer->createTexture(surf);
    cairo_destroy(cr);
    cairo_surface_destroy(surf);

    button.breezeTex[key] = tex;
    return tex;
}

CHyprColor CHyprBar::currentTextColor() {
    const auto INACTIVE = g_pGlobalState->config.inactiveTextColor->value();
    if (!m_bWindowHasFocus && INACTIVE > 0)
        return configColor(INACTIVE);
    return configColor(g_pGlobalState->config.textColor->value());
}

CHyprBar::CHyprBar(PHLWINDOW pWindow) : IHyprWindowDecoration(pWindow) {
    m_pWindow = pWindow;
    m_hidden  = isKnownCSD(pWindow);

    const auto PMONITOR         = pWindow->m_monitor.lock();
    PMONITOR->m_scheduledRecalc = true;

    // button events
    m_pMouseButtonCallback = Event::bus()->m_events.input.mouse.button.listen([&](IPointer::SButtonEvent e, Event::SCallbackInfo& info) { onMouseButton(info, e); });
    m_pTouchDownCallback   = Event::bus()->m_events.input.touch.down.listen([&](ITouch::SDownEvent e, Event::SCallbackInfo& info) { onTouchDown(info, e); });
    m_pTouchUpCallback     = Event::bus()->m_events.input.touch.up.listen([&](ITouch::SUpEvent e, Event::SCallbackInfo& info) { onTouchUp(info, e); });

    // move events
    m_pTouchMoveCallback = Event::bus()->m_events.input.touch.motion.listen([&](ITouch::SMotionEvent e, Event::SCallbackInfo& info) { onTouchMove(info, e); });
    m_pMouseMoveCallback = Event::bus()->m_events.input.mouse.move.listen([&](Vector2D c, Event::SCallbackInfo& info) { onMouseMove(c); });

    Animation::mgr()->createAnimation(configColor(g_pGlobalState->config.barColor->value()), m_cRealBarColor, Config::animationTree()->getAnimationPropertyConfig("border"),
                                         pWindow, AVARDAMAGE_NONE);
    m_cRealBarColor->setUpdateCallback([&](auto) { damageEntire(); });

    // Listen for minimize requests from client-side decorations (CSD windows like Steam, Firefox, Chrome, etc.)
    auto pXDG = pWindow->m_xdgSurface.lock();
    if (pXDG && pXDG->m_toplevel.lock()) {
        m_pStateChangedCallback = pXDG->m_toplevel.lock()->m_events.stateChanged.listen([this, wpTop = pXDG->m_toplevel] {
            auto top = wpTop.lock();
            auto pw = m_pWindow.lock();
            if (pw && top && top->m_state.requestsMinimize.value_or(false)) {
                std::string addr = std::format("0x{:x}", (uintptr_t)pw.get());
                Config::Supplementary::executor()->spawn("/home/sasel/.config/hypr/scripts/toggle-minimize.py min " + addr);
            }
        });
    } else if (auto pXWayland = pWindow->m_xwaylandSurface.lock()) {
        m_pStateChangedCallback = pXWayland->m_events.stateChanged.listen([this, wpXW = pWindow->m_xwaylandSurface] {
            auto xw = wpXW.lock();
            auto pw = m_pWindow.lock();
            if (pw && xw && xw->m_state.requestsMinimize.value_or(false)) {
                std::string addr = std::format("0x{:x}", (uintptr_t)pw.get());
                Config::Supplementary::executor()->spawn("/home/sasel/.config/hypr/scripts/toggle-minimize.py min " + addr);
            }
        });
    }
}

CHyprBar::~CHyprBar() {
    if (m_bDraggingCSD && m_bDragInitiated) {
        Pointer::Cursor::overrideController->unsetOverride(Pointer::Cursor::CURSOR_OVERRIDE_SPECIAL_ACTION);
    }
    if (g_pGlobalState)
        std::erase(g_pGlobalState->bars, m_self);
}

SDecorationPositioningInfo CHyprBar::getPositioningInfo() {
    const auto                 HEIGHT     = g_pGlobalState->config.barHeight->value();
    const auto                 ENABLED    = g_pGlobalState->config.enabled->value();
    const auto                 PRECEDENCE = g_pGlobalState->config.barPrecedenceOverBorder->value();

    SDecorationPositioningInfo info;
    info.policy         = m_hidden ? DECORATION_POSITION_ABSOLUTE : DECORATION_POSITION_STICKY;
    info.edges          = DECORATION_EDGE_TOP;
    info.priority       = PRECEDENCE ? 10005 : 5000;
    info.reserved       = true;
    info.desiredExtents = {{0, m_hidden || !ENABLED ? 0 : HEIGHT}, {0, 0}};
    return info;
}

void CHyprBar::onPositioningReply(const SDecorationPositioningReply& reply) {
    if (reply.assignedGeometry.size() != m_bAssignedBox.size())
        m_bWindowSizeChanged = true;

    m_bAssignedBox = reply.assignedGeometry;
}

std::string CHyprBar::getDisplayName() {
    return "Hyprbar";
}

bool CHyprBar::inputIsValid() {
    if (!g_pGlobalState->config.enabled->value())
        return false;

    if (!m_pWindow->m_workspace || !m_pWindow->m_workspace->isVisible() || !g_pInputManager->m_exclusiveLSes.empty() ||
        (g_pSeatManager->m_seatGrab && (!m_pWindow->wlSurface() || !g_pSeatManager->m_seatGrab->accepts(m_pWindow->wlSurface()->resource()))))
        return false;

    const auto WINDOWATCURSOR = Desktop::CViewHitTester{*Desktop::viewState()}.windowAt(g_pInputManager->getMouseCoordsInternal(),
                                                                     Desktop::View::RESERVED_EXTENTS | Desktop::View::INPUT_EXTENTS | Desktop::View::ALLOW_FLOATING);

    auto       focusState = Desktop::focusState();
    auto       window     = focusState->window();
    auto       monitor    = focusState->monitor();

    auto PW = m_pWindow.lock();
    if (!PW)
        return false;

    if (m_hidden) {
        if (WINDOWATCURSOR != PW)
            return false;
    } else {
        if (WINDOWATCURSOR != PW && PW != window)
            return false;
    }

    // check if input is on top or overlay shell layers
    auto     PMONITOR     = monitor;
    PHLLS    foundSurface = nullptr;
    Vector2D surfaceCoords;

    // check top layer
    Desktop::CViewHitTester{*Desktop::viewState()}.layerSurfaceAt(g_pInputManager->getMouseCoordsInternal(), &PMONITOR->m_layerSurfaceLayers[ZWLR_LAYER_SHELL_V1_LAYER_TOP], &surfaceCoords, &foundSurface);

    if (foundSurface)
        return false;
    // check overlay layer
    Desktop::CViewHitTester{*Desktop::viewState()}.layerSurfaceAt(g_pInputManager->getMouseCoordsInternal(), &PMONITOR->m_layerSurfaceLayers[ZWLR_LAYER_SHELL_V1_LAYER_OVERLAY], &surfaceCoords,
                                        &foundSurface);

    if (foundSurface)
        return false;

    return true;
}


void CHyprBar::onMouseButton(Event::SCallbackInfo& info, IPointer::SButtonEvent e) {
    if (e.button != BTN_LEFT)
        return;

    auto PW = m_pWindow.lock();

    if (e.state != WL_POINTER_BUTTON_STATE_PRESSED) {
        if (m_hidden) {
            if (m_bDraggingCSD) {
                if (Desktop::View::validMapped(PW)) {
                    g_layoutManager->setTargetGeom(PW->layoutTarget()->position(), PW->layoutTarget());
                    PW->updateWindowData();
                    Desktop::focusState()->fullWindowFocus(PW, Desktop::FOCUS_REASON_CLICK);
                }
                if (m_bDragInitiated) {
                    if (g_layoutManager && g_layoutManager->dragController() && g_layoutManager->dragController()->mode() == MBIND_MOVE)
                        g_pKeybindManager->changeMouseBindMode(MBIND_INVALID);
                    Pointer::Cursor::overrideController->unsetOverride(Pointer::Cursor::CURSOR_OVERRIDE_SPECIAL_ACTION);
                    hideSnapPreview();
                    // Do NOT set info.cancelled = true!
                    // Removing info.cancelled allows pointer button UP to reach Electron/GTK,
                    // preventing swallowed / frozen clicks on menu items or buttons.
                    checkAndTriggerEdgeSnap(PW, g_pInputManager->getMouseCoordsInternal());
                }
                m_bDraggingCSD   = false;
                m_bDragInitiated = false;
            }
            if (m_bCancelledDown) {
                info.cancelled   = true;
                m_bCancelledDown = false;
            }
            return;
        }

        if (m_bDraggingThis || m_bDragPending)
            handleUpEvent(info);
        return;
    }

    if (inputIsValid()) {
        handleDownEvent(info, std::nullopt);
    }
}

void CHyprBar::onTouchDown(Event::SCallbackInfo& info, ITouch::SDownEvent e) {
    // Don't do anything if you're already grabbed a window with another finger
    if (!inputIsValid() || e.touchID != 0)
        return;

    handleDownEvent(info, e);
}

void CHyprBar::onTouchUp(Event::SCallbackInfo& info, ITouch::SUpEvent e) {
    if (!m_bDragPending || !m_bTouchEv || e.touchID != m_touchId)
        return;

    handleUpEvent(info);
}

void CHyprBar::onMouseMove(Vector2D coords) {
    if (m_hidden) {
        if (!m_bDraggingCSD)
            return;

        auto PWINDOW = m_pWindow.lock();
        if (!Desktop::View::validMapped(PWINDOW)) {
            if (m_bDragInitiated)
                Pointer::Cursor::overrideController->unsetOverride(Pointer::Cursor::CURSOR_OVERRIDE_SPECIAL_ACTION);
            m_bDraggingCSD   = false;
            m_bDragInitiated = false;
            return;
        }

        Vector2D currentMouse = g_pInputManager->getMouseCoordsInternal();
        Vector2D totalDelta   = currentMouse - m_vDragStartMouse;

        if (!m_bDragInitiated) {
            if (std::abs(totalDelta.x) < 3.0f && std::abs(totalDelta.y) < 3.0f)
                return;

            m_bDragInitiated = true;
            Pointer::Cursor::overrideController->setOverride("grabbing", Pointer::Cursor::CURSOR_OVERRIDE_SPECIAL_ACTION);

            bool wasFullscreen = Fullscreen::controller()->isFullscreen(PWINDOW);
            bool wasSnapped = PWINDOW->m_ruleApplicator && PWINDOW->m_ruleApplicator->m_tagKeeper.isTagged("snapped");
            float curW = PWINDOW->layoutTarget()->position().w;

            g_pHyprRenderer->damageWindow(PWINDOW, true);

            if (wasFullscreen) {
                Fullscreen::controller()->setFullscreenMode(PWINDOW, Fullscreen::FSMODE_NONE);
            }
            Config::Actions::clearTags(PWINDOW);
            PWINDOW->updateWindowData();

            if (wasSnapped || wasFullscreen) {
                Vector2D targetSize = PWINDOW->layoutTarget()->position().size();
                if (wasSnapped) {
                    auto optSize = getAndConsumePreSnapSize(PWINDOW);
                    targetSize = optSize.value_or(Vector2D{900, 600});
                }

                float ratioX = curW > 0 ? std::clamp((double)(m_vGrabOffset.x / curW), 0.05, 0.95) : 0.5f;

                m_vGrabOffset.x = targetSize.x * ratioX;
                m_vGrabOffset.y = std::clamp((double)m_vGrabOffset.y, 5.0, 35.0);

                Vector2D newPos = (currentMouse - m_vGrabOffset).round();
                CBox newBox = {newPos, targetSize};

                PWINDOW->layoutTarget()->setPositionGlobal(newBox);
                g_layoutManager->setTargetGeom(newBox, PWINDOW->layoutTarget());
                PWINDOW->layoutTarget()->warpPositionSize();
                PWINDOW->updateWindowDecos();
                g_pHyprRenderer->damageWindow(PWINDOW, true);
            }
        }

        if (!PWINDOW->m_isFloating) {
            g_layoutManager->changeFloatingMode(PWINDOW->layoutTarget());
        }
        if (Fullscreen::controller()->isFullscreen(PWINDOW)) {
            Fullscreen::controller()->setFullscreenMode(PWINDOW, Fullscreen::FSMODE_NONE);
        }

        // Exact window tracking: window top-left is positioned so m_vGrabOffset stays under the cursor
        Vector2D newPos = (currentMouse - m_vGrabOffset).round();
        Vector2D size   = PWINDOW->layoutTarget()->position().size();
        CBox     newBox = {newPos, size};

        g_pHyprRenderer->damageWindow(PWINDOW, true);
        PWINDOW->layoutTarget()->setPositionGlobal(newBox);
        PWINDOW->layoutTarget()->warpPositionSize();
        PWINDOW->updateWindowDecos();
        g_pHyprRenderer->damageWindow(PWINDOW, true);

        Vector2D middle = newBox.middle();
        const auto PMONITOR = State::monitorState()->query().vec(middle).run();
        if (PMONITOR && PMONITOR->m_activeWorkspace && PWINDOW->m_isFloating) {
            const auto WS = PMONITOR->m_activeSpecialWorkspace ? PMONITOR->m_activeSpecialWorkspace : PMONITOR->m_activeWorkspace;
            if (PWINDOW->m_workspace != WS) {
                g_pHyprRenderer->damageWindow(PWINDOW, true);
                PWINDOW->layoutTarget()->assignToSpace(WS->m_space);
                // Immediately re-anchor window to exact cursor position so assignToSpace does not jump
                PWINDOW->layoutTarget()->setPositionGlobal(newBox);
                g_layoutManager->setTargetGeom(newBox, PWINDOW->layoutTarget());
                PWINDOW->layoutTarget()->warpPositionSize();
                PWINDOW->updateWindowDecos();
                g_pHyprRenderer->damageWindow(PWINDOW, true);
            }
        }
        updateSnapPreview(currentMouse);
        return;
    }

    // ensure proper redraws of button icons on hover when using hardware cursors
    if (!m_hidden && g_pGlobalState->config.iconOnHover->value())
        damageOnButtonHover();

    if (!m_bDragPending || m_bTouchEv || !Desktop::View::validMapped(m_pWindow) || m_touchId != 0)
        return;

    m_bDragPending = false;
    handleMovement();
    updateSnapPreview(g_pInputManager->getMouseCoordsInternal());
}

void CHyprBar::onTouchMove(Event::SCallbackInfo& info, ITouch::SMotionEvent e) {
    if (!m_bDragPending || !m_bTouchEv || !Desktop::View::validMapped(m_pWindow) || e.touchID != m_touchId)
        return;

    auto PMONITOR     = m_pWindow->m_monitor.lock();
    PMONITOR          = PMONITOR ? PMONITOR : Desktop::focusState()->monitor();
    const auto COORDS = Vector2D(PMONITOR->m_position.x + e.pos.x * PMONITOR->m_size.x, PMONITOR->m_position.y + e.pos.y * PMONITOR->m_size.y);

    if (!m_bDraggingThis) {
        // Initial setup for dragging a window.
        g_pKeybindManager->m_dispatchers["setfloating"]("activewindow");
        g_pKeybindManager->m_dispatchers["resizewindowpixel"]("exact 50% 50%,activewindow");
        // pin it so you can change workspaces while dragging a window
        g_pKeybindManager->m_dispatchers["pin"]("activewindow");
    }
    g_pKeybindManager->m_dispatchers["movewindowpixel"](std::format("exact {} {},activewindow", (int)(COORDS.x - (assignedBoxGlobal().w / 2)), (int)COORDS.y));
    m_bDraggingThis = true;
}

void CHyprBar::handleDownEvent(Event::SCallbackInfo& info, std::optional<ITouch::SDownEvent> touchEvent) {
    m_bTouchEv = touchEvent.has_value();
    if (m_bTouchEv)
        m_touchId = touchEvent.value().touchID;

    const auto PWINDOW = m_pWindow.lock();
    if (!PWINDOW)
        return;

    const auto MODS = g_pInputManager->getModsFromAllKBs();
    const auto ALTMASK = g_pKeybindManager->stringToModMask("ALT");
    if ((MODS & ALTMASK) != 0)
        return;

    const auto HEIGHT           = g_pGlobalState->config.barHeight->value();
    const auto BARBUTTONPADDING = g_pGlobalState->config.barButtonPadding->value();
    const auto BARPADDING       = g_pGlobalState->config.barPadding->value();
    const auto ALIGNBUTTONS     = g_pGlobalState->config.barButtonsAlignment->value();
    const auto ON_DOUBLE_CLICK  = g_pGlobalState->config.onDoubleClick->value();

    const bool BUTTONSRIGHT = ALIGNBUTTONS != "left";

    if (m_hidden) {
        // CSD Window (Antigravity IDE, Steam, Firefox, Chrome, Vesktop, etc.)
        CBox windowBox = PWINDOW->getWindowMainSurfaceBox();
        const auto PWORKSPACE      = PWINDOW->m_workspace;
        const auto WORKSPACEOFFSET = PWORKSPACE && !PWINDOW->m_pinned ? PWORKSPACE->m_renderOffset->value() : Vector2D();
        windowBox.translate(WORKSPACEOFFSET);

        Vector2D mousePos = g_pInputManager->getMouseCoordsInternal() - windowBox.pos();
        const auto CSD_HEIGHT = std::max<int>(50, HEIGHT);

        if (mousePos.x < 0 || mousePos.x >= windowBox.w || mousePos.y < 0 || mousePos.y >= CSD_HEIGHT)
            return;

        // In CSD windows, native buttons (close, maximize, minimize) are in the top-right corner (~140px).
        // Let clicks in that area pass directly to the app without dragging so native close/maximize buttons work.
        if (mousePos.x > windowBox.w - 140)
            return;

        if (Desktop::focusState()->window() != PWINDOW)
            Desktop::focusState()->fullWindowFocus(PWINDOW, Desktop::FOCUS_REASON_CLICK);

        if (PWINDOW->m_isFloating)
            Desktop::windowState()->raise(PWINDOW);

        // Double click: maximize / restore
        auto now = Time::steadyNow();
        auto diffMs = std::chrono::duration_cast<std::chrono::milliseconds>(now - m_lastMouseDown).count();
        if (diffMs < 350) {
            if (Fullscreen::controller()->isFullscreen(PWINDOW)) {
                Fullscreen::controller()->setFullscreenMode(PWINDOW, Fullscreen::FSMODE_NONE);
            } else {
                Fullscreen::controller()->setFullscreenMode(PWINDOW, Fullscreen::FSMODE_MAXIMIZED);
            }
            m_bDraggingCSD   = false;
            m_bDragInitiated = false;
            m_lastMouseDown  = Time::steadyNow() - std::chrono::seconds(5);
            info.cancelled   = true;
            m_bCancelledDown = true;
            return;
        }

        m_lastMouseDown   = now;
        m_bDraggingCSD    = true;
        m_bDragInitiated  = false;
        m_vDragStartMouse = g_pInputManager->getMouseCoordsInternal();
        m_vGrabOffset     = mousePos;
        return;
    }

    auto COORDS = cursorRelativeToBar();
    if (m_bTouchEv) {
        ITouch::SDownEvent e        = touchEvent.value();
        auto               PMONITOR = State::monitorState()->query().name(!e.device->m_boundOutput.empty() ? e.device->m_boundOutput : "").run();
        PMONITOR                    = PMONITOR ? PMONITOR : Desktop::focusState()->monitor();
        COORDS = Vector2D(PMONITOR->m_position.x + e.pos.x * PMONITOR->m_size.x, PMONITOR->m_position.y + e.pos.y * PMONITOR->m_size.y) - assignedBoxGlobal().pos();
    }

    if (!VECINRECT(COORDS, 0, 0, assignedBoxGlobal().w, HEIGHT - 1)) {

        if (m_bDraggingThis) {
            if (m_bTouchEv)
                g_pKeybindManager->m_dispatchers["settiled"]("activewindow");
            g_pKeybindManager->m_dispatchers["mouse"]("0movewindow");
            Log::logger->log(Log::DEBUG, "[hyprbars] Dragging ended on {:x}", (uintptr_t)PWINDOW.get());
        }

        m_bDraggingThis = false;
        m_bDragPending  = false;
        m_bTouchEv      = false;
        return;
    }

    if (Desktop::focusState()->window() != PWINDOW)
        Desktop::focusState()->fullWindowFocus(PWINDOW, Desktop::FOCUS_REASON_CLICK);

    if (PWINDOW->m_isFloating)
        Desktop::windowState()->raise(PWINDOW);

    info.cancelled   = true;
    m_bCancelledDown = true;

    if (doButtonPress(BARPADDING, BARBUTTONPADDING, HEIGHT, COORDS, BUTTONSRIGHT))
        return;

    if (!ON_DOUBLE_CLICK.empty() &&
        std::chrono::duration_cast<std::chrono::milliseconds>(Time::steadyNow() - m_lastMouseDown).count() < 400 /* Arbitrary delay I found suitable */) {
        if (ON_DOUBLE_CLICK == "fullscreen 1" || ON_DOUBLE_CLICK.find("window.fullscreen") != std::string::npos) {
            if (Desktop::View::validMapped(PWINDOW))
                Fullscreen::controller()->setFullscreenMode(PWINDOW, Fullscreen::controller()->isFullscreen(PWINDOW) ? Fullscreen::FSMODE_NONE : Fullscreen::FSMODE_MAXIMIZED);
        } else {
            Config::Supplementary::executor()->spawn(ON_DOUBLE_CLICK);
        }
        m_bDragPending = false;
    } else {
        m_lastMouseDown = Time::steadyNow();
        m_bDragPending  = true;
    }
}


void CHyprBar::handleUpEvent(Event::SCallbackInfo& info) {
    if (m_bCancelledDown)
        info.cancelled = true;

    m_bCancelledDown = false;

    if (m_bDraggingThis) {
        g_pKeybindManager->changeMouseBindMode(MBIND_INVALID);
        m_bDraggingThis = false;
        hideSnapPreview();
        if (m_bTouchEv)
            Config::Actions::floatWindow(Config::Actions::eTogglableAction::TOGGLE_ACTION_DISABLE);

        Log::logger->log(Log::DEBUG, "[hyprbars] Dragging ended on {:x}", (uintptr_t)m_pWindow.lock().get());
        checkAndTriggerEdgeSnap(m_pWindow.lock(), g_pInputManager->getMouseCoordsInternal());
    }

    m_bDragPending = false;
    m_bTouchEv     = false;
    m_touchId      = 0;
}


bool CHyprBar::isDragging() const {
    return m_bDraggingThis || (m_hidden && m_bDraggingCSD && m_bDragInitiated);
}

void CHyprBar::handleMovement() {
    auto PWINDOW = m_pWindow.lock();
    if (Desktop::View::validMapped(PWINDOW)) {
        CBox curBox = PWINDOW->layoutTarget()->position();
        bool wasFullscreen = Fullscreen::controller()->isFullscreen(PWINDOW);
        bool wasSnapped = PWINDOW->m_ruleApplicator && PWINDOW->m_ruleApplicator->m_tagKeeper.isTagged("snapped");

        damageEntire();
        g_pHyprRenderer->damageWindow(PWINDOW, true);

        if (wasFullscreen)
            Fullscreen::controller()->setFullscreenMode(PWINDOW, Fullscreen::FSMODE_NONE);

        Config::Actions::clearTags(PWINDOW);
        PWINDOW->updateWindowData();

        if (wasSnapped || wasFullscreen) {
            Vector2D targetSize = PWINDOW->layoutTarget()->position().size();
            if (wasSnapped) {
                auto optSize = getAndConsumePreSnapSize(PWINDOW);
                targetSize = optSize.value_or(Vector2D{900, 600});
            }

            Vector2D mousePos = g_pInputManager->getMouseCoordsInternal();
            float ratioX = curBox.w > 0 ? std::clamp((double)((mousePos.x - curBox.x) / curBox.w), 0.05, 0.95) : 0.5f;

            Vector2D newPos = {mousePos.x - targetSize.x * ratioX, mousePos.y - 15.0f};
            CBox newBox = {newPos.round(), targetSize};

            PWINDOW->layoutTarget()->setPositionGlobal(newBox);
            g_layoutManager->setTargetGeom(newBox, PWINDOW->layoutTarget());
            PWINDOW->layoutTarget()->warpPositionSize();
            PWINDOW->updateWindowDecos();
            damageEntire();
            g_pHyprRenderer->damageWindow(PWINDOW, true);
        }
    }
    g_pKeybindManager->changeMouseBindMode(MBIND_MOVE);
    m_bDraggingThis = true;
    Log::logger->log(Log::DEBUG, "[hyprbars] Dragging initiated on {:x}", (uintptr_t)m_pWindow.lock().get());
    return;
}

bool CHyprBar::doButtonPress(Config::INTEGER barPadding, Config::INTEGER barButtonPadding, Config::INTEGER barHeight, Vector2D COORDS, const bool BUTTONSRIGHT) {
    //check if on a button
    float offset = barPadding;

    for (auto& b : g_pGlobalState->buttons) {
        const auto BARBUF     = Vector2D{(int)assignedBoxGlobal().w, barHeight};
        Vector2D   currentPos = Vector2D{(BUTTONSRIGHT ? BARBUF.x - barButtonPadding - b.size - offset : offset), (BARBUF.y - b.size) / 2.0}.floor();

        if (VECINRECT(COORDS, currentPos.x, currentPos.y, currentPos.x + b.size + barButtonPadding, currentPos.y + b.size)) {
            // hit on button
            std::string cmd = b.cmd;
            auto PW = m_pWindow.lock();
            if (Desktop::View::validMapped(PW)) {
                if (cmd == "hyprctl dispatch fullscreen 1" || cmd.find("window.fullscreen") != std::string::npos) {
                    Fullscreen::controller()->setFullscreenMode(PW, Fullscreen::controller()->isFullscreen(PW) ? Fullscreen::FSMODE_NONE : Fullscreen::FSMODE_MAXIMIZED);
                    return true;
                }
                if (cmd == "hyprctl dispatch killactive" || cmd.find("window.close") != std::string::npos) {
                    Config::Actions::closeWindow(PW);
                    return true;
                }
            }
            if (cmd.find("toggle-minimize.py min") != std::string::npos && PW) {
                cmd += " " + std::format("0x{:x}", (uintptr_t)PW.get());
            }
            g_pKeybindManager->m_dispatchers["exec"](cmd);
            return true;
        }

        offset += barButtonPadding + b.size;
    }
    return false;
}

void CHyprBar::renderBarTitle(const Vector2D& bufferSize, const float scale) {
    const auto COLORVAL         = g_pGlobalState->config.textColor->value();
    const auto SIZE             = g_pGlobalState->config.barTextSize->value();
    const auto FONT             = g_pGlobalState->config.barTextFont->value();
    const auto ALIGN            = g_pGlobalState->config.barTextAlign->value();
    const auto BARPADDING       = g_pGlobalState->config.barPadding->value();
    const auto BARBUTTONPADDING = g_pGlobalState->config.barButtonPadding->value();

    float      buttonSizes = BARBUTTONPADDING;
    for (auto& b : g_pGlobalState->buttons) {
        buttonSizes += b.size + BARBUTTONPADDING;
    }

    const int  scaledSize        = std::round(SIZE * scale);
    const auto scaledButtonsSize = buttonSizes * scale;
    const auto scaledBarPadding  = BARPADDING * scale;
    const int  paddingTotal      = scaledBarPadding * 2 + scaledButtonsSize + (ALIGN != "left" ? scaledButtonsSize : 0);
    const int  maxWidth          = std::clamp(static_cast<int>(bufferSize.x - paddingTotal), 0, INT_MAX);

    if (m_szLastTitle.empty() || maxWidth < 1) {
        m_pTextTex = nullptr;
        return;
    }

    (void)COLORVAL;
    const CHyprColor COLOR = m_bForcedTitleColor.value_or(currentTextColor());
    m_pTextTex             = g_pHyprRenderer->renderText(m_szLastTitle, COLOR, scaledSize, false, FONT, maxWidth);
}

size_t CHyprBar::getVisibleButtonCount(Config::INTEGER barButtonPadding, Config::INTEGER barPadding, const Vector2D& bufferSize, const float scale) {
    float  availableSpace = bufferSize.x - barPadding * scale * 2;
    size_t count          = 0;

    for (const auto& button : g_pGlobalState->buttons) {
        const float buttonSpace = (button.size + barButtonPadding) * scale;
        if (availableSpace >= buttonSpace) {
            count++;
            availableSpace -= buttonSpace;
        } else
            break;
    }

    return count;
}

void CHyprBar::renderBarButtons(CBox* barBox, const float scale, const float a) {
    const auto BARBUTTONPADDING = g_pGlobalState->config.barButtonPadding->value();
    const auto BARPADDING       = g_pGlobalState->config.barPadding->value();
    const auto ALIGNBUTTONS     = g_pGlobalState->config.barButtonsAlignment->value();
    const auto INACTIVECOLOR    = g_pGlobalState->config.inactiveButtonColor->value();

    const bool BUTTONSRIGHT    = ALIGNBUTTONS != "left";
    const auto visibleCount    = getVisibleButtonCount(BARBUTTONPADDING, BARPADDING, Vector2D{barBox->w, barBox->h}, scale);
    const bool INVALIDATEICONS = m_bButtonsDirty || m_bWindowSizeChanged;

    int        offset = BARPADDING * scale;
    for (size_t i = 0; i < visibleCount; ++i) {
        auto&      button           = g_pGlobalState->buttons[i];
        const auto scaledButtonSize = button.size * scale;
        const auto scaledButtonsPad = BARBUTTONPADDING * scale;

        if (!button.breezeKind.empty()) {
            // Breeze: el círculo solo aparece al pasar el ratón
            if (m_iButtonHoverState & (1 << i)) {
                auto color = button.bgcol;
                color.a *= a;
                CBox buttonBox = {barBox->x + (BUTTONSRIGHT ? barBox->w - offset - scaledButtonSize : offset), barBox->y + (barBox->h - scaledButtonSize) / 2.0,
                                  scaledButtonSize, scaledButtonSize};
                buttonBox.round();
                g_pHyprOpenGL->renderRect(buttonBox, color, {.round = static_cast<int>(std::round(scaledButtonSize / 2.0)), .roundingPower = 2.F});
            }
            offset += scaledButtonsPad + scaledButtonSize;
            continue;
        }

        auto       color = button.bgcol;

        if (INACTIVECOLOR > 0) {
            color = m_bWindowHasFocus ? color : configColor(INACTIVECOLOR);
            if (INVALIDATEICONS && button.userfg && button.iconTex)
                button.iconTex = nullptr;
        }

        color.a *= a;

        CBox buttonBox = {barBox->x + (BUTTONSRIGHT ? barBox->w - offset - scaledButtonSize : offset), barBox->y + (barBox->h - scaledButtonSize) / 2.0, scaledButtonSize,
                          scaledButtonSize};
        buttonBox.round();

        g_pHyprOpenGL->renderRect(buttonBox, color, {.round = static_cast<int>(std::round(scaledButtonSize / 2.0)), .roundingPower = 2.F});

        offset += scaledButtonsPad + scaledButtonSize;
    }
}

void CHyprBar::renderBarButtonsText(CBox* barBox, const float scale, const float a) {
    const auto HEIGHT           = g_pGlobalState->config.barHeight->value();
    const auto BARBUTTONPADDING = g_pGlobalState->config.barButtonPadding->value();
    const auto BARPADDING       = g_pGlobalState->config.barPadding->value();
    const auto ALIGNBUTTONS     = g_pGlobalState->config.barButtonsAlignment->value();
    const auto ICONONHOVER      = g_pGlobalState->config.iconOnHover->value();

    const bool BUTTONSRIGHT = ALIGNBUTTONS != "left";
    const auto visibleCount = getVisibleButtonCount(BARBUTTONPADDING, BARPADDING, Vector2D{barBox->w, barBox->h}, scale);
    const auto COORDS       = cursorRelativeToBar();

    int        offset        = BARPADDING * scale;
    float      noScaleOffset = BARPADDING;

    for (size_t i = 0; i < visibleCount; ++i) {
        auto&      button           = g_pGlobalState->buttons[i];
        const auto scaledButtonSize = button.size * scale;
        const auto scaledButtonsPad = BARBUTTONPADDING * scale;

        // check if hovering here
        const auto BARBUF     = Vector2D{(int)assignedBoxGlobal().w, HEIGHT};
        Vector2D   currentPos = Vector2D{(BUTTONSRIGHT ? BARBUF.x - BARBUTTONPADDING - button.size - noScaleOffset : noScaleOffset), (BARBUF.y - button.size) / 2.0}.floor();
        bool       hovering   = VECINRECT(COORDS, currentPos.x, currentPos.y, currentPos.x + button.size + BARBUTTONPADDING, currentPos.y + button.size);
        noScaleOffset += BARBUTTONPADDING + button.size;

        if (!button.breezeKind.empty()) {
            const bool hovered = (m_iButtonHoverState & (1 << i)) != 0;
            // con hover el icono toma el color de la barra sobre el círculo, como en Breeze
            const auto fg  = hovered ? m_cRealBarColor->value() : (button.userfg && m_bWindowHasFocus ? button.fgcol : currentTextColor());
            const int  px  = std::round(scaledButtonSize);
            auto       tex = breezeIcon(button, Fullscreen::controller()->isFullscreen(m_pWindow.lock()), CHyprColor(fg.r, fg.g, fg.b, 1.F), px);
            if (tex && tex->m_texID != 0) {
                CBox pos = {barBox->x + (BUTTONSRIGHT ? barBox->width - offset - scaledButtonSize : offset), barBox->y + (barBox->height - scaledButtonSize) / 2.0,
                            scaledButtonSize, scaledButtonSize};
                pos.round();
                g_pHyprOpenGL->renderTexture(tex, pos, {.a = a});
            }
            offset += scaledButtonsPad + scaledButtonSize;

            if (hovering != hovered) {
                m_iButtonHoverState ^= (1 << i);
                damageEntire();
            }
            continue;
        }

        if ((!button.iconTex || button.iconTex->m_texID == 0) && !button.icon.empty()) {
            // render icon
            auto fgcol = button.userfg ? button.fgcol : (button.bgcol.r + button.bgcol.g + button.bgcol.b < 1) ? CHyprColor(0xFFFFFFFF) : CHyprColor(0xFF000000);

            button.iconTex = g_pHyprRenderer->renderText(button.icon, fgcol, std::round(button.size * 0.62 * scale), false, "sans", scaledButtonSize);
        }

        if (!button.iconTex || button.iconTex->m_texID == 0)
            continue;

        const auto iconX = barBox->x + (BUTTONSRIGHT ? barBox->width - offset - scaledButtonSize / 2.0 : offset + scaledButtonSize / 2.0) - button.iconTex->m_size.x / 2.0;
        const auto iconY = barBox->y + barBox->height / 2.0 - button.iconTex->m_size.y / 2.0;
        CBox       pos   = {iconX, iconY, button.iconTex->m_size.x, button.iconTex->m_size.y};

        if (!ICONONHOVER || (ICONONHOVER && m_iButtonHoverState > 0))
            g_pHyprOpenGL->renderTexture(button.iconTex, pos, {.a = a});
        offset += scaledButtonsPad + scaledButtonSize;

        bool currentBit = (m_iButtonHoverState & (1 << i)) != 0;
        if (hovering != currentBit) {
            m_iButtonHoverState ^= (1 << i);
            // damage to get rid of some artifacts when icons are "hidden"
            damageEntire();
        }
    }
}

void CHyprBar::draw(PHLMONITOR pMonitor, const float& a) {
    const auto ENABLED = g_pGlobalState->config.enabled->value();

    if (m_bLastEnabledState != ENABLED) {
        m_bLastEnabledState = ENABLED;
        g_pDecorationPositioner->repositionDeco(this);
    }

    if (m_hidden || !Desktop::View::validMapped(m_pWindow) || !ENABLED)
        return;

    const auto PWINDOW = m_pWindow.lock();

    if (!PWINDOW->m_ruleApplicator->decorate().valueOrDefault())
        return;

    auto data = CBarPassElement::SBarData{this, a};
    g_pHyprRenderer->m_renderPass.add(makeUnique<CBarPassElement>(data));
}

void CHyprBar::renderPass(PHLMONITOR pMonitor, const float& a) {
    const auto  PWINDOW = m_pWindow.lock();

    static auto PENABLEBLURGLOBAL = CConfigValue<Config::BOOL>("decoration:blur:enabled");
    const auto  BARCOLOR          = g_pGlobalState->config.barColor->value();
    const auto  HEIGHT            = g_pGlobalState->config.barHeight->value();
    const auto  PRECEDENCE        = g_pGlobalState->config.barPrecedenceOverBorder->value();
    const auto  ALIGNBUTTONS      = g_pGlobalState->config.barButtonsAlignment->value();
    const auto  ENABLETITLE       = g_pGlobalState->config.barTitleEnabled->value();
    const auto  ENABLEBLUR        = g_pGlobalState->config.barBlur->value();
    const auto  INACTIVECOLOR     = g_pGlobalState->config.inactiveButtonColor->value();

    (void)INACTIVECOLOR;
    {
        bool currentWindowFocus = PWINDOW == Desktop::focusState()->window();
        if (currentWindowFocus != m_bWindowHasFocus) {
            m_bWindowHasFocus    = currentWindowFocus;
            m_bButtonsDirty      = true;
            m_bTitleColorChanged = true;
        }
    }

    const auto       INACTIVEBAR = g_pGlobalState->config.inactiveBarColor->value();
    const CHyprColor DEST_COLOR  = m_bForcedBarColor.value_or(configColor(!m_bWindowHasFocus && INACTIVEBAR > 0 ? INACTIVEBAR : BARCOLOR));
    if (DEST_COLOR != m_cRealBarColor->goal())
        *m_cRealBarColor = DEST_COLOR;

    CHyprColor color = m_cRealBarColor->value();

    color.a *= a;
    const bool BUTTONSRIGHT = ALIGNBUTTONS != "left";
    const bool SHOULDBLUR   = ENABLEBLUR && *PENABLEBLURGLOBAL && color.a < 1.F;

    if (HEIGHT < 1) {
        m_iLastHeight = HEIGHT;
        return;
    }

    const auto PWORKSPACE      = PWINDOW->m_workspace;
    const auto WORKSPACEOFFSET = PWORKSPACE && !PWINDOW->m_pinned ? PWORKSPACE->m_renderOffset->value() : Vector2D();

    const auto ROUNDING = PWINDOW->rounding() + (PRECEDENCE ? 0 : PWINDOW->getRealBorderSize());

    const auto scaledRounding = ROUNDING > 0 ? ROUNDING * pMonitor->m_scale - 2 /* idk why but otherwise it looks bad due to the gaps */ : 0;

    m_seExtents = {{0, HEIGHT}, {}};

    const auto DECOBOX = assignedBoxGlobal();

    const auto BARBUF = DECOBOX.size() * pMonitor->m_scale;

    CBox       titleBarBox = {DECOBOX.x - pMonitor->m_position.x, DECOBOX.y - pMonitor->m_position.y, DECOBOX.w,
                              DECOBOX.h + ROUNDING * 3 /* to fill the bottom cuz we can't disable rounding there */};

    titleBarBox.translate(PWINDOW->m_floatingOffset).scale(pMonitor->m_scale).round();

    if (titleBarBox.w < 1 || titleBarBox.h < 1)
        return;

    g_pHyprOpenGL->scissor(titleBarBox);

    if (ROUNDING) {
        CBox windowBox = {PWINDOW->position(Desktop::View::IGeometric::GEOMETRIC_CURRENT).x + PWINDOW->m_floatingOffset.x - pMonitor->m_position.x,
                          PWINDOW->position(Desktop::View::IGeometric::GEOMETRIC_CURRENT).y + PWINDOW->m_floatingOffset.y - pMonitor->m_position.y + 1, PWINDOW->size(Desktop::View::IGeometric::GEOMETRIC_CURRENT).x,
                          PWINDOW->size(Desktop::View::IGeometric::GEOMETRIC_CURRENT).y - 1};

        if (windowBox.w < 1 || windowBox.h < 1)
            return;

        glClearStencil(0);
        glClear(GL_STENCIL_BUFFER_BIT);

        g_pHyprOpenGL->setCapStatus(GL_STENCIL_TEST, true);

        glStencilFunc(GL_ALWAYS, 1, -1);
        glStencilOp(GL_KEEP, GL_KEEP, GL_REPLACE);

        glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE);

        windowBox.translate(WORKSPACEOFFSET).scale(pMonitor->m_scale).round();
        g_pHyprOpenGL->renderRect(windowBox, CHyprColor(0, 0, 0, 0), {.round = scaledRounding, .roundingPower = m_pWindow->roundingPower()});
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE);

        glStencilFunc(GL_NOTEQUAL, 1, -1);
        glStencilOp(GL_KEEP, GL_KEEP, GL_REPLACE);
    }

    if (SHOULDBLUR)
        g_pHyprOpenGL->renderRect(titleBarBox, color, {.round = scaledRounding, .roundingPower = m_pWindow->roundingPower(), .blur = true, .blurA = a});
    else
        g_pHyprOpenGL->renderRect(titleBarBox, color, {.round = scaledRounding, .roundingPower = m_pWindow->roundingPower()});

    // render title
    if (ENABLETITLE && (m_szLastTitle != PWINDOW->m_title || m_bWindowSizeChanged || !m_pTextTex || m_pTextTex->m_texID == 0 || m_bTitleColorChanged)) {
        m_szLastTitle = PWINDOW->m_title;
        renderBarTitle(BARBUF, pMonitor->m_scale);
    }

    if (ROUNDING) {
        // cleanup stencil
        glClearStencil(0);
        glClear(GL_STENCIL_BUFFER_BIT);
        g_pHyprOpenGL->setCapStatus(GL_STENCIL_TEST, false);
        glStencilMask(-1);
        glStencilFunc(GL_ALWAYS, 1, 0xFF);
    }

    CBox textBox = {titleBarBox.x, titleBarBox.y, (int)BARBUF.x, (int)BARBUF.y};
    if (ENABLETITLE && m_pTextTex) {
        const auto BARPADDING       = g_pGlobalState->config.barPadding->value();
        const auto BARBUTTONPADDING = g_pGlobalState->config.barButtonPadding->value();
        const auto ALIGN            = g_pGlobalState->config.barTextAlign->value();

        float      buttonSizes = BARBUTTONPADDING;
        for (auto& b : g_pGlobalState->buttons) {
            buttonSizes += b.size + BARBUTTONPADDING;
        }

        const auto scaledBorderSize  = PWINDOW->getRealBorderSize() * pMonitor->m_scale;
        const auto scaledButtonsSize = buttonSizes * pMonitor->m_scale;
        const auto scaledBarPadding  = BARPADDING * pMonitor->m_scale;
        const auto xOffset           = ALIGN == "left" ? std::round(scaledBarPadding + (BUTTONSRIGHT ? 0 : scaledButtonsSize)) :
                                                         std::round(((BARBUF.x - scaledBorderSize) / 2.0 - m_pTextTex->m_size.x / 2.0));
        const auto yOffset           = std::round((BARBUF.y - m_pTextTex->m_size.y) / 2.0);
        CBox       titleBox          = {textBox.x + xOffset, textBox.y + yOffset, m_pTextTex->m_size.x, m_pTextTex->m_size.y};

        g_pHyprOpenGL->renderTexture(m_pTextTex, titleBox, {.a = a});
    }

    renderBarButtons(&textBox, pMonitor->m_scale, a);
    m_bButtonsDirty = false;

    g_pHyprOpenGL->scissor(nullptr);

    renderBarButtonsText(&textBox, pMonitor->m_scale, a);

    m_bWindowSizeChanged = false;
    m_bTitleColorChanged = false;

    // dynamic updates change the extents
    if (m_iLastHeight != HEIGHT) {
        PWINDOW->layoutTarget()->recalc();
        m_iLastHeight = HEIGHT;
    }
}

eDecorationType CHyprBar::getDecorationType() {
    return DECORATION_CUSTOM;
}

void CHyprBar::updateWindow(PHLWINDOW pWindow) {
    damageEntire();
}

void CHyprBar::onConfigReloaded() {
    m_bButtonsDirty      = true;
    m_bTitleColorChanged = true;
    m_pTextTex           = nullptr;

    g_pDecorationPositioner->repositionDeco(this);
    damageEntire();
}

void CHyprBar::damageEntire() {
    g_pHyprRenderer->damageBox(assignedBoxGlobal());
}

Vector2D CHyprBar::cursorRelativeToBar() {
    return g_pInputManager->getMouseCoordsInternal() - assignedBoxGlobal().pos();
}

eDecorationLayer CHyprBar::getDecorationLayer() {
    return DECORATION_LAYER_UNDER;
}

uint64_t CHyprBar::getDecorationFlags() {
    return DECORATION_ALLOWS_MOUSE_INPUT | (g_pGlobalState->config.barPartOfWindow->value() ? DECORATION_PART_OF_MAIN_WINDOW : 0);
}

CBox CHyprBar::assignedBoxGlobal() {
    if (!Desktop::View::validMapped(m_pWindow))
        return {};

    CBox box = m_bAssignedBox;
    box.translate(g_pDecorationPositioner->getEdgeDefinedPoint(DECORATION_EDGE_TOP, m_pWindow.lock()));

    const auto PWORKSPACE      = m_pWindow->m_workspace;
    const auto WORKSPACEOFFSET = PWORKSPACE && !m_pWindow->m_pinned ? PWORKSPACE->m_renderOffset->value() : Vector2D();

    return box.translate(WORKSPACEOFFSET);
}

PHLWINDOW CHyprBar::getOwner() {
    return m_pWindow.lock();
}



void CHyprBar::updateRules() {
    const auto PWINDOW              = m_pWindow.lock();
    if (!PWINDOW)
        return;

    auto       prevHidden           = m_hidden;
    auto       prevForcedTitleColor = m_bForcedTitleColor;

    m_bForcedBarColor   = std::nullopt;
    m_bForcedTitleColor = std::nullopt;
    m_hidden            = isKnownCSD(PWINDOW);

    if (PWINDOW->m_ruleApplicator) {
        if (PWINDOW->m_ruleApplicator->m_otherProps.props.contains(g_pGlobalState->nobarRuleIdx))
            m_hidden = truthy(PWINDOW->m_ruleApplicator->m_otherProps.props.at(g_pGlobalState->nobarRuleIdx)->effect);
        if (PWINDOW->m_ruleApplicator->m_otherProps.props.contains(g_pGlobalState->barColorRuleIdx))
            m_bForcedBarColor = CHyprColor(Config::ParserUtils::parseColor(PWINDOW->m_ruleApplicator->m_otherProps.props.at(g_pGlobalState->barColorRuleIdx)->effect).value_or(0));
        if (PWINDOW->m_ruleApplicator->m_otherProps.props.contains(g_pGlobalState->titleColorRuleIdx))
            m_bForcedTitleColor = CHyprColor(Config::ParserUtils::parseColor(PWINDOW->m_ruleApplicator->m_otherProps.props.at(g_pGlobalState->titleColorRuleIdx)->effect).value_or(0));
    }

    if (prevHidden != m_hidden)
        g_pDecorationPositioner->repositionDeco(this);
    if (prevForcedTitleColor != m_bForcedTitleColor)
        m_bTitleColorChanged = true;

    if (!m_pStateChangedCallback) {
        auto pXDG = PWINDOW->m_xdgSurface.lock();
        if (pXDG && pXDG->m_toplevel.lock()) {
            m_pStateChangedCallback = pXDG->m_toplevel.lock()->m_events.stateChanged.listen([this, wpTop = pXDG->m_toplevel] {
                auto top = wpTop.lock();
                auto pw = m_pWindow.lock();
                if (pw && top && top->m_state.requestsMinimize.value_or(false)) {
                    std::string addr = std::format("0x{:x}", (uintptr_t)pw.get());
                    Config::Supplementary::executor()->spawn("/home/sasel/.config/hypr/scripts/toggle-minimize.py min " + addr);
                }
            });
        } else if (auto pXWayland = PWINDOW->m_xwaylandSurface.lock()) {
            m_pStateChangedCallback = pXWayland->m_events.stateChanged.listen([this, wpXW = PWINDOW->m_xwaylandSurface] {
                auto xw = wpXW.lock();
                auto pw = m_pWindow.lock();
                if (pw && xw && xw->m_state.requestsMinimize.value_or(false)) {
                    std::string addr = std::format("0x{:x}", (uintptr_t)pw.get());
                    Config::Supplementary::executor()->spawn("/home/sasel/.config/hypr/scripts/toggle-minimize.py min " + addr);
                }
            });
        }
    }
}

void CHyprBar::damageOnButtonHover() {
    const auto BARPADDING       = g_pGlobalState->config.barPadding->value();
    const auto BARBUTTONPADDING = g_pGlobalState->config.barButtonPadding->value();
    const auto HEIGHT           = g_pGlobalState->config.barHeight->value();
    const auto ALIGNBUTTONS     = g_pGlobalState->config.barButtonsAlignment->value();
    const bool BUTTONSRIGHT     = ALIGNBUTTONS != "left";

    float      offset = BARPADDING;

    const auto COORDS = cursorRelativeToBar();

    for (auto& b : g_pGlobalState->buttons) {
        const auto BARBUF     = Vector2D{(int)assignedBoxGlobal().w, HEIGHT};
        Vector2D   currentPos = Vector2D{(BUTTONSRIGHT ? BARBUF.x - BARBUTTONPADDING - b.size - offset : offset), (BARBUF.y - b.size) / 2.0}.floor();

        bool       hover = VECINRECT(COORDS, currentPos.x, currentPos.y, currentPos.x + b.size + BARBUTTONPADDING, currentPos.y + b.size);

        if (hover != m_bButtonHovered) {
            m_bButtonHovered = hover;
            damageEntire();
        }

        offset += BARBUTTONPADDING + b.size;
    }
}
