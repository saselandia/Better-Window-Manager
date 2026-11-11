// Cálculos del plugin que no dependen de Hyprland (F6b): piezas del marco, daños, sombra de nueve
// trozos como KWin, secciones de redimensionado y acciones de la rueda. Se prueban en
// tests/breezebars_wire_test.cpp.
#pragma once

#include "DecoWire.hpp"

#include <algorithm>
#include <cmath>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

namespace BwmDeco {

    // Qt::WindowFrameSection → esquinas de Layout::eRectCorner de Hyprland
    // (1 arriba, 2 abajo, 4 izquierda, 8 derecha; 0 = no es un borde).
    inline uint8_t cornerForSection(uint32_t section) {
        constexpr uint8_t TOP = 1, BOTTOM = 2, LEFT = 4, RIGHT = 8;
        switch (section) {
            case 1: return LEFT;
            case 2: return TOP | LEFT;
            case 3: return TOP;
            case 4: return TOP | RIGHT;
            case 5: return RIGHT;
            case 6: return BOTTOM | RIGHT;
            case 7: return BOTTOM;
            case 8: return BOTTOM | LEFT;
            default: return 0;
        }
    }

    constexpr uint32_t TITLE_BAR_AREA = 9;

    // Dónde va cada pieza (arriba, abajo, izquierda, derecha) para un marco del tamaño actual. Si la
    // ventana cambió de tamaño y aún no hay imagen nueva, la última se estira a estos rectángulos.
    inline std::array<SRectD, 4> partTargets(const SRectD& frame, const SExtents& b) {
        const double midH = std::max(0.0, frame.h - b.top - b.bottom);
        return {SRectD{frame.x, frame.y, frame.w, b.top}, SRectD{frame.x, frame.y + frame.h - b.bottom, frame.w, b.bottom},
                SRectD{frame.x, frame.y + b.top, b.left, midH}, SRectD{frame.x + frame.w - b.right, frame.y + b.top, b.right, midH}};
    }

    struct SPixelRect {
        int  x = 0, y = 0, w = 0, h = 0;
        bool operator==(const SPixelRect&) const = default;
    };

    // Daños lógicos de un Frame → rectángulos en píxeles del búfer, pieza a pieza, redondeados hacia
    // fuera. Sin daños (o el primer Frame) se devuelve el búfer entero.
    inline std::vector<SPixelRect> damageInBuffer(const SFrame& f, bool everything) {
        std::vector<SPixelRect> out;
        if (everything || f.damage.empty()) {
            out.push_back({0, 0, static_cast<int>(f.width), static_cast<int>(f.height)});
            return out;
        }
        for (const auto& d : f.damage) {
            for (const auto& p : f.parts) {
                if (p.w == 0 || p.h == 0 || p.logical.w <= 0 || p.logical.h <= 0)
                    continue;
                const double x1 = std::max(d.x, p.logical.x), y1 = std::max(d.y, p.logical.y);
                const double x2 = std::min(d.x + d.w, p.logical.x + p.logical.w), y2 = std::min(d.y + d.h, p.logical.y + p.logical.h);
                if (x2 <= x1 || y2 <= y1)
                    continue;
                const double sx = p.w / p.logical.w, sy = p.h / p.logical.h;
                const int    px1 = std::clamp(static_cast<int>(std::floor((x1 - p.logical.x) * sx)), 0, static_cast<int>(p.w));
                const int    py1 = std::clamp(static_cast<int>(std::floor((y1 - p.logical.y) * sy)), 0, static_cast<int>(p.h));
                const int    px2 = std::clamp(static_cast<int>(std::ceil((x2 - p.logical.x) * sx)), 0, static_cast<int>(p.w));
                const int    py2 = std::clamp(static_cast<int>(std::ceil((y2 - p.logical.y) * sy)), 0, static_cast<int>(p.h));
                if (px2 > px1 && py2 > py1)
                    out.push_back({static_cast<int>(p.x) + px1, static_cast<int>(p.y) + py1, px2 - px1, py2 - py1});
            }
        }
        return out;
    }

    // Un trozo de la sombra: de dónde sale en la imagen (unidades lógicas de la imagen) y dónde se
    // dibuja (coordenadas globales lógicas).
    struct SShadowQuad {
        SRectD src, dst;
    };

    // Sombra de nueve trozos como KWin (src/scene/shadowitem.cpp, generateShadowQuads): las esquinas a
    // su tamaño, los lados estirados con la franja del rectángulo interior, y si la ventana es tan
    // pequeña que las esquinas se solapan, se recortan a medias y el lado entre ellas no se dibuja.
    // `frame` es el marco completo de la decoración; el centro no se dibuja (Breeze lo deja vacío).
    inline std::vector<SShadowQuad> shadowQuads(const SRectD& frame, const SShadow& s) {
        std::vector<SShadowQuad> out;
        if (s.width == 0 || s.height == 0 || s.dpr <= 0)
            return out;
        const double W = s.width / s.dpr, H = s.height / s.dpr;
        const auto&  in = s.inner;
        // Tamaños de los elementos (Shadow::init de KWin)
        const double topH = in.y, bottomH = H - (in.y + in.h), leftW = in.x, rightW = W - (in.x + in.w);
        const SRectD outer{frame.x - s.padding.left, frame.y - s.padding.top, frame.w + s.padding.left + s.padding.right,
                           frame.h + s.padding.top + s.padding.bottom};
        // Esquinas: [x1, y1, x2, y2]
        double tl[4] = {outer.x, outer.y, outer.x + leftW, outer.y + topH};
        double tr[4] = {outer.x + outer.w - rightW, outer.y, outer.x + outer.w, outer.y + topH};
        double br[4] = {outer.x + outer.w - rightW, outer.y + outer.h - bottomH, outer.x + outer.w, outer.y + outer.h};
        double bl[4] = {outer.x, outer.y + outer.h - bottomH, outer.x + leftW, outer.y + outer.h};
        bool   drawTop = true, drawRight = true, drawBottom = true, drawLeft = true;
        if (tl[2] >= tr[0]) {
            drawTop          = false;
            const double off = std::abs(tl[2] - tr[0]) / 2;
            tl[2] -= std::floor(off);
            tr[0] += std::ceil(off);
        }
        if (tr[3] >= br[1]) {
            drawRight        = false;
            const double off = std::abs(tr[3] - br[1]) / 2;
            tr[3] -= std::floor(off);
            br[1] += std::ceil(off);
        }
        if (bl[2] >= br[0]) {
            drawBottom       = false;
            const double off = std::abs(bl[2] - br[0]) / 2;
            bl[2] -= std::floor(off);
            br[0] += std::ceil(off);
        }
        if (tl[3] >= bl[1]) {
            drawLeft         = false;
            const double off = std::abs(tl[3] - bl[1]) / 2;
            tl[3] -= std::floor(off);
            bl[1] += std::ceil(off);
        }
        auto rect = [](const double r[4]) { return SRectD{r[0], r[1], std::max(0.0, r[2] - r[0]), std::max(0.0, r[3] - r[1])}; };
        // Esquinas: la parte de la imagen de su esquina, del tamaño que haya quedado
        const SRectD TL = rect(tl), TR = rect(tr), BR = rect(br), BL = rect(bl);
        out.push_back({{0, 0, TL.w, TL.h}, TL});
        out.push_back({{W - TR.w, 0, TR.w, TR.h}, TR});
        out.push_back({{W - BR.w, H - BR.h, BR.w, BR.h}, BR});
        out.push_back({{0, H - BL.h, BL.w, BL.h}, BL});
        if (drawTop)
            out.push_back({{in.x, 0, in.w, topH}, {tl[2], outer.y, tr[0] - tl[2], topH}});
        if (drawRight)
            out.push_back({{W - rightW, in.y, rightW, in.h}, {outer.x + outer.w - rightW, tr[3], rightW, br[1] - tr[3]}});
        if (drawBottom)
            out.push_back({{in.x, H - bottomH, in.w, bottomH}, {bl[2], outer.y + outer.h - bottomH, br[0] - bl[2], bottomH}});
        if (drawLeft)
            out.push_back({{0, in.y, leftW, in.h}, {outer.x, tl[3], leftW, bl[1] - tl[3]}});
        std::erase_if(out, [](const SShadowQuad& q) { return q.dst.w <= 0 || q.dst.h <= 0 || q.src.w <= 0 || q.src.h <= 0; });
        return out;
    }

    // Rueda sobre la barra (kwinrc [MouseBindings] CommandTitlebarWheel). Lo que Hyprland no tiene
    // (enrollar, encima/debajo, opacidad) no hace nada.
    enum class eWheelAction {
        NOTHING,
        RAISE,
        LOWER,
        MAXIMIZE,
        RESTORE,
        PREVIOUS_DESKTOP,
        NEXT_DESKTOP,
    };

    inline eWheelAction wheelAction(const std::string& command, double angleDeltaY) {
        const bool up = angleDeltaY > 0;
        if (angleDeltaY == 0)
            return eWheelAction::NOTHING;
        if (command == "Raise/Lower")
            return up ? eWheelAction::RAISE : eWheelAction::LOWER;
        if (command == "Maximize/Restore")
            return up ? eWheelAction::MAXIMIZE : eWheelAction::RESTORE;
        if (command == "Previous/Next Desktop")
            return up ? eWheelAction::PREVIOUS_DESKTOP : eWheelAction::NEXT_DESKTOP;
        return eWheelAction::NOTHING;
    }

    // Botones de Request 2 (alternar maximizado), como DecoratedWindowImpl de KWin: izquierdo =
    // ambos ejes, central = vertical, derecho = horizontal.
    enum class eMaximizeAxis {
        BOTH,
        VERTICAL,
        HORIZONTAL,
    };

    inline eMaximizeAxis maximizeAxis(uint32_t buttons) {
        if (buttons & 4)
            return eMaximizeAxis::VERTICAL;
        if (buttons & 2)
            return eMaximizeAxis::HORIZONTAL;
        return eMaximizeAxis::BOTH;
    }

    // Colores de los tooltips del esquema de KDE ([Colors:Tooltip] de kdeglobals), ARGB.
    struct STooltipColors {
        uint32_t background = 0xff292c30, foreground = 0xfffcfcfc;
    };

    inline std::optional<uint32_t> parseKdeColor(const std::string& value) {
        int  c[4] = {0, 0, 0, 255};
        int  n    = 0;
        auto s    = std::stringstream(value);
        for (std::string part; n < 4 && std::getline(s, part, ',');) {
            try {
                c[n++] = std::clamp(std::stoi(part), 0, 255);
            } catch (...) { return std::nullopt; }
        }
        if (n < 3)
            return std::nullopt;
        return static_cast<uint32_t>(c[3]) << 24 | static_cast<uint32_t>(c[0]) << 16 | static_cast<uint32_t>(c[1]) << 8 | static_cast<uint32_t>(c[2]);
    }

    inline STooltipColors tooltipColors(const std::string& kdeglobals) {
        STooltipColors     out;
        std::istringstream in(kdeglobals);
        bool               inGroup = false;
        for (std::string line; std::getline(in, line);) {
            if (!line.empty() && line.back() == '\r')
                line.pop_back();
            if (line.starts_with('[')) {
                inGroup = line == "[Colors:Tooltip]";
                continue;
            }
            if (!inGroup)
                continue;
            const auto eq = line.find('=');
            if (eq == std::string::npos)
                continue;
            const auto key = line.substr(0, eq);
            if (auto c = parseKdeColor(line.substr(eq + 1))) {
                if (key == "BackgroundNormal")
                    out.background = *c;
                else if (key == "ForegroundNormal")
                    out.foreground = *c;
            }
        }
        return out;
    }

} // namespace BwmDeco
