// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QObject>
#include <QPointer>
#include <QHash>
#include <QSet>
#include <QTimer>
#include <QVariantList>
class ViewCorona;
class PanelViewHost;
class QScreen;
// In-process lifecycle for existing native containments. The caller owns Corona,
// loads its layout first and supplies persisted bindings (e.g. migration report).
// No autostart/skin watcher and no production activation is installed here.
class PanelRuntime:public QObject {
    Q_OBJECT
    Q_PROPERTY(QVariantList panels READ panels NOTIFY changed)
    Q_PROPERTY(QString skin READ skin NOTIFY changed)
    Q_PROPERTY(QString error READ error NOTIFY changed)
public:
    PanelRuntime(ViewCorona *corona,QString viewSettingsFile,bool layerSurfaces,QObject *parent=nullptr,bool nativePanelPolicy=false);
    ~PanelRuntime()override;
    bool setAssignments(const QHash<uint,QString> &outputs);
    Q_INVOKABLE bool setSkin(const QString &skin);
    Q_INVOKABLE void reconcile();
    QVariantList panels()const{return m_status;}
    QString skin()const{return m_skin;}
    QString error()const{return m_error;}
    PanelViewHost *view(uint containmentId)const;
    QVariantMap readiness()const;
    bool quiescing()const{return m_quiescing;}
    // Enabled by disposable previews and by transactional profile edit sessions.
    // Native Panel Settings keep runtime bindings by output description.
    void setOutputMovesAllowed(bool allowed){m_outputMovesAllowed=allowed;}
    void setPanelCloningAllowed(bool allowed){m_panelCloningAllowed=allowed;}
    // "Add Panel" of the original desktop edit mode (ViewCorona::addPanelRequested).
    void setPanelAddingAllowed(bool allowed){m_panelAddingAllowed=allowed;}
    bool addPanel(const QString &actionData,QScreen *target);
    QHash<uint,QString> assignments()const;
Q_SIGNALS:
    void changed();
private:
    void observe(QScreen *screen);
    void drop(uint containmentId);
    void dropAll();
    void moveToOutput(uint containmentId,QScreen *target);
    void cloneToOutput(uint containmentId,int location,QScreen *target);
    void updateReservations();
    QPointer<ViewCorona> m_corona;
    QString m_settingsFile,m_skin="default",m_error;
    bool m_layerSurfaces,m_reconciling=false;
    bool m_nativePanelPolicy=false;
    bool m_quiescing=false;
    bool m_outputMovesAllowed=false;
    bool m_panelCloningAllowed=false;
    bool m_panelAddingAllowed=false;
    QSet<uint> m_reopenSettings;
    QHash<uint,QString> m_assignments;
    QHash<uint,QVariantMap> m_initialPanelSettings;
    QHash<uint,QPointer<PanelViewHost>> m_views;
    QSet<uint> m_observed;
    QTimer m_reconcile;
    QVariantList m_status;
};
