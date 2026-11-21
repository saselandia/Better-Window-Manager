// Esquinas superiores cuadradas en las ventanas con barra: la barra queda
// redondeada arriba y se une en recto con el contenido, como en KDE Plasma.
// Hyprland solo redondea las 4 esquinas a la vez, así que tras grabar las
// ventanas en el pase cada superficie principal con barra se reparte en dos:
// el original, recortado por debajo de la franja superior (conserva el redondeo
// de abajo), y una copia sin redondeo que dibuja sólo esa franja. No se solapan:
// una ventana translúcida no se mezcla dos veces arriba.
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
#include <string_view>
#include <format>

// La lista de elementos del pase es privada.
#define private public
#include <hyprland/src/render/pass/Pass.hpp>
#undef private

#include <hyprland/src/render/pass/SurfacePassElement.hpp>
#include <hyprland/src/render/Renderer.hpp>
#include <hyprland/src/desktop/view/Window.hpp>
#include <hyprland/src/output/Monitor.hpp>

#include "barDeco.hpp"
#include "SquareTop.hpp"

static constexpr std::string_view SQUARE_PASS_NAME = "CBarSquareTopPassElement";

class CBarSquareTopPassElement : public CSurfacePassElement {
  public:
    CBarSquareTopPassElement(const SRenderData& data) : CSurfacePassElement(data) {}

    // Sin región opaca: así el pase nunca descarta por oclusión la superficie original.
    virtual CRegion opaqueRegion() {
        return {};
    }
    virtual bool needsLiveBlur() {
        return false;
    }
    virtual bool needsPrecomputeBlur() {
        return false;
    }
    virtual const char* passName() {
        return SQUARE_PASS_NAME.data();
    }
};

static bool hasVisibleBar(PHLWINDOW w) {
    for (auto& b : g_pGlobalState->bars) {
        if (b && b->getOwner() == w)
            return !b->m_hidden;
    }
    return false;
}

void squareBarredWindowTops() {
    if (!g_pGlobalState || !g_pGlobalState->config.enabled->value() || !g_pHyprRenderer)
        return;

    auto&                                            elems = g_pHyprRenderer->m_renderPass.m_passElements;
    std::vector<std::pair<size_t, UP<IPassElement>>> inserts;

    for (size_t i = 0; i < elems.size(); ++i) {
        auto& el = elems[i].element;
        if (!el || el->type() != EK_SURFACE || std::string_view(el->passName()) != "CSurfacePassElement")
            continue;

        // ya procesada (p. ej. si el evento se emite más de una vez en el frame)
        if (i + 1 < elems.size() && elems[i + 1].element && std::string_view(elems[i + 1].element->passName()) == SQUARE_PASS_NAME)
            continue;

        auto*       surf = static_cast<CSurfacePassElement*>(el.get());
        const auto& d    = surf->m_data;

        if (!d.mainSurface || d.popup || d.dontRound || d.rounding <= 0 || !d.pWindow || !d.surface || !d.pMonitor || !d.texture)
            continue;
        if (d.pWindow->resource() != d.surface || !hasVisibleBar(d.pWindow))
            continue;

        const auto scale = d.pMonitor->m_scale;
        // d.rounding viene en píxeles escalados; la franja va en lógicos (+2 de margen)
        CBox full = surf->getTexBox();
        full.scale(scale).round();
        const double stripH = std::min(full.h, std::round((d.rounding / scale + 2.0) * scale));
        CBox         strip{full.x, full.y, full.w, stripH};
        CBox         rest{full.x, full.y + stripH, full.w, full.h - stripH};
        if (!d.clipBox.empty()) {
            strip = strip.intersection(d.clipBox);
            rest  = rest.intersection(d.clipBox);
        }
        if (strip.w < 1 || strip.h < 1)
            continue;

        auto copy      = d;
        copy.dontRound = true;
        copy.clipBox   = strip;
        // The strip is drawn only once now, so it keeps the window's blur too
        inserts.emplace_back(i + 1, makeUnique<CBarSquareTopPassElement>(copy));
        // An empty clipBox means "no clip": a window shorter than the strip draws nothing else
        surf->m_data.clipBox = rest.w >= 1 && rest.h >= 1 ? rest : CBox{full.x, full.y + full.h, full.w, 1};
    }

    for (auto it = inserts.rbegin(); it != inserts.rend(); ++it)
        elems.insert(elems.begin() + it->first, Render::CRenderPass::SPassElementData{.element = std::move(it->second)});
}

void removeSquareTopElements() {
    if (g_pHyprRenderer)
        g_pHyprRenderer->m_renderPass.removeAllOfType(std::string(SQUARE_PASS_NAME));
}
