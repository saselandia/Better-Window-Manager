// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include "desktops.h"
#include <optional>
namespace BwmPlasma {
struct Workspace {int64_t id;std::string name;bool special=false;};
struct OutputWorkspace {std::string name;int64_t active;};
// Shared BWM IDs; this is a projection, never a new layout/configuration manager.
std::optional<DesktopSnapshot> workspaceSnapshot(int configuredCount,const std::vector<Workspace> &workspaces,
    const std::vector<OutputWorkspace> &outputs,const std::string &focusedOutput);
}
