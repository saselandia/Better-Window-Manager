// SPDX-License-Identifier: GPL-2.0-or-later
#include "provider.h"
#include <wayland-server-core.h>
#include <wayland-client.h>
#include <sys/socket.h>
#include <unistd.h>
#include <cerrno>
#include <cstring>
#include <map>
#include <set>

namespace BwmPlasma {
namespace {
constexpr char managementInterface[]="org_kde_plasma_virtual_desktop_management";
constexpr char controlInterface[]="bwm_plasma_desktop_control_v1";
// Registry-only election marker shared by cooperating BWM providers. It is not
// a setting or a replacement for KDE's desktop protocol. Lowest visible ID wins.
const wl_interface claimInterface={"bwm_plasma_desktop_provider_claim_v1",1,0,nullptr,0,nullptr};
}
struct DesktopProvider::Impl {
    wl_display *serverDisplay=nullptr,*probeDisplay=nullptr;
    wl_client *probeClient=nullptr;
    struct Peer {
        wl_listener destroyed{};
        Impl *owner=nullptr;
    } peer;
    wl_registry *registry=nullptr;
    wl_callback *fence=nullptr;
    wl_event_source *fdSource=nullptr,*timer=nullptr,*startIdle=nullptr;
    wl_global *claim=nullptr;
    std::set<wl_resource*> claimResources;
    uint32_t claimName=0,managementName=0,controlName=0;
    struct Entry{std::string interface;uint32_t version;};
    std::map<uint32_t,Entry> globals;
    std::unique_ptr<DesktopProtocol> protocol;
    DesktopProtocol::Activate activate;
    DesktopSnapshot desired;
    bool requested=false,inventoryReady=false,snapshotReady=false,terminal=false,ioFailed=false,claimRemoved=false;
    std::string state="disabled",reason;

    static void bindClaim(wl_client *client,void *data,uint32_t,uint32_t id){
        auto *p=static_cast<Impl*>(data);
        if(p->claimResources.size()>=256){wl_client_post_no_memory(client);return;}
        auto *resource=wl_resource_create(client,&claimInterface,1,id);
        if(!resource){wl_client_post_no_memory(client);return;}
        wl_resource_set_implementation(resource,nullptr,p,[](wl_resource *r){
            if(auto *owner=static_cast<Impl*>(wl_resource_get_user_data(r)))owner->claimResources.erase(r);
        });
        p->claimResources.insert(resource);
    }

    void withdraw(const std::string &why,bool failure=false){
        if(terminal){
            // A retired observer can subsequently lose its peer. Stop polling
            // HUP/error even though the publication is already terminal.
            if(failure){
                ioFailed=true;
                if(timer)wl_event_source_timer_update(timer,0);
                if(fdSource){wl_event_source_remove(fdSource);fdSource=nullptr;}
            }
            return;
        }
        // Retain exactly one generation, including managers/desktops. The KDE
        // protocol has no client destructor requests for those bound resources.
        // wl_global_remove stops new discovery, not already-offered binds.
        if(protocol)protocol->withdraw();
        if(claim && !claimRemoved){wl_global_remove(claim);claimRemoved=true;}
        terminal=true;ioFailed|=failure;state=failure?"failed":"retired";reason=why;
        if(startIdle){wl_event_source_remove(startIdle);startIdle=nullptr;}
        if(timer)wl_event_source_timer_update(timer,0);
        if(failure && fdSource){wl_event_source_remove(fdSource);fdSource=nullptr;}
    }
    bool foreignGlobals()const{
        for(const auto &[name,entry]:globals)
            if((entry.interface==managementInterface && name!=managementName) ||
               (entry.interface==controlInterface && name!=controlName))return true;
        return false;
    }
    uint32_t firstClaim()const{
        for(const auto &[name,entry]:globals)if(entry.interface==claimInterface.name)return name;
        return 0;
    }
    void flush(){
        if(!probeDisplay || ioFailed)return;
        const auto result=wl_display_flush(probeDisplay);
        if(result<0 && errno!=EAGAIN){withdraw("observer-flush-failed",true);return;}
        if(fdSource && wl_event_source_fd_update(fdSource,WL_EVENT_READABLE | (result<0?WL_EVENT_WRITABLE:0))<0)
            withdraw("observer-poll-update-failed",true);
    }
    static void fenceDone(void *data,wl_callback *callback,uint32_t){
        auto *p=static_cast<Impl*>(data);wl_callback_destroy(callback);p->fence=nullptr;
        wl_event_source_timer_update(p->timer,0);
        if(p->terminal)return;
        p->inventoryReady=true;
        p->evaluate();
    }
    void sync(){
        if(terminal || fence)return;
        fence=wl_display_sync(probeDisplay);
        if(!fence){withdraw("observer-sync-allocation-failed",true);return;}
        static const wl_callback_listener listener={fenceDone};
        if(wl_callback_add_listener(fence,&listener,this)<0 || wl_event_source_timer_update(timer,1000)<0){
            withdraw("observer-sync-setup-failed",true);return;
        }
        flush();
    }
    void evaluate(){
        if(terminal)return;
        if(!probeDisplay){
            if(!requested || !snapshotReady){
                if(startIdle){wl_event_source_remove(startIdle);startIdle=nullptr;}
                state="disabled";return;
            }
            // Plugin initialization/configuration can precede dispatch by more
            // than the inventory deadline. Start the peer and its clock only
            // inside the existing event loop, after explicit backend opt-in.
            state="waiting-for-event-loop";
            if(!startIdle)startIdle=wl_event_loop_add_idle(wl_display_get_event_loop(serverDisplay),[](void *data){
                auto *p=static_cast<Impl*>(data);p->startIdle=nullptr;
                if(!p->terminal && p->requested && p->snapshotReady)p->startObserver();
            },this);
            if(!startIdle)withdraw("observer-idle-allocation-failed",true);
            return;
        }
        // Observed conflicts revoke actions in this callback. Another module
        // can still publish before our observer is dispatched; this is not a
        // lock on arbitrary wl_global_create calls. Publication starts paused.
        if(protocol && foreignGlobals()){withdraw("foreign-provider-appeared");return;}
        if(fence || !inventoryReady)return;
        if(!requested || !snapshotReady){state="disabled";return;}
        if(foreignGlobals()){
            if(claim){withdraw("foreign-provider-during-election");return;}
            state="blocked";reason="existing-visible-desktop-provider";return;
        }
        if(!claim){
            if(firstClaim()){state="blocked";reason="existing-provider-claim";return;}
            claim=wl_global_create(serverDisplay,&claimInterface,1,this,bindClaim);
            if(!claim){withdraw("claim-allocation-failed",true);return;}
            claimName=wl_global_get_name(claim,probeClient);
            if(!claimName){withdraw("claim-hidden-by-global-filter",true);return;}
            state="claiming";reason.clear();sync();return;
        }
        if(!globals.contains(claimName) || firstClaim()!=claimName){withdraw("provider-election-lost-or-hidden");return;}
        if(!protocol){
            protocol=std::make_unique<DesktopProtocol>(serverDisplay,activate,false);
            if(!protocol->valid() || !protocol->publish(desired)){withdraw("provider-publication-failed",true);return;}
            managementName=protocol->managementName(probeClient);controlName=protocol->controlName(probeClient);
            if(!managementName || !controlName){withdraw("provider-hidden-by-global-filter",true);return;}
            state="publishing";sync();return;
        }
        const auto management=globals.find(managementName),control=globals.find(controlName);
        if(management==globals.end() || control==globals.end() || management->second.version<4 || control->second.version<2){
            withdraw("own-provider-not-visible",true);return;
        }
        protocol->setAvailable(true);state="active";reason.clear();
    }
    static void global(void *data,wl_registry *,uint32_t name,const char *interface,uint32_t version){
        auto *p=static_cast<Impl*>(data);
        if(p->terminal)return;
        if(strcmp(interface,managementInterface) && strcmp(interface,controlInterface) && strcmp(interface,claimInterface.name))return;
        if(!p->globals.contains(name) && p->globals.size()>=128){p->withdraw("registry-limit-exceeded",true);return;}
        p->globals[name]={interface,version};p->evaluate();
    }
    static void removed(void *data,wl_registry *,uint32_t name){
        auto *p=static_cast<Impl*>(data);p->globals.erase(name);
        if(!p->terminal && p->protocol && (name==p->managementName || name==p->controlName || name==p->claimName)){
            p->withdraw("own-global-withdrawn",true);return;
        }
        p->evaluate();
    }
    static int dispatch(int,uint32_t mask,void *data){
        auto *p=static_cast<Impl*>(data);
        if(p->ioFailed)return 0;
        if(mask&(WL_EVENT_HANGUP|WL_EVENT_ERROR)){p->withdraw("observer-disconnected",true);return 0;}
        if(mask&WL_EVENT_READABLE){
            while(wl_display_prepare_read(p->probeDisplay)!=0){
                if(wl_display_dispatch_pending(p->probeDisplay)<0){p->withdraw("observer-dispatch-failed",true);return 0;}
            }
            if(wl_display_read_events(p->probeDisplay)<0 || wl_display_dispatch_pending(p->probeDisplay)<0){
                p->withdraw("observer-read-failed",true);return 0;
            }
        }
        p->flush();return 0;
    }
    void startObserver(){
        state="inventory";
        int sockets[2];
        if(socketpair(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0,sockets)<0){withdraw("observer-socketpair-failed",true);return;}
        // libwayland owns each endpoint after successful construction. No
        // listening socket, getenv/WAYLAND_DISPLAY, fork, thread or roundtrip.
        probeClient=wl_client_create(serverDisplay,sockets[0]);
        if(!probeClient){close(sockets[0]);close(sockets[1]);withdraw("observer-peer-failed",true);return;}
        peer.owner=this;peer.destroyed.notify=[](wl_listener *listener,void *){
            auto *p=reinterpret_cast<Peer*>(listener)->owner;
            wl_list_remove(&p->peer.destroyed.link);p->probeClient=nullptr;
            p->withdraw("observer-server-peer-destroyed",true);
        };
        wl_client_add_destroy_listener(probeClient,&peer.destroyed);
        probeDisplay=wl_display_connect_to_fd(sockets[1]);
        // wl_display_connect_to_fd consumes/closes this fd even on failure.
        if(!probeDisplay){withdraw("observer-connect-failed",true);return;}
        auto *loop=wl_display_get_event_loop(serverDisplay);
        fdSource=wl_event_loop_add_fd(loop,wl_display_get_fd(probeDisplay),WL_EVENT_READABLE,dispatch,this);
        timer=wl_event_loop_add_timer(loop,[](void *data){static_cast<Impl*>(data)->withdraw("observer-inventory-timeout",true);return 0;},this);
        registry=wl_display_get_registry(probeDisplay);
        if(!fdSource || !timer || !registry){withdraw("observer-setup-failed",true);return;}
        static const wl_registry_listener listener={global,removed};
        if(wl_registry_add_listener(registry,&listener,this)<0){withdraw("observer-listener-failed",true);return;}
        sync();
    }
    explicit Impl(wl_display *display,DesktopProtocol::Activate callback):serverDisplay(display),activate(std::move(callback)){
        if(!display)withdraw("missing-server-display",true);
    }
    ~Impl(){
        if(startIdle)wl_event_source_remove(startIdle);
        if(fdSource)wl_event_source_remove(fdSource);
        if(timer)wl_event_source_remove(timer);
        if(fence)wl_callback_destroy(fence);
        if(registry)wl_registry_destroy(registry);
        if(probeDisplay)wl_display_disconnect(probeDisplay);
        if(probeClient){wl_list_remove(&peer.destroyed.link);wl_client_destroy(probeClient);}
        protocol.reset();
        if(claim)wl_global_destroy(claim);
        for(auto *r:claimResources){wl_resource_set_user_data(r,nullptr);wl_resource_destroy(r);}
    }
};
DesktopProvider::DesktopProvider(wl_display *display,DesktopProtocol::Activate activate):d(std::make_unique<Impl>(display,std::move(activate))){}
DesktopProvider::~DesktopProvider()=default;
bool DesktopProvider::valid()const{return !d->ioFailed;}
bool DesktopProvider::publish(const DesktopSnapshot &snapshot){
    if(d->terminal)return false;
    if(!DesktopProtocol::validSnapshot(snapshot)){
        if(d->claim)d->withdraw("invalid-backend-snapshot");
        else {d->requested=false;d->state="disabled";d->reason="invalid-backend-snapshot";}
        return false;
    }
    d->desired=snapshot;d->snapshotReady=true;
    if(d->protocol && !d->terminal && !d->protocol->publish(snapshot)){d->withdraw("invalid-provider-snapshot",true);return false;}
    d->evaluate();d->flush();return !d->terminal;
}
void DesktopProvider::setAvailable(bool requested){
    d->requested=requested;
    if(!requested && d->claim && !d->terminal)d->withdraw("disabled-after-claim");
    else d->evaluate();
    d->flush();
}
bool DesktopProvider::available()const{return d->protocol && d->protocol->available();}
const DesktopSnapshot &DesktopProvider::snapshot()const{return d->desired;}
std::string DesktopProvider::arbitrationState()const{return d->state;}
std::string DesktopProvider::arbitrationReason()const{return d->reason;}
bool DesktopProvider::restartRequired()const{return d->terminal;}
uint64_t DesktopProvider::accepted()const{return d->protocol?d->protocol->accepted():0;}
uint64_t DesktopProvider::rejected()const{return d->protocol?d->protocol->rejected():0;}
std::string DesktopProvider::lastRejected()const{return d->protocol?d->protocol->lastRejected():"";}
size_t DesktopProvider::pending()const{return d->protocol?d->protocol->pending():0;}
uint64_t DesktopProvider::cancelled()const{return d->protocol?d->protocol->cancelled():0;}
}
