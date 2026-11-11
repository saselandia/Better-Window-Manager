#pragma once

#define WLR_USE_UNSTABLE

#include <hyprland/src/render/decorations/IHyprWindowDecoration.hpp>
#include <hyprland/src/render/OpenGL.hpp>
#include <hyprland/src/render/gl/GLTexture.hpp>
#include <hyprland/src/devices/IPointer.hpp>
#include <hyprland/src/devices/ITouch.hpp>
#include <hyprland/src/desktop/rule/windowRule/WindowRule.hpp>
#include <hyprland/src/helpers/AnimatedVariable.hpp>
#include <hyprland/src/helpers/time/Time.hpp>
#include <hyprland/src/helpers/signal/Signal.hpp>
#include "globals.hpp"
#include "barRemote.hpp"

#define private public
#include <hyprland/src/managers/input/InputManager.hpp>
#undef private

namespace Event {
    struct SCallbackInfo;
}

void checkAndTriggerEdgeSnap(PHLWINDOW pWindow, const Vector2D& mousePos);

class CHyprBar : public IHyprWindowDecoration {
  public:
    CHyprBar(PHLWINDOW);
    virtual ~CHyprBar();

    virtual SDecorationPositioningInfo getPositioningInfo();

    virtual void                       onPositioningReply(const SDecorationPositioningReply& reply);

    virtual void                       draw(PHLMONITOR, float const& a);

    virtual eDecorationType            getDecorationType();

    virtual void                       updateWindow(PHLWINDOW);

    virtual void                       damageEntire();

    virtual eDecorationLayer           getDecorationLayer();

    virtual uint64_t                   getDecorationFlags();

    bool                               m_bButtonsDirty = true;

    virtual std::string                getDisplayName();

    PHLWINDOW                          getOwner();

    void                               updateRules();
    void                               onConfigReloaded();

    WP<CHyprBar>                       m_self;
    bool                               m_hidden = false;
    bool                               inputIsValid();
    bool                               isDragging() const;

    // bwm-decorator (F6b): la barra la dibuja la decoración de KDE activa; sin auxiliar, la plana de siempre
    uint32_t                           remoteId() const {
        return m_remote.id;
    }
    bool                               remoteActive();
    void                               onRemoteReady();
    void                               onRemoteLost();
    void                               onRemoteReconfigured();
    void                               onRemoteMessage(const BwmDeco::SMessage& msg, int fd);
    const SRemoteState&                remote() const {
        return m_remote;
    }
    std::optional<CBox>                frameBoxGlobal(bool forRender);
    void                               renderShadow(PHLMONITOR pMonitor, float a);

  private:
    SBoxExtents                m_seExtents;

    PHLWINDOWREF               m_pWindow;

    CBox                       m_bAssignedBox;

    SP<Render::ITexture>       m_pTextTex;

    bool                       m_bWindowSizeChanged = false;

    bool                       m_bTitleColorChanged = false;
    bool                       m_bButtonHovered     = false;
    bool                       m_bLastEnabledState  = false;
    bool                       m_bWindowHasFocus    = false;
    std::optional<CHyprColor>  m_bForcedBarColor;
    std::optional<CHyprColor>  m_bForcedTitleColor;

    Time::steady_tp            m_lastMouseDown = Time::steadyNow();

    PHLANIMVAR<CHyprColor>     m_cRealBarColor;

    Vector2D                   cursorRelativeToBar();
    CHyprColor                 currentTextColor();

    void                       renderPass(PHLMONITOR, float const& a);
    void                       renderBarTitle(const Vector2D& bufferSize, const float scale);
    void renderBarButtons(CBox* barBox, const float scale, const float a);
    void renderBarButtonsText(CBox* barBox, const float scale, const float a);
    void damageOnButtonHover();

    void onMouseButton(Event::SCallbackInfo& info, IPointer::SButtonEvent e);
    void onTouchDown(Event::SCallbackInfo& info, ITouch::SDownEvent e);
    void onTouchUp(Event::SCallbackInfo& info, ITouch::SUpEvent e);
    void onMouseMove(Vector2D coords);
    void onTouchMove(Event::SCallbackInfo& info, ITouch::SMotionEvent e);

    void handleDownEvent(Event::SCallbackInfo& info, std::optional<ITouch::SDownEvent> touchEvent);
    void handleUpEvent(Event::SCallbackInfo& info);
    void handleMovement();
    bool doButtonPress(Config::INTEGER barPadding, Config::INTEGER barButtonPadding, Config::INTEGER barHeight, Vector2D COORDS, bool BUTTONSRIGHT);

    CBox assignedBoxGlobal();

    CHyprSignalListener m_pMouseButtonCallback;
    CHyprSignalListener m_pTouchDownCallback;
    CHyprSignalListener m_pTouchUpCallback;

    CHyprSignalListener m_pTouchMoveCallback;
    CHyprSignalListener m_pMouseMoveCallback;
    CHyprSignalListener m_pStateChangedCallback;

    std::string         m_szLastTitle;

    bool                m_bDraggingThis  = false;
    bool                m_bTouchEv       = false;
    bool                m_bDragPending   = false;
    bool                m_bCancelledDown = false;
    int                 m_touchId        = 0;
    bool                m_bDraggingCSD   = false;
    bool                m_bDragInitiated = false;
    Vector2D            m_vDragStartMouse;
    Vector2D            m_vGrabOffset;

    // store hover state for buttons as a bitfield
    unsigned int m_iButtonHoverState = 0;

    // for dynamic updates
    int    m_iLastHeight = 0;

    // bwm-decorator
    SRemoteState        m_remote;
    bool                m_bResizing = false;
    Time::steady_tp     m_lastTitleClick;
    CHyprSignalListener m_pAxisCallback;

    void                syncRemote();
    void                destroyRemote();
    BwmDeco::SWindowState currentRemoteState();
    void                updateRemotePositioning();
    void                renderRemote(PHLMONITOR pMonitor, float a);
    void                uploadRemoteTexture();
    bool                remoteInputAllowed();
    bool                remoteHit(const Vector2D& mouse, Vector2D* local);
    bool                remoteMouseButton(Event::SCallbackInfo& info, const IPointer::SButtonEvent& e);
    void                remoteMouseMove(const Vector2D& mouse);
    void                onAxis(Event::SCallbackInfo& info, const IPointer::SAxisEvent& e);
    void                handlePointerResult(const BwmDeco::SPointerResult& r);
    void                handleRequest(const BwmDeco::SRequest& r);
    void                runDoubleClickAction();
    void                toggleAxisMaximize(BwmDeco::eMaximizeAxis axis);
    void                showWindowMenu(const Vector2D& global);
    void                spawnMinimize();
    std::optional<CBox> contentBoxGlobal(bool forRender);
    void                applyRoundingOverride(int value);
    void                releaseRemoteBuffers();

    size_t getVisibleButtonCount(Config::INTEGER barButtonPadding, Config::INTEGER barPadding, const Vector2D& bufferSize, const float scale);

    friend class CBarPassElement;
    friend class CBreezeShadow;
};
