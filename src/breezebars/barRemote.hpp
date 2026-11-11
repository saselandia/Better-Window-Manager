// Estado de una barra cuando la dibuja bwm-decorator (F6b). Lo usa CHyprBar (barDeco.hpp).
#pragma once

#include "DecoLogic.hpp"

#include <hyprland/src/render/decorations/IHyprWindowDecoration.hpp>
#include <hyprland/src/render/pass/PassElement.hpp>
#include <hyprland/src/helpers/time/Time.hpp>

#include <array>
#include <optional>
#include <string>
#include <vector>

class CHyprBar;

struct SRemoteBuffer {
    void*  map  = nullptr;
    size_t size = 0;
};

struct SRemoteState {
    uint32_t                                id      = 0;
    bool                                    created = false;
    std::optional<BwmDeco::SWindowState>    lastSent;
    std::optional<BwmDeco::SGeometry>       geometry;

    // Último Frame, copiado al recibirlo (el auxiliar reutiliza sus búferes)
    std::array<SRemoteBuffer, 2>            buffers;
    std::vector<uint8_t>                    pixels;
    uint32_t                                width = 0, height = 0, stride = 0;
    std::array<BwmDeco::SPart, 4>           parts;
    bool                                    hasFrame = false;
    std::vector<BwmDeco::SPixelRect>        pendingDamage;
    SP<Render::ITexture>                    texture;

    // Sombra del tema (nueve trozos)
    std::optional<BwmDeco::SShadow>         shadow;
    std::vector<uint8_t>                    shadowPixels;
    bool                                    shadowDirty = false;
    SP<Render::ITexture>                    shadowTexture;

    // Puntero
    uint32_t                                section       = 0;
    bool                                    pointerInside = false;
    Vector2D                                lastPointer   = {-1, -1};
    uint32_t                                buttons       = 0;
    struct SPress {
        uint32_t button   = 0;
        bool     released = false;
    };
    std::optional<SPress> press;
    double                                  lastWheel = 0;

    // Posicionamiento con el que se colocó la decoración la última vez
    std::optional<BwmDeco::SExtents>        positionedBorders;
    bool                                    positionedRemote = false;
    int                                     roundingOverride = -1;

    // Maximizado sólo en un eje (botón central o derecho de maximizar, como KWin)
    bool                                    maxV = false, maxH = false;
    CBox                                    restoreV, restoreH;
};

// Sombra de la decoración de KDE: otra decoración de Hyprland para que sus bordes cuenten en los daños
// sin reservar espacio (como la sombra propia de Hyprland).
class CBreezeShadow : public IHyprWindowDecoration {
  public:
    CBreezeShadow(PHLWINDOW window, WP<CHyprBar> bar);
    virtual ~CBreezeShadow() = default;

    virtual SDecorationPositioningInfo getPositioningInfo();
    virtual void                       onPositioningReply(const SDecorationPositioningReply& reply);
    virtual void                       draw(PHLMONITOR, float const& a);
    virtual eDecorationType            getDecorationType();
    virtual void                       updateWindow(PHLWINDOW);
    virtual void                       damageEntire();
    virtual eDecorationLayer           getDecorationLayer();
    virtual uint64_t                   getDecorationFlags();
    virtual std::string                getDisplayName();

    void                               renderPass(PHLMONITOR pMonitor, float a);
    std::optional<CBox>                outerBox();

  private:
    PHLWINDOWREF                     m_window;
    WP<CHyprBar>                     m_bar;
    std::optional<BwmDeco::SExtents> m_positioned;
};

class CBreezeShadowPassElement : public IPassElement {
  public:
    CBreezeShadowPassElement(CBreezeShadow* deco, float a) : m_deco(deco), m_a(a) {}
    virtual ~CBreezeShadowPassElement() = default;
    virtual std::vector<UP<IPassElement>> draw() override;
    virtual bool                          needsLiveBlur() override {
        return false;
    }
    virtual bool needsPrecomputeBlur() override {
        return false;
    }
    virtual std::optional<CBox> boundingBox() override;
    virtual const char*         passName() override {
        return "CBreezeShadowPassElement";
    }
    virtual ePassElementType type() override {
        return EK_CUSTOM;
    }

  private:
    CBreezeShadow* m_deco;
    float          m_a;
};

// Tooltip de los botones (Request 5/6). Uno a la vez, como QToolTip.
void showDecorationToolTip(const std::string& text, const Vector2D& globalPos);
void hideDecorationToolTip();
void renderDecorationToolTip(eRenderStage stage);
void clearDecorationToolTip();
