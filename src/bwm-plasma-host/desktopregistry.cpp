// SPDX-License-Identifier: GPL-2.0-or-later
#include "desktopregistry.h"
#include <QGuiApplication>
#include <QHash>
#include <QtGui/qguiapplication_platform.h>
#include <wayland-client.h>
namespace {
// KDE's own QWaylandClientExtension consumers can lose their binding when any
// duplicate interface global is removed. A fresh process is the supported reset.
bool desktopBindingWasAmbiguous=false;
}
struct NativeDesktopRegistry::Wire {
    NativeDesktopRegistry *owner;
    wl_registry *registry=nullptr;
    wl_callback *sync=nullptr;
    struct Global {QByteArray interface;quint32 version;};
    QHash<quint32,Global> globals;
    bool complete=false,overflow=false;
    explicit Wire(NativeDesktopRegistry *o):owner(o){
        auto *native=qGuiApp->nativeInterface<QNativeInterface::QWaylandApplication>();
        auto *display=native?native->display():nullptr;
        if(!display){complete=true;return;}
        registry=wl_display_get_registry(display);if(!registry){complete=true;return;}
        static const wl_registry_listener listener={announced,removed};
        wl_registry_add_listener(registry,&listener,this);
        sync=wl_display_sync(display);if(!sync){complete=true;return;}
        static const wl_callback_listener callback={done};
        wl_callback_add_listener(sync,&callback,this);
        // Nonblocking flush; Qt dispatches its default queue on the GUI thread.
        wl_display_flush(display);
    }
    ~Wire(){if(sync)wl_callback_destroy(sync);if(registry)wl_registry_destroy(registry);}
    static void announced(void *data,wl_registry *,uint32_t name,const char *interface,uint32_t version){
        auto *w=static_cast<Wire*>(data);const QByteArray type(interface);
        if(type!="org_kde_plasma_virtual_desktop_management" && type!="bwm_plasma_desktop_control_v1")return;
        if(w->globals.size()>=64 && !w->globals.contains(name))w->overflow=true;
        else w->globals.insert(name,{type,version});
        if(w->count("org_kde_plasma_virtual_desktop_management")>1)desktopBindingWasAmbiguous=true;
        emit w->owner->changed();
    }
    static void removed(void *data,wl_registry *,uint32_t name){
        auto *w=static_cast<Wire*>(data);if(w->globals.remove(name))emit w->owner->changed();
    }
    static void done(void *data,wl_callback *callback,uint32_t){
        auto *w=static_cast<Wire*>(data);w->sync=nullptr;wl_callback_destroy(callback);w->complete=true;emit w->owner->changed();
    }
    int count(const QByteArray &type)const {int count=0;for(const auto &g:globals)if(g.interface==type)++count;return count;}
};
NativeDesktopRegistry::NativeDesktopRegistry(QObject *parent):QObject(parent),m_wire(std::make_unique<Wire>(this)){}
NativeDesktopRegistry::~NativeDesktopRegistry()=default;
bool NativeDesktopRegistry::complete()const{return m_wire->complete;}
wl_registry *NativeDesktopRegistry::handle()const{return m_wire->registry;}
quint32 NativeDesktopRegistry::controlName()const{
    if(!topologyCompatible())return 0;
    for(auto i=m_wire->globals.cbegin();i!=m_wire->globals.cend();++i)if(i->interface=="bwm_plasma_desktop_control_v1")return i.key();
    return 0;
}
bool NativeDesktopRegistry::controlPresent(quint32 name)const{
    const auto i=m_wire->globals.constFind(name);return i!=m_wire->globals.cend() && i->interface=="bwm_plasma_desktop_control_v1";
}
bool NativeDesktopRegistry::topologyCompatible()const{
    if(!complete() || desktopBindingWasAmbiguous || m_wire->overflow || m_wire->count("org_kde_plasma_virtual_desktop_management")!=1 || m_wire->count("bwm_plasma_desktop_control_v1")!=1)return false;
    for(const auto &g:m_wire->globals)if(g.version<(g.interface=="org_kde_plasma_virtual_desktop_management"?4u:2u))return false;
    return true;
}
bool NativeDesktopRegistry::bindingMatches(quint32 controlName,quint32 managementName)const{
    return topologyCompatible() && associationPresent(controlName,managementName);
}
bool NativeDesktopRegistry::associationPresent(quint32 controlName,quint32 managementName)const{
    const auto control=m_wire->globals.constFind(controlName),management=m_wire->globals.constFind(managementName);
    return control!=m_wire->globals.cend() && management!=m_wire->globals.cend() &&
        control->interface=="bwm_plasma_desktop_control_v1" && management->interface=="org_kde_plasma_virtual_desktop_management";
}
QVariantMap NativeDesktopRegistry::state()const{
    return {{"complete",complete()},{"topologyCompatible",topologyCompatible()},{"overflow",m_wire->overflow},{"restartRequired",desktopBindingWasAmbiguous},
        {"managementGlobals",m_wire->count("org_kde_plasma_virtual_desktop_management")},
        {"controlGlobals",m_wire->count("bwm_plasma_desktop_control_v1")},{"scope","current-wayland-connection-visible-globals"}};
}
