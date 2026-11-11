#pragma once
// BWM F7: pure policy/state from KWin v6.7.5 decoration negotiation (no class heuristics).
#include <algorithm>
#include <cstdint>
#include <deque>
#include <optional>
#include <span>
#include <string_view>
namespace BwmCsd {
constexpr uint32_t Client=1, Server=2;
struct Input {
    bool x11=false, overrideRedirect=false, x11Special=false;
    bool x11Ready=true, motifNoBorder=false, gtkFrameExtents=false;
    bool xdg=false, kde=false, kdeExplicit=false;
    uint32_t requested=0, applied=Server;
    bool noBar=false, decorate=true, fullscreen=false;
};
struct Decision { bool bar; bool ready; std::string_view reason; };
inline Decision decide(const Input& i) {
    if(i.noBar)return {false,true,"override: breezebars:no_bar"};
    if(!i.decorate)return {false,true,"override: decorate=false (no frame)"};
    if(i.fullscreen)return {false,true,"fullscreen: no frame"};
    if(i.x11) {
        if(i.overrideRedirect||i.x11Special)return {false,true,"x11: unmanaged/special surface"};
        if(!i.x11Ready)return {false,false,"x11: awaiting properties"};
        if(i.gtkFrameExtents)return {false,true,"x11: _GTK_FRAME_EXTENTS"};
        if(i.motifNoBorder)return {false,true,"x11: _MOTIF_WM_HINTS decorations=0"};
        return {true,true,"x11: WM decoration requested/default"};
    }
    if(!i.xdg&&!i.kde)return {false,true,"wayland: no decoration protocol (CSD)"};
    if(i.applied==0&&i.xdg)return {false,false,"xdg-decoration: awaiting ack/commit"};
    if(i.xdg)return {i.applied==Server,true,i.applied==Client?"xdg-decoration: committed client-side":"xdg-decoration: committed server-side"};
    if(i.applied==0)return {false,true,"kde-server-decoration: None"};
    return {i.applied==Server,true,i.applied==Client?"kde-server-decoration: client-side":"kde-server-decoration: server-side"};
}
inline uint32_t desiredXdg(uint32_t request,bool suppress=false) { return !suppress&&request==Client?Client:Server; }
inline uint32_t desiredKde(uint32_t request,bool explicitRequest,bool suppress=false) {
    if(suppress)return 0;
    return explicitRequest&&request<=Server?request:Server;
}
inline bool motifHasNoFrame(std::span<const uint32_t> words,uint8_t format) { return format==32&&words.size()>=3&&(words[0]&2)&&words[2]==0; }
inline bool gtkHasFrameHint(bool cardinal,uint8_t format,size_t words) { return cardinal&&format==32&&words==4; }
struct LegacyModeState {
    uint32_t applied=Server,pending=Server;bool waiting=false;
    void configure(uint32_t mode){pending=mode;waiting=true;}
    bool commit(){if(!waiting)return false;bool changed=applied!=pending;applied=pending;waiting=false;return changed;}
};
// An xdg mode is applied only after the configure is acknowledged AND its surface commits.
// Serial comparisons use the Wayland half-range rule, including uint32 wraparound.
struct ModeState {
    uint32_t applied=0;
    std::optional<uint32_t> initial;
    void deferInitial(uint32_t mode){initial=mode;}
    void initialCommit(uint32_t serial){if(initial){configure(serial,*initial);initial.reset();}}
    std::deque<std::pair<uint32_t,uint32_t>> pending;
    std::optional<uint32_t> acknowledged;
    void configure(uint32_t serial,uint32_t mode) {
        if(!pending.empty()&&pending.back().first==serial)pending.back().second=mode;
        else pending.emplace_back(serial,mode);
        if(pending.size()>64)pending.pop_front();
    }
    void ack(uint32_t serial) {
        while(!pending.empty()&&static_cast<int32_t>(serial-pending.front().first)>=0) {
            acknowledged=pending.front().second;pending.pop_front();
        }
    }
    bool commit() {
        if(!acknowledged)return false;
        bool changed=applied!=*acknowledged;applied=*acknowledged;acknowledged.reset();return changed;
    }
};
}
