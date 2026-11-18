// SPDX-License-Identifier: GPL-2.0-or-later
#include "panelsession.h"
#include "configurationsession.h"
#include "packagewindows.h"
#include "catalog.h"
#include "taskbridge.h"
#include <Plasma/Containment>
#include <Plasma/Applet>
#include <PlasmaQuick/ConfigView>
#include <PlasmaQuick/AppletQuickItem>
#include <KConfigLoader>
#include <QAction>
#include <QMenu>
#include <QMetaMethod>
#include <functional>
#include <limits>
#include <cmath>

namespace {
Plasma::Containment *systemTray(Plasma::Applet *applet) {
    if (applet->pluginMetaData().pluginId() != QStringLiteral("org.kde.plasma.systemtray")) return nullptr;
    auto *tray = qobject_cast<Plasma::Containment *>(applet);
    return tray && tray->containmentType() == Plasma::Containment::CustomEmbedded ? tray : nullptr;
}

QVariantMap backendRow(Plasma::Applet *applet) {
    auto assessment = Catalog::runtimeAssessment(applet->pluginMetaData());
    if (applet->failedToLaunch()) assessment["status"] = "launch-failed";
    return {{"id", applet->id()}, {"package", applet->pluginMetaData().pluginId()},
            {"failedToLaunch", applet->failedToLaunch()}, {"launchError", applet->launchErrorMessage()},
            {"runtime", assessment}};
}
}

PanelSession::PanelSession(Plasma::Containment *containment,bool connectConfiguration):m_containment(containment),m_packageWindows(new PackageWindows(containment,this)) {
    if(connectConfiguration)connect(containment,&Plasma::Containment::configureRequested,this,&PanelSession::openConfiguration);
    m_notify.setSingleShot(true);m_notify.setInterval(0);
    connect(&m_notify,&QTimer::timeout,this,&PanelSession::changed);
    connect(containment,&Plasma::Containment::appletsChanged,this,[this]{
        if(m_containment)for(auto *a:m_containment->applets())watchApplet(a);
        m_notify.start();
    });
    connect(containment,&Plasma::Applet::configNeedsSaving,&m_notify,qOverload<>(&QTimer::start));
    connect(containment,&Plasma::Containment::locationChanged,&m_notify,qOverload<>(&QTimer::start));
    connect(containment,&Plasma::Containment::formFactorChanged,&m_notify,qOverload<>(&QTimer::start));
    watchApplet(containment);
    for(auto *a:containment->applets())watchApplet(a);
}
void PanelSession::setError(const QString &error) {if(m_error!=error){m_error=error;emit errorChanged();}}
Plasma::Applet *PanelSession::findApplet(uint id) const {
    if(!m_containment || m_containment->destroyed())return nullptr;
    if(m_containment->id()==id)return m_containment;
    for(auto *a:m_containment->applets())if(a->id()==id && !a->destroyed())return a;
    return nullptr;
}
void PanelSession::watchApplet(Plasma::Applet *applet) {
    const uint id=applet->id();
    if(m_watched.contains(id))return;
    m_watched.insert(id);
    connect(applet,&QObject::destroyed,this,[this,id]{
        m_watched.remove(id);delete m_sessions.take(id).data();
        for(auto it=m_actions.begin();it!=m_actions.end();) {
            if(!it->applet || it->applet->id()==id)it=m_actions.erase(it);else ++it;
        }
        m_notify.start();
    });
    connect(applet,&Plasma::Applet::titleChanged,&m_notify,qOverload<>(&QTimer::start));
    connect(applet,&Plasma::Applet::iconChanged,&m_notify,qOverload<>(&QTimer::start));
    connect(applet,&Plasma::Applet::immutabilityChanged,&m_notify,qOverload<>(&QTimer::start));
    connect(applet,&Plasma::Applet::destroyedChanged,this,[this,id](bool removed){
        if(removed)delete m_sessions.take(id).data();
        m_notify.start();
    });
    connect(applet,&Plasma::Applet::contextualActionsChanged,this,[this,id]{emit actionsChanged(id);});
    if (auto *tray = systemTray(applet)) {
        const auto watchChildren = [this, tray] {
            for (auto *child : tray->applets()) watchApplet(child);
            m_notify.start();
        };
        connect(tray, &Plasma::Containment::appletsChanged, this, watchChildren);
        watchChildren();
    }
}
void PanelSession::bindPanelItem(PlasmaQuick::AppletQuickItem *item) {
    if(!m_containment || !item || item->applet()!=m_containment){setError(tr("The view does not belong to this containment."));return;}
    if(m_panelItem!=item) {
        if(m_panelItem)disconnect(m_panelItem,&QObject::destroyed,&m_notify,nullptr);
        m_panelItem=item;
        connect(item,&QObject::destroyed,&m_notify,qOverload<>(&QTimer::start));
    }
    m_notify.start();setError({});
    BwmTaskBridge::attachEnabled(item);
}
QVariantMap PanelSession::panelInfo() const {
    if(!m_containment || m_containment->destroyed())return {};
    bool mutableWidgets=true;for(auto *a:m_containment->applets())if(!a->destroyed() && a->immutable())mutableWidgets=false;
    return {{"id",m_containment->id()},{"package",m_containment->pluginMetaData().pluginId()},
        {"location",int(m_containment->location())},{"formFactor",int(m_containment->formFactor())},
        {"immutable",m_containment->immutable()},{"viewBound",bool(m_panelItem)},
        {"canReorder",m_panelItem && !m_containment->immutable() && mutableWidgets && m_panelItem->metaObject()->indexOfMethod("reorderApplets(QVariant)")>=0},
        {"runtimeVerified",false}};
}
QVariantList PanelSession::order() const {
    if(!m_containment)return {};
    QHash<uint,Plasma::Applet*> live;
    for(auto *a:m_containment->applets())if(!a->destroyed())live.insert(a->id(),a);
    QVariantList ids;
    if(auto *scheme=m_containment->configScheme()) {
        if(auto *entry=scheme->KCoreConfigSkeleton::findItem("AppletOrder")) {
            for(const auto &text:entry->property().toString().split(';',Qt::SkipEmptyParts)) {
                bool ok=false;const uint id=text.toUInt(&ok);
                if(ok && live.remove(id))ids.append(id);
            }
        }
    }
    // A just-added applet may not be in AppletOrder until the native callLater(save).
    for(auto *a:m_containment->applets())if(live.contains(a->id()))ids.append(a->id());
    return ids;
}
QVariantList PanelSession::widgets() const {
    QVariantList result;
    for(const auto &id:order())if(auto *a=findApplet(id.toUInt()))
        result.append(QVariantMap{{"id",a->id()},{"package",a->pluginMetaData().pluginId()},
            {"title",a->title()},{"icon",a->icon()},{"immutable",a->immutable()},
            {"failedToLaunch",a->failedToLaunch()},{"launchError",a->launchErrorMessage()}});
    return result;
}
QVariantList PanelSession::widgetBackends() const {
    QVariantList result;
    // Use live instances, not a fresh global catalog lookup: two copies of one
    // package remain distinct, and removed widgets disappear on the next query.
    for(const auto &id:order())if(auto *a=findApplet(id.toUInt())) {
        auto row = backendRow(a);
        if (auto *tray = systemTray(a)) {
            QVariantList children;
            for (auto *child : tray->applets()) {
                if (!child || child->destroyed()) continue;
                auto embedded = backendRow(child);
                embedded["declaredActivationService"] = child->pluginMetaData().value(QStringLiteral("X-Plasma-DBusActivationService"));
                children.append(embedded);
            }
            row["embeddedApplets"] = children;
            row["embeddedInventoryScope"] = "live-native-tray-applets";
        }
        result.append(row);
    }
    return result;
}
uint PanelSession::addWidget(const QString &pluginId) {
    setError({});
    if(!m_containment || m_containment->destroyed() || m_containment->immutable()) {
        setError(tr("This containment is unavailable or locked."));return 0;
    }
    bool selectable=false;
    for(const auto &entry:Catalog::discover()) {
        const auto data=entry.toMap();
        if(data.value("id").toString()==pluginId){selectable=data.value("catalogVisible").toBool();break;}
    }
    if(!selectable){setError(tr("The package is not an available widget in the native catalog."));return 0;}
    auto *applet=m_containment->createApplet(pluginId);
    if(!applet || applet->failedToLaunch()) {
        const auto reason=applet ? applet->launchErrorMessage() : QString();
        setError(reason.isEmpty() ? tr("The native loader could not create this widget.") : reason);
        if(applet)applet->destroy();return 0;
    }
    watchApplet(applet);
    // Creation is not a certificate for its services or compositor-specific backend.
    return applet->id();
}
bool PanelSession::removeWidget(uint id) {
    setError({});
    auto *applet=findApplet(id);
    if(!applet || applet==m_containment || m_containment->immutable() || applet->immutable()) {
        setError(tr("The widget is missing or locked, or the ID refers to the panel."));return false;
    }
    // Native permanent removal clears this instance's config. No synthetic appletsrc edits,
    // notification service or imitation of the original undo notification.
    applet->destroy();return true;
}
bool PanelSession::requestOrder(const QVariantList &ids) {
    setError({});
    if(!m_containment || m_containment->destroyed() || m_containment->immutable() || !m_panelItem) {
        setError(tr("This panel is unavailable, locked or has no bound native view."));return false;
    }
    const auto current=order();QSet<uint> expected,requested;
    for(auto *applet:m_containment->applets())if(!applet->destroyed() && applet->immutable()) {
        setError(tr("A widget in this panel is locked."));return false;
    }
    for(const auto &id:current)expected.insert(id.toUInt());
    for(const auto &value:ids) {
        bool ok=false;const double number=value.toDouble(&ok);
        if(!ok || value.metaType().id()==QMetaType::Bool || !std::isfinite(number) || number<=0 ||
            number>std::numeric_limits<uint>::max() || std::floor(number)!=number || requested.contains(uint(number))) {
            setError(tr("Widget order must contain each instance ID exactly once."));return false;
        }
        requested.insert(uint(number));
    }
    if(requested!=expected){setError(tr("Widget order must match the current panel instances."));return false;}
    if(!QMetaObject::invokeMethod(m_panelItem,"reorderApplets",Q_ARG(QVariant,QVariant(ids)))) {
        setError(tr("This containment has no native reorderApplets contract."));return false;
    }
    m_notify.start();return true;
}
QVariantList PanelSession::widgetActions(uint id,bool prepare) {
    setError({});QPointer<Plasma::Applet> applet=findApplet(id);
    if(!applet){setError(tr("The widget no longer exists."));return {};}
    // Announce one menu opening. State refreshes must not re-enter a package factory
    // which may rebuild its actions and emit contextualActionsChanged again.
    if(prepare)applet->contextualActionsAboutToShow();
    if(!applet || applet->destroyed())return {};
    QSet<QAction*> seen;
    std::function<QVariantList(const QList<QAction*>&)> snapshot=[&](const QList<QAction*> &list){
        QVariantList result;
        for(auto *action:list) {
            if(!action || seen.contains(action))continue;seen.insert(action);
            QString token;
            for(auto it=m_actions.cbegin();it!=m_actions.cend();++it)
                if(it->applet==applet && it->action==action){token=it.key();break;}
            if(token.isEmpty()) {
                token=QStringLiteral("action-%1").arg(++m_nextAction);
                m_actions.insert(token,{applet,action});
                connect(action,&QAction::changed,this,[this,id]{emit actionsChanged(id);});
                connect(action,&QObject::destroyed,this,[this,token]{m_actions.remove(token);});
            }
            result.append(QVariantMap{{"token",token},{"text",action->text()},{"icon",action->icon().name()},
                {"enabled",action->isEnabled()},{"visible",action->isVisible()},{"separator",action->isSeparator()},
                {"checkable",action->isCheckable()},{"checked",action->isChecked()},
                {"submenu",action->menu() ? snapshot(action->menu()->actions()) : QVariantList()}});
        }
        return result;
    };
    return snapshot(applet->contextualActions());
}
bool PanelSession::triggerAction(uint id,const QString &token) {
    setError({});auto *applet=findApplet(id);const auto ref=m_actions.value(token);
    if(!applet || ref.applet!=applet || !ref.action) {
        setError(tr("The action no longer belongs to this widget."));return false;
    }
    QSet<QAction*> seen;
    std::function<bool(const QList<QAction*>&)> reachable=[&](const QList<QAction*> &list){
        for(auto *action:list) {
            if(!action || !action->isEnabled() || !action->isVisible() || action->isSeparator() || seen.contains(action))continue;
            seen.insert(action);
            if(action==ref.action)return !action->menu();
            if(action->menu() && reachable(action->menu()->actions()))return true;
        }
        return false;
    };
    if(!reachable(applet->contextualActions())){setError(tr("The action is no longer available or is disabled."));return false;}
    ref.action->trigger();return true;
}
ConfigurationSession *PanelSession::configuration(uint id) const {return m_sessions.value(id).data();}
bool PanelSession::configure(uint id) {
    auto *applet=findApplet(id);if(!applet)return false;
    openConfiguration(applet);return true;
}
void PanelSession::openConfiguration(Plasma::Applet *applet) {
    if(!m_containment || !applet || applet->destroyed() || (applet!=m_containment && !m_containment->applets().contains(applet)))return;
    const uint id=applet->id();
    auto *session=configuration(id);
    if(session && !session->view()){delete session;session=nullptr;}
    if(!session) {
        session=new ConfigurationSession(applet);session->setParent(this);m_sessions.insert(id,session);
        watchApplet(applet);
    }
    session->show();Q_EMIT configurationOpened(id);
}
