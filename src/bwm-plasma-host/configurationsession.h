// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QObject>
#include <QVariantList>
#include <QVariantMap>
#include <QPointer>
#include <memory>
class QQuickItem;
namespace Plasma { class Applet; }
namespace PlasmaQuick { class ConfigView; }
class ConfigurationSession : public QObject {
    Q_OBJECT
    Q_PROPERTY(QVariantList pages READ pages NOTIFY pagesChanged)
    Q_PROPERTY(QString error READ error NOTIFY changed)
    Q_PROPERTY(bool dirty READ dirty NOTIFY changed)
public:
    // R4 probes keep their transactional diagnostic harness. Interactive R5 views
    // use Plasma's installed AppletConfiguration.qml and its native page workflow.
    explicit ConfigurationSession(Plasma::Applet *applet,bool nativeFrame=false);
    ~ConfigurationSession() override;
    QVariantList pages() const;
    QString error() const { return m_error; }
    bool dirty() const;
    PlasmaQuick::ConfigView *view() const;
    Q_INVOKABLE bool apply();
    Q_INVOKABLE void cancel();
    Q_INVOKABLE void defaults();
    Q_INVOKABLE void show();
Q_SIGNALS:
    void changed();
    void pagesChanged();
private Q_SLOTS:
    void pageValueChanged();
    void nativePageChanged();
private:
    QVariantMap collect() const;
    void populate(const QVariantMap &values);
    QVariantMap stored() const;
    QVariantMap pageValues(QObject *page,const QVariantMap &values) const;
    void observe();
    QQuickItem *nativePage() const;
    QPointer<Plasma::Applet> m_applet;
    QPointer<PlasmaQuick::ConfigView> m_view;
    QVariantList m_pages;
    QVariantMap m_baseline;
    QVariantMap m_defaults;
    QVariantMap m_pending;
    QString m_error;
    bool m_loading = false;
    bool m_nativeFrame = false;
};
