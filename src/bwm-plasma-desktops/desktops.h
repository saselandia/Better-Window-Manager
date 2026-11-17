// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <cstdint>
#include <functional>
#include <memory>
#include <string>
#include <vector>
struct wl_display;
struct wl_client;
namespace BwmPlasma {
struct Desktop {
    std::string id, name;
    std::vector<std::string> outputs;
    bool operator==(const Desktop &) const = default;
};
struct DesktopSnapshot {
    std::vector<Desktop> desktops;
    std::string current;
    uint32_t rows=1;
    bool operator==(const DesktopSnapshot &) const = default;
};
// A global on the caller's existing Wayland display. No socket, thread or daemon.
// Backend snapshots are authoritative: a request never fabricates an event/ack.
class DesktopProtocol {
public:
    using Activate=std::function<bool(const std::string &,const std::string &)>;
    DesktopProtocol(wl_display *display,Activate activate,bool initiallyAvailable=true);
    // Final resource destruction: do not dispatch client requests after this.
    // Use withdraw() and retain this object for a live protocol withdrawal.
    ~DesktopProtocol();
    bool valid() const;
    bool publish(const DesktopSnapshot &snapshot);
    static bool validSnapshot(const DesktopSnapshot &snapshot);
    // Irreversible for this instance. Retain the object while clients may have
    // requests in flight; removed globals and bound resources stay allocated.
    void withdraw();
    uint32_t managementName(wl_client *client)const;
    uint32_t controlName(wl_client *client)const;
    const DesktopSnapshot &snapshot() const;
    uint64_t accepted() const;
    uint64_t rejected() const;
    std::string lastRejected() const;
    void setAvailable(bool available);
    bool available()const;
    size_t pending()const;
    uint64_t cancelled()const;
private:
    struct Impl;
    std::unique_ptr<Impl> d;
};
}
