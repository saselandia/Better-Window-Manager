// SPDX-License-Identifier: GPL-2.0-or-later
#include "workspaces.h"
#include "countmirror.h"
#include "activation.h"
#include <iostream>
#include <stdexcept>
void check(bool condition){if(!condition)throw std::runtime_error("Workspace projection regression");}
int main(int argc,char **argv){
    using namespace BwmPlasma;
    if(argc==3 && std::string_view(argv[1])=="--receipt"){
        CountMirror mirror;const bool accepted=mirror.accept(argv[2]);
        std::cout<<mirror.receipt(accepted)<<'\n';return 0;
    }
    auto s=workspaceSnapshot(3,{{2,"Custom"},{8,"Eight"},{99,"old-minimized"},{-98,"special:minimized",true},{-9,"special:magic",true}},{{"A",1},{"B",8}},"B");
    check(bool(s));check(s->desktops.size()==4);check(s->current=="8");check(s->rows==1);
    check(s->desktops[1].id=="2" && s->desktops[1].name=="Custom");check(s->desktops[3].outputs==std::vector<std::string>{"B"});
    auto unknown=workspaceSnapshot(0,{{7,"Seven"}},{{"A",7}},"missing");check(unknown && unknown->desktops.size()==1 && unknown->current.empty());
    auto high=workspaceSnapshot(100,{},{{"A",99}},"A");check(high && high->desktops.size()==99 && high->current.empty());
    for(const auto &d:high->desktops)check(d.id!="99" && d.id.find("special:")==std::string::npos);
    check(!workspaceSnapshot(2,{{1,"one"},{1,"duplicate"}}, {},""));
    check(!workspaceSnapshot(2,{},{{"A",1},{"A",2}},"A"));
    check(!workspaceSnapshot(2,{},{{"",1}},""));
    CountMirror mirror;check(!mirror.known());
    check(mirror.accept("bwm-plasma-desktops-count 7") && mirror.value()==7 && mirror.revision()==1);
    check(mirror.accept("bwm-plasma-desktops-count 7") && mirror.revision()==1);
    for(const auto &command:{"bwm-plasma-desktops-count 0","bwm-plasma-desktops-count 101","bwm-plasma-desktops-count true",
        "bwm-plasma-desktops-count 7;quit","bwm-plasma-desktops-count 07","bwm-plasma-desktops-count  7","bwm-plasma-desktops-count-other 7"})
        check(!mirror.accept(command) && mirror.value()==7 && mirror.revision()==1);
    check(mirror.accept("bwm-plasma-desktops-count 2") && mirror.value()==2 && mirror.revision()==2);
    const auto retained=workspaceSnapshot(mirror.value(),{{3,"Live Three"},{8,"Live Eight"}},{{"A",8}},"A");
    check(retained && retained->desktops.size()==4 && retained->current=="8");
    ActivationState active{"A",{{"A",1},{"B",2}}};
    int backendCalls=0;bool pretend=false,deny=false,wrongOutput=false,failReadback=false;
    WorkspaceActivator activate([&]()->std::optional<ActivationState>{if(failReadback && backendCalls)return {};return active;},
        [&](const std::string &id,const std::string &output){
            ++backendCalls;if(deny)return false;if(pretend)return true;
            active.focusedOutput=wrongOutput?"A":(output.empty()?active.focusedOutput:output);
            for(auto &o:active.outputs)if(o.name==active.focusedOutput)o.active=std::stoi(id);
            return true;
        });
    check(activate.activate("1","") && backendCalls==0 && activate.noops()==1);
    check(activate.activate("2","B") && backendCalls==1 && activate.outcome()=="applied-verified");
    check(activate.activate("2","B") && backendCalls==1 && activate.noops()==2);
    pretend=true;check(!activate.activate("3","") && activate.outcome()=="activation-readback-mismatch");pretend=false;
    wrongOutput=true;check(!activate.activate("4","B") && activate.outcome()=="activation-readback-mismatch");wrongOutput=false;
    deny=true;check(!activate.activate("5","") && activate.outcome()=="absolute-activation-denied");deny=false;
    const auto dispatched=activate.dispatched();
    for(const auto &id:{"0","99","-1","01","2147483648","1;quit"})check(!activate.activate(id,"") && activate.dispatched()==dispatched);
    check(!activate.activate("5","missing") && activate.dispatched()==dispatched);
    failReadback=true;check(!activate.activate("5","") && activate.outcome()=="activation-state-unavailable");failReadback=false;
    WorkspaceActivator lost([&]()->std::optional<ActivationState>{if(backendCalls==99)return {};return active;},
        [&](const auto &,const auto &){backendCalls=99;return true;});
    check(!lost.activate("6","") && lost.outcome()=="activation-readback-unavailable");
    WorkspaceActivator malformed([]{return std::optional(ActivationState{"A",{{"A",1},{"A",2}}});},{});
    check(!malformed.activate("1","") && malformed.outcome()=="activation-state-unavailable");
    WorkspaceActivator throws([&]{return std::optional(active);},[](const auto &,const auto &)->bool{throw std::runtime_error("fixture");});
    check(!throws.activate("8","") && throws.outcome()=="activation-exception");
    auto overflow=workspaceSnapshot(101,{{INT64_MAX,"invalid"},{1,"one"}}, {},"");check(overflow && overflow->desktops.size()==1);
    std::cout<<"{\"workspaceProjectionPassed\":true,\"specialAndLegacyMinimizedExcluded\":true,\"duplicateBackendRejected\":true}\n";
}
