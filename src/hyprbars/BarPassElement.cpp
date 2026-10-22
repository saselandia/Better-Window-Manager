#include "BarPassElement.hpp"
#include <hyprland/src/render/OpenGL.hpp>
#include <hyprland/src/render/Renderer.hpp>
#include "barDeco.hpp"

using namespace Render::GL;

CBarPassElement::CBarPassElement(const CBarPassElement::SBarData& data_) : data(data_) {
    ;
}

std::vector<UP<IPassElement>> CBarPassElement::draw() {
    data.deco->renderPass(g_pHyprRenderer->m_renderData.pMonitor.lock(), data.a);
    return {};
}

bool CBarPassElement::needsLiveBlur() {
    static auto PENABLEBLURGLOBAL = CConfigValue<Config::BOOL>("decoration:blur:enabled");

    CHyprColor  color = data.deco->m_bForcedBarColor.value_or(CHyprColor{static_cast<uint64_t>(g_pGlobalState->config.barColor->value())});
    color.a *= data.a;
    const bool SHOULDBLUR = g_pGlobalState->config.barBlur->value() && *PENABLEBLURGLOBAL && color.a < 1.F;

    return SHOULDBLUR;
}

std::optional<CBox> CBarPassElement::boundingBox() {
    // Temporary fix: expand the bar bb a bit, otherwise occlusion gets too aggressive.
    return data.deco->assignedBoxGlobal().translate(-g_pHyprRenderer->m_renderData.pMonitor->m_position).expand(10);
}

bool CBarPassElement::needsPrecomputeBlur() {
    return false;
}

CSnapPreviewPassElement::CSnapPreviewPassElement(const CSnapPreviewPassElement::SSnapData& data_) : data(data_) {
    ;
}

std::vector<UP<IPassElement>> CSnapPreviewPassElement::draw() {
    auto pMonitor = g_pHyprRenderer->m_renderData.pMonitor.lock();
    if (!pMonitor)
        return {};

    CBox box = data.box;
    box.translate(-pMonitor->m_position).scale(pMonitor->m_scale).round();

    const int inset = std::max(4, (int)std::round(6 * pMonitor->m_scale));
    box.x += inset;
    box.y += inset;
    box.w = std::max(10, (int)box.w - inset * 2);
    box.h = std::max(10, (int)box.h - inset * 2);

    const int radius     = std::max(6, (int)std::round(8 * pMonitor->m_scale));
    const int borderSize = std::max(2, (int)std::round(3 * pMonitor->m_scale));

    g_pHyprOpenGL->scissor(nullptr);

    // Translucent KDE Plasma Breeze Blue highlight fill (#3daee9)
    CHyprColor fillCol{61.0 / 255.0, 174.0 / 255.0, 233.0 / 255.0, 0.35};
    g_pHyprOpenGL->renderRect(box, fillCol, {.round = radius, .roundingPower = 2.0f});

    // Crisp KDE Plasma Breeze Blue border (#3daee9)
    Config::CGradientValueData borderGrad(CHyprColor{61.0 / 255.0, 174.0 / 255.0, 233.0 / 255.0, 0.95});
    g_pHyprOpenGL->renderBorder(box, borderGrad, {.round = radius, .roundingPower = 2.0f, .borderSize = borderSize, .a = 1.0f});

    return {};
}

bool CSnapPreviewPassElement::needsLiveBlur() {
    return false;
}

bool CSnapPreviewPassElement::needsPrecomputeBlur() {
    return false;
}

std::optional<CBox> CSnapPreviewPassElement::boundingBox() {
    if (!g_pHyprRenderer->m_renderData.pMonitor)
        return std::nullopt;
    CBox b = data.box;
    return b.translate(-g_pHyprRenderer->m_renderData.pMonitor->m_position).expand(10);
}

