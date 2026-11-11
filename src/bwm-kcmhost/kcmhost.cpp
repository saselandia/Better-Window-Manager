// SPDX-License-Identifier: GPL-2.0-or-later
#include "kcmhost.h"
#include <KPluginMetaData>
#include <KQuickConfigModule>
#include <KQuickConfigModuleLoader>
#include <QQmlEngine>
#include <memory>

static const auto KCM_NAMESPACE = QStringLiteral("plasma/kcms/systemsettings");

KcmHost::KcmHost(QQuickItem *parent) : QQuickItem(parent) {}
KcmHost::~KcmHost() { unload(); }

bool KcmHost::available(const QString &module) {
    return KPluginMetaData::findPluginById(KCM_NAMESPACE, module).isValid();
}

QVariantMap KcmHost::info(const QString &module) {
    const auto data = KPluginMetaData::findPluginById(KCM_NAMESPACE, module);
    if (!data.isValid())
        return {};
    return {{QStringLiteral("name"), data.name()}, {QStringLiteral("description"), data.description()},
            {QStringLiteral("icon"), data.iconName()}};
}

void KcmHost::setModule(const QString &module) {
    if (module == m_module)
        return;
    m_module = module;
    Q_EMIT moduleChanged();
    if (isComponentComplete())
        reload();
}

QObject *KcmHost::kcm() const { return m_kcm.data(); }
int KcmHost::depth() const { return m_kcm ? m_kcm->depth() : 0; }

void KcmHost::componentComplete() {
    QQuickItem::componentComplete();
    reload();
}

void KcmHost::unload() {
    if (m_kcm) {
        // Sub pages and mainUi are children of the module; deleting it releases them.
        m_kcm->deleteLater();
        m_kcm.clear();
    }
}

void KcmHost::reload() {
    unload();
    m_error.clear();
    m_name.clear();
    m_description.clear();
    m_icon.clear();
    if (!m_module.isEmpty()) {
        const auto data = KPluginMetaData::findPluginById(KCM_NAMESPACE, m_module);
        if (!data.isValid()) {
            m_error = QStringLiteral("KCM not installed: %1").arg(m_module);
        } else {
            m_name = data.name();
            m_description = data.description();
            m_icon = data.iconName();
            QQmlEngine *engine = qmlEngine(this);
            // Share the window engine (as systemsettings does) so the KCM's items can live here.
            std::shared_ptr<QQmlEngine> shared(engine, [](QQmlEngine *) {});
            auto result = KQuickConfigModuleLoader::loadModule(data, this, {}, shared);
            if (!result) {
                m_error = result.errorText;
            } else {
                m_kcm = result.plugin;
                connect(m_kcm, &KQuickConfigModule::pagePushed, this, &KcmHost::depthChanged);
                connect(m_kcm, &KQuickConfigModule::pageRemoved, this, &KcmHost::depthChanged);
                // mainUi() first: it sets the module's engine, which load() may use (kcm_fonts adds
                // its image provider there and crashed when load() came first).
                if (!m_kcm->mainUi())
                    m_error = m_kcm->errorString();
                else
                    m_kcm->load();
            }
        }
    }
    Q_EMIT kcmChanged();
    Q_EMIT errorChanged();
    Q_EMIT depthChanged();
}

QQuickItem *KcmHost::mainUi() const { return m_kcm ? m_kcm->mainUi() : nullptr; }

QQuickItem *KcmHost::subPage(int index) const {
    return m_kcm && index >= 0 && index < m_kcm->depth() - 1 ? m_kcm->subPage(index) : nullptr;
}

void KcmHost::pop() {
    if (m_kcm && m_kcm->depth() > 1)
        m_kcm->pop();
}
