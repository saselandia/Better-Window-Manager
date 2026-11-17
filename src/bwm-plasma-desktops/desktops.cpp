// SPDX-License-Identifier: GPL-2.0-or-later
#include "desktops.h"
#include "plasma-desktops-server.h"
#include "desktop-control-server.h"
#include <wayland-server-core.h>
#include <algorithm>
#include <map>
#include <set>
#include <utility>
#include <deque>
namespace BwmPlasma {
struct DesktopProtocol::Impl {
    wl_global *global=nullptr,*controlGlobal=nullptr;
    wl_event_loop *loop=nullptr;
    wl_event_source *idle=nullptr;
    DesktopSnapshot state;
    Activate activate;
    std::set<wl_resource*> managers;
    std::set<wl_resource*> controls;
    struct Handle{std::string id;uint64_t serial;};
    std::map<wl_resource*,Handle> handles;
    struct Peer {
        wl_listener destroyed{}; // First member, for the Wayland listener callback.
        Impl *owner=nullptr;wl_client *client=nullptr;wl_resource *control=nullptr;
        bool paused=true; // Read-only until this connection explicitly owns/resumes a control.
        ~Peer(){wl_list_remove(&destroyed.link);}
    };
    std::map<wl_client*,std::unique_ptr<Peer>> peers;
    struct Pending{wl_client *client;wl_resource *resource;uint64_t serial;std::string id,output;};
    std::deque<Pending> queue;
    bool available=true,withdrawn=false;
    uint64_t accepted=0,rejected=0,cancelled=0,nextHandle=1;
    std::string lastRejected;
    const Desktop *find(const std::string &id)const {
        const auto i=std::find_if(state.desktops.begin(),state.desktops.end(),[&](const auto &v){return v.id==id;});
        return i==state.desktops.end()?nullptr:&*i;
    }
    void reject(const std::string &operation){++rejected;lastRejected=operation;}
    static Impl *self(wl_resource *r){return static_cast<Impl*>(wl_resource_get_user_data(r));}
    static void managerDestroyed(wl_resource *r){if(auto *p=self(r))p->managers.erase(r);}
    void cancel(wl_client *client){
        const auto before=queue.size();std::erase_if(queue,[&](const auto &v){return v.client==client;});cancelled+=before-queue.size();
        if(queue.empty() && idle){wl_event_source_remove(idle);idle=nullptr;}
    }
    static void peerDestroyed(wl_listener *listener,void *){
        auto *peer=reinterpret_cast<Peer*>(listener);auto *owner=peer->owner;auto *client=peer->client;
        owner->cancel(client);owner->peers.erase(client);
    }
    Peer *peer(wl_client *client){
        if(auto i=peers.find(client);i!=peers.end())return i->second.get();
        if(peers.size()>=512)return nullptr;
        auto value=std::make_unique<Peer>();value->owner=this;value->client=client;
        value->destroyed.notify=peerDestroyed;wl_client_add_destroy_listener(client,&value->destroyed);
        auto *result=value.get();peers.emplace(client,std::move(value));return result;
    }
    static void desktopDestroyed(wl_resource *r){if(auto *p=self(r)){
        const auto before=p->queue.size();std::erase_if(p->queue,[&](const auto &v){return v.resource==r;});p->cancelled+=before-p->queue.size();p->handles.erase(r);
    }}
    static void controlDestroyed(wl_resource *r){if(auto *p=self(r)){
        p->controls.erase(r);
        const auto i=p->peers.find(wl_resource_get_client(r));
        if(i!=p->peers.end() && i->second->control==r){i->second->control=nullptr;i->second->paused=true;p->cancel(i->first);}
    }}
    static void destroyControl(wl_client *,wl_resource *r){wl_resource_destroy(r);}
    static void pause(wl_client *client,wl_resource *r,uint32_t serial,uint32_t value){
        auto *p=self(r);if(!p || p->withdrawn)return;
        if(value>1){wl_resource_post_error(r,BWM_PLASMA_DESKTOP_CONTROL_V1_ERROR_INVALID_STATE,"Invalid paused state");return;}
        const auto i=p->peers.find(client);if(i==p->peers.end())return;
        i->second->paused=value;
        if(value)p->cancel(client);
        bwm_plasma_desktop_control_v1_send_acknowledged(r,serial,value);
    }
    static void bindControl(wl_client *client,void *data,uint32_t version,uint32_t id){
        auto *p=static_cast<Impl*>(data);
        if(p->controls.size()>=4096){wl_client_post_no_memory(client);return;}
        auto *peer=p->peer(client);
        if(!peer){wl_client_post_no_memory(client);return;}
        auto *r=wl_resource_create(client,&bwm_plasma_desktop_control_v1_interface,std::min(version,2u),id);
        if(!r){wl_client_post_no_memory(client);return;}
        static const struct bwm_plasma_desktop_control_v1_interface implementation={destroyControl,pause};
        wl_resource_set_implementation(r,&implementation,p,controlDestroyed);
        p->controls.insert(r);
        if(p->withdrawn){
            bwm_plasma_desktop_control_v1_send_availability(r,0);
            if(version>=2)bwm_plasma_desktop_control_v1_send_desktop_global(r,0);
            return;
        }
        if(peer->control){wl_resource_post_error(r,BWM_PLASMA_DESKTOP_CONTROL_V1_ERROR_ALREADY_BOUND,"Desktop control already owned by this connection");return;}
        peer->control=r;peer->paused=true;p->cancel(client);
        bwm_plasma_desktop_control_v1_send_availability(r,p->available);
        if(version>=2)bwm_plasma_desktop_control_v1_send_desktop_global(r,wl_global_get_name(p->global,client));
    }
    void drain(){
        idle=nullptr;
        while(!queue.empty()){
            const auto request=queue.front();queue.pop_front();
            const auto h=handles.find(request.resource),end=handles.end();
            const auto peer=peers.find(request.client);
            if(!available || peer==peers.end() || peer->second->paused || h==end || h->second.serial!=request.serial || !find(request.id)){
                ++cancelled;continue;
            }
            // Backend callbacks run serially on this display's event loop. A
            // pause request cannot be acknowledged until this callback returns.
            if(!activate || !activate(request.id,request.output))reject("activation-application-denied");
        }
    }
    void send(wl_resource *r,const Desktop &v,bool initial,const DesktopSnapshot *before=nullptr) {
        const auto version=wl_resource_get_version(r);
        const Desktop *old=nullptr;
        if(before)for(const auto &item:before->desktops)if(item.id==v.id){old=&item;break;}
        if(initial)org_kde_plasma_virtual_desktop_send_desktop_id(r,v.id.c_str());
        if(initial || !old || old->name!=v.name)org_kde_plasma_virtual_desktop_send_name(r,v.name.c_str());
        const auto position=uint32_t(&v-state.desktops.data());
        const auto oldPosition=old?uint32_t(old-before->desktops.data()):UINT32_MAX;
        if(version>=3 && (initial || position!=oldPosition))org_kde_plasma_virtual_desktop_send_position(r,position);
        if(initial || !before || before->current!=state.current){
            if(v.id==state.current)org_kde_plasma_virtual_desktop_send_activated(r);
            else org_kde_plasma_virtual_desktop_send_deactivated(r);
        }
        if(version>=4)for(const auto &output:v.outputs)
            if(initial || !old || std::find(old->outputs.begin(),old->outputs.end(),output)==old->outputs.end())
                org_kde_plasma_virtual_desktop_send_output_entered(r,output.c_str());
        org_kde_plasma_virtual_desktop_send_done(r);
    }
    void request(wl_resource *r,const char *output) {
        const auto i=handles.find(r);if(i==handles.end())return;
        if(!find(i->second.id)){reject("activate-removed-desktop");return;}
        auto *client=wl_resource_get_client(r);auto *owner=peer(client);
        if(!owner || !available || owner->paused){reject("activate-suspended-or-unavailable");return;}
        if(output && !std::any_of(state.desktops.begin(),state.desktops.end(),[&](const auto &v){return std::find(v.outputs.begin(),v.outputs.end(),output)!=v.outputs.end();})){
            reject("activate-unknown-output");return;
        }
        if(queue.size()>=32){reject("activation-queue-full");return;}
        queue.push_back({client,r,i->second.serial,i->second.id,output?output:""});
        if(!idle)idle=wl_event_loop_add_idle(loop,[](void *data){static_cast<Impl*>(data)->drain();},this);
        if(!idle){queue.pop_back();reject("activation-scheduler-unavailable");return;}
        ++accepted;
    }
    static void requestActivate(wl_client *,wl_resource *r){if(auto *p=self(r))p->request(r,nullptr);}
    static void requestOutput(wl_client *,wl_resource *r,const char *output){if(auto *p=self(r))p->request(r,output);}
    static void get(wl_client *client,wl_resource *manager,uint32_t id,const char *desktopId) {
        auto *p=self(manager);if(!p)return;
        if(p->handles.size()>=4096){wl_client_post_no_memory(client);return;}
        auto *r=wl_resource_create(client,&org_kde_plasma_virtual_desktop_interface,wl_resource_get_version(manager),id);
        if(!r){wl_client_post_no_memory(client);return;}
        static const struct org_kde_plasma_virtual_desktop_interface implementation={requestActivate,requestOutput};
        wl_resource_set_implementation(r,&implementation,p,desktopDestroyed);p->handles.emplace(r,Handle{desktopId,p->nextHandle++});
        if(const auto *v=p->find(desktopId))p->send(r,*v,true);
        else {org_kde_plasma_virtual_desktop_send_removed(r);wl_resource_destroy(r);}
    }
    // These are policy requests, not supported operations. The protocol permits
    // denial; diagnostics explicitly exclude creation/removal from capabilities.
    static void create(wl_client *,wl_resource *r,const char *,uint32_t){if(auto *p=self(r))p->reject("create-unsupported");}
    static void remove(wl_client *,wl_resource *r,const char *){if(auto *p=self(r))p->reject("remove-unsupported");}
    static void bind(wl_client *client,void *data,uint32_t version,uint32_t id) {
        auto *p=static_cast<Impl*>(data);
        if(!p->peer(client)){wl_client_post_no_memory(client);return;}
        if(p->managers.size()>=256){wl_client_post_no_memory(client);return;}
        auto *r=wl_resource_create(client,&org_kde_plasma_virtual_desktop_management_interface,std::min(version,4u),id);
        if(!r){wl_client_post_no_memory(client);return;}
        static const struct org_kde_plasma_virtual_desktop_management_interface implementation={get,create,remove};
        wl_resource_set_implementation(r,&implementation,p,managerDestroyed);p->managers.insert(r);
        for(uint32_t i=0;i<p->state.desktops.size();++i)org_kde_plasma_virtual_desktop_management_send_desktop_created(r,p->state.desktops[i].id.c_str(),i);
        if(version>=2)org_kde_plasma_virtual_desktop_management_send_rows(r,p->state.rows);
        org_kde_plasma_virtual_desktop_management_send_done(r);
    }
};
DesktopProtocol::DesktopProtocol(wl_display *display,Activate activate,bool initiallyAvailable):d(std::make_unique<Impl>()) {
    d->activate=std::move(activate);
    d->available=initiallyAvailable;
    if(display){
        d->loop=wl_display_get_event_loop(display);
        d->global=wl_global_create(display,&org_kde_plasma_virtual_desktop_management_interface,4,d.get(),Impl::bind);
        d->controlGlobal=wl_global_create(display,&bwm_plasma_desktop_control_v1_interface,2,d.get(),Impl::bindControl);
    }
}
DesktopProtocol::~DesktopProtocol(){
    if(d->idle)wl_event_source_remove(d->idle);d->queue.clear();
    if(d->controlGlobal)wl_global_destroy(d->controlGlobal);
    if(d->global)wl_global_destroy(d->global);
    for(auto *r:d->managers){wl_resource_set_user_data(r,nullptr);wl_resource_destroy(r);}
    for(const auto &[r,handle]:d->handles){wl_resource_set_user_data(r,nullptr);wl_resource_destroy(r);}
    // Final teardown, not live withdrawal: Hyprland unloads plugins before it
    // destroys clients. Destroy ALL control resources while their callbacks and
    // interface metadata still reside in the loaded module, including retired
    // controls/late binds no longer referenced by Peer::control.
    for(auto *r:d->controls){wl_resource_set_user_data(r,nullptr);wl_resource_destroy(r);}
}
bool DesktopProtocol::valid()const{return !d->withdrawn && d->global && d->controlGlobal;}
uint32_t DesktopProtocol::managementName(wl_client *client)const{return d->global?wl_global_get_name(d->global,client):0;}
uint32_t DesktopProtocol::controlName(wl_client *client)const{return d->controlGlobal?wl_global_get_name(d->controlGlobal,client):0;}
void DesktopProtocol::withdraw(){
    if(d->withdrawn)return;
    setAvailable(false);d->withdrawn=true;
    for(const auto &[client,peer]:d->peers){
        peer->paused=true;
        peer->control=nullptr;
    }
    if(d->controlGlobal)wl_global_remove(d->controlGlobal);
    if(d->global)wl_global_remove(d->global);
}
bool DesktopProtocol::validSnapshot(const DesktopSnapshot &state){
    if(state.desktops.size()>1000 || state.rows==0 || state.rows>1000)return false;
    std::set<std::string> ids,outputs;
    for(const auto &v:state.desktops){
        if(v.id.empty() || v.id.size()>512 || v.name.size()>4096 || v.id.find('\0')!=std::string::npos || v.name.find('\0')!=std::string::npos || !ids.insert(v.id).second)return false;
        for(const auto &output:v.outputs)if(output.empty() || output.size()>512 || output.find('\0')!=std::string::npos || !outputs.insert(output).second)return false;
    }
    if(!state.current.empty() && !ids.contains(state.current))return false;
    return true;
}
bool DesktopProtocol::publish(const DesktopSnapshot &state){
    if(!valid() || !validSnapshot(state))return false;
    if(state==d->state)return true;
    const auto before=std::exchange(d->state,state);
    for(auto *manager:d->managers){
        for(const auto &v:before.desktops)if(!d->find(v.id))org_kde_plasma_virtual_desktop_management_send_desktop_removed(manager,v.id.c_str());
        for(uint32_t i=0;i<state.desktops.size();++i)if(std::none_of(before.desktops.begin(),before.desktops.end(),[&](const auto &v){return v.id==state.desktops[i].id;}))
            org_kde_plasma_virtual_desktop_management_send_desktop_created(manager,state.desktops[i].id.c_str(),i);
        if(wl_resource_get_version(manager)>=2 && before.rows!=state.rows)org_kde_plasma_virtual_desktop_management_send_rows(manager,state.rows);
    }
    std::vector<wl_resource*> removed;
    for(const auto &[r,handle]:d->handles){
        if(const auto *v=d->find(handle.id))d->send(r,*v,false,&before);
        else {org_kde_plasma_virtual_desktop_send_removed(r);removed.push_back(r);}
    }
    for(auto *r:removed)wl_resource_destroy(r);
    for(auto *manager:d->managers)org_kde_plasma_virtual_desktop_management_send_done(manager);
    return true;
}
const DesktopSnapshot &DesktopProtocol::snapshot()const{return d->state;}
uint64_t DesktopProtocol::accepted()const{return d->accepted;}
uint64_t DesktopProtocol::rejected()const{return d->rejected;}
std::string DesktopProtocol::lastRejected()const{return d->lastRejected;}
void DesktopProtocol::setAvailable(bool value){
    if(d->withdrawn && value)return;
    if(d->available==value)return;d->available=value;
    if(!value){d->cancelled+=d->queue.size();d->queue.clear();if(d->idle){wl_event_source_remove(d->idle);d->idle=nullptr;}}
    for(const auto &[client,peer]:d->peers)if(peer->control)bwm_plasma_desktop_control_v1_send_availability(peer->control,value);
}
bool DesktopProtocol::available()const{return d->available;}
size_t DesktopProtocol::pending()const{return d->queue.size();}
uint64_t DesktopProtocol::cancelled()const{return d->cancelled;}
}
