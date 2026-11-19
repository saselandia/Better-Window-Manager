// SPDX-License-Identifier: GPL-2.0-or-later
#include "viewcorona.h"
#include <Plasma/Containment>
#include <QGuiApplication>
#include <QQuickWindow>
#include <QScreen>
ViewCorona::ViewCorona() {
    for(auto *screen:QGuiApplication::screens())observe(screen);
    for(int i=0;i<numScreens();++i)m_screenIds.insert(QGuiApplication::screens()[i],i);
    connect(qApp,&QGuiApplication::screenAdded,this,[this](QScreen *screen){observe(screen);Q_EMIT screenAdded(QGuiApplication::screens().indexOf(screen));notifyScreens();});
    connect(qApp,&QGuiApplication::screenRemoved,this,[this](QScreen *screen){
        const int previous=m_screenIds.value(screen,-1);if(previous>=0)Q_EMIT screenRemoved(previous);notifyScreens();
    });
}
ViewCorona::~ViewCorona() {
    // Corona destroys its containments in the base destructor, after our map dies.
    for(auto *containment:m_views.keys())forget(containment);
}
int ViewCorona::numScreens()const{return QGuiApplication::screens().size();}
QRect ViewCorona::screenGeometry(int id)const {
    const auto screens=QGuiApplication::screens();
    if(id==-1){QRect full;for(auto *screen:screens)full=full.united(screen->geometry());return full;}
    return id>=0 && id<screens.size() ? screens[id]->geometry() : QRect();
}
QRect ViewCorona::availableScreenRect(int id)const {
    const auto screens=QGuiApplication::screens();
    if(id<0 || id>=screens.size())return {};
    // Qt is the current provider. Do not invent a fixed panel reservation. A later
    // compositor adapter must supply reservations when Qt cannot expose them.
    return screens[id]->availableGeometry();
}
QRegion ViewCorona::availableScreenRegion(int id)const{return availableScreenRect(id);}
int ViewCorona::screenForContainment(const Plasma::Containment *containment)const {
    auto *window=m_views.value(containment).window.data();
    return window ? QGuiApplication::screens().indexOf(window->screen()) : -1;
}
bool ViewCorona::isScreenUiReady(int screen)const {
    if(screen<0 || screen>=numScreens())return false;
    for(auto it=m_views.constBegin();it!=m_views.constEnd();++it) {
        auto *window=it.value().window.data();
        if(!window || QGuiApplication::screens().indexOf(window->screen())!=screen)continue;
        if(!window->isVisible() || !it.key()->isUiReady())return false;
    }
    return true;
}
void ViewCorona::bind(Plasma::Containment *containment,QQuickWindow *window) {
    if(!containment || containment->corona()!=this || !window)return;
    if(m_views.contains(containment) && m_views.value(containment).window==window)return;
    forget(containment);
    Binding binding;binding.window=window;
    binding.containmentDestroyed=connect(containment,&QObject::destroyed,this,[this,containment]{forget(containment);});
    binding.windowDestroyed=connect(window,&QObject::destroyed,this,[this,containment]{forget(containment);containment->reactToScreenChange();});
    binding.screenChanged=connect(window,&QQuickWindow::screenChanged,this,[containment]{containment->reactToScreenChange();});
    m_views.insert(containment,binding);
    containment->reactToScreenChange();
}
void ViewCorona::forget(const Plasma::Containment *containment) {
    const auto binding=m_views.take(containment);
    disconnect(binding.containmentDestroyed);disconnect(binding.windowDestroyed);disconnect(binding.screenChanged);
}
void ViewCorona::unbind(Plasma::Containment *containment) {
    if(!containment || !m_views.contains(containment))return;
    forget(containment);containment->reactToScreenChange();
}
void ViewCorona::observe(QScreen *screen) {
    connect(screen,&QScreen::geometryChanged,this,[this]{notifyScreens();});
    connect(screen,&QScreen::availableGeometryChanged,this,[this]{notifyScreens();});
}
void ViewCorona::notifyScreens() {
    m_screenIds.clear();for(int i=0;i<numScreens();++i)m_screenIds.insert(QGuiApplication::screens()[i],i);
    for(int i=0;i<numScreens();++i) {
        Q_EMIT screenGeometryChanged(i);Q_EMIT availableScreenRectChanged(i);Q_EMIT availableScreenRegionChanged(i);
    }
    for(auto it=m_views.cbegin();it!=m_views.cend();++it)const_cast<Plasma::Containment*>(it.key())->reactToScreenChange();
}
