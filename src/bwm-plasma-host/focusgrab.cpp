// SPDX-License-Identifier: GPL-2.0-or-later
#include "focusgrab.h"
#include "qwayland-hyprland-focus-grab-v1.h"
#include <QGuiApplication>
#include <QWaylandClientExtensionTemplate>
#include <QWindow>
#include <qpa/qplatformnativeinterface.h>

namespace {
class Manager : public QWaylandClientExtensionTemplate<Manager>, public QtWayland::hyprland_focus_grab_manager_v1 {
public:
    Manager():QWaylandClientExtensionTemplate<Manager>(1){initialize();}
    ~Manager() override{if(isActive())destroy();}
};
Manager *manager() {
    if(!QGuiApplication::platformName().startsWith(QLatin1String("wayland")))return nullptr;
    static Manager *instance=new Manager; // Lives with the Wayland connection of the process.
    return instance->isActive() ? instance : nullptr;
}
wl_surface *surfaceFor(QWindow *window) {
    if(!window || !window->handle() || !window->isVisible())return nullptr;
    auto *native=QGuiApplication::platformNativeInterface();
    return native ? static_cast<wl_surface*>(native->nativeResourceForWindow("surface",window)) : nullptr;
}
}

class FocusGrabClient : public QtWayland::hyprland_focus_grab_v1 {
public:
    FocusGrabClient(::hyprland_focus_grab_v1 *object,FocusGrab *owner):QtWayland::hyprland_focus_grab_v1(object),m_owner(owner){}
    ~FocusGrabClient() override{destroy();}
protected:
    void hyprland_focus_grab_v1_cleared() override{if(m_owner)Q_EMIT m_owner->cleared();}
private:
    QPointer<FocusGrab> m_owner;
};

FocusGrab::FocusGrab(QObject *parent):QObject(parent){}
FocusGrab::~FocusGrab(){stop();}
bool FocusGrab::available(){return manager();}
bool FocusGrab::start(const QList<QWindow*> &windows) {
    stop();
    auto *m=manager();
    if(!m)return false;
    QList<wl_surface*> surfaces;
    for(auto *window:windows)if(auto *surface=surfaceFor(window);surface && !surfaces.contains(surface))surfaces.append(surface);
    if(surfaces.isEmpty())return false;
    m_client=new FocusGrabClient(m->create_grab(),this);
    for(auto *surface:surfaces)m_client->add_surface(surface);
    m_client->commit();
    return true;
}
void FocusGrab::stop(){delete m_client;m_client=nullptr;}
