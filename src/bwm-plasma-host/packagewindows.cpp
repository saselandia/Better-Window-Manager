// SPDX-License-Identifier: GPL-2.0-or-later
#include "packagewindows.h"
#include "surfaces.h"
#include <Plasma/Applet>
#include <Plasma/Containment>
#include <PlasmaQuick/AppletQuickItem>
#include <PlasmaQuick/Dialog>
#include <PlasmaQuick/AppletPopup>
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
    QVariantList result;for(const auto &record:m_records)result.append(record);return result;
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
        if(!owner)if(auto *context=qmlContext(quick))owner=context->contextProperty("plasmoid").value<Plasma::Applet*>();
        if(owner && (owner==m_containment || m_containment->applets().contains(owner)))targets.append(quick);
    }
    // A package's onVisibleChanged may destroy another window in the snapshot.
    for(const auto &window:targets)if(window)window->hide();
}
bool PackageWindows::eventFilter(QObject *,QEvent *event) {
    if(event->type()==QEvent::ChildAdded || event->type()==QEvent::Show || event->type()==QEvent::PolishRequest)schedule();
    return false;
}
void PackageWindows::refresh() {
    if(!m_containment)return;
    for(auto *window:QGuiApplication::allWindows()) {
        auto *quick=qobject_cast<QQuickWindow*>(window);
        if(!quick || qobject_cast<PlasmaQuick::AppletPopup*>(quick))continue;
        auto *dialog=qobject_cast<PlasmaQuick::Dialog*>(window);
        // Ownership is determined before considering a role. Other Qt windows,
        // including the configuration host, are never rewritten globally.
        auto *context=qmlContext(quick);
        auto *owner=context ? context->contextProperty("plasmoid").value<Plasma::Applet*>() : nullptr;
        if(!owner || !m_containment->applets().contains(owner))continue;
        auto *item=PlasmaQuick::AppletQuickItem::itemForApplet(owner);
        if(!item || !item->window())continue;
        QVariantMap record{{"appletId",owner->id()},{"package",owner->pluginMetaData().pluginId()},
            {"window",quick->objectName()},{"adapted",false},{"waylandVerified",false}};
        auto *anchor=dialog ? dialog->visualParent() : nullptr;
        const bool requested=!anchor;
        if(!anchor)anchor=item;
        if(!dialog)record["status"]="requires-explicit-window-type-adapter";
        else if(dialog->property("bwmPackageWindowAdapted").toBool()) {
            record["status"]="layer-role-prepared";record["adapted"]=true;
        } else if(!item->window()->property("bwmLayerPanel").toBool())record["status"]="normal-window-preview";
        else if(anchor->window()!=item->window())record["status"]="unsupported-foreign-anchor";
        else if(dialog->isVisible() || dialog->handle())record["status"]="requires-pre-surface-registration";
        else {
            // Notification/OSD/tooltip/output-only Dialogs keep their type, flags and input
            // region (Qt maps WindowTransparentForInput to an empty region); they only get
            // an overlay role without keyboard interactivity instead of an xdg toplevel.
            const bool nonInteractive=dialog->isOutputOnly() || dialog->type()==PlasmaQuick::Dialog::Tooltip
                || dialog->type()==PlasmaQuick::Dialog::Notification || dialog->type()==PlasmaQuick::Dialog::OnScreenDisplay;
            auto *adapter=new PopupAnchor(dialog);
            adapter->setIndependentWindow(true);
            adapter->setNonInteractive(nonInteractive);
            adapter->setUseRequestedPosition(requested);
            adapter->setPopup(dialog);adapter->setVisualParent(anchor);
            dialog->setProperty("bwmPackageWindowAdapted",true);
            dialog->setProperty("bwmPackageWindowNonInteractive",nonInteractive);
            record["status"]="layer-role-prepared";record["adapted"]=true;
        }
        record["nonInteractive"]=dialog && dialog->property("bwmPackageWindowNonInteractive").toBool();
        record["placement"]=requested ? "package-requested-global-position" : "native-visual-parent";
        if(!m_records.contains(quick))connect(quick,&QObject::destroyed,this,[this,quick]{m_records.remove(quick);Q_EMIT changed();});
        if(m_records.value(quick)!=record){m_records.insert(quick,record);Q_EMIT changed();}
    }
}
