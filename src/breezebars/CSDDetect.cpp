// BWM F7: KWin policy over Hyprland's protocols. Never runs Qt or blocks on X replies.
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
#include <format>
#include <hyprutils/memory/SharedPtr.hpp>
#include <hyprutils/memory/UniquePtr.hpp>
#include <hyprutils/memory/WeakPtr.hpp>
#include <wayland-server.h>
#include <xcb/xcb.h>
#include <xcb/xcbext.h>
#include <poll.h>
#include <cstdlib>


#include <deque>
#include <dlfcn.h>
#define private public
#include <hyprland/src/protocols/XDGShell.hpp>
#include <hyprland/src/protocols/XDGDecoration.hpp>
#include <hyprland/src/protocols/ServerDecorationKDE.hpp>
#undef private
#include <hyprland/src/protocols/core/Compositor.hpp>
#include <hyprland/src/desktop/state/WindowState.hpp>
#include <hyprland/src/desktop/view/Window.hpp>
#include <hyprland/src/xwayland/XSurface.hpp>
#include <hyprland/src/Compositor.hpp>
#include <hyprland/src/plugins/PluginAPI.hpp>
#include <hyprland/src/plugins/HookSystem.hpp>
#include <hyprland/src/managers/fullscreen/FullscreenController.hpp>
#include <hyprland/src/render/Renderer.hpp>
#include "CSDDetect.hpp"
#include "CSDLogic.hpp"
#include "barDeco.hpp"

namespace {
bool enabled() { return g_pGlobalState&&g_pGlobalState->config.enabled&&g_pGlobalState->config.enabled->value(); }
// Resource destruction removes records before allocator addresses can be reused.
struct Watch : wl_listener {
    std::function<void()> cleanup;
    Watch(wl_resource* resource,std::function<void()> fn):cleanup(std::move(fn)) {
        notify=[](wl_listener* listener,void*) { auto fn=static_cast<Watch*>(listener)->cleanup;fn(); };
        wl_resource_add_destroy_listener(resource,this);
    }
    ~Watch() { wl_list_remove(&link); }
};
void refreshBars() {
    if(!g_pGlobalState)return;
    auto bars=g_pGlobalState->bars;
    for(auto& bar:bars)if(bar) {
        bool hidden=bar->m_hidden;bar->updateRules();
        if(hidden!=bar->m_hidden)if(auto w=bar->getOwner()) { w->updateWindowDecos();bar->damageEntire();g_pHyprRenderer->damageWindow(w,true); }
    }
}
bool suppressed(PHLWINDOW w) {
    if(!w)return false;
    if(Fullscreen::controller()->getFullscreenModes(w).internal==Fullscreen::FSMODE_FULLSCREEN)return true;
    if(!w->m_ruleApplicator)return false;
    if(!w->m_ruleApplicator->decorate().valueOrDefault())return true;
    auto& props=w->m_ruleApplicator->m_otherProps.props;
    auto it=props.find(g_pGlobalState->nobarRuleIdx);
    if(it==props.end())return false;
    auto text=it->second->effect;
    return truthy(text);
}
PHLWINDOW forSurface(SP<CWLSurfaceResource> surface) {
    for(auto& w:Desktop::windowState()->windows())if(w->resource()==surface)return w;
    return nullptr;
}
struct XdgState {
    CXDGDecoration* deco=nullptr;
    WP<CZxdgToplevelDecorationV1> resource;
    WP<CXDGSurfaceResource> surface;
    decltype(CZxdgToplevelDecorationV1::requests.setMode) originalSet;
    decltype(CZxdgToplevelDecorationV1::requests.unsetMode) originalUnset;
    BwmCsd::ModeState mode;
    CHyprSignalListener ack,commit,map;
    std::unique_ptr<Watch> watch;
};
struct KdeState {
    CServerDecorationKDE* deco=nullptr;
    WP<COrgKdeKwinServerDecoration> resource;
    decltype(COrgKdeKwinServerDecoration::requests.requestMode) original;
    BwmCsd::LegacyModeState mode;
    bool explicitRequest=false;
    CHyprSignalListener commit;
    std::unique_ptr<Watch> watch;
};
std::unordered_map<CXDGDecoration*,std::shared_ptr<XdgState>> xdgs;
std::unordered_map<CServerDecorationKDE*,std::shared_ptr<KdeState>> kdes;
using XdgFactory=std::function<void(CZxdgDecorationManagerV1*,uint32_t,wl_resource*)>;
using KdeFactory=std::function<void(COrgKdeKwinServerDecorationManager*,uint32_t,wl_resource*)>;
template<class R,class F>struct ManagerState { R* manager;F original;std::unique_ptr<Watch> watch; };
std::unordered_map<CZxdgDecorationManagerV1*,std::unique_ptr<ManagerState<CZxdgDecorationManagerV1,XdgFactory>>> xmanagers;
std::unordered_map<COrgKdeKwinServerDecorationManager*,std::unique_ptr<ManagerState<COrgKdeKwinServerDecorationManager,KdeFactory>>> kmanagers;
CFunctionHook *xdgHook=nullptr,*kdeHook=nullptr;
wl_event_source* timer=nullptr;
void sendXdg(const std::shared_ptr<XdgState>& state,uint32_t mode,bool force=false) {
    auto r=state->resource.lock();auto surface=state->surface.lock();
    if(!r||!surface||(!force&&state->deco->mostRecentlySent==mode))return;
    r->sendConfigure(static_cast<zxdgToplevelDecorationV1Mode>(mode));
    state->deco->mostRecentlySent=mode;
    if(surface->m_initialCommit&&!surface->m_mapped)state->mode.deferInitial(mode);
    else state->mode.configure(surface->scheduleConfigure(),mode);
}
void wrapXdg(CXDGDecoration* d) {
    if(!d||xdgs.contains(d))return;
    auto top=CXDGToplevelResource::fromResource(d->toplevelResource());
    if(!top)return;
    auto state=std::make_shared<XdgState>();state->deco=d;state->resource=d->m_resource;state->surface=top->m_owner;
    state->originalSet=d->m_resource->requests.setMode;state->originalUnset=d->m_resource->requests.unsetMode;
    if(auto surface=state->surface.lock();surface&&surface->m_mapped)state->mode.applied=d->mostRecentlySent;
    xdgs[d]=state;
    state->watch=std::make_unique<Watch>(d->m_resource->resource(),[d]{xdgs.erase(d);});
    std::weak_ptr<XdgState> weak=state;
    d->m_resource->setSetMode([weak](CZxdgToplevelDecorationV1* r,zxdgToplevelDecorationV1Mode requested) {
        if(auto s=weak.lock()) {
            if(!enabled()){s->originalSet(r,requested);sendXdg(s,s->deco->mostRecentlySent,true);}
            else {s->deco->mostRecentlyRequested=requested;auto top=CXDGToplevelResource::fromResource(s->deco->toplevelResource());sendXdg(s,BwmCsd::desiredXdg(requested,top&&suppressed(top->m_window.lock())),true);}
        }
    });
    d->m_resource->setUnsetMode([weak](CZxdgToplevelDecorationV1* r) {
        if(auto s=weak.lock()) { if(!enabled()){s->originalUnset(r);sendXdg(s,s->deco->mostRecentlySent,true);}else {s->deco->mostRecentlyRequested=0;sendXdg(s,2,true);} }
    });
    if(auto surface=state->surface.lock()) {
        state->ack=surface->m_events.ack.listen([weak](uint32_t serial){if(auto s=weak.lock())s->mode.ack(serial);});
        auto apply=[weak] {
            if(auto s=weak.lock()) {
                // First configure must follow the client's initial empty commit.
                if(s->mode.initial)if(auto surface=s->surface.lock())s->mode.initialCommit(surface->scheduleConfigure());
                if(s->mode.commit())refreshBars();
            }
        };
        state->commit=surface->m_events.commit.listen(apply);state->map=surface->m_events.map.listen(apply);
    }
    // Associate the constructor's decoration.configure with an xdg_surface serial, even without set_mode.
    sendXdg(state,enabled()?BwmCsd::desiredXdg(d->mostRecentlyRequested,suppressed(top->m_window.lock())):2,true);
}
void sendKde(const std::shared_ptr<KdeState>& s,uint32_t mode,bool force=false) {
    auto r=s->resource.lock();if(!r||(!force&&s->deco->m_mostRecentlySent==mode))return;
    r->sendMode(mode);s->deco->m_mostRecentlySent=mode;s->mode.configure(mode);
    // Legacy KDE has no ack; changes become effective on the next wl_surface commit.
}
void wrapKde(CServerDecorationKDE* d) {
    if(!d||kdes.contains(d))return;
    auto s=std::make_shared<KdeState>();s->deco=d;s->resource=d->m_resource;s->original=d->m_resource->requests.requestMode;
    s->explicitRequest=d->m_requestsSent>0;s->mode.applied=d->m_mostRecentlySent;kdes[d]=s;
    s->watch=std::make_unique<Watch>(d->m_resource->resource(),[d]{kdes.erase(d);});
    std::weak_ptr<KdeState> weak=s;
    d->m_resource->setRequestMode([weak](COrgKdeKwinServerDecoration* r,uint32_t request) {
        if(auto s=weak.lock()) {
            s->explicitRequest=true;
            if(!enabled()){s->original(r,request);s->deco->m_mostRecentlyRequested=request;sendKde(s,s->deco->m_mostRecentlySent,true);}
            else {s->deco->m_mostRecentlyRequested=request;sendKde(s,BwmCsd::desiredKde(request,true,suppressed(forSurface(s->deco->m_surf))),true);}
        }
    });
    if(d->m_surf)s->commit=d->m_surf->m_events.commit.listen([weak] {
        if(auto s=weak.lock())if(s->mode.commit())refreshBars();
    });
}
// Hook the generated callback setters, NOT tiny policy methods that Hyprland inlines.
// Both call sites were verified in the installed 0.56.2 binary; original callbacks are restored on exit.
using SetXdg=void(*)(CZxdgDecorationManagerV1*,XdgFactory&&);
using SetKde=void(*)(COrgKdeKwinServerDecorationManager*,KdeFactory&&);
void setXdgFactory(CZxdgDecorationManagerV1* manager,XdgFactory&& fn) {
    auto record=std::make_unique<ManagerState<CZxdgDecorationManagerV1,XdgFactory>>();record->manager=manager;record->original=fn;
    if(auto it=xmanagers.find(manager);it!=xmanagers.end())xmanagers.erase(it);
    record->watch=std::make_unique<Watch>(manager->resource(),[manager]{xmanagers.erase(manager);});xmanagers[manager]=std::move(record);
    XdgFactory wrapped=[old=std::move(fn)](auto* mgr,uint32_t id,wl_resource* top) {
        old(mgr,id,top);auto it=PROTO::xdgDecoration->m_decorations.find(top);if(it!=PROTO::xdgDecoration->m_decorations.end())wrapXdg(it->second.get());
    };
    reinterpret_cast<SetXdg>(xdgHook->m_original)(manager,std::move(wrapped));
}
void setKdeFactory(COrgKdeKwinServerDecorationManager* manager,KdeFactory&& fn) {
    auto record=std::make_unique<ManagerState<COrgKdeKwinServerDecorationManager,KdeFactory>>();record->manager=manager;record->original=fn;
    if(auto it=kmanagers.find(manager);it!=kmanagers.end())kmanagers.erase(it);
    record->watch=std::make_unique<Watch>(manager->resource(),[manager]{kmanagers.erase(manager);});kmanagers[manager]=std::move(record);
    KdeFactory wrapped=[old=std::move(fn)](auto* mgr,uint32_t id,wl_resource* surf) {
        old(mgr,id,surf);for(auto& d:PROTO::serverDecorationKDE->m_decos)if(d->m_surf==CWLSurfaceResource::fromResource(surf))wrapKde(d.get());
    };
    reinterpret_cast<SetKde>(kdeHook->m_original)(manager,std::move(wrapped));
}
// Read X11 properties asynchronously on a separate XCB connection. No waits in render/IPC paths.
struct XState {
    PHLWINDOWREF owner;
    pid_t pid=0;
    unsigned motifSeq=0,gtkSeq=0;
    bool motifDone=false,gtkDone=false,motifNoBorder=false,gtk=false;
};
xcb_connection_t* connection=nullptr;
wl_event_source* xsource=nullptr;
std::string display;
std::chrono::steady_clock::time_point nextConnectionAttempt{};
xcb_atom_t motifAtom=0,gtkAtom=0,moveResizeAtom=0;
unsigned motifAtomSeq=0,gtkAtomSeq=0,moveResizeAtomSeq=0;
std::unordered_map<uint32_t,XState> xwindows;
void disconnectX() {
    if(xsource)wl_event_source_remove(xsource);xsource=nullptr;
    if(connection)xcb_disconnect(connection);connection=nullptr;
    motifAtom=gtkAtom=moveResizeAtom=0;motifAtomSeq=gtkAtomSeq=moveResizeAtomSeq=0;xwindows.clear();
}
void query(XState& s,uint32_t xid) {
    if(!connection||!motifAtom||!gtkAtom)return;
    if(s.motifSeq)xcb_discard_reply(connection,s.motifSeq);
    if(s.gtkSeq)xcb_discard_reply(connection,s.gtkSeq);
    s.motifDone=s.gtkDone=false;
    s.motifSeq=xcb_get_property(connection,0,xid,motifAtom,XCB_ATOM_ANY,0,5).sequence;
    s.gtkSeq=xcb_get_property(connection,0,xid,gtkAtom,XCB_ATOM_CARDINAL,0,4).sequence;
    xcb_flush(connection);
}
bool reply(unsigned& sequence,void** result) {
    if(!sequence)return false;
    xcb_generic_error_t* error=nullptr;
    if(!xcb_poll_for_reply(connection,sequence,result,&error))return false;
    free(error);sequence=0;return true;
}
void pumpX() {
    if(!connection)return;
    if(xcb_connection_has_error(connection)){disconnectX();return;}
    bool changed=false;
    while(auto event=xcb_poll_for_event(connection)) {
        uint8_t type=event->response_type&0x7f;
        if(type==XCB_CLIENT_MESSAGE) {
            const auto e=reinterpret_cast<xcb_client_message_event_t*>(event);
            if(enabled() && moveResizeAtom && e->type==moveResizeAtom && e->format==32) {
                auto it=xwindows.find(e->window);
                if(it!=xwindows.end()) if(auto owner=it->second.owner.lock(); owner && owner->getPID()==it->second.pid)
                    handleClientMoveResize(owner,e->data.data32[2],e->data.data32[3]);
            }
        } else if(type==XCB_PROPERTY_NOTIFY) {
            auto e=reinterpret_cast<xcb_property_notify_event_t*>(event);
            if(e->atom==motifAtom||e->atom==gtkAtom)if(auto it=xwindows.find(e->window);it!=xwindows.end()){query(it->second,e->window);changed=true;}
        } else if(type==XCB_DESTROY_NOTIFY)xwindows.erase(reinterpret_cast<xcb_destroy_notify_event_t*>(event)->window);
        free(event);
    }
    bool atomsReady=motifAtom&&gtkAtom;
    void* raw=nullptr;
    if(reply(motifAtomSeq,&raw)){if(raw)motifAtom=static_cast<xcb_intern_atom_reply_t*>(raw)->atom;free(raw);raw=nullptr;}
    if(reply(gtkAtomSeq,&raw)){if(raw)gtkAtom=static_cast<xcb_intern_atom_reply_t*>(raw)->atom;free(raw);raw=nullptr;}
    if(reply(moveResizeAtomSeq,&raw)){if(raw)moveResizeAtom=static_cast<xcb_intern_atom_reply_t*>(raw)->atom;free(raw);raw=nullptr;}
    if(!atomsReady&&motifAtom&&gtkAtom)for(auto& [id,s]:xwindows)query(s,id);
    for(auto it=xwindows.begin();it!=xwindows.end();) {
        auto& s=it->second;auto owner=s.owner.lock();
        if(!owner||owner->getPID()!=s.pid) { if(s.motifSeq)xcb_discard_reply(connection,s.motifSeq);if(s.gtkSeq)xcb_discard_reply(connection,s.gtkSeq);it=xwindows.erase(it);continue; }
        if(reply(s.motifSeq,&raw)) {
            s.motifDone=true;s.motifNoBorder=false;
            auto r=static_cast<xcb_get_property_reply_t*>(raw);
            if(r&&r->format==32&&xcb_get_property_value_length(r)>=12) {auto v=static_cast<uint32_t*>(xcb_get_property_value(r));s.motifNoBorder=BwmCsd::motifHasNoFrame({v,static_cast<size_t>(xcb_get_property_value_length(r)/4)},r->format);}
            free(raw);raw=nullptr;changed=true;
        }
        if(reply(s.gtkSeq,&raw)) {
            s.gtkDone=true;auto r=static_cast<xcb_get_property_reply_t*>(raw);
            // Presence of a valid 4-CARDINAL hint is CSD, even with zero shadow extents.
            s.gtk=r&&r->bytes_after==0&&BwmCsd::gtkHasFrameHint(r->type==XCB_ATOM_CARDINAL,r->format,xcb_get_property_value_length(r)/4);
            free(raw);raw=nullptr;changed=true;
        }
        ++it;
    }
    if(changed)refreshBars();
}
void connectX() {
    const char* value=getenv("DISPLAY");if(!value||!*value)return;
    if(connection&&(display!=value||xcb_connection_has_error(connection)))disconnectX();
    if(connection)return;
    auto now=std::chrono::steady_clock::now();if(now<nextConnectionAttempt)return;
    nextConnectionAttempt=now+std::chrono::seconds(5);
    connection=xcb_connect(value,nullptr);
    if(xcb_connection_has_error(connection)){disconnectX();return;}
    display=value;
    // Observe EWMH messages sent to the root; never request SubstructureRedirect (the WM owns it).
    auto screens=xcb_setup_roots_iterator(xcb_get_setup(connection));
    for(;screens.rem;xcb_screen_next(&screens)) {
        uint32_t mask=XCB_EVENT_MASK_SUBSTRUCTURE_NOTIFY;
        xcb_change_window_attributes(connection,screens.data->root,XCB_CW_EVENT_MASK,&mask);
    }
    moveResizeAtomSeq=xcb_intern_atom(connection,0,sizeof("_NET_WM_MOVERESIZE")-1,"_NET_WM_MOVERESIZE").sequence;
    for(auto& [id,state]:xwindows) {uint32_t mask=XCB_EVENT_MASK_PROPERTY_CHANGE|XCB_EVENT_MASK_STRUCTURE_NOTIFY;xcb_change_window_attributes(connection,id,XCB_CW_EVENT_MASK,&mask);}
    motifAtomSeq=xcb_intern_atom(connection,0,15,"_MOTIF_WM_HINTS").sequence;
    gtkAtomSeq=xcb_intern_atom(connection,0,18,"_GTK_FRAME_EXTENTS").sequence;
    xsource=wl_event_loop_add_fd(g_pCompositor->m_wlEventLoop,xcb_get_file_descriptor(connection),WL_EVENT_READABLE|WL_EVENT_HANGUP|WL_EVENT_ERROR,
        [](int,uint32_t,void*)->int{pumpX();return 0;},nullptr);
    xcb_flush(connection);
}
}

void refreshDecorationDetection() {
    if(!xwindows.empty())connectX();
    pumpX();
    for(auto& [d,s]:xdgs) {
        auto top=CXDGToplevelResource::fromResource(d->toplevelResource());
        sendXdg(s,enabled()?BwmCsd::desiredXdg(d->mostRecentlyRequested,top&&suppressed(top->m_window.lock())):2);
    }
    for(auto& [d,s]:kdes)sendKde(s,enabled()?BwmCsd::desiredKde(d->m_mostRecentlyRequested,s->explicitRequest,suppressed(forSurface(d->m_surf))):2);
    refreshBars();
}
void initDecorationDetection() {
    // Exact Itanium ABI symbols of the installed/checked 0.56.2 headers. No external nm process at runtime.
    auto install=[](CFunctionHook*& hook,const char* symbol,void* replacement) {
        auto source=dlsym(RTLD_DEFAULT,symbol);
        if(!source)throw std::runtime_error(std::string("breezebars: decoration ABI missing: ")+symbol);
        hook=HyprlandAPI::createFunctionHook(PHANDLE,source,replacement);
        if(!hook||!hook->hook())throw std::runtime_error("breezebars: cannot hook decoration callback setter");
    };
    install(xdgHook,"_ZN24CZxdgDecorationManagerV124setGetToplevelDecorationEOSt8functionIFvPS_jP11wl_resourceEE",reinterpret_cast<void*>(&setXdgFactory));
    install(kdeHook,"_ZN34COrgKdeKwinServerDecorationManager9setCreateEOSt8functionIFvPS_jP11wl_resourceEE",reinterpret_cast<void*>(&setKdeFactory));
    if(PROTO::xdgDecoration) {
        for(auto& manager:PROTO::xdgDecoration->m_managers)manager->setGetToplevelDecoration(XdgFactory(manager->requests.getToplevelDecoration));
        for(auto& [top,d]:PROTO::xdgDecoration->m_decorations)wrapXdg(d.get());
    }
    if(PROTO::serverDecorationKDE) {
        for(auto& manager:PROTO::serverDecorationKDE->m_managers)manager->setCreate(KdeFactory(manager->requests.create));
        for(auto& d:PROTO::serverDecorationKDE->m_decos)wrapKde(d.get());
    }
    connectX(); // X setup happens at initialization/timer, never on render or IPC queries.
    timer=wl_event_loop_add_timer(g_pCompositor->m_wlEventLoop,[](void*)->int {refreshDecorationDetection();if(timer)wl_event_source_timer_update(timer,100);return 0;},nullptr);
    wl_event_source_timer_update(timer,100);
}
void closeDecorationDetection() {
    if(timer)wl_event_source_remove(timer);timer=nullptr;
    if(xdgHook)HyprlandAPI::removeFunctionHook(PHANDLE,xdgHook);xdgHook=nullptr;
    if(kdeHook)HyprlandAPI::removeFunctionHook(PHANDLE,kdeHook);kdeHook=nullptr;
    for(auto& [manager,s]:xmanagers)manager->setGetToplevelDecoration(std::move(s->original));
    for(auto& [manager,s]:kmanagers)manager->setCreate(std::move(s->original));
    for(auto& [d,s]:xdgs)if(auto r=s->resource.lock()) {r->setSetMode(std::move(s->originalSet));r->setUnsetMode(std::move(s->originalUnset));}
    for(auto& [d,s]:kdes)if(auto r=s->resource.lock())r->setRequestMode(std::move(s->original));
    xdgs.clear();kdes.clear();xmanagers.clear();kmanagers.clear();disconnectX();
}
SDecoDetection detectDecorations(PHLWINDOW w) {
    SDecoDetection out;if(!w){out.ready=false;out.reason="no window";return out;}
    BwmCsd::Input input;
    input.x11=w->m_isX11;
    input.fullscreen=Fullscreen::controller()->getFullscreenModes(w).internal==Fullscreen::FSMODE_FULLSCREEN;
    input.decorate=!w->m_ruleApplicator||w->m_ruleApplicator->decorate().valueOrDefault();
    if(w->m_ruleApplicator&&g_pGlobalState) {
        auto& props=w->m_ruleApplicator->m_otherProps.props;auto it=props.find(g_pGlobalState->nobarRuleIdx);
        if(it!=props.end()) {auto v=it->second->effect;input.noBar=truthy(v);}
    }
    if(input.x11) {
        input.overrideRedirect=w->isX11OverrideRedirect();input.x11Special=w->m_X11DoesntWantBorders;input.x11Ready=false;
        if(auto surface=w->m_xwaylandSurface.lock()) {
            {
                auto id=surface->m_xID;auto it=xwindows.find(id);
                if(it==xwindows.end()||it->second.owner.lock()!=w||it->second.pid!=w->getPID()) {
                    XState state;state.owner=w;state.pid=w->getPID();xwindows[id]=std::move(state);
                    uint32_t mask=XCB_EVENT_MASK_PROPERTY_CHANGE|XCB_EVENT_MASK_STRUCTURE_NOTIFY;
                    if(connection){xcb_change_window_attributes(connection,id,XCB_CW_EVENT_MASK,&mask);query(xwindows[id],id);xcb_flush(connection);}
                    it=xwindows.find(id);
                }
                input.x11Ready=it->second.motifDone&&it->second.gtkDone;input.motifNoBorder=it->second.motifNoBorder;input.gtkFrameExtents=it->second.gtk;
            }
        }
    } else {
        auto surface=w->m_xdgSurface.lock();auto top=surface?surface->m_toplevel.lock():nullptr;
        if(top&&PROTO::xdgDecoration)if(auto it=PROTO::xdgDecoration->m_decorations.find(top->m_resource->resource());it!=PROTO::xdgDecoration->m_decorations.end()) {
            auto d=it->second.get();input.xdg=true;out.xdgRequested=d->mostRecentlyRequested;out.sent=d->mostRecentlySent;
            input.applied=xdgs.contains(d)?xdgs.at(d)->mode.applied:0;
        }
        if(!input.xdg&&PROTO::serverDecorationKDE)for(auto& d:PROTO::serverDecorationKDE->m_decos)if(d->m_surf==w->resource()) {
            input.kde=true;out.kdeRequested=d->m_mostRecentlyRequested;out.sent=d->m_mostRecentlySent;
            input.kdeExplicit=kdes.contains(d.get())?kdes.at(d.get())->explicitRequest:d->m_requestsSent>0;
            input.applied=kdes.contains(d.get())?kdes.at(d.get())->mode.applied:d->m_mostRecentlySent;break;
        }
    }
    out.observed=input;auto decision=BwmCsd::decide(input);out.clientDraws=!decision.bar;out.ready=decision.ready;out.reason=decision.reason;out.applied=input.applied;
    return out;
}
