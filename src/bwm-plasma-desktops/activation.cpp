// SPDX-License-Identifier: GPL-2.0-or-later
#include "activation.h"
#include <charconv>
#include <set>
namespace BwmPlasma {
namespace {
bool valid(const ActivationState &s){
    if(s.outputs.size()>256)return false;
    std::set<std::string> names;
    for(const auto &o:s.outputs)
        if(o.name.empty() || o.name.size()>512 || o.name.find('\0')!=std::string::npos || !names.insert(o.name).second)return false;
    return s.focusedOutput.empty() || names.contains(s.focusedOutput);
}
bool observed(const ActivationState &s,int id,const std::string &output){
    if(s.focusedOutput.empty() || (!output.empty() && s.focusedOutput!=output))return false;
    for(const auto &o:s.outputs)if(o.name==s.focusedOutput)return o.active==id;
    return false;
}
}
WorkspaceActivator::WorkspaceActivator(Read read,ApplyExact apply):m_read(std::move(read)),m_apply(std::move(apply)){}
bool WorkspaceActivator::activate(const std::string &id,const std::string &output){
    int number=0;const auto [end,error]=std::from_chars(id.data(),id.data()+id.size(),number);
    if(error!=std::errc() || end!=id.data()+id.size() || number<=0 || number==99 || std::to_string(number)!=id ||
       output.size()>512 || output.find('\0')!=std::string::npos){m_outcome="invalid-activation-request";return false;}
    try {
        const auto before=m_read?m_read():std::nullopt;
        if(!before || !valid(*before)){m_outcome="activation-state-unavailable";return false;}
        if(!output.empty()){
            bool found=false;for(const auto &o:before->outputs)if(o.name==output)found=true;
            if(!found){m_outcome="activation-output-vanished";return false;}
        }
        if(observed(*before,number,output)){++m_noops;m_outcome="already-current";return true;}
        if(!m_apply){m_outcome="absolute-activation-denied";return false;}
        ++m_dispatched;
        if(!m_apply(id,output)){m_outcome="absolute-activation-denied";return false;}
        const auto after=m_read?m_read():std::nullopt;
        if(!after || !valid(*after)){m_outcome="activation-readback-unavailable";return false;}
        if(!observed(*after,number,output)){m_outcome="activation-readback-mismatch";return false;}
        m_outcome="applied-verified";return true;
    }catch(...){m_outcome="activation-exception";return false;}
}
}
