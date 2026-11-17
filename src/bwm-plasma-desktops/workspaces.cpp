// SPDX-License-Identifier: GPL-2.0-or-later
#include "workspaces.h"
#include <map>
#include <set>
namespace BwmPlasma {
std::optional<DesktopSnapshot> workspaceSnapshot(int count,const std::vector<Workspace> &workspaces,
    const std::vector<OutputWorkspace> &outputs,const std::string &focusedOutput){
    const auto normal=[](int64_t id){return id>0 && id!=99 && id<=INT32_MAX;};
    std::map<int64_t,Desktop> desktops;
    if(count>=1 && count<=100)for(int i=1;i<=count;++i)if(normal(i))desktops.emplace(i,Desktop{std::to_string(i),std::to_string(i),{}});
    std::set<int64_t> live;
    for(const auto &w:workspaces)if(!w.special && normal(w.id)){
        if(!live.insert(w.id).second)return {};
        desktops[w.id]={std::to_string(w.id),w.name,{}};
    }
    DesktopSnapshot result;std::set<std::string> names;
    for(const auto &o:outputs){
        if(o.name.empty() || !names.insert(o.name).second)return {};
        if(!normal(o.active))continue;
        auto [it,inserted]=desktops.try_emplace(o.active,Desktop{std::to_string(o.active),std::to_string(o.active),{}});
        it->second.outputs.push_back(o.name);
        if(o.name==focusedOutput)result.current=std::to_string(o.active);
    }
    for(auto &[id,d]:desktops)result.desktops.push_back(std::move(d));
    return result;
}
}
