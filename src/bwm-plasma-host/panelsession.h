// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QObject>
#include <QHash>
#include <QPointer>
#include <QSet>
#include <QVariantList>
#include <QVariantMap>
#include <QTimer>
namespace Plasma {class Applet;class Containment;}
namespace PlasmaQuick {class AppletQuickItem;}
class QAction;
class ConfigurationSession;
class PackageWindows;

// In-process R4 contract. R5 can consume the same native configureRequested path.
class PanelSession : public QObject {
    Q_OBJECT
    Q_PROPERTY(QVariantMap panelInfo READ panelInfo NOTIFY changed)
    Q_PROPERTY(QVariantList widgets READ widgets NOTIFY changed)
    Q_PROPERTY(QVariantList widgetBackends READ widgetBackends NOTIFY changed)
    Q_PROPERTY(QVariantList order READ order NOTIFY changed)
    Q_PROPERTY(QString error READ error NOTIFY errorChanged)
public:
    explicit PanelSession(Plasma::Containment *containment,bool connectConfiguration=true,bool nativeConfiguration=false);
    ConfigurationSession *configuration(uint appletId) const;
    Q_INVOKABLE bool configure(uint appletId);
    QVariantMap panelInfo() const;
    QVariantList widgets() const;
    QVariantList widgetBackends() const;
    QVariantList order() const;
    QString error() const {return m_error;}
    void bindPanelItem(PlasmaQuick::AppletQuickItem *item);
    Q_INVOKABLE uint addWidget(const QString &pluginId);
    Q_INVOKABLE bool removeWidget(uint appletId);
    // Accepted requests are applied/serialized by the original panel LayoutManager.
    Q_INVOKABLE bool requestOrder(const QVariantList &ids);
    Q_INVOKABLE QVariantList widgetActions(uint appletId,bool prepare=true);
    Q_INVOKABLE bool triggerAction(uint appletId,const QString &token);
    PackageWindows *packageWindows()const{return m_packageWindows;}
Q_SIGNALS:
    void configurationOpened(uint appletId);
    void changed();
    void errorChanged();
    void actionsChanged(uint appletId);
private:
    Plasma::Applet *findApplet(uint id) const;
    void watchApplet(Plasma::Applet *applet);
    void setError(const QString &error);
    struct ActionRef {QPointer<Plasma::Applet> applet;QPointer<QAction> action;};
    void openConfiguration(Plasma::Applet *applet);
    QPointer<Plasma::Containment> m_containment;
    QHash<uint,QPointer<ConfigurationSession>> m_sessions;
    QSet<uint> m_watched;
    QPointer<PlasmaQuick::AppletQuickItem> m_panelItem;
    QHash<QString,ActionRef> m_actions;
    quint64 m_nextAction=0;
    QTimer m_notify;
    QString m_error;
    PackageWindows *m_packageWindows;
    bool m_nativeConfiguration=false;
};
