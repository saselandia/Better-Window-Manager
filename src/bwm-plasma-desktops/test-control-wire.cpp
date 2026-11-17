// SPDX-License-Identifier: GPL-2.0-or-later
// Two independent clients: a control barrier must never revoke the other peer.
#include "desktop-control-client.h"
#include "plasma-desktops-client.h"
#include <wayland-client.h>
#include <cstring>
#include <iostream>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>
#include <unistd.h>
void check(bool condition){if(!condition)throw std::runtime_error("Per-client desktop barrier regression");}
struct Client;
struct Desktop {
    Client *client;std::string id;org_kde_plasma_virtual_desktop *object;
    ~Desktop(){org_kde_plasma_virtual_desktop_destroy(object);}
};
struct Client {
    wl_display *display;wl_registry *registry;
    org_kde_plasma_virtual_desktop_management *manager=nullptr;
    bwm_plasma_desktop_control_v1 *control=nullptr;
    uint32_t controlName=0,ack=0;bool paused=true,available=false;
    bool autoControl=true;
    std::string current;std::map<std::string,std::unique_ptr<Desktop>> desktops;
    static void activated(void *data,org_kde_plasma_virtual_desktop *){auto *d=static_cast<Desktop*>(data);d->client->current=d->id;}
    static void stringEvent(void *,org_kde_plasma_virtual_desktop *,const char *){}
    static void emptyEvent(void *,org_kde_plasma_virtual_desktop *){}
    static void positionEvent(void *,org_kde_plasma_virtual_desktop *,uint32_t){}
    static void created(void *data,org_kde_plasma_virtual_desktop_management *manager,const char *id,uint32_t){
        auto *c=static_cast<Client*>(data);auto d=std::make_unique<Desktop>();d->client=c;d->id=id;
        d->object=org_kde_plasma_virtual_desktop_management_get_virtual_desktop(manager,id);
        static const org_kde_plasma_virtual_desktop_listener listener={stringEvent,stringEvent,activated,emptyEvent,emptyEvent,emptyEvent,positionEvent,stringEvent};
        org_kde_plasma_virtual_desktop_add_listener(d->object,&listener,d.get());c->desktops.emplace(id,std::move(d));
    }
    static void removed(void *data,org_kde_plasma_virtual_desktop_management *,const char *id){static_cast<Client*>(data)->desktops.erase(id);}
    static void done(void *,org_kde_plasma_virtual_desktop_management *){}
    static void rows(void *,org_kde_plasma_virtual_desktop_management *,uint32_t){}
    static void availability(void *data,bwm_plasma_desktop_control_v1 *,uint32_t value){static_cast<Client*>(data)->available=value;}
    static void acknowledged(void *data,bwm_plasma_desktop_control_v1 *,uint32_t serial,uint32_t value){auto *c=static_cast<Client*>(data);c->ack=serial;c->paused=value;}
    void bindControl(){
        control=static_cast<bwm_plasma_desktop_control_v1*>(wl_registry_bind(registry,controlName,&bwm_plasma_desktop_control_v1_interface,1));
        static const bwm_plasma_desktop_control_v1_listener listener={availability,acknowledged,nullptr}; // Legacy v1 client remains supported.
        bwm_plasma_desktop_control_v1_add_listener(control,&listener,this);
    }
    static void global(void *data,wl_registry *,uint32_t name,const char *interface,uint32_t){
        auto *c=static_cast<Client*>(data);
        if(!strcmp(interface,"org_kde_plasma_virtual_desktop_management")){
            c->manager=static_cast<org_kde_plasma_virtual_desktop_management*>(wl_registry_bind(c->registry,name,&org_kde_plasma_virtual_desktop_management_interface,4));
            static const org_kde_plasma_virtual_desktop_management_listener listener={created,removed,done,rows};
            org_kde_plasma_virtual_desktop_management_add_listener(c->manager,&listener,c);
        }else if(!strcmp(interface,"bwm_plasma_desktop_control_v1")){c->controlName=name;if(c->autoControl)c->bindControl();}
    }
    static void globalRemoved(void *,wl_registry *,uint32_t){}
    explicit Client(int fd,bool controlled=true):display(wl_display_connect_to_fd(fd)),autoControl(controlled){
        check(display);registry=wl_display_get_registry(display);
        static const wl_registry_listener listener={global,globalRemoved};wl_registry_add_listener(registry,&listener,this);
        for(int i=0;i<4;++i)roundtrip();check(manager && (!controlled || (control && available)) && desktops.size()==3 && current=="1");
    }
    ~Client(){
        desktops.clear();if(control)bwm_plasma_desktop_control_v1_destroy(control);
        if(manager)org_kde_plasma_virtual_desktop_management_destroy(manager);wl_registry_destroy(registry);wl_display_flush(display);wl_display_disconnect(display);
    }
    void roundtrip(){check(wl_display_roundtrip(display)>=0);}
    void pause(uint32_t serial,bool value){bwm_plasma_desktop_control_v1_set_paused(control,serial,value);}
    void activate(const std::string &id){org_kde_plasma_virtual_desktop_request_activate(desktops.at(id)->object);}
    void expect(const std::string &id){for(int i=0;i<12 && current!=id;++i)roundtrip();check(current==id);}
};
int main(){
    try {
        Client first(std::stoi(getenv("WAYLAND_SOCKET")),false),second(std::stoi(getenv("BWM_R4_SECOND_CLIENT_FD")));
        first.activate("3");first.roundtrip();check(first.current=="1");
        first.bindControl();first.roundtrip();check(first.available);
        first.pause(1,false);first.roundtrip();check(first.ack==1 && !first.paused);
        second.pause(1,false);second.roundtrip();check(second.ack==1 && !second.paused);
        first.activate("3");first.pause(2,true);first.roundtrip();
        check(first.ack==2 && first.paused);first.expect("1");second.expect("1");
        second.activate("2");second.expect("2");first.expect("2"); // Unrelated peer still works.
        first.activate("3");first.roundtrip();check(first.current=="2");
        first.pause(3,false);first.roundtrip();check(first.ack==3 && !first.paused);
        first.activate("3");first.expect("3");second.expect("3");
        bwm_plasma_desktop_control_v1_destroy(first.control);first.control=nullptr;
        first.activate("1");first.roundtrip();check(first.current=="3"); // Owner loss is fail closed.
        first.bindControl();first.roundtrip();first.pause(4,false);first.roundtrip();
        first.activate("1");first.expect("1");second.expect("1");
        // A request already in flight at global withdrawal must address an
        // inert resource, never kill the entire client with invalid_object.
        const int command=std::stoi(getenv("BWM_R4_DESKTOP_TEST_FD"));check(::write(command,"withdraw\n",9)==9);
        first.roundtrip();second.roundtrip();
        first.pause(5,true);second.pause(2,true);first.roundtrip();second.roundtrip();
        check(first.ack==4 && second.ack==1); // Retired controls cannot acknowledge/resume work.
        std::cout<<"{\"unownedConnectionDenied\":true,\"sameFlushPendingActivationCancelled\":true,\"perClientIsolationPassed\":true,\"destroyedOwnerStaysPaused\":true,\"rebindAndResumePassed\":true,\"retiredControlsAcceptInFlightRequestsInertly\":true}\n";
        return 0;
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
