// SPDX-License-Identifier: GPL-2.0-or-later
#include "packagewindows.h"
#include "surfaces.h"
#include <Plasma/Applet>
#include <Plasma/Containment>
#include <PlasmaQuick/AppletQuickItem>
#include <PlasmaQuick/Dialog>
#include <PlasmaQuick/AppletPopup>
#include <PlasmaQuick/PopupPlasmaWindow>
#include <QPlatformSurfaceEvent>
#include <LayerShellQt/Window>
#include <QQmlContext>
#include <QGuiApplication>
#include <QEvent>
#include <QTimer>

PackageWindows::PackageWindows(Plasma::Containment *containment,QObject *parent)
    :QObject(parent),m_containment(containment) {
    qApp->installEventFilter(this);schedule();
    connect(containment,&Plasma::Containment::appletAdded,this,[this]{schedule();});
}
QVariantList PackageWindows::capabilities()const {
    QVariantList result;
    for(auto it=m_records.cbegin();it!=m_records.cend();++it){
        auto record=it.value();record["visible"]=it.key()->isVisible();
        record["popupRect"]=it.key()->property("bwmPopupRect");
        record["rolePreparedAtSurfaceCreation"]=it.key()->property("bwmPackageRoleAtSurfaceCreation").toBool();
        result.append(record);
    }
    return result;
}
void PackageWindows::schedule() {
    if(m_scheduled)return;m_scheduled=true;
    QTimer::singleShot(0,this,[this]{m_scheduled=false;refresh();});
}
void PackageWindows::suspend() {
    if(!m_containment)return;
    QList<QPointer<Plasma::Applet>> applets;for(auto *applet:m_containment->applets())applets.append(applet);
    for(const auto &applet:applets)if(applet)if(auto *item=PlasmaQuick::AppletQuickItem::itemForApplet(applet))item->setProperty("expanded",false);
    if(!m_containment)return;
    QList<QPointer<QQuickWindow>> targets;
    for(auto *window:QGuiApplication::allWindows()) {
        auto *quick=qobject_cast<QQuickWindow*>(window);if(!quick)continue;
        Plasma::Applet *owner=nullptr;
        if(auto *popup=qobject_cast<PlasmaQuick::AppletPopup*>(quick)) {
            auto *item=qobject_cast<PlasmaQuick::AppletQuickItem*>(popup->appletInterface());if(item)owner=item->applet();
        }
        if(!owner)if(auto *popup=qobject_cast<PlasmaQuick::PopupPlasmaWindow*>(quick)) {
            for(auto *anchor=popup->visualParent();anchor;anchor=anchor->parentItem())
                if(auto *item=qobject_cast<PlasmaQuick::AppletQuickItem*>(anchor)){owner=item->applet();break;}
        }
        if(!owner)if(auto *context=qmlContext(quick))owner=context->contextProperty("plasmoid").value<Plasma::Applet*>();
        if(owner && (owner==m_containment || m_containment->applets().contains(owner)))targets.append(quick);
    }
    // A package's onVisibleChanged may destroy another window in the snapshot.
    for(const auto &window:targets)if(window)window->hide();
}
namespace {
Plasma::Applet *visualOwner(QQuickItem *anchor){
    for(auto *item=anchor;item;item=item->parentItem())
        if(auto *applet=qobject_cast<PlasmaQuick::AppletQuickItem*>(item))return applet->applet();
    return nullptr;
}
}
bool PackageWindows::eventFilter(QObject *object,QEvent *event) {
    // PopupPlasmaWindow/ToolTipDialog can be created and shown in one C++ call,
    // without a QML context. SurfaceCreated precedes QWaylandWindow::setVisible
    // and its shell-role selection in Qt 6.11.2. LayerShellQt supports assigning
    // its integration at this boundary through its public Window API.
    if(event->type()==QEvent::PlatformSurface &&
       static_cast<QPlatformSurfaceEvent*>(event)->surfaceEventType()==QPlatformSurfaceEvent::SurfaceCreated){
        if(auto *popup=qobject_cast<PlasmaQuick::PopupPlasmaWindow*>(object))prepare(popup,true);
    }
    if(event->type()==QEvent::ChildAdded || event->type()==QEvent::Show || event->type()==QEvent::PolishRequest)schedule();
    return false;
}
void PackageWindows::refresh() {
    if(!m_containment)return;
    for(auto *window:QGuiApplication::allWindows())if(auto *quick=qobject_cast<QQuickWindow*>(window))prepare(quick);
}
void PackageWindows::prepare(QQuickWindow *quick,bool creatingSurface) {
    if(!m_containment || !quick || qobject_cast<PlasmaQuick::AppletPopup*>(quick))return;
    auto *dialog=qobject_cast<PlasmaQuick::Dialog*>(quick);
    auto *popup=qobject_cast<PlasmaQuick::PopupPlasmaWindow*>(quick);
    if(popup && !m_observedPopups.contains(quick)){
        m_observedPopups.insert(quick);
        connect(popup,&PlasmaQuick::PopupPlasmaWindow::visualParentChanged,this,[this,popup]{prepare(popup);});
        connect(popup,&QObject::destroyed,this,[this,quick]{m_observedPopups.remove(quick);});
    }
    auto *anchor=popup?popup->visualParent():dialog?dialog->visualParent():nullptr;
    // If the shared tooltip moves into an ordinary configuration window, restore
    // its original backend. A Wayland role cannot be changed on a mapped surface.
    if(popup && anchor && anchor->window() && !anchor->window()->property("bwmLayerPanel").toBool() &&
       quick->property("bwmPackageWindowAdapted").toBool()){
        const bool visible=quick->isVisible();quick->hide();quick->destroy();
        delete quick->findChild<PopupAnchor*>(QStringLiteral("bwmPackagePopupAnchor"),Qt::FindDirectChildrenOnly);
        delete LayerShellQt::Window::get(quick);
        quick->setProperty("bwmPackageWindowAdapted",false);
        quick->setProperty("bwmPackageWindowNonInteractive",false);
        quick->setProperty("bwmPopupRect",QVariant());
        if(visible)quick->show();
    }
    // The current visual owner wins for a C++ shared tooltip, which is reused
    // across applets/containments. Never infer ownership from process/window title.
    auto *context=qmlContext(quick);
    auto *owner=popup?visualOwner(anchor):context?context->contextProperty("plasmoid").value<Plasma::Applet*>():nullptr;
    // R5: the panel containment's own popups (ConfigOverlay's handle popup, the paneltoolbox
    // tooltip) are anchored to items of the panel window: they need the same layer role,
    // or they map as ordinary toplevels away from the panel. Only by visual anchor: windows
    // whose QML context merely names the containment (Panel Settings) keep their own owner.
    const bool containmentPopup=popup && anchor && owner==m_containment;
    if(!owner || !(containmentPopup || m_containment->applets().contains(owner))){
        if(m_records.remove(quick))Q_EMIT changed();return;
    }
    auto *item=PlasmaQuick::AppletQuickItem::itemForApplet(owner);
    if(!item || !item->window())return;
    QVariantMap record{{"appletId",owner->id()},{"package",owner->pluginMetaData().pluginId()},
        {"window",quick->objectName()},{"windowClass",quick->metaObject()->className()},
        {"adapted",false},{"waylandVerified",false}};
    const bool requested=!anchor;
    if(!anchor)anchor=item;
    auto *adapter=quick->findChild<PopupAnchor*>(QStringLiteral("bwmPackagePopupAnchor"),Qt::FindDirectChildrenOnly);
    if(popup && !adapter && !creatingSurface && quick->property("bwmPackagePopupManaged").toBool() &&
       item->window()->property("bwmLayerPanel").toBool() && anchor->window()==item->window() &&
       (quick->isVisible() || quick->handle())){
        const bool visible=quick->isVisible();quick->hide();quick->destroy();
        prepare(quick);if(visible)quick->show();return;
    }
    if(!dialog && !popup)record["status"]="requires-explicit-window-type-adapter";
    else if(!item->window()->property("bwmLayerPanel").toBool())record["status"]="normal-window-preview";
    else if(anchor->window()!=item->window())record["status"]="unsupported-foreign-anchor";
    else if(!adapter && !creatingSurface && (quick->isVisible() || quick->handle()))record["status"]="requires-pre-surface-registration";
    else {
        const bool nonInteractive=popup?quick->flags().testFlag(Qt::WindowDoesNotAcceptFocus):
            dialog->isOutputOnly() || dialog->type()==PlasmaQuick::Dialog::Tooltip ||
            dialog->type()==PlasmaQuick::Dialog::Notification || dialog->type()==PlasmaQuick::Dialog::OnScreenDisplay;
        if(!adapter){
            adapter=new PopupAnchor(quick);adapter->setObjectName("bwmPackagePopupAnchor");
            adapter->setIndependentWindow(true);
            adapter->setNonInteractive(nonInteractive);
            adapter->setUseRequestedPosition(requested);
            adapter->setVisualParent(anchor);adapter->setPopup(quick);
            quick->setProperty("bwmPackageWindowAdapted",true);
            if(popup)quick->setProperty("bwmPackagePopupManaged",true);
            quick->setProperty("bwmPackageWindowNonInteractive",nonInteractive);
            quick->setProperty("bwmPackageRoleAtSurfaceCreation",creatingSurface);
        } else adapter->setVisualParent(anchor);
        record["status"]="layer-role-prepared";record["adapted"]=true;
    }
    record["nonInteractive"]=quick->property("bwmPackageWindowNonInteractive").toBool();
    record["placement"]=requested ? "package-requested-global-position" : "native-visual-parent";
    if(!m_trackedWindows.contains(quick)){
        m_trackedWindows.insert(quick);
        connect(quick,&QObject::destroyed,this,[this,quick]{m_trackedWindows.remove(quick);m_records.remove(quick);Q_EMIT changed();});
    }
    if(m_records.value(quick)!=record){m_records.insert(quick,record);Q_EMIT changed();}
}
