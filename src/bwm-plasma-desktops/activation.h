// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include "workspaces.h"
#include <functional>
namespace BwmPlasma {
struct ActivationState {
    std::string focusedOutput;
    std::vector<OutputWorkspace> outputs;
};
// The callback MUST apply an absolute ID, never a toggle/back-and-forth string.
// Reads are fresh backend observations, not the published/cached desktop model.
class WorkspaceActivator {
public:
    using Read=std::function<std::optional<ActivationState>()>;
    using ApplyExact=std::function<bool(const std::string &,const std::string &)>;
    WorkspaceActivator(Read read,ApplyExact apply);
    bool activate(const std::string &id,const std::string &output);
    const std::string &outcome()const{return m_outcome;}
    uint64_t dispatched()const{return m_dispatched;}
    uint64_t noops()const{return m_noops;}
private:
    Read m_read;ApplyExact m_apply;
    std::string m_outcome;
    uint64_t m_dispatched=0,m_noops=0;
};
}
