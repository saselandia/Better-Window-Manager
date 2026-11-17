// SPDX-License-Identifier: GPL-2.0-or-later
// TEST ONLY: minimal data-only Wayland display, never an installed/session daemon.
#include "desktops.h"
#ifdef BWM_ARBITRATED_PROVIDER
#include "provider.h"
using TestProtocol=BwmPlasma::DesktopProvider;
#else
using TestProtocol=BwmPlasma::DesktopProtocol;
#endif
#include "plasma-desktops-server.h"
#include "desktop-control-server.h"
#include "countmirror.h"
#include "workspaces.h"
#include "activation.h"
#include "test-xdg-shell-server.h"
#include <wayland-server.h>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <string>
#include <unistd.h>
#ifdef BWM_THUMBNAIL_FIXTURE
#include "thumbnail-server.h"
#endif
namespace {
void destroy(wl_client *,wl_resource *r){wl_resource_destroy(r);}
void regionRect(wl_client *,wl_resource *,int32_t,int32_t,int32_t,int32_t){}
void region(wl_client *c,wl_resource *,uint32_t id){
    auto *r=wl_resource_create(c,&wl_region_interface,1,id);
    static const struct wl_region_interface implementation={destroy,regionRect,regionRect};
    wl_resource_set_implementation(r,&implementation,nullptr,nullptr);
}
void surface(wl_client *,wl_resource *r,uint32_t){wl_resource_post_error(r,0,"Data-only test display does not render surfaces");}
void bindCompositor(wl_client *c,void *,uint32_t version,uint32_t id){
    auto *r=wl_resource_create(c,&wl_compositor_interface,1,id);
    static const struct wl_compositor_interface implementation={surface,region};
    wl_resource_set_implementation(r,&implementation,nullptr,nullptr);
}
void positioner(wl_client *,wl_resource *r,uint32_t){wl_resource_post_error(r,0,"Data-only test display has no positioners");}
void xdgSurface(wl_client *,wl_resource *r,uint32_t,wl_resource *){wl_resource_post_error(r,0,"Data-only test display has no shell surfaces");}
void pong(wl_client *,wl_resource *,uint32_t){}
void bindShell(wl_client *c,void *,uint32_t,uint32_t id){
    auto *r=wl_resource_create(c,&xdg_wm_base_interface,1,id);
    static const struct xdg_wm_base_interface implementation={destroy,positioner,xdgSurface,pong};
    wl_resource_set_implementation(r,&implementation,nullptr,nullptr);
}
struct Output{const char *name;int x;};
void bindOutput(wl_client *c,void *data,uint32_t version,uint32_t id){
    auto *o=static_cast<Output*>(data);auto *r=wl_resource_create(c,&wl_output_interface,std::min(version,4u),id);
    static const struct wl_output_interface implementation={destroy};
    wl_resource_set_implementation(r,&implementation,o,nullptr);
    wl_output_send_geometry(r,o->x,0,520,290,WL_OUTPUT_SUBPIXEL_UNKNOWN,"BWM fixture",o->name,WL_OUTPUT_TRANSFORM_NORMAL);
    wl_output_send_mode(r,WL_OUTPUT_MODE_CURRENT|WL_OUTPUT_MODE_PREFERRED,1920,1080,60000);
    if(version>=2)wl_output_send_scale(r,1);
    if(version>=4){wl_output_send_name(r,o->name);wl_output_send_description(r,o->name);}
    if(version>=2)wl_output_send_done(r);
}
// Test-only alternative globals. They never activate a workspace. The foreign
// control deliberately advertises no association despite claiming availability.
void extraActivate(wl_client *,wl_resource *){}
void extraOutput(wl_client *,wl_resource *,const char *){}
void extraGet(wl_client *c,wl_resource *manager,uint32_t id,const char *){
    auto *r=wl_resource_create(c,&org_kde_plasma_virtual_desktop_interface,wl_resource_get_version(manager),id);
    static const struct org_kde_plasma_virtual_desktop_interface implementation={extraActivate,extraOutput};
    wl_resource_set_implementation(r,&implementation,nullptr,nullptr);
    org_kde_plasma_virtual_desktop_send_removed(r);wl_resource_destroy(r);
}
void extraCreate(wl_client *,wl_resource *,const char *,uint32_t){}
void extraRemove(wl_client *,wl_resource *,const char *){}
void bindExtraDesktop(wl_client *c,void *,uint32_t version,uint32_t id){
    auto *r=wl_resource_create(c,&org_kde_plasma_virtual_desktop_management_interface,std::min(version,4u),id);
    static const struct org_kde_plasma_virtual_desktop_management_interface implementation={extraGet,extraCreate,extraRemove};
    wl_resource_set_implementation(r,&implementation,nullptr,nullptr);
    if(version>=2)org_kde_plasma_virtual_desktop_management_send_rows(r,1);
    org_kde_plasma_virtual_desktop_management_send_done(r);
}
void extraPause(wl_client *,wl_resource *r,uint32_t serial,uint32_t value){bwm_plasma_desktop_control_v1_send_acknowledged(r,serial,value);}
void bindExtraControl(wl_client *c,void *,uint32_t version,uint32_t id){
    auto *r=wl_resource_create(c,&bwm_plasma_desktop_control_v1_interface,std::min(version,2u),id);
    static const struct bwm_plasma_desktop_control_v1_interface implementation={destroy,extraPause};
    wl_resource_set_implementation(r,&implementation,nullptr,nullptr);
    bwm_plasma_desktop_control_v1_send_availability(r,1);
    if(version>=2)bwm_plasma_desktop_control_v1_send_desktop_global(r,0);
}
struct Fixture {
    wl_display *display;
    std::unique_ptr<TestProtocol> protocol;
    std::vector<std::unique_ptr<TestProtocol>> retired;
    BwmPlasma::CountMirror counts;
    std::unique_ptr<BwmPlasma::WorkspaceActivator> activator;
    std::string focusedOutput="r4-output-A";
    bool pretendActivation=false;
    uint64_t activationActions=0;
    std::string commands;
    wl_global *extraDesktop=nullptr,*extraControl=nullptr;
    void retire(){
        if(!protocol)return;
#ifdef BWM_ARBITRATED_PROVIDER
        protocol->setAvailable(false);
#else
        protocol->withdraw();
#endif
        retired.push_back(std::move(protocol));
    }
    void clearExtras(){
        if(extraControl){wl_global_destroy(extraControl);extraControl=nullptr;}
        if(extraDesktop){wl_global_destroy(extraDesktop);extraDesktop=nullptr;}
    }
    bool restore(){
        focusedOutput="r4-output-A";pretendActivation=false;activationActions=0;
        activator=std::make_unique<BwmPlasma::WorkspaceActivator>([this]{
            BwmPlasma::ActivationState state{focusedOutput};
            for(const auto &d:protocol->snapshot().desktops)for(const auto &o:d.outputs)state.outputs.push_back({o,std::stoll(d.id)});
            return std::optional(state);
        },[this](const std::string &id,const std::string &output){
            ++activationActions;if(pretendActivation)return true;
            auto state=protocol->snapshot();const auto name=output.empty()?focusedOutput:output;
            focusedOutput=name;
            for(auto &v:state.desktops){std::erase(v.outputs,name);if(v.id==id)v.outputs.push_back(name);}
            state.current=id;return protocol->publish(state);
        });
        protocol=std::make_unique<TestProtocol>(display,[this](const auto &id,const auto &output){return activator->activate(id,output);});
        const bool published=protocol->publish({{{"1","One",{"r4-output-A"}},{"2","Two",{"r4-output-B"}},{"3","Three",{}}},"1",1});
        protocol->setAvailable(true);return published;
    }
    void command(const std::string &line){
#ifdef BWM_THUMBNAIL_FIXTURE
        if(thumbnailTestCommand(line))return;
#endif
        if(line=="quit"){wl_display_terminate(display);return;}
        if(line=="activation-pretend-on"){pretendActivation=true;return;}
        if(line=="activation-pretend-off"){pretendActivation=false;return;}
        if(line=="activation-status"){
            printf("{\"actions\":%llu,\"pretend\":%s,\"outcome\":\"%s\",\"rejected\":%llu}\n",
                (unsigned long long)activationActions,pretendActivation?"true":"false",activator?activator->outcome().c_str():"",
                (unsigned long long)(protocol?protocol->rejected():0));fflush(stdout);return;
        }
        if(line.starts_with("bwm-plasma-desktops-count")){
            if(!protocol || !counts.accept(line))return;
            const auto current=protocol->snapshot();
            std::vector<BwmPlasma::Workspace> live;std::vector<BwmPlasma::OutputWorkspace> outputs;
            for(const auto &d:current.desktops){
                const auto id=std::stoi(d.id);
                if(id<=3)live.push_back({id,d.name});
                for(const auto &output:d.outputs)outputs.push_back({output,id});
            }
            auto next=BwmPlasma::workspaceSnapshot(counts.value(),live,outputs,focusedOutput);
            if(!next || !protocol->publish(*next))std::abort();return;
        }
        if(line=="extra-desktop"){if(!extraDesktop)extraDesktop=wl_global_create(display,&org_kde_plasma_virtual_desktop_management_interface,4,nullptr,bindExtraDesktop);return;}
        if(line=="extra-control"){if(!extraControl)extraControl=wl_global_create(display,&bwm_plasma_desktop_control_v1_interface,2,nullptr,bindExtraControl);return;}
        if(line=="drop-extras"){clearExtras();return;}
        if(line=="foreign"){retire();clearExtras();extraDesktop=wl_global_create(display,&org_kde_plasma_virtual_desktop_management_interface,4,nullptr,bindExtraDesktop);extraControl=wl_global_create(display,&bwm_plasma_desktop_control_v1_interface,2,nullptr,bindExtraControl);return;}
        if(line=="stall"){
            // Test-only hung-provider simulation. The runner owns stdin and
            // always closes it on failure, so this cannot outlive the fixture.
            printf("stalled\n");fflush(stdout);std::string resume;char c;
            while(read(STDIN_FILENO,&c,1)==1){resume+=c;if(c=='\n'){if(resume=="unstall\n")return;resume.clear();}}
            wl_display_terminate(display);return;
        }
        if(line=="restore" && !protocol){if(!restore())std::abort();return;}
        if(!protocol)return;
        auto s=protocol->snapshot();
        if(line=="shrink"){
            focusedOutput="r4-output-A";
            s.desktops.erase(s.desktops.begin()+2);s.desktops[0].name="Renamed One";
            s.current="1";s.desktops[0].outputs={"r4-output-A"};s.desktops[1].outputs={"r4-output-B"};protocol->publish(s);
        }else if(line=="reorder"){
            std::swap(s.desktops[0],s.desktops[1]);s.rows=2;protocol->publish(s);
        }else if(line=="invalid"){
            s.desktops.push_back(s.desktops.front());if(protocol->publish(s))std::abort();
        }else if(line=="recreate"){
            s.desktops.push_back({"3","New Three",{}});protocol->publish(s);
        }else if(line=="registry-append"){
            s.desktops.push_back({"4","Fourth",{}});if(!protocol->publish(s))std::abort();
            printf("appended\n");fflush(stdout);
        }else if(line=="unavailable")protocol->setAvailable(false);
        else if(line=="available")protocol->setAvailable(true);
        else if(line=="withdraw")retire();
    }
};
int input(int fd,uint32_t,void *data){
    auto *f=static_cast<Fixture*>(data);char buf[256];const auto n=read(fd,buf,sizeof(buf));
    if(n<=0){wl_display_terminate(f->display);return 0;}
    f->commands.append(buf,n);size_t at;
    while((at=f->commands.find('\n'))!=std::string::npos){const auto line=f->commands.substr(0,at);f->commands.erase(0,at+1);f->command(line);}
    return 0;
}
}
int main(int argc,char **argv){
    if(argc!=3)return 10;
    auto *display=wl_display_create();if(!display)return 1;
    if(wl_display_init_shm(display)<0)return 2;
#ifdef BWM_THUMBNAIL_FIXTURE
    createThumbnailTestGlobals(display);
#endif
    wl_global_create(display,&wl_compositor_interface,1,nullptr,bindCompositor);
    wl_global_create(display,&xdg_wm_base_interface,1,nullptr,bindShell);
    Output a{"r4-output-A",0},b{"r4-output-B",1920};
    wl_global_create(display,&wl_output_interface,4,&a,bindOutput);wl_global_create(display,&wl_output_interface,4,&b,bindOutput);
    Fixture fixture{display};
    if(!fixture.restore())return 3;
    if(!wl_client_create(display,std::stoi(argv[1]))){perror("fixture first wl_client_create");return 4;}
    if(!wl_client_create(display,std::stoi(argv[2]))){perror("fixture second wl_client_create");return 4;}
    auto *source=wl_event_loop_add_fd(wl_display_get_event_loop(display),STDIN_FILENO,WL_EVENT_READABLE,input,&fixture);
    printf("ready\n");fflush(stdout);wl_display_run(display);
    wl_event_source_remove(source);
    if(fixture.protocol)printf("{\"accepted\":%llu,\"cancelled\":%llu,\"rejected\":%llu}\n",(unsigned long long)fixture.protocol->accepted(),(unsigned long long)fixture.protocol->cancelled(),(unsigned long long)fixture.protocol->rejected());
    fixture.protocol.reset();fixture.clearExtras();wl_display_destroy_clients(display);fixture.retired.clear();wl_display_destroy(display);
}
