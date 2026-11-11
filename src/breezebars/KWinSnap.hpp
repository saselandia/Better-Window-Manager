#pragma once

#include "globals.hpp"
#include "SnapGeometry.hpp"
#include "CSDDetect.hpp"
#include <hyprland/src/managers/eventLoop/EventLoopManager.hpp>
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
#include <cstdlib>

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
// Release consumes the displayed target, including its monitor and modifier-selected tile.
inline std::optional<SSnapTarget> g_kwinDisplayedTarget;
inline PHLWINDOWREF g_kwinPreviewWindow;
inline void clearKWinTarget() {g_kwinDisplayedTarget.reset();g_kwinPreviewWindow.reset();}

// Configured by kwin.lua; users may override through snap_config in their last-loaded Lua.
inline BwmSnap::Zones g_kwinSnapZones;
struct SCustomTile { std::string description; int workspace; BwmSnap::Rect rect; double padding; };
inline std::vector<SCustomTile> g_kwinCustomTiles;
inline double g_kwinCornerRatio=.25;
inline bool g_kwinQuickTile=true,g_kwinMaximize=true;
struct SFrameBorders {double left=0,top=0,right=0,bottom=0;};
inline SFrameBorders snapBorders(PHLWINDOW w) {
    SFrameBorders out;
    for(auto& b:g_pGlobalState->bars)if(b&&b->getOwner()==w&&!b->m_hidden) {
        auto e=b->getPositioningInfo().desiredExtents;
        return {e.topLeft.x,e.topLeft.y,e.bottomRight.x,e.bottomRight.y};
    }
    return out;
}
inline BwmSnap::Rect snapFrame(PHLWINDOW w) {
    auto r=w->layoutTarget()->position();auto b=snapBorders(w);
    return {r.x-b.left,r.y-b.top,r.w+b.left+b.right,r.h+b.top+b.bottom};
}
inline bool fitsSnap(PHLWINDOW w,BwmSnap::Rect frame) {
    auto b=snapBorders(w);double width=frame.w-b.left-b.right,height=frame.h-b.top-b.bottom;
    auto min=w->minSize(),max=w->maxSize();
    return width>0&&height>0&&(!min||(width>=min->x&&height>=min->y))&&(!max||(width<=max->x&&height<=max->y));
}
inline void setSnapFrame(PHLWINDOW w,BwmSnap::Rect frame) {
    auto b=snapBorders(w);CBox content{frame.x+b.left,frame.y+b.top,frame.w-b.left-b.right,frame.h-b.top-b.bottom};
    g_pHyprRenderer->damageWindow(w,true);w->layoutTarget()->setPositionGlobal(content);
    w->layoutTarget()->warpPositionSize();w->updateWindowDecos();g_pHyprRenderer->damageWindow(w,true);
}
inline bool snapParticipant(PHLWINDOW w,PHLWINDOW moving) {
    return Desktop::View::validMapped(w)&&w!=moving&&w->m_workspace==moving->m_workspace&&w->m_isFloating&&
           !w->isHidden()&&!w->isX11OverrideRedirect()&&!Fullscreen::controller()->isFullscreen(w);
}
inline void applyKWinMagnet(PHLWINDOW w,Vector2D pointer) {
    if(!g_pGlobalState->config.enabled->value()||!Desktop::View::validMapped(w)||!w->m_isFloating)return;
    auto monitor=State::monitorState()->query().vec(pointer).run();if(!monitor)return;
    auto a=monitor->m_reservedArea.apply(CBox{monitor->m_position,monitor->m_size});
    std::vector<BwmSnap::Rect> others;
    for(auto& other:Desktop::windowState()->windows())if(snapParticipant(other,w))others.push_back(snapFrame(other));
    auto frame=snapFrame(w);auto dest=BwmSnap::magnet(frame,{a.x,a.y,a.w,a.h},others,g_kwinSnapZones);
    if(std::abs(frame.x-dest.x)>.01||std::abs(frame.y-dest.y)>.01)setSnapFrame(w,dest);
}
inline PHLWINDOWREF g_kwinResizeWindow;
inline BwmSnap::Rect g_kwinResizeBefore;
inline void syncAdjacentResize(bool final=false) {
    const auto& drag=g_layoutManager->dragController();
    if(!g_pGlobalState->config.enabled->value()){g_kwinResizeWindow.reset();return;}
    if(!final&&(!drag||drag->mode()!=MBIND_RESIZE||!drag->target())){g_kwinResizeWindow.reset();return;}
    auto w=final?g_kwinResizeWindow.lock():drag->target()->window();if(!Desktop::View::validMapped(w))return;
    if(!w->m_ruleApplicator||!w->m_ruleApplicator->m_tagKeeper.isTagged("snapped")){g_kwinResizeWindow.reset();return;}
    auto after=snapFrame(w);
    if(g_kwinResizeWindow.lock()!=w){g_kwinResizeWindow=w;g_kwinResizeBefore=after;return;}
    auto before=g_kwinResizeBefore;
    if(std::abs(before.w-after.w)<.01&&std::abs(before.h-after.h)<.01)return;
    std::vector<std::pair<PHLWINDOW,BwmSnap::Rect>> changes;
    for(auto& other:Desktop::windowState()->windows())if(snapParticipant(other,w)&&other->m_ruleApplicator&&other->m_ruleApplicator->m_tagKeeper.isTagged("snapped")) {
        auto neighbour=snapFrame(other);
        auto next=BwmSnap::adjacent(before,after,neighbour,8);
        if(!next) {
            bool horizontal=BwmSnap::overlaps(before.y,before.bottom(),neighbour.y,neighbour.bottom())&&
                ((std::abs(before.right()-neighbour.x)<=8&&std::abs(after.right()-before.right())>.1)||
                 (std::abs(before.x-neighbour.right())<=8&&std::abs(after.x-before.x)>.1));
            bool vertical=BwmSnap::overlaps(before.x,before.right(),neighbour.x,neighbour.right())&&
                ((std::abs(before.bottom()-neighbour.y)<=8&&std::abs(after.bottom()-before.bottom())>.1)||
                 (std::abs(before.y-neighbour.bottom())<=8&&std::abs(after.y-before.y)>.1));
            if(horizontal||vertical){setSnapFrame(w,before);return;}
        }
        if(next) {
            if(!fitsSnap(other,*next)){setSnapFrame(w,before);return;}
            changes.emplace_back(other,*next);
        }
    }
    for(auto& [other,frame]:changes)setSnapFrame(other,frame);
    g_kwinResizeBefore=after;
}
inline UP<SEventLoopDoLaterLock> g_kwinAfterInput;
inline void queueKWinAfterInput(PHLWINDOW moving) {
    if(g_kwinAfterInput)return;
    PHLWINDOWREF weak=moving;
    g_kwinAfterInput=g_pEventLoopManager->doLaterLock([weak] {
        g_kwinAfterInput.reset();
        if(!g_pGlobalState||!g_pGlobalState->config.enabled->value())return;
        if(auto w=weak.lock();Desktop::View::validMapped(w)) {
            bool dragging=false;
            for(auto& b:g_pGlobalState->bars)if(b&&b->getOwner()==w&&b->isDragging())dragging=true;
            const auto& controller=g_layoutManager->dragController();
            if(controller&&controller->mode()==MBIND_MOVE&&controller->target()&&controller->target()->window()==w)dragging=true;
            if(dragging)applyKWinMagnet(w,g_pInputManager->getMouseCoordsInternal());
        }
        syncAdjacentResize();
    });
}
inline std::optional<SSnapTarget> getSnapTarget(const Vector2D& mousePos) {
    auto monitor=State::monitorState()->query().vec(mousePos).run();
    if(!monitor)return {};
    auto usable=monitor->m_reservedArea.apply(CBox{monitor->m_position,monitor->m_size});
    BwmSnap::Rect area{usable.x,usable.y,usable.w,usable.h};
    // Shift-drag chooses a leaf from the actual KWin tile tree.
    if(g_pInputManager->getModsFromAllKBs() & 1) {
        auto workspace=monitor->m_activeWorkspace;
        for(size_t i=0;i<g_kwinCustomTiles.size();++i) {
            auto& tile=g_kwinCustomTiles[i];
            if(tile.description!=monitor->m_description||!workspace||tile.workspace!=workspace->m_id)continue;
            auto r=BwmSnap::padded(tile.rect,area,0);
            if(mousePos.x>=r.x&&mousePos.x<=r.right()&&mousePos.y>=r.y&&mousePos.y<=r.bottom()) {
                auto f=BwmSnap::padded(tile.rect,area,tile.padding);
                return SSnapTarget{"custom",CBox{f.x,f.y,f.w,f.h},monitor};
            }
        }
        return {};
    }
    if(!g_kwinQuickTile&&!g_kwinMaximize)return {};
    auto target=BwmSnap::edge({mousePos.x,mousePos.y},{monitor->m_position.x,monitor->m_position.y,monitor->m_size.x,monitor->m_size.y},area,10,g_kwinCornerRatio);
    if(!target||(target->direction=="maximize"?!g_kwinMaximize:!g_kwinQuickTile))return {};
    auto r=target->frame;
    return SSnapTarget{target->direction,CBox{r.x,r.y,r.w,r.h},monitor};
}
inline std::string snapQuote(const std::string& text) {
    std::string out="'";for(char c:text)out+=c=='\''?"'\\''":std::string(1,c);return out+"'";
}
inline uint64_t g_kwinOutlineSequence=0;
inline void outline(const std::optional<SSnapTarget>& target) {
    auto serial=++g_kwinOutlineSequence;
    if(!target){Config::Supplementary::executor()->spawn("qs -c ii ipc call plasmaOutline hide "+std::to_string(serial));return;}
    auto b=target->box;
    auto monitor=target->monitor;
    auto a=monitor->m_reservedArea.apply(CBox{monitor->m_position,monitor->m_size});
    std::string payload=std::format("{{\"sequence\":{},\"x\":{},\"y\":{},\"width\":{},\"height\":{},\"area\":[{},{},{},{}]}}",serial,b.x,b.y,b.w,b.h,a.x,a.y,a.w,a.h);
    Config::Supplementary::executor()->spawn("qs -c ii ipc call plasmaOutline display "+snapQuote(payload));
}

inline void hideSnapPreview() {
    if (g_bSnapPreviewActive) {
        g_bSnapPreviewActive = false;
        outline(std::nullopt);
        CBox dmgBox          = g_snapPreviewBox;
        dmgBox.expand(16);
        g_pHyprRenderer->damageBox(dmgBox);
        if (auto pOld = g_snapPreviewMonitor.lock())
            g_pHyprRenderer->damageMonitor(pOld);
    }
}

inline void updateSnapPreview(const Vector2D& mousePos,PHLWINDOW window) {
    if (!g_pGlobalState || !g_pGlobalState->config.enabled->value()) {
        clearKWinTarget();hideSnapPreview();
        return;
    }

    auto target = getSnapTarget(mousePos);
    if(target&&window&&!fitsSnap(window,{target->box.x,target->box.y,target->box.w,target->box.h}))target.reset();
    g_kwinDisplayedTarget=target;g_kwinPreviewWindow=window;
    if (target.has_value() && target->monitor) {
        auto pOldMon   = g_snapPreviewMonitor.lock();
        CBox oldBox    = g_snapPreviewBox;
        bool wasActive = g_bSnapPreviewActive;

        g_bSnapPreviewActive = true;
        g_snapPreviewBox     = target->box;
        g_snapPreviewMonitor = target->monitor;
        if (!wasActive || !(oldBox == target->box)) outline(target);

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

    auto target = g_kwinPreviewWindow.lock()==pWindow ? g_kwinDisplayedTarget : std::nullopt;
    if (target.has_value() && !target->direction.empty()) {
        recordPreSnapSize(pWindow);
        std::string addr = std::format("0x{:x}", (uintptr_t)pWindow.get());
        // La ventana puede pertenecer ya al monitor vecino por su centro. El destino es el
        // monitor de la previsualización, no el que Python encuentre unos milisegundos después.
        const char* home = std::getenv("HOME");
        if (!home) {
            hideSnapPreview();
            return;
        }
        std::string cmd = snapQuote(std::string(home) + "/.config/hypr/skins/plasma/scripts/kwin-tiles.py") + " apply "
            + snapQuote(addr) + " --monitor " + snapQuote("desc:" + target->monitor->m_description)
            + " --direction " + target->direction + " --frame "
            + snapQuote(std::format("{},{},{},{}",target->box.x,target->box.y,target->box.w,target->box.h));
        if (pWindow->getPID() > 0)
            cmd += " --pid " + std::to_string(pWindow->getPID());
        Config::Supplementary::executor()->spawn(cmd);
    }
    clearKWinTarget();hideSnapPreview();
}

// The outline is painted by KSvg in the Breeze shell; no hard-coded GL preview remains.
inline void renderSnapPreviewOverlay(eRenderStage) {}
