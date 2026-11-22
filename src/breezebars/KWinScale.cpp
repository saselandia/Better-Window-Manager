// SPDX-FileCopyrightText: 2026 BWM contributors
// SPDX-License-Identifier: GPL-2.0-or-later
#include <hyprland/src/desktop/view/Window.hpp>
#include <hyprland/src/desktop/Workspace.hpp>
#include <hyprland/src/config/ConfigValue.hpp>
#include <hyprland/src/event/EventBus.hpp>
#include <hyprland/src/managers/fullscreen/FullscreenController.hpp>
#include <hyprland/src/render/Renderer.hpp>
#include <hyprland/src/state/MonitorState.hpp>
#include "globals.hpp"
#include "KWinScale.hpp"
#include <algorithm>
#include <cmath>
#include <format>
#include <vector>
#include <chrono>
extern "C" {
#include <lua.h>
#include <lauxlib.h>
}

namespace {
using Desktop::View::WINDOW_ALPHA_FADE;
struct Opening {
    PHLWINDOWREF window;
    pid_t pid;
    Vector2D position, size;
    PHLWORKSPACEREF workspace;
    PHLMONITORREF monitor;
};
std::vector<Opening> openings;
CHyprSignalListener opened, closed, preRender, preReload;
SP<SHyprCtlCommand> command;
bool enabled=false;
bool tracing=false;
double inScale=.8;
uint64_t starts=0, observedFrames=0, resetOnClose=0, cancelled=0;
struct Trace { double ms,alpha,active,full,layout,workspace,moveFrom,width,height,surfaceAlpha,overall,dim,tint;std::string stage; };
std::vector<Trace> traces;
void trace(PHLWINDOW w,std::string stage) {
    if(!tracing || traces.size()>=512)return;
    traces.push_back({std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now().time_since_epoch()).count(),
        w->alphaValue(WINDOW_ALPHA_FADE),w->alphaValue(Desktop::View::WINDOW_ALPHA_ACTIVE),
        w->alphaValue(Desktop::View::WINDOW_ALPHA_FULLSCREEN),w->alphaValue(Desktop::View::WINDOW_ALPHA_LAYOUT),
        w->m_workspace->m_alpha->value(),w->alphaValue(Desktop::View::WINDOW_ALPHA_MOVE_FROM_WORKSPACE),
        w->sizeAnimation()->value().x,w->sizeAnimation()->value().y,w->wlSurface()->m_alphaModifier,w->wlSurface()->m_overallOpacity,
        w->m_dimPercent->value(),w->m_notRespondingTint->value(),std::move(stage)});
}

bool active() {
    static auto animations=CConfigValue<Config::INTEGER>("animations:enabled");
    return enabled && *animations && g_pGlobalState && g_pGlobalState->config.enabled->value();
}
bool eligible(PHLWINDOW w) {
    if(!active() || !Desktop::View::validMapped(w) || !w->m_monitor || !w->m_workspace || !w->m_workspace->isVisible() || w->m_workspace->m_isSpecialWorkspace ||
       w->m_X11DoesntWantBorders || !w->m_ruleApplicator || w->m_ruleApplicator->noAnim().valueOrDefault() ||
       Fullscreen::controller()->isFullscreen(w))return false;
    // Explicit per-window animation rules always belong to the user. This
    // adapter only owns the standard Breeze scale/fade leaves, not other styles.
    if(w->m_ruleApplicator->animationStyle().hasValue())return false;
    const auto &alpha=w->alpha(WINDOW_ALPHA_FADE);
    return alpha && alpha->enabled() && alpha->getBezierName()=="kwin_out_cubic";
}
bool stillOwns(const Opening &s, PHLWINDOW w) {
    return w && w->getPID()==s.pid && eligible(w) &&
        s.workspace.lock()==w->m_workspace && s.monitor.lock()==w->m_monitor.lock() &&
        w->positionAnimation()->goal()==s.position && w->sizeAnimation()->goal()==s.size;
}
void begin(PHLWINDOW w) {
    if(!eligible(w))return;
    const auto &size=w->sizeAnimation();
    if(!size || !size->enabled() || size->getBezierName()!="kwin_out_cubic" ||
       size->getStyle()!=std::format("popin {}%",int(std::lround(inScale*100))))return;
    std::erase_if(openings,[&](const auto &s){return s.window.expired() || s.window.lock()==w;});
    if(openings.size()>=256)return;
    openings.push_back({w,w->getPID(),w->positionAnimation()->goal(),w->sizeAnimation()->goal(),w->m_workspace,w->m_monitor});
    trace(w,"open");
    ++starts;
}
void render(PHLMONITOR monitor) {
    if(!active()){openings.clear();return;}
    std::erase_if(openings,[&](const Opening &s){
        auto w=s.window.lock();
        if(!stillOwns(s,w)){++cancelled;return true;}
        if(w->m_monitor.lock()!=monitor)return false;
        auto &alpha=w->alpha(WINDOW_ALPHA_FADE);
        trace(w,"render");
        ++observedFrames;
        return !alpha->isBeingAnimated() && alpha->value()>=1;
    });
}
void close(PHLWINDOW w) {
    auto it=std::ranges::find_if(openings,[&](const auto &s){return s.window.lock()==w && w->getPID()==s.pid;});
    if(it==openings.end())return;
    if(stillOwns(*it,w)) {
        // window.close is emitted before makeSnapshotFB and CWindowFadeout::create.
        // KWin ScaleEffect cancels its entry animation and closes from full scale
        // and opacity. Restore only these values, synchronously before the snapshot.
        w->positionAnimation()->value()=it->position;
        w->sizeAnimation()->value()=it->size;
        w->alpha(WINDOW_ALPHA_FADE)->value()=1.f;
        // A close before the first animation tick can still carry mapWindow's
        // initial dim value. Respect custom dim timelines and nonzero dim goals.
        if(!w->m_dimPercent->enabled() && w->m_dimPercent->goal()==0.f)
            w->m_dimPercent->value()=0.f;
        trace(w,"close");
        ++resetOnClose;
    } else ++cancelled;
    openings.erase(it);
}
int configure(lua_State *L) {
    luaL_checktype(L,1,LUA_TTABLE);
    lua_getfield(L,1,"enabled");enabled=lua_toboolean(L,-1);lua_pop(L,1);
    lua_getfield(L,1,"in_scale");const double scale=lua_isnumber(L,-1)?lua_tonumber(L,-1):.8;lua_pop(L,1);
    inScale=std::isfinite(scale)?std::clamp(scale,.1,1.):.8;
    lua_getfield(L,1,"trace");tracing=lua_toboolean(L,-1);lua_pop(L,1);
    traces.clear();
    if(tracing)traces.reserve(512);
    openings.clear();
    return 0;
}
std::string status(eHyprCtlOutputFormat,std::string) {
    auto result=std::format(R"({{"version":1,"enabled":{},"tracked":{},"starts":{},"observedFrames":{},"resetOnClose":{},"cancelled":{}}})",
                       active(),openings.size(),starts,observedFrames,resetOnClose,cancelled);
    result.pop_back();result+=",\"trace\":[";
    for(size_t i=0;i<traces.size();++i){const auto &t=traces[i];if(i)result+=",";
        result+=std::format(R"({{"ms":{},"stage":"{}","alpha":{},"active":{},"full":{},"layout":{},"workspace":{},"moveFrom":{},"size":[{},{}],"surfaceAlpha":{},"overall":{},"dim":{},"tint":{}}})",
                           t.ms,t.stage,t.alpha,t.active,t.full,t.layout,t.workspace,t.moveFrom,t.width,t.height,t.surfaceAlpha,t.overall,t.dim,t.tint);}
    return result+"]}";
}
}

void initKWinScale() {
    HyprlandAPI::addLuaFunction(PHANDLE,"breezebars","scale_config",configure);
    command=HyprlandAPI::registerHyprCtlCommand(PHANDLE,SHyprCtlCommand{.name="breezebars-scale",.exact=true,.fn=status});
    opened=Event::bus()->m_events.window.openLate.listen([](PHLWINDOW w){begin(w);});
    closed=Event::bus()->m_events.window.close.listen([](PHLWINDOW w){close(w);});
    preRender=Event::bus()->m_events.render.pre.listen([](PHLMONITOR m){render(m);});
    preReload=Event::bus()->m_events.config.preReload.listen([]{openings.clear();enabled=false;});
}
void finishKWinScale() {
    enabled=false;opened.reset();closed.reset();preRender.reset();preReload.reset();openings.clear();traces.clear();
    if(command){HyprlandAPI::unregisterHyprCtlCommand(PHANDLE,command);command.reset();}
}
