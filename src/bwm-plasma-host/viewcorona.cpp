// SPDX-License-Identifier: GPL-2.0-or-later
#include "viewcorona.h"
#include <Plasma/Containment>
#include <QAction>
#include <QGuiApplication>
#include <QIcon>
#include <QMenu>
#include <QQuickWindow>
#include <QScreen>
ViewCorona::ViewCorona() {
    for(auto *screen:QGuiApplication::screens())observe(screen);
    for(int i=0;i<numScreens();++i)m_screenIds.insert(QGuiApplication::screens()[i],i);
    connect(qApp,&QGuiApplication::screenAdded,this,[this](QScreen *screen){observe(screen);Q_EMIT screenAdded(QGuiApplication::screens().indexOf(screen));notifyScreens();});
    connect(qApp,&QGuiApplication::screenRemoved,this,[this](QScreen *screen){
        m_availableRects.remove(screen);
        const int previous=m_screenIds.value(screen,-1);if(previous>=0)Q_EMIT screenRemoved(previous);notifyScreens();
    });
    // ShellCorona 6.7.5 registers "add panel" and "edit mode" on the Corona action collection;
    // DesktopEditMode.qml reads "add panel" and org.kde.contextmenu reads "edit mode".
    auto *addPanel=new QAction(QIcon::fromTheme(QStringLiteral("list-add")),tr("Add Panel"),this);
    setAction(QStringLiteral("add panel"),addPanel);
    auto *editAction=new QAction(QIcon::fromTheme(QStringLiteral("document-edit")),tr("Enter Edit Mode"),this);
    editAction->setCheckable(true);
    connect(editAction,&QAction::triggered,this,[this](bool checked){
        if(checked)setEnteredEditModeViaDesktop(true);
        setEditMode(checked);
    });
    connect(this,&Plasma::Corona::editModeChanged,this,[this,editAction](bool edit){
        editAction->setChecked(edit);
        editAction->setText(edit ? tr("Exit Edit Mode") : tr("Enter Edit Mode"));
        if(!edit)setEnteredEditModeViaDesktop(false);
    });
    setAction(QStringLiteral("edit mode"),editAction);
}
ViewCorona::~ViewCorona() {
    delete m_addPanelMenu.data();
    // Corona destroys its containments in the base destructor, after our map dies.
    for(auto *containment:m_views.keys())forget(containment);
}
void ViewCorona::setEnteredEditModeViaDesktop(bool viaDesktop) {
    if(m_enteredEditModeViaDesktop==viaDesktop)return;
    m_enteredEditModeViaDesktop=viaDesktop;
    Q_EMIT enteredEditModeViaDesktopChanged();
}
void ViewCorona::setPanelBeingConfigured(QObject *panel) {
    if(m_panelBeingConfigured==panel)return;
    m_panelBeingConfigured=panel;
    Q_EMIT panelBeingConfiguredChanged();
}
QMenu *ViewCorona::addPanelMenu()const{return m_addPanelMenu.data();}
void ViewCorona::showAddPanelContextMenu(const QPoint &pos) {
    if(immutability()!=Plasma::Types::Mutable)return;
    delete m_addPanelMenu.data();
    QScreen *target=QGuiApplication::screenAt(pos);
    if(!target)target=QGuiApplication::primaryScreen();
    auto *menu=new QMenu();
    menu->setAttribute(Qt::WA_DeleteOnClose);
    auto *defaultPanel=menu->addAction(QIcon::fromTheme(QStringLiteral("list-add")),tr("Default Panel"));
    defaultPanel->setObjectName(QStringLiteral("org.kde.plasma.desktop.defaultPanel"));
    connect(defaultPanel,&QAction::triggered,this,[this,target]{
        Q_EMIT addPanelRequested(QStringLiteral("org.kde.plasma.desktop.defaultPanel"),target);
    });
    auto *emptyPanel=menu->addAction(QIcon::fromTheme(QStringLiteral("list-add")),tr("Empty Panel"));
    emptyPanel->setObjectName(QStringLiteral("org.kde.plasma.desktop.emptyPanel"));
    connect(emptyPanel,&QAction::triggered,this,[this,target]{
        Q_EMIT addPanelRequested(QStringLiteral("org.kde.plasma.desktop.emptyPanel"),target);
    });
    m_addPanelMenu=menu;
    menu->popup(pos);
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
    auto *screen=screens[id];
    const QRect published=m_availableRects.value(screen);
    if(published.isValid() && !published.isEmpty() && screen->geometry().contains(published))return published;
    return screen->availableGeometry();
}
QRegion ViewCorona::availableScreenRegion(int id)const{return availableScreenRect(id);}
void ViewCorona::setScreenAvailableRect(QScreen *screen,const QRect &rect) {
    if(!screen)return;
    const QRect previous=m_availableRects.value(screen);
    const QRect next=(rect.isValid() && !rect.isEmpty() && screen->geometry().contains(rect)) ? rect : QRect();
    if(previous==next)return;
    if(next.isValid())m_availableRects.insert(screen,next);
    else m_availableRects.remove(screen);
    const int id=QGuiApplication::screens().indexOf(screen);
    if(id>=0){Q_EMIT availableScreenRectChanged(id);Q_EMIT availableScreenRegionChanged(id);}
}
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
