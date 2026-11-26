// SPDX-License-Identifier: GPL-2.0-or-later
#include "focusgrab.h"
#include "qwayland-hyprland-focus-grab-v1.h"
#include <QGuiApplication>
#include <QWaylandClientExtensionTemplate>
#include <QWindow>
#include <QPlatformSurfaceEvent>
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
    if(!window || !window->handle() || !window->isVisible() || !window->isExposed())return nullptr;
    auto *native=QGuiApplication::platformNativeInterface();
    return native ? static_cast<wl_surface*>(native->nativeResourceForWindow("surface",window)) : nullptr;
}
}

class FocusGrabClient : public QtWayland::hyprland_focus_grab_v1 {
public:
    FocusGrabClient(::hyprland_focus_grab_v1 *object,FocusGrab *owner):QtWayland::hyprland_focus_grab_v1(object),m_owner(owner){}
    ~FocusGrabClient() override{destroy();}
protected:
    void hyprland_focus_grab_v1_cleared() override{
        const QPointer<FocusGrab> owner=m_owner;
        if(owner){owner->stop();Q_EMIT owner->cleared();}
    }
private:
    QPointer<FocusGrab> m_owner;
};

FocusGrab::FocusGrab(QObject *parent):QObject(parent){}
FocusGrab::~FocusGrab(){stop();}
bool FocusGrab::available(){return manager();}
bool FocusGrab::start(const QList<QWindow*> &windows) {
    stop();
    auto *m=manager();
    if(!m || windows.isEmpty() || !windows.first() || windows.first()->flags().testFlag(Qt::WindowDoesNotAcceptFocus))return false;
    QList<wl_surface*> surfaces;
    for(auto *window:windows) {
        auto *surface=surfaceFor(window);
        if(!surface)return false; // Never silently commit a partial whitelist.
        if(!surfaces.contains(surface))surfaces.append(surface);
    }
    m_client=new FocusGrabClient(m->create_grab(),this);
    // Hyprland 0.56.2 CFocusGrab::refocusKeyboard gives the keyboard to the first committed
    // surface of an unordered map when the focused one is not whitelisted. With the panel in
    // the same commit it could pick the panel: Qt then reports the panel view as the focus
    // window and PopupPlasmaWindow hides the popup it just opened (launcher closing at once).
    // Commit the destination alone first, so refocusKeyboard can only choose it; the next
    // commit finds that surface focused and committed and keeps it.
    m_client->add_surface(surfaces.first());
    m_client->commit();
    if(surfaces.size()>1) {
        for(int i=1;i<surfaces.size();++i)m_client->add_surface(surfaces.at(i));
        m_client->commit();
    }
    for(auto *window:windows) {
        if(m_windows.contains(window))continue;
        m_windows.append(window);
        window->installEventFilter(this);
        m_connections.append(connect(window,&QWindow::visibleChanged,this,[this](bool visible){if(!visible)stop();}));
        m_connections.append(connect(window,&QObject::destroyed,this,[this]{stop();}));
    }
    return true;
}
void FocusGrab::stop(){
    for(const auto &connection:m_connections)disconnect(connection);
    m_connections.clear();
    for(const auto &window:m_windows)if(window)window->removeEventFilter(this);
    m_windows.clear();
    delete m_client;m_client=nullptr;
}
bool FocusGrab::eventFilter(QObject *,QEvent *event){
    if(event->type()==QEvent::Hide || (event->type()==QEvent::PlatformSurface &&
       static_cast<QPlatformSurfaceEvent*>(event)->surfaceEventType()==QPlatformSurfaceEvent::SurfaceAboutToBeDestroyed))stop();
    return false;
}
