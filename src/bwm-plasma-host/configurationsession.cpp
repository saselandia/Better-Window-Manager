// SPDX-License-Identifier: GPL-2.0-or-later
#include "configurationsession.h"
#include <Plasma/Applet>
#include <PlasmaQuick/ConfigView>
#include <PlasmaQuick/ConfigModel>
#include <KConfigLoader>
#include <KSharedConfig>
#include <QQmlEngine>
#include <QQmlContext>
#include <QQmlComponent>
#include <QQuickItem>
#include <QMetaProperty>
#include <QCoreApplication>
#include <QElapsedTimer>
#include <QScopedValueRollback>
#include <QDir>
ConfigurationSession::ConfigurationSession(Plasma::Applet *applet)
    : m_applet(applet), m_view(new PlasmaQuick::ConfigView(applet)) {
    // ConfigView emulates WA_DeleteOnClose using deleteLater() in hideEvent.
    // Observe it rather than owning it with a unique_ptr (which would double-delete).
    connect(m_view.data(),&QObject::destroyed,this,[this]{ m_pages.clear(); emit pagesChanged(); emit changed(); });
    auto *model=m_view->configModel();
    if (!model || !applet->configScheme()) {
        m_error=tr("This package has no usable configuration model/schema.");
        m_view->rootContext()->setContextProperty("bwmConfigSession",this);m_view->init();return;
    }
    m_loading=true;
    m_baseline=stored();
    applet->configScheme()->useDefaults(true);m_defaults=stored();applet->configScheme()->useDefaults(false);
    for(int i=0;i<model->rowCount();++i) {
        auto category=model->get(i).toMap();
        if(!category.value("visible",true).toBool()) continue;
        if(!category.value("pluginName").toString().isEmpty()) {
            m_error=tr("This category requires a KCM adapter which is not implemented."); continue;
        }
        QQmlComponent component(m_view->engine());
        const QString module=category.value("configUiModule").toString(),type=category.value("configUiComponent").toString();
        if(!module.isEmpty() && !type.isEmpty()) {
            // Same precedence as Plasma 6.7.5 AppletConfiguration.qml. A named QML
            // component is not a KCModule; let Qt resolve its installed module.
            component.loadFromModule(module,type,QQmlComponent::PreferSynchronous);
            category.insert("loader","module");
        } else if(!category.value("source").toString().isEmpty()) {
            const auto source=category.value("source").toString();
            component.loadUrl(QDir::isAbsolutePath(source) ? QUrl::fromLocalFile(source) : QUrl(source),QQmlComponent::PreferSynchronous);
            category.insert("loader","source");
        } else {
            m_error=tr("This category needs a source URL or both a QML module and component name.");continue;
        }
        QElapsedTimer timer;timer.start();
        while(component.status()==QQmlComponent::Loading && timer.elapsed()<3000) QCoreApplication::processEvents();
        if(component.status()!=QQmlComponent::Ready) {
            m_error=component.errorString();if(m_error.isEmpty())m_error=tr("Configuration component loading timed out.");continue;
        }
        QObject *object=component.beginCreate(m_view->rootContext());
        if(!object){m_error=component.errorString();continue;}
        auto initial=pageValues(object,m_baseline);
        if(object->metaObject()->indexOfProperty("title")>=0)initial.insert("title",category.value("name"));
        // Native pages may declare required cfg_* and title properties, or read them
        // in Component.onCompleted. Supply them before completing the component.
        component.setInitialProperties(object,initial);component.completeCreate();
        if(component.isError()){delete object;m_error=component.errorString();continue;}
        auto *item=qobject_cast<QQuickItem*>(object);
        if(!item) { delete object; m_error=component.errorString(); if(m_error.isEmpty()) m_error=tr("Configuration page must be an Item."); continue; }
        item->setParent(m_view.data());
        category.insert("item",QVariant::fromValue(item));
        m_pages.append(category);
    }
    if(m_pages.isEmpty() && m_error.isEmpty())m_error=tr("This package has no editable applet configuration pages. The panel editor is not provided by this preview.");
    for(const auto &category:m_pages) {
        auto *page=category.toMap().value("item").value<QQuickItem*>();
        // AppletConfiguration.qml 6.7.5 only walks Plasmoid.configuration.keys(): a cfg_*
        // property without a schema entry is never filled nor saved there, so it is ignored
        // here too instead of blocking the page (e.g. cfg_lastSeenVersion helpers).
        // saveConfig() is honoured in apply(); loadConfig() is never called by Plasma 6.7.5.
        for(int i=0;i<page->metaObject()->propertyCount();++i) {
            const QString name=QString::fromLatin1(page->metaObject()->property(i).name());
            if(!name.startsWith("cfg_"))continue;
            const QString key=name.mid(4);
            if(!m_baseline.contains(key))continue;
            if(!page->metaObject()->property(i).hasNotifySignal() || !page->metaObject()->property(i).isWritable())
                m_error=tr("This setting needs a writable property with change notification: %1").arg(key);
        }
    }
    populate(m_baseline);
    m_loading=false;
    observe();
    m_view->rootContext()->setContextProperty("bwmConfigSession",this);
    m_view->init();
}
ConfigurationSession::~ConfigurationSession() { delete m_view.data(); }
PlasmaQuick::ConfigView *ConfigurationSession::view() const { return m_view.data(); }
QVariantMap ConfigurationSession::stored() const {
    QVariantMap values;
    if(auto *scheme=m_applet->configScheme()) for(auto *entry:scheme->items()) values.insert(entry->name(),entry->property());
    return values;
}
QVariantMap ConfigurationSession::collect() const {
    return m_pending;
}
QVariantMap ConfigurationSession::pageValues(QObject *page,const QVariantMap &values) const {
    QVariantMap result;
    for(int i=0;i<page->metaObject()->propertyCount();++i) {
        const QString name=QString::fromLatin1(page->metaObject()->property(i).name());
        if(!name.startsWith("cfg_"))continue;
        QString key=name.mid(4);
        if(values.contains(key))result.insert(name,values.value(key));
        else if(key.endsWith("Default") && m_baseline.contains(key.chopped(7)))result.insert(name,m_defaults.value(key.chopped(7)));
        else if(key.endsWith("Immutable") && m_baseline.contains(key.chopped(9)))result.insert(name,m_applet->configScheme()->isImmutable(key.chopped(9)));
    }
    return result;
}
void ConfigurationSession::populate(const QVariantMap &values) {
    const QScopedValueRollback<bool> loading(m_loading,true);
    m_pending=values;
    for(const auto &category:m_pages) {
        auto *page=category.toMap().value("item").value<QQuickItem*>();
        const auto properties=pageValues(page,values);
        for(auto it=properties.cbegin();it!=properties.cend();++it)page->setProperty(it.key().toUtf8(),it.value());
    }
}
void ConfigurationSession::observe() {
    const auto slot=metaObject()->method(metaObject()->indexOfSlot("pageValueChanged()"));
    for(const auto &category:m_pages) {
        auto *page=category.toMap().value("item").value<QQuickItem*>();
        for(int i=0;i<page->metaObject()->propertyCount();++i) {
            auto prop=page->metaObject()->property(i);
            const QString name=QString::fromLatin1(prop.name());
            if(name.startsWith("cfg_") && m_baseline.contains(name.mid(4)) && prop.hasNotifySignal())
                QObject::connect(page,prop.notifySignal(),this,slot,Qt::UniqueConnection);
        }
    }
}
void ConfigurationSession::pageValueChanged() {
    if(m_loading || !m_view || !m_applet) return;
    auto *source=qobject_cast<QQuickItem*>(sender());
    if(!source) return;
    // An alias may share a notify signal with other properties. Gather all matching keys
    // before synchronizing peers, and never re-read a stale hidden page as the authority.
    QVariantMap updates;
    for(int i=0;i<source->metaObject()->propertyCount();++i) {
        const auto prop=source->metaObject()->property(i);
        const QString name=QString::fromLatin1(prop.name()),key=name.mid(4);
        if(!name.startsWith("cfg_") || !m_baseline.contains(key) || prop.notifySignalIndex()!=senderSignalIndex()) continue;
        auto value=prop.read(source);
        value.convert(m_baseline.value(key).metaType()); // Invalid values remain staged; apply rejects them.
        if(value!=m_pending.value(key)) updates.insert(key,value);
    }
    if(updates.isEmpty()) return;
    {
        const QScopedValueRollback<bool> loading(m_loading,true);
        for(auto it=updates.cbegin();it!=updates.cend();++it) m_pending.insert(it.key(),it.value());
        for(const auto &category:m_pages) {
            auto *page=category.toMap().value("item").value<QQuickItem*>();
            if(page==source) continue;
            for(auto it=updates.cbegin();it!=updates.cend();++it) {
                const QByteArray name=("cfg_"+it.key()).toUtf8();
                if(page->metaObject()->indexOfProperty(name)>=0) {
                    page->setProperty(name,it.value());
                    auto represented=page->property(name);
                    if(!represented.convert(m_baseline.value(it.key()).metaType()) || represented!=it.value())
                        m_error=tr("These pages cannot represent the same staged value: %1").arg(it.key());
                }
            }
        }
    }
    emit changed();
}
bool ConfigurationSession::dirty() const {
    if(m_loading || !m_view) return false;
    const auto values=collect();
    for(auto it=values.cbegin();it!=values.cend();++it) {
        auto value=it.value();
        if(!value.convert(m_baseline.value(it.key()).metaType()) || value!=m_baseline.value(it.key())) return true;
    }
    return false;
}
bool ConfigurationSession::apply() {
    if(!m_view || !m_applet || !m_error.isEmpty() || !m_applet->configScheme()) return false;
    auto *scheme=m_applet->configScheme();
    // As AppletConfiguration.qml::saveConfig(): a page's own saveConfig() runs first so it can
    // set cfg_* properties; their change notifications update the staged values below.
    for(const auto &category:m_pages) {
        auto *page=category.toMap().value("item").value<QQuickItem*>();
        if(page && page->metaObject()->indexOfMethod("saveConfig()")>=0)QMetaObject::invokeMethod(page,"saveConfig");
    }
    if(!m_error.isEmpty()){emit changed();return false;}
    QVariantMap changes;
    for(const auto &category:m_pages) {
        auto *page=category.toMap().value("item").value<QQuickItem*>();
        if(page->metaObject()->indexOfProperty("configurationValid")>=0 && !page->property("configurationValid").toBool()) {
            m_error=tr("This configuration page reports invalid settings. Cancel and reopen to review them.");emit changed();return false;
        }
    }
    const auto values=collect();
    for(auto it=values.cbegin();it!=values.cend();++it) {
        auto value=it.value();
        auto *entry=scheme->KCoreConfigSkeleton::findItem(it.key());
        if(!value.convert(entry->property().metaType())) { m_error=tr("Unsupported value type."); emit changed(); return false; }
        if(value!=m_baseline.value(it.key())) {
            if(scheme->isImmutable(it.key())) { m_error=tr("A setting is locked by policy."); emit changed(); return false; }
            changes.insert(it.key(),value);
        }
    }
    // Reparse before saving: preserve unknown keys and detect edits by another configurator.
    scheme->config()->reparseConfiguration(); scheme->load();
    for(auto it=changes.cbegin();it!=changes.cend();++it) {
        auto *entry=scheme->KCoreConfigSkeleton::findItem(it.key());
        if(entry->property()!=m_baseline.value(it.key())) { m_error=tr("Settings changed elsewhere. Cancel and reopen before applying."); emit changed(); return false; }
    }
    for(auto it=changes.cbegin();it!=changes.cend();++it) scheme->KCoreConfigSkeleton::findItem(it.key())->setProperty(it.value());
    if(!scheme->save()) { m_error=tr("Could not save settings."); emit changed(); return false; }
    scheme->load();
    for(auto it=changes.cbegin();it!=changes.cend();++it)
        if(scheme->KCoreConfigSkeleton::findItem(it.key())->property()!=it.value()) { m_error=tr("Saved value could not be confirmed."); emit changed(); return false; }
    m_baseline=stored(); populate(m_baseline); emit changed(); return true;
}
void ConfigurationSession::cancel() { if(!m_view) return; populate(m_baseline); m_view->close(); emit changed(); }
void ConfigurationSession::defaults() {
    if(!m_view || !m_applet || !m_applet->configScheme()) return;
    QVariantMap values=m_defaults;
    for(auto it=values.begin();it!=values.end();++it) if(m_applet->configScheme()->isImmutable(it.key()))it.value()=m_baseline.value(it.key());
    populate(values); emit changed();
}
void ConfigurationSession::show() { if(m_view) { m_view->show(); m_view->requestActivate(); } }
