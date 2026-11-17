// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include "desktops.h"
namespace BwmPlasma {
// Same-display observer, not a server/daemon. All methods run on the server loop.
// The internal peer/deadline are created in an idle only after snapshot + opt-in.
// One publication generation per lifetime: withdrawal requires a fresh session.
class DesktopProvider {
public:
    DesktopProvider(wl_display *display,DesktopProtocol::Activate activate);
    ~DesktopProvider();
    bool valid()const;
    bool publish(const DesktopSnapshot &snapshot);
    void setAvailable(bool requested);
    bool available()const;
    const DesktopSnapshot &snapshot()const;
    std::string arbitrationState()const;
    std::string arbitrationReason()const;
    bool restartRequired()const;
    uint64_t accepted()const;
    uint64_t rejected()const;
    std::string lastRejected()const;
    size_t pending()const;
    uint64_t cancelled()const;
private:
    struct Impl;
    std::unique_ptr<Impl> d;
};
}
