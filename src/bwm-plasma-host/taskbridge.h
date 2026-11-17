// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include "tasksource.h"
#include "taskmenupolicy.h"
#include "launchrouter.h"
#include <QPointer>
#include <QProcess>
#include <QQueue>
#include <QTimer>
#include <QHash>
#include <QSet>
namespace TaskManager {class WindowTasksModel;class TasksModel;}
class QAbstractProxyModel;
class BwmTaskBridge:public QObject {
    Q_OBJECT
public:
    BwmTaskBridge(QString runtime,QString config,QString program,QString helper,QObject *parent=nullptr);
    ~BwmTaskBridge()override;
    void attach(QObject *root);
    void tick();
    BwmTaskSource *source(){return &m_source;}
    QString error()const{return m_error;}
    int boundCount()const{return m_bound.size();}
    QVariantMap state()const;
    static void attachEnabled(QObject *root);
    static QVariantMap diagnostics();
    static BwmTaskBridge *thumbnailBridge();
    quint64 snapshotSequence()const{return m_snapshotSequence;}
    bool setSuspended(bool suspended);
    static bool suspendAll(bool suspended);
Q_SIGNALS:
    void snapshotCommitted(quint64 sequence);
    void launchQueued(QJsonObject request); // Pinned launcher or .desktop Action accepted into the queue.
private:
    void discover(QAbstractItemModel *model,QSet<QAbstractItemModel*> &seen,QSet<TaskManager::WindowTasksModel*> &targets,QSet<QAbstractProxyModel*> &filters);
    void enqueue(const QJsonObject &request);
    void installRoutes(const QSet<QAbstractProxyModel*> &filters);
    void startAction();
    void start(QProcess &process,const QString &operation);
    void restore();
    bool active()const;
    struct Binding {QPointer<TaskManager::WindowTasksModel> target;QPointer<QAbstractItemModel> previous;};
    struct Route {QPointer<QAbstractProxyModel> filter;QPointer<QAbstractItemModel> concat;QPointer<BwmLaunchRouter> router;};
    QHash<QAbstractProxyModel*,Route> m_routes;
    int m_launchRequests=0;
    QString m_runtime,m_config,m_program,m_helper,m_error;
    QList<QPointer<QObject>> m_roots;
    QList<QPointer<TaskManager::TasksModel>> m_taskModels;
    QHash<TaskManager::WindowTasksModel*,Binding> m_bound;
    BwmTaskSource m_source;
    TaskMenuPolicy m_menus;
    QProcess m_snapshot,m_action;
    QTimer m_poll,m_snapshotTimeout,m_actionTimeout;
    QQueue<QJsonObject> m_actions;
    bool m_snapshotValid=false;
    bool m_suspended=false;
    quint64 m_snapshotSequence=0;
};
