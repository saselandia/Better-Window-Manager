// SPDX-License-Identifier: GPL-2.0-or-later
// Experimental global on Hyprland's existing display. OFF by default; no loader.
#define WLR_USE_UNSTABLE
#include <hyprland/src/plugins/PluginAPI.hpp>
#include <hyprland/src/Compositor.hpp>
#include <hyprland/src/config/values/types/BoolValue.hpp>
#include <hyprland/src/config/shared/actions/ConfigActions.hpp>
#include <hyprland/src/state/WorkspaceState.hpp>
#include <hyprland/src/state/MonitorState.hpp>
#include <hyprland/src/desktop/state/FocusState.hpp>
#include <hyprland/src/desktop/Workspace.hpp>
#include <hyprland/src/output/Monitor.hpp>
#include <hyprland/src/event/EventBus.hpp>
#include <nlohmann/json.hpp>
#include "provider.h"
#include "workspaces.h"
#include "countmirror.h"
#include "activation.h"
#include <charconv>
#include <map>
#include <memory>
#include <deque>
namespace {
HANDLE handle;
struct Extension {
    SP<Config::Values::CBoolValue> enabled;
    std::unique_ptr<BwmPlasma::DesktopProvider> protocol;
    std::unique_ptr<BwmPlasma::WorkspaceActivator> activator;
    wl_event_source *timer=nullptr,*idle=nullptr;
    CHyprSignalListener active,created,removed,focused,layout;
    SP<SHyprCtlCommand> command,countCommand;
    BwmPlasma::CountMirror countMirror;
    int configuredCount=0;
    uint64_t applied=0,observed=0,failed=0;
    std::string lastError,lastActivationError;
    static int number(const std::string &id){
        int n=0;const auto [end,error]=std::from_chars(id.data(),id.data()+id.size(),n);
        return error==std::errc() && end==id.data()+id.size() && n>0 && n!=99?n:0;
    }
    void schedule(){if(!idle)idle=wl_event_loop_add_idle(g_pCompositor->m_wlEventLoop,[](void *data){
        auto *self=static_cast<Extension*>(data);self->idle=nullptr;self->refresh();
    },this);}
    void refresh(){
        try {
            if(protocol->restartRequired()){protocol->setAvailable(false);return;}
            if(!enabled->value()){
                configuredCount=0;protocol->setAvailable(false);return;
            }
            if(!countMirror.known()){
                configuredCount=0;lastError="awaiting-shared-workspace-count";protocol->setAvailable(false);return;
            }
            BwmPlasma::DesktopSnapshot snapshot;
            configuredCount=countMirror.value();
            if(enabled->value()){
                std::vector<BwmPlasma::Workspace> workspaces;std::vector<BwmPlasma::OutputWorkspace> outputs;
                for(const auto &w:State::workspaceState()->workspaces())if(!w->inert())workspaces.push_back({w->m_id,w->m_name,w->m_isSpecialWorkspace});
                for(const auto &m:State::monitorState()->monitors())if(m->m_activeWorkspace)outputs.push_back({m->m_name,m->m_activeWorkspace->m_id});
                const auto monitor=Desktop::focusState()->monitor();
                auto projected=BwmPlasma::workspaceSnapshot(configuredCount,workspaces,outputs,monitor?monitor->m_name:"");
                if(!projected){lastError="ambiguous-workspace-backend";protocol->setAvailable(false);return;}
                snapshot=std::move(*projected);
            }
            if(!protocol->publish(snapshot)){lastError="invalid-backend-snapshot";protocol->setAvailable(false);return;}
            protocol->setAvailable(true);lastError.clear();
        }catch(...){lastError="backend-snapshot-failed";protocol->setAvailable(false);}
    }
    BwmPlasma::ActivationState activationState(){
        BwmPlasma::ActivationState state;
        const auto focus=Desktop::focusState()->monitor();
        if(focus)state.focusedOutput=focus->m_name;
        for(const auto &m:State::monitorState()->monitors())
            state.outputs.push_back({m->m_name,m->m_activeWorkspace?m->m_activeWorkspace->m_id:0});
        return state;
    }
    bool applyExact(const std::string &id,const std::string &output){
        PHLWORKSPACE workspace;
        for(const auto &w:State::workspaceState()->workspaces())if(w->m_id==number(id)){
            if(w->inert()){lastActivationError="workspace-inert";return false;}
            workspace=w.lock();break;
        }
        if(!output.empty()){
            PHLMONITOR target;
            for(const auto &m:State::monitorState()->monitors())if(m->m_name==output)target=m;
            if(!target || !workspace || workspace->m_monitor!=target){lastActivationError="cross-output-or-unmaterialized-request-denied";return false;}
        }
        if(!workspace){
            const auto focus=Desktop::focusState()->monitor();
            if(!focus){lastActivationError="no-focused-monitor";return false;}
            workspace=State::workspaceState()->create(number(id),focus->m_id,id);
        }
        if(!workspace){lastActivationError="workspace-resolution-failed";return false;}
        // Hyprland's focusMonitor already focuses the active workspace. A
        // second changeWorkspace on that same workspace can simulate pointer
        // movement and refocus the old output (empty target + cursor:no_warps).
        // For inactive workspaces let changeWorkspace own its native cross-
        // output focus path; do not pre-focus and suppress that branch either.
        const auto owner=workspace->m_monitor.lock();
        if(owner && owner->m_activeWorkspace==workspace){
            const auto result=Config::Actions::focusMonitor(owner);
            if(!result)lastActivationError="monitor-focus-failed";
            return bool(result);
        }
        // Object overload is absolute; the string overload consults
        // binds:workspace_back_and_forth and can select a different ID.
        const auto result=Config::Actions::changeWorkspace(workspace);
        if(!result)lastActivationError="workspace-action-failed";
        return bool(result);
    }
    bool apply(const std::string &id,const std::string &output){
        lastActivationError.clear();
        if(!enabled->value() || !protocol->available() || !number(id)){
            ++failed;lastActivationError="provider-disabled-or-invalid-id";return false;
        }
        const bool result=activator->activate(id,output);
        if(result){++observed;if(activator->outcome()=="applied-verified")++applied;}
        else {++failed;if(lastActivationError.empty())lastActivationError=activator->outcome();}
        refresh();return result;
    }
    ~Extension(){
        active.reset();created.reset();removed.reset();focused.reset();layout.reset();
        if(idle)wl_event_source_remove(idle);if(timer)wl_event_source_remove(timer);
        protocol.reset();
        if(command)HyprlandAPI::unregisterHyprCtlCommand(handle,command);
        if(countCommand)HyprlandAPI::unregisterHyprCtlCommand(handle,countCommand);
    }
};
std::unique_ptr<Extension> extension;
}
APICALL EXPORT std::string PLUGIN_API_VERSION(){return HYPRLAND_API_VERSION;}
APICALL EXPORT PLUGIN_DESCRIPTION_INFO PLUGIN_INIT(HANDLE pluginHandle){
    handle=pluginHandle;
    // Both functions return C strings: compare their contents, never the pointers.
    if(std::string{__hyprland_api_get_hash()}!=std::string{__hyprland_api_get_client_hash()})
        throw std::runtime_error("bwm-plasma-desktops: Hyprland headers/runtime mismatch");
    auto pending=std::make_unique<Extension>();auto *e=pending.get();
    e->enabled=makeShared<Config::Values::CBoolValue>("plugin:bwm_plasma_desktops:enabled","Experimental native Plasma desktop provider",false);
    if(!HyprlandAPI::addConfigValueV2(handle,e->enabled))throw std::runtime_error("Cannot register native desktop opt-in");
    e->activator=std::make_unique<BwmPlasma::WorkspaceActivator>([e]{return std::optional(e->activationState());},
        [e](const auto &id,const auto &output){return e->applyExact(id,output);});
    e->protocol=std::make_unique<BwmPlasma::DesktopProvider>(g_pCompositor->m_wlDisplay,[e](const auto &id,const auto &output){return e->apply(id,output);});
    if(!e->protocol->valid())throw std::runtime_error("Cannot initialize native desktop provider observer");
    e->active=Event::bus()->m_events.workspace.active.listen([e](PHLWORKSPACE){e->schedule();});
    e->created=Event::bus()->m_events.workspace.created.listen([e](PHLWORKSPACEREF){e->schedule();});
    e->removed=Event::bus()->m_events.workspace.removed.listen([e](PHLWORKSPACEREF){e->schedule();});
    e->focused=Event::bus()->m_events.monitor.focused.listen([e](PHLMONITOR){e->schedule();});
    e->layout=Event::bus()->m_events.monitor.layoutChanged.listen([e]{e->schedule();});
    e->timer=wl_event_loop_add_timer(g_pCompositor->m_wlEventLoop,[](void *data){auto *self=static_cast<Extension*>(data);self->schedule();wl_event_source_timer_update(self->timer,500);return 0;},e);
    if(!e->timer)throw std::runtime_error("Cannot create desktop reconciliation timer");
    wl_event_source_timer_update(e->timer,500);
    e->command=HyprlandAPI::registerHyprCtlCommand(handle,{.name="bwm-plasma-desktops",.exact=true,.fn=[e](eHyprCtlOutputFormat,std::string){
        return nlohmann::json{{"version",1},{"protocolVersion",4},{"barrierProtocolVersion",2},{"enabled",e->enabled->value()},{"providerAvailable",e->protocol->available()},{"configuredCountAvailable",e->configuredCount>0},
            {"serverArbitrationVersion",1},{"arbitrationState",e->protocol->arbitrationState()},
            {"arbitrationReason",e->protocol->arbitrationReason()},{"providerRestartRequired",e->protocol->restartRequired()},
            {"arbitrationScope","observer-visible-globals"},{"singlePublicationGeneration",true},
            {"observerStartup","deferred-event-loop"},
            {"providerLifecycleVersion",1},
            {"countMirrorVersion",1},{"configuredCount",e->configuredCount},{"countRevision",e->countMirror.revision()},
            {"configuredCountSource","shared-bwm-bridge"},
            {"activationReadbackVersion",1},{"activationRoutingVersion",2},{"observedActivations",e->observed},{"dispatchedActivations",e->activator->dispatched()},
            {"activationNoops",e->activator->noops()},{"lastActivationOutcome",e->activator->outcome()},{"lastActivationError",e->lastActivationError},
            {"desktops",e->protocol->snapshot().desktops.size()},{"current",e->protocol->snapshot().current},
            {"queuedActivations",e->protocol->pending()},{"cancelledActivations",e->protocol->cancelled()},{"perClientBarrierSupported",true},{"acceptedRequests",e->protocol->accepted()},{"rejectedRequests",e->protocol->rejected()},
            {"lastRejectedOperation",e->protocol->lastRejected()},{"appliedActivations",e->applied},{"failedActivations",e->failed},{"lastError",e->lastError},
            {"creationSupported",false},{"removalSupported",false},{"crossOutputRelocationSupported",false},{"liveSessionVerified",false},{"operationalVerified",false}}.dump();
    }});
    if(!e->command)throw std::runtime_error("Cannot register native desktop diagnostics");
    e->countCommand=HyprlandAPI::registerHyprCtlCommand(handle,{.name="bwm-plasma-desktops-count",.exact=false,.fn=[e](eHyprCtlOutputFormat,std::string request){
        if(e->protocol->restartRequired())return std::string("{\"version\":1,\"accepted\":false,\"error\":\"provider-retired\"}");
        const auto revision=e->countMirror.revision();const bool accepted=e->countMirror.accept(request);
        if(accepted && revision!=e->countMirror.revision())e->schedule();
        return e->countMirror.receipt(accepted);
    }});
    if(!e->countCommand)throw std::runtime_error("Cannot register shared workspace count mirror");
    e->refresh();
    extension=std::move(pending);
    return {"bwm-plasma-desktops","Experimental Plasma desktop protocol on the existing compositor display","BWM","0.1"};
}
APICALL EXPORT void PLUGIN_EXIT(){extension.reset();}
