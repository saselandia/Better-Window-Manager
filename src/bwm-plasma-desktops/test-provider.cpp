// SPDX-License-Identifier: GPL-2.0-or-later
// TEST ONLY. Data-only display/socketpairs; no environment/session connection.
#include "provider.h"
#include "desktop-control-client.h"
#include "plasma-desktops-client.h"
#include <wayland-server-core.h>
#include <wayland-client.h>
#include <sys/socket.h>
#include <poll.h>
#include <unistd.h>
#include <algorithm>
#include <cerrno>
#include <dlfcn.h>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <iostream>
#include <map>
#include <stdexcept>

using namespace BwmPlasma;
void check(bool condition,const char *message){if(!condition)throw std::runtime_error(message);}
const DesktopSnapshot snapshot={{{"1","One",{"output-A"}},{"2","Two",{"output-B"}}},"1",1};
struct Server {
    wl_display *display=wl_display_create();
    Server(){check(display,"private display allocation");}
    ~Server(){wl_display_destroy_clients(display);wl_display_destroy(display);}
    void step(){
        check(wl_event_loop_dispatch(wl_display_get_event_loop(display),1)>=0,"server dispatch");
        wl_display_flush_clients(display);
    }
};
struct Client {
    wl_display *display=nullptr;wl_registry *registry=nullptr;
    wl_client *peer=nullptr;
    wl_proxy *claim=nullptr;
    std::map<uint32_t,std::string> globals;
    size_t maximumManagement=0;
    org_kde_plasma_virtual_desktop_management *manager=nullptr;
    bwm_plasma_desktop_control_v1 *control=nullptr;
    org_kde_plasma_virtual_desktop *desktop=nullptr,*lateDesktop=nullptr;
    uint32_t ack=0,association=0;bool available=false;
    static void global(void *data,wl_registry *,uint32_t name,const char *interface,uint32_t){
        auto *c=static_cast<Client*>(data);c->globals[name]=interface;
        c->maximumManagement=std::max(c->maximumManagement,c->count("org_kde_plasma_virtual_desktop_management"));
    }
    static void removed(void *data,wl_registry *,uint32_t name){static_cast<Client*>(data)->globals.erase(name);}
    size_t count(const char *interface)const{
        size_t n=0;for(const auto &[name,type]:globals)if(type==interface)++n;return n;
    }
    uint32_t name(const char *interface)const{
        for(const auto &[name,type]:globals)if(type==interface)return name;return 0;
    }
    explicit Client(Server &server){
        int sockets[2];check(socketpair(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0,sockets)==0,"client socketpair");
        peer=wl_client_create(server.display,sockets[0]);check(peer,"client server endpoint");
        display=wl_display_connect_to_fd(sockets[1]);check(display,"client endpoint");
        registry=wl_display_get_registry(display);
        static const wl_registry_listener listener={global,removed};wl_registry_add_listener(registry,&listener,this);
        flush();
    }
    void flush(){check(wl_display_flush(display)>=0 || errno==EAGAIN,"client flush");}
    void step(){
        check(wl_display_dispatch_pending(display)>=0,"client pending");
        pollfd fd{wl_display_get_fd(display),POLLIN,0};
        if(poll(&fd,1,0)>0){
            check(!(fd.revents&(POLLERR|POLLHUP)),"client connection remains alive");
            check(wl_display_prepare_read(display)==0,"client prepare read");
            check(wl_display_read_events(display)>=0,"client read events");
            check(wl_display_dispatch_pending(display)>=0,"client event dispatch");
        }
        flush();check(wl_display_get_error(display)==0,"no client protocol error");
    }
    static void stringEvent(void *,org_kde_plasma_virtual_desktop *,const char *){}
    static void emptyEvent(void *,org_kde_plasma_virtual_desktop *){}
    static void position(void *,org_kde_plasma_virtual_desktop *,uint32_t){}
    static void listen(org_kde_plasma_virtual_desktop *desktop){
        static const org_kde_plasma_virtual_desktop_listener listener={stringEvent,stringEvent,emptyEvent,emptyEvent,emptyEvent,emptyEvent,position,stringEvent};
        org_kde_plasma_virtual_desktop_add_listener(desktop,&listener,nullptr);
    }
    void bind(){
        const auto m=name("org_kde_plasma_virtual_desktop_management"),c=name("bwm_plasma_desktop_control_v1");
        check(m && c,"provider globals discovered");
        manager=static_cast<org_kde_plasma_virtual_desktop_management*>(wl_registry_bind(registry,m,&org_kde_plasma_virtual_desktop_management_interface,4));
        static const org_kde_plasma_virtual_desktop_management_listener managerListener={
            [](void *,auto *,const char *,uint32_t){},[](void *,auto *,const char *){},[](void *,auto *){},[](void *,auto *,uint32_t){}
        };
        org_kde_plasma_virtual_desktop_management_add_listener(manager,&managerListener,this);
        control=static_cast<bwm_plasma_desktop_control_v1*>(wl_registry_bind(registry,c,&bwm_plasma_desktop_control_v1_interface,2));
        static const bwm_plasma_desktop_control_v1_listener controlListener={
            [](void *data,auto *,uint32_t value){static_cast<Client*>(data)->available=value;},
            [](void *data,auto *,uint32_t serial,uint32_t){static_cast<Client*>(data)->ack=serial;},
            [](void *data,auto *,uint32_t name){static_cast<Client*>(data)->association=name;}
        };
        bwm_plasma_desktop_control_v1_add_listener(control,&controlListener,this);
        desktop=org_kde_plasma_virtual_desktop_management_get_virtual_desktop(manager,"2");listen(desktop);
    }
    void bindClaim(){
        static const wl_interface interface={"bwm_plasma_desktop_provider_claim_v1",1,0,nullptr,0,nullptr};
        const auto id=name(interface.name);check(id,"claim offered");
        claim=static_cast<wl_proxy*>(wl_registry_bind(registry,id,&interface,1));
    }
    ~Client(){
        if(claim)wl_proxy_destroy(claim);
        if(lateDesktop)org_kde_plasma_virtual_desktop_destroy(lateDesktop);
        if(desktop)org_kde_plasma_virtual_desktop_destroy(desktop);
        if(control)bwm_plasma_desktop_control_v1_destroy(control);
        if(manager)org_kde_plasma_virtual_desktop_management_destroy(manager);
        wl_registry_destroy(registry);wl_display_flush(display);wl_display_disconnect(display);
    }
};
template<class Condition>void until(Server &s,Client &c,Condition condition){
    const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(3);
    while(!condition()){
        check(std::chrono::steady_clock::now()<deadline,"bounded arbitration condition timed out");s.step();c.step();
    }
    for(int i=0;i<8;++i){s.step();c.step();}
}
void run(const char *name,void (*test)()){
    test();std::cout<<"PASS "<<name<<'\n';
}
void disabledAndRetired(){
    Server s;DesktopProvider p(s.display,{});Client c(s);check(p.valid(),"provider setup");
    check(p.publish(snapshot),"valid snapshot stored without advertising");
    until(s,c,[&]{return p.arbitrationState()=="disabled";});
    check(c.globals.empty(),"disabled provider advertises no globals or claim");
    p.setAvailable(true);check(!p.available(),"initial opt-in is asynchronous");
    until(s,c,[&]{return p.available();});
    check(c.count("org_kde_plasma_virtual_desktop_management")==1 && c.count("bwm_plasma_desktop_control_v1")==1,"unique native pair");
    c.bind();c.flush();until(s,c,[&]{return c.available && c.association!=0;});
    check(c.association==c.name("org_kde_plasma_virtual_desktop_management"),"same-display association");
    p.setAvailable(false);
    until(s,c,[&]{return c.globals.empty();});
    check(!p.available() && p.restartRequired() && !c.available,"retired provider and unavailable notification");
    p.setAvailable(true);check(!p.publish(snapshot),"retired instance cannot republish");
    check(!p.available() && c.maximumManagement==1,"no empty/second generation publication");
}
void existingProvider(){
    Server s;DesktopProtocol other(s.display,{});check(other.publish(snapshot),"foreign initial snapshot");
    DesktopProvider p(s.display,{});Client c(s);p.publish(snapshot);p.setAvailable(true);
    until(s,c,[&]{return p.arbitrationState()=="blocked";});
    check(!p.available() && c.count("bwm_plasma_desktop_provider_claim_v1")==0,"existing provider blocks publication before claim");
    other.withdraw();until(s,c,[&]{return p.available();});
    check(c.maximumManagement==1,"pre-existing provider never duplicated");
}
void simultaneousProviders(){
    Server s;DesktopProvider a(s.display,{}),b(s.display,{});Client c(s);
    a.publish(snapshot);b.publish(snapshot);a.setAvailable(true);b.setAvailable(true);
    until(s,c,[&]{return a.available() || b.available();});
    check(a.available()!=b.available(),"single elected owner");
    check(c.maximumManagement==1 && c.count("bwm_plasma_desktop_control_v1")==1,"simultaneous BWM providers never duplicate pair");
}
void lateConflict(){
    Server s;DesktopProvider p(s.display,{});Client c(s);p.publish(snapshot);p.setAvailable(true);
    until(s,c,[&]{return p.available();});
    DesktopProtocol other(s.display,{});other.publish(snapshot);
    until(s,c,[&]{return p.restartRequired();});
    check(!p.available() && p.arbitrationReason()=="foreign-provider-appeared","late conflict revokes own provider");
    check(c.count("org_kde_plasma_virtual_desktop_management")==1,"only foreign provider remains");
    other.withdraw();until(s,c,[&]{return c.globals.empty();});
    p.setAvailable(true);check(!p.available(),"late conflict cannot automatically reclaim");
}
void inFlightResources(){
    Server s;int activations=0;DesktopProvider p(s.display,[&](const auto &,const auto &){++activations;return true;});Client c(s);
    p.publish(snapshot);p.setAvailable(true);until(s,c,[&]{return p.available();});
    c.bind();c.flush();until(s,c,[&]{return c.available;});
    // These requests target existing resources and are not flushed until after
    // withdrawal. Retain the core and its old snapshot to serve queued gets.
    bwm_plasma_desktop_control_v1_set_paused(c.control,1,0);
    org_kde_plasma_virtual_desktop_request_activate(c.desktop);
    c.lateDesktop=org_kde_plasma_virtual_desktop_management_get_virtual_desktop(c.manager,"1");Client::listen(c.lateDesktop);
    p.setAvailable(false);c.flush();until(s,c,[&]{return c.globals.empty();});
    check(c.ack==0 && activations==0 && !c.available,"in-flight resources stay valid, inert and unacknowledged");
    check(p.pending()==0,"withdrawal drains no pending work");
}
void inFlightBinds(){
    Server s;int activations=0;DesktopProvider p(s.display,[&](const auto &,const auto &){++activations;return true;});Client c(s);
    p.publish(snapshot);p.setAvailable(true);until(s,c,[&]{return p.available();});
    c.bind();bwm_plasma_desktop_control_v1_set_paused(c.control,1,0);
    org_kde_plasma_virtual_desktop_request_activate(c.desktop);
    p.setAvailable(false);c.flush();until(s,c,[&]{return c.globals.empty();});
    check(c.association==0 && c.ack==0 && activations==0 && !c.available,"offered pre-removal binds remain safe and unavailable");
}
void invalidSnapshot(){
    Server s;DesktopProvider p(s.display,{});Client c(s);p.publish(snapshot);p.setAvailable(true);
    until(s,c,[&]{return p.available();});
    auto invalid=snapshot;invalid.desktops.push_back(invalid.desktops.front());
    check(!p.publish(invalid),"invalid snapshot rejected");p.setAvailable(true);
    until(s,c,[&]{return c.globals.empty();});
    check(!p.available() && p.arbitrationReason()=="invalid-backend-snapshot","invalid backend cannot become available after rejection");
}
void filterHiddenClaim(){
    Server s;
    wl_display_set_global_filter(s.display,[](const wl_client *,const wl_global *global,void *){
        return strcmp(wl_global_get_interface(global)->name,"bwm_plasma_desktop_provider_claim_v1")!=0;
    },nullptr);
    DesktopProvider p(s.display,{});Client c(s);p.publish(snapshot);p.setAvailable(true);
    until(s,c,[&]{return p.restartRequired();});
    check(!p.available() && p.arbitrationReason()=="claim-hidden-by-global-filter" && c.globals.empty(),"do not override compositor filter or publish with invisible claim");
}
void filterHiddenProvider(){
    Server s;
    wl_display_set_global_filter(s.display,[](const wl_client *,const wl_global *global,void *){
        return strcmp(wl_global_get_interface(global)->name,"bwm_plasma_desktop_control_v1")!=0;
    },nullptr);
    DesktopProvider p(s.display,{});Client c(s);p.publish(snapshot);p.setAvailable(true);
    until(s,c,[&]{return p.restartRequired();});
    check(!p.available() && p.arbitrationReason()=="provider-hidden-by-global-filter" && c.globals.empty(),"hidden control never becomes available");
}
void boundedInventory(){
    Server s;
    static const wl_interface marker={"bwm_plasma_desktop_provider_claim_v1",1,0,nullptr,0,nullptr};
    std::vector<wl_global*> markers;
    for(int i=0;i<129;++i)markers.push_back(wl_global_create(s.display,&marker,1,nullptr,[](auto *,void *,uint32_t,uint32_t){}));
    DesktopProvider p(s.display,{});Client c(s);p.publish(snapshot);p.setAvailable(true);
    until(s,c,[&]{return p.restartRequired();});
    check(!p.available() && p.arbitrationReason()=="registry-limit-exceeded","bounded target inventory fails closed");
    check(c.count("org_kde_plasma_virtual_desktop_management")==0,"overflow never publishes KDE provider");
    for(auto *marker:markers)wl_global_destroy(marker);
}
void callbackWithdrawal(){
    Server s;DesktopProvider *owner=nullptr;int activations=0;
    DesktopProvider p(s.display,[&](const auto &,const auto &){++activations;owner->setAvailable(false);return true;});owner=&p;
    Client c(s);p.publish(snapshot);p.setAvailable(true);until(s,c,[&]{return p.available();});
    c.bind();c.flush();until(s,c,[&]{return c.available;});
    bwm_plasma_desktop_control_v1_set_paused(c.control,1,0);c.flush();until(s,c,[&]{return c.ack==1;});
    org_kde_plasma_virtual_desktop_request_activate(c.desktop);
    org_kde_plasma_virtual_desktop_request_activate(c.desktop);
    c.flush();until(s,c,[&]{return p.restartRequired();});
    check(activations==1 && p.accepted()==2 && p.cancelled()==1 && p.pending()==0,"withdrawal inside callback retains core and cancels remaining action");
}
void observerDisconnected(){
    for(bool retired:{false,true}){
        Server s;DesktopProvider p(s.display,{});Client c(s);p.publish(snapshot);p.setAvailable(true);
        until(s,c,[&]{return p.available();});
        if(retired){p.setAvailable(false);until(s,c,[&]{return c.globals.empty();});}
        wl_display_destroy_clients(s.display);
        check(!p.available() && p.restartRequired() && !p.valid(),"active/retired observer loss stops polling synchronously");
        // Client destructor only destroys local proxies; do not dispatch a dead fd.
    }
}
void inventoryTimeout(){
    Server s;DesktopProvider p(s.display,{});
    p.publish(snapshot);p.setAvailable(true);
    // Start the observer, but deliberately leave the private server's reply
    // unflushed. Only this data-only fixture simulates an unresponsive peer.
    auto *loop=wl_display_get_event_loop(s.display);
    const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(3);
    while(!p.restartRequired()){
        check(std::chrono::steady_clock::now()<deadline,"private inventory deadline");
        check(wl_event_loop_dispatch(loop,20)>=0,"private unflushed inventory dispatch");
    }
    check(p.restartRequired() && !p.available() && p.arbitrationReason()=="observer-inventory-timeout","deadline cannot grant publication");
}
void delayedStartup(){
    Server s;
    const auto descriptors=[](){return size_t(std::distance(std::filesystem::directory_iterator("/proc/self/fd"),std::filesystem::directory_iterator()));};
    const auto before=descriptors();
    DesktopProvider p(s.display,{});check(p.publish(snapshot),"store backend before startup");
    check(descriptors()==before,"disabled provider creates no peer/socket/timer descriptors");
    p.setAvailable(true);
    check(p.arbitrationState()=="waiting-for-event-loop" && descriptors()==before,"opt-in queues initialization, not peer/deadline");
    // TEST ONLY: represent initialization taking longer than the 1s deadline.
    // The production provider never waits or sleeps on the compositor thread.
    check(poll(nullptr,0,1100)==0,"private delayed-loop fixture wait");
    check(!p.restartRequired() && !p.available(),"slow startup before dispatch cannot time out the unstarted inventory");
    p.setAvailable(false);check(p.arbitrationState()=="disabled","disable cancels the pending start");
    for(int i=0;i<5;++i)s.step();
    check(descriptors()==before && !p.restartRequired(),"cancelled idle does not start an observer");
    Client c(s);p.setAvailable(true);until(s,c,[&]{return p.available();});
    check(c.maximumManagement==1,"reenabling before claim creates exactly one generation");
}
void descriptorLifecycle(){
    const auto descriptors=[](){return size_t(std::distance(std::filesystem::directory_iterator("/proc/self/fd"),std::filesystem::directory_iterator()));};
    const auto before=descriptors();
    for(int i=0;i<20;++i){
        Server s;DesktopProvider p(s.display,{});Client c(s);p.publish(snapshot);p.setAvailable(true);
        until(s,c,[&]{return p.available();});p.setAvailable(false);
        until(s,c,[&]{return c.globals.empty();});
    }
    check(descriptors()==before,"observer/display teardown does not retain descriptors");
}
void moduleTeardownBeforeClients(){
    for(bool retired:{false,true}){
        Server s;Client c(s);
        void *library=dlopen(BWM_TEST_PROVIDER_MODULE,RTLD_NOW|RTLD_LOCAL);check(library,"private module dlopen");
        const auto create=reinterpret_cast<void*(*)(wl_display*)>(dlsym(library,"bwm_test_provider_create"));
        const auto retire=reinterpret_cast<void(*)(void*)>(dlsym(library,"bwm_test_provider_retire"));
        const auto destroy=reinterpret_cast<void(*)(void*)>(dlsym(library,"bwm_test_provider_destroy"));
        check(create && retire && destroy,"private module exports");
        void *provider=create(s.display);check(provider,"private provider creation");
        until(s,c,[&]{return c.count("bwm_plasma_desktop_control_v1")==1;});
        c.bind();c.bindClaim();c.flush();until(s,c,[&]{return c.available;});
        const auto resources=[&]{
            size_t count=0;
            wl_client_for_each_resource(c.peer,[](wl_resource *resource,void *data){
                const char *name=wl_resource_get_class(resource);
                if(!strcmp(name,"org_kde_plasma_virtual_desktop_management") || !strcmp(name,"org_kde_plasma_virtual_desktop") ||
                   !strcmp(name,"bwm_plasma_desktop_control_v1") || !strcmp(name,"bwm_plasma_desktop_provider_claim_v1"))++*static_cast<size_t*>(data);
                return WL_ITERATOR_CONTINUE;
            },&count);return count;
        };
        check(resources()==4,"all module-defined protocol resource kinds are bound");
        const auto controlName=c.name("bwm_plasma_desktop_control_v1");
        bwm_plasma_desktop_control_v1 *late=nullptr;
        if(retired){
            retire(provider);until(s,c,[&]{return c.globals.empty();});
            // A retained old control plus a control bound from a pre-removal
            // offer must both be destroyed before unloading the DSO.
            late=static_cast<bwm_plasma_desktop_control_v1*>(wl_registry_bind(c.registry,controlName,&bwm_plasma_desktop_control_v1_interface,2));
            static const bwm_plasma_desktop_control_v1_listener listener={
                [](void *,auto *,uint32_t){},[](void *,auto *,uint32_t,uint32_t){},[](void *,auto *,uint32_t){}
            };
            bwm_plasma_desktop_control_v1_add_listener(late,&listener,nullptr);
            c.flush();until(s,c,[&]{return resources()==5;});
        }
        destroy(provider);check(resources()==0,"finalize destroys active/retired resources before module unload");
        check(dlclose(library)==0,"private module dlclose");
        void *stillLoaded=dlopen(BWM_TEST_PROVIDER_MODULE,RTLD_NOW|RTLD_NOLOAD);
        if(stillLoaded)dlclose(stillLoaded);
        check(!stillLoaded,"callback/interface code defining module actually unmapped");
        // Hyprland 0.56.2 follows this order at cleanup: plugin unload, then
        // wl_display_destroy_clients. Do NOT dispatch queued client requests.
        wl_display_destroy_clients(s.display);
        if(late)bwm_plasma_desktop_control_v1_destroy(late);
    }
}
int main(){
    try {
        run("disabled/opt-in/withdrawal",disabledAndRetired);
        run("existing provider and removal",existingProvider);
        run("simultaneous BWM election",simultaneousProviders);
        run("late foreign conflict",lateConflict);
        run("in-flight manager/desktop/control",inFlightResources);
        run("in-flight offered binds",inFlightBinds);
        run("invalid backend state",invalidSnapshot);
        run("hidden claim preserves global filter",filterHiddenClaim);
        run("hidden provider preserves global filter",filterHiddenProvider);
        run("bounded registry inventory",boundedInventory);
        run("withdrawal inside backend callback",callbackWithdrawal);
        run("observer disconnect",observerDisconnected);
        run("inventory timeout",inventoryTimeout);
        run("slow startup and cancelled idle",delayedStartup);
        run("descriptor lifecycle over 20 displays",descriptorLifecycle);
        run("module unload before client destruction",moduleTeardownBeforeClients);
        std::cout<<"{\"arbitrationScenariosPassed\":16,\"hyprlandSessionModified\":false,\"renderingVerified\":false}\n";
        return 0;
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
