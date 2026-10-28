#pragma once

#include "globals.hpp"
#include "BarPassElement.hpp"
#include <hyprland/src/desktop/state/WindowState.hpp>
#include <hyprland/src/desktop/state/ViewState.hpp>
#include <hyprland/src/desktop/state/ViewHitTester.hpp>
#include <hyprland/src/state/MonitorState.hpp>
#include <hyprland/src/managers/fullscreen/FullscreenController.hpp>
#include <hyprland/src/Compositor.hpp>
#include <hyprland/src/render/Renderer.hpp>
#include <hyprland/src/render/OpenGL.hpp>
#include <hyprland/src/managers/input/InputManager.hpp>
#include <hyprland/src/managers/KeybindManager.hpp>
#include <hyprland/src/layout/target/Target.hpp>
#include <hyprland/src/layout/LayoutManager.hpp>
#include <hyprland/src/config/supplementary/executor/Executor.hpp>
#include <unordered_map>
#include <fstream>
#include <string>
#include <cmath>
#include <algorithm>
#include <optional>

// In-memory store of pre-snap floating window sizes
#define g_preSnapSizes g_plasmaPreSnapSizes
inline std::unordered_map<uintptr_t, Vector2D> g_plasmaPreSnapSizes;

inline void savePresnapToFile(const std::string& addr, int w, int h) {
    try {
        std::unordered_map<std::string, std::pair<int, int>> data;
        std::ifstream in("/tmp/hypr_presnap_sizes.txt");
        if (in.is_open()) {
            std::string line;
            while (std::getline(in, line)) {
                auto colon = line.find(':');
                auto comma = line.find(',');
                if (colon != std::string::npos && comma != std::string::npos) {
                    std::string k = line.substr(0, colon);
                    int valW = std::stoi(line.substr(colon + 1, comma - colon - 1));
                    int valH = std::stoi(line.substr(comma + 1));
                    data[k] = {valW, valH};
                }
            }
            in.close();
        }
        data[addr] = {w, h};
        std::ofstream out("/tmp/hypr_presnap_sizes.txt");
        if (out.is_open()) {
            for (const auto& [k, v] : data) {
                out << k << ":" << v.first << "," << v.second << "\n";
            }
            out.close();
        }
    } catch (...) {}
}

inline std::optional<Vector2D> readPresnapFromFile(const std::string& addr) {
    try {
        std::ifstream in("/tmp/hypr_presnap_sizes.txt");
        if (in.is_open()) {
            std::string line;
            while (std::getline(in, line)) {
                if (line.starts_with(addr + ":")) {
                    auto colon = line.find(':');
                    auto comma = line.find(',');
                    if (colon != std::string::npos && comma != std::string::npos) {
                        int valW = std::stoi(line.substr(colon + 1, comma - colon - 1));
                        int valH = std::stoi(line.substr(comma + 1));
                        if (valW > 100 && valH > 100)
                            return Vector2D{(double)valW, (double)valH};
                    }
                }
            }
            in.close();
        }
    } catch (...) {}

    // Fallback: check /tmp/hypr_presnap_sizes.json
    try {
        std::ifstream jin("/tmp/hypr_presnap_sizes.json");
        if (jin.is_open()) {
            std::string content((std::istreambuf_iterator<char>(jin)), std::istreambuf_iterator<char>());
            auto pos = content.find("\"" + addr + "\"");
            if (pos != std::string::npos) {
                auto bracket = content.find('[', pos);
                auto comma   = content.find(',', bracket);
                auto closeB  = content.find(']', comma);
                if (bracket != std::string::npos && comma != std::string::npos && closeB != std::string::npos) {
                    int w = std::stoi(content.substr(bracket + 1, comma - bracket - 1));
                    int h = std::stoi(content.substr(comma + 1, closeB - comma - 1));
                    if (w > 100 && h > 100)
                        return Vector2D{(double)w, (double)h};
                }
            }
            jin.close();
        }
    } catch (...) {}

    return std::nullopt;
}

inline void recordPreSnapSize(PHLWINDOW pWindow) {
    if (!Desktop::View::validMapped(pWindow))
        return;

    bool isSnapped = pWindow->m_ruleApplicator && pWindow->m_ruleApplicator->m_tagKeeper.isTagged("snapped");
    if (!isSnapped) {
        Vector2D sz = pWindow->layoutTarget()->position().size();
        if (sz.x > 100 && sz.y > 100) {
            g_preSnapSizes[(uintptr_t)pWindow.get()] = sz;
            std::string addr = std::format("0x{:x}", (uintptr_t)pWindow.get());
            savePresnapToFile(addr, (int)sz.x, (int)sz.y);
        }
    }
}

inline std::optional<Vector2D> getAndConsumePreSnapSize(PHLWINDOW pWindow) {
    if (!pWindow)
        return std::nullopt;

    auto it = g_preSnapSizes.find((uintptr_t)pWindow.get());
    if (it != g_preSnapSizes.end()) {
        Vector2D sz = it->second;
        g_preSnapSizes.erase(it);
        if (sz.x > 100 && sz.y > 100)
            return sz;
    }

    std::string addr = std::format("0x{:x}", (uintptr_t)pWindow.get());
    return readPresnapFromFile(addr);
}

// Snap preview overlay state
#define g_bSnapPreviewActive g_bPlasmaSnapPreviewActive
#define g_snapPreviewBox     g_plasmaSnapPreviewBox
#define g_snapPreviewMonitor g_plasmaSnapPreviewMonitor
inline bool          g_bPlasmaSnapPreviewActive = false;
inline CBox          g_plasmaSnapPreviewBox;
inline PHLMONITORREF g_plasmaSnapPreviewMonitor;

struct SSnapTarget {
    std::string direction;
    CBox box;
    PHLMONITOR monitor;
};

inline std::optional<SSnapTarget> getSnapTarget(const Vector2D& mousePos) {
    auto pMonitor = State::monitorState()->query().vec(mousePos).run();
    if (!pMonitor)
        pMonitor = State::monitorState()->query().vec(g_pInputManager->getMouseCoordsInternal()).run();
    if (!pMonitor)
        return std::nullopt;

    const int EDGE_THRESHOLD    = 40;
    const int CORNER_THRESHOLD  = 150;
    const int BOTTOM_BAR_HEIGHT = 44;

    float relX = mousePos.x - pMonitor->m_position.x;
    float relY = mousePos.y - pMonitor->m_position.y;
    float monW = pMonitor->m_size.x;
    float monH = pMonitor->m_size.y;

    bool atTop    = (relY <= EDGE_THRESHOLD);
    bool atBottom = (relY >= monH - BOTTOM_BAR_HEIGHT - EDGE_THRESHOLD);
    bool atLeft   = (relX <= EDGE_THRESHOLD);
    bool atRight  = (relX >= monW - EDGE_THRESHOLD);

    if (!atTop && !atBottom && !atLeft && !atRight)
        return std::nullopt;

    double usableX = pMonitor->m_position.x;
    double usableY = pMonitor->m_position.y;
    double usableW = monW;
    double usableH = monH - BOTTOM_BAR_HEIGHT;

    double halfW = std::floor(usableW / 2.0);
    double halfH = std::floor(usableH / 2.0);
    double remW  = usableW - halfW;
    double remH  = usableH - halfH;

    std::string dir = "";
    CBox box;

    if (atTop) {
        if (atLeft || relX <= CORNER_THRESHOLD) {
            dir = "top-left";
            box = CBox{usableX, usableY, halfW, halfH};
        } else if (atRight || relX >= monW - CORNER_THRESHOLD) {
            dir = "top-right";
            box = CBox{usableX + halfW, usableY, remW, halfH};
        } else {
            dir = "top";
            box = CBox{usableX, usableY, usableW, usableH};
        }
    } else if (atBottom) {
        if (atLeft || relX <= CORNER_THRESHOLD) {
            dir = "bottom-left";
            box = CBox{usableX, usableY + halfH, halfW, remH};
        } else if (atRight || relX >= monW - CORNER_THRESHOLD) {
            dir = "bottom-right";
            box = CBox{usableX + halfW, usableY + halfH, remW, remH};
        } else {
            dir = "bottom";
            box = CBox{usableX, usableY + halfH, usableW, remH};
        }
    } else if (atLeft) {
        if (relY >= monH - BOTTOM_BAR_HEIGHT - CORNER_THRESHOLD) {
            dir = "bottom-left";
            box = CBox{usableX, usableY + halfH, halfW, remH};
        } else if (relY <= CORNER_THRESHOLD) {
            dir = "top-left";
            box = CBox{usableX, usableY, halfW, halfH};
        } else {
            dir = "left";
            box = CBox{usableX, usableY, halfW, usableH};
        }
    } else if (atRight) {
        if (relY >= monH - BOTTOM_BAR_HEIGHT - CORNER_THRESHOLD) {
            dir = "bottom-right";
            box = CBox{usableX + halfW, usableY + halfH, remW, remH};
        } else if (relY <= CORNER_THRESHOLD) {
            dir = "top-right";
            box = CBox{usableX + halfW, usableY, remW, halfH};
        } else {
            dir = "right";
            box = CBox{usableX + halfW, usableY, remW, usableH};
        }
    }

    if (dir.empty())
        return std::nullopt;

    return SSnapTarget{dir, box, pMonitor};
}

inline void hideSnapPreview() {
    if (g_bSnapPreviewActive) {
        g_bSnapPreviewActive = false;
        CBox dmgBox          = g_snapPreviewBox;
        dmgBox.expand(16);
        g_pHyprRenderer->damageBox(dmgBox);
        if (auto pOld = g_snapPreviewMonitor.lock())
            g_pHyprRenderer->damageMonitor(pOld);
    }
}

inline void updateSnapPreview(const Vector2D& mousePos) {
    if (!g_pGlobalState || !g_pGlobalState->config.enabled->value()) {
        hideSnapPreview();
        return;
    }

    auto target = getSnapTarget(mousePos);
    if (target.has_value() && target->monitor) {
        auto pOldMon   = g_snapPreviewMonitor.lock();
        CBox oldBox    = g_snapPreviewBox;
        bool wasActive = g_bSnapPreviewActive;

        g_bSnapPreviewActive = true;
        g_snapPreviewBox     = target->box;
        g_snapPreviewMonitor = target->monitor;

        if (wasActive && pOldMon && pOldMon != target->monitor) {
            g_pHyprRenderer->damageMonitor(pOldMon);
        } else if (wasActive && !(oldBox == target->box)) {
            CBox dmgOld = oldBox;
            dmgOld.expand(16);
            g_pHyprRenderer->damageBox(dmgOld);
        }

        CBox dmgNew = target->box;
        dmgNew.expand(16);
        g_pHyprRenderer->damageBox(dmgNew);
        g_pHyprRenderer->damageMonitor(target->monitor);
    } else {
        hideSnapPreview();
    }
}

inline void checkAndTriggerEdgeSnap(PHLWINDOW pWindow, const Vector2D& mousePos) {
    if (!Desktop::View::validMapped(pWindow)) {
        hideSnapPreview();
        return;
    }

    if (!g_pGlobalState || !g_pGlobalState->config.enabled->value()) {
        hideSnapPreview();
        return;
    }

    auto target = getSnapTarget(mousePos);
    if (target.has_value() && !target->direction.empty()) {
        recordPreSnapSize(pWindow);
        std::string addr = std::format("0x{:x}", (uintptr_t)pWindow.get());
        std::string cmd  = std::format("/home/sasel/.config/hypr/scripts/quick-tile.py {} {}", target->direction, addr);
        Config::Supplementary::executor()->spawn(cmd);
    }
    hideSnapPreview();
}

inline void renderSnapPreviewOverlay(eRenderStage stage) {
    if (stage != RENDER_LAST_MOMENT || !g_bSnapPreviewActive)
        return;

    if (!g_pGlobalState || !g_pGlobalState->config.enabled->value())
        return;

    auto pMonitor = g_pHyprRenderer->m_renderData.pMonitor.lock();
    if (!pMonitor || pMonitor != g_snapPreviewMonitor.lock())
        return;

    CSnapPreviewPassElement::SSnapData snapData{g_snapPreviewBox};
    g_pHyprRenderer->m_renderPass.add(makeUnique<CSnapPreviewPassElement>(snapData));
}

